"""행렬과 1차원 리스트의 반복문 MAC 및 절대오차 기반 판정."""

import math

from .models import EPSILON, Matrix
from .validation import validate_epsilon


def flatten_matrix(matrix: Matrix) -> list[float]:
    """검증된 N×N 행렬을 행 우선 순서의 N²개 원소로 펼친다."""
    return [value for row in matrix for value in row]


def mac_score_flat(pattern: list[float], kernel: list[float]) -> float:
    """미리 펼친 두 입력을 처음부터 끝까지 같은 순서로 곱해 더한다."""
    if len(pattern) != len(kernel):
        raise ValueError("패턴과 필터의 길이가 달라 MAC을 계산할 수 없습니다.")
    total = 0.0
    for value, weight in zip(pattern, kernel):
        total += value * weight
    if not math.isfinite(total):
        raise ArithmeticError("MAC 결과가 유한하지 않습니다. 입력값의 범위를 줄이세요.")
    return total


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
