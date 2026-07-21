#!/usr/bin/env python
"""Apply the locked WP1-CAT-N3BP-v1 gates to one split."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
for path in (VALIDATION, Path(__file__).resolve().parent):
    sys.path.insert(0, str(path))

from campaign_common import require_full_lock_runtime  # noqa: E402
from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)


SPLITS = ("development", "calibration", "holdout")
TRAJECTORY_METRICS = {
    "closure_position_scaled",
    "closure_velocity_scaled",
    "relative_energy_drift",
    "linear_momentum_drift_scaled",
    "angular_momentum_drift_scaled",
    "minimum_pair_separation_scaled",
}
CASE_METRICS = TRAJECTORY_METRICS | {
    "exact_mass_match",
    "external_parameter_error",
    "external_period_relative_error",
    "planar_stability_classified",
    "planar_stability_label_agreement",
}
REBOUND_METRICS = {
    "dop853_rebound_position_error_scaled",
    "dop853_rebound_velocity_error_scaled",
}
CATALOGUE_METRICS = {
    "candidate_count",
    "candidate_success_rate",
    "external_seed_count",
    "evaluation_row_used_as_seed_count",
    "stored_closure_position_scaled_max",
    "stored_closure_velocity_scaled_max",
    "monodromy_symplectic_defect_max",
    "monodromy_reciprocal_pair_error_max",
    "partition_disjoint_rate",
    "one_to_one_match_rate",
    "duplicate_count",
}
STRUCTURAL_METRICS = {
    "structural_blind_holdout",
    "structural_independent_root_discovery",
    "structural_general_n3bp_catalogue",
}


def _require_finite_metrics(
    values: Any, required: set[str], context: str
) -> None:
    if not isinstance(values, dict):
        raise RuntimeError(f"{context} metrics are missing")
    missing = sorted(required.difference(values))
    if missing:
        raise RuntimeError(f"{context} metrics are missing required values: {missing}")
    nonfinite = sorted(
        name
        for name in required
        if isinstance(values[name], bool)
        or not isinstance(values[name], (int, float))
        or not math.isfinite(float(values[name]))
    )
    if nonfinite:
        raise RuntimeError(f"{context} metrics are non-finite or non-numeric: {nonfinite}")


def validate_evidence_contract(
    spec: dict[str, Any], corpus: dict[str, Any], results: dict[str, Any]
) -> list[dict[str, Any]]:
    """Validate exact split identity and metric completeness before gating."""

    campaign = spec["campaign"]
    if corpus.get("campaign") != campaign or results.get("campaign") != campaign:
        raise RuntimeError("specification, corpus, and result campaigns must match")
    split = results.get("split")
    if split not in SPLITS:
        raise RuntimeError(f"invalid result split: {split!r}")
    corpus_cases = corpus.get("cases")
    result_cases = results.get("cases")
    if not isinstance(corpus_cases, list) or not isinstance(result_cases, list):
        raise RuntimeError("corpus and result cases must be lists")
    expected_total = int(spec["execution"]["expected_external_case_count"])
    corpus_ids = [str(case.get("case_id", "")) for case in corpus_cases]
    if (
        len(corpus_cases) != expected_total
        or any(not case_id for case_id in corpus_ids)
        or len(set(corpus_ids)) != len(corpus_ids)
        or any(case.get("split") not in SPLITS for case in corpus_cases)
    ):
        raise RuntimeError("corpus case IDs/count/splits violate the locked contract")

    expected = {
        str(case["case_id"]): case
        for case in corpus_cases
        if case["split"] == split
    }
    observed_ids = [str(case.get("case_id", "")) for case in result_cases]
    if (
        len(observed_ids) != len(expected)
        or len(set(observed_ids)) != len(observed_ids)
        or set(observed_ids) != set(expected)
    ):
        raise RuntimeError(
            f"{split} result case-ID set/count does not exactly match the corpus"
        )
    expected_rebound = int(spec["execution"]["rebound_cases_per_split"])
    if sum(bool(case.get("rebound_selected")) for case in expected.values()) != expected_rebound:
        raise RuntimeError(f"{split} corpus has the wrong REBOUND case count")

    for case in result_cases:
        case_id = str(case["case_id"])
        if bool(case.get("rebound_selected")) != bool(
            expected[case_id].get("rebound_selected")
        ):
            raise RuntimeError(f"{case_id} REBOUND selection differs from corpus")
        if not isinstance(case.get("success"), bool):
            raise RuntimeError(f"{case_id} lacks an explicit success value")
        required = CASE_METRICS | (
            REBOUND_METRICS if case["rebound_selected"] else set()
        )
        _require_finite_metrics(case.get("metrics"), required, case_id)

    _require_finite_metrics(
        results.get("catalogue_metrics"), CATALOGUE_METRICS, "catalogue"
    )
    _require_finite_metrics(
        results.get("structural"), STRUCTURAL_METRICS, "structural"
    )
    root = results.get("root_native_metrics")
    if split == "development":
        _require_finite_metrics(root, TRAJECTORY_METRICS, "development root")
    elif root is not None:
        raise RuntimeError(f"{split} result unexpectedly contains root metrics")
    return result_cases


def require_new_holdout_evaluation(split: str, output: str | Path) -> None:
    if split == "holdout" and Path(output).resolve().exists():
        raise RuntimeError("refusing to overwrite an existing holdout evaluation")


def _values(cases, name):
    return [float(case["metrics"][name]) for case in cases if name in case["metrics"]]


def _maximum(cases, name, root=None):
    values = _values(cases, name)
    if root is not None and name in root:
        values.append(float(root[name]))
    if not values:
        raise RuntimeError(f"no values available for required maximum metric {name}")
    return max(values)


def _minimum(cases, name, root=None):
    values = _values(cases, name)
    if root is not None and name in root:
        values.append(float(root[name]))
    if not values:
        raise RuntimeError(f"no values available for required minimum metric {name}")
    return min(values)


def _rate(cases, name) -> float:
    values = _values(cases, name)
    if not values:
        raise RuntimeError(f"no values available for required rate metric {name}")
    return sum(values) / len(values)


def _quantile(cases, name, quantile) -> float:
    values = _values(cases, name)
    if not values:
        raise RuntimeError(f"no values available for required quantile metric {name}")
    return float(np.quantile(values, quantile))


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
    split = results.get("split")
    require_new_holdout_evaluation(str(split), args.output)
    if corpus.get("spec_sha256") != sha256_file(args.spec):
        raise RuntimeError("external corpus uses another specification")
    if results["spec_sha256"] != sha256_file(args.spec):
        raise RuntimeError("split result uses another specification")
    if results["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("split result uses another corpus")
    cases = validate_evidence_contract(spec, corpus, results)
    full_lock = None
    if split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout evaluation requires the full qualification lock")
        full_lock = verify_lock(args.lock, ROOT, expected_prefix=spec["campaign"])
        current_runtime = runtime_fingerprint()
        require_full_lock_runtime(full_lock, current_runtime)
        if results.get("runtime") != full_lock["runtime"]:
            raise RuntimeError("holdout result runtime differs from the full lock")
        if full_lock.get("spec_sha256") != sha256_file(args.spec):
            raise RuntimeError("holdout specification differs from full lock")
        if full_lock.get("corpus_sha256") != sha256_file(args.corpus):
            raise RuntimeError("holdout corpus differs from full lock")
        expected_holdout_ids = sorted(
            case["case_id"]
            for case in corpus["cases"]
            if case["split"] == "holdout"
        )
        if full_lock.get("holdout_ids") != expected_holdout_ids:
            raise RuntimeError("holdout corpus case IDs differ from the full lock")
        if results.get("qualification_id") != full_lock["qualification_id"]:
            raise RuntimeError("holdout result qualification ID mismatch")
        if results.get("lock_sha256") != full_lock["lock_sha256"]:
            raise RuntimeError("holdout result full-lock mismatch")

    root = results.get("root_native_metrics")
    catalogue = results["catalogue_metrics"]
    structural = results["structural"]
    gates_spec = spec["gates"]
    closure_position = max(
        float(catalogue["stored_closure_position_scaled_max"]),
        _maximum(cases, "closure_position_scaled", root),
    )
    closure_velocity = max(
        float(catalogue["stored_closure_velocity_scaled_max"]),
        _maximum(cases, "closure_velocity_scaled", root),
    )
    classified_cases = [
        case
        for case in cases
        if case["metrics"]["planar_stability_classified"] == 1.0
    ]
    stability_agreement = (
        _rate(classified_cases, "planar_stability_label_agreement")
        if classified_cases
        else 0.0
    )
    gates = [
        make_gate("case_success_rate", sum(bool(case.get("success")) for case in cases) / len(cases), ">=", 1.0),
        make_gate("rebound_case_count", sum(case.get("rebound_selected", False) for case in cases), "==", spec["execution"]["rebound_cases_per_split"]),
        make_gate("candidate_count", catalogue["candidate_count"], "==", gates_spec["candidate_count"]),
        make_gate("candidate_success_rate", catalogue["candidate_success_rate"], ">=", gates_spec["candidate_success_rate_min"]),
        make_gate("external_seed_count", catalogue["external_seed_count"], "==", gates_spec["external_seed_count"]),
        make_gate("evaluation_row_used_as_seed_count", catalogue["evaluation_row_used_as_seed_count"], "==", gates_spec["evaluation_row_used_as_seed_count"]),
        make_gate("closure_position_scaled_max", closure_position, "<=", gates_spec["closure_position_scaled_max"]),
        make_gate("closure_velocity_scaled_max", closure_velocity, "<=", gates_spec["closure_velocity_scaled_max"]),
        make_gate("relative_energy_drift_max", _maximum(cases, "relative_energy_drift", root), "<=", gates_spec["relative_energy_drift_max"]),
        make_gate("linear_momentum_drift_scaled_max", _maximum(cases, "linear_momentum_drift_scaled", root), "<=", gates_spec["linear_momentum_drift_scaled_max"]),
        make_gate("angular_momentum_drift_scaled_max", _maximum(cases, "angular_momentum_drift_scaled", root), "<=", gates_spec["angular_momentum_drift_scaled_max"]),
        make_gate("minimum_pair_separation_scaled_min", _minimum(cases, "minimum_pair_separation_scaled", root), ">=", gates_spec["minimum_pair_separation_scaled_min"]),
        make_gate("exact_mass_match_rate", _rate(cases, "exact_mass_match"), ">=", gates_spec["exact_mass_match_rate_min"]),
        make_gate("external_parameter_error_p95", _quantile(cases, "external_parameter_error", 0.95), "<=", gates_spec["external_parameter_error_p95_max"]),
        make_gate("external_parameter_error_max", _maximum(cases, "external_parameter_error"), "<=", gates_spec["external_parameter_error_max"]),
        make_gate("external_period_relative_error_p95", _quantile(cases, "external_period_relative_error", 0.95), "<=", gates_spec["external_period_relative_error_p95_max"]),
        make_gate("external_period_relative_error_max", _maximum(cases, "external_period_relative_error"), "<=", gates_spec["external_period_relative_error_max"]),
        make_gate("planar_stability_classified_rate", _rate(cases, "planar_stability_classified"), ">=", gates_spec["planar_stability_classified_rate_min"]),
        make_gate("planar_stability_label_agreement", stability_agreement, ">=", gates_spec["planar_stability_label_agreement_min"]),
        make_gate("monodromy_symplectic_defect_max", catalogue["monodromy_symplectic_defect_max"], "<=", gates_spec["monodromy_symplectic_defect_max"]),
        make_gate("monodromy_reciprocal_pair_error_max", catalogue["monodromy_reciprocal_pair_error_max"], "<=", gates_spec["monodromy_reciprocal_pair_error_max"]),
        make_gate("dop853_rebound_position_error_scaled_max", _maximum(cases, "dop853_rebound_position_error_scaled"), "<=", gates_spec["dop853_rebound_position_error_scaled_max"]),
        make_gate("dop853_rebound_velocity_error_scaled_max", _maximum(cases, "dop853_rebound_velocity_error_scaled"), "<=", gates_spec["dop853_rebound_velocity_error_scaled_max"]),
        make_gate("partition_disjoint_rate", catalogue["partition_disjoint_rate"], ">=", gates_spec["partition_disjoint_rate_min"]),
        make_gate("one_to_one_match_rate", catalogue["one_to_one_match_rate"], ">=", gates_spec["one_to_one_match_rate_min"]),
        make_gate("duplicate_count", catalogue["duplicate_count"], "<=", gates_spec["duplicate_count_max"]),
        make_gate("structural_blind_holdout", structural["structural_blind_holdout"], "==", gates_spec["structural_blind_holdout"]),
        make_gate("structural_independent_root_discovery", structural["structural_independent_root_discovery"], "==", gates_spec["structural_independent_root_discovery"]),
        make_gate("structural_general_n3bp_catalogue", structural["structural_general_n3bp_catalogue"], "==", gates_spec["structural_general_n3bp_catalogue"]),
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
        "rebound_case_count": sum(case.get("rebound_selected", False) for case in cases),
        "gates": gates,
    }
    if full_lock is not None:
        payload["qualification_id"] = full_lock["qualification_id"]
        payload["lock_sha256"] = full_lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    print(
        f"WP1-CAT-N3BP-v1 {split}: {status} "
        f"({sum(gate['passed'] for gate in gates)}/{len(gates)} gates)"
    )


if __name__ == "__main__":
    main()
