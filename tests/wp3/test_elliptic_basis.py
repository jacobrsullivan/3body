"""
Unit tests for elliptic_basis.py (AMENDED WP3.3 Phase 2).

Tests Jacobi elliptic functions, complete elliptic integrals, and elliptic basis construction.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import pytest
from symbolic.elliptic_basis import (
    jacobi_sn,
    jacobi_cn,
    jacobi_dn,
    complete_elliptic_K,
    complete_elliptic_E,
    estimate_elliptic_parameter,
    construct_elliptic_basis,
    test_jacobi_identities
)


class TestJacobiEllipticFunctions:
    """Test Jacobi elliptic functions."""

    def test_jacobi_identities(self):
        """Test fundamental Jacobi identities."""
        # sn² + cn² = 1
        # dn² + m·sn² = 1

        test_cases = [
            (0.0, 0.5),
            (0.5, 0.1),
            (1.0, 0.5),
            (1.5, 0.9),
            (2.0, 0.5),
        ]

        for u, m in test_cases:
            sn = jacobi_sn(u, m)
            cn = jacobi_cn(u, m)
            dn = jacobi_dn(u, m)

            # Identity 1: sn² + cn² = 1
            assert np.isclose(sn**2 + cn**2, 1.0, rtol=1e-10), \
                f"sn²+cn² ≠ 1 at u={u}, m={m}"

            # Identity 2: dn² + m·sn² = 1
            assert np.isclose(dn**2 + m*sn**2, 1.0, rtol=1e-10), \
                f"dn²+m·sn² ≠ 1 at u={u}, m={m}"

    def test_jacobi_initial_values(self):
        """Test values at u=0."""
        m = 0.5

        assert np.isclose(jacobi_sn(0, m), 0.0, atol=1e-10), "sn(0) should be 0"
        assert np.isclose(jacobi_cn(0, m), 1.0, rtol=1e-10), "cn(0) should be 1"
        assert np.isclose(jacobi_dn(0, m), 1.0, rtol=1e-10), "dn(0) should be 1"

    def test_jacobi_m_limits(self):
        """Test limiting cases m→0 and m→1."""
        u = 1.0

        # m=0: sn→sin, cn→cos, dn→1
        m_small = 0.001
        sn_0 = jacobi_sn(u, m_small)
        cn_0 = jacobi_cn(u, m_small)
        dn_0 = jacobi_dn(u, m_small)

        assert np.isclose(sn_0, np.sin(u), atol=0.01), "sn(u,0) should approach sin(u)"
        assert np.isclose(cn_0, np.cos(u), atol=0.01), "cn(u,0) should approach cos(u)"
        assert np.isclose(dn_0, 1.0, atol=0.01), "dn(u,0) should approach 1"

        # m=1: sn→tanh, cn→sech, dn→sech
        m_large = 0.999
        sn_1 = jacobi_sn(u, m_large)
        cn_1 = jacobi_cn(u, m_large)
        dn_1 = jacobi_dn(u, m_large)

        assert np.isclose(sn_1, np.tanh(u), atol=0.1), "sn(u,1) should approach tanh(u)"
        assert np.isclose(cn_1, 1.0/np.cosh(u), atol=0.1), "cn(u,1) should approach sech(u)"


class TestCompleteEllipticIntegrals:
    """Test complete elliptic integrals K(m) and E(m)."""

    def test_complete_K_values(self):
        """Test known values of K(m)."""
        # K(0) = π/2
        K_0 = complete_elliptic_K(0.0)
        assert np.isclose(K_0, np.pi/2, rtol=1e-6), f"K(0) = {K_0} ≠ π/2"

        # K(1/2) ≈ 1.8540746773...
        K_half = complete_elliptic_K(0.5)
        assert np.isclose(K_half, 1.8540746773, rtol=1e-6), f"K(1/2) incorrect"

    def test_complete_E_values(self):
        """Test known values of E(m)."""
        # E(0) = π/2
        E_0 = complete_elliptic_E(0.0)
        assert np.isclose(E_0, np.pi/2, rtol=1e-6), f"E(0) = {E_0} ≠ π/2"

        # E(1) = 1
        E_1 = complete_elliptic_E(0.999)  # Use 0.999 instead of 1 to avoid singularity
        assert np.isclose(E_1, 1.0, atol=0.01), f"E(1) should approach 1"

    def test_K_E_inequality(self):
        """Test Legendre relation: K(m)E'(m) + E(m)K'(m) - K(m)K'(m) = π/2"""
        # For m in (0,1), we have E(m) < K(m)
        m_values = [0.1, 0.3, 0.5, 0.7, 0.9]

        for m in m_values:
            K = complete_elliptic_K(m)
            E = complete_elliptic_E(m)

            assert E <= K, f"E(m) should be ≤ K(m) for m={m}"


