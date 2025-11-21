"""
Physical interpretability and function type classification (AMENDED WP3.3).

This module provides tools for understanding and categorizing discovered integrals:
1. Function type classification (9 categories)
2. Physical interpretation heuristics
3. Complexity scoring for different function types
4. Interpretability metrics

These tools help prioritize candidates that are physically meaningful and
mathematically tractable for validation.

References:
- AMENDED_Task-3.3.3-Implementation-Plan.md
- AMENDED_WP3.3-Symbolic-Regression-Summary.md
"""

import numpy as np
import sympy as sp
from typing import Tuple, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class FunctionType(Enum):
    """
    Classification of integral function types.

    Categories ordered roughly by interpretability and validation difficulty:
    1. POLYNOMIAL: Standard polynomial expressions (easiest)
    2. RATIONAL: Ratios of polynomials
    3. RADICAL: Square roots and other radicals
    4. TRIGONOMETRIC: Sin/cos/tan functions
    5. EXPONENTIAL: Exponential/logarithm functions
    6. SPINOR: Spinor/quaternion-based (KS coordinates)
    7. ELLIPTIC: Elliptic functions (Jacobi, Weierstrass)
    8. THETA: Theta functions (doubly periodic)
    9. MIXED: Mixed or unclassified complex expressions
    """
    POLYNOMIAL = "polynomial"
    RATIONAL = "rational"
    RADICAL = "radical"
    TRIGONOMETRIC = "trigonometric"
    EXPONENTIAL = "exponential"
    SPINOR = "spinor_quaternion"
    ELLIPTIC = "elliptic"
    THETA = "theta"
    MIXED = "mixed_complex"


@dataclass
class InterpretabilityScore:
    """
    Interpretability scoring for a candidate integral.

    Attributes:
        function_type: Primary function type classification
        interpretability: Score 0-1 (1 = most interpretable)
        validation_difficulty: Score 0-1 (0 = easiest to validate)
        physical_meaning: Suggested physical interpretation
        contains_radicals: True if expression has square roots
        contains_transcendentals: True if has sin/cos/exp/log
        contains_special_functions: True if has elliptic/theta
        max_polynomial_degree: Maximum polynomial degree
        has_physical_symmetry: True if has recognizable symmetry
        physical_hints: List of physical interpretation hints
    """
    function_type: FunctionType
    interpretability: float
    validation_difficulty: float
    physical_meaning: str
    contains_radicals: bool
    contains_transcendentals: bool
    contains_special_functions: bool
    max_polynomial_degree: int
    has_physical_symmetry: bool
    physical_hints: List[str]


def classify_function_type(expr: sp.Expr) -> FunctionType:
    """
    Classify the primary function type of a symbolic expression.

    Args:
        expr: SymPy expression

    Returns:
        function_type: Classified FunctionType

    Example:
        >>> expr = sp.sympify("x**2 + y**2")
        >>> classify_function_type(expr)
        <FunctionType.POLYNOMIAL: 'polynomial'>

        >>> expr = sp.sympify("jacobi_sn(x, 0.5)")
        >>> classify_function_type(expr)
        <FunctionType.ELLIPTIC: 'elliptic'>
    """
    # Convert to string for pattern matching
    expr_str = str(expr)

    # Check for theta functions (highest priority)
    theta_patterns = ['jacobi_theta', 'theta1', 'theta2', 'theta3', 'theta4']
    if any(pattern in expr_str for pattern in theta_patterns):
        return FunctionType.THETA

    # Check for elliptic functions
    elliptic_patterns = [
        'jacobi_sn', 'jacobi_cn', 'jacobi_dn',
        'weierstrass_p', 'elliptic_k', 'elliptic_e'
    ]
    if any(pattern in expr_str for pattern in elliptic_patterns):
        return FunctionType.ELLIPTIC

    # Check for spinor/quaternion indicators
    # Look for patterns like u0, u1, u2, u3 or spinor_* functions
    spinor_patterns = ['spinor', 'quaternion', 'u0_', 'u1_', 'u2_', 'u3_']
    if any(pattern in expr_str for pattern in spinor_patterns):
        return FunctionType.SPINOR

    # Use SymPy atom analysis for other types
    atoms = expr.atoms(sp.Function, sp.Pow)

    # Check for exponential/logarithm
    has_exp = any(isinstance(atom, (sp.exp, sp.log, sp.log10)) for atom in atoms)
    has_exp_str = 'exp' in expr_str or 'log' in expr_str
    if has_exp or has_exp_str:
        return FunctionType.EXPONENTIAL

    # Check for trigonometric
    has_trig = any(isinstance(atom, (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc))
                   for atom in atoms)
    trig_patterns = ['sin', 'cos', 'tan']
    has_trig_str = any(pattern in expr_str for pattern in trig_patterns)
    if has_trig or has_trig_str:
        return FunctionType.TRIGONOMETRIC

    # Check for radicals (square roots, cube roots, etc.)
    has_radical = False
    for atom in atoms:
        if isinstance(atom, sp.Pow):
            # Check if exponent is a fraction
            exp = atom.exp
            if exp.is_Rational and exp.q != 1:  # Fractional exponent
                has_radical = True
                break

    if has_radical or 'sqrt' in expr_str:
        return FunctionType.RADICAL

    # Check for rational (ratio of polynomials)
    if expr.is_rational_function():
        numer, denom = expr.as_numer_denom()
        if denom != 1:
            return FunctionType.RATIONAL

    # Check if polynomial
    free_symbols = expr.free_symbols
    if expr.is_polynomial(*free_symbols):
        return FunctionType.POLYNOMIAL

    # Default: mixed/complex
    return FunctionType.MIXED


