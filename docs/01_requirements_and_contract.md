# Requirements & Contract

## Document Status

- Status: Draft
- Last updated: 2026-09-10 (Day 02)
- Role: 확정된 Requirement 영역의 현재 Source of Truth
- Rule: 오늘 합의하지 않은 Metric 공식, 자료형, Algorithm, UI는 확정하지 않는다.

## Problem

기존 Aim Trainer의 Score만으로는 Tracking Run 안에서 다음 상태가 시간에 따라 어떻게 나타났는지 확인하기 어렵다.

- Target이 화면에서 어떻게 움직였는가
- Crosshair가 Target 영역 안에 유지되었는가
- 언제, 어느 방향으로 Target을 놓쳤는가
- Off-target 상태가 얼마나 지속되었는가
- Target 영역으로 언제 다시 들어왔는가
- Target의 움직임 변화 이후 Tracking 상태가 어떻게 회복되었는가

이 시스템은 원인을 진단하지 않고, 영상에서 직접 관측 가능한 Tracking 상태와 변화를 제공한다.

## User

Primary User는 별도 Coach 없이 자신의 Aim Trainer 녹화 영상을 분석하고, 같은 Scenario에서 수행한 자신의 Run들을 비교하려는 개인 사용자다.

## Goals

- 하나의 Tracking Run에서 On-target 유지와 Off-target 발생을 시계열로 확인한다.
- Target Movement Direction에 따라 Tracking 상태가 어떻게 관측되는지 확인한다.
- Off-target 상태에서 Target이 Crosshair 기준 어느 방향에 위치했는지 확인한다.
- Off-target의 크기, 지속, Re-entry를 정량적으로 확인한다.
- Target Movement Direction 변경 이후의 Recovery와 Off-target 이후 Re-entry를 구분한다.
- 같은 Scenario의 독립된 Run 결과를 나란히 비교한다.
- 최종 결과의 근거를 Frame 또는 Timestamp 수준까지 추적할 수 있어야 한다.

## Requirement Facts

- 영상에서 직접 관측하는 것은 screen-space Target 상태와 Crosshair 대비 관계다.
- 실제 손 움직임, Mouse 입력 Event, 생리학적 Reaction Time은 직접 관측하지 않는다.
- 관측된 차이로부터 자세, 근육, 감도, 에이밍 습관의 원인을 확정하지 않는다.
- `Measurement != Diagnosis` 원칙을 적용한다.

## Design Decisions

### Tracking Analysis Boundary

- Tracking 분석은 최초 On-target 시점부터 시작한다.
- 최초 On-target 이후의 On-target Frame과 Off-target Frame을 모두 Tracking 데이터로 사용한다.
- 최초 On-target 이전 구간은 Tracking Metric의 분석 구간이 아니다.
- Off-target와 Target Missing은 서로 다른 상태다.

### On-target and Off-target

- `On-target`: Crosshair가 Target의 유효 영역 내부에 있는 상태
- `Off-target`: Target이 관측되었고 Crosshair가 Target의 유효 영역 외부에 있는 상태
- Target 내부에서는 중심과의 거리에 따라 Tracking 품질을 다시 등급화하지 않는다.

### Directional Analysis

- `Target Movement Direction`: Target 영상이 시간에 따라 화면상 이동하는 방향
- `Relative Target Direction`: Target이 Crosshair 기준으로 위치한 방향
- `Direction Change Event`: Target Movement Direction이 시간에 따라 변경된 사건
- 두 Direction은 서로 구분되는 분석 축으로 기록하고 각각 결과를 생성한다.
- `Movement Direction x Relative Direction`의 8 x 8 조합별 분석은 현재 MVP에 포함하지 않는다.
- Tracking에서 Relative Target Direction은 우선 Off-target 상태의 방향을 설명하는 데 사용한다.
- Target Movement Direction과 Relative Target Direction은 각각 8개 방향 Category를 사용하는 것을 MVP 방향으로 두며, 정확한 경계는 Deferred한다.

### Recovery Concepts

- `Direction-change Recovery`: Target Movement Direction 변경 이후의 Tracking 회복
- `Off-target Re-entry`: On-target에서 Off-target로 이탈한 뒤 Target 영역에 다시 진입하는 과정
- 두 개념은 시작 Event가 다르므로 하나의 Metric으로 합치지 않는다.
- 정확한 Operational Definition과 계산 공식은 Deferred한다.

### Metric Scope Change

기존 전체 유효 Frame의 Target 중심 거리를 Tracking 품질로 평가하던 다음 Metric은 기존 의미로 MVP 필수 Metric에서 제거한다.

