# Day 11 — Detection Baseline Comparison and Shape Features

## Today's Goal and Completion Status

- 기록일: 2026-10-02
- 현재 단계: Phase 2 — Target Detection & Trajectory 진행 중
- 오늘 완료한 범위: 세 Baseline의 단일 Frame 비교 함수, Shape Feature 계산 및 관찰, 코드 설명 주석
- 아직 완료하지 않은 범위: 최종 Detection Contract 선택, Production 반영, Phase 2 종료

Day 10에서 5×5 Closing이 끊긴 Target Mask를 복구하는 동시에 상단 Noise도 유효 후보로 만들 수 있음을 확인했다. 오늘은 Original / Closing-only / Closing+Top-strip을 독립된 조건으로 비교하고, 위치 규칙의 대안으로 Target 자체의 형상을 관찰했다.

처음 계획했던 Phase 2 종료와 OFF_TARGET Event 구현까지 진행하지 않았다. Python의 목록, 함수 반환값, Dictionary와 후보 선택 순서를 작은 단위로 학습한 뒤, 비교 함수에 세 방식을 담는 지점에서 작업을 마무리했다.

## Working Method and Ownership

사용자는 Primary Coder로서 Frame 크기와 중앙점 계산, 검출 결과 Tuple 받기, 후보 목록과 선택 결과 분리, Aspect Ratio·Circularity 계산, Dictionary 구성과 조회를 단계별로 작성하고 실행 결과를 전달했다. 실제 Target과 상단 Noise의 수치도 직접 확인했다.

AI는 개념 설명, TODO 제시, 오류 원인 Review를 보조했다. 코드가 길어져 직접 수정을 요청한 이후에는 Closing-only의 수집·선택 순서 수정, Top-strip 결과 추가, 비교 함수와 출력 연결, 중복 출력 정리, 합성 테스트 5개 작성, 코드 주석과 문서 정리를 수행했다.

오늘은 사용자의 요청에 따라 AI가 프로젝트 코드 실행, import 검증, 컴파일 또는 테스트를 수행하지 않았다. 아래의 새 실행 결과는 사용자가 검사 스크립트를 직접 실행해 전달한 출력이다.

## Baseline Conditions

| 방식 | 실제 처리 순서 | 위치 조건 |
|---|---|---|
| Original | HSV Mask → Contour 추출 → Area Filter → 단일 후보 선택 | 없음 |
| Closing-only | HSV Mask → 5×5 Closing → Contour 추출 → Area Filter → 단일 후보 선택 | 없음 |
| Closing+Top-strip | HSV Mask → 5×5 Closing → Contour 추출 → Area Filter → Top-strip Filter → 단일 후보 선택 | 사각형 전체가 상단 30px 안에 있으면 제외 |

OpenCV 코드에서는 Contour를 먼저 얻어야 그 면적과 Bounding Box를 계산할 수 있다. 따라서 표에는 실제 코드의 Contour 추출 순서를 표시했다.

두 Closing 방식은 같은 5×5 Closing Mask를 사용한다. Closing-only는 면적 조건만 통과한 후보를 별도 목록에 모은다. `collect_valid_candidates()`에는 면적과 Top-strip 조건이 함께 들어 있으므로 Closing+Top-strip에서만 사용한다. 이 함수는 새로운 목록을 반환하며 Closing-only의 후보 목록을 수정하지 않는다.

Top-strip의 `y + height <= 30`은 현재 Noise를 관찰해 만든 실험 기준이다. Target이 이 영역에 나타나지 않는다는 Domain Contract로 확정하지 않았다.

## Shared Candidate and Tracking State Contract

- 유효 후보가 정확히 하나일 때만 해당 Contour를 선택한다.
- 후보가 없거나 여러 개이면 선택된 Contour는 `None`이다.
- 후보 목록은 그대로 보존하고, 선택 결과는 별도 변수에 저장한다.
- 선택된 Contour가 없으면 `MISSING`이다.
- 선택된 Contour의 내부 또는 경계에 화면 중앙점이 있으면 `ON_TARGET`, 밖에 있으면 `OFF_TARGET`이다.
- `MISSING`은 조준 실패를 뜻하는 `OFF_TARGET`과 구분한다.

## Comparison Function and Dictionary

`src/inspect_target_mask.py`의 `compare_frame(frame)`은 출력이나 파일 저장 없이 다음 두 단계의 Dictionary를 반환한다.

```python
{
    "original": {
        "valid_candidate_count": 1,
        "tracking_state": "ON_TARGET",
    },
    "closing_only": {
        "valid_candidate_count": 2,
        "tracking_state": "MISSING",
    },
    "closing_top_strip": {
        "valid_candidate_count": 1,
        "tracking_state": "ON_TARGET",
    },
}
```

위 숫자는 764번 Frame의 실제 관찰값이다. 바깥 Key는 비교 방식, 안쪽 Key는 결과의 의미다. Tuple의 반환 순서를 외우는 대신 `result["closing_only"]["tracking_state"]`처럼 이름으로 조회할 수 있다.

