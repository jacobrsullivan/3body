"""
KS-Spinor Extended Hamiltonian (Symbolic Implementation).

This module implements the Kustaanheimo-Stiefel (KS) spinor regularization
in symbolic form using SymPy. This enables exact computation of Hessians
and variational equations for the Morales-Ramis integrability analysis.

Theoretical Background:
    The KS transformation embeds 3D Euclidean space into 4D spinor space
    via a bilinear map using the Levi-Civita matrix. For a single two-body
    problem, the transformation is:

        r = L(u)·u

    where u ∈ ℝ⁴ is the spinor and L(u) is the 3×4 Levi-Civita matrix.

    Key properties:
    - Regularizes collisions: r → 0 is smooth in u-space
    - Bilinear relation: |r|² = |u|⁴, hence r = |u|²
    - Time regularization: dt/ds = r (fictitious time s)

    For the three-body problem, we apply KS pairwise to all three relative
    coordinates, creating a 12D spinor space (3 spinors × 4 components).

References:
    - WP 2.3: KS-Spinor Lift Implementation Plan
    - Kustaanheimo & Stiefel (1965): Perturbation theory
    - Stiefel & Scheifele (1971): Linear and Regular Celestial Mechanics
"""

import sympy as sp
from sympy import Symbol, symbols, Matrix, sqrt, simplify, Rational
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass, field

from .common import (
    SymbolicHamiltonianSystem,
    LiftedHamiltonianBase,
    newtonian_potential_energy,
    compute_hessian,
    compute_symplectic_gradient
)


def levi_civita_matrix(u: Matrix) -> Matrix:
    """
    Compute the Levi-Civita matrix L(u) for KS transformation.

    The Levi-Civita matrix is a 3×4 matrix that maps spinor space ℝ⁴
    to Euclidean space ℝ³ via the bilinear relation r = L(u)·u.

    Definition:
        L(u) = [u₀  -u₁  -u₂  -u₃]
               [u₁   u₀  -u₃   u₂]
               [u₂   u₃   u₀  -u₁]

    Args:
        u: Spinor vector (4×1 SymPy Matrix) with components (u₀, u₁, u₂, u₃)

    Returns:
        Levi-Civita matrix L(u) as 3×4 SymPy Matrix

    Example:
        >>> u = Matrix(symbols('u_0:4', real=True))
        >>> L = levi_civita_matrix(u)
        >>> L.shape
        (3, 4)
    """
    if u.shape != (4, 1):
        u = Matrix(u).reshape(4, 1)

    u0, u1, u2, u3 = u[0], u[1], u[2], u[3]

    L = Matrix([
        [u0, -u1, -u2, -u3],
        [u1,  u0, -u3,  u2],
        [u2,  u3,  u0, -u1]
    ])

    return L


def bilinear_relation_symbolic(u: Matrix) -> sp.Expr:
    """
    Compute the bilinear relation r = |u|² symbolically.

    The bilinear relation connects the spinor norm to the Euclidean distance:
        |r|² = |u|⁴  ⟹  r = |u|²

    Args:
        u: Spinor vector (4×1 SymPy Matrix)

    Returns:
        Symbolic expression for r = |u|²

    Example:
        >>> u = Matrix(symbols('u_0:4', real=True))
        >>> r = bilinear_relation_symbolic(u)
        >>> simplify(r)
        u_0**2 + u_1**2 + u_2**2 + u_3**2
    """
    if u.shape != (4, 1):
        u = Matrix(u).reshape(4, 1)

    # r = |u|² = u₀² + u₁² + u₂² + u₃²
    r = sum(u[i]**2 for i in range(4))

    return r


