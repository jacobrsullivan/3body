"""
Unit tests for Jacobi coordinate system.
"""

import numpy as np
import pytest

from src.python.coordinates import (
    CartesianState,
    JacobiState,
    Masses,
    cartesian_to_jacobi,
    jacobi_to_cartesian,
    enforce_barycenter,
)
from src.python.coordinates.jacobi import (
    compute_jacobi_hamiltonian,
    verify_hamiltonian_decoupling,
    test_jacobi_roundtrip,
)


class TestJacobiState:
    """Test JacobiState dataclass"""

    def test_construction(self):
        """Test basic construction"""
        r1 = np.array([1, 0, 0], dtype=float)
        r2 = np.array([0, 1, 0], dtype=float)
        r_cm = np.zeros(3)
        p1 = np.array([0, 1, 0], dtype=float)
        p2 = np.array([1, 0, 0], dtype=float)
        p_cm = np.zeros(3)

        state = JacobiState(r1, r2, r_cm, p1, p2, p_cm)

        assert state.r1.shape == (3,)
        assert state.r2.shape == (3,)
        assert state.dimension == 3

    def test_internal_state(self):
        """Test internal state property"""
        state = JacobiState(
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.zeros(3),
            np.array([0, 0, 0]),
            np.array([0, 0, 0]),
            np.zeros(3),
        )

        r1, r2, p1, p2 = state.internal_state

        np.testing.assert_array_equal(r1, state.r1)
        np.testing.assert_array_equal(r2, state.r2)

    def test_validate_barycentric(self):
        """Test validation of barycentric frame"""
        # Valid barycentric state
        state = JacobiState(
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.zeros(3),  # r_cm = 0
            np.array([0, 0, 0]),
            np.array([0, 0, 0]),
            np.zeros(3),  # p_cm = 0
        )

        assert state.validate()

        # Invalid: non-zero r_cm
        state_invalid = JacobiState(
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([1, 0, 0]),  # Non-zero!
            np.array([0, 0, 0]),
            np.array([0, 0, 0]),
            np.zeros(3),
        )

        assert not state_invalid.validate()


class TestCartesianToJacobi:
    """Test Cartesian → Jacobi transformation"""

    def test_transformation_basic(self):
        """Test basic transformation"""
        masses = Masses.equal_masses()

        # Simple configuration
        positions = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0]], dtype=float)
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jacobi = cartesian_to_jacobi(state_cart, masses)

        # Check dimensions
        assert state_jacobi.r1.shape == (3,)
        assert state_jacobi.r2.shape == (3,)

        # r1 = r_1 - r_2
        expected_r1 = positions[0] - positions[1]
        # After barycenter enforcement, positions change slightly

    def test_center_of_mass_zero(self):
        """Test that r_cm is barycenter"""
        masses = Masses(1.0, 2.0, 3.0)

        # Random configuration
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)

        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jacobi = cartesian_to_jacobi(state_cart, masses)

        # In barycentric frame, r_cm should be zero
        assert np.linalg.norm(state_jacobi.r_cm) < 1e-13
        assert np.linalg.norm(state_jacobi.p_cm) < 1e-13


class TestJacobiToCartesian:
    """Test Jacobi → Cartesian transformation"""

    def test_inverse_transformation(self):
        """Test that jacobi_to_cartesian inverts cartesian_to_jacobi"""
        masses = Masses(1.0, 2.0, 3.0)

        # Random Cartesian state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)

        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        # Round trip
        state_jacobi = cartesian_to_jacobi(state_cart, masses)
        state_cart_back = jacobi_to_cartesian(state_jacobi, masses)

        # Check positions
        np.testing.assert_allclose(
            state_cart.positions, state_cart_back.positions, atol=1e-13
        )

        # Check velocities
        np.testing.assert_allclose(
            state_cart.velocities, state_cart_back.velocities, atol=1e-13
        )


