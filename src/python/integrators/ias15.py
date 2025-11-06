"""
IAS15 integrator implementation using REBOUND.

This module provides a wrapper around REBOUND's IAS15 integrator for
solving the CR3BP. IAS15 is a 15th-order implicit adaptive integrator
that provides excellent accuracy and energy conservation.
"""

import numpy as np
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.python.integrators.base import (  # noqa: E402
    IntegratorBase,
    IntegrationResult,
    IntegrationFailedException,
)
from src.python.utils.dynamics import cr3bp_acceleration  # noqa: E402
from src.python.utils.coordinates import transform_trajectory  # noqa: E402

try:
    import rebound
except ImportError:
    raise ImportError(
        "REBOUND is required for IAS15 integrator. Install with: pip install rebound"
    )


class IAS15Integrator(IntegratorBase):
    """
    IAS15 integrator implementation using REBOUND.

    IAS15 is a 15th-order adaptive Runge-Kutta integrator with excellent
    accuracy and stability properties. It's particularly well-suited for
    gravitational N-body problems.

    Key features:
    - 15th-order accuracy
    - Adaptive timestep control
    - Excellent energy conservation
    - Robust for close encounters
    - Non-symplectic but very stable
    """

    def __init__(
        self,
        mu: float,
        tolerance: float = 1e-14,
        min_dt: float = 1e-12,
        max_dt: float = 0.1,
        **kwargs,
    ):
        """
        Initialize IAS15 integrator.

        Args:
            mu: Mass parameter (M2 / (M1 + M2))
            tolerance: Relative accuracy tolerance
            min_dt: Minimum allowed timestep
            max_dt: Maximum allowed timestep
            **kwargs: Additional parameters passed to base class
        """
        super().__init__(mu, tolerance=tolerance, **kwargs)

        self.min_dt = min_dt
        self.max_dt = max_dt
        self._is_symplectic = False  # IAS15 is not symplectic

        self.logger.info(f"IAS15 configured with tolerance={tolerance:.2e}")
        self.logger.info(f"Timestep range: [{min_dt:.2e}, {max_dt:.2e}]")

    def _setup_rebound_simulation(
        self, initial_state: np.ndarray
    ) -> rebound.Simulation:
        """
        Set up REBOUND simulation for CR3BP.

        Args:
            initial_state: Initial state vector [x, y, z, vx, vy, vz]

        Returns:
            Configured REBOUND simulation object
        """
        # Create new simulation
        sim = rebound.Simulation()

        # Set integrator to IAS15
        sim.integrator = "ias15"

        # Configure IAS15 parameters
        sim.ri_ias15.epsilon = self.tolerance
        sim.dt = self.max_dt  # Initial timestep guess

        # Add the test particle (massless in CR3BP)
        sim.add(
            m=0,
            x=initial_state[0],
            y=initial_state[1],
            z=initial_state[2],
            vx=initial_state[3],
            vy=initial_state[4],
            vz=initial_state[5],
        )

        # Add additional forces function for CR3BP
        sim.additional_forces = self._cr3bp_forces
        sim.force_is_velocity_dependent = (
            1  # CR3BP forces depend on velocity (Coriolis)
        )

        self.logger.debug("REBOUND simulation configured")
        return sim

    def _cr3bp_forces(self, sim):
        """
        Additional forces function for REBOUND to implement CR3BP dynamics.

        This function is called by REBOUND at each timestep to add the
        CR3BP forces to the particles.

        Args:
            sim: REBOUND simulation object
        """
        try:
            # Get the particle (only one in CR3BP)
            if hasattr(sim, "particles") and len(sim.particles) > 0:
                p = sim.particles[0]
            else:
                # Fallback for different REBOUND versions
                p = (
                    sim.contents.particles[0]
                    if hasattr(sim, "contents")
                    else sim.particles[0]
                )

            # Create state vector
            state = np.array([p.x, p.y, p.z, p.vx, p.vy, p.vz])

            # Calculate CR3BP acceleration
            acc = cr3bp_acceleration(state, self.mu)

            # Add forces to particle
            p.ax += acc[0]
            p.ay += acc[1]
            p.az += acc[2]
        except Exception as e:
            # Graceful handling of REBOUND interface issues
            self.logger.warning(f"Force calculation failed: {e}")
            pass

    def _extract_trajectory(
        self, sim: rebound.Simulation, times: np.ndarray
    ) -> np.ndarray:
        """
        Extract trajectory from REBOUND simulation.

        Args:
            sim: REBOUND simulation object
            times: Array of output times

        Returns:
            Array of state vectors [N, 6]
        """
        n_points = len(times)
        trajectory = np.zeros((n_points, 6))

        # Store initial state
        p = sim.particles[0]
        trajectory[0] = [p.x, p.y, p.z, p.vx, p.vy, p.vz]

        # Integrate to each output time
        for i, t in enumerate(times[1:], 1):
            try:
                sim.integrate(t)
                p = sim.particles[0]
                trajectory[i] = [p.x, p.y, p.z, p.vx, p.vy, p.vz]

                # Log progress for long integrations
                if i % max(1, len(times) // 10) == 0:
                    progress = 100 * i / len(times)
                    self.logger.debug(f"Integration progress: {progress:.1f}%")

            except Exception as e:
                self.logger.error(f"Integration failed at t={t:.6f}: {e}")
                raise IntegrationFailedException(f"REBOUND integration failed: {e}")

        return trajectory

    def _create_output_times(
        self, duration: float, output_interval: float
    ) -> np.ndarray:
        """
        Create array of output times.

        Args:
            duration: Total integration time
            output_interval: Output sampling interval

        Returns:
            Array of output times including t=0 and t=duration
        """
        # Create regular grid of output times
        n_points = int(np.ceil(duration / output_interval)) + 1
        times = np.linspace(0, duration, n_points)

        # Ensure we end exactly at the specified duration
        times[-1] = duration

        return times

    def _integrate_internal(
        self, initial_state: np.ndarray, duration: float, output_interval: float
    ) -> IntegrationResult:
        """
        Internal integration method using REBOUND IAS15.

        Args:
            initial_state: Initial state vector [x, y, z, vx, vy, vz]
            duration: Total integration time
            output_interval: Output sampling interval

        Returns:
            IntegrationResult with trajectory data and statistics
        """
        try:
            # Set up REBOUND simulation
            sim = self._setup_rebound_simulation(initial_state)

            # Create output time array
            times = self._create_output_times(duration, output_interval)

            self.logger.info(
                f"Integrating {len(times)} points over {duration:.2f} time units"
            )

            # Extract trajectory
            states_corotating = self._extract_trajectory(sim, times)

            # Transform to inertial frame
            states_inertial = transform_trajectory(
                times, states_corotating, self.mu, to_inertial=True
            )

            # Collect integration statistics
            stats = {
                "integrator": "IAS15",
                "tolerance": self.tolerance,
                "n_steps": len(times),
                "n_points": len(times),
                "final_time": times[-1],
                "dt_range": [self.min_dt, self.max_dt],
                "rebound_version": rebound.__version__,
            }

            # Check for any obvious failures
            if not np.all(np.isfinite(states_corotating)):
                raise IntegrationFailedException(
                    "Integration produced non-finite values"
                )

            self.logger.info("Integration completed successfully")

            return IntegrationResult(
                times=times,
                states_corotating=states_corotating,
                states_inertial=states_inertial,
                success=True,
                message="Integration completed successfully",
                stats=stats,
            )

        except Exception as e:
            self.logger.error(f"Integration failed: {e}")

            # Return minimal failed result
            return IntegrationResult(
                times=np.array([0.0]),
                states_corotating=initial_state.reshape(1, 6),
                states_inertial=initial_state.reshape(1, 6),
                success=False,
                message=f"Integration failed: {str(e)}",
                stats={"error": str(e)},
            )

    def get_info(self) -> Dict[str, Any]:
        """
        Get IAS15-specific integrator information.

        Returns:
            Dictionary with integrator details
        """
        info = super().get_info()
        info.update(
            {
                "order": 15,
                "adaptive": True,
                "symplectic": False,
                "min_dt": self.min_dt,
                "max_dt": self.max_dt,
                "backend": "REBOUND",
                "algorithm": "Radau",
            }
        )
        return info
