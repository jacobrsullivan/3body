#!/usr/bin/env python
"""
Build a WP1 validation catalogue from external JPL periodic-orbit seeds.

This script does not claim that WP1 generated the orbit seeds. It validates
JPL initial conditions with the WP1 integrator stack, records explicit
accept/reject thresholds, and writes a publication-scoped external-seeded
catalogue containing only rows that pass those thresholds.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from compare_to_jpl import load_jpl, stratified_sample  # noqa: E402
from src.python.integrators.ias15 import IAS15Integrator  # noqa: E402
from src.python.utils.dynamics import calculate_jacobi_constant  # noqa: E402


STATE_KEYS = ["x", "y", "z", "vx", "vy", "vz"]
DEFAULT_CLOSURE_THRESHOLD = 1e-8
DEFAULT_JACOBI_DRIFT_THRESHOLD = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a validated JPL-seeded WP1 reference catalogue"
    )
    parser.add_argument("--jpl", required=True, help="Normalized JPL Parquet file")
    parser.add_argument(
        "--mu", type=float, default=0.012150585609624, help="Mass parameter"
    )
    parser.add_argument(
        "--max-jpl", type=int, default=300, help="Max JPL orbits to stratify/sample"
    )
    parser.add_argument(
        "--tolerance", type=float, default=1e-14, help="IAS15 tolerance"
    )
    parser.add_argument(
        "--closure-threshold",
        type=float,
        default=DEFAULT_CLOSURE_THRESHOLD,
        help="Maximum one-period closure error for catalogue acceptance",
    )
    parser.add_argument(
        "--jacobi-drift-threshold",
        type=float,
        default=DEFAULT_JACOBI_DRIFT_THRESHOLD,
        help="Maximum absolute one-period Jacobi drift for catalogue acceptance",
    )
    parser.add_argument(
        "--metrics-output", required=True, help="CSV path for all sampled metrics"
    )
    parser.add_argument(
        "--catalog-output",
        required=True,
        help="Parquet path for accepted external-seeded catalogue rows",
    )
    parser.add_argument("--summary", required=True, help="Output summary JSON path")
    return parser.parse_args()


def _safe_token(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback


def build_catalog_id(row: dict[str, Any], source_index: int) -> str:
    family = _safe_token(row.get("family"), "family")
    lpoint = _safe_token(row.get("lpoint"), "lp")
    branch = _safe_token(row.get("branch"), "branch")
    return f"jpl-{family}-{lpoint}-{branch}-{source_index:05d}"


def _finite_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if np.isfinite(result) else float("nan")


def state_from_row(row: dict[str, Any]) -> np.ndarray:
    return np.array([_finite_float(row.get(k)) for k in STATE_KEYS], dtype=float)


def is_valid_seed(row: dict[str, Any]) -> bool:
    state = state_from_row(row)
    period = _finite_float(row.get("period"))
    return bool(np.all(np.isfinite(state)) and period > 0)


def should_accept(
    closure_error: float,
    jacobi_drift: float,
    closure_threshold: float,
    jacobi_drift_threshold: float,
) -> bool:
    return bool(
        np.isfinite(closure_error)
        and np.isfinite(jacobi_drift)
        and closure_error <= closure_threshold
        and jacobi_drift <= jacobi_drift_threshold
    )


def _stat(values: list[float]) -> dict[str, Any]:
    finite = np.array([v for v in values if np.isfinite(v)], dtype=float)
    if len(finite) == 0:
        return {"count": 0}
    return {
        "count": int(len(finite)),
        "median": float(np.median(finite)),
        "p95": float(np.percentile(finite, 95)),
        "max": float(np.max(finite)),
    }


def _group_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = "|".join(
            [
                str(row.get("family", "") or ""),
                str(row.get("lpoint", "") or ""),
                str(row.get("branch", "") or ""),
            ]
        )
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def validate_seed(
    row: dict[str, Any],
    source_index: int,
    integrator: IAS15Integrator,
    mu: float,
    closure_threshold: float,
    jacobi_drift_threshold: float,
) -> dict[str, Any]:
    state = state_from_row(row)
    period = _finite_float(row.get("period"))

    base = {
        "catalog_id": build_catalog_id(row, source_index),
        "source": "JPL",
        "source_index": source_index,
        "family": str(row.get("family", "") or ""),
        "lpoint": str(row.get("lpoint", "") or ""),
        "branch": str(row.get("branch", "") or ""),
        "mu": float(mu),
        "period": period,
        "jacobi_reference": _finite_float(row.get("jacobi")),
        "stability": _finite_float(row.get("stability")),
        "x": float(state[0]),
        "y": float(state[1]),
        "z": float(state[2]),
        "vx": float(state[3]),
        "vy": float(state[4]),
        "vz": float(state[5]),
        "integrator": "IAS15",
        "tolerance": float(integrator.tolerance),
        "closure_threshold": float(closure_threshold),
        "jacobi_drift_threshold": float(jacobi_drift_threshold),
    }

    if not is_valid_seed(row):
        return {
            **base,
            "integration_success": False,
            "accepted": False,
            "closure_error": float("nan"),
            "jacobi_drift": float("nan"),
            "jacobi_catalog_delta": float("nan"),
            "failure_reason": "invalid_seed",
        }

    c0 = calculate_jacobi_constant(state, mu)
    result = integrator.integrate(state, duration=period, output_interval=period / 200)
    if not result.success:
        return {
            **base,
            "integration_success": False,
            "accepted": False,
            "closure_error": float("nan"),
            "jacobi_drift": float("nan"),
            "jacobi_catalog_delta": abs(c0 - base["jacobi_reference"])
            if np.isfinite(base["jacobi_reference"])
            else float("nan"),
            "failure_reason": result.message,
        }

    final_state = result.states_corotating[-1]
    c1 = calculate_jacobi_constant(final_state, mu)
    closure_error = float(np.linalg.norm(final_state - state))
    jacobi_drift = float(abs(c1 - c0))
    accepted = should_accept(
        closure_error, jacobi_drift, closure_threshold, jacobi_drift_threshold
    )

    return {
        **base,
        "integration_success": True,
        "accepted": accepted,
        "closure_error": closure_error,
        "jacobi_drift": jacobi_drift,
        "jacobi_catalog_delta": abs(c0 - base["jacobi_reference"])
        if np.isfinite(base["jacobi_reference"])
        else float("nan"),
        "failure_reason": "",
    }


def _write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        raise ValueError("No rows to write")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_parquet(path: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


def main() -> None:
    args = parse_args()

    jpl_rows_all = load_jpl(args.jpl)
    sampled = stratified_sample(jpl_rows_all, args.max_jpl)
    integrator = IAS15Integrator(args.mu, tolerance=args.tolerance)

    print(
        f"  Validating {len(sampled)} JPL-seeded orbits "
        f"(sampled from {len(jpl_rows_all)})...",
        flush=True,
    )

    rows: list[dict[str, Any]] = []
    for source_index, row in enumerate(sampled):
        metrics = validate_seed(
            row=row,
            source_index=source_index,
            integrator=integrator,
            mu=args.mu,
            closure_threshold=args.closure_threshold,
            jacobi_drift_threshold=args.jacobi_drift_threshold,
        )
        rows.append(metrics)
        status = "ACCEPT" if metrics["accepted"] else "REJECT"
        print(
            f"  [{source_index + 1}/{len(sampled)}] {status} "
            f"closure={metrics['closure_error']:.2e} "
            f"dC={metrics['jacobi_drift']:.2e}",
            flush=True,
        )

    accepted_rows = [r for r in rows if r["accepted"]]

    _write_csv(args.metrics_output, rows)
    _write_parquet(args.catalog_output, accepted_rows)

    closure_values = [r["closure_error"] for r in rows]
    drift_values = [r["jacobi_drift"] for r in rows]
    accepted_closures = [r["closure_error"] for r in accepted_rows]
    accepted_drifts = [r["jacobi_drift"] for r in accepted_rows]

    summary = {
        "meta": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "source": "JPL",
            "scope": "external-seeded WP1 validation catalogue",
            "n_jpl_total": len(jpl_rows_all),
            "n_sampled": len(sampled),
            "n_valid_integrations": sum(1 for r in rows if r["integration_success"]),
            "n_accepted": len(accepted_rows),
            "acceptance_rate": len(accepted_rows) / len(rows) if rows else 0.0,
            "sampling": "stratified_by_family_lpoint_branch_jacobi",
            "mu": args.mu,
            "integrator": "IAS15",
            "tolerance": args.tolerance,
            "closure_threshold": args.closure_threshold,
            "jacobi_drift_threshold": args.jacobi_drift_threshold,
            "metrics_output": args.metrics_output,
            "catalog_output": args.catalog_output,
        },
        "all_sampled": {
            "closure_error": _stat(closure_values),
            "jacobi_drift": _stat(drift_values),
        },
        "accepted_catalog": {
            "closure_error": _stat(accepted_closures),
            "jacobi_drift": _stat(accepted_drifts),
            "groups": _group_counts(accepted_rows),
        },
    }

    os.makedirs(os.path.dirname(args.summary), exist_ok=True)
    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote metrics CSV: {args.metrics_output}")
    print(f"Wrote accepted catalogue: {args.catalog_output}")
    print(f"Wrote summary: {args.summary}")


if __name__ == "__main__":
    main()
