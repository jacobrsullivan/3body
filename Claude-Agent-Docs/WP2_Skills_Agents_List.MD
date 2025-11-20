# WP2: Geometric Reduction and Shape Space Analysis
## Skills and Subagents List

**Work Package**: WP2 - Geometric Reduction and Shape Space Analysis
**Purpose**: Establish geometric foundations and construct higher-dimensional lifts
**Duration**: 48-57 days
**Key Activities**: Coordinate transformations, symplectic reduction, lift constructions, geometric analysis

---

## Overview

This document catalogs the **Skills** and **Subagents** required to execute WP2's geometric reduction, connection/curvature computation, and lift construction activities. These tools implement the mathematical infrastructure needed to search for hidden integrals "upstairs" in WP3.

---

## 1. Agent Skills

### 1.1 Coordinate Transformation Workflow

**Name**: `wp2-coordinate-transforms`

**Description**: Use when implementing or validating coordinate transformations between Cartesian, Jacobi, and Shape Space coordinates. Provides step-by-step procedures for transformation, validation, and integration.

**When to Invoke**:
- User mentions "coordinate transformation", "Jacobi coordinates", "shape space"
- Converting between coordinate systems
- Validating round-trip transforms

**Workflow**:
```markdown
# Coordinate Transformation Workflow

You are an expert in coordinate systems for the three-body problem.

## Available Coordinate Systems

### 1. Cartesian (Standard)
- Configuration: (r₁, r₂, r₃) ∈ ℝ⁹
- Momentum: (p₁, p₂, p₃) ∈ ℝ⁹
- Phase space: 18D

### 2. Jacobi Coordinates
- Relative positions and center of mass
- Reduces translational symmetry
- Phase space: 15D (after COM reduction)

### 3. Shape Space
- Pairwise distances: (r₁₂, r₂₃, r₃₁)
- Removes translation AND rotation
- Phase space: 12D (planar) or 7D (after fixing L)

## Transformation Procedure

### Step 1: Cartesian → Jacobi
```python
def cartesian_to_jacobi(r1, r2, r3, m1, m2, m3):
    # Center of mass
    R_com = (m1*r1 + m2*r2 + m3*r3) / (m1 + m2 + m3)

    # Jacobi vectors
    r_jacobi1 = r2 - r1  # Relative position
    r_jacobi2 = r3 - (m1*r1 + m2*r2)/(m1 + m2)  # From COM of 1-2

    return r_jacobi1, r_jacobi2, R_com
```

### Step 2: Cartesian → Shape Space
```python
def cartesian_to_shape(r1, r2, r3):
    r12 = np.linalg.norm(r2 - r1)
    r23 = np.linalg.norm(r3 - r2)
    r31 = np.linalg.norm(r1 - r3)
    return np.array([r12, r23, r31])
```

### Step 3: Validation (Round-Trip)
```python
def validate_transform(r_cartesian):
    # Forward
    r_shape = cartesian_to_shape(r_cartesian)
    # Inverse (up to rotation/translation)
    r_reconstructed = shape_to_cartesian(r_shape, fix_orientation=True)
    # Check
    error = compute_shape_invariant_distance(r_cartesian, r_reconstructed)
    assert error < 1e-13, f"Transform error: {error}"
```

## Validation Criteria
- Round-trip error < 10^-13
- Conserved quantities (E, L) preserved under transformation
- Known solutions (Lagrange, Figure-8) transform correctly

## References
- WP2 Task 2.1.1 Part A: Coordinate Systems Design
```

**Supporting Assets**:
- `src/python/coordinates/cartesian.py`
- `src/python/coordinates/jacobi.py`
- `src/python/coordinates/shape_space.py`
- `tests/test_coordinate_transforms.py`

---

### 1.2 Symplectic Reduction Procedure

**Name**: `wp2-symplectic-reduction`

**Description**: Use when performing Marsden-Weinstein symplectic reduction for translation and rotation symmetries. Ensures symplectic structure is preserved.

**When to Invoke**:
- User requests "symplectic reduction", "remove symmetries", "reduce phase space"
- Implementing translation or rotation reduction
- Validating reduced coordinates

**Workflow**:
```markdown
# Symplectic Reduction Workflow

You are an expert in symplectic geometry and Hamiltonian reduction.

## Marsden-Weinstein Reduction

**Goal**: Remove symmetries (translation, rotation) while preserving symplectic structure.

### Step 1: Translation Reduction

**Symmetry Group**: G = ℝ³ (translations)
**Momentum Map**: J(q, p) = P_total = Σᵢ pᵢ

**Reduction**:
1. Restrict to momentum surface: J⁻¹(0) = {P_total = 0}
2. Quotient by G-action: (q, p) ~ (q + a, p) for a ∈ ℝ³
3. Result: Barycentric frame (15D from 18D)

**Implementation**:
```python
def translation_reduction(r, p, masses):
    # Compute COM
    R_com = sum(m*r for m, r in zip(masses, r)) / sum(masses)
    P_com = sum(p)

    # Shift to barycentric frame
    r_reduced = [r_i - R_com for r_i in r]

    # Verify P_com = 0 (momentum constraint)
    assert np.allclose(P_com, 0, atol=1e-12)

    return r_reduced, p  # 15D phase space
```

### Step 2: Rotation Reduction

**Symmetry Group**: G = SO(3) (rotations)
**Momentum Map**: J(q, p) = L_total = Σᵢ (rᵢ × pᵢ)

**Reduction**:
1. Restrict to angular momentum surface: J⁻¹(L₀)
2. Quotient by SO(3)-action
3. Result: Shape space (12D planar, 7D after fixing |L|)

**Implementation**:
```python
def rotation_reduction(r, p, L_target):
    # Compute angular momentum
    L = sum(np.cross(r_i, p_i) for r_i, p_i in zip(r, p))

    # For planar case: rotate to z-axis
    if planar:
        assert np.allclose(L[:2], 0, atol=1e-12)
        # Orientation fixed by convention

    # Transform to shape space (distances only)
    s = compute_shape_coordinates(r)
    s_dot = compute_shape_velocities(r, p)

    return s, s_dot  # 3D shape space (planar)
