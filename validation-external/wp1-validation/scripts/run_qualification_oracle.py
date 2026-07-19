#!/usr/bin/env python
"""Compare WP1 float64 propagation with an arbitrary-precision Taylor oracle."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from qualification_common import (  # noqa: E402
    deterministic_subset,
    load_corpus,
    load_spec,
    state_from_row,
    write_csv,
)
from src.python.integrators.heyoka_taylor import HeyokaTaylorIntegrator  # noqa: E402
from src.python.integrators.ias15 import IAS15Integrator  # noqa: E402
from src.python.utils.dynamics import calculate_jacobi_constant  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument(
        "--split", required=True, choices=["development", "calibration", "holdout"]
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    settings = spec["oracle"]
    rows = deterministic_subset(
        load_corpus(args.corpus, args.split),
        int(settings["maximum_cases"][args.split]),
        salt=f"oracle:{spec['sampling']['split_salt']}:{args.split}",
        group_keys=("system", "family", "stability_regime"),
    )
    if not rows:
        raise RuntimeError(f"No oracle rows for split {args.split}")

    ias_cache: dict[float, IAS15Integrator] = {}
    oracle_cache: dict[float, HeyokaTaylorIntegrator] = {}
    results: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        started = time.perf_counter()
        state = state_from_row(row)
        period = float(row["period"])
        mu = float(row["mu"])
        base = {
            "catalog_id": row["catalog_id"],
            "split": row["split"],
            "system": row["system"],
            "family": row["family"],
            "lpoint": row["lpoint"],
            "branch": row["branch"],
            "stability_regime": row["stability_regime"],
            "mu": mu,
            "period": period,
            "stability": row["stability"],
        }
        try:
            if mu not in ias_cache:
                ias_cache[mu] = IAS15Integrator(
                    mu, tolerance=float(spec["float64"]["tolerance"])
                )
                oracle_cache[mu] = HeyokaTaylorIntegrator(
                    mu,
                    tolerance=float(settings["tolerance"]),
                    precision_bits=int(settings["precision_bits"]),
                )
            points = int(settings["output_points"])
            interval = period / (points - 1)
            ias = ias_cache[mu].integrate(state, period, interval)
            oracle = oracle_cache[mu].integrate(state, period, interval)
            if not ias.success:
                raise RuntimeError(f"IAS15 failed: {ias.message}")
            if not oracle.success:
                raise RuntimeError(f"high-precision oracle failed: {oracle.message}")
            if ias.states_corotating.shape != oracle.states_corotating.shape:
                raise RuntimeError(
                    f"checkpoint shape mismatch: {ias.states_corotating.shape} vs "
                    f"{oracle.states_corotating.shape}"
                )
            errors = np.linalg.norm(
                ias.states_corotating - oracle.states_corotating, axis=1
            )
            c0 = calculate_jacobi_constant(state, mu)
            ias_drift = max(
                abs(calculate_jacobi_constant(value, mu) - c0)
                for value in ias.states_corotating
            )
            ias_closure = float(np.linalg.norm(ias.states_corotating[-1] - state))
            oracle_closure = float(
                np.linalg.norm(oracle.states_corotating[-1] - state)
            )
            results.append(
                {
                    **base,
                    "success": True,
                    "precision_bits": settings["precision_bits"],
                    "requested_tolerance": settings["tolerance"],
                    "high_precision_jacobi_drift": float(
                        oracle.stats["jacobi_relative_drift_float"]
                    ),
                    "ias15_jacobi_max_drift": float(ias_drift),
                    "checkpoint_state_error_p95": float(np.percentile(errors, 95)),
                    "checkpoint_state_error_max": float(np.max(errors)),
                    "final_state_error": float(errors[-1]),
                    "ias15_closure_error": ias_closure,
                    "oracle_closure_error": oracle_closure,
                    "closure_metric_delta": abs(ias_closure - oracle_closure),
                    "wall_time_seconds": time.perf_counter() - started,
                    "failure_reason": "",
                }
            )
        except Exception as exc:
            results.append(
                {
                    **base,
                    "success": False,
                    "precision_bits": settings["precision_bits"],
                    "requested_tolerance": settings["tolerance"],
                    "high_precision_jacobi_drift": float("nan"),
                    "ias15_jacobi_max_drift": float("nan"),
                    "checkpoint_state_error_p95": float("nan"),
                    "checkpoint_state_error_max": float("nan"),
                    "final_state_error": float("nan"),
                    "ias15_closure_error": float("nan"),
                    "oracle_closure_error": float("nan"),
                    "closure_metric_delta": float("nan"),
                    "wall_time_seconds": time.perf_counter() - started,
                    "failure_reason": str(exc),
                }
            )
        print(
            f"[{index + 1}/{len(rows)}] {row['catalog_id']} "
            f"success={results[-1]['success']}",
            flush=True,
        )

    write_csv(args.output, results)
    print(f"Wrote {len(results)} oracle comparisons: {args.output}")


if __name__ == "__main__":
    main()
