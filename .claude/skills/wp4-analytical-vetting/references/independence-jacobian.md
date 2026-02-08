# Functional Independence via Jacobian Rank Test

Theory and implementation for testing functional independence of conserved quantities.

## Mathematical Foundation

### Definition of Functional Independence

A set of smooth functions {I₁, I₂, ..., Iₖ} on a manifold M is **functionally independent** at a point x if their differentials are linearly independent:

```
rank(dI₁, dI₂, ..., dIₖ)|ₓ = k
```

Equivalently, the gradients ∇I₁, ..., ∇Iₖ are linearly independent at x.

### Jacobian Matrix Formulation

The Jacobian matrix of k functions on ℝⁿ is:

```
J = [∇I₁]     [∂I₁/∂x₁  ∂I₁/∂x₂  ...  ∂I₁/∂xₙ]
    [∇I₂]  =  [∂I₂/∂x₁  ∂I₂/∂x₂  ...  ∂I₂/∂xₙ]
    [ ⋮ ]     [   ⋮        ⋮      ⋱      ⋮    ]
    [∇Iₖ]     [∂Iₖ/∂x₁  ∂Iₖ/∂x₂  ...  ∂Iₖ/∂xₙ]
```

**Independence criterion**: rank(J) = k almost everywhere on M.

### For New Candidate

Given k known independent integrals {I₁, ..., Iₖ} and a candidate Ĩ:

```
Ĩ is independent of {I₁, ..., Iₖ} ⟺ rank([∇I₁, ..., ∇Iₖ, ∇Ĩ]) = k+1
```

### Geometric Interpretation

For a 2n-dimensional phase space:
- k independent integrals → motion confined to (2n-k)-dimensional surface
- n independent integrals in involution → motion on n-dimensional torus (Liouville)

In the three-body problem (n=3, phase space = 6D):
- 3 known integrals (E, L, C) → motion on 3D surface
- A 4th independent integral → motion on 2D surface (highly constrained!)

## SVD-Based Rank Computation

### Numerical Rank via SVD

The most robust method for numerical rank computation:

```python
import numpy as np

def compute_numerical_rank(matrix: np.ndarray, tolerance: float = 1e-8) -> int:
    """
    Compute numerical rank using SVD.
    
    Parameters:
        matrix: k × n Jacobian matrix
        tolerance: Relative tolerance for singular value cutoff
        
    Returns:
        Numerical rank
    """
    U, S, Vt = np.linalg.svd(matrix)
    
    # Relative tolerance based on largest singular value
    threshold = tolerance * S[0] if len(S) > 0 else tolerance
    
    rank = np.sum(S > threshold)
    return rank


def analyze_singular_values(matrix: np.ndarray) -> dict:
    """
    Detailed SVD analysis for rank determination.
    """
    U, S, Vt = np.linalg.svd(matrix)
    
    # Condition number
    cond = S[0] / S[-1] if S[-1] > 0 else np.inf
    
    # Rank at various tolerances
    tolerances = [1e-6, 1e-8, 1e-10, 1e-12]
    ranks = {}
    for tol in tolerances:
        threshold = tol * S[0]
        ranks[tol] = np.sum(S > threshold)
    
    # Gap analysis
    ratios = S[:-1] / S[1:]  # Ratio of consecutive singular values
    max_gap_idx = np.argmax(ratios) if len(ratios) > 0 else -1
    
    return {
        'singular_values': S,
        'condition_number': cond,
        'ranks_by_tolerance': ranks,
        'max_gap_index': max_gap_idx,
        'gap_ratio': ratios[max_gap_idx] if max_gap_idx >= 0 else 1.0
    }
```

### Tolerance Selection Heuristic

