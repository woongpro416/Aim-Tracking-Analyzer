# Data & Metric Specification

## Document Status

- Status: Draft skeleton with confirmed Day 02 domain concepts
- Last updated: 2026-09-10
- Metric 공식, Threshold, 자료형 및 Schema는 아직 확정하지 않았다.

## Data Hierarchy

```text
Aim Type
-> Scenario
-> Run
-> Run Metadata
-> Run Metrics
```

- Run 한 개는 Video File 한 개다.
- Run Metadata와 Run Metrics는 분리한다.
- Session과 Condition은 현재 데이터 계층으로 사용하지 않는다.

## Coordinate System

- Crosshair는 화면 정중앙에 고정되어 있다고 본다.
- Screen Center를 Crosshair Position으로 사용한다.
- 화면 좌표의 원점, 축 방향, 경계 포함 규칙은 Deferred한다.

## Video and Frame Data

- 최초 On-target 이전 구간과 Tracking 분석 구간을 구분한다.
- 최초 On-target 이후의 On-target 및 Off-target Frame을 모두 분석에 사용한다.
- Missing Frame은 Off-target Frame과 다르다.
- Frame Index와 Timestamp Contract는 Deferred한다.

## Scenario and Run

- 각 Run은 독립적으로 분석한다.
- 서로 다른 Run의 Frame-level Trajectory는 연결하지 않는다.
- 같은 Scenario의 Run만 현재 MVP의 직접 비교 대상이다.
- 별도 Scenario Summary와 Trend 판정은 현재 MVP에 포함하지 않는다.

## Run Metadata

Run Metadata의 최소 필수 Field와 각 자료형은 아직 확정하지 않았다.

기존 후보에는 run ID, scenario, date, resolution, fps, sensitivity, dpi, warmup, notes가 있으나 Day 02에서 최종 Contract로 확정하지 않았다.

## Target and Detection Data

- 현재 대상은 하나의 유효 영역을 가진 단일 세로 타원형 Target이다.
- On-target는 Crosshair가 Target 유효 영역 내부에 있는 상태다.
- Off-target는 Target이 관측되었고 Crosshair가 Target 유효 영역 외부에 있는 상태다.
- Target 중심은 Relative Direction 또는 Off-target Severity 계산에 필요할 수 있지만, On-target 내부 품질 등급에는 사용하지 않는다.
- Target 영역, 중심, 경계의 Detection 및 Validation 방법은 Deferred한다.

## Timestamp

- Event와 Metric 근거는 Frame 또는 Timestamp 수준으로 추적 가능해야 한다.
- Decoder Timestamp와 Frame Index / FPS 계산 중 어떤 기준을 사용할지는 Deferred한다.

## Trajectory Data

현재 필요한 논리적 흐름은 다음과 같다.

```text
Video
-> Frame / Timestamp
-> Target Observation
-> On-target / Off-target / Missing State
-> Target Movement Direction
-> Relative Target Direction for applicable Event context
-> Event
-> Metric
-> Summary
```

`Target Movement Direction`과 `Relative Target Direction`은 별도로 기록하고 별도로 집계한다. 두 Direction을 조합한 8 x 8 결과는 만들지 않는다.

정확한 Row Schema, Field 이름, 자료형은 Deferred한다.

## Run Metrics

### Removed in Their Previous Meaning

- Mean Tracking Error
- Median Tracking Error
- RMSE X
- RMSE Y
- Vertical / Horizontal RMSE Ratio

위 Metric은 전체 유효 Frame의 Target 중심 거리를 Tracking 품질로 평가하던 기존 의미로는 MVP에서 사용하지 않는다.

### Confirmed Analysis Responsibilities

- On-target 유지와 Off-target 발생 관측
- Off-target Count와 Total Off-target Duration
- Off-target 이탈 방향
- Off-target 이탈 크기 정량화
- Off-target Re-entry
- Direction Change Event
- Direction-change Recovery
- Movement Direction별 결과
- Relative Direction별 결과
- 방향별 유효 관측량

정식 Metric 이름과 최종 목록은 아직 확정하지 않는다.

## Metric Preconditions

- Event Count가 `0`이 되려면 유효한 분석 대상과 관측 구간이 존재해야 한다.
- 특정 방향의 결과를 관측된 `0`으로 해석하려면 그 방향의 유효 관측량이 0보다 커야 한다.
- Event 기반 Average, Latency, Maximum은 계산 대상 Event가 존재해야 한다.
- 시간 기반 Metric은 신뢰 가능한 Timestamp 전제조건을 충족해야 한다.
- 구체적인 최소 Sample, Coverage 및 FPS 조건은 Deferred한다.

## Missing and Invalid Data

- `Missing`: 특정 Frame 또는 Timestamp의 필요한 원본 관측값 부재
- `invalid`: 입력 또는 값이 Contract를 위반함
- Missing은 Off-target로 변환하지 않는다.
- Video Open 실패와 Frame Decode 실패의 세부 Contract는 Deferred한다.

## Metric Result States

- `0`: 유효한 관측 대상과 구간이 존재했지만 해당 Event가 발생하지 않음
- `unavailable`: Metric 계산에 필요한 데이터 또는 전제조건이 충족되지 않음
- Event가 없어 Event 기반 Average, Latency 또는 Maximum을 계산할 수 없는 경우도 `unavailable`로 처리한다.
- `not applicable`은 별도 상태로 추가하지 않는다.
- `unavailable` 이유를 별도로 제공할지는 아직 결정하지 않았다.

## Metric Comparison Status

- `incompatible`: 두 Run 모두 Metric은 존재하지만 척도 또는 전제조건 차이로 직접 비교할 수 없음
- `warning`: 비교는 가능하지만 정밀도 또는 해석에 주의가 필요함
- `unavailable`: 특정 Run에서 해당 Metric을 신뢰성 있게 계산할 수 없음

기존 Mean Error와 RMSE X/Y의 Resolution mismatch 정책은 해당 Metric 제거로 대체되었다. 새 Off-target Severity의 비교 Preconditions는 Metric 정의 후 결정한다.

## Open Questions

- 8개 Direction의 정확한 각도 Boundary
- 정지 또는 저속 상태의 Direction 표현
- Target Movement Direction과 Relative Target Direction 계산 방식
- Tracking Off-target Event에 Relative Direction을 귀속하는 기준
- Target 영역과 실제 Aim Trainer 판정 영역의 일치 여부
- 짧은 1 Frame Off-target 처리
- Off-target Severity를 Target Center 거리와 Target Boundary 거리 중 무엇으로 정의할지
- Off-target Severity의 방향별 및 Run별 집계 방식
- Direction-change Recovery Operational Definition
- Off-target Re-entry Operational Definition
- 방향전환 후 On-target가 유지된 경우 Recovery 결과
- 각 Direction의 최소 유효 관측량
- 각 Direction에 제공할 최종 Metric 목록
- 길이가 다른 Run의 Count, Total, Rate 비교 정책
- `unavailable` 이유 제공 여부
- 최종 Output Schema와 Comparison Result Contract
