"""Unsoftened inertial Newtonian dynamics for exactly three point masses."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .contract import FloatArray, StateLike, SystemParameters, as_state_vector


class CollisionSingularityError(FloatingPointError):
    """Raised when two point masses occupy the same Cartesian position."""


def newtonian_accelerations(
    positions: ArrayLike,
    parameters: SystemParameters,
) -> FloatArray:
    """Return accelerations under exact, unsoftened Newtonian gravity.

    For body ``i``::

        a_i = G * sum_{j != i} m_j (r_j - r_i) / |r_j - r_i|^3

    Pair contributions are accumulated together to preserve the equal and
    opposite force structure to floating-point accuracy.
    """

    position_array = np.asarray(positions, dtype=np.float64)
    if position_array.shape != (3, 3):
        raise ValueError(
            f"positions must have shape (3, 3), got {position_array.shape}"
        )
    if not np.all(np.isfinite(position_array)):
        raise ValueError("positions must contain only finite values")

    accelerations = np.zeros((3, 3), dtype=np.float64)
    masses = parameters.masses
    gravitational_constant = parameters.gravitational_constant

    for first, second in ((0, 1), (0, 2), (1, 2)):
        displacement = position_array[second] - position_array[first]
        distance_squared = float(np.dot(displacement, displacement))
        if distance_squared == 0.0:
            raise CollisionSingularityError(
                f"bodies {first + 1} and {second + 1} are coincident"
            )
        inverse_distance_cubed = distance_squared ** -1.5
        pair_factor = gravitational_constant * inverse_distance_cubed
        accelerations[first] += pair_factor * masses[second] * displacement
        accelerations[second] -= pair_factor * masses[first] * displacement

    return accelerations


def newtonian_rhs(
    time: float,
    state: StateLike,
    parameters: SystemParameters,
) -> FloatArray:
    """Return the derivative of the explicit 18D inertial state."""

    del time  # The Newtonian point-mass system is autonomous.
    vector = as_state_vector(state)
    positions = vector[:9].reshape(3, 3)
    velocities = vector[9:].reshape(3, 3)
    accelerations = newtonian_accelerations(positions, parameters)
    return np.concatenate((velocities.ravel(), accelerations.ravel()))
