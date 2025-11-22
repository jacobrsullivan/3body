"""
Common symbolic utilities for lift Hamiltonians.

Provides base classes and utility functions for symbolic computation
of extended Hamiltonians, gradients, and Hessians.
"""

import sympy as sp
from sympy import Symbol, symbols, Matrix, diff, simplify, sqrt
from typing import List, Tuple, Dict, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class SymbolicHamiltonianSystem:
    """
    Symbolic representation of a Hamiltonian system.

    Attributes:
        H: Hamiltonian function (SymPy expression)
        coordinates: Phase space coordinates (q, p) or (q, p, θ, p_θ)
        parameters: System parameters (masses, etc.)
        dimension: Dimension of configuration space
        is_extended: True if this is a lifted Hamiltonian
    """

    H: sp.Expr
    """Hamiltonian expression."""

    coordinates: Tuple[sp.Symbol, ...]
    """Phase space coordinates (q₁, ..., qₙ, p₁, ..., pₙ)."""

    parameters: Dict[str, sp.Symbol]
    """System parameters (e.g., masses, mu)."""

    dimension: int
    """Dimension of configuration space."""

    is_extended: bool = False
    """Whether this is an extended (lifted) Hamiltonian."""

    constraints: Optional[List[sp.Expr]] = None
    """Constraint functions (for constrained systems like KS)."""


    def gradient(self) -> sp.Matrix:
        """
        Compute symplectic gradient ∇H = (∂H/∂q, ∂H/∂p).

        Returns:
            Column vector of partial derivatives
        """
        return compute_symplectic_gradient(self.H, self.coordinates)

    def hessian(self) -> sp.Matrix:
        """
        Compute Hessian matrix ∇²H.

        Returns:
            Hessian matrix (2n × 2n) or (2(n+k) × 2(n+k)) for extended
        """
        return compute_hessian(self.H, self.coordinates)

    def hamiltons_equations(self) -> Tuple[List[sp.Expr], List[sp.Expr]]:
        """
        Compute Hamilton's equations of motion.

        Returns:
            (dq_dt, dp_dt) where:
                dq_dt = ∂H/∂p
                dp_dt = -∂H/∂q
        """
        n = self.dimension
        if self.is_extended:
            # Extended system has additional coordinates
            n_total = len(self.coordinates) // 2
        else:
            n_total = n

        q_coords = self.coordinates[:n_total]
        p_coords = self.coordinates[n_total:]

        dq_dt = [diff(self.H, p) for p in p_coords]
        dp_dt = [-diff(self.H, q) for q in q_coords]

        return dq_dt, dp_dt

    def symplectic_matrix(self) -> sp.Matrix:
        """
        Construct symplectic matrix J.

        For 2n-dimensional phase space:
            J = [[0, I], [-I, 0]]

        Returns:
            Symplectic matrix (2n × 2n)
        """
        n = len(self.coordinates) // 2
        I = sp.eye(n)
        O = sp.zeros(n, n)

        J = sp.Matrix.vstack(
            sp.Matrix.hstack(O, I),
            sp.Matrix.hstack(-I, O)
        )

        return J

    def evaluate_numerical(
        self,
        state: List[float],
        param_values: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Evaluate Hamiltonian numerically at a given state.

        Args:
            state: Phase space point [q₁, ..., qₙ, p₁, ..., pₙ]
            param_values: Parameter values to substitute

        Returns:
            Numerical value of H
        """
        subs_dict = dict(zip(self.coordinates, state))

        if param_values:
            subs_dict.update({
                self.parameters[k]: v for k, v in param_values.items()
            })

        H_numerical = self.H.subs(subs_dict)
        return float(H_numerical.evalf())


def compute_symplectic_gradient(
    H: sp.Expr,
    coordinates: Tuple[sp.Symbol, ...]
) -> sp.Matrix:
    """
    Compute symplectic gradient of Hamiltonian.

    ∇H = (∂H/∂q₁, ..., ∂H/∂qₙ, ∂H/∂p₁, ..., ∂H/∂pₙ)ᵀ

    Args:
        H: Hamiltonian expression
        coordinates: (q₁, ..., qₙ, p₁, ..., pₙ)

    Returns:
        Gradient as column vector (2n × 1)
    """
    grad = sp.Matrix([diff(H, coord) for coord in coordinates])
    return grad


def compute_hessian(
    H: sp.Expr,
    coordinates: Tuple[sp.Symbol, ...]
) -> sp.Matrix:
    """
    Compute Hessian matrix of Hamiltonian.

    ∇²H = [∂²H/∂xᵢ∂xⱼ] where x = (q, p)

    Args:
        H: Hamiltonian expression
        coordinates: (q₁, ..., qₙ, p₁, ..., pₙ)

    Returns:
        Hessian matrix (2n × 2n)
    """
    n = len(coordinates)
    hess = sp.zeros(n, n)

    for i, coord_i in enumerate(coordinates):
        for j, coord_j in enumerate(coordinates):
            hess[i, j] = diff(diff(H, coord_i), coord_j)

    return hess


def create_position_vectors(
    n_bodies: int,
    planar: bool = True,
    prefix: str = 'q'
) -> Tuple[List[sp.Symbol], int]:
    """
    Create symbolic position vectors for n bodies.

    Args:
        n_bodies: Number of bodies
        planar: If True, use 2D (x, y); if False, use 3D (x, y, z)
        prefix: Variable prefix (default 'q')

    Returns:
        (position_symbols, dimension)
    """
    dim_per_body = 2 if planar else 3
    total_dim = n_bodies * dim_per_body

    if planar:
        coords = []
        for i in range(1, n_bodies + 1):
            coords.append(Symbol(f'{prefix}_{i}_x', real=True))
            coords.append(Symbol(f'{prefix}_{i}_y', real=True))
    else:
        coords = []
        for i in range(1, n_bodies + 1):
            coords.append(Symbol(f'{prefix}_{i}_x', real=True))
            coords.append(Symbol(f'{prefix}_{i}_y', real=True))
            coords.append(Symbol(f'{prefix}_{i}_z', real=True))

    return coords, total_dim


def create_momentum_vectors(
    n_bodies: int,
    planar: bool = True,
    prefix: str = 'p'
) -> List[sp.Symbol]:
    """
    Create symbolic momentum vectors for n bodies.

    Args:
        n_bodies: Number of bodies
        planar: If True, use 2D; if False, use 3D
        prefix: Variable prefix (default 'p')

    Returns:
        List of momentum symbols
    """
    dim_per_body = 2 if planar else 3

    if planar:
        momenta = []
        for i in range(1, n_bodies + 1):
            momenta.append(Symbol(f'{prefix}_{i}_x', real=True))
            momenta.append(Symbol(f'{prefix}_{i}_y', real=True))
    else:
        momenta = []
        for i in range(1, n_bodies + 1):
            momenta.append(Symbol(f'{prefix}_{i}_x', real=True))
            momenta.append(Symbol(f'{prefix}_{i}_y', real=True))
            momenta.append(Symbol(f'{prefix}_{i}_z', real=True))

    return momenta


def newtonian_kinetic_energy(
    momenta: List[sp.Symbol],
    masses: List[sp.Symbol]
) -> sp.Expr:
    """
    Compute kinetic energy T = Σ pᵢ²/(2mᵢ).

    Args:
        momenta: Momentum components [p₁ₓ, p₁ᵧ, p₂ₓ, p₂ᵧ, ...]
        masses: Body masses [m₁, m₂, ...]

    Returns:
        Kinetic energy expression
    """
    n_bodies = len(masses)
    dim_per_body = len(momenta) // n_bodies

    T = 0
    for i in range(n_bodies):
        m_i = masses[i]
        for d in range(dim_per_body):
            p_component = momenta[i * dim_per_body + d]
            T += p_component**2 / (2 * m_i)

    return T


def newtonian_potential_energy(
    positions: List[sp.Symbol],
    masses: List[sp.Symbol],
    gravitational_constant: sp.Symbol = Symbol('G', positive=True)
) -> sp.Expr:
    """
    Compute gravitational potential energy.

    V = -Σᵢ<ⱼ G·mᵢ·mⱼ / rᵢⱼ

    Args:
        positions: Position components [q₁ₓ, q₁ᵧ, q₂ₓ, q₂ᵧ, ...]
        masses: Body masses [m₁, m₂, ...]
        gravitational_constant: G (default Symbol('G'))

    Returns:
        Potential energy expression
    """
    n_bodies = len(masses)
    dim_per_body = len(positions) // n_bodies

    V = 0
    for i in range(n_bodies):
        for j in range(i + 1, n_bodies):
            # Extract positions of bodies i and j
            pos_i = [positions[i * dim_per_body + d] for d in range(dim_per_body)]
            pos_j = [positions[j * dim_per_body + d] for d in range(dim_per_body)]

            # Compute distance rᵢⱼ = |qᵢ - qⱼ|
            r_ij_squared = sum((pos_i[d] - pos_j[d])**2 for d in range(dim_per_body))
            r_ij = sqrt(r_ij_squared)

            # Add pairwise potential
            V += -gravitational_constant * masses[i] * masses[j] / r_ij

    return V


def simplify_hamiltonian(
    H: sp.Expr,
    assumptions: Optional[Dict] = None
) -> sp.Expr:
    """
    Simplify Hamiltonian expression.

    Args:
        H: Hamiltonian expression
        assumptions: Optional assumptions (e.g., {'mu': (0, 1)})

    Returns:
        Simplified Hamiltonian
    """
    # Apply basic simplification
    H_simplified = simplify(H)

    # Could add more sophisticated simplification based on assumptions
    # For now, just return basic simplification

    return H_simplified


def compute_angular_momentum_2d(
    positions: List[sp.Symbol],
    momenta: List[sp.Symbol]
) -> sp.Expr:
    """
    Compute total angular momentum for 2D system.

    L = Σᵢ (xᵢ·pᵧᵢ - yᵢ·pₓᵢ)

    Args:
        positions: [x₁, y₁, x₂, y₂, ...]
        momenta: [pₓ₁, pᵧ₁, pₓ₂, pᵧ₂, ...]

    Returns:
        Angular momentum (scalar for 2D)
    """
    n_bodies = len(positions) // 2

    L = 0
    for i in range(n_bodies):
        x_i = positions[2*i]
        y_i = positions[2*i + 1]
        px_i = momenta[2*i]
        py_i = momenta[2*i + 1]

        L += x_i * py_i - y_i * px_i

    return L


class LiftedHamiltonianBase(ABC):
    """
    Abstract base class for lifted Hamiltonian systems.

    Subclasses must implement:
    - _construct_hamiltonian(): Build the extended Hamiltonian
    - _compute_connection(): Compute connection one-form (if applicable)
    """

    def __init__(
        self,
        base_hamiltonian: sp.Expr,
        base_coordinates: Tuple[sp.Symbol, ...],
        parameters: Dict[str, sp.Symbol]
    ):
        """
        Initialize lifted Hamiltonian.

        Args:
            base_hamiltonian: Downstairs Hamiltonian H(q, p)
            base_coordinates: Downstairs coordinates (q, p)
            parameters: System parameters
        """
        self.H_base = base_hamiltonian
        self.base_coords = base_coordinates
        self.params = parameters

        # To be set by subclass
        self.H_extended: Optional[sp.Expr] = None
        self.extended_coords: Optional[Tuple[sp.Symbol, ...]] = None
        self.connection: Optional[sp.Expr] = None

    @abstractmethod
    def _construct_hamiltonian(self) -> sp.Expr:
        """Construct extended Hamiltonian H̃."""
        pass

    @abstractmethod
    def _compute_connection(self) -> Optional[sp.Expr]:
        """Compute connection one-form (if applicable)."""
        pass

    def get_symbolic_system(self) -> SymbolicHamiltonianSystem:
        """
        Get SymbolicHamiltonianSystem representation.

        Returns:
            Complete symbolic system
        """
        if self.H_extended is None:
            self.H_extended = self._construct_hamiltonian()

        if self.connection is None:
            self.connection = self._compute_connection()

        n_base = len(self.base_coords) // 2
        n_extended = len(self.extended_coords) // 2

        return SymbolicHamiltonianSystem(
            H=self.H_extended,
            coordinates=self.extended_coords,
            parameters=self.params,
            dimension=n_extended,
            is_extended=True
        )
