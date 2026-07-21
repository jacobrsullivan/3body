#!/usr/bin/env python
"""Freeze the native catalogue before accepting any external split evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
for path in (ROOT, VALIDATION, Path(__file__).resolve().parent):
    sys.path.insert(0, str(path))

from campaign_common import (  # noqa: E402
    require_source_free_generation_event,
    verify_specification_lock,
)
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
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--scope", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output).resolve()
    if output.exists():
        raise RuntimeError("native candidate lock already exists")
    require_source_free_generation_event()

    require_clean_worktree(ROOT)
    specification_lock = verify_specification_lock(args.spec)
    catalogue_path = Path(args.catalogue).resolve()
    catalogue = load_json(catalogue_path)
    spec = load_json(args.spec)
    if catalogue.get("campaign") != spec["campaign"]:
        raise RuntimeError("native catalogue campaign mismatch")
    if catalogue.get("spec_sha256") != sha256_file(args.spec):
        raise RuntimeError("native catalogue specification mismatch")
    if catalogue.get("candidate_count") != spec["execution"]["expected_candidate_count"]:
        raise RuntimeError("native catalogue has the wrong candidate count")

    files = tracked_files(ROOT, args.scope)
    required = {Path(args.spec).resolve(), catalogue_path}
    if not required.issubset(set(files)):
        raise RuntimeError("candidate freeze scopes omit the spec or native catalogue")
    file_hashes = {
        path.relative_to(ROOT).as_posix(): sha256_file(path) for path in files
    }
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "lock_type": "native_candidate_pre_external_evaluation",
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(ROOT, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "external_evaluation_started_at_freeze": False,
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "catalogue_file_sha256": sha256_file(catalogue_path),
        "catalogue_payload_sha256": catalogue["catalogue_sha256"],
        "candidate_count": catalogue["candidate_count"],
        "code_snapshot_sha256": sha256_bytes(canonical_json(file_hashes)),
        "runtime": runtime_fingerprint(),
        "file_hashes": file_hashes,
    }
    payload["candidate_lock_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(output, payload)
    print(f"frozen native candidate payload: {payload['candidate_lock_sha256']}")


if __name__ == "__main__":
    main()
