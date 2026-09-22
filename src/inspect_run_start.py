import math
from pathlib import Path

import cv2


# 원본 영상을 한 프레임씩 확인해 60초 Run의 시작 프레임을 수동으로 찾는다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = PROJECT_ROOT / "data" / "raw" / "woong01.mp4"


def main() -> None:
    # OpenCV에 전달하기 전에 입력 경로가 실제 파일인지 확인한다.
    if not VIDEO_PATH.exists():
        raise FileNotFoundError("비디오 파일이 존재하지 않습니다.")
    if not VIDEO_PATH.is_file():
        raise ValueError("올바른 비디오 파일이 아닙니다.")

    print(f"{VIDEO_PATH.resolve()} 비디오 파일을 확인했습니다.")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))

    try:
        # 영상 열기와 시간 계산에 필요한 FPS를 검증한다.
        if not video_capture.isOpened():
            raise RuntimeError("비디오 파일을 열 수 없습니다.")
        print("비디오 파일 열기에 성공했습니다.")

        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        frame_index = 0
        selected_frame_index = None

        if not math.isfinite(video_fps) or video_fps <= 0:
            raise ValueError("FPS는 0보다 큰 유한한 숫자여야 합니다.")

        print("조작: [아무 키] 다음 프레임 | [s] 에임 트래킹 분석 시작 프레임 선택 | [q] 종료")

        # 사용자가 s를 누를 때까지 프레임을 순서대로 표시한다.
        while True:
            read_success, frame = video_capture.read()

            if not read_success:
                break

            frame_time_seconds = frame_index / video_fps
            print(
                f"현재 프레임 인덱스: {frame_index} | "
                f"녹화 기준 시간(초): {frame_time_seconds:.6f}"
            )

            # 원본 비율을 유지한 1280x720 미리보기로 화면에 표시한다.
            display_frame = cv2.resize(
                frame,
                (1280, 720),
                interpolation=cv2.INTER_AREA,
            )
            cv2.imshow("에임 트래킹 분석 시작 프레임 확인", display_frame)
            pressed_key = cv2.waitKey(0)

            if pressed_key == ord("s"):
                selected_frame_index = frame_index
                break

            if pressed_key == ord("q"):
                break

            frame_index += 1

        if selected_frame_index is None:
            print("프레임이 선택되지 않았습니다.")
            return

        # 선택한 프레임 인덱스를 원본 영상 기준 시간으로 변환한다.
        selected_run_start_seconds = selected_frame_index / video_fps

        print(f"선택한 에임 트래킹 분석 시작 프레임 인덱스: {selected_frame_index}")
        print(f"선택한 에임 트래킹 분석 시작 시간(초): {selected_run_start_seconds}")

    finally:
        # 중간 종료나 예외가 발생해도 영상과 창 자원을 정리한다.
        video_capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
