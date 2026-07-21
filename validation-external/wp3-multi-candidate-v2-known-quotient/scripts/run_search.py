#!/usr/bin/env python
"""Execute the frozen WP3 observable-known-quotient successor search."""

from __future__ import annotations

import argparse
from fractions import Fraction
from pathlib import Path
import sys
from typing import Any

import numpy as np
from numpy.typing import NDArray


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-known-quotient"
SOURCE_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
V1_RESOLUTION_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution"
CHALLENGE_PATH = (
    VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution/data/challenge_corpus.json"
)
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
from src.python.wp3_exploration_v4 import (  # noqa: E402
    KnownQuotientFit,
    fit_known_quotient_spectrum,
)
from src.python.wp3_multi_v2 import (  # noqa: E402
    angular_momentum_squared_coefficients,
    structural_zero_feature_indices,
)


FloatArray = NDArray[np.float64]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _load_common():
    return campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp3_multi_v2_kq_common_run",
    )


def _load_source_runner():
    return campaign_module(
        V1_RESOLUTION_ROOT / "scripts/run_resolution.py",
        "_wp3_multi_v2_kq_source_runner",
    )


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


def _known_lie_metric(
    derivatives: FloatArray,
    weights: FloatArray,
    known: FloatArray,
    scales: FloatArray,
) -> float:
    response = derivatives @ known
    coefficient_scale = max(
        float(np.linalg.norm(scales * known)), np.finfo(float).tiny
    )
    return float(np.sqrt(np.sum(weights * np.square(response)))) / coefficient_scale


def _fit_summary(fit: KnownQuotientFit) -> dict[str, Any]:
    return {
        "driver": fit.driver,
        "value_rank": fit.value_rank,
        "value_nuisance_nullity": fit.value_nuisance_nullity,
        "value_nuisance_derivative_rank": fit.value_nuisance_derivative_rank,
        "known_observable_rank": fit.known_observable_rank,
        "known_response_projection_residual": (
            fit.known_response_projection_residual
        ),
        "known_response_norm": fit.known_response_norm,
        "mode_known_response_projection_max": (
            fit.mode_known_response_projection_max
        ),
        "generalized_spectral_uncertainty": (
            fit.generalized_spectral_uncertainty
        ),
        "generalized_singular_values": (
            fit.generalized_singular_values.tolist()
        ),
        "reconstructed_lie_rms": fit.reconstructed_lie_rms.tolist(),
        "mode_count": len(fit.raw_coefficients),
        "clusters": [
            {
                "first_rank": start + 1,
                "last_rank": end,
                "dimension": end - start,
                "minimum": float(fit.generalized_singular_values[start]),
                "maximum": float(fit.generalized_singular_values[end - 1]),
            }
            for start, end in fit.generalized_clusters
        ],
    }


