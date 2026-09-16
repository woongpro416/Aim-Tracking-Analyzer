import cv2
from pathlib import Path


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
    finally:
        video_capture.release()

if __name__ == "__main__":
    main()
