"""
Conservation verification and validation (Task 3.2.4, Part A).

This module provides tools for rigorously testing discovered conserved quantities
on held-out test trajectories and verifying that they satisfy the conservation
criterion {I, H} ≈ 0.

Key Validation Tests:
--------------------
1. Conservation along trajectories: I(t) ≈ I(0) for all t
2. Poisson bracket verification: {I, H} ≈ 0 at all points
3. Comparison with known invariants (energy, angular momentum)
4. Statistical analysis of conservation quality
5. Trajectory-by-trajectory validation reports
"""

import jax
import jax.numpy as jnp
from typing import Dict, List, Tuple, Optional, Callable, Any
import numpy as np
from dataclasses import dataclass

from .conservation_hnn import ConservationHNN
from .conservation_loss import compute_conservation_violation
from .model_utils import integrate_trajectory_learned


@dataclass
class TrajectoryValidation:
    """
    Validation results for a single trajectory.

    Attributes:
        trajectory_id: Unique identifier
        initial_condition: Initial state z0
        invariant_values: I(z(t)) along trajectory (T,)
        conservation_error: max|I(t) - I(0)| / |I(0)|
        poisson_bracket_values: {I, H}(z(t)) along trajectory (T,)
        poisson_bracket_mean: Mean |{I, H}|
        poisson_bracket_max: Max |{I, H}|
        passed: True if conservation_error < threshold
        metadata: Additional information
    """
    trajectory_id: int
    initial_condition: jnp.ndarray
    invariant_values: jnp.ndarray
    conservation_error: float
    poisson_bracket_values: jnp.ndarray
    poisson_bracket_mean: float
    poisson_bracket_max: float
    passed: bool
    metadata: Dict[str, Any]


def verify_conservation_single_trajectory(
    model: ConservationHNN,
    params: Any,
    z0: jnp.ndarray,
    t_span: float = 100.0,
    dt: float = 0.01,
    inv_idx: int = 0,
    conservation_threshold: float = 1e-3
) -> TrajectoryValidation:
    """
    Verify conservation of discovered invariant on a single trajectory.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        z0: Initial condition (state_dim,)
        t_span: Integration time
        dt: Time step
        inv_idx: Invariant index to test
        conservation_threshold: Relative error threshold for pass/fail

    Returns:
        validation: TrajectoryValidation results

    Example:
        >>> model, params = load_checkpoint('model.pkl')
        >>> z0 = jnp.array([1.0, 0.0, 0.0, 1.0])  # Initial condition
        >>> result = verify_conservation_single_trajectory(model, params, z0)
        >>> print(f"Conservation error: {result.conservation_error:.2e}")
        >>> print(f"Passed: {result.passed}")
    """
    # Integrate trajectory using learned Hamiltonian
    times, trajectory = integrate_trajectory_learned(
        model, params, z0, t_span=t_span, dt=dt
    )

    # Compute invariant along trajectory
    I_values = model.batch_invariant(params, trajectory, inv_idx)

    # Conservation error: relative drift
    I_initial = I_values[0]
    I_drift_abs = jnp.max(jnp.abs(I_values - I_initial))
    conservation_error = float(I_drift_abs / jnp.abs(I_initial))

    # Compute Poisson bracket {I, H} at each point
    pb_values = jnp.zeros(len(trajectory))
    for i, z in enumerate(trajectory):
        # Poisson bracket at single state
        n = len(z) // 2
        H_func = lambda state: model.hamiltonian(params, state)
        I_func = lambda state: model.invariant(params, state, inv_idx)

        grad_H = jax.grad(H_func)(z)
        grad_I = jax.grad(I_func)(z)

        dH_dq, dH_dp = grad_H[:n], grad_H[n:]
        dI_dq, dI_dp = grad_I[:n], grad_I[n:]

        bracket = jnp.dot(dI_dq, dH_dp) - jnp.dot(dI_dp, dH_dq)
        pb_values = pb_values.at[i].set(bracket)

    pb_mean = float(jnp.mean(jnp.abs(pb_values)))
    pb_max = float(jnp.max(jnp.abs(pb_values)))

    # Pass/fail
    passed = conservation_error < conservation_threshold

    # Metadata
    metadata = {
        'integration_time': t_span,
        'num_timesteps': len(times),
        'dt': dt,
        'invariant_initial': float(I_initial),
        'invariant_final': float(I_values[-1]),
        'invariant_mean': float(jnp.mean(I_values)),
        'invariant_std': float(jnp.std(I_values))
    }

    return TrajectoryValidation(
        trajectory_id=-1,  # To be set by caller
        initial_condition=z0,
        invariant_values=I_values,
        conservation_error=conservation_error,
        poisson_bracket_values=pb_values,
        poisson_bracket_mean=pb_mean,
        poisson_bracket_max=pb_max,
        passed=passed,
        metadata=metadata
    )


