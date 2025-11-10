"""
Unit tests for rotation reduction.

Tests the implementation of symplectic reduction by SO(3) rotations
for the three-body problem.
"""

import pytest
import numpy as np

from src.python.coordinates.cartesian import CartesianState, compute_energy
from src.python.coordinates.base import Masses
from src.python.reduction.translation_reduction import TranslationReduction
from src.python.reduction.rotation_reduction import (
    RotationReduction,
    RotationReducedState,
    OrientationConvention,
    test_rotation_invariance,
)


class TestRotationReduction:
    """Test RotationReduction class"""

    def test_momentum_map_computes_angular_momentum(self):
        """Momentum map should return angular momentum"""
        # Create simple state with known angular momentum
        masses = Masses(1.0, 1.0, 1.0)

        # Circular motion in xy-plane
        R = 1.0
        omega = 1.0
        positions = R * np.array([
            [1.0, 0.0, 0.0],
            [-0.5, 0.866, 0.0],
            [-0.5, -0.866, 0.0]
        ])

        velocities = R * omega * np.array([
            [0.0, 1.0, 0.0],
            [-0.866, -0.5, 0.0],
            [0.866, -0.5, 0.0]
        ])

        state = CartesianState(positions, velocities, dimension=2)

        # First reduce by translations
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Compute angular momentum
        rot_reducer = RotationReduction()
        L = rot_reducer.momentum_map(trans_reduced.state, masses)

        # For planar motion, L should point in z-direction
        assert abs(L[0]) < 1e-10
        assert abs(L[1]) < 1e-10
        assert L[2] > 0  # Positive z-component

    def test_reduce_fixes_orientation(self):
        """reduce() should fix orientation to canonical form"""
        # Random barycentric state
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Reduce by translations first
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Reduce by rotations
        rot_reducer = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Check that body 1-2 axis is aligned with x-axis
        r12 = rot_reduced.state.positions[0] - rot_reduced.state.positions[1]
        assert abs(r12[1]) < 1e-10  # y-component should be zero
        assert abs(r12[2]) < 1e-10  # z-component should be zero
        assert r12[0] > 0  # x-component should be positive

    def test_reduce_preserves_angular_momentum(self):
        """Angular momentum should be unchanged by rotation reduction"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Reduce by translations
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Compute initial angular momentum
        rot_reducer = RotationReduction()
        L0 = rot_reducer.momentum_map(trans_reduced.state, masses)

        # Reduce by rotations
        rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Stored L should match computed L
        assert np.linalg.norm(rot_reduced.L - L0) < 1e-14

        # After reduction, L should still be the same
        L1 = rot_reducer.momentum_map(rot_reduced.state, masses)
        assert np.linalg.norm(L1 - L0) < 1e-14

    def test_reduce_preserves_energy(self):
        """Energy should be unchanged by rotation reduction"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Reduce by translations
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        E0 = trans_reduced.compute_energy()

        # Reduce by rotations
        rot_reducer = RotationReduction()
        rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        E1 = rot_reduced.compute_energy()

        # Energy should be identical (rotation is a symmetry)
        assert abs(E1 - E0) < 1e-14

    def test_reduce_raises_if_not_barycentric(self):
        """Should raise if state is not in barycentric frame"""
        # Non-barycentric state
        state = CartesianState(
            positions=np.array([
                [1.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
                [3.0, 0.0, 0.0]
            ]),
            velocities=np.zeros((3, 3))
        )
        masses = Masses(1.0, 1.0, 1.0)

        rot_reducer = RotationReduction()

        with pytest.raises(ValueError, match="barycentric"):
            rot_reducer.reduce(state, masses)

    def test_reconstruct_from_reduced(self):
        """Should be able to reconstruct original orientation"""
        # Create barycentric state
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Reduce by rotations
        rot_reducer = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Reconstruct
        state_reconstructed = rot_reducer.reconstruct_from_reduced(
            rot_reduced, rot_reduced.theta
        )

        # Should match original (up to numerical error)
        pos_diff = np.linalg.norm(
            state_reconstructed.positions - trans_reduced.state.positions
        )
        vel_diff = np.linalg.norm(
            state_reconstructed.velocities - trans_reduced.state.velocities
        )

        assert pos_diff < 1e-12
        assert vel_diff < 1e-12


class TestRotationMatrices:
    """Test rotation matrix utilities"""

    def test_rotation_matrix_z_identity(self):
        """R_z(0) should be identity"""
        R = RotationReduction._rotation_matrix_z(0.0)
        assert np.allclose(R, np.eye(3))

    def test_rotation_matrix_z_orthogonal(self):
        """R_z should be orthogonal: R^T R = I"""
        theta = np.pi / 4
        R = RotationReduction._rotation_matrix_z(theta)

        assert np.allclose(R @ R.T, np.eye(3))
        assert np.allclose(R.T @ R, np.eye(3))

    def test_rotation_matrix_z_determinant(self):
        """R_z should have det = 1 (proper rotation)"""
        theta = np.pi / 3
        R = RotationReduction._rotation_matrix_z(theta)

        assert np.abs(np.linalg.det(R) - 1.0) < 1e-14

    def test_rotation_matrix_axis_angle_identity(self):
        """R(n, 0) should be identity"""
        n = np.array([1.0, 0.0, 0.0])
        R = RotationReduction._rotation_matrix_axis_angle(n, 0.0)

        assert np.allclose(R, np.eye(3))

    def test_rotation_matrix_axis_angle_orthogonal(self):
        """R should be orthogonal"""
        n = np.array([1.0, 1.0, 1.0]) / np.sqrt(3)
        theta = np.pi / 4
        R = RotationReduction._rotation_matrix_axis_angle(n, theta)

        assert np.allclose(R @ R.T, np.eye(3))
        assert np.allclose(R.T @ R, np.eye(3))

    def test_rotation_matrix_axis_angle_determinant(self):
        """R should have det = 1"""
        n = np.array([0.0, 1.0, 0.0])
        theta = np.pi / 6
        R = RotationReduction._rotation_matrix_axis_angle(n, theta)

        assert np.abs(np.linalg.det(R) - 1.0) < 1e-14

    def test_rotation_matrix_axis_angle_rodrigues(self):
        """Verify Rodrigues formula explicitly"""
        # Rotation about z-axis should match R_z
        n = np.array([0.0, 0.0, 1.0])
        theta = np.pi / 4

        R_rodrigues = RotationReduction._rotation_matrix_axis_angle(n, theta)
        R_z = RotationReduction._rotation_matrix_z(theta)

        assert np.allclose(R_rodrigues, R_z)


class TestOrientationConventions:
    """Test different orientation-fixing conventions"""

    def test_align_axis_12_planar(self):
        """ALIGN_AXIS_12 should align 1-2 axis with x-axis"""
        state = CartesianState(
            positions=np.array([
                [1.0, 1.0, 0.0],
                [0.0, 0.0, 0.0],
                [-1.0, 0.5, 0.0]
            ]),
            velocities=np.random.randn(3, 3),
            dimension=2
        )
        masses = Masses(1.0, 1.0, 1.0)

        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        rot_reducer = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        r12 = rot_reduced.state.positions[0] - rot_reduced.state.positions[1]
        assert abs(r12[1]) < 1e-10
        assert abs(r12[2]) < 1e-10

    def test_align_angular_momentum_spatial(self):
        """ALIGN_ANGULAR_MOMENTUM should align L with z-axis"""
        # Create state with angular momentum not in z-direction
        state = CartesianState(
            positions=np.array([
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [-1.0, -1.0, 0.0]
            ]),
            velocities=np.array([
                [0.0, 0.0, 1.0],
                [0.0, 0.0, -0.5],
                [0.0, 0.0, -0.5]
            ])
        )
        masses = Masses(1.0, 1.0, 1.0)

        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        rot_reducer = RotationReduction(OrientationConvention.ALIGN_ANGULAR_MOMENTUM)
        rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # L should point in z-direction
        L = rot_reduced.L
        L_hat = L / np.linalg.norm(L)
        z_hat = np.array([0.0, 0.0, 1.0])

        # Allow for sign flip
        assert (np.allclose(L_hat, z_hat) or np.allclose(L_hat, -z_hat))


class TestRotationInvariance:
    """Test that Hamiltonian is invariant under rotations"""

    def test_rotation_invariance_equal_masses(self):
        """Energy should be unchanged by rotation (equal masses)"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        result = test_rotation_invariance(state, masses, n_tests=20)

        assert result['passed']
        assert result['max_error'] < 1e-13

    def test_rotation_invariance_unequal_masses(self):
        """Energy should be unchanged by rotation (unequal masses)"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 2.0, 3.0)

        result = test_rotation_invariance(state, masses, n_tests=20)

        assert result['passed']
        assert result['max_error'] < 1e-13

    def test_rotation_invariance_planar(self):
        """Energy should be unchanged by rotation (planar case)"""
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0.0

        velocities = np.random.randn(3, 3)
        velocities[:, 2] = 0.0

        state = CartesianState(positions, velocities, dimension=2)
        masses = Masses(1.0, 1.0, 1.0)

        result = test_rotation_invariance(state, masses, n_tests=20)

        assert result['passed']
        assert result['max_error'] < 1e-13


class TestRotationReducedState:
    """Test RotationReducedState dataclass"""

    def test_is_planar_detection(self):
        """is_planar should correctly identify planar states"""
        # Create planar reduced state
        state = CartesianState(
            positions=np.array([
                [1.0, 0.0, 0.0],
                [-0.5, 0.866, 0.0],
                [-0.5, -0.866, 0.0]
            ]),
            velocities=np.zeros((3, 3)),
            dimension=2
        )
        masses = Masses(1.0, 1.0, 1.0)
        L = np.array([0.0, 0.0, 1.0])

        reduced = RotationReducedState(
            state=state,
            masses=masses,
            L=L
        )

        assert reduced.is_planar

    def test_L_magnitude(self):
        """L_magnitude should return correct magnitude"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)
        L = np.array([1.0, 2.0, 3.0])

        reduced = RotationReducedState(
            state=state,
            masses=masses,
            L=L
        )

        expected_magnitude = np.sqrt(1**2 + 2**2 + 3**2)
        assert abs(reduced.L_magnitude - expected_magnitude) < 1e-14


class TestComposedReduction:
    """Test composed translation + rotation reduction"""

    def test_full_reduction_to_shape_space(self):
        """Compose translation and rotation reduction"""
        # Random state
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Reduce by translations
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Reduce by rotations
        rot_reducer = RotationReduction()
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Verify all constraints
        assert trans_reducer.validate_constraint(shape_reduced.state, masses)
        assert rot_reducer.validate_constraint(
            shape_reduced.state, masses, shape_reduced.L
        )

    def test_full_reduction_preserves_energy(self):
        """Full reduction should preserve energy"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        E0 = compute_energy(state, masses)

        # Full reduction
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        rot_reducer = RotationReduction()
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        E1 = shape_reduced.compute_energy()

        assert abs(E1 - E0) < 1e-14


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
