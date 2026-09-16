# Day 03 — Requirements and Implementation Readiness

## Today's Goal

코드를 작성하지 않고 Day 02에서 Deferred한 비교 정책, unavailable Reason, 최소 Output, Input/Run Contract를 검토했다. 논의를 진행하면서 Recording과 실제 Run Segment, Run-level Data와 Tracking Maintenance Metric의 경계를 새로 구분했다.

Primary Author와 Primary Coder는 프로젝트 작성자이며, AI는 Requirement Reviewer, Contract Reviewer, Design Reviewer, Implementation Readiness Reviewer와 Technical Mentor 역할로 제한했다.

## Starting Point

Day 03은 길이가 다른 Run과 방향별 관측 시간이 다른 결과를 어떻게 비교할지 결정하는 문제에서 시작했다.

초기 질문:

- Raw Count와 Total Duration을 그대로 비교할 것인가?
- 관측 시간 대비 Rate를 사용할 것인가?
- 방향별 관측량 차이를 어떻게 보여줄 것인가?
- 최소 관측량이나 Warning이 필요한가?

## Run Duration and Recording Reassessment

실제 Aim Trainer 조건을 다시 확인하면서 다음을 구분했다.

```text
Video Duration != Run Duration
```

- Aim Trainer의 실제 Run은 현재 Scenario에서 60초다.
- Recording은 Countdown 전 준비 시간과 Run 종료 후 여유 시간을 포함할 수 있다.
- nominal 60 FPS는 권장 환경이 아니라 현재 MVP의 통제된 Input Contract로 강화했다.
- 비지원 FPS 입력은 현재 MVP에서 invalid다.
- `60 FPS x 60 seconds = exactly 3600 decoded frames`는 아직 Contract로 고정하지 않았다.

## Run Start Marker Discovery

실제 Recording에서 모든 정상 Run 시작 전에 중앙 Countdown이 나타나는 것을 확인했다.

```text
3 -> 2 -> 1 -> 0
```

`Countdown = 0`을 Run Start Marker로 선택했다.

최종 Workflow:

```text
Automatic Countdown Detection
-> success: Run Start 자동 확정
-> failure or uncertain: User Manual Run Start Selection
-> Run Start 확정
-> 60-second Run Segment Analysis
```

자동 탐지 성공 시 매번 사용자 확인을 요구하지 않는다. 하나의 Video에서 둘 이상의 독립 Run이 발견되면 현재 `1 Video = 1 Run` Contract 위반으로 invalid 처리한다.

## Run Start and First On-target Separation

Run Start와 Tracking Maintenance 시작은 같은 시점이 아님을 확인했다.

```text
Recording Start
-> Countdown
-> Countdown = 0 / Run Start
-> Initial Acquisition
-> First On-target
-> Tracking Maintenance
-> Run End
-> Recording End
```

기존 Day 02의 `First On-target 이전은 Tracking Metric 분석 대상이 아니다`는 결정은 다음처럼 정교화했다.

- Run-level Data Boundary: Run Start부터 Run End까지
- Initial Acquisition: Run Start부터 First On-target까지
- Tracking Maintenance Metric Boundary: First On-target부터 Run End까지

First On-target 이전 Frame도 Run 수행 데이터이므로 버리지 않는다. 다만 Initial Acquisition의 Target 밖 상태를 Tracking Maintenance Off-target Event와 동일하게 취급하지 않는다.

## First On-target Result

최소한 다음 의미를 구분하기로 했다.

1. First On-target이 관측됨
2. 충분히 관측했지만 Run 종료까지 First On-target이 관측되지 않음
3. Observation 부족 또는 Missing으로 발생 여부를 판단할 수 없음

First On-target이 없어도 Run Start와 60초 Segment를 정상 처리했다면 Run-level 분석은 성공할 수 있다.

```text
Initial Acquisition = 60 seconds
Tracking Maintenance = absent
Tracking Maintenance Metrics = unavailable with reasons
```

## Run Comparison Decision

현재 비교 책임을 세 계층으로 구분했다.

### Single Run

- 해당 Run에서 실제로 관측된 Raw Metric과 Valid Observation을 제공한다.
- 하나의 Run으로 방향별 우열, 사용자 취약성 또는 장기 성향을 자동 판단하지 않는다.

### Selected Run Comparison

- 같은 Scenario의 독립 Run 결과를 나란히 확인한다.
- Strict A/B Test로 해석하지 않는다.
- Raw Count와 Raw Duration을 유지하고 관련 Valid Observation을 함께 보여준다.
- 시간당 Rate는 현재 MVP 필수 Metric으로 추가하지 않는다.

