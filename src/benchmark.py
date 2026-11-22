"""I/O를 제외한 MAC 함수 호출 시간 측정."""

from time import perf_counter_ns

from .mac import flatten_matrix, mac_score, mac_score_flat
from .models import DEFAULT_REPEATS, BenchmarkResult, Matrix
from .patterns import generate_pattern
from .validation import validate_matrix, validate_repeats


def make_benchmark_fixture(n: int) -> tuple[Matrix, list[Matrix]]:
    """정답 비교에 포함하지 않는 고정된 성능 측정용 입력을 생성한다."""
    return [[1.0] * n for _ in range(n)], [
        generate_pattern(n, "Cross"), generate_pattern(n, "X")
    ]


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

    start = perf_counter_ns()
    flat_pattern = flatten_matrix(pattern)
    flat_kernels = [flatten_matrix(kernel) for kernel in kernels]
    flatten_ms = (perf_counter_ns() - start) / 1_000_000

    # 두 구현을 각각 워밍업하면서 점수와 누적 순서의 일치도 확인한다.
    for kernel, flat_kernel in zip(kernels, flat_kernels):
        if mac_score(pattern, kernel) != mac_score_flat(flat_pattern, flat_kernel):
            raise ArithmeticError("2D와 1D MAC 점수가 다릅니다.")

    layouts = ((mac_score, pattern, kernels), (mac_score_flat, flat_pattern, flat_kernels))
    elapsed_ns = [0, 0]
    for i in range(repeats):
        # 각 회차에서 먼저 측정하는 구현을 교대한다.
        order = (0, 1) if i % 2 == 0 else (1, 0)
        for index in order:
            score, values, weights = layouts[index]
            for weight in weights:
                start = perf_counter_ns()
                score(values, weight)
                duration = perf_counter_ns() - start
                elapsed_ns[index] += duration
    total_calls = repeats * len(kernels)
    return BenchmarkResult(
        size=n,
        average_ms=elapsed_ns[0] / total_calls / 1_000_000,
        repeats_per_filter=repeats,
        filter_count=len(kernels),
        source=source,
        flat_average_ms=elapsed_ns[1] / total_calls / 1_000_000,
        flatten_ms=flatten_ms,
    )
