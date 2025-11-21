"""
Tests for extended phase space with time regularization.

Tests ExtendedKSState and related functionality for dual time tracking.
"""

import pytest
import numpy as np

from src.python.regularization.extended_phase_space import (
    ExtendedKSState,
    create_extended_ks_state,
    compute_time_dilation_history,
    compute_energy_drift,
    validate_extended_trajectory
)
from src.python.regularization.spinor_vector import SpinorVector


class TestExtendedKSState:
    """Test ExtendedKSState data structure"""

    def test_creation(self):
        """Test basic creation of extended state"""
        u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))
        p_u = SpinorVector(np.array([0.0, 0.5, 0.0, 0.0]))

        state = ExtendedKSState(
            u=u,
            p_u=p_u,
            s=0.0,
            K=-0.5,
            t=0.0,
            E=-0.5
        )

        assert state.s == 0.0
        assert state.t == 0.0
        assert state.E == -0.5
        assert state.K == -0.5

    def test_time_dilation_factor(self):
        """Test time dilation factor computation"""
        u = SpinorVector(np.array([2.0, 0.0, 0.0, 0.0]))
        p_u = SpinorVector(np.zeros(4))

        state = ExtendedKSState(u, p_u, s=0.0, K=0.0, t=0.0, E=0.0)

        # Ω = ‖u‖² = 4.0
        assert np.isclose(state.time_dilation_factor, 4.0)

    def test_physical_radius(self):
        """Test physical radius extraction"""
        u = SpinorVector(np.array([1.0, 1.0, 0.0, 0.0]))
        p_u = SpinorVector(np.zeros(4))

        state = ExtendedKSState(u, p_u, s=0.0, K=0.0, t=0.0, E=0.0)

        # r = ‖u‖² = 2.0
        assert np.isclose(state.physical_radius, 2.0)

    def test_validate_time_relation(self):
        """Test time-energy consistency validation"""
        # Create state with consistent K and E
        u = SpinorVector(np.array([2.0, 0.0, 0.0, 0.0]))  # ‖u‖² = 4
        p_u = SpinorVector(np.zeros(4))
        E = -1.0
        K = E * 4.0  # K = E·Ω = -4.0

        state = ExtendedKSState(u, p_u, s=0.0, K=K, t=0.0, E=E)

        assert state.validate_time_relation()

    def test_validate_time_relation_failure(self):
        """Test detection of time-energy inconsistency"""
        u = SpinorVector(np.array([2.0, 0.0, 0.0, 0.0]))  # ‖u‖² = 4
        p_u = SpinorVector(np.zeros(4))

        # Deliberately inconsistent K and E
        state = ExtendedKSState(u, p_u, s=0.0, K=-1.0, t=0.0, E=-1.0)

        # K should be -4.0 (= E·Ω = -1.0 · 4.0), but is -1.0
        assert not state.validate_time_relation(tol=1e-10)

    def test_to_vector_and_back(self):
        """Test conversion to/from flat vector"""
        u = SpinorVector(np.array([1.0, 2.0, 3.0, 4.0]))
        p_u = SpinorVector(np.array([0.5, 0.6, 0.7, 0.8]))

        state = ExtendedKSState(
            u, p_u,
            s=1.5,
            K=-2.0,
            t=0.75,
            E=-0.5
        )

        # Convert to vector
        vec = state.to_vector()
        assert len(vec) == 12

        # Convert back
        state_reconstructed = ExtendedKSState.from_vector(vec)

        # Compare
        assert np.allclose(state.u.components, state_reconstructed.u.components)
        assert np.allclose(state.p_u.components, state_reconstructed.p_u.components)
        assert np.isclose(state.s, state_reconstructed.s)
        assert np.isclose(state.K, state_reconstructed.K)
        assert np.isclose(state.t, state_reconstructed.t)
        assert np.isclose(state.E, state_reconstructed.E)

    def test_with_updated_time(self):
        """Test time advancement"""
        u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))  # Ω = 1
        p_u = SpinorVector(np.zeros(4))

        state = ExtendedKSState(u, p_u, s=0.0, K=-1.0, t=0.0, E=-1.0)

        # Advance by ds = 0.5
        state_new = state.with_updated_time(ds=0.5)

        # Check updates
        assert np.isclose(state_new.s, 0.5)
        assert np.isclose(state_new.t, 0.5)  # dt = Ω·ds = 1·0.5 = 0.5
        assert np.isclose(state_new.E, -1.0)  # Conserved
        assert state_new.validate_time_relation()


    def test_validate_all_constraints(self):
        """Test comprehensive constraint validation"""
        u = SpinorVector(np.array([2.0, 0.0, 0.0, 0.0]))
        p_u = SpinorVector(np.zeros(4))
        E = -0.5
        Omega = 4.0  # ‖u‖²
        K = E * Omega  # = -2.0

        state = ExtendedKSState(u, p_u, s=0.0, K=K, t=0.0, E=E)

        results = state.validate_all_constraints()

        assert results['time_energy_consistent']
        assert results['bilinear_satisfied']
        assert results['time_dilation_positive']
        assert results['all_constraints_satisfied']


