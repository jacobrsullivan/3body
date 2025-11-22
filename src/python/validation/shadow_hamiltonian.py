"""
Shadow Hamiltonian Analysis for Symplectic Integrators (WP1 Phase 3).

Implements backward error analysis to verify that numerical trajectories
are exact solutions of a nearby "shadow" Hamiltonian H̃.

Mathematical Background:
========================

Backward Error Analysis Theorem (Hairer et al., 2006):
------------------------------------------------------
For a symplectic integrator with stepsize h applied to Hamiltonian H,
the numerical solution is the exact solution of a modified Hamiltonian:

    H̃ = H + h²·H₂ + h⁴·H₄ + O(h⁶)

where H₂, H₄ are correction terms.

Key Property:
- For bounded H̃, the numerical trajectory exhibits bounded error
- Secular drift in H̃ indicates non-symplectic behavior or instability
- Target for WP1 Tier 2: |ΔH̃| < 10⁻²⁵

Computation Strategy:
---------------------
1. Integrate trajectory with symplectic method
2. Compute H (original Hamiltonian) along trajectory
3. Estimate H₂ correction using finite differences
4. Compute shadow Hamiltonian H̃ = H + h²·H₂
5. Verify H̃ is bounded and drift-free

References:
-----------
- Hairer, Lubich, Wanner (2006): "Geometric Numerical Integration", Chapter IX
- Sanz-Serna & Calvo (1994): "Numerical Hamiltonian Problems"
- Reich (1999): "Backward error analysis for numerical integrators"
"""

from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
import numpy as np
from scipy.interpolate import interp1d
import logging

logger = logging.getLogger(__name__)


@dataclass
class ShadowHamiltonianResult:
    """
    Results from shadow Hamiltonian analysis.

    Attributes:
        times: Time points
        H_original: Original Hamiltonian H along trajectory
        H_shadow: Shadow Hamiltonian H̃ along trajectory
        H2_correction: Second-order correction H₂
        drift: Linear drift rate (from regression)
        rms_error: RMS variation in H̃
        bounded: Whether H̃ is bounded (passes validation)
        metadata: Additional information
    """
    times: np.ndarray
    H_original: np.ndarray
    H_shadow: np.ndarray
    H2_correction: np.ndarray
    drift: float
    rms_error: float
    bounded: bool
    metadata: Dict[str, Any]


