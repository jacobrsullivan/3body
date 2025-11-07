"""
Abstract base class for CR3BP integrators.

This module defines the standard interface that all integrator implementations
must follow, ensuring consistent behavior and easy swapping between different
numerical integration methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class IntegrationResult:
    """
    Container for integration results with metadata.

    Attributes:
        times: Array of time points
        states_corotating: State vectors in co-rotating frame [N, 6]
        states_inertial: State vectors in inertial frame [N, 6]
        success: Whether integration completed successfully
        message: Status or error message
        stats: Integration statistics dictionary
    """

    times: np.ndarray
    states_corotating: np.ndarray
    states_inertial: np.ndarray
    success: bool
    message: str
    stats: Dict[str, Any]


class IntegratorError(Exception):
    """Base exception for integrator-related errors."""

    pass


class IntegrationFailedException(IntegratorError):
    """Raised when integration fails to complete."""

    pass


class InvalidInitialConditionsError(IntegratorError):
    """Raised when initial conditions are invalid."""

    pass


class IntegratorBase(ABC):
    """
    Abstract base class for CR3BP integrators.

    All integrator implementations must inherit from this class and implement
    the required abstract methods. This ensures a consistent interface for
    the benchmark harness.
    """

    def __init__(self, mu: float, **kwargs):
        """
        Initialize the integrator.

        Args:
            mu: Mass parameter (M2 / (M1 + M2))
            **kwargs: Integrator-specific parameters
        """
        self.mu = self._validate_mu(mu)
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

        # Default parameters that can be overridden
        self.tolerance = kwargs.get("tolerance", 1e-14)
        self.max_steps = kwargs.get("max_steps", 1000000)
        self.timeout = kwargs.get("timeout", 3600)  # 1 hour default

        self.logger.info(f"Initialized {self.name} with mu={mu:.6e}")

    def _validate_mu(self, mu: float) -> float:
        """Validate mass parameter."""
        if not isinstance(mu, (int, float)):
            raise ValueError("Mass parameter mu must be numeric")
        if not (0 < mu < 1):
            raise ValueError("Mass parameter mu must be in range (0, 1)")
        return float(mu)

    def _validate_initial_state(self, state: np.ndarray) -> np.ndarray:
        """Validate initial state vector."""
        state = np.asarray(state, dtype=float)
        if state.shape != (6,):
            raise InvalidInitialConditionsError(
                f"Initial state must have shape (6,), got {state.shape}"
            )
        if not np.all(np.isfinite(state)):
            raise InvalidInitialConditionsError(
                "Initial state contains non-finite values"
            )
        return state

    def _validate_time_parameters(
        self, duration: float, output_interval: float
    ) -> Tuple[float, float]:
        """Validate integration time parameters."""
        if duration <= 0:
            raise ValueError("Duration must be positive")
        if output_interval <= 0:
            raise ValueError("Output interval must be positive")
        if output_interval > duration:
            raise ValueError("Output interval cannot exceed duration")
        return float(duration), float(output_interval)

    @abstractmethod
    def _integrate_internal(
        self, initial_state: np.ndarray, duration: float, output_interval: float
    ) -> IntegrationResult:
        """
        Internal integration method to be implemented by subclasses.

        Args:
            initial_state: Initial state [x, y, z, vx, vy, vz] (co-rotating)
            duration: Total integration time
            output_interval: Time interval for output sampling

        Returns:
            IntegrationResult containing trajectory and metadata
        """
        pass

    def integrate(
        self, initial_state: np.ndarray, duration: float, output_interval: float
    ) -> IntegrationResult:
        """
        Integrate CR3BP trajectory with error handling and timing.

        Args:
            initial_state: Initial state [x, y, z, vx, vy, vz] (co-rotating)
            duration: Total integration time in normalized units
            output_interval: Time interval for output sampling

        Returns:
            IntegrationResult containing trajectory in both frames and metadata

        Raises:
            InvalidInitialConditionsError: If initial conditions are invalid
            IntegrationFailedException: If integration fails
        """
        # Input validation
        initial_state = self._validate_initial_state(initial_state)
        duration, output_interval = self._validate_time_parameters(
            duration, output_interval
        )

        self.logger.info(f"Starting integration for {duration:.2f} time units")
        self.logger.debug(f"Initial state: {initial_state}")
        self.logger.debug(f"Output interval: {output_interval:.6f}")

        start_time = time.time()

        try:
            # Perform the actual integration
            result = self._integrate_internal(initial_state, duration, output_interval)

            # Add timing information
            wall_time = time.time() - start_time
            result.stats["wall_time"] = wall_time
            result.stats["points_per_second"] = (
                len(result.times) / wall_time if wall_time > 0 else float("inf")
            )

            if result.success:
                self.logger.info(
                    f"Integration completed successfully in {wall_time:.3f}s"
                )
                self.logger.info(f"Generated {len(result.times)} output points")
            else:
                self.logger.error(f"Integration failed: {result.message}")

            return result

        except Exception as e:
            wall_time = time.time() - start_time
            self.logger.error(f"Integration failed after {wall_time:.3f}s: {e}")

            # Return failed result
            return IntegrationResult(
                times=np.array([0.0]),
                states_corotating=initial_state.reshape(1, 6),
                states_inertial=initial_state.reshape(1, 6),
                success=False,
                message=str(e),
                stats={"wall_time": wall_time, "error": str(e)},
            )

    def get_info(self) -> Dict[str, Any]:
        """
        Get integrator information and current settings.

        Returns:
            Dictionary containing integrator metadata
        """
        return {
            "name": self.name,
            "mu": self.mu,
            "tolerance": self.tolerance,
            "max_steps": self.max_steps,
            "timeout": self.timeout,
            "type": (
                "symplectic"
                if hasattr(self, "_is_symplectic") and self._is_symplectic
                else "non-symplectic"
            ),
        }

    def __str__(self) -> str:
        """String representation of the integrator."""
        return f"{self.name}(mu={self.mu:.6e}, tol={self.tolerance:.2e})"

    def __repr__(self) -> str:
        """Detailed string representation of the integrator."""
        return (
            f"{self.name}(mu={self.mu}, "
            f"tolerance={self.tolerance}, max_steps={self.max_steps})"
        )
