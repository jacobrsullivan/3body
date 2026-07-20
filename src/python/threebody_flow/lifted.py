"""Physical-time constrained pairwise KS lift of the Newtonian flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.ks import ks_jacobian
from src.python.n3bp_qualification import SystemParameters, newtonian_accelerations
from src.python.pairwise_ks import PairwiseKSResult


FloatArray: TypeAlias = NDArray[np.float64]


def _vector(value: ArrayLike, size: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length {size}")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class PairwiseKSPhaseDerivative:
    """One physical-time derivative in a selected KS gauge."""

    q_dot: ArrayLike
    Q_dot: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(self, "q_dot", _vector(self.q_dot, 4, "q_dot"))
        object.__setattr__(self, "Q_dot", _vector(self.Q_dot, 4, "Q_dot"))

    def as_vector(self) -> FloatArray:
        return np.concatenate((self.q_dot, self.Q_dot))


@dataclass(frozen=True)
class PairwiseKSFlow:
    """Redundant constrained KS flow for the three oriented physical pairs."""

    pair_derivatives: tuple[
        PairwiseKSPhaseDerivative,
        PairwiseKSPhaseDerivative,
        PairwiseKSPhaseDerivative,
    ]
    xi_derivatives: ArrayLike
    position_closure_derivative: ArrayLike
    velocity_closure_derivative: ArrayLike

    def __post_init__(self) -> None:
        if len(self.pair_derivatives) != 3:
            raise ValueError("exactly three pair derivatives are required")
        object.__setattr__(
            self, "xi_derivatives", _vector(self.xi_derivatives, 3, "xi_derivatives")
        )
        object.__setattr__(
            self,
            "position_closure_derivative",
            _vector(
                self.position_closure_derivative,
                3,
                "position_closure_derivative",
            ),
        )
        object.__setattr__(
            self,
            "velocity_closure_derivative",
            _vector(
                self.velocity_closure_derivative,
                3,
                "velocity_closure_derivative",
            ),
        )


def _fiber_generator(vector: FloatArray) -> FloatArray:
    q1, q2, q3, q4 = vector
    return np.array([-q2, q1, -q4, q3])


def pairwise_ks_flow(
    lifted: PairwiseKSResult,
    parameters: SystemParameters,
) -> PairwiseKSFlow:
    """Lift pair position/momentum derivatives without changing physical time."""

    state = lifted.reconstruct()
    accelerations = newtonian_accelerations(state.positions, parameters)
    masses = np.asarray(parameters.masses, dtype=np.float64)
    pairs = ((0, 1), (1, 2), (2, 0))
    reduced_masses = tuple(
        float(masses[first] * masses[second] / (masses[first] + masses[second]))
        for first, second in pairs
    )
    derivatives: list[PairwiseKSPhaseDerivative] = []
    xi_derivatives: list[float] = []
    position_derivatives: list[FloatArray] = []
    velocity_derivatives: list[FloatArray] = []
    physical_pairs = lifted.lift.project_pairs()
    for ks_state, physical, pair, reduced_mass in zip(
        lifted.lift.pair_states,
        physical_pairs,
        pairs,
        reduced_masses,
        strict=True,
    ):
        first, second = pair
        x_dot = state.velocities[second] - state.velocities[first]
        p_dot = reduced_mass * (accelerations[second] - accelerations[first])
        jacobian = ks_jacobian(ks_state.q)
        q_dot = jacobian.T @ x_dot / (4.0 * ks_state.radius)
        Q_dot = ks_jacobian(q_dot).T @ physical.p + jacobian.T @ p_dot
        derivative = PairwiseKSPhaseDerivative(q_dot=q_dot, Q_dot=Q_dot)
        derivatives.append(derivative)
        xi_derivatives.append(
            float(
                np.dot(_fiber_generator(q_dot), ks_state.Q)
                + np.dot(_fiber_generator(ks_state.q), Q_dot)
            )
        )
        position_derivatives.append(x_dot)
        velocity_derivatives.append(p_dot / reduced_mass)
    return PairwiseKSFlow(
        pair_derivatives=tuple(derivatives),  # type: ignore[arg-type]
        xi_derivatives=np.array(xi_derivatives),
        position_closure_derivative=sum(position_derivatives, np.zeros(3)),
        velocity_closure_derivative=sum(velocity_derivatives, np.zeros(3)),
    )