class ShadowHamiltonianAnalyzer:
    """
    Analyze shadow Hamiltonian for symplectic integrators.

    Performs backward error analysis to verify numerical accuracy.
    """

    def __init__(
        self,
        hamiltonian: Callable[[np.ndarray], float],
        gradient: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        hessian: Optional[Callable[[np.ndarray], np.ndarray]] = None
    ):
        """
        Initialize shadow Hamiltonian analyzer.

        Args:
            hamiltonian: H(state) → scalar (total energy)
            gradient: ∇H(state) → (6,) [optional]
            hessian: ∇²H(state) → (6,6) [optional]
        """
        self.hamiltonian = hamiltonian
        self.gradient = gradient
        self.hessian = hessian

    def _compute_gradient_numerical(
        self,
        state: np.ndarray,
        eps: float = 1e-7
    ) -> np.ndarray:
        """
        Compute gradient numerically via finite differences.

        Args:
            state: Current state
            eps: Finite difference step

        Returns:
            Gradient vector
        """
        dim = len(state)
        grad = np.zeros(dim)
        H0 = self.hamiltonian(state)

        for i in range(dim):
            state_plus = state.copy()
            state_plus[i] += eps
            H_plus = self.hamiltonian(state_plus)
            grad[i] = (H_plus - H0) / eps

        return grad

    def _compute_hessian_numerical(
        self,
        state: np.ndarray,
        eps: float = 1e-6
    ) -> np.ndarray:
        """
        Compute Hessian numerically.

        Args:
            state: Current state
            eps: Finite difference step

        Returns:
            Hessian matrix (dim, dim)
        """
        dim = len(state)
        hess = np.zeros((dim, dim))
        H0 = self.hamiltonian(state)

        # First-order terms
        H_plus = np.zeros(dim)
        for i in range(dim):
            state_plus = state.copy()
            state_plus[i] += eps
            H_plus[i] = self.hamiltonian(state_plus)

        # Second-order terms
        for i in range(dim):
            for j in range(i, dim):
                state_plus = state.copy()
                state_plus[i] += eps
                state_plus[j] += eps
                H_plus_ij = self.hamiltonian(state_plus)

                if i == j:
                    # Diagonal
                    state_plus2 = state.copy()
                    state_plus2[i] += 2*eps
                    H_plus2 = self.hamiltonian(state_plus2)
                    hess[i, i] = (H_plus2 - 2*H_plus[i] + H0) / (eps**2)
                else:
                    # Off-diagonal
                    hess[i, j] = (H_plus_ij - H_plus[i] - H_plus[j] + H0) / (eps**2)
                    hess[j, i] = hess[i, j]

        return hess

    def _compute_H2_correction(
        self,
        state: np.ndarray,
        velocity: np.ndarray,
        h: float
    ) -> float:
        """
        Compute second-order correction H₂.

        Using simplified formula from Hairer et al. (2006):
            H₂ ≈ (1/12) · v^T · ∇²H · v

        where v is the velocity along the trajectory.

        Args:
            state: Current state
            velocity: Velocity dstate/dt
            h: Timestep

        Returns:
            H₂ correction term
        """
        # Compute Hessian
        if self.hessian is not None:
            hess = self.hessian(state)
        else:
            hess = self._compute_hessian_numerical(state)

        # H₂ = (1/12) · v^T · ∇²H · v
        H2 = (1.0 / 12.0) * np.dot(velocity, hess @ velocity)

        return H2

    def analyze_trajectory(
        self,
        times: np.ndarray,
        states: np.ndarray,
        timestep: float,
        drift_threshold: float = 1e-25
    ) -> ShadowHamiltonianResult:
        """
        Analyze shadow Hamiltonian along numerical trajectory.

        Args:
            times: Time points
            states: State trajectory (N, 6)
            timestep: Integration timestep h
            drift_threshold: Threshold for drift (Tier 2: 10⁻²⁵)

        Returns:
            ShadowHamiltonianResult
        """
        n_points = len(times)
        H_original = np.zeros(n_points)
        H2_correction = np.zeros(n_points)

        logger.info(f"Computing shadow Hamiltonian for {n_points} points...")

        # Compute H along trajectory
        for i in range(n_points):
            H_original[i] = self.hamiltonian(states[i])

        # Compute velocities (numerical derivative)
        velocities = np.zeros_like(states)
        for i in range(1, n_points - 1):
            dt_fwd = times[i+1] - times[i]
            dt_bwd = times[i] - times[i-1]
            velocities[i] = (states[i+1] - states[i-1]) / (dt_fwd + dt_bwd)

        # Forward/backward differences for endpoints
        velocities[0] = (states[1] - states[0]) / (times[1] - times[0])
        velocities[-1] = (states[-1] - states[-2]) / (times[-1] - times[-2])

        # Compute H₂ corrections
        for i in range(n_points):
            H2_correction[i] = self._compute_H2_correction(
                states[i],
                velocities[i],
                timestep
            )

        # Shadow Hamiltonian: H̃ = H + h²·H₂
        H_shadow = H_original + (timestep**2) * H2_correction

        # Analyze drift (linear regression)
        drift_rate = self._compute_drift_rate(times, H_shadow)
        rms_error = np.std(H_shadow)

        # Check if bounded
        max_drift = np.abs(H_shadow[-1] - H_shadow[0])
        bounded = max_drift < drift_threshold

        metadata = {
            'timestep': timestep,
            'drift_threshold': drift_threshold,
            'max_drift': max_drift,
            'mean_H': np.mean(H_original),
            'mean_H_shadow': np.mean(H_shadow),
            'std_H': np.std(H_original),
            'std_H_shadow': np.std(H_shadow),
        }

        logger.info(f"Shadow Hamiltonian analysis complete:")
        logger.info(f"  Drift rate: {drift_rate:.2e}")
        logger.info(f"  Max drift: {max_drift:.2e}")
        logger.info(f"  RMS error: {rms_error:.2e}")
        logger.info(f"  Bounded: {bounded}")

        return ShadowHamiltonianResult(
            times=times,
            H_original=H_original,
            H_shadow=H_shadow,
            H2_correction=H2_correction,
            drift=drift_rate,
            rms_error=rms_error,
            bounded=bounded,
            metadata=metadata
        )

    def _compute_drift_rate(self, times: np.ndarray, H: np.ndarray) -> float:
        """
        Compute linear drift rate via least squares.

        Args:
            times: Time array
            H: Hamiltonian values

        Returns:
            Drift rate dH/dt
        """
        # Linear regression: H(t) = a + b·t
        A = np.vstack([np.ones_like(times), times]).T
        coeffs, residuals, rank, s = np.linalg.lstsq(A, H, rcond=None)

        drift_rate = coeffs[1]  # Slope
        return drift_rate


def create_cr3bp_shadow_analyzer(mu: float) -> ShadowHamiltonianAnalyzer:
    """
    Create shadow Hamiltonian analyzer for CR3BP.

    Args:
        mu: Mass parameter

    Returns:
        ShadowHamiltonianAnalyzer configured for CR3BP
    """
    from ..utils.dynamics import calculate_jacobi_constant

    def hamiltonian_cr3bp(state: np.ndarray) -> float:
        """
        CR3BP Hamiltonian (Jacobi constant).

        In CR3BP, the Jacobi constant C is the conserved quantity.
        """
        return -calculate_jacobi_constant(state, mu)  # Negative for energy

    return ShadowHamiltonianAnalyzer(
        hamiltonian=hamiltonian_cr3bp,
        gradient=None,  # Will use numerical
        hessian=None   # Will use numerical
    )


def validate_tier2_precision(
    result: ShadowHamiltonianResult,
    threshold: float = 1e-25
) -> bool:
    """
    Validate Tier 2 precision target.

    Args:
        result: Shadow Hamiltonian analysis result
        threshold: Tier 2 threshold (default: 10⁻²⁵)

    Returns:
        True if meets Tier 2 precision
    """
    meets_drift = np.abs(result.drift) < threshold
    meets_rms = result.rms_error < threshold
    is_bounded = result.bounded

    logger.info(f"Tier 2 Validation:")
    logger.info(f"  Drift < {threshold:.0e}: {meets_drift}")
    logger.info(f"  RMS < {threshold:.0e}: {meets_rms}")
    logger.info(f"  Bounded: {is_bounded}")

    return meets_drift and meets_rms and is_bounded
