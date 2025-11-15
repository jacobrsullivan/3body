"""
Jacobi-Maupertuis metrics on lifted manifolds (WP 3.1, Task 3.1.1).

This module extends the JM metric from shape space to the higher-dimensional
lifted spaces constructed in WP2:
    - S¹ principal bundle (WP 2.2)
    - KS-Spinor regularized manifold (WP 2.3)

The lifted JM metrics enable the geometric search for hidden conserved
quantities via Killing field equations (Task 3.1.2).

Mathematical Framework:
    On a configuration manifold Q with metric g, the JM metric is:
        g_JM(q) = 2(E - V(q)) · g(q)

    Geodesics of g_JM (with respect to action parameter) are trajectories
    of the mechanical system at fixed energy E.

    Key Insight: Hidden symmetries appear as Killing structures of g_JM.
"""

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState, shape_distances_to_cartesian_canonical
from ..coordinates.cartesian import compute_potential_energy
from ..lifts.s1_bundle import BundleState, S1Bundle
from .jm_metric import (
    RiemannianMetric,
    compute_shape_space_metric,
    compute_effective_potential
)
from .connection_form import compute_connection_coefficients, ConnectionForm
from .locked_inertia import compute_moment_of_inertia_planar


# ============================================================================
# Part A: S¹ Bundle JM Metric
# ============================================================================

@dataclass(frozen=True)
class BundleMetric:
    """
    Metric tensor on S¹ principal bundle P = Shape Space × S¹.

    This is a 4×4 matrix representing:
        g_lift = [ g_shape    -A  ]
                 [  -A^T       1  ]

    where:
        - g_shape: 3×3 shape space metric
        - A: 3×1 connection one-form coefficients
        - 1: scalar fiber metric

    Attributes:
        components: Full 4×4 metric tensor
        base_metric: 3×3 shape space metric g_shape
        connection: Connection form A
        base_point: Bundle state where metric is evaluated
    """

    components: np.ndarray  # (4, 4)
    base_metric: RiemannianMetric  # Shape space metric
    connection: ConnectionForm
    base_point: BundleState

    def inverse(self) -> np.ndarray:
        """Compute contravariant metric g^{ij}."""
        return np.linalg.inv(self.components)

    def determinant(self) -> float:
        """Compute det(g_lift)."""
        return np.linalg.det(self.components)

    def eigenvalues(self) -> np.ndarray:
        """Compute eigenvalues (sorted ascending)."""
        return np.linalg.eigvalsh(self.components)

    def is_positive_definite(self, tolerance: float = 1e-14) -> bool:
        """Check if metric is positive definite."""
        eigenvals = self.eigenvalues()
        return np.all(eigenvals > tolerance)

    def extract_shape_block(self) -> np.ndarray:
        """Extract 3×3 shape space block."""
        return self.components[:3, :3]

    def extract_fiber_component(self) -> float:
        """Extract fiber metric component g_θθ."""
        return self.components[3, 3]


def compute_s1_bundle_metric(
    bundle_state: BundleState,
    masses: Masses,
    epsilon: float = 1e-6
) -> BundleMetric:
    """
    Compute lifted metric on S¹ bundle (WP 2.2).

    The metric on the total space P = S × S¹ is:
        g_lift = g_shape + (dθ - A)²

    In matrix form:
        g_lift = [ g_shape    -A  ]
                 [  -A^T       1  ]

    where A is the mechanical connection one-form.

    Args:
        bundle_state: Point in S¹ bundle
        masses: Mass parameters
        epsilon: For numerical derivatives

    Returns:
        BundleMetric object (4×4 tensor)

    Physical Interpretation:
        - The connection A couples shape motion to fiber rotation
        - If A = 0, bundle is trivial (product metric)
        - |A| measures the "magnetic twist" obstructing integrability

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> shape = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0,
        ...                          dr12_dt=0, dr23_dt=0, dr31_dt=0, L=1.0)
        >>> bundle_state = BundleState(shape, theta=0.0,
        ...                             shape_momenta=np.zeros(3), p_theta=0.0)
        >>> g_lift = compute_s1_bundle_metric(bundle_state, masses)
        >>> assert g_lift.is_positive_definite()
    """
    # Extract shape space projection
    shape_state = bundle_state.shape_state

    # Compute shape space metric (3×3)
    g_shape = compute_shape_space_metric(shape_state, masses, epsilon)

    # Compute connection form (3-component vector)
    connection = compute_connection_coefficients(shape_state, masses)

    # Assemble 4×4 bundle metric
    g_lift = np.zeros((4, 4))

    # Upper-left 3×3 block: shape metric
    g_lift[:3, :3] = g_shape.components

    # Off-diagonal: -A (coupling between shape and fiber)
    g_lift[:3, 3] = -connection.coefficients
    g_lift[3, :3] = -connection.coefficients

    # Lower-right: fiber metric (standard S¹ metric)
    g_lift[3, 3] = 1.0

    return BundleMetric(
        components=g_lift,
        base_metric=g_shape,
        connection=connection,
        base_point=bundle_state
    )


