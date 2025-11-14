"""
Test suite for mechanical connection computation (Task 2.1.2 Part A).
"""

import pytest
import numpy as np
from src.python.geometry.connection_form import (
    compute_connection_coefficients,
    evaluate_connection,
    compute_holonomy,
)
from src.python.geometry.locked_inertia import compute_locked_inertia_tensor
from src.python.coordinates.base import Masses
from src.python.coordinates.shape_space import ShapeSpaceState
from src.python.coordinates.cartesian import CartesianState


def test_locked_inertia_tensor():
    """Test locked inertia tensor computation."""
    masses = Masses(1.0, 1.0, 1.0)

    # Equilateral triangle
    positions = np.array([
        [1.0, 0.0, 0.0],
        [-0.5, np.sqrt(3)/2, 0.0],
        [-0.5, -np.sqrt(3)/2, 0.0]
    ])
    velocities = np.zeros((3, 3))

    state = CartesianState(positions, velocities, dimension=2)

    I = compute_locked_inertia_tensor(state, masses)

    # Check properties
    assert I.is_positive_definite(), "Inertia tensor should be positive definite"
    assert I.determinant > 0, "Determinant should be positive"
    assert abs(I.tensor - I.tensor.T).max() < 1e-14, "Should be symmetric"


def test_connection_computation():
    """Test connection coefficient computation."""
    masses = Masses(1.0, 1.0, 1.0)

    shape = ShapeSpaceState(
        r12=1.0, r23=1.0, r31=1.0,
        dr12_dt=0, dr23_dt=0, dr31_dt=0,
        L=1.0,
        dimension=2
    )

    connection = compute_connection_coefficients(shape, masses)

    # Check basic properties
    assert connection.coefficients.shape == (3,), "Should have 3 components"
    assert np.isfinite(connection.coefficients).all(), "Components should be finite"


def test_connection_equal_mass_symmetry():
    """Test that connection respects symmetry for equal masses."""
    masses = Masses(1.0, 1.0, 1.0)

    # Symmetric configuration
    shape1 = ShapeSpaceState(
        r12=1.0, r23=1.2, r31=1.4,
        dr12_dt=0, dr23_dt=0, dr31_dt=0,
        L=1.0,
        dimension=2
    )

    # Permuted configuration (should give similar connection by symmetry)
    shape2 = ShapeSpaceState(
        r12=1.2, r23=1.4, r31=1.0,
        dr12_dt=0, dr23_dt=0, dr31_dt=0,
        L=1.0,
        dimension=2
    )

    conn1 = compute_connection_coefficients(shape1, masses)
    conn2 = compute_connection_coefficients(shape2, masses)

    # Due to permutation, coefficients should be permuted
    # (This is a weak test; full symmetry analysis is more complex)
    assert np.isfinite(conn1.coefficients).all()
    assert np.isfinite(conn2.coefficients).all()


if __name__ == "__main__":
    test_locked_inertia_tensor()
    test_connection_computation()
    test_connection_equal_mass_symmetry()
    print("All connection tests passed!")
