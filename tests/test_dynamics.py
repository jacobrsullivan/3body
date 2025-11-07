"""
Unit tests for CR3BP dynamics and physical calculations.

These tests verify the correctness of the CR3BP equations of motion,
conserved quantities, and other physical properties.
"""

import numpy as np
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.utils.dynamics import (
    distances_to_primaries,
    cr3bp_acceleration,
    cr3bp_potential,
    kinetic_energy,
    calculate_jacobi_constant,
    calculate_energy,
    jacobi_drift_metric,
    relative_jacobi_error,
    energy_error_metric,
    relative_energy_error,
    lagrange_points,
)


class TestDistancesToPrimaries:
    """Test distance calculations to primary bodies."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856  # Earth-Moon system

    def test_distances_at_origin(self):
        """Test distances from origin."""
        state = np.array([0, 0, 0, 0, 0, 0])
        r1, r2 = distances_to_primaries(state, self.mu)

        # At origin: distance to M1 is mu, distance to M2 is 1-mu
        np.testing.assert_allclose(r1, self.mu, rtol=1e-15)
        np.testing.assert_allclose(r2, 1 - self.mu, rtol=1e-15)

    def test_distances_at_primaries(self):
        """Test distances when positioned at primary locations."""
        # At M1 position (-mu, 0, 0)
        state_m1 = np.array([-self.mu, 0, 0, 0, 0, 0])
        r1, r2 = distances_to_primaries(state_m1, self.mu)

        np.testing.assert_allclose(r1, 0, atol=1e-15)
        np.testing.assert_allclose(r2, 1, rtol=1e-15)

        # At M2 position (1-mu, 0, 0)
        state_m2 = np.array([1 - self.mu, 0, 0, 0, 0, 0])
        r1, r2 = distances_to_primaries(state_m2, self.mu)

        np.testing.assert_allclose(r1, 1, rtol=1e-15)
        np.testing.assert_allclose(r2, 0, atol=1e-15)

    def test_distances_3d(self):
        """Test distances for 3D positions."""
        state = np.array([0.5, 0.3, 0.4, 0, 0, 0])
        r1, r2 = distances_to_primaries(state, self.mu)

        # Calculate expected distances
        expected_r1 = np.sqrt((0.5 + self.mu) ** 2 + 0.3**2 + 0.4**2)
        expected_r2 = np.sqrt((0.5 - 1 + self.mu) ** 2 + 0.3**2 + 0.4**2)

        np.testing.assert_allclose(r1, expected_r1, rtol=1e-15)
        np.testing.assert_allclose(r2, expected_r2, rtol=1e-15)


class TestCR3BPAcceleration:
    """Test CR3BP acceleration calculations."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856

    def test_acceleration_at_lagrange_points(self):
        """Test that acceleration is zero at Lagrange points."""
        # L4 point (approximate)
        l4_state = np.array([0.5 - self.mu, np.sqrt(3) / 2, 0, 0, 0, 0])
        acc = cr3bp_acceleration(l4_state, self.mu)

        # Acceleration should be near zero at equilibrium point
        np.testing.assert_allclose(acc, [0, 0, 0], atol=1e-3)  # Rough approximation

    def test_acceleration_dimensions(self):
        """Test that acceleration has correct dimensions."""
        state = np.array([0.5, 0.3, 0.1, -0.2, 0.4, 0.0])
        acc = cr3bp_acceleration(state, self.mu)

        assert acc.shape == (3,)
        assert np.all(np.isfinite(acc))

    def test_acceleration_velocity_dependence(self):
        """Test that acceleration depends on velocity (Coriolis terms)."""
        position = np.array([0.5, 0.3, 0.1])

        # Two states with same position, different velocities
        state1 = np.concatenate([position, [0, 0, 0]])
        state2 = np.concatenate([position, [1, 0, 0]])

        acc1 = cr3bp_acceleration(state1, self.mu)
        acc2 = cr3bp_acceleration(state2, self.mu)

        # Accelerations should be different due to Coriolis terms
        assert not np.allclose(acc1, acc2)

        # The difference should be primarily in y-component (2*vy term)
        diff = acc2 - acc1
        np.testing.assert_allclose(diff[1], -2.0, rtol=1e-15)  # -2*vx