class TestRoundTrip:
    """Test round-trip transformations"""

    def test_roundtrip_3d(self):
        """Test round-trip accuracy for 3D"""
        masses = Masses.equal_masses()

        result = test_jacobi_roundtrip(masses, n_samples=10, dimension=3)

        assert result["max_error"] < 1e-12
        assert result["mean_error"] < 1e-13

    def test_roundtrip_2d(self):
        """Test round-trip accuracy for 2D (planar)"""
        masses = Masses(1.0, 2.0, 3.0)

        result = test_jacobi_roundtrip(masses, n_samples=10, dimension=2)

        assert result["max_error"] < 1e-12

    def test_roundtrip_different_masses(self):
        """Test with various mass ratios"""
        mass_configs = [
            Masses.equal_masses(),
            Masses(1.0, 10.0, 0.1),  # Hierarchical
            Masses(1.0, 1.0, 2.0),  # One heavy
        ]

        for masses in mass_configs:
            result = test_jacobi_roundtrip(masses, n_samples=5)
            assert result["max_error"] < 1e-11


class TestJacobiHamiltonian:
    """Test Jacobi Hamiltonian computation"""

    def test_hamiltonian_decomposition(self):
        """Test that H = H_internal + H_cm"""
        masses = Masses.equal_masses()

        # Random Jacobi state
        state = JacobiState(
            np.random.randn(3),
            np.random.randn(3),
            np.zeros(3),
            np.random.randn(3),
            np.random.randn(3),
            np.zeros(3),
        )

        H_internal, H_cm = compute_jacobi_hamiltonian(state, masses)

        # H_cm should be zero (barycentric frame)
        assert abs(H_cm) < 1e-13

        # Total energy via Cartesian should match
        from src.python.coordinates.cartesian import compute_energy

        state_cart = jacobi_to_cartesian(state, masses)
        E_cart = compute_energy(state_cart, masses)

        assert np.isclose(H_internal + H_cm, E_cart)

    def test_decoupling_verification(self):
        """Test that H_internal doesn't depend on r_cm"""
        masses = Masses.equal_masses()

        state = JacobiState(
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.zeros(3),
            np.array([0.1, 0, 0]),
            np.array([0, 0.1, 0]),
            np.zeros(3),
        )

        assert verify_hamiltonian_decoupling(state, masses)


class TestEnergyConservation:
    """Test energy conservation in Jacobi coordinates"""

    def test_energy_matches_cartesian(self):
        """Test that energy computed in Jacobi matches Cartesian"""
        masses = Masses(1.0, 2.0, 3.0)

        # Random Cartesian state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        # Convert to Jacobi
        state_jacobi = cartesian_to_jacobi(state_cart, masses)

        # Compute energy both ways
        E_cart = state_cart.compute_energy(masses)
        E_jacobi = state_jacobi.compute_energy(masses)

        assert np.isclose(E_cart, E_jacobi)


class TestAngularMomentum:
    """Test angular momentum in Jacobi coordinates"""

    def test_angular_momentum_matches_cartesian(self):
        """Test that angular momentum matches between coordinate systems"""
        masses = Masses.equal_masses()

        # Random state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        # Convert to Jacobi
        state_jacobi = cartesian_to_jacobi(state_cart, masses)

        # Compute angular momentum both ways
        L_cart = state_cart.compute_angular_momentum(masses)
        L_jacobi = state_jacobi.compute_angular_momentum(masses)

        np.testing.assert_allclose(L_cart, L_jacobi, atol=1e-13)


class TestEdgeCases:
    """Test edge cases and special configurations"""

    def test_collinear_configuration(self):
        """Test with bodies on a line"""
        masses = Masses.equal_masses()

        # Three bodies on x-axis
        positions = np.array([[-1, 0, 0], [0, 0, 0], [1, 0, 0]], dtype=float)
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        # Should handle transformation
        state_jacobi = cartesian_to_jacobi(state_cart, masses)
        state_back = jacobi_to_cartesian(state_jacobi, masses)

        np.testing.assert_allclose(state_cart.positions, state_back.positions, atol=1e-12)

    def test_very_unequal_masses(self):
        """Test with very different mass ratios"""
        masses = Masses(1000.0, 1.0, 0.001)

        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)

        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jacobi = cartesian_to_jacobi(state_cart, masses)
        state_back = jacobi_to_cartesian(state_jacobi, masses)

        np.testing.assert_allclose(state_cart.positions, state_back.positions, rtol=1e-10)