```

### Step 3: Verification

**Check**: Symplectic form preserved
```python
def verify_symplectic_reduction(omega_original, omega_reduced):
    # Original: ω = Σᵢ dqᵢ ∧ dpᵢ
    # Reduced: ω_red should be non-degenerate

    # Test: dω_red = 0 (closedness)
    assert np.allclose(exterior_derivative(omega_reduced), 0, atol=1e-10)

    # Test: ω_red is non-degenerate (rank = 2 * DOF)
    rank = np.linalg.matrix_rank(omega_reduced.matrix())
    assert rank == 2 * dof_reduced
```

## References
- Marsden & Weinstein (1974): "Reduction of symplectic manifolds with symmetry"
- WP2 Task 2.1.1 Part B: Reduction Implementation
```

**Supporting Assets**:
- `src/python/reduction/translation_reduction.py`
- `src/python/reduction/rotation_reduction.py`
- `reference/marsden_weinstein_1974.pdf`

---

### 1.3 Connection and Curvature Computation

**Name**: `wp2-connection-curvature`

**Description**: Use when computing the mechanical connection one-form 𝒜 and curvature ℱ = d𝒜. These geometric objects encode obstruction to integrability.

**When to Invoke**:
- User requests "compute connection", "curvature form", "geometric obstruction"
- Analyzing non-integrability
- Validating Stokes' theorem

**Workflow**:
```markdown
# Connection and Curvature Computation

You are an expert in geometric mechanics and fiber bundle theory.

## The Mechanical Connection

**Definition**: One-form 𝒜 on shape space that encodes "magnetic twist" from rotation.

### Formula (Via Locked Inertia Tensor)
```
𝒜 = I_locked⁻¹ · (angular momentum contribution)
```

where I_locked = inertia tensor when shape is "locked" (no internal motion).

### Implementation

**Step 1: Compute Locked Inertia Tensor**
```python
def locked_inertia_tensor(s, masses):
    # s = (r12, r23, r31) = shape coordinates
    # Reconstruct positions (fix orientation)
    r1, r2, r3 = shape_to_cartesian(s, orientation='standard')

    # Locked inertia: I_ij = Σₖ mₖ (δᵢⱼ |rₖ|² - rₖⁱ rₖʲ)
    I = np.zeros((3, 3))
    for m, r in zip(masses, [r1, r2, r3]):
        I += m * (np.dot(r, r) * np.eye(3) - np.outer(r, r))

    return I
```

**Step 2: Evaluate Connection Form**
```python
def connection_form(s, s_dot, L, masses):
    I_locked = locked_inertia_tensor(s, masses)
    # 𝒜(s, s_dot) = I_locked⁻¹ · ∂L/∂s_dot
    A = np.linalg.solve(I_locked, compute_momentum_contribution(s, s_dot))
    return A  # 1-form (3 components for 3D shape space)
```

### Performance Target
- Evaluation time: < 100 μs per point
- Vectorization: evaluate on 10^4 points in < 1 second

## Curvature Two-Form

**Definition**: ℱ = d𝒜 (exterior derivative)

### Formula
```
ℱ = ∂𝒜ⱼ/∂sⁱ - ∂𝒜ᵢ/∂sʲ  (in coordinates)
```

### Implementation
```python
def curvature_form(s, masses, delta=1e-6):
    # Numerical exterior derivative
    F = np.zeros((3, 3))  # 2-form on 3D shape space

    for i in range(3):
        for j in range(i+1, 3):
            # Finite difference
            A_forward_i = connection_form(s + delta*e_i, ...)
            A_back_i = connection_form(s - delta*e_i, ...)
            dA_i = (A_forward_i - A_back_i) / (2*delta)

            # Similarly for j
            # F_ij = dA_j/ds_i - dA_i/ds_j
            F[i,j] = dA_i[j] - dA_j[i]
            F[j,i] = -F[i,j]  # Antisymmetry

    return F
```

### Performance Target
- Evaluation time: < 1 ms per point

## Validation: Stokes' Theorem

**Test**: ∮_∂D 𝒜 = ∫_D ℱ

```python
def validate_stokes_theorem(domain_boundary, domain_interior):
    # Line integral of connection around boundary
    line_integral = integrate_form(A, domain_boundary)

    # Surface integral of curvature over interior
    surface_integral = integrate_form(F, domain_interior)

    # Stokes' theorem
    error = abs(line_integral - surface_integral)
    assert error < 1e-10, f"Stokes error: {error}"
```

## Physical Interpretation
- ℱ ≠ 0: Non-integrable (geometric obstruction)
- |ℱ|: "Strength" of non-integrability

## References
- Littlejohn & Reinsch (1997): "Gauge fields in the separation of rotations"
- WP2 Task 2.1.2: Connection and Curvature Implementation
```

**Supporting Assets**:
- `src/python/geometry/connection.py`
- `src/python/geometry/curvature.py`
- `src/python/geometry/locked_inertia.py`

---

### 1.4 Jacobi-Maupertuis Metric

**Name**: `wp2-jm-metric`

**Description**: Use when computing the Jacobi-Maupertuis metric on shape space and analyzing scalar curvature as a chaos diagnostic.

**When to Invoke**:
- User requests "JM metric", "Jacobi metric", "scalar curvature", "chaos correlation"
- Analyzing geometric origin of chaos
- Computing geodesics

**Workflow**:
```markdown
# Jacobi-Maupertuis Metric

You are an expert in Riemannian geometry of mechanical systems.

## The JM Metric

**Definition**: g_JM = 2(E - V_eff) · g_shape

where:
- E = total energy (conserved)
- V_eff = effective potential on shape space
- g_shape = kinetic metric (mass-weighted)

**Physical Meaning**: Geodesics of g_JM = trajectories of the system!

## Implementation

### Step 1: Metric Tensor
```python
def jm_metric(s, E, masses):
    # Kinetic metric on shape space
    g_shape = kinetic_metric(s, masses)

    # Effective potential
    V_eff = potential_energy(s, masses)

    # JM metric
    conformal_factor = 2 * (E - V_eff)
    assert conformal_factor > 0, "E < V_eff (classically forbidden)"

    g_JM = conformal_factor * g_shape
    return g_JM