def compute_interpretability_score(expr: sp.Expr) -> InterpretabilityScore:
    """
    Compute comprehensive interpretability score for an expression.

    Args:
        expr: SymPy expression

    Returns:
        score: InterpretabilityScore object

    Example:
        >>> expr = sp.sympify("p_x**2 + p_y**2 + x**2 + y**2")
        >>> score = compute_interpretability_score(expr)
        >>> print(f"Type: {score.function_type}")
        >>> print(f"Interpretability: {score.interpretability:.2f}")
        >>> print(f"Physical meaning: {score.physical_meaning}")
    """
    # Classify function type
    func_type = classify_function_type(expr)

    # Check for various function categories
    expr_str = str(expr)
    atoms = expr.atoms(sp.Function, sp.Pow)

    contains_radicals = any(
        isinstance(atom, sp.Pow) and atom.exp.is_Rational and atom.exp.q != 1
        for atom in atoms
    ) or 'sqrt' in expr_str

    contains_transcendentals = any(
        'sin' in expr_str or 'cos' in expr_str or
        'exp' in expr_str or 'log' in expr_str
    )

    contains_special_functions = any([
        'jacobi' in expr_str,
        'weierstrass' in expr_str,
        'theta' in expr_str,
        'elliptic' in expr_str
    ])

    # Compute max polynomial degree
    free_symbols = expr.free_symbols
    max_degree = 0
    if free_symbols:
        try:
            if expr.is_polynomial(*free_symbols):
                max_degree = sp.degree(expr, gen=list(free_symbols)[0])
        except:
            max_degree = 0

    # Detect physical symmetries
    has_symmetry, symmetry_hints = detect_physical_symmetries(expr)

    # Generate physical hints
    physical_hints = generate_physical_hints(expr, func_type)
    physical_hints.extend(symmetry_hints)

    # Interpretability scoring (0-1, higher is more interpretable)
    interpretability = _compute_interpretability_value(
        func_type,
        contains_special_functions,
        max_degree
    )

    # Validation difficulty (0-1, higher is more difficult)
    validation_difficulty = _compute_validation_difficulty(
        func_type,
        contains_special_functions,
        max_degree
    )

    # Physical meaning suggestion
    physical_meaning = _suggest_physical_meaning(expr, func_type, physical_hints)

    return InterpretabilityScore(
        function_type=func_type,
        interpretability=interpretability,
        validation_difficulty=validation_difficulty,
        physical_meaning=physical_meaning,
        contains_radicals=contains_radicals,
        contains_transcendentals=contains_transcendentals,
        contains_special_functions=contains_special_functions,
        max_polynomial_degree=max_degree,
        has_physical_symmetry=has_symmetry,
        physical_hints=physical_hints
    )


