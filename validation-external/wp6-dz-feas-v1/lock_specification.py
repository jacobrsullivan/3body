#!/usr/bin/env python
"""Create the WP6-DZ-FEAS-v1 pre-discovery specification lock."""

from __future__ import annotations

import json
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


CAMPAIGN_ROOT = VALIDATION_ROOT / "wp6-dz-feas-v1"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
PROTOCOL = CAMPAIGN_ROOT / "discovery_protocol.json"
SEEDS = CAMPAIGN_ROOT / "sources/seed_manifest.json"
PLAN = REPO_ROOT / "notes/wp6-dz-feas-v1-plan.md"
OUTPUT = CAMPAIGN_ROOT / "reports/wp6_dz_feas_v1_specification_lock.json"


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=REPO_ROOT, text=True
    ).strip()


def main() -> None:
    if _git("status", "--short"):
        raise RuntimeError("pre-discovery lock requires a clean worktree")
    if OUTPUT.exists():
        raise RuntimeError("refusing to overwrite specification lock")

    forbidden = (
        CAMPAIGN_ROOT / "results/search_results.json",
        CAMPAIGN_ROOT / "results/qualification_results.json",
        CAMPAIGN_ROOT / "candidates/candidate_ledger.json",
        CAMPAIGN_ROOT / "sources/discovery_manifest.json",
        CAMPAIGN_ROOT / "reports/wp6_dz_feas_v1_record.json",
        VALIDATION_ROOT / "wp6-dz-mr-v1",
    )
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise RuntimeError(f"discovery artifacts already exist: {present}")

    spec = load_json(SPEC)
    protocol = load_json(PROTOCOL)
    seeds = load_json(SEEDS)
    if (
        spec.get("campaign") != "WP6-DZ-FEAS-v1"
        or protocol.get("campaign") != spec["campaign"]
        or seeds.get("campaign") != spec["campaign"]
        or spec.get("specification_status") != "LOCKABLE_BEFORE_DISCOVERY"
        or protocol.get("protocol_status") != "LOCKABLE_BEFORE_DISCOVERY"
    ):
        raise RuntimeError("campaign inputs are not lockable")
    if (
        len(protocol["queries"]) != 12
        or len(spec["mandatory_candidate_classes"]) != 8
        or len(spec["witness_requirements"]) != 12
        or protocol["caps"]["primary_sources_inspected"]
        != spec["stop_rule"]["source_cap"]
        or protocol["caps"]["candidate_families"]
        != spec["stop_rule"]["candidate_family_cap"]
        or protocol["caps"]["citation_expansion_sources"]
        != spec["stop_rule"]["citation_expansion_cap"]
    ):
        raise RuntimeError("protocol and specification disagree")

    prerequisite_hashes: dict[str, str] = {}
    for item in spec["prerequisites"].values():
        for key, hash_key in (
            ("lock_file", "lock_file_sha256"),
            ("record_file", "record_file_sha256"),
        ):
            relative = item[key]
            observed = sha256_file(REPO_ROOT / relative)
            if observed != item[hash_key]:
                raise RuntimeError(f"prerequisite changed: {relative}")
            prerequisite_hashes[relative] = observed

    legacy_path = seeds["repository_negative_control"]["path"]
    legacy_hash = sha256_file(REPO_ROOT / legacy_path)
    if legacy_hash != seeds["repository_negative_control"]["sha256"]:
        raise RuntimeError("legacy negative-control fixture changed")

    unsigned = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "lock_type": "pre_discovery_feasibility_specification",
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
        "legacy_negative_control": {
            "path": legacy_path,
            "sha256": legacy_hash,
        },
        "locked_counts": {
            "queries": len(protocol["queries"]),
            "mandatory_candidate_classes": len(spec["mandatory_candidate_classes"]),
            "witness_requirements": len(spec["witness_requirements"]),
            "source_cap": spec["stop_rule"]["source_cap"],
            "candidate_family_cap": spec["stop_rule"]["candidate_family_cap"],
            "citation_expansion_cap": spec["stop_rule"]["citation_expansion_cap"],
        },
        "discovery_started_at_lock": False,
        "candidate_ledger_present_at_lock": False,
        "discovery_source_manifest_present_at_lock": False,
        "qualification_outputs_present_at_lock": False,
        "discovery_implementation_present_at_lock": False,
        "wp6_dz_mr_campaign_present_at_lock": False,
    }
    payload = dict(unsigned)
    payload["specification_lock_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(OUTPUT, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
