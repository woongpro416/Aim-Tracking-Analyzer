import cv2
from pathlib import Path
import math


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = PROJECT_ROOT / "data" / "raw" / "woong01.mp4"


def main():
    if not VIDEO_PATH.exists():
        raise FileNotFoundError("비디오 파일이 존재하지 않습니다.")
    if not VIDEO_PATH.is_file():
        raise ValueError("올바른 비디오 파일이 아닙니다.")

    print(f"{VIDEO_PATH.resolve()} 파일을 성공적으로 확인했습니다.")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))

    try:
        if not video_capture.isOpened():
            raise RuntimeError("비디오 파일을 열 수 없습니다.")
        print("Video Open에 성공했습니다.")

        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        print(f"FPS: {video_fps}")
        print(f"FPS Type: {type(video_fps)}")

        video_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Width: {video_width}")
        print(f"Height: {video_height}")

        reported_frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
        print(reported_frame_count)

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


        decoded_frame_count = 0

        while True:
            read_success, frame = video_capture.read()

            if not read_success:
                break
            decoded_frame_count += 1

        print(f"Reported Frame Count: {reported_frame_count}")
        print(f"Decoded Frame Count: {decoded_frame_count}")

    finally:
        video_capture.release()


if __name__ == "__main__":
    main()
