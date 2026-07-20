"""Exact tangent conversion from qualified N3BP states to Jacobi variables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    newtonian_accelerations,
)
from src.python.threebody_reduction import JacobiPhaseState


FloatArray: TypeAlias = NDArray[np.float64]


def _readonly(value: ArrayLike, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    result = np.array(array, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class JacobiVectorField:
    """A 12D canonical Jacobi state and its physical-time derivative."""

    state: ArrayLike
    derivative: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _readonly(self.state, (12,), "state"))
        object.__setattr__(
            self,
            "derivative",
            _readonly(self.derivative, (12,), "derivative"),
        )


def jacobi_vector_field(
    state: InertialState,
    parameters: SystemParameters,
) -> JacobiVectorField:
    """Map the exact Newtonian vector field into canonical Jacobi variables."""

    jacobi = JacobiPhaseState.from_inertial(state, parameters)
    masses = parameters.masses
    m1, m2, m3 = (float(value) for value in masses)
    m12 = m1 + m2
    total = m12 + m3
    mu12 = m1 * m2 / m12
    mu3_12 = m3 * m12 / total

    accelerations = newtonian_accelerations(state.positions, parameters)
    acceleration_12 = (m1 * accelerations[0] + m2 * accelerations[1]) / m12
    rho_dot = jacobi.p_rho / mu12
    lambda_dot = jacobi.p_lambda / mu3_12
    p_rho_dot = mu12 * (accelerations[1] - accelerations[0])
    p_lambda_dot = mu3_12 * (accelerations[2] - acceleration_12)
    return JacobiVectorField(
        state=jacobi.quotient.as_canonical_vector(),
        derivative=np.concatenate(
            (rho_dot, lambda_dot, p_rho_dot, p_lambda_dot)
        ),
    )
