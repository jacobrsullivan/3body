#!/usr/bin/env python
"""Execute one frozen WP2-MULTIQ-v1 qualification split."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import sympy as sp


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = Path(__file__).resolve().parents[1]
for path in (ROOT, VALIDATION):
    sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from src.python.ks import KSPhaseState, fiber_generator, s1_action  # noqa: E402
from src.python.n3bp_qualification import (  # noqa: E402
    IAS15Config,
    InertialState,
    SystemParameters,
    figure_eight_choreography,
    lagrange_equilateral,
    newtonian_rhs,
    normalize_center_of_mass,
    propagate_rebound_ias15,
    total_energy,
)
from src.python.wp2_multi_v1 import (  # noqa: E402
    CHART_LOCAL_ORDER,
    DEFAULT_COLLISION_FLOOR,
    PHYSICAL_CHANNELS,
    MultiKSState,
    TripleCollisionOutOfScope,
    collision_shell_state,
    global_time_rate,
    lift_inertial_state,
    pair_distances,
    project_derivative,
    project_state,
    regularized_hamiltonian,
    regularized_channels,
    selected_physical_channel,
    switch_to_regularizing_chart,
    torus_action,
    transition_chart,
    vector_field,
)


N3BP = VALIDATION / "wp1-n3bp-validation"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--n3bp-corpus", required=True)
    parser.add_argument("--split", choices=("development", "calibration", "holdout"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    return parser.parse_args()


def _reference():
    path = CAMPAIGN / "reference/autodiff_reference.py"
    definition = importlib.util.spec_from_file_location("wp2_multi_autodiff", path)
    if definition is None or definition.loader is None:
        raise RuntimeError("cannot load the WP2-MULTI autodiff reference")
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    return module


def _scaled(first, second) -> float:
    left = np.asarray(first, dtype=np.float64)
    right = np.asarray(second, dtype=np.float64)
    return float(np.max(np.abs(left - right)) / max(1.0, float(np.max(np.abs(right)))))


def _verify_specification_lock(spec_path: str) -> dict[str, Any]:
    lock_path = CAMPAIGN / "reports/wp2_multi_v1_specification_lock.json"
    lock = load_json(lock_path)
    from qualification_tools import canonical_json, sha256_bytes

    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256")
    if sha256_bytes(canonical_json(unsigned)) != recorded:
        raise RuntimeError("WP2-MULTI specification lock integrity failure")
    if lock["spec_sha256"] != sha256_file(spec_path):
        raise RuntimeError("WP2-MULTI specification changed after claim lock")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"WP2-MULTI prerequisite changed: {relative}")
    return lock


def _verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "wp1_n3bp": (
            N3BP / "reports/wp1_n3bp_qualification_lock.json",
            N3BP / "reports/wp1_n3bp_qualification_record.json",
            "WP1Q-N3BP-v1",
        ),
        "wp2_kepler_ks": (
            VALIDATION / "wp2-ks-validation/reports/wp2_ks_qualification_lock.json",
            VALIDATION / "wp2-ks-validation/reports/wp2_ks_qualification_record.json",
            "WP2KSQ-v1",
        ),
        "wp2_threebody_reduction": (
            VALIDATION / "wp2-threebody-validation/reports/wp2_threebody_qualification_lock.json",
            VALIDATION / "wp2-threebody-validation/reports/wp2_threebody_qualification_record.json",
            "WP2-3BRQ-v1",
        ),
        "wp2_threebody_flow": (
            VALIDATION / "wp2-threebody-flow-validation/reports/wp2_threebody_flow_qualification_lock.json",
            VALIDATION / "wp2-threebody-flow-validation/reports/wp2_threebody_flow_qualification_record.json",
            "WP2-3BFLOWQ-v1",
        ),
        "wp2_one_channel": (
            VALIDATION / "wp2-up-validation-v2/reports/wp2_up_v2_qualification_lock.json",
            VALIDATION / "wp2-up-validation-v2/reports/wp2_up_v2_qualification_record.json",
            "WP2-UPQ-v2",
        ),
    }
    evidence = {}
    for key, (lock_path, record_path, prefix) in paths.items():
        expected = spec["prerequisites"][key]
        lock = verify_lock(lock_path, ROOT, expected_prefix=prefix)
        record = load_json(record_path)
        valid = bool(
            record.get("status") == "PASS"
            and record.get("qualification_id") == expected["qualification_id"] == lock["qualification_id"]
            and lock["lock_sha256"] == expected["lock_sha256"]
            and sha256_file(record_path) == expected["record_file_sha256"]
        )
        if not valid:
            raise RuntimeError(f"invalid WP2-MULTI prerequisite: {key}")
        evidence[key] = {"status": "PASS", "qualification_id": record["qualification_id"]}
    return evidence


def _rotation_xyz(angles) -> np.ndarray:
    ax, ay, az = (float(value) for value in angles)
    cx, sx, cy, sy, cz, sz = np.cos(ax), np.sin(ax), np.cos(ay), np.sin(ay), np.cos(az), np.sin(az)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return rz @ ry @ rx


def _source_state(case: dict[str, Any]) -> tuple[InertialState, SystemParameters]:
    kind = case["case_type"]
    if kind == "lagrange":
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
        return normalize_center_of_mass(state, orbit.parameters), orbit.parameters
    if kind == "figure_eight":
        orbit = figure_eight_choreography()
        return normalize_center_of_mass(orbit.initial_state, orbit.parameters), orbit.parameters
    if kind == "sjtu_periodic":
        masses = np.array([float(value) for value in case["masses"]])
        parameters = SystemParameters(masses, gravitational_constant=1.0)
        positions = np.array([[float(case["x1"]), 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        v1, v2 = float(case["v1"]), float(case["v2"])
        velocities = np.array([[0.0, v1, 0.0], [0.0, v2, 0.0], [0.0, -(masses[0] * v1 + masses[1] * v2) / masses[2], 0.0]])
        return normalize_center_of_mass(InertialState.from_components(positions, velocities), parameters), parameters
    raise ValueError(f"unsupported source case type: {kind}")


def _near_state(parameters: SystemParameters, chart: str, selected_edge: int, distance: float) -> InertialState:
    a, b, c = CHART_LOCAL_ORDER[chart]
    local_masses = parameters.masses[[a, b, c]]
    direction = np.array([0.73, -0.41, 0.547])
    direction /= np.linalg.norm(direction)
    other = np.array([1.2, -0.4, 0.7])
    local_positions = np.zeros((3, 3))
    local_positions[0 if selected_edge == 1 else 1] = distance * direction
    local_positions[1 if selected_edge == 1 else 0] = other
    W1 = np.array([0.17, -0.08, 0.11])
    W2 = np.array([-0.09, 0.13, -0.04])
    local_momenta = np.stack((W1, W2, -W1 - W2))
    local_velocities = local_momenta / local_masses[:, None]
    positions = np.empty((3, 3))
    velocities = np.empty((3, 3))
    for local_index, original_index in enumerate((a, b, c)):
        positions[original_index] = local_positions[local_index]
        velocities[original_index] = local_velocities[local_index]
    return normalize_center_of_mass(InertialState.from_components(positions, velocities), parameters)


def _reference_metrics(state, parameters, reference):
    vector = state.as_vector().copy()
    vector[17] += 0.173
    probe = MultiKSState.from_vector(state.chart, vector)
    order = CHART_LOCAL_ORDER[state.chart]
    value, derivative = reference.evaluate(
        vector,
        parameters.masses[list(order)],
        parameters.gravitational_constant,
    )
    production = vector_field(probe, parameters)
    return _scaled(production.hamiltonian, value), _scaled(production.derivative, derivative)


def _rotate_tangent(flow, angles):
    first = s1_action(KSPhaseState(flow.derivative[:4], flow.derivative[9:13]), float(angles[0]))
    second = s1_action(KSPhaseState(flow.derivative[4:8], flow.derivative[13:17]), float(angles[1]))
    return np.concatenate((first.q, second.q, [flow.derivative[8]], first.Q, second.Q, [flow.derivative[17]]))


def _common_metrics(state, parameters, reference, spec):
    flow = vector_field(state, parameters)
    independent_h, independent_v = _reference_metrics(state, parameters, reference)
    physical = project_state(state, parameters)
    projected = project_derivative(flow, parameters)
    expected = flow.time_rate * newtonian_rhs(0.0, physical.values, parameters)
    angles = (0.731, -1.127)
    moved = torus_action(state, angles)
    moved_flow = vector_field(moved, parameters)
    charts = tuple(CHART_LOCAL_ORDER)
    first_target = charts[(charts.index(state.chart) + 1) % 3]
    second_target = charts[(charts.index(state.chart) + 2) % 3]
    transitioned = transition_chart(state, parameters, first_target, angles=(0.19, -0.41))
    cycled = transition_chart(transitioned, parameters, second_target, angles=(-0.67, 0.83))
    returned = transition_chart(cycled, parameters, state.chart, angles=(1.03, -1.29))
    return {
        "independent_hamiltonian_scaled": independent_h,
        "independent_vector_field_scaled": independent_v,
        "shell_abs": abs(flow.hamiltonian) / max(1.0, abs(state.p_t)),
        "xi_abs": float(np.max(np.abs(state.momentum_maps))),
        "xi_lie_abs": float(np.max(np.abs(flow.momentum_map_derivatives))),
        "gauge_hamiltonian_scaled": _scaled(moved_flow.hamiltonian, flow.hamiltonian),
        "gauge_vector_covariance_scaled": _scaled(moved_flow.derivative, _rotate_tangent(flow, angles)),
        "chart_roundtrip_scaled": _scaled(project_state(transitioned, parameters).values, physical.values),
        "chart_hamiltonian_scaled": _scaled(regularized_hamiltonian(transitioned, parameters), flow.hamiltonian),
        "chart_time_rate_scaled": _scaled(global_time_rate(transitioned), flow.time_rate),
        "chart_cocycle_scaled": _scaled(project_state(returned, parameters).values, physical.values),
        "projected_sundman_field_scaled": _scaled(projected, expected),
    }


def _switch_trajectory_metric(state, parameters, horizon, execution):
    physical = project_state(state, parameters)
    distances = pair_distances(state)
    smallest = min(PHYSICAL_CHANNELS, key=lambda channel: (distances[channel], channel))
    bad_chart = next(
        chart for chart in CHART_LOCAL_ORDER if smallest not in regularized_channels(chart)
    )
    bad = lift_inertial_state(
        physical,
        parameters,
        bad_chart,
        angles=(0.23, -0.47),
        physical_time=state.physical_time,
        p_t=state.p_t,
    )
    switched = switch_to_regularizing_chart(
        bad, parameters, angles=(-0.31, 0.59)
    )
    if switched.chart == bad_chart or smallest not in regularized_channels(switched.chart):
        raise RuntimeError("smallest-pair switch policy selected an invalid chart")

    _, baseline = _integrate_chart(switched, parameters, horizon, execution)
    _, midpoint = _integrate_chart(bad, parameters, 0.5 * horizon, execution)
    transitioned = transition_chart(
        midpoint, parameters, switched.chart, angles=(0.71, -0.37)
    )
    _, mixed = _integrate_chart(transitioned, parameters, 0.5 * horizon, execution)
    return _scaled(
        project_state(mixed, parameters).values,
        project_state(baseline, parameters).values,
    )


def _integrate_chart(state, parameters, horizon, execution, rhs_kind="production"):
    reference = _reference() if rhs_kind == "reference" else None
    order = CHART_LOCAL_ORDER[state.chart]

    def rhs(_, value):
        if reference is None:
            return vector_field(MultiKSState.from_vector(state.chart, value), parameters).derivative
        return reference.evaluate(value, parameters.masses[list(order)], parameters.gravitational_constant)[1]

    result = solve_ivp(
        rhs,
        (0.0, horizon),
        state.as_vector(),
        method="DOP853",
        rtol=float(execution["integration_rtol"]),
        atol=float(execution["integration_atol"]),
        max_step=float(execution["integration_max_step"]),
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result, MultiKSState.from_vector(state.chart, result.y[:, -1])


def _trajectory_metric(state, parameters, horizon, execution):
    _, final = _integrate_chart(state, parameters, horizon, execution)
    physical_initial = project_state(state, parameters)
    elapsed = final.physical_time - state.physical_time
    if elapsed <= 0.0:
        raise RuntimeError("regularized trajectory did not advance physical time")
    reference = propagate_rebound_ias15(
        physical_initial,
        np.array([0.0, elapsed]),
        parameters,
        config=IAS15Config(epsilon=1e-12, adaptive_mode="global"),
    )
    return _scaled(project_state(final, parameters).values, reference.states[-1])


def _collision_probe(exact, parameters, selected_edge, physical_distance):
    vector = exact.as_vector().copy()
    q_slice = slice(0, 4) if selected_edge == 1 else slice(4, 8)
    P_slice = slice(9, 13) if selected_edge == 1 else slice(13, 17)
    direction = exact.as_vector()[P_slice]
    direction /= np.linalg.norm(direction)
    vector[q_slice] = np.sqrt(physical_distance) * direction
    base = vector[P_slice].copy()

    def shell(scale):
        probe = vector.copy()
        probe[P_slice] = scale * base
        return regularized_hamiltonian(MultiKSState.from_vector(exact.chart, probe), parameters)

    lower, upper = 0.1, 2.0
    while shell(lower) * shell(upper) > 0.0:
        upper *= 2.0
        if upper > 64.0:
            raise RuntimeError("failed to bracket collision-shell momentum")
    vector[P_slice] = brentq(shell, lower, upper, xtol=1e-14) * base
    return MultiKSState.from_vector(exact.chart, vector)


def _collision_metrics(case, parameters, reference, spec):
    selected = int(case["selected_edge"])
    exact = collision_shell_state(
        parameters,
        case["chart"],
        selected,
        other_q=np.array([0.8, 0.0, 0.25, -0.1]),
        collision_direction=np.array([1.0, -0.3, 0.2, 0.4]),
        energy=-1.7,
    )
    if selected_physical_channel(case["chart"], selected) != case["physical_channel"]:
        raise RuntimeError("exact-passage corpus channel does not match chart edge")
    production = vector_field(exact, parameters)
    order = CHART_LOCAL_ORDER[exact.chart]
    ref_h, ref_v = reference.evaluate(exact.as_vector(), parameters.masses[list(order)], parameters.gravitational_constant)
    distances = np.asarray(
        spec["corpus"]["near_collision_selected_distances"], dtype=np.float64
    )
    probes = [
        _collision_probe(exact, parameters, selected, float(distance))
        for distance in distances
    ]
    probe_fields = np.stack(
        [vector_field(probe, parameters).derivative for probe in probes]
    )
    raw_errors = [
        _scaled(field, production.derivative) for field in probe_fields
    ]
    q_norms = np.sqrt(distances)
    vandermonde = np.vander(q_norms, N=3, increasing=True)
    extrapolated = np.linalg.solve(vandermonde, probe_fields)[0]
    collision_limit = _scaled(extrapolated, production.derivative)
    convergence = float(
        all(
            later <= earlier
            for earlier, later in zip(raw_errors, raw_errors[1:])
        )
    )

    gauge_angles = (0.731, -1.127)
    moved = torus_action(exact, gauge_angles)
    moved_flow = vector_field(moved, parameters)
    horizon = float(spec["execution"]["passage_s_horizon"])
    maximum_h = 0.0
    maximum_xi = 0.0
    maximum_reference = 0.0
    passage = True
    crossing = True
    selected_q = slice(0, 4) if selected == 1 else slice(4, 8)
    collision_tangent = production.derivative[selected_q]
    for sign in (-1.0, 1.0):
        result, final = _integrate_chart(exact, parameters, sign * horizon, spec["execution"])
        _, final_reference = _integrate_chart(exact, parameters, sign * horizon, spec["execution"], rhs_kind="reference")
        passage = passage and bool(result.success and np.all(np.isfinite(result.y)))
        maximum_h = max(maximum_h, abs(regularized_hamiltonian(final, parameters) - production.hamiltonian) / max(1.0, abs(exact.p_t)))
        maximum_xi = max(maximum_xi, float(np.max(np.abs(final.momentum_maps - exact.momentum_maps))))
        maximum_reference = max(maximum_reference, _scaled(final.as_vector(), final_reference.as_vector()))
        crossing = crossing and bool(
            sign * float(np.dot(final.as_vector()[selected_q], collision_tangent)) > 0.0
        )
    triple_rejected = 0.0
    small = np.sqrt(0.5 * float(spec["corpus"]["triple_collision_floor"]))
    try:
        vector_field(
            MultiKSState(
                case["chart"],
                np.array([small, 0.0, 0.0, 0.0]),
                np.array([0.0, small, 0.0, 0.0]),
                0.0,
                np.ones(4),
                np.ones(4),
                1.0,
            ),
            parameters,
        )
    except TripleCollisionOutOfScope:
        triple_rejected = 1.0
    return {
        "independent_hamiltonian_scaled": _scaled(production.hamiltonian, ref_h),
        "independent_vector_field_scaled": _scaled(production.derivative, ref_v),
        "shell_abs": abs(production.hamiltonian),
        "xi_abs": float(np.max(np.abs(exact.momentum_maps))),
        "xi_lie_abs": float(np.max(np.abs(production.momentum_map_derivatives))),
        "gauge_hamiltonian_scaled": _scaled(moved_flow.hamiltonian, production.hamiltonian),
        "gauge_vector_covariance_scaled": _scaled(
            moved_flow.derivative, _rotate_tangent(production, gauge_angles)
        ),
        "collision_limit_scaled": collision_limit,
        "collision_probe_raw_scaled_max": max(raw_errors),
        "collision_probe_convergence": convergence,
        "collision_spinor_crossing": float(crossing),
        "collision_passage_finite": float(passage and crossing and convergence == 1.0),
        "collision_passage_hamiltonian_drift_scaled": maximum_h,
        "collision_passage_xi_drift_abs": maximum_xi,
        "collision_passage_reference_scaled": maximum_reference,
        "triple_collision_rejected": triple_rejected,
    }


def _symbolic_identity_rate() -> float:
    q = sp.symbols("q0:4", real=True)
    x = sp.Matrix([2 * (q[0] * q[2] + q[1] * q[3]), 2 * (q[0] * q[3] - q[1] * q[2]), q[0] ** 2 + q[1] ** 2 - q[2] ** 2 - q[3] ** 2])
    radius = sum(value * value for value in q)
    jacobian = x.jacobian(q)
    norm_identity = sp.expand(x.dot(x) - radius**2) == 0
    jacobian_identity = all(
        sp.expand(value) == 0
        for value in (jacobian * jacobian.T - 4 * radius * sp.eye(3))
    )
    mu, kappa, r2, r3, momentum_squared = sp.symbols(
        "mu kappa r2 r3 momentum_squared", nonzero=True
    )
    collision_shell = r3 * r2 * (momentum_squared / (8 * mu) - kappa)
    collision_identity = (
        sp.simplify(collision_shell.subs(momentum_squared, 8 * mu * kappa)) == 0
    )
    return sum((norm_identity, jacobian_identity, collision_identity)) / 3.0


def _physical_chart_transition_matrix(source_chart: str, target_chart: str) -> np.ndarray:
    source_order = CHART_LOCAL_ORDER[source_chart]
    target_order = CHART_LOCAL_ORDER[target_chart]

    def transform(vector):
        X1, X2 = vector[:3], vector[3:6]
        W1, W2 = vector[6:9], vector[9:12]
        positions = np.zeros((3, 3))
        momenta = np.zeros((3, 3))
        a, b, c = source_order
        positions[a], positions[b], positions[c] = X1, X2, 0.0
        momenta[a], momenta[b], momenta[c] = W1, W2, -W1 - W2
        ta, tb, tc = target_order
        return np.concatenate(
            (
                positions[ta] - positions[tc],
                positions[tb] - positions[tc],
                momenta[ta],
                momenta[tb],
            )
        )

    identity = np.eye(12)
    return np.column_stack([transform(identity[:, index]) for index in range(12)])


def _constraint_gradient(state: MultiKSState, edge: int) -> np.ndarray:
    gradient = np.zeros(18)
    if edge == 1:
        gradient[:4] = -fiber_generator(state.P1)
        gradient[9:13] = fiber_generator(state.q1)
    else:
        gradient[4:8] = -fiber_generator(state.P2)
        gradient[13:17] = fiber_generator(state.q2)
    return gradient


def _gauge_tangent(state: MultiKSState, edge: int) -> np.ndarray:
    tangent = np.zeros(18)
    if edge == 1:
        tangent[:4] = fiber_generator(state.q1)
        tangent[9:13] = fiber_generator(state.P1)
    else:
        tangent[4:8] = fiber_generator(state.q2)
        tangent[13:17] = fiber_generator(state.P2)
    return tangent


def _structural_metrics(spec, split):
    count = int(spec["execution"]["structural_cases_per_split"])
    seed = int(spec["execution"]["structural_seed_by_split"][split])
    rng = np.random.default_rng(seed)
    passes = 0
    rank_min = 2
    generator_error = 0.0
    transition_defect = 0.0
    identity_error = 0.0
    symplectic = np.block(
        [[np.zeros((6, 6)), np.eye(6)], [-np.eye(6), np.zeros((6, 6))]]
    )
    charts = tuple(CHART_LOCAL_ORDER)
    for index in range(count):
        while True:
            positions = rng.normal(size=(3, 3))
            if min(
                np.linalg.norm(positions[first] - positions[second])
                for first, second in ((0, 1), (0, 2), (1, 2))
            ) > float(spec["corpus"]["minimum_noncolliding_distance"]):
                break
        masses = rng.uniform(0.35, 2.5, size=3)
        momenta = rng.normal(size=(3, 3))
        momenta -= np.sum(momenta, axis=0) / 3.0
        parameters = SystemParameters(masses, gravitational_constant=1.0)
        physical = normalize_center_of_mass(
            InertialState.from_components(positions, momenta / masses[:, None]),
            parameters,
        )
        chart = charts[index % len(charts)]
        state = lift_inertial_state(
            physical, parameters, chart, angles=rng.uniform(-np.pi, np.pi, size=2)
        )
        gradients = np.stack(
            (_constraint_gradient(state, 1), _constraint_gradient(state, 2))
        )
        tangents = np.column_stack(
            (_gauge_tangent(state, 1), _gauge_tangent(state, 2))
        )
        constraint_rank = int(np.linalg.matrix_rank(gradients, tol=1e-11))
        gauge_rank = int(np.linalg.matrix_rank(tangents, tol=1e-11))
        rank_min = min(rank_min, constraint_rank, gauge_rank)
        hamiltonian_tangents = np.column_stack(
            [np.concatenate((gradient[9:], -gradient[:9])) for gradient in gradients]
        )
        generator_error = max(
            generator_error, _scaled(hamiltonian_tangents, tangents)
        )

        target = charts[(index + 1) % len(charts)]
        matrix = _physical_chart_transition_matrix(chart, target)
        transition_defect = max(
            transition_defect,
            float(np.linalg.norm(matrix.T @ symplectic @ matrix - symplectic, ord=np.inf)),
        )
        vector = state.as_vector().copy()
        vector[17] += 0.173
        off_shell = MultiKSState.from_vector(chart, vector)
        expected = global_time_rate(off_shell) * (
            total_energy(project_state(off_shell, parameters), parameters)
            + off_shell.p_t
        )
        identity_error = max(
            identity_error, _scaled(regularized_hamiltonian(off_shell, parameters), expected)
        )
        passed = bool(
            constraint_rank == 2
            and gauge_rank == 2
            and 18 - constraint_rank - gauge_rank == 14
            and generator_error <= 5e-12
            and transition_defect <= 5e-12
            and identity_error <= 5e-12
        )
        passes += passed
    return {
        "case_count": count,
        "dimension_and_constraint_count_pass_rate": passes / count,
        "constraint_and_gauge_rank_min": rank_min,
        "hamiltonian_generator_scaled_max": generator_error,
        "physical_transition_symplectic_defect_max": transition_defect,
        "heggie_identity_scaled_max": identity_error,
    }


def _evaluate_case(case, source_definitions, reference, spec):
    _, parameters = _source_state(source_definitions[case["source_case_id"]])
    if case["category"] == "exact_passage":
        metrics = _collision_metrics(case, parameters, reference, spec)
    else:
        if case["category"] == "generic":
            physical, parameters = _source_state(source_definitions[case["source_case_id"]])
            horizon = float(spec["execution"]["generic_s_horizon"])
        else:
            physical = _near_state(parameters, case["chart"], int(case["selected_edge"]), float(case["near_distance"]))
            horizon = float(spec["execution"]["near_collision_s_horizon"])
        state = lift_inertial_state(
            physical,
            parameters,
            case["chart"],
            angles=case["gauge_angles"],
        )
        metrics = _common_metrics(state, parameters, reference, spec)
        metrics["trajectory_scaled"] = _trajectory_metric(state, parameters, horizon, spec["execution"])
        switched = _switch_trajectory_metric(
            state, parameters, horizon, spec["execution"]
        )
        metrics["chart_cocycle_scaled"] = max(
            metrics["chart_cocycle_scaled"], switched
        )
        metrics["switched_trajectory_scaled"] = switched
        metrics["switch_policy_pass"] = 1.0
    required_flags = (
        "switch_policy_pass",
        "collision_probe_convergence",
        "collision_spinor_crossing",
    )
    success = bool(
        all(np.isfinite(value) for value in metrics.values())
        and all(metrics.get(name, 1.0) == 1.0 for name in required_flags)
    )
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "source_case_id": case["source_case_id"],
        "chart": case["chart"],
        "selected_edge": case["selected_edge"],
        "physical_channel": case["physical_channel"],
        "success": success,
        "metrics": metrics,
    }


def main() -> None:
    args = _args()
    output = Path(args.output)
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    source_corpus = load_json(args.n3bp_corpus)
    specification_lock = _verify_specification_lock(args.spec)
    if corpus["spec_sha256"] != sha256_file(args.spec):
        raise RuntimeError("WP2-MULTI corpus uses another specification")
    if corpus["n3bp_corpus_sha256"] != sha256_file(args.n3bp_corpus):
        raise RuntimeError("WP2-MULTI source corpus hash mismatch")
    full_lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires the WP2-MULTI full lock")
        if output.exists():
            raise RuntimeError("refusing to execute the WP2-MULTI holdout twice")
        full_lock = verify_lock(args.lock, ROOT, expected_prefix=spec["campaign"])
        if runtime_fingerprint() != full_lock["runtime"]:
            raise RuntimeError("holdout runtime differs from the frozen WP2-MULTI runtime")
    prerequisites = _verify_prerequisites(spec)
    definitions = {str(case["case_id"]): case for case in source_corpus["cases"]}
    reference = _reference()
    cases = []
    for case in corpus["cases"]:
        if case["split"] != args.split:
            continue
        try:
            cases.append(_evaluate_case(case, definitions, reference, spec))
        except Exception as error:
            cases.append(
                {
                    "case_id": case["case_id"],
                    "category": case["category"],
                    "source_case_id": case["source_case_id"],
                    "chart": case["chart"],
                    "selected_edge": case["selected_edge"],
                    "physical_channel": case["physical_channel"],
                    "success": False,
                    "error": f"{type(error).__name__}: {error}",
                    "metrics": {},
                }
            )
    structural = _structural_metrics(spec, args.split)
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": args.split,
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "corpus_sha256": sha256_file(args.corpus),
        "source_corpus_sha256": sha256_file(args.n3bp_corpus),
        "prerequisites": prerequisites,
        "runtime": runtime_fingerprint(),
        "structural": {
            "symbolic_identity_pass_rate": _symbolic_identity_rate(),
            **structural,
            "unseen_scientific_holdout": 0,
            "triple_collision_qualified": 0,
        },
        "cases": cases,
    }
    if full_lock is not None:
        payload["qualification_id"] = full_lock["qualification_id"]
        payload["lock_sha256"] = full_lock["lock_sha256"]
    atomic_write_json(output, payload)
    print(f"WP2-MULTIQ-v1 {args.split}: {sum(case['success'] for case in cases)}/{len(cases)} cases")


if __name__ == "__main__":
    main()
