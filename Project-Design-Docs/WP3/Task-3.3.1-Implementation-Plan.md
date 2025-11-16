# Task 3.3.1: Symbolic Regression Pipeline Implementation
## Detailed Implementation Plan

**Duration**: 4-5 days
**Prerequisites**: WP 3.1 and/or WP 3.2 outputs (numerical candidate integrals)
**Objective**: Implement and integrate symbolic regression tools to convert numerical functions into analytical expressions

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Validation Strategy](#validation-strategy)
5. [Integration Points](#integration-points)
6. [Testing Plan](#testing-plan)
7. [Deliverables](#deliverables)

---

## Overview

### Purpose

Task 3.3.1 creates the infrastructure for **symbolic regression**: the process of discovering analytical mathematical expressions from numerical data. This is critical for converting the numerical candidate integrals discovered in WP 3.1 (geometric methods) and WP 3.2 (machine learning) into symbolic forms suitable for rigorous analytical validation in WP4.

### Key Challenge

**Problem**: Given a numerical function $I_{\text{num}}(q, p)$ evaluated on a set of phase space points, find a symbolic expression $I_{\text{sym}}(q, p)$ such that:

$$
\|I_{\text{num}} - I_{\text{sym}}\|_{\infty} < \epsilon \quad \text{with } \epsilon \approx 10^{-10}
$$

while minimizing the complexity of $I_{\text{sym}}$.

### Approach

**Two-Stage Pipeline**:

1. **Stage 1: SINDy (Fast, Sparse)**
   - Use sparse regression on predefined basis functions
   - Fast convergence (seconds to minutes)
   - Best for polynomial/rational expressions

2. **Stage 2: PySR (Slow, Exploratory)**
   - Evolutionary search over expression trees
   - Discovers complex functional forms
   - Fallback when SINDy fails

---

## Architecture

### Module Structure

```
src/python/symbolic/
├── regression_pipeline.py          # Main API (this task)
├── sindy_wrapper.py                # SINDy integration
├── pysr_wrapper.py                 # PySR integration
├── expression_simplification.py    # SymPy post-processing
├── numerical_validation.py         # Residual checking
└── export.py                       # Save results (SymPy, LaTeX, NumPy)
```

### Data Flow

```
Numerical Integral I_num(q,p)
    ↓
Sample on dense grid (N=10^4 to 10^6 points)
    ↓
    ├─→ SINDy (polynomial basis)
    │       ↓
    │   Success? → Simplify → Validate → Output
    │       ↓ Failure
    └─→ PySR (evolutionary search)
            ↓
        Pareto front (accuracy vs. complexity)
            ↓
        Select best → Simplify → Validate → Output
```

---

## Implementation Details

### Part A: SINDy Integration (2 days)

#### A.1: Core SINDy Wrapper

**File**: `src/python/symbolic/sindy_wrapper.py`

```python
"""
SINDy (Sparse Identification of Nonlinear Dynamics) wrapper for integral discovery.
"""

import numpy as np
import pysindy as ps
from typing import Callable, List, Tuple, Dict, Optional
from dataclasses import dataclass
import sympy as sp


@dataclass
class SINDyResult:
    """Result from SINDy symbolic regression."""
    expression: sp.Expr  # Symbolic expression (SymPy)
    coefficients: np.ndarray  # Fitted coefficients
    residual: float  # Max absolute error
    sparsity: int  # Number of non-zero terms
    basis_names: List[str]  # Names of basis functions used
    success: bool  # Whether fit is acceptable


class SINDyRegressor:
    """
    Wrapper for PySINDy library for conserved quantity discovery.

    Solves the sparse regression problem:
        min_ξ ||I_num - Θ·ξ||₂² + λ||ξ||₁

    where Θ is the library of basis functions.
    """

    def __init__(
        self,
        basis_functions: List[Tuple[Callable, str]],
        threshold: float = 0.01,
        max_iter: int = 100,
        normalize_columns: bool = True,
        verbose: bool = False
    ):
        """
        Initialize SINDy regressor.

        Args:
            basis_functions: List of (func, name) tuples
            threshold: Sparsity threshold for STLSQ algorithm
            max_iter: Maximum iterations for sequential thresholding
            normalize_columns: Normalize feature library columns
            verbose: Print progress
        """
        self.basis_functions = basis_functions
        self.threshold = threshold
        self.max_iter = max_iter
        self.normalize_columns = normalize_columns
        self.verbose = verbose

        # Build PySINDy feature library
        self._build_library()

    def _build_library(self):
        """Construct PySINDy FeatureLibrary from basis functions."""
        from pysindy.feature_library import CustomLibrary

        # Extract functions and names
        funcs = [f for f, _ in self.basis_functions]
        names = [n for _, n in self.basis_functions]

        self.library = CustomLibrary(
            library_functions=funcs,
            function_names=names
        )

    def fit(
        self,
        I_numerical: Callable[[np.ndarray], float],
        sample_points: np.ndarray,
        residual_tolerance: float = 1e-10
    ) -> SINDyResult:
        """
        Fit symbolic expression to numerical function.

        Args:
            I_numerical: Function to fit I(q,p) -> R
            sample_points: Phase space points (N, 2n) where n = DOF
            residual_tolerance: Accept if max|error| < this

        Returns:
            SINDyResult with fitted expression
        """
        # Evaluate numerical function
        if self.verbose:
            print(f"Evaluating I_num on {len(sample_points)} points...")

        I_values = np.array([I_numerical(z) for z in sample_points])

        # Reshape for PySINDy (expects (n_samples, n_features))
        X = sample_points
        y = I_values.reshape(-1, 1)

        # Create SINDy model
        model = ps.SINDy(
            feature_library=self.library,
            optimizer=ps.STLSQ(
                threshold=self.threshold,
                max_iter=self.max_iter,
                normalize_columns=self.normalize_columns
            ),
            feature_names=[f"z{i}" for i in range(X.shape[1])]
        )

        # Fit
        if self.verbose:
            print("Fitting SINDy model...")
        model.fit(X, y, quiet=not self.verbose)

        # Extract coefficients
        coeffs = model.coefficients()[0]  # First (only) equation

        # Build SymPy expression
        symbols_z = sp.symbols(f'z0:{X.shape[1]}')
        expr = self._build_sympy_expression(coeffs, symbols_z)

        # Compute residual
        expr_lambda = sp.lambdify(symbols_z, expr, 'numpy')
        predictions = np.array([expr_lambda(*z) for z in sample_points])
        residual = np.max(np.abs(predictions - I_values))

        # Check success
        success = residual < residual_tolerance
        sparsity = np.count_nonzero(coeffs)

        if self.verbose:
            print(f"Residual: {residual:.2e}, Sparsity: {sparsity}/{len(coeffs)}")
            print(f"Expression: {expr}")

        return SINDyResult(
            expression=expr,
            coefficients=coeffs,
            residual=residual,
            sparsity=sparsity,
            basis_names=[self.basis_functions[i][1] for i in range(len(coeffs)) if abs(coeffs[i]) > 1e-12],
            success=success
        )

    def _build_sympy_expression(
        self,
        coefficients: np.ndarray,
        symbols: Tuple[sp.Symbol, ...]
    ) -> sp.Expr:
        """
        Convert coefficient array to SymPy expression.

        The library evaluates as:
            Θ(x) = [φ₀(x), φ₁(x), ..., φₘ(x)]

        So the expression is:
            I(x) = Σᵢ ξᵢ φᵢ(x)

        We need to reconstruct φᵢ from basis_functions.
        """
        # This is simplified; actual implementation depends on library structure
        # For polynomial basis, PySINDy provides built-in conversion

        expr = sp.S(0)  # Start with zero

        # Manually reconstruct (would use PySINDy's equations() in practice)
        for i, coeff in enumerate(coefficients):
            if abs(coeff) > 1e-12:  # Non-zero coefficient
                # Get basis function name and convert to SymPy
                basis_name = self.basis_functions[i][1]
                basis_expr = self._name_to_sympy(basis_name, symbols)
                expr += coeff * basis_expr

        return sp.simplify(expr)

    def _name_to_sympy(self, name: str, symbols: Tuple[sp.Symbol, ...]) -> sp.Expr:
        """
        Convert basis function name to SymPy expression.

        Examples:
            "z0" -> z0
            "z0*z1" -> z0*z1
            "z0^2" -> z0**2
        """
        # Parse string to SymPy (simplified version)
        # In practice, use sympy.sympify with proper namespace
        namespace = {f'z{i}': symbols[i] for i in range(len(symbols))}
        return sp.sympify(name.replace('^', '**'), locals=namespace)


def symbolic_regression_sindy(
    I_numerical: Callable[[np.ndarray], float],
    sample_points: np.ndarray,
    basis_functions: List[Tuple[Callable, str]],
    threshold: float = 0.01,
    residual_tolerance: float = 1e-10,
    verbose: bool = False
) -> SINDyResult:
    """
    Convenience function for SINDy symbolic regression.

    Example:
        >>> basis = [(lambda z: z[0], "z0"), (lambda z: z[0]**2, "z0^2")]
        >>> result = symbolic_regression_sindy(my_function, points, basis)
        >>> print(result.expression)
        0.5*z0**2 + 1.3*z0
    """
    regressor = SINDyRegressor(
        basis_functions=basis_functions,
        threshold=threshold,
        verbose=verbose
    )

    return regressor.fit(I_numerical, sample_points, residual_tolerance)
```

**Validation Tests**:

```python
# tests/symbolic/test_sindy_wrapper.py

def test_sindy_linear():
    """Test SINDy on linear function: I(z) = 2*z0 + 3*z1"""
    def I_true(z):
        return 2*z[0] + 3*z[1]

    # Sample points
    np.random.seed(42)
    points = np.random.randn(1000, 2)

    # Basis: {1, z0, z1}
    basis = [
        (lambda z: 1.0, "1"),
        (lambda z: z[0], "z0"),
        (lambda z: z[1], "z1")
    ]

    result = symbolic_regression_sindy(I_true, points, basis, threshold=0.01)

    assert result.success
    assert result.residual < 1e-10
    assert result.sparsity == 2  # Only z0 and z1 terms


def test_sindy_quadratic():
    """Test on quadratic: I(z) = z0^2 + 2*z0*z1 + z1^2"""
    def I_true(z):
        return z[0]**2 + 2*z[0]*z[1] + z[1]**2

    points = np.random.randn(2000, 2)

    # Polynomial basis up to degree 2
    basis = construct_polynomial_basis(dim=2, max_degree=2)

    result = symbolic_regression_sindy(I_true, points, basis)

    assert result.success
    assert abs(result.residual) < 1e-9
```

---

#### A.2: Expression Simplification

**File**: `src/python/symbolic/expression_simplification.py`

```python
"""
Post-processing and simplification of symbolic expressions.
"""

import sympy as sp
from typing import Dict, List, Tuple


def simplify_expression(
    expr: sp.Expr,
    known_integrals: Dict[str, sp.Expr] = None,
    target_form: str = 'polynomial'
) -> Tuple[sp.Expr, Dict[str, any]]:
    """
    Simplify symbolic expression using SymPy and physics knowledge.

    Args:
        expr: Raw expression from symbolic regression
        known_integrals: Dictionary of known quantities (E, L, etc.)
        target_form: Desired form ('polynomial', 'rational', 'trigonometric')

    Returns:
        simplified_expr: Simplified expression
        metadata: Simplification steps and statistics
    """
    metadata = {'steps': []}

    # Step 1: Basic algebraic simplification
    expr_simp = sp.simplify(expr)
    metadata['steps'].append(('simplify', expr_simp))

    # Step 2: Factor if polynomial
    if target_form == 'polynomial':
        expr_simp = sp.factor(expr_simp)
        metadata['steps'].append(('factor', expr_simp))

    # Step 3: Rationalize denominators
    expr_simp = sp.ratsimp(expr_simp)
    metadata['steps'].append(('ratsimp', expr_simp))

    # Step 4: Trigonometric simplification
    if target_form == 'trigonometric':
        expr_simp = sp.trigsimp(expr_simp)
        metadata['steps'].append(('trigsimp', expr_simp))

    # Step 5: Collect terms by powers
    if expr_simp.is_polynomial():
        symbols_list = list(expr_simp.free_symbols)
        for sym in symbols_list:
            expr_simp = sp.collect(expr_simp, sym)

    # Step 6: Round small coefficients to zero
    expr_simp = round_coefficients(expr_simp, threshold=1e-12)
    metadata['steps'].append(('round', expr_simp))

    # Step 7: Substitute known integrals (optional)
    if known_integrals:
        expr_simp = expr_simp.subs(known_integrals)
        metadata['steps'].append(('substitute', expr_simp))

    # Metadata
    metadata['complexity'] = count_operations(expr_simp)
    metadata['degree'] = get_polynomial_degree(expr_simp)
    metadata['symbols'] = list(expr_simp.free_symbols)

    return expr_simp, metadata


def round_coefficients(expr: sp.Expr, threshold: float = 1e-12) -> sp.Expr:
    """
    Round coefficients smaller than threshold to zero.

    Example:
        1.0*x + 1e-14*y -> 1.0*x
    """
    def round_term(term):
        if term.is_number:
            if abs(float(term)) < threshold:
                return sp.S(0)
            else:
                # Round to reasonable precision
                return sp.nsimplify(term, rational=True)
        return term

    return expr.replace(lambda x: x.is_number, round_term)


def count_operations(expr: sp.Expr) -> int:
    """Count number of mathematical operations in expression."""
    return sp.count_ops(expr)


def get_polynomial_degree(expr: sp.Expr) -> int:
    """Get maximum degree of polynomial (or -1 if not polynomial)."""
    if not expr.is_polynomial():
        return -1

    symbols_list = list(expr.free_symbols)
    if not symbols_list:
        return 0

    poly = sp.Poly(expr, *symbols_list)
    return poly.total_degree()


def convert_to_latex(expr: sp.Expr) -> str:
    """Convert expression to LaTeX for publication."""
    return sp.latex(expr)


def convert_to_numpy_function(expr: sp.Expr, symbols: List[sp.Symbol]) -> callable:
    """
    Convert SymPy expression to fast NumPy function.

    Returns:
        func: Callable that accepts NumPy array
    """
    return sp.lambdify(symbols, expr, 'numpy')
```

---

### Part B: PySR Integration (2 days)

**File**: `src/python/symbolic/pysr_wrapper.py`

```python
"""
PySR (Python Symbolic Regression) wrapper for complex expression discovery.
"""

import numpy as np
import pandas as pd
from pysr import PySRRegressor
from typing import Callable, List, Dict, Optional
from dataclasses import dataclass
import sympy as sp


@dataclass
class PySRResult:
    """Result from PySR symbolic regression (Pareto front)."""
    pareto_front: pd.DataFrame  # All solutions (complexity vs. accuracy)
    best_expression: sp.Expr  # Best trade-off
    best_residual: float
    best_complexity: int
    search_time: float  # Seconds


class PySRRegressor:
    """
    Wrapper for PySR evolutionary symbolic regression.

    Uses genetic programming to search expression space.
    """

    def __init__(
        self,
        niterations: int = 100,
        populations: int = 20,
        population_size: int = 33,
        binary_operators: List[str] = None,
        unary_operators: List[str] = None,
        constraints: Dict = None,
        maxsize: int = 20,
        parsimony: float = 0.01,
        complexity_of_constants: int = 1,
        verbose: bool = False
    ):
        """
        Initialize PySR regressor.

        Args:
            niterations: Number of generations
            populations: Number of parallel populations
            population_size: Individuals per population
            binary_operators: ["+", "-", "*", "/", "^"]
            unary_operators: ["sin", "cos", "exp", "log", "sqrt"]
            constraints: Operator-specific constraints
            maxsize: Maximum expression size (number of nodes)
            parsimony: Penalty for complexity
            complexity_of_constants: Cost of constant terms
            verbose: Print progress
        """
        # Default operators
        if binary_operators is None:
            binary_operators = ["+", "-", "*", "/", "^"]
        if unary_operators is None:
            unary_operators = ["sin", "cos", "exp", "log", "sqrt", "abs"]

        # Default constraints
        if constraints is None:
            constraints = {
                "^": (-1, 3),  # Power limited to cubic
                "/": (-1, 1),  # Denominator complexity limit
                "log": 3,      # Argument complexity
                "exp": 3,
            }

        self.model = PySRRegressor(
            niterations=niterations,
            populations=populations,
            population_size=population_size,
            binary_operators=binary_operators,
            unary_operators=unary_operators,
            constraints=constraints,
            maxsize=maxsize,
            parsimony=parsimony,
            complexity_of_constants=complexity_of_constants,
            verbosity=1 if verbose else 0,
            # Performance options
            procs=0,  # Use all available cores
            multithreading=True,
            batching=True,
            # Convergence
            early_stop_condition="stop_if(loss, complexity) = loss < 1e-12",
        )

        self.verbose = verbose

    def fit(
        self,
        I_numerical: Callable[[np.ndarray], float],
        sample_points: np.ndarray,
        variable_names: List[str] = None
    ) -> PySRResult:
        """
        Fit symbolic expression using evolutionary search.

        Args:
            I_numerical: Numerical function to fit
            sample_points: Phase space points (N, dim)
            variable_names: Names for variables (e.g., ["q0", "q1", "p0", "p1"])

        Returns:
            PySRResult with Pareto front of solutions
        """
        import time

        # Evaluate numerical function
        if self.verbose:
            print(f"Evaluating I_num on {len(sample_points)} points...")

        I_values = np.array([I_numerical(z) for z in sample_points])

        # Set variable names
        if variable_names is None:
            variable_names = [f"z{i}" for i in range(sample_points.shape[1])]

        # Fit
        if self.verbose:
            print("Starting PySR evolutionary search...")
            print(f"  Iterations: {self.model.niterations}")
            print(f"  Populations: {self.model.populations}")

        start_time = time.time()
        self.model.fit(sample_points, I_values, variable_names=variable_names)
        elapsed = time.time() - start_time

        # Extract results (Pareto front)
        pareto_df = self.model.equations_

        # Select best expression (trade-off between accuracy and complexity)
        best_idx = self._select_best_from_pareto(pareto_df)
        best_row = pareto_df.iloc[best_idx]

        # Convert to SymPy
        best_expr = sp.sympify(best_row['equation'])
        best_residual = best_row['loss']
        best_complexity = best_row['complexity']

        if self.verbose:
            print(f"Best expression (complexity={best_complexity}, loss={best_residual:.2e}):")
            print(f"  {best_expr}")
            print(f"Search completed in {elapsed:.1f}s")

        return PySRResult(
            pareto_front=pareto_df,
            best_expression=best_expr,
            best_residual=best_residual,
            best_complexity=best_complexity,
            search_time=elapsed
        )

    def _select_best_from_pareto(self, pareto_df: pd.DataFrame) -> int:
        """
        Select best expression from Pareto front.

        Strategy: Minimize score = loss + parsimony * complexity
        """
        scores = pareto_df['loss'] + self.model.parsimony * pareto_df['complexity']
        return scores.idxmin()


def symbolic_regression_pysr(
    I_numerical: Callable[[np.ndarray], float],
    sample_points: np.ndarray,
    niterations: int = 100,
    maxsize: int = 20,
    verbose: bool = False
) -> PySRResult:
    """
    Convenience function for PySR symbolic regression.

    Example:
        >>> result = symbolic_regression_pysr(my_integral, points, niterations=50)
        >>> print(result.best_expression)
        z0**2 + sin(z1)
    """
    regressor = PySRRegressorWrapper(
        niterations=niterations,
        maxsize=maxsize,
        verbose=verbose
    )

    return regressor.fit(I_numerical, sample_points)
```

---

### Part C: Main Pipeline (1 day)

**File**: `src/python/symbolic/regression_pipeline.py`

```python
"""
Main symbolic regression pipeline: SINDy → PySR → Validation.
"""

import numpy as np
import sympy as sp
from typing import Callable, List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from .sindy_wrapper import symbolic_regression_sindy, SINDyResult
from .pysr_wrapper import symbolic_regression_pysr, PySRResult
from .expression_simplification import simplify_expression
from .numerical_validation import validate_symbolic_fit


class RegressionMethod(Enum):
    """Symbolic regression method selection."""
    SINDY = "sindy"
    PYSR = "pysr"
    AUTO = "auto"  # Try SINDy first, fallback to PySR


@dataclass
class SymbolicRegressionResult:
    """Complete symbolic regression result."""
    expression: sp.Expr  # Final simplified expression
    method_used: RegressionMethod
    residual: float  # Max absolute error
    complexity: int  # Number of operations
    success: bool  # Whether fit is acceptable

    # Method-specific results
    sindy_result: Optional[SINDyResult] = None
    pysr_result: Optional[PySRResult] = None

    # Validation
    validation_passed: bool = False
    validation_points: int = 0

    # Metadata
    metadata: Dict = field(default_factory=dict)


def symbolic_regression_pipeline(
    I_numerical: Callable[[np.ndarray], float],
    sample_points: np.ndarray,
    basis_functions: List[Tuple[Callable, str]],
    method: RegressionMethod = RegressionMethod.AUTO,
    residual_tolerance: float = 1e-10,
    sindy_threshold: float = 0.01,
    pysr_iterations: int = 100,
    validation_points: Optional[np.ndarray] = None,
    verbose: bool = False
) -> SymbolicRegressionResult:
    """
    Complete symbolic regression pipeline with automatic method selection.

    Workflow:
        1. Try SINDy (fast, polynomial basis)
        2. If SINDy fails, try PySR (slow, exploratory)
        3. Simplify resulting expression
        4. Validate on independent test points

    Args:
        I_numerical: Numerical function to fit
        sample_points: Training points (N, dim)
        basis_functions: Basis for SINDy
        method: Regression method (AUTO, SINDY, PYSR)
        residual_tolerance: Acceptance threshold
        sindy_threshold: SINDy sparsity parameter
        pysr_iterations: PySR search iterations
        validation_points: Independent test set (if None, use holdout)
        verbose: Print progress

    Returns:
        SymbolicRegressionResult with best fit
    """
    result = SymbolicRegressionResult(
        expression=sp.S(0),
        method_used=method,
        residual=np.inf,
        complexity=0,
        success=False
    )

    # Prepare validation set
    if validation_points is None:
        # Use 20% holdout
        n_train = int(0.8 * len(sample_points))
        train_points = sample_points[:n_train]
        validation_points = sample_points[n_train:]
    else:
        train_points = sample_points

    # Stage 1: Try SINDy
    if method in [RegressionMethod.SINDY, RegressionMethod.AUTO]:
        if verbose:
            print("=" * 60)
            print("Stage 1: SINDy (Sparse Polynomial Regression)")
            print("=" * 60)

        try:
            sindy_res = symbolic_regression_sindy(
                I_numerical,
                train_points,
                basis_functions,
                threshold=sindy_threshold,
                residual_tolerance=residual_tolerance,
                verbose=verbose
            )

            result.sindy_result = sindy_res

            if sindy_res.success:
                if verbose:
                    print(f"✓ SINDy succeeded! Residual: {sindy_res.residual:.2e}")

                result.expression = sindy_res.expression
                result.residual = sindy_res.residual
                result.complexity = sindy_res.sparsity
                result.method_used = RegressionMethod.SINDY
                result.success = True

                # Skip PySR if SINDy worked
                if method == RegressionMethod.AUTO:
                    method = RegressionMethod.SINDY

        except Exception as e:
            if verbose:
                print(f"✗ SINDy failed: {e}")

    # Stage 2: Try PySR (if SINDy failed and method allows)
    if not result.success and method in [RegressionMethod.PYSR, RegressionMethod.AUTO]:
        if verbose:
            print("\n" + "=" * 60)
            print("Stage 2: PySR (Evolutionary Search)")
            print("=" * 60)

        try:
            pysr_res = symbolic_regression_pysr(
                I_numerical,
                train_points,
                niterations=pysr_iterations,
                verbose=verbose
            )

            result.pysr_result = pysr_res

            # Check if acceptable
            if pysr_res.best_residual < residual_tolerance:
                if verbose:
                    print(f"✓ PySR succeeded! Residual: {pysr_res.best_residual:.2e}")

                result.expression = pysr_res.best_expression
                result.residual = pysr_res.best_residual
                result.complexity = pysr_res.best_complexity
                result.method_used = RegressionMethod.PYSR
                result.success = True
            else:
                if verbose:
                    print(f"⚠ PySR converged but residual too large: {pysr_res.best_residual:.2e}")

                # Still use best effort
                result.expression = pysr_res.best_expression
                result.residual = pysr_res.best_residual
                result.complexity = pysr_res.best_complexity
                result.method_used = RegressionMethod.PYSR

        except Exception as e:
            if verbose:
                print(f"✗ PySR failed: {e}")

    # Stage 3: Simplification
    if result.expression != sp.S(0):
        if verbose:
            print("\n" + "=" * 60)
            print("Stage 3: Expression Simplification")
            print("=" * 60)
            print(f"Before: {result.expression}")

        simplified, metadata = simplify_expression(result.expression)
        result.expression = simplified
        result.metadata['simplification'] = metadata

        if verbose:
            print(f"After:  {result.expression}")
            print(f"Complexity: {metadata['complexity']} operations")

    # Stage 4: Validation on independent test set
    if result.expression != sp.S(0):
        if verbose:
            print("\n" + "=" * 60)
            print("Stage 4: Validation on Test Set")
            print("=" * 60)

        validation_passed, val_residual = validate_symbolic_fit(
            result.expression,
            I_numerical,
            validation_points,
            tolerance=residual_tolerance
        )

        result.validation_passed = validation_passed
        result.validation_points = len(validation_points)
        result.metadata['validation_residual'] = val_residual

        if verbose:
            status = "✓ PASSED" if validation_passed else "✗ FAILED"
            print(f"{status} - Validation residual: {val_residual:.2e}")

    # Final summary
    if verbose:
        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(f"Method: {result.method_used.value}")
        print(f"Expression: {result.expression}")
        print(f"Training residual: {result.residual:.2e}")
        print(f"Validation: {'PASSED' if result.validation_passed else 'FAILED'}")
        print(f"Success: {result.success}")

    return result
```

---

## Validation Strategy

### V1: Known Function Recovery

**Test**: Can the pipeline recover known mathematical expressions?

```python
def test_recover_energy():
    """Test on Hamiltonian: H = 0.5*(p0^2 + p1^2) + V(q0, q1)"""
    # Define energy function
    def H(z):
        q0, q1, p0, p1 = z
        return 0.5 * (p0**2 + p1**2) + potential(q0, q1)

    # Sample points
    points = generate_phase_space_grid(n=1000, dim=4)

    # Basis (quadratic in momenta)
    basis = construct_polynomial_basis(dim=4, max_degree=2)

    # Regress
    result = symbolic_regression_pipeline(H, points, basis)

    assert result.success
    assert result.residual < 1e-12
    # Check expression matches expected form


def test_recover_angular_momentum():
    """Test on L = q0*p1 - q1*p0"""
    def L(z):
        q0, q1, p0, p1 = z
        return q0*p1 - q1*p0

    points = np.random.randn(2000, 4)
    basis = construct_polynomial_basis(dim=4, max_degree=2)

    result = symbolic_regression_pipeline(L, points, basis)

    assert result.success
    assert result.sparsity == 2  # Only two terms
```

---

## Integration Points

### Input Interface

**From WP 3.1**:
```python
# Killing field converted to integral
I_geometric = integral_from_killing_field(killing_field, metric)

# Regress to symbolic form
result = symbolic_regression_pipeline(
    I_numerical=I_geometric.evaluate,
    sample_points=sample_grid,
    basis_functions=geometric_basis
)
```

**From WP 3.2**:
```python
# ML-discovered integral
I_ml = trained_hnn.predict_integral(state)

# Convert to symbolic
result = symbolic_regression_pipeline(
    I_numerical=I_ml,
    sample_points=trajectory_data,
    basis_functions=polynomial_basis,
    method=RegressionMethod.PYSR  # May need complex forms
)
```

### Output Interface

**To WP 3.3.3** (Candidate Ranking):
```python
# Create candidate from regression result
candidate = CandidateIntegral(
    expression=result.expression,
    source='symbolic_regression',
    conservation_error=result.residual,
    complexity=result.complexity,
    independent=True  # To be tested
)

candidates.append(candidate)
```

---

## Testing Plan

### Unit Tests

1. **SINDy wrapper**: `test_sindy_wrapper.py`
   - Linear functions
   - Quadratic functions
   - Failure cases (non-polynomial)

2. **PySR wrapper**: `test_pysr_wrapper.py`
   - Transcendental functions
   - Rational functions
   - Pareto front selection

3. **Simplification**: `test_simplification.py`
   - Coefficient rounding
   - Factorization
   - Trigonometric identities

### Integration Tests

4. **Full pipeline**: `test_regression_pipeline.py`
   - Auto method selection
   - SINDy → PySR fallback
   - Validation on test set

### Performance Tests

5. **Timing benchmarks**:
   - SINDy: Should complete in < 1 minute
   - PySR: Allow up to 1 hour for complex searches

---

## Deliverables

### Code Modules (5 files)

- [x] `sindy_wrapper.py` (~400 lines)
- [x] `pysr_wrapper.py` (~350 lines)
- [x] `expression_simplification.py` (~250 lines)
- [x] `numerical_validation.py` (~200 lines) - See below
- [x] `regression_pipeline.py` (~300 lines)

**Total**: ~1,500 lines

### Documentation

- [ ] API documentation (Sphinx docstrings)
- [ ] Tutorial notebook: "Symbolic Regression for Conserved Quantities"
- [ ] Examples: Kepler problem, harmonic oscillator

### Tests

- [ ] Unit tests: 15+ test functions
- [ ] Integration tests: 5+ end-to-end scenarios
- [ ] Performance benchmarks

---

## Numerical Validation Module

**File**: `src/python/symbolic/numerical_validation.py`

```python
"""
Validation of symbolic expressions against numerical ground truth.
"""

import numpy as np
import sympy as sp
from typing import Callable, Tuple, List


def validate_symbolic_fit(
    I_symbolic: sp.Expr,
    I_numerical: Callable[[np.ndarray], float],
    test_points: np.ndarray,
    tolerance: float = 1e-10
) -> Tuple[bool, float]:
    """
    Verify that symbolic expression matches numerical function on test set.

    Args:
        I_symbolic: SymPy expression
        I_numerical: Ground truth function
        test_points: Test phase space points (N, dim)
        tolerance: Acceptance threshold for max|error|

    Returns:
        success: True if max residual < tolerance
        max_residual: Maximum absolute error
    """
    # Convert SymPy to NumPy function
    symbols_list = sorted(I_symbolic.free_symbols, key=lambda s: s.name)
    I_symbolic_func = sp.lambdify(symbols_list, I_symbolic, 'numpy')

    # Evaluate both functions
    residuals = []
    for z in test_points:
        try:
            val_sym = float(I_symbolic_func(*z))
            val_num = float(I_numerical(z))
            residuals.append(abs(val_sym - val_num))
        except Exception as e:
            # Handle evaluation errors (e.g., division by zero)
            residuals.append(np.inf)

    max_residual = np.max(residuals)
    success = max_residual < tolerance

    return success, max_residual


def compute_residual_statistics(
    I_symbolic: sp.Expr,
    I_numerical: Callable[[np.ndarray], float],
    test_points: np.ndarray
) -> dict:
    """
    Compute detailed residual statistics.

    Returns:
        stats: Dictionary with mean, std, max, percentiles
    """
    symbols_list = sorted(I_symbolic.free_symbols, key=lambda s: s.name)
    I_symbolic_func = sp.lambdify(symbols_list, I_symbolic, 'numpy')

    residuals = np.array([
        abs(float(I_symbolic_func(*z)) - float(I_numerical(z)))
        for z in test_points
    ])

    return {
        'mean': np.mean(residuals),
        'std': np.std(residuals),
        'max': np.max(residuals),
        'median': np.median(residuals),
        'p95': np.percentile(residuals, 95),
        'p99': np.percentile(residuals, 99)
    }
```

---

## Success Criteria

### Minimum Success
- [ ] SINDy wrapper functional on polynomial test cases
- [ ] PySR wrapper runs without errors
- [ ] At least one known integral (E or L) recovered

### Target Success
- [ ] Full pipeline converts numerical → symbolic with residual < 1e-10
- [ ] Works on at least 3/5 test cases
- [ ] Validation on independent test set passes

### Stretch Success
- [ ] Auto method selection always chooses optimal approach
- [ ] PySR discovers complex forms (transcendental, rational)
- [ ] Pipeline completes in < 10 minutes for typical cases

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Implementation Plan
**Estimated Implementation Time**: 4-5 days
