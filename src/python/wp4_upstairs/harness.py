"""Deterministic control gauntlet for WP4 upstairs readiness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from src.python.ks import KSPhaseState, project_cotangent
from src.python.n3bp_qualification import SystemParameters
from src.python.upstairs_ks import (
    UpstairsKSState,
    lift_jacobi_state,
    regularized_hamiltonian,
    s1_action,
    upstairs_vector_field,
)


FloatArray = NDArray[np.float64]
Integral = Callable[[FloatArray], float]
POSITIVE_CONTROLS = ("K_h", "Xi", "Lx", "Ly", "Lz")


@dataclass(frozen=True)
class ReadinessCase:
    case_id: str
    parameters: SystemParameters
    state: UpstairsKSState
    energy: float


_CASE_DEFINITIONS = (
    ("equal-01", (1.0, 1.0, 1.0), 0.00,
     (1.20, 0.30, -0.20, -0.40, 1.40, 0.50, 0.20, 0.60, -0.30, -0.50, 0.15, 0.40)),
    ("equal-02", (1.0, 1.0, 1.0), 0.37,
     (-0.80, 1.10, 0.40, 1.30, 0.20, -0.60, 0.55, -0.35, 0.25, 0.10, 0.45, -0.30)),
    ("equal-03", (1.0, 1.0, 1.0), -0.81,
     (0.65, -1.05, 0.75, -1.20, -0.45, 0.90, -0.40, 0.30, 0.50, 0.35, -0.25, 0.20)),
    ("mass-421-01", (4.0, 2.0, 1.0), 0.19,
     (1.10, -0.55, 0.35, -0.70, 1.65, -0.40, 0.45, 0.20, -0.50, -0.30, 0.55, 0.15)),
    ("mass-421-02", (4.0, 2.0, 1.0), -0.52,
     (-1.35, 0.40, 0.25, 1.10, 0.85, -0.75, 0.25, -0.45, 0.60, 0.50, -0.20, 0.35)),
    ("mass-235-01", (2.0, 3.0, 5.0), 1.07,
     (0.90, 0.70, -0.45, -1.40, 0.60, 1.05, -0.35, 0.50, 0.20, 0.40, 0.25, -0.55)),
)


def deterministic_cases() -> tuple[ReadinessCase, ...]:
    cases: list[ReadinessCase] = []
    for case_id, masses, angle, jacobi in _CASE_DEFINITIONS:
        parameters = SystemParameters(masses, gravitational_constant=1.0)
        shell = lift_jacobi_state(np.asarray(jacobi, dtype=float), parameters, angle=angle)
        cases.append(ReadinessCase(case_id, parameters, shell.state, shell.energy))
    return tuple(cases)


def canonical_poisson_matrix() -> FloatArray:
    identity = np.eye(7, dtype=float)
    zero = np.zeros((7, 7), dtype=float)
    return np.block([[zero, identity], [-identity, zero]])


def finite_difference_gradient(
    function: Integral,
    state: FloatArray,
    relative_step: float,
) -> FloatArray:
    """Return a deterministic five-point central-difference gradient."""
    vector = np.asarray(state, dtype=float)
    gradient = np.empty_like(vector)
    for index in range(vector.size):
        step = relative_step * max(1.0, abs(float(vector[index])))
        offset = np.zeros_like(vector)
        offset[index] = step
        gradient[index] = (
            function(vector - 2.0 * offset)
            - 8.0 * function(vector - offset)
            + 8.0 * function(vector + offset)
            - function(vector + 2.0 * offset)
        ) / (12.0 * step)
    return gradient


def poisson_bracket(
    first_gradient: FloatArray,
    second_gradient: FloatArray,
) -> float:
    return float(first_gradient @ canonical_poisson_matrix() @ second_gradient)


def _angular_momentum_unchecked(vector: FloatArray) -> FloatArray:
    state = UpstairsKSState.from_vector(vector)
    pair = project_cotangent(
        KSPhaseState(state.q, state.Q), require_zero_level=False
    )
    return np.cross(pair.x, pair.p) + np.cross(
        state.lambda_vector, state.p_lambda
    )


def _integrals(case: ReadinessCase) -> dict[str, Integral]:
    parameters = case.parameters
    energy = case.energy

    def hamiltonian(vector: FloatArray) -> float:
        return regularized_hamiltonian(
            UpstairsKSState.from_vector(vector), parameters, energy
        )

    def xi(vector: FloatArray) -> float:
        return UpstairsKSState.from_vector(vector).xi

    def angular(index: int) -> Integral:
        return lambda vector: float(_angular_momentum_unchecked(vector)[index])

    def coordinate(vector: FloatArray) -> float:
        return float(vector[0])

    def dependent(vector: FloatArray) -> float:
        return 2.0 * hamiltonian(vector) - 3.0 * xi(vector)

    return {
        "K_h": hamiltonian,
        "Xi": xi,
        "Lx": angular(0),
        "Ly": angular(1),
        "Lz": angular(2),
        "q0_nonconserved": coordinate,
        "dependent_2K_minus_3Xi": dependent,
    }


def _rank(gradients: list[FloatArray], relative_tolerance: float) -> int:
    matrix = np.vstack(gradients)
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    if singular_values.size == 0 or singular_values[0] == 0.0:
        return 0
    return int(np.count_nonzero(singular_values > relative_tolerance * singular_values[0]))


def _scaled_lie(gradient: FloatArray, vector_field: FloatArray) -> float:
    denominator = max(1.0, np.linalg.norm(gradient) * np.linalg.norm(vector_field))
    return float(abs(np.dot(gradient, vector_field)) / denominator)


def _scaled_error(observed: FloatArray | float, expected: FloatArray | float) -> float:
    left = np.asarray(observed, dtype=float)
    right = np.asarray(expected, dtype=float)
    return float(np.max(np.abs(left - right)) / max(1.0, np.max(np.abs(right))))


def _gauge_metrics(
    case: ReadinessCase,
    integrals: dict[str, Integral],
    angles: list[float],
) -> dict[str, float]:
    initial = case.state.as_vector()
    residuals = {name: 0.0 for name in (*POSITIVE_CONTROLS, "dependent_2K_minus_3Xi")}
    coordinate_changes: list[float] = []
    for angle in angles:
        transformed = s1_action(case.state, float(angle)).as_vector()
        for name in residuals:
            residuals[name] = max(
                residuals[name],
                _scaled_error(integrals[name](transformed), integrals[name](initial)),
            )
        coordinate_changes.append(
            abs(integrals["q0_nonconserved"](transformed) - integrals["q0_nonconserved"](initial))
        )
    return {
        "residual_scaled": residuals,
        "negative_coordinate_gauge_change": max(coordinate_changes),
    }


def _integration_metrics(
    case: ReadinessCase,
    integrals: dict[str, Integral],
    execution: dict[str, Any],
) -> dict[str, Any]:
    initial = case.state.as_vector()

    def rhs(_time: float, vector: FloatArray) -> FloatArray:
        state = UpstairsKSState.from_vector(vector)
        return upstairs_vector_field(state, case.parameters, case.energy).derivative

    sample_count = int(execution["integration_sample_count"])
    horizon = float(execution["integration_horizon"])
    solution = solve_ivp(
        rhs,
        (0.0, horizon),
        initial,
        method="DOP853",
        t_eval=np.linspace(0.0, horizon, sample_count),
        rtol=float(execution["integration_rtol"]),
        atol=float(execution["integration_atol"]),
        max_step=float(execution["integration_max_step"]),
    )
    if not solution.success or solution.y.shape != (14, sample_count):
        return {"success": False, "message": solution.message}
    drifts: dict[str, float] = {}
    for name in (*POSITIVE_CONTROLS, "dependent_2K_minus_3Xi", "q0_nonconserved"):
        values = np.asarray([integrals[name](row) for row in solution.y.T])
        drifts[name] = float(
            np.max(np.abs(values - values[0])) / max(1.0, abs(float(values[0])))
        )
    return {"success": True, "drifts": drifts, "step_count": int(solution.t.size)}


def evaluate_readiness(spec: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen readiness controls and return raw evidence."""
    execution = spec["execution"]
    finite_difference_step = float(execution["finite_difference_relative_step"])
    gauge_step = float(execution["gauge_generator_step"])
    rank_tolerance = float(execution["rank_relative_tolerance"])
    cases_payload: list[dict[str, Any]] = []

    for case in deterministic_cases():
        vector = case.state.as_vector()
        functions = _integrals(case)
        gradients = {
            name: finite_difference_gradient(function, vector, finite_difference_step)
            for name, function in functions.items()
        }
        flow = upstairs_vector_field(case.state, case.parameters, case.energy)
        lie = {
            name: _scaled_lie(gradient, flow.derivative)
            for name, gradient in gradients.items()
        }

        hamiltonian_vector = canonical_poisson_matrix() @ gradients["K_h"]
        xi_vector = canonical_poisson_matrix() @ gradients["Xi"]
        plus = s1_action(case.state, gauge_step).as_vector()
        minus = s1_action(case.state, -gauge_step).as_vector()
        gauge_generator = (plus - minus) / (2.0 * gauge_step)

        names = list(functions)
        antisymmetry = 0.0
        for first in names:
            for second in names:
                antisymmetry = max(
                    antisymmetry,
                    abs(
                        poisson_bracket(gradients[first], gradients[second])
                        + poisson_bracket(gradients[second], gradients[first])
                    ),
                )

        momentum_commutation = max(
            abs(poisson_bracket(gradients["K_h"], gradients[name]))
            for name in ("Xi", "Lx", "Ly", "Lz")
        )
        momentum_commutation = max(
            momentum_commutation,
            max(
                abs(poisson_bracket(gradients["Xi"], gradients[name]))
                for name in ("Lx", "Ly", "Lz")
            ),
        )
        angular_errors = (
            poisson_bracket(gradients["Lx"], gradients["Ly"]) - functions["Lz"](vector),
            poisson_bracket(gradients["Ly"], gradients["Lz"]) - functions["Lx"](vector),
            poisson_bracket(gradients["Lz"], gradients["Lx"]) - functions["Ly"](vector),
        )

        known_gradients = [gradients[name] for name in POSITIVE_CONTROLS]
        known_rank = _rank(known_gradients, rank_tolerance)
        dependent_rank = _rank(
            [*known_gradients, gradients["dependent_2K_minus_3Xi"]], rank_tolerance
        )
        coordinate_rank = _rank(
            [*known_gradients, gradients["q0_nonconserved"]], rank_tolerance
        )
        gauge = _gauge_metrics(
            case, functions, [float(value) for value in execution["gauge_angles"]]
        )
        integration = _integration_metrics(case, functions, execution)

        cases_payload.append({
            "case_id": case.case_id,
            "masses": [float(value) for value in case.parameters.masses],
            "energy": case.energy,
            "initial_shell_abs": abs(functions["K_h"](vector)),
            "initial_xi_abs": abs(functions["Xi"](vector)),
            "lie_derivative_scaled": lie,
            "canonical": {
                "hamiltonian_vector_field_scaled": _scaled_error(
                    hamiltonian_vector, flow.derivative
                ),
                "poisson_antisymmetry_abs": antisymmetry,
                "xi_generator_scaled": _scaled_error(xi_vector, gauge_generator),
                "momentum_commutation_abs": momentum_commutation,
                "angular_momentum_so3_abs": float(max(abs(value) for value in angular_errors)),
            },
            "rank": {
                "known": known_rank,
                "with_dependent": dependent_rank,
                "dependent_increment": dependent_rank - known_rank,
                "with_nonconserved_coordinate": coordinate_rank,
                "nonconserved_coordinate_increment": coordinate_rank - known_rank,
            },
            "gauge": gauge,
            "integration": integration,
        })

    positive_lie_max = max(
        case["lie_derivative_scaled"][name]
        for case in cases_payload
        for name in POSITIVE_CONTROLS
    )
    negative_lie_min = min(
        case["lie_derivative_scaled"]["q0_nonconserved"] for case in cases_payload
    )
    integration_successes = [case["integration"]["success"] for case in cases_payload]
    positive_drift_max = max(
        case["integration"]["drifts"][name]
        for case in cases_payload
        for name in POSITIVE_CONTROLS
        if case["integration"]["success"]
    )
    coordinate_drift_min = min(
        case["integration"]["drifts"]["q0_nonconserved"]
        for case in cases_payload
        if case["integration"]["success"]
    )
    dependent_lie_max = max(
        case["lie_derivative_scaled"]["dependent_2K_minus_3Xi"]
        for case in cases_payload
    )
    dependent_gauge_max = max(
        case["gauge"]["residual_scaled"]["dependent_2K_minus_3Xi"]
        for case in cases_payload
    )
    dependent_drift_max = max(
        case["integration"]["drifts"]["dependent_2K_minus_3Xi"]
        for case in cases_payload
        if case["integration"]["success"]
    )
    positive_gauge_by_control = {
        name: max(case["gauge"]["residual_scaled"][name] for case in cases_payload)
        for name in POSITIVE_CONTROLS
    }
    positive_lie_by_control = {
        name: max(case["lie_derivative_scaled"][name] for case in cases_payload)
        for name in POSITIVE_CONTROLS
    }
    positive_drift_by_control = {
        name: max(
            case["integration"]["drifts"][name]
            for case in cases_payload
            if case["integration"]["success"]
        )
        for name in POSITIVE_CONTROLS
    }
    thresholds = {definition["metric"]: definition["threshold"] for definition in spec["gates"]}
    positive_decisions = {
        name: (
            positive_lie_by_control[name] <= thresholds["positive_control_lie_scaled_max"]
            and positive_gauge_by_control[name] <= thresholds["positive_gauge_residual_scaled_max"]
            and positive_drift_by_control[name] <= thresholds["positive_trajectory_drift_scaled_max"]
        )
        for name in POSITIVE_CONTROLS
    }
    coordinate_rejected = (
        negative_lie_min >= thresholds["negative_coordinate_lie_scaled_min"]
        and min(case["gauge"]["negative_coordinate_gauge_change"] for case in cases_payload)
        >= thresholds["negative_coordinate_gauge_change_min"]
        and coordinate_drift_min >= thresholds["negative_coordinate_trajectory_drift_scaled_min"]
    )
    dependent_rejected = (
        dependent_lie_max <= thresholds["dependent_control_lie_scaled_max"]
        and dependent_gauge_max <= thresholds["dependent_control_gauge_residual_scaled_max"]
        and dependent_drift_max <= thresholds["dependent_control_trajectory_drift_scaled_max"]
        and max(case["rank"]["dependent_increment"] for case in cases_payload) == 0
    )
    metrics = {
        "deterministic_state_count": len(cases_payload),
        "initial_shell_abs_max": max(case["initial_shell_abs"] for case in cases_payload),
        "initial_xi_abs_max": max(case["initial_xi_abs"] for case in cases_payload),
        "positive_control_lie_scaled_max": positive_lie_max,
        "dependent_control_lie_scaled_max": dependent_lie_max,
        "negative_coordinate_lie_scaled_min": negative_lie_min,
        "hamiltonian_vector_field_scaled_max": max(
            case["canonical"]["hamiltonian_vector_field_scaled"] for case in cases_payload
        ),
        "poisson_antisymmetry_abs_max": max(
            case["canonical"]["poisson_antisymmetry_abs"] for case in cases_payload
        ),
        "xi_generator_scaled_max": max(
            case["canonical"]["xi_generator_scaled"] for case in cases_payload
        ),
        "momentum_commutation_abs_max": max(
            case["canonical"]["momentum_commutation_abs"] for case in cases_payload
        ),
        "angular_momentum_so3_abs_max": max(
            case["canonical"]["angular_momentum_so3_abs"] for case in cases_payload
        ),
        "known_functional_rank_min": min(case["rank"]["known"] for case in cases_payload),
        "dependent_rank_increment_max": max(
            case["rank"]["dependent_increment"] for case in cases_payload
        ),
        "nonconserved_rank_increment_min": min(
            case["rank"]["nonconserved_coordinate_increment"] for case in cases_payload
        ),
        "positive_gauge_residual_scaled_max": max(
            max(case["gauge"]["residual_scaled"][name] for name in POSITIVE_CONTROLS)
            for case in cases_payload
        ),
        "dependent_control_gauge_residual_scaled_max": dependent_gauge_max,
        "negative_coordinate_gauge_change_min": min(
            case["gauge"]["negative_coordinate_gauge_change"] for case in cases_payload
        ),
        "integration_success_rate": sum(integration_successes) / len(integration_successes),
        "positive_trajectory_drift_scaled_max": positive_drift_max,
        "dependent_control_trajectory_drift_scaled_max": dependent_drift_max,
        "negative_coordinate_trajectory_drift_scaled_min": coordinate_drift_min,
        "positive_controls_accepted": sum(positive_decisions.values()),
        "negative_controls_rejected": int(coordinate_rejected) + int(dependent_rejected),
        "candidate_validation_triggered": 0,
        "morales_ramis_triggered": 0,
        "publication_reserve_open_attempts": 0,
    }
    return {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "case_count": len(cases_payload),
        "controls": {
            "positive": {
                name: {
                    "decision": "ACCEPT_KNOWN_CONTROL" if positive_decisions[name] else "REJECT",
                    "lie_derivative_scaled_max": positive_lie_by_control[name],
                    "gauge_residual_scaled_max": positive_gauge_by_control[name],
                    "trajectory_drift_scaled_max": positive_drift_by_control[name],
                }
                for name in POSITIVE_CONTROLS
            },
            "negative": {
                "q0_nonconserved": {
                    "decision": "REJECT_NONCONSERVED_AND_GAUGE_VARIANT" if coordinate_rejected else "CONTROL_FAILURE"
                },
                "dependent_2K_minus_3Xi": {
                    "decision": "REJECT_FUNCTIONALLY_DEPENDENT" if dependent_rejected else "CONTROL_FAILURE",
                    "conservation_precheck_passed": bool(
                        dependent_lie_max <= thresholds["dependent_control_lie_scaled_max"]
                        and dependent_gauge_max <= thresholds["dependent_control_gauge_residual_scaled_max"]
                        and dependent_drift_max <= thresholds["dependent_control_trajectory_drift_scaled_max"]
                    ),
                },
            },
        },
        "metrics": metrics,
        "cases": cases_payload,
    }
