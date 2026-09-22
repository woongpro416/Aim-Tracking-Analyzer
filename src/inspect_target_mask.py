from pathlib import Path

import cv2

from target_detection import LOWER_HSV, UPPER_HSV, create_target_mask


# 대표 프레임에 HSV 범위를 적용한 이진 마스크를 저장하고 형태를 확인한다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_PATH = PROJECT_ROOT / "outputs" / "representative_frame_1256.png"
MASK_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "target_mask_1256.png"

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

    # 실제 검출 코드와 같은 함수로 단일 채널 마스크를 생성한다.
    mask = create_target_mask(frame)

    print(f"마스크 크기(높이, 너비): {mask.shape}")
    print(f"마스크 자료형(dtype): {mask.dtype}")
    print(f"HSV 하한값: {LOWER_HSV.tolist()}")
    print(f"HSV 상한값: {UPPER_HSV.tolist()}")

    # 고정된 파일명으로 저장해 재실행 시 이미지가 계속 누적되지 않게 한다.
    MASK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mask_save_success = cv2.imwrite(
        str(MASK_OUTPUT_PATH),
        mask,
    )

    if not mask_save_success:
        raise RuntimeError(f"타겟 마스크를 저장하지 못했습니다: {MASK_OUTPUT_PATH}")

    print(f"타겟 마스크 저장 경로: {MASK_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
