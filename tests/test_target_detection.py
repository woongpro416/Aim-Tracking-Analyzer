import sys
from pathlib import Path

import cv2
import numpy as np
import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

# 프로젝트가 아직 패키지화되지 않았으므로 src 경로를 등록한 뒤 검출 함수를 가져온다.
from target_detection import create_target_mask, detect_target
from tracking_state import classify_tracking_state


# 빈 입력과 단일·복수 후보를 통해 검출 결과 계약을 확인한다.
def test_blank_frame_has_no_target():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    (
        detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        selected_contour,
    ) = detect_target(frame)

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 0
    assert valid_candidate_count == 0
    assert selected_contour is None


def test_single_cyan_circle_is_detected():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (255, 255, 0), -1)

    (
        detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        selected_contour,
    ) = detect_target(frame)

    assert detected is True
    assert bounding_box == (40, 40, 21, 21)
    assert center == (50.5, 50.5)
    assert contour_count == 1
    assert valid_candidate_count == 1
    assert selected_contour is not None


def test_two_cyan_circles_are_ambiguous():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (25, 50), 10, (255, 255, 0), -1)
    cv2.circle(frame, (75, 50), 10, (255, 255, 0), -1)

    (
        detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        selected_contour,
    ) = detect_target(frame)

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 2
    assert valid_candidate_count == 2
    assert selected_contour is None


def test_dark_cyan_region_is_not_detected():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (50, 50, 0), -1)

    (
        detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        selected_contour,
    ) = detect_target(frame)

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 0
    assert valid_candidate_count == 0
    assert selected_contour is None


def test_mask_is_single_channel_uint8():
    frame = np.zeros((80, 120, 3), dtype=np.uint8)

    mask = create_target_mask(frame)

    assert mask.shape == (80, 120)
    assert mask.dtype == np.uint8


# 이전 기준값 50은 통과하지만 새 기준값 150보다 작은 색상 잡음을 재현한다.
def test_small_cyan_noise_region_is_filtered_out():
    frame = np.zeros(
        (100, 100, 3),
        dtype=np.uint8,
    )

    cv2.rectangle(
        frame,
        (10, 40),
        (21, 51),
        (255, 255, 0),
        -1,
    )

    (
        detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        selected_contour,
    ) = detect_target(frame)

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 1
    assert valid_candidate_count == 0
    assert selected_contour is None


def test_top_strip_noise_is_removed_without_removing_central_target():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (255, 255, 0), -1)
    cv2.rectangle(frame, (5, 0), (24, 9), (255, 255, 0), -1)
    detected, bbox, center, contour_count, candidate_count, contour = detect_target(frame)
    assert detected is True
    assert contour_count == 2
    assert candidate_count == 1
    assert bbox == (40, 40, 21, 21)
    assert classify_tracking_state(contour, (50, 50)) == "ON_TARGET"


def test_only_top_strip_noise_is_missing_not_off_target():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(frame, (5, 0), (24, 9), (255, 255, 0), -1)
    detected, bbox, center, contour_count, candidate_count, contour = detect_target(frame)
    assert detected is False
    assert candidate_count == 0
    assert contour_count == 1
    assert bbox is None and center is None
    assert classify_tracking_state(contour, (50, 50)) == "MISSING"


def test_candidate_extending_below_top_strip_is_kept():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(frame, (5, 11), (24, 30), (255, 255, 0), -1)
    result = detect_target(frame)
    assert result[0] is True
    assert result[1] == (5, 11, 20, 20)
    assert result[4] == 1
    assert classify_tracking_state(result[5], (50, 50)) == "OFF_TARGET"


def test_closing_connects_a_small_gap_in_one_target():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(frame, (20, 20), (80, 80), (255, 255, 0), -1)
    frame[20:81, 49:52] = 0
    result = detect_target(frame)
    assert result[0] is True
    assert result[4] == 1
    assert classify_tracking_state(result[5], (50, 50)) == "ON_TARGET"


def test_actual_target_wholly_in_top_strip_has_documented_erasure_risk():
    # 의도된 MVP 제약을 고정한다. Shape가 원이어도 상단에 완전히 포함되면 제외된다.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 15), 10, (255, 255, 0), -1)
    result = detect_target(frame)
    assert result[0] is False
    assert result[4] == 0
    assert result[5] is None


def test_invalid_bgr_input_fails_before_detection():
    for frame in (None, np.zeros((100, 100), dtype=np.uint8)):
        with pytest.raises(ValueError):
            detect_target(frame)
