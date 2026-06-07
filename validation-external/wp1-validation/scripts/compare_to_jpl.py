#!/usr/bin/env python
"""
Compare WP1 orbit candidates against JPL periodic orbit references.

Two independent tests per orbit:
1. Integrator accuracy — integrate JPL ICs for one period, measure closure error
2. Richardson quality — geometric distance between Richardson and JPL ICs
"""

from __future__ import annotations

import argparse
import collections
import csv
import glob
import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pyarrow.parquet as pq

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.python.integrators.ias15 import IAS15Integrator
from src.python.utils.dynamics import calculate_jacobi_constant
from src.python.orbits.periodic_families import (
    LyapunovOrbitGenerator,
    HaloOrbitGenerator,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare WP1 orbits to JPL catalog")
    parser.add_argument("--jpl", required=True, help="Normalized JPL Parquet file")
    parser.add_argument(
        "--use-periodic-library",
        action="store_true",
        help="Use WP1 periodic families library",
    )
    parser.add_argument(
        "--wp1-hdf5-dir", default=None, help="Directory of WP1 HDF5 outputs"
    )
    parser.add_argument(
        "--max-orbits", type=int, default=200, help="Max WP1 orbits to use for matching"
    )
    parser.add_argument(
        "--max-jpl", type=int, default=300, help="Max JPL orbits (stratified sample)"
    )
    parser.add_argument(
        "--mu", type=float, default=0.012150585609624, help="Mass parameter"
    )
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--summary", default=None, help="Output summary JSON path")
    return parser.parse_args()


def load_jpl(path: str) -> List[Dict[str, Any]]:
    table = pq.read_table(path)
    return table.to_pylist()


def stratified_sample(
    jpl_rows: List[Dict[str, Any]], max_total: int
) -> List[Dict[str, Any]]:
    """Sample JPL orbits proportionally across (family, lpoint, branch) groups.

    Within each group, selects evenly-spaced orbits across Jacobi constant range.
    """
    if len(jpl_rows) <= max_total:
        return jpl_rows

    # Group by (family, lpoint, branch)
    groups: Dict[tuple, List[Dict[str, Any]]] = collections.defaultdict(list)
    for row in jpl_rows:
        key = (
            str(row.get("family", "")).lower(),
            str(row.get("lpoint", "")).upper(),
            str(row.get("branch", "")).lower(),
        )
        groups[key].append(row)

    # Allocate proportionally, minimum 1 per group
    n_groups = len(groups)
    remaining = max_total
    allocations: Dict[tuple, int] = {}

    for key, rows in groups.items():
        alloc = max(1, int(round(len(rows) / len(jpl_rows) * max_total)))
        alloc = min(alloc, len(rows), remaining)
        allocations[key] = alloc
        remaining -= alloc
        if remaining <= 0:
            break

    # Distribute any leftover to largest groups
    if remaining > 0:
        for key in sorted(groups, key=lambda k: len(groups[k]), reverse=True):
            can_add = len(groups[key]) - allocations.get(key, 0)
            add = min(can_add, remaining)
            allocations[key] = allocations.get(key, 0) + add
            remaining -= add
            if remaining <= 0:
                break

    # Sample evenly-spaced within each group sorted by Jacobi
    sampled = []
    for key, rows in groups.items():
        n = allocations.get(key, 0)
        if n <= 0:
            continue
        sorted_rows = sorted(rows, key=lambda r: r.get("jacobi", 0.0) or 0.0)
        if n >= len(sorted_rows):
            sampled.extend(sorted_rows)
        else:
            indices = np.linspace(0, len(sorted_rows) - 1, n, dtype=int)
            sampled.extend(sorted_rows[i] for i in indices)

    return sampled


def build_wp1_candidates_from_library(mu: float) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for L_point in ["L1", "L2"]:
        lyap = LyapunovOrbitGenerator(mu=mu, L_point=L_point)
        for orbit in lyap.generate_family(n_orbits=10, amplitude_range=(0.01, 0.2)):
            C = calculate_jacobi_constant(orbit.initial_state, mu)
            candidates.append(
                {
                    "family": "lyapunov",
                    "lpoint": L_point,
                    "state": orbit.initial_state,
                    "period": orbit.period,
                    "jacobi": C,
                }
            )

        halo = HaloOrbitGenerator(mu=mu, L_point=L_point)
        for orbit in halo.generate_family(n_orbits=10, amplitude_range=(0.01, 0.2)):
            C = calculate_jacobi_constant(orbit.initial_state, mu)
            candidates.append(
                {
                    "family": "halo",
                    "lpoint": L_point,
                    "state": orbit.initial_state,
                    "period": orbit.period,
                    "jacobi": C,
                }
            )

    return candidates


def build_wp1_candidates_from_hdf5(
    hdf5_dir: str, max_orbits: int, mu: float
) -> List[Dict[str, Any]]:
    files = glob.glob(os.path.join(hdf5_dir, "*.h5"))[:max_orbits]
    candidates: List[Dict[str, Any]] = []

    import h5py

    for fp in files:
        with h5py.File(fp, "r") as f:
            state = f["states_corotating"][0]
            C = calculate_jacobi_constant(state, mu)
            candidates.append(
                {
                    "family": "unknown",
                    "lpoint": "",
                    "state": state,
                    "period": np.nan,
                    "jacobi": C,
                }
            )
    return candidates


def match_candidate(
    jpl_row: Dict[str, Any], candidates: List[Dict[str, Any]]
) -> Dict[str, Any] | None:
    if not candidates:
        return None

    family = str(jpl_row.get("family", "")).lower()
    lpoint = str(jpl_row.get("lpoint", "")).upper()

    filtered = candidates
    if family:
        filtered = [c for c in filtered if family in c["family"].lower()]
    if lpoint:
        filtered = [c for c in filtered if lpoint in c["lpoint"].upper()]

    if not filtered:
        filtered = candidates

    C_jpl = jpl_row.get("jacobi")
    if C_jpl is None or not np.isfinite(C_jpl):
        return filtered[0]

    deltas = [abs(c["jacobi"] - C_jpl) for c in filtered]
    return filtered[int(np.argmin(deltas))]


def main() -> None:
    args = parse_args()

    jpl_rows = load_jpl(args.jpl)
    n_total_jpl = len(jpl_rows)

    # Stratified sample
    jpl_rows = stratified_sample(jpl_rows, args.max_jpl)
    n_sampled = len(jpl_rows)

    if args.use_periodic_library:
        candidates = build_wp1_candidates_from_library(args.mu)
    elif args.wp1_hdf5_dir:
        candidates = build_wp1_candidates_from_hdf5(
            args.wp1_hdf5_dir, args.max_orbits, args.mu
        )
    else:
        raise ValueError("Provide --use-periodic-library or --wp1-hdf5-dir")

    integrator = IAS15Integrator(args.mu, tolerance=1e-14)

    print(
        f"  Comparing {n_sampled} JPL orbits (sampled from {n_total_jpl}) "
        f"against {len(candidates)} WP1 candidates...",
        flush=True,
    )

    results = []
    for idx, row in enumerate(jpl_rows, 1):
        state_jpl = np.array(
            [row.get(k, np.nan) for k in ["x", "y", "z", "vx", "vy", "vz"]],
            dtype=float,
        )
        period_jpl = row.get("period")
        C_jpl = row.get("jacobi")

        # --- Test 1: Integrator accuracy (uses JPL ICs) ---
        closure_error_jpl = np.nan
        jacobi_drift_jpl = np.nan

        if (
            np.all(np.isfinite(state_jpl))
            and period_jpl is not None
            and np.isfinite(period_jpl)
            and period_jpl > 0
        ):
            C_initial = calculate_jacobi_constant(state_jpl, args.mu)
            result = integrator.integrate(
                state_jpl, duration=period_jpl, output_interval=period_jpl / 200
            )
            final_state = result.states_corotating[-1]
            closure_error_jpl = float(np.linalg.norm(final_state - state_jpl))
            C_final = calculate_jacobi_constant(final_state, args.mu)
            jacobi_drift_jpl = float(abs(C_final - C_initial))

        # --- Test 2: Richardson quality (geometric, no integration) ---
        candidate = match_candidate(row, candidates)
        state_distance = np.nan
        delta_C = np.nan
        period_error = np.nan

        if candidate is not None:
            state_wp1 = np.array(candidate["state"], dtype=float)
            if np.all(np.isfinite(state_jpl)):
                state_distance = float(np.linalg.norm(state_wp1 - state_jpl))

            if C_jpl is not None and np.isfinite(C_jpl):
                delta_C = float(abs(candidate["jacobi"] - C_jpl))

            if (
                period_jpl is not None
                and np.isfinite(period_jpl)
                and period_jpl > 0
                and np.isfinite(candidate["period"])
            ):
                period_error = float(abs(candidate["period"] - period_jpl) / period_jpl)

        results.append(
            {
                "family": row.get("family", ""),
                "lpoint": row.get("lpoint", ""),
                "branch": row.get("branch", ""),
                "jacobi_jpl": C_jpl if C_jpl is not None else np.nan,
                "closure_error_jpl": closure_error_jpl,
                "jacobi_drift_jpl": jacobi_drift_jpl,
                "state_distance_richardson": state_distance,
                "delta_C_richardson": delta_C,
                "period_error_richardson": period_error,
            }
        )
        print(
            f"  [{idx}/{n_sampled}] closure={closure_error_jpl:.2e}  "
            f"jac_drift={jacobi_drift_jpl:.2e}  state_dist={state_distance:.2e}",
            flush=True,
        )

    # Write CSV
    csv_fields = [
        "family",
        "lpoint",
        "branch",
        "jacobi_jpl",
        "closure_error_jpl",
        "jacobi_drift_jpl",
        "state_distance_richardson",
        "delta_C_richardson",
        "period_error_richardson",
    ]
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(results)

    # Summary JSON
    summary_path = args.summary or os.path.splitext(args.output)[0] + "_summary.json"

    def _stat(values):
        values = np.array([v for v in values if np.isfinite(v)])
        if len(values) == 0:
            return {"count": 0}
        return {
            "count": int(len(values)),
            "median": float(np.median(values)),
            "p95": float(np.percentile(values, 95)),
            "max": float(np.max(values)),
        }

    summary = {
        "integrator_accuracy": {
            "closure_error": _stat([r["closure_error_jpl"] for r in results]),
            "jacobi_drift": _stat([r["jacobi_drift_jpl"] for r in results]),
        },
        "richardson_quality": {
            "state_distance": _stat([r["state_distance_richardson"] for r in results]),
            "delta_C": _stat([r["delta_C_richardson"] for r in results]),
            "period_error": _stat([r["period_error_richardson"] for r in results]),
        },
        "meta": {
            "n_jpl_total": n_total_jpl,
            "n_sampled": n_sampled,
            "n_wp1_candidates": len(candidates),
            "max_jpl": args.max_jpl,
        },
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote CSV: {args.output}")
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    main()
