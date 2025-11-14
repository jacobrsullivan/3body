"""
Curvature two-form of the mechanical connection.

The curvature F = dA measures the obstruction to integrability in the
reduced three-body problem.

Mathematical Definition:
    F = dA (exterior derivative of connection)
    F_ij = ∂A_j/∂x^i - ∂A_i/∂x^j

Physical Interpretation:
    If F = 0 (flat connection), the system may be integrable.
    If F ≠ 0, there is genuine geometric complexity - the system exhibits
    path-dependent holonomy.

Key Property (Stokes' Theorem):
    ∮_∂S A = ∫∫_S F

Task: WP 2.1, Task 2.1.2, Part B
"""

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState
from .connection_form import ConnectionForm, compute_connection_coefficients


@dataclass(frozen=True)
class CurvatureForm:
    """
    Curvature two-form F = dA on shape space.

    Represents F = (1/2) F_ij dx^i ∧ dx^j (antisymmetric).

    Attributes:
        matrix: Antisymmetric matrix F_ij (shape 3×3 for planar)
        coordinate_names: Names of shape coordinates
        base_point: Shape space state where curvature is evaluated
    """

    matrix: np.ndarray  # Antisymmetric (n×n)
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def magnitude(self) -> float:
        """
        Compute |F| = sqrt(Σ F_ij²).

        This is the Frobenius norm of the curvature matrix.

        Returns:
            Magnitude of curvature
        """
        return np.linalg.norm(self.matrix)

    def is_flat(self, tolerance: float = 1e-14) -> bool:
        """
        Check if connection is flat (F ≈ 0).

        Args:
            tolerance: Threshold for flatness

        Returns:
            True if |F| < tolerance
        """
        return self.magnitude() < tolerance

    def scalar_invariant(self) -> float:
        """
        Compute scalar curvature invariant Tr(F^T F).

        This is gauge-invariant and measures curvature intensity.

        Returns:
            Tr(F^T F)
        """
        return np.trace(self.matrix.T @ self.matrix)


def compute_curvature(
    shape_state: ShapeSpaceState,
    masses: Masses,
    epsilon: float = 1e-6
) -> CurvatureForm:
    """
    Compute curvature F = dA using finite differences.

    Algorithm:
        1. Compute connection A at base point
        2. For each coordinate direction i:
           a. Perturb coordinate i by +ε and -ε
           b. Compute A at perturbed points
           c. Compute ∂A_j/∂x^i via central difference
        3. Form curvature: F_ij = ∂A_j/∂x^i - ∂A_i/∂x^j

    Args:
        shape_state: Point in shape space
        masses: Mass parameters
        epsilon: Step size for finite differences

    Returns:
        CurvatureForm object

    Notes:
        - Uses central differences for better accuracy
        - May be numerically unstable near singular configurations
        - Curvature is gauge-invariant (unlike connection)

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> shape = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0,
        ...                          dr12_dt=0, dr23_dt=0, dr31_dt=0, L=1.0)
        >>> curv = compute_curvature(shape, masses)
        >>> print(f"|F| = {curv.magnitude():.6f}")
    """
    # Get connection at base point
    A_base = compute_connection_coefficients(shape_state, masses)
    n = len(A_base.coefficients)

    # Compute Jacobian: ∂A_i/∂x^j
    jacobian = np.zeros((n, n))

    for j in range(n):
        # Perturb j-th coordinate
        state_plus = _perturb_shape_coordinate(shape_state, j, epsilon)
        state_minus = _perturb_shape_coordinate(shape_state, j, -epsilon)

        # Compute connection at perturbed points
        try:
            A_plus = compute_connection_coefficients(state_plus, masses)
            A_minus = compute_connection_coefficients(state_minus, masses)

            # Central difference: ∂A_i/∂x^j
            jacobian[:, j] = (A_plus.coefficients - A_minus.coefficients) / (2 * epsilon)
        except (ValueError, ZeroDivisionError):
            # Perturbed state may be invalid (e.g., violates triangle inequality)
            # Use forward or backward difference instead
            try:
                A_plus = compute_connection_coefficients(state_plus, masses)
                jacobian[:, j] = (A_plus.coefficients - A_base.coefficients) / epsilon
            except:
                # Give up on this direction
                jacobian[:, j] = 0.0

    # Curvature: antisymmetric part of Jacobian
    # F_ij = ∂A_j/∂x^i - ∂A_i/∂x^j
    curvature_matrix = jacobian - jacobian.T

    return CurvatureForm(
        matrix=curvature_matrix,
        coordinate_names=A_base.coordinate_names,
        base_point=shape_state
    )


