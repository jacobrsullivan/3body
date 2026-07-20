#!/usr/bin/env python
"""Create an integrity-bearing final record for a completed WP3-UP-v2 search."""

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True); parser.add_argument("--corpus", required=True)
    parser.add_argument("--lock", required=True); parser.add_argument("--results", required=True)
    parser.add_argument("--gate", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite immutable WP3-UP-v2 record")
    spec, results, gate = load_json(args.spec), load_json(args.results), load_json(args.gate)
    lock = verify_lock(args.lock, ROOT, expected_prefix=spec["campaign"])
    for payload, name in ((results, "results"), (gate, "gate")):
        if payload.get("campaign") != spec["campaign"]:
            raise RuntimeError(f"{name} does not match the campaign")
        if payload.get("qualification_id") != lock["qualification_id"] or payload.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError(f"{name} does not match the search lock")
    if gate.get("SEARCH_READY") != "PASS":
        raise RuntimeError("cannot finalize a search that was not ready")
    search = results["search"]
    candidate_count = int(search["candidate_count"])
    expected_candidate_ready = "PASS" if candidate_count else "NOT_TRIGGERED"
    expected_sealed = "REQUIRED" if candidate_count else "NOT_TRIGGERED"
    expected_status = (
        "CANDIDATE_REQUIRES_SEPARATE_QUALIFICATION"
        if candidate_count
        else "COMPLETE_BOUNDED_NULL_RESULT"
    )
    if (
        results.get("status") != expected_status
        or results.get("interpretation_status") != "PROHIBITED"
        or results.get("spec_sha256") != sha256_file(args.spec)
        or results.get("corpus_sha256") != sha256_file(args.corpus)
        or gate.get("candidate_count") != candidate_count
        or gate.get("CANDIDATE_READY") != expected_candidate_ready
        or gate.get("SEALED_QUALIFICATION") != expected_sealed
        or gate.get("WP4_READY") != "BLOCKED"
        or gate.get("publication_reserve_status") != "SEALED_UNEXECUTED"
    ):
        raise RuntimeError("search results and staged gate are inconsistent")
    unsigned = {
        "schema_version": "1.0", "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"], "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(), "status": results["status"],
        "interpretation_status": results["interpretation_status"],
        "claim_boundary": spec["evidence_boundary"],
        "spec_sha256": sha256_file(args.spec), "corpus_sha256": sha256_file(args.corpus),
        "results_sha256": sha256_file(args.results), "gate_sha256": sha256_file(args.gate),
        "candidate_count": candidate_count,
        "search_ready": gate["SEARCH_READY"], "candidate_ready": gate["CANDIDATE_READY"],
        "sealed_qualification": gate["SEALED_QUALIFICATION"], "wp4_ready": gate["WP4_READY"],
        "publication_reserve_status": gate["publication_reserve_status"],
        "matrix_hashes": results["matrix_hashes"], "source_summary": results["source_summary"],
        "feature_count": int(search["feature_count"]), "value_rank": int(search["value_rank"]),
        "value_identity_nullity": int(search["value_identity_nullity"]),
        "known_algebra_active_rank": int(search["known_algebra_active_rank"]),
        "smallest_post_projection_singular_value": float(min(search["post_projection_singular_values"])),
        "numerical_nullity_at_candidate_threshold": int(search["numerical_nullity_at_candidate_threshold"]),
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(destination, record)
    print(f"finalized {lock['qualification_id']}: {results['status']}")
    print(f"record SHA-256: {sha256_file(destination)}")


if __name__ == "__main__":
    main()
