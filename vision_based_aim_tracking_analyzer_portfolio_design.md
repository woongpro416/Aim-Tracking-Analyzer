# Vision 기반 Aim Tracking Analyzer 포트폴리오 미니 프로젝트 설계서

## 0. 문서 목적

이 문서는 **Aim Lab, Kovaak's 또는 유사 에임 연습 프로그램의 녹화 영상을 입력하면, 단일 타깃의 화면상 궤적을 추출하고 조준 오차·축별 RMSE·On-target Ratio·방향전환 후 회복 지연을 정량화하여 비교 리포트를 생성하는 미니 프로젝트**의 설계서다.

이 프로젝트의 목적은 게임 전체 상황 판단 AI를 만드는 것이 아니다.  
**통제된 영상 환경에서 Detection → Tracking → Time-series Metrics → Validation → Report 흐름을 끝까지 구현하는 것**에 집중한다.

포트폴리오 관점의 핵심 질문은 다음과 같다.

> 영상에서 타깃 위치를 안정적으로 검출할 수 있는가?  
> 프레임별 Detection을 시간축 Trajectory로 변환할 수 있는가?  
> 조준 오차를 X/Y 축과 시간축 관점에서 정량화할 수 있는가?  
> 방향전환 이후 Tracking이 다시 안정되는 데 얼마나 걸리는가?  
> 두 세션의 차이를 Raw Metric으로 재현 가능하게 비교할 수 있는가?

---

# 1. 프로젝트 한 줄 정의

**에임 연습 영상을 입력받아 타깃 궤적을 추출하고, Tracking Error와 방향전환 회복 지표를 계산하여 두 세션의 움직임 차이를 정량적으로 비교하는 Vision 기반 Video Motion Analyzer.**

---

# 2. 프로젝트 목표

## 2.1 MVP 목표

영상 1개를 입력하면 다음 결과를 생성한다.

1. MP4 영상 프레임 Decode
2. 단일 타깃 중심 좌표 추출
3. 화면 중심 기준 조준 오차 계산
4. 수평/수직 RMSE 계산
5. On-target Ratio 계산
6. 방향전환 Event 검출
7. 방향전환 후 Tracking Recovery Latency 계산
8. Trajectory CSV 저장
9. Metrics JSON 저장
10. 분석 그래프 생성
11. Markdown 요약 리포트 생성

MVP의 핵심은 **Metric 수를 많이 만드는 것보다 각 Metric을 검증 가능하게 구현하는 것**이다.

## 2.2 최종 출력 예시

```text
[Tracking Summary]

Mean Tracking Error: 22.8 px
RMSE X: 17.4 px
RMSE Y: 29.1 px
Vertical / Horizontal RMSE Ratio: 1.67
On-target Ratio: 69.2%

Direction-change Recovery Latency
- Horizontal: 108 ms
- Vertical: 156 ms

Detection Coverage: 98.1%

[Comparison]
Session B는 Session A보다
- Mean Error 11.3% 감소
- Vertical RMSE 18.7% 감소
- Vertical Recovery Latency 24 ms 감소
```

---

# 3. 프로젝트 범위

## 포함

- 에임 연습 프로그램 녹화 영상
- 단일 타깃 Tracking
- 화면 중앙 고정 Crosshair 가정
- OpenCV 기반 Color Segmentation
- 타깃 중심 좌표 추출
- Tracking Trajectory 생성
- X/Y Error 분석
- Mean Error / RMSE X/Y
- On-target Ratio
- 방향전환 Event Detection
- Tracking Recovery Latency
- 세션 2개 비교
- CSV / JSON / PNG / Markdown 결과 생성
- pytest Unit Test
- Synthetic Trajectory Test
- 일부 Frame 수동 검증

## MVP에서 제외

- 실제 FPS 경기 전체 분석
- 다수 적 객체 ID Tracking
- YOLO 기반 Detector
- ByteTrack / BoT-SORT
- FastAPI / Web UI
- LLM 코칭
- 실제 마우스 손 움직임 추적
- MediaPipe Pose / Hands
- 감도 자동 추천
- 강화학습
- 모델 직접 학습
- 실시간 Streaming 분석

