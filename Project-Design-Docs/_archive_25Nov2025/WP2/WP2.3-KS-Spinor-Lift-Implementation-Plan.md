# WP 2.3: Kustaanheimo-Stiefel (KS) Spinor "Pairwise" Lift
## Work Package 2 - Geometric Reduction and Shape Space Analysis

**Status**: Design Phase
**Priority**: Critical Path for Lift-Integrability Hypothesis (Extended)
**Estimated Duration**: 12-15 days
**Dependencies**: WP2.2 Complete or In-Progress (S¹ Lift), Task 2.1.1 (Coordinates)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Implementation Architecture](#implementation-architecture)
4. [Part A: KS Transformation for Single Pair](#part-a-ks-transformation-for-single-pair)
5. [Part B: Pairwise Application to 3BP](#part-b-pairwise-application-to-3bp)
6. [Part C: Constrained Hamiltonian Dynamics](#part-c-constrained-hamiltonian-dynamics)
7. [Part D: Integrability Analysis](#part-d-integrability-analysis)
8. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
9. [Implementation Schedule](#implementation-schedule)
10. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

WP 2.3 implements the **Kustaanheimo-Stiefel (KS) spinor lift**—a more sophisticated dimensional increase that regularizes collisions and potentially reveals hidden integrability through spinor algebra. Unlike the minimal S¹ lift (WP2.2), the KS lift is motivated by:

1. **Collision Regularization**: KS transform makes collisions (singularities) regular
2. **Spinor Structure**: Connection to SU(2) representation theory
3. **Higher Dimensionality**: More room for hidden symmetries (12D vs. 4D in S¹ case)
4. **Historical Success**: KS regularization solved the perturbed Kepler problem

**The "Pairwise" Strategy**: Apply KS transformation to all three pairwise relative coordinates:
- $(r_{12}, \dot{r}_{12}) \to (u_{12}, \dot{u}_{12})$ where $u_{12} \in \mathbb{R}^4$
- $(r_{23}, \dot{r}_{23}) \to (u_{23}, \dot{u}_{23})$ where $u_{23} \in \mathbb{R}^4$
- $(r_{31}, \dot{r}_{31}) \to (u_{31}, \dot{u}_{31})$ where $u_{31} \in \mathbb{R}^4$

**Result**: 3D configuration space → 12D spinor space, constrained to effective 9D.

### Objectives

1. **KS Transform Implementation**: Single-pair transformation with bilinear relation
2. **Pairwise Extension**: Apply to all three body pairs simultaneously
3. **Constraint Manifold**: Implement Bilinear constraints ($|u|^2 = r$, orthogonality)
4. **Regularized Dynamics**: Integrate on constraint manifold (collision-free)
5. **Integrability Search**: Look for hidden integrals in spinor coordinates
6. **Comparison**: Contrast with S¹ lift—does higher dimension help?

### Deliverables

- **Deliverable 2.3.1**: KS transformation library (forward and inverse)
- **Deliverable 2.3.2**: Pairwise spinor coordinate system for 3BP
- **Deliverable 2.3.3**: Constrained Hamiltonian integrator (RATTLE/SHAKE)
- **Deliverable 2.3.4**: Collision regularization validation (integrate through collisions)
- **Deliverable 2.3.5**: Integrability analysis report (compare to WP2.2 results)
- **Deliverable 2.3.6**: Technical report: "KS Spinor Geometry of the 3BP"

---

## Mathematical Background

### The Kustaanheimo-Stiefel (KS) Transformation

For a **single** two-body problem, the KS transformation embeds 3D space into 4D:

#### Definition

**Position Space**: A 3D vector $\mathbf{r} = (x, y, z)$ with $r = |\mathbf{r}|$ is represented by a 4D spinor:

$$
\mathbf{u} = (u_0, u_1, u_2, u_3) \in \mathbb{R}^4
$$

related by the **bilinear map**:

$$
\mathbf{r} = L(\mathbf{u}) \mathbf{u}
$$

where $L(\mathbf{u})$ is the **Levi-Civita matrix**:

$$
L(\mathbf{u}) = \begin{pmatrix}
u_0 & -u_1 & -u_2 & -u_3 \\
u_1 & u_0 & -u_3 & u_2 \\
u_2 & u_3 & u_0 & -u_1
\end{pmatrix}
$$

**Key Property**:
$$
|\mathbf{r}|^2 = |\mathbf{u}|^4 \quad \Rightarrow \quad r = |\mathbf{u}|^2
$$

This is the **bilinear constraint** relating 4D spinor to 3D position.

#### Velocity Space

Velocities transform similarly:

$$
\dot{\mathbf{r}} = 2 L(\mathbf{u}) \dot{\mathbf{u}}
$$

#### Time Regularization

To regularize collisions ($r \to 0$), introduce **fictitious time** $s$:

$$
\frac{dt}{ds} = r = |\mathbf{u}|^2
$$

**Effect**: As $r \to 0$ (collision), real time $t$ slows down relative to fictitious time $s$. The trajectory becomes regular in $(s, \mathbf{u})$ coordinates even through collisions.

### Extension to Three-Body Problem

For three bodies, we have three pairwise distances:
- $\mathbf{r}_{12} = \mathbf{r}_1 - \mathbf{r}_2$, $r_{12} = |\mathbf{r}_{12}|$
- $\mathbf{r}_{23} = \mathbf{r}_2 - \mathbf{r}_3$, $r_{23} = |\mathbf{r}_{23}|$
- $\mathbf{r}_{31} = \mathbf{r}_3 - \mathbf{r}_1$, $r_{31} = |\mathbf{r}_{31}|$

**Pairwise KS Strategy**: Apply KS to each pair:

$$
\begin{aligned}
\mathbf{r}_{12} &= L(\mathbf{u}_{12}) \mathbf{u}_{12}, \quad r_{12} = |\mathbf{u}_{12}|^2 \\
\mathbf{r}_{23} &= L(\mathbf{u}_{23}) \mathbf{u}_{23}, \quad r_{23} = |\mathbf{u}_{23}|^2 \\
\mathbf{r}_{31} &= L(\mathbf{u}_{31}) \mathbf{u}_{31}, \quad r_{31} = |\mathbf{u}_{31}|^2
\end{aligned}
$$

**Dimensional Count**:
- Original: 3 vectors in 3D = 9 DOF
- Spinor: 3 vectors in 4D = 12 DOF
- Constraints: 3 bilinear relations + 1 closure ($\mathbf{r}_{12} + \mathbf{r}_{23} + \mathbf{r}_{31} = 0$)
- Net: 12 - 3 = 9 DOF (same as original, but regularized)

### The Constraint Manifold

The spinor coordinates are not independent. They must satisfy:

1. **Bilinear Constraints** (3 equations):
   $$
   |\mathbf{u}_{ij}|^2 = r_{ij} \quad \text{for } ij \in \{12, 23, 31\}
   $$

2. **Closure Constraint** (1 vector equation = 3 scalar equations):
   $$
   L(\mathbf{u}_{12})\mathbf{u}_{12} + L(\mathbf{u}_{23})\mathbf{u}_{23} + L(\mathbf{u}_{31})\mathbf{u}_{31} = \mathbf{0}
   $$

3. **Orthogonality** (velocities must be tangent to constraint manifold)

**Total**: 6 constraints reduce 12D to effective 6D configuration space (phase space: 12D).

### Regularized Hamiltonian

In fictitious time $s$, the Hamiltonian becomes:

$$
\mathcal{K}(\mathbf{u}, \mathbf{u}') = \frac{1}{2} \sum_{ij} \frac{|\mathbf{u}'_{ij}|^2}{|\mathbf{u}_{ij}|^2} - V_{\text{reg}}(\mathbf{u})
$$

where $\mathbf{u}' = d\mathbf{u}/ds$ and $V_{\text{reg}}$ is the regularized potential.

**Key Property**: $\mathcal{K}$ has **no singularities** at collisions ($|\mathbf{u}| = 0$ is regular).

---

## Implementation Architecture

### Module Structure

```
src/python/regularization/
├── __init__.py                    # Package exports
├── ks_transform.py                # A: Single-pair KS transformation
├── levi_civita.py                 # A: Levi-Civita matrix operations
├── spinor_algebra.py              # A: Quaternion/spinor operations
└── inverse_transform.py           # A: Spinor → Cartesian

src/python/lifts/
├── ks_pairwise.py                 # B: Pairwise KS for 3BP
├── spinor_coordinates.py          # B: (u12, u23, u31) system
└── constraint_manifold.py         # B: Bilinear + closure constraints

src/python/integration/
├── constrained_integrator.py      # C: RATTLE/SHAKE on constraints
├── fictitious_time.py             # C: dt/ds = r regularization
└── collision_detector.py          # C: Monitor near-collisions

src/python/analysis/
├── ks_integrability.py            # D: Search integrals in spinor coords
├── spinor_symmetries.py           # D: SU(2) structure analysis
└── comparison_s1_vs_ks.py         # D: Compare lift strategies

tests/regularization/
├── test_ks_transform.py           # Unit tests
├── test_bilinear_relation.py      # Validate |u|² = r
├── test_collision_passage.py      # Integrate through collision
└── test_spinor_algebra.py         # Algebraic consistency
```

### Data Structures

```python
@dataclass(frozen=True)
class SpinorVector:
    """
    4D spinor representing a 3D vector via KS transform.

    Attributes:
        components: (u₀, u₁, u₂, u₃) ∈ ℝ⁴
    """
    components: np.ndarray  # Shape (4,)

    def __post_init__(self):
        assert self.components.shape == (4,), "Spinor must be 4D"

    @property
    def u0(self) -> float:
        return self.components[0]

    @property
    def u1(self) -> float:
        return self.components[1]

    @property
    def u2(self) -> float:
        return self.components[2]

    @property
    def u3(self) -> float:
        return self.components[3]

    @property
    def norm_squared(self) -> float:
        """‖u‖² = u₀² + u₁² + u₂² + u₃²"""
        return np.dot(self.components, self.components)

    @property
    def radius(self) -> float:
        """r = ‖u‖² (bilinear relation)"""
        return self.norm_squared


@dataclass(frozen=True)
class KSState:
    """
    State in KS coordinates for a single pair.

    Represents (r, v) ∈ ℝ³ × ℝ³ as (u, u') ∈ ℝ⁴ × ℝ⁴.
    """
    u: SpinorVector  # Position spinor
    u_prime: SpinorVector  # Velocity spinor (du/ds)
    fictitious_time: float  # s (regularized time)

    def to_cartesian(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert to Cartesian (r, v).

        Returns:
            (position, velocity) each ∈ ℝ³
        """
        # Apply bilinear map
        r = levi_civita_map(self.u, self.u)
        v = 2 * levi_civita_map(self.u, self.u_prime)

        return r, v


@dataclass(frozen=True)
class PairwiseSpinorState:
    """
    Spinor coordinates for all three pairs in 3BP.

    Configuration space: ℝ¹² (constrained to 9D manifold)
    Phase space: ℝ²⁴ (constrained to 18D manifold)
    """
    u12: SpinorVector  # Spinor for r₁₂
    u23: SpinorVector  # Spinor for r₂₃
    u31: SpinorVector  # Spinor for r₃₁

    u12_prime: SpinorVector  # Velocity du₁₂/ds
    u23_prime: SpinorVector  # Velocity du₂₃/ds
    u31_prime: SpinorVector  # Velocity du₃₁/ds

    fictitious_time: float  # s

    @property
    def dimension(self) -> int:
        """Phase space dimension: 2 × 12 = 24 (before constraints)"""
        return 24

    @property
    def constraint_dimension(self) -> int:
        """Number of constraints: 3 bilinear + 3 closure = 6"""
        return 6

    @property
    def effective_dimension(self) -> int:
        """Effective dimension: 24 - 2×6 = 12 (phase space after constraints)"""
        return self.dimension - 2 * self.constraint_dimension

    def to_cartesian(self, masses: Masses) -> CartesianState:
        """
        Convert spinor state to Cartesian 3BP state.

        Returns:
            Cartesian state with (r₁, r₂, r₃, v₁, v₂, v₃)
        """
        # Apply inverse KS to each pair
        r12, v12 = KSState(self.u12, self.u12_prime, self.fictitious_time).to_cartesian()
        r23, v23 = KSState(self.u23, self.u23_prime, self.fictitious_time).to_cartesian()
        r31, v31 = KSState(self.u31, self.u31_prime, self.fictitious_time).to_cartesian()

        # Reconstruct individual body positions
        # (requires solving linear system with closure constraint)
        positions, velocities = reconstruct_body_coordinates(
            r12, r23, r31,
            v12, v23, v31,
            masses
        )

        return CartesianState(positions, velocities, dimension=3)


@dataclass(frozen=True)
class ConstraintManifold:
    """
    Represents the constraint manifold for pairwise KS coordinates.

    Constraints:
        1. Bilinear: ‖u_ij‖² = r_ij for each pair
        2. Closure: r₁₂ + r₂₃ + r₃₁ = 0 (as vectors)
    """
    tolerance: float = 1e-14

    def evaluate_constraints(
        self,
        state: PairwiseSpinorState
    ) -> np.ndarray:
        """
        Evaluate constraint functions g(u) = 0.

        Returns:
            Array of shape (6,) with constraint violations
        """
        constraints = np.zeros(6)

        # Bilinear constraints (3)
        # (In practice, may use weaker formulation)
        constraints[0] = state.u12.norm_squared - compute_r12(state)
        constraints[1] = state.u23.norm_squared - compute_r23(state)
        constraints[2] = state.u31.norm_squared - compute_r31(state)

        # Closure constraint (3 components)
        r12 = levi_civita_map(state.u12, state.u12)
        r23 = levi_civita_map(state.u23, state.u23)
        r31 = levi_civita_map(state.u31, state.u31)

        closure = r12 + r23 + r31  # Should be ≈ 0
        constraints[3:6] = closure

        return constraints

    def is_satisfied(self, state: PairwiseSpinorState) -> bool:
        """Check if constraints are satisfied"""
        g = self.evaluate_constraints(state)
        return np.linalg.norm(g) < self.tolerance

    def project_onto_manifold(
        self,
        state: PairwiseSpinorState
    ) -> PairwiseSpinorState:
        """
        Project state onto constraint manifold.

        Uses Newton-Raphson to find nearest point satisfying constraints.
        """
        # Iterative projection algorithm
        # (Implementation: Newton solver for g(u) = 0)
        pass
```

---

## Part A: KS Transformation for Single Pair

### Objectives

1. Implement Levi-Civita matrix $L(\mathbf{u})$
2. Forward transform: $(r, v) \to (u, u')$
3. Inverse transform: $(u, u') \to (r, v)$
4. Validate bilinear relation: $r = |\mathbf{u}|^2$

### Key Algorithms

#### A1: Levi-Civita Matrix

```python
def levi_civita_matrix(u: SpinorVector) -> np.ndarray:
    """
    Compute Levi-Civita matrix L(u).

    L(u) is a 3×4 matrix such that r = L(u) u.

    Args:
        u: Spinor vector (4D)

    Returns:
        L(u) matrix (3×4)
    """
    u0, u1, u2, u3 = u.components

    L = np.array([
        [u0, -u1, -u2, -u3],
        [u1,  u0, -u3,  u2],
        [u2,  u3,  u0, -u1]
    ])

    return L


def levi_civita_map(u1: SpinorVector, u2: SpinorVector) -> np.ndarray:
    """
    Compute bilinear map L(u1) u2.

    This maps two 4D spinors to a 3D vector.

    Args:
        u1, u2: Spinor vectors

    Returns:
        3D vector L(u1) u2
    """
    L = levi_civita_matrix(u1)
    return L @ u2.components
```

#### A2: Forward KS Transform

```python
def cartesian_to_ks(
    position: np.ndarray,
    velocity: np.ndarray
) -> KSState:
    """
    Transform Cartesian (r, v) to KS spinor (u, u').

    This is the inverse problem: given r, find u such that L(u)u = r.

    Args:
        position: 3D position vector
        velocity: 3D velocity vector

    Returns:
        KSState with (u, u', s=0)
    """
    r = position
    v = velocity
    r_norm = np.linalg.norm(r)

    # Choose spinor u such that r = L(u) u
    # Multiple solutions exist (gauge freedom); pick canonical one

    # Canonical choice (from Stiefel & Scheifele):
    if r[2] >= 0:
        # Use "northern hemisphere" chart
        u0 = np.sqrt(r_norm + r[2])
        u1 = r[1] / (np.sqrt(2) * np.sqrt(r_norm + r[2]))
        u2 = -r[0] / (np.sqrt(2) * np.sqrt(r_norm + r[2]))
        u3 = 0.0
    else:
        # Use "southern hemisphere" chart
        u0 = r[1] / (np.sqrt(2) * np.sqrt(r_norm - r[2]))
        u1 = np.sqrt(r_norm - r[2])
        u2 = 0.0
        u3 = -r[0] / (np.sqrt(2) * np.sqrt(r_norm - r[2]))

    u = SpinorVector(np.array([u0, u1, u2, u3]))

    # Compute u' from v: v = 2 L(u) u'
    # Solve: L(u) u' = v/2
    L = levi_civita_matrix(u)

    # Least-squares solution (L is 3×4, underdetermined)
    u_prime_components, _, _, _ = np.linalg.lstsq(L, v / 2, rcond=None)
    u_prime = SpinorVector(u_prime_components)

    return KSState(u=u, u_prime=u_prime, fictitious_time=0.0)
```

#### A3: Validation Tests

```python
def test_bilinear_relation():
    """
    Verify r = L(u) u and |r|² = |u|⁴.
    """
    # Random 3D vector
    r = np.random.randn(3)
    v = np.random.randn(3)

    # Transform to KS
    ks_state = cartesian_to_ks(r, v)

    # Reconstruct position
    r_reconstructed = levi_civita_map(ks_state.u, ks_state.u)

    # Check bilinear relation
    assert np.allclose(r, r_reconstructed, atol=1e-12)

    # Check norm relation
    r_norm_squared = np.dot(r, r)
    u_norm_fourth = ks_state.u.norm_squared ** 2

    assert np.abs(r_norm_squared - u_norm_fourth) < 1e-12


def test_velocity_transform():
    """
    Verify v = 2 L(u) u'.
    """
    r = np.random.randn(3)
    v = np.random.randn(3)

    ks_state = cartesian_to_ks(r, v)

    # Reconstruct velocity
    v_reconstructed = 2 * levi_civita_map(ks_state.u, ks_state.u_prime)

    assert np.allclose(v, v_reconstructed, atol=1e-10)


def test_round_trip():
    """
    Verify Cartesian → KS → Cartesian is identity.
    """
    r = np.random.randn(3)
    v = np.random.randn(3)

    # Forward
    ks_state = cartesian_to_ks(r, v)

    # Backward
    r_back, v_back = ks_state.to_cartesian()

    assert np.allclose(r, r_back, atol=1e-12)
    assert np.allclose(v, v_back, atol=1e-10)
```

---

## Part B: Pairwise Application to 3BP

### Objectives

1. Define pairwise spinor coordinates for 3BP
2. Implement constraint manifold (bilinear + closure)
3. Validate constraint satisfaction
4. Projection: Spinor → Cartesian 3BP

### Key Algorithms

#### B1: Pairwise Coordinate Construction

```python
def cartesian_3bp_to_pairwise_spinor(
    cart_state: CartesianState,
    masses: Masses
) -> PairwiseSpinorState:
    """
    Transform Cartesian 3BP to pairwise spinor coordinates.

    Args:
        cart_state: (r₁, r₂, r₃, v₁, v₂, v₃)
        masses: Body masses

    Returns:
        PairwiseSpinorState with (u₁₂, u₂₃, u₃₁)
    """
    # Compute pairwise relative coordinates
    r12 = cart_state.positions[0] - cart_state.positions[1]
    r23 = cart_state.positions[1] - cart_state.positions[2]
    r31 = cart_state.positions[2] - cart_state.positions[0]

    v12 = cart_state.velocities[0] - cart_state.velocities[1]
    v23 = cart_state.velocities[1] - cart_state.velocities[2]
    v31 = cart_state.velocities[2] - cart_state.velocities[0]

    # Transform each pair to KS
    ks12 = cartesian_to_ks(r12, v12)
    ks23 = cartesian_to_ks(r23, v23)
    ks31 = cartesian_to_ks(r31, v31)

    return PairwiseSpinorState(
        u12=ks12.u,
        u23=ks23.u,
        u31=ks31.u,
        u12_prime=ks12.u_prime,
        u23_prime=ks23.u_prime,
        u31_prime=ks31.u_prime,
        fictitious_time=0.0
    )
```

#### B2: Constraint Evaluation

```python
def evaluate_closure_constraint(
    state: PairwiseSpinorState
) -> np.ndarray:
    """
    Evaluate closure: r₁₂ + r₂₃ + r₃₁ = 0.

    Args:
        state: Pairwise spinor state

    Returns:
        Closure violation (3D vector, should be ≈ 0)
    """
    # Reconstruct 3D vectors from spinors
    r12 = levi_civita_map(state.u12, state.u12)
    r23 = levi_civita_map(state.u23, state.u23)
    r31 = levi_civita_map(state.u31, state.u31)

    closure = r12 + r23 + r31

    return closure


def project_onto_constraint_manifold(
    state: PairwiseSpinorState,
    max_iterations: int = 100,
    tolerance: float = 1e-14
) -> PairwiseSpinorState:
    """
    Project spinor state onto constraint manifold.

    Uses iterative Newton-Raphson to enforce constraints:
        g(u) = 0

    Args:
        state: Initial state (possibly off-manifold)
        max_iterations: Max Newton steps
        tolerance: Convergence tolerance

    Returns:
        Projected state satisfying constraints
    """
    u = state.to_vector()  # Flatten to vector

    for iteration in range(max_iterations):
        # Evaluate constraints
        g = evaluate_all_constraints(u)

        if np.linalg.norm(g) < tolerance:
            break  # Converged

        # Compute constraint Jacobian ∇g
        jacobian = compute_constraint_jacobian(u)

        # Newton step: Δu = -(∇g)^T g / ‖∇g‖²
        # (Projected gradient descent)
        delta_u = -jacobian.T @ g / (np.linalg.norm(jacobian) ** 2 + 1e-10)

        # Update
        u = u + delta_u

    # Convert back to PairwiseSpinorState
    return PairwiseSpinorState.from_vector(u)
```

#### B3: Inverse Transform

```python
def pairwise_spinor_to_cartesian_3bp(
    spinor_state: PairwiseSpinorState,
    masses: Masses
) -> CartesianState:
    """
    Reconstruct Cartesian 3BP from pairwise spinors.

    This requires solving a linear system since:
        r₁₂ = r₁ - r₂
        r₂₃ = r₂ - r₃
        r₃₁ = r₃ - r₁

    Args:
        spinor_state: Pairwise spinor coordinates
        masses: Body masses

    Returns:
        Cartesian 3BP state
    """
    # Reconstruct pairwise Cartesian
    r12, v12 = KSState(
        spinor_state.u12,
        spinor_state.u12_prime,
        spinor_state.fictitious_time
    ).to_cartesian()

    r23, v23 = KSState(
        spinor_state.u23,
        spinor_state.u23_prime,
        spinor_state.fictitious_time
    ).to_cartesian()

    r31, v31 = KSState(
        spinor_state.u31,
        spinor_state.u31_prime,
        spinor_state.fictitious_time
    ).to_cartesian()

    # Solve linear system for individual body coordinates
    # System:
    #   r₁ - r₂ = r₁₂
    #   r₂ - r₃ = r₂₃
    #   r₃ - r₁ = r₃₁  (redundant: r₁₂ + r₂₃ + r₃₁ = 0)
    #   m₁r₁ + m₂r₂ + m₃r₃ = 0  (barycentric)

    # Matrix form: A [r₁; r₂; r₃] = b
    # (Implementation: linear solve)

    A = np.array([
        [1, -1,  0],
        [0,  1, -1],
        [masses.m1, masses.m2, masses.m3]
    ])

    b_x = np.array([r12[0], r23[0], 0])
    b_y = np.array([r12[1], r23[1], 0])
    b_z = np.array([r12[2], r23[2], 0])

    x_coords = np.linalg.solve(A, b_x)
    y_coords = np.linalg.solve(A, b_y)
    z_coords = np.linalg.solve(A, b_z)

    positions = np.column_stack([x_coords, y_coords, z_coords])

    # Similarly for velocities
    # (Omitted for brevity—same linear system)

    velocities = solve_for_velocities(v12, v23, v31, masses)

    return CartesianState(positions, velocities, dimension=3)
```

---

## Part C: Constrained Hamiltonian Dynamics

### Objectives

1. Define regularized Hamiltonian in fictitious time
2. Implement constrained integrator (RATTLE/SHAKE)
3. Integrate through collisions (validate regularization)
4. Monitor constraint drift

### Key Algorithms

#### C1: Regularized Hamiltonian

```python
def regularized_hamiltonian(
    state: PairwiseSpinorState,
    masses: Masses,
    G: float = 1.0
) -> float:
    """
    Compute regularized Hamiltonian in fictitious time s.

    𝒦 = (1/2) Σ |u'ᵢⱼ|² / |uᵢⱼ|² - Vᵣₑ(u)

    where Vᵣₑ is the regularized potential.

    Args:
        state: Spinor state
        masses: Body masses
        G: Gravitational constant

    Returns:
        𝒦 (energy in fictitious time)
    """
    # Kinetic term
    T = 0.0
    for u, u_prime in [
        (state.u12, state.u12_prime),
        (state.u23, state.u23_prime),
        (state.u31, state.u31_prime)
    ]:
        r = u.norm_squared  # r = |u|²
        u_prime_norm_sq = u_prime.norm_squared

        T += 0.5 * u_prime_norm_sq / r

    # Potential term (transformed)
    # V = -G Σ mᵢmⱼ / rᵢⱼ
    # In regularized coords: Vᵣₑ = -G Σ mᵢmⱼ / |uᵢⱼ|²

    V_reg = 0.0
    r12 = state.u12.radius
    r23 = state.u23.radius
    r31 = state.u31.radius

    V_reg -= G * masses.m1 * masses.m2 / r12
    V_reg -= G * masses.m2 * masses.m3 / r23
    V_reg -= G * masses.m3 * masses.m1 / r31

    return T + V_reg
```

#### C2: RATTLE Integrator

```python
class RATTLEIntegrator:
    """
    Symplectic integrator for constrained Hamiltonian systems.

    RATTLE = velocity Verlet + constraint projection.
    Maintains constraints to machine precision.
    """

    def __init__(
        self,
        hamiltonian: Callable,
        constraint_manifold: ConstraintManifold,
        masses: Masses
    ):
        self.hamiltonian = hamiltonian
        self.constraints = constraint_manifold
        self.masses = masses

    def step(
        self,
        state: PairwiseSpinorState,
        ds: float  # Step in fictitious time
    ) -> PairwiseSpinorState:
        """
        Single RATTLE step.

        Algorithm:
            1. Half-step velocity (unconstrained)
            2. Full-step position
            3. Project position onto manifold
            4. Half-step velocity (with constraint correction)
            5. Project velocity onto tangent space

        Args:
            state: Current state
            ds: Fictitious time step

        Returns:
            Updated state (on constraint manifold)
        """
        # 1. Half-step velocity
        forces = self.compute_forces(state)
        u_prime_half = state.velocities + 0.5 * ds * forces

        # 2. Full-step position
        u_new = state.positions + ds * u_prime_half

        # 3. Project position
        u_new_projected = self.constraints.project_onto_manifold(u_new)

        # 4. Compute corrected velocity
        # (requires constraint Jacobian)
        lambda_multipliers = self.compute_lagrange_multipliers(
            u_new_projected,
            u_prime_half,
            ds
        )

        jacobian = self.constraints.compute_jacobian(u_new_projected)
        u_prime_corrected = u_prime_half - jacobian.T @ lambda_multipliers

        # 5. Second half-step
        forces_new = self.compute_forces_from_positions(u_new_projected)
        u_prime_new = u_prime_corrected + 0.5 * ds * forces_new

        # 6. Project velocity onto tangent space
        u_prime_final = self.project_velocity_onto_tangent(
            u_prime_new,
            u_new_projected
        )

        return PairwiseSpinorState(
            positions=u_new_projected,
            velocities=u_prime_final,
            fictitious_time=state.fictitious_time + ds
        )

    def integrate(
        self,
        initial_state: PairwiseSpinorState,
        s_span: tuple[float, float],
        n_steps: int
    ) -> SpinorTrajectory:
        """
        Integrate on constraint manifold.

        Args:
            initial_state: Initial spinor state
            s_span: Fictitious time interval
            n_steps: Number of steps

        Returns:
            Trajectory in spinor coordinates
        """
        s_start, s_end = s_span
        ds = (s_end - s_start) / n_steps

        states = [initial_state]
        s_values = [s_start]

        state = initial_state

        for i in range(n_steps):
            state = self.step(state, ds)
            states.append(state)
            s_values.append(s_start + (i + 1) * ds)

        return SpinorTrajectory(
            fictitious_times=np.array(s_values),
            states=states
        )
```

#### C3: Collision Passage Validation

```python
def test_collision_regularization():
    """
    Integrate through a binary collision (1-2 approach).

    Without regularization: integrator fails at r₁₂ → 0.
    With KS regularization: smooth passage through collision.
    """
    masses = Masses(1.0, 1.0, 1.0)

    # Initial condition: body 1 and 2 on collision course
    # (Head-on collision setup)
    cart_state = setup_collision_initial_condition()

    # Transform to KS
    spinor_state = cartesian_3bp_to_pairwise_spinor(cart_state, masses)

    # Integrate with RATTLE
    integrator = RATTLEIntegrator(
        hamiltonian=lambda s: regularized_hamiltonian(s, masses),
        constraint_manifold=ConstraintManifold(),
        masses=masses
    )

    trajectory = integrator.integrate(
        initial_state=spinor_state,
        s_span=(0, 100),  # Long integration in fictitious time
        n_steps=10000
    )

    # Convert back to Cartesian
    cart_trajectory = [
        pairwise_spinor_to_cartesian_3bp(s, masses)
        for s in trajectory.states
    ]

    # Find minimum distance
    min_r12 = min(
        np.linalg.norm(s.positions[0] - s.positions[1])
        for s in cart_trajectory
    )

    print(f"Minimum r₁₂: {min_r12:.6e}")

    # Should reach very close to zero without crashing
    assert min_r12 < 1e-3, "Should pass through near-collision"
    assert len(cart_trajectory) == len(trajectory.states), "Integration completed"
```

---

## Part D: Integrability Analysis

### Objectives

1. Search for integrals of motion in spinor coordinates
2. Compare with S¹ lift results (WP2.2)
3. Analyze SU(2) spinor symmetry structure
4. Classify: integrable, partially integrable, or non-integrable

### Key Algorithms

#### D1: Integral Search in Spinor Coordinates

```python
def search_spinor_integrals(
    trajectory: SpinorTrajectory,
    candidate_functions: list[Callable]
) -> list[Callable]:
    """
    Search for conserved quantities in spinor representation.

    Tests candidates beyond standard integrals (E, L).

    Args:
        trajectory: Test trajectory in spinor coords
        candidate_functions: List of trial functions

    Returns:
        List of conserved candidates
    """
    conserved = []

    for candidate in candidate_functions:
        values = [candidate(state) for state in trajectory.states]

        drift = np.max(np.abs(values - values[0]))

        if drift < 1e-12:
            conserved.append(candidate)

    return conserved


def generate_spinor_candidates() -> list[Callable]:
    """
    Generate candidate integrals using spinor structure.

    Ideas:
        - Spinor norms: |u₁₂|, |u₂₃|, |u₃₁|
        - SU(2) Casimirs: u · u (quaternion norm)
        - Cross products: u₁₂ · (u₂₃ × u₃₁)
        - Spinor inner products: ⟨u₁₂, u₂₃⟩
    """
    candidates = []

    # Norm combinations
    def norm_sum(state):
        return (state.u12.norm_squared +
                state.u23.norm_squared +
                state.u31.norm_squared)

    candidates.append(norm_sum)

    # Spinor dot products
    def dot_12_23(state):
        return np.dot(state.u12.components, state.u23.components)

    candidates.append(dot_12_23)

    # More sophisticated: SU(2) invariants
    # (Implementation depends on spinor algebra library)

    return candidates
```

#### D2: Comparison with S¹ Lift

```python
def compare_lift_strategies(
    cart_state: CartesianState,
    masses: Masses,
    integration_time: float
) -> dict:
    """
    Compare S¹ lift (WP2.2) vs. KS lift (WP2.3).

    Metrics:
        - Number of integrals found
        - Computational cost
        - Collision handling
        - Chaos indicators

    Args:
        cart_state: Initial 3BP state
        masses: Body masses
        integration_time: How long to integrate

    Returns:
        Comparison report
    """
    # S¹ lift integration
    s1_trajectory = integrate_s1_lift(cart_state, masses, integration_time)
    s1_integrals = find_integrals(s1_trajectory)

    # KS lift integration
    ks_trajectory = integrate_ks_lift(cart_state, masses, integration_time)
    ks_integrals = find_integrals(ks_trajectory)

    # Chaos indicators
    s1_lyapunov = compute_lyapunov_exponent(s1_trajectory)
    ks_lyapunov = compute_lyapunov_exponent(ks_trajectory)

    return {
        'S1_lift': {
            'dimension': s1_trajectory.dimension,
            'n_integrals': len(s1_integrals),
            'lyapunov': s1_lyapunov,
            'computational_cost': s1_trajectory.computation_time
        },
        'KS_lift': {
            'dimension': ks_trajectory.dimension,
            'n_integrals': len(ks_integrals),
            'lyapunov': ks_lyapunov,
            'computational_cost': ks_trajectory.computation_time
        },
        'comparison': {
            'ks_advantage': len(ks_integrals) > len(s1_integrals),
            'dimension_increase': ks_trajectory.dimension - s1_trajectory.dimension
        }
    }
```

#### D3: SU(2) Symmetry Analysis

```python
def analyze_su2_structure(
    spinor_state: PairwiseSpinorState
) -> dict:
    """
    Analyze SU(2) spinor representation structure.

    Spinors form a representation of SU(2) (2:1 cover of SO(3)).
    Check for SU(2) symmetries that may reveal integrability.

    Returns:
        Dictionary with SU(2) analysis
    """
    # Spinor as complex 2-vector (alternative representation)
    # u = (u₀ + i u₁, u₂ + i u₃)

    # Check for SU(2) invariants
    # (Implementation depends on representation theory)

    pass
```

---

## Integration with Existing Infrastructure

### Dependencies

- **Task 2.1.1**: Cartesian coordinates (for round-trip transforms)
- **WP2.2**: S¹ lift (for comparison)
- **WP1**: High-precision integrators (symplectic methods)

### Outputs

- Regularized trajectories (collision-free)
- Integrability classification for KS lift
- Comparison report: S¹ vs. KS
- Handoff to WP3: Optimal lift strategy for invariant search

---

## Implementation Schedule

### Phase 1: Single-Pair KS (3 days)
- **Day 1**: Levi-Civita matrix, bilinear relation
- **Day 2**: Forward/inverse transforms
- **Day 3**: Validation tests, round-trip accuracy

### Phase 2: Pairwise Extension (3 days)
- **Day 4**: Pairwise coordinate system
- **Day 5**: Constraint manifold definition
- **Day 6**: Projection onto manifold

### Phase 3: Constrained Integration (4 days)
- **Day 7-8**: RATTLE integrator implementation
- **Day 9**: Fictitious time regularization
- **Day 10**: Collision passage tests

### Phase 4: Integrability Analysis (3 days)
- **Day 11**: Integral search in spinor coords
- **Day 12**: SU(2) symmetry analysis
- **Day 13**: Comparison with S¹ lift

### Phase 5: Documentation (2 days)
- **Day 14**: Technical report, visualizations
- **Day 15**: Final validation, results summary

**Total**: 15 days

---

## Success Criteria

### Functional Requirements
- [ ] KS transform implemented (forward and inverse)
- [ ] Bilinear relation validated: $r = |\mathbf{u}|^2$ (error < 1e-12)
- [ ] Pairwise spinor system functional
- [ ] Constraints satisfied during integration (drift < 1e-10)
- [ ] RATTLE integrator passes tests

### Scientific Requirements
- [ ] **Collision Regularization**: Integrate through $r_{ij} < 10^{-5}$ without failure
- [ ] **Integrability Classification**:
  - How many independent integrals in KS coordinates?
  - Compare to S¹ lift (more? fewer? same?)
- [ ] **Spinor Structure**: Document SU(2) representation properties
- [ ] **Comparative Analysis**: Is KS lift "better" than S¹? (define metric)

### Quality Requirements
- [ ] Test coverage > 95%
- [ ] Complete API documentation
- [ ] Technical report written
- [ ] Visualization of spinor dynamics

---

## Risk Mitigation

### Risk 1: Constraint Drift
**Likelihood**: High
**Impact**: High (violates constraint manifold)

**Mitigation**:
- Use RATTLE (constraint-preserving integrator)
- Monitor constraints at every step
- Automatic re-projection if drift > threshold

### Risk 2: Computational Cost of 12D Integration
**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- 12D is manageable (similar to 3BP in 4D)
- Use sparse Jacobians for constraints
- Adaptive step size

### Risk 3: KS May Not Reveal New Integrals
**Likelihood**: High
**Impact**: Medium (disappointing but scientifically valid)

**Mitigation**:
- Negative result is valuable: documents obstruction
- If KS fails, confirms 3BP is "truly" non-integrable (no lift helps)
- Proceed to WP3 with best available lift

### Risk 4: Chart Singularities in KS Transform
**Likelihood**: Medium
**Impact**: Low

**Mitigation**:
- Use multiple coordinate charts (northern/southern hemisphere)
- Automatic chart switching when needed
- Well-documented in KS literature

---

## References

1. Kustaanheimo & Stiefel, "Perturbation theory of Kepler motion based on spinor regularization" (1965)
2. Stiefel & Scheifele, *Linear and Regular Celestial Mechanics* (1971)
3. Waldvogel, "Quaternions and the perturbed Kepler problem" (2006)
4. Aarseth, *Gravitational N-Body Simulations* (2003) - KS in practice
5. Yoshida, "A new derivation of the Kustaanheimo-Stiefel transformation" (1982)

---

## Appendix: Why KS Regularization Works

The KS transformation regularizes collisions because:

1. **Collision** ($r \to 0$) **maps to** $|\mathbf{u}| \to 0$ (origin in 4D)
2. **The origin in 4D is a regular point** of the transformed equations
3. **Fictitious time slows down** near collisions: $dt/ds = r \to 0$
   - Infinite real time to reach collision
   - Finite fictitious time to pass through

**Analogy**: Like approaching the speed of light—from your frame (fictitious time $s$), you reach it in finite time; from external frame (real time $t$), it takes forever.

This is the same mechanism that makes **Poincaré maps** work: regularize time so that infinite-time events become finite in a new clock.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Next Review**: After Part A implementation
**Dependencies**: WP2.2 (S¹ lift) for comparison
**Status**: Ready for Implementation
