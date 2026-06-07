#!/usr/bin/env python
"""
Extended precision validation for a small WP1 orbit subset.

If heyoka is available, attempts high-precision Taylor integration.
Otherwise falls back to WP1 IAS15 integration.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

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
    parser = argparse.ArgumentParser(description="Extended precision validation")
    parser.add_argument(
        "--use-periodic-library",
        action="store_true",
        help="Use WP1 periodic families library",
    )
    parser.add_argument(
        "--mu", type=float, default=0.012150585609624, help="Mass parameter"
    )
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument(
        "--max-orbits", type=int, default=20, help="Number of orbits to test"
    )
    return parser.parse_args()


def build_candidates(mu: float, max_orbits: int) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for L_point in ["L1", "L2"]:
        lyap = LyapunovOrbitGenerator(mu=mu, L_point=L_point)
        for orbit in lyap.generate_family(n_orbits=5, amplitude_range=(0.02, 0.2)):
            candidates.append({"state": orbit.initial_state, "period": orbit.period})

        halo = HaloOrbitGenerator(mu=mu, L_point=L_point)
        for orbit in halo.generate_family(n_orbits=5, amplitude_range=(0.02, 0.2)):
            candidates.append({"state": orbit.initial_state, "period": orbit.period})

    return candidates[:max_orbits]


def try_heyoka_integrate(
    state: np.ndarray, duration: float, mu: float
) -> Dict[str, Any] | None:
    try:
        import heyoka as hy
    except Exception:
        return None

    try:
        x, y, z, vx, vy, vz = hy.make_vars("x", "y", "z", "vx", "vy", "vz")
        r1 = hy.sqrt((x + mu) ** 2 + y**2 + z**2)
        r2 = hy.sqrt((x - 1 + mu) ** 2 + y**2 + z**2)

        ax = 2 * vy + x - (1 - mu) * (x + mu) / r1**3 - mu * (x - 1 + mu) / r2**3
        ay = -2 * vx + y - (1 - mu) * y / r1**3 - mu * y / r2**3
        az = -(1 - mu) * z / r1**3 - mu * z / r2**3

        sys = [
            (x, vx),
            (y, vy),
            (z, vz),
            (vx, ax),
            (vy, ay),
            (vz, az),
        ]

        ta = hy.taylor_adaptive(sys, state, tol=1e-28)
        ta.propagate(duration)
        final_state = np.array(ta.state, dtype=float)

        return {
            "final_state": final_state,
            "engine": "heyoka",
        }
    except Exception:
        return None


def main() -> None:
    args = parse_args()

    candidates = build_candidates(args.mu, args.max_orbits)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    n_total = len(candidates)
    print(f"  Testing {n_total} orbits...", flush=True)

    rows = []
    for i, cand in enumerate(candidates, 1):
        state = np.array(cand["state"], dtype=float)
        period = float(cand["period"])

        heyoka_result = try_heyoka_integrate(state, period, args.mu)
        if heyoka_result is not None:
            final_state = heyoka_result["final_state"]
            engine = heyoka_result["engine"]
        else:
            integrator = IAS15Integrator(args.mu, tolerance=1e-14)
            result = integrator.integrate(
                state, duration=period, output_interval=period / 200
            )
            final_state = result.states_corotating[-1]
            engine = "ias15"

        closure_error = float(np.linalg.norm(final_state - state))
        C0 = calculate_jacobi_constant(state, args.mu)
        C1 = calculate_jacobi_constant(final_state, args.mu)
        jacobi_drift = float(abs(C1 - C0) / abs(C0))

        rows.append(
            {
                "engine": engine,
                "period": period,
                "closure_error": closure_error,
                "jacobi_drift": jacobi_drift,
            }
        )
        print(
            f"  [{i}/{n_total}] {engine}  closure={closure_error:.2e}  dC/C={jacobi_drift:.2e}",
            flush=True,
        )

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["engine", "period", "closure_error", "jacobi_drift"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