---

# 4. 핵심 아이디어

FPS Aim Trainer의 Crosshair가 화면 중앙에 고정되어 있다고 가정한다.

따라서 MVP에서는 Crosshair를 별도로 검출하지 않고 화면 중심을 기준점으로 사용한다.

```python
screen_center_x = frame_width / 2
screen_center_y = frame_height / 2

error_x = target_x - screen_center_x
error_y = target_y - screen_center_y
error_distance = (error_x**2 + error_y**2) ** 0.5
```

전체 흐름:

```text
Video
  ↓
Frame Decode
  ↓
Target Detection
  ↓
Target Center (x, y)
  ↓
Trajectory
  ↓
Screen Center와 비교
  ↓
Time-series Metrics
  ↓
Validation
  ↓
Comparison Report
```

---

# 5. 기술 스택

## 필수

- Python 3.11+
- OpenCV
- NumPy
- Pandas
- Matplotlib
- pytest

## 권장

- SciPy: smoothing / signal processing
- Pydantic: Metrics JSON schema validation
- argparse: CLI input

## MVP 이후 선택

- YOLO: Color Segmentation이 실제 영상에서 불안정할 때
- FastAPI: 분석 Engine을 API로 노출할 때
- Streamlit: 결과 시각화 UI가 필요할 때
- LLM API: Metrics 기반 자연어 요약을 확장할 때

---

# 6. 권장 개발 전략

처음부터 AI Model을 추가하지 않는다.

```text
V0: OpenCV Detection + Trajectory + Basic Metrics
V1: Direction-change Event + Recovery Latency + Validation
V2: Session Comparison + Portfolio Report
V3: Optional YOLO / API / LLM Extension
```

MVP 완료 전에는 V3 기능을 시작하지 않는다.

---

# 7. 시스템 아키텍처

```text
Input MP4
   ↓
Video Reader
(OpenCV)
   ↓
Target Detector
(HSV / Mask / Contour)
   ↓
Trajectory Builder
(frame, timestamp, x, y)
   ↓
Metrics Engine
(Error / RMSE / On-target / Direction Change / Recovery Latency)
   ↓
Validator
(Synthetic Data / Manual Frame Check)
   ↓
Visualizer
(Trajectory / Error Timeline / X-Y Comparison)
   ↓
Report Generator
(CSV / JSON / PNG / Markdown)
```

각 계층의 책임을 섞지 않는다.

---

# 8. 프로젝트 폴더 구조

```text
aim-video-analyzer/
│
├── README.md
├── requirements.txt
│
├── data/
│   ├── raw/
│   │   ├── session_a.mp4
│   │   └── session_b.mp4
│   └── synthetic/
│
├── src/
│   ├── __init__.py
│   ├── video_reader.py
│   ├── target_detector.py
│   ├── trajectory.py
│   ├── metrics.py
│   ├── events.py
│   ├── visualizer.py
│   ├── report.py
│   └── schemas.py
│
├── outputs/
│   └── latest/
│       ├── trajectory.csv
│       ├── metrics.json
│       ├── trajectory.png
│       ├── tracking_error.png
│       ├── xy_error.png
│       └── report.md
│
├── tests/
│   ├── test_detector.py
│   ├── test_metrics.py
│   ├── test_events.py
│   └── test_synthetic.py
│
└── main.py
```

---

# 9. Video Reader 계약

입력:

```text
sample.mp4
```

프레임 출력 Contract:

```python
{
    "frame_index": 120,
    "timestamp_ms": 2000.0,
    "frame": ndarray
}
```

필수 메타데이터:

```text
FPS
WIDTH
HEIGHT
TOTAL_FRAMES
DURATION_MS
```

Empty / Invalid Contract:

```text
영상 파일을 열 수 없음
→ 명시적 오류

프레임 Decode 실패
→ 해당 Frame 기록 또는 명시적 처리
```

---

# 10. Target Detection

## MVP: Color Segmentation

실험 환경의 Target 색상을 고정한다.

