"""
Regularization techniques for Killing field solutions (WP 3.1, Task 3.1.3, Part D).

When the null space is degenerate (multiple solutions), we apply physical priors
to select the most meaningful solutions:
- Smoothness: Minimize ||∇K||²
- Physical symmetries: Permutation invariance, gauge fixing
- Boundedness: Solutions don't grow unbounded

Methods:
- Smoothness regularization via Laplacian eigenproblemmystery
- Physical prior projection
- Gauge fixing (divergence-free, etc.)
"""

from typing import Optional, List, Tuple
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .mesh_generation import Mesh


# =============================================================================
# Part D1: Smoothness Regularization
# =============================================================================

def apply_smoothness_regularization(
    null_basis: np.ndarray,
    mesh: Mesh,
    *,
    smoothness_penalty: float = 1e-3,
    num_smooth: Optional[int] = None,
    verbose: bool = False
) -> np.ndarray:
    """
    Select smoothest linear combinations of null space vectors.

    Motivation:
        Null space may be degenerate (many solutions, dimension > expected).
        Physical Killing fields should be smooth (low gradient norm).

    Method:
        Among all K in null space, minimize:
            J[K] = ||∇K||²_L2 = ∫ |∇K|² dV

        This becomes an eigenvalue problem for the discrete Laplacian
        restricted to the null space:
            (V^T L V) c = λ c

        where V is the null_basis matrix and L is the mesh Laplacian.

    Args:
        null_basis: (n_total × k) null space basis vectors
        mesh: Mesh structure for computing Laplacian
        smoothness_penalty: Select vectors with eigenvalue < penalty * max(eigenvalue)
        num_smooth: Number of smoothest vectors to return (None = auto-select)
        verbose: Print diagnostic information

    Returns:
        (n_total × k') smoothed basis vectors (k' ≤ k)
    """
    n_total, k = null_basis.shape

    if k == 0:
        if verbose:
            print("Empty null space - nothing to regularize")
        return null_basis

    if verbose:
        print(f"Applying smoothness regularization:")
        print(f"  Null space dimension: {k}")

    # Step 1: Compute discrete Laplacian on mesh
    L = compute_mesh_laplacian(mesh, verbose=verbose)

    # Step 2: Project Laplacian onto null space
    # L_projected = V^T L V  where V = null_basis
    # This is a (k × k) matrix
    if verbose:
        print("  Projecting Laplacian onto null space...")

    L_projected = null_basis.T @ (L @ null_basis)

    # Step 3: Solve eigenproblem for smoothest modes
    if verbose:
        print("  Computing eigenvalues...")

    eigenvalues, eigenvectors = np.linalg.eigh(L_projected)

    # Eigenvalues are non-negative (Laplacian is positive semi-definite)
    # Smallest eigenvalues → smoothest functions

    if verbose:
        print(f"  Eigenvalue range: [{eigenvalues[0]:.2e}, {eigenvalues[-1]:.2e}]")

    # Step 4: Select smoothest vectors
    if num_smooth is None:
        # Auto-select: keep vectors with λ < penalty * λ_max
        threshold = smoothness_penalty * eigenvalues.max()
        smooth_mask = eigenvalues < threshold
        num_smooth = np.sum(smooth_mask)

        if num_smooth == 0:
            # Keep at least one
            num_smooth = 1
            smooth_mask = np.zeros(k, dtype=bool)
            smooth_mask[0] = True

        if verbose:
            print(f"  Auto-selected {num_smooth}/{k} smooth vectors (threshold={threshold:.2e})")
    else:
        num_smooth = min(num_smooth, k)
        smooth_mask = np.arange(k) < num_smooth
        if verbose:
            print(f"  Keeping {num_smooth} smoothest vectors")

    smooth_eigenvectors = eigenvectors[:, smooth_mask]

    # Step 5: Transform back to original space
    # New basis = V @ eigenvectors
    smoothed_basis = null_basis @ smooth_eigenvectors

    if verbose:
        print(f"  Regularized basis dimension: {smoothed_basis.shape[1]}")

    return smoothed_basis


