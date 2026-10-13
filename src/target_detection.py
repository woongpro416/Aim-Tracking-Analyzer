from collections.abc import Iterable

import cv2
import numpy as np


# 밝은 청록색 타겟을 분리하기 위한 HSV 범위다.
LOWER_HSV = np.array([85, 180, 180], dtype=np.uint8)
UPPER_HSV = np.array([100, 255, 255], dtype=np.uint8)

# cv2.contourArea() 기준 150 제곱픽셀 미만의 작은 배경 조각은 후보에서 제외한다.
# 실제 영상에서는 잡음의 최대 면적이 106.5였고, 150부터 결과가 안정되었다.
MIN_CANDIDATE_AREA = 150.0

# 승인된 MVP 정책이다. 30px 규칙의 검증 범위는 현재 1920×1080 HUD 환경이다.
DETECTION_POLICY = "closing_top_strip"
CLOSING_KERNEL_SIZE = 5
TOP_STRIP_BOTTOM_Y = 30

# 검출 함수가 반환하는 좌표와 결과 형식을 명시한다.
BoundingBox = tuple[int, int, int, int]
CenterPoint = tuple[float, float]
TargetContour = np.ndarray
DetectionResult = tuple[
    bool,
    BoundingBox | None,
    CenterPoint | None,
    int,
    int,
    TargetContour | None,
]


def create_target_mask(frame: np.ndarray) -> np.ndarray:
    """BGR 프레임에서 밝은 청록색 영역만 흰색인 이진 마스크를 만든다."""

    # None이나 채널 수가 다른 배열을 OpenCV 색상 변환에 넘기지 않는다.
    if frame is None:
        raise ValueError("BGR 프레임이 None일 수 없습니다.")

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            "BGR 프레임은 (높이, 너비, 3) 형태여야 합니다: "
            f"실제 형태={frame.shape}"
        )

    # BGR보다 색상 범위를 다루기 쉬운 HSV로 변환한 뒤 범위 안의 픽셀만 남긴다.
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv_frame, LOWER_HSV, UPPER_HSV)


def close_target_mask(mask: np.ndarray) -> np.ndarray:
    """승인된 5×5 Closing으로 HSV Mask의 작은 끊김을 연결한다."""
    kernel = np.ones((CLOSING_KERNEL_SIZE, CLOSING_KERNEL_SIZE), dtype=np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def is_top_strip_candidate(bbox: BoundingBox) -> bool:
    """bbox 전체가 상단 [0, 30)px에 포함되면 제외 대상으로 본다."""
    _x, y, _width, height = bbox
    # y + height는 사각형의 아래쪽 제외 경계다. 실제 Target도 이 영역이면 제외된다.
    return y + height <= TOP_STRIP_BOTTOM_Y


def filter_target_candidates(contours: Iterable[TargetContour]) -> list[TargetContour]:
    """면적과 승인된 Top-strip 조건을 적용한다. 후보 선택은 별도로 수행한다."""
    valid_candidates = []
    for contour in contours:
        if cv2.contourArea(contour) < MIN_CANDIDATE_AREA:
            continue
        if is_top_strip_candidate(cv2.boundingRect(contour)):
            continue
        valid_candidates.append(contour)
    return valid_candidates


def detect_target(frame: np.ndarray) -> DetectionResult:
    """HSV → 5×5 Closing → 면적 → Top-strip → 단일 후보의 최종 MVP 검출이다."""

    # 이진 마스크의 서로 떨어진 흰색 영역을 외곽 윤곽선으로 추출한다.
    mask = close_target_mask(create_target_mask(frame))
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    valid_candidates = filter_target_candidates(contours)

    # 후보가 없거나 여러 개면 위치를 임의로 선택하지 않고 미결정으로 반환한다.
    # contour_count는 Closing 후, Candidate Filter 전의 외부 윤곽선 수다.
    contour_count = len(contours)
    valid_candidate_count = len(valid_candidates)
    target_detected = valid_candidate_count == 1

    if not target_detected:
        return False, None, None, contour_count, valid_candidate_count, None

    # 단일 후보의 사각형 중심을 픽셀 좌표계의 타겟 중심으로 사용한다.
    target_contour = valid_candidates[0]
    bounding_box = cv2.boundingRect(target_contour)
    x, y, width, height = bounding_box
    center = (
        x + width / 2,
        y + height / 2,
    )

    return (
        True,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        target_contour,
    )
