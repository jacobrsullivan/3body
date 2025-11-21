"""
Variational Equation Computation (WP 4.2, Tasks 4.2.1 and 4.2.4).

Computes Normal Variational Equations (NVE) for periodic orbits, both
"downstairs" (original coordinates) and "upstairs" (lifted coordinates).

The variational equation describes linearized dynamics around a reference
solution. For Hamiltonian systems, it has special structure due to symplectic
geometry.

Mathematical Background:
=======================

Given a Hamiltonian H(q,p) and reference solution γ(t) = (q₀(t), p₀(t)),
the Variational Equation (VE) for perturbations δy = (δq, δp) is:

    d(δy)/dt = J ∇²H|_{γ(t)} δy

where J is the symplectic matrix and ∇²H is the Hessian of H.

The Normal Variational Equation (NVE) is the VE projected to directions
perpendicular to the orbit (removing the trivial tangent direction).

For a periodic orbit with period T, the monodromy matrix M = Φ(T) determines
stability. The differential Galois group of the NVE determines integrability
via the Morales-Ramis criterion.

References:
- Morales-Ruiz & Ramis, "Galoisian obstructions to integrability" (1999)
- Hairer, Lubich, Wanner, "Geometric Numerical Integration" (2006)
- Meyer & Hall, "Introduction to Hamiltonian Dynamical Systems" (1992)
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, List
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import qr, svd, null_space

from .periodic_orbits import PeriodicOrbit


@dataclass(frozen=True)
class VariationalEquationData:
    """
    Data structure for variational equation along an orbit.

    Attributes:
        reference_orbit: The periodic orbit being analyzed
        times: Time points along orbit
        states: State trajectory (n_points, 2n)
        hessians: Hessian matrices ∇²H at each time point
        phase_space_dim: Dimension of phase space (2n)
        config_space_dim: Dimension of configuration space (n)
    """
    reference_orbit: PeriodicOrbit
    times: np.ndarray
    states: np.ndarray
    hessians: Optional[np.ndarray] = None  # (n_points, 2n, 2n)
    phase_space_dim: int = 0
    config_space_dim: int = 0

    def __post_init__(self):
        """Compute derived quantities."""
        if self.phase_space_dim == 0:
            dim = len(self.reference_orbit.initial_condition)
            object.__setattr__(self, 'phase_space_dim', dim)
            object.__setattr__(self, 'config_space_dim', dim // 2)


@dataclass(frozen=True)
class NormalVariationalEquation:
    """
    Normal Variational Equation (perpendicular to orbit).

    The NVE is the VE projected to the normal space, removing the
    trivial tangent direction along the orbit.

    Attributes:
        ve_data: Full variational equation data
        normal_directions: Orthonormal basis for normal space (2n-1 vectors)
        reduced_dimension: Dimension of normal space (2n-1)
        tangent_direction: Unit tangent to orbit (for reference)
    """
    ve_data: VariationalEquationData
    normal_directions: np.ndarray  # (n_points, 2n, 2n-1)
    reduced_dimension: int
    tangent_direction: Optional[np.ndarray] = None  # (n_points, 2n)


class VariationalEquationComputer:
    """
    Compute variational equations for Hamiltonian systems.

    This class handles both numerical and symbolic computation of
    variational equations, Hessians, and normal projections.
    """

    def __init__(
        self,
        hamiltonian: Callable[[np.ndarray], float],
        gradient: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        hessian: Optional[Callable[[np.ndarray], np.ndarray]] = None
    ):
        """
        Initialize variational equation computer.

        Args:
            hamiltonian: H(q,p) → scalar
            gradient: ∇H(q,p) → (2n,) [optional, will use finite diff if not provided]
            hessian: ∇²H(q,p) → (2n, 2n) [optional, will use finite diff if not provided]
        """
        self.H = hamiltonian
        self.grad_H = gradient
        self.hess_H = hessian

    def compute_reference_orbit(
        self,
        orbit: PeriodicOrbit,
        n_periods: float = 1.0,
        n_points: int = 500,
        **integrator_kwargs
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrate reference periodic orbit.

        Args:
            orbit: Periodic orbit specification
            n_periods: Number of periods to integrate
            n_points: Number of output points
            **integrator_kwargs: Options for scipy.integrate.solve_ivp

        Returns:
            times: Time array (n_points,)
            states: State array (n_points, 2n)
        """
        def hamilton_rhs(t, y):
            """Hamilton's equations: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q"""
            n = len(y) // 2

            if self.grad_H is not None:
                grad = self.grad_H(y)
                dq_dt = grad[n:]   # ∂H/∂p
                dp_dt = -grad[:n]  # -∂H/∂q
            else:
                # Numerical gradient
                eps = 1e-8
                dH_dq = np.zeros(n)
                dH_dp = np.zeros(n)
                H_0 = self.H(y)

                for i in range(n):
                    y_plus = y.copy()
                    y_plus[i] += eps
                    dH_dq[i] = (self.H(y_plus) - H_0) / eps

                    y_plus = y.copy()
                    y_plus[n + i] += eps
                    dH_dp[i] = (self.H(y_plus) - H_0) / eps

                dq_dt = dH_dp
                dp_dt = -dH_dq

            return np.concatenate([dq_dt, dp_dt])

        # Integration settings
        t_final = orbit.period * n_periods
        t_eval = np.linspace(0, t_final, n_points)

        defaults = {
            'method': 'DOP853',
            'rtol': 1e-12,
            'atol': 1e-14
        }
        defaults.update(integrator_kwargs)

        # Integrate
        sol = solve_ivp(
            hamilton_rhs,
            (0, t_final),
            orbit.initial_condition,
            t_eval=t_eval,
            **defaults
        )

        if not sol.success:
            raise RuntimeError(f"Orbit integration failed: {sol.message}")

        return sol.t, sol.y.T

    def compute_hessian_numerical(
        self,
        state: np.ndarray,
        eps: float = 1e-7
    ) -> np.ndarray:
        """
        Compute Hessian ∇²H numerically via finite differences.

        Args:
            state: Phase space point (2n,)
            eps: Finite difference step size

        Returns:
            Hessian matrix (2n, 2n)
        """
        n = len(state) // 2
        dim = 2 * n
        hess = np.zeros((dim, dim))

        # Central differences: ∂²H/∂x_i∂x_j ≈ [H(x+e_i+e_j) - H(x+e_i) - H(x+e_j) + H(x)] / eps²

        H_0 = self.H(state)

        # First-order terms: H(x + e_i)
        H_plus = np.zeros(dim)
        for i in range(dim):
            state_plus = state.copy()
            state_plus[i] += eps
            H_plus[i] = self.H(state_plus)

        # Second-order terms: H(x + e_i + e_j)
        for i in range(dim):
            for j in range(i, dim):
                state_plus = state.copy()
                state_plus[i] += eps
                state_plus[j] += eps
                H_plus_ij = self.H(state_plus)

                # Hessian element
                if i == j:
                    # Diagonal: ∂²H/∂x_i² ≈ [H(x+2e_i) - 2H(x+e_i) + H(x)] / eps²
                    state_plus2 = state.copy()
                    state_plus2[i] += 2*eps
                    H_plus2 = self.H(state_plus2)
                    hess[i, i] = (H_plus2 - 2*H_plus[i] + H_0) / (eps**2)
                else:
                    # Off-diagonal: ∂²H/∂x_i∂x_j ≈ [H(x+e_i+e_j) - H(x+e_i) - H(x+e_j) + H(x)] / eps²
                    hess[i, j] = (H_plus_ij - H_plus[i] - H_plus[j] + H_0) / (eps**2)
                    hess[j, i] = hess[i, j]  # Symmetric

        return hess

    def compute_hessians_along_orbit(
        self,
        states: np.ndarray,
        eps: float = 1e-7
    ) -> np.ndarray:
        """
        Compute Hessian at each point along orbit.

        Args:
            states: State trajectory (n_points, 2n)
            eps: Finite difference step size (if using numerical)

        Returns:
            Hessians (n_points, 2n, 2n)
        """
        n_points = len(states)
        dim = states.shape[1]
        hessians = np.zeros((n_points, dim, dim))

        for i, state in enumerate(states):
            if self.hess_H is not None:
                hessians[i] = self.hess_H(state)
            else:
                hessians[i] = self.compute_hessian_numerical(state, eps)

        return hessians

    def compute_variational_equation(
        self,
        orbit: PeriodicOrbit,
        n_points: int = 500
    ) -> VariationalEquationData:
        """
        Compute full variational equation data along orbit.

        Args:
            orbit: Periodic orbit
            n_points: Number of evaluation points

        Returns:
            VariationalEquationData containing orbit and Hessians
        """
        # Integrate reference orbit
        times, states = self.compute_reference_orbit(orbit, n_periods=1.0, n_points=n_points)

        # Compute Hessians along orbit
        hessians = self.compute_hessians_along_orbit(states)

        return VariationalEquationData(
            reference_orbit=orbit,
            times=times,
            states=states,
            hessians=hessians
        )

    def compute_tangent_direction(
        self,
        times: np.ndarray,
        states: np.ndarray
    ) -> np.ndarray:
        """
        Compute tangent vector to orbit (velocity along orbit).

        Args:
            times: Time points
            states: State trajectory

        Returns:
            Tangent vectors (n_points, 2n), normalized
        """
        # Tangent = dγ/dt (velocity along orbit)
        # Use numerical derivative

        n_points = len(times)
        dim = states.shape[1]
        tangents = np.zeros((n_points, dim))

        # Central differences for interior points
        for i in range(1, n_points - 1):
            dt_fwd = times[i+1] - times[i]
            dt_bwd = times[i] - times[i-1]
            tangents[i] = (states[i+1] - states[i-1]) / (dt_fwd + dt_bwd)

        # Forward/backward differences for endpoints
        tangents[0] = (states[1] - states[0]) / (times[1] - times[0])
        tangents[-1] = (states[-1] - states[-2]) / (times[-1] - times[-2])

        # Normalize
        for i in range(n_points):
            norm = np.linalg.norm(tangents[i])
            if norm > 1e-10:
                tangents[i] /= norm

        return tangents

    def compute_normal_directions(
        self,
        tangent: np.ndarray
    ) -> np.ndarray:
        """
        Compute orthonormal basis for normal space (perpendicular to tangent).

        Uses QR decomposition to find orthonormal complement.

        Args:
            tangent: Tangent vector (2n,), assumed normalized

        Returns:
            Normal basis (2n, 2n-1): columns are orthonormal normal vectors
        """
        dim = len(tangent)

        # Start with tangent as first column
        # Complete to full basis using QR decomposition

        # Create random matrix with tangent as first column
        A = np.random.randn(dim, dim)
        A[:, 0] = tangent

        # QR decomposition
        Q, _ = qr(A)

        # Q[:, 0] is now normalized tangent
        # Q[:, 1:] are orthonormal normals
        normal_basis = Q[:, 1:]

        return normal_basis

    def compute_normal_variational_equation(
        self,
        orbit: PeriodicOrbit,
        n_points: int = 500
    ) -> NormalVariationalEquation:
        """
        Compute Normal Variational Equation (projected to normal space).

        This removes the trivial tangent direction, reducing from 2n to 2n-1 dimensions.

        Args:
            orbit: Periodic orbit
            n_points: Number of evaluation points

        Returns:
            NormalVariationalEquation with normal projection data
        """
        # Compute full VE
        ve_data = self.compute_variational_equation(orbit, n_points)

        # Compute tangent direction
        tangents = self.compute_tangent_direction(ve_data.times, ve_data.states)

        # Compute normal directions at each point
        n_points_actual = len(ve_data.times)
        dim = ve_data.phase_space_dim
        normal_directions = np.zeros((n_points_actual, dim, dim - 1))

        for i in range(n_points_actual):
            normal_directions[i] = self.compute_normal_directions(tangents[i])

        return NormalVariationalEquation(
            ve_data=ve_data,
            normal_directions=normal_directions,
            reduced_dimension=dim - 1,
            tangent_direction=tangents
        )

    def integrate_variational_equation(
        self,
        ve_data: VariationalEquationData,
        initial_perturbation: np.ndarray,
        **integrator_kwargs
    ) -> np.ndarray:
        """
        Integrate variational equation for given initial perturbation.

        Solves: d(δy)/dt = J ∇²H(γ(t)) δy

        Args:
            ve_data: Variational equation data
            initial_perturbation: δy(0) ∈ ℝ^{2n}
            **integrator_kwargs: Options for integrator

        Returns:
            Perturbation evolution δy(t) (n_points, 2n)
        """
        n = ve_data.config_space_dim
        dim = 2 * n

        # Symplectic matrix J
        I = np.eye(n)
        J = np.block([[np.zeros((n, n)), I],
                      [-I, np.zeros((n, n))]])

        # Interpolate Hessians for time-dependent VE
        from scipy.interpolate import interp1d
        # This is simplified - in practice, interpolate Hessian components
        def ve_rhs(t, delta_y):
            """VE right-hand side: d(δy)/dt = J ∇²H(γ(t)) δy"""
            # Find nearest time point (simplified)
            idx = np.argmin(np.abs(ve_data.times - t))
            hess = ve_data.hessians[idx]
            return J @ hess @ delta_y

        # Integrate
        sol = solve_ivp(
            ve_rhs,
            (ve_data.times[0], ve_data.times[-1]),
            initial_perturbation,
            t_eval=ve_data.times,
            **integrator_kwargs
        )

        if not sol.success:
            raise RuntimeError(f"VE integration failed: {sol.message}")

        return sol.y.T

    def compute_monodromy_matrix(
        self,
        ve_data: VariationalEquationData,
        n_samples: int = 100
    ) -> np.ndarray:
        """
        Compute monodromy matrix M = Φ(T) (linearized Poincaré map).

        The monodromy matrix is the state transition matrix after one period.
        Its eigenvalues (Floquet multipliers) determine stability.

        Args:
            ve_data: Variational equation data
            n_samples: Number of basis vectors to integrate

        Returns:
            Monodromy matrix M (2n, 2n)
        """
        dim = ve_data.phase_space_dim

        # Integrate VE for each basis vector
        M = np.zeros((dim, dim))

        for i in range(dim):
            # Initial perturbation: i-th basis vector
            delta_y_0 = np.zeros(dim)
            delta_y_0[i] = 1.0

            # Integrate
            delta_y = self.integrate_variational_equation(ve_data, delta_y_0)

            # Final perturbation = i-th column of monodromy matrix
            M[:, i] = delta_y[-1]

        return M