class TestEllipticBasisConstruction:
    """Test elliptic basis function construction."""

    def test_basis_construction_basic(self):
        """Test basic elliptic basis construction."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_elliptic_basis(masses, max_degree=2, m_values=[0.5])

        # Should have functions for 3 bodies × multiple types
        assert len(basis) >= 10, f"Expected ≥10 functions, got {len(basis)}"

        # Each function should be tuple (callable, description)
        for func, desc in basis:
            assert callable(func), f"Function {desc} is not callable"
            assert isinstance(desc, str), f"Description is not string"

    def test_basis_evaluation(self):
        """Test that elliptic basis functions can be evaluated."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_elliptic_basis(masses, max_degree=1, m_values=[0.5])

        # Create test state (18D: 9D position + 9D velocity for 3 bodies)
        state = np.random.randn(18)

        # Evaluate each basis function
        for func, desc in basis[:10]:  # Test first 10
            try:
                value = func(state)
                assert np.isfinite(value), f"Function {desc} returned non-finite value"
            except Exception as e:
                pytest.fail(f"Failed to evaluate {desc}: {e}")

    def test_basis_sn_function(self):
        """Test that sn-based basis functions work correctly."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_elliptic_basis(masses, max_degree=1, m_values=[0.5])

        # Find sn-based functions
        sn_funcs = [(f, desc) for f, desc in basis if 'sn(' in desc]
        assert len(sn_funcs) > 0, "Should have sn-based functions"

        # Test on specific state
        state = np.ones(18)  # All ones for simplicity
        sn_func, desc = sn_funcs[0]

        value = sn_func(state)
        assert np.isfinite(value), f"{desc} returned non-finite value"
        assert -1 <= value <= 1, f"sn should be in [-1, 1], got {value}"

    def test_basis_multiple_m_values(self):
        """Test basis with multiple elliptic parameters."""
        masses = np.array([1.0, 1.0, 1.0])
        m_values = [0.1, 0.5, 0.9]

        basis = construct_elliptic_basis(masses, max_degree=1, m_values=m_values)

        # Should have functions for each m value
        for m in m_values:
            m_funcs = [desc for f, desc in basis if f'm={m:.1f}' in desc]
            assert len(m_funcs) > 0, f"Should have functions for m={m}"


class TestEllipticParameterEstimation:
    """Test elliptic parameter estimation from trajectory."""

    def test_estimate_from_quasi_periodic(self):
        """Test estimation from quasi-periodic signal."""
        # Create synthetic quasi-periodic trajectory
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 18)

        # Quasi-periodic integral
        omega1 = 1.0
        omega2 = np.sqrt(2)  # Incommensurable

        def quasi_periodic_integral(state):
            # Use state to determine time index (simplified)
            idx = int(np.sum(np.abs(state[:3])) * 100) % len(t)
            return np.sin(omega1 * t[idx]) + 0.5 * np.sin(omega2 * t[idx])

        m_est = estimate_elliptic_parameter(trajectory, t, quasi_periodic_integral)

        # m should be in [0, 1]
        assert 0.0 <= m_est <= 1.0, f"Elliptic parameter m={m_est} outside [0,1]"

    def test_estimate_from_constant(self):
        """Test estimation from constant (should return default)."""
        t = np.linspace(0, 100, 1000)
        trajectory = np.random.randn(1000, 18)

        def constant_integral(state):
            return 1.0

        m_est = estimate_elliptic_parameter(trajectory, t, constant_integral)

        # Should return default value
        assert m_est == 0.5, f"Expected default m=0.5 for constant, got {m_est}"


class TestEllipticBasisIntegration:
    """Test integration with symbolic regression."""

    def test_basis_library_matrix(self):
        """Test building basis library matrix for regression."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_elliptic_basis(masses, max_degree=1, m_values=[0.5])

        # Sample states
        n_samples = 100
        states = np.random.randn(n_samples, 18)

        # Build library matrix
        n_funcs = len(basis)
        Theta = np.zeros((n_samples, n_funcs))

        for i, state in enumerate(states):
            for j, (func, desc) in enumerate(basis):
                Theta[i, j] = func(state)

        # Check shape
        assert Theta.shape == (n_samples, n_funcs)

        # Check for NaNs/infs
        assert not np.any(np.isnan(Theta)), "Basis matrix has NaNs"
        assert not np.any(np.isinf(Theta)), "Basis matrix has infinities"


def test_jacobi_identities_suite():
    """Run full Jacobi identities test suite."""
    result = test_jacobi_identities()
    assert result is True, "Jacobi identities test failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
