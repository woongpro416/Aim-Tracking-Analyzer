# Day 13 — OFF_TARGET 구간과 기초 Tracking Metrics

- 날짜: 2026-10-14
- 단계: Phase 3 — Tracking Metrics 진행 중
- 범위: 기존 `tracking_state_sequence`에서 조준 이탈 구간을 묶고 지속 시간과 Run 단위 합계를 계산

## 작업 내용과 결정한 계약

Phase 2의 `ON_TARGET / OFF_TARGET / MISSING` 상태를 그대로 사용한다. 연속된 `OFF_TARGET` Frame만 하나의 `off_target_interval`로 묶는다. `ON_TARGET` 또는 `MISSING`을 만나면 구간을 끝내고, `MISSING` 시간은 조준 이탈 시간에 포함하지 않는다. `MISSING` 종료를 조준 회복 성공으로 해석하지 않는다. 마지막 Frame까지 `OFF_TARGET`이면 종료 경계를 마지막 Frame 번호 + 1로 기록하고 종료 원인을 `RUN_END`로 둔다.

`Event`라는 일반적인 이름보다 분석 대상이 드러나는 `off_target_interval`을 선택했다. 함수·파일·변수·테스트 이름을 이 용어로 맞췄다. Target 하나의 생애를 뜻하는 구간이 아니라, 조준이 Target 밖에 있었던 **연속 관측 구간**이다.

구간은 영상의 절대 Frame 번호를 사용한 `[start_frame_index, end_frame_index_exclusive)`로 표현한다. 종료 원인 `end_reason`은 `ON_TARGET`, `MISSING`, `RUN_END` 중 하나다. Frame 수는 `종료 경계 - 시작 번호`, 지속 시간은 `Frame 수 / fps`다. 예를 들어 Frame 101~102가 모두 `OFF_TARGET`이고 Run이 끝나면 `[101, 103)`, 2 Frame, 60 FPS에서 `2 / 60`초다.

`src/off_target_intervals.py`의 `group_off_target_intervals()`는 각 구간에 시작·종료 경계, 종료 원인, `off_target_frame_count`, `off_target_duration_seconds`를 담는다. `print_interval_summary()`와 Frame별 상태 출력은 결과를 읽기 쉽게 보여주는 개발용 출력이다.

`src/tracking_metrics.py`의 `calculate_off_target_metrics()`는 구간 개수, 전체 OFF_TARGET Frame 수, 전체 지속 시간, 평균 구간 지속 시간을 반환한다. 평균의 분모는 **전체 Frame 수가 아니라 구간 개수**다. 구간이 0개면 합계는 `0`/`0.0`이고, 평균은 관측 대상이 없다는 뜻으로 `None`이다. 예제의 2 Frame 구간과 1 Frame 구간은 총 3 Frame·0.05초이며 평균 구간 시간은 `0.05 / 2 = 0.025`초다.

## 검증한 내용

`tests/test_off_target_intervals.py`에서 Run 마지막 OFF_TARGET Frame 포함, `MISSING`에 의한 분리와 시간 제외, 빈 상태 목록, ON_TARGET만 있는 목록을 검증했다. 사용자가 **4 passed**를 확인했다.

`tests/test_tracking_metrics.py`에서 서로 길이가 다른 두 구간의 합계·평균과 빈 구간 목록의 `None` 평균을 검증했다. 사용자가 **2 passed**를 확인했다. 두 파일은 각각 실행한 결과이며, 오늘 변경 사항 전체를 대상으로 한 통합 회귀 테스트 결과로 합산해 표현하지 않는다.

## 구현 책임과 배운 점

사용자가 `for` 순회, 상태 분기, 구간 시작·종료, Dictionary 추가, Frame 수·지속 시간, Run 합계·평균 계산을 직접 작성하고 샘플과 테스트를 실행했다. Codex는 개념·작은 TODO·오류 리뷰를 제공했고, 요청에 따라 이름 변경, 출력 정리, Metrics 테스트 파일의 반복 코드, 파일 상단 설명과 이번 작업일지를 작성했다.

- `interval_start is None`은 진행 중인 구간이 없다는 뜻이다. Frame 번호 `0`과 구분한다.
- `intervals.append(interval)`처럼 **목록에 Dictionary를 추가**한다. 구간 하나와 구간 목록은 자료형과 역할이 다르다.
- `[시작, 종료)` 경계를 사용하면 Frame 수를 뺄셈으로 구할 수 있고, Run 종료에서도 마지막 Frame을 빠뜨리지 않는다.
- 평균 구간 시간은 전체 시간 / 구간 수이며, 빈 목록에서는 `0`으로 나누지 않고 `None`을 반환한다.

## 남은 검증과 한계

오늘은 Synthetic Sequence와 작은 Metrics 입력까지만 확인했다. Phase 2의 실제 3600 Frame `tracking_state_sequence`를 새 함수에 연결해 **OFF_TARGET 1000 Frame이 구간에 정확히 한 번씩 포함되는지**와 총 시간이 약 `16.667`초인지 확인해야 한다. 전체 회귀 테스트도 새 변경 이후 다시 실행해야 한다. 실제 구간 개수는 Sequence로 계산하기 전까지 적지 않는다.

현재 구간 함수는 입력 상태 목록이 시간순이며 Frame 번호가 연속이고 `fps`가 유효하다는 Phase 2 입력 계약에 의존한다. `MISSING`은 게임 내 Target 전환과 검출 실패를 모두 포함할 수 있으므로 원인을 단정하지 않는다. Recovery, 방향별 분석, Target 식별 및 Tracking Accuracy는 이번 구현 범위에 포함하지 않는다.

다음 세션에서는 저장된 Production 결과로 3600 Frame 정합성을 확인하고, 필요하면 누락된 작은 경계 사례를 보강한 뒤 전체 회귀 테스트를 실행한다.

## 추천 커밋 메시지

```text
feat: add OFF_TARGET intervals and metrics 및 Day13 학습 기록
```
