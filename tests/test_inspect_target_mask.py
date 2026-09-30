import sys
from pathlib import Path
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from inspect_target_mask import collect_valid_candidates, is_top_strip_candidate

def test_top_strip_candidate_boundary():
    # 상단 조각, 실제 Target, 30px 경계 안팎을 각각 확인한다.
    assert is_top_strip_candidate((1125, 0, 44, 28)) is True
    assert is_top_strip_candidate((934, 474, 146, 146)) is False
    assert is_top_strip_candidate((0, 29, 1, 1)) is True
    assert is_top_strip_candidate((0, 29, 1, 2)) is False


def test_collect_valid_candidates_excludes_top_strip_and_small_noise():
    # 흰 영역 세 개로 상단 조각, 실제 Target, 면적 미달 잡음을 재현한다.
    mask = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(mask, (10, 0), (30, 10), 255, -1)
    cv2.rectangle(mask, (40, 40), (80, 80), 255, -1)
    cv2.rectangle(mask, (5, 50), (9, 54), 255, -1)

    # 필터 후 중앙 Target 한 개만 남아야 한다.
    candidates = collect_valid_candidates(mask)

    assert len(candidates) == 1
    assert cv2.boundingRect(candidates[0]) == (40, 40, 41, 41)


def test_collect_valid_candidates_returns_empty_for_empty_mask():
    # Target이 없는 Mask에서는 빈 후보 목록을 반환한다.
    mask = np.zeros((100, 100), dtype=np.uint8)

    assert collect_valid_candidates(mask) == []
