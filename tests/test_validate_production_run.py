import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from validate_production_run import validate_result


def valid_input():
    result = {
        "summary": {
            "detection_policy": "closing_top_strip", "fps": 60.0,
            "frame_width": 100, "frame_height": 100,
            "run_segment_frame_count": 2, "raw_observation_count": 2,
            "tracking_state_sequence_count": 2,
            "state_counts": {"ON_TARGET": 1, "OFF_TARGET": 0, "MISSING": 1},
        },
        "raw_observations": [
            {"frame_index": 0, "center": (50.5, 50.5), "valid_candidate_count": 1},
            {"frame_index": 1, "center": None, "valid_candidate_count": 0},
        ],
        "tracking_state_sequence": [
            {"frame_index": 0, "tracking_state": "ON_TARGET"},
            {"frame_index": 1, "tracking_state": "MISSING"},
        ],
    }
    reference = {
        "expected_detection_policy": "closing_top_strip", "fps": 60.0,
        "frame_width": 100, "frame_height": 100, "frame_count": 2,
        "first_frame_index": 0,
        "verified_label_count": 2,
        "expected_state_counts": {"ON_TARGET": 1, "OFF_TARGET": 0, "MISSING": 1},
        "labels": {"0": "ON_TARGET", "1": "MISSING"},
    }
    return result, reference


def test_valid_result_matches_counts_and_manual_labels():
    result, reference = valid_input()
    report = validate_result(result, reference)
    assert report["status"] == "passed"
    assert report["manual_match_count"] == 2
    assert report["missing_contract_preserved"] is True


def test_frame_count_mismatch_is_not_reported_as_success():
    result, reference = valid_input()
    result["raw_observations"].pop()
    with pytest.raises(RuntimeError):
        validate_result(result, reference)


def test_duplicate_frame_index_is_not_hidden_by_a_dictionary():
    result, reference = valid_input()
    result["tracking_state_sequence"][1]["frame_index"] = 0
    with pytest.raises(RuntimeError):
        validate_result(result, reference)


def test_missing_target_is_not_allowed_to_be_off_target():
    result, reference = valid_input()
    result["tracking_state_sequence"][1]["tracking_state"] = "OFF_TARGET"
    with pytest.raises(RuntimeError):
        validate_result(result, reference)


def test_manual_label_conflict_fails_even_when_counts_match():
    result, reference = valid_input()
    reference["labels"]["0"] = "OFF_TARGET"
    with pytest.raises(RuntimeError):
        validate_result(result, reference)


def test_unreviewed_label_is_not_accepted_as_ground_truth():
    result, reference = valid_input()
    reference["labels"]["0"] = None
    with pytest.raises(ValueError):
        validate_result(result, reference)


def test_empty_manual_label_set_cannot_complete_validation():
    result, reference = valid_input()
    reference["labels"] = {}
    with pytest.raises(RuntimeError):
        validate_result(result, reference)


def test_partial_manual_label_set_cannot_silently_reduce_review_scope():
    result, reference = valid_input()
    reference["labels"].pop("1")
    with pytest.raises(RuntimeError):
        validate_result(result, reference)
