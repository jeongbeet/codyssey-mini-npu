"""연산 입력과 결과를 표현하는 공통 데이터 구조."""

from dataclasses import dataclass

Matrix = list[list[float]]
EPSILON = 1e-9
MIN_REPEATS = 10
DEFAULT_REPEATS = 100
BENCHMARK_SIZES = (3, 5, 13, 25)


@dataclass(frozen=True)
class PreparedCase:
    case_id: str
    size: int
    pattern: Matrix
    filters: dict[str, Matrix]
    expected: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    size: int | None
    expected: str | None
    score_cross: float | None
    score_x: float | None
    decision: str | None
    passed: bool
    reason: str = ""


@dataclass(frozen=True)
class BenchmarkResult:
    size: int
    average_ms: float
    repeats_per_filter: int
    filter_count: int
    source: str
    flat_average_ms: float
    flatten_ms: float

    @property
    def mac_count(self) -> int:
        """필터 하나를 처리하는 MAC 누적 횟수."""
        return self.size * self.size

    @property
    def total_calls(self) -> int:
        return self.repeats_per_filter * self.filter_count
