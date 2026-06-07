---
name: wp3-symbolic-regression
description: >
  Symbolic regression and sparse identification (SINDy) for discovering conserved quantities
  from trajectory data. Use when: (1) running SINDy sparse regression on basis functions,
  (2) running PySR evolutionary symbolic regression, (3) using hybrid SINDy+PySR pipelines,
  (4) validating candidate expressions for conservation, (5) testing multi-scale conservation,
  (6) detecting quasi-periodic behavior, (7) measuring long-time stability drift,
  (8) interpreting and classifying discovered expressions, (9) simplifying complex expressions,
  or (10) scoring candidates for physical interpretability. Triggers on requests involving
  symbolic regression, SINDy, LASSO, sparse identification, PySR, evolutionary search,
  expression simplification, conservation testing, Poisson bracket validation, multi-scale
  validation, interpretability scoring, or candidate expression analysis.
---

# WP3 Symbolic Regression

Symbolic regression and SINDy for discovering conserved quantities from trajectory data.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SYMBOLIC REGRESSION PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Trajectory Data (times, states)                                           │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ STAGE 1: Basis Function Library                                 │      │
│   │ • Polynomial, Rational, Spinor, Elliptic, Theta                │      │
│   │ • ~50-200 candidate functions                                   │      │
│   └────────────────────────────┬────────────────────────────────────┘      │
│                                │                                            │
│         ┌──────────────────────┼──────────────────────┐                    │
│         ▼                      ▼                      ▼                    │
│   ┌───────────┐          ┌───────────┐          ┌───────────┐              │
│   │  SINDy    │          │   PySR    │          │  Hybrid   │              │
│   │  (Fast)   │          │  (Slow)   │          │  (Best)   │              │
│   │  LASSO    │          │ Evolution │          │ SINDy→PySR│              │
│   └─────┬─────┘          └─────┬─────┘          └─────┬─────┘              │
│         │                      │                      │                    │
│         └──────────────────────┼──────────────────────┘                    │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ STAGE 2: Conservation Validation                                │      │
│   │ • Multi-scale test (dt = 0.01, 0.1, 1.0, 10.0)                  │      │
│   │ • Long-time stability (drift < 10⁻¹⁰ per period)               │      │
│   │ • Quasi-periodic detection                                      │      │
│   └────────────────────────────┬────────────────────────────────────┘      │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ STAGE 3: Interpretability Scoring                               │      │
│   │ • Function type classification (9 categories)                   │      │
│   │ • Physical symmetry detection                                   │      │
│   │ • Expression simplification                                     │      │
│   └────────────────────────────┬────────────────────────────────────┘      │
│                                ▼                                            │
│                    Ranked Candidate List → WP4                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Method Selection

| Method | Speed | Discovery Power | Interpretability | Best For |
|--------|-------|-----------------|------------------|----------|
| **SINDy** | Fast (seconds) | Limited to basis | High | Known basis, sparse solution |
| **PySR** | Slow (minutes-hours) | Can discover new forms | Medium | Unknown functional form |
| **Hybrid** | Medium | Best of both | High | Production use |

### Decision Tree

```
Is functional form known?
├─ Yes → SINDy (LASSO on basis)
└─ No → Need evolutionary search?
         ├─ No → Try SINDy first, then PySR if fails
         └─ Yes → PySR or Hybrid
```

---

## Quick Start

```python
from src.python.symbolic.regression_pipeline import SymbolicRegressionPipeline
import numpy as np

# Generate trajectory
times, states = integrator.integrate(state0, (0, 100), dt=0.1)

# Create pipeline with default settings
pipeline = SymbolicRegressionPipeline(
    basis_type='polynomial',
    max_complexity=10,
    method='hybrid'
)

# Search for conserved quantities
results = pipeline.search(times, states, mu=mu)

# Display top candidates
for i, cand in enumerate(results.candidates[:3]):
    print(f"\n=== Candidate {i+1} ===")
    print(f"Expression: {cand.expression}")
    print(f"Conservation error: {cand.conservation_error:.2e}")
    print(f"Confidence: {cand.confidence:.3f}")
    print(f"Interpretability: {cand.interpretability:.2f}")
```

---

## SINDy (Sparse Identification)