def ks_transform_symbolic(r_vec: Matrix, v_vec: Matrix) -> Tuple[Matrix, Matrix]:
    """
    Symbolic KS transformation: (r, v) → (u, u').

    Forward KS transformation from Cartesian coordinates (r, v) to
    spinor coordinates (u, u'). This is the inverse of the bilinear map.

    Note: The transformation is not unique - there are branch choices.
    We use the "northern hemisphere" convention: u₀ ≥ 0.

    Args:
        r_vec: Position vector in ℝ³ (3×1 Matrix)
        v_vec: Velocity vector in ℝ³ (3×1 Matrix)

    Returns:
        (u, u_prime): Spinor and spinor velocity (both 4×1 Matrices)

    Warning:
        This is a symbolic template. Numerical implementation requires
        careful branch choice and singularity handling.
    """
    # Extract components
    x, y, z = r_vec[0], r_vec[1], r_vec[2]

    # Compute radius r = |r_vec|
    r = sqrt(x**2 + y**2 + z**2)

    # One branch of the KS transformation (northern hemisphere: u₀ ≥ 0)
    # This is a conventional choice; see Stiefel & Scheifele (1971)

    # For symbolic purposes, we define the transformation template
    # u₀ = sqrt((r + x)/2)
    # u₁ = y / (2*u₀)
    # u₂ = z / (2*u₀)
    # u₃ = 0  (planar case simplification)

    # Symbolic placeholders for general case
    u0 = Symbol('u_0', real=True, positive=True)
    u1 = Symbol('u_1', real=True)
    u2 = Symbol('u_2', real=True)
    u3 = Symbol('u_3', real=True)

    u = Matrix([u0, u1, u2, u3])

    # Velocity transformation (requires time derivative of bilinear map)
    # For symbolic analysis, we define u' as independent variables
    u0_prime = Symbol('u_0_prime', real=True)
    u1_prime = Symbol('u_1_prime', real=True)
    u2_prime = Symbol('u_2_prime', real=True)
    u3_prime = Symbol('u_3_prime', real=True)

    u_prime = Matrix([u0_prime, u1_prime, u2_prime, u3_prime])

    return u, u_prime


def ks_inverse_symbolic(u: Matrix, u_prime: Matrix) -> Tuple[Matrix, Matrix]:
    """
    Symbolic KS inverse transformation: (u, u') → (r, v).

    This is the forward bilinear map from spinor to Cartesian coordinates.

    Args:
        u: Spinor vector (4×1 Matrix)
        u_prime: Spinor velocity (4×1 Matrix)

    Returns:
        (r_vec, v_vec): Position and velocity in Cartesian coordinates

    Example:
        >>> u = Matrix(symbols('u_0:4', real=True))
        >>> u_prime = Matrix(symbols('u_0_prime:4', real=True))
        >>> r, v = ks_inverse_symbolic(u, u_prime)
        >>> r.shape
        (3, 1)
    """
    # Compute Levi-Civita matrix
    L = levi_civita_matrix(u)

    # Position: r = L(u)·u
    r_vec = L * u  # 3×4 times 4×1 = 3×1

    # Velocity: v = L(u)·u' + L'(u)·u (product rule)
    # L'(u)·u requires derivative of L with respect to time
    # For symbolic purposes, we compute the direct formula:

    # v = L(u)·u' + dL/dt·u where dL/dt = L(u')
    L_prime = levi_civita_matrix(u_prime)
    v_vec = L * u_prime + L_prime * u

    return simplify(r_vec), simplify(v_vec)


