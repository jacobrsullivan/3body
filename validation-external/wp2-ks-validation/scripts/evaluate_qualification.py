#!/usr/bin/env python
"""Apply the frozen WP2KSQ-v1 gates to one split result."""

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
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix="WP2KSQ-v1")
        if results.get("qualification_id") != lock["qualification_id"]:
            raise RuntimeError("holdout results have the wrong qualification ID")
        if results.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError("holdout results have the wrong lock hash")

    cases = results["cases"]
    elliptic = [case for case in cases if case["case_type"] == "elliptic"]
    radial = [case for case in cases if case["case_type"] == "radial_collision"]
    gates_spec = spec["gates"]
    structural = results["structural_metrics"]
    gates = [
        make_gate(
            "case_success_rate",
            sum(bool(case["success"]) for case in cases) / len(cases),
            ">=",
            gates_spec["case_success_rate_min"],
        ),
        make_gate("analytic_state_error_max", _maximum(elliptic, "analytic_state_error_max"), "<=", gates_spec["analytic_state_error_max"]),
        make_gate("rebound_state_error_max", _maximum(elliptic, "rebound_state_error_max"), "<=", gates_spec["rebound_state_error_max"]),
        make_gate("closure_position_error_max", _maximum(elliptic, "closure_position_error"), "<=", gates_spec["closure_position_error_max"]),
        make_gate("closure_velocity_error_max", _maximum(elliptic, "closure_velocity_error"), "<=", gates_spec["closure_velocity_error_max"]),
        make_gate("regularized_hamiltonian_abs_max", _maximum(elliptic, "regularized_hamiltonian_abs_max"), "<=", gates_spec["regularized_hamiltonian_abs_max"]),
        make_gate("momentum_map_abs_max", _maximum(elliptic, "momentum_map_abs_max"), "<=", gates_spec["momentum_map_abs_max"]),
        make_gate("physical_energy_abs_error_max", _maximum(elliptic, "physical_energy_abs_error_max"), "<=", gates_spec["physical_energy_abs_error_max"]),
        make_gate("period_relative_error_max", _maximum(elliptic, "period_relative_error"), "<=", gates_spec["period_relative_error_max"]),
        make_gate("structural_radius_error_max", structural["radius_error_max"], "<=", gates_spec["structural_radius_error_max"]),
        make_gate("structural_s1_invariance_error_max", structural["s1_invariance_error_max"], "<=", gates_spec["structural_s1_invariance_error_max"]),
        make_gate("structural_cotangent_roundtrip_error_max", structural["cotangent_roundtrip_error_max"], "<=", gates_spec["structural_cotangent_roundtrip_error_max"]),
        make_gate("structural_poisson_error_max", structural["poisson_error_max"], "<=", gates_spec["structural_poisson_error_max"]),
    ]
    if radial:
        gates.extend(
            [
                make_gate("radial_collision_q_norm_max", _maximum(radial, "collision_q_norm"), "<=", gates_spec["radial_collision_q_norm_max"]),
                make_gate("radial_symmetry_error_max", _maximum(radial, "symmetry_error"), "<=", gates_spec["radial_symmetry_error_max"]),
                make_gate("radial_regularized_hamiltonian_abs_max", _maximum(radial, "regularized_hamiltonian_abs_max"), "<=", gates_spec["radial_regularized_hamiltonian_abs_max"]),
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
    print(f"WP2KSQ-v1 {split} decision: {status} ({sum(gate['passed'] for gate in gates)}/{len(gates)} gates)")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
