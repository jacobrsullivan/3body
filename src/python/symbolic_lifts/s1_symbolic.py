"""
S¹ Bundle Extended Hamiltonian (Symbolic Implementation).

This module implements the S¹ bundle lift construction from WP 2.1-2.2,
but in fully symbolic form using SymPy. This enables exact computation
of Hessians and upstairs variational equations for the Morales-Ramis test.

Theoretical Background:
    The S¹ bundle extends the phase space from (q, p) to (q, p, θ, p_θ)
    where θ ∈ S¹ is a fiber coordinate and p_θ is its conjugate momentum.

    The extended Hamiltonian takes the form:
        H̃(q, p, θ, p_θ) = H(q, p) + V_lift(θ, p_θ) + A(q, p)·J(q)·dq/dt

    where:
    - H(q, p) is the base (downstairs) Hamiltonian
    - V_lift is the lifting potential (e.g., p_θ²/2 for minimal lift)
    - A is the connection one-form (magnetic term)
    - The connection encodes the "twist" of the bundle

References:
    - WP 2.1.2: Mechanical connection and reduction
    - WP 2.2: S¹ bundle construction
    - Section VI of theoretical paper: Upstairs Morales-Ramis
"""

import sympy as sp
from sympy import Symbol, symbols, sqrt, simplify, cos, sin
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass

from .common import (
    SymbolicHamiltonianSystem,
    LiftedHamiltonianBase,
    compute_angular_momentum_2d,
    newtonian_kinetic_energy,
    newtonian_potential_energy
)


@dataclass
class S1BundleHamiltonian(LiftedHamiltonianBase):
    """
    S¹ bundle extended Hamiltonian.

    The extension adds (θ, p_θ) coordinates to (q, p):
    - θ ∈ S¹: Fiber coordinate (angle)
    - p_θ: Conjugate momentum to θ

    The extended Hamiltonian includes:
    1. Base Hamiltonian H(q, p)
    2. Lifting potential V_lift(θ, p_θ)
    3. Connection term A(q, p)

    For the minimal S¹ lift, we typically use:
        H̃ = H(q, p) + p_θ²/2 + A(q, p)·(dθ/dt)

    where A is the mechanical connection (related to angular momentum).
    """

    lift_type: str = 'minimal'
    """Type of lift: 'minimal', 'magnetic', or 'custom'."""

    def _construct_hamiltonian(self) -> sp.Expr:
        """
        Construct S¹ extended Hamiltonian.

        For minimal lift:
            H̃ = H(q, p) + p_θ²/2

        For magnetic lift:
            H̃ = H(q, p) + p_θ²/2 + A·L

        where L is angular momentum and A is connection strength.

        Returns:
            Extended Hamiltonian expression
        """
        # Get base dimension
        n_base = len(self.base_coords) // 2

        # Create extended coordinates: (q, p, θ, p_θ)
        theta = Symbol('theta', real=True)
        p_theta = Symbol('p_theta', real=True)

        self.extended_coords = (*self.base_coords, theta, p_theta)

        # Start with base Hamiltonian
        H_extended = self.H_base

        # Add fiber kinetic energy: p_θ²/2
        H_extended += p_theta**2 / 2

        # Add connection term (if magnetic lift)
        if self.lift_type == 'magnetic':
            # Connection proportional to angular momentum
            if n_base == 2:  # Planar case
                q_coords = self.base_coords[:n_base]
                p_coords = self.base_coords[n_base:]

                # Compute angular momentum
                L = compute_angular_momentum_2d(list(q_coords), list(p_coords))

                # Connection strength (parameter)
                alpha = self.params.get('alpha', Symbol('alpha', real=True))

                # Add coupling: α·L·p_θ
                H_extended += alpha * L * p_theta

        return simplify(H_extended)

    def _compute_connection(self) -> Optional[sp.Expr]:
        """
        Compute connection one-form A.

        For planar 3-body problem with angular momentum reduction:
            A = L / I

        where L is total angular momentum and I is moment of inertia.

        Returns:
            Connection one-form (or None for minimal lift)
        """
        if self.lift_type == 'minimal':
            return None

        n_base = len(self.base_coords) // 2

        if self.lift_type == 'magnetic' and n_base == 2:
            q_coords = self.base_coords[:n_base]
            p_coords = self.base_coords[n_base:]

            # Angular momentum
            L = compute_angular_momentum_2d(list(q_coords), list(p_coords))

            # Moment of inertia (simplified - would need masses for exact)
            # I ≈ Σ mᵢ·rᵢ²
            # For now, return L (connection ∝ L)
            return L

        return None


