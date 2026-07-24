"""Source-disjoint exact Hessian checks for WP6-FI1-v1."""

from __future__ import annotations

import sympy as sp


def mass_invariant(masses: tuple[sp.Rational, ...]) -> sp.Expr:
    m1, m2, m3 = masses
    return sp.cancel((m1 * m2 + m2 * m3 + m3 * m1) / (m1 + m2 + m3) ** 2)


def _lagrange_positions(
    masses: tuple[sp.Rational, ...],
) -> list[sp.Matrix]:
    m1, m2, m3 = masses
    total = m1 + m2 + m3
    alpha = sp.Rational(1, 2)
    beta = sp.sqrt(3) / 2
    unscaled = [
        sp.Matrix([(m2 + 2 * m3) * alpha, m2 * beta]),
        sp.Matrix([-(m1 - m3) * alpha, -(m1 + m3) * beta]),
        sp.Matrix([-(2 * m1 + m2) * alpha, m2 * beta]),
    ]
    return [total ** sp.Rational(-2, 3) * value for value in unscaled]


def mass_weighted_hessian(
    masses: tuple[sp.Rational, ...],
) -> sp.Matrix:
    positions = _lagrange_positions(masses)
    hessian = sp.zeros(6)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        delta = positions[i] - positions[j]
        radius = sp.sqrt(sp.expand(delta.dot(delta)))
        block = masses[i] * masses[j] * (
            sp.eye(2) / radius**3
            - 3 * delta * delta.T / radius**5
        )
        for row in range(2):
            for column in range(2):
                hessian[2 * i + row, 2 * i + column] += block[row, column]
                hessian[2 * j + row, 2 * j + column] += block[row, column]
                hessian[2 * i + row, 2 * j + column] -= block[row, column]
                hessian[2 * j + row, 2 * i + column] -= block[row, column]
    scaling = sp.diag(
        *(1 / sp.sqrt(mass) for mass in masses for _ in range(2))
    )
    return sp.simplify(scaling * hessian * scaling)


def hessian_charpoly(mass_strings: tuple[str, str, str]) -> dict[str, object]:
    masses = tuple(sp.Rational(value) for value in mass_strings)
    q_value = mass_invariant(masses)
    variable = sp.symbols("lambda")
    observed = sp.factor(
        mass_weighted_hessian(masses).charpoly(variable).as_expr()
    )
    nonclassical = variable**2 + variable + (27 * q_value - 8) / 4
    expected = sp.factor(
        variable**2 * (variable + 2) * (variable - 1) * nonclassical
    )
    return {
        "Q": str(q_value),
        "observed_charpoly": str(observed),
        "expected_charpoly": str(expected),
        "exact_match": sp.simplify(observed - expected) == 0,
        "center_of_mass_zero": all(
            sp.simplify(value) == 0
            for value in sum(
                (
                    mass * position
                    for mass, position in zip(
                        masses, _lagrange_positions(masses), strict=True
                    )
                ),
                sp.zeros(2, 1),
            )
        ),
    }

def branch_identities() -> dict[str, bool]:
    a, b = sp.symbols("a b", positive=True)
    q_from_second_table_conditions = sp.cancel(
        6 * a / (sp.Rational(189, 8) * a)
    )
    integer = sp.symbols("n", integer=True)
    pair_relation_identity = sp.expand(
        (13 - 2 * integer**2) ** 2
        - (169 - 144 * integer**2 * (13 - integer**2) / 36)
    )
    return {
        "second_table_conditions_force_16_over_63": (
            q_from_second_table_conditions == sp.Rational(16, 63)
        ),
        "incompatible_with_8_over_27": (
            q_from_second_table_conditions != sp.Rational(8, 27)
        ),
        "pair_relation_elimination_identity": (
            sp.simplify(pair_relation_identity) == 0
        ),
    }
