"""CR3BP state-transition and periodic-orbit stability calculations.

The state convention is ``[x, y, z, vx, vy, vz]`` in normalized rotating
coordinates.  Unlike the generic WP4 variational module, this implementation
linearizes the rotating-frame CR3BP equations directly and propagates the
state and 6x6 state-transition matrix in one solve.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class MonodromyResult:
    """One-period state-transition result for a periodic-orbit seed."""

    final_state: np.ndarray
    monodromy: np.ndarray
    eigenvalues: np.ndarray
    stability_index: float
    closure_error: float
    determinant_error: float
    reciprocal_pair_error: float
    nfev: int


def cr3bp_rhs(_time: float, state: np.ndarray, mu: float) -> np.ndarray:
    """Return the first-order rotating-frame CR3BP vector field."""
    x, y, z, vx, vy, vz = np.asarray(state, dtype=float)
    dx1 = x + mu
    dx2 = x - 1.0 + mu
    r1_sq = dx1 * dx1 + y * y + z * z
    r2_sq = dx2 * dx2 + y * y + z * z
    if r1_sq <= 0.0 or r2_sq <= 0.0:
        raise ValueError("CR3BP state coincides with a primary")

    r1_cubed = r1_sq ** 1.5
    r2_cubed = r2_sq ** 1.5
    m1 = 1.0 - mu

    ax = 2.0 * vy + x - m1 * dx1 / r1_cubed - mu * dx2 / r2_cubed
    ay = -2.0 * vx + y - m1 * y / r1_cubed - mu * y / r2_cubed
    az = -m1 * z / r1_cubed - mu * z / r2_cubed
    return np.array([vx, vy, vz, ax, ay, az], dtype=float)


def cr3bp_jacobian(state: np.ndarray, mu: float) -> np.ndarray:
    """Return the analytic 6x6 Jacobian of :func:`cr3bp_rhs`."""
    x, y, z = np.asarray(state, dtype=float)[:3]
    dx1 = x + mu
    dx2 = x - 1.0 + mu
    r1_sq = dx1 * dx1 + y * y + z * z
    r2_sq = dx2 * dx2 + y * y + z * z
    if r1_sq <= 0.0 or r2_sq <= 0.0:
        raise ValueError("CR3BP state coincides with a primary")

    r1_3 = r1_sq ** 1.5
    r2_3 = r2_sq ** 1.5
    r1_5 = r1_sq ** 2.5
    r2_5 = r2_sq ** 2.5
    m1 = 1.0 - mu

    omega_xx = 1.0 + m1 * (3.0 * dx1 * dx1 / r1_5 - 1.0 / r1_3)
    omega_xx += mu * (3.0 * dx2 * dx2 / r2_5 - 1.0 / r2_3)
    omega_yy = 1.0 + m1 * (3.0 * y * y / r1_5 - 1.0 / r1_3)
    omega_yy += mu * (3.0 * y * y / r2_5 - 1.0 / r2_3)
    omega_zz = m1 * (3.0 * z * z / r1_5 - 1.0 / r1_3)
    omega_zz += mu * (3.0 * z * z / r2_5 - 1.0 / r2_3)
    omega_xy = 3.0 * y * (m1 * dx1 / r1_5 + mu * dx2 / r2_5)
    omega_xz = 3.0 * z * (m1 * dx1 / r1_5 + mu * dx2 / r2_5)
    omega_yz = 3.0 * y * z * (m1 / r1_5 + mu / r2_5)

    jacobian = np.zeros((6, 6), dtype=float)
    jacobian[:3, 3:] = np.eye(3)
    jacobian[3:, :3] = np.array(
        [
            [omega_xx, omega_xy, omega_xz],
            [omega_xy, omega_yy, omega_yz],
            [omega_xz, omega_yz, omega_zz],
        ]
    )
    jacobian[3, 4] = 2.0
    jacobian[4, 3] = -2.0
    return jacobian


def stability_index_from_eigenvalues(eigenvalues: np.ndarray) -> float:
    """Return the JPL/Poincare stability index from Floquet multipliers.

    The published catalogue convention is
    ``nu = 0.5 * (rho + 1 / rho)``, where ``rho`` is the largest multiplier
    modulus.  Marginally stable periodic orbits have ``nu == 1``.
    """
    values = np.asarray(eigenvalues, dtype=complex)
    if values.shape != (6,) or not np.all(np.isfinite(values)):
        raise ValueError("Expected six finite Floquet multipliers")
    rho = float(np.max(np.abs(values)))
    if rho <= 0.0:
        raise ValueError("Floquet multiplier modulus must be positive")
    return 0.5 * (rho + 1.0 / rho)


def reciprocal_pair_error(eigenvalues: np.ndarray) -> float:
    """Measure the worst mismatch from reciprocal Floquet pairing."""
    values = np.asarray(eigenvalues, dtype=complex)
    errors = []
    for index, value in enumerate(values):
        partners = np.delete(values, index)
        errors.append(float(np.min(np.abs(value * partners - 1.0))))
    return max(errors)


def integrate_state_and_stm(
    initial_state: np.ndarray,
    period: float,
    mu: float,
    *,
    rtol: float = 3e-12,
    atol: float = 3e-14,
    max_step: float = np.inf,
) -> MonodromyResult:
    """Propagate a CR3BP state and identity STM for one period."""
    state0 = np.asarray(initial_state, dtype=float)
    if state0.shape != (6,) or not np.all(np.isfinite(state0)):
        raise ValueError("initial_state must contain six finite values")
    if not np.isfinite(period) or period <= 0.0:
        raise ValueError("period must be finite and positive")
    if not 0.0 < mu < 1.0:
        raise ValueError("mu must lie in (0, 1)")

    combined0 = np.concatenate([state0, np.eye(6).reshape(-1)])

    def combined_rhs(time: float, combined: np.ndarray) -> np.ndarray:
        state = combined[:6]
        stm = combined[6:].reshape(6, 6)
        return np.concatenate(
            [cr3bp_rhs(time, state, mu), (cr3bp_jacobian(state, mu) @ stm).ravel()]
        )

    solution = solve_ivp(
        combined_rhs,
        (0.0, float(period)),
        combined0,
        method="DOP853",
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    if not solution.success:
        raise RuntimeError(f"State/STM integration failed: {solution.message}")

    final_state = solution.y[:6, -1]
    monodromy = solution.y[6:, -1].reshape(6, 6)
    eigenvalues = np.linalg.eigvals(monodromy)
    return MonodromyResult(
        final_state=final_state,
        monodromy=monodromy,
        eigenvalues=eigenvalues,
        stability_index=stability_index_from_eigenvalues(eigenvalues),
        closure_error=float(np.linalg.norm(final_state - state0)),
        determinant_error=float(abs(np.linalg.det(monodromy) - 1.0)),
        reciprocal_pair_error=reciprocal_pair_error(eigenvalues),
        nfev=int(solution.nfev),
    )