```text
Target Color = red 또는 특정 단색
Background = dark / neutral
Single Target
```

처리 흐름:

```text
frame
→ BGR to HSV
→ cv2.inRange()
→ morphology
→ contour detection
→ contour validation
→ centroid
```

핵심 코드 개념:

```python
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, lower_color, upper_color)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
```

Centroid:

```python
M = cv2.moments(contour)

if M["m00"] != 0:
    cx = M["m10"] / M["m00"]
    cy = M["m01"] / M["m00"]
```

---

# 11. Detection Validation

잘못된 contour를 제거하기 위해 최소한 다음 조건을 사용한다.

- min_area
- max_area
- aspect_ratio
- circularity
- ROI

Circularity:

```text
4πA / P²
```

원형에 가까울수록 1에 가까워진다.

MVP에서는 Detection 규칙을 복잡하게 늘리기보다 **검출률과 중심좌표 오차를 측정하면서 필요한 조건만 추가**한다.

---

# 12. Tracking Data Schema

매 Frame 다음 데이터를 저장한다.

```csv
frame,timestamp_ms,target_x,target_y,error_x,error_y,error_distance,target_found
0,0,1030,541,70,1,70.01,true
1,16,1028,541,68,1,68.01,true
2,33,1023,540,63,0,63.00,true
```

Target이 검출되지 않은 Frame도 삭제하지 않고 `target_found=false`로 기록한다.

이 데이터가 이후 Metrics Engine의 Input Contract가 된다.

---

# 13. 핵심 Metrics

## 13.1 Mean / Median Tracking Error

```text
Mean Error = mean(error_distance)
Median Error = median(error_distance)
```

낮을수록 Crosshair 중심과 Target 중심의 평균 거리가 작다는 의미다.

## 13.2 RMSE

```text
RMSE_X = sqrt(mean(error_x²))
RMSE_Y = sqrt(mean(error_y²))
```

축별 성능 비교:

```text
VerticalHorizontalRatio = RMSE_Y / RMSE_X
```

예:

```text
RMSE_X = 18
RMSE_Y = 30
Ratio = 1.67
```

이 경우 수직 오차가 수평보다 상대적으로 크다고 설명할 수 있다.

---

# 14. On-Target Ratio

Target의 반경을 검출된 contour 또는 설정값으로 추정한다.

```text
error_distance <= target_radius
```

이면 On-target Frame으로 정의한다.

```text
OnTargetRatio = on_target_frames / valid_detection_frames
```

Target Detection 실패 Frame은 분모 처리 정책을 명확하게 문서화한다.

---

# 15. Target Velocity

Target Screen Trajectory 기준 속도를 계산한다.

```python
vx = (x[t] - x[t - 1]) / dt
vy = (y[t] - y[t - 1]) / dt
```

주의:

영상에서 관측되는 Target Screen Velocity는 순수 Target 이동 속도와 Player Camera Movement가 합쳐진 결과다.

따라서 본 프로젝트에서는 이를 **screen-space target velocity**로 정의한다.

Noise가 크면 Moving Average 또는 Savitzky-Golay Filter를 적용한다.

---

# 16. Direction Change Detection

Horizontal Direction Change:

```text
sign(vx[t-1]) != sign(vx[t])
```

Vertical Direction Change:

```text
sign(vy[t-1]) != sign(vy[t])
```

Noise로 인한 잘못된 Event를 줄이기 위해:

```text
minimum velocity
minimum persistence frames
minimum displacement
```

조건을 사용한다.

예:

```text
방향 부호가 바뀐 뒤 최소 3 frame 이상 유지
```

---

# 17. Direction-change Recovery Latency

기존 설계의 `Reaction Time`을 그대로 사람의 순수 반응시간이라고 해석하지 않는다.

영상 하나만으로는 실제 손 움직임 시작 시점을 직접 관측할 수 없기 때문이다.

따라서 MVP Metric 이름은:

```text
Direction-change Recovery Latency
```

로 정의한다.

```text
T0 = Target screen trajectory의 유효한 방향전환 Event 시점

T1 = 방향전환 이후 Tracking Error가
     다시 감소 방향으로 전환되고
     일정 Frame 이상 유지되기 시작한 시점

Recovery Latency = T1 - T0
```

