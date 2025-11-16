# WP 3.3: Symbolic Regression and Consolidation

## Overview

This module implements **Task 3.3: Symbolic Regression and Consolidation** from the WP3 implementation plan. It serves as the critical bridge between numerical discovery (WP3.1, WP3.2) and rigorous validation (WP4).

**Primary Goal**: Convert numerical candidate integrals into analytical symbolic expressions.

## Module Structure

```
src/python/symbolic/
├── __init__.py                   # Package exports
├── README.md                     # This file
├── basis_functions.py            # Physics-informed basis libraries
├── geometric_invariants.py       # Coordinate-independent quantities
├── regression_pipeline.py        # SINDy/PySR interfaces
├── simplification.py             # Expression optimization
├── validation.py                 # Conservation verification
└── candidate_ranking.py          # Consolidation and ranking
```

## Installation

### Required Dependencies

```bash
# Core dependencies (required)
pip install numpy scipy sympy

# Symbolic regression (optional but recommended)
pip install pysindy  # For SINDy regression
pip install pysr     # For PySR genetic programming

# Note: PySR requires Julia to be installed
# See: https://github.com/MilesCranmer/PySR
```

## Quick Start

### Example 1: Basic Symbolic Regression

```python
import numpy as np
from symbolic import (
    construct_hierarchical_basis,
    sindy_regression,
    simplify_candidate_integral
)

# Define numerical integral
def my_integral(z):
    return z[0]**2 + z[1]**2

# Generate sample data
samples = np.random.randn(1000, 4)  # 1000 states, 4D phase space

# Build basis library
library = construct_hierarchical_basis(
    state_dim=4,
    max_polynomial_degree=2,
    masses=np.array([1.0, 1.0, 1.0])
)

# Perform regression
result = sindy_regression(my_integral, samples, library)

print(f"Discovered expression: {result.expression_str}")
print(f"Residual: {result.residual:.2e}")
```

### Example 2: Complete Pipeline (Discovery → Validation)

```python
from symbolic import *

# 1. Regression
result = sindy_regression(numerical_integral, samples, library)

# 2. Simplification
simplified = simplify_candidate_integral(
    result.expression_sympy,
    state_variables=[q0, q1, p0, p1]
)

# 3. Validation
validation = validate_candidate_integral(
    simplified.simplified,
    numerical_integral,
    hamiltonian_func,
    samples,
    [q0, q1, p0, p1]
)

# 4. Create candidate
candidate = CandidateIntegral(
    name="Discovered_1",
    expression_symbolic=simplified.simplified,
    expression_numerical=numerical_integral,
    source=CandidateSource.SYMBOLIC_REGRESSION,
    conservation_error=validation.conservation_error,
    complexity=count_operations(simplified.simplified),
    is_independent=validation.is_independent,
    validation_result=validation
)

print(f"Is conserved: {validation.is_conserved}")
print(f"Conservation error: {validation.conservation_error:.2e}")
```

### Example 3: Consolidating Multiple Candidates

```python
from symbolic import consolidate_and_rank, generate_candidate_report

# Collect candidates from all sources
all_candidates = []

# From WP3.1 (geometric)
all_candidates.extend(wp31_candidates)

# From WP3.2 (ML)
all_candidates.extend(wp32_candidates)

# From WP3.3 (symbolic regression)
all_candidates.extend(wp33_candidates)

# Rank by quality
ranked = consolidate_and_rank(
    all_candidates,
    sample_states=samples,
    known_trivial=[energy_func, angular_momentum_func],
    remove_duplicates=True
)

# Generate report
report = generate_candidate_report(ranked, top_n=10)
print(report)

# Save to file
with open('top_candidates.md', 'w') as f:
    f.write(report)
```

## Key Features

### 1. Physics-Informed Basis Functions

Automatically generate basis functions respecting the physics:

