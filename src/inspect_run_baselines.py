import argparse
import json
import math
from html import escape
from pathlib import Path

import cv2

from inspect_target_mask import compare_frame
from target_detection import DETECTION_POLICY
from main import (
    VIDEO_PATH,
    KNOWN_RUN_START_SECONDS,
    RUN_DURATION_SECONDS,
)


METHOD_NAMES = ("original", "closing_only", "closing_top_strip")
STATE_CHANGE = "tracking_state_changed"
COUNT_ONLY_CHANGE = "candidate_count_only"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "day12_validation"

# Day 10에서 사용자가 원본 화면으로 확인한 Label이다. 자동 예측과 구분한다.
# 출처: docs/workflow/day10_representative_frame_validation_and_closing_experiment.md
# 이 인덱스들은 검증 표본이며 Detection의 Frame별 예외 조건이 아니다.
DAY10_MANUAL_LABELS = {
    356: "ON_TARGET",
    381: "ON_TARGET",
    436: "OFF_TARGET",
    764: "ON_TARGET",
    851: "MISSING",
    926: "OFF_TARGET",
    927: "ON_TARGET",
    1228: "ON_TARGET",
    1229: "OFF_TARGET",
    1380: "OFF_TARGET",
}


def classify_frame_change(comparison_results: dict) -> str | None:
    """상태 차이를 우선하고, 상태가 모두 같을 때만 후보 수 차이를 별도로 분류한다."""
    original = comparison_results["original"]
    state_changed = False
    candidate_count_changed = False

    for method_name in METHOD_NAMES:
        result = comparison_results[method_name]
        if result["tracking_state"] != original["tracking_state"]:
            state_changed = True
        if result["valid_candidate_count"] != original["valid_candidate_count"]:
            candidate_count_changed = True

    if state_changed:
        return STATE_CHANGE
    if candidate_count_changed:
        return COUNT_ONLY_CHANGE
    return None


