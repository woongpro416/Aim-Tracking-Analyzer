# Vision-based Aim Tracking Analyzer

> **Project Build README — 설계·손코딩 중심 개발용**
>
> 이 문서는 최종 포트폴리오 README가 아니라, 프로젝트를 직접 설계하고 구현하기 위한 **Working README**다.  
> 구현이 끝난 뒤 실제 코드·테스트·결과를 근거로 포트폴리오용 README로 다시 압축한다.

---

## 1. Project Goal

에임 연습 영상에서 단일 Target의 screen-space trajectory를 추출하고, Tracking Error와 방향전환 이후의 회복 지표를 계산하여 **같은 Scenario에 속한 Run의 움직임 차이를 검증 가능한 Raw Metric으로 비교**한다.

핵심 기술 흐름:

```text
Video
→ Frame Decode
→ Target Detection
→ Trajectory
→ Time-series Metrics
→ Validation
→ Scenario-level Run Comparison
→ Report
```

### Aim Practice 영역 구분

에임 연습은 분석 목적에 따라 크게 Tracking과 Flick Shot으로 구분한다.

```text
Aim Practice
├── Tracking
│   ├── Continuous Target Following
│   ├── Mean Tracking Error
│   ├── RMSE X/Y
│   ├── On-target Ratio
│   ├── Direction Change
│   └── Recovery Latency
│
└── Flick Shot
    ├── Target Acquisition
    ├── Acquisition Time
    ├── Initial Aim Error
    ├── Overshoot / Undershoot
    ├── Correction Count
    ├── Time to Hit
    └── Hit Rate
```

Tracking은 **움직이는 Target을 지속적으로 얼마나 안정적으로 따라가는가**를 분석한다.

Flick Shot은 **새 Target이 나타났을 때 얼마나 빠르고 정확하게 획득하는가**를 분석한다.

두 유형은 분석 목적과 단위가 다르므로 동일한 Metric 체계로 평가하지 않는다. 현재 MVP는 **Tracking Analysis Only**로 제한한다.

### 분석 수준

Tracking 분석은 두 수준으로 구분한다.

1. **Run-level Analysis**
   - 영상 한 개 내부의 Frame, Trajectory, Tracking Metric 분석
   - Error Timeline
   - Direction Change Event
   - Recovery Latency
2. **Scenario-level Run Comparison**
   - 같은 Scenario에 속한 여러 Run의 Metric 비교
   - 서로 다른 Run의 Frame-level Trajectory는 연결하지 않음

현재 MVP에서는 여러 Run을 다시 평균내는 별도 Summary 계층을 만들지 않는다. 필요하면 향후 Scenario-level Trend 또는 평균으로 확장한다.

이 프로젝트의 주인공은 YOLO, FastAPI, LLM 같은 기술의 개수가 아니다.

핵심은 다음 세 가지다.

1. 영상에서 측정 가능한 데이터를 직접 정의한다.
2. 각 처리 단계의 Input / Output / Responsibility를 직접 설계한다.
3. 계산한 Metric이 맞는지 Test와 Synthetic Data로 검증한다.

---

## 2. Portfolio Objective

이 프로젝트를 통해 보여주려는 역량:

- OpenCV 기반 Video Processing
- Target Detection 및 Centroid 추출
- Frame data → Trajectory data 변환
- Time-series Metric 설계
- X/Y Tracking Error 및 RMSE 분석
- Direction-change Event 분석
- Synthetic Data 기반 Metric 검증
- pytest 기반 Unit Test
- 같은 Scenario의 Run 간 정량 비교
- Requirement → Contract → Responsibility → Implementation → Test 흐름
- AI-assisted coding을 사용하더라도 핵심 설계와 첫 구현을 직접 수행하는 개발 방식

이번 프로젝트에서는 **“Codex가 만들어 준 프로젝트를 이해하는 것”이 아니라 “내가 설계하고 손코딩한 프로젝트를 Codex에게 검토받는 것”**을 목표로 한다.

---

## 3. Scope

### Current MVP

**Tracking Analysis Only**

현재 구현 대상은 단일 Target의 연속 궤적과 Tracking Metric이다. Flick Shot은 별도 후속 분석 영역으로 둔다.

### MVP

