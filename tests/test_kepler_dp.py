"""
Kepler Smoke Test (Day 4)

Tests basic functionality using the Kepler problem (two-body orbit).
This is analytically solvable and provides a baseline validation
for the integration framework.

The Kepler problem should show perfect energy conservation in theory,
so any drift is purely numerical error. This provides a stringent
test of integrator accuracy.
"""

import numpy as np
import pytest
import rebound


class TestKeplerSmokeTest:
    """
    Kepler problem smoke tests using REBOUND's IAS15 integrator.

    The Kepler problem is the simplest dynamical system for testing
    integrators. Energy should be exactly conserved, so any drift
    indicates numerical error.
    """

    def test_kepler_energy_conservation_short(self):
        """
        Short Kepler integration test (100 periods).

        Verifies basic functionality before running the full 10^4 period test.
        """
        # Setup simulation
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.dt = 0.01  # Initial timestep (adaptive)

        # Add star at origin
        sim.add(m=1.0)

        # Add planet in elliptical orbit (e=0.5, a=1.0)
        sim.add(m=1e-6, a=1.0, e=0.5)

        # Compute orbital period: T = 2π√(a³/GM)
        # For a=1, M=1: T = 2π
        orbital_period = 2 * np.pi

        # Calculate initial energy
        E0 = sim.energy()

        # Integrate for 100 orbital periods
        n_periods = 100
        t_final = n_periods * orbital_period

        sim.integrate(t_final)

        # Calculate final energy
        E_final = sim.energy()

        # Compute relative energy error
        relative_error = abs((E_final - E0) / E0)

        # Should maintain excellent energy conservation
        assert relative_error < 1e-14, (
            f"Energy conservation failed: relative error = {relative_error:.3e}"
        )

    def test_kepler_energy_conservation_long(self):
        """
        Long Kepler integration test (10^4 periods).

        This is the main Day 4 validation test. IAS15 should maintain
        energy conservation to better than 1e-14 relative error even
        over very long integration times.
        """
        # Setup simulation
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.dt = 0.01  # Initial timestep

        # Configure IAS15 for high accuracy
        sim.ri_ias15.epsilon = 1e-15  # Very tight tolerance

        # Add star at origin (solar mass)
        sim.add(m=1.0)

        # Add planet in elliptical orbit
        # a=1.0 AU, e=0.5 (moderately elliptical)
        # Small mass to avoid 2-body corrections
        sim.add(m=1e-6, a=1.0, e=0.5)

        # Orbital period for a=1, M=1: T = 2π
        orbital_period = 2 * np.pi

        # Calculate initial energy (should be negative for bound orbit)
        E0 = sim.energy()

        # Verify initial energy is negative (bound orbit)
        assert E0 < 0, "Initial energy should be negative for bound orbit"

        # Integrate for 10^4 orbital periods
        n_periods = 10000
        t_final = n_periods * orbital_period

        print(f"\nIntegrating Kepler problem for {n_periods} orbits...")
        print(f"Initial energy: E0 = {E0:.15e}")

        sim.integrate(t_final)

        # Calculate final energy
        E_final = sim.energy()

        print(f"Final energy:   Ef = {E_final:.15e}")

        # Compute energy drift
        dE = E_final - E0
        relative_error = abs(dE / E0)

        print(f"Energy drift: ΔE = {dE:.3e}")
        print(f"Relative error: {relative_error:.3e}")

        # Main assertion: relative error should be < 1e-14
        assert relative_error < 1e-14, (
            f"Energy conservation failed after {n_periods} orbits: "
            f"relative error = {relative_error:.3e} (required < 1e-14)"
        )

    def test_kepler_circular_orbit(self):
        """
        Test circular orbit (e=0) as special case.

        Circular orbits are symmetric and should show even better
        energy conservation than elliptical orbits.
        """
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.ri_ias15.epsilon = 1e-15

        # Add star
        sim.add(m=1.0)

        # Add planet in circular orbit (e=0)
        sim.add(m=1e-6, a=1.0, e=0.0)

        E0 = sim.energy()

        # Integrate for 1000 periods
        orbital_period = 2 * np.pi
        sim.integrate(1000 * orbital_period)

        E_final = sim.energy()
        relative_error = abs((E_final - E0) / E0)

        # Circular orbit should have excellent conservation
        # Slightly relaxed to 2e-15 to account for numerical precision
        assert relative_error < 2e-15

    def test_kepler_highly_elliptical(self):
        """
        Test highly elliptical orbit (e=0.9).

        High eccentricity orbits are more challenging due to the
        large velocity changes at periapsis.
        """
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.ri_ias15.epsilon = 1e-15

        # Add star
        sim.add(m=1.0)

        # Add planet in highly elliptical orbit
        sim.add(m=1e-6, a=1.0, e=0.9)

        E0 = sim.energy()

        # Integrate for 1000 periods
        orbital_period = 2 * np.pi
        sim.integrate(1000 * orbital_period)

        E_final = sim.energy()
        relative_error = abs((E_final - E0) / E0)

        # Should still maintain excellent conservation
        # even for highly elliptical orbit
        assert relative_error < 1e-13

    def test_kepler_angular_momentum_conservation(self):
        """
        Test angular momentum conservation in Kepler problem.

        Angular momentum should also be exactly conserved in the
        2-body problem, providing an additional validation check.
        """
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.ri_ias15.epsilon = 1e-15

        sim.add(m=1.0)
        sim.add(m=1e-6, a=1.0, e=0.5)

        # Move to center of mass frame
        sim.move_to_com()

        # Calculate initial angular momentum
        particles = sim.particles
        L0 = np.array([
            particles[1].m * (particles[1].y * particles[1].vz - particles[1].z * particles[1].vy),
            particles[1].m * (particles[1].z * particles[1].vx - particles[1].x * particles[1].vz),
            particles[1].m * (particles[1].x * particles[1].vy - particles[1].y * particles[1].vx)
        ])
        L0_mag = np.linalg.norm(L0)

        # Integrate
        sim.integrate(1000 * 2 * np.pi)

        # Calculate final angular momentum
        particles = sim.particles
        L_final = np.array([
            particles[1].m * (particles[1].y * particles[1].vz - particles[1].z * particles[1].vy),
            particles[1].m * (particles[1].z * particles[1].vx - particles[1].x * particles[1].vz),
            particles[1].m * (particles[1].x * particles[1].vy - particles[1].y * particles[1].vx)
        ])
        L_final_mag = np.linalg.norm(L_final)

        # Check angular momentum conservation
        relative_error = abs((L_final_mag - L0_mag) / L0_mag)
        assert relative_error < 1e-14


