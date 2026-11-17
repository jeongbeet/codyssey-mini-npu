"""이중 반복문 MAC과 절대오차 기반 판정."""

import math

from .models import EPSILON, Matrix
from .validation import validate_epsilon


def mac_score(pattern: Matrix, kernel: Matrix) -> float:
    """사전 검증된 같은 크기의 N×N 행렬을 곱해 누적한다."""
    total = 0.0
    n = len(pattern)
    for row in range(n):
        # 행 참조는 한 번만 읽고 원래의 행 우선 누적 순서를 유지한다.
        pattern_row = pattern[row]
        kernel_row = kernel[row]
        for col in range(n):
            total += pattern_row[col] * kernel_row[col]
    if not math.isfinite(total):
        raise ArithmeticError("MAC 결과가 유한하지 않습니다. 입력값의 범위를 줄이세요.")
    return total


def decide(
    score_a: float,
    score_b: float,
    label_a: str,
    label_b: str,
    epsilon: float = EPSILON,
) -> str:
    """|A-B| < epsilon일 때만 동점이며, 경계값은 큰 점수를 선택한다."""
    validate_epsilon(epsilon)
    if not math.isfinite(score_a) or not math.isfinite(score_b):
        raise ArithmeticError("유한한 MAC 점수만 비교할 수 있습니다.")
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b
