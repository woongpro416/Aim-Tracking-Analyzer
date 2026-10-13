# Day 12 — Detection Validation and Phase 2 Closeout

- 현재 단계: **Phase 2 — Target Detection & Trajectory 완료. Phase 3 — Tracking Metrics 준비**
- 이번 우선순위: 기존 Detection 비교의 검증·안정화. 새 알고리즘 도입보다 종료 근거 확보

## Ownership

사용자는 `dict.items()`로 방식별 결과를 조회하고, 중첩 `state_counts`를 초기화한 뒤 Frame 비교·상태 누적·합계 확인을 직접 연결했다. 새 비교 테스트 5개도 직접 실행했다.

기존 파일 검증과 순차 Decode를 재사용하는 부분은 요청에 따라 AI가 연결했다. 이후 Phase 2 마무리에 한해 사용자가 구현 지원 범위를 확대하여, AI가 B 기준 변경 분류·목록 저장·표본 선정·원본 갤러리·수동 Label 보존·관련 테스트를 구현했다.

최종 Detection Contract와 수동 Ground Truth는 사용자가 결정했다. 사용자가 Closing+Top-strip의 Production 반영과 환경 제약을 승인했고, Codex가 최소 정책 반영·코드 정리·Regression·전체 Run 검증·문서화를 수행했다. 새 Shape Threshold는 정하지 않았다.

## Day 12에서 해결한 문제와 작업

Day 12는 한 Frame의 비교 결과를 전체 Run으로 확장하고, 사람이 확인한 정답을 근거로 최종 검출 방식을 선택한 작업이다. 새 알고리즘을 늘리는 대신 현재 영상에서 사용할 규칙과 검증 근거를 확정했다.

| 문제 | 수행한 작업 | 결과·배운 점 |
| --- | --- | --- |
| 세 방식의 상태를 어떻게 누적할지 몰랐다 | 방식별로 ON_TARGET / OFF_TARGET / MISSING을 담는 중첩 Dictionary를 만들고 `state_counts[method_name][state] += 1`을 연결했다 | 특정 Frame이나 MISSING에 고정해서 더하는 것이 아니라 각 방식이 반환한 상태에 자동 누적한다 |
| 상태별 Count가 전체 Frame 수와 맞는지 확인하기 어려웠다 | 방식별 `sum(counts.values())`로 합계를 확인하고 전체 60초 Run에 반복 적용했다 | 세 방식 모두 합계 3600. 후보 수와 상태 Frame 수를 구분했다 |
| 영상 검사·Decode 로직을 처음부터 다시 작성해야 했다 | 기존 파일·FPS·해상도·시작 시각 검증과 순차 Decode를 재사용해 `inspect_run_baselines.py`에 연결했다 | 기존 기반 위에서 비교·집계 핵심을 학습했다. Frame 번호와 실제 이미지 배열도 구분했다 |
| 전체 Count만으로 어느 방식이 실제 화면에 맞는지 알 수 없었다 | 상태 또는 후보 수가 달라진 Frame을 기록하고, 시간대·변경 패턴을 고려해 표본을 선정했다 | 변경 Frame 188개. 기존 10개와 추가 8개를 사람이 확인하여 총 18개 Ground Truth 확보 |
| Closing-only에서 Target이 있는데 MISSING이 늘어났다 | 상단 Noise도 Closing 후 면적 조건을 통과하는 것을 확인하고, bbox 전체가 상단 30px 안에 있는 후보만 제외했다 | Closing-only 14/18, Closing+Top-strip 18/18. 사용자가 현재 HUD에 한정한 최종 정책으로 승인 |
| Production 변경이 Original 비교 기준까지 바꿀 위험이 있었다 | Inspector의 Original을 Closing 전 HSV·면적 기준으로 독립 계산하고, 공통 Mask·Closing·필터 함수는 재사용했다 | 최종 Production을 바꿔도 Original 집계 2136 / 1183 / 281을 보존 |
| 출력만 확인하면 기록 누락이나 잘못된 성공을 놓칠 수 있었다 | `analyze_run()`이 목록과 Summary를 반환하게 하고, 별도 검증 도구로 개수·순서·후보 계약·Label을 검사했다 | Run / Raw / State 각각 3600, 연속 Index 356~3955, 수동 Label 18/18 일치 |
| 실험·실제 분석·Debug 출력이 섞여 있었다 | Production과 Inspector의 책임을 분리하고, 중복 집계·변수·좌표 전체 출력을 정리했다. Frame 번호에서 파일명을 만들도록 수정했다 | 실행 요약은 간결하게 유지하고, 상세 검증은 별도 JSON에 보존. 비교 이미지는 명시적 요청 때만 생성 |
| 정책의 한계와 직접 구현한 범위가 문서에 충분히 드러나지 않았다 | README·요구사항·ADR·검증 계획·보고서에 최종 정책, 선택 근거, 구현 책임과 미검증 범위를 기록했다 | 53개 테스트와 실제 Run 검증을 근거로 Phase 2 종료. Phase 3의 입력 목록 확보 |