def compute_s1_jm_metric(
    bundle_state: BundleState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    G: float = 1.0,
    epsilon: float = 1e-6
) -> BundleMetric:
    """
    Compute Jacobi-Maupertuis metric on S¹ bundle (Task 3.1.1, Part A4).

    This is the core computation for WP 3.1 geometric search.

    Mathematical Formula:
        g_JM^(S¹) = 2(E - V_eff(s)) · g_lift(s, θ)

    where:
        - E: Total energy (conserved)
        - V_eff(s): Effective potential (gravitational + centrifugal)
        - g_lift: Lifted metric on S¹ bundle

    Args:
        bundle_state: Point in S¹ bundle (s, θ)
        masses: Body masses
        energy: Total energy E
        L_magnitude: Angular momentum magnitude |L|
        G: Gravitational constant
        epsilon: Numerical differentiation step

    Returns:
        BundleMetric with JM conformal factor applied

    Raises:
        ValueError: If E ≤ V_eff (classically forbidden region)

    Physical Significance:
        - Geodesics in g_JM are dynamical trajectories
        - Killing fields → conserved quantities
        - Negative curvature → geometric signature of chaos

    Usage in WP 3.1:
        This metric is input to Task 3.1.2 (Killing PDE formulation).
    """
    # Extract shape space projection
    shape_state = bundle_state.shape_state

    # Compute effective potential
    V_eff = compute_effective_potential(shape_state, masses, L_magnitude, G)

    # Check classical accessibility
    if energy <= V_eff:
        raise ValueError(
            f"Classically forbidden: E = {energy:.6f} ≤ V_eff = {V_eff:.6f} "
            f"at shape ({shape_state.r12:.3f}, {shape_state.r23:.3f}, {shape_state.r31:.3f})"
        )

    # Compute lifted metric (kinetic part)
    g_lift = compute_s1_bundle_metric(bundle_state, masses, epsilon)

    # Apply JM conformal factor
    conformal_factor = 2 * (energy - V_eff)
    g_jm_components = conformal_factor * g_lift.components

    return BundleMetric(
        components=g_jm_components,
        base_metric=g_lift.base_metric,  # Base metric also scaled
        connection=g_lift.connection,
        base_point=bundle_state
    )


def compute_s1_jm_metric_field(
    bundle_states: list[BundleState],
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0
) -> list[Optional[BundleMetric]]:
    """
    Compute JM metric at multiple points in S¹ bundle.

    Useful for generating meshes for PDE discretization (Task 3.1.2).

    Args:
        bundle_states: List of points in bundle
        masses: Mass parameters
        energy: Total energy
        L_magnitude: Angular momentum

    Returns:
        List of BundleMetric objects (None for classically forbidden points)

    Notes:
        - Skips points where E ≤ V_eff
        - Can be parallelized over bundle_states
    """
    metrics = []

    for state in bundle_states:
        try:
            metric = compute_s1_jm_metric(state, masses, energy, L_magnitude)
            metrics.append(metric)
        except ValueError:
            # Classically forbidden or invalid
            metrics.append(None)

    return metrics


# ============================================================================
# Part B: KS-Spinor Manifold JM Metric
# ============================================================================

