# Lightweight System Design

## Document Status

- Status: Draft / Implementation Entry Design
- Last updated: 2026-09-16 (Day 04)
- Role: 상세 Class나 Package 구조를 정하지 않고 MVP Pipeline과 단계별 책임을 설명한다.

## Design Goals

- Recording 안의 분석 대상 Run을 신뢰할 수 있게 분리한다.
- Decode 가능한 모든 Frame을 순서대로 처리한다.
- Frame-level Observation을 Event와 Metric으로 변환한다.
- Run, Phase, Event와 Metric의 책임을 섞지 않는다.
- 정상 Output은 Run/Phase/Event/Metric 수준으로 유지하고 Frame-level Persistence는 선택적 Validation Artifact로 제한한다.
- 각 구현 Slice를 독립적으로 검증할 수 있어야 한다.

## System Boundary

최종 서비스의 System Input은 Web Interface를 통한 단일 Video File Upload다. 최종 사용자는 Local Video Path를 직접 입력하지 않는다.

```text
User
-> Web Frontend (Vue 3 + Vite)
-> Web/API Boundary
-> Video Upload Handling
-> Temporary Local File
-> Local Path
-> Analysis Core
-> Structured Analysis Result
   |-> Web Response
   `-> TXT Report
```

Web Layer의 Frontend Technology는 Vue 3 + Vite를 사용한다. Frontend는 Video Upload UI와 Analysis Result 표시를 담당하며 Analysis Core에 직접 의존하지 않고 Web/API Boundary를 통해 연결된다.

Server 측 Web/API Boundary는 업로드된 Video를 내부 분석 가능한 Local File로 준비하고 Local Path를 Analysis Core에 전달한다. Analysis Core가 생성하는 Structured Analysis Result는 기존 Internal Analysis Output의 canonical structured form이며, Web Response와 TXT Report는 동일한 Result에서 파생한다.

Vue 프로젝트 생성, Frontend 세부 구조, FastAPI, Upload API와 Temporary File 처리의 구체적인 구현은 현재 Analysis Core 구현 범위 밖이며 별도 Slice로 Deferred한다.

현재 MVP는 통제된 nominal 60 FPS Aim Trainer Recording 한 개에서 하나의 60초 Tracking Run을 분석한다.

MVP가 직접 관측하는 범위:

- Video와 Frame Decode 결과
- Screen Center 기준 Crosshair 위치
- 단일 Target Observation
- Initial Acquisition과 Tracking Maintenance
- On-target / Off-target / Missing
- Direction, Event와 Metric

MVP가 직접 관측하지 않는 범위:

- Mouse 입력 Event
- 실제 손 움직임
- 생리학적 Reaction Time
- 자세, 감도 또는 신체 원인

## Analysis Core Pipeline

기존 분석 Pipeline은 Local Video Path를 입력받은 이후의 Analysis Core 내부 Pipeline이다.

```text
Local Video Path
-> Input Validation
-> Run Boundary Resolution
-> Sequential Frame Processing
-> Target Observation
-> Phase / Tracking State Analysis
-> Event Detection
-> Metric Aggregation
-> Structured Analysis Result
```

## Stage Responsibilities

### Analysis Core Video Input

- 분석할 Recording Video 한 개를 받는다.
- Server가 준비한 Local Video Path를 내부 Input Contract로 사용한다.
- 원본 Recording과 생성될 Run Result의 관계를 유지한다.

### Input Validation

- Video를 처리할 수 있는지 확인한다.
- 현재 MVP가 지원하는 nominal 60 FPS 조건을 확인한다.
- 명확한 Contract 위반은 invalid input으로 구분한다.
- 59.94 FPS 허용 오차와 세부 실패 표현은 Deferred한다.

### Run Boundary Resolution

- Recording 전체와 실제 Run Segment를 구분한다.
- 기본적으로 중앙 Countdown의 `0` 시점을 자동 탐색한다.
- 자동 탐색 실패 또는 불확실 시 Manual Run Start를 요청한다.
- Run Start 이후 Domain 기준 60초를 Run Segment로 사용한다.
- 하나의 Video에서 둘 이상의 독립 Run이 확인되면 현재 MVP 입력으로 지원하지 않는다.

### Sequential Frame Processing

- Sampling하지 않고 Decode 가능한 Frame을 순서대로 처리한다.
- 분석 중 필요한 Frame 순서와 시간 정보를 다음 단계에 제공한다.
- 정상 EOF, Decode 실패와 Segment 부족의 세부 Contract는 구현 Slice에서 결정한다.

### Target Observation

- 각 Frame에서 단일 Target의 관측 가능 여부와 필요한 기하 정보를 생성한다.
- Missing을 Off-target로 변환하지 않는다.
- Detector의 정확한 Algorithm과 Validation 조건은 별도 Slice에서 결정한다.

### Phase / Tracking State Analysis

- Run Start부터 First On-target까지를 Initial Acquisition으로 구분한다.
- First On-target부터 Run End까지를 Tracking Maintenance로 구분한다.
- Tracking Maintenance에서 On-target / Off-target / Missing 상태를 판단한다.
- First On-target가 없거나 판단 불가능한 경우에도 Run-level 결과와 이유를 생성할 수 있어야 한다.

### Event Detection

- 확정된 Operational Definition에 따라 Frame-level 상태 변화에서 Event를 생성한다.
- 확정된 Event는 개별 결과로 보존한다.
- Event는 Run, Phase, Duration, 순서와 시간적 위치 및 필요한 Direction 문맥을 구분할 수 있어야 한다.
- Off-target, Re-entry, Direction Change와 Recovery의 세부 공식은 관련 Slice까지 Deferred한다.

### Metric Aggregation

- Run, Phase, Event와 Direction 결과로 확정된 Metric을 계산한다.
- Metric과 관련 Valid Observation 및 Missing/Coverage를 연결한다.
- 계산 불가 Metric은 unavailable 상태와 사용자 확인 가능한 Domain Reason을 가진다.

### Structured Analysis Result

- 기존 Internal Analysis Output의 canonical structured form이며 새로운 별도 Output 계층이 아니다.
- Internal Analysis Output과 User-facing Summary를 구분한다.
- Internal Output은 Run/Phase/Event/Metric 결과를 보존한다.
- User Summary는 Internal Output에서 파생되며 모든 Frame Detail을 노출하지 않는다.
- Web Response와 TXT Report는 동일한 Structured Analysis Result의 Representation이며 별도의 분석 계산을 수행하지 않는다.

## Runtime and Persistence Boundary

```text
Runtime:
Frame -> Observation -> Event -> Metric

