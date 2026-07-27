#!/usr/bin/env python
"""Freeze and seal the fail-closed WP6-DZ-FEAS-v2 qualification."""

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


CAMPAIGN = "WP6-DZ-FEAS-v2"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp6-dz-feas-v2"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
PROTOCOL = CAMPAIGN_ROOT / "constructive_protocol.json"
REFERENCE = CAMPAIGN_ROOT / "reference/barycentric_reference.py"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_specification_lock.json"
)
SEARCH_LEDGER = CAMPAIGN_ROOT / "search/search_ledger.json"
QUALIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_qualification_lock.json"
)
CANDIDATE_LEDGER = CAMPAIGN_ROOT / "candidates/candidate_ledger.json"
RESULTS = CAMPAIGN_ROOT / "results/qualification_results.json"
RECORD = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_qualification_record.json"
REPORT = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_qualification_report.md"
EXPECTED_SYSTEM_COUNT = 11700


def _valid_signature(
    payload: dict[str, Any],
    signature_field: str,
) -> bool:
    unsigned = dict(payload)
    signature = unsigned.pop(signature_field, None)
    return signature == sha256_bytes(canonical_json(unsigned))


def _verify_specification_lock() -> dict[str, Any]:
    lock = load_json(SPECIFICATION_LOCK)
    if not _valid_signature(lock, "specification_lock_sha256"):
        raise RuntimeError("specification lock signature is invalid")
    if (
        lock.get("campaign") != CAMPAIGN
        or lock.get("lock_type") != "pre_constructive_search_specification"
        or lock.get("spec_sha256") != sha256_file(SPEC)
        or lock.get("protocol_sha256") != sha256_file(PROTOCOL)
        or lock.get("search_ledger_present_at_lock") is not False
        or lock.get("qualification_outputs_present_at_lock") is not False
    ):
        raise RuntimeError("specification lock does not match v2")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    return lock


def _verify_search_ledger(
    specification_lock: dict[str, Any],
) -> dict[str, Any]:
    ledger = load_json(SEARCH_LEDGER)
    if not _valid_signature(ledger, "search_payload_sha256"):
        raise RuntimeError("search ledger signature is invalid")
    if (
        ledger.get("campaign") != CAMPAIGN
        or ledger.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or ledger.get("spec_sha256") != sha256_file(SPEC)
        or ledger.get("protocol_sha256") != sha256_file(PROTOCOL)
        or ledger.get("reference_sha256") != sha256_file(REFERENCE)
        or ledger.get("expected_system_count") != EXPECTED_SYSTEM_COUNT
        or not all(ledger.get("reference_checks", {}).values())
    ):
        raise RuntimeError("search ledger does not match frozen inputs")

    records = ledger["records"]
    expected_ids = [
        f"S{index:05d}" for index in range(1, len(records) + 1)
    ]
    observed_ids = [record["system_id"] for record in records]
    if observed_ids != expected_ids:
        raise RuntimeError("search records are not a contiguous locked prefix")

    statuses = ("UNIT_IDEAL", "NON_UNIT_IDEAL", "TIMEOUT", "ERROR")
    recomputed = {
        status: sum(record["status"] == status for record in records)
        for status in statuses
    }
    if (
        ledger.get("executed_system_count") != len(records)
        or ledger.get("status_counts") != recomputed
        or sum(recomputed.values()) != len(records)
    ):
        raise RuntimeError("search ledger counts are inconsistent")

    complete = (
        len(records) == EXPECTED_SYSTEM_COUNT
        and ledger.get("abort_reason") is None
        and recomputed["TIMEOUT"] == 0
        and recomputed["ERROR"] == 0
    )
    expected_status = "COMPLETE" if complete else "INCOMPLETE"
    if ledger.get("search_status") != expected_status:
        raise RuntimeError("search status does not follow the locked policy")
    return ledger


def _unresolved(ledger: dict[str, Any]) -> dict[str, list[str]]:
    timeouts = [
        record["system_id"]
        for record in ledger["records"]
        if record["status"] == "TIMEOUT"
    ]
    errors = [
        record["system_id"]
        for record in ledger["records"]
        if record["status"] == "ERROR"
    ]
    missing = [
        f"S{index:05d}"
        for index in range(
            ledger["executed_system_count"] + 1,
            EXPECTED_SYSTEM_COUNT + 1,
        )
    ]
    return {
        "timeout_system_ids": timeouts,
        "error_system_ids": errors,
        "unexecuted_system_ids": missing,
    }


