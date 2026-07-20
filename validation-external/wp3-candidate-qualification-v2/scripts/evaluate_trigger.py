#!/usr/bin/env python
"""Evaluate whether WP3-UP-v2 may instantiate sealed candidate qualification."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))
from qualification_tools import (  # noqa: E402
    atomic_write_json, canonical_json, load_json, sha256_bytes, sha256_file,
    utc_now, verify_lock,
)


def _verify_record(record: dict, expected: dict, results_path: str, gate_path: str) -> None:
    unsigned = dict(record)
    payload_hash = unsigned.pop("record_payload_sha256", None)
    if payload_hash != expected["record_payload_sha256"] or payload_hash != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("search record payload hash is invalid")
    if (
        record.get("qualification_id") != expected["qualification_id"]
        or record.get("lock_sha256") != expected["lock_sha256"]
        or record.get("record_payload_sha256") != expected["record_payload_sha256"]
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
    lock = verify_lock(args.search_lock, ROOT, expected_prefix="WP3-UP-CAND-v2")
    record = load_json(args.search_record)
    results = load_json(args.search_results)
    gate = load_json(args.search_gate)
    reserve = load_json(args.commitments)
    if (
        lock["qualification_id"] != expected["qualification_id"]
        or lock["lock_sha256"] != expected["lock_sha256"]
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
    candidate_count = int(results["search"]["candidate_count"])
    ready_modes = [mode for mode in results["search"]["modes"] if mode["candidate_ready"]]
    if (
        candidate_count != len(ready_modes)
        or gate.get("candidate_count") != candidate_count
        or record.get("candidate_count") != candidate_count
    ):
        raise RuntimeError("candidate count disagrees across frozen evidence")
    if (
        sha256_file(args.commitments) != protocol["publication_reserve_sha256"]
        or reserve.get("status") != "SEALED_UNEXECUTED"
        or reserve.get("case_count") != 24
    ):
        raise RuntimeError("publication reserve is not sealed")

    trigger_ready = bool(
        candidate_count == 1
        and gate.get("CANDIDATE_READY") == "PASS"
        and gate.get("SEALED_QUALIFICATION") == "REQUIRED"
        and record.get("candidate_ready") == "PASS"
        and record.get("sealed_qualification") == "REQUIRED"
    )
    if candidate_count == 0:
        if gate.get("CANDIDATE_READY") != "NOT_TRIGGERED" or gate.get("SEALED_QUALIFICATION") != "NOT_TRIGGERED":
            raise RuntimeError("zero-candidate staged policy is inconsistent")
        status = "NOT_TRIGGERED_NO_CANDIDATE"
        candidate_lock = "NOT_CREATED"
        sealed_execution = "PROHIBITED"
        wp4_candidate = "BLOCKED"
    elif trigger_ready:
        status = "REQUIRES_NEW_CANDIDATE_SPEC_AND_LOCK"
        candidate_lock = "REQUIRED_BEFORE_EXECUTION"
        sealed_execution = "BLOCKED_PENDING_LOCK"
        wp4_candidate = "BLOCKED_PENDING_QUALIFICATION"
    else:
        status = "BLOCKED_AMBIGUOUS_TRIGGER"
        candidate_lock = "NOT_CREATED"
        sealed_execution = "PROHIBITED"
        wp4_candidate = "BLOCKED"

    payload = {
        "schema_version": "1.0",
        "campaign": protocol["campaign"],
        "generated_utc": utc_now(),
        "status": status,
        "search_qualification_id": lock["qualification_id"],
        "search_lock_sha256": lock["lock_sha256"],
        "search_record_sha256": sha256_file(args.search_record),
        "search_record_payload_sha256": record["record_payload_sha256"],
        "search_results_sha256": sha256_file(args.search_results),
        "search_gate_sha256": sha256_file(args.search_gate),
        "candidate_count": candidate_count,
        "candidate_specific_lock": candidate_lock,
        "sealed_execution": sealed_execution,
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "publication_reserve_sha256": sha256_file(args.commitments),
        "wp4_candidate_validation": wp4_candidate,
    }
    atomic_write_json(destination, payload)
    lines = [
        "# Candidate-Specific Qualification Decision v2", "",
        f"- Status: **{status}**", f"- Candidate count: {candidate_count}",
        f"- Candidate-specific lock: **{candidate_lock}**",
        f"- Sealed execution: **{sealed_execution}**",
        "- Publication reserve: **SEALED_UNEXECUTED**",
        f"- WP4 candidate validation: **{wp4_candidate}**", "",
        "The immutable search record was verified. No expression is inferred from a non-triggered numerical mode, and no reserve row was opened.", "",
    ]
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"{protocol['campaign']}: {status}; reserve=SEALED_UNEXECUTED")


if __name__ == "__main__":
    main()
