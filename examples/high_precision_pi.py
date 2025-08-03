#!/usr/bin/env python3
"""
High-precision π calculation using QD Python bindings.
Demonstrates multiple algorithms for computing π to extended precision.
"""

import os
import sys
import time

# Add the project root to the path to import qd_python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qd_python as qd  # noqa: E402


def machin_pi_formula():
    """
    Calculate π using Machin's formula with dd_real precision.
    π = 16*arctan(1/5) - 4*arctan(1/239)
    """
    print("Machin's Formula: π = 16*arctan(1/5) - 4*arctan(1/239)")

    start_time = time.perf_counter()

    # Machin's formula coefficients
    coeff1 = qd.dd_real("16")
    coeff2 = qd.dd_real("4")

    # Arguments
    arg1 = qd.dd_real("1") / qd.dd_real("5")
    arg2 = qd.dd_real("1") / qd.dd_real("239")

    # Calculate π
    pi_calculated = coeff1 * qd.atan(arg1) - coeff2 * qd.atan(arg2)

    end_time = time.perf_counter()

    # Compare with QD library constant
    pi_qd = qd.pi
    difference = qd.abs(pi_calculated - pi_qd)

    print(f"Calculated π: {pi_calculated.to_string(35)}")
    print(f"QD Library π: {pi_qd.to_string(35)}")
    print(f"Difference:   {difference.to_string(10)}")
    print(f"Relative error: {(difference / pi_qd).to_string(10)}")
    print(f"Computation time: {(end_time - start_time)*1000:.2f} ms")
    print()

    return pi_calculated


