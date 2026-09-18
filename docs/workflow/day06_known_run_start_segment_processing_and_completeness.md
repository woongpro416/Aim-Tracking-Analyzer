# Day 06 — Known Run Start Segment Processing and Completeness

## Today's Goal

Day 06에서는 Day 05에 확보한 Human-verified Known Run Start를 `main.py`의 기존 단일 Sequential Decode loop에 연결했다.

```text
Known Run Start Seconds
-> Run End 계산
-> Frame Time 계산
-> [Run Start, Run End) 구간 판정
-> Segment Frame 관찰
-> Successful Decode Coverage 계산
-> Segment Completeness 판정
```

Primary Coder는 프로젝트 작성자이며, 직접 핵심 로직을 작성하고 각 정상·실패 경로를 실행해 결과를 확인했다. AI는 개념 설명, 작은 구현 단위 제시, 코드 Review와 검증 결과 해석을 보조했다. 사용자의 명시적 요청 후에는 출력 문구의 한글화와 도메인 표현 통일만 직접 수정했다.

## Development Input and Duration Contract

Day 05의 Human Ground Truth를 개발·검증용 입력으로 연결했다.

```text
KNOWN_RUN_START_SECONDS = 5.933333333333334
RUN_DURATION_SECONDS = 60.0
```

`RUN_DURATION_SECONDS`를 60초 Duration의 유일한 Source of Truth로 사용했다.

```text
run_end_seconds
= known_run_start_seconds + RUN_DURATION_SECONDS
```

`3600 Frames`는 구현에 입력하는 반복 횟수나 성공 조건으로 사용하지 않았다. 60 FPS Video에서 60초 구간을 시간 조건으로 판정한 결과로만 관찰했다.

## Known Run Start Validation

다음 순서로 Known Start를 검증했다.

```text
None 검사
-> finite 검사
-> 음수 검사
-> Run End 계산
```

- `None`은 Ground Truth가 제공되지 않은 상태다.
- `NaN`, `Infinity`와 `-Infinity`는 유한한 시간값이 아니다.
- 음수는 recording-relative time으로 허용하지 않는다.
- `0.0`은 누락값이 아니라 유효한 시작 시간이다.
- `math.isfinite(None)`의 `TypeError`를 피하기 위해 `None` 검사를 먼저 수행했다.

## Zero-based Frame Time

기존 Sequential Decode loop 안에서 `decoded_frame_count`의 증가 전 값을 현재 프레임의 0-based index로 사용했다.

```text
read() success
-> current_frame_index = decoded_frame_count
-> frame_time_seconds = current_frame_index / video_fps
-> Segment 포함 판정
-> decoded_frame_count += 1
```

첫 성공 프레임은 다음과 같다.

```text
index = 0
time = 0 / video_fps = 0.0 seconds
```

`current_frame_index`를 직접 증가시키지 않는다. 각 반복에서 증가한 `decoded_frame_count`를 다시 대입받는 구조다.

## Half-open Segment Boundary

Run Segment에는 half-open interval을 적용했다.

```text
[run_start_seconds, run_end_seconds)
```

각 Decode 성공 Frame의 포함 조건은 다음과 같다.

```text
run_start_seconds <= frame_time_seconds < run_end_seconds
```

- Start와 같은 프레임은 포함한다.
- End와 같은 프레임은 제외한다.
- Segment Frame Count는 조건을 만족한 Decode 성공 Frame에 대해서만 증가한다.
- 전체 Decoded Frame Count는 Segment 조건과 무관하게 모든 Decode 성공 Frame에 대해 증가한다.

## First and Last Segment Frame Observation

Frame Count만으로는 Segment 경계가 한 Frame 밀렸는지 확인할 수 없다. 따라서 첫 포함 Frame과 마지막 포함 Frame의 Index를 관찰했다.

