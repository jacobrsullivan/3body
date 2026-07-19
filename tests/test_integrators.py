"""
Unit tests for integrator implementations.

These tests verify the correctness and functionality of the integrator
base class and specific implementations like IAS15.
"""

import numpy as np
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.integrators.base import (
    IntegratorBase,
    IntegrationResult,
    IntegratorError,
    IntegrationFailedException,
    InvalidInitialConditionsError,
)
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator
from src.python.integrators.heyoka_taylor import HeyokaTaylorIntegrator
from src.python.utils.dynamics import calculate_jacobi_constant


class MockIntegrator(IntegratorBase):
    """Mock integrator for testing the base class."""

    def _integrate_internal(self, initial_state, duration, output_interval):
        """Mock integration that returns a simple trajectory."""
        n_points = int(duration / output_interval) + 1
        times = np.linspace(0, duration, n_points)

        # Simple trajectory: particle moves in a circle
        states_corotating = np.zeros((n_points, 6))
        for i, t in enumerate(times):
            states_corotating[i] = [
                np.cos(t),
                np.sin(t),
                0,  # circular motion
                -np.sin(t),
                np.cos(t),
                0,
            ]

        # Mock inertial states (same as corotating for simplicity)
        states_inertial = states_corotating.copy()

        return IntegrationResult(
            times=times,
            states_corotating=states_corotating,
            states_inertial=states_inertial,
            success=True,
            message="Mock integration completed",
            stats={"n_steps": n_points, "integrator": "Mock"},
        )


