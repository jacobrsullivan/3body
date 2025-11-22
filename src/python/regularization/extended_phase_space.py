"""
Extended phase space data structures with time regularization.

Implements the complete (4+1)-dimensional KS lift with explicit tracking
of both fictitious time (s) and physical time (t), along with their
conjugate energies (K and E).

Mathematical Framework:
    Extended phase space: (u, p_u, s, K, t, E) ∈ R^10
    - u ∈ R^4: KS spinor (spatial configuration)
    - p_u ∈ R^4: Spinor momenta
    - s ∈ R: Fictitious time (integration parameter)
    - K ∈ R: Regularized energy (conjugate to s)
    - t ∈ R: Physical time (observer's clock)
    - E ∈ R: Physical energy (conserved Hamiltonian)

Key Relations:
    - dt/ds = Ω(u) = ‖u‖² (time transformation)
    - K = E · Ω(u) (energy-time consistency)
    - r = ‖u‖² (bilinear relation)

References:
    - AMENDED_KS-Symplectic-Reduction-Conjectural-Statement.md
    - AMENDED_WP2.3-KS-Spinor-Lift-Implementation-Plan.md
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import warnings

from .spinor_vector import SpinorVector


@dataclass(frozen=True)
class ExtendedKSState:
    """
    Complete KS state including both spatial and temporal variables.

    This represents a point in the extended phase space:
        (u, p_u, s, K, t, E) ∈ T*R^4 × T*R

    Attributes:
        u: SpinorVector — 4D spinor (spatial configuration)
        p_u: SpinorVector — Conjugate spinor momenta
        s: float — Fictitious time (regularized clock)
        K: float — Regularized energy (conjugate to s)
        t: float — Physical time (observer's clock)
        E: float — Physical energy (conserved Hamiltonian)

    Constraints:
        - Bilinear: ‖u‖² ≈ r (physical radius)
        - Energy: K ≈ E · ‖u‖² (energy scaling with time dilation)
        - Time relation: dt/ds = ‖u‖²

    Example:
        >>> u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))
        >>> p_u = SpinorVector(np.array([0.0, 0.5, 0.0, 0.0]))
        >>> state = ExtendedKSState(u, p_u, s=0.0, K=-0.5, t=0.0, E=-0.5)
        >>> state.time_dilation_factor  # Should be 1.0
        1.0
        >>> state.validate_time_relation()  # Should be True
        True
    """

    u: SpinorVector
    p_u: SpinorVector
    s: float
    K: float
    t: float
    E: float

    def __post_init__(self):
        """Validate physical constraints on initialization"""
        # Check energy relation with tolerance
        time_dilation = self.u.norm_squared
        expected_K = self.E * time_dilation

        # Allow some numerical tolerance
        if abs(self.K - expected_K) > 1e-8:
            warnings.warn(
                f"Energy constraint violation at initialization: "
                f"K = {self.K:.6e}, E·Ω = {expected_K:.6e}, "
                f"difference = {abs(self.K - expected_K):.6e}"
            )

    @property
    def time_dilation_factor(self) -> float:
        """
        Time dilation factor Ω = dt/ds = ‖u‖².

        This is the "clock ratio" between physical and fictitious time.
        As u → 0 (collision), time dilation → 0 (time slows down).
        """
        return self.u.norm_squared

    @property
    def physical_radius(self) -> float:
        """Physical radius r = ‖u‖² (from bilinear relation)"""
        return self.u.norm_squared

    def to_vector(self) -> np.ndarray:
        """
        Flatten to vector for integration.

        Returns:
            [u₀, u₁, u₂, u₃, p_u₀, p_u₁, p_u₂, p_u₃, s, K, t, E]
            (12-dimensional state vector)
        """
        return np.concatenate([
            self.u.components,
            self.p_u.components,
            [self.s, self.K, self.t, self.E]
        ])

    @classmethod
    def from_vector(cls, state_vec: np.ndarray) -> 'ExtendedKSState':
        """
        Construct from flat array.

        Args:
            state_vec: Array of length 12

        Returns:
            ExtendedKSState
        """
        if len(state_vec) != 12:
            raise ValueError(f"Extended KS state must be 12D, got {len(state_vec)}")

        u = SpinorVector(state_vec[0:4])
        p_u = SpinorVector(state_vec[4:8])
        s, K, t, E = state_vec[8:12]

        return cls(u=u, p_u=p_u, s=s, K=K, t=t, E=E)

    def validate_time_relation(self, tol: float = 1e-10) -> bool:
        """
        Check if time-energy relation is satisfied: K = E · ‖u‖²

        This is the consistency condition from dt/ds = ‖u‖².

        Args:
            tol: Numerical tolerance

        Returns:
            True if relation is satisfied within tolerance
        """
        lhs = self.K
        rhs = self.E * self.u.norm_squared
        return abs(lhs - rhs) < tol

    def validate_bilinear_relation(self, r_expected: Optional[float] = None, tol: float = 1e-10) -> bool:
        """
        Check bilinear relation: r = ‖u‖²

        Args:
            r_expected: Expected physical radius (optional)
            tol: Numerical tolerance

        Returns:
            True if relation satisfied
        """
        r_from_spinor = self.u.norm_squared

        if r_expected is not None:
            return abs(r_from_spinor - r_expected) < tol

        # If no expected value, just check it's positive
        return r_from_spinor > 0

    def validate_all_constraints(self, tol: float = 1e-10) -> dict:
        """
        Validate all physical constraints.

        Returns:
            Dictionary with validation results
        """
        results = {
            'time_energy_consistent': self.validate_time_relation(tol),
            'bilinear_satisfied': self.validate_bilinear_relation(tol=tol),
            'time_dilation_positive': self.time_dilation_factor > 0,
            'K_value': self.K,
            'E_value': self.E,
            'Omega_value': self.time_dilation_factor,
            'K_expected': self.E * self.time_dilation_factor,
            'K_error': abs(self.K - self.E * self.time_dilation_factor)
        }

        results['all_constraints_satisfied'] = (
            results['time_energy_consistent'] and
            results['bilinear_satisfied'] and
            results['time_dilation_positive']
        )

        return results

    def with_updated_time(self, ds: float) -> 'ExtendedKSState':
        """
        Advance time coordinates by fictitious time step ds.

        Updates:
            - s → s + ds (fictitious time advances)
            - t → t + Ω(u)·ds (physical time advances)
            - K updated to maintain K = E·Ω
            - E remains constant (conserved)

        Args:
            ds: Fictitious time step

        Returns:
            New state with updated times
        """
        Omega = self.time_dilation_factor
        dt = Omega * ds

        s_new = self.s + ds
        t_new = self.t + dt
        K_new = self.E * Omega  # Maintain consistency
        E_new = self.E  # Conserved

        return ExtendedKSState(
            u=self.u,
            p_u=self.p_u,
            s=s_new,
            K=K_new,
            t=t_new,
            E=E_new
        )

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"ExtendedKSState(\n"
            f"  u={self.u.components},\n"
            f"  p_u={self.p_u.components},\n"
            f"  s={self.s:.6f}, K={self.K:.6f},\n"
            f"  t={self.t:.6f}, E={self.E:.6f},\n"
            f"  Ω=dt/ds={self.time_dilation_factor:.6f}\n"
            f")"
        )


def create_extended_ks_state(
    u: np.ndarray,
    p_u: np.ndarray,
    s: float = 0.0,
    t: float = 0.0,
    E: float = 0.0,
    compute_K: bool = True
) -> ExtendedKSState:
    """
    Create ExtendedKSState with automatic K computation.

    Args:
        u: Spinor coordinates (4D array)
        p_u: Spinor momenta (4D array)
        s: Fictitious time
        t: Physical time
        E: Physical energy
        compute_K: If True, compute K = E·‖u‖² automatically

    Returns:
        ExtendedKSState
    """
    u_spinor = SpinorVector(u)
    p_u_spinor = SpinorVector(p_u)

    if compute_K:
        Omega = u_spinor.norm_squared
        K = E * Omega
    else:
        K = 0.0

    return ExtendedKSState(
        u=u_spinor,
        p_u=p_u_spinor,
        s=s,
        K=K,
        t=t,
        E=E
    )


def compute_time_dilation_history(
    trajectory: list[ExtendedKSState]
) -> np.ndarray:
    """
    Extract time dilation factors along a trajectory.

    Args:
        trajectory: List of ExtendedKSState

    Returns:
        Array of Ω(s) values
    """
    return np.array([state.time_dilation_factor for state in trajectory])


def compute_energy_drift(
    trajectory: list[ExtendedKSState]
) -> dict:
    """
    Compute energy conservation along trajectory.

    Monitors both:
        - E (physical energy, should be exactly conserved)
        - K (regularized energy, should follow K = E·Ω)

    Args:
        trajectory: List of ExtendedKSState

    Returns:
        Dictionary with drift statistics
    """
    n = len(trajectory)

    E_values = np.array([s.E for s in trajectory])
    K_values = np.array([s.K for s in trajectory])
    Omega_values = np.array([s.time_dilation_factor for s in trajectory])

    # Expected K from energy relation
    K_expected = E_values * Omega_values

    # Compute drifts
    E_drift = np.max(np.abs(E_values - E_values[0]))
    K_drift = np.max(np.abs(K_values - K_expected))

    return {
        'E_initial': E_values[0],
        'E_final': E_values[-1],
        'E_drift': E_drift,
        'E_relative_drift': E_drift / abs(E_values[0]) if E_values[0] != 0 else float('inf'),
        'E_conserved': E_drift < 1e-12,
        'K_drift_from_relation': K_drift,
        'K_relation_satisfied': K_drift < 1e-10,
        'max_Omega': np.max(Omega_values),
        'min_Omega': np.min(Omega_values),
        'Omega_range': np.max(Omega_values) - np.min(Omega_values)
    }


def validate_extended_trajectory(
    trajectory: list[ExtendedKSState],
    verbose: bool = False
) -> dict:
    """
    Comprehensive validation of extended KS trajectory.

    Checks:
        1. Energy conservation (E)
        2. Time-energy relation (K = E·Ω)
        3. Time monotonicity (s and t increasing)
        4. Physical constraints at each point

    Args:
        trajectory: List of ExtendedKSState
        verbose: Print detailed results

    Returns:
        Validation results dictionary
    """
    if len(trajectory) < 2:
        raise ValueError("Trajectory must have at least 2 points")

    # Energy analysis
    energy_stats = compute_energy_drift(trajectory)

    # Time monotonicity
    s_values = np.array([state.s for state in trajectory])
    t_values = np.array([state.t for state in trajectory])

    s_monotonic = np.all(np.diff(s_values) > 0)
    t_monotonic = np.all(np.diff(t_values) >= 0)  # Can have dt=0 at collision

    # Point-by-point constraint validation
    constraint_violations = []
    for i, state in enumerate(trajectory):
        validation = state.validate_all_constraints()
        if not validation['all_constraints_satisfied']:
            constraint_violations.append({
                'index': i,
                's': state.s,
                'validation': validation
            })

    results = {
        'trajectory_length': len(trajectory),
        's_range': (s_values[0], s_values[-1]),
        't_range': (t_values[0], t_values[-1]),
        's_monotonic': s_monotonic,
        't_monotonic': t_monotonic,
        'energy_stats': energy_stats,
        'num_constraint_violations': len(constraint_violations),
        'constraint_violations': constraint_violations[:5],  # First 5 only
        'trajectory_valid': (
            s_monotonic and
            t_monotonic and
            energy_stats['E_conserved'] and
            energy_stats['K_relation_satisfied'] and
            len(constraint_violations) == 0
        )
    }

    if verbose:
        print("="*60)
        print("Extended KS Trajectory Validation")
        print("="*60)
        print(f"Trajectory length: {results['trajectory_length']}")
        print(f"s range: {results['s_range']}")
        print(f"t range: {results['t_range']}")
        print(f"\nTime monotonicity:")
        print(f"  s monotonic: {results['s_monotonic']}")
        print(f"  t monotonic: {results['t_monotonic']}")
        print(f"\nEnergy conservation:")
        print(f"  E drift: {energy_stats['E_drift']:.2e}")
        print(f"  E conserved: {energy_stats['E_conserved']}")
        print(f"  K-E relation satisfied: {energy_stats['K_relation_satisfied']}")
        print(f"\nConstraints:")
        print(f"  Violations: {results['num_constraint_violations']}")
        print(f"\nOverall valid: {results['trajectory_valid']}")
        print("="*60)

    return results
