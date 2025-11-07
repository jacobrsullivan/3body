"""
Unit tests for Cartesian coordinate system.
"""

import numpy as np
import pytest

from src.python.coordinates import (
    CartesianState,
    Masses,
    enforce_barycenter,
    ConservationMonitor,
)
from src.python.coordinates.cartesian import (
    compute_energy,
    compute_angular_momentum,
    compute_linear_momentum,
    compute_accelerations,
    cartesian_rhs,
    moment_of_inertia,
)


class TestMasses:
    """Test Masses dataclass"""

    def test_construction(self):
        """Test basic construction"""
        masses = Masses(1.0, 2.0, 3.0)
        assert masses.m1 == 1.0
        assert masses.m2 == 2.0
        assert masses.m3 == 3.0

    def test_total_mass(self):
        """Test total mass property"""
        masses = Masses(1.0, 2.0, 3.0)
        assert masses.total == 6.0

    def test_reduced_masses(self):
        """Test reduced mass calculations"""
        masses = Masses(2.0, 3.0, 5.0)

        # μ₁₂ = m₁m₂/(m₁+m₂) = 6/5
        assert np.isclose(masses.mu12, 6.0 / 5.0)

        # μ₃ = (m₁+m₂)m₃/M = 5*5/10 = 2.5
        assert np.isclose(masses.mu3, 2.5)

    def test_equal_masses(self):
        """Test equal mass constructor"""
        masses = Masses.equal_masses(2.0)
        assert masses.m1 == masses.m2 == masses.m3 == 2.0

    def test_invalid_masses(self):
        """Test that negative masses raise error"""
        with pytest.raises(ValueError):
            Masses(-1.0, 2.0, 3.0)
        with pytest.raises(ValueError):
            Masses(1.0, 0.0, 3.0)


class TestCartesianState:
    """Test CartesianState dataclass"""

    def test_construction(self):
        """Test basic construction"""
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state = CartesianState(positions, velocities)

        assert state.positions.shape == (3, 3)
        assert state.velocities.shape == (3, 3)
        assert state.dimension == 3

    def test_from_flat_3d(self):
        """Test construction from flat array (3D)"""
        z = np.arange(18, dtype=float)
        state = CartesianState.from_flat(z, dimension=3)

        # Check reconstruction
        z_reconstructed = state.to_flat()
        np.testing.assert_allclose(z, z_reconstructed)

    def test_from_flat_2d(self):
        """Test construction from flat array (2D)"""
        z = np.arange(12, dtype=float)
        state = CartesianState.from_flat(z, dimension=2)

        assert state.dimension == 2
        # z-components should be zero
        np.testing.assert_allclose(state.positions[:, 2], 0)
        np.testing.assert_allclose(state.velocities[:, 2], 0)

        # Check reconstruction
        z_reconstructed = state.to_flat()
        np.testing.assert_allclose(z, z_reconstructed)

    def test_planar_constraint(self):
        """Planar states should have z=0"""
        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])

        state = CartesianState(positions, velocities, dimension=2)
        assert np.allclose(state.positions[:, 2], 0)
        assert np.allclose(state.velocities[:, 2], 0)

    def test_planar_violation_raises(self):
        """Non-planar data should raise error for dimension=2"""
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)

        with pytest.raises(ValueError):
            CartesianState(positions, velocities, dimension=2)

    def test_validate(self):
        """Test validation (always true for unrestricted Cartesian)"""
        state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        assert state.validate()


class TestBarycentricEnforcement:
    """Test barycentric frame projection"""

    def test_arbitrary_state_projection(self):
        """Test projection of arbitrary state to barycentric frame"""
        # Random state (not in barycentric frame)
        state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        masses = Masses.equal_masses()

        # Enforce barycenter
        state_bc = enforce_barycenter(state, masses)

        # Check constraints
        P = compute_linear_momentum(state_bc, masses)
        assert np.linalg.norm(P) < 1e-14

        m = masses.as_array()
        r_cm = np.sum(state_bc.positions * m[:, np.newaxis], axis=0)
        assert np.linalg.norm(r_cm) < 1e-14

    def test_already_barycentric(self):
        """State already in barycentric frame should be unchanged"""
        masses = Masses.equal_masses()

        # Create barycentric state
        positions = np.array([[1, 0, 0], [-0.5, 0.866, 0], [-0.5, -0.866, 0]], dtype=float)
        velocities = np.zeros((3, 3))

        # Enforce barycenter
        positions -= np.mean(positions, axis=0)

        state = CartesianState(positions, velocities)
        state_bc = enforce_barycenter(state, masses)

        np.testing.assert_allclose(state.positions, state_bc.positions, atol=1e-14)