**Location**: `src/python/symbolic/regression_pipeline.py`

### Theory

Express conserved quantity as sparse linear combination of basis functions:

```
I(x) = Σᵢ cᵢ φᵢ(x)   where most cᵢ = 0
```

**Optimization problem** (LASSO):
```
min ||Φc - 0||₂² + λ||c||₁

where:
- Φ = matrix of basis function values [φ₁(x), φ₂(x), ...]
- c = coefficient vector
- λ = regularization strength (sparsity)
- Target = 0 (we want dI/dt = 0)
```

### Conservation-Constrained SINDy

For conservation, we want dI/dt ≈ 0 along trajectory:

```
dI/dt = Σᵢ cᵢ (∂φᵢ/∂x · ẋ) ≈ 0
```

**Optimization**:
```
min ||Φ̇c||₂² + λ||c||₁

where Φ̇ = time derivatives of basis functions
```

### Usage

```python
from src.python.symbolic.regression_pipeline import SINDyRegressor

# Basic SINDy with polynomial basis
sindy = SINDyRegressor(
    basis_type='polynomial',
    max_degree=4,
    threshold=0.1,        # Sparsity threshold (coefficients < threshold → 0)
    alpha=0.01            # LASSO regularization strength
)

result = sindy.fit(times, states)

print(f"Non-zero terms: {sum(result.coefficients != 0)}")
print(f"Expression: {result.expression}")
print(f"Conservation error: {result.error:.2e}")
```

### SINDy with Custom Basis

```python
from src.python.symbolic.spinor_basis import generate_spinor_basis

# Use spinor basis for close-encounter trajectories
spinor_funcs = generate_spinor_basis()

sindy = SINDyRegressor(
    basis_functions=spinor_funcs,  # Custom basis
    threshold=0.05,
    alpha=0.001
)

result = sindy.fit(times, states)
```

### Conservation-Constrained SINDy

```python
from src.python.symbolic.regression_pipeline import ConservationSINDy

# Explicitly enforce dI/dt = 0 in loss function
sindy = ConservationSINDy(
    basis_type='polynomial',
    max_degree=3,
    conservation_weight=10.0  # Weight on dI/dt = 0 constraint
)

result = sindy.fit(times, states)
print(f"dI/dt error: {result.time_derivative_error:.2e}")
```

**Reference**: See `references/sindy-theory.md` for full theory.

---

## PySR (Evolutionary Symbolic Regression)

**Location**: `src/python/symbolic/regression_pipeline.py`

### Theory

Evolutionary search for symbolic expressions using genetic programming:
1. Initialize population of random expressions
2. Evaluate fitness (conservation error)
3. Select, crossover, mutate
4. Repeat until convergence

### Usage

```python
from src.python.symbolic.regression_pipeline import PySRRegressor

# Create PySR regressor
pysr = PySRRegressor(
    populations=100,              # Number of parallel populations
    niterations=50,               # Iterations per population
    binary_operators=['+', '-', '*', '/'],
    unary_operators=['sin', 'cos', 'sqrt', 'exp'],
    maxsize=15,                   # Maximum expression complexity
    timeout_in_seconds=300        # Time limit
)

# Run evolutionary search
result = pysr.fit(times, states, target='conservation')

# Pareto front: trade-off between complexity and accuracy
print("Pareto front of expressions:")
for expr in result.pareto_front:
    print(f"  Complexity {expr.complexity}: {expr.expression}")
    print(f"    Error: {expr.error:.2e}")
```

### PySR with Custom Operators

```python
from scipy.special import ellipj

# Add elliptic functions to operator set
def jacobi_sn(x, m=0.5):
    sn, cn, dn, ph = ellipj(x, m)
    return sn

pysr = PySRRegressor(
    binary_operators=['+', '-', '*', '/'],
    unary_operators=['sin', 'cos', 'sn', 'cn', 'dn'],
    extra_sympy_mappings={
        'sn': lambda x: jacobi_sn(x, m),
        'cn': lambda x: jacobi_cn(x, m),
        'dn': lambda x: jacobi_dn(x, m)
    },
    maxsize=20
)
```

**Reference**: See `references/pysr-usage.md` for advanced usage.

---

