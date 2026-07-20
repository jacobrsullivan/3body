"""Qualified-source sampling for the WP3 exploratory search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from src.python.n3bp_qualification import (
    DOP853Config,
    InertialState,
    SystemParameters,
    figure_eight_choreography,
    lagrange_equilateral,
    normalize_center_of_mass,
    propagate_dop853,
)


EXECUTABLE_SPLITS = frozenset(("training", "calibration"))


class ReservedSplitError(RuntimeError):
    """Raised when exploratory code is asked to expose a reserved split."""


@dataclass(frozen=True)
class SamplePoint:
    """One exact vector-field evaluation point with provenance."""

    sample_id: str
    case_id: str
    split: str
    source_kind: str
    state: InertialState
    parameters: SystemParameters
    physical_time: float | None = None


def _rotation_xyz(angles: list[float]) -> np.ndarray:
    x_angle, y_angle, z_angle = (float(value) for value in angles)
    cx, sx = np.cos(x_angle), np.sin(x_angle)
    cy, sy = np.cos(y_angle), np.sin(y_angle)
    cz, sz = np.cos(z_angle), np.sin(z_angle)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return np.einsum(
        "ij,jk->ik",
        rz,
        np.einsum("ij,jk->ik", ry, rx, optimize=False),
        optimize=False,
    )


def _rotate_state(state: InertialState, rotation: np.ndarray) -> InertialState:
    return InertialState.from_components(
        np.einsum("ij,kj->ik", state.positions, rotation, optimize=False),
        np.einsum("ij,kj->ik", state.velocities, rotation, optimize=False),
    )


def build_upstream_case(
    case: Mapping[str, Any],
) -> tuple[InertialState, SystemParameters, float]:
    """Reconstruct a frozen WP1Q-N3BP-v1 source case."""

    case_type = str(case["case_type"])
    if case_type == "lagrange":
        orbit = lagrange_equilateral(
            side_length=float(case["side_length"]),
            mass=float(case["mass"]),
            gravitational_constant=float(case["gravitational_constant"]),
            phase=float(case["phase"]),
        )
        rotation = _rotation_xyz(list(case["rotation_xyz"]))
        initial = _rotate_state(orbit.initial_state, rotation)
        return initial, orbit.parameters, orbit.period
    if case_type == "figure_eight":
        orbit = figure_eight_choreography()
        return orbit.initial_state, orbit.parameters, orbit.period
    if case_type == "sjtu_periodic":
        masses = np.array([float(value) for value in case["masses"]])
        x1 = float(case["x1"])
        v1 = float(case["v1"])
        v2 = float(case["v2"])
        parameters = SystemParameters(masses, gravitational_constant=1.0)
        positions = np.array(
            [[x1, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        )
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
        return initial, parameters, float(case["period"])
    raise ValueError(f"unsupported upstream case type: {case_type}")


def _trajectory_points(
    item: Mapping[str, Any],
    upstream_cases: Mapping[str, Mapping[str, Any]],
    execution: Mapping[str, Any],
    split: str,
) -> list[SamplePoint]:
    source_case_id = str(item["source_case_id"])
    if source_case_id not in upstream_cases:
        raise ValueError(f"unknown upstream source case: {source_case_id}")
    source_case = upstream_cases[source_case_id]
    expected_split = str(item["required_upstream_split"])
    if source_case.get("split") != expected_split:
        raise ValueError(
            f"upstream split mismatch for {source_case_id}: "
            f"expected {expected_split}, got {source_case.get('split')}"
        )
    if expected_split == "holdout":
        raise ReservedSplitError(
            f"refusing to expose upstream holdout case {source_case_id}"
        )

    initial, parameters, period = build_upstream_case(source_case)
    sample_count = int(item["sample_count"])
    if sample_count < 2:
        raise ValueError("trajectory sample_count must be at least two")
    duration = period * float(item.get("period_fraction", 1.0))
    times = np.linspace(0.0, duration, sample_count)
    trajectory = propagate_dop853(
        initial,
        times,
        parameters,
        config=DOP853Config(
            rtol=float(execution["rtol"]),
            atol=float(execution["atol"]),
            max_step=period * float(execution["max_step_fraction_of_period"]),
        ),
    )
    case_id = str(item["case_id"])
    return [
        SamplePoint(
            sample_id=f"{case_id}:{index:04d}",
            case_id=case_id,
            split=split,
            source_kind="qualified_trajectory",
            state=InertialState(state),
            parameters=parameters,
            physical_time=float(time),
        )
        for index, (time, state) in enumerate(
            zip(trajectory.times, trajectory.states, strict=True)
        )
    ]


def _minimum_separation(positions: np.ndarray) -> float:
    return min(
        float(np.linalg.norm(positions[first] - positions[second]))
        for first, second in ((0, 1), (0, 2), (1, 2))
    )


def _collocation_points(
    item: Mapping[str, Any],
    split: str,
) -> list[SamplePoint]:
    rng = np.random.default_rng(int(item["seed"]))
    count = int(item["count"])
    if count < 1:
        raise ValueError("collocation count must be positive")
    mass_low, mass_high = (float(value) for value in item["mass_range"])
    gravity_low, gravity_high = (
        float(value) for value in item["gravitational_constant_range"]
    )
    length_low, length_high = (float(value) for value in item["length_scale_range"])
    velocity_low, velocity_high = (
        float(value) for value in item["velocity_factor_range"]
    )
    minimum_fraction = float(item["minimum_separation_fraction"])
    set_id = str(item["set_id"])

    points: list[SamplePoint] = []
    for index in range(count):
        masses = rng.uniform(mass_low, mass_high, size=3)
        gravitational_constant = float(rng.uniform(gravity_low, gravity_high))
        parameters = SystemParameters(masses, gravitational_constant)
        length_scale = float(rng.uniform(length_low, length_high))
        for _ in range(10_000):
            positions = rng.normal(size=(3, 3)) * length_scale
            if _minimum_separation(positions) >= minimum_fraction * length_scale:
                break
        else:
            raise RuntimeError("could not draw a collision-free collocation point")
        velocity_unit = np.sqrt(
            gravitational_constant * parameters.total_mass / length_scale
        )
        velocity_factor = float(rng.uniform(velocity_low, velocity_high))
        velocities = rng.normal(size=(3, 3)) * velocity_unit * velocity_factor
        state = normalize_center_of_mass(
            InertialState.from_components(positions, velocities), parameters
        )
        points.append(
            SamplePoint(
                sample_id=f"{set_id}:{index:04d}",
                case_id=set_id,
                split=split,
                source_kind="deterministic_spatial_collocation",
                state=state,
                parameters=parameters,
            )
        )
    return points


def sample_exploration_split(
    corpus: Mapping[str, Any],
    upstream_corpus: Mapping[str, Any],
    split: str,
) -> tuple[SamplePoint, ...]:
    """Materialize training/calibration points and refuse every reserved split."""

    allowed = tuple(str(value) for value in corpus["executable_splits"])
    if not allowed or not set(allowed).issubset(EXECUTABLE_SPLITS):
        raise ReservedSplitError(
            "exploration corpus must declare only training and calibration splits"
        )
    if split not in allowed:
        raise ReservedSplitError(
            f"split {split!r} is not executable; allowed splits are {allowed}"
        )
    upstream_cases = {
        str(case["case_id"]): case for case in upstream_corpus["cases"]
    }
    execution = corpus["execution"]
    points: list[SamplePoint] = []
    for item in corpus["trajectory_sources"]:
        if item["split"] == split:
            points.extend(
                _trajectory_points(item, upstream_cases, execution, split)
            )
    for item in corpus["collocation_sources"]:
        if item["split"] == split:
            points.extend(_collocation_points(item, split))
    if not points:
        raise ValueError(f"exploration corpus has no samples for split {split}")
    return tuple(points)
