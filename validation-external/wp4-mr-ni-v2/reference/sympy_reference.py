"""Source-disjoint SymPy reference for WP4-MR-NI-v2 exact arithmetic."""

from __future__ import annotations

import math
from typing import Sequence

import sympy


EXCEPTIONAL = (sympy.Rational(1, 3), sympy.Rational(8, 27), sympy.Rational(2, 9))


def parse_rational(value: object) -> sympy.Rational:
    if isinstance(value, bool):
        raise TypeError("boolean values are not rational inputs")
    if isinstance(value, sympy.Rational):
        return value
    if isinstance(value, int):
        return sympy.Rational(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("floating-point input must be finite")
        numerator, denominator = value.as_integer_ratio()
        return sympy.Rational(numerator, denominator)
    if isinstance(value, str):
        stripped = value.strip()
        unsigned = stripped.lstrip("+-").lower()
        if unsigned.startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("hexadecimal input must be finite")
            numerator, denominator = parsed.as_integer_ratio()
            return sympy.Rational(numerator, denominator)
        return sympy.Rational(stripped)
    raise TypeError(f"unsupported rational input type: {type(value).__name__}")


def mass_invariant(masses: Sequence[object]) -> sympy.Rational:
    if len(masses) != 3:
        raise ValueError("exactly three masses are required")
    first, second, third = (parse_rational(value) for value in masses)
    if any(value <= 0 for value in (first, second, third)):
        raise ValueError("all masses must be strictly positive")
    return sympy.cancel(
        (first * second + second * third + third * first)
        / (first + second + third) ** 2
    )


def exponent_polynomial(sigma: object) -> tuple[sympy.Rational, ...]:
    value = parse_rational(sigma)
    variable = sympy.symbols("lambda")
    expression = sympy.expand(
        ((2 * variable - 3) ** 2 - 13) ** 2 - 144 * (1 - 3 * value)
    )
    polynomial = sympy.Poly(expression, variable)
    return tuple(sympy.Rational(coefficient) for coefficient in polynomial.all_coeffs())


def classify_masses(masses: Sequence[object]) -> dict[str, object]:
    parsed = tuple(parse_rational(value) for value in masses)
    sigma = mass_invariant(parsed)
    return {
        "masses": [str(value) for value in parsed],
        "sigma": str(sigma),
        "universal_complete_meromorphic_integrability_obstructed": True,
        "single_additional_status": (
            "LINEAR_NVE_EXCEPTION" if sigma in EXCEPTIONAL else "OBSTRUCTED"
        ),
        "exceptional_linear_nve": sigma in EXCEPTIONAL,
        "exponent_polynomial": [str(value) for value in exponent_polynomial(sigma)],
    }
