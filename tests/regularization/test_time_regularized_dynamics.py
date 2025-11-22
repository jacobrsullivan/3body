"""
Tests for time-regularized constrained dynamics (Phase 2).

Tests:
- Time-regularized Hamiltonian evaluation
- Integration with dual time tracking
- Kepler orbit validation (Phase 5)
- Energy conservation (E and K)
- Time relation K = E · Ω
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose

from src.python.regularization.time_regularized_dynamics import (
    TimeRegularizedHamiltonian,
    TimeRegularizedTrajectory,
    integrate_time_regularized_ks,
    validate_kepler_orbit,
    create_kepler_initial_state
)
from src.python.regularization.extended_phase_space import create_extended_ks_state
from src.python.regularization.spinor_vector import SpinorVector


class TestTimeRegularizedHamiltonian:
    """Test Hamiltonian evaluation"""

    def test_creation(self):
        """Test Hamiltonian creation"""
        H = TimeRegularizedHamiltonian(mu=1.0)
        assert H.mu == 1.0

    def test_evaluate_simple_state(self):
        """Test Hamiltonian evaluation"""
        H = TimeRegularizedHamiltonian(mu=1.0)

        u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))
        p_u = SpinorVector(np.array([0.0, 1.0, 0.0, 0.0]))

        state = create_extended_ks_state(u, p_u, s=0, K=-0.5, t=0, E=-0.5)

        H_val = H.evaluate_regularized(state)

        # H = (1/2)‖p_u‖² - μ/‖u‖²
        expected = 0.5 * 1.0 - 1.0 / 1.0
        assert_allclose(H_val, expected)

    def test_forces_computation(self):
        """Test force computation"""
        H = TimeRegularizedHamiltonian(mu=1.0)

        u = SpinorVector(np.array([2.0, 0.0, 0.0, 0.0]))
        p_u = SpinorVector(np.zeros(4))

        state = create_extended_ks_state(u, p_u, s=0, K=0, t=0, E=0)

        forces = H.compute_forces(state)

        assert forces.shape == (4,)
        assert not np.any(np.isnan(forces))


class TestIntegration:
    """Test time-regularized integration"""

    def test_short_integration(self):
        """Test short integration"""
        # Circular orbit at r=1
        u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))
        p_u = SpinorVector(np.array([0.0, 1.0, 0.0, 0.0]))

        E = -0.5  # Energy for circular orbit
        K = E * 1.0  # Ω = ‖u‖² = 1

        state0 = create_extended_ks_state(u, p_u, s=0, K=K, t=0, E=E)

        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 1.0), n_points=100)

        assert traj.length == 100
        assert len(traj.s_values) == 100
        assert len(traj.t_values) == 100

    def test_time_advancement(self):
        """Test that physical time advances"""
        state0 = create_kepler_initial_state(semi_major_axis=1.0, eccentricity=0.0, mu=1.0)

        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 10.0), n_points=100)

        # Physical time should advance
        assert traj.t_values[-1] > traj.t_values[0]
        # Fictitious time should match s_span
        assert_allclose(traj.s_values[-1], 10.0, rtol=1e-6)

    def test_energy_conservation(self):
        """Test that E and K are conserved"""
        state0 = create_kepler_initial_state(semi_major_axis=1.0, eccentricity=0.3, mu=1.0)

        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 50.0), n_points=500, rtol=1e-10, atol=1e-12)

        E_vals, K_vals = traj.get_energies()

        # Both energies should be conserved
        E_std = np.std(E_vals)
        K_std = np.std(K_vals)

        assert E_std < 1e-6, f"E not conserved: std = {E_std}"
        assert K_std < 1e-6, f"K not conserved: std = {K_std}"

    def test_time_relation(self):
        """Test K = E · Ω relation"""
        state0 = create_kepler_initial_state(semi_major_axis=1.0, eccentricity=0.5, mu=1.0)

        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 30.0), n_points=300)

        E_vals, K_vals = traj.get_energies()
        Omega_vals = traj.get_time_dilations()

        # Check K = E · Ω at each point
        K_expected = E_vals * Omega_vals
        errors = np.abs(K_vals - K_expected)

        max_error = np.max(errors)
        assert max_error < 1e-6, f"Time relation violated: max error = {max_error}"


class TestKeplerValidation:
    """Test validation against Kepler orbits (Phase 5)"""

    def test_circular_orbit(self):
        """Test circular orbit period"""
        a = 1.0  # Semi-major axis
        mu = 1.0

        # Period: T = 2π√(a³/μ)
        expected_period = 2 * np.pi * np.sqrt(a**3 / mu)

        state0 = create_kepler_initial_state(semi_major_axis=a, eccentricity=0.0, mu=mu)

        H = TimeRegularizedHamiltonian(mu=mu)

        # Integrate for one period in fictitious time (estimate)
        # For circular orbit, physical time ≈ fictitious time
        s_span = (0, expected_period * 1.1)

        traj = integrate_time_regularized_ks(state0, H, s_span, n_points=1000, rtol=1e-10, atol=1e-12)

        results = validate_kepler_orbit(traj, expected_period, tolerance=0.05)

        assert results['E_conservation'], f"E drift: {results['E_drift']}"
        assert results['K_conservation'], f"K drift: {results['K_drift']}"
        assert results['time_relation_satisfied'], f"Time relation error: {results['time_relation_error']}"

    def test_elliptical_orbit(self):
        """Test elliptical orbit"""
        a = 1.0
        e = 0.6
        mu = 1.0

        expected_period = 2 * np.pi * np.sqrt(a**3 / mu)

        state0 = create_kepler_initial_state(semi_major_axis=a, eccentricity=e, mu=mu)

        H = TimeRegularizedHamiltonian(mu=mu)

        # Integrate for approximately one period
        s_span = (0, expected_period * 2.0)  # Larger span for elliptical

        traj = integrate_time_regularized_ks(state0, H, s_span, n_points=1000, rtol=1e-10, atol=1e-12)

        results = validate_kepler_orbit(traj, expected_period, tolerance=0.1)

        assert results['E_conservation'], f"E drift: {results['E_drift']}"
        assert results['K_conservation'], f"K drift: {results['K_drift']}"

    def test_near_collision_orbit(self):
        """Test highly eccentric orbit (near collision)"""
        a = 1.0
        e = 0.95  # Very eccentric
        mu = 1.0

        state0 = create_kepler_initial_state(semi_major_axis=a, eccentricity=e, mu=mu)

        H = TimeRegularizedHamiltonian(mu=mu)

        # Integrate through near-collision
        s_span = (0, 20.0)

        traj = integrate_time_regularized_ks(state0, H, s_span, n_points=1000, rtol=1e-10, atol=1e-12)

        E_vals, K_vals = traj.get_energies()

        # Energies should still be conserved even near collision
        E_std = np.std(E_vals) / np.abs(np.mean(E_vals))
        K_std = np.std(K_vals) / np.abs(np.mean(K_vals))

        assert E_std < 0.01, f"E not conserved near collision: {E_std}"
        assert K_std < 0.01, f"K not conserved near collision: {K_std}"

        # Time dilation should vary significantly
        Omega_vals = traj.get_time_dilations()
        Omega_range = np.max(Omega_vals) - np.min(Omega_vals)

        assert Omega_range > 1.0, "Time dilation should vary for eccentric orbit"


class TestTrajectory:
    """Test trajectory structure"""

    def test_trajectory_properties(self):
        """Test trajectory data structure"""
        state0 = create_kepler_initial_state()
        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 5.0), n_points=50)

        assert traj.length == 50
        assert len(traj.s_values) == 50
        assert len(traj.t_values) == 50
        assert len(traj.states) == 50

    def test_get_energies(self):
        """Test energy extraction"""
        state0 = create_kepler_initial_state()
        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 5.0), n_points=50)

        E_vals, K_vals = traj.get_energies()

        assert len(E_vals) == 50
        assert len(K_vals) == 50

    def test_get_time_dilations(self):
        """Test time dilation extraction"""
        state0 = create_kepler_initial_state()
        H = TimeRegularizedHamiltonian(mu=1.0)

        traj = integrate_time_regularized_ks(state0, H, (0, 5.0), n_points=50)

        Omega_vals = traj.get_time_dilations()

        assert len(Omega_vals) == 50
        assert np.all(Omega_vals > 0)  # Time dilation should be positive
