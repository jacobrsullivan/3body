# AMENDED Task 3.3.3: Enhanced Candidate Ranking for Complex Integrals
## Implementation Plan for Multi-Scale Validation and Interpretability Scoring

**Duration**: 3-4 days (extended from 3 days)
**Prerequisites**: Tasks 3.3.1, 3.3.2 (including AMENDED features)
**Objective**: Consolidate candidates from all discovery methods with enhanced validation for complex integrals and interpretability-aware scoring

**Amendment Date**: 2025-11-20
**Amendment Rationale**: The original Task 3.3.3 handles polynomial/rational integrals well. This amendment extends validation to handle complex integrals (elliptic, spinor-based) and adds interpretability scoring to prioritize physically meaningful expressions.

---

## Table of Contents

1. [Overview](#overview)
2. [Current Implementation Status](#current-implementation-status)
3. [Extended Architecture](#extended-architecture)
4. [Multi-Scale Conservation Testing](#multi-scale-conservation-testing)
5. [Function Type Classification](#function-type-classification)
6. [Enhanced Scoring System](#enhanced-scoring-system)
7. [Testing Plan](#testing-plan)
8. [Deliverables](#deliverables)

---

## Overview

### Current State

**IMPLEMENTED** (✅ Complete):
- Candidate consolidation from WP3.1 (Killing), WP3.2 (ML), WP3.3 (symbolic)
- Duplicate detection (symbolic + numerical equivalence)
- Triviality filtering (remove E, L, p_θ, linear combinations)
- Basic scoring (conservation error + complexity + independence)
- Report generation (Markdown/LaTeX)

**File**: `src/python/symbolic/candidate_ranking.py` (534 lines)
**File**: `src/python/symbolic/validation.py` (512 lines)

### Extended Goals

This amendment adds:

1. **Multi-Scale Conservation Testing**: Validate conservation at multiple time scales (critical for complex integrals with quasi-periodic motion)
2. **Function Type Classification**: Identify mathematical class of expressions (polynomial, elliptic, spinor, etc.)
3. **Interpretability Scoring**: Bonus for physically meaningful expressions
4. **Enhanced Ranking**: Function-type aware scoring with interpretability bonus

---

## Current Implementation Status

### Module: `candidate_ranking.py`

**Classes/Functions Implemented**:
| Component | Purpose | Status |
|-----------|---------|--------|
| `CandidateIntegral` | Metadata for candidates | ✅ COMPLETE |
| `CandidateSource` | KILLING_FIELD, ML, SYMBOLIC | ✅ COMPLETE |
| `compute_candidate_score()` | Basic scoring function | ✅ COMPLETE |
| `detect_duplicate_candidates()` | Find equivalent expressions | ✅ COMPLETE |
| `filter_trivial_candidates()` | Remove known integrals | ✅ COMPLETE |
| `consolidate_and_rank()` | Main API | ✅ COMPLETE |

**Current Scoring**:
```python
Score = w_cons * log10(error) + w_comp * complexity + w_indep * penalty
```

**Limitations**:
- ❌ No multi-scale conservation testing
- ❌ No function-type classification
- ❌ No interpretability bonus
- ❌ Same penalty for all complex expressions (elliptic = theta = uninterpretable)

---

### Module: `validation.py`

**Functions Implemented**:
| Function | Purpose | Status |
|----------|---------|--------|
| `validate_symbolic_numerical_agreement()` | Residual test | ✅ COMPLETE |
| `test_conservation_on_trajectory()` | Single trajectory | ✅ COMPLETE |
| `test_conservation_ensemble()` | Multiple trajectories | ✅ COMPLETE |
| `compute_poisson_bracket_symbolic()` | {I, H} | ✅ COMPLETE |
| `check_functional_independence()` | Jacobian rank | ✅ COMPLETE |

**Limitations**:
- ❌ No multi-scale testing
- ❌ No long-time integration tests
- ❌ No quasi-periodic structure detection

---

## Extended Architecture

### Extended Module Structure

```
src/python/symbolic/
├── validation.py                    # EXTEND (+200 lines)
│   ├── [EXISTING] validate_symbolic_numerical_agreement()
│   ├── [EXISTING] test_conservation_on_trajectory()
│   ├── [EXISTING] test_conservation_ensemble()
│   ├── [NEW] multi_scale_conservation_test()        # Test at multiple dt
│   ├── [NEW] long_time_conservation_test()          # 100+ orbital periods
│   ├── [NEW] detect_quasi_periodic_structure()      # Two incommensurate frequencies
│   └── [NEW] validate_complex_integral()            # Extended validation
│
├── candidate_ranking.py             # EXTEND (+100 lines)
│   ├── [EXISTING] compute_candidate_score()
│   ├── [NEW] identify_function_type()               # Classify expression
│   ├── [NEW] compute_interpretability_bonus()       # Physical meaning heuristics
│   ├── [NEW] compute_enhanced_score()               # Function-type aware scoring
│   └── [EXTEND] CandidateIntegral dataclass         # Add function_type field
│
└── interpretability.py              # NEW MODULE (~200 lines)
    ├── has_physical_interpretation()
    ├── matches_symmetry_pattern()
    ├── is_coordinate_independent()
    └── classify_by_geometric_meaning()
```

---

## Implementation Details

### Part A: Multi-Scale Conservation Testing (NEW - 1 day)

**Extend**: `src/python/symbolic/validation.py` (+200 lines)

#### A.1: Multi-Scale Test Rationale

**Problem**: Complex integrals (elliptic, quasi-periodic) may appear non-conserved at short time scales due to:
- Numerical precision limits
- Stiff dynamics requiring adaptive timesteps
- Aliasing of high-frequency components

**Solution**: Test conservation at multiple time scales and require consistency:
```python
Δt = [0.01, 0.1, 1.0, 10.0] seconds
For each Δt:
    Subsample trajectory at interval Δt
    Compute max|ΔI/I|
    Require: all scales show |ΔI/I| < threshold
```

#### A.2: Implementation

```python
"""
Extended validation module for complex integrals.
"""

from typing import Dict, List, Tuple
import numpy as np
import sympy as sp


def multi_scale_conservation_test(
    I_symbolic: sp.Expr,
    I_numerical: Callable,
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    dt_values: List[float] = [0.01, 0.1, 1.0, 10.0],
    threshold: float = 1e-6
) -> Tuple[bool, Dict[float, float]]:
    """
    Test conservation at multiple time scales.

    Args:
        I_symbolic: SymPy expression for integral
        I_numerical: Numerical evaluation function
        trajectory: Trajectory states (N_steps, state_dim)
        trajectory_times: Time values (N_steps,)
        dt_values: Time scales to test (in same units as trajectory_times)
        threshold: Conservation error threshold

    Returns:
        is_conserved_all_scales: True if conserved at all scales
        errors_by_scale: Dictionary mapping dt -> max|ΔI/I|

    Physical Interpretation:
        - dt=0.01: Short orbital time scale (instantaneous conservation)
        - dt=0.1: Few orbital periods (fast dynamics)
        - dt=1.0: Many orbital periods (secular drift)
        - dt=10.0: Long-time stability (chaotic divergence)
    """
    errors_by_scale = {}

    # Convert symbolic to numerical function
    I_func = lambdify_expression(I_symbolic)

    for dt in dt_values:
        # Subsample trajectory at this time scale
        time_step = trajectory_times[1] - trajectory_times[0]
        subsample_stride = max(1, int(dt / time_step))

        subsampled_trajectory = trajectory[::subsample_stride]
        subsampled_times = trajectory_times[::subsample_stride]

        if len(subsampled_trajectory) < 10:
            # Not enough points for meaningful test
            errors_by_scale[dt] = np.nan
            continue

        # Evaluate integral along subsampled trajectory
        I_values = np.array([I_func(state) for state in subsampled_trajectory])

        # Compute conservation error
        I_mean = np.mean(I_values)
        I_std = np.std(I_values)
        I_max = np.max(np.abs(I_values))
        I_min = np.min(np.abs(I_values))

        if abs(I_mean) > 1e-12:
            drift = (I_max - I_min) / abs(I_mean)
        else:
            # Integral near zero - use absolute drift
            drift = I_max - I_min

        errors_by_scale[dt] = drift

    # Check if conserved at all scales
    valid_errors = [e for e in errors_by_scale.values() if not np.isnan(e)]
    is_conserved_all_scales = all(e < threshold for e in valid_errors)

    return is_conserved_all_scales, errors_by_scale


def long_time_conservation_test(
    I_symbolic: sp.Expr,
    initial_state: np.ndarray,
    hamiltonian_func: Callable,
    masses: np.ndarray,
    t_max: float = 100.0,
    n_periods_estimate: int = 100,
    threshold: float = 1e-5
) -> Tuple[bool, float, np.ndarray]:
    """
    Test conservation over long time integration (100+ orbital periods).

    Args:
        I_symbolic: Integral expression
        initial_state: Initial phase space state
        hamiltonian_func: Hamiltonian function for dynamics
        masses: Body masses
        t_max: Maximum integration time
        n_periods_estimate: Estimated number of orbital periods in t_max
        threshold: Acceptable drift |ΔI/I|

    Returns:
        is_conserved: True if drift < threshold
        drift: Measured max|ΔI/I| over trajectory
        I_history: Integral values over time (for plotting)
    """
    from scipy.integrate import solve_ivp

    # Define Hamiltonian dynamics
    def hamiltonian_ode(t, state):
        n = len(state) // 2
        q, p = state[:n], state[n:]

        # Hamilton's equations: q̇ = ∂H/∂p, ṗ = -∂H/∂q
        # (Simplified - proper implementation needs symbolic differentiation)
        dq_dt = p  # Simplified
        dp_dt = -q  # Simplified (placeholder)

        return np.concatenate([dq_dt, dp_dt])

    # Integrate
    sol = solve_ivp(
        hamiltonian_ode,
        (0, t_max),
        initial_state,
        method='DOP853',  # High-order adaptive method
        dense_output=True,
        rtol=1e-10,
        atol=1e-12
    )

    # Evaluate integral along trajectory
    I_func = lambdify_expression(I_symbolic)
    I_history = np.array([I_func(sol.y[:, i]) for i in range(sol.y.shape[1])])

    # Compute drift
    I0 = I_history[0]
    if abs(I0) > 1e-12:
        drift = np.max(np.abs(I_history - I0)) / abs(I0)
    else:
        drift = np.max(np.abs(I_history - I0))

    is_conserved = drift < threshold

    return is_conserved, drift, I_history


def detect_quasi_periodic_structure(
    I_history: np.ndarray,
    times: np.ndarray
) -> Tuple[bool, List[float]]:
    """
    Detect if integral has quasi-periodic structure (two incommensurable frequencies).

    Uses Fourier analysis to identify dominant frequencies.

    Args:
        I_history: Integral values over time (N,)
        times: Time values (N,)

    Returns:
        is_quasi_periodic: True if two dominant incommensurable frequencies found
        frequencies: List of dominant frequencies

    Criterion:
        Quasi-periodic if:
        - Two dominant peaks in power spectrum
        - Frequencies are incommensurable (ω1/ω2 is irrational)
        - No higher harmonics
    """
    from scipy.fft import fft, fftfreq

    # Compute FFT
    N = len(I_history)
    dt = times[1] - times[0]
    yf = fft(I_history)
    xf = fftfreq(N, dt)[:N//2]
    power = 2.0/N * np.abs(yf[:N//2])

    # Find dominant frequencies
    threshold = 0.1 * np.max(power)  # 10% of max power
    peaks_idx = np.where(power > threshold)[0]
    peaks_freqs = xf[peaks_idx]
    peaks_power = power[peaks_idx]

    # Sort by power
    sorted_idx = np.argsort(peaks_power)[::-1]
    dominant_freqs = peaks_freqs[sorted_idx[:5]]  # Top 5

    # Check for two incommensurable frequencies
    if len(dominant_freqs) >= 2:
        f1, f2 = dominant_freqs[0], dominant_freqs[1]
        ratio = f1 / f2 if f2 != 0 else 0

        # Check if ratio is irrational (approximately)
        # Rational if ratio ≈ p/q for small integers p, q
        is_rational = False
        for p in range(1, 10):
            for q in range(1, 10):
                if abs(ratio - p/q) < 0.01:
                    is_rational = True
                    break

        is_quasi_periodic = not is_rational and len(dominant_freqs) >= 2
    else:
        is_quasi_periodic = False

    return is_quasi_periodic, dominant_freqs.tolist()
```

---

### Part B: Function Type Classification (NEW - 0.5 days)

**Extend**: `src/python/symbolic/candidate_ranking.py` (+50 lines)

```python
def identify_function_type(expr: sp.Expr) -> str:
    """
    Classify symbolic expression by mathematical function type.

    Types:
        - 'polynomial': Pure polynomial (no transcendentals)
        - 'rational': Ratio of polynomials
        - 'algebraic': Involves sqrt or nth roots
        - 'trigonometric': Contains sin, cos, tan
        - 'elliptic_jacobi': Contains sn, cn, dn (Jacobi elliptic)
        - 'elliptic_weierstrass': Contains ℘ (Weierstrass)
        - 'theta': Contains Jacobi theta functions
        - 'spinor_bilinear': Polynomial in spinor components
        - 'exponential': Contains exp, log
        - 'unknown': Cannot classify

    Args:
        expr: SymPy expression

    Returns:
        function_type: Classification string
    """
    # Check for spinor symbols
    symbols = {str(s) for s in expr.free_symbols}
    if any('u12' in s or 'u23' in s or 'u31' in s for s in symbols):
        # Check if polynomial in spinors
        if expr.is_polynomial():
            return 'spinor_bilinear'

    # Check for elliptic functions
    expr_str = str(expr)
    if 'sn(' in expr_str or 'cn(' in expr_str or 'dn(' in expr_str:
        return 'elliptic_jacobi'
    if 'wp(' in expr_str or '℘' in expr_str:
        return 'elliptic_weierstrass'
    if 'theta' in expr_str:
        return 'theta'

    # Check for algebraic (sqrt, roots)
    if expr.has(sp.sqrt) or expr.has(sp.root):
        return 'algebraic'

    # Check for trigonometric
    if expr.has(sp.sin) or expr.has(sp.cos) or expr.has(sp.tan):
        return 'trigonometric'

    # Check for exponential
    if expr.has(sp.exp) or expr.has(sp.log):
        return 'exponential'

    # Check for rational
    numer, denom = expr.as_numer_denom()
    if denom != 1:
        if numer.is_polynomial() and denom.is_polynomial():
            return 'rational'

    # Check for polynomial
    if expr.is_polynomial():
        return 'polynomial'

    return 'unknown'
```

---

### Part C: Interpretability Scoring (NEW - 0.5 days)

**New Module**: `src/python/symbolic/interpretability.py` (~200 lines)

```python
"""
Physical interpretability assessment for candidate integrals.
"""

import sympy as sp
from typing import Dict, List


def has_physical_interpretation(
    expr: sp.Expr,
    known_quantities: Dict[str, sp.Expr]
) -> Tuple[bool, str]:
    """
    Check if expression has obvious physical meaning.

    Interpretable patterns:
        - Energy-like: kinetic + potential
        - Angular momentum: r × p components
        - Runge-Lenz: p × L - r/|r| (Kepler symmetry)
        - Spinor norm: |u|^2 = r (KS geometry)
        - Action variables: ∫ p·dq

    Args:
        expr: Symbolic expression
        known_quantities: Dict of E, L, etc.

    Returns:
        is_interpretable: True if pattern recognized
        interpretation: Human-readable description
    """
    # Pattern 1: Pure energy or angular momentum
    if expr in known_quantities.values():
        return True, "Known conserved quantity"

    # Pattern 2: Power of conserved quantity
    for name, known_expr in known_quantities.items():
        if expr == known_expr**2:
            return True, f"Square of {name}"
        if expr == known_expr**3:
            return True, f"Cube of {name}"

    # Pattern 3: Product of conserved quantities
    if expr.is_Mul:
        terms = expr.as_ordered_factors()
        known_terms = [t for t in terms if t in known_quantities.values()]
        if len(known_terms) >= 2:
            return True, f"Product of conserved quantities"

    # Pattern 4: Geometric invariant
    if is_coordinate_independent(expr):
        return True, "Coordinate-independent geometric quantity"

    # Pattern 5: Symmetry generator
    if matches_symmetry_pattern(expr):
        return True, "Symmetry generator (Noether charge)"

    return False, "No obvious physical interpretation"


def is_coordinate_independent(expr: sp.Expr) -> bool:
    """
    Check if expression is manifestly coordinate-independent.

    Examples:
        - Distances: |r12|, |r23|
        - Dot products: r12 · v12
        - Cross products: |r12 × v12|
    """
    # Check if only involves geometric invariants
    symbols = {str(s) for s in expr.free_symbols}

    geometric_symbols = {'r12', 'r23', 'r31', 'L', 'E', 'I'}
    if symbols.issubset(geometric_symbols):
        return True

    return False


def matches_symmetry_pattern(expr: sp.Expr) -> bool:
    """
    Check if expression matches a known symmetry generator pattern.

    Examples:
        - Translation: p_x, p_y, p_z (linear momentum components)
        - Rotation: L_x, L_y, L_z (angular momentum components)
        - Galilean boost: t·p - m·r
    """
    # Check for linear momentum (pure p)
    if expr.is_Symbol and str(expr).startswith('p'):
        return True

    # Check for angular momentum form: q*p - p*q type
    if expr.is_Add:
        terms = expr.as_ordered_terms()
        if len(terms) == 2:
            t1, t2 = terms
            if t1.is_Mul and t2.is_Mul:
                # Check for qp - pq pattern
                return True  # Simplified check

    return False


def compute_interpretability_bonus(
    candidate: 'CandidateIntegral',
    known_quantities: Dict[str, sp.Expr]
) -> float:
    """
    Compute interpretability bonus for scoring.

    Bonus (negative = better score):
        - -100: Strong physical interpretation (Noether charge, etc.)
        - -50: Moderate interpretation (geometric invariant)
        - -20: Weak interpretation (product of conserved quantities)
        - 0: No interpretation

    Args:
        candidate: CandidateIntegral object
        known_quantities: Known conserved quantities

    Returns:
        bonus: Interpretability bonus (negative is good)
    """
    is_interp, interpretation = has_physical_interpretation(
        candidate.expression_symbolic,
        known_quantities
    )

    if not is_interp:
        return 0.0

    # Categorize interpretation strength
    if "symmetry" in interpretation.lower() or "noether" in interpretation.lower():
        return -100.0  # Strong interpretation
    elif "geometric" in interpretation.lower() or "coordinate-independent" in interpretation.lower():
        return -50.0  # Moderate interpretation
    elif "product" in interpretation.lower() or "power" in interpretation.lower():
        return -20.0  # Weak interpretation
    else:
        return -10.0  # Some interpretation
```

---

### Part D: Enhanced Scoring System (NEW - 0.5 days)

**Extend**: `src/python/symbolic/candidate_ranking.py` (+50 lines)

```python
def compute_enhanced_score(
    candidate: CandidateIntegral,
    weights: Dict[str, float],
    known_quantities: Dict[str, sp.Expr],
    conservation_threshold: float = 1e-6
) -> float:
    """
    Enhanced scoring function with function-type awareness and interpretability.

    Score = w_cons * penalty_cons(error) +
            w_comp * complexity +
            w_indep * penalty_indep(independent) +
            w_interp * interpretability_bonus +
            w_type * function_type_bonus

    Lower score is better.

    Args:
        candidate: CandidateIntegral object
        weights: Scoring weights
        known_quantities: Known conserved quantities (E, L, etc.)
        conservation_threshold: Threshold for conservation error

    Returns:
        score: Enhanced score (lower is better)
    """
    from .interpretability import compute_interpretability_bonus

    # Standard penalties
    if candidate.conservation_error < conservation_threshold:
        penalty_conservation = -np.log10(candidate.conservation_error + 1e-16)
    else:
        penalty_conservation = 1e6  # Very high penalty

    penalty_independence = 0.0 if candidate.is_independent else 1e6

    complexity_penalty = candidate.complexity

    # NEW: Interpretability bonus
    interpretability_bonus = compute_interpretability_bonus(candidate, known_quantities)

    # NEW: Function type bonus
    function_type_bonus = {
        'polynomial': 0,          # Baseline
        'rational': 10,           # Slightly more complex
        'algebraic': 20,          # sqrt is acceptable
        'spinor_bilinear': -30,   # Prefer spinor forms (KS-natural)
        'trigonometric': 30,      # Periodic okay if physical
        'elliptic_jacobi': 50,    # Complex but historically precedented
        'elliptic_weierstrass': 60,  # More complex
        'theta': 100,             # Very complex, last resort
        'exponential': 40,        # Scaling transformations
        'unknown': 200,           # Strongly penalize unclassified
    }.get(candidate.function_type, 0)

    # Weighted sum
    score = (
        weights.get('conservation', 10.0) * penalty_conservation +
        weights.get('complexity', 1.0) * complexity_penalty +
        weights.get('independence', 100.0) * penalty_independence +
        weights.get('interpretability', 1.0) * interpretability_bonus +
        weights.get('function_type', 1.0) * function_type_bonus
    )

    return score


# Extend CandidateIntegral dataclass
@dataclass
class CandidateIntegral:
    """Extended with function_type field."""
    # ... existing fields ...
    function_type: str = 'unknown'  # NEW FIELD
    interpretability_score: float = 0.0  # NEW FIELD
    multi_scale_errors: Dict[float, float] = field(default_factory=dict)  # NEW FIELD
```

---

## Testing Plan

### Unit Tests

```python
# tests/wp3/test_enhanced_validation.py

def test_multi_scale_conservation():
    """Test multi-scale conservation testing."""
    # Create trajectory with known conserved quantity
    # Test at multiple scales
    # Verify all scales show conservation

def test_function_type_classification():
    """Test classification of different expression types."""
    test_cases = [
        (sp.Symbol('x')**2 + sp.Symbol('y'), 'polynomial'),
        (sp.sin(sp.Symbol('x')), 'trigonometric'),
        (sp.Function('sn')(sp.Symbol('x'), sp.Symbol('k')), 'elliptic_jacobi'),
    ]
    for expr, expected_type in test_cases:
        assert identify_function_type(expr) == expected_type

def test_interpretability_scoring():
    """Test physical interpretability assessment."""
    # Test energy, angular momentum (should be interpretable)
    # Test random polynomial (should not be interpretable)
```

---

## Deliverables (UPDATED)

### Code Modules

- [ ] `src/python/symbolic/validation.py` (+200 lines, EXTEND)
- [ ] `src/python/symbolic/candidate_ranking.py` (+100 lines, EXTEND)
- [ ] `src/python/symbolic/interpretability.py` (~200 lines, NEW)
- **TOTAL NEW CODE**: ~500 lines

### Tests

- [ ] `tests/wp3/test_enhanced_validation.py` (~200 lines)
- [ ] `tests/wp3/test_interpretability.py` (~150 lines)
- **TOTAL TEST CODE**: ~350 lines

### Documentation

- [ ] Tutorial: "Multi-Scale Validation for Complex Integrals"
- [ ] Guide: "Interpreting Candidate Integrals"

---

## Success Criteria (REVISED)

### Minimum Success
- [ ] Multi-scale testing functional
- [ ] Function type classification works
- [ ] Enhanced scoring implemented

### Target Success
- [ ] Multi-scale test catches false positives (non-conserved integrals)
- [ ] Interpretability bonus correctly prioritizes physical expressions
- [ ] Enhanced ranking tested on 10+ candidates

### Stretch Success
- [ ] Quasi-periodic structure detection operational
- [ ] Interpretability heuristics validated by domain experts
- [ ] Publication: "Automated Physical Interpretation of Discovered Integrals"

---

**Document Version**: 2.0 (AMENDED)
**Created**: 2025-11-20
**Status**: AMENDMENT - Enhanced Ranking and Validation
**Estimated Implementation Time**: 3-4 days
**Key Additions**:
- Multi-scale conservation testing for complex integrals
- Function type classification (9 categories)
- Physical interpretability scoring
- Enhanced ranking with function-type bonuses
