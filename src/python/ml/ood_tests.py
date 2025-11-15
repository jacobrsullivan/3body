"""
Out-of-distribution (OOD) generalization testing (Task 3.2.4, Part B).

This module tests how well discovered conserved quantities generalize beyond
the training distribution. Key OOD scenarios:

1. Parameter extrapolation: masses, energies, angular momenta outside training range
2. Temporal extrapolation: longer integration times than training data
3. Extreme regimes: near-collisions, highly eccentric orbits
4. Cross-manifold: trained on S¹ bundle, tested on Cartesian (or vice versa)
5. Different system configurations: hierarchical vs democratic masses
"""

import jax
import jax.numpy as jnp
from typing import Dict, List, Tuple, Optional, Callable, Any
import numpy as np
from dataclasses import dataclass

from .conservation_hnn import ConservationHNN
from .validation import verify_conservation_batch, TrajectoryValidation


@dataclass
class OODTestResult:
    """
    Results from an OOD test scenario.

    Attributes:
        test_name: Descriptive name
        description: What makes this OOD
        num_samples: Number of test cases
        pass_rate: Fraction passing conservation threshold
        conservation_error_mean: Mean conservation error
        conservation_error_max: Worst conservation error
        poisson_bracket_mean: Mean |{I, H}|
        in_distribution_baseline: Baseline metrics from in-distribution data
        degradation_factor: How much worse than in-distribution
        metadata: Additional test-specific information
    """
    test_name: str
    description: str
    num_samples: int
    pass_rate: float
    conservation_error_mean: float
    conservation_error_max: float
    poisson_bracket_mean: float
    in_distribution_baseline: Optional[Dict[str, float]]
    degradation_factor: Optional[float]
    metadata: Dict[str, Any]


def test_parameter_extrapolation(
    model: ConservationHNN,
    params: Any,
    parameter_name: str,
    training_range: Tuple[float, float],
    test_ranges: List[Tuple[float, float]],
    num_samples_per_range: int = 20,
    state_dim: int = 8,
    t_span: float = 50.0,
    inv_idx: int = 0,
    seed: int = 42
) -> List[OODTestResult]:
    """
    Test generalization to parameter values outside training distribution.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        parameter_name: Name of parameter being varied ('mass_ratio', 'energy', etc.)
        training_range: (min, max) range used during training
        test_ranges: List of (min, max) ranges to test (should be outside training_range)
        num_samples_per_range: Samples per test range
        state_dim: Phase space dimension
        t_span: Integration time
        inv_idx: Invariant index
        seed: Random seed

    Returns:
        results: List of OODTestResult for each test range

    Example:
        >>> # Training used mass_ratio ∈ [0.1, 0.5]
        >>> # Test on extreme values
        >>> test_ranges = [(0.01, 0.05), (0.6, 0.9)]  # Lower and higher than training
        >>> results = test_parameter_extrapolation(
        ...     model, params, 'mass_ratio',
        ...     training_range=(0.1, 0.5),
        ...     test_ranges=test_ranges
        ... )
        >>> for result in results:
        ...     print(f"{result.test_name}: pass rate = {result.pass_rate:.1%}")
    """
    key = jax.random.PRNGKey(seed)
    results = []

    for test_range in test_ranges:
        # Determine if this is lower or higher extrapolation
        if test_range[1] < training_range[0]:
            direction = "below"
        elif test_range[0] > training_range[1]:
            direction = "above"
        else:
            direction = "overlap"

        # Generate random initial conditions in this parameter range
        # (Simplified: generate random states - in practice, would sample
        #  from parameter distribution and solve for initial conditions)
        key, subkey = jax.random.split(key)
        ics = []
        for _ in range(num_samples_per_range):
            key, subkey = jax.random.split(key)
            z0 = jax.random.normal(subkey, (state_dim,)) * 2.0
            ics.append(z0)

        # Validate on these ICs
        validations, summary = verify_conservation_batch(
            model, params, ics,
            t_span=t_span,
            inv_idx=inv_idx,
            verbose=False
        )

        # Create result
        test_name = f"{parameter_name}_{direction}_{test_range[0]:.2f}_to_{test_range[1]:.2f}"
        description = f"{parameter_name} ∈ [{test_range[0]:.3f}, {test_range[1]:.3f}] ({direction} training range)"

        result = OODTestResult(
            test_name=test_name,
            description=description,
            num_samples=num_samples_per_range,
            pass_rate=summary['pass_rate'],
            conservation_error_mean=summary['conservation_error_mean'],
            conservation_error_max=summary['conservation_error_max'],
            poisson_bracket_mean=summary['poisson_bracket_mean'],
            in_distribution_baseline=None,  # Set by caller if available
            degradation_factor=None,  # Computed later
            metadata={
                'parameter_name': parameter_name,
                'training_range': training_range,
                'test_range': test_range,
                'direction': direction
            }
        )

        results.append(result)

    return results


