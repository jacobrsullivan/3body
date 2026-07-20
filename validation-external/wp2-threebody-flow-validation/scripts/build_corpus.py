#!/usr/bin/env python
"""Select bounded external checkpoint cases for WP2-3BFLOWQ-v1."""

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
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec = load_json(args.spec)
    spatial = load_json(args.spatial_corpus)
    cases = []
    per_split = spec["execution"]["cases_per_family_by_split"]
    for split in ("development", "calibration", "holdout"):
        for family in ("equal_mass_plummer", "mass_4_2_1_plummer"):
            available = sorted(
                (
                    case
                    for case in spatial["cases"]
                    if case["split"] == split and case["source_family"] == family
                ),
                key=lambda item: item["case_id"],
            )
            for source in available[: int(per_split[split])]:
                cases.append(
                    {
                        "case_id": f"flow-{source['case_id']}",
                        "split": split,
                        "source_case_id": source["case_id"],
                        "source_family": family,
                        "checkpoint_indices": spec["execution"]["checkpoint_indices"],
                    }
                )
    atomic_write_json(
        args.output,
        {
            "schema_version": "1.0",
            "corpus_id": "wp2-threebody-flow-external-v1",
            "spatial_corpus_sha256": sha256_file(args.spatial_corpus),
            "cases": cases,
        },
    )
    print(f"selected {len(cases)} flow qualification cases")


if __name__ == "__main__":
    main()