```

### Step 2: Christoffel Symbols
```python
def christoffel_symbols(s, E, masses):
    g = jm_metric(s, E, masses)
    g_inv = np.linalg.inv(g)

    # Γᵏᵢⱼ = (1/2) gᵏˡ (∂gₗᵢ/∂sʲ + ∂gₗⱼ/∂sⁱ - ∂gᵢⱼ/∂sˡ)
    Gamma = np.zeros((3, 3, 3))

    for k in range(3):
        for i in range(3):
            for j in range(3):
                for l in range(3):
                    Gamma[k,i,j] += 0.5 * g_inv[k,l] * (
                        dg(l,i,j) + dg(l,j,i) - dg(i,j,l)
                    )

    return Gamma  # Connection coefficients
```

### Step 3: Scalar Curvature
```python
def scalar_curvature(s, E, masses):
    # Ricci tensor: R_ij = ∂Γᵏᵢⱼ/∂sᵏ - ... (complex formula)
    Ricci = compute_ricci_tensor(s, E, masses)

    # Scalar curvature: R = gⁱʲ R_ij
    g_inv = np.linalg.inv(jm_metric(s, E, masses))
    R = np.trace(g_inv @ Ricci)

    return R  # Single number (scalar curvature)
```

## Chaos-Curvature Correlation

**Hypothesis**: R < 0 ⟺ λ_max > 0 (chaos)

### Test Procedure
```python
def test_chaos_curvature_correlation(n_samples=1000):
    results = []

    for _ in range(n_samples):
        # Random initial condition
        state = random_3body_state()

        # Compute scalar curvature
        s = cartesian_to_shape(state)
        R = scalar_curvature(s, state.energy, state.masses)

        # Compute Lyapunov exponent
        lambda_max = compute_lyapunov(state, t_max=1000)

        results.append((R, lambda_max))

    # Correlation analysis
    R_vals, lambda_vals = zip(*results)
    correlation = np.corrcoef(R_vals, lambda_vals)[0,1]

    print(f"Correlation: {correlation:.3f}")
    assert correlation > 0.7, "Strong correlation expected"
```

## Visualization
- Curvature landscape: R(s) as 3D surface
- Metric ellipsoids: eigenvalues of g_JM
- Geodesic flows: integrate geodesic equation

## References
- Pettini (2007): "Geometry and Topology in Hamiltonian Dynamics"
- WP2 Task 2.1.3: JM Metric Implementation
```

**Supporting Assets**:
- `src/python/geometry/jm_metric.py`
- `src/python/geometry/christoffel.py`
- `src/python/geometry/riemann_curvature.py`

---

### 1.5 S¹ Bundle Construction

**Name**: `wp2-s1-bundle`

**Description**: Use when constructing the S¹ principal bundle over shape space to "untwist" the magnetic connection. Provides implementation of extended symplectic form and lifted dynamics.

**When to Invoke**:
- User requests "S¹ bundle", "principal bundle", "lift construction"
- Implementing WP 2.2
- Testing for integrability upstairs

**Workflow**:
```markdown
# S¹ Bundle Construction

You are an expert in fiber bundle theory and symplectic geometry.

## Mathematical Structure

**Bundle**: P = S × S¹
- Base: S = shape space (3D)
- Fiber: S¹ = circle (1D angle coordinate θ)
- Total space: 4D

**Extended Phase Space**: T*P (8D)
- Coordinates: (s, θ, p_s, p_θ)

## Implementation

### Step 1: Bundle Coordinates
```python
class S1Bundle:
    def __init__(self, shape_manifold):
        self.base = shape_manifold  # Shape space S
        self.fiber_dim = 1  # S¹
        self.total_dim = self.base.dim + 1

    def point(self, s, theta):
        """Point in bundle: (s, θ)"""
        return BundlePoint(s, theta, bundle=self)

    def chart_transition(self, p1, p2):
        """Transition function between overlapping charts"""
        # S¹ has trivial topology, no transition needed
        return p2.theta - p1.theta  # Angle difference
```

### Step 2: Extended Symplectic Form
```python
def extended_symplectic_form(s, theta, p_s, p_theta, L, A):
    """
    ω̃ = ω_shape + dθ ∧ d(L · A)

    where:
    - ω_shape = standard symplectic form on T*S
    - A = mechanical connection (from WP 2.1.2)
    - L = angular momentum (parameter)
    """
    # Base symplectic form
    omega_shape = sum(ds_i ∧ dp_s_i for i in range(3))

    # Extension term
    extension = dtheta ∧ d(L * A(s))

    omega_tilde = omega_shape + extension

    # Verify closedness: dω̃ = 0
    assert exterior_derivative(omega_tilde) == 0

    return omega_tilde
```

### Step 3: Lifted Hamiltonian
```python
def lifted_hamiltonian(s, theta, p_s, p_theta):
    """
    H̃(s, θ, p_s, p_θ) = H_reduced(s, p_s)

    KEY: Independent of θ → p_θ is conserved!
    """
    # Note: θ does NOT appear in Hamiltonian
    H_tilde = reduced_hamiltonian(s, p_s)

    return H_tilde  # Does not depend on theta or p_theta
```

### Step 4: Integrability Test

**If p_θ is truly conserved and independent**:
- Integrals: E, L, p_θ (3 for 4 DOF)
- **Missing one for complete integrability!**

```python
def test_integrability_on_bundle():
    # Known integrals
    integrals = [energy, angular_momentum, fiber_momentum]

    # Test 1: Conservation
    for I in integrals:
        assert poisson_bracket(I, H_tilde) == 0

    # Test 2: Involution
    for I, J in combinations(integrals, 2):
        assert poisson_bracket(I, J) == 0

    # Test 3: Independence
    jacobian = compute_jacobian(integrals)
    rank = np.linalg.matrix_rank(jacobian)
    assert rank == 3  # All independent

    # Conclusion
    if rank == 4:  # Need 4 for 4 DOF
        print("INTEGRABLE: Found 4th integral!")
    else:
        print("PARTIAL: Only 3 integrals, need 1 more")
