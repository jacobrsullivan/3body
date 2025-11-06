#!/usr/bin/env python3
"""
IAS15 Integrator Usage Example

This script demonstrates how to use the IAS15 integrator for CR3BP
trajectory integration and analysis.

Run this script with:
    python notebooks/ias15_example.py
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.integrators.ias15 import IAS15Integrator
from src.python.utils.dynamics import (
    calculate_jacobi_constant,
    lagrange_points,
    relative_jacobi_error,
)
from src.python.utils.analysis import IntegratorAnalyzer
from src.python.utils.coordinates import get_primary_positions_inertial


def example_l4_orbit():
    """Example: Stable orbit near L4 Lagrange point."""
    print("=" * 60)
    print("Example 1: Stable L4 Orbit Integration")
    print("=" * 60)

    # Earth-Moon system parameters
    mu = 0.0121505856

    # Create IAS15 integrator
    integrator = IAS15Integrator(mu, tolerance=1e-14)
    print(f"Integrator info: {integrator}")

    # Initial conditions near L4 point
    initial_state = np.array([0.4878, 0.8660, 0, 0, 0, 0])
    duration = 62.83  # 10 periods
    output_interval = 0.628  # 100 points per period

    print(f"\nInitial state: {initial_state}")
    print(f"Integration duration: {duration:.2f} time units")
    print(f"Output interval: {output_interval:.3f}")

    # Initial Jacobi constant
    initial_jacobi = calculate_jacobi_constant(initial_state, mu)
    print(f"Initial Jacobi constant: {initial_jacobi:.8f}")

    # Perform integration
    print("\nStarting integration...")
    result = integrator.integrate(initial_state, duration, output_interval)

    if not result.success:
        print(f"Integration failed: {result.message}")
        return

    print(f"Integration completed successfully!")
    print(f"Generated {len(result.times)} trajectory points")
    print(f"Wall time: {result.stats.get('wall_time', 0):.3f} seconds")

    # Analyze results
    analyzer = IntegratorAnalyzer(mu)
    analysis = analyzer.analyze_trajectory(result.times, result.states_corotating)

    # Print accuracy metrics
    jacobi_drift = analysis["jacobi"]["drift_relative"]
    energy_drift = analysis["energy"]["drift_relative"]

    print(f"\nAccuracy Analysis:")
    print(f"  Jacobi drift (relative): {jacobi_drift:.2e}")
    print(f"  Energy drift (relative): {energy_drift:.2e}")
    print(f"  Trajectory length: {analysis['position']['trajectory_length']:.3f}")
    print(f"  Max speed: {analysis['velocity']['max_speed']:.3f}")

    # Quality assessment
    quality = analysis["quality"]
    print(f"\nQuality Assessment:")
    print(f"  Finite values: {'✓' if quality['finite_values'] else '✗'}")
    print(
        f"  Reasonable magnitudes: {'✓' if quality['reasonable_magnitudes'] else '✗'}"
    )
    print(f"  Smooth trajectory: {'✓' if quality['smooth_trajectory'] else '✗'}")

    if quality["issues"]:
        print("  Issues detected:")
        for issue in quality["issues"]:
            print(f"    - {issue}")

    return result, analysis


def example_close_encounter():
    """Example: Integration with close encounter."""
    print("\n" + "=" * 60)
    print("Example 2: Close Encounter Trajectory")
    print("=" * 60)

    mu = 0.0121505856
    integrator = IAS15Integrator(
        mu, tolerance=1e-15
    )  # Higher precision for close encounter

    # Initial conditions that lead to close encounter with secondary
    initial_state = np.array([0.8, 0.1, 0, 0.2, 1.2, 0])
    duration = 3.14  # Half period
    output_interval = 0.01  # High resolution

    print(f"Initial state: {initial_state}")
    print(f"Using higher precision (tol=1e-15) for close encounter")

    result = integrator.integrate(initial_state, duration, output_interval)

    if not result.success:
        print(f"Integration failed: {result.message}")
        return

    print(f"Integration completed: {len(result.times)} points")

    # Find minimum distance to secondary
    min_dist_to_secondary = float("inf")
    for state in result.states_corotating:
        # Distance to secondary at (1-mu, 0, 0)
        dist = np.sqrt((state[0] - (1 - mu)) ** 2 + state[1] ** 2 + state[2] ** 2)
        min_dist_to_secondary = min(min_dist_to_secondary, dist)

    print(f"Minimum distance to secondary: {min_dist_to_secondary:.6f}")

    # Analyze conservation
    jacobi_error = relative_jacobi_error(result.states_corotating, mu)
    print(f"Jacobi conservation: {jacobi_error:.2e}")

    return result


def example_visualization():
    """Example: Create trajectory visualization."""
    print("\n" + "=" * 60)
    print("Example 3: Trajectory Visualization")
    print("=" * 60)

    # Run a short integration for visualization
    mu = 0.0121505856
    integrator = IAS15Integrator(mu)

    initial_state = np.array([0.4878, 0.8660, 0, 0, 0, 0])
    duration = 12.56  # 2 periods
    output_interval = 0.1

    result = integrator.integrate(initial_state, duration, output_interval)

    if not result.success:
        print(f"Visualization failed: {result.message}")
        return

    # Create plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Co-rotating frame trajectory
    states_co = result.states_corotating
    ax1.plot(states_co[:, 0], states_co[:, 1], "b-", linewidth=1.5, label="Trajectory")
    ax1.plot(states_co[0, 0], states_co[0, 1], "go", markersize=8, label="Start")
    ax1.plot(states_co[-1, 0], states_co[-1, 1], "ro", markersize=8, label="End")

    # Mark primaries
    ax1.plot(-mu, 0, "ko", markersize=10, label="M1 (Primary)")
    ax1.plot(1 - mu, 0, "ko", markersize=6, label="M2 (Secondary)")

    # Mark Lagrange points
    L_points = lagrange_points(mu)
    ax1.plot(L_points[3, 0], L_points[3, 1], "k^", markersize=8, label="L4")
    ax1.plot(L_points[4, 0], L_points[4, 1], "kv", markersize=8, label="L5")

    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_title("Co-rotating Frame")
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8)
    ax1.set_aspect("equal")

    # Plot 2: Inertial frame trajectory
    states_in = result.states_inertial
    ax2.plot(states_in[:, 0], states_in[:, 1], "r-", linewidth=1.5, label="Trajectory")
    ax2.plot(states_in[0, 0], states_in[0, 1], "go", markersize=8, label="Start")
    ax2.plot(states_in[-1, 0], states_in[-1, 1], "ro", markersize=8, label="End")

    # Mark rotating primaries at different times
    for i in [
        0,
        len(result.times) // 4,
        len(result.times) // 2,
        3 * len(result.times) // 4,
        -1,
    ]:
        t = result.times[i]
        r1_inert, r2_inert = get_primary_positions_inertial(t, mu)
        alpha = 0.3 + 0.7 * i / len(result.times)
        ax2.plot(r1_inert[0], r1_inert[1], "ko", markersize=8, alpha=alpha)
        ax2.plot(r2_inert[0], r2_inert[1], "ko", markersize=4, alpha=alpha)

    ax2.set_xlabel("x")
    ax2.set_ylabel("y")
    ax2.set_title("Inertial Frame")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8)
    ax2.set_aspect("equal")

    # Plot 3: Jacobi constant evolution
    jacobi_values = [calculate_jacobi_constant(state, mu) for state in states_co]
    initial_jacobi = jacobi_values[0]
    jacobi_deviations = [(j - initial_jacobi) / initial_jacobi for j in jacobi_values]

    ax3.plot(result.times, jacobi_deviations, "g-", linewidth=1.5)
    ax3.set_xlabel("Time")
    ax3.set_ylabel("Relative Jacobi Deviation")
    ax3.set_title("Jacobi Constant Conservation")
    ax3.grid(True, alpha=0.3)
    ax3.ticklabel_format(style="scientific", axis="y", scilimits=(0, 0))

    # Plot 4: Distance from origin
    distances = [np.linalg.norm(state[:3]) for state in states_co]
    ax4.plot(result.times, distances, "m-", linewidth=1.5)
    ax4.set_xlabel("Time")
    ax4.set_ylabel("Distance from Origin")
    ax4.set_title("Orbital Distance Variation")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    output_file = Path(__file__).parent / "ias15_example_plots.png"
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"Plots saved to: {output_file}")

    # Also try to display if running interactively
    try:
        plt.show()
    except:
        print("Display not available, plot saved to file only")


def example_performance_comparison():
    """Example: Compare different tolerance settings."""
    print("\n" + "=" * 60)
    print("Example 4: Performance vs. Accuracy Trade-off")
    print("=" * 60)

    mu = 0.0121505856
    initial_state = np.array([0.4878, 0.8660, 0, 0, 0, 0])
    duration = 12.56  # 2 periods
    output_interval = 0.2

    tolerances = [1e-10, 1e-12, 1e-14, 1e-16]

    print(f"{'Tolerance':<12} {'Wall Time':<12} {'Jacobi Drift':<15} {'Points':<8}")
    print("-" * 55)

    for tol in tolerances:
        integrator = IAS15Integrator(mu, tolerance=tol)

        result = integrator.integrate(initial_state, duration, output_interval)

        if result.success:
            jacobi_error = relative_jacobi_error(result.states_corotating, mu)
            wall_time = result.stats.get("wall_time", 0)
            n_points = len(result.times)

            print(
                f"{tol:<12.0e} {wall_time:<12.3f} {jacobi_error:<15.2e} {n_points:<8d}"
            )
        else:
            print(f"{tol:<12.0e} {'FAILED':<12} {'N/A':<15} {'N/A':<8}")


def main():
    """Run all examples."""
    print("IAS15 Integrator Examples")
    print("========================")
    print("\nThis script demonstrates the IAS15 integrator capabilities")
    print("for CR3BP trajectory integration and analysis.\n")

    try:
        # Run examples
        result1, analysis1 = example_l4_orbit()
        result2 = example_close_encounter()
        example_visualization()
        example_performance_comparison()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

        # Final summary
        if result1 and analysis1:
            print(f"\nL4 orbit integration summary:")
            print(f"  Jacobi drift: {analysis1['jacobi']['drift_relative']:.2e}")
            print(f"  Energy drift: {analysis1['energy']['drift_relative']:.2e}")
            print(
                f"  Quality: {'Excellent' if analysis1['jacobi']['drift_relative'] < 1e-12 else 'Good'}"
            )

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("  pip install rebound matplotlib")
    except Exception as e:
        print(f"Example failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
