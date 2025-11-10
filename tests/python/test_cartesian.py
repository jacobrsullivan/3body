"""
Tests for Cartesian coordinate system.

Tests:
    - CartesianState construction and validation
    - Barycenter enforcement
    - Energy and momentum computation
    - Conservation laws
    - Accelerations and equations of motion
"""

import pytest
import numpy as np
from src.python.coordinates.base import Masses
from src.python.coordinates.cartesian import (
    CartesianState,
    enforce_barycenter,
    compute_energy,
    compute_linear_momentum,
    compute_angular_momentum,
    compute_accelerations,
    cartesian_rhs,
    ConservationMonitor,
    moment_of_inertia,
)


class TestCartesianState:
    """Test CartesianState dataclass"""

    def test_construction_3d(self):
        """Test 3D Cartesian state construction"""
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state = CartesianState(positions, velocities, dimension=3)

        assert state.positions.shape == (3, 3)
        assert state.velocities.shape == (3, 3)
        assert state.dimension == 3

    def test_construction_2d(self):
        """Test 2D Cartesian state construction"""
        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        state = CartesianState(positions, velocities, dimension=2)

        assert state.dimension == 2
        assert np.allclose(state.positions[:, 2], 0)
        assert np.allclose(state.velocities[:, 2], 0)

    def test_from_flat_3d(self):
        """Test flat array → CartesianState (3D)"""
        z = np.random.randn(18)
        state = CartesianState.from_flat(z, dimension=3)
        z_reconstructed = state.to_flat()

        np.testing.assert_allclose(z, z_reconstructed, rtol=1e-14)

    def test_from_flat_2d(self):
        """Test flat array → CartesianState (2D)"""
        z = np.random.randn(12)
        state = CartesianState.from_flat(z, dimension=2)
        z_reconstructed = state.to_flat()

        np.testing.assert_allclose(z, z_reconstructed, rtol=1e-14)
        assert state.dimension == 2

    def test_invalid_planar_construction(self):
        """Planar state with non-zero z should fail"""
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)

        with pytest.raises(ValueError):
            CartesianState(positions, velocities, dimension=2)

    def test_invalid_shape(self):
        """Invalid array shapes should fail"""
        with pytest.raises(ValueError):
            CartesianState(np.random.randn(3, 2), np.random.randn(3, 3))


class TestBarycentricEnforcement:
    """Test barycentric frame projection"""

    def test_arbitrary_state_projection(self):
        """Arbitrary state → barycentric frame"""
        # Random state (not in barycentric frame)
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Enforce barycenter
        state_bc = enforce_barycenter(state, masses)

        # Check constraints
        P = compute_linear_momentum(state_bc, masses)
        assert np.linalg.norm(P) < 1e-14

        m = masses.as_array()
        r_cm = np.sum(state_bc.positions * m[:, np.newaxis], axis=0)
        assert np.linalg.norm(r_cm) < 1e-14

    def test_barycenter_idempotent(self):
        """Enforcing barycenter twice should not change state"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 2.0, 3.0)

        state1 = enforce_barycenter(state, masses)
        state2 = enforce_barycenter(state1, masses)

        np.testing.assert_allclose(state1.positions, state2.positions, atol=1e-14)
        np.testing.assert_allclose(state1.velocities, state2.velocities, atol=1e-14)

    def test_unequal_masses(self):
        """Test barycenter enforcement with unequal masses"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(10.0, 1.0, 0.1)

        state_bc = enforce_barycenter(state, masses)

        # Verify barycentric constraints
        m = masses.as_array()
        r_cm = np.sum(state_bc.positions * m[:, np.newaxis], axis=0) / masses.total
        v_cm = np.sum(state_bc.velocities * m[:, np.newaxis], axis=0) / masses.total

        assert np.linalg.norm(r_cm) < 1e-14
        assert np.linalg.norm(v_cm) < 1e-14


class TestConservationLaws:
    """Test energy, momentum conservation"""

    def test_lagrange_equilateral_triangle(self):
        """Lagrange equilateral triangle setup"""
        # Equal masses at vertices of equilateral triangle
        # Use smaller velocity for bound orbit
        R = 1.0
        masses = Masses(1.0, 1.0, 1.0)

        # Positions (equilateral triangle)
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])

        # Use slower rotation (not equilibrium, just testing structure)
        omega = 0.5

        velocities = R * omega * np.column_stack([
            -np.sin(angles), np.cos(angles), np.zeros(3)
        ])

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        # Check this is a valid configuration
        # Angular momentum should be non-zero
        L = compute_angular_momentum(state, masses)
        assert np.abs(L[2]) > 0.1

        # Linear momentum should be zero (barycentric)
        P = compute_linear_momentum(state, masses)
        assert np.linalg.norm(P) < 1e-12

        # Energy should be finite
        E = compute_energy(state, masses)
        assert np.isfinite(E)

    def test_energy_computation(self):
        """Test energy computation for simple configuration"""
        # Two bodies at rest, one unit apart, third far away
        positions = np.array([
            [0.5, 0, 0],
            [-0.5, 0, 0],
            [0, 10, 0]
        ])
        velocities = np.zeros((3, 3))

        masses = Masses(1.0, 1.0, 0.001)
        state = CartesianState(positions, velocities)

        E = compute_energy(state, masses)

        # Should be dominated by potential energy between bodies 1-2
        # V ≈ -m1*m2/r12 = -1*1/1 = -1
        assert E < 0
        assert np.abs(E + 1.0) < 0.1  # Roughly -1

    def test_angular_momentum_conservation(self):
        """Angular momentum should be constant for isolated system"""
        # Random state in barycentric frame
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)
        state = enforce_barycenter(state, masses)

        L0 = compute_angular_momentum(state, masses)

        # Evolve slightly (first order)
        dt = 0.001
        z = state.to_flat()
        dz = cartesian_rhs(0, z, masses, dimension=3)
        z_new = z + dt * dz

        state_new = CartesianState.from_flat(z_new, dimension=3)
        L1 = compute_angular_momentum(state_new, masses)

        # Angular momentum should be approximately conserved
        # (not exact due to first-order integration)
        assert np.linalg.norm(L1 - L0) / np.linalg.norm(L0) < 0.01