- MP4 Video Reader
- HSV 기반 단일 Target Detection
- Target Centroid
- Trajectory CSV
- Mean / Median Tracking Error
- RMSE X / Y
- On-target Ratio
- Direction Change Event
- Direction-change Recovery Latency
- Synthetic Data Test
- 일부 Frame Manual Validation
- Trajectory / Error / X-Y Visualization
- Scenario-level Run Comparison
- Metrics JSON
- Markdown Report
- pytest

### Out of Scope

MVP 완료 전에는 다음을 구현하지 않는다.

- YOLO Detector
- ByteTrack / BoT-SORT
- FastAPI
- Web UI
- LLM Coach
- Hand Camera / MediaPipe
- 실제 FPS 전체 경기 분석
- 자동 Sensitivity 추천
- Model Training / Fine-tuning
- Real-time Streaming
- Flick Shot Analyzer 및 Flick 전용 Metric
- 고정 Benchmark 또는 다른 사용자 Population을 이용한 절대 평가
- 근거 없는 “좋은 에임 / 나쁜 에임” 판정

### Data Structure

```text
Aim Type
→ Scenario
→ Run
→ Run Metadata
→ Run Metrics
```

- **Aim Type**: Tracking 또는 Flick Shot과 같은 상위 에임 연습 유형. 현재 MVP는 Tracking만 지원한다.
- **Scenario**: Smooth Tracking, Reactive Tracking, Vertical Tracking과 같이 사용자가 선택하는 에임 연습 카테고리다.
- **Run**: Scenario에 추가되는 독립된 영상 하나다. MVP에서는 `Run 1개 = Video File 1개`다.
- **Run Metadata**: date, resolution, fps, dpi, sensitivity, warmup, notes와 같은 입력·환경 정보다.
- **Run Metrics**: 영상 분석으로 생성된 Mean Error, RMSE, Recovery Latency 등의 측정 결과다.

`Session`과 `Condition`은 현재 데이터 계층으로 사용하지 않는다.

### Run Comparison Policy

같은 Scenario에 속한 Run은 Metadata가 달라도 비교 대상으로 선택할 수 있다. Metadata 차이는 비교를 차단하는 조건이 아니라 결과 해석에 참고하는 정보이며, 차이의 원인을 인과관계로 확정하지 않는다. 다른 Scenario의 Run은 현재 MVP의 직접 비교 대상이 아니다.

비교 상태의 공통 의미는 다음과 같다.

```text
incompatible:
두 Run 모두 해당 Metric은 계산되었지만
척도 또는 전제조건 차이로 직접 비교할 수 없음

warning:
Metric 비교는 가능하지만
정밀도 또는 해석에 주의가 필요함

unavailable:
특정 Run에서 해당 Metric 자체를
신뢰성 있게 계산할 수 없음
```

권장 녹화 환경은 `1920 × 1080`, `nominal 60 FPS`다. 이는 입력 허용 조건이 아니며, 다른 Resolution 또는 FPS의 영상도 입력 자체를 거부하지 않는다.

현재 확정된 Metric 비교 정책:

- Resolution이 다른 Run의 Mean Error, RMSE X, RMSE Y 직접 비교는 `incompatible`
- FPS mismatch만으로 millisecond 단위 Recovery Latency 비교를 차단하지 않으며 temporal precision `warning`으로 취급
- FPS Metadata가 잘못됐거나 Temporal Metric의 전제조건을 충족하지 못하면 해당 Run의 Temporal Metric은 `unavailable`

현재 확정하지 않는 항목:

- Resolution mismatch에서 Median Error, On-target Ratio, Detection Coverage, Vertical / Horizontal RMSE Ratio, Recovery Latency의 직접 비교 가능 여부
- Frame Index / FPS 기반 timestamp와 Decoder timestamp 중 어떤 기준을 사용할지
- Temporal Metric을 `unavailable`로 판단하는 구체적인 FPS 또는 Metadata 조건
- 한쪽 Metric이 `unavailable`이거나 비교 가능한 Metric이 없을 때의 Comparison Result Contract

각 항목은 관련 Metric의 Operational Definition과 Preconditions를 다루는 Phase에서 결정한다. Timestamp 기준은 Phase 1, Comparison 상태 전파는 Phase 6에서 정의한다.

---

## 4. Architecture — Initial Hypothesis

