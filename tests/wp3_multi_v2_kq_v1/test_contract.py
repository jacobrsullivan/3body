from __future__ import annotations

from pathlib import Path

from validation_external_import import campaign_module


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-multi-candidate-v2-known-quotient"
COMMON = campaign_module(
    CAMPAIGN / "scripts/campaign_common.py",
    "_test_wp3_multi_v2_kq_common",
)
GATE = campaign_module(
    CAMPAIGN / "scripts/evaluate_publication_gate.py",
    "_test_wp3_multi_v2_kq_gate",
)


def test_specification_lock_and_prerequisites_verify() -> None:
    spec_path = CAMPAIGN / "search_spec.json"
    lock = COMMON.verify_specification_lock(spec_path)
    prerequisites = COMMON.verify_prerequisites(
        __import__("json").loads(spec_path.read_text())
    )
    assert lock["campaign"] == "WP3-MULTI-CAND-v2-KQ-v1"
    assert prerequisites["known_function_resolution_qualification_id"].startswith(
        "WP3-MULTI-CAND-v2-RES-v2-"
    )


def test_publication_reserve_is_still_sealed() -> None:
    reserve = COMMON.verify_publication_reserve(
        "9b2ba04206e891eb1de331d98bbd1a02b2db5170a3a70c739b791a18982302fd"
    )
    assert reserve["status"] == "SEALED_UNEXECUTED"
    assert reserve["source_rows_present"] is False


def test_gate_authorizes_only_bounded_null_interpretation() -> None:
    bounded = GATE.decide_publication_gate("COMPLETE_BOUNDED_NULL_RESULT")
    candidate = GATE.decide_publication_gate(
        "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION"
    )
    assert bounded["PUBLICATION_GATE"] == "PASS_BOUNDED_NULL_ONLY"
    assert bounded["INTERPRETATION_AUTHORIZATION"] == "BOUNDED_NULL_ONLY"
    assert candidate["INTERPRETATION_AUTHORIZATION"] == "PROHIBITED"
