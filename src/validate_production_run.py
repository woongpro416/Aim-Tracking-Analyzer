"""Production 결과를 검증하는 개발 도구다. Detection 정책을 선택하거나 변경하지 않는다."""

import hashlib
import json

from main import PROJECT_ROOT, VIDEO_PATH, analyze_run, print_run_summary
from tracking_state import (
    TRACKING_STATE_MISSING,
    TRACKING_STATE_OFF_TARGET,
    TRACKING_STATE_ON_TARGET,
)


GROUND_TRUTH_PATH = PROJECT_ROOT / "tests" / "data" / "manual_ground_truth.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "day12_validation"


def validate_result(result: dict, reference: dict) -> dict:
    """실제 분석 결과의 개수·순서·상태 계약과 사용자 Label을 확인한다."""
    summary = result["summary"]
    raw = result["raw_observations"]
    sequence = result["tracking_state_sequence"]
    if summary["detection_policy"] != reference["expected_detection_policy"]:
        raise RuntimeError("Production Detection Contract가 승인된 정책과 다릅니다.")
    for field in ("fps", "frame_width", "frame_height"):
        if summary[field] != reference[field]:
            raise RuntimeError(f"검증 영상 메타데이터가 다릅니다: {field}")

    expected_count = reference["frame_count"]
    if not (len(raw) == len(sequence) == summary["run_segment_frame_count"] == expected_count):
        raise RuntimeError("Raw Observation / Tracking State / Run Frame 수가 다릅니다.")
    if summary["raw_observation_count"] != len(raw) or summary["tracking_state_sequence_count"] != len(sequence):
        raise RuntimeError("Summary의 Frame 수와 실제 목록 길이가 다릅니다.")

    first = reference["first_frame_index"]
    expected_indices = list(range(first, first + expected_count))
    if [record["frame_index"] for record in raw] != expected_indices:
        raise RuntimeError("Raw Observation의 Frame Index가 누락·중복되거나 순서가 다릅니다.")
    if [record["frame_index"] for record in sequence] != expected_indices:
        raise RuntimeError("Tracking State의 Frame Index가 누락·중복되거나 순서가 다릅니다.")

    counts = {TRACKING_STATE_ON_TARGET: 0, TRACKING_STATE_OFF_TARGET: 0, TRACKING_STATE_MISSING: 0}
    for observation, state_record in zip(raw, sequence):
        state = state_record["tracking_state"]
        if state not in counts:
            raise RuntimeError(f"알 수 없는 Tracking State입니다: {state}")
        counts[state] += 1
        if observation["valid_candidate_count"] == 1:
            if observation["center"] is None or state == TRACKING_STATE_MISSING:
                raise RuntimeError("단일 후보의 Center 또는 Tracking State가 잘못되었습니다.")
        elif observation["center"] is not None or state != TRACKING_STATE_MISSING:
            raise RuntimeError("미결정 Target의 Center 또는 MISSING 구분이 잘못되었습니다.")
    if counts != summary["state_counts"] or counts != reference["expected_state_counts"]:
        raise RuntimeError(f"승인 Baseline과 Production 상태 집계가 다릅니다: {counts}")

    labels = reference["labels"]
    if not labels:
        raise RuntimeError("수동 Ground Truth가 없어 최종 검증을 완료할 수 없습니다.")
    if len(labels) != reference["verified_label_count"]:
        raise RuntimeError("확인한 수동 Ground Truth의 일부 Label이 누락되었습니다.")
    states_by_index = {record["frame_index"]: record["tracking_state"] for record in sequence}
    manual_results = []
    for index_text, label in labels.items():
        if label not in counts:
            raise ValueError(f"수동 Label은 확인된 Tracking State여야 합니다: {index_text}")
        index = int(index_text)
        if index not in states_by_index:
            raise RuntimeError(f"수동 Label의 Frame이 Run 구간에 없습니다: {index}")
        predicted = states_by_index[index]
        manual_results.append({"frame_index": index, "ground_truth": label, "prediction": predicted, "match": predicted == label})
    mismatches = [record for record in manual_results if not record["match"]]
    if mismatches:
        raise RuntimeError(f"Production과 수동 Ground Truth가 충돌합니다: {mismatches}")

    return {
        "status": "passed",
        "detection_policy": summary["detection_policy"],
        "run_segment_frame_count": expected_count,
        "raw_observation_count": len(raw),
        "tracking_state_sequence_count": len(sequence),
        "state_counts": counts,
        "frame_indices_complete_and_ordered": True,
        "missing_contract_preserved": True,
        "manual_label_count": len(labels),
        "manual_match_count": len(manual_results),
        "manual_results": manual_results,
        "scope": "Manual matches apply to reviewed frames only, not full-video accuracy.",
    }


def main() -> None:
    reference = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    if VIDEO_PATH.name != reference["video_filename"]:
        raise RuntimeError("수동 Label은 지정한 검증 영상에만 적용됩니다.")
    with VIDEO_PATH.open("rb") as video_file:
        input_hash = hashlib.file_digest(video_file, "sha256").hexdigest()
    if input_hash != reference["video_sha256"]:
        raise RuntimeError("검증 영상 파일이 기존 Ground Truth의 영상과 다릅니다.")

    print("승인된 Production Pipeline의 전체 Run을 분석합니다.")
    result = analyze_run()
    report = validate_result(result, reference)
    report["video_sha256"] = input_hash
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "production_run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "production_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print_run_summary(result["summary"])
    print(f"사용자 Ground Truth 일치: {report['manual_match_count']}/{report['manual_label_count']}")
    print("최종 Production 검증: PASS")
    print(f"검증 결과 저장: {OUTPUT_DIR / 'production_validation.json'}")


if __name__ == "__main__":
    main()
