#!/usr/bin/env python
"""Apply frozen WP2-3BRQ-v1 gates to one compositional result split."""

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


def _maximum(
    cases: list[dict[str, Any]],
    structural: dict[str, Any],
    metric: str,
) -> float:
    values = [
        float(case["metrics"][metric])
        for case in cases
        if metric in case.get("metrics", {})
    ]
    if metric in structural:
        values.append(float(structural[metric]))
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
        raise RuntimeError("results use a different downstream specification")
    if results["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("results use a different downstream corpus")
    expected_ids = sorted(
        str(case["case_id"]) for case in corpus["cases"] if case["split"] == split
    )
    result_ids = sorted(str(case["case_id"]) for case in results["cases"])
    if result_ids != expected_ids:
        raise RuntimeError(f"{split} result IDs do not match the frozen corpus")

    lock = None
    if split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout evaluation requires the downstream lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix="WP2-3BRQ-v1")
        if results.get("qualification_id") != lock["qualification_id"]:
            raise RuntimeError("holdout results have the wrong qualification ID")
        if results.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError("holdout results have the wrong lock hash")

    cases = results["cases"]
    structural = results["structural_metrics"]
    gates_spec = spec["gates"]
    prerequisite_pass_rate = sum(
        item.get("status") == "PASS" for item in results["prerequisites"].values()
    ) / len(results["prerequisites"])
    singular_samples = sum(
        int(case.get("metrics", {}).get("singular_samples", 0)) for case in cases
    )
    correctly_classified = sum(
        int(case.get("metrics", {}).get("correctly_classified_singular_samples", 0))
        for case in cases
    )
    singular_rate = (
        1.0 if singular_samples == 0 else correctly_classified / singular_samples
    )
    generic_samples = sum(
        int(case.get("metrics", {}).get("generic_samples", 0)) for case in cases
    )
    gates = [
        make_gate(
            "case_success_rate",
            sum(bool(case["success"]) for case in cases) / len(cases),
            ">=",
            gates_spec["case_success_rate_min"],
        ),
        make_gate(
            "prerequisite_pass_rate",
            prerequisite_pass_rate,
            ">=",
            gates_spec["prerequisite_pass_rate_min"],
        ),
    ]
    maximum_gates = (
        "jacobi_roundtrip_scaled",
        "jacobi_symplectic_error",
        "jacobi_one_form_scaled",
        "energy_split_scaled",
        "angular_momentum_split_scaled",
        "euclidean_roundtrip_scaled",
        "euclidean_rigid_invariance_scaled",
        "euclidean_energy_scaled",
        "pairwise_position_roundtrip_scaled",
        "pairwise_velocity_roundtrip_scaled",
        "pairwise_xi_abs",
        "pairwise_position_closure_scaled",
        "pairwise_velocity_closure_scaled",
        "pairwise_s1_projection_scaled",
        "pairwise_s1_reconstruction_scaled",
    )
    for metric in maximum_gates:
        gates.append(
            make_gate(
                f"{metric}_max",
                _maximum(cases, structural, metric),
                "<=",
                gates_spec[f"{metric}_max"],
            )
        )
    gates.extend(
        [
            make_gate(
                "singular_classification_rate",
                singular_rate,
                ">=",
                gates_spec["singular_classification_rate_min"],
            ),
            make_gate(
                "generic_sample_count",
                generic_samples,
                ">=",
                gates_spec["generic_sample_count_min"],
            ),
            make_gate(
                "structural_translation_dimension",
                structural["translation_dimension"],
                "==",
                gates_spec["structural_translation_dimension"],
            ),
            make_gate(
                "structural_rotation_poisson_dimension",
                structural["rotation_poisson_dimension"],
                "==",
                gates_spec["structural_rotation_poisson_dimension"],
            ),
            make_gate(
                "structural_generic_leaf_dimension",
                structural["generic_leaf_dimension"],
                "==",
                gates_spec["structural_generic_leaf_dimension"],
            ),
            make_gate(
                "structural_pairwise_dimension",
                structural["pairwise_dimension"],
                "==",
                gates_spec["structural_pairwise_dimension"],
            ),
            make_gate(
                "structural_global_sundman_qualified",
                structural["global_sundman_qualified"],
                "==",
                gates_spec["structural_global_sundman_qualified"],
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
        "case_count": len(cases),
        "case_ids": result_ids,
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "results_sha256": sha256_file(args.results),
        "prerequisites": results["prerequisites"],
        "gates": gates,
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    print(
        f"WP2-3BRQ-v1 {split} decision: {status} "
        f"({sum(gate['passed'] for gate in gates)}/{len(gates)} gates)"
    )
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
