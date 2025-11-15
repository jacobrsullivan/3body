"""
Physics-informed basis function library for symbolic regression (Task 3.3.2).

This module constructs hierarchical basis function libraries tailored to
the geometric structure of the three-body problem. The basis functions
are designed to:

1. Respect coordinate invariance (use geometric quantities)
2. Incorporate conservation laws (E, L, etc.)
3. Scale hierarchically (linear → quadratic → cubic → transcendental)
4. Avoid overfitting (physics-motivated restrictions)

The basis library is used by symbolic regression algorithms (SINDy, PySR)
to search for analytical expressions of conserved quantities.

References:
- Brunton et al., "Discovering governing equations from data" (2016)
- Champion et al., "Data-driven discovery of coordinates" (2019)
"""

import numpy as np
from typing import List, Tuple, Callable, Dict, Optional, Sequence
from dataclasses import dataclass
from enum import Enum


class CoordinateSystem(Enum):
    """Coordinate systems for three-body problem."""
    CARTESIAN = "cartesian"
    S1_BUNDLE = "s1_bundle"
    KS_SPINOR = "ks_spinor"
    SHAPE_SPACE = "shape_space"


@dataclass
class BasisFunction:
    """
    A single basis function for symbolic regression.

    Attributes:
        func: Callable that evaluates the function
        name: Human-readable name (e.g., "r12^2")
        symbol: SymPy-compatible symbol string
        degree: Polynomial degree (1=linear, 2=quadratic, etc., 0=transcendental)
        category: Type of function ('geometric', 'polynomial', 'transcendental', etc.)
        description: Optional longer description
    """
    func: Callable[[np.ndarray], float]
    name: str
    symbol: str
    degree: int
    category: str
    description: str = ""

    def evaluate(self, state: np.ndarray) -> float:
        """Evaluate basis function on a state."""
        return self.func(state)

    def evaluate_batch(self, states: np.ndarray) -> np.ndarray:
        """Evaluate on batch of states (N, dim)."""
        return np.array([self.func(state) for state in states])


class BasisLibrary:
    """
    Collection of basis functions for symbolic regression.

    Provides hierarchical construction of basis functions with
    physics-informed constraints.
    """

    def __init__(
        self,
        coordinate_system: CoordinateSystem = CoordinateSystem.CARTESIAN,
        masses: Optional[np.ndarray] = None
    ):
        """
        Initialize basis library.

        Args:
            coordinate_system: Type of coordinates used
            masses: Masses of the three bodies (if applicable)
        """
        self.coordinate_system = coordinate_system
        self.masses = masses if masses is not None else np.array([1.0, 1.0, 1.0])
        self.functions: List[BasisFunction] = []

    def add_function(self, basis_func: BasisFunction) -> None:
        """Add a basis function to the library."""
        self.functions.append(basis_func)

    def get_function_names(self) -> List[str]:
        """Get list of all function names."""
        return [f.name for f in self.functions]

    def get_function_symbols(self) -> List[str]:
        """Get list of all function symbols."""
        return [f.symbol for f in self.functions]

    def evaluate_library(self, state: np.ndarray) -> np.ndarray:
        """
        Evaluate all basis functions on a state.

        Args:
            state: Phase space state vector

        Returns:
            features: Array of evaluated basis functions (n_functions,)
        """
        return np.array([f.evaluate(state) for f in self.functions])

    def evaluate_library_batch(self, states: np.ndarray) -> np.ndarray:
        """
        Evaluate all basis functions on batch of states.

        Args:
            states: Batch of phase space states (N, dim)

        Returns:
            features: Feature matrix (N, n_functions)
        """
        N = len(states)
        n_funcs = len(self.functions)
        features = np.zeros((N, n_funcs))

        for j, func in enumerate(self.functions):
            features[:, j] = func.evaluate_batch(states)

        return features

    def filter_by_degree(self, max_degree: int) -> List[BasisFunction]:
        """Return functions up to specified degree."""
        return [f for f in self.functions if f.degree <= max_degree]

    def filter_by_category(self, category: str) -> List[BasisFunction]:
        """Return functions of specified category."""
        return [f for f in self.functions if f.category == category]


