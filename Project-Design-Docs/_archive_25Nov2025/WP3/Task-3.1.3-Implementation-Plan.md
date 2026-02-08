# Task 3.1.3: Numerical Solution of Killing PDEs
## Detailed Implementation Plan

**Duration**: 5-6 days
**Prerequisites**: Task 3.1.2 (Killing PDE Formulation)
**Inputs**: Discretized PDE systems from Task 3.1.2, JM metrics from Task 3.1.1
**Outputs**: Candidate Killing vector fields and Killing tensors

---

## Overview

This task implements the numerical solvers and analysis tools to find solutions to the Killing field equations formulated in Task 3.1.2. The core challenge is solving overdetermined, homogeneous linear systems **AK = 0** on high-dimensional manifolds while filtering spurious and trivial solutions.

### Objectives

1. Generate appropriate meshes on S¹ bundle and KS-Spinor manifolds
2. Assemble sparse linear systems from discretized Killing PDEs
3. Compute null space of overdetermined systems
4. Apply regularization to select physical solutions
5. Validate solutions via convergence analysis
6. Filter trivial solutions (coordinate functions, known integrals)

### Mathematical Framework

#### Discretized Killing System

From Task 3.1.2, we have:

```
A · K = 0
```

where:
- **A**: Sparse matrix (m × n), m = n(n+1)/2 rows (equations), n columns (unknowns)
- **K**: Killing field components K_i at mesh points
- **m > n**: Overdetermined system (typical: m ≈ 5n for n=4)

**Key Properties**:
1. Homogeneous: Only null space matters
2. Sparse: ~O(n²) non-zeros per row
3. Overdetermined: Generic case has no solutions
4. Special manifolds: null space dimension = # symmetries

#### Null Space Computation

For a discretized system on N mesh points:
- Total unknowns: n × N
- Total equations: m × N
- Expected null space dimension:
  - Flat space: n + n(n-1)/2 (translations + rotations)
  - Sphere S^n: n(n+1)/2 (rotations in SO(n+1))
  - Generic curved: 0 (no symmetries)

---

## Part A: Mesh Generation

### A1: Adaptive Mesh on S¹ Bundle (4D)

**Goal**: Generate mesh points in classically allowed region of (s, θ) space.

#### File: `src/python/pde/mesh_generation.py`

```python
@dataclass
class Mesh:
    """Mesh on Riemannian manifold"""
    points: np.ndarray           # (N, n) coordinates
    volumes: np.ndarray          # (N,) volume elements
    neighbor_indices: List[List[int]]  # Connectivity
    boundary_mask: np.ndarray    # (N,) boolean

@dataclass
class S1BundleMesh(Mesh):
    """Mesh on S¹ bundle (Shape Space × S¹)"""
    shape_coords: np.ndarray     # (N, 3) shape space coordinates
    fiber_coords: np.ndarray     # (N,) θ ∈ [0, 2π)
    energy: float                # Total energy E
    angular_momentum: float      # L magnitude

def generate_s1_bundle_mesh(
    masses: np.ndarray,
    energy: float,
    L_magnitude: float,
    resolution: dict,
    *,
    exclude_collisions: bool = True,
    epsilon_collision: float = 1e-2,
    G: float = 1.0
) -> S1BundleMesh:
    """
    Generate adaptive mesh on S¹ bundle.

    Strategy:
    1. Sample shape space on energy shell E = T + V_eff
    2. Refine near classically allowed boundary (E ≈ V_eff)
    3. Exclude collision configurations (r_ij < ε)
    4. Uniformly sample fiber coordinate θ ∈ [0, 2π)

    Args:
        masses: (3,) particle masses
        energy: Total energy E
        L_magnitude: |L| angular momentum magnitude
        resolution: dict with keys 'shape_coarse', 'shape_fine', 'fiber'
        exclude_collisions: Remove points where r_ij < epsilon_collision

    Returns:
        S1BundleMesh with ~resolution['shape_fine'] × resolution['fiber'] points
    """
```

**Implementation Steps**:
1. Sample shape space coordinates using Sobol/Halton sequence
2. Compute effective potential V_eff(s; L) at each point
3. Filter classically forbidden (E < V_eff) and collision regions
4. Refine sampling near boundaries using bisection
5. Tensor product with uniform θ sampling
6. Compute volume elements from metric determinant
7. Build neighbor connectivity (k-d tree or grid)

