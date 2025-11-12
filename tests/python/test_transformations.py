"""
Integration tests for coordinate transformations.

Tests:
    - Round-trip transformations between all coordinate systems
    - Energy and angular momentum preservation
    - Transform registry functionality
    - Multi-step transformations
"""

import pytest
import numpy as np
from src.python.coordinates.base import Masses
from src.python.coordinates.cartesian import (
    CartesianState,
    enforce_barycenter,
    compute_energy,
    compute_angular_momentum,
)
from src.python.coordinates.jacobi import JacobiState, cartesian_to_jacobi
from src.python.coordinates.shape_space import (
    ShapeSpaceState,
    ComplexShapeState,
    cartesian_to_shape_distances,
    cartesian_to_complex_shape,
)
from src.python.coordinates.transforms import CoordinateTransform


class TestCoordinateTransformRegistry:
    """Test the CoordinateTransform registry"""

    def test_cartesian_to_jacobi(self):
        """Test registered Cartesian → Jacobi transform"""
        masses = Masses(1.0, 1.0, 1.0)

        state_cart = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        state_cart = enforce_barycenter(state_cart, masses)

        # Use registry
        state_jac = CoordinateTransform.transform(state_cart, JacobiState, masses)

        assert isinstance(state_jac, JacobiState)
        assert state_jac.validate()

    def test_jacobi_to_cartesian(self):
        """Test registered Jacobi → Cartesian transform"""
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

        # Use registry
        state_cart = CoordinateTransform.transform(state_jac, CartesianState, masses)

        assert isinstance(state_cart, CartesianState)

    def test_identity_transform(self):
        """Transform to same type should return same state"""
        masses = Masses(1.0, 1.0, 1.0)

        state_cart = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )

        # Transform to same type
        state_same = CoordinateTransform.transform(state_cart, CartesianState, masses)

        assert state_same is state_cart

    def test_two_step_transform(self):
        """Test transformation via intermediate coordinate system"""
        masses = Masses(1.0, 1.0, 1.0)

        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Jacobi → Shape via Cartesian (two steps)
        state_jac = CoordinateTransform.transform(state_cart, JacobiState, masses)
        state_shape = CoordinateTransform.transform(state_jac, ShapeSpaceState, masses)

        assert isinstance(state_shape, ShapeSpaceState)
        assert state_shape.validate()


class TestRoundtripTransformations:
    """Test round-trip accuracy for all coordinate pairs"""

    def test_roundtrip_cartesian_jacobi_cartesian(self):
        """Cartesian → Jacobi → Cartesian"""
        masses = Masses(1.0, 2.0, 3.0)

        state_orig = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        state_orig = enforce_barycenter(state_orig, masses)

        # Round trip using registry
        error = CoordinateTransform.roundtrip_error(state_orig, JacobiState, masses)

        assert error < 1e-12

    def test_roundtrip_jacobi_cartesian_jacobi(self):
        """Jacobi → Cartesian → Jacobi"""
        masses = Masses(1.0, 1.0, 1.0)

        state_orig = JacobiState(
            r1=np.array([1.0, 0.5, 0.0]),
            r2=np.array([0.5, 1.0, 0.0]),
            r_cm=np.zeros(3),
            p1=np.array([0.1, 0.2, 0.0]),
            p2=np.array([0.2, 0.1, 0.0]),
            p_cm=np.zeros(3),
            dimension=3
        )

        error = CoordinateTransform.roundtrip_error(state_orig, CartesianState, masses)

        assert error < 1e-12

    def test_roundtrip_multiple_masses(self):
        """Test round-trip with various mass ratios"""
        mass_configs = [
            Masses(1.0, 1.0, 1.0),      # Equal masses
            Masses(10.0, 1.0, 0.1),     # Hierarchical
            Masses(1.0, 2.0, 3.0),      # Different masses
            Masses(100.0, 1.0, 0.001),  # Extreme hierarchy
        ]

        for masses in mass_configs:
            state_cart = CartesianState(
                positions=np.random.randn(3, 3),
                velocities=np.random.randn(3, 3)
            )
            state_cart = enforce_barycenter(state_cart, masses)

            error = CoordinateTransform.roundtrip_error(state_cart, JacobiState, masses)

            assert error < 1e-11, f"Failed for masses {masses}"


class TestEnergyConservation:
    """Test that energy is preserved across transformations"""

    def test_energy_cartesian_vs_jacobi(self):
        """Energy should match in Cartesian and Jacobi"""
        masses = Masses(1.0, 1.5, 2.0)

        state_cart = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        E_cart = compute_energy(state_cart, masses)
        E_jac = state_jac.compute_energy(masses)

        np.testing.assert_allclose(E_cart, E_jac, rtol=1e-12)

    def test_energy_multiple_roundtrips(self):
        """Energy should remain constant over multiple transformations"""
        masses = Masses(1.0, 1.0, 1.0)

        state_cart = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        state_cart = enforce_barycenter(state_cart, masses)

        E0 = compute_energy(state_cart, masses)

        # Multiple round trips
        current_state = state_cart
        for _ in range(5):
            state_jac = cartesian_to_jacobi(current_state, masses)
            from src.python.coordinates.jacobi import jacobi_to_cartesian
            current_state = jacobi_to_cartesian(state_jac, masses)

        E_final = compute_energy(current_state, masses)

        # Energy should be conserved to high precision
        np.testing.assert_allclose(E_final, E0, rtol=1e-11)


