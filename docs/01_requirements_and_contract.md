# Requirements & Contract

## Document Status

- Status: Draft / Current Source of Truth
- Last updated: 2026-09-16 (Day 04)
- Role: 현재 MVP가 무엇을 만들고 어떤 입력과 결과를 지원하는지 정의한다.
- Rule: 이 문서에서 확정하지 않은 Algorithm, Threshold, Schema, UI 및 구현 구조는 임의로 확정하지 않는다.
- History: Day 01과 Day 02 Workflow는 당시의 판단을 보존하는 학습 기록이다. 충돌하는 경우 이 문서와 최신 ADR을 우선한다.

## Problem and User

Primary User는 별도 Coach 없이 자신의 Aim Trainer Recording을 분석하는 개인 사용자다.

기존 Score만으로 확인하기 어려운 다음 관측 결과를 한 Run 안에서 설명한다.

- Target이 화면에서 어떻게 움직였는가
- Crosshair가 Target 영역 안에 유지되었는가
- 언제, 어느 방향으로 Target을 놓쳤는가
- Off-target 상태가 얼마나 지속되었는가
- Target 영역으로 언제 다시 들어왔는가
- Target Movement Direction 변경 이후 Tracking 상태가 어떻게 변했는가

같은 Scenario의 독립 Run 결과를 나란히 확인할 수 있지만, 다른 사람이나 고정 Benchmark에 대한 절대평가를 목표로 하지 않는다.

## Core Principle

```text
Measurement != Diagnosis
```

- 영상에서 직접 관측하는 것은 screen-space Target 상태와 Crosshair 대비 관계다.
- 실제 손 움직임, Mouse 입력 Event와 생리학적 Reaction Time은 직접 관측하지 않는다.
- 자세, 근육, 감도, 입력 습관 또는 개인 능력의 원인을 진단하지 않는다.
- 결과 설명은 관측된 Run, Phase, Event와 Metric의 범위를 넘지 않는다.

## Domain Model

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

- 현재 MVP의 Aim Type은 Tracking이다.
- Run은 하나의 독립적인 분석 단위다.
- 현재 MVP에서 Video File 한 개에는 분석 대상 Run이 정확히 한 개만 존재해야 한다.
- Recording Video 전체 길이와 실제 Run Segment 길이는 다를 수 있다.
- Run Metadata와 분석으로 생성된 결과는 구분한다.
- Session과 Condition은 현재 데이터 계층으로 사용하지 않는다.

## Input Contract

### System and Analysis Core Input Boundary

최종 System Input은 Web Interface를 통한 단일 Video File Upload다. 최종 사용자가 Local Video Path를 직접 입력하지 않는다.

```text
Web Video Upload
-> Server가 내부 분석 가능한 Temporary Local File 준비
-> Local Video Path 생성
-> Analysis Core에 전달
```

Local Video Path는 Server와 Analysis Core 사이의 내부 Input Contract다. Day 04에서 직접 사용하는 Local Video Path는 Web Upload Boundary를 개발 중 대신하며, Analysis Core의 실제 내부 Contract를 검증하기 위한 입력이다.

Web Framework, Upload API와 Temporary File 처리의 구체적인 방식은 Deferred한다.

### Supported Input

- System과 Analysis Core가 처리하는 분석 대상은 Aim Trainer Recording Video 한 개다.
- 한 Video에는 분석 대상 Run이 정확히 한 개만 존재해야 한다.
- 현재 MVP는 nominal 60 FPS Recording만 지원한다.
- Crosshair는 화면 정중앙에 고정되어 있어야 한다.
- 시스템은 Crosshair를 별도로 Detection하지 않고 Screen Center를 기준점으로 사용한다.
- 현재 Target은 하나의 유효 영역을 가진 단일 세로 타원형 Target이다.
- 현재 Scenario의 실제 Run Duration은 60초다.
- Video는 Run 전후의 여유 녹화 구간을 포함할 수 있다.

### Invalid Input Decisions

- 지원 FPS 조건을 충족하지 않는 입력은 `invalid`다.
- 하나의 Video에 둘 이상의 독립 Run이 포함된 입력은 현재 MVP Contract 위반이며 `invalid`다.
- Video Open 실패, Frame을 읽을 수 없는 입력과 필요한 60초 Segment 부족의 세부 Contract는 Deferred한다.
- 59.94 FPS 허용 여부, nominal 60 FPS 판정 허용 오차와 Variable Frame Rate 처리는 Deferred한다.