- **Polynomial**: Linear, quadratic, cubic terms
- **Geometric**: Distances, angles, radial velocities
- **Conservation-based**: E, L, and their powers
- **Transcendental**: sin, cos, exp, log (optional)

```python
from symbolic import construct_hierarchical_basis, CoordinateSystem

library = construct_hierarchical_basis(
    state_dim=8,
    coordinate_system=CoordinateSystem.S1_BUNDLE,
    masses=np.array([1.0, 1.0, 1.0]),
    max_polynomial_degree=3,
    include_transcendental=True,
    include_conservation=True
)

print(f"Total basis functions: {len(library.functions)}")
```

### 2. Multiple Regression Methods

**SINDy** (Sparse Identification):
- Fast and interpretable
- Best for polynomial expressions
- Enforces sparsity (few terms)

```python
result = sindy_regression(
    integral_func,
    samples,
    library,
    threshold=0.01,  # Sparsity parameter
    alpha=0.05       # Regularization
)
```

**PySR** (Evolutionary Search):
- Discovers complex forms
- Transcendental functions
- Pareto optimization (accuracy vs. complexity)

```python
result = pysr_regression(
    integral_func,
    samples,
    niterations=100,
    maxsize=20,
    binary_operators=["+", "-", "*", "/", "^"],
    unary_operators=["square", "sin", "cos"]
)
```

**Hierarchical Search**:
- Tries increasing complexity automatically
- Stops when good fit found

```python
result = hierarchical_regression(
    integral_func,
    samples,
    state_dim=8,
    masses=masses,
    method='sindy',
    max_complexity=3,
    residual_threshold=1e-8
)
```

### 3. Expression Simplification

Automatically simplify discovered expressions:

```python
from symbolic import simplify_candidate_integral

result = simplify_candidate_integral(
    expr=complex_expression,
    state_variables=[q0, q1, p0, p1],
    known_conserved={'E': energy_expr, 'L': angular_momentum_expr},
    aggressive=True  # Try harder to simplify
)

print(f"Original:   {result.original} ({count_operations(result.original)} ops)")
print(f"Simplified: {result.simplified} ({count_operations(result.simplified)} ops)")
print(f"Reduction:  {result.reduction_factor:.2f}")
```

### 4. Comprehensive Validation

Verify candidates are genuine:

```python
validation = validate_candidate_integral(
    expr_symbolic,
    expr_numerical,
    hamiltonian_func,
    sample_states,
    state_symbols,
    known_integrals=[energy_func, L_func],
    test_trajectories=initial_conditions,
    hamiltonian_symbolic=H_sym
)

print(f"Conserved: {validation.is_conserved}")
print(f"Error: {validation.conservation_error:.2e}")
print(f"Independent: {validation.is_independent}")
print(f"Poisson bracket: {validation.poisson_bracket_with_H}")
```

### 5. Candidate Ranking

Automatically rank by quality:

```python
ranked = consolidate_and_rank(
    candidates,
    sample_states,
    weights={
        'conservation': 1000.0,     # Most important
        'complexity': 1.0,
        'independence_bonus': -100.0,
        'not_independent_penalty': 200.0
    }
)

# Best candidates first
for i, cand in enumerate(ranked[:5], 1):
    print(f"{i}. {cand.name}: score={cand.score:.2f}, error={cand.conservation_error:.2e}")
```

## Integration with WP3.1 and WP3.2

### From WP3.1 (Geometric Search)

```python
from symbolic import create_candidate_from_wp31_killing
from analysis import ConservedIntegral  # From WP3.1

# Assuming you have a Killing field result from WP3.1
killing_result = ...  # From WP3.1 pipeline

# Convert to WP3.3 candidate
candidate = create_candidate_from_wp31_killing(
    killing_field_name=killing_result.name,
    integral_expr=killing_result.symbolic_expr,
    integral_func=killing_result.evaluate,
    validation=validation_result,
    is_tensor=False
)
```

### From WP3.2 (ML Discovery)

