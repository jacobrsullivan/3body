# KS-Spinor Transformation Theory

Mathematical foundations for the Kustaanheimo-Stiefel transformation and spinor regularization.

## Table of Contents

1. [Historical Context](#historical-context)
2. [The KS Transformation](#the-ks-transformation)
3. [Levi-Civita Matrix](#levi-civita-matrix)
4. [Bilinear Constraint](#bilinear-constraint)
5. [Sundman Time Transformation](#sundman-time-transformation)
6. [Regularized Hamiltonian](#regularized-hamiltonian)
7. [Pairwise Extension to Three-Body](#pairwise-extension-to-three-body)
8. [Implementation](#implementation)

---

## Historical Context

### The Collision Problem

In the two-body Kepler problem, the force diverges at collision:

```
F = -k/r² → ∞ as r → 0
```

This causes:
- Numerical integration failure
- Timestep collapse
- Loss of precision

### Regularization Idea

**Levi-Civita (1906)**: For 2D Kepler, use complex squaring z = u²
**Kustaanheimo-Stiefel (1965)**: Extended to 3D using quaternions/spinors

Key insight: Lift to 4D where the singularity disappears!

---

## The KS Transformation

### Definition

Map from 4D spinor space to 3D position space:

```
u = (u₀, u₁, u₂, u₃) ∈ ℝ⁴
r = (x, y, z) ∈ ℝ³

Transformation:
x = u₀² - u₁² - u₂² + u₃²
y = 2(u₀u₁ - u₂u₃)
z = 2(u₀u₂ + u₁u₃)
```

### Bilinear Relation

```
|r| = r = |u|² = u₀² + u₁² + u₂² + u₃²
```

This is the fundamental identity: distance equals spinor norm squared.

### Inverse Transformation

The inverse is multi-valued (S¹ gauge freedom). One choice:

```python
def ks_inverse(r):
    """
    Inverse KS: 3D position → 4D spinor (one branch).
    """
    x, y, z = r
    r_norm = np.linalg.norm(r)
    
    if x >= 0:
        # Branch with u₃ = 0
        u0 = np.sqrt((r_norm + x) / 2)
        u1 = y / (2 * u0) if u0 > 1e-10 else 0
        u2 = z / (2 * u0) if u0 > 1e-10 else 0
        u3 = 0
    else:
        # Branch with u₂ = 0
        u1 = np.sqrt((r_norm - x) / 2)
        u0 = y / (2 * u1) if u1 > 1e-10 else 0
        u2 = 0
        u3 = z / (2 * u1) if u1 > 1e-10 else 0
    
    return np.array([u0, u1, u2, u3])
```

---

## Levi-Civita Matrix

### Definition

The KS transformation can be written using the Levi-Civita matrix L(u):

```
r_ext = L(u) · u

where r_ext = (x, y, z, 0) (4D with zero fourth component)
```

### Matrix Form

```
L(u) = | u₀  -u₁  -u₂   u₃ |
       | u₁   u₀  -u₃  -u₂ |
       | u₂   u₃   u₀   u₁ |
       | u₃  -u₂   u₁  -u₀ |
```

### Properties

1. **Orthogonality**: L(u)ᵀ L(u) = |u|² · I₄
2. **Symmetry**: L(u) = L(u)ᵀ (self-adjoint)
3. **Quaternionic**: L(u) represents quaternion multiplication

### Implementation

```python
def levi_civita_matrix(u):
    """Build 4×4 Levi-Civita matrix."""
    u0, u1, u2, u3 = u
    return np.array([
        [u0, -u1, -u2,  u3],
        [u1,  u0, -u3, -u2],
        [u2,  u3,  u0,  u1],
        [u3, -u2,  u1, -u0]
    ])

def ks_transform(u):
    """KS transformation: spinor → position."""
    L = levi_civita_matrix(u)
    r_ext = L @ u
    return r_ext[:3]  # First 3 components
```

---

## Bilinear Constraint

### The Constraint

Physical trajectories must satisfy:

```
Ξ = u₀p₁ - u₁p₀ + u₂p₃ - u₃p₂ = 0
```

where p_u = (p₀, p₁, p₂, p₃) is the spinor momentum.

### Geometric Meaning

This constraint is the **momentum map for S¹ gauge symmetry**!

The KS transformation has a U(1) ≅ S¹ gauge freedom:
```
u ↦ e^{iφ} u  (spinor rotation)
```

This leaves r unchanged (since r = |u|²). The constraint Ξ = 0 fixes the gauge.

### As Momentum Map

```
J: T*ℝ⁴ → ℝ
J(u, p_u) = Ξ = ⟨Xu, p_u⟩

where X = generator of S¹ action on spinors
```

The constraint Ξ = 0 is the zero level set J⁻¹(0).

### Symplectic Reduction

```
Physical phase space = J⁻¹(0) / S¹ ≅ T*(ℝ³ \ {0})
```

This is how KS relates to standard phase space!

---

## Sundman Time Transformation

### The Transformation

Replace physical time t with fictitious time s:

```
dt/ds = g(r) = r = |u|²
```

### Effect on Dynamics

Near collision (r → 0):
- Physical time slows down (dt/ds → 0)
- Fictitious time continues at finite rate
- Trajectory passes smoothly through r = 0 in s-time

### Extended Phase Space

Include time as a coordinate:

```
Extended state: (u, p_u, t, -E)

where:
- t = physical time (coordinate)
- -E = energy (conjugate momentum to t)
```

### Regularized Equations

In fictitious time s:

```
du/ds = ∂K/∂p_u
dp_u/ds = -∂K/∂u
dt/ds = |u|²
dE/ds = 0  (energy conserved)
```

where K is the regularized Hamiltonian.

---

## Regularized Hamiltonian

### Kepler Hamiltonian

Original (singular):
```
H = |p|²/(2m) - k/r
```

### KS Regularized Form

Transform to spinor variables and use Sundman time:

```
K = |p_u|²/(8|u|²) - E|u|²/2 - k/2
```

or equivalently (with constraint):

```
K = |p_u|²/8 - (E|u|² + k)/2 = 0
```

The last equality (K = 0) is the **energy surface constraint**.

### Properties

1. **Nonsingular**: K is smooth at u = 0
2. **Oscillator-like**: Motion is bounded oscillation for E < 0
3. **Constraint surface**: K = 0 defines physical trajectories

### Equations of Motion

```
du_i/ds = ∂K/∂p_i = p_i / 4

dp_i/ds = -∂K/∂u_i = E · u_i
```

These are harmonic oscillator equations with frequency ω² = -E (for bound orbits E < 0).

---

## Pairwise Extension to Three-Body

### Idea

Apply KS to each pair of bodies:

```
r₁₂ → u₁₂ ∈ ℝ⁴
r₂₃ → u₂₃ ∈ ℝ⁴
r₃₁ → u₃₁ ∈ ℝ⁴
```

### Configuration Space

```
Spinor space: ℝ⁴ × ℝ⁴ × ℝ⁴ = ℝ¹²

Constraints:
- 3 bilinear constraints (Ξ₁₂ = Ξ₂₃ = Ξ₃₁ = 0)
- 3 closure constraints (triangle consistency)

Effective dimension: 12 - 6 = 6 (matches 3BP config space)
```

### Closure Constraints

The three relative positions must close to form a triangle:

```
r₁₂ + r₂₃ + r₃₁ = 0
```

In spinor form, this becomes 3 algebraic constraints on (u₁₂, u₂₃, u₃₁).

### Phase Space

```
Full spinor phase: T*ℝ¹² = ℝ²⁴

Constraints: 6 position + 6 momentum = 12

Reduced: 24 - 12 = 12 (matches 3BP phase space... approximately)
```

### Sundman Strategy for Three-Body

Several options for g(r):

```
'sum':     g = r₁₂ + r₂₃ + r₃₁  (balanced regularization)
'product': g = r₁₂ · r₂₃ · r₃₁  (aggressive near any collision)
'min':     g = min(r₁₂, r₂₃, r₃₁)  (focuses on nearest pair)
```

---

## Implementation

### Complete KS Transform

```python
class KSTransform:
    """Kustaanheimo-Stiefel transformation."""
    
    @staticmethod
    def forward(u):
        """Spinor → Position."""
        L = levi_civita_matrix(u)
        r_ext = L @ u
        return r_ext[:3]
    
    @staticmethod
    def inverse(r, branch='auto'):
        """Position → Spinor (choosing branch)."""
        x, y, z = r
        r_norm = np.linalg.norm(r)
        
        if branch == 'auto':
            branch = 'u3_zero' if x >= 0 else 'u2_zero'
        
        if branch == 'u3_zero':
            u0 = np.sqrt((r_norm + x) / 2)
            if u0 > 1e-10:
                u1 = y / (2 * u0)
                u2 = z / (2 * u0)
            else:
                u1, u2 = 0, 0
            u3 = 0
        else:  # u2_zero
            u1 = np.sqrt((r_norm - x) / 2)
            if u1 > 1e-10:
                u0 = y / (2 * u1)
                u3 = z / (2 * u1)
            else:
                u0, u3 = 0, 0
            u2 = 0
        
        return np.array([u0, u1, u2, u3])
    
    @staticmethod
    def velocity_to_momentum(u, v, mass=1.0):
        """Convert velocity to spinor momentum."""
        L = levi_civita_matrix(u)
        r_norm = np.dot(u, u)
        v_ext = np.append(v, 0)  # Extend to 4D
        p_u = 0.5 * r_norm * L.T @ v_ext / mass
        return p_u[:4]
    
    @staticmethod
    def momentum_to_velocity(u, p_u, mass=1.0):
        """Convert spinor momentum to velocity."""
        L = levi_civita_matrix(u)
        r_norm = np.dot(u, u)
        v_ext = 2 * mass * L @ p_u / r_norm
        return v_ext[:3]
    
    @staticmethod
    def bilinear_constraint(u, p_u):
        """Compute constraint Ξ = 0."""
        return u[0]*p_u[1] - u[1]*p_u[0] + u[2]*p_u[3] - u[3]*p_u[2]
```

### Pairwise KS for Three-Body

```python
class PairwiseKS:
    """KS transformation applied to all three body pairs."""
    
    def __init__(self, masses):
        self.masses = masses
        self.ks = KSTransform()
        
    def transform_positions(self, positions):
        """Transform 3 positions to 3 spinors."""
        r1, r2, r3 = positions
        
        r12 = r2 - r1
        r23 = r3 - r2
        r31 = r1 - r3
        
        u12 = self.ks.inverse(r12)
        u23 = self.ks.inverse(r23)
        u31 = self.ks.inverse(r31)
        
        return np.concatenate([u12, u23, u31])  # 12D
    
    def inverse_transform(self, spinors):
        """Transform 3 spinors back to positions."""
        u12 = spinors[:4]
        u23 = spinors[4:8]
        u31 = spinors[8:12]
        
        r12 = self.ks.forward(u12)
        r23 = self.ks.forward(u23)
        r31 = self.ks.forward(u31)
        
        # Reconstruct positions (COM at origin)
        # r1 + r12 = r2, r2 + r23 = r3, r3 + r31 = r1
        # With constraint: m1*r1 + m2*r2 + m3*r3 = 0
        
        return self._reconstruct_positions(r12, r23, r31)
    
    def closure_constraint(self, spinors):
        """Check r12 + r23 + r31 = 0."""
        u12, u23, u31 = spinors[:4], spinors[4:8], spinors[8:12]
        
        r12 = self.ks.forward(u12)
        r23 = self.ks.forward(u23)
        r31 = self.ks.forward(u31)
        
        return np.linalg.norm(r12 + r23 + r31)
```

### Time-Regularized Dynamics

```python
class TimeRegularizedDynamics:
    """Full time-regularized three-body dynamics."""
    
    def __init__(self, masses, sundman_strategy='sum'):
        self.masses = masses
        self.pairwise_ks = PairwiseKS(masses)
        self.strategy = sundman_strategy
        
    def compute_g(self, spinors):
        """Compute Sundman factor g = dt/ds."""
        r12 = np.dot(spinors[:4], spinors[:4])
        r23 = np.dot(spinors[4:8], spinors[4:8])
        r31 = np.dot(spinors[8:12], spinors[8:12])
        
        if self.strategy == 'sum':
            return r12 + r23 + r31
        elif self.strategy == 'product':
            return r12 * r23 * r31
        elif self.strategy == 'min':
            return min(r12, r23, r31)
    
    def equations_of_motion(self, s, state):
        """
        Equations in fictitious time s.
        
        State: (u12, u23, u31, p12, p23, p31, t, E)
        """
        spinors = state[:12]
        momenta = state[12:24]
        t = state[24]
        E = state[25]
        
        g = self.compute_g(spinors)
        
        # Spinor derivatives
        du_ds = self._compute_du(spinors, momenta, E)
        
        # Momentum derivatives
        dp_ds = self._compute_dp(spinors, momenta, E)
        
        # Time derivative
        dt_ds = g
        
        # Energy derivative (conserved)
        dE_ds = 0
        
        return np.concatenate([du_ds, dp_ds, [dt_ds, dE_ds]])
```

---

## References

- Kustaanheimo, P. & Stiefel, E. (1965). "Perturbation theory of Kepler motion based on spinor regularization"
- Stiefel, E. & Scheifele, G. (1971). *Linear and Regular Celestial Mechanics*
- Waldvogel, J. (2006). "Quaternions and the perturbed Kepler problem"
- `Science-Research-Docs/WP3 – Generalized KS.pdf`