```python
def select_rank_tolerance(singular_values: np.ndarray) -> float:
    """
    Heuristically select tolerance for rank determination.
    
    Strategy: Find largest gap in singular value spectrum.
    """
    if len(singular_values) <= 1:
        return 1e-8  # Default
    
    # Log-scale gaps
    log_sv = np.log10(singular_values + 1e-16)
    gaps = -np.diff(log_sv)  # Negative because SV are decreasing
    
    # Find largest gap
    max_gap_idx = np.argmax(gaps)
    
    # Tolerance midway between (in log scale)
    if max_gap_idx < len(singular_values) - 1:
        tol = np.sqrt(singular_values[max_gap_idx] * 
                      singular_values[max_gap_idx + 1])
    else:
        tol = singular_values[-1] * 0.1
    
    # Clamp to reasonable range
    return max(1e-14, min(1e-4, tol / singular_values[0]))
```

## Independence Tester Implementation

### Core Class

```python
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
import numpy as np

@dataclass
class IndependenceResult:
    """Results from functional independence test."""
    passed: bool
    base_rank: int
    extended_rank: int
    rank_increased: bool
    pass_rate: float
    num_samples: int
    tolerance: float
    singular_values_sample: np.ndarray  # From one sample
    failed_states: List[np.ndarray]
    
    def summary(self) -> str:
        return f"""Independence Test Results:
  Passed: {self.passed}
  Base rank (E, L, C): {self.base_rank}
  Extended rank (E, L, C, Ĩ): {self.extended_rank}
  Rank increased: {self.rank_increased}
  Pass rate: {self.pass_rate:.1%}
  Samples: {self.num_samples}
  Tolerance: {self.tolerance:.0e}"""


class IndependenceTester:
    """Test functional independence via Jacobian rank."""
    
    def __init__(self, mu: float, tolerance: float = 1e-8):
        self.mu = mu
        self.tolerance = tolerance
        self._known_integrals = {
            'energy': self._energy,
            'angular_momentum': self._angular_momentum_z,
            'jacobi_constant': self._jacobi_constant
        }
    
    def _energy(self, state, mu):
        x, y, z, vx, vy, vz = state
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        return 0.5*(vx**2 + vy**2 + vz**2) - (1-mu)/r1 - mu/r2
    
    def _angular_momentum_z(self, state, mu):
        x, y, z, vx, vy, vz = state
        return x*vy - y*vx
    
    def _jacobi_constant(self, state, mu):
        x, y, z, vx, vy, vz = state
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        Omega = 0.5*(x**2 + y**2) + (1-mu)/r1 + mu/r2
        return 2*Omega - (vx**2 + vy**2 + vz**2)
    
    def test_independence(
        self,
        candidate: Callable,
        known_integrals: Optional[Dict[str, Callable]] = None,
        num_samples: int = 10000,
        min_pass_rate: float = 0.99,
        seed: int = 42
    ) -> IndependenceResult:
        """
        Test if candidate is functionally independent of known integrals.
        
        Parameters:
            candidate: Function I(state, mu) -> float
            known_integrals: Dict of name -> function, or None for defaults
            num_samples: Number of sample points
            min_pass_rate: Minimum fraction where rank increases
            seed: Random seed
            
        Returns:
            IndependenceResult
        """
        if known_integrals is None:
            known_integrals = self._known_integrals
        
        np.random.seed(seed)
        
        known_funcs = list(known_integrals.values())
        k = len(known_funcs)  # Number of known integrals
        
        passes = 0
        failed_states = []
        sample_sv = None
        
        for i in range(num_samples):
            state = self._generate_valid_state()
            
            # Compute gradients
            base_grads = [self._compute_gradient(f, state) 
                         for f in known_funcs]
            candidate_grad = self._compute_gradient(candidate, state)
            
            # Build Jacobian matrices
            J_base = np.array(base_grads)
            J_extended = np.vstack([J_base, candidate_grad])
            
            # Compute ranks
            base_rank = compute_numerical_rank(J_base, self.tolerance)
            extended_rank = compute_numerical_rank(J_extended, self.tolerance)
            
            # Store first sample's singular values for diagnostics
            if i == 0:
                _, sample_sv, _ = np.linalg.svd(J_extended)
            
            # Check if rank increased
            if extended_rank > base_rank:
                passes += 1
            else:
                if len(failed_states) < 10:  # Store up to 10 failures
                    failed_states.append(state.copy())
        
        pass_rate = passes / num_samples
        
        return IndependenceResult(
            passed=pass_rate >= min_pass_rate,
            base_rank=k,  # Expected base rank
            extended_rank=k + 1 if pass_rate >= min_pass_rate else k,
            rank_increased=pass_rate >= min_pass_rate,
            pass_rate=pass_rate,
            num_samples=num_samples,
            tolerance=self.tolerance,
            singular_values_sample=sample_sv,
            failed_states=failed_states
        )
    
    def _compute_gradient(
        self, func: Callable, state: np.ndarray, 
        epsilon: float = 1e-7
    ) -> np.ndarray:
        """Compute gradient via central differences."""
        n = len(state)
        grad = np.zeros(n)
        
        for i in range(n):
            state_plus = state.copy()
            state_minus = state.copy()
            state_plus[i] += epsilon
            state_minus[i] -= epsilon
            
            grad[i] = (func(state_plus, self.mu) - 
                      func(state_minus, self.mu)) / (2*epsilon)
        
        return grad
    
    def _generate_valid_state(self) -> np.ndarray:
        """Generate physically valid state avoiding singularities."""
        while True:
            x = np.random.uniform(0.5, 1.5)
            y = np.random.uniform(-0.5, 0.5)
            z = np.random.uniform(-0.1, 0.1)
            vx = np.random.uniform(-0.5, 0.5)
            vy = np.random.uniform(0.0, 1.0)
            vz = np.random.uniform(-0.2, 0.2)
            
            state = np.array([x, y, z, vx, vy, vz])
            
            r1 = np.sqrt((x + self.mu)**2 + y**2 + z**2)
            r2 = np.sqrt((x - 1 + self.mu)**2 + y**2 + z**2)
            
            if r1 > 0.1 and r2 > 0.1:
                return state
```