def construct_polynomial_basis(
    state_dim: int,
    max_degree: int = 3,
    include_cross_terms: bool = True
) -> List[BasisFunction]:
    """
    Construct polynomial basis functions.

    Args:
        state_dim: Dimension of phase space
        max_degree: Maximum polynomial degree
        include_cross_terms: Include mixed terms like z_i * z_j

    Returns:
        basis: List of polynomial basis functions

    Example:
        For dim=4, degree=2:
            Linear: z0, z1, z2, z3
            Quadratic: z0^2, z0*z1, ..., z3^2
    """
    basis = []

    # Constant (degree 0)
    basis.append(BasisFunction(
        func=lambda z: 1.0,
        name="1",
        symbol="1",
        degree=0,
        category="polynomial",
        description="Constant term"
    ))

    # Linear terms (degree 1)
    if max_degree >= 1:
        for i in range(state_dim):
            basis.append(BasisFunction(
                func=lambda z, i=i: z[i],
                name=f"z{i}",
                symbol=f"z_{i}",
                degree=1,
                category="polynomial",
                description=f"Linear term {i}"
            ))

    # Quadratic terms (degree 2)
    if max_degree >= 2:
        # Pure quadratic: z_i^2
        for i in range(state_dim):
            basis.append(BasisFunction(
                func=lambda z, i=i: z[i]**2,
                name=f"z{i}^2",
                symbol=f"z_{i}^2",
                degree=2,
                category="polynomial",
                description=f"Quadratic term z{i}^2"
            ))

        # Cross terms: z_i * z_j (i < j)
        if include_cross_terms:
            for i in range(state_dim):
                for j in range(i + 1, state_dim):
                    basis.append(BasisFunction(
                        func=lambda z, i=i, j=j: z[i] * z[j],
                        name=f"z{i}*z{j}",
                        symbol=f"z_{i} z_{j}",
                        degree=2,
                        category="polynomial",
                        description=f"Cross term z{i}*z{j}"
                    ))

    # Cubic terms (degree 3) - selective to avoid explosion
    if max_degree >= 3:
        # Pure cubic: z_i^3
        for i in range(state_dim):
            basis.append(BasisFunction(
                func=lambda z, i=i: z[i]**3,
                name=f"z{i}^3",
                symbol=f"z_{i}^3",
                degree=3,
                category="polynomial",
                description=f"Cubic term z{i}^3"
            ))

        # Selected mixed cubics: z_i^2 * z_j (limited to avoid too many terms)
        if include_cross_terms and state_dim <= 8:
            for i in range(min(state_dim, 4)):  # Limit to first 4 coordinates
                for j in range(state_dim):
                    if i != j:
                        basis.append(BasisFunction(
                            func=lambda z, i=i, j=j: z[i]**2 * z[j],
                            name=f"z{i}^2*z{j}",
                            symbol=f"z_{i}^2 z_{j}",
                            degree=3,
                            category="polynomial",
                            description=f"Cubic cross term z{i}^2*z{j}"
                        ))

    return basis