def compute_mesh_laplacian(
    mesh: Mesh,
    *,
    weight_type: str = 'uniform',
    verbose: bool = False
) -> sp.csr_matrix:
    """
    Compute discrete Laplacian operator on mesh.

    The Laplacian measures local smoothness:
        (L·f)_i = sum_j w_ij (f_j - f_i)

    Different weight schemes:
    - 'uniform': w_ij = 1/degree
    - 'distance': w_ij = 1/|x_i - x_j|
    - 'cotangent': w_ij = cot(angle) (for triangulated meshes)

    For vector fields K = (K_0, K_1, ..., K_{n-1}) at N points:
        L acts component-wise on flattened vector (n × N total)

    Args:
        mesh: Mesh structure with connectivity
        weight_type: Type of weighting scheme
        verbose: Print information

    Returns:
        (n_total × n_total) sparse Laplacian matrix
        where n_total = n (dimension) × N (points)
    """
    n = mesh.dimension
    N = mesh.num_points
    n_total = n * N

    if verbose:
        print(f"  Computing mesh Laplacian:")
        print(f"    Mesh: {N} points, {n}D")
        print(f"    Total DOF: {n_total}")
        print(f"    Weight type: {weight_type}")

    # Build Laplacian in COO format
    rows = []
    cols = []
    data = []

    for pt_idx in range(N):
        neighbors = mesh.neighbor_indices[pt_idx]
        degree = len(neighbors)

        if degree == 0:
            # Isolated point - zero Laplacian
            continue

        # Compute weights
        if weight_type == 'uniform':
            weights = np.ones(degree) / degree
        elif weight_type == 'distance':
            distances = np.linalg.norm(
                mesh.points[neighbors] - mesh.points[pt_idx],
                axis=1
            )
            weights = 1.0 / (distances + 1e-10)
            weights /= np.sum(weights)  # Normalize
        else:
            raise ValueError(f"Unknown weight type: {weight_type}")

        # For each field component
        for comp in range(n):
            row_idx = pt_idx * n + comp

            # Diagonal term: -sum(weights)
            rows.append(row_idx)
            cols.append(row_idx)
            data.append(-1.0)  # Since weights sum to 1

            # Off-diagonal terms: weights
            for neighbor, weight in zip(neighbors, weights):
                col_idx = neighbor * n + comp
                rows.append(row_idx)
                cols.append(col_idx)
                data.append(weight)

    L = sp.coo_matrix((data, (rows, cols)), shape=(n_total, n_total))

    if verbose:
        print(f"    Non-zeros: {L.nnz:,}")
        print(f"    Sparsity: {100 * (1 - L.nnz / n_total**2):.2f}%")

    return L.tocsr()


# =============================================================================
# Part D2: Physical Priors
# =============================================================================

def apply_physical_priors(
    null_basis: np.ndarray,
    mesh: Mesh,
    *,
    permutation_symmetry: bool = True,
    gauge_fixing: Optional[str] = 'divergence_free',
    particle_masses: Optional[np.ndarray] = None,
    verbose: bool = False
) -> np.ndarray:
    """
    Apply physical constraints to reduce null space.

    Priors:
    1. Permutation symmetry: Respect particle exchange symmetry
    2. Gauge fixing: Impose ∇·K = 0 (divergence-free) or other gauge
    3. Boundedness: Remove solutions that grow unboundedly
    4. Parity: Respect reflection symmetries

    Args:
        null_basis: (n_total × k) null space basis
        mesh: Mesh structure
        permutation_symmetry: Enforce invariance under particle permutations
        gauge_fixing: Type of gauge ('divergence_free', 'coulomb', or None)
        particle_masses: (3,) masses for permutation symmetry
        verbose: Print information

    Returns:
        (n_total × k') filtered basis
    """
    n = mesh.dimension
    N = mesh.num_points
    k = null_basis.shape[1]

    if verbose:
        print(f"Applying physical priors:")
        print(f"  Initial basis dimension: {k}")

    filtered_basis = null_basis.copy()

    # Prior 1: Gauge fixing
    if gauge_fixing == 'divergence_free':
        if verbose:
            print("  Applying divergence-free gauge...")
        filtered_basis = apply_divergence_free_gauge(
            filtered_basis, mesh, verbose=verbose
        )

    # Prior 2: Permutation symmetry
    if permutation_symmetry and particle_masses is not None:
        if verbose:
            print("  Applying permutation symmetry...")
        # TODO: Implement permutation symmetry projection
        # This requires identifying which coordinates correspond to which particles
        pass

    # Prior 3: Boundedness check
    if verbose:
        print("  Checking boundedness...")
    bounded_mask = check_boundedness(filtered_basis, mesh)
    filtered_basis = filtered_basis[:, bounded_mask]

    if verbose:
        print(f"  Final basis dimension: {filtered_basis.shape[1]}")

    return filtered_basis


