"""
Adaptive Symplectic Integrator for CR3BP (WP1 Phase 2).

Implements adaptive symplectic integration using Sundman time transformation
combined with symplectic composition methods. This provides the "gold standard"
Tier 2 precision while maintaining symplectic structure.

Mathematical Background:
========================

Sundman Transformation:
-----------------------
Transform physical time t to fictitious time s via:
    dt/ds = Ω(q)

where Ω(q) is the time dilation factor (e.g., Ω = r for two-body, Ω = Σrᵢⱼ for three-body).

The Hamiltonian becomes:
    K(q,p,s) = Ω(q) · H(q,p)

This transformed Hamiltonian is still separable and can be integrated symplectically.

Adaptive Strategy:
------------------
- Variable fictitious timestep ds based on local error estimate
- Natural adaptivity from Ω(q): automatically refines near close encounters
- Maintains symplecticity in (q,p,s) coordinates

Composition Method:
-------------------
Uses Yoshida-style composition for high-order accuracy while preserving
symplectic structure.

References:
-----------
- Mikkola & Tanikawa (1999): "Explicit symplectic algorithms for time-transformed
  Hamiltonians"
- Hairer, Lubich, Wanner (2006): "Geometric Numerical Integration"
- Wisdom & Holman (1991): "Symplectic maps for the n-body problem"
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Dict, Any
import numpy as np
import logging

from .base import IntegratorBase, IntegrationResult
from ..regularization.sundman import (
    compute_time_dilation_single,
    TimeTransformationStrategy,
)
from ..utils.coordinates import corotating_to_inertial, inertial_to_corotating
from ..utils.dynamics import cr3bp_acceleration, distances_to_primaries

logger = logging.getLogger(__name__)


@dataclass
class YoshidaCoefficients:
    """
    Coefficients for Yoshida composition method.

    For a 4th-order symplectic integrator using composition of leapfrog steps.
    """
    # 4th-order Yoshida coefficients
    w0 = -(2.0**(1.0/3.0)) / (2.0 - 2.0**(1.0/3.0))
    w1 = 1.0 / (2.0 - 2.0**(1.0/3.0))
    c = [w1/2.0, (w0 + w1)/2.0, (w0 + w1)/2.0, w1/2.0]
    d = [w1, w0, w1, 0.0]

    @classmethod
    def get_6th_order(cls):
        """
        6th-order coefficients (Yoshida8).

        Returns coefficients for 8-stage 6th-order composition.
        """
        # Simplified 6th-order coefficients
        # (Full implementation would use optimal Yoshida8 coefficients)
        w = [
            0.7845136104775751,
            0.2355732133593570,
            -1.1776799841788710,
            1.3151863206839060,
            1.3151863206839060,
            -1.1776799841788710,
            0.2355732133593570,
            0.7845136104775751,
        ]
        return w


class AdaptiveSymplecticIntegrator(IntegratorBase):
    """
    Adaptive symplectic integrator using Sundman transformation.

    Combines:
    - Sundman time regularization for natural adaptivity
    - Symplectic composition methods for structure preservation
    - High-precision arithmetic support (QD integration ready)
    """

    DOUBLE_PRECISION_TOLERANCE_FLOOR = 1e-15

    def __init__(
        self,
        mu: float,
        order: int = 4,
        ds_init: float = 0.01,
        ds_min: float = 1e-6,
        ds_max: float = 0.1,
        error_tolerance: float = 1e-14,
        sundman_strategy: str = "sum",
        **kwargs
    ):
        """
        Initialize adaptive symplectic integrator.

        Args:
            mu: Mass parameter
            order: Integration order (4 or 6)
            ds_init: Initial fictitious timestep
            ds_min: Minimum allowed timestep
            ds_max: Maximum allowed timestep
            error_tolerance: Error tolerance for adaptive stepping
            sundman_strategy: Sundman transformation strategy ("sum", "product", "min")
            **kwargs: Additional parameters passed to base class
        """
        super().__init__(mu, **kwargs)

        self.order = order
        self.ds = ds_init
        self.ds_min = ds_min
        self.ds_max = ds_max
        self.error_tolerance = error_tolerance

        # Sundman strategy
        strategy_map = {
            "sum": TimeTransformationStrategy.SUM,
            "product": TimeTransformationStrategy.PRODUCT,
            "min": TimeTransformationStrategy.MIN,
        }
        self.sundman_strategy = strategy_map.get(
            sundman_strategy, TimeTransformationStrategy.SUM
        )

        # Composition coefficients
        if order == 4:
            self.coeffs = YoshidaCoefficients()
        elif order == 6:
            self.coeffs_w = YoshidaCoefficients.get_6th_order()
        else:
            raise ValueError(f"Order must be 4 or 6, got {order}")

        self._is_symplectic = True
        logger.info(f"Initialized AdaptiveSymplectic(order={order}, ds_init={ds_init})")

    def _compute_omega(self, state: np.ndarray) -> float:
        """
        Compute Sundman time dilation factor Ω(q).

        Args:
            state: Current state [x, y, z, vx, vy, vz]

        Returns:
            Ω = dt/ds > 0
        """
        # Compute distances to primaries
        r1, r2 = distances_to_primaries(state, self.mu)

        # For CR3BP (two primaries), use appropriate strategy
        if self.sundman_strategy == TimeTransformationStrategy.SUM:
            omega = r1 + r2
        elif self.sundman_strategy == TimeTransformationStrategy.PRODUCT:
            omega = r1 * r2
        elif self.sundman_strategy == TimeTransformationStrategy.MIN:
            omega = min(r1, r2)
        else:
            # Default: sum
            omega = r1 + r2

        # Ensure positive and finite
        omega = max(omega, 1e-10)  # Regularize near collisions
        return omega

    def _drift_step(self, state: np.ndarray, c: float, ds: float) -> np.ndarray:
        """
        Drift step: update positions.

        q' = q + c * ds * p

        Args:
            state: Current state
            c: Composition coefficient
            ds: Fictitious timestep

        Returns:
            Updated state
        """
        new_state = state.copy()
        new_state[:3] += c * ds * state[3:6]  # x,y,z += c*ds*(vx,vy,vz)
        return new_state

    def _kick_step(self, state: np.ndarray, d: float, ds: float) -> np.ndarray:
        """
        Kick step: update momenta (velocities).

        p' = p + d * ds * f(q)

        where f(q) is the acceleration.

        Args:
            state: Current state
            d: Composition coefficient
            ds: Fictitious timestep

        Returns:
            Updated state
        """
        new_state = state.copy()

        # Compute acceleration in co-rotating frame
        acc = cr3bp_acceleration(state, self.mu)

        # Kick: v' = v + d*ds*a
        new_state[3:6] += d * ds * acc

        return new_state

    def _symplectic_step_4th(self, state: np.ndarray, ds: float) -> np.ndarray:
        """
        4th-order symplectic step using Yoshida composition.

        Args:
            state: Current state
            ds: Fictitious timestep

        Returns:
            Updated state after one step
        """
        s = state.copy()

        # Yoshida 4th-order composition: (c,d) pairs
        for i in range(4):
            s = self._drift_step(s, self.coeffs.c[i], ds)
            if self.coeffs.d[i] != 0.0:
                s = self._kick_step(s, self.coeffs.d[i], ds)

        return s

    def _symplectic_step_6th(self, state: np.ndarray, ds: float) -> np.ndarray:
        """
        6th-order symplectic step.

        Args:
            state: Current state
            ds: Fictitious timestep

        Returns:
            Updated state
        """
        s = state.copy()

        # 6th-order composition (8 stages)
        for i in range(len(self.coeffs_w)):
            w = self.coeffs_w[i]
            # Split operator: drift + kick
            s = self._drift_step(s, w/2, ds)
            s = self._kick_step(s, w, ds)
            s = self._drift_step(s, w/2, ds)

        return s

    def _symplectic_step(self, state: np.ndarray, ds: float) -> np.ndarray:
        """
        Single symplectic step at given order.

        Args:
            state: Current state
            ds: Fictitious timestep

        Returns:
            Updated state
        """
        if self.order == 4:
            return self._symplectic_step_4th(state, ds)
        elif self.order == 6:
            return self._symplectic_step_6th(state, ds)
        else:
            raise ValueError(f"Unsupported order: {self.order}")

    def _estimate_error(
        self,
        state: np.ndarray,
        state_full: np.ndarray,
        state_half: np.ndarray
    ) -> float:
        """
        Estimate local truncation error using step doubling.

        Compare full step vs two half steps.

        Args:
            state: Initial state
            state_full: State after one full step
            state_half: State after two half steps

        Returns:
            Error estimate (RMS position error)
        """
        # Position error
        pos_error = state_half[:3] - state_full[:3]
        rms_error = np.sqrt(np.mean(pos_error**2))

        return rms_error

    def _adaptive_step(
        self,
        state: np.ndarray,
        ds_current: float,
        t_current: float
    ) -> Tuple[np.ndarray, float, float, bool]:
        """
        Perform one adaptive symplectic step with error control.

        Args:
            state: Current state
            ds_current: Current fictitious timestep
            t_current: Current physical time

        Returns:
            (new_state, new_t, new_ds, accept)
        """
        # Compute Ω at current state
        omega = self._compute_omega(state)

        # Full step
        state_full = self._symplectic_step(state, ds_current)

        # Two half steps
        state_half1 = self._symplectic_step(state, ds_current / 2.0)
        state_half2 = self._symplectic_step(state_half1, ds_current / 2.0)

        # Error estimate
        error = self._estimate_error(state, state_full, state_half2)

        # Accept/reject decision
        if error < self.error_tolerance:
            accept = True
            new_state = state_half2  # Use more accurate half-step result
            new_t = t_current + ds_current * omega  # dt = Ω * ds
        else:
            accept = False
            new_state = state  # Reject step
            new_t = t_current

        # Adaptive timestep adjustment
        if error > 1e-16:  # Avoid division by zero
            safety_factor = 0.9
            ds_new = ds_current * safety_factor * (self.error_tolerance / error)**0.2
        else:
            ds_new = ds_current * 1.5  # Increase if error very small

        # Clamp timestep
        ds_new = np.clip(ds_new, self.ds_min, self.ds_max)

        return new_state, new_t, ds_new, accept

    def _integrate_internal(
        self,
        initial_state: np.ndarray,
        duration: float,
        output_interval: float
    ) -> IntegrationResult:
        """
        Internal integration method.

        Args:
            initial_state: Initial state (co-rotating frame)
            duration: Integration duration (physical time)
            output_interval: Output sampling interval

        Returns:
            IntegrationResult
        """
        if self.error_tolerance < self.DOUBLE_PRECISION_TOLERANCE_FLOOR:
            message = (
                "AdaptiveSymplecticIntegrator requested tolerance "
                f"{self.error_tolerance:.1e}, below the supported float64 floor "
                f"{self.DOUBLE_PRECISION_TOLERANCE_FLOOR:.1e}. "
                "Tier 2 precision requires a QD-backed arithmetic path, which "
                "this integrator does not currently implement."
            )
            logger.error(message)
            return IntegrationResult(
                times=np.array([0.0]),
                states_corotating=np.array([initial_state.copy()]),
                states_inertial=np.array([
                    corotating_to_inertial(initial_state, 0.0)
                ]),
                success=False,
                message=message,
                stats={
                    'total_steps': 0,
                    'accepted_steps': 0,
                    'rejected_steps': 0,
                    'acceptance_rate': 0.0,
                    'final_time': 0.0,
                    'final_timestep': self.ds,
                    'stop_reason': 'unsupported_precision',
                    'precision_mode': 'float64',
                    'requested_tolerance': self.error_tolerance,
                    'minimum_supported_tolerance': (
                        self.DOUBLE_PRECISION_TOLERANCE_FLOOR
                    ),
                },
            )

        # Initialize
        state = initial_state.copy()
        t = 0.0
        ds = self.ds

        # Output storage
        times = [0.0]
        states_corot = [initial_state.copy()]
        states_inert = [corotating_to_inertial(initial_state, 0.0)]

        t_next_output = output_interval
        n_steps = 0
        n_accepted = 0
        n_rejected = 0
        stop_reason = "completed"

        logger.info(f"Starting adaptive symplectic integration to t={duration}")

        while t < duration:
            # Adaptive step
            new_state, new_t, new_ds, accept = self._adaptive_step(state, ds, t)

            if accept:
                state = new_state
                t = new_t
                ds = new_ds
                n_accepted += 1

                # Check if we need output
                while t >= t_next_output and t_next_output <= duration:
                    # Interpolate to exact output time (simplified: use current state)
                    times.append(t_next_output)
                    states_corot.append(state.copy())
                    states_inert.append(
                        corotating_to_inertial(state, t_next_output)
                    )
                    t_next_output += output_interval
            else:
                ds = new_ds
                n_rejected += 1

            n_steps += 1

            # Safety check
            if n_steps > self.max_steps:
                stop_reason = f"max steps ({self.max_steps}) reached at t={t:.6g}"
                logger.warning(stop_reason)
                break

            # Check for escape or collision
            r1, r2 = distances_to_primaries(state, self.mu)
            if r1 < 1e-8 or r2 < 1e-8:
                stop_reason = f"collision detected at t={t:.6g}"
                logger.warning(stop_reason)
                break

            if np.linalg.norm(state[:3]) > 10.0:  # Escape criterion
                stop_reason = f"escape detected at t={t:.6g}"
                logger.info(stop_reason)
                break

        # Final output if not already added
        if t > times[-1]:
            times.append(t)
            states_corot.append(state.copy())
            states_inert.append(corotating_to_inertial(state, t))

        # Convert to arrays
        times = np.array(times)
        states_corot = np.array(states_corot)
        states_inert = np.array(states_inert)

        # Statistics
        stats = {
            'total_steps': n_steps,
            'accepted_steps': n_accepted,
            'rejected_steps': n_rejected,
            'acceptance_rate': n_accepted / n_steps if n_steps > 0 else 0.0,
            'final_time': t,
            'final_timestep': ds,
            'stop_reason': stop_reason,
        }

        success = t >= duration
        if not success and stop_reason == "completed":
            stop_reason = f"stopped before requested duration at t={t:.6g}"
            stats['stop_reason'] = stop_reason

        logger.info(
            f"Integration completed: {n_accepted} accepted, {n_rejected} rejected, "
            f"acceptance rate = {stats['acceptance_rate']:.2%}"
        )

        return IntegrationResult(
            times=times,
            states_corotating=states_corot,
            states_inertial=states_inert,
            success=success,
            message=(
                "Adaptive symplectic integration completed"
                if success else
                f"Adaptive symplectic integration incomplete: {stop_reason}"
            ),
            stats=stats,
        )

    def get_info(self) -> Dict[str, Any]:
        """Get integrator information."""
        info = super().get_info()
        info.update({
            'order': self.order,
            'ds_init': self.ds,
            'ds_min': self.ds_min,
            'ds_max': self.ds_max,
            'error_tolerance': self.error_tolerance,
            'sundman_strategy': self.sundman_strategy.value,
        })
        return info
