"""
Chaos Indicators for CR3BP Trajectory Analysis (WP1).

This module implements MEGNO (Mean Exponential Growth of Nearby Orbits)
and FLI (Fast Lyapunov Indicator) for distinguishing regular vs chaotic
motion in the Circular Restricted Three-Body Problem.

Mathematical Background:
========================

MEGNO (Cincotta & Simó, 2000):
-------------------------------
MEGNO is a sensitive chaos indicator that converges to:
- MEGNO ≈ 2.0 for regular (quasi-periodic) motion
- MEGNO → ∞ (grows logarithmically) for chaotic motion

Definition:
    MEGNO(t) = (2/t) ∫₀ᵗ δ(s)/||δ(s)|| · d||δ(s)||/ds · s ds

where δ(t) is the deviation vector evolving via variational equations.

FLI (Fast Lyapunov Indicator):
-------------------------------
FLI measures the maximum growth of tangent vectors:
    FLI(t) = log₁₀(||δ(t)||)

Classification:
- FLI < 2-3: Regular motion
- FLI > 4-5: Chaotic motion (for t = 10⁴ periods)

References:
-----------
- Cincotta, P. M., & Simó, C. (2000). Simple tools to study global dynamics
  in non-axisymmetric galactic potentials. A&AS, 147, 205-228.
- Lega, E., Guzzo, M., & Froeschlé, C. (2016). Theory and applications of
  the Fast Lyapunov Indicator (FLI) method. LNP, 915, 35-54.
- Rein, H., & Tamayo, D. (2015). WHFAST: a fast and unbiased implementation
  of a symplectic Wisdom-Holman integrator for long-term gravitational
  simulations. MNRAS, 452, 376-388.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Dict, Any
import numpy as np
from scipy.integrate import ode, solve_ivp
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChaosIndicatorResult:
    """
    Results from chaos indicator computation.

    Attributes:
        times: Time points where indicators were computed
        megno: MEGNO values at each time point
        fli: FLI values at each time point
        mean_megno: Time-averaged MEGNO (for classification)
        final_fli: Final FLI value (for classification)
        classification: 'regular' or 'chaotic' based on indicators
        deviation_norm: Norm of deviation vector ||δ(t)||
        metadata: Additional computation metadata
    """
    times: np.ndarray
    megno: np.ndarray
    fli: np.ndarray
    mean_megno: float
    final_fli: float
    classification: str
    deviation_norm: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)


class MEGNOIndicator:
    """
    MEGNO (Mean Exponential Growth of Nearby Orbits) implementation.

    Integrates the deviation vector and accumulates the time-weighted
    integral to compute MEGNO indicator for chaos detection.
    """

    def __init__(
        self,
        dynamics_function: Callable[[float, np.ndarray], np.ndarray],
        jacobian_function: Optional[Callable[[float, np.ndarray], np.ndarray]] = None,
        normalization_interval: float = 1.0
    ):
        """
        Initialize MEGNO indicator.

        Args:
            dynamics_function: f(t, y) → dy/dt for the reference orbit
            jacobian_function: J(t, y) → Jacobian matrix for variational eq.
                              If None, will use numerical differentiation
            normalization_interval: Time interval for renormalizing deviation vector
        """
        self.dynamics = dynamics_function
        self.jacobian = jacobian_function
        self.normalization_interval = normalization_interval

        # Will be set during computation
        self._dim = None
        self._t_last_norm = 0.0
        self._cumulative_megno_integral = 0.0

    def _numerical_jacobian(self, t: float, state: np.ndarray, eps: float = 1e-7) -> np.ndarray:
        """
        Compute Jacobian numerically via finite differences.

        Args:
            t: Time
            state: Current state
            eps: Finite difference step

        Returns:
            Jacobian matrix (dim, dim)
        """
        dim = len(state)
        jac = np.zeros((dim, dim))
        f0 = self.dynamics(t, state)

        for i in range(dim):
            state_plus = state.copy()
            state_plus[i] += eps
            f_plus = self.dynamics(t, state_plus)
            jac[:, i] = (f_plus - f0) / eps

        return jac

    def _variational_rhs(
        self,
        t: float,
        combined_state: np.ndarray
    ) -> np.ndarray:
        """
        Combined RHS for reference orbit + deviation vector + MEGNO accumulation.

        State vector structure:
        combined_state = [y (reference), δ (deviation), Y (MEGNO integral), W (weighted integral)]

        Args:
            t: Current time
            combined_state: Combined state vector

        Returns:
            Time derivative of combined state
        """
        # Extract components
        y = combined_state[:self._dim]  # Reference orbit
        delta = combined_state[self._dim:2*self._dim]  # Deviation vector
        Y = combined_state[2*self._dim]  # MEGNO integral accumulator
        W = combined_state[2*self._dim + 1]  # Weighted integral accumulator

        # Reference orbit dynamics
        dy_dt = self.dynamics(t, y)

        # Variational equation: d(δ)/dt = J(y) · δ
        if self.jacobian is not None:
            jac = self.jacobian(t, y)
        else:
            jac = self._numerical_jacobian(t, y)

        ddelta_dt = jac @ delta

        # MEGNO accumulation
        delta_norm = np.linalg.norm(delta)
        delta_dot_norm = np.linalg.norm(ddelta_dt)

        if delta_norm > 1e-15:  # Avoid division by zero
            # d(||δ||)/dt ≈ (δ · d(δ)/dt) / ||δ||
            d_norm_dt = np.dot(delta, ddelta_dt) / delta_norm

            # MEGNO integrand: (δ/||δ||) · d||δ||/dt
            megno_integrand = d_norm_dt / delta_norm

            # Weighted integral: ∫ megno_integrand · t dt
            dW_dt = megno_integrand * t
            dY_dt = 0.0  # Y is just a counter (not needed for this formulation)
        else:
            dW_dt = 0.0
            dY_dt = 0.0

        # Combine derivatives
        dcombined_dt = np.zeros_like(combined_state)
        dcombined_dt[:self._dim] = dy_dt
        dcombined_dt[self._dim:2*self._dim] = ddelta_dt
        dcombined_dt[2*self._dim] = dY_dt
        dcombined_dt[2*self._dim + 1] = dW_dt

        return dcombined_dt

    def compute(
        self,
        initial_state: np.ndarray,
        t_final: float,
        output_interval: float = 1.0,
        initial_deviation: Optional[np.ndarray] = None,
        **integrator_kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute MEGNO indicator along trajectory.

        Args:
            initial_state: Initial condition for reference orbit
            t_final: Final integration time
            output_interval: Time interval for output
            initial_deviation: Initial deviation vector (random if None)
            **integrator_kwargs: Additional arguments for scipy integrator

        Returns:
            Tuple of (times, megno_values, deviation_norms)
        """
        self._dim = len(initial_state)

        # Initialize deviation vector (small random perturbation)
        if initial_deviation is None:
            np.random.seed(42)  # Reproducibility
            initial_deviation = 1e-10 * np.random.randn(self._dim)
            initial_deviation /= np.linalg.norm(initial_deviation)  # Normalize

        # Combined initial condition
        # [reference, deviation, Y_accumulator, W_accumulator]
        combined_initial = np.zeros(2 * self._dim + 2)
        combined_initial[:self._dim] = initial_state
        combined_initial[self._dim:2*self._dim] = initial_deviation
        combined_initial[2*self._dim] = 0.0  # Y
        combined_initial[2*self._dim + 1] = 0.0  # W

        # Integration times
        t_eval = np.arange(0, t_final + output_interval, output_interval)

        # Set up integrator defaults
        defaults = {
            'method': 'DOP853',
            'rtol': 1e-12,
            'atol': 1e-14,
            'dense_output': False
        }
        defaults.update(integrator_kwargs)

        # Integrate
        logger.info(f"Computing MEGNO for {t_final} time units...")
        sol = solve_ivp(
            self._variational_rhs,
            (0, t_final),
            combined_initial,
            t_eval=t_eval,
            **defaults
        )

        if not sol.success:
            raise RuntimeError(f"MEGNO integration failed: {sol.message}")

        # Extract results
        times = sol.t
        W_values = sol.y[2*self._dim + 1, :]  # Weighted integral
        deviation_norms = np.linalg.norm(sol.y[self._dim:2*self._dim, :], axis=0)

        # Compute MEGNO: (2/t) * W(t)
        megno = np.zeros_like(times)
        for i, t in enumerate(times):
            if t > 1e-10:  # Avoid division by zero
                megno[i] = (2.0 / t) * W_values[i]
            else:
                megno[i] = 0.0

        return times, megno, deviation_norms


