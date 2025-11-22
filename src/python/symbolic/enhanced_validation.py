"""
Enhanced validation for complex integrals (AMENDED WP3.3).

Extends standard validation with:
1. Multi-scale conservation testing (detect quasi-periodic motion)
2. Long-time stability analysis (100+ orbital periods)
3. Quasi-periodic structure detection (Fourier analysis)

These enhanced tests are critical for validating complex integrals involving
elliptic functions, spinor-based expressions, or other non-polynomial forms.

References:
- AMENDED_Task-3.3.3-Implementation-Plan.md
- AMENDED_WP3.3-Symbolic-Regression-Summary.md
"""

import numpy as np
import sympy as sp
from typing import Callable, List, Tuple, Dict, Optional
from dataclasses import dataclass
from scipy.integrate import solve_ivp
from scipy.fft import fft, fftfreq


@dataclass
class MultiScaleResult:
    """
    Result from multi-scale conservation testing.

    Attributes:
        is_conserved_all_scales: True if conserved at all tested scales
        errors_by_scale: Dictionary mapping dt -> max|ΔI/I|
        worst_scale: Time scale with largest conservation error
        best_scale: Time scale with smallest conservation error
    """
    is_conserved_all_scales: bool
    errors_by_scale: Dict[float, float]
    worst_scale: float
    best_scale: float


def multi_scale_conservation_test(
    I_symbolic: sp.Expr,
    I_numerical: Optional[Callable] = None,
    trajectory: Optional[np.ndarray] = None,
    trajectory_times: Optional[np.ndarray] = None,
    state_symbols: Optional[List[sp.Symbol]] = None,
    dt_values: List[float] = None,
    threshold: float = 1e-6
) -> MultiScaleResult:
    """
    Test conservation at multiple time scales.

    Physical interpretation:
    - dt=0.01: Short orbital time scale (instantaneous conservation)
    - dt=0.1: Few orbital periods (fast dynamics)
    - dt=1.0: Many orbital periods (secular drift)
    - dt=10.0: Long-time stability (chaotic divergence)

    Args:
        I_symbolic: SymPy expression for integral
        I_numerical: Numerical evaluation function (optional, computed from I_symbolic)
        trajectory: Trajectory states (N_steps, state_dim)
        trajectory_times: Time values (N_steps,)
        state_symbols: SymPy symbols for state vector
        dt_values: Time scales to test (default: [0.01, 0.1, 1.0, 10.0])
        threshold: Conservation error threshold

    Returns:
        result: MultiScaleResult with conservation errors at each scale

    Example:
        >>> # Test integral on trajectory at multiple scales
        >>> result = multi_scale_conservation_test(
        ...     I_symbolic=p_theta,  # Fiber momentum
        ...     trajectory=traj_data,
        ...     trajectory_times=t_data,
        ...     state_symbols=state_syms,
        ...     dt_values=[0.1, 1.0, 10.0]
        ... )
        >>> print(f"Conserved at all scales: {result.is_conserved_all_scales}")
        >>> print(f"Worst error: {result.errors_by_scale[result.worst_scale]:.2e}")
    """
    if dt_values is None:
        dt_values = [0.01, 0.1, 1.0, 10.0]

    # Create numerical function if not provided
    if I_numerical is None:
        from .validation import lambdify_expression
        I_numerical = lambdify_expression(I_symbolic, state_symbols)

    errors_by_scale = {}

    for dt in dt_values:
        # Subsample trajectory at this time scale
        time_step = trajectory_times[1] - trajectory_times[0]
        subsample_stride = max(1, int(dt / time_step))

        subsampled_trajectory = trajectory[::subsample_stride]
        subsampled_times = trajectory_times[::subsample_stride]

        if len(subsampled_trajectory) < 10:
            # Not enough points for meaningful test
            errors_by_scale[dt] = np.nan
            continue

        # Evaluate integral along subsampled trajectory
        I_values = np.array([I_numerical(state) for state in subsampled_trajectory])

        # Compute conservation error
        I_mean = np.mean(I_values)
        I_max = np.max(I_values)
        I_min = np.min(I_values)

        if abs(I_mean) > 1e-12:
            drift = (I_max - I_min) / abs(I_mean)
        else:
            # Integral near zero - use absolute drift
            drift = I_max - I_min

        errors_by_scale[dt] = drift

    # Find worst and best scales
    valid_errors = {dt: err for dt, err in errors_by_scale.items() if not np.isnan(err)}
    if valid_errors:
        worst_scale = max(valid_errors, key=valid_errors.get)
        best_scale = min(valid_errors, key=valid_errors.get)
        is_conserved_all_scales = all(err < threshold for err in valid_errors.values())
    else:
        worst_scale = dt_values[0]
        best_scale = dt_values[0]
        is_conserved_all_scales = False

    return MultiScaleResult(
        is_conserved_all_scales=is_conserved_all_scales,
        errors_by_scale=errors_by_scale,
        worst_scale=worst_scale,
        best_scale=best_scale
    )