class TestKeplerOrbitElements:
    """
    Test orbital element stability in Kepler problem.

    Orbital elements (a, e, i, etc.) should remain constant in the
    2-body problem. This provides additional validation beyond
    energy conservation.
    """

    def test_semimajor_axis_conservation(self):
        """Test that semi-major axis remains constant."""
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.ri_ias15.epsilon = 1e-15

        sim.add(m=1.0)
        sim.add(m=1e-6, a=1.0, e=0.5)

        # Get initial orbital elements
        orbit_0 = sim.particles[1].orbit(primary=sim.particles[0])
        a_0 = orbit_0.a

        # Integrate for 1000 periods
        sim.integrate(1000 * 2 * np.pi)

        # Get final orbital elements
        orbit_final = sim.particles[1].orbit(primary=sim.particles[0])
        a_final = orbit_final.a

        # Check semi-major axis conservation
        relative_error = abs((a_final - a_0) / a_0)
        assert relative_error < 1e-13

    def test_eccentricity_conservation(self):
        """Test that eccentricity remains constant."""
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.ri_ias15.epsilon = 1e-15

        sim.add(m=1.0)
        sim.add(m=1e-6, a=1.0, e=0.5)

        orbit_0 = sim.particles[1].orbit(primary=sim.particles[0])
        e_0 = orbit_0.e

        sim.integrate(1000 * 2 * np.pi)

        orbit_final = sim.particles[1].orbit(primary=sim.particles[0])
        e_final = orbit_final.e

        # Eccentricity should remain constant
        assert abs(e_final - e_0) < 1e-13


@pytest.mark.slow
class TestKeplerExtreme:
    """
    Extreme Kepler tests (marked as slow).

    These tests push the integrator to its limits and may take
    several minutes to complete.
    """

    def test_kepler_very_long_integration(self):
        """
        Very long integration: 10^5 periods.

        This test verifies that IAS15 maintains accuracy even over
        extremely long timescales (marked as slow test).
        """
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.ri_ias15.epsilon = 1e-15

        sim.add(m=1.0)
        sim.add(m=1e-6, a=1.0, e=0.5)

        E0 = sim.energy()

        # Integrate for 10^5 periods (very long!)
        n_periods = 100000
        sim.integrate(n_periods * 2 * np.pi)

        E_final = sim.energy()
        relative_error = abs((E_final - E0) / E0)

        # Even after 10^5 periods, should maintain good accuracy
        assert relative_error < 1e-12
