import cv2
from pathlib import Path

from target_detection import LOWER_HSV, UPPER_HSV, create_target_mask

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_PATH = PROJECT_ROOT / "outputs" / "representative_frame_1256.png"
MASK_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "target_mask_1256.png"

def main():
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"대표 프레임 이미지를 찾을 수 없습니다: {IMAGE_PATH}")
    if not IMAGE_PATH.is_file():
        raise ValueError(f"대표 프레임 경로가 파일이 아닙니다: {IMAGE_PATH}")

    frame = cv2.imread(str(IMAGE_PATH))
    if frame is None:
        raise ValueError(f"대표 프레임 이미지를 읽을 수 없습니다: {IMAGE_PATH}")

    mask = create_target_mask(frame)

    print(f"마스크 크기(높이, 너비): {mask.shape}")
    print(f"마스크 자료형(dtype): {mask.dtype}")
    print(f"HSV 하한값: {LOWER_HSV.tolist()}")
    print(f"HSV 상한값: {UPPER_HSV.tolist()}")

    mask_save_success = cv2.imwrite(
        str(MASK_OUTPUT_PATH),
        mask,
    )

    if not mask_save_success:
        raise RuntimeError(f"타겟 마스크를 저장하지 못했습니다: {MASK_OUTPUT_PATH}")

    print(f"타겟 마스크 저장 경로: {MASK_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
