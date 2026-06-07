# Coordinate Systems Reference

Coordinate systems and transformations used in CR3BP integration.

## Table of Contents

1. [Overview](#overview)
2. [Rotating (Synodic) Frame](#rotating-synodic-frame)
3. [Inertial (Barycentric) Frame](#inertial-barycentric-frame)
4. [KS Regularized Coordinates](#ks-regularized-coordinates)
5. [Jacobi Coordinates](#jacobi-coordinates)
6. [Transformations](#transformations)
7. [Implementation](#implementation)

---

## Overview

| Coordinate System | Dimension | Use Case | Singularity |
|-------------------|-----------|----------|-------------|
| **Rotating** | 6D | Standard CR3BP | At primaries |
| **Inertial** | 6D | Physical interpretation | At primaries |
| **KS (u, p_u)** | 8D | Close encounters | None |
| **Jacobi** | 6D | Reduction analysis | At collisions |

---

## Rotating (Synodic) Frame

### Definition

The rotating frame co-rotates with the two primaries, which remain fixed on the x-axis.

**Origin**: Barycenter of m₁ and m₂
**x-axis**: Points from m₁ toward m₂
**z-axis**: Normal to orbital plane (along angular momentum)
**y-axis**: Completes right-handed system

### Primary Positions

```
m₁ (larger): (-μ, 0, 0)
m₂ (smaller): (1-μ, 0, 0)

where μ = m₂/(m₁ + m₂)
```

### State Vector

```
state = [x, y, z, vx, vy, vz]

Position: (x, y, z)
Velocity: (vx, vy, vz) = (ẋ, ẏ, ż) in rotating frame
```

### Equations of Motion

```
ẍ - 2ẏ = ∂Ω/∂x
ÿ + 2ẋ = ∂Ω/∂y
z̈      = ∂Ω/∂z

Ω(x,y,z) = (x² + y²)/2 + (1-μ)/r₁ + μ/r₂ + μ(1-μ)/2

r₁ = √[(x+μ)² + y² + z²]
r₂ = √[(x-1+μ)² + y² + z²]
```

The Coriolis terms (±2ẏ, ∓2ẋ) arise from frame rotation.

### Jacobi Constant

```
C = 2Ω - (ẋ² + ẏ² + ż²)
```

This is the only known integral of motion in the CR3BP.

---

## Inertial (Barycentric) Frame

### Definition

Fixed inertial frame centered at the barycenter.

**Origin**: Barycenter (same as rotating)
**X-axis**: Fixed direction (e.g., vernal equinox)
**Z-axis**: Normal to orbital plane
**Y-axis**: Completes right-handed system

### Primary Positions (Time-Dependent)

```
m₁: R₁(t) = (-μ·cos(t), -μ·sin(t), 0)
m₂: R₂(t) = ((1-μ)·cos(t), (1-μ)·sin(t), 0)
```

### State Vector

```
State_inertial = [X, Y, Z, VX, VY, VZ]

Position: (X, Y, Z) in inertial frame
Velocity: (VX, VY, VZ) = (Ẋ, Ẏ, Ż) in inertial frame
```

### Equations of Motion

```
Ẍ = -(1-μ)(X - X₁)/r₁³ - μ(X - X₂)/r₂³
Ÿ = -(1-μ)(Y - Y₁)/r₁³ - μ(Y - Y₂)/r₂³
Z̈ = -(1-μ)Z/r₁³ - μZ/r₂³

r₁ = √[(X-X₁)² + (Y-Y₁)² + Z²]
r₂ = √[(X-X₂)² + (Y-Y₂)² + Z²]
```

No Coriolis terms, but time-dependent potential.

---

## KS Regularized Coordinates

### Definition

4D spinor coordinates that regularize the 1/r singularity.

**Position spinor**: u = (u₀, u₁, u₂, u₃) ∈ ℝ⁴
**Momentum spinor**: p_u = (p₀, p₁, p₂, p₃) ∈ ℝ⁴
**Fictitious time**: s (dt/ds = |u|²)

### State Vector

```
State_KS = [u₀, u₁, u₂, u₃, p₀, p₁, p₂, p₃]

or extended: [u, p_u, t, E] including physical time and energy
```

### Mapping to Cartesian

```
x = u₀² - u₁² - u₂² + u₃²
y = 2(u₀u₁ - u₂u₃)
z = 2(u₀u₂ + u₁u₃)
r = |u|² = u₀² + u₁² + u₂² + u₃²
```

### Constraint

The bilinear relation must be satisfied:

```
Ξ = u₀p₁ - u₁p₀ + u₂p₃ - u₃p₂ = 0
```

### Regularized Hamiltonian

```
K = |p_u|²/(2|u|²) - U_eff - E = 0

where U_eff includes primary potential and perturbations
```

---

## Jacobi Coordinates

### Definition

Hierarchical coordinates useful for reduction and analysis.

**For 3-body**:
- r₁₂: Vector from body 1 to body 2
- r₃: Vector from COM(1,2) to body 3

### State Vector

```
State_Jacobi = [r₁₂, r₃, p₁₂, p₃]

r₁₂ = (x₁₂, y₁₂, z₁₂): relative position 1→2
r₃ = (x₃, y₃, z₃): position of 3 relative to COM(1,2)
p₁₂, p₃: conjugate momenta
```

### Reduced Masses

```
μ₁₂ = m₁m₂/(m₁ + m₂)
μ₃ = m₃(m₁ + m₂)/(m₁ + m₂ + m₃)
```

### Use Cases

- Symplectic reduction
- Shape space analysis
- WP2 geometric foundations

---

## Transformations

### Rotating → Inertial

```python
def rotating_to_inertial(state_rot, t, mu):
    """
    Transform from rotating to inertial frame.

    Args:
        state_rot: [x, y, z, vx, vy, vz] in rotating frame
        t: time (rotation angle = t in normalized units)
        mu: mass ratio

    Returns:
        state_inert: [X, Y, Z, VX, VY, VZ] in inertial frame
    """
    x, y, z, vx, vy, vz = state_rot

    # Rotation matrix (frame rotates with ω = 1)
    cos_t = np.cos(t)
    sin_t = np.sin(t)

    # Position transformation
    X = x * cos_t - y * sin_t
    Y = x * sin_t + y * cos_t
    Z = z

    # Velocity transformation (includes frame rotation ω×r)
    # v_inertial = R(t) · v_rotating + ω × R(t) · r
    VX = (vx - y) * cos_t - (vy + x) * sin_t
    VY = (vx - y) * sin_t + (vy + x) * cos_t
    VZ = vz

    return np.array([X, Y, Z, VX, VY, VZ])
```

### Inertial → Rotating

```python
def inertial_to_rotating(state_inert, t, mu):
    """
    Transform from inertial to rotating frame.
    """
    X, Y, Z, VX, VY, VZ = state_inert

    cos_t = np.cos(t)
    sin_t = np.sin(t)

    # Position transformation (inverse rotation)
    x = X * cos_t + Y * sin_t
    y = -X * sin_t + Y * cos_t
    z = Z

    # Velocity transformation
    # v_rotating = R(-t) · v_inertial - ω × r_rotating
    vx = VX * cos_t + VY * sin_t + y
    vy = -VX * sin_t + VY * cos_t - x
    vz = VZ

    return np.array([x, y, z, vx, vy, vz])
```

### Cartesian → KS

```python
def cartesian_to_ks(r, v, which_primary='m2'):
    """
    Transform Cartesian to KS coordinates.

    Args:
        r: (3,) position relative to primary
        v: (3,) velocity relative to primary
        which_primary: 'm1' or 'm2'

    Returns:
        u: (4,) KS position spinor
        p_u: (4,) KS momentum spinor
    """
    x, y, z = r
    R = np.sqrt(x**2 + y**2 + z**2)

    # Gauge choice: set u₃ = 0 when x ≥ 0, else u₂ = 0
    if x >= 0:
        s = np.sqrt(R + x)
        u = np.array([
            s / np.sqrt(2),
            y / (np.sqrt(2) * s) if s > 1e-10 else 0,
            z / (np.sqrt(2) * s) if s > 1e-10 else 0,
            0
        ])
    else:
        s = np.sqrt(R - x)
        u = np.array([
            y / (np.sqrt(2) * s) if s > 1e-10 else 0,
            s / np.sqrt(2),
            0,
            z / (np.sqrt(2) * s) if s > 1e-10 else 0
        ])

    # Velocity → KS momentum via L(u) matrix
    L = ks_matrix(u)
    v_ext = np.array([v[0], v[1], v[2], 0])
    p_u = 0.5 * R * L.T @ v_ext

    return u, p_u
```

### KS → Cartesian

```python
def ks_to_cartesian(u, p_u):
    """
    Transform KS to Cartesian coordinates.
    """
    L = ks_matrix(u)

    # Position
    r_ext = L @ u
    r = r_ext[:3]

    # Velocity
    R = np.dot(u, u)
    v_ext = 2 * L @ p_u / R
    v = v_ext[:3]

    return r, v

def ks_matrix(u):
    """Build the KS matrix L(u)."""
    u0, u1, u2, u3 = u
    return np.array([
        [u0, -u1, -u2,  u3],
        [u1,  u0, -u3, -u2],
        [u2,  u3,  u0,  u1],
        [u3, -u2,  u1, -u0]
    ])
```

---

## Implementation

### Coordinate Manager

```python
from src.python.utils.coordinates import CoordinateManager

class CoordinateManager:
    """Unified coordinate transformation handler."""

    def __init__(self, mu):
        self.mu = mu

    def transform(self, state, from_system, to_system, t=None):
        """
        Transform state between coordinate systems.

        Args:
            state: state vector in source system
            from_system: 'rotating', 'inertial', 'ks', 'jacobi'
            to_system: target system
            t: time (required for rotating ↔ inertial)

        Returns:
            state in target system
        """
        # Build transformation chain
        if from_system == to_system:
            return state.copy()

        if from_system == 'rotating' and to_system == 'inertial':
            return rotating_to_inertial(state, t, self.mu)

        if from_system == 'inertial' and to_system == 'rotating':
            return inertial_to_rotating(state, t, self.mu)

        if from_system == 'rotating' and to_system == 'ks':
            # Extract relative position to primary
            r_rel, v_rel = self._relative_to_primary(state, 'm2')
            u, p_u = cartesian_to_ks(r_rel, v_rel, 'm2')
            return np.concatenate([u, p_u])

        if from_system == 'ks' and to_system == 'rotating':
            u, p_u = state[:4], state[4:8]
            r_rel, v_rel = ks_to_cartesian(u, p_u)
            return self._from_relative(r_rel, v_rel, 'm2')

        raise ValueError(f"Unknown transformation: {from_system} → {to_system}")

    def _relative_to_primary(self, state, primary):
        """Get position/velocity relative to a primary."""
        x, y, z, vx, vy, vz = state

        if primary == 'm1':
            r_rel = np.array([x + self.mu, y, z])
        else:  # m2
            r_rel = np.array([x - (1 - self.mu), y, z])

        v_rel = np.array([vx, vy, vz])
        return r_rel, v_rel

    def _from_relative(self, r_rel, v_rel, primary):
        """Convert back from relative coordinates."""
        if primary == 'm1':
            x = r_rel[0] - self.mu
        else:
            x = r_rel[0] + (1 - self.mu)

        return np.array([x, r_rel[1], r_rel[2], v_rel[0], v_rel[1], v_rel[2]])
```

### Trajectory Conversion

```python
def convert_trajectory(times, states, from_system, to_system, mu):
    """
    Convert entire trajectory between coordinate systems.

    Args:
        times: (N,) time array
        states: (N, d) state array
        from_system, to_system: coordinate system names
        mu: mass ratio

    Returns:
        (N, d') converted states
    """
    manager = CoordinateManager(mu)

    converted = []
    for t, state in zip(times, states):
        state_conv = manager.transform(state, from_system, to_system, t=t)
        converted.append(state_conv)

    return np.array(converted)
```

### Multi-Coordinate Output

```python
def integrate_multicoord(state0, t_span, dt, mu, systems=['rotating', 'inertial']):
    """
    Integrate and output in multiple coordinate systems.
    """
    # Integrate in rotating frame
    integrator = IAS15Integrator(mu=mu)
    times, states_rot = integrator.integrate(state0, t_span, dt)

    # Convert to other systems
    result = {
        'times': times,
        'rotating': states_rot,
    }

    if 'inertial' in systems:
        result['inertial'] = convert_trajectory(
            times, states_rot, 'rotating', 'inertial', mu
        )

    if 'ks' in systems:
        result['ks'] = convert_trajectory(
            times, states_rot, 'rotating', 'ks', mu
        )

    return result
```

---

## Physical Constants

### Common Mass Ratios

| System | μ = m₂/(m₁+m₂) | Notes |
|--------|----------------|-------|
| Earth-Moon | 0.012150585609624 | Standard test |
| Sun-Jupiter | 9.5388e-4 | Planet-dominated |
| Sun-Earth | 3.0035e-6 | Very small μ |
| Equal masses | 0.5 | Symmetric |
| Test (μ→0) | 0.001 | Near-Kepler |

### Lagrange Points (Rotating Frame)

```python
def lagrange_points(mu):
    """Compute Lagrange point positions."""
    # L1: Between m1 and m2
    # Solve: x - (1-μ)/(x+μ)² + μ/(x-1+μ)² = 0

    # L2: Beyond m2
    # L3: Beyond m1

    # L4, L5: Equilateral triangle
    L4 = np.array([0.5 - mu, np.sqrt(3)/2, 0])
    L5 = np.array([0.5 - mu, -np.sqrt(3)/2, 0])

    return {'L1': L1, 'L2': L2, 'L3': L3, 'L4': L4, 'L5': L5}
```
