"""Exact rectilinear zero-energy model locked by ``WP6-DZ-FEAS-v2``."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

import sympy as sp


SUPPORT_EXPONENTS = (-2, -1, 0, 1, 2)
SUPPORTS = tuple(
    support for size in (1, 2) for support in combinations(SUPPORT_EXPONENTS, size)
)
COVER_IDS = ("PHI-AFFINE", "PHI-LEFT-SQ", "PHI-RIGHT-SQ", "PHI-BOTH-SQ")
MASS_ORDER_CASES = (
    ("M01", (1, 1, 1)),
    ("M02", (1, 2, 3)),
    ("M03", (1, 3, 2)),
    ("M04", (2, 1, 3)),
    ("M05", (2, 3, 1)),
    ("M06", (3, 1, 2)),
    ("M07", (3, 2, 1)),
    ("M08", (2, 3, 5)),
    ("M09", (2, 5, 3)),
    ("M10", (3, 2, 5)),
    ("M11", (3, 5, 2)),
    ("M12", (5, 2, 3)),
    ("M13", (5, 3, 2)),
)


def _positive_masses(
    values: Sequence[int | sp.Rational | sp.Expr],
) -> tuple[sp.Expr, ...]:
    if len(values) != 3:
        raise ValueError("masses must contain three values")
    masses: list[sp.Expr] = []
    for value in values:
        if isinstance(value, (bool, float)):
            raise TypeError("mass inputs must be exact")
        mass = sp.sympify(value)
        if mass.is_positive is not True:
            raise ValueError("masses must be provably strictly positive")
        masses.append(mass)
    return tuple(masses)


def _canonical_numerator(expression: sp.Expr) -> sp.Expr:
    numerator, _ = sp.fraction(sp.cancel(sp.together(expression)))
    return sp.primitive(sp.Poly(sp.expand(numerator)))[1].as_expr()


@dataclass(frozen=True)
class RectilinearModel:
    """Rational McGehee vector field in one ordered collinear chamber."""

    masses: tuple[sp.Expr, sp.Expr, sp.Expr]
    x: sp.Symbol
    v: sp.Symbol
    u: sp.Symbol
    r: sp.Symbol
    za: sp.Expr
    zb: sp.Expr
    mass_metric: sp.Matrix
    potential_shape: sp.Expr
    normalized_energy: sp.Expr
    energy_numerator: sp.Expr
    A: sp.Expr
    B: sp.Expr
    vector_field: tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]


@dataclass(frozen=True)
class GraphTemplate:
    """One locked rational/Puiseux graph and its exact coefficient equations."""

    cover_id: str
    support_v: tuple[int, ...]
    support_u: tuple[int, ...]
    z: sp.Symbol
    x_of_z: sp.Expr
    v_of_z: sp.Expr
    u_of_z: sp.Expr
    coefficients: tuple[sp.Symbol, ...]
    energy_residual: sp.Expr
    v_residual: sp.Expr
    u_residual: sp.Expr

    def coefficient_equations(self, expression: sp.Expr) -> tuple[sp.Expr, ...]:
        numerator = _canonical_numerator(expression)
        polynomial = sp.Poly(numerator, self.z)
        return tuple(
            coefficient for coefficient in polynomial.all_coeffs() if coefficient != 0
        )


def build_rectilinear_model(
    masses: Sequence[int | sp.Rational | sp.Expr],
) -> RectilinearModel:
    """Build the locked arbitrary-mass rational vector field exactly."""

    m1, m2, m3 = _positive_masses(masses)
    x, v, u, r = sp.symbols("x v u r")
    total_mass = m1 + m2 + m3
    metric = sp.Matrix(
        [
            [m1 * (m2 + m3) / total_mass, m1 * m3 / total_mass],
            [m1 * m3 / total_mass, m3 * (m1 + m2) / total_mass],
        ]
    )
    za = x * v + u
    zb = (1 - x) * v - u
    velocity = sp.Matrix([za, zb])
    potential = m1 * m2 / x + m2 * m3 / (1 - x) + m1 * m3
    kinetic_twice = (velocity.T * metric * velocity)[0]
    energy = sp.cancel(kinetic_twice / 2 - potential)
    energy_numerator = sp.expand(
        x * (1 - x) * kinetic_twice
        - 2 * (m1 * m2 * (1 - x) + m2 * m3 * x + m1 * m3 * x * (1 - x))
    )

    A = sp.cancel(-m2 / x**2 - m2 / (1 - x) ** 2 - (m1 + m3))
    acceleration_a = sp.cancel(-(m1 + m2) / x**2 + m3 / (1 - x) ** 2 - m3)
    B = sp.cancel(acceleration_a - x * A)
    vector_field = (
        r * v,
        u,
        sp.cancel(v**2 / 2 + A),
        sp.cancel(B - v * u / 2),
    )
    return RectilinearModel(
        masses=(m1, m2, m3),
        x=x,
        v=v,
        u=u,
        r=r,
        za=za,
        zb=zb,
        mass_metric=metric,
        potential_shape=potential,
        normalized_energy=energy,
        energy_numerator=energy_numerator,
        A=A,
        B=B,
        vector_field=vector_field,
    )


def shape_cover(cover_id: str, z: sp.Symbol) -> sp.Expr:
    """Return one of the four frozen rational shape covers."""

    covers = {
        "PHI-AFFINE": z,
        "PHI-LEFT-SQ": z**2,
        "PHI-RIGHT-SQ": 1 - z**2,
        "PHI-BOTH-SQ": z**2 / (1 + z**2),
    }
    try:
        return covers[cover_id]
    except KeyError as error:
        raise ValueError(f"unknown shape cover: {cover_id}") from error


def _graph(
    z: sp.Symbol,
    prefix: str,
    support: Iterable[int],
) -> tuple[sp.Expr, tuple[sp.Symbol, ...]]:
    exponents = tuple(support)
    if exponents not in SUPPORTS:
        raise ValueError(f"support is outside the locked library: {exponents}")
    coefficients = sp.symbols(" ".join(f"{prefix}_{power:+d}" for power in exponents))
    if isinstance(coefficients, sp.Symbol):
        coefficients = (coefficients,)
    return (
        sp.Add(
            *(
                coefficient * z**power
                for coefficient, power in zip(coefficients, exponents)
            )
        ),
        tuple(coefficients),
    )


def build_graph_template(
    model: RectilinearModel,
    cover_id: str,
    support_v: tuple[int, ...],
    support_u: tuple[int, ...],
) -> GraphTemplate:
    """Construct all three exact graph identities for one locked template."""

    z = sp.Symbol("z")
    x_of_z = shape_cover(cover_id, z)
    v_of_z, alpha = _graph(z, "alpha", support_v)
    u_of_z, beta = _graph(z, "beta", support_u)
    substitution = {model.x: x_of_z, model.v: v_of_z, model.u: u_of_z}
    x_derivative = sp.diff(x_of_z, z)
    energy = model.normalized_energy.subs(substitution)
    v_residual = sp.diff(v_of_z, z) * u_of_z - x_derivative * (
        v_of_z**2 / 2 + model.A.subs(model.x, x_of_z)
    )
    u_residual = sp.diff(u_of_z, z) * u_of_z - x_derivative * (
        model.B.subs(model.x, x_of_z) - v_of_z * u_of_z / 2
    )
    return GraphTemplate(
        cover_id=cover_id,
        support_v=support_v,
        support_u=support_u,
        z=z,
        x_of_z=x_of_z,
        v_of_z=v_of_z,
        u_of_z=u_of_z,
        coefficients=alpha + beta,
        energy_residual=sp.cancel(energy),
        v_residual=sp.cancel(v_residual),
        u_residual=sp.cancel(u_residual),
    )


def reconstruct_barycentric_state(
    masses: Sequence[int | sp.Rational | sp.Expr],
    *,
    r: sp.Expr,
    x: sp.Expr,
    v: sp.Expr,
    u: sp.Expr,
) -> dict[str, tuple[sp.Expr, ...] | sp.Expr]:
    """Lift a reduced state to barycentric collinear positions and velocities."""

    m1, m2, m3 = _positive_masses(masses)
    total_mass = m1 + m2 + m3
    a = sp.cancel(r * x)
    b = sp.cancel(r * (1 - x))
    da = sp.cancel((x * v + u) / sp.sqrt(r))
    db = sp.cancel(((1 - x) * v - u) / sp.sqrt(r))
    positions = (
        sp.cancel(-((m2 + m3) * a + m3 * b) / total_mass),
        sp.cancel((m1 * a - m3 * b) / total_mass),
        sp.cancel((m1 * a + (m1 + m2) * b) / total_mass),
    )
    velocities = (
        sp.cancel(-((m2 + m3) * da + m3 * db) / total_mass),
        sp.cancel((m1 * da - m3 * db) / total_mass),
        sp.cancel((m1 * da + (m1 + m2) * db) / total_mass),
    )
    return {
        "a": a,
        "b": b,
        "da": da,
        "db": db,
        "positions": positions,
        "velocities": velocities,
        "center_of_mass": sp.simplify(
            sum(mass * position for mass, position in zip((m1, m2, m3), positions))
        ),
        "linear_momentum": sp.simplify(
            sum(mass * velocity for mass, velocity in zip((m1, m2, m3), velocities))
        ),
    }
