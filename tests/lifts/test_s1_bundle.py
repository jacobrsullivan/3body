"""
Tests for S¹ bundle data structures (WP 2.2, Part A).
"""

import numpy as np
from src.python.lifts.s1_bundle import (
    BundleState,
    S1Bundle,
    BundleChart,
    create_bundle_state,
    project_to_base,
    create_trivial_chart,
)
from src.python.coordinates.base import Masses
from src.python.coordinates.shape_space import ShapeSpaceState


def test_bundle_state_creation():
    """Test creating bundle states"""
    state = create_bundle_state(
        r12=1.0, r23=1.0, r31=1.0,
        theta=np.pi / 4,
        p_r12=0.1, p_r23=0.2, p_r31=0.3,
        p_theta=0.5,
        L=1.0
    )

    assert state.shape_state.r12 == 1.0
    assert state.shape_state.r23 == 1.0
    assert state.shape_state.r31 == 1.0
    assert abs(state.theta - np.pi / 4) < 1e-14
    assert state.p_theta == 0.5
    assert len(state.shape_momenta) == 3


def test_theta_normalization():
    """Test that theta is normalized to [0, 2π)"""
    state = create_bundle_state(
        r12=1.0, r23=1.0, r31=1.0,
        theta=3 * np.pi,  # > 2π
        L=1.0
    )

    assert 0 <= state.theta < 2 * np.pi
    assert abs(state.theta - np.pi) < 1e-10  # Should wrap to π


def test_bundle_projection():
    """Test projection π: P → S"""
    masses = Masses(1.0, 1.0, 1.0)
    bundle = S1Bundle(masses)

    state = create_bundle_state(
        r12=1.0, r23=1.2, r31=1.4,
        theta=1.5,
        p_theta=0.7,
        L=1.0
    )

    projected = bundle.project_to_base(state)

    # Projection should drop fiber coordinates
    assert projected.r12 == state.shape_state.r12
    assert projected.r23 == state.shape_state.r23
    assert projected.r31 == state.shape_state.r31


def test_lift_from_base():
    """Test lifting shape space state to bundle"""
    masses = Masses(1.0, 1.0, 1.0)
    bundle = S1Bundle(masses)

    shape_state = ShapeSpaceState(
        r12=1.0, r23=1.2, r31=1.4,
        dr12_dt=0, dr23_dt=0, dr31_dt=0,
        L=1.0,
        dimension=2
    )

    # Lift with specific theta
    lifted = bundle.lift_from_base(shape_state, theta=np.pi/3)

    assert lifted.shape_state.r12 == shape_state.r12
    assert lifted.shape_state.r23 == shape_state.r23
    assert abs(lifted.theta - np.pi/3) < 1e-14


def test_fiber_over_point():
    """Test that fiber π⁻¹(s) is a circle"""
    masses = Masses(1.0, 1.0, 1.0)
    bundle = S1Bundle(masses)

    shape_state = ShapeSpaceState(
        r12=1.0, r23=1.0, r31=1.0,
        dr12_dt=0, dr23_dt=0, dr31_dt=0,
        L=1.0,
        dimension=2
    )

    fiber = bundle.fiber_over_point(shape_state, n_points=100)

    # All points should project to same base
    for state in fiber:
        projected = bundle.project_to_base(state)
        assert abs(projected.r12 - shape_state.r12) < 1e-12
        assert abs(projected.r23 - shape_state.r23) < 1e-12

    # Theta values should cover [0, 2π)
    theta_values = [s.theta for s in fiber]
    assert min(theta_values) >= 0
    assert max(theta_values) < 2 * np.pi


def test_bundle_dimensions():
    """Test bundle dimensions"""
    masses = Masses(1.0, 1.0, 1.0)
    bundle = S1Bundle(masses)

    assert bundle.base_dimension == 3  # Shape space
    assert bundle.fiber_dimension == 1  # S¹
    assert bundle.total_dimension == 4  # S × S¹


def test_vector_conversion():
    """Test to_vector and from_vector"""
    state = create_bundle_state(
        r12=1.0, r23=1.2, r31=1.4,
        theta=1.5,
        p_r12=0.1, p_r23=0.2, p_r31=0.3,
        p_theta=0.5,
        L=1.0
    )

    # Convert to vector
    z = state.to_vector()
    assert len(z) == 8

    # Convert back
    state_reconstructed = BundleState.from_vector(z, L=1.0)

    assert abs(state_reconstructed.shape_state.r12 - state.shape_state.r12) < 1e-12
    assert abs(state_reconstructed.theta - state.theta) < 1e-12
    assert np.allclose(state_reconstructed.shape_momenta, state.shape_momenta)
    assert abs(state_reconstructed.p_theta - state.p_theta) < 1e-12


if __name__ == "__main__":
    test_bundle_state_creation()
    test_theta_normalization()
    test_bundle_projection()
    test_lift_from_base()
    test_fiber_over_point()
    test_bundle_dimensions()
    test_vector_conversion()
    print("All S¹ bundle tests passed!")