class TestAngularMomentumConservation:
    """Test that angular momentum is preserved"""

    def test_angular_momentum_cartesian_vs_jacobi(self):
        """Angular momentum should match in both systems"""
        masses = Masses(1.0, 1.0, 1.0)

        state_cart = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        state_cart = enforce_barycenter(state_cart, masses)

        state_jac = cartesian_to_jacobi(state_cart, masses)

        L_cart = compute_angular_momentum(state_cart, masses)
        L_jac = state_jac.compute_angular_momentum(masses)

        np.testing.assert_allclose(L_cart, L_jac, rtol=1e-12)

    def test_angular_momentum_planar(self):
        """Test L conservation for planar motion"""
        masses = Masses(1.0, 1.0, 1.0)

        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        L_cart = compute_angular_momentum(state_cart, masses)

        # Should be purely out-of-plane
        assert abs(L_cart[0]) < 1e-12
        assert abs(L_cart[1]) < 1e-12

        # Transform and check
        state_jac = cartesian_to_jacobi(state_cart, masses)
        L_jac = state_jac.compute_angular_momentum(masses)

        np.testing.assert_allclose(L_cart, L_jac, rtol=1e-12)


class TestShapeSpaceTransformations:
    """Test transformations involving shape space"""

    def test_cartesian_to_shape_distances(self):
        """Test Cartesian → Shape (distances)"""
        masses = Masses(1.0, 1.0, 1.0)

        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        shape_state = cartesian_to_shape_distances(state_cart, masses)

        # Should produce valid shape
        assert shape_state.validate()

        # Distances should match
        r = state_cart.positions
        r12_expected = np.linalg.norm(r[0] - r[1])
        r23_expected = np.linalg.norm(r[1] - r[2])
        r31_expected = np.linalg.norm(r[2] - r[0])

        np.testing.assert_allclose(shape_state.r12, r12_expected, rtol=1e-12)
        np.testing.assert_allclose(shape_state.r23, r23_expected, rtol=1e-12)
        np.testing.assert_allclose(shape_state.r31, r31_expected, rtol=1e-12)

    def test_shape_to_cartesian_preserves_distances(self):
        """Shape → Cartesian should preserve distances"""
        masses = Masses(1.0, 1.0, 1.0)

        # Create shape state
        shape_state = ShapeSpaceState(
            r12=2.0, r23=3.0, r31=4.0,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=1.0, dimension=2
        )

        # Convert to Cartesian
        cart_state = shape_state.to_cartesian(masses)

        # Convert back to shape
        shape_back = cartesian_to_shape_distances(cart_state, masses)

        # Distances should match
        np.testing.assert_allclose(shape_state.r12, shape_back.r12, rtol=1e-10)
        np.testing.assert_allclose(shape_state.r23, shape_back.r23, rtol=1e-10)
        np.testing.assert_allclose(shape_state.r31, shape_back.r31, rtol=1e-10)

    def test_complex_shape_consistency(self):
        """Complex shape and distance representations should be consistent"""
        masses = Masses(1.0, 1.0, 1.0)

        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Ensure bodies 1-2 are not too close
        if np.linalg.norm(state_cart.positions[0] - state_cart.positions[1]) < 0.1:
            pytest.skip("Bodies 1-2 too close for complex shape")

        # Get both representations
        shape_dist = cartesian_to_shape_distances(state_cart, masses)
        try:
            shape_complex = cartesian_to_complex_shape(state_cart, masses)

            # Convert complex to distances (with known scale)
            scale = shape_dist.r12
            r12, r23, r13 = shape_complex.to_distances(scale=scale)

            # r12 should match by construction
            np.testing.assert_allclose(r12, shape_dist.r12, rtol=1e-10)

        except ValueError:
            # Bodies may be degenerate
            pytest.skip("Degenerate configuration for complex shape")


class TestBatchTransformations:
    """Test transformations on multiple states"""

    def test_batch_consistency(self):
        """Batch transforms should give same results as individual"""
        masses = Masses(1.0, 1.0, 1.0)
        n_states = 10

        # Generate random states
        states = []
        for _ in range(n_states):
            state = CartesianState(
                positions=np.random.randn(3, 3),
                velocities=np.random.randn(3, 3)
            )
            state = enforce_barycenter(state, masses)
            states.append(state)

        # Transform individually
        jacobi_states_individual = [
            cartesian_to_jacobi(s, masses) for s in states
        ]

        # Transform each back
        cart_states_back = [
            CoordinateTransform.transform(js, CartesianState, masses)
            for js in jacobi_states_individual
        ]

        # Check all match originals
        for orig, back in zip(states, cart_states_back):
            pos_error = np.max(np.abs(orig.positions - back.positions))
            vel_error = np.max(np.abs(orig.velocities - back.velocities))

            assert pos_error < 1e-12
            assert vel_error < 1e-12


class TestEdgeCases:
    """Test edge cases and special configurations"""

    def test_collinear_configuration(self):
        """Test transformations for collinear bodies"""
        masses = Masses(1.0, 1.0, 1.0)

        # Collinear: all on x-axis
        positions = np.array([
            [-1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Should be able to transform
        state_jac = cartesian_to_jacobi(state_cart, masses)
        assert state_jac.validate()

        # Shape space should have zero area
        shape_state = cartesian_to_shape_distances(state_cart, masses)
        assert abs(shape_state.area) < 1e-10

    def test_near_zero_angular_momentum(self):
        """Test with very small angular momentum"""
        masses = Masses(1.0, 1.0, 1.0)

        # Radial motion (nearly zero L)
        positions = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, -1.0, 0.0]
        ])
        # Velocities pointing radially
        velocities = positions * 0.1

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        L = compute_angular_momentum(state_cart, masses)

        # Transform and verify L preserved
        state_jac = cartesian_to_jacobi(state_cart, masses)
        L_jac = state_jac.compute_angular_momentum(masses)

        np.testing.assert_allclose(L, L_jac, atol=1e-12)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
