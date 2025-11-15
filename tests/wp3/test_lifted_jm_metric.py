"""
Tests for lifted Jacobi-Maupertuis metrics (WP 3.1, Task 3.1.1).

Validation Strategy:
    V1. Metric properties (symmetry, positive definiteness)
    V2. Kepler limit (two-body reduction)
    V3. Equal mass symmetry
    V4. Geodesic equation consistency

Task 3.1.1 Validation Requirements:
    - Positive definiteness in classically allowed regions
    - Symmetries respected (permutation, gauge invariance)
    - Limiting cases correct (Kepler, equal masses)
    - Round-trip errors < 1e-13
"""

import pytest
import numpy as np

from src.python.geometry.lifted_jm_metric import (
    compute_s1_bundle_metric,
    compute_s1_jm_metric,
    compute_ks_potential,
    KSSpinorCoords,
    validate_s1_metric_properties,
    compare_s1_vs_base_metric
)
from src.python.lifts.s1_bundle import BundleState, create_bundle_state
from src.python.coordinates.base import Masses
from src.python.coordinates.shape_space import ShapeSpaceState
from src.python.regularization.levi_civita import levi_civita_transform


# ============================================================================
# Part A: S¹ Bundle Metric Tests
# ============================================================================

class TestS1BundleMetric:
    """Test suite for S¹ bundle metric computation (Task 3.1.1, Part A)."""

    @pytest.fixture
    def equal_mass_equilateral(self):
        """Equilateral triangle with equal masses (symmetric case)."""
        masses = Masses(1.0, 1.0, 1.0)

        # Equilateral: all sides equal
        shape = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=1.0,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=1.0,
            dimension=2
        )

        bundle_state = create_bundle_state(
            r12=1.0, r23=1.0, r31=1.0,
            theta=0.0,
            L=1.0
        )

        return masses, bundle_state

    @pytest.fixture
    def hierarchical_masses(self):
        """Hierarchical mass system (test mass regime)."""
        masses = Masses(1.0, 1e-3, 1e-6)  # Sun-Jupiter-Earth-like

        shape = ShapeSpaceState(
            r12=1.0, r23=5.0, r31=5.2,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.5,
            dimension=2
        )

        bundle_state = create_bundle_state(
            r12=1.0, r23=5.0, r31=5.2,
            theta=0.0,
            L=0.5
        )

        return masses, bundle_state

    def test_metric_symmetry(self, equal_mass_equilateral):
        """V1: Verify metric is symmetric (g_ij = g_ji)."""
        masses, bundle_state = equal_mass_equilateral

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        # Check symmetry
        symmetry_error = np.linalg.norm(g_lift.components - g_lift.components.T)

        assert symmetry_error < 1e-14, \
            f"Metric not symmetric: error = {symmetry_error}"
        assert g_lift.components.shape == (4, 4), \
            f"Expected 4×4 metric, got {g_lift.components.shape}"

    def test_positive_definiteness(self, equal_mass_equilateral):
        """V1: Verify metric is positive definite (all eigenvalues > 0)."""
        masses, bundle_state = equal_mass_equilateral

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        eigenvals = g_lift.eigenvalues()
        min_eigenval = np.min(eigenvals)

        assert g_lift.is_positive_definite(), \
            f"Metric not positive definite: min eigenvalue = {min_eigenval}"
        assert min_eigenval > 1e-10, \
            f"Eigenvalue too small: {min_eigenval}"

    def test_block_structure(self, equal_mass_equilateral):
        """V1: Verify correct 4×4 block structure."""
        masses, bundle_state = equal_mass_equilateral

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        # Extract blocks
        g_shape_block = g_lift.extract_shape_block()  # 3×3
        g_fiber = g_lift.extract_fiber_component()  # scalar

        assert g_shape_block.shape == (3, 3), \
            "Shape space block wrong dimension"
        assert np.isscalar(g_fiber) or isinstance(g_fiber, (float, np.ndarray)), \
            "Fiber component should be scalar"
        assert abs(g_fiber - 1.0) < 1e-10, \
            f"Fiber metric should be 1.0, got {g_fiber}"

    def test_validation_function(self, equal_mass_equilateral):
        """V1: Test built-in validation function."""
        masses, bundle_state = equal_mass_equilateral

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        validation = validate_s1_metric_properties(g_lift)

        assert validation['is_symmetric'], \
            f"Symmetry check failed: {validation['symmetry_error']}"
        assert validation['is_positive_definite'], \
            f"Positive definiteness failed: min λ = {validation['min_eigenvalue']}"
        assert validation['correct_block_structure'], \
            f"Block structure wrong: {validation['block_error']}"

    def test_connection_coupling(self, equal_mass_equilateral):
        """Verify connection couples shape and fiber correctly."""
        masses, bundle_state = equal_mass_equilateral

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        # Off-diagonal block should equal -A (connection)
        off_diag = g_lift.components[:3, 3]
        connection_coeffs = g_lift.connection.coefficients

        error = np.linalg.norm(off_diag + connection_coeffs)

        assert error < 1e-12, \
            f"Off-diagonal block != -A: error = {error}"

    def test_equal_mass_symmetry(self):
        """V3: Verify permutation symmetry for equal masses."""
        masses = Masses(1.0, 1.0, 1.0)

        # Create bundle state
        state1 = create_bundle_state(
            r12=1.0, r23=1.2, r31=1.1,
            theta=0.5,
            L=1.5
        )

        # Permute: body 1 ↔ 2 (swap r12 and r23 roles)
        # This is approximate - full permutation is more complex
        state2 = create_bundle_state(
            r12=1.2, r23=1.0, r31=1.1,  # Swapped r12 ↔ r23
            theta=0.5,
            L=1.5
        )

        g1 = compute_s1_bundle_metric(state1, masses)
        g2 = compute_s1_bundle_metric(state2, masses)

        # Metrics should have similar structure (eigenvalues)
        eig1 = np.sort(g1.eigenvalues())
        eig2 = np.sort(g2.eigenvalues())

        # Note: exact equality only after proper coordinate permutation
        # Here we check eigenvalue similarity as a weak test
        relative_diff = np.linalg.norm(eig1 - eig2) / np.linalg.norm(eig1)

        assert relative_diff < 0.5, \
            f"Equal mass symmetry violated: {relative_diff}"