## Run Boundary Resolution

정상 Aim Trainer Run에는 화면 중앙의 Countdown이 존재한다.

```text
3 -> 2 -> 1 -> 0
```

- `Countdown = 0`인 시점을 Run Start Marker로 사용한다.
- 기본 Workflow는 Automatic Countdown Detection이다.
- 자동 탐지가 정상적으로 성공하면 별도 사용자 확인 없이 Run Start를 확정한다.
- 자동 탐지가 실패하거나 불확실하여 정상 Run Start를 하나로 확정할 수 없으면 사용자에게 Manual Run Start 지정을 요청한다.
- Manual Start는 여러 Run 중 하나를 선택하는 기능이 아니라, 단 하나인 Run의 시작점을 확정하기 위한 Fallback이다.
- 최종적으로 Run Start가 하나 확정되어야 분석을 계속할 수 있다.
- Run End는 Domain 기준으로 Run Start 이후 정확히 60초가 지난 시점이다.
- `60 FPS x 60 seconds = exactly 3600 decoded frames`를 Contract로 고정하지 않는다.
- 정확한 Frame/Timestamp 경계 계산은 Timestamp Specification까지 Deferred한다.

## Run-level Data Boundary and Phases

Run-level Data Boundary와 Tracking Maintenance Metric Boundary를 구분한다.

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

### Run-level Data Boundary

- Run Start부터 Run End까지의 60초 전체를 Run-level 분석 데이터로 처리한다.
- First On-target 이전 Frame도 버리지 않는다.
- Runtime에서는 Sampling하지 않고 Decode 가능한 모든 Frame을 순서대로 처리한다.

### Initial Acquisition

- Run Start부터 First On-target까지의 Phase다.
- 아직 최초 Target을 획득하는 과정이다.
- 이 Phase의 Target 밖 상태를 Tracking Maintenance의 Off-target Event와 같은 의미로 취급하지 않는다.
- Frame-level Observation은 Runtime 계산에 사용하지만 정상 Internal Output으로 영구 저장하지 않는다.
- Acquisition Time, Path Directness, Overshoot와 같은 Acquisition Metric은 Deferred한다.

### Tracking Maintenance

- First On-target부터 Run End까지의 Phase다.
- On-target, Off-target, Off-target Event, Re-entry, Tracking Stability와 Directional Tracking Result는 이 Phase의 의미를 기준으로 한다.
- 기존 문장의 `Tracking 분석은 First On-target부터 시작한다`는 Tracking Maintenance Metric Boundary를 뜻하는 것으로 정교화한다.

### First On-target Result

최소한 다음 의미를 구분할 수 있어야 한다.

1. First On-target이 관측됨
2. Target을 충분히 관측했지만 Run 종료까지 First On-target이 관측되지 않음
3. Target Observation 부족 또는 Missing으로 발생 여부를 신뢰성 있게 판단할 수 없음

First On-target이 관측되지 않아도 Run Start와 60초 Segment를 정상적으로 처리했다면 Run-level 분석 자체는 성공할 수 있다.

```text
Initial Acquisition = 전체 Run
Tracking Maintenance = 존재하지 않음
Tracking Maintenance Metric = unavailable with user-facing reason
```

First On-target 없음은 `invalid input`이나 분석 시스템 실패와 같지 않다.

## Tracking State Contract

Tracking Maintenance에서 다음 상태를 사용한다.

- `On-target`: Crosshair가 Target의 유효 영역 내부에 있는 상태
- `Off-target`: Target이 관측되었고 Crosshair가 Target 유효 영역 외부에 있는 상태
- `Missing`: 해당 Frame 또는 Timestamp에서 필요한 Target Observation이 없는 상태

Missing은 Off-target로 변환하지 않는다. Target 내부에서는 Target 중심과의 거리에 따라 Tracking 품질을 다시 등급화하지 않는다.

## Metric Scope

기존 전체 유효 Frame의 Target 중심 거리를 Tracking 품질로 평가하던 다음 Metric은 기존 의미로 MVP 필수 Metric에서 제거한다.

- Mean Tracking Error
- Median Tracking Error
- RMSE X
- RMSE Y
- Vertical / Horizontal RMSE Ratio

현재 Tracking Maintenance 분석은 다음 책임을 중심으로 한다.

