"""
Tests for pairwise KS transformation (WP 2.3).

Tests:
1. Pairwise spinor state creation
2. Constraint validation
3. 3BP → pairwise KS → 3BP roundtrip
4. Constraint manifold dimension
"""

import pytest
import numpy as np

from src.python.coordinates.base import CartesianState, Masses
from src.python.regularization import (
    PairwiseSpinorState,
    cartesian_3bp_to_pairwise_ks,
    pairwise_ks_to_cartesian_3bp,
    validate_pairwise_roundtrip,
    compute_constraint_manifold_dimension,
    create_spinor,
)


@pytest.fixture
def equal_masses():
    """Equal mass system."""
    return Masses(m1=1.0, m2=1.0, m3=1.0)


@pytest.fixture
def simple_cartesian_state():
    """Simple test state: equilateral triangle."""
    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([-0.5, np.sqrt(3)/2, 0.0])
    r3 = np.array([-0.5, -np.sqrt(3)/2, 0.0])

    v1 = np.array([0.0, 0.1, 0.0])
    v2 = np.array([0.0, -0.05, 0.0])
    v3 = np.array([0.0, -0.05, 0.0])

    return CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)


def test_pairwise_spinor_state_creation():
    """Test PairwiseSpinorState creation and properties."""
    u12 = create_spinor(1.0, 0.0, 0.0, 0.0)
    u23 = create_spinor(0.0, 1.0, 0.0, 0.0)
    u31 = create_spinor(0.0, 0.0, 1.0, 0.0)

    u12_prime = create_spinor(0.1, 0.0, 0.0, 0.0)
    u23_prime = create_spinor(0.0, 0.1, 0.0, 0.0)
    u31_prime = create_spinor(0.0, 0.0, 0.1, 0.0)

    state = PairwiseSpinorState(
        u12=u12,
        u23=u23,
        u31=u31,
        u12_prime=u12_prime,
        u23_prime=u23_prime,
        u31_prime=u31_prime
    )

    # Check dimensions
    assert state.spinor_coordinates.shape == (12,)
    assert state.spinor_velocities.shape == (12,)
    assert state.to_vector().shape == (24,)


def test_pairwise_state_vector_conversion():
    """Test to_vector and from_vector roundtrip."""
    u12 = create_spinor(1.0, 2.0, 3.0, 4.0)
    u23 = create_spinor(0.5, 1.0, 1.5, 2.0)
    u31 = create_spinor(-0.5, 0.0, 0.5, 1.0)

    u12_prime = create_spinor(0.1, 0.2, 0.3, 0.4)
    u23_prime = create_spinor(0.05, 0.1, 0.15, 0.2)
    u31_prime = create_spinor(-0.05, 0.0, 0.05, 0.1)

    state = PairwiseSpinorState(
        u12=u12,
        u23=u23,
        u31=u31,
        u12_prime=u12_prime,
        u23_prime=u23_prime,
        u31_prime=u31_prime
    )

    # Convert to vector
    vec = state.to_vector()

    # Reconstruct
    state_reconstructed = PairwiseSpinorState.from_vector(vec)

    # Compare
    np.testing.assert_allclose(
        state_reconstructed.to_vector(),
        state.to_vector(),
        atol=1e-12
    )


def test_cartesian_to_pairwise_ks(simple_cartesian_state):
    """Test forward 3BP Cartesian → pairwise KS transform."""
    pairwise_state = cartesian_3bp_to_pairwise_ks(simple_cartesian_state)

    # Verify types
    assert isinstance(pairwise_state, PairwiseSpinorState)

    # Verify spinors are 4D
    assert pairwise_state.u12.to_array().shape == (4,)
    assert pairwise_state.u23.to_array().shape == (4,)
    assert pairwise_state.u31.to_array().shape == (4,)


def test_pairwise_ks_to_cartesian(simple_cartesian_state, equal_masses):
    """Test inverse pairwise KS → 3BP Cartesian transform."""
    # Forward transform
    pairwise_state = cartesian_3bp_to_pairwise_ks(simple_cartesian_state)

    # Inverse transform
    cart_reconstructed = pairwise_ks_to_cartesian_3bp(pairwise_state, equal_masses)

    # Verify types
    assert isinstance(cart_reconstructed, CartesianState)

    # Positions should match (up to numerical error)
    np.testing.assert_allclose(
        cart_reconstructed.r1,
        simple_cartesian_state.r1,
        atol=1e-8
    )
    np.testing.assert_allclose(
        cart_reconstructed.r2,
        simple_cartesian_state.r2,
        atol=1e-8
    )
    np.testing.assert_allclose(
        cart_reconstructed.r3,
        simple_cartesian_state.r3,
        atol=1e-8
    )


