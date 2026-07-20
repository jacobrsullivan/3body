from __future__ import annotations

import numpy as np
import pytest

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    angular_momentum,
    total_energy,
)
from src.python.threebody_reduction import (
    JacobiPhaseState,
    ReductionChartSingularity,
    canonical_body_frame,
    jacobi_coordinate_matrix,
    reduce_euclidean,
    reduce_translation,
)


def _random_state(seed: int = 17) -> tuple[InertialState, SystemParameters]:
    rng = np.random.default_rng(seed)
    positions = rng.normal(size=(3, 3))
    velocities = rng.normal(size=(3, 3))
    parameters = SystemParameters([0.7, 1.3, 2.1], gravitational_constant=0.83)
    return InertialState.from_components(positions, velocities), parameters


def _proper_rotation(seed: int = 81) -> np.ndarray:
    matrix = np.random.default_rng(seed).normal(size=(3, 3))
    rotation, _ = np.linalg.qr(matrix)
    if np.linalg.det(rotation) < 0.0:
        rotation[:, 0] *= -1.0
    return rotation


def test_jacobi_roundtrip_and_immutable_contract() -> None:
    state, parameters = _random_state()
    jacobi = JacobiPhaseState.from_inertial(state, parameters)
    reconstructed = jacobi.to_inertial()
    assert np.allclose(reconstructed.values, state.values, atol=2e-15, rtol=0.0)
    with pytest.raises(ValueError):
        jacobi.rho[0] = 0.0


def test_jacobi_linear_map_is_canonical_and_preserves_one_form() -> None:
    state, parameters = _random_state(19)
    jacobi = JacobiPhaseState.from_inertial(state, parameters)
    coordinate_matrix = np.kron(jacobi_coordinate_matrix(parameters), np.eye(3))
    momentum_matrix = np.linalg.inv(coordinate_matrix).T
    transform = np.block(
        [
            [coordinate_matrix, np.zeros((9, 9))],
            [np.zeros((9, 9)), momentum_matrix],
        ]
    )
    canonical = np.block(
        [[np.zeros((9, 9)), np.eye(9)], [-np.eye(9), np.zeros((9, 9))]]
    )
    assert np.allclose(transform @ canonical @ transform.T, canonical, atol=2e-15)

    old_momenta = (parameters.masses[:, None] * state.velocities).ravel()
    old_phase = np.concatenate((state.positions.ravel(), old_momenta))
    assert np.allclose(
        transform @ old_phase,
        jacobi.as_canonical_vector(),
        atol=2e-15,
        rtol=0.0,
    )
    variation = np.random.default_rng(20).normal(size=9)
    new_variation = coordinate_matrix @ variation
    new_momenta = jacobi.as_canonical_vector()[9:]
    assert np.isclose(
        np.dot(old_momenta, variation),
        np.dot(new_momenta, new_variation),
        atol=2e-15,
        rtol=0.0,
    )


def test_translation_reduction_has_correct_energy_and_momentum_splits() -> None:
    state, parameters = _random_state(21)
    result = reduce_translation(state, parameters)
    center_energy = np.dot(
        result.reconstruction.total_momentum, result.reconstruction.total_momentum
    ) / (2.0 * parameters.total_mass)
    assert np.isclose(
        total_energy(state, parameters),
        result.quotient.total_energy() + center_energy,
        atol=3e-15,
        rtol=2e-15,
    )
    expected_angular = (
        np.cross(
            result.reconstruction.center_of_mass,
            result.reconstruction.total_momentum,
        )
        + result.quotient.angular_momentum()
    )
    assert np.allclose(
        angular_momentum(state, parameters), expected_angular, atol=3e-15, rtol=0.0
    )
    assert result.quotient.phase_dimension == 12
    assert result.quotient.configuration_dimension == 6


def test_translation_quotient_is_galilean_invariant() -> None:
    state, parameters = _random_state(23)
    shift = np.array([1.1, -0.4, 2.0])
    boost = np.array([-0.2, 0.7, 0.3])
    moved = InertialState.from_components(
        state.positions + shift,
        state.velocities + boost,
    )
    first = reduce_translation(state, parameters)
    second = reduce_translation(moved, parameters)
    assert np.allclose(
        first.quotient.as_canonical_vector(),
        second.quotient.as_canonical_vector(),
        atol=2e-15,
        rtol=0.0,
    )
    assert np.allclose(second.reconstruct().values, moved.values, atol=3e-15, rtol=0.0)


def test_euclidean_quotient_roundtrip_gauge_and_dimensions() -> None:
    state, parameters = _random_state(29)
    result = reduce_euclidean(state, parameters)
    quotient = result.quotient
    assert np.allclose(result.reconstruct().values, state.values, atol=4e-15, rtol=0.0)
    assert quotient.rho_body[0] > 0.0
    assert quotient.lambda_body[1] > 0.0
    assert np.array_equal(quotient.rho_body[1:], np.zeros(2))
    assert quotient.lambda_body[2] == 0.0
    assert quotient.poisson_dimension == 9
    assert quotient.generic_fixed_momentum_leaf_dimension == 8
    assert quotient.zero_momentum_leaf_dimension == 6
    expected_body_angular = (
        result.reconstruction.body_frame.T
        @ reduce_translation(state, parameters).quotient.angular_momentum()
    )
    assert np.allclose(
        quotient.angular_momentum_body, expected_body_angular, atol=3e-15, rtol=0.0
    )


def test_euclidean_quotient_is_rigid_motion_and_boost_invariant() -> None:
    state, parameters = _random_state(31)
    rotation = _proper_rotation()
    shift = np.array([1.7, -0.2, 0.9])
    boost = np.array([0.15, -0.7, 0.4])
    moved = InertialState.from_components(
        state.positions @ rotation.T + shift,
        state.velocities @ rotation.T + boost,
    )
    first = reduce_euclidean(state, parameters)
    second = reduce_euclidean(moved, parameters)
    assert np.allclose(
        first.quotient.as_orbit_coordinates(),
        second.quotient.as_orbit_coordinates(),
        atol=5e-15,
        rtol=0.0,
    )
    assert np.isclose(first.quotient.total_energy(), second.quotient.total_energy())
    assert np.allclose(second.reconstruct().values, moved.values, atol=8e-15, rtol=0.0)


def test_body_frame_is_equivariant_under_proper_rotations() -> None:
    state, parameters = _random_state(37)
    translated = reduce_translation(state, parameters).quotient
    rotation = _proper_rotation(82)
    frame = canonical_body_frame(translated.rho, translated.lambda_vector)
    rotated_frame = canonical_body_frame(
        rotation @ translated.rho,
        rotation @ translated.lambda_vector,
    )
    assert np.allclose(rotated_frame, rotation @ frame, atol=5e-15, rtol=0.0)


@pytest.mark.parametrize(
    "positions",
    [
        np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 1.0, 0.0]]),
        np.array([[-1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [2.0, 0.0, 0.0]]),
    ],
)
def test_euclidean_chart_rejects_singular_orbit_strata(positions: np.ndarray) -> None:
    state = InertialState.from_components(positions, np.zeros((3, 3)))
    parameters = SystemParameters([1.0, 1.0, 1.0])
    with pytest.raises(ReductionChartSingularity):
        reduce_euclidean(state, parameters)
