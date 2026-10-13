# math는 유한한 숫자 검증에, Path는 프로젝트 기준의 영상 경로 구성에 사용한다.
import math
from pathlib import Path

# 실제 Run 분석의 실행 진입점이다. Baseline 비교와 Shape 관찰은 Inspector에 둔다.
import cv2

# 승인된 Closing + Top-strip 검출과 공통 상태 판정만 호출한다.
from target_detection import DETECTION_POLICY, detect_target
from tracking_state import (
    classify_tracking_state,
    TRACKING_STATE_MISSING,
    TRACKING_STATE_OFF_TARGET,
    TRACKING_STATE_ON_TARGET,
)


# 프로젝트 입력 영상과 분석할 Run 구간을 정의한다.
# 시작 시각은 사람이 확인한 356번 Frame / 60 FPS다. 자동 Countdown 탐색 결과가 아니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = PROJECT_ROOT / "data" / "raw" / "woong01.mp4"
RUN_DURATION_SECONDS = 60.0
KNOWN_RUN_START_SECONDS = 5.933333333333334

# Observation에 기록하는 상태값을 한곳에서 관리해 오타와 중복을 방지한다.
STATUS_DETECTED = "타겟 검출됨"
STATUS_NO_CANDIDATE = "타겟 미결정: 유효 후보 없음"
STATUS_AMBIGUOUS = "타겟 미결정: 유효 후보 여러 개"