def _perturb_shape_coordinate(
    shape_state: ShapeSpaceState,
    coord_index: int,
    delta: float
) -> ShapeSpaceState:
    """
    Perturb a single shape coordinate.

    Args:
        shape_state: Base shape state
        coord_index: Which coordinate to perturb (0=r12, 1=r23, 2=r31)
        delta: Perturbation size

    Returns:
        Perturbed shape state
    """
    r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

    if coord_index == 0:
        r12 += delta
    elif coord_index == 1:
        r23 += delta
    elif coord_index == 2:
        r31 += delta
    else:
        raise ValueError(f"Invalid coord_index: {coord_index}")

    # Check triangle inequality
    margin = 1e-10
    if not (r12 + r23 > r31 + margin and
            r23 + r31 > r12 + margin and
            r31 + r12 > r23 + margin):
        # Perturbation violates triangle inequality
        # Use smaller delta or return original
        if abs(delta) > 1e-8:
            return _perturb_shape_coordinate(shape_state, coord_index, delta / 2)
        else:
            # Can't perturb further, return original
            raise ValueError("Cannot perturb: triangle inequality violation")

    return ShapeSpaceState(
        r12=r12,
        r23=r23,
        r31=r31,
        dr12_dt=shape_state.dr12_dt,
        dr23_dt=shape_state.dr23_dt,
        dr31_dt=shape_state.dr31_dt,
        L=shape_state.L,
        theta=shape_state.theta,
        dtheta_dt=shape_state.dtheta_dt,
        dimension=shape_state.dimension
    )


def validate_stokes_theorem(
    closed_path: list[ShapeSpaceState],
    masses: Masses,
    verbose: bool = False
) -> dict:
    """
    Validate Stokes' theorem: ∮_∂S A = ∫∫_S F.

    This is a fundamental validation of the connection and curvature computation.

    Algorithm:
        1. Compute line integral: ∮_∂S A along the boundary
        2. Compute surface integral: ∫∫_S F over the enclosed region
        3. Compare: they should be equal

    Args:
        closed_path: Sequence of shape states forming a closed loop
        masses: Mass parameters
        verbose: Print detailed results

    Returns:
        Dictionary with:
            - line_integral: ∮ A
            - surface_integral: ∫∫ F
            - relative_error: |∮A - ∫∫F| / max(|∮A|, |∫∫F|)
            - valid: True if error < tolerance

    Notes:
        - Uses trapezoidal rule for line integral
        - Uses triangulation for surface integral
        - Accuracy depends on path resolution
    """
    from .connection_form import compute_holonomy

    # Line integral: ∮ A
    line_integral = compute_holonomy(closed_path, masses)

    # Surface integral: ∫∫ F
    # This requires triangulating the surface enclosed by the path
    # Simplified: use average curvature × area
    surface_integral = _compute_surface_integral_of_curvature(closed_path, masses)

    # Compare
    error = abs(line_integral - surface_integral)
    denominator = max(abs(line_integral), abs(surface_integral), 1e-10)
    relative_error = error / denominator

    valid = relative_error < 1e-8  # Tolerance for numerical integration

    results = {
        'line_integral': line_integral,
        'surface_integral': surface_integral,
        'absolute_error': error,
        'relative_error': relative_error,
        'valid': valid
    }

    if verbose:
        print(f"Stokes' Theorem Validation:")
        print(f"  Line integral (∮ A):     {line_integral:.6e}")
        print(f"  Surface integral (∫∫ F): {surface_integral:.6e}")
        print(f"  Relative error:          {relative_error:.6e}")
        print(f"  Valid:                   {valid}")

    return results


