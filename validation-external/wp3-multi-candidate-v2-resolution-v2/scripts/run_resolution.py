#!/usr/bin/env python
"""Execute corrected observable-space resolution of the WP3 v2 candidate."""

from __future__ import annotations

import argparse
from fractions import Fraction
from pathlib import Path
import sys
from typing import Any

import mpmath
import numpy as np
from numpy.typing import NDArray


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution-v2"
SOURCE_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
V1_RESOLUTION_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from validation_external_import import campaign_module  # noqa: E402
from src.python.wp3_exploration_v3.search import balanced_row_weights  # noqa: E402
from src.python.wp3_multi_v2 import (  # noqa: E402
    angular_momentum_squared_coefficients,
    structural_zero_feature_indices,
)


FloatArray = NDArray[np.float64]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--challenge-corpus", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _load_common():
    return campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp3_multi_v2_resolution_v2_common_run",
    )


def _load_v1_runner():
    return campaign_module(
        V1_RESOLUTION_ROOT / "scripts/run_resolution.py",
        "_wp3_multi_v2_resolution_v2_v1_runner",
    )


def _load_feature_reference():
    return campaign_module(
        V1_RESOLUTION_ROOT / "reference/mpmath_features.py",
        "_wp3_multi_v2_resolution_v2_feature_reference",
    )


def _load_physical_reference():
    return campaign_module(
        CAMPAIGN_ROOT / "reference/physical_l2.py",
        "_wp3_multi_v2_resolution_v2_physical_reference",
    )


def fit_zero_intercept_scale(
    candidate: FloatArray,
    known: FloatArray,
    weights: FloatArray,
) -> float:
    denominator = float(np.sum(weights * np.square(known)))
    if denominator <= np.finfo(float).tiny:
        raise ValueError("known response has zero weighted norm")
    return float(np.sum(weights * candidate * known) / denominator)


def relative_weighted_rms(
    residual: FloatArray,
    reference: FloatArray,
    weights: FloatArray,
) -> float:
    numerator = float(np.sqrt(np.sum(weights * np.square(residual))))
    denominator = float(np.sqrt(np.sum(weights * np.square(reference))))
    return numerator / max(denominator, np.finfo(float).tiny)


def centered_response_projection(
    first: FloatArray,
    second: FloatArray,
    weights: FloatArray,
) -> float:
    first_centered = first - float(np.sum(weights * first))
    second_centered = second - float(np.sum(weights * second))
    numerator = abs(float(np.sum(weights * first_centered * second_centered)))
    first_norm = float(np.sqrt(np.sum(weights * np.square(first_centered))))
    second_norm = float(np.sqrt(np.sum(weights * np.square(second_centered))))
    return numerator / max(first_norm * second_norm, np.finfo(float).tiny)


def _split_metrics(
    values: FloatArray,
    derivatives: FloatArray,
    coefficients: FloatArray,
    known_coefficients: FloatArray,
    weights: FloatArray,
    held_scale: float,
) -> dict[str, float]:
    candidate = values @ coefficients
    known = values @ known_coefficients
    candidate_lie = derivatives @ coefficients
    known_lie = derivatives @ known_coefficients
    value_residual = candidate - held_scale * known
    lie_residual = candidate_lie - held_scale * known_lie
    fitted_scale = fit_zero_intercept_scale(candidate, known, weights)
    centered = candidate - float(np.sum(weights * candidate))
    return {
        "fitted_scale": fitted_scale,
        "held_scale_relative_value_rms": relative_weighted_rms(
            value_residual, candidate, weights
        ),
        "held_scale_lie_rms": float(
            np.sqrt(np.sum(weights * np.square(lie_residual)))
        ),
        "held_scale_lie_abs_max": float(np.max(np.abs(lie_residual))),
        "candidate_value_std": float(
            np.sqrt(np.sum(weights * np.square(centered)))
        ),
    }


