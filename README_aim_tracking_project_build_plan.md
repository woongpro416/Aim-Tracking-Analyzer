# Vision-based Aim Tracking Analyzer

> **Project Build README — 설계·손코딩 중심 개발용**
>
> 이 문서는 최종 포트폴리오 README가 아니라, 프로젝트를 직접 설계하고 구현하기 위한 **Working README**다.  
> 구현이 끝난 뒤 실제 코드·테스트·결과를 근거로 포트폴리오용 README로 다시 압축한다.

---

## 1. Project Goal

에임 연습 영상에서 단일 Target의 screen-space trajectory를 추출하고, Tracking Error와 방향전환 이후의 회복 지표를 계산하여 **두 Session의 움직임 차이를 검증 가능한 Raw Metric으로 비교**한다.

핵심 기술 흐름:

```text
Video
→ Frame Decode
→ Target Detection
→ Trajectory
→ Time-series Metrics
→ Validation
→ Session Comparison
→ Report
```

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
- Session 간 정량 비교
- Requirement → Contract → Responsibility → Implementation → Test 흐름
- AI-assisted coding을 사용하더라도 핵심 설계와 첫 구현을 직접 수행하는 개발 방식

이번 프로젝트에서는 **“Codex가 만들어 준 프로젝트를 이해하는 것”이 아니라 “내가 설계하고 손코딩한 프로젝트를 Codex에게 검토받는 것”**을 목표로 한다.

---

## 3. Scope

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
- Session A / B Comparison
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
feat: compare tracking sessions
docs: document metric validation and limitations
```

Commit을 “하루 공부 완료”가 아니라 **기능 또는 검증 단위**로 남긴다.

---

# 8. Phase Plan

## Phase 0 — Problem & Contract Setup

### 목표

코딩 전에 프로젝트의 관측 범위와 용어를 확정한다.

### 내가 결정할 것

- Target이 무엇인가?
- Crosshair를 왜 Screen Center로 볼 수 있는가?
- Target Missing Frame은 어떻게 표현할 것인가?
- Pixel Metric의 의미는 무엇인가?
- “Reaction Time” 대신 어떤 관측 가능한 이름을 사용할 것인가?
- Session 비교에서 어떤 조건을 고정할 것인가?

### 완료 Gate

코드 없이 아래 흐름을 설명할 수 있다.

```text
Video
→ Target Position
→ Trajectory
→ Error Metric
→ Event Metric
→ Validation
→ Session Comparison
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

```text
Synthetic Trajectory Test
Manual Frame Annotation
Detection Coverage
Centroid Error
Known-value Metric Test
```

### 완료 Gate

README에서 다음 질문에 답할 수 있어야 한다.

> 이 Metric이 맞게 계산된다는 것을 어떻게 검증했나요?

---

## Phase 6 — Session Comparison & Report

### 목표

같은 Scenario의 Session A / B를 비교한다.

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
- [ ] Session A / B 비교
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

---

# 16. Project Success Statement

이 프로젝트의 성공 기준은 다음 한 문장으로 정의한다.

> **같은 Tracking Scenario의 영상 두 개를 입력했을 때, Target Trajectory를 직접 추출하고 검증된 Raw Metric을 사용해 두 Session의 Tracking 특성이 어떻게 달라졌는지를 설명할 수 있다.**

그리고 개발 과정에 대한 성공 기준은 하나를 더 둔다.

> **핵심 Feature의 Requirement, Contract, Responsibility, 첫 구현, Test Behavior와 주요 Engineering Decision을 내가 직접 작성하고 설명할 수 있다.**
