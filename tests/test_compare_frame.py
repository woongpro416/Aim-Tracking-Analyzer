# 비교 함수가 반환해야 할 후보 수와 상태를 합성 이미지로 확인하는 테스트다.
# Path로 src 위치를 찾고 sys.path에 넣어, 현재 프로젝트의 단순한 파일 구조에서 함수를 import한다.
import sys
from pathlib import Path

# 원본 영상을 사용하지 않고, 작은 BGR 이미지에 도형을 그려 각 상황을 재현한다.
import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

# import만으로 검사 스크립트의 main()이 실행되지는 않는다.
from inspect_target_mask import compare_frame


def test_empty_frame_returns_zero_candidates_and_missing():
    # 후보가 없어도 함수가 결과 Dictionary를 반환해야 한다.
    # 준비: (높이, 너비, 채널)=(100, 100, 3)인 검은 이미지다. frame 자체가 None인 경우와 다르다.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # 검사 대상 함수에 이미지를 전달해 세 방식의 결과를 받는다.
    result = compare_frame(frame)

    # 확인: 방식 이름으로 결과를 조회한다. 후보 수 0은 숫자이며, 상태는 MISSING 문자열이다.
    for method_name in ("original", "closing_only", "closing_top_strip"):
        assert result[method_name] == {
            "valid_candidate_count": 0,
            "tracking_state": "MISSING",
        }


def test_single_target_is_not_added_twice():
    # 후보 선택 때문에 같은 Contour가 목록에 중복 추가되는 오류를 막는다.
    # 준비: 화면 중앙의 청록색 원 하나다. 색상은 OpenCV의 (B, G, R) 순서로 지정한다.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (255, 255, 0), -1)

    # 검사 대상 함수가 후보를 수집하고, 후보가 하나인지 판단하도록 한다.
    result = compare_frame(frame)

    # 확인: 세 방식 모두 후보가 하나이고 화면 중앙점이 원 안에 있다.
    for method_name in ("original", "closing_only", "closing_top_strip"):
        assert result[method_name] == {
            "valid_candidate_count": 1,
            "tracking_state": "ON_TARGET",
        }


def test_multiple_candidates_return_missing_instead_of_none():
    # 후보를 모두 모은 뒤 판단하며, 모호해도 함수 전체가 None을 반환하지 않는다.
    # 준비: 상단 영역 밖에 충분히 떨어진 원 두 개를 배치해, Closing 후에도 두 후보가 남게 한다.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (25, 50), 10, (255, 255, 0), -1)
    cv2.circle(frame, (75, 50), 10, (255, 255, 0), -1)

    # 검사 대상 함수를 호출한다. 첫 후보만 보고 조기에 결론 내리지 않아야 한다.
    result = compare_frame(frame)

    # 확인: 후보 목록에는 두 개가 남지만, 선택된 Contour는 None이므로 세 상태 모두 MISSING이다.
    for method_name in ("original", "closing_only", "closing_top_strip"):
        assert result[method_name] == {
            "valid_candidate_count": 2,
            "tracking_state": "MISSING",
        }


def test_top_strip_filter_does_not_change_closing_only_result():
    # 중앙 Target과 상단 Noise를 배치한다. 상단 제외는 Top-strip 방식에만 적용한다.
    # 준비: 상단 사각형의 Contour 면적은 19×9=171로 면적 기준 150을 통과한다.
    # Bounding Box의 아래쪽 끝은 10px이므로, Top-strip 조건을 확인하는 합성 Noise로 사용한다.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(frame, (50, 50), 10, (255, 255, 0), -1)
    cv2.rectangle(frame, (5, 0), (24, 9), (255, 255, 0), -1)

    # 같은 이미지를 세 방식에 전달해 필터 조건의 차이를 비교한다.
    result = compare_frame(frame)

    # 확인: 상단 제거가 Closing-only에 섞이면 아래 후보 수 2 조건이 깨진다.
    assert result["closing_only"] == {
        "valid_candidate_count": 2,
        "tracking_state": "MISSING",
    }
    # Top-strip 방식에서는 상단 사각형만 제외되고 중앙 Target은 남아야 한다.
    assert result["closing_top_strip"] == {
        "valid_candidate_count": 1,
        "tracking_state": "ON_TARGET",
    }


def test_only_top_strip_noise_leaves_no_selected_target():
    # 면적을 통과해도 상단 조각을 제외한 뒤에는 선택할 Target이 없다.
    # 준비: 중앙 Target 없이 상단 Noise만 있는 상황이다.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(frame, (5, 0), (24, 9), (255, 255, 0), -1)

    # 상단 후보를 제외한 뒤 후보가 없는 상황도 결과 Dictionary에 담아야 한다.
    result = compare_frame(frame)

    # 확인: Closing-only는 Noise를 유일한 후보로 선택하지만 화면 중앙점은 그 밖에 있다.
    assert result["closing_only"] == {
        "valid_candidate_count": 1,
        "tracking_state": "OFF_TARGET",
    }
    # Top-strip 방식은 후보가 0개이므로 OFF_TARGET이 아니라 MISSING이어야 한다.
    assert result["closing_top_strip"] == {
        "valid_candidate_count": 0,
        "tracking_state": "MISSING",
    }