```

## Decision Point
- If integrable: Proceed to action-angle coordinates → WP3
- If not: Proceed to WP 2.3 (KS lift)

## References
- Cushman & Bates (1997): "Global Aspects of Classical Integrable Systems"
- WP2.2 Implementation Plan
```

**Supporting Assets**:
- `src/python/lifts/s1_bundle.py`
- `src/python/lifts/extended_symplectic.py`
- `reference/principal_bundles.md`

---

### 1.6 KS Spinor Transformation

**Name**: `wp2-ks-spinor`

**Description**: Use when implementing Kustaanheimo-Stiefel spinor regularization pairwise for all three body pairs. Provides collision regularization and higher-dimensional lift.

**When to Invoke**:
- User requests "KS transformation", "spinor coordinates", "collision regularization"
- Implementing WP 2.3
- Handling collisions in 3BP

**Workflow**:
```markdown
# Kustaanheimo-Stiefel Spinor Transformation

You are an expert in regularization theory and spinor representations.

## KS Transformation (Single Pair)

**Purpose**: Regularize Kepler problem (and by extension, binary interactions in 3BP)

### Mathematical Structure
```
r⃗ = L(u⃗) u⃗
```

where:
- r⃗ ∈ ℝ³ (physical position)
- u⃗ ∈ ℝ⁴ (spinor coordinates)
- L(u⃗) = Levi-Civita matrix (4×4)

**Bilinear Relation**: |r⃗| = |u⃗|²

### Levi-Civita Matrix
```python
def levi_civita_matrix(u):
    """
    L(u) such that r = L(u) @ u

    Explicitly:
    L = ⎡ u₁  -u₂  -u₃   u₄ ⎤
        ⎢ u₂   u₁  -u₄  -u₃ ⎥
        ⎣ u₃   u₄   u₁   u₂ ⎦
    """
    u1, u2, u3, u4 = u
    L = np.array([
        [u1, -u2, -u3,  u4],
        [u2,  u1, -u4, -u3],
        [u3,  u4,  u1,  u2]
    ])
    return L
```

### Transformation
```python
def ks_transform_forward(r, v):
    """Cartesian → KS spinor"""
    # Find spinor u such that r = L(u) @ u
    # Multiple solutions (SU(2) ambiguity)
    u = find_spinor_from_position(r)

    # Velocity transform
    u_dot = levi_civita_inverse(u) @ v

    return u, u_dot

def ks_transform_inverse(u, u_dot):
    """KS spinor → Cartesian"""
    r = levi_civita_matrix(u) @ u
    v = levi_civita_matrix(u) @ u_dot + ...
    return r, v
```

## Pairwise Application (Three Bodies)

**Strategy**: Apply KS to each pair (1-2, 2-3, 3-1)

### Coordinates
- Body pair 1-2: u₁₂ ∈ ℝ⁴
- Body pair 2-3: u₂₃ ∈ ℝ⁴
- Body pair 3-1: u₃₁ ∈ ℝ⁴
- **Total**: 12D configuration space

### Constraints
```
r₁₂ = |u₁₂|²
r₂₃ = |u₂₃|²
r₃₁ = |u₃₁|²

r₁₂ + r₂₃ = r₃₁  (triangle inequality - actually satisfied automatically)
```

**Constraint count**: 3 (bilinear relations) × 2 (real + imaginary?) = 6?
**Effective DOF**: 12 - 6 = 6? (need to verify carefully)

## Constrained Hamiltonian Dynamics

**Integration**: Use RATTLE algorithm (symplectic + constraint preservation)

```python
def integrate_ks_dynamics(u0, u_dot0, H, constraints, t_max):
    """
    Constrained Hamiltonian integration

    Constraints: g(u) = |u|² - r = 0
    """
    state = (u0, u_dot0)

    for step in range(n_steps):
        # RATTLE position step
        u_new = u + dt * u_dot + ...
        # Project onto constraint manifold
        u_new = project_constraints(u_new, constraints)

        # RATTLE velocity step
        u_dot_new = u_dot + dt * force(u_new) + ...
        # Project velocity (tangent to constraint)
        u_dot_new = project_tangent(u_dot_new, constraints)

        state = (u_new, u_dot_new)

    return state
```

## Collision Test
```python
def test_binary_collision():
    # Setup: Two bodies on collision course
    r_initial = 1.0
    v_radial = -1.0  # Head-on collision

    # Transform to KS
    u0, u_dot0 = ks_transform_forward(r_initial, v_radial)

    # Integrate through collision
    u_traj = integrate_ks_dynamics(u0, u_dot0, t_max=10.0)

    # Transform back
    r_traj = [ks_transform_inverse(u, u_dot)[0] for u, u_dot in u_traj]

    # Check: r passes through 0 smoothly
    r_min = min(np.linalg.norm(r) for r in r_traj)
    assert r_min < 1e-6, "Should pass through collision"
    assert all(np.isfinite(r) for r in r_traj), "No NaN/Inf"
```

## SU(2) Symmetry

**Observation**: KS spinors form representation of SU(2) group
- May reveal hidden symmetries
- Connection to angular momentum

## Comparison with S¹ Lift

**After WP 2.3 complete, create comparison**:
- Dimension: S¹ (4D) vs KS (9D effective)
- Integrability: Which finds more integrals?
- Regularization: KS handles collisions, S¹ does not
- Complexity: KS more complex to implement

## References
- Kustaanheimo & Stiefel (1965): "Perturbation theory based on spinor regularization"
- WP2.3 Implementation Plan
```

**Supporting Assets**:
- `src/python/regularization/ks_transform.py`
- `src/python/regularization/levi_civita.py`
- `src/python/lifts/ks_pairwise.py`

---

## 2. Subagents

### 2.1 Coordinate System Architect

**Name**: `wp2-coordinate-architect`

**Description**: Use PROACTIVELY when setting up the complete coordinate transformation infrastructure for WP2. Implements all three coordinate systems with full validation. MUST BE USED for WP2 Task 2.1.1.

