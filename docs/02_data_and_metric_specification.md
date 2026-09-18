# Data & Metric Specification

## Document Status

- Status: Draft / Current Domain and Metric Source of Truth
- Last updated: 2026-09-17 (Day 05)
- Role: Run, Phase, Observation, Event와 Metric의 의미 및 보존 범위를 정의한다.
- Rule: 공식, Threshold, 자료형과 Schema는 명시적으로 확정한 경우에만 사용한다.

## Data Hierarchy

```text
Aim Type
-> Scenario
-> Recording Video
-> Run
-> Phase
-> Event
-> Metric
-> Result
```

- 현재 MVP는 Tracking Aim Type만 지원한다.
- Video File 한 개에는 분석 대상 Run이 정확히 한 개만 존재한다.
- Run은 Scenario 안에서 독립적으로 분석한다.
- 서로 다른 Run의 Frame-level Observation을 하나의 연속 Trajectory로 연결하지 않는다.
- Run Metadata와 분석 결과는 구분한다.

## Runtime Data and Persistent Output

Runtime Processing과 Persistent Internal Output을 구분한다.

### Runtime

```text
Decoded Frame
-> Frame-level Observation
-> Phase / State
-> Event
-> Metric Aggregation
```

- Sampling하지 않고 Decode 가능한 모든 Frame을 순서대로 처리한다.
- Frame마다 필요한 Target Observation, Phase, State와 Direction을 판단한다.
- 분석 실행 중에는 Duration과 Event 계산에 필요한 시간 정보를 사용한다.

### Normal Persistent Internal Output

```text
Run-level Result
Phase-level Result
Event-level Result
Metric-level Result
```

정상 Output에 다음을 필수로 영구 저장하지 않는다.

- Raw Frame 이미지 복제본
- 모든 Frame Timestamp
- 전체 구조화된 Frame-level Observation

Frame-level Observation은 Validation 또는 Debugging 실행에서 선택적으로 생성할 수 있다. 저장된 결과만으로 새로운 Event나 Direction을 재계산해야 한다면 원본 Video를 다시 처리한다.

## Recording Video and Run

- Recording Video는 Run 전후의 여유 구간을 포함할 수 있다.
- `Video Duration != Run Duration`이다.
- 현재 Scenario의 Run Duration은 60초다.
- 화면 중앙의 Countdown 표시가 사라진 첫 번째 decoded Frame이 Run Start 경계다.
- 마지막 Countdown 표시 Frame은 Run에서 제외하고 첫 Countdown 미표시 Frame은 포함한다.
- Run Start는 Domain에서 Recording 시작 기준의 seconds로 표현하며 Frame Index는 내부 처리와 Ground Truth 검증에 사용한다.
- Run Start는 Automatic Countdown Detection 또는 Manual Fallback으로 확정한다.
- Run End는 Domain 기준으로 Run Start 이후 60초다.
- Recording-relative seconds와 decoded Frame의 정확한 Mapping은 Deferred한다.

Run-level Internal Output은 다음 개념을 보존한다.

- 원본 Recording과 Run의 관계
- 독립 Run 식별
- Recording 내부 Run Start와 Run End
- Run Start 결정 방식
- 필요한 Run Segment 처리 완전성

Run ID 형식, Timestamp 자료형과 Status Schema는 Deferred한다.

## Coordinate and Target Assumptions

- Crosshair는 화면 정중앙에 고정되어 있다고 본다.
- Screen Center를 Crosshair Position으로 사용한다.
- 현재 Target은 하나의 유효 영역을 가진 단일 세로 타원형 Target이다.
- On-target 판정에는 Target의 유효 영역이 필요하다.
- Target 중심은 Direction 또는 Off-target Severity에 사용될 수 있지만 On-target 내부 품질 등급에는 사용하지 않는다.
- 화면 원점, 축 방향, 경계 포함 규칙과 Target 영역 Validation은 Deferred한다.

## Run Phases

### Initial Acquisition

```text
Run Start -> First On-target
```

- Run 시작 후 최초 Target 획득 과정이다.
- Target 밖에 있는 상태를 Tracking Maintenance의 Off-target Event와 동일하게 처리하지 않는다.
- Phase의 Frame-level 근거는 Runtime에서 처리하지만 정상 Output에는 집계된 Phase 결과를 보존한다.
- Acquisition Metric의 최종 목록과 공식은 Deferred한다.

