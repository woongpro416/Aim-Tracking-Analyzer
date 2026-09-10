# Day 02 — Requirements & Contract

## Today's Goal

코드를 작성하지 않고 Primary Author가 사용자, 문제, Tracking Domain Definition, MVP 범위와 부분 Contract를 직접 결정했다. AI는 Requirement Reviewer, Contract Reviewer와 Technical Mentor 역할만 수행했다.

## Repository Review

- 기존 Build Plan과 Portfolio Design은 Working Reference다.
- `docs/01_requirements_and_contract.md`는 비어 있는 Skeleton에서 현재 Requirement 영역의 Source of Truth 초안으로 갱신했다.
- Day 01의 Tracking-only, Scenario/Run, Metadata/Metrics 분리, Run-level/Scenario-level 구분은 유지한다.
- Day 01의 Mean Error/RMSE 중심 Metric Scope는 Day 02 결정으로 대체한다.

## User and Problem

- Primary User는 별도 Coach 없이 자신의 Aim Trainer 영상을 분석하는 개인 사용자다.
- 사용자는 절대평가보다 같은 Scenario에 속한 자신의 독립 Run 결과를 비교하려 한다.
- 기존 Score만으로 확인하기 어려운 시계열 Tracking 상태, 방향, 이탈과 회복을 영상에서 직접 관측하려 한다.
- 실제 손 움직임, 자세, 감도 원인 또는 생리학적 Reaction Time을 진단하지 않는다.

## Confirmed Input Model

- Crosshair는 화면 정중앙에 고정되어 있다.
- Screen Center를 Crosshair Position으로 사용하고 별도 Crosshair Detection은 하지 않는다.
- 현재 Target은 유효 영역을 가진 단일 세로 타원형 도형이다.
- Run 한 개는 Video File 한 개다.

## Confirmed Tracking Boundary

```text
Target 접근
-> 최초 On-target
-> Tracking 분석 시작
-> On-target 유지
-> Off-target
-> Re-entry
-> 반복
```

- 최초 On-target 이후의 On-target와 Off-target Frame을 모두 분석한다.
- 최초 On-target 이전 Frame은 Tracking Metric 분석 구간이 아니다.
- Missing은 Off-target가 아니다.

## Confirmed Tracking State

- On-target는 Crosshair가 Target 유효 영역 내부에 있는 상태다.
- Off-target는 Target이 관측되었고 Crosshair가 Target 유효 영역 외부에 있는 상태다.
- Target 내부에서는 중심과의 거리에 따라 품질을 등급화하지 않는다.
- Tracking Stability는 On-target 유지, Off-target 발생과 지속, Re-entry, 반복적인 상태 전환의 관점에서 본다.

## Directional Analysis Decision

두 Direction을 구분한다.

```text
Target Movement Direction
= Target 영상의 screen-space 이동 방향

Relative Target Direction
= Crosshair 기준 Target 위치 방향

Direction Change Event
= Target Movement Direction이 변경된 사건
```

- 두 Direction은 별도로 기록하고 별도로 집계한다.
- 각 축은 8개 Direction Category를 사용하는 방향으로 설계한다.
- 8 x 8 조합 분석은 MVP에서 제외한다.
- Tracking의 Relative Target Direction은 우선 Off-target 상태의 방향을 설명한다.
- Flick의 Relative Target Direction은 Future Requirement에서 Target Appearance 시점의 Initial Direction을 설명한다.

## Recovery Decision

두 Recovery 개념을 합치지 않는다.

- Direction-change Recovery: Target Movement Direction 변경 이후의 회복
- Off-target Re-entry: Off-target 발생 이후 Target 영역으로 다시 진입하는 과정

방향전환 후 계속 On-target인 경우의 Recovery 의미와 두 Metric의 정확한 공식은 Deferred한다.

## Explicit MVP Scope Change

기존 방식:

```text
전체 유효 Frame
-> Target Center Distance
-> Mean / Median / RMSE
-> Tracking 품질 평가
```

변경된 방식:

```text
최초 On-target 이후
-> On-target / Off-target / Missing
-> Off-target 방향 / 크기 / 지속
-> Re-entry
-> Direction Change and Recovery
-> 방향별 Tracking 결과
```

기존 Mean / Median Tracking Error, RMSE X/Y, Vertical / Horizontal RMSE Ratio는 기존 의미로 MVP 필수 Metric에서 제거한다. `Tracking Error`라는 용어도 현재 Requirements에서는 사용하지 않는다.

Off-target 상태에서는 이탈의 크기를 정량화해야 하지만, Target Center 거리와 Target Boundary 거리 중 어떤 정의를 사용할지는 Deferred한다.

## Value and Result Contract

```text
0
= 유효한 관측 대상과 분석 구간이 있었지만 Event가 발생하지 않음

Missing
= 특정 Frame / Timestamp의 필요한 원본 관측값이 없음

unavailable
= Metric 계산에 필요한 데이터 또는 전제조건이 부족함

invalid
= 입력 또는 값이 Contract를 위반함
```

