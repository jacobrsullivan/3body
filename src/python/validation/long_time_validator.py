"""
Long-time validation for WP 4.3: Numerical Robustness.

This module performs extended integration (10⁴-10⁶ periods) to verify:
1. Long-term conservation (no secular drift)
2. Shadow Hamiltonian analysis (backward error)
3. Comparison of integral drift vs energy drift

True conserved quantities should drift at the same rate as the energy
(both limited by integrator error), not faster.
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple
from scipy.integrate import solve_ivp


@dataclass
class LongTimeResult:
    """
    Result from long-time integration validation.

    Attributes:
        success: Integration completed successfully
        max_drift_I: Maximum |I(t) - I(0)| / |I(0)|
        max_drift_E: Maximum |E(t) - E(0)| / |E(0)|
        drift_ratio: max_drift_I / max_drift_E
        drift_I_rate: Linear drift rate (slope) for I
        drift_E_rate: Linear drift rate (slope) for E
        is_bounded: True if drift is bounded (not secular)
        integration_time: Total integration time achieved
        n_checkpoints: Number of checkpoints evaluated
        times: Array of checkpoint times
        drift_I_history: Array of I drift at each checkpoint
        drift_E_history: Array of E drift at each checkpoint
    """
    success: bool
    max_drift_I: float
    max_drift_E: float
    drift_ratio: float
    drift_I_rate: float
    drift_E_rate: float
    is_bounded: bool
    integration_time: float
    n_checkpoints: int
    times: np.ndarray
    drift_I_history: np.ndarray
    drift_E_history: np.ndarray

    def __str__(self) -> str:
        lines = []
        lines.append("LONG-TIME VALIDATION RESULT")
        lines.append(f"  Integration time: {self.integration_time:.2e}")
        lines.append(f"  Max drift (I): {self.max_drift_I:.2e}")
        lines.append(f"  Max drift (E): {self.max_drift_E:.2e}")
        lines.append(f"  Drift ratio (I/E): {self.drift_ratio:.2f}")
        lines.append(f"  Drift rate (I): {self.drift_I_rate:.2e}")
        lines.append(f"  Drift rate (E): {self.drift_E_rate:.2e}")
        if self.is_bounded:
            lines.append("  ✓ Drift is BOUNDED (not secular)")
        else:
            lines.append("  ✗ Drift appears SECULAR (growing)")
        return "\n".join(lines)


class LongTimeValidator:
    """
    Long-time integration and shadow Hamiltonian analysis.

    Example:
        >>> validator = LongTimeValidator()
        >>> result = validator.validate_long_time(
        ...     ic=initial_condition,
        ...     integral_func=my_integral,
        ...     hamiltonian_func=my_hamiltonian,
        ...     dynamics_func=my_dynamics,
        ...     t_max=1e6
        ... )
        >>> print(f"Bounded drift: {result.is_bounded}")
    """

    def __init__(
        self,
        integrator: str = 'DOP853',
        rtol: float = 1e-13,
        atol: float = 1e-15,
        n_checkpoints: int = 1000
    ):
        """
        Initialize long-time validator.

        Args:
            integrator: ODE integrator (should be symplectic or high-order)
            rtol: Relative tolerance (tighter for long integration)
            atol: Absolute tolerance (tighter for long integration)
            n_checkpoints: Number of checkpoints to monitor
        """
        self.integrator = integrator
        self.rtol = rtol
        self.atol = atol
        self.n_checkpoints = n_checkpoints

    def validate_long_time(
        self,
        ic: np.ndarray,
        integral_func: Callable,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        t_max: float = 1e6,
        verbose: bool = True
    ) -> LongTimeResult:
        """
        Integrate for very long times and monitor drift.

        Args:
            ic: Initial condition
            integral_func: Integral evaluator I(state)
            hamiltonian_func: Hamiltonian evaluator H(state)
            dynamics_func: Dynamics RHS function
            t_max: Maximum integration time (in orbital periods)
            verbose: Print progress

        Returns:
            LongTimeResult
        """
        if verbose:
            print("=" * 70)
            print(f"LONG-TIME VALIDATION (t_max = {t_max:.2e})")
            print("=" * 70)

        # Checkpoint times
        t_eval = np.linspace(0, t_max, self.n_checkpoints)

        # Initial values
        try:
            I_0 = integral_func(ic)
            E_0 = hamiltonian_func(ic)
        except Exception as e:
            if verbose:
                print(f"Error evaluating initial conditions: {e}")
            return self._failed_result()

        # Integrate
        try:
            if verbose:
                print(f"Integrating to t = {t_max:.2e}...")

            sol = solve_ivp(
                lambda t, y: dynamics_func(t, y),
                [0, t_max],
                ic,
                t_eval=t_eval,
                method=self.integrator,
                rtol=self.rtol,
                atol=self.atol,
                dense_output=False
            )

            if not sol.success:
                if verbose:
                    print(f"Integration failed: {sol.message}")
                return self._failed_result()

            if verbose:
                print(f"Integration successful ({len(sol.t)} steps)")

        except Exception as e:
            if verbose:
                print(f"Integration error: {e}")
            return self._failed_result()

        # Evaluate integral and energy along trajectory
        if verbose:
            print("Evaluating conservation...")

        I_vals = []
        E_vals = []

        for i, y in enumerate(sol.y.T):
            try:
                I_vals.append(integral_func(y))
                E_vals.append(hamiltonian_func(y))
            except Exception:
                I_vals.append(np.nan)
                E_vals.append(np.nan)

        I_vals = np.array(I_vals)
        E_vals = np.array(E_vals)

        # Compute drifts
        drift_I = np.abs(I_vals - I_0) / (np.abs(I_0) + 1e-16)
        drift_E = np.abs(E_vals - E_0) / (np.abs(E_0) + 1e-16)

        # Remove NaNs
        valid = np.isfinite(drift_I) & np.isfinite(drift_E)
        drift_I = drift_I[valid]
        drift_E = drift_E[valid]
        t_valid = sol.t[valid]

        if len(drift_I) == 0:
            if verbose:
                print("No valid evaluations")
            return self._failed_result()

        # Statistics
        max_drift_I = np.max(drift_I)
        max_drift_E = np.max(drift_E)
        drift_ratio = max_drift_I / (max_drift_E + 1e-16)

        # Linear fit to detect secular drift
        drift_I_rate = np.polyfit(t_valid, drift_I, 1)[0]
        drift_E_rate = np.polyfit(t_valid, drift_E, 1)[0]

        # Check if bounded (growth factor < 10 from first to last window)
        is_bounded = self._check_bounded_drift(drift_I, window=100)

        result = LongTimeResult(
            success=True,
            max_drift_I=max_drift_I,
            max_drift_E=max_drift_E,
            drift_ratio=drift_ratio,
            drift_I_rate=drift_I_rate,
            drift_E_rate=drift_E_rate,
            is_bounded=is_bounded,
            integration_time=t_max,
            n_checkpoints=len(t_valid),
            times=t_valid,
            drift_I_history=drift_I,
            drift_E_history=drift_E
        )

        if verbose:
            print(f"\n{result}")
            print("=" * 70)

        return result

    def shadow_hamiltonian_analysis(
        self,
        ic: np.ndarray,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        t_max: float = 1e4,
        verbose: bool = True
    ) -> Dict:
        """
        Backward error analysis: estimate shadow Hamiltonian.

        For symplectic integrators, the numerical trajectory is an exact
        solution of a nearby "shadow" Hamiltonian H_shadow ≈ H + O(h^p).

        Args:
            ic: Initial condition
            hamiltonian_func: Hamiltonian evaluator
            dynamics_func: Dynamics RHS
            t_max: Integration time
            verbose: Print results

        Returns:
            Dictionary with shadow Hamiltonian analysis
        """
        if verbose:
            print("=" * 70)
            print("SHADOW HAMILTONIAN ANALYSIS")
            print("=" * 70)

        # Integrate
        t_eval = np.linspace(0, t_max, 1000)

        try:
            sol = solve_ivp(
                lambda t, y: dynamics_func(t, y),
                [0, t_max],
                ic,
                t_eval=t_eval,
                method=self.integrator,
                rtol=self.rtol,
                atol=self.atol
            )

            if not sol.success:
                if verbose:
                    print("Integration failed")
                return {'success': False}

        except Exception as e:
            if verbose:
                print(f"Error: {e}")
            return {'success': False}

        # Evaluate energy along trajectory
        E_vals = np.array([hamiltonian_func(y) for y in sol.y.T])

        # Shadow Hamiltonian estimate: mean energy
        H_shadow = np.mean(E_vals)
        E_std = np.std(E_vals)

        # Check if energy oscillates around constant (bounded)
        is_bounded = self._check_bounded_drift(np.abs(E_vals - H_shadow), window=100)

        result = {
            'success': True,
            'H_shadow': H_shadow,
            'energy_std': E_std,
            'is_bounded': is_bounded,
            'energy_history': E_vals,
            'times': sol.t
        }

        if verbose:
            print(f"  Shadow Hamiltonian: {H_shadow:.6e}")
            print(f"  Energy std dev: {E_std:.2e}")
            if is_bounded:
                print("  ✓ Energy error BOUNDED (symplectic-like behavior)")
            else:
                print("  ✗ Energy error GROWING (may not be conservative)")
            print("=" * 70)

        return result

    def _check_bounded_drift(
        self,
        errors: np.ndarray,
        window: int = 100
    ) -> bool:
        """
        Check if error is bounded (not growing secularly).

        Compares error in first window vs last window.

        Args:
            errors: Array of errors over time
            window: Window size for comparison

        Returns:
            True if error is bounded
        """
        if len(errors) < 2 * window:
            return True  # Not enough data

        error_early = np.max(errors[:window])
        error_late = np.max(errors[-window:])

        # Growth factor
        growth_factor = error_late / (error_early + 1e-16)

        # If error grows by >10x, it's secular drift
        return growth_factor < 10.0

    def _failed_result(self) -> LongTimeResult:
        """Return a failed result."""
        return LongTimeResult(
            success=False,
            max_drift_I=np.inf,
            max_drift_E=np.inf,
            drift_ratio=np.inf,
            drift_I_rate=np.inf,
            drift_E_rate=np.inf,
            is_bounded=False,
            integration_time=0.0,
            n_checkpoints=0,
            times=np.array([]),
            drift_I_history=np.array([]),
            drift_E_history=np.array([])
        )
