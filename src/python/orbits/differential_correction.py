"""Strict symmetry-based differential correction for CR3BP periodic seeds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares

from src.python.validation.cr3bp_variational import cr3bp_rhs


Family = Literal["lyapunov", "halo"]


@dataclass(frozen=True)
class CorrectionResult:
    """Explicit outcome of a periodic-orbit differential correction."""

    success: bool
    family: Family
    initial_state: np.ndarray
    period: float
    symmetry_residual: float
    closure_error: float
    nfev: int
    message: str
    fixed_component: str
    fixed_value: float


def _propagate(state: np.ndarray, duration: float, mu: float) -> np.ndarray:
    solution = solve_ivp(
        lambda time, value: cr3bp_rhs(time, value, mu),
        (0.0, float(duration)),
        np.asarray(state, dtype=float),
        method="DOP853",
        rtol=2e-12,
        atol=2e-14,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution.y[:, -1]


def _result(
    *,
    family: Family,
    state: np.ndarray,
    half_period: float,
    residual: np.ndarray,
    mu: float,
    nfev: int,
    optimizer_success: bool,
    message: str,
    fixed_component: str,
    fixed_value: float,
    residual_tolerance: float,
    closure_tolerance: float,
) -> CorrectionResult:
    period = 2.0 * float(half_period)
    symmetry_residual = float(np.linalg.norm(residual))
    try:
        closure_error = float(np.linalg.norm(_propagate(state, period, mu) - state))
    except Exception as exc:
        return CorrectionResult(
            success=False,
            family=family,
            initial_state=state,
            period=period,
            symmetry_residual=symmetry_residual,
            closure_error=float("inf"),
            nfev=nfev,
            message=f"full-period verification failed: {exc}",
            fixed_component=fixed_component,
            fixed_value=fixed_value,
        )

    success = bool(
        optimizer_success
        and np.isfinite(symmetry_residual)
        and np.isfinite(closure_error)
        and symmetry_residual <= residual_tolerance
        and closure_error <= closure_tolerance
    )
    if optimizer_success and not success:
        message = (
            f"verification failed: residual={symmetry_residual:.3e}, "
            f"closure={closure_error:.3e}"
        )
    return CorrectionResult(
        success=success,
        family=family,
        initial_state=state,
        period=period,
        symmetry_residual=symmetry_residual,
        closure_error=closure_error,
        nfev=nfev,
        message=message,
        fixed_component=fixed_component,
        fixed_value=fixed_value,
    )


def correct_planar_lyapunov(
    seed_state: np.ndarray,
    seed_period: float,
    mu: float,
    *,
    fixed_x: float | None = None,
    residual_tolerance: float = 1e-10,
    closure_tolerance: float = 1e-9,
    max_nfev: int = 40,
) -> CorrectionResult:
    """Correct ``vy0`` and half-period while holding planar ``x0`` fixed."""
    seed = np.asarray(seed_state, dtype=float)
    if seed.shape != (6,) or not np.all(np.isfinite(seed)):
        raise ValueError("seed_state must contain six finite values")
    if not np.isfinite(seed_period) or seed_period <= 0.0:
        raise ValueError("seed_period must be finite and positive")
    x0 = float(seed[0] if fixed_x is None else fixed_x)

    def state_from_variables(values: np.ndarray) -> np.ndarray:
        return np.array([x0, 0.0, 0.0, 0.0, values[0], 0.0], dtype=float)

    def residual(values: np.ndarray) -> np.ndarray:
        final = _propagate(state_from_variables(values), values[1], mu)
        return final[[1, 3]]

    lower = np.array([seed[4] - max(2.0, 3.0 * abs(seed[4])), 0.2 * seed_period])
    upper = np.array([seed[4] + max(2.0, 3.0 * abs(seed[4])), 0.8 * seed_period])
    optimum = least_squares(
        residual,
        np.array([seed[4], 0.5 * seed_period]),
        bounds=(lower, upper),
        x_scale="jac",
        ftol=1e-13,
        xtol=1e-13,
        gtol=1e-13,
        max_nfev=max_nfev,
    )
    state = state_from_variables(optimum.x)
    return _result(
        family="lyapunov",
        state=state,
        half_period=optimum.x[1],
        residual=optimum.fun,
        mu=mu,
        nfev=int(optimum.nfev),
        optimizer_success=bool(optimum.success),
        message=str(optimum.message),
        fixed_component="x",
        fixed_value=x0,
        residual_tolerance=residual_tolerance,
        closure_tolerance=closure_tolerance,
    )


def correct_halo(
    seed_state: np.ndarray,
    seed_period: float,
    mu: float,
    *,
    fixed_z: float | None = None,
    residual_tolerance: float = 1e-10,
    closure_tolerance: float = 1e-9,
    max_nfev: int = 60,
) -> CorrectionResult:
    """Correct ``x0``, ``vy0`` and half-period while holding ``z0`` fixed."""
    seed = np.asarray(seed_state, dtype=float)
    if seed.shape != (6,) or not np.all(np.isfinite(seed)):
        raise ValueError("seed_state must contain six finite values")
    if not np.isfinite(seed_period) or seed_period <= 0.0:
        raise ValueError("seed_period must be finite and positive")
    z0 = float(seed[2] if fixed_z is None else fixed_z)
    if abs(z0) < 1e-12:
        raise ValueError("Halo correction requires non-zero fixed_z")

    def state_from_variables(values: np.ndarray) -> np.ndarray:
        return np.array([values[0], 0.0, z0, 0.0, values[1], 0.0], dtype=float)

    def residual(values: np.ndarray) -> np.ndarray:
        final = _propagate(state_from_variables(values), values[2], mu)
        return final[[1, 3, 5]]

    x_span = max(0.35, 2.0 * abs(seed[0]))
    vy_span = max(3.0, 4.0 * abs(seed[4]))
    lower = np.array(
        [seed[0] - x_span, seed[4] - vy_span, 0.2 * seed_period], dtype=float
    )
    upper = np.array(
        [seed[0] + x_span, seed[4] + vy_span, 0.8 * seed_period], dtype=float
    )
    optimum = least_squares(
        residual,
        np.array([seed[0], seed[4], 0.5 * seed_period]),
        bounds=(lower, upper),
        x_scale="jac",
        ftol=1e-13,
        xtol=1e-13,
        gtol=1e-13,
        max_nfev=max_nfev,
    )
    state = state_from_variables(optimum.x)
    return _result(
        family="halo",
        state=state,
        half_period=optimum.x[2],
        residual=optimum.fun,
        mu=mu,
        nfev=int(optimum.nfev),
        optimizer_success=bool(optimum.success),
        message=str(optimum.message),
        fixed_component="z",
        fixed_value=z0,
        residual_tolerance=residual_tolerance,
        closure_tolerance=closure_tolerance,
    )
