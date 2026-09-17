# Day 05 — Metadata Validation, Sequential Decode, and Known Run Start Ground Truth

## Today's Goal

Day 05에서는 새로운 분석 Domain으로 확장하지 않고 Phase 1의 다음 하위 Slice를 구현하고 검증했다.

```text
Raw Metadata Inspection
-> Metadata Validation
-> Supported FPS Validation
-> Sequential Frame Decode
-> Human-verified Known Run Start Ground Truth
```

Primary Coder는 프로젝트 작성자이며, AI는 개념 설명, 코드 Review와 Validation 보조 역할을 맡았다.

## Raw Metadata Inspection

열린 `VideoCapture`에서 다음 Metadata를 원본 반환값 그대로 조회했다.

- FPS: `60.0`
- Width: `1920.0`
- Height: `1080.0`
- Reported Frame Count: `4124.0`

첫 관찰에서는 반올림하거나 `int`로 변환하지 않았다. OpenCV `VideoCapture.get()`이 반환한 `float` 값을 유지했다.

## Metadata Validation

다음 기본 유효성 조건을 구현했다.

- FPS는 finite이고 `0`보다 커야 한다.
- Width는 finite이고 `0`보다 커야 한다.
- Height는 finite이고 `0`보다 커야 한다.
- Reported Frame Count는 조회하고 관찰하지만 Validation 실패 조건으로 사용하지 않는다.

실제 `woong01.mp4`는 정상 경로를 통과했다. NaN, 무한대, `0`, 음수에 대한 실패 경로는 아직 실제 실행으로 검증하지 않았다.

## Supported FPS Validation

실제 관찰값이 정확히 `60.0`임을 확인한 뒤, 현재 통제된 입력에 대한 최소 지원 규칙을 다음과 같이 구현했다.

```text
FPS == 60.0
-> Supported

그 외의 유효한 FPS
-> Unsupported FPS
```

- `round()`와 tolerance를 사용하지 않았다.
- 59.94 FPS 지원과 Variable Frame Rate 처리는 Deferred 상태를 유지한다.
- Invalid Metadata 검사와 Unsupported FPS 판정을 분리했다.

## Sequential Frame Decode

Metadata와 FPS Validation을 통과한 동일한 열린 `VideoCapture`를 사용해 Recording 처음부터 Frame을 순차적으로 읽었다.

```text
read()
-> 성공한 Frame만 decoded_frame_count 증가
-> 첫 False에서 반복 종료
```

Observed result:

- Reported Frame Count: `4124.0`
- Decoded Frame Count: `4124`

두 값은 이번 실행에서 일치했지만, Reported Frame Count를 Decode 성공의 Source of Truth로 사용하지 않았다.

OpenCV `read()`의 `False`만으로 정상 EOF와 Decode Failure를 확정적으로 구분할 수 없음을 확인했다. 따라서 이번 결과는 첫 실패 신호 전까지 `4124` Frames를 성공적으로 Decode했다는 의미로 제한한다.

## Resource Lifecycle

다음 lifecycle을 유지했다.

```text
Path Validation
-> Video Open
-> Open State Check
-> Metadata Inspection and Validation
-> Sequential Decode
-> finally
-> release()
```

Metadata Validation 실패, Unsupported FPS와 Decode 처리 중 예외가 발생해도 `finally`에서 Video resource가 해제되는 구조다.

## Known Run Start Contract Clarification

실제 영상을 확인하며 기존의 `Countdown = 0` 가정이 영상과 맞지 않음을 발견했다. 마지막으로 표시되는 Countdown 숫자는 Frame capture timing에 따라 달라질 수 있으므로 특정 숫자를 Run Start Contract로 고정하지 않는다.

현재 Known Run Start 의미는 다음과 같이 정리했다.

> Run Start는 화면 중앙의 Countdown 표시가 사라진 첫 번째 decoded frame의 recording-relative time이다.

```text
마지막 Countdown 표시 Frame
-> 첫 Countdown 미표시 Frame
   -> Run Start 포함
```

- 마지막 Countdown Frame은 Run Segment에서 제외한다.
- 첫 Countdown 미표시 Frame은 Run Segment에 포함한다.
- 마지막 표시 숫자 `0.1x`는 관찰 특징이며 Domain Contract가 아니다.
- Automatic Countdown Detection은 아직 구현하지 않았다.

