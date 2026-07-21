from __future__ import annotations

import numpy as np

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    angular_momentum,
)
from src.python.wp1_catalogue_n3bp_v1 import canonical_section_state
from src.python.wp2_multi_v1 import (
    lift_inertial_state,
    project_state,
    torus_action,
    vector_field,
)
from src.python.wp3_multi_v1 import (
    evaluate_multi_features,
    feature_descriptors,
    feature_names,
    known_module_coefficients,
    multi_state_vector,
    multi_tangent_vector,
    torus_generators,
)


CHARTS = ("central-1", "central-2", "central-3")


def _physical_state() -> tuple[InertialState, SystemParameters]:
    state = InertialState(
        canonical_section_state(
            1.02,
            0.98,
            -0.371,
            1.217,
            0.451,
            7.54,
        )
    )
    return state, SystemParameters([1.02, 0.98, 1.0])


def test_complete_shared_degree_three_grammar() -> None:
    assert len(feature_descriptors()) == 1520
    assert len(feature_names()) == 1520
    assert len(set(feature_names())) == 1520
    assert all(1 <= len(state) <= 3 for state, _ in feature_descriptors())
    assert all(len(state) + len(parameters) <= 3 for state, parameters in feature_descriptors())


def test_exact_known_module_has_declared_rank() -> None:
    known = known_module_coefficients()
    matrix = np.column_stack(list(known.values()))
    assert len(known) == 52
    assert sum(name.startswith("constraint:") for name in known) == 40
    assert sum(name.startswith("known:") for name in known) == 12
    assert np.linalg.matrix_rank(matrix, tol=1e-12) == 52


def test_torus_generators_match_finite_actions() -> None:
    physical, parameters = _physical_state()
    state = lift_inertial_state(physical, parameters, "central-2", angles=(0.2, -0.4))
    generators = torus_generators(state)
    epsilon = 2e-7
    for index in range(2):
        angles_plus = [0.0, 0.0]
        angles_minus = [0.0, 0.0]
        angles_plus[index] = epsilon
        angles_minus[index] = -epsilon
        finite = (
            multi_state_vector(torus_action(state, angles_plus))
            - multi_state_vector(torus_action(state, angles_minus))
        ) / (2.0 * epsilon)
        assert np.max(np.abs(finite - generators[index])) < 2e-9


def test_known_module_vanishes_or_is_conserved_and_chart_independent() -> None:
    physical, parameters = _physical_state()
    expected_angular = angular_momentum(physical, parameters)
    known = known_module_coefficients()
    angular_values = []
    for chart in CHARTS:
        state = lift_inertial_state(
            physical,
            parameters,
            chart,
            angles=(0.37, -0.82),
        )
        flow = vector_field(state, parameters)
        evaluation = evaluate_multi_features(
            state,
            multi_tangent_vector(flow.derivative),
            parameters,
            fixed_energy=state.energy,
        )
        gauge_evaluations = [
            evaluate_multi_features(
                state,
                generator,
                parameters,
                fixed_energy=state.energy,
            )
            for generator in torus_generators(state)
        ]
        constraint_values = [
            abs(float(evaluation.values @ coefficients))
            for name, coefficients in known.items()
            if name.startswith("constraint:")
        ]
        assert max(constraint_values) < 2e-14
        for name, coefficients in known.items():
            scale = max(np.linalg.norm(coefficients), 1.0)
            assert abs(float(evaluation.derivatives @ coefficients)) < 2e-12 * scale
            assert max(
                abs(float(item.derivatives @ coefficients))
                for item in gauge_evaluations
            ) < 2e-12 * scale
        angular_values.append(
            np.array(
                [
                    evaluation.values @ known["known:Lx"],
                    evaluation.values @ known["known:Ly"],
                    evaluation.values @ known["known:Lz"],
                ]
            )
        )
        projected = project_state(state, parameters)
        assert np.max(np.abs(projected.as_vector() - physical.as_vector())) < 2e-14
    assert np.max(np.abs(np.stack(angular_values) - expected_angular)) < 3e-14
