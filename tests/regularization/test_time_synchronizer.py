"""
Tests for time synchronization utilities.

Tests the coordination between fictitious time (s) and physical time (t)
via the Sundman transformation dt/ds = Ω(q).
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from src.python.regularization.time_synchronizer import (
    DualTimeTrajectory,
    TimeSynchronizer,
    validate_time_consistency,
    resample_to_physical_time,
    compute_time_dilation_profile
)
from src.python.regularization.sundman import (
    SundmanTransformation,
    TimeTransformationStrategy
)


class TestDualTimeTrajectory:
    """Test DualTimeTrajectory data structure"""

    def test_creation(self):
        """Test basic trajectory creation"""
        s = np.linspace(0, 10, 100)
        t = s ** 2  # Non-linear time relation

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        assert traj.length == 100
        assert_array_equal(traj.s_values, s)
        assert_array_equal(traj.t_values, t)

    def test_length_mismatch_fails(self):
        """Test that mismatched lengths raise error"""
        s = np.linspace(0, 10, 100)
        t = np.linspace(0, 20, 50)  # Different length

        with pytest.raises(ValueError, match="Length mismatch"):
            DualTimeTrajectory(s_values=s, t_values=t)

    def test_properties(self):
        """Test span properties"""
        s = np.array([0.0, 1.0, 2.0, 3.0])
        t = np.array([0.0, 0.5, 2.0, 4.5])

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        assert traj.s_span == (0.0, 3.0)
        assert traj.t_span == (0.0, 4.5)
        assert traj.length == 4

    def test_time_dilation_stats_with_omega(self):
        """Test statistics with explicit Omega values"""
        s = np.linspace(0, 10, 100)
        Omega = np.ones(100) * 2.0  # Constant dilation
        t = s * 2.0  # dt/ds = 2

        traj = DualTimeTrajectory(
            s_values=s,
            t_values=t,
            Omega_values=Omega
        )

        stats = traj.get_time_dilation_stats()

        assert_allclose(stats['Omega_min'], 2.0)
        assert_allclose(stats['Omega_max'], 2.0)
        assert_allclose(stats['Omega_mean'], 2.0)
        assert_allclose(stats['Omega_std'], 0.0, atol=1e-10)

    def test_time_dilation_stats_without_omega(self):
        """Test statistics estimated from time differences"""
        s = np.linspace(0, 10, 100)
        t = s * 3.0  # Constant Omega = 3

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        stats = traj.get_time_dilation_stats()

        assert_allclose(stats['Omega_mean'], 3.0, rtol=1e-6)

    def test_interpolate_physical_time(self):
        """Test interpolation of physical time"""
        s = np.array([0.0, 1.0, 2.0, 3.0])
        t = np.array([0.0, 1.0, 4.0, 9.0])  # t = s^2

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        # Query at midpoint
        s_query = np.array([0.5, 1.5, 2.5])
        t_interp = traj.interpolate_physical_time(s_query)

        # Should be close to s^2 for quadratic data
        expected = s_query ** 2
        assert_allclose(t_interp, expected, rtol=0.1)

    def test_interpolate_fictitious_time(self):
        """Test interpolation of fictitious time"""
        s = np.linspace(0, 10, 100)
        t = s ** 2  # Non-linear

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        # Query at some physical times
        t_query = np.array([0.25, 1.0, 4.0, 9.0])
        s_interp = traj.interpolate_fictitious_time(t_query)

        # Should be close to sqrt(t)
        expected = np.sqrt(t_query)
        assert_allclose(s_interp, expected, rtol=0.01)

    def test_interpolate_non_monotonic_fails(self):
        """Test that non-monotonic physical time raises error"""
        s = np.array([0.0, 1.0, 2.0, 3.0])
        t = np.array([0.0, 2.0, 1.0, 3.0])  # Not monotonic

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        with pytest.raises(ValueError, match="monotonically increasing"):
            traj.interpolate_fictitious_time(np.array([1.5]))

    def test_with_states(self):
        """Test trajectory with state information"""
        s = np.linspace(0, 5, 10)
        t = s * 2.0
        states = [{'x': i} for i in range(10)]

        traj = DualTimeTrajectory(
            s_values=s,
            t_values=t,
            states=states
        )

        assert len(traj.states) == 10
        assert traj.states[5]['x'] == 5

    def test_states_length_mismatch_fails(self):
        """Test that mismatched states length raises error"""
        s = np.linspace(0, 5, 10)
        t = s * 2.0
        states = [{'x': i} for i in range(5)]  # Wrong length

        with pytest.raises(ValueError, match="States length"):
            DualTimeTrajectory(s_values=s, t_values=t, states=states)


class TestTimeSynchronizer:
    """Test TimeSynchronizer class"""

    def test_initialization(self):
        """Test synchronizer initialization"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation, s_initial=0.0, t_initial=0.0)

        assert sync.s_initial == 0.0
        assert sync.t_initial == 0.0
        assert len(sync.s_history) == 1
        assert len(sync.t_history) == 1
        assert len(sync.Omega_history) == 0

    def test_advance_time_constant_omega(self):
        """Test time advancement with constant Omega"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Advance with radius = 2.0, so Omega = 2.0
        ds = 0.1
        s_new, t_new, Omega = sync.advance_time(ds, 2.0)

        assert_allclose(s_new, 0.1)
        assert_allclose(t_new, 0.2)  # dt = Omega * ds = 2.0 * 0.1
        assert_allclose(Omega, 2.0)

        assert len(sync.s_history) == 2
        assert len(sync.t_history) == 2
        assert len(sync.Omega_history) == 1

    def test_advance_time_multiple_steps(self):
        """Test multiple time steps"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        radii = [1.0, 0.5, 2.0, 1.5]
        ds = 0.1

        for r in radii:
            sync.advance_time(ds, r)

        assert len(sync.s_history) == 5  # Initial + 4 steps
        assert len(sync.t_history) == 5
        assert len(sync.Omega_history) == 4

        # Check final values
        expected_s = 0.0 + 4 * ds
        expected_t = sum(r * ds for r in radii)

        assert_allclose(sync.s_history[-1], expected_s)
        assert_allclose(sync.t_history[-1], expected_t)

    def test_reset(self):
        """Test reset functionality"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Advance a few steps
        for i in range(5):
            sync.advance_time(0.1, 1.0 + i * 0.1)

        # Reset
        sync.reset(s_initial=2.0, t_initial=5.0)

        assert len(sync.s_history) == 1
        assert len(sync.t_history) == 1
        assert len(sync.Omega_history) == 0
        assert sync.s_history[0] == 2.0
        assert sync.t_history[0] == 5.0

    def test_get_trajectory(self):
        """Test trajectory extraction"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Advance a few steps
        for i in range(10):
            sync.advance_time(0.1, 1.0)

        traj = sync.get_trajectory()

        assert isinstance(traj, DualTimeTrajectory)
        assert traj.length == 11  # Initial + 10 steps
        assert_allclose(traj.s_values[-1], 1.0)
        assert_allclose(traj.t_values[-1], 1.0)  # Omega = 1.0 throughout
        # Omega_values has 10 elements (one per advance_time call)
        assert len(traj.Omega_values) == 10

    def test_validate_monotonicity_success(self):
        """Test monotonicity validation with valid data"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Advance with positive Omega
        for i in range(10):
            sync.advance_time(0.1, 1.0 + i * 0.1)

        result = sync.validate_monotonicity()

        assert result['s_monotonic'] == True
        assert result['t_monotonic'] == True
        assert result['negative_dt_count'] == 0

    def test_compute_average_dilation(self):
        """Test average dilation computation"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Advance with constant Omega = 2.0
        for _ in range(100):
            sync.advance_time(0.1, 2.0)

        avg_dilation = sync.compute_average_dilation()

        assert_allclose(avg_dilation, 2.0, rtol=1e-10)

    def test_compute_average_dilation_varying_omega(self):
        """Test average dilation with varying Omega"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Vary radius from 1 to 3
        radii = np.linspace(1.0, 3.0, 100)
        ds = 0.1

        for r in radii:
            sync.advance_time(ds, r)

        # Average Omega should be around 2.0 (midpoint of 1-3)
        avg_dilation = sync.compute_average_dilation()
        expected = np.mean(radii)

        assert_allclose(avg_dilation, expected, rtol=1e-6)

    def test_repr(self):
        """Test string representation"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        sync.advance_time(0.5, 1.0)
        sync.advance_time(0.5, 1.0)

        repr_str = repr(sync)

        assert "TimeSynchronizer" in repr_str
        assert "points=3" in repr_str


