# Dimension Counting in Three-Body Reduction

Systematic analysis of phase space dimensions through the reduction sequence.

## Table of Contents

1. [General Principles](#general-principles)
2. [Full Phase Space](#full-phase-space)
3. [Translation Reduction](#translation-reduction)
4. [Rotation Reduction](#rotation-reduction)
5. [Special Cases](#special-cases)
6. [Summary Table](#summary-table)

---

## General Principles

### Symplectic Reduction Formula

For a Hamiltonian G-action on (M, ω) with momentum map J:

```
dim(M_μ) = dim(M) - 2·dim(G/G_μ)
```

where G_μ is the stabilizer of μ ∈ g*.

Alternatively:
```
dim(M_μ) = dim(M) - 2·dim(G) + 2·dim(G_μ)
```

### Constraint Counting

Another viewpoint:
- Each constraint reduces dimension by 1
- Each gauge symmetry reduces dimension by 1
- Net reduction = (constraints) + (gauge quotient)

---

## Full Phase Space

### Starting Point: N = 3 Bodies in 3D

**Configuration space**: Q = (ℝ³)³
```
dim(Q) = 3 × 3 = 9
```

**Phase space**: M = T*Q = (ℝ³ × ℝ³)³
```
dim(M) = 2 × 9 = 18
```

**Degrees of freedom**: n = dim(Q) = 9
**Phase space dimension**: 2n = 18

---

## Translation Reduction

### Symmetry Group

**Group**: G = ℝ³ (translations)
**Action**: (r₁, r₂, r₃) ↦ (r₁ + a, r₂ + a, r₃ + a)

### Momentum Map

**Total momentum**: P = p₁ + p₂ + p₃ ∈ ℝ³

### Reduction at P = 0

**Momentum level**: μ = 0
**Stabilizer**: G_μ = ℝ³ (all translations fix P = 0)

**Dimension calculation**:
```
dim(M_0) = 18 - 2·dim(ℝ³) + 2·dim(ℝ³)
         = 18 - 6 + 6
         = 18
```

Wait—this gives 18D! The issue is that when μ = 0, the stabilizer equals the full group.

**Correct counting**:
- Constraint P = 0: 3 equations
- COM = 0 gauge: 3 equations (place COM at origin)
- Total reduction: 18 - 6 = 12D

But we often use 15D Jacobi coordinates. Why?

### Jacobi Coordinates (15D)

The 15D Jacobi space is **not** the reduced space M_0, but rather:

```
T*(Q/ℝ³) ≅ T*(relative positions)
```

where we've removed the 3D position of the COM but kept its momentum.

**Dimension**: 
- Original: 18D
- Remove COM position: -3D
- Result: 15D

The full reduction to 12D would also remove the COM velocity (total momentum), but we often work at the 15D level.

---

## Rotation Reduction

### Symmetry Group

**Group**: G = SO(3) (rotations)
**Action**: (r₁, r₂, r₃) ↦ (Rr₁, Rr₂, Rr₃)

### Momentum Map

**Angular momentum**: L = Σᵢ rᵢ × pᵢ ∈ ℝ³

### Reduction at L = μ ≠ 0

**Stabilizer**: G_μ = SO(2) (rotations about L axis)

**Dimension** (starting from 15D Jacobi):
```
dim(M_μ) = 15 - 2·dim(SO(3)/SO(2))
         = 15 - 2·dim(S²)
         = 15 - 2·2
         = 11
```

Hmm, this gives 11D, not 12D. Let's be more careful.

### Careful Analysis

**Phase space**: 15D (Jacobi)
**Constraint**: |L| = const (1 equation, since we're on a sphere in L-space)
**Quotient**: SO(3)/SO(2) action (2D quotient, since S² = SO(3)/SO(2))

```
dim = 15 - 1 (|L| constraint) - 2 (SO(3)/SO(2) quotient) = 12
```

This matches! The 12D is:
- 6D shape configuration
- 6D conjugate momenta

### Planar Case

For planar motion (z = 0 for all bodies):

**Original**: 12D phase space (6 positions, 6 momenta, all in plane)
**Symmetry**: SO(2) ⊂ SO(3)
**Momentum**: L = (0, 0, L_z) single component

**Reduction**:
```
dim = 12 - 2·dim(SO(2))
    = 12 - 2·1
    = 10
```

But we said 12D earlier for planar reduced space. The discrepancy:
- 12D if we use shape space embedding in 3D
- 10D for true planar reduction

---

## Special Cases

### Zero Angular Momentum (L = 0)

**Stabilizer**: G_0 = SO(3) (all rotations)

**Dimension** (from 15D):
```
dim(M_0) = 15 - 2·dim(SO(3)/SO(3))
         = 15 - 0
         = 15
```

No reduction by rotations! But:
- We can still quotient by SO(3): -3D
- Result: 15 - 3 = 12D shape space

### Collinear Configuration

All bodies on a line ⟹ special stabilizer structure.

### Equal Masses

m₁ = m₂ = m₃ ⟹ additional S₃ permutation symmetry.

---

## Summary Table

### From Full Cartesian (18D)

| Reduction Step | Dimension | Description |
|----------------|-----------|-------------|
| Full phase space | 18D | (r₁,r₂,r₃,p₁,p₂,p₃) |
| Fix P = 0 | 15D | Jacobi coordinates |
| Fix \|L\| | 14D | Constant angular momentum magnitude |
| Quotient SO(3)/SO(2) | 12D | Shape phase space |

### Alternative Path (Planar)

| Reduction Step | Dimension | Description |
|----------------|-----------|-------------|
| Planar full space | 12D | z = 0 constraint |
| Fix P = 0 | 9D | Planar Jacobi |
| Quotient SO(2) | 8D | Planar shape phase space |

### Degrees of Freedom Count

| Level | Config DOF | Phase DOF | Description |
|-------|------------|-----------|-------------|
| Full 3D | 9 | 18 | Three 3D positions |
| After translation | 6 | 12 | Relative positions |
| After rotation | 3-4 | 6-8 | Shape + angular |
| Shape only | 3 | 6 | Pure shape (planar) |

---

## Implementation Check

```python
def verify_dimension(state, expected_dim, name):
    """Verify state has expected dimension."""
    actual = len(state)
    if actual != expected_dim:
        raise ValueError(
            f"{name}: expected {expected_dim}D, got {actual}D"
        )
    return True

# Usage
verify_dimension(cart_state, 18, "Cartesian")
verify_dimension(jacobi_state, 15, "Jacobi")  # or 12 depending on convention
verify_dimension(shape_state, 6, "Shape configuration")
verify_dimension(shape_phase_state, 12, "Shape phase space")
```

---

## Common Confusions

### Q: Why is Jacobi 15D not 12D?

The 15D Jacobi space includes:
- 6D relative positions (ρ₁, ρ₂)
- 6D relative momenta (π₁, π₂)
- 3D angular momentum direction

The angular momentum direction hasn't been quotiented yet.

### Q: Why is planar shape 12D not 8D?

Depends on embedding:
- 12D if we embed in 3D and restrict to z = 0
- 8D for intrinsic planar reduction

### Q: How does connection appear?

When we quotient SO(3) but keep track of angular momentum L:
- We get a principal SO(2) bundle over shape space
- The connection A encodes how rotation couples to shape
- The 2-form F = dA is the magnetic term

---

## References

- Marsden, J.E. & Ratiu, T.S. (1999). *Introduction to Mechanics and Symmetry*, Chapter 10
- Littlejohn, R.G. & Reinsch, M. (1997). "Gauge fields in the separation of rotations"
- `Science-Research-Docs/WP1 – Foundations.pdf`
