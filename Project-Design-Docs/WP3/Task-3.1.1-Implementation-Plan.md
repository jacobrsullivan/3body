# Task 3.1.1: Lifted Jacobi-Maupertuis Metric Implementation
## WP 3.1 - Deterministic Geometric Search (Killing Fields/Tensors)

**Status**: Planning
**Priority**: Critical Path (Required for all WP 3.1 tasks)
**Estimated Duration**: 3-4 days
**Dependencies**: WP 2.1.3 (JM Metric), WP 2.2/2.3 (Lift Constructions)

---

## Overview

This task implements the Jacobi-Maupertuis (JM) metric on the lifted configuration spaces constructed in WP2. The JM metric transforms the dynamics of the three-body problem into geodesic motion, allowing us to search for symmetries (Killing fields/tensors) that correspond to conserved quantities.

### Objectives

1. Implement JM metric on the S¹ principal bundle (WP 2.2)
2. Implement JM metric on the KS-Spinor constrained manifold (WP 2.3)
3. Compute metric tensor components with high precision
4. Validate against limiting cases (Kepler problem, equal masses)
5. Prepare infrastructure for Killing equation formulation (Task 3.1.2)

### Mathematical Background

#### Jacobi-Maupertuis Principle

The **Jacobi-Maupertuis metric** converts a Hamiltonian dynamical system into a Riemannian geodesic problem.

For a Hamiltonian system with fixed energy $E$:
$$
H(q, p) = \frac{1}{2} g^{ij}(q) p_i p_j + V(q) = E
$$

The **JM metric** on the configuration manifold is:
$$
g_{JM}(q) = 2(E - V(q)) \cdot g(q)
$$

where $g(q)$ is the kinetic energy metric (mass-weighted).

**Key Property**: Trajectories with energy $E$ are geodesics of $g_{JM}$ (with parameter = action, not time).

**Why This Matters**: Conserved quantities correspond to **geometric symmetries** of $g_{JM}$ (Killing structures).

---

#### JM Metric on the S¹ Bundle

**Configuration Space**: $\widetilde{Q} = S \times S^1$ (4D)
- $S$: 3D shape space (planar 3BP reduced configuration)
- $S^1$: Fiber coordinate $\theta \in [0, 2\pi)$

**Lifted Hamiltonian** (from WP 2.2):
$$
\widetilde{H}(s, \theta, p_s, p_\theta) = H_{\text{red}}(s, p_s) + \text{(potential terms)}
$$

**JM Metric**:
$$
g_{JM}^{(S^1)}(s, \theta) = 2(E - V(s)) \cdot g_{\text{lift}}(s, \theta)
$$

where:
- $g_{\text{lift}}$ is the metric on the bundle (induced from shape space + fiber)
- $V(s)$ is the effective potential in shape space coordinates

**Dimension**: 4×4 metric tensor (3 shape + 1 fiber coordinate)

---

#### JM Metric on the KS-Spinor Manifold

**Configuration Space**: $\widetilde{Q} = \{\mathbf{u} \in \mathbb{R}^{12} : \text{constraints}\}$ (9D constrained)
- 12D: Three 4D spinors $\mathbf{u}_{12}, \mathbf{u}_{23}, \mathbf{u}_{31}$
- 3 constraints: Triangle closure in spinor variables

**Lifted Hamiltonian** (from WP 2.3):
$$
\widetilde{H}_{KS}(\mathbf{u}, \mathbf{p}_u) = \frac{1}{2} M^{ij}(\mathbf{u}) p_{u,i} p_{u,j} + V(\mathbf{u})
$$

**JM Metric**:
$$
g_{JM}^{(KS)}(\mathbf{u}) = 2(E - V(\mathbf{u})) \cdot M(\mathbf{u})
$$

where $M(\mathbf{u})$ is the mass matrix in spinor coordinates (from KS transformation).

**Dimension**: 9×9 metric tensor (on the constrained 9D manifold)

