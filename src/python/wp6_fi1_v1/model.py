"""Exact mass-branch reproduction for the WP6-FI1-v1 theorem track."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Sequence, TypeAlias


RationalInput: TypeAlias = Fraction | int | float | str
LEGACY_FIRST_NVE_EXCEPTIONAL_Q = (
    Fraction(1, 3),
    Fraction(8, 27),
    Fraction(2, 9),
)


def exact_fraction(value: RationalInput) -> Fraction:
    """Parse accepted rational representations without tolerance."""

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
    """Return the symmetric normalized mass invariant Q."""

    m1, m2, m3 = _positive_masses(masses)
    total = m1 + m2 + m3
    return (m1 * m2 + m2 * m3 + m3 * m1) / total**2


def mass_domain_certificate(
    masses: Sequence[RationalInput],
) -> dict[str, object]:
    """Prove 0<Q<=1/3 by the exact squared-difference identity."""

    m1, m2, m3 = _positive_masses(masses)
    total = m1 + m2 + m3
    q_value = mass_invariant((m1, m2, m3))
    square_sum = (m1 - m2) ** 2 + (m2 - m3) ** 2 + (m3 - m1) ** 2
    gap = Fraction(1, 3) - q_value
    return {
        "Q": str(q_value),
        "positive": q_value > 0,
        "at_most_one_third": q_value <= Fraction(1, 3),
        "gap": str(gap),
        "squared_difference_identity": (
            gap == square_sum / (6 * total**2)
        ),
        "equality_exactly_equal_masses": (
            (gap == 0) == (m1 == m2 == m3)
        ),
    }


def real_witness_nonclassical_polynomial(
    masses: Sequence[RationalInput],
) -> tuple[Fraction, Fraction, Fraction]:
    """Return the monic quadratic for the two nonclassical Hessian roots."""

    q_value = mass_invariant(masses)
    return (Fraction(1), Fraction(1), (27 * q_value - 8) / 4)


def second_witness_a_squared(
    masses: Sequence[RationalInput],
) -> tuple[Fraction, Fraction]:
    """Return ``a_*^2`` as ``real + i*sqrt(3)*imaginary_coefficient``."""

    m1, m2, m3 = _positive_masses(masses)
    total = m1 + m2 + m3
    real_numerator = (
        2 * m1**2
        + 2 * m2**2
        + 2 * m3**2
        - 5 * m1 * m2
        - 5 * m2 * m3
        + 7 * m1 * m3
    )
    imaginary_base = m1 * m2 + m2 * m3 - 5 * m1 * m3
    denominator = 2 * total**2
    return real_numerator / denominator, -imaginary_base / denominator


def _real_witness_candidates(q_value: Fraction) -> dict[str, bool]:
    return {
        "table_membership_candidate": q_value == Fraction(8, 27),
        "pair_equivalence_candidate": q_value == Fraction(1, 3),
    }


def _complex_witness_rejects(
    masses: tuple[Fraction, Fraction, Fraction],
    q_value: Fraction,
) -> dict[str, object]:
    m1, m2, m3 = masses
    total = m1 + m2 + m3
    a_real, a_imaginary = second_witness_a_squared(masses)
    result: dict[str, object] = {
        "a_squared_real": str(a_real),
        "a_squared_i_sqrt3_coefficient": str(a_imaginary),
        "a_squared_nonreal": a_imaginary != 0,
    }
    if q_value == Fraction(1, 3):
        equal_masses = m1 == m2 == m3
        result.update(
            {
                "branch": "Q=1/3",
                "equal_masses_forced": equal_masses,
                "table_membership_rejected": equal_masses and a_imaginary != 0,
                "pair_equivalence_rejected": equal_masses and a_imaginary != 0,
            }
        )
        return result

    if q_value != Fraction(8, 27):
        raise ValueError("complex witness is only selected for locked candidates")

    if a_imaginary != 0:
        result.update(
            {
                "branch": "Q=8/27, nonreal a_squared",
                "table_membership_rejected": True,
                "pair_equivalence_rejected": True,
            }
        )
        return result

    scale_condition = total**2 == Fraction(189, 8) * m1 * m3
    pair_identity = a_real == Fraction(-1, 27)
    integer_relation_impossible = (
        pair_identity
        and Fraction(36) * a_real == Fraction(-4, 3)
    )
    result.update(
        {
            "branch": "Q=8/27, real a_squared",
            "imaginary_vanishing_condition": (
                m1 * m2 + m2 * m3 == 5 * m1 * m3
            ),
            "table_scale_condition": scale_condition,
            "table_membership_rejected": not scale_condition,
            "forced_a_squared_minus_one_over_27": pair_identity,
            "integer_pair_relation_left_side": str(Fraction(36) * a_real),
            "integer_pair_relation_right_side_is_integer": True,
            "pair_equivalence_rejected": integer_relation_impossible,
        }
    )
    return result


@dataclass(frozen=True)
class OneIntegralCertificate:
    masses: tuple[Fraction, Fraction, Fraction]
    q_value: Fraction
    selected_witness: str
    real_witness: dict[str, bool]
    selected_witness_checks: dict[str, object]
    legacy_first_nve_exception: bool
    theorem_obstruction: bool

    def as_payload(self) -> dict[str, object]:
        return {
            "masses": [str(value) for value in self.masses],
            "Q": str(self.q_value),
            "selected_witness": self.selected_witness,
            "real_witness": self.real_witness,
            "selected_witness_checks": self.selected_witness_checks,
            "legacy_first_nve_exception": self.legacy_first_nve_exception,
            "legacy_first_nve_exceptional_set": [
                str(value) for value in LEGACY_FIRST_NVE_EXCEPTIONAL_Q
            ],
            "meromorphic_first_integral_independent_of_classical_integrals_obstructed": (
                self.theorem_obstruction
            ),
            "fixed_reduced_leaf_transfer_claimed": False,
            "nonmeromorphic_integrals_excluded": False,
        }


def one_integral_certificate(
    masses: Sequence[RationalInput],
) -> OneIntegralCertificate:
    """Select a witness and certify the pinned theorem's exact mass branch."""

    parsed = _positive_masses(masses)
    q_value = mass_invariant(parsed)
    real = _real_witness_candidates(q_value)
    if not any(real.values()):
        selected = "real_lagrange"
        checks: dict[str, object] = {
            "table_membership_rejected": True,
            "pair_equivalence_rejected": True,
        }
    else:
        selected = "complex_lagrange"
        checks = _complex_witness_rejects(parsed, q_value)
    obstruction = bool(
        checks["table_membership_rejected"]
        and checks["pair_equivalence_rejected"]
    )
    return OneIntegralCertificate(
        masses=parsed,
        q_value=q_value,
        selected_witness=selected,
        real_witness=real,
        selected_witness_checks=checks,
        legacy_first_nve_exception=q_value in LEGACY_FIRST_NVE_EXCEPTIONAL_Q,
        theorem_obstruction=obstruction,
    )


def universal_branch_certificate() -> dict[str, object]:
    """Record the exact exhaustive branch logic for all positive masses."""

    return {
        "positive_mass_domain": "0<Q<=1/3",
        "real_witness_table_candidate_set": ["8/27"],
        "real_witness_pair_candidate_set": ["1/3"],
        "candidate_union": ["8/27", "1/3"],
        "Q_1_3_forces_equal_masses": True,
        "Q_1_3_complex_witness_a_squared_nonreal": True,
        "Q_8_27_complex_table_conditions_force_Q": "16/63",
        "Q_8_27_table_contradiction": Fraction(16, 63) != Fraction(8, 27),
        "Q_8_27_real_a_squared_subbranch": "-1/27",
        "Q_8_27_pair_relation_would_equate_noninteger_to_integer": "-4/3",
        "all_positive_mass_branches_obstructed": True,
        "arbitrary_dimension_extension_is_published_theorem_input": True,
        "fixed_reduced_leaf_transfer_claimed": False,
    }
