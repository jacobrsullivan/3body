"""State and parameter contracts for the full Newtonian three-body problem."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray: TypeAlias = NDArray[np.float64]
STATE_SIZE = 18
BODY_COUNT = 3
SPACE_DIMENSION = 3


def _readonly_float64(
    value: ArrayLike,
    shape: tuple[int, ...],
    name: str,
) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    result = np.array(array, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class SystemParameters:
    """Physical parameters for three positive point masses."""

    masses: ArrayLike
    gravitational_constant: float = 1.0

    def __post_init__(self) -> None:
        masses = _readonly_float64(self.masses, (BODY_COUNT,), "masses")
        if np.any(masses <= 0.0):
            raise ValueError("all masses must be strictly positive")

        gravitational_constant = float(self.gravitational_constant)
        if not np.isfinite(gravitational_constant) or gravitational_constant <= 0.0:
            raise ValueError("gravitational_constant must be finite and positive")

        object.__setattr__(self, "masses", masses)
        object.__setattr__(self, "gravitational_constant", gravitational_constant)

    @property
    def total_mass(self) -> float:
        return float(np.sum(self.masses))


@dataclass(frozen=True)
class InertialState:
    """Immutable 18D inertial Cartesian state.

    Ordering is position-major followed by velocity-major::

        [r1x, r1y, r1z, r2x, r2y, r2z, r3x, r3y, r3z,
         v1x, v1y, v1z, v2x, v2y, v2z, v3x, v3y, v3z]

    The contract does not imply a center-of-mass frame. Planar states are
    represented in the same 18D schema with all z components equal to zero.
    """

    values: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _readonly_float64(self.values, (STATE_SIZE,), "state"),
        )

    @classmethod
    def from_components(
        cls,
        positions: ArrayLike,
        velocities: ArrayLike,
    ) -> "InertialState":
        position_array = np.asarray(positions, dtype=np.float64)
        velocity_array = np.asarray(velocities, dtype=np.float64)
        if position_array.shape != (BODY_COUNT, SPACE_DIMENSION):
            raise ValueError(
                "positions must have shape (3, 3), "
                f"got {position_array.shape}"
            )
        if velocity_array.shape != (BODY_COUNT, SPACE_DIMENSION):
            raise ValueError(
                "velocities must have shape (3, 3), "
                f"got {velocity_array.shape}"
            )
        return cls(np.concatenate((position_array.ravel(), velocity_array.ravel())))

    @property
    def positions(self) -> FloatArray:
        return self.values[:9].reshape(BODY_COUNT, SPACE_DIMENSION)

    @property
    def velocities(self) -> FloatArray:
        return self.values[9:].reshape(BODY_COUNT, SPACE_DIMENSION)

    def as_vector(self, *, copy: bool = True) -> FloatArray:
        if copy:
            return np.array(self.values, copy=True)
        return self.values


StateLike: TypeAlias = InertialState | ArrayLike


def as_state_vector(state: StateLike, *, copy: bool = False) -> FloatArray:
    """Validate a state-like object and return its 18D float64 vector."""

    if isinstance(state, InertialState):
        return state.as_vector(copy=copy)

    array = np.asarray(state, dtype=np.float64)
    if array.shape != (STATE_SIZE,):
        raise ValueError(f"state must have shape ({STATE_SIZE},), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError("state must contain only finite values")
    return np.array(array, copy=True) if copy else array
