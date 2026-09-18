# Validation Report

## Document Status

- Status: Active / Results through Day 05
- Last updated: 2026-09-17 (Day 05)
- Role: Test & Validation Plan에 따라 실제로 수행한 검증 결과와 근거를 기록한다.
- Rule: 아직 실행하지 않은 결과를 작성하거나 성공을 주장하지 않는다.

## Validation Scope

Phase 1의 Local Video Path, Video Open, Raw Metadata, 정상 Metadata/FPS 경로, 전체 Sequential Decode와 Human-verified Known Run Start를 검증했다. 60초 Run Segment Processing과 Segment Completeness는 아직 범위에 포함하지 않았다.

## Validation Environment

- OS / Shell: Windows / PowerShell
- Python environment: Project `.venv`
- OpenCV: `5.0.0`
- Representative local input: `data/raw/woong01.mp4`
- 실제 Video는 Repository에 Commit하지 않는다.

## Test Execution Summary

| Validation | Result | Evidence |
| --- | --- | --- |
| Local Path exists / is file | PASS | 실제 Path 확인 메시지 출력 |
| Video Open / `isOpened()` | PASS | `Video Open에 성공했습니다.` 출력 |
| Raw Metadata inspection | PASS | FPS, Width, Height, Reported Frame Count 관찰 |
| Metadata/FPS happy path | PASS | 예외 없이 Validation 통과 |
| Full sequential decode | PASS | 첫 `False` 전까지 4124 Frames Decode |
| Resource cleanup normal path | PASS | `finally`에서 `release()` 실행 |
| Human Run Start selection | PASS | Frame 356 선택 및 seconds 변환 |
| Invalid/Unsupported failure paths | NOT RUN | 별도 입력 또는 Test Double 미준비 |
| 60-second Segment / Completeness | NOT RUN | 다음 Slice |

## Input and Video Decode Results

Observed raw metadata:

- FPS: `60.0` (`float`)
- Width: `1920.0`
- Height: `1080.0`
- Reported Frame Count: `4124.0`

Sequential decode result:

- Decoded Frame Count: `4124`
- 이번 입력에서는 Reported와 Decoded Count가 일치했다.
- 두 값의 일치는 관찰 결과이며 Reported Frame Count를 Decode 성공의 Source of Truth로 사용하지 않았다.
- OpenCV `read()`의 마지막 `False`가 정상 EOF인지 Decode Failure인지는 이 실행만으로 구분하지 않았다.

## Run Boundary Results

- Contract: Countdown 표시가 사라진 첫 decoded Frame을 Run Start에 포함한다.
- 마지막 Countdown 표시 Frame: `355`
- 첫 Countdown 미표시 Frame: `356`
- Selected Run Start Frame: `356`
- Selected Run Start Seconds: `5.933333333333334`
- Selection method: 개발용 `src/inspect_run_start.py`에서 Human Verification

## Target Observation Results

## State and Direction Results

## Event and Metric Results

## Known-value and Synthetic Results

## Manual Validation Results

- 원본 Video를 Frame 단위로 전진하며 Countdown 표시 여부를 확인했다.
- 마지막 표시 숫자 자체는 고정 Contract로 사용할 수 없음을 확인했다.
- Frame `356`부터 Countdown이 보이지 않고 Aim Training이 시작되는 것을 확인했다.

## Deviations and Failures

- 실행 중 예상하지 못한 예외는 없었다.
- Invalid Metadata와 Unsupported FPS 예외 경로는 아직 의도적으로 실행하지 않았다.
- Decode Failure와 정상 EOF의 구분은 구현하지 않았다.

## Known Limitations

- 현재 FPS 지원 규칙은 OpenCV Metadata의 exact `60.0` 비교다.
- 59.94 FPS tolerance와 Variable Frame Rate는 지원하지 않는다.
- Run Start seconds를 `main.py` Segment Processing에 아직 연결하지 않았다.
- `[Run Start, Run End)` 처리와 Segment Completeness는 검증하지 않았다.
- Automatic Countdown Detection과 Manual Fallback UI는 구현하지 않았다.

## Conclusion

대표 Video에서 Path Validation, Video Open, Raw Metadata 관찰과 정상 경로 Validation, 전체 Sequential Decode 및 Human-verified Run Start Ground Truth 확보까지 완료했다. 다음 검증 대상은 Known Run Start를 이용한 정확한 60초 Segment Processing과 time coverage 기반 Completeness다.