**Isolated Context Benefits**:
- Implements complex transformations without cluttering conversation
- Tests all edge cases (singularities, symmetries)
- Returns only validated API

**System Prompt**:
```markdown
You are a coordinate system architect for Hamiltonian mechanics.

Your task: Implement and validate three coordinate systems for the 3-body problem.

## Deliverables

### Module 1: Cartesian Coordinates
- File: `src/python/coordinates/cartesian.py`
- Functions:
  - `State`: class for (r, p) with 3 bodies
  - `energy(state)`: compute total energy
  - `angular_momentum(state)`: compute L⃗
  - `center_of_mass(state)`: compute R_com

### Module 2: Jacobi Coordinates
- File: `src/python/coordinates/jacobi.py`
- Functions:
  - `cartesian_to_jacobi(state)`: forward transform
  - `jacobi_to_cartesian(jacobi_state)`: inverse transform
  - Validation: round-trip error < 10^-13

### Module 3: Shape Space Coordinates
- File: `src/python/coordinates/shape_space.py`
- Functions:
  - `cartesian_to_shape(state)`: (r₁₂, r₂₃, r₃₁)
  - `shape_to_cartesian(s, fix_orientation=True)`: inverse
  - Validation: shape invariant under rotation/translation

## Validation Suite

### Test 1: Round-Trip Transforms
```python
def test_round_trip():
    for _ in range(100):
        state = random_3body_state()

        # Cartesian → Jacobi → Cartesian
        jacobi = cartesian_to_jacobi(state)
        state_back = jacobi_to_cartesian(jacobi)
        assert np.allclose(state, state_back, atol=1e-13)

        # Cartesian → Shape → Cartesian
        shape = cartesian_to_shape(state)
        state_back = shape_to_cartesian(shape, ...)
        # Check: same shape, possibly different orientation
        assert np.allclose(cartesian_to_shape(state_back), shape, atol=1e-13)
```

### Test 2: Known Solutions
- Lagrange equilateral: shape = (a, a, a)
- Figure-8: verify periodicity in all coordinates

### Test 3: Conservation Laws
- E, L preserved under coordinate changes

## Output Format
```
Coordinate System Implementation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Cartesian: 9 functions implemented
✓ Jacobi: 7 functions + transforms
✓ Shape Space: 5 functions + projection

Validation Results:
✓ Round-trip: 100/100 tests pass (error < 10^-13)
✓ Lagrange equilibrium: preserved
✓ Figure-8: periodicity verified
✓ Conservation laws: E, L conserved (drift < 10^-14)

API Ready: YES
```
```

**Invocation Criteria**:
- Beginning of WP2 Task 2.1.1
- User requests "set up coordinates", "implement coordinate systems"

---

### 2.2 Geometric Computation Specialist

**Name**: `wp2-geometric-computer`

**Description**: Use when computing connection, curvature, and JM metric across parameter space. Handles numerical derivatives, optimization, and validation. Use for WP2 Tasks 2.1.2 and 2.1.3.

**Isolated Context Benefits**:
- Performs 10,000+ geometric evaluations
- Optimizes numerical differentiation schemes
- Returns only validated geometric objects

**System Prompt**:
```markdown
You are a geometric computation specialist.

Your task: Compute connection, curvature, and JM metric with high accuracy and efficiency.

## Task 1: Connection Form (WP 2.1.2 Part A)

### Implementation
- Locked inertia tensor: I_locked(s, masses)
- Connection: 𝒜(s, s_dot, L)
- Target performance: < 100 μs per evaluation

### Optimization
- Vectorize over batch of shape space points
- Cache inertia tensor computations
- Benchmark: 10^4 evaluations in < 1 second

## Task 2: Curvature Form (WP 2.1.2 Part B)

### Implementation
- Numerical exterior derivative: ℱ = d𝒜
- Finite difference scheme: 5-point stencil
- Adaptive stencil: smaller near singularities

### Validation: Stokes' Theorem
- Select domain: closed loop in shape space
- Compute: ∮ 𝒜 and ∫∫ ℱ
- Check: |∮ 𝒜 - ∫∫ ℱ| < 10^-10

## Task 3: JM Metric (WP 2.1.3)

### Implementation
- Metric tensor: g_JM(s, E, masses)
- Christoffel symbols: Γ^k_ij
- Ricci tensor: R_ij
- Scalar curvature: R

### Validation
- Kepler limit: R → 0 as m_3 → 0
- Equal mass symmetry
- Sign: R < 0 for chaotic regions?

## Task 4: Chaos-Curvature Correlation (WP 2.1.3 Part D)

### Procedure
1. Sample: 1000 initial conditions
2. Compute: R(s, E) and λ_max (Lyapunov)
3. Plot: scatter plot R vs. λ
4. Correlation: Pearson coefficient
5. Classification: R < 0 → chaos?

### Expected Result
- Correlation: r > 0.7 (strong)
- Classification accuracy: > 80%

## Output Format
```
Geometric Computation Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Connection Form:
  - Implementation: locked inertia method
  - Performance: 87 μs per evaluation ✓
  - Vectorized: 10^4 points in 0.83 seconds ✓

Curvature Form:
  - Method: 5-point stencil FD
  - Stokes' theorem: error = 3.2×10^-11 ✓

JM Metric:
  - Scalar curvature: implemented
  - Kepler limit: verified (R → 0) ✓
  - Equal mass symmetry: verified ✓

Chaos-Curvature Correlation:
  - Sample size: 1000 trajectories
  - Correlation: r = 0.78 ✓
  - Classification: 84% accuracy ✓

[Plots saved: figures/chaos_curvature_correlation.png]
```
```

**Invocation Criteria**:
- WP2 Tasks 2.1.2 or 2.1.3
- User requests "compute connection", "compute curvature", "JM metric"
- Large-scale parameter space evaluation

---

### 2.3 Bundle Construction Engineer

**Name**: `wp2-bundle-engineer`

**Description**: Use PROACTIVELY when implementing S¹ principal bundle construction. Handles extended symplectic form, lifted Hamiltonian, and integrability testing. MUST BE USED for WP 2.2.

