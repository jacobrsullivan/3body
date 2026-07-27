#!/usr/bin/env python
"""Audit, freeze, and seal the WP6-DZ-FEAS-v3 qualification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    git_output,
    load_json,
    require_clean_worktree,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    tracked_files,
    utc_now,
    verify_lock,
)


CAMPAIGN = "WP6-DZ-FEAS-v3"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp6-dz-feas-v3"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
PROTOCOL = CAMPAIGN_ROOT / "constructive_protocol.json"
SEEDS = CAMPAIGN_ROOT / "sources/seed_manifest.json"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_specification_lock.json"
)
SEARCH_LEDGER = CAMPAIGN_ROOT / "search/search_ledger.json"
CANDIDATE_LEDGER = CAMPAIGN_ROOT / "candidates/candidate_ledger.json"
AUDIT_REPORT = CAMPAIGN_ROOT / "proof/WP6-DZ-FEAS-v3-audit.md"
QUALIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_qualification_lock.json"
)
RESULTS = CAMPAIGN_ROOT / "results/qualification_results.json"
RECORD = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_qualification_record.json"
REPORT = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_qualification_report.md"
V2_CANDIDATES = (
    VALIDATION_ROOT / "wp6-dz-feas-v2/candidates/candidate_ledger.json"
)
EXPECTED_SYSTEM_COUNT = 11700
EXPECTED_SEARCH_LEDGER_SHA256 = (
    "145a2e91cb2f22628f698327effab63ac26527f4f32e96a33c833a594979f8a5"
)


def _valid_signature(
    payload: dict[str, Any],
    signature_field: str,
) -> bool:
    unsigned = dict(payload)
    signature = unsigned.pop(signature_field, None)
    return signature == sha256_bytes(canonical_json(unsigned))


def _signed_payload(
    payload: dict[str, Any],
    signature_field: str,
) -> dict[str, Any]:
    signed = dict(payload)
    signed[signature_field] = sha256_bytes(canonical_json(payload))
    return signed


def _verify_specification_lock() -> dict[str, Any]:
    lock = load_json(SPECIFICATION_LOCK)
    if (
        not _valid_signature(lock, "specification_lock_sha256")
        or lock.get("campaign") != CAMPAIGN
        or lock.get("spec_sha256") != sha256_file(SPEC)
        or lock.get("protocol_sha256") != sha256_file(PROTOCOL)
        or lock.get("seed_manifest_sha256") != sha256_file(SEEDS)
    ):
        raise RuntimeError("v3 specification lock is invalid")
    for relative, expected in lock["predecessor_artifact_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"frozen predecessor changed: {relative}")
    return lock


def _v2_unresolved_ids() -> set[str]:
    candidate = load_json(V2_CANDIDATES)
    if (
        not _valid_signature(candidate, "candidate_payload_sha256")
        or candidate.get("unresolved_system_count") != 151
    ):
        raise RuntimeError("v2 unresolved ledger is invalid")
    return set(candidate["timeout_system_ids"]) | set(
        candidate["unexecuted_system_ids"]
    )


def _verify_search() -> tuple[dict[str, Any], dict[str, Any]]:
    specification_lock = _verify_specification_lock()
    ledger = load_json(SEARCH_LEDGER)
    if (
        sha256_file(SEARCH_LEDGER) != EXPECTED_SEARCH_LEDGER_SHA256
        or not _valid_signature(ledger, "search_payload_sha256")
        or ledger.get("campaign") != CAMPAIGN
        or ledger.get("search_status") != "COMPLETE"
        or ledger.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or ledger.get("spec_sha256") != sha256_file(SPEC)
        or ledger.get("protocol_sha256") != sha256_file(PROTOCOL)
        or ledger.get("seed_manifest_sha256") != sha256_file(SEEDS)
        or ledger.get("expected_system_count") != EXPECTED_SYSTEM_COUNT
        or ledger.get("executed_system_count") != EXPECTED_SYSTEM_COUNT
        or ledger.get("abort_reason") is not None
        or not all(ledger.get("runtime_checks", {}).values())
        or not all(ledger.get("reference_checks", {}).values())
    ):
        raise RuntimeError("v3 search ledger is invalid")

    expected_status_counts = {
        "UNIT_IDEAL": EXPECTED_SYSTEM_COUNT,
        "NON_UNIT_IDEAL": 0,
        "TIMEOUT": 0,
        "ERROR": 0,
        "DISAGREEMENT": 0,
    }
    if ledger.get("status_counts") != expected_status_counts:
        raise RuntimeError("v3 search did not close every ideal as unit")

    records = ledger["records"]
    expected_ids = [
        f"S{index:05d}" for index in range(1, EXPECTED_SYSTEM_COUNT + 1)
    ]
    if [record["system_id"] for record in records] != expected_ids:
        raise RuntimeError("v3 records are not the full locked enumeration")
    for record in records:
        audits = record["stage_audits"]
        if (
            record["status"] != "UNIT_IDEAL"
            or not audits
            or not all(audit["algorithms_agree"] for audit in audits)
            or audits[-1]["primary_is_unit"] is not True
            or audits[-1]["verification_is_unit"] is not True
            or not audits[-1]["equation_sha256"]
            or not audits[-1]["primary_basis_sha256"]
            or not audits[-1]["verification_basis_sha256"]
        ):
            raise RuntimeError(
                f"invalid terminal ideal audit: {record['system_id']}"
            )

    v2_ids = _v2_unresolved_ids()
    decisions = ledger["v2_unresolved_decisions"]
    if (
        set(decisions) != v2_ids
        or len(decisions) != 151
        or set(decisions.values()) != {"UNIT_IDEAL"}
    ):
        raise RuntimeError("v3 did not close every v2 unresolved system")

    stage_counts = {
        stage: sum(record["decision_stage"] == stage for record in records)
        for stage in ("ENERGY", "ENERGY_AND_V", "FULL")
    }
    if stage_counts != {
        "ENERGY": 11687,
        "ENERGY_AND_V": 13,
        "FULL": 0,
    }:
        raise RuntimeError(f"unexpected v3 stage distribution: {stage_counts}")
    details = {
        "status_counts": expected_status_counts,
        "stage_counts": stage_counts,
        "energy_and_v_system_ids": [
            record["system_id"]
            for record in records
            if record["decision_stage"] == "ENERGY_AND_V"
        ],
        "v2_unresolved_count": len(decisions),
        "v2_unresolved_status": "ALL_UNIT_IDEAL",
    }
    return ledger, details


def audit() -> None:
    for output in (CANDIDATE_LEDGER, AUDIT_REPORT):
        if output.exists():
            raise RuntimeError(f"refusing to overwrite audit output: {output}")
    require_clean_worktree(REPO_ROOT)
    ledger, details = _verify_search()
    generated_utc = utc_now()
    candidate_payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "status": "SEARCH_AND_BRANCH_AUDIT_COMPLETE",
        "generated_utc": generated_utc,
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "search_payload_sha256": ledger["search_payload_sha256"],
        "expected_system_count": EXPECTED_SYSTEM_COUNT,
        "status_counts": details["status_counts"],
        "stage_counts": details["stage_counts"],
        "energy_and_v_system_ids": details["energy_and_v_system_ids"],
        "v2_unresolved_count": details["v2_unresolved_count"],
        "v2_unresolved_status": details["v2_unresolved_status"],
        "candidate_count": 0,
        "non_unit_system_ids": [],
        "qualifying_candidate_ids": [],
        "branch_audit_status": "VACUOUS_NO_NON_UNIT_IDEALS",
        "proposed_outcome": "COMPLETE_BOUNDED_NULL_RESULT",
        "mr_promotion_authorized": False,
    }
    candidate = _signed_payload(
        candidate_payload,
        "candidate_payload_sha256",
    )
    atomic_write_json(CANDIDATE_LEDGER, candidate)

    system_lines = "\n".join(
        f"- `{system_id}`"
        for system_id in details["energy_and_v_system_ids"]
    )
    report = f"""# WP6-DZ-FEAS-v3 Audit