현재 설계의 출발점은 다음과 같다.

```text
Input Video
   ↓
Video Reader
   ↓
Target Detector
   ↓
Trajectory Builder
   ↓
Metrics / Event Analysis
   ↓
Validation
   ↓
Visualization / Report
```

이 구조는 **확정된 정답이 아니다.**

각 Phase를 구현하기 전에 다음을 다시 판단한다.

- 이 책임을 별도 Module로 분리할 이유가 있는가?
- Input / Output Contract는 무엇인가?
- 다음 단계가 현재 Output을 그대로 받을 수 있는가?
- 빈 결과와 잘못된 입력은 어떻게 표현할 것인가?
- Test하기 쉬운 Boundary인가?

구현 과정에서 더 단순한 구조가 적합하다고 판단하면 이유를 기록하고 수정한다.

### Engineering Decision — Tracking Only

```text
Decision:
MVP는 Tracking Analysis만 구현한다.

Reason:
Tracking과 Flick Shot은 목표와 분석 단위가 다르다.
Tracking은 continuous time-series 분석이고,
Flick은 event-based target acquisition 분석에 가깝다.
두 영역을 동시에 구현하면 Metric 정의와 검증 범위가 불필요하게 커진다.

Alternative:
Tracking + Flick을 하나의 MVP에서 동시에 구현

Trade-off:
초기 기능 범위는 좁아지지만,
Tracking Metric의 Operational Definition과 Validation에 더 집중할 수 있다.

Future:
공통 Video / Detection Layer를 재사용하여
Flick Analyzer를 별도 분석 Module로 확장할 수 있다.
```

---

# 5. Project Ownership Rules

## 내가 직접 결정하는 것

Codex가 대신 결정하지 않는다.

- Requirement 해석
- MVP 범위
- Feature의 Input / Output
- Data type / Data shape
- Empty / Invalid Contract
- 파일 분리 여부
- 함수 / Class Responsibility
- Algorithm 선택
- Threshold 또는 Parameter의 의미
- Test Behavior
- Assertion 방향
- 첫 구현 코드
- Git Commit 단위
- 최종 README에서 주장할 범위

## Codex에게 맡길 수 있는 것

- 모호한 Requirement를 질문으로 드러내기
- 개념 설명
- 내가 제안한 설계의 문제점 Review
- 두 설계안의 Trade-off 설명
- API / Library 문법 확인
- Error Message 분석
- Data type 추적
- Edge Case 제안
- 내가 작성한 Test가 무엇을 증명하는지 Review
- 코드 중복 / Responsibility 혼합 Review
- 작은 Hint 제공
- 구현 후 Refactoring 후보 제안

## Codex에게 맡기지 않는 것

내가 명시적으로 요청하기 전에는 다음을 하지 않는다.

- Feature 전체 완성 코드 작성
- 여러 파일을 한 번에 자동 구현
- Repository 전체 Scaffold 완성
- Architecture 정답 선제시
- 함수 Signature 정답 선제시
- pytest Assertion 선작성
- Error 발생 직후 수정 코드 전체 제공
- 새 Library / Framework 자동 추가
- 요구사항에 없는 기능 확장
- Git Commit / Push
- Portfolio README의 성과 과장

---

# 6. Codex Collaboration Protocol

프로젝트에서는 Codex를 다음 역할로 사용한다.

```text
Requirement Reviewer
→ Design Reviewer
→ Concept Tutor
→ Debugging Partner
→ Code Reviewer
→ Test Reviewer
```

**Primary Coder는 나다.**

Codex의 기본 Hint 단계:

```text
1. 문제를 다시 정의하는 질문
2. Input / Output / Data type 힌트
3. Concept / Algorithm 힌트
4. 함수 또는 Library 사용법 수준 힌트
5. 최소 코드 조각
6. 완성 코드
```

5~6단계는 내가 명시적으로 요청할 때만 사용한다.

오류가 발생하면 Codex는 먼저 다음을 확인한다.

```text
현재 변수의 실제 type은?
현재 함수의 Input Contract는?
현재 함수의 Output Contract는?
어느 단계에서 Data Flow가 끊겼는가?
어떤 Responsibility가 섞였는가?
```

바로 정답 코드를 제시하지 않는다.

---

# 7. Feature Development Loop

