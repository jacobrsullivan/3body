#!/usr/bin/env python
"""Execute one WP2-UP-v1 qualification split."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json, load_json, runtime_fingerprint, sha256_file, utc_now, verify_lock,
)
from src.python.ks import KSPhaseState, project_cotangent  # noqa: E402
from src.python.n3bp_qualification import InertialState, SystemParameters  # noqa: E402
from src.python.threebody_flow import canonical_jacobi_flow  # noqa: E402
from src.python.threebody_reduction import JacobiPhaseState  # noqa: E402
from src.python.upstairs_ks import (  # noqa: E402
    UpstairsKSState, lift_jacobi_state, momentum_map_derivative,
    project_derivative, project_state, regularized_hamiltonian, s1_action,
    upstairs_vector_field,
)


SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"
SPATIAL_LOCK = SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_lock.json"
SPATIAL_RECORD = SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_record.json"
KS_ROOT = VALIDATION_ROOT / "wp2-ks-validation/reports"
KS_LOCK = KS_ROOT / "wp2_ks_qualification_lock.json"
KS_RECORD = KS_ROOT / "wp2_ks_qualification_record.json"
FLOW_ROOT = VALIDATION_ROOT / "wp2-threebody-flow-validation/reports"
FLOW_LOCK = FLOW_ROOT / "wp2_threebody_flow_qualification_lock.json"
FLOW_RECORD = FLOW_ROOT / "wp2_threebody_flow_qualification_record.json"
REFERENCE = CAMPAIGN_ROOT / "reference/upstairs_reference.py"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--spatial-results", required=True)
    parser.add_argument("--split", choices=("development", "calibration", "holdout"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    return parser.parse_args()


def _reference_module():
    spec = importlib.util.spec_from_file_location("wp2_up_reference", REFERENCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load independent upstairs reference")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verify_one(expected: dict[str, str], lock_path: Path, record_path: Path, prefix: str) -> dict[str, str]:
    lock = verify_lock(lock_path, REPO_ROOT, expected_prefix=prefix)
    record = load_json(record_path)
    valid = bool(
        record.get("status") == "PASS"
        and record.get("qualification_id") == expected["qualification_id"] == lock["qualification_id"]
        and record.get("lock_sha256") == expected["lock_sha256"] == lock["lock_sha256"]
        and sha256_file(record_path) == expected["record_sha256"]
    )
    if not valid:
        raise RuntimeError(f"invalid prerequisite: {prefix}")
    return {
        "status": "PASS", "qualification_id": record["qualification_id"],
        "lock_sha256": lock["lock_sha256"], "record_sha256": sha256_file(record_path),
    }


def _verify_prerequisites(spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        "wp1_spatial_n3bp": _verify_one(spec["prerequisites"]["wp1_spatial_n3bp"], SPATIAL_LOCK, SPATIAL_RECORD, "WP1Q-N3BP-SPATIAL-v2"),
        "wp2_kepler_ks": _verify_one(spec["prerequisites"]["wp2_kepler_ks"], KS_LOCK, KS_RECORD, "WP2KSQ-v1"),
        "wp2_threebody_flow": _verify_one(spec["prerequisites"]["wp2_threebody_flow"], FLOW_LOCK, FLOW_RECORD, "WP2-3BFLOWQ-v1"),
    }


def _scaled(first: np.ndarray | float, second: np.ndarray | float) -> float:
    left, right = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    return float(np.max(np.abs(left - right)) / max(1.0, float(np.max(np.abs(right)))))


def _rotate_derivative(vector: np.ndarray, angle: float) -> np.ndarray:
    state = UpstairsKSState.from_vector(vector)
    return s1_action(state, angle).as_vector()


def _project_without_level(state: UpstairsKSState) -> np.ndarray:
    physical = project_cotangent(KSPhaseState(state.q, state.Q), require_zero_level=False)
    return np.concatenate((physical.x, state.lambda_vector, physical.p, state.p_lambda))


def _canonical_gradient_error(state: UpstairsKSState, parameters: SystemParameters, energy: float, step: float) -> float:
    vector = state.as_vector()
    gradient = np.empty(14)
    for index in range(14):
        offset = np.zeros(14)
        offset[index] = step
        plus = regularized_hamiltonian(UpstairsKSState.from_vector(vector + offset), parameters, energy)
        minus = regularized_hamiltonian(UpstairsKSState.from_vector(vector - offset), parameters, energy)
        gradient[index] = (plus - minus) / (2.0 * step)
    expected = np.concatenate((gradient[7:], -gradient[:7]))
    observed = upstairs_vector_field(state, parameters, energy).derivative
    return _scaled(observed, expected)


def _angular_momentum_lie(state: np.ndarray, derivative: np.ndarray) -> float:
    rho, lam, p_rho, p_lam = state.reshape(4, 3)
    rho_dot, lam_dot, p_rho_dot, p_lam_dot = derivative.reshape(4, 3)
    lie = (
        np.cross(rho_dot, p_rho) + np.cross(rho, p_rho_dot)
        + np.cross(lam_dot, p_lam) + np.cross(lam, p_lam_dot)
    )
    scale = max(1.0, float(np.linalg.norm(rho) * np.linalg.norm(p_rho)), float(np.linalg.norm(lam) * np.linalg.norm(p_lam)))
    return float(np.max(np.abs(lie)) / scale)


def _short_flow_metrics(shell, parameters: SystemParameters, execution: dict[str, Any]) -> tuple[float, float, float]:
    s_horizon = float(execution["integration_s_horizon"])
    rtol, atol = float(execution["integration_rtol"]), float(execution["integration_atol"])
    max_step = float(execution["integration_max_step"])
    initial = np.concatenate((shell.state.as_vector(), [0.0]))

    def upstairs_rhs(_s: float, value: np.ndarray) -> np.ndarray:
        flow = upstairs_vector_field(UpstairsKSState.from_vector(value[:14]), parameters, shell.energy)
        return np.concatenate((flow.derivative, [flow.physical_time_rate]))

    upstairs = solve_ivp(upstairs_rhs, (0.0, s_horizon), initial, method="DOP853", rtol=rtol, atol=atol, max_step=max_step)
    if not upstairs.success:
        raise RuntimeError(upstairs.message)
    final_upstairs = UpstairsKSState.from_vector(upstairs.y[:14, -1])
    physical_time = float(upstairs.y[14, -1])
    physical_initial = project_state(shell.state)

    def physical_rhs(_time: float, value: np.ndarray) -> np.ndarray:
        return canonical_jacobi_flow(value, parameters).derivative

    physical = solve_ivp(physical_rhs, (0.0, physical_time), physical_initial, method="DOP853", rtol=rtol, atol=atol, max_step=max(physical_time / 20.0, 1e-10))
    if not physical.success:
        raise RuntimeError(physical.message)
    projection_error = _scaled(_project_without_level(final_upstairs), physical.y[:, -1])
    hamiltonian_drift = abs(regularized_hamiltonian(final_upstairs, parameters, shell.energy)) / max(1.0, abs(shell.energy))
    xi_drift = abs(final_upstairs.xi - shell.state.xi)
    return projection_error, hamiltonian_drift, xi_drift


def _evaluate_checkpoint(state: InertialState, parameters: SystemParameters, angle: float, reference: Any, execution: dict[str, Any], *, integrate: bool) -> dict[str, float]:
    jacobi = JacobiPhaseState.from_inertial(state, parameters).quotient.as_canonical_vector()
    shell = lift_jacobi_state(jacobi, parameters, angle=angle)
    flow = upstairs_vector_field(shell.state, parameters, shell.energy)
    ref_h, ref_vector = reference.evaluate(shell.state.as_vector(), np.asarray(parameters.masses), float(parameters.gravitational_constant), shell.energy)
    physical_flow = canonical_jacobi_flow(jacobi, parameters)
    projected = project_derivative(flow)
    transformed = s1_action(shell.state, 0.731)
    transformed_flow = upstairs_vector_field(transformed, parameters, shell.energy)
    expected_covariance = _rotate_derivative(flow.derivative, 0.731)
    physical_lie = physical_flow.derivative
    if integrate:
        short_projection, short_hamiltonian, short_xi = _short_flow_metrics(shell, parameters, execution)
    else:
        short_projection = short_hamiltonian = short_xi = 0.0
    collision = UpstairsKSState(
        np.zeros(4), shell.state.lambda_vector,
        np.array([0.31, -0.47, 0.59, 0.83]), shell.state.p_lambda,
    )
    collision_flow = upstairs_vector_field(collision, parameters, shell.energy)
    return {
        "reference_hamiltonian_scaled": _scaled(flow.hamiltonian, ref_h),
        "reference_vector_field_scaled": _scaled(flow.derivative, ref_vector),
        "shell_hamiltonian_scaled": abs(flow.hamiltonian) / max(1.0, abs(shell.energy)),
        "xi_level_abs": abs(shell.state.xi),
        "roundtrip_scaled": _scaled(project_state(shell.state), jacobi),
        "sundman_projection_scaled": _scaled(projected, shell.state.radius * physical_flow.derivative),
        "canonical_gradient_scaled": _canonical_gradient_error(shell.state, parameters, shell.energy, float(execution["finite_difference_step"])),
        "s1_hamiltonian_scaled": _scaled(regularized_hamiltonian(transformed, parameters, shell.energy), flow.hamiltonian),
        "s1_projection_scaled": _scaled(project_state(transformed), jacobi),
        "s1_vector_covariance_scaled": _scaled(transformed_flow.derivative, expected_covariance),
        "xi_lie_abs": abs(momentum_map_derivative(flow)),
        "angular_momentum_lie_scaled": _angular_momentum_lie(jacobi, physical_lie),
        "short_flow_projection_scaled": short_projection,
        "short_flow_hamiltonian_drift_scaled": short_hamiltonian,
        "short_flow_xi_drift_abs": short_xi,
        "selected_collision_finite": float(np.all(np.isfinite(collision_flow.derivative))),
    }


def main() -> None:
    args = _args()
    spec, corpus = load_json(args.spec), load_json(args.corpus)
    spatial_corpus, spatial_results = load_json(args.spatial_corpus), load_json(args.spatial_results)
    if corpus["spec_sha256"] != sha256_file(args.spec) or corpus["spatial_corpus_sha256"] != sha256_file(args.spatial_corpus):
        raise RuntimeError("WP2-UP corpus input mismatch")
    if spatial_results["split"] != args.split:
        raise RuntimeError("spatial result split mismatch")
    lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires the WP2-UP lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    prerequisites = _verify_prerequisites(spec)
    definitions = {case["case_id"]: case for case in spatial_corpus["cases"]}
    source_results = {case["case_id"]: case for case in spatial_results["cases"]}
    reference = _reference_module()
    cases = []
    for definition in (case for case in corpus["cases"] if case["split"] == args.split):
        source_id = definition["source_case_id"]
        source_definition, source_result = definitions[source_id], source_results[source_id]
        parameters = SystemParameters([float(value) for value in source_definition["masses_decimal"]], gravitational_constant=1.0)
        checkpoint_metrics = []
        for offset, checkpoint in enumerate(definition["checkpoint_indices"]):
            inertial = InertialState(np.asarray(source_result["oracle"]["states_decimal"][checkpoint], dtype=float))
            checkpoint_metrics.append(_evaluate_checkpoint(
                inertial, parameters, float(definition["gauge_angle"]), reference,
                spec["execution"], integrate=(offset == 0),
            ))
        metrics = {name: max(float(item[name]) for item in checkpoint_metrics) for name in checkpoint_metrics[0]}
        success = bool(all(np.isfinite(value) for value in metrics.values()))
        cases.append({"case_id": definition["case_id"], "source_case_id": source_id, "source_family": definition["source_family"], "success": success, "metrics": metrics})
    payload: dict[str, Any] = {
        "schema_version": "1.0", "campaign": spec["campaign"], "split": args.split,
        "generated_utc": utc_now(), "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus), "spatial_corpus_sha256": sha256_file(args.spatial_corpus),
        "spatial_results_sha256": sha256_file(args.spatial_results), "prerequisites": prerequisites,
        "runtime": runtime_fingerprint(), "cases": cases,
        "structural": {"simultaneous_regularization_qualified": 0},
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    print(f"wrote {args.split} evidence for {len(cases)} WP2-UP cases")


if __name__ == "__main__":
    main()
