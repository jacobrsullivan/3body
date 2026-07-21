#!/usr/bin/env python
"""Execute the fail-closed WP3-MULTI-CAND-v1 search."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp


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
    total_energy,
)
from src.python.threebody_reduction import TranslationQuotientState  # noqa: E402
from src.python.wp1_catalogue_n3bp_v1 import inertial_rhs  # noqa: E402
from src.python.wp2_multi_v1 import (  # noqa: E402
    lift_inertial_state,
    project_state,
    torus_action,
    vector_field,
)
from src.python.wp3_exploration_v3 import search_quotient_modes  # noqa: E402
from src.python.wp3_exploration_v3.search import balanced_row_weights  # noqa: E402
from src.python.wp3_multi_v1 import (  # noqa: E402
    evaluate_multi_features,
    feature_names,
    known_module_coefficients,
    multi_tangent_vector,
    torus_generators,
)


FloatArray = NDArray[np.float64]
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v1"
WP2_ROOT = VALIDATION_ROOT / "wp2-multi-validation"
WP1_ROOT = VALIDATION_ROOT / "wp1-catalogue-n3bp-validation"
SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"


def _load_common():
    return campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp3_multi_campaign_common_search",
    )


def _load_nondimensionalize():
    module_path = REPO_ROOT / "src/python/wp3_exploration_v2/normalization.py"
    specification = importlib.util.spec_from_file_location(
        "_wp3_multi_frozen_normalization", module_path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load frozen normalizer: {module_path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(specification.name, None)
        raise
    return module.nondimensionalize


nondimensionalize = _load_nondimensionalize()


@dataclass(frozen=True)
class _PhysicalPoint:
    state: InertialState
    parameters: SystemParameters
    length_scale: float
    point_id: str


@dataclass(frozen=True)
class _AtlasRows:
    values: FloatArray
    flow: FloatArray
    gauge1: FloatArray
    gauge2: FloatArray
    overlap_reference: FloatArray
    overlap_difference: FloatArray
    group_ids: tuple[str, ...]
    family_ids: tuple[str, ...]
    point_ids: tuple[str, ...]
    overlap_group_ids: tuple[str, ...]
    overlap_family_ids: tuple[str, ...]
    overlap_point_ids: tuple[str, ...]
    fixed_energy_abs_max: float
    chart_projection_scaled_max: float
    minimum_pair_separation_scaled_min: float
    physical_point_count: int
    chart_count: int
    gauge_pair_count: int


@dataclass(frozen=True)
class _CombinedRows:
    values: FloatArray
    constraints: FloatArray
    group_ids: tuple[str, ...]
    family_ids: tuple[str, ...]
    point_ids: tuple[str, ...]
    block_scales: dict[str, float]
    block_weight_totals: dict[str, float]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--source-corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--spatial-development", required=True)
    parser.add_argument("--spatial-calibration", required=True)
    parser.add_argument("--wp1-catalogue", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _verify_spatial_inputs(
    spatial_record_path: Path,
    spatial_corpus_path: str,
    development_path: str,
    calibration_path: str,
) -> dict[str, str]:
    record = load_json(spatial_record_path)
    corpus_evidence = record["evidence_files"]["corpus"]
    if sha256_file(spatial_corpus_path) != corpus_evidence["sha256"]:
        raise RuntimeError("spatial corpus is not qualification-bound")
    output = {"corpus_sha256": sha256_file(spatial_corpus_path)}
    for split, result_path in (
        ("development", development_path),
        ("calibration", calibration_path),
    ):
        evidence = record["evidence_files"][f"{split}_evaluation"]
        evaluation_path = REPO_ROOT / evidence["path"]
        if sha256_file(evaluation_path) != evidence["sha256"]:
            raise RuntimeError(f"qualified spatial {split} evaluation changed")
        evaluation = load_json(evaluation_path)
        if (
            evaluation.get("status") != "PASS"
            or evaluation.get("results_sha256") != sha256_file(result_path)
        ):
            raise RuntimeError(f"spatial {split} result is not qualification-bound")
        output[f"{split}_results_sha256"] = sha256_file(result_path)
        output[f"{split}_evaluation_sha256"] = sha256_file(evaluation_path)
    return output


def _matrix_sha256(matrix: FloatArray) -> str:
    contiguous = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _float(value: str | float) -> float:
    if isinstance(value, str) and ("0x" in value or "0X" in value):
        return float.fromhex(value)
    return float(value)


def _wp1_points(case: dict[str, Any], candidate: dict[str, Any]) -> list[_PhysicalPoint]:
    parameters_payload = candidate["parameters"]
    masses = [
        _float(parameters_payload["m1"]),
        _float(parameters_payload["m2"]),
        _float(parameters_payload["m3"]),
    ]
    period = _float(parameters_payload["period"])
    initial = np.asarray([_float(value) for value in candidate["state18"]])
    fractions = np.asarray(case["checkpoint_fractions"], dtype=np.float64)
    times = period * fractions
    solution = solve_ivp(
        inertial_rhs,
        (0.0, period),
        initial,
        args=(masses,),
        method="DOP853",
        t_eval=times,
        rtol=2e-12,
        atol=2e-14,
        max_step=period / 128.0,
    )
    if not solution.success or solution.y.shape != (18, len(times)):
        raise RuntimeError(f"WP1 checkpoint propagation failed: {case['case_id']}")
    parameters = SystemParameters(masses, gravitational_constant=1.0)
    return [
        _PhysicalPoint(
            state=InertialState(np.asarray(solution.y[:, index], dtype=np.float64)),
            parameters=parameters,
            length_scale=float(case["length_scale"]),
            point_id=f"{case['case_id']}:fraction-{fraction:.8f}",
        )
        for index, fraction in enumerate(fractions)
    ]


def _source_points(
    case: dict[str, Any],
    *,
    spatial_definitions: dict[str, dict[str, Any]],
    spatial_results: dict[str, dict[str, Any]],
    wp1_candidates: dict[str, dict[str, Any]],
) -> list[_PhysicalPoint]:
    kind = case["source_kind"]
    if kind == "qualified_external_trajectory":
        definition = spatial_definitions[case["source_case_id"]]
        result = spatial_results[case["source_case_id"]]
        parameters = SystemParameters(
            [float(value) for value in definition["masses_decimal"]],
            gravitational_constant=1.0,
        )
        return [
            _PhysicalPoint(
                state=InertialState(
                    np.asarray(result["oracle"]["states_decimal"][checkpoint], dtype=float)
                ),
                parameters=parameters,
                length_scale=float(case["length_scale"]),
                point_id=f"{case['case_id']}:checkpoint-{checkpoint}",
            )
            for checkpoint in case["checkpoint_indices"]
        ]
    if kind == "deterministic_spatial_collocation":
        return [
            _PhysicalPoint(
                state=InertialState.from_components(
                    case["positions"], case["velocities"]
                ),
                parameters=SystemParameters(
                    case["masses"], gravitational_constant=1.0
                ),
                length_scale=float(case["length_scale"]),
                point_id=case["case_id"],
            )
        ]
    if kind == "qualified_wp1_periodic_catalogue":
        return _wp1_points(case, wp1_candidates[case["candidate_id"]])
    raise ValueError(f"unsupported source kind: {kind}")


def _dimensionless_inertial(point: _PhysicalPoint) -> tuple[InertialState, SystemParameters]:
    system = nondimensionalize(
        point.state,
        point.parameters,
        length_scale=point.length_scale,
    )
    state = system.state
    quotient = TranslationQuotientState(
        parameters=system.parameters,
        rho=state[:3],
        lambda_vector=state[3:6],
        p_rho=state[6:9],
        p_lambda=state[9:12],
    )
    return quotient.to_inertial(), system.parameters


def _pair_separation(state: InertialState) -> float:
    positions = state.positions
    return min(
        float(np.linalg.norm(positions[first] - positions[second]))
        for first, second in ((0, 1), (1, 2), (2, 0))
    )


def _build_atlas_rows(
    split: str,
    corpus: dict[str, Any],
    *,
    spatial_definitions: dict[str, dict[str, Any]],
    spatial_results: dict[str, dict[str, Any]],
    wp1_candidates: dict[str, dict[str, Any]],
) -> _AtlasRows:
    values: list[FloatArray] = []
    flow_rows: list[FloatArray] = []
    gauge1_rows: list[FloatArray] = []
    gauge2_rows: list[FloatArray] = []
    overlap_reference: list[FloatArray] = []
    overlap_difference: list[FloatArray] = []
    group_ids: list[str] = []
    family_ids: list[str] = []
    point_ids: list[str] = []
    overlap_group_ids: list[str] = []
    overlap_family_ids: list[str] = []
    overlap_point_ids: list[str] = []
    energy_differences: list[float] = []
    projection_errors: list[float] = []
    separations: list[float] = []
    physical_point_count = 0
    charts = tuple(corpus["charts"])
    angles = tuple(tuple(float(value) for value in pair) for pair in corpus["torus_angle_pairs"])
    for case in (item for item in corpus["cases"] if item["split"] == split):
        points = _source_points(
            case,
            spatial_definitions=spatial_definitions,
            spatial_results=spatial_results,
            wp1_candidates=wp1_candidates,
        )
        dimensionless = [_dimensionless_inertial(point) for point in points]
        fixed_energy = total_energy(*dimensionless[0])
        for point, (physical, parameters) in zip(points, dimensionless, strict=True):
            physical_point_count += 1
            current_energy = total_energy(physical, parameters)
            energy_differences.append(abs(current_energy - fixed_energy))
            separations.append(_pair_separation(physical))
            chart_angle_values: dict[tuple[str, int], FloatArray] = {}
            for chart in charts:
                for angle_index, angle_pair in enumerate(angles):
                    state = lift_inertial_state(
                        physical,
                        parameters,
                        chart,
                        angles=angle_pair,
                        p_t=-fixed_energy,
                    )
                    flow = vector_field(state, parameters)
                    tangent = multi_tangent_vector(flow.derivative)
                    evaluation = evaluate_multi_features(
                        state,
                        tangent,
                        parameters,
                        fixed_energy=fixed_energy,
                    )
                    gauge_generators = torus_generators(state)
                    gauge_evaluations = [
                        evaluate_multi_features(
                            state,
                            generator,
                            parameters,
                            fixed_energy=fixed_energy,
                        )
                        for generator in gauge_generators
                    ]
                    if evaluation.names != feature_names():
                        raise RuntimeError("multi-chart feature ordering changed")
                    projected = project_state(state, parameters)
                    projection_errors.append(
                        float(
                            np.max(
                                np.abs(
                                    projected.as_vector() - physical.as_vector()
                                )
                            )
                        )
                    )
                    values.append(evaluation.values)
                    flow_rows.append(evaluation.derivatives)
                    gauge1_rows.append(gauge_evaluations[0].derivatives)
                    gauge2_rows.append(gauge_evaluations[1].derivatives)
                    group_ids.append(case["case_id"])
                    family_ids.append(case["source_family"])
                    point_ids.append(point.point_id)
                    chart_angle_values[(chart, angle_index)] = evaluation.values
            base_chart = charts[0]
            for angle_index in range(len(angles)):
                base = chart_angle_values[(base_chart, angle_index)]
                for chart in charts[1:]:
                    target = chart_angle_values[(chart, angle_index)]
                    overlap_reference.append(0.5 * (base + target))
                    overlap_difference.append(base - target)
                    overlap_group_ids.append(case["case_id"])
                    overlap_family_ids.append(case["source_family"])
                    overlap_point_ids.append(point.point_id)
    minimum = min(separations)
    return _AtlasRows(
        values=np.stack(values),
        flow=np.stack(flow_rows),
        gauge1=np.stack(gauge1_rows),
        gauge2=np.stack(gauge2_rows),
        overlap_reference=np.stack(overlap_reference),
        overlap_difference=np.stack(overlap_difference),
        group_ids=tuple(group_ids),
        family_ids=tuple(family_ids),
        point_ids=tuple(point_ids),
        overlap_group_ids=tuple(overlap_group_ids),
        overlap_family_ids=tuple(overlap_family_ids),
        overlap_point_ids=tuple(overlap_point_ids),
        fixed_energy_abs_max=max(energy_differences),
        chart_projection_scaled_max=max(projection_errors),
        minimum_pair_separation_scaled_min=minimum,
        physical_point_count=physical_point_count,
        chart_count=len(charts),
        gauge_pair_count=len(angles),
    )


def _combine(rows: _AtlasRows) -> _CombinedRows:
    values = np.vstack(
        (
            rows.values,
            rows.values,
            rows.values,
            rows.overlap_reference,
        )
    )
    group_ids = (
        rows.group_ids
        + rows.group_ids
        + rows.group_ids
        + rows.overlap_group_ids
    )
    family_ids = (
        rows.family_ids
        + rows.family_ids
        + rows.family_ids
        + rows.overlap_family_ids
    )
    point_ids = (
        rows.point_ids
        + rows.point_ids
        + rows.point_ids
        + rows.overlap_point_ids
    )
    weights = balanced_row_weights(group_ids, family_ids)
    sizes = {
        "physical_lie": rows.flow.shape[0],
        "gauge_generator_1": rows.gauge1.shape[0],
        "gauge_generator_2": rows.gauge2.shape[0],
        "chart_overlap": rows.overlap_difference.shape[0],
    }
    offsets: dict[str, slice] = {}
    start = 0
    for name, size in sizes.items():
        offsets[name] = slice(start, start + size)
        start += size
    weight_totals = {
        name: float(np.sum(weights[block])) for name, block in offsets.items()
    }
    scales = {
        name: float(np.sqrt(0.25 / weight_totals[name]))
        for name in sizes
    }
    constraints = np.vstack(
        (
            scales["physical_lie"] * rows.flow,
            scales["gauge_generator_1"] * rows.gauge1,
            scales["gauge_generator_2"] * rows.gauge2,
            scales["chart_overlap"] * rows.overlap_difference,
        )
    )
    return _CombinedRows(
        values=values,
        constraints=constraints,
        group_ids=group_ids,
        family_ids=family_ids,
        point_ids=point_ids,
        block_scales=scales,
        block_weight_totals=weight_totals,
    )


def _known_control_metrics(
    training: _AtlasRows,
    calibration: _AtlasRows,
    known: dict[str, FloatArray],
    search: dict[str, Any],
) -> dict[str, float | int]:
    known_metrics = search["known_module_metrics"]
    combined_max = max(
        max(
            float(metric["training_lie_rms_per_coefficient_scale"]),
            float(metric["calibration_lie_rms_per_coefficient_scale"]),
        )
        for metric in known_metrics.values()
    )
    constraint_value_max = max(
        max(
            float(np.max(np.abs(training.values @ coefficients))),
            float(np.max(np.abs(calibration.values @ coefficients))),
        )
        for name, coefficients in known.items()
        if name.startswith("constraint:")
    )
    angular_overlap_max = max(
        max(
            float(np.max(np.abs(training.overlap_difference @ coefficients))),
            float(np.max(np.abs(calibration.overlap_difference @ coefficients))),
        )
        for name, coefficients in known.items()
        if name.startswith("known:")
    )
    return {
        "known_module_combined_constraint_rms_max": combined_max,
        "constraint_value_abs_max": constraint_value_max,
        "known_angular_chart_overlap_abs_max": angular_overlap_max,
        "parameter_weighted_angular_control_count": sum(
            name.startswith("known:") and "*" in name for name in known
        ),
    }


def main() -> None:
    args = _args()
    if Path(args.output).exists():
        raise RuntimeError("refusing to overwrite one-shot WP3 multi search output")
    common = _load_common()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    source_corpus = load_json(args.source_corpus)
    spatial_corpus = load_json(args.spatial_corpus)
    wp1_catalogue = load_json(args.wp1_catalogue)
    specification_lock = common.verify_specification_lock(args.spec)
    observed_runtime = common.verify_decision_runtime(spec["decision_runtime"])
    if (
        corpus.get("campaign") != spec["campaign"]
        or corpus.get("spec_sha256") != sha256_file(args.spec)
        or corpus.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or corpus.get("source_corpus_sha256") != sha256_file(args.source_corpus)
        or corpus.get("wp1_catalogue_sha256") != sha256_file(args.wp1_catalogue)
    ):
        raise RuntimeError("search corpus input mismatch")
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("corpus_sha256") != sha256_file(args.corpus)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("search lock does not bind the frozen inputs")

    prerequisites = {
        "wp2_multi": common.verify_prerequisite(
            spec["prerequisites"]["wp2_multi"],
            lock_path=WP2_ROOT / "reports/wp2_multi_v1_qualification_lock.json",
            record_path=WP2_ROOT / "reports/wp2_multi_v1_qualification_record.json",
            prefix="WP2-MULTIQ-v1",
        ),
        "wp1_catalogue": common.verify_prerequisite(
            spec["prerequisites"]["wp1_catalogue"],
            lock_path=WP1_ROOT / "reports/wp1_cat_n3bp_v1_qualification_lock.json",
            record_path=WP1_ROOT / "reports/wp1_cat_n3bp_v1_qualification_record.json",
            prefix="WP1-CAT-N3BP-v1",
        ),
        "wp1_spatial_n3bp": common.verify_prerequisite(
            spec["prerequisites"]["wp1_spatial_n3bp"],
            lock_path=SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_lock.json",
            record_path=SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_record.json",
            prefix="WP1Q-N3BP-SPATIAL-v2",
        ),
    }
    reserve = common.verify_publication_reserve(
        args.commitments,
        spec["prerequisites"]["sealed_publication_reserve_sha256"],
    )
    spatial_inputs = _verify_spatial_inputs(
        SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_record.json",
        args.spatial_corpus,
        args.spatial_development,
        args.spatial_calibration,
    )
    if sha256_file(args.source_corpus) != spec["prerequisites"][
        "source_exploration_corpus_sha256"
    ]:
        raise RuntimeError("source corpus hash changed")
    if sha256_file(args.wp1_catalogue) != spec["prerequisites"]["wp1_catalogue"][
        "native_catalogue_sha256"
    ]:
        raise RuntimeError("WP1 native catalogue hash changed")

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
    training_rows = _build_atlas_rows(
        "development",
        corpus,
        spatial_definitions=definitions,
        spatial_results=development_results,
        wp1_candidates=wp1_candidates,
    )
    calibration_rows = _build_atlas_rows(
        "calibration",
        corpus,
        spatial_definitions=definitions,
        spatial_results=calibration_results,
        wp1_candidates=wp1_candidates,
    )
    minimum_separation = min(
        training_rows.minimum_pair_separation_scaled_min,
        calibration_rows.minimum_pair_separation_scaled_min,
    )
    if minimum_separation < float(
        spec["data"]["minimum_pair_separation_scaled_min"]
    ):
        raise RuntimeError("search corpus is outside the collision-free overlap domain")
    training = _combine(training_rows)
    calibration = _combine(calibration_rows)
    search_spec = spec["search"]
    known = known_module_coefficients()
    search = search_quotient_modes(
        training.values,
        training.constraints,
        training.constraints,
        calibration.values,
        calibration.constraints,
        calibration.constraints,
        feature_names=feature_names(),
        known_module=known,
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
        candidate_lie_rms_max=float(
            search_spec["candidate_combined_constraint_rms_max"]
        ),
        candidate_gauge_lie_rms_max=float(
            search_spec["candidate_combined_constraint_rms_max"]
        ),
        calibration_ratio_floor=float(search_spec["calibration_ratio_floor"]),
        calibration_to_training_max=float(
            search_spec["calibration_to_training_max"]
        ),
        family_fold_subspace_projection_min=float(
            search_spec["family_fold_subspace_projection_min"]
        ),
        calibration_trajectory_drift_max=float(
            search_spec["calibration_trajectory_drift_max"]
        ),
        gauge_orbit_spread_max=float(search_spec["gauge_orbit_spread_max"]),
    )
    known_metrics = _known_control_metrics(
        training_rows, calibration_rows, known, search
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
    block_normalization_error = max(
        abs(
            training.block_weight_totals[name]
            * training.block_scales[name] ** 2
            - 0.25
        )
        for name in training.block_scales
    )
    block_normalization_error = max(
        block_normalization_error,
        max(
            abs(
                calibration.block_weight_totals[name]
                * calibration.block_scales[name] ** 2
                - 0.25
            )
            for name in calibration.block_scales
        ),
    )
    fixed_energy_abs_max = max(
        training_rows.fixed_energy_abs_max,
        calibration_rows.fixed_energy_abs_max,
    )
    chart_projection_max = max(
        training_rows.chart_projection_scaled_max,
        calibration_rows.chart_projection_scaled_max,
    )
    readiness_gates = [
        make_gate("prerequisite_pass_rate", 1.0, ">=", 1.0),
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate("search_lock_verified", 1, "==", 1),
        make_gate("sealed_reserve_intact", 1, "==", 1),
        make_gate("spatial_inputs_hash_verified", 1, "==", 1),
        make_gate(
            "feature_count",
            int(search["feature_count"]),
            "==",
            int(spec["library"]["search_feature_count"]),
        ),
        make_gate(
            "exact_known_module_rank",
            int(search["exact_known_module_rank"]),
            "==",
            int(spec["library"]["exact_known_module_rank"]),
        ),
        make_gate(
            "parameter_weighted_angular_control_count",
            int(known_metrics["parameter_weighted_angular_control_count"]),
            "==",
            9,
        ),
        make_gate(
            "known_module_combined_constraint_rms_max",
            float(known_metrics["known_module_combined_constraint_rms_max"]),
            "<=",
            float(search_spec["known_module_combined_constraint_rms_max"]),
        ),
        make_gate(
            "constraint_value_abs_max",
            float(known_metrics["constraint_value_abs_max"]),
            "<=",
            float(search_spec["constraint_value_abs_max"]),
        ),
        make_gate(
            "known_angular_chart_overlap_abs_max",
            float(known_metrics["known_angular_chart_overlap_abs_max"]),
            "<=",
            float(search_spec["chart_overlap_spread_max"]),
        ),
        make_gate(
            "known_module_projection_residual",
            float(search["exact_known_module_projection_residual"]),
            "<=",
            float(search_spec["known_module_projection_residual_max"]),
        ),
        make_gate(
            "all_generalized_modes_evaluated",
            int(search["evaluated_mode_count"]),
            "==",
            int(search["observable_value_rank"]),
        ),
        make_gate("decision_runtime_exact", 1, "==", 1),
        make_gate(
            "fixed_energy_checkpoint_abs_max",
            fixed_energy_abs_max,
            "<=",
            float(search_spec["fixed_energy_checkpoint_abs_max"]),
        ),
        make_gate(
            "chart_projection_state_scaled_max",
            chart_projection_max,
            "<=",
            float(search_spec["chart_projection_state_scaled_max"]),
        ),
        make_gate("chart_count", training_rows.chart_count, "==", 3),
        make_gate("gauge_pair_count", training_rows.gauge_pair_count, "==", 3),
        make_gate("constraint_block_normalization_error", block_normalization_error, "<=", 2e-15),
        make_gate(
            "minimum_pair_separation_scaled_min",
            minimum_separation,
            ">=",
            float(spec["data"]["minimum_pair_separation_scaled_min"]),
        ),
        make_gate(
            "spectral_decision_partition_consistent",
            int(spectral_consistent),
            "==",
            1,
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
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "corpus_sha256": sha256_file(args.corpus),
        "source_corpus_sha256": sha256_file(args.source_corpus),
        "wp1_catalogue_sha256": sha256_file(args.wp1_catalogue),
        "prerequisites": prerequisites,
        "sealed_publication_reserve": reserve,
        "qualified_spatial_inputs": spatial_inputs,
        "runtime": runtime_fingerprint(),
        "decision_runtime": observed_runtime,
        "readiness_gates": readiness_gates,
        "search_ready": search_ready,
        "constraint_block_scales": {
            "training": training.block_scales,
            "calibration": calibration.block_scales,
        },
        "matrix_hashes": {
            "training_values": _matrix_sha256(training_rows.values),
            "training_physical_lie": _matrix_sha256(training_rows.flow),
            "training_gauge_generator_1": _matrix_sha256(training_rows.gauge1),
            "training_gauge_generator_2": _matrix_sha256(training_rows.gauge2),
            "training_chart_overlap": _matrix_sha256(training_rows.overlap_difference),
            "training_combined_values": _matrix_sha256(training.values),
            "training_combined_constraints": _matrix_sha256(training.constraints),
            "calibration_values": _matrix_sha256(calibration_rows.values),
            "calibration_physical_lie": _matrix_sha256(calibration_rows.flow),
            "calibration_gauge_generator_1": _matrix_sha256(calibration_rows.gauge1),
            "calibration_gauge_generator_2": _matrix_sha256(calibration_rows.gauge2),
            "calibration_chart_overlap": _matrix_sha256(calibration_rows.overlap_difference),
            "calibration_combined_values": _matrix_sha256(calibration.values),
            "calibration_combined_constraints": _matrix_sha256(calibration.constraints),
        },
        "source_summary": {
            "training_groups": len(set(training_rows.group_ids)),
            "calibration_groups": len(set(calibration_rows.group_ids)),
            "training_physical_points": training_rows.physical_point_count,
            "calibration_physical_points": calibration_rows.physical_point_count,
            "training_atlas_rows": training_rows.values.shape[0],
            "calibration_atlas_rows": calibration_rows.values.shape[0],
            "training_combined_constraint_rows": training.constraints.shape[0],
            "calibration_combined_constraint_rows": calibration.constraints.shape[0],
            "chart_count": training_rows.chart_count,
            "gauge_pair_count": training_rows.gauge_pair_count,
            "fixed_energy_checkpoint_abs_max": fixed_energy_abs_max,
            "chart_projection_state_scaled_max": chart_projection_max,
            "minimum_pair_separation_scaled_min": minimum_separation,
        },
        "known_control_metrics": known_metrics,
        "search": search,
    }
    atomic_write_json(args.output, payload)
    print(
        f"{spec['campaign']}: {status}; SEARCH_READY={search_ready}; "
        f"candidate_subspaces={candidate_count}; interpretation=PROHIBITED"
    )


if __name__ == "__main__":
    main()