코드 파일 삭제나 대규모 구조 변경은 하지 않았다. 생성 이미지 삭제는 별도의 사용자 요청에 따라 수행했으며 영상·Label·검증 JSON은 보존했다. 이번 최종 정리에서는 Shape Filter, Hough Circle, 추가 Threshold 튜닝을 도입하지 않았다.

## 초급 개발자 복습 — Day 12 코드가 하는 일

### 1. Dictionary로 방식과 상태를 찾아 Count를 더한다

`state_counts`는 두 단계로 값을 찾는 Dictionary다. 바깥 Key는 방식 이름이고 안쪽 Key는 상태 이름이다.

```python
for method_name, method_result in comparison_results.items():
    state = method_result["tracking_state"]
    state_counts[method_name][state] += 1
```

예를 들어 현재 Frame에서 `method_name`이 `"closing_only"`, `state`가 `"MISSING"`이면 `state_counts["closing_only"]["MISSING"]`을 1 늘린다. 다음 Frame의 결과가 ON_TARGET이면 ON_TARGET을 늘린다. Frame 764나 MISSING에 고정된 코드가 아니다.

`method_result["valid_candidate_count"]`는 **현재 Frame의 후보 개수**다. 후보가 2개여서 MISSING이어도, 처리한 Frame은 한 장이므로 MISSING Count는 **1** 늘린다. 또한 Dictionary Key는 철자가 정확해야 한다. `valid_candidtae_count`처럼 잘못 쓰면 `valid_candidate_count`와 다른 Key여서 `KeyError`가 발생한다.

### 2. 합계로 빠진 Frame이 없는지 확인한다

```python
for method_name, counts in state_counts.items():
    total = sum(counts.values())
    print(method_name, counts, "합계:", total)
```

`counts.values()`는 한 방식의 세 상태 Count이고, `sum()`은 이를 더한다. 한 방식이 3600장의 Frame마다 상태 하나를 기록했다면 합계도 3600이어야 한다. `print()`를 반복문 밖에 두면 마지막 방식만 출력되므로, 방식별 결과를 보려면 반복문 안에 둔다.

합계만 같다고 누락·중복이 없다고 단정할 수는 없다. 한 Frame을 빠뜨리고 다른 Frame을 두 번 기록해도 합계는 같을 수 있다. 그래서 최종 검증에서는 Frame Index 목록까지 `356~3955`의 연속 번호와 비교했다.

### 3. Frame 번호와 이미지 배열은 다르다

`current_frame_index`는 영상에서 몇 번째 Frame인지 나타내는 정수다. `video_capture.read()`가 반환한 `frame`은 픽셀을 담은 NumPy 배열이다. `compare_frame(frame)`은 이 이미지 배열을 받아 색상·Contour를 분석한다. Frame 번호만 전달해서는 픽셀을 검사할 수 없다.

현재 BGR Frame의 `shape`는 `(1080, 1920, 3)`이다. 순서는 높이·너비·채널이며, HSV Mask는 색상 조건을 통과한 곳을 흰색으로 표시하는 `(1080, 1920)` 단일 채널 배열이다. Closing은 이 흰 영역의 작은 끊김을 연결한다. 동시에 작은 Noise도 커질 수 있어 후보 필터가 필요하다.

