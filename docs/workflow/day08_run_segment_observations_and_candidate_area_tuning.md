# Day 08 — Run Segment Observations and Candidate Area Tuning

## Today's Goal

Day 08에서는 Day 07의 단일 프레임 타겟 검출 함수를 60초 Run Segment의 모든 프레임에 연결했다. 각 프레임의 검출 결과를 Observation으로 보존하고, 전체 Run에서 발견된 작은 색상 잡음을 근거로 최소 후보 면적을 조정했다.

```text
60초 Run Segment Frame
-> HSV Binary Mask
-> External Contours
-> Minimum Area Filter
-> 단일 후보 여부 결정
-> Frame Observation 저장
-> 상태별 Count와 정합성 검증
```

Day 08의 목적은 Aim 성능 점수를 계산하는 것이 아니라, 이후 Tracking과 On-target 판정이 사용할 신뢰 가능한 프레임 단위 관찰값을 만드는 것이다.

## Primary Coder and AI-assisted Work

Primary Coder는 `target_observations` 목록, 상태 분기, 상태별 Count, 대표 Missing Observation 출력, 검증 이미지 저장 로직과 작은 청록색 영역을 검사하는 pytest를 단계적으로 직접 작성하고 실행했다. 오류가 발생했을 때 `KeyError: -1`, 잘못된 이미지 확장자, Python Import Path와 pytest 설치 문제를 직접 수정하며 실행 결과를 확인했다.

AI는 각 TODO의 도메인 의미와 적절한 코드 위치를 설명하고, 코드 Review, 오류 원인 분석과 검증 이미지 해석을 보조했다. 사용자가 최종 세밀 조정을 명시적으로 위임한 뒤에는 AI가 전체 3,600프레임의 면적 기준 Sweep, 경계 프레임 확인, 최종 `MIN_CANDIDATE_AREA = 150.0` 선택, 임시 이미지 삭제와 전체 코드 정리를 수행했다.

따라서 Day 08은 사용자가 핵심 흐름을 직접 학습·구현하고, 최종 Threshold 실험과 정리를 AI가 보조한 `AI-assisted development`다.

## Is the Target Detector AI?

현재 Target Detector 자체에는 AI 또는 Machine Learning Model이 들어가지 않는다.

| 구분 | 현재 사용 여부 | 설명 |
|---|---|---|
| HSV 색상 범위 | 사용 | 사람이 정한 범위로 청록색 픽셀 분리 |
| Contour | 사용 | 연결된 Mask 영역의 외곽선 추출 |
| Area Threshold | 사용 | 작은 색상 조각을 규칙으로 제외 |
| Bounding Box Center | 사용 | 검출 영역의 사각형 중심 계산 |
| 학습 데이터 | 미사용 | 모델 학습 과정 없음 |
| YOLO·CNN·ONNX | 미사용 | 가중치 또는 추론 모델 없음 |

`detect_target()`이라는 이름 때문에 AI 추론처럼 보일 수 있지만, 현재 구현은 입력이 같으면 항상 같은 결과를 내는 Classical Computer Vision 기반 규칙식이다.

AI가 들어간 영역은 실행 중인 검출 Pipeline이 아니라 개발 과정이다. AI Coding Assistant가 설명, 코드 검수, Threshold Sweep과 Refactoring을 보조했다. Portfolio에서는 다음처럼 구분하는 것이 정확하다.

```text
Product Algorithm: Rule-based OpenCV target detection
Development Process: AI-assisted implementation and validation
```

## Frame Observation Contract

분석 구간의 각 프레임을 다음 Dictionary 형태로 저장했다.

```python
observation = {
    "frame_index": current_frame_index,
    "frame_time_seconds": frame_time_seconds,
    "status": status,
    "center": center,
    "valid_candidate_count": valid_candidate_count,
}
```

Dictionary를 사용한 이유는 한 프레임의 Index, Time, 상태와 위치를 하나의 묶음으로 보존하면서 각 값의 의미를 Key로 확인할 수 있기 때문이다. Observation은 프레임 순서가 중요하므로 List에 차례대로 추가했다.

## Observation States

면적 조건을 통과한 후보 수에 따라 세 가지 상태를 기록했다.

| 조건 | 상태 | Center |
|---|---|---|
| 유효 후보 `1개` | `타겟 검출됨` | Bounding Box 중심 좌표 |
| 유효 후보 `0개` | `타겟 미결정: 유효 후보 없음` | `None` |
| 유효 후보 `2개 이상` | `타겟 미결정: 유효 후보 여러 개` | `None` |

`center = None`은 좌표 `(0, 0)`이나 빈 좌표가 아니다. 해당 프레임에서 타겟 위치를 하나로 결정하지 않았다는 명시적인 상태다.

상태 문자열은 `main.py`의 상수로 분리해 분기와 집계에서 같은 값을 사용하도록 정리했다.

## Full-run Observation and Validation

Known Run Start `5.933333333333334초`부터 60초 동안 총 `3,600`프레임을 관찰했다.

다음 두 정합성 조건이 모두 `True`임을 확인했다.

