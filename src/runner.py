"""사용자 입력 모드와 JSON 일괄 분석의 실행 흐름."""

from pathlib import Path
from time import perf_counter_ns
from typing import Any

from .benchmark import benchmark_mac, make_benchmark_fixture
from .data_loader import load_dataset, prepare_case
from .input_handler import read_matrix
from .mac import decide, flatten_matrix, mac_score_flat
from .models import (
    BENCHMARK_SIZES,
    DEFAULT_REPEATS,
    EPSILON,
    CaseResult,
    PreparedCase,
)
from .patterns import generate_pattern
from .report import (
    print_benchmarks,
    print_case_result,
    print_manual_result,
    print_matrix,
    print_summary,
)
from .validation import ValidationError, validate_epsilon


def evaluate_case(case: PreparedCase, epsilon: float = EPSILON) -> CaseResult:
    try:
        pattern = flatten_matrix(case.pattern)
        cross = mac_score_flat(pattern, flatten_matrix(case.filters["Cross"]))
        diagonal = mac_score_flat(pattern, flatten_matrix(case.filters["X"]))
        decision = decide(cross, diagonal, "Cross", "X", epsilon)
    except ArithmeticError as exc:
        return CaseResult(
            case.case_id, case.size, case.expected, None, None, None, False,
            f"연산 오류: {exc}",
        )
    passed = decision == case.expected
    if decision == "UNDECIDED":
        reason = (
            f"동점: |Cross-X|={abs(cross - diagonal):.17g} < epsilon={epsilon:g}; "
            f"expected={case.expected}"
        )
    elif not passed:
        reason = f"판정 {decision}가 expected={case.expected}와 다릅니다."
    else:
        reason = ""
    return CaseResult(
        case.case_id, case.size, case.expected, cross, diagonal, decision, passed,
        reason,
    )


def analyze_dataset(
    data: dict[str, Any], epsilon: float = EPSILON
) -> tuple[list[CaseResult], dict[int, PreparedCase]]:
    validate_epsilon(epsilon)
    results = []
    representatives: dict[int, PreparedCase] = {}
    for case_id, raw_case in data["patterns"].items():
        try:
            case = prepare_case(case_id, raw_case, data["filters"])
        except ValidationError as exc:
            result = CaseResult(
                case_id, None, None, None, None, None, False,
                f"스키마 검증 오류: {exc}",
            )
        else:
            result = evaluate_case(case, epsilon)
            # 정답 불일치·동점이어도 계산이 유효하면 성능 측정에 사용할 수 있다.
            if result.decision is not None:
                representatives.setdefault(case.size, case)
        results.append(result)
    return results, representatives


def run_manual_mode(
    epsilon: float = EPSILON, repeats: int = DEFAULT_REPEATS, size: int = 3
) -> int:
    filter_a = read_matrix("필터 A", size)
    filter_b = read_matrix("필터 B", size)
    print_matrix("필터 A 저장 확인", filter_a)
    print_matrix("필터 B 저장 확인", filter_b)
    pattern = read_matrix("패턴", size)

    flat_pattern = flatten_matrix(pattern)
    flat_a = flatten_matrix(filter_a)
    flat_b = flatten_matrix(filter_b)
    start = perf_counter_ns()
    score_a = mac_score_flat(flat_pattern, flat_a)
    time_a_ms = (perf_counter_ns() - start) / 1_000_000
    start = perf_counter_ns()
    score_b = mac_score_flat(flat_pattern, flat_b)
    time_b_ms = (perf_counter_ns() - start) / 1_000_000

    decision = decide(score_a, score_b, "A", "B", epsilon)
    print_manual_result(score_a, score_b, time_a_ms, time_b_ms, decision, epsilon)
    print_benchmarks([benchmark_mac(pattern, [filter_a, filter_b], repeats)])
    return 0


def run_generate_mode(size: int, repeats: int = DEFAULT_REPEATS) -> int:
    labels = ("Cross", "X")
    patterns = [generate_pattern(size, label) for label in labels]
    for label, pattern in zip(labels, patterns):
        print_matrix(f"{label} ({size}×{size})", pattern)
    # 각 모양을 한 번씩 입력으로 삼아 같은 필터 쌍과 비교한다.
    print_benchmarks([
        benchmark_mac(pattern, patterns, repeats, f"생성 패턴 {label}")
        for label, pattern in zip(labels, patterns)
    ])
    return 0


def run_json_mode(
    path: str | Path, epsilon: float = EPSILON, repeats: int = DEFAULT_REPEATS
) -> int:
    data = load_dataset(path)
    results, representatives = analyze_dataset(data, epsilon)
    print(f"\nJSON 분석: {path} | epsilon={epsilon:g}")
    for result in results:
        print_case_result(result)

    benchmarks = []
    for size in BENCHMARK_SIZES:
        case = representatives.get(size)
        if case is None:
            pattern, kernels = make_benchmark_fixture(size)
            source = "측정용 생성 데이터 (JSON 테스트 제외)"
        else:
            pattern = case.pattern
            kernels = [case.filters["Cross"], case.filters["X"]]
            source = case.case_id
        benchmarks.append(benchmark_mac(pattern, kernels, repeats, source))
    print_benchmarks(benchmarks)
    print_summary(results)
    return 1 if any(not result.passed for result in results) else 0
