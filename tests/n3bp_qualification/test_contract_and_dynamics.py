"""Contract, invariant, and differential-equation tests."""

from __future__ import annotations

import numpy as np
import pytest

from src.python.n3bp_qualification import (
    CollisionSingularityError,
    InertialState,
    SystemParameters,
    center_of_mass_position,
    center_of_mass_velocity,
    linear_momentum,
    newtonian_accelerations,
    newtonian_rhs,
    normalize_center_of_mass,
)


def generic_state() -> InertialState:
    return InertialState.from_components(
        positions=np.array(
            [[-1.2, 0.4, 0.2], [0.7, -0.8, 0.5], [1.1, 0.9, -0.6]]
        ),
        velocities=np.array(
            [[0.3, -0.2, 0.1], [-0.4, 0.6, -0.3], [0.2, 0.1, 0.5]]
        ),
    )


def generic_parameters() -> SystemParameters:
    return SystemParameters([1.0, 2.0, 3.5], gravitational_constant=0.7)


def axis_angle_rotation(axis: np.ndarray, angle: float) -> np.ndarray:
    unit_axis = axis / np.linalg.norm(axis)
    x, y, z = unit_axis
    cross_matrix = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    return (
        np.eye(3) * np.cos(angle)
        + (1.0 - np.cos(angle)) * np.outer(unit_axis, unit_axis)
        + np.sin(angle) * cross_matrix
    )


def test_state_contract_has_unambiguous_18d_ordering() -> None:
    positions = np.arange(9, dtype=np.float64).reshape(3, 3)
    velocities = np.arange(9, 18, dtype=np.float64).reshape(3, 3)
    state = InertialState.from_components(positions, velocities)

    np.testing.assert_array_equal(state.values, np.arange(18, dtype=np.float64))
    np.testing.assert_array_equal(state.positions, positions)
    np.testing.assert_array_equal(state.velocities, velocities)
    assert not state.values.flags.writeable


@pytest.mark.parametrize(
    "values",
    [np.zeros(17), np.zeros((18, 1)), np.full(18, np.nan)],
)
def test_state_contract_rejects_invalid_vectors(values: np.ndarray) -> None:
    with pytest.raises(ValueError):
        InertialState(values)


@pytest.mark.parametrize(
    "masses, gravitational_constant",
    [([1.0, 2.0], 1.0), ([1.0, 0.0, 2.0], 1.0), ([1.0, 2.0, 3.0], 0.0)],
)
def test_parameter_contract_rejects_invalid_physics(
    masses: list[float],
    gravitational_constant: float,
) -> None:
    with pytest.raises(ValueError):
        SystemParameters(masses, gravitational_constant)


def test_center_of_mass_normalization_is_mass_weighted_galilean_transform() -> None:
    state = generic_state()
    parameters = generic_parameters()
    normalized = normalize_center_of_mass(state, parameters)

    np.testing.assert_allclose(
        center_of_mass_position(normalized, parameters), np.zeros(3), atol=2e-16
    )
    np.testing.assert_allclose(
        center_of_mass_velocity(normalized, parameters), np.zeros(3), atol=2e-16
    )
    np.testing.assert_allclose(
        linear_momentum(normalized, parameters), np.zeros(3), atol=1e-15
    )
    for first, second in ((0, 1), (0, 2), (1, 2)):
        np.testing.assert_allclose(
            normalized.positions[second] - normalized.positions[first],
            state.positions[second] - state.positions[first],
            atol=2e-16,
        )
        np.testing.assert_allclose(
            normalized.velocities[second] - normalized.velocities[first],
            state.velocities[second] - state.velocities[first],
            atol=2e-16,
        )


def test_pairwise_force_accumulation_conserves_total_momentum_derivative() -> None:
    state = generic_state()
    parameters = generic_parameters()
    accelerations = newtonian_accelerations(state.positions, parameters)
    total_force = np.sum(parameters.masses[:, None] * accelerations, axis=0)
    np.testing.assert_allclose(total_force, np.zeros(3), atol=3e-16)


def test_collision_singularity_is_explicit() -> None:
    positions = generic_state().positions.copy()
    positions[1] = positions[0]
    with pytest.raises(CollisionSingularityError, match="coincident"):
        newtonian_accelerations(positions, generic_parameters())


def test_rhs_is_covariant_under_body_permutation() -> None:
    state = generic_state()
    parameters = generic_parameters()
    permutation = np.array([2, 0, 1])

    permuted_state = InertialState.from_components(
        state.positions[permutation], state.velocities[permutation]
    )
    permuted_parameters = SystemParameters(
        parameters.masses[permutation], parameters.gravitational_constant
    )
    base_rhs = newtonian_rhs(0.0, state, parameters)
    permuted_rhs = newtonian_rhs(0.0, permuted_state, permuted_parameters)
    expected = np.concatenate(
        (
            base_rhs[:9].reshape(3, 3)[permutation].ravel(),
            base_rhs[9:].reshape(3, 3)[permutation].ravel(),
        )
    )
    np.testing.assert_allclose(permuted_rhs, expected, rtol=3e-15, atol=3e-15)


def test_rhs_is_covariant_under_proper_spatial_rotation() -> None:
    state = generic_state()
    parameters = generic_parameters()
    rotation = axis_angle_rotation(np.array([1.0, -2.0, 0.5]), 0.73)
    rotated_state = InertialState.from_components(
        state.positions @ rotation.T,
        state.velocities @ rotation.T,
    )

    base_rhs = newtonian_rhs(0.0, state, parameters)
    rotated_rhs = newtonian_rhs(0.0, rotated_state, parameters)
    expected = np.concatenate(
        (
            (base_rhs[:9].reshape(3, 3) @ rotation.T).ravel(),
            (base_rhs[9:].reshape(3, 3) @ rotation.T).ravel(),
        )
    )
    np.testing.assert_allclose(rotated_rhs, expected, rtol=3e-15, atol=3e-15)


def test_rhs_obeys_newtonian_position_time_scaling() -> None:
    state = generic_state()
    parameters = generic_parameters()
    spatial_scale = 2.7
    scaled_state = InertialState.from_components(
        spatial_scale * state.positions,
        state.velocities / np.sqrt(spatial_scale),
    )

    base_rhs = newtonian_rhs(0.0, state, parameters)
    scaled_rhs = newtonian_rhs(0.0, scaled_state, parameters)
    expected = np.concatenate(
        (
            base_rhs[:9] / np.sqrt(spatial_scale),
            base_rhs[9:] / spatial_scale**2,
        )
    )
    np.testing.assert_allclose(scaled_rhs, expected, rtol=3e-15, atol=3e-15)