T1 Operational Definition 예:

```text
abs(error_distance)의 1차 변화량이 음수
AND
최소 k frame 연속 유지
```

이 Metric은 실제 생리학적 Reaction Time이 아니라 **화면상의 Tracking 회복 지연**을 측정한다.

---

# 18. Lag / Lead 분석

MVP에서는 Lag / Lead를 핵심 완료 조건에 넣지 않는다.

이유:

- 화면 중심 Crosshair 환경에서는 screen-space Target movement와 Player Camera movement가 결합되어 있음
- 방향 부호 정의를 잘못하면 의미가 쉽게 뒤집힘
- MVP 핵심 Metric만으로도 충분한 포트폴리오 가치가 있음

향후 확장 시 Operational Definition을 먼저 작성한 뒤 추가한다.

---

# 19. Overshoot / Undershoot

MVP Stretch Goal로 둔다.

Overshoot 후보 정의:

```text
Target 중심에 접근
→ error 축 부호가 바뀜
→ 일정 크기 이상 반대편으로 넘어감
→ 다시 재보정
```

후보 지표:

```text
Overshoot Count
Overshoot Rate
Recovery Distance
```

중요:

Overshoot가 발생했다고 해서 감도가 높거나 팔에 힘이 들어갔다고 자동 진단하지 않는다.

---

# 20. Smoothness / Jerk

MVP 필수 범위에서 제외하고 확장 지표로 둔다.

```text
position
→ velocity
→ acceleration
→ jerk
```

미분을 반복할수록 Noise가 크게 증폭되므로 충분한 Smoothing과 검증 없이 절대 점수화하지 않는다.

향후 사용 시:

```text
Mean Absolute Jerk
P90 Jerk
```

정도를 **개인 세션 간 비교 지표**로만 사용한다.

---

# 21. 방향별 분석

MVP:

```text
Horizontal
Vertical
```

두 축만 비교한다.

확장:

```text
Diagonal
Curve
Clockwise / Counter-clockwise
```

복잡한 방향 분류는 MVP 이후로 보류한다.

---

# 22. 첫 사용자 실험

포트폴리오 MVP에서는 실험을 단순하게 유지한다.

## Session A

기본 조건에서 동일 Tracking Scenario 5회.

## Session B

한 가지 조건만 변경한 뒤 동일 Tracking Scenario 5회.

예:

```text
Warm-up 없음
vs
Figure-8 Warm-up 2분
```

비교:

```text
Mean Error
RMSE X
RMSE Y
On-target Ratio
Horizontal Recovery Latency
Vertical Recovery Latency
```

한 번의 Run 차이보다 여러 Run의 평균을 비교한다.

---

# 23. 감도 비교 실험

첫 포트폴리오 완료 조건에서는 제외한다.

감도 비교는 프로젝트가 안정된 뒤 확장 실험으로 진행할 수 있다.

진행 시 다음 원칙을 지킨다.

```text
한 번에 하나의 변수만 변경
각 조건 반복 측정
순서 효과 최소화
Session Metadata 저장
```

목표는 “최적 감도 자동 추천”이 아니라 **조건 변화에 따라 Raw Metric이 어떻게 변했는지 비교**하는 것이다.

---

# 24. 분석 단계

MVP에서는 LLM을 사용하지 않는다.

```text
Video
↓
OpenCV
↓
Trajectory
↓
Metrics Engine
↓
Rule-based Summary
↓
Markdown Report
```

측정값 자체가 프로젝트의 핵심 산출물이다.

LLM이 없어도 프로젝트는 완전하게 동작해야 한다.

---

# 25. Metrics JSON Schema 예시

```json
{
  "mean_error_px": 22.8,
  "median_error_px": 18.4,
  "rmse_x": 17.4,
  "rmse_y": 29.1,
  "vertical_horizontal_ratio": 1.67,
  "on_target_ratio": 0.692,
  "detection_coverage": 0.981,
  "recovery_latency_ms": {
    "horizontal_mean": 108.0,
    "vertical_mean": 156.0
  }
}
```

