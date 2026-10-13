import math
from collections.abc import Iterable
from pathlib import Path
from pprint import pprint

# OpenCV는 영상 처리, NumPy는 Closing에 사용할 작은 배열(Kernel)을 담당한다.
import cv2
import numpy as np

from tracking_state import classify_tracking_state

from target_detection import (
    LOWER_HSV,
    MIN_CANDIDATE_AREA,
    UPPER_HSV,
    CLOSING_KERNEL_SIZE,
    close_target_mask,
    create_target_mask,
    filter_target_candidates,
    is_top_strip_candidate,
)


# 대표 프레임의 원본 Mask와 Closing 결과를 비교하는 실험용 검사 스크립트다.
# Original / Closing-only는 비교 기준으로 보존한다. Shape 계산은 Deferred 관찰 도구다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 764번은 5×5 Closing 후 상단 조각이 유효 후보로 늘어난 사례다.
# 이 번호만 바꾸면 입력·출력 파일명이 함께 바뀐다.
FRAME_INDEX = 764
IMAGE_PATH = PROJECT_ROOT / "outputs" / f"representative_frame_{FRAME_INDEX}.png"
MASK_OUTPUT_PATH = PROJECT_ROOT / "outputs" / f"target_mask_{FRAME_INDEX}.png"
CLOSED_3X3_OUTPUT_PATH = PROJECT_ROOT / "outputs" / f"closed_mask_{FRAME_INDEX}_3x3.png"
CLOSED_5X5_OUTPUT_PATH = PROJECT_ROOT / "outputs" / f"closed_mask_{FRAME_INDEX}_5x5.png"