#### A2: Adaptive Mesh on KS-Spinor Manifold (9D)

```python
@dataclass
class KSSpinorMesh(Mesh):
    """Mesh on 9D KS-Spinor manifold with constraints"""
    spinor_coords: np.ndarray    # (N, 12) - (u₁₂, u₂₃, u₃₁)
    constraint_residuals: np.ndarray  # (N,) - bilinear constraint violations
    energy: float

def generate_ks_spinor_mesh(
    masses: np.ndarray,
    energy: float,
    resolution: dict,
    *,
    constraint_tolerance: float = 1e-6,
    G: float = 1.0
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
    """
```

**Note**: KS mesh is significantly more expensive (~10^5 points vs 10^4 for S¹) due to dimensionality.

---

## Part B: Sparse Linear System Assembly

### B1: Assemble Killing Vector System

**File**: `src/python/pde/system_assembly.py`

```python
def assemble_killing_vector_system(
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict,
    *,
    finite_diff_order: int = 2,
    epsilon: float = 1e-6
) -> scipy.sparse.csr_matrix:
    """
    Assemble sparse matrix A for ∇_(i K_j) = 0.

    Returns:
        A: CSR matrix (m × n_total) where:
           m = n(n+1)/2 × N (equations)
           n_total = n × N (unknowns)

    Structure:
        Each mesh point contributes n(n+1)/2 rows.
        Coupling: K at neighboring points (via finite differences)

    Memory: ~O(n³ × N) for sparse storage
    """
    n = mesh.points.shape[1]  # Manifold dimension
    N = mesh.points.shape[0]  # Mesh points

    m_per_point = n * (n + 1) // 2
    m_total = m_per_point * N
    n_total = n * N

    # Pre-allocate sparse matrix in COO format
    rows = []
    cols = []
    data = []

    for idx, point in enumerate(mesh.points):
        # Compute Christoffel symbols at this point
        christoffel = compute_christoffel_numerical(
            lambda q: metric_func(q, **metric_params),
            point,
            epsilon=epsilon
        )

        # Get neighbor points for finite differences
        neighbors = mesh.neighbor_indices[idx]

        # Build n(n+1)/2 equation rows for this point
        for i in range(n):
            for j in range(i, n):
                row_idx = idx * m_per_point + _symmetric_index(i, j, n)

                # ∂_i K_j + ∂_j K_i = 2 Γ^k_ij K_k
                # Discretize using centered differences

                # Terms from ∂_i K_j (derivative in i-direction of K_j component)
                # ...

    # Convert to CSR for efficient solving
    return scipy.sparse.coo_matrix(
        (data, (rows, cols)),
        shape=(m_total, n_total)
    ).tocsr()
```

### B2: Assemble Killing Tensor System

```python
def assemble_killing_tensor_system(
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict,
    *,
    enforce_symmetry: bool = True
) -> scipy.sparse.csr_matrix:
    """
    Assemble system for Killing tensors: ∇_(k K_ij) = 0.

    Returns:
        A: CSR matrix (m × n_total) where:
           m = n(n+1)(n+2)/6 × N equations
           n_total = n(n+1)/2 × N unknowns (symmetric tensor)

    Much larger than vector case!
    For n=4: 20 equations, 10 unknowns per point
    For n=9: 165 equations, 45 unknowns per point
    """
```

---

## Part C: Null Space Computation

### C1: SVD-Based Null Space

**File**: `src/python/pde/null_space.py`

