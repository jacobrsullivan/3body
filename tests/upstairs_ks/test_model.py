"""Structural tests for the WP2-UP-v1 canonical one-channel lift."""

from __future__ import annotations

import numpy as np
import pytest

from src.python.n3bp_qualification import figure_eight_choreography
from src.python.threebody_flow import canonical_jacobi_flow
from src.python.threebody_reduction import JacobiPhaseState
from src.python.upstairs_ks import (
    UpstairsKSState,
    angular_momentum,
    lift_jacobi_state,
    momentum_map_derivative,
    project_derivative,
    project_state,
    regularized_hamiltonian,
    s1_action,
    upstairs_vector_field,
)


def _case(angle: float = 0.37):
    orbit = figure_eight_choreography()
    jacobi = JacobiPhaseState.from_inertial(
        orbit.initial_state, orbit.parameters
    ).quotient.as_canonical_vector()
    shell = lift_jacobi_state(jacobi, orbit.parameters, angle=angle)
    return orbit.parameters, jacobi, shell


def test_shell_roundtrip_and_sundman_projection() -> None:
    parameters, jacobi, shell = _case()
    flow = upstairs_vector_field(shell.state, parameters, shell.energy)
    physical = canonical_jacobi_flow(jacobi, parameters)

    assert project_state(shell.state) == pytest.approx(jacobi, abs=2e-14)
    assert shell.state.xi == pytest.approx(0.0, abs=2e-14)
    assert flow.hamiltonian == pytest.approx(0.0, abs=2e-14)
    assert project_derivative(flow) == pytest.approx(
        shell.state.radius * physical.derivative, abs=3e-13
    )
    assert momentum_map_derivative(flow) == pytest.approx(0.0, abs=3e-13)


def test_circle_action_preserves_projection_hamiltonian_and_flow() -> None:
    parameters, _, shell = _case()
    reference = upstairs_vector_field(shell.state, parameters, shell.energy)
    transformed = s1_action(shell.state, -1.13)
    transformed_flow = upstairs_vector_field(transformed, parameters, shell.energy)

    assert project_state(transformed) == pytest.approx(
        project_state(shell.state), abs=3e-14
    )
    assert regularized_hamiltonian(transformed, parameters, shell.energy) == pytest.approx(
        reference.hamiltonian, abs=3e-14
    )
    expected = s1_action(
        UpstairsKSState(
            reference.derivative[:4],
            reference.derivative[4:7],
            reference.derivative[7:11],
            reference.derivative[11:14],
        ),
        -1.13,
    ).as_vector()
    assert transformed_flow.derivative == pytest.approx(expected, abs=3e-13)


def test_vector_field_is_canonical_gradient() -> None:
    parameters, _, shell = _case()
    vector = shell.state.as_vector()
    flow = upstairs_vector_field(shell.state, parameters, shell.energy)
    step = 2e-7
    gradient = np.empty(14)
    for index in range(14):
        offset = np.zeros(14)
        offset[index] = step
        plus = regularized_hamiltonian(
            UpstairsKSState.from_vector(vector + offset), parameters, shell.energy
        )
        minus = regularized_hamiltonian(
            UpstairsKSState.from_vector(vector - offset), parameters, shell.energy
        )
        gradient[index] = (plus - minus) / (2.0 * step)
    expected = np.concatenate((gradient[7:], -gradient[:7]))
    assert flow.derivative == pytest.approx(expected, abs=2e-8, rel=2e-8)


def test_selected_binary_collision_has_finite_vector_field() -> None:
    parameters, _, shell = _case()
    collision = UpstairsKSState(
        q=np.zeros(4),
        lambda_vector=np.array([1.2, -0.4, 0.7]),
        Q=np.array([0.3, -0.7, 0.2, 0.9]),
        p_lambda=np.array([-0.2, 0.6, 0.1]),
    )
    flow = upstairs_vector_field(collision, parameters, shell.energy)
    assert np.all(np.isfinite(flow.derivative))
    assert flow.physical_time_rate == 0.0


def test_angular_momentum_is_gauge_invariant() -> None:
    _, _, shell = _case()
    assert angular_momentum(s1_action(shell.state, 2.71)) == pytest.approx(
        angular_momentum(shell.state), abs=3e-14
    )
