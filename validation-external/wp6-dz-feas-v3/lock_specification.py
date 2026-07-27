#!/usr/bin/env python
"""Create the WP6-DZ-FEAS-v3 pre-implementation specification lock."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    utc_now,
)


CAMPAIGN = "WP6-DZ-FEAS-v3"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp6-dz-feas-v3"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
PROTOCOL = CAMPAIGN_ROOT / "constructive_protocol.json"
SEEDS = CAMPAIGN_ROOT / "sources/seed_manifest.json"
PLAN = REPO_ROOT / "notes/wp6-dz-feas-v3-plan.md"
OUTPUT = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_specification_lock.json"


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=REPO_ROOT, text=True
    ).strip()


def _valid_signature(
    payload: dict[str, Any],
    signature_field: str,
) -> bool:
    unsigned = dict(payload)
    signature = unsigned.pop(signature_field, None)
    return signature == sha256_bytes(canonical_json(unsigned))


def main() -> None:
    if _git("status", "--short"):
        raise RuntimeError("pre-implementation lock requires a clean worktree")
    if OUTPUT.exists():
        raise RuntimeError("refusing to overwrite specification lock")

    forbidden = (
        REPO_ROOT / "src/python/wp6_dz_feas_v3",
        REPO_ROOT / "tests/wp6_dz_feas_v3",
        CAMPAIGN_ROOT / "reference",
        CAMPAIGN_ROOT / "run_constructive_search.py",
        CAMPAIGN_ROOT / "search/search_ledger.json",
        CAMPAIGN_ROOT / "candidates/candidate_ledger.json",
        CAMPAIGN_ROOT / "qualification.py",
        CAMPAIGN_ROOT / "results/qualification_results.json",
        CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_qualification_lock.json",
        CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_qualification_record.json",
        VALIDATION_ROOT / "wp6-dz-mr-v1",
    )
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise RuntimeError(f"v3 implementation artifacts already exist: {present}")

    spec = load_json(SPEC)
    protocol = load_json(PROTOCOL)
    seeds = load_json(SEEDS)
    if (
        spec.get("campaign") != CAMPAIGN
        or protocol.get("campaign") != CAMPAIGN
        or seeds.get("campaign") != CAMPAIGN
        or spec.get("specification_status")
        != "LOCK_BEFORE_IMPLEMENTATION_AND_SEARCH"
        or protocol.get("protocol_status")
        != "LOCK_BEFORE_IMPLEMENTATION_AND_SEARCH"
    ):
        raise RuntimeError("campaign inputs are not lockable")

    exponents = protocol["enumeration"]["support_exponents"]
    maximum_cardinality = protocol["enumeration"][
        "maximum_support_cardinality"
    ]
    support_count = sum(
        len(list(combinations(exponents, size)))
        for size in range(1, maximum_cardinality + 1)
    )
    cover_count = len(protocol["enumeration"]["shape_cover_ids"])
    mass_count = len(protocol["enumeration"]["mass_order_cases"])
    ideal_count = cover_count * support_count**2 * mass_count
    stop = spec["stop_rule"]
    if (
        len(spec["witness_requirements"]) != 12
        or support_count != 15
        or support_count != stop["support_count_per_variable"]
        or cover_count != stop["shape_cover_count"]
        or mass_count != stop["mass_order_case_count"]
        or ideal_count != stop["coefficient_ideal_count"]
        or ideal_count != protocol["enumeration"]["total_systems"]
        or protocol["enumeration"]["systems_per_mass_case"]
        != cover_count * support_count**2
    ):
        raise RuntimeError("v3 protocol counts disagree")

    artifact_hashes: dict[str, str] = {}
    for artifact in seeds["artifacts"]:
        path = REPO_ROOT / artifact["path"]
        observed = sha256_file(path)
        if observed != artifact["sha256"]:
            raise RuntimeError(f"frozen v2 artifact changed: {artifact['path']}")
        artifact_hashes[artifact["path"]] = observed

    predecessor = spec["predecessor"]
    record = load_json(REPO_ROOT / predecessor["record_file"])
    if (
        sha256_file(REPO_ROOT / predecessor["qualification_lock_file"])
        != predecessor["qualification_lock_file_sha256"]
        or sha256_file(REPO_ROOT / predecessor["record_file"])
        != predecessor["record_file_sha256"]
        or sha256_file(REPO_ROOT / predecessor["results_file"])
        != predecessor["results_file_sha256"]
        or sha256_file(REPO_ROOT / predecessor["search_ledger_file"])
        != predecessor["search_ledger_file_sha256"]
        or not _valid_signature(record, "record_payload_sha256")
        or record.get("qualification_id") != predecessor["qualification_id"]
        or record.get("status") != predecessor["required_status"]
    ):
        raise RuntimeError("v2 predecessor qualification is invalid")

    search = load_json(REPO_ROOT / predecessor["search_ledger_file"])
    candidate = load_json(
        REPO_ROOT
        / "validation-external/wp6-dz-feas-v2/candidates/candidate_ledger.json"
    )
    observed = predecessor["observed"]
    if (
        not _valid_signature(search, "search_payload_sha256")
        or search.get("search_status") != "INCOMPLETE"
        or search.get("expected_system_count")
        != observed["expected_system_count"]
        or search.get("executed_system_count")
        != observed["executed_system_count"]
        or search.get("status_counts", {}).get("UNIT_IDEAL")
        != observed["unit_ideal_count"]
        or search.get("status_counts", {}).get("NON_UNIT_IDEAL")
        != observed["non_unit_ideal_count"]
        or search.get("status_counts", {}).get("TIMEOUT")
        != observed["timeout_count"]
        or search.get("status_counts", {}).get("ERROR")
        != observed["error_count"]
        or search.get("abort_reason") != observed["abort_reason"]
        or candidate.get("unresolved_system_count")
        != observed["unresolved_system_count"]
    ):
        raise RuntimeError("v2 unresolved-set evidence does not match v3 spec")

    unsigned = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "lock_type": "pre_implementation_constructive_search_specification",
        "locked_utc": utc_now(),
        "base_git_commit": _git("rev-parse", "HEAD"),
        "spec_path": SPEC.relative_to(REPO_ROOT).as_posix(),
        "spec_sha256": sha256_file(SPEC),
        "protocol_path": PROTOCOL.relative_to(REPO_ROOT).as_posix(),
        "protocol_sha256": sha256_file(PROTOCOL),
        "seed_manifest_path": SEEDS.relative_to(REPO_ROOT).as_posix(),
        "seed_manifest_sha256": sha256_file(SEEDS),
        "plan_sha256": sha256_file(PLAN),
        "predecessor_qualification_id": record["qualification_id"],
        "predecessor_record_payload_sha256": record[
            "record_payload_sha256"
        ],
        "predecessor_artifact_hashes": dict(sorted(artifact_hashes.items())),
        "locked_counts": {
            "witness_requirements": len(spec["witness_requirements"]),
            "shape_covers": cover_count,
            "support_exponents": len(exponents),
            "maximum_support_cardinality": maximum_cardinality,
            "supports_per_variable": support_count,
            "mass_order_cases": mass_count,
            "coefficient_ideals": ideal_count,
            "v2_unresolved_acceptance_count": stop[
                "v2_unresolved_acceptance_count"
            ],
            "per_system_timeout_seconds": stop[
                "per_system_timeout_seconds"
            ],
            "aggregate_compute_cap_seconds": stop[
                "aggregate_compute_cap_seconds"
            ],
            "memory_cap_megabytes": stop["memory_cap_megabytes"],
            "required_algorithms": stop["required_algorithms"],
        },
        "implementation_present_at_lock": False,
        "implementation_tests_present_at_lock": False,
        "constructive_search_started_at_lock": False,
        "search_ledger_present_at_lock": False,
        "candidate_ledger_present_at_lock": False,
        "qualification_outputs_present_at_lock": False,
        "wp6_dz_mr_campaign_present_at_lock": False,
    }
    payload = dict(unsigned)
    payload["specification_lock_sha256"] = sha256_bytes(
        canonical_json(unsigned)
    )
    atomic_write_json(OUTPUT, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