실제 구현에서 확정되지 않은 Field는 미리 추가하지 않는다.

---

# 26. Rule-based Summary

복잡한 코칭 대신 측정값에 근거한 짧은 Summary만 생성한다.

예:

```python
if rmse_y > rmse_x * 1.3:
    summary.append(
        "수직 Tracking Error가 수평보다 상대적으로 크게 나타났습니다."
    )

if vertical_latency > horizontal_latency + 30:
    summary.append(
        "수직 방향전환 이후 Tracking 회복 지연이 더 길게 나타났습니다."
    )
```

원인을 추측하지 않는다.

---

# 27. LLM 확장 원칙

MVP에서 구현하지 않는다.

향후 LLM을 추가하더라도 입력은 원본 영상이 아니라 검증된 `metrics.json`으로 제한한다.

```text
Video
→ CV / Metrics
→ Metrics JSON
→ Optional LLM
→ Natural Language Explanation
```

LLM은 측정되지 않은 원인을 사실처럼 생성해서는 안 된다.

---

# 28. 시각화

MVP 필수 그래프는 3개로 제한한다.

## Tracking Error Timeline

```text
X = time
Y = error_distance
```

방향전환 Event를 세로선으로 표시할 수 있다.

## X / Y Error Comparison

```text
RMSE X
vs
RMSE Y
```

또는 두 축의 Error Distribution을 비교한다.

## Target Trajectory

화면 좌표계에:

```text
Target Trajectory
Screen Center
```

를 함께 표시한다.

선택:

```text
Session A vs Session B comparison chart
```

---

# 29. Session Metadata

각 분석 실행은 영상과 함께 최소한 다음 정보를 저장한다.

```json
{
  "session_id": "session_a",
  "scenario": "smooth_tracking",
  "resolution": "1920x1080",
  "recording_fps": 60,
  "dpi": 800,
  "sensitivity": 5.5,
  "warmup": "none",
  "notes": ""
}
```

세션 비교에서 바뀐 조건을 추적할 수 있어야 한다.

---

# 30. 권장 녹화 환경

가능하면 다음 조건을 고정한다.

```text
Resolution: fixed
Recording FPS: 60 이상
Scenario: fixed
Target Color: fixed
Background: fixed
DPI: recorded
Sensitivity: recorded
```

실험마다 여러 변수를 동시에 바꾸지 않는다.

---

# 31. 향후 확장: YOLO Detector

Color Segmentation으로 충분한 Detection 품질을 얻지 못할 경우에만 고려한다.

확장 흐름:

```text
HSV Detector
↓
Detector Interface 유지
↓
YOLO Detector로 교체
```

이때 Metrics Engine과 Report Generator는 수정하지 않는 구조를 목표로 한다.

이 확장은 **Detector Boundary 설계가 실제로 분리되어 있음을 보여주는 추가 과제**로 사용할 수 있다.

---

# 32. 향후 확장: API / UI / LLM

MVP 이후 필요할 때만 추가한다.

```text
FastAPI
→ 분석 요청 API

Streamlit
→ 결과 확인 UI

LLM
→ Metrics 기반 자연어 설명
```

포트폴리오 첫 버전에서는 분석 Engine의 완성도를 우선한다.

---

# 33. 개발 단계

## Phase 1 — Video → Target Coordinates

목표:

```text
MP4를 읽고 Target 중심좌표를 trajectory.csv로 저장
```

완료 기준:

```text
유효 Frame Detection Coverage >= 95%
```

## Phase 2 — Basic Metrics

```text
Mean Error
Median Error
RMSE X/Y
On-target Ratio
```

## Phase 3 — Direction Analysis

```text
Screen-space Velocity
Direction Change Event
Recovery Latency
```

## Phase 4 — Validation

```text
Synthetic Trajectory
Known Noise
Known Direction Change
Known Recovery Delay
```

## Phase 5 — Visualization

```text
Trajectory
Error Timeline
X/Y Comparison
```

## Phase 6 — Session Comparison

```text
Session A
vs
Session B
```

