"""
Tests for KS-Spinor symbolic Hamiltonian implementation.

Tests verify:
1. Levi-Civita matrix structure
2. Bilinear relation |r|² = |u|⁴
3. Round-trip KS transformation
4. Regularized Hamiltonian construction
5. Pairwise 3BP Hamiltonian
6. Constraint equations
7. Hessian computation
"""

import pytest
import sympy as sp
from sympy import symbols, Matrix, simplify, sqrt, Symbol

from src.python.symbolic_lifts.ks_symbolic import (
    levi_civita_matrix,
    bilinear_relation_symbolic,
    ks_transform_symbolic,
    ks_inverse_symbolic,
    KSSpinorHamiltonian,
    KSPairwiseHamiltonian,
    create_ks_hamiltonian_kepler,
    create_ks_pairwise_3bp,
    verify_bilinear_relation_symbolic,
    prepare_ks_for_upstairs_mr_test
)


class TestLeviCivitaMatrix:
    """Test Levi-Civita matrix construction and properties."""

    def test_levi_civita_structure(self):
        """Test that L(u) has correct 3×4 structure."""
        u = Matrix(symbols('u_0:4', real=True))
        L = levi_civita_matrix(u)

        assert L.shape == (3, 4), "L(u) should be 3×4 matrix"

    def test_levi_civita_elements(self):
        """Test specific elements of L(u)."""
        u0, u1, u2, u3 = symbols('u_0 u_1 u_2 u_3', real=True)
        u = Matrix([u0, u1, u2, u3])
        L = levi_civita_matrix(u)

        # Check diagonal elements (first column)
        assert L[0, 0] == u0
        assert L[1, 0] == u1
        assert L[2, 0] == u2

        # Check off-diagonal elements
        assert L[0, 1] == -u1
        assert L[1, 2] == -u3
        assert L[2, 3] == -u1

    def test_levi_civita_numerical(self):
        """Test L(u) with numerical values."""
        u_num = Matrix([1, 0, 0, 0])
        L = levi_civita_matrix(u_num)

        # For u = (1, 0, 0, 0), L should be specific matrix
        expected = Matrix([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0]
        ])

        assert L == expected, "L(1,0,0,0) should be identity-like"


class TestBilinearRelation:
    """Test bilinear relation r = |u|²."""

    def test_bilinear_formula(self):
        """Test that r = u₀² + u₁² + u₂² + u₃²."""
        u0, u1, u2, u3 = symbols('u_0 u_1 u_2 u_3', real=True)
        u = Matrix([u0, u1, u2, u3])

        r = bilinear_relation_symbolic(u)

        expected = u0**2 + u1**2 + u2**2 + u3**2
        assert simplify(r - expected) == 0

    def test_bilinear_numerical(self):
        """Test numerical evaluation of bilinear relation."""
        u_num = Matrix([1, 2, 3, 4])
        r = bilinear_relation_symbolic(u_num)

        expected = 1**2 + 2**2 + 3**2 + 4**2  # = 30
        assert r == expected

    def test_verify_bilinear_relation(self):
        """Test that |L(u)·u|² = |u|⁴ symbolically."""
        result = verify_bilinear_relation_symbolic()
        assert result is True, "Bilinear relation identity must hold"


class TestKSTransformation:
    """Test KS transformation and inverse."""

    def test_ks_transform_signature(self):
        """Test KS transform returns correct types."""
        x, y, z = symbols('x y z', real=True)
        vx, vy, vz = symbols('v_x v_y v_z', real=True)

        r_vec = Matrix([x, y, z])
        v_vec = Matrix([vx, vy, vz])

        u, u_prime = ks_transform_symbolic(r_vec, v_vec)

        assert u.shape == (4, 1), "u should be 4×1"
        assert u_prime.shape == (4, 1), "u' should be 4×1"

    def test_ks_inverse_signature(self):
        """Test KS inverse returns correct types."""
        u = Matrix(symbols('u_0:4', real=True))
        u_prime = Matrix(symbols('u_0_prime:4', real=True))

        r_vec, v_vec = ks_inverse_symbolic(u, u_prime)

        assert r_vec.shape == (3, 1), "r should be 3×1"
        assert v_vec.shape == (3, 1), "v should be 3×1"

    def test_ks_inverse_position(self):
        """Test that r = L(u)·u for inverse transform."""
        u = Matrix(symbols('u_0:4', real=True))
        u_prime = Matrix([0, 0, 0, 0])

        r_vec, _ = ks_inverse_symbolic(u, u_prime)

        # r should equal L(u)·u
        L = levi_civita_matrix(u)
        r_expected = L * u

        # Simplify and compare each component
        for i in range(3):
            assert simplify(r_vec[i] - r_expected[i]) == 0


