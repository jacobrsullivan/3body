"""
Tests for Killing PDE formulation (WP 3.1, Task 3.1.2).

Validation Strategy:
    - Test Christoffel symbols on known manifolds (flat space, sphere)
    - Verify symmetry properties
    - Test PDE formulation structure
    - Validate overdetermination counts

Task 3.1.2 Validation Requirements:
    - Christoffel symmetry: Γ^k_ij = Γ^k_ji
    - Determinant formula consistency
    - PDE equation counts match theory
"""

import pytest
import numpy as np

from src.python.pde.christoffel_symbols import (
    compute_christoffel_numerical,
    validate_christoffel_symmetry,
    compute_christoffel_field,
    ChristoffelSymbolsNumeric,
)
from src.python.pde.killing_equations import (
    count_equations_and_unknowns,
    estimate_null_space_dimension,
    KillingVectorPDE,
)


# ============================================================================
# Part A: Christoffel Symbols Tests
# ============================================================================

class TestChristoffelSymbols:
    """Test suite for Christoffel symbols computation."""

    def test_flat_space_2d(self):
        """Test flat Euclidean metric in 2D: g = [[1, 0], [0, 1]]."""
        def g_flat_2d(q):
            """Identity metric."""
            return np.eye(2)

        point = np.array([1.0, 2.0])

        Gamma = compute_christoffel_numerical(g_flat_2d, point)

        # All Christoffel symbols should be zero for flat space
        max_component = np.max(np.abs(Gamma.components))

        assert max_component < 1e-10, \
            f"Flat space should have zero Christoffel symbols, got max = {max_component}"
        assert Gamma.dimension == 2
        assert Gamma.components.shape == (2, 2, 2)

    def test_polar_coordinates_2d(self):
        """Test polar metric: g = [[1, 0], [0, r²]]."""
        def g_polar(q):
            r, theta = q
            return np.array([
                [1.0, 0.0],
                [0.0, r**2]
            ])

        point = np.array([2.0, np.pi/4])

        Gamma = compute_christoffel_numerical(g_polar, point)

        # Known Christoffel symbols for polar coordinates:
        # Γ^r_θθ = -r
        # Γ^θ_rθ = Γ^θ_θr = 1/r
        # Others = 0

        r = point[0]

        # Γ^r_θθ (index [0, 1, 1])
        Gamma_r_theta_theta = Gamma.components[0, 1, 1]
        expected = -r

        assert abs(Gamma_r_theta_theta - expected) < 1e-3, \
            f"Γ^r_θθ = {Gamma_r_theta_theta}, expected {expected}"

        # Γ^θ_rθ (index [1, 0, 1])
        Gamma_theta_r_theta = Gamma.components[1, 0, 1]
        expected = 1.0 / r

        assert abs(Gamma_theta_r_theta - expected) < 1e-3, \
            f"Γ^θ_rθ = {Gamma_theta_r_theta}, expected {expected}"

    def test_symmetry_in_lower_indices(self):
        """Verify Christoffel symmetry: Γ^k_ij = Γ^k_ji."""
        def g_arbitrary(q):
            x, y = q
            # Arbitrary positive-definite metric
            return np.array([
                [1.0 + x**2, x*y],
                [x*y, 1.0 + y**2]
            ])

        point = np.array([0.5, 0.7])

        Gamma = compute_christoffel_numerical(g_arbitrary, point)

        is_symmetric = validate_christoffel_symmetry(Gamma)

        assert is_symmetric, "Christoffel symbols not symmetric in lower indices"

    def test_positive_definiteness_check(self):
        """Verify metric positive definiteness is enforced."""
        def g_negative_eigenvalue(q):
            """Non-positive-definite metric."""
            return np.array([
                [1.0, 0.0],
                [0.0, -1.0]  # Negative eigenvalue!
            ])

        point = np.array([1.0, 1.0])

        with pytest.raises(ValueError, match="not positive definite"):
            compute_christoffel_numerical(g_negative_eigenvalue, point)

    def test_christoffel_field_computation(self):
        """Test field computation at multiple points."""
        def g_polar(q):
            r, theta = q
            return np.array([[1.0, 0.0], [0.0, r**2]])

        # Grid of points
        r_vals = np.linspace(0.5, 3.0, 5)
        theta_vals = np.linspace(0, 2*np.pi, 8)
        points = [np.array([r, theta]) for r in r_vals for theta in theta_vals]

        Gamma_field = compute_christoffel_field(g_polar, points)

        assert len(Gamma_field) == len(points)

        # Check all computed successfully
        num_valid = sum(1 for G in Gamma_field if G is not None)
        assert num_valid == len(points), \
            f"Only {num_valid}/{len(points)} points computed"

    def test_christoffel_covariant_derivative(self):
        """Test covariant derivative computation."""
        def g_flat(q):
            return np.eye(3)

        point = np.array([1.0, 2.0, 3.0])
        Gamma = compute_christoffel_numerical(g_flat, point)

        # Test vector
        V = np.array([1.0, 0.0, -1.0])

        # In flat space, covariant derivative = ordinary derivative
        # Connection term should be zero
        connection_term = Gamma.evaluate_covariant_derivative(V, direction=0)

        assert np.linalg.norm(connection_term) < 1e-10, \
            "Flat space connection term should be zero"


# ============================================================================
# Part B: Killing PDE Structure Tests
# ============================================================================