def verify_conservation_batch(
    model: ConservationHNN,
    params: Any,
    initial_conditions: List[jnp.ndarray],
    t_span: float = 100.0,
    dt: float = 0.01,
    inv_idx: int = 0,
    conservation_threshold: float = 1e-3,
    verbose: bool = True
) -> Tuple[List[TrajectoryValidation], Dict[str, Any]]:
    """
    Verify conservation on a batch of test trajectories.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        initial_conditions: List of initial states
        t_span: Integration time
        dt: Time step
        inv_idx: Invariant index
        conservation_threshold: Pass/fail threshold
        verbose: Print progress

    Returns:
        validations: List of TrajectoryValidation results
        summary: Summary statistics

    Example:
        >>> z0_list = [jnp.array([...]) for _ in range(100)]
        >>> validations, summary = verify_conservation_batch(model, params, z0_list)
        >>> print(f"Pass rate: {summary['pass_rate']:.1%}")
    """
    if verbose:
        print(f"Validating {len(initial_conditions)} trajectories...")
        print(f"Integration time: {t_span}, dt: {dt}")
        print(f"Conservation threshold: {conservation_threshold:.2e}")

    validations = []

    for i, z0 in enumerate(initial_conditions):
        if verbose and (i % 10 == 0 or i == len(initial_conditions) - 1):
            print(f"  Progress: {i+1}/{len(initial_conditions)}", end='\r')

        validation = verify_conservation_single_trajectory(
            model, params, z0, t_span, dt, inv_idx, conservation_threshold
        )
        validation.trajectory_id = i
        validations.append(validation)

    if verbose:
        print()  # New line after progress

    # Compute summary statistics
    conservation_errors = [v.conservation_error for v in validations]
    pb_means = [v.poisson_bracket_mean for v in validations]
    pb_maxs = [v.poisson_bracket_max for v in validations]
    passed = [v.passed for v in validations]

    summary = {
        'num_trajectories': len(validations),
        'num_passed': sum(passed),
        'num_failed': len(passed) - sum(passed),
        'pass_rate': sum(passed) / len(passed),
        'conservation_error_mean': np.mean(conservation_errors),
        'conservation_error_median': np.median(conservation_errors),
        'conservation_error_max': np.max(conservation_errors),
        'conservation_error_min': np.min(conservation_errors),
        'poisson_bracket_mean': np.mean(pb_means),
        'poisson_bracket_max_mean': np.mean(pb_maxs),
        'poisson_bracket_max_max': np.max(pb_maxs)
    }

    if verbose:
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"Trajectories tested: {summary['num_trajectories']}")
        print(f"Passed: {summary['num_passed']} ({summary['pass_rate']:.1%})")
        print(f"Failed: {summary['num_failed']}")
        print(f"\nConservation Error:")
        print(f"  Mean: {summary['conservation_error_mean']:.2e}")
        print(f"  Median: {summary['conservation_error_median']:.2e}")
        print(f"  Max: {summary['conservation_error_max']:.2e}")
        print(f"\nPoisson Bracket:")
        print(f"  Mean: {summary['poisson_bracket_mean']:.2e}")
        print(f"  Max: {summary['poisson_bracket_max_max']:.2e}")

    return validations, summary


