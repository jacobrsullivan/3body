"""
Symbolic regression pipeline for discovering analytical expressions (Task 3.3.1).

This module provides interfaces to symbolic regression tools:
1. SINDy (Sparse Identification of Nonlinear Dynamics)
2. PySR (Python Symbolic Regression via evolutionary algorithms)

The pipeline converts numerical candidate integrals from WP3.1 (geometric)
and WP3.2 (ML) into concise analytical expressions suitable for WP4 validation.

Key Features:
- Physics-informed basis function libraries
- Sparsity-promoting regression (few terms)
- Multi-stage regression (coarse to fine)
- Expression complexity control
- Numerical validation of fitted expressions

References:
- Brunton et al., "Discovering governing equations from data" (2016)
- Cranmer, "Interpretable ML for Science with PySR" (2023)
"""

import numpy as np
import sympy as sp
from typing import Callable, List, Tuple, Dict, Optional, Union
from dataclasses import dataclass
import warnings

# Optional dependencies - gracefully handle if not installed
try:
    import pysindy as ps
    PYSINDY_AVAILABLE = True
except ImportError:
    PYSINDY_AVAILABLE = False
    warnings.warn("pysindy not installed. Install with: pip install pysindy")

try:
    from pysr import PySRRegressor
    import pandas as pd
    PYSR_AVAILABLE = True
except ImportError:
    PYSR_AVAILABLE = False
    warnings.warn("PySR not installed. Install with: pip install pysr")

from .basis_functions import BasisLibrary, construct_hierarchical_basis


@dataclass
class RegressionResult:
    """
    Result from symbolic regression.

    Attributes:
        expression_str: String representation of fitted expression
        expression_sympy: SymPy expression object
        coefficients: Dictionary of coefficient values
        residual: Root mean squared error on training data
        complexity: Expression complexity (number of operations)
        basis_functions_used: List of basis function names in expression
        method: Regression method used ('sindy' or 'pysr')
        metadata: Additional method-specific information
    """
    expression_str: str
    expression_sympy: sp.Expr
    coefficients: Dict[str, float]
    residual: float
    complexity: int
    basis_functions_used: List[str]
    method: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def evaluate(self, state: np.ndarray, variable_mapping: Dict[str, int]) -> float:
        """
        Evaluate symbolic expression on a state.

        Args:
            state: Phase space state vector
            variable_mapping: Map from symbol names to state indices

        Returns:
            value: Evaluated expression
        """
        # Create substitution dictionary
        subs = {sp.Symbol(name): state[idx] for name, idx in variable_mapping.items()}
        return float(self.expression_sympy.subs(subs))


def sindy_regression(
    I_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    basis_library: BasisLibrary,
    threshold: float = 0.01,
    alpha: float = 0.05,
    max_iter: int = 20,
    normalize_columns: bool = True
) -> RegressionResult:
    """
    Perform sparse regression using SINDy.

    SINDy fits a sparse linear combination of basis functions:
        I(z) ≈ sum_j ξ_j φ_j(z)

    where sparsity is enforced via sequential thresholded least squares.

    Args:
        I_numerical: Numerical function to fit
        sample_states: Sample points (N, state_dim)
        basis_library: BasisLibrary object with basis functions
        threshold: Sparsity threshold (coefficients < threshold set to 0)
        alpha: L2 regularization parameter
        max_iter: Maximum iterations for STLSQ
        normalize_columns: Normalize feature columns before fitting

    Returns:
        result: RegressionResult with fitted expression

    Raises:
        RuntimeError: If pysindy is not installed

    Example:
        >>> library = construct_hierarchical_basis(state_dim=8, max_polynomial_degree=2)
        >>> samples = np.random.randn(1000, 8)
        >>> result = sindy_regression(my_integral, samples, library)
        >>> print(f"Expression: {result.expression_str}")
        >>> print(f"Residual: {result.residual:.2e}")
    """
    if not PYSINDY_AVAILABLE:
        raise RuntimeError("pysindy not installed. Cannot use SINDy regression.")

    # Evaluate numerical function on samples
    N = len(sample_states)
    I_values = np.array([I_numerical(state) for state in sample_states])

    # Evaluate basis library on samples
    Theta = basis_library.evaluate_library_batch(sample_states)  # (N, n_functions)

    # SINDy regression using STLSQ
    optimizer = ps.STLSQ(
        threshold=threshold,
        alpha=alpha,
        max_iter=max_iter,
        normalize_columns=normalize_columns
    )

    # Fit: I_values = Theta @ ξ
    optimizer.fit(Theta, I_values)
    coefficients = optimizer.coef_

    # Extract non-zero coefficients
    nonzero_idx = np.where(np.abs(coefficients) > 1e-12)[0]
    active_funcs = [basis_library.functions[i] for i in nonzero_idx]
    active_coeffs = coefficients[nonzero_idx]

    # Build symbolic expression
    expression_terms = []
    coeff_dict = {}

    for idx, (func, coeff) in enumerate(zip(active_funcs, active_coeffs)):
        # Create symbolic term
        if abs(coeff) < 1e-12:
            continue

        symbol = sp.Symbol(func.symbol) if func.symbol != "1" else 1
        term = coeff * symbol if symbol != 1 else coeff
        expression_terms.append(term)

        coeff_dict[func.name] = float(coeff)

    if len(expression_terms) == 0:
        expression_sympy = sp.S.Zero
        expression_str = "0"
    else:
        expression_sympy = sum(expression_terms)
        expression_str = str(expression_sympy)

    # Compute residual
    I_pred = Theta @ coefficients
    residual = np.sqrt(np.mean((I_values - I_pred)**2))

    # Count complexity (number of operations)
    complexity = len(active_funcs)

    return RegressionResult(
        expression_str=expression_str,
        expression_sympy=expression_sympy,
        coefficients=coeff_dict,
        residual=residual,
        complexity=complexity,
        basis_functions_used=[f.name for f in active_funcs],
        method='sindy',
        metadata={
            'threshold': threshold,
            'alpha': alpha,
            'n_active_terms': len(active_funcs),
            'total_basis_size': len(basis_library.functions)
        }
    )


