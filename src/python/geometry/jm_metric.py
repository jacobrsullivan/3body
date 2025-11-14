"""
Jacobi-Maupertuis (JM) metric on shape space.

The JM metric is a Riemannian metric that encodes the dynamics at fixed energy.
Geodesics in this metric correspond to actual dynamical trajectories.

Mathematical Definition:
    g_JM = 2(E - V_eff) · g_shape

where:
    - E is the total energy (conserved)
    - V_eff is the effective potential (including centrifugal term)
    - g_shape is the induced metric on shape space

Physical Interpretation:
    The JM metric measures the "cost" of moving through shape space.
    Negative scalar curvature R < 0 is the geometric signature of chaos.

Task: WP 2.1, Task 2.1.3, Part A
"""

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState, shape_distances_to_cartesian_canonical
from ..coordinates.cartesian import compute_potential_energy, compute_energy
from .locked_inertia import compute_moment_of_inertia_planar


@dataclass(frozen=True)
class RiemannianMetric:
    """
    Riemannian metric tensor at a point in shape space.

    Represents g = g_ij dx^i ⊗ dx^j (symmetric positive-definite).

    Attributes:
        components: Symmetric matrix g_ij (3×3 for planar)
        coordinate_names: Names of coordinates
        base_point: Shape space state where metric is evaluated
    """

    components: np.ndarray  # Symmetric (n×n)
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def inverse(self) -> np.ndarray:
        """
        Compute contravariant metric g^ij.

        Returns:
            g^{-1} (n×n matrix)
        """
        return np.linalg.inv(self.components)

    def determinant(self) -> float:
        """
        Compute det(g).

        Returns:
            Determinant (positive for valid metric)
        """
        return np.linalg.det(self.components)

    def eigenvalues(self) -> np.ndarray:
        """
        Compute eigenvalues (principal axis lengths).

        Returns:
            Sorted eigenvalues (ascending)
        """
        return np.linalg.eigvalsh(self.components)

    def is_positive_definite(self, tolerance: float = 1e-14) -> bool:
        """
        Check if metric is positive definite.

        Returns:
            True if all eigenvalues > tolerance
        """
        eigenvals = self.eigenvalues()
        return np.all(eigenvals > tolerance)

    def trace(self) -> float:
        """
        Compute Tr(g) = Σ g_ii.

        Returns:
            Trace of metric
        """
        return np.trace(self.components)


def compute_effective_potential(
    shape_state: ShapeSpaceState,
    masses: Masses,
    L_magnitude: float,
    G: float = 1.0
) -> float:
    """
    Compute effective potential V_eff = V_grav + L²/(2I).

    The effective potential includes:
        1. Gravitational potential: V_grav = -Σ G m_i m_j / r_ij
        2. Centrifugal barrier: L²/(2I) where I is moment of inertia

    Args:
        shape_state: Configuration in shape space
        masses: Body masses
        L_magnitude: Angular momentum magnitude |L|
        G: Gravitational constant

    Returns:
        V_eff: Effective potential (scalar)

    Raises:
        ValueError: If configuration is invalid (collision)

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> shape = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0,
        ...                          dr12_dt=0, dr23_dt=0, dr31_dt=0, L=1.0)
        >>> V_eff = compute_effective_potential(shape, masses, L_magnitude=1.0)
        >>> print(f"V_eff = {V_eff:.6f}")
    """
    # Convert to Cartesian
    cart_state = shape_distances_to_cartesian_canonical(shape_state, masses)

    # Gravitational potential
    V_grav = compute_potential_energy(cart_state, masses, G)

    # Moment of inertia
    if shape_state.dimension == 2:
        I = compute_moment_of_inertia_planar(cart_state, masses)
    else:
        # For 3D, use full inertia tensor
        from .locked_inertia import compute_locked_inertia_tensor
        I_tensor = compute_locked_inertia_tensor(cart_state, masses)
        I = I_tensor.trace() / 2  # Average moment of inertia

    if I < 1e-14:
        raise ValueError("Degenerate configuration: I ≈ 0 (collision)")

    # Centrifugal term
    V_centrifugal = L_magnitude**2 / (2 * I)

    return V_grav + V_centrifugal