- On-target 유지
- Off-target 발생과 지속
- Off-target 방향과 크기
- Re-entry
- Direction Change와 Recovery
- Target Movement Direction별 결과
- Relative Target Direction별 결과
- 결과가 산출된 Valid Observation과 Missing/Coverage

Off-target Severity 공식, 1 Frame Off-target 처리와 Recovery Operational Definition은 Deferred한다.

## Directional Analysis

- `Target Movement Direction`: Target 영상이 시간에 따라 screen-space에서 이동하는 방향
- `Relative Target Direction`: Target이 Crosshair 기준으로 위치한 방향
- `Direction Change Event`: Target Movement Direction이 변경된 사건
- 두 Direction은 별도 분석 축으로 기록하고 별도로 집계한다.
- `Movement Direction x Relative Direction`의 8 x 8 조합 분석은 현재 MVP에 포함하지 않는다.
- Tracking에서 Relative Target Direction은 우선 Off-target 상태의 방향 문맥을 설명한다.
- 각 축은 8개 Direction Category를 사용하는 방향으로 두며 정확한 경계, Noise와 정지·저속 처리는 Deferred한다.
- 방향별 결과에는 Phase별 Valid Observation을 확인할 수 있어야 한다.

## Recovery Concepts

- `Direction-change Recovery`: Target Movement Direction 변경 이후의 Tracking 회복
- `Off-target Re-entry`: On-target에서 Off-target로 이탈한 뒤 Target 영역에 다시 진입하는 과정
- 두 개념은 시작 Event가 다르므로 하나의 Metric으로 합치지 않는다.
- 두 개념의 정확한 Operational Definition과 계산 공식은 Deferred한다.

## Run Analysis and Comparison Responsibilities

### Single Run Result

- 해당 Run에서 실제로 관측된 Raw Metric과 Valid Observation을 제공한다.
- 방향별 Raw Result를 제공할 수 있지만 하나의 Run만으로 방향 간 우열, 개인 취약성 또는 장기 성향을 자동 판단하지 않는다.

### Selected Run Comparison

- 같은 Scenario의 독립 Run 결과를 나란히 확인할 수 있다.
- 서로 다른 Run의 Frame-level Trajectory를 연결하지 않는다.
- Run을 완전히 동일한 자극을 사용한 Strict A/B Test로 해석하지 않는다.
- Raw Count와 Raw Duration을 유지하고 관련 Valid Observation을 함께 확인할 수 있어야 한다.
- 시간당 Event Rate는 현재 MVP의 필수 Metric이 아니다.
- 2~3개 Run 차이로 지속적인 향상, 약점 개선 또는 Trend를 자동 판정하지 않는다.

### Future Personal Pattern Analysis

- 여러 Run 결과를 누적하여 반복적인 방향 패턴, Event 형태와 시간 변화를 분석하는 별도 Future 영역이다.
- Normalization, 최소 Run 수, Trend 기준과 통계 방식은 Future Contract에서 결정한다.
- 반복 패턴을 설명하더라도 신체, 자세, 감도 또는 입력 습관의 원인을 진단하지 않는다.
- Future AI Run Pattern Analysis는 이 영역의 선택적 분석 방법이며 현재 MVP 완료 조건이 아니다.

## Result State Contract

### Zero

- 유효한 관측 대상과 분석 구간이 존재했지만 해당 Event가 발생하지 않은 상태다.
- Event Count와 Total Event Duration은 `0`이 될 수 있다.
- 방향별 `0`은 해당 방향의 Valid Observation이 존재할 때만 관측된 0으로 해석한다.

### Missing

- 특정 Frame 또는 Timestamp에서 필요한 원본 Observation이 없는 상태다.
- Missing은 Off-target나 `0`이 아니다.
- Missing 누적은 Metric이 `unavailable`이 되는 원인이 될 수 있다.

### Unavailable

- Metric 계산에 필요한 데이터 또는 전제조건이 부족한 상태다.
- Event 표본이 필요한 Average, Median, Maximum 또는 Latency는 해당 Event가 없으면 `unavailable`일 수 있다.
- 모든 unavailable Metric은 사용자가 확인 가능한 Reason을 가져야 한다.
- 같은 원인이 여러 Metric에 영향을 주더라도 각 Metric에서 이유를 확인할 수 있어야 한다.
- Reason은 Domain 의미로 설명하며 내부 예외명이나 Debug Code만으로 표시하지 않는다.
- Reason Code, Enum과 내부 Debug 구조는 Deferred한다.