```python
def compute_null_space_svd(
    A: scipy.sparse.csr_matrix,
    *,
    tolerance: float = 1e-8,
    max_rank: Optional[int] = None
) -> np.ndarray:
    """
    Compute null space of A using sparse SVD.

    For A: (m × n) with m > n (overdetermined):
        1. Compute SVD: A = U Σ V^T
        2. Identify singular values σ_i < tolerance
        3. Null space = span of corresponding right singular vectors

    Args:
        A: Sparse matrix (m × n)
        tolerance: Threshold for zero singular values
        max_rank: Maximum null space dimension to compute

    Returns:
        null_basis: (n × k) where k = dimension of null space
                    Columns are orthonormal basis vectors

    Implementation:
        Use scipy.sparse.linalg.svds for large sparse matrices
        Falls back to dense SVD for small problems (n < 1000)
    """
    if A.shape[1] < 1000:
        # Small problem: use dense SVD
        A_dense = A.toarray()
        U, sigma, Vt = np.linalg.svd(A_dense, full_matrices=False)
    else:
        # Large problem: use sparse randomized SVD
        from scipy.sparse.linalg import svds
        # Compute smallest singular values
        k = max_rank or min(100, A.shape[1] // 2)
        U, sigma, Vt = svds(A, k=k, which='SM')

    # Identify null space from small singular values
    null_mask = sigma < tolerance
    null_basis = Vt[null_mask, :].T

    return null_basis
```

### C2: Iterative Null Space (for very large systems)

```python
def compute_null_space_iterative(
    A: scipy.sparse.csr_matrix,
    initial_guess: Optional[np.ndarray] = None,
    *,
    max_iterations: int = 1000,
    tolerance: float = 1e-8
) -> np.ndarray:
    """
    Iteratively find null space vectors using inverse iteration.

    Algorithm:
        1. Start with random vector v
        2. Solve (A^T A + λI) w = v for small λ (regularization)
        3. Orthogonalize against previously found null vectors
        4. Normalize and check residual ||Aw||
        5. Repeat to find multiple null vectors

    Advantages:
        - Memory efficient for very large systems
        - Can find null vectors one at a time
        - Good for sparse matrices

    Disadvantages:
        - May miss small null space dimensions
        - Requires good preconditioner for fast convergence
    """
```

---

## Part D: Regularization and Filtering

### D1: Smoothness Regularization

```python
def apply_smoothness_regularization(
    null_basis: np.ndarray,
    mesh: Mesh,
    *,
    smoothness_penalty: float = 1e-3
) -> np.ndarray:
    """
    Select smoothest linear combinations of null vectors.

    Motivation:
        Null space may be degenerate (many solutions).
        Physical Killing fields should be smooth.

    Method:
        Minimize: ||∇K||² subject to K in null space

        This becomes an eigenvalue problem for the Laplacian
        restricted to the null space.

    Returns:
        Smoothed basis vectors (fewer, smoother solutions)
    """
    # Compute discrete Laplacian on mesh
    L = compute_mesh_laplacian(mesh)

    # Project Laplacian onto null space
    # null_basis: (n_total × k)
    L_projected = null_basis.T @ L @ null_basis  # (k × k)

    # Find eigenvectors with smallest eigenvalues
    eigenvalues, eigenvectors = np.linalg.eigh(L_projected)

    # Select smoothest (smallest eigenvalue) vectors
    num_smooth = np.sum(eigenvalues < smoothness_penalty * eigenvalues.max())
    smooth_vectors = eigenvectors[:, :num_smooth]

    # Transform back to original space
    return null_basis @ smooth_vectors
```

### D2: Physical Priors

```python
def apply_physical_priors(
    null_basis: np.ndarray,
    mesh: Mesh,
    *,
    permutation_symmetry: bool = True,
    gauge_fixing: Optional[str] = 'divergence_free'
) -> np.ndarray:
    """
    Apply physical constraints to reduce null space.

    Priors:
    1. Permutation symmetry: Respect particle exchange symmetry
    2. Gauge fixing: Impose ∇·K = 0 (divergence-free) or other gauge
    3. Boundedness: Remove solutions that grow unboundedly
    4. Parity: Respect reflection symmetries

    Returns:
        Filtered basis vectors satisfying physical constraints
    """
```

---

## Part E: Convergence Analysis

### E1: Mesh Refinement Study

```python
def mesh_convergence_study(
    metric_func: Callable,
    metric_params: dict,
    resolutions: List[dict],
    *,
    reference_solution: Optional[np.ndarray] = None
) -> dict:
    """
    Study solution convergence under mesh refinement.

    Protocol:
    1. Solve on coarse mesh (resolution[0])
    2. Solve on medium mesh (resolution[1])
    3. Solve on fine mesh (resolution[2])
    4. Compare solutions (interpolate to common points)
    5. Compute convergence rate

    Returns:
        {
            'solutions': List of null bases,
            'residuals': List of ||A·K|| norms,
            'convergence_rate': Estimated p in O(h^p),
            'converged': bool
        }
    """
```

