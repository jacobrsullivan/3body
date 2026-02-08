---
name: wp1-validation-suite
description: Validation framework for CR3BP trajectory quality including shadow Hamiltonian analysis, time reversibility tests, and conservation checks. Use when validating integration accuracy, checking energy/Jacobi conservation, performing backward error analysis, or testing integrator reliability. Triggers on requests involving trajectory validation, conservation tests, reversibility checks, or precision verification.
---

# WP1 Validation Suite

Validation workflows for verifying CR3BP trajectory quality and integration accuracy.

## Validation Methods

| Method | What It Tests | Tier 1 Target | Tier 2 Target |
|--------|--------------|---------------|---------------|
| Jacobi Conservation | Energy-like integral | ΔC < 10⁻¹⁴ | ΔC < 10⁻²⁵ |
| Time Reversibility | Symplectic structure | Δq < 10⁻¹² | Δq < 10⁻²⁰ |
| Shadow Hamiltonian | Backward error | drift < 10⁻¹⁴/period | drift < 10⁻²⁵/period |

**Decision tree:**
- Quick sanity check? → Jacobi conservation
- Testing symplectic integrator? → Time reversibility
- Analyzing long-term error? → Shadow Hamiltonian
- Full validation? → All three methods

## Quick Start

```python
from src.python.utils.dynamics import jacobi_constant
import numpy as np

# After integration
times, states = integrator.integrate(state0, t_span, dt)

# 1. Jacobi constant check
C_values = [jacobi_constant(s, mu) for s in states]
C_drift = max(C_values) - min(C_values)
print(f"Jacobi drift: {C_drift:.2e}")
assert C_drift < 1e-14, "Tier 1 precision violated"
```

## Jacobi Constant Conservation

**Location**: `src/python/utils/dynamics.py`

The Jacobi constant C = 2Ω - v² is conserved in CR3BP.

```python
from src.python.utils.dynamics import jacobi_constant

# Compute along trajectory
C_values = [jacobi_constant(state, mu) for state in states]

# Absolute drift
C_drift_abs = max(C_values) - min(C_values)

# Relative drift
C_mean = np.mean(C_values)
C_drift_rel = C_drift_abs / abs(C_mean)

print(f"Absolute drift: {C_drift_abs:.2e}")
print(f"Relative drift: {C_drift_rel:.2e}")

# Validation criteria
if C_drift_rel < 1e-14:
    print("Tier 1 PASS")
elif C_drift_rel < 1e-25:
    print("Tier 2 PASS")
else:
    print("FAIL - precision insufficient")
```

**Interpretation:**
- ΔC < 10⁻¹⁴ → Tier 1 quality (standard)
- ΔC < 10⁻²⁵ → Tier 2 quality (ultra-high precision)
- ΔC > 10⁻¹⁰ → Integration failure, check for close encounters

## Time Reversibility Tests

**Location**: `src/python/validation/time_reversibility.py`

Symplectic integrators should be time-reversible: forward → backward returns to start.

```python
from src.python.validation.time_reversibility import TimeReversibilityTester

tester = TimeReversibilityTester(integrator=integrator)

result = tester.test_reversibility(
    state0=initial_state,
    t_half=50.0,      # integrate to t=50, then back to t=0
    dt=0.01
)

print(f"Position error: {result['rms_pos_error']:.3e}")
print(f"Velocity error: {result['rms_vel_error']:.3e}")

# Validation criteria
if result['rms_pos_error'] < 1e-12:
    print("Tier 1 reversibility PASS")
elif result['rms_pos_error'] < 1e-20:
    print("Tier 2 reversibility PASS")
```

**Expected Results:**
- Symplectic integrators (Yoshida8): Δq ~ machine epsilon × N_steps
- Non-symplectic (IAS15): Δq may grow with integration time
- Tier 2 with QD: Δq < 10⁻²⁰ possible

## Shadow Hamiltonian Analysis

**Location**: `src/python/validation/shadow_hamiltonian.py`

**Theory**: Symplectic integrators exactly conserve a "shadow Hamiltonian":
```
H̃ = H + h²·H₂ + h⁴·H₄ + O(h⁶)
```

where h is timestep. The shadow Hamiltonian drift reveals true backward error.