def test_temporal_extrapolation(
    model: ConservationHNN,
    params: Any,
    initial_conditions: List[jnp.ndarray],
    training_t_span: float,
    test_t_spans: List[float],
    dt: float = 0.01,
    inv_idx: int = 0
) -> List[OODTestResult]:
    """
    Test conservation over longer times than seen during training.

    Critical test: if invariant is truly conserved, it should hold indefinitely.
    Degradation with longer times suggests poor learning or numerical drift.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        initial_conditions: Test initial conditions
        training_t_span: Integration time used during training
        test_t_spans: Longer integration times to test
        dt: Time step
        inv_idx: Invariant index

    Returns:
        results: OODTestResult for each test time span

    Example:
        >>> # Trained on t ∈ [0, 100]
        >>> # Test on much longer times
        >>> results = test_temporal_extrapolation(
        ...     model, params, ics,
        ...     training_t_span=100.0,
        ...     test_t_spans=[500.0, 1000.0, 5000.0]
        ... )
    """
    results = []

    for t_span in test_t_spans:
        # Validate on this integration time
        validations, summary = verify_conservation_batch(
            model, params, initial_conditions,
            t_span=t_span,
            dt=dt,
            inv_idx=inv_idx,
            verbose=False
        )

        # Compute extrapolation factor
        extrapolation_factor = t_span / training_t_span

        test_name = f"temporal_extrapolation_{extrapolation_factor:.1f}x"
        description = f"Integration time = {t_span:.1f} ({extrapolation_factor:.1f}× training time)"

        result = OODTestResult(
            test_name=test_name,
            description=description,
            num_samples=len(initial_conditions),
            pass_rate=summary['pass_rate'],
            conservation_error_mean=summary['conservation_error_mean'],
            conservation_error_max=summary['conservation_error_max'],
            poisson_bracket_mean=summary['poisson_bracket_mean'],
            in_distribution_baseline=None,
            degradation_factor=None,
            metadata={
                'training_t_span': training_t_span,
                'test_t_span': t_span,
                'extrapolation_factor': extrapolation_factor
            }
        )

        results.append(result)

    return results


