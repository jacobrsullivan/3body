#!/usr/bin/env python
"""Evaluate the fail-closed WP3 publication gate."""

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
    load_json,
    sha256_file,
    utc_now,
)
from src.python.wp3_exploration import evaluate_publication_gate  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = evaluate_publication_gate(
        args.spec,
        args.manifest,
        repo_root=REPO_ROOT,
    )
    result.update(
        {
            "generated_utc": utc_now(),
            "spec_sha256": sha256_file(args.spec),
            "evidence_manifest_sha256": sha256_file(args.manifest),
            "evidence_manifest_campaign": load_json(args.manifest)["campaign"],
        }
    )
    atomic_write_json(args.output, result)
    print(
        f"{result['campaign']}: {result['status']} "
        f"({result['passed_gate_count']}/{result['required_gate_count']} gates)"
    )


if __name__ == "__main__":
    main()
