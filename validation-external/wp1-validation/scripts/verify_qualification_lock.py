#!/usr/bin/env python
"""Verify the complete WP1 qualification lock before holdout execution."""

from __future__ import annotations

import argparse

from qualification_common import load_json, sha256_file, verify_qualification_lock


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--corpus-manifest", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lock = verify_qualification_lock(args.lock, args.repo_root)
    manifest = load_json(args.corpus_manifest)
    if lock["corpus_manifest_sha256"] != sha256_file(args.corpus_manifest):
        raise RuntimeError("Frozen corpus manifest hash does not match the lock")
    if lock["corpus_sha256"] != manifest["corpus_sha256"]:
        raise RuntimeError("Frozen corpus content hash does not match the lock")
    if lock["holdout_ids_sha256"] != manifest["holdout_ids_sha256"]:
        raise RuntimeError("Frozen holdout ID hash does not match the corpus manifest")
    print(
        f"Qualification lock verified: {lock['qualification_id']} "
        f"({len(lock['file_hashes'])} files)"
    )


if __name__ == "__main__":
    main()
