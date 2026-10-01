# Path는 실행 위치와 관계없이 프로젝트 안의 입력·출력 경로를 만드는 데 사용한다.
from pathlib import Path

# OpenCV는 영상 처리, NumPy는 Closing에 사용할 작은 배열(Kernel)을 담당한다.
import cv2
import numpy as np

# 기존 검출과 상태 판정 함수를 재사용해 실험에서도 같은 판정 기준을 유지한다.
from target_detection import detect_target
from tracking_state import classify_tracking_state

from target_detection import (
    LOWER_HSV,
    MIN_CANDIDATE_AREA,
    UPPER_HSV,
    create_target_mask,
)

# math.pi는 원형도 계산에, pprint는 중첩 Dictionary를 읽기 쉽게 출력하는 데 사용한다.
import math
from pprint import pprint


# 대표 프레임의 원본 Mask와 Closing 결과를 비교하는 실험용 검사 스크립트다.
# Closing·Top-strip·Shape 관찰은 실험이며 Production Detection Contract는 바꾸지 않는다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 764번은 5×5 Closing 후 상단 조각이 유효 후보로 늘어난 사례다.
# 검사 Frame을 바꿀 때는 입력 이미지와 세 출력 파일명의 인덱스를 함께 맞춘다.
IMAGE_PATH = PROJECT_ROOT / "outputs" / "representative_frame_764.png"
MASK_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "target_mask_764.png"
CLOSED_3X3_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "closed_mask_764_3x3.png"
CLOSED_5X5_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "closed_mask_764_5x5.png"


def is_top_strip_candidate(bbox: tuple[int, int, int, int]) -> bool:
    """후보 사각형 전체가 화면 맨 위 30px 안에 있는지 확인한다."""
    x, y, width, height = bbox
    # 30px은 현재 Noise에서 관찰한 실험 기준이며, 실제 Target의 이동 범위로 확정한 값은 아니다.
    hud_bottom_y = 30

    # y는 사각형 위쪽 위치다. 아래쪽 끝까지 30px 이내여야 사각형 전체가 상단에 포함된다.
    candidate_bottom_y = y + height
    if candidate_bottom_y <= hud_bottom_y:
        return True
    else:
        return False


