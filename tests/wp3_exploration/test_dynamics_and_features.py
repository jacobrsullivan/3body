"""Exactness and covariance checks for the WP3 Jacobi feature path."""

from __future__ import annotations

import numpy as np

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    angular_momentum,
    newtonian_rhs,
    normalize_center_of_mass,
    total_energy,
)
from src.python.threebody_reduction import JacobiPhaseState
from src.python.wp3_exploration import (
    evaluate_invariant_features,
    feature_dimensions,
    jacobi_vector_field,
    known_control_coefficients,
)


def _spatial_state() -> tuple[InertialState, SystemParameters]:
    parameters = SystemParameters([0.7, 1.1, 1.6], gravitational_constant=0.9)
    positions = np.array(
        [
            [-0.8, 0.2, 0.4],
            [0.9, -0.4, 0.1],
            [0.3, 1.2, -0.7],
        ]
    )
    velocities = np.array(
        [
            [0.4, -0.3, 0.8],
            [-0.7, 0.2, -0.1],
            [0.1, 0.6, -0.5],
        ]
    )
    state = normalize_center_of_mass(
        InertialState.from_components(positions, velocities), parameters
    )
    return state, parameters


def _proper_rotation(seed: int) -> np.ndarray:
    matrix = np.random.default_rng(seed).normal(size=(3, 3))
    rotation, _ = np.linalg.qr(matrix)
    if np.linalg.det(rotation) < 0.0:
        rotation[:, 0] *= -1.0
    return rotation


def test_jacobi_vector_field_is_tangent_map_of_full_rhs() -> None:
    state, parameters = _spatial_state()
    vector_field = jacobi_vector_field(state, parameters)
    full_derivative = newtonian_rhs(0.0, state.values, parameters)
    step = 1.0e-7
    plus = InertialState(state.values + step * full_derivative)
    minus = InertialState(state.values - step * full_derivative)
    plus_jacobi = JacobiPhaseState.from_inertial(plus, parameters)
    minus_jacobi = JacobiPhaseState.from_inertial(minus, parameters)
    finite_difference = (
        plus_jacobi.quotient.as_canonical_vector()
        - minus_jacobi.quotient.as_canonical_vector()
    ) / (2.0 * step)
    np.testing.assert_allclose(
        vector_field.derivative,
        finite_difference,
        rtol=2.0e-9,
        atol=2.0e-9,
    )


def test_feature_lie_derivatives_match_directional_finite_difference() -> None:
    state, parameters = _spatial_state()
    vector_field = jacobi_vector_field(state, parameters)
    evaluation = evaluate_invariant_features(
        vector_field.state, vector_field.derivative, parameters
    )
    step = 1.0e-7
    plus = evaluate_invariant_features(
        vector_field.state + step * vector_field.derivative,
        vector_field.derivative,
        parameters,
    )
    minus = evaluate_invariant_features(
        vector_field.state - step * vector_field.derivative,
        vector_field.derivative,
        parameters,
    )
    finite_difference = (plus.values - minus.values) / (2.0 * step)
    np.testing.assert_allclose(
        evaluation.lie_derivatives,
        finite_difference,
        rtol=2.0e-7,
        atol=2.0e-7,
    )


def test_energy_and_angular_momentum_squared_are_exact_controls() -> None:
    state, parameters = _spatial_state()
    vector_field = jacobi_vector_field(state, parameters)
    evaluation = evaluate_invariant_features(
        vector_field.state, vector_field.derivative, parameters
    )
    controls = known_control_coefficients()
    for coefficients in controls.values():
        assert abs(float(evaluation.lie_derivatives @ coefficients)) < 2.0e-12
    assert np.isclose(
        evaluation.values @ controls["energy"],
        total_energy(state, parameters),
        rtol=2.0e-15,
        atol=2.0e-15,
    )
    angular = angular_momentum(state, parameters)
    angular_squared = float(np.dot(angular, angular))
    assert np.isclose(
        evaluation.values @ controls["angular_momentum_squared"],
        angular_squared,
        rtol=2.0e-15,
        atol=2.0e-15,
    )


def test_each_known_control_is_dimensionally_homogeneous() -> None:
    dimensions = feature_dimensions()
    controls = known_control_coefficients()
    expected = {
        "energy": (1, 2, -2),
        "angular_momentum_squared": (2, 4, -2),
    }
    for name, coefficients in controls.items():
        support_dimensions = {
            dimensions[int(index)] for index in np.flatnonzero(coefficients)
        }
        assert support_dimensions == {expected[name]}


def test_feature_values_and_lie_derivatives_are_so3_invariant() -> None:
    state, parameters = _spatial_state()
    rotation = _proper_rotation(937)
    rotated = InertialState.from_components(
        state.positions @ rotation.T,
        state.velocities @ rotation.T,
    )
    original_field = jacobi_vector_field(state, parameters)
    rotated_field = jacobi_vector_field(rotated, parameters)
    original = evaluate_invariant_features(
        original_field.state, original_field.derivative, parameters
    )
    transformed = evaluate_invariant_features(
        rotated_field.state, rotated_field.derivative, parameters
    )
    np.testing.assert_allclose(original.values, transformed.values, atol=2.0e-12)
    np.testing.assert_allclose(
        original.lie_derivatives,
        transformed.lie_derivatives,
        atol=8.0e-12,
    )
