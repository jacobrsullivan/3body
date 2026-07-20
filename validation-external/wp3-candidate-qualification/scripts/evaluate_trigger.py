#!/usr/bin/env python
"""Evaluate whether sealed candidate qualification may be instantiated."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))
from qualification_tools import atomic_write_json, load_json, sha256_file, utc_now, verify_lock  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--search-lock", required=True)
    parser.add_argument("--search-results", required=True)
    parser.add_argument("--search-gate", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    protocol = load_json(args.protocol)
    lock = verify_lock(args.search_lock, ROOT, expected_prefix="WP3-UP-CAND-v1")
    results, gate, reserve = load_json(args.search_results), load_json(args.search_gate), load_json(args.commitments)
    expected = protocol["search_prerequisite"]
    if lock["qualification_id"] != expected["qualification_id"] or lock["lock_sha256"] != expected["lock_sha256"]:
        raise RuntimeError("candidate protocol references a different search lock")
    if results.get("qualification_id") != lock["qualification_id"] or results.get("lock_sha256") != lock["lock_sha256"]:
        raise RuntimeError("search result does not match its lock")
    candidate_count = int(results["search"]["candidate_count"])
    ready_modes = [mode for mode in results["search"]["modes"] if mode["candidate_ready"]]
    gate_ready = gate.get("CANDIDATE_READY") == "PASS"
    if candidate_count != len(ready_modes):
        raise RuntimeError("candidate count disagrees with frozen modes")
    if reserve.get("status") != "SEALED_UNEXECUTED" or reserve.get("case_count") != 24:
        raise RuntimeError("publication reserve is not sealed")
    if candidate_count == 0:
        status = "NOT_TRIGGERED_NO_CANDIDATE"
        candidate_lock = "NOT_CREATED"
        sealed_execution = "PROHIBITED"
        wp4_candidate = "BLOCKED"
    elif candidate_count == 1 and gate_ready:
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
        "schema_version": "1.0", "campaign": protocol["campaign"], "generated_utc": utc_now(),
        "status": status, "search_qualification_id": lock["qualification_id"],
        "search_lock_sha256": lock["lock_sha256"], "search_results_sha256": sha256_file(args.search_results),
        "search_gate_sha256": sha256_file(args.search_gate), "candidate_count": candidate_count,
        "candidate_specific_lock": candidate_lock, "sealed_execution": sealed_execution,
        "publication_reserve_status": "SEALED_UNEXECUTED", "publication_reserve_sha256": sha256_file(args.commitments),
        "wp4_candidate_validation": wp4_candidate,
    }
    atomic_write_json(args.output, payload)
    lines = [
        "# Candidate-Specific Qualification Decision", "", f"- Status: **{status}**",
        f"- Candidate count: {candidate_count}", f"- Candidate-specific lock: **{candidate_lock}**",
        f"- Sealed execution: **{sealed_execution}**", "- Publication reserve: **SEALED_UNEXECUTED**",
        f"- WP4 candidate validation: **{wp4_candidate}**", "",
        "No candidate expression is inferred from a non-triggered numerical mode. The reserve remains closed.", "",
    ]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print(f"{protocol['campaign']}: {status}; reserve=SEALED_UNEXECUTED")


if __name__ == "__main__":
    main()
