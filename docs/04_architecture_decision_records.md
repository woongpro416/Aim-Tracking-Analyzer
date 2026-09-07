# Architecture Decision Records

## Document Status

## Decision Selection Criteria

## Decision Index

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