모든 Feature는 아래 순서로 진행한다.

## Step 1 — Requirement Decomposition

코드 작성 전에 내가 직접 작성한다.

```text
User / Actor:
Problem:
Input:
Expected Output:
Success:
Empty:
Invalid:
Out of Scope:
Unknown / Question:
```

중요:

```text
Requirement Fact
Design Decision
Assumption
```

을 구분한다.

---

## Step 2 — Contract Design

구현 전에 다음을 적는다.

```text
Input type:
Output type:
Data shape:
Empty behavior:
Invalid behavior:
Side effect:
```

예상 결과도 먼저 적는다.

```text
Input을 넣으면
어떤 type / shape / file / value가 나와야 하는가?
```

Codex는 내가 작성한 Contract를 Review만 한다.

---

## Step 3 — Responsibility Design

내가 직접 후보를 정한다.

```text
이 Feature의 책임은 무엇인가?
하지 말아야 할 책임은 무엇인가?
어떤 Module과 연결되는가?
별도 함수/모듈이 필요한가?
```

Module을 나누기 전에 반드시:

> 왜 분리해야 하는가?

에 답한다.

“Architecture가 원래 그렇기 때문”은 이유로 사용하지 않는다.

---

## Step 4 — Test Behavior First

완성 코드를 쓰기 전에 최소한 다음 Behavior를 정의한다.

```text
Happy:
Empty / Missing:
Boundary:
Invalid:
```

모든 Feature가 네 종류를 전부 필요로 하는 것은 아니다.

테스트마다 다음을 적는다.

```text
Input:
Expected:
증명하는 Contract:
막는 Bug:
```

Assertion은 내가 직접 작성한다.

---

## Step 5 — First Implementation

첫 구현은 내가 직접 손코딩한다.

규칙:

- 기존 완성 답안 없음
- Codex에게 Feature 전체 코드 요청 금지
- 문법이 기억나지 않으면 Documentation 또는 작은 Hint 사용 가능
- 한 번에 작은 동작 단위로 실행
- 실행 전 결과를 예측
- 오류가 나면 Error Message를 먼저 읽음

막힌다고 바로 구조를 갈아엎지 않는다.

---

## Step 6 — Codex Review

첫 구현 이후 Codex에게 다음 순서로 Review를 요청한다.

```text
1. Contract가 코드와 일치하는가?
2. Responsibility가 섞였는가?
3. Data type / shape가 일관적인가?
4. Edge Case가 빠졌는가?
5. Test가 Requirement를 실제로 증명하는가?
6. 불필요한 복잡성이 있는가?
7. 지금 Refactoring이 필요한가?
```

Review에서 발견된 문제는 내가 먼저 수정한다.

---

## Step 7 — Verification

다음 중 해당하는 방법으로 검증한다.

```text
pytest
Synthetic Data
Manual Frame Check
CSV Inspection
Graph Inspection
Known-value Calculation
```

“화면상 그럴듯함”만으로 완료 처리하지 않는다.

---

## Step 8 — Decision Log

의미 있는 선택만 짧게 기록한다.

```text
Decision:
Why:
Alternative:
Trade-off:
Evidence:
```

예:

```text
Decision:
MVP Detector로 YOLO 대신 HSV segmentation 사용

Why:
통제된 단색 Target 환경에서 더 단순하고 검증하기 쉬움

Alternative:
YOLO Detector

Trade-off:
환경 변화에는 약하지만 MVP Metric Engine 검증에 집중 가능
```

---

## Step 9 — Commit

하나의 의미 있는 동작 단위가 끝났을 때 Commit한다.

예:

```text
feat: add video frame reader
feat: extract target centroid with hsv mask
feat: build trajectory csv
test: validate rmse with synthetic trajectory
feat: compare tracking runs in a scenario
docs: document metric validation and limitations
```

Commit을 “하루 공부 완료”가 아니라 **기능 또는 검증 단위**로 남긴다.

---

# 8. Phase Plan

## Phase 0 — Problem & Contract Setup

### 목표

코딩 전에 프로젝트의 관측 범위와 용어를 확정한다.

### 내가 결정할 것

