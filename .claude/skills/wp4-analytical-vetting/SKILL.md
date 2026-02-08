---
name: wp4-analytical-vetting
description: Analytical validation tests for candidate conserved quantities in the three-body problem. Use when computing Poisson brackets, testing involution (mutual commutativity), verifying functional independence via Jacobian rank, or vetting candidates from WP3. Triggers on requests involving {I, H} = 0 tests, Liouville integrability criteria, rank deficiency detection, or analytical gatekeeping of integrals.
---

# WP4 Analytical Vetting

First-stage validation for candidate integrals discovered by WP3.

## Test Selection

| Test | Purpose | Pass Criterion | Threshold |
|------|---------|----------------|-----------|
| Conservation | Is {I, H} = 0? | Poisson bracket vanishes | < 10⁻¹² |
| Involution | Does I commute with E, L, C? | {I, Ij} = 0 for all known | < 10⁻¹⁰ |
| Independence | Is I functionally independent? | Jacobian rank increases | >99% pass rate |

**Decision tree:**
- Candidate from WP3? → Start with Conservation test
- Conservation passes? → Test Involution
- Involution passes? → Test Independence
- All pass? → Proceed to Morales-Ramis (WP4.2)

## Quick Start

```python
from src.python.validation.analytical_vetting import (
    PoissonBracketValidator,
    InvolutionTester,
    IndependenceTester
)

mu = 0.012150585609624  # Earth-Moon mass ratio

# Candidate integral from WP3
def candidate_integral(state, mu):
    x, y, z, vx, vy, vz = state
    # ... your integral expression ...
    return value

# Run all three tests
pb_val = PoissonBracketValidator(mu=mu)
inv_val = InvolutionTester(mu=mu)
ind_val = IndependenceTester(mu=mu)

# Sequential gating
conservation = pb_val.test_conservation(candidate_integral, num_samples=1000)
if not conservation.passed:
    print(f"REJECT: Not conserved ({conservation.max_poisson_bracket:.2e})")
else:
    involution = inv_val.test_involution(candidate_integral, ['energy', 'angular_momentum'])
    if not involution.passed:
        print("REJECT: Not in involution")
    else:
        independence = ind_val.test_independence(
            candidate_integral,
            ['energy', 'angular_momentum', 'jacobi_constant'],
            num_samples=10000
        )
        if independence.passed:
            print("PASS: Proceed to Morales-Ramis test")
```

## Task 4.1.1: Conservation Test

**Location**: `src/python/validation/poisson_brackets.py`

**Theory**: A quantity I is conserved iff {I, H} = 0

```
{I, H} = Σ (∂I/∂qᵢ ∂H/∂pᵢ - ∂I/∂pᵢ ∂H/∂qᵢ)
```

### Symbolic Computation (Preferred)

```python
from src.python.validation.poisson_brackets import compute_poisson_bracket
import sympy as sp

# Define symbolic expression
x, y, vx, vy = sp.symbols('x y vx vy')
I_expr = x**2 + y**2  # example integral
H_expr = (vx**2 + vy**2) / 2 - 1/sp.sqrt(x**2 + y**2)  # example Hamiltonian

# Compute symbolically
pb = compute_poisson_bracket(I_expr, H_expr, symbolic=True)
print(f"{{I, H}} = {pb}")  # Should simplify to 0
```

### Numerical Computation (Fallback)

```python
from src.python.validation.poisson_brackets import compute_poisson_bracket

state = np.array([1.0, 0.5, 0.0, 0.3, 0.5, 0.0])
pb = compute_poisson_bracket(
    integral_func=candidate_integral,
    hamiltonian_func=hamiltonian,
    state=state,
    mu=mu
)
print(f"{{I, H}} ≈ {pb:.2e}")  # Should be < 10⁻¹²
```

### Using the Validator

```python
from src.python.validation.analytical_vetting import PoissonBracketValidator

validator = PoissonBracketValidator(mu=mu)
result = validator.test_conservation(
    integral_func=candidate_integral,
    num_samples=1000
)

print(f"Passed: {result.passed}")
print(f"Max |{{I, H}}|: {result.max_poisson_bracket:.2e}")
print(f"Mean |{{I, H}}|: {result.mean_poisson_bracket:.2e}")
```

**Acceptance**: |{I, H}| < 10⁻¹² at all sample points

## Task 4.1.2: Involution Test

**Location**: `src/python/validation/involution_tester.py`

**Theory**: For Liouville integrability, all integrals must mutually commute:

```
{Iᵢ, Iⱼ} = 0  for all pairs i, j
```

### Testing Against Known Integrals

```python
from src.python.validation.involution_tester import test_involution

result = test_involution(
    integrals=[
        ('Energy', energy_func),
        ('Angular Momentum', angular_momentum_func),
        ('Jacobi Constant', jacobi_constant_func),
        ('Candidate', candidate_integral)
    ],
    mu=mu,
    num_samples=1000
)

# Involution matrix (should be zeros)
print("Involution matrix:")
print(result.involution_matrix)

print(f"All in involution: {result.all_commute}")
```

### Using the Tester Class

```python
from src.python.validation.analytical_vetting import InvolutionTester

tester = InvolutionTester(mu=mu)
result = tester.test_involution(
    integral_func=candidate_integral,
    known_integrals=['energy', 'angular_momentum', 'jacobi_constant']
)

for integral_name, pb_value in result.poisson_brackets.items():
    status = "PASS" if abs(pb_value) < 1e-10 else "FAIL"
    print(f"{{I, {integral_name}}} = {pb_value:.2e} [{status}]")
```