def detect_physical_symmetries(expr: sp.Expr) -> Tuple[bool, List[str]]:
    """
    Detect recognizable physical symmetries in expression.

    Args:
        expr: SymPy expression

    Returns:
        has_symmetry: True if recognizable symmetry found
        hints: List of symmetry descriptions

    Example:
        >>> expr = sp.sympify("x**2 + y**2 + z**2")
        >>> has_sym, hints = detect_physical_symmetries(expr)
        >>> print(hints)
        ['Spherically symmetric (r²)']
    """
    hints = []
    expr_str = str(expr)

    # Rotational symmetry indicators
    # Pattern: x^2 + y^2 or x^2 + y^2 + z^2 (spherical)
    symbols_dict = {str(s): s for s in expr.free_symbols}

    # Check for spherical symmetry (x² + y² + z²)
    if ('x' in symbols_dict and 'y' in symbols_dict and 'z' in symbols_dict):
        x, y, z = symbols_dict['x'], symbols_dict['y'], symbols_dict['z']
        r_squared = x**2 + y**2 + z**2
        if expr.has(r_squared) or expr == r_squared:
            hints.append("Spherically symmetric (r²)")

    # Check for cylindrical symmetry (x² + y²)
    if 'x' in symbols_dict and 'y' in symbols_dict:
        x, y = symbols_dict['x'], symbols_dict['y']
        rho_squared = x**2 + y**2
        if expr.has(rho_squared) or expr == rho_squared:
            hints.append("Cylindrically symmetric (ρ²)")

    # Angular momentum indicators
    # Pattern: x*p_y - y*p_x (z-component of L)
    angular_momentum_patterns = [
        ('x', 'p_y', 'y', 'p_x'),  # L_z
        ('y', 'p_z', 'z', 'p_y'),  # L_x
        ('z', 'p_x', 'x', 'p_z'),  # L_y
    ]

    for q1, p2, q2, p1 in angular_momentum_patterns:
        if all(s in symbols_dict for s in [q1, p2, q2, p1]):
            L_component = symbols_dict[q1] * symbols_dict[p2] - symbols_dict[q2] * symbols_dict[p1]
            if expr.has(L_component) or expr == L_component:
                hints.append(f"Angular momentum component")
                break

    # Energy-like patterns (kinetic + potential)
    # Pattern: p_x^2 + p_y^2 + ... (kinetic energy)
    momentum_symbols = [s for s in symbols_dict.keys() if s.startswith('p_') or s.startswith('p')]
    if len(momentum_symbols) >= 2:
        kinetic_terms = sum(symbols_dict[p]**2 for p in momentum_symbols)
        if expr.has(kinetic_terms):
            hints.append("Contains kinetic energy term")

    # Position-dependent potential patterns
    position_symbols = [s for s in symbols_dict.keys() if s.startswith('q_') or s.startswith('x')]
    if len(position_symbols) >= 1:
        has_potential = any(symbols_dict[q]**n in expr.atoms()
                           for q in position_symbols for n in [1, 2, 3, 4])
        if has_potential:
            hints.append("Contains position-dependent potential term")

    # Conservation patterns (fiber/action variables)
    if 'theta' in expr_str and 'p_theta' in expr_str:
        hints.append("Fiber momentum (cyclic coordinate)")

    has_symmetry = len(hints) > 0
    return has_symmetry, hints


