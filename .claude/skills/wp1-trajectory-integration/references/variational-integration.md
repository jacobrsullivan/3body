# Variational Integration Reference

Theory and implementation of variational equations for WP4 Morales-Ramis validation.

## Table of Contents

1. [Theory](#theory)
2. [Variational Equations](#variational-equations)
3. [Monodromy Matrix](#monodromy-matrix)
4. [Floquet Multipliers](#floquet-multipliers)
5. [Implementation](#implementation)
6. [Connection to Differential Galois Theory](#connection-to-differential-galois-theory)
7. [Numerical Considerations](#numerical-considerations)

---

## Theory

### The Linearized Flow

Given a reference trajectory x(t) satisfying ẋ = f(x), the variational equations describe how infinitesimal perturbations δx evolve:

```
d/dt(δx) = Df(x(t)) · δx
```

where Df is the Jacobian matrix of the vector field.

For Hamiltonian systems with H(q, p), this becomes:

```
d/dt(δq)   =  ∂²H/∂p∂q · δq + ∂²H/∂p² · δp
d/dt(δp)   = -∂²H/∂q² · δq - ∂²H/∂q∂p · δp
```

or in matrix form:

```
d/dt[δq]   [∂²H/∂p∂q   ∂²H/∂p² ] [δq]
    [δp] = [-∂²H/∂q²  -∂²H/∂q∂p] [δp]
```

### Fundamental Matrix

The fundamental matrix Φ(t) satisfies:

```
dΦ/dt = Df(x(t)) · Φ(t)
Φ(0) = I (identity)
```

Any perturbation evolves as:
```
δx(t) = Φ(t) · δx(0)
```

### Symplectic Structure

For Hamiltonian systems, Φ(t) is symplectic:

```
Φᵀ J Φ = J

where J = [0  I]
          [-I 0]
```

This implies det(Φ) = 1 at all times.

---

## Variational Equations

### CR3BP Variational Equations

For the CR3BP in rotating frame with state x = [q, p] = [x, y, z, vx, vy, vz]:

```python
def cr3bp_variational(t, state, mu):
    """
    Compute state derivative and variational matrix.

    Args:
        t: time
        state: (42,) = [x(6), Φ(36)] flattened state + fundamental matrix
        mu: mass ratio

    Returns:
        (42,) derivative of state + fundamental matrix
    """
    # Extract state and fundamental matrix
    x = state[:6]
    Phi = state[6:].reshape(6, 6)

    # Compute positions
    r1_vec = np.array([x[0] + mu, x[1], x[2]])
    r2_vec = np.array([x[0] - 1 + mu, x[1], x[2]])
    r1 = np.linalg.norm(r1_vec)
    r2 = np.linalg.norm(r2_vec)

    # State derivative (CR3BP dynamics)
    x_dot = cr3bp_dynamics(t, x, mu)

    # Hessian matrix components
    # Ω_xx, Ω_xy, Ω_xz, Ω_yy, Ω_yz, Ω_zz
    Omega_xx = 1 - (1-mu)/r1**3 - mu/r2**3 + 3*(1-mu)*(x[0]+mu)**2/r1**5 + 3*mu*(x[0]-1+mu)**2/r2**5
    Omega_yy = 1 - (1-mu)/r1**3 - mu/r2**3 + 3*(1-mu)*x[1]**2/r1**5 + 3*mu*x[1]**2/r2**5
    Omega_zz = -(1-mu)/r1**3 - mu/r2**3 + 3*(1-mu)*x[2]**2/r1**5 + 3*mu*x[2]**2/r2**5
    Omega_xy = 3*(1-mu)*(x[0]+mu)*x[1]/r1**5 + 3*mu*(x[0]-1+mu)*x[1]/r2**5
    Omega_xz = 3*(1-mu)*(x[0]+mu)*x[2]/r1**5 + 3*mu*(x[0]-1+mu)*x[2]/r2**5
    Omega_yz = 3*(1-mu)*x[1]*x[2]/r1**5 + 3*mu*x[1]*x[2]/r2**5

    # Build Jacobian matrix A = Df(x)
    A = np.array([
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1],
        [Omega_xx, Omega_xy, Omega_xz, 0, 2, 0],
        [Omega_xy, Omega_yy, Omega_yz, -2, 0, 0],
        [Omega_xz, Omega_yz, Omega_zz, 0, 0, 0]
    ])

    # Fundamental matrix derivative
    Phi_dot = A @ Phi

    # Combine
    return np.concatenate([x_dot, Phi_dot.flatten()])
```

---

## Monodromy Matrix

### Definition

For a periodic orbit with period T, the monodromy matrix M is:

```
M = Φ(T)
```

where Φ(T) is the fundamental matrix evaluated at t = T.

### Properties

1. **Symplectic**: MᵀJM = J, so det(M) = 1
2. **Eigenvalues in pairs**: If λ is an eigenvalue, so is 1/λ
3. **Two trivial eigenvalues**: λ = 1 (twice) for Hamiltonian periodic orbits

### Computing Monodromy

```python
from src.python.validation.variational_equations import VariationalIntegrator

# Create integrator
var_integrator = VariationalIntegrator(
    mu=mu,
    integrator='adaptive_symplectic',
    precision='qd'  # Tier 2 for WP4
)

# Find periodic orbit (or use known family)
from src.python.orbits.periodic_families import get_lyapunov_orbit
orbit_ic, period = get_lyapunov_orbit(mu=mu, lagrange_point='L1', Az=0.1)

# Integrate exactly one period
result = var_integrator.integrate(
    state0=orbit_ic,
    t_span=(0, period),
    compute_monodromy=True
)

# Extract monodromy matrix
M = result['monodromy']
print(f"Monodromy matrix shape: {M.shape}")  # (6, 6)

# Verify symplectic
J = np.array([[0, 0, 0, 1, 0, 0],
              [0, 0, 0, 0, 1, 0],
              [0, 0, 0, 0, 0, 1],
              [-1, 0, 0, 0, 0, 0],
              [0, -1, 0, 0, 0, 0],
              [0, 0, -1, 0, 0, 0]])

symplectic_error = np.max(np.abs(M.T @ J @ M - J))
print(f"Symplectic error: {symplectic_error:.2e}")  # Should be < 1e-20 for Tier 2
```

---

## Floquet Multipliers

### Definition

Floquet multipliers are the eigenvalues of the monodromy matrix:

```
det(M - λI) = 0
```

### Structure

For a 6D Hamiltonian system (3 DOF):
- 6 multipliers total
- Come in reciprocal pairs: (λ₁, 1/λ₁), (λ₂, 1/λ₂), (λ₃, 1/λ₃)
- Two are always λ = 1 (along orbit, energy conservation)

### Stability Classification

| Configuration | Stability | Interpretation |
|---------------|-----------|----------------|
| All |λᵢ| = 1 | Stable | Elliptic (oscillating perturbations) |
| Some |λᵢ| ≠ 1 | Unstable | Hyperbolic (exponential growth) |
| Complex λ with |λ| ≠ 1 | Complex unstable | Spiral + exponential |

### Computing Floquet Multipliers

```python
# From monodromy matrix
eigenvalues, eigenvectors = np.linalg.eig(M)

print("Floquet multipliers:")
for i, lam in enumerate(eigenvalues):
    print(f"  λ_{i+1} = {lam:.6f}, |λ| = {abs(lam):.6f}")

# Check reciprocal pairs
for i in range(3):
    product = eigenvalues[2*i] * eigenvalues[2*i + 1]
    print(f"  λ_{2*i+1} × λ_{2*i+2} = {product:.6f}")  # Should be ~1
```

### Lyapunov Exponents

The maximum Lyapunov exponent is related to Floquet multipliers:

```
σ_max = (1/T) × ln(max|λᵢ|)
```

For stable periodic orbits, σ_max = 0.

---

## Implementation

### Full Variational Integration

```python
from src.python.validation.variational_equations import VariationalIntegrator

class VariationalIntegrator:
    """
    Integrator for state + variational equations.
    """

    def __init__(self, mu, integrator='adaptive_symplectic', precision='double'):
        self.mu = mu
        self.integrator_type = integrator
        self.precision = precision

    def integrate(self, state0, t_span, compute_monodromy=False):
        """
        Integrate state and variational equations.

        Args:
            state0: (6,) initial state
            t_span: (t0, tf) time span
            compute_monodromy: If True, return monodromy matrix

        Returns:
            dict with 'times', 'states', 'phi', and optionally 'monodromy', 'floquet'
        """
        # Initialize augmented state: [x(6), Φ(36)]
        Phi0 = np.eye(6).flatten()
        augmented0 = np.concatenate([state0, Phi0])

        # Integrate
        if self.integrator_type == 'adaptive_symplectic':
            integrator = AdaptiveSymplecticIntegrator(
                mu=self.mu,
                order=6,
                tol=1e-20 if self.precision == 'qd' else 1e-14
            )
        else:
            integrator = IAS15Integrator(mu=self.mu)

        times, augmented_states = self._integrate_variational(
            augmented0, t_span, integrator
        )

        # Extract results
        states = augmented_states[:, :6]
        phi_flat = augmented_states[:, 6:]
        phi = phi_flat.reshape(-1, 6, 6)

        result = {
            'times': times,
            'states': states,
            'phi': phi,  # Fundamental matrix at each time
        }

        if compute_monodromy:
            result['monodromy'] = phi[-1]
            result['floquet'] = np.linalg.eigvals(phi[-1])

        return result
```

---

## Connection to Differential Galois Theory

### Morales-Ramis Theorem

**Statement**: If a Hamiltonian system is meromorphically integrable, then the identity component G⁰ of the differential Galois group of the variational equations along any particular solution is abelian.

**Contrapositive**: Non-abelian G⁰ ⟹ Non-integrable

### Application to 3BP

1. **Downstairs (reduced space)**:
   - Compute VE along periodic orbit (e.g., L4 Lagrange)
   - Apply Kovacic algorithm to determine Galois group
   - Expected: Non-abelian (SL(2,ℂ) subgroup)
   - Confirms classical non-integrability

2. **Upstairs (lifted space)**:
   - Lift periodic orbit to S¹ bundle or KS-Spinor space
   - Compute extended VE with lifted Hamiltonian
   - Apply Kovacic algorithm
   - If abelian: lift-integrability confirmed
   - If non-abelian: lift failed

### Monodromy → Galois Connection

The monodromy matrix M generates part of the differential Galois group:
- Monodromy group ⊆ Galois group
- Eigenvalue structure reveals algebraic constraints
- Floquet multipliers encode stability type

For the Morales-Ramis test:
```
Eigenvalues of M → Constraints on Galois group
  |λ| = 1 (elliptic) → Could be abelian
  |λ| ≠ 1 (hyperbolic) → Often non-abelian
  Complex λ → Rich algebraic structure
```

---

## Numerical Considerations

### Precision Requirements

| Analysis | Required Precision | Integrator |
|----------|-------------------|------------|
| Stability analysis | ΔC < 10⁻¹⁰ | IAS15 |
| Floquet multipliers | ΔC < 10⁻¹⁴ | AdaptiveSymplectic |
| Morales-Ramis test | ΔC < 10⁻²⁵ | AdaptiveSymplectic + QD |

### Symplectic Verification

Always verify symplectic structure:

```python
def verify_symplectic(Phi, tol=1e-12):
    """Verify fundamental matrix is symplectic."""
    J = np.block([
        [np.zeros((3,3)), np.eye(3)],
        [-np.eye(3), np.zeros((3,3))]
    ])

    error = np.max(np.abs(Phi.T @ J @ Phi - J))

    if error > tol:
        print(f"WARNING: Symplectic structure violated: {error:.2e}")
        return False
    return True
```

### Period Accuracy

For monodromy computation, period must be very accurate:

```python
def refine_period(state0, period_estimate, mu, tol=1e-12):
    """Refine orbital period using Poincaré section."""
    from scipy.optimize import brentq

    def crossing_condition(T):
        # Integrate to time T
        _, states = integrator.integrate(state0, (0, T))
        # Return y-coordinate (for y=0 section)
        return states[-1][1]

    # Bracket and refine
    period_refined = brentq(crossing_condition,
                           period_estimate * 0.99,
                           period_estimate * 1.01,
                           xtol=tol)
    return period_refined
```

### Regularization for Close Encounters

If periodic orbit passes near primaries:

```python
# Use Sundman-regularized variational equations
var_integrator = VariationalIntegrator(
    mu=mu,
    integrator='adaptive_symplectic',
    sundman_strategy='sum',
    precision='qd'
)
```

### Output for WP4

```python
def prepare_for_wp4(var_result, orbit_info):
    """Package variational results for WP4 Morales-Ramis test."""
    return {
        'orbit_type': orbit_info['type'],  # 'lyapunov', 'halo', etc.
        'period': orbit_info['period'],
        'mu': orbit_info['mu'],
        'monodromy_matrix': var_result['monodromy'],
        'floquet_multipliers': var_result['floquet'],
        'symplectic_error': verify_symplectic_error(var_result['monodromy']),
        'jacobi_drift': compute_jacobi_drift(var_result['states'], orbit_info['mu']),
    }
```
