# Test & Validation Plan

## Document Status

- Status: Active / Phase 1 Validation
- Last updated: 2026-09-17 (Day 05)
- Role: 무엇을 어떤 근거로 검증할지 구현 Slice별로 추가한다.
- Rule: 수행하지 않은 Test는 Planned 또는 NOT RUN으로 구분하며 결과를 작성하거나 성공을 주장하지 않는다.

## Validation Goal

- Video Path 확인, Video Open과 실제 Frame Decode 성공을 서로 분리해 검증한다.
- Raw Metadata를 변환하지 않고 관찰한 뒤 FPS, Width와 Height의 최소 유효성 조건을 검증한다.
- Reported Frame Count를 Decode 성공 또는 Segment Completeness의 Source of Truth로 사용하지 않는다.
- Human-verified Run Start Ground Truth를 확보하여 이후 Segment Processing과 Automatic Detector의 Expected Result로 사용한다.

## Input Validation

현재 대표 입력 `data/raw/woong01.mp4`에서 다음 정상 경로를 실행한다.

- `Path.exists()`와 `Path.is_file()`
- `VideoCapture.isOpened()`
- FPS, Width와 Height가 finite이고 `0`보다 큼
- FPS Metadata가 현재 지원 규칙인 exact `60.0`과 일치함

존재하지 않는 Path, 디렉터리 Path, Invalid Metadata와 Unsupported FPS 실패 경로는 별도 입력 또는 Test Double이 준비된 뒤 실행한다.

## Video Decode Validation

- 동일한 열린 `VideoCapture`에서 처음부터 끝까지 Sequential Decode한다.
- `read()`가 성공한 Frame만 Decoded Frame Count에 포함한다.
- Reported Frame Count와 Decoded Frame Count를 별도로 기록한다.
- 첫 `read() == False`에서 반복을 종료하되, 이 신호만으로 정상 EOF와 Decode Failure를 구분했다고 주장하지 않는다.
- Validation 또는 처리 중 예외가 발생해도 `finally`에서 `release()`되는 구조를 유지한다.

## Run Boundary Validation

- Run Start Expected Boundary는 화면 중앙의 Countdown 표시가 사라진 첫 decoded Frame이다.
- `src/inspect_run_start.py`에서 Frame을 순차적으로 확인하고 `s`로 Ground Truth Frame을 선택한다.
- 대표 Video의 Expected Result는 마지막 Countdown Frame `355`, 첫 Countdown 미표시 Frame `356`, Run Start `5.933333333333334` seconds다.
- Known Start를 이용한 `[Run Start, Run End)` 처리와 Segment Completeness는 다음 Slice에서 검증한다.

## Target Observation Validation

## On-target / Off-target / Missing Validation

## Direction Validation

## Event Validation

## Metric Validation

## Known Failure Cases

아직 실제 실행하지 않은 실패 경로:

- FPS, Width 또는 Height가 NaN, 무한대, `0` 또는 음수
- FPS가 유효하지만 exact `60.0`이 아닌 Unsupported FPS
- Video 중간 Decode Failure
- Run End 전에 Decode가 중단되어 필요한 60초 Segment가 부족한 경우
- Inspector가 선택 없이 EOF 또는 사용자 취소로 끝나는 경우

## Validation Results Link

실제 실행 결과는 `docs/06_validation_report.md`에 기록한다.
