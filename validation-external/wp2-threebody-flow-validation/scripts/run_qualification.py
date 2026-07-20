#!/usr/bin/env python
"""Execute one WP2-3BFLOWQ-v1 qualification split."""

from __future__ import annotations

import argparse
import importlib.util
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
from src.python.ks import KSPhaseState, project_cotangent  # noqa: E402
from src.python.n3bp_qualification import (  # noqa: E402
    InertialState,
    SystemParameters,
    newtonian_accelerations,
    newtonian_rhs,
)
from src.python.pairwise_ks import (  # noqa: E402
    CanonicalPairwiseKSLift,
    PairwiseKSResult,
    lift_pairwise_ks,
)
from src.python.threebody_flow import (  # noqa: E402
    canonical_jacobi_flow,
    euclidean_reduced_flow,
    pairwise_ks_flow,
)
from src.python.threebody_reduction import (  # noqa: E402
    JacobiPhaseState,
    reduce_euclidean,
)


SPATIAL_ROOT = REPO_ROOT / "validation-external/wp3-spatial-validation"
SPATIAL_LOCK = SPATIAL_ROOT / "reports/wp3_spatial_qualification_lock.json"
SPATIAL_RECORD = SPATIAL_ROOT / "reports/wp3_spatial_qualification_record.json"
KS_LOCK = REPO_ROOT / "validation-external/wp2-ks-validation/reports/wp2_ks_qualification_lock.json"
KS_RECORD = REPO_ROOT / "validation-external/wp2-ks-validation/reports/wp2_ks_qualification_record.json"
REFERENCE = CAMPAIGN_ROOT / "reference/independent_reduction.py"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--spatial-results", required=True)
    parser.add_argument(
        "--split", choices=("development", "calibration", "holdout"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    return parser.parse_args()


def _reference_module():
    spec = importlib.util.spec_from_file_location("independent_reduction", REFERENCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load clean-room reduction reference")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    definitions = (
        ("wp1_spatial_n3bp", SPATIAL_LOCK, SPATIAL_RECORD, "WP1Q-N3BP-SPATIAL-v1"),
        ("wp2_kepler_ks", KS_LOCK, KS_RECORD, "WP2KSQ-v1"),
    )
    output = {}
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
            raise RuntimeError(f"invalid prerequisite: {name}")
        output[name] = {
            "status": "PASS",
            "qualification_id": record["qualification_id"],
            "record_sha256": sha256_file(record_path),
            "lock_sha256": lock["lock_sha256"],
        }
    return output


def _rotation_derivative(vector: np.ndarray, angle: float) -> np.ndarray:
    cosine, sine = np.cos(angle), np.sin(angle)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    return np.concatenate((rotation @ vector[:2], rotation @ vector[2:]))


def _scale_error(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.max(np.abs(first - second)) / max(1.0, float(np.max(np.abs(second)))))


def _evaluate_state(
    state: InertialState,
    parameters: SystemParameters,
    reference: Any,
    execution: dict[str, Any],
) -> dict[str, float]:
    masses = np.asarray(parameters.masses)
    clean = reference.jacobi_reduce(state.positions, state.velocities, masses)
    production = JacobiPhaseState.from_inertial(state, parameters)
    clean_vector = np.concatenate(
        (clean["rho"], clean["lambda"], clean["p_rho"], clean["p_lambda"])
    )
    independent_state_error = _scale_error(
        clean_vector, production.quotient.as_canonical_vector()
    )
    clean_positions, clean_velocities = reference.jacobi_reconstruct(clean, masses)
    independent_roundtrip = max(
        _scale_error(clean_positions, state.positions),
        _scale_error(clean_velocities, state.velocities),
    )
    independent_frame = reference.body_frame(clean["rho"], clean["lambda"])
    euclidean = reduce_euclidean(state, parameters)
    independent_frame_error = _scale_error(
        independent_frame, euclidean.reconstruction.body_frame
    )

    canonical = canonical_jacobi_flow(production.quotient)
    full_rhs = newtonian_rhs(0.0, state.values, parameters)
    step = float(execution["finite_difference_step"])
    clean_tangent = reference.jacobi_reduce(
        full_rhs[:9].reshape(3, 3),
        full_rhs[9:].reshape(3, 3),
        masses,
    )
    clean_tangent_vector = np.concatenate(
        (
            clean_tangent["rho"],
            clean_tangent["lambda"],
            clean_tangent["p_rho"],
            clean_tangent["p_lambda"],
        )
    )
    canonical_error = _scale_error(canonical.derivative, clean_tangent_vector)

    hamiltonian_lie = abs(
        reference.newtonian_energy_lie(
            state.positions,
            state.velocities,
            full_rhs[9:].reshape(3, 3),
            masses,
            float(parameters.gravitational_constant),
        )
    ) / max(
        1.0, abs(canonical.hamiltonian)
    )

    reduced = euclidean_reduced_flow(production.quotient)
    plus_euclidean = reduce_euclidean(
        InertialState(state.values + step * full_rhs), parameters
    )
    minus_euclidean = reduce_euclidean(
        InertialState(state.values - step * full_rhs), parameters
    )
    quotient_fd = (
        plus_euclidean.quotient.as_orbit_coordinates()
        - minus_euclidean.quotient.as_orbit_coordinates()
    ) / (2.0 * step)
    frame_fd = (
        plus_euclidean.reconstruction.body_frame
        - minus_euclidean.reconstruction.body_frame
    ) / (2.0 * step)

    angles = np.asarray(execution["gauge_angles"], dtype=float)
    lifted = lift_pairwise_ks(state, parameters, angles=angles)
    ks_flow = pairwise_ks_flow(lifted, parameters)
    accelerations = newtonian_accelerations(state.positions, parameters)
    pair_indices = ((0, 1), (1, 2), (2, 0))
    projection_error = 0.0
    for ks_state, derivative, (first, second) in zip(
        lifted.lift.pair_states,
        ks_flow.pair_derivatives,
        pair_indices,
        strict=True,
    ):
        plus = project_cotangent(
            KSPhaseState(
                ks_state.q + step * derivative.q_dot,
                ks_state.Q + step * derivative.Q_dot,
            ),
            require_zero_level=False,
        )
        minus = project_cotangent(
            KSPhaseState(
                ks_state.q - step * derivative.q_dot,
                ks_state.Q - step * derivative.Q_dot,
            ),
            require_zero_level=False,
        )
        projected_fd = (plus.as_vector() - minus.as_vector()) / (2.0 * step)
        reduced_mass = masses[first] * masses[second] / (masses[first] + masses[second])
        expected = np.concatenate(
            (
                state.velocities[second] - state.velocities[first],
                reduced_mass * (accelerations[second] - accelerations[first]),
            )
        )
        projection_error = max(projection_error, _scale_error(projected_fd, expected))

    transformed_lift = lifted.lift.act_s1_cubed(angles)
    transformed = PairwiseKSResult(transformed_lift, lifted.reconstruction)
    transformed_flow = pairwise_ks_flow(transformed, parameters)
    gauge_error = 0.0
    for original_derivative, transformed_derivative, angle in zip(
        ks_flow.pair_derivatives,
        transformed_flow.pair_derivatives,
        angles,
        strict=True,
    ):
        gauge_error = max(
            gauge_error,
            _scale_error(
                transformed_derivative.q_dot,
                _rotation_derivative(original_derivative.q_dot, float(angle)),
            ),
            _scale_error(
                transformed_derivative.Q_dot,
                _rotation_derivative(original_derivative.Q_dot, float(angle)),
            ),
        )
    return {
        "independent_jacobi_state_scaled": independent_state_error,
        "independent_jacobi_roundtrip_scaled": independent_roundtrip,
        "independent_body_frame_scaled": independent_frame_error,
        "canonical_tangent_scaled": canonical_error,
        "hamiltonian_lie_scaled": hamiltonian_lie,
        "reduced_quotient_fd_scaled": _scale_error(
            reduced.quotient_derivative, quotient_fd
        ),
        "reconstruction_frame_fd_scaled": _scale_error(
            reduced.body_frame_derivative, frame_fd
        ),
        "pairwise_projection_fd_scaled": projection_error,
        "pairwise_xi_derivative_abs": float(np.max(np.abs(ks_flow.xi_derivatives))),
        "pairwise_position_closure_derivative": float(
            np.linalg.norm(ks_flow.position_closure_derivative)
        ),
        "pairwise_velocity_closure_derivative": float(
            np.linalg.norm(ks_flow.velocity_closure_derivative)
        ),
        "pairwise_s1_covariance_scaled": gauge_error,
    }


def main() -> None:
    args = _args()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    spatial_corpus = load_json(args.spatial_corpus)
    spatial_results = load_json(args.spatial_results)
    lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires the flow lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    prerequisites = _verify_prerequisites(spec)
    reference = _reference_module()
    symbolic = reference.exact_canonical_residual()
    symbolic_pass = int(all(value == "0" for row in symbolic for value in row))
    source_definitions = {case["case_id"]: case for case in spatial_corpus["cases"]}
    source_results = {case["case_id"]: case for case in spatial_results["cases"]}
    selected = [case for case in corpus["cases"] if case["split"] == args.split]
    output_cases = []
    for case in selected:
        source_id = case["source_case_id"]
        definition = source_definitions[source_id]
        source = source_results[source_id]
        parameters = SystemParameters(
            [float(value) for value in definition["masses_decimal"]], 1.0
        )
        metrics = []
        for index in case["checkpoint_indices"]:
            state_values = np.array(
                [float(value) for value in source["oracle"]["states_decimal"][index]]
            )
            metrics.append(
                _evaluate_state(InertialState(state_values), parameters, reference, spec["execution"])
            )
        aggregated = {
            name: max(float(item[name]) for item in metrics)
            for name in metrics[0]
        }
        aggregated["symbolic_canonical_pass"] = symbolic_pass
        output_cases.append(
            {
                "case_id": case["case_id"],
                "source_case_id": source_id,
                "success": True,
                "metrics": aggregated,
            }
        )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": args.split,
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "spatial_results_sha256": sha256_file(args.spatial_results),
        "prerequisites": prerequisites,
        "structural": {"global_sundman_qualified": 0},
        "runtime": runtime_fingerprint(),
        "cases": output_cases,
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)


if __name__ == "__main__":
    main()
