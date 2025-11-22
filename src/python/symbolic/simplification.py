"""
Expression simplification and optimization for symbolic integrals (Task 3.3.1 support).

This module provides tools to simplify and optimize symbolic expressions
discovered through regression, making them more interpretable and suitable
for analytical validation.

Key operations:
- Algebraic simplification (SymPy)
- Numerical coefficient rounding
- Common factor extraction
- Trigonometric simplification
- Physical interpretation hints

The goal is to transform complex regression outputs into clean, publication-ready
analytical expressions.

References:
- SymPy documentation on simplification
- Meurer et al., "SymPy: symbolic computing in Python" (2017)
"""

import sympy as sp
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from fractions import Fraction


@dataclass
class SimplificationResult:
    """
    Result of expression simplification.

    Attributes:
        original: Original expression
        simplified: Simplified expression
        simplification_steps: List of intermediate steps
        reduction_factor: Ratio of complexities (simplified / original)
        numerical_equivalence: Whether expressions are numerically equivalent
    """
    original: sp.Expr
    simplified: sp.Expr
    simplification_steps: List[Tuple[str, sp.Expr]]
    reduction_factor: float
    numerical_equivalence: bool = True


def count_operations(expr: sp.Expr) -> int:
    """
    Count number of operations in an expression.

    Args:
        expr: SymPy expression

    Returns:
        n_ops: Number of operations (additions, multiplications, etc.)
    """
    return sp.count_ops(expr)


def round_coefficients(
    expr: sp.Expr,
    decimals: int = 6,
    try_rational: bool = True,
    rational_tolerance: float = 1e-6
) -> sp.Expr:
    """
    Round numerical coefficients in expression.

    Attempts to convert floats to exact rationals if close to simple fractions.

    Args:
        expr: SymPy expression with float coefficients
        decimals: Number of decimal places for rounding
        try_rational: Attempt to convert to rational numbers
        rational_tolerance: Tolerance for rational approximation

    Returns:
        rounded_expr: Expression with rounded coefficients

    Example:
        >>> x = sp.Symbol('x')
        >>> expr = 0.333333*x + 0.5*x**2
        >>> round_coefficients(expr, decimals=2, try_rational=True)
        x/3 + x**2/2
    """
    # Extract all float coefficients
    floats = [atom for atom in expr.atoms(sp.Float)]

    substitutions = {}
    for f in floats:
        val = float(f)

        if try_rational:
            # Try to find simple rational approximation
            frac = Fraction(val).limit_denominator(1000)
            if abs(frac - val) < rational_tolerance:
                substitutions[f] = sp.Rational(frac.numerator, frac.denominator)
            else:
                substitutions[f] = sp.Float(round(val, decimals))
        else:
            substitutions[f] = sp.Float(round(val, decimals))

    return expr.subs(substitutions)


def verify_numerical_equivalence(
    expr1: sp.Expr,
    expr2: sp.Expr,
    n_test_points: int = 1000,
    tolerance: float = 1e-10,
    domain_bounds: Tuple[float, float] = (-10.0, 10.0)
) -> Tuple[bool, float]:
    """
    Verify two expressions are numerically equivalent.

    Tests equivalence by evaluating at random points in the domain.

    Args:
        expr1: First expression
        expr2: Second expression
        n_test_points: Number of random test points
        tolerance: Relative error tolerance
        domain_bounds: (min, max) bounds for random sampling

    Returns:
        (is_equivalent, max_error): Whether equivalent and maximum relative error
    """
    # Get all free symbols
    symbols = list(expr1.free_symbols | expr2.free_symbols)

    if not symbols:
        # Constant expressions - compare directly
        try:
            val1 = float(expr1)
            val2 = float(expr2)
            error = abs(val1 - val2)
            return error < tolerance, error
        except:
            return False, float('inf')

    # Lambdify for fast numerical evaluation
    try:
        f1 = sp.lambdify(symbols, expr1, 'numpy')
        f2 = sp.lambdify(symbols, expr2, 'numpy')
    except:
        # Lambdification failed
        return False, float('inf')

    # Generate random test points
    low, high = domain_bounds
    errors = []

    for _ in range(n_test_points):
        # Random values for each symbol
        args = [np.random.uniform(low, high) for _ in symbols]

        try:
            val1 = f1(*args)
            val2 = f2(*args)

            # Handle complex numbers
            if np.iscomplexobj(val1) or np.iscomplexobj(val2):
                val1 = complex(val1)
                val2 = complex(val2)
                error = abs(val1 - val2)
            else:
                val1 = float(val1)
                val2 = float(val2)
                error = abs(val1 - val2)

            # Relative error
            if abs(val1) > tolerance:
                rel_error = error / abs(val1)
            else:
                rel_error = error

            errors.append(rel_error)

        except (ValueError, ZeroDivisionError, OverflowError, TypeError):
            # Skip problematic points
            continue

    if not errors:
        # No successful evaluations
        return False, float('inf')

    max_error = max(errors)
    is_equivalent = max_error < tolerance

    return is_equivalent, max_error


