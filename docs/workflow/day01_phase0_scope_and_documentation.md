# Day 01 — Phase 0 Scope and Documentation Setup

## Today's Goal

오늘은 구현을 시작하지 않고, Aim Tracking Analyzer의 문제 범위와 핵심 용어를 정리했다.

프로젝트의 목표는 빠른 완성이 아니라 다음 개발 흐름을 직접 경험하는 것이다.

```text
Requirement
→ Contract
→ Responsibility
→ Implementation
→ Test
→ Validation
→ Change Management
→ Release
```

Primary Author와 Primary Coder는 프로젝트 작성자이며, AI는 Requirement Reviewer, Design Reviewer, Concept Tutor, Debugging Partner, Code Reviewer, Test Reviewer 역할로 제한한다.

## MVP Scope Decision

현재 MVP는 **Tracking Analysis Only**로 확정했다.

```text
Current MVP:
Tracking Video
→ Continuous Trajectory
→ Tracking Metrics

Future Extension:
Flick Shot Video
→ Target Acquisition Event
→ Flick-specific Metrics
```

Tracking은 continuous time-series analysis, Flick Shot은 event-based target acquisition analysis에 가깝기 때문에 하나의 Metric 체계로 평가하지 않는다.

YOLO, FastAPI, Web UI, LLM Coach, Real-time Streaming과 Flick Shot 구현은 현재 MVP 범위에 포함하지 않는다.

## Data Concept

최종 데이터 개념은 다음과 같이 단순화했다.

```text
Aim Type
→ Scenario
→ Run
→ Run Metadata
→ Run Metrics
```

- **Aim Type**: Tracking 또는 Flick Shot과 같은 상위 연습 유형
- **Scenario**: Smooth Tracking, Reactive Tracking, Vertical Tracking과 같은 연습 카테고리
- **Run**: Scenario에 추가되는 독립된 영상 하나
- **Run 1개 = Video File 1개**
- **Run Metadata**: 입력 영상과 연습 환경에 관한 정보
- **Run Metrics**: 영상 분석으로 계산된 결과

`Session`과 `Condition`은 현재 데이터 계층으로 사용하지 않는다.

## Analysis Levels

분석 수준은 다음 두 가지로 구분했다.

### Run-level Analysis

영상 하나 내부의 Frame, Timestamp, Trajectory, Tracking Metric을 분석한다.

서로 다른 Run의 Frame-level Trajectory는 연결하지 않는다.

### Scenario-level Run Comparison

같은 Scenario에 속한 독립 Run들의 Metric을 비교한다.

현재 MVP에서는 여러 Run을 평균내는 별도 Session Summary 또는 Scenario Summary를 만들지 않는다. Scenario-level Trend와 평균은 필요할 경우 향후 확장한다.

## Run Metadata and Run Metrics

Run Metadata와 Run Metrics는 분리한다.

Run Metadata 후보:

- run_id
- scenario
- date
- resolution
- fps
- sensitivity
- dpi
- warmup
- notes

Run Metrics 후보:

- Mean Error
- Median Error
- RMSE X/Y
- On-target Ratio
- Recovery Latency
- Detection Coverage

Metadata 차이는 비교를 자동으로 차단하지 않지만, 차이로부터 Metric 변화의 원인을 인과관계로 확정하지 않는다.

## Comparison Policy

현재 확정한 비교 정책:

- 같은 Scenario의 Run Comparison은 가능
- 다른 Scenario의 직접 비교는 현재 MVP 범위 밖
- Sensitivity, Warm-up, Date 차이가 있어도 비교 가능
- Metadata 차이는 결과 해석 시 참고하며 인과관계로 단정하지 않음
- Recommended Recording Profile은 `1920 × 1080`, `nominal 60 FPS`
- Recommended Recording Profile은 입력 허용 조건이 아님
- 다른 Resolution 또는 FPS의 영상도 입력 자체를 거부하지 않음

Resolution mismatch 정책:

