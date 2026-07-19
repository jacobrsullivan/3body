#!/usr/bin/env python
"""
Rotating-frame reversibility validation for a WP1 orbit subset.

Tests forward/reversed integration error at multiple forward times
(T=1, 10, 50 TU). For CR3BP this uses the rotating-frame reversing
symmetry configured by create_cr3bp_reversibility_tester(), not a plain
velocity flip.
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
from src.python.orbits.periodic_families import (  # noqa: E402
    LyapunovOrbitGenerator,
    HaloOrbitGenerator,
)
from src.python.validation.time_reversibility import (  # noqa: E402
    create_cr3bp_reversibility_tester,
)


FORWARD_TIMES = [1.0, 10.0, 50.0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Time-reversibility validation")
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
        "--max-orbits", type=int, default=20, help="Number of orbits to test"
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


def main() -> None:
    args = parse_args()

    candidates = build_candidates(args.mu, args.max_orbits)
    tester = create_cr3bp_reversibility_tester(args.mu)
    integrator = IAS15Integrator(args.mu, tolerance=1e-14)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.summary), exist_ok=True)

    n_total = len(candidates)
    print(
        f"  Testing {n_total} orbits x {len(FORWARD_TIMES)} forward times...",
        flush=True,
    )

    fieldnames = [
        "orbit_idx",
        "family",
        "lpoint",
        "forward_time",
        "position_rms_error",
        "velocity_rms_error",
        "max_position_error",
        "energy_error",
        "passes_tier1",
    ]
    rows = []

    for i, cand in enumerate(candidates):
        state = np.array(cand["state"], dtype=float)
        for T in FORWARD_TIMES:
            try:
                result = tester.test_reversibility(
                    integrator,
                    state,
                    forward_time=T,
                )
                row = {
                    "orbit_idx": i,
                    "family": cand["family"],
                    "lpoint": cand["lpoint"],
                    "forward_time": T,
                    "position_rms_error": result.position_rms_error,
                    "velocity_rms_error": result.velocity_rms_error,
                    "max_position_error": result.max_position_error,
                    "energy_error": result.energy_error,
                    "passes_tier1": result.passes_tier1,
                }
                rows.append(row)
                print(
                    f"  [{i + 1}/{n_total}] T={T:5.1f}  "
                    f"pos_rms={result.position_rms_error:.2e}  "
                    f"tier1={'PASS' if result.passes_tier1 else 'FAIL'}",
                    flush=True,
                )
            except Exception as e:
                print(f"  [{i + 1}/{n_total}] T={T:5.1f}  FAILED: {e}", flush=True)

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote: {args.output}")

    # Build summary grouped by forward_time
    summary: Dict[str, Any] = {}
    for T in FORWARD_TIMES:
        t_rows = [r for r in rows if r["forward_time"] == T]
        if not t_rows:
            continue
        pos_rms = [r["position_rms_error"] for r in t_rows]
        key = f"T_{T:g}"
        summary[key] = {
            "n": len(t_rows),
            "median_pos_rms": float(np.median(pos_rms)),
            "p95_pos_rms": float(np.percentile(pos_rms, 95)),
            "max_pos_rms": float(np.max(pos_rms)),
            "tier1_pass_rate": sum(1 for r in t_rows if r["passes_tier1"])
            / len(t_rows),
        }

    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote: {args.summary}")


if __name__ == "__main__":
    main()
