from __future__ import annotations

from fractions import Fraction
from itertools import permutations
from pathlib import Path
import sys

import pytest

from src.python.wp4_mr_v2 import (
    LINEAR_NVE_EXCEPTION,
    OBSTRUCTED,
    classify_masses,
    exact_fraction,
    exponent_polynomial,
    mass_invariant,
)


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402


def _reference():
    return campaign_module(
        VALIDATION / "wp4-mr-ni-v2/reference/sympy_reference.py",
        "_wp4_mr_v2_test_reference",
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1/4", Fraction(1, 4)),
        ("0.125", Fraction(1, 8)),
        (
            "0x1.f0a3d70a3d70ap-1",
            Fraction(*float.fromhex("0x1.f0a3d70a3d70ap-1").as_integer_ratio()),
        ),
        (0.1, Fraction(*float(0.1).as_integer_ratio())),
        (7, Fraction(7)),
    ],
)
def test_exact_fraction_preserves_input_value(
    value: object, expected: Fraction
) -> None:
    assert exact_fraction(value) == expected


@pytest.mark.parametrize("value", [True, "", float("inf"), "-0x1p+1024"])
def test_exact_fraction_rejects_invalid_values(value: object) -> None:
    with pytest.raises((TypeError, ValueError, OverflowError)):
        exact_fraction(value)


@pytest.mark.parametrize(
    ("masses", "sigma", "status"),
    [
        (("1", "2", "3"), Fraction(11, 36), OBSTRUCTED),
        (("1", "1", "1"), Fraction(1, 3), LINEAR_NVE_EXCEPTION),
        (("1", "1", "1/4"), Fraction(8, 27), LINEAR_NVE_EXCEPTION),
        (("1", "1", "5/2"), Fraction(8, 27), LINEAR_NVE_EXCEPTION),
        (("1", "2", "15/2"), Fraction(2, 9), LINEAR_NVE_EXCEPTION),
        (
            ("1", "1", "2500001/1000000"),
            Fraction(6000002000000, 20250009000001),
            OBSTRUCTED,
        ),
    ],
)
def test_locked_exact_benchmarks(
    masses: tuple[str, str, str], sigma: Fraction, status: str
) -> None:
    result = classify_masses(masses)
    assert result.sigma == sigma
    assert result.single_additional_status == status
    assert result.universal_complete_meromorphic_integrability_obstructed is True


def test_mass_invariant_has_exact_permutation_and_scale_symmetry() -> None:
    masses = (Fraction(7, 5), Fraction(11, 13), Fraction(17, 19))
    expected = mass_invariant(masses)
    for permutation in permutations(masses):
        assert mass_invariant(permutation) == expected
        assert (
            mass_invariant(tuple(Fraction(23, 29) * value for value in permutation))
            == expected
        )


def test_exponent_polynomial_matches_declared_nested_radical_equation() -> None:
    sigma = Fraction(11, 36)
    coefficients = exponent_polynomial(sigma)
    assert coefficients == (
        Fraction(16),
        Fraction(-96),
        Fraction(112),
        Fraction(96),
        Fraction(4),
    )


def test_source_disjoint_sympy_reference_agrees_exactly() -> None:
    reference = _reference()
    source = (VALIDATION / "wp4-mr-ni-v2/reference/sympy_reference.py").read_text()
    assert "src.python.wp4_mr_v2" not in source
    cases = (
        ("1", "2", "3"),
        ("1", "1", "1"),
        ("1", "1", "1/4"),
        ("1", "2", "15/2"),
        ("0x1.f0a3d70a3d70ap-1", "1.03", "1"),
    )
    for masses in cases:
        assert classify_masses(masses).as_payload() == reference.classify_masses(masses)


@pytest.mark.parametrize("masses", [(0, 1, 1), (-1, 1, 1), (1, 2)])
def test_classification_requires_three_positive_masses(
    masses: tuple[object, ...],
) -> None:
    with pytest.raises(ValueError):
        classify_masses(masses)
