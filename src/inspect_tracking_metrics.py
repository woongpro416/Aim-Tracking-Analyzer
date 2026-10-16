import json
from pathlib import Path
import math

from off_target_intervals import group_off_target_intervals
from tracking_metrics import calculate_off_target_metrics, calculate_observed_on_target_ratio

PROJECT_ROOT = Path(__file__).resolve().parent.parent
production_run_path = (
    PROJECT_ROOT / "outputs" / "day12_validation" / "production_run.json"
)

with production_run_path.open(encoding="utf-8") as production_run_file:
    production_run = json.load(production_run_file)

tracking_state_sequence = production_run["tracking_state_sequence"]
fps = production_run["summary"]["fps"]

off_target_intervals = group_off_target_intervals(tracking_state_sequence, fps)
run_tracking_metrics = calculate_off_target_metrics(off_target_intervals)

print(run_tracking_metrics)


# 각 interval에서 "off_target_frame_count"를 꺼내 합산한다.
total_off_target_frame_count = sum(
    interval["off_target_frame_count"] for interval in off_target_intervals)

assert total_off_target_frame_count == 1000
assert (
    total_off_target_frame_count
    == run_tracking_metrics["total_off_target_frame_count"]
)

expected_off_target_duration_seconds = total_off_target_frame_count / fps
assert math.isclose(
    run_tracking_metrics["total_off_target_duration_seconds"],
    expected_off_target_duration_seconds,
    rel_tol=1e-9,
)

print("OFF_TARGET Frame 합계 검증 통과")

for interval in off_target_intervals:
    calculated_frame_count = (
        interval["end_frame_index_exclusive"]
        - interval["start_frame_index"]
    )
    assert calculated_frame_count == interval["off_target_frame_count"]
    assert interval["end_reason"] in ("ON_TARGET" , "MISSING" , "RUN_END")


end_reason_counts = {"ON_TARGET": 0, "MISSING": 0, "RUN_END": 0}

for interval in off_target_intervals:
    end_reason = interval["end_reason"]
    end_reason_counts[end_reason] += 1

assert sum(end_reason_counts.values()) == len(off_target_intervals)
print(end_reason_counts)

# 구간 사이에 Frame 중복, 누락 확인
observed_off_target_frame_indices = []

for record in tracking_state_sequence:
    if record["tracking_state"] == "OFF_TARGET":
        observed_off_target_frame_indices.append(record["frame_index"])
        
print("off_target 프레임 인덱스: ", observed_off_target_frame_indices)


# 구간이 나타내는 Frame 번호
interval_off_target_frame_indices = []

for interval in off_target_intervals:
    for frame_index in range(
        interval["start_frame_index"],
        interval["end_frame_index_exclusive"],
    ):
        interval_off_target_frame_indices.append(frame_index)

assert interval_off_target_frame_indices == observed_off_target_frame_indices


state_counts = production_run["summary"]["state_counts"]

observed_on_target_ratio = calculate_observed_on_target_ratio(
    state_counts["ON_TARGET"],
    state_counts["OFF_TARGET"],
)

print("관측 구간 조준 일치율: ", observed_on_target_ratio)