### Tracking Maintenance

```text
First On-target -> Run End
```

- 최초 획득 이후 On-target 유지, Off-target, Re-entry와 Tracking Recovery를 분석하는 Phase다.
- First On-target이 관측되지 않으면 이 Phase는 존재하지 않을 수 있다.
- Observation 부족으로 First On-target 판단이 불가능한 경우에는 단순한 Phase 부재와 구분한다.

### First On-target Result

최소한 다음 의미를 구분한다.

- First On-target observed
- 충분한 관측이 있었지만 Run 종료까지 not observed
- Observation 부족 또는 Missing으로 indeterminate

정확한 상태 자료형과 판단 Coverage Threshold는 Deferred한다.

## Phase-level Persistent Result

각 Phase에 대해 다음 개념을 확인할 수 있어야 한다.

- Phase 존재 또는 판단 상태
- Phase 시간 범위 또는 Duration
- First On-target 판단 결과
- Valid Observation 규모
- Missing Observation 또는 Coverage 규모
- Direction별 Valid Observation
- Phase가 없거나 판단 불가능한 경우 Domain Reason

Count, Duration 또는 Ratio 중 어떤 표현을 사용할지는 Deferred한다. Coverage는 관측 가능 범위이지 Detection 정확도를 의미하지 않는다.

## Observation and Tracking State

### Valid Observation

- Metric이나 Event 판단에 사용할 수 있는 Observation이다.
- Valid Observation의 정확한 전제조건과 최소 Sample은 관련 Metric을 구현할 때 결정한다.

### Missing

- 특정 Frame 또는 Timestamp에 필요한 원본 Observation이 없는 상태다.
- Missing은 Off-target로 변환하지 않는다.
- Missing 누적은 Phase 판단 또는 Metric 계산을 `unavailable`로 만드는 원인이 될 수 있다.

### Tracking Maintenance State

- `On-target`: Crosshair가 Target 유효 영역 내부
- `Off-target`: Target이 관측되었고 Crosshair가 Target 유효 영역 외부
- `Missing`: 필요한 Target Observation이 없음

Initial Acquisition에서 Target 밖에 있는 Observation은 위치 관계가 유사하더라도 Tracking Maintenance의 Off-target Event와 같은 의미가 아니다.

## Direction Data

### Target Movement Direction

Target 영상이 시간에 따라 screen-space에서 이동하는 방향이다.

### Relative Target Direction

Target이 Crosshair를 기준으로 위치한 방향이다. Tracking에서는 우선 Off-target 상태의 방향 문맥에 사용한다.

### Direction Rules

- 두 Direction은 별도 축으로 보존하고 별도로 집계한다.
- 두 축을 결합한 8 x 8 결과는 MVP에서 생성하지 않는다.
- 두 축은 각각 8개 Direction Category를 사용하는 방향으로 둔다.
- 정확한 Angle Boundary, Noise, 정지·저속 처리와 Event별 Direction 귀속은 Deferred한다.
- Initial Acquisition과 Tracking Maintenance의 Direction Valid Observation을 구분할 수 있어야 한다.
- Target Observation은 유효하지만 Direction은 판정 불가능한 경우의 표현은 Deferred한다.

## Event Data

### Persistence Decision

- Operational Definition이 확정되어 Runtime에서 생성되는 Event는 개별 Event 결과를 정상 Internal Output에 영구 보존한다.
- 모든 미래 Event 종류를 현재 확정하지 않는다.
- Frame-level Observation이 아니라 의미 있는 상태 변화로 압축된 Event 결과를 보존한다.

### Event Context Requirement

개별 Event는 최소한 다음 의미를 구분할 수 있어야 한다.

- 어떤 Run에 속하는가
- 어떤 Phase에서 발생했는가
- Event 종류는 무엇인가
- Event Duration은 얼마인가
- Run 내부에서 어떤 순서로 발생했는가
- Run 내부의 시간적 위치 또는 시간 범위는 무엇인가
- Event에 필요한 Direction 문맥이 있는가

Event ID 형식, Sequence 표현, Start/End Timestamp 자료형, JSON Schema와 DB 구조는 Deferred한다.

### Current Event Concepts

- Off-target Event
- Off-target Re-entry
- Direction Change Event
- Direction-change Recovery 관련 Event