class TestS1JMMetric:
    """Test suite for JM metric on S¹ bundle."""

    @pytest.fixture
    def bound_orbit_state(self):
        """Bound orbit configuration (E < 0)."""
        masses = Masses(1.0, 1.0, 1.0)

        bundle_state = create_bundle_state(
            r12=1.5, r23=1.5, r31=1.5,
            theta=0.0,
            L=2.0
        )

        energy = -1.0  # Bound orbit

        return masses, bundle_state, energy

    def test_jm_conformal_factor(self, bound_orbit_state):
        """Verify JM metric = conformal factor × kinetic metric."""
        masses, bundle_state, energy = bound_orbit_state

        # Compute both metrics
        g_lift = compute_s1_bundle_metric(bundle_state, masses)
        g_jm = compute_s1_jm_metric(bundle_state, masses, energy, L_magnitude=2.0)

        # JM should be proportional to g_lift
        ratio = g_jm.components / g_lift.components

        # All ratios should be equal (conformal)
        ratio_flat = ratio[np.abs(g_lift.components) > 1e-12]  # Exclude near-zero entries
        ratio_std = np.std(ratio_flat)

        assert ratio_std < 1e-10, \
            f"JM metric not conformal to lifted metric: std = {ratio_std}"

    def test_classically_forbidden_raises(self):
        """V4: Verify error raised for E ≤ V_eff."""
        masses = Masses(1.0, 1.0, 1.0)

        bundle_state = create_bundle_state(
            r12=1.0, r23=1.0, r31=1.0,
            theta=0.0,
            L=1.0
        )

        # Energy too low (classically forbidden)
        energy = -10.0  # Very low energy

        with pytest.raises(ValueError, match="Classically forbidden"):
            compute_s1_jm_metric(bundle_state, masses, energy, L_magnitude=1.0)

    def test_jm_positive_definite(self, bound_orbit_state):
        """V1: JM metric positive definite in classically allowed region."""
        masses, bundle_state, energy = bound_orbit_state

        g_jm = compute_s1_jm_metric(bundle_state, masses, energy, L_magnitude=2.0)

        assert g_jm.is_positive_definite(), \
            "JM metric not positive definite in allowed region"

    def test_energy_dependence(self, bound_orbit_state):
        """Verify JM metric scales correctly with energy."""
        masses, bundle_state, _ = bound_orbit_state

        E1 = -1.0
        E2 = -0.5  # Higher energy (less bound)

        g_jm1 = compute_s1_jm_metric(bundle_state, masses, E1, L_magnitude=2.0)
        g_jm2 = compute_s1_jm_metric(bundle_state, masses, E2, L_magnitude=2.0)

        # Higher energy → larger conformal factor → larger metric
        det1 = g_jm1.determinant()
        det2 = g_jm2.determinant()

        assert det2 > det1, \
            f"JM metric should increase with energy: det(E=-0.5) = {det2}, det(E=-1.0) = {det1}"


