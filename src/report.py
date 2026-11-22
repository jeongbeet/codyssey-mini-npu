"""콘솔 결과와 성능 표 출력."""

from .models import BenchmarkResult, CaseResult, Matrix


def format_score(score: float | None) -> str:
    return "-" if score is None else f"{score:.12g}"


def print_matrix(title: str, matrix: Matrix) -> None:
    print(f"{title}:")
    for row in matrix:
        print("  " + " ".join(format_score(value) for value in row))


def print_manual_result(
    score_a: float,
    score_b: float,
    time_a_ms: float,
    time_b_ms: float,
    decision: str,
    epsilon: float,
) -> None:
    print(f"\nA 점수: {format_score(score_a)} | MAC 시간: {time_a_ms:.6f} ms")
    print(f"B 점수: {format_score(score_b)} | MAC 시간: {time_b_ms:.6f} ms")
    display = "UNDECIDED (판정 불가)" if decision == "UNDECIDED" else decision
    print(f"판정: {display} | epsilon={epsilon:g}")


def print_case_result(result: CaseResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"\n[{status}] {result.case_id}")
    print(
        f"  Cross={format_score(result.score_cross)} | "
        f"X={format_score(result.score_x)} | "
        f"판정={result.decision or '-'} | expected={result.expected or '-'}"
    )
    if result.reason:
        print(f"  사유: {result.reason}")


def print_benchmarks(results: list[BenchmarkResult]) -> None:
    print("\n성능 분석 — 동일 입력의 MAC 함수 1회 평균")
    print("크기(N×N)    2D 평균(ms)   1D 평균(ms)   2D/1D   변환(ms)   MAC 횟수(N²)   필터별 반복   구현당 호출   입력")
    for result in results:
        size = f"{result.size}x{result.size}"
        ratio = (
            f"{result.average_ms / result.flat_average_ms:.2f}x"
            if result.flat_average_ms else "-"
        )
        print(
            f"{size:<10} {result.average_ms:>11.6f} {result.flat_average_ms:>13.6f} "
            f"{ratio:>7} {result.flatten_ms:>11.6f} "
            f"{result.mac_count:>14} {result.repeats_per_filter:>12} "
            f"{result.total_calls:>9}   {result.source}"
        )
    print("변환은 패턴과 필터를 한 번 펼친 시간입니다. 두 평균은 MAC 호출만 측정합니다.")
    print("N²는 필터 1개의 MAC 누적 횟수이며, 두 필터의 판정은 2N²회입니다.")


def summarize_results(results: list[CaseResult]) -> tuple[int, int, int]:
    total = len(results)
    passed = sum(result.passed for result in results)
    return total, passed, total - passed


def print_summary(results: list[CaseResult]) -> None:
    total, passed, failed = summarize_results(results)
    print(f"\n전체 테스트: {total} | PASS: {passed} | FAIL: {failed}")
    if failed:
        print("실패 케이스:")
        for result in results:
            if not result.passed:
                print(f"  - {result.case_id}: {result.reason}")
    else:
        print("실패 케이스가 없습니다.")