def construct_transcendental_basis(
    state_dim: int,
    functions: Optional[List[str]] = None
) -> List[BasisFunction]:
    """
    Construct transcendental basis functions.

    Args:
        state_dim: Dimension of phase space
        functions: List of function types to include
                   Options: 'sin', 'cos', 'exp', 'log', 'sqrt', 'tanh'

    Returns:
        basis: List of transcendental basis functions
    """
    if functions is None:
        functions = ['sin', 'cos']  # Default: periodic functions

    basis = []

    for i in range(state_dim):
        if 'sin' in functions:
            basis.append(BasisFunction(
                func=lambda z, i=i: np.sin(z[i]),
                name=f"sin(z{i})",
                symbol=f"\\sin(z_{i})",
                degree=0,  # Transcendental, not polynomial
                category="transcendental",
                description=f"Sine of z{i}"
            ))

        if 'cos' in functions:
            basis.append(BasisFunction(
                func=lambda z, i=i: np.cos(z[i]),
                name=f"cos(z{i})",
                symbol=f"\\cos(z_{i})",
                degree=0,
                category="transcendental",
                description=f"Cosine of z{i}"
            ))

        if 'exp' in functions:
            basis.append(BasisFunction(
                func=lambda z, i=i: np.exp(z[i]) if abs(z[i]) < 10 else np.sign(z[i]) * np.exp(10),
                name=f"exp(z{i})",
                symbol=f"\\exp(z_{i})",
                degree=0,
                category="transcendental",
                description=f"Exponential of z{i} (clipped)"
            ))

        if 'log' in functions:
            basis.append(BasisFunction(
                func=lambda z, i=i: np.log(abs(z[i]) + 1e-10),
                name=f"log(|z{i}|)",
                symbol=f"\\log(|z_{i}|)",
                degree=0,
                category="transcendental",
                description=f"Log of absolute value z{i}"
            ))

        if 'sqrt' in functions:
            basis.append(BasisFunction(
                func=lambda z, i=i: np.sqrt(abs(z[i])),
                name=f"sqrt(|z{i}|)",
                symbol=f"\\sqrt{{|z_{{{i}}}|}}",
                degree=0,
                category="transcendental",
                description=f"Square root of absolute value z{i}"
            ))

        if 'tanh' in functions:
            basis.append(BasisFunction(
                func=lambda z, i=i: np.tanh(z[i]),
                name=f"tanh(z{i})",
                symbol=f"\\tanh(z_{i})",
                degree=0,
                category="transcendental",
                description=f"Hyperbolic tangent of z{i}"
            ))

    return basis


def construct_conservation_basis(
    masses: np.ndarray,
    include_energy_powers: bool = True,
    include_angular_momentum_powers: bool = True
) -> List[BasisFunction]:
    """
    Construct basis functions from known conserved quantities.

    These are guaranteed to be conserved, useful for:
    - Validation (check if regression recovers known integrals)
    - Building blocks for more complex integrals

    Args:
        masses: Array of three body masses
        include_energy_powers: Include E^2, E^3, etc.
        include_angular_momentum_powers: Include L^2, L^3, etc.

    Returns:
        basis: List of conservation-based basis functions
    """
    basis = []

    # Energy (Hamiltonian)
    def compute_energy(z):
        """Compute total energy E = T + V."""
        n = len(z) // 2
        q = z[:n]
        p = z[n:]

        # Kinetic energy T = (1/2) sum_i p_i^2 / m_i
        # For 3-body in reduced coordinates, this is approximate
        # Proper implementation requires coordinate-specific formulas
        T = 0.5 * np.sum(p**2)  # Simplified

        # Potential energy V = -sum_{i<j} G m_i m_j / r_ij
        # Simplified - proper implementation needs position extraction
        V = 0.0  # Placeholder

        return T + V

    basis.append(BasisFunction(
        func=compute_energy,
        name="E",
        symbol="E",
        degree=2,  # Quadratic in momenta
        category="conservation",
        description="Total energy (Hamiltonian)"
    ))

    if include_energy_powers:
        basis.append(BasisFunction(
            func=lambda z: compute_energy(z)**2,
            name="E^2",
            symbol="E^2",
            degree=4,
            category="conservation",
            description="Energy squared"
        ))

    # Angular momentum magnitude
    def compute_L_magnitude(z):
        """Compute |L|."""
        # Placeholder - requires proper coordinate transformation
        return 1.0  # TODO: Implement

    basis.append(BasisFunction(
        func=compute_L_magnitude,
        name="L",
        symbol="L",
        degree=2,
        category="conservation",
        description="Angular momentum magnitude"
    ))

    if include_angular_momentum_powers:
        basis.append(BasisFunction(
            func=lambda z: compute_L_magnitude(z)**2,
            name="L^2",
            symbol="L^2",
            degree=4,
            category="conservation",
            description="Angular momentum squared"
        ))

    # Combined terms
    basis.append(BasisFunction(
        func=lambda z: compute_energy(z) * compute_L_magnitude(z),
        name="E*L",
        symbol="E L",
        degree=4,
        category="conservation",
        description="Energy times angular momentum"
    ))

    return basis


