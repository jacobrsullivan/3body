#!/usr/bin/env python
"""Evaluate one frozen WP1 qualification split against predeclared gates."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qualification_common import (
    as_bool,
    atomic_write_json,
    deterministic_subset,
    load_json,
    load_corpus,
    load_spec,
    maximum,
    percentile,
    rate,
    read_csv,
    repository_root,
    resolve_manifest_path,
    sha256_file,
    verify_qualification_lock,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus-manifest", required=True)
    parser.add_argument("--lock")
    parser.add_argument(
        "--split", required=True, choices=["development", "calibration", "holdout"]
    )
    parser.add_argument("--float64", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--stability", required=True)
    parser.add_argument("--reconstruction", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def add_gate(
    gates: list[dict[str, Any]],
    name: str,
    observed: float | int,
    comparator: str,
    threshold: float | int,
) -> None:
    finite = math.isfinite(float(observed))
    if comparator == ">=":
        passed = finite and observed >= threshold
    elif comparator == "<=":
        passed = finite and observed <= threshold
    elif comparator == "==":
        passed = finite and observed == threshold
    else:  # pragma: no cover - programmer error.
        raise ValueError(f"Unsupported gate comparator: {comparator}")
    gates.append(
        {
            "name": name,
            "observed": observed,
            "comparator": comparator,
            "threshold": threshold,
            "passed": bool(passed),
        }
    )


def summarize_groups(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        key: dict(sorted(Counter(str(row[key]) for row in rows).items()))
        for key in ("system", "family", "stability_regime")
    }


def result_ids(name: str, rows: list[dict[str, Any]]) -> set[str]:
    identifiers = [str(row.get("catalog_id", "")) for row in rows]
    if not identifiers or any(not identifier for identifier in identifiers):
        raise RuntimeError(f"{name} results have missing catalogue identifiers")
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError(f"{name} results contain duplicate catalogue identifiers")
    return set(identifiers)


def validate_result_identity(
    data: dict[str, list[dict[str, Any]]],
    corpus_rows: list[dict[str, Any]],
    spec: dict[str, Any],
    split: str,
) -> None:
    """Prove that every result row is the predeclared deterministic case set."""
    corpus_by_id = {str(row["catalog_id"]): row for row in corpus_rows}
    if len(corpus_by_id) != len(corpus_rows):
        raise RuntimeError(f"Qualification corpus has duplicate IDs in {split}")

    actual = {name: result_ids(name, rows) for name, rows in data.items()}
    corpus_ids = set(corpus_by_id)
    if actual["float64"] != corpus_ids:
        missing = sorted(corpus_ids - actual["float64"])
        unexpected = sorted(actual["float64"] - corpus_ids)
        raise RuntimeError(
            "float64 results do not exactly cover the frozen split: "
            f"missing={missing[:5]}, unexpected={unexpected[:5]}"
        )

    oracle = spec["oracle"]
    expected_oracle = {
        str(row["catalog_id"])
        for row in deterministic_subset(
            corpus_rows,
            int(oracle["maximum_cases"][split]),
            salt=f"oracle:{spec['sampling']['split_salt']}:{split}",
            group_keys=("system", "family", "stability_regime"),
        )
    }
    stability = spec["stability"]
    expected_stability = {
        str(row["catalog_id"])
        for row in deterministic_subset(
            corpus_rows,
            int(stability["maximum_cases"][split]),
            salt=f"stability:{spec['sampling']['split_salt']}:{split}",
            group_keys=("system", "family", "lpoint", "branch", "stability_regime"),
        )
    }

    geometry = {
        str(row["catalog_id"]): float(row["min_secondary_distance_radii"])
        for row in data["float64"]
    }
    reconstruction = spec["reconstruction"]
    eligible = [
        row
        for row in corpus_rows
        if geometry[str(row["catalog_id"])]
        >= float(reconstruction["minimum_secondary_distance_radii"])
        and (
            row["family"] == "lyapunov"
            or (row["family"] == "halo" and abs(float(row["z"])) >= 1e-12)
        )
    ]
    expected_reconstruction = {
        str(row["catalog_id"])
        for row in deterministic_subset(
            eligible,
            int(reconstruction["maximum_cases"][split]),
            salt=f"reconstruction:{spec['sampling']['split_salt']}:{split}",
            group_keys=("system", "family", "lpoint", "branch", "stability_regime"),
        )
    }
    expected = {
        "float64": corpus_ids,
        "oracle": expected_oracle,
        "stability": expected_stability,
        "reconstruction": expected_reconstruction,
    }
    for name, expected_ids in expected.items():
        if actual[name] != expected_ids:
            missing = sorted(expected_ids - actual[name])
            unexpected = sorted(actual[name] - expected_ids)
            raise RuntimeError(
                f"{name} results do not match the deterministic case set: "
                f"missing={missing[:5]}, unexpected={unexpected[:5]}"
            )
        for row in data[name]:
            source = corpus_by_id[str(row["catalog_id"])]
            for field in ("system", "family", "stability_regime"):
                if str(row.get(field)) != str(source[field]):
                    raise RuntimeError(
                        f"{name} result {row['catalog_id']} has altered {field} metadata"
                    )


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    spec = load_spec(spec_path)
    corpus_manifest = load_json(args.corpus_manifest)
    if corpus_manifest["spec_sha256"] != sha256_file(spec_path):
        raise RuntimeError("Qualification corpus and current spec hashes differ")
    corpus_path = resolve_manifest_path(
        args.corpus_manifest, corpus_manifest["corpus_path"]
    )
    if sha256_file(corpus_path) != corpus_manifest["corpus_sha256"]:
        raise RuntimeError("Qualification corpus content does not match its manifest")
    lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("Holdout evaluation requires a qualification lock")
        lock = verify_qualification_lock(args.lock, repository_root(spec_path))
        if lock["spec_sha256"] != sha256_file(spec_path):
            raise RuntimeError("Holdout spec does not match frozen qualification lock")
        if lock["corpus_manifest_sha256"] != sha256_file(args.corpus_manifest):
            raise RuntimeError(
                "Holdout corpus does not match frozen qualification lock"
            )
        if lock["corpus_sha256"] != corpus_manifest["corpus_sha256"]:
            raise RuntimeError(
                "Holdout corpus hash does not match frozen qualification lock"
            )

    paths = {
        "float64": Path(args.float64).resolve(),
        "oracle": Path(args.oracle).resolve(),
        "stability": Path(args.stability).resolve(),
        "reconstruction": Path(args.reconstruction).resolve(),
    }
    data = {name: read_csv(path) for name, path in paths.items()}
    for name, rows in data.items():
        if any(row.get("split") != args.split for row in rows):
            raise RuntimeError(f"{name} results contain rows outside {args.split}")
    corpus_rows = load_corpus(corpus_path, args.split)
    validate_result_identity(data, corpus_rows, spec, args.split)

    gates: list[dict[str, Any]] = []
    float_rows = data["float64"]
    float_config = spec["float64"]
    float_gates = float_config["gates"]
    add_gate(
        gates,
        "float64.minimum_cases",
        len(float_rows),
        ">=",
        int(float_config["minimum_cases"][args.split]),
    )
    add_gate(
        gates,
        "float64.integration_success_rate",
        rate(row["integration_success"] for row in float_rows),
        ">=",
        float(float_gates["integration_success_rate_min"]),
    )
    add_gate(
        gates,
        "float64.jacobi_catalog_delta_p95",
        percentile((row["jacobi_catalog_delta"] for row in float_rows), 95),
        "<=",
        float(float_gates["jacobi_catalog_delta_p95_max"]),
    )
    add_gate(
        gates,
        "float64.jacobi_catalog_delta_max",
        maximum(row["jacobi_catalog_delta"] for row in float_rows),
        "<=",
        float(float_gates["jacobi_catalog_delta_max"]),
    )
    add_gate(
        gates,
        "float64.jacobi_max_drift_p95",
        percentile((row["jacobi_max_drift"] for row in float_rows), 95),
        "<=",
        float(float_gates["jacobi_max_drift_p95_max"]),
    )
    add_gate(
        gates,
        "float64.jacobi_max_drift_max",
        maximum(row["jacobi_max_drift"] for row in float_rows),
        "<=",
        float(float_gates["jacobi_max_drift_max"]),
    )
    add_gate(
        gates,
        "float64.frame_roundtrip_max",
        maximum(row["frame_roundtrip_error"] for row in float_rows),
        "<=",
        float(float_gates["frame_roundtrip_max"]),
    )
    add_gate(
        gates,
        "float64.reversibility_error_p95",
        percentile((row["reversibility_error"] for row in float_rows), 95),
        "<=",
        float(float_gates["reversibility_error_p95_max"]),
    )
    add_gate(
        gates,
        "float64.reversibility_error_max",
        maximum(row["reversibility_error"] for row in float_rows),
        "<=",
        float(float_gates["reversibility_error_max"]),
    )
    oracle_rows = data["oracle"]
    oracle_config = spec["oracle"]
    oracle_gates = oracle_config["gates"]
    add_gate(
        gates,
        "oracle.minimum_cases",
        len(oracle_rows),
        ">=",
        int(oracle_config["minimum_cases"][args.split]),
    )
    add_gate(
        gates,
        "oracle.success_rate",
        rate(row["success"] for row in oracle_rows),
        ">=",
        float(oracle_gates["success_rate_min"]),
    )
    add_gate(
        gates,
        "oracle.high_precision_jacobi_drift_p95",
        percentile((row["high_precision_jacobi_drift"] for row in oracle_rows), 95),
        "<=",
        float(oracle_gates["high_precision_jacobi_drift_p95_max"]),
    )
    add_gate(
        gates,
        "oracle.high_precision_jacobi_drift_max",
        maximum(row["high_precision_jacobi_drift"] for row in oracle_rows),
        "<=",
        float(oracle_gates["high_precision_jacobi_drift_max"]),
    )
    add_gate(
        gates,
        "oracle.checkpoint_state_error_p95",
        percentile((row["checkpoint_state_error_p95"] for row in oracle_rows), 95),
        "<=",
        float(oracle_gates["checkpoint_state_error_p95_max"]),
    )
    add_gate(
        gates,
        "oracle.checkpoint_state_error_max",
        maximum(row["checkpoint_state_error_max"] for row in oracle_rows),
        "<=",
        float(oracle_gates["checkpoint_state_error_max"]),
    )

    stability_rows = data["stability"]
    stability_config = spec["stability"]
    stability_gates = stability_config["gates"]
    add_gate(
        gates,
        "stability.minimum_cases",
        len(stability_rows),
        ">=",
        int(stability_config["minimum_cases"][args.split]),
    )
    add_gate(
        gates,
        "stability.success_rate",
        rate(row["success"] for row in stability_rows),
        ">=",
        float(stability_gates["success_rate_min"]),
    )
    add_gate(
        gates,
        "stability.relative_index_error_p95",
        percentile((row["relative_index_error"] for row in stability_rows), 95),
        "<=",
        float(stability_gates["relative_index_error_p95_max"]),
    )
    add_gate(
        gates,
        "stability.relative_index_error_max",
        maximum(row["relative_index_error"] for row in stability_rows),
        "<=",
        float(stability_gates["relative_index_error_max"]),
    )
    add_gate(
        gates,
        "stability.classification_accuracy",
        rate(row["classification_match"] for row in stability_rows),
        ">=",
        float(stability_gates["classification_accuracy_min"]),
    )
    add_gate(
        gates,
        "stability.monodromy_determinant_error_max",
        maximum(row["monodromy_determinant_error"] for row in stability_rows),
        "<=",
        float(stability_gates["monodromy_determinant_error_max"]),
    )
    add_gate(
        gates,
        "stability.reciprocal_pair_error_max",
        maximum(row["reciprocal_pair_error"] for row in stability_rows),
        "<=",
        float(stability_gates["reciprocal_pair_error_max"]),
    )

    reconstruction_rows = data["reconstruction"]
    reconstruction_config = spec["reconstruction"]
    reconstruction_gates = reconstruction_config["gates"]
    successful_reconstructions = [
        row for row in reconstruction_rows if as_bool(row["success"])
    ]
    add_gate(
        gates,
        "reconstruction.minimum_cases",
        len(reconstruction_rows),
        ">=",
        int(reconstruction_config["minimum_cases"][args.split]),
    )
    add_gate(
        gates,
        "reconstruction.success_rate",
        rate(row["success"] for row in reconstruction_rows),
        ">=",
        float(reconstruction_gates["success_rate_min"]),
    )
    add_gate(
        gates,
        "reconstruction.closure_error_p95",
        percentile((row["closure_error"] for row in successful_reconstructions), 95),
        "<=",
        float(reconstruction_gates["closure_error_p95_max"]),
    )
    add_gate(
        gates,
        "reconstruction.closure_error_max",
        maximum(row["closure_error"] for row in successful_reconstructions),
        "<=",
        float(reconstruction_gates["closure_error_max"]),
    )
    add_gate(
        gates,
        "reconstruction.symmetry_residual_p95",
        percentile(
            (row["symmetry_residual"] for row in successful_reconstructions), 95
        ),
        "<=",
        float(reconstruction_gates["symmetry_residual_p95_max"]),
    )

    declared_systems = set(spec["external_source"]["systems"])
    declared_families = {"lyapunov", "halo"}
    declared_regimes = set(spec["sampling"]["stability_regimes"])
    for name, rows in data.items():
        add_gate(
            gates,
            f"coverage.{name}.declared_systems",
            len({row["system"] for row in rows}.intersection(declared_systems)),
            "==",
            len(declared_systems),
        )
        add_gate(
            gates,
            f"coverage.{name}.declared_families",
            len({row["family"] for row in rows}.intersection(declared_families)),
            "==",
            len(declared_families),
        )
        add_gate(
            gates,
            f"coverage.{name}.stability_regimes",
            len({row["stability_regime"] for row in rows}),
            "==",
            len(declared_regimes),
        )

    result = {
        "schema_version": "1.0",
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "split": args.split,
        "status": "PASS" if all(gate["passed"] for gate in gates) else "FAIL",
        "spec_sha256": sha256_file(spec_path),
        "corpus_manifest_sha256": sha256_file(args.corpus_manifest),
        "qualification_id": lock["qualification_id"] if lock else None,
        "lock_sha256": lock["lock_sha256"] if lock else None,
        "input_hashes": {name: sha256_file(path) for name, path in paths.items()},
        "case_counts": {name: len(rows) for name, rows in data.items()},
        "group_coverage": summarize_groups(float_rows),
        "result_group_coverage": {
            name: summarize_groups(rows) for name, rows in data.items()
        },
        "gates": gates,
    }
    atomic_write_json(args.output, result)
    failed = [gate for gate in gates if not gate["passed"]]
    print(f"{args.split} qualification: {result['status']} ({len(gates)} gates)")
    for gate in failed:
        print(
            f"FAIL {gate['name']}: {gate['observed']} {gate['comparator']} "
            f"{gate['threshold']}",
            flush=True,
        )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