def collect_valid_candidates(mask: np.ndarray) -> list[np.ndarray]:
    """면적과 상단 위치 기준을 통과한 Contour만 돌려준다."""
    # 이 함수에는 Top-strip 조건이 포함되어 있으므로 Closing-only 계산에는 사용하지 않는다.
    # 외부 윤곽선만 찾고, 윤곽선의 직선 구간은 필요한 점만 남겨 표현한다.
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

    # 후보가 없어도 None 대신 빈 목록 []을 반환하므로 호출한 쪽에서 len()으로 판단할 수 있다.
    return valid_candidates


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
    """한 화면을 세 방식으로 검사해 후보 수와 조준 상태를 반환한다."""
    # 1. 이미지 배열의 순서는 (높이, 너비, 채널)이고, 좌표의 순서는 (x, y)다.
    # //를 사용해 화면 중앙을 정수 픽셀 좌표로 만든다.
    height, width = frame.shape[:2]

    crosshair_x = width // 2
    crosshair_y = height // 2
    crosshair_center = (crosshair_x, crosshair_y)

    # 2. Original: 원본 detect_target()의 여섯 반환값을 순서대로 받는다.
    # 이 비교에서는 유효 후보 수와 선택된 Contour를 사용한다.
    (
        detected,
        bounding_box,
        center,
        contour_count,
        original_valid_candidate_count,
        original_selected_contour,
    ) = detect_target(frame)

    # 선택된 Contour가 None이면 MISSING, 중앙점이 내부/경계면 ON_TARGET, 밖이면 OFF_TARGET이다.
    original_tracking_state = classify_tracking_state(
        original_selected_contour,
        crosshair_center,
    )
    # Dictionary의 문자열 Key로 값의 의미를 표시한다. 후보 수와 상태만 담는 최소 구조다.
    original_result = {
        "valid_candidate_count": original_valid_candidate_count,
        "tracking_state": original_tracking_state,
    }


    # 3. 두 Closing 방식은 같은 HSV Mask에 같은 5×5 Closing을 적용한 결과를 사용한다.
    # ones()는 모두 1인 5×5 배열을 만들고, uint8은 8비트 정수 자료형을 뜻한다.
    mask = create_target_mask(frame)
    kernel_5x5 = np.ones((5, 5), dtype=np.uint8)
    closed_mask_5x5 = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_5x5,
    )

    # _는 여기서 사용하지 않는 윤곽선 계층 정보를 받는 변수다.
    closed_contours, _ = cv2.findContours(
        closed_mask_5x5,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    # 4. Closing-only 후보는 별도 목록에 보존한다. append()는 후보를 목록 끝에 추가한다.
    closing_only_candidates = []

    # Closing-only: 면적 조건만 적용하며, 상단 위치 조건은 적용하지 않는다.
    for contour in closed_contours:
        area = cv2.contourArea(contour)

        if area >= MIN_CANDIDATE_AREA:
            closing_only_candidates.append(contour)

    # for 반복문이 끝난 뒤 선택한다. 후보 수가 0 또는 2 이상이면 선택 결과는 None이다.
    # 목록을 Contour 하나로 덮어쓰지 않으므로 이후에도 len()으로 전체 후보 수를 확인할 수 있다.
    if len(closing_only_candidates) == 1:
        closing_only_selected_contour = closing_only_candidates[0]
    else:
        closing_only_selected_contour = None

    # 상태를 먼저 계산한 뒤 Dictionary에 넣어, 값이 준비되기 전에 변수를 참조하지 않는다.
    closing_only_tracking_state = classify_tracking_state(
        closing_only_selected_contour,
        crosshair_center,
    )
    closing_only_result = {
        "valid_candidate_count": len(closing_only_candidates),
        "tracking_state": closing_only_tracking_state,
    }

    # 5. Closing+Top-strip: 면적과 상단 위치 조건을 적용한 새 목록을 얻는다.
    # 이 과정은 위 closing_only_candidates 목록을 수정하지 않는다.
    closing_top_strip_candidates = collect_valid_candidates(closed_mask_5x5)

    # 이 방식도 후보가 정확히 하나일 때만 선택한다. 여러 후보 중 임의로 고르지 않는다.
    if len(closing_top_strip_candidates) == 1:
        closing_top_strip_selected_contour = closing_top_strip_candidates[0]
    else:
        closing_top_strip_selected_contour = None

    # 같은 중앙점과 같은 상태 판정 함수를 써서 필터 조건의 차이만 비교한다.
    closing_top_strip_tracking_state = classify_tracking_state(
        closing_top_strip_selected_contour,
        crosshair_center,
    )
    closing_top_strip_result = {
        "valid_candidate_count": len(closing_top_strip_candidates),
        "tracking_state": closing_top_strip_tracking_state,
    }

    # 6. 바깥 Key는 방식 이름, 안쪽 Key는 후보 수와 상태다. 후보가 없어도 Dictionary를 반환한다.
    # 이 함수는 출력이나 파일 저장을 하지 않으므로 이후 여러 Frame을 순회할 때도 재사용할 수 있다.
    return {
        "original": original_result,
        "closing_only": closing_only_result,
        "closing_top_strip": closing_top_strip_result,
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

    # imread()가 반환하는 이미지 배열은 BGR 순서다. 읽기에 실패하면 None이 반환된다.
    frame = cv2.imread(str(IMAGE_PATH))
    if frame is None:
        raise ValueError(f"대표 프레임 이미지를 읽을 수 없습니다: {IMAGE_PATH}")

    # 실제 검출 코드와 같은 함수로 단일 채널 마스크를 생성한다.
    mask = create_target_mask(frame)

    # Kernel 크기만 달리해 같은 원본 Mask에 Closing을 적용한다.
    # main()의 Mask는 이미지 저장과 Shape 관찰용이다. 비교 상태 계산은 compare_frame()이 맡는다.
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

    # 입력 이미지 크기와 정수 중앙점을 출력해 검사 대상의 좌표 기준을 확인한다.
    height, width = frame.shape[:2]

    crosshair_x = width // 2
    crosshair_y = height // 2
    crosshair_center = (crosshair_x, crosshair_y)

    print("높이와 너비: ", height, width)
    print("Crosshair 중심점: ", crosshair_center)

    # 세 방식의 상태 계산은 비교 함수에 맡기고, 여기서는 반환된 결과를 출력한다.
    comparison_results = compare_frame(frame)
    # 비교 결과는 한 번만 출력한다. sort_dicts=False는 작성한 방식 순서를 유지한다.
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

    # 세 Mask를 764번 전용 파일명으로 저장해 시각적으로 비교한다.
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