def _physical_l2_binary(case: dict[str, Any]) -> float:
    positions = np.asarray(
        [[float(Fraction(value)) for value in row] for row in case["positions"]],
        dtype=np.float64,
    )
    velocities = np.asarray(
        [[float(Fraction(value)) for value in row] for row in case["velocities"]],
        dtype=np.float64,
    )
    masses = np.asarray(
        [float(Fraction(value)) for value in case["masses"]], dtype=np.float64
    )
    angular = np.sum(np.cross(positions, masses[:, None] * velocities), axis=0)
    return float(np.dot(angular, angular))


def _raw_cosine(first: FloatArray, second: FloatArray) -> float:
    return abs(float(np.dot(first, second))) / max(
        float(np.linalg.norm(first)) * float(np.linalg.norm(second)),
        np.finfo(float).tiny,
    )


def _direction_summary(
    values_by_split: dict[str, FloatArray],
    derivatives_by_split: dict[str, FloatArray],
    weights_by_split: dict[str, FloatArray],
    coefficients: FloatArray,
    known_coefficients: FloatArray,
) -> dict[str, Any]:
    training_values = values_by_split["training"]
    training_weights = weights_by_split["training"]
    training_scale = fit_zero_intercept_scale(
        training_values @ coefficients,
        training_values @ known_coefficients,
        training_weights,
    )
    splits = {
        name: _split_metrics(
            values_by_split[name],
            derivatives_by_split[name],
            coefficients,
            known_coefficients,
            weights_by_split[name],
            training_scale,
        )
        for name in values_by_split
    }
    scale_spread = max(
        abs(metrics["fitted_scale"] - training_scale)
        / max(abs(training_scale), np.finfo(float).tiny)
        for metrics in splits.values()
    )
    return {
        "training_scale": training_scale,
        "split_scale_relative_spread": scale_spread,
        "raw_coefficient_cosine_to_l2": _raw_cosine(
            coefficients, known_coefficients
        ),
        "splits": splits,
    }


def _aggregate_metric(
    summaries: dict[str, dict[str, Any]], split: str, field: str
) -> float:
    return max(
        float(summary["splits"][split][field]) for summary in summaries.values()
    )


def _high_precision_checks(
    challenge: dict[str, Any],
    committed: FloatArray,
    known: FloatArray,
    held_scale: float,
) -> dict[str, Any]:
    feature_reference = _load_feature_reference()
    physical_reference = _load_physical_reference()
    v1_runner = _load_v1_runner()
    known_relative_max = 0.0
    production_candidate_difference_max = 0.0
    candidate_residual_squared = mpmath.mpf("0")
    candidate_squared = mpmath.mpf("0")
    with mpmath.workdps(80):
        committed_mp = [mpmath.mpf(float(value)) for value in committed]
        known_mp = [mpmath.mpf(float(value)) for value in known]
        scale_mp = mpmath.mpf(float(held_scale))
        for case in challenge["cases"]:
            feature_values, _ = feature_reference.evaluate(case, dps=80)
            physical = physical_reference.evaluate(case, dps=80)
            known_value = mpmath.fsum(
                coefficient * value
                for coefficient, value in zip(known_mp, feature_values, strict=True)
            )
            candidate_value = mpmath.fsum(
                coefficient * value
                for coefficient, value in zip(
                    committed_mp, feature_values, strict=True
                )
            )
            known_relative_max = max(
                known_relative_max,
                float(abs(known_value - physical) / max(mpmath.mpf("1"), abs(physical))),
            )
            residual = candidate_value - scale_mp * physical
            candidate_residual_squared += residual * residual
            candidate_squared += candidate_value * candidate_value
            production_values, _ = v1_runner._challenge_production(case)
            production_candidate = float(production_values @ committed)
            production_candidate_difference_max = max(
                production_candidate_difference_max,
                abs(production_candidate - float(candidate_value))
                / max(1.0, abs(float(candidate_value))),
            )
        candidate_relative_rms = float(
            mpmath.sqrt(candidate_residual_squared / candidate_squared)
        )
    reference_source = (
        CAMPAIGN_ROOT / "reference/physical_l2.py"
    ).read_text(encoding="utf-8")
    return {
        "decimal_digits": 80,
        "physical_reference": "source-disjoint exact-rational mpmath q cross p",
        "physical_reference_sha256": sha256_file(
            CAMPAIGN_ROOT / "reference/physical_l2.py"
        ),
        "production_import_absent": "src.python" not in reference_source,
        "feature_l2_physical_relative_difference_max": known_relative_max,
        "candidate_l2_relative_value_rms": candidate_relative_rms,
        "production_mpmath_candidate_relative_difference_max": (
            production_candidate_difference_max
        ),
    }


