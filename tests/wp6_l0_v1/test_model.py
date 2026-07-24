from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path

import pytest

from src.python.wp6_l0_v1 import (
    allowed_eigenvalue,
    common_level_certificate,
    spectral_obstruction,
    universal_zero_momentum_certificate,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "validation-external/wp6-l0-v1/reference/equal_mass_euler.py"


def _reference():
    spec = importlib.util.spec_from_file_location("wp6_l0_reference", REFERENCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_allowed_spectrum_has_exact_minus_one_lower_bound() -> None:
    values = [allowed_eigenvalue(index) for index in range(100)]
    assert values[:6] == [
        Fraction(-1),
        Fraction(0),
        Fraction(2),
        Fraction(5),
        Fraction(9),
        Fraction(14),
    ]
    assert min(values) == -1
    assert all(value >= -1 for value in values)


@pytest.mark.parametrize(
    ("longitudinal", "transverse"),
    [
        ("24/5", Fraction(-12, 5)),
        ("2000001/1000000", Fraction(-2000001, 2000000)),
        (3, Fraction(-3, 2)),
    ],
)
def test_pacella_strict_bound_gives_sl2_obstruction(
    longitudinal: object,
    transverse: Fraction,
) -> None:
    result = spectral_obstruction(longitudinal)
    assert result.transverse_eigenvalue == transverse
    assert result.pacella_premise
    assert result.below_allowed_spectrum
    assert result.galois_group_sl2


def test_lambda_two_is_a_required_strict_boundary_control() -> None:
    result = spectral_obstruction(2)
    assert result.transverse_eigenvalue == -1
    assert result.pacella_premise is False
    assert result.below_allowed_spectrum is False
    assert result.galois_group_sl2 is False


@pytest.mark.parametrize("energy", ["-3/2", "1/7", 9])
def test_every_nonzero_energy_zero_momentum_level_is_qualified(
    energy: object,
) -> None:
    result = common_level_certificate(energy)
    assert result.restricted_integrability_obstructed
    payload = result.as_payload()
    assert payload["necessary_galois_condition"] == "solvable identity component"
    assert payload["one_additional_integral_excluded"] is False
    assert payload["spatial_claim"] is False


def test_double_zero_and_cross_track_inputs_are_not_qualified() -> None:
    double_zero = common_level_certificate(0)
    assert not double_zero.restricted_integrability_obstructed
    assert double_zero.reason.startswith("UNQUALIFIED_DOUBLE_ZERO")
    assert not common_level_certificate(1, angular_momentum=1).restricted_integrability_obstructed
    assert not common_level_certificate(1, planar=False).restricted_integrability_obstructed
    assert not common_level_certificate(1, positive_masses=False).restricted_integrability_obstructed
    assert not common_level_certificate(
        1, pacella_spectrum_available=False
    ).restricted_integrability_obstructed


def test_source_disjoint_equal_mass_euler_benchmark() -> None:
    assert "src.python" not in REFERENCE.read_text(encoding="utf-8")
    result = _reference().exact_euler_spectrum()
    assert result["longitudinal_spectrum"] == ["0", "2", "24/5"]
    assert result["transverse_spectrum"] == ["-12/5", "-1", "0"]
    assert result["central_direction_eigenvalue"]
    assert result["nonclassical_direction_eigenvalue"]
    production = spectral_obstruction(result["longitudinal_lambda"])
    assert str(production.transverse_eigenvalue) == result["transverse_lambda"]


def test_source_disjoint_allowed_spectrum_agrees_exactly() -> None:
    reference = _reference().allowed_spectrum(20)
    production = [str(allowed_eigenvalue(index)) for index in range(20)]
    assert production == reference


def test_universal_certificate_preserves_all_nonclaims() -> None:
    result = universal_zero_momentum_certificate()
    assert result["all_planar_positive_mass_h_nonzero_C_zero_levels_obstructed"]
    assert result["H_zero_C_zero_obstructed_by_this_witness"] is False
    assert result["one_additional_integral_excluded"] is False
    assert result["spatial_transfer_claimed"] is False


@pytest.mark.parametrize("value", [True, "", float("inf"), "-0x1p+1024"])
def test_malformed_energy_is_rejected(value: object) -> None:
    with pytest.raises((TypeError, ValueError, OverflowError)):
        common_level_certificate(value)


@pytest.mark.parametrize("index", [-1, 1.5, True])
def test_invalid_allowed_spectrum_index_is_rejected(index: object) -> None:
    with pytest.raises(ValueError):
        allowed_eigenvalue(index)  # type: ignore[arg-type]