위 개념 중 정확한 시작/종료 조건과 공식이 확정되지 않은 항목은 구현 Contract가 아니라 Deferred 개념이다.

## Metric Responsibilities

### Removed in Their Previous Meaning

- Mean Tracking Error
- Median Tracking Error
- RMSE X
- RMSE Y
- Vertical / Horizontal RMSE Ratio

위 Metric은 전체 유효 Frame의 Target 중심 거리를 Tracking 품질로 평가하던 기존 의미로는 MVP에서 사용하지 않는다.

### Confirmed Analysis Responsibilities

- On-target 유지 결과
- Off-target Event Count
- Total Off-target Duration
- Off-target Direction
- Off-target Severity 정량화 책임
- Off-target Re-entry
- Direction Change Event
- Direction-change Recovery
- Movement Direction별 결과
- Relative Direction별 결과
- Run/Phase/Direction별 Valid Observation
- Phase별 Missing 또는 Coverage

정식 Metric 이름, 공식과 최종 목록은 아직 확정하지 않는다.

## Metric Preconditions and Result States

### Zero

- 유효한 분석 대상과 관측 구간이 존재했지만 Event가 발생하지 않은 결과다.
- Event Count와 Total Event Duration은 `0`이 될 수 있다.
- 특정 방향의 관측된 `0`은 해당 방향의 Valid Observation이 존재해야 한다.

### Unavailable

- Metric 계산에 필요한 데이터 또는 전제조건이 충족되지 않은 결과다.
- Event 표본이 필요한 Average, Median, Maximum 또는 Latency는 Event가 없으면 `unavailable`일 수 있다.
- Tracking Maintenance Phase가 없으면 관련 Metric은 `unavailable`이다.
- 모든 unavailable Metric은 사용자 확인 가능한 Domain Reason을 가져야 한다.
- 같은 원인이 여러 Metric에 영향을 주더라도 각 Metric에서 이유를 확인할 수 있어야 한다.

### Invalid

- 입력 또는 값이 Contract를 위반한 상태다.
- 비지원 FPS와 여러 Run이 포함된 Video는 현재 확정된 invalid input 사례다.

### Not Applicable

- 별도 상태로 추가하지 않는다.

## Run Comparison Data

- Run은 먼저 독립적으로 분석한다.
- 같은 Scenario의 Run Result를 나란히 비교할 수 있다.
- Run 간 Frame-level Observation을 연결하지 않는다.
- Raw Count와 Raw Duration을 보존하고 관련 Valid Observation을 함께 제공한다.
- 방향별 시간 보정 Rate는 현재 MVP 필수 Metric이 아니다.
- Single Run 결과에서 방향 간 우열이나 개인 성향을 자동 판정하지 않는다.
- Personal Pattern, Normalization과 Trend는 Future Contract다.

## Traceability and Recalculation Limits

현재 필수 Traceability는 다음 범위다.

```text
Original Video
-> Run
-> Run Boundary
-> Phase
-> Event / Metric
-> Result
```

- 개별 Event는 Run 내부 시간적 문맥을 보존하지만 원본 Frame으로 이동하는 기능은 필수가 아니다.
- Frame-level Observation 없이 Event 정의나 Direction Boundary를 변경하여 재계산하는 기능은 보장하지 않는다.
- 필요한 경우 원본 Video를 새로운 분석 로직으로 다시 처리한다.
- Validation/Debugging 실행에서는 선택적인 Frame-level Artifact를 생성할 수 있다.

## Deferred Decisions

- Recording-relative seconds와 decoded Frame의 exact Mapping 및 60초 Frame Boundary 계산
- 59.94 FPS와 Variable Frame Rate 처리
- Video Open/Decode 실패와 정상 EOF Contract
- First On-target Coverage Threshold
- Valid Observation 및 Missing/Coverage 표현
- 정확한 8방향 Angle Boundary
- Direction Noise와 정지·저속 처리
- 1 Frame Off-target 처리
- Off-target Severity 공식과 이름
- Direction-change Recovery와 Re-entry Operational Definition
- Event별 Direction 귀속
- 방향별 최소 Sample
- 최종 Metric 목록
- Acquisition Metric
- Personal Pattern Analysis와 Trend
- 전체 Output Schema, DB와 Version Migration
