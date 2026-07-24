#!/usr/bin/env python
"""Finalize committed WP4-LIFT-NI-v3 PASS evidence."""

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
    parser.add_argument("--results", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    record_path = Path(args.record)
    report_path = Path(args.report)
    if record_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite immutable final output")
    require_clean_worktree(REPO_ROOT)
    result_relative = Path(args.results).resolve().relative_to(REPO_ROOT).as_posix()
    git_output(REPO_ROOT, "ls-files", "--error-unmatch", result_relative)
    spec = load_json(args.spec)
    results = load_json(args.results)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        results.get("status") != "PASS"
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or not all(gate.get("passed") for gate in results.get("gates", []))
        or not all(results.get("theorem_obligations", {}).values())
        or results.get("mr_reproduced_premise_verified") is not True
    ):
        raise RuntimeError("v3 results are not finalizable PASS evidence")
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
        "prohibited_short_claim": results["prohibited_short_claim"],
        "prohibited_raw_upstairs_claim": results[
            "prohibited_raw_upstairs_claim"
        ],
        "prohibited_global_claim": results["prohibited_global_claim"],
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "source_manifest_sha256": results["source_manifest_sha256"],
        "proof_addendum_sha256": results["proof_addendum_sha256"],
        "inherited_v2_proof_sha256": results["inherited_v2_proof_sha256"],
        "results_sha256": sha256_file(args.results),
        "source_records": results["source_records"],
        "source_text_checks": results["source_text_checks"],
        "prerequisites": results["prerequisites"],
        "mr_reproduced_premise_verified": results[
            "mr_reproduced_premise_verified"
        ],
        "mr_reproduction_summary": results["mr_reproduction_summary"],
        "wp2_chart_contract_verified": results["wp2_chart_contract_verified"],
        "implementation_identity": results["implementation_identity"],
        "production_reference_exact_agreement": results[
            "production_reference_exact_agreement"
        ],
        "theorem_obligations": results["theorem_obligations"],
        "negative_controls": results["negative_controls"],
        "v2_proof_coverage": results["v2_proof_coverage"],
        "v3_addendum_coverage": results["v3_addendum_coverage"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)
    lines = [
        "# WP4-LIFT-NI-v3 Qualification Report",
        "",
        "**Status:** PASS",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Qualified Result",
        "",
        results["authorized_claim"],
        "",
        "- Reproduced MR premise: PASS",
        "- Unchanged v2 transfer implementation identity: PASS",
        "- Exact production/reference agreement: PASS",
        f"- Theorem obligations: {sum(results['theorem_obligations'].values())}/10",
        f"- Negative controls rejected: {sum(results['negative_controls'].values())}/{len(results['negative_controls'])}",
        "",
        "## Claim Boundary",
        "",
        results["claim_boundary"],
        "",
        "## Prohibited Summaries",
        "",
        f"- {results['prohibited_short_claim']}",
        f"- {results['prohibited_raw_upstairs_claim']}",
        f"- {results['prohibited_global_claim']}",
        "",
        "## Integrity",
        "",
        f"- Evidence commit: `{evidence_commit}`",
        f"- Qualification lock: `{lock['lock_sha256']}`",
        f"- Results SHA-256: `{sha256_file(args.results)}`",
        f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"finalized {lock['qualification_id']}: PASS")


if __name__ == "__main__":
    main()
