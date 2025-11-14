"""
Riemann curvature tensor and scalar curvature.

The scalar curvature R of the JM metric is a diagnostic for chaos:
    R < 0  ⟺  Chaotic dynamics (sensitive dependence on initial conditions)
    R ≈ 0  ⟺  Approximately integrable
    R > 0  ⟺  Regular dynamics (rare for 3-body problem)

Mathematical Definitions:
    Ricci tensor:    R_ij = ∂_k Γ^k_ij - ∂_j Γ^k_ik + Γ^k_ij Γ^l_kl - Γ^k_il Γ^l_jk
    Scalar curvature: R = g^ij R_ij

Task: WP 2.1, Task 2.1.3, Part B
"""

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState
from .jm_metric import RiemannianMetric, compute_jm_metric
from .christoffel import (
    ChristoffelSymbols,
    compute_christoffel_symbols,
    compute_metric_derivatives,
    compute_christoffel_derivatives,
)


@dataclass(frozen=True)
class CurvatureTensors:
    """
    Curvature tensors at a point in shape space.

    Attributes:
        riemann: Riemann curvature tensor R^l_ijk (optional, expensive)
        ricci: Ricci tensor R_ij (n×n symmetric)
        scalar: Scalar curvature R (most important for chaos analysis)
        base_point: Shape space state where computed
    """

    ricci: np.ndarray  # Shape (n, n)
    scalar: float
    base_point: ShapeSpaceState
    riemann: Optional[np.ndarray] = None  # Shape (n, n, n, n) if computed

    @property
    def is_positive(self) -> bool:
        """True if scalar curvature is positive"""
        return self.scalar > 0

    @property
    def is_negative(self) -> bool:
        """True if scalar curvature is negative (chaotic)"""
        return self.scalar < 0

    def is_flat(self, tolerance: float = 1e-14) -> bool:
        """True if scalar curvature is approximately zero"""
        return abs(self.scalar) < tolerance


