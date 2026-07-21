#!/usr/bin/env python
"""Build the deterministic exact-mass external corpus after candidate freeze."""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
for path in (ROOT, VALIDATION, Path(__file__).resolve().parent):
    sys.path.insert(0, str(path))

from campaign_common import (  # noqa: E402
    locked_mass_grid,
    verify_candidate_lock,
    verify_source_snapshot,
    verify_specification_lock,
)
from qualification_tools import atomic_write_json, load_json, sha256_file, utc_now  # noqa: E402


SPLITS = ("development", "calibration", "holdout")


def _hash(salt: str, suffix: str) -> str:
    return hashlib.sha256(f"{salt}|{suffix}".encode("ascii")).hexdigest()


def _parse_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("#") or not line.strip():
                continue
            columns = line.split()
            if len(columns) != 9:
                raise RuntimeError(f"malformed selected source row: {line.rstrip()}")
            source_line = int(columns[0])
            m1, m2, m3, x1, v1, v2, period = map(float, columns[1:8])
            label = columns[8]
            numeric = (m1, m2, m3, x1, v1, v2, period)
            if (
                source_line <= 0
                or not all(math.isfinite(value) for value in numeric)
                or label not in {"S", "U"}
                or m3 != 1.0
                or period <= 0.0
            ):
                raise RuntimeError(f"invalid selected source row: {line.rstrip()}")
            rows.append(
                {
                    "source_line": source_line,
                    "m1": m1,
                    "m2": m2,
                    "m3": m3,
                    "x1": x1,
                    "v1": v1,
                    "v2": v2,
                    "period": period,
                    "source_stability": label,
                }
            )
    return rows


def _quotas(count: int, fractions: list[float]) -> list[int]:
    exact = [count * fraction for fraction in fractions]
    quotas = [math.floor(value) for value in exact]
    remainder_order = sorted(
        range(len(fractions)), key=lambda index: (-(exact[index] - quotas[index]), index)
    )
    for index in remainder_order[: count - sum(quotas)]:
        quotas[index] += 1
    return quotas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--candidate-lock", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    verify_specification_lock(args.spec)
    candidate_lock = verify_candidate_lock(
        args.candidate_lock, args.catalogue, args.spec
    )
    spec = load_json(args.spec)
    manifest, source = verify_source_snapshot(spec, args.source_manifest)
    rows = _parse_rows(source)
    expected_source_count = int(spec["execution"]["expected_candidate_count"])
    if len(rows) != expected_source_count:
        raise RuntimeError(
            f"selected source snapshot has {len(rows)} rows, "
            f"expected {expected_source_count}"
        )
    if manifest["external_snapshot"]["selected_row_count"] != len(rows):
        raise RuntimeError("selected source snapshot disagrees with manifest row count")
    grid = locked_mass_grid(spec)
    mass_keys = {
        (round(row["m1"], 12), round(row["m2"], 12)) for row in rows
    }
    expected_mass_keys = {
        (round(m1, 12), round(m2, 12)) for m1 in grid for m2 in grid
    }
    if mass_keys != expected_mass_keys or len(mass_keys) != len(rows):
        raise RuntimeError("selected source snapshot is not the exact locked mass grid")
    if len({row["source_line"] for row in rows}) != len(rows):
        raise RuntimeError("selected source snapshot reuses upstream line numbers")
    eligible = [row for row in rows if (row["m1"], row["m2"]) != (1.0, 1.0)]
    if len(rows) - len(eligible) != 1:
        raise RuntimeError("selected source snapshot must contain exactly one root row")
    if len(eligible) != int(spec["execution"]["expected_external_case_count"]):
        raise RuntimeError("wrong number of eligible external rows")

    salt = str(spec["external_source"]["split_salt"])
    fractions = [
        float(spec["execution"]["split_fractions"][split]) for split in SPLITS
    ]
    cases: list[dict[str, Any]] = []
    for label in ("S", "U"):
        labelled = [row for row in eligible if row["source_stability"] == label]
        labelled.sort(
            key=lambda row: _hash(
                salt, f"{label}|{row['m1']:.3f}|{row['m2']:.3f}"
            )
        )
        offset = 0
        for split, quota in zip(SPLITS, _quotas(len(labelled), fractions), strict=True):
            for row in labelled[offset : offset + quota]:
                case_id = f"sjtu-m1-{row['m1']:.3f}-m2-{row['m2']:.3f}"
                cases.append({"case_id": case_id, "split": split, **row})
            offset += quota
    if len(cases) != len(eligible):
        raise RuntimeError("stratification dropped external rows")
    if len({case["case_id"] for case in cases}) != len(cases):
        raise RuntimeError("stratification produced duplicate external case IDs")

    rebound_count = int(spec["execution"]["rebound_cases_per_split"])
    for split in SPLITS:
        members = [case for case in cases if case["split"] == split]
        selected = {
            case["case_id"]
            for case in sorted(
                members, key=lambda case: _hash(salt, f"rebound|{case['case_id']}")
            )[:rebound_count]
        }
        for case in members:
            case["rebound_selected"] = case["case_id"] in selected
    cases.sort(key=lambda case: case["case_id"])

    catalogue = load_json(args.catalogue)
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "selected_source_sha256": sha256_file(source),
        "candidate_lock_sha256": candidate_lock["candidate_lock_sha256"],
        "native_catalogue_file_sha256": sha256_file(args.catalogue),
        "native_catalogue_payload_sha256": catalogue["catalogue_sha256"],
        "root_row_excluded": True,
        "cases": cases,
    }
    atomic_write_json(args.output, payload)
    counts = {split: sum(case["split"] == split for case in cases) for split in SPLITS}
    labels = {label: sum(case["source_stability"] == label for case in cases) for label in ("S", "U")}
    print(f"built {len(cases)} exact-mass cases: splits={counts}, labels={labels}")


if __name__ == "__main__":
    main()
