"""
Test suite for integral conversion and filtering (WP 3.1, Task 3.1.4).

Tests:
- Killing vector to integral conversion
- Killing tensor to integral conversion
- Gradient computation
- Batch conversion
"""

import pytest
import numpy as np
from scipy.spatial import cKDTree

from src.python.analysis.integral_from_killing import (
    ConservedIntegral,
    State,
    killing_vector_to_integral,
    killing_tensor_to_integral,
    convert_killing_fields_batch
)
from src.python.pde.mesh_generation import Mesh


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def simple_2d_mesh():
    """Create a simple 2D mesh for testing"""
    # Regular grid in 2D
    x = np.linspace(-1, 1, 10)
    y = np.linspace(-1, 1, 10)
    xx, yy = np.meshgrid(x, y)
    points = np.column_stack([xx.ravel(), yy.ravel()])

    N = len(points)
    volumes = np.ones(N) * 0.04  # Uniform volume elements

    # Build k-NN connectivity
    tree = cKDTree(points)
    neighbor_indices = []
    for i in range(N):
        _, indices = tree.query(points[i], k=9)
        neighbor_indices.append(indices[1:].tolist())

    boundary_mask = np.zeros(N, dtype=bool)
    # Mark boundary points
    boundary_mask[xx.ravel() == -1] = True
    boundary_mask[xx.ravel() == 1] = True
    boundary_mask[yy.ravel() == -1] = True
    boundary_mask[yy.ravel() == 1] = True

    return Mesh(
        points=points,
        volumes=volumes,
        neighbor_indices=neighbor_indices,
        boundary_mask=boundary_mask,
        dimension=2
    )


@pytest.fixture
def flat_metric_2d():
    """Flat metric in 2D"""
    def metric(q):
        return np.eye(2)
    return metric


@pytest.fixture
def constant_killing_field_2d(simple_2d_mesh):
    """Constant Killing vector field (translation)"""
    N = simple_2d_mesh.num_points
    # K = ∂_x (constant vector field in x-direction)
    K = np.zeros(2 * N)
    K[0::2] = 1.0  # K_x = 1 at all points
    K[1::2] = 0.0  # K_y = 0 at all points
    return K


# =============================================================================
# Test Integral Conversion
# =============================================================================

def test_state_creation():
    """Test State dataclass"""
    q = np.array([1.0, 2.0])
    p = np.array([3.0, 4.0])

    state = State(q=q, p=p)

    assert state.dimension == 2
    assert np.allclose(state.q, q)
    assert np.allclose(state.p, p)

    # Test array conversion
    arr = state.to_array()
    assert len(arr) == 4
    assert np.allclose(arr[:2], q)
    assert np.allclose(arr[2:], p)

    # Test from_array
    state2 = State.from_array(arr)
    assert np.allclose(state2.q, q)
    assert np.allclose(state2.p, p)


def test_killing_vector_to_integral_constant_field(simple_2d_mesh, flat_metric_2d, constant_killing_field_2d):
    """Test conversion of constant Killing vector (translation)"""
    integral = killing_vector_to_integral(
        constant_killing_field_2d,
        simple_2d_mesh,
        flat_metric_2d,
        interpolation_method='linear'
    )

    assert isinstance(integral, ConservedIntegral)
    assert integral.source == 'killing_vector'

    # For constant K = (1, 0) and flat metric, I = K · v = v_x
    state = State(q=np.array([0.5, 0.5]), p=np.array([2.0, 3.0]))
    I_val = integral(state.to_array())

    # Should be approximately p_x = 2.0
    assert abs(I_val - 2.0) < 0.5  # Allow interpolation error


def test_killing_vector_gradient(simple_2d_mesh, flat_metric_2d, constant_killing_field_2d):
    """Test gradient computation"""
    integral = killing_vector_to_integral(
        constant_killing_field_2d,
        simple_2d_mesh,
        flat_metric_2d
    )

    state = State(q=np.array([0.0, 0.0]), p=np.array([1.0, 1.0]))

    if integral.gradient is not None:
        dI_dq, dI_dp = integral.gradient(state.to_array())

        assert len(dI_dq) == 2
        assert len(dI_dp) == 2

        # For I = v_x, ∂I/∂p_x should be ~1, others ~0
        assert abs(dI_dp[0] - 1.0) < 0.5


