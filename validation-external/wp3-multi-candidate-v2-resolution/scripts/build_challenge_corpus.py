#!/usr/bin/env python
"""Build the deterministic unsealed candidate-resolution challenge corpus."""

from __future__ import annotations

import argparse
from fractions import Fraction
from pathlib import Path
import random
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import atomic_write_json, load_json, sha256_file  # noqa: E402
from validation_external_import import campaign_module  # noqa: E402


def _center(
    vectors: list[list[Fraction]], masses: tuple[Fraction, Fraction, Fraction]
) -> list[list[Fraction]]:
    total = sum(masses)
    center = [
        sum(masses[body] * vectors[body][component] for body in range(3)) / total
        for component in range(3)
    ]
    return [
        [vectors[body][component] - center[component] for component in range(3)]
        for body in range(3)
    ]


def _separations(positions: list[list[Fraction]]) -> list[float]:
    array = np.asarray([[float(value) for value in row] for row in positions])
    return [
        float(np.linalg.norm(array[first] - array[second]))
        for first, second in ((0, 1), (1, 2), (2, 0))
    ]


def _case(
    rng: random.Random,
    index: int,
    spec: dict[str, Any],
) -> dict[str, Any]:
    challenge = spec["challenge_corpus"]
    mass_low, mass_high = challenge["mass_numerator_range"]
    mass_denominator = int(challenge["mass_denominator"])
    component_low, component_high = challenge["state_component_numerator_range"]
    component_denominator = int(challenge["state_component_denominator"])
    spatial = index % 2 == 0
    while True:
        masses = tuple(
            Fraction(rng.randint(mass_low, mass_high), mass_denominator)
            for _ in range(3)
        )
        raw_positions = [
            [
                Fraction(
                    0
                    if component == 2 and not spatial
                    else rng.randint(component_low, component_high),
                    component_denominator,
                )
                for component in range(3)
            ]
            for _ in range(3)
        ]
        raw_velocities = [
            [
                Fraction(
                    0
                    if component == 2 and not spatial
                    else rng.randint(component_low, component_high),
                    component_denominator,
                )
                for component in range(3)
            ]
            for _ in range(3)
        ]
        positions = _center(raw_positions, masses)
        velocities = _center(raw_velocities, masses)
        distances = _separations(positions)
        if (
            min(distances) >= float(challenge["minimum_pair_separation"])
            and float(np.prod(distances))
            >= float(challenge["minimum_collision_product"])
            and (not spatial or any(row[2] != 0 for row in positions))
        ):
            break
    development_count = int(challenge["development_challenge_count"])
    split = (
        "development_challenge"
        if index < development_count
        else "calibration_challenge"
    )
    return {
        "case_id": f"resolution-{index:04d}",
        "split": split,
        "family": "spatial" if spatial else "planar",
        "masses": [str(value) for value in masses],
        "positions": [[str(value) for value in row] for row in positions],
        "velocities": [[str(value) for value in row] for row in velocities],
        "minimum_pair_separation_binary64": min(distances),
        "collision_product_binary64": float(np.prod(distances)),
    }


def build(spec_path: Path) -> dict[str, Any]:
    spec = load_json(spec_path)
    common = campaign_module(
        spec_path.parent / "scripts/campaign_common.py",
        "_wp3_multi_v2_resolution_common_builder",
    )
    specification_lock = common.verify_specification_lock(spec_path)
    challenge = spec["challenge_corpus"]
    total = int(challenge["development_challenge_count"]) + int(
        challenge["calibration_challenge_count"]
    )
    rng = random.Random(int(challenge["seed"]))
    cases = [_case(rng, index, spec) for index in range(total)]
    return {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "kind": "UNSEALED_DETERMINISTIC_RESOLUTION_CHALLENGE",
        "spec_sha256": sha256_file(spec_path),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "seed": int(challenge["seed"]),
        "development_challenge_count": int(challenge["development_challenge_count"]),
        "calibration_challenge_count": int(challenge["calibration_challenge_count"]),
        "spatial_case_count": sum(case["family"] == "spatial" for case in cases),
        "planar_case_count": sum(case["family"] == "planar" for case in cases),
        "publication_reserve_used": False,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite challenge corpus")
    payload = build(Path(args.spec).resolve())
    atomic_write_json(destination, payload)
    print(
        f"built {len(payload['cases'])} unsealed resolution cases; "
        f"spatial={payload['spatial_case_count']}; reserve_used=false"
    )


if __name__ == "__main__":
    main()