## Frozen Scope

The campaign repeated the exact 11,700-system mathematical enumeration from
WP6-DZ-FEAS-v2. It changed only the pre-registered exact equation
construction, localization, term order, dual-algorithm verification, and
resource caps.

## Exact Controls

- Specification lock: `{ledger["specification_lock_sha256"]}`
- Search ledger SHA-256: `{sha256_file(SEARCH_LEDGER)}`
- Search payload SHA-256: `{ledger["search_payload_sha256"]}`
- Source-disjoint reference checks: all pass
- Runtime checks: all pass
- Exact algorithms: F5B grevlex and Buchberger grevlex over `QQ`
- Algorithm disagreements: 0

## Ideal Results

- Systems executed: 11,700/11,700
- Unit ideals: 11,700
- Non-unit ideals: 0
- Timeouts: 0
- Errors: 0
- Energy-stage decisions: 11,687
- Energy-and-v-stage decisions: 13
- Full-stage decisions: 0

The 13 systems requiring the vector residual were:

{system_lines}

## V2 Gap Closure

All 140 v2 timeouts and all 11 v2 unexecuted systems were rerun in the full
v3 enumeration. Every one of those 151 systems is an exact dual-algorithm
unit ideal.

## Candidate And Branch Audit

No non-unit ideal exists in the frozen enumeration, so there is no
coefficient branch or sentinel candidate to promote. The branch audit is
vacuously complete and the candidate count is zero.

