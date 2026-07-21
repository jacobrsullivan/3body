"""Canonical two-spinor atlas for isolated N3BP binary collisions.

For one local body ordering ``(a, b, c)``, the two canonical relative pairs
are ``X1=r_a-r_c, W1=p_a`` and ``X2=r_b-r_c, W2=p_b`` on the zero-total-
momentum translation quotient.  Each pair is lifted with the qualified KS
cotangent convention.  The extended Hamiltonian uses the same global clock
in every chart,

``K = r1*r2*r3*(H+p_t)``,  ``dt/ds = r1*r2*r3``.

The selected two collision divisors are smooth.  Three central-body charts
cover every isolated binary collision.  The unregularized edge of a chart and
triple collision are explicit chart-domain boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.ks import (
    KSPhaseState,
    KeplerPhaseState,
    cotangent_projection_jacobian,
    fiber_generator,
    ks_jacobian,
    ks_position,
    lift_cotangent,
    project_cotangent,
    s1_action,
)
from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    linear_momentum,
    total_energy,
)


FloatArray: TypeAlias = NDArray[np.float64]

# Local order is (a, b, c), where c is the central body and both c-edges are
# represented by KS spinors.  Body indices are zero based.
CHART_LOCAL_ORDER: Mapping[str, tuple[int, int, int]] = {
    "central-1": (1, 2, 0),
    "central-2": (2, 0, 1),
    "central-3": (0, 1, 2),
}


class ChartDomainError(ValueError):
    """Raised when a state reaches a collision not regularized by its chart."""


class TripleCollisionOutOfScope(ChartDomainError):
    """Raised when two pair distances identify an out-of-scope triple collision."""


def _vector(value: ArrayLike, size: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length {size}")
    result = np.array(array, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


def _chart_order(chart: str) -> tuple[int, int, int]:
    try:
        return CHART_LOCAL_ORDER[chart]
    except KeyError as error:
        raise ValueError(f"unknown WP2-MULTI chart: {chart}") from error


@dataclass(frozen=True)
class MultiKSState:
    """Extended canonical state ``(q1,q2,t,P1,P2,p_t)`` in one chart."""

    chart: str
    q1: ArrayLike
    q2: ArrayLike
    physical_time: float
    P1: ArrayLike
    P2: ArrayLike
    p_t: float

    def __post_init__(self) -> None:
        _chart_order(self.chart)
        object.__setattr__(self, "q1", _vector(self.q1, 4, "q1"))
        object.__setattr__(self, "q2", _vector(self.q2, 4, "q2"))
        object.__setattr__(self, "P1", _vector(self.P1, 4, "P1"))
        object.__setattr__(self, "P2", _vector(self.P2, 4, "P2"))
        for name in ("physical_time", "p_t"):
            value = float(getattr(self, name))
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, value)

    @classmethod
    def from_vector(cls, chart: str, value: ArrayLike) -> "MultiKSState":
        vector = _vector(value, 18, "state")
        return cls(
            chart=chart,
            q1=vector[:4],
            q2=vector[4:8],
            physical_time=float(vector[8]),
            P1=vector[9:13],
            P2=vector[13:17],
            p_t=float(vector[17]),
        )

    @property
    def ks1(self) -> KSPhaseState:
        return KSPhaseState(self.q1, self.P1)

    @property
    def ks2(self) -> KSPhaseState:
        return KSPhaseState(self.q2, self.P2)

    @property
    def momentum_maps(self) -> FloatArray:
        return np.array([self.ks1.xi, self.ks2.xi])

    @property
    def energy(self) -> float:
        return -self.p_t

    def as_vector(self) -> FloatArray:
        return np.concatenate(
            (
                self.q1,
                self.q2,
                [self.physical_time],
                self.P1,
                self.P2,
                [self.p_t],
            )
        )


@dataclass(frozen=True)
class MultiKSFlow:
    """Hamiltonian derivative in the extended canonical ordering."""

    state: MultiKSState
    derivative: ArrayLike
    hamiltonian: float
    time_rate: float
    momentum_map_derivatives: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "derivative", _vector(self.derivative, 18, "derivative")
        )
        object.__setattr__(
            self,
            "momentum_map_derivatives",
            _vector(self.momentum_map_derivatives, 2, "momentum_map_derivatives"),
        )
        if not np.isfinite(self.hamiltonian):
            raise ValueError("hamiltonian must be finite")
        if not np.isfinite(self.time_rate) or self.time_rate < 0.0:
            raise ValueError("time_rate must be finite and non-negative")


@dataclass(frozen=True)
class _ChartData:
    order: tuple[int, int, int]
    m_a: float
    m_b: float
    m_c: float
    mu1: float
    mu2: float
    k1: float
    k2: float
    k3: float
    total_mass: float


def _chart_data(chart: str, parameters: SystemParameters) -> _ChartData:
    order = _chart_order(chart)
    m_a, m_b, m_c = (float(parameters.masses[index]) for index in order)
    gravity = float(parameters.gravitational_constant)
    return _ChartData(
        order=order,
        m_a=m_a,
        m_b=m_b,
        m_c=m_c,
        mu1=m_a * m_c / (m_a + m_c),
        mu2=m_b * m_c / (m_b + m_c),
        k1=gravity * m_a * m_c,
        k2=gravity * m_b * m_c,
        k3=gravity * m_a * m_b,
        total_mass=m_a + m_b + m_c,
    )


def _configuration(
    state: MultiKSState,
    *,
    unregularized_floor: float = 0.0,
) -> tuple[FloatArray, FloatArray, FloatArray, float, float, float]:
    if unregularized_floor < 0.0 or not np.isfinite(unregularized_floor):
        raise ValueError("unregularized_floor must be finite and non-negative")
    X1 = ks_position(state.q1)
    X2 = ks_position(state.q2)
    difference = X1 - X2
    r1 = state.ks1.radius
    r2 = state.ks2.radius
    r3 = float(np.linalg.norm(difference))
    if r3 <= unregularized_floor:
        if r1 <= unregularized_floor or r2 <= unregularized_floor:
            raise TripleCollisionOutOfScope(
                "two simultaneous pair collisions are an out-of-scope triple collision"
            )
        raise ChartDomainError(
            "the active chart does not regularize its a-b edge; transition charts first"
        )
    return X1, X2, difference, r1, r2, r3


def pair_distances(state: MultiKSState) -> dict[str, float]:
    """Return original-body pair distances for chart selection and diagnostics."""

    _, _, _, r1, r2, r3 = _configuration(state)
    a, b, c = _chart_order(state.chart)
    return {
        "12": _edge_distance({0, 1}, a, b, c, r1, r2, r3),
        "23": _edge_distance({1, 2}, a, b, c, r1, r2, r3),
        "31": _edge_distance({0, 2}, a, b, c, r1, r2, r3),
    }


def _edge_distance(
    pair: set[int],
    a: int,
    b: int,
    c: int,
    r1: float,
    r2: float,
    r3: float,
) -> float:
    if pair == {a, c}:
        return r1
    if pair == {b, c}:
        return r2
    return r3


def ordered_pair_distances(state: MultiKSState) -> FloatArray:
    """Return distances in fixed ``(r12,r23,r31)`` order."""

    _, _, _, r1, r2, r3 = _configuration(state)
    a, b, c = _chart_order(state.chart)
    return np.array(
        [
            _edge_distance({0, 1}, a, b, c, r1, r2, r3),
            _edge_distance({1, 2}, a, b, c, r1, r2, r3),
            _edge_distance({0, 2}, a, b, c, r1, r2, r3),
        ]
    )


def global_time_rate(state: MultiKSState) -> float:
    """Evaluate the chart-independent Heggie clock ``r12*r23*r31``."""

    distances = ordered_pair_distances(state)
    return float(np.prod(distances))


def regularized_hamiltonian(
    state: MultiKSState,
    parameters: SystemParameters,
) -> float:
    """Evaluate ``K=r12*r23*r31*(H+p_t)`` without selected collision poles."""

    data = _chart_data(state.chart, parameters)
    _, _, _, r1, r2, r3 = _configuration(state)
    J1P1 = ks_jacobian(state.q1) @ state.P1
    J2P2 = ks_jacobian(state.q2) @ state.P2
    first = np.dot(state.P1, state.P1) / (8.0 * data.mu1) - data.k1
    second = np.dot(state.P2, state.P2) / (8.0 * data.mu2) - data.k2
    cross = np.dot(J1P1, J2P2) / (16.0 * data.m_c)
    F = r2 * first + r1 * second + cross + state.p_t * r1 * r2
    return float(r3 * F - data.k3 * r1 * r2)


def vector_field(
    state: MultiKSState,
    parameters: SystemParameters,
) -> MultiKSFlow:
    """Evaluate the complete analytic extended-canonical Hamiltonian field."""

    data = _chart_data(state.chart, parameters)
    _, _, difference, r1, r2, r3 = _configuration(state)
    J1 = ks_jacobian(state.q1)
    J2 = ks_jacobian(state.q2)
    A1 = J1 @ state.P1
    A2 = J2 @ state.P2
    first = np.dot(state.P1, state.P1) / (8.0 * data.mu1) - data.k1
    second = np.dot(state.P2, state.P2) / (8.0 * data.mu2) - data.k2
    cross = np.dot(A1, A2) / (16.0 * data.m_c)
    F = r2 * first + r1 * second + cross + state.p_t * r1 * r2

    q1_dot = r3 * (
        r2 * state.P1 / (4.0 * data.mu1) + J1.T @ A2 / (16.0 * data.m_c)
    )
    q2_dot = r3 * (
        r1 * state.P2 / (4.0 * data.mu2) + J2.T @ A1 / (16.0 * data.m_c)
    )

    unit_difference = difference / r3
    dr3_q1 = J1.T @ unit_difference
    dr3_q2 = -(J2.T @ unit_difference)
    dF_q1 = (
        2.0 * state.q1 * (second + state.p_t * r2)
        + ks_jacobian(state.P1).T @ A2 / (16.0 * data.m_c)
    )
    dF_q2 = (
        2.0 * state.q2 * (first + state.p_t * r1)
        + ks_jacobian(state.P2).T @ A1 / (16.0 * data.m_c)
    )
    gradient_q1 = dr3_q1 * F + r3 * dF_q1 - 2.0 * data.k3 * r2 * state.q1
    gradient_q2 = dr3_q2 * F + r3 * dF_q2 - 2.0 * data.k3 * r1 * state.q2
    P1_dot = -gradient_q1
    P2_dot = -gradient_q2
    time_rate = r1 * r2 * r3
    derivative = np.concatenate(
        (q1_dot, q2_dot, [time_rate], P1_dot, P2_dot, [0.0])
    )

    # Xi(q,P) is bilinear, so both tangent terms contribute.
    xi_derivatives = np.array(
        [
            np.dot(fiber_generator(q1_dot), state.P1)
            + np.dot(fiber_generator(state.q1), P1_dot),
            np.dot(fiber_generator(q2_dot), state.P2)
            + np.dot(fiber_generator(state.q2), P2_dot),
        ]
    )
    return MultiKSFlow(
        state=state,
        derivative=derivative,
        hamiltonian=regularized_hamiltonian(state, parameters),
        time_rate=time_rate,
        momentum_map_derivatives=xi_derivatives,
    )


def lift_inertial_state(
    state: InertialState,
    parameters: SystemParameters,
    chart: str,
    *,
    angles: Sequence[float] = (0.0, 0.0),
    physical_time: float = 0.0,
    p_t: float | None = None,
    momentum_tolerance: float = 1e-11,
) -> MultiKSState:
    """Lift a zero-total-momentum inertial state into one atlas chart."""

    if len(angles) != 2 or not np.all(np.isfinite(angles)):
        raise ValueError("angles must contain two finite gauge angles")
    momentum = linear_momentum(state, parameters)
    momentum_scale = max(
        1.0,
        float(np.sum(parameters.masses[:, None] * np.abs(state.velocities))),
    )
    if np.linalg.norm(momentum) > momentum_tolerance * momentum_scale:
        raise ValueError("WP2-MULTI charts require the zero-momentum quotient")
    a, b, c = _chart_order(chart)
    positions = state.positions
    physical_momenta = parameters.masses[:, None] * state.velocities
    pair1 = KeplerPhaseState(positions[a] - positions[c], physical_momenta[a])
    pair2 = KeplerPhaseState(positions[b] - positions[c], physical_momenta[b])
    ks1 = lift_cotangent(pair1, angle=float(angles[0]), momentum_level=0.0)
    ks2 = lift_cotangent(pair2, angle=float(angles[1]), momentum_level=0.0)
    temporal_momentum = -total_energy(state, parameters) if p_t is None else float(p_t)
    return MultiKSState(
        chart=chart,
        q1=ks1.q,
        q2=ks2.q,
        physical_time=physical_time,
        P1=ks1.Q,
        P2=ks2.Q,
        p_t=temporal_momentum,
    )


def _local_physical_pairs(state: MultiKSState) -> tuple[KeplerPhaseState, KeplerPhaseState]:
    return project_cotangent(state.ks1), project_cotangent(state.ks2)


def project_state(
    state: MultiKSState,
    parameters: SystemParameters,
) -> InertialState:
    """Project a noncollision zero-Xi chart state to barycentric inertial form."""

    first, second = _local_physical_pairs(state)
    data = _chart_data(state.chart, parameters)
    central_position = -(
        data.m_a * first.x + data.m_b * second.x
    ) / data.total_mass
    positions_local = np.stack(
        (central_position + first.x, central_position + second.x, central_position)
    )
    momenta_local = np.stack((first.p, second.p, -first.p - second.p))
    velocities_local = momenta_local / np.array(
        [data.m_a, data.m_b, data.m_c]
    )[:, None]
    positions = np.empty((3, 3), dtype=np.float64)
    velocities = np.empty((3, 3), dtype=np.float64)
    for local_index, original_index in enumerate(data.order):
        positions[original_index] = positions_local[local_index]
        velocities[original_index] = velocities_local[local_index]
    return InertialState.from_components(positions, velocities)


def project_positions(
    state: MultiKSState,
    parameters: SystemParameters,
) -> FloatArray:
    """Project positions even when one selected KS spinor is at collision."""

    data = _chart_data(state.chart, parameters)
    X1 = ks_position(state.q1)
    X2 = ks_position(state.q2)
    central = -(data.m_a * X1 + data.m_b * X2) / data.total_mass
    local = np.stack((central + X1, central + X2, central))
    positions = np.empty((3, 3), dtype=np.float64)
    for local_index, original_index in enumerate(data.order):
        positions[original_index] = local[local_index]
    return positions


def project_derivative(
    flow: MultiKSFlow,
    parameters: SystemParameters,
) -> FloatArray:
    """Push an away-from-collision chart derivative to the 18D inertial state."""

    state = flow.state
    first = cotangent_projection_jacobian(state.ks1) @ np.concatenate(
        (flow.derivative[:4], flow.derivative[9:13])
    )
    second = cotangent_projection_jacobian(state.ks2) @ np.concatenate(
        (flow.derivative[4:8], flow.derivative[13:17])
    )
    data = _chart_data(state.chart, parameters)
    X1_dot, W1_dot = first[:3], first[3:]
    X2_dot, W2_dot = second[:3], second[3:]
    central_dot = -(data.m_a * X1_dot + data.m_b * X2_dot) / data.total_mass
    position_derivative_local = np.stack(
        (central_dot + X1_dot, central_dot + X2_dot, central_dot)
    )
    momentum_derivative_local = np.stack((W1_dot, W2_dot, -W1_dot - W2_dot))
    velocity_derivative_local = momentum_derivative_local / np.array(
        [data.m_a, data.m_b, data.m_c]
    )[:, None]
    positions = np.empty((3, 3), dtype=np.float64)
    velocities = np.empty((3, 3), dtype=np.float64)
    for local_index, original_index in enumerate(data.order):
        positions[original_index] = position_derivative_local[local_index]
        velocities[original_index] = velocity_derivative_local[local_index]
    return np.concatenate((positions.ravel(), velocities.ravel()))


def torus_action(
    state: MultiKSState,
    angles: Sequence[float],
) -> MultiKSState:
    """Apply the independent cotangent ``S1 x S1`` action."""

    if len(angles) != 2 or not np.all(np.isfinite(angles)):
        raise ValueError("angles must contain two finite values")
    first = s1_action(state.ks1, float(angles[0]))
    second = s1_action(state.ks2, float(angles[1]))
    return MultiKSState(
        chart=state.chart,
        q1=first.q,
        q2=second.q,
        physical_time=state.physical_time,
        P1=first.Q,
        P2=second.Q,
        p_t=state.p_t,
    )


def transition_chart(
    state: MultiKSState,
    parameters: SystemParameters,
    target_chart: str,
    *,
    angles: Sequence[float] = (0.0, 0.0),
) -> MultiKSState:
    """Change atlas charts through the common physical quotient."""

    if target_chart == state.chart:
        return torus_action(state, angles)
    physical = project_state(state, parameters)
    return lift_inertial_state(
        physical,
        parameters,
        target_chart,
        angles=angles,
        physical_time=state.physical_time,
        p_t=state.p_t,
    )


def collision_shell_state(
    parameters: SystemParameters,
    chart: str,
    selected_edge: int,
    *,
    other_q: ArrayLike,
    collision_direction: ArrayLike,
    other_momentum: ArrayLike | None = None,
    physical_time: float = 0.0,
    energy: float = -1.0,
) -> MultiKSState:
    """Construct an exact isolated-binary point on ``K=Xi1=Xi2=0``."""

    if selected_edge not in (1, 2):
        raise ValueError("selected_edge must be 1 or 2")
    data = _chart_data(chart, parameters)
    q_other = _vector(other_q, 4, "other_q")
    if float(np.dot(q_other, q_other)) == 0.0:
        raise TripleCollisionOutOfScope("the noncolliding KS edge must remain nonzero")
    direction = _vector(collision_direction, 4, "collision_direction")
    direction_norm = float(np.linalg.norm(direction))
    if direction_norm == 0.0:
        raise ValueError("collision_direction must be nonzero")
    other_P = (
        np.zeros(4, dtype=np.float64)
        if other_momentum is None
        else _vector(other_momentum, 4, "other_momentum")
    )
    if abs(KSPhaseState(q_other, other_P).xi) > 2e-12:
        raise ValueError("other edge must lie on Xi=0")
    mu = data.mu1 if selected_edge == 1 else data.mu2
    kappa = data.k1 if selected_edge == 1 else data.k2
    collision_P = direction / direction_norm * np.sqrt(8.0 * mu * kappa)
    if selected_edge == 1:
        q1, q2, P1, P2 = np.zeros(4), q_other, collision_P, other_P
    else:
        q1, q2, P1, P2 = q_other, np.zeros(4), other_P, collision_P
    return MultiKSState(
        chart=chart,
        q1=q1,
        q2=q2,
        physical_time=physical_time,
        P1=P1,
        P2=P2,
        p_t=-float(energy),
    )