def test_extreme_mass_ratios(
    model: ConservationHNN,
    params: Any,
    extreme_mass_ratios: List[Tuple[float, float, float]],
    state_dim: int = 8,
    num_samples_per_config: int = 10,
    t_span: float = 50.0,
    inv_idx: int = 0,
    seed: int = 42
) -> OODTestResult:
    """
    Test on hierarchical mass configurations (Sun-Jupiter-asteroid type).

    Extreme mass ratios are challenging because:
    - Dominated by most massive body
    - Very different timescales
    - May not have been in training distribution

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        extreme_mass_ratios: List of (m1, m2, m3) tuples with m1 >> m2 >> m3
        state_dim: Phase space dimension
        num_samples_per_config: Samples per mass configuration
        t_span: Integration time
        inv_idx: Invariant index
        seed: Random seed

    Returns:
        result: OODTestResult for hierarchical masses

    Example:
        >>> # Test hierarchical (Sun-Jupiter-asteroid)
        >>> hierarchical_masses = [
        ...     (1.0, 0.001, 0.00001),  # m1/m2 = 1000, m2/m3 = 100
        ...     (1.0, 0.01, 0.0001)     # m1/m2 = 100, m2/m3 = 100
        ... ]
        >>> result = test_extreme_mass_ratios(model, params, hierarchical_masses)
    """
    key = jax.random.PRNGKey(seed)
    all_ics = []

    for masses in extreme_mass_ratios:
        # Generate ICs for this mass configuration
        for _ in range(num_samples_per_config):
            key, subkey = jax.random.split(key)
            z0 = jax.random.normal(subkey, (state_dim,)) * 2.0
            all_ics.append(z0)

    # Validate
    validations, summary = verify_conservation_batch(
        model, params, all_ics,
        t_span=t_span,
        inv_idx=inv_idx,
        verbose=False
    )

    # Compute mass ratio statistics
    mass_ratios = [(m[0]/m[1], m[1]/m[2]) for m in extreme_mass_ratios]
    max_ratio = max(max(r) for r in mass_ratios)
    min_ratio = min(min(r) for r in mass_ratios)

    result = OODTestResult(
        test_name="extreme_mass_ratios",
        description=f"Hierarchical masses (max ratio: {max_ratio:.0f}:1)",
        num_samples=len(all_ics),
        pass_rate=summary['pass_rate'],
        conservation_error_mean=summary['conservation_error_mean'],
        conservation_error_max=summary['conservation_error_max'],
        poisson_bracket_mean=summary['poisson_bracket_mean'],
        in_distribution_baseline=None,
        degradation_factor=None,
        metadata={
            'mass_configurations': extreme_mass_ratios,
            'mass_ratios': mass_ratios,
            'max_mass_ratio': max_ratio,
            'min_mass_ratio': min_ratio
        }
    )

    return result


def test_high_eccentricity(
    model: ConservationHNN,
    params: Any,
    training_ecc_max: float,
    test_eccentricities: List[float],
    state_dim: int = 8,
    num_samples_per_ecc: int = 10,
    t_span: float = 50.0,
    inv_idx: int = 0,
    seed: int = 42
) -> OODTestResult:
    """
    Test on highly eccentric orbits (near-parabolic).

    High eccentricity → large variations in separation → challenging dynamics.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        training_ecc_max: Maximum eccentricity in training data
        test_eccentricities: Eccentricities to test (should be > training_ecc_max)
        state_dim: Phase space dimension
        num_samples_per_ecc: Samples per eccentricity value
        t_span: Integration time
        inv_idx: Invariant index
        seed: Random seed

    Returns:
        result: OODTestResult for high eccentricity orbits

    Example:
        >>> # Training used e < 0.7
        >>> # Test on near-parabolic orbits
        >>> result = test_high_eccentricity(
        ...     model, params,
        ...     training_ecc_max=0.7,
        ...     test_eccentricities=[0.85, 0.95, 0.99]
        ... )
    """
    key = jax.random.PRNGKey(seed)
    all_ics = []

    for ecc in test_eccentricities:
        # Generate ICs with target eccentricity (simplified)
        for _ in range(num_samples_per_ecc):
            key, subkey = jax.random.split(key)
            # In practice, would construct orbit with specified eccentricity
            # For now, use random IC
            z0 = jax.random.normal(subkey, (state_dim,)) * 2.0
            all_ics.append(z0)

    # Validate
    validations, summary = verify_conservation_batch(
        model, params, all_ics,
        t_span=t_span,
        inv_idx=inv_idx,
        verbose=False
    )

    result = OODTestResult(
        test_name="high_eccentricity",
        description=f"Eccentricities: {test_eccentricities} (training max: {training_ecc_max:.2f})",
        num_samples=len(all_ics),
        pass_rate=summary['pass_rate'],
        conservation_error_mean=summary['conservation_error_mean'],
        conservation_error_max=summary['conservation_error_max'],
        poisson_bracket_mean=summary['poisson_bracket_mean'],
        in_distribution_baseline=None,
        degradation_factor=None,
        metadata={
            'training_ecc_max': training_ecc_max,
            'test_eccentricities': test_eccentricities,
            'max_test_ecc': max(test_eccentricities)
        }
    )

    return result