def compute_floquet_multipliers(monodromy_matrix: np.ndarray) -> np.ndarray:
    """
    Compute Floquet multipliers (eigenvalues of monodromy matrix).

    For Hamiltonian systems, Floquet multipliers come in reciprocal pairs
    (if λ is a multiplier, so is 1/λ).

    Args:
        monodromy_matrix: Monodromy matrix M

    Returns:
        Floquet multipliers (eigenvalues)
    """
    eigenvalues = np.linalg.eigvals(monodromy_matrix)
    return eigenvalues


def classify_orbit_stability(floquet_multipliers: np.ndarray, tol: float = 1e-6) -> str:
    """
    Classify orbit stability from Floquet multipliers.

    Args:
        floquet_multipliers: Eigenvalues of monodromy matrix
        tol: Tolerance for |λ| = 1

    Returns:
        Stability classification: 'stable', 'unstable', 'neutral', 'elliptic'
    """
    # Check if all multipliers are on unit circle
    mags = np.abs(floquet_multipliers)

    on_circle = np.all(np.abs(mags - 1.0) < tol)

    if on_circle:
        # Check if multipliers are complex (elliptic)
        has_complex = np.any(np.abs(floquet_multipliers.imag) > tol)
        if has_complex:
            return 'elliptic'
        else:
            return 'neutral'
    else:
        # Some multipliers outside unit circle
        has_outside = np.any(mags > 1.0 + tol)
        if has_outside:
            return 'unstable'
        else:
            return 'stable'