def collect_valid_candidates(mask: np.ndarray) -> list[np.ndarray]:
    """기존 Mask 검사 인터페이스를 유지하며 Production 후보 필터를 재사용한다."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return filter_target_candidates(contours)


def collect_area_candidates(contours: Iterable[np.ndarray]) -> list[np.ndarray]:
    """Original과 Closing-only는 기존 면적 조건만 적용하는 실험 기준이다."""
    candidates = []
    for contour in contours:
        if cv2.contourArea(contour) >= MIN_CANDIDATE_AREA:
            candidates.append(contour)
    return candidates


def summarize_candidates(candidates: list[np.ndarray], crosshair_center: tuple[int, int]) -> dict:
    """세 Baseline의 단일 후보 선택과 상태 분류를 같은 규칙으로 요약한다."""
    selected_contour = candidates[0] if len(candidates) == 1 else None
    return {
        "valid_candidate_count": len(candidates),
        "tracking_state": classify_tracking_state(selected_contour, crosshair_center),
    }


def calculate_aspect_ratio(
    bbox: tuple[int, int, int, int],
) -> float:
    """(x, y, width, height) 사각형에서 너비/높이를 계산한다."""
    # bbox 자체를 네 변수로 나눈다. 위치인 x, y는 이 비율 계산에 사용하지 않는다.
    x, y, width, height = bbox
    # 길이가 잘못된 사각형은 계산을 진행하지 않고 명시적으로 알린다.
    if width <= 0 or height <= 0:
        raise ValueError("너비와 높이는 0 이하일 수 없습니다.")
    # 1.0이면 너비와 높이가 같다. 정사각형도 1.0이므로 이것만으로 원이라고 판단하지 않는다.
    ratio = width / height
    # print는 화면에 보여주고, return은 다른 코드가 사용할 계산값을 돌려준다.
    return ratio


def calculate_circularity(contour: np.ndarray) -> float:
    """Contour의 면적과 닫힌 둘레 길이로 원형도(Circularity)를 계산한다."""
    # True는 마지막 점과 첫 점을 연결한 닫힌 윤곽선의 둘레를 계산하라는 뜻이다.
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    # 둘레가 0이면 아래 나눗셈을 할 수 없으므로 유효하지 않은 입력으로 처리한다.
    if perimeter <= 0:
        raise ValueError("perimeter 는 0 이하일 수 없습니다.")

    # 4π × 면적 / 둘레²: 이상적인 원은 1이며, 실제 픽셀 윤곽선에서는 값이 달라질 수 있다.
    # 현재는 값을 관찰하는 단계다. 이 값으로 후보를 제외하는 Threshold는 아직 정하지 않았다.
    circularity = (4 * math.pi * area) / (perimeter * perimeter)

    return circularity


def compare_frame(frame: np.ndarray) -> dict:
    """Production 변경과 관계없이 Original / Closing-only / Closing+Top-strip을 비교한다."""
    mask = create_target_mask(frame)
    height, width = frame.shape[:2]
    crosshair_center = (width // 2, height // 2)

    # Original은 detect_target()을 호출하지 않는다. HSV + 면적 기준을 독립적으로 보존한다.
    original_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    original_candidates = collect_area_candidates(original_contours)

    closed_mask = close_target_mask(mask)
    closed_contours, _ = cv2.findContours(closed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    closing_only_candidates = collect_area_candidates(closed_contours)
    closing_top_strip_candidates = filter_target_candidates(closed_contours)

    return {
        "original": summarize_candidates(original_candidates, crosshair_center),
        "closing_only": summarize_candidates(closing_only_candidates, crosshair_center),
        "closing_top_strip": summarize_candidates(closing_top_strip_candidates, crosshair_center),
    }


def main() -> None:
    # 대표 프레임이 없으면 선행 스크립트의 실행 순서를 안내한다.
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            "대표 프레임이 없습니다. inspect_target_frame.py의 REPRESENTATIVE_FRAME_INDEX를 "
            f"{FRAME_INDEX}로 맞춰 먼저 추출하세요: "
            f"{IMAGE_PATH}"
        )
    if not IMAGE_PATH.is_file():
        raise ValueError(f"대표 프레임 경로가 파일이 아닙니다: {IMAGE_PATH}")

    # imread()가 반환하는 이미지 배열은 BGR 순서다. 읽기에 실패하면 None이 반환된다.
    frame = cv2.imread(str(IMAGE_PATH))
    if frame is None:
        raise ValueError(f"대표 프레임 이미지를 읽을 수 없습니다: {IMAGE_PATH}")

    # 실제 검출 코드와 같은 함수로 단일 채널 마스크를 생성한다.
    mask = create_target_mask(frame)

    # Kernel 크기만 달리해 같은 원본 Mask에 Closing을 적용한다.
    # main()의 Mask는 이미지 저장과 Shape 관찰용이다. 비교 상태 계산은 compare_frame()이 맡는다.
    kernel_3x3 = np.ones((3, 3), dtype=np.uint8)
    kernel_5x5 = np.ones((CLOSING_KERNEL_SIZE, CLOSING_KERNEL_SIZE), dtype=np.uint8)

    closed_mask_3x3 = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_3x3,
    )

    closed_mask_5x5 = close_target_mask(mask)

    # 입력 이미지 크기와 정수 중앙점을 출력해 검사 대상의 좌표 기준을 확인한다.
    height, width = frame.shape[:2]

    crosshair_x = width // 2
    crosshair_y = height // 2
    crosshair_center = (crosshair_x, crosshair_y)

    print("높이와 너비: ", height, width)
    print("Crosshair 중심점: ", crosshair_center)

    # 단일 Frame에서는 누적 Count 대신 실제 후보 수와 상태를 한 번 출력한다.
    comparison_results = compare_frame(frame)
    print("Baseline 비교 결과:")
    pprint(comparison_results, sort_dicts=False)

    # Shape 관찰에는 상단 Noise도 포함해야 하므로 면적 조건만 적용한 후보를 모은다.
    closed_contours, _ = cv2.findContours(
        closed_mask_5x5,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    closing_only_candidates = []

    # Top-strip 적용 전 후보를 다시 모아, 제거 대상 Noise의 Shape 값도 관찰한다.
    for contour in closed_contours:
        area = cv2.contourArea(contour)

        if area >= MIN_CANDIDATE_AREA:
            closing_only_candidates.append(contour)

    print("\nClosing-only 후보별 Shape 정보:")
    # 후보마다 사각형·비율·면적·둘레·원형도를 표시한다. 아직 Shape로 후보를 제거하지 않는다.
    for contour in closing_only_candidates:
        bbox = cv2.boundingRect(contour)

        ratio = calculate_aspect_ratio(bbox)
        print("Bounding Box: ", bbox, "Aspect Ratio: ", ratio)

        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        print("Area: ", area, "Perimeter: ", perimeter)
        print("Circularity:", calculate_circularity(contour))

    # Mask는 (높이, 너비)의 단일 채널 배열이다. 색상 조건과 Kernel도 함께 남겨 실험 조건을 확인한다.
    print(f"마스크 크기(높이, 너비): {mask.shape}")
    print(f"마스크 자료형(dtype): {mask.dtype}")
    print(f"HSV 하한값: {LOWER_HSV.tolist()}")
    print(f"HSV 상한값: {UPPER_HSV.tolist()}")
    print(f"3x3 Kernel 형태/자료형: {kernel_3x3.shape}, {kernel_3x3.dtype}")
    print(f"5x5 Kernel 형태/자료형: {kernel_5x5.shape}, {kernel_5x5.dtype}")

    # 선택한 Frame 번호로 세 Mask를 저장해 시각적으로 비교한다.
    MASK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mask_save_success = cv2.imwrite(
        str(MASK_OUTPUT_PATH),
        mask,
    )

    # imwrite()의 성공 여부를 확인한다. 저장 실패를 정상 완료로 처리하지 않는다.
    if not mask_save_success:
        raise RuntimeError(f"타겟 마스크를 저장하지 못했습니다: {MASK_OUTPUT_PATH}")

    print(f"타겟 마스크 저장 경로: {MASK_OUTPUT_PATH}")

    # 3×3 결과는 Day 10 비교 자료로 유지한다. 세 방식의 상태 비교에는 5×5만 사용한다.
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

    # 5×5 결과를 저장해 Target의 끊긴 부분과 상단 Noise가 어떻게 변했는지 눈으로 확인한다.
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


# 파일을 직접 실행할 때만 검사한다. 테스트에서 함수를 import할 때는 이미지 저장을 수행하지 않는다.
if __name__ == "__main__":
    main()
