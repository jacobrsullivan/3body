#!/usr/bin/env python
"""Bind the WP3-UP-v3 result to its fail-closed candidate decision."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))
from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_lock,
)


def _verify_record(
    record: dict,
    expected: dict,
    results_path: str,
    gate_path: str,
) -> None:
    unsigned = dict(record)
    payload_hash = unsigned.pop("record_payload_sha256", None)
    if (
        payload_hash != expected["record_payload_sha256"]
        or payload_hash != sha256_bytes(canonical_json(unsigned))
    ):
        raise RuntimeError("search record payload hash is invalid")
    if (
        record.get("qualification_id") != expected["qualification_id"]
        or record.get("lock_sha256") != expected["lock_sha256"]
        or record.get("results_sha256") != sha256_file(results_path)
        or record.get("gate_sha256") != sha256_file(gate_path)
        or record.get("search_ready") != "PASS"
        or record.get("publication_reserve_status") != "SEALED_UNEXECUTED"
    ):
        raise RuntimeError("search record is inconsistent")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--search-lock", required=True)
    parser.add_argument("--search-record", required=True)
    parser.add_argument("--search-results", required=True)
    parser.add_argument("--search-gate", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite immutable candidate decision")

    protocol = load_json(args.protocol)
    expected = protocol["search_prerequisite"]
    lock = verify_lock(args.search_lock, ROOT, expected_prefix="WP3-UP-CAND-v3")
    record = load_json(args.search_record)
    results = load_json(args.search_results)
    gate = load_json(args.search_gate)
    reserve = load_json(args.commitments)
    if (
        lock["qualification_id"] != expected["qualification_id"]
        or lock["lock_sha256"] != expected["lock_sha256"]
        or sha256_file(args.search_lock) != expected["lock_file_sha256"]
        or sha256_file(args.search_record) != expected["record_sha256"]
        or sha256_file(args.search_results) != expected["results_sha256"]
        or sha256_file(args.search_gate) != expected["gate_sha256"]
    ):
        raise RuntimeError("candidate protocol references different search evidence")
    _verify_record(record, expected, args.search_results, args.search_gate)

    if (
        results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or gate.get("qualification_id") != lock["qualification_id"]
        or gate.get("lock_sha256") != lock["lock_sha256"]
        or gate.get("SEARCH_READY") != "PASS"
    ):
        raise RuntimeError("search outputs do not match their ready lock")
    search = results["search"]
    candidate_count = int(search["candidate_count"])
    null_certified = bool(
        search["null_result_spectral_certificate"][
            "certifies_no_training_eligible_direction"
        ]
    )
    if (
        candidate_count != len(search["candidate_subspaces"])
        or gate.get("candidate_count") != candidate_count
        or record.get("candidate_count") != candidate_count
        or (candidate_count == 0) != null_certified
    ):
        raise RuntimeError("candidate decision disagrees across frozen evidence")
    if (
        sha256_file(args.commitments) != protocol["publication_reserve_sha256"]
        or reserve.get("status") != "SEALED_UNEXECUTED"
        or reserve.get("case_count") != 24
    ):
        raise RuntimeError("publication reserve is not sealed")

    if candidate_count == 0:
        if (
            results.get("status") != "COMPLETE_BOUNDED_NULL_RESULT"
            or gate.get("NULL_RESULT_READY") != "PASS"
            or gate.get("CANDIDATE_READY") != "NOT_TRIGGERED"
            or gate.get("SEALED_QUALIFICATION") != "NOT_TRIGGERED"
        ):
            raise RuntimeError("zero-candidate staged policy is inconsistent")
        status = "NOT_TRIGGERED_NO_CANDIDATE"
        candidate_lock = "NOT_CREATED"
    else:
        if (
            results.get("status") != "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION"
            or gate.get("NULL_RESULT_READY") != "BLOCKED"
            or gate.get("CANDIDATE_READY") != "BLOCKED_PENDING_RESOLUTION"
        ):
            raise RuntimeError("candidate-subspace staged policy is inconsistent")
        status = "REQUIRES_CANDIDATE_RESOLUTION_SPEC"
        candidate_lock = "BLOCKED_PENDING_RESOLUTION"

    payload = {
        "schema_version": "1.0",
        "campaign": protocol["campaign"],
        "generated_utc": utc_now(),
        "status": status,
        "search_qualification_id": lock["qualification_id"],
        "search_lock_sha256": lock["lock_sha256"],
        "search_lock_file_sha256": sha256_file(args.search_lock),
        "search_record_sha256": sha256_file(args.search_record),
        "search_record_payload_sha256": record["record_payload_sha256"],
        "search_results_sha256": sha256_file(args.search_results),
        "search_gate_sha256": sha256_file(args.search_gate),
        "candidate_count": candidate_count,
        "null_result_spectral_certificate": search["null_result_spectral_certificate"],
        "candidate_specific_lock": candidate_lock,
        "sealed_execution": "PROHIBITED",
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "publication_reserve_sha256": sha256_file(args.commitments),
        "wp4_candidate_validation": "BLOCKED",
    }
    atomic_write_json(destination, payload)
    lines = [
        "# Candidate-Specific Qualification Decision v3",
        "",
        f"- Status: **{status}**",
        f"- Candidate-subspace count: {candidate_count}",
        f"- Candidate-specific lock: **{candidate_lock}**",
        "- Sealed execution: **PROHIBITED**",
        "- Publication reserve: **SEALED_UNEXECUTED**",
        "- WP4 candidate validation: **BLOCKED**",
        "",
        "The immutable search record and spectral certificate were verified. No reserve row was opened.",
        "",
    ]
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"{protocol['campaign']}: {status}; reserve=SEALED_UNEXECUTED")


if __name__ == "__main__":
    main()
