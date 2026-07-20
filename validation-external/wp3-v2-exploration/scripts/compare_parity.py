#!/usr/bin/env python
"""Compare local and independent-host WP3 v2 exploration evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    sha256_file,
    utc_now,
)


MODE_METRICS = (
    "training_lie_rms",
    "calibration_lie_rms",
    "calibration_to_training_ratio",
    "training_weighted_value_std",
    "calibration_weighted_value_std",
    "calibration_trajectory_drift_max",
)
CONTROL_METRICS = ("weighted_value_std", "weighted_lie_rms", "lie_max_abs")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--reference-gate", required=True)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--comparison-gate", required=True)
    parser.add_argument("--reference-label", required=True)
    parser.add_argument("--comparison-label", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _check(name: str, passed: bool, **details: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), **details}


def _input_hashes(payload: dict[str, Any]) -> dict[str, Any]:
    names = (
        "spec_sha256",
        "corpus_sha256",
        "spatial_corpus_sha256",
        "spatial_development_sha256",
        "spatial_calibration_sha256",
        "prerequisites",
    )
    return {name: payload[name] for name in names}


def _search_structure(payload: dict[str, Any]) -> dict[str, Any]:
    search = payload["search"]
    names = (
        "feature_count",
        "training_row_count",
        "calibration_row_count",
        "value_rank",
        "value_identity_nullity",
        "known_algebra_declared_count",
        "known_algebra_active_rank",
        "numerical_nullity_at_candidate_threshold",
        "candidate_mode_ranks",
        "candidate_count",
    )
    return {name: search[name] for name in names}


def _gate_decisions(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        stage: {
            "status": payload[stage]["status"],
            "interpretation_authorized": payload[stage].get(
                "interpretation_authorized"
            ),
            "gates": [
                {
                    "name": gate["name"],
                    "comparator": gate["comparator"],
                    "threshold": gate["threshold"],
                    "passed": gate["passed"],
                }
                for gate in payload[stage].get("gates", [])
            ],
        }
        for stage in ("SEARCH_READY", "CANDIDATE_READY", "PUBLICATION_READY")
    }


def _relative_delta(first: float, second: float) -> float:
    return abs(first - second) / max(abs(first), abs(second), 1.0)


def _numeric_deltas(
    reference: dict[str, Any], comparison: dict[str, Any]
) -> dict[str, float]:
    first_search = reference["search"]
    second_search = comparison["search"]
    first_singular = np.asarray(first_search["post_projection_singular_values"])
    second_singular = np.asarray(second_search["post_projection_singular_values"])
    if first_singular.shape != second_singular.shape:
        raise RuntimeError("parity singular-value vectors differ in shape")
    singular_delta = float(
        np.max(
            np.abs(first_singular - second_singular)
            / np.maximum.reduce(
                (
                    np.abs(first_singular),
                    np.abs(second_singular),
                    np.ones_like(first_singular),
                )
            )
        )
    )
    coefficient_relative = 0.0
    coefficient_cosine_min = 1.0
    metric_relative = 0.0
    for first_mode, second_mode in zip(
        first_search["modes"], second_search["modes"], strict=True
    ):
        first = np.asarray(first_mode["coefficients"], dtype=float)
        second = np.asarray(second_mode["coefficients"], dtype=float)
        if float(np.dot(first, second)) < 0.0:
            second = -second
        coefficient_relative = max(
            coefficient_relative,
            float(np.linalg.norm(first - second))
            / max(float(np.linalg.norm(first)), float(np.linalg.norm(second))),
        )
        coefficient_cosine_min = min(
            coefficient_cosine_min,
            float(np.dot(first, second))
            / float(np.linalg.norm(first) * np.linalg.norm(second)),
        )
        metric_relative = max(
            metric_relative,
            *(
                _relative_delta(float(first_mode[name]), float(second_mode[name]))
                for name in MODE_METRICS
            ),
        )
    control_delta = 0.0
    for name, first_metrics in first_search["known_control_metrics"].items():
        second_metrics = second_search["known_control_metrics"][name]
        control_delta = max(
            control_delta,
            *(
                abs(float(first_metrics[metric]) - float(second_metrics[metric]))
                for metric in CONTROL_METRICS
            ),
        )
    return {
        "singular_value_relative_delta_max": singular_delta,
        "mode_coefficient_relative_l2_max": coefficient_relative,
        "mode_coefficient_cosine_min": coefficient_cosine_min,
        "mode_metric_relative_delta_max": metric_relative,
        "known_control_metric_abs_delta_max": control_delta,
    }


def main() -> None:
    args = _args()
    spec = load_json(args.spec)
    reference = load_json(args.reference)
    comparison = load_json(args.comparison)
    reference_gate = load_json(args.reference_gate)
    comparison_gate = load_json(args.comparison_gate)
    checks = [
        _check("input_hashes", _input_hashes(reference) == _input_hashes(comparison)),
        _check(
            "implementation_snapshot",
            reference["implementation_snapshot"]
            == comparison["implementation_snapshot"],
        ),
        _check("matrix_hashes", reference["matrix_hashes"] == comparison["matrix_hashes"]),
        _check("source_summary", reference["source_summary"] == comparison["source_summary"]),
        _check("search_structure", _search_structure(reference) == _search_structure(comparison)),
        _check(
            "staged_gate_decisions",
            _gate_decisions(reference_gate) == _gate_decisions(comparison_gate),
        ),
        _check(
            "sealed_reserve_status",
            reference["sealed_publication_reserve"]
            == comparison["sealed_publication_reserve"],
        ),
    ]
    if {check["name"] for check in checks} != set(spec["required_exact_matches"]):
        raise RuntimeError("parity implementation and exact-match policy differ")
    deltas = _numeric_deltas(reference, comparison)
    for name, observed in deltas.items():
        threshold = float(spec["thresholds"][name])
        if name.endswith("_min"):
            checks.append(_check(name, observed >= threshold, observed=observed, comparator=">=", threshold=threshold))
        else:
            checks.append(_check(name, observed <= threshold, observed=observed, comparator="<=", threshold=threshold))
    status = "PASS" if all(check["passed"] for check in checks) else "FAIL"
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "status": status,
        "spec_sha256": sha256_file(args.spec),
        "implementation_sha256": sha256_file(Path(__file__)),
        "reference": {
            "label": args.reference_label,
            "path": args.reference,
            "sha256": sha256_file(args.reference),
            "runtime": reference["runtime"],
        },
        "comparison": {
            "label": args.comparison_label,
            "path": args.comparison,
            "sha256": sha256_file(args.comparison),
            "runtime": comparison["runtime"],
        },
        "checks": checks,
    }
    atomic_write_json(args.output, payload)
    print(
        f"{spec['campaign']}: {status} "
        f"({sum(check['passed'] for check in checks)}/{len(checks)} checks)"
    )
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
