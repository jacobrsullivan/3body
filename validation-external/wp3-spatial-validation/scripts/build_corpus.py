#!/usr/bin/env python
"""Select and canonicalize the frozen Brutus spatial qualification corpus."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import atomic_write_json, load_json, sha256_file  # noqa: E402


FAMILIES = (
    ("equal_mass_plummer", "equal"),
    ("mass_4_2_1_plummer", "unequal"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--equal-source", required=True)
    parser.add_argument("--unequal-source", required=True)
    parser.add_argument("--selected-rows", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--sealed-commitments", required=True)
    parser.add_argument("--sealed-secret", required=True)
    parser.add_argument("--holdout-key", required=True)
    return parser.parse_args()


def _vectors(parts: list[str], offset: int) -> tuple[list[str], list[str], str]:
    mass = parts[offset]
    position = parts[offset + 1 : offset + 4]
    velocity = parts[offset + 4 : offset + 7]
    return position, velocity, mass


def _spatial_rank_ratio(parts: list[str]) -> float:
    initial = [_vectors(parts, offset) for offset in (1, 8, 15)]
    masses = np.array([float(item[2]) for item in initial])
    positions = np.array([[float(value) for value in item[0]] for item in initial])
    velocities = np.array([[float(value) for value in item[1]] for item in initial])
    m12 = masses[0] + masses[1]
    rho = positions[1] - positions[0]
    lambda_vector = positions[2] - (
        masses[0] * positions[0] + masses[1] * positions[1]
    ) / m12
    rho_dot = velocities[1] - velocities[0]
    lambda_dot = velocities[2] - (
        masses[0] * velocities[0] + masses[1] * velocities[1]
    ) / m12
    singular_values = np.linalg.svd(
        np.stack((rho, lambda_vector, rho_dot, lambda_dot)),
        compute_uv=False,
    )
    return float(singular_values[-1] / singular_values[0])


def _case(family: str, line: str, split: str) -> dict[str, Any]:
    parts = line.split()
    if len(parts) != 46:
        raise ValueError(f"unexpected Brutus row width: {len(parts)}")
    initial = [_vectors(parts, offset) for offset in (1, 8, 15)]
    final = [_vectors(parts, offset) for offset in (22, 29, 36)]
    source_index = int(parts[0])
    line_sha256 = hashlib.sha256(line.encode("ascii")).hexdigest()
    return {
        "case_id": f"brutus-{family}-{source_index:05d}",
        "split": split,
        "source_family": family,
        "source_index": source_index,
        "source_line_sha256": line_sha256,
        "masses_decimal": [item[2] for item in initial],
        "initial_positions_decimal": [item[0] for item in initial],
        "initial_velocities_decimal": [item[1] for item in initial],
        "brutus_final_positions_decimal": [item[0] for item in final],
        "brutus_final_velocities_decimal": [item[1] for item in final],
        "duration_decimal": parts[43],
        "brutus_tolerance_decimal": parts[44],
        "brutus_word_length_bits": int(float(parts[45])),
        "initial_spatial_rank_ratio": _spatial_rank_ratio(parts),
    }


def _eligible(line: str, selection: dict[str, Any]) -> bool:
    parts = line.split()
    if len(parts) != 46:
        return False
    duration = float(parts[43])
    tolerance = float(parts[44])
    word_length = int(float(parts[45]))
    return bool(
        float(selection["duration_min"]) <= duration <= float(selection["duration_max"])
        and tolerance <= float(selection["source_tolerance_max"])
        and word_length >= int(selection["source_word_length_bits_min"])
        and _spatial_rank_ratio(parts)
        >= float(selection["initial_spatial_rank_ratio_min"])
    )


def _rank(seed: str, family: str, line: str) -> str:
    index = line.split(maxsplit=1)[0]
    return hashlib.sha256(f"{seed}:{family}:{index}".encode("ascii")).hexdigest()


def main() -> None:
    args = _parse_args()
    spec = load_json(args.spec)
    manifest = load_json(args.manifest)
    selection = spec["source_selection"]
    source_paths = {"equal": Path(args.equal_source), "unequal": Path(args.unequal_source)}
    expected_hashes = {item["family"]: item["sha256"] for item in manifest["sources"]}
    key = Path(args.holdout_key).read_bytes().strip()
    if len(key) < 32:
        raise ValueError("holdout key must contain at least 32 bytes")

    cases: list[dict[str, Any]] = []
    selected_rows: list[str] = []
    commitments: list[dict[str, Any]] = []
    secrets: list[dict[str, Any]] = []
    counts = {
        "development": int(selection["development_per_family"]),
        "calibration": int(selection["calibration_per_family"]),
        "holdout": int(selection["holdout_per_family"]),
    }
    qualification_count = sum(counts.values())
    reserve_count = int(selection["wp3_sealed_reserve_per_family"])

    for family, path_key in FAMILIES:
        path = source_paths[path_key]
        if sha256_file(path) != expected_hashes[family]:
            raise RuntimeError(f"source hash mismatch for {family}")
        with path.open("r", encoding="ascii") as stream:
            header = stream.readline().rstrip("\n")
            lines = [line.rstrip("\n") for line in stream if line.strip()]
        eligible = [line for line in lines if _eligible(line, selection)]
        eligible.sort(key=lambda line: _rank(selection["selection_seed"], family, line))
        required = qualification_count + reserve_count
        if len(eligible) < required:
            raise RuntimeError(f"not enough eligible rows for {family}")
        qualification_lines = eligible[:qualification_count]
        reserve_lines = eligible[qualification_count:required]
        cursor = 0
        selected_rows.append(f"# family={family}")
        selected_rows.append(header)
        for split in ("development", "calibration", "holdout"):
            for line in qualification_lines[cursor : cursor + counts[split]]:
                cases.append(_case(family, line, split))
                selected_rows.append(line)
            cursor += counts[split]
        for line in reserve_lines:
            digest = hmac.new(key, line.encode("ascii"), hashlib.sha256).hexdigest()
            commitment_id = hashlib.sha256(
                f"{family}:{digest}".encode("ascii")
            ).hexdigest()[:20]
            commitments.append(
                {
                    "commitment_id": commitment_id,
                    "hmac_sha256": digest,
                    "source_family": family,
                    "status": "SEALED_UNEXECUTED",
                }
            )
            secrets.append(
                {
                    "commitment_id": commitment_id,
                    "source_family": family,
                    "source_line": line,
                }
            )

    cases.sort(key=lambda item: (item["split"], item["case_id"]))
    destination = Path(args.selected_rows)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(selected_rows) + "\n", encoding="ascii")
    atomic_write_json(
        args.corpus,
        {
            "schema_version": "1.0",
            "corpus_id": "brutus-spatial-chaotic-v1",
            "source_manifest_sha256": sha256_file(args.manifest),
            "selected_rows_sha256": sha256_file(destination),
            "cases": cases,
        },
    )
    commitments.sort(key=lambda item: item["commitment_id"])
    atomic_write_json(
        args.sealed_commitments,
        {
            "schema_version": "1.0",
            "campaign": "WP3-PUBLICATION-HOLDOUT-v1",
            "status": "SEALED_UNEXECUTED",
            "case_count": len(commitments),
            "selection_source": spec["campaign"],
            "key_location_policy": "The HMAC key and source rows are stored outside the repository on the designated holdout custodian host.",
            "commitments": commitments,
        },
    )
    atomic_write_json(
        args.sealed_secret,
        {
            "schema_version": "1.0",
            "campaign": "WP3-PUBLICATION-HOLDOUT-v1",
            "holdout_key_hex": key.hex(),
            "cases": secrets,
        },
    )
    print(
        f"selected {len(cases)} qualification cases and sealed "
        f"{len(commitments)} WP3 publication cases"
    )


if __name__ == "__main__":
    main()