## Handling Edge Cases

### Degenerate States

Some states may have lower base rank (e.g., at equilibrium points):

```python
def test_independence_robust(
    tester: IndependenceTester,
    candidate: Callable,
    num_samples: int = 10000,
    min_base_rank: int = 3
) -> IndependenceResult:
    """
    Test independence, filtering out degenerate states.
    
    Degenerate states are those where the base rank is lower than expected.
    """
    known_funcs = list(tester._known_integrals.values())
    
    valid_samples = 0
    passes = 0
    failed_states = []
    
    attempts = 0
    max_attempts = num_samples * 10
    
    while valid_samples < num_samples and attempts < max_attempts:
        attempts += 1
        state = tester._generate_valid_state()
        
        # Compute base gradients
        base_grads = [tester._compute_gradient(f, state) 
                     for f in known_funcs]
        J_base = np.array(base_grads)
        
        # Check base rank
        base_rank = compute_numerical_rank(J_base, tester.tolerance)
        
        if base_rank < min_base_rank:
            continue  # Skip degenerate state
        
        valid_samples += 1
        
        # Compute candidate gradient
        candidate_grad = tester._compute_gradient(candidate, state)
        J_extended = np.vstack([J_base, candidate_grad])
        extended_rank = compute_numerical_rank(J_extended, tester.tolerance)
        
        if extended_rank > base_rank:
            passes += 1
        else:
            if len(failed_states) < 10:
                failed_states.append(state.copy())
    
    pass_rate = passes / valid_samples if valid_samples > 0 else 0.0
    
    return IndependenceResult(
        passed=pass_rate >= 0.99,
        base_rank=min_base_rank,
        extended_rank=min_base_rank + 1 if pass_rate >= 0.99 else min_base_rank,
        rank_increased=pass_rate >= 0.99,
        pass_rate=pass_rate,
        num_samples=valid_samples,
        tolerance=tester.tolerance,
        singular_values_sample=None,
        failed_states=failed_states
    )
```

### Near-Singular Gradients

Handle cases where gradient computation may fail:

```python
def safe_compute_gradient(
    func: Callable, state: np.ndarray, mu: float,
    epsilon: float = 1e-7
) -> Optional[np.ndarray]:
    """
    Compute gradient with error handling.
    
    Returns None if gradient cannot be reliably computed.
    """
    n = len(state)
    grad = np.zeros(n)
    
    try:
        f0 = func(state, mu)
        if not np.isfinite(f0):
            return None
        
        for i in range(n):
            state_plus = state.copy()
            state_minus = state.copy()
            state_plus[i] += epsilon
            state_minus[i] -= epsilon
            
            f_plus = func(state_plus, mu)
            f_minus = func(state_minus, mu)
            
            if not (np.isfinite(f_plus) and np.isfinite(f_minus)):
                return None
            
            grad[i] = (f_plus - f_minus) / (2*epsilon)
        
        if not np.all(np.isfinite(grad)):
            return None
        
        return grad
        
    except Exception:
        return None
```

## Symbolic Independence Test

When expressions are available:

```python
import sympy as sp

def test_independence_symbolic(
    integrals: List[sp.Expr],
    variables: List[sp.Symbol]
) -> dict:
    """
    Test functional independence symbolically.
    
    Returns dict with jacobian, rank, is_independent
    """
    n = len(variables)
    k = len(integrals)
    
    # Build Jacobian matrix
    J = sp.Matrix(k, n, lambda i, j: sp.diff(integrals[i], variables[j]))
    
    # Compute rank symbolically
    # This finds the maximum rank over generic points
    rank = J.rank()
    
    # Check if full rank
    is_independent = (rank == k)
    
    # Find any dependencies
    dependencies = []
    if not is_independent:
        # Null space reveals dependencies
        null = J.nullspace()
        if null:
            dependencies = null
    
    return {
        'jacobian': J,
        'rank': rank,
        'expected_rank': k,
        'is_independent': is_independent,
        'dependencies': dependencies
    }
```

### Example: Testing Jacobi Constant Independence

```python
x, y, z = sp.symbols('x y z', real=True)
vx, vy, vz = sp.symbols('vx vy vz', real=True)
mu = sp.Symbol('mu', positive=True)

variables = [x, y, z, vx, vy, vz]

r1 = sp.sqrt((x + mu)**2 + y**2 + z**2)
r2 = sp.sqrt((x - 1 + mu)**2 + y**2 + z**2)

# Known integrals
E = (vx**2 + vy**2 + vz**2)/2 - (1-mu)/r1 - mu/r2
L = x*vy - y*vx
Omega = (x**2 + y**2)/2 + (1-mu)/r1 + mu/r2
C = 2*Omega - (vx**2 + vy**2 + vz**2)

# Test independence
result = test_independence_symbolic([E, L, C], variables)
print(f"Rank: {result['rank']}")
print(f"Independent: {result['is_independent']}")

# Note: C = 2Ω - v² is NOT independent of E
# In fact, E + ½(x² + y²) and C are related
```

## Finding Independent Sets

Given multiple candidates, find maximal independent subset:

```python
def find_independent_set(
    candidates: List[Dict[str, Callable]],
    mu: float,
    num_samples: int = 1000,
    tolerance: float = 1e-8
) -> List[str]:
    """
    Find maximal independent subset of candidates.
    
    Uses greedy algorithm: add candidates that increase rank.
    """
    selected = []
    selected_funcs = []
    
    # Start with known integrals
    tester = IndependenceTester(mu=mu, tolerance=tolerance)
    base_funcs = list(tester._known_integrals.values())
    
    # Generate test states
    states = [tester._generate_valid_state() for _ in range(num_samples)]
    
    # Compute base rank
    base_grads = []
    for state in states[:100]:  # Use subset for efficiency
        grads = [tester._compute_gradient(f, state) for f in base_funcs]
        J = np.array(grads)
        rank = compute_numerical_rank(J, tolerance)
        base_grads.append(rank)
    
    current_rank = int(np.median(base_grads))
    current_funcs = base_funcs.copy()
    
    # Greedily add candidates
    for cand in candidates:
        name = cand['name']
        func = cand['func']
        
        # Test if adding this candidate increases rank
        rank_increases = 0
        
        for state in states:
            grads = [tester._compute_gradient(f, state) 
                    for f in current_funcs + [func]]
            J = np.array(grads)
            new_rank = compute_numerical_rank(J, tolerance)
            
            if new_rank > current_rank:
                rank_increases += 1
        
        pass_rate = rank_increases / len(states)
        
        if pass_rate > 0.99:
            selected.append(name)
            selected_funcs.append(func)
            current_funcs.append(func)
            current_rank += 1
            print(f"Added {name}, new rank = {current_rank}")
    
    return selected
```

