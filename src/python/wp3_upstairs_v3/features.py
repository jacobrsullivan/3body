"""Complete degree-three grammar with an exact known module and constraint ideal."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations_with_replacement
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import SystemParameters
from src.python.upstairs_ks import UpstairsKSState


FloatArray: TypeAlias = NDArray[np.float64]
Descriptor = tuple[tuple[int, ...], tuple[int, ...]]
_STATE_NAMES = (
    "q1", "q2", "q3", "q4", "lambda_x", "lambda_y", "lambda_z",
    "Q1", "Q2", "Q3", "Q4", "p_lambda_x", "p_lambda_y", "p_lambda_z",
)
_PARAMETER_NAMES = ("h", "mass_s2", "mass_s3")


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (14,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length 14")
    return array


@lru_cache(maxsize=1)
def feature_descriptors() -> tuple[Descriptor, ...]:
    """Return all combined-degree-three-or-less monomials with a state factor."""

    descriptors: list[Descriptor] = []
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
    return tuple(names)


def parameter_values(parameters: SystemParameters, fixed_energy: float) -> FloatArray:
    masses = np.asarray(parameters.masses, dtype=np.float64)
    if not np.isfinite(fixed_energy):
        raise ValueError("fixed_energy must be finite")
    return np.asarray(
        [
            float(fixed_energy),
            float(masses[0] * masses[1] + masses[1] * masses[2] + masses[2] * masses[0]),
            float(np.prod(masses)),
        ],
        dtype=np.float64,
    )


def s1_generator(state: UpstairsKSState) -> FloatArray:
    """Return the infinitesimal simultaneous KS circle-action tangent."""

    q1, q2, q3, q4 = state.q
    Q1, Q2, Q3, Q4 = state.Q
    return np.asarray(
        [
            -q2, q1, -q4, q3,
            0.0, 0.0, 0.0,
            -Q2, Q1, -Q4, Q3,
            0.0, 0.0, 0.0,
        ],
        dtype=np.float64,
    )


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
class UpstairsV3FeatureEvaluation:
    names: tuple[str, ...]
    values: FloatArray
    lie_derivatives: FloatArray

    def __post_init__(self) -> None:
        if self.values.shape != (len(self.names),) or self.lie_derivatives.shape != self.values.shape:
            raise ValueError("feature arrays do not match names")
        if not np.all(np.isfinite(self.values)) or not np.all(np.isfinite(self.lie_derivatives)):
            raise ValueError("feature evaluation must be finite")


def evaluate_upstairs_v3_features(
    state: UpstairsKSState,
    derivative: ArrayLike,
    parameters: SystemParameters,
    *,
    fixed_energy: float,
) -> UpstairsV3FeatureEvaluation:
    vector = state.as_vector()
    tangent = _vector(derivative, "derivative")
    parameters_vector = parameter_values(parameters, fixed_energy)
    values: list[float] = []
    lies: list[float] = []
    for state_indices, parameter_indices in feature_descriptors():
        factor = 1.0
        for index in parameter_indices:
            factor *= float(parameters_vector[index])
        value, lie = _monomial_value_lie(vector, tangent, state_indices, factor)
        values.append(value)
        lies.append(lie)
    return UpstairsV3FeatureEvaluation(
        names=feature_names(),
        values=np.asarray(values, dtype=np.float64),
        lie_derivatives=np.asarray(lies, dtype=np.float64),
    )


def _coefficient_vector(terms: dict[Descriptor, float]) -> FloatArray:
    indices = {descriptor: index for index, descriptor in enumerate(feature_descriptors())}
    vector = np.zeros(len(indices), dtype=np.float64)
    for descriptor, coefficient in terms.items():
        vector[indices[descriptor]] += float(coefficient)
    return vector


def _multiply(
    terms: dict[tuple[int, ...], float],
    *,
    state_factor: int | None = None,
    parameter_factor: int | None = None,
) -> dict[Descriptor, float]:
    output: dict[Descriptor, float] = {}
    for state_indices, coefficient in terms.items():
        expanded_state = tuple(sorted((*state_indices, state_factor))) if state_factor is not None else state_indices
        expanded_parameters = (parameter_factor,) if parameter_factor is not None else ()
        output[(expanded_state, expanded_parameters)] = coefficient
    return output


@lru_cache(maxsize=1)
def known_module_coefficients() -> dict[str, FloatArray]:
    """Return the exact Xi ideal and angular-momentum parameter module.

    On the zero-momentum quotient, Xi times every combined-degree-one-or-less
    factor is the complete degree-three part of the constraint ideal. The
    degree-two angular momenta and their degree-one parameter multiples are all
    represented members of the known-integral module.
    """

    xi = {
        (0, 8): 1.0,
        (1, 7): -1.0,
        (2, 10): 1.0,
        (3, 9): -1.0,
    }
    angular = {
        "Lx": {
            (0, 10): -0.5, (1, 9): 0.5, (2, 8): -0.5, (3, 7): 0.5,
            (5, 13): 1.0, (6, 12): -1.0,
        },
        "Ly": {
            (0, 9): 0.5, (1, 10): 0.5, (2, 7): -0.5, (3, 8): -0.5,
            (6, 11): 1.0, (4, 13): -1.0,
        },
        "Lz": {
            (0, 8): -0.5, (1, 7): 0.5, (2, 10): 0.5, (3, 9): -0.5,
            (4, 12): 1.0, (5, 11): -1.0,
        },
    }
    controls: dict[str, FloatArray] = {"constraint:Xi": _coefficient_vector(_multiply(xi))}
    for state_index, name in enumerate(_STATE_NAMES):
        controls[f"constraint:Xi*{name}"] = _coefficient_vector(
            _multiply(xi, state_factor=state_index)
        )
    for parameter_index, name in enumerate(_PARAMETER_NAMES):
        controls[f"constraint:Xi*{name}"] = _coefficient_vector(
            _multiply(xi, parameter_factor=parameter_index)
        )
    for angular_name, terms in angular.items():
        controls[f"known:{angular_name}"] = _coefficient_vector(_multiply(terms))
        for parameter_index, parameter_name in enumerate(_PARAMETER_NAMES):
            controls[f"known:{parameter_name}*{angular_name}"] = _coefficient_vector(
                _multiply(terms, parameter_factor=parameter_index)
            )
    return controls