## Hybrid Pipeline

Combine SINDy (fast initial search) with PySR (flexible refinement):

```python
from src.python.symbolic.regression_pipeline import HybridRegressor

# Stage 1: SINDy for initial candidates
# Stage 2: PySR for refinement
hybrid = HybridRegressor(
    sindy_threshold=0.1,
    pysr_iterations=20,
    simplify_expressions=True
)

result = hybrid.fit(times, states)

print("=== SINDy Candidates ===")
for c in result.sindy_candidates[:3]:
    print(f"  {c.expression}: error={c.error:.2e}")

print("\n=== Refined by PySR ===")
for c in result.refined_candidates[:3]:
    print(f"  {c.expression}: error={c.error:.2e}")
```

---

## Validation

**Location**: `src/python/symbolic/enhanced_validation.py`

### Multi-Scale Conservation Test

Test conservation at multiple time scales to catch slowly-varying functions:

```python
from src.python.symbolic.enhanced_validation import multi_scale_conservation_test

# Test at multiple timescales
scales_result = multi_scale_conservation_test(
    candidate_func=lambda state: result.expression.eval(state),
    times=times,
    states=states,
    scales=[0.01, 0.1, 1.0, 10.0]  # dt values
)

print("Conservation by timescale:")
for scale, error in scales_result.items():
    status = "✓" if error < 1e-10 else "✗"
    print(f"  dt={scale}: error = {error:.2e} {status}")
```

### Long-Time Stability

```python
from src.python.symbolic.enhanced_validation import long_time_stability

stability = long_time_stability(
    candidate_func,
    times,
    states,
    n_periods=1000  # Number of orbital periods
)

print(f"Drift rate: {stability.drift_rate:.2e} per period")
print(f"Total drift: {stability.total_drift:.2e}")
print(f"Is stable: {stability.is_stable}")
```

### Quasi-Periodic Detection

```python
from src.python.symbolic.enhanced_validation import detect_quasi_periodic

qp = detect_quasi_periodic(times, states)

if qp.is_quasi_periodic:
    print(f"Quasi-periodic motion detected!")
    print(f"Frequencies: {qp.frequencies}")
    print(f"Ratio: {qp.frequency_ratio:.4f}")
    print(f"Suggestion: Use elliptic basis with m ≈ {qp.suggested_m:.4f}")
```

**Reference**: See `references/validation-methods.md` for complete validation theory.

---

## Interpretability

**Location**: `src/python/symbolic/interpretability.py`

### Function Type Classification

Classify expressions into 9 physical categories:

| Type | Examples | Score |
|------|----------|-------|
| Polynomial | x², xy, x³ | 1.0 |
| Rational | 1/r, 1/(1+r²) | 0.9 |
| Radical | √r, ∛(x²+y²) | 0.85 |
| Trigonometric | sin(θ), cos(φ) | 0.8 |
| Exponential | e^x, e^(-r) | 0.75 |
| Spinor | \|u\|², u·v | 0.8 |
| Elliptic | sn(u,m), cn(u,m) | 0.7 |
| Theta | θ₁(z,q), θ₃(z,q) | 0.6 |
| Mixed | Complex combinations | 0.3-0.5 |

```python
from src.python.symbolic.interpretability import (
    classify_function,
    interpretability_score,
    detect_physical_symmetry
)

expr = "u1_norm**2 + u2_norm**2"

# Classify function type
func_type = classify_function(expr)
print(f"Type: {func_type}")  # → 'spinor'

# Score interpretability (0-1)
score = interpretability_score(expr)
print(f"Interpretability: {score:.2f}")  # → 0.85

# Detect physical symmetries
symmetries = detect_physical_symmetry(expr)
print(f"Symmetries: {symmetries}")  # → ['rotation_invariant']
```

### Expression Simplification

```python
from src.python.symbolic.simplification import simplify_expression

original = "x**2 + 2*x*y + y**2 + 0*z"
simplified = simplify_expression(original)
print(f"Original: {original}")
print(f"Simplified: {simplified}")  # → "(x + y)**2"
```

---

## Complete Search Workflow

