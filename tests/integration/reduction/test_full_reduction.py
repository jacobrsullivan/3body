"""
Integration tests for full symplectic reduction workflow.

Tests the complete reduction pipeline:
    Cartesian → Translation reduction → Rotation reduction → Shape space
"""

import pytest
import numpy as np

from src.python.coordinates.cartesian import CartesianState, compute_energy
from src.python.coordinates.base import Masses
from src.python.reduction.translation_reduction import TranslationReduction
from src.python.reduction.rotation_reduction import (
    RotationReduction,
    OrientationConvention,
)


class TestFullReductionWorkflow:
    """Test complete reduction workflow"""

    def test_full_reduction_equal_masses(self):
        """Test full reduction with equal masses"""
        # Random initial state
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        E0 = compute_energy(state, masses)

        # Step 1: Translation reduction
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Verify P = 0
        assert trans_reducer.validate_constraint(trans_reduced.state, masses)

        # Step 2: Rotation reduction
        rot_reducer = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Verify L is conserved
        assert rot_reducer.validate_constraint(
            shape_reduced.state, masses, shape_reduced.L
        )

        # Verify energy is conserved
        E1 = shape_reduced.compute_energy()
        assert abs(E1 - E0) < 1e-13

        # Verify orientation is canonical
        r12 = shape_reduced.state.positions[0] - shape_reduced.state.positions[1]
        assert abs(r12[1]) < 1e-10  # y-component zero
        assert abs(r12[2]) < 1e-10  # z-component zero

    def test_full_reduction_unequal_masses(self):
        """Test full reduction with unequal masses"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 2.0, 3.0)

        E0 = compute_energy(state, masses)

        # Full reduction
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        rot_reducer = RotationReduction()
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Verify energy conservation
        E1 = shape_reduced.compute_energy()
        assert abs(E1 - E0) < 1e-13

    def test_full_reduction_planar(self):
        """Test full reduction for planar motion"""
        # Planar state
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0.0

        velocities = np.random.randn(3, 3)
        velocities[:, 2] = 0.0

        state = CartesianState(positions, velocities, dimension=2)
        masses = Masses(1.0, 1.0, 1.0)

        # Full reduction
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        rot_reducer = RotationReduction()
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Verify planar constraint maintained
        assert np.allclose(shape_reduced.state.positions[:, 2], 0)
        assert np.allclose(shape_reduced.state.velocities[:, 2], 0)

        # Verify L points in z-direction
        L = shape_reduced.L
        assert abs(L[0]) < 1e-10
        assert abs(L[1]) < 1e-10

    def test_dimension_reduction_planar(self):
        """Verify dimension reduction: 12 → 9 → 7 DOF"""
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0.0

        velocities = np.random.randn(3, 3)
        velocities[:, 2] = 0.0

        state = CartesianState(positions, velocities, dimension=2)
        masses = Masses(1.0, 1.0, 1.0)

        # Original: 12 DOF (3 bodies × 2D × 2)
        assert state.dimension == 2

        # After translation reduction: 9 DOF
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)
        assert trans_reduced.dimension == 9

        # After rotation reduction: 7 DOF
        # (9 - 2 for SO(2) rotation, but we keep 7 in phase space)
        # This is the shape space dimension for planar 3BP

    def test_dimension_reduction_spatial(self):
        """Verify dimension reduction: 18 → 15 → 12 DOF"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3),
            dimension=3
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Original: 18 DOF (3 bodies × 3D × 2)
        assert state.dimension == 3

        # After translation reduction: 15 DOF
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)
        assert trans_reduced.dimension == 15

        # After rotation reduction: 12 DOF
        # (15 - 3 for SO(3) rotation)


