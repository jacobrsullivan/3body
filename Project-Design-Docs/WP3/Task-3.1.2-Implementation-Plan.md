# Task 3.1.2: Killing PDE Formulation
## WP 3.1 - Deterministic Geometric Search (Killing Fields/Tensors)

**Status**: Planning
**Priority**: Critical Path
**Estimated Duration**: 2-3 days
**Dependencies**: Task 3.1.1 (Lifted JM Metric)

---

## Overview

This task formulates the partial differential equations (PDEs) that characterize Killing vector fields and Killing tensors on the lifted manifolds. Solving these PDEs (Task 3.1.3) will reveal geometric symmetries corresponding to conserved quantities.

### Objectives

1. Derive the Killing vector field equation for linear integrals
2. Derive the Killing tensor equation for quadratic integrals
3. Implement symbolic/numerical formulation of these PDEs
4. Create discretized PDE systems suitable for numerical solution
5. Incorporate physical symmetry priors (permutation, gauge invariance)

### Mathematical Background

#### Killing Vector Fields

A **Killing vector field** $K = K^i \partial_i$ preserves the Riemannian metric $g$:

$$
\mathcal{L}_K g = 0
$$

where $\mathcal{L}_K$ is the Lie derivative.

**Killing Equation** (coordinate form):
$$
\nabla_i K_j + \nabla_j K_i = 0 \quad \text{or} \quad \nabla_{(i} K_{j)} = 0
$$

where $\nabla$ is the Levi-Civita connection and $()$ denotes symmetrization.

**Expanded Form** (using Christoffel symbols):
$$
\frac{\partial K_j}{\partial q^i} + \frac{\partial K_i}{\partial q^j} - 2\Gamma^k_{ij} K_k = 0
$$

**Number of Equations**:
- For $n$-dimensional manifold: $\frac{n(n+1)}{2}$ independent equations
- For unknowns $K_i$: $n$ components
- System is overdetermined for $n > 3$

**For Our Problem**:
- S¹ bundle: $n=4$ → 10 equations, 4 unknowns
- KS manifold: $n=9$ → 45 equations, 9 unknowns

---

#### Killing Tensors

A **Killing tensor** of rank 2 is a symmetric (0,2)-tensor $K_{ij}$ satisfying:

$$
\nabla_{(k} K_{ij)} = 0
$$

**Expanded Form**:
$$
\frac{\partial K_{ij}}{\partial q^k} + \frac{\partial K_{ik}}{\partial q^j} + \frac{\partial K_{jk}}{\partial q^i} - 2\Gamma^{\ell}_{ki} K_{\ell j} - 2\Gamma^{\ell}_{kj} K_{i\ell} - 2\Gamma^{\ell}_{ij} K_{k\ell} = 0
$$

**Number of Equations**:
- For $n$-dimensional manifold: $\frac{n(n+1)(n+2)}{6}$ independent equations
- For unknowns $K_{ij}$ (symmetric): $\frac{n(n+1)}{2}$ components
- Heavily overdetermined

**For Our Problem**:
- S¹ bundle: $n=4$ → 20 equations, 10 unknowns
- KS manifold: $n=9$ → 165 equations, 45 unknowns

---

#### Physical Interpretation

**Why These Equations**:
- Killing vector → Linear integral: $I = K_i \dot{q}^i$ (conserved momentum)
- Killing tensor → Quadratic integral: $I = K_{ij} \dot{q}^i \dot{q}^j$ (conserved "angular momentum squared")

**Examples**:
- Rotational symmetry → Angular momentum (Killing vector)
- Kepler problem in 4D → Runge-Lenz vector (Killing tensor)

---

## Implementation Tasks

### Part A: Christoffel Symbols Computation

#### A1. Symbolic Computation

**Goal**: Compute Christoffel symbols of $g_{JM}$ symbolically for low-dimensional cases.

**Christoffel Symbols**:
$$
\Gamma^k_{ij} = \frac{1}{2} g^{k\ell} \left( \frac{\partial g_{\ell i}}{\partial q^j} + \frac{\partial g_{\ell j}}{\partial q^i} - \frac{\partial g_{ij}}{\partial q^\ell} \right)
$$

**Implementation using SymPy**:

**A1.1**: Create module `src/python/pde/christoffel_symbols.py`

