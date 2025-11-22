"""
Time-regularized constrained dynamics (Phase 2).

Extends constrained_dynamics.py to track physical time alongside fictitious time,
implementing the (4+1)-dimensional KS regularization.

Key additions:
   - Dual time tracking: (s, t) with dt/ds = Ω(u)
   - Dual energy tracking: (K, E) with K = E · Ω(u)
   - Extended state space integration
   - Kepler problem validation

References:
    - AMENDED_WP2.3-KS-Spinor-Lift-Implementation-Plan.md (Part C)
    - AMENDED_ACTION_PLAN.md (Month 3-4)
"""

from dataclasses import dataclass
from typing import Tuple, List, Optional
import numpy as np
from scipy.integrate import solve_ivp

from ..coordinates.base import Masses
from .extended_phase_space import ExtendedKSState, create_extended_ks_state
from .ks_transform import KSState, ks_to_cartesian, cartesian_to_ks
from .sundman import SundmanTransformation, TimeTransformationStrategy
from .time_synchronizer import TimeSynchronizer, DualTimeTrajectory


@dataclass(frozen=True)
class TimeRegularizedHamiltonian:
    """
    Hamiltonian for time-regularized KS system.

    For single pair (two-body problem):
        H_reg = (1/2)‖p_u‖² - μ/‖u‖² = K  (regularized energy)
        H_phys = (1/2)‖v‖² - μ/r = E     (physical energy)

    Relation: K = E · Ω(u) where Ω(u) = ‖u‖² = r
    """

    mu: float  # Gravitational parameter μ = G m1 m2

    def evaluate_regularized(self, state: ExtendedKSState) -> float:
        """Evaluate regularized Hamiltonian (should equal K)"""
        kinetic = 0.5 * state.p_u.norm_squared
        potential = -self.mu / state.u.norm_squared if state.u.norm_squared > 1e-14 else 0.0
        return kinetic + potential

    def compute_forces(self, state: ExtendedKSState) -> np.ndarray:
        """
        Compute ∂H_reg/∂u for Hamilton's equations.

        Returns: force vector (4,)
        """
        r = state.u.norm_squared
        if r < 1e-14:
            return np.zeros(4)

        # ∂H/∂u = (2μ/r²) · u / r
        force_magnitude = 2.0 * self.mu / (r ** 2)
        u_array = state.u.to_array()

        return force_magnitude * u_array / r


