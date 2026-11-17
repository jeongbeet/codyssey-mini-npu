import copy
import unittest
from pathlib import Path

from src.data_loader import load_dataset
from src.report import summarize_results
from src.runner import analyze_dataset
from tests.test_data_loader import matrix, sample_dataset

ROOT = Path(__file__).resolve().parent.parent


class RunnerTests(unittest.TestCase):
    def test_supplied_dataset(self):
        results, representatives = analyze_dataset(load_dataset(ROOT / "data.json"))
        self.assertEqual(summarize_results(results), (6, 3, 3))
        self.assertEqual(
            [(result.case_id, result.decision, result.passed) for result in results],
            [
                ("size_5_1", "UNDECIDED", False),
                ("size_5_2", "Cross", True),
                ("size_13_1", "X", True),
                ("size_13_2", "UNDECIDED", False),
                ("size_25_1", "UNDECIDED", False),
                ("size_25_2", "Cross", True),
            ],
        )
        self.assertEqual(set(representatives), {5, 13, 25})

    def test_bad_cases_do_not_stop_later_cases(self):
        data = sample_dataset()
        good = data["patterns"]["size_3_1"]
        bad_cases = {
            "bad_key": copy.deepcopy(good),
            "size_3_2": {"input": [[1.0]], "expected": "+"},
            "size_3_3": {"input": matrix()},
            "size_3_4": {"input": matrix(), "expected": "circle"},
            "size_5_1": {"input": matrix(5), "expected": "+"},
            "size_3_5": None,
            "size_3_6": {"input": matrix(value=True), "expected": "+"},
            "size_3_7": {"input": matrix(value=float("nan")), "expected": "+"},
        }
        data["patterns"] = {**bad_cases, "size_3_1": good}
        results, _ = analyze_dataset(data)
        self.assertEqual(summarize_results(results), (9, 1, 8))
        self.assertTrue(results[-1].passed)
        for result in results[:-1]:
            self.assertIsNone(result.decision)
            self.assertIn("검증 오류", result.reason)

    def test_bad_filter_group_does_not_stop_other_sizes(self):
        for bad_group in (
            {"cross": matrix(), "x": [[0.0]]},
            {"cross": matrix()},
            {"cross": matrix(), "x": matrix(), "circle": matrix()},
        ):
            data = sample_dataset()
            data["filters"]["size_3"] = bad_group
            data["filters"]["size_5"] = {
                "cross": matrix(5), "x": matrix(5, 0.0),
            }
            data["patterns"]["size_5_1"] = {"input": matrix(5), "expected": "+"}
            with self.subTest(group=bad_group):
                results, _ = analyze_dataset(data)
                self.assertEqual(summarize_results(results), (2, 1, 1))
                self.assertTrue(results[1].passed)

    def test_expected_does_not_override_decision(self):
        data = sample_dataset()
        data["patterns"]["size_3_1"]["expected"] = "x"
        results, _ = analyze_dataset(data)
        self.assertEqual(results[0].decision, "Cross")
        self.assertFalse(results[0].passed)
        self.assertIn("expected=X", results[0].reason)

    def test_numeric_overflow_is_a_case_failure(self):
        data = sample_dataset()
        data["filters"]["size_3"]["cross"] = matrix(value=2.0)
        data["patterns"] = {
            "size_3_1": {"input": matrix(value=1e308), "expected": "+"},
            "size_3_2": {"input": matrix(), "expected": "+"},
        }
        results, _ = analyze_dataset(data)
        self.assertEqual(summarize_results(results), (2, 1, 1))
        self.assertIn("연산 오류", results[0].reason)
        self.assertTrue(results[1].passed)