## Phase 7 — Portfolio Closing

```text
README
Architecture
Test Evidence
Limitations
Demo Output
```

---

# 34. 첫 Milestone

다음 명령 하나로:

```bash
python main.py --video data/raw/session_a.mp4
```

아래를 생성한다.

```text
outputs/latest/
├── trajectory.csv
├── metrics.json
├── trajectory.png
├── tracking_error.png
├── xy_error.png
└── report.md
```

이 단계까지 완료하면 프로젝트의 핵심 Pipeline이 살아 있다.

---

# 35. MVP 완료 기준

프로그램이 다음 질문에 답할 수 있으면 MVP 성공이다.

1. 평균 Tracking Error는 얼마인가?
2. X/Y 중 어느 축의 오차가 더 큰가?
3. Target을 놓치지 않고 몇 %의 Frame에서 검출했는가?
4. Crosshair가 Target 범위 안에 있었던 비율은 얼마인가?
5. 방향전환 이후 Tracking Error가 다시 감소하기까지 얼마나 걸렸는가?
6. 두 Session의 Raw Metric은 어떻게 달라졌는가?

---

# 36. 테스트 전략

## Unit Test

### Target Detector

Synthetic 또는 고정 Test Image에서 Target Centroid를 검증한다.

### Metrics

인공 좌표를 사용해:

```text
Mean Error
RMSE X
RMSE Y
On-target Ratio
```

계산 결과를 검증한다.

### Event Detector

알고 있는 방향전환 시점을 가진 Trajectory를 넣어 Event Index를 검증한다.

## Synthetic Data Test

실제 영상 전에 정답을 알고 있는 Trajectory를 만든다.

예:

```text
sin wave
triangle wave
figure-8
```

의도적으로 추가:

```text
noise
missing frames
direction change
known recovery delay
```

분석기가 알려진 값을 어느 정도 복원하는지 확인한다.

이 테스트는 포트폴리오 핵심 증거로 남긴다.

---

# 37. Detection 정확도 검증

자동 Detector 결과 일부를 수동 Annotation과 비교한다.

권장:

```text
100 frames manual check
```

측정:

```text
Detection Coverage
Mean Centroid Error
P95 Centroid Error
Miss Rate
```

완료 기준 예:

```text
Detection Coverage >= 95%
Mean Centroid Error <= 프로젝트에서 정한 허용값
```

허용값은 실제 Target 크기와 영상 해상도를 확인한 뒤 결정한다.

---

# 38. 중요 설계 원칙

## 측정과 해석을 분리한다

```text
Measurement ≠ Diagnosis
```

예:

```text
Vertical RMSE가 Horizontal RMSE보다 높다.
```

는 측정값이다.

하지만:

```text
팔에 힘이 들어가서 그렇다.
감도가 너무 높아서 그렇다.
```

는 현재 영상만으로 확정할 수 없는 가설이다.

## Metric 이름을 관측 범위에 맞춘다

영상에서 직접 확인할 수 없는 인간의 생리학적 Reaction Time을 과장하지 않는다.

따라서 본 프로젝트에서는:

```text
Reaction Time
```

보다:

```text
Direction-change Recovery Latency
```

를 사용한다.

## Raw Metric을 우선한다

Aim Trainer 자체 점수보다:

```text
pixel error
RMSE
ratio
latency
coverage
```

처럼 계산 과정을 설명할 수 있는 값을 중심으로 한다.

---

# 39. 프로젝트에서 피해야 할 것

처음부터 다음 형태로 확장하지 않는다.

```text
영상 업로드
→ YOLO
→ FastAPI
→ Web Dashboard
→ LLM
→ 자동 감도 추천
```

기능이 많아지면 핵심 분석 Engine의 정확도를 검증하기 어렵다.

대신:

```text
Detection
→ Trajectory
→ Metrics
→ Validation
→ Comparison
```

을 먼저 완성한다.

---

# 40. 핵심 차별점

기존 Aim Trainer는 주로:

```text
Score
Accuracy
Hits
```

를 제공한다.

