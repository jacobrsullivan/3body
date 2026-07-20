#!/usr/bin/env python
"""Apply frozen WP2-UP-v1 gates to one split."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import atomic_write_json, load_json, make_gate, sha256_file, utc_now, verify_lock  # noqa: E402


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
    if results["spec_sha256"] != sha256_file(args.spec) or results["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("results do not match WP2-UP frozen inputs")
    expected = sorted(case["case_id"] for case in corpus["cases"] if case["split"] == split)
    observed = sorted(case["case_id"] for case in results["cases"])
    if observed != expected:
        raise RuntimeError("WP2-UP result IDs do not match the corpus")
    lock = None
    if split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout evaluation requires the WP2-UP lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
        if results.get("qualification_id") != lock["qualification_id"] or results.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError("WP2-UP holdout lock mismatch")
    cases = results["cases"]
    gates_spec = spec["gates"]
    prerequisite_rate = sum(item["status"] == "PASS" for item in results["prerequisites"].values()) / len(results["prerequisites"])
    gates = [
        make_gate("case_success_rate", sum(case["success"] for case in cases) / len(cases), ">=", gates_spec["case_success_rate_min"]),
        make_gate("prerequisite_pass_rate", prerequisite_rate, ">=", gates_spec["prerequisite_pass_rate_min"]),
    ]
    maxima = (
        "reference_hamiltonian_scaled", "reference_vector_field_scaled",
        "shell_hamiltonian_scaled", "xi_level_abs", "roundtrip_scaled",
        "sundman_projection_scaled", "canonical_gradient_scaled",
        "s1_hamiltonian_scaled", "s1_projection_scaled",
        "s1_vector_covariance_scaled", "xi_lie_abs",
        "angular_momentum_lie_scaled", "short_flow_projection_scaled",
        "short_flow_hamiltonian_drift_scaled", "short_flow_xi_drift_abs",
    )
    for metric in maxima:
        gates.append(make_gate(f"{metric}_max", max(float(case["metrics"][metric]) for case in cases), "<=", gates_spec[f"{metric}_max"]))
    gates.append(make_gate(
        "selected_collision_finite_rate",
        sum(case["metrics"]["selected_collision_finite"] for case in cases) / len(cases),
        ">=", gates_spec["selected_collision_finite_rate_min"],
    ))
    gates.append(make_gate(
        "structural_simultaneous_regularization_qualified",
        results["structural"]["simultaneous_regularization_qualified"],
        "==", gates_spec["structural_simultaneous_regularization_qualified"],
    ))
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    payload = {
        "schema_version": "1.0", "campaign": spec["campaign"], "split": split,
        "status": status, "generated_utc": utc_now(), "case_count": len(cases),
        "case_ids": observed, "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus), "results_sha256": sha256_file(args.results),
        "prerequisites": results["prerequisites"], "gates": gates,
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    print(f"{spec['campaign']} {split}: {status} ({sum(g['passed'] for g in gates)}/{len(gates)} gates)")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
