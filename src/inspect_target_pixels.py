from pathlib import Path

import cv2


# inspect_target_frame.py가 만든 대표 프레임에서 색상 샘플을 확인한다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_PATH = PROJECT_ROOT / "outputs" / "representative_frame_1256.png"

SAMPLE_POINTS = {
    "타겟 내부 왼쪽": (900, 540),
    "타겟 내부 위쪽": (940, 500),
    "타겟 내부 아래쪽": (940, 590),
    "회색 배경": (700, 540),
    "청록색 UI 바": (150, 50),
}


def main() -> None:
    # 대표 프레임이 없으면 선행 스크립트의 실행 순서를 안내한다.
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            "대표 프레임이 없습니다. inspect_target_frame.py를 먼저 실행하세요: "
            f"{IMAGE_PATH}"
        )
    if not IMAGE_PATH.is_file():
        raise ValueError(f"대표 프레임 경로가 파일이 아닙니다: {IMAGE_PATH}")

    frame = cv2.imread(str(IMAGE_PATH))

    if frame is None:
        raise ValueError(f"대표 프레임 이미지를 읽을 수 없습니다: {IMAGE_PATH}")

    # 같은 픽셀을 BGR과 HSV 양쪽에서 비교할 수 있도록 색상 공간을 변환한다.
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    height, width, _channels = frame.shape

    # 좌표의 유효성을 확인한 뒤 NumPy의 [y, x] 순서로 픽셀을 읽는다.
    for label, coordinates in SAMPLE_POINTS.items():
        x, y = coordinates

        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(
                "이미지 범위를 벗어난 샘플 좌표입니다: "
                f"샘플={label}, 좌표=({x}, {y}), "
                f"이미지 크기=(너비={width}, 높이={height})"
            )

        bgr_pixel = frame[y, x]
        hsv_pixel = hsv_frame[y, x]

        print(
            f"샘플={label} | "
            f"좌표(x, y)=({x}, {y}) | "
            f"BGR 값={bgr_pixel.tolist()} | "
            f"HSV 값={hsv_pixel.tolist()}"
        )

if __name__ == "__main__":
    main()
