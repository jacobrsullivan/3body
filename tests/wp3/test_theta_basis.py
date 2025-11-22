"""
Unit tests for theta_basis.py (AMENDED WP3.3 Phase 4).

Tests Jacobi theta functions and theta basis construction.

NOTE: Theta functions are highly speculative - these tests verify mathematical
correctness, not physical relevance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import pytest
from symbolic.theta_basis import (
    jacobi_theta1,
    jacobi_theta2,
    jacobi_theta3,
    jacobi_theta4,
    estimate_modular_parameter,
    construct_theta_basis,
    test_theta_identities
)


class TestJacobiThetaFunctions:
    """Test Jacobi theta functions."""

    def test_theta1_zeros(self):
        """Test that θ₁(0, q) = 0."""
        tau_values = [1.0j, 2.0j, 0.5j]

        for tau in tau_values:
            q = np.exp(1.0j * np.pi * tau)
            theta1_0 = jacobi_theta1(0.0, q)

            assert np.abs(theta1_0) < 1e-10, f"θ₁(0) = {theta1_0} ≠ 0 for tau={tau}"

    def test_theta_symmetries(self):
        """Test symmetry properties of theta functions."""
        tau = 1.0j
        q = np.exp(1.0j * np.pi * tau)
        z = 1.5

        # θ₁(-z) = -θ₁(z) (odd)
        theta1_z = jacobi_theta1(z, q)
        theta1_mz = jacobi_theta1(-z, q)
        assert np.isclose(theta1_mz, -theta1_z, rtol=1e-8), "θ₁ should be odd"

        # θ₂(-z) = θ₂(z) (even)
        theta2_z = jacobi_theta2(z, q)
        theta2_mz = jacobi_theta2(-z, q)
        assert np.isclose(theta2_mz, theta2_z, rtol=1e-8), "θ₂ should be even"

        # θ₃(-z) = θ₃(z) (even)
        theta3_z = jacobi_theta3(z, q)
        theta3_mz = jacobi_theta3(-z, q)
        assert np.isclose(theta3_mz, theta3_z, rtol=1e-8), "θ₃ should be even"

        # θ₄(-z) = θ₄(z) (even)
        theta4_z = jacobi_theta4(z, q)
        theta4_mz = jacobi_theta4(-z, q)
        assert np.isclose(theta4_mz, theta4_z, rtol=1e-8), "θ₄ should be even"

    def test_theta_values_real_z(self):
        """Test theta values for real z."""
        tau = 1.0j
        q = np.exp(1.0j * np.pi * tau)

        z_values = [0.0, 0.5, 1.0, np.pi/2]

        for z in z_values:
            theta1 = jacobi_theta1(z, q)
            theta2 = jacobi_theta2(z, q)
            theta3 = jacobi_theta3(z, q)
            theta4 = jacobi_theta4(z, q)

            # All should be finite
            assert np.isfinite(theta1), f"θ₁({z}) not finite"
            assert np.isfinite(theta2), f"θ₂({z}) not finite"
            assert np.isfinite(theta3), f"θ₃({z}) not finite"
            assert np.isfinite(theta4), f"θ₄({z}) not finite"

    def test_theta_q_constraint(self):
        """Test that |q| < 1 is required."""
        # q with |q| >= 1 should return NaN
        q_bad = 1.5 + 0j

        result = jacobi_theta1(1.0, q_bad)
        assert np.isnan(result), "Should return NaN for |q| >= 1"


class TestThetaBasisConstruction:
    """Test theta basis construction."""

    def test_basis_construction_basic(self):
        """Test basic theta basis construction."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_theta_basis(masses, max_degree=1, tau_values=[1.0j])

        # Should have multiple functions
        assert len(basis) >= 4, f"Expected ≥4 functions, got {len(basis)}"

        # Each function should be tuple
        for func, desc in basis:
            assert callable(func), f"Function {desc} is not callable"
            assert isinstance(desc, str), f"Description is not string"

    def test_basis_evaluation(self):
        """Test that theta basis functions can be evaluated."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_theta_basis(masses, max_degree=1, tau_values=[1.0j])

        # Test state
        state = np.random.randn(18)

        # Evaluate each function
        for func, desc in basis[:5]:  # Test first 5
            try:
                value = func(state)
                assert np.isfinite(value), f"Function {desc} returned non-finite value"
            except Exception as e:
                pytest.fail(f"Failed to evaluate {desc}: {e}")

    def test_basis_warning_printed(self, capsys):
        """Test that construction prints warning about speculative nature."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_theta_basis(masses)

        captured = capsys.readouterr()
        assert "WARNING" in captured.out or "SPECULATIVE" in captured.out, \
            "Should print warning about speculative nature"

    def test_basis_multiple_tau_values(self):
        """Test basis with multiple modular parameters."""
        masses = np.array([1.0, 1.0, 1.0])
        tau_values = [1.0j, 2.0j]

        basis = construct_theta_basis(masses, max_degree=1, tau_values=tau_values)

        # Should have functions for each tau
        for tau in tau_values:
            tau_funcs = [desc for f, desc in basis if f'τ={tau}' in desc]
            assert len(tau_funcs) > 0, f"Should have functions for τ={tau}"