def apply_divergence_free_gauge(
    null_basis: np.ndarray,
    mesh: Mesh,
    *,
    tolerance: float = 1e-6,
    verbose: bool = False
) -> np.ndarray:
    """
    Project null space onto divergence-free vector fields.

    Divergence-free condition: ∇·K = ∂_i K^i = 0

    Method:
        1. Compute divergence of each basis vector
        2. Remove components with large divergence
        3. Or project onto div-free subspace (Helmholtz decomposition)

    Args:
        null_basis: (n_total × k) basis vectors
        mesh: Mesh structure
        tolerance: Max |div(K)| allowed
        verbose: Print info

    Returns:
        (n_total × k') divergence-free basis
    """
    n = mesh.dimension
    N = mesh.num_points
    k = null_basis.shape[1]

    # Compute divergence for each basis vector
    divergences = np.zeros((N, k))

    for basis_idx in range(k):
        K = null_basis[:, basis_idx]  # Flattened vector field

        # Reshape to (N, n)
        K_field = K.reshape((N, n))

        # Compute divergence at each mesh point
        for pt_idx in range(N):
            div = 0.0
            neighbors = mesh.neighbor_indices[pt_idx]

            if len(neighbors) < 2 * n:
                # Not enough neighbors for finite differences
                divergences[pt_idx, basis_idx] = 0.0
                continue

            # Finite difference: ∂_i K^i
            for i in range(n):
                # Find neighbors along dimension i
                point = mesh.points[pt_idx]
                neighbor_points = mesh.points[neighbors]

                # Simple forward difference (could be improved)
                for neighbor in neighbors:
                    offset = mesh.points[neighbor] - point
                    if np.abs(offset[i]) > 1e-10:  # Along dimension i
                        dKi_dxi = (K_field[neighbor, i] - K_field[pt_idx, i]) / offset[i]
                        div += dKi_dxi / len(neighbors)  # Crude average
                        break

            divergences[pt_idx, basis_idx] = div

    # Compute L2 norm of divergence for each basis vector
    div_norms = np.sqrt(np.mean(divergences**2, axis=0))

    if verbose:
        print(f"    Divergence norms: {div_norms}")

    # Filter: keep only vectors with small divergence
    div_free_mask = div_norms < tolerance
    div_free_basis = null_basis[:, div_free_mask]

    if verbose:
        print(f"    Kept {div_free_basis.shape[1]}/{k} divergence-free vectors")

    return div_free_basis


def check_boundedness(
    null_basis: np.ndarray,
    mesh: Mesh,
    *,
    growth_threshold: float = 10.0
) -> np.ndarray:
    """
    Check if basis vectors are bounded on the mesh.

    A vector field is unbounded if ||K(x)|| grows rapidly away from origin.

    Method:
        Compute ||K|| at each mesh point.
        If max/min ratio > growth_threshold, reject.

    Args:
        null_basis: (n_total × k) basis
        mesh: Mesh
        growth_threshold: Max ratio of ||K||_max / ||K||_min

    Returns:
        (k,) boolean mask of bounded vectors
    """
    n = mesh.dimension
    N = mesh.num_points
    k = null_basis.shape[1]

    bounded_mask = np.ones(k, dtype=bool)

    for basis_idx in range(k):
        K = null_basis[:, basis_idx].reshape((N, n))

        # Compute norm at each point
        norms = np.linalg.norm(K, axis=1)

        # Check growth
        if np.min(norms) > 1e-10:
            ratio = np.max(norms) / np.min(norms)
            if ratio > growth_threshold:
                bounded_mask[basis_idx] = False

    return bounded_mask


# =============================================================================
# Gauge Transformations
# =============================================================================

def helmholtz_decomposition(
    vector_field: np.ndarray,
    mesh: Mesh
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Helmholtz decomposition: K = K_div_free + ∇φ

    Decomposes vector field into:
    - Divergence-free (solenoidal) component
    - Gradient (irrotational) component

    Method:
        1. Solve Poisson equation: Δφ = ∇·K
        2. Compute ∇φ
        3. K_div_free = K - ∇φ

    Args:
        vector_field: (n_total,) flattened vector field
        mesh: Mesh structure

    Returns:
        (K_div_free, K_gradient) both (n_total,)
    """
    # TODO: Implement Helmholtz decomposition
    # Requires solving Poisson equation on mesh
    raise NotImplementedError("Helmholtz decomposition not yet implemented")


# =============================================================================
# Utility Functions
# =============================================================================

def compute_gradient_norm(
    vector_field: np.ndarray,
    mesh: Mesh
) -> float:
    """
    Compute L² norm of gradient: ||∇K||_L2

    Args:
        vector_field: (n_total,) flattened field
        mesh: Mesh structure

    Returns:
        ||∇K||_L2 scalar
    """
    n = mesh.dimension
    N = mesh.num_points

    K = vector_field.reshape((N, n))

    gradient_norm_sq = 0.0

    for pt_idx in range(N):
        neighbors = mesh.neighbor_indices[pt_idx]

        if len(neighbors) < 2 * n:
            continue

        # Compute gradient at this point (crude estimate)
        grad_K = np.zeros((n, n))  # ∂K_j/∂x_i

        for i in range(n):
            for neighbor in neighbors:
                offset = mesh.points[neighbor] - mesh.points[pt_idx]
                if np.abs(offset[i]) > 1e-10:
                    dK = K[neighbor, :] - K[pt_idx, :]
                    grad_K[i, :] = dK / offset[i]
                    break

        # Add to norm
        gradient_norm_sq += np.sum(grad_K**2) * mesh.volumes[pt_idx]

    return np.sqrt(gradient_norm_sq)
