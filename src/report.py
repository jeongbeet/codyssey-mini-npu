"""콘솔 결과와 성능 표 출력."""

from .models import BenchmarkResult, CaseResult, Matrix


def format_score(score: float | None) -> str:
    return "-" if score is None else f"{score:.12g}"


def print_matrix(name: str, matrix: Matrix) -> None:
    print(f"{name} 저장 확인:")
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
    print("\n성능 분석 — MAC 함수 1회 기준 평균")
    print("크기(N×N)   평균 시간(ms)   연산 횟수(N²)   필터별 반복   총 호출")
    for result in results:
        size = f"{result.size}x{result.size}"
        print(
            f"{size:<10} {result.average_ms:>12.6f} "
            f"{result.mac_count:>14} {result.repeats_per_filter:>12} "
            f"{result.total_calls:>9}"
        )
    for result in results:
        print(f"  {result.size}x{result.size} 측정 데이터: {result.source}")
    print("입력·출력·파일 읽기·검증·데이터 생성·워밍업은 측정 시간에서 제외합니다.")
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
