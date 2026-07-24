"""Fail-closed evidence checks for WP6-DZ-FEAS-v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-dz-feas-v1"
REPORTS = CAMPAIGN / "reports"
EXPECTED_OUTCOME = "COMPLETE_BOUNDED_NULL_RESULT"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_specification_was_locked_before_discovery() -> None:
    lock = _json(REPORTS / "wp6_dz_feas_v1_specification_lock.json")
    unsigned = dict(lock)
    signature = unsigned.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert lock["campaign"] == "WP6-DZ-FEAS-v1"
    assert lock["lock_type"] == "pre_discovery_feasibility_specification"
    assert lock["spec_sha256"] == _sha256(CAMPAIGN / "qualification_spec.json")
    assert lock["protocol_sha256"] == _sha256(CAMPAIGN / "discovery_protocol.json")
    assert lock["seed_manifest_sha256"] == _sha256(
        CAMPAIGN / "sources/seed_manifest.json"
    )
    for field in (
        "candidate_ledger_present_at_lock",
        "discovery_implementation_present_at_lock",
        "discovery_source_manifest_present_at_lock",
        "discovery_started_at_lock",
        "qualification_outputs_present_at_lock",
        "wp6_dz_mr_campaign_present_at_lock",
    ):
        assert lock[field] is False


def test_locked_search_frontier_and_source_budget_are_complete() -> None:
    spec = _json(CAMPAIGN / "qualification_spec.json")
    protocol = _json(CAMPAIGN / "discovery_protocol.json")
    receipt = _json(CAMPAIGN / "search_receipt.json")
    seeds = _json(CAMPAIGN / "sources/seed_manifest.json")
    manifest = _json(CAMPAIGN / "sources/discovery_manifest.json")

    expected_queries = {item["query_id"]: item["text"] for item in protocol["queries"]}
    observed_queries = {item["query_id"]: item["text"] for item in receipt["queries"]}
    assert observed_queries == expected_queries
    assert receipt["query_count"] == len(expected_queries) == 12
    assert all(item["window_complete"] for item in receipt["queries"])
    assert receipt["query_frontier_exhausted"] is True
    assert receipt["all_plausible_results_audited"] is True
    assert receipt["eligible_citation_expansion_exhausted"] is True

    sources = {item["source_id"]: item for item in manifest["sources"]}
    assert len(sources) == manifest["primary_source_count"] == 16
    assert len(sources) <= spec["stop_rule"]["source_cap"]
    assert (
        sum(item["role"] == "CITATION_EXPANSION" for item in sources.values())
        == spec["stop_rule"]["citation_expansion_cap"]
    )
    for seed in seeds["sources"]:
        assert sources[seed["source_id"]]["sha256"] == seed["sha256"]


def test_candidate_ledger_derives_only_the_bounded_null_result() -> None:
    spec = _json(CAMPAIGN / "qualification_spec.json")
    ledger = _json(CAMPAIGN / "candidate_ledger.json")
    requirement_ids = set(spec["witness_requirements"])
    candidates = ledger["candidates"]

    assert ledger["status"] == "DISCOVERY_COMPLETE"
    assert ledger["proposed_outcome"] == EXPECTED_OUTCOME
    assert ledger["nearest_miss_candidate_id"] == "C03"
    assert len(candidates) == ledger["candidate_family_count"] == 12
    assert len(candidates) <= spec["stop_rule"]["candidate_family_cap"]
    assert all(
        set(candidate["requirements"]) == requirement_ids for candidate in candidates
    )
    assert all(
        any(
            requirement["status"] == "FAIL"
            for requirement in candidate["requirements"].values()
        )
        for candidate in candidates
    )

    nearest = next(item for item in candidates if item["candidate_id"] == "C03")
    assert nearest["requirements"]["W1"]["status"] == "PASS"
    assert nearest["requirements"]["W2"]["status"] == "PASS"
    assert nearest["requirements"]["W3"]["status"] == "PASS"
    assert nearest["requirements"]["W4"]["status"] == "PASS"
    assert nearest["requirements"]["W5"]["status"] == "FAIL"

    coverage = {
        item["candidate_class"]: item for item in ledger["mandatory_class_coverage"]
    }
    assert set(coverage) == set(spec["mandatory_candidate_classes"])
    assert all(item["status"] == "COMPLETE" for item in coverage.values())
    assert all(item["candidate_ids"] for item in coverage.values())


def test_claim_boundary_and_mr_prohibition_are_explicit() -> None:
    spec = _json(CAMPAIGN / "qualification_spec.json")
    boundary = (ROOT / "src/python/wp6_dz_feas_v1/QUALIFICATION_BOUNDARY.md").read_text(
        encoding="utf-8"
    )
    audit = (CAMPAIGN / "proof/WP6-DZ-FEAS-v1-audit.md").read_text(encoding="utf-8")
    reference = (CAMPAIGN / "reference/exact_controls.py").read_text(encoding="utf-8")

    assert "No suitable witness exists." in spec["decision_policy"].values()
    assert "WP6-DZ-MR-v1" in spec["decision_policy"]["MR_PROMOTION_RULE"]
    assert "QUALIFIED_WITNESS" in spec["decision_policy"]["MR_PROMOTION_RULE"]
    assert EXPECTED_OUTCOME in boundary
    assert "bounded witness-feasibility campaign" in boundary
    assert "WP6-DZ-MR-v1" in audit
    assert "must not be created" in audit
    assert "src.python" not in reference
    assert "wp6_dz_feas_v1" not in reference
    for relative in (
        "validation-external/wp6-dz-mr-v1",
        "src/python/wp6_dz_mr_v1",
        "tests/wp6_dz_mr_v1",
    ):
        assert not (ROOT / relative).exists()


def test_final_record_seals_bounded_null_when_present() -> None:
    record_path = REPORTS / "wp6_dz_feas_v1_qualification_record.json"
    if not record_path.exists():
        pytest.skip("qualification has not been finalized")

    lock = _json(REPORTS / "wp6_dz_feas_v1_qualification_lock.json")
    results = _json(CAMPAIGN / "results/qualification_results.json")
    record = _json(record_path)
    unsigned = dict(record)
    signature = unsigned.pop("record_payload_sha256")

    assert hashlib.sha256(_canonical(unsigned)).hexdigest() == signature
    assert results["qualification_gate_status"] == "PASS"
    assert results["outcome"] == EXPECTED_OUTCOME
    assert results["mr_promotion_authorized"] is False
    assert all(gate["passed"] for gate in results["gates"])
    assert record["qualification_id"] == lock["qualification_id"]
    assert record["lock_sha256"] == lock["lock_sha256"]
    assert record["status"] == EXPECTED_OUTCOME
    assert record["nearest_miss_candidate_id"] == "C03"
    assert record["qualifying_candidate_ids"] == []
    assert record["results_sha256"] == _sha256(
        CAMPAIGN / "results/qualification_results.json"
    )
