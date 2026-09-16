# Day 04 — Video Input Boundary and Open Validation

## Today's Goal

Day 04부터 Requirement 중심의 Phase 0를 종료하고 실제 구현 단계로 전환했다. Primary Coder는 프로젝트 작성자이며, AI는 Implementation Mentor, Contract Reviewer, Code Reviewer와 Validation Reviewer 역할로 제한했다.

원래 Day 04 Initial Slice는 Metadata, FPS Validation과 Sequential Decode까지 포함했지만, 오늘은 다음의 더 작은 구현 단위를 실제 Video로 검증하고 작업을 종료했다.

```text
Development Local Video Path
-> Path Validation
-> OpenCV Video Open
-> Open State Check
-> Resource Release
```

Metadata Inspection 이후 작업은 검증되지 않은 상태로 Day 05에 넘긴다.

## System Input and Analysis Core Boundary

최종 사용자 입력과 Analysis Core 입력을 구분했다.

```text
Final System:
User
-> Web Video Upload
-> Server-side Temporary Local File
-> Local Path
-> Analysis Core

Day 04 Development:
Development Local Path
----------------------> Analysis Core
```

- 최종 사용자는 Local Video Path를 직접 입력하지 않는다.
- Local Video Path는 Server와 Analysis Core 사이의 내부 Input Contract다.
- Day 04의 Local Path는 Web Upload Boundary를 개발 중 직접 대체하는 입력이다.
- FastAPI, Upload API, Temporary File 처리와 Web UI 구현은 현재 Slice에 포함하지 않았다.

## Output Boundary Clarification

기존 Internal Analysis Output을 별도 계층으로 복제하지 않고 Structured Analysis Result의 canonical structured form으로 정의했다.

```text
Analysis Core
-> Structured Analysis Result
   |-> Web Response Representation
   `-> TXT Report Representation
