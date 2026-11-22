import unittest
from unittest.mock import patch

from src.benchmark import benchmark_mac, make_benchmark_fixture
from src.mac import flatten_matrix, mac_score, mac_score_flat


class BenchmarkTests(unittest.TestCase):
    def test_average_is_per_single_mac_call(self):
        pattern, kernels = make_benchmark_fixture(3)
        clock_ns = 0

        def timed(function, duration):
            def run(*args):
                nonlocal clock_ns
                clock_ns += duration
                return function(*args)
            return run

        with (
            patch("src.benchmark.perf_counter_ns", side_effect=lambda: clock_ns),
            patch("src.benchmark.flatten_matrix", side_effect=timed(flatten_matrix, 10000)) as pack,
            patch("src.benchmark.mac_score", side_effect=timed(mac_score, 2000)) as baseline,
            patch("src.benchmark.mac_score_flat", side_effect=timed(mac_score_flat, 1000)) as flat,
        ):
            result = benchmark_mac(pattern, kernels, repeats=10)
        self.assertAlmostEqual(result.average_ms, 0.002)
        self.assertAlmostEqual(result.flat_average_ms, 0.001)
        self.assertAlmostEqual(result.flatten_ms, 0.030)
        self.assertEqual(result.mac_count, 9)
        self.assertEqual(result.total_calls, 20)
        self.assertEqual(pack.call_count, 3)
        self.assertEqual(baseline.call_count, 22)  # 필터별 워밍업 1회 포함
        self.assertEqual(flat.call_count, 22)
