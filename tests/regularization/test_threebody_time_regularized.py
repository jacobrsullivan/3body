"""
Tests for Phase 3: Three-Body Time-Regularized Dynamics.

Tests the integration of:
- Pairwise spinor states with time tracking
- Three-body Hamiltonian with time regularization
- Integration and conservation laws
"""

import pytest
import numpy as np
from src.python.regularization.threebody_time_regularized import (
    PairwiseSpinorStateWithTime,
    ThreeBodyTimeRegularizedHamiltonian,
    ThreeBodyTrajectory,
    integrate_threebody_time_regularized,
)
from src.python.regularization.spinor_vector import SpinorVector
from src.python.coordinates.base import Masses


class TestPairwiseSpinorStateWithTime:
    """Test extended pairwise spinor state with time tracking."""

    def test_creation(self):
        """Test basic state creation."""
        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([0.0, 1.0, 0.0, 0.0])
        u31 = np.array([0.0, 0.0, 1.0, 0.0])

        p12 = np.array([0.0, 0.0, 0.0, 0.1])
        p23 = np.array([0.0, 0.0, 0.1, 0.0])
        p31 = np.array([0.0, 0.1, 0.0, 0.0])

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(p12),
            p_u23=SpinorVector(p23),
            p_u31=SpinorVector(p31),
            s=0.0,
            K=-0.5,
            t=0.0,
            E=-0.5
        )

        assert state.s == 0.0
        assert state.K == -0.5
        assert state.t == 0.0
        assert state.E == -0.5

    def test_spinor_coordinates(self):
        """Test spinor coordinate extraction."""
        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([0.0, 1.0, 0.0, 0.0])
        u31 = np.array([0.0, 0.0, 1.0, 0.0])

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(np.zeros(4)),
            p_u23=SpinorVector(np.zeros(4)),
            p_u31=SpinorVector(np.zeros(4)),
            s=0.0, K=0.0, t=0.0, E=0.0
        )

        coords = state.spinor_coordinates
        assert coords.shape == (12,)
        assert np.allclose(coords[0:4], u12)
        assert np.allclose(coords[4:8], u23)
        assert np.allclose(coords[8:12], u31)

    def test_pairwise_radii(self):
        """Test pairwise radius computation."""
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # r12 = |u|² = 1.0
        u23 = np.array([1.0, 1.0, 0.0, 0.0])  # r23 = 2.0
        u31 = np.array([1.0, 1.0, 1.0, 0.0])  # r31 = 3.0

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(np.zeros(4)),
            p_u23=SpinorVector(np.zeros(4)),
            p_u31=SpinorVector(np.zeros(4)),
            s=0.0, K=0.0, t=0.0, E=0.0
        )

        r12, r23, r31 = state.get_pairwise_radii()
        assert np.isclose(r12, 1.0)
        assert np.isclose(r23, 2.0)
        assert np.isclose(r31, 3.0)

    def test_time_dilation_computation(self):
        """Test time dilation factor computation."""
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # r12 = 1.0
        u23 = np.array([1.0, 0.0, 0.0, 0.0])  # r23 = 1.0
        u31 = np.array([1.0, 0.0, 0.0, 0.0])  # r31 = 1.0

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(np.zeros(4)),
            p_u23=SpinorVector(np.zeros(4)),
            p_u31=SpinorVector(np.zeros(4)),
            s=0.0, K=0.0, t=0.0, E=0.0
        )

        # Sum strategy: Ω = r12 + r23 + r31 = 3.0
        Omega = state.compute_time_dilation(strategy="sum")
        assert np.isclose(Omega, 3.0)

    def test_time_relation_validation(self):
        """Test K = E·Ω validation."""
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # r12 = 1.0
        u23 = np.array([1.0, 0.0, 0.0, 0.0])  # r23 = 1.0
        u31 = np.array([1.0, 0.0, 0.0, 0.0])  # r31 = 1.0

        # Ω = 3.0, E = -0.5 → K = -1.5
        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(np.zeros(4)),
            p_u23=SpinorVector(np.zeros(4)),
            p_u31=SpinorVector(np.zeros(4)),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        assert state.validate_time_relation(tolerance=1e-6)

    def test_to_vector_and_back(self):
        """Test state vector conversion roundtrip."""
        u12 = np.random.randn(4)
        u23 = np.random.randn(4)
        u31 = np.random.randn(4)
        p12 = np.random.randn(4)
        p23 = np.random.randn(4)
        p31 = np.random.randn(4)

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(p12),
            p_u23=SpinorVector(p23),
            p_u31=SpinorVector(p31),
            s=1.5, K=-0.7, t=2.3, E=-0.5
        )

        vec = state.to_vector()
        assert vec.shape == (27,)

        reconstructed = PairwiseSpinorStateWithTime.from_vector(vec, s=1.5)

        assert np.allclose(reconstructed.u12.to_array(), u12)
        assert np.allclose(reconstructed.u23.to_array(), u23)
        assert np.allclose(reconstructed.u31.to_array(), u31)
        assert np.allclose(reconstructed.p_u12.to_array(), p12)
        assert np.allclose(reconstructed.p_u23.to_array(), p23)
        assert np.allclose(reconstructed.p_u31.to_array(), p31)
        assert reconstructed.s == 1.5
        assert reconstructed.K == -0.7
        assert reconstructed.t == 2.3
        assert reconstructed.E == -0.5