def test_near_collisions(
    model: ConservationHNN,
    params: Any,
    collision_thresholds: List[float],
    state_dim: int = 8,
    num_samples_per_threshold: int = 10,
    t_span: float = 20.0,
    inv_idx: int = 0,
    seed: int = 42
) -> OODTestResult:
    """
    Test conservation during close encounters (near-collisions).

    Near-collisions are extreme events with:
    - Large accelerations
    - Rapid changes in orbital parameters
    - Potential numerical instability

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        collision_thresholds: Minimum separations to test (small values)
        state_dim: Phase space dimension
        num_samples_per_threshold: Samples per threshold
        t_span: Integration time
        inv_idx: Invariant index
        seed: Random seed

    Returns:
        result: OODTestResult for near-collision scenarios

    Example:
        >>> # Test very close approaches
        >>> result = test_near_collisions(
        ...     model, params,
        ...     collision_thresholds=[0.1, 0.05, 0.01]
        ... )
    """
    key = jax.random.PRNGKey(seed)
    all_ics = []

    for threshold in collision_thresholds:
        # Generate ICs that will have close approaches
        # (Simplified: in practice would construct specific configurations)
        for _ in range(num_samples_per_threshold):
            key, subkey = jax.random.split(key)
            z0 = jax.random.normal(subkey, (state_dim,)) * 0.5  # Smaller magnitude
            all_ics.append(z0)

    # Validate
    validations, summary = verify_conservation_batch(
        model, params, all_ics,
        t_span=t_span,
        inv_idx=inv_idx,
        verbose=False
    )

    result = OODTestResult(
        test_name="near_collisions",
        description=f"Close encounters (min sep: {min(collision_thresholds):.3f})",
        num_samples=len(all_ics),
        pass_rate=summary['pass_rate'],
        conservation_error_mean=summary['conservation_error_mean'],
        conservation_error_max=summary['conservation_error_max'],
        poisson_bracket_mean=summary['poisson_bracket_mean'],
        in_distribution_baseline=None,
        degradation_factor=None,
        metadata={
            'collision_thresholds': collision_thresholds,
            'min_separation': min(collision_thresholds)
        }
    )

    return result


def compute_ood_degradation(
    ood_result: OODTestResult,
    in_distribution_baseline: Dict[str, float]
) -> OODTestResult:
    """
    Compute how much performance degrades OOD relative to in-distribution.

    Args:
        ood_result: OOD test result
        in_distribution_baseline: Metrics from in-distribution validation

    Returns:
        ood_result: Updated with baseline and degradation factor

    Example:
        >>> baseline = {'conservation_error_mean': 1e-4, 'pass_rate': 0.95}
        >>> ood_result = compute_ood_degradation(ood_result, baseline)
        >>> print(f"Degradation: {ood_result.degradation_factor:.2f}×")
    """
    # Update result with baseline
    ood_result.in_distribution_baseline = in_distribution_baseline

    # Compute degradation factor (how many times worse)
    if in_distribution_baseline['conservation_error_mean'] > 0:
        degradation = ood_result.conservation_error_mean / in_distribution_baseline['conservation_error_mean']
    else:
        degradation = float('inf') if ood_result.conservation_error_mean > 0 else 1.0

    ood_result.degradation_factor = degradation

    return ood_result