def pysr_regression(
    I_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    niterations: int = 100,
    populations: int = 20,
    population_size: int = 33,
    maxsize: int = 20,
    binary_operators: Optional[List[str]] = None,
    unary_operators: Optional[List[str]] = None,
    complexity_weight: float = 0.01,
    parsimony: float = 0.001,
    timeout_in_seconds: Optional[float] = None,
    return_pareto_front: bool = False
) -> Union[RegressionResult, List[RegressionResult]]:
    """
    Perform symbolic regression using PySR (evolutionary algorithm).

    PySR searches over expression trees using genetic programming,
    balancing accuracy vs. complexity via Pareto optimization.

    Args:
        I_numerical: Numerical function to fit
        sample_states: Sample points (N, state_dim)
        niterations: Number of evolutionary iterations
        populations: Number of parallel populations
        population_size: Size of each population
        maxsize: Maximum expression complexity (number of nodes)
        binary_operators: Binary ops (default: ['+', '-', '*', '/', '^'])
        unary_operators: Unary ops (default: ['square', 'cube', 'sqrt'])
        complexity_weight: Weight for complexity in loss
        parsimony: Additional parsimony penalty
        timeout_in_seconds: Max runtime (None = no limit)
        return_pareto_front: If True, return all Pareto-optimal expressions

    Returns:
        result: RegressionResult (or list if return_pareto_front=True)

    Raises:
        RuntimeError: If PySR is not installed

    Example:
        >>> samples = np.random.randn(1000, 8)
        >>> result = pysr_regression(my_integral, samples, niterations=50)
        >>> print(f"Best expression: {result.expression_str}")
    """
    if not PYSR_AVAILABLE:
        raise RuntimeError("PySR not installed. Install with: pip install pysr")

    # Evaluate numerical function
    N, state_dim = sample_states.shape
    I_values = np.array([I_numerical(state) for state in sample_states])

    # Default operators
    if binary_operators is None:
        binary_operators = ["+", "-", "*", "/", "^"]

    if unary_operators is None:
        unary_operators = ["square", "cube"]

    # Configure PySR
    model = PySRRegressor(
        niterations=niterations,
        populations=populations,
        population_size=population_size,
        binary_operators=binary_operators,
        unary_operators=unary_operators,
        maxsize=maxsize,
        complexity_of_operators={
            "+": 1, "-": 1, "*": 2, "/": 2, "^": 3,
            "square": 2, "cube": 3, "sqrt": 2,
            "sin": 3, "cos": 3, "exp": 4, "log": 3
        },
        loss="L2DistLoss()",
        model_selection="best",  # or "accuracy" for Pareto front
        timeout_in_seconds=timeout_in_seconds,
        parsimony=parsimony,
        verbosity=0,
        random_state=42
    )

    # Fit
    model.fit(sample_states, I_values)

    # Get results
    equations_df = model.equations_

    if return_pareto_front:
        # Return all Pareto-optimal expressions
        results = []
        for _, row in equations_df.iterrows():
            expr_str = row['equation']
            complexity = row['complexity']
            mse = row['loss']
            residual = np.sqrt(mse)

            # Convert to SymPy
            try:
                expr_sympy = sp.sympify(expr_str)
            except:
                expr_sympy = sp.S.Zero

            results.append(RegressionResult(
                expression_str=expr_str,
                expression_sympy=expr_sympy,
                coefficients={},  # PySR doesn't separate coefficients
                residual=residual,
                complexity=complexity,
                basis_functions_used=[],
                method='pysr',
                metadata={'row_index': len(results)}
            ))
        return results
    else:
        # Return best expression
        best_row = equations_df.iloc[-1]  # Last row is typically best
        expr_str = best_row['equation']
        complexity = best_row['complexity']
        mse = best_row['loss']
        residual = np.sqrt(mse)

        # Convert to SymPy
        try:
            expr_sympy = sp.sympify(expr_str)
        except:
            expr_sympy = sp.S.Zero

        return RegressionResult(
            expression_str=expr_str,
            expression_sympy=expr_sympy,
            coefficients={},
            residual=residual,
            complexity=int(complexity),
            basis_functions_used=[],
            method='pysr',
            metadata={
                'n_pareto_expressions': len(equations_df),
                'pareto_front_available': True
            }
        )


