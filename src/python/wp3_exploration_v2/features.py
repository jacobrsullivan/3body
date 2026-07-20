"""Low-degree SO(3) scalar features and exact Lie derivatives."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, combinations_with_replacement
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import SystemParameters


FloatArray: TypeAlias = NDArray[np.float64]
VECTOR_NAMES = ("rho", "lambda", "p_rho", "p_lambda")
DOT_PAIRS = tuple(combinations_with_replacement(range(4), 2))
TRIPLE_INDICES = tuple(combinations(range(4), 3))
DOT_NAMES = tuple(
    f"dot({VECTOR_NAMES[first]},{VECTOR_NAMES[second]})"
    for first, second in DOT_PAIRS
)
TRIPLE_NAMES = tuple(
    "triple(" + ",".join(VECTOR_NAMES[index] for index in triple) + ")"
    for triple in TRIPLE_INDICES
)
ENERGY_NAMES = (
    "kinetic_rho",
    "kinetic_lambda",
    "potential_12",
    "potential_23",
    "potential_31",
)
PRIMITIVE_NAMES = DOT_NAMES + TRIPLE_NAMES + ENERGY_NAMES
PRODUCT_PAIRS = tuple(combinations_with_replacement(range(len(PRIMITIVE_NAMES)), 2))
MONOMIAL_NAMES = (
    "constant",
    *PRIMITIVE_NAMES,
    *(
        f"{PRIMITIVE_NAMES[first]}*{PRIMITIVE_NAMES[second]}"
        for first, second in PRODUCT_PAIRS
    ),
)
PARAMETER_NAMES = ("1", "mass_s2", "mass_s3")
FEATURE_NAMES = tuple(
    f"{parameter}:{monomial}"
    for parameter in PARAMETER_NAMES
    for monomial in MONOMIAL_NAMES
)


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (12,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length 12")
    return array


@dataclass(frozen=True)
class FeatureEvaluation:
    """Frozen feature ordering, values, and exact directional derivatives."""

    names: tuple[str, ...]
    values: ArrayLike
    lie_derivatives: ArrayLike

    def __post_init__(self) -> None:
        values = np.asarray(self.values, dtype=np.float64)
        derivatives = np.asarray(self.lie_derivatives, dtype=np.float64)
        expected = (len(self.names),)
        if values.shape != expected or derivatives.shape != expected:
            raise ValueError("feature vectors do not match feature names")
        if not np.all(np.isfinite(values)) or not np.all(np.isfinite(derivatives)):
            raise ValueError("feature vectors must be finite")
        values = np.array(values, copy=True)
        derivatives = np.array(derivatives, copy=True)
        values.setflags(write=False)
        derivatives.setflags(write=False)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "lie_derivatives", derivatives)


def feature_names() -> tuple[str, ...]:
    return FEATURE_NAMES


def _potential(
    vector: FloatArray,
    vector_dot: FloatArray,
    strength: float,
) -> tuple[float, float]:
    radius = float(np.linalg.norm(vector))
    if radius == 0.0:
        raise ZeroDivisionError("feature library is singular at binary collision")
    return (
        -strength / radius,
        strength * float(np.dot(vector, vector_dot)) / radius**3,
    )


def _primitive_values(
    state: FloatArray,
    derivative: FloatArray,
    parameters: SystemParameters,
) -> tuple[FloatArray, FloatArray]:
    vectors = state.reshape(4, 3)
    vector_dots = derivative.reshape(4, 3)
    dots = np.array(
        [np.dot(vectors[first], vectors[second]) for first, second in DOT_PAIRS]
    )
    dots_dot = np.array(
        [
            np.dot(vector_dots[first], vectors[second])
            + np.dot(vectors[first], vector_dots[second])
            for first, second in DOT_PAIRS
        ]
    )
    triples = []
    triples_dot = []
    for first, second, third in TRIPLE_INDICES:
        triples.append(
            np.dot(vectors[first], np.cross(vectors[second], vectors[third]))
        )
        triples_dot.append(
            np.dot(vector_dots[first], np.cross(vectors[second], vectors[third]))
            + np.dot(
                vectors[first], np.cross(vector_dots[second], vectors[third])
            )
            + np.dot(
                vectors[first], np.cross(vectors[second], vector_dots[third])
            )
        )

    m1, m2, m3 = (float(value) for value in parameters.masses)
    m12 = m1 + m2
    total = m12 + m3
    mu12 = m1 * m2 / m12
    mu3_12 = m3 * m12 / total
    p_rho, p_lambda = vectors[2], vectors[3]
    p_rho_dot, p_lambda_dot = vector_dots[2], vector_dots[3]
    kinetic = [
        float(np.dot(p_rho, p_rho) / (2.0 * mu12)),
        float(np.dot(p_lambda, p_lambda) / (2.0 * mu3_12)),
    ]
    kinetic_dot = [
        float(np.dot(p_rho, p_rho_dot) / mu12),
        float(np.dot(p_lambda, p_lambda_dot) / mu3_12),
    ]
    rho, lambda_vector = vectors[:2]
    rho_dot, lambda_dot = vector_dots[:2]
    pair_vectors = (
        (rho, rho_dot, m1 * m2),
        (
            lambda_vector - (m1 / m12) * rho,
            lambda_dot - (m1 / m12) * rho_dot,
            m2 * m3,
        ),
        (
            -lambda_vector - (m2 / m12) * rho,
            -lambda_dot - (m2 / m12) * rho_dot,
            m3 * m1,
        ),
    )
    potentials = [_potential(*pair) for pair in pair_vectors]
    values = np.concatenate(
        (dots, np.asarray(triples), np.asarray(kinetic), [item[0] for item in potentials])
    )
    derivatives = np.concatenate(
        (
            dots_dot,
            np.asarray(triples_dot),
            np.asarray(kinetic_dot),
            [item[1] for item in potentials],
        )
    )
    return values, derivatives


def evaluate_feature_library(
    state: ArrayLike,
    derivative: ArrayLike,
    parameters: SystemParameters,
) -> FeatureEvaluation:
    """Evaluate all degree-zero, one, and two primitive monomials."""

    state_array = _vector(state, "state")
    derivative_array = _vector(derivative, "derivative")
    primitives, primitives_dot = _primitive_values(
        state_array, derivative_array, parameters
    )
    products = np.array(
        [primitives[first] * primitives[second] for first, second in PRODUCT_PAIRS]
    )
    products_dot = np.array(
        [
            primitives_dot[first] * primitives[second]
            + primitives[first] * primitives_dot[second]
            for first, second in PRODUCT_PAIRS
        ]
    )
    monomials = np.concatenate(([1.0], primitives, products))
    monomials_dot = np.concatenate(([0.0], primitives_dot, products_dot))
    masses = np.asarray(parameters.masses, dtype=np.float64)
    parameter_blocks = np.array(
        [
            1.0,
            masses[0] * masses[1] + masses[1] * masses[2] + masses[2] * masses[0],
            float(np.prod(masses)),
        ]
    )
    return FeatureEvaluation(
        names=FEATURE_NAMES,
        values=np.concatenate([block * monomials for block in parameter_blocks]),
        lie_derivatives=np.concatenate(
            [block * monomials_dot for block in parameter_blocks]
        ),
    )


def _monomial_index(name: str) -> int:
    return MONOMIAL_NAMES.index(name)


def _product_name(first: str, second: str) -> str:
    left = PRIMITIVE_NAMES.index(first)
    right = PRIMITIVE_NAMES.index(second)
    if left > right:
        left, right = right, left
    return f"{PRIMITIVE_NAMES[left]}*{PRIMITIVE_NAMES[right]}"


def _block_vector(block: int, monomial_coefficients: Mapping[str, float]) -> FloatArray:
    result = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    offset = block * len(MONOMIAL_NAMES)
    for name, coefficient in monomial_coefficients.items():
        result[offset + _monomial_index(name)] = coefficient
    return result


def _squared_linear(linear: Mapping[str, float]) -> dict[str, float]:
    output: dict[str, float] = {}
    items = list(linear.items())
    for first_index, (first, first_coefficient) in enumerate(items):
        for second, second_coefficient in items[first_index:]:
            factor = 1.0 if first == second else 2.0
            name = _product_name(first, second)
            output[name] = output.get(name, 0.0) + (
                factor * first_coefficient * second_coefficient
            )
    return output


def known_algebra_coefficients() -> dict[str, FloatArray]:
    """Return all represented parameter and known-integral algebra directions."""

    energy = {name: 1.0 for name in ENERGY_NAMES}
    angular_momentum_squared = {
        _product_name(DOT_NAMES[0], DOT_NAMES[7]): 1.0,
        _product_name(DOT_NAMES[2], DOT_NAMES[2]): -1.0,
        _product_name(DOT_NAMES[4], DOT_NAMES[9]): 1.0,
        _product_name(DOT_NAMES[6], DOT_NAMES[6]): -1.0,
        _product_name(DOT_NAMES[1], DOT_NAMES[8]): 2.0,
        _product_name(DOT_NAMES[3], DOT_NAMES[5]): -2.0,
    }
    energy_squared = _squared_linear(energy)
    controls: dict[str, FloatArray] = {}
    for block, parameter in enumerate(PARAMETER_NAMES):
        controls[f"{parameter}:constant"] = _block_vector(
            block, {"constant": 1.0}
        )
        controls[f"{parameter}:H"] = _block_vector(block, energy)
        controls[f"{parameter}:H2"] = _block_vector(block, energy_squared)
        controls[f"{parameter}:L2"] = _block_vector(
            block, angular_momentum_squared
        )
    return controls