## Development Ground Truth Inspector

분석 본체와 분리된 개발·검증용 `src/inspect_run_start.py`를 프로젝트 작성자가 직접 구현했다.

Inspector responsibilities:

- Video Path Validation
- OpenCV Video Open과 Open State Check
- Frame별 Sequential Decode
- 원본을 유지한 `1280 x 720` preview 생성
- 키 입력에 따른 Frame 이동
- `s` 입력 시 현재 Frame을 Known Run Start로 선택
- 선택된 Frame Index를 recording-relative seconds로 변환
- `q` 입력 시 선택 없이 종료
- `finally`에서 Video resource와 OpenCV window 정리

Human verification result:

- 마지막 Countdown Frame: `355`
- 첫 Countdown 미표시 Frame: `356`
- Selected Run Start Frame: `356`
- Selected Run Start Seconds: `5.933333333333334`

이 값은 최종 사용자가 초 단위 숫자를 직접 입력한다는 의미가 아니다. 현재 개발 단계에서 Automatic Countdown Detector를 검증하기 위한 Human Ground Truth다.

## Validation Status

### Completed

- 실제 Video Raw Metadata 관찰
- FPS, Width와 Height 정상 경로 Validation
- exact `60.0` Supported FPS 정상 경로 확인
- 전체 Video Sequential Decode
- Reported Frame Count와 Decoded Frame Count 분리
- `try/finally` 기반 resource cleanup 유지
- Known Run Start 의미 정교화
- 개발용 Human Ground Truth Inspector 구현
- Human Ground Truth Frame과 seconds 확인

### Not Yet Validated

- Invalid FPS: NaN, 무한대, `0`, 음수
- Invalid Width/Height: NaN, 무한대, `0`, 음수
- Unsupported FPS 실제 실패 실행
- Decode 중간 실패와 정상 EOF의 구분
- Inspector의 EOF 종료와 사용자 취소를 서로 다른 상태로 표현하는 동작

## Tomorrow / Next Slice

다음 항목은 Day 05에서 구현하지 않았으며 다음 작업으로 넘긴다.

1. Known Run Start seconds를 `main.py`의 개발용 입력으로 연결
2. `Run End = Run Start + 60.0 seconds` 계산과 검증
3. 기존 단일 Sequential Decode loop 안에서 Frame time 계산
4. `[Run Start, Run End)` 구간의 모든 Decode 성공 Frame 처리
5. exact `3600 Frames`를 가정하지 않는 Run Segment Frame Count 관찰
6. time coverage 기반 Segment Completeness 판정
7. Run End 도달 전에 Decode가 중단된 실패 경로 검증
8. 확정된 Countdown disappearance Contract를 Source of Truth 문서에 반영
9. Metadata 및 Unsupported FPS 실패 경로 실제 테스트

## Explicitly Deferred

- Automatic Countdown Detection
- Countdown OCR 또는 AI Model
- Manual Fallback UI
- Target Detection과 Crosshair Detection
- First On-target, On-target / Off-target와 Missing
- Direction, Event와 Metric
- FastAPI, Vue, TXT Report와 Database
- `CAP_PROP_POS_MSEC` Seek
- Variable Frame Rate와 PTS 기반 Timestamp
- full architecture refactoring

## Repository Notes

- `src/main.py`는 Metadata Validation과 전체 Sequential Decode까지 담당한다.
- `src/inspect_run_start.py`는 개발·검증용 Ground Truth 생성 도구다.
- 실제 Video는 Repository에 Commit하지 않는다.
- Python Test 코드는 아직 작성하지 않았다.
- Git Commit과 Push는 수행하지 않았다.

## Study Notes

- OpenCV Metadata 원본 관찰과 Validation은 별도 단계다.
- Video Open 성공과 실제 Frame Decode 성공은 서로 다른 검증 결과다.
- Reported Frame Count는 Decoded Frame Count의 Source of Truth가 아니다.
- `read()`의 False는 정상 EOF 전용 신호가 아니다.
- Known Run Start는 Countdown 숫자값이 아니라 Countdown이 사라진 첫 Frame이다.
- Human Ground Truth는 이후 Automatic Detector의 Expected Result로 사용한다.
