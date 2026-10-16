"""OFF_TARGET 구간 목록의 횟수와 지속 시간을 Run 단위로 집계한다.

평균은 전체 지속 시간을 구간 수로 나누며, 구간이 없으면 None으로 기록한다.
"""


def calculate_off_target_metrics(intervals: list[dict]) -> dict:
    interval_count = len(intervals)
    total_frame_count = 0
    total_duration_seconds = 0.0

    for interval in intervals:
        total_frame_count = total_frame_count + interval["off_target_frame_count"]
        total_duration_seconds = total_duration_seconds + interval["off_target_duration_seconds"]

    off_target_average_interval_duration_seconds: float | None = None

    if interval_count > 0:
        off_target_average_interval_duration_seconds = total_duration_seconds / interval_count

    return {
        "off_target_interval_count": interval_count,
        "total_off_target_frame_count": total_frame_count,
        "total_off_target_duration_seconds": total_duration_seconds,
        "off_target_average_interval_duration_seconds": off_target_average_interval_duration_seconds,
    }


def calculate_observed_on_target_ratio(
        on_target_frame_count: int,
        off_target_frame_count: int,
) -> float | None:
    if on_target_frame_count < 0 or off_target_frame_count < 0:
        raise ValueError("조준,오조준의 Frame 값은 음수가 될 수 없습니다.")

    observed_frame_count = on_target_frame_count + off_target_frame_count

    if observed_frame_count == 0:
        return None

    on_target_ratio = (on_target_frame_count / observed_frame_count)

    return on_target_ratio



if __name__ == "__main__":
    sample_intervals = [
        {"off_target_frame_count": 2,
         "off_target_duration_seconds": 2 / 60},
        {"off_target_frame_count": 1,
         "off_target_duration_seconds": 1 / 60},
    ]

    print(calculate_off_target_metrics(sample_intervals))
    print(calculate_off_target_metrics([]))
    print(calculate_observed_on_target_ratio(3, 1))
    print(calculate_observed_on_target_ratio(0, 0))