**Challenge**: Must respect constraints (metric is degenerate in $\mathbb{R}^{12}$, non-degenerate on constraint surface).

---

## Implementation Tasks

### Part A: S¹ Bundle JM Metric

#### A1. Bundle Coordinate System

**Goal**: Define coordinate charts and transformations for the S¹ bundle.

**Coordinates**:
- Shape space coordinates: $(s_1, s_2, s_3)$ (e.g., relative distances or normalized positions)
- Fiber coordinate: $\theta \in [0, 2\pi)$ (orientation angle)

**Implementation Steps**:

**A1.1**: Create module `src/python/geometry/lifted_jm_metric.py`

**A1.2**: Implement S¹ bundle coordinate class:
```python
@dataclass
class S1BundleCoords:
    """Coordinates on S¹ principal bundle over shape space."""
    s: np.ndarray  # Shape (3,) - base space coords
    theta: float   # Fiber coordinate

    def to_array(self) -> np.ndarray:
        """Return as flat array [s1, s2, s3, θ]."""
        return np.append(self.s, self.theta)
```

**A1.3**: Implement coordinate transformations:
- Shape space → S¹ bundle: Trivial (just append $\theta$)
- S¹ bundle → Cartesian: Requires fixing orientation (using $\theta$) + reconstruction

**Deliverable A1**:
- S¹ bundle coordinate representation
- Validation: Round-trip transformations (error < 1e-14)

---

#### A2. Base Space Metric (Shape Space)

**Goal**: Compute the mass-weighted metric on shape space $g_{\text{shape}}(s)$.

**Mathematical Definition**:

For shape space parameterized by relative distances $(r_{12}, r_{23}, r_{31})$:
$$
g_{\text{shape}} = \sum_{i=1}^3 m_i \, dr_i \otimes dr_i \big|_{\text{reduced}}
$$

This is the induced metric from the quotient by $\mathbb{R}^3 \times SO(3)$.

**Practical Computation**:

Use Jacobian of the projection map:
$$
g_{\text{shape}}^{ij} = J^T G_{\text{cart}} J
$$

where:
- $G_{\text{cart}} = \text{diag}(m_1, m_1, m_1, m_2, m_2, m_2, m_3, m_3, m_3)$ (mass matrix)
- $J = \frac{\partial \text{Cartesian}}{\partial s}$ (Jacobian of reconstruction map)

**Implementation Steps**:

**A2.1**: Implement shape space metric evaluator:
```python
def shape_space_metric(s: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """
    Compute 3×3 metric tensor on shape space.

    Args:
        s: Shape coordinates (3,)
        masses: Body masses (3,)

    Returns:
        g_shape: Metric tensor (3, 3)
    """
    # Compute Jacobian numerically or analytically
    J = compute_shape_to_cartesian_jacobian(s, masses)
    G_cart = np.diag(np.repeat(masses, 3))  # Mass matrix
    g_shape = J.T @ G_cart @ J
    return g_shape
```

**A2.2**: Handle singularities:
- Near collisions: $r_{ij} \to 0$ → metric blows up
- Collinear configurations: Rank degeneracy
- Mitigation: Regularization parameter $\epsilon$, or switch to KS coordinates

**A2.3**: Validation:
- Kepler limit ($m_3 \to 0$): Reduce to 2-body metric
- Equal masses: Verify symmetry under permutations
- Positive definiteness: All eigenvalues > 0 (away from collisions)

**Deliverable A2**:
- `shape_space_metric(s, masses)` function
- Test suite with limiting cases
- Performance: < 10 μs per evaluation

---

#### A3. Fiber Metric Contribution

**Goal**: Compute the metric contribution from the S¹ fiber.

**Mathematical Definition**:

The S¹ fiber is parameterized by $\theta$. The fiber metric is:
$$
g_{\text{fiber}} = d\theta \otimes d\theta
$$

But this is coupled to the base via the **mechanical connection** $A$ (from WP 2.1.2):
$$
g_{\text{lift}} = g_{\text{shape}} + (d\theta - A)^2
$$

