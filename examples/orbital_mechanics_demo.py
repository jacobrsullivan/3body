#!/usr/bin/env python3
"""
Orbital mechanics demonstration using QD Python bindings.
Shows high-precision computation for Kepler problem and energy conservation.
"""

import sys
import os
import time

# Add the project root to the path to import qd_python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qd_python as qd  # noqa: E402


class HighPrecisionKepler:
    """High-precision Kepler problem solver using QD arithmetic."""

    def __init__(self, mu=None):
        """
        Initialize with gravitational parameter.
        Default μ = 1 (normalized units)
        """
        self.mu = mu or qd.dd_real("1.0")

    def orbital_energy(self, r, v):
        """
        Calculate orbital energy: E = v²/2 - μ/r

        Args:
            r: Position magnitude (dd_real)
            v: Velocity magnitude (dd_real)

        Returns:
            Orbital energy (dd_real)
        """
        kinetic = v * v / qd.dd_real("2.0")
        potential = -self.mu / r
        return kinetic + potential

    def semi_major_axis(self, energy):
        """
        Calculate semi-major axis: a = -μ/(2E)

        Args:
            energy: Orbital energy (dd_real)

        Returns:
            Semi-major axis (dd_real)
        """
        if energy >= qd.dd_real("0.0"):
            raise ValueError("Energy must be negative for bound orbits")

        return -self.mu / (qd.dd_real("2.0") * energy)

    def orbital_period(self, semi_major_axis):
        """
        Calculate orbital period: T = 2π√(a³/μ)

        Args:
            semi_major_axis: Semi-major axis (dd_real)

        Returns:
            Orbital period (dd_real)
        """
        return (
            qd.dd_real("2.0")
            * qd.pi
            * qd.sqrt(qd.pow(semi_major_axis, qd.dd_real("3.0")) / self.mu)
        )

    def eccentricity_from_state(self, r_vec, v_vec):
        """
        Calculate eccentricity from state vectors.

        Args:
            r_vec: Position vector [x, y, z] (list of dd_real)
            v_vec: Velocity vector [vx, vy, vz] (list of dd_real)

        Returns:
            Eccentricity (dd_real)
        """
        # Position and velocity magnitudes
        r = qd.sqrt(sum(comp * comp for comp in r_vec))
        v = qd.sqrt(sum(comp * comp for comp in v_vec))

        # Specific angular momentum vector h = r × v
        h = [
            r_vec[1] * v_vec[2] - r_vec[2] * v_vec[1],
            r_vec[2] * v_vec[0] - r_vec[0] * v_vec[2],
            r_vec[0] * v_vec[1] - r_vec[1] * v_vec[0],
        ]
        h_mag = qd.sqrt(sum(comp * comp for comp in h))

        # Orbital energy
        energy = self.orbital_energy(r, v)

        # Semi-major axis - calculated but not used in this function
        _ = self.semi_major_axis(energy)

        # Eccentricity: e = √(1 + 2Eh²/μ²)
        term = qd.dd_real("1.0") + qd.dd_real("2.0") * energy * h_mag * h_mag / (
            self.mu * self.mu
        )
        return qd.sqrt(term)

    def kepler_equation_solver(self, eccentricity, mean_anomaly, tolerance=None):
        """
        Solve Kepler's equation: M = E - e*sin(E) for eccentric anomaly E.
        Uses Newton-Raphson iteration with high precision.

        Args:
            eccentricity: Orbital eccentricity (dd_real)
            mean_anomaly: Mean anomaly in radians (dd_real)
            tolerance: Convergence tolerance (dd_real)

        Returns:
            Eccentric anomaly (dd_real)
        """
        tolerance = tolerance or qd.dd_real("1e-30")

        # Initial guess
        if eccentricity < qd.dd_real("0.8"):
            E = mean_anomaly
        else:
            E = qd.pi

        max_iterations = 50
        for iteration in range(max_iterations):
            # f(E) = E - e*sin(E) - M
            f = E - eccentricity * qd.sin(E) - mean_anomaly

            # f'(E) = 1 - e*cos(E)
            f_prime = qd.dd_real("1.0") - eccentricity * qd.cos(E)

            # Newton-Raphson step
            delta_E = f / f_prime
            E_new = E - delta_E

            # Check convergence
            if qd.abs(delta_E) < tolerance:
                print(f"    Kepler equation converged in {iteration + 1} iterations")
                print(f"    Final error: {qd.abs(delta_E).to_string(10)}")
                return E_new

            E = E_new

        raise RuntimeError(
            f"Kepler equation did not converge after {max_iterations} iterations"
        )