### Future Personal Pattern Analysis

- 여러 Run에서 반복되는 방향별 Pattern과 Event 형태를 분석한다.
- 시간에 따른 변화는 별도 Trend Contract가 필요하다.
- Normalization, 최소 Run 수와 통계 기준은 Future다.
- Pattern을 설명하더라도 신체, 감도, 자세 또는 습관의 원인을 진단하지 않는다.

## Unavailable Reason Policy

다음 원칙을 확정했다.

- 모든 unavailable Metric은 사용자가 확인 가능한 Reason을 가진다.
- 같은 원인이 여러 Metric에 영향을 주더라도 각 Metric에서 이유를 확인할 수 있어야 한다.
- Reason은 Domain 의미로 설명하며 내부 Exception이나 Debug Code만으로 표시하지 않는다.
- Reason Code, Enum, Schema와 내부 Debug 구조는 Deferred한다.

State 의미도 정교화했다.

- Event가 없으면 Count와 Total Duration은 `0`일 수 있다.
- Event 표본이 필요한 Average, Median, Maximum과 Latency는 `unavailable`일 수 있다.
- Missing은 unavailable과 같은 상태가 아니지만 Metric unavailable의 원인이 될 수 있다.
- Invalid Input은 Metric unavailable과 다르다.

## Internal Output and User Summary Separation

최소 Output을 하나로 묶지 않고 두 계층으로 나누었다.

```text
Internal Analysis Output
!=
User-facing Summary
```

- Internal Output은 Traceability, Metric 근거, Run Comparison, Validation과 Future Pattern Analysis를 위한 결과다.
- User Summary는 한 Run에서 무엇이 관측되었는지 사용자가 직관적으로 이해하도록 Internal Output에서 파생한다.
- User Summary의 최종 최소 항목은 아직 Deferred다.

## Persistence Scope Decision

Runtime 분석과 영구 저장 범위를 구분했다.

```text
Runtime:
Frame -> Observation -> Event -> Metric

Persistent Internal Output:
Run + Phase + Event + Metric
```

정상 Output에 필수로 저장하지 않는 항목:

- Raw Frame 이미지 복제본
- 모든 Frame Timestamp
- 전체 구조화된 Frame-level Observation
- Metric에서 원본 Frame으로 이동하는 기능

Frame-level Observation은 Validation/Debugging 실행에서 선택적으로 생성할 수 있다. 이 결정으로 저장된 Output만을 이용한 새 Event 또는 Direction 재계산은 포기하고 필요 시 원본 Video를 다시 분석하는 Trade-off를 수용했다.

## Reduced Traceability

기존의 넓은 Traceability를 MVP 규모에 맞게 축소했다.

Previous:

```text
Metric -> Event -> Frame/Timestamp -> Video
```

Current MVP:

```text
Original Video
-> Run
-> Run Boundary
-> Phase
-> Event / Metric
-> Summary
```

이 결정은 구현 세부가 아니라 Requirement Scope 변경으로 ADR에 기록한다.

## Required Internal Output

### Run-level

- 원본 Recording과 Run 관계
- 독립 Run 식별
- Recording 안의 Run Start와 Run End
- Automatic/Manual Run Start 결정 방식
- 60초 Segment 처리 완전성

### Phase-level

- Phase 존재 또는 판단 상태
- Phase 시간 범위 또는 Duration
- First On-target 판단 결과
- Phase별 Valid Observation
- Phase별 Missing 또는 Coverage
- Phase별 Direction Valid Observation
- Phase가 없거나 판단 불가능한 경우 Reason

### Event-level

- 확정된 Event는 개별 결과를 영구 보존한다.
- Run, Phase, Event 종류와 Duration을 구분한다.
- Run 내부 발생 순서와 시간적 위치 또는 범위를 보존한다.
- Event에 필요한 Direction 문맥을 보존한다.
- Event ID, Timestamp 자료형과 Schema는 Deferred한다.

### Metric-level

- 확정된 Metric Value와 Result State
- 관련 Run/Phase/Direction 문맥
- Valid Observation과 Missing/Coverage 근거
- unavailable인 경우 사용자 확인 가능한 Reason

## Implementation Readiness Review

현재 Domain 설계는 첫 구현에 충분하다고 판단했다. 더 많은 Metric, Event Schema, DB 또는 Pattern Contract를 설계하는 것은 Over-design 위험이 있다.

구현 전 필요한 작업:

- Day 03 결정을 Source of Truth와 ADR에 동기화
- 실제 대표 Recording을 로컬에 준비

