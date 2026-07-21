"""Integrity helpers for WP3-MULTI-CAND-v2-RES-v2."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution-v2"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp3_multi_v2_resolution_v2_specification_lock.json"
)
ASSESSMENT_PATH = (
    CAMPAIGN_ROOT / "reports/wp3_multi_v2_resolution_v1_protocol_assessment.json"
)
SOURCE_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
V1_RESOLUTION_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution"
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
        raise RuntimeError("corrected resolution specification lock is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "corrective_claim_specification"
        or lock.get("candidate_access_before_lock")
        != "DISCLOSED_FROM_SUPERSEDED_V1"
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("corrected resolution lock does not bind this spec")
    for relative, expected_hash in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected_hash:
            raise RuntimeError(f"corrected resolution prerequisite changed: {relative}")
    return lock


def verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    assessment = load_json(ASSESSMENT_PATH)
    source = spec["prerequisites"]["wp3_multi_v2"]
    superseded = spec["prerequisites"]["superseded_resolution_v1"]
    challenge = spec["prerequisites"]["challenge_corpus"]
    paths = {
        "source_results": REPO_ROOT / source["results_file"],
        "source_gate": REPO_ROOT / source["publication_gate_file"],
        "superseded_result": REPO_ROOT / superseded["result_file"],
        "challenge": REPO_ROOT / challenge["path"],
    }
    if (
        assessment.get("status") != superseded["expected_status"]
        or assessment.get("successor") != spec["campaign"]
        or assessment.get("claim_authorization") != "NONE"
        or assessment.get("publication_reserve_accessed") is not False
        or sha256_file(paths["source_results"]) != source["results_sha256"]
        or sha256_file(paths["source_gate"]) != source["publication_gate_sha256"]
        or sha256_file(paths["superseded_result"])
        != superseded["result_sha256"]
        or sha256_file(paths["challenge"]) != challenge["sha256"]
    ):
        raise RuntimeError("corrected resolution prerequisites do not match")
    source_results = load_json(paths["source_results"])
    source_gate = load_json(paths["source_gate"])
    if (
        source_results.get("qualification_id") != source["qualification_id"]
        or source_results.get("status")
        != "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION"
        or source_gate.get("PUBLICATION_GATE")
        != "BLOCKED_PENDING_CANDIDATE_RESOLUTION"
    ):
        raise RuntimeError("WP3 v2 candidate state changed")
    return {
        "source_qualification_id": source["qualification_id"],
        "superseded_qualification_id": superseded["qualification_id"],
        "assessment_sha256": sha256_file(ASSESSMENT_PATH),
        "challenge_sha256": sha256_file(paths["challenge"]),
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