- Mean Tracking Error
- Median Tracking Error
- RMSE X
- RMSE Y
- Vertical / Horizontal RMSE Ratio

현재 Requirements에서는 기존 `Tracking Error`라는 용어를 사용하지 않는다.

대신 Off-target 상태에서 다음 사용자 목적을 분리한다.

- 이탈 방향
- 이탈 크기
- 이탈 지속
- Re-entry
- Direction-change Recovery

Off-target 이탈 크기의 공식과 정식 Metric 이름은 Data & Metric Specification에서 결정한다.

### Run Comparison

- Run 한 개는 Video File 한 개다.
- 각 Run은 독립적으로 분석한다.
- 서로 다른 Run의 Frame-level Trajectory를 연결하지 않는다.
- 같은 Scenario에 속한 Run의 결과만 현재 MVP의 직접 비교 대상으로 한다.
- 2~3개 Run의 결과를 나란히 비교할 수 있지만, 이를 근거로 Trend 또는 지속적인 실력 향상을 판정하지 않는다.
- 여러 Run을 평균낸 별도 Scenario Summary는 현재 MVP에 포함하지 않는다.

### Traceability

- 시점별 분석 상태는 원본 Run의 Frame 또는 Timestamp와 연결할 수 있어야 한다.
- Event 결과는 근거가 된 시점 또는 시간 구간으로 추적할 수 있어야 한다.
- 방향별 결과는 해당 방향의 유효 관측량을 함께 확인할 수 있어야 한다.
- 구체적인 파일, Schema, ID, UI 표현은 아직 결정하지 않는다.

## Input Constraints / Assumptions

- MVP 입력은 Crosshair가 화면 정중앙에 고정된 Aim Trainer 녹화 영상이다.
- 시스템은 Crosshair를 별도로 Detection하거나 Tracking하지 않고 화면 중심을 Crosshair 기준점으로 사용한다.
- 영상의 Crop, Padding 또는 화면 구성 변경으로 Crosshair 기준점이 달라지지 않았다고 가정한다.
- 현재 Tracking 대상은 하나의 유효 영역을 가진 단일 세로 타원형 Target이다.
- 시각적으로 검출한 Target 영역과 Aim Trainer의 실제 판정 영역이 같은지는 Validation이 필요하다.

## MVP Scope

- Tracking Analysis Only
- 최초 On-target 이후의 Run-level Tracking 분석
- On-target / Off-target / Missing 상태 구분
- On-target 유지와 Off-target Event 분석
- Off-target 방향, 크기, 지속 및 Re-entry 분석
- Target Movement Direction별 분석
- Off-target 상태의 Relative Target Direction 분석
- Direction Change Event와 Direction-change Recovery 분석
- 결과와 근거 시계열 데이터의 Traceability
- 같은 Scenario의 독립 Run 결과 비교

## Future Requirements

### Flick Shot Analyzer

- Flick은 `새 Target Appearance -> First On-target`의 Target Acquisition 구간을 분석한다.
- Flick에서는 Target Appearance 시점의 Initial Relative Target Direction을 사용한다.
- Target까지의 도달 시간, 초기 거리, 상대 경로, Path Directness, Overshoot, Correction은 Future Requirement다.
- Target 소멸과 새 Target 출현은 영상상의 Event Transition으로 관측할 수 있지만, Mouse Click Timestamp를 직접 측정한 것으로 해석하지 않는다.

### Other Extensions

- AI Run Pattern Analysis
- 여러 Run의 Trend / Summary / 지속적 향상 판정
- 다른 Scenario 간 직접 비교

## Out of Scope

- Flick Shot 구현
- Mouse Click 또는 입력 장치 Event 검출
- 실제 손 또는 Crosshair의 물리적 이동 속도 측정
- 생리학적 Reaction Time 측정
- 자세, 근육, 감도, 습관 원인 진단
- 절대적인 좋은 Aim / 나쁜 Aim 판정
- 다른 사용자 Population 또는 고정 Benchmark 비교
- Movement Direction과 Relative Direction의 8 x 8 조합 분석
- YOLO, FastAPI, Web UI, LLM Coach, Real-time Streaming

## Input Contract

현재 확정된 부분:

- Video File 한 개가 Run 한 개를 구성한다.
- Tracking 입력 영상은 고정된 화면 중앙 Crosshair와 단일 Target 조건을 충족해야 한다.
- Scenario-level Comparison의 대상 Run은 같은 Scenario에 속해야 한다.

최소 사용자 입력 정보, 허용 Video 조건, Video Open 및 Decode 실패 Contract는 아직 Deferred한다.

## Output Contract

현재 확정된 부분:

