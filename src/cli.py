"""명령행 옵션과 대화형 메뉴."""

import argparse
import sys
from pathlib import Path

from .data_loader import DatasetError
from .models import DEFAULT_REPEATS, EPSILON
from .runner import run_json_mode, run_manual_mode
from .validation import ValidationError, validate_epsilon, validate_repeats

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data.json"


def epsilon_argument(value: str) -> float:
    try:
        number = float(value)
        validate_epsilon(number)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return number


def repeats_argument(value: str) -> int:
    try:
        number = int(value)
        validate_repeats(number)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mini NPU Simulator — 반복문 MAC 분석")
    parser.add_argument("--mode", choices=("manual", "json"), help="생략하면 메뉴 표시")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="JSON 데이터 경로")
    parser.add_argument(
        "--epsilon", type=epsilon_argument, default=EPSILON,
        help=f"절대오차 허용값 (기본: {EPSILON:g}, 양수)",
    )
    parser.add_argument(
        "--repeats", type=repeats_argument, default=DEFAULT_REPEATS,
        help=f"필터별 반복 측정 횟수 (기본: {DEFAULT_REPEATS}, 최소: 10)",
    )
    args = parser.parse_args(argv)

    def execute(mode: str) -> int:
        try:
            if mode == "manual":
                return run_manual_mode(args.epsilon, args.repeats)
            return run_json_mode(args.data, args.epsilon, args.repeats)
        except (DatasetError, ValidationError, ArithmeticError) as exc:
            print(f"오류: {exc}", file=sys.stderr)
            return 2

    try:
        if args.mode is not None:
            return execute(args.mode)
        while True:
            print("\nMini NPU Simulator")
            print("1. 사용자 입력 (3×3)\n2. data.json 분석\n0. 종료")
            try:
                choice = input("선택 > ").strip()
            except EOFError:
                print("\n입력이 종료되어 메뉴를 닫습니다.")
                return 0
            if choice == "0":
                return 0
            if choice in {"1", "2"}:
                execute("manual" if choice == "1" else "json")
            else:
                print("입력 오류: 0, 1, 2 중 하나를 선택하세요.")
    except EOFError:
        print("\n입력 오류: 행렬 입력을 완료하기 전에 입력이 종료되었습니다.", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n사용자가 실행을 중단했습니다.", file=sys.stderr)
        return 130