def main() -> None:
    args = _args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite one-shot corrected resolution")
    common = _load_common()
    v1_runner = _load_v1_runner()
    spec = load_json(args.spec)
    challenge = load_json(args.challenge_corpus)
    specification_lock = common.verify_specification_lock(args.spec)
    prerequisites = common.verify_prerequisites(spec)
    reserve_before = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or lock.get("challenge_corpus_sha256") != sha256_file(args.challenge_corpus)
        or lock.get("corrected_interpretation_before_implementation_lock") is not False
    ):
        raise RuntimeError("corrected implementation lock does not bind inputs")

    source_results = load_json(SOURCE_ROOT / "results/search_results.json")
    mode = next(item for item in source_results["search"]["modes"] if item["rank"] == 1)
    committed = np.asarray(mode["coefficients"], dtype=np.float64)
    known = angular_momentum_squared_coefficients()
    v1_spec = load_json(V1_RESOLUTION_ROOT / "qualification_spec.json")
    training, calibration = v1_runner._rebuild_source_rows(v1_spec)
    rebuilt_hashes = {
        "training_values_full": v1_runner._matrix_sha256(training.values),
        "training_derivatives_full": v1_runner._matrix_sha256(training.derivatives),
        "calibration_values_full": v1_runner._matrix_sha256(calibration.values),
        "calibration_derivatives_full": v1_runner._matrix_sha256(
            calibration.derivatives
        ),
    }
    matrix_identity = rebuilt_hashes == source_results["matrix_hashes"]
    if not matrix_identity:
        raise RuntimeError("corrected resolution failed source matrix byte identity")

    challenge_values = []
    challenge_derivatives = []
    physical_l2 = []
    for case in challenge["cases"]:
        values, derivatives = v1_runner._challenge_production(case)
        challenge_values.append(values)
        challenge_derivatives.append(derivatives)
        physical_l2.append(_physical_l2_binary(case))
    challenge_values_array = np.stack(challenge_values)
    challenge_derivatives_array = np.stack(challenge_derivatives)
    physical_l2_array = np.asarray(physical_l2, dtype=np.float64)

    zero_indices = np.asarray(structural_zero_feature_indices(), dtype=np.int64)
    active_mask = np.ones(committed.size, dtype=bool)
    active_mask[zero_indices] = False
    active_indices = np.flatnonzero(active_mask)
    source_search_spec = load_json(SOURCE_ROOT / "search_spec.json")["search"]
    replications = [
        v1_runner.generalized_direction(
            training.values[:, active_indices],
            training.derivatives[:, active_indices],
            training.group_ids,
            training.family_ids,
            known[active_indices],
            driver=driver,
            value_rank_relative_tolerance=float(
                source_search_spec["value_rank_relative_tolerance"]
            ),
        )
        for driver in ("numpy", "gesdd", "gesvd")
    ]
    directions = {"committed": committed}
    backend_metadata = []
    for replication in replications:
        full = np.zeros_like(committed)
        full[active_indices] = replication["raw_coefficients"]
        driver = str(replication["driver"])
        directions[driver] = full
        backend_metadata.append(
            {
                "driver": driver,
                "generalized_singular_value": replication[
                    "generalized_singular_value"
                ],
                "value_rank": replication["value_rank"],
                "value_nuisance_nullity": replication["value_nuisance_nullity"],
                "value_nuisance_derivative_rank": replication[
                    "value_nuisance_derivative_rank"
                ],
            }
        )

    values_by_split = {
        "training": training.values,
        "calibration": calibration.values,
        "challenge": challenge_values_array,
    }
    derivatives_by_split = {
        "training": training.derivatives,
        "calibration": calibration.derivatives,
        "challenge": challenge_derivatives_array,
    }
    weights_by_split = {
        "training": balanced_row_weights(training.group_ids, training.family_ids),
        "calibration": balanced_row_weights(
            calibration.group_ids, calibration.family_ids
        ),
        "challenge": np.full(
            challenge_values_array.shape[0],
            1.0 / challenge_values_array.shape[0],
            dtype=np.float64,
        ),
    }
    direction_summaries = {
        name: _direction_summary(
            values_by_split,
            derivatives_by_split,
            weights_by_split,
            coefficients,
            known,
        )
        for name, coefficients in directions.items()
    }
    committed_responses = {
        split: values @ committed for split, values in values_by_split.items()
    }
    response_projections = []
    for name, coefficients in directions.items():
        if name == "committed":
            continue
        for split, values in values_by_split.items():
            response_projections.append(
                {
                    "driver": name,
                    "split": split,
                    "projection": centered_response_projection(
                        committed_responses[split],
                        values @ coefficients,
                        weights_by_split[split],
                    ),
                }
            )
    response_projection_min = min(
        item["projection"] for item in response_projections
    )

    feature_l2 = challenge_values_array @ known
    production_physical_l2_relative_max = float(
        np.max(
            np.abs(feature_l2 - physical_l2_array)
            / np.maximum(1.0, np.abs(physical_l2_array))
        )
    )
    committed_scale = float(direction_summaries["committed"]["training_scale"])
    independent_precision = _high_precision_checks(
        challenge, committed, known, committed_scale
    )

    thresholds = spec["thresholds"]
    training_relative_max = _aggregate_metric(
        direction_summaries, "training", "held_scale_relative_value_rms"
    )
    calibration_relative_max = _aggregate_metric(
        direction_summaries, "calibration", "held_scale_relative_value_rms"
    )
    challenge_relative_max = _aggregate_metric(
        direction_summaries, "challenge", "held_scale_relative_value_rms"
    )
    scale_spread_max = max(
        float(summary["split_scale_relative_spread"])
        for summary in direction_summaries.values()
    )
    lie_rms_max = max(
        _aggregate_metric(direction_summaries, split, "held_scale_lie_rms")
        for split in values_by_split
    )
    lie_abs_max = max(
        _aggregate_metric(direction_summaries, split, "held_scale_lie_abs_max")
        for split in values_by_split
    )
    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate("implementation_lock_verified", 1, "==", 1),
        make_gate("superseded_v1_assessment_verified", 1, "==", 1),
        make_gate("source_matrix_byte_identity", int(matrix_identity), "==", 1),
        make_gate(
            "publication_reserve_intact_before",
            int(reserve_before["status"] == "SEALED_UNEXECUTED"),
            "==",
            1,
        ),
        make_gate(
            "training_candidate_l2_relative_value_rms_max",
            training_relative_max,
            "<=",
            float(thresholds["training_candidate_l2_relative_value_rms_max"]),
        ),
        make_gate(
            "calibration_candidate_l2_relative_value_rms_max",
            calibration_relative_max,
            "<=",
            float(thresholds["calibration_candidate_l2_relative_value_rms_max"]),
        ),
        make_gate(
            "challenge_candidate_l2_relative_value_rms_max",
            challenge_relative_max,
            "<=",
            float(thresholds["challenge_candidate_l2_relative_value_rms_max"]),
        ),
        make_gate(
            "split_scale_relative_spread_max",
            scale_spread_max,
            "<=",
            float(thresholds["split_scale_relative_spread_max"]),
        ),
        make_gate(
            "held_scale_lie_rms_max",
            lie_rms_max,
            "<=",
            float(thresholds["held_scale_lie_rms_max"]),
        ),
        make_gate(
            "held_scale_lie_abs_max",
            lie_abs_max,
            "<=",
            float(thresholds["held_scale_lie_abs_max"]),
        ),
        make_gate(
            "backend_centered_response_projection_min",
            response_projection_min,
            ">=",
            float(thresholds["backend_centered_response_projection_min"]),
        ),
        make_gate(
            "backend_l2_relative_value_rms_max",
            max(training_relative_max, calibration_relative_max, challenge_relative_max),
            "<=",
            float(thresholds["backend_l2_relative_value_rms_max"]),
        ),
        make_gate(
            "production_physical_l2_relative_difference_max",
            production_physical_l2_relative_max,
            "<=",
            float(thresholds["production_physical_l2_relative_difference_max"]),
        ),
        make_gate(
            "mpmath_feature_physical_l2_relative_difference_max",
            independent_precision[
                "feature_l2_physical_relative_difference_max"
            ],
            "<=",
            float(
                thresholds["mpmath_feature_physical_l2_relative_difference_max"]
            ),
        ),
        make_gate(
            "mpmath_candidate_l2_relative_value_rms_max",
            independent_precision["candidate_l2_relative_value_rms"],
            "<=",
            float(thresholds["mpmath_candidate_l2_relative_value_rms_max"]),
        ),
    ]
    scientific_gates_pass = all(gate["passed"] for gate in gates)
    decision = (
        "KNOWN_L2_FUNCTION_EQUIVALENCE"
        if scientific_gates_pass
        else "UNRESOLVED"
    )
    reserve_after = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": decision,
        "decision": decision,
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "challenge_corpus_sha256": sha256_file(args.challenge_corpus),
        "runtime": runtime_fingerprint(),
        "prerequisites": prerequisites,
        "candidate_access": {
            "prior_access_disclosed": True,
            "corrected_interpretation_after_implementation_lock": True,
            "source_mode_rank": 1,
        },
        "source_matrix_hashes": rebuilt_hashes,
        "direction_summaries": direction_summaries,
        "backend_replication": {
            "metadata": backend_metadata,
            "response_projections": response_projections,
            "centered_response_projection_min": response_projection_min,
        },
        "physical_l2": {
            "production_feature_physical_relative_difference_max": (
                production_physical_l2_relative_max
            ),
            "challenge_case_count": len(challenge["cases"]),
        },
        "independent_precision": independent_precision,
        "aggregate_metrics": {
            "training_relative_value_rms_max": training_relative_max,
            "calibration_relative_value_rms_max": calibration_relative_max,
            "challenge_relative_value_rms_max": challenge_relative_max,
            "split_scale_relative_spread_max": scale_spread_max,
            "held_scale_lie_rms_max": lie_rms_max,
            "held_scale_lie_abs_max": lie_abs_max,
        },
        "gates": gates,
        "scientific_gates_pass": scientific_gates_pass,
        "claim_boundary": spec["evidence_boundary"],
        "publication_reserve_before": reserve_before,
        "publication_reserve_after": reserve_after,
        "publication_reserve_accessed": False,
        "next_action": (
            "Freeze and execute a successor search that removes the full observable "
            "L^2 equivalence class before making any bounded-null claim."
            if decision == "KNOWN_L2_FUNCTION_EQUIVALENCE"
            else "Preserve the WP3 v2 spectral candidate as unresolved and keep the "
            "publication reserve sealed."
        ),
    }
    atomic_write_json(destination, payload)
    print(
        f"{spec['campaign']}: {decision}; "
        f"response_projection_min={response_projection_min:.12f}; "
        f"challenge_relative_rms_max={challenge_relative_max:.6e}; "
        "reserve=SEALED_UNEXECUTED"
    )


if __name__ == "__main__":
    main()