def compute_ricci_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> np.ndarray:
    """
    Compute Ricci tensor R_ij from Christoffel symbols.

    Formula:
        R_ij = ∂_k Γ^k_ij - ∂_j Γ^k_ik + Γ^k_ij Γ^l_kl - Γ^k_il Γ^l_jk

    Args:
        christoffel: Γ^k_ij
        christoffel_derivatives: ∂Γ^k_ij/∂x^l (4D array)

    Returns:
        R_ij: Ricci tensor (n×n symmetric matrix)

    Notes:
        - Ricci tensor is symmetric: R_ij = R_ji
        - Contracted form of Riemann tensor: R_ij = R^k_ikj
        - Measures "average" curvature in a direction
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives  # dGamma[l, k, i, j] = ∂Γ^k_ij/∂x^l

    n = Gamma.shape[0]
    ricci = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # First term: ∂_k Γ^k_ij
            for k in range(n):
                ricci[i, j] += dGamma[k, k, i, j]

            # Second term: -∂_j Γ^k_ik
            for k in range(n):
                ricci[i, j] -= dGamma[j, k, i, k]

            # Third term: Γ^k_ij Γ^l_kl
            for k in range(n):
                for l in range(n):
                    ricci[i, j] += Gamma[k, i, j] * Gamma[l, k, l]

            # Fourth term: -Γ^k_il Γ^l_jk
            for k in range(n):
                for l in range(n):
                    ricci[i, j] -= Gamma[k, i, l] * Gamma[l, j, k]

    # Symmetrize (should already be symmetric, but numerical errors)
    ricci = (ricci + ricci.T) / 2

    return ricci


def compute_scalar_curvature(
    metric: RiemannianMetric,
    ricci: np.ndarray
) -> float:
    """
    Compute scalar curvature R = g^ij R_ij.

    This is the trace of the Ricci tensor with respect to the metric.

    Args:
        metric: Metric tensor g_ij
        ricci: Ricci tensor R_ij

    Returns:
        R: Scalar curvature

    Physical Interpretation (for JM metric):
        - R < 0: Negative curvature → geodesics diverge → chaos
        - R = 0: Flat → may be integrable
        - R > 0: Positive curvature → geodesics converge → regular

    Example:
        >>> g = compute_jm_metric(state, masses, energy, L)
        >>> # ... compute Christoffel, derivatives ...
        >>> ricci = compute_ricci_tensor(christoffel, dGamma)
        >>> R = compute_scalar_curvature(g, ricci)
        >>> if R < 0:
        ...     print("Chaotic region!")
    """
    g_inv = metric.inverse()

    # Trace: R = g^ij R_ij
    R = np.trace(g_inv @ ricci)

    return R


def compute_curvature_tensors(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    compute_riemann: bool = False
) -> CurvatureTensors:
    """
    Complete pipeline: state → metric → Christoffel → curvature.

    This is the main entry point for computing scalar curvature.

    Args:
        shape_state: Point in shape space
        masses: Mass parameters
        energy: Total energy E
        L_magnitude: Angular momentum |L|
        compute_riemann: Whether to compute full Riemann tensor (expensive)

    Returns:
        CurvatureTensors with Ricci and scalar curvature

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> shape = ShapeSpaceState(r12=1.0, r23=1.2, r31=1.4,
        ...                          dr12_dt=0, dr23_dt=0, dr31_dt=0, L=1.0)
        >>> curv = compute_curvature_tensors(shape, masses, energy=-1.0, L_magnitude=1.0)
        >>> print(f"Scalar curvature: R = {curv.scalar:.6f}")
        >>> if curv.is_negative:
        ...     print("This configuration is chaotic!")

    Notes:
        - This is computationally expensive (second derivatives of metric)
        - May fail near metric singularities (E ≈ V_eff)
        - Consider caching results for repeated queries
    """
    # 1. Compute JM metric
    metric = compute_jm_metric(shape_state, masses, energy, L_magnitude)

    # 2. Compute metric derivatives
    metric_func = lambda s: compute_jm_metric(s, masses, energy, L_magnitude)
    dg = compute_metric_derivatives(metric_func, shape_state)

    # 3. Compute Christoffel symbols
    christoffel = compute_christoffel_symbols(metric, dg)

    # 4. Compute Christoffel derivatives
    christoffel_func = lambda s: compute_christoffel_symbols(
        metric_func(s),
        compute_metric_derivatives(metric_func, s)
    )
    dGamma = compute_christoffel_derivatives(christoffel_func, shape_state)

    # 5. Compute Ricci tensor
    ricci = compute_ricci_tensor(christoffel, dGamma)

    # 6. Compute scalar curvature
    R = compute_scalar_curvature(metric, ricci)

    # 7. Optionally compute full Riemann tensor
    riemann = None
    if compute_riemann:
        riemann = compute_riemann_tensor(christoffel, dGamma)

    return CurvatureTensors(
        ricci=ricci,
        scalar=R,
        base_point=shape_state,
        riemann=riemann
    )


def compute_riemann_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> np.ndarray:
    """
    Compute Riemann curvature tensor R^l_ijk.

    Formula:
        R^l_ijk = ∂_j Γ^l_ik - ∂_k Γ^l_ij + Γ^l_mj Γ^m_ik - Γ^l_mk Γ^m_ij

    Args:
        christoffel: Γ^k_ij
        christoffel_derivatives: ∂Γ^k_ij/∂x^l

    Returns:
        R^l_ijk: Riemann tensor (n×n×n×n array)

    Notes:
        - This is very expensive to compute and store
        - Usually not needed; Ricci and scalar curvature suffice
        - Has symmetries: R^l_ijk = -R^l_ikj, etc.
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives

    n = Gamma.shape[0]
    riemann = np.zeros((n, n, n, n))

    for l in range(n):
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    # First two terms: derivatives
                    riemann[l, i, j, k] += dGamma[j, l, i, k]  # ∂_j Γ^l_ik
                    riemann[l, i, j, k] -= dGamma[k, l, i, j]  # -∂_k Γ^l_ij

                    # Last two terms: quadratic in Christoffel
                    for m in range(n):
                        riemann[l, i, j, k] += Gamma[l, m, j] * Gamma[m, i, k]
                        riemann[l, i, j, k] -= Gamma[l, m, k] * Gamma[m, i, j]

    return riemann


