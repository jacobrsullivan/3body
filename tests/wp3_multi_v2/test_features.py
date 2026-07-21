from __future__ import annotations

import numpy as np

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    angular_momentum,
    total_energy,
)
from src.python.wp1_catalogue_n3bp_v1 import canonical_section_state
from src.python.wp2_multi_v1 import (
    lift_inertial_state,
    project_derivative,
    project_state,
    vector_field,
)
from src.python.wp3_multi_v2 import (
    BODY_PERMUTATIONS,
    angular_momentum_squared_coefficients,
    evaluate_multi_features,
    feature_descriptors,
    feature_names,
    known_module_coefficients,
    permute_physical_inputs,
    structural_zero_feature_indices,
)


CHARTS = ("central-1", "central-2", "central-3")
ANGLES = ((0.0, 0.0), (0.61, -1.17), (-1.17, 0.61))


def _physical_flow() -> tuple[InertialState, np.ndarray, SystemParameters, float]:
    state = InertialState(
        canonical_section_state(1.02, 0.98, -0.371, 1.217, 0.451, 7.54)
    )
    parameters = SystemParameters([1.02, 0.98, 1.0])
    fixed_energy = total_energy(state, parameters)
    lifted = lift_inertial_state(
        state,
        parameters,
        "central-2",
        angles=(0.37, -0.82),
        p_t=-fixed_energy,
    )
    tangent = project_derivative(vector_field(lifted, parameters), parameters)
    return state, tangent, parameters, fixed_energy


def test_frozen_feature_count_and_exact_reynolds_zero_identities() -> None:
    descriptors = feature_descriptors()
    assert len(descriptors) == 285
    assert len(feature_names()) == 285
    assert len(set(feature_names())) == 285
    assert len(structural_zero_feature_indices()) == 36
    assert sum(descriptor[0] == 0 for descriptor in descriptors) == 95
    assert sum(descriptor[0] == 1 for descriptor in descriptors) == 95
    assert sum(descriptor[0] == 2 for descriptor in descriptors) == 95

    state, tangent, parameters, fixed_energy = _physical_flow()
    evaluation = evaluate_multi_features(
        state, tangent, parameters, fixed_energy=fixed_energy
    )
    zeros = np.asarray(structural_zero_feature_indices())
    assert np.array_equal(evaluation.values[zeros], np.zeros(len(zeros)))
    assert np.array_equal(evaluation.derivatives[zeros], np.zeros(len(zeros)))


def test_analytic_tangent_derivative_matches_centered_finite_difference() -> None:
    state, tangent, parameters, fixed_energy = _physical_flow()
    evaluation = evaluate_multi_features(
        state, tangent, parameters, fixed_energy=fixed_energy
    )
    epsilon = 2e-7
    plus = InertialState(state.as_vector() + epsilon * tangent)
    minus = InertialState(state.as_vector() - epsilon * tangent)
    zero_tangent = np.zeros(18)
    plus_values = evaluate_multi_features(
        plus, zero_tangent, parameters, fixed_energy=fixed_energy
    ).values
    minus_values = evaluate_multi_features(
        minus, zero_tangent, parameters, fixed_energy=fixed_energy
    ).values
    finite = (plus_values - minus_values) / (2.0 * epsilon)
    active = np.setdiff1d(np.arange(285), structural_zero_feature_indices())
    scale = np.maximum(1.0, np.abs(evaluation.derivatives[active]))
    assert (
        np.max(np.abs(finite[active] - evaluation.derivatives[active]) / scale) < 2e-8
    )


def test_angular_momentum_squared_is_exact_known_module() -> None:
    state, tangent, parameters, fixed_energy = _physical_flow()
    evaluation = evaluate_multi_features(
        state, tangent, parameters, fixed_energy=fixed_energy
    )
    coefficients = angular_momentum_squared_coefficients()
    expected = angular_momentum(state, parameters)
    assert (
        abs(float(evaluation.values @ coefficients) - np.linalg.norm(expected) ** 2)
        < 8e-16
    )
    assert abs(float(evaluation.derivatives @ coefficients)) < 2e-13
    known = known_module_coefficients()
    assert tuple(known) == ("known:angular_momentum_squared",)
    assert np.linalg.matrix_rank(np.column_stack(list(known.values()))) == 1


def test_reynolds_library_is_body_permutation_and_rotation_invariant() -> None:
    state, tangent, parameters, fixed_energy = _physical_flow()
    reference = evaluate_multi_features(
        state, tangent, parameters, fixed_energy=fixed_energy
    )
    for permutation in BODY_PERMUTATIONS:
        permuted = permute_physical_inputs(state, tangent, parameters, permutation)
        evaluation = evaluate_multi_features(
            permuted[0], permuted[1], permuted[2], fixed_energy=fixed_energy
        )
        assert np.allclose(evaluation.values, reference.values, rtol=2e-15, atol=2e-14)
        assert np.allclose(
            evaluation.derivatives,
            reference.derivatives,
            rtol=3e-15,
            atol=3e-14,
        )

    rotation = np.asarray([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    rotated_state = InertialState.from_components(
        state.positions @ rotation.T,
        state.velocities @ rotation.T,
    )
    rotated_tangent = np.concatenate(
        (
            (tangent[:9].reshape(3, 3) @ rotation.T).ravel(),
            (tangent[9:].reshape(3, 3) @ rotation.T).ravel(),
        )
    )
    rotated = evaluate_multi_features(
        rotated_state, rotated_tangent, parameters, fixed_energy=fixed_energy
    )
    assert np.allclose(rotated.values, reference.values, rtol=2e-15, atol=2e-14)
    assert np.allclose(
        rotated.derivatives, reference.derivatives, rtol=3e-15, atol=3e-14
    )


def test_features_are_chart_and_gauge_independent_after_projection() -> None:
    state, _, parameters, fixed_energy = _physical_flow()
    evaluations = []
    for chart in CHARTS:
        for angles in ANGLES:
            lifted = lift_inertial_state(
                state, parameters, chart, angles=angles, p_t=-fixed_energy
            )
            flow = vector_field(lifted, parameters)
            projected = project_state(lifted, parameters)
            tangent = project_derivative(flow, parameters)
            assert np.max(np.abs(projected.as_vector() - state.as_vector())) < 3e-14
            evaluations.append(
                evaluate_multi_features(
                    projected, tangent, parameters, fixed_energy=fixed_energy
                )
            )
    reference = evaluations[0]
    for evaluation in evaluations[1:]:
        assert np.allclose(evaluation.values, reference.values, rtol=3e-14, atol=3e-13)
        assert np.allclose(
            evaluation.derivatives,
            reference.derivatives,
            rtol=4e-13,
            atol=4e-12,
        )
