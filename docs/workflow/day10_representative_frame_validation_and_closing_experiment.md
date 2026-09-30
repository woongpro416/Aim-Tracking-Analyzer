# Day 10 — Representative Frame Validation and Closing Experiment

## Today's Goal and Scope

Day 09에서 미뤘던 대표 프레임의 수동 검증을 먼저 진행했다. 경계 프레임에서 원본 HSV Mask와 Contour 기반 Tracking State가 사람의 판단과 어긋나는 사례가 발견되어, 예정했던 OFF_TARGET Event 및 Duration Metric 구현은 시작하지 않았다.

```text
원본 Frame 수동 판단
-> 원본 / 3×3 / 5×5 Closing Mask 비교
-> Contour 후보와 Tracking State 확인
-> 상단 조각 제외 실험
```

현재 `src/target_detection.py`와 `src/tracking_state.py`의 실제 판정 규칙은 변경하지 않았다. Closing과 상단 조각 제외는 `src/inspect_target_mask.py`에서만 시험했다.

## Primary Coder and AI-assisted Work

Primary Coder는 상태별 첫 등장 인덱스를 저장하는 Dictionary와 순회 로직을 작성했다. 원본 프레임을 직접 추출하고 Crosshair 중앙점과 Target의 관계를 보고 대표 프레임의 정답을 판단했다. `1228`은 ON_TARGET, 바로 다음 `1229`는 OFF_TARGET이며, `926`은 OFF_TARGET, 바로 다음 `927`은 ON_TARGET이라고 판단했다. `764`도 분명한 ON_TARGET으로 확인했다. 상단 후보를 구분하는 `is_top_strip_candidate()`와 첫 pytest 경계 테스트도 직접 작성하고 실행했다.

AI는 `3×3`·`5×5` 비교, Contour와 후보 수 진단, 전체 Run의 두 판정 방식 비교를 수행했다. 사용자가 현재 실험의 마무리 구현을 요청한 뒤 `collect_valid_candidates()`의 상단 조각 제외 조건, 합성 Mask 테스트, 코드 설명 주석과 이 일지를 작성했다. 전체 Run 비교는 AI가 먼저 진행한 진단이며 Primary Coder가 모든 변경 프레임을 수동 라벨링한 작업이 아니다.

## Manual Labels and Representative-frame Result

아래 정답은 원본 화면을 보고 판단한 값이다. `원본`은 현재 실제 검출 방식, 나머지 두 열은 검사 스크립트의 실험 방식이다.

| Frame Index | 수동 정답 | 원본 | 5×5 Closing | 5×5 + 상단 조각 제외 |
|---:|---|---|---|---|
| `356` | ON_TARGET | ON_TARGET | ON_TARGET | ON_TARGET |
| `381` | ON_TARGET | OFF_TARGET | ON_TARGET | ON_TARGET |
| `436` | OFF_TARGET | OFF_TARGET | OFF_TARGET | OFF_TARGET |
| `764` | ON_TARGET | ON_TARGET | MISSING | ON_TARGET |
| `851` | MISSING | MISSING | MISSING | MISSING |
| `926` | OFF_TARGET | OFF_TARGET | OFF_TARGET | OFF_TARGET |
| `927` | ON_TARGET | OFF_TARGET | ON_TARGET | ON_TARGET |
| `1228` | ON_TARGET | OFF_TARGET | ON_TARGET | ON_TARGET |
| `1229` | OFF_TARGET | OFF_TARGET | OFF_TARGET | OFF_TARGET |
| `1380` | OFF_TARGET | OFF_TARGET | OFF_TARGET | OFF_TARGET |

`381`에서는 Crosshair가 만든 Mask 끊김 때문에 원본 Contour가 중앙점을 제외했다. `3×3` Closing은 이 프레임을 여전히 OFF_TARGET으로 판정했고, `5×5` Closing은 중앙점을 Contour 경계에 포함해 ON_TARGET으로 판정했다. 따라서 `pointPolygonTest()`의 경계값 `0`을 곧바로 OFF_TARGET으로 바꾸면 `381`의 오류가 다시 생긴다.

`926`, `1229`, `1380`에서는 Crosshair 그림의 일부가 Target과 겹쳐도 중앙점은 배경 쪽에 있어 OFF_TARGET으로 판단했다. Crosshair 선의 겹침과 판정 기준점의 위치를 구분했다. `851`은 Target이 사라지는 전환 장면으로, MISSING을 OFF_TARGET으로 바꾸지 않았다.

## Closing and Top-strip Candidate Finding

