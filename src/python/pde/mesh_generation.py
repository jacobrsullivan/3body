"""
Mesh generation for lifted manifolds (WP 3.1, Task 3.1.3, Part A).

This module generates adaptive meshes on:
1. S¹ bundle (Shape Space × S¹) - 4D
2. KS-Spinor manifold - 9D (12D with constraints)

Challenges:
- High dimensionality (4D-9D)
- Singular regions (collisions, forbidden zones)
- Energy shell constraints
- Adaptive refinement near boundaries

Strategy:
- Use quasi-random sequences (Sobol) for uniform coverage
- Adaptive refinement in classically allowed regions
- Exclude collision configurations
- Build neighbor connectivity for finite differences
"""

from dataclasses import dataclass, field
from typing import Optional, List, Callable, Tuple
import numpy as np
from scipy.spatial import cKDTree

try:
    from scipy.stats import qmc
    SCIPY_QMC_AVAILABLE = True
except ImportError:
    SCIPY_QMC_AVAILABLE = False
    qmc = None


# =============================================================================
# Base Mesh Data Structures
# =============================================================================

@dataclass
class Mesh:
    """Base class for meshes on Riemannian manifolds"""
    points: np.ndarray           # (N, n) coordinates on manifold
    volumes: np.ndarray          # (N,) volume elements (from metric determinant)
    neighbor_indices: List[List[int]]  # Connectivity graph
    boundary_mask: np.ndarray    # (N,) boolean - True if on boundary
    dimension: int               # Manifold dimension n

    def __post_init__(self):
        """Validate mesh consistency"""
        N = self.points.shape[0]
        assert self.volumes.shape == (N,), "Volume array shape mismatch"
        assert self.boundary_mask.shape == (N,), "Boundary mask shape mismatch"
        assert len(self.neighbor_indices) == N, "Neighbor list length mismatch"
        assert self.points.shape[1] == self.dimension, "Dimension mismatch"

    @property
    def num_points(self) -> int:
        """Number of mesh points"""
        return self.points.shape[0]

    def find_neighbors(self, point_idx: int, radius: Optional[float] = None) -> np.ndarray:
        """Find neighbors of a given point within radius"""
        if radius is None:
            return np.array(self.neighbor_indices[point_idx])
        # Build KD-tree for radius search
        tree = cKDTree(self.points)
        indices = tree.query_ball_point(self.points[point_idx], radius)
        return np.array(indices)


@dataclass
class S1BundleMesh(Mesh):
    """
    Mesh on S¹ principal bundle (Shape Space × S¹).

    Coordinates: (s₀, s₁, s₂, θ) where:
    - s ∈ ℝ³ are shape space coordinates (e.g., Jacobi coords)
    - θ ∈ [0, 2π) is S¹ fiber coordinate

    Physical interpretation:
    - s describes planar configuration shape
    - θ is overall rotation angle
    """
    shape_coords: np.ndarray     # (N, 3) - shape space part
    fiber_coords: np.ndarray     # (N,) - θ ∈ [0, 2π)
    energy: float                # Total energy E
    angular_momentum: float      # |L| magnitude
    masses: np.ndarray           # (3,) particle masses

    def __post_init__(self):
        """Additional validation for S¹ bundle"""
        super().__post_init__()
        assert self.dimension == 4, "S¹ bundle must be 4D"
        assert self.shape_coords.shape == (self.num_points, 3), "Shape coords shape mismatch"
        assert self.fiber_coords.shape == (self.num_points,), "Fiber coords shape mismatch"
        assert np.all((self.fiber_coords >= 0) & (self.fiber_coords < 2*np.pi)), \
            "Fiber coordinates must be in [0, 2π)"


@dataclass
class KSSpinorMesh(Mesh):
    """
    Mesh on 9D KS-Spinor manifold.

    Coordinates: 12D spinor (u₁₂, u₂₃, u₃₁) each ∈ ℝ⁴
    Constraints: 3 bilinear relations → 9D manifold

    Physical interpretation:
    - Each u_ij regularizes collision of particles i,j
    - Constraint: Triangle closure in spinor space
    """
    spinor_coords: np.ndarray    # (N, 12) - full spinor coordinates
    constraint_residuals: np.ndarray  # (N,) - violation of constraints
    energy: float                # Total energy
    masses: np.ndarray           # (3,) particle masses

    def __post_init__(self):
        """Additional validation for KS-Spinor"""
        super().__post_init__()
        assert self.dimension == 9, "KS-Spinor manifold is 9D after constraints"
        assert self.spinor_coords.shape == (self.num_points, 12), \
            "Spinor coords must be (N, 12)"
        assert self.constraint_residuals.shape == (self.num_points,), \
            "Constraint residuals shape mismatch"


