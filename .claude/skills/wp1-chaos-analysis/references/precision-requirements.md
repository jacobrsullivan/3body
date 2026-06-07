# Precision Requirements for Chaos Analysis

Detailed precision analysis for chaos indicator computation across the project's two-tier precision strategy.

## Table of Contents

1. [Precision Tier Overview](#precision-tier-overview)
2. [Error Sources in Chaos Analysis](#error-sources-in-chaos-analysis)
3. [Tier 1 Configuration](#tier-1-configuration)
4. [Tier 2 Configuration](#tier-2-configuration)
5. [Indicator-Specific Requirements](#indicator-specific-requirements)
6. [Validation Protocols](#validation-protocols)
7. [When to Upgrade Precision](#when-to-upgrade-precision)

---

## Precision Tier Overview

| Tier | Arithmetic | Target ΔC/C | Use Case | Speed |
|------|------------|-------------|----------|-------|
| **Tier 1** | IEEE double (15-16 digits) | < 10⁻¹⁴ | Catalogue screening, parameter sweeps | ~50 periods/s |
| **Tier 2** | QD double-double (31 digits) | < 10⁻²⁵ | WP4 validation, Morales-Ramis prep | ~5-10 periods/s |

---

## Error Sources in Chaos Analysis

### 1. Floating-Point Roundoff

| Source | Tier 1 Error | Tier 2 Error |
|--------|-------------|--------------|
| Basic arithmetic | 10⁻¹⁶ | 10⁻³² |
| Accumulated roundoff (N ops) | √N × 10⁻¹⁶ | √N × 10⁻³² |
| Transcendental functions | 10⁻¹⁵ | 10⁻³¹ |

### 2. Integrator Truncation

| Integrator | Order | Local Error | Global Error (T periods) |
|------------|-------|-------------|-------------------------|
| IAS15 | 15 | O(h¹⁶) | ~ T × h¹⁵ |
| Yoshida8 | 8 | O(h⁹) | ~ T × h⁸ |
| AdaptiveSymplectic | 6 | O(h⁷) | ~ T × h⁶ (but symplectic) |

### 3. Variational Equation Errors

The deviation vector δx grows exponentially for chaotic orbits:

```
|δx(t)| ~ |δx(0)| × exp(λt)
```

This amplifies numerical errors:

| Chaos Type | Error Amplification | Precision Needed |
|------------|--------------------|--------------------|
| Regular | Polynomial O(t^α) | Tier 1 sufficient |
| Weakly chaotic | Slow exponential | Tier 1, long integration |
| Strongly chaotic | Fast exponential | Tier 2 recommended |

### 4. Close Encounter Errors

Near the primaries (r₁ → 0 or r₂ → 0):

```
Force ~ 1/r²  →  Numerical error ~ ε/r²
```

| Distance r | Tier 1 Force Error | Tier 2 Force Error |
|------------|-------------------|-------------------|
| 10⁻² | 10⁻¹² | 10⁻²⁸ |
| 10⁻³ | 10⁻¹⁰ | 10⁻²⁶ |
| 10⁻⁴ | 10⁻⁸ | 10⁻²⁴ |

**Solution**: Sundman time transformation (see integration-guidelines.md)

---

## Tier 1 Configuration

### Integrator: IAS15

```python
from src.python.integrators.ias15 import IAS15Integrator

integrator = IAS15Integrator(mu=mu)
```

**Characteristics:**
- 15th-order adaptive Gauss-Radau
- Automatic timestep control
- Non-symplectic but excellent energy conservation

### Chaos Analyzer Setup

```python
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

analyzer = create_cr3bp_chaos_analyzer(
    mu=mu,
    integrator='ias15',
    precision='double'
)
```

### Expected Precision

| Metric | Target | Typical Achieved |
|--------|--------|------------------|
| Jacobi constant drift | < 10⁻¹⁴ | 10⁻¹⁵ - 10⁻¹⁴ |
| MEGNO accuracy | ±0.1 | ±0.05 |
| FLI accuracy | ±0.2 | ±0.1 |
| Classification confidence | 95% | 97% |

### Validation Checks

```python
def validate_tier1_chaos(result, times, states, mu):
    """Validate Tier 1 chaos analysis results."""

    # Check Jacobi constant conservation
    C_values = [jacobi_constant(s, mu) for s in states]
    C_drift = (max(C_values) - min(C_values)) / abs(C_values[0])

    if C_drift > 1e-14:
        return False, f"Jacobi drift {C_drift:.2e} exceeds Tier 1 threshold"

    # Check for numerical artifacts in MEGNO
    if result['megno'] < 0:
        return False, "Negative MEGNO indicates numerical instability"

    # Check consistency
    if result['megno'] < 2.5 and result['fli'] > 4.0:
        return False, "MEGNO-FLI disagreement - needs review"

    return True, "Tier 1 validation passed"
```

---

## Tier 2 Configuration

### Integrator: AdaptiveSymplectic + QD

```python
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator

integrator = AdaptiveSymplecticIntegrator(
    mu=mu,
    order=6,
    tol=1e-20,
    sundman_strategy='sum',
    arithmetic='qd'  # Double-double precision
)
```

### QD Library Usage

```python
from src.python.qd_python import dd_real

# All computations in double-double
state_qd = [dd_real(x) for x in state0]
mu_qd = dd_real(mu)

# Jacobi constant in extended precision
def jacobi_constant_qd(state, mu):
    x, y, z, vx, vy, vz = state
    r1 = ((x + mu)**2 + y**2 + z**2).sqrt()
    r2 = ((x - dd_real(1.0) + mu)**2 + y**2 + z**2).sqrt()
    Omega = dd_real(0.5) * (x**2 + y**2) + (dd_real(1.0) - mu) / r1 + mu / r2
    return dd_real(2.0) * Omega - (vx**2 + vy**2 + vz**2)
```

### Chaos Analyzer Setup

```python
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

analyzer = create_cr3bp_chaos_analyzer(
    mu=mu,
    integrator='adaptive_symplectic',
    integrator_kwargs={
        'order': 6,
        'tol': 1e-20,
        'sundman_strategy': 'sum'
    },
    precision='qd'
)
```

### Expected Precision

| Metric | Target | Typical Achieved |
|--------|--------|------------------|
| Jacobi constant drift | < 10⁻²⁵ | 10⁻²⁶ - 10⁻²⁵ |
| MEGNO accuracy | ±0.01 | ±0.005 |
| FLI accuracy | ±0.05 | ±0.02 |
| Classification confidence | 99.9% | 99.95% |
| Monodromy matrix error | < 10⁻²⁰ | 10⁻²² |

### Validation Checks

```python
def validate_tier2_chaos(result, times, states, mu):
    """Validate Tier 2 chaos analysis results."""
    from src.python.qd_python import dd_real

    # Check Jacobi constant conservation in QD
    C_values = [jacobi_constant_qd(s, mu) for s in states]
    C_drift = float((max(C_values) - min(C_values)) / abs(C_values[0]))

    if C_drift > 1e-25:
        return False, f"Jacobi drift {C_drift:.2e} exceeds Tier 2 threshold"

    # Check shadow Hamiltonian
    from src.python.validation.shadow_hamiltonian import ShadowHamiltonianAnalyzer
    shadow = ShadowHamiltonianAnalyzer(dynamics_func=cr3bp_dynamics)
    shadow_result = shadow.analyze(times, states, dt=times[1]-times[0])

    if shadow_result['drift_rate'] > 1e-25:
        return False, f"Shadow Hamiltonian drift {shadow_result['drift_rate']:.2e} too large"

    # Verify monodromy matrix (for periodic orbits)
    if result.get('monodromy_matrix') is not None:
        M = result['monodromy_matrix']
        det_M = np.linalg.det(M)
        if abs(det_M - 1.0) > 1e-20:
            return False, f"Monodromy determinant {det_M:.2e} ≠ 1"

    return True, "Tier 2 validation passed"
```

---

## Indicator-Specific Requirements

### MEGNO

| Aspect | Tier 1 | Tier 2 |
|--------|--------|--------|
| Integration time | 100 periods | 1000+ periods |
| Timestep | 0.01 | 0.001 |
| Threshold precision | ±0.1 | ±0.01 |
| Convergence criterion | |⟨Y⟩ - 2| < 0.1 for 10 periods | |⟨Y⟩ - 2| < 0.01 for 100 periods |

### FLI

| Aspect | Tier 1 | Tier 2 |
|--------|--------|--------|
| Integration time | 50 periods | 500 periods |
| Timestep | 0.01 | 0.001 |
| Threshold precision | ±0.2 | ±0.05 |

### Monodromy Matrix (Periodic Orbits)

| Aspect | Tier 1 | Tier 2 |
|--------|--------|--------|
| Period matching | |T_computed - T_true| < 10⁻¹⁰ | |T_computed - T_true| < 10⁻²⁰ |
| det(M) accuracy | |det(M) - 1| < 10⁻¹⁰ | |det(M) - 1| < 10⁻²⁰ |
| Eigenvalue accuracy | 10⁻¹² | 10⁻²⁵ |

---

## Validation Protocols

### Protocol 1: Conservation Check

```python
def conservation_check(states, mu, tier='tier1'):
    """Check Jacobi constant conservation."""
    threshold = 1e-14 if tier == 'tier1' else 1e-25

    C = [jacobi_constant(s, mu) for s in states]
    drift = (max(C) - min(C)) / abs(C[0])

    return drift < threshold
```

### Protocol 2: Shadow Hamiltonian Analysis

```python
def shadow_hamiltonian_check(times, states, tier='tier1'):
    """Verify backward error analysis."""
    from src.python.validation.shadow_hamiltonian import ShadowHamiltonianAnalyzer

    threshold = 1e-14 if tier == 'tier1' else 1e-25

    analyzer = ShadowHamiltonianAnalyzer(dynamics_func=cr3bp_dynamics)
    result = analyzer.analyze(times, states, dt=times[1]-times[0])

    return result['drift_rate'] < threshold
```

### Protocol 3: Time Reversibility

```python
def reversibility_check(state0, t_final, integrator, tier='tier1'):
    """Check time reversibility."""
    threshold = 1e-14 if tier == 'tier1' else 1e-20

    # Forward integration
    _, states_fwd = integrator.integrate(state0, (0, t_final))

    # Backward integration
    _, states_bwd = integrator.integrate(states_fwd[-1], (t_final, 0))

    error = np.linalg.norm(states_bwd[-1] - state0)
    return error < threshold
```

### Protocol 4: Consistency Check

```python
def indicator_consistency_check(megno, fli):
    """Check MEGNO-FLI consistency."""

    # Both should agree on classification
    megno_regular = megno < 2.5
    fli_regular = fli < 3.0

    megno_chaotic = megno > 3.0
    fli_chaotic = fli > 4.0

    # Consistent if both agree on type
    consistent = (megno_regular == fli_regular) or (megno_chaotic == fli_chaotic)

    # Or if one is borderline
    megno_borderline = 2.5 <= megno <= 3.0
    fli_borderline = 3.0 <= fli <= 4.0

    return consistent or megno_borderline or fli_borderline
```

---

## When to Upgrade Precision

### Automatic Upgrade Triggers

```python
def should_upgrade_to_tier2(result, tier1_validation):
    """Determine if Tier 2 precision is needed."""

    reasons = []

    # Conservation failure
    if not tier1_validation['conservation_passed']:
        reasons.append("Jacobi conservation failed")

    # Shadow Hamiltonian drift
    if tier1_validation['shadow_drift'] > 1e-14:
        reasons.append("Shadow Hamiltonian drift too large")

    # Borderline classification
    if 2.5 <= result['megno'] <= 3.0:
        reasons.append("MEGNO in borderline range")

    if 3.0 <= result['fli'] <= 4.0:
        reasons.append("FLI in borderline range")

    # Indicator disagreement
    if not indicator_consistency_check(result['megno'], result['fli']):
        reasons.append("MEGNO-FLI inconsistency")

    # For WP4 Morales-Ramis
    if result.get('for_morales_ramis', False):
        reasons.append("Morales-Ramis preparation requires Tier 2")

    # Periodic orbit analysis
    if result.get('is_periodic', False):
        reasons.append("Periodic orbit monodromy requires Tier 2")

    return len(reasons) > 0, reasons
```

### Upgrade Workflow

```python
def analyze_with_auto_upgrade(state0, mu, t_max):
    """Analyze orbit with automatic precision upgrade."""

    # Start with Tier 1
    analyzer_t1 = create_cr3bp_chaos_analyzer(mu=mu, precision='double')
    result_t1 = analyzer_t1.analyze(state0, t_max)

    # Validate Tier 1
    validation = validate_tier1_chaos(result_t1, ...)

    # Check if upgrade needed
    needs_upgrade, reasons = should_upgrade_to_tier2(result_t1, validation)

    if needs_upgrade:
        print(f"Upgrading to Tier 2: {', '.join(reasons)}")

        analyzer_t2 = create_cr3bp_chaos_analyzer(
            mu=mu,
            precision='qd',
            integrator='adaptive_symplectic'
        )
        result_t2 = analyzer_t2.analyze(state0, t_max * 10)  # Extended time

        return result_t2, 'tier2'

    return result_t1, 'tier1'
```

---

## Precision Budget Summary

### Tier 1 Error Budget

| Source | Allocation | Notes |
|--------|-----------|-------|
| Roundoff | 10⁻¹⁶ | IEEE double limit |
| Integration | 10⁻¹⁵ | IAS15 truncation |
| Close encounters | 10⁻¹⁴ | Without regularization |
| **Total** | **10⁻¹⁴** | Jacobi constant target |

### Tier 2 Error Budget

| Source | Allocation | Notes |
|--------|-----------|-------|
| Roundoff | 10⁻³² | QD double-double |
| Integration | 10⁻²⁶ | Symplectic + small dt |
| Close encounters | 10⁻²⁵ | With Sundman transformation |
| **Total** | **10⁻²⁵** | Jacobi constant target |
