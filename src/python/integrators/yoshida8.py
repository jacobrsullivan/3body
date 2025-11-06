"""
Yoshida-8 Symplectic Integrator

Implements 6th-order symplectic composition integrator for CR3BP.
Uses Yoshida's composition method to achieve high-order accuracy
while preserving the symplectic structure of Hamiltonian systems.

Note: Despite the "8" in the name (referring to the composition structure),
this is a 6th-order accurate method.

References:
    Yoshida, H. (1990). Construction of higher order symplectic integrators.
    Physics Letters A, 150(5-7), 262-268.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass

from src.python.integrators.base import IntegratorBase, IntegrationResult
from src.python.utils.dynamics import cr3bp_acceleration


# Yoshida 6th order coefficients (FR method)
# These coefficients provide 6th-order accuracy while maintaining symplecticity
# Source: Yoshida, H. (1990). Construction of higher order symplectic integrators.
# Physics Letters A, 150(5-7), 262-268.
#
# The FR (Forest-Ruth) 6th order method uses 7 substeps
# Symmetric composition: w1, w2, w3, w4, w3, w2, w1
YOSHIDA8_COEFFICIENTS = {
    'w': np.array([
        0.78451361047755726382,
        0.23557321335935813368,
        -1.17767998417887100695,
        1.31518632068391121889,
        -1.17767998417887100695,
        0.23557321335935813368,
        0.78451361047755726382
    ])
}


class Yoshida8Integrator(IntegratorBase):
    """
    Yoshida 6th-order symplectic composition integrator.

    This integrator uses composition of simpler symplectic steps
    to achieve 6th-order accuracy while maintaining the symplectic
    structure. It's particularly well-suited for long-term integration
    of Hamiltonian systems like the CR3BP.

    Note: The class name "Yoshida8" refers to the 8-stage composition,
    but the actual order of accuracy is 6th order.

    Attributes:
        mu: CR3BP mass parameter
        dt: Fixed timestep for integration
    """

    def __init__(self, mu: float, dt: float = 0.001):
        """
        Initialize Yoshida-8 integrator.

        Args:
            mu: Mass parameter (m2/(m1+m2))
            dt: Integration timestep (fixed, default=0.001)

        Note:
            For CR3BP near Lagrange points, typical stable timesteps are
            dt ~ 0.001-0.002 to resolve the libration frequencies.
        """
        super().__init__(mu)
        self.dt = dt
        self.coefficients = YOSHIDA8_COEFFICIENTS['w']

        # Validate coefficients sum to 1 (composition property)
        coeff_sum = np.sum(self.coefficients)
        if not np.isclose(coeff_sum, 1.0, atol=1e-12):
            raise ValueError(
                f"Yoshida coefficients must sum to 1, got {coeff_sum}"
            )

    def _drift_step(self, state: np.ndarray, c: float, h: float) -> np.ndarray:
        """
        Perform drift (kinetic) step: position update.

        In the symplectic splitting, the drift step updates positions
        using current velocities.

        Args:
            state: Current state [x, y, z, vx, vy, vz]
            c: Coefficient for this substep
            h: Timestep

        Returns:
            Updated state after drift
        """
        new_state = state.copy()
        # Update position: q = q + c*h*v
        new_state[:3] += c * h * state[3:6]
        return new_state

    def _kick_step(self, state: np.ndarray, d: float, h: float) -> np.ndarray:
        """
        Perform kick (potential) step: velocity update.

        In the symplectic splitting, the kick step updates velocities
        using forces computed from current positions.

        Args:
            state: Current state [x, y, z, vx, vy, vz]
            d: Coefficient for this substep
            h: Timestep

        Returns:
            Updated state after kick
        """
        new_state = state.copy()
        # Compute acceleration at current position
        accel = cr3bp_acceleration(new_state, self.mu)
        # Update velocity: v = v + d*h*a
        new_state[3:6] += d * h * accel
        return new_state

    def _yoshida8_step(self, state: np.ndarray, h: float) -> np.ndarray:
        """
        Perform one Yoshida-8 integration step.

        Uses composition method with 7 coefficients to achieve
        6th-order accuracy.

        Args:
            state: Current state [x, y, z, vx, vy, vz]
            h: Timestep

        Returns:
            State after one Yoshida-8 step
        """
        # Yoshida-8 uses a specific pattern of drift-kick-drift
        # with 7 coefficient pairs
        w = self.coefficients

        current_state = state.copy()

        # Composition: Apply substeps with Yoshida coefficients
        # Pattern: drift(w[0]/2) - kick(w[0]) - drift(w[0]/2 + w[1]/2) - ...

        # First half-drift
        current_state = self._drift_step(current_state, w[0] / 2, h)

        # Main composition sequence
        for i in range(len(w)):
            # Full kick
            current_state = self._kick_step(current_state, w[i], h)

            # Drift (sum of current and next half-steps)
            if i < len(w) - 1:
                drift_coeff = w[i] / 2 + w[i + 1] / 2
            else:
                drift_coeff = w[i] / 2
            current_state = self._drift_step(current_state, drift_coeff, h)

        return current_state

    def _integrate_internal(
        self,
        initial_state: np.ndarray,
        duration: float,
        output_interval: float
    ) -> IntegrationResult:
        """
        Internal integration method using Yoshida-8.

        Args:
            initial_state: Initial state [x, y, z, vx, vy, vz] (co-rotating)
            duration: Total integration time
            output_interval: Time interval for output sampling

        Returns:
            IntegrationResult with trajectory data
        """

        # Determine number of steps
        n_steps = int(np.ceil(duration / self.dt))
        n_output = int(np.ceil(duration / output_interval))

        # Adjust dt to hit final time exactly
        dt_actual = duration / n_steps

        # Output stride
        output_stride = max(1, n_steps // n_output)

        # Preallocate arrays
        times = []
        states_corotating = []

        # Initial state
        current_state = initial_state.copy()
        times.append(0.0)
        states_corotating.append(current_state.copy())

        # Main integration loop
        t = 0.0
        for step in range(n_steps):
            # Yoshida-8 step
            current_state = self._yoshida8_step(current_state, dt_actual)
            t += dt_actual

            # Store output
            if (step + 1) % output_stride == 0 or step == n_steps - 1:
                times.append(t)
                states_corotating.append(current_state.copy())

        # Convert to arrays
        times = np.array(times)
        states_corotating = np.array(states_corotating)

        # Transform to inertial frame
        from src.python.utils.coordinates import transform_trajectory_to_inertial
        states_inertial = transform_trajectory_to_inertial(
            states_corotating, times
        )

        # Integration statistics
        stats = {
            "integrator": "Yoshida-8",
            "order": 6,
            "timestep": dt_actual,
            "n_steps": n_steps,
            "n_points": len(times),
            "final_time": times[-1],
        }

        return IntegrationResult(
            times=times,
            states_corotating=states_corotating,
            states_inertial=states_inertial,
            success=True,
            message="Integration completed successfully",
            stats=stats
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Yoshida8Integrator(mu={self.mu:.6f}, dt={self.dt:.6f})"
        )


def find_optimal_timestep(
    mu: float,
    initial_state: np.ndarray,
    duration: float,
    target_jacobi_drift: float = 1e-13,
    dt_range: tuple = (0.001, 0.1),
    n_trials: int = 10
) -> float:
    """
    Find optimal timestep for Yoshida-8 integrator.

    Performs a sweep over timestep values to find the largest dt
    that maintains Jacobi constant drift below target.

    Args:
        mu: Mass parameter
        initial_state: Initial state for test integration
        duration: Test integration duration
        target_jacobi_drift: Maximum allowed relative Jacobi drift
        dt_range: (min_dt, max_dt) range to search
        n_trials: Number of timesteps to try

    Returns:
        Optimal timestep value
    """
    from src.python.utils.dynamics import calculate_jacobi_constant

    dt_values = np.logspace(
        np.log10(dt_range[0]),
        np.log10(dt_range[1]),
        n_trials
    )

    J0 = calculate_jacobi_constant(initial_state, mu)

    results = []

    for dt in dt_values:
        integrator = Yoshida8Integrator(mu=mu, dt=dt)

        try:
            result = integrator.integrate(
                initial_state=initial_state,
                duration=duration,
                output_interval=duration / 10
            )

            # Compute Jacobi drift
            J_final = calculate_jacobi_constant(
                result.states_corotating[-1], mu
            )
            jacobi_drift = abs((J_final - J0) / J0)

            results.append({
                'dt': dt,
                'jacobi_drift': jacobi_drift,
                'passes': jacobi_drift < target_jacobi_drift
            })

        except Exception as e:
            results.append({
                'dt': dt,
                'jacobi_drift': np.inf,
                'passes': False
            })

    # Find largest dt that passes
    passing = [r for r in results if r['passes']]

    if not passing:
        # Return smallest dt if none pass
        return dt_range[0]

    # Return largest passing dt
    optimal = max(passing, key=lambda r: r['dt'])
    return optimal['dt']