def generate_physical_hints(expr: sp.Expr, func_type: FunctionType) -> List[str]:
    """
    Generate physical interpretation hints based on function type.

    Args:
        expr: SymPy expression
        func_type: Classified function type

    Returns:
        hints: List of interpretation hints
    """
    hints = []

    if func_type == FunctionType.POLYNOMIAL:
        hints.append("Polynomial conserved quantity (standard form)")
        hints.append("Likely algebraic integral or combination of E, L")

    elif func_type == FunctionType.RATIONAL:
        hints.append("Rational function (may indicate scaled coordinate)")
        hints.append("Could represent normalized quantity or ratio of integrals")

    elif func_type == FunctionType.RADICAL:
        hints.append("Contains radicals (may involve distances or speeds)")
        hints.append("Check for |r|, |v|, or orbital elements")

    elif func_type == FunctionType.TRIGONOMETRIC:
        hints.append("Trigonometric function (periodic/angular structure)")
        hints.append("May represent angle variables or phase relationships")

    elif func_type == FunctionType.EXPONENTIAL:
        hints.append("Exponential function (unusual for conservative systems)")
        hints.append("Verify this is not a numerical artifact")

    elif func_type == FunctionType.SPINOR:
        hints.append("Spinor/quaternion-based (KS regularization)")
        hints.append("Related to regularized coordinates u₀, u₁, u₂, u₃")
        hints.append("May encode hidden symmetries not visible in Cartesian coords")

    elif func_type == FunctionType.ELLIPTIC:
        hints.append("Elliptic function (integrable system indicator)")
        hints.append("Jacobi functions sn/cn/dn or Weierstrass ℘")
        hints.append("Indicates quasi-periodic motion with two time scales")
        hints.append("CRITICAL: High-value discovery if genuine")

    elif func_type == FunctionType.THETA:
        hints.append("Theta function (doubly periodic)")
        hints.append("θ₁, θ₂, θ₃, or θ₄ Jacobi theta functions")
        hints.append("Strongest indication of complete integrability")
        hints.append("EXCEPTIONAL: Verify rigorously - potential breakthrough")

    elif func_type == FunctionType.MIXED:
        hints.append("Complex mixed expression")
        hints.append("May require further simplification")
        hints.append("Check if this reduces to simpler form")

    return hints


def _compute_interpretability_value(
    func_type: FunctionType,
    has_special_functions: bool,
    max_degree: int
) -> float:
    """
    Compute interpretability score (0-1, higher is better).

    Scoring:
    - Polynomial (low degree): 1.0 (most interpretable)
    - Rational: 0.85
    - Radical: 0.80
    - Trigonometric: 0.75
    - Spinor: 0.60 (physically meaningful but complex)
    - Elliptic: 0.50 (high value but harder to interpret)
    - Exponential: 0.40
    - Theta: 0.45 (very complex but high value)
    - Mixed: 0.30
    """
    base_scores = {
        FunctionType.POLYNOMIAL: 1.0,
        FunctionType.RATIONAL: 0.85,
        FunctionType.RADICAL: 0.80,
        FunctionType.TRIGONOMETRIC: 0.75,
        FunctionType.SPINOR: 0.60,
        FunctionType.ELLIPTIC: 0.50,
        FunctionType.EXPONENTIAL: 0.40,
        FunctionType.THETA: 0.45,
        FunctionType.MIXED: 0.30
    }

    score = base_scores[func_type]

    # Penalty for high polynomial degree
    if func_type == FunctionType.POLYNOMIAL and max_degree > 4:
        score *= (4.0 / max_degree)**0.5

    return max(0.0, min(1.0, score))


def _compute_validation_difficulty(
    func_type: FunctionType,
    has_special_functions: bool,
    max_degree: int
) -> float:
    """
    Compute validation difficulty score (0-1, higher is harder).

    Scoring:
    - Polynomial (low degree): 0.1 (easiest)
    - Rational: 0.2
    - Radical: 0.3
    - Trigonometric: 0.4
    - Exponential: 0.5
    - Spinor: 0.6 (requires KS framework)
    - Elliptic: 0.8 (requires specialized validation)
    - Theta: 0.9 (hardest - requires advanced theory)
    - Mixed: 0.7
    """
    base_difficulties = {
        FunctionType.POLYNOMIAL: 0.1,
        FunctionType.RATIONAL: 0.2,
        FunctionType.RADICAL: 0.3,
        FunctionType.TRIGONOMETRIC: 0.4,
        FunctionType.EXPONENTIAL: 0.5,
        FunctionType.SPINOR: 0.6,
        FunctionType.MIXED: 0.7,
        FunctionType.ELLIPTIC: 0.8,
        FunctionType.THETA: 0.9
    }

    difficulty = base_difficulties[func_type]

    # Increase difficulty for high polynomial degree
    if func_type == FunctionType.POLYNOMIAL and max_degree > 4:
        difficulty += 0.1 * (max_degree - 4)

    return max(0.0, min(1.0, difficulty))


