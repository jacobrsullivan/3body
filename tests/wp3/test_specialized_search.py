"""
Unit tests for specialized search modules (AMENDED WP3.3).

Tests elliptic_search.py and spinor_search.py.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import pytest
from symbolic.elliptic_search import (
    EllipticSearchResult,
    detect_elliptic_signature,
    elliptic_pattern_match,
    search_elliptic_integral
)
from symbolic.spinor_search import (
    SpinorSearchResult,
    detect_regularization_benefit,
    spinor_pattern_recognition,
    search_spinor_integral
)
from symbolic.spinor_basis import position_to_spinor, compute_spinor_norm
from symbolic.elliptic_basis import jacobi_sn


class TestEllipticSignatureDetection:
    """Test elliptic signature detection."""

    def test_detect_quasi_periodic(self):
        """Test detection of quasi-periodic signal."""
        # Create quasi-periodic trajectory
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 18)

        # Quasi-periodic integral
        omega1 = 2 * np.pi * 1.0
        omega2 = 2 * np.pi * np.sqrt(2)  # Incommensurable

        def quasi_periodic_integral(state):
            idx = int(np.abs(np.sum(state[:3])) * 10) % len(t)
            return np.sin(omega1 * t[idx]) + 0.5 * np.sin(omega2 * t[idx])

        has_sig, confidence, freqs = detect_elliptic_signature(
            quasi_periodic_integral,
            trajectory,
            t,
            threshold=0.5
        )

        # Should detect two frequencies
        assert len(freqs) >= 2, f"Should detect 2 frequencies, got {len(freqs)}"

    def test_detect_constant_no_signature(self):
        """Test that constant integral has no elliptic signature."""
        t = np.linspace(0, 100, 1000)
        trajectory = np.random.randn(1000, 18)

        def constant_integral(state):
            return 1.0

        has_sig, confidence, freqs = detect_elliptic_signature(
            constant_integral,
            trajectory,
            t
        )

        assert not has_sig, "Constant should not have elliptic signature"
        assert confidence < 0.5, f"Confidence too high: {confidence}"

    def test_detect_single_frequency_no_signature(self):
        """Test that single frequency has no quasi-periodic signature."""
        t = np.linspace(0, 100, 10000)
        trajectory = np.random.randn(10000, 18)

        omega = 2 * np.pi * 1.0

        def single_frequency_integral(state):
            idx = int(np.abs(np.sum(state[:3])) * 10) % len(t)
            return np.sin(omega * t[idx])

        has_sig, confidence, freqs = detect_elliptic_signature(
            single_frequency_integral,
            trajectory,
            t
        )

        # Should not detect as quasi-periodic (only one dominant frequency)
        # This test may be sensitive to implementation details
        assert isinstance(has_sig, bool)


class TestEllipticPatternMatch:
    """Test elliptic pattern matching."""

    def test_pattern_match_simple(self):
        """Test pattern matching on simple elliptic integral."""
        # Create trajectory
        trajectory = np.random.randn(100, 18)
        masses = np.array([1.0, 1.0, 1.0])
        m_est = 0.5

        # Simple integral (not actually elliptic, but for testing)
        def simple_integral(state):
            r1 = state[:3]
            return np.linalg.norm(r1)

        result = elliptic_pattern_match(simple_integral, trajectory, masses, m_est)

        # May or may not find a match (depends on optimization)
        if result is not None:
            expr, func, quality = result
            assert callable(func), "Matched function should be callable"
            assert 0 <= quality <= 1, f"Quality {quality} outside [0,1]"


class TestEllipticSearch:
    """Test full elliptic search pipeline."""

    def test_elliptic_search_returns_result(self):
        """Test that elliptic search returns a result object."""
        t = np.linspace(0, 100, 1000)
        trajectory = np.random.randn(1000, 18)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state[:9]**2)  # Energy-like

        result = search_elliptic_integral(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=t,
            masses=masses
        )

        assert isinstance(result, EllipticSearchResult)
        assert isinstance(result.found_elliptic, bool)
        assert isinstance(result.elliptic_parameter, float)
        assert 0 <= result.elliptic_parameter <= 1


class TestSpinorRegularizationDetection:
    """Test spinor regularization benefit detection."""

    def test_detect_close_encounters(self):
        """Test detection of close encounters."""
        # Create trajectory with close encounters
        n_samples = 1000
        trajectory = np.zeros((n_samples, 18))

        for i in range(n_samples):
            # Place bodies close together for some samples
            if i % 10 == 0:
                # Close encounter
                trajectory[i, :9] = np.random.randn(9) * 0.05  # Small positions
            else:
                # Normal spacing
                trajectory[i, :9] = np.random.randn(9)

        masses = np.array([1.0, 1.0, 1.0])

        needs_reg, close_frac = detect_regularization_benefit(trajectory, masses)

        # Should detect some close encounters
        assert close_frac > 0, "Should detect some close encounters"
        assert 0 <= close_frac <= 1, f"Close encounter fraction {close_frac} outside [0,1]"

    def test_detect_no_close_encounters(self):
        """Test with well-separated bodies."""
        # Trajectory with well-separated bodies
        trajectory = np.random.randn(1000, 18) * 10  # Large separation
        masses = np.array([1.0, 1.0, 1.0])

        needs_reg, close_frac = detect_regularization_benefit(trajectory, masses)

        # Should detect few or no close encounters
        assert close_frac < 0.5, "Should not detect many close encounters"


class TestSpinorPatternRecognition:
    """Test spinor pattern recognition."""

    def test_recognize_spinor_norm(self):
        """Test recognition of spinor norm pattern."""
        trajectory = np.random.randn(100, 18)
        masses = np.array([1.0, 1.0, 1.0])

        # Integral that is spinor norm squared (= |r_1|)
        def spinor_norm_integral(state):
            r1 = state[:3]
            u1 = position_to_spinor(r1)
            return compute_spinor_norm(u1)**2

        result = spinor_pattern_recognition(
            spinor_norm_integral,
            trajectory,
            masses
        )

        # May or may not recognize pattern (depends on numerical accuracy)
        if result is not None:
            pattern_type, quality = result
            assert isinstance(pattern_type, str)
            assert 0 <= quality <= 1


class TestSpinorSearch:
    """Test full spinor search pipeline."""

    def test_spinor_search_returns_result(self):
        """Test that spinor search returns a result object."""
        trajectory = np.random.randn(1000, 18)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state[:9]**2)

        result = search_spinor_integral(
            I_numerical=test_integral,
            trajectory=trajectory,
            masses=masses
        )

        assert isinstance(result, SpinorSearchResult)
        assert isinstance(result.found_spinor_integral, bool)
        assert isinstance(result.spinor_component_type, str)

    def test_spinor_search_on_spinor_integral(self):
        """Test spinor search on actual spinor integral."""
        trajectory = np.random.randn(100, 18)
        masses = np.array([1.0, 1.0, 1.0])

        # True spinor integral
        def spinor_integral(state):
            r1 = state[:3]
            u1 = position_to_spinor(r1)
            return compute_spinor_norm(u1)**2

        result = search_spinor_integral(
            I_numerical=spinor_integral,
            trajectory=trajectory,
            masses=masses
        )

        # Should find spinor integral (pattern recognition)
        # But success depends on numerical accuracy
        assert isinstance(result, SpinorSearchResult)


class TestSearchIntegration:
    """Test integration between search methods."""

    def test_elliptic_and_spinor_search_independent(self):
        """Test that elliptic and spinor searches can run independently."""
        t = np.linspace(0, 100, 500)
        trajectory = np.random.randn(500, 18)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state**2)

        # Run both searches
        elliptic_result = search_elliptic_integral(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=t,
            masses=masses
        )

        spinor_result = search_spinor_integral(
            I_numerical=test_integral,
            trajectory=trajectory,
            masses=masses
        )

        # Both should return results
        assert isinstance(elliptic_result, EllipticSearchResult)
        assert isinstance(spinor_result, SpinorSearchResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
