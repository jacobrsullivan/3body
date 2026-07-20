#!/usr/bin/env python
"""Freeze external trajectory references and deterministic spatial collocation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import atomic_write_json, load_json, sha256_file  # noqa: E402


def _length_scale(positions: np.ndarray) -> float:
    return max(
        float(np.linalg.norm(positions[first] - positions[second]))
        for first, second in ((0, 1), (0, 2), (1, 2))
    )


def _spatial_rank(
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
) -> float:
    m1, m2, _ = masses
    m12 = m1 + m2
    vectors = np.stack(
        (
            positions[1] - positions[0],
            positions[2] - (m1 * positions[0] + m2 * positions[1]) / m12,
            velocities[1] - velocities[0],
            velocities[2] - (m1 * velocities[0] + m2 * velocities[1]) / m12,
        )
    )
    singular = np.linalg.svd(vectors, compute_uv=False)
    return float(singular[-1] / singular[0])


def _synthetic_case(
    rng: np.random.Generator,
    split: str,
    index: int,
    spec: dict,
) -> dict:
    minimum_mass = float(spec["data"]["synthetic_min_mass_fraction"])
    minimum_rank = float(spec["data"]["synthetic_spatial_rank_ratio_min"])
    for _ in range(10000):
        masses = rng.dirichlet(np.array([1.7, 2.1, 2.5]))
        if float(np.min(masses)) < minimum_mass:
            continue
        positions = rng.normal(size=(3, 3))
        velocities = rng.normal(size=(3, 3)) * rng.uniform(0.25, 1.75)
        positions -= np.sum(masses[:, None] * positions, axis=0)
        velocities -= np.sum(masses[:, None] * velocities, axis=0)
        positions /= _length_scale(positions)
        if _spatial_rank(positions, velocities, masses) < minimum_rank:
            continue
        return {
            "case_id": f"collocation-{split}-{index:04d}",
            "split": split,
            "source_kind": "deterministic_spatial_collocation",
            "source_family": "synthetic_mass_scan",
            "masses": masses.tolist(),
            "positions": positions.tolist(),
            "velocities": velocities.tolist(),
            "length_scale": _length_scale(positions),
            "spatial_rank_ratio": _spatial_rank(positions, velocities, masses),
        }
    raise RuntimeError("could not generate a qualified synthetic collocation state")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec = load_json(args.spec)
    spatial = load_json(args.spatial_corpus)
    cases = []
    checkpoint_indices = spec["data"]["external_checkpoint_indices"]
    for source in spatial["cases"]:
        if source["split"] not in ("development", "calibration"):
            continue
        positions = np.asarray(source["initial_positions_decimal"], dtype=float)
        cases.append(
            {
                "case_id": f"external-{source['case_id']}",
                "split": source["split"],
                "source_kind": "qualified_external_trajectory",
                "source_family": source["source_family"],
                "source_case_id": source["case_id"],
                "checkpoint_indices": checkpoint_indices,
                "length_scale": _length_scale(positions),
            }
        )
    rng = np.random.default_rng(int(spec["data"]["synthetic_collocation_seed"]))
    for split in ("development", "calibration"):
        count = int(spec["data"][f"synthetic_{split}_count"])
        cases.extend(_synthetic_case(rng, split, index, spec) for index in range(count))
    atomic_write_json(
        args.output,
        {
            "schema_version": "1.0",
            "corpus_id": "wp3-exploration-v2-frozen-corpus",
            "spec_sha256": sha256_file(args.spec),
            "spatial_corpus_sha256": sha256_file(args.spatial_corpus),
            "sealed_commitments_sha256": sha256_file(args.commitments),
            "cases": cases,
        },
    )
    print(f"froze {len(cases)} WP3 v2 source groups")


if __name__ == "__main__":
    main()
