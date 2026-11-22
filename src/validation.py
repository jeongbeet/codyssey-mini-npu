"""입력 크기, 숫자, 실행 정책 검증."""

import math
import re

from .models import MIN_REPEATS, Matrix


class ValidationError(ValueError):
    """사용자에게 원인을 설명할 수 있는 입력 검증 오류."""


def validate_size(n: int) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValidationError("행렬 크기는 양의 정수여야 합니다.")


def validate_matrix(matrix: object, n: int) -> Matrix:
    """N×N의 유한한 수를 검사하고 float 행렬의 복사본을 반환한다."""
    validate_size(n)
    if not isinstance(matrix, list) or len(matrix) != n:
        raise ValidationError(f"행 수 불일치: {n}개의 행이 필요합니다.")

    validated: Matrix = []
    for row_index, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != n:
            raise ValidationError(
                f"{row_index + 1}행 열 수 불일치: {n}개의 숫자가 필요합니다."
            )
        converted = []
        for col_index, value in enumerate(row):
            # 정상 원소마다 위치 문자열을 만들지 않고 오류가 난 경우에만 만든다.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(
                    f"{row_index + 1}행 {col_index + 1}열: 숫자만 허용합니다."
                )
            try:
                number = float(value)
            except (ValueError, OverflowError) as exc:
                raise ValidationError(
                    f"{row_index + 1}행 {col_index + 1}열: 숫자 범위를 초과했습니다."
                ) from exc
            if not math.isfinite(number):
                raise ValidationError(
                    f"{row_index + 1}행 {col_index + 1}열: NaN과 무한대는 허용하지 않습니다."
                )
            converted.append(number)
        validated.append(converted)
    return validated


def parse_case_size(case_id: str) -> int:
    match = re.fullmatch(r"size_([1-9]\d*)_(\d+)", case_id)
    if match is None:
        raise ValidationError("케이스 키는 size_{N}_{idx} 형식이어야 합니다.")
    try:
        return int(match.group(1))
    except ValueError as exc:
        raise ValidationError("케이스 크기를 정수로 변환할 수 없습니다.") from exc


def validate_epsilon(epsilon: float) -> None:
    if (
        isinstance(epsilon, bool)
        or not isinstance(epsilon, (int, float))
        or not math.isfinite(epsilon)
        or epsilon <= 0
    ):
        raise ValidationError("epsilon은 0보다 큰 유한한 수여야 합니다.")


def validate_repeats(repeats: int) -> None:
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < MIN_REPEATS:
        raise ValidationError(f"반복 횟수는 {MIN_REPEATS} 이상의 정수여야 합니다.")