def compute_curvature_field(
    shape_space_grid: list[ShapeSpaceState],
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    verbose: bool = False
) -> dict:
    """
    Compute scalar curvature at multiple points in shape space.

    Args:
        shape_space_grid: List of shape states
        masses: Mass parameters
        energy: Total energy
        L_magnitude: Angular momentum
        verbose: Print progress

    Returns:
        Dictionary with:
            - curvatures: Array of R values (NaN for invalid points)
            - valid_fraction: Fraction of points where R computed successfully
            - negative_fraction: Fraction with R < 0 (chaotic)
            - mean_curvature: Mean of valid curvatures

    Example:
        >>> grid = [ShapeSpaceState(r12=r1, r23=r2, r31=r3, ...)
        ...         for r1 in np.linspace(0.5, 2, 10)
        ...         for r2 in np.linspace(0.5, 2, 10)
        ...         for r3 in np.linspace(0.5, 2, 10)]
        >>> result = compute_curvature_field(grid, masses, energy=-1.0)
        >>> print(f"Negative curvature fraction: {result['negative_fraction']:.2%}")
    """
    N = len(shape_space_grid)
    curvatures = np.full(N, np.nan)

    for i, state in enumerate(shape_space_grid):
        if verbose and i % 100 == 0:
            print(f"Computing curvature: {i}/{N}")

        try:
            curv = compute_curvature_tensors(state, masses, energy, L_magnitude)
            curvatures[i] = curv.scalar
        except (ValueError, np.linalg.LinAlgError, ZeroDivisionError):
            # Invalid state or numerical issues
            pass

    # Statistics
    valid_mask = ~np.isnan(curvatures)
    valid_curvatures = curvatures[valid_mask]

    valid_fraction = np.sum(valid_mask) / N if N > 0 else 0.0
    negative_fraction = np.sum(valid_curvatures < 0) / len(valid_curvatures) if len(valid_curvatures) > 0 else 0.0
    mean_curvature = np.mean(valid_curvatures) if len(valid_curvatures) > 0 else 0.0

    return {
        'curvatures': curvatures,
        'valid_fraction': valid_fraction,
        'negative_fraction': negative_fraction,
        'mean_curvature': mean_curvature,
        'min_curvature': np.nanmin(curvatures) if np.any(valid_mask) else 0.0,
        'max_curvature': np.nanmax(curvatures) if np.any(valid_mask) else 0.0,
    }


def validate_ricci_symmetry(
    ricci: np.ndarray,
    tolerance: float = 1e-12
) -> bool:
    """
    Validate that Ricci tensor is symmetric.

    Args:
        ricci: Ricci tensor R_ij
        tolerance: Numerical tolerance

    Returns:
        True if symmetric
    """
    asymmetry = np.linalg.norm(ricci - ricci.T)
    return asymmetry < tolerance


def classify_curvature_regions(
    shape_space_grid: list[ShapeSpaceState],
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    threshold: float = 0.0
) -> dict:
    """
    Classify shape space regions by curvature sign.

    Args:
        shape_space_grid: Grid of shape states
        masses: Mass parameters
        energy: Total energy
        L_magnitude: Angular momentum
        threshold: Threshold for classification (default: 0)

    Returns:
        Dictionary with:
            - negative_indices: Indices where R < threshold (chaotic)
            - positive_indices: Indices where R > threshold (regular)
            - flat_indices: Indices where |R| ≤ threshold
            - invalid_indices: Indices where R couldn't be computed
    """
    negative_indices = []
    positive_indices = []
    flat_indices = []
    invalid_indices = []

    for i, state in enumerate(shape_space_grid):
        try:
            curv = compute_curvature_tensors(state, masses, energy, L_magnitude)

            if curv.scalar < -abs(threshold):
                negative_indices.append(i)
            elif curv.scalar > abs(threshold):
                positive_indices.append(i)
            else:
                flat_indices.append(i)

        except (ValueError, np.linalg.LinAlgError, ZeroDivisionError):
            invalid_indices.append(i)

    return {
        'negative_indices': negative_indices,
        'positive_indices': positive_indices,
        'flat_indices': flat_indices,
        'invalid_indices': invalid_indices,
    }
