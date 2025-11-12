"""
Tests for Jacobi coordinate system.

Tests:
    - JacobiState construction and validation
    - Cartesian ↔ Jacobi transformations
    - Hamiltonian decomposition
    - Round-trip accuracy
"""

import pytest
import numpy as np
from src.python.coordinates.base import Masses
from src.python.coordinates.cartesian import CartesianState, enforce_barycenter
from src.python.coordinates.jacobi import (
    JacobiState,
    cartesian_to_jacobi,
    jacobi_to_cartesian,
    compute_jacobi_hamiltonian,
    verify_hamiltonian_decoupling,
    test_jacobi_roundtrip,
)


class TestJacobiState:
    """Test JacobiState dataclass"""

    def test_construction_3d(self):
        """Test 3D Jacobi state construction"""
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r_cm = np.zeros(3)
        p1 = np.array([0.0, 0.5, 0.0])
        p2 = np.array([0.5, 0.0, 0.0])
        p_cm = np.zeros(3)

        state = JacobiState(r1, r2, r_cm, p1, p2, p_cm, dimension=3)

        assert state.r1.shape == (3,)
        assert state.dimension == 3
        assert state.validate()  # Should be in barycentric frame

    def test_construction_2d(self):
        """Test 2D Jacobi state construction"""
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r_cm = np.zeros(3)
        p1 = np.array([0.0, 0.5, 0.0])
        p2 = np.array([0.5, 0.0, 0.0])
        p_cm = np.zeros(3)

        state = JacobiState(r1, r2, r_cm, p1, p2, p_cm, dimension=2)

        assert state.dimension == 2

    def test_invalid_planar_construction(self):
        """2D Jacobi state with non-zero z should fail"""
        r1 = np.array([1.0, 0.0, 0.5])  # Non-zero z
        r2 = np.array([0.0, 1.0, 0.0])
        r_cm = np.zeros(3)
        p1 = np.zeros(3)
        p2 = np.zeros(3)
        p_cm = np.zeros(3)

        with pytest.raises(ValueError):
            JacobiState(r1, r2, r_cm, p1, p2, p_cm, dimension=2)

    def test_internal_state_property(self):
        """Test internal_state property"""
        state = JacobiState(
            r1=np.array([1, 0, 0]),
            r2=np.array([0, 1, 0]),
            r_cm=np.zeros(3),
            p1=np.array([0, 0.5, 0]),
            p2=np.array([0.5, 0, 0]),
            p_cm=np.zeros(3),
            dimension=3
        )

        r1, r2, p1, p2 = state.internal_state

        np.testing.assert_array_equal(r1, state.r1)
        np.testing.assert_array_equal(r2, state.r2)
        np.testing.assert_array_equal(p1, state.p1)
        np.testing.assert_array_equal(p2, state.p2)


class TestCartesianToJacobi:
    """Test Cartesian → Jacobi transformation"""

    def test_simple_configuration(self):
        """Test transformation for simple configuration"""
        # Simple configuration: three bodies along x-axis
        positions = np.array([
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 2.0, 0.0]
        ])
        velocities = np.zeros((3, 3))

        masses = Masses(1.0, 1.0, 1.0)
        state_cart = CartesianState(positions, velocities, dimension=3)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        # r1 should be r1 - r2 = (1,0,0) - (-1,0,0) = (2,0,0)
        expected_r1 = np.array([2.0, 0.0, 0.0])
        np.testing.assert_allclose(state_jac.r1, expected_r1, rtol=1e-10)

        # Should be in barycentric frame
        assert state_jac.validate()

    def test_equal_masses(self):
        """Test with equal masses"""
        masses = Masses.equal_masses(1.0)

        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        # Reduced masses should be correct
        assert masses.mu12 == 0.5
        assert np.abs(masses.mu3 - 2.0/3.0) < 1e-10

        # Should be in barycentric frame
        assert np.linalg.norm(state_jac.r_cm) < 1e-12
        assert np.linalg.norm(state_jac.p_cm) < 1e-12

    def test_hierarchical_masses(self):
        """Test with hierarchical mass system"""
        masses = Masses(1000.0, 1.0, 0.001)  # Sun-planet-asteroid like

        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        # Should be in barycentric frame (use looser tolerance)
        assert np.linalg.norm(state_jac.r_cm) < 1e-12
        assert np.linalg.norm(state_jac.p_cm) < 1e-12