def _suggest_physical_meaning(
    expr: sp.Expr,
    func_type: FunctionType,
    hints: List[str]
) -> str:
    """
    Suggest primary physical meaning based on expression analysis.

    Args:
        expr: SymPy expression
        func_type: Classified type
        hints: Accumulated hints

    Returns:
        meaning: Suggested physical interpretation
    """
    # Check hints for specific patterns
    if any('Angular momentum' in h for h in hints):
        return "Angular momentum component"

    if any('kinetic energy' in h for h in hints):
        if any('potential' in h for h in hints):
            return "Total energy or energy-like integral"
        else:
            return "Kinetic energy or momentum-related quantity"

    if any('Fiber momentum' in h for h in hints):
        return "Fiber momentum (cyclic coordinate integral)"

    if any('Spherically symmetric' in h for h in hints):
        return "Rotationally invariant quantity"

    # Type-specific defaults
    if func_type == FunctionType.POLYNOMIAL:
        return "Polynomial conserved quantity (algebraic integral)"
    elif func_type == FunctionType.SPINOR:
        return "Spinor-based integral (KS regularized coordinate)"
    elif func_type == FunctionType.ELLIPTIC:
        return "Elliptic integral (indicates integrability)"
    elif func_type == FunctionType.THETA:
        return "Theta function integral (complete integrability indicator)"
    else:
        return "Unknown physical interpretation"


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Interpretability Module - Tests")
    print("=" * 70)

    # Test 1: Polynomial (energy-like)
    print("\nTest 1: Polynomial expression")
    print("-" * 70)
    p_x, p_y, x, y = sp.symbols('p_x p_y x y')
    expr1 = p_x**2 + p_y**2 + x**2 + y**2

    score1 = compute_interpretability_score(expr1)
    print(f"Expression: {expr1}")
    print(f"Function type: {score1.function_type.value}")
    print(f"Interpretability: {score1.interpretability:.2f}")
    print(f"Validation difficulty: {score1.validation_difficulty:.2f}")
    print(f"Physical meaning: {score1.physical_meaning}")
    print(f"Hints: {score1.physical_hints}")

    # Test 2: Angular momentum
    print("\nTest 2: Angular momentum")
    print("-" * 70)
    expr2 = x * p_y - y * p_x

    score2 = compute_interpretability_score(expr2)
    print(f"Expression: {expr2}")
    print(f"Function type: {score2.function_type.value}")
    print(f"Physical meaning: {score2.physical_meaning}")
    print(f"Hints: {score2.physical_hints}")

    # Test 3: Radical (distance)
    print("\nTest 3: Radical expression")
    print("-" * 70)
    expr3 = sp.sqrt(x**2 + y**2)

    score3 = compute_interpretability_score(expr3)
    print(f"Expression: {expr3}")
    print(f"Function type: {score3.function_type.value}")
    print(f"Contains radicals: {score3.contains_radicals}")
    print(f"Interpretability: {score3.interpretability:.2f}")

    # Test 4: Elliptic function
    print("\nTest 4: Elliptic function")
    print("-" * 70)
    k = sp.Symbol('k')
    u = sp.Symbol('u')
    # Create a mock elliptic expression (SymPy doesn't have built-in Jacobi functions easily)
    expr4_str = "jacobi_sn(u, k)"
    expr4 = sp.Function('jacobi_sn')(u, k)

    score4 = compute_interpretability_score(expr4)
    print(f"Expression: {expr4}")
    print(f"Function type: {score4.function_type.value}")
    print(f"Contains special functions: {score4.contains_special_functions}")
    print(f"Interpretability: {score4.interpretability:.2f}")
    print(f"Validation difficulty: {score4.validation_difficulty:.2f}")
    print(f"Physical meaning: {score4.physical_meaning}")
    print(f"Hints:")
    for hint in score4.physical_hints:
        print(f"  - {hint}")

    # Test 5: Spinor basis function
    print("\nTest 5: Spinor/quaternion expression")
    print("-" * 70)
    u0, u1, u2, u3 = sp.symbols('u0_1 u1_1 u2_1 u3_1')
    expr5 = u0**2 + u1**2 + u2**2 + u3**2

    score5 = compute_interpretability_score(expr5)
    print(f"Expression: {expr5}")
    print(f"Function type: {score5.function_type.value}")
    print(f"Physical meaning: {score5.physical_meaning}")
    print(f"Validation difficulty: {score5.validation_difficulty:.2f}")

    print("\n" + "=" * 70)
    print("All tests complete")
    print("=" * 70)