```python
def search_for_integrals(times, states, mu, E, L):
    """Complete symbolic regression workflow."""
    from src.python.symbolic.regression_pipeline import HybridRegressor
    from src.python.symbolic.enhanced_validation import multi_scale_conservation_test
    from src.python.symbolic.interpretability import interpretability_score

    # 1. Run hybrid search
    regressor = HybridRegressor(
        sindy_threshold=0.1,
        pysr_iterations=30
    )
    result = regressor.fit(times, states)

    print(f"Stage 1: Found {len(result.candidates)} raw candidates")

    # 2. Validate each candidate
    validated = []
    for candidate in result.candidates:
        # Multi-scale conservation test
        scales = multi_scale_conservation_test(
            candidate.eval_func,
            times, states,
            scales=[0.1, 1.0, 10.0]
        )

        max_error = max(scales.values())

        if max_error < 1e-10:
            candidate.max_error = max_error
            candidate.interpretability = interpretability_score(candidate.expression)
            validated.append(candidate)

    print(f"Stage 2: {len(validated)} candidates pass validation")

    # 3. Rank by interpretability
    validated.sort(key=lambda c: -c.interpretability)

    # 4. Display results
    print("\n=== Final Candidates ===")
    for i, c in enumerate(validated[:5]):
        print(f"\n{i+1}. {c.expression}")
        print(f"   Max conservation error: {c.max_error:.2e}")
        print(f"   Interpretability: {c.interpretability:.2f}")

    return validated
```

---

## Specialized Search Methods

### Spinor Search

```python
from src.python.symbolic.spinor_search import search_spinor_integral

result = search_spinor_integral(times, states, mu=mu)

if result.success:
    print(f"Found spinor integral: {result.expression}")
    print(f"Pattern type: {result.pattern_type}")
    print(f"Conservation: {result.conservation_error:.2e}")
```

### Elliptic Search

```python
from src.python.symbolic.elliptic_search import search_elliptic_integral

result = search_elliptic_integral(times, states, mu=mu)

if result.success:
    print(f"Found elliptic integral: {result.expression}")
    print(f"Elliptic parameter m: {result.m:.4f}")
```

---

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Too many candidates | Low threshold | Increase `threshold` parameter |
| No candidates found | High threshold or wrong basis | Lower threshold, try different basis |
| PySR too slow | Complex search space | Reduce `niterations`, `populations`, set `timeout` |
| Expressions too complex | No size limit | Reduce `maxsize` in PySR |
| Spurious conservation | Slowly varying function | Use multi-scale validation |
| Numerical noise | Finite precision | Use higher-precision trajectories |

### Diagnostic Function

```python
def diagnose_regression_issues(result, times, states):
    """Diagnose common regression problems."""
    issues = []

    # Check candidate count
    if len(result.candidates) == 0:
        issues.append("No candidates found - try lowering threshold")
    elif len(result.candidates) > 50:
        issues.append("Too many candidates - try raising threshold")

    # Check conservation errors
    for c in result.candidates[:5]:
        if c.conservation_error > 1e-5:
            issues.append(f"High conservation error for {c.expression}")

    # Check interpretability
    avg_interp = np.mean([c.interpretability for c in result.candidates[:10]])
    if avg_interp < 0.3:
        issues.append("Low interpretability - expressions may be too complex")

    if not issues:
        print("✓ No issues detected")
    else:
        for issue in issues:
            print(f"⚠ {issue}")
```

---

## Tests

```bash
# All symbolic regression tests
pytest tests/wp3/test_specialized_search.py -v
pytest tests/wp3/test_enhanced_validation.py -v
pytest tests/wp3/test_interpretability.py -v

# Specific tests
pytest tests/wp3/test_specialized_search.py::test_sindy_basic -v
pytest tests/wp3/test_enhanced_validation.py::test_multi_scale -v
```

---

## References

- `references/sindy-theory.md` - SINDy methodology and theory
- `references/pysr-usage.md` - PySR evolutionary search
- `references/validation-methods.md` - Conservation validation
- `src/python/symbolic/regression_pipeline.py` - Implementation
- Brunton et al. (2016), "Discovering governing equations from data by sparse identification of nonlinear dynamical systems", *PNAS*
- Cranmer et al. (2020), "Discovering symbolic models from deep learning with inductive biases", *NeurIPS*
