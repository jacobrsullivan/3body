"""
Tests for Sundman time transformations.

Tests various time dilation strategies for regularization.
"""

import pytest
import numpy as np

from src.python.regularization.sundman import (
    TimeTransformationStrategy,
    compute_time_dilation_single,
    compute_time_dilation_threebody,
    compute_time_dilation_from_spinors,
    SundmanTransformation,
    integrate_physical_time,
    compute_effective_timestep
)


class TestSingleBodyTimeDilation:
    """Test time dilation for single pair"""

    def test_standard_sundman(self):
        """Test standard Sundman transformation"""
        r = 2.5
        Omega = compute_time_dilation_single(r, TimeTransformationStrategy.STANDARD)

        assert np.isclose(Omega, r)

    def test_ks_single(self):
        """Test KS time dilation for single pair"""
        r = 3.0
        Omega = compute_time_dilation_single(r, TimeTransformationStrategy.KS_SINGLE)

        # For single pair, KS uses Ω = r (same as standard)
        assert np.isclose(Omega, r)

    def test_negative_radius_fails(self):
        """Test that negative radius raises error"""
        with pytest.raises(ValueError, match="positive"):
            compute_time_dilation_single(-1.0)


class TestThreeBodyTimeDilation:
    """Test time dilation for three-body problem"""

    def test_sum_strategy(self):
        """Test sum strategy: Ω = r₁₂ + r₂₃ + r₃₁"""
        r12, r23, r31 = 1.0, 2.0, 3.0

        result = compute_time_dilation_threebody(
            r12, r23, r31,
            TimeTransformationStrategy.SUM
        )

        assert np.isclose(result.Omega, 6.0)
        assert result.strategy == TimeTransformationStrategy.SUM
        assert result.radii == (1.0, 2.0, 3.0)

    def test_product_strategy(self):
        """Test product strategy: Ω = r₁₂ · r₂₃ · r₃₁"""
        r12, r23, r31 = 2.0, 3.0, 4.0

        result = compute_time_dilation_threebody(
            r12, r23, r31,
            TimeTransformationStrategy.PRODUCT
        )

        assert np.isclose(result.Omega, 24.0)  # 2 · 3 · 4 = 24

    def test_min_strategy(self):
        """Test min strategy: Ω = min(r₁₂, r₂₃, r₃₁)"""
        r12, r23, r31 = 2.0, 1.0, 3.0

        result = compute_time_dilation_threebody(
            r12, r23, r31,
            TimeTransformationStrategy.MIN
        )

        assert np.isclose(result.Omega, 1.0)  # min(2, 1, 3) = 1

    def test_weighted_sum_strategy(self):
        """Test weighted sum strategy"""
        r12, r23, r31 = 1.0, 2.0, 3.0
        weights = np.array([0.5, 0.3, 0.2])

        result = compute_time_dilation_threebody(
            r12, r23, r31,
            TimeTransformationStrategy.WEIGHTED_SUM,
            weights=weights
        )

        expected = 0.5*1.0 + 0.3*2.0 + 0.2*3.0  # = 1.7
        assert np.isclose(result.Omega, expected)

    def test_weighted_sum_requires_weights(self):
        """Test that weighted sum fails without weights"""
        with pytest.raises(ValueError, match="requires weights"):
            compute_time_dilation_threebody(
                1.0, 2.0, 3.0,
                TimeTransformationStrategy.WEIGHTED_SUM
            )

    def test_metadata_included(self):
        """Test that result includes metadata"""
        result = compute_time_dilation_threebody(
            1.0, 2.0, 3.0,
            TimeTransformationStrategy.SUM
        )

        assert 'min_radius' in result.metadata
        assert 'max_radius' in result.metadata
        assert result.metadata['min_radius'] == 1.0
        assert result.metadata['max_radius'] == 3.0


class TestSpinorTimeDilation:
    """Test time dilation from spinor coordinates"""

    def test_compute_from_spinors(self):
        """Test computing Ω from spinor coordinates"""
        # Create spinors with known radii
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # ‖u₁₂‖² = 1
        u23 = np.array([np.sqrt(2), 0.0, 0.0, 0.0])  # ‖u₂₃‖² = 2
        u31 = np.array([np.sqrt(3), 0.0, 0.0, 0.0])  # ‖u₃₁‖² = 3

        result = compute_time_dilation_from_spinors(
            u12, u23, u31,
            TimeTransformationStrategy.SUM
        )

        assert np.isclose(result.Omega, 6.0)  # 1 + 2 + 3 = 6


