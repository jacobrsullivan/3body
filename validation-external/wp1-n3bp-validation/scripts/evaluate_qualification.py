#!/usr/bin/env python
"""Apply the frozen WP1Q-N3BP-v1 gates to one split result."""

from __future__ import annotations

import argparse
from pathlib import Path
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


def _maximum(cases: list[dict[str, Any]], metric: str) -> float:
    values = [float(case["metrics"][metric]) for case in cases if metric in case["metrics"]]
    if not values:
        raise RuntimeError(f"no values found for mandatory metric {metric}")
    return max(values)


def _minimum(cases: list[dict[str, Any]], metric: str) -> float:
    values = [float(case["metrics"][metric]) for case in cases if metric in case["metrics"]]
    if not values:
        raise RuntimeError(f"no values found for mandatory metric {metric}")
    return min(values)


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
    split = str(results["split"])
    if results["spec_sha256"] != sha256_file(args.spec):
        raise RuntimeError("results use a different specification")
    if results["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("results use a different corpus")
    expected_ids = sorted(
        str(case["case_id"]) for case in corpus["cases"] if case["split"] == split
    )
    result_ids = sorted(str(case["case_id"]) for case in results["cases"])
    if result_ids != expected_ids:
        raise RuntimeError(f"{split} result IDs do not match the frozen corpus")

    lock = None
    if split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout evaluation requires the qualification lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix="WP1Q-N3BP-v1")
        if results.get("qualification_id") != lock["qualification_id"]:
            raise RuntimeError("holdout results have the wrong qualification ID")
        if results.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError("holdout results have the wrong lock hash")

    cases = results["cases"]
    lagrange = [case for case in cases if case["case_type"] == "lagrange"]
    sjtu = [case for case in cases if case["case_type"] == "sjtu_periodic"]
    gates_spec = spec["gates"]
    structural = results["structural_metrics"]
    gates = [
        make_gate("case_success_rate", sum(bool(case["success"]) for case in cases) / len(cases), ">=", gates_spec["case_success_rate_min"]),
        make_gate("dop853_rebound_position_error_scaled_max", _maximum(cases, "dop853_rebound_position_error_scaled"), "<=", gates_spec["dop853_rebound_position_error_scaled_max"]),
        make_gate("dop853_rebound_velocity_error_scaled_max", _maximum(cases, "dop853_rebound_velocity_error_scaled"), "<=", gates_spec["dop853_rebound_velocity_error_scaled_max"]),
        make_gate("lagrange_analytic_position_error_scaled_max", _maximum(lagrange, "lagrange_analytic_position_error_scaled"), "<=", gates_spec["lagrange_analytic_position_error_scaled_max"]),
        make_gate("lagrange_analytic_velocity_error_scaled_max", _maximum(lagrange, "lagrange_analytic_velocity_error_scaled"), "<=", gates_spec["lagrange_analytic_velocity_error_scaled_max"]),
        make_gate("periodic_closure_position_scaled_max", _maximum(cases, "periodic_closure_position_scaled"), "<=", gates_spec["periodic_closure_position_scaled_max"]),
        make_gate("periodic_closure_velocity_scaled_max", _maximum(cases, "periodic_closure_velocity_scaled"), "<=", gates_spec["periodic_closure_velocity_scaled_max"]),
        make_gate("relative_energy_drift_max", _maximum(cases, "relative_energy_drift"), "<=", gates_spec["relative_energy_drift_max"]),
        make_gate("linear_momentum_drift_scaled_max", _maximum(cases, "linear_momentum_drift_scaled"), "<=", gates_spec["linear_momentum_drift_scaled_max"]),
        make_gate("angular_momentum_drift_scaled_max", _maximum(cases, "angular_momentum_drift_scaled"), "<=", gates_spec["angular_momentum_drift_scaled_max"]),
        make_gate("center_of_mass_position_drift_scaled_max", _maximum(cases, "center_of_mass_position_drift_scaled"), "<=", gates_spec["center_of_mass_position_drift_scaled_max"]),
        make_gate("center_of_mass_velocity_drift_scaled_max", _maximum(cases, "center_of_mass_velocity_drift_scaled"), "<=", gates_spec["center_of_mass_velocity_drift_scaled_max"]),
        make_gate("minimum_pair_separation_scaled_min", _minimum(cases, "minimum_pair_separation_scaled"), ">=", gates_spec["minimum_pair_separation_scaled_min"]),
        make_gate("structural_translation_boost_error_max", structural["translation_boost_error_max"], "<=", gates_spec["structural_translation_boost_error_max"]),
        make_gate("structural_rotation_error_max", structural["rotation_error_max"], "<=", gates_spec["structural_rotation_error_max"]),
        make_gate("structural_permutation_error_max", structural["permutation_error_max"], "<=", gates_spec["structural_permutation_error_max"]),
        make_gate("structural_internal_force_balance_error_max", structural["internal_force_balance_error_max"], "<=", gates_spec["structural_internal_force_balance_error_max"]),
        make_gate("structural_barycenter_residual_max", structural["barycenter_residual_max"], "<=", gates_spec["structural_barycenter_residual_max"]),
    ]
    if sjtu:
        gates.extend(
            [
                make_gate("sjtu_closure_position_scaled_max", _maximum(sjtu, "periodic_closure_position_scaled"), "<=", gates_spec["sjtu_closure_position_scaled_max"]),
                make_gate("sjtu_closure_velocity_scaled_max", _maximum(sjtu, "periodic_closure_velocity_scaled"), "<=", gates_spec["sjtu_closure_velocity_scaled_max"]),
            ]
        )
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": split,
        "status": status,
        "generated_utc": utc_now(),
        "case_count": len(cases),
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
    print(f"WP1Q-N3BP-v1 {split} decision: {status} ({sum(gate['passed'] for gate in gates)}/{len(gates)} gates)")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
