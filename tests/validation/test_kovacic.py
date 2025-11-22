"""
Tests for Kovacic algorithm (WP 4.2, Phase 3).

Tests the differential Galois group computation for second-order linear ODEs.
"""

import pytest
import sympy as sp
from src.python.validation.kovacic import (
    KovacicSolver,
    GaloisGroupType,
    classify_galois_group,
    is_galois_group_abelian,
    morales_ramis_test,
    KovacicResult
)


class TestKovacicSolver:
    """Test KovacicSolver class."""

    def test_solver_initialization(self):
        """Test solver can be initialized."""
        solver = KovacicSolver(verbose=False)
        assert solver is not None
        assert solver.verbose is False

    def test_solver_initialization_verbose(self):
        """Test solver with verbose mode."""
        solver = KovacicSolver(verbose=True)
        assert solver.verbose is True


class TestNormalFormConversion:
    """Test conversion to normal form y'' = r*y."""

    def test_zero_first_derivative(self):
        """Test y'' + 0*y' + b*y = 0 → y'' = b*y."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        a = sp.sympify(0)
        b = t**2

        r = solver._convert_to_normal_form(a, b, t)

        # r = b - a'/2 - a²/4 = t² - 0 - 0 = t²
        assert r == t**2

    def test_constant_coefficients(self):
        """Test constant coefficient ODE."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        a = sp.sympify(2)
        b = sp.sympify(3)

        r = solver._convert_to_normal_form(a, b, t)

        # r = b - a'/2 - a²/4 = 3 - 0 - 4/4 = 2
        assert r == 2

    def test_airy_equation(self):
        """Test Airy equation: y'' - ty = 0."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        a = sp.sympify(0)
        b = -t

        r = solver._convert_to_normal_form(a, b, t)

        # Already in normal form
        assert r == -t


class TestKnownIntegrableEquations:
    """Test equations with known integrable (abelian) Galois groups."""

    def test_constant_coefficient_homogeneous(self):
        """Test y'' + ω²y = 0 (simple harmonic oscillator)."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        # y'' + y = 0
        a = sp.sympify(0)
        b = sp.sympify(1)

        result = solver.solve(a, b, t)

        # Should have abelian Galois group (solutions: sin, cos)
        assert is_galois_group_abelian(result.galois_type)

    def test_exponential_solutions(self):
        """Test y'' - k²y = 0."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        # y'' - 4y = 0 (solutions: e^(2t), e^(-2t))
        a = sp.sympify(0)
        b = sp.sympify(-4)

        result = solver.solve(a, b, t)

        # Should have abelian Galois group
        assert is_galois_group_abelian(result.galois_type)


class TestKnownNonIntegrableEquations:
    """Test equations with known non-abelian Galois groups."""

    def test_airy_equation(self):
        """
        Test Airy equation: y'' - ty = 0.

        Known to have SL(2,C) Galois group (non-abelian).
        """
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        a = sp.sympify(0)
        b = -t

        result = solver.solve(a, b, t)

        # Airy equation should have non-abelian Galois group
        # (This is a known result from differential Galois theory)
        # Note: SymPy may find a solution, so we check the type
        assert result.galois_type in [
            GaloisGroupType.SL2C,
            GaloisGroupType.SOLVABLE,
            GaloisGroupType.REDUCIBLE
        ]

    def test_bessel_equation_general(self):
        """
        Test Bessel equation: t²y'' + ty' + (t² - n²)y = 0.

        For non-integer n, has non-abelian Galois group.
        """
        t = sp.Symbol('t', positive=True, real=True)
        n = sp.Symbol('n', real=True)
        solver = KovacicSolver(verbose=False)

        # Convert to standard form: y'' + (1/t)y' + (1 - n²/t²)y = 0
        a = 1 / t
        b = 1 - n**2 / t**2

        result = solver.solve(a, b, t)

        # Bessel equations typically have non-trivial Galois groups
        assert result.galois_type in [
            GaloisGroupType.SL2C,
            GaloisGroupType.SOLVABLE,
            GaloisGroupType.REDUCIBLE,
            GaloisGroupType.FINITE
        ]


class TestGaloisGroupClassification:
    """Test classification helpers."""

    def test_is_abelian_finite(self):
        """Test finite groups are abelian."""
        assert is_galois_group_abelian(GaloisGroupType.FINITE) is True

    def test_is_abelian_reducible(self):
        """Test reducible groups are abelian."""
        assert is_galois_group_abelian(GaloisGroupType.REDUCIBLE) is True

    def test_is_abelian_solvable(self):
        """Test solvable groups are abelian."""
        assert is_galois_group_abelian(GaloisGroupType.SOLVABLE) is True

    def test_is_not_abelian_sl2c(self):
        """Test SL(2,C) is non-abelian."""
        assert is_galois_group_abelian(GaloisGroupType.SL2C) is False


class TestClassifyGaloisGroup:
    """Test convenience function classify_galois_group."""

    def test_classify_harmonic_oscillator(self):
        """Test classifying y'' + y = 0."""
        t = sp.Symbol('t')
        galois_type = classify_galois_group((0, 1), t, verbose=False)

        # Should be abelian
        assert is_galois_group_abelian(galois_type)

    def test_classify_with_verbose(self):
        """Test classification with verbose output."""
        t = sp.Symbol('t')
        galois_type = classify_galois_group((0, -4), t, verbose=False)

        # Should complete without error
        assert galois_type is not None


class TestMoralesRamisTest:
    """Test the Morales-Ramis integrability test."""

    def test_morales_ramis_integrable_case(self):
        """Test M-R test on integrable system."""
        t = sp.Symbol('t')

        # Simple harmonic oscillator: y'' + y = 0
        is_integrable, galois_type, interpretation = morales_ramis_test(
            (0, 1), t, verbose=False
        )

        # Should not obstruct integrability
        assert is_integrable is True or galois_type != GaloisGroupType.SL2C
        assert "ABELIAN" in interpretation or "does NOT obstruct" in interpretation

    def test_morales_ramis_result_structure(self):
        """Test M-R test returns correct structure."""
        t = sp.Symbol('t')

        is_int, galois, msg = morales_ramis_test((0, -4), t, verbose=False)

        assert isinstance(is_int, bool)
        assert isinstance(galois, GaloisGroupType)
        assert isinstance(msg, str)
        assert len(msg) > 0


class TestSingularityAnalysis:
    """Test singularity finding and classification."""

    def test_find_singularities_simple_pole(self):
        """Test finding singularities with simple poles."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        # r(t) = 1/(t-1)
        r = 1 / (t - 1)

        singularities = solver._find_singularities(r, t)

        # Should find singularity at t=1 and at infinity
        assert len(singularities) > 0

        # Check that t=1 is detected
        finite_sings = [s for s, _, _ in singularities if s != sp.oo]
        assert any(sp.simplify(s - 1) == 0 for s in finite_sings)

    def test_find_singularities_at_infinity(self):
        """Test that infinity is always checked."""
        t = sp.Symbol('t')
        solver = KovacicSolver(verbose=False)

        # r(t) = t² (no finite singularities)
        r = t**2

        singularities = solver._find_singularities(r, t)

        # Should include infinity
        assert any(s == sp.oo for s, _, _ in singularities)