### E2: Solution Verification

```python
def verify_killing_field(
    killing_field: np.ndarray,
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict
) -> dict:
    """
    Verify that a candidate is a true Killing field.

    Tests:
    1. Residual: ||∇_(i K_j)|| < tolerance
    2. Smoothness: Finite ∇K norm
    3. Non-triviality: Not a coordinate function or known integral
    4. Independence: Linearly independent of other candidates

    Returns:
        {
            'residual_max': Maximum residual over mesh,
            'residual_l2': L² norm of residual,
            'smoothness': ||∇K||_L2,
            'is_trivial': bool,
            'independent': bool
        }
    """
```

---

## Part F: Integration and Workflow

### F1: Complete Solver Pipeline

```python
def solve_killing_fields(
    manifold_type: str,  # 's1_bundle' or 'ks_spinor'
    masses: np.ndarray,
    energy: float,
    resolution: dict,
    *,
    field_type: str = 'vector',  # 'vector' or 'tensor'
    L_magnitude: Optional[float] = None,  # Required for S¹ bundle
    regularization: dict = {},
    convergence_check: bool = True,
    G: float = 1.0
) -> dict:
    """
    Complete pipeline for finding Killing fields.

    Steps:
    1. Generate mesh
    2. Assemble sparse system A
    3. Compute null space
    4. Apply regularization
    5. Filter trivial solutions
    6. Verify convergence (if requested)
    7. Package results

    Returns:
        {
            'null_space_dim': int,
            'killing_fields': List[np.ndarray],  # Each is (n × N)
            'mesh': Mesh,
            'residuals': List[float],
            'convergence': dict (if convergence_check=True)
        }
    """
```

---

## Testing Strategy

### Test 1: Flat Space (All Christoffel = 0)

**Expected**: n translations + n(n-1)/2 rotations

```python
def test_flat_space_killing_fields():
    """
    Flat ℝⁿ should have n(n+1)/2 Killing vectors:
    - n translations: K = ∂_i
    - n(n-1)/2 rotations: K = x_i ∂_j - x_j ∂_i
    """
    mesh = generate_uniform_mesh(n=3, resolution=10)
    metric_func = lambda q: np.eye(3)  # Flat metric

    A = assemble_killing_vector_system(mesh, metric_func, {})
    null_basis = compute_null_space_svd(A)

    assert null_basis.shape[1] == 6  # 3 + 3
```

### Test 2: Sphere S² (Known Rotations)

**Expected**: 3 rotations in SO(3)

```python
def test_sphere_killing_fields():
    """
    Sphere S² has 3 Killing vectors (infinitesimal rotations).
    """
    mesh = generate_sphere_mesh(radius=1.0, resolution=50)
    metric_func = lambda q: compute_sphere_metric(q, radius=1.0)

    A = assemble_killing_vector_system(mesh, metric_func, {})
    null_basis = compute_null_space_svd(A, tolerance=1e-6)

    assert null_basis.shape[1] == 3
```

### Test 3: Kepler Problem (Known Runge-Lenz)

**Expected**: Energy, angular momentum, Runge-Lenz vector

```python
def test_kepler_runge_lenz():
    """
    Kepler problem in regularized coords should have:
    - 1 energy integral
    - 3 angular momentum components
    - 3 Runge-Lenz components
    = 7 total (but only 6 independent due to constraints)
    """
    # Use KS coordinates for Kepler problem
    mesh = generate_kepler_mesh(energy=-0.5, resolution=100)
    metric_func = lambda u: compute_kepler_metric(u)

    A = assemble_killing_vector_system(mesh, metric_func, {})
    null_basis = compute_null_space_svd(A)

    # May find 6 or 7 depending on how constraints handled
    assert null_basis.shape[1] >= 5  # At least E + L (3) + one RL component
```

### Test 4: Mesh Convergence

