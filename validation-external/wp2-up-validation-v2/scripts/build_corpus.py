#!/usr/bin/env python
"""Freeze all qualified spatial cases for WP2-UP-v2."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))
from qualification_tools import atomic_write_json, load_json, sha256_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec, spatial = load_json(args.spec), load_json(args.spatial_corpus)
    angles = tuple(float(value) for value in spec["execution"]["gauge_angles"])
    counters = {}
    cases = []
    for source in sorted(spatial["cases"], key=lambda item: item["case_id"]):
        key = (source["split"], source["source_family"])
        index = counters.get(key, 0)
        counters[key] = index + 1
        cases.append({
            "case_id": f"up-v2-{source['case_id']}", "split": source["split"],
            "source_case_id": source["case_id"], "source_family": source["source_family"],
            "checkpoint_indices": spec["execution"]["checkpoint_indices"],
            "gauge_angle": angles[index % len(angles)],
        })
    atomic_write_json(args.output, {
        "schema_version": "1.0", "corpus_id": "wp2-up-v2-spatial-conformance",
        "spec_sha256": sha256_file(args.spec),
        "spatial_corpus_sha256": sha256_file(args.spatial_corpus), "cases": cases,
    })
    print(f"froze {len(cases)} WP2-UP-v2 cases")


if __name__ == "__main__":
    main()