```text
Run Segment Frame Count == Observation Count

Detected Count
+ No-candidate Count
+ Ambiguous Count
== Observation Count
```

첫 번째와 마지막 Observation은 다음과 같다.

```text
First Frame Index: 356
First Center: (958.0, 544.0)

Last Frame Index: 3955
Last Center: (980.0, 512.0)
```

## Missing Observation Review

`유효 후보 없음` 상태가 모두 검출 실패인 것은 아니었다.

- Frame `851`, `852`: 기존 타겟이 사라지는 애니메이션 중간 상태
- Frame `2244`, `3799`: 화면에 타겟이 실제로 없는 전환 구간
- Frame `858~861`: 희미한 원형 잔상이 남은 소멸 애니메이션
- Frame `864`: 육안으로 확인되는 타겟이 없는 상태

따라서 Target이 없는 전환 시간과 소멸 애니메이션을 억지로 `검출됨`으로 바꾸지 않았다. Day 08의 Raw Observation에서는 이 프레임들을 `center = None`으로 보존한다.

## Why `MIN_CANDIDATE_AREA = 150.0`?

### 1. `50.0`에서 발견한 문제

초기 `MIN_CANDIDATE_AREA = 1.0`은 면적이 0인 점·선 형태만 제외하므로 작은 배경 조각도 유효 후보가 됐다. 작은 청록색 사각형 Test를 추가한 뒤 기준을 `50.0`으로 올렸지만, 전체 Run에서는 여전히 `21`프레임이 후보 여러 개 상태로 남았다.

대표 프레임을 확인한 결과 실제 타겟은 하나였고, 함께 검출된 추가 후보는 멀리 떨어진 작은 청록색 배경 조각이었다.

| Frame | Main Target Area | Extra Fragment Area |
|---:|---:|---:|
| `737` | `22964.5` | `58.5` |
| `2072` | `16429.0` | `56.5` |
| `3749` | `16354.5` | `57.5` |

전체 Ambiguous Frame에서 작은 추가 후보의 최대 면적은 `106.5`였다.

### 2. 전체 3,600프레임 Threshold Sweep

한두 프레임만 보고 값을 정하지 않고 동일한 60초 구간에 여러 면적 기준을 적용했다.

| Minimum Area | 단일 후보 | 후보 없음 | 후보 여러 개 | 단일 후보 결정률 |
|---:|---:|---:|---:|---:|
| `1` | `2545` | `242` | `813` | `70.69%` |
| `25` | `3218` | `273` | `109` | `89.39%` |
| `40` | `3289` | `275` | `36` | `91.36%` |
| `50` | `3303` | `276` | `21` | `91.75%` |
| `75` | `3313` | `281` | `6` | `92.03%` |
| `100` | `3318` | `281` | `1` | `92.17%` |
| `150` | `3319` | `281` | `0` | `92.19%` |
| `2000` | `3319` | `281` | `0` | `92.19%` |
| `3000` | `3276` | `324` | `0` | `91.00%` |

### 3. 최종 선택 이유

`150.0`을 선택한 이유는 다음과 같다.

1. 관찰된 작은 잡음의 최대 면적 `106.5`보다 크다.
2. 전체 Run에서 후보 여러 개 상태를 `0`으로 줄인 가장 작은 실험값이다.
3. `150~2000`에서 집계 결과가 동일해 일시적인 한 점이 아닌 안정 구간의 시작값이다.
4. `3000`부터 정상 후보까지 제거되며 후보 없음이 증가하므로 지나치게 큰 값은 피했다.
5. `50`에서는 검출됐던 면적 `50~66.5`의 다섯 프레임을 확인한 결과 안정된 타겟이 아니라 소멸 잔상 또는 실제 공백이었다.

즉, `150`은 가장 높은 검출률을 만들기 위해 고른 임의의 숫자가 아니다. 확인한 잡음은 제거하면서 정상 타겟과 충분한 간격을 두고, 과도한 Filtering을 시작하기 전의 가장 작은 안정값이다.

`cv2.contourArea()`의 값은 흰색 픽셀 개수와 완전히 같은 값이 아니라 Contour가 둘러싼 기하학적 면적이며 단위는 제곱픽셀로 해석한다.

## Final Run Result

최종 `MIN_CANDIDATE_AREA = 150.0`을 적용한 결과다.

| Observation | Result |
|---|---:|
| Run Segment Frames | `3600` |
| Observation Count | `3600` |
| Single-target Frames | `3319` |
| No-candidate Frames | `281` |
| Ambiguous Frames | `0` |
| Single-target Decision Rate | `92.19%` |
| Segment Completeness | `Complete` |

`92.19%`는 명중률이나 Aim Tracking 점수가 아니다. 전체 분석 프레임 중 유효 후보를 정확히 하나로 결정한 프레임의 비율이다.

## Unit Tests

pytest는 다음 여섯 동작을 검증한다.

