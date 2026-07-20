#!/usr/bin/env python
"""Execute one bounded WP2-3BRQ-v1 compositional qualification split."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from src.python.n3bp_qualification import (  # noqa: E402
    DOP853Config,
    InertialState,
    SystemParameters,
    angular_momentum,
    figure_eight_choreography,
    lagrange_equilateral,
    normalize_center_of_mass,
    propagate_dop853,
    total_energy,
)
from src.python.pairwise_ks import (  # noqa: E402
    lift_pairwise_ks,
    pairwise_dimension_accounting,
)
from src.python.threebody_reduction import (  # noqa: E402
    JacobiPhaseState,
    ReductionChartSingularity,
    jacobi_coordinate_matrix,
    reduce_euclidean,
    reduce_translation,
)


WP2_LOCK = (
    REPO_ROOT
    / "validation-external/wp2-ks-validation/reports/wp2_ks_qualification_lock.json"
)
WP2_RECORD = (
    REPO_ROOT
    / "validation-external/wp2-ks-validation/reports/wp2_ks_qualification_record.json"
)
N3BP_LOCK = (
    REPO_ROOT
    / "validation-external/wp1-n3bp-validation/reports/wp1_n3bp_qualification_lock.json"
)
N3BP_RECORD = (
    REPO_ROOT
    / "validation-external/wp1-n3bp-validation/reports/wp1_n3bp_qualification_record.json"
)
N3BP_CORPUS = (
    REPO_ROOT / "validation-external/wp1-n3bp-validation/data/qualification_corpus.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument(
        "--split", choices=("development", "calibration", "holdout"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    return parser.parse_args()


def _verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    definitions = (
        ("wp2_ks", WP2_LOCK, WP2_RECORD, "WP2KSQ-v1"),
        ("wp1_n3bp", N3BP_LOCK, N3BP_RECORD, "WP1Q-N3BP-v1"),
    )
    results: dict[str, Any] = {}
    for name, lock_path, record_path, prefix in definitions:
        expected = spec["prerequisites"][name]
        lock = verify_lock(lock_path, REPO_ROOT, expected_prefix=prefix)
        record = load_json(record_path)
        valid = bool(
            record.get("status") == "PASS"
            and record.get("qualification_id") == expected["qualification_id"]
            and record.get("qualification_id") == lock["qualification_id"]
            and record.get("lock_sha256") == expected["lock_sha256"]
            and record.get("lock_sha256") == lock["lock_sha256"]
            and sha256_file(record_path) == expected["record_sha256"]
        )
        if not valid:
            raise RuntimeError(f"invalid prerequisite qualification: {name}")
        results[name] = {
            "status": "PASS",
            "qualification_id": record["qualification_id"],
            "lock_sha256": lock["lock_sha256"],
            "record_sha256": sha256_file(record_path),
        }
    return results


def _rotation_xyz(angles: list[float]) -> np.ndarray:
    x_angle, y_angle, z_angle = (float(value) for value in angles)
    cx, sx = np.cos(x_angle), np.sin(x_angle)
    cy, sy = np.cos(y_angle), np.sin(y_angle)
    cz, sz = np.cos(z_angle), np.sin(z_angle)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return rz @ ry @ rx


def _source_case(case: dict[str, Any]) -> tuple[InertialState, SystemParameters, float]:
    case_type = case["case_type"]
    if case_type == "lagrange":
        orbit = lagrange_equilateral(
            side_length=float(case["side_length"]),
            mass=float(case["mass"]),
            gravitational_constant=float(case["gravitational_constant"]),
            phase=float(case["phase"]),
        )
        rotation = _rotation_xyz(case["rotation_xyz"])
        state = InertialState.from_components(
            orbit.initial_state.positions @ rotation.T,
            orbit.initial_state.velocities @ rotation.T,
        )
        return state, orbit.parameters, orbit.period
    if case_type == "figure_eight":
        orbit = figure_eight_choreography()
        return orbit.initial_state, orbit.parameters, orbit.period
    if case_type == "sjtu_periodic":
        masses = np.array([float(value) for value in case["masses"]])
        parameters = SystemParameters(masses, gravitational_constant=1.0)
        x1 = float(case["x1"])
        v1 = float(case["v1"])
        v2 = float(case["v2"])
        state = InertialState.from_components(
            [[x1, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            [
                [0.0, v1, 0.0],
                [0.0, v2, 0.0],
                [0.0, -(masses[0] * v1 + masses[1] * v2) / masses[2], 0.0],
            ],
        )
        return (
            normalize_center_of_mass(state, parameters),
            parameters,
            float(case["period"]),
        )
    raise ValueError(f"unsupported source case type: {case_type}")


def _proper_rotation(rng: np.random.Generator) -> np.ndarray:
    rotation, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    if np.linalg.det(rotation) < 0.0:
        rotation[:, 0] *= -1.0
    return rotation


def _scales(
    state: InertialState, parameters: SystemParameters
) -> tuple[float, float, float]:
    distances = [
        float(np.linalg.norm(state.positions[second] - state.positions[first]))
        for first, second in ((0, 1), (1, 2), (2, 0))
    ]
    length = max(distances)
    velocity = max(
        float(
            np.sqrt(parameters.gravitational_constant * parameters.total_mass / length)
        ),
        float(np.max(np.linalg.norm(state.velocities, axis=1))),
    )
    momentum = float(np.max(parameters.masses)) * velocity
    return length, velocity, momentum


def _state_errors(
    first: InertialState,
    second: InertialState,
    length_scale: float,
    velocity_scale: float,
) -> tuple[float, float]:
    position = float(
        np.max(np.linalg.norm(first.positions - second.positions, axis=1))
        / length_scale
    )
    velocity = float(
        np.max(np.linalg.norm(first.velocities - second.velocities, axis=1))
        / velocity_scale
    )
    return position, velocity


def _sample_metrics(
    state: InertialState,
    parameters: SystemParameters,
    rng: np.random.Generator,
    chart_tolerance: float,
) -> dict[str, float | int]:
    length_scale, velocity_scale, momentum_scale = _scales(state, parameters)
    translation = reduce_translation(state, parameters)
    jacobi = JacobiPhaseState.from_inertial(state, parameters)
    jacobi_reconstructed = jacobi.to_inertial()
    jacobi_position, jacobi_velocity = _state_errors(
        state, jacobi_reconstructed, length_scale, velocity_scale
    )

    coordinate = np.kron(jacobi_coordinate_matrix(parameters), np.eye(3))
    momentum = np.linalg.inv(coordinate).T
    transform = np.block(
        [
            [coordinate, np.zeros((9, 9))],
            [np.zeros((9, 9)), momentum],
        ]
    )
    canonical = np.block(
        [[np.zeros((9, 9)), np.eye(9)], [-np.eye(9), np.zeros((9, 9))]]
    )
    symplectic_error = float(
        np.max(np.abs(transform @ canonical @ transform.T - canonical))
    )
    old_momenta = (parameters.masses[:, None] * state.velocities).ravel()
    variation = rng.normal(size=9)
    new_variation = coordinate @ variation
    old_one_form = float(np.dot(old_momenta, variation))
    new_one_form = float(np.dot(jacobi.as_canonical_vector()[9:], new_variation))
    one_form_error = abs(old_one_form - new_one_form) / max(
        1.0, abs(old_one_form), abs(new_one_form)
    )

    center_energy = float(
        np.dot(
            translation.reconstruction.total_momentum,
            translation.reconstruction.total_momentum,
        )
        / (2.0 * parameters.total_mass)
    )
    source_energy = total_energy(state, parameters)
    split_energy = translation.quotient.total_energy() + center_energy
    energy_error = abs(source_energy - split_energy) / max(
        1.0, abs(source_energy), abs(split_energy)
    )
    source_angular = angular_momentum(state, parameters)
    split_angular = (
        np.cross(
            translation.reconstruction.center_of_mass,
            translation.reconstruction.total_momentum,
        )
        + translation.quotient.angular_momentum()
    )
    angular_error = float(np.linalg.norm(source_angular - split_angular)) / max(
        1.0, float(np.linalg.norm(source_angular)), float(np.linalg.norm(split_angular))
    )

    pairwise = lift_pairwise_ks(
        state,
        parameters,
        angles=rng.uniform(-np.pi, np.pi, size=3),
    )
    pair_reconstructed = pairwise.reconstruct()
    pair_position, pair_velocity = _state_errors(
        state, pair_reconstructed, length_scale, velocity_scale
    )
    residuals = pairwise.lift.constraint_residuals()
    transformed = pairwise.lift.act_s1_cubed(rng.uniform(-np.pi, np.pi, size=3))
    projection_error = 0.0
    for first, second in zip(
        pairwise.lift.project_pairs(), transformed.project_pairs(), strict=True
    ):
        projection_error = max(
            projection_error,
            float(np.linalg.norm(first.x - second.x)) / length_scale,
            float(np.linalg.norm(first.p - second.p)) / momentum_scale,
        )
    transformed_state = transformed.to_inertial(pairwise.reconstruction)
    gauge_position, gauge_velocity = _state_errors(
        state, transformed_state, length_scale, velocity_scale
    )

    rho = translation.quotient.rho
    lambda_vector = translation.quotient.lambda_vector
    denominator = float(np.linalg.norm(rho) * np.linalg.norm(lambda_vector))
    cross_ratio = (
        0.0
        if denominator == 0.0
        else float(np.linalg.norm(np.cross(rho, lambda_vector)) / denominator)
    )
    metrics: dict[str, float | int] = {
        "jacobi_roundtrip_scaled": max(jacobi_position, jacobi_velocity),
        "jacobi_symplectic_error": symplectic_error,
        "jacobi_one_form_scaled": one_form_error,
        "energy_split_scaled": energy_error,
        "angular_momentum_split_scaled": angular_error,
        "pairwise_position_roundtrip_scaled": pair_position,
        "pairwise_velocity_roundtrip_scaled": pair_velocity,
        "pairwise_xi_abs": residuals.momentum_map_max,
        "pairwise_position_closure_scaled": residuals.position_closure_norm
        / length_scale,
        "pairwise_velocity_closure_scaled": residuals.velocity_closure_norm
        / velocity_scale,
        "pairwise_s1_projection_scaled": projection_error,
        "pairwise_s1_reconstruction_scaled": max(gauge_position, gauge_velocity),
        "generic_samples": 0,
        "singular_samples": 0,
        "correctly_classified_singular_samples": 0,
    }
    if cross_ratio <= chart_tolerance:
        metrics["singular_samples"] = 1
        try:
            reduce_euclidean(
                state,
                parameters,
                relative_tolerance=chart_tolerance,
            )
        except ReductionChartSingularity:
            metrics["correctly_classified_singular_samples"] = 1
        return metrics

    reduced = reduce_euclidean(
        state,
        parameters,
        relative_tolerance=chart_tolerance,
    )
    metrics["generic_samples"] = 1
    reconstructed = reduced.reconstruct()
    reduced_position, reduced_velocity = _state_errors(
        state, reconstructed, length_scale, velocity_scale
    )
    rotation = _proper_rotation(rng)
    shift = rng.normal(size=3) * length_scale
    boost = rng.normal(size=3) * velocity_scale
    moved = InertialState.from_components(
        state.positions @ rotation.T + shift,
        state.velocities @ rotation.T + boost,
    )
    moved_reduced = reduce_euclidean(
        moved,
        parameters,
        relative_tolerance=chart_tolerance,
    )
    first = reduced.quotient
    second = moved_reduced.quotient
    shape_error = float(
        np.max(np.abs(first.shape_coordinates - second.shape_coordinates))
        / length_scale
    )
    momentum_error = max(
        float(np.max(np.abs(first.p_rho_body - second.p_rho_body))) / momentum_scale,
        float(np.max(np.abs(first.p_lambda_body - second.p_lambda_body)))
        / momentum_scale,
    )
    quotient_energy = first.total_energy()
    translation_energy = translation.quotient.total_energy()
    metrics.update(
        {
            "euclidean_roundtrip_scaled": max(reduced_position, reduced_velocity),
            "euclidean_rigid_invariance_scaled": max(shape_error, momentum_error),
            "euclidean_energy_scaled": abs(quotient_energy - translation_energy)
            / max(1.0, abs(quotient_energy), abs(translation_energy)),
        }
    )
    return metrics


def _merge_samples(samples: list[dict[str, float | int]]) -> dict[str, float | int]:
    additive = {
        "generic_samples",
        "singular_samples",
        "correctly_classified_singular_samples",
    }
    keys = {key for sample in samples for key in sample}
    merged: dict[str, float | int] = {}
    for key in keys:
        values = [sample[key] for sample in samples if key in sample]
        merged[key] = sum(values) if key in additive else max(values)
    singular = int(merged.get("singular_samples", 0))
    correct = int(merged.get("correctly_classified_singular_samples", 0))
    merged["singular_classification_rate"] = (
        1.0 if singular == 0 else correct / singular
    )
    return merged


def evaluate_case(
    case: dict[str, Any],
    source_cases: dict[str, dict[str, Any]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    source = source_cases[str(case["source_case_id"])]
    initial, parameters, period = _source_case(source)
    times = np.array(case["sample_fractions"], dtype=float) * period
    trajectory = propagate_dop853(
        initial,
        times,
        parameters,
        config=DOP853Config(
            rtol=float(spec["execution"]["production_rtol"]),
            atol=float(spec["execution"]["production_atol"]),
            max_step=period
            * float(spec["execution"]["production_max_step_fraction_of_period"]),
        ),
    )
    rng = np.random.default_rng(int(case["evaluation_seed"]))
    samples = [
        _sample_metrics(
            InertialState(values),
            parameters,
            rng,
            float(spec["execution"]["chart_relative_tolerance"]),
        )
        for values in trajectory.states
    ]
    return {
        "case_id": str(case["case_id"]),
        "source_case_id": str(case["source_case_id"]),
        "sample_count": len(samples),
        "success": True,
        "metrics": _merge_samples(samples),
    }


def structural_metrics(spec: dict[str, Any], split: str) -> dict[str, float | int]:
    rng = np.random.default_rng(
        int(spec["execution"]["structural_seed_by_split"][split])
    )
    samples: list[dict[str, float | int]] = []
    count = int(spec["execution"]["structural_random_cases_per_split"])
    for _ in range(count):
        while True:
            positions = rng.normal(size=(3, 3))
            rho = positions[1] - positions[0]
            lambda_vector = positions[2] - 0.5 * (positions[0] + positions[1])
            denominator = np.linalg.norm(rho) * np.linalg.norm(lambda_vector)
            cross_ratio = (
                0.0
                if denominator == 0.0
                else np.linalg.norm(np.cross(rho, lambda_vector)) / denominator
            )
            distances = [
                np.linalg.norm(positions[second] - positions[first])
                for first, second in ((0, 1), (1, 2), (2, 0))
            ]
            if min(distances) > 0.2 and cross_ratio > 0.15:
                break
        state = InertialState.from_components(positions, rng.normal(size=(3, 3)))
        parameters = SystemParameters(
            rng.uniform(0.35, 2.5, size=3),
            gravitational_constant=float(rng.uniform(0.25, 1.8)),
        )
        samples.append(
            _sample_metrics(
                state,
                parameters,
                rng,
                float(spec["execution"]["chart_relative_tolerance"]),
            )
        )
    merged = _merge_samples(samples)
    dimensions = pairwise_dimension_accounting()
    merged.update(
        {
            "translation_dimension": 12,
            "rotation_poisson_dimension": 9,
            "generic_leaf_dimension": 8,
            "pairwise_dimension": int(
                dimensions["translation_reduced_n3bp_phase_space"]
            ),
            "global_sundman_qualified": int(
                bool(dimensions["global_sundman_time_qualified"])
            ),
        }
    )
    return merged


def main() -> None:
    args = parse_args()
    output = Path(args.output).resolve()
    downstream_lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires a downstream lock")
        if output.exists():
            raise RuntimeError(
                "refusing to execute the WP2-3BRQ holdout more than once"
            )
        downstream_lock = verify_lock(
            args.lock, REPO_ROOT, expected_prefix="WP2-3BRQ-v1"
        )

    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    if downstream_lock is not None:
        if downstream_lock["spec_sha256"] != sha256_file(args.spec):
            raise RuntimeError("holdout specification does not match the lock")
        if downstream_lock["corpus_sha256"] != sha256_file(args.corpus):
            raise RuntimeError("holdout corpus does not match the lock")
    prerequisites = _verify_prerequisites(spec)
    source_payload = load_json(N3BP_CORPUS)
    source_cases = {str(case["case_id"]): case for case in source_payload["cases"]}
    cases = [case for case in corpus["cases"] if case["split"] == args.split]
    if not cases:
        raise RuntimeError(f"no {args.split} cases in the downstream corpus")

    results: list[dict[str, Any]] = []
    for case in cases:
        try:
            results.append(evaluate_case(case, source_cases, spec))
        except Exception as error:
            results.append(
                {
                    "case_id": str(case["case_id"]),
                    "source_case_id": str(case["source_case_id"]),
                    "success": False,
                    "error": f"{type(error).__name__}: {error}",
                    "metrics": {},
                }
            )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": args.split,
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "source_corpus_sha256": sha256_file(N3BP_CORPUS),
        "runtime": runtime_fingerprint(),
        "prerequisites": prerequisites,
        "structural_metrics": structural_metrics(spec, args.split),
        "cases": results,
    }
    if downstream_lock is not None:
        payload["qualification_id"] = downstream_lock["qualification_id"]
        payload["lock_sha256"] = downstream_lock["lock_sha256"]
    atomic_write_json(output, payload)
    print(
        f"WP2-3BRQ-v1 {args.split}: "
        f"{sum(bool(item['success']) for item in results)}/{len(results)} cases"
    )


if __name__ == "__main__":
    main()
