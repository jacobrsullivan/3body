"""
Automatic Regularization Switching (WP1 Phase 5).

Implements smooth automatic switching between Cartesian and regularized
coordinates based on distance to primaries.

Strategy (Mikkola's approach):
- Distance to primary < r_switch_on → activate KS/LC
- Distance to primary > r_switch_off → deactivate
- Hysteresis: r_switch_off = 2 × r_switch_on
"""

from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class SwitchingConfig:
    """Configuration for coordinate switching."""
    r_switch_on: float = 0.01
    r_switch_off: float = 0.02  # Hysteresis
    max_energy_error: float = 1e-14


class AdaptiveRegularizationIntegrator:
    """Automatically switch between Cartesian and regularized coordinates."""

    def __init__(
        self,
        base_integrator,
        regularized_integrator,
        config: SwitchingConfig = None
    ):
        """
        Initialize adaptive switching integrator.

        Args:
            base_integrator: Cartesian integrator
            regularized_integrator: Regularized integrator (KS/LC)
            config: Switching configuration
        """
        self.cartesian_integrator = base_integrator
        self.regularized_integrator = regularized_integrator
        self.config = config or SwitchingConfig()
        self.is_regularized = False
        logger.info("Initialized AdaptiveRegularizationIntegrator")

    def integrate_with_switching(
        self,
        initial_state: np.ndarray,
        t_final: float,
        output_interval: float
    ):
        """
        Integrate with automatic coordinate switching.

        Returns:
            Integration result
        """
        from ..utils.dynamics import distances_to_primaries

        state = initial_state.copy()
        t = 0.0

        while t < t_final:
            r1, r2 = distances_to_primaries(state, self.cartesian_integrator.mu)
            r_min = min(r1, r2)

            # Switching logic
            if not self.is_regularized and r_min < self.config.r_switch_on:
                logger.info(f"Switching to regularized coordinates at t={t:.3f}")
                self.is_regularized = True

            if self.is_regularized and r_min > self.config.r_switch_off:
                logger.info(f"Switching to Cartesian coordinates at t={t:.3f}")
                self.is_regularized = False

            # Integrate using appropriate coordinates
            if self.is_regularized:
                result = self.regularized_integrator.integrate(
                    state, output_interval, output_interval
                )
            else:
                result = self.cartesian_integrator.integrate(
                    state, output_interval, output_interval
                )

            if not result.success:
                break

            state = result.states_corotating[-1]
            t += output_interval

        logger.info(f"Integration complete with {self.is_regularized} switches")