## Diagnostics and Visualization

```python
import matplotlib.pyplot as plt

def plot_singular_value_spectrum(result: IndependenceResult, save_path: str = None):
    """
    Plot singular value spectrum for rank analysis.
    """
    sv = result.singular_values_sample
    if sv is None:
        print("No singular values available")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Linear scale
    ax1.bar(range(len(sv)), sv, color='steelblue')
    ax1.set_xlabel('Index')
    ax1.set_ylabel('Singular Value')
    ax1.set_title('Singular Value Spectrum (Linear)')
    ax1.axhline(y=result.tolerance * sv[0], color='r', linestyle='--', 
                label=f'Tolerance = {result.tolerance:.0e} × σ₁')
    ax1.legend()
    
    # Log scale
    ax2.semilogy(range(len(sv)), sv, 'o-', color='steelblue')
    ax2.axhline(y=result.tolerance * sv[0], color='r', linestyle='--',
                label=f'Tolerance')
    ax2.set_xlabel('Index')
    ax2.set_ylabel('Singular Value (log scale)')
    ax2.set_title('Singular Value Spectrum (Log)')
    ax2.legend()
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def diagnose_independence_failure(
    result: IndependenceResult,
    candidate: Callable,
    tester: IndependenceTester
) -> str:
    """
    Diagnose why independence test failed.
    """
    if result.passed:
        return "Test passed - no diagnosis needed"
    
    lines = ["Independence Test Failure Diagnosis:"]
    lines.append(f"  Pass rate: {result.pass_rate:.1%} (needed 99%)")
    
    if result.failed_states:
        lines.append(f"\n  Analyzing {len(result.failed_states)} failed states:")
        
        for i, state in enumerate(result.failed_states[:3]):
            # Compute gradients at failed state
            known_funcs = list(tester._known_integrals.values())
            base_grads = [tester._compute_gradient(f, state) for f in known_funcs]
            cand_grad = tester._compute_gradient(candidate, state)
            
            J_base = np.array(base_grads)
            J_ext = np.vstack([J_base, cand_grad])
            
            _, sv_base, _ = np.linalg.svd(J_base)
            _, sv_ext, _ = np.linalg.svd(J_ext)
            
            lines.append(f"\n  State {i+1}:")
            lines.append(f"    Base singular values: {sv_base}")
            lines.append(f"    Extended singular values: {sv_ext}")
            
            # Check if candidate gradient is nearly in span of base
            # Project candidate onto base span
            U, S, Vt = np.linalg.svd(J_base.T, full_matrices=False)
            projection = U @ U.T @ cand_grad
            residual = np.linalg.norm(cand_grad - projection)
            
            lines.append(f"    Residual from base span: {residual:.2e}")
            
            if residual < 1e-6:
                lines.append("    → Candidate gradient lies in span of known gradients")
                lines.append("    → Candidate is likely a function of known integrals")
    
    return "\n".join(lines)
```

## References

- Golub, G.H. & Van Loan, C.F. (2013). *Matrix Computations*, Ch. 2
- Arnold, V.I. (1989). *Mathematical Methods of Classical Mechanics*, Ch. 10
- Olver, P.J. (1993). *Applications of Lie Groups to Differential Equations*, Ch. 5
- Higham, N.J. (2002). *Accuracy and Stability of Numerical Algorithms*, Ch. 5