**A1.2**: Implement symbolic Christoffel computation:
```python
import sympy as sp
from typing import List, Tuple

def christoffel_symbols_symbolic(
    g: sp.Matrix,
    coords: List[sp.Symbol]
) -> Tuple[sp.Array, sp.Array, sp.Array]:
    """
    Compute Christoffel symbols symbolically.

    Args:
        g: Metric tensor as SymPy Matrix (n×n)
        coords: List of coordinate symbols

    Returns:
        Gamma: Christoffel symbols (n×n×n array)
        g_inv: Inverse metric (n×n)
        dg: Metric derivatives (n×n×n)
    """
    n = len(coords)
    g_inv = g.inv()

    # Metric derivatives: ∂g_ab/∂q^c
    dg = sp.MutableDenseNDimArray.zeros(n, n, n)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                dg[i, j, k] = sp.diff(g[i, j], coords[k])

    # Christoffel symbols: Γ^k_ij
    Gamma = sp.MutableDenseNDimArray.zeros(n, n, n)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                term = sp.Rational(0)
                for ell in range(n):
                    term += g_inv[k, ell] * (
                        dg[ell, i, j] + dg[ell, j, i] - dg[i, j, ell]
                    )
                Gamma[k, i, j] = sp.simplify(term / 2)

    return Gamma, g_inv, dg
```

**A1.3**: Simplify expressions:
- Use SymPy's `simplify()`, `factor()`, `trigsimp()`
- Apply physical constraints (e.g., equal masses → permutation symmetry)
- Cache results for performance

**Deliverable A1**:
- Symbolic Christoffel computation for S¹ bundle (4D)
- Validation: Sum rule $\Gamma^i_{ij} = \frac{1}{2g} \frac{\partial g}{\partial q^j}$ where $g = \det(g_{ij})$

---

#### A2. Numerical Computation

**Goal**: Compute Christoffel symbols numerically at specific points (for high dimensions).

**Implementation**:

**A2.1**: Numerical derivative of metric:
```python
def christoffel_symbols_numerical(
    g_func: Callable,
    q: np.ndarray,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute Christoffel symbols numerically using finite differences.

    Args:
        g_func: Function returning metric tensor g(q)
        q: Point in configuration space (n,)
        epsilon: Finite difference step

    Returns:
        Gamma: Christoffel symbols (n, n, n)
    """
    n = len(q)

    # Compute metric and inverse
    g = g_func(q)
    g_inv = np.linalg.inv(g)

    # Compute metric derivatives via finite differences
    dg = np.zeros((n, n, n))
    for k in range(n):
        q_plus = q.copy()
        q_minus = q.copy()
        q_plus[k] += epsilon
        q_minus[k] -= epsilon

        g_plus = g_func(q_plus)
        g_minus = g_func(q_minus)

        dg[:, :, k] = (g_plus - g_minus) / (2 * epsilon)

    # Christoffel symbols
    Gamma = np.zeros((n, n, n))
    for k in range(n):
        for i in range(n):
            for j in range(n):
                term = 0.0
                for ell in range(n):
                    term += g_inv[k, ell] * (
                        dg[ell, i, j] + dg[ell, j, i] - dg[i, j, ell]
                    )
                Gamma[k, i, j] = term / 2

    return Gamma
```

**A2.2**: Validation and error estimation:
- Compare with symbolic results (for small systems)
- Richardson extrapolation for accuracy improvement
- Error bounds: $O(\epsilon^2)$ for centered differences

**Deliverable A2**:
- Numerical Christoffel computation for KS manifold (9D)
- Performance: < 1 ms per point (with caching)

---

### Part B: Killing Vector Field Equation

#### B1. Symbolic Formulation

**Goal**: Formulate the Killing equation as a system of linear PDEs.

**Killing Equation**:
$$
\frac{\partial K_j}{\partial q^i} + \frac{\partial K_i}{\partial q^j} = 2\Gamma^k_{ij} K_k
$$

**Matrix Form** (for discretization):

Collect all equations into a single system:
$$
\mathbf{D} \mathbf{K} = \mathbf{C}(\mathbf{K})
$$

where:
- $\mathbf{D}$: Differential operator matrix
- $\mathbf{K}$: Unknown Killing field (as a vector)
- $\mathbf{C}$: Christoffel coupling terms

**Implementation**:

**B1.1**: Create module `src/python/pde/killing_equations.py`

