---
name: wp1-trajectory-integration
description: >
  High-precision numerical integration for CR3BP trajectories. Use when: 
  (1) integrating three-body trajectories, (2) selecting integrators (IAS15, 
  Yoshida8, AdaptiveSymplectic), (3) computing Jacobi constants, (4) setting up 
  precision tiers, (5) handling close encounters with regularization, (6) computing 
  variational equations for WP4 validation, (7) transforming between coordinate 
  systems (rotating, inertial, KS), (8) estimating orbital periods, (9) configuring 
  timestep control, or (10) preparing trajectories for downstream WP2/WP3/WP4 
  analysis. Triggers on requests involving orbit integration, timestep control, 
  symplectic methods, trajectory generation, variational equations, monodromy matrix, 
  Floquet multipliers, dense output, Sundman transformation, or coordinate conversion.
---

# WP1 Trajectory Integration

Numerical integration workflows for the Circular Restricted Three-Body Problem (CR3BP).

## Integrator Selection

Choose integrator based on precision requirements and orbit characteristics:

| Integrator | Precision (ΔC) | Speed | Symplectic | Use Case |
|------------|----------------|-------|------------|----------|
| **IAS15** | ~10⁻¹⁵ | 50 periods/s | No (adaptive) | Tier 1 catalogue (10⁵ orbits) |
| **Yoshida8** | ~10⁻⁸ | 250 periods/s | Yes | Long-term stability |
| **AdaptiveSymplectic** | ~10⁻²⁵ | 10-20 periods/s | Yes | Tier 2 extreme precision |

### Decision Tree

```
Start
  │
  ├── Need symplectic structure preservation?
  │     ├── Yes, need ΔC < 10⁻²⁵? → AdaptiveSymplectic + QD
  │     ├── Yes, need speed over precision? → Yoshida8
  │     └── No → Continue
  │
  ├── Close encounters expected (r < 0.1)?
  │     ├── Yes → AdaptiveSymplectic with Sundman
  │     └── No → Continue
  │
  ├── Need ΔC < 10⁻¹⁴?
  │     ├── Yes → IAS15 (Tier 1)
  │     └── No → Yoshida8 (fastest)
  │
  └── Computing variational equations?
        ├── Yes → AdaptiveSymplectic (Tier 2)
        └── No → IAS15 (Tier 1)
```

## Quick Start

```python
from src.python.integrators.ias15 import IAS15Integrator
from src.python.utils.dynamics import jacobi_constant
import numpy as np

# Earth-Moon mass ratio
mu = 0.012150585609624

# Initial state: [x, y, z, vx, vy, vz] in rotating frame
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])

# Estimate orbital period
T_period = estimate_period(state0, mu)

# Integrate for 100 periods
integrator = IAS15Integrator(mu=mu)
times, states = integrator.integrate(
    state0=state0,
    t_span=(0, 100 * T_period),
    dt=T_period / 100  # 100 points per period
)

# Verify Jacobi constant conservation
C_values = [jacobi_constant(s, mu) for s in states]
C_drift = max(C_values) - min(C_values)
print(f"Jacobi drift: {C_drift:.2e}")  # Should be < 1e-14 for Tier 1
```

## Integrator Workflows

### IAS15 (15th-Order Adaptive Radau)

**Location**: `src/python/integrators/ias15.py`

Excellent energy conservation with automatic timestep adaptation. Non-symplectic but achieves ~10⁻¹⁵ relative energy drift.

```python
from src.python.integrators.ias15 import IAS15Integrator

integrator = IAS15Integrator(
    mu=mu,
    epsilon=1e-9,       # Convergence parameter (default)
)
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 100),    # Time span
    dt=0.1              # Output timestep (internal is adaptive)
)
```

**Key Characteristics**:
- Automatic internal timestep control
- 15th-order accuracy (Gauss-Radau quadrature)
- Handles moderate close encounters
- Best for: Tier 1 exploration, general cataloguing

### Yoshida8 (8th-Order Symplectic)

**Location**: `src/python/integrators/yoshida8.py`

Preserves Hamiltonian structure exactly. Best for long-term stability studies.

```python
from src.python.integrators.yoshida8 import Yoshida8Integrator

integrator = Yoshida8Integrator(mu=mu)
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 1000),
    dt=0.01             # Fixed timestep (critical for symplectic)
)
```