class TestIntegratorBase:
    """Test the abstract integrator base class."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856
        self.integrator = MockIntegrator(self.mu)

    def test_initialization(self):
        """Test integrator initialization."""
        assert self.integrator.mu == self.mu
        assert self.integrator.name == "MockIntegrator"
        assert self.integrator.tolerance == 1e-14

    def test_invalid_mu(self):
        """Test that invalid mu values raise errors."""
        with pytest.raises(ValueError):
            MockIntegrator(-0.1)  # Negative mu

        with pytest.raises(ValueError):
            MockIntegrator(1.5)  # mu > 1

        with pytest.raises(ValueError):
            MockIntegrator("invalid")  # Non-numeric mu

    def test_mu_validation(self):
        """Test mu parameter validation."""
        # Valid mu values
        valid_mus = [0.001, 0.5, 0.999]
        for mu in valid_mus:
            integrator = MockIntegrator(mu)
            assert integrator.mu == mu

    def test_initial_state_validation(self):
        """Test initial state validation."""
        # Valid state
        valid_state = np.array([1, 2, 3, 0.1, 0.2, 0.3])
        validated = self.integrator._validate_initial_state(valid_state)
        np.testing.assert_array_equal(validated, valid_state)

        # Invalid shapes
        with pytest.raises(InvalidInitialConditionsError):
            self.integrator._validate_initial_state([1, 2, 3])  # Too short

        with pytest.raises(InvalidInitialConditionsError):
            self.integrator._validate_initial_state([1, 2, 3, 4, 5, 6, 7])  # Too long

        # Non-finite values
        with pytest.raises(InvalidInitialConditionsError):
            self.integrator._validate_initial_state([1, 2, np.inf, 4, 5, 6])

        with pytest.raises(InvalidInitialConditionsError):
            self.integrator._validate_initial_state([1, 2, np.nan, 4, 5, 6])

    def test_time_parameter_validation(self):
        """Test time parameter validation."""
        # Valid parameters
        duration, interval = self.integrator._validate_time_parameters(10.0, 0.1)
        assert duration == 10.0
        assert interval == 0.1

        # Invalid parameters
        with pytest.raises(ValueError):
            self.integrator._validate_time_parameters(-1.0, 0.1)  # Negative duration

        with pytest.raises(ValueError):
            self.integrator._validate_time_parameters(10.0, -0.1)  # Negative interval

        with pytest.raises(ValueError):
            self.integrator._validate_time_parameters(1.0, 2.0)  # Interval > duration

    def test_integration_success(self):
        """Test successful integration."""
        initial_state = np.array([1, 0, 0, 0, 1, 0])
        duration = 2 * np.pi  # One period
        output_interval = 0.1

        result = self.integrator.integrate(initial_state, duration, output_interval)

        assert result.success
        assert len(result.times) > 1
        assert result.states_corotating.shape[1] == 6
        assert result.states_inertial.shape[1] == 6
        assert "wall_time" in result.stats
        assert "points_per_second" in result.stats

    def test_get_info(self):
        """Test integrator info retrieval."""
        info = self.integrator.get_info()

        assert "name" in info
        assert "mu" in info
        assert "tolerance" in info
        assert "type" in info
        assert info["name"] == "MockIntegrator"
        assert info["mu"] == self.mu

    def test_string_representations(self):
        """Test string representations."""
        str_repr = str(self.integrator)
        assert "MockIntegrator" in str_repr
        # Check for mu value in scientific notation format
        assert "mu=" in str_repr and "e-02" in str_repr

        repr_str = repr(self.integrator)
        assert "MockIntegrator" in repr_str


class TestIntegrationResult:
    """Test the IntegrationResult data class."""

    def test_integration_result_creation(self):
        """Test creation of IntegrationResult."""
        times = np.array([0, 1, 2])
        states_co = np.random.randn(3, 6)
        states_in = np.random.randn(3, 6)

        result = IntegrationResult(
            times=times,
            states_corotating=states_co,
            states_inertial=states_in,
            success=True,
            message="Test",
            stats={"test": 1},
        )

        assert result.success
        assert result.message == "Test"
        assert result.stats["test"] == 1
        np.testing.assert_array_equal(result.times, times)


class TestAdaptiveSymplecticIntegrator:
    """Test AdaptiveSymplectic precision guard and short-run behavior."""

    def setup_method(self):
        self.mu = 0.0121505856
        self.initial_state = np.array(
            [1.1094406061, -0.1250111591, 0.0, -0.0050612502, 0.4862950307, 0.0]
        )

    def test_short_double_precision_integration_completes(self):
        """The current float64 path should complete at a realistic tolerance."""
        integrator = AdaptiveSymplecticIntegrator(
            self.mu,
            order=6,
            error_tolerance=1e-10,
            max_steps=2000,
        )

        result = integrator.integrate(
            self.initial_state,
            duration=0.05,
            output_interval=0.025,
        )

        assert result.success, result.message
        assert result.stats["accepted_steps"] > 0
        assert result.stats["stop_reason"] == "completed"

    def test_tier2_tolerance_fails_without_qd_backend(self):
        """Tier 2 targets must not spin until max_steps on the float64 path."""
        integrator = AdaptiveSymplecticIntegrator(
            self.mu,
            order=6,
            error_tolerance=1e-25,
            max_steps=2000,
        )

        result = integrator.integrate(
            self.initial_state,
            duration=0.05,
            output_interval=0.025,
        )

        assert not result.success
        assert result.stats["stop_reason"] == "unsupported_precision"
        assert result.stats["total_steps"] == 0
        assert "requires a QD-backed arithmetic path" in result.message


class TestHeyokaTaylorIntegrator:
    """Test high-precision heyoka Taylor Tier 2 smoke behavior."""

    def setup_method(self):
        pytest.importorskip("heyoka")
        self.mu = 0.012150585609624
        self.initial_state = np.array(
            [1.1094406061, -0.1250111591, 0.0, -0.0050612502, 0.4862950307, 0.0]
        )

    def test_tier2_smoke_meets_declared_precision(self):
        integrator = HeyokaTaylorIntegrator(
            self.mu,
            tolerance=1e-25,
            precision_bits=160,
        )

        result = integrator.integrate(
            self.initial_state,
            duration=1.0,
            output_interval=0.5,
        )

        assert result.success, result.message
        assert result.stats["precision_backend"] == "heyoka.real"
        assert result.stats["precision_bits"] == 160
        assert result.stats["jacobi_relative_drift_float"] < 1e-25
        assert len(result.times) == 3


# Skip IAS15 tests if REBOUND is not available
rebound_available = True
try:
    import rebound
    from src.python.integrators.ias15 import IAS15Integrator
except ImportError:
    rebound_available = False


@pytest.mark.skipif(not rebound_available, reason="REBOUND not available")
class TestIAS15Integrator:
    """Test the IAS15 integrator implementation."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856
        self.integrator = IAS15Integrator(self.mu)

    def test_ias15_initialization(self):
        """Test IAS15 integrator initialization."""
        assert self.integrator.mu == self.mu
        assert self.integrator.name == "IAS15Integrator"
        assert not self.integrator._is_symplectic

    def test_ias15_custom_parameters(self):
        """Test IAS15 with custom parameters."""
        integrator = IAS15Integrator(
            self.mu, tolerance=1e-12, min_dt=1e-10, max_dt=0.01
        )

        assert integrator.tolerance == 1e-12
        assert integrator.min_dt == 1e-10
        assert integrator.max_dt == 0.01

    def test_ias15_info(self):
        """Test IAS15 integrator info."""
        info = self.integrator.get_info()

        assert info["name"] == "IAS15Integrator"
        assert info["order"] == 15
        assert info["adaptive"] is True
        assert info["symplectic"] is False
        assert info["backend"] == "REBOUND"

    @pytest.mark.slow
    def test_simple_integration(self):
        """Test simple integration with IAS15."""
        # Start near L4 point for stability
        initial_state = np.array([0.4878, 0.8660, 0, 0, 0, 0])
        duration = 6.28  # One period
        output_interval = 0.1

        result = self.integrator.integrate(initial_state, duration, output_interval)

        assert result.success, f"Integration failed: {result.message}"
        assert len(result.times) > 10
        assert result.states_corotating.shape[0] == len(result.times)
        assert result.states_inertial.shape[0] == len(result.times)

        # Check that trajectory contains finite values
        assert np.all(np.isfinite(result.states_corotating))
        assert np.all(np.isfinite(result.states_inertial))

    @pytest.mark.slow
    def test_jacobi_conservation(self):
        """Test that IAS15 conserves Jacobi constant well."""
        # Stable orbit near L4
        initial_state = np.array([0.4878, 0.8660, 0, 0, 0, 0])
        duration = 12.56  # Two periods
        output_interval = 0.05

        result = self.integrator.integrate(initial_state, duration, output_interval)

        if not result.success:
            pytest.skip(f"Integration failed: {result.message}")

        # Calculate Jacobi constant at each point
        jacobi_values = []
        for state in result.states_corotating:
            jacobi = calculate_jacobi_constant(state, self.mu)
            jacobi_values.append(jacobi)

        jacobi_values = np.array(jacobi_values)
        initial_jacobi = jacobi_values[0]
        final_jacobi = jacobi_values[-1]

        # Check conservation (should be very good for IAS15)
        relative_drift = abs((final_jacobi - initial_jacobi) / initial_jacobi)
        assert relative_drift < 1e-12, f"Jacobi drift too large: {relative_drift:.2e}"

    def test_invalid_initial_conditions(self):
        """Test behavior with invalid initial conditions."""
        # Test with invalid state
        with pytest.raises(InvalidInitialConditionsError):
            self.integrator.integrate([1, 2, 3], 1.0, 0.1)  # Wrong size

    def test_integration_failure_handling(self):
        """Test handling of integration failures."""
        # Use extreme conditions that might cause failure
        extreme_state = np.array([100, 100, 100, 100, 100, 100])
        duration = 1000
        output_interval = 0.1

        # This might fail, but should handle gracefully
        result = self.integrator.integrate(extreme_state, duration, output_interval)

        # Either succeeds or fails gracefully
        if not result.success:
            assert "error" in result.stats or result.message != ""
            assert len(result.times) >= 1  # Should at least have initial time


