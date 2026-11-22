"""콘솔에서 행렬을 한 행씩 입력받는다."""

import math

from .data_loader import LABEL_ALIASES
from .models import Matrix
from .patterns import generate_pattern
from .validation import validate_matrix, validate_size


def read_size() -> int:
    while True:
        try:
            size = int(input("생성할 패턴 크기 N > "))
            validate_size(size)
            return size
        except ValueError:
            print("크기는 양의 정수로 입력하세요.")


def read_matrix(name: str, n: int) -> Matrix:
    print(f"\n{name}: {n}줄을 입력하세요. 각 줄은 공백으로 구분한 숫자 {n}개입니다.")
    print("자동 생성하려면 첫 줄에 cross 또는 x를 입력하세요.")
    rows: Matrix = []
    while len(rows) < n:
        line = input(f"  {len(rows) + 1}/{n}행 > ")
        if not rows and line.strip().lower() in LABEL_ALIASES:
            return generate_pattern(n, line)
        tokens = line.split()
        if len(tokens) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        try:
            row = [float(token) for token in tokens]
        except ValueError:
            print("입력 형식 오류: 숫자로 변환할 수 없는 값이 있습니다. 다시 입력하세요.")
            continue
        if not all(math.isfinite(value) for value in row):
            print("입력 형식 오류: NaN과 무한대는 허용하지 않습니다. 다시 입력하세요.")
            continue
        rows.append(row)
    return validate_matrix(rows, n)