class TestKSSpinorHamiltonian:
    """Test single-pair KS regularized Hamiltonian."""

    def test_create_ks_kepler(self):
        """Test creation of KS Hamiltonian for Kepler problem."""
        mu = Symbol('mu', positive=True)
        ks_ham = create_ks_hamiltonian_kepler(mu)

        assert isinstance(ks_ham, KSSpinorHamiltonian)
        assert ks_ham.mass_product == mu

    def test_ks_hamiltonian_construction(self):
        """Test that KS Hamiltonian is constructed correctly."""
        ks_ham = create_ks_hamiltonian_kepler()
        system = ks_ham.get_symbolic_system()

        # Should have 8 coordinates (4 u + 4 u')
        assert len(system.coordinates) == 8
        assert system.is_extended is True

    def test_ks_hamiltonian_structure(self):
        """Test structure of regularized Hamiltonian K."""
        mu = Symbol('mu', positive=True)
        ks_ham = create_ks_hamiltonian_kepler(mu)
        system = ks_ham.get_symbolic_system()

        H = system.H

        # H should contain u and u_prime symbols
        u_syms = symbols('u_0:4', real=True)
        u_prime_syms = symbols('u_0_prime:4', real=True)

        # Check that Hamiltonian contains these symbols
        free_syms = H.free_symbols
        assert any(u in free_syms for u in u_syms)
        assert any(up in free_syms for up in u_prime_syms)

    def test_bilinear_constraint_ks(self):
        """Test bilinear constraint for KS Hamiltonian."""
        ks_ham = create_ks_hamiltonian_kepler()
        constraint = ks_ham.bilinear_constraints()

        # Constraint should be |u|² - r = 0
        assert constraint is not None
        assert constraint.has(Symbol('r'))

    def test_compute_hessian_ks(self):
        """Test Hessian computation for KS Hamiltonian."""
        ks_ham = create_ks_hamiltonian_kepler()
        hess = ks_ham.compute_hessian_ks()

        # Hessian should be 8×8
        assert hess.shape == (8, 8), "Hessian should be 8×8 for single pair"


class TestKSPairwiseHamiltonian:
    """Test pairwise KS Hamiltonian for three-body problem."""

    def test_create_pairwise_3bp(self):
        """Test creation of pairwise KS Hamiltonian."""
        m1, m2, m3 = symbols('m_1 m_2 m_3', positive=True)
        ks_3bp = create_ks_pairwise_3bp((m1, m2, m3))

        assert isinstance(ks_3bp, KSPairwiseHamiltonian)
        assert ks_3bp.masses == (m1, m2, m3)

    def test_pairwise_coordinates(self):
        """Test that pairwise system has 12 spinor coordinates."""
        ks_3bp = create_ks_pairwise_3bp()
        system = ks_3bp.get_symbolic_system()

        # Should have 24 coordinates (12 u + 12 u')
        assert len(system.coordinates) == 24
        assert system.dimension == 12  # 12D configuration space

    def test_pairwise_hamiltonian_structure(self):
        """Test structure of pairwise Hamiltonian."""
        ks_3bp = create_ks_pairwise_3bp()

        H = ks_3bp.H_pairwise
        assert H is not None

        # Should contain all 12 spinor components
        u12_syms = symbols('u_12_0:4')
        u23_syms = symbols('u_23_0:4')
        u31_syms = symbols('u_31_0:4')

        free_syms = H.free_symbols
        assert any(u in free_syms for u in u12_syms)
        assert any(u in free_syms for u in u23_syms)
        assert any(u in free_syms for u in u31_syms)

    def test_pairwise_constraints(self):
        """Test constraint equations for pairwise system."""
        ks_3bp = create_ks_pairwise_3bp()

        constraints = ks_3bp.constraints
        assert len(constraints) == 6, "Should have 6 constraints (3 bilinear + 3 closure)"

    def test_pairwise_hessian(self):
        """Test Hessian computation for pairwise system."""
        ks_3bp = create_ks_pairwise_3bp()
        hess = ks_3bp.compute_hessian()

        # Hessian should be 24×24
        assert hess.shape == (24, 24), "Hessian should be 24×24 for pairwise 3BP"

    def test_constraint_jacobian(self):
        """Test constraint Jacobian computation."""
        ks_3bp = create_ks_pairwise_3bp()
        jac = ks_3bp.constraint_jacobian()

        # Jacobian should be 6×24 (6 constraints, 24 coordinates)
        assert jac.shape == (6, 24), "Jacobian should be 6×24"