@dataclass(frozen=True)
class KSSpinorCoords:
    """
    Coordinates on KS-Spinor constrained manifold (WP 2.3).

    Three 4D spinors representing pairwise relative vectors via
    Kustaanheimo-Stiefel transformation.

    Configuration Space Dimension: 9 (intrinsic, after constraints)
                                    12 (extrinsic, before constraints)

    Constraints (3 equations):
        Triangle closure: r₁₂ + r₂₃ + r₃₁ = 0
        where r_ij = L(u_ij) u_ij (Levi-Civita matrix)

    Attributes:
        u12: Spinor for pair (1,2) ∈ ℝ⁴
        u23: Spinor for pair (2,3) ∈ ℝ⁴
        u31: Spinor for pair (3,1) ∈ ℝ⁴
    """

    u12: np.ndarray  # (4,)
    u23: np.ndarray  # (4,)
    u31: np.ndarray  # (4,)

    def __post_init__(self):
        """Validate dimensions."""
        for name, spinor in [('u12', self.u12), ('u23', self.u23), ('u31', self.u31)]:
            spinor_arr = np.asarray(spinor)
            if spinor_arr.shape != (4,):
                raise ValueError(f"{name} must be (4,), got {spinor_arr.shape}")
            object.__setattr__(self, name, spinor_arr)

    def to_array(self) -> np.ndarray:
        """Flatten to 12D vector."""
        return np.concatenate([self.u12, self.u23, self.u31])

    @classmethod
    def from_array(cls, u: np.ndarray) -> "KSSpinorCoords":
        """Construct from flat 12D vector."""
        if len(u) != 12:
            raise ValueError(f"Expected 12D vector, got {len(u)}")
        return cls(u12=u[:4], u23=u[4:8], u31=u[8:12])

    def check_constraints(self, tolerance: float = 1e-12) -> bool:
        """
        Verify triangle closure constraint.

        Returns:
            True if constraints satisfied within tolerance
        """
        from ..regularization.levi_civita import levi_civita_transform

        r12 = levi_civita_transform(self.u12)
        r23 = levi_civita_transform(self.u23)
        r31 = levi_civita_transform(self.u31)

        residual = np.linalg.norm(r12 + r23 + r31)
        return residual < tolerance


@dataclass(frozen=True)
class KSMetric:
    """
    Metric tensor on KS-Spinor constrained manifold.

    Intrinsic: 9×9 (on constraint surface)
    Extrinsic: 12×12 (in ambient ℝ¹²)

    Attributes:
        components: Metric tensor (9×9 or 12×12)
        intrinsic: Whether metric is projected onto constraint surface
        base_point: KS coordinates where metric is evaluated
    """

    components: np.ndarray  # (9,9) or (12,12)
    intrinsic: bool
    base_point: KSSpinorCoords

    @property
    def dimension(self) -> int:
        """Dimension of metric (9 or 12)."""
        return self.components.shape[0]

    def inverse(self) -> np.ndarray:
        """Compute contravariant metric."""
        return np.linalg.inv(self.components)

    def eigenvalues(self) -> np.ndarray:
        """Compute eigenvalues."""
        return np.linalg.eigvalsh(self.components)

    def is_positive_definite(self, tolerance: float = 1e-14) -> bool:
        """Check positive definiteness."""
        eigenvals = self.eigenvalues()
        return np.all(eigenvals > tolerance)


def compute_ks_mass_matrix(
    ks_coords: KSSpinorCoords,
    masses: Masses,
    intrinsic: bool = True
) -> KSMetric:
    """
    Compute mass matrix (kinetic energy metric) in KS spinor coordinates.

    The mass matrix M relates spinor velocities to kinetic energy:
        T = (1/2) u̇ᵀ M u̇

    Args:
        ks_coords: Point in KS-Spinor space
        masses: Body masses
        intrinsic: If True, project onto 9D constraint surface

    Returns:
        KSMetric object (9×9 or 12×12)

    Algorithm:
        1. Compute Jacobian J = ∂r/∂u (transformation to Cartesian)
        2. Pull back mass-weighted metric: M = JᵀGJ
        3. If intrinsic: project onto null space of constraints

    Notes:
        - Extrinsic (12×12) is degenerate (rank 9)
        - Intrinsic (9×9) is non-degenerate on constraint surface
        - Implementation requires KS transformation Jacobian
    """
    from ..regularization.levi_civita import levi_civita_jacobian

    # Compute Jacobians for each pair
    J12 = levi_civita_jacobian(ks_coords.u12)  # (3, 4)
    J23 = levi_civita_jacobian(ks_coords.u23)
    J31 = levi_civita_jacobian(ks_coords.u31)

    # Mass matrix in Cartesian (diagonal)
    m = masses.as_array()
    G_mass = np.diag(np.repeat(m, 3))  # (9, 9)

    # Full Jacobian: Cartesian → KS (9, 12)
    # r₁ = f(u12, u23), r₂ = g(u12, u23), r₃ = h(u23, u31)
    # This requires careful assembly based on triangle closure

    # Simplified approach: each pair contributes independently (approximate)
    # Full derivation in WP 2.3 documentation

    # Placeholder for full implementation
    # TODO: Complete Jacobian assembly
    M_ext = np.eye(12) * np.mean(m)  # Temporary placeholder

    if intrinsic:
        # Project onto constraint surface
        C_jac = _compute_ks_constraint_jacobian(ks_coords)  # (3, 12)
        Z = _null_space(C_jac)  # (12, 9) - basis for tangent space

        M_int = Z.T @ M_ext @ Z  # (9, 9)

        return KSMetric(
            components=M_int,
            intrinsic=True,
            base_point=ks_coords
        )
    else:
        return KSMetric(
            components=M_ext,
            intrinsic=False,
            base_point=ks_coords
        )


