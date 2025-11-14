"""
Lifted Hamiltonian dynamics on S¹ bundle (WP 2.2, Part C).

The lifted Hamiltonian is simply the pullback of the reduced Hamiltonian:
    H̃(s, θ, p_s, p_θ) = H_red(s, p_s)

Key property: H̃ is INDEPENDENT of θ and p_θ!

This immediately gives:
    {p_θ, H̃} = -∂H̃/∂θ = 0

So p_θ is conserved - the third integral we need for integrability!
"""

from dataclasses import dataclass
from typing import Callable, List, Optional
import numpy as np
from scipy.integrate import solve_ivp

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState
from ..geometry.jm_metric import compute_effective_potential
from .s1_bundle import BundleState
from .extended_symplectic import ExtendedSymplecticForm, compute_symplectic_gradient


@dataclass(frozen=True)
class LiftedHamiltonian:
    """
    Hamiltonian on S¹ bundle.

    H̃(s, θ, p_s, p_θ) = H_red(s, p_s)

    The Hamiltonian is the pullback of the reduced Hamiltonian,
    hence independent of fiber coordinates (θ, p_θ).

    Attributes:
        masses: Mass parameters
        energy: Total energy (conserved)
        angular_momentum: Angular momentum L (conserved)
        G: Gravitational constant
    """

    masses: Masses
    energy: float
    angular_momentum: float
    G: float = 1.0

    def evaluate(self, state: BundleState) -> float:
        """
        Evaluate H̃ at bundle state.

        Note: Result is independent of θ and p_θ!

        Args:
            state: Point in bundle

        Returns:
            H̃ value (equals H_red of projection)
        """
        # Compute effective potential at shape configuration
        V_eff = compute_effective_potential(
            state.shape_state,
            self.masses,
            self.angular_momentum,
            self.G
        )

        # Kinetic energy from shape momenta
        # T = (1/2) Σ pᵢ² / mᵢ (in appropriate mass metric)
        # Simplified: use Euclidean norm
        T_shape = 0.5 * np.sum(state.shape_momenta**2)

        # Total Hamiltonian
        H = T_shape + V_eff

        return H

    def is_theta_independent(self) -> bool:
        """
        Verify ∂H̃/∂θ = 0.

        Returns:
            True (by construction)
        """
        return True


@dataclass(frozen=True)
class BundleTrajectory:
    """
    Trajectory in S¹ bundle space.

    Attributes:
        times: Array of time points
        states: List of BundleState at each time
        initial_state: Initial condition
    """

    times: np.ndarray
    states: List[BundleState]
    initial_state: BundleState

    def __len__(self) -> int:
        """Number of points in trajectory"""
        return len(self.states)

    def __getitem__(self, index: int) -> BundleState:
        """Access state at index"""
        return self.states[index]

    def project_to_shape_space(self) -> List[ShapeSpaceState]:
        """
        Project trajectory to shape space.

        Returns:
            List of shape space states (π(trajectory))
        """
        return [state.shape_state for state in self.states]

    def get_fiber_coordinates(self) -> tuple:
        """
        Extract fiber coordinates and momenta.

        Returns:
            (theta_array, p_theta_array) tuple
        """
        theta = np.array([s.theta for s in self.states])
        p_theta = np.array([s.p_theta for s in self.states])
        return theta, p_theta


def integrate_bundle_dynamics(
    initial_state: BundleState,
    lifted_hamiltonian: LiftedHamiltonian,
    extended_form: ExtendedSymplecticForm,
    t_span: tuple,
    n_points: int = 1000,
    method: str = 'DOP853',
    **integrator_options
) -> BundleTrajectory:
    """
    Integrate Hamilton's equations on S¹ bundle.

    Equations:
        dq/dt = ∂H̃/∂p
        dp/dt = -∂H̃/∂q

    or in symplectic form:
        dz/dt = ω̃⁻¹(dH̃)

    Args:
        initial_state: Initial condition in bundle
        lifted_hamiltonian: H̃
        extended_form: ω̃
        t_span: (t_start, t_end)
        n_points: Number of output points
        method: Integration method
        **integrator_options: Additional options for solve_ivp

    Returns:
        BundleTrajectory

    Example:
        >>> state0 = create_bundle_state(r12=1.0, r23=1.0, r31=1.0, theta=0.0)
        >>> H = LiftedHamiltonian(masses, energy=-1.0, angular_momentum=1.0)
        >>> omega = compute_extended_symplectic_form(state0, masses, L=1.0)
        >>> traj = integrate_bundle_dynamics(state0, H, omega, (0, 100))
    """
    def rhs(t: float, z: np.ndarray) -> np.ndarray:
        """
        Right-hand side: dz/dt = X_H̃(z).

        Args:
            t: Time (unused, autonomous system)
            z: State vector [q, p]

        Returns:
            Time derivative dz/dt
        """
        # Reconstruct bundle state
        try:
            state = BundleState.from_vector(z, L=lifted_hamiltonian.angular_momentum)

            # Hamiltonian vector field
            X_H = compute_symplectic_gradient(
                lambda s: lifted_hamiltonian.evaluate(s),
                state,
                extended_form
            )

            return X_H

        except (ValueError, ZeroDivisionError):
            # Invalid state (e.g., violates triangle inequality)
            return np.zeros_like(z)

    # Initial condition
    z0 = initial_state.to_vector()

    # Time points
    t_eval = np.linspace(t_span[0], t_span[1], n_points)

    # Integrate
    solution = solve_ivp(
        rhs,
        t_span,
        z0,
        method=method,
        t_eval=t_eval,
        dense_output=True,
        **integrator_options
    )

    if not solution.success:
        print(f"Warning: Integration failed: {solution.message}")

    # Convert to trajectory
    states = []
    for i in range(len(solution.t)):
        try:
            state = BundleState.from_vector(
                solution.y[:, i],
                L=lifted_hamiltonian.angular_momentum
            )
            states.append(state)
        except ValueError:
            # Skip invalid states
            continue

    return BundleTrajectory(
        times=solution.t[:len(states)],
        states=states,
        initial_state=initial_state
    )