검사 스크립트의 `main()`은 이미지를 읽고 비교 함수를 한 번 호출해 결과를 출력한다. Shape 관찰과 Mask 저장도 담당한다. Shape 관찰용 후보는 Top-strip 적용 전에 다시 모으므로 상단 Noise의 값도 확인할 수 있다. 현재는 Mask 저장·Shape 관찰을 위해 일부 전처리를 다시 수행하며, 이 단순한 실험 구조를 유지한다.

## User-confirmed Frame 764 Result

- 입력 크기: 높이 `1080`, 너비 `1920`
- Crosshair 중심점: `(960, 540)`

| 방식 | 유효 후보 수 | Tracking State |
|---|---:|---|
| Original | 1 | ON_TARGET |
| Closing-only | 2 | MISSING |
| Closing+Top-strip | 1 | ON_TARGET |

Closing-only에서는 실제 Target과 상단 조각이 모두 면적 기준을 통과했다. 단일 Target을 결정하지 못해 MISSING이 됐다. Top-strip을 적용하면 상단 조각이 제외되어 Target 하나가 남았다.

이 결과는 새 비교 함수가 764번 Frame에서 기대한 결과를 반환한다는 실행 확인이다. 전체 영상의 정확도 또는 최종 정책 채택 근거로 단독 사용하지 않는다.

## Shape Feature Study

### Aspect Ratio

`calculate_aspect_ratio(bbox)`는 `(x, y, width, height)`에서 `width / height`를 계산한다. 너비 또는 높이가 0 이하이면 `ValueError`를 발생시킨다.

`1.0`이면 너비와 높이가 같다. 정사각형도 같은 비율이므로 이것만으로 원형이라고 판단하지 않는다. 계산값은 `print()`로 보여주는 것과 별개로 `return`으로 호출한 코드에 전달한다.

### Circularity

`calculate_circularity(contour)`는 다음 값을 사용한다.

```text
Area = cv2.contourArea(contour)
Perimeter = cv2.arcLength(contour, True)
Circularity = 4 × π × Area / Perimeter²
```

`True`는 닫힌 윤곽선의 둘레를 계산한다는 뜻이다. 둘레가 0 이하이면 계산을 진행하지 않는다. 이상적인 원의 값은 1이지만 실제 픽셀 Contour에서는 값이 달라질 수 있다.

### Observed Candidates

아래 값은 사용자가 764번 Frame의 Closing-only 후보에서 확인한 결과다. 비율·둘레·원형도는 읽기 쉽게 소수점 여섯 자리로 표시했다.

| 후보 | Bounding Box `(x, y, w, h)` | Aspect Ratio | Area | Perimeter | Circularity |
|---|---|---:|---:|---:|---:|
| 실제 Target | `(934, 474, 146, 146)` | 1.000000 | 16386.5 | 531.379724 | 0.729266 |
| 상단 Noise | `(1125, 0, 44, 28)` | 1.571429 | 172.5 | 174.669047 | 0.071050 |

이 두 후보에서는 Shape 값의 차이를 관찰했다. 다른 크기의 Target, 경계 장면, 조준선이 가린 Target에서도 구분에 도움이 되는지는 아직 검증하지 않았다. Shape Threshold와 Shape Filter는 구현·확정하지 않았다. Hough Circle은 계속 보류한다.

## Python Review and Corrections

| 학습 중 문제 | 원인과 정리 |
|---|---|
| Frame 중앙점 계산 | `frame.shape[:2]`는 Tuple이므로 높이와 너비로 나눈 뒤 각각 `// 2`로 계산했다. |
| Aspect Ratio 함수의 반복 호출 | 함수 안에서 자기 자신을 호출하는 대신 전달받은 bbox를 네 변수로 받았다. |
| 비율 출력 뒤 `None`이 표시됨 | 화면 출력만으로 값이 반환되지 않는다. 계산한 비율을 `return`했다. |
| 후보 수 비교와 선택 | 숫자 값 비교에는 `==`를 사용하며, 목록을 모두 모은 뒤 선택했다. |
| 후보 선택 중 중복 append 또는 조기 종료 | 선택할 Contour는 별도 변수에 저장하고, 함수 전체를 중간에 `None`으로 반환하지 않도록 정리했다. |
| `UnboundLocalError` | Tracking State를 계산하기 전에 Dictionary에서 참조했다. 계산 후 결과를 구성하도록 순서를 정리했다. |
| 같은 결과가 반복 출력됨 | 개별 출력·표·Dictionary 출력이 겹쳐 있었다. 비교 결과는 `pprint()`로 한 번만 출력한다. |

## Files and Comments