def compute_shape_space_metric(
    shape_state: ShapeSpaceState,
    masses: Masses,
    epsilon: float = 1e-6
) -> RiemannianMetric:
    """
    Compute induced metric on shape space via pullback.

    The shape space metric is obtained by pulling back the mass-weighted
    metric from Cartesian coordinates:

        g_shape = J^T · g_mass · J

    where J is the Jacobian of the embedding: shape → Cartesian.

    Args:
        shape_state: Point in shape space
        masses: Mass parameters
        epsilon: Step size for numerical Jacobian

    Returns:
        RiemannianMetric object

    Notes:
        - Uses finite differences to compute Jacobian
        - Metric is symmetric and positive-definite (for valid configurations)
    """
    # Compute Jacobian numerically
    jacobian = _compute_embedding_jacobian(shape_state, masses, epsilon)

    # Mass metric in Cartesian (diagonal)
    m = masses.as_array()
    if shape_state.dimension == 2:
        # Planar: 6 DOF (2D positions for 3 bodies)
        g_mass = np.diag(np.repeat(m, 2))
    else:
        # Spatial: 9 DOF
        g_mass = np.diag(np.repeat(m, 3))

    # Pullback: g_shape = J^T @ g_mass @ J
    g_shape = jacobian.T @ g_mass @ jacobian

    return RiemannianMetric(
        components=g_shape,
        coordinate_names=['r12', 'r23', 'r31'],
        base_point=shape_state
    )