`5×5` Closing은 끊어진 Target Mask를 연결하는 한편, 화면 상단의 작은 청록색 조각도 유효 후보로 키웠다. `764`에서는 면적 기준 `150`을 통과한 후보가 다음 두 개였다.

| 후보 | Bounding Box `(x, y, width, height)` | Contour Area |
|---|---|---:|
| 실제 Target | `(934, 474, 146, 146)` | `16386.5` |
| 화면 상단 조각 | `(1125, 0, 44, 28)` | `172.5` |

현재 검출 계약은 유효 후보가 정확히 하나일 때만 Target을 선택한다. 따라서 `5×5` Closing만 적용하면 `764`가 MISSING이 된다. 실험용 필터에서는 Bounding Box 전체가 화면 상단 `0~29px`에 들어가는 후보를 건너뛴다. `764`의 후보 수는 `2 -> 1`이 되었고, 남은 Contour로 계산한 상태는 ON_TARGET이었다. 위 표의 수동 라벨 10개도 이 실험 방식과 일치했다.

상단 `30px` 규칙은 관찰한 상단 조각에 대한 실험 기준이다. 실제 영상 전체에서 Target이 이 영역에 나타나지 않는다는 계약으로 아직 확정하지 않았다.

## Full-run Comparison: Diagnostic Only

AI가 원본 방식과 `5×5` Closing만 적용한 방식을 60초 Run의 `3,600`프레임에서 자동 비교했다. `188`프레임에서 판정이 달랐다.

| 변경 | Frame Count |
|---|---:|
| OFF_TARGET -> ON_TARGET | `182` |
| ON_TARGET -> MISSING | `2` |
| OFF_TARGET -> MISSING | `4` |

로컬 `outputs/closing_5x5_state_changes.csv`는 두 알고리즘이 **서로 다르게 판정한 인덱스 목록**이다. 정답 라벨 목록이나 개선된 프레임 수가 아니다. MISSING으로 바뀐 6프레임의 추가 후보는 모두 화면 상단 `y=0`에서 시작했지만, 이 사실만으로 `5×5 + 상단 조각 제외`를 전체 Run에 채택하지 않는다. 그 조합의 전체 Run 검증도 아직 하지 않았다.

## Code and Test Changes

- `src/main.py`: 상태별 첫 등장 Frame Index를 한 번씩 기록해 대표 프레임 탐색에 사용한다.
- `src/inspect_target_frame.py`: 검사할 원본 프레임을 추출한다. 현재 설정은 `764`다.
- `src/inspect_target_candidates.py`: 선택된 Target Contour, Bounding Box, Target Center를 얇은 선으로 시각화한다. 현재 설정은 `356`이다.
- `src/inspect_target_mask.py`: 원본·`3×3`·`5×5` Mask를 저장하고 `764`의 상단 후보 제외 전후 개수를 출력한다.
- `tests/test_inspect_target_mask.py`: 상단 `30px` 경계, 합성 Mask의 상단 조각·작은 잡음 제외, 빈 Mask를 검증한다.

pytest 전체 결과는 `15 passed`다. `764` 검사 스크립트에서는 `5×5` 면적 기준 후보 `2개`, 상단 조각 제외 후 `1개`를 확인했다.

## Limitations and Deferred Work

- 현재 `main.py`의 Tracking State와 Day 09 Count는 원본 검출 방식의 결과다. 실험용 Closing과 상단 필터는 반영되지 않았다.
- 수동으로 선택한 10프레임을 확인했지만 전체 `3,600`프레임의 정답을 확보한 것은 아니다.
- 원래 Day 10 계획의 `Contour + Screen Center Crosshair + Tracking State + Frame Index`가 모두 표시된 주석 이미지 생성은 완료하지 않았다. 현재 검사 이미지는 용도별로 분리되어 있다.
- OFF_TARGET Event의 MISSING 분리 기준, Event Duration, Run-level Metric은 설계·구현하지 않았다. Metric을 계산하기 전에 검출 규칙과 수동 검증을 먼저 정리해야 한다.

## Study Notes

- `bbox`는 `(x, y, width, height)`이고, `y + height`로 상단 영역에 완전히 포함되는지 확인한다.
- `continue`는 상단 조각을 후보 목록에 추가하지 않고 다음 Contour로 넘어간다.
- Mask 전처리는 오류를 고칠 수도 있고 새로운 유효 후보를 만들어 MISSING을 일으킬 수도 있다.
- 알고리즘 간 판정 차이는 수동 정답이 아니며, 코드 채택의 근거로 단독 사용하지 않는다.
