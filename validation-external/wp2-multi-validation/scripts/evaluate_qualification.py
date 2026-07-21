#!/usr/bin/env python
"""Apply the frozen WP2-MULTIQ-v1 gates to one split."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))

from qualification_tools import atomic_write_json, load_json, make_gate, sha256_file, utc_now, verify_lock  # noqa: E402


def _values(cases, name):
    if not cases:
        raise RuntimeError(f"no cases available for required metric {name}")
    missing = [case.get("case_id", "<unknown>") for case in cases if name not in case.get("metrics", {})]
    if missing:
        raise RuntimeError(f"required metric {name} missing from cases: {missing}")
    return [float(case["metrics"][name]) for case in cases]


def _maximum(cases, name):
    return max(_values(cases, name))


def _minimum(cases, name):
    return min(_values(cases, name))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    args = parser.parse_args()

    spec, corpus, results = load_json(args.spec), load_json(args.corpus), load_json(args.results)
    split = results["split"]
    if results.get("campaign") != spec["campaign"] or corpus.get("campaign") != spec["campaign"]:
        raise RuntimeError("WP2-MULTI campaign identity mismatch")
    if results["spec_sha256"] != sha256_file(args.spec) or results["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("WP2-MULTI result input hash mismatch")
    if split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout evaluation requires the WP2-MULTI lock")
        lock = verify_lock(args.lock, ROOT, expected_prefix=spec["campaign"])
        if results.get("qualification_id") != lock["qualification_id"] or results.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError("WP2-MULTI holdout result is not bound to the lock")
        if Path(args.output).exists():
            raise RuntimeError("refusing to overwrite a WP2-MULTI holdout evaluation")
    cases = results["cases"]
    expected_cases = [case for case in corpus["cases"] if case["split"] == split]
    expected_ids = {case["case_id"] for case in expected_cases}
    observed_ids = [case.get("case_id") for case in cases]
    if len(observed_ids) != len(set(observed_ids)) or set(observed_ids) != expected_ids:
        raise RuntimeError("WP2-MULTI split result does not contain the exact frozen case set")
    expected_categories = {
        name: sum(case["category"] == name for case in expected_cases)
        for name in ("generic", "near_binary", "exact_passage")
    }
    observed_categories = {
        name: sum(case.get("category") == name for case in cases)
        for name in expected_categories
    }
    if observed_categories != expected_categories:
        raise RuntimeError("WP2-MULTI split category counts differ from the corpus")
    for case in cases:
        expected = next(item for item in expected_cases if item["case_id"] == case["case_id"])
        if (
            case.get("category") != expected["category"]
            or case.get("physical_channel") != expected["physical_channel"]
            or case.get("chart") != expected["chart"]
            or case.get("selected_edge") != expected["selected_edge"]
        ):
            raise RuntimeError(f"case metadata mismatch for {case['case_id']}")
    generic = [case for case in cases if case["category"] == "generic"]
    near = [case for case in cases if case["category"] == "near_binary"]
    passage = [case for case in cases if case["category"] == "exact_passage"]
    noncollision = generic + near
    gates_spec = spec["gates"]
    gates = [
        make_gate("case_success_rate", sum(case["success"] for case in cases) / len(cases), ">=", gates_spec["case_success_rate_min"]),
        make_gate("prerequisite_pass_rate", sum(item["status"] == "PASS" for item in results["prerequisites"].values()) / len(results["prerequisites"]), ">=", gates_spec["prerequisite_pass_rate_min"]),
        make_gate("symbolic_identity_pass_rate", results["structural"]["symbolic_identity_pass_rate"], ">=", gates_spec["symbolic_identity_pass_rate_min"]),
        make_gate("structural_case_count", results["structural"]["case_count"], "==", spec["execution"]["structural_cases_per_split"]),
        make_gate("dimension_and_constraint_count_pass_rate", results["structural"]["dimension_and_constraint_count_pass_rate"], ">=", gates_spec["dimension_and_constraint_count_pass_rate_min"]),
        make_gate("independent_hamiltonian_scaled_max", _maximum(cases, "independent_hamiltonian_scaled"), "<=", gates_spec["independent_hamiltonian_scaled_max"]),
        make_gate("independent_vector_field_scaled_max", _maximum(cases, "independent_vector_field_scaled"), "<=", gates_spec["independent_vector_field_scaled_max"]),
        make_gate("shell_abs_max", _maximum(cases, "shell_abs"), "<=", gates_spec["shell_abs_max"]),
        make_gate("xi_abs_max", _maximum(cases, "xi_abs"), "<=", gates_spec["xi_abs_max"]),
        make_gate("xi_lie_abs_max", _maximum(cases, "xi_lie_abs"), "<=", gates_spec["xi_lie_abs_max"]),
        make_gate("gauge_hamiltonian_scaled_max", _maximum(cases, "gauge_hamiltonian_scaled"), "<=", gates_spec["gauge_hamiltonian_scaled_max"]),
        make_gate("gauge_vector_covariance_scaled_max", _maximum(cases, "gauge_vector_covariance_scaled"), "<=", gates_spec["gauge_vector_covariance_scaled_max"]),
        make_gate("chart_roundtrip_scaled_max", _maximum(noncollision, "chart_roundtrip_scaled"), "<=", gates_spec["chart_roundtrip_scaled_max"]),
        make_gate("chart_hamiltonian_scaled_max", _maximum(noncollision, "chart_hamiltonian_scaled"), "<=", gates_spec["chart_hamiltonian_scaled_max"]),
        make_gate("chart_time_rate_scaled_max", _maximum(noncollision, "chart_time_rate_scaled"), "<=", gates_spec["chart_time_rate_scaled_max"]),
        make_gate("chart_cocycle_scaled_max", _maximum(noncollision, "chart_cocycle_scaled"), "<=", gates_spec["chart_cocycle_scaled_max"]),
        make_gate("projected_sundman_field_scaled_max", _maximum(noncollision, "projected_sundman_field_scaled"), "<=", gates_spec["projected_sundman_field_scaled_max"]),
        make_gate("generic_trajectory_scaled_max", _maximum(generic, "trajectory_scaled"), "<=", gates_spec["generic_trajectory_scaled_max"]),
        make_gate("near_binary_trajectory_scaled_max", _maximum(near, "trajectory_scaled"), "<=", gates_spec["near_binary_trajectory_scaled_max"]),
        make_gate("collision_limit_scaled_max", _maximum(passage, "collision_limit_scaled"), "<=", gates_spec["collision_limit_scaled_max"]),
        make_gate("collision_passage_finite_rate", _minimum(passage, "collision_passage_finite"), ">=", gates_spec["collision_passage_finite_rate_min"]),
        make_gate("collision_passage_hamiltonian_drift_scaled_max", _maximum(passage, "collision_passage_hamiltonian_drift_scaled"), "<=", gates_spec["collision_passage_hamiltonian_drift_scaled_max"]),
        make_gate("collision_passage_xi_drift_abs_max", _maximum(passage, "collision_passage_xi_drift_abs"), "<=", gates_spec["collision_passage_xi_drift_abs_max"]),
        make_gate("collision_passage_reference_scaled_max", _maximum(passage, "collision_passage_reference_scaled"), "<=", gates_spec["collision_passage_reference_scaled_max"]),
        make_gate("triple_collision_rejection_rate", _minimum(passage, "triple_collision_rejected"), ">=", gates_spec["triple_collision_rejection_rate_min"]),
        make_gate("structural_unseen_scientific_holdout", results["structural"]["unseen_scientific_holdout"], "==", gates_spec["structural_unseen_scientific_holdout"]),
        make_gate("structural_triple_collision_qualified", results["structural"]["triple_collision_qualified"], "==", gates_spec["structural_triple_collision_qualified"]),
    ]
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": split,
        "generated_utc": utc_now(),
        "status": status,
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "results_sha256": sha256_file(args.results),
        "case_count": len(cases),
        "category_counts": observed_categories,
        "gates": gates,
    }
    if split == "holdout":
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    print(f"WP2-MULTIQ-v1 {split}: {status} ({sum(gate['passed'] for gate in gates)}/{len(gates)} gates)")


if __name__ == "__main__":
    main()
