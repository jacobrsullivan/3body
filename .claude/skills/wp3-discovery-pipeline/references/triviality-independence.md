# Triviality and Independence Testing

Theory and implementation for filtering trivial candidates and testing functional independence.

## Table of Contents

1. [Overview](#overview)
2. [Triviality Criteria](#triviality-criteria)
3. [Functional Independence](#functional-independence)
4. [Jacobian Rank Test](#jacobian-rank-test)
5. [Implementation](#implementation)
6. [Edge Cases](#edge-cases)

---

## Overview

### The Filtering Problem

After symbolic regression, we typically have many candidate conserved quantities. Most are **trivial**:
- Constants (variance = 0)
- Known integrals (E, L, C)
- Linear combinations of known integrals

**Goal**: Identify truly new, functionally independent integrals.

### Pipeline Position

```
Raw Candidates (N ~ 50-200)
         │
         ▼
┌─────────────────────┐
│ Triviality Filter   │ → Remove ~80%
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Independence Test   │ → Remove ~15%
└─────────┬───────────┘
          │
          ▼
Final Candidates (N ~ 1-5)
```

---

## Triviality Criteria

### Criterion 1: Constants

A candidate I(x) is trivial if it's constant along the trajectory:

```
Var(I) = (1/N) Σᵢ (I(xᵢ) - μ)² < ε

where μ = mean(I), ε ~ 10⁻¹²
```

**Implementation**:
```python
def is_constant(I_values, tolerance=1e-12):
    """Check if candidate is effectively constant."""
    variance = np.var(I_values)
    mean_sq = np.mean(I_values)**2 + 1e-15
    relative_variance = variance / mean_sq
    return relative_variance < tolerance
```

### Criterion 2: Known Integrals

A candidate is trivial if it correlates strongly with known integrals:

```
|corr(I, E)| > 0.99  →  I ≈ f(E)
|corr(I, L)| > 0.99  →  I ≈ f(L)
|corr(I, C)| > 0.99  →  I ≈ f(C)
```

**Implementation**:
```python
def correlates_with_known(I_values, known_integrals, threshold=0.99):
    """Check correlation with known integrals."""
    for name, known_values in known_integrals.items():
        corr = np.corrcoef(I_values, known_values)[0, 1]
        if np.abs(corr) > threshold:
            return True, name, corr
    return False, None, None
```

### Criterion 3: Linear Combinations

A candidate is trivial if it's a linear combination of known integrals:

```
I ≈ αE + βL + γC + δ
```

Test via linear regression:
```
min_{α,β,γ,δ} ||I - (αE + βL + γC + δ)||²
```

If residual is small, candidate is trivial.

**Implementation**:
```python
def is_linear_combination(I_values, known_integrals, tolerance=1e-10):
    """
    Check if I is a linear combination of known integrals.
    
    Solves: I ≈ Σⱼ αⱼ Kⱼ + δ
    """
    # Build design matrix [K₁, K₂, ..., 1]
    n = len(I_values)
    m = len(known_integrals) + 1  # +1 for constant term
    
    X = np.zeros((n, m))
    for j, (name, values) in enumerate(known_integrals.items()):
        X[:, j] = values
    X[:, -1] = 1  # Constant term
    
    # Least squares fit
    coeffs, residuals, rank, s = np.linalg.lstsq(X, I_values, rcond=None)
    
    # Compute relative residual
    predicted = X @ coeffs
    residual = np.linalg.norm(I_values - predicted) / (np.linalg.norm(I_values) + 1e-15)
    
    is_combination = residual < tolerance
    
    return is_combination, coeffs, residual
```

### Criterion 4: Fiber Momentum (for lifted spaces)

In S¹ bundle lift, the fiber momentum p_θ is conserved by construction. It's trivial for our purposes.

```python
def is_fiber_momentum(expression_str):
    """Check if candidate is just fiber momentum."""
    trivial_patterns = ['p_theta', 'p[3]', 'momentum[3]', 'fiber_momentum']
    expr_lower = expression_str.lower()
    return any(pattern in expr_lower for pattern in trivial_patterns)
```

---

## Functional Independence

### Definition

Functions {I₁, I₂, ..., Iₖ} are **functionally independent** on a domain D if:

```
rank(J) = k  almost everywhere in D

where J = [∇I₁, ∇I₂, ..., ∇Iₖ]ᵀ  (Jacobian matrix)
```

Equivalently: No Iⱼ can be expressed as a function of the others.

### For Invariant Discovery

Given known integrals {E, L, C}, a new candidate Ĩ is **independent** if:

```
rank([∇E, ∇L, ∇C, ∇Ĩ]) = 4  (one more than rank of [∇E, ∇L, ∇C])
```

### Geometric Interpretation

- Each independent integral constrains motion to a lower-dimensional surface
- k independent integrals in n-dimensional phase space → motion on (n-k)-dim surface
- For Liouville integrability of 2n-dim system: need n independent integrals in involution

---

## Jacobian Rank Test

### Algorithm

```
Input: Candidate function Ĩ, known functions {E, L, C}, sample states
Output: Is Ĩ independent? Pass rate

1. For each sample state x:
   a. Compute gradients ∇E(x), ∇L(x), ∇C(x), ∇Ĩ(x)
   b. Form Jacobian J = [∇E; ∇L; ∇C; ∇Ĩ]
   c. Compute rank(J) with tolerance τ
   d. Record if rank increased (compared to without Ĩ)

2. Pass rate = (# states where rank increased) / (total states)

3. Return: pass_rate > 0.99
```

### Numerical Gradient Computation

```python
def numerical_gradient(func, x, epsilon=1e-7):
    """
    Compute gradient via central differences.
    
    ∂f/∂xᵢ ≈ (f(x + εeᵢ) - f(x - εeᵢ)) / (2ε)
    """
    n = len(x)
    grad = np.zeros(n)
    
    for i in range(n):
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += epsilon
        x_minus[i] -= epsilon
        
        grad[i] = (func(x_plus) - func(x_minus)) / (2 * epsilon)
    
    return grad
```

### Rank Computation

```python
def numerical_rank(matrix, tolerance=1e-8):
    """
    Compute numerical rank via SVD.
    
    rank = number of singular values > tolerance * max(singular values)
    """
    U, S, Vt = np.linalg.svd(matrix)
    threshold = tolerance * S[0] if len(S) > 0 else tolerance
    return np.sum(S > threshold)
```

### Complete Jacobian Rank Test

```python
def jacobian_rank_test(candidate_func, known_funcs, states, tolerance=1e-8):
    """
    Test functional independence via Jacobian rank.
    
    Args:
        candidate_func: Function Ĩ(state) → scalar
        known_funcs: List of functions [E, L, C, ...]
        states: Array of sample states (N × dim)
        tolerance: Rank tolerance
    
    Returns:
        passed: bool (pass_rate > 0.99)
        pass_rate: Fraction of states where rank increased
        details: Dict with diagnostic info
    """
    n_samples = len(states)
    n_known = len(known_funcs)
    dim = states.shape[1]
    
    rank_increased_count = 0
    base_ranks = []
    extended_ranks = []
    
    for state in states:
        # Compute gradients of known functions
        known_grads = np.array([
            numerical_gradient(f, state) for f in known_funcs
        ])
        
        # Compute gradient of candidate
        candidate_grad = numerical_gradient(candidate_func, state)
        
        # Base Jacobian (known only)
        J_base = known_grads
        rank_base = numerical_rank(J_base, tolerance)
        base_ranks.append(rank_base)
        
        # Extended Jacobian (known + candidate)
        J_extended = np.vstack([known_grads, candidate_grad])
        rank_extended = numerical_rank(J_extended, tolerance)
        extended_ranks.append(rank_extended)
        
        # Check if rank increased
        if rank_extended > rank_base:
            rank_increased_count += 1
    
    pass_rate = rank_increased_count / n_samples
    passed = pass_rate > 0.99
    
    return {
        'passed': passed,
        'pass_rate': pass_rate,
        'mean_base_rank': np.mean(base_ranks),
        'mean_extended_rank': np.mean(extended_ranks),
        'rank_increase': np.mean(extended_ranks) - np.mean(base_ranks)
    }
```

---

## Implementation

### Complete Triviality Checker

```python
class TrivialityChecker:
    """
    Check if candidate integrals are trivial.
    """
    
    def __init__(self, known_integrals, constant_tol=1e-12, 
                 correlation_threshold=0.99, linear_tol=1e-10):
        """
        Args:
            known_integrals: Dict {name: values_array}
            constant_tol: Tolerance for constant detection
            correlation_threshold: Threshold for correlation test
            linear_tol: Tolerance for linear combination test
        """
        self.known_integrals = known_integrals
        self.constant_tol = constant_tol
        self.correlation_threshold = correlation_threshold
        self.linear_tol = linear_tol
    
    def check(self, candidate_values, expression_str=None):
        """
        Check if candidate is trivial.
        
        Returns:
            (is_trivial, reason)
        """
        # Test 1: Constant
        if is_constant(candidate_values, self.constant_tol):
            return True, "constant"
        
        # Test 2: Correlation with known
        is_corr, name, corr = correlates_with_known(
            candidate_values, self.known_integrals, self.correlation_threshold
        )
        if is_corr:
            return True, f"correlates_with_{name} (r={corr:.3f})"
        
        # Test 3: Linear combination
        is_lin, coeffs, residual = is_linear_combination(
            candidate_values, self.known_integrals, self.linear_tol
        )
        if is_lin:
            return True, f"linear_combination (residual={residual:.2e})"
        
        # Test 4: Fiber momentum (if expression available)
        if expression_str and is_fiber_momentum(expression_str):
            return True, "fiber_momentum"
        
        return False, None
    
    def filter(self, candidates, states):
        """Filter out trivial candidates."""
        non_trivial = []
        
        for cand in candidates:
            values = cand.eval_func(states)
            is_trivial, reason = self.check(values, cand.expression)
            
            if not is_trivial:
                non_trivial.append(cand)
            else:
                cand.trivial_reason = reason
        
        return non_trivial
```

### Complete Independence Tester

```python
class IndependenceTest:
    """
    Test functional independence of candidate integrals.
    """
    
    def __init__(self, tolerance=1e-8, min_pass_rate=0.99):
        self.tolerance = tolerance
        self.min_pass_rate = min_pass_rate
    
    def is_independent(self, candidate_func, known_funcs, states):
        """
        Test if candidate is independent of known functions.
        """
        result = jacobian_rank_test(
            candidate_func, known_funcs, states, self.tolerance
        )
        return result['passed']
    
    def find_independent_set(self, candidates, states, known_funcs=None):
        """
        Find maximal set of mutually independent candidates.
        
        Greedy algorithm: Add candidates one by one if they increase rank.
        """
        if known_funcs is None:
            known_funcs = []
        
        independent = []
        current_funcs = list(known_funcs)
        
        for cand in candidates:
            # Test if candidate is independent of current set
            result = jacobian_rank_test(
                cand.eval_func, current_funcs, states, self.tolerance
            )
            
            if result['passed']:
                independent.append(cand)
                current_funcs.append(cand.eval_func)
        
        return independent
```

---

## Edge Cases

### Degenerate States

At certain states (e.g., equilibria), the Jacobian may have lower rank:

```python
def filter_degenerate_states(states, known_funcs, min_rank=3):
    """Remove states where known integrals have degenerate Jacobian."""
    valid_states = []
    
    for state in states:
        grads = [numerical_gradient(f, state) for f in known_funcs]
        J = np.array(grads)
        rank = numerical_rank(J)
        
        if rank >= min_rank:
            valid_states.append(state)
    
    return np.array(valid_states)
```

### Numerical Gradient Issues

Near singularities, numerical gradients may fail:

```python
def safe_numerical_gradient(func, x, epsilon=1e-7):
    """Gradient with error handling."""
    try:
        grad = numerical_gradient(func, x, epsilon)
        if np.any(np.isnan(grad)) or np.any(np.isinf(grad)):
            return None
        return grad
    except:
        return None
```

### Rank Tolerance Selection

Too tight tolerance → false positives (noise looks like dependence)
Too loose tolerance → false negatives (miss near-dependence)

**Heuristic**: Use tolerance ≈ 10⁻⁸ for double precision, scale with data noise.

---

## References

- Arnold, V.I. (1989). *Mathematical Methods of Classical Mechanics*, Ch. 10
- Olver, P.J. (1993). *Applications of Lie Groups to Differential Equations*
- Golub, G.H. & Van Loan, C.F. (2013). *Matrix Computations*, Ch. 2 (SVD and rank)
