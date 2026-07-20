"""Conserved quantities and center-of-mass operations for N3BP qualification."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .contract import (
    FloatArray,
    InertialState,
    StateLike,
    SystemParameters,
    as_state_vector,
)


def _components(state: StateLike) -> tuple[FloatArray, FloatArray]:
    vector = as_state_vector(state)
    return vector[:9].reshape(3, 3), vector[9:].reshape(3, 3)


def center_of_mass_position(
    state: StateLike,
    parameters: SystemParameters,
) -> FloatArray:
    positions, _ = _components(state)
    weighted_position = np.sum(parameters.masses[:, None] * positions, axis=0)
    return weighted_position / parameters.total_mass


def center_of_mass_velocity(
    state: StateLike,
    parameters: SystemParameters,
) -> FloatArray:
    _, velocities = _components(state)
    weighted_velocity = np.sum(parameters.masses[:, None] * velocities, axis=0)
    return weighted_velocity / parameters.total_mass


def normalize_center_of_mass(
    state: StateLike,
    parameters: SystemParameters,
) -> InertialState:
    """Apply a Galilean translation and boost to the barycentric frame."""

    positions, velocities = _components(state)
    normalized_positions = positions - center_of_mass_position(state, parameters)
    normalized_velocities = velocities - center_of_mass_velocity(state, parameters)
    return InertialState.from_components(normalized_positions, normalized_velocities)


def linear_momentum(
    state: StateLike,
    parameters: SystemParameters,
) -> FloatArray:
    _, velocities = _components(state)
    return np.sum(parameters.masses[:, None] * velocities, axis=0)


def angular_momentum(
    state: StateLike,
    parameters: SystemParameters,
) -> FloatArray:
    positions, velocities = _components(state)
    momenta = parameters.masses[:, None] * velocities
    return np.sum(np.cross(positions, momenta), axis=0)


def kinetic_energy(state: StateLike, parameters: SystemParameters) -> float:
    _, velocities = _components(state)
    return float(
        0.5 * np.sum(parameters.masses[:, None] * velocities * velocities)
    )


def potential_energy(state: StateLike, parameters: SystemParameters) -> float:
    positions, _ = _components(state)
    potential = 0.0
    for first, second in ((0, 1), (0, 2), (1, 2)):
        distance = float(np.linalg.norm(positions[second] - positions[first]))
        if distance == 0.0:
            return float("-inf")
        potential -= (
            parameters.gravitational_constant
            * parameters.masses[first]
            * parameters.masses[second]
            / distance
        )
    return potential


def total_energy(state: StateLike, parameters: SystemParameters) -> float:
    return kinetic_energy(state, parameters) + potential_energy(state, parameters)


@dataclass(frozen=True)
class ConservedQuantities:
    energy: float
    linear_momentum: FloatArray
    angular_momentum: FloatArray


def conserved_quantities(
    state: StateLike,
    parameters: SystemParameters,
) -> ConservedQuantities:
    return ConservedQuantities(
        energy=total_energy(state, parameters),
        linear_momentum=linear_momentum(state, parameters),
        angular_momentum=angular_momentum(state, parameters),
    )


@dataclass(frozen=True)
class InvariantDrift:
    max_relative_energy: float
    max_linear_momentum: float
    max_angular_momentum: float


def measure_invariant_drift(
    states: ArrayLike,
    parameters: SystemParameters,
) -> InvariantDrift:
    """Measure maximum drift from the first sample in a state sequence."""

    state_array = np.asarray(states, dtype=np.float64)
    if state_array.ndim != 2 or state_array.shape[1] != 18:
        raise ValueError(f"states must have shape (n, 18), got {state_array.shape}")
    if state_array.shape[0] < 1 or not np.all(np.isfinite(state_array)):
        raise ValueError("states must contain at least one finite sample")

    energies = np.array([total_energy(state, parameters) for state in state_array])
    momenta = np.array([linear_momentum(state, parameters) for state in state_array])
    angular = np.array([angular_momentum(state, parameters) for state in state_array])

    energy_scale = max(abs(float(energies[0])), np.finfo(np.float64).tiny)
    return InvariantDrift(
        max_relative_energy=float(
            np.max(np.abs(energies - energies[0])) / energy_scale
        ),
        max_linear_momentum=float(
            np.max(np.linalg.norm(momenta - momenta[0], axis=1))
        ),
        max_angular_momentum=float(
            np.max(np.linalg.norm(angular - angular[0], axis=1))
        ),
    )
