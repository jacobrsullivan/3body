"""Canonical fixed-energy KS lift for one Jacobi binary channel.

The physical translation-reduced state is ordered as
``(rho, lambda, p_rho, p_lambda)``.  The selected binary coordinate ``rho``
is replaced by a KS spinor while the second Jacobi pair remains Cartesian.
The upstairs canonical ordering is ``(q, lambda, Q, p_lambda)``.

For fixed physical energy ``h`` the Hamiltonian is

``K_h = |Q|^2/(8 mu_rho) - G m1 m2 + |q|^2 (T_lambda + U_23 + U_31 - h)``.

On ``K_h = Xi = 0`` it projects to the Newtonian three-body flow with
``dt/ds = |q|^2``.  The selected ``rho = 0`` collision is regular whenever
the other two pair separations remain nonzero.  This is a genuine canonical
upstairs Hamiltonian, but it is not a simultaneous three-binary regularizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.ks import (
    KSPhaseState,
    KeplerPhaseState,
    cotangent_projection_jacobian,
    ks_position,
    lift_cotangent,
    momentum_map,
    project_cotangent,
    s1_action as ks_s1_action,
)
from src.python.n3bp_qualification import SystemParameters
from src.python.threebody_flow import canonical_jacobi_flow, jacobi_hamiltonian


FloatArray: TypeAlias = NDArray[np.float64]
_UPSTAIRS_DIMENSION = 14


def _vector(value: ArrayLike, size: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length {size}")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result


def _mass_data(parameters: SystemParameters) -> tuple[float, ...]:
    m1, m2, m3 = (float(value) for value in parameters.masses)
    m12 = m1 + m2
    total = m12 + m3
    return m1, m2, m3, m12, m1 * m2 / m12, m3 * m12 / total


@dataclass(frozen=True)
class UpstairsKSState:
    """Canonical coordinates ``(q, lambda, Q, p_lambda)`` in 14 dimensions."""

    q: ArrayLike
    lambda_vector: ArrayLike
    Q: ArrayLike
    p_lambda: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(self, "q", _vector(self.q, 4, "q"))
        object.__setattr__(
            self, "lambda_vector", _vector(self.lambda_vector, 3, "lambda_vector")
        )
        object.__setattr__(self, "Q", _vector(self.Q, 4, "Q"))
        object.__setattr__(
            self, "p_lambda", _vector(self.p_lambda, 3, "p_lambda")
        )

    @classmethod
    def from_vector(cls, value: ArrayLike) -> "UpstairsKSState":
        vector = _vector(value, _UPSTAIRS_DIMENSION, "state")
        return cls(vector[:4], vector[4:7], vector[7:11], vector[11:14])

    @property
    def radius(self) -> float:
        return float(np.dot(self.q, self.q))

    @property
    def xi(self) -> float:
        return momentum_map(self.q, self.Q)

    def as_vector(self) -> FloatArray:
        return np.concatenate((self.q, self.lambda_vector, self.Q, self.p_lambda))


@dataclass(frozen=True)
class UpstairsKSShell:
    """One zero-Xi local lift together with its fixed physical energy."""

    state: UpstairsKSState
    energy: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.energy):
            raise ValueError("energy must be finite")


@dataclass(frozen=True)
class UpstairsKSFlow:
    """Hamiltonian derivative in fictitious Sundman time."""

    state: UpstairsKSState
    derivative: ArrayLike
    hamiltonian: float
    physical_time_rate: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "derivative", _vector(self.derivative, _UPSTAIRS_DIMENSION, "derivative")
        )
        if not np.isfinite(self.hamiltonian):
            raise ValueError("hamiltonian must be finite")
        if not np.isfinite(self.physical_time_rate) or self.physical_time_rate < 0.0:
            raise ValueError("physical_time_rate must be finite and non-negative")


def lift_jacobi_state(
    state: ArrayLike,
    parameters: SystemParameters,
    *,
    angle: float = 0.0,
) -> UpstairsKSShell:
    """Lift a collision-free canonical Jacobi state to ``K_h = Xi = 0``."""

    vector = _vector(state, 12, "jacobi_state")
    rho, lambda_vector, p_rho, p_lambda = vector.reshape(4, 3)
    ks = lift_cotangent(
        KeplerPhaseState(x=rho, p=p_rho), angle=float(angle), momentum_level=0.0
    )
    upstairs = UpstairsKSState(ks.q, lambda_vector, ks.Q, p_lambda)
    return UpstairsKSShell(
        state=upstairs,
        energy=jacobi_hamiltonian(vector, parameters),
    )


def project_state(state: UpstairsKSState) -> FloatArray:
    """Project a noncollision zero-Xi upstairs state to canonical Jacobi form."""

    physical = project_cotangent(KSPhaseState(state.q, state.Q))
    return np.concatenate(
        (physical.x, state.lambda_vector, physical.p, state.p_lambda)
    )


def projection_jacobian(state: UpstairsKSState) -> FloatArray:
    """Jacobian of the upstairs-to-Jacobi projection away from ``q = 0``."""

    pair = cotangent_projection_jacobian(KSPhaseState(state.q, state.Q))
    derivative = np.zeros((12, _UPSTAIRS_DIMENSION), dtype=np.float64)
    derivative[:3, :4] = pair[:3, :4]
    derivative[3:6, 4:7] = np.eye(3)
    derivative[6:9, :4] = pair[3:6, :4]
    derivative[6:9, 7:11] = pair[3:6, 4:8]
    derivative[9:12, 11:14] = np.eye(3)
    return derivative


def _interaction_data(
    state: UpstairsKSState,
    parameters: SystemParameters,
) -> tuple[float, FloatArray, FloatArray]:
    m1, m2, m3, m12, _, mu3_12 = _mass_data(parameters)
    rho = ks_position(state.q)
    x23 = state.lambda_vector - (m1 / m12) * rho
    x31 = -state.lambda_vector - (m2 / m12) * rho
    norm23 = float(np.linalg.norm(x23))
    norm31 = float(np.linalg.norm(x31))
    if norm23 == 0.0 or norm31 == 0.0:
        raise ZeroDivisionError("unregularized secondary binary collision")
    gravity = float(parameters.gravitational_constant)
    k23 = gravity * m2 * m3
    k31 = gravity * m3 * m1
    kinetic_lambda = float(np.dot(state.p_lambda, state.p_lambda) / (2.0 * mu3_12))
    scalar = kinetic_lambda - k23 / norm23 - k31 / norm31
    force23 = k23 * x23 / norm23**3
    force31 = k31 * x31 / norm31**3
    gradient_rho = -(m1 / m12) * force23 - (m2 / m12) * force31
    gradient_lambda = force23 - force31
    return scalar, gradient_rho, gradient_lambda


def regularized_hamiltonian(
    state: UpstairsKSState,
    parameters: SystemParameters,
    energy: float,
) -> float:
    """Evaluate the canonical fixed-energy Hamiltonian ``K_h``."""

    if not np.isfinite(energy):
        raise ValueError("energy must be finite")
    m1, m2, _, _, mu12, _ = _mass_data(parameters)
    interaction, _, _ = _interaction_data(state, parameters)
    k12 = float(parameters.gravitational_constant) * m1 * m2
    return float(
        np.dot(state.Q, state.Q) / (8.0 * mu12)
        - k12
        + state.radius * (interaction - float(energy))
    )


def sundman_rate(state: UpstairsKSState) -> float:
    """Return ``dt/ds = |q|^2``."""

    return state.radius


def upstairs_vector_field(
    state: UpstairsKSState,
    parameters: SystemParameters,
    energy: float,
) -> UpstairsKSFlow:
    """Evaluate Hamilton's equations for the one-channel upstairs model."""

    if not np.isfinite(energy):
        raise ValueError("energy must be finite")
    m1, m2, _, _, mu12, mu3_12 = _mass_data(parameters)
    interaction, gradient_rho, gradient_lambda = _interaction_data(state, parameters)
    radius = state.radius
    q_dot = state.Q / (4.0 * mu12)
    lambda_dot = radius * state.p_lambda / mu3_12
    q_gradient = (
        2.0 * state.q * (interaction - float(energy))
        + radius * _ks_jacobian_unchecked(state.q).T @ gradient_rho
    )
    Q_dot = -q_gradient
    p_lambda_dot = -radius * gradient_lambda
    derivative = np.concatenate((q_dot, lambda_dot, Q_dot, p_lambda_dot))
    return UpstairsKSFlow(
        state=state,
        derivative=derivative,
        hamiltonian=regularized_hamiltonian(state, parameters, energy),
        physical_time_rate=radius,
    )


