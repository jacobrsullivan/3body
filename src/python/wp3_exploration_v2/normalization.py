"""Per-system Newtonian nondimensionalization for WP3 v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import InertialState, SystemParameters
from src.python.threebody_flow import canonical_jacobi_flow
from src.python.threebody_reduction import JacobiPhaseState


FloatArray: TypeAlias = NDArray[np.float64]


def _readonly(value: ArrayLike, size: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length {size}")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class NondimensionalSystem:
    """Canonical state and flow in a system's frozen dimensionless units."""

    state: ArrayLike
    derivative: ArrayLike
    parameters: SystemParameters
    length_scale: float
    mass_scale: float
    time_scale: float
    momentum_scale: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _readonly(self.state, 12, "state"))
        object.__setattr__(
            self, "derivative", _readonly(self.derivative, 12, "derivative")
        )
        for name in ("length_scale", "mass_scale", "time_scale", "momentum_scale"):
            if not np.isfinite(getattr(self, name)) or getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be finite and positive")


def nondimensionalize(
    state: InertialState,
    parameters: SystemParameters,
    *,
    length_scale: float,
) -> NondimensionalSystem:
    """Map an inertial state into G=M=L=1 canonical Jacobi variables.

    The supplied length is frozen per source system, rather than recomputed at
    each checkpoint. Time and momentum units are then fixed by Newtonian
    similarity: T=sqrt(L^3/(G M)) and P=M L/T.
    """

    gravity = float(parameters.gravitational_constant)
    mass_scale = float(np.sum(parameters.masses))
    length_scale = float(length_scale)
    if gravity <= 0.0 or mass_scale <= 0.0 or length_scale <= 0.0:
        raise ValueError("G, total mass, and length scale must be positive")
    time_scale = float(np.sqrt(length_scale**3 / (gravity * mass_scale)))
    momentum_scale = mass_scale * length_scale / time_scale
    physical = JacobiPhaseState.from_inertial(state, parameters).quotient
    rho, lambda_vector, p_rho, p_lambda = physical.as_canonical_vector().reshape(
        4, 3
    )
    dimensionless_state = np.concatenate(
        (
            rho / length_scale,
            lambda_vector / length_scale,
            p_rho / momentum_scale,
            p_lambda / momentum_scale,
        )
    )
    dimensionless_parameters = SystemParameters(
        np.asarray(parameters.masses, dtype=np.float64) / mass_scale,
        gravitational_constant=1.0,
    )
    flow = canonical_jacobi_flow(dimensionless_state, dimensionless_parameters)
    return NondimensionalSystem(
        state=flow.state,
        derivative=flow.derivative,
        parameters=dimensionless_parameters,
        length_scale=length_scale,
        mass_scale=mass_scale,
        time_scale=time_scale,
        momentum_scale=momentum_scale,
    )
