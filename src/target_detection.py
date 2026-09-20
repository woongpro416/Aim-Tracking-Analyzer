import cv2
import numpy as np


LOWER_HSV = np.array([85, 180, 180], dtype=np.uint8)
UPPER_HSV = np.array([100, 255, 255], dtype=np.uint8)
MIN_CANDIDATE_AREA = 1.0

BoundingBox = tuple[int, int, int, int]
CenterPoint = tuple[float, float]
DetectionResult = tuple[
    bool,
    BoundingBox | None,
    CenterPoint | None,
    int,
    int,
]


def create_target_mask(frame: np.ndarray) -> np.ndarray:
    if frame is None:
        raise ValueError("BGR 프레임이 None일 수 없습니다.")

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            "BGR 프레임은 (높이, 너비, 3) 형태여야 합니다: "
            f"실제 형태={frame.shape}"
        )

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv_frame, LOWER_HSV, UPPER_HSV)


def detect_target(frame: np.ndarray) -> DetectionResult:
    mask = create_target_mask(frame)
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    valid_candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area >= MIN_CANDIDATE_AREA:
            valid_candidates.append(contour)

    contour_count = len(contours)
    valid_candidate_count = len(valid_candidates)
    target_detected = valid_candidate_count == 1

    if not target_detected:
        return False, None, None, contour_count, valid_candidate_count

    target_contour = valid_candidates[0]
    bounding_box = cv2.boundingRect(target_contour)
    x, y, width, height = bounding_box
    center = (
        x + width / 2,
        y + height / 2,
    )

    return True, bounding_box, center, contour_count, valid_candidate_count
