"""Frozen physical-quotient feature grammar for WP3-MULTI-CAND-v2."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations_with_replacement, permutations
import math
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import InertialState, SystemParameters


FloatArray: TypeAlias = NDArray[np.float64]
Descriptor: TypeAlias = tuple[int, tuple[int, ...], tuple[int, ...]]

GRAM_NAMES = (
    "X1.X1",
    "X1.X2",
    "X1.W1",
    "X1.W2",
    "X2.X2",
    "X2.W1",
    "X2.W2",
    "W1.W1",
    "W1.W2",
    "W2.W2",
)
PARAMETER_NAMES = ("fixed_energy", "mass_s2", "mass_s3")
DENOMINATOR_NAMES = (
    "one",
    "collision_product_r12_r23_r31",
    "barycentric_moment_of_inertia",
)
BODY_PERMUTATIONS = tuple(permutations(range(3)))

_GRAM_PAIRS = (
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 2),
    (2, 3),
    (3, 3),
)


def _stable_dot(first: ArrayLike, second: ArrayLike) -> float:
    return math.fsum(
        float(left) * float(right) for left, right in zip(first, second, strict=True)
    )


def _stable_norm(value: ArrayLike) -> float:
    array = np.asarray(value, dtype=np.float64)
    return math.sqrt(_stable_dot(array, array))


def _tangent(value: ArrayLike) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (18,) or not np.all(np.isfinite(array)):
        raise ValueError("tangent must be a finite vector of length 18")
    return array


def _validate_translation_quotient(
    state: InertialState,
    tangent: FloatArray,
    parameters: SystemParameters,
) -> None:
    masses = parameters.masses
    momenta = masses[:, None] * state.velocities
    momentum_derivatives = masses[:, None] * tangent[9:].reshape(3, 3)
    momentum_scale = max(1.0, float(np.sum(np.abs(momenta))))
    derivative_scale = max(1.0, float(np.sum(np.abs(momentum_derivatives))))
    if np.linalg.norm(np.sum(momenta, axis=0)) > 2e-10 * momentum_scale:
        raise ValueError("features require the zero-total-momentum quotient")
    if np.linalg.norm(np.sum(momentum_derivatives, axis=0)) > 2e-10 * derivative_scale:
        raise ValueError("tangent leaves the zero-total-momentum quotient")


@lru_cache(maxsize=1)
def feature_descriptors() -> tuple[Descriptor, ...]:
    """Return the frozen 3 x 95 Reynolds-feature descriptors."""

    descriptors: list[Descriptor] = []
    for denominator_index in range(len(DENOMINATOR_NAMES)):
        for gram_degree in (1, 2):
            for gram_indices in combinations_with_replacement(
                range(len(GRAM_NAMES)), gram_degree
            ):
                for parameter_degree in range(0, 3 - gram_degree):
                    for parameter_indices in combinations_with_replacement(
                        range(len(PARAMETER_NAMES)), parameter_degree
                    ):
                        descriptors.append(
                            (denominator_index, gram_indices, parameter_indices)
                        )
    return tuple(descriptors)


@lru_cache(maxsize=1)
def feature_names() -> tuple[str, ...]:
    names: list[str] = []
    for denominator_index, gram_indices, parameter_indices in feature_descriptors():
        factors = [GRAM_NAMES[index] for index in gram_indices]
        factors.extend(PARAMETER_NAMES[index] for index in parameter_indices)
        numerator = "*".join(factors)
        denominator = DENOMINATOR_NAMES[denominator_index]
        names.append(
            numerator if denominator == "one" else f"({numerator})/{denominator}"
        )
    return tuple(names)


@lru_cache(maxsize=1)
def structural_zero_feature_indices() -> tuple[int, ...]:
    """Return exact Reynolds identities retained in the declared library."""

    quadratic_zeros = {(0, 3), (3, 9), (4, 5), (5, 7)}
    return tuple(
        index
        for index, (_, gram_indices, _) in enumerate(feature_descriptors())
        if (len(gram_indices) == 1 and gram_indices[0] in (3, 5))
        or (len(gram_indices) == 2 and gram_indices in quadratic_zeros)
    )


def parameter_values(
    parameters: SystemParameters,
    fixed_energy: float,
) -> FloatArray:
    if not np.isfinite(fixed_energy):
        raise ValueError("fixed_energy must be finite")
    masses = parameters.masses
    pair_products = sorted(
        (
            float(masses[0] * masses[1]),
            float(masses[1] * masses[2]),
            float(masses[2] * masses[0]),
        )
    )
    return np.asarray(
        [
            float(fixed_energy),
            math.fsum(pair_products),
            math.prod(sorted(float(value) for value in masses)),
        ],
        dtype=np.float64,
    )


def denominator_values_and_derivatives(
    state: InertialState,
    tangent: ArrayLike,
    parameters: SystemParameters,
) -> tuple[FloatArray, FloatArray]:
    """Evaluate the three global denominators and their tangent derivatives."""

    derivative = _tangent(tangent)
    positions = state.positions
    position_derivatives = derivative[:9].reshape(3, 3)
    distances: list[float] = []
    distance_derivatives: list[float] = []
    for first, second in ((0, 1), (1, 2), (2, 0)):
        relative = positions[first] - positions[second]
        relative_derivative = position_derivatives[first] - position_derivatives[second]
        distance = _stable_norm(relative)
        if not np.isfinite(distance) or distance <= 0.0:
            raise ValueError("collision denominators require nonzero pair distances")
        distances.append(distance)
        distance_derivatives.append(
            _stable_dot(relative, relative_derivative) / distance
        )
    collision_product = math.prod(sorted(distances))
    collision_product_derivative = collision_product * math.fsum(
        sorted(
            rate / distance
            for rate, distance in zip(distance_derivatives, distances, strict=True)
        )
    )

    masses = parameters.masses
    total_mass = math.fsum(float(value) for value in masses)
    center = np.asarray(
        [
            math.fsum(
                float(masses[index] * positions[index, component]) for index in range(3)
            )
            / total_mass
            for component in range(3)
        ]
    )
    center_derivative = np.asarray(
        [
            math.fsum(
                float(masses[index] * position_derivatives[index, component])
                for index in range(3)
            )
            / total_mass
            for component in range(3)
        ]
    )
    centered = positions - center
    centered_derivative = position_derivatives - center_derivative
    inertia = math.fsum(
        float(masses[body] * centered[body, component] ** 2)
        for body in range(3)
        for component in range(3)
    )
    inertia_derivative = 2.0 * math.fsum(
        float(
            masses[body]
            * centered[body, component]
            * centered_derivative[body, component]
        )
        for body in range(3)
        for component in range(3)
    )
    if not np.isfinite(inertia) or inertia <= 0.0:
        raise ValueError("moment-of-inertia denominator must be positive")
    values = np.asarray([1.0, collision_product, inertia], dtype=np.float64)
    derivatives = np.asarray(
        [0.0, collision_product_derivative, inertia_derivative], dtype=np.float64
    )
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(derivatives)):
        raise ArithmeticError("denominator evaluation is not finite")
    return values, derivatives


def _local_grams(
    positions: FloatArray,
    momenta: FloatArray,
    position_derivatives: FloatArray,
    momentum_derivatives: FloatArray,
    order: tuple[int, int, int],
) -> tuple[FloatArray, FloatArray]:
    first, second, central = order
    vectors = np.stack(
        (
            positions[first] - positions[central],
            positions[second] - positions[central],
            momenta[first],
            momenta[second],
        )
    )
    vector_derivatives = np.stack(
        (
            position_derivatives[first] - position_derivatives[central],
            position_derivatives[second] - position_derivatives[central],
            momentum_derivatives[first],
            momentum_derivatives[second],
        )
    )
    values = np.asarray(
        [_stable_dot(vectors[a], vectors[b]) for a, b in _GRAM_PAIRS],
        dtype=np.float64,
    )
    derivatives = np.asarray(
        [
            math.fsum(
                (
                    _stable_dot(vector_derivatives[a], vectors[b]),
                    _stable_dot(vectors[a], vector_derivatives[b]),
                )
            )
            for a, b in _GRAM_PAIRS
        ],
        dtype=np.float64,
    )
    return values, derivatives


def _monomial_value_derivative(
    values: FloatArray,
    derivatives: FloatArray,
    indices: tuple[int, ...],
    factor: float,
) -> tuple[float, float]:
    value = factor
    for index in indices:
        value *= float(values[index])
    derivative = 0.0
    for differentiated, differentiated_index in enumerate(indices):
        term = factor * float(derivatives[differentiated_index])
        for position, index in enumerate(indices):
            if position != differentiated:
                term *= float(values[index])
        derivative += term
    return value, derivative


@dataclass(frozen=True)
class MultiFeatureEvaluation:
    names: tuple[str, ...]
    values: FloatArray
    derivatives: FloatArray
    denominator_values: FloatArray
    denominator_derivatives: FloatArray

    def __post_init__(self) -> None:
        count = len(self.names)
        if self.values.shape != (count,) or self.derivatives.shape != (count,):
            raise ValueError("feature arrays do not match names")
        if self.denominator_values.shape != (
            3,
        ) or self.denominator_derivatives.shape != (3,):
            raise ValueError("denominator arrays have the wrong shape")
        if not all(
            np.all(np.isfinite(array))
            for array in (
                self.values,
                self.derivatives,
                self.denominator_values,
                self.denominator_derivatives,
            )
        ):
            raise ValueError("feature evaluation must be finite")


def evaluate_multi_features(
    state: InertialState,
    tangent: ArrayLike,
    parameters: SystemParameters,
    *,
    fixed_energy: float,
) -> MultiFeatureEvaluation:
    """Evaluate the full six-permutation Reynolds library."""

    derivative = _tangent(tangent)
    _validate_translation_quotient(state, derivative, parameters)
    positions = state.positions
    position_derivatives = derivative[:9].reshape(3, 3)
    momenta = parameters.masses[:, None] * state.velocities
    momentum_derivatives = parameters.masses[:, None] * derivative[9:].reshape(3, 3)
    parameters_array = parameter_values(parameters, fixed_energy)
    denominator_values, denominator_derivatives = denominator_values_and_derivatives(
        state, derivative, parameters
    )

    permutation_values: list[FloatArray] = []
    permutation_derivatives: list[FloatArray] = []
    descriptors = feature_descriptors()
    for order in BODY_PERMUTATIONS:
        grams, gram_derivatives = _local_grams(
            positions,
            momenta,
            position_derivatives,
            momentum_derivatives,
            order,
        )
        values: list[float] = []
        derivatives: list[float] = []
        for denominator_index, gram_indices, parameter_indices in descriptors:
            parameter_factor = 1.0
            for parameter_index in parameter_indices:
                parameter_factor *= float(parameters_array[parameter_index])
            numerator, numerator_derivative = _monomial_value_derivative(
                grams, gram_derivatives, gram_indices, parameter_factor
            )
            denominator = float(denominator_values[denominator_index])
            denominator_derivative = float(denominator_derivatives[denominator_index])
            values.append(numerator / denominator)
            derivatives.append(
                (
                    numerator_derivative * denominator
                    - numerator * denominator_derivative
                )
                / (denominator * denominator)
            )
        permutation_values.append(np.asarray(values, dtype=np.float64))
        permutation_derivatives.append(np.asarray(derivatives, dtype=np.float64))

    # Relabeling only permutes the six local rows. Columnwise sorting makes the
    # Reynolds summation order itself invariant, instead of leaving a body-label
    # dependent floating-point reduction order.
    values = np.mean(np.sort(np.stack(permutation_values), axis=0), axis=0)
    derivatives = np.mean(np.sort(np.stack(permutation_derivatives), axis=0), axis=0)
    zero_indices = np.asarray(structural_zero_feature_indices(), dtype=np.int64)
    zero_scale = max(
        1.0,
        float(np.max(np.abs(values))),
        float(np.max(np.abs(derivatives))),
    )
    if (
        float(np.max(np.abs(values[zero_indices]))) > 5e-13 * zero_scale
        or float(np.max(np.abs(derivatives[zero_indices]))) > 5e-13 * zero_scale
    ):
        raise ArithmeticError("declared Reynolds zero identity did not cancel")
    values[zero_indices] = 0.0
    derivatives[zero_indices] = 0.0
    return MultiFeatureEvaluation(
        names=feature_names(),
        values=values,
        derivatives=derivatives,
        denominator_values=denominator_values,
        denominator_derivatives=denominator_derivatives,
    )


def _coefficient_vector(terms: Mapping[Descriptor, float]) -> FloatArray:
    lookup = {
        descriptor: index for index, descriptor in enumerate(feature_descriptors())
    }
    coefficients = np.zeros(len(lookup), dtype=np.float64)
    for descriptor, coefficient in terms.items():
        coefficients[lookup[descriptor]] += float(coefficient)
    return coefficients


@lru_cache(maxsize=1)
def angular_momentum_squared_coefficients() -> FloatArray:
    """Return the exact coefficient vector for total angular momentum squared."""

    terms: dict[Descriptor, float] = {
        (0, (0, 7), ()): 1.0,
        (0, (2, 2), ()): -1.0,
        (0, (4, 9), ()): 1.0,
        (0, (6, 6), ()): -1.0,
        (0, (1, 8), ()): 2.0,
        (0, (3, 5), ()): -2.0,
    }
    coefficients = _coefficient_vector(terms)
    coefficients.setflags(write=False)
    return coefficients


@lru_cache(maxsize=1)
def known_module_coefficients() -> dict[str, FloatArray]:
    return {"known:angular_momentum_squared": angular_momentum_squared_coefficients()}


def permute_physical_inputs(
    state: InertialState,
    tangent: ArrayLike,
    parameters: SystemParameters,
    permutation: tuple[int, int, int],
) -> tuple[InertialState, FloatArray, SystemParameters]:
    """Relabel all body-indexed physical inputs by one permutation."""

    if tuple(sorted(permutation)) != (0, 1, 2):
        raise ValueError("permutation must contain body indices 0, 1, 2")
    derivative = _tangent(tangent)
    indices = np.asarray(permutation, dtype=np.int64)
    permuted_state = InertialState.from_components(
        state.positions[indices], state.velocities[indices]
    )
    position_derivatives = derivative[:9].reshape(3, 3)[indices]
    velocity_derivatives = derivative[9:].reshape(3, 3)[indices]
    permuted_tangent = np.concatenate(
        (position_derivatives.ravel(), velocity_derivatives.ravel())
    )
    permuted_parameters = SystemParameters(
        parameters.masses[indices],
        gravitational_constant=parameters.gravitational_constant,
    )
    return permuted_state, permuted_tangent, permuted_parameters
