from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-dz-feas-v2"
LOCK_PATH = CAMPAIGN / "reports/wp6_dz_feas_v2_specification_lock.json"
QUALIFICATION_LOCK_PATH = (
    CAMPAIGN / "reports/wp6_dz_feas_v2_qualification_lock.json"
)


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


def test_final_search_ledger_is_integrity_checked_when_present() -> None:
    ledger_path = CAMPAIGN / "search/search_ledger.json"
    if not ledger_path.exists():
        pytest.skip("constructive search has not executed")
    ledger = _json(ledger_path)
    unsigned = dict(ledger)
    signature = unsigned.pop("search_payload_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert ledger["expected_system_count"] == 11700
    records = ledger["records"]
    assert ledger["executed_system_count"] == len(records)
    assert [record["system_id"] for record in records] == [
        f"S{index:05d}" for index in range(1, len(records) + 1)
    ]
    statuses = ("UNIT_IDEAL", "NON_UNIT_IDEAL", "TIMEOUT", "ERROR")
    recomputed = {
        status: sum(record["status"] == status for record in records)
        for status in statuses
    }
    assert ledger["status_counts"] == recomputed
    assert all(ledger["reference_checks"].values())
    complete = (
        len(records) == 11700
        and ledger["abort_reason"] is None
        and recomputed["TIMEOUT"] == 0
        and recomputed["ERROR"] == 0
    )
    assert ledger["search_status"] == ("COMPLETE" if complete else "INCOMPLETE")


def test_observed_v2_result_is_pinned_and_fail_closed() -> None:
    ledger_path = CAMPAIGN / "search/search_ledger.json"
    if not ledger_path.exists():
        pytest.skip("constructive search has not executed")
    ledger = _json(ledger_path)
    assert _sha256(ledger_path) == (
        "ebec58e4571e352f8d264be958025aa983621c4badcb4e4caae61a83cd7abac1"
    )
    assert ledger["search_status"] == "INCOMPLETE"
    assert ledger["executed_system_count"] == 11689
    assert ledger["status_counts"] == {
        "UNIT_IDEAL": 11549,
        "NON_UNIT_IDEAL": 0,
        "TIMEOUT": 140,
        "ERROR": 0,
    }
    assert ledger["abort_reason"] == "aggregate_compute_cap_exceeded"
    assert not (ROOT / "validation-external/wp6-dz-mr-v1").exists()


def test_qualification_record_is_signed_and_fail_closed_when_present() -> None:
    record_path = (
        CAMPAIGN / "reports/wp6_dz_feas_v2_qualification_record.json"
    )
    if not record_path.exists():
        pytest.skip("v2 qualification has not been sealed")
    lock = _json(QUALIFICATION_LOCK_PATH)
    unsigned_lock = dict(lock)
    lock_signature = unsigned_lock.pop("lock_sha256")
    assert hashlib.sha256(_canonical(unsigned_lock)).hexdigest() == lock_signature

    candidate_path = CAMPAIGN / "candidates/candidate_ledger.json"
    results_path = CAMPAIGN / "results/qualification_results.json"
    candidate = _json(candidate_path)
    unsigned_candidate = dict(candidate)
    candidate_signature = unsigned_candidate.pop("candidate_payload_sha256")
    assert (
        hashlib.sha256(_canonical(unsigned_candidate)).hexdigest()
        == candidate_signature
    )
    results = _json(results_path)
    unsigned_results = dict(results)
    results_signature = unsigned_results.pop("results_payload_sha256")
    assert (
        hashlib.sha256(_canonical(unsigned_results)).hexdigest()
        == results_signature
    )
    record = _json(record_path)
    unsigned_record = dict(record)
    record_signature = unsigned_record.pop("record_payload_sha256")
    assert (
        hashlib.sha256(_canonical(unsigned_record)).hexdigest()
        == record_signature
    )
    assert record["status"] == results["outcome"] == "INCOMPLETE"
    assert record["qualification_gate_status"] == "FAIL_CLOSED"
    assert candidate["unresolved_system_count"] == 151
    assert candidate["candidate_count"] == 0
    assert record["mr_promotion_authorized"] is False
    assert results["mr_promotion_authorized"] is False
    assert record["search_ledger_sha256"] == _sha256(
        CAMPAIGN / "search/search_ledger.json"
    )
    assert record["candidate_ledger_sha256"] == _sha256(candidate_path)
    assert record["results_sha256"] == _sha256(results_path)
