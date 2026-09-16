# Architecture Decision Records

## Document Status

- Status: Draft / Active Decision Log
- Last updated: 2026-09-16 (Day 03)
- Role: 여러 Requirement, Data, Test 또는 구현 Slice에 함께 영향을 주는 주요 결정을 기록한다.

## Decision Selection Criteria

다음 조건 중 하나 이상을 만족하는 결정을 기록한다.

- 여러 Requirement, Metric, Test 또는 Output에 동시에 영향을 줌
- 이전 결정을 명시적으로 대체하거나 범위를 정교화함
- 대안과 Trade-off를 설명할 필요가 있음
- MVP 경계 또는 데이터 보존 범위를 변경함

## Decision Index

| Decision | Status | Date |
| --- | --- | --- |
| AI Analysis Placement | Accepted | Day 01 |
| Binary Tracking State and Off-target-focused Analysis | Accepted | Day 02 |
| Separate Directional Analysis Axes without 8 x 8 Cross-analysis | Accepted | Day 02 |
| Recording Video and Run Segment Separation | Accepted | Day 03 |
| Run-level Data Boundary and Phase Separation | Accepted | Day 03 |
| Runtime Frame Processing and Persistent Output Separation | Accepted | Day 03 |
| Reduced Persistent Traceability Scope | Accepted | Day 03 |
| Single Run Observation and Future Personal Pattern Separation | Accepted | Day 03 |
| Per-Metric User-facing Unavailable Reason | Accepted | Day 03 |

## Decision Records

### AI Analysis Placement

#### Context

현재 통제된 Aim Trainer 환경에서 MVP의 핵심은 복잡한 AI Model보다 신뢰할 수 있는 Video 분석, Event와 Metric Validation이다.

#### Alternative

Detection 또는 초기 분석 단계부터 Machine Learning Model을 사용한다.

#### Decision

AI Analysis는 Validated Run Metrics 이후의 Future Extension 계층으로 둔다.

#### Reason

측정값의 신뢰성과 분석 Contract를 먼저 확보한 뒤 Pattern Analysis에 사용하기 위해서다.

#### Consequence

현재 MVP에서 Deep Learning Model은 필수가 아니다. Future AI 결과도 원인을 진단하지 않고 검증된 Pattern을 설명하는 범위로 제한한다.

#### Deferred

Model, Feature, Dataset, 최소 Run 수와 평가 기준.

### Binary Tracking State and Off-target-focused Analysis

#### Context

초기 Working Reference는 전체 유효 Frame에서 Crosshair와 Target 중심 거리를 Tracking Error로 사용하고 Mean / Median Error와 RMSE X/Y를 MVP 핵심 Metric으로 두었다.

#### Previous / Alternative

전체 Frame의 Target Center Distance를 Tracking 품질로 사용한다.

#### Decision

- Tracking Maintenance 성공 상태는 On-target / Off-target를 중심으로 분석한다.
- On-target 내부의 중심 거리는 Tracking 품질 등급에 사용하지 않는다.
- 기존 Mean / Median Tracking Error, RMSE X/Y와 Vertical / Horizontal RMSE Ratio는 기존 의미로 MVP 필수 Metric에서 제거한다.
- Off-target 상태에서는 방향, 크기, 지속과 Re-entry를 분석한다.

#### Reason

Target 내부의 모든 위치를 성공 상태로 보는 Domain Definition과 Metric 의미를 일치시키기 위해서다.

#### Consequence

- Target 영역과 내부/외부 판정 Validation이 중요해진다.
- Off-target Severity와 Event 정의가 필요하다.
- 초기 Working Reference의 Metric, Graph, Test와 완료 기준 일부가 superseded된다.

#### Deferred

Off-target Severity 공식, 짧은 이탈 처리와 최종 Metric 목록.

### Separate Directional Analysis Axes without 8 x 8 Cross-analysis

#### Context

Target이 화면에서 이동하는 방향과 Target이 Crosshair 기준으로 벗어난 방향은 서로 다른 질문에 답한다.

#### Alternative

한 종류의 Direction만 사용하거나 두 Direction의 모든 조합을 집계한다.

#### Decision

- Target Movement Direction과 Relative Target Direction을 별도 분석 축으로 사용한다.
- 각 축은 8개 Direction Category를 사용하는 방향으로 둔다.
- 두 축의 결과는 별도로 생성하며 8 x 8 조합 분석은 MVP에 포함하지 않는다.
- Tracking의 Relative Target Direction은 우선 Off-target 문맥에 사용한다.

#### Reason

Movement와 Crosshair-relative 위치의 의미를 혼동하지 않으면서 Sample 희소성과 MVP Scope를 제한하기 위해서다.

#### Consequence

