"""
Tests for KS transformation (WP 2.3).

Tests:
1. Levi-Civita matrix properties
2. Bilinear relation r = L(u)·u
3. Forward/inverse KS transform
4. Roundtrip accuracy
5. Collision regularization
"""

import pytest
import numpy as np

from src.python.regularization import (
    levi_civita_matrix,
    levi_civita_map,
    inverse_levi_civita_map,
    validate_bilinear_relation,
    SpinorVector,
    create_spinor,
    KSState,
    cartesian_to_ks,
    ks_to_cartesian,
    validate_ks_roundtrip,
)


def test_levi_civita_matrix_structure():
    """Test Levi-Civita matrix has correct structure."""
    u = np.array([1.0, 0.0, 0.0, 0.0])
    L = levi_civita_matrix(u)

    # Should be 3×4
    assert L.shape == (3, 4)

    # Expected for u = (1,0,0,0)
    expected = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0]
    ])

    np.testing.assert_allclose(L, expected, atol=1e-12)


def test_levi_civita_orthogonality():
    """Test L(u)·L^T(u) = ‖u‖² I₃."""
    u = np.array([1.0, 2.0, 3.0, 4.0])
    L = levi_civita_matrix(u)

    # Compute L·L^T (3×3)
    LLT = L @ L.T

    # Should equal ‖u‖² I₃
    u_norm_sq = np.dot(u, u)
    expected = u_norm_sq * np.eye(3)

    np.testing.assert_allclose(LLT, expected, atol=1e-12)


def test_bilinear_relation():
    """Test r = L(u)·u bilinear relation."""
    u = np.array([1.0, 2.0, 3.0, 4.0])

    # Compute r = L(u)·u
    r = levi_civita_map(u, u)

    # Verify ‖r‖² = ‖u‖⁴
    r_norm_sq = np.dot(r, r)
    u_norm_sq = np.dot(u, u)

    np.testing.assert_allclose(r_norm_sq, u_norm_sq**2, rtol=1e-12)

    # Verify validation function
    assert validate_bilinear_relation(u, r)


def test_inverse_levi_civita_map():
    """Test inverse LC map: r → u such that L(u)·u = r."""
    r = np.array([1.0, 2.0, 3.0])

    # Find u from r
    u = inverse_levi_civita_map(r)

    # Verify u is 4D
    assert u.shape == (4,)

    # Verify L(u)·u = r
    r_reconstructed = levi_civita_map(u, u)
    np.testing.assert_allclose(r_reconstructed, r, atol=1e-10)


def test_spinor_vector_operations():
    """Test SpinorVector arithmetic."""
    u1 = create_spinor(1.0, 2.0, 3.0, 4.0)
    u2 = create_spinor(0.5, 1.0, 1.5, 2.0)

    # Addition
    u_sum = u1 + u2
    expected_sum = np.array([1.5, 3.0, 4.5, 6.0])
    np.testing.assert_allclose(u_sum.to_array(), expected_sum, atol=1e-12)

    # Scalar multiplication
    u_scaled = u1 * 2.0
    expected_scaled = np.array([2.0, 4.0, 6.0, 8.0])
    np.testing.assert_allclose(u_scaled.to_array(), expected_scaled, atol=1e-12)

    # Norm
    u_norm_sq = u1.norm_squared
    expected_norm_sq = 1 + 4 + 9 + 16
    np.testing.assert_allclose(u_norm_sq, expected_norm_sq, atol=1e-12)

    # Radius property
    assert u1.radius == u1.norm_squared


def test_cartesian_to_ks_forward():
    """Test forward Cartesian → KS transform."""
    r = np.array([1.0, 0.0, 0.0])
    v = np.array([0.0, 1.0, 0.0])

    # Transform to KS
    ks_state = cartesian_to_ks(r, v)

    # Verify types
    assert isinstance(ks_state, KSState)
    assert isinstance(ks_state.u, SpinorVector)
    assert isinstance(ks_state.u_prime, SpinorVector)

    # Verify radius
    assert ks_state.radius == pytest.approx(1.0, abs=1e-10)

    # Verify time derivative
    assert ks_state.time_derivative == ks_state.radius


