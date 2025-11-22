"""
Specialized symbolic regression for spinor-based integrals (AMENDED WP3.3).

This module provides targeted search methods for discovering integrals
expressed in Kustaanheimo-Stiefel (KS) regularized coordinates.

Spinor-based integrals may reveal hidden SO(4) symmetries not visible
in Cartesian coordinates. This is particularly relevant for the three-body
problem with close encounters where KS regularization removes singularities.

Use this module when:
- Close encounters or collisions occur
- Standard Cartesian regression fails
- Seeking integrals related to regularization symmetries

References:
- AMENDED_Task-3.3.1-Implementation-Plan.md
- Kustaanheimo & Stiefel (1965), "Perturbation theory of Kepler motion"
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass

from .spinor_basis import (
    construct_spinor_basis,
    position_to_spinor,
    compute_spinor_norm,
    quaternion_product
)
from .validation import validate_candidate_integral, ValidationResult


@dataclass
class SpinorSearchResult:
    """
    Result from spinor-based integral search.

    Attributes:
        found_spinor_integral: True if spinor form discovered
        best_expression: Best symbolic expression
        best_function: Best numerical function
        validation: ValidationResult
        search_method: Method that found the result
        spinor_component_type: Type of spinor combination (norm/product/etc)
    """
    found_spinor_integral: bool
    best_expression: Optional[sp.Expr]
    best_function: Optional[Callable]
    validation: Optional[ValidationResult]
    search_method: str
    spinor_component_type: str


def detect_regularization_benefit(
    trajectory: np.ndarray,
    masses: np.ndarray
) -> Tuple[bool, float]:
    """
    Detect if KS regularization would benefit this trajectory.

    Indicators:
        1. Close encounters (small inter-body distances)
        2. Large velocity variations
        3. Near-collision events

    Args:
        trajectory: Cartesian trajectory (N, dim)
        masses: Body masses

    Returns:
        needs_regularization: True if regularization beneficial
        close_encounter_fraction: Fraction of trajectory with close encounters
    """
    n_bodies = len(masses)
    dim = 3
    n_samples = len(trajectory)

    # Extract positions
    close_encounter_count = 0
    close_threshold = 0.1  # Threshold for "close" approach

    for state in trajectory:
        # Extract positions
        positions = []
        for i in range(n_bodies):
            r_i = state[i*dim:(i+1)*dim]
            positions.append(r_i)

        # Check all pairwise distances
        for i in range(n_bodies):
            for j in range(i+1, n_bodies):
                r_ij = positions[i] - positions[j]
                dist = np.linalg.norm(r_ij)

                if dist < close_threshold:
                    close_encounter_count += 1
                    break  # Count each timestep at most once

    close_encounter_fraction = close_encounter_count / n_samples

    needs_regularization = close_encounter_fraction > 0.05  # More than 5% close

    return needs_regularization, close_encounter_fraction


def spinor_pattern_recognition(
    I_numerical: Callable,
    trajectory: np.ndarray,
    masses: np.ndarray
) -> Optional[Tuple[str, float]]:
    """
    Recognize if integral matches common spinor patterns.

    Common patterns:
        1. Spinor norm: I = |u_i|² (equivalent to |r_i|)
        2. Spinor sum: I = Σ |u_i|²
        3. Spinor inner product: I = u_i · u_j
        4. Spinor bilinear: I = (u_i · u_j)(u_k · u_l)
        5. Quaternion product component: I = (u_i * u_j)_k

    Args:
        I_numerical: Candidate integral
        trajectory: Trajectory data
        masses: Body masses

    Returns:
        (pattern_type, match_quality) if pattern found, else None
    """
    n_bodies = len(masses)
    dim = 3

    # Test pattern 1: |u_1|²
    for i in range(n_bodies):
        def make_norm_pattern(body_idx):
            def pattern(state):
                r = state[body_idx*dim:(body_idx+1)*dim]
                u = position_to_spinor(r)
                return compute_spinor_norm(u)**2
            return pattern

        pattern_func = make_norm_pattern(i)

        # Evaluate on trajectory sample
        errors = []
        for state in trajectory[::50]:  # Sample
            predicted = pattern_func(state)
            actual = I_numerical(state)
            errors.append((predicted - actual)**2)

        rmse = np.sqrt(np.mean(errors))
        if rmse < 0.01:
            return (f"spinor_norm_body_{i+1}", 1.0 - rmse)

    # Test pattern 2: Σ |u_i|²
    def sum_norms_pattern(state):
        total = 0.0
        for i in range(n_bodies):
            r = state[i*dim:(i+1)*dim]
            u = position_to_spinor(r)
            total += compute_spinor_norm(u)**2
        return total

    errors = []
    for state in trajectory[::50]:
        predicted = sum_norms_pattern(state)
        actual = I_numerical(state)
        errors.append((predicted - actual)**2)

    rmse = np.sqrt(np.mean(errors))
    if rmse < 0.01:
        return ("spinor_sum_norms", 1.0 - rmse)

    # Test pattern 3: u_i · u_j (inner product)
    for i in range(n_bodies):
        for j in range(i+1, n_bodies):
            def make_inner_product_pattern(bi, bj):
                def pattern(state):
                    ri = state[bi*dim:(bi+1)*dim]
                    rj = state[bj*dim:(bj+1)*dim]
                    ui = position_to_spinor(ri)
                    uj = position_to_spinor(rj)
                    return np.dot(ui, uj)
                return pattern

            pattern_func = make_inner_product_pattern(i, j)

            errors = []
            for state in trajectory[::50]:
                predicted = pattern_func(state)
                actual = I_numerical(state)
                errors.append((predicted - actual)**2)

            rmse = np.sqrt(np.mean(errors))
            if rmse < 0.01:
                return (f"spinor_inner_product_{i+1}_{j+1}", 1.0 - rmse)

    return None


def spinor_sindy_search(
    I_numerical: Callable,
    trajectory: np.ndarray,
    masses: np.ndarray,
    threshold: float = 0.01
) -> Optional[Tuple[sp.Expr, float, List[str]]]:
    """
    SINDy-style sparse regression on spinor basis.

    Args:
        I_numerical: Candidate integral
        trajectory: Trajectory data
        masses: Body masses
        threshold: Sparsity threshold

    Returns:
        (expression, residual, active_terms) if successful, else None
    """
    # Build spinor basis
    spinor_basis = construct_spinor_basis(
        masses=masses,
        max_degree=2,
        include_quaternion_products=True
    )

    # Limit to first 50 functions to avoid combinatorial explosion
    spinor_basis = spinor_basis[:50]

    # Evaluate basis library
    sample_states = trajectory[::20]  # Subsample
    n_samples = len(sample_states)
    n_funcs = len(spinor_basis)

    Theta = np.zeros((n_samples, n_funcs))
    for i, state in enumerate(sample_states):
        for j, (func, desc) in enumerate(spinor_basis):
            try:
                Theta[i, j] = func(state)
            except:
                Theta[i, j] = 0.0

    # Check for NaN/inf
    if np.any(~np.isfinite(Theta)):
        return None

    # Target values
    b = np.array([I_numerical(state) for state in sample_states])

    if np.any(~np.isfinite(b)):
        return None

    # Sparse regression
    from sklearn.linear_model import Lasso

    lasso = Lasso(alpha=threshold, max_iter=10000, fit_intercept=False)
    lasso.fit(Theta, b)

    coeffs = lasso.coef_
    residual = np.sqrt(np.mean((Theta @ coeffs - b)**2))

    # Extract non-zero terms
    nonzero_idx = np.where(np.abs(coeffs) > threshold)[0]

    if len(nonzero_idx) == 0 or residual > 0.1:
        return None

    # Build symbolic expression (simplified)
    expr = sp.S(0)
    active_terms = []

    for idx in nonzero_idx:
        coeff = coeffs[idx]
        func, desc = spinor_basis[idx]

        # Create symbolic term
        term_name = desc.replace(' ', '_').replace('(', '_').replace(')', '').replace(',', '_').replace('.', '_')
        term_symbol = sp.Symbol(term_name)
        expr += coeff * term_symbol
        active_terms.append(f"{coeff:.4f}·{desc}")

    return (expr, residual, active_terms)


def search_spinor_integral(
    I_numerical: Callable,
    trajectory: np.ndarray,
    masses: np.ndarray,
    state_symbols: Optional[List[sp.Symbol]] = None
) -> SpinorSearchResult:
    """
    Main spinor integral search function.

    Pipeline:
        1. Check if regularization would be beneficial
        2. Try pattern recognition
        3. Try spinor SINDy search
        4. Validate best candidate

    Args:
        I_numerical: Candidate conserved quantity
        trajectory: Phase space trajectory (Cartesian coordinates)
        masses: Body masses
        state_symbols: SymPy symbols for state variables

    Returns:
        result: SpinorSearchResult with findings

    Example:
        >>> result = search_spinor_integral(my_integral, traj, masses)
        >>> if result.found_spinor_integral:
        ...     print(f"Spinor integral found: {result.best_expression}")
        ...     print(f"Type: {result.spinor_component_type}")
    """
    # Step 1: Check if regularization beneficial
    needs_reg, close_frac = detect_regularization_benefit(trajectory, masses)

    if needs_reg:
        print(f"  ✓ Regularization beneficial (close encounters: {close_frac:.1%})")
    else:
        print(f"  ℹ Regularization not critical (close encounters: {close_frac:.1%})")

    # Step 2: Pattern recognition
    print("  Attempting spinor pattern recognition...")
    pattern_result = spinor_pattern_recognition(I_numerical, trajectory, masses)

    if pattern_result is not None:
        pattern_type, quality = pattern_result
        print(f"  ✓ Pattern match found: {pattern_type} (quality: {quality:.4f})")

        # Build symbolic expression based on pattern type
        if "spinor_norm_body" in pattern_type:
            body_idx = int(pattern_type.split('_')[-1])
            u = sp.symbols(f'u_{{0,{body_idx}}} u_{{1,{body_idx}}} u_{{2,{body_idx}}} u_{{3,{body_idx}}}')
            expr = sum(ui**2 for ui in u)

        elif pattern_type == "spinor_sum_norms":
            n_bodies = len(masses)
            expr = sp.S(0)
            for i in range(n_bodies):
                u = sp.symbols(f'u_{{0,{i+1}}} u_{{1,{i+1}}} u_{{2,{i+1}}} u_{{3,{i+1}}}')
                expr += sum(ui**2 for ui in u)

        elif "spinor_inner_product" in pattern_type:
            parts = pattern_type.split('_')
            i, j = int(parts[-2]), int(parts[-1])
            ui = sp.symbols(f'u_{{0,{i}}} u_{{1,{i}}} u_{{2,{i}}} u_{{3,{i}}}')
            uj = sp.symbols(f'u_{{0,{j}}} u_{{1,{j}}} u_{{2,{j}}} u_{{3,{j}}}')
            expr = sum(ui[k]*uj[k] for k in range(4))

        else:
            expr = sp.Symbol(pattern_type)

        # Validate
        if state_symbols is None:
            state_symbols = [sp.Symbol(f'z{i}') for i in range(len(trajectory[0]))]

        validation = validate_candidate_integral(
            expr, I_numerical, trajectory, state_symbols
        )

        return SpinorSearchResult(
            found_spinor_integral=True,
            best_expression=expr,
            best_function=I_numerical,
            validation=validation,
            search_method="pattern_recognition",
            spinor_component_type=pattern_type
        )

    # Step 3: Spinor SINDy search
    print("  Attempting spinor SINDy search...")
    sindy_result = spinor_sindy_search(I_numerical, trajectory, masses)

    if sindy_result is not None:
        expr, residual, active_terms = sindy_result
        print(f"  ✓ Spinor SINDy found candidate (residual: {residual:.2e})")
        print(f"    Active terms: {len(active_terms)}")
        for term in active_terms[:5]:
            print(f"      {term}")

        if state_symbols is None:
            state_symbols = [sp.Symbol(f'z{i}') for i in range(len(trajectory[0]))]

        validation = validate_candidate_integral(
            expr, I_numerical, trajectory, state_symbols
        )

        return SpinorSearchResult(
            found_spinor_integral=True,
            best_expression=expr,
            best_function=I_numerical,
            validation=validation,
            search_method="spinor_sindy",
            spinor_component_type="sparse_combination"
        )

    # No spinor form found
    print("  ✗ No spinor form discovered")

    return SpinorSearchResult(
        found_spinor_integral=False,
        best_expression=None,
        best_function=None,
        validation=None,
        search_method="none",
        spinor_component_type="unknown"
    )


# Example usage
if __name__ == "__main__":
    print("Spinor Search Module - Example")
    print("=" * 70)

    # Create synthetic spinor integral: I = |u_1|²
    def synthetic_spinor_integral(state):
        """Mock spinor integral: I = |u_1|²"""
        r1 = state[:3]
        u1 = position_to_spinor(r1)
        return compute_spinor_norm(u1)**2

    # Generate synthetic trajectory
    trajectory = np.random.randn(1000, 18)  # 3 bodies
    masses = np.array([1.0, 1.0, 1.0])

    # Run spinor search
    print("\nSearching for spinor structure...")
    print("-" * 70)

    result = search_spinor_integral(
        I_numerical=synthetic_spinor_integral,
        trajectory=trajectory,
        masses=masses
    )

    print("\nResults:")
    print(f"  Found spinor integral: {result.found_spinor_integral}")
    print(f"  Method: {result.search_method}")
    print(f"  Type: {result.spinor_component_type}")

    if result.best_expression:
        print(f"  Expression: {result.best_expression}")

    print("\n" + "=" * 70)
