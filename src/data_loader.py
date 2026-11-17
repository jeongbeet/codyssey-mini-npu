"""JSON 로드와 케이스별 스키마·라벨 검증."""

import json
from pathlib import Path
from typing import Any

from .models import PreparedCase
from .validation import ValidationError, parse_case_size, validate_matrix


class DatasetError(ValueError):
    """파일 또는 최상위 JSON 구조를 읽을 수 없는 오류."""


def load_dataset(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open(encoding="utf-8-sig") as stream:
            data = json.load(stream)
    except (OSError, UnicodeError, ValueError) as exc:
        raise DatasetError(f"JSON 파일을 읽을 수 없습니다: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise DatasetError("JSON 최상위 값은 객체여야 합니다.")
    for section in ("filters", "patterns"):
        if not isinstance(data.get(section), dict):
            raise DatasetError(f"'{section}' 객체가 필요합니다.")
    if not data["patterns"]:
        raise DatasetError("patterns에 실행할 테스트 케이스가 없습니다.")
    return data


def normalize_label(raw_label: object) -> str:
    if isinstance(raw_label, str):
        aliases = {"+": "Cross", "cross": "Cross", "x": "X"}
        normalized = aliases.get(raw_label.strip().lower())
        if normalized is not None:
            return normalized
    raise ValidationError(
        f"지원하지 않는 라벨 {raw_label!r}: +/cross/Cross 또는 x/X가 필요합니다."
    )


def prepare_case(
    case_id: str, raw_case: object, raw_filters: dict[str, Any]
) -> PreparedCase:
    size = parse_case_size(case_id)
    if not isinstance(raw_case, dict):
        raise ValidationError("케이스는 input과 expected를 가진 객체여야 합니다.")
    for field in ("input", "expected"):
        if field not in raw_case:
            raise ValidationError(f"케이스에 '{field}'가 없습니다.")
    expected = normalize_label(raw_case["expected"])
    try:
        pattern = validate_matrix(raw_case["input"], size)
    except ValidationError as exc:
        raise ValidationError(f"패턴: {exc}") from exc

    group_key = f"size_{size}"
    group = raw_filters.get(group_key)
    if not isinstance(group, dict):
        raise ValidationError(f"필터 그룹 '{group_key}'가 없거나 객체가 아닙니다.")
    filters = {}
    for raw_label, matrix in group.items():
        label = normalize_label(raw_label)
        if label in filters:
            raise ValidationError(f"{group_key}: 정규화 후 '{label}' 필터가 중복됩니다.")
        try:
            filters[label] = validate_matrix(matrix, size)
        except ValidationError as exc:
            raise ValidationError(f"{group_key}/{label} 필터: {exc}") from exc
    if set(filters) != {"Cross", "X"}:
        raise ValidationError(f"{group_key}: Cross와 X 필터가 모두 필요합니다.")
    return PreparedCase(case_id, size, pattern, filters, expected)