where $A = A_i(s) ds^i$ is the connection one-form.

**Full Bundle Metric**:
$$
g_{\text{lift}} = \begin{pmatrix}
g_{\text{shape}} & -A \\
-A^T & 1
\end{pmatrix}
$$

**Implementation Steps**:

**A3.1**: Retrieve connection form from WP 2.1.2:
```python
def connection_form(s: np.ndarray, L: float, masses: np.ndarray) -> np.ndarray:
    """
    Mechanical connection one-form A_i(s).

    Args:
        s: Shape coordinates (3,)
        L: Angular momentum magnitude
        masses: Body masses (3,)

    Returns:
        A: Connection components (3,) in shape space basis
    """
    # From WP 2.1.2 implementation
    I_locked = locked_inertia_tensor(s, masses)
    # A_i = (I^-1 L)_i (simplified formula)
    return np.linalg.solve(I_locked, np.full(3, L))
```

**A3.2**: Implement lifted metric on S¹ bundle:
```python
def s1_bundle_metric(s: np.ndarray, masses: np.ndarray, L: float) -> np.ndarray:
    """
    Compute 4×4 metric tensor on S¹ bundle.

    Args:
        s: Shape coordinates (3,)
        masses: Body masses (3,)
        L: Angular momentum

    Returns:
        g_lift: Lifted metric tensor (4, 4)
    """
    g_shape = shape_space_metric(s, masses)  # 3×3
    A = connection_form(s, L, masses)        # (3,)

    # Construct block matrix
    g_lift = np.zeros((4, 4))
    g_lift[:3, :3] = g_shape
    g_lift[:3, 3] = -A
    g_lift[3, :3] = -A
    g_lift[3, 3] = 1.0
    return g_lift
```

**Deliverable A3**:
- `s1_bundle_metric(s, masses, L)` function
- Validation: Metric is symmetric and positive-definite
- Test: Connection vanishes for axisymmetric configurations

---

#### A4. S¹ Bundle JM Metric

**Goal**: Combine kinetic metric with potential to form JM metric.

**Mathematical Definition**:
$$
g_{JM}^{(S^1)}(s, \theta) = 2(E - V_{\text{eff}}(s)) \cdot g_{\text{lift}}(s)
$$

where:
- $E$: Total energy (fixed)
- $V_{\text{eff}}(s)$: Effective potential in shape space (gravitational + centrifugal)

**Effective Potential**:
$$
V_{\text{eff}}(s) = V_{\text{grav}}(s) + \frac{L^2}{2 I(s)}
$$

where $I(s)$ is the moment of inertia.

**Implementation Steps**:

**A4.1**: Implement effective potential:
```python
def effective_potential(s: np.ndarray, L: float, masses: np.ndarray, G: float = 1.0) -> float:
    """
    Effective potential in shape space.

    Args:
        s: Shape coordinates (3,)
        L: Angular momentum magnitude
        masses: Body masses (3,)
        G: Gravitational constant

    Returns:
        V_eff: Effective potential
    """
    # Gravitational potential
    r12, r23, r31 = s  # Assuming s = (r12, r23, r31)
    V_grav = -G * (masses[0]*masses[1]/r12 +
                   masses[1]*masses[2]/r23 +
                   masses[2]*masses[0]/r31)

    # Centrifugal term
    I = moment_of_inertia(s, masses)
    V_centrifugal = L**2 / (2*I)

    return V_grav + V_centrifugal
```

**A4.2**: Implement JM metric on S¹ bundle:
```python
def s1_jm_metric(s: np.ndarray, theta: float, E: float, L: float, masses: np.ndarray) -> np.ndarray:
    """
    Jacobi-Maupertuis metric on S¹ bundle.

    Args:
        s: Shape coordinates (3,)
        theta: Fiber coordinate
        E: Total energy
        L: Angular momentum magnitude
        masses: Body masses (3,)

    Returns:
        g_JM: JM metric tensor (4, 4)
    """
    V_eff = effective_potential(s, L, masses)
    prefactor = 2 * (E - V_eff)

    if prefactor <= 0:
        raise ValueError(f"Energy E={E} < V_eff={V_eff} at s={s}")

    g_lift = s1_bundle_metric(s, masses, L)
    g_JM = prefactor * g_lift
    return g_JM
```

