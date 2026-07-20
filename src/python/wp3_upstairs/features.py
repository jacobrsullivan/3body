"""Exact low-degree feature values and Lie derivatives upstairs."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations_with_replacement
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.upstairs_ks import (
    UpstairsKSState,
    angular_momentum,
    project_state,
    projection_jacobian,
)


FloatArray: TypeAlias = NDArray[np.float64]
_VARIABLE_NAMES = (
    "q1", "q2", "q3", "q4", "lambda_x", "lambda_y", "lambda_z",
    "Q1", "Q2", "Q3", "Q4", "p_lambda_x", "p_lambda_y", "p_lambda_z",
)
_KNOWN_NAMES = ("known:H", "known:H2", "known:Lx", "known:Ly", "known:Lz", "known:L2")


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (14,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length 14")
    return array


@lru_cache(maxsize=None)
def monomial_indices(max_degree: int = 3) -> tuple[tuple[int, ...], ...]:
    """Return the canonical monomial grammar, excluding the constant."""

    if max_degree < 1 or max_degree > 4:
        raise ValueError("max_degree must be between one and four")
    return tuple(
        indices
        for degree in range(1, max_degree + 1)
        for indices in combinations_with_replacement(range(14), degree)
    )


@lru_cache(maxsize=None)
def feature_names(max_degree: int = 3) -> tuple[str, ...]:
    names = ["*".join(_VARIABLE_NAMES[index] for index in indices) for indices in monomial_indices(max_degree)]
    names.extend(_KNOWN_NAMES)
    return tuple(names)


def known_control_coefficients(max_degree: int = 3) -> Mapping[str, FloatArray]:
    """Return one-hot controls for the explicitly appended known algebra."""

    names = feature_names(max_degree)
    controls = {}
    for name in _KNOWN_NAMES:
        vector = np.zeros(len(names), dtype=np.float64)
        vector[names.index(name)] = 1.0
        controls[name.removeprefix("known:")] = vector
    return controls


@dataclass(frozen=True)
class UpstairsFeatureEvaluation:
    names: tuple[str, ...]
    values: FloatArray
    lie_derivatives: FloatArray

    def __post_init__(self) -> None:
        if self.values.shape != (len(self.names),):
            raise ValueError("feature value count does not match names")
        if self.lie_derivatives.shape != self.values.shape:
            raise ValueError("feature derivative count does not match values")
        if not np.all(np.isfinite(self.values)) or not np.all(np.isfinite(self.lie_derivatives)):
            raise ValueError("feature evaluation must be finite")


def _monomial_value_and_lie(
    state: FloatArray,
    derivative: FloatArray,
    indices: tuple[int, ...],
) -> tuple[float, float]:
    value = 1.0
    for index in indices:
        value *= float(state[index])
    lie = 0.0
    for differentiated, index in enumerate(indices):
        term = float(derivative[index])
        for position, factor in enumerate(indices):
            if position != differentiated:
                term *= float(state[factor])
        lie += term
    return value, lie


def evaluate_upstairs_features(
    state: UpstairsKSState,
    derivative: ArrayLike,
    *,
    physical_energy: float,
    max_degree: int = 3,
) -> UpstairsFeatureEvaluation:
    """Evaluate the frozen polynomial grammar and known integral controls."""

    vector = state.as_vector()
    tangent = _vector(derivative, "derivative")
    if not np.isfinite(physical_energy):
        raise ValueError("physical_energy must be finite")
    values = []
    lies = []
    for indices in monomial_indices(max_degree):
        value, lie = _monomial_value_and_lie(vector, tangent, indices)
        values.append(value)
        lies.append(lie)
    angular = angular_momentum(state)
    physical = project_state(state).reshape(4, 3)
    physical_tangent = (projection_jacobian(state) @ tangent).reshape(4, 3)
    rho, lambda_vector, p_rho, p_lambda = physical
    rho_dot, lambda_dot, p_rho_dot, p_lambda_dot = physical_tangent
    angular_lie = (
        np.cross(rho_dot, p_rho)
        + np.cross(rho, p_rho_dot)
        + np.cross(lambda_dot, p_lambda)
        + np.cross(lambda_vector, p_lambda_dot)
    )
    angular2 = float(np.dot(angular, angular))
    values.extend(
        (
            float(physical_energy),
            float(physical_energy) ** 2,
            float(angular[0]),
            float(angular[1]),
            float(angular[2]),
            angular2,
        )
    )
    lies.extend(
        (
            0.0,
            0.0,
            float(angular_lie[0]),
            float(angular_lie[1]),
            float(angular_lie[2]),
            2.0 * float(np.dot(angular, angular_lie)),
        )
    )
    return UpstairsFeatureEvaluation(
        names=feature_names(max_degree),
        values=np.asarray(values, dtype=np.float64),
        lie_derivatives=np.asarray(lies, dtype=np.float64),
    )
