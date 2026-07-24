#!/usr/bin/env python
"""Lock the WP5-PUB-v1 claim and publication specification."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp5-pub-v1"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
SOURCES = CAMPAIGN_ROOT / "sources/manifest.json"
REVIEW_SCHEMA = CAMPAIGN_ROOT / "review/external_review_schema.json"
OUTPUT = CAMPAIGN_ROOT / "reports/wp5_pub_v1_specification_lock.json"

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
)


def _pinned_files(spec: dict) -> dict[str, str]:
    pinned: dict[str, str] = {}
    for prerequisite in spec["prerequisites"].values():
        for key, value in prerequisite.items():
            if not key.endswith("_file") or key + "_sha256" not in prerequisite:
                continue
            pinned[str(value)] = str(prerequisite[key + "_sha256"])
    source = spec["scientific_source_manifest"]
    pinned[str(source["path"])] = str(source["sha256"])
    return dict(sorted(pinned.items()))


def main() -> None:
    require_clean_worktree(REPO_ROOT)
    if OUTPUT.exists():
        raise RuntimeError(f"refusing to overwrite specification lock: {OUTPUT}")

    implementation_paths = [
        REPO_ROOT / "publication/wp5-pub-v1",
        CAMPAIGN_ROOT / "scripts/verify_package.py",
        CAMPAIGN_ROOT / "results/internal_evaluation.json",
        CAMPAIGN_ROOT / "reports/wp5_pub_v1_internal_record.json",
        CAMPAIGN_ROOT / "external_reviews",
    ]
    present = [str(path) for path in implementation_paths if path.exists()]
    if present:
        raise RuntimeError(
            "publication implementation or qualification output exists before lock: "
            + ", ".join(present)
        )

    spec = load_json(SPEC)
    if spec.get("campaign") != "WP5-PUB-v1":
        raise RuntimeError("unexpected campaign")
    pinned = _pinned_files(spec)
    for relative, expected in pinned.items():
        actual = sha256_file(REPO_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"prerequisite hash mismatch for {relative}: {actual} != {expected}"
            )

    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "lock_type": "claim_and_publication_specification",
        "locked_utc": utc_now(),
        "base_git_commit": git_output(REPO_ROOT, "rev-parse", "HEAD"),
        "worktree_clean_at_lock": True,
        "spec_path": SPEC.relative_to(REPO_ROOT).as_posix(),
        "spec_sha256": sha256_file(SPEC),
        "source_manifest_path": SOURCES.relative_to(REPO_ROOT).as_posix(),
        "source_manifest_sha256": sha256_file(SOURCES),
        "review_schema_path": REVIEW_SCHEMA.relative_to(REPO_ROOT).as_posix(),
        "review_schema_sha256": sha256_file(REVIEW_SCHEMA),
        "prerequisite_file_hashes": pinned,
        "implementation_present_at_lock": False,
        "qualification_outputs_present_at_lock": False,
        "external_review_evidence_present_at_lock": False,
    }
    payload["specification_lock_sha256"] = sha256_bytes(
        canonical_json(payload)
    )
    atomic_write_json(OUTPUT, payload)
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    print(payload["specification_lock_sha256"])


if __name__ == "__main__":
    main()