def freeze() -> None:
    if QUALIFICATION_LOCK.exists():
        raise RuntimeError("refusing to overwrite qualification lock")
    for output in (CANDIDATE_LEDGER, RESULTS, RECORD, REPORT):
        if output.exists():
            raise RuntimeError(f"qualification output already exists: {output}")
    require_clean_worktree(REPO_ROOT)

    specification_lock = _verify_specification_lock()
    ledger = _verify_search_ledger(specification_lock)
    unresolved = _unresolved(ledger)
    if ledger["search_status"] != "INCOMPLETE":
        raise RuntimeError("this freeze path is only for the observed v2 result")

    scopes = (
        "notes/wp6-dz-feas-v2-plan.md",
        "src/python/wp6_dz_feas_v2",
        "tests/wp6_dz_feas_v2",
        "validation-external/qualification_tools.py",
        "validation-external/wp6-dz-feas-v2",
    )
    files = tracked_files(REPO_ROOT, scopes)
    required = {
        SPEC.resolve(),
        PROTOCOL.resolve(),
        REFERENCE.resolve(),
        SPECIFICATION_LOCK.resolve(),
        SEARCH_LEDGER.resolve(),
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
        "lock_type": "post_search_fail_closed_qualification",
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(REPO_ROOT, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "qualification_outputs_absent_at_freeze": True,
        "wp6_dz_mr_campaign_absent_at_freeze": not (
            VALIDATION_ROOT / "wp6-dz-mr-v1"
        ).exists(),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "spec_sha256": sha256_file(SPEC),
        "protocol_sha256": sha256_file(PROTOCOL),
        "reference_sha256": sha256_file(REFERENCE),
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "search_payload_sha256": ledger["search_payload_sha256"],
        "search_summary": {
            "search_status": ledger["search_status"],
            "expected_system_count": EXPECTED_SYSTEM_COUNT,
            "executed_system_count": ledger["executed_system_count"],
            "status_counts": ledger["status_counts"],
            "abort_reason": ledger["abort_reason"],
            "unresolved_system_count": sum(
                len(system_ids) for system_ids in unresolved.values()
            ),
        },
        "code_snapshot_sha256": snapshot_sha256,
        "runtime": runtime,
        "file_hashes": dict(sorted(file_hashes.items())),
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(QUALIFICATION_LOCK, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


def _signed_payload(
    payload: dict[str, Any],
    signature_field: str,
) -> dict[str, Any]:
    signed = dict(payload)
    signed[signature_field] = sha256_bytes(canonical_json(payload))
    return signed


def seal() -> None:
    for output in (CANDIDATE_LEDGER, RESULTS, RECORD, REPORT):
        if output.exists():
            raise RuntimeError(f"refusing to overwrite output: {output}")
    require_clean_worktree(REPO_ROOT)

    lock = verify_lock(
        QUALIFICATION_LOCK,
        REPO_ROOT,
        expected_prefix=CAMPAIGN,
    )
    specification_lock = _verify_specification_lock()
    ledger = _verify_search_ledger(specification_lock)
    if (
        sha256_file(SEARCH_LEDGER) != lock["search_ledger_sha256"]
        or ledger["search_payload_sha256"] != lock["search_payload_sha256"]
    ):
        raise RuntimeError("qualification lock and search ledger disagree")

    unresolved = _unresolved(ledger)
    unresolved_count = sum(len(system_ids) for system_ids in unresolved.values())
    non_unit_ids = [
        record["system_id"]
        for record in ledger["records"]
        if record["status"] == "NON_UNIT_IDEAL"
    ]
    if (
        ledger["search_status"] != "INCOMPLETE"
        or unresolved_count == 0
        or non_unit_ids
    ):
        raise RuntimeError("observed v2 outcome is not the locked fail-closed case")
    if (VALIDATION_ROOT / "wp6-dz-mr-v1").exists():
        raise RuntimeError("WP6-DZ-MR-v1 is prohibited by an incomplete result")

    generated_utc = utc_now()
    candidate_payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "status": "SEARCH_INCOMPLETE",
        "generated_utc": generated_utc,
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "candidate_count": 0,
        "qualifying_candidate_ids": [],
        "non_unit_system_ids": non_unit_ids,
        **unresolved,
        "unresolved_system_count": unresolved_count,
        "proposed_outcome": "INCOMPLETE",
        "mr_promotion_authorized": False,
    }
    candidate_ledger = _signed_payload(
        candidate_payload,
        "candidate_payload_sha256",
    )
    atomic_write_json(CANDIDATE_LEDGER, candidate_ledger)

    gates = [
        {"name": "specification_lock_valid", "passed": True},
        {"name": "qualification_lock_valid", "passed": True},
        {"name": "production_reference_exact_agreement", "passed": True},
        {
            "name": "all_11700_systems_executed",
            "passed": ledger["executed_system_count"] == EXPECTED_SYSTEM_COUNT,
        },
        {
            "name": "all_executed_systems_exactly_decided",
            "passed": (
                ledger["status_counts"]["TIMEOUT"] == 0
                and ledger["status_counts"]["ERROR"] == 0
            ),
        },
        {"name": "all_non_unit_ideals_audited", "passed": not non_unit_ids},
        {"name": "wp6_dz_mr_v1_absent", "passed": True},
    ]
    authorized_claim = (
        "WP6-DZ-FEAS-v2 executed 11,689 of 11,700 locked exact coefficient "
        "ideals. Of those, 11,549 were proved unit ideals, 140 timed out, "
        "and no resolved ideal was non-unit. Eleven systems were not executed "
        "before the aggregate cap. The campaign is INCOMPLETE."
    )
    results_payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "generated_utc": generated_utc,
        "outcome": "INCOMPLETE",
        "qualification_gate_status": "FAIL_CLOSED",
        "authorized_claim": authorized_claim,
        "claim_boundary": (
            "This record is an operationally complete account of an incomplete "
            "finite search. It does not authorize a bounded null result, witness "
            "promotion, nonexistence, nonintegrability, or Morales-Ramis claims."
        ),
        "search_summary": lock["search_summary"],
        "unresolved_system_count": unresolved_count,
        "candidate_count": 0,
        "qualifying_candidate_ids": [],
        "gates": gates,
        "mr_promotion_authorized": False,
        "mr_promotion_rule": (
            "Only a signed QUALIFIED_WITNESS record naming one frozen full-system "
            "witness may create WP6-DZ-MR-v1."
        ),
        "prohibited_claims": {
            "BOUNDED_NULL": "The 11,700-system search found no graph.",
            "NONEXISTENCE": "No suitable double-zero algebraic orbit exists.",
            "NONINTEGRABILITY": (
                "The planar Newtonian three-body problem is nonintegrable on "
                "(H,C)=(0,0)."
            ),
            "MR": "A Morales-Ramis or Ziglin obstruction has been proved.",
        },
        "qualification_lock_sha256": lock["lock_sha256"],
        "search_ledger_sha256": sha256_file(SEARCH_LEDGER),
        "candidate_ledger_sha256": sha256_file(CANDIDATE_LEDGER),
    }
    results = _signed_payload(results_payload, "results_payload_sha256")
    atomic_write_json(RESULTS, results)

    record_payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "generated_utc": generated_utc,
        "status": "INCOMPLETE",
        "qualification_gate_status": "FAIL_CLOSED",
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
        "results_sha256": sha256_file(RESULTS),
        "search_summary": lock["search_summary"],
        "unresolved": unresolved,
        "candidate_count": 0,
        "qualifying_candidate_ids": [],
        "mr_promotion_authorized": False,
    }
    record = _signed_payload(record_payload, "record_payload_sha256")
    atomic_write_json(RECORD, record)

    report = f"""# WP6-DZ-FEAS-v2 Qualification Report

**Qualification gate:** `FAIL_CLOSED`

**Outcome:** `INCOMPLETE`

**Qualification ID:** `{lock["qualification_id"]}`

## Authorized Claim

{authorized_claim}

## Search Result

- Locked systems: {EXPECTED_SYSTEM_COUNT:,}
- Executed systems: {ledger["executed_system_count"]:,}
- Exact unit ideals: {ledger["status_counts"]["UNIT_IDEAL"]:,}
- Non-unit ideals: {ledger["status_counts"]["NON_UNIT_IDEAL"]:,}
- Timed-out ideals: {ledger["status_counts"]["TIMEOUT"]:,}
- Search errors: {ledger["status_counts"]["ERROR"]:,}
- Unexecuted systems: {len(unresolved["unexecuted_system_ids"]):,}
- Abort reason: `{ledger["abort_reason"]}`
- Peak memory: {ledger["peak_memory_megabytes"]:.3f} MiB

All 140 timeouts occurred in the `PHI-BOTH-SQ` cover. No resolved system
produced a candidate branch. These observations define a solver-remediation
target; they do not establish a bounded null result.

## Promotion

`WP6-DZ-MR-v1` remains prohibited. An `INCOMPLETE` record cannot promote a
witness or support a Morales-Ramis or Ziglin conclusion.

## Integrity

- Evidence commit: `{lock["base_git_commit"]}`
- Qualification lock: `{lock["lock_sha256"]}`
- Search ledger SHA-256: `{sha256_file(SEARCH_LEDGER)}`
- Search payload SHA-256: `{ledger["search_payload_sha256"]}`
- Candidate ledger SHA-256: `{sha256_file(CANDIDATE_LEDGER)}`
- Results SHA-256: `{sha256_file(RESULTS)}`
- Record payload SHA-256: `{record["record_payload_sha256"]}`
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="ascii")
    print(json.dumps(record, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "seal"))
    arguments = parser.parse_args()
    if arguments.action == "freeze":
        freeze()
    else:
        seal()


if __name__ == "__main__":
    main()
