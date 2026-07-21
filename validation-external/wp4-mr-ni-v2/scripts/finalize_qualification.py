#!/usr/bin/env python
"""Finalize committed WP4-MR-NI-v2 evidence into a record and report."""

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
    parser.add_argument("--record", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    record_path = Path(args.record)
    report_path = Path(args.report)
    if record_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite immutable final qualification output")
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
    ):
        raise RuntimeError("qualification results are not finalizable PASS evidence")
    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    application = results["project_application"]
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
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "source_manifest_sha256": results["source_manifest_sha256"],
        "catalogue_sha256": results["catalogue_sha256"],
        "results_sha256": sha256_file(args.results),
        "source_records": results["source_records"],
        "source_text_checks": results["source_text_checks"],
        "source_power_notation": results["source_power_notation"],
        "benchmark_count": len(results["benchmark_results"]),
        "project_candidate_count": application["candidate_count"],
        "distinct_mass_triple_count": application["distinct_mass_triple_count"],
        "exceptional_mass_triple_count": application["exceptional_mass_triple_count"],
        "nonexceptional_mass_triple_count": application[
            "nonexceptional_mass_triple_count"
        ],
        "all_project_masses_positive": application["all_project_masses_positive"],
        "all_project_cases_universally_obstructed": application[
            "all_cases_universally_obstructed"
        ],
        "production_reference_exact_agreement": application[
            "production_reference_exact_agreement"
        ],
        "invalidated_predecessor": results["invalidated_predecessor"],
        "legacy_placeholder": results["legacy_placeholder"],
        "independent_reference": results["independent_reference"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)
    lines = [
        "# WP4-MR-NI-v2 Qualification Report",
        "",
        "**Status:** PASS",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Qualified Result",
        "",
        results["authorized_claim"],
        "",
        f"- Qualified WP1 catalogue cases: {application['candidate_count']}",
        f"- Distinct exact mass triples: {application['distinct_mass_triple_count']}",
        f"- Linear-NVE exceptional mass triples: {application['exceptional_mass_triple_count']}",
        f"- Nonexceptional mass triples: {application['nonexceptional_mass_triple_count']}",
        "- Production/reference arithmetic: exact agreement",
        "- Legacy Kovacic placeholder: excluded",
        "",
        "The linear-NVE exceptional classification is not interpreted as nonlinear integrability. The universal complete-integrability obstruction applies to every positive-mass case, including exceptional first-variational-equation cases.",
        "",
        "## Qualification Gates",
        "",
        "| Gate | Observed | Requirement | Result |",
        "|---|---:|---:|:---:|",
        *[_format_gate(item) for item in results["gates"]],
        "",
        "## Claim Boundary",
        "",
        results["claim_boundary"],
        "",
        "## Integrity",
        "",
        f"- Evidence commit: `{evidence_commit}`",
        f"- Qualification lock: `{lock['lock_sha256']}`",
        f"- Results SHA-256: `{sha256_file(args.results)}`",
        f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
        "- WP4-MR-NI-v1: invalidated before implementation or execution",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"finalized {lock['qualification_id']}: PASS")


if __name__ == "__main__":
    main()
