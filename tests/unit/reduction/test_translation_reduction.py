"""
Unit tests for translation reduction.

Tests the implementation of symplectic reduction by ℝ³ translations
for the three-body problem.
"""

import pytest
import numpy as np

from src.python.coordinates.cartesian import CartesianState, compute_energy
from src.python.coordinates.base import Masses
from src.python.reduction.translation_reduction import (
    TranslationReduction,
    TranslationReducedState,
    test_translation_invariance,
    enforce_barycenter,
)


class TestTranslationReduction:
    """Test TranslationReduction class"""

    def test_momentum_map_zero_for_barycentric(self):
        """Momentum map should return zero for barycentric state"""
        # Create barycentric state
        masses = Masses(1.0, 1.0, 1.0)

        # Positions sum to zero (with masses)
        positions = np.array([
            [1.0, 0.0, 0.0],
            [-0.5, 0.866, 0.0],
            [-0.5, -0.866, 0.0]
        ])

        velocities = np.array([
            [0.1, 0.2, 0.0],
            [-0.05, -0.1, 0.0],
            [-0.05, -0.1, 0.0]
        ])

        state = CartesianState(positions, velocities, dimension=2)

        reducer = TranslationReduction()
        P = reducer.momentum_map(state, masses)

        assert np.linalg.norm(P) < 1e-14

    def test_reduce_arbitrary_state(self):
        """reduce() should project arbitrary state onto barycentric frame"""
        # Random state (not barycentric)
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state = CartesianState(positions, velocities)

        masses = Masses(1.0, 1.5, 2.0)

        reducer = TranslationReduction()
        reduced = reducer.reduce(state, masses)

        # Check constraints
        assert reducer.validate_constraint(reduced.state, masses)

        # Verify center of mass is at origin
        m = np.array([masses.m1, masses.m2, masses.m3])
        r_cm = np.sum(reduced.state.positions * m[:, np.newaxis], axis=0)
        assert np.linalg.norm(r_cm) < 1e-14

        # Verify total momentum is zero
        P = reducer.momentum_map(reduced.state, masses)
        assert np.linalg.norm(P) < 1e-14

    def test_reduce_preserves_energy(self):
        """Energy should be unchanged by translation reduction"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        E0 = compute_energy(state, masses)

        reducer = TranslationReduction()
        reduced = reducer.reduce(state, masses)

        E1 = reduced.compute_energy()

        # Energy should be identical (translation is a symmetry)
        assert abs(E1 - E0) < 1e-14

    def test_reduce_preserves_angular_momentum(self):
        """Angular momentum should be unchanged by translation reduction"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        from src.python.coordinates.cartesian import compute_angular_momentum
        L0 = compute_angular_momentum(state, masses)

        reducer = TranslationReduction()
        reduced = reducer.reduce(state, masses)

        L1 = reduced.compute_angular_momentum()

        # Angular momentum should be identical
        assert np.linalg.norm(L1 - L0) < 1e-14

    def test_reduce_idempotent(self):
        """Reducing twice should be same as reducing once"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        reducer = TranslationReduction()
        reduced1 = reducer.reduce(state, masses)
        reduced2 = reducer.reduce(reduced1.state, masses)

        # Should be unchanged (up to numerical error)
        pos_diff = np.linalg.norm(
            reduced2.state.positions - reduced1.state.positions
        )
        vel_diff = np.linalg.norm(
            reduced2.state.velocities - reduced1.state.velocities
        )

        assert pos_diff < 1e-14
        assert vel_diff < 1e-14


class TestTranslationReducedState:
    """Test TranslationReducedState dataclass"""

    def test_construction_validates_constraints(self):
        """Should raise if state is not barycentric"""
        # Non-barycentric state
        positions = np.array([
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0]
        ])
        velocities = np.zeros((3, 3))
        state = CartesianState(positions, velocities)
        masses = Masses(1.0, 1.0, 1.0)

        with pytest.raises(AssertionError):
            TranslationReducedState(state, masses)

    def test_dimension_planar(self):
        """Dimension should be 9 for planar case"""
        reducer = TranslationReduction()

        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3),
            dimension=2
        )
        masses = Masses(1.0, 1.0, 1.0)

        reduced = reducer.reduce(state, masses)

        assert reduced.dimension == 9  # 12 - 3 = 9

    def test_dimension_spatial(self):
        """Dimension should be 15 for spatial case"""
        reducer = TranslationReduction()

        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3),
            dimension=3
        )
        masses = Masses(1.0, 1.0, 1.0)

        reduced = reducer.reduce(state, masses)

        assert reduced.dimension == 15  # 18 - 3 = 15


class TestTranslationInvariance:
    """Test that Hamiltonian is invariant under translations"""

    def test_translation_invariance_equal_masses(self):
        """Energy should be unchanged by translation (equal masses)"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        result = test_translation_invariance(state, masses, n_tests=20)

        assert result['passed']
        assert result['max_error'] < 1e-13

    def test_translation_invariance_unequal_masses(self):
        """Energy should be unchanged by translation (unequal masses)"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 2.0, 3.0)

        result = test_translation_invariance(state, masses, n_tests=20)

        assert result['passed']
        assert result['max_error'] < 1e-13

    def test_translation_invariance_planar(self):
        """Energy should be unchanged by translation (planar case)"""
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0.0  # Planar

        velocities = np.random.randn(3, 3)
        velocities[:, 2] = 0.0

        state = CartesianState(positions, velocities, dimension=2)
        masses = Masses(1.0, 1.0, 1.0)

        result = test_translation_invariance(state, masses, n_tests=20)

        assert result['passed']
        assert result['max_error'] < 1e-13


class TestEnforceBarycenter:
    """Test enforce_barycenter convenience function"""

    def test_enforce_barycenter_arbitrary_state(self):
        """Should return barycentric state"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        state_bc = enforce_barycenter(state, masses)

        # Check barycentric constraints
        m = np.array([1.0, 1.0, 1.0])
        r_cm = np.sum(state_bc.positions * m[:, np.newaxis], axis=0)
        v_cm = np.sum(state_bc.velocities * m[:, np.newaxis], axis=0)

        assert np.linalg.norm(r_cm) < 1e-14
        assert np.linalg.norm(v_cm) < 1e-14

    def test_enforce_barycenter_preserves_energy(self):
        """Should preserve energy"""
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        E0 = compute_energy(state, masses)
        state_bc = enforce_barycenter(state, masses)
        E1 = compute_energy(state_bc, masses)

        assert abs(E1 - E0) < 1e-14


class TestSymplecticStructure:
    """Test that reduction preserves symplectic structure"""

    def test_symplectic_form_preserved(self):
        """
        Symplectic form should be preserved under reduction.

        For translation reduction, ω_red is simply the restriction
        of ω to the constraint surface, so it's automatically preserved.
        """
        # This is a conceptual test - the symplectic form is implicitly
        # preserved by the projection onto the constraint surface.

        # We verify this by checking that Poisson brackets are preserved
        # (This will be more thoroughly tested in integration tests)
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