def leibniz_pi_series(iterations=1000000):
    """
    Calculate π using the Leibniz formula (Gregory-Leibniz series).
    π/4 = 1 - 1/3 + 1/5 - 1/7 + 1/9 - ...
    """
    print(f"Leibniz Series: π/4 = 1 - 1/3 + 1/5 - 1/7 + ... ({iterations} terms)")

    start_time = time.perf_counter()

    sum_val = qd.dd_real("0.0")

    for n in range(iterations):
        denominator = qd.dd_real(2 * n + 1)
        term = qd.dd_real("1.0") / denominator

        if n % 2 == 1:
            term = -term

        sum_val += term

        # Show convergence progress
        if iterations > 10000 and n > 0 and n % (iterations // 10) == 0:
            current_pi = qd.dd_real("4.0") * sum_val
            error = qd.abs(current_pi - qd.pi)
            print(
                f"  After {n:7d} terms: π ≈ {current_pi.to_string(15)}, "
                f"error: {error.to_string(8)}"
            )

    pi_leibniz = qd.dd_real("4.0") * sum_val
    end_time = time.perf_counter()

    difference = qd.abs(pi_leibniz - qd.pi)

    print(f"Final result: {pi_leibniz.to_string(35)}")
    print(f"QD Library π: {qd.pi.to_string(35)}")
    print(f"Difference:   {difference.to_string(10)}")
    print(f"Relative error: {(difference / qd.pi).to_string(10)}")
    print(f"Computation time: {(end_time - start_time)*1000:.1f} ms")
    print()

    return pi_leibniz


def monte_carlo_pi(n_samples=1000000):
    """
    Estimate π using Monte Carlo method.
    Generate random points in unit square and count those inside unit circle.
    """
    print(f"Monte Carlo Method ({n_samples} samples)")

    start_time = time.perf_counter()

    # Simple linear congruential generator for reproducible results
    seed = 12345
    points_inside = 0

    for i in range(n_samples):
        # Generate pseudo-random x and y in [-1, 1]
        seed = (1103515245 * seed + 12345) % (2**31)
        x = qd.dd_real(seed) / qd.dd_real(2**30) - qd.dd_real("1.0")

        seed = (1103515245 * seed + 12345) % (2**31)
        y = qd.dd_real(seed) / qd.dd_real(2**30) - qd.dd_real("1.0")

        # Check if point is inside unit circle
        if x * x + y * y <= qd.dd_real("1.0"):
            points_inside += 1

        # Show progress
        if n_samples > 100000 and i > 0 and i % (n_samples // 10) == 0:
            current_pi = qd.dd_real("4.0") * qd.dd_real(points_inside) / qd.dd_real(i)
            error = qd.abs(current_pi - qd.pi)
            print(
                f"  After {i:7d} samples: π ≈ {current_pi.to_string(8)}, "
                f"error: {error.to_string(6)}"
            )

    pi_monte_carlo = (
        qd.dd_real("4.0") * qd.dd_real(points_inside) / qd.dd_real(n_samples)
    )
    end_time = time.perf_counter()

    difference = qd.abs(pi_monte_carlo - qd.pi)

    print(f"Final result: {pi_monte_carlo.to_string(35)}")
    print(f"QD Library π: {qd.pi.to_string(35)}")
    print(f"Difference:   {difference.to_string(10)}")
    print(f"Relative error: {(difference / qd.pi).to_string(10)}")
    print(f"Computation time: {(end_time - start_time)*1000:.1f} ms")
    print()

    return pi_monte_carlo


def spigot_algorithm(digits=50):
    """
    Simple spigot algorithm for π calculation.
    Demonstrates digit-by-digit calculation.
    """
    print(f"Spigot Algorithm (first {digits} digits)")

    start_time = time.perf_counter()

    # Initialize array for the algorithm
    n = digits + 10  # Extra precision
    a = [2] * (10 * n // 3)

    pi_digits = []

    for i in range(n):
        carry = 0
        for j in range(len(a) - 1, -1, -1):
            temp = a[j] * 10 + carry
            a[j] = temp % (2 * j + 1)
            carry = temp // (2 * j + 1)

        pi_digits.append(carry % 10)
        carry //= 10

    # Convert to dd_real
    pi_str = str(pi_digits[0]) + "." + "".join(map(str, pi_digits[1:digits]))
    pi_spigot = qd.dd_real(pi_str)

    end_time = time.perf_counter()

    difference = qd.abs(pi_spigot - qd.pi)

    print(f"Calculated π: {pi_spigot.to_string(35)}")
    print(f"QD Library π: {qd.pi.to_string(35)}")
    print(f"Difference:   {difference.to_string(10)}")
    print(f"Relative error: {(difference / qd.pi).to_string(10)}")
    print(f"Computation time: {(end_time - start_time)*1000:.2f} ms")
    print()

    return pi_spigot


def compare_precision_with_float():
    """Compare QD precision with Python float for π calculations."""
    print("Precision Comparison with Python Float")
    print("-" * 50)

    # Machin's formula with float
    import math

    float_pi = 16 * math.atan(1 / 5) - 4 * math.atan(1 / 239)
    qd_pi = machin_pi_formula()

    print("Machin's Formula Results:")
    print(f"Python float: {float_pi:.15f}")
    print(f"QD dd_real:   {qd_pi.to_string(35)}")
    print("Float digits of agreement: ~15")
    print("QD digits available: ~31")
    print(f"Precision advantage: ~{31-15} additional digits")
    print()


def main():
    """Main function demonstrating π calculation algorithms."""
    print("High-Precision π Calculation Examples")
    print("=" * 50)
    print("Using QD Library Python bindings for extended precision arithmetic")
    print()

    # Reference value
    print(f"Reference π (QD Library): {qd.pi.to_string(35)}")
    print()

    # Run different algorithms
    algorithms = []

    print("Algorithm 1: Machin's Formula")
    print("-" * 30)
    algorithms.append(("Machin", machin_pi_formula()))

    print("Algorithm 2: Leibniz Series")
    print("-" * 30)
    algorithms.append(("Leibniz", leibniz_pi_series(100000)))  # Reduced for speed

    print("Algorithm 3: Monte Carlo Method")
    print("-" * 30)
    algorithms.append(("Monte Carlo", monte_carlo_pi(100000)))  # Reduced for speed

    print("Algorithm 4: Spigot Algorithm")
    print("-" * 30)
    algorithms.append(("Spigot", spigot_algorithm(30)))

    # Summary comparison
    print("Algorithm Accuracy Summary")
    print("=" * 50)
    reference = qd.pi

    for name, result in algorithms:
        error = qd.abs(result - reference)
        relative_error = error / reference

        print(
            f"{name:12s}: error = {error.to_string(8):>12s}, "
            f"relative = {relative_error.to_string(8):>12s}"
        )

    print()
    compare_precision_with_float()

    print("Key Findings:")
    print("- Machin's formula provides fastest convergence to high precision")
    print("- Leibniz series converges slowly but demonstrates iterative precision")
    print("- Monte Carlo shows statistical vs analytical approach trade-offs")
    print("- QD bindings maintain ~31 digits vs ~15 for Python float")
    print(
        "- All deterministic methods achieve precision limited by "
        "dd_real representation"
    )


if __name__ == "__main__":
    main()
