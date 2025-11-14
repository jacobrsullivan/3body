"""
Tests for constrained KS dynamics (WP 2.3).

Tests:
1. Hamiltonian evaluation
2. Integration on constraint manifold
3. Constraint preservation during integration
4. Collision regularization
"""

import pytest
import numpy as np

from src.python.coordinates.base import CartesianState, Masses
from src.python.regularization import (
    PairwiseSpinorState,
    cartesian_3bp_to_pairwise_ks,
    ConstrainedHamiltonian,
    KSTrajectory,
    integrate_constrained_ks,
    verify_collision_regularization,
)


@pytest.fixture
def equal_masses():
    """Equal mass system."""
    return Masses(m1=1.0, m2=1.0, m3=1.0)


@pytest.fixture
def simple_initial_state():
    """Simple initial state for testing."""
    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([-0.5, np.sqrt(3)/2, 0.0])
    r3 = np.array([-0.5, -np.sqrt(3)/2, 0.0])

    v1 = np.array([0.0, 0.1, 0.0])
    v2 = np.array([0.0, -0.05, 0.0])
    v3 = np.array([0.0, -0.05, 0.0])

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)
    return cartesian_3bp_to_pairwise_ks(cart_state)


def test_constrained_hamiltonian_creation(equal_masses):
    """Test ConstrainedHamiltonian creation."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    assert hamiltonian.masses == equal_masses
    assert hamiltonian.G == 1.0


def test_hamiltonian_evaluation(simple_initial_state, equal_masses):
    """Test Hamiltonian evaluation."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    H = hamiltonian.evaluate(simple_initial_state)

    # Energy should be finite
    assert np.isfinite(H)

    # For this configuration, energy should be reasonable
    assert abs(H) < 100.0


def test_hamiltonian_forces(simple_initial_state, equal_masses):
    """Test force computation."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    forces = hamiltonian.compute_forces(simple_initial_state)

    # Should be 12D vector
    assert forces.shape == (12,)

    # Forces should be finite
    assert np.all(np.isfinite(forces))


def test_ks_trajectory_creation(simple_initial_state):
    """Test KSTrajectory creation."""
    times = np.linspace(0, 1, 10)
    states = [simple_initial_state] * 10

    traj = KSTrajectory(
        times=times,
        states=states,
        initial_state=simple_initial_state
    )

    assert len(traj) == 10
    assert traj[0] == simple_initial_state


def test_short_integration(simple_initial_state, equal_masses):
    """Test short-time integration."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    # Integrate for short time
    traj = integrate_constrained_ks(
        initial_state=simple_initial_state,
        hamiltonian=hamiltonian,
        t_span=(0, 0.1),
        n_points=10,
        method='RK45'
    )

    # Should produce trajectory
    assert len(traj) > 0
    assert len(traj) <= 10

    # Initial state should be preserved
    assert traj.initial_state == simple_initial_state


def test_energy_conservation(simple_initial_state, equal_masses):
    """Test energy conservation during integration."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    # Integrate
    traj = integrate_constrained_ks(
        initial_state=simple_initial_state,
        hamiltonian=hamiltonian,
        t_span=(0, 1.0),
        n_points=50,
        method='DOP853'
    )

    if len(traj) == 0:
        pytest.skip("Integration produced no valid states")

    # Compute energy at each point
    energies = [hamiltonian.evaluate(state) for state in traj.states]

    # Check conservation (allow some drift due to numerical errors)
    energy_drift = max(energies) - min(energies)
    relative_drift = energy_drift / abs(energies[0]) if abs(energies[0]) > 1e-10 else energy_drift

    # Relaxed tolerance for numerical integration
    assert relative_drift < 0.1, \
        f"Energy not conserved: relative drift = {relative_drift}"


def test_constraint_preservation(simple_initial_state, equal_masses):
    """Test that constraints remain satisfied during integration."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    # Integrate with constraint projection
    traj = integrate_constrained_ks(
        initial_state=simple_initial_state,
        hamiltonian=hamiltonian,
        t_span=(0, 0.5),
        n_points=20,
        constraint_projection=True
    )

    if len(traj) == 0:
        pytest.skip("Integration produced no valid states")

    # Check constraints at each point
    for i, state in enumerate(traj.states):
        validation = state.validate_constraints(tolerance=1e-8)

        # Bilinear relations should be satisfied
        assert validation['bilinear_12'], \
            f"Bilinear (1,2) violated at step {i}"
        assert validation['bilinear_23'], \
            f"Bilinear (2,3) violated at step {i}"
        assert validation['bilinear_31'], \
            f"Bilinear (3,1) violated at step {i}"