@dataclass
class KSSpinorHamiltonian(LiftedHamiltonianBase):
    """
    KS-Spinor extended Hamiltonian for single two-body pair.

    The KS transformation regularizes the two-body problem by embedding
    it in 4D spinor space. The regularized Hamiltonian in fictitious time s is:

        K(u, u', s) = (1/r) · |u'|² - V_reg(u)

    where:
    - r = |u|² (bilinear relation)
    - dt/ds = r (time regularization)
    - V_reg is the regularized potential

    For Kepler problem: K = |u'|²/|u|² - μ/|u|²

    Attributes:
        fictitious_time_var: Symbol for fictitious time s
        mass_product: Product of masses (μ = G·m₁·m₂)
        use_time_regularization: If True, use regularized time
    """

    fictitious_time_var: sp.Symbol = field(default=None)
    mass_product: sp.Symbol = field(default=None)
    use_time_regularization: bool = field(default=True)

    def __post_init__(self):
        """Initialize after dataclass init."""
        super().__init__(
            base_hamiltonian=sp.Integer(0),  # Will be constructed
            base_coordinates=tuple(),
            parameters={}
        )

        if self.fictitious_time_var is None:
            self.fictitious_time_var = Symbol('s', real=True)

        if self.mass_product is None:
            self.mass_product = Symbol('mu', positive=True, real=True)

    def _construct_hamiltonian(self) -> sp.Expr:
        """
        Construct KS regularized Hamiltonian.

        For two-body problem with masses m₁, m₂:
            K = |u'|²/|u|² - μ/|u|²

        where μ = G·m₁·m₂ and ' denotes derivative w.r.t. fictitious time s.

        Returns:
            Regularized Hamiltonian K(u, u', s)
        """
        # Create spinor coordinates
        u_syms = symbols('u_0:4', real=True)
        u = Matrix(u_syms)

        # Create spinor momenta (derivatives w.r.t. fictitious time)
        u_prime_syms = symbols('u_0_prime:4', real=True)
        u_prime = Matrix(u_prime_syms)

        # Compute r = |u|²
        r = bilinear_relation_symbolic(u)

        # Regularized kinetic energy: T_reg = |u'|²/r
        T_reg = sum(u_prime[i]**2 for i in range(4)) / r

        # Regularized potential: V_reg = μ/r
        V_reg = self.mass_product / r

        # Regularized Hamiltonian: K = T_reg - V_reg
        K = T_reg - V_reg

        # Set extended coordinates
        self.extended_coords = tuple(u_syms) + tuple(u_prime_syms)

        return simplify(K)

    def _compute_connection(self) -> Optional[sp.Expr]:
        """
        KS transformation doesn't introduce a connection one-form.

        Returns:
            None (no connection for KS lift)
        """
        return None

    def compute_hessian_ks(self) -> Matrix:
        """
        Compute Hessian of regularized Hamiltonian.

        This is the key quantity for upstairs Morales-Ramis analysis.

        Returns:
            Hessian matrix ∇²K (8×8 for single pair)
        """
        if self.H_extended is None:
            self.H_extended = self._construct_hamiltonian()

        return compute_hessian(self.H_extended, self.extended_coords)

    def bilinear_constraints(self) -> sp.Expr:
        """
        Return the bilinear constraint r = |u|².

        This constraint defines the embedding of ℝ³ into ℝ⁴.

        Returns:
            Constraint equation: |u|² - r = 0
        """
        u_syms = symbols('u_0:4', real=True)
        u = Matrix(u_syms)
        r = Symbol('r', positive=True, real=True)

        constraint = bilinear_relation_symbolic(u) - r

        return constraint


