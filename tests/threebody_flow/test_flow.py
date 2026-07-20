"""Structural tests for canonical, reduced, and pairwise KS three-body flow."""

from __future__ import annotations

import numpy as np

from src.python.ks import KSPhaseState, project_cotangent
from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    newtonian_rhs,
    normalize_center_of_mass,
)
from src.python.pairwise_ks import lift_pairwise_ks
from src.python.threebody_flow import (
    canonical_jacobi_flow,
    euclidean_reduced_flow,
    jacobi_hamiltonian,
    pairwise_ks_flow,
)
from src.python.threebody_reduction import JacobiPhaseState, reduce_euclidean
from src.python.wp3_exploration import jacobi_vector_field


def _case() -> tuple[InertialState, SystemParameters]:
    parameters = SystemParameters([0.7, 1.1, 1.6], gravitational_constant=0.9)
    state = InertialState.from_components(
        [
            [-0.8, 0.2, 0.4],
            [0.9, -0.4, 0.1],
            [0.3, 1.2, -0.7],
        ],
        [
            [0.4, -0.3, 0.8],
            [-0.7, 0.2, -0.1],
            [0.1, 0.6, -0.5],
        ],
    )
    return normalize_center_of_mass(state, parameters), parameters


def test_canonical_hamiltonian_flow_matches_full_tangent_map() -> None:
    state, parameters = _case()
    jacobi = JacobiPhaseState.from_inertial(state, parameters).quotient
    flow = canonical_jacobi_flow(jacobi)
    tangent = jacobi_vector_field(state, parameters)
    np.testing.assert_allclose(flow.derivative, tangent.derivative, atol=4e-15)
    assert np.isclose(flow.hamiltonian, jacobi.total_energy(), atol=4e-15)


def test_canonical_flow_is_symplectic_gradient_of_hamiltonian() -> None:
    state, parameters = _case()
    vector = JacobiPhaseState.from_inertial(
        state, parameters
    ).quotient.as_canonical_vector()
    flow = canonical_jacobi_flow(vector, parameters)
    step = 1e-6
    gradient = np.empty(12)
    for index in range(12):
        offset = np.zeros(12)
        offset[index] = step
        gradient[index] = (
            jacobi_hamiltonian(vector + offset, parameters)
            - jacobi_hamiltonian(vector - offset, parameters)
        ) / (2.0 * step)
    expected = np.concatenate((gradient[6:], -gradient[:6]))
    np.testing.assert_allclose(flow.derivative, expected, rtol=3e-9, atol=3e-9)
    assert abs(float(np.dot(gradient, flow.derivative))) < 2e-9


def test_reduced_flow_matches_directional_finite_difference() -> None:
    state, parameters = _case()
    quotient = JacobiPhaseState.from_inertial(state, parameters).quotient
    reduced = euclidean_reduced_flow(quotient)
    rhs = newtonian_rhs(0.0, state.values, parameters)
    step = 1e-7
    plus = reduce_euclidean(InertialState(state.values + step * rhs), parameters)
    minus = reduce_euclidean(InertialState(state.values - step * rhs), parameters)
    finite_quotient = (
        plus.quotient.as_orbit_coordinates()
        - minus.quotient.as_orbit_coordinates()
    ) / (2.0 * step)
    finite_frame = (
        plus.reconstruction.body_frame - minus.reconstruction.body_frame
    ) / (2.0 * step)
    np.testing.assert_allclose(
        reduced.quotient_derivative, finite_quotient, rtol=5e-8, atol=5e-8
    )
    np.testing.assert_allclose(
        reduced.body_frame_derivative, finite_frame, rtol=5e-8, atol=5e-8
    )
    skew = reduced.body_frame.T @ reduced.body_frame_derivative
    np.testing.assert_allclose(skew + skew.T, np.zeros((3, 3)), atol=2e-14)


def test_pairwise_ks_flow_projects_to_each_physical_pair_derivative() -> None:
    state, parameters = _case()
    lifted = lift_pairwise_ks(state, parameters, angles=[0.2, -0.7, 1.1])
    flow = pairwise_ks_flow(lifted, parameters)
    step = 1e-7
    for ks_state, derivative in zip(
        lifted.lift.pair_states, flow.pair_derivatives, strict=True
    ):
        plus = project_cotangent(
            KSPhaseState(
                ks_state.q + step * derivative.q_dot,
                ks_state.Q + step * derivative.Q_dot,
            ),
            require_zero_level=False,
        )
        minus = project_cotangent(
            KSPhaseState(
                ks_state.q - step * derivative.q_dot,
                ks_state.Q - step * derivative.Q_dot,
            ),
            require_zero_level=False,
        )
        finite = (plus.as_vector() - minus.as_vector()) / (2.0 * step)
        assert np.all(np.isfinite(finite))
    np.testing.assert_allclose(flow.xi_derivatives, np.zeros(3), atol=2e-13)
    np.testing.assert_allclose(
        flow.position_closure_derivative, np.zeros(3), atol=2e-14
    )
    np.testing.assert_allclose(
        flow.velocity_closure_derivative, np.zeros(3), atol=2e-14
    )
