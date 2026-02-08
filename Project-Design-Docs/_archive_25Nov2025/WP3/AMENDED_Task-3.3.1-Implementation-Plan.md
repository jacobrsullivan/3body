# AMENDED Task 3.3.1: Extended Symbolic Regression Pipeline
## Implementation Plan for Complex Function Discovery

**Duration**: 5-6 days (extended from 4-5 days)
**Prerequisites**: Task 3.3.2 (Enriched Basis Functions)
**Objective**: Extend the symbolic regression pipeline to discover potentially non-standard analytical expressions including elliptic functions, algebraic forms, and spinor-based integrals

**Amendment Date**: 2025-11-20
**Amendment Rationale**: The current implementation supports polynomial and simple transcendental functions via SINDy/PySR. This amendment adds specialized search methods for elliptic functions and spinor-based expressions, motivated by integrable system theory and KS regularization.

---

## Table of Contents

1. [Overview](#overview)
2. [Current Implementation Status](#current-implementation-status)
3. [Extended Architecture](#extended-architecture)
4. [Implementation Details](#implementation-details)
5. [Elliptic Function Regression](#elliptic-function-regression)
6. [Spinor-Based Regression](#spinor-based-regression)
7. [Multi-Method Integration](#multi-method-integration)
8. [Testing Plan](#testing-plan)
9. [Deliverables](#deliverables)

---

## Overview

### Current State

**IMPLEMENTED** (✅ Complete):
- SINDy (Sparse Identification) regression
- PySR (Evolutionary search) regression
- Hierarchical search (increasing polynomial degree)
- Comparison tools (SINDy vs. PySR benchmarking)

**File**: `src/python/symbolic/regression_pipeline.py` (520 lines)

### Extended Goals

This amendment adds three new regression capabilities:

1. **Elliptic Function Regression**: Template-based search for Jacobi sn/cn/dn and Weierstrass ℘ functions
2. **Spinor-Based Regression**: Specialized search using KS spinor coordinates
3. **Multi-Stage Pipeline**: Coordinated use of all methods with intelligent fallback

---

## Current Implementation Status

### Module: `regression_pipeline.py`

**Functions Implemented**:
| Function | Purpose | Status |
|----------|---------|--------|
| `sindy_regression()` | Sparse polynomial fitting | ✅ COMPLETE |
| `pysr_regression()` | Evolutionary search | ✅ COMPLETE |
| `hierarchical_regression()` | Adaptive complexity | ✅ COMPLETE |
| `compare_methods()` | Benchmark SINDy vs PySR | ✅ COMPLETE |

**Dependencies**:
- `pysindy` - ✅ Optional, graceful degradation
- `pysr` - ✅ Optional, graceful degradation
- `sympy` - ✅ Required

**Coverage**:
- ✅ Polynomial expressions (degree 1-3)
- ✅ Rational functions (via PySR)
- ✅ Simple transcendentals (sin, cos, exp, log)
- ❌ Elliptic functions (NOT IMPLEMENTED)
- ❌ Spinor-based search (NOT IMPLEMENTED)

---

## Extended Architecture

### New Module Structure

```
src/python/symbolic/
├── regression_pipeline.py          # EXTEND (+200 lines)
│   ├── [EXISTING] sindy_regression()
│   ├── [EXISTING] pysr_regression()
│   ├── [EXISTING] hierarchical_regression()
│   ├── [NEW] elliptic_regression()            # Template-based elliptic search
│   ├── [NEW] spinor_regression()              # KS spinor specialized search
│   └── [NEW] multi_stage_regression()         # Coordinated pipeline
│
├── elliptic_search.py              # NEW MODULE (~400 lines)
│   ├── EllipticSearcher class
│   ├── fit_jacobi_template()                  # Fit sn(f(q,p), k)
│   ├── fit_weierstrass_template()             # Fit ℘(f(q,p), ω)
│   ├── optimize_modulus()                      # Find best k
│   └── optimize_lattice_params()              # Find best ω₁, ω₂
│
└── spinor_search.py                # NEW MODULE (~300 lines)
    ├── SpinorSearcher class
    ├── transform_to_spinor_coords()
    ├── spinor_basis_regression()
    └── validate_spinor_expression()
```

---

## Implementation Details

### Part A: Elliptic Function Regression (NEW - 2 days)

**File**: `src/python/symbolic/elliptic_search.py` (NEW, ~400 lines)

#### A.1: Elliptic Function Search Strategy

**Challenge**: Elliptic functions have both function form AND parameters to fit:
```
I(q, p) ≈ c₁·sn(f₁(q,p), k₁) + c₂·cn(f₂(q,p), k₂) + ... + const
```

**Two-Level Optimization**:
1. **Outer loop**: Try different argument templates f(q,p)
2. **Inner loop**: For each template, optimize modulus k (or lattice ω)

#### A.2: Implementation

```python
"""
Elliptic function regression module.

Searches for conserved quantities expressible as elliptic functions
by template matching and parameter optimization.
"""

import numpy as np
from scipy.optimize import minimize, differential_evolution
from mpmath import ellipfun, ellipk, ellipe
import sympy as sp
from typing import Callable, List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class EllipticRegressionResult:
    """Result from elliptic function regression."""
    expression_str: str
    expression_sympy: sp.Expr
    coefficients: Dict[str, float]
    moduli: Dict[str, float]  # Fitted elliptic moduli
    residual: float
    complexity: int
    template_used: str
    optimization_history: List[float]


class EllipticSearcher:
    """
    Template-based search for elliptic function representations.

    Strategy:
        1. Define argument templates: f(q,p) = E, √E·θ, L/√E, etc.
        2. For each template and elliptic function (sn, cn, dn, ℘):
            a. Fix argument template
            b. Optimize modulus k (or lattice ω) to minimize residual
        3. Select best fit across all templates
    """

    def __init__(
        self,
        function_types: List[str] = ['sn', 'cn', 'dn'],
        argument_templates: Optional[List[str]] = None,
        modulus_range: Tuple[float, float] = (0.1, 0.99)
    ):
        """
        Initialize elliptic searcher.

        Args:
            function_types: Elliptic functions to try ('sn', 'cn', 'dn', 'wp')
            argument_templates: Template types ('energy', 'angle', 'action', 'geometric')
            modulus_range: Range for modulus parameter k search
        """
        self.function_types = function_types
        self.modulus_range = modulus_range

        if argument_templates is None:
            self.argument_templates = ['energy', 'angle', 'action', 'geometric']
        else:
            self.argument_templates = argument_templates

        self.best_result = None
        self.all_results = []

    def search(
        self,
        I_numerical: Callable[[np.ndarray], float],
        sample_states: np.ndarray,
        masses: np.ndarray,
        max_templates: int = 10,
        optimization_method: str = 'differential_evolution'
    ) -> EllipticRegressionResult:
        """
        Search for best elliptic function representation.

        Args:
            I_numerical: Numerical integral to fit
            sample_states: Sample points (N, state_dim)
            masses: Body masses
            max_templates: Maximum number of templates to try
            optimization_method: 'differential_evolution' or 'minimize'

        Returns:
            best_result: Best EllipticRegressionResult across all templates
        """
        # Evaluate numerical function
        I_values = np.array([I_numerical(state) for state in sample_states])

        # Construct argument functions
        arg_funcs = self._construct_argument_functions(masses)

        best_residual = np.inf
        best_result = None

        # Try each combination
        templates_tried = 0
        for func_type in self.function_types:
            for arg_name, arg_func in arg_funcs.items():
                if templates_tried >= max_templates:
                    break

                print(f"  Trying {func_type}({arg_name}, k)...")

                # Optimize modulus for this template
                result = self._fit_template(
                    I_values,
                    sample_states,
                    func_type,
                    arg_func,
                    arg_name,
                    optimization_method
                )

                self.all_results.append(result)
                templates_tried += 1

                if result.residual < best_residual:
                    best_residual = result.residual
                    best_result = result
                    print(f"    ✓ New best: residual={result.residual:.2e}, k={result.moduli['k']:.3f}")

        self.best_result = best_result
        return best_result

    def _fit_template(
        self,
        I_values: np.ndarray,
        sample_states: np.ndarray,
        func_type: str,
        arg_func: Callable,
        arg_name: str,
        optimization_method: str
    ) -> EllipticRegressionResult:
        """
        Fit a single elliptic function template.

        Optimizes: I(z) ≈ c₁·elliptic_func(arg_func(z), k) + c₂

        Returns:
            result: Fitted result with optimal k, c₁, c₂
        """
        # Evaluate argument function on all samples
        arg_values = np.array([arg_func(state) for state in sample_states])

        # Define objective: find k, c1, c2 that minimize residual
        def objective(params):
            k, c1, c2 = params

            # Clip k to valid range
            k = np.clip(k, self.modulus_range[0], self.modulus_range[1])

            # Evaluate elliptic function
            try:
                if func_type == 'sn':
                    elliptic_vals = np.array([float(ellipfun('sn', u, k)) for u in arg_values])
                elif func_type == 'cn':
                    elliptic_vals = np.array([float(ellipfun('cn', u, k)) for u in arg_values])
                elif func_type == 'dn':
                    elliptic_vals = np.array([float(ellipfun('dn', u, k)) for u in arg_values])
                else:
                    raise ValueError(f"Unknown function type: {func_type}")

                # Predicted integral
                I_pred = c1 * elliptic_vals + c2

                # Residual
                residual = np.sqrt(np.mean((I_values - I_pred)**2))

                # Penalize extreme parameters
                penalty = 0.0
                if abs(c1) > 1e3 or abs(c2) > 1e3:
                    penalty += 1e6

                return residual + penalty

            except:
                return 1e10  # Failed evaluation

        # Optimize
        if optimization_method == 'differential_evolution':
            # Global optimization
            bounds = [(self.modulus_range[0], self.modulus_range[1]),  # k
                      (-10.0, 10.0),  # c1
                      (-10.0, 10.0)]  # c2

            opt_result = differential_evolution(
                objective,
                bounds,
                maxiter=100,
                popsize=15,
                seed=42,
                workers=1
            )
            k_opt, c1_opt, c2_opt = opt_result.x
            residual = opt_result.fun

        else:
            # Local optimization (faster but may miss global optimum)
            x0 = [0.5, 1.0, 0.0]  # Initial guess
            opt_result = minimize(
                objective,
                x0,
                method='L-BFGS-B',
                bounds=[(self.modulus_range[0], self.modulus_range[1]),
                        (-10.0, 10.0),
                        (-10.0, 10.0)]
            )
            k_opt, c1_opt, c2_opt = opt_result.x
            residual = opt_result.fun

        # Build symbolic expression
        u_sym = sp.Symbol(f'f_{arg_name}')  # Argument symbol
        k_sym = sp.Symbol('k')

        if func_type == 'sn':
            func_sym = sp.Function('sn')(u_sym, k_sym)
        elif func_type == 'cn':
            func_sym = sp.Function('cn')(u_sym, k_sym)
        elif func_type == 'dn':
            func_sym = sp.Function('dn')(u_sym, k_sym)

        expression_sympy = c1_opt * func_sym + c2_opt
        expression_str = f"{c1_opt:.4f}*{func_type}({arg_name}, {k_opt:.4f}) + {c2_opt:.4f}"

        return EllipticRegressionResult(
            expression_str=expression_str,
            expression_sympy=expression_sympy,
            coefficients={'c1': c1_opt, 'c2': c2_opt},
            moduli={'k': k_opt},
            residual=residual,
            complexity=3,  # Function call + 2 coefficients
            template_used=f"{func_type}({arg_name})",
            optimization_history=[]
        )

    def _construct_argument_functions(self, masses: np.ndarray) -> Dict[str, Callable]:
        """
        Construct physically motivated argument functions.

        Returns:
            arg_funcs: Dictionary mapping name -> function
        """
        arg_funcs = {}

        # Energy-based (if 'energy' in templates)
        if 'energy' in self.argument_templates:
            arg_funcs['sqrt_E'] = lambda state: np.sqrt(abs(self._compute_energy(state, masses)))
            arg_funcs['E'] = lambda state: self._compute_energy(state, masses)

        # Angle-based
        if 'angle' in self.argument_templates:
            arg_funcs['theta'] = lambda state: state[3] if len(state) >= 8 else 0.0  # S¹ fiber angle
            arg_funcs['atan_py_px'] = lambda state: np.arctan2(state[-2], state[-3])

        # Action-like
        if 'action' in self.argument_templates:
            arg_funcs['sqrt_E_theta'] = lambda state: (
                np.sqrt(abs(self._compute_energy(state, masses))) * state[3]
            ) if len(state) >= 8 else 0.0

        # Geometric
        if 'geometric' in self.argument_templates:
            arg_funcs['r12'] = lambda state: self._compute_r12(state, masses)

        return arg_funcs

    def _compute_energy(self, state, masses):
        """Compute total energy (simplified)."""
        n = len(state) // 2
        p = state[n:]
        return 0.5 * np.sum(p**2)  # Kinetic only (simplified)

    def _compute_r12(self, state, masses):
        """Compute r12 distance (simplified)."""
        return 1.0  # Placeholder


def elliptic_regression(
    I_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    masses: np.ndarray,
    function_types: List[str] = ['sn', 'cn', 'dn'],
    max_templates: int = 10
) -> EllipticRegressionResult:
    """
    Perform elliptic function regression.

    Args:
        I_numerical: Numerical integral to fit
        sample_states: Sample points
        masses: Body masses
        function_types: Elliptic functions to try
        max_templates: Maximum templates to search

    Returns:
        result: Best elliptic function fit

    Example:
        >>> result = elliptic_regression(my_integral, samples, masses)
        >>> print(f"Best fit: {result.expression_str}")
        >>> print(f"Residual: {result.residual:.2e}")
    """
    searcher = EllipticSearcher(
        function_types=function_types,
        argument_templates=['energy', 'angle', 'action']
    )

    result = searcher.search(
        I_numerical,
        sample_states,
        masses,
        max_templates=max_templates
    )

    return result
```

**Key Features**:
- Template-based search (try different argument functions)
- Parameter optimization (modulus k via differential evolution)
- Multiple elliptic function types (sn, cn, dn)
- Robust error handling

---

### Part B: Spinor-Based Regression (NEW - 1.5 days)

**File**: `src/python/symbolic/spinor_search.py` (NEW, ~300 lines)

```python
"""
Spinor-based symbolic regression for KS coordinates.

Specialized search that exploits KS regularization structure.
"""

import numpy as np
import sympy as sp
from typing import Callable
from ..spinor_basis import cartesian_to_ks_spinors, construct_spinor_basis


def spinor_regression(
    I_numerical: Callable[[np.ndarray], float],
    sample_states_cartesian: np.ndarray,
    masses: np.ndarray,
    max_degree: int = 2
) -> RegressionResult:
    """
    Perform regression using KS spinor coordinates.

    Strategy:
        1. Transform Cartesian states to KS spinor coordinates
        2. Construct spinor basis (bilinear forms, norms, etc.)
        3. Run SINDy on spinor basis
        4. Convert result back to Cartesian form (if needed)

    Args:
        I_numerical: Numerical integral in Cartesian coords
        sample_states_cartesian: Cartesian phase space states
        masses: Body masses
        max_degree: Maximum polynomial degree in spinors

    Returns:
        result: RegressionResult with spinor-based expression
    """
    from .regression_pipeline import sindy_regression

    # Transform to spinor coordinates
    print("Converting to KS spinor coordinates...")
    spinor_coords_list = [
        cartesian_to_ks_spinors(state, masses)
        for state in sample_states_cartesian
    ]

    # Construct spinor basis
    spinor_basis_lib = construct_spinor_basis(masses, max_degree=max_degree)

    # Create BasisLibrary object
    from ..basis_functions import BasisLibrary, BasisFunction, CoordinateSystem

    library = BasisLibrary(CoordinateSystem.KS_SPINOR, masses)
    for func, name in spinor_basis_lib:
        library.add_function(BasisFunction(
            func=func,
            name=name,
            symbol=name,
            degree=max_degree,
            category='spinor'
        ))

    # Run SINDy regression in spinor space
    print(f"Running SINDy on {len(library.functions)} spinor basis functions...")
    result = sindy_regression(
        I_numerical,  # Still evaluates on Cartesian, but basis is spinor
        sample_states_cartesian,
        library,
        threshold=0.01
    )

    # Add metadata
    result.metadata['coordinate_system'] = 'ks_spinor'
    result.metadata['spinor_basis_size'] = len(library.functions)

    return result
```

---

### Part C: Multi-Stage Regression Pipeline (NEW - 1 day)

**Extend**: `src/python/symbolic/regression_pipeline.py` (+200 lines)

```python
def multi_stage_regression(
    I_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    state_dim: int,
    masses: np.ndarray,
    residual_threshold: float = 1e-8,
    enable_elliptic: bool = True,
    enable_spinor: bool = True
) -> RegressionResult:
    """
    Multi-stage regression pipeline with intelligent fallback.

    Stages:
        1. Polynomial (SINDy, degree 1-3)
        2. Transcendental (PySR with sin/cos)
        3. Spinor-based (if enabled and state is Cartesian)
        4. Elliptic functions (if enabled)

    Each stage only runs if previous stages failed to meet threshold.

    Args:
        I_numerical: Numerical integral
        sample_states: Sample points
        state_dim: Phase space dimension
        masses: Body masses
        residual_threshold: Target residual
        enable_elliptic: Try elliptic function search
        enable_spinor: Try spinor-based search

    Returns:
        result: Best RegressionResult across all stages
    """
    results = []

    # Stage 1: Polynomial (fast)
    print("=" * 70)
    print("STAGE 1: Polynomial Regression (SINDy)")
    print("=" * 70)

    for degree in [1, 2, 3]:
        library = construct_hierarchical_basis(
            state_dim=state_dim,
            masses=masses,
            max_polynomial_degree=degree,
            include_transcendental=False
        )

        result = sindy_regression(I_numerical, sample_states, library)
        results.append(result)

        print(f"  Degree {degree}: residual={result.residual:.2e}, complexity={result.complexity}")

        if result.residual < residual_threshold:
            print(f"✓ SUCCESS at Stage 1 (polynomial degree {degree})")
            return result

    # Stage 2: Transcendental (PySR)
    if PYSR_AVAILABLE:
        print("\n" + "=" * 70)
        print("STAGE 2: Transcendental Functions (PySR)")
        print("=" * 70)

        result = pysr_regression(
            I_numerical,
            sample_states,
            niterations=50,
            unary_operators=['square', 'cube', 'sin', 'cos']
        )
        results.append(result)

        print(f"  PySR: residual={result.residual:.2e}, complexity={result.complexity}")

        if result.residual < residual_threshold:
            print("✓ SUCCESS at Stage 2 (transcendental)")
            return result

    # Stage 3: Spinor-based (if enabled)
    if enable_spinor and state_dim >= 18:  # Assume Cartesian 3-body
        print("\n" + "=" * 70)
        print("STAGE 3: Spinor-Based Regression (KS Coordinates)")
        print("=" * 70)

        try:
            from .spinor_search import spinor_regression
            result = spinor_regression(I_numerical, sample_states, masses, max_degree=2)
            results.append(result)

            print(f"  Spinor: residual={result.residual:.2e}, complexity={result.complexity}")

            if result.residual < residual_threshold:
                print("✓ SUCCESS at Stage 3 (spinor)")
                return result
        except Exception as e:
            print(f"  ⚠ Spinor regression failed: {e}")

    # Stage 4: Elliptic functions (if enabled)
    if enable_elliptic:
        print("\n" + "=" * 70)
        print("STAGE 4: Elliptic Function Search")
        print("=" * 70)

        try:
            from .elliptic_search import elliptic_regression
            result = elliptic_regression(
                I_numerical,
                sample_states,
                masses,
                max_templates=10
            )
            results.append(result)

            print(f"  Elliptic: residual={result.residual:.2e}, template={result.template_used}")

            if result.residual < residual_threshold * 10:  # Relaxed threshold
                print("✓ SUCCESS at Stage 4 (elliptic)")
                return result
        except Exception as e:
            print(f"  ⚠ Elliptic regression failed: {e}")

    # No stage succeeded - return best result
    print("\n" + "=" * 70)
    print("⚠ NO STAGE ACHIEVED THRESHOLD")
    print("=" * 70)

    best_result = min(results, key=lambda r: r.residual)
    print(f"Returning best result: residual={best_result.residual:.2e} (method={best_result.method})")

    return best_result
```

---

## Testing Plan

### Unit Tests

```python
# tests/wp3/test_elliptic_search.py

def test_simple_pendulum_recovery():
    """
    Simple pendulum has exact solution:
        θ(t) = 2*arcsin(k*sn(ω*t, k))

    Test if elliptic regression can discover this.
    """
    # Generate pendulum data
    theta_max = np.pi / 4
    k_true = np.sin(theta_max / 2)
    omega = 1.0

    t_vals = np.linspace(0, 10, 100)
    theta_vals = np.array([
        2 * np.arcsin(k_true * float(ellipfun('sn', omega * t, k_true)))
        for t in t_vals
    ])

    # Create integral: should be H = (dθ/dt)^2/2 + cos(θ) (constant)
    # ... (test implementation)

def test_elliptic_modulus_optimization():
    """Test that modulus k is correctly optimized."""
    # Create synthetic data with known k
    k_true = 0.7
    # ... (test implementation)
```

---

## Deliverables (UPDATED)

### Code Modules

- [ ] `src/python/symbolic/elliptic_search.py` (~400 lines, NEW)
- [ ] `src/python/symbolic/spinor_search.py` (~300 lines, NEW)
- [ ] `src/python/symbolic/regression_pipeline.py` (+200 lines, EXTEND)
- **TOTAL NEW CODE**: ~900 lines

### Tests

- [ ] `tests/wp3/test_elliptic_search.py` (~300 lines)
- [ ] `tests/wp3/test_spinor_search.py` (~200 lines)
- [ ] `tests/wp3/test_multi_stage_regression.py` (~200 lines)
- **TOTAL TEST CODE**: ~700 lines

### Documentation

- [ ] Tutorial: "Elliptic Functions in Symbolic Regression"
- [ ] Example notebook: "Discovering Complex Integrals"
- [ ] Performance benchmarks (time per regression stage)

---

## Success Criteria (REVISED)

### Minimum Success
- [ ] Elliptic search module functional (runs without errors)
- [ ] Can fit synthetic pendulum data
- [ ] Multi-stage pipeline selects best method

### Target Success
- [ ] Elliptic regression finds pendulum solution automatically
- [ ] Spinor regression recovers Kepler integrals
- [ ] Multi-stage pipeline tested on 5+ test cases

### Stretch Success
- [ ] Discover non-polynomial integral in three-body problem
- [ ] Elliptic function search faster than brute-force PySR
- [ ] Publication: "Automated Discovery of Elliptic Integrals"

---

**Document Version**: 2.0 (AMENDED)
**Created**: 2025-11-20
**Status**: AMENDMENT - Extended Pipeline Design
**Estimated Implementation Time**: 5-6 days
**Key Additions**:
- Elliptic function template search with parameter optimization
- Spinor-based regression using KS coordinates
- Multi-stage pipeline with intelligent fallback
- Benchmark tests on known integrable systems
