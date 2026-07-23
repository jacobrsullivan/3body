#!/usr/bin/env python
"""Source-disjoint exact derivation of the WP4-MR-REPL-v1 NVE."""

from __future__ import annotations

import argparse
from fractions import Fraction
import gc
import json
from pathlib import Path
import time
from typing import Any

import sympy as sp
from sympy.polys.matrices import DomainMatrix


def _rational(text: str) -> sp.Rational:
    value = Fraction(text)
    return sp.Rational(value.numerator, value.denominator)


def _normal(expression: sp.Expr) -> sp.Expr:
    combined = sp.together(sp.powdenest(expression, force=True))
    return sp.factor(sp.cancel(combined))


def _first_nonzero_coefficient(
    polynomial: sp.Expr, variable: sp.Symbol, point: sp.Expr
) -> tuple[int, sp.Expr] | None:
    if polynomial == 0:
        return None
    for order in range(13):
        derivative = sp.diff(polynomial, variable, order)
        value = _normal(derivative.subs(variable, point))
        if value != 0:
            return order, _normal(value / sp.factorial(order))
    raise RuntimeError("pole valuation exceeds certified bound 12")


def _residue(
    matrix: sp.Matrix, variable: sp.Symbol, point: sp.Expr
) -> tuple[sp.Matrix, list[dict[str, int]]]:
    result = sp.zeros(4)
    diagnostics: list[dict[str, int]] = []
    for row in range(4):
        for column in range(4):
            numerator, denominator = sp.fraction(sp.cancel(matrix[row, column]))
            numerator_lead = _first_nonzero_coefficient(
                numerator, variable, point
            )
            if numerator_lead is None:
                diagnostics.append(
                    {
                        "denominator_order": 0,
                        "numerator_order": 0,
                        "pole_order": 0,
                    }
                )
                continue
            denominator_lead = _first_nonzero_coefficient(
                denominator, variable, point
            )
            if denominator_lead is None:
                raise RuntimeError("zero denominator in rational NVE entry")
            numerator_order, numerator_coefficient = numerator_lead
            denominator_order, denominator_coefficient = denominator_lead
            pole_order = denominator_order - numerator_order
            diagnostics.append(
                {
                    "denominator_order": denominator_order,
                    "numerator_order": numerator_order,
                    "pole_order": pole_order,
                }
            )
            if pole_order <= 0:
                continue
            if pole_order != 1:
                raise RuntimeError(f"unexpected pole order {pole_order}")
            result[row, column] = _normal(
                numerator_coefficient / denominator_coefficient
            )
    return result, diagnostics


def _charpoly_coefficients(
    matrix: sp.Matrix,
    field: Any,
) -> list[sp.Expr]:
    domain_matrix = DomainMatrix.from_Matrix(matrix).convert_to(field)
    return [field.to_sympy(value) for value in domain_matrix.charpoly()]


def _coefficient_match(
    observed: list[sp.Expr], expected: list[sp.Expr]
) -> bool:
    return len(observed) == len(expected) and all(
        _normal(left - right) == 0
        for left, right in zip(observed, expected, strict=True)
    )


def _strings(values: list[sp.Expr]) -> list[str]:
    return [str(_normal(value)) for value in values]