def create_s1_hamiltonian_cr3bp(
    mu: Optional[sp.Symbol] = None,
    lift_type: str = 'minimal'
) -> S1BundleHamiltonian:
    """
    Create S¹ extended Hamiltonian for Circular Restricted 3-Body Problem.

    The CR3BP Hamiltonian in rotating frame is:
        H = (pₓ² + pᵧ²)/2 - (x·pᵧ - y·pₓ) - (1-μ)/r₁ - μ/r₂

    where:
    - (x, y) are positions in rotating frame
    - (pₓ, pᵧ) are conjugate momenta
    - μ is the mass ratio
    - r₁, r₂ are distances to primary and secondary

    Args:
        mu: Mass ratio parameter (default: create as symbol)
        lift_type: 'minimal' or 'magnetic'

    Returns:
        S1BundleHamiltonian with CR3BP as base

    Example:
        >>> mu_sym = sp.Symbol('mu', real=True, positive=True)
        >>> s1_ham = create_s1_hamiltonian_cr3bp(mu=mu_sym)
        >>> system = s1_ham.get_symbolic_system()
        >>> print(system.H)  # Extended Hamiltonian
    """
    # Create symbols
    if mu is None:
        mu = Symbol('mu', real=True, positive=True)

    x, y = symbols('x y', real=True)
    px, py = symbols('p_x p_y', real=True)

    base_coords = (x, y, px, py)

    # Kinetic energy in rotating frame
    T = (px**2 + py**2) / 2

    # Coriolis term (from rotating frame)
    Coriolis = -(x * py - y * px)

    # Potential energy
    # Distance to primary (mass 1-μ at (-μ, 0))
    r1_squared = (x + mu)**2 + y**2
    r1 = sqrt(r1_squared)

    # Distance to secondary (mass μ at (1-μ, 0))
    r2_squared = (x - (1 - mu))**2 + y**2
    r2 = sqrt(r2_squared)

    V = -(1 - mu) / r1 - mu / r2

    # Total base Hamiltonian
    H_base = T + Coriolis + V

    # Parameters
    params = {'mu': mu}
    if lift_type == 'magnetic':
        params['alpha'] = Symbol('alpha', real=True)

    # Create S¹ bundle
    s1_ham = S1BundleHamiltonian(
        base_hamiltonian=H_base,
        base_coordinates=base_coords,
        parameters=params,
        lift_type=lift_type
    )

    return s1_ham


def create_s1_hamiltonian_general_3bp(
    masses: Optional[Tuple[sp.Symbol, sp.Symbol, sp.Symbol]] = None,
    planar: bool = True,
    lift_type: str = 'minimal',
    use_com_frame: bool = True
) -> S1BundleHamiltonian:
    """
    Create S¹ extended Hamiltonian for general 3-body problem.

    Args:
        masses: (m₁, m₂, m₃) as SymPy symbols (default: create symbols)
        planar: If True, use 2D; if False, use 3D
        lift_type: 'minimal' or 'magnetic'
        use_com_frame: If True, reduce to center-of-mass frame

    Returns:
        S1BundleHamiltonian for general 3BP

    Example:
        >>> m1, m2, m3 = sp.symbols('m_1 m_2 m_3', positive=True, real=True)
        >>> s1_ham = create_s1_hamiltonian_general_3bp(masses=(m1, m2, m3))
        >>> system = s1_ham.get_symbolic_system()
    """
    # Create mass symbols if not provided
    if masses is None:
        m1, m2, m3 = symbols('m_1 m_2 m_3', positive=True, real=True)
        masses = (m1, m2, m3)
    else:
        m1, m2, m3 = masses

    G = Symbol('G', positive=True, real=True)  # Gravitational constant

    if planar:
        # 2D planar case
        # Positions
        x1, y1 = symbols('x_1 y_1', real=True)
        x2, y2 = symbols('x_2 y_2', real=True)
        x3, y3 = symbols('x_3 y_3', real=True)

        # Momenta
        px1, py1 = symbols('p_x1 p_y1', real=True)
        px2, py2 = symbols('p_x2 p_y2', real=True)
        px3, py3 = symbols('p_x3 p_y3', real=True)

        q_coords = (x1, y1, x2, y2, x3, y3)
        p_coords = (px1, py1, px2, py2, px3, py3)

        # Kinetic energy
        T = (px1**2 + py1**2)/(2*m1) + (px2**2 + py2**2)/(2*m2) + (px3**2 + py3**2)/(2*m3)

        # Potential energy
        r12 = sqrt((x1 - x2)**2 + (y1 - y2)**2)
        r13 = sqrt((x1 - x3)**2 + (y1 - y3)**2)
        r23 = sqrt((x2 - x3)**2 + (y2 - y3)**2)

        V = -G * (m1*m2/r12 + m1*m3/r13 + m2*m3/r23)

        H_base = T + V

        if use_com_frame:
            # Add constraint for COM at origin (Lagrange multiplier approach)
            # For now, just use full coordinates
            # In practice, would reduce to relative coordinates
            pass

    else:
        # 3D case
        # Positions
        x1, y1, z1 = symbols('x_1 y_1 z_1', real=True)
        x2, y2, z2 = symbols('x_2 y_2 z_2', real=True)
        x3, y3, z3 = symbols('x_3 y_3 z_3', real=True)

        # Momenta
        px1, py1, pz1 = symbols('p_x1 p_y1 p_z1', real=True)
        px2, py2, pz2 = symbols('p_x2 p_y2 p_z2', real=True)
        px3, py3, pz3 = symbols('p_x3 p_y3 p_z3', real=True)

        q_coords = (x1, y1, z1, x2, y2, z2, x3, y3, z3)
        p_coords = (px1, py1, pz1, px2, py2, pz2, px3, py3, pz3)

        # Kinetic energy
        T = ((px1**2 + py1**2 + pz1**2)/(2*m1) +
             (px2**2 + py2**2 + pz2**2)/(2*m2) +
             (px3**2 + py3**2 + pz3**2)/(2*m3))

        # Potential energy
        r12 = sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
        r13 = sqrt((x1 - x3)**2 + (y1 - y3)**2 + (z1 - z3)**2)
        r23 = sqrt((x2 - x3)**2 + (y2 - y3)**2 + (z2 - z3)**2)

        V = -G * (m1*m2/r12 + m1*m3/r13 + m2*m3/r23)

        H_base = T + V

    base_coords = q_coords + p_coords

    # Parameters
    params = {
        'm1': m1, 'm2': m2, 'm3': m3, 'G': G
    }
    if lift_type == 'magnetic':
        params['alpha'] = Symbol('alpha', real=True)

    # Create S¹ bundle
    s1_ham = S1BundleHamiltonian(
        base_hamiltonian=H_base,
        base_coordinates=base_coords,
        parameters=params,
        lift_type=lift_type
    )

    return s1_ham


