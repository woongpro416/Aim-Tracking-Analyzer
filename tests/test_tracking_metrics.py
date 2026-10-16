import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tracking_metrics import calculate_off_target_metrics, calculate_observed_on_target_ratio


def test_totals_and_average_for_two_intervals():
    intervals = [
        {
            "off_target_frame_count": 2,
            "off_target_duration_seconds": 2 / 60,
        },
        {
            "off_target_frame_count": 1,
            "off_target_duration_seconds": 1 / 60,
        },
    ]

    metrics = calculate_off_target_metrics(intervals)

    assert metrics["off_target_interval_count"] == 2
    assert metrics["total_off_target_frame_count"] == 3
    assert metrics["total_off_target_duration_seconds"] == pytest.approx(0.05)
    assert metrics["off_target_average_interval_duration_seconds"] == pytest.approx(0.025)


def test_empty_intervals_return_zero_totals_and_no_average():
    metrics = calculate_off_target_metrics([])

    assert metrics["off_target_interval_count"] == 0
    assert metrics["total_off_target_frame_count"] == 0
    assert metrics["total_off_target_duration_seconds"] == 0.0
    assert metrics["off_target_average_interval_duration_seconds"] is None


def test_observed_on_target_ratio_with_observed_frames():
    observed_on_target_ratio = calculate_observed_on_target_ratio(3, 1)

    assert observed_on_target_ratio == 0.75

def test_observed_on_target_ratio_without_observed_frames():
    observed_on_target_ratio = calculate_observed_on_target_ratio(0, 0)

    assert observed_on_target_ratio is None

def test_observed_on_target_ratio_zero_when_all_observed_frames_off_target():
    observed_on_target_ratio = calculate_observed_on_target_ratio(0, 4)

    assert observed_on_target_ratio == 0.0


def test_observed_on_target_ratio_rejects_negative_frame_count():
    with pytest.raises(ValueError):
        calculate_observed_on_target_ratio(-1, -2)

def test_observed_on_target_ratio_on_target_negative_frame_count():
    with pytest.raises(ValueError):
        calculate_observed_on_target_ratio(-1, 2)

def test_observed_on_target_ratio_off_target_negative_frame_count():
    with pytest.raises(ValueError):
        calculate_observed_on_target_ratio(1, -2)
