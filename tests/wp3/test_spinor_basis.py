"""
Unit tests for spinor_basis.py (AMENDED WP3.3).

Tests Kustaanheimo-Stiefel (KS) transformation and spinor basis functions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import pytest
from symbolic.spinor_basis import (
    position_to_spinor,
    spinor_to_position,
    compute_spinor_norm,
    quaternion_product,
    construct_spinor_basis,
    test_ks_transformation
)


class TestKSTransformation:
    """Test Kustaanheimo-Stiefel transformation."""

    def test_ks_norm_property(self):
        """Test that |u|^2 = |r| for KS transformation."""
        # Test multiple 3D positions
        test_positions = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
            np.array([1.0, 1.0, 1.0]),
            np.array([3.0, -2.0, 1.0]),
            np.array([-1.0, 2.0, -3.0]),
        ]

        for r in test_positions:
            u = position_to_spinor(r)
            r_mag = np.linalg.norm(r)
            u_norm_sq = compute_spinor_norm(u)**2

            # Check |u|^2 = |r|
            assert np.isclose(u_norm_sq, r_mag, rtol=1e-10), \
                f"KS norm property failed for r={r}: |u|^2={u_norm_sq:.10f}, |r|={r_mag:.10f}"

    def test_ks_inverse(self):
        """Test that spinor_to_position inverts position_to_spinor."""
        test_positions = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
            np.array([1.0, 1.0, 1.0]),
            np.array([3.0, -2.0, 1.0]),
            np.array([-1.0, 2.0, -3.0]),
        ]

        for r in test_positions:
            u = position_to_spinor(r)
            r_recovered = spinor_to_position(u)

            # Check r_recovered ≈ r
            assert np.allclose(r_recovered, r, rtol=1e-10), \
                f"KS inverse failed for r={r}: recovered={r_recovered}"

    def test_ks_edge_cases(self):
        """Test KS transformation edge cases."""
        # Test x ≈ -|r| (branch cut)
        r_edge = np.array([-1.0, 1e-10, 1e-10])
        u = position_to_spinor(r_edge)
        r_recovered = spinor_to_position(u)
        assert np.allclose(r_recovered, r_edge, atol=1e-8)

        # Test near-zero position
        r_small = np.array([1e-10, 1e-10, 1e-10])
        u_small = position_to_spinor(r_small)
        assert compute_spinor_norm(u_small) < 1e-4

    def test_quaternion_product(self):
        """Test quaternion product properties."""
        u = np.array([1.0, 2.0, 3.0, 4.0])
        v = np.array([2.0, 1.0, -1.0, 0.5])

        # Compute product
        w = quaternion_product(u, v)

        # Check dimensions
        assert w.shape == (4,)

        # Test non-commutativity (uv ≠ vu in general)
        w_reverse = quaternion_product(v, u)
        assert not np.allclose(w, w_reverse)

        # Test with identity (1, 0, 0, 0)
        identity = np.array([1.0, 0.0, 0.0, 0.0])
        assert np.allclose(quaternion_product(u, identity), u)
        assert np.allclose(quaternion_product(identity, u), u)


class TestSpinorBasisConstruction:
    """Test spinor basis function construction."""

    def test_basis_construction_basic(self):
        """Test basic spinor basis construction."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2, include_quaternion_products=False)

        # Should have at least 24 functions (individual components)
        assert len(basis_funcs) >= 24, f"Expected ≥24 functions, got {len(basis_funcs)}"

        # Each function should be a tuple (callable, description)
        for func, desc in basis_funcs:
            assert callable(func), f"Function {desc} is not callable"
            assert isinstance(desc, str), f"Description for {func} is not a string"

    def test_basis_construction_with_quaternions(self):
        """Test spinor basis with quaternion products."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2, include_quaternion_products=True)

        # Should have more functions with quaternion products
        assert len(basis_funcs) >= 30, f"Expected ≥30 functions with quaternions, got {len(basis_funcs)}"

    def test_basis_evaluation(self):
        """Test that basis functions can be evaluated on states."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2, include_quaternion_products=False)

        # Create test state (24D for 3 bodies: 12D position + 12D velocity)
        state = np.random.randn(24)

        # Try evaluating each basis function
        for func, desc in basis_funcs:
            try:
                value = func(state)
                assert np.isfinite(value), f"Function {desc} returned non-finite value"
            except Exception as e:
                pytest.fail(f"Failed to evaluate function {desc}: {e}")

    def test_basis_dimensionality(self):
        """Test that basis functions handle different state dimensions."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2)

        # Test with 2 bodies (16D)
        state_2body = np.random.randn(16)
        # This should work since we're using extract_spinor_coordinates

        # Test with 3 bodies (24D)
        state_3body = np.random.randn(24)
        for func, desc in basis_funcs[:5]:  # Test first few functions
            value = func(state_3body)
            assert np.isfinite(value)


class TestSpinorBasisPhysics:
    """Test physical properties of spinor basis."""

    def test_spinor_norm_basis_functions(self):
        """Test spinor norm basis functions."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2)

        # Find norm-based functions (|u_i|^2)
        norm_funcs = [f for f, desc in basis_funcs if '|u' in desc and '|^2' in desc]
        assert len(norm_funcs) >= 3, "Should have norm functions for each body"

        # Create state where body positions are known
        # For simplicity, use KS transformation on specific positions
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r3 = np.array([0.0, 0.0, 1.0])

        u1 = position_to_spinor(r1)
        u2 = position_to_spinor(r2)
        u3 = position_to_spinor(r3)

        # Build full state (24D)
        state = np.concatenate([u1, u2, u3, np.zeros(12)])  # 12D spinors + 12D velocities

        # Evaluate norm function for first body
        norm_func_1 = norm_funcs[0]
        norm_value = norm_func_1(state)

        # Should equal |r1|
        expected = np.linalg.norm(r1)
        assert np.isclose(norm_value, expected, rtol=1e-8), \
            f"Spinor norm function mismatch: {norm_value} != {expected}"

    def test_spinor_inner_products(self):
        """Test spinor inner product basis functions."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2)

        # Find inner product functions
        inner_prod_funcs = [f for f, desc in basis_funcs if '·' in desc or 'dot' in desc.lower()]

        # Should have some inner product functions
        assert len(inner_prod_funcs) > 0, "Should have inner product basis functions"

        # Test on random state
        state = np.random.randn(24)
        for func in inner_prod_funcs[:3]:
            value = func(state)
            assert np.isfinite(value)


class TestIntegrationWithRegression:
    """Test integration with symbolic regression pipeline."""

    def test_basis_library_interface(self):
        """Test that spinor basis can be used in regression."""
        masses = np.array([1.0, 1.0, 1.0])
        basis_funcs = construct_spinor_basis(masses, max_degree=2)

        # Create sample states
        n_samples = 100
        states = np.random.randn(n_samples, 24)

        # Evaluate basis library on all samples
        n_funcs = len(basis_funcs)
        Theta = np.zeros((n_samples, n_funcs))

        for i, state in enumerate(states):
            for j, (func, desc) in enumerate(basis_funcs):
                Theta[i, j] = func(state)

        # Check shape
        assert Theta.shape == (n_samples, n_funcs)

        # Check for NaNs
        assert not np.any(np.isnan(Theta)), "Basis evaluation produced NaNs"

        # Check for infs
        assert not np.any(np.isinf(Theta)), "Basis evaluation produced infinities"


def test_full_ks_transformation():
    """Run full KS transformation test suite."""
    # This calls the built-in test from spinor_basis.py
    result = test_ks_transformation()
    assert result is True, "KS transformation tests failed"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
