"""Source-disjoint 80-digit evaluator for the v2 Reynolds feature direction."""

from __future__ import annotations

from itertools import combinations_with_replacement, permutations
from typing import Any, Sequence

import mpmath


GRAM_PAIRS = (
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
BODY_PERMUTATIONS = tuple(permutations(range(3)))


def descriptors() -> tuple[tuple[int, tuple[int, ...], tuple[int, ...]], ...]:
    output = []
    for denominator in range(3):
        for gram_degree in (1, 2):
            for grams in combinations_with_replacement(range(10), gram_degree):
                for parameter_degree in range(0, 3 - gram_degree):
                    for parameters in combinations_with_replacement(
                        range(3), parameter_degree
                    ):
                        output.append((denominator, grams, parameters))
    return tuple(output)


def structural_zeros() -> tuple[int, ...]:
    quadratic = {(0, 3), (3, 9), (4, 5), (5, 7)}
    return tuple(
        index
        for index, (_, grams, _) in enumerate(descriptors())
        if (len(grams) == 1 and grams[0] in (3, 5))
        or (len(grams) == 2 and grams in quadratic)
    )


def _rational(value: str) -> mpmath.mpf:
    numerator, separator, denominator = value.partition("/")
    return (
        mpmath.mpf(numerator) / mpmath.mpf(denominator)
        if separator
        else mpmath.mpf(value)
    )


def _dot(first: Sequence[mpmath.mpf], second: Sequence[mpmath.mpf]) -> mpmath.mpf:
    return mpmath.fsum(left * right for left, right in zip(first, second, strict=True))


def _subtract(
    first: Sequence[mpmath.mpf], second: Sequence[mpmath.mpf]
) -> list[mpmath.mpf]:
    return [left - right for left, right in zip(first, second, strict=True)]


def _norm(value: Sequence[mpmath.mpf]) -> mpmath.mpf:
    return mpmath.sqrt(_dot(value, value))


def _physical(
    case: dict[str, Any],
) -> tuple[list[list[mpmath.mpf]], list[list[mpmath.mpf]], list[mpmath.mpf]]:
    positions = [[_rational(value) for value in row] for row in case["positions"]]
    velocities = [[_rational(value) for value in row] for row in case["velocities"]]
    masses = [_rational(value) for value in case["masses"]]
    return positions, velocities, masses


def _flow(
    positions: list[list[mpmath.mpf]],
    velocities: list[list[mpmath.mpf]],
    masses: list[mpmath.mpf],
) -> tuple[list[list[mpmath.mpf]], list[list[mpmath.mpf]], mpmath.mpf]:
    accelerations = [[mpmath.mpf("0") for _ in range(3)] for _ in range(3)]
    distances = []
    for first, second in ((0, 1), (0, 2), (1, 2)):
        displacement = _subtract(positions[second], positions[first])
        distance = _norm(displacement)
        distances.append(distance)
        factor = distance**-3
        for component in range(3):
            accelerations[first][component] += (
                factor * masses[second] * displacement[component]
            )
            accelerations[second][component] -= (
                factor * masses[first] * displacement[component]
            )
    clock = mpmath.fprod(distances)
    return (
        [[clock * value for value in row] for row in velocities],
        [[clock * value for value in row] for row in accelerations],
        clock,
    )


def _energy(
    positions: list[list[mpmath.mpf]],
    velocities: list[list[mpmath.mpf]],
    masses: list[mpmath.mpf],
) -> mpmath.mpf:
    kinetic = mpmath.fsum(
        masses[body] * _dot(velocities[body], velocities[body]) / 2 for body in range(3)
    )
    potential = -mpmath.fsum(
        masses[first]
        * masses[second]
        / _norm(_subtract(positions[first], positions[second]))
        for first, second in ((0, 1), (1, 2), (2, 0))
    )
    return kinetic + potential


def evaluate(
    case: dict[str, Any], *, dps: int = 80
) -> tuple[list[mpmath.mpf], list[mpmath.mpf]]:
    with mpmath.workdps(dps):
        positions, velocities, masses = _physical(case)
        position_dot, velocity_dot, _ = _flow(positions, velocities, masses)
        momenta = [
            [masses[body] * value for value in velocities[body]] for body in range(3)
        ]
        momentum_dot = [
            [masses[body] * value for value in velocity_dot[body]] for body in range(3)
        ]
        distances = [
            _norm(_subtract(positions[first], positions[second]))
            for first, second in ((0, 1), (1, 2), (2, 0))
        ]
        collision = mpmath.fprod(distances)
        collision_dot = collision * mpmath.fsum(
            _dot(
                _subtract(positions[first], positions[second]),
                _subtract(position_dot[first], position_dot[second]),
            )
            / distances[index] ** 2
            for index, (first, second) in enumerate(((0, 1), (1, 2), (2, 0)))
        )
        total_mass = mpmath.fsum(masses)
        center = [
            mpmath.fsum(masses[body] * positions[body][component] for body in range(3))
            / total_mass
            for component in range(3)
        ]
        center_dot = [
            mpmath.fsum(
                masses[body] * position_dot[body][component] for body in range(3)
            )
            / total_mass
            for component in range(3)
        ]
        centered = [_subtract(row, center) for row in positions]
        centered_dot = [_subtract(row, center_dot) for row in position_dot]
        inertia = mpmath.fsum(
            masses[body] * _dot(centered[body], centered[body]) for body in range(3)
        )
        inertia_dot = 2 * mpmath.fsum(
            masses[body] * _dot(centered[body], centered_dot[body]) for body in range(3)
        )
        denominator_values = (mpmath.mpf(1), collision, inertia)
        denominator_derivatives = (mpmath.mpf(0), collision_dot, inertia_dot)
        parameters = (
            _energy(positions, velocities, masses),
            masses[0] * masses[1] + masses[1] * masses[2] + masses[2] * masses[0],
            masses[0] * masses[1] * masses[2],
        )
        per_values = []
        per_derivatives = []
        for first, second, central in BODY_PERMUTATIONS:
            vectors = (
                _subtract(positions[first], positions[central]),
                _subtract(positions[second], positions[central]),
                momenta[first],
                momenta[second],
            )
            vector_dot = (
                _subtract(position_dot[first], position_dot[central]),
                _subtract(position_dot[second], position_dot[central]),
                momentum_dot[first],
                momentum_dot[second],
            )
            grams = [_dot(vectors[a], vectors[b]) for a, b in GRAM_PAIRS]
            gram_dot = [
                _dot(vector_dot[a], vectors[b]) + _dot(vectors[a], vector_dot[b])
                for a, b in GRAM_PAIRS
            ]
            local_values = []
            local_derivatives = []
            for denominator, gram_indices, parameter_indices in descriptors():
                factor = mpmath.fprod(parameters[index] for index in parameter_indices)
                numerator = factor * mpmath.fprod(
                    grams[index] for index in gram_indices
                )
                numerator_dot = mpmath.mpf(0)
                for differentiated, gram_index in enumerate(gram_indices):
                    term = factor * gram_dot[gram_index]
                    for position, index in enumerate(gram_indices):
                        if position != differentiated:
                            term *= grams[index]
                    numerator_dot += term
                divisor = denominator_values[denominator]
                divisor_dot = denominator_derivatives[denominator]
                local_values.append(numerator / divisor)
                local_derivatives.append(
                    (numerator_dot * divisor - numerator * divisor_dot) / divisor**2
                )
            per_values.append(local_values)
            per_derivatives.append(local_derivatives)
        values = [
            mpmath.fsum(row[index] for row in per_values) / 6 for index in range(285)
        ]
        derivatives = [
            mpmath.fsum(row[index] for row in per_derivatives) / 6
            for index in range(285)
        ]
        for index in structural_zeros():
            values[index] = mpmath.mpf(0)
            derivatives[index] = mpmath.mpf(0)
        return values, derivatives


def evaluate_direction(
    case: dict[str, Any], coefficients: Sequence[float], *, dps: int = 80
) -> tuple[mpmath.mpf, mpmath.mpf]:
    with mpmath.workdps(dps):
        values, derivatives = evaluate(case, dps=dps)
        coefficient_mp = [mpmath.mpf(float(value)) for value in coefficients]
        return (
            mpmath.fsum(
                left * right for left, right in zip(values, coefficient_mp, strict=True)
            ),
            mpmath.fsum(
                left * right
                for left, right in zip(derivatives, coefficient_mp, strict=True)
            ),
        )
