"""
Unit tests for interpretability.py (AMENDED WP3.3).

Tests function type classification and interpretability scoring.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import sympy as sp
import pytest
from symbolic.interpretability import (
    FunctionType,
    InterpretabilityScore,
    classify_function_type,
    compute_interpretability_score,
    detect_physical_symmetries,
    generate_physical_hints
)


class TestFunctionTypeClassification:
    """Test function type classification."""

    def test_polynomial_classification(self):
        """Test classification of polynomial expressions."""
        # Simple polynomial
        expr = sp.sympify("x**2 + y**2 + z**2")
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.POLYNOMIAL

        # Higher degree polynomial
        expr = sp.sympify("x**3 + 2*x*y + y**2")
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.POLYNOMIAL

    def test_rational_classification(self):
        """Test classification of rational functions."""
        # Simple rational function
        expr = sp.sympify("(x**2 + 1) / (y**2 + 1)")
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.RATIONAL

        # More complex rational
        expr = sp.sympify("x / (x**2 + y**2)")
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.RATIONAL

    def test_radical_classification(self):
        """Test classification of radical expressions."""
        # Square root
        expr = sp.sqrt(sp.Symbol('x')**2 + sp.Symbol('y')**2)
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.RADICAL

        # Cube root
        x = sp.Symbol('x')
        expr = x**(sp.Rational(1, 3))
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.RADICAL

    def test_trigonometric_classification(self):
        """Test classification of trigonometric functions."""
        x = sp.Symbol('x')

        # Sin
        expr = sp.sin(x)
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.TRIGONOMETRIC

        # Cos
        expr = sp.cos(x) + sp.sin(x)
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.TRIGONOMETRIC

    def test_exponential_classification(self):
        """Test classification of exponential functions."""
        x = sp.Symbol('x')

        # Exponential
        expr = sp.exp(x)
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.EXPONENTIAL

        # Logarithm
        expr = sp.log(x)
        func_type = classify_function_type(expr)
        assert func_type == FunctionType.EXPONENTIAL

    def test_spinor_classification(self):
        """Test classification of spinor expressions."""
        # Spinor coordinates
        u0, u1, u2, u3 = sp.symbols('u0_1 u1_1 u2_1 u3_1')
        expr = u0**2 + u1**2 + u2**2 + u3**2

        func_type = classify_function_type(expr)
        assert func_type == FunctionType.SPINOR

    def test_elliptic_classification(self):
        """Test classification of elliptic functions."""
        u, k = sp.symbols('u k')

        # Mock Jacobi function (as SymPy Function)
        jacobi_sn = sp.Function('jacobi_sn')
        expr = jacobi_sn(u, k)

        func_type = classify_function_type(expr)
        assert func_type == FunctionType.ELLIPTIC

    def test_theta_classification(self):
        """Test classification of theta functions."""
        z, tau = sp.symbols('z tau')

        # Mock theta function
        theta1 = sp.Function('jacobi_theta1')
        expr = theta1(z, tau)

        func_type = classify_function_type(expr)
        assert func_type == FunctionType.THETA

    def test_mixed_classification(self):
        """Test classification of mixed/complex expressions."""
        x, y = sp.symbols('x y')

        # Mix of types
        expr = sp.sin(x) * sp.exp(y) + sp.sqrt(x**2 + y**2)
        func_type = classify_function_type(expr)
        # Should classify as the highest priority type found
        # In this case, exponential should take precedence
        assert func_type in [FunctionType.EXPONENTIAL, FunctionType.MIXED]


class TestInterpretabilityScoring:
    """Test interpretability scoring."""

    def test_polynomial_interpretability(self):
        """Test interpretability of polynomial."""
        expr = sp.sympify("x**2 + y**2")
        score = compute_interpretability_score(expr)

        assert score.function_type == FunctionType.POLYNOMIAL
        assert score.interpretability > 0.8, "Polynomials should be highly interpretable"
        assert score.validation_difficulty < 0.3, "Polynomials should be easy to validate"
        assert not score.contains_special_functions
        assert score.max_polynomial_degree == 2

    def test_elliptic_interpretability(self):
        """Test interpretability of elliptic function."""
        u, k = sp.symbols('u k')
        jacobi_sn = sp.Function('jacobi_sn')
        expr = jacobi_sn(u, k)

        score = compute_interpretability_score(expr)

        assert score.function_type == FunctionType.ELLIPTIC
        assert score.interpretability < 0.7, "Elliptic functions less interpretable"
        assert score.validation_difficulty > 0.7, "Elliptic functions harder to validate"
        assert score.contains_special_functions
        assert "CRITICAL" in score.physical_meaning or any("CRITICAL" in hint for hint in score.physical_hints)

    def test_theta_interpretability(self):
        """Test interpretability of theta function."""
        z, tau = sp.symbols('z tau')
        theta = sp.Function('jacobi_theta1')
        expr = theta(z, tau)

        score = compute_interpretability_score(expr)

        assert score.function_type == FunctionType.THETA
        assert score.validation_difficulty > 0.85, "Theta functions hardest to validate"
        assert "EXCEPTIONAL" in score.physical_meaning or any("EXCEPTIONAL" in hint for hint in score.physical_hints)

    def test_spinor_interpretability(self):
        """Test interpretability of spinor expression."""
        u0, u1, u2, u3 = sp.symbols('u0_1 u1_1 u2_1 u3_1')
        expr = u0**2 + u1**2

        score = compute_interpretability_score(expr)

        assert score.function_type == FunctionType.SPINOR
        assert 0.4 < score.interpretability < 0.8
        assert 0.5 < score.validation_difficulty < 0.7


class TestPhysicalSymmetryDetection:
    """Test physical symmetry detection."""

    def test_spherical_symmetry(self):
        """Test detection of spherical symmetry."""
        x, y, z = sp.symbols('x y z')
        expr = x**2 + y**2 + z**2

        has_sym, hints = detect_physical_symmetries(expr)

        assert has_sym, "Should detect spherical symmetry"
        assert any("Spherically symmetric" in h for h in hints), f"Hints: {hints}"

    def test_cylindrical_symmetry(self):
        """Test detection of cylindrical symmetry."""
        x, y = sp.symbols('x y')
        expr = x**2 + y**2

        has_sym, hints = detect_physical_symmetries(expr)

        assert has_sym, "Should detect cylindrical symmetry"
        assert any("Cylindrically symmetric" in h for h in hints), f"Hints: {hints}"

    def test_angular_momentum(self):
        """Test detection of angular momentum."""
        x, y, p_x, p_y = sp.symbols('x y p_x p_y')
        expr = x * p_y - y * p_x  # L_z

        has_sym, hints = detect_physical_symmetries(expr)

        assert has_sym, "Should detect angular momentum"
        assert any("Angular momentum" in h for h in hints), f"Hints: {hints}"

    def test_kinetic_energy(self):
        """Test detection of kinetic energy term."""
        p_x, p_y, p_z = sp.symbols('p_x p_y p_z')
        expr = p_x**2 + p_y**2 + p_z**2

        has_sym, hints = detect_physical_symmetries(expr)

        assert has_sym, "Should detect kinetic energy"
        assert any("kinetic energy" in h.lower() for h in hints), f"Hints: {hints}"

    def test_no_symmetry(self):
        """Test with expression having no obvious symmetry."""
        a, b = sp.symbols('a b')
        expr = a + b

        has_sym, hints = detect_physical_symmetries(expr)

        # May or may not detect symmetry depending on implementation
        # Just check it doesn't crash
        assert isinstance(has_sym, bool)
        assert isinstance(hints, list)


class TestPhysicalHints:
    """Test physical interpretation hint generation."""

    def test_polynomial_hints(self):
        """Test hints for polynomial."""
        expr = sp.sympify("x**2 + y**2")
        hints = generate_physical_hints(expr, FunctionType.POLYNOMIAL)

        assert len(hints) > 0
        assert any("Polynomial" in h for h in hints)
        assert any("algebraic" in h.lower() for h in hints)

    def test_elliptic_hints(self):
        """Test hints for elliptic function."""
        u, k = sp.symbols('u k')
        hints = generate_physical_hints(
            sp.Function('jacobi_sn')(u, k),
            FunctionType.ELLIPTIC
        )

        assert len(hints) > 0
        assert any("Elliptic" in h for h in hints)
        assert any("integrable" in h.lower() for h in hints)
        assert any("CRITICAL" in h for h in hints)

    def test_theta_hints(self):
        """Test hints for theta function."""
        z, tau = sp.symbols('z tau')
        hints = generate_physical_hints(
            sp.Function('theta1')(z, tau),
            FunctionType.THETA
        )

        assert len(hints) > 0
        assert any("Theta" in h for h in hints)
        assert any("EXCEPTIONAL" in h for h in hints)

    def test_spinor_hints(self):
        """Test hints for spinor expression."""
        u0, u1 = sp.symbols('u0_1 u1_1')
        hints = generate_physical_hints(u0**2 + u1**2, FunctionType.SPINOR)

        assert len(hints) > 0
        assert any("Spinor" in h or "spinor" in h for h in hints)
        assert any("regularization" in h.lower() or "KS" in h for h in hints)


class TestIntegrationWithRanking:
    """Test integration with candidate ranking."""

    def test_score_comparison(self):
        """Test that interpretability can be used for ranking."""
        # Create different types of expressions
        x, y = sp.symbols('x y')

        expr_poly = x**2 + y**2
        expr_trig = sp.sin(x) + sp.cos(y)
        expr_elliptic = sp.Function('jacobi_sn')(x, y)

        # Compute scores
        score_poly = compute_interpretability_score(expr_poly)
        score_trig = compute_interpretability_score(expr_trig)
        score_elliptic = compute_interpretability_score(expr_elliptic)

        # Polynomial should be most interpretable
        assert score_poly.interpretability > score_trig.interpretability
        assert score_poly.interpretability > score_elliptic.interpretability

        # Polynomial should be easiest to validate
        assert score_poly.validation_difficulty < score_trig.validation_difficulty
        assert score_poly.validation_difficulty < score_elliptic.validation_difficulty

    def test_full_scoring_workflow(self):
        """Test complete scoring workflow for a candidate."""
        # Create test expression
        p_x, p_y, x, y = sp.symbols('p_x p_y x y')
        expr = p_x**2 + p_y**2 + x**2 + y**2  # Energy-like

        # Compute interpretability
        score = compute_interpretability_score(expr)

        # Verify all fields are populated
        assert score.function_type is not None
        assert 0.0 <= score.interpretability <= 1.0
        assert 0.0 <= score.validation_difficulty <= 1.0
        assert isinstance(score.physical_meaning, str)
        assert isinstance(score.contains_radicals, bool)
        assert isinstance(score.contains_transcendentals, bool)
        assert isinstance(score.contains_special_functions, bool)
        assert isinstance(score.max_polynomial_degree, int)
        assert isinstance(score.has_physical_symmetry, bool)
        assert isinstance(score.physical_hints, list)

        # Check physical interpretation
        assert "energy" in score.physical_meaning.lower() or \
               any("kinetic" in h.lower() for h in score.physical_hints)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
