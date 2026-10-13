# Validation Report

## Document Status

- Status: **Phase 2 complete / Final Production validation passed**
- Last updated: 2026-10-13 (Day 12 closeout)
- Role: 실제 실행한 검증 결과와 제한된 근거를 기록한다. 계획과 미검증 범위는 성공 결과와 구분한다.

## Validation Scope

영상 입력 정상 경로, 전체 Sequential Decode, 사람이 확인한 Run Start, 60초 Segment 완전성, 승인된 Closing+Top-strip Detection, 세 Tracking State와 Frame별 기록을 검증했다. 비교 도구의 결과와 별도로 실제 Production `analyze_run()`을 재실행하여 18개 사용자 Label과 비교했다.

Direction, OFF_TARGET Event, Recovery, Score 등 Tracking Metric은 이번 범위에 없다.

## Validation Environment and Input

- OS / Shell: Windows / PowerShell
- Python: `3.12.0`, 프로젝트 `.venv`
- OpenCV: `5.0.0` (`opencv-python` `5.0.0.93`)
- NumPy: `2.5.3`, pytest: `9.1.1`
- 입력: `data/raw/woong01.mp4` (Git 미포함)
- SHA-256: `9197211c8fbade5695db6dc0761b06ad5dffbb315b0f4258ddc6a5de8512a394`
- 메타데이터: FPS `60.0`, 너비 `1920.0`, 높이 `1080.0`, 전체 Frame Count `4124.0`
- 실제 순차 Decode: `4124` Frame, 마지막 Frame의 시간 범위 끝 `68.73333333333333`초

Reported와 Decoded Count가 일치한 것은 이 입력의 관찰 결과다. 구간 완전성은 성공적으로 Decode한 범위로 확인한다. 마지막 `read() == False`가 정상 EOF인지 Decode Failure인지는 별도로 구분하지 않았다.

## Execution and Evidence