**Timestep Selection for Yoshida8**:
```
dt = T_period / N  where:
  - N ≥ 100 for Tier 1 (ΔC ~ 10⁻⁸)
  - N ≥ 500 for better precision
  - N ≥ 1000 for periodic orbit analysis
```

### AdaptiveSymplectic (Tier 2)

**Location**: `src/python/integrators/adaptive_symplectic.py`

Symplectic with Sundman time transformation for close encounters. Required for Tier 2.

```python
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator

integrator = AdaptiveSymplecticIntegrator(
    mu=mu,
    order=6,                    # Composition order (4 or 6)
    tol=1e-20,                  # Error tolerance
    sundman_strategy='sum',     # Time regularization
    min_dt=1e-10,               # Minimum timestep
    max_dt=0.01,                # Maximum timestep
)
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 100),
    max_steps=10000000
)
```

**Sundman Strategies**:

| Strategy | Formula | Best For |
|----------|---------|----------|
| `'sum'` | g = 1/(r₁ + r₂) | Balanced, general use |
| `'product'` | g = 1/(r₁ · r₂) | Binary close encounters |
| `'min'` | g = 1/min(r₁, r₂) | Single primary approach |

See `references/integrator-details.md` for complete configuration guide.

## Period Estimation

Accurate period estimation is critical for setting integration times:

```python
def estimate_period(state0, mu, method='frequency'):
    """
    Estimate orbital period from initial conditions.
    
    Methods:
      'frequency': Linearized frequency near Lagrange points
      'velocity': Kepler-like estimate from orbital velocity
      'numerical': Short integration + Poincaré crossing
    """
    x, y, z, vx, vy, vz = state0
    
    if method == 'velocity':
        # Simple Kepler-like estimate
        r = np.sqrt(x**2 + y**2 + z**2)
        v = np.sqrt(vx**2 + vy**2 + vz**2)
        a_eff = 2/r - v**2  # Effective semi-major axis
        if a_eff > 0:
            return 2 * np.pi * np.sqrt(1/a_eff**3)
        else:
            return 2 * np.pi  # Default for hyperbolic
    
    elif method == 'numerical':
        # Short integration to detect Poincaré crossing
        from src.python.utils.poincare import PoincareSection
        section = PoincareSection.create_standard_section('y_zero', mu=mu)
        # ... detect first return
        
    elif method == 'frequency':
        # Jacobi constant based estimate
        C = jacobi_constant(state0, mu)
        omega_eff = np.sqrt(max(C - 2.5, 0.1))
        return 2 * np.pi / omega_eff

# Usage
T = estimate_period(state0, mu)
t_span = (0, 100 * T)  # 100 periods
```

## Integration Time Selection

| Use Case | Periods | Tier | Notes |
|----------|---------|------|-------|
| Quick screening | 10-50 | 1 | Parameter exploration |
| Chaos classification | 100 | 1 | MEGNO/FLI computation |
| Standard catalogue | 100-500 | 1 | WP3 ML training |
| Periodic orbit analysis | 1-10 | 2 | Exact period required |
| WP4 validation | 1000+ | 2 | Morales-Ramis test |
| Long-time stability | 10000+ | 2 | Shadow Hamiltonian analysis |

## Variational Equations

For WP4 Morales-Ramis validation, integrate state + variational equations simultaneously:

```python
from src.python.validation.variational_equations import VariationalIntegrator

# Create variational integrator
var_integrator = VariationalIntegrator(
    mu=mu,
    integrator='adaptive_symplectic',
    precision='qd'  # Double-double for Tier 2
)

# Integrate state + fundamental matrix
result = var_integrator.integrate(
    state0=state0,
    t_span=(0, T_period),      # One period for monodromy
    compute_monodromy=True,    # Extract monodromy matrix at t=T
)

# Results
times = result['times']
states = result['states']                    # (N, 6) trajectory
fundamental_matrices = result['phi']         # (N, 6, 6) Φ(t)
monodromy_matrix = result['monodromy']       # (6, 6) M = Φ(T)
floquet_multipliers = result['floquet']      # (6,) eigenvalues of M
```

**Monodromy Matrix Properties**:
- Symplectic: det(M) = 1 (verify for validation)
- Floquet multipliers come in reciprocal pairs: (λ, 1/λ)
- |λ| = 1 → stable, |λ| ≠ 1 → unstable
- Connects to Differential Galois Group in Morales-Ramis theory

