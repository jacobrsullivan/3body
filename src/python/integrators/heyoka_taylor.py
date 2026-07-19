"""
High-precision CR3BP integration using heyoka's Taylor method.

This integrator is intended for bounded Tier 2 validation smoke runs. It uses
heyoka.real arithmetic for the integration and for Jacobi-drift measurement,
then returns float arrays for compatibility with the existing WP1 artifact
format. The high-precision drift evidence is stored in result.stats.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np

from .base import IntegrationResult, IntegratorBase
from ..utils.coordinates import corotating_to_inertial

try:
    import heyoka as hy
except ImportError:  # pragma: no cover - exercised only when env is incomplete.
    hy = None


logger = logging.getLogger(__name__)


class HeyokaTaylorIntegrator(IntegratorBase):
    """Arbitrary-precision Taylor integrator for CR3BP Tier 2 smoke checks."""

    def __init__(
        self,
        mu: float,
        tolerance: float = 1e-25,
        precision_bits: int = 160,
        high_accuracy: bool = True,
        compact_mode: bool = True,
        preserve_high_precision_states: bool = False,
        **kwargs: Any,
    ):
        if hy is None:
            raise ImportError(
                "heyoka.py is required for HeyokaTaylorIntegrator. "
                "Install heyoka.py in the WP1 environment."
            )

        super().__init__(mu, tolerance=tolerance, **kwargs)
        self.precision_bits = int(precision_bits)
        self.high_accuracy = high_accuracy
        self.compact_mode = compact_mode
        self.preserve_high_precision_states = bool(preserve_high_precision_states)
        self._is_symplectic = False
        self._system = self._build_system()

    def _real(self, value: Any):
        return hy.real(str(value), self.precision_bits)

    def _real_from_float(self, value: float):
        return hy.real(repr(float(value)), self.precision_bits)

    def _build_system(self):
        x, y, z, vx, vy, vz = hy.make_vars("x", "y", "z", "vx", "vy", "vz")
        mu = self._real(self.mu)
        one = self._real("1")
        two = self._real("2")

        r1_sq = (x + mu) * (x + mu) + y * y + z * z
        r2_sq = (x - one + mu) * (x - one + mu) + y * y + z * z
        r1 = hy.sqrt(r1_sq)
        r2 = hy.sqrt(r2_sq)
        r1_cubed = r1_sq * r1
        r2_cubed = r2_sq * r2

        ax = (
            two * vy
            + x
            - (one - mu) * (x + mu) / r1_cubed
            - mu * (x - one + mu) / r2_cubed
        )
        ay = -two * vx + y - (one - mu) * y / r1_cubed - mu * y / r2_cubed
        az = -(one - mu) * z / r1_cubed - mu * z / r2_cubed

        return [(x, vx), (y, vy), (z, vz), (vx, ax), (vy, ay), (vz, az)]

    def _jacobi_constant_real(self, state: List[Any]):
        x, y, z, vx, vy, vz = state
        mu = self._real(self.mu)
        one = self._real("1")
        two = self._real("2")
        half = self._real("0.5")

        r1 = ((x + mu) * (x + mu) + y * y + z * z) ** half
        r2 = ((x - one + mu) * (x - one + mu) + y * y + z * z) ** half

        return (
            x * x
            + y * y
            + two * (one - mu) / r1
            + two * mu / r2
            - (vx * vx + vy * vy + vz * vz)
        )

    def _make_output_times(self, duration: float, output_interval: float) -> List[float]:
        targets: List[float] = []
        target = output_interval
        tol = max(abs(duration), abs(output_interval), 1.0) * 1e-14

        while target < duration - tol:
            targets.append(float(target))
            target += output_interval

        targets.append(float(duration))
        return targets

    def _integrate_internal(
        self,
        initial_state: np.ndarray,
        duration: float,
        output_interval: float,
    ) -> IntegrationResult:
        state_real = [self._real_from_float(value) for value in initial_state]
        tolerance_real = self._real(f"{self.tolerance:.17e}")

        try:
            integrator = hy.taylor_adaptive_real(
                self._system,
                state_real,
                tol=tolerance_real,
                high_accuracy=self.high_accuracy,
                compact_mode=self.compact_mode,
                prec=self.precision_bits,
            )
        except Exception as exc:
            return IntegrationResult(
                times=np.array([0.0]),
                states_corotating=initial_state.reshape(1, 6),
                states_inertial=np.array([corotating_to_inertial(initial_state, 0.0)]),
                success=False,
                message=f"heyoka Taylor setup failed: {exc}",
                stats={"error": str(exc), "precision_backend": "heyoka.real"},
            )

        c_initial = self._jacobi_constant_real(list(integrator.state))

        times = [0.0]
        states_corotating = [initial_state.astype(float).copy()]
        states_inertial = [corotating_to_inertial(initial_state, 0.0)]
        states_high_precision = (
            [[str(value) for value in integrator.state]]
            if self.preserve_high_precision_states
            else None
        )
        times_high_precision = [str(integrator.time)] if states_high_precision else None
        outcomes = []
        total_steps = 0

        for target in self._make_output_times(duration, output_interval):
            outcome = integrator.propagate_until(self._real_from_float(target))
            outcomes.append(str(outcome[0]))
            if len(outcome) > 3:
                total_steps += int(outcome[3])

            if float(integrator.time) + 1e-12 < target:
                break

            state_float = np.array([float(value) for value in integrator.state])
            times.append(float(target))
            states_corotating.append(state_float)
            states_inertial.append(corotating_to_inertial(state_float, target))
            if states_high_precision is not None and times_high_precision is not None:
                states_high_precision.append([str(value) for value in integrator.state])
                times_high_precision.append(str(integrator.time))

        c_final = self._jacobi_constant_real(list(integrator.state))
        relative_drift = abs((c_final - c_initial) / c_initial)
        relative_drift_float = float(relative_drift)
        final_time = float(integrator.time)
        success = final_time + 1e-12 >= duration and relative_drift_float < self.tolerance

        stats: Dict[str, Any] = {
            "precision_backend": "heyoka.real",
            "precision_bits": self.precision_bits,
            "requested_tolerance": self.tolerance,
            "jacobi_initial": str(c_initial),
            "jacobi_final": str(c_final),
            "jacobi_relative_drift": str(relative_drift),
            "jacobi_relative_drift_float": relative_drift_float,
            "final_time": final_time,
            "total_steps": total_steps,
            "outcomes": outcomes,
        }
        if states_high_precision is not None and times_high_precision is not None:
            stats["states_corotating_high_precision"] = states_high_precision
            stats["times_high_precision"] = times_high_precision

        message = (
            "heyoka Taylor integration completed"
            if success
            else "heyoka Taylor integration failed Tier 2 precision criteria"
        )

        return IntegrationResult(
            times=np.array(times),
            states_corotating=np.array(states_corotating),
            states_inertial=np.array(states_inertial),
            success=success,
            message=message,
            stats=stats,
        )

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info.update(
            {
                "backend": "heyoka.real",
                "precision_bits": self.precision_bits,
                "order": "adaptive Taylor",
                "high_accuracy": self.high_accuracy,
                "compact_mode": self.compact_mode,
                "preserve_high_precision_states": self.preserve_high_precision_states,
            }
        )
        return info