def _compute_embedding_jacobian(
    shape_state: ShapeSpaceState,
    masses: Masses,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute Jacobian of embedding: shape → Cartesian.

    J_ij = ∂(Cartesian)_i / ∂(shape)_j

    Args:
        shape_state: Base point
        masses: Mass parameters
        epsilon: Finite difference step

    Returns:
        Jacobian matrix (6×3 for planar, 9×3 for spatial)
    """
    # Convert base state to Cartesian
    cart_base = shape_distances_to_cartesian_canonical(shape_state, masses)

    if shape_state.dimension == 2:
        n_cart = 6  # 3 bodies × 2D
    else:
        n_cart = 9  # 3 bodies × 3D

    n_shape = 3  # (r12, r23, r31)
    jacobian = np.zeros((n_cart, n_shape))

    # For each shape coordinate
    for j in range(n_shape):
        # Perturb shape coordinate j
        perturbed_state = _perturb_shape_coordinate(shape_state, j, epsilon)

        try:
            # Convert to Cartesian
            cart_perturbed = shape_distances_to_cartesian_canonical(perturbed_state, masses)

            # Finite difference: ∂(Cart)/∂(shape_j)
            delta_cart = (cart_perturbed.positions - cart_base.positions).ravel()

            if shape_state.dimension == 2:
                delta_cart = delta_cart[:6]  # Only x, y components

            jacobian[:, j] = delta_cart / epsilon

        except ValueError:
            # Perturbed state invalid
            jacobian[:, j] = 0.0

    return jacobian


def _perturb_shape_coordinate(
    shape_state: ShapeSpaceState,
    coord_index: int,
    delta: float
) -> ShapeSpaceState:
    """Perturb a single shape coordinate."""
    r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

    if coord_index == 0:
        r12 += delta
    elif coord_index == 1:
        r23 += delta
    elif coord_index == 2:
        r31 += delta

    # Check triangle inequality
    if not (r12 + r23 > r31 and r23 + r31 > r12 and r31 + r12 > r23):
        raise ValueError("Triangle inequality violated")

    return ShapeSpaceState(
        r12=r12, r23=r23, r31=r31,
        dr12_dt=shape_state.dr12_dt,
        dr23_dt=shape_state.dr23_dt,
        dr31_dt=shape_state.dr31_dt,
        L=shape_state.L,
        theta=shape_state.theta,
        dtheta_dt=shape_state.dtheta_dt,
        dimension=shape_state.dimension
    )


def compute_jm_metric(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    G: float = 1.0
) -> RiemannianMetric:
    """
    Compute Jacobi-Maupertuis metric: g_JM = 2(E - V_eff) · g_shape.

    The JM metric is defined on the energy shell H = E. Geodesics in this
    metric correspond to dynamical trajectories at fixed energy.

    Args:
        shape_state: Point in shape space
        masses: Body masses
        energy: Total energy E (conserved)
        L_magnitude: Angular momentum magnitude |L|
        G: Gravitational constant

    Returns:
        RiemannianMetric object (JM metric)

    Raises:
        ValueError: If E ≤ V_eff (classically forbidden region)

    Physical Interpretation:
        - Conformal factor 2(E - V_eff) represents "kinetic energy available"
        - Larger factor → easier to move (more kinetic energy)
        - At turning points (E = V_eff), metric degenerates

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> shape = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0,
        ...                          dr12_dt=0, dr23_dt=0, dr31_dt=0, L=1.0)
        >>> g_JM = compute_jm_metric(shape, masses, energy=-1.0, L_magnitude=1.0)
        >>> print(g_JM.determinant())
    """
    # Compute shape space metric
    g_shape = compute_shape_space_metric(shape_state, masses)

    # Compute effective potential
    V_eff = compute_effective_potential(shape_state, masses, L_magnitude, G)

    # Check classical accessibility
    if energy <= V_eff:
        raise ValueError(
            f"Classically forbidden: E = {energy:.6f} ≤ V_eff = {V_eff:.6f}"
        )

    # Conformal factor
    conformal_factor = 2 * (energy - V_eff)

    # JM metric
    g_jm = conformal_factor * g_shape.components

    return RiemannianMetric(
        components=g_jm,
        coordinate_names=g_shape.coordinate_names,
        base_point=shape_state
    )


def compute_jm_metric_field(
    shape_space_grid: list[ShapeSpaceState],
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0
) -> list[Optional[RiemannianMetric]]:
    """
    Compute JM metric at multiple points in shape space.

    Args:
        shape_space_grid: List of shape states
        masses: Mass parameters
        energy: Total energy
        L_magnitude: Angular momentum magnitude

    Returns:
        List of RiemannianMetric objects (None for classically forbidden points)
    """
    metrics = []

    for state in shape_space_grid:
        try:
            metric = compute_jm_metric(state, masses, energy, L_magnitude)
            metrics.append(metric)
        except ValueError:
            # Classically forbidden or invalid configuration
            metrics.append(None)

    return metrics


def find_classical_boundary(
    shape_space_region: tuple,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    resolution: int = 50
) -> list[ShapeSpaceState]:
    """
    Find boundary between classically allowed and forbidden regions.

    The boundary is defined by E = V_eff(q).

    Args:
        shape_space_region: ((r12_min, r12_max), (r23_min, r23_max))
        masses: Mass parameters
        energy: Total energy
        L_magnitude: Angular momentum
        resolution: Grid resolution

    Returns:
        List of shape states on the boundary

    Notes:
        - Boundary forms a surface in 3D shape space
        - At boundary, JM metric degenerates (turning point)
    """
    (r12_range, r23_range) = shape_space_region
    r12_grid = np.linspace(*r12_range, resolution)
    r23_grid = np.linspace(*r23_range, resolution)

    boundary_points = []

    for r12 in r12_grid:
        for r23 in r23_grid:
            # For fixed r12, r23, find r31 such that E = V_eff
            # This requires solving a nonlinear equation
            # Simplified: check several r31 values

            for r31_factor in np.linspace(0.1, 1.9, 20):
                r31 = (r12 + r23) * r31_factor / 2

                try:
                    state = ShapeSpaceState(
                        r12=r12, r23=r23, r31=r31,
                        dr12_dt=0, dr23_dt=0, dr31_dt=0,
                        L=L_magnitude,
                        dimension=2
                    )

                    V_eff = compute_effective_potential(state, masses, L_magnitude)

                    # Check if close to boundary
                    if abs(energy - V_eff) < 0.01:
                        boundary_points.append(state)

                except ValueError:
                    continue

    return boundary_points
