#!/usr/bin/env python
"""Execute the fail-closed WP3-MULTI-CAND-v2 quotient search."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
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
from src.python.n3bp_qualification import (  # noqa: E402
    InertialState,
    SystemParameters,
    angular_momentum,
    newtonian_rhs,
    total_energy,
)
from src.python.wp2_multi_v1 import (  # noqa: E402
    lift_inertial_state,
    project_derivative,
    project_state,
    vector_field,
)
from src.python.wp3_exploration_v3 import search_quotient_modes  # noqa: E402
from src.python.wp3_multi_v2 import (  # noqa: E402
    BODY_PERMUTATIONS,
    angular_momentum_squared_coefficients,
    evaluate_multi_features,
    feature_names,
    known_module_coefficients,
    permute_physical_inputs,
    structural_zero_feature_indices,
)


FloatArray = NDArray[np.float64]
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
V1_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v1"
WP2_ROOT = VALIDATION_ROOT / "wp2-multi-validation"
WP1_ROOT = VALIDATION_ROOT / "wp1-catalogue-n3bp-validation"
SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"
RESERVE_PATH = (
    VALIDATION_ROOT / "wp3-v2-exploration/sealed/publication_holdout_commitments.json"
)


def _load_common():
    return campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp3_multi_v2_campaign_common_search",
    )


def _load_v1_runner():
    return campaign_module(
        V1_ROOT / "scripts/run_search.py",
        "_wp3_multi_v2_frozen_v1_loader",
    )


@dataclass(frozen=True)
class _Rows:
    values: FloatArray
    derivatives: FloatArray
    group_ids: tuple[str, ...]
    family_ids: tuple[str, ...]
    point_ids: tuple[str, ...]
    group_count: int
    physical_point_count: int
    fixed_energy_abs_max: float
    chart_projection_scaled_max: float
    minimum_pair_separation_scaled_min: float
    minimum_denominator_abs: float
    gauge_orbit_spread_max: float
    chart_overlap_spread_max: float
    body_permutation_spread_max: float
    rotation_spread_max: float
    energy_control_relative_lie_max: float
    angular_momentum_squared_relative_error_max: float
    wp2_pushforward_tangent_relative_error_max: float
    wp2_time_rate_relative_error_max: float


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--spatial-development", required=True)
    parser.add_argument("--spatial-calibration", required=True)
    parser.add_argument("--wp1-catalogue", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _matrix_sha256(matrix: FloatArray) -> str:
    contiguous = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _relative_spread(arrays: Sequence[FloatArray]) -> float:
    stacked = np.stack(arrays)
    scale = np.maximum(1.0, np.max(np.abs(stacked), axis=0))
    return float(np.max(np.ptp(stacked, axis=0) / scale))


def _pair_separation(state: InertialState) -> float:
    return min(
        float(np.linalg.norm(state.positions[first] - state.positions[second]))
        for first, second in ((0, 1), (1, 2), (2, 0))
    )


def _collision_product(state: InertialState) -> float:
    return float(
        np.prod(
            [
                np.linalg.norm(state.positions[first] - state.positions[second])
                for first, second in ((0, 1), (1, 2), (2, 0))
            ]
        )
    )


def _energy_relative_lie(
    state: InertialState,
    tangent: FloatArray,
    parameters: SystemParameters,
) -> float:
    masses = parameters.masses
    gravity = parameters.gravitational_constant
    positions = state.positions
    velocities = state.velocities
    position_derivatives = tangent[:9].reshape(3, 3)
    velocity_derivatives = tangent[9:].reshape(3, 3)
    kinetic = 0.5 * float(np.sum(masses[:, None] * np.square(velocities)))
    kinetic_lie = float(np.sum(masses[:, None] * velocities * velocity_derivatives))
    potential = 0.0
    potential_lie = 0.0
    for first, second in ((0, 1), (1, 2), (2, 0)):
        relative = positions[first] - positions[second]
        relative_derivative = position_derivatives[first] - position_derivatives[second]
        distance = float(np.linalg.norm(relative))
        coefficient = float(gravity * masses[first] * masses[second])
        potential -= coefficient / distance
        potential_lie += coefficient * float(
            np.dot(relative, relative_derivative) / distance**3
        )
    scale = max(1.0, abs(kinetic) + abs(potential))
    return abs(kinetic_lie + potential_lie) / scale


def _rotate_inputs(
    state: InertialState,
    tangent: FloatArray,
) -> tuple[InertialState, FloatArray]:
    rotation = np.asarray(
        [
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    rotated_state = InertialState.from_components(
        state.positions @ rotation.T,
        state.velocities @ rotation.T,
    )
    rotated_tangent = np.concatenate(
        (
            (tangent[:9].reshape(3, 3) @ rotation.T).ravel(),
            (tangent[9:].reshape(3, 3) @ rotation.T).ravel(),
        )
    )
    return rotated_state, rotated_tangent


def _build_rows(
    split: str,
    spec: dict[str, Any],
    corpus: dict[str, Any],
    *,
    spatial_definitions: dict[str, dict[str, Any]],
    spatial_results: dict[str, dict[str, Any]],
    wp1_candidates: dict[str, dict[str, Any]],
) -> _Rows:
    legacy = _load_v1_runner()
    values: list[FloatArray] = []
    derivatives: list[FloatArray] = []
    group_ids: list[str] = []
    family_ids: list[str] = []
    point_ids: list[str] = []
    energy_differences: list[float] = []
    projection_errors: list[float] = []
    separations: list[float] = []
    denominator_abs: list[float] = []
    gauge_spreads: list[float] = []
    chart_spreads: list[float] = []
    permutation_spreads: list[float] = []
    rotation_spreads: list[float] = []
    energy_lies: list[float] = []
    angular_errors: list[float] = []
    pushforward_tangent_errors: list[float] = []
    time_rate_errors: list[float] = []
    charts = tuple(spec["library"]["charts"])
    angle_pairs = tuple(
        tuple(float(value) for value in pair)
        for pair in spec["library"]["torus_angle_pairs"]
    )
    selected_cases = [case for case in corpus["cases"] if case["split"] == split]
    for case in selected_cases:
        points = legacy._source_points(
            case,
            spatial_definitions=spatial_definitions,
            spatial_results=spatial_results,
            wp1_candidates=wp1_candidates,
        )
        dimensionless = [legacy._dimensionless_inertial(point) for point in points]
        fixed_energy = total_energy(*dimensionless[0])
        for point, (physical, parameters) in zip(points, dimensionless, strict=True):
            current_energy = total_energy(physical, parameters)
            energy_differences.append(abs(current_energy - fixed_energy))
            separations.append(_pair_separation(physical))
            canonical_time_rate = _collision_product(physical)
            canonical_tangent = canonical_time_rate * newtonian_rhs(
                0.0, physical, parameters
            )
            all_values: list[FloatArray] = []
            all_derivatives: list[FloatArray] = []
            all_tangents: list[FloatArray] = []
            chart_value_means: list[FloatArray] = []
            chart_derivative_means: list[FloatArray] = []
            for chart in charts:
                chart_values: list[FloatArray] = []
                chart_derivatives: list[FloatArray] = []
                for angle_pair in angle_pairs:
                    lifted = lift_inertial_state(
                        physical,
                        parameters,
                        chart,
                        angles=angle_pair,
                        p_t=-fixed_energy,
                    )
                    flow = vector_field(lifted, parameters)
                    projected = project_state(lifted, parameters)
                    projected_tangent = project_derivative(flow, parameters)
                    projected_tangent *= canonical_time_rate / flow.time_rate
                    tangent_scale = max(
                        1.0,
                        float(np.max(np.abs(canonical_tangent))),
                        float(np.max(np.abs(projected_tangent))),
                    )
                    pushforward_tangent_errors.append(
                        float(
                            np.max(np.abs(projected_tangent - canonical_tangent))
                            / tangent_scale
                        )
                    )
                    time_rate_errors.append(
                        abs(flow.time_rate - canonical_time_rate)
                        / max(1.0, abs(canonical_time_rate))
                    )
                    tangent = canonical_tangent
                    evaluation = evaluate_multi_features(
                        physical,
                        tangent,
                        parameters,
                        fixed_energy=fixed_energy,
                    )
                    projection_scale = max(
                        1.0, float(np.max(np.abs(physical.as_vector())))
                    )
                    projection_errors.append(
                        float(
                            np.max(np.abs(projected.as_vector() - physical.as_vector()))
                            / projection_scale
                        )
                    )
                    denominator_abs.extend(np.abs(evaluation.denominator_values))
                    chart_values.append(evaluation.values)
                    chart_derivatives.append(evaluation.derivatives)
                    all_values.append(evaluation.values)
                    all_derivatives.append(evaluation.derivatives)
                    all_tangents.append(tangent)
                gauge_spreads.append(
                    max(
                        _relative_spread(chart_values),
                        _relative_spread(chart_derivatives),
                    )
                )
                chart_value_means.append(np.mean(np.stack(chart_values), axis=0))
                chart_derivative_means.append(
                    np.mean(np.stack(chart_derivatives), axis=0)
                )
            chart_spreads.append(
                max(
                    _relative_spread(chart_value_means),
                    _relative_spread(chart_derivative_means),
                )
            )
            row_values = np.mean(np.stack(all_values), axis=0)
            row_derivatives = np.mean(np.stack(all_derivatives), axis=0)
            mean_tangent = np.mean(np.stack(all_tangents), axis=0)
            direct = evaluate_multi_features(
                physical,
                mean_tangent,
                parameters,
                fixed_energy=fixed_energy,
            )

            relabeled_values: list[FloatArray] = []
            relabeled_derivatives: list[FloatArray] = []
            for permutation in BODY_PERMUTATIONS:
                relabeled = permute_physical_inputs(
                    physical, mean_tangent, parameters, permutation
                )
                evaluation = evaluate_multi_features(
                    relabeled[0],
                    relabeled[1],
                    relabeled[2],
                    fixed_energy=fixed_energy,
                )
                relabeled_values.append(evaluation.values)
                relabeled_derivatives.append(evaluation.derivatives)
            permutation_spreads.append(
                max(
                    _relative_spread(relabeled_values),
                    _relative_spread(relabeled_derivatives),
                )
            )

            rotated_state, rotated_tangent = _rotate_inputs(physical, mean_tangent)
            rotated = evaluate_multi_features(
                rotated_state,
                rotated_tangent,
                parameters,
                fixed_energy=fixed_energy,
            )
            rotation_spreads.append(
                max(
                    _relative_spread((direct.values, rotated.values)),
                    _relative_spread((direct.derivatives, rotated.derivatives)),
                )
            )
            energy_lies.append(_energy_relative_lie(physical, mean_tangent, parameters))
            angular = angular_momentum(physical, parameters)
            expected_l2 = float(np.dot(angular, angular))
            observed_l2 = float(row_values @ angular_momentum_squared_coefficients())
            angular_errors.append(
                abs(observed_l2 - expected_l2) / max(1.0, abs(expected_l2))
            )
            values.append(row_values)
            derivatives.append(row_derivatives)
            group_ids.append(case["case_id"])
            family_ids.append(case["source_family"])
            point_ids.append(point.point_id)
    return _Rows(
        values=np.stack(values),
        derivatives=np.stack(derivatives),
        group_ids=tuple(group_ids),
        family_ids=tuple(family_ids),
        point_ids=tuple(point_ids),
        group_count=len(selected_cases),
        physical_point_count=len(values),
        fixed_energy_abs_max=max(energy_differences),
        chart_projection_scaled_max=max(projection_errors),
        minimum_pair_separation_scaled_min=min(separations),
        minimum_denominator_abs=min(denominator_abs),
        gauge_orbit_spread_max=max(gauge_spreads),
        chart_overlap_spread_max=max(chart_spreads),
        body_permutation_spread_max=max(permutation_spreads),
        rotation_spread_max=max(rotation_spreads),
        energy_control_relative_lie_max=max(energy_lies),
        angular_momentum_squared_relative_error_max=max(angular_errors),
        wp2_pushforward_tangent_relative_error_max=max(pushforward_tangent_errors),
        wp2_time_rate_relative_error_max=max(time_rate_errors),
    )


def _search_full_library(
    training: _Rows,
    calibration: _Rows,
    search_spec: dict[str, Any],
) -> dict[str, Any]:
    names = feature_names()
    zeros = np.asarray(structural_zero_feature_indices(), dtype=np.int64)
    if any(
        np.any(matrix[:, zeros] != 0.0)
        for matrix in (
            training.values,
            training.derivatives,
            calibration.values,
            calibration.derivatives,
        )
    ):
        raise RuntimeError("exact Reynolds zero columns are not identically zero")
    active_mask = np.ones(len(names), dtype=bool)
    active_mask[zeros] = False
    active_indices = np.flatnonzero(active_mask)
    active_names = tuple(names[index] for index in active_indices)
    active_training_values = training.values[:, active_indices]
    active_training_derivatives = training.derivatives[:, active_indices]
    active_calibration_values = calibration.values[:, active_indices]
    active_calibration_derivatives = calibration.derivatives[:, active_indices]
    column_scales = np.sqrt(np.mean(np.square(active_training_values), axis=0))
    if np.any(column_scales <= 1e-14):
        bad = [active_names[index] for index in np.flatnonzero(column_scales <= 1e-14)]
        raise RuntimeError(f"unexpected unobservable Reynolds columns: {bad}")
    known_full = known_module_coefficients()
    known_active = {
        name: coefficients[active_indices] for name, coefficients in known_full.items()
    }
    search = search_quotient_modes(
        active_training_values,
        active_training_derivatives,
        np.zeros_like(active_training_values),
        active_calibration_values,
        active_calibration_derivatives,
        np.zeros_like(active_calibration_values),
        feature_names=active_names,
        known_module=known_active,
        training_group_ids=training.group_ids,
        training_family_ids=training.family_ids,
        training_point_ids=training.point_ids,
        calibration_group_ids=calibration.group_ids,
        calibration_family_ids=calibration.family_ids,
        calibration_point_ids=calibration.point_ids,
        mode_count=int(search_spec["mode_count"]),
        fold_mode_count=int(search_spec["fold_mode_count"]),
        value_rank_relative_tolerance=float(
            search_spec["value_rank_relative_tolerance"]
        ),
        singular_cluster_relative_tolerance=float(
            search_spec["singular_cluster_relative_tolerance"]
        ),
        singular_cluster_absolute_tolerance=float(
            search_spec["singular_cluster_absolute_tolerance"]
        ),
        svd_backward_error_factor=float(search_spec["svd_backward_error_factor"]),
        candidate_lie_rms_max=float(search_spec["candidate_lie_rms_max"]),
        candidate_gauge_lie_rms_max=float(search_spec["candidate_lie_rms_max"]),
        calibration_ratio_floor=float(search_spec["calibration_ratio_floor"]),
        calibration_to_training_max=float(search_spec["calibration_to_training_max"]),
        family_fold_subspace_projection_min=float(
            search_spec["family_fold_subspace_projection_min"]
        ),
        calibration_trajectory_drift_max=float(
            search_spec["calibration_trajectory_drift_max"]
        ),
        gauge_orbit_spread_max=float(search_spec["gauge_orbit_spread_max"]),
    )
    for mode in search["modes"]:
        if "coefficients" not in mode:
            continue
        full = np.zeros(len(names), dtype=np.float64)
        full[active_indices] = np.asarray(mode["coefficients"], dtype=np.float64)
        mode["coefficients"] = full.tolist()
    search["feature_count"] = len(names)
    search["active_feature_count"] = len(active_indices)
    search["structural_zero_feature_count"] = len(zeros)
    search["structural_zero_feature_indices"] = zeros.tolist()
    search["structural_zero_feature_names"] = [names[index] for index in zeros]
    search["active_feature_indices_sha256"] = hashlib.sha256(
        np.asarray(active_indices, dtype="<i8").tobytes()
    ).hexdigest()
    return search


def _known_lie_metric(search: dict[str, Any]) -> float:
    return max(
        max(
            float(metric["training_lie_rms_per_coefficient_scale"]),
            float(metric["calibration_lie_rms_per_coefficient_scale"]),
        )
        for metric in search["known_module_metrics"].values()
    )


def main() -> None:
    args = _args()
    if Path(args.output).exists():
        raise RuntimeError("refusing to overwrite one-shot WP3 v2 search output")
    common = _load_common()
    legacy = _load_v1_runner()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    spatial_corpus = load_json(args.spatial_corpus)
    wp1_catalogue = load_json(args.wp1_catalogue)
    specification_lock = common.verify_specification_lock(args.spec)
    observed_runtime = common.verify_decision_runtime(spec["decision_runtime"])
    if sha256_file(args.corpus) != spec["prerequisites"]["v1_search_corpus_sha256"]:
        raise RuntimeError("frozen WP3 v1 search corpus changed")
    if (
        sha256_file(args.wp1_catalogue)
        != spec["prerequisites"]["wp1_catalogue"]["native_catalogue_sha256"]
    ):
        raise RuntimeError("WP1 native catalogue changed")
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("corpus_sha256") != sha256_file(args.corpus)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("search lock does not bind the frozen inputs")

    prerequisites = {
        "wp2_multi": common.verify_qualification_prerequisite(
            spec["prerequisites"]["wp2_multi"],
            lock_path=WP2_ROOT / "reports/wp2_multi_v1_qualification_lock.json",
            record_path=WP2_ROOT / "reports/wp2_multi_v1_qualification_record.json",
            prefix="WP2-MULTIQ-v1",
        ),
        "wp1_catalogue": common.verify_qualification_prerequisite(
            spec["prerequisites"]["wp1_catalogue"],
            lock_path=WP1_ROOT / "reports/wp1_cat_n3bp_v1_qualification_lock.json",
            record_path=WP1_ROOT / "reports/wp1_cat_n3bp_v1_qualification_record.json",
            prefix="WP1-CAT-N3BP-v1",
        ),
        "wp3_multi_v1": common.verify_wp3_v1_prerequisite(
            spec["prerequisites"]["wp3_multi_v1"],
            lock_path=V1_ROOT / "reports/wp3_multi_v1_search_lock.json",
            record_path=V1_ROOT / "reports/wp3_multi_v1_search_record.json",
            gate_path=V1_ROOT / "results/publication_gate.json",
        ),
    }
    reserve = common.verify_publication_reserve(
        args.commitments,
        spec["prerequisites"]["sealed_publication_reserve_sha256"],
    )
    spatial_inputs = legacy._verify_spatial_inputs(
        SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_record.json",
        args.spatial_corpus,
        args.spatial_development,
        args.spatial_calibration,
    )
    definitions = {case["case_id"]: case for case in spatial_corpus["cases"]}
    development_results = {
        case["case_id"]: case for case in load_json(args.spatial_development)["cases"]
    }
    calibration_results = {
        case["case_id"]: case for case in load_json(args.spatial_calibration)["cases"]
    }
    wp1_candidates = {
        candidate["candidate_id"]: candidate
        for candidate in wp1_catalogue["candidates"]
    }
    training = _build_rows(
        "development",
        spec,
        corpus,
        spatial_definitions=definitions,
        spatial_results=development_results,
        wp1_candidates=wp1_candidates,
    )
    calibration = _build_rows(
        "calibration",
        spec,
        corpus,
        spatial_definitions=definitions,
        spatial_results=calibration_results,
        wp1_candidates=wp1_candidates,
    )
    search_spec = spec["search"]
    search = _search_full_library(training, calibration, search_spec)
    expected_groups = spec["data"]["expected_group_counts"]
    expected_points = spec["data"]["expected_physical_point_counts"]
    metric_maxima = {
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
    minimum_pair_separation = min(
        training.minimum_pair_separation_scaled_min,
        calibration.minimum_pair_separation_scaled_min,
    )
    minimum_denominator = min(
        training.minimum_denominator_abs, calibration.minimum_denominator_abs
    )
    candidate_count = int(search["candidate_count"])
    null_certified = bool(
        search["null_result_spectral_certificate"][
            "certifies_no_training_eligible_direction"
        ]
    )
    spectral_consistent = bool(
        (candidate_count == 0) == null_certified
        and candidate_count == len(search["candidate_subspaces"])
        and sum(
            int(cluster["dimension"])
            for cluster in search["generalized_singular_clusters"]
        )
        == int(search["observable_value_rank"])
    )
    readiness_gates = [
        make_gate("prerequisite_pass_rate", 1.0, ">=", 1.0),
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate("search_lock_verified", 1, "==", 1),
        make_gate("sealed_reserve_intact", 1, "==", 1),
        make_gate("qualified_spatial_inputs_verified", 1, "==", 1),
        make_gate(
            "development_group_count",
            training.group_count,
            "==",
            int(expected_groups["development"]),
        ),
        make_gate(
            "calibration_group_count",
            calibration.group_count,
            "==",
            int(expected_groups["calibration"]),
        ),
        make_gate(
            "development_physical_point_count",
            training.physical_point_count,
            "==",
            int(expected_points["development"]),
        ),
        make_gate(
            "calibration_physical_point_count",
            calibration.physical_point_count,
            "==",
            int(expected_points["calibration"]),
        ),
        make_gate(
            "declared_feature_count",
            int(search["feature_count"]),
            "==",
            int(spec["library"]["search_feature_count"]),
        ),
        make_gate(
            "active_feature_count", int(search["active_feature_count"]), "==", 249
        ),
        make_gate(
            "exact_structural_zero_count",
            int(search["structural_zero_feature_count"]),
            "==",
            36,
        ),
        make_gate(
            "exact_known_module_rank",
            int(search["exact_known_module_rank"]),
            "==",
            int(spec["library"]["exact_known_module_rank"]),
        ),
        make_gate(
            "known_module_lie_rms_max",
            _known_lie_metric(search),
            "<=",
            float(search_spec["known_module_lie_rms_max"]),
        ),
        make_gate(
            "known_module_projection_residual",
            float(search["exact_known_module_projection_residual"]),
            "<=",
            float(search_spec["known_module_projection_residual_max"]),
        ),
        make_gate(
            "angular_momentum_squared_relative_error_max",
            metric_maxima["angular_momentum_squared_relative_error_max"],
            "<=",
            1e-10,
        ),
        make_gate(
            "energy_control_relative_lie_max",
            metric_maxima["energy_control_relative_lie_max"],
            "<=",
            float(search_spec["energy_control_relative_lie_max"]),
        ),
        make_gate(
            "body_permutation_spread_max",
            metric_maxima["body_permutation_spread_max"],
            "<=",
            float(search_spec["body_permutation_spread_max"]),
        ),
        make_gate(
            "rotation_spread_max",
            metric_maxima["rotation_spread_max"],
            "<=",
            float(search_spec["rotation_spread_max"]),
        ),
        make_gate(
            "gauge_orbit_spread_max",
            metric_maxima["gauge_orbit_spread_max"],
            "<=",
            float(search_spec["gauge_orbit_spread_max"]),
        ),
        make_gate(
            "chart_overlap_spread_max",
            metric_maxima["chart_overlap_spread_max"],
            "<=",
            float(search_spec["chart_overlap_spread_max"]),
        ),
        make_gate(
            "fixed_energy_checkpoint_abs_max",
            metric_maxima["fixed_energy_abs_max"],
            "<=",
            float(search_spec["fixed_energy_checkpoint_abs_max"]),
        ),
        make_gate(
            "chart_projection_state_scaled_max",
            metric_maxima["chart_projection_scaled_max"],
            "<=",
            float(search_spec["chart_projection_state_scaled_max"]),
        ),
        make_gate(
            "wp2_pushforward_tangent_relative_error_max",
            metric_maxima["wp2_pushforward_tangent_relative_error_max"],
            "<=",
            float(search_spec["chart_overlap_spread_max"]),
        ),
        make_gate(
            "wp2_time_rate_relative_error_max",
            metric_maxima["wp2_time_rate_relative_error_max"],
            "<=",
            float(search_spec["chart_overlap_spread_max"]),
        ),
        make_gate(
            "minimum_pair_separation_scaled_min",
            minimum_pair_separation,
            ">=",
            float(spec["data"]["minimum_pair_separation_scaled_min"]),
        ),
        make_gate(
            "minimum_denominator_abs",
            minimum_denominator,
            ">=",
            float(spec["data"]["minimum_denominator_abs"]),
        ),
        make_gate(
            "all_generalized_modes_evaluated",
            int(search["evaluated_mode_count"]),
            "==",
            int(search["observable_value_rank"]),
        ),
        make_gate("decision_runtime_exact", 1, "==", 1),
        make_gate(
            "spectral_decision_partition_consistent", int(spectral_consistent), "==", 1
        ),
    ]
    search_ready = "PASS" if all(gate["passed"] for gate in readiness_gates) else "FAIL"
    if search_ready != "PASS":
        status = "INVALID_SEARCH_NOT_READY"
    elif candidate_count:
        status = "CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION"
    elif not null_certified:
        status = "INVALID_SPECTRAL_DECISION_INCONSISTENT"
    else:
        status = "COMPLETE_BOUNDED_NULL_RESULT"
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": status,
        "interpretation_status": "PROHIBITED_PENDING_PUBLICATION_GATE",
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "corpus_sha256": sha256_file(args.corpus),
        "wp1_catalogue_sha256": sha256_file(args.wp1_catalogue),
        "prerequisites": prerequisites,
        "sealed_publication_reserve": reserve,
        "qualified_spatial_inputs": spatial_inputs,
        "runtime": runtime_fingerprint(),
        "decision_runtime": observed_runtime,
        "readiness_gates": readiness_gates,
        "search_ready": search_ready,
        "matrix_hashes": {
            "training_values_full": _matrix_sha256(training.values),
            "training_derivatives_full": _matrix_sha256(training.derivatives),
            "calibration_values_full": _matrix_sha256(calibration.values),
            "calibration_derivatives_full": _matrix_sha256(calibration.derivatives),
        },
        "source_summary": {
            "training_groups": training.group_count,
            "calibration_groups": calibration.group_count,
            "training_physical_points": training.physical_point_count,
            "calibration_physical_points": calibration.physical_point_count,
            "chart_count": len(spec["library"]["charts"]),
            "gauge_pair_count": len(spec["library"]["torus_angle_pairs"]),
            "atlas_projection_count_per_physical_point": len(spec["library"]["charts"])
            * len(spec["library"]["torus_angle_pairs"]),
            "minimum_pair_separation_scaled_min": minimum_pair_separation,
            "minimum_denominator_abs": minimum_denominator,
            **metric_maxima,
        },
        "search": search,
    }
    atomic_write_json(args.output, payload)
    print(
        f"{spec['campaign']}: {status}; SEARCH_READY={search_ready}; "
        f"candidate_subspaces={candidate_count}; interpretation=PROHIBITED"
    )


if __name__ == "__main__":
    main()
