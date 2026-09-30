from pathlib import Path

import cv2
import numpy as np

from target_detection import (
    LOWER_HSV,
    MIN_CANDIDATE_AREA,
    UPPER_HSV,
    create_target_mask,
)

# 대표 프레임의 원본 Mask와 Closing 결과를 비교하는 실험용 검사 스크립트다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 764번은 5×5 Closing 후 상단 조각이 유효 후보로 늘어난 사례다.
IMAGE_PATH = PROJECT_ROOT / "outputs" / "representative_frame_764.png"
MASK_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "target_mask_764.png"
CLOSED_3X3_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "closed_mask_764_3x3.png"
CLOSED_5X5_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "closed_mask_764_5x5.png"


def is_top_strip_candidate(bbox: tuple[int, int, int, int]) -> bool:
    """후보 사각형 전체가 화면 맨 위 30px 안에 있는지 확인한다."""
    x, y, width, height = bbox
    hud_bottom_y = 30

    candidate_bottom_y = y + height
    if candidate_bottom_y <= hud_bottom_y:
        return True
    else:
        return False


def collect_valid_candidates(mask: np.ndarray) -> list[np.ndarray]:
    """면적과 상단 위치 기준을 통과한 Contour만 돌려준다."""
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    valid_candidates = []

    # 작은 색상 잡음을 먼저 제외하고 남은 후보의 화면 위치를 검사한다.
    for contour in contours:
        if cv2.contourArea(contour) < MIN_CANDIDATE_AREA:
            continue

        bbox = cv2.boundingRect(contour)

        # 실험: 화면 상단 30px 안에 완전히 들어간 조각은 타겟 후보에서 제외한다.
        is_top_strip = is_top_strip_candidate(bbox)
        if is_top_strip:
            continue

        valid_candidates.append(contour)

    return valid_candidates


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

    # Kernel 크기만 달리해 같은 원본 Mask에 Closing을 적용한다.
    kernel_3x3 = np.ones((3, 3), dtype=np.uint8)
    kernel_5x5 = np.ones((5, 5), dtype=np.uint8)

    closed_mask_3x3 = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_3x3,
    )

    closed_mask_5x5 = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_5x5,
    )

    # 5×5에서 면적 기준만 적용한 후보 수와 상단 제외 후 후보 수를 비교한다.
    closed_contours, _ = cv2.findContours(
        closed_mask_5x5,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    area_valid_count = sum(
        cv2.contourArea(contour) >= MIN_CANDIDATE_AREA
        for contour in closed_contours
    )
    filtered_candidates = collect_valid_candidates(closed_mask_5x5)
    print(f"5×5 Closing 면적 조건 통과 후보 수: {area_valid_count}")
    print(f"상단 조각 제외 후 후보 수: {len(filtered_candidates)}")

    print(f"마스크 크기(높이, 너비): {mask.shape}")
    print(f"마스크 자료형(dtype): {mask.dtype}")
    print(f"HSV 하한값: {LOWER_HSV.tolist()}")
    print(f"HSV 상한값: {UPPER_HSV.tolist()}")
    print(f"3×3 Kernel 형태/자료형: {kernel_3x3.shape}, {kernel_3x3.dtype}")
    print(f"5×5 Kernel 형태/자료형: {kernel_5x5.shape}, {kernel_5x5.dtype}")

    # 세 Mask를 764번 전용 파일명으로 저장해 시각적으로 비교한다.
    MASK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mask_save_success = cv2.imwrite(
        str(MASK_OUTPUT_PATH),
        mask,
    )

    if not mask_save_success:
        raise RuntimeError(f"타겟 마스크를 저장하지 못했습니다: {MASK_OUTPUT_PATH}")

    print(f"타겟 마스크 저장 경로: {MASK_OUTPUT_PATH}")

    closed_3x3_save_success = cv2.imwrite(
        str(CLOSED_3X3_OUTPUT_PATH),
        closed_mask_3x3,
    )

    if not closed_3x3_save_success:
        raise RuntimeError(
            "3×3 Closing 마스크를 저장하지 못했습니다: "
            f"{CLOSED_3X3_OUTPUT_PATH}"
        )

    print(f"3×3 Closing 마스크 저장 경로: {CLOSED_3X3_OUTPUT_PATH}")

    closed_5x5_save_success = cv2.imwrite(
        str(CLOSED_5X5_OUTPUT_PATH),
        closed_mask_5x5,
    )

    if not closed_5x5_save_success:
        raise RuntimeError(
            "5×5 Closing 마스크를 저장하지 못했습니다: "
            f"{CLOSED_5X5_OUTPUT_PATH}"
        )

    print(f"5×5 Closing 마스크 저장 경로: {CLOSED_5X5_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
