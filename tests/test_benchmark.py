import unittest
from unittest.mock import patch

from src.benchmark import benchmark_mac, make_benchmark_fixture
from src.mac import mac_score


class BenchmarkTests(unittest.TestCase):
    def test_average_is_per_single_mac_call(self):
        pattern, kernels = make_benchmark_fixture(3)
        # 총 20회 측정에서 호출당 1000ns이며 워밍업 2회는 측정 밖이다.
        with (
            patch("src.benchmark.perf_counter_ns", side_effect=range(0, 40000, 1000)),
            patch("src.benchmark.mac_score", wraps=mac_score) as compute,
        ):
            result = benchmark_mac(pattern, kernels, repeats=10)
        self.assertAlmostEqual(result.average_ms, 0.001)
        self.assertEqual(result.mac_count, 9)
        self.assertEqual(result.total_calls, 20)
        self.assertEqual(compute.call_count, 22)
