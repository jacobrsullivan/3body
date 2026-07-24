from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path

import pytest

from src.python.wp6_common_level_v1 import (
    CIRCULAR_RELATION_COMPLEX_WITNESS,
    NONCIRCULAR_NONZERO_MOMENTUM,
    UNQUALIFIED_DOUBLE_ZERO,
    ZERO_MOMENTUM_NONZERO_ENERGY,
    circular_discriminant_certificate,
    circular_discriminant_squared,
    classify_common_level,
    equal_mass_euler_certificate,
    equal_mass_euler_matrix,
    generic_discriminant_certificate,
    generic_discriminant_squared,
    generic_nve_coefficients,
    kepler_relation_certificate,
    universal_common_level_certificate,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "validation-external/wp6-common-level-v1/reference/euler_conic.py"


def _reference():
    spec = importlib.util.spec_from_file_location(
        "wp6_common_level_reference", REFERENCE
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("energy", "momentum", "expected_branch", "expected_e_squared"),
    [
        ("-3/2", "0", ZERO_MOMENTUM_NONZERO_ENERGY, "1"),
        ("0", "1", NONCIRCULAR_NONZERO_MOMENTUM, "1"),
        ("-3/8", "1", NONCIRCULAR_NONZERO_MOMENTUM, "1/4"),
        ("-1/2", "1", CIRCULAR_RELATION_COMPLEX_WITNESS, "0"),
        ("0", "0", UNQUALIFIED_DOUBLE_ZERO, "1"),
        ("-2", "1", NONCIRCULAR_NONZERO_MOMENTUM, "-3"),
    ],
)
def test_exact_common_level_partition(
    energy: str,
    momentum: str,
    expected_branch: str,
    expected_e_squared: str,
) -> None:
    result = classify_common_level(energy, momentum)
    assert result.branch == expected_branch
    assert str(result.eccentricity_squared) == expected_e_squared
    assert result.qualified is (expected_branch != UNQUALIFIED_DOUBLE_ZERO)
    assert (
        result.as_payload()["restricted_rational_complete_integrability_obstructed"]
        is result.qualified
    )


def test_partition_is_exhaustive_and_pairwise_exclusive_on_exact_grid() -> None:
    branches = {
        ZERO_MOMENTUM_NONZERO_ENERGY,
        NONCIRCULAR_NONZERO_MOMENTUM,
        CIRCULAR_RELATION_COMPLEX_WITNESS,
        UNQUALIFIED_DOUBLE_ZERO,
    }
    for numerator_h in range(-8, 9):
        for numerator_c in range(-8, 9):
            result = classify_common_level(
                Fraction(numerator_h, 4), Fraction(numerator_c, 4)
            )
            assert result.branch in branches
            if numerator_h == 0 and numerator_c == 0:
                assert result.branch == UNQUALIFIED_DOUBLE_ZERO
            else:
                assert result.qualified


def test_circular_relation_requires_complex_witness() -> None:
    result = classify_common_level("-1/2", 1)
    assert result.branch == CIRCULAR_RELATION_COMPLEX_WITNESS
    assert result.witness == "EULER_MOULTON_COMPLEX_HOMOGRAPHIC"
    assert result.real_circular_orbit_is_obstruction_witness is False
    assert "LEMMA_5_3" in result.reason


def test_zero_momentum_branch_requires_qualified_predecessor() -> None:
    result = classify_common_level(7, 0)
    assert result.branch == ZERO_MOMENTUM_NONZERO_ENERGY
    assert result.requires_wp6_l0_predecessor


@pytest.mark.parametrize(
    ("energy", "momentum", "mu", "eccentricity_squared"),
    [
        ("0", "1", "1", "1"),
        ("-3/8", "1", "1", "1/4"),
        ("-1/2", "1", "1", "0"),
        ("7/5", "-2/3", "11/7", "8189/5445"),
    ],
)
def test_kepler_relation_is_exact(
    energy: str,
    momentum: str,
    mu: str,
    eccentricity_squared: str,
) -> None:
    result = kepler_relation_certificate(energy, momentum, mu, eccentricity_squared)
    assert result["relation_holds"]
    assert result["derived_eccentricity_squared"] == eccentricity_squared


def test_incorrect_kepler_relation_is_detected() -> None:
    result = kepler_relation_certificate("-3/8", 1, 1, "1/3")
    assert result["relation_holds"] is False


def test_equal_mass_euler_spectrum_is_verified_by_exact_eigenvectors() -> None:
    result = equal_mass_euler_certificate()
    assert result["central_multiplier_mu"] == "5/4"
    assert result["spectrum"] == ["0", "1", "12/5"]
    assert result["physical_delta"] == "7/5"
    assert result["exact_spectrum_verified"]
    matrix = equal_mass_euler_matrix()
    assert all(sum(row) == 0 for row in matrix)


def test_discriminant_benchmarks_and_strict_positivity() -> None:
    generic = generic_discriminant_certificate("7/5", 1)
    assert generic["Delta_squared"] == "1406596/625"
    assert generic["all_terms_strictly_positive"]
    assert generic["strictly_positive"]
    assert generic_discriminant_squared("7/5", 1) == Fraction(1186, 25) ** 2

    circular = circular_discriminant_certificate("7/5")
    assert circular["Delta_squared"] == "816/25"
    assert circular["strictly_positive"]
    assert circular["real_circular_orbit_is_obstruction_witness"] is False
    assert circular_discriminant_squared("7/5") == Fraction(816, 25)


def test_generic_nve_coefficients_match_source_disjoint_reference() -> None:
    assert "src.python" not in REFERENCE.read_text(encoding="utf-8")
    production = generic_nve_coefficients("7/5", 1, "1186/25", 3)
    reference = _reference().generic_nve_coefficients("7/5", "1", "1186/25", "3")
    assert production == reference


def test_source_disjoint_reference_derives_relation_and_euler_spectrum() -> None:
    reference = _reference()
    relation = reference.derive_kepler_relation()
    assert relation["relation_verified"]
    assert relation["residual"] == "0"
    euler = reference.exact_equal_mass_euler_spectrum()
    assert euler["central_multiplier_mu"] == "5/4"
    assert euler["spectrum"] == ["0", "1", "12/5"]
    assert euler["physical_delta"] == "7/5"


def test_reference_branch_classification_agrees_on_locked_benchmarks() -> None:
    reference = _reference()
    for energy, momentum in (
        ("-3/2", "0"),
        ("0", "1"),
        ("-3/8", "1"),
        ("-1/2", "1"),
        ("0", "0"),
    ):
        production = classify_common_level(energy, momentum)
        independent = reference.classify_relation(energy, momentum)
        assert independent["branch"] == production.branch
        assert independent["qualified"] is production.qualified
        assert independent["eccentricity_squared"] == str(
            production.eccentricity_squared
        )


def test_universal_certificate_preserves_theorem_quantifiers() -> None:
    result = universal_common_level_certificate()
    assert result["branch_conditions_pairwise_disjoint"]
    assert result["all_non_double_zero_levels_covered"]
    assert result["direct_common_level_theorem_not_fi1_transfer"]
    assert result["double_zero_qualified"] is False
    assert result["one_additional_integral_excluded"] is False
    assert result["spatial_claim"] is False
    assert result["pointwise_every_open_domain_claim"] is False
    assert result["collinear_witness_in_regular_noncollinear_so3_chart"] is False


@pytest.mark.parametrize(
    "arguments",
    [
        (True, 0),
        ("", 0),
        (float("inf"), 0),
        (0, float("nan")),
        (1, 1, 0),
        (1, 1, -1),
    ],
)
def test_invalid_common_level_inputs_are_rejected(
    arguments: tuple[object, ...],
) -> None:
    with pytest.raises((TypeError, ValueError, OverflowError)):
        classify_common_level(*arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("function", "arguments"),
    [
        (generic_discriminant_squared, (0, 1)),
        (generic_discriminant_squared, (1, 0)),
        (circular_discriminant_squared, (0,)),
        (generic_nve_coefficients, ("7/5", 1, "1", 3)),
        (generic_nve_coefficients, ("7/5", 1, "1186/25", 2)),
    ],
)
def test_spectral_premises_and_poles_are_rejected(
    function: object,
    arguments: tuple[object, ...],
) -> None:
    with pytest.raises(ValueError):
        function(*arguments)  # type: ignore[operator]
