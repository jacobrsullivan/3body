"""SO(3)-invariant feature library and exact Lie derivatives for WP3."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations_with_replacement
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import SystemParameters


FloatArray: TypeAlias = NDArray[np.float64]
DimensionSignature: TypeAlias = tuple[int, int, int]
VECTOR_NAMES = ("rho", "lambda", "p_rho", "p_lambda")
VECTOR_DIMENSIONS: tuple[DimensionSignature, ...] = (
    (0, 1, 0),
    (0, 1, 0),
    (1, 1, -1),
    (1, 1, -1),
)
GRAM_PAIRS = tuple(combinations_with_replacement(range(4), 2))
GRAM_NAMES = tuple(
    f"dot({VECTOR_NAMES[first]},{VECTOR_NAMES[second]})"
    for first, second in GRAM_PAIRS
)
QUADRATIC_PAIRS = tuple(combinations_with_replacement(range(len(GRAM_NAMES)), 2))
QUADRATIC_NAMES = tuple(
    f"{GRAM_NAMES[first]}*{GRAM_NAMES[second]}"
    for first, second in QUADRATIC_PAIRS
)
KINETIC_NAMES = ("kinetic_rho", "kinetic_lambda")
POTENTIAL_NAMES = ("potential_12", "potential_23", "potential_31")
FEATURE_NAMES = GRAM_NAMES + QUADRATIC_NAMES + KINETIC_NAMES + POTENTIAL_NAMES


def _add_dimensions(
    first: DimensionSignature,
    second: DimensionSignature,
) -> DimensionSignature:
    return tuple(
        left + right for left, right in zip(first, second, strict=True)
    )


GRAM_DIMENSIONS = tuple(
    _add_dimensions(VECTOR_DIMENSIONS[first], VECTOR_DIMENSIONS[second])
    for first, second in GRAM_PAIRS
)
QUADRATIC_DIMENSIONS = tuple(
    _add_dimensions(GRAM_DIMENSIONS[first], GRAM_DIMENSIONS[second])
    for first, second in QUADRATIC_PAIRS
)
ENERGY_DIMENSION: DimensionSignature = (1, 2, -2)
FEATURE_DIMENSIONS = (
    GRAM_DIMENSIONS
    + QUADRATIC_DIMENSIONS
    + (ENERGY_DIMENSION,) * (len(KINETIC_NAMES) + len(POTENTIAL_NAMES))
)


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (12,):
        raise ValueError(f"{name} must have shape (12,), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def feature_names() -> tuple[str, ...]:
    return FEATURE_NAMES


def feature_dimensions() -> tuple[DimensionSignature, ...]:
    """Return mass, length, and time exponents for every feature."""

    return FEATURE_DIMENSIONS


def format_dimension_signature(signature: DimensionSignature) -> str:
    """Format a dimension signature as a stable sector identifier."""

    mass, length, time = signature
    return f"M{mass:+d}_L{length:+d}_T{time:+d}"


@dataclass(frozen=True)
class FeatureEvaluation:
    """Feature values and exact directional derivatives along the N3BP flow."""

    names: tuple[str, ...]
    values: FloatArray
    lie_derivatives: FloatArray

    def __post_init__(self) -> None:
        expected = (len(self.names),)
        values = np.asarray(self.values, dtype=np.float64)
        derivatives = np.asarray(self.lie_derivatives, dtype=np.float64)
        if values.shape != expected or derivatives.shape != expected:
            raise ValueError("feature arrays do not match feature names")
        if not np.all(np.isfinite(values)) or not np.all(np.isfinite(derivatives)):
            raise ValueError("feature arrays must contain only finite values")
        values = np.array(values, copy=True)
        derivatives = np.array(derivatives, copy=True)
        values.setflags(write=False)
        derivatives.setflags(write=False)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "lie_derivatives", derivatives)


def _mass_data(parameters: SystemParameters) -> tuple[float, ...]:
    m1, m2, m3 = (float(value) for value in parameters.masses)
    m12 = m1 + m2
    total = m12 + m3
    return m1, m2, m3, m12, m1 * m2 / m12, m3 * m12 / total


def _potential_feature(
    vector: FloatArray,
    derivative: FloatArray,
    strength: float,
) -> tuple[float, float]:
    radius = float(np.linalg.norm(vector))
    if radius == 0.0:
        raise ZeroDivisionError("WP3 features are undefined at binary collision")
    value = -strength / radius
    lie_derivative = strength * float(np.dot(vector, derivative)) / radius**3
    return value, lie_derivative


def evaluate_invariant_features(
    state: ArrayLike,
    derivative: ArrayLike,
    parameters: SystemParameters,
) -> FeatureEvaluation:
    """Evaluate the invariant feature library and its exact Lie derivative."""

    state_array = _vector(state, "state")
    derivative_array = _vector(derivative, "derivative")
    vectors = state_array.reshape(4, 3)
    vector_derivatives = derivative_array.reshape(4, 3)

    gram = np.array(
        [np.dot(vectors[first], vectors[second]) for first, second in GRAM_PAIRS],
        dtype=np.float64,
    )
    gram_dot = np.array(
        [
            np.dot(vector_derivatives[first], vectors[second])
            + np.dot(vectors[first], vector_derivatives[second])
            for first, second in GRAM_PAIRS
        ],
        dtype=np.float64,
    )
    quadratic = np.array(
        [gram[first] * gram[second] for first, second in QUADRATIC_PAIRS],
        dtype=np.float64,
    )
    quadratic_dot = np.array(
        [
            gram_dot[first] * gram[second] + gram[first] * gram_dot[second]
            for first, second in QUADRATIC_PAIRS
        ],
        dtype=np.float64,
    )

    m1, m2, m3, m12, mu12, mu3_12 = _mass_data(parameters)
    kinetic = np.array([gram[7] / (2.0 * mu12), gram[9] / (2.0 * mu3_12)])
    kinetic_dot = np.array(
        [gram_dot[7] / (2.0 * mu12), gram_dot[9] / (2.0 * mu3_12)]
    )

    rho, lambda_vector = vectors[0], vectors[1]
    rho_dot, lambda_dot = vector_derivatives[0], vector_derivatives[1]
    x12 = rho
    x23 = lambda_vector - (m1 / m12) * rho
    x31 = -lambda_vector - (m2 / m12) * rho
    x12_dot = rho_dot
    x23_dot = lambda_dot - (m1 / m12) * rho_dot
    x31_dot = -lambda_dot - (m2 / m12) * rho_dot
    gravitational_constant = parameters.gravitational_constant
    potential_pairs = (
        _potential_feature(x12, x12_dot, gravitational_constant * m1 * m2),
        _potential_feature(x23, x23_dot, gravitational_constant * m2 * m3),
        _potential_feature(x31, x31_dot, gravitational_constant * m3 * m1),
    )
    potential = np.array([item[0] for item in potential_pairs])
    potential_dot = np.array([item[1] for item in potential_pairs])
    return FeatureEvaluation(
        names=FEATURE_NAMES,
        values=np.concatenate((gram, quadratic, kinetic, potential)),
        lie_derivatives=np.concatenate(
            (gram_dot, quadratic_dot, kinetic_dot, potential_dot)
        ),
    )


def _quadratic_feature_name(first: str, second: str) -> str:
    first_index = GRAM_NAMES.index(first)
    second_index = GRAM_NAMES.index(second)
    if first_index > second_index:
        first, second = second, first
    return f"{first}*{second}"


def known_control_coefficients() -> dict[str, FloatArray]:
    """Return universal coefficients for energy and angular-momentum squared."""

    index = {name: position for position, name in enumerate(FEATURE_NAMES)}
    energy = np.zeros(len(FEATURE_NAMES))
    for name in KINETIC_NAMES + POTENTIAL_NAMES:
        energy[index[name]] = 1.0

    gram = {
        (first, second): GRAM_NAMES[position]
        for position, (first, second) in enumerate(GRAM_PAIRS)
    }
    angular_squared = np.zeros(len(FEATURE_NAMES))

    def add(first: tuple[int, int], second: tuple[int, int], value: float) -> None:
        name = _quadratic_feature_name(gram[first], gram[second])
        angular_squared[index[name]] += value

    add((0, 0), (2, 2), 1.0)
    add((0, 2), (0, 2), -1.0)
    add((1, 1), (3, 3), 1.0)
    add((1, 3), (1, 3), -1.0)
    add((0, 1), (2, 3), 2.0)
    add((0, 3), (1, 2), -2.0)
    return {"energy": energy, "angular_momentum_squared": angular_squared}