- Event가 없으면 Event Count와 Total Duration은 `0`이 될 수 있다.
- Event가 없으면 Event 기반 Average, Latency, Maximum은 `unavailable`이다.
- 방향별 `0`은 해당 방향의 유효 관측량이 0보다 클 때만 관측된 0이다.
- `not applicable`은 별도 상태로 추가하지 않는다.

## Run Comparison Decision

- Run-level 결과를 먼저 생성한다.
- 같은 Scenario의 Run A와 Run B에서 같은 종류의 결과를 나란히 비교한다.
- 다른 Run의 Frame-level Trajectory를 연결하지 않는다.
- 2~3개 Run 차이로 Trend, 지속적 향상 또는 약점 개선을 판정하지 않는다.
- 방향별 결과에는 유효 Frame 수 또는 유효 관측 시간을 확인할 수 있어야 한다.

## Traceability Requirement

```text
Video
-> Frame / Timestamp
-> Target State
-> Target Movement Direction
-> Relative Target Direction
-> On-target / Off-target / Missing
-> Event
-> Metric
-> Summary
```

최종 숫자만 제공하지 않고 Event와 Metric의 근거가 된 Run, Frame, Timestamp 또는 시간 구간을 추적 가능하게 유지한다. 구체적인 파일과 UI는 아직 결정하지 않는다.

## Future Requirement — Flick Shot

```text
새 Target Appearance
-> Initial Relative Direction
-> Target Acquisition 과정
-> First On-target
```

- Flick은 Tracking과 다른 Acquire 분석이다.
- Target 도달 시간, 초기 거리, 상대 경로, Path Directness, Overshoot와 Correction은 Future Requirement다.
- Target 소멸과 새 Target 출현은 영상상의 전환 증거이지 Mouse Click Timestamp 측정이 아니다.

## Superseded Working-reference Areas

나중에 Working Reference를 동기화할 때 다음 영역을 수정해야 한다.

- 프로젝트 Goal과 MVP Metric 목록
- Mean / Median Error 및 RMSE 정의
- `error_distance <= target_radius` 기반 On-target 정의
- Error 감소를 전제로 한 Recovery 정의
- Tracking Error Timeline과 X/Y 비교 그래프
- Metrics JSON 및 Summary 예시
- Run Comparison Metric과 Resolution mismatch 정책
- Phase별 구현 목표, 테스트 대상, Definition of Done
- MVP 완료 질문과 최종 성공 예시

Day 01 기록은 과거 판단을 보존하고 Day 02에서 대체되었다는 변경 이력을 남기는 방향을 우선 검토한다.

## Deferred Decisions

- 최소 사용자 입력과 최소 Output Contract
- 최초 On-target가 없는 Run의 결과
- Video Open 실패, Frame Decode 실패와 정상 종료 구분
- Target 영역과 실제 판정 영역 Validation
- 좌표계와 8방향 각도 Boundary
- Target Movement Direction, Relative Target Direction과 Noise 처리
- Off-target Event와 짧은 1 Frame 이탈 정의
- Off-target Severity 공식과 정식 이름
- 두 Recovery의 Operational Definition
- 방향별 최소 Sample과 최종 Metric 목록
- Timestamp 기준
- 길이가 다른 Run 및 방향별 관측 시간이 다른 결과의 비교 정책
- `unavailable` 이유 제공 여부
- Comparison Result 상태 전파
- Requirement ID 체계 도입 여부

## Questions to Resume on Day 03

1. 길이가 다른 Run의 Count와 Total을 그대로 비교할지, Rate를 함께 제공할지, 또는 `warning`을 사용할지 결정한다.
2. `unavailable` 결과에 계산 불가 이유를 반드시 제공할지 결정한다.
3. 정상 Tracking 분석이 성공했을 때 반드시 존재해야 하는 최소 Output을 정의한다.
4. 최소 사용자 입력과 Invalid Video Contract를 정의한다.

## Repository Changes

- Requirements & Contract에 Day 02 확정 내용 반영
- Data & Metric Specification에 확정 Domain Concept과 Deferred 목록 반영
- ADR에 Metric Scope 변경과 Directional Analysis 결정 기록
- Day 02 Workflow 작성
- Python 코드, 테스트, Architecture 및 Git 작업 없음

## Study Notes

- On-target 성공 상태와 Target 중심 거리는 같은 개념이 아니다.
- `0`은 관측된 없음이고, `unavailable`은 계산 전제조건 부족이다.
- Target Movement Direction과 Relative Target Direction은 같은 Trajectory에서 나오지만 다른 질문에 답한다.
- Event 결과는 Summary뿐 아니라 근거 Frame과 Timestamp까지 추적할 수 있어야 한다.
- 변경된 Requirement는 기존 Metric, 비교, 테스트와 완료 기준에 연쇄 영향을 준다.
