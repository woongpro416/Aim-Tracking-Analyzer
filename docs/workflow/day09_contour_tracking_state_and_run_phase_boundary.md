# Day 09 — Contour Tracking State and Run Phase Boundary

## Today's Goal

Day 09에서는 Day 08의 Frame별 Target Observation과 화면 중앙 Crosshair의 관계를 해석해 `ON_TARGET`, `OFF_TARGET`, `MISSING` 상태를 만들었다. 또한 최초 `ON_TARGET` Frame을 찾아 Run을 Initial Acquisition과 Tracking Maintenance로 나누는 경계를 정의했다.

```text
Target Detection
+ Screen Center Crosshair
-> External Contour Point Test
-> ON_TARGET / OFF_TARGET / MISSING
-> First On-target
-> Run-level Phase Boundary Summary
```

Day 09 결과는 Aim Accuracy나 Skill Score가 아니다. 현재 선택한 Domain Contract에 따라 각 Frame의 Target과 Crosshair 관계를 분류하고, Run Phase 경계를 표현한 Derived Result다.

## Primary Coder and AI-assisted Work

Primary Coder는 On-target Domain Contract, Crosshair 좌표 의미, Raw Observation과 Tracking State 분리 방식, First On-target Frame의 Phase 포함 방식을 직접 선택했다. 또한 Contour 반환 계약, Point-in-Contour 판정, Tracking State 분류, 별도 Sequence 생성, 상태 Count, First On-target 탐색과 Run Phase Summary를 작은 단위로 직접 구현하고 실행했다.

AI는 각 선택지의 의미와 Trade-off 설명, 작은 TODO 제시, Python 문법과 OpenCV API 설명, 코드 Review, 오류 원인 분석, 출력 정리와 문서화를 보조했다. 마지막 가독성 정리와 출력 라벨 정리는 사용자의 명시적 요청에 따라 AI가 직접 수정했다.

따라서 Day 09은 사용자가 Domain Rule과 핵심 로직을 직접 선택·구현하고 AI가 학습, Review와 정리를 보조한 `AI-assisted development`다.

## On-target Domain Contract

On-target은 Bounding Box나 임의 Radius가 아니라 Target의 External Contour를 기준으로 판정한다.

```text
단일 Target 결정 가능
+ Crosshair Point가 External Contour 내부 또는 경계
-> ON_TARGET

단일 Target 결정 가능
+ Crosshair Point가 External Contour 외부
-> OFF_TARGET

단일 Target 결정 불가능
-> MISSING
```

Target은 원형 또는 타원형에 가까우므로 Bounding Box를 사용하면 사각형 모서리까지 Target으로 과대 판정할 수 있다. Mask의 한 픽셀을 직접 검사하는 방식도 사용하지 않았다. Crosshair가 Target 내부 Mask에 작은 검은 Hole을 만들 수 있기 때문이다.

`cv2.findContours()`의 `RETR_EXTERNAL`로 얻은 외부 실루엣과 `cv2.pointPolygonTest()`를 사용한다. `measureDist=False`일 때 반환값의 의미는 다음과 같다.

| 반환값 | 의미 | Domain 결과 |
|---:|---|---|
| 양수 | Contour 내부 | `ON_TARGET` |
| `0` | Contour 경계 | `ON_TARGET` |
| 음수 | Contour 외부 | `OFF_TARGET` |

경계는 Target 영역에 포함된 것으로 정의했다.

## Transient Contour Contract

`detect_target()`은 단일 Target을 결정한 경우 선택된 External Contour를 여섯 번째 값으로 반환한다.

```text
단일 유효 후보 -> selected_contour
후보 없음 또는 여러 개 -> None
```

Contour는 현재 Frame의 Point-in-Contour 판정에만 일시적으로 사용하고 Observation에는 저장하지 않는다. 반면 Target Center는 향후 OFF_TARGET Direction, Distance와 Recovery 분석에 사용할 수 있으므로 기존 Raw Observation에서 계속 보존한다.

```text
Contour
-> 현재 Frame의 On-target 판정용 임시 형상

Target Center
-> 이후 분석을 위해 보존하는 위치 정보
```