저장소 루트에서 실행한다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe src/validate_production_run.py
.\.venv\Scripts\python.exe src/inspect_run_baselines.py
```

| 검증 | 결과 | 근거 |
| --- | --- | --- |
| 기존·추가 Unit / Regression | PASS | **53 passed** |
| 영상 Path / Open / Metadata 정상 경로 | PASS | 실제 Production 분석 정상 완료 |
| 60초 Segment / 시간 범위 완전성 | PASS | Frame 356~3955, 총 3600, Decode 범위가 Run End를 포함 |
| Run / Raw Observation / Tracking State 개수 | PASS | 각각 3600 |
| Frame 누락·중복·순서 | PASS | 두 목록 모두 연속 Index 356~3955와 일치 |
| 후보 수·Center·MISSING 계약 | PASS | 단일 후보는 Center 존재, 미결정은 Center None·MISSING |
| 기대 상태 집계 재현 | PASS | ON 2319 / OFF 1000 / MISSING 281 |
| 사용자 Ground Truth | PASS | Production 18/18 일치 |
| Original Baseline 보존 | PASS | Production 변경 뒤에도 2136 / 1183 / 281 재현 |
| 영상 동일성 | PASS | 고정 검증 자료의 SHA-256과 일치 |
| Invalid Metadata / Unsupported FPS 전체 실패 경로 | NOT RUN | 별도 입력·Test Double로 모든 경로를 실행하지 않음 |

`tests/data/manual_ground_truth.json`에 영상 동일성·집계·사용자 Label을 Version Control로 보존한다. 개발 출력 `outputs/day12_validation/production_run.json`과 `production_validation.json`에는 실제 전체 결과와 검증 보고서가 있고, 이 생성 폴더는 Git에서 제외한다.

## Run Boundary Results

- Countdown 표시의 마지막 Frame은 `355`, 첫 미표시 Frame은 `356`으로 사용자가 확인했다.
- Run Start: `5.933333333333334`초, Run End: `65.93333333333334`초.
- `[Run Start, Run End)`로 처리하여 시작 Frame은 포함하고 끝 경계는 제외한다.
- 첫 분석 Frame `356`, 마지막 분석 Frame `3955` (`65.91666666666667`초).
- 분석 Frame 수 `3600`. 자동 Countdown 탐지는 아직 구현하지 않았다.

## Final Detection and State Results

사용자 승인 정책은 `HSV → 5×5 Closing → External Contour → Area ≥ 150 → bbox 전체의 y+h ≤ 30 제외 → 단일 후보 선택`이다. 기존 HSV·면적 조건과 상태 의미를 유지했다.

ON_TARGET은 선택 Contour 내부·경계에 중앙 Crosshair가 있는 경우, OFF_TARGET은 Contour 외부인 경우다. 후보 0개 또는 복수 후보는 MISSING이며 OFF_TARGET으로 치환하지 않는다.

| 방식 | ON_TARGET | OFF_TARGET | MISSING | 합계 | 사용자 Label 일치 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 2136 | 1183 | 281 | 3600 | 9/18 |
| Closing-only | 2316 | 997 | 287 | 3600 | 14/18 |
| Closing+Top-strip / Production | 2319 | 1000 | 281 | 3600 | 18/18 |

최종 Production의 MISSING 원인은 후보 없음 281개, 복수 후보 0개다. 세 Baseline의 상태 변경 Frame 188개, 후보 수만 변경 Frame 0개도 재현했다. 상태 집계는 알고리즘의 출력 분포이며 전체 Frame의 정확도 지표가 아니다.

## Synthetic and Regression Coverage

- 빈 Frame·단일 후보·복수 후보·작은 면적·잘못된 BGR 입력.
- Closing의 작은 끊김 연결, 상단 Noise 제거, 상단 경계를 넘는 후보 유지, 상단 실제 Target 오제거 위험.
- Contour 내부·경계·외부·None의 상태 의미.
- 실험 Original 보존과 후보 필터 독립성.
- 상태/후보 수 변경 분류, 표본 선정, 사용자 Label 보존·null 처리.
- 검증 자료의 Frame 수·중복·Label 누락·충돌·빈 Label이 정상 결과로 통과하지 않는지 확인.

합성 테스트는 계약과 오류 방지를 검증한다. 다른 실제 영상에서의 일반화 성능을 증명하지 않는다.

## Manual Validation Results and Limits

Day 10 사용자 Label 10개에 Day 12 추가 Label 8개를 합쳐 18개를 확인했다. Closing-only는 `764, 2617, 3623, 3722`에서 Target이 확인됐는데 MISSING이었다. 최종 Production은 확인한 18개 모두 사용자 Label과 일치했다. 전체 Label과 선정 근거는 [Day 12 종료 기록](workflow/day12_detection_validation_and_phase2_closeout.md)에 있다.

표본은 같은 영상의 변경 패턴·시간대를 고려해 선정했으며 정책 선택에도 사용했다. 독립적인 새 영상 평가나 무작위 전수 정답이 아니다. **18/18은 전체 영상 정확도 100%를 의미하지 않는다.**

Top-strip은 현재 **1920×1080 HUD 환경의 MVP 규칙**이다. Bounding Box 전체가 상단 `[0, 30)`px 안에 들어간 후보만 제외한다. 실제 Target이 그 영역에 완전히 들어가면 오제거할 수 있다. 다른 해상도·Scenario·HUD 일반화 성능은 검증하지 않았다.

현재는 화면 중앙 Crosshair, 60 FPS CFR, 수동 Known Run Start를 가정한다. exact `60.0` 이외 FPS·VFR, 자동 Countdown 탐지, Decode Failure와 EOF 구분은 후속 범위다. Shape Filter·Hough Circle·추가 Threshold 튜닝은 이번 Production에 도입하지 않았다.

## Phase Handoff

승인 정책, Unit / Regression, 전체 Run 정합성과 제한된 수동 검증을 통과해 **Phase 2를 종료했다.** Phase 3는 반환된 `tracking_state_sequence`를 사용한다. MISSING의 Event 경계 역할을 정한 뒤 OFF_TARGET Event와 Duration부터 구현한다.