class TestThreeBodyTimeRegularizedHamiltonian:
    """Test three-body Hamiltonian with time regularization."""

    def test_creation(self):
        """Test Hamiltonian creation."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses, strategy="sum")

        assert H.masses == masses
        assert H.strategy == "sum"
        assert H.G == 1.0

    def test_potential_computation(self):
        """Test gravitational potential computation."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        # Simple state with known radii
        u12 = np.array([1.0, 0.0, 0.0, 0.0])  # r12 = 1.0
        u23 = np.array([1.0, 0.0, 0.0, 0.0])  # r23 = 1.0
        u31 = np.array([1.0, 0.0, 0.0, 0.0])  # r31 = 1.0

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(np.zeros(4)),
            p_u23=SpinorVector(np.zeros(4)),
            p_u31=SpinorVector(np.zeros(4)),
            s=0.0, K=0.0, t=0.0, E=0.0
        )

        V = H._compute_potential(state)
        # V = -G(m1m2/r12 + m2m3/r23 + m3m1/r31) = -(1 + 1 + 1) = -3
        assert np.isclose(V, -3.0)

    def test_hamiltonian_evaluation(self):
        """Test full Hamiltonian evaluation."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        # State with some kinetic energy
        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([1.0, 0.0, 0.0, 0.0])
        u31 = np.array([1.0, 0.0, 0.0, 0.0])

        p = 0.1 * np.ones(4)  # Small momentum

        state = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(p),
            p_u23=SpinorVector(p),
            p_u31=SpinorVector(p),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        H_val = H.evaluate(state)
        # Should be finite and well-defined
        assert np.isfinite(H_val)


class TestIntegration:
    """Test three-body time-regularized integration."""

    def test_short_integration(self):
        """Test short integration doesn't crash."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        # Simple initial state
        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([0.0, 1.0, 0.0, 0.0])
        u31 = np.array([0.0, 0.0, 1.0, 0.0])

        p = 0.05 * np.ones(4)

        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(p),
            p_u23=SpinorVector(p),
            p_u31=SpinorVector(p),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        # Integrate for short time
        traj = integrate_threebody_time_regularized(
            state0, H, (0, 1.0), n_points=10, rtol=1e-8, atol=1e-10
        )

        assert len(traj.s_values) == 10
        assert len(traj.states) == 10
        assert traj.s_values[0] == 0.0
        assert traj.s_values[-1] == 1.0

    def test_time_advancement(self):
        """Test that physical time advances."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([0.0, 1.0, 0.0, 0.0])
        u31 = np.array([0.0, 0.0, 1.0, 0.0])

        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(0.05 * np.ones(4)),
            p_u23=SpinorVector(0.05 * np.ones(4)),
            p_u31=SpinorVector(0.05 * np.ones(4)),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        traj = integrate_threebody_time_regularized(
            state0, H, (0, 5.0), n_points=50
        )

        t_vals = traj.t_values
        # Physical time should increase
        assert t_vals[-1] > t_vals[0]
        # Should be monotonic
        assert np.all(np.diff(t_vals) > 0)

    def test_energy_conservation(self):
        """Test that E is conserved during integration."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        u12 = np.array([1.0, 0.2, 0.1, 0.0])
        u23 = np.array([0.1, 1.0, 0.2, 0.0])
        u31 = np.array([0.2, 0.1, 1.0, 0.0])

        # Compute initial Ω and set K = E·Ω
        Omega0 = np.linalg.norm(u12)**2 + np.linalg.norm(u23)**2 + np.linalg.norm(u31)**2
        E0 = -0.5
        K0 = E0 * Omega0

        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(0.05 * np.array([1, -1, 1, -1])),
            p_u23=SpinorVector(0.05 * np.array([-1, 1, -1, 1])),
            p_u31=SpinorVector(0.05 * np.array([1, 1, -1, -1])),
            s=0.0, K=K0, t=0.0, E=E0
        )

        traj = integrate_threebody_time_regularized(
            state0, H, (0, 10.0), n_points=100, rtol=1e-10, atol=1e-12
        )

        E_vals, K_vals = traj.get_energies()

        # E should be conserved
        E_drift = np.std(E_vals) / np.abs(np.mean(E_vals))
        assert E_drift < 0.01, f"E not conserved: relative drift = {E_drift}"


