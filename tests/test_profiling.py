import subprocess
import sys
import tracemalloc
import unittest
from pathlib import Path
from unittest.mock import patch

from src.profiling import estimate_peak_bytes, profile_mac

ROOT = Path(__file__).resolve().parent.parent


class ProfilingTests(unittest.TestCase):
    def test_memory_budget_rejects_before_allocating(self):
        with patch("src.profiling.make_profile_fixture") as allocate:
            with self.assertRaisesRegex(ValueError, "예산"):
                profile_mac(size=1000, memory_budget_mib=1)
        allocate.assert_not_called()

    def test_profile_computes_scores_and_releases_memory_tracing(self):
        result = profile_mac(size=1, repeats=10, memory_budget_mib=1)
        self.assertEqual(result.scores, (1.0, 1.0))
        self.assertGreater(result.traced_peak_mib, 0)
        self.assertGreaterEqual(result.generation_ms, 0)
        self.assertGreaterEqual(result.validation_ms, 0)
        self.assertGreaterEqual(result.mac_mean_ms, 0)
        self.assertFalse(tracemalloc.is_tracing())

    def test_invalid_size_repeats_and_budget(self):
        for size in (0, -1, True, 2.5):
            with self.subTest(size=size), self.assertRaises(ValueError):
                estimate_peak_bytes(size)
        for options in (
            {"repeats": 9}, {"memory_budget_mib": 0},
            {"memory_budget_mib": float("nan")},
            {"memory_budget_mib": float("inf")},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                profile_mac(size=1, **options)

    def test_existing_memory_tracing_is_preserved(self):
        tracemalloc.start()
        try:
            with self.assertRaisesRegex(ValueError, "별도 Python"):
                profile_mac(size=1)
            self.assertTrue(tracemalloc.is_tracing())
        finally:
            tracemalloc.stop()

    def test_command_reports_measurements_and_budget_errors(self):
        for args, code, message in (
            (["--size", "3"], 0, "MAC 단계/필터: 9"),
            (["--size", "1000", "--memory-budget-mib", "1"], 2, "예산"),
        ):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, "-m", "src.profiling", *args],
                    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                    timeout=20,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertIn(message, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
