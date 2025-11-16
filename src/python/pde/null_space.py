"""
Null space computation for overdetermined sparse systems (WP 3.1, Task 3.1.3, Part C).

Solves homogeneous systems A·K = 0 to find Killing fields.

Methods:
- SVD-based (exact for small/medium systems)
- Iterative (for very large systems)
- Randomized SVD (scalable approximation)
"""

from typing import Optional, Tuple, List
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


# =============================================================================
# Part C1: SVD-Based Null Space
# =============================================================================

def compute_null_space_svd(
    A: sp.csr_matrix,
    *,
    tolerance: float = 1e-8,
    max_rank: Optional[int] = None,
    method: str = 'auto',
    verbose: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute null space of A using Singular Value Decomposition.

    For A: (m × n) with m > n (overdetermined):
        A = U Σ V^T

    Null space = span of right singular vectors with σ < tolerance.

    Args:
        A: Sparse or dense matrix (m × n)
        tolerance: Threshold for zero singular values
        max_rank: Maximum number of singular vectors to compute (None = all)
        method: 'auto', 'dense', 'sparse', or 'randomized'
        verbose: Print progress information

    Returns:
        (null_basis, singular_values)
        null_basis: (n × k) orthonormal basis for null space
        singular_values: (n,) all computed singular values (sorted)
    """
    m, n = A.shape

    if verbose:
        print(f"Computing null space via SVD:")
        print(f"  Matrix shape: {m} × {n}")
        print(f"  Overdetermination: {m/n:.2f}")
        print(f"  Method: {method}")

    # Choose method automatically if requested
    if method == 'auto':
        if n < 500:
            method = 'dense'
        elif n < 5000:
            method = 'sparse'
        else:
            method = 'randomized'
        if verbose:
            print(f"  Auto-selected method: {method}")

    # Perform SVD
    if method == 'dense':
        # Convert to dense and use full SVD
        if verbose:
            print("  Converting to dense matrix...")
        A_dense = A.toarray() if sp.issparse(A) else A

        if verbose:
            print("  Computing dense SVD...")
        U, sigma, Vt = np.linalg.svd(A_dense, full_matrices=False)

    elif method == 'sparse':
        # Use sparse SVD (computes largest singular values)
        k = max_rank or min(min(m, n) - 1, 100)

        if verbose:
            print(f"  Computing {k} smallest singular values...")

        try:
            # Try to compute smallest singular values
            U, sigma, Vt = spla.svds(A, k=k, which='SM', maxiter=10000)

            # svds returns unsorted - sort by singular value
            sort_idx = np.argsort(sigma)
            sigma = sigma[sort_idx]
            Vt = Vt[sort_idx, :]

        except spla.ArpackNoConvergence as e:
            if verbose:
                print(f"  ARPACK did not converge. Using partial results.")
            sigma = e.singular_values
            Vt = e.vt
            sort_idx = np.argsort(sigma)
            sigma = sigma[sort_idx]
            Vt = Vt[sort_idx, :]

    elif method == 'randomized':
        # Randomized SVD (fast approximation)
        from sklearn.utils.extmath import randomized_svd

        k = max_rank or min(min(m, n) - 1, 200)

        if verbose:
            print(f"  Computing randomized SVD with k={k}...")

        U, sigma, Vt = randomized_svd(
            A,
            n_components=k,
            n_iter=5,
            random_state=42
        )

    else:
        raise ValueError(f"Unknown method: {method}")

    # Identify null space from small singular values
    null_mask = sigma < tolerance

    if verbose:
        print(f"  Singular values computed: {len(sigma)}")
        print(f"  Null space dimension: {np.sum(null_mask)}")
        print(f"  Smallest σ: {sigma[0]:.2e}")
        if len(sigma) > 1:
            print(f"  Largest σ: {sigma[-1]:.2e}")
        print(f"  Tolerance: {tolerance:.2e}")

    # Extract null space basis
    null_basis = Vt[null_mask, :].T  # Transpose to get column vectors

    if null_basis.shape[1] == 0:
        if verbose:
            print("  WARNING: No null space found (empty)!")
        # Return trivial null space
        null_basis = np.zeros((n, 0))

    return null_basis, sigma


# =============================================================================
# Part C2: Iterative Null Space (for very large systems)
# =============================================================================

def compute_null_space_iterative(
    A: sp.csr_matrix,
    initial_guess: Optional[np.ndarray] = None,
    *,
    max_iterations: int = 1000,
    max_vectors: int = 10,
    tolerance: float = 1e-8,
    verbose: bool = False
) -> Tuple[np.ndarray, List[float]]:
    """
    Iteratively find null space vectors using inverse iteration.

    Algorithm:
    1. Start with random vector v (or initial_guess)
    2. Solve (A^T A + λI) w = v for small λ
    3. Orthogonalize w against previously found null vectors
    4. Check if ||A·w|| < tolerance
    5. If yes, add w to null space basis
    6. Repeat to find multiple vectors

    Advantages:
        - Memory efficient for very large systems
        - Can find null vectors one at a time
        - Good for sparse matrices

    Disadvantages:
        - May miss small null space dimensions
        - Slower than direct SVD for small problems

    Args:
        A: Sparse matrix (m × n)
        initial_guess: (n,) starting vector (random if None)
        max_iterations: Maximum iterations per vector
        max_vectors: Maximum number of null vectors to find
        tolerance: ||A·v|| threshold for accepting null vector
        verbose: Print progress

    Returns:
        (null_basis, residuals)
        null_basis: (n × k) orthonormal null space basis
        residuals: List of ||A·v|| for each basis vector
    """
    m, n = A.shape

    if verbose:
        print(f"Computing null space iteratively:")
        print(f"  Matrix shape: {m} × {n}")
        print(f"  Max vectors: {max_vectors}")

    # Form A^T A (normal equations)
    AtA = A.T @ A  # (n × n) sparse

    # Regularization parameter (small to push towards null space)
    lambda_reg = 1e-10

    # Regularized system: (A^T A + λI)
    I = sp.eye(n, format='csr')
    AtA_reg = AtA + lambda_reg * I

    # Preconditioner (optional, for faster convergence)
    # M = spla.spilu(AtA_reg.tocsc())  # Incomplete LU
    # M_op = spla.LinearOperator((n, n), M.solve)

    # Storage for null space basis
    null_vectors = []
    residuals = []

    for vec_idx in range(max_vectors):
        if verbose:
            print(f"\n  Finding null vector {vec_idx + 1}...")

        # Initialize random vector
        if initial_guess is not None and vec_idx == 0:
            v = initial_guess.copy()
        else:
            v = np.random.randn(n)

        # Orthogonalize against previously found vectors
        for prev_vec in null_vectors:
            v -= np.dot(v, prev_vec) * prev_vec

        # Normalize
        v /= np.linalg.norm(v)

        # Inverse iteration
        for it in range(max_iterations):
            # Solve (A^T A + λI) w = v
            w, info = spla.cg(AtA_reg, v, tol=1e-10, maxiter=1000)

            if info != 0:
                if verbose:
                    print(f"    Iteration {it}: CG did not converge (info={info})")
                break

            # Orthogonalize against null space basis
            for prev_vec in null_vectors:
                w -= np.dot(w, prev_vec) * prev_vec

            # Normalize
            w_norm = np.linalg.norm(w)
            if w_norm < 1e-14:
                if verbose:
                    print(f"    Iteration {it}: Vector collapsed to zero")
                break
            w /= w_norm

            # Check convergence: ||v - w|| → 0
            diff = np.linalg.norm(v - w)
            v = w  # Update for next iteration

            if diff < 1e-12:
                if verbose:
                    print(f"    Converged at iteration {it}")
                break

        # Check if w is in null space
        residual = np.linalg.norm(A @ w)

        if verbose:
            print(f"    Residual ||A·v||: {residual:.2e}")

        if residual < tolerance:
            null_vectors.append(w)
            residuals.append(residual)
            if verbose:
                print(f"    ✓ Accepted (dim = {len(null_vectors)})")
        else:
            if verbose:
                print(f"    ✗ Rejected (residual too large)")
            # No more null vectors found
            break

    # Convert to array
    if len(null_vectors) > 0:
        null_basis = np.column_stack(null_vectors)
    else:
        null_basis = np.zeros((n, 0))

    if verbose:
        print(f"\n  Final null space dimension: {null_basis.shape[1]}")

    return null_basis, residuals


# =============================================================================
# Utility Functions
# =============================================================================

def verify_null_space(
    A: sp.csr_matrix,
    null_basis: np.ndarray,
    *,
    tolerance: float = 1e-6
) -> dict:
    """
    Verify that null_basis spans the null space of A.

    Tests:
    1. ||A·v|| < tolerance for each basis vector v
    2. Basis vectors are orthonormal
    3. Rank check: basis is linearly independent

    Args:
        A: Matrix (m × n)
        null_basis: (n × k) candidate null space basis
        tolerance: Threshold for residuals

    Returns:
        {
            'is_null_space': bool,  # All tests passed
            'residuals': np.ndarray,  # ||A·v|| for each v
            'max_residual': float,
            'orthonormality': float,  # || V^T V - I ||
            'rank': int  # Rank of basis (should equal k)
        }
    """
    n, k = null_basis.shape

    # Test 1: Residuals
    residuals = np.zeros(k)
    for i in range(k):
        v = null_basis[:, i]
        Av = A @ v
        residuals[i] = np.linalg.norm(Av)

    max_residual = np.max(residuals) if k > 0 else 0.0

    # Test 2: Orthonormality
    if k > 0:
        VtV = null_basis.T @ null_basis
        orthonormality_error = np.linalg.norm(VtV - np.eye(k))
    else:
        orthonormality_error = 0.0

    # Test 3: Rank
    if k > 0:
        rank = np.linalg.matrix_rank(null_basis, tol=tolerance)
    else:
        rank = 0

    # Overall validation
    is_null_space = (
        max_residual < tolerance and
        orthonormality_error < tolerance and
        rank == k
    )

    return {
        'is_null_space': is_null_space,
        'residuals': residuals,
        'max_residual': max_residual,
        'orthonormality': orthonormality_error,
        'rank': rank,
        'expected_rank': k
    }


def estimate_null_space_dimension_theoretical(dimension: int, manifold_type: str) -> int:
    """
    Estimate expected null space dimension based on manifold type.

    Args:
        dimension: Manifold dimension n
        manifold_type: 'flat', 'sphere', or 'generic'

    Returns:
        Expected number of Killing vectors
    """
    n = dimension

    if manifold_type == 'flat':
        # Flat ℝⁿ: n translations + n(n-1)/2 rotations
        return n + n * (n - 1) // 2  # = n(n+1)/2

    elif manifold_type == 'sphere':
        # Sphere Sⁿ: rotations in SO(n+1)
        return (n + 1) * n // 2

    elif manifold_type == 'generic':
        # Generic curved manifold: typically no Killing vectors
        return 0

    else:
        raise ValueError(f"Unknown manifold type: {manifold_type}")


def project_onto_null_space(
    vector: np.ndarray,
    null_basis: np.ndarray
) -> np.ndarray:
    """
    Project vector onto null space spanned by null_basis.

    Args:
        vector: (n,) vector to project
        null_basis: (n × k) orthonormal basis

    Returns:
        (n,) projection of vector onto null space
    """
    if null_basis.shape[1] == 0:
        return np.zeros_like(vector)

    # Projection: P·v = V V^T v where V is null_basis
    return null_basis @ (null_basis.T @ vector)


def complement_null_space(
    null_basis: np.ndarray,
    *,
    full_dimension: int
) -> np.ndarray:
    """
    Compute orthonormal basis for complement of null space.

    Args:
        null_basis: (n × k) null space basis
        full_dimension: n

    Returns:
        (n × (n-k)) basis for complement
    """
    n = full_dimension
    k = null_basis.shape[1]

    if k == 0:
        # Null space is empty - complement is full space
        return np.eye(n)

    if k == n:
        # Null space is full - complement is empty
        return np.zeros((n, 0))

    # Use QR decomposition to extend null_basis to full orthonormal basis
    # Start with [null_basis | random_vectors]
    random_vecs = np.random.randn(n, n - k)
    combined = np.column_stack([null_basis, random_vecs])

    # QR decomposition
    Q, R = np.linalg.qr(combined)

    # Q[:, :k] should be close to null_basis
    # Q[:, k:] is complement basis
    complement_basis = Q[:, k:]

    return complement_basis
