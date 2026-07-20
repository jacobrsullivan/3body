#!/usr/bin/env python
"""Select a fresh Brutus corpus while preserving the sealed WP3 reserve."""

from __future__ import annotations

import argparse
import hashlib
import hmac
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


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--equal-source", required=True)
    parser.add_argument("--unequal-source", required=True)
    parser.add_argument("--previous-selected-rows", required=True)
    parser.add_argument("--publication-commitments", required=True)
    parser.add_argument("--publication-secret", required=True)
    parser.add_argument("--selected-rows", required=True)
    parser.add_argument("--corpus", required=True)
    return parser.parse_args()


def _vectors(parts: list[str], offset: int) -> tuple[list[str], list[str], str]:
    return parts[offset + 1 : offset + 4], parts[offset + 4 : offset + 7], parts[offset]


def _spatial_rank_ratio(parts: list[str]) -> float:
    initial = [_vectors(parts, offset) for offset in (1, 8, 15)]
    masses = np.array([float(item[2]) for item in initial])
    positions = np.array([[float(value) for value in item[0]] for item in initial])
    velocities = np.array([[float(value) for value in item[1]] for item in initial])
    m12 = masses[0] + masses[1]
    vectors = np.stack(
        (
            positions[1] - positions[0],
            positions[2] - (masses[0] * positions[0] + masses[1] * positions[1]) / m12,
            velocities[1] - velocities[0],
            velocities[2] - (masses[0] * velocities[0] + masses[1] * velocities[1]) / m12,
        )
    )
    singular = np.linalg.svd(vectors, compute_uv=False)
    return float(singular[-1] / singular[0])


def _eligible(line: str, selection: dict[str, Any]) -> bool:
    parts = line.split()
    return bool(
        len(parts) == 46
        and float(selection["duration_min"]) <= float(parts[43]) <= float(selection["duration_max"])
        and float(parts[44]) <= float(selection["source_tolerance_max"])
        and int(float(parts[45])) >= int(selection["source_word_length_bits_min"])
        and _spatial_rank_ratio(parts) >= float(selection["initial_spatial_rank_ratio_min"])
    )


def _case(family: str, line: str, split: str) -> dict[str, Any]:
    parts = line.split()
    initial = [_vectors(parts, offset) for offset in (1, 8, 15)]
    final = [_vectors(parts, offset) for offset in (22, 29, 36)]
    index = int(parts[0])
    return {
        "case_id": f"brutus-{family}-{index:05d}",
        "split": split,
        "source_family": family,
        "source_index": index,
        "source_line_sha256": hashlib.sha256(line.encode("ascii")).hexdigest(),
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


def _rank(seed: str, family: str, line: str) -> str:
    index = line.split(maxsplit=1)[0]
    return hashlib.sha256(f"{seed}:{family}:{index}".encode("ascii")).hexdigest()


def _previous_rows(path: str) -> set[str]:
    return {
        line
        for line in Path(path).read_text(encoding="ascii").splitlines()
        if line and not line.startswith("#") and len(line.split()) == 46
    }


def _reserve_rows(secret_path: str, commitments_path: str) -> set[str]:
    secret = load_json(secret_path)
    commitments = load_json(commitments_path)
    key = bytes.fromhex(secret["holdout_key_hex"])
    expected = {
        (item["commitment_id"], item["hmac_sha256"], item["source_family"])
        for item in commitments["commitments"]
    }
    observed = set()
    rows = set()
    for item in secret["cases"]:
        line = item["source_line"]
        digest = hmac.new(key, line.encode("ascii"), hashlib.sha256).hexdigest()
        observed.add((item["commitment_id"], digest, item["source_family"]))
        rows.add(line)
    if observed != expected or len(rows) != commitments["case_count"]:
        raise RuntimeError("publication reserve secret does not match commitments")
    return rows


def main() -> None:
    args = _args()
    spec = load_json(args.spec)
    manifest = load_json(args.manifest)
    selection = spec["source_selection"]
    expected_hashes = {item["family"]: item["sha256"] for item in manifest["sources"]}
    source_paths = {"equal": Path(args.equal_source), "unequal": Path(args.unequal_source)}
    previous = _previous_rows(args.previous_selected_rows)
    reserve = _reserve_rows(args.publication_secret, args.publication_commitments)
    if previous & reserve:
        raise RuntimeError("v1 qualification and publication reserve overlap")
    excluded = previous | reserve
    counts = {
        "development": int(selection["development_per_family"]),
        "calibration": int(selection["calibration_per_family"]),
        "holdout": int(selection["holdout_per_family"]),
    }
    cases = []
    selected_rows = []
    for family, key in FAMILIES:
        source_path = source_paths[key]
        if sha256_file(source_path) != expected_hashes[family]:
            raise RuntimeError(f"source hash mismatch for {family}")
        with source_path.open("r", encoding="ascii") as stream:
            header = stream.readline().rstrip("\n")
            lines = [line.rstrip("\n") for line in stream if line.strip()]
        eligible = [line for line in lines if line not in excluded and _eligible(line, selection)]
        eligible.sort(key=lambda line: _rank(selection["selection_seed"], family, line))
        required = sum(counts.values())
        if len(eligible) < required:
            raise RuntimeError(f"not enough fresh eligible rows for {family}")
        selected_rows.extend((f"# family={family}", header))
        cursor = 0
        for split in ("development", "calibration", "holdout"):
            for line in eligible[cursor : cursor + counts[split]]:
                cases.append(_case(family, line, split))
                selected_rows.append(line)
            cursor += counts[split]
    cases.sort(key=lambda item: (item["split"], item["case_id"]))
    destination = Path(args.selected_rows)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(selected_rows) + "\n", encoding="ascii")
    atomic_write_json(
        args.corpus,
        {
            "schema_version": "1.0",
            "corpus_id": "brutus-spatial-chaotic-v2-fresh",
            "source_manifest_sha256": sha256_file(args.manifest),
            "selected_rows_sha256": sha256_file(destination),
            "previous_selected_rows_sha256": sha256_file(args.previous_selected_rows),
            "sealed_commitments_sha256": sha256_file(args.publication_commitments),
            "excluded_previous_case_count": len(previous),
            "excluded_publication_reserve_count": len(reserve),
            "publication_reserve_exclusion_verified": True,
            "cases": cases,
        },
    )
    print(
        f"selected {len(cases)} fresh qualification cases after excluding "
        f"{len(previous)} prior and {len(reserve)} sealed rows"
    )


if __name__ == "__main__":
    main()