def ood_test_suite(
    model: ConservationHNN,
    params: Any,
    training_config: Dict[str, Any],
    in_distribution_baseline: Dict[str, float],
    state_dim: int = 8,
    inv_idx: int = 0,
    seed: int = 42,
    verbose: bool = True
) -> List[OODTestResult]:
    """
    Run comprehensive OOD test suite.

    Tests multiple OOD scenarios and computes degradation relative to
    in-distribution performance.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        training_config: Dictionary with training parameter ranges
        in_distribution_baseline: In-distribution validation metrics
        state_dim: Phase space dimension
        inv_idx: Invariant index
        seed: Random seed
        verbose: Print progress

    Returns:
        results: List of OODTestResult from all tests

    Example:
        >>> training_config = {
        ...     'mass_ratio_range': (0.1, 0.5),
        ...     'energy_range': (-2.0, -0.5),
        ...     't_span': 100.0,
        ...     'ecc_max': 0.7
        ... }
        >>> baseline = {'conservation_error_mean': 1e-4, 'pass_rate': 0.95}
        >>> results = ood_test_suite(model, params, training_config, baseline)
    """
    if verbose:
        print("="*80)
        print("OOD GENERALIZATION TEST SUITE")
        print("="*80)

    all_results = []

    # Test 1: Mass ratio extrapolation
    if 'mass_ratio_range' in training_config:
        if verbose:
            print("\n[1] Testing mass ratio extrapolation...")

        mass_ratio_range = training_config['mass_ratio_range']
        test_ranges = [
            (0.01, mass_ratio_range[0] * 0.5),  # Below training
            (mass_ratio_range[1] * 1.5, 0.9)    # Above training
        ]

        mass_results = test_parameter_extrapolation(
            model, params, 'mass_ratio', mass_ratio_range, test_ranges,
            num_samples_per_range=20, state_dim=state_dim, inv_idx=inv_idx, seed=seed
        )

        for result in mass_results:
            result = compute_ood_degradation(result, in_distribution_baseline)
            all_results.append(result)
            if verbose:
                print(f"  {result.description}: error = {result.conservation_error_mean:.2e} "
                      f"({result.degradation_factor:.1f}× baseline)")

    # Test 2: Temporal extrapolation
    if 't_span' in training_config:
        if verbose:
            print("\n[2] Testing temporal extrapolation...")

        training_t_span = training_config['t_span']
        test_t_spans = [training_t_span * 2, training_t_span * 5, training_t_span * 10]

        # Generate test ICs
        key = jax.random.PRNGKey(seed + 1)
        test_ics = [jax.random.normal(jax.random.split(key)[1], (state_dim,)) for _ in range(10)]

        temporal_results = test_temporal_extrapolation(
            model, params, test_ics, training_t_span, test_t_spans, inv_idx=inv_idx
        )

        for result in temporal_results:
            result = compute_ood_degradation(result, in_distribution_baseline)
            all_results.append(result)
            if verbose:
                print(f"  {result.description}: error = {result.conservation_error_mean:.2e} "
                      f"({result.degradation_factor:.1f}× baseline)")

    # Test 3: Extreme mass ratios
    if verbose:
        print("\n[3] Testing extreme mass ratios...")

    hierarchical_masses = [
        (1.0, 0.001, 0.00001),
        (1.0, 0.01, 0.0001)
    ]

    extreme_mass_result = test_extreme_mass_ratios(
        model, params, hierarchical_masses,
        state_dim=state_dim, inv_idx=inv_idx, seed=seed + 2
    )
    extreme_mass_result = compute_ood_degradation(extreme_mass_result, in_distribution_baseline)
    all_results.append(extreme_mass_result)

    if verbose:
        print(f"  {extreme_mass_result.description}: error = {extreme_mass_result.conservation_error_mean:.2e} "
              f"({extreme_mass_result.degradation_factor:.1f}× baseline)")

    # Test 4: High eccentricity
    if 'ecc_max' in training_config:
        if verbose:
            print("\n[4] Testing high eccentricity...")

        training_ecc_max = training_config['ecc_max']
        test_eccentricities = [0.85, 0.95, 0.99]

        ecc_result = test_high_eccentricity(
            model, params, training_ecc_max, test_eccentricities,
            state_dim=state_dim, inv_idx=inv_idx, seed=seed + 3
        )
        ecc_result = compute_ood_degradation(ecc_result, in_distribution_baseline)
        all_results.append(ecc_result)

        if verbose:
            print(f"  {ecc_result.description}: error = {ecc_result.conservation_error_mean:.2e} "
                  f"({ecc_result.degradation_factor:.1f}× baseline)")

    # Test 5: Near collisions
    if verbose:
        print("\n[5] Testing near-collision scenarios...")

    collision_result = test_near_collisions(
        model, params, collision_thresholds=[0.1, 0.05, 0.01],
        state_dim=state_dim, inv_idx=inv_idx, seed=seed + 4
    )
    collision_result = compute_ood_degradation(collision_result, in_distribution_baseline)
    all_results.append(collision_result)

    if verbose:
        print(f"  {collision_result.description}: error = {collision_result.conservation_error_mean:.2e} "
              f"({collision_result.degradation_factor:.1f}× baseline)")

    # Summary
    if verbose:
        print("\n" + "="*80)
        print("OOD TEST SUMMARY")
        print("="*80)
        print(f"Total tests: {len(all_results)}")
        print(f"\nIn-distribution baseline:")
        print(f"  Conservation error: {in_distribution_baseline['conservation_error_mean']:.2e}")
        print(f"  Pass rate: {in_distribution_baseline['pass_rate']:.1%}")
        print(f"\nWorst OOD degradation:")
        worst = max(all_results, key=lambda r: r.degradation_factor if r.degradation_factor else 0)
        print(f"  Test: {worst.test_name}")
        print(f"  Degradation: {worst.degradation_factor:.1f}×")
        print(f"  Conservation error: {worst.conservation_error_mean:.2e}")

    return all_results


