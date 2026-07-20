#!/usr/bin/env python
"""Execute one bounded WP1Q-N3BP-v1 qualification split."""

from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import sys
from typing import Any, Callable

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
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
    IAS15Config,
    InertialState,
    SystemParameters,
    center_of_mass_position,
    center_of_mass_velocity,
    figure_eight_choreography,
    lagrange_analytic_state,
    lagrange_equilateral,
    measure_invariant_drift,
    newtonian_rhs,
    normalize_center_of_mass,
    propagate_dop853,
    propagate_rebound_ias15,
)


AnalyticEvaluator = Callable[[float], InertialState]


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


def _rotation_xyz(angles: list[float]) -> np.ndarray:
    x_angle, y_angle, z_angle = (float(value) for value in angles)
    cx, sx = np.cos(x_angle), np.sin(x_angle)
    cy, sy = np.cos(y_angle), np.sin(y_angle)
    cz, sz = np.cos(z_angle), np.sin(z_angle)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return rz @ ry @ rx


def _rotate_state(state: InertialState, rotation: np.ndarray) -> InertialState:
    return InertialState.from_components(
        state.positions @ rotation.T,
        state.velocities @ rotation.T,
    )


def build_case(
    case: dict[str, Any],
) -> tuple[InertialState, SystemParameters, float, AnalyticEvaluator | None]:
    case_type = case["case_type"]
    if case_type == "lagrange":
        orbit = lagrange_equilateral(
            side_length=float(case["side_length"]),
            mass=float(case["mass"]),
            gravitational_constant=float(case["gravitational_constant"]),
            phase=float(case["phase"]),
        )
        rotation = _rotation_xyz(case["rotation_xyz"])
        initial = _rotate_state(orbit.initial_state, rotation)

        def analytic(time: float) -> InertialState:
            return _rotate_state(lagrange_analytic_state(orbit, time), rotation)

        return initial, orbit.parameters, orbit.period, analytic
    if case_type == "figure_eight":
        orbit = figure_eight_choreography()
        return orbit.initial_state, orbit.parameters, orbit.period, None
    if case_type == "sjtu_periodic":
        masses = np.array([float(value) for value in case["masses"]])
        x1 = float(case["x1"])
        v1 = float(case["v1"])
        v2 = float(case["v2"])
        parameters = SystemParameters(masses, gravitational_constant=1.0)
        positions = np.array([[x1, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        velocities = np.array(
            [
                [0.0, v1, 0.0],
                [0.0, v2, 0.0],
                [0.0, -(masses[0] * v1 + masses[1] * v2) / masses[2], 0.0],
            ]
        )
        initial = normalize_center_of_mass(
            InertialState.from_components(positions, velocities), parameters
        )
        return initial, parameters, float(case["period"]), None
    raise ValueError(f"unsupported N3BP case type: {case_type}")


def _scales(state: InertialState, parameters: SystemParameters) -> tuple[float, float]:
    positions = state.positions
    length = max(
        float(np.linalg.norm(positions[0] - positions[1])),
        float(np.linalg.norm(positions[0] - positions[2])),
        float(np.linalg.norm(positions[1] - positions[2])),
    )
    velocity = float(
        np.sqrt(parameters.gravitational_constant * parameters.total_mass / length)
    )
    return length, velocity


def evaluate_case(case: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    initial, parameters, period, analytic = build_case(case)
    checkpoints = int(spec["execution"]["checkpoints_per_period"])
    times = np.linspace(0.0, period, checkpoints)
    max_step = period * float(
        spec["execution"]["production_max_step_fraction_of_period"]
    )
    dop853 = propagate_dop853(
        initial,
        times,
        parameters,
        config=DOP853Config(
            rtol=float(spec["execution"]["production_rtol"]),
            atol=float(spec["execution"]["production_atol"]),
            max_step=max_step,
        ),
    )
    adaptive_mode = (
        spec["execution"]["rebound_adaptive_mode_figure_eight"]
        if case["case_type"] == "figure_eight"
        else spec["execution"]["rebound_adaptive_mode_sjtu"]
    )
    reference = propagate_rebound_ias15(
        initial,
        times,
        parameters,
        config=IAS15Config(
            epsilon=float(spec["execution"]["rebound_epsilon"]),
            adaptive_mode=str(adaptive_mode),
        ),
    )
    length_scale, velocity_scale = _scales(initial, parameters)
    dop_positions = dop853.states[:, :9].reshape(-1, 3, 3)
    dop_velocities = dop853.states[:, 9:].reshape(-1, 3, 3)
    ref_positions = reference.states[:, :9].reshape(-1, 3, 3)
    ref_velocities = reference.states[:, 9:].reshape(-1, 3, 3)
    position_error = float(
        np.max(np.linalg.norm(dop_positions - ref_positions, axis=2)) / length_scale
    )
    velocity_error = float(
        np.max(np.linalg.norm(dop_velocities - ref_velocities, axis=2)) / velocity_scale
    )
    closure_position = float(
        np.max(np.linalg.norm(dop_positions[-1] - initial.positions, axis=1))
        / length_scale
    )
    closure_velocity = float(
        np.max(np.linalg.norm(dop_velocities[-1] - initial.velocities, axis=1))
        / velocity_scale
    )
    separations = np.concatenate(
        [
            np.linalg.norm(dop_positions[:, 0] - dop_positions[:, 1], axis=1),
            np.linalg.norm(dop_positions[:, 0] - dop_positions[:, 2], axis=1),
            np.linalg.norm(dop_positions[:, 1] - dop_positions[:, 2], axis=1),
        ]
    )
    invariant_drift = measure_invariant_drift(dop853.states, parameters)
    com_positions = np.array(
        [center_of_mass_position(state, parameters) for state in dop853.states]
    )
    com_velocities = np.array(
        [center_of_mass_velocity(state, parameters) for state in dop853.states]
    )
    metrics: dict[str, float] = {
        "dop853_rebound_position_error_scaled": position_error,
        "dop853_rebound_velocity_error_scaled": velocity_error,
        "periodic_closure_position_scaled": closure_position,
        "periodic_closure_velocity_scaled": closure_velocity,
        "relative_energy_drift": invariant_drift.max_relative_energy,
        "linear_momentum_drift_scaled": invariant_drift.max_linear_momentum
        / (parameters.total_mass * velocity_scale),
        "angular_momentum_drift_scaled": invariant_drift.max_angular_momentum
        / (parameters.total_mass * length_scale * velocity_scale),
        "center_of_mass_position_drift_scaled": float(
            np.max(np.linalg.norm(com_positions - com_positions[0], axis=1))
            / length_scale
        ),
        "center_of_mass_velocity_drift_scaled": float(
            np.max(np.linalg.norm(com_velocities - com_velocities[0], axis=1))
            / velocity_scale
        ),
        "minimum_pair_separation_scaled": float(np.min(separations) / length_scale),
    }
    if analytic is not None:
        analytic_states = np.stack([analytic(float(time)).values for time in times])
        analytic_positions = analytic_states[:, :9].reshape(-1, 3, 3)
        analytic_velocities = analytic_states[:, 9:].reshape(-1, 3, 3)
        metrics["lagrange_analytic_position_error_scaled"] = float(
            np.max(np.linalg.norm(dop_positions - analytic_positions, axis=2))
            / length_scale
        )
        metrics["lagrange_analytic_velocity_error_scaled"] = float(
            np.max(np.linalg.norm(dop_velocities - analytic_velocities, axis=2))
            / velocity_scale
        )
    return {
        "case_id": str(case["case_id"]),
        "case_type": str(case["case_type"]),
        "success": True,
        "period": period,
        "metrics": metrics,
    }


def structural_metrics(seed: int, count: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    translation_boost_error = 0.0
    rotation_error = 0.0
    permutation_error = 0.0
    force_balance_error = 0.0
    barycenter_residual = 0.0
    for _ in range(count):
        while True:
            positions = rng.normal(size=(3, 3))
            pairwise = [
                np.linalg.norm(positions[i] - positions[j])
                for i, j in ((0, 1), (0, 2), (1, 2))
            ]
            if min(pairwise) > 0.35:
                break
        velocities = rng.normal(size=(3, 3))
        parameters = SystemParameters(
            rng.uniform(0.4, 2.0, size=3), rng.uniform(0.3, 1.7)
        )
        state = InertialState.from_components(positions, velocities)
        rhs = newtonian_rhs(0.0, state.values, parameters)
        rhs_positions = rhs[:9].reshape(3, 3)
        rhs_velocities = rhs[9:].reshape(3, 3)
        length_scale, velocity_scale = _scales(state, parameters)
        acceleration_scale = (
            parameters.gravitational_constant
            * parameters.total_mass
            / length_scale**2
        )

        translation = rng.normal(size=3)
        boost = rng.normal(size=3)
        moved = InertialState.from_components(
            positions + translation, velocities + boost
        )
        moved_rhs = newtonian_rhs(0.0, moved.values, parameters)
        expected_moved = InertialState.from_components(
            rhs_positions + boost, rhs_velocities
        ).values
        translation_boost_error = max(
            translation_boost_error,
            float(np.max(np.abs(moved_rhs - expected_moved)))
            / max(1.0, velocity_scale, acceleration_scale),
        )

        matrix = rng.normal(size=(3, 3))
        rotation, _ = np.linalg.qr(matrix)
        if np.linalg.det(rotation) < 0.0:
            rotation[:, 0] *= -1.0
        rotated = _rotate_state(state, rotation)
        rotated_rhs = newtonian_rhs(0.0, rotated.values, parameters)
        expected_rotated = InertialState.from_components(
            rhs_positions @ rotation.T, rhs_velocities @ rotation.T
        ).values
        rotation_error = max(
            rotation_error,
            float(np.max(np.abs(rotated_rhs - expected_rotated)))
            / max(1.0, velocity_scale, acceleration_scale),
        )

        permutation = rng.permutation(3)
        permuted_parameters = SystemParameters(
            parameters.masses[permutation], parameters.gravitational_constant
        )
        permuted = InertialState.from_components(
            positions[permutation], velocities[permutation]
        )
        permuted_rhs = newtonian_rhs(0.0, permuted.values, permuted_parameters)
        expected_permuted = InertialState.from_components(
            rhs_positions[permutation], rhs_velocities[permutation]
        ).values
        permutation_error = max(
            permutation_error,
            float(np.max(np.abs(permuted_rhs - expected_permuted)))
            / max(1.0, velocity_scale, acceleration_scale),
        )

        internal_force = np.sum(
            parameters.masses[:, None] * rhs_velocities, axis=0
        )
        force_balance_error = max(
            force_balance_error,
            float(np.linalg.norm(internal_force))
            / (parameters.total_mass * acceleration_scale),
        )
        normalized = normalize_center_of_mass(state, parameters)
        barycenter_residual = max(
            barycenter_residual,
            float(np.linalg.norm(center_of_mass_position(normalized, parameters)))
            / length_scale,
            float(np.linalg.norm(center_of_mass_velocity(normalized, parameters)))
            / velocity_scale,
        )
    return {
        "translation_boost_error_max": translation_boost_error,
        "rotation_error_max": rotation_error,
        "permutation_error_max": permutation_error,
        "internal_force_balance_error_max": force_balance_error,
        "barycenter_residual_max": barycenter_residual,
    }


def main() -> None:
    args = parse_args()
    output = Path(args.output).resolve()
    lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires a qualification lock")
        if output.exists():
            raise RuntimeError("refusing to execute the N3BP holdout more than once")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix="WP1Q-N3BP-v1")

    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    if lock is not None:
        if lock["spec_sha256"] != sha256_file(args.spec):
            raise RuntimeError("holdout specification does not match the lock")
        if lock["corpus_sha256"] != sha256_file(args.corpus):
            raise RuntimeError("holdout corpus does not match the lock")
    cases = [case for case in corpus["cases"] if case["split"] == args.split]
    if not cases:
        raise RuntimeError(f"no {args.split} cases in the qualification corpus")

    results: list[dict[str, Any]] = []
    for case in cases:
        try:
            results.append(evaluate_case(case, spec))
        except Exception as error:
            results.append(
                {
                    "case_id": str(case["case_id"]),
                    "case_type": str(case["case_type"]),
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
        "runtime": runtime_fingerprint(),
        "rebound_distribution_version": importlib.metadata.version("rebound"),
        "structural_metrics": structural_metrics(
            int(spec["execution"]["structural_seed_by_split"][args.split]),
            int(spec["execution"]["structural_random_cases_per_split"]),
        ),
        "cases": results,
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(output, payload)
    print(
        f"WP1Q-N3BP-v1 {args.split}: "
        f"{sum(item['success'] for item in results)}/{len(results)} cases"
    )


if __name__ == "__main__":
    main()