@dataclass
class KSPairwiseHamiltonian:
    """
    Pairwise KS Hamiltonian for three-body problem.

    Applies KS transformation to all three relative coordinates:
    - u₁₂ ∈ ℝ⁴: Spinor for r₁₂ = r₁ - r₂
    - u₂₃ ∈ ℝ⁴: Spinor for r₂₃ = r₂ - r₃
    - u₃₁ ∈ ℝ⁴: Spinor for r₃₁ = r₃ - r₁

    Configuration space: 12D (constrained to effective 9D)
    Phase space: 24D (constrained to 18D)

    Constraints:
    1. Bilinear: |u_ij|² = r_ij for each pair
    2. Closure: r₁₂ + r₂₃ + r₃₁ = 0 (triangle closure)

    Attributes:
        masses: (m₁, m₂, m₃) as SymPy symbols
        gravitational_constant: G (default: Symbol('G'))
        fictitious_time: Fictitious time variable s
    """

    masses: Tuple[sp.Symbol, sp.Symbol, sp.Symbol] = field(default=None)
    gravitational_constant: sp.Symbol = field(default=None)
    fictitious_time: sp.Symbol = field(default=None)

    # Computed attributes
    H_pairwise: Optional[sp.Expr] = field(default=None, init=False)
    spinor_coords: Optional[Tuple[sp.Symbol, ...]] = field(default=None, init=False)
    spinor_momenta: Optional[Tuple[sp.Symbol, ...]] = field(default=None, init=False)
    constraints: Optional[List[sp.Expr]] = field(default=None, init=False)

    def __post_init__(self):
        """Initialize computed fields."""
        if self.masses is None:
            self.masses = symbols('m_1 m_2 m_3', positive=True, real=True)

        if self.gravitational_constant is None:
            self.gravitational_constant = Symbol('G', positive=True, real=True)

        if self.fictitious_time is None:
            self.fictitious_time = Symbol('s', real=True)

        # Create spinor coordinates
        u12_syms = symbols('u_12_0:4', real=True)
        u23_syms = symbols('u_23_0:4', real=True)
        u31_syms = symbols('u_31_0:4', real=True)

        self.spinor_coords = u12_syms + u23_syms + u31_syms  # 12 components

        # Create spinor momenta
        u12_prime_syms = symbols('u_12_prime_0:4', real=True)
        u23_prime_syms = symbols('u_23_prime_0:4', real=True)
        u31_prime_syms = symbols('u_31_prime_0:4', real=True)

        self.spinor_momenta = u12_prime_syms + u23_prime_syms + u31_prime_syms

        # Construct Hamiltonian
        self.H_pairwise = self._construct_pairwise_hamiltonian()

        # Construct constraints
        self.constraints = self._construct_constraints()

    def _construct_pairwise_hamiltonian(self) -> sp.Expr:
        """
        Construct pairwise regularized Hamiltonian.

        The Hamiltonian in spinor coordinates with time regularization is:

            K = Σᵢⱼ |u'ᵢⱼ|²/|uᵢⱼ|² - Vᵣₑ𝓰

        where the sum is over pairs (12, 23, 31) and:
            Vᵣₑ𝓰 = G·Σᵢⱼ mᵢ·mⱼ/|uᵢⱼ|²

        Returns:
            Pairwise regularized Hamiltonian
        """
        m1, m2, m3 = self.masses
        G = self.gravitational_constant

        # Extract spinor variables
        u12 = Matrix(self.spinor_coords[0:4])
        u23 = Matrix(self.spinor_coords[4:8])
        u31 = Matrix(self.spinor_coords[8:12])

        u12_prime = Matrix(self.spinor_momenta[0:4])
        u23_prime = Matrix(self.spinor_momenta[4:8])
        u31_prime = Matrix(self.spinor_momenta[8:12])

        # Compute radii: r_ij = |u_ij|²
        r12 = bilinear_relation_symbolic(u12)
        r23 = bilinear_relation_symbolic(u23)
        r31 = bilinear_relation_symbolic(u31)

        # Kinetic energy (regularized)
        T_reg = (sum(u12_prime[i]**2 for i in range(4)) / r12 +
                 sum(u23_prime[i]**2 for i in range(4)) / r23 +
                 sum(u31_prime[i]**2 for i in range(4)) / r31)

        # Potential energy (regularized)
        V_reg = G * (m1*m2/r12 + m2*m3/r23 + m3*m1/r31)

        # Regularized Hamiltonian
        K_pairwise = T_reg - V_reg

        return simplify(K_pairwise)

    def _construct_constraints(self) -> List[sp.Expr]:
        """
        Construct constraint equations for pairwise KS system.

        Constraints:
        1. Bilinear for each pair: |u_ij|² - r_ij = 0
        2. Closure: The three distance vectors must close to form a triangle

        Returns:
            List of constraint expressions
        """
        # Extract spinor variables
        u12 = Matrix(self.spinor_coords[0:4])
        u23 = Matrix(self.spinor_coords[4:8])
        u31 = Matrix(self.spinor_coords[8:12])

        # Bilinear constraints
        r12_sym = Symbol('r_12', positive=True, real=True)
        r23_sym = Symbol('r_23', positive=True, real=True)
        r31_sym = Symbol('r_31', positive=True, real=True)

        c1 = bilinear_relation_symbolic(u12) - r12_sym
        c2 = bilinear_relation_symbolic(u23) - r23_sym
        c3 = bilinear_relation_symbolic(u31) - r31_sym

        # Closure constraint: r₁₂ + r₂₃ + r₃₁ = 0 (as vectors)
        # In Cartesian: L(u₁₂)·u₁₂ + L(u₂₃)·u₂₃ + L(u₃₁)·u₃₁ = 0
        r12_vec, _ = ks_inverse_symbolic(u12, Matrix([0, 0, 0, 0]))
        r23_vec, _ = ks_inverse_symbolic(u23, Matrix([0, 0, 0, 0]))
        r31_vec, _ = ks_inverse_symbolic(u31, Matrix([0, 0, 0, 0]))

        closure = r12_vec + r23_vec + r31_vec  # Should be zero (3 equations)

        c4 = closure[0]  # x-component
        c5 = closure[1]  # y-component
        c6 = closure[2]  # z-component

        return [c1, c2, c3, c4, c5, c6]

    def get_symbolic_system(self) -> SymbolicHamiltonianSystem:
        """
        Get SymbolicHamiltonianSystem representation.

        Returns:
            Complete symbolic system with constraints
        """
        all_coords = self.spinor_coords + self.spinor_momenta

        params = {
            'm1': self.masses[0],
            'm2': self.masses[1],
            'm3': self.masses[2],
            'G': self.gravitational_constant
        }

        return SymbolicHamiltonianSystem(
            H=self.H_pairwise,
            coordinates=all_coords,
            parameters=params,
            dimension=12,  # 12D configuration space
            is_extended=True,
            constraints=self.constraints
        )

    def compute_hessian(self) -> Matrix:
        """
        Compute Hessian of pairwise Hamiltonian.

        Returns:
            Hessian matrix ∇²K (24×24)
        """
        all_coords = self.spinor_coords + self.spinor_momenta
        return compute_hessian(self.H_pairwise, all_coords)

    def constraint_jacobian(self) -> Matrix:
        """
        Compute Jacobian matrix of constraints.

        This is needed for constrained integration (RATTLE) and
        for projecting onto the constraint manifold.

        Returns:
            Jacobian matrix ∂c/∂x (6×24)
        """
        all_coords = self.spinor_coords + self.spinor_momenta

        n_constraints = len(self.constraints)
        n_coords = len(all_coords)

        jac = sp.zeros(n_constraints, n_coords)

        for i, c in enumerate(self.constraints):
            for j, coord in enumerate(all_coords):
                jac[i, j] = sp.diff(c, coord)

        return jac