## Qualified Interpretation

The evidence supports `COMPLETE_BOUNDED_NULL_RESULT`: no graph in the frozen
four-cover, one- and two-term Laurent, thirteen-sentinel library can become
a W1-W12 arbitrary-positive-mass witness.

It does not prove that no suitable algebraic orbit exists outside that
library, does not prove nonintegrability on `(H,C)=(0,0)`, and does not
authorize `WP6-DZ-MR-v1`.
"""
    AUDIT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_REPORT.write_text(report, encoding="ascii")
    print(json.dumps(candidate, indent=2, sort_keys=True))


def _verify_candidate() -> dict[str, Any]:
    candidate = load_json(CANDIDATE_LEDGER)
    ledger, details = _verify_search()
    if (
        not _valid_signature(candidate, "candidate_payload_sha256")
        or candidate.get("campaign") != CAMPAIGN
        or candidate.get("status") != "SEARCH_AND_BRANCH_AUDIT_COMPLETE"
        or candidate.get("search_ledger_sha256")
        != sha256_file(SEARCH_LEDGER)
        or candidate.get("search_payload_sha256")
        != ledger["search_payload_sha256"]
        or candidate.get("status_counts") != details["status_counts"]
        or candidate.get("stage_counts") != details["stage_counts"]
        or candidate.get("candidate_count") != 0
        or candidate.get("non_unit_system_ids") != []
        or candidate.get("qualifying_candidate_ids") != []
        or candidate.get("branch_audit_status")
        != "VACUOUS_NO_NON_UNIT_IDEALS"
        or candidate.get("proposed_outcome")
        != "COMPLETE_BOUNDED_NULL_RESULT"
        or candidate.get("mr_promotion_authorized") is not False
    ):
        raise RuntimeError("v3 candidate audit is invalid")
    return candidate


def freeze() -> None:
    if QUALIFICATION_LOCK.exists():
        raise RuntimeError("refusing to overwrite qualification lock")
    for output in (RESULTS, RECORD, REPORT):
        if output.exists():
            raise RuntimeError(f"qualification output already exists: {output}")
    require_clean_worktree(REPO_ROOT)
    specification_lock = _verify_specification_lock()
    ledger, details = _verify_search()
    candidate = _verify_candidate()
    if not AUDIT_REPORT.is_file():
        raise RuntimeError("human-readable branch audit is missing")
    if (VALIDATION_ROOT / "wp6-dz-mr-v1").exists():
        raise RuntimeError("WP6-DZ-MR-v1 is not authorized")

    scopes = (
        "notes/wp6-dz-feas-v3-plan.md",
        "src/python/wp6_dz_feas_v3",
        "tests/wp6_dz_feas_v3",
        "validation-external/qualification_tools.py",
        "validation-external/wp6-dz-feas-v3",
    )
    files = tracked_files(REPO_ROOT, scopes)
    required = {
        SPEC.resolve(),
        PROTOCOL.resolve(),
        SEEDS.resolve(),
        SPECIFICATION_LOCK.resolve(),
        SEARCH_LEDGER.resolve(),
        CANDIDATE_LEDGER.resolve(),
        AUDIT_REPORT.resolve(),
        Path(__file__).resolve(),
    }
    if not required.issubset(set(files)):
        omitted = sorted(str(path) for path in required.difference(files))
        raise RuntimeError(f"qualification freeze omits inputs: {omitted}")
    file_hashes = {
        path.relative_to(REPO_ROOT).as_posix(): sha256_file(path)
        for path in files
    }
    snapshot_sha256 = sha256_bytes(canonical_json(file_hashes))
    runtime = runtime_fingerprint()
    runtime["sympy"] = __import__("sympy").__version__
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": f"{CAMPAIGN}-{snapshot_sha256[:12]}",
        "lock_type": "post_search_bounded_null_qualification",
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(REPO_ROOT, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "qualification_outputs_absent_at_freeze": True,
        "wp6_dz_mr_campaign_absent_at_freeze": True,
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "spec_sha256": sha256_file(SPEC),
        "protocol_sha256": sha256_file(PROTOCOL),
        "seed_manifest_sha256": sha256_file(SEEDS),
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "search_payload_sha256": ledger["search_payload_sha256"],
        "candidate_ledger_sha256": sha256_file(CANDIDATE_LEDGER),
        "candidate_payload_sha256": candidate["candidate_payload_sha256"],
        "audit_report_sha256": sha256_file(AUDIT_REPORT),
        "search_summary": {
            "search_status": ledger["search_status"],
            "expected_system_count": EXPECTED_SYSTEM_COUNT,
            "executed_system_count": ledger["executed_system_count"],
            "status_counts": ledger["status_counts"],
            "stage_counts": details["stage_counts"],
            "v2_unresolved_count": details["v2_unresolved_count"],
            "candidate_count": candidate["candidate_count"],
        },
        "code_snapshot_sha256": snapshot_sha256,
        "runtime": runtime,
        "file_hashes": dict(sorted(file_hashes.items())),
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(QUALIFICATION_LOCK, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


def seal() -> None:
    for output in (RESULTS, RECORD, REPORT):
        if output.exists():
            raise RuntimeError(f"refusing to overwrite output: {output}")
    require_clean_worktree(REPO_ROOT)
    lock = verify_lock(
        QUALIFICATION_LOCK,
        REPO_ROOT,
        expected_prefix=CAMPAIGN,
    )
    specification_lock = _verify_specification_lock()
    ledger, details = _verify_search()
    candidate = _verify_candidate()
    if (
        lock["search_ledger_sha256"] != sha256_file(SEARCH_LEDGER)
        or lock["candidate_ledger_sha256"] != sha256_file(CANDIDATE_LEDGER)
        or lock["audit_report_sha256"] != sha256_file(AUDIT_REPORT)
    ):
        raise RuntimeError("qualification lock and audited evidence disagree")
    if (VALIDATION_ROOT / "wp6-dz-mr-v1").exists():
        raise RuntimeError("WP6-DZ-MR-v1 is not authorized")

    generated_utc = utc_now()
    authorized_claim = (
        "Within the four frozen v2 shape covers, exact one- and two-term "
        "Laurent supports with exponents -2 through 2, and thirteen exact "
        "mass/order sentinels, all 11,700 saturated coefficient ideals are "
        "dual-exact unit ideals. This finite library contains no graph that "
        "can extend to a W1-W12 arbitrary-positive-mass witness."
    )
    gates = [
        {"name": "specification_lock_valid", "passed": True},
        {"name": "qualification_lock_valid", "passed": True},
        {"name": "source_disjoint_reference_checks_pass", "passed": True},
        {"name": "all_11700_systems_executed", "passed": True},
        {"name": "all_11700_systems_dual_exact_unit", "passed": True},
        {"name": "all_151_v2_gaps_closed", "passed": True},
        {"name": "all_non_unit_branches_audited", "passed": True},
        {"name": "candidate_count_zero", "passed": True},
        {"name": "wp6_dz_mr_v1_absent", "passed": True},
    ]
    results_payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "generated_utc": generated_utc,
        "outcome": "COMPLETE_BOUNDED_NULL_RESULT",
        "qualification_gate_status": "PASS",
        "authorized_claim": authorized_claim,
        "claim_boundary": (
            "The result exhausts only the frozen 11,700 graph ideals. It is "
            "not a nonexistence theorem for algebraic double-zero orbits, a "
            "nonintegrability theorem, or a Morales-Ramis obstruction."
        ),
        "search_summary": lock["search_summary"],
        "energy_and_v_system_ids": details["energy_and_v_system_ids"],
        "candidate_count": 0,
        "qualifying_candidate_ids": [],
        "gates": gates,
        "mr_promotion_authorized": False,
        "mr_promotion_rule": (
            "Only a signed QUALIFIED_WITNESS record naming one frozen "
            "full-system witness may create WP6-DZ-MR-v1."
        ),
        "prohibited_claims": {
            "NONEXISTENCE": (
                "No explicit nonhomothetic algebraic H=C=0 orbit exists."
            ),
            "NONINTEGRABILITY": (
                "The planar Newtonian three-body problem is nonintegrable "
                "on (H,C)=(0,0)."
            ),
            "MR": "A Morales-Ramis or Ziglin obstruction has been proved.",
            "SCOPE": (
                "The search covers implicit curves, larger supports, other "
                "covers, or transcendental trajectories."
            ),
        },
        "qualification_lock_sha256": lock["lock_sha256"],
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "candidate_ledger_sha256": sha256_file(CANDIDATE_LEDGER),
        "audit_report_sha256": sha256_file(AUDIT_REPORT),
    }
    results = _signed_payload(results_payload, "results_payload_sha256")
    atomic_write_json(RESULTS, results)

    record_payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "generated_utc": generated_utc,
        "status": "COMPLETE_BOUNDED_NULL_RESULT",
        "qualification_gate_status": "PASS",
        "authorized_claim": authorized_claim,
        "evidence_git_commit": lock["base_git_commit"],
        "qualification_lock_git_commit": git_output(
            REPO_ROOT, "rev-parse", "HEAD"
        ),
        "qualification_lock_sha256": lock["lock_sha256"],
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "candidate_ledger_sha256": sha256_file(CANDIDATE_LEDGER),
        "audit_report_sha256": sha256_file(AUDIT_REPORT),
        "results_sha256": sha256_file(RESULTS),
        "search_summary": lock["search_summary"],
        "candidate_count": 0,
        "qualifying_candidate_ids": [],
        "mr_promotion_authorized": False,
    }
    record = _signed_payload(record_payload, "record_payload_sha256")
    atomic_write_json(RECORD, record)

    report = f"""# WP6-DZ-FEAS-v3 Qualification Report