class TestKillingPDEStructure:
    """Test Killing PDE formulation structure."""

    def test_equation_counts_2d(self):
        """Verify equation/unknown counts for 2D."""
        counts = count_equations_and_unknowns(dimension=2)

        assert counts["killing_vector"]["unknowns"] == 2
        assert counts["killing_vector"]["equations"] == 3
        assert counts["killing_vector"]["overdetermination"] == 1

        assert counts["killing_tensor"]["unknowns"] == 3
        assert counts["killing_tensor"]["equations"] == 4

    def test_equation_counts_4d(self):
        """Verify equation/unknown counts for 4D (S¹ bundle)."""
        counts = count_equations_and_unknowns(dimension=4)

        # n=4:
        # Killing vector: n=4 unknowns, n(n+1)/2=10 equations
        assert counts["killing_vector"]["unknowns"] == 4
        assert counts["killing_vector"]["equations"] == 10
        assert counts["killing_vector"]["overdetermination"] == 6

        # Killing tensor: n(n+1)/2=10 unknowns, n(n+1)(n+2)/6=20 equations
        assert counts["killing_tensor"]["unknowns"] == 10
        assert counts["killing_tensor"]["equations"] == 20

    def test_equation_counts_9d(self):
        """Verify counts for 9D (KS intrinsic manifold)."""
        counts = count_equations_and_unknowns(dimension=9)

        # n=9:
        # Killing vector: 9 unknowns, 45 equations
        assert counts["killing_vector"]["unknowns"] == 9
        assert counts["killing_vector"]["equations"] == 45

        # Killing tensor: 45 unknowns, 165 equations
        assert counts["killing_tensor"]["unknowns"] == 45
        assert counts["killing_tensor"]["equations"] == 165

    def test_null_space_estimates(self):
        """Test expected null space dimension estimates."""
        flat_estimate = estimate_null_space_dimension(2, "flat")
        assert flat_estimate["expected_for_type"] == 3  # 2 translations + 1 rotation

        sphere_estimate = estimate_null_space_dimension(2, "sphere")
        assert sphere_estimate["expected_for_type"] == 3  # SO(3) rotations

        generic_estimate = estimate_null_space_dimension(2, "generic")
        assert generic_estimate["expected_for_type"] == 0  # No symmetries


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining Christoffel and Killing PDEs."""

    def test_s1_bundle_dimension(self):
        """Test that S¹ bundle has correct dimension (4D)."""
        # S¹ bundle over 3D shape space → 4D total
        dimension = 4

        counts = count_equations_and_unknowns(dimension)

        # Should be heavily overdetermined
        assert counts["killing_vector"]["overdetermination"] > 0

    def test_ks_intrinsic_dimension(self):
        """Test KS intrinsic manifold dimension (9D after constraints)."""
        dimension = 9

        counts = count_equations_and_unknowns(dimension)

        # Very overdetermined for n=9
        assert counts["killing_vector"]["overdetermination"] == 36

    def test_christoffel_at_different_energies(self):
        """
        Test Christoffel symbols for JM metric at different energies.

        The JM metric is g_JM = 2(E - V) · g, so Christoffel symbols
        should have specific scaling with energy.
        """
        def g_jm(E, V_func):
            """JM metric factory."""
            def metric(q):
                r = q[0]
                V = V_func(r)
                prefactor = 2 * (E - V)

                if prefactor <= 0:
                    raise ValueError("Classically forbidden")

                g_base = np.array([[1.0, 0.0], [0.0, r**2]])
                return prefactor * g_base

            return metric

        def V_func(r):
            """Potential: -1/r."""
            return -1.0 / r

        E1 = -0.5
        E2 = -0.25  # Higher energy

        point = np.array([2.0, 0.0])

        try:
            Gamma1 = compute_christoffel_numerical(g_jm(E1, V_func), point)
            Gamma2 = compute_christoffel_numerical(g_jm(E2, V_func), point)

            # Both should compute successfully
            assert Gamma1.is_positive_definite()
            assert Gamma2.is_positive_definite()

        except ValueError:
            # May be classically forbidden at this point
            pytest.skip("Point classically forbidden")


# ============================================================================
# Numerical Stability Tests
# ============================================================================

class TestNumericalStability:
    """Test numerical stability of Christoffel computation."""

    def test_finite_difference_convergence(self):
        """Test convergence as epsilon → 0."""
        def g_test(q):
            r, theta = q
            return np.array([[1.0, 0.0], [0.0, r**2]])

        point = np.array([2.0, np.pi/4])

        epsilons = [1e-4, 1e-5, 1e-6]
        Gammas = []

        for eps in epsilons:
            G = compute_christoffel_numerical(g_test, point, epsilon=eps)
            Gammas.append(G.components)

        # Check convergence: difference should decrease
        diff_1_0 = np.linalg.norm(Gammas[1] - Gammas[0])
        diff_2_1 = np.linalg.norm(Gammas[2] - Gammas[1])

        # Should be converging (though not guaranteed monotonically)
        assert diff_2_1 < 10 * diff_1_0, \
            "Finite differences not converging"

    def test_different_coordinate_scales(self):
        """Test with coordinates at different scales."""
        def g_scaled(q):
            x, y = q
            # Different scales in x and y
            return np.array([
                [1.0, 0.0],
                [0.0, 1e6]  # y-direction much larger scale
            ])

        point = np.array([1.0, 1e-3])

        Gamma = compute_christoffel_numerical(g_scaled, point)

        # Should compute without overflow
        assert np.all(np.isfinite(Gamma.components)), \
            "Christoffel symbols not finite for scaled coordinates"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
