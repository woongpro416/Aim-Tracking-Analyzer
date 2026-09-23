import cv2

from target_detection import TargetContour

CrosshairPoint = tuple[int, int]

TRACKING_STATE_ON_TARGET = "ON_TARGET"
TRACKING_STATE_OFF_TARGET = "OFF_TARGET"
TRACKING_STATE_MISSING = "MISSING"


def is_crosshair_on_target(
    target_contour: TargetContour,
    crosshair_point: CrosshairPoint,
) -> bool:
    point_test_result = cv2.pointPolygonTest(
        target_contour,
        crosshair_point,
        False,
    )
    if point_test_result >= 0:
        return True
    return False


def classify_tracking_state(
    target_contour: TargetContour | None,
    crosshair_point: CrosshairPoint,
) -> str:
    if target_contour is None:
        return TRACKING_STATE_MISSING

    if is_crosshair_on_target(target_contour, crosshair_point):
        return TRACKING_STATE_ON_TARGET

    return TRACKING_STATE_OFF_TARGET
