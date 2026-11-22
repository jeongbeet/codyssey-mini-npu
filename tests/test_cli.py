import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.input_handler import read_matrix

ROOT = Path(__file__).resolve().parent.parent
MANUAL_INPUT = (
    "0 1 0\n1 1 1\n0 1 0\n"
    "1 0 1\n0 1 0\n1 0 1\n"
    "0 1 0\n1 1 1\n0 1 0\n"
)


class InputTests(unittest.TestCase):
    def test_invalid_rows_are_reentered(self):
        lines = [
            "1 2", "1 2 3 4", "a b c", "nan 0 0", "inf 0 0",
            "1 2 3", "4 5 6", "7 8 9",
        ]
        output = io.StringIO()
        with patch("builtins.input", side_effect=lines), contextlib.redirect_stdout(output):
            result = read_matrix("테스트", 3)
        self.assertEqual(result, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
        self.assertEqual(output.getvalue().count("입력 형식 오류"), 5)


class CliTests(unittest.TestCase):
    def run_app(self, *args, input_text="", cwd=ROOT):
        return subprocess.run(
            [sys.executable, str(ROOT / "main.py"), *args],
            input=input_text, text=True, encoding="utf-8",
            capture_output=True, cwd=cwd, timeout=20,
        )

    def test_json_mode_and_default_path_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_app("--mode", "json", "--repeats", "10", cwd=directory)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("전체 테스트: 6 | PASS: 3 | FAIL: 3", result.stdout)
        self.assertRegex(result.stdout, r"3x3\s+[^\n]*측정용 생성 데이터")
        for size in ("5x5", "13x13", "25x25"):
            self.assertIn(size, result.stdout)

    def test_package_entry_point(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--mode", "json", "--repeats", "10"],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=20,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("전체 테스트: 6 | PASS: 3 | FAIL: 3", result.stdout)

    def test_manual_mode(self):
        result = self.run_app("--mode", "manual", "--repeats", "10", input_text=MANUAL_INPUT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("A 점수: 5", result.stdout)
        self.assertIn("B 점수: 1", result.stdout)
        self.assertIn("판정: A", result.stdout)
        self.assertIn("MAC 시간:", result.stdout)
        self.assertLess(result.stdout.index("필터 B 저장 확인"), result.stdout.index("\n패턴:"))

    def test_manual_tie(self):
        result = self.run_app("--mode", "manual", input_text="0 0 0\n" * 9)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UNDECIDED (판정 불가)", result.stdout)

    def test_manual_generated_inputs_and_flat_scores(self):
        for n, score_a, score_b, decision in ((5, 1, 9, "B"), (1, 1, 1, "UNDECIDED")):
            with self.subTest(n=n):
                result = self.run_app("--mode", "manual", "--size", str(n), input_text="cross\nX\nx\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"A 점수: {score_a} |", result.stdout)
                self.assertIn(f"B 점수: {score_b} |", result.stdout)
                self.assertIn(f"판정: {decision}", result.stdout)
                self.assertIn("2D/1D", result.stdout)

    def test_generator_cli_and_interactive_size_retry(self):
        for args, inputs in ((("--mode", "generate", "--size", "4"), ""),
                             ((), "3\n0\nbad\n4\n0\n")):
            with self.subTest(args=args):
                result = self.run_app("--repeats", "10", *args, input_text=inputs)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Cross (4×4):\n  0 0 1 0", result.stdout)
                self.assertIn("X (4×4):\n  1 0 0 1", result.stdout)
                for label in ("Cross", "X"):
                    self.assertRegex(result.stdout, rf"4x4\s+[^\n]*생성 패턴 {label}")

    def test_interactive_menu(self):
        result = self.run_app("--repeats", "10", input_text="bad\n2\n0\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0, 1, 2, 3 중 하나", result.stdout)
        self.assertIn("전체 테스트: 6 | PASS: 3 | FAIL: 3", result.stdout)

    def test_file_error_returns_to_menu(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / "missing.json")
            result = self.run_app("--data", missing, input_text="2\n0\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("JSON 파일을 읽을 수 없습니다", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_direct_file_error_has_exit_code_two(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_app("--mode", "json", "--data", str(Path(directory) / "missing.json"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSON 파일을 읽을 수 없습니다", result.stderr)

    def test_incomplete_manual_input_is_explained(self):
        result = self.run_app("--mode", "manual", input_text="1 2 3\n")
        self.assertEqual(result.returncode, 2)
        self.assertIn("입력을 완료하기 전에", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_options(self):
        for args in (
            ("--mode", "generate", "--size", "0"),
            ("--repeats", "9"), ("--epsilon", "0"),
            ("--epsilon", "nan"), ("--epsilon", "inf"),
        ):
            with self.subTest(args=args):
                result = self.run_app(*args)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