Phase와 Direction별 Valid Observation을 함께 보존해야 한다.

#### Deferred

Angle Boundary, Direction Noise, 정지·저속 처리와 Event별 Direction 귀속.

### Recording Video and Run Segment Separation

#### Context

실제 Recording에는 Countdown 전 준비 시간과 Run 종료 후 여유 시간이 포함될 수 있다. Video Duration과 실제 Aim Trainer Run Duration은 같지 않다.

#### Previous / Alternative

- Video File 전체를 하나의 Run 시간 범위로 사용한다.
- 사용자가 정확한 Run 구간으로 영상을 후편집한다.

#### Decision

- 현재 MVP에서 Video File 한 개는 분석 대상 Run 한 개와 연결된다.
- Video 전체와 실제 Run Segment의 시간 범위를 구분한다.
- 중앙 Countdown의 `0` 시점을 Run Start Marker로 사용한다.
- 기본은 Automatic Countdown Detection이며 실패 또는 불확실 시 Manual Run Start Fallback을 사용한다.
- 자동 탐지 성공 시 사용자 확인 없이 분석을 진행한다.
- 하나의 Video에 둘 이상의 독립 Run이 존재하면 invalid input으로 처리한다.
- 현재 Scenario의 Run은 Run Start 이후 60초다.

#### Reason

사용자에게 후편집을 요구하지 않으면서 일관된 단일 Run Contract를 유지하기 위해서다.

#### Consequence

- Run Boundary Resolution이 분석 Pipeline의 선행 책임이 된다.
- Run Start 결정 방식과 Segment 처리 완전성을 Internal Output에 보존한다.
- Day 04 첫 Slice에서는 Human-verified Known Run Start로 Segment 처리를 먼저 검증한다.

#### Deferred

Countdown Detection Algorithm, Confidence, Manual Input 표현, exact Timestamp와 60초 Frame 경계.

### Run-level Data Boundary and Phase Separation

#### Context

기존에는 First On-target 이전 구간을 Tracking Metric 분석 범위 밖으로 두었다. 실제 Run을 검토한 결과 최초 Target 획득 과정도 Run 수행의 일부이며 데이터를 버리면 향후 Acquisition 분석 근거를 잃는다.

#### Previous / Alternative

- First On-target 이전 Frame을 Run-level 분석에서 제외한다.
- Initial Acquisition을 Tracking Maintenance Off-target Event와 동일하게 집계한다.

#### Decision

- Run-level Data Boundary는 Run Start부터 Run End까지의 60초 전체다.
- Run Start부터 First On-target까지를 Initial Acquisition으로 구분한다.
- First On-target부터 Run End까지를 Tracking Maintenance로 구분한다.
- Initial Acquisition의 Target 밖 상태를 Tracking Maintenance Off-target Event와 동일하게 취급하지 않는다.
- First On-target는 observed, 충분한 관측에서 not observed, Observation 부족으로 indeterminate인 의미를 구분한다.
- First On-target가 없어도 Run-level 분석은 성공할 수 있으며 Tracking Maintenance Metric은 unavailable Reason을 가진다.

#### Reason

Run 전체 수행 데이터를 보존하면서 최초 획득과 유지 Tracking의 서로 다른 의미를 혼합하지 않기 위해서다.

#### Consequence

- 기존의 `Tracking 분석은 First On-target부터 시작`은 Tracking Maintenance Metric Boundary로 범위가 정교화된다.
- Phase별 Duration, Valid Observation, Missing/Coverage와 Direction Observation이 필요하다.

#### Deferred

Initial Acquisition Metric, First On-target Coverage Threshold와 Run Start 즉시 On-target인 경우의 Phase 표현.

### Runtime Frame Processing and Persistent Output Separation

#### Context

1분 nominal 60 FPS Run의 모든 Frame 이미지와 Observation을 영구 저장하면 현재 사용자 목적보다 저장 및 Contract 범위가 커진다. 반면 Frame-level 계산과 개별 Event 분포는 필요하다.

#### Alternative

- 모든 Raw Frame과 Frame-level Observation을 영구 저장한다.
- Event Aggregate만 저장하고 개별 Event는 폐기한다.

#### Decision

- Runtime에서는 Sampling 없이 Decode 가능한 모든 Frame을 순서대로 분석한다.
- Raw Frame 이미지, 모든 Frame Timestamp와 전체 Frame-level Observation은 정상 Internal Output에 필수로 저장하지 않는다.
- Frame-level Observation은 Validation/Debugging 실행에서 선택적으로 생성할 수 있다.
- Operational Definition이 확정된 Event는 개별 결과로 영구 보존한다.
- Event는 Duration뿐 아니라 Run 내부 발생 순서와 시간적 위치 및 필요한 Direction 문맥을 구분할 수 있어야 한다.
- Metric과 Summary는 영구 보존 대상이다.

