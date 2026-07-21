"""Exact mass-invariant arithmetic for the locked Morales-Ramis application."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Sequence, TypeAlias


RationalInput: TypeAlias = Fraction | int | float | str

OBSTRUCTED = "OBSTRUCTED"
LINEAR_NVE_EXCEPTION = "LINEAR_NVE_EXCEPTION"
EXCEPTIONAL_SIGMA = (
    Fraction(1, 3),
    Fraction(8, 27),
    Fraction(2, 9),
)


def exact_fraction(value: RationalInput) -> Fraction:
    """Parse repository decimal, fraction, float, or hexadecimal values exactly."""

    if isinstance(value, bool):
        raise TypeError("boolean values are not rational inputs")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("floating-point input must be finite")
        numerator, denominator = value.as_integer_ratio()
        return Fraction(numerator, denominator)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("rational input must not be empty")
        unsigned = stripped.lstrip("+-").lower()
        if unsigned.startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("hexadecimal input must be finite")
            numerator, denominator = parsed.as_integer_ratio()
            return Fraction(numerator, denominator)
        return Fraction(stripped)
    raise TypeError(f"unsupported rational input type: {type(value).__name__}")


def _positive_masses(
    masses: Sequence[RationalInput],
) -> tuple[Fraction, Fraction, Fraction]:
    if len(masses) != 3:
        raise ValueError("exactly three masses are required")
    parsed = tuple(exact_fraction(value) for value in masses)
    if any(value <= 0 for value in parsed):
        raise ValueError("all masses must be strictly positive")
    return parsed  # type: ignore[return-value]


def mass_invariant(masses: Sequence[RationalInput]) -> Fraction:
    """Return sigma=(m1*m2+m2*m3+m3*m1)/(m1+m2+m3)^2 exactly."""

    first, second, third = _positive_masses(masses)
    numerator = first * second + second * third + third * first
    denominator = (first + second + third) ** 2
    return numerator / denominator


def exponent_polynomial(sigma: RationalInput) -> tuple[Fraction, ...]:
    """Return coefficients of ((2*l-3)^2-13)^2-144*(1-3*sigma)."""

    value = exact_fraction(sigma)
    return (
        Fraction(16),
        Fraction(-96),
        Fraction(112),
        Fraction(96),
        Fraction(-128) + Fraction(432) * value,
    )


@dataclass(frozen=True)
class MoralesRamisClassification:
    masses: tuple[Fraction, Fraction, Fraction]
    sigma: Fraction
    universal_complete_meromorphic_integrability_obstructed: bool
    single_additional_status: str

    @property
    def exceptional_linear_nve(self) -> bool:
        return self.single_additional_status == LINEAR_NVE_EXCEPTION

    def as_payload(self) -> dict[str, object]:
        return {
            "masses": [str(value) for value in self.masses],
            "sigma": str(self.sigma),
            "universal_complete_meromorphic_integrability_obstructed": self.universal_complete_meromorphic_integrability_obstructed,
            "single_additional_status": self.single_additional_status,
            "exceptional_linear_nve": self.exceptional_linear_nve,
            "exponent_polynomial": [
                str(value) for value in exponent_polynomial(self.sigma)
            ],
        }


def classify_masses(masses: Sequence[RationalInput]) -> MoralesRamisClassification:
    parsed = _positive_masses(masses)
    sigma = mass_invariant(parsed)
    return MoralesRamisClassification(
        masses=parsed,
        sigma=sigma,
        universal_complete_meromorphic_integrability_obstructed=True,
        single_additional_status=(
            LINEAR_NVE_EXCEPTION if sigma in EXCEPTIONAL_SIGMA else OBSTRUCTED
        ),
    )
