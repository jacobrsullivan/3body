# Precision Tiers Reference

Detailed analysis of the two-tier precision system for trajectory generation.

## Table of Contents

1. [Overview](#overview)
2. [Tier 1: Standard Precision](#tier-1-standard-precision)
3. [Tier 2: Ultra-High Precision](#tier-2-ultra-high-precision)
4. [QD Library Usage](#qd-library-usage)
5. [Precision Budget Analysis](#precision-budget-analysis)
6. [Automatic Tier Selection](#automatic-tier-selection)
7. [Validation Protocols](#validation-protocols)

---

## Overview

The project uses a two-tier precision system to balance computational cost against accuracy requirements for different analysis stages.

| Property | Tier 1 | Tier 2 |
|----------|--------|--------|
| **Target ΔC/C** | < 10⁻¹⁴ | < 10⁻²⁵ |
| **Orbits** | 10⁵ | 10⁴ |
| **Integrator** | IAS15 | AdaptiveSymplectic |
| **Arithmetic** | IEEE double | QD double-double |
| **Speed** | ~50 periods/s | ~5-10 periods/s |
| **Use Case** | Exploration, WP3 ML | Validation, WP4 Morales-Ramis |

---

## Tier 1: Standard Precision

### Target

```
Jacobi constant relative drift: |ΔC|/|C| < 10⁻¹⁴
```

### Configuration

```python
from src.python.integrators.ias15 import IAS15Integrator

# Tier 1 integrator setup
integrator = IAS15Integrator(
    mu=0.012150585609624,
    epsilon=1e-9,       # Convergence parameter
)

# Standard integration
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 100 * T_period),
    dt=T_period / 100   # 100 points per period
)
```

### Use Cases

| Application | Description |
|-------------|-------------|
| Catalogue generation | 10⁵ orbits for parameter space coverage |
| Chaos classification | MEGNO/FLI computation (100 periods) |
| WP3 ML training | Training data for Hamiltonian Neural Networks |
| Parameter exploration | Quick surveys of initial condition space |
| Poincaré sections | Return map analysis |

### Performance

```
Benchmark: Earth-Moon system (μ = 0.0122)

Integration speed:     50 periods/second
Typical Jacobi drift:  2-5 × 10⁻¹⁵
Memory per orbit:      ~0.5 MB (100 periods, dt=0.1)
```

### Validation Criteria

```python
def validate_tier1(times, states, mu):
    """Validate Tier 1 integration quality."""
    # Compute Jacobi constants
    C_values = [jacobi_constant(s, mu) for s in states]
    C_mean = np.mean(C_values)

    # Relative drift
    C_drift_rel = (max(C_values) - min(C_values)) / abs(C_mean)

    # Check threshold
    passed = C_drift_rel < 1e-14

    return {
        'C_drift_relative': C_drift_rel,
        'C_drift_absolute': max(C_values) - min(C_values),
        'passed': passed,
        'tier': 1
    }
```

---

## Tier 2: Ultra-High Precision

### Target

```
Jacobi constant relative drift: |ΔC|/|C| < 10⁻²⁵
95th percentile requirement (for validation)
```

### Configuration

```python
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator
from src.python.qd_python import dd_real

# Convert to QD types
mu_qd = dd_real(0.012150585609624)
state0_qd = [dd_real(x) for x in initial_state]

# Tier 2 integrator setup
integrator = AdaptiveSymplecticIntegrator(
    mu=mu_qd,
    order=6,
    tol=dd_real(1e-25),
    sundman_strategy='sum',
    precision='qd'
)

# High-precision integration
times, states = integrator.integrate(
    state0=state0_qd,
    t_span=(0, 1000 * T_period),
    max_steps=100000000
)
```

### Use Cases

| Application | Description |
|-------------|-------------|
| WP4 validation | Morales-Ramis variational equations |
| Candidate verification | Verify conservation of discovered integrals |
| Periodic orbit families | High-precision family continuation |
| Long-time studies | >10⁵ periods with symplectic structure |
| Shadow Hamiltonian | Backward error analysis |

### Performance

```
Benchmark: Earth-Moon system (μ = 0.0122) with QD

Integration speed:     5-10 periods/second
Typical Jacobi drift:  1-5 × 10⁻²⁶
Memory per orbit:      ~4 MB (1000 periods + variational)
```

### Validation Criteria

```python
def validate_tier2(times, states, mu_qd):
    """Validate Tier 2 integration quality."""
    from src.python.qd_python import dd_real

    # Compute Jacobi constants in QD
    C_values = [jacobi_constant_qd(s, mu_qd) for s in states]

    # Convert to float for comparison
    C_drift_rel = float(
        (max(C_values) - min(C_values)) / abs(C_values[0])
    )

    # Check 95th percentile threshold
    passed = C_drift_rel < 1e-25

    # Additional symplectic checks
    symplectic_error = check_symplectic_structure(states)

    return {
        'C_drift_relative': C_drift_rel,
        'symplectic_error': symplectic_error,
        'passed': passed and symplectic_error < 1e-25,
        'tier': 2
    }
```

---

## QD Library Usage

### Overview

The QD (Quad-Double) library provides extended precision arithmetic:
- **Double-double**: ~31 decimal digits
- **Quad-double**: ~62 decimal digits (not typically needed)

### Installation

```bash
# Built via project script
./scripts/build_cpp.sh

# Verify installation
python -c "from src.python.qd_python import dd_real; print(dd_real(1)/dd_real(3))"
```

### Basic Usage

```python
from src.python.qd_python import dd_real

# Create double-double values
a = dd_real(1.0)
b = dd_real(3.0)

# Arithmetic operations
c = a / b           # 0.333...333 to 31 digits
d = a + b           # 4.0
e = a * b           # 3.0
f = dd_real.sqrt(a) # 1.0

# Convert back to float
float_val = float(c)

# String representation (full precision)
print(str(c))  # Shows all 31 digits
```

### Array Operations

```python
def qd_array_ops(arr_float):
    """Convert float array to QD and back."""
    # Float → QD
    arr_qd = [dd_real(x) for x in arr_float]

    # Operations in QD
    sum_qd = sum(arr_qd)

    # QD → Float
    result = float(sum_qd)

    return result
```

### Integrator with QD

```python
def tier2_integration(state0, t_span, mu):
    """Full Tier 2 integration workflow."""
    from src.python.qd_python import dd_real

    # Convert everything to QD
    mu_qd = dd_real(mu)
    state0_qd = [dd_real(x) for x in state0]
    t0_qd = dd_real(t_span[0])
    tf_qd = dd_real(t_span[1])

    # Create Tier 2 integrator
    integrator = AdaptiveSymplecticIntegrator(
        mu=mu_qd,
        order=6,
        tol=dd_real(1e-25),
        precision='qd'
    )

    # Integrate
    times_qd, states_qd = integrator.integrate(
        state0=state0_qd,
        t_span=(t0_qd, tf_qd)
    )

    # Convert back for storage (but keep QD for validation)
    times = [float(t) for t in times_qd]
    states = [[float(x) for x in s] for s in states_qd]

    return times, states, states_qd  # Keep QD for validation
```

### When to Use QD

| Situation | Use QD? | Reason |
|-----------|---------|--------|
| Tier 1 exploration | No | Too slow, not needed |
| Chaos classification | No | MEGNO/FLI need ~10⁻¹⁰ |
| WP3 ML training | No | Neural networks use float32/64 |
| WP4 Morales-Ramis | **Yes** | Variational equations need precision |
| Shadow Hamiltonian | **Yes** | Backward error analysis |
| Long-time symplectic | **Yes** | Prevent drift accumulation |
| Periodic orbit families | **Yes** | Continuation requires precision |

---

## Precision Budget Analysis

### Tier 1 Error Budget

| Source | Contribution | Notes |
|--------|--------------|-------|
| Floating-point roundoff | 10⁻¹⁶ | IEEE double limit |
| IAS15 truncation error | 10⁻¹⁵ | 15th order |
| Close encounters | Variable | Can blow up without regularization |
| Output interpolation | 10⁻¹⁵ | Dense output error |
| **Total budget** | **10⁻¹⁴** | Conservative sum |

### Tier 2 Error Budget

| Source | Contribution | Notes |
|--------|--------------|-------|
| QD roundoff | 10⁻³² | 31 digits |
| Symplectic truncation | 10⁻²⁶ | 6th order composition |
| Sundman regularization | 10⁻²⁵ | Time transformation |
| Symplectic structure | Exact | By construction |
| **Total budget** | **10⁻²⁵** | Conservative sum |

### Error Accumulation

For N orbital periods:

```
Tier 1: ΔC ~ N × 10⁻¹⁵ (secular for non-symplectic)
Tier 2: ΔC ~ √N × 10⁻²⁶ (random walk for symplectic)
```

This means:
- Tier 1 valid for ~10³ periods before drift exceeds threshold
- Tier 2 valid for ~10⁸ periods

---

## Automatic Tier Selection

### Decision Logic

```python
def select_tier(state0, mu, requirements):
    """
    Automatically select appropriate precision tier.

    Args:
        state0: initial state
        mu: mass ratio
        requirements: dict with analysis requirements

    Returns:
        'tier1' or 'tier2'
    """
    # Check for close encounters
    is_close, r_min, _ = detect_close_encounter(state0, mu, threshold=0.1)
    if is_close and r_min < 0.01:
        return 'tier2'  # Need regularization

    # Check precision requirements
    if requirements.get('variational', False):
        return 'tier2'  # Morales-Ramis needs high precision

    if requirements.get('precision', 1e-14) < 1e-20:
        return 'tier2'

    if requirements.get('n_periods', 100) > 10000:
        return 'tier2'  # Long integration needs symplectic

    return 'tier1'
```

### Automatic Promotion

```python
def integrate_with_promotion(state0, t_span, mu, dt=0.1):
    """
    Integrate with automatic tier promotion on failure.
    """
    # Try Tier 1 first
    integrator_t1 = IAS15Integrator(mu=mu)
    times, states = integrator_t1.integrate(state0, t_span, dt)

    # Validate
    validation = validate_tier1(times, states, mu)

    if validation['passed']:
        return times, states, 1

    # Promote to Tier 2
    print(f"Promoting to Tier 2 (drift: {validation['C_drift_relative']:.2e})")

    from src.python.qd_python import dd_real
    mu_qd = dd_real(mu)
    state0_qd = [dd_real(x) for x in state0]

    integrator_t2 = AdaptiveSymplecticIntegrator(
        mu=mu_qd, order=6, tol=dd_real(1e-25)
    )
    times, states = integrator_t2.integrate(state0_qd, t_span)

    # Convert back
    times = [float(t) for t in times]
    states = [[float(x) for x in s] for s in states]

    return times, states, 2
```

---

## Validation Protocols

### Tier 1 Validation

```python
def full_tier1_validation(times, states, mu):
    """Complete Tier 1 validation suite."""
    results = {}

    # 1. Jacobi conservation
    C_values = [jacobi_constant(s, mu) for s in states]
    results['jacobi_drift'] = max(C_values) - min(C_values)
    results['jacobi_pass'] = results['jacobi_drift'] < 1e-14

    # 2. NaN check
    results['has_nan'] = np.any(np.isnan(states))

    # 3. Escape check
    r_max = max(np.sqrt(s[0]**2 + s[1]**2 + s[2]**2) for s in states)
    results['escaped'] = r_max > 10.0

    # 4. Close encounter check
    r_mins = [min_primary_distance(s, mu) for s in states]
    results['min_distance'] = min(r_mins)

    # Overall
    results['passed'] = (
        results['jacobi_pass'] and
        not results['has_nan'] and
        not results['escaped']
    )

    return results
```

### Tier 2 Validation

```python
def full_tier2_validation(times, states_qd, mu_qd):
    """Complete Tier 2 validation suite."""
    results = {}

    # 1. Jacobi conservation (in QD)
    C_values = [jacobi_constant_qd(s, mu_qd) for s in states_qd]
    results['jacobi_drift'] = float(max(C_values) - min(C_values))
    results['jacobi_pass'] = results['jacobi_drift'] < 1e-25

    # 2. Symplectic structure (for variational equations)
    if 'phi' in states_qd:
        phi_final = states_qd['phi'][-1]
        J = symplectic_matrix(6)
        symp_error = np.max(np.abs(phi_final.T @ J @ phi_final - J))
        results['symplectic_error'] = float(symp_error)
        results['symplectic_pass'] = results['symplectic_error'] < 1e-20

    # 3. Time reversibility (optional, expensive)
    # results['reversibility'] = test_reversibility(...)

    results['passed'] = results['jacobi_pass']

    return results
```

---

## Reference Documents

- `Science-Research-Docs/Explanation_DoubleDoubleArithmetic.md` - QD library details
- `Science-Research-Docs/Explanation_REBOUND.md` - IAS15 integrator theory
- `Project-Design-Docs/WP1/` - Full implementation specifications
- `Research_Synthesis__Variational_Equations.md` - Precision requirements for Morales-Ramis