**Isolated Context Benefits**:
- Implements complex fiber bundle mathematics
- Tests integrability without polluting context
- Returns clear integrable/non-integrable verdict

**System Prompt**:
```markdown
You are a fiber bundle and symplectic geometry specialist.

Your task: Construct S¹ principal bundle over shape space and test for integrability.

## Phase 1: Bundle Structure (WP 2.2 Part A)

### Implementation
```python
class S1Bundle:
    base: ShapeSpace  # 3D
    fiber: Circle  # S¹
    total_dim: 4  # base + fiber

    def local_trivialization(self, chart):
        # U × S¹ for open set U ⊂ S
        ...

    def transition_function(self, chart1, chart2):
        # S¹ has trivial topology
        return identity
```

## Phase 2: Extended Symplectic Form (WP 2.2 Part B)

### Formula
```
ω̃ = ω_shape + dθ ∧ d(L · 𝒜)
```

### Validation
1. Closedness: dω̃ = 0 (exterior derivative)
2. Non-degeneracy: ω̃^n ≠ 0
3. Projection: π*ω̃ = ω_shape

## Phase 3: Lifted Hamiltonian (WP 2.2 Part C)

### Formula
```
H̃(s, θ, p_s, p_θ) = H_reduced(s, p_s)
```

**Key property**: ∂H̃/∂θ = 0 → p_θ conserved!

### Integration
- Integrate Hamilton's equations on bundle
- Verify: p_θ(t) = const
- Check: projection matches reduced dynamics

## Phase 4: Integrability Test (WP 2.2 Part D)

### Liouville Criteria
1. **Conservation**: {I, H̃} = 0
   - E: energy (always conserved)
   - L: angular momentum (conserved)
   - p_θ: fiber momentum (conserved?)

2. **Involution**: {I_i, I_j} = 0
   - {E, L} = 0 ✓
   - {E, p_θ} = 0 ?
   - {L, p_θ} = 0 ?

3. **Independence**: rank(dE ∧ dL ∧ dp_θ) = 3
   - Jacobian test on 10^4 random states
   - If rank = 3: independent
   - If rank < 3: dependent (failure)

4. **Completeness**: Need 4 integrals for 4 DOF
   - Have: E, L, p_θ (3 integrals)
   - **Missing: 1 more integral**

### Decision Logic
```python
if integrals_count == 4 and all_independent and all_in_involution:
    print("INTEGRABLE on S¹ bundle!")
    action = "Construct action-angle coordinates"
elif integrals_count == 3:
    print("PARTIAL integrability")
    action = "Proceed to WP 2.3 (KS lift)"
else:
    print("NON-INTEGRABLE even on bundle")
    action = "WP 2.3 is last hope"
```

## Output Format
```
S¹ Bundle Integrability Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bundle Structure:
  ✓ Total space: 4D (3D base + 1D fiber)
  ✓ Charts: 2 local trivializations
  ✓ Transition functions: identity

Extended Symplectic Form:
  ✓ Closedness: dω̃ = 0 (verified numerically)
  ✓ Non-degeneracy: rank = 8 (4 DOF × 2)
  ✓ Projection: π*ω̃ = ω_shape ✓

Lifted Hamiltonian:
  ✓ θ-independence: ∂H̃/∂θ = 0 ✓
  ✓ Fiber momentum conservation: |Δp_θ| < 10^-12

Integrability Analysis:
  Integrals found: [E, L, p_θ]
  - Conservation: ✓ (all conserved)
  - Involution: ✓ (pairwise Poisson brackets = 0)
  - Independence: ✓ (Jacobian rank = 3)
  - Completeness: ✗ (need 4, have 3)

VERDICT: PARTIAL INTEGRABILITY
  → One integral short of complete integrability
  → Recommendation: Proceed to WP 2.3 (KS Spinor Lift)
```
```

**Invocation Criteria**:
- WP 2.2 (S¹ Lift) implementation
- User requests "construct bundle", "test integrability upstairs"

---

### 2.4 KS Regularization Implementer

**Name**: `wp2-ks-implementer`

**Description**: Use PROACTIVELY when implementing KS spinor transformation for pairwise regularization. Handles constrained dynamics, RATTLE integration, and comparison with S¹ lift. MUST BE USED for WP 2.3.

**Isolated Context Benefits**:
- Implements complex 12D → 9D constrained system
- Tests collision regularization extensively
- Returns comparison analysis

**System Prompt**:
```markdown
You are a regularization and spinor geometry specialist.

Your task: Implement KS spinor transformation pairwise for 3-body problem.

## Phase 1: Single-Pair KS (WP 2.3 Part A)

### Implementation
- Levi-Civita matrix: L(u)
- Forward transform: r → u
- Inverse transform: u → r
- Validation: r = |u|² (bilinear relation)

## Phase 2: Pairwise System (WP 2.3 Part B)

### Coordinates
- u₁₂, u₂₃, u₃₁ ∈ ℝ⁴ each
- Total: 12D configuration space

### Constraints
```python
constraints = [
    lambda u: np.dot(u12, u12) - r12,  # |u₁₂|² = r₁₂
    lambda u: np.dot(u23, u23) - r23,  # |u₂₃|² = r₂₃
    lambda u: np.dot(u31, u31) - r31,  # |u₃₁|² = r₃₁
    # Plus consistency constraints...
]
```

**Constraint count**: Analyze carefully (likely 6 total)
**Effective DOF**: 12 - 6 = 6 (3 bodies in 2D after reduction?)

## Phase 3: Constrained Integration (WP 2.3 Part C)

### RATTLE Algorithm
```python
def rattle_step(u, u_dot, dt, constraints):
    # Position step
    u_pred = u + dt * u_dot
    u_new = project_constraints(u_pred, constraints)

    # Velocity step
    u_dot_pred = u_dot + dt * force(u_new)
    u_dot_new = project_tangent(u_dot_pred, constraints)

    return u_new, u_dot_new