- 현재 Aim Type은 무엇이며, 선택한 Tracking Scenario는 무엇인가?
- Target이 무엇인가?
- Crosshair를 왜 Screen Center로 볼 수 있는가?
- Target Missing Frame은 어떻게 표현할 것인가?
- Pixel Metric의 의미는 무엇인가?
- “Reaction Time” 대신 어떤 관측 가능한 이름을 사용할 것인가?
- Run Metadata 차이가 비교 가능성과 결과 해석에 어떤 영향을 주는가?

### 완료 Gate

코드 없이 아래 흐름을 설명할 수 있다.

```text
Video
→ Target Position
→ Trajectory
→ Error Metric
→ Event Metric
→ Validation
→ Scenario-level Run Comparison
```

---

## Phase 1 — Video Reader

### 목표

MP4를 읽고 Frame + Timestamp를 안정적으로 생성한다.

### 구현 전 내가 작성할 것

```text
Input:
Output:
Frame type:
Timestamp type/unit:
End-of-video:
Invalid video:
```

### 완료 Gate

- Sample Video를 열 수 있음
- Frame count / FPS / Resolution을 설명할 수 있음
- Frame과 Timestamp Contract가 명확함
- Invalid Input 동작을 Test 또는 명시적으로 확인

---

## Phase 2 — Target Detection & Trajectory

### 목표

HSV 기반 Target Detection으로 Centroid를 추출하고 Trajectory를 생성한다.

### 설계 질문

- HSV를 왜 사용하는가?
- 어떤 Contour를 Target으로 선택하는가?
- Target 미검출은 어떻게 표현하는가?
- Detector가 Error Metric까지 계산해야 하는가?
- Trajectory Row의 Contract는 무엇인가?

### 완료 Gate

```text
Video Frame
→ Detection
→ Centroid
→ Trajectory Row
→ trajectory.csv
```

흐름을 직접 구현하고 설명할 수 있다.

추가 검증:

- Detection Coverage 측정
- 일부 Frame Manual Check

---

## Phase 3 — Basic Metrics

### 목표

Trajectory로부터 다음을 계산한다.

```text
Mean Error
Median Error
RMSE X
RMSE Y
On-target Ratio
```

### 설계 질문

- Metric 함수는 DataFrame을 받을 것인가, Array를 받을 것인가?
- Missing Detection Frame은 계산에서 어떻게 처리하는가?
- On-target Radius는 어디에서 오는가?
- RMSE X/Y가 각각 무엇을 의미하는가?

### 완료 Gate

Known Synthetic Input에서 계산값을 직접 예측하고 pytest로 확인한다.

---

## Phase 4 — Direction Change & Recovery Latency

### 목표

Screen-space Target Direction Change를 찾고 Tracking Recovery Latency를 계산한다.

### 가장 중요한 규칙

`Reaction Time`이라는 표현을 먼저 사용하지 않는다.

실제 손 움직임 시작을 직접 관찰하지 않기 때문에 이 프로젝트에서 측정하는 것은 **영상상의 Tracking Recovery Latency**다.

### 내가 먼저 정의할 것

```text
Direction Change의 Operational Definition:
T0:
T1:
Recovery 상태:
Noise 처리:
Minimum persistence:
Invalid / insufficient event:
```

### 완료 Gate

Synthetic Trajectory에 알고 있는 방향전환과 Recovery Delay를 넣고 Event Detector가 이를 복원하는지 확인한다.

---

## Phase 5 — Validation

### 목표

“분석기가 숫자를 출력한다”에서 “그 숫자를 신뢰할 근거가 있다”로 이동한다.

### 검증 방법

최소 신뢰 근거를 세 단계로 둔다.

1. **Known-value Unit Test**
   - 사람이 예상값을 계산할 수 있는 작은 Input으로 기본 Metric 공식 검증
2. **Synthetic Trajectory Validation**
   - 방향전환 시점과 Recovery Delay를 미리 알고 있는 데이터에서 Known Value 복원 정도 확인
3. **Manual Frame Validation**
   - 실제 영상 일부 Frame의 Target 위치를 수동 확인
   - Detection Coverage와 Centroid Error 검증

세부 허용 오차, 수동 검증 Frame 수와 선택 방법은 구현 및 실험 과정에서 별도로 결정한다.

### 완료 Gate

README에서 다음 질문에 답할 수 있어야 한다.

> 이 Metric이 맞게 계산된다는 것을 어떻게 검증했나요?

