# Task 2.1.2: Computation of the "Magnetic Twist" (Connection and Curvature)
## WP 2.1 - Geometric Reduction and Shape Space Analysis

**Status**: Design Phase
**Priority**: Critical Path
**Estimated Duration**: 8-10 days
**Dependencies**: Task 2.1.1 Complete (Coordinate Systems and Reduction)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Implementation Architecture](#implementation-architecture)
4. [Part A: Connection Form Computation](#part-a-connection-form-computation)
5. [Part B: Curvature Computation](#part-b-curvature-computation)
6. [Part C: Numerical Implementation](#part-c-numerical-implementation)
7. [Part D: Visualization and Validation](#part-d-visualization-and-validation)
8. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
9. [Implementation Schedule](#implementation-schedule)
10. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

Task 2.1.2 implements the computation of the **mechanical connection one-form** ($\mathcal{A}$) and its **curvature two-form** ($\mathcal{F} = d\mathcal{A}$). These geometric objects encode the fundamental obstruction to integrability in the reduced (shape space) dynamics of the three-body problem.

**Physical Interpretation**: The connection $\mathcal{A}$ measures how the system automatically rotates when you change its shape while conserving angular momentum. The curvature $\mathcal{F}$ measures the path-dependence of this rotation — if $\mathcal{F} \neq 0$, the system exhibits genuine geometric complexity that cannot be eliminated by coordinate changes.

### Objectives

1. **Symbolic Computation**: Derive analytical expressions for the connection one-form in shape space coordinates
2. **Numerical Evaluation**: Compute $\mathcal{A}$ and $\mathcal{F}$ at arbitrary phase space points with high precision
3. **Curvature Analysis**: Identify regions where $|\mathcal{F}| \neq 0$ (obstruction to integrability)
4. **Visualization**: Create intuitive visualizations of the connection and curvature fields
5. **Validation**: Verify theoretical properties (Stokes' theorem, gauge invariance)

### Deliverables

- **Deliverable 2.2.1**: Analytical expressions for $\mathcal{A}$ in multiple coordinate representations (symbolic)
- **Deliverable 2.2.2**: High-precision numerical evaluator for $\mathcal{A}$ and $\mathcal{F}$
- **Deliverable 2.2.3**: Curvature field visualization library
- **Deliverable 2.2.4**: Validation report confirming theoretical properties
- **Deliverable 2.2.5**: Integration with WP2 lifts (S¹ and KS-Spinor)

---

## Mathematical Background

### The Mechanical Connection

When we perform symplectic reduction by rotations, the reduced symplectic form on shape space is **not** simply the quotient of the original symplectic form. Instead, it acquires a "magnetic" or "gauge" term:

$$
\omega_{\text{red}} = \omega_{\text{shape}} - d(\mathbf{L} \cdot \mathcal{A})
$$

where:
- $\omega_{\text{shape}}$ is the naive symplectic form on shape space
- $\mathbf{L}$ is the conserved angular momentum (labels the reduction)
- $\mathcal{A}$ is the **mechanical connection one-form**

### Definition of the Connection

The connection $\mathcal{A}$ is defined as follows:

**Setup**: Let $\pi: M \to M/SO(3)$ be the projection from the full phase space to shape space.

**Connection Form**: For a tangent vector $v \in T_s(M/SO(3))$ in shape space, we can lift it to a horizontal tangent vector $\tilde{v} \in T_m M$ (at some $m \in \pi^{-1}(s)$). The connection is:

$$
\mathcal{A}(v) = \mu_{\text{rot}}(\tilde{v}) = \langle \mathbf{L}, \xi(v) \rangle
$$

where $\xi(v)$ is the infinitesimal rotation generator associated with the lift.

**Practical Formula** (planar case): In terms of shape coordinates $(r_{12}, r_{23}, r_{31}, \dot{r}_{12}, \dot{r}_{23}, \dot{r}_{31})$ and the orientation angle $\theta$:

$$
\mathcal{A} = \mathcal{A}_{r_{12}} dr_{12} + \mathcal{A}_{r_{23}} dr_{23} + \mathcal{A}_{r_{31}} dr_{31}
$$

where the coefficients $\mathcal{A}_{r_{ij}}$ measure the rotation rate induced by changing distance $r_{ij}$.

### The Curvature Two-Form

The curvature is the exterior derivative of the connection:

$$
\mathcal{F} = d\mathcal{A}
$$

In coordinates:

$$
\mathcal{F} = \sum_{i<j} F_{ij} \, dr_i \wedge dr_j
$$

where:

$$
F_{ij} = \frac{\partial \mathcal{A}_j}{\partial r_i} - \frac{\partial \mathcal{A}_i}{\partial r_j}
$$

**Key Property**: $\mathcal{F} = 0$ (flat connection) if and only if the reduced system admits action-angle coordinates (local integrability). For the three-body problem, we expect $\mathcal{F} \neq 0$ in generic regions, confirming non-integrability.

### Theoretical Properties to Validate

1. **Stokes' Theorem**: $\oint_{\partial S} \mathcal{A} = \int_S \mathcal{F}$ for any 2D surface $S$ in shape space
2. **Gauge Invariance**: $\mathcal{A}$ transforms correctly under orientation-fixing gauge changes
3. **Bianchi Identity**: $d\mathcal{F} = 0$ (automatic for 2-forms in 3D space)
4. **Compatibility with Reduction**: The reduced Hamiltonian vector field is horizontal with respect to $\mathcal{A}$

---

## Implementation Architecture

### Module Structure

```
src/python/geometry/
├── __init__.py                    # Package exports
├── connection.py                  # A: Mechanical connection computation
├── curvature.py                   # B: Curvature computation
├── locked_inertia.py              # Helper: Locked inertia tensor
├── shape_basis.py                 # Helper: Shape space vector fields
└── validation.py                  # Property validation (Stokes, etc.)

src/python/visualization/
├── connection_field.py            # D: Vector field visualization
├── curvature_heatmap.py          # D: Curvature magnitude plots
└── geometric_flow.py             # D: Parallel transport visualization

tests/geometry/
├── test_connection.py             # Unit tests for connection
├── test_curvature.py              # Unit tests for curvature
├── test_stokes_theorem.py         # Validation: Stokes theorem
└── test_gauge_invariance.py       # Validation: Gauge transformations
```

### Data Structures

```python
@dataclass(frozen=True)
class ConnectionForm:
    """
    Mechanical connection one-form on shape space.

    Represents A = A_i dx^i where x^i are shape coordinates.
    """
    coefficients: np.ndarray  # Components A_i
    coordinate_names: list[str]  # ['r12', 'r23', 'r31', ...]
    base_point: ShapeSpaceState  # Where connection is evaluated
    angular_momentum: np.ndarray  # L (conserved quantity)

    def evaluate(self, tangent_vector: np.ndarray) -> float:
        """Evaluate A(v) for tangent vector v"""
        return np.dot(self.coefficients, tangent_vector)


@dataclass(frozen=True)
class CurvatureForm:
    """
    Curvature two-form F = dA on shape space.

    Represents F = (1/2) F_{ij} dx^i ∧ dx^j (antisymmetric).
    """
    matrix: np.ndarray  # Antisymmetric matrix F_{ij}
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def magnitude(self) -> float:
        """Frobenius norm of curvature"""
        return np.linalg.norm(self.matrix)

    def is_flat(self, tolerance: float = 1e-14) -> bool:
        """Check if connection is flat (F ≈ 0)"""
        return self.magnitude() < tolerance
```

### Design Patterns

1. **Lazy Evaluation**: Compute connection only when needed (expensive operation)
2. **Memoization**: Cache connection computations for repeated queries
3. **Symbolic + Numeric**: Use SymPy for derivation, NumPy for evaluation
4. **Coordinate-Agnostic**: Support multiple shape space coordinates (distances, angles, complex variable)

---

## Part A: Connection Form Computation

### Objectives

1. Derive analytical expressions for $\mathcal{A}$ in shape space coordinates
2. Implement numerical evaluation at arbitrary phase space points
3. Validate against known test cases (e.g., two-body limit)

### Key Algorithms

#### A1: Locked Inertia Tensor

The connection is related to the **locked inertia tensor** — the inertia tensor when shape is held fixed:

$$
I_{locked} = \sum_{i=1}^3 m_i |\mathbf{r}_i - \mathbf{r}_{cm}|^2
$$

**Algorithm**:
```python
def compute_locked_inertia_tensor(state: CartesianState, masses: Masses) -> np.ndarray:
    """
    Compute locked inertia tensor I_αβ = Σ m_i (r_i^α r_i^β)

    This is the inertia tensor in the body frame (barycentric).
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    r = state.positions  # Already in barycentric frame

    I = np.zeros((3, 3))
    for i in range(3):
        I += m[i] * np.outer(r[i], r[i])

    return I
```

#### A2: Shape Space Vector Field Lift

To compute $\mathcal{A}$, we need to lift shape space tangent vectors to the full phase space.

**Algorithm**: Given a shape velocity $\delta s$ (e.g., change in $r_{12}$), compute the induced angular velocity $\omega$.

```python
def lift_shape_tangent_to_rotation(
    shape_state: ShapeSpaceState,
    shape_velocity: np.ndarray,
    masses: Masses
) -> np.ndarray:
    """
    Lift shape space tangent vector to angular velocity.

    This computes ω such that changing shape by δs induces rotation ω
    while preserving angular momentum.

    Returns:
        omega: Angular velocity vector (3D)
    """
    # Convert shape to Cartesian (canonical orientation)
    cart_state = shape_to_cartesian_canonical(shape_state)

    # Compute locked inertia tensor
    I = compute_locked_inertia_tensor(cart_state, masses)

    # Compute how shape change affects angular momentum
    # This requires computing ∂L/∂s
    dL_ds = compute_angular_momentum_derivative(cart_state, shape_velocity, masses)

    # Solve: I ω = dL/ds for ω
    omega = np.linalg.solve(I, dL_ds)

    return omega
```

#### A3: Connection Coefficients

```python
def compute_connection_coefficients(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> ConnectionForm:
    """
    Compute connection one-form A at a point in shape space.

    Returns:
        ConnectionForm with coefficients [A_r12, A_r23, A_r31, ...]
    """
    # Shape coordinates
    shape_coords = ['r12', 'r23', 'r31']
    n_coords = len(shape_coords)

    coefficients = np.zeros(n_coords)

    # For each shape coordinate direction
    for i, coord in enumerate(shape_coords):
        # Unit tangent vector in this direction
        e_i = np.zeros(n_coords)
        e_i[i] = 1.0

        # Lift to angular velocity
        omega = lift_shape_tangent_to_rotation(shape_state, e_i, masses)

        # Connection coefficient: A_i = L · ω_i
        L = shape_state.L  # Angular momentum
        coefficients[i] = np.dot(L, omega)

    return ConnectionForm(
        coefficients=coefficients,
        coordinate_names=shape_coords,
        base_point=shape_state,
        angular_momentum=L
    )
```

### Validation Tests

1. **Two-Body Limit**: For three bodies with one mass → 0, connection should reduce to known formula
2. **Symmetry**: For equal masses, connection should respect permutation symmetry
3. **Gauge Invariance**: Connection transforms correctly under orientation gauge changes
4. **Dimensional Analysis**: Connection has units of angular momentum

---

## Part B: Curvature Computation

### Objectives

1. Implement exterior derivative operator on shape space
2. Compute curvature $\mathcal{F} = d\mathcal{A}$ numerically
3. Identify regions where $|\mathcal{F}| \neq 0$

### Key Algorithms

#### B1: Numerical Exterior Derivative

```python
def compute_exterior_derivative(
    connection_func: Callable[[ShapeSpaceState], ConnectionForm],
    base_state: ShapeSpaceState,
    epsilon: float = 1e-8
) -> CurvatureForm:
    """
    Compute dA using finite differences.

    F_{ij} = ∂A_j/∂x^i - ∂A_i/∂x^j

    Args:
        connection_func: Function that computes A at any point
        base_state: Point where to compute curvature
        epsilon: Step size for finite differences

    Returns:
        CurvatureForm object
    """
    # Get connection at base point
    A_base = connection_func(base_state)
    n = len(A_base.coefficients)

    # Compute Jacobian: ∂A_i/∂x^j
    jacobian = np.zeros((n, n))

    for j in range(n):
        # Perturb j-th coordinate
        state_plus = perturb_shape_coordinate(base_state, j, epsilon)
        state_minus = perturb_shape_coordinate(base_state, j, -epsilon)

        # Compute connection at perturbed points
        A_plus = connection_func(state_plus)
        A_minus = connection_func(state_minus)

        # Central difference
        jacobian[:, j] = (A_plus.coefficients - A_minus.coefficients) / (2 * epsilon)

    # Curvature: antisymmetric part of Jacobian
    curvature_matrix = jacobian - jacobian.T

    return CurvatureForm(
        matrix=curvature_matrix,
        coordinate_names=A_base.coordinate_names,
        base_point=base_state
    )
```

#### B2: Symbolic Curvature (Using SymPy)

For analytical validation:

```python
def symbolic_curvature_planar_equal_mass():
    """
    Derive symbolic expression for curvature (planar, equal masses).

    This provides an exact formula for validation.
    """
    import sympy as sp

    # Shape coordinates (symmetric under permutations for equal masses)
    r12, r23, r31 = sp.symbols('r_12 r_23 r_31', positive=True, real=True)

    # For equal masses, can use symmetry to simplify
    # Connection coefficients (derived analytically)
    A_r12 = sp.Function('A_r12')(r12, r23, r31)
    A_r23 = sp.Function('A_r23')(r12, r23, r31)
    A_r31 = sp.Function('A_r31')(r12, r23, r31)

    # Curvature components
    F_12_23 = sp.diff(A_r23, r12) - sp.diff(A_r12, r23)
    F_23_31 = sp.diff(A_r31, r23) - sp.diff(A_r23, r31)
    F_31_12 = sp.diff(A_r12, r31) - sp.diff(A_r31, r12)

    # For equal masses, explicit formulas can be derived
    # (This requires substantial calculation - see Part B design doc)

    return {
        'F_12_23': F_12_23,
        'F_23_31': F_23_31,
        'F_31_12': F_31_12
    }
```

#### B3: Curvature Magnitude

```python
def compute_curvature_magnitude(curvature: CurvatureForm) -> float:
    """
    Compute |F| = sqrt(Σ F_ij^2).

    This is the Frobenius norm of the curvature 2-form.
    """
    return np.linalg.norm(curvature.matrix)


def curvature_scalar_invariant(curvature: CurvatureForm) -> float:
    """
    Compute Tr(F^2), a scalar curvature invariant.

    This is gauge-invariant and measures curvature intensity.
    """
    F = curvature.matrix
    return np.trace(F @ F.T)
```

### Validation Tests

1. **Stokes' Theorem**: Verify $\oint_{\partial S} \mathcal{A} = \int_S \mathcal{F}$ numerically
2. **Bianchi Identity**: Check $d\mathcal{F} = 0$ (should be automatic)
3. **Non-Degeneracy**: Confirm $|\mathcal{F}| > 0$ for generic configurations

---

## Part C: Numerical Implementation

### Objectives

1. Efficient numerical routines for connection/curvature evaluation
2. High-precision arithmetic where needed
3. Vectorized operations for batch computations

### Performance Targets

- Connection evaluation: < 100 μs per point
- Curvature evaluation: < 1 ms per point (includes finite differences)
- Batch evaluation (1000 points): < 1 second

### Optimization Strategies

#### C1: Caching and Memoization

```python
from functools import lru_cache

class ConnectionEvaluator:
    """Evaluator with caching for repeated queries."""

    def __init__(self, masses: Masses):
        self.masses = masses
        self._cache = {}

    @lru_cache(maxsize=1024)
    def evaluate_at(self, state_hash: int) -> ConnectionForm:
        """Evaluate connection (with caching)"""
        # Hash-based lookup
        if state_hash in self._cache:
            return self._cache[state_hash]

        # Compute and cache
        connection = compute_connection_coefficients(state, self.masses)
        self._cache[state_hash] = connection
        return connection
```

#### C2: Vectorized Batch Computation

```python
def compute_connection_field_vectorized(
    shape_states: np.ndarray,  # (N, 6) array of shape space points
    masses: Masses
) -> np.ndarray:
    """
    Compute connection at N points simultaneously.

    Uses NumPy broadcasting for efficiency.

    Returns:
        (N, 3) array of connection coefficients
    """
    N = shape_states.shape[0]
    connections = np.zeros((N, 3))

    # Vectorized locked inertia computation
    # (requires careful indexing)

    for i in range(N):
        state = ShapeSpaceState.from_array(shape_states[i])
        conn = compute_connection_coefficients(state, masses)
        connections[i] = conn.coefficients

    return connections
```

#### C3: Adaptive Precision

```python
def compute_connection_adaptive_precision(
    shape_state: ShapeSpaceState,
    masses: Masses,
    target_precision: float = 1e-12
) -> ConnectionForm:
    """
    Compute connection, escalating to higher precision if needed.

    Strategy:
        1. Try double precision
        2. If numerical derivatives unstable, use quad precision
        3. If still unstable, use symbolic differentiation
    """
    # Try double precision first
    try:
        conn = compute_connection_coefficients(shape_state, masses)

        # Check stability
        if is_numerically_stable(conn, threshold=target_precision):
            return conn
    except NumericalInstabilityError:
        pass

    # Escalate to quad precision
    # (Implementation depends on QD library)

    # Last resort: symbolic
    return compute_connection_symbolic(shape_state, masses)
```

---

## Part D: Visualization and Validation

### Objectives

1. Create intuitive visualizations of connection and curvature fields
2. Interactive exploration tools
3. Publication-quality figures

### Key Visualizations

#### D1: Connection Vector Field

```python
def plot_connection_field(
    masses: Masses,
    shape_space_region: tuple,
    L_magnitude: float
):
    """
    Plot connection as a vector field on shape space.

    For 2D visualization, we fix one coordinate (e.g., r31) and plot
    in the (r12, r23) plane.
    """
    import matplotlib.pyplot as plt
    from matplotlib.quiver import Quiver

    # Create grid
    r12_range, r23_range = shape_space_region
    r12_grid, r23_grid = np.meshgrid(
        np.linspace(*r12_range, 20),
        np.linspace(*r23_range, 20)
    )

    # Compute connection at each grid point
    connections = np.zeros((20, 20, 2))

    for i in range(20):
        for j in range(20):
            # Create shape state (fixing r31)
            state = ShapeSpaceState(
                r12=r12_grid[i, j],
                r23=r23_grid[i, j],
                r31=1.0,  # Fixed
                L=L_magnitude
            )

            conn = compute_connection_coefficients(state, masses)
            connections[i, j] = conn.coefficients[:2]

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.quiver(r12_grid, r23_grid,
              connections[:, :, 0], connections[:, :, 1],
              color='blue', alpha=0.7)

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_title(f'Connection Field (L={L_magnitude:.2f})')

    plt.show()
```

#### D2: Curvature Heatmap

```python
def plot_curvature_heatmap(
    masses: Masses,
    shape_space_region: tuple,
    L_magnitude: float
):
    """
    Plot |F| as a heatmap on shape space.

    Regions with high |F| indicate strong obstruction to integrability.
    """
    # Compute curvature magnitude on grid
    curvature_magnitudes = np.zeros((50, 50))

    for i in range(50):
        for j in range(50):
            state = ...  # Create state at grid point
            curv = compute_curvature(state, masses)
            curvature_magnitudes[i, j] = curv.magnitude()

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(curvature_magnitudes,
                   extent=shape_space_region,
                   origin='lower',
                   cmap='hot',
                   interpolation='bilinear')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('$|\\mathcal{F}|$')

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_title('Curvature Magnitude')

    plt.show()
```

#### D3: Stokes' Theorem Validation

```python
def validate_stokes_theorem(
    masses: Masses,
    closed_path: list[ShapeSpaceState]
):
    """
    Verify ∮ A = ∫∫ F over a closed path.

    This is a fundamental validation of our computation.
    """
    # Compute line integral of A around path
    line_integral = 0.0

    for i in range(len(closed_path) - 1):
        state1 = closed_path[i]
        state2 = closed_path[i + 1]

        # Connection at midpoint
        state_mid = interpolate_shape_states(state1, state2, 0.5)
        conn = compute_connection_coefficients(state_mid, masses)

        # Path tangent
        tangent = compute_path_tangent(state1, state2)

        # Contribution to line integral
        line_integral += conn.evaluate(tangent)

    # Compute surface integral of F
    # (requires triangulation of enclosed surface)
    surface_integral = compute_surface_integral_of_curvature(
        closed_path, masses
    )

    # Compare
    error = abs(line_integral - surface_integral)
    relative_error = error / max(abs(line_integral), abs(surface_integral), 1e-10)

    print(f"Line integral:    {line_integral:.6e}")
    print(f"Surface integral: {surface_integral:.6e}")
    print(f"Relative error:   {relative_error:.6e}")

    return relative_error < 1e-10
```

---

## Integration with Existing Infrastructure

### Dependencies from Task 2.1.1

- `CartesianState`, `JacobiState`, `ShapeSpaceState` (coordinates)
- `RotationReducedState` (reduced states)
- `compute_angular_momentum()` (from cartesian.py)
- Shape space transformations

### Handoff to Future Tasks

- **WP 2.2 (S¹ Lift)**: Extended connection $\widetilde{\mathcal{A}}$ on fiber bundle
- **WP 2.3 (KS Lift)**: Connection on spinor coordinates
- **WP 3.1 (Killing Tensors)**: Use curvature to guide search for integrals

---

## Implementation Schedule

### Phase 1: Connection Computation (3 days)
- **Day 1**: Locked inertia tensor, shape space lifts
- **Day 2**: Connection coefficient computation
- **Day 3**: Validation (two-body limit, symmetries)

### Phase 2: Curvature Computation (2 days)
- **Day 4**: Numerical exterior derivative
- **Day 5**: Symbolic curvature (SymPy), validation

### Phase 3: Numerical Optimization (2 days)
- **Day 6**: Vectorization, caching
- **Day 7**: High-precision adaptive methods

### Phase 4: Visualization and Validation (2 days)
- **Day 8**: Vector field and heatmap plotting
- **Day 9**: Stokes' theorem validation

### Phase 5: Documentation (1 day)
- **Day 10**: API docs, technical report section, tutorial notebook

**Total**: 10 days (can be compressed to 8 with parallel work)

---

## Success Criteria

### Functional Requirements
- [ ] Connection $\mathcal{A}$ computable at arbitrary shape space points
- [ ] Curvature $\mathcal{F}$ computed with error < 1e-10 (validated via Stokes)
- [ ] Correct behavior in limiting cases (two-body, equal masses)
- [ ] Gauge invariance verified numerically

### Performance Requirements
- [ ] Connection evaluation: < 100 μs per point
- [ ] Curvature evaluation: < 1 ms per point
- [ ] Batch evaluation (1000 points): < 1 second

### Quality Requirements
- [ ] Test coverage > 95%
- [ ] Stokes' theorem validated to < 1e-10 error
- [ ] Publication-quality visualizations
- [ ] Complete API documentation

### Scientific Validation
- [ ] Confirm $|\mathcal{F}| > 0$ for generic three-body configurations
- [ ] Identify special configurations where $\mathcal{F} \approx 0$ (if any)
- [ ] Compare with known results from literature (if available)

---

## Risk Mitigation

### Risk 1: Numerical Instability Near Collisions
**Mitigation**:
- Use regularized coordinates (KS transform)
- Softened potentials for testing
- Adaptive precision escalation

### Risk 2: High Computational Cost
**Mitigation**:
- Implement caching for repeated queries
- Vectorize batch computations
- Profile and optimize hot paths

### Risk 3: Complexity of Symbolic Derivation
**Mitigation**:
- Start with planar, equal-mass case (maximal symmetry)
- Use computer algebra (SymPy) to automate derivations
- Validate symbolics against numerical results

### Risk 4: Visualization Challenges (High-Dimensional)
**Mitigation**:
- Fix some coordinates to create 2D slices
- Use multiple projections
- Interactive 3D plots with rotation

---

## References

### Geometric Mechanics
1. Marsden & Ratiu, *Introduction to Mechanics and Symmetry* (1999) - Chapter on connections
2. Littlejohn & Reinsch, "Gauge fields in the separation of rotations and internal motions" (1997)
3. Montgomery, "Gauge theory of the falling cat" (1993) - Pedagogical introduction

### Three-Body Problem Geometry
4. Saari & Hulkower, "On the manifolds of total collapse orbits and of completely parabolic orbits for the n-body problem" (1981)
5. McCord, Meyer, & Wang, "The integral manifolds of the three body problem" (2008)

### Numerical Methods
6. Hairer, Lubich, Wanner, *Geometric Numerical Integration* (2006) - Discrete exterior calculus
7. Desbrun et al., "Discrete Exterior Calculus" (2005) - Computational geometry

---

## Appendix: Coordinate System Choices

For this task, we primarily work in:

1. **Distance Coordinates**: $(r_{12}, r_{23}, r_{31})$
   - Pros: Gauge-invariant, symmetric for equal masses
   - Cons: Triangle inequality constraints, singular at collisions

2. **Oriented Triangle Coordinates**: Shape + orientation angle $\theta$
   - Pros: Clear geometric interpretation
   - Cons: Gauge-dependent (must fix orientation)

3. **Complex Shape Variable** (planar): $z = (r_3 - r_1)/(r_2 - r_1)$
   - Pros: Conformal structure, Möbius symmetry
   - Cons: Planar only, singular when bodies align

We implement connection in all three representations for cross-validation.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Next Review**: After Part A implementation
**Dependencies**: Task 2.1.1 Complete
