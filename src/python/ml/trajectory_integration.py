"""
High-precision trajectory integration for ML training data (Task 3.2.1, Part B).

This module integrates 3-body trajectories on lifted manifolds (S¹ bundle, KS-Spinor)
with high precision for generating training datasets.

Quality requirements:
- Energy conservation: |ΔE|/E < 10⁻¹²
- Symplectic structure preservation
- Collision avoidance or regularization
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, List
import numpy as np
from scipy.integrate import solve_ivp

from .parameter_sampling import InitialCondition


@dataclass
class Trajectory:
    """
    Single integrated trajectory.

    Attributes:
        times: (N_steps,) time array
        states: (N_steps, dim) phase space states
        derivatives: (N_steps, dim) time derivatives dz/dt
        energy_drift: |ΔE|/E over trajectory
        symplectic_error: Symplectic structure violation
        initial_condition: Initial condition used
        manifold_type: 's1' or 'ks'
        integration_time: Wall-clock time for integration (seconds)
        success: Whether integration completed successfully
    """
    times: np.ndarray
    states: np.ndarray
    derivatives: np.ndarray
    energy_drift: float
    symplectic_error: float
    initial_condition: InitialCondition
    manifold_type: str
    integration_time: float
    success: bool = True

    def __post_init__(self):
        """Validate dimensions."""
        assert len(self.times) == len(self.states), "times and states must have same length"
        assert self.states.shape == self.derivatives.shape, "states and derivatives must have same shape"


@dataclass
class IntegrationConfig:
    """
    Configuration for trajectory integration.

    Attributes:
        integrator: Integration method ('DOP853', 'DOP5', 'LSODA')
        rtol: Relative tolerance
        atol: Absolute tolerance
        max_step: Maximum timestep
        dense_output: Whether to use dense output
        t_eval_dt: Timestep for output sampling
    """
    integrator: str = 'DOP853'
    rtol: float = 1e-13
    atol: float = 1e-14
    max_step: float = 0.01
    dense_output: bool = True
    t_eval_dt: float = 0.01  # Output timestep


def integrate_s1_bundle_trajectory(
    ic: InitialCondition,
    t_span: float,
    config: Optional[IntegrationConfig] = None,
    energy_drift_threshold: float = 1e-10
) -> Optional[Trajectory]:
    """
    Integrate trajectory on S¹ principal bundle.

    The S¹ bundle has coordinates z = (s, θ, p_s, p_θ) where:
    - s: shape space coordinates (3D)
    - θ: fiber coordinate (S¹)
    - p_s, p_θ: conjugate momenta

    Args:
        ic: Initial condition in 3-body Cartesian coordinates
        t_span: Integration time
        config: Integration configuration
        energy_drift_threshold: Maximum acceptable energy drift

    Returns:
        Trajectory object if successful, None if quality checks fail
    """
    import time

    if config is None:
        config = IntegrationConfig()

    start_time = time.time()

    try:
        # Convert initial condition to S¹ bundle coordinates
        z0 = _cartesian_to_s1_bundle(ic)

        # Define dynamics on S¹ bundle
        def s1_dynamics(t, z):
            return _s1_bundle_hamiltonian_dynamics(z, ic.masses, ic.energy)

        # Time evaluation points
        times = np.arange(0, t_span, config.t_eval_dt)

        # Integrate
        sol = solve_ivp(
            s1_dynamics,
            t_span=(0, t_span),
            y0=z0,
            method=config.integrator,
            t_eval=times,
            rtol=config.rtol,
            atol=config.atol,
            max_step=config.max_step,
            dense_output=config.dense_output
        )

        if not sol.success:
            print(f"Integration failed: {sol.message}")
            return None

        # Compute derivatives at each point
        derivatives = np.array([s1_dynamics(sol.t[i], sol.y[:, i]) for i in range(len(sol.t))])

        # Quality checks
        energies = _compute_s1_energies(sol.y.T, ic.masses)
        energy_drift = np.abs(energies - energies[0]).max() / (np.abs(energies[0]) + 1e-14)

        # Symplectic structure check
        symplectic_error = _check_symplectic_structure(sol.y.T, derivatives)

        # Reject if quality is poor
        if energy_drift > energy_drift_threshold:
            print(f"Rejecting trajectory: energy drift {energy_drift:.2e} > {energy_drift_threshold:.2e}")
            return None

        integration_time = time.time() - start_time

        return Trajectory(
            times=sol.t,
            states=sol.y.T,  # Transpose to (N_steps, dim)
            derivatives=derivatives,
            energy_drift=energy_drift,
            symplectic_error=symplectic_error,
            initial_condition=ic,
            manifold_type='s1',
            integration_time=integration_time,
            success=True
        )

    except Exception as e:
        print(f"Integration error: {e}")
        return None


def _cartesian_to_s1_bundle(ic: InitialCondition) -> np.ndarray:
    """
    Convert Cartesian initial condition to S¹ bundle coordinates.

    This is a simplified version. For production, would use the full
    transformation from WP2 (src/python/lifts/s1_bundle.py).

    Args:
        ic: Initial condition in Cartesian coordinates

    Returns:
        z: State in S¹ bundle coordinates (8D)
            [r12, r23, r31, θ, p_r12, p_r23, p_r31, p_θ]
    """
    q = ic.position  # (3, 3)
    v = ic.velocity  # (3, 3)
    masses = ic.masses  # (3,)

    # Compute shape coordinates (mutual distances)
    r12 = np.linalg.norm(q[1] - q[0])
    r23 = np.linalg.norm(q[2] - q[1])
    r31 = np.linalg.norm(q[0] - q[2])

    # Fiber coordinate (angle - simplified)
    # In full implementation, this would be computed from the twist
    theta = 0.0  # Placeholder

    # Shape momenta (simplified - would use proper transformation)
    # For now, use projection of velocities
    p_r12 = masses[0] * masses[1] * np.dot(v[1] - v[0], (q[1] - q[0]) / r12)
    p_r23 = masses[1] * masses[2] * np.dot(v[2] - v[1], (q[2] - q[1]) / r23)
    p_r31 = masses[2] * masses[0] * np.dot(v[0] - v[2], (q[0] - q[2]) / r31)

    # Fiber momentum (angular momentum component)
    L_total = np.sum(masses[:, None] * np.cross(q, v, axis=1), axis=0)
    p_theta = np.linalg.norm(L_total)

    return np.array([r12, r23, r31, theta, p_r12, p_r23, p_r31, p_theta])


def _s1_bundle_hamiltonian_dynamics(
    z: np.ndarray,
    masses: np.ndarray,
    energy: float
) -> np.ndarray:
    """
    Hamiltonian dynamics on S¹ bundle: dz/dt = J ∇H.

    This is a simplified placeholder. For production, would use:
    - src/python/lifts/s1_bundle.py
    - src/python/geometry/lifted_jm_metric.py

    Args:
        z: State in S¹ bundle coordinates (8D)
        masses: Body masses (3,)
        energy: Total energy

    Returns:
        dz/dt: Time derivative (8D)
    """
    # Placeholder implementation
    # Real implementation would compute:
    # 1. Metric tensor g on S¹ bundle
    # 2. Christoffel symbols Γ
    # 3. Hamiltonian H = g^{ij} p_i p_j / 2 + V(q)
    # 4. Hamilton's equations: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q

    # For now, return zero (will be replaced with proper implementation)
    dz_dt = np.zeros_like(z)

    # Simple dynamics approximation (not physically accurate, just for structure)
    # In production, this would call the proper WP2 dynamics
    q = z[:4]  # Configuration
    p = z[4:]  # Momenta

    # Simplified Hamiltonian flow (placeholder)
    dq_dt = p / np.array([masses[0] * masses[1], masses[1] * masses[2],
                          masses[2] * masses[0], 1.0])
    dp_dt = np.zeros_like(p)  # Placeholder

    dz_dt = np.concatenate([dq_dt, dp_dt])

    return dz_dt


def _compute_s1_energies(states: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """
    Compute energy at each timestep for quality check.

    Args:
        states: (N, 8) states along trajectory
        masses: Body masses (3,)

    Returns:
        energies: (N,) energy values
    """
    # Placeholder - would use proper Hamiltonian from WP2
    N = len(states)
    energies = np.zeros(N)

    for i in range(N):
        z = states[i]
        # Simplified energy computation
        # Real version would use H(z) = g^{ij} p_i p_j / 2 + V(q)
        p = z[4:]
        T = 0.5 * np.sum(p**2)  # Simplified kinetic energy
        V = 0.0  # Would compute potential from shape coordinates
        energies[i] = T + V

    return energies


def _check_symplectic_structure(
    states: np.ndarray,
    derivatives: np.ndarray
) -> float:
    """
    Verify symplectic 2-form preservation.

    For Hamiltonian systems: ω = dq ∧ dp is conserved.

    Args:
        states: (N, dim) states along trajectory
        derivatives: (N, dim) time derivatives

    Returns:
        Symplectic error (standard deviation of ω)
    """
    N, dim = states.shape
    n = dim // 2

    # Extract q and p components
    q_dot = derivatives[:, :n]
    p_dot = derivatives[:, n:]

    # Compute simplified symplectic invariant
    # Real implementation would compute full ω_ij matrix
    omega_values = []
    for i in range(N):
        # Simplified: just check magnitude
        omega = np.sum(q_dot[i] * p_dot[i])
        omega_values.append(omega)

    omega_drift = np.std(omega_values) / (np.abs(np.mean(omega_values)) + 1e-14)
    return omega_drift


def integrate_batch(
    initial_conditions: List[InitialCondition],
    t_span: float,
    config: Optional[IntegrationConfig] = None,
    manifold_type: str = 's1',
    verbose: bool = True
) -> List[Trajectory]:
    """
    Integrate batch of trajectories.

    Args:
        initial_conditions: List of initial conditions
        t_span: Integration time
        config: Integration configuration
        manifold_type: 's1' or 'ks'
        verbose: Print progress

    Returns:
        List of successfully integrated trajectories
    """
    if config is None:
        config = IntegrationConfig()

    trajectories = []

    if manifold_type == 's1':
        integrate_func = integrate_s1_bundle_trajectory
    else:
        raise NotImplementedError(f"Manifold type '{manifold_type}' not yet implemented")

    for i, ic in enumerate(initial_conditions):
        if verbose and i % 10 == 0:
            print(f"Integrating trajectory {i + 1}/{len(initial_conditions)}...")

        traj = integrate_func(ic, t_span, config)

        if traj is not None:
            trajectories.append(traj)

    success_rate = len(trajectories) / len(initial_conditions)
    print(f"\nIntegration complete: {len(trajectories)}/{len(initial_conditions)} successful ({success_rate:.1%})")

    return trajectories


def integrate_batch_parallel(
    initial_conditions: List[InitialCondition],
    t_span: float,
    config: Optional[IntegrationConfig] = None,
    manifold_type: str = 's1',
    num_workers: int = 4
) -> List[Trajectory]:
    """
    Integrate batch of trajectories in parallel.

    Uses multiprocessing for speedup on multi-core systems.

    Args:
        initial_conditions: List of initial conditions
        t_span: Integration time
        config: Integration configuration
        manifold_type: 's1' or 'ks'
        num_workers: Number of parallel workers

    Returns:
        List of successfully integrated trajectories
    """
    from multiprocessing import Pool
    from functools import partial

    if config is None:
        config = IntegrationConfig()

    if manifold_type == 's1':
        integrate_func = integrate_s1_bundle_trajectory
    else:
        raise NotImplementedError(f"Manifold type '{manifold_type}' not yet implemented")

    # Create partial function with fixed arguments
    integrate_one = partial(integrate_func, t_span=t_span, config=config)

    print(f"Integrating {len(initial_conditions)} trajectories using {num_workers} workers...")

    with Pool(num_workers) as pool:
        trajectories = pool.map(integrate_one, initial_conditions)

    # Filter out None (failed integrations)
    trajectories = [t for t in trajectories if t is not None]

    success_rate = len(trajectories) / len(initial_conditions)
    print(f"Integration complete: {len(trajectories)}/{len(initial_conditions)} successful ({success_rate:.1%})")

    return trajectories


if __name__ == "__main__":
    # Quick test
    print("Testing trajectory integration...")

    from .parameter_sampling import generate_test_samples

    # Generate test initial conditions
    ics = generate_test_samples(num_samples=2)

    print(f"\nIntegrating {len(ics)} test trajectories...")

    # Integrate
    trajectories = integrate_batch(
        ics,
        t_span=10.0,
        config=IntegrationConfig(t_eval_dt=0.1),
        verbose=True
    )

    print(f"\nSuccessfully integrated {len(trajectories)} trajectories")

    if trajectories:
        traj = trajectories[0]
        print(f"\nFirst trajectory:")
        print(f"  Duration: {traj.times[-1]:.2f} time units")
        print(f"  Steps: {len(traj.times)}")
        print(f"  Energy drift: {traj.energy_drift:.2e}")
        print(f"  Symplectic error: {traj.symplectic_error:.2e}")
        print(f"  Integration time: {traj.integration_time:.2f} seconds")