### 4. 후보를 결정하는 것과 조준 상태를 판단하는 것을 나눈다

`target_detection.py`는 Target 후보를 고르고, `tracking_state.py`는 선택된 Target과 화면 중앙점의 관계를 판단한다.

- 후보 1개: Target 하나를 선택할 수 있다. 중앙점이 Contour 내부·경계이면 ON_TARGET, 밖이면 OFF_TARGET이다.
- 후보 0개: 선택할 Target이 없다. Center·Contour는 None이고 MISSING이다.
- 후보 여러 개: 어느 후보가 Target인지 결정하지 못했다. 이 경우도 None·MISSING이다.

MISSING은 조준이 Target 밖이었다는 뜻이 아니다. Target을 결정하지 못했기 때문에 조준 상태도 판단하지 못했다는 뜻이다.

Bounding Box `(x, y, width, height)`에서 `y + height`는 아래쪽 제외 경계다. `y=10, height=20`이면 30이므로 상단 필터에서 제외한다. `y=10, height=21`이면 31이므로 상단 영역 밖으로 이어져 유지한다. 실제 Target도 상단에 완전히 들어가면 제거될 수 있다는 한계를 함께 기록했다.

### 5. 사람의 정답과 프로그램 출력을 비교한다

Ground Truth는 사용자가 원본을 보고 확인한 정답이다. 예측을 그대로 정답으로 저장하면 프로그램이 자기 결과와 비교하게 되어 오류를 발견하기 어렵다. 그래서 사용자 Label과 예측을 별도로 보존했다.

53개 테스트는 빈 후보·상단 경계·Label 누락 같은 상황에서 코드가 정한 규칙을 지키는지 확인한다. 실제 3600 Frame 재분석은 목록의 개수·순서·집계가 맞는지 확인한다. 수동 Label 18개 비교는 그 표본에서 화면 판단과 예측이 맞는지 확인한다. 세 검증은 서로 확인하는 대상이 다르다.

18/18은 확인한 표본에서 모두 일치했다는 뜻이다. 다른 영상까지 정확하거나 전체 3600 Frame이 모두 정답이라는 뜻은 아니다.

### 6. 반환값을 만들면 다음 기능에서 재사용할 수 있다

`print()`는 화면에 결과를 보여준다. `return`은 호출한 코드가 사용할 수 있도록 결과를 돌려준다. `analyze_run()`이 Raw Observation과 Tracking State Sequence를 반환하게 만들어, 검증 도구와 Phase 3가 같은 분석 결과를 사용할 수 있게 했다.

Inspector는 여러 방식을 비교하는 개발 도구다. Production은 승인한 한 방식으로 실제 분석을 수행한다. 다음 Phase 3에서는 이 상태 목록으로 연속 OFF_TARGET Event와 Duration을 계산하되, 먼저 MISSING을 만났을 때 Event를 어떻게 처리할지 결정한다.

## Full-run Baselines

동일 입력의 영상 시작 기준 Frame 356~3955를 순차 Decode하여 비교했다. Run 길이는 60초, 입력 FPS는 60.0, Run Frame 수는 3600이다. 전체 영상의 실제 Decode 수는 4124다.

| 방식 | ON_TARGET | OFF_TARGET | MISSING | 합계 |
| --- | ---: | ---: | ---: | ---: |
| Original | 2136 | 1183 | 281 | 3600 |
| Closing-only | 2316 | 997 | 287 | 3600 |
| Closing+Top-strip | 2319 | 1000 | 281 | 3600 |

Original은 Day 09 수치를 재현한다. Count는 상태 분류 집계이며 전체 영상 정확도가 아니다.

## Change Recording — User-selected B Contract

- 세 방식의 Tracking State 또는 Valid Candidate Count가 하나라도 다르면 기록한다.
- 상태 차이가 있으면 `tracking_state_changed`로 분류한다.
- 상태가 모두 같고 후보 수만 다르면 `candidate_count_only`로 분류한다.
- 두 값이 모두 달라도 상태 변경으로 한 번만 집계한다.
- `changed_frames`에는 영상 기준 Index, 영상/Run 시각, 변경 유형, 세 방식의 예측을 보존한다.

