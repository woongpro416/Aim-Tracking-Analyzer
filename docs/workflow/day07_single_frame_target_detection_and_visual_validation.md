# Day 07 — Single-frame Target Detection and Visual Validation

## Today's Goal

Day 07에서는 Phase 2의 첫 번째 Slice로 실제 Run Segment 내부의 단일 프레임에서 타겟 영역을 검출하고, 검출 결과를 사람이 확인할 수 있는 상태까지 구현했다.

```text
Run 내부 대표 프레임
-> BGR/HSV 픽셀 관찰
-> HSV Binary Mask
-> External Contour Candidate
-> 최소 Area Filter
-> Detection Decision
-> Bounding Box와 Center
-> Visual Validation
```

전체 60초 Run Processing, Frame-to-frame Tracking, Missing Observation과 Target Trajectory는 Day 08 이후로 넘겼다.

## Primary Coder and AI-assisted Work

Primary Coder는 대표 프레임 추출, 픽셀 관찰, Mask 생성, Contour Candidate 측정, Area Filter, Bounding Box와 Center 계산, 시각화 흐름을 작은 단계로 직접 작성하고 실행 결과를 확인했다.

AI는 각 단계의 OpenCV 함수와 자료형, 좌표계, 반복문과 상태 변수의 의미를 설명하고 코드 Review 및 실제 이미지 검증을 보조했다. 작업 후반의 출력 문구 정리, 공통 Mask 로직 통합, 프레임 단위 `detect_target(frame)` 함수 분리와 추가 프레임 진단은 AI-assisted 변경으로 진행했다.

## Representative Frame

기존 Sequential Decode 구조와 0-based Frame Index 계약을 유지해 `woong01.mp4`의 frame `1256`을 대표 프레임으로 저장했다. Video Seek은 추가하지 않았다.

| Observation | Result |
|---|---:|
| Frame Index | `1256` |
| Human-readable Order | `1257번째` |
| Recording-relative Time | `20.933333333333334초` |
| Run-relative Time | `15.0초` |
| Frame Shape | `(1080, 1920, 3)` |
| Frame dtype | `uint8` |

Run 시작 frame `356`에서 `900` frames 뒤이므로 Run-relative time은 `15초`다.

```text
(1256 - 356) / 60 FPS = 15 seconds
```

대표 프레임은 `outputs/representative_frame_1256.png`로 저장했다.

## Pixel and Color Observation

대표 프레임을 BGR에서 HSV로 변환한 뒤 타겟 내부, 회색 배경과 청록색 UI의 고정 좌표를 관찰했다.

| Sample | BGR | HSV |
|---|---|---|
| Target Left Inner | `[252, 254, 31]` | `[90, 224, 254]` |
| Target Upper Inner | `[253, 255, 58]` | `[90, 197, 255]` |
| Target Lower Inner | `[249, 231, 34]` | `[93, 220, 249]` |
| Gray Background | `[148, 143, 142]` | `[115, 10, 148]` |
| Cyan UI Bar | `[212, 232, 82]` | `[86, 165, 232]` |

관찰 결과는 다음과 같다.

- 타겟은 Blue와 Green이 높고 Red가 낮은 cyan 계열이다.
- 타겟 내부는 조명과 음영 때문에 BGR 값이 완전히 균일하지 않다.
- 타겟의 Hue는 대표 샘플에서 `90~93`으로 비교적 안정적이었다.
- 회색 배경은 Saturation이 `10`으로 매우 낮아 타겟과 분리 가능했다.
- 청록색 UI는 Target과 Hue가 가까워 Hue만으로는 False Positive 가능성이 있었다.
- 이미지 좌표는 `(x, y)`로 표현하지만 NumPy 접근은 `frame[y, x]`를 사용했다.

## Initial Binary Mask

첫 Mask는 다음 HSV 범위로 생성했다.

```text
LOWER_HSV = [85, 180, 0]
UPPER_HSV = [100, 255, 255]
```

`cv2.inRange()` 결과는 `(1080, 1920)` shape의 단일 채널 `uint8` 배열이며, 범위 안의 픽셀은 `255`, 범위 밖의 픽셀은 `0`으로 표현됐다.

대표 frame `1256`에서는 회색 배경과 UI 대부분이 제거됐고 타겟 본체가 흰색 연결 영역으로 유지됐다. Crosshair와 색상 차이 때문에 타겟 내부에 작은 검은 구멍이 존재했지만 외부 실루엣은 유지됐다.

