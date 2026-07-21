#!/usr/bin/env python
"""Finalize committed WP3 v2 evidence after its publication gate."""

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


def _require_committed(path: str | Path) -> None:
    relative = Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    git_output(REPO_ROOT, "ls-files", "--error-unmatch", relative)


def _format_gate(gate: dict[str, Any]) -> str:
    return (
        f"| `{gate['name']}` | {gate['observed']} | "
        f"{gate['comparator']} {gate['threshold']} | "
        f"{'PASS' if gate['passed'] else 'FAIL'} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    destinations = (Path(args.record), Path(args.report), Path(args.decision))
    if any(path.exists() for path in destinations):
        raise RuntimeError("refusing to overwrite immutable final search output")
    require_clean_worktree(REPO_ROOT)
    _require_committed(args.results)
    _require_committed(args.gate)
    spec = load_json(args.spec)
    results = load_json(args.results)
    gate = load_json(args.gate)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or gate.get("qualification_id") != lock["qualification_id"]
        or gate.get("lock_sha256") != lock["lock_sha256"]
        or gate.get("results_sha256") != sha256_file(args.results)
        or gate.get("SEARCH_READY") != "PASS"
        or gate.get("publication_reserve", {}).get("status") != "SEALED_UNEXECUTED"
    ):
        raise RuntimeError("final search inputs are inconsistent")
    search = results["search"]
    candidate_count = int(search["candidate_count"])
    null_result = candidate_count == 0
    expected_gate = (
        "PASS_BOUNDED_NULL_ONLY"
        if null_result
        else "BLOCKED_PENDING_CANDIDATE_RESOLUTION"
    )
    expected_authorization = "BOUNDED_NULL_ONLY" if null_result else "PROHIBITED"
    if (
        gate.get("PUBLICATION_GATE") != expected_gate
        or gate.get("INTERPRETATION_AUTHORIZATION") != expected_authorization
        or gate.get("candidate_subspace_count") != candidate_count
    ):
        raise RuntimeError("publication gate does not match the search")
    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    certificate = search["null_result_spectral_certificate"]
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
        "claim_boundary": spec["evidence_boundary"],
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "results_sha256": sha256_file(args.results),
        "gate_sha256": sha256_file(args.gate),
        "candidate_subspace_count": candidate_count,
        "search_ready": gate["SEARCH_READY"],
        "null_result_ready": gate["NULL_RESULT_READY"],
        "candidate_ready": gate["CANDIDATE_READY"],
        "sealed_qualification": gate["SEALED_QUALIFICATION"],
        "wp4_candidate_ready": gate["WP4_CANDIDATE_READY"],
        "publication_reserve_status": gate["publication_reserve"]["status"],
        "matrix_hashes": results["matrix_hashes"],
        "source_summary": results["source_summary"],
        "declared_feature_count": int(search["feature_count"]),
        "active_feature_count": int(search["active_feature_count"]),
        "structural_zero_feature_count": int(search["structural_zero_feature_count"]),
        "observable_value_rank": int(search["observable_value_rank"]),
        "value_nuisance_nullity": int(search["value_nuisance_nullity"]),
        "value_nuisance_derivative_rank": int(search["value_nuisance_derivative_rank"]),
        "exact_known_module_rank": int(search["exact_known_module_rank"]),
        "exact_known_module_projection_residual": float(
            search["exact_known_module_projection_residual"]
        ),
        "smallest_generalized_combined_constraint_value_singular_value": float(
            min(search["generalized_lie_value_singular_values"])
        ),
        "generalized_spectral_uncertainty": float(
            search["generalized_spectral_uncertainty"]
        ),
        "backend_guarded_spectral_lower_bound": float(
            certificate["backend_guarded_lower_bound"]
        ),
        "candidate_training_threshold": float(
            certificate["candidate_training_threshold"]
        ),
        "candidate_subspaces": search["candidate_subspaces"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(args.record, record)
    decision = {
        "schema_version": "1.0",
        "campaign": "WP3-MULTI-CAND-v2-CANDIDATE-GATE",
        "generated_utc": utc_now(),
        "status": (
            "NOT_TRIGGERED_NO_CANDIDATE"
            if null_result
            else "REQUIRES_CANDIDATE_RESOLUTION_SPEC"
        ),
        "search_qualification_id": lock["qualification_id"],
        "search_lock_sha256": lock["lock_sha256"],
        "search_record_payload_sha256": record["record_payload_sha256"],
        "candidate_subspace_count": candidate_count,
        "candidate_specific_lock": (
            "NOT_CREATED" if null_result else "BLOCKED_PENDING_RESOLUTION"
        ),
        "sealed_execution": "PROHIBITED",
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "wp4_candidate_validation": gate["WP4_CANDIDATE_READY"],
        "morales_ramis_track_relationship": "INDEPENDENT_NOT_CANDIDATE_VALIDATION",
    }
    atomic_write_json(args.decision, decision)
    lines = [
        "# WP3-MULTI-CAND-v2 Search Report",
        "",
        f"**Status:** {results['status']}",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        f"**Publication gate:** {gate['PUBLICATION_GATE']}",
        "",
        f"**Interpretation authorization:** {gate['INTERPRETATION_AUTHORIZATION']}",
        "",
        "## Bounded Decision",
        "",
    ]
    if null_result:
        lines.extend(
            [
                "The frozen physical-quotient Reynolds library contains no training-eligible direction after the exact zero identities and known angular-momentum-squared direction are removed.",
                "",
                f"- Declared columns: {search['feature_count']}",
                f"- Exact structural-zero columns: {search['structural_zero_feature_count']}",
                f"- Active columns: {search['active_feature_count']}",
                f"- Observable quotient rank: {search['observable_value_rank']}",
                f"- Exact known-module rank removed: {search['exact_known_module_rank']}",
                f"- Smallest generalized singular value: `{certificate['smallest_generalized_singular_value']:.12e}`",
                f"- Backend-guarded lower bound: `{certificate['backend_guarded_lower_bound']:.12e}`",
                f"- Candidate threshold: `{certificate['candidate_training_threshold']:.12e}`",
                "",
                "This is a finite-library bounded null, not a no-integral or non-integrability theorem.",
            ]
        )
    else:
        lines.extend(
            [
                f"The spectral decision contains {candidate_count} unresolved candidate subspace(s).",
                "",
                "No candidate expression is interpreted or reported. Candidate resolution must be separately specified and frozen before reserve execution.",
            ]
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
            "## Evidence Boundary",
            "",
            spec["evidence_boundary"],
            "",
            "## Integrity",
            "",
            f"- Evidence commit: `{evidence_commit}`",
            f"- Search lock: `{lock['lock_sha256']}`",
            f"- Results SHA-256: `{sha256_file(args.results)}`",
            f"- Publication gate SHA-256: `{sha256_file(args.gate)}`",
            "- Publication reserve: **SEALED_UNEXECUTED**",
            "",
        ]
    )
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print(
        f"finalized {lock['qualification_id']}: {results['status']}; "
        f"publication_gate={gate['PUBLICATION_GATE']}"
    )


if __name__ == "__main__":
    main()