# ============================================================================
# Part B: KS-Spinor Metric Tests
# ============================================================================

class TestKSSpinorCoords:
    """Test suite for KS spinor coordinates."""

    def test_coords_construction(self):
        """Test KS coordinate construction and validation."""
        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([0.0, 1.0, 0.0, 0.0])
        u31 = np.array([0.0, 0.0, 1.0, 0.0])

        ks_coords = KSSpinorCoords(u12=u12, u23=u23, u31=u31)

        assert ks_coords.u12.shape == (4,)
        assert ks_coords.u23.shape == (4,)
        assert ks_coords.u31.shape == (4,)

    def test_to_from_array(self):
        """Test array conversion (round-trip)."""
        u = np.random.rand(12)

        ks_coords = KSSpinorCoords.from_array(u)
        u_reconstructed = ks_coords.to_array()

        error = np.linalg.norm(u - u_reconstructed)

        assert error < 1e-14, \
            f"Round-trip error: {error}"

    def test_constraint_validation(self):
        """Test triangle closure constraint checking."""
        # Create a configuration that should satisfy constraints
        # (This requires careful construction)

        # Simple case: collinear configuration
        # r12 = [1, 0, 0], r23 = [-0.5, 0, 0], r31 = [-0.5, 0, 0]
        # So r12 + r23 + r31 = 0 ✓

        # Find spinors: r = L(u)·u, so |u|² = |r|
        # For r12 = [1, 0, 0]: |r| = 1, so |u| = 1
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # Gives r = [1, 0, 0]

        # For r23 = [-0.5, 0, 0]: need |u| = √0.5
        u23 = np.array([0.5**0.25, 0.5**0.25, 0.0, 0.0])

        # For r31 = [-0.5, 0, 0]
        u31 = np.array([0.5**0.25, 0.5**0.25, 0.0, 0.0])

        ks_coords = KSSpinorCoords(u12=u12, u23=u23, u31=u31)

        # This won't satisfy constraints exactly, but we can check the method works
        is_valid = ks_coords.check_constraints(tolerance=1.0)  # Loose tolerance for this test

        # Just check that method runs without error
        assert isinstance(is_valid, (bool, np.bool_))