- First Segment Frame은 초기 `None` 상태에서 최초 포함 Frame을 만났을 때 한 번만 저장했다.
- Last Segment Frame은 포함 Frame을 만날 때마다 현재 Index로 갱신했다.
- Index `0`이 유효하므로 미설정 상태는 truthy 검사가 아닌 `is None`으로 구분했다.
- First/Last Frame Time은 loop 종료 후 Index를 FPS로 나누어 계산했다.

## Frame Time and Coverage End

현재 constant-FPS MVP에서 Frame Time과 Coverage End를 다음처럼 구분했다.

```text
frame_time_seconds
= current_frame_index / video_fps

frame_coverage_end_seconds
= (current_frame_index + 1) / video_fps
```

- Frame Time은 해당 Frame의 시작 시간이며 Segment 포함 판정에 사용한다.
- Coverage End는 해당 Frame 한 칸까지 성공적으로 Decode한 뒤의 시간 경계다.
- `frame_coverage_end_seconds`는 Segment 조건 밖에서 모든 Decode 성공 Frame마다 갱신했다.
- 이 계산은 CFR MVP 구현이며 VFR, PTS 또는 실제 노출 시간으로 일반화하지 않는다.

## Segment Completeness

Reported Frame Count를 Completeness의 Source of Truth로 사용하지 않았다. 다음 조건으로 마지막 successful decode coverage가 필요한 Run End에 도달했는지 판정했다.

```text
frame_coverage_end_seconds >= run_end_seconds
-> Complete

frame_coverage_end_seconds < run_end_seconds
-> Incomplete
```

Incomplete인 경우에도 Video가 짧은지, 중간 Decode Failure가 발생했는지 원인을 단정하지 않았다.

> 필요한 분석 종료 시간까지 프레임을 성공적으로 디코딩하지 못했다.

## Normal Path Observed Result

`woong01.mp4`와 Human Ground Truth를 사용한 정상 실행 결과다.

| Observation | Result |
|---|---:|
| FPS | `60.0` |
| Known Run Start Seconds | `5.933333333333334` |
| Run End Seconds | `65.93333333333334` |
| First Segment Frame Index | `356` |
| First Segment Frame Time | `5.933333333333334` |
| Last Segment Frame Index | `3955` |
| Last Segment Frame Time | `65.91666666666667` |
| Run Segment Frame Count | `3600` |
| Reported Frame Count | `4124.0` |
| Decoded Frame Count | `4124` |
| Successful Decode Coverage End | `68.73333333333333` |
| Segment Completeness | `Complete` |

Frame `356`은 Start와 같아 포함되고 Frame `3956`은 End와 같아 제외된다. 따라서 마지막 포함 Frame은 `3955`다.

## Manual Failure-path Validation

복잡한 Video Fixture를 추가하지 않고 개발용 Known Start 상수를 임시로 변경해 다음 경로를 직접 검증했다.

| Temporary Input | Expected Meaning | Observed Result |
|---|---|---|
| `0.0` | 유효한 시작 경계 | Frame `0`~`3599`, Count `3600`, Complete |
| `None` | Ground Truth 미제공 | `ValueError`: 시작 위치가 존재하지 않음 |
| `math.nan` | non-finite | `ValueError`: 유효하지 않은 숫자 |
| `math.inf` | non-finite | `ValueError`: 유효하지 않은 숫자 |
| `-1.0` | 음수 recording-relative time | `ValueError`: 시작 위치는 음수일 수 없음 |
| `20.0` | Run End `80.0`에 도달하지 못함 | Incomplete |

`20.0`을 사용한 Incomplete 경로의 관찰값은 다음과 같다.

| Observation | Result |
|---|---:|
| Temporary Start Seconds | `20.0` |
| Run End Seconds | `80.0` |
| First Segment Frame Index | `1200` |
| Last Segment Frame Index | `4123` |
| Last Segment Frame Time | `68.71666666666667` |
| Segment Frame Count | `2924` |
| Successful Decode Coverage End | `68.73333333333333` |
| Segment Completeness | `Incomplete` |

모든 수동 검증 후 `KNOWN_RUN_START_SECONDS`는 Human Ground Truth인 `5.933333333333334`로 복원했다.

## Resource Lifecycle