class TestJacobiToCartesian:
    """Test Jacobi → Cartesian transformation"""

    def test_simple_inverse(self):
        """Test inverse transformation"""
        # Create a Jacobi state
        state_jac = JacobiState(
            r1=np.array([1.0, 0.0, 0.0]),
            r2=np.array([0.0, 1.0, 0.0]),
            r_cm=np.zeros(3),
            p1=np.array([0.0, 0.5, 0.0]),
            p2=np.array([0.5, 0.0, 0.0]),
            p_cm=np.zeros(3),
            dimension=3
        )

        masses = Masses(1.0, 1.0, 1.0)
        state_cart = jacobi_to_cartesian(state_jac, masses)

        # Should produce valid Cartesian state
        assert state_cart.positions.shape == (3, 3)
        assert state_cart.velocities.shape == (3, 3)

        # Should be in barycentric frame
        m = masses.as_array()
        r_cm = np.sum(state_cart.positions * m[:, np.newaxis], axis=0)
        assert np.linalg.norm(r_cm) < 1e-12


class TestRoundtripAccuracy:
    """Test round-trip transformation accuracy"""

    def test_roundtrip_equal_masses(self):
        """Test Cartesian → Jacobi → Cartesian with equal masses"""
        masses = Masses(1.0, 1.0, 1.0)

        # Random Cartesian state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        # Round trip
        state_jac = cartesian_to_jacobi(state_cart, masses)
        state_cart_back = jacobi_to_cartesian(state_jac, masses)

        # Check accuracy
        pos_error = np.linalg.norm(state_cart.positions - state_cart_back.positions)
        vel_error = np.linalg.norm(state_cart.velocities - state_cart_back.velocities)

        assert pos_error < 1e-13
        assert vel_error < 1e-13

    def test_roundtrip_unequal_masses(self):
        """Test round-trip with unequal masses"""
        masses = Masses(10.0, 1.0, 0.1)

        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        # Round trip
        state_jac = cartesian_to_jacobi(state_cart, masses)
        state_cart_back = jacobi_to_cartesian(state_jac, masses)

        # Check accuracy
        pos_error = np.linalg.norm(state_cart.positions - state_cart_back.positions)
        vel_error = np.linalg.norm(state_cart.velocities - state_cart_back.velocities)

        assert pos_error < 1e-12
        assert vel_error < 1e-12

    def test_roundtrip_planar(self):
        """Test round-trip for planar motion"""
        masses = Masses(1.0, 2.0, 3.0)

        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Round trip
        state_jac = cartesian_to_jacobi(state_cart, masses)
        state_cart_back = jacobi_to_cartesian(state_jac, masses)

        # Check planar constraint preserved
        assert np.allclose(state_cart_back.positions[:, 2], 0, atol=1e-14)
        assert np.allclose(state_cart_back.velocities[:, 2], 0, atol=1e-14)

        # Check accuracy
        pos_error = np.max(np.abs(state_cart.positions - state_cart_back.positions))
        vel_error = np.max(np.abs(state_cart.velocities - state_cart_back.velocities))

        assert pos_error < 1e-13
        assert vel_error < 1e-13

    def test_roundtrip_multiple_samples(self):
        """Test round-trip for many random samples"""
        masses = Masses(1.0, 1.5, 2.0)
        results = test_jacobi_roundtrip(masses, n_samples=100, dimension=3)

        # Should have very small errors
        assert results['max_error'] < 1e-12
        assert results['mean_error'] < 1e-13


