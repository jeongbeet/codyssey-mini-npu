import math
import unittest

from src.mac import decide, mac_score
from src.validation import ValidationError


class MacTests(unittest.TestCase):
    def test_signed_fractional_values(self):
        pattern = [[1.5, -2.0], [3.0, 4.0]]
        kernel = [[2.0, 3.0], [-1.0, 0.5]]
        self.assertEqual(mac_score(pattern, kernel), -4.0)

    def test_all_required_sizes(self):
        for size in (3, 5, 13, 25):
            with self.subTest(size=size):
                matrix = [[1.0] * size for _ in range(size)]
                self.assertEqual(mac_score(matrix, matrix), size * size)

    def test_overflow_is_reported(self):
        with self.assertRaises(ArithmeticError):
            mac_score([[1e308]], [[1e308]])

    def test_epsilon_boundary_in_both_directions(self):
        epsilon = 1e-9
        for delta, expected in (
            (0.0, "UNDECIDED"),
            (epsilon / 2, "UNDECIDED"),
            (epsilon, "B"),
            (epsilon * 2, "B"),
            (-epsilon / 2, "UNDECIDED"),
            (-epsilon, "A"),
            (-epsilon * 2, "A"),
        ):
            with self.subTest(delta=delta):
                self.assertEqual(decide(0.0, delta, "A", "B", epsilon), expected)

    def test_float_noise_is_a_tie(self):
        self.assertEqual(decide(0.1 + 0.2, 0.3, "Cross", "X"), "UNDECIDED")

    def test_invalid_epsilon(self):
        for epsilon in (0, -1, math.nan, math.inf, True):
            with self.subTest(epsilon=epsilon), self.assertRaises(ValidationError):
                decide(1.0, 2.0, "A", "B", epsilon)

    def test_nonfinite_scores_are_rejected(self):
        for score in (math.nan, math.inf, -math.inf):
            with self.subTest(score=score), self.assertRaises(ArithmeticError):
                decide(score, 1.0, "A", "B")
