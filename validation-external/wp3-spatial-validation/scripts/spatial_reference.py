"""Independent Brutus-case parsing, Taylor oracle, and variational diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import heyoka as hy
import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class ReferenceCase:
    masses: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray
    final_positions: np.ndarray
    final_velocities: np.ndarray
    duration: float

    @property
    def state(self) -> np.ndarray:
        return np.concatenate((self.positions.ravel(), self.velocities.ravel()))

    @property
    def final_state(self) -> np.ndarray:
        return np.concatenate(
            (self.final_positions.ravel(), self.final_velocities.ravel())
        )


def parse_case(case: dict[str, Any]) -> ReferenceCase:
    return ReferenceCase(
        masses=np.array([float(value) for value in case["masses_decimal"]]),
        positions=np.array(
            [[float(value) for value in row] for row in case["initial_positions_decimal"]]
        ),
        velocities=np.array(
            [[float(value) for value in row] for row in case["initial_velocities_decimal"]]
        ),
        final_positions=np.array(
            [
                [float(value) for value in row]
                for row in case["brutus_final_positions_decimal"]
            ]
        ),
        final_velocities=np.array(
            [
                [float(value) for value in row]
                for row in case["brutus_final_velocities_decimal"]
            ]
        ),
        duration=float(case["duration_decimal"]),
    )


def case_scales(case: ReferenceCase) -> tuple[float, float]:
    length = max(
        float(np.linalg.norm(case.positions[first] - case.positions[second]))
        for first, second in ((0, 1), (0, 2), (1, 2))
    )
    velocity = float(np.sqrt(np.sum(case.masses) / length))
    return length, velocity


def spatial_rank_ratio(case: ReferenceCase) -> float:
    m1, m2, _ = case.masses
    m12 = m1 + m2
    rho = case.positions[1] - case.positions[0]
    lambda_vector = case.positions[2] - (
        m1 * case.positions[0] + m2 * case.positions[1]
    ) / m12
    rho_dot = case.velocities[1] - case.velocities[0]
    lambda_dot = case.velocities[2] - (
        m1 * case.velocities[0] + m2 * case.velocities[1]
    ) / m12
    singular_values = np.linalg.svd(
        np.stack((rho, lambda_vector, rho_dot, lambda_dot)), compute_uv=False
    )
    return float(singular_values[-1] / singular_values[0])


def _real(value: Any, precision_bits: int) -> Any:
    return hy.real(str(value), precision_bits)


@lru_cache(maxsize=None)
def _system(mass_strings: tuple[str, str, str], precision_bits: int) -> list[Any]:
    variables = hy.make_vars(*(f"z{index}" for index in range(18)))
    masses = [_real(value, precision_bits) for value in mass_strings]
    system: list[Any] = []
    for index in range(9):
        system.append((variables[index], variables[9 + index]))
    zero = _real("0", precision_bits)
    for body in range(3):
        for component in range(3):
            acceleration = zero
            for other in range(3):
                if body == other:
                    continue
                displacement = [
                    variables[3 * other + axis] - variables[3 * body + axis]
                    for axis in range(3)
                ]
                radius_squared = sum(value * value for value in displacement)
                radius = hy.sqrt(radius_squared)
                acceleration += (
                    masses[other]
                    * displacement[component]
                    / (radius_squared * radius)
                )
            system.append((variables[9 + 3 * body + component], acceleration))
    return system


def _decimal_state(case: dict[str, Any], precision_bits: int) -> list[Any]:
    values: list[str] = []
    for row in case["initial_positions_decimal"]:
        values.extend(row)
    for row in case["initial_velocities_decimal"]:
        values.extend(row)
    return [_real(value, precision_bits) for value in values]


def _energy(state: list[Any], masses: list[Any], precision_bits: int) -> Any:
    half = _real("0.5", precision_bits)
    kinetic = _real("0", precision_bits)
    for body in range(3):
        speed_squared = sum(
            state[9 + 3 * body + axis] ** 2 for axis in range(3)
        )
        kinetic += half * masses[body] * speed_squared
    potential = _real("0", precision_bits)
    for first, second in ((0, 1), (0, 2), (1, 2)):
        radius_squared = sum(
            (state[3 * second + axis] - state[3 * first + axis]) ** 2
            for axis in range(3)
        )
        potential -= masses[first] * masses[second] / (radius_squared**half)
    return kinetic + potential


def integrate_taylor(
    case: dict[str, Any],
    times: np.ndarray,
    *,
    precision_bits: int,
    tolerance: str,
) -> dict[str, Any]:
    mass_strings = tuple(str(value) for value in case["masses_decimal"])
    state = _decimal_state(case, precision_bits)
    integrator = hy.taylor_adaptive_real(
        _system(mass_strings, precision_bits),
        state,
        tol=_real(tolerance, precision_bits),
        high_accuracy=True,
        compact_mode=True,
        prec=precision_bits,
    )
    masses = [_real(value, precision_bits) for value in mass_strings]
    initial_energy = _energy(list(integrator.state), masses, precision_bits)
    decimal_states = [[str(value) for value in integrator.state]]
    outcomes: list[str] = []
    steps = 0
    for time in times[1:]:
        outcome = integrator.propagate_until(_real(repr(float(time)), precision_bits))
        outcomes.append(str(outcome[0]))
        if len(outcome) > 3:
            steps += int(outcome[3])
        decimal_states.append([str(value) for value in integrator.state])
    final_energy = _energy(list(integrator.state), masses, precision_bits)
    relative_energy_drift = abs(
        (final_energy - initial_energy)
        / max(abs(initial_energy), _real("1", precision_bits))
    )
    return {
        "precision_bits": precision_bits,
        "tolerance": tolerance,
        "times_decimal": [repr(float(value)) for value in times],
        "states_decimal": decimal_states,
        "states_float64": np.array(
            [[float(value) for value in row] for row in decimal_states]
        ),
        "relative_energy_drift_decimal": str(relative_energy_drift),
        "outcomes": outcomes,
        "total_steps": steps,
    }


def _rhs_and_tangent(
    _time: float,
    combined: np.ndarray,
    masses: np.ndarray,
) -> np.ndarray:
    state = combined[:18]
    tangent = combined[18:]
    positions = state[:9].reshape(3, 3)
    velocities = state[9:].reshape(3, 3)
    delta_positions = tangent[:9].reshape(3, 3)
    delta_velocities = tangent[9:].reshape(3, 3)
    accelerations = np.zeros((3, 3))
    delta_accelerations = np.zeros((3, 3))
    for body in range(3):
        for other in range(3):
            if body == other:
                continue
            displacement = positions[other] - positions[body]
            delta_displacement = delta_positions[other] - delta_positions[body]
            radius_squared = float(np.dot(displacement, displacement))
            radius = float(np.sqrt(radius_squared))
            inverse_cube = 1.0 / (radius_squared * radius)
            accelerations[body] += masses[other] * displacement * inverse_cube
            delta_accelerations[body] += masses[other] * (
                delta_displacement * inverse_cube
                - 3.0
                * displacement
                * float(np.dot(displacement, delta_displacement))
                / (radius_squared * radius_squared * radius)
            )
    return np.concatenate(
        (
            velocities.ravel(),
            accelerations.ravel(),
            delta_velocities.ravel(),
            delta_accelerations.ravel(),
        )
    )


def finite_time_lyapunov(
    case: ReferenceCase,
    *,
    total_duration: float,
    segment_duration: float,
    rtol: float,
    atol: float,
) -> float:
    digest = np.frombuffer(
        __import__("hashlib").sha256(case.state.tobytes()).digest(), dtype=np.uint8
    ).astype(float)
    tangent = np.resize(digest - np.mean(digest), 18)
    tangent[:9] = (
        tangent[:9].reshape(3, 3)
        - np.average(
            tangent[:9].reshape(3, 3), axis=0, weights=case.masses
        )
    ).ravel()
    tangent[9:] = (
        tangent[9:].reshape(3, 3)
        - np.average(
            tangent[9:].reshape(3, 3), axis=0, weights=case.masses
        )
    ).ravel()
    tangent = tangent.ravel()
    tangent /= np.linalg.norm(tangent)
    state = case.state.copy()
    accumulated = 0.0
    elapsed = 0.0
    while elapsed < total_duration - 1e-15:
        stop = min(total_duration, elapsed + segment_duration)
        result = solve_ivp(
            _rhs_and_tangent,
            (elapsed, stop),
            np.concatenate((state, tangent)),
            args=(case.masses,),
            method="DOP853",
            rtol=rtol,
            atol=atol,
        )
        if not result.success:
            raise RuntimeError(result.message)
        state = result.y[:18, -1]
        tangent = result.y[18:, -1]
        norm = float(np.linalg.norm(tangent))
        if not np.isfinite(norm) or norm <= 0.0:
            raise ArithmeticError("invalid variational tangent norm")
        accumulated += np.log(norm)
        tangent /= norm
        elapsed = stop
    return float(accumulated / total_duration)
