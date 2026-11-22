import unittest

from src.patterns import generate_pattern
from src.validation import ValidationError


class PatternTests(unittest.TestCase):
    def test_odd_even_and_single_cell(self):
        for n, label, rows in (
            (5, "Cross", ["00100", "00100", "11111", "00100", "00100"]),
            (5, "X", ["10001", "01010", "00100", "01010", "10001"]),
            (4, "Cross", ["0010", "0010", "1111", "0010"]),
            (4, "X", ["1001", "0110", "0110", "1001"]),
            (1, "Cross", ["1"]), (1, "X", ["1"]),
        ):
            with self.subTest(n=n, label=label):
                expected = [list(map(float, row)) for row in rows]
                self.assertEqual(generate_pattern(n, label), expected)

    def test_invalid_size_and_label(self):
        for n, label in ((0, "X"), (-1, "Cross"), (True, "X"), (3, "unknown")):
            with self.subTest(n=n, label=label), self.assertRaises(ValidationError):
                generate_pattern(n, label)