#### Reason

저장 규모와 Contract를 제한하면서 Event 분포 및 Future Pattern Analysis에 필요한 압축된 근거를 유지하기 위해서다.

#### Consequence

- 저장된 Output만으로 새로운 Event 정의나 Direction Boundary를 과거 Frame에 적용할 수 없다.
- 필요 시 원본 Video를 다시 분석한다.
- Event-level 최소 Context는 Event 구현 Slice에서 구체화한다.

#### Deferred

Event ID, Sequence와 Timestamp 표현, 전체 Output Schema 및 Version Migration.

### Reduced Persistent Traceability Scope

#### Context

기존 Requirement는 Metric에서 원본 Frame/Timestamp까지 영구적으로 역추적하는 넓은 Traceability를 요구했다. 현재 미니프로젝트의 사용자 목적에는 Run, Phase, Event와 Metric 수준의 근거가 우선이다.

#### Previous / Alternative

```text
Metric -> Event -> Frame/Timestamp -> Video
```

#### Decision

현재 MVP의 필수 Persistent Traceability를 다음 범위로 축소한다.

```text
Original Video
-> Run
-> Run Boundary
-> Phase
-> Event / Metric
-> Summary
```

Metric에서 원본 Frame으로 이동하는 기능은 MVP 필수에서 제외한다.

#### Reason

현재 프로젝트 규모에서 사용자 가치가 낮은 Frame-level 영구 추적 기능보다 Run 분석과 Event/Metric 검증에 집중하기 위해서다.

#### Consequence

- Frame-level 사후 감사와 Output 단독 재계산은 보장하지 않는다.
- Validation은 Known-value Test, Synthetic Data, 선택적 Debug Artifact와 필요 시 원본 Video 재분석으로 수행한다.

#### Deferred

향후 Frame Viewer, 상세 Audit Trail과 재현성 Version Contract.

### Single Run Observation and Future Personal Pattern Separation

#### Context

각 Aim Trainer Run에는 Direction 순서, 노출 시간과 Direction Change 시점의 랜덤성이 있다. 한 Run을 동일 자극 A/B Test나 개인 능력 진단으로 해석하면 과장될 수 있다.

#### Alternative

- 한 Run의 방향별 Raw Count로 개인 취약성을 자동 판정한다.
- 적은 수의 Run 차이로 Trend 또는 지속적인 개선을 판정한다.

#### Decision

- Single Run은 해당 Run에서 관측된 Raw Metric과 Valid Observation을 제공한다.
- Selected Run Comparison은 같은 Scenario의 독립 Run 결과를 나란히 보여준다.
- Single Run이나 소수 Run으로 방향별 우열, 개인 성향 또는 지속적 개선을 자동 판단하지 않는다.
- 여러 Run의 반복 Pattern과 시간 변화는 Future Personal Pattern Analysis에서 다룬다.
- Direction별 시간 보정 Rate는 현재 MVP 필수 Metric이 아니다.

#### Reason

관측 사실과 장기적인 개인 경향 추론을 분리하기 위해서다.

#### Consequence

Run/Phase/Direction별 Valid Observation과 개별 Event 결과를 보존한다. Future Pattern Analysis는 저장된 Run 결과를 사용한다.

#### Deferred

Normalization, 최소 Run 수, Trend 기준, 통계 방식과 AI Pattern Analysis.

### Per-Metric User-facing Unavailable Reason

#### Context

`unavailable`만 표시하면 Phase 부재, Event 부재, Missing, Timestamp 문제 또는 관측량 부족을 사용자가 구분하기 어렵다.

#### Alternative

- Reason을 내부 Debug 정보로만 보존한다.
- 공통 원인을 한 번만 제공하고 개별 Metric에는 이유를 생략한다.

#### Decision

- 모든 unavailable Metric은 사용자가 확인 가능한 Reason을 가진다.
- 동일 원인이 여러 Metric에 영향을 주더라도 각 Metric에서 이유를 확인할 수 있어야 한다.
- Reason은 Domain 의미로 설명하며 내부 예외명이나 Debug Code만으로 표시하지 않는다.

#### Reason

각 Metric을 독립적으로 읽을 때 계산 불가 이유를 이해할 수 있게 하기 위해서다.

#### Consequence

- Event 없음으로 Count가 0인 경우와 Event 표본 부족으로 파생 Metric이 unavailable인 경우를 구분한다.
- Missing은 unavailable과 다른 상태지만 Metric unavailable의 원인이 될 수 있다.
- 반복되는 Reason은 허용한다.

#### Deferred

Reason Code, Enum, 사용자 문구와 내부 Debug 정보의 구조적 분리 및 Output Schema.