| 파일 | 오늘 작업한 내용 |
|---|---|
| `src/inspect_target_mask.py` | Shape 계산 함수, 세 방식의 비교 Dictionary, 출력 연결 및 중복 출력 정리. 단락별 입력·계산·선택·반환·저장 역할을 주석으로 설명했다. |
| `tests/test_compare_frame.py` | 비교 조건과 빈 후보·단일 후보·복수 후보·상단 Noise를 검사하는 합성 테스트 5개를 작성하고 각 준비/호출/확인 단락을 설명했다. |
| `src/main.py` | 기존 Raw Observation, Tracking Sequence, 시간 범위, 상태 집계, 최초 ON_TARGET 경계의 역할을 주석으로 보강했다. 검출 및 상태 판정 로직은 변경하지 않았다. |
| `README.md` | Day 11까지 실제 구현, 역할 분담, 데이터 흐름, 검증 기록, 한계와 실행 방법을 프로젝트 소개 형식으로 정리했다. |

`src/target_detection.py`와 `src/tracking_state.py`의 Production 규칙은 변경하지 않았다.

## Testing and Validation Status

| 항목 | 현재 확인 상태 |
|---|---|
| 비교 함수의 764번 Frame 출력 | 사용자가 직접 실행하고 세 방식의 결과를 확인함 |
| Aspect Ratio·Circularity 관찰 | 사용자가 Target과 Noise의 값을 확인함 |
| 기존 자동 테스트 | Day 10의 기록은 `15 passed`; 오늘 다시 실행하지 않음 |
| 새 비교 함수 테스트 5개 | 작성 완료, 미실행 |
| 전체 3,600 Frame의 세 Baseline 비교 | 미실행 |
| Shape Filter와 Top-strip의 비교 | 미구현·미검증 |
| 최종 정책 반영 후 Regression | 정책 선택 전이므로 미진행 |

새 테스트는 후보 없음, 정상 후보 하나, 모호한 후보 여러 개, Top-strip 조건의 독립성, 상단 Noise만 제외하고 후보가 없어지는 상황을 다룬다. 합성 테스트로 실제 영상의 Shape 임계값이 검증되는 것은 아니다.

## Next Slice

1. 기존 Run 구간과 순차 디코딩 조건을 재사용하는 실험용 전체 Run 비교를 작성한다. 각 Frame에 `compare_frame(frame)`을 호출하고 세 방식의 상태 수·후보 수·변경 인덱스를 기록한다. 실행은 사용자가 수행한다.
2. 변경 유형과 영상 내 시간 위치를 나눠 대표 Frame 약 10~20개를 고른다. 새 MISSING, 경계 복구, 정상 유지 사례를 포함하고 사용자가 원본 화면으로 수동 Label을 정한다.
3. Top-strip 적용 전 Target/Noise의 Shape 값을 더 모은다. 관찰값을 설명한 뒤 사용자가 임계값을 선택한다. 임계값 선택에 사용하지 않은 Frame도 일부 확인한다.
4. `Closing+Shape`를 추가해 `Closing+Top-strip`과 비교한다. 필요성이 확인된 경우에만 `Closing+Shape+제한적인 Top-strip`을 검토한다.
5. 수동 Label 일치, Domain Feature, 위치 의존성, Closing Noise 제거, 실제 Target 오제거, 코드 단순함을 함께 보고 최종 정책을 선택한다.
6. 선택 후에만 Production에 반영한다. 사용자가 Regression Test와 전체 Run을 실행해 `ON_TARGET + OFF_TARGET + MISSING = 3600`, `Tracking State 수 = Raw Observation 수 = Run Frame 수`를 확인한다.
7. 근거와 한계를 문서화하고 Phase 2를 종료한다. 이후 MISSING의 Event 경계 역할을 선택한 뒤 OFF_TARGET Event Grouping과 Duration으로 넘어간다.

가장 작은 다음 TODO는 현재 한 Frame의 결과 Dictionary에서 방식 이름·후보 수·상태를 꺼내는 짧은 반복문을 작성하는 것이다. 새 문법이 필요하면 먼저 설명한 뒤 이 반복문을 전체 Run 비교에 연결한다. 큰 비교 Framework나 Class hierarchy는 만들지 않는다.

### Next-session Success Levels

- Minimum Success: 전체 Run의 세 Baseline 비교 결과를 얻고 수동 검증할 Frame 목록을 정한다.
- Good Success: 수동 Label과 추가 Shape 값을 관찰해 Shape Filter의 첫 비교 조건을 선택한다.
- Bonus: 충분한 근거가 모인 경우 정책을 선택하고 반영·Regression·전체 Run 정합성 확인까지 진행한다. 시간 때문에 확인 단계를 생략하지 않는다.

## Study Notes

- 후보 목록을 만드는 단계와 하나를 선택하는 단계는 분리한다.
- 후보 수 `0`, 빈 목록 `[]`, 선택 결과 `None`, 상태 `MISSING`은 서로 다른 표현이다.
- Dictionary는 방식 이름과 결과의 의미를 Key로 표현하며, `return`과 화면 출력은 역할이 다르다.
- Shape 값 하나와 한 Frame의 성공만으로 검출 정책을 확정하지 않는다.
- 직접 구현·실행한 부분과 AI 도움으로 수정·문서화한 부분을 구분해 기록한다.

## Recommended Commit Message

```text
feat: add 3-way detection comparison and Day11 학습·README 정리
```