```

- Web Response와 TXT Report는 같은 Result에서 파생한다.
- Representation 계층은 분석 계산을 다시 수행하지 않는다.
- TXT를 분석 결과의 원본으로 사용하거나 다시 읽어서 Web Result를 만들지 않는다.
- JSON Schema와 TXT Format, 저장 및 Download 정책은 Deferred했다.

## Frontend Technology Decision

최종 Web Frontend Technology는 Vue 3 + Vite로 결정했다.

- Frontend는 Video Upload UI와 Analysis Result 표시를 담당한다.
- Frontend는 Analysis Core에 직접 의존하지 않고 Web/API Boundary를 통해 연결된다.
- Vue 3 + Vite는 Domain Requirement가 아니라 Technology / Architecture Decision이다.
- Vue Project 생성, npm Dependency 설치와 Frontend 코드는 작성하지 않았다.

## Development Environment

- Python 가상환경: `.venv`
- Video library: `opencv-python`
- 개발용 실제 Video: `data/raw/woong01.mp4`
- Video 파일은 Repository에 Commit하지 않는다.
- OpenCV 실행은 `.venv`의 Python을 사용해야 한다. System Python에는 `cv2`가 설치되어 있지 않은 것을 확인했다.

## Path Validation Implementation

`pathlib.Path`를 사용해 개발용 Video Path를 표현했다.

초기 상대경로는 다음 실행 위치에 의존했다.

```text
src> python main.py                    -> success
project root> python src/main.py       -> failure
```

실행 위치 의존성을 제거하기 위해 `__file__`을 기준으로 Project Root를 계산하도록 수정했다.

현재 Path Validation 순서:

```text
Path 생성
-> exists() 확인
-> is_file() 확인
-> Validation 성공
```

- Path 객체 생성은 실제 파일 존재를 보장하지 않는다.
- 파일 없음은 `FileNotFoundError`로 구분한다.
- 경로가 실제 파일이 아니면 `ValueError`로 구분한다.
- 개발 중 성공 확인은 `return`이 아니라 `print`로 관찰했다.
- 실행 동작은 `main()` 내부에 두어 import 시 부작용을 피했다.

## Video Open Implementation

Path Validation 성공 후 OpenCV로 Video Open을 시도했다.

```text
Validated Local Path
-> cv2.VideoCapture
-> isOpened()
-> Open Success / Runtime Failure
-> finally
-> release()
```

- `VideoCapture` 객체 생성과 실제 Open 성공을 구분했다.
- `isOpened()`를 Open 성공 판정에 사용했다.
- Video Open 실패는 Path 실패와 다른 책임으로 구분했다.
- `try/finally`를 사용해 성공 또는 실패와 관계없이 `release()`가 호출되는 구조로 정리했다.
- 현재 단계는 Video Open까지이며 Frame Decode 성공을 의미하지 않는다.

## Validation Results

### Valid Local Video Path

Expected:

- 실제 Video Path가 존재한다.
- Path가 실제 파일이다.

Observed:

- `data/raw/woong01.mp4`의 절대 경로가 의도한 위치로 해석되었다.
- `exists()`와 `is_file()` 검사를 통과했다.

Result: `PASS`

### Working Directory Independence

Expected:

- 실행 위치가 Project Root 또는 `src`여도 같은 Video Path를 사용한다.

Observed:

- `__file__` 기반 Project Root 적용 후 두 실행 위치에서 같은 Video를 확인했다.

Result: `PASS`

### Video Open

Expected:

- 실제 Video를 OpenCV가 열 수 있다.
- `isOpened()`가 `True`다.

Observed:

- `.venv` Python에서 Video Open 성공 메시지를 확인했다.
- 예외 없이 정상 종료했다.

Result: `PASS`

### Resource Cleanup

Expected:

- 성공 또는 예외 발생 시 Video resource를 해제한다.

Observed:

- Open 이후 처리를 `try/finally`로 감싸고 `finally`에서 `release()`를 호출하도록 구현했다.
- 실패 경로의 실제 resource 상태를 별도 계측하지는 않았다.

Result: `PASS by code review`

## Day 04 Completion Status

오늘 완료한 범위:

- 최종 System Input과 Analysis Core Input 경계 문서화
- Structured Analysis Result와 Web/TXT Representation 경계 문서화
- Vue 3 + Vite Frontend Technology Decision 기록
- 실제 Video Path 생성과 Validation
- 실행 위치에 독립적인 개발용 Path 구성
- OpenCV Video Open과 `isOpened()` 확인
- `try/finally` 기반 resource 해제

원래 Day 04 Success Gate 중 아직 완료하지 않은 범위:

- Metadata Inspection
- Metadata Validation
- 실제 FPS 관찰과 nominal 60 FPS 판정
- 모든 Decode 가능한 Frame의 Sequential Decode
- 정상 EOF와 Decode Failure 구분
- Human-verified Known Run Start
- 60-second Run Segment Processing
- Segment Completeness Check

따라서 Day 04는 전체 Initial Slice 완료가 아니라 **Video Input Boundary와 Video Open 하위 Slice 완료** 상태로 종료한다.

## Day 05 Handoff

다음 구현은 새로운 Requirement 발굴이 아니라 현재 Video resource를 사용한 Metadata Inspection부터 시작한다.

```text
Video Open
-> Raw Metadata Inspection
   - FPS
   - Width
   - Height
   - Frame Count
-> Metadata Validation
-> observed FPS 기반 최소 지원 규칙 결정
-> Sequential Frame Decode
```

Day 05 첫 실행에서는 Metadata 원본 값을 반올림하거나 정수로 변환하지 않는다. Duration을 확정하지 않으며 Frame Count를 Segment Completeness의 근거로 사용하지 않는다.

## Explicitly Deferred

- FastAPI, Upload API와 Temporary File 구현
- Vue Project 생성과 Frontend 코드
- Endpoint, HTTP Method와 Request/Response Schema
- TXT Writer와 Report Format
- exact Timestamp와 60초 Frame Boundary
- 59.94 FPS 허용 여부와 FPS tolerance
- Automatic Countdown Detection과 Manual Fallback
- Target Detection, Tracking State, Direction, Event와 Metric

## Repository Notes

- Source of Truth 문서에는 System/Input/Output Boundary와 관련 ADR을 반영했다.
- `src/main.py`는 프로젝트 작성자가 직접 구현했다.
- Python Test 코드는 아직 작성하지 않았다.
- Git Commit과 Push는 수행하지 않았다.
- Root의 ignore 파일명을 `gitignore`에서 `.gitignore`로 바로잡았으며, `.venv`와 Raw Video가 ignore되는 것을 확인했다.

## Study Notes

- 최종 사용자의 Web Upload와 Analysis Core의 Local Path는 서로 다른 Input Contract다.
- 상대경로는 Current Working Directory에 의존하지만 `__file__`은 Source File 위치를 기준으로 사용할 수 있다.
- `exists()`와 `is_file()`은 서로 다른 질문에 답한다.
- `VideoCapture` 생성과 `isOpened()` 성공은 구분해야 한다.
- `try/finally`는 성공과 실패 모두에서 resource 정리를 보장한다.