def construct_hierarchical_basis(
    state_dim: int,
    coordinate_system: CoordinateSystem = CoordinateSystem.CARTESIAN,
    masses: Optional[np.ndarray] = None,
    max_polynomial_degree: int = 2,
    include_transcendental: bool = False,
    include_conservation: bool = True
) -> BasisLibrary:
    """
    Construct complete hierarchical basis library.

    This is the main entry point for creating physics-informed basis functions
    for the three-body problem.

    Args:
        state_dim: Dimension of phase space (e.g., 6 for planar 3-body)
        coordinate_system: Type of coordinates
        masses: Body masses
        max_polynomial_degree: Maximum polynomial degree (1, 2, or 3)
        include_transcendental: Include sin, cos, etc.
        include_conservation: Include E, L, and their powers

    Returns:
        library: Complete BasisLibrary object

    Example:
        >>> library = construct_hierarchical_basis(
        ...     state_dim=8,
        ...     coordinate_system=CoordinateSystem.S1_BUNDLE,
        ...     max_polynomial_degree=2,
        ...     include_transcendental=False
        ... )
        >>> print(f"Total basis functions: {len(library.functions)}")
        >>> features = library.evaluate_library(state)
    """
    library = BasisLibrary(coordinate_system, masses)

    # Level 1: Polynomial basis
    poly_basis = construct_polynomial_basis(
        state_dim,
        max_degree=max_polynomial_degree,
        include_cross_terms=True
    )
    for func in poly_basis:
        library.add_function(func)

    # Level 2: Conservation-based functions
    if include_conservation and masses is not None:
        cons_basis = construct_conservation_basis(
            masses,
            include_energy_powers=(max_polynomial_degree >= 3),
            include_angular_momentum_powers=(max_polynomial_degree >= 3)
        )
        for func in cons_basis:
            library.add_function(func)

    # Level 3: Transcendental functions (optional)
    if include_transcendental:
        trans_basis = construct_transcendental_basis(
            state_dim,
            functions=['sin', 'cos']  # Conservative choice
        )
        for func in trans_basis:
            library.add_function(func)

    return library


def get_pysr_operators(
    max_complexity: int = 20,
    allow_division: bool = True,
    allow_transcendental: bool = False
) -> Dict[str, List[str]]:
    """
    Get operator lists for PySR symbolic regression.

    Args:
        max_complexity: Maximum expression complexity
        allow_division: Allow division operator (can be unstable)
        allow_transcendental: Allow sin, cos, exp, log

    Returns:
        operators: Dict with 'binary' and 'unary' operator lists

    Example:
        >>> ops = get_pysr_operators(allow_transcendental=True)
        >>> # Use with PySR: model = PySRRegressor(**ops)
    """
    binary = ["+", "-", "*"]
    if allow_division:
        binary.append("/")
    binary.append("^")  # Power operator

    unary = ["square", "cube"]
    if allow_transcendental:
        unary.extend(["sin", "cos", "exp", "log"])

    return {
        "binary_operators": binary,
        "unary_operators": unary,
        "maxsize": max_complexity
    }


# Example usage and testing
if __name__ == "__main__":
    # Example: Construct basis for S¹ bundle (4D configuration + 4D momentum = 8D)
    masses = np.array([1.0, 1.0, 1.0])

    library = construct_hierarchical_basis(
        state_dim=8,
        coordinate_system=CoordinateSystem.S1_BUNDLE,
        masses=masses,
        max_polynomial_degree=2,
        include_transcendental=False,
        include_conservation=True
    )

    print(f"Total basis functions: {len(library.functions)}")
    print(f"\nFirst 10 functions:")
    for i, func in enumerate(library.functions[:10]):
        print(f"  {i}: {func.name} (degree={func.degree}, category={func.category})")

    # Test evaluation
    test_state = np.random.randn(8)
    features = library.evaluate_library(test_state)
    print(f"\nEvaluated on random state: {features.shape}")
    print(f"First 5 feature values: {features[:5]}")