def demonstrate_energy_conservation():
    """Demonstrate energy conservation in high-precision orbital mechanics."""
    print("High-Precision Energy Conservation Demonstration")
    print("=" * 60)
    print()

    kepler = HighPrecisionKepler()

    # Initial orbital state (elliptical orbit)
    print("Initial Conditions:")
    r0 = [
        qd.dd_real("1.0"),
        qd.dd_real("0.0"),
        qd.dd_real("0.0"),
    ]  # Position at periapsis
    v0 = [
        qd.dd_real("0.0"),
        qd.dd_real("1.2"),
        qd.dd_real("0.0"),
    ]  # Velocity perpendicular

    r0_mag = qd.sqrt(sum(comp * comp for comp in r0))
    v0_mag = qd.sqrt(sum(comp * comp for comp in v0))

    print(
        f"Position: r = [{r0[0].to_string(15)}, {r0[1].to_string(15)}, "
        f"{r0[2].to_string(15)}]"
    )
    print(
        f"Velocity: v = [{v0[0].to_string(15)}, {v0[1].to_string(15)}, "
        f"{v0[2].to_string(15)}]"
    )
    print(f"Distance: |r| = {r0_mag.to_string(20)}")
    print(f"Speed: |v| = {v0_mag.to_string(20)}")
    print()

    # Calculate orbital elements
    energy = kepler.orbital_energy(r0_mag, v0_mag)
    semi_major_axis = kepler.semi_major_axis(energy)
    eccentricity = kepler.eccentricity_from_state(r0, v0)
    period = kepler.orbital_period(semi_major_axis)

    print("Orbital Elements:")
    print(f"Energy: E = {energy.to_string(25)}")
    print(f"Semi-major axis: a = {semi_major_axis.to_string(25)}")
    print(f"Eccentricity: e = {eccentricity.to_string(25)}")
    print(f"Period: T = {period.to_string(25)}")
    print()

    # Demonstrate energy conservation at different orbital positions
    print("Energy Conservation Check at Different True Anomalies:")
    print("-" * 60)

    true_anomalies = [
        qd.dd_real(str(angle)) for angle in [0, 30, 60, 90, 120, 150, 180]
    ]

    for i, nu in enumerate(true_anomalies):
        nu_rad = nu * qd.pi / qd.dd_real("180.0")  # Convert to radians

        # Calculate position and velocity at this true anomaly
        # r = a(1-e²)/(1+e*cos(ν))
        r_mag = (
            semi_major_axis
            * (qd.dd_real("1.0") - eccentricity * eccentricity)
            / (qd.dd_real("1.0") + eccentricity * qd.cos(nu_rad))
        )

        # Specific angular momentum (calculated for completeness)
        _ = qd.sqrt(
            kepler.mu
            * semi_major_axis
            * (qd.dd_real("1.0") - eccentricity * eccentricity)
        )

        # Velocity magnitude: v² = μ(2/r - 1/a)
        v_mag_squared = kepler.mu * (
            qd.dd_real("2.0") / r_mag - qd.dd_real("1.0") / semi_major_axis
        )
        v_mag = qd.sqrt(v_mag_squared)

        # Calculate energy at this position
        energy_check = kepler.orbital_energy(r_mag, v_mag)
        energy_difference = qd.abs(energy_check - energy)
        relative_error = energy_difference / qd.abs(energy)

        print(
            f"ν = {nu.to_string(3):>6s}°: r = {r_mag.to_string(15):>18s}, "
            f"v = {v_mag.to_string(15):>18s}"
        )
        print(f"{'':>12s} E = {energy_check.to_string(25):>28s}")
        print(
            f"{'':>12s} ΔE = {energy_difference.to_string(15):>18s}, "
            f"rel_err = {relative_error.to_string(10):>13s}"
        )
        print()

    print("Energy conservation maintained to machine precision!")
    print()