class TestSundmanTransformation:
    """Test SundmanTransformation callable class"""

    def test_single_pair_callable(self):
        """Test using transformation as callable for single pair"""
        transform = SundmanTransformation(TimeTransformationStrategy.STANDARD)

        Omega = transform(2.5)
        assert np.isclose(Omega, 2.5)

    def test_threebody_callable(self):
        """Test using transformation for three-body"""
        transform = SundmanTransformation(TimeTransformationStrategy.SUM)

        Omega = transform(1.0, 2.0, 3.0)
        assert np.isclose(Omega, 6.0)

    def test_derivative_single_pair(self):
        """Test derivative for single pair"""
        transform = SundmanTransformation(TimeTransformationStrategy.STANDARD)

        # For Ω = r, ∂Ω/∂r = 1
        grad = transform.compute_derivative(2.0)
        assert np.allclose(grad, [1.0])

    def test_derivative_sum_strategy(self):
        """Test derivative for sum strategy"""
        transform = SundmanTransformation(TimeTransformationStrategy.SUM)

        # For Ω = r₁₂ + r₂₃ + r₃₁, ∂Ω/∂rᵢⱼ = 1
        grad = transform.compute_derivative(1.0, 2.0, 3.0)
        assert np.allclose(grad, [1.0, 1.0, 1.0])

    def test_derivative_product_strategy(self):
        """Test derivative for product strategy"""
        transform = SundmanTransformation(TimeTransformationStrategy.PRODUCT)

        r12, r23, r31 = 2.0, 3.0, 4.0
        grad = transform.compute_derivative(r12, r23, r31)

        # ∂(r₁₂·r₂₃·r₃₁)/∂r₁₂ = r₂₃·r₃₁ = 12
        # ∂(r₁₂·r₂₃·r₃₁)/∂r₂₃ = r₁₂·r₃₁ = 8
        # ∂(r₁₂·r₂₃·r₃₁)/∂r₃₁ = r₁₂·r₂₃ = 6
        expected = [12.0, 8.0, 6.0]
        assert np.allclose(grad, expected)

    def test_invalid_number_of_radii(self):
        """Test that invalid number of radii fails"""
        transform = SundmanTransformation(TimeTransformationStrategy.SUM)

        with pytest.raises(ValueError, match="Expected 1 or 3"):
            transform(1.0, 2.0)  # 2 radii is invalid


class TestPhysicalTimeIntegration:
    """Test integration of physical time from fictitious time"""

    def test_constant_dilation(self):
        """Test integration with constant Ω = 1"""
        s_values = np.linspace(0, 1, 11)
        Omega_values = np.ones_like(s_values)

        t_values = integrate_physical_time(s_values, Omega_values, t_initial=0.0)

        # For constant Ω = 1, should have t = s
        assert np.allclose(t_values, s_values)

    def test_linear_dilation(self):
        """Test with linearly increasing Ω"""
        s_values = np.linspace(0, 1, 101)
        Omega_values = 1 + s_values  # Linear: Ω(s) = 1 + s

        t_values = integrate_physical_time(s_values, Omega_values, t_initial=0.0)

        # Integral of (1 + s) from 0 to s is: s + s²/2
        t_expected = s_values + s_values**2 / 2
        assert np.allclose(t_values, t_expected, atol=1e-4)

    def test_nonzero_initial_time(self):
        """Test with non-zero initial physical time"""
        s_values = np.linspace(0, 1, 11)
        Omega_values = np.ones_like(s_values)

        t_values = integrate_physical_time(s_values, Omega_values, t_initial=5.0)

        # Should have t = 5 + s
        assert np.allclose(t_values, 5.0 + s_values)


class TestEffectiveTimestep:
    """Test effective timestep computation"""

    def test_effective_timestep(self):
        """Test dt = Ω · ds"""
        ds = 0.1
        Omega = 2.5

        dt = compute_effective_timestep(ds, Omega)
        assert np.isclose(dt, 0.25)

    def test_small_omega_near_collision(self):
        """Test that dt → 0 as Ω → 0 (near collision)"""
        ds = 0.1
        Omega = 1e-6  # Very small, near collision

        dt = compute_effective_timestep(ds, Omega)
        assert dt < 1e-6
        assert dt == ds * Omega


class TestValidation:
    """Test validation of time dilation results"""

    def test_validate_positive_omega(self):
        """Test that result validates positive Omega"""
        result = compute_time_dilation_threebody(
            1.0, 2.0, 3.0,
            TimeTransformationStrategy.SUM
        )

        assert result.validate()

    def test_validate_detects_negative(self):
        """Test detection of negative Omega (shouldn't happen in practice)"""
        from src.python.regularization.sundman import TimeDilationResult

        result = TimeDilationResult(
            Omega=-1.0,
            strategy=TimeTransformationStrategy.SUM
        )

        assert not result.validate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