class TestTrajectory:
    """Test trajectory analysis functions."""

    def test_get_energies(self):
        """Test energy extraction from trajectory."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        u = np.array([1.0, 0.0, 0.0, 0.0])
        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u),
            u23=SpinorVector(u),
            u31=SpinorVector(u),
            p_u12=SpinorVector(0.05 * np.ones(4)),
            p_u23=SpinorVector(0.05 * np.ones(4)),
            p_u31=SpinorVector(0.05 * np.ones(4)),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        traj = integrate_threebody_time_regularized(
            state0, H, (0, 5.0), n_points=50
        )

        E_vals, K_vals = traj.get_energies()
        assert len(E_vals) == 50
        assert len(K_vals) == 50

    def test_get_time_dilations(self):
        """Test time dilation extraction."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        u = np.array([1.0, 0.0, 0.0, 0.0])
        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u),
            u23=SpinorVector(u),
            u31=SpinorVector(u),
            p_u12=SpinorVector(0.05 * np.ones(4)),
            p_u23=SpinorVector(0.05 * np.ones(4)),
            p_u31=SpinorVector(0.05 * np.ones(4)),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        traj = integrate_threebody_time_regularized(
            state0, H, (0, 5.0), n_points=50
        )

        Omega_vals = traj.get_time_dilations()
        assert len(Omega_vals) == 50
        assert np.all(Omega_vals > 0)  # Ω should always be positive

    def test_get_pairwise_separations(self):
        """Test pairwise separation extraction."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        u = np.array([1.0, 0.0, 0.0, 0.0])
        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u),
            u23=SpinorVector(u),
            u31=SpinorVector(u),
            p_u12=SpinorVector(0.05 * np.ones(4)),
            p_u23=SpinorVector(0.05 * np.ones(4)),
            p_u31=SpinorVector(0.05 * np.ones(4)),
            s=0.0, K=-1.5, t=0.0, E=-0.5
        )

        traj = integrate_threebody_time_regularized(
            state0, H, (0, 5.0), n_points=50
        )

        r12, r23, r31 = traj.get_pairwise_separations()
        assert len(r12) == 50
        assert len(r23) == 50
        assert len(r31) == 50
        assert np.all(r12 > 0)
        assert np.all(r23 > 0)
        assert np.all(r31 > 0)

    def test_validate_conservation(self):
        """Test conservation validation function."""
        masses = Masses(m1=1.0, m2=1.0, m3=1.0)
        H = ThreeBodyTimeRegularizedHamiltonian(masses=masses)

        u12 = np.array([1.0, 0.0, 0.0, 0.0])
        u23 = np.array([0.0, 1.0, 0.0, 0.0])
        u31 = np.array([0.0, 0.0, 1.0, 0.0])

        # Set K = E·Ω correctly
        Omega0 = 1.0 + 1.0 + 1.0  # sum strategy
        E0 = -0.5
        K0 = E0 * Omega0

        state0 = PairwiseSpinorStateWithTime(
            u12=SpinorVector(u12),
            u23=SpinorVector(u23),
            u31=SpinorVector(u31),
            p_u12=SpinorVector(0.05 * np.ones(4)),
            p_u23=SpinorVector(0.05 * np.ones(4)),
            p_u31=SpinorVector(0.05 * np.ones(4)),
            s=0.0, K=K0, t=0.0, E=E0
        )

        traj = integrate_threebody_time_regularized(
            state0, H, (0, 10.0), n_points=100
        )

        results = traj.validate_conservation()

        assert 'E_conserved' in results
        assert 'E_drift' in results
        assert 'time_relation_satisfied' in results
        assert 'time_relation_error' in results
        # E should be reasonably conserved
        assert results['E_drift'] < 0.1