class TestValidateTimeConsistency:
    """Test time consistency validation"""

    def test_perfect_consistency(self):
        """Test with perfectly consistent data"""
        s = np.linspace(0, 10, 100)
        Omega = np.ones(100) * 2.0

        # Integrate to get t
        from src.python.regularization.sundman import integrate_physical_time
        t = integrate_physical_time(s, Omega, t_initial=0.0)

        result = validate_time_consistency(s, t, Omega, tolerance=1e-10)

        assert result['consistent'] == True
        assert result['max_error'] < 1e-10

    def test_small_inconsistency(self):
        """Test detection of small inconsistency"""
        s = np.linspace(0, 10, 100)
        Omega = np.ones(100) * 2.0
        # Add systematic drift that integration won't match
        t = s * 2.0 + s * 0.01  # Linear drift

        result = validate_time_consistency(s, t, Omega, tolerance=1e-8)

        assert result['consistent'] == False
        assert result['max_error'] > 1e-8

    def test_length_mismatch_fails(self):
        """Test that length mismatch raises error"""
        s = np.linspace(0, 10, 100)
        t = np.linspace(0, 20, 50)
        Omega = np.ones(100)

        with pytest.raises(ValueError, match="same length"):
            validate_time_consistency(s, t, Omega)


class TestResampleToPhysicalTime:
    """Test resampling to physical time grid"""

    def test_resample_linear(self):
        """Test resampling with linear time relation"""
        s = np.linspace(0, 10, 100)
        t = s * 2.0
        Omega = np.ones(100) * 2.0

        traj = DualTimeTrajectory(
            s_values=s,
            t_values=t,
            Omega_values=Omega
        )

        # Create uniform physical time grid
        t_grid = np.linspace(0, 20, 50)

        resampled = resample_to_physical_time(traj, t_grid)

        assert len(resampled.s_values) == 50
        assert len(resampled.t_values) == 50
        assert_array_equal(resampled.t_values, t_grid)

        # s should be t/2
        assert_allclose(resampled.s_values, t_grid / 2.0, rtol=1e-6)

    def test_resample_nonlinear(self):
        """Test resampling with nonlinear time relation"""
        s = np.linspace(0, 10, 200)
        t = s ** 2

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        t_grid = np.linspace(0, 100, 50)
        resampled = resample_to_physical_time(traj, t_grid)

        assert_array_equal(resampled.t_values, t_grid)

        # s should be sqrt(t)
        expected_s = np.sqrt(t_grid)
        assert_allclose(resampled.s_values, expected_s, rtol=0.01)

    def test_resample_preserves_omega(self):
        """Test that Omega is interpolated correctly"""
        s = np.linspace(0, 10, 100)
        Omega = s + 1.0  # Linear variation

        from src.python.regularization.sundman import integrate_physical_time
        t = integrate_physical_time(s, Omega, t_initial=0.0)

        traj = DualTimeTrajectory(
            s_values=s,
            t_values=t,
            Omega_values=Omega
        )

        t_grid = np.linspace(t[0], t[-1], 50)
        resampled = resample_to_physical_time(traj, t_grid)

        assert resampled.Omega_values is not None
        assert len(resampled.Omega_values) == 50


