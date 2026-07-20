#!/usr/bin/env python
"""Apply frozen WP1Q-N3BP-SPATIAL-v1 gates to one split."""

from __future__ import annotations

import argparse
from pathlib import Path
import statistics
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    make_gate,
    sha256_file,
    utc_now,
    verify_lock,
)


def _values(cases: list[dict[str, Any]], metric: str) -> list[float]:
    return [float(case["metrics"][metric]) for case in cases if case["success"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    args = parser.parse_args()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    results = load_json(args.results)
    split = results["split"]
    if results["spec_sha256"] != sha256_file(args.spec):
        raise RuntimeError("results use a different specification")
    if results["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("results use a different corpus")
    expected_ids = sorted(
        case["case_id"] for case in corpus["cases"] if case["split"] == split
    )
    result_ids = sorted(case["case_id"] for case in results["cases"])
    if result_ids != expected_ids:
        raise RuntimeError("result case IDs do not match the frozen corpus")
    lock = None
    if split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout evaluation requires the lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
        if results.get("qualification_id") != lock["qualification_id"]:
            raise RuntimeError("holdout qualification ID mismatch")
        if results.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError("holdout lock hash mismatch")

    cases = results["cases"]
    gates_spec = spec["gates"]
    count = len(cases)
    ftle = _values(cases, "finite_time_lyapunov")
    gates = [
        make_gate(
            "case_success_rate",
            sum(bool(case["success"]) for case in cases) / count,
            ">=",
            gates_spec["case_success_rate_min"],
        ),
        make_gate(
            "source_precision_rate",
            sum(_values(cases, "source_precision_pass")) / count,
            ">=",
            gates_spec["source_precision_rate_min"],
        ),
        make_gate(
            "spatial_rank_ratio_min",
            min(_values(cases, "spatial_rank_ratio")),
            ">=",
            gates_spec["spatial_rank_ratio_min"],
        ),
        make_gate(
            "positive_ftle_rate",
            sum(value > 0.0 for value in ftle) / len(ftle),
            ">=",
            gates_spec["positive_ftle_rate_min"],
        ),
        make_gate(
            "median_ftle",
            statistics.median(ftle),
            ">=",
            gates_spec["median_ftle_min"],
        ),
    ]
    for metric in (
        "oracle_convergence_position_scaled",
        "oracle_convergence_velocity_scaled",
        "oracle_brutus_position_scaled",
        "oracle_brutus_velocity_scaled",
        "production_oracle_short_position_scaled",
        "production_oracle_short_velocity_scaled",
        "oracle_relative_energy_drift",
    ):
        gates.append(
            make_gate(
                f"{metric}_max",
                max(_values(cases, metric)),
                "<=",
                gates_spec[f"{metric}_max"],
            )
        )
    gates.extend(
        [
            make_gate(
                "production_validation_horizon_max",
                max(_values(cases, "production_validation_horizon")),
                "<=",
                gates_spec["production_validation_horizon_max"],
            ),
            make_gate(
                "minimum_pair_separation_scaled_min",
                min(_values(cases, "minimum_pair_separation_scaled")),
                ">=",
                gates_spec["minimum_pair_separation_scaled_min"],
            ),
            make_gate(
                "source_payload_hash_rate",
                sum(_values(cases, "source_payload_hash_pass")) / count,
                ">=",
                gates_spec["source_payload_hash_rate_min"],
            ),
        ]
    )
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": split,
        "status": status,
        "generated_utc": utc_now(),
        "case_count": count,
        "case_ids": result_ids,
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "results_sha256": sha256_file(args.results),
        "gates": gates,
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    print(
        f"{spec['campaign']} {split}: {status} "
        f"({sum(gate['passed'] for gate in gates)}/{len(gates)} gates)"
    )
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