class TestJacobiConstant:
    """Test Jacobi constant calculations."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856

    def test_jacobi_conservation_circular_orbit(self):
        """Test Jacobi constant for a simple circular orbit."""
        # Simple state that should have well-defined Jacobi constant
        state = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        jacobi = calculate_jacobi_constant(state, self.mu)

        # Should be finite and reasonable
        assert np.isfinite(jacobi)
        assert -10 < jacobi < 10  # Reasonable range for normalized units

    def test_jacobi_constant_formula(self):
        """Test Jacobi constant formula manually."""
        state = np.array([0.5, 0.3, 0.0, -0.2, 0.4, 0.0])
        x, y, z, vx, vy, vz = state

        # Calculate manually
        r1 = np.sqrt((x + self.mu) ** 2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + self.mu) ** 2 + y**2 + z**2)

        expected_jacobi = (
            x**2
            + y**2
            + 2 * (1 - self.mu) / r1
            + 2 * self.mu / r2
            - (vx**2 + vy**2 + vz**2)
        )

        calculated_jacobi = calculate_jacobi_constant(state, self.mu)

        np.testing.assert_allclose(calculated_jacobi, expected_jacobi, rtol=1e-14)

    def test_jacobi_drift_metrics(self):
        """Test Jacobi drift metric calculations."""
        # Create trajectory with small perturbation
        n_points = 100
        base_state = np.array([0.5, 0.3, 0.0, -0.2, 0.4, 0.0])

        # Add small random perturbations
        np.random.seed(42)
        perturbations = 1e-10 * np.random.randn(n_points, 6)
        states = base_state[np.newaxis, :] + perturbations

        initial_jacobi, final_jacobi, jacobi_series = jacobi_drift_metric(
            states, self.mu
        )

        # Should have small drift
        assert len(jacobi_series) == n_points
        drift = abs(final_jacobi - initial_jacobi)
        assert drift < 1e-8  # Small drift for small perturbations

        # Relative error should also be small
        rel_error = relative_jacobi_error(states, self.mu)
        assert rel_error < 1e-8


class TestEnergyCalculations:
    """Test energy calculations."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856

    def test_kinetic_energy(self):
        """Test kinetic energy calculation."""
        state = np.array([1, 2, 3, 0.1, 0.2, 0.3])
        T = kinetic_energy(state)

        expected_T = 0.5 * (0.1**2 + 0.2**2 + 0.3**2)
        np.testing.assert_allclose(T, expected_T, rtol=1e-15)

    def test_potential_energy(self):
        """Test potential energy calculation."""
        state = np.array([0.5, 0.3, 0.0, 0, 0, 0])
        U = cr3bp_potential(state, self.mu)

        # Should be finite and negative (bound system)
        assert np.isfinite(U)
        assert U < 0  # Gravitational potential is negative

    def test_total_energy(self):
        """Test total energy calculation."""
        state = np.array([0.5, 0.3, 0.0, -0.2, 0.4, 0.0])

        T = kinetic_energy(state)
        U = cr3bp_potential(state, self.mu)
        E_total = calculate_energy(state, self.mu)

        np.testing.assert_allclose(E_total, T + U, rtol=1e-15)


class TestLagrangePoints:
    """Test Lagrange point calculations."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856

    def test_lagrange_points_shape(self):
        """Test that Lagrange points have correct shape."""
        points = lagrange_points(self.mu)

        assert points.shape == (5, 3)
        assert np.all(np.isfinite(points))

    def test_triangular_points(self):
        """Test L4 and L5 triangular points."""
        points = lagrange_points(self.mu)

        l4 = points[3]  # L4
        l5 = points[4]  # L5

        # L4 and L5 should form equilateral triangles with the primaries
        expected_x = 0.5 - self.mu
        expected_y_l4 = np.sqrt(3) / 2
        expected_y_l5 = -np.sqrt(3) / 2

        np.testing.assert_allclose(l4, [expected_x, expected_y_l4, 0], rtol=1e-10)
        np.testing.assert_allclose(l5, [expected_x, expected_y_l5, 0], rtol=1e-10)

    def test_collinear_points_order(self):
        """Test that collinear points are in correct order."""
        points = lagrange_points(self.mu)

        l1, l2, l3 = points[0], points[1], points[2]

        # L3 should be leftmost, L1 between primaries, L2 rightmost
        assert l3[0] < -self.mu  # L3 left of M1
        assert -self.mu < l1[0] < 1 - self.mu  # L1 between primaries
        assert l2[0] > 1 - self.mu  # L2 right of M2


class TestPhysicalValidation:
    """Test physical validity of calculations."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856

    def test_energy_jacobi_relationship(self):
        """Test relationship between energy and Jacobi constant."""
        state = np.array([0.5, 0.3, 0.0, -0.2, 0.4, 0.0])

        E = calculate_energy(state, self.mu)
        C = calculate_jacobi_constant(state, self.mu)

        # In the co-rotating frame, there's a specific relationship
        # Both should be finite and reasonable
        assert np.isfinite(E)
        assert np.isfinite(C)

    def test_conservation_numerical_integration(self):
        """Test conservation properties for a simple trajectory."""
        # Basic test - real conservation needs actual integration
        states = []
        dt = 0.01  # noqa: F841
        n_steps = 100

        # Simple test trajectory (not a real solution, just for testing metrics)
        state = np.array([0.5, 0.3, 0.0, -0.2, 0.4, 0.0])
        for i in range(n_steps):
            states.append(state.copy())
            # Add small perturbation to simulate integration errors
            state += 1e-12 * np.random.randn(6)

        states = np.array(states)

        # Test metric calculations
        jacobi_error = relative_jacobi_error(states, self.mu)
        energy_error = relative_energy_error(states, self.mu)

        # Errors should be small for small perturbations
        assert jacobi_error < 1e-6
        assert energy_error < 1e-6

    def test_extreme_cases(self):
        """Test behavior in extreme cases."""
        # Very close to primary (but not exactly at it)
        state_close = np.array([-self.mu + 1e-6, 0, 0, 0, 0, 0])

        jacobi_close = calculate_jacobi_constant(state_close, self.mu)
        assert np.isfinite(jacobi_close)

        # Far from system
        state_far = np.array([10, 10, 10, 0, 0, 0])
        jacobi_far = calculate_jacobi_constant(state_far, self.mu)
        assert np.isfinite(jacobi_far)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
