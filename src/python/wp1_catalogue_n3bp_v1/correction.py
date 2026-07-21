"""DOP853 closure evaluation and nonlinear correction."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares

from .model import (
    CorrectionResult,
    CorrectionSettings,
    FloatArray,
    OrbitParameters,
    PLANAR_INDICES,
    canonical_section_state,
)


def inertial_rhs(
    _time: float, state: NDArray[np.float64], masses: Sequence[float]
) -> FloatArray:
    """Newtonian three-body RHS in full 18D Cartesian inertial coordinates."""

    y = np.asarray(state, dtype=np.float64)
    if y.shape != (18,):
        raise ValueError("inertial state must have shape (18,)")
    mass = np.asarray(masses, dtype=np.float64)
    if mass.shape != (3,) or np.any(mass <= 0.0):
        raise ValueError("masses must contain three positive values")

    positions = y[:9].reshape(3, 3)
    velocities = y[9:].reshape(3, 3)
    accelerations = np.zeros((3, 3), dtype=np.float64)
    for i in range(3):
        for j in range(i + 1, 3):
            delta = positions[j] - positions[i]
            distance_squared = float(delta @ delta)
            if distance_squared <= 0.0:
                raise ValueError("collision encountered during propagation")
            inverse_cube = distance_squared ** -1.5
            accelerations[i] += mass[j] * delta * inverse_cube
            accelerations[j] -= mass[i] * delta * inverse_cube
    return np.concatenate((velocities.reshape(-1), accelerations.reshape(-1)))


def propagate_one_period(
    parameters: OrbitParameters,
    settings: CorrectionSettings = CorrectionSettings(),
) -> tuple[FloatArray, FloatArray]:
    initial = canonical_section_state(
        parameters.m1,
        parameters.m2,
        parameters.x1,
        parameters.v1,
        parameters.v2,
        parameters.period,
    )
    solution = solve_ivp(
        inertial_rhs,
        (0.0, parameters.period),
        initial,
        args=(parameters.masses,),
        method="DOP853",
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=parameters.period * settings.max_step_fraction,
    )
    if not solution.success:
        raise RuntimeError(f"DOP853 propagation failed: {solution.message}")
    return initial, np.asarray(solution.y[:, -1], dtype=np.float64)


def full_planar_closure(
    parameters: OrbitParameters,
    settings: CorrectionSettings = CorrectionSettings(),
) -> FloatArray:
    """Return all twelve planar final-minus-initial state components."""

    initial, final = propagate_one_period(parameters, settings)
    return (final - initial)[PLANAR_INDICES]


def scaled_planar_closure(
    variables: Sequence[float],
    m1: float,
    m2: float,
    settings: CorrectionSettings = CorrectionSettings(),
) -> FloatArray:
    """Closure residual used by the fixed-mass nonlinear corrector."""

    x1, v1, v2, period = (float(value) for value in variables)
    parameters = OrbitParameters(m1, m2, x1, v1, v2, period)
    residual = full_planar_closure(parameters, settings)
    velocity_scale = np.sqrt(m1 + m2 + 1.0)
    scaled = residual.copy()
    scaled[6:] /= velocity_scale
    return scaled


def correct_orbit(
    seed: OrbitParameters,
    settings: CorrectionSettings = CorrectionSettings(),
) -> CorrectionResult:
    """Correct one fixed-mass orbit with a damped trust-region least-squares solve."""

    solution = least_squares(
        scaled_planar_closure,
        seed.correction_vector(),
        args=(seed.m1, seed.m2, settings),
        method="trf",
        bounds=(
            np.array([-0.95, -5.0, -5.0, 0.25], dtype=np.float64),
            np.array([0.95, 5.0, 5.0, 30.0], dtype=np.float64),
        ),
        x_scale="jac",
        loss="linear",
        max_nfev=settings.max_nfev,
        xtol=settings.xtol,
        ftol=settings.ftol,
        gtol=settings.gtol,
    )
    parameters = OrbitParameters(seed.m1, seed.m2, *solution.x)
    residual = full_planar_closure(parameters, settings)
    position_linf = float(np.max(np.abs(residual[:6])))
    velocity_linf = float(np.max(np.abs(residual[6:])))
    residual_linf = max(position_linf, velocity_linf)
    success = bool(solution.success and residual_linf <= settings.closure_tolerance)
    state = canonical_section_state(
        parameters.m1,
        parameters.m2,
        parameters.x1,
        parameters.v1,
        parameters.v2,
        parameters.period,
    )
    return CorrectionResult(
        parameters=parameters,
        state=tuple(float(value) for value in state),
        residual=tuple(float(value) for value in residual),
        residual_linf=residual_linf,
        position_closure_linf=position_linf,
        velocity_closure_linf=velocity_linf,
        nfev=int(solution.nfev),
        success=success,
        message=str(solution.message),
    )

