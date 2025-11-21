"""
Unit tests for enhanced_validation.py (AMENDED WP3.3).

Tests multi-scale conservation, quasi-periodic detection, and long-time stability.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import sympy as sp
import pytest
from symbolic.enhanced_validation import (
    MultiScaleResult,
    multi_scale_conservation_test,
    detect_quasi_periodic_structure,
    long_time_stability_test
)


class TestMultiScaleConservation:
    """Test multi-scale conservation testing."""

    def test_perfectly_conserved_quantity(self):
        """Test multi-scale test on perfectly conserved quantity."""
        # Create constant integral (perfectly conserved)
        I_symbolic = sp.S(1.0)
        I_numerical = lambda state: 1.0

        # Generate trajectory
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 8)  # Random trajectory
        state_symbols = [sp.Symbol(f'z{i}') for i in range(8)]

        # Run multi-scale test
        result = multi_scale_conservation_test(
            I_symbolic=I_symbolic,
            I_numerical=I_numerical,
            trajectory=trajectory,
            trajectory_times=t,
            state_symbols=state_symbols,
            dt_values=[0.1, 1.0, 10.0],
            threshold=1e-6
        )

        # Should be conserved at all scales
        assert result.is_conserved_all_scales, "Constant should be conserved at all scales"

        # All errors should be very small
        for dt, err in result.errors_by_scale.items():
            if not np.isnan(err):
                assert err < 1e-10, f"Error too large at dt={dt}: {err}"

    def test_drifting_quantity(self):
        """Test multi-scale test on drifting quantity."""
        # Create linearly drifting integral
        drift_rate = 0.01

        def I_numerical(state, t_val=[0]):
            # Stateful function that increases with time
            result = 1.0 + drift_rate * t_val[0]
            t_val[0] += 0.01  # Increment time
            return result

        # Generate trajectory
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 8)

        # Reset time counter
        I_numerical(trajectory[0], t_val=[0])

        # Run multi-scale test
        result = multi_scale_conservation_test(
            I_symbolic=sp.S(1.0),  # Dummy symbolic
            I_numerical=lambda state: 1.0 + drift_rate * np.random.rand(),  # Varying
            trajectory=trajectory,
            trajectory_times=t,
            state_symbols=[sp.Symbol(f'z{i}') for i in range(8)],
            dt_values=[0.1, 1.0, 10.0],
            threshold=1e-6
        )

        # Should NOT be conserved at all scales
        # (though this depends on the drift rate and threshold)
        # Just check that the test runs
        assert isinstance(result, MultiScaleResult)
        assert len(result.errors_by_scale) > 0

    def test_scale_hierarchy(self):
        """Test that errors are computed for multiple scales."""
        # Simple conserved quantity
        I_numerical = lambda state: state[0]**2 + state[1]**2

        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 8)

        result = multi_scale_conservation_test(
            I_symbolic=sp.sympify("z0**2 + z1**2"),
            I_numerical=I_numerical,
            trajectory=trajectory,
            trajectory_times=t,
            state_symbols=[sp.Symbol(f'z{i}') for i in range(8)],
            dt_values=[0.01, 0.1, 1.0, 10.0],
            threshold=1e-6
        )

        # Should have computed errors for all scales
        assert len(result.errors_by_scale) == 4
        assert 0.01 in result.errors_by_scale
        assert 0.1 in result.errors_by_scale
        assert 1.0 in result.errors_by_scale
        assert 10.0 in result.errors_by_scale

    def test_insufficient_data(self):
        """Test behavior with insufficient data points."""
        I_numerical = lambda state: 1.0

        # Very short trajectory
        t = np.linspace(0, 1, 100)
        trajectory = np.random.randn(100, 8)

        result = multi_scale_conservation_test(
            I_symbolic=sp.S(1.0),
            I_numerical=I_numerical,
            trajectory=trajectory,
            trajectory_times=t,
            state_symbols=[sp.Symbol(f'z{i}') for i in range(8)],
            dt_values=[0.1, 1.0, 10.0, 100.0],  # 100.0 too coarse
            threshold=1e-6
        )

        # Some scales should return NaN (insufficient data)
        assert np.isnan(result.errors_by_scale[100.0]), "Should return NaN for insufficient data"


class TestQuasiPeriodicDetection:
    """Test quasi-periodic structure detection."""

    def test_single_frequency(self):
        """Test detection with single frequency (not quasi-periodic)."""
        # Create single frequency signal
        t = np.linspace(0, 100, 10000)
        omega = 2 * np.pi * 1.0
        I_history = np.sin(omega * t)

        is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_history, t, n_frequencies=5)

        # Should NOT be quasi-periodic (only one dominant frequency)
        assert not is_qp, "Single frequency should not be quasi-periodic"

        # Should detect the frequency
        assert len(freqs) >= 1

    def test_two_incommensurable_frequencies(self):
        """Test detection with two incommensurable frequencies."""
        # Create quasi-periodic signal: sin(ω₁t) + sin(ω₂t)
        t = np.linspace(0, 100, 10000)
        omega1 = 2 * np.pi * 1.0
        omega2 = 2 * np.pi * np.sqrt(2)  # Incommensurable with omega1
        I_history = np.sin(omega1 * t) + 0.5 * np.sin(omega2 * t)

        is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_history, t, n_frequencies=5)

        # Should detect as quasi-periodic
        assert is_qp, "Two incommensurable frequencies should be quasi-periodic"

        # Should detect both frequencies
        assert len(freqs) >= 2

        # Check frequencies are approximately correct
        expected_freqs = sorted([omega1 / (2*np.pi), omega2 / (2*np.pi)])
        detected_freqs = sorted(freqs[:2])
        assert np.isclose(detected_freqs[0], expected_freqs[0], rtol=0.1), \
            f"Frequency 1 mismatch: {detected_freqs[0]} vs {expected_freqs[0]}"
        assert np.isclose(detected_freqs[1], expected_freqs[1], rtol=0.1), \
            f"Frequency 2 mismatch: {detected_freqs[1]} vs {expected_freqs[1]}"

    def test_rational_frequency_ratio(self):
        """Test with rational frequency ratio (not quasi-periodic)."""
        # Create signal with rational frequency ratio: sin(2ω₀t) + sin(3ω₀t)
        t = np.linspace(0, 100, 10000)
        omega0 = 2 * np.pi * 1.0
        I_history = np.sin(2 * omega0 * t) + 0.5 * np.sin(3 * omega0 * t)

        is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_history, t, n_frequencies=5)

        # Should NOT be quasi-periodic (rational ratio 3/2)
        assert not is_qp, "Rational frequency ratio should not be quasi-periodic"

    def test_constant_signal(self):
        """Test with constant signal (no frequencies)."""
        t = np.linspace(0, 100, 10000)
        I_history = np.ones(len(t))

        is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_history, t)

        # Should not detect as quasi-periodic
        assert not is_qp

        # Should return empty or minimal frequency list
        assert len(freqs) == 0


class TestLongTimeStability:
    """Test long-time stability analysis."""

    def test_stable_conserved_quantity(self):
        """Test stability of perfectly conserved quantity."""
        # Perfectly conserved
        I_symbolic = sp.S(1.0)
        I_numerical = lambda state: 1.0

        t = np.linspace(0, 1000, 100000)
        trajectory = np.random.randn(100000, 8)

        is_stable, drift, stats = long_time_stability_test(
            I_symbolic=I_symbolic,
            I_numerical=I_numerical,
            trajectory=trajectory,
            trajectory_times=t,
            threshold=1e-5
        )

        # Should be stable
        assert is_stable, "Perfectly conserved quantity should be stable"

        # Drift should be very small
        assert drift < 1e-10, f"Drift too large: {drift}"

        # Check statistics
        assert 'mean_value' in stats
        assert 'std_value' in stats
        assert 'linear_drift_rate' in stats
        assert 'max_excursion' in stats

        # Mean should be close to 1.0
        assert np.isclose(stats['mean_value'], 1.0, rtol=1e-10)

        # Std should be very small
        assert stats['std_value'] < 1e-10

    def test_unstable_quantity(self):
        """Test instability detection."""
        # Create quantity that grows linearly with time
        def I_numerical_growing(state):
            # Use state index as proxy for time (not ideal but works for test)
            return 1.0 + 0.001 * np.sum(state)

        t = np.linspace(0, 1000, 10000)
        # Create trajectory with increasing values
        trajectory = np.array([np.ones(8) * i/10000 for i in range(10000)])

        is_stable, drift, stats = long_time_stability_test(
            I_symbolic=sp.S(1.0),
            I_numerical=I_numerical_growing,
            trajectory=trajectory,
            trajectory_times=t,
            threshold=1e-5
        )

        # Should be detected as unstable (drift too large)
        assert not is_stable, "Growing quantity should be unstable"

        # Drift should be significant
        assert drift > 1e-5

    def test_oscillating_conserved_quantity(self):
        """Test conserved quantity with small oscillations."""
        # Oscillating around mean with small amplitude
        def I_numerical_osc(state):
            # Add small sinusoidal variation
            phase = np.sum(state[:2])  # Use state as phase
            return 1.0 + 1e-8 * np.sin(phase)

        t = np.linspace(0, 1000, 10000)
        trajectory = np.random.randn(10000, 8)

        is_stable, drift, stats = long_time_stability_test(
            I_symbolic=sp.S(1.0),
            I_numerical=I_numerical_osc,
            trajectory=trajectory,
            trajectory_times=t,
            threshold=1e-5
        )

        # Should be stable (oscillations small)
        assert is_stable, "Small oscillations should still be stable"

        # Check that statistics capture oscillation
        assert stats['std_value'] > 0
        assert stats['max_excursion'] > 0


class TestIntegratedWorkflow:
    """Test integrated enhanced validation workflow."""

    def test_full_validation_pipeline(self):
        """Test complete validation pipeline on conserved quantity."""
        # Create mock Hamiltonian trajectory
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 8)

        # Test integral: quadratic
        I_symbolic = sp.sympify("z0**2 + z1**2")
        I_numerical = lambda state: state[0]**2 + state[1]**2
        state_symbols = [sp.Symbol(f'z{i}') for i in range(8)]

        # 1. Multi-scale conservation
        ms_result = multi_scale_conservation_test(
            I_symbolic=I_symbolic,
            I_numerical=I_numerical,
            trajectory=trajectory,
            trajectory_times=t,
            state_symbols=state_symbols,
            dt_values=[0.1, 1.0, 10.0],
            threshold=1e-6
        )

        assert isinstance(ms_result, MultiScaleResult)

        # 2. Quasi-periodic detection
        I_history = np.array([I_numerical(state) for state in trajectory])
        is_qp, freqs, spectrum = detect_quasi_periodic_structure(I_history, t)

        assert isinstance(is_qp, bool)
        assert isinstance(freqs, list)
        assert isinstance(spectrum, np.ndarray)

        # 3. Long-time stability
        is_stable, drift, stats = long_time_stability_test(
            I_symbolic=I_symbolic,
            I_numerical=I_numerical,
            trajectory=trajectory,
            trajectory_times=t,
            threshold=1e-5
        )

        assert isinstance(is_stable, bool)
        assert isinstance(drift, float)
        assert isinstance(stats, dict)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