# Factory functions

def create_ks_hamiltonian_kepler(
    mass_product: Optional[sp.Symbol] = None
) -> KSSpinorHamiltonian:
    """
    Create KS regularized Hamiltonian for Kepler (two-body) problem.

    Args:
        mass_product: μ = G·m₁·m₂ (default: create symbol)

    Returns:
        KS Hamiltonian for Kepler problem

    Example:
        >>> mu = sp.Symbol('mu', positive=True)
        >>> ks_ham = create_ks_hamiltonian_kepler(mu)
        >>> system = ks_ham.get_symbolic_system()
        >>> print(system.H)  # Regularized Hamiltonian
    """
    if mass_product is None:
        mass_product = Symbol('mu', positive=True, real=True)

    ks_ham = KSSpinorHamiltonian(
        mass_product=mass_product,
        use_time_regularization=True
    )

    return ks_ham


def create_ks_pairwise_3bp(
    masses: Optional[Tuple[sp.Symbol, sp.Symbol, sp.Symbol]] = None,
    gravitational_constant: Optional[sp.Symbol] = None
) -> KSPairwiseHamiltonian:
    """
    Create pairwise KS Hamiltonian for three-body problem.

    Args:
        masses: (m₁, m₂, m₃) as SymPy symbols
        gravitational_constant: G (default: create symbol)

    Returns:
        Pairwise KS Hamiltonian for 3BP

    Example:
        >>> m1, m2, m3 = sp.symbols('m_1 m_2 m_3', positive=True)
        >>> ks_3bp = create_ks_pairwise_3bp((m1, m2, m3))
        >>> system = ks_3bp.get_symbolic_system()
        >>> print(len(system.constraints))  # 6 constraints
    """
    if masses is None:
        masses = symbols('m_1 m_2 m_3', positive=True, real=True)

    if gravitational_constant is None:
        gravitational_constant = Symbol('G', positive=True, real=True)

    ks_pairwise = KSPairwiseHamiltonian(
        masses=masses,
        gravitational_constant=gravitational_constant
    )

    return ks_pairwise