### Invalid

- 입력 또는 값이 Contract를 위반한 상태다.
- Invalid Input은 유효 분석의 특정 Metric이 `unavailable`인 상태와 다르다.

### Not Applicable

- 현재 별도 상태로 추가하지 않는다.

## Output Contract

Internal Analysis Output과 User-facing Summary를 구분한다.

### Structured Analysis Result

Structured Analysis Result는 기존 Internal Analysis Output의 canonical structured form이다. 새로운 별도 Output 계층을 만들지 않으며 기존 Run, Phase, Event와 Metric 계층의 의미와 Output Contract를 유지한다.

```text
Analysis Core
-> Structured Analysis Result
   |-> Web Response Representation
   `-> TXT Report Representation
```

- Web Response와 TXT Report는 동일한 Structured Analysis Result에서 파생한다.
- 각 Representation은 별도의 분석 계산을 수행하지 않는다.
- TXT를 분석 결과의 원본으로 사용하거나 TXT를 다시 읽어 Web Result를 생성하지 않는다.
- TXT Report는 Structured Analysis Result에서 생성하고 저장할 수 있어야 한다.
- TXT 자동 생성 여부와 Web/TXT의 구체적인 표현 Contract는 Deferred한다.

### Internal Analysis Output

정상적인 Run-level 분석 결과에는 최소한 다음 개념이 존재해야 한다.

#### Run-level

- 원본 Recording과 Run의 출처 관계
- 독립 Run 식별
- 원본 Recording 안의 Run Start와 Run End
- Run Start가 Automatic 또는 Manual 중 어떤 방식으로 결정되었는지
- 필요한 60초 Run Segment 처리 완전성

Countdown Detection의 내부 판단 과정과 Confidence 상세 근거는 정상 Output의 필수 요소가 아니다.

#### Phase-level

- Phase 존재 또는 판단 상태
- Phase의 시간 범위 또는 Duration
- First On-target 판단 결과
- Phase별 Valid Observation
- Phase별 Missing 또는 Coverage 규모
- Phase별 Direction Valid Observation
- Phase가 없거나 판단 불가능한 경우의 Domain Reason

#### Event-level

- Operational Definition이 확정되어 생성되는 Event는 개별 결과를 영구 보존한다.
- 개별 Event는 관련 Run과 Phase, Event 종류, Duration, 발생 순서, Run 내부 시간적 위치 또는 시간 범위와 필요한 Direction 문맥을 구분할 수 있어야 한다.
- Event ID, Timestamp 자료형, Schema와 모든 Event 종류는 아직 확정하지 않는다.

#### Metric-level

- 확정된 Metric 결과와 계산에 사용된 Run/Phase/Direction 문맥
- Metric Result State
- unavailable인 경우 사용자 확인 가능한 Reason
- 관련 Valid Observation과 Missing/Coverage 근거

### User-facing Summary

- Internal Analysis Output에서 파생되어야 한다.
- 사용자가 한 Run에서 무엇이 관측되었는지 이해할 수 있는 Run-level Metric과 필요한 설명을 중심으로 한다.
- Raw Frame Data와 모든 Event Detail을 그대로 노출할 필요는 없다.
- Summary Metric과 unavailable Reason은 내부 Run/Phase/Event/Metric 결과와 의미가 일치해야 한다.
- 사용자 Summary의 최종 최소 항목과 표시 방식은 Deferred한다.

## Persistence and Traceability Scope

Runtime에서는 Decode 가능한 모든 Frame을 순서대로 분석한다.

정상 Internal Output에 영구 저장하지 않는 항목:

- Raw Frame 이미지 복제본
- 모든 Frame Timestamp
- 전체 구조화된 Frame-level Observation
- Metric에서 원본 Frame으로 이동하는 기능

Frame-level Observation은 Validation 또는 Debugging 실행에서 선택적으로 생성할 수 있다.

현재 MVP의 필수 Traceability 범위는 다음과 같다.

```text
Original Video
-> Run
-> Run Boundary
-> Phase
-> Event / Metric
-> Summary
```

저장된 Internal Output만으로 Frame-level Event를 재계산하거나 새로운 Direction Boundary를 적용하는 것은 보장하지 않는다. 필요하면 원본 Video를 새로운 분석 로직으로 다시 처리한다.

## MVP Scope

- 통제된 nominal 60 FPS Tracking Recording 입력
- Recording 내부의 단일 60초 Run Segment 분석
- Automatic Countdown 기반 Run Start Resolution과 Manual Fallback
- 모든 Decode 가능한 Frame의 Sequential Runtime Processing
- Initial Acquisition과 Tracking Maintenance Phase 구분
- On-target / Off-target / Missing 상태 분석
- Off-target Event와 Re-entry 분석
- Off-target 방향, 크기와 지속 분석
- Target Movement Direction별 분석
- Off-target 상태의 Relative Target Direction 분석
- Direction Change와 Direction-change Recovery 분석
- Run / Phase / Event / Metric 중심 Internal Output
- 같은 Scenario의 독립 Run Result Comparison
- Known-value Test, Synthetic Validation과 Manual Validation

## Future and Out of Scope

- Flick Shot Analyzer와 Flick 전용 Metric
- Personal Pattern Analysis, Trend와 AI Pattern Analysis
- Mouse Click 또는 입력 장치 Event 검출
- 실제 손 또는 Crosshair의 물리적 이동 속도 측정
- 생리학적 Reaction Time 측정
- 자세, 근육, 감도와 습관 원인 진단
- 절대적인 좋은 Aim / 나쁜 Aim 판정
- 다른 사용자 Population 또는 고정 Benchmark 비교
- Movement Direction과 Relative Direction의 8 x 8 조합 분석
- YOLO, LLM Coach와 Real-time Streaming
- FastAPI와 Web UI의 구체적인 구현. Web Upload는 최종 System Boundary로 확정하지만 현재 Analysis Core 구현 범위에는 포함하지 않는다.
- Database와 Version Migration

## Deferred Decisions

### Video and Time

- exact Timestamp 계산 기준
- 59.94 FPS 허용 여부와 nominal FPS 판정 허용 오차
- Variable Frame Rate 처리
- Video Open 실패, Frame Decode 실패와 정상 EOF의 세부 Contract
- Run Start 자동 탐색 실패 후 Manual Start가 제공되지 않은 경우
- Run Start 이후 필요한 60초 Segment가 부족한 경우

### Phase and Observation

- First On-target 판단 Coverage Threshold
- Run Start와 동시에 First On-target인 경우 Initial Acquisition 표현
- Valid Observation의 Count / Duration 표현
- Missing / Coverage의 Count / Duration / Ratio 표현
- Target 영역과 실제 Aim Trainer 판정 영역의 일치 Validation

### Direction and Event

- 정확한 8방향 Angle Boundary
- Direction Noise와 정지·저속 Target 처리
- Off-target Event와 짧은 1 Frame 이탈 정의
- Off-target Severity 공식
- Direction-change Recovery와 Off-target Re-entry Operational Definition
- Event별 Direction 귀속
- 방향별 최소 Sample
- 최종 Metric 전체 목록
- Acquisition Metric

### Output and Future Analysis

- User-facing Summary의 최종 최소 항목
- 전체 JSON Schema, DB와 UI
- Web Framework, Endpoint URL, HTTP Method, Multipart Field, FastAPI/Pydantic Schema와 HTTP Error Response
- Upload Size Limit, 확장자 정책, Temporary Directory, File Naming, Delete Timing, 동시성, Streaming, Cloud Storage와 Security 구현
- TXT Format, Filename, 저장 위치, Encoding, Template, 자동 생성 여부, Download 방식과 보관 기간
- Personal Pattern Analysis, Trend와 AI Pattern Analysis Contract
- Version Migration과 Requirement ID 체계

## Superseded Decisions

다음 초기 결정은 이 문서와 최신 ADR로 대체되었다.

- 전체 Frame Target 중심 거리 기반 Tracking Error
- Mean / Median Tracking Error와 RMSE X/Y를 MVP 필수 Metric으로 지정한 결정
- Recording Video 전체를 곧 Run으로 보는 해석
- Run-level 분석 범위를 First On-target 이후로만 보는 해석
- 모든 Metric을 Frame/Timestamp까지 영구 역추적해야 한다는 Traceability 범위

루트의 Build Plan과 Portfolio Design은 Working Reference이며 최신 결정과 충돌하는 경우 이 문서를 우선한다.
