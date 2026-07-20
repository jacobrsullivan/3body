"""Integrity and prerequisite verification for WP4-UP-READY-v3."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Iterable

from src.python.wp4_upstairs_v2.integrity import (
    _input_files,
    atomic_write_json,
    canonical_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_signed_lock,
    verify_wp2_prerequisite,
)


def verify_wp3_v3_null_result(
    root: str | Path,
    expected: dict[str, Any],
) -> dict[str, Any]:
    repo = Path(root).resolve()
    paths = {
        "search_lock_file_sha256": repo / expected["search_lock_path"],
        "search_record_sha256": repo / expected["search_record_path"],
        "search_results_sha256": repo / expected["search_results_path"],
        "staged_gate_sha256": repo / expected["staged_gate_path"],
        "candidate_decision_sha256": repo / expected["candidate_decision_path"],
        "candidate_protocol_sha256": repo / expected["candidate_protocol_path"],
        "publication_reserve_sha256": repo / expected["publication_reserve_path"],
    }
    observed_hashes = {name: sha256_file(path) for name, path in paths.items()}
    if any(observed_hashes[name] != expected[name] for name in observed_hashes):
        raise RuntimeError("WP3-v3 evidence hash mismatch")

    lock = verify_signed_lock(paths["search_lock_file_sha256"], repo)
    record = load_json(paths["search_record_sha256"])
    unsigned_record = dict(record)
    record_payload = unsigned_record.pop("record_payload_sha256", None)
    if (
        record_payload != expected["search_record_payload_sha256"]
        or sha256_bytes(canonical_json(unsigned_record)) != record_payload
    ):
        raise RuntimeError("WP3-v3 search record payload integrity failure")
    results = load_json(paths["search_results_sha256"])
    gate = load_json(paths["staged_gate_sha256"])
    decision = load_json(paths["candidate_decision_sha256"])
    reserve = load_json(paths["publication_reserve_sha256"])
    certificate = results.get("search", {}).get("null_result_spectral_certificate", {})

    required_gate = {
        "SEARCH_READY": "PASS",
        "NULL_RESULT_READY": "PASS",
        "CANDIDATE_READY": "NOT_TRIGGERED",
        "SEALED_QUALIFICATION": "NOT_TRIGGERED",
        "WP4_READY": "BLOCKED",
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "candidate_count": 0,
        "qualification_id": expected["qualification_id"],
        "lock_sha256": expected["lock_sha256"],
    }
    for name, value in required_gate.items():
        if gate.get(name) != value:
            raise RuntimeError(f"WP3-v3 null-result contract failed at {name}")
    if not (
        lock.get("qualification_id") == expected["qualification_id"]
        and lock.get("lock_sha256") == expected["lock_sha256"]
        and record.get("qualification_id") == expected["qualification_id"]
        and record.get("lock_sha256") == expected["lock_sha256"]
        and record.get("status") == "COMPLETE_BOUNDED_NULL_RESULT"
        and record.get("candidate_count") == 0
        and record.get("search_ready") == "PASS"
        and record.get("null_result_ready") == "PASS"
        and record.get("candidate_ready") == "NOT_TRIGGERED"
        and record.get("sealed_qualification") == "NOT_TRIGGERED"
        and record.get("results_sha256") == expected["search_results_sha256"]
        and record.get("gate_sha256") == expected["staged_gate_sha256"]
        and results.get("status") == "COMPLETE_BOUNDED_NULL_RESULT"
        and results.get("search", {}).get("candidate_count") == 0
        and certificate.get("certifies_no_training_eligible_direction") is True
        and float(certificate.get("backend_guarded_lower_bound", 0.0))
        > float(certificate.get("candidate_training_threshold", 0.0))
        and decision.get("status") == "NOT_TRIGGERED_NO_CANDIDATE"
        and decision.get("candidate_count") == 0
        and decision.get("candidate_specific_lock") == "NOT_CREATED"
        and decision.get("sealed_execution") == "PROHIBITED"
        and decision.get("wp4_candidate_validation") == "BLOCKED"
        and decision.get("search_record_sha256") == expected["search_record_sha256"]
        and decision.get("null_result_spectral_certificate") == certificate
        and decision.get("publication_reserve_sha256")
        == expected["publication_reserve_sha256"]
        and reserve.get("status") == "SEALED_UNEXECUTED"
        and reserve.get("case_count") == 24
    ):
        raise RuntimeError("WP3-v3 immutable null-result chain is inconsistent")
    return {
        "search_status": gate["SEARCH_READY"],
        "null_result_status": gate["NULL_RESULT_READY"],
        "candidate_count": 0,
        "candidate_status": gate["CANDIDATE_READY"],
        "sealed_qualification_status": gate["SEALED_QUALIFICATION"],
        "wp4_candidate_status": gate["WP4_READY"],
        "publication_reserve_status": gate["publication_reserve_status"],
        "qualification_id": gate["qualification_id"],
        "lock_sha256": gate["lock_sha256"],
        "search_record_payload_sha256": record_payload,
        "spectral_certificate": certificate,
        **observed_hashes,
    }


def build_readiness_lock_v3(
    *,
    root: str | Path,
    spec_path: str | Path,
    scopes: Iterable[str],
    external_paths: Iterable[str],
    output_paths: Iterable[str],
    prerequisite: dict[str, Any],
    wp3_state: dict[str, Any],
) -> dict[str, Any]:
    repo = Path(root).resolve()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo,
        text=True,
    ).strip()
    if dirty:
        raise RuntimeError("WP4-v3 freeze requires a clean worktree")
    present_outputs = [path for path in output_paths if (repo / path).exists()]
    if present_outputs:
        raise RuntimeError(
            "readiness outputs must be absent at freeze: " + ", ".join(present_outputs)
        )
    files = _input_files(repo, scopes)
    file_hashes = {
        path.relative_to(repo).as_posix(): sha256_file(path) for path in files
    }
    external_hashes = {path: sha256_file(repo / path) for path in external_paths}
    snapshot = sha256_bytes(
        canonical_json(
            {
                "file_hashes": file_hashes,
                "external_file_hashes": external_hashes,
            }
        )
    )
    base_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "qualification_id": f"WP4-UP-READY-v3-{snapshot[:12]}",
        "frozen_utc": utc_now(),
        "base_git_commit": base_commit,
        "clean_worktree_at_freeze": True,
        "readiness_outputs_absent_at_freeze": True,
        "candidate_input_present_at_freeze": False,
        "publication_reserve_opened_at_freeze": False,
        "spec_sha256": sha256_file(spec_path),
        "code_snapshot_sha256": snapshot,
        "file_hashes": file_hashes,
        "external_file_hashes": external_hashes,
        "wp2_upstairs_prerequisite": prerequisite,
        "wp3_upstairs_state": wp3_state,
        "runtime": runtime_fingerprint(),
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


__all__ = [
    "atomic_write_json",
    "build_readiness_lock_v3",
    "canonical_json",
    "load_json",
    "make_gate",
    "runtime_fingerprint",
    "sha256_bytes",
    "sha256_file",
    "utc_now",
    "verify_signed_lock",
    "verify_wp2_prerequisite",
    "verify_wp3_v3_null_result",
]