class FLIIndicator:
    """
    FLI (Fast Lyapunov Indicator) implementation.

    Tracks the logarithmic growth of deviation vectors for
    rapid chaos detection.
    """

    def __init__(
        self,
        dynamics_function: Callable[[float, np.ndarray], np.ndarray],
        jacobian_function: Optional[Callable[[float, np.ndarray], np.ndarray]] = None
    ):
        """
        Initialize FLI indicator.

        Args:
            dynamics_function: f(t, y) → dy/dt for the reference orbit
            jacobian_function: J(t, y) → Jacobian matrix for variational eq.
        """
        self.dynamics = dynamics_function
        self.jacobian = jacobian_function
        self._dim = None

    def _numerical_jacobian(self, t: float, state: np.ndarray, eps: float = 1e-7) -> np.ndarray:
        """Compute Jacobian numerically."""
        dim = len(state)
        jac = np.zeros((dim, dim))
        f0 = self.dynamics(t, state)

        for i in range(dim):
            state_plus = state.copy()
            state_plus[i] += eps
            f_plus = self.dynamics(t, state_plus)
            jac[:, i] = (f_plus - f0) / eps

        return jac

    def _variational_rhs(self, t: float, combined_state: np.ndarray) -> np.ndarray:
        """
        Combined RHS for reference orbit + deviation vector.

        Args:
            t: Current time
            combined_state: [reference_state, deviation_vector]

        Returns:
            Time derivative
        """
        # Extract components
        y = combined_state[:self._dim]
        delta = combined_state[self._dim:]

        # Reference orbit
        dy_dt = self.dynamics(t, y)

        # Variational equation
        if self.jacobian is not None:
            jac = self.jacobian(t, y)
        else:
            jac = self._numerical_jacobian(t, y)

        ddelta_dt = jac @ delta

        return np.concatenate([dy_dt, ddelta_dt])

    def compute(
        self,
        initial_state: np.ndarray,
        t_final: float,
        output_interval: float = 1.0,
        initial_deviation: Optional[np.ndarray] = None,
        **integrator_kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute FLI indicator along trajectory.

        Args:
            initial_state: Initial condition for reference orbit
            t_final: Final integration time
            output_interval: Time interval for output
            initial_deviation: Initial deviation vector (random if None)
            **integrator_kwargs: Additional arguments for scipy integrator

        Returns:
            Tuple of (times, fli_values, deviation_norms)
        """
        self._dim = len(initial_state)

        # Initialize deviation vector
        if initial_deviation is None:
            np.random.seed(42)
            initial_deviation = 1e-10 * np.random.randn(self._dim)
            initial_deviation /= np.linalg.norm(initial_deviation)

        # Combined initial condition
        combined_initial = np.concatenate([initial_state, initial_deviation])

        # Integration times
        t_eval = np.arange(0, t_final + output_interval, output_interval)

        # Integrator defaults
        defaults = {
            'method': 'DOP853',
            'rtol': 1e-12,
            'atol': 1e-14
        }
        defaults.update(integrator_kwargs)

        # Integrate
        logger.info(f"Computing FLI for {t_final} time units...")
        sol = solve_ivp(
            self._variational_rhs,
            (0, t_final),
            combined_initial,
            t_eval=t_eval,
            **defaults
        )

        if not sol.success:
            raise RuntimeError(f"FLI integration failed: {sol.message}")

        # Extract results
        times = sol.t
        deviation_norms = np.linalg.norm(sol.y[self._dim:, :], axis=0)

        # Compute FLI: log₁₀(||δ(t)||)
        fli = np.log10(deviation_norms + 1e-300)  # Avoid log(0)

        return times, fli, deviation_norms


class ChaosAnalyzer:
    """
    Unified chaos analysis using both MEGNO and FLI.

    Provides high-level interface for chaos detection and classification.
    """

    def __init__(
        self,
        dynamics_function: Callable[[float, np.ndarray], np.ndarray],
        jacobian_function: Optional[Callable[[float, np.ndarray], np.ndarray]] = None,
        megno_threshold: float = 2.5,
        fli_threshold: float = 3.0
    ):
        """
        Initialize chaos analyzer.

        Args:
            dynamics_function: System dynamics f(t, y) → dy/dt
            jacobian_function: Optional Jacobian function
            megno_threshold: MEGNO threshold for chaos (default: 2.5)
            fli_threshold: FLI threshold for chaos (default: 3.0)
        """
        self.megno_indicator = MEGNOIndicator(dynamics_function, jacobian_function)
        self.fli_indicator = FLIIndicator(dynamics_function, jacobian_function)

        self.megno_threshold = megno_threshold
        self.fli_threshold = fli_threshold

    def analyze(
        self,
        initial_state: np.ndarray,
        t_final: float,
        output_interval: float = 1.0,
        compute_both: bool = True,
        **integrator_kwargs
    ) -> ChaosIndicatorResult:
        """
        Perform complete chaos analysis on trajectory.

        Args:
            initial_state: Initial condition
            t_final: Integration time
            output_interval: Output sampling interval
            compute_both: If True, compute both MEGNO and FLI
            **integrator_kwargs: Integration parameters

        Returns:
            ChaosIndicatorResult with classification and indicators
        """
        # Compute MEGNO
        times_megno, megno, dev_norm_megno = self.megno_indicator.compute(
            initial_state, t_final, output_interval, **integrator_kwargs
        )

        # Compute FLI (use same initial deviation for consistency)
        if compute_both:
            times_fli, fli, dev_norm_fli = self.fli_indicator.compute(
                initial_state, t_final, output_interval, **integrator_kwargs
            )
        else:
            # FLI can be computed from deviation norm
            times_fli = times_megno
            dev_norm_fli = dev_norm_megno
            fli = np.log10(dev_norm_fli + 1e-300)

        # Compute time-averaged MEGNO (last 20% of integration)
        start_idx = int(0.8 * len(megno))
        mean_megno = np.mean(megno[start_idx:])

        # Final FLI value
        final_fli = fli[-1]

        # Classification
        megno_chaotic = mean_megno > self.megno_threshold
        fli_chaotic = final_fli > self.fli_threshold

        if megno_chaotic or fli_chaotic:
            classification = 'chaotic'
        else:
            classification = 'regular'

        # Metadata
        metadata = {
            'megno_threshold': self.megno_threshold,
            'fli_threshold': self.fli_threshold,
            'megno_chaotic': megno_chaotic,
            'fli_chaotic': fli_chaotic,
            'agreement': megno_chaotic == fli_chaotic
        }

        return ChaosIndicatorResult(
            times=times_megno,
            megno=megno,
            fli=fli,
            mean_megno=mean_megno,
            final_fli=final_fli,
            classification=classification,
            deviation_norm=dev_norm_megno,
            metadata=metadata
        )

    def classify_orbit(
        self,
        initial_state: np.ndarray,
        t_final: float = 1000.0,
        **kwargs
    ) -> str:
        """
        Quick classification: regular or chaotic.

        Args:
            initial_state: Initial condition
            t_final: Integration time (default: 1000 periods)
            **kwargs: Additional parameters

        Returns:
            Classification string: 'regular' or 'chaotic'
        """
        result = self.analyze(initial_state, t_final, **kwargs)
        return result.classification


# Convenience functions for CR3BP


def cr3bp_dynamics_wrapper(mu: float) -> Callable[[float, np.ndarray], np.ndarray]:
    """
    Create CR3BP dynamics function for chaos indicators.

    Args:
        mu: Mass parameter

    Returns:
        Dynamics function f(t, state) → dstate/dt
    """
    from ..utils.dynamics import cr3bp_acceleration

    def dynamics(t: float, state: np.ndarray) -> np.ndarray:
        """CR3BP equations of motion in co-rotating frame."""
        if len(state) != 6:
            raise ValueError("State must be 6-dimensional [x, y, z, vx, vy, vz]")

        # Acceleration
        acc = cr3bp_acceleration(state, mu)

        # Return [velocity, acceleration]
        return np.concatenate([state[3:6], acc])

    return dynamics


def create_cr3bp_chaos_analyzer(
    mu: float,
    megno_threshold: float = 2.5,
    fli_threshold: float = 3.0
) -> ChaosAnalyzer:
    """
    Create chaos analyzer for CR3BP.

    Args:
        mu: Mass parameter
        megno_threshold: MEGNO classification threshold
        fli_threshold: FLI classification threshold

    Returns:
        ChaosAnalyzer configured for CR3BP
    """
    dynamics = cr3bp_dynamics_wrapper(mu)
    return ChaosAnalyzer(
        dynamics,
        jacobian_function=None,  # Will use numerical differentiation
        megno_threshold=megno_threshold,
        fli_threshold=fli_threshold
    )
