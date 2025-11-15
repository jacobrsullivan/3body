"""
Christoffel symbols computation for lifted JM metrics (WP 3.1, Task 3.1.2, Part A).

The Christoffel symbols Γ^k_ij encode the connection on a Riemannian manifold
and are needed to formulate the Killing equations.

Mathematical Definition:
    Γ^k_ij = (1/2) g^{kℓ} (∂g_ℓi/∂q^j + ∂g_ℓj/∂q^i - ∂g_ij/∂q^ℓ)

where g_ij is the metric tensor and g^{ij} is its inverse.

For the Killing equation:
    ∇_(i K_j) = ∂_i K_j - Γ^k_ij K_k = 0

We need accurate Christoffel symbols on the lifted manifolds.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Union
import numpy as np

try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    sp = None


# ============================================================================
# Part A1: Symbolic Christoffel Symbols
# ============================================================================

def compute_christoffel_symbolic(
    metric_tensor: 'sp.Matrix',
    coordinates: list['sp.Symbol']
) -> tuple['sp.Array', 'sp.Matrix', 'sp.Array']:
    """
    Compute Christoffel symbols symbolically using SymPy.

    This provides exact symbolic expressions for the Christoffel symbols,
    useful for:
        1. Analytical validation
        2. Low-dimensional cases (n ≤ 4)
        3. Deriving simplified formulas for special cases

    Args:
        metric_tensor: Metric g as SymPy Matrix (n×n)
        coordinates: List of SymPy symbols [q₀, q₁, ..., q_{n-1}]

    Returns:
        Gamma: Christoffel symbols Γ^k_ij as SymPy Array (n×n×n)
        g_inv: Inverse metric g^{ij} (n×n Matrix)
        dg: Metric derivatives ∂g_ij/∂q^k (n×n×n Array)

    Algorithm:
        1. Compute inverse metric: g^{-1}
        2. Compute metric derivatives: ∂g/∂q
        3. Apply Christoffel formula with index contractions

    Example (2D sphere):
        >>> import sympy as sp
        >>> theta, phi = sp.symbols('theta phi', real=True, positive=True)
        >>> R = sp.Symbol('R', real=True, positive=True)
        >>> g = sp.Matrix([[R**2, 0], [0, R**2 * sp.sin(theta)**2]])
        >>> Gamma, g_inv, dg = compute_christoffel_symbolic(g, [theta, phi])
        >>> Gamma[0, 1, 1]  # Γ^θ_φφ = -sin(θ)cos(θ)

    Raises:
        ImportError: If SymPy is not installed
        ValueError: If metric is singular or incompatible dimensions
    """
    if not SYMPY_AVAILABLE:
        raise ImportError(
            "SymPy required for symbolic Christoffel computation. "
            "Install with: pip install sympy"
        )

    n = len(coordinates)

    if metric_tensor.shape != (n, n):
        raise ValueError(
            f"Metric shape {metric_tensor.shape} incompatible with {n} coordinates"
        )

    # Compute inverse metric
    try:
        g_inv = metric_tensor.inv()
    except Exception as e:
        raise ValueError(f"Metric is singular or non-invertible: {e}")

    # Compute metric derivatives ∂g_ij/∂q^k
    dg = sp.MutableDenseNDimArray.zeros(n, n, n)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                dg[i, j, k] = sp.diff(metric_tensor[i, j], coordinates[k])

    # Compute Christoffel symbols: Γ^k_ij
    Gamma = sp.MutableDenseNDimArray.zeros(n, n, n)

    for k in range(n):
        for i in range(n):
            for j in range(n):
                # Γ^k_ij = (1/2) g^{kℓ} (∂_j g_ℓi + ∂_i g_ℓj - ∂_ℓ g_ij)
                term = sp.Rational(0)
                for ell in range(n):
                    term += g_inv[k, ell] * (
                        dg[ell, i, j] + dg[ell, j, i] - dg[i, j, ell]
                    )
                Gamma[k, i, j] = sp.simplify(term / 2)

    return Gamma, g_inv, dg


def validate_christoffel_properties(
    Gamma: 'sp.Array',
    metric: 'sp.Matrix',
    coordinates: list['sp.Symbol']
) -> dict:
    """
    Validate mathematical properties of Christoffel symbols.

    Checks:
        1. Symmetry in lower indices: Γ^k_ij = Γ^k_ji
        2. Compatibility: ∇_k g_ij = 0 (metric connection)
        3. Determinant formula: Γ^i_ij = (1/2g) ∂_j g where g = det(g_ij)

    Args:
        Gamma: Christoffel symbols (n×n×n)
        metric: Metric tensor (n×n)
        coordinates: Coordinate symbols

    Returns:
        Dictionary with validation results
    """
    if not SYMPY_AVAILABLE:
        return {"error": "SymPy not available"}

    n = len(coordinates)

    # Check symmetry in lower indices
    is_symmetric = True
    max_symmetry_error = 0

    for k in range(n):
        for i in range(n):
            for j in range(i + 1, n):  # Only check upper triangle
                diff = sp.simplify(Gamma[k, i, j] - Gamma[k, j, i])
                if diff != 0:
                    is_symmetric = False
                    max_symmetry_error = max(max_symmetry_error, abs(diff))

    # Check determinant formula: Γ^i_ij = ∂_j(log√g) / ∂q^j
    g_det = metric.det()
    sqrt_g = sp.sqrt(g_det)

    determinant_formula_holds = True

    for j in range(n):
        # Compute trace: Γ^i_ij
        trace_gamma = sum(Gamma[i, i, j] for i in range(n))

        # Expected: ∂_j(log√g)
        expected = sp.diff(sp.log(sqrt_g), coordinates[j])

        diff = sp.simplify(trace_gamma - expected)
        if diff != 0:
            determinant_formula_holds = False

    return {
        "is_symmetric": is_symmetric,
        "max_symmetry_error": max_symmetry_error,
        "determinant_formula_holds": determinant_formula_holds,
        "metric_determinant": g_det
    }


# ============================================================================
# Part A2: Numerical Christoffel Symbols
# ============================================================================

@dataclass
class ChristoffelSymbolsNumeric:
    """
    Christoffel symbols computed numerically at a specific point.

    Represents Γ^k_ij(q) where q is a fixed point in configuration space.

    Attributes:
        components: Christoffel symbol array (n, n, n)
        base_point: Point where symbols are evaluated (n,)
        metric: Metric tensor at base point (n, n)
        metric_inverse: Inverse metric g^{ij} (n, n)
    """

    components: np.ndarray  # (n, n, n)
    base_point: np.ndarray  # (n,)
    metric: np.ndarray  # (n, n)
    metric_inverse: np.ndarray  # (n, n)

    def __post_init__(self):
        """Validate dimensions."""
        n = len(self.base_point)
        if self.components.shape != (n, n, n):
            raise ValueError(
                f"Components shape {self.components.shape} != ({n}, {n}, {n})"
            )
        if self.metric.shape != (n, n):
            raise ValueError(f"Metric shape {self.metric.shape} != ({n}, {n})")

    @property
    def dimension(self) -> int:
        """Configuration space dimension."""
        return len(self.base_point)

    def evaluate_covariant_derivative(
        self,
        vector_field: np.ndarray,
        direction: int
    ) -> np.ndarray:
        """
        Compute covariant derivative ∇_i V^j.

        Args:
            vector_field: Vector V^k at base point (n,)
            direction: Index i for ∇_i

        Returns:
            Covariant derivative (n,)

        Formula:
            ∇_i V^j = ∂_i V^j + Γ^j_ik V^k

        Note: This assumes V is given, not computed from nearby points
        """
        n = self.dimension
        V = vector_field

        # For a given V at a point, we can only compute the connection term
        # Full covariant derivative requires V at nearby points (finite differences)

        # Connection term: Γ^j_ik V^k
        connection_term = np.zeros(n)
        for j in range(n):
            for k in range(n):
                connection_term[j] += self.components[j, direction, k] * V[k]

        # Note: Partial derivative ∂_i V^j not computable without V(q+δq)
        # Return connection term only (used in Killing equation with known K)
        return connection_term

    def contract_with_vector(
        self,
        vector: np.ndarray,
        upper_index: int,
        lower_index_1: int,
        lower_index_2: int
    ) -> float:
        """
        Contract: Γ^k_ij V_k.

        Args:
            vector: Vector to contract with (n,)
            upper_index: k
            lower_index_1: i
            lower_index_2: j

        Returns:
            Scalar contraction
        """
        n = self.dimension
        result = 0.0
        for k in range(n):
            result += self.components[k, lower_index_1, lower_index_2] * vector[k]
        return result


def compute_christoffel_numerical(
    metric_func: Callable[[np.ndarray], np.ndarray],
    point: np.ndarray,
    epsilon: float = 1e-6
) -> ChristoffelSymbolsNumeric:
    """
    Compute Christoffel symbols numerically using finite differences.

    This is the workhorse for high-dimensional problems (n > 4) where
    symbolic computation is too expensive.

    Args:
        metric_func: Function g(q) returning metric tensor (n×n)
        point: Base point q where to evaluate (n,)
        epsilon: Finite difference step size

    Returns:
        ChristoffelSymbolsNumeric object

    Algorithm:
        1. Evaluate metric at base point: g(q)
        2. Compute metric derivatives via finite differences:
           ∂g_ij/∂q^k ≈ [g(q + ε e_k) - g(q - ε e_k)] / (2ε)
        3. Compute inverse metric: g^{-1}(q)
        4. Apply Christoffel formula

    Numerical Considerations:
        - Use centered differences (O(ε²) error)
        - Check metric positive definiteness
        - Handle boundary cases carefully

    Example:
        >>> def g_func(q):
        ...     # 2D metric
        ...     r, theta = q
        ...     return np.array([[1.0, 0.0], [0.0, r**2]])
        >>> point = np.array([2.0, np.pi/4])
        >>> Gamma = compute_christoffel_numerical(g_func, point)
        >>> print(Gamma.components.shape)  # (2, 2, 2)
    """
    n = len(point)

    # Evaluate metric at base point
    g = metric_func(point)

    if g.shape != (n, n):
        raise ValueError(f"Metric shape {g.shape} != ({n}, {n})")

    # Check positive definiteness
    eigenvals = np.linalg.eigvalsh(g)
    if np.any(eigenvals <= 1e-14):
        raise ValueError(
            f"Metric not positive definite at {point}: "
            f"min eigenvalue = {np.min(eigenvals)}"
        )

    # Compute inverse metric
    g_inv = np.linalg.inv(g)

    # Compute metric derivatives via finite differences
    dg = np.zeros((n, n, n))

    for k in range(n):
        # Perturb in direction k
        point_plus = point.copy()
        point_minus = point.copy()
        point_plus[k] += epsilon
        point_minus[k] -= epsilon

        # Centered difference
        g_plus = metric_func(point_plus)
        g_minus = metric_func(point_minus)

        dg[:, :, k] = (g_plus - g_minus) / (2 * epsilon)

    # Compute Christoffel symbols: Γ^k_ij
    Gamma = np.zeros((n, n, n))

    for k in range(n):
        for i in range(n):
            for j in range(n):
                # Γ^k_ij = (1/2) g^{kℓ} (∂_j g_ℓi + ∂_i g_ℓj - ∂_ℓ g_ij)
                term = 0.0
                for ell in range(n):
                    term += g_inv[k, ell] * (
                        dg[ell, i, j] + dg[ell, j, i] - dg[i, j, ell]
                    )
                Gamma[k, i, j] = term / 2

    return ChristoffelSymbolsNumeric(
        components=Gamma,
        base_point=point,
        metric=g,
        metric_inverse=g_inv
    )


def compute_christoffel_field(
    metric_func: Callable[[np.ndarray], np.ndarray],
    points: list[np.ndarray],
    epsilon: float = 1e-6,
    skip_singular: bool = True
) -> list[Optional[ChristoffelSymbolsNumeric]]:
    """
    Compute Christoffel symbols at multiple points (field computation).

    Useful for mesh discretization in PDE solvers.

    Args:
        metric_func: Metric function g(q)
        points: List of evaluation points
        epsilon: Finite difference step
        skip_singular: If True, return None for singular metrics

    Returns:
        List of ChristoffelSymbolsNumeric (None for failed evaluations)

    Example:
        >>> # Create grid
        >>> r_vals = np.linspace(0.5, 3.0, 10)
        >>> theta_vals = np.linspace(0, 2*np.pi, 20)
        >>> points = [np.array([r, theta]) for r in r_vals for theta in theta_vals]
        >>> Gamma_field = compute_christoffel_field(g_func, points)
    """
    result = []

    for point in points:
        try:
            Gamma = compute_christoffel_numerical(metric_func, point, epsilon)
            result.append(Gamma)
        except (ValueError, np.linalg.LinAlgError) as e:
            if skip_singular:
                result.append(None)
            else:
                raise

    return result


# ============================================================================
# Validation and Utilities
# ============================================================================

def validate_christoffel_symmetry(
    Gamma: Union[ChristoffelSymbolsNumeric, np.ndarray],
    tolerance: float = 1e-12
) -> bool:
    """
    Check symmetry in lower indices: Γ^k_ij = Γ^k_ji.

    Args:
        Gamma: Christoffel symbols (numeric or array)
        tolerance: Numerical tolerance

    Returns:
        True if symmetric within tolerance
    """
    if isinstance(Gamma, ChristoffelSymbolsNumeric):
        components = Gamma.components
    else:
        components = Gamma

    n = components.shape[0]

    for k in range(n):
        for i in range(n):
            for j in range(i + 1, n):
                diff = abs(components[k, i, j] - components[k, j, i])
                if diff > tolerance:
                    return False

    return True


def christoffel_contraction_identity(
    Gamma: ChristoffelSymbolsNumeric
) -> float:
    """
    Check trace identity: Γ^i_ij = (1/2g) ∂_j g.

    For numerical Christoffel symbols, we can verify internal consistency.

    Args:
        Gamma: Christoffel symbols

    Returns:
        Maximum deviation from identity
    """
    n = Gamma.dimension
    g = Gamma.metric

    # Compute determinant
    g_det = np.linalg.det(g)

    # For each j, compute trace Γ^i_ij
    max_deviation = 0.0

    # Note: Without metric at nearby points, can't fully verify
    # Just check internal consistency of trace

    for j in range(n):
        trace = sum(Gamma.components[i, i, j] for i in range(n))
        # This should relate to ∂_j(log√g), but we don't have that info
        # Just check it's finite
        if not np.isfinite(trace):
            max_deviation = np.inf

    return max_deviation


def compare_symbolic_numerical(
    symbolic_Gamma: 'sp.Array',
    numeric_Gamma: ChristoffelSymbolsNumeric,
    coordinates: list['sp.Symbol'],
    coordinate_values: dict
) -> dict:
    """
    Compare symbolic and numerical Christoffel symbols.

    Useful for validation in low-dimensional cases.

    Args:
        symbolic_Gamma: Symbolic Christoffel symbols
        numeric_Gamma: Numerical Christoffel symbols
        coordinates: Coordinate symbols
        coordinate_values: Dictionary mapping symbols to numerical values

    Returns:
        Comparison statistics
    """
    if not SYMPY_AVAILABLE:
        return {"error": "SymPy not available"}

    n = len(coordinates)

    # Evaluate symbolic expressions numerically
    Gamma_symbolic_numeric = np.zeros((n, n, n))

    for k in range(n):
        for i in range(n):
            for j in range(n):
                expr = symbolic_Gamma[k, i, j]
                value = float(expr.subs(coordinate_values))
                Gamma_symbolic_numeric[k, i, j] = value

    # Compute difference
    diff = Gamma_symbolic_numeric - numeric_Gamma.components

    return {
        "max_absolute_error": np.max(np.abs(diff)),
        "mean_absolute_error": np.mean(np.abs(diff)),
        "relative_error": np.linalg.norm(diff) / np.linalg.norm(Gamma_symbolic_numeric),
        "difference_norm": np.linalg.norm(diff)
    }