def _ks_jacobian_unchecked(q: FloatArray) -> FloatArray:
    q1, q2, q3, q4 = q
    return 2.0 * np.array(
        [
            [q3, q4, q1, q2],
            [q4, -q3, -q2, q1],
            [q1, q2, -q3, -q4],
        ]
    )


def project_derivative(flow: UpstairsKSFlow) -> FloatArray:
    """Push an upstairs derivative to canonical Jacobi variables."""

    return projection_jacobian(flow.state) @ flow.derivative


def s1_action(state: UpstairsKSState, angle: float) -> UpstairsKSState:
    """Apply the KS circle action, leaving the second Jacobi pair unchanged."""

    transformed = ks_s1_action(KSPhaseState(state.q, state.Q), angle)
    return UpstairsKSState(
        transformed.q, state.lambda_vector, transformed.Q, state.p_lambda
    )


def momentum_map_derivative(flow: UpstairsKSFlow) -> float:
    """Evaluate ``dXi/ds`` from the canonical vector field."""

    q_dot = flow.derivative[:4]
    Q_dot = flow.derivative[7:11]
    q1, q2, q3, q4 = flow.state.q
    Q1, Q2, Q3, Q4 = flow.state.Q
    dq1, dq2, dq3, dq4 = q_dot
    dQ1, dQ2, dQ3, dQ4 = Q_dot
    return float(
        dq1 * Q2 + q1 * dQ2
        - dq2 * Q1 - q2 * dQ1
        + dq3 * Q4 + q3 * dQ4
        - dq4 * Q3 - q4 * dQ3
    )


def angular_momentum(state: UpstairsKSState) -> FloatArray:
    """Return the physical translation-reduced angular momentum vector."""

    physical = project_state(state)
    rho, lambda_vector, p_rho, p_lambda = physical.reshape(4, 3)
    return np.cross(rho, p_rho) + np.cross(lambda_vector, p_lambda)


def physical_projection_residual(
    flow: UpstairsKSFlow,
    parameters: SystemParameters,
) -> FloatArray:
    """Difference from the Sundman-scaled physical Hamiltonian vector field."""

    physical = project_state(flow.state)
    physical_flow = canonical_jacobi_flow(physical, parameters)
    return project_derivative(flow) - flow.physical_time_rate * physical_flow.derivative