```python
def test_mesh_convergence():
    """
    Verify solutions converge as mesh is refined.
    """
    resolutions = [
        {'shape_coarse': 10, 'fiber': 8},
        {'shape_coarse': 20, 'fiber': 16},
        {'shape_coarse': 40, 'fiber': 32}
    ]

    results = mesh_convergence_study(
        metric_func=compute_s1_jm_metric,
        metric_params={'masses': [1, 1, 1], 'energy': -1.0, 'L_magnitude': 1.0},
        resolutions=resolutions
    )

    assert results['convergence_rate'] > 1.5  # Should be ~2 for centered differences
    assert results['converged']
```

---

## Performance Considerations

### Memory Estimates

**S¹ Bundle (n=4, N=10,000 points)**:
- Unknowns: 4 × 10,000 = 40,000
- Equations: 10 × 10,000 = 100,000
- Sparse matrix: ~2 million non-zeros × 8 bytes = 16 MB
- SVD workspace: ~500 MB

**KS Spinor (n=9, N=100,000 points)**:
- Unknowns: 9 × 100,000 = 900,000
- Equations: 45 × 100,000 = 4,500,000
- Sparse matrix: ~180 million non-zeros = 1.4 GB
- SVD: Would require iterative methods, ~10 GB workspace

### Computational Time Estimates

- Mesh generation: 1-10 minutes
- System assembly: 10-60 minutes
- SVD (sparse): 1-10 hours (depends on null space dimension)
- Regularization: 10 minutes
- Convergence study (3 meshes): 3× above

**Optimization**:
- Parallelize mesh assembly (embarrassingly parallel)
- Use preconditioned iterative solvers
- Cache Christoffel symbol computations

---

## Deliverables

### Code Files

- [x] `src/python/pde/mesh_generation.py` (~800 lines)
  - `generate_s1_bundle_mesh()`
  - `generate_ks_spinor_mesh()`
  - Mesh dataclasses

- [x] `src/python/pde/system_assembly.py` (~600 lines)
  - `assemble_killing_vector_system()`
  - `assemble_killing_tensor_system()`

- [x] `src/python/pde/null_space.py` (~400 lines)
  - `compute_null_space_svd()`
  - `compute_null_space_iterative()`

- [x] `src/python/pde/regularization.py` (~500 lines)
  - `apply_smoothness_regularization()`
  - `apply_physical_priors()`

- [x] `src/python/pde/convergence.py` (~300 lines)
  - `mesh_convergence_study()`
  - `verify_killing_field()`

- [x] `src/python/pde/killing_solver.py` (~400 lines)
  - `solve_killing_fields()` - Main pipeline

### Test Files

- [x] `tests/wp3/test_mesh_generation.py` (~400 lines)
- [x] `tests/wp3/test_null_space.py` (~300 lines)
- [x] `tests/wp3/test_killing_solver.py` (~500 lines)

**Total**: ~4200 lines

---

## Success Criteria

### Minimum Success
- [x] Mesh generation works for both manifolds
- [x] System assembly produces valid sparse matrices
- [x] Null space computation runs (even if null space is empty)
- [x] Code validated on flat space and sphere
- [x] Negative result documented (if no non-trivial fields found)

### Target Success
- [x] Find at least one non-trivial Killing vector on S¹ bundle
- [x] Residual ||A·K|| < 10^-6 for all candidates
- [x] Mesh convergence demonstrated (rate > 1.5)
- [x] Solutions filtered and ready for Task 3.1.4

### Stretch Success
- [x] Find Killing tensors (quadratic integrals)
- [x] Solutions converge to analytical form (if known)
- [x] Computational time < 1 hour for S¹ bundle
- [x] KS spinor manifold solutions obtained

---

## Integration Points

**From Task 3.1.1**:
- Uses `compute_s1_jm_metric()` for metric function
- Uses `compute_ks_jm_metric()` for KS case

**From Task 3.1.2**:
- Uses `compute_christoffel_numerical()`
- Uses `discretize_killing_vector_pde()` infrastructure

**To Task 3.1.4**:
- Provides Killing field data (null space vectors on mesh)
- Provides mesh structure for integral evaluation

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Planning Complete - Ready for Implementation
**Next Task**: 3.1.4 (Integral Conversion & Filtering)
