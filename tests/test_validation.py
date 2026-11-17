import math
import unittest

from src.validation import (
    ValidationError,
    parse_case_size,
    validate_matrix,
    validate_repeats,
)


class ValidationTests(unittest.TestCase):
    def test_integer_and_float_matrix(self):
        self.assertEqual(
            validate_matrix([[1, 2.5], [-3, 0]], 2),
            [[1.0, 2.5], [-3.0, 0.0]],
        )

    def test_matrix_shape_errors(self):
        for matrix in (None, [], [1, 2], [[1, 2]], [[1, 2], [3]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValidationError):
                validate_matrix(matrix, 2)

    def test_non_numeric_and_nonfinite_values(self):
        for value in ("1", True, None, math.nan, math.inf, -math.inf, 10**1000):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_matrix([[value]], 1)

    def test_case_size(self):
        self.assertEqual(parse_case_size("size_13_2"), 13)
        self.assertEqual(parse_case_size("size_3_0"), 3)
        for key in ("bad", "size_0_1", "size_5", "size_5_x", "size_5_1_extra"):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                parse_case_size(key)

    def test_minimum_repeat_count(self):
        validate_repeats(10)
        for repeats in (9, 0, -1, 10.0, True):
            with self.subTest(repeats=repeats), self.assertRaises(ValidationError):
                validate_repeats(repeats)
