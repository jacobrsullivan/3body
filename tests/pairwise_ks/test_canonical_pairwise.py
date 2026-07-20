from __future__ import annotations

import numpy as np
import pytest

from src.python.ks import KeplerPhaseState, lift_cotangent
from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    figure_eight_choreography,
    lagrange_equilateral,
)
from src.python.pairwise_ks import (
    CanonicalPairwiseKSLift,
    lift_pairwise_ks,
    pairwise_dimension_accounting,
)


def _state() -> tuple[InertialState, SystemParameters]:
    positions = np.array([[0.2, -0.8, 0.4], [1.4, 0.3, -0.1], [-0.7, 0.9, 0.8]])
    velocities = np.array([[0.3, -0.1, 0.7], [-0.4, 0.6, -0.2], [0.5, 0.2, -0.3]])
    return (
        InertialState.from_components(positions, velocities),
        SystemParameters([0.6, 1.4, 2.3], gravitational_constant=0.72),
    )


@pytest.mark.parametrize("angles", [(0.0, 0.0, 0.0), (0.7, -1.2, 2.4)])
def test_full_state_roundtrip_for_arbitrary_gauges(angles: tuple[float, ...]) -> None:
    state, parameters = _state()
    result = lift_pairwise_ks(state, parameters, angles=angles)
    residuals = result.lift.constraint_residuals()
    assert residuals.momentum_map_max < 2e-15
    assert residuals.position_closure_norm < 3e-15
    assert residuals.velocity_closure_norm < 3e-15
    assert np.allclose(result.reconstruct().values, state.values, atol=5e-15, rtol=0.0)


def test_s1_cubed_action_preserves_all_physical_pair_states() -> None:
    state, parameters = _state()
    original = lift_pairwise_ks(state, parameters)
    transformed = original.lift.act_s1_cubed([0.4, -2.2, 1.1])
    for first, second in zip(
        original.lift.project_pairs(), transformed.project_pairs(), strict=True
    ):
        assert np.allclose(first.as_vector(), second.as_vector(), atol=3e-15, rtol=0.0)
    assert np.allclose(
        transformed.to_inertial(original.reconstruction).values,
        state.values,
        atol=6e-15,
        rtol=0.0,
    )


def test_pair_momenta_and_kepler_parameters_use_nonunit_masses() -> None:
    state, parameters = _state()
    result = lift_pairwise_ks(state, parameters)
    projected = result.lift.project_pairs()
    pair_indices = ((0, 1), (1, 2), (2, 0))
    for pair, physical, (first, second) in zip(
        result.lift.kepler_parameters, projected, pair_indices, strict=True
    ):
        expected_velocity = state.velocities[second] - state.velocities[first]
        assert np.allclose(
            physical.p,
            pair.reduced_mass * expected_velocity,
            atol=2e-15,
            rtol=0.0,
        )
        first_mass = parameters.masses[first]
        second_mass = parameters.masses[second]
        assert np.isclose(
            pair.kappa,
            parameters.gravitational_constant * first_mass * second_mass,
        )


def test_pairwise_lift_handles_qualified_collinear_and_lagrange_states() -> None:
    figure_eight = figure_eight_choreography()
    lagrange = lagrange_equilateral(side_length=1.7, mass=0.8)
    for orbit in (figure_eight, lagrange):
        result = lift_pairwise_ks(orbit.initial_state, orbit.parameters)
        assert np.allclose(
            result.reconstruct().values,
            orbit.initial_state.values,
            atol=8e-15,
            rtol=0.0,
        )


def test_broken_position_closure_is_rejected_on_reconstruction() -> None:
    state, parameters = _state()
    result = lift_pairwise_ks(state, parameters)
    third = result.lift.project_pairs()[2]
    broken_third = lift_cotangent(
        KeplerPhaseState(third.x + np.array([0.1, 0.0, 0.0]), third.p)
    )
    broken = CanonicalPairwiseKSLift(
        parameters,
        result.lift.ks12,
        result.lift.ks23,
        broken_third,
    )
    assert broken.constraint_residuals().position_closure_norm > 0.09
    with pytest.raises(ValueError, match="triangle closure"):
        broken.to_inertial(result.reconstruction)


def test_binary_collision_has_no_physical_to_ks_section() -> None:
    state, parameters = _state()
    positions = np.array(state.positions, copy=True)
    positions[1] = positions[0]
    collision = InertialState.from_components(positions, state.velocities)
    with pytest.raises(ValueError, match="undefined at x = 0"):
        lift_pairwise_ks(collision, parameters)


def test_dimension_accounting_is_explicit_and_bounded() -> None:
    dimensions = pairwise_dimension_accounting()
    assert dimensions["three_ks_phase_spaces"] == 24
    assert dimensions["three_physical_pair_phase_spaces"] == 18
    assert dimensions["translation_reduced_n3bp_phase_space"] == 12
    assert dimensions["global_sundman_time_qualified"] is False
