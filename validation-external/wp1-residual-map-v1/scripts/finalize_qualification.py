#!/usr/bin/env python
"""Finalize committed WP1-RESIDUAL-MAP-v1 PASS evidence."""

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
    canonical_json,
    git_output,
    load_json,
    require_clean_worktree,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_lock,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    record_path = Path(args.record)
    report_path = Path(args.report)
    if record_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite immutable final output")
    require_clean_worktree(REPO_ROOT)
    for path in (args.map, args.results):
        relative = Path(path).resolve().relative_to(REPO_ROOT).as_posix()
        git_output(REPO_ROOT, "ls-files", "--error-unmatch", relative)
    spec = load_json(args.spec)
    results = load_json(args.results)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        results.get("status") != "PASS"
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or results.get("map_sha256") != sha256_file(args.map)
        or not all(gate.get("passed") for gate in results.get("gates", []))
    ):
        raise RuntimeError("results are not finalizable PASS evidence")
    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    unsigned = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "evidence_git_commit": evidence_commit,
        "status": "PASS",
        "authorized_claim": results["authorized_claim"],
        "claim_boundary": results["claim_boundary"],
        "prohibited_claim": results["prohibited_claim"],
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "catalogue_sha256": results["catalogue_sha256"],
        "prerequisites": results["prerequisites"],
        "map_sha256": results["map_sha256"],
        "results_sha256": sha256_file(args.results),
        "candidate_count": results["candidate_count"],
        "counts": results["counts"],
        "production_reference_exact_agreement": results[
            "production_reference_exact_agreement"
        ],
        "reference_source_disjoint": results["reference_source_disjoint"],
        "publication_contract_complete": results[
            "publication_contract_complete"
        ],
        "negative_controls": results["negative_controls"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)
    lines = [
        "# WP1-RESIDUAL-MAP-v1 Qualification Report",
        "",
        "**Status:** PASS",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Qualified Result",
        "",
        results["authorized_claim"],
        "",
        f"- Catalogue rows mapped: {results['candidate_count']}/169",
        f"- Local stable normal-form track: {results['counts']['local_stable_normal_form']}",
        f"- Asymptotic manifold track: {results['counts']['asymptotic_manifold']}",
        f"- Higher-variational overlays: {results['counts']['higher_variational_exception_overlay']}",
        "- Independent exact implementation agreement: PASS",
        "- Publication gate on every row: PASS",
        "",
        "## Claim Boundary",
        "",
        results["claim_boundary"],
        "",
        "## Prohibited Claim",
        "",
        results["prohibited_claim"],
        "",
        "## Integrity",
        "",
        f"- Evidence commit: `{evidence_commit}`",
        f"- Qualification lock: `{lock['lock_sha256']}`",
        f"- Map SHA-256: `{results['map_sha256']}`",
        f"- Results SHA-256: `{sha256_file(args.results)}`",
        f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"finalized {lock['qualification_id']}: PASS")


if __name__ == "__main__":
    main()