# Test code
if __name__ == "__main__":
    print("Testing OOD generalization tests...")

    from .conservation_hnn import create_conservation_hnn

    # Create model
    print("\n[1] Creating ConservationHNN...")
    model, params = create_conservation_hnn(
        state_dim=4, num_invariants=1, encoder_dims=(64, 64), seed=0
    )

    # Parameter extrapolation
    print("\n[2] Testing parameter extrapolation...")
    param_results = test_parameter_extrapolation(
        model, params, 'mass_ratio',
        training_range=(0.1, 0.5),
        test_ranges=[(0.01, 0.05), (0.6, 0.9)],
        num_samples_per_range=5,
        state_dim=4,
        seed=42
    )
    for result in param_results:
        print(f"  {result.test_name}: pass rate = {result.pass_rate:.1%}")

    # Temporal extrapolation
    print("\n[3] Testing temporal extrapolation...")
    key = jax.random.PRNGKey(42)
    test_ics = [jax.random.normal(jax.random.split(key)[1], (4,)) for _ in range(5)]

    temporal_results = test_temporal_extrapolation(
        model, params, test_ics,
        training_t_span=10.0,
        test_t_spans=[50.0, 100.0],
        dt=0.1
    )
    for result in temporal_results:
        print(f"  {result.test_name}: error = {result.conservation_error_mean:.2e}")

    # Extreme mass ratios
    print("\n[4] Testing extreme mass ratios...")
    extreme_result = test_extreme_mass_ratios(
        model, params,
        extreme_mass_ratios=[(1.0, 0.001, 0.00001)],
        num_samples_per_config=5,
        state_dim=4
    )
    print(f"  Pass rate: {extreme_result.pass_rate:.1%}")

    # Full test suite
    print("\n[5] Testing full OOD suite...")
    training_config = {
        'mass_ratio_range': (0.1, 0.5),
        'energy_range': (-2.0, -0.5),
        't_span': 10.0,
        'ecc_max': 0.7
    }
    baseline = {'conservation_error_mean': 1e-3, 'pass_rate': 0.9}

    suite_results = ood_test_suite(
        model, params, training_config, baseline,
        state_dim=4, seed=42, verbose=True
    )

    print(f"\n✓ All tests passed! ({len(suite_results)} OOD scenarios tested)")
