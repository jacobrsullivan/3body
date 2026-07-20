#!/usr/bin/env python
"""Freeze a bounded qualification campaign before first holdout execution."""

from __future__ import annotations

import argparse
from pathlib import Path

from qualification_tools import atomic_write_json, build_lock


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--development", required=True)
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--scope", action="append", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output).resolve()
    for forbidden in (
        output.parent.parent / "results" / "holdout.json",
        output.parent.parent / "results" / "holdout_evaluation.json",
        output.parent / (output.stem.replace("_lock", "_record") + ".json"),
    ):
        if forbidden.exists():
            raise RuntimeError(
                f"refusing to freeze after holdout/final output exists: {forbidden}"
            )

    lock = build_lock(
        repo_root=args.repo_root,
        qualification_prefix=args.prefix,
        spec_path=args.spec,
        corpus_path=args.corpus,
        source_manifest_path=args.source_manifest,
        development_evaluation_path=args.development,
        calibration_evaluation_path=args.calibration,
        scopes=args.scope,
    )
    atomic_write_json(output, lock)
    print(f"Frozen {lock['qualification_id']}")
    print(f"Lock SHA-256: {lock['lock_sha256']}")


if __name__ == "__main__":
    main()
