# Constraints as Momentum Maps

The deep geometric interpretation of the KS bilinear constraint.

## Table of Contents

1. [Overview](#overview)
2. [Gauge Symmetry in KS](#gauge-symmetry-in-ks)
3. [The Bilinear Constraint](#the-bilinear-constraint)
4. [Momentum Map Interpretation](#momentum-map-interpretation)
5. [Symplectic Reduction](#symplectic-reduction)
6. [Connection to Three-Body Problem](#connection-to-three-body-problem)
7. [Implications for Lift-Integrability](#implications-for-lift-integrability)

---

## Overview

### The Key Insight

The KS transformation has a hidden S¹ symmetry. The bilinear constraint:

```
Ξ = u₀p₁ - u₁p₀ + u₂p₃ - u₃p₂ = 0
```

is not just an arbitrary constraint—it is the **momentum map** for this S¹ action!

This places the KS transformation squarely within the framework of symplectic geometry and Marsden-Weinstein reduction.

### Why This Matters

1. **Geometric understanding**: KS is symplectic reduction in disguise
2. **Constraint preservation**: Momentum maps are automatically conserved
3. **Extension to 3BP**: Guides how to construct pairwise KS
4. **Lift-integrability**: Connects to the S¹ bundle construction

---

## Gauge Symmetry in KS

### The S¹ Action

On spinor space ℝ⁴, there is an S¹ action:

```
φ · u = (cos φ · u₀ - sin φ · u₁, sin φ · u₀ + cos φ · u₁,
         cos φ · u₂ - sin φ · u₃, sin φ · u₂ + cos φ · u₃)
```

This can be written as:
```
φ · u = exp(φ · J) · u
```

where J is the generator matrix.

### Generator Matrix

```
J = | 0  -1   0   0 |
    | 1   0   0   0 |
    | 0   0   0  -1 |
    | 0   0   1   0 |
```

The infinitesimal action is:
```
Xu = J · u = (-u₁, u₀, -u₃, u₂)
```

### Invariance of Position

The position r = ks(u) is invariant under this S¹ action:

```
ks(φ · u) = ks(u) for all φ ∈ S¹
```

Proof: The KS transformation involves only |u|² and combinations like u₀² - u₁² which are S¹-invariant.

---

## The Bilinear Constraint

### Statement

Physical trajectories must satisfy:

```
Ξ(u, p_u) = u₀p₁ - u₁p₀ + u₂p₃ - u₃p₂ = 0
```

### Equivalent Forms

Using the generator J:
```
Ξ = ⟨Ju, p_u⟩ = (Ju)ᵀ p_u
```

Or in matrix form:
```
Ξ = uᵀ Jᵀ p_u = -uᵀ J p_u
```

### Physical Meaning

Ξ measures the "angular momentum" in the fictitious S¹ direction:
- Ξ = 0: No rotation in gauge direction
- Ξ ≠ 0: "Spinning" in the fiber

The constraint Ξ = 0 fixes the gauge.

---

## Momentum Map Interpretation

### Hamiltonian Action

The S¹ action on T*ℝ⁴ is **Hamiltonian** with momentum map:

```
J: T*ℝ⁴ → ℝ
J(u, p_u) = Ξ = ⟨Ju, p_u⟩
```

### Verification

To verify J is a momentum map, check:
```
{J, f} = Xf for all f
```

where X is the infinitesimal generator.

The Poisson bracket:
```
{Ξ, u_i} = ∂Ξ/∂p_i = (Ju)_i = X_{u_i}
{Ξ, p_i} = -∂Ξ/∂u_i = -(Jᵀp)_i = X_{p_i}
```

Yes! The Hamiltonian vector field of Ξ equals the generator of the S¹ action.

### Equivariance

The momentum map is **equivariant**:
```
J(φ · (u, p)) = J(u, p) for all φ
```

This follows because the S¹ action is abelian.

---

## Symplectic Reduction

### Level Set

The constraint surface is:
```
J⁻¹(0) = {(u, p_u) ∈ T*ℝ⁴ : Ξ = 0}
```

This is a 7-dimensional submanifold of T*ℝ⁴ (8D).

### Quotient

The reduced space is:
```
M_red = J⁻¹(0) / S¹
```

Dimension: 7 - 1 = 6

### Identification

**Key result**: 
```
M_red ≅ T*(ℝ³ \ {0})
```

The reduced space is exactly the phase space of the Kepler problem (minus collision)!

### Proof Sketch

1. At each point u with |u|² = r, the S¹ orbit is a circle
2. Quotienting identifies all spinors u giving the same position r
3. The constraint Ξ = 0 fixes the "phase" degree of freedom
4. Result: 6D space parameterized by (r, p) with r ≠ 0

---

## Connection to Three-Body Problem

### Pairwise Constraints

For three-body with pairwise KS:

```
Ξ₁₂ = ⟨J·u₁₂, p₁₂⟩ = 0
Ξ₂₃ = ⟨J·u₂₃, p₂₃⟩ = 0
Ξ₃₁ = ⟨J·u₃₁, p₃₁⟩ = 0
```

Each is a momentum map for S¹ action on that pair.

### Product of S¹ Actions

The full gauge group is:
```
G = S¹ × S¹ × S¹ = T³ (3-torus)
```

Momentum map:
```
J: T*(ℝ⁴ × ℝ⁴ × ℝ⁴) → ℝ³
J(u, p) = (Ξ₁₂, Ξ₂₃, Ξ₃₁)
```

### Reduction

```
Physical phase space = J⁻¹(0) / T³
```

Dimension: 24 - 3 (constraints) - 3 (quotient) = 18... but we also have closure constraints!

### Closure Constraints

The triangle closure r₁₂ + r₂₃ + r₃₁ = 0 gives 3 more constraints.

These are **not** momentum maps (not from a symmetry), but they're compatible with the S¹ actions.

Final dimension: 24 - 6 (bilinear) - 3 (closure) = 15 (matches Jacobi space after translation reduction).

---

## Implications for Lift-Integrability

### The S¹ Bundle Connection

The S¹ lift in WP 2.2 and the KS gauge symmetry are related:

| S¹ Bundle Lift | KS Gauge Symmetry |
|----------------|-------------------|
| Add S¹ fiber to shape space | S¹ acts on spinor space |
| p_θ = fiber momentum | Ξ = gauge momentum |
| Conserved if H̃ θ-independent | Conserved by construction |

### Unifying Perspective

Both constructions "extend" phase space with an S¹:
- S¹ lift: Adds θ to absorb connection
- KS: Uses gauge freedom in spinor representation

The constraint Ξ = 0 in KS is analogous to fixing p_θ in S¹ lift!

### Path to Integrability

If we can show:
1. The extended system (before reducing by S¹) has additional structure
2. New integrals exist in the extended space
3. These integrals descend appropriately

Then lift-integrability is demonstrated.

### The Hopf Fibration

For single-pair KS, the geometry is:
```
S³ → S²
```

This is the Hopf fibration! The S¹ fiber over each point of S² corresponds to the gauge freedom.

For the two-body problem:
- S³ = energy surface in spinor space
- S² = direction of position vector r/|r|
- S¹ fiber = gauge orbit

The hidden SO(4) symmetry of Kepler is revealed in this picture:
```
SO(4) = SU(2) × SU(2)
```

acting on spinors.

---

## Implementation

### Constraint as Momentum Map

```python
class S1MomentumMap:
    """S¹ momentum map (KS bilinear constraint)."""
    
    # Generator matrix J
    J = np.array([
        [0, -1, 0, 0],
        [1, 0, 0, 0],
        [0, 0, 0, -1],
        [0, 0, 1, 0]
    ])
    
    @classmethod
    def evaluate(cls, u, p_u):
        """Compute Ξ = ⟨Ju, p_u⟩."""
        Ju = cls.J @ u
        return np.dot(Ju, p_u)
    
    @classmethod
    def gradient_u(cls, p_u):
        """∂Ξ/∂u = Jᵀp."""
        return cls.J.T @ p_u
    
    @classmethod
    def gradient_p(cls, u):
        """∂Ξ/∂p = Ju."""
        return cls.J @ u
    
    @classmethod
    def hamiltonian_vector_field(cls, u, p_u):
        """Hamiltonian vector field X_Ξ."""
        # X_Ξ = (∂Ξ/∂p, -∂Ξ/∂u) = (Ju, -Jᵀp)
        return np.concatenate([cls.J @ u, -cls.J.T @ p_u])
    
    @classmethod
    def s1_action(cls, phi, u):
        """Apply S¹ rotation by angle φ."""
        c, s = np.cos(phi), np.sin(phi)
        return np.array([
            c*u[0] - s*u[1],
            s*u[0] + c*u[1],
            c*u[2] - s*u[3],
            s*u[2] + c*u[3]
        ])
```

### Verifying Momentum Map Property

```python
def verify_momentum_map(u, p_u, delta=1e-7):
    """
    Verify that Ξ is momentum map for S¹ action.
    
    Check: X_Ξ equals infinitesimal generator of S¹.
    """
    mm = S1MomentumMap()
    
    # Hamiltonian vector field of Ξ
    X_Xi = mm.hamiltonian_vector_field(u, p_u)
    
    # Infinitesimal generator (derivative of action at φ=0)
    u_rotated = mm.s1_action(delta, u)
    X_generator = np.concatenate([
        (u_rotated - u) / delta,
        np.zeros(4)  # p unchanged infinitesimally
    ])
    
    # Compare (should match up to O(delta))
    error = np.linalg.norm(X_Xi[:4] - X_generator[:4])
    
    return {
        'is_momentum_map': error < 10 * delta,
        'error': error
    }
```

### Constrained Dynamics

```python
def project_to_constraint(state, tolerance=1e-14):
    """
    Project state to constraint surface Ξ = 0.
    
    Uses gauge transformation to achieve Ξ = 0.
    """
    u, p_u = state[:4], state[4:8]
    Xi = S1MomentumMap.evaluate(u, p_u)
    
    if abs(Xi) < tolerance:
        return state  # Already on constraint
    
    # Find φ such that Ξ(φ·u, φ·p) = 0
    # This is a root-finding problem
    from scipy.optimize import brentq
    
    def Xi_of_phi(phi):
        u_rot = S1MomentumMap.s1_action(phi, u)
        p_rot = S1MomentumMap.s1_action(phi, p_u)
        return S1MomentumMap.evaluate(u_rot, p_rot)
    
    # Find root
    phi_star = brentq(Xi_of_phi, 0, 2*np.pi)
    
    # Apply rotation
    u_new = S1MomentumMap.s1_action(phi_star, u)
    p_new = S1MomentumMap.s1_action(phi_star, p_u)
    
    return np.concatenate([u_new, p_new, state[8:]])
```

---

## References

- Zhao, L. (2015). "The KS transformation as a symplectic reduction"
- Kummer, M. (1982). "On the regularization of the Kepler problem"
- Cushman, R. & Duistermaat, J.J. (1997). "The quantum mechanical spherical pendulum"
- `Science-Research-Docs/WP2 – 2-Body Kepler + KS.pdf`
