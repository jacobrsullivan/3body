"""Exactness tests for the WP3 upstairs feature grammar."""

from __future__ import annotations

import numpy as np
import pytest

from src.python.n3bp_qualification import figure_eight_choreography
from src.python.threebody_reduction import JacobiPhaseState
from src.python.upstairs_ks import lift_jacobi_state, s1_action, upstairs_vector_field
from src.python.wp3_upstairs import (
    evaluate_upstairs_features,
    feature_names,
    known_control_coefficients,
    monomial_indices,
)


def _evaluation(angle: float = 0.23):
    orbit = figure_eight_choreography()
    jacobi = JacobiPhaseState.from_inertial(
        orbit.initial_state, orbit.parameters
    ).quotient.as_canonical_vector()
    shell = lift_jacobi_state(jacobi, orbit.parameters, angle=angle)
    flow = upstairs_vector_field(shell.state, orbit.parameters, shell.energy)
    return shell, flow, evaluate_upstairs_features(
        shell.state, flow.derivative, physical_energy=shell.energy
    )


def test_degree_three_grammar_has_expected_size_and_unique_names() -> None:
    assert len(monomial_indices()) == 679
    assert len(feature_names()) == 685
    assert len(set(feature_names())) == 685


def test_monomial_lie_derivatives_match_directional_finite_difference() -> None:
    shell, flow, evaluation = _evaluation()
    step = 1e-7
    plus_state = type(shell.state).from_vector(shell.state.as_vector() + step * flow.derivative)
    minus_state = type(shell.state).from_vector(shell.state.as_vector() - step * flow.derivative)
    plus = evaluate_upstairs_features(plus_state, flow.derivative, physical_energy=shell.energy)
    minus = evaluate_upstairs_features(minus_state, flow.derivative, physical_energy=shell.energy)
    finite = (plus.values[:679] - minus.values[:679]) / (2.0 * step)
    assert evaluation.lie_derivatives[:679] == pytest.approx(finite, abs=2e-8, rel=2e-8)


def test_known_controls_are_exact_and_gauge_invariant() -> None:
    shell, flow, evaluation = _evaluation()
    transformed = s1_action(shell.state, 1.17)
    transformed_flow = upstairs_vector_field(transformed, flow_parameters(), shell.energy)
    other = evaluate_upstairs_features(
        transformed, transformed_flow.derivative, physical_energy=shell.energy
    )
    assert evaluation.values[-6:] == pytest.approx(other.values[-6:], abs=3e-13)
    assert evaluation.lie_derivatives[-6:] == pytest.approx(np.zeros(6), abs=2e-13)
    controls = known_control_coefficients()
    assert set(controls) == {"H", "H2", "Lx", "Ly", "Lz", "L2"}
    assert all(np.count_nonzero(vector) == 1 for vector in controls.values())


def flow_parameters():
    return figure_eight_choreography().parameters