def compute_ks_potential(
    ks_coords: KSSpinorCoords,
    masses: Masses,
    G: float = 1.0
) -> float:
    """
    Compute gravitational potential in KS spinor coordinates.

    Uses bilinear relation: r_ij = |u_ij|²

    Args:
        ks_coords: Spinor coordinates
        masses: Body masses
        G: Gravitational constant

    Returns:
        V: Gravitational potential (scalar)

    Formula:
        V = -G Σᵢ<ⱼ (mᵢmⱼ / rᵢⱼ)
        where rᵢⱼ = |uᵢⱼ|²

    Key Advantage of KS:
        Potential remains smooth even at collisions (rᵢⱼ → 0)
        since u → 0 smoothly (regularization).
    """
    m = masses.as_array()

    # Bilinear relation: r_ij = |u_ij|²
    r12_squared = np.linalg.norm(ks_coords.u12)**2
    r23_squared = np.linalg.norm(ks_coords.u23)**2
    r31_squared = np.linalg.norm(ks_coords.u31)**2

    # Avoid division by zero
    eps = 1e-16
    r12 = np.sqrt(r12_squared + eps)
    r23 = np.sqrt(r23_squared + eps)
    r31 = np.sqrt(r31_squared + eps)

    V = -G * (
        m[0] * m[1] / r12 +
        m[1] * m[2] / r23 +
        m[2] * m[0] / r31
    )

    return V


