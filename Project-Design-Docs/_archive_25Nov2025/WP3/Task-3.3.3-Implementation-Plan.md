# Task 3.3.3: Candidate Ranking and Consolidation Implementation
## Detailed Implementation Plan

**Duration**: 3 days
**Prerequisites**: Tasks 3.3.1, 3.3.2, and outputs from WP 3.1 & WP 3.2
**Objective**: Consolidate all candidate integrals from geometric, ML, and symbolic methods into a ranked list ready for rigorous validation in WP4

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Ranking Methodology](#ranking-methodology)
5. [Validation Strategy](#validation-strategy)
6. [Integration Points](#integration-points)
7. [Testing Plan](#testing-plan)
8. [Deliverables](#deliverables)

---

## Overview

### Purpose

Task 3.3.3 is the **culmination of WP3**: it brings together all candidate conserved quantities discovered through three independent methodologies and produces a definitive ranked list for rigorous analytical validation in WP4.

**Input Sources**:
1. **WP 3.1**: Killing fields → geometric integrals (analytical or numerical)
2. **WP 3.2**: Hamiltonian Neural Networks → learned conserved quantities (numerical)
3. **WP 3.3.1**: Symbolic regression → analytical expressions
4. **WP 3.3.2**: Physics-informed candidates (from basis function analysis)

**Output**: Top 5-10 candidate integrals with:
- Symbolic expressions (SymPy format)
- Conservation error quantification
- Functional independence verification
- Complexity metrics
- Physical interpretation (if possible)

### Key Challenges

1. **Heterogeneous representations**: Candidates come in different forms (SymPy, numerical functions, neural networks)
2. **Duplicate detection**: Same integral may be discovered multiple times in different forms
3. **Trivial filtering**: Must exclude known integrals (E, L, p_θ) and their trivial combinations
4. **Multi-objective ranking**: Balance conservation accuracy, simplicity, and novelty

---

## Architecture

### Module Structure

```
src/python/symbolic/
├── candidate_ranking.py            # Main API (this task)
├── deduplication.py                # Detect equivalent expressions
├── triviality_filter.py            # Remove known/trivial integrals
├── independence_test.py            # Jacobian rank, Poisson brackets
├── complexity_metrics.py           # Quantify expression complexity
├── visualization.py                # Phase space plots, level sets
└── report_generation.py            # Final report and export
```

### Consolidation Pipeline

```
Inputs:
  ├─ WP 3.1: Geometric candidates (N₁ ≈ 0-10)
  ├─ WP 3.2: ML candidates (N₂ ≈ 0-5)
  └─ WP 3.3.1: Symbolic regression (N₃ ≈ N₁ + N₂)
      ↓
Unification: Convert all to SymPy expressions
      ↓
Filtering:
  ├─ Remove duplicates (N → N - d)
  ├─ Remove trivial (E, L, p_θ, constants)
  └─ Remove dependent combinations (E+L, 2E, etc.)
      ↓
Validation:
  ├─ Conservation test (numerical trajectories)
  ├─ Independence test (Jacobian rank)
  └─ Involution test (Poisson brackets)
      ↓
Ranking:
  ├─ Score = f(conservation, complexity, independence)
  └─ Sort by score (ascending = better)
      ↓
Top 5-10 candidates → WP4
```

---

## Implementation Details

### Part A: Candidate Representation (0.5 days)

**File**: `src/python/symbolic/candidate_ranking.py`

```python
"""
Core data structures and ranking logic for candidate integrals.
"""

import numpy as np
import sympy as sp
from typing import Callable, List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CandidateSource(Enum):
    """Source of candidate integral discovery."""
    KILLING_FIELD = "killing_field"      # WP 3.1 geometric
    ML_DISCOVERY = "ml_discovery"         # WP 3.2 neural network
    SYMBOLIC_REGRESSION = "symbolic_regression"  # WP 3.3.1
    PHYSICS_BASIS = "physics_basis"       # WP 3.3.2 basis analysis
    MANUAL = "manual"                     # User-specified


@dataclass
class CandidateIntegral:
    """
    Represents a candidate conserved quantity.

    Attributes:
        expression: Symbolic SymPy expression
        source: Discovery method
        conservation_error: Numerical conservation test result
        complexity: Expression complexity (operation count)
        independent: Functionally independent of known integrals
        in_involution: Poisson commutes with other integrals
        metadata: Additional information
    """
    expression: sp.Expr
    source: CandidateSource
    conservation_error: float
    complexity: int
    independent: bool = False
    in_involution: bool = False

    # Detailed metrics
    jacobian_rank_increase: int = 0  # How many dimensions of independence added
    poisson_bracket_residuals: Dict[str, float] = field(default_factory=dict)

    # Metadata
    metadata: Dict = field(default_factory=dict)
    discovery_method_details: str = ""

    # Scoring (computed later)
    score: float = np.inf

    def __repr__(self) -> str:
        return f"CandidateIntegral({self.expression}, score={self.score:.2e})"

    def to_dict(self) -> dict:
        """Export to dictionary for JSON serialization."""
        return {
            'expression': str(self.expression),
            'expression_latex': sp.latex(self.expression),
            'source': self.source.value,
            'conservation_error': float(self.conservation_error),
            'complexity': int(self.complexity),
            'independent': bool(self.independent),
            'in_involution': bool(self.in_involution),
            'score': float(self.score),
            'metadata': self.metadata
        }


@dataclass
class ConsolidatedResults:
    """
    Complete results from candidate consolidation.

    Attributes:
        all_candidates: All discovered candidates (before filtering)
        filtered_candidates: After triviality and duplicate removal
        ranked_candidates: Final ranked list
        known_integrals: Known conserved quantities (E, L, etc.)
        statistics: Summary statistics
    """
    all_candidates: List[CandidateIntegral]
    filtered_candidates: List[CandidateIntegral]
    ranked_candidates: List[CandidateIntegral]

    known_integrals: Dict[str, sp.Expr]

    # Statistics
    n_total: int = 0
    n_duplicates_removed: int = 0
    n_trivial_removed: int = 0
    n_dependent_removed: int = 0
    n_final: int = 0

    # Validation summary
    n_conserved: int = 0  # Conservation error < threshold
    n_independent: int = 0  # Functionally independent
    n_involution: int = 0  # Mutual involution

    def summary_table(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 70,
            "CANDIDATE INTEGRAL CONSOLIDATION SUMMARY",
            "=" * 70,
            f"Total candidates discovered: {self.n_total}",
            f"  - Duplicates removed: {self.n_duplicates_removed}",
            f"  - Trivial removed: {self.n_trivial_removed}",
            f"  - Dependent removed: {self.n_dependent_removed}",
            f"Final candidate count: {self.n_final}",
            "",
            "Validation Results:",
            f"  - Conserved (error < 1e-6): {self.n_conserved}/{self.n_final}",
            f"  - Independent: {self.n_independent}/{self.n_final}",
            f"  - In involution: {self.n_involution}/{self.n_final}",
            "=" * 70,
        ]

        if self.ranked_candidates:
            lines.append("")
            lines.append("TOP 5 CANDIDATES:")
            lines.append("-" * 70)
            for i, cand in enumerate(self.ranked_candidates[:5], 1):
                lines.append(f"{i}. {cand.expression}")
                lines.append(f"   Source: {cand.source.value}")
                lines.append(f"   Conservation error: {cand.conservation_error:.2e}")
                lines.append(f"   Complexity: {cand.complexity}")
                lines.append(f"   Score: {cand.score:.2e}")
                lines.append("")

        return "\n".join(lines)


def consolidate_candidates(
    killing_field_candidates: List[CandidateIntegral] = None,
    ml_candidates: List[CandidateIntegral] = None,
    symbolic_candidates: List[CandidateIntegral] = None,
    physics_candidates: List[CandidateIntegral] = None,
    known_integrals: Dict[str, sp.Expr] = None,
    masses: np.ndarray = np.array([1.0, 1.0, 1.0]),
    conservation_threshold: float = 1e-6,
    ranking_weights: Dict[str, float] = None,
    verbose: bool = False
) -> ConsolidatedResults:
    """
    Main consolidation pipeline.

    Args:
        killing_field_candidates: From WP 3.1
        ml_candidates: From WP 3.2
        symbolic_candidates: From WP 3.3.1
        physics_candidates: From WP 3.3.2
        known_integrals: Dictionary of known conserved quantities
        masses: Body masses
        conservation_threshold: Accept if |dI/dt| < this
        ranking_weights: Scoring function weights
        verbose: Print progress

    Returns:
        ConsolidatedResults with ranked candidates
    """
    # Default arguments
    if killing_field_candidates is None:
        killing_field_candidates = []
    if ml_candidates is None:
        ml_candidates = []
    if symbolic_candidates is None:
        symbolic_candidates = []
    if physics_candidates is None:
        physics_candidates = []

    if known_integrals is None:
        known_integrals = default_known_integrals()

    if ranking_weights is None:
        ranking_weights = {
            'conservation': 10.0,
            'complexity': 1.0,
            'independence': 100.0,
            'involution': 50.0
        }

    # Stage 1: Collect all candidates
    if verbose:
        print("=" * 70)
        print("Stage 1: Collecting candidates from all sources")
        print("=" * 70)

    all_candidates = (
        killing_field_candidates +
        ml_candidates +
        symbolic_candidates +
        physics_candidates
    )
    n_total = len(all_candidates)

    if verbose:
        print(f"  Killing fields: {len(killing_field_candidates)}")
        print(f"  ML discoveries: {len(ml_candidates)}")
        print(f"  Symbolic regression: {len(symbolic_candidates)}")
        print(f"  Physics basis: {len(physics_candidates)}")
        print(f"  TOTAL: {n_total}")

    # Stage 2: Remove duplicates
    if verbose:
        print("\n" + "=" * 70)
        print("Stage 2: Duplicate removal")
        print("=" * 70)

    from .deduplication import remove_duplicates
    unique_candidates, n_duplicates = remove_duplicates(all_candidates, verbose=verbose)

    if verbose:
        print(f"  Removed {n_duplicates} duplicates")
        print(f"  Unique candidates: {len(unique_candidates)}")

    # Stage 3: Remove trivial integrals
    if verbose:
        print("\n" + "=" * 70)
        print("Stage 3: Triviality filtering")
        print("=" * 70)

    from .triviality_filter import filter_trivial
    nontrivial_candidates, n_trivial = filter_trivial(
        unique_candidates,
        known_integrals,
        verbose=verbose
    )

    if verbose:
        print(f"  Removed {n_trivial} trivial candidates")
        print(f"  Non-trivial candidates: {len(nontrivial_candidates)}")

    # Stage 4: Test functional independence
    if verbose:
        print("\n" + "=" * 70)
        print("Stage 4: Independence testing")
        print("=" * 70)

    from .independence_test import test_independence, remove_dependent
    for cand in nontrivial_candidates:
        cand.independent, cand.jacobian_rank_increase = test_independence(
            cand.expression,
            known_integrals,
            masses
        )

    # Remove linearly dependent candidates
    independent_candidates, n_dependent = remove_dependent(
        nontrivial_candidates,
        verbose=verbose
    )

    if verbose:
        n_indep = sum(1 for c in independent_candidates if c.independent)
        print(f"  Independent candidates: {n_indep}/{len(independent_candidates)}")

    # Stage 5: Test involution (Poisson brackets)
    if verbose:
        print("\n" + "=" * 70)
        print("Stage 5: Involution testing")
        print("=" * 70)

    from .independence_test import test_involution
    for i, cand in enumerate(independent_candidates):
        if verbose and i % 5 == 0:
            print(f"  Testing candidate {i+1}/{len(independent_candidates)}...")

        cand.in_involution, cand.poisson_bracket_residuals = test_involution(
            cand.expression,
            known_integrals,
            masses
        )

    # Stage 6: Compute scores and rank
    if verbose:
        print("\n" + "=" * 70)
        print("Stage 6: Scoring and ranking")
        print("=" * 70)

    from .complexity_metrics import compute_complexity
    for cand in independent_candidates:
        # Update complexity if not already set
        if cand.complexity == 0:
            cand.complexity = compute_complexity(cand.expression)

        # Compute score
        cand.score = compute_score(cand, ranking_weights, conservation_threshold)

    # Sort by score (lower is better)
    ranked_candidates = sorted(independent_candidates, key=lambda c: c.score)

    if verbose:
        print(f"  Ranked {len(ranked_candidates)} candidates")
        print("\nTop 3:")
        for i, cand in enumerate(ranked_candidates[:3], 1):
            print(f"  {i}. {cand.expression} (score={cand.score:.2e})")

    # Compile statistics
    n_conserved = sum(1 for c in ranked_candidates if c.conservation_error < conservation_threshold)
    n_independent = sum(1 for c in ranked_candidates if c.independent)
    n_involution = sum(1 for c in ranked_candidates if c.in_involution)

    return ConsolidatedResults(
        all_candidates=all_candidates,
        filtered_candidates=independent_candidates,
        ranked_candidates=ranked_candidates,
        known_integrals=known_integrals,
        n_total=n_total,
        n_duplicates_removed=n_duplicates,
        n_trivial_removed=n_trivial,
        n_dependent_removed=n_dependent,
        n_final=len(ranked_candidates),
        n_conserved=n_conserved,
        n_independent=n_independent,
        n_involution=n_involution
    )


def compute_score(
    candidate: CandidateIntegral,
    weights: Dict[str, float],
    conservation_threshold: float
) -> float:
    """
    Compute ranking score for candidate.

    Score = w_cons * penalty_cons(error) +
            w_comp * complexity +
            w_indep * penalty_indep(independent) +
            w_invol * penalty_invol(involution)

    Lower score is better.
    """
    # Conservation penalty (exponential growth for large errors)
    if candidate.conservation_error < conservation_threshold:
        penalty_conservation = -np.log10(candidate.conservation_error)  # Reward low error
    else:
        penalty_conservation = 1e6  # Very high penalty for non-conserved

    # Independence penalty (0 if independent, large if not)
    penalty_independence = 0.0 if candidate.independent else 1e6

    # Involution penalty (0 if in involution, moderate if not)
    penalty_involution = 0.0 if candidate.in_involution else 100.0

    # Complexity (direct penalty)
    complexity_penalty = candidate.complexity

    # Weighted sum
    score = (
        weights.get('conservation', 10.0) * penalty_conservation +
        weights.get('complexity', 1.0) * complexity_penalty +
        weights.get('independence', 100.0) * penalty_independence +
        weights.get('involution', 50.0) * penalty_involution
    )

    return score


def default_known_integrals() -> Dict[str, sp.Expr]:
    """Default known conserved quantities."""
    # Symbols
    E, Lx, Ly, Lz, p_theta = sp.symbols('E L_x L_y L_z p_theta', real=True)

    return {
        'E': E,
        'L_x': Lx,
        'L_y': Ly,
        'L_z': Lz,
        'L': sp.sqrt(Lx**2 + Ly**2 + Lz**2),
        'p_theta': p_theta
    }
```

---

### Part B: Deduplication (0.5 days)

**File**: `src/python/symbolic/deduplication.py`

```python
"""
Detect and remove duplicate candidate integrals.

Two expressions are considered duplicates if:
1. Symbolically equivalent (after simplification)
2. Numerically equivalent on test set (within tolerance)
3. One is a trivial transformation of the other (scaling, translation)
"""

import numpy as np
import sympy as sp
from typing import List, Tuple
from .candidate_ranking import CandidateIntegral


def remove_duplicates(
    candidates: List[CandidateIntegral],
    symbolic_tolerance: float = 1e-12,
    numerical_tolerance: float = 1e-8,
    verbose: bool = False
) -> Tuple[List[CandidateIntegral], int]:
    """
    Remove duplicate candidates.

    Returns:
        unique_candidates: List without duplicates
        n_duplicates: Number of duplicates removed
    """
    if not candidates:
        return [], 0

    unique = []
    n_duplicates = 0

    for cand in candidates:
        is_duplicate = False

        for existing in unique:
            if are_equivalent(
                cand.expression,
                existing.expression,
                symbolic_tolerance,
                numerical_tolerance
            ):
                is_duplicate = True

                if verbose:
                    print(f"Duplicate found: {cand.expression} ≈ {existing.expression}")

                # Keep the one from better source (prioritize geometric over ML)
                if cand.source.value < existing.source.value:
                    # Replace existing with new (better source)
                    unique.remove(existing)
                    unique.append(cand)

                break

        if not is_duplicate:
            unique.append(cand)
        else:
            n_duplicates += 1

    return unique, n_duplicates


def are_equivalent(
    expr1: sp.Expr,
    expr2: sp.Expr,
    symbolic_tol: float = 1e-12,
    numerical_tol: float = 1e-8
) -> bool:
    """
    Check if two expressions are equivalent.

    Uses both symbolic and numerical tests.
    """
    # Test 1: Symbolic equivalence
    diff = sp.simplify(expr1 - expr2)
    if diff == 0:
        return True

    # Test 2: Symbolic equivalence up to constant
    symbols_list = list((expr1.free_symbols | expr2.free_symbols))
    if not symbols_list:
        # Both are constants
        return abs(float(expr1) - float(expr2)) < symbolic_tol

    # Test 3: Check if difference is constant
    try:
        diff_poly = sp.Poly(diff, *symbols_list)
        if diff_poly.is_constant:
            return True
    except:
        pass

    # Test 4: Numerical equivalence (sample test)
    try:
        # Generate random test points
        n_tests = 100
        test_points = {sym: np.random.randn(n_tests) for sym in symbols_list}

        # Evaluate both expressions
        f1 = sp.lambdify(symbols_list, expr1, 'numpy')
        f2 = sp.lambdify(symbols_list, expr2, 'numpy')

        vals1 = f1(*[test_points[s] for s in symbols_list])
        vals2 = f2(*[test_points[s] for s in symbols_list])

        # Check if difference is small or constant
        diff_vals = vals1 - vals2
        if np.std(diff_vals) < numerical_tol:
            # Difference is approximately constant
            return True

    except:
        pass  # Evaluation failed, not equivalent

    return False
```

---

### Part C: Triviality Filtering (0.5 days)

**File**: `src/python/symbolic/triviality_filter.py` (extends WP3.1 version)

```python
"""
Filter trivial candidate integrals (known conserved quantities and their combinations).
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Dict
from .candidate_ranking import CandidateIntegral


def filter_trivial(
    candidates: List[CandidateIntegral],
    known_integrals: Dict[str, sp.Expr],
    tolerance: float = 1e-8,
    verbose: bool = False
) -> Tuple[List[CandidateIntegral], int]:
    """
    Remove candidates that are trivial combinations of known integrals.

    A candidate is trivial if it's:
    1. Exactly a known integral (E, L, p_θ)
    2. A polynomial combination of known integrals (E^2, E*L, etc.)
    3. A constant
    4. A coordinate (if known)

    Returns:
        nontrivial_candidates: Filtered list
        n_trivial: Number removed
    """
    nontrivial = []
    n_trivial = 0

    for cand in candidates:
        if is_trivial(cand.expression, known_integrals, tolerance):
            n_trivial += 1
            if verbose:
                print(f"Trivial: {cand.expression}")
        else:
            nontrivial.append(cand)

    return nontrivial, n_trivial


def is_trivial(
    expr: sp.Expr,
    known_integrals: Dict[str, sp.Expr],
    tolerance: float = 1e-8
) -> bool:
    """
    Check if expression is a trivial combination of known integrals.
    """
    # Test 1: Is it exactly a known integral?
    for name, known_expr in known_integrals.items():
        if sp.simplify(expr - known_expr) == 0:
            return True

    # Test 2: Is it a constant?
    if expr.is_number:
        return True

    # Test 3: Is it a polynomial in known integrals?
    try:
        # Try to express as polynomial in known integrals
        known_symbols = [known_integrals[k] for k in known_integrals]
        poly = sp.Poly(expr, *known_symbols)

        # If successful, it's a polynomial combination → trivial
        if poly is not None:
            return True
    except:
        pass  # Not a polynomial in known integrals

    # Test 4: Linear regression against known integrals
    # (numerical test to catch cases symbolic methods miss)
    if is_linear_combination_numerical(expr, known_integrals, tolerance):
        return True

    return False


def is_linear_combination_numerical(
    expr: sp.Expr,
    known_integrals: Dict[str, sp.Expr],
    tolerance: float = 1e-8
) -> bool:
    """
    Numerical test: Is expr ≈ Σᵢ aᵢ Iᵢ for some constants aᵢ?
    """
    # Get all free symbols
    all_symbols = expr.free_symbols
    for known_expr in known_integrals.values():
        all_symbols |= known_expr.free_symbols

    if not all_symbols:
        return True  # All constants

    symbols_list = sorted(all_symbols, key=lambda s: s.name)

    # Generate random test points
    n_tests = 200
    test_points = np.random.randn(n_tests, len(symbols_list))

    # Evaluate candidate expression
    f_expr = sp.lambdify(symbols_list, expr, 'numpy')
    y = np.array([f_expr(*pt) for pt in test_points])

    # Evaluate known integrals (feature matrix)
    X = np.zeros((n_tests, len(known_integrals)))
    for i, known_expr in enumerate(known_integrals.values()):
        f_known = sp.lambdify(symbols_list, known_expr, 'numpy')
        X[:, i] = np.array([f_known(*pt) for pt in test_points])

    # Linear regression: y ≈ X @ coeffs
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        mse = residuals[0] / n_tests if len(residuals) > 0 else np.inf

        if mse < tolerance:
            return True  # Good linear fit → trivial combination
    except:
        pass

    return False
```

---

### Part D: Independence and Involution Testing (0.5 days)

**File**: `src/python/symbolic/independence_test.py`

```python
"""
Test functional independence and involution of candidate integrals.
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Dict
from .candidate_ranking import CandidateIntegral


def test_independence(
    candidate_expr: sp.Expr,
    known_integrals: Dict[str, sp.Expr],
    masses: np.ndarray,
    n_samples: int = 1000,
    rank_threshold: float = 0.9
) -> Tuple[bool, int]:
    """
    Test if candidate is functionally independent of known integrals.

    Uses numerical Jacobian rank test.

    Returns:
        is_independent: True if rank increases
        rank_increase: Dimension of new independence (0, 1, or more)
    """
    # Collect all integrals (known + candidate)
    all_integrals = list(known_integrals.values()) + [candidate_expr]

    # Get all symbols
    all_symbols = set()
    for integral in all_integrals:
        all_symbols |= integral.free_symbols

    symbols_list = sorted(all_symbols, key=lambda s: s.name)

    # Sample phase space
    samples = np.random.randn(n_samples, len(symbols_list))

    # Compute Jacobian matrix (n_samples, n_integrals)
    jacobian = np.zeros((n_samples, len(all_integrals)))

    for i, integral in enumerate(all_integrals):
        # Gradient
        grad = [sp.diff(integral, sym) for sym in symbols_list]
        grad_func = sp.lambdify(symbols_list, grad, 'numpy')

        for j, point in enumerate(samples):
            jacobian[j, i] = np.linalg.norm(grad_func(*point))

    # Compute rank
    rank_with_candidate = np.linalg.matrix_rank(jacobian)
    rank_without_candidate = np.linalg.matrix_rank(jacobian[:, :-1])

    rank_increase = rank_with_candidate - rank_without_candidate
    is_independent = rank_increase > 0

    return is_independent, rank_increase


def test_involution(
    candidate_expr: sp.Expr,
    known_integrals: Dict[str, sp.Expr],
    masses: np.ndarray,
    tolerance: float = 1e-6
) -> Tuple[bool, Dict[str, float]]:
    """
    Test if candidate Poisson-commutes with all known integrals.

    Computes {candidate, I_known} for all known I.

    Returns:
        in_involution: True if all brackets ≈ 0
        residuals: Dictionary of Poisson bracket residuals
    """
    residuals = {}

    for name, known_expr in known_integrals.items():
        bracket = poisson_bracket(candidate_expr, known_expr)
        bracket_simplified = sp.simplify(bracket)

        # Numerical evaluation to estimate magnitude
        residual = estimate_bracket_magnitude(bracket_simplified, tolerance)
        residuals[name] = residual

    # In involution if all residuals are small
    in_involution = all(r < tolerance for r in residuals.values())

    return in_involution, residuals


def poisson_bracket(f: sp.Expr, g: sp.Expr) -> sp.Expr:
    """
    Compute Poisson bracket {f, g} = Σᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ).

    Assumes symbols are named q0, q1, ..., p0, p1, ...
    """
    # Extract q and p symbols
    all_symbols = f.free_symbols | g.free_symbols
    q_symbols = sorted([s for s in all_symbols if s.name.startswith('q')], key=lambda x: x.name)
    p_symbols = sorted([s for s in all_symbols if s.name.startswith('p')], key=lambda x: x.name)

    bracket = sp.S(0)

    for q, p in zip(q_symbols, p_symbols):
        df_dq = sp.diff(f, q)
        df_dp = sp.diff(f, p)
        dg_dq = sp.diff(g, q)
        dg_dp = sp.diff(g, p)

        bracket += df_dq * dg_dp - df_dp * dg_dq

    return bracket


def estimate_bracket_magnitude(
    bracket_expr: sp.Expr,
    tolerance: float,
    n_samples: int = 100
) -> float:
    """
    Estimate numerical magnitude of Poisson bracket.

    Returns maximum absolute value over random samples.
    """
    if bracket_expr == 0:
        return 0.0

    symbols_list = sorted(bracket_expr.free_symbols, key=lambda s: s.name)

    if not symbols_list:
        # Constant bracket
        return abs(float(bracket_expr))

    # Sample and evaluate
    try:
        func = sp.lambdify(symbols_list, bracket_expr, 'numpy')
        samples = np.random.randn(n_samples, len(symbols_list))
        values = np.array([func(*s) for s in samples])
        return np.max(np.abs(values))
    except:
        return np.inf  # Evaluation failed → assume large


def remove_dependent(
    candidates: List[CandidateIntegral],
    verbose: bool = False
) -> Tuple[List[CandidateIntegral], int]:
    """
    Remove candidates that are linearly dependent on higher-ranked ones.

    Strategy: Keep first (best) candidates, remove later ones if dependent.
    """
    independent = []
    n_removed = 0

    for cand in candidates:
        # Check if dependent on any already-selected candidate
        is_dependent = False

        for existing in independent:
            if are_linearly_dependent(cand.expression, existing.expression):
                is_dependent = True
                n_removed += 1

                if verbose:
                    print(f"Dependent: {cand.expression} on {existing.expression}")
                break

        if not is_dependent:
            independent.append(cand)

    return independent, n_removed


def are_linearly_dependent(expr1: sp.Expr, expr2: sp.Expr) -> bool:
    """
    Check if expr1 ≈ c * expr2 for some constant c.
    """
    try:
        ratio = sp.simplify(expr1 / expr2)
        if ratio.is_number:
            return True
    except:
        pass

    return False
```

---

### Part E: Report Generation (1 day)

**File**: `src/python/symbolic/report_generation.py`

```python
"""
Generate final consolidated report for WP4 handoff.
"""

import numpy as np
import sympy as sp
from typing import List
import json
import matplotlib.pyplot as plt

from .candidate_ranking import CandidateIntegral, ConsolidatedResults


def generate_report(
    results: ConsolidatedResults,
    output_dir: str = "./reports",
    generate_plots: bool = True
) -> str:
    """
    Generate comprehensive report for WP4.

    Outputs:
        - JSON file with all data
        - LaTeX table for publication
        - Markdown summary
        - Visualization plots (optional)

    Returns:
        report_path: Path to generated report
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    # 1. JSON export (full data)
    json_path = os.path.join(output_dir, "candidates.json")
    export_json(results, json_path)

    # 2. LaTeX table
    latex_path = os.path.join(output_dir, "candidates_table.tex")
    generate_latex_table(results.ranked_candidates[:10], latex_path)

    # 3. Markdown report
    md_path = os.path.join(output_dir, "CANDIDATE_REPORT.md")
    generate_markdown_report(results, md_path)

    # 4. Visualizations
    if generate_plots:
        plot_path = os.path.join(output_dir, "visualizations")
        generate_visualizations(results, plot_path)

    return md_path


def export_json(results: ConsolidatedResults, output_path: str):
    """Export results to JSON format."""
    data = {
        'summary': {
            'n_total': results.n_total,
            'n_final': results.n_final,
            'n_conserved': results.n_conserved,
            'n_independent': results.n_independent,
            'n_involution': results.n_involution
        },
        'candidates': [cand.to_dict() for cand in results.ranked_candidates]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


def generate_latex_table(candidates: List[CandidateIntegral], output_path: str):
    """Generate LaTeX table for publication."""
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Top Candidate Conserved Quantities}",
        r"\begin{tabular}{clcccc}",
        r"\toprule",
        r"Rank & Expression & Source & $\epsilon_{\text{cons}}$ & Complexity & Independent \\",
        r"\midrule"
    ]

    for i, cand in enumerate(candidates, 1):
        expr_latex = sp.latex(cand.expression)
        if len(expr_latex) > 40:
            expr_latex = expr_latex[:37] + "..."

        source_abbrev = {
            'killing_field': 'KF',
            'ml_discovery': 'ML',
            'symbolic_regression': 'SR'
        }.get(cand.source.value, cand.source.value[:2].upper())

        indep_mark = r"\checkmark" if cand.independent else r"\times"

        lines.append(
            f"{i} & ${expr_latex}$ & {source_abbrev} & "
            f"{cand.conservation_error:.1e} & {cand.complexity} & {indep_mark} \\\\"
        )

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}"
    ])

    with open(output_path, 'w') as f:
        f.write("\n".join(lines))


def generate_markdown_report(results: ConsolidatedResults, output_path: str):
    """Generate markdown summary report."""
    with open(output_path, 'w') as f:
        f.write("# Candidate Conserved Quantities Report\n\n")
        f.write(f"**Generated**: {pd.Timestamp.now()}\n\n")
        f.write("---\n\n")

        # Summary
        f.write(results.summary_table())
        f.write("\n\n")

        # Detailed candidate list
        f.write("## Detailed Candidate List\n\n")

        for i, cand in enumerate(results.ranked_candidates, 1):
            f.write(f"### {i}. {cand.expression}\n\n")
            f.write(f"- **Source**: {cand.source.value}\n")
            f.write(f"- **Conservation error**: {cand.conservation_error:.2e}\n")
            f.write(f"- **Complexity**: {cand.complexity} operations\n")
            f.write(f"- **Independent**: {'Yes' if cand.independent else 'No'}\n")
            f.write(f"- **In involution**: {'Yes' if cand.in_involution else 'No'}\n")
            f.write(f"- **Score**: {cand.score:.2e}\n\n")

            if cand.poisson_bracket_residuals:
                f.write("**Poisson brackets**:\n")
                for name, res in cand.poisson_bracket_residuals.items():
                    f.write(f"  - {{I, {name}}} ≈ {res:.2e}\n")
                f.write("\n")

            f.write("---\n\n")


def generate_visualizations(results: ConsolidatedResults, output_dir: str):
    """Generate diagnostic plots."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Plot 1: Score distribution
    scores = [c.score for c in results.ranked_candidates if c.score < 1e6]
    plt.figure(figsize=(8, 5))
    plt.hist(scores, bins=20, edgecolor='black')
    plt.xlabel('Score')
    plt.ylabel('Count')
    plt.title('Candidate Score Distribution')
    plt.yscale('log')
    plt.savefig(os.path.join(output_dir, 'score_distribution.png'), dpi=150)
    plt.close()

    # Plot 2: Conservation error vs. complexity
    errors = [c.conservation_error for c in results.ranked_candidates]
    complexities = [c.complexity for c in results.ranked_candidates]

    plt.figure(figsize=(8, 6))
    plt.scatter(complexities, errors, alpha=0.6)
    plt.xlabel('Complexity')
    plt.ylabel('Conservation Error')
    plt.yscale('log')
    plt.title('Conservation Error vs. Complexity')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'error_vs_complexity.png'), dpi=150)
    plt.close()
```

---

## Success Criteria

### Minimum Success
- [ ] Consolidation pipeline runs without errors
- [ ] At least one candidate passes all filters
- [ ] Report generated

### Target Success
- [ ] 3-5 independent candidates in final list
- [ ] All candidates have conservation error < 1e-5
- [ ] Clear ranking with interpretable scores

### Stretch Success
- [ ] Publication-ready table and figures
- [ ] At least one candidate with error < 1e-10
- [ ] Physical interpretation for top candidate

---

## Deliverables

### Code Modules (7 files)

- [ ] `candidate_ranking.py` (~600 lines)
- [ ] `deduplication.py` (~250 lines)
- [ ] `triviality_filter.py` (~300 lines)
- [ ] `independence_test.py` (~400 lines)
- [ ] `complexity_metrics.py` (~150 lines)
- [ ] `visualization.py` (~300 lines)
- [ ] `report_generation.py` (~400 lines)

**Total**: ~2,400 lines

### Documentation

- [ ] Final candidate report (Markdown + LaTeX)
- [ ] JSON export for WP4 integration
- [ ] Visualization gallery

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Implementation Plan
**Estimated Implementation Time**: 3 days
