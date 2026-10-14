"""연속된 OFF_TARGET Frame을 구간으로 묶고 각 구간의 지속 시간을 계산한다.

ON_TARGET 또는 MISSING에서 구간을 종료하며, 경계는 [시작, 종료)로 기록한다.
"""


def group_off_target_intervals(
        tracking_state_sequence: list[dict],
        fps: float,
) -> list[dict]:
    intervals = []
    interval_start = None

    for record in tracking_state_sequence:
        frame_index = record["frame_index"]
        current_state = record["tracking_state"]

        if current_state == "OFF_TARGET":
            if interval_start is None:
                interval_start = frame_index
        elif current_state == "ON_TARGET" or current_state == "MISSING":
            if interval_start is not None:
                off_target_frame_count = frame_index - interval_start
                off_target_duration_seconds = off_target_frame_count / fps
                interval = {
                    "start_frame_index": interval_start,
                    "end_frame_index_exclusive": frame_index,
                    "end_reason": current_state,
                    "off_target_frame_count": off_target_frame_count,
                    "off_target_duration_seconds": off_target_duration_seconds,
                }
                intervals.append(interval)
                interval_start = None

        current_interval_description = "없음"
        if interval_start is not None:
            current_interval_description = f"Frame {interval_start}부터"

        print(
            f"[Frame {frame_index}] 상태: {current_state} | "
            f"진행 중 구간: {current_interval_description} | "
            f"저장 완료: {len(intervals)}개"
        )

    if interval_start is not None:
        off_target_frame_count = (frame_index + 1 ) - interval_start
        off_target_duration_seconds = off_target_frame_count / fps
        end_interval = {
            "start_frame_index": interval_start,
            "end_frame_index_exclusive": frame_index + 1,
            "end_reason": "RUN_END",
            "off_target_frame_count": off_target_frame_count,
            "off_target_duration_seconds": off_target_duration_seconds,
        }
        intervals.append(end_interval)

    return intervals


def print_interval_summary(intervals: list[dict]) -> None:
    """저장된 OFF_TARGET 구간을 Frame 경계와 종료 원인으로 출력한다."""
    print()
    print(f"OFF_TARGET 구간 결과: {len(intervals)}개")

    if len(intervals) == 0:
        print("관측된 OFF_TARGET 구간이 없습니다.")
        return

    print("Frame 구간 [시작, 종료): 종료 번호는 포함하지 않습니다.")
    end_reason_descriptions = {
        "ON_TARGET": "ON_TARGET 관측",
        "MISSING": "관측 불가",
        "RUN_END": "Run 종료",
    }

    for interval_number, interval in enumerate(intervals, start=1):
        end_reason = interval["end_reason"]
        print(
            f"구간 {interval_number}: "
            f"Frame [{interval['start_frame_index']}, "
            f"{interval['end_frame_index_exclusive']}) | "
            f"종료 원인: {end_reason} ({end_reason_descriptions[end_reason]})"
        )


if __name__ == "__main__":
    sample_sequence = [
        {"frame_index": 100,
         "frame_time_seconds": 100 / 60, "tracking_state": "ON_TARGET"},
        {"frame_index": 101,
         "frame_time_seconds": 101 / 60, "tracking_state": "OFF_TARGET"},
        {"frame_index": 102,
         "frame_time_seconds": 102 / 60, "tracking_state": "OFF_TARGET"},
    ]

    sample_intervals = group_off_target_intervals(sample_sequence, fps=60.0)
    print_interval_summary(sample_intervals)
    print(sample_intervals)
