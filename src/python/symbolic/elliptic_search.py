"""
Specialized symbolic regression for elliptic functions (AMENDED WP3.3).

This module provides targeted search methods for discovering elliptic function
integrals. It extends standard symbolic regression with:
1. Elliptic parameter estimation
2. Pattern matching for Jacobi function forms
3. Hybrid SINDy+elliptic search
4. Validation of elliptic identities

Use this module when:
- Multi-scale validation indicates quasi-periodic structure
- Standard polynomial regression fails
- Two incommensurable frequencies detected

References:
- AMENDED_Task-3.3.1-Implementation-Plan.md
- AMENDED_WP3.3-Symbolic-Regression-Summary.md
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Optional, Callable, Dict
from dataclasses import dataclass

from .elliptic_basis import (
    construct_elliptic_basis,
    estimate_elliptic_parameter,
    jacobi_sn, jacobi_cn, jacobi_dn
)
from .regression_pipeline import sindy_regression
from .validation import validate_candidate_integral, ValidationResult


@dataclass
class EllipticSearchResult:
    """
    Result from elliptic function search.

    Attributes:
        found_elliptic: True if elliptic form discovered
        best_expression: Best symbolic expression
        best_function: Best numerical function
        elliptic_parameter: Estimated m value
        validation: ValidationResult
        search_method: Method that found the result
        confidence: Confidence score (0-1)
    """
    found_elliptic: bool
    best_expression: Optional[sp.Expr]
    best_function: Optional[Callable]
    elliptic_parameter: float
    validation: Optional[ValidationResult]
    search_method: str
    confidence: float


def detect_elliptic_signature(
    I_numerical: Callable,
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    threshold: float = 0.7
) -> Tuple[bool, float, List[float]]:
    """
    Detect if a candidate integral has elliptic function signature.

    Elliptic signature indicators:
        1. Quasi-periodic with 2 incommensurable frequencies
        2. Power spectrum shows two dominant peaks
        3. Amplitude modulation pattern
        4. Periodicity ratio ω₂/ω₁ is irrational

    Args:
        I_numerical: Candidate integral function
        trajectory: Phase space trajectory
        trajectory_times: Time points
        threshold: Confidence threshold

    Returns:
        has_signature: True if elliptic signature detected
        confidence: Confidence score (0-1)
        frequencies: [ω₁, ω₂] dominant frequencies
    """
    # Evaluate integral
    I_values = np.array([I_numerical(state) for state in trajectory])

    # Check for NaNs
    if np.any(np.isnan(I_values)):
        return False, 0.0, []

    # Remove mean and normalize
    I_values = I_values - np.mean(I_values)
    if np.std(I_values) < 1e-12:
        return False, 0.0, []  # Constant

    I_values = I_values / np.std(I_values)

    # FFT analysis
    fft = np.fft.rfft(I_values)
    freqs = np.fft.rfftfreq(len(I_values), d=np.mean(np.diff(trajectory_times)))
    power = np.abs(fft)**2

    # Find peaks
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(power, height=np.max(power)*0.05)

    if len(peaks) < 2:
        return False, 0.0, []

    # Get two strongest peaks
    sorted_peaks = peaks[np.argsort(power[peaks])[-2:]]
    omega1, omega2 = sorted(freqs[sorted_peaks])

    if omega1 < 1e-10:
        return False, 0.0, []

    # Check if frequencies are incommensurable
    ratio = omega2 / omega1

    # Check if ratio is close to rational with small denominator
    is_rational = False
    for p in range(1, 10):
        for q in range(1, 10):
            if np.abs(ratio - p/q) < 0.01:
                is_rational = True
                break
        if is_rational:
            break

    if is_rational:
        # Ratio is rational - not quasi-periodic
        return False, 0.3, [omega1, omega2]

    # Check power spectrum concentration
    total_power = np.sum(power)
    top2_power = np.sum(power[sorted_peaks])
    concentration = top2_power / total_power

    # Confidence based on:
    # 1. Frequency ratio is irrational
    # 2. Power concentrated in two peaks
    # 3. No other strong peaks

    confidence = concentration
    if concentration > threshold:
        return True, confidence, [omega1, omega2]
    else:
        return False, confidence, [omega1, omega2]


def elliptic_pattern_match(
    I_numerical: Callable,
    trajectory: np.ndarray,
    masses: np.ndarray,
    m_est: float
) -> Optional[Tuple[sp.Expr, Callable, float]]:
    """
    Try to match candidate integral to known elliptic patterns.

    Common patterns:
        1. Pure Jacobi: I = A·sn(B·|r|, m) + C
        2. Jacobi product: I = A·sn(|r₁|)·cn(|r₂|)
        3. Mixed: I = A·sn(|r|) + B·|r|²

    Args:
        I_numerical: Candidate integral
        trajectory: Trajectory data
        masses: Body masses
        m_est: Estimated elliptic parameter

    Returns:
        (expression, function, fit_quality) if match found, else None
    """
    n_bodies = len(masses)

    # Extract coordinates from first state to understand dimension
    sample_state = trajectory[0]
    dim_total = len(sample_state)

    # Try pattern 1: I ≈ A·sn(B·|r₁|, m) + C
    for i in range(n_bodies):
        # Build candidate function
        def make_sn_pattern(body_idx, m_val):
            def pattern(state, A, B, C):
                dim = 3
                n_bodies_local = dim_total // 6
                r = state[body_idx * dim : (body_idx + 1) * dim]
                r_mag = np.linalg.norm(r)
                return A * jacobi_sn(B * r_mag, m_val) + C
            return pattern

        pattern_func = make_sn_pattern(i, m_est)

        # Fit parameters A, B, C
        from scipy.optimize import minimize

        def objective(params):
            A, B, C = params
            errors = []
            for state in trajectory[::10]:  # Sample every 10th point
                predicted = pattern_func(state, A, B, C)
                actual = I_numerical(state)
                errors.append((predicted - actual)**2)
            return np.mean(errors)

        # Initial guess
        x0 = [1.0, 1.0, 0.0]
        bounds = [(-10, 10), (0.1, 10), (-10, 10)]

        try:
            result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
            if result.success and result.fun < 0.01:
                A_opt, B_opt, C_opt = result.x

                # Build symbolic expression
                r_i = sp.Symbol(f'r_{i+1}')
                m_sym = sp.Symbol('m')
                expr = A_opt * sp.Function('sn')(B_opt * r_i, m_sym) + C_opt

                # Build numerical function
                def fitted_func(state):
                    return pattern_func(state, A_opt, B_opt, C_opt)

                return (expr, fitted_func, 1.0 - result.fun)
        except:
            pass

    # Try pattern 2: I ≈ A·cn(|r₁|, m) + B
    for i in range(n_bodies):
        def make_cn_pattern(body_idx, m_val):
            def pattern(state, A, B):
                dim = 3
                n_bodies_local = dim_total // 6
                r = state[body_idx * dim : (body_idx + 1) * dim]
                r_mag = np.linalg.norm(r)
                return A * jacobi_cn(r_mag, m_val) + B
            return pattern

        pattern_func = make_cn_pattern(i, m_est)

        def objective(params):
            A, B = params
            errors = []
            for state in trajectory[::10]:
                predicted = pattern_func(state, A, B)
                actual = I_numerical(state)
                errors.append((predicted - actual)**2)
            return np.mean(errors)

        x0 = [1.0, 0.0]
        bounds = [(-10, 10), (-10, 10)]

        try:
            result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
            if result.success and result.fun < 0.01:
                A_opt, B_opt = result.x

                r_i = sp.Symbol(f'r_{i+1}')
                m_sym = sp.Symbol('m')
                expr = A_opt * sp.Function('cn')(r_i, m_sym) + B_opt

                def fitted_func(state):
                    return pattern_func(state, A_opt, B_opt)

                return (expr, fitted_func, 1.0 - result.fun)
        except:
            pass

    return None


def elliptic_sindy_hybrid(
    I_numerical: Callable,
    trajectory: np.ndarray,
    masses: np.ndarray,
    m_est: float,
    threshold: float = 0.01
) -> Optional[Tuple[sp.Expr, float]]:
    """
    Hybrid SINDy + elliptic basis search.

    Combines:
        1. Standard polynomial basis
        2. Elliptic function basis with estimated m
        3. Sparse regression to find coefficients

    Args:
        I_numerical: Candidate integral
        trajectory: Trajectory data
        masses: Body masses
        m_est: Estimated elliptic parameter
        threshold: Sparsity threshold

    Returns:
        (expression, residual) if successful, else None
    """
    # Build combined basis
    from .basis_functions import construct_hierarchical_basis

    # Standard basis (limited)
    standard_basis = construct_hierarchical_basis(
        masses=masses,
        max_polynomial_degree=2,
        include_transcendental=False
    )[:20]  # Limit to 20 functions

    # Elliptic basis
    elliptic_basis = construct_elliptic_basis(
        masses=masses,
        max_degree=1,
        m_values=[m_est]
    )[:20]  # Limit to 20 functions

    # Combine
    combined_basis = standard_basis + elliptic_basis

    # Evaluate basis library on trajectory
    sample_states = trajectory[::10]  # Subsample
    n_samples = len(sample_states)
    n_funcs = len(combined_basis)

    Theta = np.zeros((n_samples, n_funcs))
    for i, state in enumerate(sample_states):
        for j, (func, desc) in enumerate(combined_basis):
            try:
                Theta[i, j] = func(state)
            except:
                Theta[i, j] = 0.0

    # Target values
    b = np.array([I_numerical(state) for state in sample_states])

    # Sparse regression (LASSO)
    from sklearn.linear_model import Lasso

    lasso = Lasso(alpha=threshold, max_iter=10000, fit_intercept=False)
    lasso.fit(Theta, b)

    coeffs = lasso.coef_
    residual = np.mean((Theta @ coeffs - b)**2)**0.5

    # Extract non-zero terms
    nonzero_idx = np.where(np.abs(coeffs) > threshold)[0]

    if len(nonzero_idx) == 0:
        return None

    # Build symbolic expression
    state_symbols = sp.symbols(' '.join([f'z{i}' for i in range(len(sample_states[0]))]))

    expr = sp.S(0)
    for idx in nonzero_idx:
        coeff = coeffs[idx]
        func, desc = combined_basis[idx]

        # Create symbolic term (simplified representation)
        if 'sn' in desc or 'cn' in desc or 'dn' in desc:
            # Elliptic term - use description as placeholder
            term_symbol = sp.Symbol(desc.replace('(', '_').replace(')', '').replace(' ', '_').replace(',', '_').replace('.', '_').replace('=', ''))
            expr += coeff * term_symbol
        else:
            # Polynomial term - use generic symbol
            term_symbol = sp.Symbol(f'f_{idx}')
            expr += coeff * term_symbol

    return (expr, residual)


def search_elliptic_integral(
    I_numerical: Callable,
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    masses: np.ndarray,
    state_symbols: Optional[List[sp.Symbol]] = None
) -> EllipticSearchResult:
    """
    Main elliptic integral search function.

    Pipeline:
        1. Detect elliptic signature
        2. Estimate elliptic parameter m
        3. Try pattern matching
        4. Try hybrid SINDy+elliptic
        5. Validate best candidate

    Args:
        I_numerical: Candidate conserved quantity
        trajectory: Phase space trajectory
        trajectory_times: Time points
        masses: Body masses
        state_symbols: SymPy symbols for state variables

    Returns:
        result: EllipticSearchResult with findings

    Example:
        >>> result = search_elliptic_integral(my_integral, traj, times, masses)
        >>> if result.found_elliptic:
        ...     print(f"Elliptic integral found: {result.best_expression}")
        ...     print(f"Elliptic parameter m = {result.elliptic_parameter:.4f}")
    """
    # Step 1: Detect elliptic signature
    has_signature, confidence, freqs = detect_elliptic_signature(
        I_numerical,
        trajectory,
        trajectory_times,
        threshold=0.6
    )

    if not has_signature:
        return EllipticSearchResult(
            found_elliptic=False,
            best_expression=None,
            best_function=None,
            elliptic_parameter=0.5,
            validation=None,
            search_method="signature_detection",
            confidence=confidence
        )

    print(f"  ✓ Elliptic signature detected (confidence: {confidence:.2f})")
    print(f"    Dominant frequencies: {freqs[0]:.4f}, {freqs[1]:.4f}")

    # Step 2: Estimate elliptic parameter
    m_est = estimate_elliptic_parameter(trajectory, trajectory_times, I_numerical)
    print(f"    Estimated m = {m_est:.4f}")

    # Step 3: Try pattern matching
    print("  Attempting pattern matching...")
    pattern_result = elliptic_pattern_match(I_numerical, trajectory, masses, m_est)

    if pattern_result is not None:
        expr, func, quality = pattern_result
        print(f"  ✓ Pattern match found (quality: {quality:.4f})")

        # Validate
        if state_symbols is None:
            state_symbols = [sp.Symbol(f'z{i}') for i in range(len(trajectory[0]))]

        validation = validate_candidate_integral(
            expr, func, trajectory, state_symbols
        )

        return EllipticSearchResult(
            found_elliptic=True,
            best_expression=expr,
            best_function=func,
            elliptic_parameter=m_est,
            validation=validation,
            search_method="pattern_matching",
            confidence=quality
        )

    # Step 4: Try hybrid SINDy+elliptic
    print("  Attempting hybrid SINDy+elliptic search...")
    hybrid_result = elliptic_sindy_hybrid(I_numerical, trajectory, masses, m_est)

    if hybrid_result is not None:
        expr, residual = hybrid_result
        print(f"  ✓ Hybrid search found candidate (residual: {residual:.2e})")

        if state_symbols is None:
            state_symbols = [sp.Symbol(f'z{i}') for i in range(len(trajectory[0]))]

        validation = validate_candidate_integral(
            expr, I_numerical, trajectory, state_symbols
        )

        return EllipticSearchResult(
            found_elliptic=True,
            best_expression=expr,
            best_function=I_numerical,
            elliptic_parameter=m_est,
            validation=validation,
            search_method="hybrid_sindy_elliptic",
            confidence=1.0 - residual
        )

    # No elliptic form found
    print("  ✗ No elliptic form discovered")

    return EllipticSearchResult(
        found_elliptic=False,
        best_expression=None,
        best_function=None,
        elliptic_parameter=m_est,
        validation=None,
        search_method="none",
        confidence=0.0
    )


# Example usage
if __name__ == "__main__":
    print("Elliptic Search Module - Example")
    print("=" * 70)

    # Create synthetic quasi-periodic integral
    def synthetic_elliptic_integral(state):
        """Mock elliptic integral: I = sn(|r₁|, 0.5)"""
        r1 = state[:3]
        r1_mag = np.linalg.norm(r1)
        return jacobi_sn(r1_mag, 0.5)

    # Generate synthetic trajectory
    t = np.linspace(0, 100, 10000)
    trajectory = np.random.randn(10000, 18)  # 3 bodies

    masses = np.array([1.0, 1.0, 1.0])

    # Run elliptic search
    print("\nSearching for elliptic structure...")
    print("-" * 70)

    result = search_elliptic_integral(
        I_numerical=synthetic_elliptic_integral,
        trajectory=trajectory,
        trajectory_times=t,
        masses=masses
    )

    print("\nResults:")
    print(f"  Found elliptic: {result.found_elliptic}")
    print(f"  Method: {result.search_method}")
    print(f"  Confidence: {result.confidence:.4f}")
    print(f"  Elliptic parameter m: {result.elliptic_parameter:.4f}")

    if result.best_expression:
        print(f"  Expression: {result.best_expression}")

    print("\n" + "=" * 70)
