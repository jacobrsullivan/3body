"""Analytic, published-orbit, reference, and covariance propagation tests."""

from __future__ import annotations

import numpy as np

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    angular_momentum,
    center_of_mass_position,
    center_of_mass_velocity,
    figure_eight_choreography,
    lagrange_analytic_state,
    lagrange_equilateral,
    linear_momentum,
    measure_invariant_drift,
    newtonian_rhs,
    propagate_dop853,
    propagate_rebound_ias15,
)


def rotate_states(states: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    positions = states[:, :9].reshape(-1, 3, 3) @ rotation.T
    velocities = states[:, 9:].reshape(-1, 3, 3) @ rotation.T
    return np.concatenate(
        (positions.reshape(-1, 9), velocities.reshape(-1, 9)), axis=1
    )


def scale_states(states: np.ndarray, spatial_scale: float) -> np.ndarray:
    result = np.array(states, copy=True)
    result[:, :9] *= spatial_scale
    result[:, 9:] /= np.sqrt(spatial_scale)
    return result


def test_lagrange_definition_uses_side_length_and_exact_centripetal_rhs() -> None:
    orbit = lagrange_equilateral(side_length=1.7, mass=0.8, gravitational_constant=1.2)
    positions = orbit.initial_state.positions
    distances = [
        np.linalg.norm(positions[first] - positions[second])
        for first, second in ((0, 1), (0, 2), (1, 2))
    ]
    np.testing.assert_allclose(distances, np.full(3, 1.7), rtol=2e-15, atol=2e-15)

    angular_frequency = 2.0 * np.pi / orbit.period
    rhs = newtonian_rhs(0.0, orbit.initial_state, orbit.parameters)
    np.testing.assert_allclose(
        rhs[:9].reshape(3, 3), orbit.initial_state.velocities, atol=0.0
    )
    np.testing.assert_allclose(
        rhs[9:].reshape(3, 3),
        -(angular_frequency**2) * positions,
        rtol=3e-15,
        atol=3e-15,
    )


def test_lagrange_dop853_matches_analytic_checkpoints_and_closure() -> None:
    orbit = lagrange_equilateral()
    times = np.linspace(0.0, orbit.period, 65)
    trajectory = propagate_dop853(
        orbit.initial_state, times, orbit.parameters
    )
    analytic = np.array(
        [lagrange_analytic_state(orbit, time).values for time in times]
    )

    assert trajectory.engine == "scipy-dop853"
    assert np.max(np.abs(trajectory.states - analytic)) < 2e-11
    closure = np.max(
        np.abs(trajectory.final_state.values - orbit.initial_state.values)
    )
    assert closure < 2e-11

    drift = measure_invariant_drift(trajectory.states, orbit.parameters)
    assert drift.max_relative_energy < 1e-11
    assert drift.max_linear_momentum < 3e-15
    assert drift.max_angular_momentum < 1e-11


def test_lagrange_dop853_matches_independent_ias15_checkpoints() -> None:
    orbit = lagrange_equilateral()
    times = orbit.period * np.array([0.0, 0.125, 0.25, 0.5, 0.75, 1.0])
    production = propagate_dop853(orbit.initial_state, times, orbit.parameters)
    reference = propagate_rebound_ias15(orbit.initial_state, times, orbit.parameters)

    assert reference.engine == "rebound-ias15"
    assert np.max(np.abs(production.states - reference.states)) < 3e-11


def test_published_figure_eight_contract_and_first_integrals() -> None:
    orbit = figure_eight_choreography()
    np.testing.assert_allclose(
        orbit.initial_state.positions[0], [0.97000436, -0.24308753, 0.0]
    )
    np.testing.assert_allclose(
        orbit.initial_state.velocities[0], [0.466203685, 0.43236573, 0.0]
    )
    np.testing.assert_allclose(
        center_of_mass_position(orbit.initial_state, orbit.parameters),
        np.zeros(3),
        atol=0.0,
    )
    np.testing.assert_allclose(
        center_of_mass_velocity(orbit.initial_state, orbit.parameters),
        np.zeros(3),
        atol=0.0,
    )
    np.testing.assert_allclose(
        linear_momentum(orbit.initial_state, orbit.parameters), np.zeros(3), atol=0.0
    )
    np.testing.assert_allclose(
        angular_momentum(orbit.initial_state, orbit.parameters), np.zeros(3), atol=2e-16
    )


def test_published_figure_eight_closure_and_invariant_drift() -> None:
    orbit = figure_eight_choreography()
    times = np.linspace(0.0, orbit.period, 129)
    trajectory = propagate_dop853(orbit.initial_state, times, orbit.parameters)
    closure = np.linalg.norm(trajectory.final_state.values - orbit.initial_state.values)
    drift = measure_invariant_drift(trajectory.states, orbit.parameters)

    # Closure is limited by the decimal precision of the published initial state.
    assert closure < 5e-6
    assert drift.max_relative_energy < 1e-11
    assert drift.max_linear_momentum < 3e-15
    assert drift.max_angular_momentum < 1e-11


def test_published_figure_eight_matches_independent_ias15_checkpoints() -> None:
    orbit = figure_eight_choreography()
    times = orbit.period * np.array([0.0, 1.0 / 12.0, 1.0 / 6.0, 1.0 / 3.0, 0.5, 1.0])
    production = propagate_dop853(orbit.initial_state, times, orbit.parameters)
    reference = propagate_rebound_ias15(orbit.initial_state, times, orbit.parameters)

    assert np.max(np.abs(production.states - reference.states)) < 2e-10


def test_dop853_trajectory_is_covariant_under_body_permutation() -> None:
    orbit = lagrange_equilateral()
    permutation = np.array([2, 0, 1])
    permuted_state = InertialState.from_components(
        orbit.initial_state.positions[permutation],
        orbit.initial_state.velocities[permutation],
    )
    permuted_parameters = SystemParameters(
        orbit.parameters.masses[permutation],
        orbit.parameters.gravitational_constant,
    )
    times = np.linspace(0.0, 0.4 * orbit.period, 17)
    base = propagate_dop853(orbit.initial_state, times, orbit.parameters)
    permuted = propagate_dop853(permuted_state, times, permuted_parameters)
    expected = np.concatenate(
        (
            base.states[:, :9].reshape(-1, 3, 3)[:, permutation].reshape(-1, 9),
            base.states[:, 9:].reshape(-1, 3, 3)[:, permutation].reshape(-1, 9),
        ),
        axis=1,
    )

    np.testing.assert_allclose(permuted.states, expected, rtol=2e-12, atol=2e-12)


def test_dop853_trajectory_is_covariant_under_rotation() -> None:
    orbit = figure_eight_choreography()
    angle = 0.61
    rotation = np.array(
        [
            [np.cos(angle), 0.0, np.sin(angle)],
            [0.0, 1.0, 0.0],
            [-np.sin(angle), 0.0, np.cos(angle)],
        ]
    )
    rotated_state = InertialState.from_components(
        orbit.initial_state.positions @ rotation.T,
        orbit.initial_state.velocities @ rotation.T,
    )
    times = np.linspace(0.0, 0.2 * orbit.period, 17)
    base = propagate_dop853(orbit.initial_state, times, orbit.parameters)
    rotated = propagate_dop853(rotated_state, times, orbit.parameters)

    np.testing.assert_allclose(
        rotated.states,
        rotate_states(base.states, rotation),
        rtol=3e-11,
        atol=3e-11,
    )


def test_dop853_trajectory_obeys_newtonian_scaling() -> None:
    orbit = lagrange_equilateral()
    spatial_scale = 2.3
    time_scale = spatial_scale**1.5
    scaled_initial = InertialState.from_components(
        spatial_scale * orbit.initial_state.positions,
        orbit.initial_state.velocities / np.sqrt(spatial_scale),
    )
    base_times = np.linspace(0.0, 0.6 * orbit.period, 25)
    scaled_times = time_scale * base_times
    base = propagate_dop853(orbit.initial_state, base_times, orbit.parameters)
    scaled = propagate_dop853(scaled_initial, scaled_times, orbit.parameters)

    np.testing.assert_allclose(
        scaled.states,
        scale_states(base.states, spatial_scale),
        rtol=4e-11,
        atol=4e-11,
    )