def compute_s1_hessian_cr3bp(
    mu_value: Optional[float] = None,
    simplify_result: bool = True
) -> sp.Matrix:
    """
    Compute Hessian of S¹ extended Hamiltonian for CR3BP.

    This is the key quantity for upstairs variational equations.

    Args:
        mu_value: Numerical value of μ (or None to keep symbolic)
        simplify_result: Whether to simplify the Hessian

    Returns:
        Hessian matrix ∇²H̃ (6×6 for minimal lift)

    Example:
        >>> hess = compute_s1_hessian_cr3bp(mu_value=0.012)
        >>> print(hess.shape)  # (6, 6)
    """
    # Create S¹ Hamiltonian
    mu = Symbol('mu', real=True, positive=True)
    s1_ham = create_s1_hamiltonian_cr3bp(mu=mu, lift_type='minimal')

    # Get symbolic system
    system = s1_ham.get_symbolic_system()

    # Compute Hessian
    hess = system.hessian()

    # Substitute numerical value if provided
    if mu_value is not None:
        hess = hess.subs(mu, mu_value)

    # Simplify if requested
    if simplify_result:
        hess = sp.simplify(hess)

    return hess


def evaluate_s1_hamiltonian_along_orbit(
    s1_ham: S1BundleHamiltonian,
    orbit_data: Dict,
    theta_initial: float = 0.0,
    p_theta_value: float = 0.0
) -> sp.Expr:
    """
    Evaluate S¹ Hamiltonian along a periodic orbit.

    Args:
        s1_ham: S¹ bundle Hamiltonian
        orbit_data: Dict with 'time', 'positions', 'momenta'
        theta_initial: Initial fiber coordinate
        p_theta_value: Value of p_θ (conserved for minimal lift)

    Returns:
        Hamiltonian value as function of time (symbolic)
    """
    # Get symbolic system
    system = s1_ham.get_symbolic_system()

    # This would require orbit interpolation
    # For now, return symbolic H̃
    return system.H


# Utility function for upstairs Morales-Ramis test
def prepare_s1_for_upstairs_mr_test(
    mu_value: float = 0.012,
    orbit_name: str = 'L4'
) -> Dict:
    """
    Prepare S¹ extended system for upstairs Morales-Ramis test.

    Returns symbolic Hamiltonian, Hessian, and coordinates ready for
    upstairs NVE computation and Kovacic algorithm application.

    Args:
        mu_value: Mass ratio for CR3BP
        orbit_name: Name of orbit to analyze

    Returns:
        Dictionary with:
        - 'hamiltonian': Extended Hamiltonian H̃
        - 'hessian': Hessian ∇²H̃
        - 'coordinates': Extended coordinates (x, y, px, py, θ, p_θ)
        - 'system': Complete SymbolicHamiltonianSystem

    Example:
        >>> data = prepare_s1_for_upstairs_mr_test(mu_value=0.012, orbit_name='L4')
        >>> H_tilde = data['hamiltonian']
        >>> hess_tilde = data['hessian']
        >>> # Use for upstairs NVE computation
    """
    mu = Symbol('mu', real=True, positive=True)
    s1_ham = create_s1_hamiltonian_cr3bp(mu=mu, lift_type='minimal')

    system = s1_ham.get_symbolic_system()

    # Substitute numerical mu
    H_numerical = system.H.subs(mu, mu_value)
    hess_numerical = system.hessian().subs(mu, mu_value)

    return {
        'hamiltonian': H_numerical,
        'hessian': hess_numerical,
        'coordinates': system.coordinates,
        'system': system,
        'orbit_name': orbit_name,
        'mu': mu_value
    }