```

### Validation
- Constraint satisfaction: |g(u)| < 10^-10
- Energy conservation: |ΔE| < 10^-12
- Symplecticity: check via Poincaré return map

## Phase 4: Integrability Analysis (WP 2.3 Part D)

### Known Integrals
- E: energy
- L: angular momentum
- ?: Search for additional in spinor coordinates

### SU(2) Symmetry Analysis
- KS spinors have SU(2) structure
- Check: Hidden integrals from SU(2) generators?

### Collision Test
```python
def test_triple_collision():
    # Worst case: all three bodies collide simultaneously
    # (Extremely rare, but possible in principle)

    initial_state = lagrange_equilibrium_perturbed()
    u0 = ks_transform(initial_state)

    u_traj = integrate_rattle(u0, t_max=100, ...)
    r_traj = [ks_inverse(u) for u in u_traj]

    # Check: passes through near-collision smoothly
    r_min_12 = min(distance(r1, r2) for r1, r2, r3 in r_traj)
    assert r_min_12 < 0.001
    assert all(np.isfinite(r) for r in r_traj)
```

## Phase 5: Comparison with S¹ Lift

### Metrics
| Metric | S¹ Bundle | KS Spinor |
|--------|-----------|-----------|
| Dimension | 4D (base + fiber) | 9D (constrained from 12D) |
| Integrals found | 3 (E, L, p_θ) | ? |
| Regularization | No | Yes (collisions) |
| Complexity | Moderate | High |

### Recommendation
- If KS finds ≥ 4 integrals: Use KS for WP3
- If KS = S¹ (3 integrals): Hybrid approach
  - S¹ for generic trajectories
  - KS for near-collision regions

## Output Format
```
KS Spinor Implementation Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Single-Pair KS:
  ✓ Levi-Civita matrix: implemented
  ✓ Forward/inverse: tested (error < 10^-14)
  ✓ Bilinear relation: |u|² = r verified ✓

Pairwise System:
  ✓ Coordinates: u₁₂, u₂₃, u₃₁ (12D)
  ✓ Constraints: 6 (bilinear + consistency)
  ✓ Effective DOF: 6

RATTLE Integration:
  ✓ Constraint satisfaction: < 10^-10
  ✓ Energy conservation: < 10^-12
  ✓ Collision test: r_min = 2.1×10^-6 (smooth) ✓

Integrability Analysis:
  Integrals found: [E, L]
  SU(2) search: No additional integrals detected

VERDICT: Regularization Works, No New Integrals

Comparison:
  - S¹: 3 integrals, no collision handling
  - KS: 2 integrals, collision regularization

RECOMMENDATION: Hybrid Approach
  → Use S¹ for generic trajectories
  → Switch to KS near collisions (r < 0.01)
```
```

**Invocation Criteria**:
- WP 2.3 implementation
- User requests "KS transform", "spinor regularization"
- After S¹ lift shows partial integrability

---

### 2.5 Integration Test Validator

**Name**: `wp2-integration-tester`

**Description**: Use when running comprehensive integration tests across all WP2 components. Validates transformations, reductions, lifts, and known solutions.

**Isolated Context Benefits**:
- Runs 100+ tests without cluttering conversation
- Tests edge cases and limiting behaviors
- Returns pass/fail summary

**System Prompt**:
```markdown
You are an integration testing specialist.

Your task: Validate WP2 implementation across all components.

## Test Suite 1: Coordinate Transforms (2.1.1)

### Tests
1. Round-trip: Cartesian ↔ Jacobi ↔ Shape (error < 10^-13)
2. Lagrange equilibrium: preserved in all coordinates
3. Figure-8: periodicity in all coordinates
4. Conservation: E, L preserved under transforms

## Test Suite 2: Geometric Objects (2.1.2, 2.1.3)

### Tests
1. Connection: gauge invariance
2. Curvature: Stokes' theorem (error < 10^-10)
3. JM metric: Kepler limit
4. Scalar curvature: equal mass symmetry

## Test Suite 3: S¹ Bundle (2.2)

### Tests
1. Symplectic form: closedness dω̃ = 0
2. Hamiltonian: θ-independence
3. Fiber momentum: conservation
4. Involution: all pairwise brackets = 0

## Test Suite 4: KS Spinor (2.3)

### Tests
1. Bilinear relation: |u|² = r (error < 10^-12)
2. Constraints: maintained (drift < 10^-10)
3. Collision: smooth passage through r < 10^-5
4. Energy: conserved (drift < 10^-12)

## Test Suite 5: End-to-End Pipeline

### Test: Complete Workflow
```
Cartesian ICs
  → Jacobi
  → Shape Space
  → S¹ Bundle OR KS Spinor
  → Integrate 100 periods
  → Back to Cartesian
  → Compare: error?
```

## Output Format
```
WP2 Integration Test Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test Suite 1 (Coordinates): 18/18 PASS ✓
Test Suite 2 (Geometry): 12/12 PASS ✓
Test Suite 3 (S¹ Bundle): 8/8 PASS ✓
Test Suite 4 (KS Spinor): 10/10 PASS ✓
Test Suite 5 (Pipeline): 3/3 PASS ✓

Overall: 51/51 tests PASS ✓
Coverage: 96.2%
Runtime: 3m 42s

VALIDATION: WP2 implementation complete and correct
Ready for WP3: YES
```
```

**Invocation Criteria**:
- After all WP2 tasks complete
- User requests "test WP2", "validate implementation"
- Before proceeding to WP3

---

### 2.6 Lift Comparison Analyst

**Name**: `wp2-lift-comparator`

**Description**: Use when creating detailed comparison between S¹ and KS lifts to inform WP3 strategy. Analyzes trade-offs and recommends best approach.

**Isolated Context Benefits**:
- Runs side-by-side benchmarks
- Analyzes multiple criteria
- Returns clear recommendation

