# Mechanical Connection Theory

Mathematical foundations for the mechanical connection in reduced three-body dynamics.

## Table of Contents

1. [Principal Bundle Structure](#principal-bundle-structure)
2. [Mechanical Connection Definition](#mechanical-connection-definition)
3. [Locked Inertia Tensor](#locked-inertia-tensor)
4. [Connection Formula](#connection-formula)
5. [Curvature Computation](#curvature-computation)
6. [Physical Interpretation](#physical-interpretation)
7. [Implementation Details](#implementation-details)

---

## Principal Bundle Structure

### Configuration Space as Bundle

The three-body configuration space (after COM reduction) has the structure of a principal SO(3) bundle:

```
π: Q → S
Q = configurations (positions of 3 bodies, COM = 0)
S = shape space (quotient by rotations)
Fiber = SO(3) (rotations)
```

For planar motion, this reduces to an S¹ bundle:
```
π: Q_planar → S_planar
Fiber = SO(2) ≅ S¹
```

### Coordinates

**Full configuration**: (r₁, r₂, r₃) with constraint Σmᵢrᵢ = 0

**Shape coordinates**: (r₁₂, r₂₃, r₃₁) = pairwise distances

**Fiber coordinate**: θ ∈ SO(2) (overall rotation angle for planar)

---

## Mechanical Connection Definition

### General Definition

A connection on a principal G-bundle is a g-valued 1-form A satisfying:
1. A(ξ_Q) = ξ for all ξ ∈ g (reproduces Lie algebra generators)
2. R_g* A = Ad_{g⁻¹} A (equivariance under right action)

### Mechanical Connection

For mechanical systems, we use the **mechanical** (or **locking**) connection:

```
A(s) = I(s)⁻¹ · J_fiber
```

where:
- I(s) = locked inertia tensor at shape s
- J_fiber = momentum in fiber direction

The contraction with a shape velocity gives:

```
⟨A(s), ṡ⟩ = ⟨I(s)⁻¹ L, ∂I(s)/∂s · ṡ⟩
```

### Horizontal and Vertical Decomposition

At each point q ∈ Q:
- **Vertical space** V_q: tangent to the fiber (pure rotations)
- **Horizontal space** H_q = ker(A_q): "shape changes without rotation"

The connection provides the splitting: T_q Q = H_q ⊕ V_q

---

## Locked Inertia Tensor

### Definition

The locked inertia tensor I(s) is the moment of inertia tensor computed when the system is "frozen" at shape s with all internal velocities zero:

```python
def compute_locked_inertia(shape_point, masses):
    """
    Compute the locked inertia tensor.

    For 3 bodies with positions rᵢ (satisfying Σmᵢrᵢ = 0):
    I_jk = Σᵢ mᵢ (|rᵢ|² δ_jk - rᵢ_j rᵢ_k)

    Returns:
        3×3 symmetric matrix
    """
    # Reconstruct positions from shape
    r1, r2, r3 = shape_to_positions(shape_point, masses)

    I = np.zeros((3, 3))
    for m, r in zip(masses, [r1, r2, r3]):
        r_sq = np.dot(r, r)
        I += m * (r_sq * np.eye(3) - np.outer(r, r))

    return I
```

### Properties

1. **Symmetric**: I = Iᵀ
2. **Positive definite** (for non-degenerate configurations)
3. **Depends only on shape** (not on orientation)

### Derivative

For the connection formula, we need ∂I/∂s:

```python
def compute_inertia_derivative(shape_point, masses, delta=1e-8):
    """
    Compute ∂I_ij/∂s_k via finite differences.

    Returns:
        (3, 3, 3) tensor where result[i,j,k] = ∂I_ij/∂s_k
    """
    dI_ds = np.zeros((3, 3, 3))
    I_center = compute_locked_inertia(shape_point, masses)

    for k in range(3):
        shape_plus = shape_point.copy()
        shape_plus[k] += delta
        I_plus = compute_locked_inertia(shape_plus, masses)

        dI_ds[:, :, k] = (I_plus - I_center) / delta

    return dI_ds
```

---

## Connection Formula

### Explicit Formula

For the mechanical connection on the three-body shape space:

```
A_k(s) = Σ_ij I⁻¹_ij(s) · ∂I_jl/∂s_k · L_l
```

where L is the (fixed) angular momentum vector.

### Component Form

```python
def compute_connection_components(shape_point, masses, L):
    """
    Compute connection 1-form components [A₁, A₂, A₃].

    A_k = Σ_ij I⁻¹_ij · ∂I_jl/∂s_k · L_l
    """
    I = compute_locked_inertia(shape_point, masses)
    I_inv = np.linalg.inv(I)
    dI_ds = compute_inertia_derivative(shape_point, masses)

    A = np.zeros(3)
    for k in range(3):
        # Contract: I⁻¹ · (∂I/∂s_k) · L
        A[k] = np.einsum('ij,jl,l->', I_inv, dI_ds[:,:,k], L)

    return A
```

### Contraction with Velocity

The physically relevant quantity is A contracted with shape velocity:

```python
def evaluate_connection(shape_point, shape_velocity, masses, L):
    """
    Evaluate A(s) · ṡ = ⟨I(s)⁻¹ L, ∂I(s)/∂s · ṡ⟩
    """
    A = compute_connection_components(shape_point, masses, L)
    return np.dot(A, shape_velocity)
```

---

## Curvature Computation

### Definition

The curvature 2-form F = dA measures the non-commutativity of horizontal lifts:

```
F = dA + ½[A ∧ A]
```

For abelian structure groups (like S¹), this simplifies to F = dA.

### Component Formula

```
F_ij = ∂A_j/∂s_i - ∂A_i/∂s_j
```

This gives a 3×3 antisymmetric matrix.

### Implementation

```python
def compute_curvature(shape_point, masses, L, delta=1e-8):
    """
    Compute curvature 2-form F = dA.

    Returns:
        3×3 antisymmetric matrix F_ij
    """
    A_center = compute_connection_components(shape_point, masses, L)

    # Compute partial derivatives
    dA_ds = np.zeros((3, 3))  # dA_ds[i,j] = ∂A_i/∂s_j

    for j in range(3):
        shape_plus = shape_point.copy()
        shape_plus[j] += delta
        A_plus = compute_connection_components(shape_plus, masses, L)
        dA_ds[:, j] = (A_plus - A_center) / delta

    # Curvature: F_ij = ∂A_j/∂s_i - ∂A_i/∂s_j
    F = dA_ds.T - dA_ds

    return F
```

### Verification

The curvature should satisfy:
1. **Antisymmetry**: F_ij = -F_ji
2. **Bianchi identity**: dF = 0 (for abelian case, automatically satisfied)

```python
def verify_curvature(F):
    """Verify curvature properties."""
    # Check antisymmetry
    antisym_error = np.max(np.abs(F + F.T))

    return {
        'antisymmetric': antisym_error < 1e-10,
        'antisymmetry_error': antisym_error
    }
```

---

## Physical Interpretation

### Magnetic Term in Reduced Hamiltonian

After symplectic reduction, the Hamiltonian becomes:

```
H_red(s, p_s) = ½ g^{ij}(s) p_i p_j + V(s) + ⟨A(s), ṡ⟩ · |L|
```

The term ⟨A(s), ṡ⟩ · |L| is the **magnetic term**—it couples shape motion to rotation.

### Coriolis and Centrifugal Forces

The magnetic term generates:
- **Coriolis force**: Proportional to ṡ (velocity-dependent)
- **Geometric phase**: Accumulated rotation during shape cycles

### Curvature as Obstruction

**Key theorem**: If F = dA ≠ 0, then:
1. The system cannot be globally Hamiltonian with the canonical symplectic form
2. Additional integrals of motion cannot exist (generically)
3. The connection has non-trivial holonomy (geometric phases)

This is why we need **lifts**: to go to a higher-dimensional space where F can become zero or exact.

### Holonomy

For a closed loop γ in shape space, the holonomy is:

```
hol(γ) = exp(∮_γ A) = exp(∫∫_Σ F)
```

where Σ is any surface bounded by γ (Stokes theorem).

Non-zero holonomy means: traversing a closed shape cycle returns the system with a net rotation—the **geometric phase**.

---

## Implementation Details

### Numerical Considerations

1. **Near-collision singularity**: I(s) becomes singular as r_ij → 0
   - Solution: Use regularized coordinates (KS)

2. **Finite difference accuracy**: Use central differences for better accuracy
   ```python
   dA_i = (A(s + δe_j) - A(s - δe_j)) / (2δ)
   ```

3. **Triangle inequality**: Shape point must satisfy triangle constraints
   - Validate before computing

### Full Implementation

```python
class MechanicalConnection:
    """Complete mechanical connection implementation."""

    def __init__(self, masses, angular_momentum=None):
        self.masses = masses
        self.L = angular_momentum if angular_momentum is not None else np.array([0, 0, 1])
        self.inertia = LockedInertiaTensor(masses)

    def components(self, shape_point):
        """Get connection components [A₁, A₂, A₃]."""
        I = self.inertia.compute(shape_point)
        I_inv = np.linalg.inv(I)
        dI_ds = self.inertia.compute_derivative(shape_point)

        A = np.zeros(3)
        for k in range(3):
            A[k] = np.einsum('ij,jl,l->', I_inv, dI_ds[:,:,k], self.L)
        return A

    def evaluate(self, shape_point, shape_velocity):
        """Contract A with velocity: A(s) · ṡ"""
        return np.dot(self.components(shape_point), shape_velocity)

    def compute_curvature(self, shape_point, delta=1e-8):
        """Compute curvature F = dA."""
        A = self.components(shape_point)
        dA_ds = np.zeros((3, 3))

        for j in range(3):
            sp = shape_point.copy()
            sp[j] += delta
            dA_ds[:, j] = (self.components(sp) - A) / delta

        return dA_ds.T - dA_ds
```

---

## References

- Marsden, J.E. & Ratiu, T.S. (1999). *Introduction to Mechanics and Symmetry*
- Montgomery, R. (1988). "The connection whose holonomy is the classical adiabatic angles"
- Littlejohn, R.G. & Reinsch, M. (1997). "Gauge fields in the separation of rotations"
- `Science-Research-Docs/WP1 – Foundations.pdf`
