#!/usr/bin/env python
"""Evaluate the successor publication gate before interpretation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    sha256_file,
    utc_now,
    verify_lock,
)
from validation_external_import import campaign_module  # noqa: E402


def decide_publication_gate(status: str) -> dict[str, str]:
    if status == "COMPLETE_BOUNDED_NULL_RESULT":
        return {
            "PUBLICATION_GATE": "PASS_BOUNDED_NULL_ONLY",
            "INTERPRETATION_AUTHORIZATION": "BOUNDED_NULL_ONLY",
            "NULL_RESULT_READY": "PASS",
            "CANDIDATE_READY": "NOT_TRIGGERED",
        }
    if status == "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION":
        return {
            "PUBLICATION_GATE": "BLOCKED_PENDING_CANDIDATE_RESOLUTION",
            "INTERPRETATION_AUTHORIZATION": "PROHIBITED",
            "NULL_RESULT_READY": "BLOCKED",
            "CANDIDATE_READY": "BLOCKED_PENDING_RESOLUTION_SPEC",
        }
    if status == "INVALID_SEARCH_NOT_READY":
        return {
            "PUBLICATION_GATE": "FAIL_INVALID_SEARCH",
            "INTERPRETATION_AUTHORIZATION": "PROHIBITED",
            "NULL_RESULT_READY": "FAIL",
            "CANDIDATE_READY": "FAIL",
        }
    raise RuntimeError(f"unknown successor status: {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite immutable successor gate")
    spec = load_json(args.spec)
    results = load_json(args.results)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    common = campaign_module(
        Path(args.spec).resolve().parent / "scripts/campaign_common.py",
        "_wp3_multi_v2_kq_common_gate",
    )
    common.verify_specification_lock(args.spec)
    reserve = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    if (
        results.get("campaign") != spec["campaign"]
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or results.get("spec_sha256") != sha256_file(args.spec)
        or results.get("interpretation_status")
        != "PROHIBITED_PENDING_PUBLICATION_GATE"
        or results.get("publication_reserve_accessed") is not False
    ):
        raise RuntimeError("successor search is not gate-eligible")
    status = results["status"]
    if status != "INVALID_SEARCH_NOT_READY" and (
        results.get("search_ready") != "PASS"
        or not all(gate.get("passed") for gate in results["readiness_gates"])
    ):
        raise RuntimeError("successor readiness contradicts status")
    search = results["search"]
    count = int(search["candidate_subspace_count"])
    null_certified = bool(search["all_domains_certify_no_eligible_direction"])
    if status != "INVALID_SEARCH_NOT_READY" and (
        not bool(search["spectral_candidate_partition_consistent"])
        or (count == 0) != null_certified
    ):
        raise RuntimeError("successor spectral partition is inconsistent")
    decision = decide_publication_gate(status)
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "results_sha256": sha256_file(args.results),
        **decision,
        "SEARCH_READY": results["search_ready"],
        "candidate_subspace_count": count,
        "all_domains_certify_no_eligible_direction": null_certified,
        "publication_reserve": reserve,
    }
    atomic_write_json(destination, payload)
    print(
        f"{spec['campaign']} publication gate: {decision['PUBLICATION_GATE']}; "
        f"interpretation={decision['INTERPRETATION_AUTHORIZATION']}; "
        "reserve=SEALED_UNEXECUTED"
    )


if __name__ == "__main__":
    main()
