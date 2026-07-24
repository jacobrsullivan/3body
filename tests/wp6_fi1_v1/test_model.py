from __future__ import annotations

from fractions import Fraction
import importlib.util
from itertools import permutations
from pathlib import Path

import pytest

from src.python.wp6_fi1_v1 import (
    LEGACY_FIRST_NVE_EXCEPTIONAL_Q,
    mass_domain_certificate,
    mass_invariant,
    one_integral_certificate,
    real_witness_nonclassical_polynomial,
    second_witness_a_squared,
    universal_branch_certificate,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "validation-external/wp6-fi1-v1/reference/sympy_hessian.py"


def _reference():
    spec = importlib.util.spec_from_file_location("wp6_fi1_reference", REFERENCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("masses", "q_value", "legacy"),
    [
        (("1", "1", "1"), Fraction(1, 3), True),
        (("1", "1", "1/4"), Fraction(8, 27), True),
        (("2", "4", "15"), Fraction(2, 9), True),
        (("2", "3", "1"), Fraction(11, 36), False),
    ],
)
def test_exact_mass_branches_all_obstruct_one_additional_integral(
    masses: tuple[str, str, str],
    q_value: Fraction,
    legacy: bool,
) -> None:
    certificate = one_integral_certificate(masses)
    assert certificate.q_value == q_value
    assert certificate.legacy_first_nve_exception is legacy
    assert certificate.theorem_obstruction is True
    payload = certificate.as_payload()
    assert payload[
        "meromorphic_first_integral_independent_of_classical_integrals_obstructed"
    ]
    assert payload["fixed_reduced_leaf_transfer_claimed"] is False


def test_q_domain_permutation_scale_and_equality_case() -> None:
    masses = (Fraction(7, 5), Fraction(11, 13), Fraction(17, 19))
    expected = mass_invariant(masses)
    for ordered in permutations(masses):
        assert mass_invariant(ordered) == expected
        assert mass_invariant(tuple(Fraction(23, 29) * x for x in ordered)) == expected
    equal = mass_domain_certificate((3, 3, 3))
    assert equal["Q"] == "1/3"
    assert equal["squared_difference_identity"]
    assert equal["equality_exactly_equal_masses"]


def test_real_witness_polynomial_matches_locked_formula() -> None:
    assert real_witness_nonclassical_polynomial((1, 1, 1)) == (
        Fraction(1),
        Fraction(1),
        Fraction(1, 4),
    )
    assert real_witness_nonclassical_polynomial((1, 1, Fraction(1, 4))) == (
        Fraction(1),
        Fraction(1),
        Fraction(0),
    )


def test_complex_witness_closes_both_real_witness_candidates() -> None:
    equal = one_integral_certificate((1, 1, 1))
    assert equal.selected_witness == "complex_lagrange"
    assert equal.selected_witness_checks["a_squared_nonreal"]
    assert equal.selected_witness_checks["table_membership_rejected"]
    assert equal.selected_witness_checks["pair_equivalence_rejected"]

    eight = one_integral_certificate((1, 1, Fraction(1, 4)))
    assert eight.selected_witness == "complex_lagrange"
    assert second_witness_a_squared(eight.masses) == (
        Fraction(-1, 27),
        Fraction(0),
    )
    assert eight.selected_witness_checks[
        "forced_a_squared_minus_one_over_27"
    ]
    assert eight.selected_witness_checks["table_membership_rejected"]
    assert eight.selected_witness_checks["pair_equivalence_rejected"]


def test_legacy_exception_set_is_not_the_final_theorem_exception_set() -> None:
    assert LEGACY_FIRST_NVE_EXCEPTIONAL_Q == (
        Fraction(1, 3),
        Fraction(8, 27),
        Fraction(2, 9),
    )
    for masses in ((1, 1, 1), (1, 1, Fraction(1, 4)), (2, 4, 15)):
        result = one_integral_certificate(masses)
        assert result.legacy_first_nve_exception
        assert result.theorem_obstruction


@pytest.mark.parametrize(
    "masses",
    [("1", "1", "1"), ("1", "1", "1/4"), ("2", "3", "1")],
)
def test_source_disjoint_exact_hessian_reproduction(
    masses: tuple[str, str, str],
) -> None:
    assert "src.python" not in REFERENCE.read_text(encoding="utf-8")
    result = _reference().hessian_charpoly(masses)
    assert result["Q"] == str(mass_invariant(masses))
    assert result["center_of_mass_zero"]
    assert result["exact_match"]


def test_source_disjoint_symbolic_branch_identities() -> None:
    assert all(_reference().branch_identities().values())
    universal = universal_branch_certificate()
    assert universal["all_positive_mass_branches_obstructed"]
    assert universal["Q_8_27_table_contradiction"]
    assert universal["fixed_reduced_leaf_transfer_claimed"] is False


@pytest.mark.parametrize(
    "masses",
    [(0, 1, 1), (-1, 1, 1), (1, 2), (1, 2, float("inf"))],
)
def test_invalid_mass_domain_is_rejected(masses: tuple[object, ...]) -> None:
    with pytest.raises((TypeError, ValueError)):
        one_integral_certificate(masses)
