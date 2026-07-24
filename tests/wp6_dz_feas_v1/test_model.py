from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

import pytest

from src.python.wp6_dz_feas_v1 import (
    COMPLETE_BOUNDED_NULL_RESULT,
    corrected_euler_homothetic_certificate,
    evaluate_candidate_ledger,
    free_fall_energy_certificate,
    legacy_euler_fixture_certificate,
    newtonian_scaling_certificate,
    periodic_energy_certificate,
    sundman_triple_collision_certificate,
)


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-dz-feas-v1"


def test_legacy_fixture_is_exactly_negative_energy() -> None:
    certificate = legacy_euler_fixture_certificate()
    assert certificate["kinetic"] == "3/2"
    assert certificate["positive_potential"] == "5/2"
    assert certificate["energy"] == "-1"
    assert certificate["angular_momentum"] == "0"
    assert certificate["stated_zero_energy_is_false"]
    assert not certificate["qualifying_witness"]


def test_corrected_euler_curve_is_exact_but_disqualified() -> None:
    certificate = corrected_euler_homothetic_certificate()
    assert certificate["kappa_squared"] == "5/2"
    assert certificate["equations_hold"]
    assert certificate["energy"] == "0"
    assert certificate["angular_momentum"] == "0"
    assert certificate["gradients_H_C_generically_independent"]
    assert certificate["known_homothetic_curve"]
    assert not certificate["known_tangent_ve_obstruction"]
    assert certificate["failed_requirements"] == ["W3", "W9"]


def test_scaling_periodic_and_free_fall_controls() -> None:
    scaling = newtonian_scaling_certificate("-7/3", "11/5")
    assert scaling["scaled_energy"] == "-35/33"
    assert scaling["sign_preserved"]
    assert scaling["nonzero_energy_cannot_scale_to_zero"]

    periodic = periodic_energy_certificate("14/5")
    assert periodic["energy"] == "-7/5"
    assert periodic["nonstationary_collision_free_periodic_H_zero_impossible"]

    free_fall = free_fall_energy_certificate()
    assert free_fall["energy"] == "-5/2"
    assert free_fall["finite_collision_free_free_fall_H_zero_impossible"]


def test_recent_triple_collision_is_homothetic_negative_energy_control() -> None:
    certificate = sundman_triple_collision_certificate()
    assert certificate["delta_over_r_squared"] == "3/4"
    assert certificate["constant_shape"]
    assert certificate["homothetic"]
    assert certificate["energy_sign"] == "negative"
    assert not certificate["energy_zero"]
    assert not certificate["qualifying_witness"]


def test_exact_controls_reject_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        newtonian_scaling_certificate(1, 0)
    with pytest.raises(ValueError):
        periodic_energy_certificate(0)


def test_locked_ledger_derives_bounded_null() -> None:
    ledger = json.loads((CAMPAIGN / "candidate_ledger.json").read_text())
    decision = evaluate_candidate_ledger(
        ledger,
        search_complete=True,
        integrity_complete=True,
    )
    assert decision.outcome == COMPLETE_BOUNDED_NULL_RESULT
    assert decision.qualifying_candidate_ids == ()
    assert decision.candidate_count == 12
    assert decision.all_requirements_decided
    assert decision.all_candidates_have_failure
    assert not decision.mr_promotion_authorized


def test_one_all_pass_candidate_is_the_only_mr_promotion_shape() -> None:
    requirements = {
        f"W{index}": {"status": "PASS", "reason": "exact test witness"}
        for index in range(1, 13)
    }
    decision = evaluate_candidate_ledger(
        {
            "candidates": [
                {"candidate_id": "test-witness", "requirements": requirements}
            ]
        },
        search_complete=True,
        integrity_complete=True,
    )
    assert decision.qualifying_candidate_ids == ("test-witness",)
    assert decision.mr_promotion_authorized


def test_fraction_control_uses_exact_binary_float_conversion() -> None:
    result = newtonian_scaling_certificate(0.5, Fraction(3, 2))
    assert result["original_energy"] == "1/2"
    assert result["scaled_energy"] == "1/3"
