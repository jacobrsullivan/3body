"""
Upstairs Variational Equations for Phase II Morales-Ramis Test.

This module computes Normal Variational Equations in LIFTED phase spaces
(S¹ bundle, KS-Spinor). This is the key component for the upstairs
Morales-Ramis compatibility test.

The upstairs NVE is computed by:
1. Lifting a downstairs periodic orbit to the extended space
2. Computing the variational equation in the lifted coordinates
3. Projecting to normal directions (perpendicular to lifted orbit)
4. Reducing to second-order form for Kovacic algorithm

Theoretical Background:
    In the lifted space (q, p, θ, p_θ), the variational equation is:
        d(δỹ)/dt = J̃ ∇²H̃(γ̃(t)) δỹ

    where:
    - γ̃(t) is the lifted periodic orbit
    - J̃ is the extended symplectic matrix
    - ∇²H̃ is the Hessian of the extended Hamiltonian (from Phase 4)

    The upstairs NVE is this VE restricted to normal directions.

References:
    - AMENDED_WP4.2, Task 4.2.4-4.2.5: Upstairs VE and Galois group
    - Section VI: Compatibility test via upstairs abelian structure
"""

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from typing import Tuple, Callable, Optional, Dict, List
from dataclasses import dataclass

from .periodic_orbits import PeriodicOrbit
from .variational_equations import VariationalEquationData, NormalVariationalEquation


@dataclass
class UpstirsOrbitData:
    """
    Data for a periodic orbit lifted to extended phase space.

    Attributes:
        downstairs_orbit: Original periodic orbit (base space)
        times: Time array
        upstairs_states: Lifted orbit states (q, p, θ, p_θ) or similar
        lift_type: Type of lift ('s1_bundle', 'ks_spinor')
        fiber_initial_conditions: Initial conditions in fiber (θ₀, p_θ₀)
        connection_values: Connection one-form evaluated along orbit (optional)
    """

    downstairs_orbit: PeriodicOrbit
    times: np.ndarray
    upstairs_states: np.ndarray
    lift_type: str
    fiber_initial_conditions: np.ndarray
    connection_values: Optional[np.ndarray] = None


@dataclass
class UpstirsVariationalEquationData:
    """
    Variational equation data in lifted space.

    Similar to VariationalEquationData but for extended coordinates.
    """

    lifted_orbit_data: UpstirsOrbitData
    times: np.ndarray
    extended_dimension: int
    """Dimension of extended phase space (2n + 2 for S¹, etc.)."""

    hessian_extended: Optional[np.ndarray] = None
    """Hessian ∇²H̃ evaluated along lifted orbit (if available)."""


@dataclass
class UpstirsNormalVariationalEquation:
    """
    Normal Variational Equation in lifted space.

    This is the upstairs NVE ready for Kovacic algorithm.
    """

    ve_data: UpstirsVariationalEquationData
    normal_directions: np.ndarray
    """Orthonormal basis for normal space (perpendicular to lifted orbit)."""

    reduced_dimension: int
    """Dimension after removing tangent direction."""

    tangent_direction: Optional[np.ndarray] = None
    """Tangent vector to lifted orbit (removed from NVE)."""


