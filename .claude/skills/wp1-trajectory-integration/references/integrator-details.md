# Integrator Details Reference

Complete configuration guide for all available integrators.

## Table of Contents

1. [IAS15 (Adaptive Radau)](#ias15-adaptive-radau)
2. [Yoshida8 (Symplectic)](#yoshida8-symplectic)
3. [AdaptiveSymplectic](#adaptivesymplectic)
4. [Dense Output](#dense-output)
5. [Performance Comparison](#performance-comparison)
6. [Selection Guidelines](#selection-guidelines)

---

## IAS15 (Adaptive Radau)

### Overview

IAS15 is a 15th-order adaptive Gauss-Radau integrator from the REBOUND library. It achieves excellent energy conservation through high-order quadrature and adaptive timestep control.

**Key Properties**:
- Order: 15 (Gauss-Radau quadrature)
- Timestep: Adaptive (internal)
- Symplectic: No (but excellent energy conservation)
- Close encounters: Handles moderate (r > 0.01)

### Configuration

```python
from src.python.integrators.ias15 import IAS15Integrator

integrator = IAS15Integrator(
    mu=0.012150585609624,   # Mass ratio
    epsilon=1e-9,           # Convergence parameter (default)
    min_dt=1e-6,            # Minimum timestep (default)
    max_dt=0.1,             # Maximum timestep (default)
    exact_finish_time=True, # Ensure exact final time (default)
)
```

### Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `epsilon` | 1e-9 | 1e-12 to 1e-6 | Convergence criterion |
| `min_dt` | 1e-6 | > 0 | Minimum internal timestep |
| `max_dt` | 0.1 | > min_dt | Maximum internal timestep |
| `exact_finish_time` | True | bool | Force exact t_final |

### Timestep Behavior

IAS15 uses adaptive internal timesteps while outputting at fixed intervals:

```python
# Output at fixed dt, internal timestep adaptive
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 100),
    dt=0.1  # Output every 0.1 time units
)
# Internal timestep varies from ~0.001 to ~0.1 depending on dynamics
```

### Energy Conservation Analysis

```
Typical relative energy drift:
  - Regular orbits: ~10⁻¹⁵ to 10⁻¹⁶
  - Mildly chaotic: ~10⁻¹⁴
  - Close encounters (r < 0.1): ~10⁻¹² to 10⁻¹⁰
```

### Best Practices

1. **Output timestep**: Use `dt = T_period / 100` for smooth trajectories
2. **Close encounters**: If r < 0.01 expected, use AdaptiveSymplectic instead
3. **Long integrations**: Check Jacobi drift periodically

---

## Yoshida8 (Symplectic)

### Overview

8th-order symmetric composition symplectic integrator. Exactly preserves symplectic structure but uses fixed timestep.

**Key Properties**:
- Order: 8 (composition method)
- Timestep: Fixed
- Symplectic: Yes (exact)
- Close encounters: Poor (requires small dt)

### Configuration

```python
from src.python.integrators.yoshida8 import Yoshida8Integrator

integrator = Yoshida8Integrator(
    mu=0.012150585609624,   # Mass ratio
)

times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 1000),
    dt=0.01                 # Fixed timestep (CRITICAL)
)
```

### Timestep Selection

The timestep directly controls accuracy:

```
dt = T_period / N

N = 50:   ΔC ~ 10⁻⁴  (very coarse, not recommended)
N = 100:  ΔC ~ 10⁻⁸  (acceptable for stability studies)
N = 200:  ΔC ~ 10⁻¹⁰ (good precision)
N = 500:  ΔC ~ 10⁻¹² (high precision)
N = 1000: ΔC ~ 10⁻¹⁴ (approaches machine precision)
```

### Yoshida Coefficients

The integrator uses the Yoshida (1990) coefficients for 8th-order composition:

```python
# Kick-drift-kick composition
# H = T(p) + V(q) split
# Coefficients satisfy symmetric order conditions
c = [c₀, c₁, c₂, c₃, c₄, c₅, c₆, c₇]  # Position coefficients
d = [d₀, d₁, d₂, d₃, d₄, d₅, d₆, d₇]  # Momentum coefficients
```

### Long-Term Stability

Because Yoshida8 is symplectic, it exhibits:
- No secular energy drift (bounded oscillations)
- Preserved phase space volume
- Correct qualitative behavior even with moderate dt

```python
# Long-term integration (10⁵ periods)
import matplotlib.pyplot as plt

integrator = Yoshida8Integrator(mu=mu)
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 100000 * T_period),
    dt=T_period / 100
)

# Energy oscillates but doesn't drift
E_values = [energy(s, mu) for s in states[::1000]]
plt.plot(times[::1000], E_values)
# Shows bounded oscillations, no secular trend
```

---

## AdaptiveSymplectic

### Overview

Symplectic integrator with adaptive timestep via Sundman time transformation. Achieves both symplectic structure preservation and close encounter handling.

**Key Properties**:
- Order: 4 or 6 (configurable)
- Timestep: Adaptive via Sundman
- Symplectic: Yes (exact in regularized coordinates)
- Close encounters: Excellent (regularized)

### Configuration

```python
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator

integrator = AdaptiveSymplecticIntegrator(
    mu=0.012150585609624,
    order=6,                    # 4 or 6 (default: 6)
    tol=1e-14,                  # Error tolerance
    sundman_strategy='sum',     # Time regularization
    min_dt=1e-10,               # Minimum timestep
    max_dt=0.01,                # Maximum timestep
    safety_factor=0.9,          # Step size safety (default)
)
```

### Parameters

| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `order` | 6 | 4, 6 | Composition order |
| `tol` | 1e-14 | 1e-25 to 1e-10 | Error tolerance |
| `sundman_strategy` | 'sum' | 'sum', 'product', 'min' | Regularization |
| `min_dt` | 1e-10 | > 0 | Minimum timestep |
| `max_dt` | 0.01 | > min_dt | Maximum timestep |
| `safety_factor` | 0.9 | 0.5 to 1.0 | Conservative step adjustment |

### Sundman Time Transformation

The Sundman transformation converts physical time t to fictitious time s:

```
dt/ds = g(r₁, r₂)

Strategy 'sum':     g = r₁ + r₂         (balanced)
Strategy 'product': g = r₁ × r₂         (aggressive near collisions)
Strategy 'min':     g = min(r₁, r₂)     (conservative)
```

Near close encounters, g → 0, so ds steps become smaller in physical time, allowing accurate traversal.

### Error Control

Step doubling with local extrapolation:

```python
# Internal algorithm:
# 1. Take full step with dt
# 2. Take two half-steps with dt/2
# 3. Compare: error = |y_full - y_half|
# 4. If error > tol: reject and reduce dt
# 5. If error << tol: accept and increase dt
```

### QD Integration

For Tier 2 precision:

```python
from src.python.qd_python import dd_real

# Convert to QD types
mu_qd = dd_real(mu)
state0_qd = [dd_real(x) for x in state0]

integrator = AdaptiveSymplecticIntegrator(
    mu=mu_qd,
    order=6,
    tol=dd_real(1e-25),
    precision='qd'
)

times, states = integrator.integrate(state0_qd, t_span)
# Achieves ΔC < 10⁻²⁵
```

---

## Dense Output

### Overview

Dense output provides continuous trajectory interpolation between stored timesteps.

**Location**: `src/python/integrators/dense_output.py`

### Configuration

```python
from src.python.integrators.dense_output import DenseOutputWrapper

# Wrap any integrator
dense_integrator = DenseOutputWrapper(
    base_integrator=IAS15Integrator(mu=mu),
    interpolation_order=5,  # Hermite interpolation order
)

# Integrate with coarse storage
times, states = dense_integrator.integrate(
    state0=initial_state,
    t_span=(0, 100),
    dt=1.0  # Coarse output
)

# Query at arbitrary times
t_query = [0.5, 1.5, 2.5, 3.141592]
states_interp = dense_integrator.interpolate(t_query)
```

### Use Cases

- Poincaré section computation (exact crossing detection)
- Event detection (periapse, apoapse, close encounter)
- Smooth visualization
- Trajectory matching

---

## Performance Comparison

### Speed Benchmarks

```
Test: 100 orbital periods, Earth-Moon system (μ = 0.0122)

Integrator            Speed (periods/s)    Jacobi Drift
---------------------------------------------------------
IAS15                 50                   2.3e-15
Yoshida8 (N=100)      250                  4.1e-08
Yoshida8 (N=500)      50                   1.2e-12
AdaptiveSymplectic    20                   8.5e-15
AdaptiveSymplectic+QD 5                    1.1e-26
```

### Memory Usage

```
Per-orbit memory (100 periods, dt=0.1):

IAS15:              ~0.5 MB (trajectory only)
Yoshida8:           ~0.5 MB (trajectory only)
AdaptiveSymplectic: ~1.0 MB (trajectory + error estimates)
+ Variational:      ~4.0 MB (+ fundamental matrix)
```

---

## Selection Guidelines

### By Use Case

| Use Case | Recommended | Reason |
|----------|-------------|--------|
| Quick exploration | IAS15 | Fast, automatic |
| Chaos classification | IAS15 | MEGNO/FLI need moderate precision |
| Long-term (10⁵ periods) | Yoshida8 | No secular drift |
| Close encounters | AdaptiveSymplectic | Regularized |
| WP3 ML training | IAS15 | Good balance speed/accuracy |
| WP4 validation | AdaptiveSymplectic+QD | Maximum precision |
| Variational equations | AdaptiveSymplectic | Consistent precision |

### By Orbit Type

| Orbit Type | Recommendation |
|------------|----------------|
| Regular, far from primaries | IAS15 or Yoshida8 |
| Regular, near L4/L5 | IAS15 |
| Chaotic, no close encounters | IAS15 |
| Close encounter likely | AdaptiveSymplectic |
| Collision orbit | AdaptiveSymplectic (essential) |
| Periodic orbit family | AdaptiveSymplectic |

### Decision Matrix

```python
def select_integrator(orbit_type, precision_needed, has_close_encounters):
    """Select optimal integrator based on requirements."""
    
    if has_close_encounters:
        return 'AdaptiveSymplectic'
    
    if precision_needed == 'tier2':
        return 'AdaptiveSymplectic'
    
    if orbit_type == 'long_term':
        return 'Yoshida8'
    
    return 'IAS15'  # Default
```