def test_pairwise_roundtrip(simple_cartesian_state, equal_masses):
    """Test full Cartesian → pairwise KS → Cartesian roundtrip."""
    results = validate_pairwise_roundtrip(
        simple_cartesian_state,
        equal_masses,
        tolerance=1e-8
    )

    assert results['roundtrip_success'], \
        f"Roundtrip failed: max position error = {results['max_position_error']}"
    assert results['constraints_satisfied'], \
        "Constraints not satisfied"


def test_constraint_validation(simple_cartesian_state):
    """Test constraint validation on pairwise state."""
    pairwise_state = cartesian_3bp_to_pairwise_ks(simple_cartesian_state)

    # Validate constraints
    validation = pairwise_state.validate_constraints(tolerance=1e-10)

    # All bilinear relations should be satisfied
    assert validation['bilinear_12'], "Bilinear relation for (1,2) failed"
    assert validation['bilinear_23'], "Bilinear relation for (2,3) failed"
    assert validation['bilinear_31'], "Bilinear relation for (3,1) failed"

    # Closure constraint should be satisfied
    assert validation['closure_satisfied'], \
        f"Closure constraint failed: error = {validation['closure_error']}"

    # All constraints satisfied
    assert validation['all_satisfied']


def test_closure_constraint_explicit():
    """Test explicit closure constraint: r12 + r23 + r31 = 0."""
    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([0.0, 1.0, 0.0])
    r3 = np.array([0.0, 0.0, 1.0])

    v1 = v2 = v3 = np.zeros(3)

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)

    # Transform
    pairwise_state = cartesian_3bp_to_pairwise_ks(cart_state)

    # Get Cartesian separations
    r12, r23, r31 = pairwise_state.to_cartesian()

    # Check closure
    closure_residual = r12 + r23 + r31
    assert np.linalg.norm(closure_residual) < 1e-10, \
        f"Closure violated: r12 + r23 + r31 = {closure_residual}"


def test_constraint_manifold_dimension():
    """Test constraint manifold dimension calculation."""
    dim_info = compute_constraint_manifold_dimension()

    # Verify dimensions
    assert dim_info['full_phase_space_dim'] == 24
    assert dim_info['total_constraints'] == 6
    assert dim_info['constrained_phase_space_dim'] == 18
    assert dim_info['configuration_space_dim'] == 12
    assert dim_info['constrained_configuration_dim'] == 9


def test_pairwise_roundtrip_collinear():
    """Test roundtrip for collinear configuration."""
    # Collinear configuration
    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([0.0, 0.0, 0.0])
    r3 = np.array([-1.0, 0.0, 0.0])

    v1 = np.array([0.0, 0.1, 0.0])
    v2 = np.array([0.0, 0.0, 0.0])
    v3 = np.array([0.0, -0.1, 0.0])

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)
    masses = Masses(m1=1.0, m2=1.0, m3=1.0)

    # Roundtrip
    results = validate_pairwise_roundtrip(cart_state, masses, tolerance=1e-8)

    assert results['roundtrip_success'], \
        f"Collinear roundtrip failed: {results['max_position_error']}"


def test_pairwise_zero_velocity():
    """Test pairwise transform with zero velocities."""
    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([0.0, 1.0, 0.0])
    r3 = np.array([0.0, 0.0, 1.0])

    v1 = v2 = v3 = np.zeros(3)

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)

    # Transform
    pairwise_state = cartesian_3bp_to_pairwise_ks(cart_state)

    # All u_prime should be small
    assert pairwise_state.u12_prime.norm_squared < 1e-10
    assert pairwise_state.u23_prime.norm_squared < 1e-10
    assert pairwise_state.u31_prime.norm_squared < 1e-10


def test_bilinear_relations_preserved():
    """Test that bilinear relations are preserved through transform."""
    r1 = np.array([2.0, 1.0, 0.5])
    r2 = np.array([-1.0, 0.5, -0.3])
    r3 = np.array([0.0, -1.5, 0.8])

    v1 = np.array([0.1, 0.2, 0.3])
    v2 = np.array([-0.1, 0.1, 0.0])
    v3 = np.array([0.0, -0.3, -0.3])

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)

    # Transform
    pairwise_state = cartesian_3bp_to_pairwise_ks(cart_state)

    # Get pairwise separations
    r12_ks, r23_ks, r31_ks = pairwise_state.to_cartesian()

    # Compute expected separations
    r12_expected = r1 - r2
    r23_expected = r2 - r3
    r31_expected = r3 - r1

    # Check bilinear relations
    np.testing.assert_allclose(r12_ks, r12_expected, atol=1e-10)
    np.testing.assert_allclose(r23_ks, r23_expected, atol=1e-10)
    np.testing.assert_allclose(r31_ks, r31_expected, atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
