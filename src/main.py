import cv2
from pathlib import Path
import math


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = PROJECT_ROOT / "data" / "raw" / "woong01.mp4"
RUN_DURATION_SECONDS = 60.0
KNOWN_RUN_START_SECONDS = 5.933333333333334


def main():
    if not VIDEO_PATH.exists():
        raise FileNotFoundError("비디오 파일이 존재하지 않습니다.")
    if not VIDEO_PATH.is_file():
        raise ValueError("올바른 비디오 파일이 아닙니다.")

    print(f"{VIDEO_PATH.resolve()} 비디오 파일을 확인했습니다.")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))

    try:
        if not video_capture.isOpened():
            raise RuntimeError("비디오 파일을 열 수 없습니다.")
        print("비디오 파일 열기에 성공했습니다.")

        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        print(f"초당 프레임 수(FPS): {video_fps}")
        print(f"FPS 값의 자료형: {type(video_fps)}")

        video_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"영상 너비(픽셀): {video_width}")
        print(f"영상 높이(픽셀): {video_height}")

        reported_frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)

        if not math.isfinite(video_fps):
            raise ValueError("FPS Metadata가 유한한 숫자가 아닙니다.")

        if video_fps <= 0:
            raise ValueError("FPS는 0보다 커야 합니다.")

        if not math.isfinite(video_width):
            raise ValueError("Width가 유한한 숫자가 아닙니다.")

        if video_width <= 0:
            raise ValueError("Width는 0보다 커야 합니다.")

        if not math.isfinite(video_height):
            raise ValueError("Height가 유한한 숫자가 아닙니다.")

        if video_height <= 0:
            raise ValueError("Height는 0보다 커야 합니다.")

        if video_fps != 60.0:
            raise ValueError(f"지원하지 않는 FPS입니다. 실제 FPS: {video_fps}")

        known_run_start_seconds = KNOWN_RUN_START_SECONDS

        if known_run_start_seconds is None:
            raise ValueError("시작 위치가 존재하지 않습니다.")

        if not math.isfinite(known_run_start_seconds):
            raise ValueError("시작 위치의 숫자가 유효하지 않습니다.")

        if known_run_start_seconds < 0:
            raise ValueError("시작 위치는 음수일 수 없습니다.")

        run_end_seconds = known_run_start_seconds + RUN_DURATION_SECONDS
        print(f"검증용 에임 트래킹 분석 시작 시간(초): {known_run_start_seconds}")
        print(f"에임 트래킹 분석 종료 시간(초): {run_end_seconds}")

        decoded_frame_count = 0
        run_segment_frame_count = 0

        first_segment_frame_index = None
        first_segment_frame_time_seconds = None
        last_segment_frame_index = None
        last_segment_frame_time_seconds = None
        frame_coverage_end_seconds = 0.0

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

            decoded_frame_count += 1
            frame_coverage_end_seconds = (current_frame_index + 1) / video_fps

        if (
            first_segment_frame_index is not None 
            and last_segment_frame_index is not None
            ):
            first_segment_frame_time_seconds = first_segment_frame_index / video_fps
            last_segment_frame_time_seconds = last_segment_frame_index / video_fps

        if frame_coverage_end_seconds >= run_end_seconds:
            print("에임 트래킹 분석 구간 완성 상태: 완료")
        else:
            print("에임 트래킹 분석 구간 완성 상태: 미완료")
            print("필요한 분석 종료 시간까지 프레임을 성공적으로 디코딩하지 못했습니다.")


        print(f"분석 구간의 첫 프레임 인덱스: {first_segment_frame_index}")
        print(f"분석 구간의 마지막 프레임 인덱스: {last_segment_frame_index}")
        print(f"분석 구간의 첫 프레임 시간(초): {first_segment_frame_time_seconds}")
        print(f"분석 구간의 마지막 프레임 시간(초): {last_segment_frame_time_seconds}")
        print(f"분석 구간 프레임 수: {run_segment_frame_count}")
        print(f"메타데이터에 기록된 전체 프레임 수: {reported_frame_count}")
        print(f"성공적으로 디코딩한 전체 프레임 수: {decoded_frame_count}")
        print(f"성공적으로 디코딩한 시간 범위의 끝(초): {frame_coverage_end_seconds}")


    finally:
        video_capture.release()


if __name__ == "__main__":
    main()