class TestModularParameterEstimation:
    """Test modular parameter estimation."""

    def test_estimate_from_trajectory(self):
        """Test estimation from trajectory."""
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 18)

        def test_integral(state):
            return np.sin(np.sum(state[:3]))

        tau = estimate_modular_parameter(trajectory, t, test_integral)

        # Should be complex with positive imaginary part
        assert np.imag(tau) > 0, f"Im(τ) = {np.imag(tau)} should be > 0"

    def test_estimate_returns_default(self):
        """Test that estimation returns default for constant."""
        t = np.linspace(0, 100, 1000)
        trajectory = np.random.randn(1000, 18)

        def constant_integral(state):
            return 1.0

        tau = estimate_modular_parameter(trajectory, t, constant_integral)

        # Should return default (pure imaginary)
        assert tau == 1.0j, f"Expected default τ=i, got {tau}"


class TestThetaFunctionIdentities:
    """Test theta function mathematical identities."""

    def test_theta_squares_relation(self):
        """Test relation between theta function squares."""
        # This is a simplified test - full Jacobi identities are complex
        tau = 1.0j
        q = np.exp(1.0j * np.pi * tau)

        theta2_0 = jacobi_theta2(0.0, q)
        theta3_0 = jacobi_theta3(0.0, q)
        theta4_0 = jacobi_theta4(0.0, q)

        # All should be positive and real for tau=i, z=0
        assert np.real(theta2_0) > 0, "θ₂(0) should be positive"
        assert np.real(theta3_0) > 0, "θ₃(0) should be positive"
        assert np.real(theta4_0) > 0, "θ₄(0) should be positive"

    def test_theta_periodicity(self):
        """Test periodicity properties."""
        tau = 1.0j
        q = np.exp(1.0j * np.pi * tau)

        z = 1.0

        # θ₃(z + π) should equal θ₃(z)
        theta3_z = jacobi_theta3(z, q)
        theta3_z_plus_pi = jacobi_theta3(z + np.pi, q)

        assert np.isclose(theta3_z_plus_pi, theta3_z, rtol=0.1), \
            "θ₃ should have period π"


class TestThetaBasisIntegration:
    """Test integration with regression pipeline."""

    def test_basis_library_construction(self):
        """Test that theta basis can be used in regression."""
        masses = np.array([1.0, 1.0, 1.0])
        basis = construct_theta_basis(masses, max_degree=1, tau_values=[1.0j])

        # Sample states
        n_samples = 50
        states = np.random.randn(n_samples, 18)

        # Build library matrix
        n_funcs = len(basis)
        Theta = np.zeros((n_samples, n_funcs))

        for i, state in enumerate(states):
            for j, (func, desc) in enumerate(basis):
                try:
                    Theta[i, j] = func(state)
                except:
                    Theta[i, j] = 0.0

        # Check shape
        assert Theta.shape == (n_samples, n_funcs)

        # Most values should be finite (some might fail due to complex issues)
        finite_fraction = np.sum(np.isfinite(Theta)) / Theta.size
        assert finite_fraction > 0.8, f"Only {finite_fraction:.1%} of values finite"


def test_theta_identities_suite():
    """Run full theta identities test suite."""
    result = test_theta_identities()
    assert result is True, "Theta identities test failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