def simplify_expression(
    expr: sp.Expr,
    method: str = 'auto',
    rational_coeffs: bool = True,
    trig_simplify: bool = True,
    factor: bool = True,
    verify_numerically: bool = True
) -> SimplificationResult:
    """
    Apply comprehensive simplification to expression.

    Args:
        expr: SymPy expression to simplify
        method: Simplification strategy ('auto', 'aggressive', 'conservative')
        rational_coeffs: Try to convert floats to rationals
        trig_simplify: Apply trigonometric simplifications
        factor: Attempt factorization
        verify_numerically: Verify simplified expression is numerically equivalent

    Returns:
        result: SimplificationResult with steps and verification

    Example:
        >>> x, y = sp.symbols('x y')
        >>> expr = x**2 + 2*x*y + y**2
        >>> result = simplify_expression(expr, factor=True)
        >>> print(result.simplified)  # (x + y)**2
    """
    original = expr
    steps = [("Original", expr)]

    # Step 1: Round coefficients
    if rational_coeffs:
        expr = round_coefficients(expr)
        steps.append(("Round coefficients", expr))

    # Step 2: Basic algebraic simplification
    expr = sp.simplify(expr)
    steps.append(("Algebraic simplify", expr))

    # Step 3: Trigonometric simplification
    if trig_simplify:
        expr_trig = sp.trigsimp(expr)
        if count_operations(expr_trig) <= count_operations(expr):
            expr = expr_trig
            steps.append(("Trigonometric simplify", expr))

    # Step 4: Factorization
    if factor:
        try:
            expr_factored = sp.factor(expr)
            if count_operations(expr_factored) <= count_operations(expr):
                expr = expr_factored
                steps.append(("Factor", expr))
        except:
            pass  # Factorization can fail for some expressions

    # Step 5: Expand and re-collect if beneficial
    if method == 'aggressive':
        expr_expanded = sp.expand(expr)
        expr_collected = sp.collect(expr_expanded, expr.free_symbols)
        if count_operations(expr_collected) < count_operations(expr):
            expr = expr_collected
            steps.append(("Expand and collect", expr))

    # Step 6: Final simplify
    expr = sp.simplify(expr)
    steps.append(("Final simplify", expr))

    # Compute reduction factor
    orig_ops = count_operations(original)
    simp_ops = count_operations(expr)
    reduction = simp_ops / orig_ops if orig_ops > 0 else 1.0

    # Verify numerical equivalence
    if verify_numerically:
        is_equivalent, max_error = verify_numerical_equivalence(original, expr)
        if not is_equivalent:
            # Warn if simplification changed numerical behavior
            import warnings
            warnings.warn(
                f"Simplification may have changed numerical behavior. "
                f"Max error: {max_error:.2e}. Returning original expression.",
                UserWarning
            )
            # Return original if verification fails
            expr = original
            steps = [("Original", original), ("Verification failed - returning original", original)]
    else:
        is_equivalent = True

    return SimplificationResult(
        original=original,
        simplified=expr,
        simplification_steps=steps,
        reduction_factor=reduction,
        numerical_equivalence=is_equivalent
    )