**Acceptance**: |{I, Ij}| < 10⁻¹⁰ for all known integrals

## Task 4.1.3: Functional Independence

**Location**: `src/python/validation/independence_tester.py`

**Theory**: Integrals are independent if their gradients are linearly independent:

```
rank([∇I₁, ∇I₂, ..., ∇Iₖ]) = k
```

### Jacobian Rank Test

```python
from src.python.validation.independence_tester import test_functional_independence

result = test_functional_independence(
    integrals=[energy_func, angular_momentum_func, jacobi_constant_func, candidate_integral],
    mu=mu,
    num_samples=10000,
    tolerance=1e-6
)

print(f"Jacobian rank: {result.rank}")
print(f"Expected rank: {len(integrals)}")
print(f"Pass rate: {result.pass_rate:.1%}")

if result.pass_rate > 0.99:
    print("PASS: Candidate is functionally independent")
else:
    print("FAIL: Candidate depends on known integrals")
```

### Using the Tester Class

```python
from src.python.validation.analytical_vetting import IndependenceTester

tester = IndependenceTester(mu=mu)
result = tester.test_independence(
    integral_func=candidate_integral,
    known_integrals=['energy', 'angular_momentum', 'jacobi_constant'],
    num_samples=10000
)

print(f"Independence: {result.passed}")
print(f"Rank increased by 1: {result.rank_increased}")
print(f"Pass rate: {result.pass_rate:.1%}")
```

**Acceptance**: rank(∇I₁, ..., ∇Iₖ, ∇I_new) = k+1 at >99% of sample points

## Complete Vetting Workflow

```python
def vet_candidate(candidate_func, mu, name="Candidate"):
    """Complete analytical vetting pipeline."""
    from src.python.validation.analytical_vetting import (
        PoissonBracketValidator,
        InvolutionTester,
        IndependenceTester
    )

    print(f"=== Vetting: {name} ===\n")

    # Stage 1: Conservation
    print("Stage 1: Conservation test")
    pb_val = PoissonBracketValidator(mu=mu)
    conservation = pb_val.test_conservation(candidate_func, num_samples=1000)
    print(f"  Max |{{I, H}}| = {conservation.max_poisson_bracket:.2e}")
    if not conservation.passed:
        return {"passed": False, "stage": 1, "reason": "Not conserved"}
    print("  PASS\n")

    # Stage 2: Involution
    print("Stage 2: Involution test")
    inv_val = InvolutionTester(mu=mu)
    involution = inv_val.test_involution(
        candidate_func,
        ['energy', 'angular_momentum', 'jacobi_constant']
    )
    for name, pb in involution.poisson_brackets.items():
        print(f"  {{I, {name}}} = {pb:.2e}")
    if not involution.passed:
        return {"passed": False, "stage": 2, "reason": "Not in involution"}
    print("  PASS\n")

    # Stage 3: Independence
    print("Stage 3: Independence test")
    ind_val = IndependenceTester(mu=mu)
    independence = ind_val.test_independence(
        candidate_func,
        ['energy', 'angular_momentum', 'jacobi_constant'],
        num_samples=10000
    )
    print(f"  Pass rate = {independence.pass_rate:.1%}")
    if not independence.passed:
        return {"passed": False, "stage": 3, "reason": "Functionally dependent"}
    print("  PASS\n")

    print("=== ANALYTICAL VETTING PASSED ===")
    print("Proceed to Morales-Ramis test (WP4.2)")
    return {"passed": True, "stage": 3, "results": {
        "conservation": conservation,
        "involution": involution,
        "independence": independence
    }}

# Usage
result = vet_candidate(candidate_integral, mu=0.012150585609624, name="My Integral")
```

## Validation on Known Integrals

Test the pipeline on known valid integrals:

```python
# Jacobi constant (should pass all tests)
def jacobi_constant(state, mu):
    x, y, z, vx, vy, vz = state
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    Omega = 0.5 * (x**2 + y**2) + (1 - mu) / r1 + mu / r2
    return 2 * Omega - (vx**2 + vy**2 + vz**2)

result = vet_candidate(jacobi_constant, mu=0.012150585609624, name="Jacobi Constant")
assert result["passed"], "Jacobi constant should pass all tests!"
```

## Common Issues

**Conservation test fails?**
- Check numerical precision (use double-double if needed)
- Verify Hamiltonian definition matches coordinate system
- Try symbolic computation if expression available

**Involution test fails?**
- Candidate may be valid but not in involution with claimed integrals
- Check for coordinate system mismatch
- Verify known integrals are correctly defined

**Independence test fails?**
- Candidate is likely a function of known integrals
- Check for hidden dependencies (e.g., C = 2Ω - v² depends on E)
- Use symbolic simplification to check algebraic dependence

**Low pass rate?**
- Increase num_samples for better statistics
- Check for numerical issues near singularities
- Exclude near-collision states from sampling

## Tests

```bash
pytest tests/validation/test_poisson_brackets.py -v
pytest tests/validation/test_involution_tester.py -v
pytest tests/validation/test_independence_tester.py -v
pytest tests/validation/test_analytical_vetting.py -v
```

## References

- `src/python/validation/analytical_vetting.py` - Main validators
- `src/python/validation/poisson_brackets.py` - Poisson bracket computation
- `src/python/validation/involution_tester.py` - Involution testing
- `src/python/validation/independence_tester.py` - Jacobian rank testing
- `Project-Design-Docs/WP4/WP4.1-Analytical-Vetting-Implementation-Plan.md`