**Deliverable A4**:
- `s1_jm_metric(s, theta, E, L, masses)` function
- Validation: Geodesics of $g_{JM}$ match trajectories (at least for simple cases)
- Error handling for classically forbidden regions ($E < V_{\text{eff}}$)

---

### Part B: KS-Spinor Manifold JM Metric

#### B1. KS Coordinate System

**Goal**: Represent the constrained 9D KS-Spinor manifold.

**Coordinates**: Three 4D spinors $\mathbf{u}_{12}, \mathbf{u}_{23}, \mathbf{u}_{31} \in \mathbb{R}^4$

**Constraints** (3 equations):
$$
\mathbf{r}_{12} + \mathbf{r}_{23} + \mathbf{r}_{31} = 0
$$

where $\mathbf{r}_{ij} = L(\mathbf{u}_{ij}) \mathbf{u}_{ij}$ (Levi-Civita matrix).

**Representation Options**:
1. **Extrinsic**: Work in $\mathbb{R}^{12}$ and project onto constraint surface
2. **Intrinsic**: Parameterize the 9D manifold directly (eliminate 3 DOF)

**Implementation Steps**:

**B1.1**: Define KS coordinate class:
```python
@dataclass
class KSSpinorCoords:
    """Coordinates on KS-Spinor constrained manifold."""
    u12: np.ndarray  # Shape (4,) - Spinor for pair 1-2
    u23: np.ndarray  # Shape (4,) - Spinor for pair 2-3
    u31: np.ndarray  # Shape (4,) - Spinor for pair 3-1

    def to_array(self) -> np.ndarray:
        """Return as flat array (12,)."""
        return np.concatenate([self.u12, self.u23, self.u31])

    def check_constraints(self, tol: float = 1e-12) -> bool:
        """Verify triangle closure constraint."""
        r12 = levi_civita_map(self.u12)
        r23 = levi_civita_map(self.u23)
        r31 = levi_civita_map(self.u31)
        residual = np.linalg.norm(r12 + r23 + r31)
        return residual < tol
```

**B1.2**: Implement Levi-Civita transformation:
```python
def levi_civita_map(u: np.ndarray) -> np.ndarray:
    """
    KS transformation: u ∈ R⁴ → r ∈ R³.

    Bilinear relation: r = L(u) u
    where L(u) is the 3×4 Levi-Civita matrix.
    """
    u0, u1, u2, u3 = u
    L = np.array([
        [u0, -u1, -u2, -u3],
        [u1,  u0, -u3,  u2],
        [u2,  u3,  u0, -u1]
    ])
    r = L @ u
    return r
```

**Deliverable B1**:
- KS spinor coordinate representation
- Constraint validation function
- Levi-Civita transformation (forward and adjoint)

---

#### B2. KS Mass Matrix

**Goal**: Compute the kinetic energy metric in KS spinor coordinates.

**Mathematical Definition**:

The kinetic energy in Cartesian coordinates is:
$$
T = \frac{1}{2} \sum_i m_i |\dot{\mathbf{r}}_i|^2
$$

After KS transformation ($\mathbf{r}_{ij} = L(\mathbf{u}_{ij}) \mathbf{u}_{ij}$), the metric becomes:
$$
M^{ij}(\mathbf{u}) = \frac{\partial \mathbf{r}}{\partial u^i} \cdot G_{\text{mass}} \cdot \frac{\partial \mathbf{r}}{\partial u^j}
$$

**Dimension**: 12×12 matrix (or 9×9 after constraint projection)

**Implementation Steps**:

