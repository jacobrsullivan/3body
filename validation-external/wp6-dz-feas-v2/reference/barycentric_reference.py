"""Source-disjoint barycentric derivation for WP6-DZ-FEAS-v2."""

from __future__ import annotations

from typing import Sequence

import sympy as sp


def derive(
    masses: Sequence[int | sp.Rational | sp.Expr],
) -> dict[str, sp.Expr | sp.Matrix | tuple[sp.Expr, ...]]:
    """Derive the gap model directly from barycentric Newton equations."""

    if len(masses) != 3 or any(isinstance(value, (bool, float)) for value in masses):
        raise ValueError("reference masses must be three exact values")
    m1, m2, m3 = (sp.sympify(value) for value in masses)
    if any(mass.is_positive is not True for mass in (m1, m2, m3)):
        raise ValueError("reference masses must be provably strictly positive")

    x, v, u, r = sp.symbols("x v u r", nonzero=True)
    total = m1 + m2 + m3
    a = r * x
    b = r * (1 - x)
    positions = (
        -((m2 + m3) * a + m3 * b) / total,
        (m1 * a - m3 * b) / total,
        (m1 * a + (m1 + m2) * b) / total,
    )
    za = x * v + u
    zb = (1 - x) * v - u
    da = za / sp.sqrt(r)
    db = zb / sp.sqrt(r)
    velocities = (
        -((m2 + m3) * da + m3 * db) / total,
        (m1 * da - m3 * db) / total,
        (m1 * da + (m1 + m2) * db) / total,
    )

    accelerations = (
        m2 / a**2 + m3 / (a + b) ** 2,
        -m1 / a**2 + m3 / b**2,
        -m2 / b**2 - m1 / (a + b) ** 2,
    )
    acceleration_a = sp.cancel(r**2 * (accelerations[1] - accelerations[0]))
    acceleration_b = sp.cancel(r**2 * (accelerations[2] - accelerations[1]))
    A = sp.cancel(acceleration_a + acceleration_b)
    B = sp.cancel(acceleration_a - x * A)

    kinetic = sp.cancel(
        sum(mass * velocity**2 for mass, velocity in zip((m1, m2, m3), velocities)) / 2
    )
    potential = m1 * m2 / a + m2 * m3 / b + m1 * m3 / (a + b)
    normalized_energy = sp.cancel(r * (kinetic - potential))
    da_independent, db_independent = sp.symbols("da_independent db_independent")
    barycentric_gap_velocities = (
        -((m2 + m3) * da_independent + m3 * db_independent) / total,
        (m1 * da_independent - m3 * db_independent) / total,
        (m1 * da_independent + (m1 + m2) * db_independent) / total,
    )
    metric = sp.hessian(
        sum(
            mass * velocity**2
            for mass, velocity in zip((m1, m2, m3), barycentric_gap_velocities)
        )
        / 2,
        (da_independent, db_independent),
    )
    return {
        "x": x,
        "v": v,
        "u": u,
        "r": r,
        "positions": tuple(sp.cancel(value) for value in positions),
        "velocities": tuple(sp.cancel(value) for value in velocities),
        "acceleration_a": acceleration_a,
        "acceleration_b": acceleration_b,
        "A": A,
        "B": B,
        "mass_metric": sp.simplify(metric),
        "normalized_energy": normalized_energy,
        "center_of_mass": sp.simplify(
            sum(mass * position for mass, position in zip((m1, m2, m3), positions))
        ),
        "linear_momentum": sp.simplify(
            sum(mass * velocity for mass, velocity in zip((m1, m2, m3), velocities))
        ),
    }