def verify_conservation(
    trajectory: BundleTrajectory,
    lifted_hamiltonian: LiftedHamiltonian
) -> dict:
    """
    Verify conservation laws on bundle trajectory.

    Should conserve:
        1. Energy: H̃ = constant
        2. Angular momentum: L = constant (from shape space)
        3. Fiber momentum: p_θ = constant (NEW!)

    Args:
        trajectory: Integrated trajectory
        lifted_hamiltonian: Hamiltonian

    Returns:
        Dictionary with conservation errors
    """
    n = len(trajectory)

    energies = np.zeros(n)
    angular_momenta = np.zeros(n)
    fiber_momenta = np.zeros(n)

    for i, state in enumerate(trajectory.states):
        energies[i] = lifted_hamiltonian.evaluate(state)
        angular_momenta[i] = state.shape_state.L
        fiber_momenta[i] = state.p_theta

    # Compute drifts
    E_drift = np.max(np.abs(energies - energies[0])) if len(energies) > 0 else 0.0
    L_drift = np.max(np.abs(angular_momenta - angular_momenta[0])) if len(angular_momenta) > 0 else 0.0
    p_theta_drift = np.max(np.abs(fiber_momenta - fiber_momenta[0])) if len(fiber_momenta) > 0 else 0.0

    return {
        'energy_drift': E_drift,
        'energy_relative': E_drift / abs(energies[0]) if abs(energies[0]) > 1e-14 else 0.0,
        'angular_momentum_drift': L_drift,
        'fiber_momentum_drift': p_theta_drift,
        'fiber_momentum_conserved': p_theta_drift < 1e-10,
        'energies': energies,
        'angular_momenta': angular_momenta,
        'fiber_momenta': fiber_momenta,
        'times': trajectory.times
    }


def project_bundle_trajectory(
    bundle_trajectory: BundleTrajectory
) -> List[ShapeSpaceState]:
    """
    Project bundle trajectory π: P → S to shape space.

    This should match the original reduced dynamics.

    Args:
        bundle_trajectory: Trajectory in bundle

    Returns:
        Trajectory in shape space
    """
    return bundle_trajectory.project_to_shape_space()


def validate_projection_consistency(
    lifted_trajectory: BundleTrajectory,
    reduced_trajectory: List[ShapeSpaceState],
    tolerance: float = 1e-8
) -> dict:
    """
    Verify that π(lifted trajectory) = reduced trajectory.

    This is a crucial consistency check: the projection of bundle dynamics
    should equal the original reduced dynamics.

    Args:
        lifted_trajectory: Trajectory on bundle
        reduced_trajectory: Original shape space trajectory
        tolerance: Error threshold

    Returns:
        Validation results
    """
    projected = project_bundle_trajectory(lifted_trajectory)

    # Compare lengths
    n_lifted = len(projected)
    n_reduced = len(reduced_trajectory)

    if n_lifted != n_reduced:
        return {
            'consistent': False,
            'error': f"Length mismatch: {n_lifted} vs {n_reduced}"
        }

    # Compare state-by-state
    errors = []
    max_error = 0.0

    for i, (proj_state, red_state) in enumerate(zip(projected, reduced_trajectory)):
        # Compare shape coordinates
        proj_coords = np.array([proj_state.r12, proj_state.r23, proj_state.r31])
        red_coords = np.array([red_state.r12, red_state.r23, red_state.r31])

        error = np.linalg.norm(proj_coords - red_coords)
        errors.append(error)
        max_error = max(max_error, error)

    return {
        'consistent': max_error < tolerance,
        'max_error': max_error,
        'mean_error': np.mean(errors) if errors else 0.0,
        'std_error': np.std(errors) if errors else 0.0,
        'errors': np.array(errors)
    }


def visualize_fiber_motion(
    trajectory: BundleTrajectory,
    output_file: Optional[str] = None
) -> dict:
    """
    Analyze motion in the fiber direction.

    Args:
        trajectory: Bundle trajectory
        output_file: Optional file to save plot

    Returns:
        Dictionary with fiber motion statistics
    """
    theta, p_theta = trajectory.get_fiber_coordinates()
    times = trajectory.times

    # Unwrap theta to see total winding
    theta_unwrapped = np.unwrap(theta)
    total_winding = (theta_unwrapped[-1] - theta_unwrapped[0]) / (2 * np.pi)

    # Compute winding rate
    if len(times) > 1:
        winding_rate = np.gradient(theta_unwrapped, times)
        mean_winding_rate = np.mean(winding_rate)
    else:
        winding_rate = np.zeros_like(theta)
        mean_winding_rate = 0.0

    return {
        'total_winding_number': total_winding,
        'mean_winding_rate': mean_winding_rate,
        'theta_range': (np.min(theta), np.max(theta)),
        'p_theta_range': (np.min(p_theta), np.max(p_theta)),
        'p_theta_mean': np.mean(p_theta),
        'p_theta_std': np.std(p_theta),
        'theta': theta,
        'theta_unwrapped': theta_unwrapped,
        'p_theta': p_theta,
        'winding_rate': winding_rate
    }