class TestComputeTimeDilationProfile:
    """Test time dilation profile computation"""

    def test_constant_omega(self):
        """Test profile with constant Omega"""
        s = np.linspace(0, 10, 1000)
        Omega = np.ones(1000) * 2.0
        t = s * 2.0

        traj = DualTimeTrajectory(
            s_values=s,
            t_values=t,
            Omega_values=Omega
        )

        profile = compute_time_dilation_profile(traj, num_bins=20)

        assert_allclose(profile['Omega_min'], 2.0)
        assert_allclose(profile['Omega_max'], 2.0)
        assert_allclose(profile['Omega_median'], 2.0)

        # All values should be in one bin
        assert profile['histogram'].sum() == 1000

    def test_varying_omega(self):
        """Test profile with varying Omega"""
        s = np.linspace(0, 10, 1000)
        Omega = np.linspace(1.0, 5.0, 1000)

        from src.python.regularization.sundman import integrate_physical_time
        t = integrate_physical_time(s, Omega, t_initial=0.0)

        traj = DualTimeTrajectory(
            s_values=s,
            t_values=t,
            Omega_values=Omega
        )

        profile = compute_time_dilation_profile(traj, num_bins=50)

        assert_allclose(profile['Omega_min'], 1.0, rtol=1e-3)
        assert_allclose(profile['Omega_max'], 5.0, rtol=1e-3)
        assert_allclose(profile['Omega_median'], 3.0, rtol=0.1)

        # Check histogram structure
        assert len(profile['histogram']) == 50
        assert len(profile['bin_centers']) == 50

    def test_without_omega_values(self):
        """Test profile estimation without explicit Omega"""
        s = np.linspace(0, 10, 1000)
        t = s * 3.0  # Constant Omega = 3

        traj = DualTimeTrajectory(s_values=s, t_values=t)

        profile = compute_time_dilation_profile(traj, num_bins=20)

        # Should estimate Omega ≈ 3 from differences
        assert_allclose(profile['Omega_median'], 3.0, rtol=0.01)


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""

    def test_kepler_orbit_time_regularization(self):
        """Test time regularization for Kepler orbit"""
        # Simulate Kepler orbit with r varying from perihelion to aphelion
        s = np.linspace(0, 2 * np.pi, 1000)

        # Radius varies: r = a(1 - e cos E)
        e = 0.95  # High eccentricity for significant time dilation
        r = 1.0 * (1.0 - e * np.cos(s))

        # Use STANDARD Sundman: Omega = r
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        ds = s[1] - s[0]
        for radius in r[1:]:
            sync.advance_time(ds, radius)

        # Validate monotonicity
        result = sync.validate_monotonicity()
        assert result['s_monotonic'] == True
        assert result['t_monotonic'] == True

        # Time dilation should vary with radius
        traj = sync.get_trajectory()
        stats = traj.get_time_dilation_stats()

        assert stats['Omega_min'] < stats['Omega_max']
        assert stats['time_dilation_active'] == True

    def test_three_body_sum_strategy(self):
        """Test three-body with SUM strategy"""
        transformation = SundmanTransformation(TimeTransformationStrategy.SUM)
        sync = TimeSynchronizer(transformation)

        # Simulate varying distances
        s_grid = np.linspace(0, 10, 100)
        ds = s_grid[1] - s_grid[0]

        for i, si in enumerate(s_grid[1:], 1):
            # Vary distances sinusoidally
            r12 = 1.0 + 0.5 * np.sin(2 * np.pi * si / 10)
            r23 = 1.0 + 0.5 * np.sin(2 * np.pi * si / 10 + np.pi / 3)
            r31 = 1.0 + 0.5 * np.sin(2 * np.pi * si / 10 + 2 * np.pi / 3)

            sync.advance_time(ds, r12, r23, r31)

        # Check trajectory
        traj = sync.get_trajectory()
        assert traj.length == 100

        # Average Omega should be around 3.0 (sum of three ~1.0 distances)
        avg = sync.compute_average_dilation()
        assert 2.5 < avg < 3.5

    def test_near_collision_regularization(self):
        """Test behavior near collision (small r)"""
        transformation = SundmanTransformation(TimeTransformationStrategy.STANDARD)
        sync = TimeSynchronizer(transformation)

        # Approach collision: r → 0
        radii = np.linspace(1.0, 0.01, 100)
        ds = 0.01

        for r in radii:
            sync.advance_time(ds, r)

        traj = sync.get_trajectory()
        stats = traj.get_time_dilation_stats()

        # Time dilation should slow down near collision
        assert stats['Omega_min'] < 0.1
        assert stats['time_dilation_active'] == True

        # Physical time advancement should slow
        dt_values = np.diff(traj.t_values)
        assert dt_values[-1] < dt_values[0]  # Slowing down
