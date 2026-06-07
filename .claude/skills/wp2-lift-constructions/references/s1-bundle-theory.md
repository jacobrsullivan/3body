# S¹ Bundle Theory

Mathematical foundations for the S¹ principal bundle lift.

## Table of Contents

1. [Principal Bundle Structure](#principal-bundle-structure)
2. [Extended Phase Space](#extended-phase-space)
3. [Extended Symplectic Form](#extended-symplectic-form)
4. [Lifted Hamiltonian](#lifted-hamiltonian)
5. [Fiber Momentum Conservation](#fiber-momentum-conservation)
6. [Integrability Analysis](#integrability-analysis)
7. [Implementation](#implementation)

---

## Principal Bundle Structure

### Construction

The S¹ bundle over shape space:

```
P = S × S¹
   ↓ π
   S (shape space)

Fiber: S¹ = U(1) (circle group)
```

### Coordinates

**Base (shape space)**: s = (r₁₂, r₂₃, r₃₁) ∈ S
**Fiber**: θ ∈ [0, 2π) ∈ S¹

**Total space point**: (s, θ) ∈ P

### Why S¹?

The mechanical connection A is an so(3)*-valued 1-form. For fixed angular momentum L:
- The residual symmetry is SO(2) ≅ S¹ (rotations about L)
- The connection projects to an ℝ-valued 1-form
- The curvature F = dA is the obstruction to integrability

By adding an S¹ fiber, we can "absorb" the connection:
```
New connection: Ã = dθ - A
Curvature: F̃ = dÃ = -dA = -F
```

If we work on P instead of S, the "magnetic term" can be eliminated.

---

## Extended Phase Space

### Cotangent Bundle of P

```
T*P = T*(S × S¹) ≅ T*S × T*S¹

Coordinates: (s, θ, p_s, p_θ)

Dimension: dim(T*P) = 2·dim(P) = 2·4 = 8
```

### Physical Interpretation

- **s**: Shape of the triangle
- **θ**: "Internal angle" or phase
- **p_s**: Momenta conjugate to shape
- **p_θ**: Momentum conjugate to phase (fiber momentum)

---

## Extended Symplectic Form

### Construction

The extended symplectic form incorporates the connection:

```
ω̃ = ω_can + dθ ∧ d(p_θ - L·A)
```

where:
- ω_can = dp_s ∧ ds + dp_θ ∧ dθ (canonical on T*P)
- A = A(s) is the mechanical connection 1-form
- L = |L| is the angular momentum magnitude

### Expanded Form

```
ω̃ = dp_s ∧ ds + dp_θ ∧ dθ + dθ ∧ d(p_θ - L·A)
  = dp_s ∧ ds + dp_θ ∧ dθ + dθ ∧ dp_θ - L·dθ ∧ dA
  = dp_s ∧ ds + dp_θ ∧ dθ + dθ ∧ dp_θ - L·dθ ∧ (∂A/∂s ds)
```

### Properties

1. **Closed**: dω̃ = 0 (since d² = 0)
2. **Non-degenerate**: det(ω̃) ≠ 0 (verify numerically)
3. **Reduces correctly**: π*ω̃|_{p_θ=L·A} = ω_red (reduced symplectic form)

### Verification

```python
def verify_extended_symplectic(omega_tilde, point):
    """Verify extended symplectic form properties."""

    # 1. Closure (compute dω̃ numerically)
    d_omega = compute_exterior_derivative(omega_tilde, point)
    closure_error = np.max(np.abs(d_omega))

    # 2. Non-degeneracy
    omega_matrix = omega_tilde.as_matrix(point)
    det = np.linalg.det(omega_matrix)

    return {
        'closed': closure_error < 1e-10,
        'nondegenerate': abs(det) > 1e-10,
        'closure_error': closure_error,
        'determinant': det
    }
```

---

## Lifted Hamiltonian

### Construction

The lifted Hamiltonian on T*P:

```
H̃(s, θ, p_s, p_θ) = H_red(s, p_s)
```

**Key property**: H̃ is **independent of θ**!

### Reduced Hamiltonian

The reduced Hamiltonian on shape space:

```
H_red(s, p_s) = ½ g^{ij}(s) p_i p_j + V_eff(s) + ⟨A(s), ṡ⟩ · L
```

where:
- g^{ij} = inverse kinetic metric on shape space
- V_eff = effective potential
- Third term = magnetic coupling

### Independence from θ

Why is H̃ independent of θ?
- θ is a "cyclic" or "ignorable" coordinate
- The shape dynamics don't depend on the overall phase
- This is the geometric content of rotational symmetry

---

## Fiber Momentum Conservation

### Noether's Theorem

Since ∂H̃/∂θ = 0, by Hamilton's equations:

```
ṗ_θ = -∂H̃/∂θ = 0
```

Therefore **p_θ is conserved**!

### Physical Meaning

p_θ represents the "momentum in the fiber direction"—a measure of how the internal phase evolves relative to the shape dynamics.

If p_θ is truly conserved, it provides a **new integral of motion** beyond E and L.

### Testing Conservation

```python
def test_fiber_momentum_conservation(times, states, tolerance=1e-12):
    """
    Test if p_θ is conserved along trajectory.
    """
    p_thetas = [state[7] for state in states]  # p_θ at index 7

    drift = max(p_thetas) - min(p_thetas)
    mean_p_theta = np.mean(p_thetas)

    conserved = drift < tolerance

    return {
        'conserved': conserved,
        'drift': drift,
        'relative_drift': drift / abs(mean_p_theta) if mean_p_theta != 0 else drift,
        'mean_value': mean_p_theta
    }
```

---

## Integrability Analysis

### Liouville Integrability

For a 2n-dimensional system to be Liouville integrable, we need:
1. n independent integrals of motion
2. In involution: {I_i, I_j} = 0

For T*P (8D, n = 4):
- Need 4 integrals
- Have: E (energy), L (angular momentum), p_θ (fiber momentum)
- Need 1 more, OR show these are sufficient

### Dimensional Consideration

Wait—we have n = 4 but only 3 obvious integrals!

However, note:
- Original reduced system was 6D shape phase space
- With 2 integrals (E, L), it was not integrable
- Lifted to 8D with 3 integrals → closer to integrability

**Question**: Does lift create a 4th integral, or should we count differently?

### Counting Degrees of Freedom

Alternative view:
- The S¹ lift adds 1 DOF (θ) but also 1 integral (p_θ)
- Net effect: same as before in terms of integrability fraction
- BUT: the new system may have hidden structure

### Involution Check

```python
def test_involution(integrals, omega_tilde, points):
    """
    Test if integrals are in involution: {I_i, I_j} = 0.

    Args:
        integrals: List of (name, function) pairs
        omega_tilde: Extended symplectic form
        points: Sample points for numerical test
    """
    n = len(integrals)
    poisson_matrix = np.zeros((n, n))

    for i, (name_i, I_i) in enumerate(integrals):
        for j, (name_j, I_j) in enumerate(integrals):
            if i >= j:
                continue

            # Compute {I_i, I_j} = ω̃(X_{I_i}, X_{I_j})
            brackets = []
            for point in points:
                bracket = poisson_bracket(I_i, I_j, omega_tilde, point)
                brackets.append(bracket)

            poisson_matrix[i, j] = np.mean(brackets)
            poisson_matrix[j, i] = -poisson_matrix[i, j]

    max_bracket = np.max(np.abs(poisson_matrix))
    in_involution = max_bracket < 1e-10

    return {
        'in_involution': in_involution,
        'poisson_matrix': poisson_matrix,
        'max_bracket': max_bracket
    }
```

---

## Implementation

### S¹ Bundle Class

```python
class S1Bundle:
    """S¹ principal bundle over shape space."""

    def __init__(self, masses, angular_momentum):
        self.masses = masses
        self.L = angular_momentum
        self.connection = MechanicalConnection(masses)

    def lift_state(self, shape_state, theta=0.0):
        """
        Lift shape space state to bundle.

        Args:
            shape_state: (6,) = [s, p_s] on shape space
            theta: Initial fiber coordinate

        Returns:
            (8,) = [s, theta, p_s, p_theta] on T*P
        """
        s = shape_state[:3]
        p_s = shape_state[3:6]

        # Compute fiber momentum
        # For consistency: p_θ = L · A(s) at equilibrium
        A = self.connection.components(s)
        p_theta = self.L * np.dot(A, p_s) / np.dot(p_s, p_s) if np.any(p_s) else 0

        return np.concatenate([s, [theta], p_s, [p_theta]])

    def project(self, lifted_state):
        """Project from bundle to shape space."""
        s = lifted_state[:3]
        p_s = lifted_state[4:7]
        return np.concatenate([s, p_s])

    def extended_hamiltonian(self, lifted_state):
        """Compute H̃(s, θ, p_s, p_θ)."""
        shape_state = self.project(lifted_state)
        return self.reduced_hamiltonian(shape_state)

    def create_integrator(self):
        """Create integrator for lifted dynamics."""
        return S1BundleIntegrator(self)
```

### Extended Symplectic Form

```python
class ExtendedSymplecticForm:
    """Extended symplectic form on T*P."""

    def __init__(self, masses, angular_momentum):
        self.masses = masses
        self.L = angular_momentum
        self.connection = MechanicalConnection(masses)

    def evaluate(self, point, v1, v2):
        """
        Evaluate ω̃(v1, v2) at point.

        Args:
            point: (8,) = [s, θ, p_s, p_θ]
            v1, v2: Tangent vectors at point
        """
        s = point[:3]

        # Canonical part
        omega_can = self._canonical_part(v1, v2)

        # Connection correction
        dA = self.connection.compute_derivative(s)
        correction = self.L * self._connection_correction(point, v1, v2, dA)

        return omega_can + correction

    def as_matrix(self, point):
        """Return ω̃ as 8×8 antisymmetric matrix."""
        omega = np.zeros((8, 8))

        # Fill in using evaluate on basis vectors
        for i in range(8):
            for j in range(i+1, 8):
                ei = np.zeros(8)
                ei[i] = 1
                ej = np.zeros(8)
                ej[j] = 1
                omega[i, j] = self.evaluate(point, ei, ej)
                omega[j, i] = -omega[i, j]

        return omega
```

---

## References

- Marsden, J.E. & Weinstein, A. (1974). "Reduction of symplectic manifolds with symmetry"
- Montgomery, R. (1988). "The connection whose holonomy is the classical adiabatic angles"
- Cushman, R. & Bates, L. (1997). *Global Aspects of Classical Integrable Systems*
- `Science-Research-Docs/WP2 – 2-Body Kepler + KS.pdf`