```python
from symbolic import create_candidate_from_wp32_ml

# Assuming you have ML model predictions
ml_model = ...  # Trained HNN from WP3.2
I_phi = ml_model.predict_invariant  # Numerical function

# Perform symbolic regression on ML output
regression_result = sindy_regression(I_phi, samples, library)

# Create candidate
candidate = create_candidate_from_wp32_ml(
    model_name="HNN_S1_bundle",
    integral_expr=regression_result.expression_sympy,
    integral_func=I_phi,
    validation=validation_result,
    is_sympnet=False
)
```

## Output for WP4

The final output is a ranked list of analytical expressions ready for WP4 validation:

```markdown
# Top Candidate Conserved Integrals

| Rank | Name | Expression | Conservation Error | Complexity | Independent |
|------|------|------------|-------------------|------------|-------------|
| 1 | I_K1 | p_θ | 3.2e-14 | 1 | ✓ |
| 2 | I_ML | r₁₂² + r₂₃² | 1.5e-07 | 5 | ✓ |
| 3 | I_Symbolic | E·L·cos(θ) | 8.4e-06 | 4 | ✗ |
```

These can be directly passed to WP4 for:
- Analytical Poisson bracket computation
- Involution testing
- Functional independence verification
- Morales-Ramis analysis

## API Reference

### Core Classes

- **`BasisLibrary`**: Collection of basis functions
- **`RegressionResult`**: Output from symbolic regression
- **`SimplificationResult`**: Simplified expression with steps
- **`ValidationResult`**: Conservation test results
- **`CandidateIntegral`**: Complete candidate with metadata

### Main Functions

- **`construct_hierarchical_basis()`**: Build physics-informed basis
- **`sindy_regression()`**: Sparse regression
- **`pysr_regression()`**: Evolutionary search
- **`simplify_candidate_integral()`**: Simplify expression
- **`validate_candidate_integral()`**: Test conservation
- **`consolidate_and_rank()`**: Rank all candidates
- **`generate_candidate_report()`**: Create summary report

See individual module docstrings for detailed API documentation.

## Performance Notes

### Computational Cost

| Operation | Typical Time | Scales With |
|-----------|-------------|-------------|
| SINDy regression | Seconds to minutes | Basis size, samples |
| PySR regression | Minutes to hours | Complexity, iterations |
| Simplification | Milliseconds | Expression size |
| Validation (single trajectory) | Seconds | Integration time |
| Validation (ensemble) | Minutes | Number of trajectories |

### Recommendations

- **SINDy first**: Fast, works well for polynomial integrals
- **PySR for hard cases**: Use when SINDy doesn't find good fit
- **Hierarchical search**: Balances speed and completeness
- **Parallel validation**: Test multiple trajectories in parallel

## Troubleshooting

### PySR Installation Issues

```bash
# Install Julia first
curl -fsSL https://install.julialang.org | sh

# Then install PySR
pip install pysr
```

### Import Errors

If you get `ModuleNotFoundError`, ensure you're in the project root:

```python
import sys
sys.path.insert(0, '/home/user/3body')
from src.python.symbolic import *
```

### Numerical Issues

If regression produces `NaN` or `Inf`:
- Check for division by zero in basis functions
- Ensure sample states are valid (no singularities)
- Try different basis functions or regression parameters

## References

1. **SINDy**: Brunton et al., "Discovering governing equations from data" (2016)
2. **PySR**: Cranmer, "Interpretable ML for Science with PySR" (2023)
3. **WP3 Design**: `Project-Design-Docs/WP3/WP3-Complete-Overview.md`
4. **Task 3.3 Plan**: `Project-Design-Docs/WP3/WP3.3-Symbolic-Regression-Summary.md`

## Contributing

This module is part of the three-body integrability research project. For questions or contributions:

- See main project documentation
- Follow code style in existing modules
- Add tests for new features
- Update this README for significant changes

---

**Version**: 1.0.0
**Status**: Complete Implementation
**Date**: 2025-11-15
