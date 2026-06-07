# Spinor Basis Theory

Mathematical foundations for KS-spinor basis functions in invariant discovery.

## Table of Contents

1. [The KS Transformation](#the-ks-transformation)
2. [Spinor Algebra](#spinor-algebra)
3. [Basis Function Construction](#basis-function-construction)
4. [Bilinear Relations](#bilinear-relations)
5. [Spinor Invariants](#spinor-invariants)
6. [Implementation](#implementation)

---

## The KS Transformation

### Motivation

In the Kepler problem, the gravitational force diverges at collision:
```
F = -k/r² → ∞ as r → 0
```

This singularity causes numerical instability. The Kustaanheimo-Stiefel (KS) transformation removes this singularity by lifting to 4D.

### Definition

Map from 4D spinor space to 3D position space:

```
u = (u₀, u₁, u₂, u₃) ∈ ℝ⁴
r = (x, y, z) ∈ ℝ³

Forward transformation:
x = u₀² - u₁² - u₂² + u₃²
y = 2(u₀u₁ - u₂u₃)
z = 2(u₀u₂ + u₁u₃)
```

### Fundamental Bilinear Relation

The key identity connecting spinor and position norms:

```
|r| = r = |u|² = u₀² + u₁² + u₂² + u₃²
```

This is why near collision (r → 0), the spinors remain well-behaved (|u| → 0 smoothly).

### Levi-Civita Matrix

The transformation can be written using the Levi-Civita matrix L(u):

```
r_extended = L(u) · u

where:
L(u) = | u₀  -u₁  -u₂   u₃ |
       | u₁   u₀  -u₃  -u₂ |
       | u₂   u₃   u₀   u₁ |
       | u₃  -u₂   u₁  -u₀ |
```

The fourth component of r_extended is always zero.

### Properties of L(u)

1. **Orthogonality**: L(u)ᵀL(u) = |u|²·I₄
2. **Symmetry**: L(u) = L(u)ᵀ
3. **Quaternionic**: Represents quaternion multiplication

---

## Spinor Algebra

### Quaternion Connection

KS spinors are essentially quaternions. For spinor u = (u₀, u₁, u₂, u₃):

```
q = u₀ + u₁i + u₂j + u₃k
```

The position r corresponds to the imaginary part of q·q̄:
```
q² = (u₀² - u₁² - u₂² + u₃²) + 2(u₀u₁ - u₂u₃)i + 2(u₀u₂ + u₁u₃)j + 0k
```

### Spinor Products

For two spinors u and v, key algebraic operations:

**Dot product**:
```
u · v = u₀v₀ + u₁v₁ + u₂v₂ + u₃v₃
```

**Quaternion product** (imaginary part gives "cross product"):
```
u × v = (u₀v₁ - u₁v₀ + u₂v₃ - u₃v₂,
         u₀v₂ - u₂v₀ + u₃v₁ - u₁v₃,
         u₀v₃ - u₃v₀ + u₁v₂ - u₂v₁)
```

**Mixed Levi-Civita product**:
```
u · L(v) · w = (u₀v₀ - u₁v₁ - u₂v₂ + u₃v₃)w₀ + ...
```

---

## Basis Function Construction

### Category 1: Spinor Norms (3 functions)

For a 3-body problem with spinors u₁, u₂, u₃:

```python
|u₁|² = u₁₀² + u₁₁² + u₁₂² + u₁₃²  # = |r₁| by bilinear relation
|u₂|² = u₂₀² + u₂₁² + u₂₂² + u₂₃²  # = |r₂|
|u₃|² = u₃₀² + u₃₁² + u₃₂² + u₃₃²  # = |r₃|
```

### Category 2: Inner Products (3 functions)

```python
u₁ · u₂ = Σᵢ u₁ᵢ u₂ᵢ
u₂ · u₃ = Σᵢ u₂ᵢ u₃ᵢ
u₃ · u₁ = Σᵢ u₃ᵢ u₁ᵢ
```

### Category 3: Quaternion Products (6 functions)

Three components of each cross product:

```python
(u₁ × u₂)_x, (u₁ × u₂)_y, (u₁ × u₂)_z
(u₂ × u₃)_x, (u₂ × u₃)_y, (u₂ × u₃)_z
```

### Category 4: Mixed Bilinear Forms (~20 functions)

```python
u₁ · L(u₂) · u₃
u₁ · L(u₃) · u₂
# ... permutations and component extractions
```

### Category 5: Momentum Products (~24 functions)

For spinor momenta pᵤ₁, pᵤ₂, pᵤ₃:

```python
pᵤ₁ · u₁, pᵤ₁ · u₂, pᵤ₁ · u₃
pᵤ₂ · u₁, pᵤ₂ · u₂, pᵤ₂ · u₃
pᵤ₁ · pᵤ₁, pᵤ₁ · pᵤ₂, ...
```

### Category 6: Higher Order (~24 functions)

```python
|u₁|⁴, |u₂|⁴, |u₃|⁴
(u₁ · u₂)², (u₂ · u₃)², (u₃ · u₁)²
|u₁|² · |u₂|², ...
```

---

## Bilinear Relations

### Position-Spinor Correspondence

For each pair of bodies, the relative position r_ij = r_j - r_i can be represented by a spinor u_ij:

```
|r_ij| = |u_ij|²
```

### Three-Body Closure

The relative positions form a closed triangle:
```
r₁₂ + r₂₃ + r₃₁ = 0
```

In spinor form, this becomes a constraint on (u₁₂, u₂₃, u₃₁).

### Bilinear Constraint

For each spinor-momentum pair, the KS constraint:
```
Ξ = u₀p₁ - u₁p₀ + u₂p₃ - u₃p₂ = 0
```

This is the momentum map for S¹ gauge symmetry (see WP2 lift-constructions).

---

## Spinor Invariants

### Known Spinor Conserved Quantities

**Spinor Angular Momentum**:
```
L_spinor = Σᵢ uᵢ × u̇ᵢ
```

**Spinor Energy** (regularized form):
```
H_spinor = Σᵢ |u̇ᵢ|²/2 - 1/|uᵢ|²
         = Σᵢ |u̇ᵢ|²/2 - 1/|uᵢ|⁴  (using bilinear)
```

**Bilinear Invariants** (potential hidden integrals):
```
I₁ = u₁ · u₂  (if conserved)
I₂ = u₁ × u₂  (if conserved)
```

### Pattern Matching

Known patterns to search for:

| Pattern | Expression | Interpretation |
|---------|------------|----------------|
| Norm sum | |u₁|² + |u₂|² | Total "spinor mass" |
| Cross invariant | u₁ · (u₂ × u₃) | Triple product |
| Energy-like | |pᵤ|² - 1/|u|² | Regularized energy |
| Momentum map | u · Jp | S¹ constraint |

---

## Implementation

### Position to Spinor

```python
def position_to_spinor(r, branch='auto'):
    """
    Convert 3D position to 4D spinor.

    Args:
        r: Position vector (N, 3) or (3,)
        branch: 'u3_zero' or 'u2_zero' or 'auto'

    Returns:
        u: Spinor (N, 4) or (4,)
    """
    r = np.atleast_2d(r)
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    r_norm = np.linalg.norm(r, axis=1)

    u = np.zeros((len(r), 4))

    # Choose branch based on sign of x
    if branch == 'auto':
        mask = x >= 0
    elif branch == 'u3_zero':
        mask = np.ones(len(r), dtype=bool)
    else:
        mask = np.zeros(len(r), dtype=bool)

    # Branch with u₃ = 0
    u0 = np.sqrt((r_norm + x) / 2)
    safe = u0 > 1e-10
    u[mask & safe, 0] = u0[mask & safe]
    u[mask & safe, 1] = y[mask & safe] / (2 * u0[mask & safe])
    u[mask & safe, 2] = z[mask & safe] / (2 * u0[mask & safe])
    u[mask, 3] = 0

    # Branch with u₂ = 0
    u1 = np.sqrt((r_norm - x) / 2)
    safe = u1 > 1e-10
    u[~mask & safe, 0] = y[~mask & safe] / (2 * u1[~mask & safe])
    u[~mask & safe, 1] = u1[~mask & safe]
    u[~mask, 2] = 0
    u[~mask & safe, 3] = z[~mask & safe] / (2 * u1[~mask & safe])

    return u.squeeze()
```

### Spinor to Position

```python
def spinor_to_position(u):
    """
    Convert 4D spinor to 3D position via KS transformation.

    Args:
        u: Spinor (N, 4) or (4,)

    Returns:
        r: Position (N, 3) or (3,)
    """
    u = np.atleast_2d(u)
    u0, u1, u2, u3 = u[:, 0], u[:, 1], u[:, 2], u[:, 3]

    x = u0**2 - u1**2 - u2**2 + u3**2
    y = 2 * (u0*u1 - u2*u3)
    z = 2 * (u0*u2 + u1*u3)

    return np.column_stack([x, y, z]).squeeze()
```

### Generate Spinor Basis

```python
def generate_spinor_basis():
    """
    Generate complete spinor basis for 3-body problem.

    Returns:
        List of basis functions, each taking (u1, u2, u3) arrays
    """
    basis = []

    # Category 1: Norms
    basis.append(lambda u1, u2, u3: np.sum(u1**2, axis=1))  # |u1|²
    basis.append(lambda u1, u2, u3: np.sum(u2**2, axis=1))  # |u2|²
    basis.append(lambda u1, u2, u3: np.sum(u3**2, axis=1))  # |u3|²

    # Category 2: Inner products
    basis.append(lambda u1, u2, u3: np.sum(u1 * u2, axis=1))  # u1·u2
    basis.append(lambda u1, u2, u3: np.sum(u2 * u3, axis=1))  # u2·u3
    basis.append(lambda u1, u2, u3: np.sum(u3 * u1, axis=1))  # u3·u1

    # Category 3: Quaternion cross products
    def quat_cross(u, v):
        """Quaternion cross product (imaginary part of u*conj(v))."""
        return np.column_stack([
            u[:, 0]*v[:, 1] - u[:, 1]*v[:, 0] + u[:, 2]*v[:, 3] - u[:, 3]*v[:, 2],
            u[:, 0]*v[:, 2] - u[:, 2]*v[:, 0] + u[:, 3]*v[:, 1] - u[:, 1]*v[:, 3],
            u[:, 0]*v[:, 3] - u[:, 3]*v[:, 0] + u[:, 1]*v[:, 2] - u[:, 2]*v[:, 1]
        ])

    for i in range(3):
        basis.append(lambda u1, u2, u3, i=i: quat_cross(u1, u2)[:, i])
        basis.append(lambda u1, u2, u3, i=i: quat_cross(u2, u3)[:, i])
        basis.append(lambda u1, u2, u3, i=i: quat_cross(u3, u1)[:, i])

    # Category 4-6: Add more as needed...
    # (Full implementation in src/python/symbolic/spinor_basis.py)

    return basis
```

### Verify Bilinear Relation

```python
def verify_bilinear_relation(r, u, tol=1e-10):
    """
    Verify |r| = |u|² for position-spinor pair.

    Returns:
        (passed, max_error)
    """
    r_norm = np.linalg.norm(np.atleast_2d(r), axis=1)
    u_norm_sq = np.sum(np.atleast_2d(u)**2, axis=1)

    error = np.abs(r_norm - u_norm_sq)
    max_error = np.max(error)

    return max_error < tol, max_error
```

---

## References

- Kustaanheimo, P. & Stiefel, E. (1965). "Perturbation theory of Kepler motion based on spinor regularization"
- Stiefel, E. & Scheifele, G. (1971). *Linear and Regular Celestial Mechanics*
- Waldvogel, J. (2006). "Quaternions and the perturbed Kepler problem"
- `Science-Research-Docs/WP3 – Generalized KS Transformations and N-Body Regularizations.pdf`