## Contour Candidate and Minimum Area Filter

Mask에서 다음 옵션으로 외부 Contour를 추출했다.

```text
cv2.RETR_EXTERNAL
cv2.CHAIN_APPROX_SIMPLE
```

`RETR_EXTERNAL`을 사용해 Target 내부의 검은 구멍은 별도 Candidate로 만들지 않고 가장 바깥쪽 외곽선만 관찰했다.

초기 frame `1256`에서는 다음 결과를 얻었다.

| Observation | Result |
|---|---:|
| Total Contour Candidates | `45` |
| Main Target Contour Area | `20799.0` |
| Main Bounding Box | `(856, 468, 164, 164)` |
| Other Candidate Areas | 대부분 `0.0` |

1픽셀 또는 선 형태의 Contour는 픽셀이 존재하더라도 내부를 감싸는 기하학적 면적이 없어 `contourArea()`가 `0.0`이 될 수 있다.

관찰 결과를 근거로 면적이 없는 Noise만 제거하는 최소 Filter를 적용했다.

```text
MIN_CANDIDATE_AREA = 1.0
```

Candidate index는 Contour list 내부의 일시적인 순서일 뿐 Target ID로 사용하지 않았다. 면적 Filter를 통과한 Candidate가 정확히 하나일 때만 현재 프레임의 타겟을 결정했다.

## Additional-frame Observation and HSV Revision

프레임 단위 로직을 frame `656`, `1256`, `2456`에 적용해 한 프레임에서만 우연히 성공한 규칙인지 확인했다.

초기 `V >= 0` 규칙에서는 어두운 우주 배경이 Target과 비슷한 Hue와 Saturation을 가져 다수의 Candidate로 남았다.

| Frame | Target V Sample | Dark Space V Sample | Initial Valid Candidate Count |
|---:|---:|---:|---:|
| `656` | `232` | `23~51` | `84` |
| `2456` | `237` | `28` | `13` |

Target과 어두운 배경의 실제 밝기 차이를 근거로 V 하한을 추가했다.

```text
LOWER_HSV = [85, 180, 180]
UPPER_HSV = [100, 255, 255]
```

`180`은 관찰한 Target 최저 V 값보다 충분히 낮고, 어두운 우주 배경 V 값보다 높은 초기 실험 경계다. 위치 Filter나 복잡한 Shape Filter를 추가하지 않고 실제 원인이었던 어두운 배경 픽셀을 Mask 단계에서 제외했다.

최종 범위를 적용한 결과는 다음과 같다.

| Frame | Total Contours | Valid Candidates | Bounding Box | Center |
|---:|---:|---:|---|---|
| `656` | `12` | `1` | `(832, 432, 134, 134)` | `(899.0, 499.0)` |
| `1256` | `17` | `1` | `(856, 468, 164, 164)` | `(938.0, 550.0)` |
| `2456` | `6` | `1` | `(950, 490, 74, 70)` | `(987.0, 525.0)` |

세 프레임은 Target 크기와 배경이 서로 달랐으며 모두 유효 Candidate가 하나로 정리됐다. 이는 전체 Run 안정성의 증명이 아니라 Day 07 범위의 추가 sanity check다.

## Detection Result

현재 임시 Detection Decision은 다음과 같다.

```text
valid_candidate_count == 1
-> target_detected = True

valid_candidate_count == 0 or >= 2
-> target_detected = False
```

`False`는 Target이 반드시 존재하지 않는다는 뜻이 아니다. `0`은 후보 미검출이고 `2개 이상`은 하나로 결정할 수 없는 상태다. 이 구분은 Day 08의 Missing Observation 처리에서 다시 다룰 예정이다.

Target Center는 정밀한 형상 중심이나 Crosshair 위치가 아니라 Bounding Box의 대표 중심으로 계산했다.

```text
center_x = x + width / 2
center_y = y + height / 2
```

frame `1256`의 결과는 다음과 같다.

```text
Bounding Box = (856, 468, 164, 164)
Target Center = (938.0, 550.0)
Screen/Crosshair Center = (960, 540)
```

Target Center와 Domain Contract의 고정 Crosshair 위치는 서로 다른 좌표다. Day 07에서는 두 점의 거리나 On-target Metric을 계산하지 않았다.

## Visual Validation

