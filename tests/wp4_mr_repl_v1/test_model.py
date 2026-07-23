from __future__ import annotations

from fractions import Fraction
from itertools import permutations

import pytest

from src.python.wp4_mr_repl_v1 import (
    COLLISION_CHARPOLY,
    TURNING_CHARPOLY,
    exact_fraction,
    infinity_charpoly,
    mass_invariant,
    nonabelian_certificate,
    reproduce,
    universal_nonabelian_domain_certificate,
    validate_residue_contract,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1/4", Fraction(1, 4)),
        ("0.125", Fraction(1, 8)),
        ("0x1.0000000000000p-3", Fraction(1, 8)),
        (0.1, Fraction(*float(0.1).as_integer_ratio())),
        (7, Fraction(7)),
    ],
)
def test_exact_fraction(value: object, expected: Fraction) -> None:
    assert exact_fraction(value) == expected


@pytest.mark.parametrize("value", [True, "", float("inf"), "-0x1p+1024"])
def test_invalid_exact_fraction(value: object) -> None:
    with pytest.raises((TypeError, ValueError, OverflowError)):
        exact_fraction(value)


@pytest.mark.parametrize(
    ("masses", "sigma"),
    [
        (("1", "1", "1"), Fraction(1, 3)),
        (("1/2", "3/4", "1"), Fraction(26, 81)),
        (("2", "3", "1"), Fraction(11, 36)),
        (("1", "1", "1/4"), Fraction(8, 27)),
    ],
)
def test_locked_mass_benchmarks(
    masses: tuple[str, str, str], sigma: Fraction
) -> None:
    result = reproduce(masses)
    assert result.sigma == sigma
    assert result.sigma_range["positive"] is True
    assert result.sigma_range["upper_bound"] is True
    assert result.sigma_range["sum_of_squares_identity"] is True
    assert result.infinity_nonunipotence["infinity_monodromy_not_unipotent"] is True
    assert result.galois["differential_galois_identity_component_nonabelian"] is True
    assert result.galois[
        "complete_meromorphic_liouville_integrability_obstructed"
    ] is True


def test_sigma_is_exactly_permutation_and_scale_invariant() -> None:
    masses = (Fraction(7, 5), Fraction(11, 13), Fraction(17, 19))
    expected = mass_invariant(masses)
    for ordered in permutations(masses):
        assert mass_invariant(ordered) == expected
        assert mass_invariant(tuple(Fraction(23, 29) * x for x in ordered)) == expected


def test_residue_contract_detects_all_locked_coefficient_changes() -> None:
    sigma = Fraction(11, 36)
    infinity = infinity_charpoly(sigma)
    assert validate_residue_contract(infinity=infinity, sigma=sigma)
    for name, original in (
        ("turning", TURNING_CHARPOLY),
        ("collision", COLLISION_CHARPOLY),
        ("infinity", infinity),
    ):
        for index in range(5):
            changed = list(original)
            changed[index] += 1
            arguments = {
                "turning": TURNING_CHARPOLY,
                "collision": COLLISION_CHARPOLY,
                "infinity": infinity,
                "sigma": sigma,
            }
            arguments[name] = changed
            assert validate_residue_contract(**arguments) is False


def test_group_argument_controls_are_required() -> None:
    sigma = Fraction(11, 36)
    assert nonabelian_certificate(sigma)[
        "differential_galois_identity_component_nonabelian"
    ]
    controls = (
        {"unipotents_in_identity_component": False},
        {"abelian_identity_component_implies_commuting": False},
        {"fundamental_group_product_relation": False},
    )
    for control in controls:
        result = nonabelian_certificate(sigma, **control)
        assert result["differential_galois_identity_component_nonabelian"] is False


@pytest.mark.parametrize("masses", [(0, 1, 1), (-1, 1, 1), (1, 2)])
def test_positive_mass_domain_is_enforced(masses: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        reproduce(masses)


def test_first_nve_exception_does_not_suspend_complete_obstruction() -> None:
    result = reproduce(("1", "1", "1/4"))
    assert result.first_nve_polynomial_exception is True
    assert result.galois[
        "complete_meromorphic_liouville_integrability_obstructed"
    ] is True
    assert result.as_payload()["complete_integrability_exceptional_set"] == []


def test_universal_domain_certificate_has_no_positive_mass_exception() -> None:
    certificate = universal_nonabelian_domain_certificate()
    assert certificate[
        "all_positive_mass_triples_have_nonabelian_identity_component"
    ] is True
    assert certificate["odd_square_decompositions"] == [["1", "25"]]
    assert certificate["forced_sigma"] == "0"
    assert certificate["complete_integrability_exceptional_set"] == []
