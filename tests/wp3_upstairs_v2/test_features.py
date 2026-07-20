from __future__ import annotations

import numpy as np
import pytest

from src.python.n3bp_qualification import figure_eight_choreography
from src.python.threebody_reduction import JacobiPhaseState
from src.python.upstairs_ks import lift_jacobi_state, upstairs_vector_field
from src.python.wp3_upstairs_v2 import (
    evaluate_upstairs_v2_features, feature_descriptors, feature_names,
    known_control_coefficients,
)


def _case():
    orbit=figure_eight_choreography()
    jacobi=JacobiPhaseState.from_inertial(orbit.initial_state,orbit.parameters).quotient.as_canonical_vector()
    shell=lift_jacobi_state(jacobi,orbit.parameters,angle=.41)
    flow=upstairs_vector_field(shell.state,orbit.parameters,shell.energy)
    evaluation=evaluate_upstairs_v2_features(shell.state,flow.derivative,orbit.parameters,fixed_energy=shell.energy)
    return orbit,shell,flow,evaluation


def test_complete_parameter_aware_grammar_size() -> None:
    assert len(feature_descriptors()) == 1120
    assert len(feature_names()) == 1126
    assert len(set(feature_names())) == 1126


def test_feature_lie_derivatives_match_directional_difference() -> None:
    orbit,shell,flow,evaluation=_case(); step=1e-7
    plus=type(shell.state).from_vector(shell.state.as_vector()+step*flow.derivative)
    minus=type(shell.state).from_vector(shell.state.as_vector()-step*flow.derivative)
    plus_eval=evaluate_upstairs_v2_features(plus,flow.derivative,orbit.parameters,fixed_energy=shell.energy)
    minus_eval=evaluate_upstairs_v2_features(minus,flow.derivative,orbit.parameters,fixed_energy=shell.energy)
    finite=(plus_eval.values[:1120]-minus_eval.values[:1120])/(2*step)
    assert evaluation.lie_derivatives[:1120] == pytest.approx(finite,abs=3e-8,rel=3e-8)


def test_known_controls_are_evaluated_and_conserved() -> None:
    _,_,_,evaluation=_case()
    assert np.max(np.abs(evaluation.lie_derivatives[-6:])) < 3e-13
    assert set(known_control_coefficients()) == {"H","H2","Lx","Ly","Lz","L2"}