def compute_ks_jm_metric(
    ks_coords: KSSpinorCoords,
    masses: Masses,
    energy: float,
    G: float = 1.0,
    intrinsic: bool = True
) -> KSMetric:
    """
    Compute Jacobi-Maupertuis metric on KS-Spinor manifold (Task 3.1.1, Part B3).

    Formula:
        g_JM^(KS) = 2(E - V(u)) · M(u)

    where:
        - M(u): Mass matrix in spinor coordinates
        - V(u): Gravitational potential

    Args:
        ks_coords: Point in KS-Spinor space
        masses: Body masses
        energy: Total energy
        G: Gravitational constant
        intrinsic: Use 9D intrinsic metric (vs. 12D extrinsic)

    Returns:
        KSMetric with JM conformal factor applied

    Raises:
        ValueError: If E ≤ V (classically forbidden)

    Physical Significance:
        - KS transformation regularizes collisions
        - Hidden symmetries may appear as SU(2) structure in spinor space
        - Geodesics integrate smoothly through near-collisions
    """
    # Verify constraints
    if not ks_coords.check_constraints():
        raise ValueError("KS coordinates violate triangle closure constraint")

    # Compute potential
    V = compute_ks_potential(ks_coords, masses, G)

    # Check classical accessibility
    if energy <= V:
        raise ValueError(f"Classically forbidden: E = {energy:.6f} ≤ V = {V:.6f}")

    # Compute mass matrix
    M = compute_ks_mass_matrix(ks_coords, masses, intrinsic)

    # Apply JM conformal factor
    conformal_factor = 2 * (energy - V)
    g_jm = conformal_factor * M.components

    return KSMetric(
        components=g_jm,
        intrinsic=intrinsic,
        base_point=ks_coords
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _compute_ks_constraint_jacobian(ks_coords: KSSpinorCoords) -> np.ndarray:
    """
    Compute Jacobian of triangle closure constraints: ∂C/∂u.

    Constraints: C(u) = r₁₂(u₁₂) + r₂₃(u₂₃) + r₃₁(u₃₁) = 0

    Returns:
        Jacobian matrix (3, 12)
    """
    from ..regularization.levi_civita import levi_civita_jacobian

    J12 = levi_civita_jacobian(ks_coords.u12)  # (3, 4)
    J23 = levi_civita_jacobian(ks_coords.u23)
    J31 = levi_civita_jacobian(ks_coords.u31)

    # Assemble full constraint Jacobian
    C_jac = np.zeros((3, 12))
    C_jac[:, 0:4] = J12
    C_jac[:, 4:8] = J23
    C_jac[:, 8:12] = J31

    return C_jac


def _null_space(A: np.ndarray, tolerance: float = 1e-12) -> np.ndarray:
    """
    Compute null space of matrix A using SVD.

    Args:
        A: Matrix (m, n)
        tolerance: Threshold for zero singular values

    Returns:
        Null space basis (n, k) where k = nullity
    """
    U, s, Vh = np.linalg.svd(A, full_matrices=True)

    # Find null singular values
    null_mask = s < tolerance

    # Null space is right singular vectors corresponding to zero singular values
    # Note: Vh is (n, n), we want columns where s[i] ≈ 0
    # Since s is (min(m,n),), we need to pad if m < n
    n = A.shape[1]
    m = A.shape[0]

    if m < n:
        # Null space has dimension n - m
        null_vecs = Vh[m:, :].T  # Last (n-m) rows of Vh
    else:
        null_vecs = Vh[null_mask, :].T

    return null_vecs


# ============================================================================
# Validation and Diagnostics
# ============================================================================

def validate_s1_metric_properties(
    metric: BundleMetric,
    tolerance: float = 1e-10
) -> dict:
    """
    Validate mathematical properties of S¹ bundle metric.

    Checks:
        1. Symmetry: g_ij = g_ji
        2. Positive definiteness: all eigenvalues > 0
        3. Block structure: correct shape/fiber coupling

    Args:
        metric: BundleMetric to validate
        tolerance: Numerical tolerance

    Returns:
        Dictionary with validation results
    """
    g = metric.components

    # Check symmetry
    symmetry_error = np.linalg.norm(g - g.T)
    is_symmetric = symmetry_error < tolerance

    # Check positive definiteness
    eigenvals = metric.eigenvalues()
    is_pos_def = np.all(eigenvals > tolerance)
    min_eigenvalue = np.min(eigenvals)

    # Check block structure
    g_shape_extracted = metric.extract_shape_block()
    g_shape_expected = metric.base_metric.components
    block_error = np.linalg.norm(g_shape_extracted - g_shape_expected)
    correct_structure = block_error < tolerance

    return {
        'is_symmetric': is_symmetric,
        'symmetry_error': symmetry_error,
        'is_positive_definite': is_pos_def,
        'min_eigenvalue': min_eigenvalue,
        'correct_block_structure': correct_structure,
        'block_error': block_error
    }


def compare_s1_vs_base_metric(
    bundle_metric: BundleMetric,
    shape_metric: RiemannianMetric,
    connection: ConnectionForm
) -> dict:
    """
    Compare S¹ bundle metric to base shape space metric.

    Quantifies the effect of the connection A on the lifted metric.

    Args:
        bundle_metric: Metric on S¹ bundle
        shape_metric: Base metric on shape space
        connection: Connection form

    Returns:
        Comparison metrics
    """
    # Extract shape space block from bundle metric
    g_lift_shape = bundle_metric.extract_shape_block()
    g_base = shape_metric.components

    # Difference: should be small if connection is weak
    difference_norm = np.linalg.norm(g_lift_shape - g_base)

    # Connection strength
    connection_strength = connection.magnitude()

    # Ratio of eigenvalues
    eig_lift = np.linalg.eigvalsh(g_lift_shape)
    eig_base = np.linalg.eigvalsh(g_base)
    eigenvalue_ratio = np.mean(eig_lift / eig_base)

    return {
        'shape_block_difference': difference_norm,
        'connection_strength': connection_strength,
        'eigenvalue_ratio': eigenvalue_ratio,
        'connection_coefficients': connection.coefficients
    }