- Run Comparison 자체는 가능
- Mean Error, RMSE X, RMSE Y는 raw pixel Metric이므로 직접 비교는 `incompatible`
- 정규화 Metric은 Future Extension으로 보류

FPS mismatch 정책:

- millisecond 단위 Temporal Metric 비교 자체는 가능
- 시간 해상도와 측정 정밀도 차이에 대한 `warning` 필요
- FPS Metadata가 잘못됐거나 Temporal Metric 전제조건을 충족하지 못하면 해당 Metric은 `unavailable`

## Comparison Status

```text
incompatible:
두 Run 모두 Metric은 계산되었지만
척도 또는 전제조건 차이로 직접 비교할 수 없음

warning:
Metric 비교는 가능하지만
정밀도 또는 해석에 주의가 필요함

unavailable:
특정 Run에서 Metric 자체를
신뢰성 있게 계산할 수 없음
```

## Minimum Validation Evidence

결과 숫자가 출력되는 것만으로 분석 성공으로 판단하지 않는다.

최소 신뢰 근거는 다음 세 단계다.

1. **Known-value Unit Test**
   - 사람이 결과를 계산할 수 있는 작은 Input으로 기본 Metric 공식 검증
2. **Synthetic Trajectory Validation**
   - 방향전환 시점과 Recovery Delay를 알고 있는 데이터에서 Known Value 복원 정도 확인
3. **Manual Frame Validation**
   - 실제 영상 일부 Frame의 Target 위치를 수동 확인
   - Detection Coverage와 Centroid Error 검증

## Documentation Decision

기존 두 문서는 초기 설계 초안으로 보존한다.

- `aim_tracking_project_build_plan.md`
- `vision_based_aim_tracking_analyzer_portfolio_design.md`

확정된 내용은 다음 7개 산출물로 나누어 다시 작성한다.

1. Requirements & Contract
2. Data & Metric Specification
3. Lightweight Architecture
4. Architecture Decision Records
5. Test & Validation Plan
6. Validation Report
7. Final README

첫 6개 문서는 `docs` 아래에 빈 뼈대를 생성했고, Final README는 저장소 루트 `README.md`에 빈 뼈대를 생성했다.

새 문서는 사용자가 질의응답을 통해 먼저 작성하고, AI는 모순, 책임 중복, 검증 불가능한 주장, 구현되지 않은 내용의 과장 여부를 검토한다.

## Deferred Decisions

다음 항목은 현재 임의로 확정하지 않았다.

- Target의 정확한 정의
- Crosshair를 Screen Center로 보는 가정의 근거
- 화면 좌표계
- Frame Index와 Timestamp의 의미 및 Timestamp 계산 기준
- Target Detection 성공과 Missing 상태
- Video Open 실패, Frame Decode 실패, 정상 종료의 구분
- 최소 Output Contract
- Median Error, On-target Ratio, Detection Coverage, Vertical / Horizontal RMSE Ratio, Recovery Latency의 Resolution mismatch 비교 정책
- Temporal Metric을 `unavailable`로 판단하는 구체적인 조건
- Comparison 상태가 최종 결과로 전파되는 방식
- `date`의 자료형, 형식, timezone

Timestamp 기준은 Phase 1 Video Reader에서, Metric별 비교 Preconditions는 각 Metric을 설계하는 Phase에서, Comparison Result Contract는 Phase 6에서 결정한다.

## Repository Changes

- 기존 설계 초안의 Tracking/Flick 구분과 Scenario/Run 용어를 정리함
- `docs` 디렉터리 생성
- 6개 내부 산출물의 빈 뼈대 생성
- 루트 `README.md`에 Final README 빈 뼈대 생성
- Python 코드 및 기능 구현 없음
- Git commit 및 push 없음

## Next Step

다음 작업은 `Requirements & Contract` 문서부터 시작한다.

한 번에 한 항목씩 한국어로 질의응답하고, 사용자가 초안을 먼저 작성한 뒤 Review를 진행한다.