def detect_quasi_periodic_structure(
    I_history: np.ndarray,
    times: np.ndarray,
    n_frequencies: int = 5
) -> Tuple[bool, List[float], np.ndarray]:
    """
    Detect if integral has quasi-periodic structure via Fourier analysis.

    Quasi-periodic functions have two (or more) incommensurable frequencies:
    - f(t) = F(ω₁·t, ω₂·t) where ω₁/ω₂ is irrational
    - Appear in integrable systems with multiple conserved quantities
    - Motivates search for theta functions (doubly periodic)

    Args:
        I_history: Integral values over time (N,)
        times: Time values (N,)
        n_frequencies: Number of dominant frequencies to return

    Returns:
        is_quasi_periodic: True if two dominant incommensurable frequencies found
        dominant_frequencies: List of dominant frequencies (sorted by power)
        power_spectrum: Full power spectrum for visualization

    Example:
        >>> is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_vals, t_vals)
        >>> if is_qp:
        ...     print(f"Quasi-periodic with frequencies: {freqs[:2]}")
    """
    # Compute FFT
    N = len(I_history)
    dt = times[1] - times[0]
    yf = fft(I_history - np.mean(I_history))  # Remove DC component
    xf = fftfreq(N, dt)[:N//2]
    power = 2.0/N * np.abs(yf[:N//2])

    # Find dominant frequencies
    threshold = 0.1 * np.max(power)  # 10% of max power
    peaks_idx = np.where(power > threshold)[0]

    if len(peaks_idx) == 0:
        return False, [], power

    peaks_freqs = xf[peaks_idx]
    peaks_power = power[peaks_idx]

    # Sort by power
    sorted_idx = np.argsort(peaks_power)[::-1]
    dominant_freqs = peaks_freqs[sorted_idx[:min(n_frequencies, len(peaks_freqs))]]

    # Check for two incommensurable frequencies
    is_quasi_periodic = False
    if len(dominant_freqs) >= 2:
        f1, f2 = dominant_freqs[0], dominant_freqs[1]
        if f2 != 0:
            ratio = f1 / f2

            # Check if ratio is irrational (approximately)
            # Rational if ratio ≈ p/q for small integers p, q
            is_rational = False
            for p in range(1, 10):
                for q in range(1, 10):
                    if abs(ratio - p/q) < 0.01:
                        is_rational = True
                        break
                if is_rational:
                    break

            is_quasi_periodic = not is_rational

    return is_quasi_periodic, dominant_freqs.tolist(), power


def long_time_stability_test(
    I_symbolic: sp.Expr,
    I_numerical: Callable,
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    threshold: float = 1e-5
) -> Tuple[bool, float, Dict]:
    """
    Test conservation stability over long time integration.

    Args:
        I_symbolic: Integral expression
        I_numerical: Numerical evaluation function
        trajectory: Long trajectory (preferably 100+ orbital periods)
        trajectory_times: Time values
        threshold: Acceptable drift |ΔI/I|

    Returns:
        is_stable: True if drift < threshold
        drift: Measured max|ΔI/I| over trajectory
        statistics: Dictionary with detailed statistics

    Statistics include:
    - mean_value: Mean of I over trajectory
    - std_value: Standard deviation
    - linear_drift: Linear trend (fitted slope)
    - max_excursion: Maximum deviation from mean
    """
    # Evaluate integral along trajectory
    I_history = np.array([I_numerical(state) for state in trajectory])

    # Compute drift
    I0 = I_history[0]
    I_mean = np.mean(I_history)
    I_std = np.std(I_history)

    if abs(I0) > 1e-12:
        drift = np.max(np.abs(I_history - I0)) / abs(I0)
    else:
        drift = np.max(np.abs(I_history - I0))

    # Compute linear trend
    from numpy.polynomial import Polynomial
    p = Polynomial.fit(trajectory_times, I_history, 1)
    linear_drift_rate = abs(p.coef[1]) / (abs(I_mean) + 1e-12)

    statistics = {
        'mean_value': float(I_mean),
        'std_value': float(I_std),
        'linear_drift_rate': float(linear_drift_rate),
        'max_excursion': float(np.max(np.abs(I_history - I_mean))),
        'relative_std': float(I_std / (abs(I_mean) + 1e-12)),
        'n_periods_estimate': len(trajectory) / 100  # Rough estimate
    }

    is_stable = drift < threshold

    return is_stable, drift, statistics


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Enhanced Validation Module - Tests")
    print("=" * 70)

    # Test 1: Multi-scale conservation (synthetic data)
    print("\nTest 1: Multi-scale conservation testing")
    print("-" * 70)

    # Create synthetic conserved quantity (constant)
    t = np.linspace(0, 100, 10000)
    traj = np.random.randn(10000, 4)  # Random trajectory
    I_const = lambda state: 1.0  # Perfectly conserved

    result = multi_scale_conservation_test(
        I_symbolic=sp.S(1.0),  # Constant
        I_numerical=I_const,
        trajectory=traj,
        trajectory_times=t,
        dt_values=[0.1, 1.0, 10.0]
    )

    print(f"  Conserved at all scales: {result.is_conserved_all_scales}")
    print(f"  Errors by scale:")
    for dt, err in sorted(result.errors_by_scale.items()):
        print(f"    dt={dt:5.2f}: error={err:.2e}")

    # Test 2: Quasi-periodic detection
    print("\nTest 2: Quasi-periodic structure detection")
    print("-" * 70)

    # Create quasi-periodic signal: f(t) = sin(ω₁t) + sin(ω₂t)
    omega1, omega2 = 2*np.pi * 1.0, 2*np.pi * np.sqrt(2)  # Incommensurable
    I_qp = np.sin(omega1 * t) + 0.5 * np.sin(omega2 * t)

    is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_qp, t)

    print(f"  Is quasi-periodic: {is_qp}")
    print(f"  Dominant frequencies: {freqs[:3]}")
    if len(freqs) >= 2:
        print(f"  Frequency ratio: {freqs[0]/freqs[1]:.6f}")

    # Test 3: Long-time stability
    print("\nTest 3: Long-time stability testing")
    print("-" * 70)

    # Perfectly conserved
    I_perfect = np.ones(len(t)) + 1e-10 * np.random.randn(len(t))  # Small noise
    is_stable, drift, stats = long_time_stability_test(
        I_symbolic=sp.S(1.0),
        I_numerical=lambda s: 1.0,
        trajectory=traj,
        trajectory_times=t,
        threshold=1e-5
    )

    print(f"  Is stable: {is_stable}")
    print(f"  Drift: {drift:.2e}")
    print(f"  Statistics:")
    for key, val in stats.items():
        print(f"    {key}: {val:.2e}")

    print("\n" + "=" * 70)
    print("All tests complete")
    print("=" * 70)