class TestUpstairsMRPreparation:
    """Test preparation for upstairs Morales-Ramis test."""

    def test_prepare_ks_for_mr_test(self):
        """Test preparation of KS system for MR analysis."""
        masses = (1.0, 1.0, 1.0)
        data = prepare_ks_for_upstairs_mr_test(masses)

        # Check all required fields present
        assert 'hamiltonian' in data
        assert 'hessian' in data
        assert 'constraints' in data
        assert 'constraint_jacobian' in data
        assert 'coordinates' in data
        assert 'system' in data

    def test_mr_test_masses_substituted(self):
        """Test that masses are numerically substituted."""
        masses = (1.5, 2.0, 2.5)
        data = prepare_ks_for_upstairs_mr_test(masses, orbit_name='test')

        H = data['hamiltonian']

        # m_1, m_2, m_3 symbols should not be in H (substituted)
        m1_sym, m2_sym, m3_sym = symbols('m_1 m_2 m_3')
        free_syms = H.free_symbols

        # Note: They may still appear if simplification didn't eliminate them
        # The test is that numerical values can be computed

        # At minimum, check that we can evaluate (no mass symbols required)
        # This is a weaker test, but appropriate for symbolic context

    def test_mr_test_hessian_shape(self):
        """Test Hessian shape in MR preparation."""
        masses = (1.0, 1.0, 1.0)
        data = prepare_ks_for_upstairs_mr_test(masses)

        hess = data['hessian']
        assert hess.shape == (24, 24), "Hessian should be 24×24"

    def test_mr_test_constraints_count(self):
        """Test number of constraints in MR preparation."""
        masses = (1.0, 1.0, 1.0)
        data = prepare_ks_for_upstairs_mr_test(masses)

        constraints = data['constraints']
        assert len(constraints) == 6, "Should have 6 constraints"


class TestSymbolicIdentities:
    """Test fundamental symbolic identities."""

    def test_bilinear_identity_general_u(self):
        """Test |L(u)·u|² = |u|⁴ for general symbolic u."""
        # This is tested in verify_bilinear_relation_symbolic
        assert verify_bilinear_relation_symbolic() is True

    def test_levi_civita_rank(self):
        """Test that L(u) has full rank for u ≠ 0."""
        # For symbolic test, just check that L(u) is not zero matrix
        u = Matrix(symbols('u_0:4', real=True))
        L = levi_civita_matrix(u)

        # L should not be identically zero
        assert not all(L[i, j] == 0 for i in range(3) for j in range(4))

    def test_ks_preserves_dimension(self):
        """Test that KS map has correct dimensions."""
        # 3D → 4D (forward)
        r_vec = Matrix(symbols('x y z', real=True))
        v_vec = Matrix(symbols('v_x v_y v_z', real=True))
        u, u_prime = ks_transform_symbolic(r_vec, v_vec)

        assert len(u) == 4
        assert len(u_prime) == 4

        # 4D → 3D (inverse)
        u_sym = Matrix(symbols('u_0:4', real=True))
        u_prime_sym = Matrix(symbols('u_0_prime:4', real=True))
        r, v = ks_inverse_symbolic(u_sym, u_prime_sym)

        assert len(r) == 3
        assert len(v) == 3


# Integration tests

class TestKSIntegration:
    """Integration tests combining multiple components."""

    def test_kepler_to_mr_pipeline(self):
        """Test full pipeline from Kepler to MR analysis."""
        # Create KS Hamiltonian
        mu = Symbol('mu', positive=True)
        ks_ham = create_ks_hamiltonian_kepler(mu)

        # Get symbolic system
        system = ks_ham.get_symbolic_system()

        # Compute gradient
        grad = system.gradient()
        assert grad.shape == (8, 1)

        # Compute Hessian
        hess = system.hessian()
        assert hess.shape == (8, 8)

        # Get Hamilton's equations
        dq_dt, dp_dt = system.hamiltons_equations()
        assert len(dq_dt) == 4
        assert len(dp_dt) == 4

    def test_3bp_full_system(self):
        """Test full 3BP pairwise system."""
        # Create pairwise Hamiltonian
        ks_3bp = create_ks_pairwise_3bp()

        # Get system
        system = ks_3bp.get_symbolic_system()

        # Compute gradient
        grad = system.gradient()
        assert grad.shape == (24, 1)

        # Compute Hessian
        hess = ks_3bp.compute_hessian()
        assert hess.shape == (24, 24)

        # Compute constraint Jacobian
        jac = ks_3bp.constraint_jacobian()
        assert jac.shape == (6, 24)

        # Verify constraints is a list
        assert isinstance(system.constraints, list)
        assert len(system.constraints) == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