See `references/variational-integration.md` for complete theory.

## Close Encounter Handling

### Detection

```python
def detect_close_encounter(state, mu, threshold=0.1):
    """Check for close encounter with primaries."""
    x, y, z = state[:3]
    
    # Distance to primary 1 (at -μ, 0, 0)
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    
    # Distance to primary 2 (at 1-μ, 0, 0)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    
    return min(r1, r2) < threshold, min(r1, r2)

# Usage during integration
for state in trajectory:
    is_close, r_min = detect_close_encounter(state, mu)
    if is_close:
        print(f"Close encounter: r_min = {r_min:.4f}")
```

### Automatic Regularization Switching

```python
from src.python.regularization.automatic_switching import AutomaticSwitcher

# Configure automatic Cartesian ↔ KS switching
switcher = AutomaticSwitcher(
    mu=mu,
    switch_threshold=0.01,  # Switch to KS when r < 0.01
    hysteresis=0.02,        # Switch back when r > 0.02
)

# Integrate with automatic switching
times, states = switcher.integrate(
    state0=initial_state,
    t_span=(0, 100),
    dt=0.1
)
```

See `references/regularization-guide.md` for KS transform details.

## Coordinate Transformations

### Available Systems

| System | Description | Use Case |
|--------|-------------|----------|
| **Rotating** | Synodic (co-rotating) | Standard CR3BP |
| **Inertial** | Barycentric fixed | Physical interpretation |
| **KS Regularized** | Spinor coordinates | Close encounters |

### Transformations

```python
from src.python.utils.coordinates import (
    rotating_to_inertial,
    inertial_to_rotating,
    cartesian_to_ks,
    ks_to_cartesian
)

# Rotating → Inertial
state_inertial = rotating_to_inertial(state_rotating, t, mu)

# Cartesian → KS (for regularization)
u, p_u = cartesian_to_ks(r, v, primary='m2')

# Full trajectory conversion
states_inertial = np.array([
    rotating_to_inertial(s, t, mu) 
    for s, t in zip(states, times)
])
```

See `references/coordinate-systems.md` for transformation equations.

## CR3BP Dynamics

**Location**: `src/python/utils/dynamics.py`

### Equations of Motion (Rotating Frame)

```
ẍ - 2ẏ = ∂Ω/∂x
ÿ + 2ẋ = ∂Ω/∂y
z̈      = ∂Ω/∂z

Ω(x,y,z) = (x² + y²)/2 + (1-μ)/r₁ + μ/r₂ + μ(1-μ)/2

r₁ = √[(x+μ)² + y² + z²]      (distance to m₁)
r₂ = √[(x-1+μ)² + y² + z²]    (distance to m₂)
```

### Jacobi Constant

The only known integral of motion in the CR3BP:

```python
from src.python.utils.dynamics import jacobi_constant, cr3bp_dynamics

# Equations of motion (for custom integrators)
state_dot = cr3bp_dynamics(t, state, mu)

# Jacobi constant (conserved)
C = jacobi_constant(state, mu)

# Verify conservation along trajectory
C_values = [jacobi_constant(s, mu) for s in states]
print(f"C range: [{min(C_values):.10f}, {max(C_values):.10f}]")
print(f"Drift: {max(C_values) - min(C_values):.2e}")
```

### Mass Ratios of Interest

| System | μ | Notes |
|--------|---|-------|
| Earth-Moon | 0.012150585609624 | Standard test case |
| Sun-Jupiter | 9.537e-4 | Planet-dominated |
| Equal masses | 0.5 | Symmetric |
| Test (μ→0) | 0.001 | Near-Kepler |

## Precision Tiers

| Tier | Target ΔC | Integrator | Arithmetic | Use Case |
|------|-----------|------------|------------|----------|
| **1** | < 10⁻¹⁴ | IAS15 | Double | Exploration, WP3 ML |
| **2** | < 10⁻²⁵ | AdaptiveSymplectic | QD (31 digits) | WP4 validation |

### Tier 2 with QD Library