class TestConservationLaws:
    """Test energy and momentum conservation"""

    def test_energy_static_configuration(self):
        """Test energy for static configuration"""
        masses = Masses.equal_masses()

        # Equilateral triangle at rest
        positions = np.array([[1, 0, 0], [-0.5, 0.866, 0], [-0.5, -0.866, 0]], dtype=float)
        positions -= np.mean(positions, axis=0)
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities)

        E = compute_energy(state, masses, G=1.0)

        # Should be purely potential (T=0, V<0)
        assert E < 0  # Negative potential energy

    def test_linear_momentum_barycentric(self):
        """Linear momentum should be zero in barycentric frame"""
        masses = Masses(1.0, 2.0, 3.0)

        # Random state
        state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state = enforce_barycenter(state, masses)

        P = compute_linear_momentum(state, masses)
        assert np.linalg.norm(P) < 1e-13

    def test_angular_momentum_circular_orbit(self):
        """Test angular momentum for circular orbit"""
        masses = Masses.equal_masses()

        # Equilateral triangle rotating
        R = 1.0
        omega = np.sqrt(3.0)  # Angular velocity for equal masses
        angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3])

        positions = R * np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])

        # Circular velocities
        velocities = R * omega * np.column_stack(
            [-np.sin(angles), np.cos(angles), np.zeros(3)]
        )

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        L = compute_angular_momentum(state, masses)

        # Should be purely in z-direction
        assert abs(L[0]) < 1e-10
        assert abs(L[1]) < 1e-10
        assert L[2] > 0  # Positive out-of-plane


class TestAccelerations:
    """Test gravitational acceleration calculations"""

    def test_two_body_acceleration(self):
        """Test acceleration for two-body case (third at infinity)"""
        positions = np.array([[0, 0, 0], [1, 0, 0], [1e10, 0, 0]], dtype=float)
        masses = Masses(1.0, 1.0, 1e-10)  # Third body negligible

        acc = compute_accelerations(positions, masses, G=1.0)

        # Body 1 should accelerate toward body 2 (positive x)
        assert acc[0, 0] > 0
        assert abs(acc[0, 1]) < 1e-10
        assert abs(acc[0, 2]) < 1e-10

        # Body 2 should accelerate toward body 1 (negative x)
        assert acc[1, 0] < 0

        # Magnitudes should be equal (equal masses)
        assert np.isclose(abs(acc[0, 0]), abs(acc[1, 0]))

    def test_acceleration_symmetry(self):
        """Test Newton's third law"""
        positions = np.random.randn(3, 3)
        masses = Masses.equal_masses()

        acc = compute_accelerations(positions, masses, G=1.0)

        # Total acceleration should be zero (no external force)
        total_acc = np.sum(acc, axis=0)
        assert np.linalg.norm(total_acc) < 1e-13


class TestRHS:
    """Test equations of motion RHS"""

    def test_rhs_shape(self):
        """Test RHS returns correct shape"""
        z = np.random.randn(18)
        masses = Masses.equal_masses()

        dz_dt = cartesian_rhs(0.0, z, masses, dimension=3)

        assert dz_dt.shape == z.shape

    def test_rhs_velocity_part(self):
        """Test that first half of RHS is velocity"""
        z = np.random.randn(18)
        masses = Masses.equal_masses()

        dz_dt = cartesian_rhs(0.0, z, masses, dimension=3)

        # First 9 components should be velocities
        np.testing.assert_allclose(dz_dt[:9], z[9:])


class TestConservationMonitor:
    """Test ConservationMonitor class"""

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        masses = Masses.equal_masses()

        monitor = ConservationMonitor(state, masses)

        assert monitor.E0 is not None
        assert len(monitor.times) == 0

    def test_monitor_record(self):
        """Test recording conservation errors"""
        state0 = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state0 = enforce_barycenter(state0, Masses.equal_masses())

        masses = Masses.equal_masses()
        monitor = ConservationMonitor(state0, masses)

        # Record several states
        for t in [0.0, 0.1, 0.2]:
            monitor.record(t, state0, masses)

        assert len(monitor.times) == 3
        assert len(monitor.energy_errors) == 3

        # Errors should be zero (same state)
        assert all(abs(e) < 1e-15 for e in monitor.energy_errors)

    def test_monitor_validate(self):
        """Test validation with tolerances"""
        state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state = enforce_barycenter(state, Masses.equal_masses())
        masses = Masses.equal_masses()

        monitor = ConservationMonitor(state, masses)
        monitor.record(0.0, state, masses)

        tolerances = {"energy": 1e-10, "angular_momentum": 1e-10, "linear_momentum": 1e-10}
        assert monitor.validate(tolerances)


class TestMomentOfInertia:
    """Test moment of inertia calculation"""

    def test_equilateral_triangle(self):
        """Test moment of inertia for equilateral triangle"""
        masses = Masses.equal_masses(1.0)
        R = 1.0

        angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3])
        positions = R * np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])
        positions -= np.mean(positions, axis=0)  # Barycenter

        velocities = np.zeros((3, 3))
        state = CartesianState(positions, velocities)

        I = moment_of_inertia(state, masses)

        # For equilateral triangle: I = 3 * m * (2R/√3)² / 2 = 2mR²
        # Wait, let me recalculate properly
        # After centering, each vertex is at distance R from center
        expected_I = 3 * 1.0 * R**2

        assert np.isclose(I, expected_I, rtol=0.01)
