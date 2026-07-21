"""Complete shared degree-three grammar for the WP2-MULTIQ-v1 atlas."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations_with_replacement
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.ks import fiber_generator
from src.python.n3bp_qualification import SystemParameters
from src.python.wp2_multi_v1 import MultiKSState


FloatArray: TypeAlias = NDArray[np.float64]
Descriptor = tuple[tuple[int, ...], tuple[int, ...]]

STATE_NAMES = (
    "q1_1", "q1_2", "q1_3", "q1_4",
    "q2_1", "q2_2", "q2_3", "q2_4",
    "P1_1", "P1_2", "P1_3", "P1_4",
    "P2_1", "P2_2", "P2_3", "P2_4",
)
PARAMETER_NAMES = ("fixed_energy", "mass_s2", "mass_s3")


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (16,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length 16")
    return array


@lru_cache(maxsize=1)
def feature_descriptors() -> tuple[Descriptor, ...]:
    """Return every combined-degree-three-or-less monomial with a state factor."""

    descriptors: list[Descriptor] = []
    for state_degree in range(1, 4):
        for state_indices in combinations_with_replacement(
            range(len(STATE_NAMES)), state_degree
        ):
            for parameter_degree in range(0, 4 - state_degree):
                for parameter_indices in combinations_with_replacement(
                    range(len(PARAMETER_NAMES)), parameter_degree
                ):
                    descriptors.append((state_indices, parameter_indices))
    return tuple(descriptors)


@lru_cache(maxsize=1)
def feature_names() -> tuple[str, ...]:
    names: list[str] = []
    for state_indices, parameter_indices in feature_descriptors():
        factors = [STATE_NAMES[index] for index in state_indices]
        factors.extend(PARAMETER_NAMES[index] for index in parameter_indices)
        names.append("*".join(factors))
    return tuple(names)


def multi_state_vector(state: MultiKSState) -> FloatArray:
    """Return the 16 non-time canonical variables in the frozen ordering."""

    return np.concatenate((state.q1, state.q2, state.P1, state.P2))


def multi_tangent_vector(derivative: ArrayLike) -> FloatArray:
    """Remove the physical-time and temporal-momentum tangent components."""

    vector = np.asarray(derivative, dtype=np.float64)
    if vector.shape != (18,) or not np.all(np.isfinite(vector)):
        raise ValueError("derivative must be a finite vector of length 18")
    return np.concatenate((vector[:8], vector[9:17]))


def parameter_values(
    parameters: SystemParameters,
    fixed_energy: float,
) -> FloatArray:
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


def torus_generators(state: MultiKSState) -> tuple[FloatArray, FloatArray]:
    """Return tangents for the two independent cotangent circle actions."""

    zero = np.zeros(4, dtype=np.float64)
    first = np.concatenate(
        (fiber_generator(state.q1), zero, fiber_generator(state.P1), zero)
    )
    second = np.concatenate(
        (zero, fiber_generator(state.q2), zero, fiber_generator(state.P2))
    )
    return first, second


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
    for differentiated in range(len(state_indices)):
        term = parameter_factor * float(tangent[state_indices[differentiated]])
        for position, index in enumerate(state_indices):
            if position != differentiated:
                term *= float(state[index])
        lie += term
    return value, lie


@dataclass(frozen=True)
class MultiFeatureEvaluation:
    names: tuple[str, ...]
    values: FloatArray
    derivatives: FloatArray

    def __post_init__(self) -> None:
        if self.values.shape != (len(self.names),):
            raise ValueError("feature values do not match names")
        if self.derivatives.shape != self.values.shape:
            raise ValueError("feature derivatives do not match values")
        if not np.all(np.isfinite(self.values)) or not np.all(
            np.isfinite(self.derivatives)
        ):
            raise ValueError("feature evaluation must be finite")


def evaluate_multi_features(
    state: MultiKSState,
    tangent: ArrayLike,
    parameters: SystemParameters,
    *,
    fixed_energy: float,
) -> MultiFeatureEvaluation:
    state_vector = multi_state_vector(state)
    tangent_vector = _vector(tangent, "tangent")
    parameter_vector = parameter_values(parameters, fixed_energy)
    values: list[float] = []
    derivatives: list[float] = []
    for state_indices, parameter_indices in feature_descriptors():
        factor = 1.0
        for index in parameter_indices:
            factor *= float(parameter_vector[index])
        value, derivative = _monomial_value_lie(
            state_vector, tangent_vector, state_indices, factor
        )
        values.append(value)
        derivatives.append(derivative)
    return MultiFeatureEvaluation(
        names=feature_names(),
        values=np.asarray(values, dtype=np.float64),
        derivatives=np.asarray(derivatives, dtype=np.float64),
    )


def _coefficient_vector(terms: Mapping[Descriptor, float]) -> FloatArray:
    indices = {
        descriptor: index for index, descriptor in enumerate(feature_descriptors())
    }
    vector = np.zeros(len(indices), dtype=np.float64)
    for descriptor, coefficient in terms.items():
        vector[indices[descriptor]] += float(coefficient)
    return vector


def _expand_terms(
    terms: Mapping[tuple[int, ...], float],
    *,
    state_factor: int | None = None,
    parameter_factor: int | None = None,
) -> dict[Descriptor, float]:
    output: dict[Descriptor, float] = {}
    for state_indices, coefficient in terms.items():
        expanded_state = tuple(
            sorted(
                state_indices
                if state_factor is None
                else (*state_indices, state_factor)
            )
        )
        expanded_parameters = () if parameter_factor is None else (parameter_factor,)
        descriptor = (expanded_state, expanded_parameters)
        output[descriptor] = output.get(descriptor, 0.0) + float(coefficient)
    return output


def _spinor_angular_terms(q_offset: int, momentum_offset: int) -> dict[str, dict[tuple[int, ...], float]]:
    q0, q1, q2, q3 = (q_offset + index for index in range(4))
    p0, p1, p2, p3 = (momentum_offset + index for index in range(4))
    return {
        "Lx": {
            tuple(sorted((q0, p3))): -0.5,
            tuple(sorted((q1, p2))): 0.5,
            tuple(sorted((q2, p1))): -0.5,
            tuple(sorted((q3, p0))): 0.5,
        },
        "Ly": {
            tuple(sorted((q0, p2))): 0.5,
            tuple(sorted((q1, p3))): 0.5,
            tuple(sorted((q2, p0))): -0.5,
            tuple(sorted((q3, p1))): -0.5,
        },
        "Lz": {
            tuple(sorted((q0, p1))): -0.5,
            tuple(sorted((q1, p0))): 0.5,
            tuple(sorted((q2, p3))): 0.5,
            tuple(sorted((q3, p2))): -0.5,
        },
    }


@lru_cache(maxsize=1)
def known_module_coefficients() -> dict[str, FloatArray]:
    """Return the complete represented Xi ideal and angular-momentum module."""

    xi_terms = {
        "Xi1": {(0, 9): 1.0, (1, 8): -1.0, (2, 11): 1.0, (3, 10): -1.0},
        "Xi2": {(4, 13): 1.0, (5, 12): -1.0, (6, 15): 1.0, (7, 14): -1.0},
    }
    controls: dict[str, FloatArray] = {}
    for xi_name, terms in xi_terms.items():
        controls[f"constraint:{xi_name}"] = _coefficient_vector(
            _expand_terms(terms)
        )
        for state_index, state_name in enumerate(STATE_NAMES):
            controls[f"constraint:{xi_name}*{state_name}"] = _coefficient_vector(
                _expand_terms(terms, state_factor=state_index)
            )
        for parameter_index, parameter_name in enumerate(PARAMETER_NAMES):
            controls[f"constraint:{xi_name}*{parameter_name}"] = _coefficient_vector(
                _expand_terms(terms, parameter_factor=parameter_index)
            )

    first = _spinor_angular_terms(0, 8)
    second = _spinor_angular_terms(4, 12)
    for component in ("Lx", "Ly", "Lz"):
        terms = dict(first[component])
        for descriptor, coefficient in second[component].items():
            terms[descriptor] = terms.get(descriptor, 0.0) + coefficient
        controls[f"known:{component}"] = _coefficient_vector(_expand_terms(terms))
        for parameter_index, parameter_name in enumerate(PARAMETER_NAMES):
            controls[f"known:{parameter_name}*{component}"] = _coefficient_vector(
                _expand_terms(terms, parameter_factor=parameter_index)
            )
    return controls
