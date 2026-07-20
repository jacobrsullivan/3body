"""Tests for WP3 v2 normalization and invariant features."""

from __future__ import annotations

import numpy as np

from src.python.n3bp_qualification import InertialState, SystemParameters
from src.python.wp3_exploration_v2 import (
    evaluate_feature_library,
    feature_names,
    known_algebra_coefficients,
    nondimensionalize,
)


def _case() -> tuple[InertialState, SystemParameters, float]:
    parameters = SystemParameters([0.7, 1.1, 1.6], gravitational_constant=0.9)
    positions = np.array(
        [[-0.8, 0.2, 0.4], [0.9, -0.4, 0.1], [0.3, 1.2, -0.7]]
    )
    velocities = np.array(
        [[0.4, -0.3, 0.8], [-0.7, 0.2, -0.1], [0.1, 0.6, -0.5]]
    )
    length = max(
        np.linalg.norm(positions[first] - positions[second])
        for first, second in ((0, 1), (0, 2), (1, 2))
    )
    return InertialState.from_components(positions, velocities), parameters, length


def test_nondimensionalization_is_newtonian_similarity_invariant() -> None:
    state, parameters, length = _case()
    reference = nondimensionalize(state, parameters, length_scale=length)
    length_factor = 3.7
    mass_factor = 2.3
    velocity_factor = np.sqrt(mass_factor / length_factor)
    scaled = InertialState.from_components(
        state.positions * length_factor,
        state.velocities * velocity_factor,
    )
    scaled_parameters = SystemParameters(
        parameters.masses * mass_factor,
        gravitational_constant=parameters.gravitational_constant,
    )
    comparison = nondimensionalize(
        scaled,
        scaled_parameters,
        length_scale=length * length_factor,
    )
    np.testing.assert_allclose(comparison.state, reference.state, atol=3e-15)
    np.testing.assert_allclose(
        comparison.derivative, reference.derivative, atol=2e-14
    )


def test_feature_library_is_so3_invariant_and_retains_parity() -> None:
    state, parameters, length = _case()
    system = nondimensionalize(state, parameters, length_scale=length)
    reference = evaluate_feature_library(
        system.state, system.derivative, system.parameters
    )
    angle = 0.73
    rotation = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    rotated_state = (system.state.reshape(4, 3) @ rotation.T).ravel()
    rotated_derivative = (system.derivative.reshape(4, 3) @ rotation.T).ravel()
    rotated = evaluate_feature_library(
        rotated_state, rotated_derivative, system.parameters
    )
    np.testing.assert_allclose(rotated.values, reference.values, atol=2e-14)
    np.testing.assert_allclose(
        rotated.lie_derivatives, reference.lie_derivatives, atol=4e-14
    )

    reflection = np.diag([-1.0, 1.0, 1.0])
    reflected = evaluate_feature_library(
        (system.state.reshape(4, 3) @ reflection).ravel(),
        (system.derivative.reshape(4, 3) @ reflection).ravel(),
        system.parameters,
    )
    names = feature_names()
    triple_indices = [
        index
        for index, name in enumerate(names)
        if name.startswith("1:triple(") and "*" not in name
    ]
    assert triple_indices
    np.testing.assert_allclose(
        reflected.values[triple_indices], -reference.values[triple_indices]
    )


def test_exact_feature_lie_derivatives_match_directional_difference() -> None:
    state, parameters, length = _case()
    system = nondimensionalize(state, parameters, length_scale=length)
    evaluation = evaluate_feature_library(
        system.state, system.derivative, system.parameters
    )
    step = 2e-7
    plus = evaluate_feature_library(
        system.state + step * system.derivative,
        system.derivative,
        system.parameters,
    )
    minus = evaluate_feature_library(
        system.state - step * system.derivative,
        system.derivative,
        system.parameters,
    )
    finite = (plus.values - minus.values) / (2.0 * step)
    np.testing.assert_allclose(
        evaluation.lie_derivatives, finite, rtol=3e-7, atol=2e-8
    )


def test_known_integral_algebra_has_zero_lie_derivative() -> None:
    state, parameters, length = _case()
    system = nondimensionalize(state, parameters, length_scale=length)
    evaluation = evaluate_feature_library(
        system.state, system.derivative, system.parameters
    )
    controls = known_algebra_coefficients()
    assert len(controls) == 12
    for name, coefficients in controls.items():
        residual = float(np.dot(evaluation.lie_derivatives, coefficients))
        assert abs(residual) < 2e-13, (name, residual)
