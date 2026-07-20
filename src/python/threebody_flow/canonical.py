"""Exact physical-time Hamiltonian flow in canonical Jacobi coordinates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import SystemParameters
from src.python.threebody_reduction import TranslationQuotientState


FloatArray: TypeAlias = NDArray[np.float64]


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


def _parts(state: ArrayLike) -> tuple[FloatArray, ...]:
    vector = _vector(state, 12, "state")
    return tuple(np.array(part, copy=True) for part in vector.reshape(4, 3))


def _pair_vectors(
    rho: FloatArray,
    lambda_vector: FloatArray,
    m1: float,
    m2: float,
    m12: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    return (
        rho,
        lambda_vector - (m1 / m12) * rho,
        -lambda_vector - (m2 / m12) * rho,
    )


def jacobi_hamiltonian(state: ArrayLike, parameters: SystemParameters) -> float:
    """Evaluate the translation-reduced Newtonian Hamiltonian."""

    rho, lambda_vector, p_rho, p_lambda = _parts(state)
    m1, m2, m3, m12, mu12, mu3_12 = _mass_data(parameters)
    x12, x23, x31 = _pair_vectors(rho, lambda_vector, m1, m2, m12)
    gravity = float(parameters.gravitational_constant)
    kinetic = float(np.dot(p_rho, p_rho) / (2.0 * mu12)) + float(
        np.dot(p_lambda, p_lambda) / (2.0 * mu3_12)
    )
    potential = -gravity * (
        m1 * m2 / np.linalg.norm(x12)
        + m2 * m3 / np.linalg.norm(x23)
        + m3 * m1 / np.linalg.norm(x31)
    )
    return float(kinetic + potential)


@dataclass(frozen=True)
class CanonicalJacobiFlow:
    """One canonical Jacobi state and its exact Hamiltonian derivative."""

    state: ArrayLike
    derivative: ArrayLike
    hamiltonian: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _vector(self.state, 12, "state"))
        object.__setattr__(
            self, "derivative", _vector(self.derivative, 12, "derivative")
        )
        if not np.isfinite(self.hamiltonian):
            raise ValueError("hamiltonian must be finite")


def canonical_jacobi_flow(
    state: ArrayLike | TranslationQuotientState,
    parameters: SystemParameters | None = None,
) -> CanonicalJacobiFlow:
    """Evaluate Hamilton's equations for the collision-free N3BP quotient."""

    if isinstance(state, TranslationQuotientState):
        if parameters is not None and parameters is not state.parameters:
            if not np.array_equal(parameters.masses, state.parameters.masses):
                raise ValueError("state and explicit parameters disagree")
        parameters = state.parameters
        state_vector = state.as_canonical_vector()
    else:
        if parameters is None:
            raise ValueError("parameters are required for an array state")
        state_vector = _vector(state, 12, "state")
    assert parameters is not None
    rho, lambda_vector, p_rho, p_lambda = _parts(state_vector)
    m1, m2, m3, m12, mu12, mu3_12 = _mass_data(parameters)
    x12, x23, x31 = _pair_vectors(rho, lambda_vector, m1, m2, m12)
    for name, pair in zip(("x12", "x23", "x31"), (x12, x23, x31), strict=True):
        if np.linalg.norm(pair) == 0.0:
            raise ZeroDivisionError(f"canonical Jacobi flow is singular at {name}=0")
    gravity = float(parameters.gravitational_constant)
    f12 = gravity * m1 * m2 * x12 / np.linalg.norm(x12) ** 3
    f23 = gravity * m2 * m3 * x23 / np.linalg.norm(x23) ** 3
    f31 = gravity * m3 * m1 * x31 / np.linalg.norm(x31) ** 3
    rho_dot = p_rho / mu12
    lambda_dot = p_lambda / mu3_12
    p_rho_dot = -f12 + (m1 / m12) * f23 + (m2 / m12) * f31
    p_lambda_dot = -f23 + f31
    derivative = np.concatenate(
        (rho_dot, lambda_dot, p_rho_dot, p_lambda_dot)
    )
    return CanonicalJacobiFlow(
        state=state_vector,
        derivative=derivative,
        hamiltonian=jacobi_hamiltonian(state_vector, parameters),
    )
