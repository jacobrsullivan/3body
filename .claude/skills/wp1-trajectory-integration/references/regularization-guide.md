# Regularization Guide

Handling close encounters through coordinate transformations and time regularization.

## Table of Contents

1. [Close Encounter Problem](#close-encounter-problem)
2. [Sundman Time Transformation](#sundman-time-transformation)
3. [Kustaanheimo-Stiefel (KS) Transformation](#kustaanheimo-stiefel-ks-transformation)
4. [Automatic Switching](#automatic-switching)
5. [Implementation](#implementation)
6. [Best Practices](#best-practices)

---

## Close Encounter Problem

### The Issue

Near a primary body, the gravitational force diverges:

```
F ~ -k/r²  →  ∞  as r → 0
```

This causes:
1. **Timestep collapse**: Adaptive integrators take infinitesimally small steps
2. **Numerical overflow**: Force magnitudes exceed floating-point range
3. **Precision loss**: Subtractive cancellation in position updates
4. **Failure**: NaN or integration termination

### Detection

```python
def detect_close_encounter(state, mu, threshold=0.1):
    """
    Detect if trajectory is near a primary.
    
    Args:
        state: [x, y, z, vx, vy, vz] in rotating frame
        mu: mass ratio
        threshold: distance threshold (Hill radius units)
        
    Returns:
        (is_close, r_min, which_primary)
    """
    x, y, z = state[:3]
    
    # Distance to primary 1 (larger mass at -μ, 0, 0)
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    
    # Distance to primary 2 (smaller mass at 1-μ, 0, 0)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    
    r_min = min(r1, r2)
    which = 'm1' if r1 < r2 else 'm2'
    
    return r_min < threshold, r_min, which
```

### Critical Distances

| Distance | Behavior |
|----------|----------|
| r > 0.5 | Normal integration |
| 0.1 < r < 0.5 | Caution, reduce timestep |
| 0.01 < r < 0.1 | Switch to regularization |
| r < 0.01 | Regularization essential |
| r < 0.001 | May need Tier 2 + QD |

---

## Sundman Time Transformation

### Concept

Replace physical time t with fictitious time s:

```
dt/ds = g(r₁, r₂)
```

where g is a regularizing function that slows "time" near close encounters.

### Strategies

| Strategy | Function g | Behavior |
|----------|-----------|----------|
| `'sum'` | r₁ + r₂ | Balanced, general purpose |
| `'product'` | r₁ × r₂ | Aggressive, best for binary encounters |
| `'min'` | min(r₁, r₂) | Conservative, single-primary approach |

### Mathematics

The equations of motion transform:

```
Original:     dq/dt = ∂H/∂p,    dp/dt = -∂H/∂q
Regularized:  dq/ds = g·∂H/∂p,  dp/ds = -g·∂H/∂q
```

The regularized Hamiltonian becomes:

```
K = g(H - E) = 0  (on energy surface)
```

### Implementation

```python
class SundmanTransformation:
    """Sundman time transformation for regularization."""
    
    def __init__(self, strategy='sum', mu=0.0):
        self.strategy = strategy
        self.mu = mu
        
    def g(self, state):
        """Compute regularizing function g(r₁, r₂)."""
        x, y, z = state[:3]
        
        r1 = np.sqrt((x + self.mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + self.mu)**2 + y**2 + z**2)
        
        if self.strategy == 'sum':
            return r1 + r2
        elif self.strategy == 'product':
            return r1 * r2
        elif self.strategy == 'min':
            return min(r1, r2)
            
    def dt_ds(self, state):
        """Physical time increment per fictitious time."""
        return self.g(state)
        
    def transform_eom(self, state, eom):
        """Transform equations of motion."""
        g = self.g(state)
        return g * eom
```

---

## Kustaanheimo-Stiefel (KS) Transformation

### Overview

The KS transformation lifts 3D Cartesian coordinates to 4D spinor coordinates, regularizing the 1/r² singularity.

**Key insight**: The Kepler problem (singular) maps to a 4D harmonic oscillator (regular).

### Transformation

Position mapping (u → r):

```
x = u₀² - u₁² - u₂² + u₃²
y = 2(u₀u₁ - u₂u₃)
z = 2(u₀u₂ + u₁u₃)
r = |u|² = u₀² + u₁² + u₂² + u₃²
```

This can be written as r = L(u)·u where L(u) is the KS matrix:

```
L(u) = [u₀  -u₁  -u₂   u₃]
       [u₁   u₀  -u₃  -u₂]
       [u₂   u₃   u₀   u₁]
       [u₃  -u₂   u₁  -u₀]
```

### Bilinear Relation (Constraint)

The KS transformation introduces a constraint:

```
Ξ = u₁p₂ - u₂p₁ + u₃p₄ - u₄p₃ = 0
```

This is the **momentum map** for the S¹ gauge symmetry. Geometrically:
- The transformation is a **principal S¹ bundle** (Hopf fibration)
- The constraint restricts to the zero level set
- Physically: no motion in the fiber direction

### Implementation

```python
from src.python.regularization.ks_transform import KSTransform

class KSTransform:
    """Kustaanheimo-Stiefel transformation."""
    
    @staticmethod
    def cartesian_to_ks(r, v, primary='m2'):
        """
        Transform Cartesian (r, v) to KS (u, p_u).
        
        Args:
            r: (3,) position relative to primary
            v: (3,) velocity relative to primary
            primary: 'm1' or 'm2' (which primary to regularize)
            
        Returns:
            u: (4,) KS position spinor
            p_u: (4,) KS momentum spinor
        """
        x, y, z = r
        R = np.sqrt(x**2 + y**2 + z**2)
        
        # Choose gauge (u₃ = 0 or u₂ = 0)
        if x >= 0:
            u0 = np.sqrt((R + x) / 2)
            u1 = y / (2 * u0) if u0 > 1e-10 else 0
            u2 = z / (2 * u0) if u0 > 1e-10 else 0
            u3 = 0
        else:
            u1 = np.sqrt((R - x) / 2)
            u0 = y / (2 * u1) if u1 > 1e-10 else 0
            u2 = 0
            u3 = z / (2 * u1) if u1 > 1e-10 else 0
            
        u = np.array([u0, u1, u2, u3])
        
        # Transform velocity to KS momentum
        L = KSTransform.ks_matrix(u)
        p_u = 0.5 * L.T @ np.concatenate([v, [0]])
        
        return u, p_u[:4]
        
    @staticmethod
    def ks_to_cartesian(u, p_u):
        """Transform KS (u, p_u) back to Cartesian (r, v)."""
        L = KSTransform.ks_matrix(u)
        r = L @ u
        v = 2 * L @ p_u / np.dot(u, u)
        return r[:3], v[:3]
        
    @staticmethod
    def ks_matrix(u):
        """Build the KS transformation matrix L(u)."""
        u0, u1, u2, u3 = u
        return np.array([
            [u0, -u1, -u2,  u3],
            [u1,  u0, -u3, -u2],
            [u2,  u3,  u0,  u1],
            [u3, -u2,  u1, -u0]
        ])
```

### Regularized Hamiltonian

In KS coordinates with Sundman time (dt/ds = r = |u|²):

```
K = |p_u|² / (2|u|²) - k/|u|² - E = 0

For 3BP:
K = |p_u|² / 2 - (1-μ)/|u|² - μ·V_perturb - E·|u|²
```

The singularity is removed: when |u| → 0, all terms remain finite.

---

## Automatic Switching

### Concept

Dynamically switch between Cartesian and regularized coordinates based on proximity to primaries.

```python
from src.python.regularization.automatic_switching import AutomaticSwitcher

switcher = AutomaticSwitcher(
    mu=mu,
    switch_threshold=0.05,  # Switch to KS when r < 0.05
    hysteresis=0.1,         # Switch back when r > 0.1
    regularization='ks',    # 'ks' or 'sundman'
)

times, states = switcher.integrate(
    state0=initial_state,
    t_span=(0, 100),
    dt=0.1
)
```

### Hysteresis

Avoid oscillating between coordinate systems:

```
Switch to KS:    r < switch_threshold
Switch back:     r > switch_threshold + hysteresis
```

### State Matching

Ensure continuity at switching boundaries:

```python
def smooth_switch(state_cart, state_ks, blend_factor):
    """Smooth transition between coordinate systems."""
    # blend_factor = 0: pure Cartesian
    # blend_factor = 1: pure KS
    
    # Convert both to same representation
    state_cart_in_ks = cartesian_to_ks(state_cart)
    
    # Blend (in KS space for numerical stability)
    blended = (1 - blend_factor) * state_cart_in_ks + blend_factor * state_ks
    
    return blended
```

---

## Implementation

### Full Regularized Integrator

```python
class RegularizedIntegrator:
    """
    Integrator with automatic regularization for close encounters.
    """
    
    def __init__(self, mu, regularization='sundman', **kwargs):
        self.mu = mu
        self.regularization = regularization
        self.switch_threshold = kwargs.get('switch_threshold', 0.05)
        self.hysteresis = kwargs.get('hysteresis', 0.05)
        
        # Base integrators
        self.cart_integrator = AdaptiveSymplecticIntegrator(
            mu=mu,
            sundman_strategy='sum' if regularization == 'sundman' else None
        )
        self.ks_integrator = KSIntegrator(mu=mu) if regularization == 'ks' else None
        
    def integrate(self, state0, t_span, dt=0.1):
        """
        Integrate with automatic regularization switching.
        """
        t, tf = t_span
        state = state0.copy()
        
        times = [t]
        states = [state.copy()]
        
        in_ks = False
        
        while t < tf:
            # Check for close encounter
            is_close, r_min, which = detect_close_encounter(state, self.mu, self.switch_threshold)
            
            # Decide switching
            if is_close and not in_ks:
                state = self._switch_to_ks(state, which)
                in_ks = True
            elif not is_close and in_ks and r_min > self.switch_threshold + self.hysteresis:
                state = self._switch_to_cart(state, which)
                in_ks = False
                
            # Integrate one step
            if in_ks:
                t_new, state_new = self.ks_integrator.step(state, dt)
            else:
                t_new, state_new = self.cart_integrator.step(state, dt)
                
            t = t_new
            state = state_new
            
            times.append(t)
            states.append(state.copy() if not in_ks else self._ks_to_cart(state))
            
        return np.array(times), np.array(states)
```

---

## Best Practices

### 1. Choosing Regularization Method

| Scenario | Recommended |
|----------|-------------|
| Occasional close encounters | Sundman with 'sum' |
| Frequent binary encounters | KS transformation |
| Collision trajectories | KS + Tier 2 |
| Mixed dynamics | Automatic switching |

### 2. Threshold Selection

```python
# Rule of thumb for switch threshold
hill_radius = (mu / 3)**(1/3)  # Hill radius of m2
switch_threshold = 0.1 * hill_radius  # 10% of Hill radius

# For very small μ
if mu < 0.01:
    switch_threshold = max(switch_threshold, 0.01)
```

### 3. Validation

Always verify regularization quality:

```python
def validate_regularization(times, states, mu):
    """Validate regularized trajectory."""
    
    # Check Jacobi conservation
    C_values = [jacobi_constant(s, mu) for s in states]
    C_drift = max(C_values) - min(C_values)
    
    # Check for NaN
    has_nan = np.any(np.isnan(states))
    
    # Check minimum distance
    r_mins = []
    for s in states:
        _, r_min, _ = detect_close_encounter(s, mu, threshold=np.inf)
        r_mins.append(r_min)
    
    return {
        'jacobi_drift': C_drift,
        'has_nan': has_nan,
        'min_distance': min(r_mins),
        'passed': C_drift < 1e-14 and not has_nan
    }
```

### 4. Performance Tips

```python
# Pre-compute common quantities
class OptimizedRegularization:
    def __init__(self, mu):
        self.mu = mu
        self.one_minus_mu = 1 - mu
        self.primary1_pos = np.array([-mu, 0, 0])
        self.primary2_pos = np.array([1-mu, 0, 0])
        
    def distances(self, state):
        """Efficient distance computation."""
        pos = state[:3]
        r1 = np.linalg.norm(pos - self.primary1_pos)
        r2 = np.linalg.norm(pos - self.primary2_pos)
        return r1, r2
```

### 5. Error Handling

```python
def safe_regularized_integration(state0, t_span, mu, max_retries=3):
    """Integration with fallback strategies."""
    
    strategies = [
        {'sundman_strategy': 'sum', 'tol': 1e-14},
        {'sundman_strategy': 'product', 'tol': 1e-16},
        {'regularization': 'ks', 'tol': 1e-20},
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            integrator = RegularizedIntegrator(mu=mu, **strategy)
            times, states = integrator.integrate(state0, t_span)
            
            validation = validate_regularization(times, states, mu)
            if validation['passed']:
                return times, states
                
        except Exception as e:
            print(f"Strategy {i+1} failed: {e}")
            continue
            
    raise RuntimeError("All regularization strategies failed")
```
