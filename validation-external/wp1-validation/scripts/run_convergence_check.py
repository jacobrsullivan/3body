#!/usr/bin/env python
"""
Convergence-order validation for WP1 integrator.

Sweeps IAS15 tolerance from 1e-8 to 1e-14 and measures closure error
and Jacobi constant drift.  A well-behaved integrator should show
error scaling roughly as O(tol).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.python.integrators.ias15 import IAS15Integrator  # noqa: E402
from src.python.utils.dynamics import calculate_jacobi_constant  # noqa: E402
from src.python.orbits.periodic_families import (  # noqa: E402
    LyapunovOrbitGenerator,
    HaloOrbitGenerator,
)


TOLERANCES = [1e-8, 1e-9, 1e-10, 1e-11, 1e-12, 1e-13, 1e-14]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convergence-order validation")
    parser.add_argument(
        "--use-periodic-library",
        action="store_true",
        help="Use WP1 periodic families library",
    )
    parser.add_argument(
        "--mu", type=float, default=0.012150585609624, help="Mass parameter"
    )
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--summary", required=True, help="Output summary JSON path")
    parser.add_argument(
        "--max-orbits", type=int, default=10, help="Number of orbits to test"
    )
    return parser.parse_args()


def build_candidates(mu: float, max_orbits: int) -> List[Dict[str, Any]]:
    """Generate test orbits from Lyapunov and Halo families at L1/L2."""
    candidates: List[Dict[str, Any]] = []
    for L_point in ["L1", "L2"]:
        lyap = LyapunovOrbitGenerator(mu=mu, L_point=L_point)
        for orbit in lyap.generate_family(n_orbits=5, amplitude_range=(0.02, 0.2)):
            candidates.append(
                {
                    "state": orbit.initial_state,
                    "period": orbit.period,
                    "family": "lyapunov",
                    "lpoint": L_point,
                }
            )

        halo = HaloOrbitGenerator(mu=mu, L_point=L_point)
        for orbit in halo.generate_family(n_orbits=5, amplitude_range=(0.02, 0.2)):
            candidates.append(
                {
                    "state": orbit.initial_state,
                    "period": orbit.period,
                    "family": "halo",
                    "lpoint": L_point,
                }
            )

    return candidates[:max_orbits]


def compute_convergence_order(tol_medians: Dict[float, float]) -> float | None:
    """Estimate convergence order via log10(error) vs log10(tol)."""
    tols = sorted(tol_medians.keys())
    # Filter out entries with zero or negative median (shouldn't happen, but be safe)
    pairs = [(t, tol_medians[t]) for t in tols if tol_medians[t] > 0]
    if len(pairs) < 2:
        return None
    log_tol = np.array([np.log10(t) for t, _ in pairs])
    log_err = np.array([np.log10(e) for _, e in pairs])
    # slope of log10(error) vs log10(tol) = convergence order
    coeffs = np.polyfit(log_tol, log_err, 1)
    return float(coeffs[0])


def main() -> None:
    args = parse_args()

    candidates = build_candidates(args.mu, args.max_orbits)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.summary), exist_ok=True)

    n_total = len(candidates)
    n_tols = len(TOLERANCES)
    n_int = n_total * n_tols
    print(
        f"  Testing {n_total} orbits x {n_tols} tolerances"
        f" ({n_int} integrations)...",
        flush=True,
    )

    fieldnames = [
        "orbit_idx",
        "family",
        "lpoint",
        "tolerance",
        "closure_error",
        "jacobi_drift",
    ]
    rows = []

    for i, cand in enumerate(candidates):
        state = np.array(cand["state"], dtype=float)
        period = float(cand["period"])
        C0 = calculate_jacobi_constant(state, args.mu)

        for tol in TOLERANCES:
            try:
                integrator = IAS15Integrator(args.mu, tolerance=tol)
                result = integrator.integrate(
                    state, duration=period, output_interval=period / 200
                )
                final_state = result.states_corotating[-1]

                closure_error = float(np.linalg.norm(final_state - state))
                C1 = calculate_jacobi_constant(final_state, args.mu)
                jacobi_drift = float(abs(C1 - C0) / abs(C0))

                rows.append(
                    {
                        "orbit_idx": i,
                        "family": cand["family"],
                        "lpoint": cand["lpoint"],
                        "tolerance": tol,
                        "closure_error": closure_error,
                        "jacobi_drift": jacobi_drift,
                    }
                )
                print(
                    f"  [{i + 1}/{n_total}] tol={tol:.0e}  "
                    f"closure={closure_error:.2e}  dC/C={jacobi_drift:.2e}",
                    flush=True,
                )
            except Exception as e:
                print(f"  [{i + 1}/{n_total}] tol={tol:.0e}  FAILED: {e}", flush=True)

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote: {args.output}")

    # Build summary grouped by tolerance
    summary: Dict[str, Any] = {}
    tol_medians_closure: Dict[float, float] = {}

    for tol in TOLERANCES:
        t_rows = [r for r in rows if r["tolerance"] == tol]
        if not t_rows:
            continue
        closures = [r["closure_error"] for r in t_rows]
        drifts = [r["jacobi_drift"] for r in t_rows]
        key = f"tol_{tol:.0e}"
        med_closure = float(np.median(closures))
        summary[key] = {
            "n": len(t_rows),
            "median_closure": med_closure,
            "p95_closure": float(np.percentile(closures, 95)),
            "median_jacobi": float(np.median(drifts)),
            "p95_jacobi": float(np.percentile(drifts, 95)),
        }
        tol_medians_closure[tol] = med_closure

    order = compute_convergence_order(tol_medians_closure)
    summary["convergence_order"] = order
    if order is not None:
        print(f"  Estimated convergence order: {order:.2f}")

    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote: {args.summary}")


if __name__ == "__main__":
    main()
