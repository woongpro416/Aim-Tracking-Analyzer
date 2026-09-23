
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from tracking_state import (
    TRACKING_STATE_MISSING,
    TRACKING_STATE_OFF_TARGET,
    TRACKING_STATE_ON_TARGET,
    classify_tracking_state,
    is_crosshair_on_target,
)


def test_crosshair_inside_target_contour_is_on_target():
    square_contour = np.array(
        [
            [[10, 10]],
            [[30, 10]],
            [[30, 30]],
            [[10, 30]],
        ],
        dtype=np.int32,
    )

    result = is_crosshair_on_target(
        square_contour,
        (20, 20),
    )

    assert result is True


def test_crosshair_on_target_contour_boundary_is_on_target():
    square_contour = np.array(
        [
            [[10, 10]],
            [[30, 10]],
            [[30, 30]],
            [[10, 30]],
        ],
        dtype=np.int32,
    )

    result = is_crosshair_on_target(
        square_contour,
        (10, 20),
    )

    assert result is True


def test_crosshair_outside_target_contour_is_off_target():
    square_contour = np.array(
        [
            [[10, 10]],
            [[30, 10]],
            [[30, 30]],
            [[10, 30]],
        ],
        dtype=np.int32,
    )

    result = is_crosshair_on_target(
        square_contour,
        (40, 20),
    )

    assert result is False


def test_missing_target_contour_is_missing():
    result = classify_tracking_state(
        None,
        (20, 20),
    )

    assert result == TRACKING_STATE_MISSING


def test_inside_target_contour_is_classified_as_on_target():
    square_contour = np.array(
        [
            [[10, 10]],
            [[30, 10]],
            [[30, 30]],
            [[10, 30]],
        ],
        dtype=np.int32,
    )

    result = classify_tracking_state(
        square_contour,
        (20, 20),
    )

    assert result == TRACKING_STATE_ON_TARGET


def test_outside_target_contour_is_classified_as_off_target():
    square_contour = np.array(
        [
            [[10, 10]],
            [[30, 10]],
            [[30, 30]],
            [[10, 30]],
        ],
        dtype=np.int32,
    )

    result = classify_tracking_state(
        square_contour,
        (40, 20),
    )

    assert result == TRACKING_STATE_OFF_TARGET
