# Symplectic Reduction Theory

Mathematical foundations for Marsden-Weinstein symplectic reduction.

## Table of Contents

1. [Hamiltonian Group Actions](#hamiltonian-group-actions)
2. [Momentum Maps](#momentum-maps)
3. [Marsden-Weinstein Reduction](#marsden-weinstein-reduction)
4. [Application to Three-Body Problem](#application-to-three-body-problem)
5. [Magnetic Terms from Reduction](#magnetic-terms-from-reduction)

---

## Hamiltonian Group Actions

### Definition

A Lie group G acts on a symplectic manifold (M, ω) in a **Hamiltonian** way if:
1. The action preserves the symplectic form: g*ω = ω for all g ∈ G
2. There exists an equivariant momentum map J: M → g*

### For Three-Body Problem

The symmetry group is SE(3) = ℝ³ ⋊ SO(3):
- **Translations ℝ³**: Move center of mass
- **Rotations SO(3)**: Rotate configuration

The action on configuration space Q = (ℝ³)³:
```
(a, R) · (r₁, r₂, r₃) = (R·r₁ + a, R·r₂ + a, R·r₃ + a)
```

### Infinitesimal Action

For ξ ∈ se(3) = ℝ³ ⊕ so(3), the infinitesimal generator is:
```
ξ_M(q) = d/dt|_{t=0} exp(tξ) · q
```

For translations: ξ_M = v (constant vector field)
For rotations: ξ_M = ω × r (rotation vector field)

---

## Momentum Maps

### Definition

A **momentum map** J: M → g* satisfies:
```
⟨dJ, ξ_M⟩ = ι_{ξ_M} ω
```

In coordinates: the Hamiltonian generating the ξ action is ⟨J(x), ξ⟩.

### Three-Body Momentum Map

For SE(3) action on T*(ℝ³)³:

**Linear momentum** (for translations):
```
P = p₁ + p₂ + p₃ ∈ ℝ³
```

**Angular momentum** (for rotations):
```
L = r₁ × p₁ + r₂ × p₂ + r₃ × p₃ ∈ ℝ³
```

Combined: J = (P, L) ∈ se(3)* ≅ ℝ³ × ℝ³

### Equivariance

The momentum map is **equivariant** if:
```
J(g·x) = Ad*_g J(x)
```

This ensures consistent reduction at different momentum levels.

### Noether's Theorem

Conserved quantities from symmetries:
- Translation invariance ⟺ P conserved
- Rotation invariance ⟺ L conserved
- Time translation invariance ⟺ E conserved

---

## Marsden-Weinstein Reduction

### The Theorem

**Theorem** (Marsden-Weinstein 1974): Let G act on (M, ω) with equivariant momentum map J. If μ ∈ g* is a regular value of J and G_μ acts freely and properly on J⁻¹(μ), then:

1. The quotient M_μ = J⁻¹(μ)/G_μ is a smooth manifold
2. M_μ carries a unique symplectic form ω_μ such that π*ω_μ = i*ω

where i: J⁻¹(μ) → M is inclusion and π: J⁻¹(μ) → M_μ is projection.

### Dimension Formula

```
dim(M_μ) = dim(M) - 2·dim(G) + dim(G_μ)
```

For the three-body problem with G = SE(3):
- dim(M) = 18 (phase space)
- dim(G) = 6 (SE(3))
- If P = 0, L ≠ 0: G_μ = SO(2) (rotations about L), dim(G_μ) = 1
- dim(M_μ) = 18 - 12 + 1 = 7

### Reduced Dynamics

The Hamiltonian H: M → ℝ descends to H_μ: M_μ → ℝ:
```
H_μ([x]) = H(x) for x ∈ J⁻¹(μ)
```

The reduced Hamiltonian flow on (M_μ, ω_μ) projects the original flow.

---

## Application to Three-Body Problem

### Stage 1: Translation Reduction

**Momentum level**: P = 0 (total momentum zero)
**Symmetry**: ℝ³ translations
**Stabilizer**: G_P = ℝ³ (all of G fixes P = 0)

**Result**:
- Constraint: Σm_i r_i = 0 (COM at origin)
- Quotient: Remove 3D gauge freedom
- Reduced space: 18 - 6 = 12D phase space... but we have Jacobi coordinates (15D)

**Why 15D?** The symplectic reduction gives 12D, but we often work with the "intermediate" 15D space before fully quotienting.

### Stage 2: Rotation Reduction

**Momentum level**: L = μ ≠ 0 (fixed angular momentum)
**Symmetry**: SO(3) rotations
**Stabilizer**: G_L = SO(2) (rotations about L axis)

**Result** (starting from 15D Jacobi):
- Quotient by SO(3)/SO(2) ≅ S²: removes 2D
- Fix |L| = const: removes 1D
- Reduced space: 15 - 3 + 1 = 13D... or 12D if planar

**Planar case** (z = 0):
- Symmetry: SO(2) instead of SO(3)
- Stabilizer: {e} (trivial for L ≠ 0)
- dim = 12 - 2 = 10D for phase space
- But with 2D configuration removed: 15 - 3 = 12D total phase space

### Summary Table

| Level | Dimension | Coordinates |
|-------|-----------|-------------|
| Full Cartesian | 18D | (r₁, r₂, r₃, p₁, p₂, p₃) |
| Jacobi (P = 0) | 15D | (ρ₁, ρ₂, π₁, π₂) + L |
| Reduced (fix L) | 12D (planar) | (r₁₂, r₂₃, r₃₁, momenta) |
| Shape space | 6D config | (r₁₂, r₂₃, r₃₁) |

---

## Magnetic Terms from Reduction

### Cotangent Bundle Reduction

When reducing a cotangent bundle T*Q by a group G acting on Q:

**Without momentum (μ = 0)**:
```
T*Q //₀ G ≅ T*(Q/G)
```
The reduced space is just the cotangent bundle of the base.

**With momentum (μ ≠ 0)**:
```
T*Q //μ G ≅ T*(Q/G) with twisted symplectic form
```

The symplectic form becomes:
```
ω_μ = ω_can - π*β_μ
```

where β_μ is a **magnetic 2-form** on Q/G.

### The Magnetic Term

For the three-body problem, after rotation reduction:
```
ω_red = ω_shape - μ · F_A
```

where:
- ω_shape = canonical form on T*(shape space)
- F_A = dA = curvature of mechanical connection
- μ = |L| (angular momentum magnitude)

### Physical Interpretation

The magnetic term μ · F_A creates:
1. **Modified Poisson brackets**: {p_i, p_j} ≠ 0
2. **Coriolis-like forces**: Velocity-dependent terms in equations
3. **Geometric phases**: Non-zero holonomy around closed paths

### Reduced Hamiltonian

```
H_red(s, p_s) = ½ g^{ij}(s) p_i p_j + V_eff(s) + ⟨A(s), ṡ⟩ · |L|
```

The third term is the **magnetic coupling** between shape motion and rotation.

---

## Implementation Notes

### Reduction in Practice

```python
class MarsdenWeinsteinReduction:
    """
    Generic Marsden-Weinstein reduction framework.
    """
    
    def __init__(self, group, action, momentum_map):
        self.group = group
        self.action = action
        self.momentum_map = momentum_map
        
    def reduce(self, state, momentum_level):
        """
        Reduce state at given momentum level.
        
        1. Project to momentum level set J⁻¹(μ)
        2. Quotient by stabilizer G_μ
        """
        # Check momentum level
        mu_actual = self.momentum_map(state)
        if not np.allclose(mu_actual, momentum_level):
            raise ValueError("State not at specified momentum level")
            
        # Find orbit representative (gauge fixing)
        reduced = self.gauge_fix(state)
        
        return reduced
        
    def gauge_fix(self, state):
        """Choose canonical representative in orbit."""
        # Implementation depends on group and chosen gauge
        raise NotImplementedError
```

### Symplectic Form Verification

```python
def verify_symplectic_reduction(original_omega, reduced_omega, projection):
    """
    Verify that π*ω_μ = i*ω.
    
    Args:
        original_omega: Symplectic form on M
        reduced_omega: Symplectic form on M_μ
        projection: Map π: J⁻¹(μ) → M_μ
    """
    # Compute pullback
    pullback = projection.pullback(reduced_omega)
    
    # Compare with restriction
    restriction = original_omega.restrict(momentum_level_set)
    
    error = np.max(np.abs(pullback - restriction))
    return error < 1e-10
```

---

## References

- Marsden, J.E. & Weinstein, A. (1974). "Reduction of symplectic manifolds with symmetry"
- Abraham, R. & Marsden, J.E. (1978). *Foundations of Mechanics*
- Marsden, J.E. & Ratiu, T.S. (1999). *Introduction to Mechanics and Symmetry*
- Ortega, J.-P. & Ratiu, T.S. (2004). *Momentum Maps and Hamiltonian Reduction*
