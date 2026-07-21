"""Source-disjoint high-precision physical angular momentum squared."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import mpmath


def _mp_fraction(value: str) -> mpmath.mpf:
    fraction = Fraction(value)
    return mpmath.mpf(fraction.numerator) / fraction.denominator


def evaluate(case: dict[str, Any], *, dps: int = 80) -> mpmath.mpf:
    """Evaluate |sum_i q_i cross (m_i v_i)|^2 from rational inputs."""

    with mpmath.workdps(dps):
        positions = [[_mp_fraction(value) for value in row] for row in case["positions"]]
        velocities = [
            [_mp_fraction(value) for value in row] for row in case["velocities"]
        ]
        masses = [_mp_fraction(value) for value in case["masses"]]
        angular = [mpmath.mpf("0") for _ in range(3)]
        for position, velocity, mass in zip(
            positions, velocities, masses, strict=True
        ):
            momentum = [mass * component for component in velocity]
            angular[0] += position[1] * momentum[2] - position[2] * momentum[1]
            angular[1] += position[2] * momentum[0] - position[0] * momentum[2]
            angular[2] += position[0] * momentum[1] - position[1] * momentum[0]
        return mpmath.fsum(component * component for component in angular)