def hierarchical_regression(
    I_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    state_dim: int,
    masses: np.ndarray,
    method: str = 'sindy',
    max_complexity: int = 3,
    residual_threshold: float = 1e-8
) -> Optional[RegressionResult]:
    """
    Hierarchical regression: try increasing complexity until fit is good.

    Strategy:
        1. Try linear basis (degree 1)
        2. If residual too high, try quadratic (degree 2)
        3. If still too high, try cubic (degree 3)
        4. If still too high, try with transcendentals

    Args:
        I_numerical: Numerical function to fit
        sample_states: Sample points
        state_dim: Dimension of phase space
        masses: Body masses
        method: 'sindy' or 'pysr'
        max_complexity: Maximum polynomial degree to try
        residual_threshold: Target residual

    Returns:
        result: Best RegressionResult, or None if all fail
    """
    # Try polynomial degrees in order
    for degree in range(1, max_complexity + 1):
        print(f"Trying polynomial degree {degree}...")

        library = construct_hierarchical_basis(
            state_dim=state_dim,
            masses=masses,
            max_polynomial_degree=degree,
            include_transcendental=False,
            include_conservation=True
        )

        if method == 'sindy':
            if not PYSINDY_AVAILABLE:
                print("SINDy not available, skipping.")
                continue

            result = sindy_regression(
                I_numerical,
                sample_states,
                library,
                threshold=0.01,
                alpha=0.05
            )
        elif method == 'pysr':
            if not PYSR_AVAILABLE:
                print("PySR not available, skipping.")
                continue

            result = pysr_regression(
                I_numerical,
                sample_states,
                niterations=50,
                maxsize=degree * 5
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        print(f"  Residual: {result.residual:.2e}, Complexity: {result.complexity}")

        if result.residual < residual_threshold:
            print(f"✓ Good fit found at degree {degree}")
            return result

    # Try with transcendentals if polynomial didn't work
    print(f"Trying with transcendental functions...")
    library = construct_hierarchical_basis(
        state_dim=state_dim,
        masses=masses,
        max_polynomial_degree=2,
        include_transcendental=True,
        include_conservation=True
    )

    if method == 'sindy':
        result = sindy_regression(I_numerical, sample_states, library, threshold=0.02)
    elif method == 'pysr':
        result = pysr_regression(
            I_numerical, sample_states,
            niterations=100,
            unary_operators=['square', 'cube', 'sin', 'cos']
        )

    print(f"  Residual: {result.residual:.2e}, Complexity: {result.complexity}")

    if result.residual < residual_threshold * 10:  # Relaxed threshold
        return result
    else:
        print("⚠ No good fit found with any method")
        return None


def compare_methods(
    I_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    basis_library: BasisLibrary
) -> Dict[str, RegressionResult]:
    """
    Compare SINDy and PySR on the same problem.

    Args:
        I_numerical: Numerical function
        sample_states: Sample points
        basis_library: Basis library (used for SINDy)

    Returns:
        results: Dict with 'sindy' and 'pysr' RegressionResults
    """
    results = {}

    # SINDy
    if PYSINDY_AVAILABLE:
        try:
            results['sindy'] = sindy_regression(I_numerical, sample_states, basis_library)
        except Exception as e:
            print(f"SINDy failed: {e}")

    # PySR
    if PYSR_AVAILABLE:
        try:
            results['pysr'] = pysr_regression(I_numerical, sample_states, niterations=50)
        except Exception as e:
            print(f"PySR failed: {e}")

    return results


# Example usage
if __name__ == "__main__":
    print("Symbolic Regression Pipeline - Example")

    # Create synthetic conserved quantity: I = z0^2 + z1^2 + 0.5*z2
    def true_integral(z):
        return z[0]**2 + z[1]**2 + 0.5 * z[2]

    # Generate sample data
    state_dim = 4
    N_samples = 500
    samples = np.random.randn(N_samples, state_dim)

    # Test SINDy
    if PYSINDY_AVAILABLE:
        print("\n=== Testing SINDy ===")
        library = construct_hierarchical_basis(
            state_dim=state_dim,
            max_polynomial_degree=2,
            masses=np.array([1., 1., 1.])
        )

        result_sindy = sindy_regression(true_integral, samples, library, threshold=0.01)
        print(f"Expression: {result_sindy.expression_str}")
        print(f"Residual: {result_sindy.residual:.2e}")
        print(f"Complexity: {result_sindy.complexity}")
        print(f"Active functions: {result_sindy.basis_functions_used}")
    else:
        print("\nSINDy not available - install with: pip install pysindy")

    # Test PySR
    if PYSR_AVAILABLE:
        print("\n=== Testing PySR ===")
        result_pysr = pysr_regression(true_integral, samples, niterations=20)
        print(f"Expression: {result_pysr.expression_str}")
        print(f"Residual: {result_pysr.residual:.2e}")
        print(f"Complexity: {result_pysr.complexity}")
    else:
        print("\nPySR not available - install with: pip install pysr")
