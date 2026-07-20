from __future__ import annotations

import numpy as np
import pytest

from src.python.n3bp_qualification import figure_eight_choreography
from src.python.threebody_reduction import JacobiPhaseState
from src.python.upstairs_ks import angular_momentum, lift_jacobi_state, upstairs_vector_field
from src.python.wp3_upstairs_v3 import (
    evaluate_upstairs_v3_features,
    feature_descriptors,
    feature_names,
    known_module_coefficients,
    s1_generator,
)


def _case():
    orbit = figure_eight_choreography()
    jacobi = JacobiPhaseState.from_inertial(
        orbit.initial_state, orbit.parameters
    ).quotient.as_canonical_vector()
    shell = lift_jacobi_state(jacobi, orbit.parameters, angle=0.41)
    flow = upstairs_vector_field(shell.state, orbit.parameters, shell.energy)
    return orbit, shell, flow


def test_complete_parameter_aware_grammar_has_no_appended_controls() -> None:
    assert len(feature_descriptors()) == 1120
    assert len(feature_names()) == 1120
    assert len(set(feature_names())) == 1120


def test_feature_lie_derivatives_match_directional_difference() -> None:
    orbit, shell, flow = _case()
    evaluation = evaluate_upstairs_v3_features(
        shell.state, flow.derivative, orbit.parameters, fixed_energy=shell.energy
    )
    step = 1e-7
    plus = type(shell.state).from_vector(shell.state.as_vector() + step * flow.derivative)
    minus = type(shell.state).from_vector(shell.state.as_vector() - step * flow.derivative)
    plus_values = evaluate_upstairs_v3_features(
        plus, flow.derivative, orbit.parameters, fixed_energy=shell.energy
    ).values
    minus_values = evaluate_upstairs_v3_features(
        minus, flow.derivative, orbit.parameters, fixed_energy=shell.energy
    ).values
    finite = (plus_values - minus_values) / (2.0 * step)
    assert evaluation.lie_derivatives == pytest.approx(finite, abs=3e-8, rel=3e-8)


def test_exact_known_module_has_expected_rank_and_dynamics() -> None:
    orbit, shell, flow = _case()
    module = known_module_coefficients()
    assert len(module) == 30
    matrix = np.column_stack(tuple(module.values()))
    assert np.linalg.matrix_rank(matrix, tol=1e-12) == 30
    physical = evaluate_upstairs_v3_features(
        shell.state, flow.derivative, orbit.parameters, fixed_energy=shell.energy
    )
    gauge = evaluate_upstairs_v3_features(
        shell.state, s1_generator(shell.state), orbit.parameters, fixed_energy=shell.energy
    )
    for name, coefficients in module.items():
        assert abs(float(physical.lie_derivatives @ coefficients)) < 2e-12, name
        assert abs(float(gauge.lie_derivatives @ coefficients)) < 2e-12, name
        if name.startswith("constraint:"):
            assert abs(float(physical.values @ coefficients)) < 2e-12, name


def test_polynomial_angular_momenta_match_projected_values() -> None:
    orbit, shell, flow = _case()
    evaluation = evaluate_upstairs_v3_features(
        shell.state, flow.derivative, orbit.parameters, fixed_energy=shell.energy
    )
    module = known_module_coefficients()
    observed = np.asarray(
        [evaluation.values @ module[f"known:L{axis}"] for axis in "xyz"]
    )
    assert observed == pytest.approx(angular_momentum(shell.state), abs=2e-14)