def analyze_run() -> dict:
    """기존 Run 분석 흐름을 실행하고 Raw Observation·State Sequence·Summary를 반환한다."""
    # OpenCV에 전달하기 전에 입력 경로가 실제 파일인지 확인한다.
    if not VIDEO_PATH.exists():
        raise FileNotFoundError("비디오 파일이 존재하지 않습니다.")
    if not VIDEO_PATH.is_file():
        raise ValueError("올바른 비디오 파일이 아닙니다.")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))

    try:
        # 비디오를 열고 분석에 필요한 메타데이터를 읽는다.
        if not video_capture.isOpened():
            raise RuntimeError("비디오 파일을 열 수 없습니다.")

        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        video_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        reported_frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)

        # 잘못된 메타데이터로 시간이나 프레임 위치를 계산하지 않도록 검증한다.
        if not math.isfinite(video_fps) or video_fps <= 0:
            raise ValueError("FPS는 0보다 큰 유한한 숫자여야 합니다.")
        if not math.isfinite(video_width) or video_width <= 0:
            raise ValueError("영상 너비는 0보다 큰 유한한 숫자여야 합니다.")
        if not math.isfinite(video_height) or video_height <= 0:
            raise ValueError("영상 높이는 0보다 큰 유한한 숫자여야 합니다.")
        if video_fps != 60.0:
            raise ValueError(f"지원하지 않는 FPS입니다. 실제 FPS: {video_fps}")

        # Crosshair는 화면 중앙에 고정된 것으로 가정한다. Target 중심 좌표와는 다른 기준점이다.
        crosshair_x = int(video_width) // 2
        crosshair_y = int(video_height) // 2
        crosshair_point = (crosshair_x, crosshair_y)

        if crosshair_x <= 0 or crosshair_y <= 0:
            raise ValueError("크로스헤어 좌표는 0 이하일 수 없습니다.")

        # 알려진 시작 시각으로부터 60초 분석 구간의 끝을 계산한다.
        known_run_start_seconds = KNOWN_RUN_START_SECONDS
        if known_run_start_seconds is None:
            raise ValueError("시작 위치가 존재하지 않습니다.")
        if not math.isfinite(known_run_start_seconds):
            raise ValueError("시작 위치는 유한한 숫자여야 합니다.")
        if known_run_start_seconds < 0:
            raise ValueError("시작 위치는 음수일 수 없습니다.")

        run_end_seconds = known_run_start_seconds + RUN_DURATION_SECONDS

        # 디코딩 범위와 분석 구간의 경계를 기록할 변수를 초기화한다.
        decoded_frame_count = 0
        run_segment_frame_count = 0
        first_segment_frame_index = None
        first_segment_frame_time_seconds = None
        last_segment_frame_index = None
        last_segment_frame_time_seconds = None
        frame_coverage_end_seconds = 0.0

        # 분석 구간의 각 프레임 결과를 순서대로 보존한다.
        # center가 None이면 해당 프레임에서는 타겟 위치를 결정하지 못했다는 뜻이다.
        target_observations = []
        # Raw Detection과 조준 상태를 분리한다. 두 목록은 같은 frame_index로 연결할 수 있다.
        tracking_state_sequence = []

        # 영상을 처음부터 한 번만 순차 디코딩하고, Run 구간만 타겟 검출한다.
        while True:
            read_success, frame = video_capture.read()
            if not read_success:
                break

            current_frame_index = decoded_frame_count
            # 현재는 60 FPS CFR 입력을 가정하며, 시간은 녹화 시작 기준의 초 단위다.
            frame_time_seconds = current_frame_index / video_fps

            # 시작은 포함하고 끝은 제외한다. 이 조건을 만족하는 Frame에만 검출을 적용한다.
            if known_run_start_seconds <= frame_time_seconds < run_end_seconds:
                if first_segment_frame_index is None:
                    first_segment_frame_index = current_frame_index

                last_segment_frame_index = current_frame_index
                run_segment_frame_count += 1

                # 검출 함수의 여섯 반환값을 받는다. _로 시작하는 변수는 여기서 사용하지 않는 값이다.
                (
                    detected,
                    _bounding_box,
                    center,
                    _contour_count,
                    valid_candidate_count,
                    selected_contour,
                ) = detect_target(frame)

                # 후보가 없거나 여러 개여서 Contour가 None이면 MISSING이다. OFF_TARGET으로 바꾸지 않는다.
                tracking_state = classify_tracking_state(
                    selected_contour,
                    crosshair_point,
                )

                # 유효 후보 수를 도메인 상태로 변환한다.
                if detected:
                    status = STATUS_DETECTED
                elif valid_candidate_count == 0:
                    status = STATUS_NO_CANDIDATE
                else:
                    status = STATUS_AMBIGUOUS

                # 한 Frame의 검출 기록을 목록에 추가하고 최종 분석 결과로 반환한다.
                observation = {
                    "frame_index": current_frame_index,
                    "frame_time_seconds": frame_time_seconds,
                    "status": status,
                    "center": center,
                    "valid_candidate_count": valid_candidate_count,
                }
                target_observations.append(observation)

                # 조준 상태에도 같은 Frame 인덱스와 시간을 넣어 Raw Observation과 대응시킨다.
                tracking_state_observation = {
                    "frame_index": current_frame_index,
                    "frame_time_seconds": frame_time_seconds,
                    "tracking_state": tracking_state,
                }

                tracking_state_sequence.append(tracking_state_observation)

            decoded_frame_count += 1
            # 마지막 Frame이 차지하는 시간까지 포함하려면 인덱스에 1을 더해야 한다.
            frame_coverage_end_seconds = (current_frame_index + 1) / video_fps

        # 상태별 첫 등장 인덱스를 보존해 수동 검증할 프레임을 찾는다.
        representative_frame_indices = {
            TRACKING_STATE_ON_TARGET: None,
            TRACKING_STATE_OFF_TARGET: None,
            TRACKING_STATE_MISSING: None,
        }

        # None은 아직 찾지 못했다는 뜻이다. 실제 인덱스 0도 유효하므로 None과 따로 구분한다.
        # Sequence의 시간 순서를 이용해 각 상태의 첫 인덱스만 기록한다.
        for observation in tracking_state_sequence:
            tracking_state = observation["tracking_state"]
            frame_index = observation["frame_index"]
            if representative_frame_indices[tracking_state] is None:
                representative_frame_indices[tracking_state] = frame_index

        # Observation 목록을 순회해 상태별 프레임 수와 정합성을 계산한다.
        observation_count = len(target_observations)
        detected_frame_count = 0
        no_candidate_count = 0
        ambiguous_candidate_count = 0
        tracking_state_count = len(tracking_state_sequence)

        for observation in target_observations:
            status = observation["status"]

            if status == STATUS_DETECTED:
                detected_frame_count += 1
            elif status == STATUS_NO_CANDIDATE:
                no_candidate_count += 1
            elif status == STATUS_AMBIGUOUS:
                ambiguous_candidate_count += 1
            else:
                raise ValueError(f"알 수 없는 타겟 관찰 상태입니다: {status}")

        # 후보 없음과 후보 여러 개는 원인이 다르지만, 둘 다 Target 하나를 결정하지 못한 상태다.
        missing_frame_count = no_candidate_count + ambiguous_candidate_count
        categorized_observation_count = detected_frame_count + missing_frame_count

        # 아래 집계는 현재 검출 규칙으로 분류한 Frame 수다. 사람의 정답과 비교한 정확도가 아니다.
        on_target_frame_count = 0
        off_target_frame_count = 0
        tracking_missing_frame_count = 0

        for tracking_state_observation in tracking_state_sequence:
            tracking_state = tracking_state_observation["tracking_state"]

            if tracking_state == TRACKING_STATE_ON_TARGET:
                on_target_frame_count += 1
            elif tracking_state == TRACKING_STATE_OFF_TARGET:
                off_target_frame_count += 1
            elif tracking_state == TRACKING_STATE_MISSING:
                tracking_missing_frame_count += 1
            else:
                raise ValueError(f"알 수 없는 트래킹 상태입니다: {tracking_state}")

        categorized_tracking_state_count = (
            on_target_frame_count
            + off_target_frame_count
            + tracking_missing_frame_count
        )

        # 시간 순으로 첫 ON_TARGET만 찾는다. break로 탐색을 끝내므로 이후 ON_TARGET으로 덮어쓰지 않는다.
        first_on_target_observation = None

        for tracking_state_observation in tracking_state_sequence:
            if (
                tracking_state_observation["tracking_state"]
                == TRACKING_STATE_ON_TARGET
            ):
                first_on_target_observation = tracking_state_observation
                break

        # ON_TARGET이 한 번도 없으면 None을 유지한다. 0초라는 유효한 결과와 구분하기 위한 처리다.
        first_on_target_frame_index = None
        first_on_target_frame_time_seconds = None
        first_on_target_run_relative_time_seconds = None

        if first_on_target_observation is not None:
            first_on_target_frame_index = first_on_target_observation[
                "frame_index"
            ]
            first_on_target_frame_time_seconds = first_on_target_observation[
                "frame_time_seconds"
            ]
            first_on_target_run_relative_time_seconds = (
                first_on_target_frame_time_seconds
                - known_run_start_seconds
            )

        first_on_target_observed = first_on_target_observation is not None

        # 최초 ON_TARGET을 기준으로 Run의 초기 확보 구간과 유지 구간의 경계를 요약한다.
        # 이 Summary는 연속 OFF_TARGET Event나 Event Duration을 계산한 결과가 아니다.
        run_phase_summary = {
            "first_on_target_observed": first_on_target_observed,
            "phase_boundary_frame_index": first_on_target_frame_index,
            "phase_boundary_time_seconds": first_on_target_frame_time_seconds,
            "initial_acquisition_duration_seconds": (
                first_on_target_run_relative_time_seconds
            ),
        }

        # 구간에 실제 Frame이 있을 때만 첫/마지막 Frame 시간을 계산한다.
        if (
            first_segment_frame_index is not None
            and last_segment_frame_index is not None
        ):
            first_segment_frame_time_seconds = first_segment_frame_index / video_fps
            last_segment_frame_time_seconds = last_segment_frame_index / video_fps

        # 단일 Target 결정률은 검출 가능 비율이다. 구간이 비어 있으면 0으로 나누지 않고 None으로 둔다.
        if run_segment_frame_count == 0:
            single_target_decision_rate = None
        else:
            single_target_decision_rate = (
                detected_frame_count / run_segment_frame_count
            )

        # 완료 여부를 출력만 하지 않고, 불완전한 Run이면 정상 결과를 반환하지 않는다.
        expected_frame_count = round(RUN_DURATION_SECONDS * video_fps)
        if frame_coverage_end_seconds < run_end_seconds:
            raise RuntimeError("Run 종료 시각까지 디코딩하지 못했습니다.")
        if run_segment_frame_count != expected_frame_count:
            raise RuntimeError(f"Run Frame 수가 다릅니다: {run_segment_frame_count} != {expected_frame_count}")
        if not (
            categorized_observation_count
            == observation_count
            == categorized_tracking_state_count
            == tracking_state_count
            == run_segment_frame_count
        ):
            raise RuntimeError("Raw Observation / Tracking State / Run Frame 수가 일치하지 않습니다.")
        if tracking_missing_frame_count != missing_frame_count:
            raise RuntimeError("Tracking MISSING과 Raw 미결정 수가 일치하지 않습니다.")

        # Phase 3는 이 Sequence를 재사용한다. Event·Duration Metric은 여기서 계산하지 않는다.
        return {
            "summary": {
                "detection_policy": DETECTION_POLICY,
                "video_path": str(VIDEO_PATH.resolve()),
                "fps": video_fps,
                "frame_width": int(video_width),
                "frame_height": int(video_height),
                "decoded_frame_count": decoded_frame_count,
                "reported_frame_count": reported_frame_count,
                "run_start_seconds": known_run_start_seconds,
                "run_end_seconds": run_end_seconds,
                "first_segment_frame_index": first_segment_frame_index,
                "last_segment_frame_index": last_segment_frame_index,
                "first_segment_frame_time_seconds": first_segment_frame_time_seconds,
                "last_segment_frame_time_seconds": last_segment_frame_time_seconds,
                "frame_coverage_end_seconds": frame_coverage_end_seconds,
                "run_segment_frame_count": run_segment_frame_count,
                "raw_observation_count": observation_count,
                "tracking_state_sequence_count": tracking_state_count,
                "state_counts": {
                    TRACKING_STATE_ON_TARGET: on_target_frame_count,
                    TRACKING_STATE_OFF_TARGET: off_target_frame_count,
                    TRACKING_STATE_MISSING: tracking_missing_frame_count,
                },
                "missing_candidate_counts": {
                    "no_candidate": no_candidate_count,
                    "ambiguous": ambiguous_candidate_count,
                },
                "single_target_decision_rate": single_target_decision_rate,
                "representative_frame_indices": representative_frame_indices,
            },
            "raw_observations": target_observations,
            "tracking_state_sequence": tracking_state_sequence,
            "run_phase_summary": run_phase_summary,
        }

    finally:
        # 중간에 예외가 발생해도 비디오 파일 핸들은 반드시 해제한다.
        video_capture.release()


def print_run_summary(summary: dict) -> None:
    """반복 Debug 출력 대신 최종 정책과 상태·Frame 수를 한 번씩 표시한다."""
    print(f"Detection Contract: {summary['detection_policy']}")
    print(f"Run Frame: {summary['first_segment_frame_index']}~{summary['last_segment_frame_index']}")
    print(f"Total Frames: {summary['run_segment_frame_count']}")
    for state, count in summary["state_counts"].items():
        print(f"{state}: {count}")
    print(f"Raw Observation Count: {summary['raw_observation_count']}")
    print(f"Tracking State Sequence Count: {summary['tracking_state_sequence_count']}")
    consistent = (
        summary["raw_observation_count"]
        == summary["tracking_state_sequence_count"]
        == summary["run_segment_frame_count"]
        == sum(summary["state_counts"].values())
    )
    print(f"Run Frame / Raw Observation / Tracking State 정합성: {'PASS' if consistent else 'FAIL'}")


def main() -> None:
    print_run_summary(analyze_run()["summary"])


# 직접 실행할 때만 전체 Run을 처리한다. import만으로 분석을 실행하지 않는다.
if __name__ == "__main__":
    main()