**B2.1**: Compute Jacobian of KS transformation:
```python
def ks_jacobian(u: np.ndarray) -> np.ndarray:
    """
    Jacobian of Levi-Civita map: ∂r/∂u (3×4 matrix).

    For r = L(u) u, we have:
    ∂r/∂u = L(u) + (∂L/∂u) u
    """
    # Analytical expression (derived symbolically)
    # Returns 3×4 matrix
    pass  # Implementation details
```

**B2.2**: Implement KS mass matrix (extrinsic, 12×12):
```python
def ks_mass_matrix_extrinsic(u12: np.ndarray, u23: np.ndarray, u31: np.ndarray,
                              masses: np.ndarray) -> np.ndarray:
    """
    Mass matrix in KS spinor coordinates (12×12, before constraint).

    Args:
        u12, u23, u31: Spinor coordinates (4,) each
        masses: Body masses (3,)

    Returns:
        M: Mass matrix (12, 12)
    """
    M = np.zeros((12, 12))

    # Each pair contributes a 4×4 block
    # (Derived from transformation of kinetic energy)
    # Placeholder - requires detailed derivation

    return M
```

**B2.3**: Project onto constraint surface (9×9):
```python
def ks_mass_matrix_intrinsic(u12: np.ndarray, u23: np.ndarray, u31: np.ndarray,
                               masses: np.ndarray) -> np.ndarray:
    """
    Mass matrix on 9D constraint surface.

    Uses constraint Jacobian to project.
    """
    M_ext = ks_mass_matrix_extrinsic(u12, u23, u31, masses)  # 12×12

    # Compute constraint Jacobian: ∂C/∂u (3×12)
    C_jac = constraint_jacobian(u12, u23, u31)

    # Null space of constraint: Z (12×9)
    Z = null_space(C_jac)  # Columns span tangent to constraint surface

    # Projected mass matrix: M_int = Z^T M_ext Z (9×9)
    M_int = Z.T @ M_ext @ Z
    return M_int
```

**Deliverable B2**:
- `ks_mass_matrix_extrinsic(u, masses)` function
- `ks_mass_matrix_intrinsic(u, masses)` function
- Validation: Positive-definite (eigenvalues > 0)
- Test: Two-body limit recovers standard KS result

---

#### B3. KS Potential and JM Metric

**Goal**: Implement the JM metric on the KS-Spinor manifold.

**Potential in KS Coordinates**:

Gravitational potential depends on distances:
$$
V(\mathbf{u}) = -G \sum_{i<j} \frac{m_i m_j}{r_{ij}(\mathbf{u})}
$$

where $r_{ij} = |\mathbf{r}_{ij}| = |\mathbf{u}_{ij}|^2$ (bilinear relation).

**JM Metric**:
$$
g_{JM}^{(KS)}(\mathbf{u}) = 2(E - V(\mathbf{u})) \cdot M(\mathbf{u})
$$

**Implementation Steps**:

**B3.1**: Implement KS potential:
```python
def ks_potential(u12: np.ndarray, u23: np.ndarray, u31: np.ndarray,
                 masses: np.ndarray, G: float = 1.0) -> float:
    """
    Gravitational potential in KS coordinates.

    Uses bilinear relation: r_ij = |u_ij|^2.
    """
    r12 = np.linalg.norm(u12)**2
    r23 = np.linalg.norm(u23)**2
    r31 = np.linalg.norm(u31)**2

    V = -G * (masses[0]*masses[1]/np.sqrt(r12) +
              masses[1]*masses[2]/np.sqrt(r23) +
              masses[2]*masses[0]/np.sqrt(r31))
    return V
```