class TestExtendedHelperFunctions:
    """Test helper functions for extended states"""

    def test_create_extended_ks_state(self):
        """Test convenient constructor"""
        u = np.array([1.0, 0.0, 0.0, 0.0])
        p_u = np.zeros(4)

        state = create_extended_ks_state(
            u, p_u,
            s=0.0,
            t=0.0,
            E=-1.0,
            compute_K=True
        )

        # K should be automatically computed as E·‖u‖² = -1.0 · 1.0 = -1.0
        assert np.isclose(state.K, -1.0)
        assert state.validate_time_relation()

    def test_compute_time_dilation_history(self):
        """Test extraction of time dilation history"""
        trajectory = []
        for i in range(5):
            r = 1.0 + i * 0.5  # Increasing radius
            u = SpinorVector(np.array([np.sqrt(r), 0.0, 0.0, 0.0]))
            p_u = SpinorVector(np.zeros(4))

            state = ExtendedKSState(u, p_u, s=float(i), K=0.0, t=float(i), E=0.0)
            trajectory.append(state)

        Omega_history = compute_time_dilation_history(trajectory)

        # Should have 5 values
        assert len(Omega_history) == 5

        # Should be increasing (since r increases)
        assert np.all(np.diff(Omega_history) > 0)


class TestEnergyDrift:
    """Test energy conservation monitoring"""

    def test_compute_energy_drift_perfect_conservation(self):
        """Test with perfectly conserved energy"""
        E = -1.0
        trajectory = []

        for i in range(10):
            u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))  # Constant Ω = 1
            p_u = SpinorVector(np.zeros(4))
            K = E * 1.0  # K = E·Ω

            state = ExtendedKSState(u, p_u, s=float(i)*0.1, K=K, t=float(i)*0.1, E=E)
            trajectory.append(state)

        results = compute_energy_drift(trajectory)

        # E should be perfectly conserved
        assert results['E_conserved']
        assert results['E_drift'] < 1e-15

        # K should follow relation
        assert results['K_relation_satisfied']

    def test_compute_energy_drift_varying_omega(self):
        """Test with varying time dilation"""
        E = -1.0
        trajectory = []

        for i in range(10):
            r = 1.0 + i * 0.2  # Varying radius
            u = SpinorVector(np.array([np.sqrt(r), 0.0, 0.0, 0.0]))
            p_u = SpinorVector(np.zeros(4))
            K = E * r  # K = E·Ω

            state = ExtendedKSState(u, p_u, s=float(i)*0.1, K=K, t=float(i)*0.15, E=E)
            trajectory.append(state)

        results = compute_energy_drift(trajectory)

        # E still conserved
        assert results['E_conserved']

        # Omega should vary
        assert results['Omega_range'] > 0.1


class TestTrajectoryValidation:
    """Test trajectory validation"""

    def test_validate_extended_trajectory(self):
        """Test validation of valid trajectory"""
        trajectory = []
        E = -1.0

        for i in range(20):
            s = i * 0.1
            r = 1.0 + 0.1 * s
            u = SpinorVector(np.array([np.sqrt(r), 0.0, 0.0, 0.0]))
            p_u = SpinorVector(np.zeros(4))
            K = E * r
            t = 0.5 * s  # Some physical time accumulation

            state = ExtendedKSState(u, p_u, s=s, K=K, t=t, E=E)
            trajectory.append(state)

        results = validate_extended_trajectory(trajectory)

        assert results['s_monotonic']
        assert results['t_monotonic']
        assert results['trajectory_valid']
        assert results['num_constraint_violations'] == 0

    def test_validate_extended_trajectory_verbose(self, capsys):
        """Test verbose output"""
        trajectory = []
        E = -1.0

        for i in range(5):
            u = SpinorVector(np.array([1.0, 0.0, 0.0, 0.0]))
            p_u = SpinorVector(np.zeros(4))
            state = ExtendedKSState(u, p_u, s=float(i), K=E, t=float(i), E=E)
            trajectory.append(state)

        validate_extended_trajectory(trajectory, verbose=True)

        captured = capsys.readouterr()
        assert "Extended KS Trajectory Validation" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
