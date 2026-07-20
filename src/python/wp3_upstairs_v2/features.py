"""Complete combined-degree-three state/parameter feature grammar."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations_with_replacement
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import SystemParameters
from src.python.threebody_flow import canonical_jacobi_flow, jacobi_hamiltonian
from src.python.upstairs_ks import UpstairsKSState, project_state, projection_jacobian


FloatArray: TypeAlias = NDArray[np.float64]
_STATE_NAMES = (
    "q1", "q2", "q3", "q4", "lambda_x", "lambda_y", "lambda_z",
    "Q1", "Q2", "Q3", "Q4", "p_lambda_x", "p_lambda_y", "p_lambda_z",
)
_PARAMETER_NAMES = ("h", "mass_s2", "mass_s3")
_KNOWN_NAMES = ("known:H", "known:H2", "known:Lx", "known:Ly", "known:Lz", "known:L2")


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (14,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length 14")
    return array


@lru_cache(maxsize=1)
def feature_descriptors() -> tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]:
    """Return every combined-degree<=3 monomial containing a state factor."""

    descriptors = []
    for state_degree in range(1, 4):
        for state_indices in combinations_with_replacement(range(14), state_degree):
            for parameter_degree in range(0, 4 - state_degree):
                for parameter_indices in combinations_with_replacement(range(3), parameter_degree):
                    descriptors.append((state_indices, parameter_indices))
    return tuple(descriptors)


@lru_cache(maxsize=1)
def feature_names() -> tuple[str, ...]:
    names = []
    for state_indices, parameter_indices in feature_descriptors():
        factors = [_STATE_NAMES[index] for index in state_indices]
        factors.extend(_PARAMETER_NAMES[index] for index in parameter_indices)
        names.append("*".join(factors))
    names.extend(_KNOWN_NAMES)
    return tuple(names)


def known_control_coefficients() -> Mapping[str, FloatArray]:
    names = feature_names()
    output = {}
    for name in _KNOWN_NAMES:
        vector = np.zeros(len(names), dtype=np.float64)
        vector[names.index(name)] = 1.0
        output[name.removeprefix("known:")] = vector
    return output


def _monomial_value_lie(
    state: FloatArray,
    tangent: FloatArray,
    state_indices: tuple[int, ...],
    parameter_factor: float,
) -> tuple[float, float]:
    value = parameter_factor
    for index in state_indices:
        value *= float(state[index])
    lie = 0.0
    for differentiated, index in enumerate(state_indices):
        term = parameter_factor * float(tangent[index])
        for position, factor in enumerate(state_indices):
            if position != differentiated:
                term *= float(state[factor])
        lie += term
    return value, lie


@dataclass(frozen=True)
class UpstairsV2FeatureEvaluation:
    names: tuple[str, ...]
    values: FloatArray
    lie_derivatives: FloatArray

    def __post_init__(self) -> None:
        if self.values.shape != (len(self.names),) or self.lie_derivatives.shape != self.values.shape:
            raise ValueError("feature arrays do not match names")
        if not np.all(np.isfinite(self.values)) or not np.all(np.isfinite(self.lie_derivatives)):
            raise ValueError("feature evaluation must be finite")


def evaluate_upstairs_v2_features(
    state: UpstairsKSState,
    derivative: ArrayLike,
    parameters: SystemParameters,
    *,
    fixed_energy: float,
) -> UpstairsV2FeatureEvaluation:
    """Evaluate parameter-aware monomials and independently checked controls."""

    vector = state.as_vector()
    tangent = _vector(derivative, "derivative")
    masses = np.asarray(parameters.masses, dtype=np.float64)
    if not np.isfinite(fixed_energy):
        raise ValueError("fixed_energy must be finite")
    parameter_values = np.array(
        [
            float(fixed_energy),
            float(masses[0]*masses[1] + masses[1]*masses[2] + masses[2]*masses[0]),
            float(np.prod(masses)),
        ]
    )
    values, lies = [], []
    for state_indices, parameter_indices in feature_descriptors():
        parameter_factor = 1.0
        for index in parameter_indices:
            parameter_factor *= float(parameter_values[index])
        value, lie = _monomial_value_lie(vector, tangent, state_indices, parameter_factor)
        values.append(value); lies.append(lie)

    physical_vector = project_state(state)
    projected_tangent = projection_jacobian(state) @ tangent
    physical_flow = canonical_jacobi_flow(physical_vector, parameters).derivative
    hamiltonian_gradient = np.concatenate((-physical_flow[6:], physical_flow[:6]))
    hamiltonian = jacobi_hamiltonian(physical_vector, parameters)
    hamiltonian_lie = float(np.dot(hamiltonian_gradient, projected_tangent))
    rho, lambda_vector, p_rho, p_lambda = physical_vector.reshape(4, 3)
    rho_dot, lambda_dot, p_rho_dot, p_lambda_dot = projected_tangent.reshape(4, 3)
    angular = np.cross(rho, p_rho) + np.cross(lambda_vector, p_lambda)
    angular_lie = (
        np.cross(rho_dot, p_rho) + np.cross(rho, p_rho_dot)
        + np.cross(lambda_dot, p_lambda) + np.cross(lambda_vector, p_lambda_dot)
    )
    angular2 = float(np.dot(angular, angular))
    values.extend((hamiltonian, hamiltonian*hamiltonian, *angular, angular2))
    lies.extend((
        hamiltonian_lie, 2.0*hamiltonian*hamiltonian_lie,
        *angular_lie, 2.0*float(np.dot(angular, angular_lie)),
    ))
    return UpstairsV2FeatureEvaluation(
        names=feature_names(), values=np.asarray(values), lie_derivatives=np.asarray(lies)
    )