def _domain_summary(
    name: str,
    fits: list[KnownQuotientFit],
    active_indices: FloatArray,
    full_feature_count: int,
    candidate_threshold: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    value_ranks = [fit.value_rank for fit in fits]
    mode_counts = [len(fit.raw_coefficients) for fit in fits]
    rank_consistent = len(set(value_ranks)) == 1 and len(set(mode_counts)) == 1
    smallest = [float(fit.generalized_singular_values[0]) for fit in fits]
    relative_spread = (max(smallest) - min(smallest)) / max(
        max(smallest), np.finfo(float).tiny
    )
    guarded_lower = min(
        max(0.0, value - fit.generalized_spectral_uncertainty)
        for value, fit in zip(smallest, fits, strict=True)
    )
    primary = next(fit for fit in fits if fit.driver == "numpy")
    candidate_clusters: list[dict[str, Any]] = []
    if rank_consistent:
        for cluster_index, (start, end) in enumerate(
            primary.generalized_clusters, start=1
        ):
            rank_guarded_lower = min(
                max(
                    0.0,
                    float(fit.generalized_singular_values[start])
                    - fit.generalized_spectral_uncertainty,
                )
                for fit in fits
            )
            if rank_guarded_lower > candidate_threshold:
                continue
            coefficient_rows = []
            for mode_index in range(start, end):
                full = np.zeros(full_feature_count, dtype=np.float64)
                full[np.asarray(active_indices, dtype=np.int64)] = (
                    primary.raw_coefficients[mode_index]
                )
                coefficient_rows.append(
                    {
                        "rank": mode_index + 1,
                        "coefficients": full.tolist(),
                    }
                )
            candidate_clusters.append(
                {
                    "domain": name,
                    "cluster": cluster_index,
                    "first_rank": start + 1,
                    "last_rank": end,
                    "dimension": end - start,
                    "backend_guarded_lower_bound": rank_guarded_lower,
                    "status": "REQUIRES_CANDIDATE_SPECIFIC_RESOLUTION",
                    "directions": coefficient_rows,
                }
            )
    summary = {
        "domain": name,
        "backend_value_ranks": dict(
            zip((fit.driver for fit in fits), value_ranks, strict=True)
        ),
        "backend_mode_counts": dict(
            zip((fit.driver for fit in fits), mode_counts, strict=True)
        ),
        "backend_value_rank_consistent": rank_consistent,
        "backend_smallest_generalized_values": dict(
            zip((fit.driver for fit in fits), smallest, strict=True)
        ),
        "backend_smallest_generalized_relative_spread": relative_spread,
        "backend_guarded_lower_bound": guarded_lower,
        "candidate_threshold": candidate_threshold,
        "certifies_no_eligible_direction": (
            rank_consistent and guarded_lower > candidate_threshold
        ),
        "known_response_projection_residual_max": max(
            fit.known_response_projection_residual for fit in fits
        ),
        "mode_known_response_projection_max": max(
            fit.mode_known_response_projection_max for fit in fits
        ),
        "fits": [_fit_summary(fit) for fit in fits],
        "candidate_cluster_count": len(candidate_clusters),
        "candidate_direction_count": sum(
            int(cluster["dimension"]) for cluster in candidate_clusters
        ),
    }
    return summary, candidate_clusters


def _metric_maxima(training: Any, calibration: Any) -> dict[str, float]:
    return {
        field: max(float(getattr(training, field)), float(getattr(calibration, field)))
        for field in (
            "fixed_energy_abs_max",
            "chart_projection_scaled_max",
            "gauge_orbit_spread_max",
            "chart_overlap_spread_max",
            "body_permutation_spread_max",
            "rotation_spread_max",
            "energy_control_relative_lie_max",
            "angular_momentum_squared_relative_error_max",
            "wp2_pushforward_tangent_relative_error_max",
            "wp2_time_rate_relative_error_max",
        )
    }


def main() -> None:
    args = _args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite one-shot known-quotient search")
    common = _load_common()
    source_runner = _load_source_runner()
    spec = load_json(args.spec)
    specification_lock = common.verify_specification_lock(args.spec)
    prerequisites = common.verify_prerequisites(spec)
    observed_runtime = common.verify_decision_runtime(spec["decision_runtime"])
    reserve_before = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or lock.get("successor_spectrum_executed_before_implementation_lock")
        is not False
    ):
        raise RuntimeError("known-quotient implementation lock does not bind inputs")

    source_results = load_json(SOURCE_ROOT / "results/search_results.json")
    source_spec = load_json(V1_RESOLUTION_ROOT / "qualification_spec.json")
    training, calibration = source_runner._rebuild_source_rows(source_spec)
    rebuilt_hashes = {
        "training_values_full": source_runner._matrix_sha256(training.values),
        "training_derivatives_full": source_runner._matrix_sha256(
            training.derivatives
        ),
        "calibration_values_full": source_runner._matrix_sha256(calibration.values),
        "calibration_derivatives_full": source_runner._matrix_sha256(
            calibration.derivatives
        ),
    }
    matrix_identity = rebuilt_hashes == source_results["matrix_hashes"]
    if not matrix_identity:
        raise RuntimeError("known-quotient source matrices changed")

    challenge = load_json(CHALLENGE_PATH)
    challenge_values = []
    challenge_derivatives = []
    physical_l2 = []
    for case in challenge["cases"]:
        values, derivatives = source_runner._challenge_production(case)
        challenge_values.append(values)
        challenge_derivatives.append(derivatives)
        physical_l2.append(_physical_l2_binary(case))
    challenge_values_array = np.stack(challenge_values)
    challenge_derivatives_array = np.stack(challenge_derivatives)
    physical_l2_array = np.asarray(physical_l2, dtype=np.float64)

    zero_indices = np.asarray(structural_zero_feature_indices(), dtype=np.int64)
    active_mask = np.ones(training.values.shape[1], dtype=bool)
    active_mask[zero_indices] = False
    active_indices = np.flatnonzero(active_mask)
    if any(
        np.any(matrix[:, zero_indices] != 0.0)
        for matrix in (
            training.values,
            training.derivatives,
            calibration.values,
            calibration.derivatives,
            challenge_values_array,
            challenge_derivatives_array,
        )
    ):
        raise RuntimeError("declared structural-zero columns are nonzero")

    training_weights = balanced_row_weights(training.group_ids, training.family_ids)
    calibration_weights = balanced_row_weights(
        calibration.group_ids, calibration.family_ids
    )
    challenge_weights = np.full(
        challenge_values_array.shape[0],
        1.0 / challenge_values_array.shape[0],
        dtype=np.float64,
    )
    active_training_values = training.values[:, active_indices]
    active_training_derivatives = training.derivatives[:, active_indices]
    active_calibration_values = calibration.values[:, active_indices]
    active_calibration_derivatives = calibration.derivatives[:, active_indices]
    active_challenge_values = challenge_values_array[:, active_indices]
    active_challenge_derivatives = challenge_derivatives_array[:, active_indices]
    feature_scales = np.sqrt(
        np.sum(
            training_weights[:, None] * np.square(active_training_values), axis=0
        )
    )
    if np.any(feature_scales <= 1e-14):
        raise RuntimeError("known-quotient active library has an unobservable column")
    known = angular_momentum_squared_coefficients()[active_indices]
    thresholds = spec["thresholds"]
    fit_kwargs = {
        "value_rank_relative_tolerance": float(
            thresholds["value_rank_relative_tolerance"]
        ),
        "nuisance_derivative_rank_relative_tolerance": float(
            thresholds["nuisance_derivative_rank_relative_tolerance"]
        ),
        "singular_cluster_relative_tolerance": float(
            thresholds["singular_cluster_relative_tolerance"]
        ),
        "singular_cluster_absolute_tolerance": float(
            thresholds["singular_cluster_absolute_tolerance"]
        ),
        "svd_backward_error_factor": float(
            thresholds["svd_backward_error_factor"]
        ),
        "feature_scales": feature_scales,
    }
    domain_inputs = {
        "development": (
            active_training_values,
            active_training_derivatives,
            training_weights,
        ),
        "calibration": (
            active_calibration_values,
            active_calibration_derivatives,
            calibration_weights,
        ),
        "challenge": (
            active_challenge_values,
            active_challenge_derivatives,
            challenge_weights,
        ),
    }
    domain_summaries = {}
    candidates = []
    known_lie_metrics = {}
    candidate_threshold = float(thresholds["candidate_lie_rms_max"])
    for domain, (values, derivatives, weights) in domain_inputs.items():
        fits = [
            fit_known_quotient_spectrum(
                values,
                derivatives,
                weights,
                known,
                driver=driver,
                **fit_kwargs,
            )
            for driver in ("numpy", "gesdd", "gesvd")
        ]
        summary, domain_candidates = _domain_summary(
            domain,
            fits,
            active_indices,
            training.values.shape[1],
            candidate_threshold,
        )
        domain_summaries[domain] = summary
        candidates.extend(domain_candidates)
        known_lie_metrics[domain] = _known_lie_metric(
            derivatives, weights, known, feature_scales
        )

    challenge_feature_l2 = active_challenge_values @ known
    challenge_physical_l2_relative_max = float(
        np.max(
            np.abs(challenge_feature_l2 - physical_l2_array)
            / np.maximum(1.0, np.abs(physical_l2_array))
        )
    )
    controls = _metric_maxima(training, calibration)
    minimum_pair_separation = min(
        training.minimum_pair_separation_scaled_min,
        calibration.minimum_pair_separation_scaled_min,
    )
    minimum_denominator = min(
        training.minimum_denominator_abs, calibration.minimum_denominator_abs
    )
    candidate_count = len(candidates)
    candidate_direction_count = sum(
        int(candidate["dimension"]) for candidate in candidates
    )
    null_certified = all(
        summary["certifies_no_eligible_direction"]
        for summary in domain_summaries.values()
    )
    partition_consistent = bool((candidate_count == 0) == null_certified)
    readiness_gates = [
        make_gate("prerequisites_verified", 1, "==", 1),
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate("implementation_lock_verified", 1, "==", 1),
        make_gate("publication_reserve_intact", 1, "==", 1),
        make_gate("source_matrix_byte_identity", int(matrix_identity), "==", 1),
        make_gate(
            "development_group_count",
            training.group_count,
            "==",
            int(spec["data_domains"]["development"]["group_count"]),
        ),
        make_gate(
            "calibration_group_count",
            calibration.group_count,
            "==",
            int(spec["data_domains"]["calibration"]["group_count"]),
        ),
        make_gate(
            "development_physical_point_count",
            training.physical_point_count,
            "==",
            int(spec["data_domains"]["development"]["physical_point_count"]),
        ),
        make_gate(
            "calibration_physical_point_count",
            calibration.physical_point_count,
            "==",
            int(spec["data_domains"]["calibration"]["physical_point_count"]),
        ),
        make_gate(
            "challenge_case_count",
            challenge_values_array.shape[0],
            "==",
            int(spec["data_domains"]["challenge"]["case_count"]),
        ),
        make_gate(
            "declared_feature_count",
            training.values.shape[1],
            "==",
            int(spec["model_and_library"]["declared_feature_count"]),
        ),
        make_gate(
            "structural_zero_feature_count",
            zero_indices.size,
            "==",
            int(spec["model_and_library"]["exact_structural_zero_count"]),
        ),
        make_gate(
            "active_feature_count",
            active_indices.size,
            "==",
            int(spec["model_and_library"]["active_feature_count"]),
        ),
        make_gate(
            "challenge_feature_physical_l2_relative_difference_max",
            challenge_physical_l2_relative_max,
            "<=",
            float(
                thresholds[
                    "challenge_feature_physical_l2_relative_difference_max"
                ]
            ),
        ),
        make_gate(
            "minimum_pair_separation_scaled_min",
            minimum_pair_separation,
            ">=",
            float(thresholds["minimum_pair_separation_scaled_min"]),
        ),
        make_gate(
            "minimum_denominator_abs",
            minimum_denominator,
            ">=",
            float(thresholds["minimum_denominator_abs"]),
        ),
        make_gate(
            "energy_control_relative_lie_max",
            controls["energy_control_relative_lie_max"],
            "<=",
            float(thresholds["energy_control_relative_lie_max"]),
        ),
        make_gate(
            "body_permutation_spread_max",
            controls["body_permutation_spread_max"],
            "<=",
            float(thresholds["body_permutation_spread_max"]),
        ),
        make_gate(
            "rotation_spread_max",
            controls["rotation_spread_max"],
            "<=",
            float(thresholds["rotation_spread_max"]),
        ),
        make_gate(
            "gauge_orbit_spread_max",
            controls["gauge_orbit_spread_max"],
            "<=",
            float(thresholds["gauge_orbit_spread_max"]),
        ),
        make_gate(
            "chart_overlap_spread_max",
            controls["chart_overlap_spread_max"],
            "<=",
            float(thresholds["chart_overlap_spread_max"]),
        ),
        make_gate(
            "wp2_pushforward_tangent_relative_error_max",
            controls["wp2_pushforward_tangent_relative_error_max"],
            "<=",
            float(thresholds["wp2_pushforward_tangent_relative_error_max"]),
        ),
        make_gate(
            "wp2_time_rate_relative_error_max",
            controls["wp2_time_rate_relative_error_max"],
            "<=",
            float(thresholds["wp2_time_rate_relative_error_max"]),
        ),
        make_gate("decision_runtime_exact", 1, "==", 1),
        make_gate(
            "spectral_candidate_partition_consistent",
            int(partition_consistent),
            "==",
            1,
        ),
    ]
    for domain, summary in domain_summaries.items():
        readiness_gates.extend(
            [
                make_gate(
                    f"{domain}_backend_value_rank_consistent",
                    int(summary["backend_value_rank_consistent"]),
                    "==",
                    1,
                ),
                make_gate(
                    f"{domain}_known_observable_rank",
                    min(
                        fit["known_observable_rank"] for fit in summary["fits"]
                    ),
                    "==",
                    int(thresholds["known_observable_rank_required"]),
                ),
                make_gate(
                    f"{domain}_known_response_projection_residual_max",
                    summary["known_response_projection_residual_max"],
                    "<=",
                    float(thresholds["known_response_projection_residual_max"]),
                ),
                make_gate(
                    f"{domain}_mode_known_response_projection_max",
                    summary["mode_known_response_projection_max"],
                    "<=",
                    float(thresholds["known_response_projection_residual_max"]),
                ),
                make_gate(
                    f"{domain}_known_lie_rms_per_coefficient_scale",
                    known_lie_metrics[domain],
                    "<=",
                    float(
                        thresholds["known_lie_rms_per_coefficient_scale_max"]
                    ),
                ),
                make_gate(
                    f"{domain}_backend_smallest_generalized_relative_spread",
                    summary[
                        "backend_smallest_generalized_relative_spread"
                    ],
                    "<=",
                    float(
                        thresholds[
                            "backend_smallest_generalized_relative_spread_max"
                        ]
                    ),
                ),
            ]
        )
    search_ready = all(gate["passed"] for gate in readiness_gates)
    if not search_ready:
        status = "INVALID_SEARCH_NOT_READY"
    elif candidate_count:
        status = "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION"
    elif null_certified:
        status = "COMPLETE_BOUNDED_NULL_RESULT"
    else:
        status = "INVALID_SEARCH_NOT_READY"
    reserve_after = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": status,
        "interpretation_status": "PROHIBITED_PENDING_PUBLICATION_GATE",
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "runtime": runtime_fingerprint(),
        "decision_runtime": observed_runtime,
        "prerequisites": prerequisites,
        "source_matrix_hashes": rebuilt_hashes,
        "controls": {
            **controls,
            "minimum_pair_separation_scaled_min": minimum_pair_separation,
            "minimum_denominator_abs": minimum_denominator,
            "challenge_feature_physical_l2_relative_difference_max": (
                challenge_physical_l2_relative_max
            ),
        },
        "known_lie_metrics": known_lie_metrics,
        "search": {
            "declared_feature_count": training.values.shape[1],
            "structural_zero_feature_count": zero_indices.size,
            "active_feature_count": active_indices.size,
            "feature_scales_sha256": source_runner._matrix_sha256(
                feature_scales[None, :]
            ),
            "domains": domain_summaries,
            "candidate_subspaces": candidates,
            "candidate_subspace_count": candidate_count,
            "candidate_direction_count": candidate_direction_count,
            "candidate_threshold": candidate_threshold,
            "all_domains_certify_no_eligible_direction": null_certified,
            "spectral_candidate_partition_consistent": partition_consistent,
        },
        "readiness_gates": readiness_gates,
        "search_ready": "PASS" if search_ready else "FAIL",
        "claim_boundary": spec["evidence_boundary"],
        "publication_reserve_before": reserve_before,
        "publication_reserve_after": reserve_after,
        "publication_reserve_accessed": False,
    }
    atomic_write_json(destination, payload)
    lower_bounds = {
        name: summary["backend_guarded_lower_bound"]
        for name, summary in domain_summaries.items()
    }
    print(
        f"{spec['campaign']}: {status}; candidates={candidate_count}; "
        f"lower_bounds={lower_bounds}; reserve=SEALED_UNEXECUTED"
    )


if __name__ == "__main__":
    main()