Day 05의 lifecycle을 그대로 유지했다.

```text
Path Validation
-> Video Open
-> Open State Check
-> Metadata Inspection and Validation
-> Supported FPS Validation
-> Known Start Validation
-> Sequential Decode and Segment Processing
-> finally
-> release()
```

Known Start Validation 실패와 처리 중 예외에서도 `finally` 구조를 통해 `VideoCapture` 자원을 해제한다.

## User-facing Output Terminology

내부 Domain Contract와 변수명의 `Run`은 유지하되, Console과 Inspector에서 사용자에게 보이는 문구는 프로젝트 목적이 드러나도록 `에임 트래킹 분석 구간`으로 표현했다.

- Metadata, Segment 경계, Count와 Coverage 출력을 한글로 통일했다.
- `src/inspect_run_start.py`의 조작 안내, Frame 관찰 문구, 선택 결과와 Window Title을 같은 용어로 정리했다.
- 라벨 없이 중복 출력되던 Reported Frame Count를 제거했다.

## Validation Status

### Completed

- Known Run Start를 개발·검증용 입력으로 연결
- `RUN_DURATION_SECONDS = 60.0` Source of Truth 정의
- Known Start의 `None`, finite와 음수 Validation
- `0.0`을 유효한 시작 시간으로 검증
- 0-based Frame Index와 CFR Frame Time 계산
- `[Run Start, Run End)` half-open Segment 판정
- First/Last Segment Frame Index와 Time 관찰
- Segment Frame Count와 전체 Decoded Frame Count 분리
- Successful Decode Coverage End 계산
- Coverage 기반 Segment Completeness 판정
- Complete와 Incomplete 경로 수동 검증
- 기존 `try/finally` Resource Lifecycle 유지
- Console과 Inspector의 User-facing 출력 용어 정리

### Not Yet Automated

- Known Start Validation의 pytest 자동화
- Segment Boundary와 Count의 pytest 자동화
- Complete/Incomplete 판정의 pytest 자동화
- 중간 Decode Failure와 정상 EOF의 구분

## Explicitly Deferred

- Automatic Countdown Detection
- Countdown OCR 또는 AI Model
- Manual Fallback UI
- Video Seek과 Run End 조기 종료
- `CAP_PROP_POS_MSEC`
- Variable Frame Rate와 PTS Timestamp
- Target Detection과 Crosshair Detection
- First On-target, On-target / Off-target와 Missing
- Direction, Event와 Metric
- FastAPI, Vue, TXT Report와 Database
- Full Architecture Refactoring

## Tomorrow / Next Slice

1. Day 06 결과를 Validation Report와 Test Plan에 반영한다.
2. 현재 구현의 가독성과 출력 순서를 최종 정리한다.
3. 지나친 구조 변경 없이 시간 경계 로직을 간단한 pytest로 검증할 수 있는지 검토한다.
4. Automatic Countdown Detection은 현재 Slice의 문서화와 검증을 마친 뒤에 다음 단계로 넘긴다.

## Repository Notes

- `src/main.py`는 Metadata Validation, Known Start Validation, 전체 Sequential Decode, Segment Processing과 Completeness 판정을 담당한다.
- `src/inspect_run_start.py`는 Human Ground Truth를 확보하는 개발·검증용 도구다.
- 실제 Video는 Repository에 Commit하지 않는다.
- Python Test 코드는 아직 작성하지 않았다.
- Git Commit과 Push는 수행하지 않았다.

## Study Notes

- Frame Time은 Frame의 시작 시간이고 Coverage End는 해당 Frame 구간을 처리한 뒤의 시간 경계다.
- Segment 경계는 `[start, end)`로 판정해 Start Frame은 포함하고 End Frame은 제외한다.
- `0.0`, `None`, non-finite와 음수는 서로 다른 입력 상태다.
- Segment Completeness는 Reported Frame Count가 아닌 successful decode coverage로 판정한다.
- Incomplete는 필요한 Run End에 도달하지 못했다는 의미이며 구체적 원인을 단정하지 않는다.
