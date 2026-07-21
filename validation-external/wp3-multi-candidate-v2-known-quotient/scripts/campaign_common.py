"""Integrity helpers for WP3-MULTI-CAND-v2-KQ-v1."""

from __future__ import annotations

from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np
import scipy


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-known-quotient"
SPECIFICATION_LOCK = CAMPAIGN_ROOT / "reports/wp3_multi_v2_kq_specification_lock.json"
SOURCE_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
RESOLUTION_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution-v2"
V1_CORPUS = VALIDATION_ROOT / "wp3-multi-candidate-v1/data/search_corpus.json"
SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"
WP1_ROOT = VALIDATION_ROOT / "wp1-catalogue-n3bp-validation"
CHALLENGE_PATH = (
    VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution/data/challenge_corpus.json"
)
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
        raise RuntimeError("known-quotient specification lock is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type")
        != "observable_known_quotient_search_specification"
        or lock.get("successor_spectrum_executed_before_lock") is not False
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("known-quotient lock does not bind this spec")
    for relative, expected_hash in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected_hash:
            raise RuntimeError(f"known-quotient prerequisite changed: {relative}")
    return lock


def verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    source_contract = spec["prerequisites"]["wp3_multi_v2"]
    resolution_contract = spec["prerequisites"]["known_function_resolution"]
    source_results = load_json(REPO_ROOT / source_contract["results_path"])
    resolution_results = load_json(
        REPO_ROOT / resolution_contract["results_path"]
    )
    resolution_record = load_json(REPO_ROOT / resolution_contract["record_path"])
    if (
        sha256_file(REPO_ROOT / source_contract["results_path"])
        != source_contract["results_sha256"]
        or source_results.get("qualification_id")
        != source_contract["qualification_id"]
        or source_results.get("status")
        != "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION"
        or sha256_file(REPO_ROOT / resolution_contract["results_path"])
        != resolution_contract["results_sha256"]
        or sha256_file(REPO_ROOT / resolution_contract["record_path"])
        != resolution_contract["record_sha256"]
        or resolution_results.get("qualification_id")
        != resolution_contract["qualification_id"]
        or resolution_results.get("status")
        != resolution_contract["expected_status"]
        or resolution_results.get("scientific_gates_pass") is not True
        or resolution_results.get("publication_reserve_accessed") is not False
        or resolution_record.get("status")
        != resolution_contract["expected_status"]
        or resolution_record.get("results_sha256")
        != resolution_contract["results_sha256"]
    ):
        raise RuntimeError("known-function resolution prerequisite changed")
    inputs = spec["prerequisites"]["source_inputs"]
    observed = {
        "wp3_v1_corpus_sha256": sha256_file(V1_CORPUS),
        "spatial_corpus_sha256": sha256_file(
            SPATIAL_ROOT / "data/qualification_corpus.json"
        ),
        "spatial_development_sha256": sha256_file(
            SPATIAL_ROOT / "results/development.json"
        ),
        "spatial_calibration_sha256": sha256_file(
            SPATIAL_ROOT / "results/calibration.json"
        ),
        "wp1_catalogue_sha256": sha256_file(WP1_ROOT / "data/native_catalogue.json"),
        "challenge_corpus_sha256": sha256_file(CHALLENGE_PATH),
    }
    if observed != inputs:
        raise RuntimeError("known-quotient source inputs changed")
    return {
        "wp3_multi_v2_qualification_id": source_contract["qualification_id"],
        "known_function_resolution_qualification_id": resolution_contract[
            "qualification_id"
        ],
        "source_input_hashes": observed,
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


def verify_decision_runtime(expected: dict[str, Any]) -> dict[str, str]:
    observed = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    if observed != expected:
        raise RuntimeError(
            f"known-quotient decision runtime changed: {observed} != {expected}"
        )
    return observed
