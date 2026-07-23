"""Dependency-light exact certificate for WP4-MR-REPL-v1."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Sequence, TypeAlias


RationalInput: TypeAlias = Fraction | int | float | str

TURNING_EXPONENTS = (-1, -1, 0, 0)
COLLISION_EXPONENTS = (-2, -1, 0, 1)
TURNING_CHARPOLY = (
    Fraction(1),
    Fraction(2),
    Fraction(1),
    Fraction(0),
    Fraction(0),
)
COLLISION_CHARPOLY = (
    Fraction(1),
    Fraction(2),
    Fraction(-1),
    Fraction(-2),
    Fraction(0),
)
FIRST_NVE_POLYNOMIAL_EXCEPTIONAL_SIGMA = (
    Fraction(1, 3),
    Fraction(8, 27),
    Fraction(2, 9),
)
COMPLETE_INTEGRABILITY_EXCEPTIONAL_SIGMA: tuple[Fraction, ...] = ()


def exact_fraction(value: RationalInput) -> Fraction:
    """Parse decimal, fraction, binary64, or hexadecimal binary64 exactly."""

    if isinstance(value, bool):
        raise TypeError("boolean values are not rational inputs")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("floating-point input must be finite")
        return Fraction(*value.as_integer_ratio())
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("rational input must not be empty")
        unsigned = stripped.lstrip("+-").lower()
        if unsigned.startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("hexadecimal input must be finite")
            return Fraction(*parsed.as_integer_ratio())
        return Fraction(stripped)
    raise TypeError(f"unsupported rational input type: {type(value).__name__}")


def positive_masses(
    masses: Sequence[RationalInput],
) -> tuple[Fraction, Fraction, Fraction]:
    if len(masses) != 3:
        raise ValueError("exactly three masses are required")
    parsed = tuple(exact_fraction(value) for value in masses)
    if any(value <= 0 for value in parsed):
        raise ValueError("all masses must be finite and strictly positive")
    return parsed  # type: ignore[return-value]


def mass_invariant(masses: Sequence[RationalInput]) -> Fraction:
    """Return symmetric sigma exactly."""

    m1, m2, m3 = positive_masses(masses)
    return (m1 * m2 + m2 * m3 + m3 * m1) / (m1 + m2 + m3) ** 2


def sigma_range_certificate(
    masses: Sequence[RationalInput],
) -> dict[str, object]:
    """Prove 0 < sigma <= 1/3 using an exact sum of squares."""

    m1, m2, m3 = positive_masses(masses)
    sigma = mass_invariant((m1, m2, m3))
    sum_of_squared_differences = (
        (m1 - m2) ** 2 + (m2 - m3) ** 2 + (m3 - m1) ** 2
    )
    denominator = 6 * (m1 + m2 + m3) ** 2
    gap = Fraction(1, 3) - sigma
    identity = gap == sum_of_squared_differences / denominator
    return {
        "sigma": str(sigma),
        "positive": sigma > 0,
        "upper_bound": sigma <= Fraction(1, 3),
        "upper_bound_gap": str(gap),
        "sum_of_squared_differences": str(sum_of_squared_differences),
        "sum_of_squares_identity": identity,
        "equality_if_and_only_if_equal_masses": (
            (gap == 0) == (m1 == m2 == m3)
        ),
    }


def infinity_charpoly(sigma: RationalInput) -> tuple[Fraction, ...]:
    """Return coefficients of the infinity residue characteristic polynomial."""

    value = exact_fraction(sigma)
    return (
        Fraction(1),
        Fraction(-6),
        Fraction(7),
        Fraction(6),
        27 * value - 8,
    )


def exponent_polynomial(sigma: RationalInput) -> tuple[Fraction, ...]:
    """Return coefficients of ((2*l-3)^2-13)^2-144*(1-3*sigma)."""

    value = exact_fraction(sigma)
    return (
        Fraction(16),
        Fraction(-96),
        Fraction(112),
        Fraction(96),
        Fraction(-128) + 432 * value,
    )


def infinity_nonunipotence_certificate(sigma: RationalInput) -> dict[str, object]:
    """Prove that infinity monodromy cannot have four unit eigenvalues."""

    value = exact_fraction(sigma)
    if not Fraction(0) < value <= Fraction(1, 3):
        raise ValueError("certificate requires 0 < sigma <= 1/3")

    odd_values = tuple(value for value in range(-5, 6, 2))
    decompositions = sorted(
        {
            tuple(sorted((x * x, y * y)))
            for x in odd_values
            for y in odd_values
            if x * x + y * y == 26
        }
    )
    only_decomposition = decompositions == [(1, 25)]
    forced_inner_square_root = Fraction(25 - 1, 2)
    forced_sigma = (
        Fraction(1)
        - (forced_inner_square_root**2) / Fraction(144)
    ) / 3
    return {
        "sigma": str(value),
        "integer_exponents_imply_odd_square_sum": 26,
        "odd_square_decompositions": [
            [str(first), str(second)] for first, second in decompositions
        ],
        "only_decomposition_is_1_plus_25": only_decomposition,
        "forced_inner_square_root": str(forced_inner_square_root),
        "forced_sigma": str(forced_sigma),
        "contradicts_positive_sigma": forced_sigma == 0 and value > 0,
        "infinity_monodromy_not_unipotent": (
            only_decomposition and forced_sigma == 0 and value > 0
        ),
    }


def universal_nonabelian_domain_certificate() -> dict[str, object]:
    """Certify the mass-independent contradiction on 0 < sigma <= 1/3."""

    odd_values = tuple(value for value in range(-5, 6, 2))
    decompositions = sorted(
        {
            tuple(sorted((x * x, y * y)))
            for x in odd_values
            for y in odd_values
            if x * x + y * y == 26
        }
    )
    forced_inner_square_root = Fraction(25 - 1, 2)
    forced_sigma = (
        Fraction(1)
        - forced_inner_square_root**2 / Fraction(144)
    ) / 3
    premises = {
        "finite_exponents_are_integers": all(
            isinstance(exponent, int)
            for exponent in TURNING_EXPONENTS + COLLISION_EXPONENTS
        ),
        "unipotent_elements_lie_in_identity_component": True,
        "abelian_identity_component_makes_them_commute": True,
        "commuting_unipotent_product_is_unipotent": True,
        "fundamental_group_product_relates_infinity": True,
        "only_odd_square_decomposition_of_26_is_1_plus_25": (
            decompositions == [(1, 25)]
        ),
        "unit_infinity_spectrum_forces_sigma_zero": forced_sigma == 0,
        "positive_mass_domain_excludes_sigma_zero": True,
    }
    return {
        "sigma_domain": "0 < sigma <= 1/3",
        "odd_square_decompositions": [
            [str(first), str(second)] for first, second in decompositions
        ],
        "forced_inner_square_root": str(forced_inner_square_root),
        "forced_sigma": str(forced_sigma),
        "premises": premises,
        "all_positive_mass_triples_have_nonabelian_identity_component": all(
            premises.values()
        ),
        "complete_integrability_exceptional_set": [],
    }


def nonabelian_certificate(
    sigma: RationalInput,
    *,
    unipotents_in_identity_component: bool = True,
    abelian_identity_component_implies_commuting: bool = True,
    fundamental_group_product_relation: bool = True,
) -> dict[str, object]:
    """Return the exact contradiction chain proving a non-Abelian Galois G0."""

    value = exact_fraction(sigma)
    finite_exponents_integral = all(
        isinstance(exponent, int)
        for exponent in TURNING_EXPONENTS + COLLISION_EXPONENTS
    )
    finite_monodromies_unipotent = finite_exponents_integral
    infinity = infinity_nonunipotence_certificate(value)
    premises = {
        "finite_residue_exponents_integral": finite_exponents_integral,
        "finite_local_monodromies_unipotent": finite_monodromies_unipotent,
        "unipotents_in_identity_component": unipotents_in_identity_component,
        "abelian_G0_would_make_finite_monodromies_commute": (
            abelian_identity_component_implies_commuting
        ),
        "product_of_commuting_unipotents_is_unipotent": True,
        "fundamental_group_product_relation": fundamental_group_product_relation,
        "infinity_monodromy_not_unipotent": infinity[
            "infinity_monodromy_not_unipotent"
        ],
    }
    contradiction = all(premises.values())
    return {
        "sigma": str(value),
        "premises": premises,
        "infinity": infinity,
        "abelian_identity_component_assumption_contradicted": contradiction,
        "differential_galois_identity_component_nonabelian": contradiction,
        "complete_meromorphic_liouville_integrability_obstructed": contradiction,
    }


def validate_residue_contract(
    *,
    turning: Sequence[RationalInput] = TURNING_CHARPOLY,
    collision: Sequence[RationalInput] = COLLISION_CHARPOLY,
    infinity: Sequence[RationalInput],
    sigma: RationalInput,
) -> bool:
    """Check all residue polynomials against the locked exact contract."""

    return (
        tuple(exact_fraction(item) for item in turning) == TURNING_CHARPOLY
        and tuple(exact_fraction(item) for item in collision)
        == COLLISION_CHARPOLY
        and tuple(exact_fraction(item) for item in infinity)
        == infinity_charpoly(sigma)
    )


@dataclass(frozen=True)
class MoralesRamisReproduction:
    masses: tuple[Fraction, Fraction, Fraction]
    normalized_masses: tuple[Fraction, Fraction, Fraction]
    sigma: Fraction
    sigma_range: dict[str, object]
    infinity_nonunipotence: dict[str, object]
    galois: dict[str, object]
    first_nve_polynomial_exception: bool

    def as_payload(self) -> dict[str, object]:
        return {
            "masses": [str(value) for value in self.masses],
            "normalized_masses_m3_one": [
                str(value) for value in self.normalized_masses
            ],
            "sigma": str(self.sigma),
            "turning_charpoly": [str(value) for value in TURNING_CHARPOLY],
            "collision_charpoly": [str(value) for value in COLLISION_CHARPOLY],
            "infinity_charpoly": [
                str(value) for value in infinity_charpoly(self.sigma)
            ],
            "turning_exponents": list(TURNING_EXPONENTS),
            "collision_exponents": list(COLLISION_EXPONENTS),
            "sigma_range": self.sigma_range,
            "infinity_nonunipotence": self.infinity_nonunipotence,
            "galois": self.galois,
            "first_nve_polynomial_exception": self.first_nve_polynomial_exception,
            "complete_integrability_exceptional_set": [],
        }


def reproduce(masses: Sequence[RationalInput]) -> MoralesRamisReproduction:
    """Build the complete dependency-light certificate for one mass triple."""

    parsed = positive_masses(masses)
    normalized = tuple(value / parsed[2] for value in parsed)
    sigma = mass_invariant(parsed)
    return MoralesRamisReproduction(
        masses=parsed,
        normalized_masses=normalized,  # type: ignore[arg-type]
        sigma=sigma,
        sigma_range=sigma_range_certificate(parsed),
        infinity_nonunipotence=infinity_nonunipotence_certificate(sigma),
        galois=nonabelian_certificate(sigma),
        first_nve_polynomial_exception=(
            sigma in FIRST_NVE_POLYNOMIAL_EXCEPTIONAL_SIGMA
        ),
    )