Persistent Internal Output:
Structured Analysis Result = Run + Phase + Event + Metric
```

정상 Output에는 Raw Frame 이미지, 모든 Frame Timestamp와 전체 Frame-level Observation을 필수로 저장하지 않는다. 필요 시 Validation/Debugging 실행에서 선택적 Frame-level Artifact를 생성한다.

## Run Boundary Flow

### Final MVP Workflow

```text
Video Input
-> Automatic Countdown Detection
-> success: Run Start 확정
-> failure or uncertain: Manual Run Start 요청
-> Run Start 확정
-> 60-second Run Segment Processing
```

### Day 04 Initial Implementation Order

첫 Slice에서는 Countdown Detection 문제를 Video Decode와 시간 경계 문제에 섞지 않는다.

또한 Web Upload와 Temporary Local File 생성 경계를 우회하고, 개발용 Local Video Path를 직접 제공하여 Analysis Core부터 검증한다.

```text
Final System:
Web Upload -> Temporary Local File -> Local Path -> Analysis Core

Day 04:
Development Local Path ------------------------> Analysis Core
```

```text
Video Open
-> Metadata Inspection
-> FPS Validation
-> Sequential Frame Decode
-> Human-verified Known Run Start
-> 60-second Run Segment Processing
-> Segment Completeness Check
```

Known Run Start는 개발 단계의 Known Boundary이며 최종 사용자 Workflow 변경이 아니다. 위 Slice가 검증된 뒤 Countdown 관측 특징, Automatic Detection과 Manual Fallback을 추가한다.

## Implementation Slice Rule

각 Slice는 다음 순서를 따른다.

```text
Requirement
-> Local Contract
-> Expected Behavior
-> User Implementation
-> Test / Validation
-> Review
```

함수, Class, Package 구조와 Framework 선택은 실제 Slice의 책임이 분명해진 뒤 결정한다.

## Constraints and Deferred Design

- exact Timestamp 기준과 60초 Frame Boundary
- 59.94 FPS 및 Variable Frame Rate 처리
- Video Open/Decode 실패 세부 Contract
- Target Detection Algorithm과 Threshold
- Direction Boundary와 Noise 처리
- Event와 Recovery Operational Definition
- Output Schema, Database와 UI
- Web Framework, Endpoint, Upload와 Temporary File 처리의 구체적인 Contract
- Web/TXT Representation Schema와 TXT 저장·전달 세부 정책
- Vue Project 구성, Component, Routing, State Management와 API Client 구조
