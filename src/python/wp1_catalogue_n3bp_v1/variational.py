"""Analytic planar variational flow and Kapela-Simo stability classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from .model import (
    CatalogueCandidate,
    FloatArray,
    OrbitParameters,
    StabilityResult,
    planar_state,
    state_from_parameters,
)


@dataclass(frozen=True, slots=True)
class StabilitySettings:
    rtol: float = 2.0e-11
    atol: float = 2.0e-13
    max_step_fraction: float = 1.0 / 256.0
    boundary_guard: float = 2.0e-4


def planar_rhs(
    _time: float, state: NDArray[np.float64], masses: Sequence[float]
) -> FloatArray:
    y = np.asarray(state, dtype=np.float64)
    mass = np.asarray(masses, dtype=np.float64)
    if y.shape != (12,) or mass.shape != (3,):
        raise ValueError("planar state and masses must have shapes (12,) and (3,)")
    positions = y[:6].reshape(3, 2)
    velocities = y[6:].reshape(3, 2)
    accelerations = np.zeros((3, 2), dtype=np.float64)
    for i in range(3):
        for j in range(i + 1, 3):
            delta = positions[j] - positions[i]
            distance_squared = float(delta @ delta)
            if distance_squared <= 0.0:
                raise ValueError("collision encountered during planar propagation")
            inverse_cube = distance_squared ** -1.5
            accelerations[i] += mass[j] * delta * inverse_cube
            accelerations[j] -= mass[i] * delta * inverse_cube
    return np.concatenate((velocities.reshape(-1), accelerations.reshape(-1)))


def planar_variational_jacobian(
    state: NDArray[np.float64], masses: Sequence[float]
) -> FloatArray:
    """Analytic 12D inertial Jacobian in planar position-velocity ordering."""

    y = np.asarray(state, dtype=np.float64)
    mass = np.asarray(masses, dtype=np.float64)
    if y.shape != (12,) or mass.shape != (3,):
        raise ValueError("planar state and masses must have shapes (12,) and (3,)")
    if np.any(mass <= 0.0):
        raise ValueError("masses must be positive")

    positions = y[:6].reshape(3, 2)
    acceleration_jacobian = np.zeros((6, 6), dtype=np.float64)
    identity = np.eye(2, dtype=np.float64)
    for i in range(3):
        for j in range(i + 1, 3):
            delta = positions[j] - positions[i]
            distance_squared = float(delta @ delta)
            if distance_squared <= 0.0:
                raise ValueError("variational Jacobian is undefined at collision")
            inverse_cube = distance_squared ** -1.5
            tidal = inverse_cube * (
                identity - 3.0 * np.outer(delta, delta) / distance_squared
            )
            i_slice = slice(2 * i, 2 * i + 2)
            j_slice = slice(2 * j, 2 * j + 2)
            acceleration_jacobian[i_slice, i_slice] -= mass[j] * tidal
            acceleration_jacobian[i_slice, j_slice] += mass[j] * tidal
            acceleration_jacobian[j_slice, i_slice] += mass[i] * tidal
            acceleration_jacobian[j_slice, j_slice] -= mass[i] * tidal

    jacobian = np.zeros((12, 12), dtype=np.float64)
    jacobian[:6, 6:] = np.eye(6, dtype=np.float64)
    jacobian[6:, :6] = acceleration_jacobian
    return jacobian


def integrate_planar_monodromy(
    parameters: OrbitParameters,
    settings: StabilitySettings = StabilitySettings(),
) -> FloatArray:
    initial_state = planar_state(state_from_parameters(parameters))
    augmented_initial = np.concatenate(
        (initial_state, np.eye(12, dtype=np.float64).reshape(-1))
    )

    def augmented_rhs(time: float, augmented: NDArray[np.float64]) -> FloatArray:
        state = augmented[:12]
        transition = augmented[12:].reshape(12, 12)
        derivative = planar_rhs(time, state, parameters.masses)
        tangent = planar_variational_jacobian(state, parameters.masses) @ transition
        return np.concatenate((derivative, tangent.reshape(-1)))

    solution = solve_ivp(
        augmented_rhs,
        (0.0, parameters.period),
        augmented_initial,
        method="DOP853",
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=parameters.period * settings.max_step_fraction,
    )
    if not solution.success:
        raise RuntimeError(f"variational DOP853 propagation failed: {solution.message}")
    return np.asarray(solution.y[12:, -1], dtype=np.float64).reshape(12, 12)


def canonical_jacobi_transform(masses: Sequence[float]) -> FloatArray:
    """Map ``(q1,q2,q3,p1,p2,p3)`` to canonical COM/Jacobi variables."""

    m1, m2, m3 = (float(value) for value in masses)
    if min(m1, m2, m3) <= 0.0:
        raise ValueError("masses must be positive")
    m12 = m1 + m2
    total = m12 + m3
    coordinate = np.array(
        [
            [m1 / total, m2 / total, m3 / total],
            [-1.0, 1.0, 0.0],
            [-m1 / m12, -m2 / m12, 1.0],
        ],
        dtype=np.float64,
    )
    momentum = np.array(
        [
            [1.0, 1.0, 1.0],
            [-m2 / m12, m1 / m12, 0.0],
            [-m3 / total, -m3 / total, m12 / total],
        ],
        dtype=np.float64,
    )
    transform = np.zeros((12, 12), dtype=np.float64)
    transform[:6, :6] = np.kron(coordinate, np.eye(2))
    transform[6:, 6:] = np.kron(momentum, np.eye(2))
    return transform


def project_translation_quotient_monodromy(
    inertial_velocity_monodromy: NDArray[np.float64], masses: Sequence[float]
) -> FloatArray:
    """Convert a 12D ``(q,v)`` STM to the canonical 8D translation quotient."""

    transition = np.asarray(inertial_velocity_monodromy, dtype=np.float64)
    mass = np.asarray(masses, dtype=np.float64)
    if transition.shape != (12, 12) or mass.shape != (3,):
        raise ValueError("monodromy and masses must have shapes (12,12) and (3,)")
    momentum_lift = np.eye(12, dtype=np.float64)
    momentum_lift[6:, 6:] = np.diag(np.repeat(mass, 2))
    canonical_inertial = (
        momentum_lift @ transition @ np.linalg.inv(momentum_lift)
    )
    jacobi = canonical_jacobi_transform(mass)
    jacobi_transition = jacobi @ canonical_inertial @ np.linalg.inv(jacobi)
    quotient_indices = np.array([2, 3, 4, 5, 8, 9, 10, 11], dtype=np.intp)
    return jacobi_transition[np.ix_(quotient_indices, quotient_indices)]


def _symplectic_matrix(dimension: int) -> FloatArray:
    if dimension % 2:
        raise ValueError("symplectic dimension must be even")
    half = dimension // 2
    return np.block(
        [
            [np.zeros((half, half)), np.eye(half)],
            [-np.eye(half), np.zeros((half, half))],
        ]
    )


def _reciprocal_pair_error(multipliers: NDArray[np.complex128]) -> float:
    remaining = list(range(len(multipliers)))
    errors: list[float] = []
    while remaining:
        first = remaining.pop(0)
        partner = min(
            remaining,
            key=lambda index: abs(multipliers[first] * multipliers[index] - 1.0),
        )
        remaining.remove(partner)
        errors.append(float(abs(multipliers[first] * multipliers[partner] - 1.0)))
    return max(errors, default=0.0)


def classify_reduced_monodromy(
    reduced_monodromy: NDArray[np.float64], boundary_guard: float = 2.0e-4
) -> StabilityResult:
    """Apply the Kapela-Simo trace/minor criterion to an 8D symplectic map."""

    monodromy = np.asarray(reduced_monodromy, dtype=np.float64)
    if monodromy.shape != (8, 8):
        raise ValueError("translation-quotient monodromy must have shape (8,8)")
    trace = float(np.trace(monodromy))
    second = float(0.5 * (trace * trace - np.trace(monodromy @ monodromy)))
    linear = trace - 4.0
    constant = second - 4.0 * trace + 8.0
    discriminant = float(linear * linear - 4.0 * constant)
    root = np.sqrt(complex(discriminant))
    reduced_traces = ((linear + root) / 2.0, (linear - root) / 2.0)

    if abs(discriminant) <= boundary_guard:
        label = "AMBIGUOUS"
    elif discriminant < 0.0:
        label = "U"
    elif any(abs(abs(value.real) - 2.0) <= boundary_guard for value in reduced_traces):
        label = "AMBIGUOUS"
    elif all(abs(value.imag) <= boundary_guard and abs(value.real) < 2.0 for value in reduced_traces):
        label = "S"
    else:
        label = "U"

    multipliers = np.asarray(np.linalg.eigvals(monodromy), dtype=np.complex128)
    symplectic = _symplectic_matrix(8)
    defect = float(
        np.linalg.norm(monodromy.T @ symplectic @ monodromy - symplectic, ord=np.inf)
    )
    return StabilityResult(
        label=label,
        trace=trace,
        second_trace_invariant=second,
        discriminant=discriminant,
        reduced_traces=reduced_traces,
        multipliers=tuple(complex(value) for value in multipliers),
        symplectic_defect=defect,
        reciprocal_pair_error=_reciprocal_pair_error(multipliers),
    )


def classify_orbit_stability(
    orbit: OrbitParameters | CatalogueCandidate,
    settings: StabilitySettings = StabilitySettings(),
) -> StabilityResult:
    parameters = (
        orbit.correction.parameters
        if isinstance(orbit, CatalogueCandidate)
        else orbit
    )
    inertial = integrate_planar_monodromy(parameters, settings)
    reduced = project_translation_quotient_monodromy(inertial, parameters.masses)
    return classify_reduced_monodromy(reduced, settings.boundary_guard)
