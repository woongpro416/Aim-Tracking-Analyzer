import cv2
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = PROJECT_ROOT / "data" / "raw" / "woong01.mp4"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "representative_frame_1256.png"
REPRESENTATIVE_FRAME_INDEX = 1256


def main():

    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"비디오 파일을 찾을 수 없습니다: {VIDEO_PATH}")
    if not VIDEO_PATH.is_file():
        raise ValueError(f"비디오 경로가 파일이 아닙니다: {VIDEO_PATH}")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))


    try:
        if not video_capture.isOpened():
            raise RuntimeError(f"비디오 파일을 열 수 없습니다: {VIDEO_PATH}")

        video_fps = video_capture.get(cv2.CAP_PROP_FPS)

        if video_fps <= 0:
            raise ValueError(f"FPS 메타데이터가 0 이하입니다: {video_fps}")


        frame_index = 0
        frame_found = False

        while True:
            read_success, frame = video_capture.read()
            if not read_success:
                break

            if frame_index == REPRESENTATIVE_FRAME_INDEX:
                frame_time_seconds = frame_index / video_fps
                print(f"대표 프레임 인덱스: {frame_index}")
                print(f"프레임 크기(높이, 너비, 채널): {frame.shape}")
                print(f"프레임 자료형(dtype): {frame.dtype}")
                print(f"녹화 기준 프레임 시간(초): {frame_time_seconds}")

                save_success = cv2.imwrite(str(OUTPUT_PATH), frame)

                if not save_success:
                    raise RuntimeError(
                        f"대표 프레임을 저장하지 못했습니다: {OUTPUT_PATH}"
                    )


                frame_found = True
                print(f"대표 프레임 저장 경로: {OUTPUT_PATH}")
                break

            frame_index += 1

        if frame_found is False:
            raise RuntimeError(
                "비디오 디코딩이 끝날 때까지 목표 프레임을 찾지 못했습니다: "
                f"목표 인덱스={REPRESENTATIVE_FRAME_INDEX}, "
                f"마지막 확인 인덱스={frame_index - 1}"
            )

    finally:
        video_capture.release()


if __name__ == "__main__":
    main()