Contour를 저장하지 않으므로 On-target Contract가 바뀌면 저장된 Raw Observation만으로 Contour 기반 상태를 다시 계산할 수 없다. 이 경우 영상을 다시 디코딩하고 검출해야 한다.

## Crosshair Contract

현재 MVP 입력은 `1920 × 1080`으로 고정했다. Crosshair는 Video Metadata로부터 계산한 정수 화면 중앙 좌표다.

```python
crosshair_x = int(video_width) // 2
crosshair_y = int(video_height) // 2
```

현재 영상의 결과는 다음과 같다.

```text
Crosshair X: 960
Crosshair Y: 540
```

홀수 해상도의 중앙 좌표 의미는 현재 MVP 범위에서 Deferred했다.

## Raw Observation and Tracking State Separation

Day 08의 `target_observations`는 Detector가 관찰한 사실을 보존하는 Raw Observation으로 유지했다.

```python
{
    "frame_index": ...,
    "frame_time_seconds": ...,
    "status": ...,
    "center": ...,
    "valid_candidate_count": ...,
}
```

Crosshair와 Target의 관계를 해석한 결과는 별도 `tracking_state_sequence`에 저장했다.

```python
{
    "frame_index": ...,
    "frame_time_seconds": ...,
    "tracking_state": ...,
}
```

두 Sequence는 모든 Run Frame에서 각각 하나의 항목을 생성한다. `frame_index`를 통해 Raw Target Center와 Derived Tracking State를 다시 연결할 수 있다.

## Full-run Tracking State Result

60초 Run의 `3,600` Frame을 분류한 결과다.

| Tracking State | Frame Count |
|---|---:|
| `ON_TARGET` | `2136` |
| `OFF_TARGET` | `1183` |
| `MISSING` | `281` |
| Total | `3600` |

다음 정합성 조건이 모두 `True`임을 확인했다.

```text
Tracking State Count == Raw Observation Count == Run Segment Frame Count

ON_TARGET + OFF_TARGET + MISSING == 3600

Tracking MISSING Count == Raw 미결정 Count == 281

ON_TARGET + OFF_TARGET == 단일 Target 결정 Count == 3319
```

`MISSING`은 `OFF_TARGET`이 아니다. Target 위치를 하나로 결정하지 못한 Observation Gap으로 유지하며 보간, Forward Fill, Backward Fill이나 Center 재사용을 하지 않았다.

## First On-target Result

Tracking State Sequence를 시간순으로 순회해 최초 `ON_TARGET` Observation을 찾았다.

```text
First On-target Frame Index: 356
First On-target Frame Time: 5.933333333333334초
First On-target Run-relative Time: 0.0초
```

현재 Run에서는 Run Start Frame부터 `ON_TARGET`이 관찰됐다.

First On-target이 관찰되지 않은 경우에는 이를 곧바로 사용자가 한 번도 Target을 맞추지 못한 것으로 해석하지 않는다. Missing 비율에 따른 Confidence Rule은 아직 정의하지 않았으며, Boundary Frame, Time과 Duration은 `None`으로 유지하는 방향을 선택했다.

## Phase Boundary Contract

First On-target Frame은 Tracking Maintenance의 첫 Frame으로 정의했다.

```text
Initial Acquisition:
[run_start, first_on_target_time)

Tracking Maintenance:
[first_on_target_time, run_end)
```

Frame Index 기준으로는 다음과 같다.

```text
Initial Acquisition:
frame_index < first_on_target_frame_index

Tracking Maintenance:
frame_index >= first_on_target_frame_index
```

현재 Run의 First On-target은 Frame `356`으로 Run Start와 같다.

```text
Initial Acquisition: [356, 356) -> 빈 구간
Tracking Maintenance: [356, 3956) -> Frame 356~3955
Initial Acquisition Duration: 0.0초
```

`[356, 356)`은 Frame Count와 Duration이 0인 유효한 빈 구간이다.

## Run-level Phase Summary

Phase는 Frame마다 독립적으로 검출되는 상태가 아니라 First On-target 하나가 정하는 Run-level Boundary다. 따라서 모든 Frame에 Phase 문자열을 반복 저장하지 않고 최소 Summary로 묶었다.

