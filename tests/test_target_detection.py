import sys
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

# 프로젝트가 아직 패키지화되지 않았으므로 src 경로를 등록한 뒤 검출 함수를 가져온다.
from target_detection import create_target_mask, detect_target


# 빈 입력과 단일·복수 후보를 통해 검출 결과 계약을 확인한다.
def test_blank_frame_has_no_target():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    detected, bounding_box, center, contour_count, valid_candidate_count = (
        detect_target(frame)
    )

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 0
    assert valid_candidate_count == 0


def test_single_cyan_circle_is_detected():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (255, 255, 0), -1)

    detected, bounding_box, center, contour_count, valid_candidate_count = (
        detect_target(frame)
    )

    assert detected is True
    assert bounding_box == (40, 40, 21, 21)
    assert center == (50.5, 50.5)
    assert contour_count == 1
    assert valid_candidate_count == 1


def test_two_cyan_circles_are_ambiguous():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (25, 50), 10, (255, 255, 0), -1)
    cv2.circle(frame, (75, 50), 10, (255, 255, 0), -1)

    detected, bounding_box, center, contour_count, valid_candidate_count = (
        detect_target(frame)
    )

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 2
    assert valid_candidate_count == 2


def test_dark_cyan_region_is_not_detected():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (50, 50, 0), -1)

    detected, bounding_box, center, contour_count, valid_candidate_count = (
        detect_target(frame)
    )

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 0
    assert valid_candidate_count == 0


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
        (10, 10),
        (21, 21),
        (255, 255, 0),
        -1,
    )

    (
        detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
    ) = detect_target(frame)

    assert detected is False
    assert bounding_box is None
    assert center is None
    assert contour_count == 1
    assert valid_candidate_count == 0