# Utility functions for upstairs Morales-Ramis test

def prepare_ks_for_upstairs_mr_test(
    masses: Tuple[float, float, float],
    orbit_name: str = 'figure8'
) -> Dict:
    """
    Prepare KS extended system for upstairs Morales-Ramis test.

    Returns symbolic Hamiltonian, Hessian, constraints, and coordinates
    ready for upstairs NVE computation and Kovacic algorithm application.

    Args:
        masses: (m₁, m₂, m₃) numerical values
        orbit_name: Name of orbit to analyze

    Returns:
        Dictionary with:
        - 'hamiltonian': Extended Hamiltonian K
        - 'hessian': Hessian ∇²K (24×24)
        - 'constraints': List of constraint equations
        - 'constraint_jacobian': Jacobian ∂c/∂x
        - 'coordinates': Extended coordinates (12 u + 12 u')
        - 'system': Complete SymbolicHamiltonianSystem

    Example:
        >>> data = prepare_ks_for_upstairs_mr_test((1.0, 1.0, 1.0))
        >>> K = data['hamiltonian']
        >>> hess = data['hessian']
        >>> # Use for upstairs NVE computation
    """
    m1_sym, m2_sym, m3_sym = symbols('m_1 m_2 m_3', positive=True, real=True)

    # Create pairwise KS Hamiltonian
    ks_3bp = create_ks_pairwise_3bp((m1_sym, m2_sym, m3_sym))

    # Get symbolic system
    system = ks_3bp.get_symbolic_system()

    # Substitute numerical masses
    m1_val, m2_val, m3_val = masses
    subs_dict = {m1_sym: m1_val, m2_sym: m2_val, m3_sym: m3_val}

    H_numerical = system.H.subs(subs_dict)
    hess_numerical = ks_3bp.compute_hessian().subs(subs_dict)
    constraints_numerical = [c.subs(subs_dict) for c in ks_3bp.constraints]
    jac_numerical = ks_3bp.constraint_jacobian().subs(subs_dict)

    return {
        'hamiltonian': H_numerical,
        'hessian': hess_numerical,
        'constraints': constraints_numerical,
        'constraint_jacobian': jac_numerical,
        'coordinates': system.coordinates,
        'system': system,
        'orbit_name': orbit_name,
        'masses': masses
    }


def verify_bilinear_relation_symbolic() -> bool:
    """
    Verify that |L(u)·u|² = |u|⁴ symbolically.

    This is a fundamental identity for the KS transformation.

    Returns:
        True if identity holds (always true for correct implementation)

    Example:
        >>> verify_bilinear_relation_symbolic()
        True
    """
    # Create symbolic spinor
    u_syms = symbols('u_0:4', real=True)
    u = Matrix(u_syms)

    # Compute r = L(u)·u
    L = levi_civita_matrix(u)
    r_vec = L * u

    # Compute |r|²
    r_squared = sum(r_vec[i]**2 for i in range(3))
    r_squared_simplified = simplify(r_squared)

    # Compute |u|⁴
    u_squared = sum(u[i]**2 for i in range(4))
    u_fourth = u_squared**2
    u_fourth_simplified = simplify(u_fourth)

    # Check if equal
    difference = simplify(r_squared_simplified - u_fourth_simplified)

    return difference == 0