```python
{
    "first_on_target_observed": True,
    "phase_boundary_frame_index": 356,
    "phase_boundary_time_seconds": 5.933333333333334,
    "initial_acquisition_duration_seconds": 0.0,
}
```

Run Start와 Run End는 기존 값이 있으므로 Summary에 중복 저장하지 않았다.

## Unit Tests

기존 Target Detection Test는 단일 후보에서만 `selected_contour`가 존재하는지 추가로 검증한다.

새 Tracking State Test는 다음 여섯 동작을 검증한다.

1. Crosshair가 Contour 내부이면 `True`다.
2. Crosshair가 Contour 경계이면 `True`다.
3. Crosshair가 Contour 외부이면 `False`다.
4. Target Contour가 `None`이면 `MISSING`이다.
5. Contour 내부는 `ON_TARGET`으로 분류된다.
6. Contour 외부는 `OFF_TARGET`으로 분류된다.

전체 회귀 테스트 결과는 다음과 같다.

```text
12 passed in 0.14s
```

## Source Changes

### `src/target_detection.py`

- `TargetContour` 타입 별칭 추가
- `DetectionResult`에 선택된 Contour 추가
- 단일 후보에서만 실제 Contour 반환
- 후보 없음 또는 여러 개에서는 Contour `None` 반환

### `src/tracking_state.py`

- `ON_TARGET`, `OFF_TARGET`, `MISSING` 상수 정의
- External Contour 내부·경계 판정 함수 추가
- Contour 존재 여부와 Point Test를 Tracking State로 변환

### `src/main.py`

- Video Metadata 기반 Screen Center Crosshair 계산
- Raw Observation과 별도 Tracking State Sequence 생성
- 상태별 Count와 Sequence 정합성 검증
- First On-target 탐색과 Run-relative Time 계산
- Run-level Phase Summary 생성과 한글 검증 출력 추가

### `tests/test_target_detection.py`

- 단일 후보에서 Contour가 존재하는지 검증
- 미결정 상태에서 Contour가 `None`인지 검증

### `tests/test_tracking_state.py`

- Synthetic 사각형으로 내부, 경계와 외부 Point 검증
- `ON_TARGET`, `OFF_TARGET`, `MISSING` 분류 검증

## Deferred Work

대표 Frame Manual Validation은 다음 세션으로 이월했다.

- `ON_TARGET` Frame 1~2개 확인
- `OFF_TARGET` Frame 1~2개 확인
- `MISSING` Frame 1~2개 확인
- First On-target Frame 확인
- 모든 Frame 이미지를 저장하지 않고 선택된 Frame만 시각 검증

이 검증이 끝나기 전에는 Day 10의 Off-target Event Duration Metric으로 확장하지 않는다.

## Limitations

- 현재 입력과 Crosshair Contract는 `1920 × 1080` 영상에 맞춰 검증했다.
- 홀수 해상도의 화면 중앙 좌표 의미는 정의하지 않았다.
- Contour를 저장하지 않으므로 Contract 변경 시 영상 재검출이 필요하다.
- First On-target이 없을 때의 Missing Confidence Threshold는 정의하지 않았다.
- 대표 Frame Manual Validation은 아직 완료하지 않았다.
- Tracking State Count는 Aim Accuracy나 Skill Score가 아니다.

## Next Slice

1. 상태별 대표 Frame Index를 최소 개수로 선택한다.
2. 선택된 Frame에 External Contour와 Crosshair를 표시한다.
3. `ON_TARGET`, `OFF_TARGET`, `MISSING`과 First On-target 의미를 사람이 확인한다.
4. Manual Validation 완료 후 Day 10 Off-target Event Metric으로 이동한다.

## Recommended Commit Message

```text
feat: add contour-based tracking states and run phase boundary
```

## Study Notes

- External Contour 내부 또는 경계에 Crosshair가 있으면 `ON_TARGET`이다.
- `MISSING`은 Target 위치를 결정하지 못한 상태이며 `OFF_TARGET`과 다르다.
- Raw Detection과 Tracking State는 별도 Sequence로 보존하고 `frame_index`로 연결한다.
- First On-target Frame은 Tracking Maintenance의 첫 Frame이다.
- 현재 Run은 시작 Frame부터 ON_TARGET이므로 Initial Acquisition Duration은 `0.0초`다.