숫자가 출력되는 것만으로는 완료하지 않는다. `Known-value Test + Synthetic Validation + 실제 Frame 검증`이 있어야 최소한 신뢰 가능한 Metric으로 판단한다.

---

## Phase 6 — Scenario-level Run Comparison & Report

### 목표

같은 Scenario에 속한 독립된 Run의 Metric을 비교한다. 서로 다른 Run의 Frame-level Trajectory를 연결하거나 별도 Summary 평균을 만들지 않는다.

### 비교 Metric

```text
Mean Error
RMSE X/Y
On-target Ratio
Recovery Latency
Detection Coverage
```

### 중요한 원칙

```text
Measurement ≠ Diagnosis
```

예:

```text
“Vertical RMSE가 18% 감소했다.”
→ 측정

“팔에 힘을 덜 줘서 좋아졌다.”
→ 현재 데이터만으로 확정할 수 없는 해석
```

현재 MVP는 절대적인 “좋은 에임 / 나쁜 에임” 기준이나 다른 사용자 Population과의 비교를 만들지 않는다. 다음과 같이 같은 Scenario에 속한 Run과 Raw Metric에 근거한 상대 표현을 사용한다.

```text
Run A 대비 감소 / 증가
Horizontal 대비 Vertical Error가 큼
이전 Run보다 감소 / 증가함
특정 Metric이 상대적으로 커짐
```

근거 없이 “평균 이상”, “프로 수준”, “감도가 너무 높다”, “반응속도가 느리다”와 같은 표현을 사용하지 않는다.

### 완료 Gate

두 영상의 차이를 Raw Metric과 Graph로 설명할 수 있다.

---

## Phase 7 — Portfolio Closing

### 목표

새 기능을 추가하지 않고 프로젝트를 증거 중심으로 정리한다.

최종 확인:

```text
Architecture
Core Implementation
Engineering Decisions
Tests
Synthetic Validation
Manual Validation
Demo Output
Limitations
Future Extension
```

MVP가 완성되면 YOLO / FastAPI / LLM을 추가하지 않아도 종료 가능하다.

### Future Extension — Flick Shot Analyzer

Flick Shot은 MVP 완료 후 별도 분석 Module로 설계한다.

공통으로 재사용 가능한 영역:

- Video Reader
- Timestamp
- Coordinate System
- Target Detection 일부
- Run Metadata
- Validation Infrastructure
- Visualization Base

Tracking 전용 분석:

- Continuous Trajectory
- Mean Tracking Error
- RMSE X/Y
- On-target Ratio
- Direction-change Recovery Latency

Flick 전용 분석 후보:

- Target Appearance Event
- Target Acquisition Time
- Initial Aim Error
- Overshoot / Undershoot
- Correction Count
- Time to Hit
- Hit Rate

Flick Metric의 세부 Operational Definition은 현재 확정하지 않고 후속 확장 시 별도로 설계한다.

### Future Extension — AI Run Pattern Analysis

AI Run Pattern Analysis는 MVP가 검증된 뒤 추가할 수 있는 선택적 Machine Learning 분석 계층이다. AI Model은 원본 영상이 아니라 Known-value Test, Synthetic Validation, Manual Validation을 거친 **Validated Run Metrics**를 입력으로 사용한다.

```text
Video
→ Computer Vision
→ Trajectory
→ Metric Calculation
→ Validation
→ Validated Run Metrics
→ AI Run Pattern Analysis
```

첫 번째 후보는 같은 Scenario의 Run Metrics를 Feature Vector로 변환하고 K-Means Clustering으로 유사한 Tracking Run Pattern을 탐색하는 것이다. Optional 후보로 Isolation Forest를 이용해 새로운 Run이 기존 개인 Run Pattern과 얼마나 다른지 확인하는 Anomaly Detection을 고려할 수 있다.

AI 결과는 원인을 진단하지 않고 검증된 Feature Pattern을 탐색하는 데만 사용한다. `Measurement ≠ Diagnosis` 원칙을 유지하며, Metadata 차이로부터 감도, 반응속도, 자세 등의 원인을 단정하지 않는다.

다른 Scenario의 Run을 하나의 Dataset으로 합치는 정책은 현재 확정하지 않는다.

