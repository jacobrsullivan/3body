#!/usr/bin/env python
"""Run float64 WP1 propagation checks over one qualification split."""

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

from qualification_common import load_corpus, load_spec, state_from_row, write_csv  # noqa: E402
from src.python.integrators.ias15 import IAS15Integrator  # noqa: E402
from src.python.utils.coordinates import (  # noqa: E402
    corotating_to_inertial,
    inertial_to_corotating,
)
from src.python.utils.dynamics import (  # noqa: E402
    calculate_jacobi_constant,
    distances_to_primaries,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument(
        "--split", required=True, choices=["development", "calibration", "holdout"]
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args()


def reversing_symmetry(state: np.ndarray) -> np.ndarray:
    """CR3BP reversing involution in rotating position/velocity coordinates."""
    x, y, z, vx, vy, vz = np.asarray(state, dtype=float)
    return np.array([x, -y, z, -vx, vy, -vz], dtype=float)


def validate_case(row: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    base = {
        "catalog_id": row["catalog_id"],
        "split": row["split"],
        "system": row["system"],
        "family": row["family"],
        "lpoint": row["lpoint"],
        "branch": row["branch"],
        "stability_regime": row["stability_regime"],
        "mu": row["mu"],
        "period": row["period"],
        "stability": row["stability"],
    }
    failure = {
        "integration_success": False,
        "jacobi_catalog_delta": float("nan"),
        "jacobi_endpoint_drift": float("nan"),
        "jacobi_max_drift": float("nan"),
        "closure_error": float("nan"),
        "stability_normalized_closure": float("nan"),
        "frame_roundtrip_error": float("nan"),
        "reversibility_error": float("nan"),
        "reversibility_position_rms": float("nan"),
        "reversibility_velocity_rms": float("nan"),
        "min_r_primary": float("nan"),
        "min_r_secondary": float("nan"),
        "min_secondary_distance_radii": float("nan"),
        "output_points": 0,
        "wall_time_seconds": 0.0,
        "failure_reason": "",
    }
    try:
        state = state_from_row(row)
        period = float(row["period"])
        mu = float(row["mu"])
        points = int(settings["output_points"])
        integrator = IAS15Integrator(mu, tolerance=float(settings["tolerance"]))
        result = integrator.integrate(
            state, duration=period, output_interval=period / (points - 1)
        )
        if not result.success:
            raise RuntimeError(result.message)
        states = np.asarray(result.states_corotating, dtype=float)
        if states.shape != (points, 6) or not np.all(np.isfinite(states)):
            raise RuntimeError(f"unexpected trajectory shape/content: {states.shape}")

        jacobi = np.array([calculate_jacobi_constant(value, mu) for value in states])
        c0 = float(jacobi[0])
        roundtrip = []
        primary_distances = []
        secondary_distances = []
        for sample_time, value in zip(result.times, states):
            inertial = corotating_to_inertial(value, float(sample_time))
            recovered = inertial_to_corotating(inertial, float(sample_time))
            roundtrip.append(float(np.max(np.abs(recovered - value))))
            r1, r2 = distances_to_primaries(value, mu)
            primary_distances.append(float(r1))
            secondary_distances.append(float(r2))

        horizon = min(float(settings["reversibility_horizon_max"]), period / 8.0)
        forward = integrator.integrate(state, horizon, horizon)
        if not forward.success:
            raise RuntimeError(f"reversibility forward leg failed: {forward.message}")
        backward = integrator.integrate(
            reversing_symmetry(forward.states_corotating[-1]), horizon, horizon
        )
        if not backward.success:
            raise RuntimeError(f"reversibility return leg failed: {backward.message}")
        recovered = reversing_symmetry(backward.states_corotating[-1])
        delta = recovered - state

        closure = float(np.linalg.norm(states[-1] - state))
        min_r2 = min(secondary_distances)
        return {
            **base,
            "integration_success": True,
            "jacobi_catalog_delta": abs(c0 - float(row["jacobi"])),
            "jacobi_endpoint_drift": abs(float(jacobi[-1]) - c0),
            "jacobi_max_drift": float(np.max(np.abs(jacobi - c0))),
            "closure_error": closure,
            "stability_normalized_closure": closure / max(1.0, float(row["stability"])),
            "frame_roundtrip_error": max(roundtrip),
            "reversibility_error": float(np.linalg.norm(delta)),
            "reversibility_position_rms": float(np.sqrt(np.mean(delta[:3] ** 2))),
            "reversibility_velocity_rms": float(np.sqrt(np.mean(delta[3:] ** 2))),
            "min_r_primary": min(primary_distances),
            "min_r_secondary": min_r2,
            "min_secondary_distance_radii": min_r2
            / float(row["secondary_radius_normalized"]),
            "output_points": len(states),
            "wall_time_seconds": time.perf_counter() - started,
            "failure_reason": "",
        }
    except Exception as exc:
        return {
            **base,
            **failure,
            "wall_time_seconds": time.perf_counter() - started,
            "failure_reason": str(exc),
        }


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    rows = load_corpus(args.corpus, args.split)
    if not rows:
        raise RuntimeError(f"No qualification rows for split {args.split}")
    settings = spec["float64"]
    results: list[dict[str, Any] | None] = [None] * len(rows)

    if args.workers <= 1:
        for index, row in enumerate(rows):
            results[index] = validate_case(row, settings)
            print(
                f"[{index + 1}/{len(rows)}] {row['catalog_id']} "
                f"success={results[index]['integration_success']}",
                flush=True,
            )
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(validate_case, row, settings): index
                for index, row in enumerate(rows)
            }
            completed = 0
            for future in as_completed(futures):
                index = futures[future]
                results[index] = future.result()
                completed += 1
                print(
                    f"[{completed}/{len(rows)}] {rows[index]['catalog_id']} "
                    f"success={results[index]['integration_success']}",
                    flush=True,
                )

    materialized = [result for result in results if result is not None]
    write_csv(args.output, materialized)
    passed = sum(bool(result["integration_success"]) for result in materialized)
    print(f"Wrote {len(materialized)} cases ({passed} successful): {args.output}")


if __name__ == "__main__":
    main()