원본 대표 프레임 복사본에 다음 정보를 표시했다.

- 초록색 Target Bounding Box
- 빨간색 Target Center

OpenCV Drawing 함수가 입력 배열을 직접 변경하므로 원본 보존을 위해 `frame.copy()`에 그렸다. 시각화 결과는 `outputs/target_detection_1256.png`로 저장했으며 실제 Target 영역과 일치함을 사람이 확인했다.

## Source Structure

### `src/inspect_target_frame.py`

- Video를 index `0`부터 순차 디코딩
- 대표 frame `1256` 선택
- shape, dtype과 recording-relative time 출력
- 원본 대표 프레임 저장

### `src/inspect_target_pixels.py`

- 대표 프레임 로드
- BGR에서 HSV로 변환
- Target, Background와 유사 UI의 고정 좌표 픽셀 관찰

### `src/inspect_target_mask.py`

- 공통 `create_target_mask(frame)` 호출
- Mask shape, dtype과 HSV 범위 출력
- Binary Mask 이미지 저장

### `src/inspect_target_candidates.py`

- 대표 BGR Frame을 프레임 단위 Detector에 전달
- Candidate Count, Detection Decision, Bounding Box와 Center 출력
- 원본 프레임에 Bounding Box와 Center를 표시해 저장

### `src/target_detection.py`

- HSV 범위와 최소 Candidate Area의 단일 Source of Truth
- BGR 입력 shape 검증
- `create_target_mask(frame)`으로 HSV Mask 생성
- `detect_target(frame)`으로 Contour, Area Filter와 Detection Result 계산
- 파일 경로에 의존하지 않는 프레임 단위 책임 제공

현재 `DetectionResult`는 Day 08 연결을 위한 가벼운 내부 tuple이며 영구 API DTO로 확정하지 않았다.

## Validation Status

### Completed

- Run 내부 대표 프레임 순차 추출
- BGR/HSV Target Pixel 관찰
- Gray Background와 Cyan UI 비교
- HSV Binary Mask 생성
- External Contour Candidate 추출
- 실제 면적 관찰에 근거한 최소 Area Filter
- Target detected 여부, Bounding Box와 Center 계산
- 원본 프레임 Visual Validation
- 서로 다른 크기와 배경을 가진 세 프레임에 대한 추가 확인
- BGR Frame을 직접 입력받는 프레임 단위 Detector 분리

## Limitations

- 전체 Run이 아니라 세 개의 대표 프레임에서만 확인했다.
- HSV 범위는 현재 `woong01.mp4`의 화면 색상과 조명에 맞춘 초기 규칙이다.
- `MIN_CANDIDATE_AREA = 1.0`은 점 형태 Noise 제거 목적이며 최종 Target 크기 계약이 아니다.
- 유효 Candidate가 여러 개이면 실제 Target이 포함돼 있어도 현재 결과는 `False`다.
- Bounding Box Center는 정확한 Contour centroid 또는 실제 게임 엔진 Hit Area 중심이 아니다.
- Crosshair는 검출하지 않고 화면 중심 계약을 유지한다.
- Morphology, Tracking, Missing Observation과 Trajectory는 구현하지 않았다.

## Day 08 Handoff

Day 08에서는 기존 Run Segment Sequential Decode loop 안에서 각 BGR Frame을 `detect_target(frame)`에 전달할 수 있다.

```text
Run Segment Frame
-> detect_target(frame)
-> detected / bounding box / center / candidate counts
-> Target Observation 또는 Missing Observation
-> Frame Index와 Time을 포함한 Center Sequence
```

전체 Run에서 실패 유형과 Candidate 수를 관찰한 뒤에만 Threshold 또는 Filter 추가 여부를 결정한다. 아직 Direction, Recovery, On-target Metric이나 Run Comparison으로 확장하지 않는다.

## Study Notes

- Mask의 흰색 픽셀은 확정 Target이 아니라 색상 조건을 통과한 후보 픽셀이다.
- Contour Candidate와 Filter를 통과한 Valid Candidate는 서로 다른 상태다.
- Hue와 Saturation이 비슷한 어두운 배경은 Value 하한으로 분리할 수 있었다.
- Target Center는 현재 Bounding Box 중심이며 Crosshair 또는 화면 중심과 다르다.
- 프레임 단위 Detector는 파일 경로가 아니라 BGR Frame을 입력받아 Day 08 loop에서 재사용할 수 있다.