다음 항목은 실제 Run 데이터가 쌓이고 MVP가 검증된 뒤 별도 Requirement / Contract 단계에서 결정한다.

- Cluster 개수
- Feature Scaling 방식
- 최종 Feature 목록
- 최소 Run 개수와 Dataset 크기
- Isolation Forest 설정값
- Cluster 이름과 의미
- AI 성능 평가 기준
- Scenario 간 통합 여부
- Raw Trajectory 학습
- Supervised Learning 및 Deep Learning 모델

---

# 9. Design Questions Checklist

새 Feature마다 전부 사용할 필요는 없지만, 구현 전에 필요한 질문을 선택한다.

## Requirement

- 누가 사용하는가?
- 무엇을 해결하려는가?
- 요구사항에서 확정된 사실은 무엇인가?
- 내가 결정한 것은 무엇인가?
- 임시 가정은 무엇인가?
- 범위 밖은 무엇인가?

## Data

- 한 건의 자료형은?
- 여러 건의 자료형은?
- Empty는?
- Missing은?
- 단위는?
- 좌표계는?
- Timestamp 기준은?

## Responsibility

- 이 함수가 반드시 해야 하는 일은?
- 절대 하면 안 되는 일은?
- 앞 단계 Output은?
- 다음 단계 Input은?

## Algorithm

- 가장 단순한 방법은?
- 왜 이 방법을 선택했는가?
- 대안은?
- 어떤 조건에서 실패하는가?

## Test

- 정상 결과는?
- Boundary는?
- 잘못된 입력은?
- 정답을 알고 있는 Synthetic Input을 만들 수 있는가?
- 이 Test가 실제로 막는 Bug는?

---

# 10. Design Ownership Evidence

포트폴리오에서 “직접 설계했다”고 말하려면 코드량보다 다음 증거가 중요하다.

프로젝트 종료 시 최소 5개의 설계 판단을 내가 직접 설명할 수 있어야 한다.

후보:

1. 왜 MVP Detector로 HSV를 선택했는가?
2. 왜 Crosshair를 별도 Detection하지 않고 Screen Center로 두었는가?
3. 왜 Frame Detection과 Metric 계산을 분리했는가?
4. Target Missing Frame을 어떤 Contract로 표현했는가?
5. 왜 X/Y RMSE를 분리했는가?
6. 왜 `Reaction Time` 대신 `Recovery Latency`로 정의했는가?
7. Direction Change Noise를 어떤 기준으로 제거했는가?
8. 왜 Synthetic Test가 필요한가?
9. 왜 Measurement와 Diagnosis를 분리했는가?
10. 왜 YOLO / FastAPI / LLM을 MVP에서 제외했는가?
11. 왜 Tracking과 Flick Shot을 분리했는가?

각 판단은 다음 형식으로 설명 가능해야 한다.

```text
Problem
→ Options
→ My Decision
→ Reason
→ Trade-off
→ Evidence
```

---

# 11. Working README Update Rule

개발 중에는 README를 결과보다 앞서 과장하지 않는다.

Feature 완료 후에만 다음을 갱신한다.

```text
Implemented
Tested
Measured Result
Known Limitation
Next Phase
```

계획은 `Roadmap`에 적고 실제 구현과 구분한다.

```text
Implemented
≠
Planned
```

---

# 12. Final Portfolio README 방향

프로젝트 완료 후 이 Working README를 그대로 공개용 README로 사용하지 않는다.

최종 README는 채용자가 2~3분 안에 읽을 수 있도록 아래 정도로 압축한다.

```text
# Vision-based Aim Tracking Analyzer

## Overview
## Problem
## Architecture
## Core Implementation
## Validation
## Results
## Engineering Decisions
## Limitations
## How to Run
```

Day별 개발일지나 긴 Codex 대화는 최종 README의 주인공이 아니다.

최종 README의 주인공은:

```text
문제
→ 내가 선택한 설계
→ 직접 구현한 Pipeline
→ 검증 방법
→ 실제 결과
→ 한계
```

다.

---

# 13. Current Status Template

프로젝트를 시작하면 아래를 계속 갱신한다.

```text
Current Phase:
Current Feature:

Requirement:
Input:
Output:
Responsibility:
Test Behavior:

Implemented:
Tested:
Blocked:
Decision Needed:
Next:
```

