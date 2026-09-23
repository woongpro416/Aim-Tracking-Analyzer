import cv2
import numpy as np


# 밝은 청록색 타겟을 분리하기 위한 HSV 범위다.
LOWER_HSV = np.array([85, 180, 180], dtype=np.uint8)
UPPER_HSV = np.array([100, 255, 255], dtype=np.uint8)

# cv2.contourArea() 기준 150 제곱픽셀 미만의 작은 배경 조각은 후보에서 제외한다.
# 실제 영상에서는 잡음의 최대 면적이 106.5였고, 150부터 결과가 안정되었다.
MIN_CANDIDATE_AREA = 150.0

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


def detect_target(frame: np.ndarray) -> DetectionResult:
    """면적 조건을 통과한 후보가 정확히 하나일 때 타겟 위치를 반환한다."""

    # 이진 마스크의 서로 떨어진 흰색 영역을 외곽 윤곽선으로 추출한다.
    mask = create_target_mask(frame)
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    # 작은 UI 조각과 색상 잡음을 제외하고 의미 있는 후보만 보존한다.
    valid_candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area >= MIN_CANDIDATE_AREA:
            valid_candidates.append(contour)

    # 후보가 없거나 여러 개면 위치를 임의로 선택하지 않고 미결정으로 반환한다.
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
