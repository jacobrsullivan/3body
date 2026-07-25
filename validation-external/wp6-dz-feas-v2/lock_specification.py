#!/usr/bin/env python
"""Create the WP6-DZ-FEAS-v2 pre-search specification lock."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
import subprocess
import sys


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


CAMPAIGN = "WP6-DZ-FEAS-v2"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp6-dz-feas-v2"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
PROTOCOL = CAMPAIGN_ROOT / "constructive_protocol.json"
SEEDS = CAMPAIGN_ROOT / "sources/seed_manifest.json"
PLAN = REPO_ROOT / "notes/wp6-dz-feas-v2-plan.md"
OUTPUT = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_specification_lock.json"


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=REPO_ROOT, text=True
    ).strip()


def _signed_record_valid(record: dict[str, object]) -> bool:
    unsigned = dict(record)
    signature = unsigned.pop("record_payload_sha256", None)
    return signature == sha256_bytes(canonical_json(unsigned))


def main() -> None:
    if _git("status", "--short"):
        raise RuntimeError("pre-search lock requires a clean worktree")
    if OUTPUT.exists():
        raise RuntimeError("refusing to overwrite specification lock")

    forbidden = (
        REPO_ROOT / "src/python/wp6_dz_feas_v2",
        REPO_ROOT / "tests/wp6_dz_feas_v2",
        VALIDATION_ROOT / "wp6_dz_feas_v2_qualification.py",
        CAMPAIGN_ROOT / "search/search_ledger.json",
        CAMPAIGN_ROOT / "candidates/candidate_ledger.json",
        CAMPAIGN_ROOT / "results/qualification_results.json",
        CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_qualification_lock.json",
        CAMPAIGN_ROOT / "reports/wp6_dz_feas_v2_qualification_record.json",
        VALIDATION_ROOT / "wp6-dz-mr-v1",
    )
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise RuntimeError(f"constructive-search artifacts already exist: {present}")

    spec = load_json(SPEC)
    protocol = load_json(PROTOCOL)
    seeds = load_json(SEEDS)
    if (
        spec.get("campaign") != CAMPAIGN
        or protocol.get("campaign") != CAMPAIGN
        or seeds.get("campaign") != CAMPAIGN
        or spec.get("specification_status") != "LOCK_BEFORE_CONSTRUCTIVE_SEARCH"
        or protocol.get("protocol_status") != "LOCK_BEFORE_SEARCH"
    ):
        raise RuntimeError("campaign inputs are not lockable")

    exponents = protocol["support_library"]["exponents"]
    maximum_cardinality = spec["stop_rule"]["maximum_support_cardinality"]
    support_count = sum(
        len(list(combinations(exponents, size)))
        for size in range(1, maximum_cardinality + 1)
    )
    cover_count = len(protocol["shape_covers"])
    mass_case_count = len(protocol["mass_order_cases"])
    ideal_count = cover_count * support_count**2 * mass_case_count
    if (
        len(spec["witness_requirements"]) != 12
        or support_count != 15
        or support_count != protocol["support_library"]["support_count"]
        or support_count != spec["stop_rule"]["support_count_per_variable"]
        or cover_count != spec["stop_rule"]["shape_cover_count"]
        or mass_case_count != spec["stop_rule"]["mass_order_case_count"]
        or ideal_count != protocol["enumeration"]["total_systems"]
        or ideal_count != spec["stop_rule"]["coefficient_ideal_count"]
        or protocol["enumeration"]["systems_per_mass_case"]
        != cover_count * support_count**2
    ):
        raise RuntimeError("protocol and specification counts disagree")

    prerequisite_hashes: dict[str, str] = {}
    prerequisite_records: dict[str, dict[str, object]] = {}
    for name, item in spec["prerequisites"].items():
        for key, hash_key in (
            ("lock_file", "lock_file_sha256"),
            ("record_file", "record_file_sha256"),
        ):
            relative = item[key]
            observed = sha256_file(REPO_ROOT / relative)
            if observed != item[hash_key]:
                raise RuntimeError(f"prerequisite changed: {relative}")
            prerequisite_hashes[relative] = observed
        if "results_file" in item:
            relative = item["results_file"]
            observed = sha256_file(REPO_ROOT / relative)
            if observed != item["results_file_sha256"]:
                raise RuntimeError(f"prerequisite changed: {relative}")
            prerequisite_hashes[relative] = observed

        record = load_json(REPO_ROOT / item["record_file"])
        if (
            not _signed_record_valid(record)
            or record.get("qualification_id") != item["qualification_id"]
            or record.get("status") != item["required_status"]
        ):
            raise RuntimeError(f"invalid prerequisite record: {name}")
        prerequisite_records[name] = {
            "qualification_id": record["qualification_id"],
            "status": record["status"],
            "record_payload_sha256": record["record_payload_sha256"],
        }

    seed_hashes: dict[str, str] = {}
    for artifact in seeds["artifacts"]:
        observed = sha256_file(REPO_ROOT / artifact["path"])
        if observed != artifact["sha256"]:
            raise RuntimeError(f"seed artifact changed: {artifact['path']}")
        seed_hashes[artifact["path"]] = observed

    unsigned = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "lock_type": "pre_constructive_search_specification",
        "locked_utc": utc_now(),
        "base_git_commit": _git("rev-parse", "HEAD"),
        "spec_path": SPEC.relative_to(REPO_ROOT).as_posix(),
        "spec_sha256": sha256_file(SPEC),
        "protocol_path": PROTOCOL.relative_to(REPO_ROOT).as_posix(),
        "protocol_sha256": sha256_file(PROTOCOL),
        "seed_manifest_path": SEEDS.relative_to(REPO_ROOT).as_posix(),
        "seed_manifest_sha256": sha256_file(SEEDS),
        "plan_sha256": sha256_file(PLAN),
        "prerequisite_file_hashes": dict(sorted(prerequisite_hashes.items())),
        "prerequisite_records": prerequisite_records,
        "seed_artifact_hashes": dict(sorted(seed_hashes.items())),
        "locked_counts": {
            "witness_requirements": len(spec["witness_requirements"]),
            "shape_covers": cover_count,
            "support_exponents": len(exponents),
            "maximum_support_cardinality": maximum_cardinality,
            "supports_per_variable": support_count,
            "mass_order_cases": mass_case_count,
            "coefficient_ideals": ideal_count,
            "candidate_family_cap": spec["stop_rule"]["candidate_family_cap"],
            "per_ideal_timeout_seconds": spec["stop_rule"]["per_ideal_timeout_seconds"],
            "aggregate_compute_cap_seconds": spec["stop_rule"][
                "aggregate_compute_cap_seconds"
            ],
            "memory_cap_megabytes": spec["stop_rule"]["memory_cap_megabytes"],
        },
        "constructive_search_started_at_lock": False,
        "search_implementation_present_at_lock": False,
        "search_ledger_present_at_lock": False,
        "candidate_ledger_present_at_lock": False,
        "qualification_outputs_present_at_lock": False,
        "wp6_dz_mr_campaign_present_at_lock": False,
    }
    payload = dict(unsigned)
    payload["specification_lock_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(OUTPUT, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