def select_change_samples(records: list[dict], change_type: str, limit: int) -> list[dict]:
    """기존 수동 표본을 재사용하고, 시간대·세 방식의 결과 패턴별로 표본을 고른다."""
    if limit <= 0:
        return []

    candidates = [record for record in records if record["change_type"] == change_type]
    selected = []
    # 이미 확인한 대표 Frame이 변경 목록에도 있으면 해당 종류의 예산에 포함한다.
    for record in candidates:
        if record["frame_index"] in DAY10_MANUAL_LABELS and len(selected) < limit:
            selected.append(record)

    selected_indices = {record["frame_index"] for record in selected}
    groups = {}
    for record in candidates:
        if record["frame_index"] in selected_indices:
            continue
        # 20초 구간은 표본 다양성을 위한 기준이며 Detection Rule이 아니다.
        time_bucket = min(int(record["run_relative_time_seconds"] // 20), 2)
        predictions = record["predictions"]
        states = tuple(predictions[name]["tracking_state"] for name in METHOD_NAMES)
        counts = ()
        if change_type == COUNT_ONLY_CHANGE:
            counts = tuple(predictions[name]["valid_candidate_count"] for name in METHOD_NAMES)
        group_key = (time_bucket, states, counts)
        groups.setdefault(group_key, []).append(record)

    # 그룹을 번갈아 방문하며, 기존 표본과 시간 간격이 큰 사례를 고른다.
    while len(selected) < limit:
        added = False
        for group in groups.values():
            if not group:
                continue
            sample = group[len(group) // 2]
            if selected:
                best_distance = -1
                for candidate in group:
                    distance = min(
                        abs(candidate["frame_index"] - previous["frame_index"])
                        for previous in selected
                    )
                    if distance > best_distance:
                        best_distance = distance
                        sample = candidate
            group.remove(sample)
            selected.append(sample)
            added = True
            if len(selected) == limit:
                break
        if not added:
            break

    return sorted(selected, key=lambda record: record["frame_index"])


def apply_manual_labels(label_path: Path, records: list[dict]) -> None:
    """별도 수동 Label 파일을 보존하고, Label이 없는 표본은 미검증으로 둔다."""
    labels = {}
    if label_path.exists():
        labels = json.loads(label_path.read_text(encoding="utf-8"))
        if not isinstance(labels, dict):
            raise ValueError("수동 Label 파일은 Frame 번호를 Key로 가진 Dictionary여야 합니다.")

    added = False
    for record in records:
        key = str(record["frame_index"])
        if key not in labels:
            labels[key] = record["ground_truth"]
            added = True
        label = labels[key]
        if label is not None and label not in ("ON_TARGET", "OFF_TARGET", "MISSING"):
            raise ValueError(f"유효하지 않은 수동 Label입니다: Frame {key}, {label!r}")
        record["ground_truth"] = label
        if label is None:
            record["ground_truth_source"] = None
            record["review_status"] = "not_manually_reviewed"
        elif DAY10_MANUAL_LABELS.get(record["frame_index"]) == label:
            record["ground_truth_source"] = "day10_user_verified"
            record["review_status"] = "previously_verified_day10"
        else:
            record["ground_truth_source"] = "user_manual_labels_file"
            record["review_status"] = "user_verified"

    # 새 표본만 추가하며, 재실행해도 사용자가 작성한 기존 Label은 덮어쓰지 않는다.
    if added:
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_manual_validation(records: list[dict]) -> dict:
    """사용자가 Label을 확인한 표본만 분모에 포함하여 예측과 비교한다."""
    verified = [record for record in records if record["ground_truth"] is not None]
    match_counts = {}
    mismatches = {}
    for name in METHOD_NAMES:
        match_counts[name] = 0
        mismatches[name] = []
        for record in verified:
            prediction = record["predictions"][name]
            if prediction["tracking_state"] == record["ground_truth"]:
                match_counts[name] += 1
            else:
                mismatches[name].append({
                    "frame_index": record["frame_index"],
                    "ground_truth": record["ground_truth"],
                    "predicted_state": prediction["tracking_state"],
                    "valid_candidate_count": prediction["valid_candidate_count"],
                })
    return {
        "verified_frame_count": len(verified),
        "match_counts": match_counts,
        "mismatches": mismatches,
    }


def export_review_frames(records: list[dict]) -> None:
    """기존 Frame Inspector처럼 순차 Decode하여 선택된 원본과 중앙 Crop만 저장한다."""
    remaining = {record["frame_index"] for record in records}
    if not remaining:
        return
    frames_dir = OUTPUT_DIR / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    video_capture = cv2.VideoCapture(str(VIDEO_PATH))
    try:
        if not video_capture.isOpened():
            raise RuntimeError("수동 검증용 원본 영상을 열 수 없습니다.")
        frame_index = 0
        while remaining:
            success, frame = video_capture.read()
            if not success:
                break
            if frame_index in remaining:
                height, width = frame.shape[:2]
                cx, cy = width // 2, height // 2
                # 원본 픽셀을 잘라낸 320px 중앙 Crop이다. 예측 윤곽선은 그리지 않는다.
                crop = frame[max(0, cy - 160):min(height, cy + 160), max(0, cx - 160):min(width, cx + 160)]
                for suffix, image in (("", frame), ("_center", crop)):
                    path = frames_dir / f"frame_{frame_index:05d}{suffix}.png"
                    if not cv2.imwrite(str(path), image):
                        raise RuntimeError(f"수동 검증 이미지를 저장하지 못했습니다: {path}")
                remaining.remove(frame_index)
            frame_index += 1
    finally:
        video_capture.release()
    if remaining:
        raise RuntimeError(f"추출하지 못한 검증 Frame이 있습니다: {sorted(remaining)}")


def write_review_report(payload: dict) -> None:
    """알고리즘 예측과 사용자 Ground Truth를 구분한 Markdown·원본 이미지 갤러리다."""
    records = payload["manual_review_frames"]
    new_records = [record for record in records if record["ground_truth_source"] != "day10_user_verified"]
    legacy_records = [record for record in records if record["ground_truth_source"] == "day10_user_verified"]
    pending_records = [record for record in records if record["ground_truth"] is None]
    state_sample_count = len(payload["sampling"]["state_change_indices"])
    count_sample_count = len(payload["sampling"]["candidate_count_only_indices"])
    state_change_count = payload["change_counts"][STATE_CHANGE]
    count_only_change_count = payload["change_counts"][COUNT_ONLY_CHANGE]
    legacy_count = payload["day10_verified_frame_count"]
    matches = payload["day10_prediction_match_counts"]
    validation = payload["manual_validation"]
    lines = [
        "# Day 12 — 제한된 수동 검증",
        "",
        f"상태 변경 표본 {state_sample_count}개를 시간대와 변경 패턴별로 선정했다. 기존 Day 10 Label {legacy_count}개를 재사용한다.",
        f"전체 상태 변경 {state_change_count}개, Candidate Count만 변경 {count_only_change_count}개. 후보 수만 변경된 표본은 {count_sample_count}개다.",
        "모든 Frame의 Ground Truth를 확보한 결과가 아니다. 최종 MVP 정책은 Closing+Top-strip이며 Production 최종 검증은 별도 도구로 수행한다.",
        "",
        "원본 갤러리: [review.html](review.html). 중앙 Crop은 원본의 320×320 픽셀이며 예측 윤곽선을 그리지 않았다.",
        "전체 변경 Index·유형·예측: [baseline_comparison.json](baseline_comparison.json).",
        "사용자 Label만 보존하는 별도 파일: [manual_labels.json](manual_labels.json). null은 미검증이다.",
        "",
        "| 방식 | ON_TARGET | OFF_TARGET | MISSING |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, counts in payload["summary"]["state_counts"].items():
        lines.append(f"| {name} | {counts['ON_TARGET']} | {counts['OFF_TARGET']} | {counts['MISSING']} |")
    lines += [
        "",
        f"각 상태 합계는 {payload['summary']['run_segment_frame_count']}이다. Day 10 사용자 Label {legacy_count}개와의 예측 일치는 "
        + ", ".join(f"{name} {matches[name]}/{legacy_count}" for name in METHOD_NAMES) + "이다.",
        "위 일치 수는 해당 표본만의 결과이며 전체 영상 정확도를 뜻하지 않는다.",
        "",
        f"기존 Label과 추가 사용자 Label을 합친 수동 검증 표본 {validation['verified_frame_count']}개의 일치:",
        "",
        "| 방식 | 수동 검증 표본 일치 |",
        "| --- | ---: |",
    ]
    for name in METHOD_NAMES:
        lines.append(f"| {name} | {validation['match_counts'][name]}/{validation['verified_frame_count']} |")
    lines += [
        "",
        "이 표본은 변경 유형·시간대에 따라 선정했으며 무작위 표본이 아니다. 전체 3600 Frame의 정확도를 추정하는 수치로 사용하지 않는다.",
        "",
        "| Frame | Run 시각(초) | 변경 유형 | 사용자 Ground Truth | Original | Closing-only | Closing+Top-strip | 원본 |",
        "| ---: | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        index = record["frame_index"]
        truth = record["ground_truth"] or "미검증"
        if record["ground_truth_source"] == "day10_user_verified":
            truth += " (Day 10 직접 확인)"
        predictions = record["predictions"]
        values = [f"{predictions[name]['tracking_state']} ({predictions[name]['valid_candidate_count']})" for name in METHOD_NAMES]
        full_path = OUTPUT_DIR / "frames" / f"frame_{index:05d}.png"
        center_path = OUTPUT_DIR / "frames" / f"frame_{index:05d}_center.png"
        image_links = "이미지 없음 — Label·예측 기록 보존"
        if full_path.is_file() and center_path.is_file():
            image_links = f"[Frame](frames/frame_{index:05d}.png) / [중앙](frames/frame_{index:05d}_center.png)"
        lines.append(
            f"| {index} | {record['run_relative_time_seconds']:.3f} | {record['change_type'] or '세 방식 동일'} | {truth} | "
            + " | ".join(values)
            + f" | {image_links} |"
        )
    lines += ["", "숫자 괄호는 Valid Candidate Count다. 새 표본은 원본을 보고 ON_TARGET / OFF_TARGET / MISSING으로 판단하며, 애매하면 보류로 남긴다.", ""]
    (OUTPUT_DIR / "manual_review.md").write_text("\n".join(lines), encoding="utf-8")

    cards = {}
    for record in records:
        index = record["frame_index"]
        rows = "".join(
            f"<tr><td>{name}</td><td>{escape(record['predictions'][name]['tracking_state'])}</td><td>{record['predictions'][name]['valid_candidate_count']}</td></tr>"
            for name in METHOD_NAMES
        )
        label = escape(record["ground_truth"] or "미검증 — 사용자가 원본으로 판단")
        images_html = '<p>검증 이미지 파일은 현재 없습니다. 사용자 Label과 알고리즘 예측은 아래에 보존되어 있습니다.</p>'
        if (OUTPUT_DIR / "frames" / f"frame_{index:05d}.png").is_file() and (OUTPUT_DIR / "frames" / f"frame_{index:05d}_center.png").is_file():
            images_html = (
                f'<div class="images"><figure><a href="frames/frame_{index:05d}.png" target="_blank"><img src="frames/frame_{index:05d}.png" alt="Frame {index} 원본"></a><figcaption>원본 전체 — 클릭하면 원본 크기로 열립니다.</figcaption></figure>'
                f'<figure><img class="crop" src="frames/frame_{index:05d}_center.png" alt="Frame {index} 중앙 Crop"><figcaption>Crosshair 중앙 320×320px Crop</figcaption></figure></div>'
            )
        cards[index] = (
            f'<section id="frame-{index}"><h2>Frame {index} · Run {record["run_relative_time_seconds"]:.3f}초</h2>'
            + images_html
            + f'<details><summary>알고리즘 예측 및 기존 사용자 Label</summary><p>사용자 Ground Truth: {label}</p>'
            f'<table><tr><th>방식</th><th>예측 상태</th><th>후보 수</th></tr>{rows}</table></details></section>'
        )
    answer_template = "\n".join(f"{record['frame_index']}: " for record in pending_records)
    review_instruction = '<p>사용자가 선정 표본의 Label을 모두 확인했고 Closing+Top-strip을 최종 MVP 정책으로 선택했습니다. 이 페이지는 실험 비교 기록입니다.</p>'
    if pending_records:
        review_instruction = '<p>새 표본은 먼저 원본으로 판단해주세요. 예측은 아래 접힌 영역에 있습니다. 이미지에는 알고리즘 윤곽선이나 상태를 그리지 않았습니다.</p>'
    gallery = (
        '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Day 12 원본 Frame 수동 검증</title>'
        '<style>body{font-family:system-ui,sans-serif;margin:24px auto;padding:0 20px;max-width:1320px;background:#f5f6f8;color:#18202c}section{background:white;padding:20px;margin:24px 0;border:1px solid #d9dfe8;border-radius:12px}.images{display:grid;grid-template-columns:2fr 1fr;gap:20px}figure{margin:0}img{width:100%;height:auto}.crop{image-rendering:pixelated}figcaption{font-size:14px;margin-top:8px;color:#4c5869}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #bbb}summary{cursor:pointer;margin:16px 0}pre{background:#e7ecf3;padding:16px}nav a{display:inline-block;margin:4px 8px}a{color:#1557b5}@media(max-width:800px){.images{grid-template-columns:1fr}}</style>'
        '<h1>Day 12 — 원본 Frame 수동 검증</h1>'
        + review_instruction
        + '<p>판정 기준: 단일 Target의 외곽 내부·경계에 Crosshair 중심점이 있으면 ON_TARGET, 밖이면 OFF_TARGET, Target을 하나로 결정할 수 없으면 MISSING입니다. 애매한 원본은 보류로 남겨주세요.</p>'
        f'<p>상태 변경 {state_change_count}개 중 표본 {state_sample_count}개를 선정했습니다. 후보 수만 변경된 Frame은 {count_only_change_count}개이며, 해당 표본은 {count_sample_count}개입니다. 판단이 남은 Frame: {len(pending_records)}개.</p>'
        '<nav>' + "".join(f'<a href="#frame-{record["frame_index"]}">{record["frame_index"]}</a>' for record in new_records) + '</nav>'
        '<p>다음 형식으로 채팅에 알려주세요. ON_TARGET / OFF_TARGET / MISSING / 보류를 사용할 수 있습니다.</p>'
        f'<pre>{escape(answer_template)}</pre>'
        + "".join(cards[record["frame_index"]] for record in new_records)
        + '<details><summary>Day 10에서 직접 확인한 기존 10개 Frame 다시 보기</summary>'
        + "".join(cards[record["frame_index"]] for record in legacy_records)
        + '</details><p>전체 예측: <a href="baseline_comparison.json">baseline_comparison.json</a> · 검증 표: <a href="manual_review.md">manual_review.md</a></p></html>'
    )
    (OUTPUT_DIR / "review.html").write_text(gallery, encoding="utf-8")


def write_comparison_results(summary: dict, changes: list[dict], representative_records: dict) -> dict:
    """자동 비교 결과와 제한된 수동 검증 계획을 JSON으로 저장한다."""
    state_samples = select_change_samples(changes, STATE_CHANGE, 12)
    count_samples = select_change_samples(changes, COUNT_ONLY_CHANGE, 4)
    manual_records = dict(representative_records)
    for record in state_samples + count_samples:
        manual_records[record["frame_index"]] = record

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manual_review_frames = sorted(manual_records.values(), key=lambda record: record["frame_index"])
    apply_manual_labels(OUTPUT_DIR / "manual_labels.json", manual_review_frames)

    change_counts = {STATE_CHANGE: 0, COUNT_ONLY_CHANGE: 0}
    for record in changes:
        change_counts[record["change_type"]] += 1

    legacy_verified_records = [
        record for record in manual_records.values()
        if record["ground_truth_source"] == "day10_user_verified"
    ]
    legacy_matches = {}
    for name in METHOD_NAMES:
        legacy_matches[name] = sum(
            record["predictions"][name]["tracking_state"] == record["ground_truth"]
            for record in legacy_verified_records
        )

    payload = {
        "status": "manual_validation_pending" if any(record["ground_truth"] is None for record in manual_review_frames) else "manual_validation_complete",
        "summary": summary,
        "change_counts": change_counts,
        "changed_frames": changes,
        "day10_ground_truth_source": (
            "docs/workflow/day10_representative_frame_validation_and_closing_experiment.md"
        ),
        "day10_verified_frame_count": len(legacy_verified_records),
        "day10_prediction_match_counts": legacy_matches,
        "sampling": {
            "state_change_budget": 12,
            "candidate_count_only_budget": 4,
            "state_change_indices": [record["frame_index"] for record in state_samples],
            "candidate_count_only_indices": [record["frame_index"] for record in count_samples],
            "note": "해당 유형이 적으면 실제 존재하는 Frame만 선택한다.",
        },
        "manual_review_frames": manual_review_frames,
        "manual_validation": summarize_manual_validation(manual_review_frames),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT_DIR / "baseline_comparison.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"변경 Frame 유형별 개수: {change_counts}")
    print(f"Tracking State 변경 표본: {payload['sampling']['state_change_indices']}")
    print(f"Candidate Count만 변경된 표본: {payload['sampling']['candidate_count_only_indices']}")
    print(f"Day 10 수동 Label {len(legacy_verified_records)}개와의 일치: {legacy_matches}")
    print(f"전체 수동 검증 표본 {payload['manual_validation']['verified_frame_count']}개와의 일치: {payload['manual_validation']['match_counts']}")
    print(f"자동 비교 결과 저장: {result_path}")
    return payload


def main(export_images: bool = False) -> None:
    state_counts = {
        "original": {
            "ON_TARGET": 0,
            "MISSING": 0,
            "OFF_TARGET": 0,
        },
        "closing_only": {
            "ON_TARGET": 0,
            "MISSING": 0,
            "OFF_TARGET": 0,
        },
        "closing_top_strip": {
            "ON_TARGET": 0,
            "MISSING": 0,
            "OFF_TARGET": 0,
        },
    }

    # main.py와 같은 입력 파일 검증을 사용한다.
    if not VIDEO_PATH.exists():
        raise FileNotFoundError("비디오 파일이 존재하지 않습니다.")
    if not VIDEO_PATH.is_file():
        raise ValueError("올바른 비디오 파일이 아닙니다.")

    print(f"{VIDEO_PATH.resolve()} 비디오 파일을 확인했습니다.")

    video_capture = cv2.VideoCapture(str(VIDEO_PATH))

    try:
        # 파일이 존재해도 OpenCV가 실제로 열 수 있는지 따로 확인한다.
        if not video_capture.isOpened():
            raise RuntimeError("비디오 파일을 열 수 없습니다.")
        print("비디오 열기 성공")

        # 기존 Production 실행과 같은 영상 메타데이터 조건을 검사한다.
        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        video_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        reported_frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)

        if not math.isfinite(video_fps) or video_fps <= 0:
            raise ValueError("FPS는 0보다 큰 유한한 숫자여야 합니다.")
        if not math.isfinite(video_width) or video_width <= 0:
            raise ValueError("영상 너비는 0보다 큰 유한한 숫자여야 합니다.")
        if not math.isfinite(video_height) or video_height <= 0:
            raise ValueError("영상 높이는 0보다 큰 유한한 숫자여야 합니다.")
        if video_fps != 60.0:
            raise ValueError(f"지원하지 않는 FPS입니다. 실제 FPS: {video_fps}")

        print(f"FPS: {video_fps}")
        print(f"영상 너비(픽셀): {video_width}")
        print(f"영상 높이(픽셀): {video_height}")

        # None은 미설정이며, 영상의 첫 시각인 0초와 구분한다.
        known_run_start_seconds = KNOWN_RUN_START_SECONDS
        if known_run_start_seconds is None:
            raise ValueError("시작 위치가 존재하지 않습니다.")
        if not math.isfinite(known_run_start_seconds):
            raise ValueError("시작 위치는 유한한 숫자여야 합니다.")
        if known_run_start_seconds < 0:
            raise ValueError("시작 위치는 음수일 수 없습니다.")

        run_end_seconds = known_run_start_seconds + RUN_DURATION_SECONDS
        print(f"Run 시작(초): {known_run_start_seconds}")
        print(f"Run 종료(초): {run_end_seconds}")

        # 여기부터는 main.py의 순차 Decode와 Run 구간 선택 흐름을 재사용한다.
        decoded_frame_count = 0
        run_segment_frame_count = 0
        first_segment_frame_index = None
        first_segment_frame_time_seconds = None
        last_segment_frame_index = None
        last_segment_frame_time_seconds = None
        frame_coverage_end_seconds = 0.0
        change_records = []
        representative_records = {}

        # 영상 처음부터 끝까지 순서대로 읽고, Run 구간에 속한 Frame만 비교 대상으로 삼는다.
        while True:
            read_success, frame = video_capture.read()
            if not read_success:
                break

            current_frame_index = decoded_frame_count
            # 영상 시작 기준의 시각이다. Run 시작 기준의 상대 시각과 구분한다.
            frame_time_seconds = current_frame_index / video_fps

            # 기존 조건을 유지한다: 시작 포함, 종료 제외.
            if known_run_start_seconds <= frame_time_seconds < run_end_seconds:
                if first_segment_frame_index is None:
                    first_segment_frame_index = current_frame_index

                last_segment_frame_index = current_frame_index
                run_segment_frame_count += 1

                # 사용자가 연결한 Frame 비교와 방식별 상태 집계다.
                comparison_results = compare_frame(frame)
                for method_name, method_result in comparison_results.items():
                    state = method_result["tracking_state"]

                    state_counts[method_name][state] += 1

                # B 기준: 상태 또는 후보 수가 하나라도 다를 때만 변경 목록에 기록한다.
                change_type = classify_frame_change(comparison_results)
                if change_type is not None or current_frame_index in DAY10_MANUAL_LABELS:
                    manual_label = DAY10_MANUAL_LABELS.get(current_frame_index)
                    record = {
                        "frame_index": current_frame_index,
                        "video_time_seconds": frame_time_seconds,
                        "run_relative_time_seconds": frame_time_seconds - known_run_start_seconds,
                        "change_type": change_type,
                        "predictions": comparison_results,
                        "ground_truth": manual_label,
                        "ground_truth_source": "day10_user_verified" if manual_label is not None else None,
                        "review_status": "previously_verified_day10" if manual_label is not None else "not_manually_reviewed",
                    }
                    if change_type is not None:
                        change_records.append(record)
                    if current_frame_index in DAY10_MANUAL_LABELS:
                        representative_records[current_frame_index] = record

            # Run 바깥 Frame도 읽은 전체 Frame 수에는 포함한다.
            decoded_frame_count += 1
            frame_coverage_end_seconds = (current_frame_index + 1) / video_fps

        # 아래도 main.py의 구간 경계와 Decode 완성도 확인을 재사용한다.
        if (
            first_segment_frame_index is not None
            and last_segment_frame_index is not None
        ):
            first_segment_frame_time_seconds = first_segment_frame_index / video_fps
            last_segment_frame_time_seconds = last_segment_frame_index / video_fps

        print("\n[분석 구간 및 디코딩 검증]")
        if frame_coverage_end_seconds >= run_end_seconds:
            print("에임 트래킹 분석 구간 완성 상태: 완료")
        else:
            print("에임 트래킹 분석 구간 완성 상태: 미완료")
            print("필요한 분석 종료 시간까지 프레임을 디코딩하지 못했습니다.")

        print(f"분석 구간의 첫 프레임 인덱스: {first_segment_frame_index}")
        print(f"분석 구간의 마지막 프레임 인덱스: {last_segment_frame_index}")
        print(f"분석 구간의 첫 프레임 시간(초): {first_segment_frame_time_seconds}")
        print(f"분석 구간의 마지막 프레임 시간(초): {last_segment_frame_time_seconds}")
        print(f"분석 구간 프레임 수: {run_segment_frame_count}")
        print(f"메타데이터에 기록된 전체 프레임 수: {reported_frame_count}")
        print(f"성공적으로 디코딩한 전체 프레임 수: {decoded_frame_count}")
        print(f"성공적으로 디코딩한 시간 범위의 끝(초): {frame_coverage_end_seconds}")

        # 실제 Decode 범위와 방식별 집계가 불완전하면 정상 결과로 저장하지 않는다.
        expected_run_frame_count = round(RUN_DURATION_SECONDS * video_fps)
        if frame_coverage_end_seconds < run_end_seconds:
            raise RuntimeError("요청한 Run 종료 시각까지 디코딩하지 못했습니다.")
        if run_segment_frame_count != expected_run_frame_count:
            raise RuntimeError(
                f"Run Frame 수가 일치하지 않습니다: {run_segment_frame_count} != {expected_run_frame_count}"
            )

        for method_name, counts in state_counts.items():
            total = sum(counts.values())
            print(method_name, counts, "합계:", total)
            if total != run_segment_frame_count:
                raise RuntimeError(f"{method_name}의 상태 합계가 Run Frame 수와 다릅니다.")
            print(f"Run Frame 수와 일치: {total == run_segment_frame_count}")

        payload = write_comparison_results(
            {
                "video_path": str(VIDEO_PATH.resolve()),
                "fps": video_fps,
                "frame_width": video_width,
                "frame_height": video_height,
                "decoded_frame_count": decoded_frame_count,
                "run_segment_frame_count": run_segment_frame_count,
                "first_run_frame_index": first_segment_frame_index,
                "last_run_frame_index": last_segment_frame_index,
                "state_counts": state_counts,
                "production_contract": DETECTION_POLICY,
                "baselines": {
                    "original": "HSV -> external contour -> area >= 150 -> single candidate",
                    "closing_only": "HSV -> 5x5 closing -> external contour -> area >= 150 -> single candidate",
                    "closing_top_strip": "Closing-only -> exclude bbox y + height <= 30 -> single candidate",
                },
            },
            change_records,
            representative_records,
        )
        # 이미지 정리 요청을 존중해 추출은 명시적으로 선택했을 때만 실행한다.
        if export_images:
            export_review_frames(payload["manual_review_frames"])
        write_review_report(payload)
        print(f"수동 검증 표와 원본 갤러리: {OUTPUT_DIR / 'review.html'}")
    finally:
        # 검증 중 예외가 발생해도 영상 자원을 해제한다.
        video_capture.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="전체 Run의 세 Detection Baseline을 비교합니다.")
    parser.add_argument("--export-images", action="store_true", help="선정한 원본·중앙 Crop PNG도 추출합니다.")
    args = parser.parse_args()
    main(export_images=args.export_images)