1. 빈 BGR 프레임에는 후보가 없다.
2. 정상 크기의 청록색 원 하나는 검출된다.
3. 정상 크기의 청록색 원 두 개는 Ambiguous 상태다.
4. 어두운 청록색 영역은 HSV 밝기 조건을 통과하지 못한다.
5. Mask는 `(높이, 너비)` 형태의 단일 채널 `uint8` 배열이다.
6. 이전 기준 `50`은 통과할 수 있지만 새 기준 `150`보다 작은 면적 `121`의 청록색 잡음은 제외된다.

최종 실행 결과는 다음과 같다.

```text
6 passed in 0.13s
```

## Code and Output Cleanup

- `main.py`에서 일회성 검증 이미지 저장과 특정 Frame Index 상수를 제거했다.
- 반복되던 Observation 상태 문자열을 상수로 통합했다.
- `타겟 검출률`을 의미가 더 정확한 `단일 타겟 결정률`로 변경했다.
- `src`의 실행 코드마다 입력 검증, 디코딩, 검출, 집계, 출력과 자원 해제 역할을 설명하는 한글 주석을 추가했다.
- 보조 검사 스크립트에 `inspect_target_frame.py`를 먼저 실행해야 한다는 안내를 추가했다.
- 보조 검사 이미지는 고정 파일명을 사용해 재실행 시 계속 쌓이지 않고 덮어쓰도록 명확히 했다.
- 기존 검증 이미지 `37개`와 Threshold 검토용 임시 이미지 `5개`, 총 `42개`를 삭제했다.
- 원본 영상과 Python 코드는 삭제하지 않았으며 최종 `outputs` 이미지 수는 `0개`다.

## Source Structure

### `src/main.py`

- 입력 영상과 Metadata 검증
- Known 60초 Run Segment 순차 디코딩
- 프레임 단위 Detector 호출
- Target Observation 생성
- 상태별 Count와 정합성 계산
- 단일 타겟 결정률과 Segment Completeness 출력

### `src/target_detection.py`

- HSV 범위와 최소 후보 면적 관리
- BGR 입력 검증과 Binary Mask 생성
- External Contour 추출과 면적 Filter
- 단일 후보의 Bounding Box와 Center 반환

### `tests/test_target_detection.py`

- 검출 성공, 실패, Ambiguous와 빈 입력 검증
- Mask shape와 dtype 검증
- 면적 `150` 미만 잡음 Filter 회귀 테스트

### `src/inspect_*.py`

- 시작 프레임 수동 확인
- 대표 프레임 추출
- BGR/HSV 픽셀 확인
- Binary Mask 확인
- Bounding Box와 Center 시각 확인

Inspector는 개발·검증 도구이며 `main.py`의 정상 분석 실행에서는 이미지 파일을 생성하지 않는다.

## Limitations

- HSV와 Area 값은 현재 `woong01.mp4` 한 영상에서 조정했다.
- 다른 해상도에서는 Contour Area 크기가 달라질 수 있으므로 `150`을 그대로 일반화할 수 없다.
- 소멸 애니메이션, 실제 타겟 공백과 검출 실패는 현재 모두 `No-candidate` Raw Observation으로 기록된다.
- 현재 Center는 Bounding Box 중심이며 정확한 Contour 무게중심이나 게임의 Hit Area가 아니다.
- Crosshair 허용 반경과 On-target 판정은 아직 정의하지 않았다.
- `92.19%`는 모델 Accuracy나 Aim 성능 점수가 아니다.
- 현재 구현은 AI Model이 아닌 규칙 기반 Classical Computer Vision이다.

## Next Slice

1. Day 08의 Observation 계약과 `MIN_CANDIDATE_AREA = 150.0`을 현재 기준으로 고정한다.
2. 화면 중심 Crosshair와 Target 영역의 관계를 어떤 규칙으로 판정할지 정의한다.
3. 단순 점 거리, Bounding Box 포함 여부와 허용 반경 중 MVP에 맞는 On-target 계약을 선택한다.
4. Missing Frame을 임의 보간하기 전에 실제 공백과 검출 실패를 구분할 정책을 문서화한다.

## Recommended Commit Message

```text
feat: Run 구간 타겟 관찰 및 후보 면적 필터 조정

- 60초 Run의 프레임별 타겟 Observation과 상태 집계 추가
- 전체 구간 실험을 근거로 최소 후보 면적을 150으로 조정
- 작은 청록색 잡음 Filter 회귀 테스트 추가
- 검증용 임시 저장 로직 제거 및 한글 코드 설명 정리
```

## Study Notes

- 현재 검출기는 학습 모델이 아니라 HSV, Contour와 Area 조건을 사용하는 규칙 기반 Computer Vision이다.
- Threshold는 한 프레임의 성공 여부가 아니라 전체 구간의 변화와 실제 실패 프레임을 함께 확인해 정한다.
- `150`은 관찰된 잡음 최대 면적 `106.5`보다 크면서 안정 구간이 시작되는 가장 작은 실험값이다.
- `center = None`은 좌표값 0이 아니라 해당 프레임에서 단일 타겟 위치를 결정하지 못했다는 상태다.
- `92.19%`는 Aim 정확도가 아니라 단일 유효 후보를 결정한 프레임 비율이다.