실제 변경 Frame은 188개이며 전부 상태 변경이다. 후보 수만 변경된 Frame은 0개다.

| Original | Closing-only | Closing+Top-strip | Frame 수 |
| --- | --- | --- | ---: |
| OFF_TARGET | ON_TARGET | ON_TARGET | 182 |
| ON_TARGET | MISSING | ON_TARGET | 2 |
| OFF_TARGET | MISSING | ON_TARGET | 1 |
| OFF_TARGET | MISSING | OFF_TARGET | 3 |

Run 초반 0~20초, 중반 20~40초, 후반 40~60초의 변경 수는 각각 56, 76, 56이다. 이 시간 구분은 검증 표본 선정에만 사용한다.

## Limited Manual Validation

상태 변경 표본 12개:

`381, 598, 764, 927, 1228, 1541, 2041, 2617, 2755, 3623, 3722, 3933`

이 중 `381, 764, 927, 1228`은 Day 10의 사용자 Label을 재사용한다. 같은 패턴의 연속 Frame에 편중되지 않도록 시간 간격과 변경 패턴을 고려했다. 후보 수만 변경된 Frame이 없어 해당 유형의 표본은 생성하지 않았다.

기존 대표 Frame 10개도 보존한다:

`356, 381, 436, 764, 851, 926, 927, 1228, 1229, 1380`

기존 10개 Label에 대한 예측 일치는 Original 7/10, Closing-only 9/10, Closing+Top-strip 10/10이다. 근거는 [Day 10의 사용자가 확인한 Label](day10_representative_frame_validation_and_closing_experiment.md)이다. 이 표본의 일치를 전체 정확도로 일반화하지 않는다.

**추가로 확인한 Frame 8개:** `598, 1541, 2041, 2617, 2755, 3623, 3722, 3933`.

사용자가 새 8개의 Label을 채팅으로 직접 제공했다. `598, 1541, 2041, 2617, 2755, 3722, 3933`은 ON_TARGET, `3623`은 OFF_TARGET이다. 수동 Label 파일에 기록했으며 알고리즘 예측에서 Label을 채우지 않았다.

기존 10개와 추가 8개를 합친 18개 표본의 비교 결과:

| 방식 | 사용자 Label과 일치 | 불일치 |
| --- | ---: | --- |
| Original | 9/18 | 실제 ON_TARGET인 9개를 OFF_TARGET으로 분류 |
| Closing-only | 14/18 | Target을 확인한 764·2617·3623·3722를 MISSING으로 분류 |
| Closing+Top-strip | 18/18 | 선정 표본에서 불일치 없음 |

이 수동 판단은 알고리즘 간 차이 중 어떤 예측이 실제 화면과 맞는지 확인하기 위한 독립 기준이다. 예를 들어 598은 사용자 ON_TARGET에 대해 Original만 OFF_TARGET이고, 3623은 사용자 OFF_TARGET에 대해 Closing-only만 MISSING이다.

표본은 변경 패턴과 시간대에 따라 선정했으며 무작위 표본이 아니다. 따라서 18/18을 전체 3600 Frame의 정확도로 표현하지 않는다. 원본과 Top-strip 방식이 모두 같은 오판을 하는 경우도 이 제한된 검증만으로 배제할 수 없다.

