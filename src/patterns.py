"""직접 입력과 성능 측정에서 공유하는 이진 패턴."""

from .data_loader import normalize_label
from .models import Matrix
from .validation import ValidationError, validate_size


def generate_pattern(n: int, label: str) -> Matrix:
    """Cross는 n//2행·열, X는 양쪽 대각선에 1을 채운다."""
    validate_size(n)
    shape = normalize_label(label)
    matrix = [[0.0] * n for _ in range(n)]
    if shape == "Cross":
        middle = n // 2
        for row in matrix:
            row[middle] = 1.0
        matrix[middle] = [1.0] * n
    elif shape == "X":
        for i, row in enumerate(matrix):
            row[i] = row[n - 1 - i] = 1.0
    else:
        raise ValidationError(f"{shape} 모양의 생성 규칙이 없습니다.")
    return matrix