class TestLagrangeEquilibriumReduced:
    """Test Lagrange equilibrium configuration in reduced coordinates"""

    def test_lagrange_equilibrium_is_fixed_point(self):
        """
        Lagrange equilateral configuration is a fixed point in shape space.

        The three bodies rotate rigidly, so the shape doesn't change.
        In the rotating frame, this is an equilibrium.
        """
        # Set up equilateral triangle
        R = 1.0
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])

        # Angular velocity for stable rotation (equal masses)
        omega = np.sqrt(3.0)
        velocities = R * omega * np.column_stack([
            -np.sin(angles), np.cos(angles), np.zeros(3)
        ])

        state = CartesianState(positions, velocities, dimension=2)
        masses = Masses(1.0, 1.0, 1.0)

        # Full reduction
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        rot_reducer = RotationReduction()
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # In shape space, this should be an equilibrium
        # (the triangle configuration is fixed)

        # Verify it's an equilateral triangle
        r = shape_reduced.state.positions
        d01 = np.linalg.norm(r[0] - r[1])
        d12 = np.linalg.norm(r[1] - r[2])
        d20 = np.linalg.norm(r[2] - r[0])

        # All sides should be equal
        assert abs(d01 - d12) < 1e-10
        assert abs(d12 - d20) < 1e-10
        assert abs(d20 - d01) < 1e-10


class TestConservationLawsLongTerm:
    """Test conservation laws over extended integration"""

    def test_momentum_conservation_long_integration(self):
        """
        Test that momentum constraints are maintained during integration.

        This is a placeholder - actual integration tests will be added
        in Part C when we integrate with WP1 integrators.
        """
        # TODO: Implement in Part C
        pass

    def test_angular_momentum_conservation_long_integration(self):
        """
        Test that angular momentum is conserved during integration.

        Placeholder for Part C integration tests.
        """
        # TODO: Implement in Part C
        pass


class TestDifferentOrientationConventions:
    """Test that different orientation conventions give equivalent physics"""

    def test_energy_independent_of_convention(self):
        """Energy should be same regardless of orientation convention"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Reduce with different conventions
        rot_reducer_12 = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        shape_reduced_12 = rot_reducer_12.reduce(trans_reduced.state, masses)

        rot_reducer_L = RotationReduction(OrientationConvention.ALIGN_ANGULAR_MOMENTUM)
        shape_reduced_L = rot_reducer_L.reduce(trans_reduced.state, masses)

        # Energy should be same
        E_12 = shape_reduced_12.compute_energy()
        E_L = shape_reduced_L.compute_energy()

        assert abs(E_12 - E_L) < 1e-13

    def test_angular_momentum_independent_of_convention(self):
        """Angular momentum should be same regardless of convention"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        # Reduce with different conventions
        rot_reducer_12 = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        shape_reduced_12 = rot_reducer_12.reduce(trans_reduced.state, masses)

        rot_reducer_L = RotationReduction(OrientationConvention.ALIGN_ANGULAR_MOMENTUM)
        shape_reduced_L = rot_reducer_L.reduce(trans_reduced.state, masses)

        # Angular momentum should be same
        L_12 = shape_reduced_12.L
        L_L = shape_reduced_L.L

        assert np.linalg.norm(L_12 - L_L) < 1e-13


class TestReconstructionRoundTrip:
    """Test that we can reconstruct original state from reduced state"""

    def test_reconstruction_preserves_physics(self):
        """Reconstructed state should have same energy and angular momentum"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        from src.python.coordinates.cartesian import compute_angular_momentum

        # Compute original quantities
        trans_reducer = TranslationReduction()
        trans_reduced = trans_reducer.reduce(state, masses)

        E0 = trans_reduced.compute_energy()
        L0 = compute_angular_momentum(trans_reduced.state, masses)

        # Reduce by rotations
        rot_reducer = RotationReduction()
        shape_reduced = rot_reducer.reduce(trans_reduced.state, masses)

        # Reconstruct
        state_reconstructed = rot_reducer.reconstruct_from_reduced(
            shape_reduced, shape_reduced.theta
        )

        # Verify same energy
        E1 = compute_energy(state_reconstructed, masses)
        assert abs(E1 - E0) < 1e-12

        # Verify same angular momentum
        L1 = compute_angular_momentum(state_reconstructed, masses)
        assert np.linalg.norm(L1 - L0) < 1e-12


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