# =============================================================================
# Part A1: S¹ Bundle Mesh Generation
# =============================================================================

def generate_s1_bundle_mesh(
    masses: np.ndarray,
    energy: float,
    L_magnitude: float,
    resolution: dict,
    *,
    exclude_collisions: bool = True,
    epsilon_collision: float = 1e-2,
    neighbor_k: int = 20,
    G: float = 1.0,
    seed: int = 42
) -> S1BundleMesh:
    """
    Generate adaptive mesh on S¹ bundle (Shape Space × S¹).

    Strategy:
    1. Sample shape space using Sobol sequence
    2. Filter by energy constraint (E > V_eff)
    3. Exclude collision regions (r_ij < ε)
    4. Tensor product with uniform θ sampling
    5. Compute volume elements from metric
    6. Build k-nearest-neighbor connectivity

    Args:
        masses: (3,) particle masses
        energy: Total energy E
        L_magnitude: Angular momentum magnitude |L|
        resolution: dict with keys:
            'shape_coarse': Coarse shape space sampling (before filtering)
            'shape_fine': Target shape space points (after filtering)
            'fiber': Number of θ samples
        exclude_collisions: Remove points where any r_ij < epsilon_collision
        epsilon_collision: Collision radius threshold
        neighbor_k: Number of nearest neighbors for connectivity
        G: Gravitational constant
        seed: Random seed for reproducibility

    Returns:
        S1BundleMesh with approximately resolution['shape_fine'] × resolution['fiber'] points
    """
    # Import dependencies
    from .....geometry.lifted_jm_metric import compute_s1_bundle_metric, BundleState
    from .....geometry.shape_space import shapespace_to_positions  # Hypothetical

    # Extract resolution parameters
    N_shape_coarse = resolution.get('shape_coarse', 1000)
    N_shape_target = resolution.get('shape_fine', 100)
    N_fiber = resolution.get('fiber', 16)

    # Step 1: Generate shape space samples using Sobol sequence
    if SCIPY_QMC_AVAILABLE:
        sampler = qmc.Sobol(d=3, scramble=True, seed=seed)
        shape_samples_unit = sampler.random(N_shape_coarse)
    else:
        # Fallback to pseudo-random
        rng = np.random.RandomState(seed)
        shape_samples_unit = rng.rand(N_shape_coarse, 3)

    # Step 2: Map to physical shape space bounds
    # For 3-body: Use scaled Jacobi coordinates or mutual distances
    # Here we use a heuristic bounding box based on energy
    # Rough estimate: r_max ~ G * sum(m_i*m_j) / |E|  (circular orbit estimate)
    if energy < 0:
        r_scale = G * np.sum(masses) / abs(energy)
    else:
        r_scale = 10.0  # Unbound case: arbitrary scale

    # Map [0,1]³ → physical bounds (symmetric around origin)
    shape_samples = (shape_samples_unit - 0.5) * 2 * r_scale  # [-r_scale, r_scale]³

    # Step 3: Filter by energy and collision constraints
    valid_shape_indices = []
    valid_shape_coords = []

    for idx, s in enumerate(shape_samples):
        # Convert shape coords to positions (this is problem-specific)
        # For now, treat s as (x₁, y₁, x₂) with y₂ = 0, x₃ = y₃ = 0, centered CM
        # This is a placeholder - actual conversion depends on coordinate choice

        # Compute effective potential V_eff(s; L)
        # V_eff = V(s) + L²/(2 I(s)) where I is moment of inertia
        # Simplified: just check gravitational potential for feasibility

        # Check collision constraint (simplified - check if points are too close)
        if exclude_collisions:
            # Rough check: pairwise distances in shape space
            min_dist = np.min(np.abs(s))  # Placeholder
            if min_dist < epsilon_collision:
                continue

        # Check energy constraint: E > V_eff (classically allowed)
        # Placeholder: accept a fraction based on simple heuristic
        # In full implementation, compute actual potential
        V_eff_approx = -G * np.sum(masses)**2 / (np.linalg.norm(s) + 1e-6)  # Rough estimate
        if energy < V_eff_approx:
            continue  # Classically forbidden

        valid_shape_indices.append(idx)
        valid_shape_coords.append(s)

    # Downsample if we have too many valid points
    valid_shape_coords = np.array(valid_shape_coords)
    if len(valid_shape_coords) > N_shape_target:
        indices = np.random.choice(len(valid_shape_coords), N_shape_target, replace=False)
        valid_shape_coords = valid_shape_coords[indices]

    N_shape_actual = len(valid_shape_coords)
    if N_shape_actual == 0:
        raise ValueError("No valid shape space points found. Relax energy or collision constraints.")

    # Step 4: Tensor product with fiber coordinate
    theta_samples = np.linspace(0, 2*np.pi, N_fiber, endpoint=False)

    # Create full mesh: (s, θ) pairs
    shape_coords_full = []
    fiber_coords_full = []
    for s in valid_shape_coords:
        for theta in theta_samples:
            shape_coords_full.append(s)
            fiber_coords_full.append(theta)

    shape_coords_full = np.array(shape_coords_full)  # (N, 3)
    fiber_coords_full = np.array(fiber_coords_full)  # (N,)

    # Combine into full 4D coordinates
    points_4d = np.column_stack([shape_coords_full, fiber_coords_full])  # (N, 4)
    N_total = points_4d.shape[0]

    # Step 5: Compute volume elements from metric determinant
    volumes = np.zeros(N_total)
    for i in range(N_total):
        s = shape_coords_full[i]
        theta = fiber_coords_full[i]

        # Compute metric at this point
        # Need to construct BundleState - placeholder for now
        # In full implementation: use actual metric computation
        # g = compute_s1_bundle_metric(...)
        # det_g = np.linalg.det(g.components)
        # volumes[i] = np.sqrt(det_g)

        # Placeholder: uniform volume
        volumes[i] = 1.0

    # Step 6: Build k-nearest-neighbor connectivity
    tree = cKDTree(points_4d)
    neighbor_indices = []
    for i in range(N_total):
        distances, indices = tree.query(points_4d[i], k=neighbor_k+1)
        # Exclude self (first element)
        neighbor_indices.append(indices[1:].tolist())

    # Step 7: Identify boundary points
    # Boundary defined as: on edge of classically allowed region or θ = 0, 2π
    # Simplified: points with fewer than k neighbors
    boundary_mask = np.array([len(neighbors) < neighbor_k for neighbors in neighbor_indices])

    # Create mesh object
    mesh = S1BundleMesh(
        points=points_4d,
        volumes=volumes,
        neighbor_indices=neighbor_indices,
        boundary_mask=boundary_mask,
        dimension=4,
        shape_coords=shape_coords_full,
        fiber_coords=fiber_coords_full,
        energy=energy,
        angular_momentum=L_magnitude,
        masses=masses
    )

    return mesh