**B1.2**: Implement symbolic Killing PDE:
```python
def killing_vector_pde_symbolic(
    Gamma: sp.Array,
    coords: List[sp.Symbol]
) -> List[sp.Expr]:
    """
    Formulate Killing vector PDE symbolically.

    Args:
        Gamma: Christoffel symbols (n×n×n)
        coords: Coordinate symbols

    Returns:
        equations: List of PDE equations
    """
    n = len(coords)

    # Define Killing vector components as functions
    K = [sp.Function(f'K{i}')(*coords) for i in range(n)]

    equations = []
    for i in range(n):
        for j in range(i, n):  # Symmetric, so only upper triangle
            # ∂K_j/∂q^i + ∂K_i/∂q^j - 2Γ^k_ij K_k = 0
            lhs = sp.diff(K[j], coords[i]) + sp.diff(K[i], coords[j])
            rhs = sum(2 * Gamma[k, i, j] * K[k] for k in range(n))
            equations.append(sp.Eq(lhs, rhs))

    return equations
```

**Deliverable B1**:
- Symbolic Killing PDE for S¹ bundle
- Export to LaTeX for documentation
- Simplification using symmetries

---

#### B2. Discretization

**Goal**: Convert continuous PDE into discrete linear system.

**Approach**: Finite difference on a mesh.

**Mesh**:
- Regular grid in configuration space
- Adaptive refinement near singularities (collisions)

**Discretization Scheme**:
- Derivatives: Central differences $\frac{\partial K_i}{\partial q^j} \approx \frac{K_i(q+\Delta q_j) - K_i(q-\Delta q_j)}{2\Delta q}$
- Unknowns: $K_i$ at each mesh point
- Result: Sparse linear system $\mathbf{A} \mathbf{x} = 0$

**Implementation**:

**B2.1**: Mesh generation:
```python
def generate_mesh(
    bounds: List[Tuple[float, float]],
    resolution: List[int]
) -> np.ndarray:
    """
    Generate regular mesh in configuration space.

    Args:
        bounds: [(q1_min, q1_max), (q2_min, q2_max), ...]
        resolution: [n1, n2, ...] grid points per dimension

    Returns:
        mesh: Grid points (N, n) where N = product(resolution)
    """
    grids = [np.linspace(b[0], b[1], r) for b, r in zip(bounds, resolution)]
    mesh_grids = np.meshgrid(*grids, indexing='ij')
    mesh = np.stack([mg.flatten() for mg in mesh_grids], axis=1)
    return mesh
```

**B2.2**: Build linear system:
```python
def discretize_killing_vector_pde(
    mesh: np.ndarray,
    g_func: Callable,
    Gamma_func: Callable
) -> Tuple[sp.sparse.csr_matrix, np.ndarray]:
    """
    Discretize Killing vector PDE on mesh.

    Args:
        mesh: Grid points (N, n)
        g_func: Metric function
        Gamma_func: Christoffel symbols function

    Returns:
        A: Sparse matrix (M, N*n) where M = number of equations
        b: Right-hand side (M,) - should be zero for homogeneous system
    """
    N, n = mesh.shape
    num_eqs = n * (n + 1) // 2  # Symmetric part of Killing equation

    # Sparse matrix construction
    # Each equation couples K_i at neighboring points
    # ...implementation details...

    return A, b
```

**Deliverable B2**:
- Discretization code for arbitrary mesh
- Sparse matrix representation (scipy.sparse)
- Validation: Recover known Killing fields (sphere → rotations)

---

### Part C: Killing Tensor Equation

#### C1. Symbolic Formulation

**Goal**: Formulate the rank-2 Killing tensor equation.

**Killing Tensor Equation**:
$$
\nabla_k K_{ij} + \nabla_j K_{ik} + \nabla_i K_{jk} = 0
$$

**Expanded**:
$$
\frac{\partial K_{ij}}{\partial q^k} + \frac{\partial K_{ik}}{\partial q^j} + \frac{\partial K_{jk}}{\partial q^i} = \text{Christoffel terms}
$$

**Implementation**:

**C1.1**: Implement symbolic Killing tensor PDE:
```python
def killing_tensor_pde_symbolic(
    Gamma: sp.Array,
    coords: List[sp.Symbol]
) -> List[sp.Expr]:
    """
    Formulate Killing tensor PDE symbolically.

    Returns:
        equations: List of PDE equations (n(n+1)(n+2)/6 equations)
    """
    n = len(coords)

    # Define symmetric tensor K_ij
    K = sp.MutableDenseNDimArray.zeros(n, n)
    for i in range(n):
        for j in range(i, n):
            K[i, j] = K[j, i] = sp.Function(f'K{i}{j}')(*coords)

    equations = []
    for i in range(n):
        for j in range(i, n):
            for k in range(j, n):  # Symmetrize
                # ∇_k K_ij + ∇_j K_ik + ∇_i K_jk = 0
                term1 = sp.diff(K[i, j], coords[k])
                term2 = sp.diff(K[i, k], coords[j])
                term3 = sp.diff(K[j, k], coords[i])

                # Christoffel correction terms
                christoffel_terms = 0  # Detailed implementation

                equations.append(sp.Eq(term1 + term2 + term3, christoffel_terms))

    return equations
```

**Deliverable C1**:
- Symbolic Killing tensor PDE
- Simplification for low-degree polynomials
- Focus: Quadratic tensors (most physical interest)

---

### Part D: Symmetry Priors and Constraints

#### D1. Physical Symmetries

**Goal**: Incorporate known symmetries to reduce search space.

**Permutation Symmetry** (equal masses):
- For $m_1 = m_2 = m_3$, the system has $S_3$ symmetry (permutation group)
- Killing fields must respect this: $K(\sigma(q)) = \sigma_* K(q)$ for $\sigma \in S_3$

**Gauge Invariance** (S¹ bundle):
- Killing fields on the bundle may or may not depend on $\theta$
- Horizontal Killing fields: $K_\theta = 0$ (generate symmetries "downstairs")
- Vertical Killing fields: Only $K_\theta \neq 0$ (generate fiber rotations)

**Implementation**:

**D1.1**: Permutation symmetry enforcement:
```python
def enforce_permutation_symmetry(
    A: sp.sparse.csr_matrix,
    mesh: np.ndarray,
    symmetry_group: str = 'S3'
) -> sp.sparse.csr_matrix:
    """
    Add constraints enforcing permutation symmetry.

    Args:
        A: Original PDE matrix
        mesh: Grid points
        symmetry_group: 'S3' (equal mass) or 'none'

    Returns:
        A_sym: Augmented matrix with symmetry constraints
    """
    # Add equations: K(σ(q)) - σ_*K(q) = 0 for σ in symmetry group
    # ...implementation...
    return A_sym
```

**Deliverable D1**:
- Symmetry enforcement module
- Validation: Reduced number of unknowns (e.g., by factor of 6 for $S_3$)

---

## Validation and Testing

### Test Cases

**T1. Flat Space (Zero Christoffel Symbols)**:
- Killing fields are constant vectors and rotations
- Validate: Recover $n(n+1)/2$ independent Killing fields

**T2. Sphere (S²)**:
- 3 rotational Killing vectors
- Validate: Numerical solver finds these

**T3. Kepler Problem (2D)**:
- Angular momentum (Killing vector)
- Runge-Lenz vector (Killing tensor)
- Validate: Recover both in polar coordinates

---

## Implementation Schedule

### Day 1: Christoffel Symbols
- Implement A1 (symbolic) and A2 (numerical)
- Validate on simple metrics (flat space, sphere)

### Day 2: Killing Vector PDE
- Implement B1 (symbolic formulation)
- Implement B2 (discretization)
- Test on sphere (recover rotations)

### Day 3: Killing Tensor + Symmetries
- Implement C1 (Killing tensor PDE)
- Implement D1 (symmetry priors)
- Integration tests

**Total**: 3 days (or 2 with focus on vector fields only)

---

## Deliverables

- [ ] `src/python/pde/christoffel_symbols.py`
- [ ] `src/python/pde/killing_equations.py`
- [ ] `src/python/pde/mesh_discretization.py`
- [ ] `src/python/pde/symmetry_constraints.py`
- [ ] Test suite with validation cases
- [ ] Technical note: "Killing Equations on Lifted Manifolds" (10 pages)

---

## Success Criteria

- [ ] Symbolic formulation validated on simple cases
- [ ] Discretization produces sparse linear systems
- [ ] Symmetry constraints reduce problem size
- [ ] Ready for numerical solution (Task 3.1.3)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Next Task**: 3.1.3 (Numerical Solution of Killing PDEs)
