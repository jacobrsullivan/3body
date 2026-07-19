#!/usr/bin/env python
"""Validate analytic CR3BP monodromy stability against JPL indices."""

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
    state_from_row,
    write_csv,
)
from src.python.validation.cr3bp_variational import integrate_state_and_stm  # noqa: E402


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


def validate_case(row: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    reference = float(row["stability"])
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
        "jpl_stability_index": reference,
    }
    try:
        result = integrate_state_and_stm(
            state_from_row(row),
            float(row["period"]),
            float(row["mu"]),
            rtol=float(settings["rtol"]),
            atol=float(settings["atol"]),
        )
        calculated = result.stability_index
        tolerance = float(settings["classification_tolerance"])
        source_stable = reference <= 1.0000001
        computed_stable = calculated <= 1.0 + tolerance
        if source_stable:
            classification_match = computed_stable
        elif reference <= 1.0 + tolerance:
            # The catalogue value itself is inside the declared marginal
            # uncertainty band; compare the indices rather than thresholding.
            classification_match = abs(calculated - reference) <= tolerance
        else:
            classification_match = calculated > 1.0 + tolerance
        return {
            **base,
            "success": True,
            "computed_stability_index": calculated,
            "relative_index_error": abs(calculated - reference) / max(1.0, abs(reference)),
            "classification_match": classification_match,
            "source_stable": source_stable,
            "computed_stable": computed_stable,
            "closure_error": result.closure_error,
            "monodromy_determinant_error": result.determinant_error,
            "reciprocal_pair_error": result.reciprocal_pair_error,
            "floquet_moduli": ";".join(
                f"{value:.17e}" for value in sorted(np.abs(result.eigenvalues))
            ),
            "nfev": result.nfev,
            "wall_time_seconds": time.perf_counter() - started,
            "failure_reason": "",
        }
    except Exception as exc:
        return {
            **base,
            "success": False,
            "computed_stability_index": float("nan"),
            "relative_index_error": float("nan"),
            "classification_match": False,
            "source_stable": reference <= 1.0000001,
            "computed_stable": False,
            "closure_error": float("nan"),
            "monodromy_determinant_error": float("nan"),
            "reciprocal_pair_error": float("nan"),
            "floquet_moduli": "",
            "nfev": 0,
            "wall_time_seconds": time.perf_counter() - started,
            "failure_reason": str(exc),
        }


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    settings = spec["stability"]
    rows = deterministic_subset(
        load_corpus(args.corpus, args.split),
        int(settings["maximum_cases"][args.split]),
        salt=f"stability:{spec['sampling']['split_salt']}:{args.split}",
        group_keys=("system", "family", "lpoint", "branch", "stability_regime"),
    )
    if not rows:
        raise RuntimeError(f"No stability rows for split {args.split}")
    results: list[dict[str, Any] | None] = [None] * len(rows)
    if args.workers <= 1:
        for index, row in enumerate(rows):
            results[index] = validate_case(row, settings)
            print(f"[{index + 1}/{len(rows)}] {row['catalog_id']}", flush=True)
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
                print(f"[{completed}/{len(rows)}] {rows[index]['catalog_id']}", flush=True)
    materialized = [result for result in results if result is not None]
    write_csv(args.output, materialized)
    print(f"Wrote {len(materialized)} stability comparisons: {args.output}")


if __name__ == "__main__":
    main()
