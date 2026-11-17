import json
import tempfile
import unittest
from pathlib import Path

from src.data_loader import DatasetError, load_dataset, normalize_label, prepare_case
from src.validation import ValidationError


def matrix(n=3, value=1.0):
    return [[value for _ in range(n)] for _ in range(n)]


def sample_dataset():
    return {
        "filters": {"size_3": {"cross": matrix(), "x": matrix(value=0.0)}},
        "patterns": {"size_3_1": {"input": matrix(), "expected": "+"}},
    }


class DataLoaderTests(unittest.TestCase):
    def test_all_supported_label_aliases(self):
        for label in ("+", "cross", "Cross", " CROSS "):
            self.assertEqual(normalize_label(label), "Cross")
        for label in ("x", "X", " x "):
            self.assertEqual(normalize_label(label), "X")
        for label in ("UNDECIDED", "circle", "", 1, None):
            with self.subTest(label=label), self.assertRaises(ValidationError):
                normalize_label(label)

    def test_filter_and_expected_normalization(self):
        data = sample_dataset()
        case = prepare_case("size_3_1", data["patterns"]["size_3_1"], data["filters"])
        self.assertEqual(case.expected, "Cross")
        self.assertEqual(set(case.filters), {"Cross", "X"})

    def test_duplicate_normalized_filter_is_rejected(self):
        data = sample_dataset()
        data["filters"]["size_3"]["Cross"] = matrix()
        with self.assertRaisesRegex(ValidationError, "중복"):
            prepare_case("size_3_1", data["patterns"]["size_3_1"], data["filters"])

    def test_file_and_top_level_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            with self.assertRaises(DatasetError):
                load_dataset(path)
            for text in (
                "{invalid",
                "[]",
                '{"filters": [], "patterns": {}}',
                '{"filters": {}}',
                '{"filters": {}, "patterns": {}}',
            ):
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(DatasetError):
                    load_dataset(path)
            path.write_bytes(b"\xff\xfe")
            with self.assertRaises(DatasetError):
                load_dataset(path)
            path.write_text(json.dumps(sample_dataset()), encoding="utf-8")
            self.assertEqual(len(load_dataset(path)["patterns"]), 1)
