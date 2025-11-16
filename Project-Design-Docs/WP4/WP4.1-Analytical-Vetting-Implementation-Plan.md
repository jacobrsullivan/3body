# WP 4.1: Analytical Vetting - Liouville Criteria
## Complete Implementation Plan

**Duration**: 8-10 days
**Prerequisites**: WP3 Complete (Candidate Integrals Available)
**Objective**: Verify that candidate conserved quantities satisfy the Liouville integrability criteria through symbolic and semi-numerical analysis

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Task 4.1.1: Poisson Bracket Computation](#task-411-poisson-bracket-computation)
4. [Task 4.1.2: Involution Testing](#task-412-involution-testing)
5. [Task 4.1.3: Functional Independence](#task-413-functional-independence)
6. [Integration Strategy](#integration-strategy)
7. [Validation Plan](#validation-plan)
8. [Deliverables](#deliverables)

---

## Overview

### Purpose

WP 4.1 implements the **first stage of the validation gauntlet**: testing whether candidates satisfy the classical **Liouville integrability criteria**. This is the most fundamental validation—if a candidate fails here, it cannot be a conserved quantity.

### The Three Liouville Criteria

For an $n$-DOF Hamiltonian system, **Liouville integrability** requires $n$ functionally independent integrals in **involution**:

1. **Conservation**: $\{I_k, H\} = 0$ for all $k$ (integrals are conserved)
2. **Involution**: $\{I_j, I_k\} = 0$ for all $j, k$ (integrals commute)
3. **Functional Independence**: $\text{rank}(\nabla I_1, \ldots, \nabla I_n) = n$ (integrals are independent)

**WP 4.1 Goal**: For each candidate $\widetilde{I}$ from WP3, verify all three criteria to machine precision or symbolically.

---

## Architecture

### Three-Task Pipeline

```
WP 4.1: Analytical Vetting (3 sequential tasks)
│
├── Task 4.1.1: Poisson Bracket Computation (3-4 days)
│   ├── Symbolic computation (SymPy/Mathematica)
│   ├── Numerical evaluation (if symbolic fails)
│   └── Conservation verification: {I, H} = 0?
│
├── Task 4.1.2: Involution Testing (2-3 days)
│   ├── Pairwise Poisson brackets: {I_i, I_j}
│   ├── Test against known integrals (E, L, p_θ)
│   └── Mutual involution of new candidates
│
└── Task 4.1.3: Functional Independence (3 days)
    ├── Jacobian matrix construction
    ├── Numerical rank computation (SVD)
    └── Statistical independence verification
```

---

## Task 4.1.1: Poisson Bracket Computation

**Duration**: 3-4 days
**Objective**: Compute $\{I, H\}$ symbolically or numerically and verify it equals zero

### Implementation Details

#### Part A: Symbolic Poisson Bracket Engine (2 days)

**File**: `src/python/validation/poisson_brackets.py`

```python
"""
Symbolic and numerical Poisson bracket computation.
"""

import numpy as np
import sympy as sp
from typing import Tuple, List, Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class PoissonBracketResult:
    """Result of Poisson bracket computation."""
    bracket_expr: sp.Expr  # Symbolic bracket (if computed)
    is_zero_symbolic: bool  # True if symbolically zero
    numerical_max: float  # Max numerical value
    numerical_samples: int  # Number of test points
    success: bool  # Conservation verified?
    method: str  # 'symbolic', 'numerical', or 'hybrid'


class PoissonBracketComputer:
    """
    Compute Poisson brackets {f, g} symbolically and numerically.

    Poisson bracket definition:
        {f, g} = Σᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ)
    """

    def __init__(
        self,
        coordinate_system: str = 'canonical',
        use_symbolic: bool = True,
        use_numerical: bool = True,
        numerical_samples: int = 10000,
        tolerance: float = 1e-12
    ):
        """
        Initialize Poisson bracket computer.

        Args:
            coordinate_system: 'canonical', 's1_bundle', or 'ks_spinor'
            use_symbolic: Attempt symbolic computation first
            use_numerical: Fall back to numerical if symbolic fails
            numerical_samples: Number of test points for numerical validation
            tolerance: Acceptance threshold for numerical brackets
        """
        self.coordinate_system = coordinate_system
        self.use_symbolic = use_symbolic
        self.use_numerical = use_numerical
        self.numerical_samples = numerical_samples
        self.tolerance = tolerance

    def compute_bracket(
        self,
        f: sp.Expr,
        g: sp.Expr,
        variables: Optional[List[sp.Symbol]] = None
    ) -> PoissonBracketResult:
        """
        Compute Poisson bracket {f, g}.

        Args:
            f: First function (SymPy expression)
            g: Second function (SymPy expression)
            variables: Phase space variables [q0, q1, ..., p0, p1, ...]
                      If None, inferred from expressions

        Returns:
            PoissonBracketResult with bracket and verification
        """
        # Extract variables if not provided
        if variables is None:
            variables = self._extract_canonical_variables(f, g)

        n_dof = len(variables) // 2
        q_vars = variables[:n_dof]
        p_vars = variables[n_dof:]

        # Attempt symbolic computation
        bracket_expr = None
        is_zero_symbolic = False

        if self.use_symbolic:
            try:
                bracket_expr = self._compute_symbolic_bracket(f, g, q_vars, p_vars)

                # Simplify
                bracket_simplified = sp.simplify(bracket_expr)

                # Check if symbolically zero
                if bracket_simplified == 0 or bracket_simplified == sp.S.Zero:
                    is_zero_symbolic = True
                    return PoissonBracketResult(
                        bracket_expr=bracket_simplified,
                        is_zero_symbolic=True,
                        numerical_max=0.0,
                        numerical_samples=0,
                        success=True,
                        method='symbolic'
                    )

                bracket_expr = bracket_simplified

            except Exception as e:
                print(f"Symbolic computation failed: {e}")
                bracket_expr = None

        # Numerical validation
        numerical_max = np.inf

        if self.use_numerical and bracket_expr is not None:
            try:
                numerical_max = self._evaluate_bracket_numerically(
                    bracket_expr,
                    variables,
                    n_samples=self.numerical_samples
                )

                success = numerical_max < self.tolerance

                return PoissonBracketResult(
                    bracket_expr=bracket_expr,
                    is_zero_symbolic=False,
                    numerical_max=numerical_max,
                    numerical_samples=self.numerical_samples,
                    success=success,
                    method='hybrid' if self.use_symbolic else 'numerical'
                )

            except Exception as e:
                print(f"Numerical evaluation failed: {e}")

        # Failed all methods
        return PoissonBracketResult(
            bracket_expr=bracket_expr if bracket_expr else sp.S.NaN,
            is_zero_symbolic=False,
            numerical_max=numerical_max,
            numerical_samples=self.numerical_samples if bracket_expr else 0,
            success=False,
            method='failed'
        )

    def _compute_symbolic_bracket(
        self,
        f: sp.Expr,
        g: sp.Expr,
        q_vars: List[sp.Symbol],
        p_vars: List[sp.Symbol]
    ) -> sp.Expr:
        """
        Symbolically compute {f, g} = Σᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ).
        """
        bracket = sp.S(0)

        for q, p in zip(q_vars, p_vars):
            df_dq = sp.diff(f, q)
            df_dp = sp.diff(f, p)
            dg_dq = sp.diff(g, q)
            dg_dp = sp.diff(g, p)

            bracket += df_dq * dg_dp - df_dp * dg_dq

        return bracket

    def _evaluate_bracket_numerically(
        self,
        bracket_expr: sp.Expr,
        variables: List[sp.Symbol],
        n_samples: int
    ) -> float:
        """
        Evaluate bracket on random phase space points.

        Returns maximum absolute value.
        """
        # Convert to NumPy function
        bracket_func = sp.lambdify(variables, bracket_expr, 'numpy')

        # Generate random samples
        samples = np.random.randn(n_samples, len(variables))

        # Evaluate
        values = []
        for sample in samples:
            try:
                val = float(bracket_func(*sample))
                values.append(abs(val))
            except:
                values.append(np.inf)  # Evaluation failed

        return np.max(values)

    def _extract_canonical_variables(
        self,
        f: sp.Expr,
        g: sp.Expr
    ) -> List[sp.Symbol]:
        """
        Extract canonical coordinates (q, p) from expressions.

        Assumes variables named q0, q1, ..., p0, p1, ...
        """
        all_symbols = f.free_symbols | g.free_symbols

        q_symbols = sorted([s for s in all_symbols if str(s).startswith('q')],
                          key=lambda x: str(x))
        p_symbols = sorted([s for s in all_symbols if str(s).startswith('p')],
                          key=lambda x: str(x))

        return q_symbols + p_symbols


def test_conservation(
    candidate_integral: sp.Expr,
    hamiltonian: sp.Expr,
    variables: Optional[List[sp.Symbol]] = None,
    tolerance: float = 1e-12,
    n_samples: int = 10000,
    verbose: bool = True
) -> PoissonBracketResult:
    """
    Test if candidate integral is conserved: {I, H} = 0.

    Convenience function for the most common use case.

    Example:
        >>> q0, q1, p0, p1 = sp.symbols('q0 q1 p0 p1')
        >>> H = (p0**2 + p1**2)/2 + q0**2 + q1**2  # Harmonic oscillator
        >>> I = (p0**2 + p1**2)/2 + q0**2 + q1**2  # Energy (same as H)
        >>> result = test_conservation(I, H)
        >>> assert result.success  # {H, H} = 0 always
    """
    computer = PoissonBracketComputer(
        numerical_samples=n_samples,
        tolerance=tolerance
    )

    if verbose:
        print("=" * 70)
        print("CONSERVATION TEST: {I, H} = 0?")
        print("=" * 70)
        print(f"Candidate: {candidate_integral}")
        print(f"Hamiltonian: {hamiltonian}")

    result = computer.compute_bracket(candidate_integral, hamiltonian, variables)

    if verbose:
        print(f"\nMethod: {result.method}")

        if result.is_zero_symbolic:
            print("✓ SYMBOLICALLY ZERO")
        elif result.success:
            print(f"✓ NUMERICALLY ZERO (max = {result.numerical_max:.2e} < {tolerance:.2e})")
        else:
            print(f"✗ NOT CONSERVED (max = {result.numerical_max:.2e} >= {tolerance:.2e})")

    return result
```

**Validation Tests**:

```python
# tests/validation/test_poisson_brackets.py

def test_poisson_bracket_harmonic_oscillator():
    """Test on harmonic oscillator: {E, H} = 0."""
    q, p = sp.symbols('q p', real=True)

    # Energy = Hamiltonian
    E = H = (p**2 + q**2) / 2

    result = test_conservation(E, H, variables=[q, p])

    assert result.is_zero_symbolic
    assert result.success


def test_poisson_bracket_angular_momentum():
    """Test 2D system: {L, H} = 0 if H is rotationally invariant."""
    q0, q1, p0, p1 = sp.symbols('q0 q1 p0 p1', real=True)

    # Rotationally invariant Hamiltonian
    H = (p0**2 + p1**2) / 2 + (q0**2 + q1**2)

    # Angular momentum
    L = q0*p1 - q1*p0

    result = test_conservation(L, H, variables=[q0, q1, p0, p1])

    assert result.is_zero_symbolic
    assert result.success


def test_poisson_bracket_non_conserved():
    """Test non-conserved quantity."""
    q, p = sp.symbols('q p')

    H = p**2 / 2 + q**2 / 2  # Harmonic oscillator
    I_bad = q  # Position is NOT conserved

    result = test_conservation(I_bad, H, variables=[q, p])

    assert not result.is_zero_symbolic
    assert not result.success  # Should fail
```

---

#### Part B: Batch Testing Pipeline (1 day)

**File**: `src/python/validation/conservation_validator.py`

```python
"""
Batch validation of conservation for multiple candidates.
"""

from typing import List, Dict
from .poisson_brackets import test_conservation, PoissonBracketResult
import sympy as sp


class ConservationValidator:
    """
    Validate conservation for a list of candidate integrals.
    """

    def __init__(
        self,
        hamiltonian: sp.Expr,
        known_integrals: Dict[str, sp.Expr],
        tolerance: float = 1e-12
    ):
        self.hamiltonian = hamiltonian
        self.known_integrals = known_integrals
        self.tolerance = tolerance

    def validate_candidates(
        self,
        candidates: List[sp.Expr],
        candidate_names: List[str] = None
    ) -> Dict[str, PoissonBracketResult]:
        """
        Test conservation for all candidates.

        Returns dictionary mapping candidate names to results.
        """
        if candidate_names is None:
            candidate_names = [f"Candidate_{i}" for i in range(len(candidates))]

        results = {}

        print("\n" + "=" * 70)
        print(f"BATCH CONSERVATION VALIDATION: {len(candidates)} candidates")
        print("=" * 70)

        for name, candidate in zip(candidate_names, candidates):
            print(f"\n[{name}]")

            result = test_conservation(
                candidate,
                self.hamiltonian,
                tolerance=self.tolerance,
                verbose=False
            )

            results[name] = result

            # Print summary
            if result.success:
                status = "✓ PASS"
            else:
                status = "✗ FAIL"

            print(f"  {status} - Method: {result.method}, Max: {result.numerical_max:.2e}")

        # Summary
        n_pass = sum(1 for r in results.values() if r.success)
        print("\n" + "=" * 70)
        print(f"SUMMARY: {n_pass}/{len(candidates)} candidates conserved")
        print("=" * 70)

        return results
```

---

## Task 4.1.2: Involution Testing

**Duration**: 2-3 days
**Objective**: Verify $\{I_i, I_j\} = 0$ for all pairs of integrals

### Implementation

**File**: `src/python/validation/involution_tester.py`

```python
"""
Test involution: {I_i, I_j} = 0 for all pairs.
"""

import numpy as np
import sympy as sp
from typing import List, Dict, Tuple
from itertools import combinations

from .poisson_brackets import PoissonBracketComputer, PoissonBracketResult


class InvolutionTester:
    """
    Test mutual involution of a set of integrals.
    """

    def __init__(
        self,
        tolerance: float = 1e-10,
        n_samples: int = 10000
    ):
        self.tolerance = tolerance
        self.n_samples = n_samples
        self.bracket_computer = PoissonBracketComputer(
            numerical_samples=n_samples,
            tolerance=tolerance
        )

    def test_involution(
        self,
        integrals: Dict[str, sp.Expr],
        verbose: bool = True
    ) -> Tuple[bool, Dict[Tuple[str, str], PoissonBracketResult]]:
        """
        Test pairwise involution for all integrals.

        Args:
            integrals: Dictionary mapping names to integral expressions
            verbose: Print progress

        Returns:
            all_in_involution: True if all brackets vanish
            bracket_results: Dictionary of pairwise bracket results
        """
        integral_names = list(integrals.keys())
        n_integrals = len(integral_names)

        if verbose:
            print("\n" + "=" * 70)
            print(f"INVOLUTION TEST: {n_integrals} integrals")
            print("=" * 70)
            print(f"Testing {n_integrals * (n_integrals - 1) // 2} pairs...")

        bracket_results = {}
        all_pass = True

        # Test all pairs (including self-brackets, which should be 0)
        for i, name_i in enumerate(integral_names):
            for j, name_j in enumerate(integral_names):
                if i >= j:  # Skip duplicates and already tested
                    continue

                I_i = integrals[name_i]
                I_j = integrals[name_j]

                if verbose:
                    print(f"\n  {{{name_i}, {name_j}}}")

                result = self.bracket_computer.compute_bracket(I_i, I_j)
                bracket_results[(name_i, name_j)] = result

                if not result.success:
                    all_pass = False
                    if verbose:
                        print(f"    ✗ FAIL - Max: {result.numerical_max:.2e}")
                else:
                    if verbose:
                        print(f"    ✓ PASS - Method: {result.method}")

        if verbose:
            n_pass = sum(1 for r in bracket_results.values() if r.success)
            print("\n" + "=" * 70)
            print(f"INVOLUTION SUMMARY: {n_pass}/{len(bracket_results)} pairs in involution")
            print("=" * 70)

        return all_pass, bracket_results
```

---

## Task 4.1.3: Functional Independence

**Duration**: 3 days
**Objective**: Verify integrals are functionally independent via Jacobian rank test

### Implementation

**File**: `src/python/validation/independence_tester.py`

```python
"""
Test functional independence via Jacobian rank.
"""

import numpy as np
import sympy as sp
from typing import List, Dict, Tuple
from scipy import linalg


class IndependenceTester:
    """
    Test functional independence of integrals via Jacobian rank.
    """

    def __init__(
        self,
        n_samples: int = 10000,
        rank_threshold: float = 0.999,
        tolerance: float = 1e-10
    ):
        self.n_samples = n_samples
        self.rank_threshold = rank_threshold
        self.tolerance = tolerance

    def test_independence(
        self,
        integrals: Dict[str, sp.Expr],
        variables: List[sp.Symbol],
        verbose: bool = True
    ) -> Tuple[bool, Dict]:
        """
        Test if integrals are functionally independent.

        Method: Compute Jacobian matrix and check rank numerically.

        Args:
            integrals: Dictionary of integral expressions
            variables: Phase space variables
            verbose: Print progress

        Returns:
            is_independent: True if rank = n_integrals on most samples
            statistics: Dictionary with rank distribution
        """
        n_integrals = len(integrals)
        n_vars = len(variables)

        if verbose:
            print("\n" + "=" * 70)
            print(f"FUNCTIONAL INDEPENDENCE TEST")
            print("=" * 70)
            print(f"  Integrals: {n_integrals}")
            print(f"  Variables: {n_vars}")
            print(f"  Samples: {self.n_samples}")

        # Compute gradients symbolically
        gradients = {}
        for name, integral in integrals.items():
            grad = [sp.diff(integral, var) for var in variables]
            gradients[name] = grad

        # Convert to NumPy functions
        grad_funcs = {}
        for name, grad in gradients.items():
            try:
                grad_funcs[name] = sp.lambdify(variables, grad, 'numpy')
            except Exception as e:
                print(f"Warning: Failed to lambdify gradient of {name}: {e}")
                return False, {}

        # Sample phase space and compute ranks
        samples = np.random.randn(self.n_samples, n_vars)
        ranks = []

        for i, sample in enumerate(samples):
            if verbose and i % 1000 == 0:
                print(f"  Progress: {i}/{self.n_samples}")

            # Build Jacobian matrix at this point
            jacobian = np.zeros((n_integrals, n_vars))

            try:
                for j, name in enumerate(integrals.keys()):
                    grad_val = grad_funcs[name](*sample)
                    jacobian[j, :] = grad_val

                # Compute rank
                rank = np.linalg.matrix_rank(jacobian, tol=self.tolerance)
                ranks.append(rank)

            except Exception as e:
                # Evaluation failed (e.g., singular point)
                ranks.append(0)

        ranks = np.array(ranks)

        # Statistics
        unique_ranks, counts = np.unique(ranks, return_counts=True)
        rank_distribution = dict(zip(unique_ranks, counts))

        fraction_full_rank = np.sum(ranks == n_integrals) / len(ranks)

        is_independent = fraction_full_rank >= self.rank_threshold

        if verbose:
            print(f"\n  Rank distribution:")
            for rank, count in rank_distribution.items():
                pct = 100 * count / len(ranks)
                print(f"    Rank {rank}: {count} ({pct:.1f}%)")

            print(f"\n  Full rank ({n_integrals}): {100*fraction_full_rank:.1f}%")

            if is_independent:
                print(f"  ✓ INDEPENDENT (>= {100*self.rank_threshold:.1f}% full rank)")
            else:
                print(f"  ✗ DEPENDENT (< {100*self.rank_threshold:.1f}% full rank)")

        statistics = {
            'rank_distribution': rank_distribution,
            'fraction_full_rank': fraction_full_rank,
            'mean_rank': np.mean(ranks),
            'std_rank': np.std(ranks)
        }

        return is_independent, statistics
```

---

## Integration Strategy

### Complete WP 4.1 Pipeline

**File**: `src/python/validation/analytical_vetting.py`

```python
"""
Complete analytical vetting pipeline (WP 4.1).
"""

from typing import List, Dict
import sympy as sp

from .conservation_validator import ConservationValidator
from .involution_tester import InvolutionTester
from .independence_tester import IndependenceTester


class AnalyticalVetter:
    """
    Complete WP 4.1 pipeline: Conservation, Involution, Independence.
    """

    def __init__(
        self,
        hamiltonian: sp.Expr,
        known_integrals: Dict[str, sp.Expr],
        variables: List[sp.Symbol],
        tolerance: float = 1e-12
    ):
        self.hamiltonian = hamiltonian
        self.known_integrals = known_integrals
        self.variables = variables
        self.tolerance = tolerance

    def vet_candidates(
        self,
        new_candidates: Dict[str, sp.Expr],
        verbose: bool = True
    ) -> Dict:
        """
        Run complete analytical vetting on new candidates.

        Returns dictionary with:
            - conservation_results
            - involution_results
            - independence_results
            - passed_candidates (list of names that passed all tests)
        """
        if verbose:
            print("\n" + "=" * 70)
            print("WP 4.1: ANALYTICAL VETTING PIPELINE")
            print("=" * 70)
            print(f"Candidates: {len(new_candidates)}")
            print(f"Known integrals: {len(self.known_integrals)}")

        # Stage 1: Conservation
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 1: CONSERVATION TEST")
            print("=" * 70)

        validator = ConservationValidator(
            self.hamiltonian,
            self.known_integrals,
            tolerance=self.tolerance
        )

        conservation_results = validator.validate_candidates(
            list(new_candidates.values()),
            list(new_candidates.keys())
        )

        # Filter: Only keep conserved candidates
        conserved_candidates = {
            name: expr for name, expr in new_candidates.items()
            if conservation_results[name].success
        }

        if verbose:
            print(f"\n{len(conserved_candidates)}/{len(new_candidates)} candidates conserved")

        if not conserved_candidates:
            if verbose:
                print("\n✗ NO CANDIDATES PASSED CONSERVATION TEST")
            return {
                'conservation_results': conservation_results,
                'involution_results': {},
                'independence_results': {},
                'passed_candidates': []
            }

        # Stage 2: Involution
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 2: INVOLUTION TEST")
            print("=" * 70)

        # Combine known + new integrals
        all_integrals = {**self.known_integrals, **conserved_candidates}

        involution_tester = InvolutionTester(
            tolerance=self.tolerance * 100  # Slightly relaxed
        )

        in_involution, involution_results = involution_tester.test_involution(
            all_integrals,
            verbose=verbose
        )

        # Stage 3: Independence
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 3: FUNCTIONAL INDEPENDENCE TEST")
            print("=" * 70)

        independence_tester = IndependenceTester()

        is_independent, independence_stats = independence_tester.test_independence(
            all_integrals,
            self.variables,
            verbose=verbose
        )

        # Final verdict
        passed_candidates = []

        if in_involution and is_independent:
            passed_candidates = list(conserved_candidates.keys())
            if verbose:
                print("\n" + "=" * 70)
                print(f"✓ SUCCESS: {len(passed_candidates)} candidates passed all tests!")
                print("=" * 70)
        else:
            if verbose:
                print("\n" + "=" * 70)
                print("✗ SOME TESTS FAILED")
                if not in_involution:
                    print("  - Involution test failed")
                if not is_independent:
                    print("  - Independence test failed")
                print("=" * 70)

        return {
            'conservation_results': conservation_results,
            'involution_results': involution_results,
            'independence_results': independence_stats,
            'passed_candidates': passed_candidates,
            'all_tests_passed': in_involution and is_independent
        }
```

---

## Validation Plan

### Test Suite

1. **Known Integrable Systems**:
   - Harmonic oscillator (1D, 2D, 3D)
   - Kepler problem (expect E, L, Runge-Lenz)
   - Free particle (expect E, all components of P, L)

2. **Known Non-Integrable Systems**:
   - Hénon-Heiles (expect only E)
   - Störmer problem (expect E, L_z)

3. **Edge Cases**:
   - Degenerate integrals (constant multiples)
   - Nearly conserved quantities (adiabatic invariants)

---

## Deliverables

### Code Modules (5 files)

- [ ] `poisson_brackets.py` (~600 lines)
- [ ] `conservation_validator.py` (~200 lines)
- [ ] `involution_tester.py` (~250 lines)
- [ ] `independence_tester.py` (~300 lines)
- [ ] `analytical_vetting.py` (~200 lines)

**Total**: ~1,550 lines

### Documentation

- [ ] API reference (Sphinx)
- [ ] Tutorial: "Verifying Liouville Integrability"
- [ ] Test coverage report

### Validation Reports

- [ ] Conservation test results for all candidates
- [ ] Involution matrix (pairwise brackets)
- [ ] Independence statistics (rank distributions)
- [ ] Final certification or rejection

---

## Success Criteria

### Minimum Success
- [ ] All three tests implemented and validated on known systems
- [ ] At least symbolic OR numerical verification working
- [ ] Test results documented for all candidates

### Target Success
- [ ] Symbolic computation works for simple candidates
- [ ] Numerical validation on 10^4 samples
- [ ] Clear pass/fail determination for each candidate

### Stretch Success
- [ ] Symbolic proofs for all candidates
- [ ] Automatic simplification of Poisson brackets
- [ ] Publication-quality certification documents

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Implementation Plan
**Estimated Implementation Time**: 8-10 days
