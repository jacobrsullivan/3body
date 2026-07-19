#!/usr/bin/env python
"""Reconstruct nearby Lyapunov/Halo orbits from perturbed external seeds."""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from qualification_common import (  # noqa: E402
    deterministic_subset,
    load_corpus,
    load_spec,
    stable_rank,
    state_from_row,
    write_csv,
)
from src.python.orbits.differential_correction import (  # noqa: E402
    correct_halo,
    correct_planar_lyapunov,
)
from src.python.utils.dynamics import calculate_jacobi_constant  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--float64-results", required=True)
    parser.add_argument(
        "--split", required=True, choices=["development", "calibration", "holdout"]
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args()


def reconstruct_case(
    row: dict[str, Any], settings: dict[str, Any], salt: str
) -> dict[str, Any]:
    started = time.perf_counter()
    seed = state_from_row(row)
    family = str(row["family"])
    sign = -1.0 if int(stable_rank(row["catalog_id"], salt)[0], 16) < 8 else 1.0
    base = {
        "catalog_id": row["catalog_id"],
        "split": row["split"],
        "system": row["system"],
        "family": family,
        "lpoint": row["lpoint"],
        "branch": row["branch"],
        "stability_regime": row["stability_regime"],
        "mu": row["mu"],
        "source_period": row["period"],
        "source_stability": row["stability"],
    }
    try:
        projected = seed.copy()
        projected[[1, 3, 5]] = 0.0
        if family == "lyapunov":
            projected[2] = 0.0
            fixed = float(projected[0]) + sign * float(
                settings["lyapunov_x_perturbation"]
            )
            result = correct_planar_lyapunov(
                projected,
                float(row["period"]),
                float(row["mu"]),
                fixed_x=fixed,
            )
        elif family == "halo":
            if abs(projected[2]) < 1e-12:
                raise ValueError("external Halo seed has zero z amplitude")
            fixed = float(projected[2]) * (
                1.0 + sign * float(settings["halo_z_relative_perturbation"])
            )
            result = correct_halo(
                projected,
                float(row["period"]),
                float(row["mu"]),
                fixed_z=fixed,
                max_nfev=200,
            )
        else:
            raise ValueError(f"unsupported reconstruction family: {family}")

        corrected = result.initial_state
        return {
            **base,
            "success": result.success,
            "fixed_component": result.fixed_component,
            "fixed_value": result.fixed_value,
            "period": result.period,
            "period_relative_change": abs(result.period - float(row["period"]))
            / float(row["period"]),
            "source_state_distance": float(np.linalg.norm(corrected - seed)),
            "jacobi": calculate_jacobi_constant(corrected, float(row["mu"])),
            "symmetry_residual": result.symmetry_residual,
            "closure_error": result.closure_error,
            "nfev": result.nfev,
            "x": corrected[0],
            "y": corrected[1],
            "z": corrected[2],
            "vx": corrected[3],
            "vy": corrected[4],
            "vz": corrected[5],
            "wall_time_seconds": time.perf_counter() - started,
            "failure_reason": "" if result.success else result.message,
        }
    except Exception as exc:
        return {
            **base,
            "success": False,
            "fixed_component": "",
            "fixed_value": float("nan"),
            "period": float("nan"),
            "period_relative_change": float("nan"),
            "source_state_distance": float("nan"),
            "jacobi": float("nan"),
            "symmetry_residual": float("nan"),
            "closure_error": float("nan"),
            "nfev": 0,
            "x": float("nan"),
            "y": float("nan"),
            "z": float("nan"),
            "vx": float("nan"),
            "vy": float("nan"),
            "vz": float("nan"),
            "wall_time_seconds": time.perf_counter() - started,
            "failure_reason": str(exc),
        }


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    settings = spec["reconstruction"]
    import csv

    with Path(args.float64_results).open("r", newline="", encoding="utf-8") as stream:
        geometry = {
            row["catalog_id"]: float(row["min_secondary_distance_radii"])
            for row in csv.DictReader(stream)
        }
    minimum_distance = float(settings["minimum_secondary_distance_radii"])
    eligible = [
        row
        for row in load_corpus(args.corpus, args.split)
        if geometry.get(row["catalog_id"], 0.0) >= minimum_distance
        and (
            row["family"] == "lyapunov"
            or (row["family"] == "halo" and abs(float(row["z"])) >= 1e-12)
        )
    ]
    salt = f"reconstruction:{spec['sampling']['split_salt']}:{args.split}"
    rows = deterministic_subset(
        eligible,
        int(settings["maximum_cases"][args.split]),
        salt=salt,
        group_keys=("system", "family", "lpoint", "branch", "stability_regime"),
    )
    if not rows:
        raise RuntimeError(f"No reconstruction rows for split {args.split}")
    results: list[dict[str, Any] | None] = [None] * len(rows)
    if args.workers <= 1:
        for index, row in enumerate(rows):
            results[index] = reconstruct_case(row, settings, salt)
            print(
                f"[{index + 1}/{len(rows)}] {row['catalog_id']} "
                f"success={results[index]['success']}",
                flush=True,
            )
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(reconstruct_case, row, settings, salt): index
                for index, row in enumerate(rows)
            }
            completed = 0
            for future in as_completed(futures):
                index = futures[future]
                results[index] = future.result()
                completed += 1
                print(
                    f"[{completed}/{len(rows)}] {rows[index]['catalog_id']} "
                    f"success={results[index]['success']}",
                    flush=True,
                )
    materialized = [result for result in results if result is not None]
    write_csv(args.output, materialized)
    print(f"Wrote {len(materialized)} reconstruction cases: {args.output}")


if __name__ == "__main__":
    main()
