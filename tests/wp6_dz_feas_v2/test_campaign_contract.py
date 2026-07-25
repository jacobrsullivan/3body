from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-dz-feas-v2"
LOCK_PATH = CAMPAIGN / "reports/wp6_dz_feas_v2_specification_lock.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_specification_lock_is_valid_and_preimplementation() -> None:
    lock = _json(LOCK_PATH)
    unsigned = dict(lock)
    signature = unsigned.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert lock["campaign"] == "WP6-DZ-FEAS-v2"
    assert lock["lock_type"] == "pre_constructive_search_specification"
    assert lock["spec_sha256"] == _sha256(CAMPAIGN / "qualification_spec.json")
    assert lock["protocol_sha256"] == _sha256(CAMPAIGN / "constructive_protocol.json")
    for field in (
        "constructive_search_started_at_lock",
        "search_implementation_present_at_lock",
        "search_ledger_present_at_lock",
        "candidate_ledger_present_at_lock",
        "qualification_outputs_present_at_lock",
        "wp6_dz_mr_campaign_present_at_lock",
    ):
        assert lock[field] is False


def test_locked_counts_recompute_to_exact_search_size() -> None:
    protocol = _json(CAMPAIGN / "constructive_protocol.json")
    spec = _json(CAMPAIGN / "qualification_spec.json")
    counts = _json(LOCK_PATH)["locked_counts"]
    supports = 5 + 10
    expected = (
        len(protocol["shape_covers"]) * supports**2 * len(protocol["mass_order_cases"])
    )
    assert supports == counts["supports_per_variable"] == 15
    assert expected == counts["coefficient_ideals"] == 11700
    assert expected == spec["stop_rule"]["coefficient_ideal_count"]
    assert len(spec["witness_requirements"]) == 12


def test_null_claim_and_mr_gate_remain_bounded() -> None:
    spec = _json(CAMPAIGN / "qualification_spec.json")
    policy = spec["decision_policy"]
    assert "four locked shape covers" in policy["AUTHORIZED_NULL_CLAIM"]
    assert "No explicit" in policy["PROHIBITED_NONEXISTENCE_CLAIM"]
    assert "QUALIFIED_WITNESS" in policy["MR_PROMOTION_RULE"]
    assert "Every other status prohibits promotion" in policy["MR_PROMOTION_RULE"]
    assert not (ROOT / "validation-external/wp6-dz-mr-v1").exists()
    assert not (ROOT / "src/python/wp6_dz_mr_v1").exists()
    assert not (ROOT / "tests/wp6_dz_mr_v1").exists()


def test_final_search_ledger_is_complete_when_present() -> None:
    ledger_path = CAMPAIGN / "search/search_ledger.json"
    if not ledger_path.exists():
        pytest.skip("constructive search has not executed")
    ledger = _json(ledger_path)
    unsigned = dict(ledger)
    signature = unsigned.pop("search_payload_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert ledger["search_status"] == "COMPLETE"
    assert ledger["expected_system_count"] == 11700
    assert ledger["executed_system_count"] == 11700
    assert ledger["status_counts"]["TIMEOUT"] == 0
    assert ledger["status_counts"]["ERROR"] == 0
    assert all(ledger["reference_checks"].values())
