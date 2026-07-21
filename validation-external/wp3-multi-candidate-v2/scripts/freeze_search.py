#!/usr/bin/env python
"""Freeze WP3-MULTI-CAND-v2 implementation and inputs before search."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    git_output,
    require_clean_worktree,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    tracked_files,
    utc_now,
)
from validation_external_import import campaign_module  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--scope", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    campaign = output.parent.parent
    for relative in (
        "results/search_results.json",
        "results/publication_gate.json",
        "reports/wp3_multi_v2_search_record.json",
        "reports/wp3_multi_v2_search_report.md",
        "reports/wp3_multi_v2_candidate_decision.json",
    ):
        if (campaign / relative).exists():
            raise RuntimeError("refusing to freeze after decision output exists")
    require_clean_worktree(root)
    common = campaign_module(
        campaign / "scripts/campaign_common.py",
        "_wp3_multi_v2_campaign_common_freeze",
    )
    specification_lock = common.verify_specification_lock(args.spec)
    spec = common.load_json(args.spec)
    if sha256_file(args.corpus) != spec["prerequisites"]["v1_search_corpus_sha256"]:
        raise RuntimeError("freeze corpus does not match the locked v1 corpus")
    files = tracked_files(root, args.scope)
    required = {
        Path(args.spec).resolve(),
        Path(args.corpus).resolve(),
        Path(args.commitments).resolve(),
        common.SPECIFICATION_LOCK.resolve(),
    }
    if not required.issubset(set(files)):
        raise RuntimeError("search freeze scopes omit required inputs")
    hashes = {path.relative_to(root).as_posix(): sha256_file(path) for path in files}
    snapshot = sha256_bytes(canonical_json(hashes))
    payload = {
        "schema_version": "1.0",
        "qualification_id": f"{args.prefix}-{snapshot[:12]}",
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(root, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "search_outputs_absent_at_freeze": True,
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "corpus_sha256": sha256_file(args.corpus),
        "sealed_commitments_sha256": sha256_file(args.commitments),
        "code_snapshot_sha256": snapshot,
        "runtime": runtime_fingerprint(),
        "file_hashes": hashes,
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(output, payload)
    print(f"Frozen {payload['qualification_id']}")
    print(f"Lock SHA-256: {payload['lock_sha256']}")


if __name__ == "__main__":
    main()
