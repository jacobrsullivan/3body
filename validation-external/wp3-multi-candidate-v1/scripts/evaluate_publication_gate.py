#!/usr/bin/env python
"""Evaluate the publication gate before any WP3 multi result interpretation."""

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


def decide_publication_gate(
    *,
    search_status: str,
    candidate_count: int,
    null_certified: bool,
) -> dict[str, str]:
    """Return the fail-closed staged decision without inspecting expressions."""

    if candidate_count < 0 or (candidate_count == 0) != null_certified:
        raise RuntimeError("spectral candidate count and null certificate disagree")
    if candidate_count == 0:
        if search_status != "COMPLETE_BOUNDED_NULL_RESULT":
            raise RuntimeError("zero-candidate search status is inconsistent")
        return {
            "PUBLICATION_GATE": "PASS_BOUNDED_NULL_ONLY",
            "INTERPRETATION_AUTHORIZATION": "BOUNDED_NULL_ONLY",
            "NULL_RESULT_READY": "PASS",
            "CANDIDATE_READY": "NOT_TRIGGERED",
            "SEALED_QUALIFICATION": "NOT_TRIGGERED",
            "WP4_READY": "NOT_TRIGGERED_NO_CANDIDATE",
        }
    if search_status != "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION":
        raise RuntimeError("candidate-subspace search status is inconsistent")
    return {
        "PUBLICATION_GATE": "BLOCKED_PENDING_CANDIDATE_RESOLUTION",
        "INTERPRETATION_AUTHORIZATION": "PROHIBITED",
        "NULL_RESULT_READY": "BLOCKED",
        "CANDIDATE_READY": "BLOCKED_PENDING_RESOLUTION_SPEC",
        "SEALED_QUALIFICATION": "BLOCKED_PENDING_RESOLUTION",
        "WP4_READY": "BLOCKED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite immutable publication gate")
    spec = load_json(args.spec)
    results = load_json(args.results)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    common = campaign_module(
        REPO_ROOT
        / "validation-external/wp3-multi-candidate-v1/scripts/campaign_common.py",
        "_wp3_multi_campaign_common_gate",
    )
    common.verify_specification_lock(args.spec)
    reserve = common.verify_publication_reserve(
        args.commitments,
        spec["prerequisites"]["sealed_publication_reserve_sha256"],
    )
    if (
        results.get("campaign") != spec["campaign"]
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or results.get("spec_sha256") != sha256_file(args.spec)
        or results.get("corpus_sha256") != sha256_file(args.corpus)
        or results.get("interpretation_status")
        != "PROHIBITED_PENDING_PUBLICATION_GATE"
        or results.get("search_ready") != "PASS"
        or not all(gate.get("passed") for gate in results.get("readiness_gates", []))
    ):
        raise RuntimeError("search is not eligible for publication-gate evaluation")
    search = results["search"]
    candidate_count = int(search["candidate_count"])
    null_certified = bool(
        search["null_result_spectral_certificate"][
            "certifies_no_training_eligible_direction"
        ]
    )
    partition_consistent = bool(
        candidate_count == len(search["candidate_subspaces"])
        and (candidate_count == 0) == null_certified
        and int(search["numerical_nullity_at_candidate_threshold"])
        == sum(
            int(candidate["dimension"])
            for candidate in search["candidate_subspaces"]
        )
    )
    if not partition_consistent:
        raise RuntimeError("spectral candidate partition is inconsistent")
    decision = decide_publication_gate(
        search_status=results.get("status", ""),
        candidate_count=candidate_count,
        null_certified=null_certified,
    )
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "results_sha256": sha256_file(args.results),
        "PUBLICATION_GATE": decision["PUBLICATION_GATE"],
        "INTERPRETATION_AUTHORIZATION": decision[
            "INTERPRETATION_AUTHORIZATION"
        ],
        "SEARCH_READY": "PASS",
        "NULL_RESULT_READY": decision["NULL_RESULT_READY"],
        "CANDIDATE_READY": decision["CANDIDATE_READY"],
        "SEALED_QUALIFICATION": decision["SEALED_QUALIFICATION"],
        "WP4_READY": decision["WP4_READY"],
        "candidate_subspace_count": candidate_count,
        "spectral_partition_consistent": True,
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
