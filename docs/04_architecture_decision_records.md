# Architecture Decision Records

## Document Status

- Status: Draft / Active Decision Log
- Last updated: 2026-09-10

## Decision Selection Criteria

다음 조건 중 하나 이상을 만족하는 결정을 기록한다.

- 여러 Requirement, Metric, Test 또는 Output에 동시에 영향을 줌
- 이전 결정을 명시적으로 대체함
- 대안과 Trade-off를 설명할 필요가 있음
- 프로젝트의 MVP 경계를 변경함

## Decision Index

| Decision | Status | Date |
| --- | --- | --- |
| AI Analysis Placement | Accepted | Day 01 |
| Binary Tracking State and Off-target-focused Analysis | Accepted | Day 02 |
| Separate Directional Analysis Axes without 8 x 8 Cross-analysis | Accepted | Day 02 |

## Decision Records

### AI Analysis Placement

#### Decision

AI Analysis는 Detection 앞단이 아니라 Validated Run Metrics 이후의 Future Extension 계층으로 둔다.

#### Reason

현재 통제된 Aim Trainer 환경에서는 HSV 기반 Detection으로 MVP 목적을 달성할 수 있다. 프로젝트의 핵심은 Detection Model의 복잡도가 아니라 Trajectory와 Metric의 신뢰성 검증이다.

검증된 Metric이 확보된 뒤 Machine Learning을 이용해 같은 Scenario의 Run Pattern을 탐색하는 방식이 현재 프로젝트의 데이터 흐름과 더 자연스럽게 연결된다.

#### Trade-off

초기 버전에서는 Deep Learning Model을 사용하지 않지만, 측정값의 신뢰성과 AI 입력 Feature의 근거를 먼저 확보할 수 있다.

구체적인 Model, Feature, Dataset, 평가 기준은 MVP 검증 이후 별도 Requirement / Contract 단계에서 결정한다.

### Binary Tracking State and Off-target-focused Analysis

#### Status

Accepted on Day 02.

#### Context

기존 Working Reference는 전체 유효 Frame에서 Crosshair와 Target 중심의 거리를 Tracking Error로 사용하고 Mean / Median Error, RMSE X/Y, Vertical / Horizontal RMSE Ratio를 MVP 핵심 Metric으로 두었다.

현재 Target은 일정한 유효 영역을 가진 도형이며, 사용자는 Crosshair가 Target 내부에 있는 동안 중심과의 거리에 따라 Tracking 품질을 다시 등급화하지 않기로 결정했다.

#### Decision

- Tracking 성공 상태는 On-target / Off-target Binary State를 중심으로 분석한다.
- On-target 내부의 중심 거리는 Tracking 품질 평가에 사용하지 않는다.
- 기존 Mean / Median Tracking Error, RMSE X/Y, Vertical / Horizontal RMSE Ratio는 기존 의미로 MVP 필수 Metric에서 제거한다.
- 기존 `Tracking Error`라는 용어는 Requirements 단계에서 사용하지 않는다.
- Off-target 상태에서는 이탈의 방향, 크기, 지속 및 Re-entry를 분석한다.
- Off-target 이탈 크기의 공식과 정식 Metric 이름은 Data & Metric Specification에서 결정한다.

#### Reason

Target 내부의 모든 위치를 성공 상태로 보는 Domain Definition과 Metric의 의미를 일치시키기 위해서다. 중심에 더 가깝다는 이유만으로 Target 내부 상태를 더 높은 품질로 평가하지 않는다.

#### Alternatives

- 전체 Frame 중심 거리 기반 Mean / Median / RMSE 유지
- Binary State만 사용하고 Off-target Severity는 분석하지 않음
- Binary State를 성공 기준으로 사용하고 Off-target 상태만 별도로 정량화

#### Consequences and Trade-offs

- On-target 내부의 미세한 중심 Drift는 Tracking 품질 Metric으로 사용하지 않는다.
- Target 영역과 내부/외부 판정의 신뢰성이 더 중요해진다.
- 기존 Error Timeline, X/Y 비교, JSON 예시, 비교 정책, 테스트와 완료 기준을 수정해야 한다.
- Off-target Severity의 거리 기준과 Resolution mismatch 정책을 새로 정의해야 한다.

#### Superseded Decisions

- 전체 Frame Target 중심 거리 기반 Tracking Error
- Mean / Median Tracking Error의 MVP 필수 Metric 지정
- RMSE X/Y 및 Vertical / Horizontal RMSE Ratio의 MVP 필수 Metric 지정

#### Deferred

- Target Center 거리와 Target Boundary 거리 중 Off-target Severity 기준
- 최종 Off-target Metric 목록과 이름
- Metric별 비교 Preconditions와 Validation 기준

### Separate Directional Analysis Axes without 8 x 8 Cross-analysis

#### Status

Accepted on Day 02.

#### Context

Tracking에서는 Target이 화면에서 이동하는 방향과 Target이 Crosshair 기준으로 벗어난 방향이 서로 다른 질문에 답한다.

#### Decision

- Target Movement Direction과 Relative Target Direction을 서로 구분되는 분석 축으로 사용한다.
- 각 분석 축은 8개 Direction Category를 사용하는 방향으로 설계한다.
- 두 축의 결과는 별도로 생성하고 비교한다.
- `Movement Direction x Relative Direction`의 최대 64개 조합별 분석은 MVP에 포함하지 않는다.
- Tracking에서 Relative Target Direction은 우선 Off-target 상태의 문맥에 사용한다.

#### Reason

Target이 어느 방향으로 움직일 때 Tracking 상태가 변하는지와 Target을 놓쳤을 때 어느 방향으로 벗어났는지는 서로 다른 관측 질문이기 때문이다.

#### Alternative

- Horizontal / Vertical 분석만 유지
- 한 종류의 Direction만 사용
- 두 Direction의 모든 조합을 집계

#### Consequences and Trade-offs

- 두 Direction의 의미 혼동을 줄일 수 있다.
- 64개 조합을 제외하여 MVP Scope와 Sample 희소성 문제를 제한한다.
- 방향별 유효 관측량과 `unavailable` Preconditions가 필요하다.
- 정확한 각도 경계, 저속 상태, Noise 처리와 방향 귀속 규칙은 별도로 정의해야 한다.

#### Deferred

- 각도 Boundary
- Target Movement Direction 및 Relative Target Direction 계산 방식
- 정지 또는 저속 Target 상태
- Off-target Event에 Relative Direction을 귀속하는 기준
- 방향별 최소 Sample과 최종 Metric 목록
