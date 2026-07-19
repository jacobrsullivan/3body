#!/usr/bin/env python
"""Build deterministic development/calibration/holdout JPL corpus splits."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import os
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from qualification_common import (
    STATE_KEYS,
    atomic_write_json,
    canonical_json,
    load_json,
    load_spec,
    sha256_bytes,
    sha256_file,
    stable_rank,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--holdout-ids", required=True)
    return parser.parse_args()


def stability_regime(value: float, spec: dict[str, Any]) -> str:
    for name, bounds in spec["sampling"]["stability_regimes"].items():
        if float(bounds[0]) <= value <= float(bounds[1]):
            return name
    raise ValueError(f"Stability value outside declared regimes: {value}")


def evenly_spaced(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (row["jacobi"], row["catalog_id"]))
    if len(ordered) <= count:
        return ordered
    indices = np.linspace(0, len(ordered) - 1, count, dtype=int)
    return [ordered[int(index)] for index in dict.fromkeys(indices)]


def assign_splits(rows: list[dict[str, Any]], split_salt: str) -> None:
    ranked = sorted(rows, key=lambda row: stable_rank(row["catalog_id"], split_salt))
    count = len(ranked)
    if count == 1:
        assignments = ["development"]
    elif count == 2:
        assignments = ["development", "holdout"]
    elif count == 3:
        assignments = ["development", "calibration", "holdout"]
    elif count == 4:
        assignments = ["development", "development", "calibration", "holdout"]
    else:
        cycle = ["development", "development", "development", "calibration", "holdout"]
        assignments = [cycle[index % len(cycle)] for index in range(count)]
    for row, split in zip(ranked, assignments):
        row["split"] = split


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    source_manifest_path = Path(args.source_manifest).resolve()
    spec = load_spec(spec_path)
    source_manifest = load_json(source_manifest_path)
    source_dir = source_manifest_path.parent

    source_config_hash = sha256_bytes(canonical_json(spec["external_source"]))
    if source_manifest["source_config_sha256"] != source_config_hash:
        raise RuntimeError(
            "JPL source manifest used a different external-source config"
        )

    records: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    for source_file in source_manifest["files"]:
        path = source_dir / source_file["path"]
        actual_hash = sha256_file(path)
        if actual_hash != source_file["sha256"]:
            raise RuntimeError(f"Pinned JPL source hash mismatch: {path}")
        source_hashes[source_file["system"]] = actual_hash
        payload = load_json(path)
        system = payload["system_key"]
        system_metadata = payload["system"]
        mu = float(system_metadata["mass_ratio"])
        secondary_radius = float(system_metadata["radius_secondary"]) / float(
            system_metadata["lunit"]
        )
        for query_index, query in enumerate(payload["queries"]):
            fields = query["fields"]
            family = str(query["family"]).lower()
            lpoint = f"L{int(query['libration_point'])}"
            branch = str(query.get("branch") or "").upper()
            for row_index, raw_row in enumerate(query["data"]):
                mapped = dict(zip(fields, raw_row))
                state = [float(mapped[key]) for key in STATE_KEYS]
                jacobi = float(mapped["jacobi"])
                period = float(mapped["period"])
                stability = float(mapped["stability"])
                identity_payload = {
                    "api_version": spec["external_source"]["required_api_version"],
                    "system": system,
                    "family": family,
                    "lpoint": lpoint,
                    "branch": branch,
                    "state": [str(mapped[key]).strip() for key in STATE_KEYS],
                    "jacobi": str(mapped["jacobi"]).strip(),
                    "period": str(mapped["period"]).strip(),
                    "stability": str(mapped["stability"]).strip(),
                }
                record_hash = sha256_bytes(canonical_json(identity_payload))
                catalog_id = f"jpl-v1-{system}-{family}-{lpoint.lower()}-{branch.lower() or 'na'}-{record_hash[:16]}"
                x, y, z = state[:3]
                r1 = float(np.sqrt((x + mu) ** 2 + y * y + z * z))
                r2 = float(np.sqrt((x - 1.0 + mu) ** 2 + y * y + z * z))
                records.append(
                    {
                        "catalog_id": catalog_id,
                        "source_record_sha256": record_hash,
                        "source_file_sha256": actual_hash,
                        "source_query_index": query_index,
                        "source_row_index": row_index,
                        "system": system,
                        "system_name": str(system_metadata["name"]),
                        "family": family,
                        "lpoint": lpoint,
                        "branch": branch,
                        "mu": mu,
                        "period": period,
                        "jacobi": jacobi,
                        "stability": stability,
                        "stability_regime": stability_regime(stability, spec),
                        "r_primary_initial": r1,
                        "r_secondary_initial": r2,
                        "secondary_radius_normalized": secondary_radius,
                        **dict(zip(STATE_KEYS, state)),
                    }
                )

    if len({record["catalog_id"] for record in records}) != len(records):
        raise RuntimeError("Stable JPL catalogue IDs are not unique")

    strata: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (
            record["system"],
            record["family"],
            record["lpoint"],
            record["branch"],
            record["stability_regime"],
        )
        strata[key].append(record)

    sampled: list[dict[str, Any]] = []
    per_stratum = int(spec["sampling"]["per_stability_stratum"])
    split_salt = str(spec["sampling"]["split_salt"])
    for key in sorted(strata):
        selected = evenly_spaced(strata[key], per_stratum)
        assign_splits(selected, f"{split_salt}:{'|'.join(key)}")
        sampled.extend(selected)
    sampled.sort(key=lambda row: row["catalog_id"])

    destination = Path(args.output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(sampled), destination, compression="zstd")

    holdout_ids = sorted(
        record["catalog_id"] for record in sampled if record["split"] == "holdout"
    )
    holdout_payload = {
        "schema_version": "1.0",
        "split_salt_sha256": sha256_bytes(split_salt.encode("utf-8")),
        "ids": holdout_ids,
        "ids_sha256": sha256_bytes(canonical_json(holdout_ids)),
    }
    atomic_write_json(args.holdout_ids, holdout_payload)

    split_counts = Counter(record["split"] for record in sampled)
    system_counts = Counter(record["system"] for record in sampled)
    family_counts = Counter(record["family"] for record in sampled)
    regime_counts = Counter(record["stability_regime"] for record in sampled)
    manifest_path = Path(args.manifest).resolve()
    manifest_dir = manifest_path.parent
    manifest = {
        "schema_version": "1.0",
        "path_base": "corpus_manifest_directory",
        "spec_path": os.path.relpath(spec_path, manifest_dir),
        "spec_sha256": sha256_file(spec_path),
        "source_manifest": os.path.relpath(source_manifest_path, manifest_dir),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "source_hashes": source_hashes,
        "source_record_count": len(records),
        "sampled_record_count": len(sampled),
        "corpus_path": os.path.relpath(destination, manifest_dir),
        "corpus_sha256": sha256_file(destination),
        "holdout_ids_path": os.path.relpath(
            Path(args.holdout_ids).resolve(), manifest_dir
        ),
        "holdout_ids_sha256": holdout_payload["ids_sha256"],
        "counts": {
            "split": dict(sorted(split_counts.items())),
            "system": dict(sorted(system_counts.items())),
            "family": dict(sorted(family_counts.items())),
            "stability_regime": dict(sorted(regime_counts.items())),
        },
    }
    atomic_write_json(manifest_path, manifest)
    print(f"Built {len(sampled)}-record qualification corpus: {destination}")
    print(f"Split counts: {dict(sorted(split_counts.items()))}")


if __name__ == "__main__":
    main()