def extract_common_factors(expr: sp.Expr) -> Tuple[sp.Expr, sp.Expr]:
    """
    Extract common factors from expression.

    Args:
        expr: Expression to factor

    Returns:
        factor: Common factor
        remainder: Remainder after factoring out

    Example:
        >>> x = sp.Symbol('x')
        >>> expr = 2*x**2 + 4*x
        >>> factor, remainder = extract_common_factors(expr)
        >>> # Returns: (2*x, x + 2)
    """
    factored = sp.factor(expr)

    # Try to identify common factor
    if factored.is_Mul:
        # Expression is a product
        factors = factored.as_ordered_factors()
        if len(factors) > 1:
            # First factor is typically the common one
            return factors[0], sp.Mul(*factors[1:])

    return sp.S.One, expr


def substitute_conserved_quantities(
    expr: sp.Expr,
    conserved_symbols: Dict[str, sp.Expr]
) -> sp.Expr:
    """
    Substitute known conserved quantities for readability.

    For example, replace combinations of momenta with 'E' or 'L'.

    Args:
        expr: Expression with phase space variables
        conserved_symbols: Dict mapping symbols to conserved quantity expressions
                          e.g., {'E': p0**2 + p1**2 + ..., 'L': ...}

    Returns:
        simplified_expr: Expression in terms of conserved quantities

    Example:
        >>> p0, p1 = sp.symbols('p0 p1')
        >>> expr = p0**2 + p1**2
        >>> E = sp.Symbol('E')
        >>> result = substitute_conserved_quantities(expr, {'E': p0**2 + p1**2})
        >>> # Returns: E
    """
    # Reverse the dictionary for substitution
    subs_dict = {v: sp.Symbol(k) for k, v in conserved_symbols.items()}

    # Try substitutions
    result = expr.subs(subs_dict)

    return sp.simplify(result)


def minimize_expression_tree(expr: sp.Expr, max_iterations: int = 10) -> sp.Expr:
    """
    Iteratively minimize expression complexity.

    Tries various simplification strategies and keeps the simplest result.

    Args:
        expr: Expression to minimize
        max_iterations: Maximum number of iterations

    Returns:
        minimal_expr: Expression with minimal operation count
    """
    current = expr
    current_ops = count_operations(current)

    for iteration in range(max_iterations):
        candidates = []

        # Try different simplification methods
        candidates.append(sp.simplify(current))
        candidates.append(sp.factor(current))
        candidates.append(sp.expand(current))
        candidates.append(sp.trigsimp(current))
        candidates.append(sp.powsimp(current))
        candidates.append(sp.radsimp(current))

        # Collect terms by each variable
        for var in current.free_symbols:
            candidates.append(sp.collect(current, var))

        # Find simplest candidate
        best = current
        best_ops = current_ops

        for candidate in candidates:
            ops = count_operations(candidate)
            if ops < best_ops:
                best = candidate
                best_ops = ops

        # Check if we made progress
        if best_ops >= current_ops:
            break  # No improvement, stop

        current = best
        current_ops = best_ops

    return current


def format_for_publication(
    expr: sp.Expr,
    variable_names: Optional[Dict[sp.Symbol, str]] = None
) -> str:
    """
    Format expression for publication (LaTeX).

    Args:
        expr: Expression to format
        variable_names: Optional mapping of symbols to desired names

    Returns:
        latex_str: LaTeX string representation

    Example:
        >>> x, y = sp.symbols('x y')
        >>> expr = x**2 + y**2
        >>> latex = format_for_publication(expr)
        >>> # Returns: "x^{2} + y^{2}"
    """
    if variable_names:
        expr = expr.subs(variable_names)

    return sp.latex(expr)


def verify_numerical_equivalence(
    expr1: sp.Expr,
    expr2: sp.Expr,
    n_test_points: int = 1000,
    tolerance: float = 1e-10
) -> Tuple[bool, float]:
    """
    Verify two expressions are numerically equivalent.

    Args:
        expr1: First expression
        expr2: Second expression
        n_test_points: Number of random test points
        tolerance: Numerical tolerance

    Returns:
        equivalent: True if expressions match within tolerance
        max_difference: Maximum absolute difference observed
    """
    # Get free symbols
    symbols = list(expr1.free_symbols | expr2.free_symbols)

    if len(symbols) == 0:
        # Constants
        val1 = float(expr1.evalf())
        val2 = float(expr2.evalf())
        return abs(val1 - val2) < tolerance, abs(val1 - val2)

    # Convert to numerical functions
    f1 = sp.lambdify(symbols, expr1, 'numpy')
    f2 = sp.lambdify(symbols, expr2, 'numpy')

    # Generate random test points
    max_diff = 0.0
    all_match = True

    for _ in range(n_test_points):
        values = np.random.randn(len(symbols))

        try:
            v1 = f1(*values)
            v2 = f2(*values)
            diff = abs(v1 - v2)

            max_diff = max(max_diff, diff)

            if diff > tolerance:
                all_match = False
        except:
            # Evaluation failed (division by zero, etc.)
            continue

    return all_match, max_diff