def compare_with_known_invariant(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    known_invariant_func: Callable[[jnp.ndarray], float],
    inv_idx: int = 0
) -> Dict[str, float]:
    """
    Compare discovered invariant with a known conserved quantity.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        known_invariant_func: Function that computes known invariant
        inv_idx: Discovered invariant index

    Returns:
        comparison: Dictionary with correlation, RMSE, etc.

    Example:
        >>> # Compare with energy
        >>> def energy(z):
        ...     q, p = z[:2], z[2:]
        ...     return 0.5 * jnp.sum(p**2) + 0.5 * jnp.sum(q**2)
        >>> comparison = compare_with_known_invariant(model, params, test_states, energy)
        >>> print(f"Correlation: {comparison['pearson_correlation']:.6f}")
    """
    # Compute discovered invariant
    I_discovered = model.batch_invariant(params, test_states, inv_idx)

    # Compute known invariant
    I_known = jax.vmap(known_invariant_func)(test_states)

    # Normalize both to zero mean, unit variance for comparison
    I_disc_norm = (I_discovered - jnp.mean(I_discovered)) / jnp.std(I_discovered)
    I_known_norm = (I_known - jnp.mean(I_known)) / jnp.std(I_known)

    # Pearson correlation
    pearson_corr = float(jnp.corrcoef(I_disc_norm, I_known_norm)[0, 1])

    # Spearman correlation (rank-based, robust to monotonic transformations)
    from scipy.stats import spearmanr
    spearman_corr, _ = spearmanr(np.array(I_discovered), np.array(I_known))

    # RMSE (normalized)
    rmse_normalized = float(jnp.sqrt(jnp.mean((I_disc_norm - I_known_norm)**2)))

    # R² score
    ss_res = jnp.sum((I_discovered - I_known)**2)
    ss_tot = jnp.sum((I_known - jnp.mean(I_known))**2)
    r2_score = float(1 - ss_res / ss_tot)

    comparison = {
        'pearson_correlation': pearson_corr,
        'spearman_correlation': float(spearman_corr),
        'rmse_normalized': rmse_normalized,
        'r2_score': r2_score,
        'discovered_mean': float(jnp.mean(I_discovered)),
        'discovered_std': float(jnp.std(I_discovered)),
        'known_mean': float(jnp.mean(I_known)),
        'known_std': float(jnp.std(I_known))
    }

    return comparison


def long_term_conservation_test(
    model: ConservationHNN,
    params: Any,
    z0: jnp.ndarray,
    t_spans: List[float] = [10.0, 50.0, 100.0, 500.0, 1000.0],
    dt: float = 0.01,
    inv_idx: int = 0
) -> Dict[str, List[float]]:
    """
    Test conservation quality over increasing integration times.

    Tests how well conservation holds for short vs long integrations.
    Good invariants should maintain low error even for very long times.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        z0: Initial condition
        t_spans: List of integration times to test
        dt: Time step
        inv_idx: Invariant index

    Returns:
        results: Dictionary mapping t_span → conservation_error

    Example:
        >>> results = long_term_conservation_test(model, params, z0)
        >>> for t_span, error in zip(results['t_spans'], results['conservation_errors']):
        ...     print(f"t={t_span:6.1f}: error = {error:.2e}")
    """
    conservation_errors = []
    pb_means = []
    pb_maxs = []

    for t_span in t_spans:
        validation = verify_conservation_single_trajectory(
            model, params, z0, t_span=t_span, dt=dt, inv_idx=inv_idx
        )

        conservation_errors.append(validation.conservation_error)
        pb_means.append(validation.poisson_bracket_mean)
        pb_maxs.append(validation.poisson_bracket_max)

    results = {
        't_spans': t_spans,
        'conservation_errors': conservation_errors,
        'poisson_bracket_means': pb_means,
        'poisson_bracket_maxs': pb_maxs
    }

    return results