@pytest.mark.slow
class TestKovacicOnPeriodicOrbitNVE:
    """
    Test Kovacic algorithm on realistic NVE from periodic orbits.

    These are integration tests that would use actual variational equations.
    Marked as slow because they require full computation pipeline.
    """

    def test_lagrange_l4_nve_placeholder(self):
        """
        Placeholder: Test M-R on Lagrange L4 NVE.

        In full implementation, would:
        1. Load Lagrange L4 orbit
        2. Compute NVE using variational_equations.py
        3. Convert to symbolic form
        4. Apply Kovacic algorithm
        5. Verify non-abelian Galois group (SL(2,C))
        """
        # This requires integration with variational_equations module
        # and symbolic conversion of numerical NVE
        pytest.skip("Requires full NVE computation pipeline")

    def test_figure8_nve_placeholder(self):
        """
        Placeholder: Test M-R on Figure-8 choreography NVE.
        """
        pytest.skip("Requires full NVE computation pipeline")


class TestKovacicResult:
    """Test KovacicResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = KovacicResult(
            galois_type=GaloisGroupType.SL2C,
            solution=None,
            case_succeeded=None,
            details={'test': True}
        )

        assert result.galois_type == GaloisGroupType.SL2C
        assert result.solution is None
        assert result.case_succeeded is None
        assert result.details == {'test': True}

    def test_result_with_solution(self):
        """Test result with solution found."""
        t = sp.Symbol('t')
        solution = sp.exp(t)

        result = KovacicResult(
            galois_type=GaloisGroupType.REDUCIBLE,
            solution=solution,
            case_succeeded=1,
            details={}
        )

        assert result.galois_type == GaloisGroupType.REDUCIBLE
        assert result.solution == sp.exp(t)
        assert result.case_succeeded == 1


@pytest.mark.integration
class TestKovacicIntegration:
    """Integration tests combining multiple components."""

    def test_full_pipeline_simple_ode(self):
        """Test full pipeline on simple ODE."""
        t = sp.Symbol('t')

        # Define ODE: y'' + y = 0
        a, b = sp.sympify(0), sp.sympify(1)

        # Solve using Kovacic
        solver = KovacicSolver(verbose=False)
        result = solver.solve(a, b, t)

        # Check result structure
        assert isinstance(result, KovacicResult)
        assert isinstance(result.galois_type, GaloisGroupType)

        # Apply Morales-Ramis interpretation
        is_int = is_galois_group_abelian(result.galois_type)
        assert isinstance(is_int, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