def test_killing_tensor_to_integral(simple_2d_mesh, flat_metric_2d):
    """Test Killing tensor conversion"""
    N = simple_2d_mesh.num_points
    n = 2
    n_components = n * (n + 1) // 2  # = 3 for 2D

    # Create simple diagonal Killing tensor: T = diag(1, 1)
    T_field = np.zeros(n_components * N)
    # Components: T_00, T_01, T_11
    T_field[0::3] = 1.0  # T_00 = 1
    T_field[1::3] = 0.0  # T_01 = 0
    T_field[2::3] = 1.0  # T_11 = 1

    integral = killing_tensor_to_integral(
        T_field,
        simple_2d_mesh,
        flat_metric_2d,
        interpolation_method='linear'
    )

    assert isinstance(integral, ConservedIntegral)
    assert integral.source == 'killing_tensor'

    # For T = I (identity), I_T = v^T v = |v|²
    state = State(q=np.array([0.0, 0.0]), p=np.array([3.0, 4.0]))
    I_val = integral(state.to_array())

    expected = 3.0**2 + 4.0**2  # = 25
    assert abs(I_val - expected) < 5.0  # Allow interpolation error


def test_batch_conversion(simple_2d_mesh, flat_metric_2d):
    """Test batch conversion of multiple Killing fields"""
    N = simple_2d_mesh.num_points

    # Create two Killing vectors
    K1 = np.zeros(2 * N)
    K1[0::2] = 1.0  # ∂_x

    K2 = np.zeros(2 * N)
    K2[1::2] = 1.0  # ∂_y

    killing_fields = [K1, K2]

    integrals = convert_killing_fields_batch(
        killing_fields,
        simple_2d_mesh,
        flat_metric_2d,
        field_type='vector',
        names=['I_x', 'I_y']
    )

    assert len(integrals) == 2
    assert integrals[0].name == 'I_x'
    assert integrals[1].name == 'I_y'

    # Both should be ConservedIntegral
    for I in integrals:
        assert isinstance(I, ConservedIntegral)


# =============================================================================
# Test Edge Cases
# =============================================================================

def test_integral_at_different_states(simple_2d_mesh, flat_metric_2d, constant_killing_field_2d):
    """Test integral evaluation at multiple states"""
    integral = killing_vector_to_integral(
        constant_killing_field_2d,
        simple_2d_mesh,
        flat_metric_2d
    )

    states = [
        State(q=np.array([0.0, 0.0]), p=np.array([1.0, 0.0])),
        State(q=np.array([0.5, 0.5]), p=np.array([2.0, 3.0])),
        State(q=np.array([-0.5, 0.3]), p=np.array([-1.0, 2.0]))
    ]

    for state in states:
        val = integral(state.to_array())
        assert np.isfinite(val)


def test_zero_killing_field(simple_2d_mesh, flat_metric_2d):
    """Test conversion of zero Killing field"""
    N = simple_2d_mesh.num_points
    K_zero = np.zeros(2 * N)

    integral = killing_vector_to_integral(
        K_zero,
        simple_2d_mesh,
        flat_metric_2d
    )

    state = State(q=np.array([0.0, 0.0]), p=np.array([1.0, 1.0]))
    val = integral(state.to_array())

    # Should be close to zero
    assert abs(val) < 1e-3


# =============================================================================
# Test ConservedIntegral Properties
# =============================================================================

def test_conserved_integral_metadata():
    """Test metadata storage"""
    def dummy_expr(state):
        return np.sum(state)

    integral = ConservedIntegral(
        name="TestIntegral",
        expression=dummy_expr,
        source='known',
        manifold_type='s1_bundle',
        metadata={'test_key': 'test_value'}
    )

    assert integral.name == "TestIntegral"
    assert integral.source == 'known'
    assert integral.manifold_type == 's1_bundle'
    assert integral.metadata['test_key'] == 'test_value'

    # Test callable
    state = np.array([1.0, 2.0, 3.0, 4.0])
    val = integral(state)
    assert val == 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