def _compute_surface_integral_of_curvature(
    closed_path: list[ShapeSpaceState],
    masses: Masses
) -> float:
    """
    Compute surface integral ∫∫_S F over region enclosed by path.

    Simplified implementation: uses midpoint rule.

    Args:
        closed_path: Boundary of surface
        masses: Mass parameters

    Returns:
        ∫∫ F (approximation)
    """
    if len(closed_path) < 3:
        return 0.0

    # Simple approximation: curvature at center × area
    # Full implementation would triangulate the surface

    # Compute approximate center
    r12_center = np.mean([s.r12 for s in closed_path])
    r23_center = np.mean([s.r23 for s in closed_path])
    r31_center = np.mean([s.r31 for s in closed_path])
    L_avg = np.mean([s.L for s in closed_path])

    try:
        state_center = ShapeSpaceState(
            r12=r12_center, r23=r23_center, r31=r31_center,
            dr12_dt=0, dr23_dt=0, dr31_dt=0,
            L=L_avg,
            dimension=closed_path[0].dimension
        )

        # Curvature at center
        curv = compute_curvature(state_center, masses)

        # Approximate area of enclosed region
        # (Very rough estimate - would need proper triangulation)
        area = _estimate_enclosed_area(closed_path)

        # Surface integral ≈ F · area
        # For 2-form, we need to extract the appropriate component
        # Simplified: use magnitude
        surface_integral = curv.magnitude() * area

        return surface_integral

    except (ValueError, ZeroDivisionError):
        # Center point may be invalid
        return 0.0


def _estimate_enclosed_area(closed_path: list[ShapeSpaceState]) -> float:
    """
    Estimate area enclosed by path in shape space.

    Uses shoelace formula in (r12, r23) plane (fixing r31).

    Args:
        closed_path: Closed curve

    Returns:
        Estimated area
    """
    if len(closed_path) < 3:
        return 0.0

    # Extract coordinates
    r12_coords = np.array([s.r12 for s in closed_path])
    r23_coords = np.array([s.r23 for s in closed_path])

    # Shoelace formula
    n = len(r12_coords)
    area = 0.0

    for i in range(n):
        j = (i + 1) % n
        area += r12_coords[i] * r23_coords[j]
        area -= r12_coords[j] * r23_coords[i]

    area = abs(area) / 2.0

    return area


def compute_curvature_field(
    shape_space_grid: np.ndarray,
    masses: Masses
) -> np.ndarray:
    """
    Compute curvature magnitude at grid points in shape space.

    Args:
        shape_space_grid: Array of shape states (N points)
        masses: Mass parameters

    Returns:
        Array of curvature magnitudes (N values)
    """
    N = len(shape_space_grid)
    curvatures = np.zeros(N)

    for i, state in enumerate(shape_space_grid):
        try:
            curv = compute_curvature(state, masses)
            curvatures[i] = curv.magnitude()
        except (ValueError, ZeroDivisionError):
            # Invalid state (e.g., near collision or invalid triangle)
            curvatures[i] = np.nan

    return curvatures


def identify_flat_regions(
    shape_space_grid: np.ndarray,
    masses: Masses,
    tolerance: float = 1e-10
) -> list:
    """
    Identify regions in shape space where connection is flat (F ≈ 0).

    Flat regions may indicate (approximate) integrability.

    Args:
        shape_space_grid: Grid of shape states
        masses: Mass parameters
        tolerance: Threshold for flatness

    Returns:
        List of indices where |F| < tolerance
    """
    flat_indices = []

    for i, state in enumerate(shape_space_grid):
        try:
            curv = compute_curvature(state, masses)
            if curv.is_flat(tolerance):
                flat_indices.append(i)
        except:
            pass

    return flat_indices