def test_ks_to_cartesian_inverse():
    """Test inverse KS → Cartesian transform."""
    # Create KS state
    u = create_spinor(1.0, 0.0, 0.0, 0.0)
    u_prime = create_spinor(0.0, 0.5, 0.0, 0.0)
    ks_state = KSState(u=u, u_prime=u_prime, fictitious_time=0.0)

    # Transform to Cartesian
    r, v = ks_to_cartesian(ks_state)

    # Verify shapes
    assert r.shape == (3,)
    assert v.shape == (3,)

    # Verify radius
    r_magnitude = np.linalg.norm(r)
    assert r_magnitude == pytest.approx(u.norm_squared, abs=1e-10)


def test_ks_roundtrip_generic():
    """Test Cartesian → KS → Cartesian roundtrip."""
    r = np.array([2.0, 1.0, 0.5])
    v = np.array([0.1, -0.2, 0.3])

    # Roundtrip
    assert validate_ks_roundtrip(r, v, tolerance=1e-10)


def test_ks_roundtrip_multiple_cases():
    """Test roundtrip for various configurations."""
    test_cases = [
        # (r, v)
        (np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])),
        (np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0])),
        (np.array([1.0, 1.0, 1.0]), np.array([0.5, 0.5, 0.5])),
        (np.array([2.0, -1.0, 0.5]), np.array([-0.3, 0.2, 0.1])),
    ]

    for r, v in test_cases:
        assert validate_ks_roundtrip(r, v, tolerance=1e-10), \
            f"Roundtrip failed for r={r}, v={v}"


def test_ks_collision_limit():
    """Test KS behavior near collision (r → 0)."""
    # Small separation
    r_small = np.array([1e-6, 0.0, 0.0])
    v = np.array([0.0, 0.1, 0.0])

    # Transform should work
    ks_state = cartesian_to_ks(r_small, v)

    # Spinor should be finite
    assert ks_state.u.norm < 1e3, "Spinor norm should be small near collision"

    # At exact collision
    r_zero = np.array([0.0, 0.0, 0.0])
    ks_zero = cartesian_to_ks(r_zero, v)

    # u' should be zero at collision
    assert ks_zero.u_prime.norm_squared < 1e-10


def test_ks_time_derivative():
    """Test time dilation factor dt/ds = r = ‖u‖²."""
    r = np.array([3.0, 4.0, 0.0])
    v = np.array([0.0, 0.0, 1.0])

    ks_state = cartesian_to_ks(r, v)

    # dt/ds should equal r = ‖u‖² = ‖r‖ (not ‖r‖²!)
    r_magnitude = np.linalg.norm(r)
    assert ks_state.time_derivative == pytest.approx(r_magnitude, abs=1e-10)


def test_ks_state_validation():
    """Test KS state validation."""
    r = np.array([1.0, 2.0, 3.0])
    v = np.array([0.5, -0.5, 0.2])

    ks_state = cartesian_to_ks(r, v)

    # Should be valid
    assert ks_state.validate(r_expected=r)

    # Should fail with wrong expected r
    r_wrong = np.array([5.0, 0.0, 0.0])
    assert not ks_state.validate(r_expected=r_wrong)


def test_velocity_transformation():
    """Test velocity transform v = 2L(u)·u'."""
    r = np.array([1.0, 0.0, 0.0])
    v_original = np.array([0.0, 2.0, 0.0])

    # Transform
    ks_state = cartesian_to_ks(r, v_original)
    r_reconstructed, v_reconstructed = ks_to_cartesian(ks_state)

    # Check velocity
    np.testing.assert_allclose(v_reconstructed, v_original, atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