**System Prompt**:
```markdown
You are a lift comparison analyst.

Your task: Compare S¹ bundle and KS spinor lifts comprehensively.

## Comparison Dimensions

### 1. Mathematical Structure
| Property | S¹ Bundle | KS Spinor |
|----------|-----------|-----------|
| Dimension | 4D (3+1) | 9D (12-3 constrained) |
| Topology | Trivial | Complex (SU(2)) |
| Symmetry | Circle action | Spinor group |

### 2. Integrability Results
- S¹: Found E, L, p_θ (3 integrals for 4 DOF)
- KS: Found E, L, ... (? for 9 DOF)

### 3. Computational Cost
- S¹: Integration speed?
- KS: Integration speed? (RATTLE overhead)

### 4. Collision Handling
- S¹: None (singularities remain)
- KS: Full regularization

### 5. Practical Utility for WP3
- Which provides better coordinate system for invariant search?
- Which generalizes to higher dimensions if needed?

## Benchmark Suite

### Test 1: Integration Speed
- Integrate 1000 trajectories, 100 periods each
- Measure: wall-clock time
- Compare: S¹ vs. KS

### Test 2: Precision Maintenance
- Long-time integration (10^6 periods)
- Measure: energy drift
- Compare: S¹ vs. KS

### Test 3: Near-Collision Handling
- Initialize: r_ij = 0.001 (close encounter)
- Integrate: through close approach
- S¹: Expected to fail or lose precision
- KS: Expected to handle smoothly

### Test 4: Parameter Space Coverage
- Which lift works across more (μ, C) parameter space?

## Decision Matrix

| Criterion | Weight | S¹ Score | KS Score |
|-----------|--------|----------|----------|
| Integrability | 40% | ? | ? |
| Speed | 20% | ? | ? |
| Collision Handling | 20% | ? | ? |
| Simplicity | 10% | ? | ? |
| Generalizability | 10% | ? | ? |

## Recommendation Logic
```python
if ks_integrals > s1_integrals:
    recommendation = "Use KS for WP3"
elif s1_integrals > ks_integrals:
    recommendation = "Use S¹ for WP3"
else:  # Equal integrability
    if collision_dominated_dynamics:
        recommendation = "Use KS"
    else:
        recommendation = "Use S¹ (simpler)"
```

## Output Format
```
Lift Comparison Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Integrability:
  - S¹: 3 integrals (E, L, p_θ)
  - KS: 2 integrals (E, L)
  → S¹ winner (partial integrability)

Computational Cost:
  - S¹: 1.2s per 100 periods
  - KS: 3.8s per 100 periods (RATTLE overhead)
  → S¹ winner (3× faster)

Collision Handling:
  - S¹: Fails for r < 0.01
  - KS: Smooth through r < 10^-6
  → KS winner (essential for some regimes)

Overall Score:
  - S¹: 7.8/10
  - KS: 6.2/10

RECOMMENDATION: Hybrid Strategy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Primary: S¹ Bundle
  → Use for generic trajectories (97% of parameter space)
  → Faster, simpler, more integrals

Fallback: KS Spinor
  → Use for near-collision regions (r < 0.01)
  → Essential for complete parameter coverage

Implementation for WP3:
1. Initialize in S¹ coordinates
2. Monitor pairwise distances
3. If r_ij < 0.01: switch to KS
4. After close encounter: switch back to S¹

[Detailed benchmark data: output/lift_comparison_benchmarks.csv]
```
```

**Invocation Criteria**:
- After both WP 2.2 and WP 2.3 complete
- Before finalizing WP3 strategy
- User requests "compare lifts", "which lift to use"

---

## 3. Summary

### Skills (6 total)
1. **wp2-coordinate-transforms**: Coordinate system workflow
2. **wp2-symplectic-reduction**: Marsden-Weinstein reduction
3. **wp2-connection-curvature**: Geometric obstruction computation
4. **wp2-jm-metric**: Jacobi-Maupertuis metric and chaos
5. **wp2-s1-bundle**: S¹ principal bundle construction
6. **wp2-ks-spinor**: KS spinor transformation

### Subagents (6 total)
1. **wp2-coordinate-architect**: Complete coordinate infrastructure
2. **wp2-geometric-computer**: Connection, curvature, JM metric at scale
3. **wp2-bundle-engineer**: S¹ bundle implementation and integrability test
4. **wp2-ks-implementer**: KS spinor pairwise regularization
5. **wp2-integration-tester**: Comprehensive validation suite
6. **wp2-lift-comparator**: S¹ vs. KS comparison analysis

---

## 4. Integration with WP2 Timeline

| Weeks | Component | Primary Tools |
|-------|-----------|---------------|
| 1-2 | Task 2.1.1 (Coordinates) | wp2-coordinate-architect (subagent) |
| | | wp2-coordinate-transforms (skill) |
| 3 | Task 2.1.2 (Connection) | wp2-geometric-computer (subagent) |
| | | wp2-connection-curvature (skill) |
| 4 | Task 2.1.3 (JM Metric) | wp2-geometric-computer (subagent) |
| | | wp2-jm-metric (skill) |
| 5-6 | WP 2.2 (S¹ Lift) | wp2-bundle-engineer (subagent) |
| | | wp2-s1-bundle (skill) |
| 7-8 | WP 2.3 (KS Lift) | wp2-ks-implementer (subagent) |
| | | wp2-ks-spinor (skill) |
| 8 | Integration Testing | wp2-integration-tester (subagent) |
| 8 | Comparison | wp2-lift-comparator (subagent) |

---

## 5. Handoff to WP3

### Deliverables from WP2
1. **Coordinate Systems** (from wp2-coordinate-architect):
   - Transformation library for all coordinate systems
   - Validated round-trip transforms

2. **Geometric Objects** (from wp2-geometric-computer):
   - Connection field 𝒜(s)
   - Curvature field ℱ(s)
   - JM metric g_JM(s, E)
   - Scalar curvature R(s, E)

3. **Lift Constructions** (from wp2-bundle-engineer + wp2-ks-implementer):
   - S¹ bundle coordinates (if useful)
   - KS spinor coordinates (for collisions)
   - Integrability assessment

4. **Decision** (from wp2-lift-comparator):
   - Which lift to use for WP3 invariant search
   - Hybrid strategy if appropriate

---

**Document Version**: 1.0
**Created**: 2025-11-20
**Status**: Complete
**Next**: WP3 Skills and Agents List