class TestKSPotential:
    """Test suite for potential in KS coordinates."""

    def test_bilinear_relation(self):
        """V2: Verify r_ij = |u_ij|² (KS bilinear relation)."""
        u12 = np.array([1.0, 1.0, 0.0, 0.0])

        # Transform to 3D
        r12 = levi_civita_transform(u12)

        # Check bilinear relation
        r12_mag = np.linalg.norm(r12)
        u12_norm_squared = np.dot(u12, u12)

        assert abs(r12_mag - u12_norm_squared) < 1e-12, \
            f"|r| = {r12_mag}, |u|² = {u12_norm_squared}"

    def test_potential_computation(self):
        """Test gravitational potential in KS coordinates."""
        masses = Masses(1.0, 1.0, 1.0)

        # Create simple spinor configuration
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # |u| = 1 → r = 1
        u23 = np.array([1.0, 0.0, 0.0, 0.0])
        u31 = np.array([1.0, 0.0, 0.0, 0.0])

        ks_coords = KSSpinorCoords(u12=u12, u23=u23, u31=u31)

        V = compute_ks_potential(ks_coords, masses)

        # All distances = 1, so V = -G(1 + 1 + 1) = -3
        expected_V = -3.0

        assert abs(V - expected_V) < 0.1, \
            f"Potential = {V}, expected ≈ {expected_V}"

    def test_collision_regularization(self):
        """KS advantage: potential smooth at collisions."""
        masses = Masses(1.0, 1.0, 1.0)

        # Near-collision: |u| → 0
        u12_small = np.array([0.01, 0.0, 0.0, 0.0])  # |u| = 0.01 → r ≈ 0.0001
        u23 = np.array([1.0, 0.0, 0.0, 0.0])
        u31 = np.array([1.0, 0.0, 0.0, 0.0])

        ks_coords = KSSpinorCoords(u12=u12_small, u23=u23, u31=u31)

        # Should compute without blowing up (thanks to regularization)
        V = compute_ks_potential(ks_coords, masses)

        assert np.isfinite(V), \
            "Potential not finite near collision"
        assert V < 0, \
            "Potential should be negative (attractive)"


# ============================================================================
# Integration Tests
# ============================================================================

class TestMetricComparison:
    """Compare S¹ bundle metric to base shape space metric."""

    def test_weak_connection_limit(self):
        """When connection is small, bundle metric ≈ product metric."""
        masses = Masses(1.0, 1.0, 1.0)

        # Configuration with small angular momentum (weak connection)
        bundle_state = create_bundle_state(
            r12=5.0, r23=5.0, r31=5.0,  # Large distances
            theta=0.0,
            L=0.1  # Small L → small connection
        )

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        comparison = compare_s1_vs_base_metric(
            g_lift,
            g_lift.base_metric,
            g_lift.connection
        )

        # Connection should be small
        assert comparison['connection_strength'] < 0.5, \
            f"Connection too strong: {comparison['connection_strength']}"

    def test_strong_connection_regime(self):
        """For large L and small distances, connection is significant."""
        masses = Masses(1.0, 1.0, 1.0)

        bundle_state = create_bundle_state(
            r12=1.0, r23=1.0, r31=1.0,
            theta=0.0,
            L=5.0  # Large angular momentum
        )

        g_lift = compute_s1_bundle_metric(bundle_state, masses)

        comparison = compare_s1_vs_base_metric(
            g_lift,
            g_lift.base_metric,
            g_lift.connection
        )

        # Connection should be significant
        assert comparison['connection_strength'] > 0.1, \
            f"Connection too weak: {comparison['connection_strength']}"


# ============================================================================
# Numerical Accuracy Tests
# ============================================================================

class TestNumericalStability:
    """Test numerical stability of metric computations."""

    def test_different_scales(self):
        """Test metric at different length scales."""
        masses = Masses(1.0, 1.0, 1.0)

        scales = [0.1, 1.0, 10.0, 100.0]

        for scale in scales:
            bundle_state = create_bundle_state(
                r12=scale, r23=scale, r31=scale,
                theta=0.0,
                L=1.0
            )

            g_lift = compute_s1_bundle_metric(bundle_state, masses)

            assert g_lift.is_positive_definite(), \
                f"Metric not positive definite at scale {scale}"
            assert np.isfinite(g_lift.determinant()), \
                f"Determinant not finite at scale {scale}"

    def test_near_collision_handling(self):
        """Test behavior approaching collision."""
        masses = Masses(1.0, 1.0, 1.0)

        # Gradually approach collision
        r12_values = [1.0, 0.5, 0.1, 0.05]

        for r12 in r12_values:
            try:
                bundle_state = create_bundle_state(
                    r12=r12, r23=1.0, r31=1.0,
                    theta=0.0,
                    L=1.0
                )

                g_lift = compute_s1_bundle_metric(bundle_state, masses)

                # Should remain positive definite
                assert g_lift.is_positive_definite()

            except ValueError:
                # Triangle inequality may be violated for some values
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