```python
from src.python.qd_python import dd_real
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator

# Convert initial conditions to QD
state0_qd = [dd_real(x) for x in state0]
mu_qd = dd_real(mu)

# Create Tier 2 integrator
integrator = AdaptiveSymplecticIntegrator(
    mu=mu_qd,
    order=6,
    tol=dd_real(1e-25),
    precision='qd'
)

# Integrate in extended precision
times, states = integrator.integrate(state0_qd, t_span)

# Verify Tier 2 conservation
C_drift = compute_jacobi_drift_qd(states, mu_qd)
print(f"Tier 2 drift: {float(C_drift):.2e}")  # Should be < 1e-25
```

See `references/precision-tiers.md` for detailed precision analysis.

## Downstream Integration

### WP2: Geometric Foundations

```python
from src.python.lifts.s1_bundle import S1Bundle

# Generate trajectory
times, states = integrator.integrate(state0, t_span, dt)

# Lift to S¹ bundle for geometric analysis
bundle = S1Bundle(mu=mu)
lifted_states = bundle.lift_trajectory(states)
```

### WP3: ML Discovery

```python
# Export trajectory for ML training
trajectory_dict = {
    'times': times,
    'states': states,
    'mu': mu,
    'C': jacobi_constant(states[0], mu),
    'classification': 'regular'  # From chaos analysis
}

# WP3 consumes these for:
# - Hamiltonian Neural Networks (HNN)
# - Symbolic regression (AI Feynman)
# - Invariant search in lifted spaces
```

### WP4: Validation

```python
from src.python.validation.morales_ramis_validator import MoralesRamisValidator

# For WP4, need variational equations
var_result = var_integrator.integrate(
    state0=periodic_orbit_ic,
    t_span=(0, period),
    compute_monodromy=True
)

# Feed to Morales-Ramis test
validator = MoralesRamisValidator(mu=mu)
galois_result = validator.analyze_monodromy(var_result['monodromy'])
```

## Error Handling

### Common Issues

| Issue | Detection | Solution |
|-------|-----------|----------|
| NaN in trajectory | `np.any(np.isnan(states))` | Enable regularization |
| Jacobi drift > threshold | `C_drift > 1e-14` | Promote to Tier 2 |
| Integration timeout | Step count exceeds max | Increase `max_steps` |
| Escape detection | `r > escape_radius` | Filter initial conditions |

### Diagnostic Function

```python
def diagnose_integration(times, states, mu):
    """Diagnose integration quality issues."""
    diagnostics = {}
    
    # Check for NaN
    diagnostics['has_nan'] = np.any(np.isnan(states))
    
    # Jacobi conservation
    C_values = [jacobi_constant(s, mu) for s in states]
    diagnostics['C_drift'] = max(C_values) - min(C_values)
    diagnostics['tier1_pass'] = diagnostics['C_drift'] < 1e-14
    
    # Close encounters
    r_mins = [min(
        np.sqrt((s[0]+mu)**2 + s[1]**2 + s[2]**2),
        np.sqrt((s[0]-1+mu)**2 + s[1]**2 + s[2]**2)
    ) for s in states]
    diagnostics['min_distance'] = min(r_mins)
    diagnostics['had_close_encounter'] = diagnostics['min_distance'] < 0.1
    
    # Escape check
    r_max = max(np.sqrt(s[0]**2 + s[1]**2 + s[2]**2) for s in states)
    diagnostics['max_distance'] = r_max
    diagnostics['escaped'] = r_max > 10.0
    
    return diagnostics
```

## Tests

```bash
# All integrator tests
pytest tests/test_integrators.py -v

# Symplectic tests
pytest tests/test_yoshida8.py -v

# Dynamics tests
pytest tests/test_dynamics.py -v

# Variational equations
pytest tests/validation/test_variational_equations.py -v

# Run with coverage
pytest tests/ --cov=src/python/integrators --cov-report=html
```

## References

- `references/precision-tiers.md` - Detailed precision analysis
- `references/integrator-details.md` - Complete integrator configurations
- `references/variational-integration.md` - Variational equations theory
- `references/regularization-guide.md` - Close encounter handling
- `references/coordinate-systems.md` - Coordinate transformations
- `src/python/integrators/` - All integrator implementations
- `src/python/utils/dynamics.py` - CR3BP equations
- `Science-Research-Docs/Explanation_REBOUND.md` - IAS15 background
- `Science-Research-Docs/Explanation_DoubleDoubleArithmetic.md` - QD library