대표 Recording은 Repository에 Commit하지 않는다. Day 04 시작 시 사용자가 직접 경로를 제공한다.

## Day 04 Initial Slice Decision

첫 Slice에서 Automatic Countdown Detection을 바로 구현하지 않는다.

```text
Video Open
-> Metadata Inspection
-> FPS Validation
-> Sequential Frame Decode
-> Human-verified Known Run Start
-> 60-second Run Segment Processing
-> Segment Completeness Check
```

Known Run Start는 개발 단계의 Known Boundary이며 최종 사용자 Workflow 변경이 아니다. 이 Slice가 정상 동작한 뒤 Countdown 관측 특징, Automatic Detection과 Manual Fallback으로 확장한다.

Target Detection, On-target / Off-target, Direction, Event와 Metric은 첫 Slice에 포함하지 않는다.

## Phase 0 Completion Decision

- Day 01~03의 Domain 및 Contract 설계로 첫 구현에 필요한 Boundary가 확보되었다.
- 확정되지 않은 Algorithm, Threshold와 Output Schema는 구현 Slice 또는 Future Contract까지 Deferred한다.
- Source of Truth 동기화 후 Phase 0 / Requirements를 종료하고 Day 04 구현 단계로 이동한다.

## Day 04 Handoff

Day 03에서는 추가 Requirement 발굴을 종료한다. 다음 작업은 Day 04 구현 단계로 넘긴다.

Day 04 시작 시 사용자가 준비할 항목:

- Repository에 Commit하지 않은 실제 대표 Recording의 로컬 경로
- nominal 60 FPS, 중앙 Countdown, 단일 Run과 전체 60초 구간을 포함하는지 확인
- 첫 Slice의 Input, Expected Output, Success와 Invalid Behavior 초안

Day 04 첫 구현 Slice:

```text
Video Open
-> Metadata Inspection
-> FPS Validation
-> Sequential Frame Decode
-> Human-verified Known Run Start
-> 60-second Run Segment Processing
-> Segment Completeness Check
```

Day 04에서 실제 Video와 Library 동작을 확인하며 결정할 항목:

- Video Open 실패의 구체적인 동작
- Frame Decode 실패와 정상 EOF 구분
- 59.94 FPS 허용 여부와 nominal FPS 판정 기준
- 첫 Slice에서 사용할 시간 기준과 60초 Segment 경계
- Run Start 이후 필요한 Segment가 부족한 경우의 처리

Automatic Countdown Detection과 Manual Fallback 연결은 Known Run Start 기반 Segment 처리가 검증된 다음 Slice로 넘긴다. Target Detection, Phase/State, Direction, Event와 Metric 구현은 그 이후 작은 Slice로 진행한다.

## Explicitly Deferred

- exact Timestamp와 60초 Frame Boundary
- 59.94 FPS 및 Variable Frame Rate
- Video Open/Decode 실패 세부 Contract
- First On-target Coverage Threshold
- Direction Angle Boundary, Noise와 정지·저속 처리
- 1 Frame Off-target
- Off-target Severity 공식
- Recovery Operational Definition
- 방향별 최소 Sample
- Event별 Direction 귀속
- Acquisition Metric
- User-facing Summary 최종 항목
- Personal Pattern Analysis, Trend와 AI Pattern Analysis
- DB, 전체 JSON Schema, Version Migration과 Requirement ID

## Repository Documentation Changes

- Requirements & Contract에 Day 03 Input, Run Boundary, Phase, State, Output 및 Traceability 결정 반영
- Data & Metric Specification에 Run -> Phase -> Event -> Metric 계층과 Runtime/Persistence 범위 반영
- Lightweight System Design에 Pipeline, 책임 및 Day 04 Slice 순서 반영
- ADR에 Day 01~03 주요 Scope 변경 기록
- Test & Validation Plan과 Validation Report Skeleton 정리
- 두 Working Reference 상단에 최신 Source of Truth 안내 추가
- Python 코드, Test 코드, Git Commit과 Push 없음

## Study Notes

- Video Duration과 Run Duration은 같은 개념이 아니다.
- Run-level Data Boundary와 Tracking Maintenance Metric Boundary는 다를 수 있다.
- 모든 Frame을 분석하는 것과 모든 Frame 결과를 영구 저장하는 것은 다르다.
- `0`은 관측된 없음이고 `unavailable`은 계산 전제조건 부족이다.
- Single Run의 관측 결과와 여러 Run의 Personal Pattern은 다른 분석 책임이다.