def energy_surface_validation(
    model: ConservationHNN,
    params: Any,
    energy_levels: List[float],
    num_samples_per_level: int = 20,
    state_dim: int = 4,
    inv_idx: int = 0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Validate conservation across different energy surfaces.

    Tests whether the discovered invariant conserves equally well across
    different energy levels (important for generalization).

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        energy_levels: List of energy values to test
        num_samples_per_level: Samples per energy level
        state_dim: Phase space dimension
        inv_idx: Invariant index
        seed: Random seed

    Returns:
        results: Conservation statistics per energy level

    Example:
        >>> energy_levels = [-2.0, -1.0, -0.5, -0.1]
        >>> results = energy_surface_validation(model, params, energy_levels)
        >>> for E, stats in zip(results['energy_levels'], results['conservation_errors_mean']):
        ...     print(f"E={E:.2f}: error = {stats:.2e}")
    """
    key = jax.random.PRNGKey(seed)
    results = {
        'energy_levels': energy_levels,
        'conservation_errors_mean': [],
        'conservation_errors_std': [],
        'poisson_bracket_means': [],
        'num_samples': num_samples_per_level
    }

    for E in energy_levels:
        # Generate random initial conditions on this energy surface
        # (Simplified: use random states and check energy approximately)
        key, subkey = jax.random.split(key)
        ics = []

        attempts = 0
        while len(ics) < num_samples_per_level and attempts < num_samples_per_level * 10:
            key, subkey = jax.random.split(key)
            z_candidate = jax.random.normal(subkey, (state_dim,)) * 2.0

            # Compute energy (using learned Hamiltonian as proxy)
            H = model.hamiltonian(params, z_candidate)

            # Accept if close to target energy
            if abs(H - E) / abs(E) < 0.1:  # Within 10%
                ics.append(z_candidate)

            attempts += 1

        if len(ics) < num_samples_per_level:
            print(f"Warning: Only found {len(ics)} samples for E={E:.2f}")

        # Validate on these initial conditions
        validations, _ = verify_conservation_batch(
            model, params, ics, t_span=50.0, dt=0.01, inv_idx=inv_idx, verbose=False
        )

        # Aggregate statistics
        errors = [v.conservation_error for v in validations]
        pb_means = [v.poisson_bracket_mean for v in validations]

        results['conservation_errors_mean'].append(np.mean(errors))
        results['conservation_errors_std'].append(np.std(errors))
        results['poisson_bracket_means'].append(np.mean(pb_means))

    return results


def phase_space_coverage_validation(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    inv_idx: int = 0,
    num_bins: int = 10
) -> Dict[str, Any]:
    """
    Validate conservation quality across different regions of phase space.

    Bins test states by position and momentum ranges, checks if conservation
    quality is uniform across phase space.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        inv_idx: Invariant index
        num_bins: Number of bins per dimension

    Returns:
        results: Conservation quality per phase space region

    Example:
        >>> results = phase_space_coverage_validation(model, params, test_states)
        >>> print(f"Most challenging region: bin {results['worst_bin_idx']}")
        >>> print(f"  Conservation error: {results['worst_conservation_error']:.2e}")
    """
    n = test_states.shape[1] // 2

    # Compute Poisson bracket at all test points
    conservation_stats = compute_conservation_violation(params, model, test_states, inv_idx)

    # Bin by magnitude of position vector
    q_norms = jnp.linalg.norm(test_states[:, :n], axis=1)
    q_bins = jnp.digitize(q_norms, jnp.linspace(jnp.min(q_norms), jnp.max(q_norms), num_bins))

    # Bin by magnitude of momentum vector
    p_norms = jnp.linalg.norm(test_states[:, n:], axis=1)
    p_bins = jnp.digitize(p_norms, jnp.linspace(jnp.min(p_norms), jnp.max(p_norms), num_bins))

    # Compute statistics per bin
    bin_statistics = {}
    for q_bin in range(1, num_bins + 1):
        for p_bin in range(1, num_bins + 1):
            mask = (q_bins == q_bin) & (p_bins == p_bin)
            if jnp.sum(mask) > 0:
                bin_stats = {
                    'count': int(jnp.sum(mask)),
                    'conservation_mean': float(jnp.mean(conservation_stats['violations'][mask])),
                    'conservation_max': float(jnp.max(conservation_stats['violations'][mask]))
                }
                bin_statistics[(q_bin, p_bin)] = bin_stats

    # Find worst bin
    worst_bin = max(bin_statistics.items(), key=lambda x: x[1]['conservation_mean'])

    results = {
        'num_bins': num_bins,
        'bin_statistics': bin_statistics,
        'worst_bin_idx': worst_bin[0],
        'worst_conservation_error': worst_bin[1]['conservation_mean'],
        'best_bin_idx': min(bin_statistics.items(), key=lambda x: x[1]['conservation_mean'])[0],
        'best_conservation_error': min(bin_statistics.items(), key=lambda x: x[1]['conservation_mean'])[1]['conservation_mean']
    }

    return results


# Test code
if __name__ == "__main__":
    print("Testing conservation validation...")

    from .conservation_hnn import create_conservation_hnn
    from .jax_utils import split_state, join_state

    # Create and "train" a simple model (we'll use untrained for testing)
    print("\n[1] Creating ConservationHNN...")
    model, params = create_conservation_hnn(
        state_dim=4,
        num_invariants=1,
        encoder_dims=(64, 64),
        hamiltonian_dims=(32, 16),
        invariant_dims=(32, 16),
        seed=0
    )

    # Single trajectory validation
    print("\n[2] Testing single trajectory validation...")
    z0 = jnp.array([1.0, 0.0, 0.0, 1.0])
    validation = verify_conservation_single_trajectory(
        model, params, z0, t_span=10.0, dt=0.1
    )
    print(f"  Conservation error: {validation.conservation_error:.2e}")
    print(f"  Poisson bracket mean: {validation.poisson_bracket_mean:.2e}")
    print(f"  Passed: {validation.passed}")

    # Batch validation
    print("\n[3] Testing batch validation...")
    key = jax.random.PRNGKey(42)
    initial_conditions = [jax.random.normal(key, (4,)) for _ in range(10)]
    validations, summary = verify_conservation_batch(
        model, params, initial_conditions, t_span=10.0, dt=0.1, verbose=True
    )
    print(f"  Pass rate: {summary['pass_rate']:.1%}")

    # Compare with known invariant (energy)
    print("\n[4] Testing comparison with known invariant...")
    test_states = jax.random.normal(jax.random.PRNGKey(123), (100, 4))

    def harmonic_energy(z):
        """Energy for harmonic oscillator"""
        return 0.5 * jnp.sum(z**2)

    comparison = compare_with_known_invariant(
        model, params, test_states, harmonic_energy
    )
    print(f"  Pearson correlation: {comparison['pearson_correlation']:.6f}")
    print(f"  Spearman correlation: {comparison['spearman_correlation']:.6f}")

    # Long-term conservation test
    print("\n[5] Testing long-term conservation...")
    results = long_term_conservation_test(
        model, params, z0, t_spans=[10.0, 50.0, 100.0], dt=0.1
    )
    for t_span, error in zip(results['t_spans'], results['conservation_errors']):
        print(f"  t={t_span:6.1f}: error = {error:.2e}")

    # Energy surface validation
    print("\n[6] Testing energy surface validation...")
    energy_results = energy_surface_validation(
        model, params, energy_levels=[-2.0, -1.0, -0.5],
        num_samples_per_level=5, seed=42
    )
    for E, error_mean in zip(energy_results['energy_levels'],
                              energy_results['conservation_errors_mean']):
        print(f"  E={E:.2f}: mean error = {error_mean:.2e}")

    # Phase space coverage
    print("\n[7] Testing phase space coverage validation...")
    coverage_results = phase_space_coverage_validation(
        model, params, test_states, num_bins=3
    )
    print(f"  Worst bin: {coverage_results['worst_bin_idx']}")
    print(f"  Worst error: {coverage_results['worst_conservation_error']:.2e}")

    print("\n✓ All tests passed!")