class UpstirsVariationalEquationComputer:
    """
    Compute variational equations in lifted phase spaces.

    This class handles:
    - Orbit lifting from downstairs to upstairs
    - Computation of upstairs VE using extended Hamiltonian
    - Projection to normal space (upstairs NVE)
    - Integration with symbolic lifts from Phase 4

    Supports:
    - S¹ bundle lift (primary)
    - KS-Spinor lift (TODO)
    """

    def __init__(
        self,
        extended_hamiltonian_symbolic: Optional[sp.Expr] = None,
        extended_coordinates: Optional[Tuple[sp.Symbol, ...]] = None,
        lift_type: str = 's1_bundle',
        numerical_mode: bool = True
    ):
        """
        Initialize upstairs VE computer.

        Args:
            extended_hamiltonian_symbolic: H̃ from Phase 4 symbolic lifts
            extended_coordinates: (q, p, θ, p_θ) symbolic variables
            lift_type: 's1_bundle' or 'ks_spinor'
            numerical_mode: If True, use numerical Hessian; if False, symbolic
        """
        self.H_extended_sym = extended_hamiltonian_symbolic
        self.extended_coords = extended_coordinates
        self.lift_type = lift_type
        self.numerical_mode = numerical_mode

        # For numerical mode, we'll compute Hessian via finite differences
        # For symbolic mode, we'll use SymPy differentiation

    def lift_orbit_to_s1_bundle(
        self,
        downstairs_orbit: PeriodicOrbit,
        theta_initial: float = 0.0,
        p_theta_initial: float = 0.0,
        n_points: int = 500,
        connection_type: str = 'minimal'
    ) -> UpstirsOrbitData:
        """
        Lift a downstairs periodic orbit to S¹ bundle.

        For minimal lift:
            - θ evolves according to: dθ/dt = ∂H̃/∂p_θ = p_θ
            - p_θ is conserved (Noether's theorem for S¹ symmetry)

        For magnetic lift:
            - θ evolves with connection: dθ/dt = p_θ + A(q, p)
            - p_θ may evolve depending on coupling

        Args:
            downstairs_orbit: Base orbit to lift
            theta_initial: Initial fiber coordinate θ₀
            p_theta_initial: Initial fiber momentum p_θ₀
            n_points: Number of points along orbit
            connection_type: 'minimal' or 'magnetic'

        Returns:
            UpstirsOrbitData with lifted orbit
        """
        # Integrate downstairs orbit
        from .variational_equations import VariationalEquationComputer

        # For simplicity, assume we have downstairs orbit data
        # In practice, would need to integrate or use provided data

        # Generate time array
        t_array = np.linspace(0, downstairs_orbit.period, n_points)

        # For minimal lift, the lifting is simple:
        # (q(t), p(t)) → (q(t), p(t), θ(t), p_θ)
        # where θ(t) = θ₀ + p_θ·t (for constant p_θ)

        # Placeholder: use initial condition directly
        # In full implementation, would integrate downstairs dynamics
        downstairs_dim = len(downstairs_orbit.initial_condition)

        # Create upstairs states array
        upstairs_states = np.zeros((n_points, downstairs_dim + 2))

        # Simple placeholder: constant downstairs state
        for i, t in enumerate(t_array):
            # Downstairs coordinates (would be integrated)
            upstairs_states[i, :downstairs_dim] = downstairs_orbit.initial_condition

            # Fiber coordinates
            if connection_type == 'minimal':
                # θ(t) = θ₀ + p_θ·t
                theta_t = theta_initial + p_theta_initial * t
                p_theta_t = p_theta_initial  # Conserved
            else:
                # Would need to integrate with connection
                theta_t = theta_initial
                p_theta_t = p_theta_initial

            upstairs_states[i, downstairs_dim] = theta_t
            upstairs_states[i, downstairs_dim + 1] = p_theta_t

        fiber_ic = np.array([theta_initial, p_theta_initial])

        return UpstirsOrbitData(
            downstairs_orbit=downstairs_orbit,
            times=t_array,
            upstairs_states=upstairs_states,
            lift_type='s1_bundle',
            fiber_initial_conditions=fiber_ic,
            connection_values=None
        )

    def compute_upstairs_variational_equation(
        self,
        lifted_orbit_data: UpstirsOrbitData,
        hamiltonian_numerical: Optional[Callable] = None
    ) -> UpstirsVariationalEquationData:
        """
        Compute variational equation in lifted space.

        d(δỹ)/dt = J̃ ∇²H̃(γ̃(t)) δỹ

        Args:
            lifted_orbit_data: Lifted orbit from lift_orbit_to_s1_bundle
            hamiltonian_numerical: Optional numerical H̃ function

        Returns:
            UpstirsVariationalEquationData
        """
        n_points = len(lifted_orbit_data.times)
        extended_dim = lifted_orbit_data.upstairs_states.shape[1]

        # Compute Hessian along lifted orbit
        if self.numerical_mode:
            # Numerical Hessian via finite differences
            hessian_array = np.zeros((n_points, extended_dim, extended_dim))

            for i, state in enumerate(lifted_orbit_data.upstairs_states):
                if hamiltonian_numerical:
                    hess_i = self._compute_hessian_numerical(
                        hamiltonian_numerical, state
                    )
                    hessian_array[i] = hess_i
                else:
                    # Placeholder: identity
                    hessian_array[i] = np.eye(extended_dim)
        else:
            # Symbolic Hessian (requires SymPy from Phase 4)
            if self.H_extended_sym is not None:
                # Compute symbolically then evaluate
                hessian_array = self._compute_hessian_symbolic(lifted_orbit_data)
            else:
                raise ValueError("Symbolic mode requires H_extended_sym")

        return UpstirsVariationalEquationData(
            lifted_orbit_data=lifted_orbit_data,
            times=lifted_orbit_data.times,
            extended_dimension=extended_dim,
            hessian_extended=hessian_array
        )

    def compute_upstairs_normal_variational_equation(
        self,
        upstairs_ve_data: UpstirsVariationalEquationData
    ) -> UpstirsNormalVariationalEquation:
        """
        Compute Normal Variational Equation in lifted space.

        Projects VE to directions perpendicular to lifted orbit.

        Args:
            upstairs_ve_data: Upstairs VE data

        Returns:
            UpstirsNormalVariationalEquation ready for Kovacic
        """
        # Compute tangent vector to lifted orbit
        lifted_states = upstairs_ve_data.lifted_orbit_data.upstairs_states
        times = upstairs_ve_data.times

        # Numerical derivative to get tangent
        tangent_vectors = np.gradient(lifted_states, times, axis=0)

        # Normalize (approximately)
        tangent_norms = np.linalg.norm(tangent_vectors, axis=1, keepdims=True)
        tangent_normalized = tangent_vectors / (tangent_norms + 1e-12)

        # Compute normal space (orthogonal complement to tangent)
        n_points, extended_dim = lifted_states.shape

        # For each point, construct orthonormal basis for normal space
        # Using QR decomposition approach
        normal_directions = np.zeros((n_points, extended_dim, extended_dim - 1))

        for i in range(n_points):
            # Start with standard basis
            basis = np.eye(extended_dim)

            # Remove tangent component from each basis vector
            tangent_i = tangent_normalized[i]

            normal_basis = []
            for j in range(extended_dim):
                v = basis[:, j]
                # Project out tangent: v - (v·t)t
                v_normal = v - np.dot(v, tangent_i) * tangent_i

                if np.linalg.norm(v_normal) > 1e-10:
                    normal_basis.append(v_normal / np.linalg.norm(v_normal))

            # Take first (extended_dim - 1) orthonormal vectors
            normal_basis_array = np.column_stack(normal_basis[:extended_dim - 1])
            normal_directions[i] = normal_basis_array

        reduced_dim = extended_dim - 1

        return UpstirsNormalVariationalEquation(
            ve_data=upstairs_ve_data,
            normal_directions=normal_directions,
            reduced_dimension=reduced_dim,
            tangent_direction=tangent_normalized
        )

    def _compute_hessian_numerical(
        self,
        H_func: Callable,
        state: np.ndarray,
        eps: float = 1e-7
    ) -> np.ndarray:
        """
        Compute Hessian numerically via finite differences.

        Args:
            H_func: Hamiltonian function
            state: State at which to evaluate
            eps: Finite difference step

        Returns:
            Hessian matrix
        """
        n = len(state)
        hess = np.zeros((n, n))

        H_0 = H_func(state)

        for i in range(n):
            for j in range(i, n):
                # Compute ∂²H/∂xᵢ∂xⱼ using central differences
                state_ij = state.copy()
                state_ij[i] += eps
                state_ij[j] += eps
                H_ij = H_func(state_ij)

                state_i = state.copy()
                state_i[i] += eps
                H_i = H_func(state_i)

                state_j = state.copy()
                state_j[j] += eps
                H_j = H_func(state_j)

                hess[i, j] = (H_ij - H_i - H_j + H_0) / (eps**2)
                hess[j, i] = hess[i, j]  # Symmetry

        return hess

    def _compute_hessian_symbolic(
        self,
        lifted_orbit_data: UpstirsOrbitData
    ) -> np.ndarray:
        """
        Compute Hessian symbolically using SymPy, then evaluate.

        Args:
            lifted_orbit_data: Lifted orbit

        Returns:
            Hessian array evaluated along orbit
        """
        if self.H_extended_sym is None or self.extended_coords is None:
            raise ValueError("Symbolic mode requires H_extended_sym and extended_coords")

        # Compute symbolic Hessian
        from ..symbolic_lifts.common import compute_hessian

        hess_sym = compute_hessian(self.H_extended_sym, self.extended_coords)

        # Evaluate along orbit
        n_points = len(lifted_orbit_data.times)
        extended_dim = lifted_orbit_data.upstairs_states.shape[1]

        hess_array = np.zeros((n_points, extended_dim, extended_dim))

        for i, state in enumerate(lifted_orbit_data.upstairs_states):
            # Substitute state values
            subs_dict = dict(zip(self.extended_coords, state))
            hess_numerical = np.array(hess_sym.subs(subs_dict).evalf()).astype(float)
            hess_array[i] = hess_numerical

        return hess_array


