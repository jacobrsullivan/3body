from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from src.python.n3bp_qualification import (
    figure_eight_choreography,
    newtonian_rhs,
    total_energy,
)
from src.python.wp2_multi_v1 import (
    CHART_LOCAL_ORDER,
    DEFAULT_COLLISION_FLOOR,
    ChartDomainError,
    MultiKSState,
    TripleCollisionOutOfScope,
    collision_shell_state,
    choose_regularizing_chart,
    global_time_rate,
    lift_inertial_state,
    ordered_pair_distances,
    project_derivative,
    project_positions,
    project_state,
    regularized_hamiltonian,
    regularized_channels,
    selected_physical_channel,
    switch_to_regularizing_chart,
    torus_action,
    transition_chart,
    vector_field,
)


def _shell(chart: str = "central-3", angles=(0.37, -0.91)):
    orbit = figure_eight_choreography()
    state = lift_inertial_state(
        orbit.initial_state, orbit.parameters, chart, angles=angles
    )
    return orbit, state


def _reference_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "validation-external/wp2-multi-validation/reference/autodiff_reference.py"
    )
    specification = importlib.util.spec_from_file_location("wp2_multi_autodiff", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.mark.parametrize("chart", sorted(CHART_LOCAL_ORDER))
def test_each_chart_roundtrips_and_uses_one_global_clock(chart: str) -> None:
    orbit, state = _shell(chart)
    projected = project_state(state, orbit.parameters)
    assert projected.values == pytest.approx(orbit.initial_state.values, abs=4e-14)
    assert state.momentum_maps == pytest.approx(np.zeros(2), abs=3e-14)
    assert regularized_hamiltonian(state, orbit.parameters) == pytest.approx(0.0, abs=2e-13)

    positions = orbit.initial_state.positions
    distances = np.array(
        [
            np.linalg.norm(positions[1] - positions[0]),
            np.linalg.norm(positions[2] - positions[1]),
            np.linalg.norm(positions[0] - positions[2]),
        ]
    )
    assert ordered_pair_distances(state) == pytest.approx(distances, abs=3e-14)
    assert global_time_rate(state) == pytest.approx(np.prod(distances), abs=3e-14)


def test_hamiltonian_is_global_clock_times_physical_extended_hamiltonian() -> None:
    orbit, shell = _shell()
    vector = shell.as_vector().copy()
    vector[17] += 0.173
    off_shell = MultiKSState.from_vector(shell.chart, vector)
    physical = project_state(off_shell, orbit.parameters)
    expected = global_time_rate(off_shell) * (
        total_energy(physical, orbit.parameters) + off_shell.p_t
    )
    assert regularized_hamiltonian(off_shell, orbit.parameters) == pytest.approx(
        expected, rel=3e-13, abs=3e-13
    )


def test_analytic_field_is_full_off_shell_canonical_gradient() -> None:
    orbit, shell = _shell()
    vector = shell.as_vector().copy()
    vector[0] += 0.013
    vector[10] -= 0.021
    vector[17] += 0.19
    state = MultiKSState.from_vector(shell.chart, vector)
    field = vector_field(state, orbit.parameters)
    step = 1e-7
    gradient = np.empty(18)
    for index in range(18):
        offset = np.zeros(18)
        offset[index] = step
        plus = regularized_hamiltonian(
            MultiKSState.from_vector(state.chart, vector + offset), orbit.parameters
        )
        minus = regularized_hamiltonian(
            MultiKSState.from_vector(state.chart, vector - offset), orbit.parameters
        )
        gradient[index] = (plus - minus) / (2.0 * step)
    expected = np.concatenate((gradient[9:17], [gradient[17]], -gradient[:8], [-gradient[8]]))
    # Reorder from canonical gradient (q1,q2,t,P1,P2,pt) to state derivative.
    expected = np.concatenate((gradient[9:13], gradient[13:17], [gradient[17]], -gradient[:4], -gradient[4:8], [-gradient[8]]))
    assert field.derivative == pytest.approx(expected, rel=2e-7, abs=2e-7)


@pytest.mark.parametrize("chart", sorted(CHART_LOCAL_ORDER))
def test_independent_autodiff_reference_matches_scalar_and_field(chart: str) -> None:
    orbit, shell = _shell(chart)
    vector = shell.as_vector().copy()
    vector[0] += 0.013
    vector[6] -= 0.009
    vector[17] += 0.17
    state = MultiKSState.from_vector(chart, vector)
    production = vector_field(state, orbit.parameters)
    order = CHART_LOCAL_ORDER[chart]
    local_masses = orbit.parameters.masses[list(order)]
    value, field = _reference_module().evaluate(
        vector, local_masses, orbit.parameters.gravitational_constant
    )
    assert value == pytest.approx(production.hamiltonian, abs=3e-13)
    assert field == pytest.approx(production.derivative, abs=3e-12)


@pytest.mark.parametrize("chart", sorted(CHART_LOCAL_ORDER))
def test_projected_shell_field_is_sundman_scaled_newtonian_flow(chart: str) -> None:
    orbit, state = _shell(chart)
    flow = vector_field(state, orbit.parameters)
    physical = project_state(state, orbit.parameters)
    expected = flow.time_rate * newtonian_rhs(0.0, physical.values, orbit.parameters)
    assert project_derivative(flow, orbit.parameters) == pytest.approx(
        expected, rel=2e-11, abs=2e-11
    )
    assert flow.momentum_map_derivatives == pytest.approx(np.zeros(2), abs=2e-12)


def test_torus_action_preserves_projection_hamiltonian_and_covaries_field() -> None:
    orbit, state = _shell()
    angles = (1.13, -2.07)
    transformed = torus_action(state, angles)
    reference = vector_field(state, orbit.parameters)
    moved = vector_field(transformed, orbit.parameters)
    assert project_state(transformed, orbit.parameters).values == pytest.approx(
        project_state(state, orbit.parameters).values, abs=4e-14
    )
    assert moved.hamiltonian == pytest.approx(reference.hamiltonian, abs=3e-13)
    tangent = MultiKSState(
        chart=state.chart,
        q1=reference.derivative[:4],
        q2=reference.derivative[4:8],
        physical_time=reference.derivative[8],
        P1=reference.derivative[9:13],
        P2=reference.derivative[13:17],
        p_t=reference.derivative[17],
    )
    expected = torus_action(tangent, angles).as_vector()
    assert moved.derivative == pytest.approx(expected, abs=2e-12)


def test_chart_transitions_preserve_the_common_quotient_and_cocycle() -> None:
    orbit, state = _shell("central-1")
    second = transition_chart(state, orbit.parameters, "central-2", angles=(0.2, -0.4))
    third = transition_chart(second, orbit.parameters, "central-3", angles=(-0.7, 0.9))
    returned = transition_chart(third, orbit.parameters, "central-1", angles=(1.1, -1.3))
    expected = project_state(state, orbit.parameters).values
    for item in (second, third, returned):
        assert project_state(item, orbit.parameters).values == pytest.approx(expected, abs=8e-14)
        assert item.physical_time == pytest.approx(state.physical_time)
        assert item.p_t == pytest.approx(state.p_t)
        assert global_time_rate(item) == pytest.approx(global_time_rate(state), abs=2e-13)


@pytest.mark.parametrize("selected_edge", [1, 2])
def test_exact_selected_collision_has_finite_on_shell_field(selected_edge: int) -> None:
    orbit = figure_eight_choreography()
    collision = collision_shell_state(
        orbit.parameters,
        "central-3",
        selected_edge,
        other_q=np.array([0.8, 0.0, 0.25, -0.1]),
        collision_direction=np.array([1.0, -0.3, 0.2, 0.4]),
        energy=-1.7,
    )
    flow = vector_field(collision, orbit.parameters)
    assert collision.momentum_maps == pytest.approx(np.zeros(2), abs=2e-14)
    assert flow.hamiltonian == pytest.approx(0.0, abs=3e-14)
    assert np.all(np.isfinite(flow.derivative))
    assert flow.time_rate == 0.0
    assert np.all(np.isfinite(project_positions(collision, orbit.parameters)))


@pytest.mark.parametrize("direction", [-1.0, 1.0])
def test_exact_collision_integrates_in_both_fictitious_time_directions(
    direction: float,
) -> None:
    orbit = figure_eight_choreography()
    collision = collision_shell_state(
        orbit.parameters,
        "central-3",
        1,
        other_q=np.array([0.8, 0.0, 0.25, -0.1]),
        collision_direction=np.array([1.0, -0.3, 0.2, 0.4]),
        energy=-1.7,
    )

    result = solve_ivp(
        lambda _, value: vector_field(
            MultiKSState.from_vector(collision.chart, value), orbit.parameters
        ).derivative,
        (0.0, direction * 5e-4),
        collision.as_vector(),
        method="DOP853",
        rtol=2e-12,
        atol=2e-13,
        max_step=2e-5,
    )
    assert result.success
    assert np.all(np.isfinite(result.y))
    final = MultiKSState.from_vector(collision.chart, result.y[:, -1])
    assert np.linalg.norm(final.q1) > 0.0
    assert regularized_hamiltonian(final, orbit.parameters) == pytest.approx(
        0.0, abs=2e-12
    )
    assert final.momentum_maps == pytest.approx(np.zeros(2), abs=2e-12)


def test_unregularized_edge_and_triple_collision_fail_closed() -> None:
    orbit = figure_eight_choreography()
    # In central-3, q1 and q2 encode r1-r3 and r2-r3. Equal nonzero
    # positions are the unregularized 1-2 collision.
    same = np.array([0.7, 0.1, -0.2, 0.3])
    unregularized = MultiKSState(
        "central-3", same, same, 0.0, np.zeros(4), np.zeros(4), 1.0
    )
    with pytest.raises(ChartDomainError):
        vector_field(unregularized, orbit.parameters)

    triple = MultiKSState(
        "central-3", np.zeros(4), np.zeros(4), 0.0, np.ones(4), np.ones(4), 1.0
    )
    with pytest.raises(TripleCollisionOutOfScope):
        vector_field(triple, orbit.parameters)


def test_locked_floor_rejects_two_small_pairs_but_not_one_selected_pair() -> None:
    orbit = figure_eight_choreography()
    scale = np.sqrt(0.5 * DEFAULT_COLLISION_FLOOR)
    double = MultiKSState(
        "central-3",
        np.array([scale, 0.0, 0.0, 0.0]),
        np.array([0.0, scale, 0.0, 0.0]),
        0.0,
        np.ones(4),
        np.ones(4),
        1.0,
    )
    with pytest.raises(TripleCollisionOutOfScope):
        vector_field(double, orbit.parameters)

    isolated = collision_shell_state(
        orbit.parameters,
        "central-3",
        1,
        other_q=np.array([0.8, 0.0, 0.25, -0.1]),
        collision_direction=np.array([1.0, -0.3, 0.2, 0.4]),
        energy=-1.7,
    )
    assert np.all(np.isfinite(vector_field(isolated, orbit.parameters).derivative))


def test_physical_channel_mapping_and_smallest_pair_switch_policy() -> None:
    assert {
        selected_physical_channel(chart, edge)
        for chart in CHART_LOCAL_ORDER
        for edge in (1, 2)
    } == {"12", "23", "31"}
    assert all(len(set(regularized_channels(chart))) == 2 for chart in CHART_LOCAL_ORDER)

    orbit = figure_eight_choreography()
    physical = orbit.initial_state
    distances = {
        "12": np.linalg.norm(physical.positions[0] - physical.positions[1]),
        "23": np.linalg.norm(physical.positions[1] - physical.positions[2]),
        "31": np.linalg.norm(physical.positions[2] - physical.positions[0]),
    }
    smallest = min(distances, key=distances.get)
    bad_chart = next(
        chart for chart in CHART_LOCAL_ORDER if smallest not in regularized_channels(chart)
    )
    bad = lift_inertial_state(physical, orbit.parameters, bad_chart)
    target = choose_regularizing_chart(bad)
    assert target != bad_chart
    assert smallest in regularized_channels(target)
    switched = switch_to_regularizing_chart(bad, orbit.parameters)
    assert switched.chart == target
    assert project_state(switched, orbit.parameters).values == pytest.approx(
        physical.values, abs=8e-14
    )


def test_transition_requires_collision_free_overlap() -> None:
    orbit = figure_eight_choreography()
    same = np.array([0.7, 0.1, -0.2, 0.3])
    unregularized = MultiKSState(
        "central-3", same, same, 0.0, np.zeros(4), np.zeros(4), 1.0
    )
    with pytest.raises(ChartDomainError):
        transition_chart(unregularized, orbit.parameters, "central-1")