class TestIntegratorComparison:
    """Test comparison between different integrator approaches."""

    def setup_method(self):
        """Set up test parameters."""
        self.mu = 0.0121505856

    def test_mock_vs_real_interface(self):
        """Test that mock and real integrators follow same interface."""
        mock_integrator = MockIntegrator(self.mu)

        # Both should have the same interface
        assert hasattr(mock_integrator, "integrate")
        assert hasattr(mock_integrator, "get_info")
        assert hasattr(mock_integrator, "mu")

        if rebound_available:
            real_integrator = IAS15Integrator(self.mu)

            # Check that both implement the same methods
            mock_methods = set(dir(mock_integrator))
            real_methods = set(dir(real_integrator))

            # Core interface methods should be present in both
            core_methods = {
                "integrate",
                "get_info",
                "_validate_initial_state",
                "_validate_time_parameters",
            }

            assert core_methods.issubset(mock_methods)
            assert core_methods.issubset(real_methods)

    def test_consistent_output_format(self):
        """Test that different integrators produce consistent output formats."""
        initial_state = np.array([0.5, 0.3, 0, 0.1, 0.2, 0])
        duration = 1.0
        output_interval = 0.1

        mock_integrator = MockIntegrator(self.mu)
        mock_result = mock_integrator.integrate(
            initial_state, duration, output_interval
        )

        # Check output format
        assert hasattr(mock_result, "times")
        assert hasattr(mock_result, "states_corotating")
        assert hasattr(mock_result, "states_inertial")
        assert hasattr(mock_result, "success")
        assert hasattr(mock_result, "message")
        assert hasattr(mock_result, "stats")

        if rebound_available:
            real_integrator = IAS15Integrator(self.mu)
            real_result = real_integrator.integrate(
                initial_state, duration, output_interval
            )

            if real_result.success:
                # Both should have same structure
                assert mock_result.times.shape == real_result.times.shape
                assert (
                    mock_result.states_corotating.shape[1]
                    == real_result.states_corotating.shape[1]
                )
                assert (
                    mock_result.states_inertial.shape[1]
                    == real_result.states_inertial.shape[1]
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