**Qualification gate:** `PASS`

**Outcome:** `COMPLETE_BOUNDED_NULL_RESULT`

**Qualification ID:** `{lock["qualification_id"]}`

## Authorized Claim

{authorized_claim}

## Evidence

- Systems executed: 11,700/11,700
- Exact dual-algorithm unit ideals: 11,700
- Non-unit ideals: 0
- Timeouts, errors, or disagreements: 0
- Energy-stage decisions: 11,687
- Energy-and-v-stage decisions: 13
- V2 unresolved systems closed: 151/151
- Candidate branches: 0
- Peak campaign memory: {ledger["peak_memory_megabytes"]:.3f} MiB
- Campaign elapsed time: {ledger["elapsed_seconds"]:.3f} seconds

## Promotion

`WP6-DZ-MR-v1` remains prohibited. A bounded null result does not supply the
particular orbit required for a candidate-specific Morales-Ramis or Ziglin
analysis.

## Claim Boundary

The result exhausts only the frozen finite graph library. It does not prove
that no suitable algebraic orbit exists outside that library and does not
prove nonintegrability on `(H,C)=(0,0)`.

## Integrity

- Evidence commit: `{lock["base_git_commit"]}`
- Qualification lock: `{lock["lock_sha256"]}`
- Search ledger SHA-256: `{sha256_file(SEARCH_LEDGER)}`
- Search payload SHA-256: `{ledger["search_payload_sha256"]}`
- Candidate ledger SHA-256: `{sha256_file(CANDIDATE_LEDGER)}`
- Audit report SHA-256: `{sha256_file(AUDIT_REPORT)}`
- Results SHA-256: `{sha256_file(RESULTS)}`
- Record payload SHA-256: `{record["record_payload_sha256"]}`
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="ascii")
    print(json.dumps(record, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("audit", "freeze", "seal"))
    arguments = parser.parse_args()
    if arguments.action == "audit":
        audit()
    elif arguments.action == "freeze":
        freeze()
    else:
        seal()


if __name__ == "__main__":
    main()
