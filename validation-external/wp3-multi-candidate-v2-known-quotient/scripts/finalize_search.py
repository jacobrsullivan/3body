#!/usr/bin/env python
"""Finalize committed successor search and publication-gate evidence."""

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
    parser.add_argument("--gate", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    record_path = Path(args.record)
    report_path = Path(args.report)
    if record_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite successor finalization")
    require_clean_worktree(REPO_ROOT)
    for path in (args.results, args.gate):
        relative = Path(path).resolve().relative_to(REPO_ROOT).as_posix()
        git_output(REPO_ROOT, "ls-files", "--error-unmatch", relative)
    spec = load_json(args.spec)
    results = load_json(args.results)
    gate = load_json(args.gate)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        results.get("qualification_id") != lock["qualification_id"]
        or gate.get("qualification_id") != lock["qualification_id"]
        or gate.get("results_sha256") != sha256_file(args.results)
        or gate.get("publication_reserve", {}).get("status")
        != "SEALED_UNEXECUTED"
    ):
        raise RuntimeError("successor result and gate are not finalizable")
    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    unsigned = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "evidence_git_commit": evidence_commit,
        "status": results["status"],
        "publication_gate": gate["PUBLICATION_GATE"],
        "interpretation_authorization": gate["INTERPRETATION_AUTHORIZATION"],
        "claim_boundary": results["claim_boundary"],
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "results_sha256": sha256_file(args.results),
        "publication_gate_sha256": sha256_file(args.gate),
        "source_matrix_hashes": results["source_matrix_hashes"],
        "domain_summaries": results["search"]["domains"],
        "candidate_subspace_count": results["search"][
            "candidate_subspace_count"
        ],
        "all_domains_certify_no_eligible_direction": results["search"][
            "all_domains_certify_no_eligible_direction"
        ],
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "publication_reserve_accessed": False,
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)
    lines = [
        "# WP3-MULTI-CAND-v2 Observable Known-Quotient Report",
        "",
        f"**Status:** {results['status']}",
        "",
        f"**Publication gate:** {gate['PUBLICATION_GATE']}",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Domain Certificates",
        "",
        "| Domain | Value rank | Smallest values | Relative spread | Guarded lower bound | Null certified |",
        "|---|---:|---|---:|---:|:---:|",
    ]
    for domain, summary in results["search"]["domains"].items():
        ranks = sorted(set(summary["backend_value_ranks"].values()))
        smallest = ", ".join(
            f"{driver}={value:.6e}"
            for driver, value in summary[
                "backend_smallest_generalized_values"
            ].items()
        )
        lines.append(
            f"| {domain} | {ranks} | {smallest} | "
            f"{summary['backend_smallest_generalized_relative_spread']:.6e} | "
            f"{summary['backend_guarded_lower_bound']:.6e} | "
            f"{'PASS' if summary['certifies_no_eligible_direction'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Readiness Gates",
            "",
            "| Gate | Observed | Requirement | Result |",
            "|---|---:|---:|:---:|",
            *[_format_gate(item) for item in results["readiness_gates"]],
            "",
            "## Claim Boundary",
            "",
            results["claim_boundary"],
            "",
            "## Integrity",
            "",
            f"- Evidence commit: `{evidence_commit}`",
            f"- Search lock: `{lock['lock_sha256']}`",
            f"- Results SHA-256: `{sha256_file(args.results)}`",
            f"- Publication gate SHA-256: `{sha256_file(args.gate)}`",
            f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
            "- Publication reserve: **SEALED_UNEXECUTED**",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"finalized {lock['qualification_id']}: {results['status']} / "
        f"{gate['PUBLICATION_GATE']}"
    )


if __name__ == "__main__":
    main()
