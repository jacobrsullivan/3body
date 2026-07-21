#!/usr/bin/env python
"""Build the frozen 45-case WP2-MULTIQ-v1 corpus."""

from __future__ import annotations

import argparse
from itertools import cycle
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))

from qualification_tools import atomic_write_json, load_json, sha256_file  # noqa: E402


ALLOCATIONS = {
    "development": {"generic": 9, "near_binary": 9, "exact_passage": 3},
    "calibration": {"generic": 5, "near_binary": 5, "exact_passage": 2},
    "holdout": {"generic": 4, "near_binary": 4, "exact_passage": 4},
}
CHARTS = ("central-1", "central-2", "central-3")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--n3bp-corpus", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    spec = load_json(args.spec)
    source = load_json(args.n3bp_corpus)
    source_ids = sorted(str(case["case_id"]) for case in source["cases"])
    if not source_ids:
        raise RuntimeError("the prerequisite N3BP corpus is empty")
    source_cycle = cycle(source_ids)
    angles = tuple(tuple(float(value) for value in pair) for pair in spec["execution"]["gauge_angles"])
    near_distances = tuple(float(value) for value in spec["corpus"]["near_collision_selected_distances"])

    cases = []
    serial = 0
    for split, allocation in ALLOCATIONS.items():
        for category in ("generic", "near_binary", "exact_passage"):
            for local_index in range(allocation[category]):
                chart = CHARTS[serial % len(CHARTS)]
                cases.append(
                    {
                        "case_id": f"multi-{split[:3]}-{category}-{local_index:02d}-{serial:03d}",
                        "split": split,
                        "category": category,
                        "source_case_id": next(source_cycle),
                        "chart": chart,
                        "selected_edge": 1 + (serial % 2),
                        "gauge_angles": list(angles[serial % len(angles)]),
                        "near_distance": near_distances[serial % len(near_distances)],
                        "checkpoint_index": serial % 5,
                    }
                )
                serial += 1

    observed = {key: 0 for key in ("generic", "near_binary", "exact_passage")}
    split_counts = {key: 0 for key in ALLOCATIONS}
    for case in cases:
        observed[case["category"]] += 1
        split_counts[case["split"]] += 1
    expected = {
        "generic": int(spec["corpus"]["generic_cases"]),
        "near_binary": int(spec["corpus"]["near_binary_cases"]),
        "exact_passage": int(spec["corpus"]["exact_passage_cases"]),
    }
    if observed != expected or split_counts != spec["corpus"]["splits"]:
        raise RuntimeError(
            f"locked corpus allocation mismatch: categories={observed}, splits={split_counts}"
        )
    atomic_write_json(
        args.output,
        {
            "schema_version": "1.0",
            "corpus_id": "wp2-multi-v1-45-case-atlas",
            "spec_sha256": sha256_file(args.spec),
            "n3bp_corpus_sha256": sha256_file(args.n3bp_corpus),
            "category_counts": observed,
            "split_counts": split_counts,
            "cases": cases,
        },
    )
    print(f"froze {len(cases)} WP2-MULTIQ-v1 cases")


if __name__ == "__main__":
    main()
