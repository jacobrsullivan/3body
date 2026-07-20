#!/usr/bin/env python
"""Freeze WP3-UP source groups from the prior disjoint exploration corpus."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import atomic_write_json, load_json, sha256_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-corpus", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec, source = load_json(args.spec), load_json(args.source_corpus)
    allowed = set(spec["data"]["executable_splits"])
    cases = []
    for case in source["cases"]:
        if case["split"] not in allowed:
            continue
        copied = dict(case)
        if copied["source_kind"] == "qualified_external_trajectory":
            copied["checkpoint_indices"] = spec["data"]["external_checkpoint_indices"]
        cases.append(copied)
    atomic_write_json(
        args.output,
        {
            "schema_version": "1.0",
            "corpus_id": "wp3-upstairs-degree3-frozen-corpus",
            "spec_sha256": sha256_file(args.spec),
            "source_corpus_sha256": sha256_file(args.source_corpus),
            "sealed_commitments_sha256": sha256_file(args.commitments),
            "gauge_angles": spec["library"]["gauge_angles"],
            "cases": cases,
        },
    )
    print(f"froze {len(cases)} WP3-UP source groups")


if __name__ == "__main__":
    main()