class TestJacobiHamiltonian:
    """Test Hamiltonian in Jacobi coordinates"""

    def test_hamiltonian_decomposition(self):
        """Test H = H_internal + H_cm decomposition"""
        masses = Masses(1.0, 1.0, 1.0)

        # Create state in barycentric frame (p_cm = 0)
        state_jac = JacobiState(
            r1=np.array([1.0, 0.0, 0.0]),
            r2=np.array([0.0, 1.0, 0.0]),
            r_cm=np.zeros(3),
            p1=np.array([0.0, 0.5, 0.0]),
            p2=np.array([0.5, 0.0, 0.0]),
            p_cm=np.zeros(3),
            dimension=3
        )

        H_internal, H_cm = compute_jacobi_hamiltonian(state_jac, masses)

        # H_cm should be zero (barycentric frame)
        assert abs(H_cm) < 1e-14

        # H_internal should be non-zero
        assert abs(H_internal) > 0

    def test_energy_conservation(self):
        """Energy in Jacobi and Cartesian should match"""
        masses = Masses(1.0, 2.0, 3.0)

        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        # Compute energy both ways
        from src.python.coordinates.cartesian import compute_energy
        E_cart = compute_energy(state_cart, masses)
        E_jac = state_jac.compute_energy(masses)

        # Should match
        np.testing.assert_allclose(E_cart, E_jac, rtol=1e-12)

    def test_hamiltonian_decoupling(self):
        """Test that H_internal is independent of r_cm"""
        masses = Masses(1.0, 1.0, 1.0)

        state_jac = JacobiState(
            r1=np.array([1.0, 0.0, 0.0]),
            r2=np.array([0.0, 1.0, 0.0]),
            r_cm=np.zeros(3),
            p1=np.array([0.0, 0.5, 0.0]),
            p2=np.array([0.5, 0.0, 0.0]),
            p_cm=np.zeros(3),
            dimension=3
        )

        # Verify decoupling
        assert verify_hamiltonian_decoupling(state_jac, masses)

    def test_zero_velocity_state(self):
        """Test Hamiltonian for zero velocity state"""
        masses = Masses(1.0, 1.0, 1.0)

        state_jac = JacobiState(
            r1=np.array([1.0, 0.0, 0.0]),
            r2=np.array([0.0, 1.0, 0.0]),
            r_cm=np.zeros(3),
            p1=np.zeros(3),
            p2=np.zeros(3),
            p_cm=np.zeros(3),
            dimension=3
        )

        H_internal, H_cm = compute_jacobi_hamiltonian(state_jac, masses)

        # Kinetic energy should be zero
        # H_internal should just be potential energy (negative)
        assert H_cm == 0
        assert H_internal < 0  # Potential energy only


class TestReducedMasses:
    """Test reduced mass calculations"""

    def test_equal_masses_mu12(self):
        """Equal masses: μ₁₂ = m/2"""
        masses = Masses(2.0, 2.0, 2.0)
        assert masses.mu12 == 1.0

    def test_equal_masses_mu3(self):
        """Equal masses: μ₃ = 2m²/(3m) = 2m/3"""
        masses = Masses(3.0, 3.0, 3.0)
        expected = (3.0 + 3.0) * 3.0 / 9.0  # 6 * 3 / 9 = 2
        np.testing.assert_allclose(masses.mu3, expected, rtol=1e-10)

    def test_hierarchical_masses(self):
        """Test reduced masses for hierarchical system"""
        masses = Masses(1000.0, 1.0, 0.001)

        # μ₁₂ ≈ m₂ (since m₁ >> m₂)
        assert abs(masses.mu12 - 1.0) / 1.0 < 0.01

        # μ₃ ≈ m₃ (since (m₁+m₂) >> m₃)
        assert abs(masses.mu3 - 0.001) / 0.001 < 0.01


class TestJacobiMethods:
    """Test methods on JacobiState"""

    def test_to_cartesian_method(self):
        """Test to_cartesian method"""
        state_jac = JacobiState(
            r1=np.array([1.0, 0.0, 0.0]),
            r2=np.array([0.0, 1.0, 0.0]),
            r_cm=np.zeros(3),
            p1=np.array([0.0, 0.5, 0.0]),
            p2=np.array([0.5, 0.0, 0.0]),
            p_cm=np.zeros(3),
            dimension=3
        )
        masses = Masses(1.0, 1.0, 1.0)

        state_cart = state_jac.to_cartesian(masses)

        assert isinstance(state_cart, CartesianState)
        assert state_cart.dimension == 3

    def test_compute_angular_momentum(self):
        """Test angular momentum computation"""
        masses = Masses(1.0, 1.0, 1.0)

        # Create random state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state_cart = CartesianState(positions, velocities)
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        # Compute L both ways
        from src.python.coordinates.cartesian import compute_angular_momentum
        L_cart = compute_angular_momentum(state_cart, masses)
        L_jac = state_jac.compute_angular_momentum(masses)

        # Should match
        np.testing.assert_allclose(L_cart, L_jac, rtol=1e-12)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
