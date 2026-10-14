import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from off_target_intervals import group_off_target_intervals


def test_run_end_includes_last_off_target_frame():
    sequence = [
        {"frame_index": 101, "frame_time_seconds": 101 / 60,
         "tracking_state": "OFF_TARGET"},
        {"frame_index": 102, "frame_time_seconds": 102 / 60,
         "tracking_state": "OFF_TARGET"},
    ]

    intervals = group_off_target_intervals(sequence, fps=60.0)

    assert len(intervals) == 1
    assert intervals[0]["start_frame_index"] == 101
    assert intervals[0]["end_frame_index_exclusive"] == 103
    assert intervals[0]["end_reason"] == "RUN_END"

    assert intervals[0]["off_target_frame_count"] == 2
    assert intervals[0]["off_target_duration_seconds"] == pytest.approx(0.0333333333)


def test_missing_splits_intervals_and_is_excluded_from_duration():
    sequence = [
        {"frame_index": 101, "frame_time_seconds": 101 / 60,
         "tracking_state": "OFF_TARGET"},
        {"frame_index": 102, "frame_time_seconds": 102 / 60,
         "tracking_state": "MISSING"},
        {"frame_index": 103, "frame_time_seconds": 103 / 60,
         "tracking_state": "OFF_TARGET"},
        {"frame_index": 104, "frame_time_seconds": 104 / 60,
         "tracking_state": "ON_TARGET"},
    ]

    intervals = group_off_target_intervals(sequence, fps=60.0)

    assert len(intervals) == 2
    assert intervals[0]["start_frame_index"] == 101
    assert intervals[0]["end_frame_index_exclusive"] == 102
    assert intervals[0]["end_reason"] == "MISSING"
    assert intervals[0]["off_target_frame_count"] == 1
    assert intervals[0]["off_target_duration_seconds"] == pytest.approx(0.0166666667)

    assert intervals[1]["start_frame_index"] == 103    
    assert intervals[1]["end_frame_index_exclusive"] == 104
    assert intervals[1]["end_reason"] == "ON_TARGET"
    assert intervals[1]["off_target_frame_count"] == 1
    assert intervals[1]["off_target_duration_seconds"] == pytest.approx(0.0166666667)


def test_empty_sequence_returns_no_intervals():
    intervals = group_off_target_intervals([], fps = 60.0)

    assert intervals == []


def test_on_target_only_returns_no_intervals():
    sequence = [
        {"frame_index": 0, "frame_time_seconds": 0 / 60,
         "tracking_state": "ON_TARGET"},
        {"frame_index": 1, "frame_time_seconds": 1 / 60,
         "tracking_state": "ON_TARGET"},
    ]

    intervals = group_off_target_intervals(sequence, fps=60.0)

    assert intervals == []