---

# 14. Codex 시작 프롬프트

새 Codex 세션의 첫 메시지로 아래 규칙을 전달한다.

```text
이 프로젝트는 포트폴리오용 Vision-based Aim Tracking Analyzer입니다.

중요한 목표는 프로젝트 완성 자체보다
제가 Requirement → Contract → Responsibility → Implementation → Test를
직접 경험하고 코드 소유권을 갖는 것입니다.

당신은 Primary Coder가 아니라
Requirement Reviewer / Design Reviewer / Concept Tutor /
Debugging Partner / Code Reviewer / Test Reviewer 역할을 맡아주세요.

규칙:

1. 기능 전체의 완성 코드를 먼저 작성하지 마세요.
2. 제가 구현하기 전에 함수 signature, 파일 구조, 정답 architecture를 먼저 확정하지 마세요.
3. 새 Feature마다 먼저 제가 Requirement Fact / Design Decision / Assumption,
   Input / Output / Empty / Invalid, Responsibility를 작성하게 해주세요.
4. 제가 설계안을 작성하면 모순, 누락, 과도한 복잡성만 Review해주세요.
5. 첫 구현은 제가 직접 손코딩합니다.
6. 오류가 나면 수정 코드를 바로 주지 말고
   현재 자료형, Input/Output Contract, Data Flow가 끊긴 위치부터 질문해주세요.
7. Hint는
   질문 → 개념 → Contract → Library/API → 최소 코드 조각 → 완성 코드
   순서로 단계적으로 제공해주세요.
8. Test Behavior와 assertion은 제가 먼저 작성합니다.
9. 구현 후에는 Contract / Responsibility / Data Type / Edge Case /
   Test Coverage / 불필요한 복잡성을 Review해주세요.
10. 요구사항에 없는 YOLO, FastAPI, LLM, UI 등의 기능을 자동으로 확장하지 마세요.
11. 제가 명시적으로 요청하기 전에는 Git commit/push를 실행하지 마세요.
12. 매 Phase 종료 시 제가 내린 설계 판단 1~2개를
    Problem → Options → Decision → Reason → Trade-off → Evidence 형식으로 정리하게 해주세요.

현재는 한 번에 한 Feature만 진행합니다.
다음 TODO를 여러 개 한꺼번에 구현하지 마세요.
```

---

# 15. Definition of Done

포트폴리오용 MVP는 다음 조건을 만족하면 종료한다.

- [ ] Video → Target Centroid → Trajectory Pipeline 동작
- [ ] Mean / Median Error 계산
- [ ] RMSE X / Y 계산
- [ ] On-target Ratio 계산
- [ ] Direction Change Event 구현
- [ ] Recovery Latency Operational Definition 문서화
- [ ] Synthetic Test로 주요 Metric 검증
- [ ] 일부 Frame Manual Validation
- [ ] 같은 Scenario의 Run 비교
- [ ] 핵심 Graph 생성
- [ ] pytest 통과
- [ ] 설계 판단 최소 5개 설명 가능
- [ ] Known Limitation 문서화
- [ ] 최종 포트폴리오 README 작성

다음 항목은 MVP 완료 조건이 아니다.

- [ ] YOLO
- [ ] FastAPI
- [ ] Web UI
- [ ] LLM
- [ ] Hand Camera
- [ ] Real-time Processing
- [ ] Flick Shot Analyzer

---

# 16. Project Success Statement

이 프로젝트의 성공 기준은 다음 한 문장으로 정의한다.

> **같은 Tracking Scenario에 속한 독립된 Run 영상을 분석했을 때, 각 Run의 Target Trajectory를 직접 추출하고 검증된 Raw Metric을 사용해 Run 간 Tracking 특성이 어떻게 달라졌는지를 설명할 수 있다.**

Metric 신뢰의 최소 조건은 `Known-value Test + Synthetic Validation + 실제 Frame 검증`을 모두 거치는 것이다. 결과 숫자가 출력되는 것만으로는 분석 성공으로 판단하지 않는다.

그리고 개발 과정에 대한 성공 기준은 하나를 더 둔다.

> **핵심 Feature의 Requirement, Contract, Responsibility, 첫 구현, Test Behavior와 주요 Engineering Decision을 내가 직접 작성하고 설명할 수 있다.**
