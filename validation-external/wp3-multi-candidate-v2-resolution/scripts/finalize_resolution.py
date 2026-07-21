#!/usr/bin/env python
"""Finalize committed candidate-resolution evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


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


ALLOWED = {
    "REJECTED_NUMERICAL_OR_GENERALIZATION_ARTIFACT",
    "EXACT_KNOWN_DIRECTION",
    "SURVIVES_RESOLUTION",
    "SURVIVES_NUMERICALLY_FORMULA_UNRESOLVED",
}


def _format_gate(gate: dict[str, Any]) -> str:
    return (
        f"| `{gate['name']}` | {gate['observed']} | "
        f"{gate['comparator']} {gate['threshold']} | "
        f"{'PASS' if gate['passed'] else 'FAIL'} |"
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
        raise RuntimeError("refusing to overwrite immutable resolution finalization")
    require_clean_worktree(REPO_ROOT)
    result_relative = Path(args.results).resolve().relative_to(REPO_ROOT).as_posix()
    git_output(REPO_ROOT, "ls-files", "--error-unmatch", result_relative)
    spec = load_json(args.spec)
    results = load_json(args.results)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        results.get("status") not in ALLOWED
        or results.get("decision") != results.get("status")
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or results.get("publication_reserve_accessed") is not False
        or results.get("publication_reserve_after", {}).get("status")
        != "SEALED_UNEXECUTED"
    ):
        raise RuntimeError("resolution result is not finalizable")
    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    unsigned = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "evidence_git_commit": evidence_commit,
        "status": results["status"],
        "decision": results["decision"],
        "next_action": results["next_action"],
        "claim_boundary": results["claim_boundary"],
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "challenge_corpus_sha256": results["challenge_corpus_sha256"],
        "results_sha256": sha256_file(args.results),
        "candidate_metadata": results["candidate_metadata"],
        "backend_replication": results["backend_replication"],
        "challenge_summary": results["challenge_summary"],
        "independent_precision": results["independent_precision"],
        "formula_resolution": results["formula_resolution"],
        "known_direction_test": results["known_direction_test"],
        "numeric_gates_pass": results["numeric_gates_pass"],
        "formula_resolved": results["formula_resolved"],
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "publication_reserve_accessed": False,
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)
    lines = [
        "# WP3-MULTI-CAND-v2 Candidate Resolution Report",
        "",
        f"**Status:** {results['status']}",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Decision",
        "",
        results["next_action"],
        "",
        f"- Backend subspace projection minimum: `{results['backend_replication']['subspace_projection_min']:.12e}`",
        f"- Backend singular-value relative spread: `{results['backend_replication']['generalized_singular_relative_spread']:.12e}`",
        f"- Challenge value standard deviation minimum: `{results['challenge_summary']['value_std_min']:.12e}`",
        f"- Challenge Lie RMS maximum: `{results['challenge_summary']['lie_rms_max']:.12e}`",
        f"- Challenge Lie absolute maximum: `{results['challenge_summary']['lie_abs_max']:.12e}`",
        f"- 80-digit value disagreement maximum: `{results['independent_precision']['value_relative_difference_max']:.12e}`",
        f"- 80-digit Lie disagreement maximum: `{results['independent_precision']['lie_relative_difference_max']:.12e}`",
        f"- Rational reconstruction terms: {results['formula_resolution']['nonzero_term_count']}",
        f"- Known-direction coefficient residual: `{results['known_direction_test']['coefficient_projection_residual']:.12e}`",
        "",
        "## Frozen Gates",
        "",
        "| Gate | Observed | Requirement | Result |",
        "|---|---:|---:|:---:|",
        *[_format_gate(item) for item in results["gates"]],
        "",
        "## Candidate Terms",
        "",
    ]
    top_terms = results["candidate_expression_access"]["committed_top_terms"]
    if top_terms:
        lines.extend(
            f"- `{item['feature']}`: `{item['coefficient']:.12e}`" for item in top_terms
        )
    else:
        lines.append("No top terms were recorded.")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            results["claim_boundary"],
            "",
            "## Integrity",
            "",
            f"- Evidence commit: `{evidence_commit}`",
            f"- Resolution lock: `{lock['lock_sha256']}`",
            f"- Results SHA-256: `{sha256_file(args.results)}`",
            f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
            "- Publication reserve: **SEALED_UNEXECUTED**",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"finalized {lock['qualification_id']}: {results['status']}")


if __name__ == "__main__":
    main()
