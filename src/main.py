import math
from pathlib import Path

import cv2

from target_detection import detect_target
from tracking_state import (
    classify_tracking_state,
    TRACKING_STATE_MISSING,
    TRACKING_STATE_OFF_TARGET,
    TRACKING_STATE_ON_TARGET,
)


# 프로젝트 입력 영상과 분석할 Run 구간을 정의한다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = PROJECT_ROOT / "data" / "raw" / "woong01.mp4"
RUN_DURATION_SECONDS = 60.0
KNOWN_RUN_START_SECONDS = 5.933333333333334

# Observation에 기록하는 상태값을 한곳에서 관리해 오타와 중복을 방지한다.
STATUS_DETECTED = "타겟 검출됨"
STATUS_NO_CANDIDATE = "타겟 미결정: 유효 후보 없음"
STATUS_AMBIGUOUS = "타겟 미결정: 유효 후보 여러 개"


def main() -> None:
    # OpenCV에 전달하기 전에 입력 경로가 실제 파일인지 확인한다.
    if not VIDEO_PATH.exists():
        raise FileNotFoundError("비디오 파일이 존재하지 않습니다.")
    if not VIDEO_PATH.is_file():
        raise ValueError("올바른 비디오 파일이 아닙니다.")

    print(f"{VIDEO_PATH.resolve()} 비디오 파일을 확인했습니다.")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))

    try:
        # 비디오를 열고 분석에 필요한 메타데이터를 읽는다.
        if not video_capture.isOpened():
            raise RuntimeError("비디오 파일을 열 수 없습니다.")

        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        video_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        reported_frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)

        print("비디오 파일 열기에 성공했습니다.")
        print(f"초당 프레임 수(FPS): {video_fps}")
        print(f"FPS 값의 자료형: {type(video_fps)}")
        print(f"영상 너비(픽셀): {video_width}")
        print(f"영상 높이(픽셀): {video_height}")

        # 잘못된 메타데이터로 시간이나 프레임 위치를 계산하지 않도록 검증한다.
        if not math.isfinite(video_fps) or video_fps <= 0:
            raise ValueError("FPS는 0보다 큰 유한한 숫자여야 합니다.")
        if not math.isfinite(video_width) or video_width <= 0:
            raise ValueError("영상 너비는 0보다 큰 유한한 숫자여야 합니다.")
        if not math.isfinite(video_height) or video_height <= 0:
            raise ValueError("영상 높이는 0보다 큰 유한한 숫자여야 합니다.")
        if video_fps != 60.0:
            raise ValueError(f"지원하지 않는 FPS입니다. 실제 FPS: {video_fps}")

        # Crosshair의 좌표를 계산한다.
        crosshair_x = int(video_width) // 2
        crosshair_y = int(video_height) // 2
        crosshair_point = (crosshair_x, crosshair_y)

        if crosshair_x <= 0 or crosshair_y <= 0:
            raise ValueError("크로스헤어 좌표는 0 이하일 수 없습니다.")
        print(f"크로스헤어 X 좌표: {crosshair_x}")
        print(f"크로스헤어 Y 좌표: {crosshair_y}")

        # 알려진 시작 시각으로부터 60초 분석 구간의 끝을 계산한다.
        known_run_start_seconds = KNOWN_RUN_START_SECONDS
        if known_run_start_seconds is None:
            raise ValueError("시작 위치가 존재하지 않습니다.")
        if not math.isfinite(known_run_start_seconds):
            raise ValueError("시작 위치는 유한한 숫자여야 합니다.")
        if known_run_start_seconds < 0:
            raise ValueError("시작 위치는 음수일 수 없습니다.")

        run_end_seconds = known_run_start_seconds + RUN_DURATION_SECONDS
        print(f"검증용 에임 트래킹 분석 시작 시간(초): {known_run_start_seconds}")
        print(f"에임 트래킹 분석 종료 시간(초): {run_end_seconds}")

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
        tracking_state_sequence = []

        # 영상을 처음부터 한 번만 순차 디코딩하고, Run 구간만 타겟 검출한다.
        while True:
            read_success, frame = video_capture.read()
            if not read_success:
                break

            current_frame_index = decoded_frame_count
            frame_time_seconds = current_frame_index / video_fps

            if known_run_start_seconds <= frame_time_seconds < run_end_seconds:
                if first_segment_frame_index is None:
                    first_segment_frame_index = current_frame_index

                last_segment_frame_index = current_frame_index
                run_segment_frame_count += 1

                (
                    detected,
                    _bounding_box,
                    center,
                    _contour_count,
                    valid_candidate_count,
                    selected_contour,
                ) = detect_target(frame)

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

                observation = {
                    "frame_index": current_frame_index,
                    "frame_time_seconds": frame_time_seconds,
                    "status": status,
                    "center": center,
                    "valid_candidate_count": valid_candidate_count,
                }
                target_observations.append(observation)

                tracking_state_observation = {
                    "frame_index": current_frame_index,
                    "frame_time_seconds": frame_time_seconds,
                    "tracking_state": tracking_state,
                }

                tracking_state_sequence.append(tracking_state_observation)

            decoded_frame_count += 1
            frame_coverage_end_seconds = (current_frame_index + 1) / video_fps

        # 상태별 첫 등장 인덱스를 보존해 수동 검증할 프레임을 찾는다.
        representative_frame_indices = {
            TRACKING_STATE_ON_TARGET: None,
            TRACKING_STATE_OFF_TARGET: None,
            TRACKING_STATE_MISSING: None,
        }

        # Sequence의 시간 순서를 이용해 각 상태의 첫 인덱스만 기록한다.
        for observation in tracking_state_sequence:
            tracking_state = observation["tracking_state"]
            frame_index = observation["frame_index"]
            if representative_frame_indices[tracking_state] is None:
                representative_frame_indices[tracking_state] = frame_index

        # 최초 인덱스는 검증용 출력이며 상태별 전체 Count와는 별개다.
        print(representative_frame_indices)


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

        missing_frame_count = no_candidate_count + ambiguous_candidate_count
        categorized_observation_count = detected_frame_count + missing_frame_count

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

        first_on_target_observation = None

        for tracking_state_observation in tracking_state_sequence:
            if (
                tracking_state_observation["tracking_state"]
                == TRACKING_STATE_ON_TARGET
            ):
                first_on_target_observation = tracking_state_observation
                break

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

        run_phase_summary = {
            "first_on_target_observed": first_on_target_observed,
            "phase_boundary_frame_index": first_on_target_frame_index,
            "phase_boundary_time_seconds": first_on_target_frame_time_seconds,
            "initial_acquisition_duration_seconds": (
                first_on_target_run_relative_time_seconds
            ),
        }

        if (
            first_segment_frame_index is not None
            and last_segment_frame_index is not None
        ):
            first_segment_frame_time_seconds = first_segment_frame_index / video_fps
            last_segment_frame_time_seconds = last_segment_frame_index / video_fps

        if run_segment_frame_count == 0:
            single_target_decision_rate = None
        else:
            single_target_decision_rate = (
                detected_frame_count / run_segment_frame_count
            )

        # Observation 개수와 상태 집계가 서로 일치하는지 출력한다.
        print("\n[타겟 관찰 검증]")
        print(f"타겟 관찰 프레임 수: {observation_count}")
        print(
            "분석 구간 프레임 수와 관찰 프레임 수가 같은가?: "
            f"{observation_count == run_segment_frame_count}"
        )
        print(f"상태별 프레임 수 합계: {categorized_observation_count}")
        print(
            "상태별 프레임 수 합계와 전체 관찰 프레임 수가 같은가?: "
            f"{categorized_observation_count == observation_count}"
        )

        # 분석 결과가 카운트 되고 있는지 확인
        print("\n[트래킹 상태 시퀀스 검증]")
        print(f"트래킹 상태 프레임 수: {tracking_state_count}")
        print(
            "타겟 관찰 프레임 수와 트래킹 상태 프레임 수가 같은가?: "
            f"{tracking_state_count == observation_count}"
        )
        print(
            "분석 구간 프레임 수와 트래킹 상태 프레임 수가 같은가?: "
            f"{tracking_state_count == run_segment_frame_count}"
        )

        if target_observations:
            print(f"첫 번째 타겟 관찰: {target_observations[0]}")
            print(f"마지막 타겟 관찰: {target_observations[-1]}")

        # 유효 후보가 정확히 하나인 프레임과 미결정 원인을 구분해 출력한다.
        print("\n[타겟 검출 통계]")
        print(f"단일 타겟 결정 프레임 수: {detected_frame_count}")
        print(f"타겟 미결정 프레임 수: {missing_frame_count}")
        print(f"유효 후보 없음 프레임 수: {no_candidate_count}")
        print(f"유효 후보 여러 개 프레임 수: {ambiguous_candidate_count}")
        if single_target_decision_rate is None:
            print("단일 타겟 결정률: 계산할 수 없음")
        else:
            print(f"단일 타겟 결정률: {single_target_decision_rate:.2%}")

        # 요청한 60초 구간이 실제 디코딩 범위에 포함됐는지 확인한다.
        print("\n[분석 구간 및 디코딩 검증]")
        if frame_coverage_end_seconds >= run_end_seconds:
            print("에임 트래킹 분석 구간 완성 상태: 완료")
        else:
            print("에임 트래킹 분석 구간 완성 상태: 미완료")
            print("필요한 분석 종료 시간까지 프레임을 디코딩하지 못했습니다.")

        print(f"분석 구간의 첫 프레임 인덱스: {first_segment_frame_index}")
        print(f"분석 구간의 마지막 프레임 인덱스: {last_segment_frame_index}")
        print(f"분석 구간의 첫 프레임 시간(초): {first_segment_frame_time_seconds}")
        print(f"분석 구간의 마지막 프레임 시간(초): {last_segment_frame_time_seconds}")
        print(f"분석 구간 프레임 수: {run_segment_frame_count}")
        print(f"메타데이터에 기록된 전체 프레임 수: {reported_frame_count}")
        print(f"성공적으로 디코딩한 전체 프레임 수: {decoded_frame_count}")
        print(f"성공적으로 디코딩한 시간 범위의 끝(초): {frame_coverage_end_seconds}")

        print("\n[트래킹 상태 통계]")
        print(f"ON_TARGET 프레임 수: {on_target_frame_count}")
        print(f"OFF_TARGET 프레임 수: {off_target_frame_count}")
        print(f"MISSING 프레임 수: {tracking_missing_frame_count}")
        print(f"트래킹 상태별 프레임 수 합계: {categorized_tracking_state_count}")
        print(
            "트래킹 상태별 합계와 전체 트래킹 상태 수가 같은가?: "
            f"{categorized_tracking_state_count == tracking_state_count}"
        )
        print(
            "트래킹 상태별 합계와 분석 구간 프레임 수가 같은가?: "
            f"{categorized_tracking_state_count == run_segment_frame_count}"
        )
        print(
            "트래킹 MISSING 수와 Raw 미결정 수가 같은가?: "
            f"{tracking_missing_frame_count == missing_frame_count}"
        )

        print("\n[최초 온타겟 및 실행 구간 단계 요약]")
        print(
            "최초 온타겟 관찰 여부: "
            f"{run_phase_summary['first_on_target_observed']}"
        )
        print(
            "단계 경계 프레임 인덱스: "
            f"{run_phase_summary['phase_boundary_frame_index']}"
        )
        print(
            "단계 경계 시간(초): "
            f"{run_phase_summary['phase_boundary_time_seconds']}"
        )
        print(
            "최초 온타겟 실행 구간 상대 시간(초): "
            f"{first_on_target_run_relative_time_seconds}"
        )
        print(
            "초기 확보 구간 지속시간(초): "
            f"{run_phase_summary['initial_acquisition_duration_seconds']}"
        )

    finally:
        # 중간에 예외가 발생해도 비디오 파일 핸들은 반드시 해제한다.
        video_capture.release()


if __name__ == "__main__":
    main()