- 정상적인 Tracking 분석 구간에는 시점별 On-target / Off-target / Missing 상태가 존재한다.
- Target Movement Direction 결과와 Relative Target Direction 결과는 별도로 제공한다.
- Off-target Event와 Re-entry Event는 근거 시간 구간으로 추적 가능해야 한다.
- Direction Change Event와 Off-target Event는 독립적으로 보존한다.
- 방향별 결과에는 해당 방향의 유효 관측량을 함께 확인할 수 있어야 한다.
- 같은 Scenario의 Run은 동일한 종류의 확정 Metric을 나란히 비교할 수 있어야 한다.

최종 Metric 목록, 결과 자료형, 파일 형식, 그래프와 Report 구성은 아직 확정하지 않는다.

## Failure, Missing, Empty, and Value States

### Zero

- 유효한 관측 대상과 분석 구간이 실제로 존재했지만 Event가 발생하지 않은 경우다.
- Event Count와 Total Event Duration은 `0`이 될 수 있다.
- 방향별 `0`은 해당 방향의 유효 관측량이 0보다 클 때만 관측된 0으로 해석한다.

### Missing

- 특정 Frame 또는 Timestamp에서 필요한 원본 관측 데이터가 없는 상태다.
- Missing은 Off-target로 해석하지 않는다.

### Unavailable

- 필요한 데이터 또는 전제조건이 부족하여 Metric을 신뢰성 있게 계산할 수 없는 상태다.
- Event가 없어 Event 기반 Average, Latency 또는 Maximum을 계산할 수 없는 경우도 `unavailable`로 처리한다.

### Invalid

- 입력 또는 값이 Contract를 위반한 상태다.

### Not Applicable

- 현재 별도 상태로 추가하지 않는다.

## Success Criteria

현재 Requirements 단계의 성공 기준:

- 사용자, 문제, Tracking 분석 구간과 상태를 설명할 수 있다.
- Target Movement Direction과 Relative Target Direction을 구분할 수 있다.
- Direction-change Recovery와 Off-target Re-entry를 구분할 수 있다.
- `0`, `Missing`, `unavailable`, `invalid`의 차이를 설명할 수 있다.
- 현재 MVP와 Future Requirement를 구분할 수 있다.

시스템의 최소 Output과 각 Metric의 Acceptance Criteria는 아직 확정하지 않는다.

## Superseded Working-reference Decisions

다음 기존 결정은 이 문서의 Day 02 결정으로 대체한다.

- 전체 Frame Target 중심 거리 기반 Tracking Error
- Mean / Median Tracking Error의 MVP 필수 Metric 지정
- RMSE X/Y 및 Vertical / Horizontal RMSE Ratio의 MVP 필수 Metric 지정
- Error 감소를 전제로 미리 작성된 Recovery 정의
- Horizontal / Vertical만을 MVP 방향 분석으로 두고 복잡한 방향 분류를 전부 Future로 둔 결정

루트의 Build Plan과 Portfolio Design은 Working Reference이며, 위 영역에서는 이 문서를 우선한다.

## Open Questions / Deferred Decisions

### Requirement and Contract

- 정상 분석 완료 시 반드시 존재해야 하는 최소 Output
- 사용자가 입력해야 하는 최소 Metadata
- 최초 On-target가 한 번도 발생하지 않은 Run의 결과 Contract
- Video Open 실패, Frame Decode 실패, 정상 종료의 구분
- `unavailable` 결과에 이유를 반드시 함께 제공할지 여부
- 길이가 다른 Run 또는 방향별 관측 시간이 다른 결과의 비교 정책
- Requirement ID 체계 도입 여부

### Data and Metric

- Target의 정확한 유효 영역과 영상상 경계 Validation
- 화면 좌표계와 방향 Category의 각도 경계
- Target Movement Direction 및 Relative Target Direction 계산 방식
- 정지 또는 저속 상태와 Noise 처리
- Off-target Event와 짧은 1 Frame 이탈의 정의
- Off-target 이탈 크기를 Center 거리와 Boundary 거리 중 무엇으로 정의할지
- Direction-change Recovery와 Off-target Re-entry의 Operational Definition
- 방향전환 후 계속 On-target인 경우 Recovery 결과 의미
- 방향별 최소 Sample과 `unavailable` 조건
- 각 Direction에 제공할 최종 Metric 목록
- Frame Index와 Timestamp의 의미 및 Timestamp 계산 기준

### Comparison

- Raw Count / Total과 관측 시간당 비율의 관계
- Run 길이가 다를 때 `warning` 또는 비교 제한 여부
- 한쪽 Metric이 `unavailable`인 경우 Comparison Result Contract
- Comparison 상태가 최종 결과에 전파되는 방식