```python
from src.python.validation.shadow_hamiltonian import ShadowHamiltonianAnalyzer

analyzer = ShadowHamiltonianAnalyzer(dynamics_func=cr3bp_dynamics)

result = analyzer.analyze(
    times=times,
    states=states,
    dt=0.01
)

print(f"H₂ correction magnitude: {result['H2']:.3e}")
print(f"Shadow H drift rate: {result['drift_rate']:.3e} per period")
print(f"Effective order: {result['effective_order']}")

# Validation
if result['drift_rate'] < 1e-14:
    print("Shadow Hamiltonian analysis PASS")
```

**Key Metrics:**
- `H2`: Leading-order correction term
- `drift_rate`: How fast shadow Hamiltonian drifts per period
- `effective_order`: Actual convergence order of integrator

## Complete Validation Workflow

For production trajectories, run all validation methods:

```python
from src.python.utils.dynamics import jacobi_constant, cr3bp_dynamics
from src.python.validation.time_reversibility import TimeReversibilityTester
from src.python.validation.shadow_hamiltonian import ShadowHamiltonianAnalyzer

def validate_trajectory(times, states, mu, integrator, tier=1):
    """Complete validation suite."""
    results = {}

    # 1. Jacobi conservation
    C_values = [jacobi_constant(s, mu) for s in states]
    C_drift = (max(C_values) - min(C_values)) / abs(np.mean(C_values))
    results['jacobi_drift'] = C_drift
    results['jacobi_pass'] = C_drift < (1e-14 if tier == 1 else 1e-25)

    # 2. Time reversibility
    tester = TimeReversibilityTester(integrator=integrator)
    rev_result = tester.test_reversibility(states[0], times[-1]/2, dt=0.01)
    results['reversibility_error'] = rev_result['rms_pos_error']
    results['reversibility_pass'] = rev_result['rms_pos_error'] < (1e-12 if tier == 1 else 1e-20)

    # 3. Shadow Hamiltonian
    analyzer = ShadowHamiltonianAnalyzer(dynamics_func=cr3bp_dynamics)
    shadow_result = analyzer.analyze(times, states, dt=times[1]-times[0])
    results['shadow_drift'] = shadow_result['drift_rate']
    results['shadow_pass'] = shadow_result['drift_rate'] < (1e-14 if tier == 1 else 1e-25)

    # Overall
    results['all_pass'] = all([
        results['jacobi_pass'],
        results['reversibility_pass'],
        results['shadow_pass']
    ])

    return results

# Usage
results = validate_trajectory(times, states, mu, integrator, tier=1)
print(f"Validation: {'PASS' if results['all_pass'] else 'FAIL'}")
```

## Batch Validation

For catalogue-scale validation:

```python
def validate_catalogue(trajectories, mu, tier=1):
    """Validate entire trajectory catalogue."""
    summary = {
        'total': len(trajectories),
        'passed': 0,
        'failed': 0,
        'failures': []
    }

    for i, traj in enumerate(trajectories):
        results = validate_trajectory(
            traj['times'], traj['states'], mu,
            traj['integrator'], tier=tier
        )

        if results['all_pass']:
            summary['passed'] += 1
        else:
            summary['failed'] += 1
            summary['failures'].append({
                'index': i,
                'jacobi_drift': results['jacobi_drift'],
                'reason': 'jacobi' if not results['jacobi_pass'] else
                         'reversibility' if not results['reversibility_pass'] else
                         'shadow'
            })

    print(f"Passed: {summary['passed']}/{summary['total']}")
    print(f"Failed: {summary['failed']}")
    return summary
```

## Diagnosing Failures

**Jacobi drift too large:**
1. Check for close encounters (r < 0.01)
2. Reduce timestep
3. Switch to AdaptiveSymplectic with Sundman transformation
4. Promote to Tier 2 precision

**Reversibility error growing:**
1. Verify integrator is symplectic (Yoshida8, not IAS15)
2. Check for numerical overflow
3. Reduce timestep

**Shadow Hamiltonian drift:**
1. Normal for non-symplectic integrators
2. For symplectic: indicates roundoff accumulation
3. Use higher precision arithmetic (QD)

## Tests

```bash
# All validation tests
pytest tests/validation/ -v

# Specific tests
pytest tests/validation/test_time_reversibility.py -v
pytest tests/validation/test_shadow_hamiltonian.py -v
pytest tests/test_dynamics.py::test_jacobi_constant -v
```

## References

- `src/python/validation/` - All validation implementations
- `src/python/utils/dynamics.py` - Jacobi constant computation
- `Science-Research-Docs/Explanation_DoubleDoubleArithmetic.md` - Tier 2 precision
- Hairer, Lubich, Wanner - "Geometric Numerical Integration" (shadow Hamiltonian theory)
