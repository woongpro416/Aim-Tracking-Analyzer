import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from inspect_run_baselines import (
    COUNT_ONLY_CHANGE,
    STATE_CHANGE,
    apply_manual_labels,
    classify_frame_change,
    select_change_samples,
    summarize_manual_validation,
)


def comparison(states, counts):
    """실제 비교 함수와 같은 작은 결과 Dictionary를 만든다."""
    names = ("original", "closing_only", "closing_top_strip")
    return {
        name: {"tracking_state": states[index], "valid_candidate_count": counts[index]}
        for index, name in enumerate(names)
    }


def state_change_record(frame_index, run_seconds):
    return {
        "frame_index": frame_index,
        "run_relative_time_seconds": run_seconds,
        "change_type": STATE_CHANGE,
        "predictions": comparison(("OFF_TARGET", "ON_TARGET", "ON_TARGET"), (1, 1, 1)),
    }


def test_equal_states_and_counts_are_not_changed():
    result = comparison(("OFF_TARGET", "OFF_TARGET", "OFF_TARGET"), (1, 1, 1))
    assert classify_frame_change(result) is None


def test_state_difference_is_recorded_even_when_candidate_counts_match():
    result = comparison(("OFF_TARGET", "ON_TARGET", "ON_TARGET"), (1, 1, 1))
    assert classify_frame_change(result) == STATE_CHANGE


def test_equal_states_with_different_candidate_counts_are_count_only():
    # 모두 MISSING이어도 후보가 없는 경우와 여러 개인 경우는 구분해 기록한다.
    result = comparison(("MISSING", "MISSING", "MISSING"), (0, 2, 2))
    assert classify_frame_change(result) == COUNT_ONLY_CHANGE


def test_state_change_takes_priority_when_both_fields_change():
    # 한 Frame을 두 유형에 중복 집계하지 않는다.
    result = comparison(("ON_TARGET", "MISSING", "ON_TARGET"), (1, 2, 1))
    assert classify_frame_change(result) == STATE_CHANGE


def test_difference_in_top_strip_method_is_not_missed():
    result = comparison(("MISSING", "MISSING", "ON_TARGET"), (2, 2, 1))
    assert classify_frame_change(result) == STATE_CHANGE


def test_missing_method_is_an_invalid_result_not_an_unchanged_frame():
    with pytest.raises(KeyError):
        classify_frame_change({})


def test_empty_change_list_returns_no_samples():
    assert select_change_samples([], STATE_CHANGE, 12) == []


def test_absent_count_only_type_does_not_create_fake_samples():
    records = [state_change_record(400, 1.0)]
    assert select_change_samples(records, COUNT_ONLY_CHANGE, 4) == []


def test_sampling_covers_early_middle_late_within_budget():
    records = [state_change_record(356 + seconds * 60, float(seconds)) for seconds in (1, 12, 21, 32, 41, 52)]
    selected = select_change_samples(records, STATE_CHANGE, 3)
    assert len(selected) == 3
    assert len({record["frame_index"] for record in selected}) == 3
    assert {int(record["run_relative_time_seconds"] // 20) for record in selected} == {0, 1, 2}


def test_sampling_reuses_day10_frame_and_does_not_exceed_available_frames():
    records = [state_change_record(381, 25 / 60), state_change_record(400, 44 / 60)]
    selected = select_change_samples(records, STATE_CHANGE, 12)
    assert [record["frame_index"] for record in selected] == [381, 400]


def test_zero_sample_budget_returns_empty_list():
    assert select_change_samples([state_change_record(400, 1.0)], STATE_CHANGE, 0) == []


def test_sampling_spreads_same_pattern_instead_of_selecting_adjacent_frames():
    records = [state_change_record(index, (index - 356) / 60) for index in range(400, 430)]
    indices = [record["frame_index"] for record in select_change_samples(records, STATE_CHANGE, 5)]
    assert len(indices) == 5
    assert min(right - left for left, right in zip(indices, indices[1:])) > 1


def test_existing_user_label_survives_automatic_report_regeneration(tmp_path):
    label_path = tmp_path / "manual_labels.json"
    label_path.write_text(json.dumps({"400": "ON_TARGET"}), encoding="utf-8")
    record = {"frame_index": 400, "ground_truth": None}
    apply_manual_labels(label_path, [record])
    assert record["ground_truth"] == "ON_TARGET"
    assert record["ground_truth_source"] == "user_manual_labels_file"
    assert json.loads(label_path.read_text(encoding="utf-8"))["400"] == "ON_TARGET"


def test_unreviewed_frame_stays_null_in_manual_label_file(tmp_path):
    label_path = tmp_path / "manual_labels.json"
    record = {"frame_index": 400, "ground_truth": None}
    apply_manual_labels(label_path, [record])
    assert record["ground_truth"] is None
    assert record["review_status"] == "not_manually_reviewed"
    assert json.loads(label_path.read_text(encoding="utf-8"))["400"] is None


def test_invalid_manual_label_is_not_silently_accepted(tmp_path):
    label_path = tmp_path / "manual_labels.json"
    label_path.write_text(json.dumps({"400": "UNKNOWN"}), encoding="utf-8")
    with pytest.raises(ValueError):
        apply_manual_labels(label_path, [{"frame_index": 400, "ground_truth": None}])


def test_manual_validation_compares_predictions_with_user_label():
    record = {
        "frame_index": 2617,
        "ground_truth": "ON_TARGET",
        "predictions": comparison(("OFF_TARGET", "MISSING", "ON_TARGET"), (1, 2, 1)),
    }
    result = summarize_manual_validation([record])
    assert result["verified_frame_count"] == 1
    assert result["match_counts"] == {"original": 0, "closing_only": 0, "closing_top_strip": 1}
    assert result["mismatches"]["closing_only"] == [{
        "frame_index": 2617,
        "ground_truth": "ON_TARGET",
        "predicted_state": "MISSING",
        "valid_candidate_count": 2,
    }]


def test_unreviewed_label_is_not_counted_as_missing_ground_truth():
    record = {
        "frame_index": 400,
        "ground_truth": None,
        "predictions": comparison(("MISSING", "MISSING", "MISSING"), (0, 0, 0)),
    }
    result = summarize_manual_validation([record])
    assert result["verified_frame_count"] == 0
    assert all(count == 0 for count in result["match_counts"].values())


def test_empty_manual_validation_has_zero_denominator_and_no_mismatches():
    result = summarize_manual_validation([])
    assert result["verified_frame_count"] == 0
    assert all(items == [] for items in result["mismatches"].values())