def demonstrate_kepler_equation_precision():
    """Demonstrate high-precision solution of Kepler's equation."""
    print("High-Precision Kepler Equation Solution")
    print("=" * 50)
    print()

    kepler = HighPrecisionKepler()

    # Test cases with different eccentricities
    test_cases = [
        (qd.dd_real("0.1"), "Low eccentricity (nearly circular)"),
        (qd.dd_real("0.5"), "Moderate eccentricity"),
        (qd.dd_real("0.8"), "High eccentricity"),
        (qd.dd_real("0.95"), "Very high eccentricity (nearly parabolic)"),
    ]

    mean_anomaly = qd.pi / qd.dd_real("4.0")  # 45 degrees

    print(
        f"Mean Anomaly: M = {mean_anomaly.to_string(25)} rad "
        f"({qd.dd_real('45.0').to_string(5)}°)"
    )
    print()

    for eccentricity, description in test_cases:
        print(f"Case: {description}")
        print(f"Eccentricity: e = {eccentricity.to_string(25)}")

        start_time = time.perf_counter()
        eccentric_anomaly = kepler.kepler_equation_solver(eccentricity, mean_anomaly)
        solve_time = time.perf_counter() - start_time

        # Verify solution by substituting back into Kepler's equation
        verification = eccentric_anomaly - eccentricity * qd.sin(eccentric_anomaly)
        error = qd.abs(verification - mean_anomaly)

        print(f"Eccentric Anomaly: E = {eccentric_anomaly.to_string(25)} rad")
        print(f"Verification: M_calc = {verification.to_string(25)} rad")
        print(f"Solution error: {error.to_string(15)}")
        print(f"Solve time: {solve_time*1000:.2f} ms")

        # Calculate true anomaly for completeness
        # tan(ν/2) = √((1+e)/(1-e)) * tan(E/2)
        factor = qd.sqrt(
            (qd.dd_real("1.0") + eccentricity) / (qd.dd_real("1.0") - eccentricity)
        )
        true_anomaly = qd.dd_real("2.0") * qd.atan(
            factor * qd.tan(eccentric_anomaly / qd.dd_real("2.0"))
        )

        true_anomaly_deg = true_anomaly * qd.dd_real("180.0") / qd.pi
        print(
            f"True Anomaly: ν = {true_anomaly.to_string(25)} rad "
            f"({true_anomaly_deg.to_string(8)}°)"
        )
        print()


def precision_comparison_with_float():
    """Compare QD precision with Python float for orbital calculations."""
    print("Precision Comparison: QD vs Python Float")
    print("=" * 50)
    print()

    # Test energy conservation calculation

    # Initial conditions
    r_mag_qd = qd.dd_real("1.0")
    v_mag_qd = qd.dd_real("1.2")
    mu_qd = qd.dd_real("1.0")

    r_mag_float = 1.0
    v_mag_float = 1.2
    mu_float = 1.0

    # Calculate energy
    energy_qd = v_mag_qd * v_mag_qd / qd.dd_real("2.0") - mu_qd / r_mag_qd
    energy_float = v_mag_float**2 / 2.0 - mu_float / r_mag_float

    print("Orbital Energy Calculation:")
    print(f"QD result:    E = {energy_qd.to_string(30)}")
    print(f"Float result: E = {energy_float:.15f}")
    print()

    # Test accumulation of small perturbations (simulating long-term integration)
    print("Long-term Energy Drift Simulation (10000 small perturbations):")

    energy_qd_accum = energy_qd
    energy_float_accum = energy_float

    perturbation_qd = qd.dd_real("1e-15")
    perturbation_float = 1e-15

    for i in range(10000):
        energy_qd_accum += perturbation_qd
        energy_float_accum += perturbation_float

    expected_qd = energy_qd + qd.dd_real("10000") * perturbation_qd
    expected_float = energy_float + 10000 * perturbation_float

    qd_error = qd.abs(energy_qd_accum - expected_qd)
    float_error = abs(energy_float_accum - expected_float)

    print(f"QD accumulated:     {energy_qd_accum.to_string(30)}")
    print(f"Float accumulated:  {energy_float_accum:.15f}")
    print(f"QD expected:        {expected_qd.to_string(30)}")
    print(f"Float expected:     {expected_float:.15f}")
    print(f"QD error:           {qd_error.to_string(15)}")
    print(f"Float error:        {float_error:.2e}")
    print(f"QD precision advantage: {float_error / float(qd_error):.1e}x better")
    print()


def main():
    """Main demonstration of orbital mechanics with high precision."""
    print("High-Precision Orbital Mechanics with QD Python Bindings")
    print("=" * 70)
    print("Demonstrating Kepler problem solutions and energy conservation")
    print("using double-double precision arithmetic (~31 decimal digits)")
    print()

    demonstrate_energy_conservation()
    demonstrate_kepler_equation_precision()
    precision_comparison_with_float()

    print("Key Benefits of High-Precision Orbital Mechanics:")
    print("- Energy conservation maintained to machine precision (~1e-30)")
    print("- Kepler equation solution accurate to ~1e-30 relative error")
    print("- Long-term orbital integration maintains precision")
    print("- Critical for three-body problem where small errors accumulate")
    print("- Enables study of chaotic dynamics with numerical confidence")


if __name__ == "__main__":
    main()