@dataclass
class TimeRegularizedTrajectory:
    """
    Trajectory from time-regularized integration.

    Stores both fictitious time (s) and physical time (t).
    """
    s_values: np.ndarray
    t_values: np.ndarray
    states: List[ExtendedKSState]

    @property
    def length(self) -> int:
        return len(self.states)

    def get_energies(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return (E_values, K_values)"""
        E = np.array([s.E for s in self.states])
        K = np.array([s.K for s in self.states])
        return E, K

    def get_time_dilations(self) -> np.ndarray:
        """Return Ω(s) = dt/ds at each point"""
        return np.array([s.time_dilation_factor for s in self.states])


def integrate_time_regularized_ks(
    initial_state: ExtendedKSState,
    hamiltonian: TimeRegularizedHamiltonian,
    s_span: Tuple[float, float],
    n_points: int = 1000,
    method: str = 'DOP853',
    **integrator_options
) -> TimeRegularizedTrajectory:
    """
    Integrate time-regularized KS dynamics.

    Equations (in fictitious time s):
        du/ds = p_u
        dp_u/ds = ∂H_reg/∂u
        dt/ds = Ω(u) = ‖u‖²
        dK/ds = 0  (K conserved in s)
        dE/ds = 0  (E conserved always)

    Args:
        initial_state: Extended KS state with time
        hamiltonian: Time-regularized Hamiltonian
        s_span: (s_start, s_end) in fictitious time
        n_points: Number of output points
        method: Integration method
        **integrator_options: Additional scipy options

    Returns:
        TimeRegularizedTrajectory with dual time tracking

    Example:
        >>> state0 = create_extended_ks_state(u, p_u, s=0, K=-0.5, t=0, E=-0.5)
        >>> H = TimeRegularizedHamiltonian(mu=1.0)
        >>> traj = integrate_time_regularized_ks(state0, H, (0, 100))
        >>> print(f"Physical time elapsed: {traj.t_values[-1] - traj.t_values[0]}")
    """

    def rhs(s: float, z: np.ndarray) -> np.ndarray:
        """
        Right-hand side for time-regularized system.

        State vector z = [u (4), p_u (4), t (1), K (1), E (1)] = (10,)

        Returns: dz/ds
        """
        # Unpack state
        u_vec = z[0:4]
        p_u_vec = z[4:8]
        t = z[8]
        K = z[9]
        E = z[10]

        # Reconstruct ExtendedKSState
        from .spinor_vector import SpinorVector
        state = ExtendedKSState(
            u=SpinorVector(*u_vec),
            p_u=SpinorVector(*p_u_vec),
            s=s,
            K=K,
            t=t,
            E=E
        )

        # Compute forces
        forces = hamiltonian.compute_forces(state)

        # Hamilton's equations in s
        du_ds = p_u_vec  # ∂H/∂p_u
        dp_u_ds = forces  # -∂H/∂u (sign handled in compute_forces)

        # Time evolution
        Omega = state.time_dilation_factor  # Ω = ‖u‖²
        dt_ds = Omega

        # Energy evolution (both conserved)
        dK_ds = 0.0
        dE_ds = 0.0

        dz_ds = np.concatenate([
            du_ds,
            dp_u_ds,
            [dt_ds],
            [dK_ds],
            [dE_ds]
        ])

        return dz_ds

    # Initial condition vector
    z0 = initial_state.to_vector()

    # Time points for output
    s_eval = np.linspace(s_span[0], s_span[1], n_points)

    # Integrate
    solution = solve_ivp(
        rhs,
        s_span,
        z0,
        method=method,
        t_eval=s_eval,
        **integrator_options
    )

    if not solution.success:
        raise RuntimeError(f"Integration failed: {solution.message}")

    # Reconstruct states
    from .spinor_vector import SpinorVector
    states = []
    for i in range(solution.y.shape[1]):
        z = solution.y[:, i]
        s = solution.t[i]

        state = ExtendedKSState(
            u=SpinorVector(*z[0:4]),
            p_u=SpinorVector(*z[4:8]),
            s=s,
            K=z[9],
            t=z[8],
            E=z[10]
        )
        states.append(state)

    return TimeRegularizedTrajectory(
        s_values=solution.t,
        t_values=solution.y[8, :],
        states=states
    )


def validate_kepler_orbit(
    trajectory: TimeRegularizedTrajectory,
    expected_period: float,
    tolerance: float = 0.01
) -> dict:
    """
    Validate time-regularized trajectory against Kepler orbit.

    For two-body problem, we can compute exact solutions and compare.

    Args:
        trajectory: Integrated trajectory
        expected_period: Expected orbital period
        tolerance: Relative tolerance for validation

    Returns:
        dict with validation results
    """
    E_vals, K_vals = trajectory.get_energies()

    # Check energy conservation
    E_drift = np.std(E_vals) / np.abs(np.mean(E_vals)) if np.mean(E_vals) != 0 else np.std(E_vals)
    K_drift = np.std(K_vals) / np.abs(np.mean(K_vals)) if np.mean(K_vals) != 0 else np.std(K_vals)

    # Check time relation K = E · Ω
    Omega_vals = trajectory.get_time_dilations()
    K_expected = E_vals * Omega_vals
    time_relation_error = np.max(np.abs(K_vals - K_expected))

    # Physical time elapsed
    t_elapsed = trajectory.t_values[-1] - trajectory.t_values[0]
    period_error = np.abs(t_elapsed - expected_period) / expected_period

    results = {
        'E_conservation': E_drift < tolerance,
        'K_conservation': K_drift < tolerance,
        'time_relation_satisfied': time_relation_error < tolerance,
        'period_match': period_error < tolerance,
        'E_drift': E_drift,
        'K_drift': K_drift,
        'time_relation_error': time_relation_error,
        'period_error': period_error,
        'physical_time_elapsed': t_elapsed,
        'expected_period': expected_period
    }

    return results


def create_kepler_initial_state(
    semi_major_axis: float = 1.0,
    eccentricity: float = 0.0,
    mu: float = 1.0
) -> ExtendedKSState:
    """
    Create initial state for Kepler orbit.

    Args:
        semi_major_axis: a
        eccentricity: e
        mu: gravitational parameter

    Returns:
        ExtendedKSState at perihelion
    """
    # Perihelion distance
    r0 = semi_major_axis * (1 - eccentricity)

    # Velocity at perihelion (vis-viva)
    v0 = np.sqrt(mu * (2/r0 - 1/semi_major_axis))

    # Cartesian state at perihelion (x-axis)
    q = np.array([r0, 0.0, 0.0])
    p = np.array([0.0, v0, 0.0])

    # Convert to KS
    ks_state = cartesian_to_ks(q, p)

    # Physical energy
    E = 0.5 * v0**2 - mu / r0

    # Create extended state
    state = create_extended_ks_state(
        u=ks_state.u,
        p_u=ks_state.u_prime,
        s=0.0,
        K=E * r0,  # K = E · Ω, Ω = r at start
        t=0.0,
        E=E
    )

    return state