# =============================================================================
# Part A2: KS-Spinor Mesh Generation
# =============================================================================

def generate_ks_spinor_mesh(
    masses: np.ndarray,
    energy: float,
    resolution: dict,
    *,
    constraint_tolerance: float = 1e-6,
    neighbor_k: int = 20,
    G: float = 1.0,
    seed: int = 42
) -> KSSpinorMesh:
    """
    Generate mesh on 9D KS-Spinor manifold.

    Challenges:
    1. 12D spinors with 3 bilinear constraints → 9D manifold
    2. Energy shell constraint
    3. Non-compact (must bound region)

    Strategy:
    1. Sample 12D spinor space in bounded region
    2. Project onto constraint surface using Newton-Raphson
    3. Filter by energy shell E ≈ H(u)
    4. Adaptive refinement in transition regions
    5. Build connectivity

    Args:
        masses: (3,) particle masses
        energy: Total energy E
        resolution: dict with keys:
            'spinor_coarse': Initial 12D samples
            'spinor_fine': Target points after projection
        constraint_tolerance: Max residual for constraint satisfaction
        neighbor_k: Nearest neighbors for connectivity
        G: Gravitational constant
        seed: Random seed

    Returns:
        KSSpinorMesh with approximately resolution['spinor_fine'] points
    """
    from ...regularization.levi_civita import levi_civita_transform  # Import actual KS transform

    # Extract resolution
    N_coarse = resolution.get('spinor_coarse', 10000)
    N_target = resolution.get('spinor_fine', 1000)

    # Step 1: Sample 12D spinor space
    if SCIPY_QMC_AVAILABLE:
        sampler = qmc.Sobol(d=12, scramble=True, seed=seed)
        spinor_samples_unit = sampler.random(N_coarse)
    else:
        rng = np.random.RandomState(seed)
        spinor_samples_unit = rng.rand(N_coarse, 12)

    # Map to physical bounds
    # KS spinors for bound orbits: |u_ij| ~ sqrt(r_ij)
    if energy < 0:
        r_scale = G * np.sum(masses) / abs(energy)
        u_scale = np.sqrt(r_scale)
    else:
        u_scale = 5.0

    spinor_samples = (spinor_samples_unit - 0.5) * 2 * u_scale

    # Step 2: Project onto constraint surface
    # Constraints for 3-body KS: bilinear relations between u₁₂, u₂₃, u₃₁
    # This is non-trivial - for now, accept samples as-is with residual check
    # Full implementation would use Newton-Raphson projection

    valid_spinors = []
    constraint_residuals_list = []

    for u in spinor_samples:
        # Check constraints (placeholder - actual constraints are complex)
        # For 3-body KS, constraints relate the three spinor pairs
        # Residual = || C(u) ||  where C are constraint functions

        # Placeholder: just check that spinors aren't too large
        residual = 0.0  # Would compute actual constraint violation

        # Filter by energy (Hamiltonian in KS coordinates)
        # H(u, u') = ... (involves kinetic and transformed potential)
        # For now, accept all

        if residual < constraint_tolerance:
            valid_spinors.append(u)
            constraint_residuals_list.append(residual)

        if len(valid_spinors) >= N_target:
            break

    valid_spinors = np.array(valid_spinors)
    constraint_residuals = np.array(constraint_residuals_list)

    if len(valid_spinors) == 0:
        raise ValueError("No valid KS-Spinor points found. Relax constraints or increase sampling.")

    N_actual = len(valid_spinors)

    # Step 3: Extract 9D coordinates (project from 12D with constraints)
    # For now, use first 9 components as coordinates (placeholder)
    points_9d = valid_spinors[:, :9]

    # Step 4: Compute volume elements (placeholder - would use actual metric)
    volumes = np.ones(N_actual)

    # Step 5: Build connectivity
    tree = cKDTree(points_9d)
    neighbor_indices = []
    for i in range(N_actual):
        distances, indices = tree.query(points_9d[i], k=min(neighbor_k+1, N_actual))
        neighbor_indices.append(indices[1:].tolist())

    # Step 6: Boundary identification
    boundary_mask = np.array([len(neighbors) < neighbor_k for neighbors in neighbor_indices])

    # Create mesh
    mesh = KSSpinorMesh(
        points=points_9d,
        volumes=volumes,
        neighbor_indices=neighbor_indices,
        boundary_mask=boundary_mask,
        dimension=9,
        spinor_coords=valid_spinors,
        constraint_residuals=constraint_residuals,
        energy=energy,
        masses=masses
    )

    return mesh