이 프로젝트는 영상에서 직접 추출한 Raw Trajectory를 사용해:

```text
어느 축에서 Error가 큰가?
방향전환 후 언제 다시 Tracking이 안정되는가?
두 Session에서 움직임 특성이 어떻게 달라졌는가?
```

를 설명하는 것을 목표로 한다.

포트폴리오의 핵심 차별점은 **Detection 자체보다 Detection 이후의 Time-series Analysis와 검증**이다.

---

# 41. 포트폴리오에서 보여줄 역량

README와 면접에서는 다음 역량을 중심으로 보여준다.

- Video Frame Processing
- OpenCV Color Segmentation
- Object Centroid Detection
- Frame → Trajectory Data Contract
- Time-series Metric Design
- X/Y RMSE Analysis
- Direction-change Event Detection
- Synthetic Data Validation
- Unit Test / pytest
- Session Comparison
- Measurement와 Interpretation 책임 분리

게임 도메인은 문제의 출발점으로 설명하되, 기술적 본체는:

```text
Video
→ Tracking
→ Time-series
→ Event Detection
→ Quantitative Analysis
```

로 표현한다.

---

# 42. 가장 현실적인 첫 구현

첫 개발 세션에는 여기까지만 만든다.

```text
1. 영상 열기
2. Frame Decode
3. HSV Target Detection
4. Centroid 계산
5. Screen Center와 Error 계산
6. trajectory.csv 저장
7. Tracking Error Timeline 출력
```

이 단계에서는 Recovery Latency, Overshoot, LLM을 구현하지 않는다.

이것만 성공해도 프로젝트의 핵심 Data Flow가 시작된다.

---

# 43. 최종 프로젝트 비전

```text
Aim Video
   ↓
Computer Vision
   ↓
Target Trajectory
   ↓
Time-series Metrics
   ↓
Validated Motion Analysis
   ↓
Session Comparison
```

최종적으로 다음 질문에 답하는 시스템을 목표로 한다.

> 내 Tracking Error는 어느 축에서 더 큰가?

> Target 방향전환 이후 얼마나 빨리 다시 안정적으로 따라가는가?

> 같은 Scenario를 반복했을 때 결과가 재현되는가?

> Session A와 Session B의 움직임 차이는 수치로 무엇인가?

> 내가 만든 Metric은 Synthetic Data에서도 의도한 값을 복원하는가?

---

# 44. 구현 우선순위

```text
P0
Video Reader
HSV Target Detection
Trajectory CSV

P1
Mean Error
RMSE X/Y
On-target Ratio

P2
Direction Change Event
Recovery Latency

P3
Synthetic Data Test
Manual Detection Validation

P4
Visualization
Session Comparison
Markdown Report

P5
README / Demo / Portfolio Closing

P6
Overshoot / Smoothness

P7
YOLO / FastAPI / UI / LLM
```

P5까지 완료하면 포트폴리오용 MVP는 종료한다.

---

# 45. 프로젝트 성공 기준

이 프로젝트가 성공했다고 볼 수 있는 최소 조건:

**사용자가 같은 Tracking Scenario의 영상 2개를 넣었을 때, 단순 점수 차이가 아니라 두 영상의 움직임 특성이 어떻게 달라졌는지를 검증 가능한 Raw Metric으로 설명할 수 있어야 한다.**

예:

```text
Session A → Session B

Mean Error
24.8 px → 21.2 px

RMSE X
18.1 px → 17.3 px

RMSE Y
31.0 px → 25.4 px

On-target Ratio
63.5% → 71.1%

Vertical Recovery Latency
158 ms → 132 ms
```

추가 성공 조건:

```text
- Detection Coverage 95% 이상
- Synthetic Test에서 주요 Metric 계산 검증
- 일부 Frame 수동 Annotation으로 Detector 오차 확인
- pytest로 Metrics / Event Detection 검증
- README에서 Architecture / Engineering Decision / Limitation 설명
```

이 정도를 재현 가능하게 만들면 **기존 Detection 중심 포트폴리오와 차별화되는 Video Tracking + Time-series Analysis 미니 프로젝트**로 충분하다.
