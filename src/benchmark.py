"""I/O를 제외한 MAC 함수 호출 시간 측정."""

from time import perf_counter_ns

from .mac import mac_score
from .models import DEFAULT_REPEATS, BenchmarkResult, Matrix
from .validation import validate_matrix, validate_repeats


def make_benchmark_fixture(n: int) -> tuple[Matrix, list[Matrix]]:
    """정답 비교에 포함하지 않는 고정된 성능 측정용 입력을 생성한다."""
    pattern = [[1.0 for _ in range(n)] for _ in range(n)]
    cross = [
        [float(row == n // 2 or col == n // 2) for col in range(n)]
        for row in range(n)
    ]
    diagonal = [
        [float(row == col or row + col == n - 1) for col in range(n)]
        for row in range(n)
    ]
    return pattern, [cross, diagonal]


def benchmark_mac(
    pattern: Matrix,
    kernels: list[Matrix],
    repeats: int = DEFAULT_REPEATS,
    source: str = "사용자 입력",
) -> BenchmarkResult:
    validate_repeats(repeats)
    n = len(pattern)
    pattern = validate_matrix(pattern, n)
    if not kernels:
        raise ValueError("측정할 필터가 필요합니다.")
    kernels = [validate_matrix(kernel, n) for kernel in kernels]

    # 초기 실행 비용을 줄이기 위한 워밍업은 평균에 포함하지 않는다.
    for kernel in kernels:
        mac_score(pattern, kernel)

    elapsed_ns = 0
    for _ in range(repeats):
        for kernel in kernels:
            start = perf_counter_ns()
            mac_score(pattern, kernel)
            elapsed_ns += perf_counter_ns() - start
    total_calls = repeats * len(kernels)
    return BenchmarkResult(
        size=n,
        average_ms=elapsed_ns / total_calls / 1_000_000,
        repeats_per_filter=repeats,
        filter_count=len(kernels),
        source=source,
    )