**B3.2**: Implement KS JM metric:
```python
def ks_jm_metric(u12: np.ndarray, u23: np.ndarray, u31: np.ndarray,
                 E: float, masses: np.ndarray, intrinsic: bool = True) -> np.ndarray:
    """
    Jacobi-Maupertuis metric on KS-Spinor manifold.

    Args:
        u12, u23, u31: Spinor coordinates
        E: Total energy
        masses: Body masses
        intrinsic: If True, return 9×9 (constraint surface); else 12×12

    Returns:
        g_JM: JM metric tensor
    """
    V = ks_potential(u12, u23, u31, masses)
    prefactor = 2 * (E - V)

    if prefactor <= 0:
        raise ValueError(f"Energy E={E} < V={V}")

    if intrinsic:
        M = ks_mass_matrix_intrinsic(u12, u23, u31, masses)
    else:
        M = ks_mass_matrix_extrinsic(u12, u23, u31, masses)

    g_JM = prefactor * M
    return g_JM
```

**Deliverable B3**:
- `ks_potential(u, masses)` function
- `ks_jm_metric(u, E, masses)` function
- Validation: Kepler limit (two spinors, third body at infinity)
- Performance: < 100 μs per evaluation

---

## Validation and Testing

### Test Suite Structure

**Unit Tests**:
- `tests/test_s1_bundle_metric.py` - S¹ bundle metric components
- `tests/test_ks_mass_matrix.py` - KS mass matrix construction
- `tests/test_jm_metrics.py` - JM metrics on both lifts

**Integration Tests**:
- `tests/integration/test_geodesics.py` - Geodesic equation matches dynamics

---

### Validation Cases

#### V1. Kepler Problem (Two-Body Limit)

**Setup**: Set $m_3 \to 0$ and place third body far away.

**Expected Results**:
- S¹ bundle metric reduces to 2D shape space + fiber
- KS metric reduces to standard 4D KS metric for Kepler problem
- JM metric geodesics are Kepler ellipses

**Test**:
```python
def test_kepler_limit():
    masses = np.array([1.0, 1.0, 1e-10])
    # Set up initial conditions for Kepler orbit
    # Compute JM metric
    # Integrate geodesic equation
    # Compare with analytical Kepler solution
    assert error < 1e-6
```

---

#### V2. Equal Mass Symmetry

**Setup**: $m_1 = m_2 = m_3 = m$.

**Expected Results**:
- Metric is symmetric under body permutations
- Lagrange equilateral configuration is a critical point

**Test**:
```python
def test_equal_mass_symmetry():
    masses = np.array([1.0, 1.0, 1.0])
    # Permute bodies: 1↔2, 2↔3
    # Verify metric components are invariant
    g1 = s1_jm_metric(s, theta, E, L, masses)
    s_permuted = permute_shape_coords(s, [1, 0, 2])
    g2 = s1_jm_metric(s_permuted, theta, E, L, masses)
    assert np.allclose(g1, g2)
```

---

#### V3. Geodesic Equation

**Setup**: Integrate geodesic equation of $g_{JM}$ and compare with Hamiltonian flow.

**Geodesic Equation**:
$$
\frac{d^2 q^i}{d\lambda^2} + \Gamma^i_{jk} \frac{dq^j}{d\lambda} \frac{dq^k}{d\lambda} = 0
$$

where $\Gamma^i_{jk}$ are Christoffel symbols of $g_{JM}$.

**Test**:
```python
def test_geodesic_matches_dynamics():
    # Initial conditions (position + velocity)
    q0 = np.array([...])
    v0 = np.array([...])

    # Integrate geodesic equation
    geodesic_traj = integrate_geodesic(g_JM, q0, v0, t_span)

    # Integrate Hamiltonian dynamics (from WP2)
    hamiltonian_traj = integrate_hamiltonian(H, q0, v0, t_span)

    # Should agree up to reparameterization (time vs. action)
    error = compute_trajectory_distance(geodesic_traj, hamiltonian_traj)
    assert error < 1e-6
```

---

#### V4. Positive Definiteness

**Setup**: Sample random points in configuration space.

**Expected Result**: All eigenvalues of $g_{JM}$ are positive (in classically allowed regions).

