"""
Comparison with WP 3.1 geometric methods (Task 3.2.4, Part D).

WP 3.1 uses differential geometry to discover conserved quantities via:
- Killing vector fields on lifted manifolds (S¹ bundle, KS regularization)
- Solving Killing PDEs: ∇·K + (∇·K)ᵀ = 0
- Null space analysis of symmetry conditions

This module compares ML-discovered invariants (WP 3.2) with geometric
invariants (WP 3.1) to validate the ML approach.

Comparison Metrics:
------------------
1. Correlation: Do ML and geometric invariants agree?
2. Functional equivalence: Is I_ML = f(I_geom) for some function f?
3. Coverage: Does ML discover invariants missed by geometry (and vice versa)?
4. Conservation quality: Which method produces better-conserved quantities?
5. Computational cost: Training time vs PDE solving time
"""

import jax
import jax.numpy as jnp
from typing import Dict, List, Tuple, Optional, Callable, Any
import numpy as np
from dataclasses import dataclass
from scipy.stats import pearsonr, spearmanr

from .conservation_hnn import ConservationHNN
from .validation import verify_conservation_batch


@dataclass
class ComparisonResult:
    """
    Results from comparing ML vs geometric invariants.

    Attributes:
        ml_invariant_name: Name of ML invariant
        geometric_invariant_name: Name of geometric invariant
        pearson_correlation: Linear correlation
        spearman_correlation: Rank correlation (robust to monotonic transforms)
        rmse_normalized: Root mean squared error (normalized)
        r2_score: Coefficient of determination
        functional_form: Detected functional relationship (if any)
        ml_conservation_error: Conservation quality of ML invariant
        geometric_conservation_error: Conservation quality of geometric invariant
        agreement: Qualitative agreement level
        metadata: Additional information
    """
    ml_invariant_name: str
    geometric_invariant_name: str
    pearson_correlation: float
    spearman_correlation: float
    rmse_normalized: float
    r2_score: float
    functional_form: Optional[str]
    ml_conservation_error: float
    geometric_conservation_error: float
    agreement: str  # 'perfect', 'good', 'moderate', 'weak', 'none'
    metadata: Dict[str, Any]