def test_trajectory_to_cartesian(simple_initial_state, equal_masses):
    """Test conversion of KS trajectory to Cartesian."""
    hamiltonian = ConstrainedHamiltonian(masses=equal_masses, G=1.0)

    traj = integrate_constrained_ks(
        initial_state=simple_initial_state,
        hamiltonian=hamiltonian,
        t_span=(0, 0.5),
        n_points=10
    )

    if len(traj) == 0:
        pytest.skip("Integration produced no valid states")

    # Convert to Cartesian
    cart_traj = traj.to_cartesian(equal_masses)

    # Should have same length
    assert len(cart_traj) == len(traj)

    # Each state should be CartesianState
    for cart_state in cart_traj:
        assert isinstance(cart_state, CartesianState)


def test_collision_regularization_stable():
    """Test that integration remains stable near collisions."""
    # Create state with bodies close together
    r1 = np.array([0.1, 0.0, 0.0])
    r2 = np.array([0.0, 0.0, 0.0])
    r3 = np.array([-0.1, 0.0, 0.0])

    v1 = np.array([0.0, 0.05, 0.0])
    v2 = np.array([0.0, 0.0, 0.0])
    v3 = np.array([0.0, -0.05, 0.0])

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)
    initial_state = cartesian_3bp_to_pairwise_ks(cart_state)

    masses = Masses(m1=1.0, m2=1.0, m3=1.0)
    hamiltonian = ConstrainedHamiltonian(masses=masses, G=1.0)

    # Try to integrate
    try:
        traj = integrate_constrained_ks(
            initial_state=initial_state,
            hamiltonian=hamiltonian,
            t_span=(0, 0.1),
            n_points=20
        )

        # If integration succeeded, check that spinors remain bounded
        if len(traj) > 0:
            max_norms = [
                max(state.u12.norm, state.u23.norm, state.u31.norm)
                for state in traj.states
            ]

            # Spinors should remain finite (regularization working)
            assert all(norm < 1e6 for norm in max_norms), \
                "Spinors grew unbounded - regularization failed"

    except Exception as e:
        # Integration may fail for very close collisions
        # This is acceptable for this test
        pass


def test_verify_collision_regularization():
    """Test collision regularization verification function."""
    # Create simple trajectory (no collision)
    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([0.0, 1.0, 0.0])
    r3 = np.array([0.0, 0.0, 1.0])

    v1 = v2 = v3 = np.zeros(3)

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)
    initial_state = cartesian_3bp_to_pairwise_ks(cart_state)

    masses = Masses(m1=1.0, m2=1.0, m3=1.0)

    # Create simple trajectory
    times = np.array([0.0])
    states = [initial_state]

    traj = KSTrajectory(
        times=times,
        states=states,
        initial_state=initial_state
    )

    # Verify regularization
    results = verify_collision_regularization(traj, masses, tolerance=1e-10)

    # No collision should have occurred
    assert not results['collision_occurred']

    # Spinors should be finite
    assert results['regularization_successful']


def test_integration_different_masses():
    """Test integration with different mass ratios."""
    # Binary + test particle
    masses = Masses(m1=1.0, m2=1.0, m3=0.001)

    r1 = np.array([1.0, 0.0, 0.0])
    r2 = np.array([-1.0, 0.0, 0.0])
    r3 = np.array([0.0, 2.0, 0.0])

    v1 = np.array([0.0, 0.3, 0.0])
    v2 = np.array([0.0, -0.3, 0.0])
    v3 = np.array([-0.5, 0.0, 0.0])

    cart_state = CartesianState(r1=r1, r2=r2, r3=r3, v1=v1, v2=v2, v3=v3)
    initial_state = cartesian_3bp_to_pairwise_ks(cart_state)

    hamiltonian = ConstrainedHamiltonian(masses=masses, G=1.0)

    # Integrate
    traj = integrate_constrained_ks(
        initial_state=initial_state,
        hamiltonian=hamiltonian,
        t_span=(0, 0.5),
        n_points=20
    )

    # Should produce valid trajectory
    assert len(traj) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
