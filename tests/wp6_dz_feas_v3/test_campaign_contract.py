from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-dz-feas-v3"
LOCK_PATH = CAMPAIGN / "reports/wp6_dz_feas_v3_specification_lock.json"
QUALIFICATION_LOCK_PATH = (
    CAMPAIGN / "reports/wp6_dz_feas_v3_qualification_lock.json"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_specification_lock_is_valid_and_preimplementation() -> None:
    lock = _json(LOCK_PATH)
    unsigned = dict(lock)
    signature = unsigned.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert signature == (
        "960fc53758af0c361f4cab58a49d2f3715f2c1ce81230cc34cba32ca2e45c1c0"
    )
    assert lock["campaign"] == "WP6-DZ-FEAS-v3"
    assert lock["lock_type"] == (
        "pre_implementation_constructive_search_specification"
    )
    assert lock["spec_sha256"] == _sha256(
        CAMPAIGN / "qualification_spec.json"
    )
    assert lock["protocol_sha256"] == _sha256(
        CAMPAIGN / "constructive_protocol.json"
    )
    for field in (
        "implementation_present_at_lock",
        "implementation_tests_present_at_lock",
        "constructive_search_started_at_lock",
        "search_ledger_present_at_lock",
        "candidate_ledger_present_at_lock",
        "qualification_outputs_present_at_lock",
        "wp6_dz_mr_campaign_present_at_lock",
    ):
        assert lock[field] is False


def test_v2_predecessor_is_hash_pinned_and_fail_closed() -> None:
    specification = _json(CAMPAIGN / "qualification_spec.json")
    predecessor = specification["predecessor"]
    for path_field, hash_field in (
        ("qualification_lock_file", "qualification_lock_file_sha256"),
        ("record_file", "record_file_sha256"),
        ("results_file", "results_file_sha256"),
        ("search_ledger_file", "search_ledger_file_sha256"),
    ):
        assert _sha256(ROOT / predecessor[path_field]) == predecessor[
            hash_field
        ]
    record = _json(ROOT / predecessor["record_file"])
    unsigned = dict(record)
    signature = unsigned.pop("record_payload_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert record["qualification_id"] == predecessor["qualification_id"]
    assert record["status"] == predecessor["required_status"] == "INCOMPLETE"
    assert record["search_summary"]["unresolved_system_count"] == 151


def test_locked_scope_and_resources_are_exact() -> None:
    specification = _json(CAMPAIGN / "qualification_spec.json")
    protocol = _json(CAMPAIGN / "constructive_protocol.json")
    stop = specification["stop_rule"]
    assert len(protocol["enumeration"]["shape_cover_ids"]) == 4
    assert len(protocol["enumeration"]["mass_order_cases"]) == 13
    assert stop["support_count_per_variable"] == 15
    assert (
        4 * 15**2 * 13
        == stop["coefficient_ideal_count"]
        == protocol["enumeration"]["total_systems"]
        == 11700
    )
    assert stop["v2_unresolved_acceptance_count"] == 151
    assert stop["per_system_timeout_seconds"] == 30
    assert stop["aggregate_compute_cap_seconds"] == 3600
    assert stop["required_algorithms"] == [
        "sympy-f5b-grevlex",
        "sympy-buchberger-grevlex",
    ]
    assert len(specification["witness_requirements"]) == 12


def test_claim_boundary_and_mr_gate_remain_fail_closed() -> None:
    specification = _json(CAMPAIGN / "qualification_spec.json")
    policy = specification["decision_policy"]
    assert "frozen v2 shape covers" in policy["AUTHORIZED_NULL_CLAIM"]
    assert "No explicit" in policy["PROHIBITED_NONEXISTENCE_CLAIM"]
    assert "QUALIFIED_WITNESS" in policy["MR_PROMOTION_RULE"]
    assert "Every other status prohibits promotion" in policy[
        "MR_PROMOTION_RULE"
    ]
    assert not (ROOT / "validation-external/wp6-dz-mr-v1").exists()
    assert not (ROOT / "src/python/wp6_dz_mr_v1").exists()
    assert not (ROOT / "tests/wp6_dz_mr_v1").exists()


def test_search_ledger_is_signed_and_complete_when_present() -> None:
    ledger_path = CAMPAIGN / "search/search_ledger.json"
    if not ledger_path.exists():
        pytest.skip("v3 constructive search has not executed")
    ledger = _json(ledger_path)
    unsigned = dict(ledger)
    signature = unsigned.pop("search_payload_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert ledger["search_status"] == "COMPLETE"
    assert ledger["expected_system_count"] == 11700
    assert ledger["executed_system_count"] == 11700
    assert ledger["status_counts"]["TIMEOUT"] == 0
    assert ledger["status_counts"]["ERROR"] == 0
    assert ledger["status_counts"]["DISAGREEMENT"] == 0
    assert len(ledger["v2_unresolved_decisions"]) == 151
    assert all(ledger["runtime_checks"].values())
    assert all(ledger["reference_checks"].values())


def test_candidate_audit_is_signed_and_empty_when_present() -> None:
    candidate_path = CAMPAIGN / "candidates/candidate_ledger.json"
    if not candidate_path.exists():
        pytest.skip("v3 candidate audit has not executed")
    candidate = _json(candidate_path)
    unsigned = dict(candidate)
    signature = unsigned.pop("candidate_payload_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert candidate["status"] == "SEARCH_AND_BRANCH_AUDIT_COMPLETE"
    assert candidate["candidate_count"] == 0
    assert candidate["non_unit_system_ids"] == []
    assert candidate["qualifying_candidate_ids"] == []
    assert candidate["branch_audit_status"] == (
        "VACUOUS_NO_NON_UNIT_IDEALS"
    )
    assert candidate["stage_counts"] == {
        "ENERGY": 11687,
        "ENERGY_AND_V": 13,
        "FULL": 0,
    }
    assert candidate["v2_unresolved_count"] == 151
    assert candidate["proposed_outcome"] == "COMPLETE_BOUNDED_NULL_RESULT"
    assert candidate["mr_promotion_authorized"] is False


def test_qualification_record_is_signed_and_bounded_when_present() -> None:
    record_path = (
        CAMPAIGN / "reports/wp6_dz_feas_v3_qualification_record.json"
    )
    if not record_path.exists():
        pytest.skip("v3 qualification has not been sealed")
    lock = _json(QUALIFICATION_LOCK_PATH)
    unsigned_lock = dict(lock)
    lock_signature = unsigned_lock.pop("lock_sha256")
    assert hashlib.sha256(_canonical(unsigned_lock)).hexdigest() == lock_signature

    results_path = CAMPAIGN / "results/qualification_results.json"
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
    assert record["status"] == results["outcome"] == (
        "COMPLETE_BOUNDED_NULL_RESULT"
    )
    assert record["qualification_gate_status"] == "PASS"
    assert record["candidate_count"] == 0
    assert record["mr_promotion_authorized"] is False
    assert results["mr_promotion_authorized"] is False
    assert all(gate["passed"] for gate in results["gates"])
    assert record["search_ledger_sha256"] == _sha256(
        CAMPAIGN / "search/search_ledger.json"
    )
    assert record["candidate_ledger_sha256"] == _sha256(
        CAMPAIGN / "candidates/candidate_ledger.json"
    )
    assert record["results_sha256"] == _sha256(results_path)