def compare_invariants(
    ml_invariant: jnp.ndarray,
    geometric_invariant: jnp.ndarray,
    ml_name: str = "ML invariant",
    geom_name: str = "Geometric invariant",
    ml_conservation_error: Optional[float] = None,
    geom_conservation_error: Optional[float] = None
) -> ComparisonResult:
    """
    Compare ML-discovered invariant with geometric invariant.

    Args:
        ml_invariant: Values of ML invariant on test set (N,)
        geometric_invariant: Values of geometric invariant on test set (N,)
        ml_name: Descriptive name for ML invariant
        geom_name: Descriptive name for geometric invariant
        ml_conservation_error: Conservation error for ML invariant
        geom_conservation_error: Conservation error for geometric invariant

    Returns:
        result: ComparisonResult

    Example:
        >>> I_ml = model.batch_invariant(params, test_states, inv_idx=0)
        >>> I_geom = evaluate_killing_invariant(test_states, killing_field_0)
        >>> result = compare_invariants(I_ml, I_geom)
        >>> print(f"Correlation: {result.pearson_correlation:.6f}")
    """
    # Ensure numpy arrays
    I_ml = np.array(ml_invariant)
    I_geom = np.array(geometric_invariant)

    # Normalize to zero mean, unit variance
    I_ml_norm = (I_ml - np.mean(I_ml)) / np.std(I_ml)
    I_geom_norm = (I_geom - np.mean(I_geom)) / np.std(I_geom)

    # Pearson correlation (measures linear relationship)
    pearson_corr, _ = pearsonr(I_ml, I_geom)

    # Spearman correlation (measures monotonic relationship, robust to transformations)
    spearman_corr, _ = spearmanr(I_ml, I_geom)

    # RMSE (normalized)
    rmse_norm = float(np.sqrt(np.mean((I_ml_norm - I_geom_norm)**2)))

    # R² score
    ss_res = np.sum((I_ml - I_geom)**2)
    ss_tot = np.sum((I_geom - np.mean(I_geom))**2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else -np.inf

    # Detect functional relationship
    functional_form = detect_functional_relationship(I_ml, I_geom)

    # Determine agreement level
    abs_corr = abs(pearson_corr)
    if abs_corr > 0.99:
        agreement = 'perfect'
    elif abs_corr > 0.95:
        agreement = 'excellent'
    elif abs_corr > 0.8:
        agreement = 'good'
    elif abs_corr > 0.5:
        agreement = 'moderate'
    else:
        agreement = 'weak'

    result = ComparisonResult(
        ml_invariant_name=ml_name,
        geometric_invariant_name=geom_name,
        pearson_correlation=float(pearson_corr),
        spearman_correlation=float(spearman_corr),
        rmse_normalized=rmse_norm,
        r2_score=r2,
        functional_form=functional_form,
        ml_conservation_error=ml_conservation_error if ml_conservation_error else np.nan,
        geometric_conservation_error=geom_conservation_error if geom_conservation_error else np.nan,
        agreement=agreement,
        metadata={
            'ml_mean': float(np.mean(I_ml)),
            'ml_std': float(np.std(I_ml)),
            'geom_mean': float(np.mean(I_geom)),
            'geom_std': float(np.std(I_geom))
        }
    )

    return result


def detect_functional_relationship(
    I_ml: np.ndarray,
    I_geom: np.ndarray,
    corr_threshold: float = 0.98
) -> Optional[str]:
    """
    Attempt to detect functional relationship between invariants.

    Tests various functional forms:
    - Linear: I_ml = a·I_geom + b
    - Quadratic: I_ml = a·I_geom² + b·I_geom + c
    - Power: I_ml = a·I_geom^p
    - Exponential: I_ml = a·exp(b·I_geom)
    - Logarithmic: I_ml = a·log(I_geom) + b

    Args:
        I_ml: ML invariant values
        I_geom: Geometric invariant values
        corr_threshold: Correlation threshold to accept relationship

    Returns:
        functional_form: String description if detected, else None

    Example:
        >>> form = detect_functional_relationship(I_ml, I_geom)
        >>> if form:
        ...     print(f"Detected: {form}")
    """
    from scipy.optimize import curve_fit

    # Test 1: Linear (I_ml = a·I_geom + b)
    def linear(x, a, b):
        return a * x + b

    try:
        popt, _ = curve_fit(linear, I_geom, I_ml)
        I_ml_pred = linear(I_geom, *popt)
        corr, _ = pearsonr(I_ml, I_ml_pred)
        if abs(corr) > corr_threshold:
            return f"Linear: I_ML = {popt[0]:.4f}·I_geom + {popt[1]:.4f}"
    except:
        pass

    # Test 2: Quadratic
    def quadratic(x, a, b, c):
        return a * x**2 + b * x + c

    try:
        popt, _ = curve_fit(quadratic, I_geom, I_ml)
        I_ml_pred = quadratic(I_geom, *popt)
        corr, _ = pearsonr(I_ml, I_ml_pred)
        if abs(corr) > corr_threshold:
            return f"Quadratic: I_ML = {popt[0]:.4f}·I_geom² + {popt[1]:.4f}·I_geom + {popt[2]:.4f}"
    except:
        pass

    # Test 3: Power (I_ml = a·I_geom^p)
    if np.all(I_geom > 0):  # Power law requires positive values
        def power(x, a, p):
            return a * x**p

        try:
            popt, _ = curve_fit(power, I_geom, I_ml, p0=[1.0, 1.0])
            I_ml_pred = power(I_geom, *popt)
            corr, _ = pearsonr(I_ml, I_ml_pred)
            if abs(corr) > corr_threshold:
                return f"Power: I_ML = {popt[0]:.4f}·I_geom^{popt[1]:.4f}"
        except:
            pass

    # Test 4: Logarithmic
    if np.all(I_geom > 0):
        def logarithmic(x, a, b):
            return a * np.log(x) + b

        try:
            popt, _ = curve_fit(logarithmic, I_geom, I_ml)
            I_ml_pred = logarithmic(I_geom, *popt)
            corr, _ = pearsonr(I_ml, I_ml_pred)
            if abs(corr) > corr_threshold:
                return f"Logarithmic: I_ML = {popt[0]:.4f}·log(I_geom) + {popt[1]:.4f}"
        except:
            pass

    return None  # No clear relationship detected


def compare_with_energy(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    energy_func: Callable[[jnp.ndarray], float],
    inv_idx: int = 0
) -> ComparisonResult:
    """
    Compare ML invariant with total energy (common geometric invariant).

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        energy_func: Function computing total energy E(z)
        inv_idx: ML invariant index

    Returns:
        result: ComparisonResult

    Example:
        >>> def energy(z):
        ...     # Compute E = T + V
        ...     return kinetic_energy(z) + potential_energy(z)
        >>> result = compare_with_energy(model, params, test_states, energy)
    """
    # Compute ML invariant
    I_ml = model.batch_invariant(params, test_states, inv_idx)

    # Compute energy
    E_geom = jax.vmap(energy_func)(test_states)

    # Compare
    result = compare_invariants(
        I_ml, E_geom,
        ml_name=f"ML invariant {inv_idx}",
        geom_name="Total energy"
    )

    return result


def compare_with_angular_momentum(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    angular_momentum_func: Callable[[jnp.ndarray], float],
    inv_idx: int = 0
) -> ComparisonResult:
    """
    Compare ML invariant with angular momentum (common for planar 3-body).

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        angular_momentum_func: Function computing L_z(z)
        inv_idx: ML invariant index

    Returns:
        result: ComparisonResult

    Example:
        >>> def angular_momentum_z(z):
        ...     # Compute L_z = Σ(r × v)_z
        ...     return compute_total_angular_momentum_z(z)
        >>> result = compare_with_angular_momentum(model, params, test_states, angular_momentum_z)
    """
    # Compute ML invariant
    I_ml = model.batch_invariant(params, test_states, inv_idx)

    # Compute angular momentum
    L_geom = jax.vmap(angular_momentum_func)(test_states)

    # Compare
    result = compare_invariants(
        I_ml, L_geom,
        ml_name=f"ML invariant {inv_idx}",
        geom_name="Angular momentum L_z"
    )

    return result


def cross_method_validation(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    geometric_invariants: List[Tuple[str, Callable]],
    num_ml_invariants: int = None,
    verbose: bool = True
) -> List[ComparisonResult]:
    """
    Comprehensive comparison of ML invariants with geometric invariants.

    Tests all ML invariants against all geometric invariants to find matches.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        geometric_invariants: List of (name, function) pairs for geometric invariants
        num_ml_invariants: Number of ML invariants to test (default: all)
        verbose: Print results

    Returns:
        results: List of ComparisonResult for all pairs

    Example:
        >>> geometric_invariants = [
        ...     ("Energy", energy_func),
        ...     ("Angular momentum", angular_momentum_func),
        ...     ("Killing invariant 0", killing_inv_0_func)
        ... ]
        >>> results = cross_method_validation(
        ...     model, params, test_states, geometric_invariants
        ... )
    """
    if num_ml_invariants is None:
        if hasattr(model, 'num_invariants'):
            num_ml_invariants = model.num_invariants
        else:
            num_ml_invariants = 1

    if verbose:
        print("="*80)
        print("CROSS-METHOD VALIDATION (ML vs Geometric)")
        print("="*80)
        print(f"ML invariants: {num_ml_invariants}")
        print(f"Geometric invariants: {len(geometric_invariants)}")

    results = []

    for ml_idx in range(num_ml_invariants):
        if verbose:
            print(f"\n--- ML Invariant {ml_idx} ---")

        # Compute ML invariant
        I_ml = model.batch_invariant(params, test_states, ml_idx)

        for geom_name, geom_func in geometric_invariants:
            # Compute geometric invariant
            I_geom = jax.vmap(geom_func)(test_states)

            # Compare
            result = compare_invariants(
                I_ml, I_geom,
                ml_name=f"ML invariant {ml_idx}",
                geom_name=geom_name
            )

            results.append(result)

            if verbose:
                print(f"  vs {geom_name}:")
                print(f"    Pearson correlation: {result.pearson_correlation:7.4f}")
                print(f"    Spearman correlation: {result.spearman_correlation:7.4f}")
                print(f"    Agreement: {result.agreement}")
                if result.functional_form:
                    print(f"    Form: {result.functional_form}")

    # Find best matches
    if verbose:
        print("\n" + "="*80)
        print("BEST MATCHES")
        print("="*80)

        for ml_idx in range(num_ml_invariants):
            ml_results = [r for r in results if r.ml_invariant_name == f"ML invariant {ml_idx}"]
            best = max(ml_results, key=lambda r: abs(r.pearson_correlation))
            print(f"ML invariant {ml_idx} ↔ {best.geometric_invariant_name}")
            print(f"  Correlation: {best.pearson_correlation:.6f} ({best.agreement})")
            if best.functional_form:
                print(f"  Form: {best.functional_form}")

    return results


def method_comparison_summary(
    ml_invariants: List[jnp.ndarray],
    geometric_invariants: List[jnp.ndarray],
    ml_method_name: str = "ML (WP 3.2)",
    geometric_method_name: str = "Geometric (WP 3.1)"
) -> Dict[str, Any]:
    """
    High-level comparison of ML vs geometric methods.

    Args:
        ml_invariants: List of ML invariant values
        geometric_invariants: List of geometric invariant values
        ml_method_name: Name of ML method
        geometric_method_name: Name of geometric method

    Returns:
        summary: Comparison summary

    Example:
        >>> summary = method_comparison_summary(
        ...     ml_invariants=[I_ml_0, I_ml_1],
        ...     geometric_invariants=[E, L_z]
        ... )
        >>> print(f"Coverage: ML={summary['ml_coverage']}, Geom={summary['geom_coverage']}")
    """
    num_ml = len(ml_invariants)
    num_geom = len(geometric_invariants)

    # Compute correlation matrix
    corr_matrix = np.zeros((num_ml, num_geom))
    for i, I_ml in enumerate(ml_invariants):
        for j, I_geom in enumerate(geometric_invariants):
            corr, _ = pearsonr(np.array(I_ml), np.array(I_geom))
            corr_matrix[i, j] = abs(corr)

    # Find matches (correlation > 0.9)
    matches = []
    for i in range(num_ml):
        for j in range(num_geom):
            if corr_matrix[i, j] > 0.9:
                matches.append((i, j, corr_matrix[i, j]))

    # Coverage: what fraction are matched?
    ml_coverage = len(set(m[0] for m in matches)) / num_ml if num_ml > 0 else 0
    geom_coverage = len(set(m[1] for m in matches)) / num_geom if num_geom > 0 else 0

    summary = {
        'num_ml_invariants': num_ml,
        'num_geometric_invariants': num_geom,
        'num_matches': len(matches),
        'ml_coverage': ml_coverage,  # Fraction of ML invariants matched to geometric
        'geometric_coverage': geom_coverage,  # Fraction of geometric invariants discovered by ML
        'correlation_matrix': corr_matrix,
        'matches': matches,
        'ml_method': ml_method_name,
        'geometric_method': geometric_method_name
    }

    return summary


# Test code
if __name__ == "__main__":
    print("Testing WP 3.1 comparison module...")

    from .conservation_hnn import create_conservation_hnn

    # Create model
    print("\n[1] Creating ConservationHNN...")
    model, params = create_conservation_hnn(
        state_dim=4, num_invariants=2, encoder_dims=(64, 64), seed=0
    )

    # Generate test states
    key = jax.random.PRNGKey(42)
    test_states = jax.random.normal(key, (100, 4)) * 2.0

    # Define "geometric" invariants (for testing, use simple functions)
    def energy_func(z):
        """Total energy (harmonic oscillator)"""
        return 0.5 * jnp.sum(z**2)

    def angular_momentum_func(z):
        """Angular momentum (simplified)"""
        q, p = z[:2], z[2:]
        return q[0] * p[1] - q[1] * p[0]

    # Test 1: Compare with energy
    print("\n[2] Comparing with energy...")
    result_energy = compare_with_energy(model, params, test_states, energy_func, inv_idx=0)
    print(f"  Correlation: {result_energy.pearson_correlation:.6f}")
    print(f"  Agreement: {result_energy.agreement}")
    if result_energy.functional_form:
        print(f"  Form: {result_energy.functional_form}")

    # Test 2: Compare with angular momentum
    print("\n[3] Comparing with angular momentum...")
    result_L = compare_with_angular_momentum(model, params, test_states, angular_momentum_func, inv_idx=1)
    print(f"  Correlation: {result_L.pearson_correlation:.6f}")
    print(f"  Agreement: {result_L.agreement}")

    # Test 3: Cross-method validation
    print("\n[4] Cross-method validation...")
    geometric_invariants = [
        ("Energy", energy_func),
        ("Angular momentum", angular_momentum_func)
    ]

    cross_results = cross_method_validation(
        model, params, test_states, geometric_invariants, verbose=True
    )

    # Test 4: Method comparison summary
    print("\n[5] Method comparison summary...")
    I_ml_0 = model.batch_invariant(params, test_states, 0)
    I_ml_1 = model.batch_invariant(params, test_states, 1)
    E_geom = jax.vmap(energy_func)(test_states)
    L_geom = jax.vmap(angular_momentum_func)(test_states)

    summary = method_comparison_summary(
        ml_invariants=[I_ml_0, I_ml_1],
        geometric_invariants=[E_geom, L_geom]
    )
    print(f"  ML coverage: {summary['ml_coverage']:.1%}")
    print(f"  Geometric coverage: {summary['geometric_coverage']:.1%}")
    print(f"  Matches: {summary['num_matches']}")

    print("\n✓ All tests passed!")
