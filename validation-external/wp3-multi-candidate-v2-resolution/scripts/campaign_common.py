"""Integrity helpers for WP3-MULTI-CAND-v2-RES-v1."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp3_multi_v2_resolution_specification_lock.json"
)
SOURCE_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
RESERVE_PATH = (
    VALIDATION_ROOT / "wp3-v2-exploration/sealed/publication_holdout_commitments.json"
)

for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
)


def verify_specification_lock(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    lock = load_json(SPECIFICATION_LOCK)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("candidate-resolution specification lock is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "candidate_resolution_specification"
        or lock.get("candidate_expression_accessed_before_lock") is not False
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("candidate-resolution lock does not bind this spec")
    for relative, expected_hash in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected_hash:
            raise RuntimeError(f"candidate-resolution prerequisite changed: {relative}")
    return lock


def verify_candidate_metadata(spec: dict[str, Any]) -> dict[str, Any]:
    expected = spec["prerequisites"]["wp3_multi_v2"]
    results = load_json(SOURCE_ROOT / "results/search_results.json")
    gate = load_json(SOURCE_ROOT / "results/publication_gate.json")
    record = load_json(SOURCE_ROOT / "reports/wp3_multi_v2_search_record.json")
    decision = load_json(SOURCE_ROOT / "reports/wp3_multi_v2_candidate_decision.json")
    search = results["search"]
    candidates = search["candidate_subspaces"]
    if (
        results.get("status") != expected["expected_status"]
        or results.get("qualification_id") != expected["qualification_id"]
        or results.get("lock_sha256") != expected["lock_sha256"]
        or int(search.get("candidate_count", -1))
        != expected["expected_candidate_subspace_count"]
        or len(candidates) != expected["expected_candidate_subspace_count"]
        or int(candidates[0].get("dimension", -1))
        != expected["expected_candidate_dimension"]
        or candidates[0].get("mode_ranks") != [expected["expected_mode_rank"]]
        or gate.get("PUBLICATION_GATE") != "BLOCKED_PENDING_CANDIDATE_RESOLUTION"
        or gate.get("INTERPRETATION_AUTHORIZATION") != "PROHIBITED"
        or record.get("record_payload_sha256") != expected["record_payload_sha256"]
        or decision.get("status") != "REQUIRES_CANDIDATE_RESOLUTION_SPEC"
    ):
        raise RuntimeError("candidate metadata does not match the locked contract")
    return {
        "qualification_id": expected["qualification_id"],
        "candidate_subspace_count": len(candidates),
        "candidate_dimension": int(candidates[0]["dimension"]),
        "mode_rank": int(candidates[0]["mode_ranks"][0]),
        "generalized_singular_value": float(
            candidates[0]["generalized_singular_value_min"]
        ),
        "backend_uncertainty": float(
            search["null_result_spectral_certificate"]["svd_backend_uncertainty_bound"]
        ),
        "publication_gate": gate["PUBLICATION_GATE"],
        "interpretation_authorization": gate["INTERPRETATION_AUTHORIZATION"],
    }


def verify_publication_reserve(expected_hash: str) -> dict[str, Any]:
    payload = load_json(RESERVE_PATH)
    commitments = payload.get("commitments", [])
    forbidden = {
        "source_case_id",
        "source_index",
        "initial_positions_decimal",
        "initial_velocities_decimal",
        "brutus_final_positions_decimal",
        "brutus_final_velocities_decimal",
    }
    if (
        sha256_file(RESERVE_PATH) != expected_hash
        or payload.get("status") != "SEALED_UNEXECUTED"
        or payload.get("case_count") != 24
        or len(commitments) != 24
        or any(item.get("status") != "SEALED_UNEXECUTED" for item in commitments)
        or any(forbidden & set(item) for item in commitments)
    ):
        raise RuntimeError("publication reserve is not intact and sealed")
    return {
        "status": "SEALED_UNEXECUTED",
        "case_count": 24,
        "sha256": sha256_file(RESERVE_PATH),
        "source_rows_present": False,
    }