class TestAccelerations:
    """Test gravitational acceleration computation"""

    def test_two_body_acceleration(self):
        """Test acceleration for two-body problem"""
        # Two equal masses, third very far away
        positions = np.array([
            [0.5, 0, 0],
            [-0.5, 0, 0],
            [100, 0, 0]
        ])
        masses = Masses(1.0, 1.0, 1e-10)

        acc = compute_accelerations(positions, masses, G=1.0)

        # Bodies 1 and 2 should accelerate towards each other
        # Force on body 1: F = -G*m2/r^2 in direction of body 2
        # Expected: a1 ≈ -1.0 in x-direction (towards body 2)
        assert acc[0, 0] < 0  # Body 1 accelerates left (towards body 2)
        assert acc[1, 0] > 0  # Body 2 accelerates right (towards body 1)

        # Magnitudes should be equal (equal masses)
        np.testing.assert_allclose(np.abs(acc[0, 0]), np.abs(acc[1, 0]), rtol=1e-6)

    def test_acceleration_symmetry(self):
        """Accelerations should satisfy Newton's third law (weak form)"""
        positions = np.random.randn(3, 3)
        masses = Masses(1.0, 2.0, 3.0)

        acc = compute_accelerations(positions, masses, G=1.0)

        # Total momentum change should be zero (no external forces)
        m = masses.as_array()
        total_force = np.sum(m[:, np.newaxis] * acc, axis=0)

        assert np.linalg.norm(total_force) < 1e-12


class TestEquationsOfMotion:
    """Test RHS for integrators"""

    def test_rhs_dimensions(self):
        """RHS should preserve dimensions"""
        z = np.random.randn(18)
        masses = Masses(1.0, 1.0, 1.0)

        dz = cartesian_rhs(0.0, z, masses, dimension=3)

        assert dz.shape == z.shape
        assert len(dz) == 18

    def test_rhs_structure(self):
        """RHS should have structure [velocities, accelerations]"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        z = state.to_flat()
        dz = cartesian_rhs(0.0, z, masses, dimension=3)

        # First half should be velocities
        dz_state = CartesianState.from_flat(dz, dimension=3)
        np.testing.assert_allclose(dz_state.positions, state.velocities, rtol=1e-14)


class TestConservationMonitor:
    """Test conservation monitoring"""

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)
        state = enforce_barycenter(state, masses)

        monitor = ConservationMonitor(state, masses)

        assert len(monitor.times) == 0
        assert monitor.E0 is not None
        assert monitor.L0 is not None
        assert np.linalg.norm(monitor.P0) < 1e-12  # Barycentric

    def test_monitor_recording(self):
        """Test error recording"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)
        state = enforce_barycenter(state, masses)

        monitor = ConservationMonitor(state, masses)

        # Record at several times
        for t in [0.1, 0.2, 0.3]:
            monitor.record(t, state, masses)

        assert len(monitor.times) == 3
        assert len(monitor.energy_errors) == 3

        # Errors should be near zero (same state)
        assert all(abs(e) < 1e-12 for e in monitor.energy_errors)

    def test_monitor_validation(self):
        """Test validation with tolerances"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)
        state = enforce_barycenter(state, masses)

        monitor = ConservationMonitor(state, masses)
        monitor.record(0.0, state, masses)

        # Should pass with reasonable tolerances
        assert monitor.validate({
            'energy': 1e-10,
            'angular_momentum': 1e-10,
            'linear_momentum': 1e-10
        })


class TestMomentOfInertia:
    """Test moment of inertia computation"""

    def test_simple_configuration(self):
        """Test moment of inertia for simple configuration"""
        # Three equal masses at unit distance from origin
        positions = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])
        velocities = np.zeros((3, 3))
        state = CartesianState(positions, velocities)
        masses = Masses(1.0, 1.0, 1.0)

        # Enforce barycenter
        state = enforce_barycenter(state, masses)

        I = moment_of_inertia(state, masses)

        # Should be positive
        assert I > 0

    def test_scaling(self):
        """Moment of inertia should scale with square of distance"""
        positions = np.random.randn(3, 3)
        velocities = np.zeros((3, 3))
        masses = Masses(1.0, 1.0, 1.0)

        state1 = CartesianState(positions, velocities)
        state1 = enforce_barycenter(state1, masses)

        state2 = CartesianState(2 * positions, velocities)
        state2 = enforce_barycenter(state2, masses)

        I1 = moment_of_inertia(state1, masses)
        I2 = moment_of_inertia(state2, masses)

        # I2 should be 4 * I1 (quadratic scaling)
        np.testing.assert_allclose(I2, 4 * I1, rtol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
