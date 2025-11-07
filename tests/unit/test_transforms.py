"""
Unit tests for coordinate transformation registry.
"""

import numpy as np
import pytest

from src.python.coordinates import (
    CartesianState,
    JacobiState,
    ShapeSpaceState,
    Masses,
    CoordinateTransform,
    enforce_barycenter,
)


class TestCoordinateTransform:
    """Test CoordinateTransform registry"""

    def test_identity_transform(self):
        """Test that transforming to same type returns self"""
        masses = Masses.equal_masses()

        state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state = enforce_barycenter(state, masses)

        state_transformed = CoordinateTransform.transform(state, CartesianState, masses)

        assert state is state_transformed

    def test_cartesian_to_jacobi(self):
        """Test Cartesian → Jacobi transformation"""
        masses = Masses.equal_masses()

        state_cart = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state_cart = enforce_barycenter(state_cart, masses)

        state_jacobi = CoordinateTransform.transform(state_cart, JacobiState, masses)

        assert isinstance(state_jacobi, JacobiState)

    def test_jacobi_to_cartesian(self):
        """Test Jacobi → Cartesian transformation"""
        masses = Masses.equal_masses()

        # Create Jacobi state
        state_jacobi = JacobiState(
            np.random.randn(3),
            np.random.randn(3),
            np.zeros(3),
            np.random.randn(3),
            np.random.randn(3),
            np.zeros(3),
        )

        state_cart = CoordinateTransform.transform(state_jacobi, CartesianState, masses)

        assert isinstance(state_cart, CartesianState)

    def test_cartesian_to_shape(self):
        """Test Cartesian → ShapeSpace transformation"""
        masses = Masses.equal_masses()

        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        state_cart = CartesianState(positions, velocities, dimension=2)

        state_shape = CoordinateTransform.transform(state_cart, ShapeSpaceState, masses)

        assert isinstance(state_shape, ShapeSpaceState)
        assert state_shape.validate()  # Should satisfy triangle inequality


class TestRoundtripTransforms:
    """Test round-trip transformations"""

    def test_cartesian_jacobi_roundtrip(self):
        """Test Cartesian → Jacobi → Cartesian"""
        masses = Masses(1.0, 2.0, 3.0)

        state_cart = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state_cart = enforce_barycenter(state_cart, masses)

        error = CoordinateTransform.roundtrip_error(state_cart, JacobiState, masses)

        assert error < 1e-12

    def test_multiple_mass_configs(self):
        """Test round-trip with various mass configurations"""
        mass_configs = [
            Masses.equal_masses(),
            Masses(1.0, 10.0, 0.1),
            Masses(100.0, 1.0, 1.0),
        ]

        for masses in mass_configs:
            state = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
            state = enforce_barycenter(state, masses)

            error = CoordinateTransform.roundtrip_error(state, JacobiState, masses)

            assert error < 1e-11


class TestEnergyConservationAcrossTransforms:
    """Test that energy is conserved across transformations"""

    def test_energy_cartesian_jacobi(self):
        """Test energy matches between Cartesian and Jacobi"""
        masses = Masses.equal_masses()

        state_cart = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state_cart = enforce_barycenter(state_cart, masses)

        state_jacobi = CoordinateTransform.transform(state_cart, JacobiState, masses)

        E_cart = state_cart.compute_energy(masses)
        E_jacobi = state_jacobi.compute_energy(masses)

        assert np.isclose(E_cart, E_jacobi)

    def test_angular_momentum_cartesian_jacobi(self):
        """Test angular momentum matches between Cartesian and Jacobi"""
        masses = Masses(1.0, 2.0, 3.0)

        state_cart = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3))
        state_cart = enforce_barycenter(state_cart, masses)

        state_jacobi = CoordinateTransform.transform(state_cart, JacobiState, masses)

        L_cart = state_cart.compute_angular_momentum(masses)
        L_jacobi = state_jacobi.compute_angular_momentum(masses)

        np.testing.assert_allclose(L_cart, L_jacobi, atol=1e-12)