# =============================================================================
# Utility Functions
# =============================================================================

def compute_mesh_spacing(mesh: Mesh) -> dict:
    """
    Compute characteristic mesh spacing statistics.

    Returns:
        {
            'mean_spacing': float,
            'min_spacing': float,
            'max_spacing': float,
            'spacing_std': float
        }
    """
    spacings = []
    for i, neighbors in enumerate(mesh.neighbor_indices):
        if len(neighbors) > 0:
            distances = np.linalg.norm(
                mesh.points[neighbors] - mesh.points[i],
                axis=1
            )
            spacings.extend(distances.tolist())

    spacings = np.array(spacings)
    return {
        'mean_spacing': np.mean(spacings),
        'min_spacing': np.min(spacings),
        'max_spacing': np.max(spacings),
        'spacing_std': np.std(spacings)
    }


def refine_mesh_region(
    mesh: Mesh,
    region_mask: np.ndarray,
    refinement_factor: int = 2
) -> Mesh:
    """
    Refine mesh in specified region by adding intermediate points.

    Args:
        mesh: Original mesh
        region_mask: (N,) boolean array indicating points to refine around
        refinement_factor: Add this many points between each neighboring pair

    Returns:
        New refined mesh
    """
    # TODO: Implement adaptive refinement
    # Strategy:
    # 1. Identify edges connecting region points
    # 2. Add intermediate points along edges
    # 3. Rebuild connectivity
    # 4. Recompute volumes
    raise NotImplementedError("Mesh refinement not yet implemented")


def visualize_mesh_2d_projection(mesh: Mesh, dims: Tuple[int, int] = (0, 1)) -> None:
    """
    Visualize 2D projection of mesh for debugging.

    Args:
        mesh: Mesh to visualize
        dims: (i, j) - which coordinate dimensions to project onto
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not available for visualization")
        return

    i, j = dims
    plt.figure(figsize=(10, 8))

    # Plot points
    plt.scatter(mesh.points[:, i], mesh.points[:, j],
                c=mesh.volumes, s=20, alpha=0.6, cmap='viridis')
    plt.colorbar(label='Volume element')

    # Highlight boundary
    boundary_points = mesh.points[mesh.boundary_mask]
    if len(boundary_points) > 0:
        plt.scatter(boundary_points[:, i], boundary_points[:, j],
                    c='red', s=50, alpha=0.8, marker='x', label='Boundary')

    plt.xlabel(f'Coordinate {i}')
    plt.ylabel(f'Coordinate {j}')
    plt.title(f'{mesh.dimension}D Mesh Projection onto dims ({i},{j})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
