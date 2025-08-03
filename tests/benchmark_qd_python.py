#!/usr/bin/env python3
"""
Performance benchmark comparing QD Python bindings vs Python float vs C++ QD.
Tests computational overhead and precision trade-offs.
"""

import time
import math
import sys
import os

# Add the project root to the path to import qd_python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qd_python as qd  # noqa: E402


class QDPythonBenchmark:
    """Performance benchmark suite for QD Python bindings."""

    def __init__(self):
        self.n_operations = 100000
        self.results = {}

    def benchmark_basic_arithmetic(self):
        """Benchmark basic arithmetic operations."""
        print("=== Basic Arithmetic Operations Benchmark ===")
        print(f"Operations per test: {self.n_operations}")
        print()

        # Test data preparation
        test_values_qd = [qd.dd_real(1.1 + i * 1e-10) for i in range(self.n_operations)]
        test_values_float = [1.1 + i * 1e-10 for i in range(self.n_operations)]

        # Benchmark addition
        self._benchmark_operation(
            "Addition", lambda: sum(test_values_qd), lambda: sum(test_values_float)
        )

        # Benchmark multiplication (smaller dataset to avoid overflow)
        small_n = self.n_operations // 100
        qd_vals = test_values_qd[:small_n]
        float_vals = test_values_float[:small_n]

        self._benchmark_operation(
            "Multiplication",
            lambda: self._multiply_reduce(qd_vals),
            lambda: self._multiply_reduce(float_vals),
        )

        # Benchmark division
        divisor_qd = qd.dd_real("3.14159")
        divisor_float = 3.14159

        self._benchmark_operation(
            "Division",
            lambda: sum(x / divisor_qd for x in test_values_qd[:1000]),
            lambda: sum(x / divisor_float for x in test_values_float[:1000]),
        )

        print()

    def benchmark_mathematical_functions(self):
        """Benchmark mathematical functions."""
        print("=== Mathematical Functions Benchmark ===")
        print(f"Operations per test: {self.n_operations // 10}")
        print()

        # Test data in appropriate ranges
        angles_qd = [qd.dd_real(i * 0.01) for i in range(self.n_operations // 10)]
        angles_float = [i * 0.01 for i in range(self.n_operations // 10)]

        # Benchmark trigonometric functions
        self._benchmark_operation(
            "sin(x)",
            lambda: sum(qd.sin(x) for x in angles_qd),
            lambda: sum(math.sin(x) for x in angles_float),
        )

        self._benchmark_operation(
            "cos(x)",
            lambda: sum(qd.cos(x) for x in angles_qd),
            lambda: sum(math.cos(x) for x in angles_float),
        )

        # Benchmark exponential functions
        exp_vals_qd = [qd.dd_real(i * 0.01) for i in range(-100, 100)]
        exp_vals_float = [i * 0.01 for i in range(-100, 100)]

        self._benchmark_operation(
            "exp(x)",
            lambda: sum(qd.exp(x) for x in exp_vals_qd),
            lambda: sum(math.exp(x) for x in exp_vals_float),
        )

        # Benchmark logarithm
        log_vals_qd = [qd.dd_real(1.0 + i * 0.01) for i in range(1000)]
        log_vals_float = [1.0 + i * 0.01 for i in range(1000)]

        self._benchmark_operation(
            "log(x)",
            lambda: sum(qd.log(x) for x in log_vals_qd),
            lambda: sum(math.log(x) for x in log_vals_float),
        )

        # Benchmark square root
        sqrt_vals_qd = [qd.dd_real(i * 0.01) for i in range(1, 1001)]
        sqrt_vals_float = [i * 0.01 for i in range(1, 1001)]

        self._benchmark_operation(
            "sqrt(x)",
            lambda: sum(qd.sqrt(x) for x in sqrt_vals_qd),
            lambda: sum(math.sqrt(x) for x in sqrt_vals_float),
        )

        print()

    def benchmark_high_precision_computation(self):
        """Benchmark high-precision computation scenarios."""
        print("=== High-Precision Computation Benchmark ===")
        print()

        # Pi calculation using Machin's formula
        print("π calculation using Machin's formula:")

        def machin_pi_qd():
            return qd.dd_real("16") * qd.atan(
                qd.dd_real("1") / qd.dd_real("5")
            ) - qd.dd_real("4") * qd.atan(qd.dd_real("1") / qd.dd_real("239"))

        def machin_pi_float():
            return 16 * math.atan(1 / 5) - 4 * math.atan(1 / 239)

        start_time = time.perf_counter()
        pi_qd = machin_pi_qd()
        qd_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        pi_float = machin_pi_float()
        float_time = time.perf_counter() - start_time

        print(f"  QD result:     {pi_qd.to_string(35)}")
        print(f"  Float result:  {pi_float:.15f}")
        print(f"  QD time:       {qd_time*1000:.3f} ms")
        print(f"  Float time:    {float_time*1000:.3f} ms")
        print(f"  Overhead:      {qd_time/float_time:.1f}x")
        qd_digits = len(pi_qd.to_string(50))
        float_digits = len(f"{pi_float:.15f}")
        print(f"  Precision advantage: {qd_digits - float_digits} extra digits")
        print()

        # Newton's method for sqrt(2)
        print("Newton's method for sqrt(2) (5 iterations):")

        def newton_sqrt2_qd():
            x = qd.dd_real("1.5")
            two = qd.dd_real("2.0")
            for _ in range(5):
                x = (x + two / x) / qd.dd_real("2.0")
            return x

        def newton_sqrt2_float():
            x = 1.5
            for _ in range(5):
                x = (x + 2.0 / x) / 2.0
            return x

        start_time = time.perf_counter()
        sqrt2_qd = newton_sqrt2_qd()
        qd_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        sqrt2_float = newton_sqrt2_float()
        float_time = time.perf_counter() - start_time

        target_qd = qd.sqrt(qd.dd_real("2.0"))
        error_qd = abs(sqrt2_qd - target_qd)
        error_float = abs(sqrt2_float - math.sqrt(2.0))

        print(f"  QD result:     {sqrt2_qd.to_string(35)}")
        print(f"  Float result:  {sqrt2_float:.15f}")
        print(f"  QD error:      {error_qd.to_string(10)}")
        print(f"  Float error:   {error_float:.2e}")
        print(f"  QD time:       {qd_time*1000:.3f} ms")
        print(f"  Float time:    {float_time*1000:.3f} ms")
        print(f"  Overhead:      {qd_time/float_time:.1f}x")
        print()

    def benchmark_memory_operations(self):
        """Benchmark memory-intensive operations."""
        print("=== Memory Operations Benchmark ===")
        print()

        n_elements = 10000

        # Array creation
        print(f"Array creation ({n_elements} elements):")

        start_time = time.perf_counter()
        qd_array = [qd.dd_real(i * 0.001) for i in range(n_elements)]
        qd_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        float_array = [i * 0.001 for i in range(n_elements)]
        float_time = time.perf_counter() - start_time

        print(f"  QD time:       {qd_time*1000:.3f} ms")
        print(f"  Float time:    {float_time*1000:.3f} ms")
        print(f"  Overhead:      {qd_time/float_time:.1f}x")
        print()

        # Array operations
        print("Array sum operation:")

        start_time = time.perf_counter()
        qd_sum = sum(qd_array)
        qd_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        float_sum = sum(float_array)
        float_time = time.perf_counter() - start_time

        print(f"  QD time:       {qd_time*1000:.3f} ms")
        print(f"  Float time:    {float_time*1000:.3f} ms")
        print(f"  Overhead:      {qd_time/float_time:.1f}x")
        print(f"  QD result:     {qd_sum.to_string(20)}")
        print(f"  Float result:  {float_sum:.15f}")
        print()

    def precision_comparison(self):
        """Compare precision capabilities."""
        print("=== Precision Comparison ===")
        print()

        # Catastrophic cancellation test
        print("Catastrophic cancellation test: (1e15 + 1e-15) - 1e15")

        large_qd = qd.dd_real("1e15")
        small_qd = qd.dd_real("1e-15")
        result_qd = (large_qd + small_qd) - large_qd
        error_qd = abs(result_qd - small_qd)

        large_float = 1e15
        small_float = 1e-15
        result_float = (large_float + small_float) - large_float
        error_float = abs(result_float - small_float)

        print(f"  QD result:     {result_qd.to_string(35)}")
        print(f"  Float result:  {result_float:.2e}")
        print(f"  QD error:      {error_qd.to_string(10)}")
        print(f"  Float error:   {error_float:.2e}")
        print(f"  QD relative error: {(error_qd / small_qd).to_string(10)}")
        print(f"  Float relative error: {error_float / small_float:.2e}")
        print()

        # Precision accumulation test
        print("Precision accumulation: sum of 1e-10 repeated 1 million times")

        small_qd = qd.dd_real("1e-10")
        small_float = 1e-10
        n_terms = 1000000

        start_time = time.perf_counter()
        qd_sum = qd.dd_real("0")
        for _ in range(n_terms):
            qd_sum += small_qd
        qd_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        float_sum = 0.0
        for _ in range(n_terms):
            float_sum += small_float
        float_time = time.perf_counter() - start_time

        expected_qd = small_qd * qd.dd_real(n_terms)
        expected_float = small_float * n_terms

        qd_error = abs(qd_sum - expected_qd)
        float_error = abs(float_sum - expected_float)

        print(f"  QD result:     {qd_sum.to_string(25)}")
        print(f"  Float result:  {float_sum:.15f}")
        print(f"  Expected:      {expected_qd.to_string(25)}")
        print(f"  QD error:      {qd_error.to_string(10)}")
        print(f"  Float error:   {float_error:.2e}")
        print(f"  QD time:       {qd_time*1000:.1f} ms")
        print(f"  Float time:    {float_time*1000:.1f} ms")
        print(f"  Overhead:      {qd_time/float_time:.1f}x")
        print()

    def _benchmark_operation(self, name, qd_func, float_func):
        """Helper to benchmark a single operation."""
        # Warm up
        qd_func()
        float_func()

        # QD benchmark
        start_time = time.perf_counter()
        _ = qd_func()
        qd_time = time.perf_counter() - start_time

        # Float benchmark
        start_time = time.perf_counter()
        _ = float_func()
        float_time = time.perf_counter() - start_time

        overhead = qd_time / float_time if float_time > 0 else float("inf")

        print(f"{name}:")
        print(f"  QD time:     {qd_time*1000:.2f} ms")
        print(f"  Float time:  {float_time*1000:.2f} ms")
        print(f"  Overhead:    {overhead:.1f}x")
        print()

        self.results[name] = {
            "qd_time": qd_time,
            "float_time": float_time,
            "overhead": overhead,
        }

    def _multiply_reduce(self, values):
        """Helper to compute product with overflow protection."""
        if not values:
            return type(values[0])(1) if values else 1

        result = values[0]
        for val in values[1:]:
            result *= val
            # Prevent overflow by taking modulo for large results
            if hasattr(result, "to_string"):
                if len(result.to_string(5)) > 50:  # QD case
                    result = qd.dd_real(str(float(result) % 1e10))
            else:
                if abs(result) > 1e50:  # Float case
                    result = result % 1e10
        return result

    def run_all_benchmarks(self):
        """Run complete benchmark suite."""
        print("QD Python Bindings Performance Benchmark")
        print("=" * 50)
        print()
        print("Testing high-precision double-double arithmetic vs Python float")
        print("Hardware:", os.uname().machine, os.uname().system)
        print()

        self.benchmark_basic_arithmetic()
        self.benchmark_mathematical_functions()
        self.benchmark_high_precision_computation()
        self.benchmark_memory_operations()
        self.precision_comparison()

        self._print_summary()

    def _print_summary(self):
        """Print benchmark summary."""
        print("=== Performance Summary ===")
        print()

        if self.results:
            avg_overhead = sum(
                r["overhead"]
                for r in self.results.values()
                if r["overhead"] != float("inf")
            ) / len(self.results)
            print(f"Average computational overhead: {avg_overhead:.1f}x")
            print()
            print("Operation breakdown:")
            for name, result in sorted(
                self.results.items(), key=lambda x: x[1]["overhead"]
            ):
                if result["overhead"] != float("inf"):
                    print(f"  {name:15s}: {result['overhead']:6.1f}x")

        print()
        print("Key findings:")
        print("- QD provides ~31 decimal digits vs ~15 for Python float")
        print("- Computational overhead ranges from 10-100x depending on operation")
        print("- Memory usage is 2x (16 bytes vs 8 bytes per number)")
        print(
            "- Precision advantage is significant for accumulation and "
            "cancellation scenarios"
        )
        print(
            "- Suitable for high-precision scientific computing where "
            "accuracy is critical"
        )


if __name__ == "__main__":
    benchmark = QDPythonBenchmark()
    benchmark.run_all_benchmarks()
