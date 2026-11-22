"""큰 행렬의 생성·검증·MAC 시간과 Python 할당 메모리를 분리해 측정한다."""

import argparse
import math
import struct
import sys
import tracemalloc
from dataclasses import dataclass
from time import perf_counter_ns

from .mac import mac_score
from .models import Matrix
from .validation import validate_matrix, validate_repeats

MIB = 1024 * 1024


@dataclass(frozen=True)
class ProfileResult:
    size: int
    repeats: int
    generation_ms: float
    validation_ms: float
    mac_mean_ms: float
    scores: tuple[float, float]
    estimated_peak_mib: float
    traced_peak_mib: float


def estimate_peak_bytes(size: int) -> int:
    """3개 float 행렬과 검증 복사본의 예산 추정치. RSS 하드 제한이 아니다."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("크기는 양의 정수여야 합니다.")
    containers = (size + 1) * sys.getsizeof([])
    references = (size * size + size) * struct.calcsize("P")
    # 리스트의 여유 용량 25%를 고려한다. float 객체는 검증 복사 시 재사용된다.
    buffers = containers + (references * 5 + 3) // 4
    floats = size * size * sys.getsizeof(0.0)
    # 입력 3개와 검증 버퍼 3개에 기타 Python 할당 여유 25%를 더한다.
    return (3 * (floats + 2 * buffers) * 5 + 3) // 4


def make_profile_fixture(size: int) -> tuple[Matrix, list[Matrix]]:
    """모든 원소를 별도의 float로 생성하여 상수 객체 공유로 인한 과소평가를 피한다."""
    pattern = [
        [((row * size + col) % 17 - 8) / 8 for col in range(size)]
        for row in range(size)
    ]
    cross = [
        [((row + 2 * col) % 13 - 6) / 6 for col in range(size)]
        for row in range(size)
    ]
    diagonal = [
        [((2 * row - col) % 11 - 5) / 5 for col in range(size)]
        for row in range(size)
    ]
    return pattern, [cross, diagonal]


def _time_pipeline(size: int, repeats: int) -> tuple[float, float, float, tuple[float, float]]:
    start = perf_counter_ns()
    pattern, kernels = make_profile_fixture(size)
    generation_ms = (perf_counter_ns() - start) / 1_000_000

    start = perf_counter_ns()
    prepared = validate_matrix(pattern, size)
    prepared_kernels = [validate_matrix(kernel, size) for kernel in kernels]
    validation_ms = (perf_counter_ns() - start) / 1_000_000

    # 워밍업은 평균에서 제외한다. 덧셈 순서는 실제 앱과 동일하다.
    scores = (
        mac_score(prepared, prepared_kernels[0]),
        mac_score(prepared, prepared_kernels[1]),
    )
    elapsed_ns = 0
    for _ in range(repeats):
        for kernel in prepared_kernels:
            start = perf_counter_ns()
            mac_score(prepared, kernel)
            elapsed_ns += perf_counter_ns() - start
    return generation_ms, validation_ms, elapsed_ns / (2 * repeats) / 1_000_000, scores


def _measure_peak(size: int) -> int:
    # 시간 측정이 끝나고 그 입력이 해제된 뒤 별도 실행한다.
    # 추적기 자체의 오버헤드는 tracemalloc의 할당량에 포함되지 않는다.
    tracemalloc.start()
    try:
        pattern, kernels = make_profile_fixture(size)
        prepared = validate_matrix(pattern, size)
        prepared_kernels = [validate_matrix(kernel, size) for kernel in kernels]
        for kernel in prepared_kernels:
            mac_score(prepared, kernel)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def profile_mac(
    size: int = 1000, repeats: int = 10, memory_budget_mib: float = 256
) -> ProfileResult:
    estimate = estimate_peak_bytes(size)
    validate_repeats(repeats)
    if not math.isfinite(memory_budget_mib) or memory_budget_mib <= 0:
        raise ValueError("메모리 예산은 0보다 큰 유한한 MiB 값이어야 합니다.")
    if estimate / MIB > memory_budget_mib:
        raise ValueError(
            f"예상 Python 할당 {estimate / MIB:.2f} MiB가 "
            f"예산 {memory_budget_mib:g} MiB를 초과합니다. 크기를 줄이세요."
        )
    if tracemalloc.is_tracing():
        raise ValueError("정확한 메모리 측정을 위해 별도 Python 프로세스에서 실행하세요.")

    generation_ms, validation_ms, mean_ms, scores = _time_pipeline(size, repeats)
    peak = _measure_peak(size)
    return ProfileResult(
        size, repeats, generation_ms, validation_ms, mean_ms, scores,
        estimate / MIB, peak / MIB,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="2D 기준 구현의 CPU MAC 시간·메모리 진단")
    parser.add_argument("--size", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=10, help="필터별 최소 10회")
    parser.add_argument("--memory-budget-mib", type=float, default=256)
    args = parser.parse_args(argv)
    try:
        result = profile_mac(args.size, args.repeats, args.memory_budget_mib)
    except (ValueError, ArithmeticError, MemoryError) as exc:
        print(f"진단 오류: {exc}", file=sys.stderr)
        return 2

    print(f"2D CPU MAC 진단: {result.size}x{result.size}, 필터별 {result.repeats}회")
    print(f"입력 생성 1회 (3개 행렬): {result.generation_ms:.6f} ms")
    print(f"검증 1회 (3개 행렬): {result.validation_ms:.6f} ms")
    print(f"MAC 함수 1회 평균: {result.mac_mean_ms:.6f} ms")
    print(f"MAC 단계/필터: {result.size * result.size}")
    print(f"계산 점수: {result.scores!r}")
    print(f"사전 Python 메모리 추정: {result.estimated_peak_mib:.2f} MiB")
    print(f"별도 실행 Python 할당 최고치: {result.traced_peak_mib:.2f} MiB")
    print("시간과 tracemalloc 메모리 측정은 별도 실행합니다. 메모리 값은 RSS가 아닙니다.")
    print("예산 검사는 이 진단의 입력·검증 버퍼 추정치이며 프로세스 메모리 하드 제한이 아닙니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