def integrate_upstairs_nve(
    upstairs_nve: UpstirsNormalVariationalEquation,
    initial_perturbation: np.ndarray,
    t_span: Tuple[float, float],
    rtol: float = 1e-12
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Integrate upstairs Normal Variational Equation.

    This evolves perturbations in normal space according to the linearized
    dynamics in the lifted phase space.

    Args:
        upstairs_nve: Upstairs NVE to integrate
        initial_perturbation: Initial δỹ (in normal space)
        t_span: (t_initial, t_final)
        rtol: Relative tolerance

    Returns:
        (times, perturbations) evolution of δỹ(t)
    """
    # Extract data
    times_ref = upstairs_nve.ve_data.times
    hessian_array = upstairs_nve.ve_data.hessian_extended
    normal_dirs = upstairs_nve.normal_directions

    # Interpolate Hessian and normal directions
    # (Simplified - would need proper interpolation)

    def nve_rhs(t, delta_y):
        """Right-hand side of NVE."""
        # Find nearest time index
        idx = np.searchsorted(times_ref, t)
        idx = min(idx, len(times_ref) - 1)

        # Get Hessian and normal basis at this time
        hess_t = hessian_array[idx]
        normal_t = normal_dirs[idx]

        # Symplectic matrix (extended)
        extended_dim = hess_t.shape[0]
        n = extended_dim // 2
        I = np.eye(n)
        J_extended = np.block([[np.zeros((n, n)), I], [-I, np.zeros((n, n))]])

        # VE in full space: d(δy)/dt = J·H''·δy
        # Project to normal space
        delta_y_full = normal_t @ delta_y
        d_delta_y_full = J_extended @ hess_t @ delta_y_full

        # Project back to normal space
        d_delta_y = normal_t.T @ d_delta_y_full

        return d_delta_y

    # Integrate
    sol = solve_ivp(
        nve_rhs,
        t_span,
        initial_perturbation,
        method='DOP853',
        rtol=rtol,
        atol=rtol * 1e-3,
        dense_output=True
    )

    return sol.t, sol.y.T


def convert_upstairs_nve_to_symbolic(
    upstairs_nve: UpstirsNormalVariationalEquation,
    fit_method: str = 'polynomial',
    max_degree: int = 4
) -> Optional[Tuple[sp.Expr, sp.Expr]]:
    """
    Convert numerical upstairs NVE to symbolic form for Kovacic algorithm.

    This is challenging because NVE coefficients are time-dependent periodic
    functions. We attempt to fit them to known function families.

    Args:
        upstairs_nve: Numerical upstairs NVE
        fit_method: 'polynomial', 'rational', or 'fourier'
        max_degree: Maximum degree for fits

    Returns:
        (a(t), b(t)) for y'' + a(t)y' + b(t)y = 0, or None if fitting fails

    Note:
        This is a research-level problem. For production use, would need
        sophisticated symbolic regression (PySR, SINDy, etc.)
    """
    # Placeholder: This requires implementing symbolic regression
    # For now, return None to indicate conversion not available

    # In practice, for specific orbits (e.g., Lagrange L4), the upstairs NVE
    # might have a known form that can be derived analytically from the
    # symbolic extended Hamiltonian.

    return None


# Integration with Phase 4 symbolic lifts
def create_upstairs_ve_computer_for_s1_cr3bp(
    mu_value: float = 0.012
) -> UpstirsVariationalEquationComputer:
    """
    Create upstairs VE computer pre-configured for S¹ bundle CR3BP.

    Uses symbolic Hamiltonian from Phase 4.

    Args:
        mu_value: Mass ratio

    Returns:
        Configured UpstirsVariationalEquationComputer

    Example:
        >>> computer = create_upstairs_ve_computer_for_s1_cr3bp(mu=0.012)
        >>> # Lift orbit
        >>> lifted = computer.lift_orbit_to_s1_bundle(orbit)
        >>> # Compute upstairs NVE
        >>> upstairs_nve = computer.compute_upstairs_normal_variational_equation(...)
    """
    from ..symbolic_lifts.s1_symbolic import prepare_s1_for_upstairs_mr_test

    # Get symbolic S¹ system
    s1_data = prepare_s1_for_upstairs_mr_test(mu_value=mu_value)

    computer = UpstirsVariationalEquationComputer(
        extended_hamiltonian_symbolic=s1_data['hamiltonian'],
        extended_coordinates=s1_data['coordinates'],
        lift_type='s1_bundle',
        numerical_mode=False  # Use symbolic from Phase 4
    )

    return computer