**Test**:
```python
def test_positive_definiteness():
    masses = np.random.rand(3) + 0.5
    E = -0.5  # Bound orbit energy
    L = 1.0

    # Sample 1000 random shape space points
    for _ in range(1000):
        s = sample_random_shape_space_point()
        V_eff = effective_potential(s, L, masses)

        if E > V_eff:  # Classically allowed
            g_JM = s1_jm_metric(s, 0.0, E, L, masses)
            eigenvalues = np.linalg.eigvalsh(g_JM)
            assert np.all(eigenvalues > 0)
```

---

## Performance Requirements

**Target Performance** (single evaluation):
- S¹ bundle metric: < 50 μs
- KS mass matrix (extrinsic): < 100 μs
- KS mass matrix (intrinsic, with projection): < 500 μs
- JM metric (both cases): < 100 μs additional overhead

**Batch Evaluation** (1000 points):
- Vectorized operations using NumPy/JAX
- Target: < 10 ms total for S¹, < 50 ms for KS

---

## Implementation Schedule

### Phase 1: S¹ Bundle Metric (2 days)
- **Day 1**: Implement parts A1-A3 (coordinate system, shape space metric, fiber coupling)
- **Day 2**: Implement part A4 (JM metric), validation tests V1-V2

### Phase 2: KS-Spinor Metric (2 days)
- **Day 3**: Implement parts B1-B2 (KS coordinates, mass matrix)
- **Day 4**: Implement part B3 (JM metric), validation tests V3-V4

**Total**: 4 days (can be compressed to 3 with parallel development)

---

## Deliverables

### Code Modules
- [ ] `src/python/geometry/lifted_jm_metric.py` - Main implementation
- [ ] `src/python/geometry/s1_bundle.py` - S¹ bundle utilities
- [ ] `src/python/geometry/ks_spinor.py` - KS spinor utilities

### Validation
- [ ] Test suite (>90% coverage)
- [ ] Validation report with numerical results
- [ ] Performance benchmarks

### Documentation
- [ ] API documentation (Sphinx-compatible docstrings)
- [ ] Technical note: "JM Metrics on Lifted Manifolds" (5-10 pages)
- [ ] Tutorial notebook demonstrating metric computation

---

## Success Criteria

**Functional**:
- [ ] Both S¹ and KS JM metrics implemented and tested
- [ ] Limiting cases (Kepler, equal mass) validated
- [ ] Geodesic equation matches Hamiltonian dynamics

**Performance**:
- [ ] Evaluation times meet targets (< 100 μs)
- [ ] Vectorized batch processing available

**Quality**:
- [ ] Test coverage > 90%
- [ ] Documentation complete

**Scientific**:
- [ ] Positive definiteness verified in classically allowed regions
- [ ] Symmetries respected (permutation, gauge invariance)

---

## Dependencies and Handoffs

### Inputs (from WP2)
- WP 2.1.3: Shape space JM metric implementation
- WP 2.1.2: Mechanical connection form $A(s)$
- WP 2.2: S¹ bundle construction
- WP 2.3: KS-Spinor transformation and constraints

### Outputs (to WP 3.1.2+)
- JM metric evaluators: `s1_jm_metric()`, `ks_jm_metric()`
- Christoffel symbol computation (derived from metric)
- Infrastructure for Killing PDE formulation

---

## References

1. **Jacobi-Maupertuis Principle**:
   - Pettini, M. *Geometry and Topology in Hamiltonian Dynamics* (2007), Chapter 2
   - Casetti et al., "Geometric approach to Hamiltonian dynamics" (2000)

2. **S¹ Bundles and Reduction**:
   - Montgomery, "The connection whose holonomy is the classical adiabatic angles" (1988)
   - Marsden & Ratiu, *Introduction to Mechanics and Symmetry* (1999)

3. **KS Regularization**:
   - Stiefel & Scheifele, *Linear and Regular Celestial Mechanics* (1971)
   - Waldvogel, "Quaternions and the perturbed Kepler problem" (2006)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Ready for Implementation
**Next Task**: 3.1.2 (Killing PDE Formulation)
