"""
Sparse linear system assembly for Killing PDEs (WP 3.1, Task 3.1.3, Part B).

Assembles the discretized system A·K = 0 from:
- Mesh points
- Metric function
- Christoffel symbols
- Finite difference stencils

Output: Sparse CSR matrix A for null space computation.
"""

from dataclasses import dataclass
from typing import Callable, Optional, List, Tuple
import numpy as np
import scipy.sparse as sp

from .mesh_generation import Mesh, S1BundleMesh, KSSpinorMesh
from .christoffel_symbols import compute_christoffel_numerical, ChristoffelSymbolsNumeric


# =============================================================================
# Helper Functions
# =============================================================================

def _symmetric_index(i: int, j: int, n: int) -> int:
    """
    Map symmetric indices (i,j) with i <= j to linear index.

    For n×n symmetric matrix, there are n(n+1)/2 independent components.
    Ordering: (0,0), (0,1), ..., (0,n-1), (1,1), (1,2), ..., (n-1,n-1)
    """
    if i > j:
        i, j = j, i  # Ensure i <= j
    return i * n - i * (i - 1) // 2 + (j - i)


def _get_finite_diff_stencil_1d(
    order: int = 2,
    derivative: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get finite difference stencil coefficients.

    Args:
        order: Accuracy order (2, 4, 6, ...)
        derivative: Which derivative (1 or 2)

    Returns:
        (offsets, coefficients)
        offsets: Array of grid point offsets (e.g., [-1, 0, 1])
        coefficients: Corresponding weights
    """
    if derivative == 1:
        if order == 2:
            # Centered difference: f'(x) ≈ (f(x+h) - f(x-h)) / (2h)
            return np.array([-1, 1]), np.array([-0.5, 0.5])
        elif order == 4:
            # 4th order: f'(x) ≈ (-f(x+2h) + 8f(x+h) - 8f(x-h) + f(x-2h)) / (12h)
            return np.array([-2, -1, 1, 2]), np.array([1/12, -2/3, 2/3, -1/12])
        else:
            raise ValueError(f"Unsupported order {order} for derivative 1")
    elif derivative == 2:
        if order == 2:
            # f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h²
            return np.array([-1, 0, 1]), np.array([1.0, -2.0, 1.0])
        else:
            raise ValueError(f"Unsupported order {order} for derivative 2")
    else:
        raise ValueError(f"Unsupported derivative order {derivative}")


# =============================================================================
# Part B1: Killing Vector System Assembly
# =============================================================================

def assemble_killing_vector_system(
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict,
    *,
    finite_diff_order: int = 2,
    epsilon: float = 1e-6,
    sparse_format: str = 'csr',
    verbose: bool = False
) -> sp.csr_matrix:
    """
    Assemble sparse matrix A for Killing vector equation ∇_(i K_j) = 0.

    The symmetrized covariant derivative is:
        ∇_(i K_j) = (1/2)(∇_i K_j + ∇_j K_i)
                  = (1/2)(∂_i K_j + ∂_j K_i - 2 Γ^k_ij K_k)
                  = 0

    This gives n(n+1)/2 equations (one for each symmetric pair i≤j).

    Discretization:
        ∂_i K_j ≈ (K_j(q + h e_i) - K_j(q - h e_i)) / (2h)

    where h is determined from mesh spacing.

    System structure:
        Unknowns: K = [K_0(q₀), K_1(q₀), ..., K_{n-1}(q₀), K_0(q₁), ...]
                  Total: n × N

        Equations: One n(n+1)/2 block per mesh point
                   Total: n(n+1)/2 × N

        Matrix A: (m_total × n_total) where:
                  m_total = n(n+1)/2 × N (rows)
                  n_total = n × N (columns)

    Args:
        mesh: Mesh on which to discretize
        metric_func: Function g(q, **params) → metric tensor
        metric_params: Parameters for metric function
        finite_diff_order: Order of accuracy (2 or 4)
        epsilon: Finite difference step size
        sparse_format: Output format ('csr', 'coo', 'lil')
        verbose: Print progress

    Returns:
        Sparse matrix A in requested format
    """
    n = mesh.dimension
    N = mesh.num_points

    # Number of equations per point
    m_per_point = n * (n + 1) // 2

    # Total dimensions
    m_total = m_per_point * N  # Equations
    n_total = n * N            # Unknowns

    if verbose:
        print(f"Assembling Killing vector system:")
        print(f"  Mesh: {N} points in {n}D")
        print(f"  System: {m_total} equations, {n_total} unknowns")
        print(f"  Overdetermination factor: {m_total/n_total:.2f}")

    # Build in COO format (easy to construct), convert at end
    rows = []
    cols = []
    data = []

    # Get finite difference stencil
    offsets, coeffs = _get_finite_diff_stencil_1d(order=finite_diff_order, derivative=1)

    # Process each mesh point
    for pt_idx in range(N):
        if verbose and pt_idx % max(1, N // 10) == 0:
            print(f"  Processing point {pt_idx}/{N}")

        q = mesh.points[pt_idx]

        # Compute Christoffel symbols at this point
        christoffel = compute_christoffel_numerical(
            lambda x: metric_func(x, **metric_params),
            q,
            epsilon=epsilon
        )
        Gamma = christoffel.components  # (n, n, n)

        # Get neighbors for finite differences
        neighbors = mesh.neighbor_indices[pt_idx]
        if len(neighbors) < 2 * n:
            # Not enough neighbors for finite differences - skip (boundary point)
            continue

        # Build tree for finding neighbors in specific directions
        neighbor_points = mesh.points[neighbors]

        # For each equation (symmetric pair i, j)
        for i in range(n):
            for j in range(i, n):
                row_idx = pt_idx * m_per_point + _symmetric_index(i, j, n)

                # Equation: ∂_i K_j + ∂_j K_i - 2 Γ^k_ij K_k = 0

                # Term 1: ∂_i K_j (derivative of K_j in direction i)
                # Discretize: find neighbors along dimension i
                for offset, coeff in zip(offsets, coeffs):
                    # Find neighbor at q + offset * h * e_i
                    target_point = q.copy()
                    target_point[i] += offset * epsilon

                    # Find closest mesh point to target
                    distances = np.linalg.norm(neighbor_points - target_point, axis=1)
                    closest_idx = neighbors[np.argmin(distances)]

                    # Add contribution to equation
                    col_idx = closest_idx * n + j  # K_j component at neighbor
                    rows.append(row_idx)
                    cols.append(col_idx)
                    data.append(coeff / epsilon)  # Scaled by h

                # Term 2: ∂_j K_i (derivative of K_i in direction j)
                if i != j:  # Avoid double counting diagonal
                    for offset, coeff in zip(offsets, coeffs):
                        target_point = q.copy()
                        target_point[j] += offset * epsilon

                        distances = np.linalg.norm(neighbor_points - target_point, axis=1)
                        closest_idx = neighbors[np.argmin(distances)]

                        col_idx = closest_idx * n + i  # K_i component at neighbor
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(coeff / epsilon)

                # Term 3: -2 Γ^k_ij K_k (contraction with Christoffel symbols)
                for k in range(n):
                    col_idx = pt_idx * n + k  # K_k at current point
                    rows.append(row_idx)
                    cols.append(col_idx)
                    data.append(-2.0 * Gamma[k, i, j])

    # Convert to sparse matrix
    A_coo = sp.coo_matrix((data, (rows, cols)), shape=(m_total, n_total))

    if sparse_format == 'csr':
        A = A_coo.tocsr()
    elif sparse_format == 'coo':
        A = A_coo
    elif sparse_format == 'lil':
        A = A_coo.tolil()
    else:
        raise ValueError(f"Unknown sparse format: {sparse_format}")

    if verbose:
        print(f"Assembly complete:")
        print(f"  Non-zeros: {A.nnz:,}")
        print(f"  Sparsity: {100 * (1 - A.nnz / (m_total * n_total)):.2f}%")
        print(f"  Memory: {A.data.nbytes / 1024**2:.2f} MB")

    return A


# =============================================================================
# Part B2: Killing Tensor System Assembly
# =============================================================================

def assemble_killing_tensor_system(
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict,
    *,
    enforce_symmetry: bool = True,
    finite_diff_order: int = 2,
    epsilon: float = 1e-6,
    sparse_format: str = 'csr',
    verbose: bool = False
) -> sp.csr_matrix:
    """
    Assemble system for Killing tensor equation ∇_(k K_ij) = 0.

    A Killing tensor K_ij (symmetric, rank-2) satisfies:
        ∇_(k K_ij) = (1/3)(∇_k K_ij + ∇_i K_jk + ∇_j K_ki) = 0

    Unknowns:
        K_ij for i ≤ j: n(n+1)/2 components per point
        Total: n(n+1)/2 × N

    Equations:
        For each triple (i, j, k) with i ≤ j ≤ k: one equation
        Count: n(n+1)(n+2)/6 per point
        Total: n(n+1)(n+2)/6 × N

    Example dimensions:
        n=2: 3 unknowns, 4 equations per point
        n=4: 10 unknowns, 20 equations per point
        n=9: 45 unknowns, 165 equations per point

    WARNING: This is significantly larger than the vector case!

    Args:
        mesh: Mesh on which to discretize
        metric_func: Function g(q, **params) → metric tensor
        metric_params: Parameters for metric function
        enforce_symmetry: Explicitly enforce K_ij = K_ji
        finite_diff_order: Order of accuracy
        epsilon: Finite difference step
        sparse_format: Output format
        verbose: Print progress

    Returns:
        Sparse matrix A for Killing tensor system
    """
    n = mesh.dimension
    N = mesh.num_points

    # Count tensor components (symmetric)
    n_components = n * (n + 1) // 2

    # Count equations (symmetric triple indices)
    m_per_point = n * (n + 1) * (n + 2) // 6

    m_total = m_per_point * N
    n_total = n_components * N

    if verbose:
        print(f"Assembling Killing tensor system:")
        print(f"  Mesh: {N} points in {n}D")
        print(f"  System: {m_total} equations, {n_total} unknowns")
        print(f"  Overdetermination factor: {m_total/n_total:.2f}")
        print(f"  WARNING: Large system! Consider reducing resolution or dimension.")

    # For very large systems (n > 6), warn about memory
    if m_total * n_total > 1e10:  # > 10 billion entries if dense
        print(f"  WARNING: Potential memory issues. Estimated sparse: {m_total * n * 8 / 1024**3:.2f} GB")

    # Build in COO format, convert at end
    rows = []
    cols = []
    data = []

    # Get stencil
    offsets, coeffs = _get_finite_diff_stencil_1d(order=finite_diff_order, derivative=1)

    # Process each mesh point
    for pt_idx in range(N):
        if verbose and pt_idx % max(1, N // 10) == 0:
            print(f"  Processing point {pt_idx}/{N}")

        q = mesh.points[pt_idx]

        # Compute Christoffel symbols
        christoffel = compute_christoffel_numerical(
            lambda x: metric_func(x, **metric_params),
            q,
            epsilon=epsilon
        )
        Gamma = christoffel.components  # (n, n, n)

        neighbors = mesh.neighbor_indices[pt_idx]
        if len(neighbors) < 2 * n:
            # Not enough neighbors for finite differences
            continue

        neighbor_points = mesh.points[neighbors]

        # For each equation (triple i ≤ j ≤ k)
        eq_idx_local = 0
        for i in range(n):
            for j in range(i, n):
                for k in range(j, n):
                    row_idx = pt_idx * m_per_point + eq_idx_local
                    eq_idx_local += 1

                    # Killing tensor equation (symmetrized):
                    # ∇_k K_ij + ∇_i K_jk + ∇_j K_ki = 0
                    #
                    # Expanded:
                    # ∂_k K_ij + ∂_i K_jk + ∂_j K_ki - (Christoffel terms) = 0

                    # Term 1: ∂_k K_ij (derivative of K_ij in direction k)
                    comp_ij = _symmetric_index(i, j, n)
                    for offset, coeff in zip(offsets, coeffs):
                        target_point = q.copy()
                        target_point[k] += offset * epsilon

                        distances = np.linalg.norm(neighbor_points - target_point, axis=1)
                        closest_idx = neighbors[np.argmin(distances)]

                        col_idx = closest_idx * n_components + comp_ij
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(coeff / epsilon)

                    # Term 2: ∂_i K_jk (derivative of K_jk in direction i)
                    comp_jk = _symmetric_index(j, k, n)
                    for offset, coeff in zip(offsets, coeffs):
                        target_point = q.copy()
                        target_point[i] += offset * epsilon

                        distances = np.linalg.norm(neighbor_points - target_point, axis=1)
                        closest_idx = neighbors[np.argmin(distances)]

                        col_idx = closest_idx * n_components + comp_jk
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(coeff / epsilon)

                    # Term 3: ∂_j K_ki (derivative of K_ki in direction j)
                    comp_ki = _symmetric_index(k, i, n)
                    for offset, coeff in zip(offsets, coeffs):
                        target_point = q.copy()
                        target_point[j] += offset * epsilon

                        distances = np.linalg.norm(neighbor_points - target_point, axis=1)
                        closest_idx = neighbors[np.argmin(distances)]

                        col_idx = closest_idx * n_components + comp_ki
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(coeff / epsilon)

                    # Christoffel terms: -Γ^ℓ_ki K_ℓj - Γ^ℓ_kj K_iℓ (for ∇_k K_ij)
                    for ell in range(n):
                        # -Γ^ℓ_ki K_ℓj
                        comp_ellj = _symmetric_index(ell, j, n)
                        col_idx = pt_idx * n_components + comp_ellj
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(-Gamma[ell, k, i])

                        # -Γ^ℓ_kj K_iℓ
                        comp_iell = _symmetric_index(i, ell, n)
                        col_idx = pt_idx * n_components + comp_iell
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(-Gamma[ell, k, j])

                    # Christoffel terms for ∇_i K_jk
                    for ell in range(n):
                        # -Γ^ℓ_ij K_ℓk
                        comp_ellk = _symmetric_index(ell, k, n)
                        col_idx = pt_idx * n_components + comp_ellk
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(-Gamma[ell, i, j])

                        # -Γ^ℓ_ik K_jℓ
                        comp_jell = _symmetric_index(j, ell, n)
                        col_idx = pt_idx * n_components + comp_jell
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(-Gamma[ell, i, k])

                    # Christoffel terms for ∇_j K_ki
                    for ell in range(n):
                        # -Γ^ℓ_jk K_ℓi
                        comp_elli = _symmetric_index(ell, i, n)
                        col_idx = pt_idx * n_components + comp_elli
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(-Gamma[ell, j, k])

                        # -Γ^ℓ_ji K_kℓ
                        comp_kell = _symmetric_index(k, ell, n)
                        col_idx = pt_idx * n_components + comp_kell
                        rows.append(row_idx)
                        cols.append(col_idx)
                        data.append(-Gamma[ell, j, i])

    A_coo = sp.coo_matrix((data, (rows, cols)), shape=(m_total, n_total))

    if sparse_format == 'csr':
        A = A_coo.tocsr()
    elif sparse_format == 'coo':
        A = A_coo
    elif sparse_format == 'lil':
        A = A_coo.tolil()
    else:
        raise ValueError(f"Unknown sparse format: {sparse_format}")

    if verbose:
        print(f"Assembly complete:")
        print(f"  Non-zeros: {A.nnz:,}")
        print(f"  Sparsity: {100 * (1 - A.nnz / (m_total * n_total)):.2f}%")
        print(f"  Memory: {A.data.nbytes / 1024**2:.2f} MB")

    return A


# =============================================================================
# Utility Functions
# =============================================================================

def estimate_assembly_memory(
    mesh: Mesh,
    field_type: str = 'vector'
) -> dict:
    """
    Estimate memory requirements for system assembly.

    Args:
        mesh: Mesh structure
        field_type: 'vector' or 'tensor'

    Returns:
        {
            'equations': int,
            'unknowns': int,
            'nnz_estimate': int,  # Estimated non-zeros
            'memory_mb': float     # Estimated memory in MB
        }
    """
    n = mesh.dimension
    N = mesh.num_points

    if field_type == 'vector':
        m_per_point = n * (n + 1) // 2
        n_components = n
    elif field_type == 'tensor':
        m_per_point = n * (n + 1) * (n + 2) // 6
        n_components = n * (n + 1) // 2
    else:
        raise ValueError(f"Unknown field type: {field_type}")

    m_total = m_per_point * N
    n_total = n_components * N

    # Estimate non-zeros: ~10n entries per row (stencil + Christoffel)
    nnz_per_row = 10 * n
    nnz_estimate = m_total * nnz_per_row

    # Memory: 8 bytes (float64) + 4 bytes (int32) per non-zero
    memory_bytes = nnz_estimate * 12
    memory_mb = memory_bytes / 1024**2

    return {
        'equations': m_total,
        'unknowns': n_total,
        'nnz_estimate': nnz_estimate,
        'memory_mb': memory_mb,
        'overdetermination': m_total / n_total if n_total > 0 else 0
    }


def validate_system_assembly(A: sp.csr_matrix, mesh: Mesh, field_type: str = 'vector') -> dict:
    """
    Validate assembled system for correctness.

    Checks:
    1. Dimensions match expected
    2. Sparsity pattern reasonable
    3. No NaN or Inf entries
    4. Condition number estimate

    Returns:
        Validation report dict
    """
    n = mesh.dimension
    N = mesh.num_points

    if field_type == 'vector':
        m_expected = n * (n + 1) // 2 * N
        n_expected = n * N
    else:
        m_expected = n * (n + 1) * (n + 2) // 6 * N
        n_expected = n * (n + 1) // 2 * N

    # Check dimensions
    dim_ok = (A.shape == (m_expected, n_expected))

    # Check for invalid values
    has_nan = np.any(np.isnan(A.data))
    has_inf = np.any(np.isinf(A.data))

    # Sparsity
    sparsity = 1.0 - A.nnz / (A.shape[0] * A.shape[1])

    # Try to estimate condition number (expensive for large matrices)
    if A.shape[0] < 1000:
        try:
            from scipy.sparse.linalg import svds
            sigma_max = svds(A, k=1, which='LM', return_singular_vectors=False)[0]
            sigma_min = svds(A, k=1, which='SM', return_singular_vectors=False)[0]
            cond_estimate = sigma_max / (sigma_min + 1e-16)
        except:
            cond_estimate = np.nan
    else:
        cond_estimate = np.nan

    return {
        'dimensions_correct': dim_ok,
        'has_nan': has_nan,
        'has_inf': has_inf,
        'sparsity': sparsity,
        'nnz': A.nnz,
        'condition_estimate': cond_estimate,
        'valid': dim_ok and not has_nan and not has_inf
    }