def simplify_candidate_integral(
    expr: sp.Expr,
    state_variables: List[sp.Symbol],
    known_conserved: Optional[Dict[str, sp.Expr]] = None,
    aggressive: bool = False
) -> SimplificationResult:
    """
    Comprehensive simplification pipeline for candidate integrals.

    This is the main entry point for simplifying discovered integrals.

    Args:
        expr: Candidate integral expression
        state_variables: List of phase space variable symbols
        known_conserved: Known conserved quantities (E, L, etc.)
        aggressive: Use aggressive simplification strategies

    Returns:
        result: SimplificationResult with simplified expression

    Example:
        >>> from sympy.abc import x, y, z
        >>> expr = x**2 + 2*x*y + y**2 + z
        >>> result = simplify_candidate_integral(expr, [x, y, z])
        >>> print(result.simplified)  # (x + y)**2 + z
    """
    method = 'aggressive' if aggressive else 'auto'

    # Step 1: Basic simplification
    result = simplify_expression(
        expr,
        method=method,
        rational_coeffs=True,
        trig_simplify=True,
        factor=True
    )

    # Step 2: Substitute known conserved quantities if provided
    if known_conserved:
        simplified = substitute_conserved_quantities(result.simplified, known_conserved)
        if count_operations(simplified) < count_operations(result.simplified):
            result.simplified = simplified
            result.simplification_steps.append(("Substitute conserved", simplified))

    # Step 3: Minimize expression tree
    minimal = minimize_expression_tree(result.simplified)
    if count_operations(minimal) < count_operations(result.simplified):
        result.simplified = minimal
        result.simplification_steps.append(("Minimize tree", minimal))

    # Recompute reduction factor
    result.reduction_factor = (
        count_operations(result.simplified) / count_operations(result.original)
        if count_operations(result.original) > 0 else 1.0
    )

    # Verify numerical equivalence
    equivalent, max_diff = verify_numerical_equivalence(
        result.original,
        result.simplified,
        n_test_points=100
    )
    result.numerical_equivalence = equivalent

    return result


# Example usage
if __name__ == "__main__":
    print("Expression Simplification - Examples\n")

    # Example 1: Basic simplification
    x, y, z = sp.symbols('x y z')
    expr1 = x**2 + 2*x*y + y**2
    result1 = simplify_expression(expr1, factor=True)
    print("Example 1: Factorization")
    print(f"  Original:   {result1.original}")
    print(f"  Simplified: {result1.simplified}")
    print(f"  Reduction:  {result1.reduction_factor:.2f}\n")

    # Example 2: Coefficient rounding
    expr2 = 0.333333*x + 0.666667*y + 1.999999*z
    rounded = round_coefficients(expr2, try_rational=True)
    print("Example 2: Coefficient rounding")
    print(f"  Original: {expr2}")
    print(f"  Rounded:  {rounded}\n")

    # Example 3: Complex expression
    expr3 = sp.sin(x)**2 + sp.cos(x)**2 + x*y - y*x + 2*x + 4*x
    result3 = simplify_candidate_integral(expr3, [x, y])
    print("Example 3: Complex simplification")
    print(f"  Original:   {result3.original}")
    print(f"  Simplified: {result3.simplified}")
    print(f"  Steps:")
    for name, step_expr in result3.simplification_steps:
        print(f"    {name}: {step_expr}")
    print(f"  Equivalent: {result3.numerical_equivalence}\n")

    # Example 4: LaTeX formatting
    expr4 = (x + y)**2 / z
    latex = format_for_publication(expr4)
    print("Example 4: LaTeX formatting")
    print(f"  Expression: {expr4}")
    print(f"  LaTeX: {latex}\n")