## Local Evidence and Reproduction

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe src/validate_production_run.py
.\.venv\Scripts\python.exe src/inspect_run_baselines.py
```

생성 결과는 Git에서 제외된 `outputs/day12_validation/`에 저장한다.

- `baseline_comparison.json`: 모든 변경 Index·유형·예측, 집계 및 표본 목록
- `manual_labels.json`: 사용자 Label을 별도로 보존. 재실행 시 기존 Label을 자동 예측으로 덮어쓰지 않음
- `manual_review.md`: 사용자 Label과 예측을 분리한 검증 표
- `review.html`: 원본과 중앙 320×320 Crop 갤러리. 예측은 기본적으로 접혀 있음
- `frames/`: 명시적으로 이미지 추출을 요청했을 때의 원본과 중앙 Crop
- `production_run.json`: 최종 Production 관찰값·상태 목록·Summary
- `production_validation.json`: 실제 Production의 정합성과 사용자 Label 일치 결과

`tests/data/manual_ground_truth.json`은 Git에 포함한 Regression 기준이다. 사용자 Label 18개, 검증 영상의 SHA-256, 기대 상태 집계를 보존한다. 기대 집계는 알고리즘 회귀 기준이며 전체 Frame의 사람 정답을 뜻하지 않는다. Label을 Production 검출의 예외 규칙으로 사용하지 않는다.

원본에는 예측 윤곽선이나 상태를 그리지 않았다. 18개 Crop이 원본의 중앙 픽셀과 같고, 재추출한 기존 10개 Frame이 기존 PNG와 같은 것을 확인했다. HTML의 이미지 참조 36개도 모두 확인했다.

이 이미지 확인은 최초 자료 생성 당시의 기록이다. 사용자 요청으로 기존 이미지 66개를 삭제했다. 원본 영상, Label, 예측 JSON은 보존했고 추가 Label 기록과 최종 검증에서 이미지 추출을 다시 실행하지 않았다. 현재 보고서는 없는 이미지 링크 대신 Label·예측 기록을 표시한다. 비교 도구의 기본 실행은 이미지를 생성하지 않으며 `--export-images`를 지정한 경우에만 추출한다.

## Approved Production Contract

사용자는 **Closing+Top-strip**을 최종 MVP 정책으로 선택했다. 수동 표본 일치가 18/18이고 Closing-only의 추가 MISSING 문제가 확인됐으며, 현재 목표가 이 영상의 안정적인 Tracking State 확보이기 때문이다. Shape-aware 방식의 추가 검증은 Deferred했다.

처리 순서는 `HSV → 5×5 Closing → External Contour → Area ≥ 150 → Top-strip Filter → 단일 후보 선택`이다. HSV 범위와 면적 Threshold는 기존 값을 유지했다.

- Top-strip은 현재 영상의 **1920×1080 HUD 환경에 한정된 MVP 규칙**이다.
- Bounding Box `(x, y, width, height)`의 **`y + height <= 30`**일 때만 제외한다. 전체 사각형이 상단 `[0, 30)`px에 있어야 한다.
- 실제 Target이 이 영역에 완전히 들어가면 오제거할 위험이 있다.
- **18/18은 제한된 수동 표본 결과이며 전체 영상 정확도 100%를 의미하지 않는다.** 정책 선택과 검증에 같은 영상의 선정 표본을 사용했다.
- 다른 해상도, Scenario 및 HUD에서 일반화 성능은 검증하지 않았다. 현재 실행 코드가 모든 다른 해상도를 차단하는 것은 아니다.

후보가 정확히 하나일 때만 Contour·Bounding Box·Center를 선택한다. 후보 0개 또는 여러 개면 위치는 `None`이고 상태는 MISSING이다. ON_TARGET은 중앙점이 Contour 내부 또는 경계, OFF_TARGET은 선택 Contour 외부이며 기존 의미를 유지한다.

## Final Tests and Production Reanalysis

기존 및 추가 Unit / Regression Test는 **53 passed**다. 정상·빈·복수 후보, Closing 복구, 상단 경계, 실제 Target 오제거 위험, None·잘못된 채널, 상태 경계, Original Baseline 보존을 확인했다. 비교 도구의 변경 분류·표본·Label 보존과 검증 도구의 Frame 누락·중복·집계 불일치·Label 누락·충돌도 테스트했다.

실제 `analyze_run()`을 다시 실행하고, 자동 비교 방식이 아닌 최종 Production 출력으로 검증했다.

| 검증 | 실제 결과 |
| --- | --- |
| Detection 정책 | `closing_top_strip` |
| 입력 메타데이터 | 60 FPS, 1920×1080 |
| 전체 실제 Decode | 4124 Frame |
| 분석 Index | 356~3955, 누락·중복 없이 시간 순서 유지 |
| Run / Raw Observation / Tracking State | 각각 3600 |
| 상태 집계 | ON_TARGET 2319 / OFF_TARGET 1000 / MISSING 281, 합계 3600 |
| MISSING 원인 | 후보 없음 281 / 복수 후보 0 |
| 후보와 상태 계약 | 단일 후보는 Center 존재, 미결정은 Center None·MISSING |
| 사용자 Ground Truth | 18/18 일치 |
| Production 반영 후 세 Baseline | 위의 기존 집계와 변경 Frame 188개 재현 |

영상 동일성은 SHA-256 `9197211c8fbade5695db6dc0761b06ad5dffbb315b0f4258ddc6a5de8512a394`로 확인했다. 전체 집계의 재현은 Regression 검증이고 수동 정확도 근거는 확인한 18개로 한정한다.

## File Responsibilities and Cleanup

- `main.py`: 최종 Production 검출로 Raw Observation·Tracking State Sequence·Summary 반환. 반복 Debug 대신 CLI 요약만 출력한다.
- `target_detection.py`: 승인된 정책과 공통 Mask·Closing·후보 필터. 반환값 6개 형식은 유지한다.
- `tracking_state.py`: Contour와 화면 중앙점으로 상태 분류. 판정 코드는 변경하지 않았다.
- `inspect_target_mask.py`: 독립된 Original과 두 Closing Baseline 비교, Shape 관찰. Production 정책 선택 책임은 없다.
- `inspect_run_baselines.py`: 전체 비교·변경 기록·제한된 표본·수동 Label 보존. 기본 실행에서 이미지 생성 없음.
- `validate_production_run.py`: Production 결과의 순서·개수·상태 계약·고정 집계·사용자 Label 검증과 개발용 JSON 저장.
- 기타 Inspector: 원본 추출·픽셀·후보 시각 검사. Frame Index에서 출력 파일명을 만들고 불필요한 Contour 좌표 전체 출력은 줄였다.

Production은 Inspector를 import하지 않는다. `compare_frame()`의 Original은 HSV Mask와 면적 조건으로 직접 계산하여 Production 정책 변경의 영향을 받지 않는다. Closing과 Top-strip 공통 함수는 재사용한다. 단일 Frame의 중복 집계 실습 코드와 중복 변수·출력은 정리했으며 기존 검사 파일을 삭제하거나 대규모 구조를 변경하지 않았다.

## Phase 2 Gate and Phase 3 Boundary

최종 정책 승인, Production 반영, 53개 테스트, 전체 3600 Frame 정합성, 사용자 Ground Truth 18개 비교와 문서화를 완료하여 **Phase 2를 종료한다.** 기록한 중심 좌표와 상태 Sequence를 Phase 3 입력으로 재사용한다.

Phase 3는 MISSING의 Event 경계 역할을 먼저 결정한 뒤, OFF_TARGET Event Grouping과 Duration을 작은 단위로 구현한다. 이번 작업에서는 Event·Metric을 구현하지 않았다. Shape Filter, Hough Circle, 추가 Threshold 튜닝은 진행하지 않았다.

## 추천 커밋 메시지

아래 메시지는 Day 12의 Detection 반영·검증·정리·문서 변경을 함께 커밋할 때의 추천안이다. 실제 커밋은 수행하지 않았다.

```text
feat(detection): Closing+Top-strip 적용 및 Phase 2 검증 완료

- 전체 Run 3600 frames의 Baseline 비교와 Tracking State 정합성 검증
- manual Ground Truth 18개와 Production 결과 일치 확인
- Production/Inspector 책임 분리 및 debug 출력 정리
- Unit/Regression tests 53 passed와 README·Day12 작업일지 기록
- 현재 HUD 환경 제약과 Shape Filter Deferred 명시
```

## Study Notes

- 직접 작성한 상태 집계 로직을 전체 Run에 연결하고 합계 3600을 확인했다.
- B 기준으로 상태 또는 후보 수 차이를 기록하며, 상태 변경을 우선해 중복 집계를 피했다.
- 자동 예측, 기존 사용자 Label, 미검증 표본을 분리했다.
- 사용자가 승인한 Closing+Top-strip을 Production에 반영하고 53개 테스트와 실제 Run 검증을 통과했다.
- 18/18 표본 일치와 전체 집계 재현을 구분하며, 상단 실제 Target 오제거·환경 의존성을 한계로 기록했다.