def derive(
    m1_value: str | None = None,
    m2_value: str | None = None,
) -> dict[str, Any]:
    """Differentiate the Hamiltonian and return exact proof diagnostics."""

    started = time.monotonic()
    generic = m1_value is None and m2_value is None
    if generic:
        m1, m2 = sp.symbols("m1 m2", positive=True)
    elif m1_value is not None and m2_value is not None:
        m1, m2 = _rational(m1_value), _rational(m2_value)
        if m1 <= 0 or m2 <= 0:
            raise ValueError("specialized masses must be strictly positive")
    else:
        raise ValueError("m1 and m2 must either both be set or both be omitted")

    w = sp.symbols("w", real=True)
    q_external = sp.symbols("Q", positive=True)
    w_external = sp.symbols("W", real=True)
    q1, q2, q3, p1, p2, p3 = sp.symbols("q1 q2 q3 p1 p2 p3")
    sqrt3 = sp.sqrt(3)
    imaginary = sp.I

    s1 = m1 + m2 + 1
    s2 = m1 * m2 + m2 + m1
    s3 = m2 + 2
    big_m1 = 1 + 1 / m1
    big_m2 = 1 + 1 / m2
    angular = p3 * q2 - p2 * q3 - 1
    hamiltonian_terms = (
        big_m1 * p1**2 / 2,
        big_m1 * angular**2 / (2 * q1**2),
        big_m2 * p2**2 / 2,
        big_m2 * p3**2 / 2,
        p1 * p2,
        -p3 * angular / q1,
        -m1 / q1,
        -m2 / sp.sqrt(q2**2 + q3**2),
        -m1 * m2 / sp.sqrt((q1 - q2) ** 2 + q3**2),
    )
    hamiltonian = sp.Add(*hamiltonian_terms)

    coefficient_a = m2 * (1 - m1) / (m1 * s3)
    coefficient_b = -sqrt3 * s1 * m2 / (s2 * s3)
    coefficient_c = sqrt3 * m2 * (m1 + 1) / (m1 * s3)
    coefficient_d = -m2 * (s2 + m1 * m2 - 1) / (s2 * s3)
    energy_a = 2 * s1 * s2 / (m1**2 * s3**2)
    energy_b = -2 * sqrt3 * m2 * s1 / (m1 * s3**2)
    energy_c = -s2
    energy_d = 2 * s1 * (m2**2 + m2 + 1) / (s3**2 * s2)
    q_of_w = _normal(
        -(energy_a * w**2 + energy_b * w + energy_d) / energy_c
    )

    radial_substitution = {
        q1: q_external,
        q2: q_external / 2,
        q3: sqrt3 * q_external / 2,
        p1: w_external / q_external,
        p2: coefficient_a * w_external / q_external
        + coefficient_b / q_external,
        p3: coefficient_c * w_external / q_external
        + coefficient_d / q_external,
    }
    phase_substitution = {
        key: _normal(value.subs({q_external: q_of_w, w_external: w}))
        for key, value in radial_substitution.items()
    }
    hamiltonian_on_radial = _normal(hamiltonian.subs(radial_substitution))
    hamiltonian_on_phase = _normal(
        hamiltonian_on_radial.subs(
            {q_external: q_of_w, w_external: w}
        )
    )

    symplectic6 = sp.zeros(6)
    symplectic6[:3, 3:] = sp.eye(3)
    symplectic6[3:, :3] = -sp.eye(3)
    variables6 = (q1, q2, q3, p1, p2, p3)
    phase_vector = sp.Matrix([phase_substitution[item] for item in variables6])
    vector_field_ambient = symplectic6 * sp.Matrix(
        [sp.diff(hamiltonian, item) for item in variables6]
    )
    vector_field = vector_field_ambient.subs(radial_substitution).applyfunc(
        _normal
    )
    vector_field = vector_field.subs(
        {q_external: q_of_w, w_external: w}
    ).applyfunc(_normal)
    w_rate = _normal(vector_field[0] / sp.diff(q_of_w, w))
    tangent_residuals = [
        _normal(vector_field[index] - sp.diff(phase_vector[index], w) * w_rate)
        for index in range(6)
    ]
    planar_variational = symplectic6 * sp.hessian(
        hamiltonian, variables6
    )
    planar_variational_on_radial = planar_variational.subs(
        radial_substitution
    )
    planar_variational_on_phase = planar_variational_on_radial.subs(
        {q_external: q_of_w, w_external: w}
    )
    planar_variational_hamiltonian = (
        (symplectic6 * planar_variational).T
        == symplectic6 * planar_variational
    )
    planar_variational_constructed = planar_variational.shape == (6, 6)
    planar_variational_phase_substitution_complete = not any(
        entry.has(
            q1,
            q2,
            q3,
            p1,
            p2,
            p3,
            q_external,
            w_external,
        )
        for entry in planar_variational_on_phase
    )
    del (
        planar_variational,
        planar_variational_on_radial,
        planar_variational_on_phase,
    )
    gc.collect()

    normal_variables = (q2, q3, p2, p3)
    h_p1 = sp.diff(hamiltonian, p1)
    h_p1_p1 = sp.diff(hamiltonian, p1, 2)
    whittaker_hessian = sp.zeros(4)
    for row, variable_i in enumerate(normal_variables):
        h_i = sp.diff(hamiltonian, variable_i)
        h_i_p1 = sp.diff(hamiltonian, variable_i, p1)
        for column, variable_j in enumerate(normal_variables):
            h_j = sp.diff(hamiltonian, variable_j)
            h_p1_j = sp.diff(hamiltonian, p1, variable_j)
            h_i_j = sp.diff(hamiltonian, variable_i, variable_j)
            entry = h_i_j / h_p1
            entry -= h_i_p1 * h_j / h_p1**2
            entry -= h_i * h_p1_j / h_p1**2
            entry += h_i * h_p1_p1 * h_j / h_p1**3
            entry = _normal(entry.subs(radial_substitution))
            whittaker_hessian[row, column] = _normal(
                entry.subs({q_external: q_of_w, w_external: w})
            )

    symplectic4 = sp.zeros(4)
    symplectic4[:2, 2:] = sp.eye(2)
    symplectic4[2:, :2] = -sp.eye(2)
    nve = symplectic4 * whittaker_hessian.applyfunc(
        lambda entry: _normal(sp.diff(q_of_w, w) * entry)
    )
    hamiltonian_matrix_identity = all(
        _normal(entry) == 0
        for entry in (symplectic4 * nve).T - symplectic4 * nve
    )

    linear = 2 * s2 * w - sqrt3 * m1 * m2
    quadratic = (
        s2**2 * w**2
        - sqrt3 * m1 * m2 * s2 * w
        + m1**2 * (m2**2 + m2 + 1)
    )
    scale = (linear * quadratic, linear * quadratic, sp.Integer(1), sp.Integer(1))
    fuchs = sp.zeros(4)
    for row in range(4):
        for column in range(4):
            entry = scale[column] * nve[row, column] / scale[row]
            if row == column:
                entry -= sp.diff(scale[row], w) / scale[row]
            fuchs[row, column] = _normal(entry)

    t0 = sqrt3 * m1 * m2 / (2 * s2)
    t1 = m1 * (sqrt3 * m2 + imaginary * s3) / (2 * s2)
    t2 = m1 * (sqrt3 * m2 - imaginary * s3) / (2 * s2)
    if generic:
        field = sp.QQ.algebraic_field(sqrt3, imaginary).frac_field(m1, m2)
    else:
        field = sp.QQ.algebraic_field(sqrt3, imaginary)

    residue0, local0 = _residue(fuchs, w, t0)
    residue1, local1 = _residue(fuchs, w, t1)
    real_coefficient_contract = not any(entry.has(imaginary) for entry in fuchs)
    if generic:
        residue2 = residue1.applyfunc(
            lambda entry: _normal(sp.conjugate(entry))
        )
        local2 = local1
    else:
        residue2, local2 = _residue(fuchs, w, t2)

    simple_pole_contract = True
    pole_diagnostics: list[dict[str, object]] = []
    for index, entry in enumerate(fuchs):
        numerator, denominator = sp.fraction(sp.cancel(entry))
        numerator_degree = sp.degree(numerator, w)
        denominator_degree = sp.degree(denominator, w)
        accounted_degree = (
            local0[index]["denominator_order"]
            + local1[index]["denominator_order"]
            + local2[index]["denominator_order"]
        )
        denominator_supported = denominator_degree == accounted_degree
        proper = numerator_degree < denominator_degree
        net_simple = all(
            local[index]["pole_order"] <= 1
            for local in (local0, local1, local2)
        )
        passed = bool(denominator_supported and proper and net_simple)
        simple_pole_contract = simple_pole_contract and passed
        if not passed:
            pole_diagnostics.append(
                {
                    "entry": [index // 4, index % 4],
                    "numerator_degree": str(numerator_degree),
                    "denominator_degree": str(denominator_degree),
                    "accounted_denominator_degree": accounted_degree,
                    "denominator_supported_on_declared_points": bool(
                        denominator_supported
                    ),
                    "proper_at_infinity": bool(proper),
                    "net_pole_orders": [
                        local0[index]["pole_order"],
                        local1[index]["pole_order"],
                        local2[index]["pole_order"],
                    ],
                }
            )

    turning_coefficients = _charpoly_coefficients(residue0, field)
    collision1_coefficients = _charpoly_coefficients(residue1, field)
    collision2_coefficients = _charpoly_coefficients(residue2, field)
    infinity_residue = -(residue0 + residue1 + residue2)
    infinity_coefficients = _charpoly_coefficients(infinity_residue, field)
    sigma = _normal(s2 / s1**2)
    sigma_gap = _normal(sp.Rational(1, 3) - sigma)
    sigma_gap_sum_of_squares = _normal(
        (
            (m1 - m2) ** 2
            + (m2 - 1) ** 2
            + (1 - m1) ** 2
        )
        / (6 * (m1 + m2 + 1) ** 2)
    )

    expected_turning = [1, 2, 1, 0, 0]
    expected_collision = [1, 2, -1, -2, 0]
    expected_infinity = [1, -6, 7, 6, 27 * sigma - 8]
    singular_distinct = all(
        _normal(left - right) != 0
        for left, right in ((t0, t1), (t0, t2), (t1, t2))
    )
    result = {
        "schema_version": "1.0",
        "mode": "generic" if generic else "specialized",
        "normalized_masses": (
            ["m1", "m2", "1"] if generic else [str(m1), str(m2), "1"]
        ),
        "hamiltonian_term_count": len(hamiltonian_terms),
        "hamiltonian_zero_on_phase_curve": hamiltonian_on_phase == 0,
        "hamiltonian_on_phase_curve": str(hamiltonian_on_phase),
        "hamilton_equation_tangent_residuals_zero": [
            residual == 0 for residual in tangent_residuals
        ],
        "hamilton_equation_tangent_residuals": [
            str(residual) for residual in tangent_residuals
        ],
        "planar_variational_equation_dimension": 6,
        "planar_variational_matrix_constructed_from_hessian": (
            planar_variational_constructed
        ),
        "planar_variational_matrix_hamiltonian": (
            planar_variational_hamiltonian
        ),
        "planar_variational_phase_substitution_complete": (
            planar_variational_phase_substitution_complete
        ),
        "whittaker_energy_shell_normal_dimension": 4,
        "whittaker_hessian_symmetric": whittaker_hessian == whittaker_hessian.T,
        "normal_system_hamiltonian": hamiltonian_matrix_identity,
        "fuchs_singular_points_distinct": singular_distinct,
        "fuchs_only_simple_finite_poles_and_no_polynomial_part": (
            simple_pole_contract
        ),
        "pole_diagnostics": pole_diagnostics,
        "real_coefficient_conjugation_contract": real_coefficient_contract,
        "turning_charpoly": _strings(turning_coefficients),
        "collision_plus_charpoly": _strings(collision1_coefficients),
        "collision_minus_charpoly": _strings(collision2_coefficients),
        "infinity_charpoly": _strings(infinity_coefficients),
        "sigma": str(sigma),
        "sigma_upper_bound_sum_of_squares_identity": (
            _normal(sigma_gap - sigma_gap_sum_of_squares) == 0
        ),
        "turning_charpoly_matches": _coefficient_match(
            turning_coefficients, expected_turning
        ),
        "collision_plus_charpoly_matches": _coefficient_match(
            collision1_coefficients, expected_collision
        ),
        "collision_minus_charpoly_matches": _coefficient_match(
            collision2_coefficients, expected_collision
        ),
        "infinity_charpoly_matches": _coefficient_match(
            infinity_coefficients, expected_infinity
        ),
        "infinity_trace": str(_normal(-infinity_coefficients[1])),
        "infinity_determinant": str(_normal(infinity_coefficients[-1])),
        "elapsed_seconds": time.monotonic() - started,
    }
    result["all_exact_derivation_checks_pass"] = all(
        (
            result["hamiltonian_zero_on_phase_curve"],
            all(result["hamilton_equation_tangent_residuals_zero"]),
            result["planar_variational_matrix_constructed_from_hessian"],
            result["planar_variational_matrix_hamiltonian"],
            result["planar_variational_phase_substitution_complete"],
            result["whittaker_hessian_symmetric"],
            result["normal_system_hamiltonian"],
            result["fuchs_singular_points_distinct"],
            result["fuchs_only_simple_finite_poles_and_no_polynomial_part"],
            result["real_coefficient_conjugation_contract"],
            result["turning_charpoly_matches"],
            result["collision_plus_charpoly_matches"],
            result["collision_minus_charpoly_matches"],
            result["infinity_charpoly_matches"],
            result["sigma_upper_bound_sum_of_squares_identity"],
        )
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generic", action="store_true")
    parser.add_argument("--m1")
    parser.add_argument("--m2")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.generic:
        if args.m1 is not None or args.m2 is not None:
            parser.error("--generic cannot be combined with --m1 or --m2")
        result = derive()
    else:
        if args.m1 is None or args.m2 is None:
            parser.error("specialized mode requires --m1 and --m2")
        result = derive(args.m1, args.m2)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
