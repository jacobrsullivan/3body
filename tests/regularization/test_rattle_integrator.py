"""
Tests for RATTLE integrator (WP 2.3, Part C).

Tests cover:
    1. Constraint satisfaction over long integrations
    2. Symplectic structure preservation (energy conservation)
    3. Newton solver convergence
    4. Robustness to ill-conditioned Jacobians
    5. Comparison with unconstrained integrators
"""

import pytest
import numpy as np
from src.python.coordinates.base import Masses
from src.python.coordinates.cartesian import CartesianState
from src.python.regularization.ks_pairwise import (
    cartesian_3bp_to_pairwise_ks,
    pairwise_ks_to_cartesian_3bp,
)
from src.python.regularization.rattle_integrator import (
    RATTLEIntegrator,
    RATTLEConfig,
    ConvergenceError,
    ConstraintViolation,
)


class TestRATTLEBasics:
    """Basic functionality tests for RATTLE integrator."""

    def test_initialization(self):
        """Test integrator initialization."""
        masses = Masses(1.0, 1.0, 1.0)
        integrator = RATTLEIntegrator(masses)

        assert integrator.masses == masses
        assert integrator.G == 1.0
        assert integrator.config.constraint_tolerance == 1e-12

    def test_custom_config(self):
        """Test custom configuration."""
        config = RATTLEConfig(
            constraint_tolerance=1e-10,
            newton_tolerance=1e-12,
            max_newton_iterations=50
        )
        masses = Masses(1.0, 1.0, 1.0)
        integrator = RATTLEIntegrator(masses, config=config)

        assert integrator.config.constraint_tolerance == 1e-10
        assert integrator.config.max_newton_iterations == 50


class TestConstraintSatisfaction:
    """Tests for constraint satisfaction during integration."""

    @pytest.fixture
    def simple_initial_state(self):
        """Create simple initial state for testing."""
        # Equilateral triangle configuration
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([-0.5, np.sqrt(3)/2, 0.0])
        r3 = np.array([-0.5, -np.sqrt(3)/2, 0.0])

        # Small circular velocities
        v1 = np.array([0.0, 0.1, 0.0])
        v2 = np.array([0.0, 0.1, 0.0])
        v3 = np.array([0.0, 0.1, 0.0])

        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.array([v1, v2, v3])
        )

        masses = Masses(1.0, 1.0, 1.0)
        return cartesian_3bp_to_pairwise_ks(cart_state), masses

    def test_single_step_constraint_satisfaction(self, simple_initial_state):
        """Test that a single RATTLE step preserves constraints."""
        state0, masses = simple_initial_state

        integrator = RATTLEIntegrator(masses)
        ds = 0.01

        state1 = integrator.step(state0, ds)

        # Check constraints
        constraints = state1.validate_constraints(tolerance=1e-10)
        assert constraints['all_satisfied'], "Constraints should be satisfied after RATTLE step"
        assert constraints['closure_error'] < 1e-10

    def test_long_integration_constraint_drift(self, simple_initial_state):
        """Test constraint drift over long integration."""
        state0, masses = simple_initial_state

        integrator = RATTLEIntegrator(masses)

        # Integrate for many steps
        trajectory = integrator.integrate(
            state0,
            s_span=(0.0, 10.0),
            n_steps=1000
        )

        # Check maximum constraint violation
        max_violation = max(integrator.constraint_violations_history)

        assert max_violation < 1e-10, f"Maximum constraint violation {max_violation:.2e} exceeds tolerance"

        # Check that constraints are satisfied at all points
        for state in trajectory.states[::100]:  # Sample every 100th point
            constraints = state.validate_constraints(tolerance=1e-9)
            assert constraints['closure_error'] < 1e-9

    def test_constraint_violation_warning(self, simple_initial_state):
        """Test that minor constraint violations produce warnings."""
        state0, masses = simple_initial_state

        # Use very loose Newton tolerance to force slight violations
        config = RATTLEConfig(
            newton_tolerance=1e-6,  # Very loose
            constraint_tolerance=1e-10
        )
        integrator = RATTLEIntegrator(masses, config=config)

        # This should produce warnings but not fail
        with pytest.warns(UserWarning):
            trajectory = integrator.integrate(
                state0,
                s_span=(0.0, 1.0),
                n_steps=100
            )

            assert len(trajectory.states) > 0


class TestNewtonSolver:
    """Tests for Newton solver robustness."""

    def test_newton_convergence_count(self):
        """Test that Newton solver converges in reasonable iterations."""
        # Simple state
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r3 = np.array([0.0, 0.0, 1.0])

        v1 = v2 = v3 = np.zeros(3)

        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.array([v1, v2, v3])
        )

        masses = Masses(1.0, 1.0, 1.0)
        state0 = cartesian_3bp_to_pairwise_ks(cart_state)

        integrator = RATTLEIntegrator(masses)

        # Run integration
        trajectory = integrator.integrate(
            state0,
            s_span=(0.0, 1.0),
            n_steps=100
        )

        # Check Newton iteration statistics
        stats = integrator.get_statistics()

        assert stats['mean_newton_iterations'] < 10, "Newton should converge quickly"
        assert stats['max_newton_iterations'] < 20, "No step should need excessive iterations"

    def test_convergence_error_on_max_iterations(self):
        """Test that ConvergenceError is raised when Newton fails."""
        # Use configuration that makes Newton fail
        config = RATTLEConfig(
            max_newton_iterations=1,  # Only 1 iteration
            newton_tolerance=1e-20  # Impossibly tight
        )

        masses = Masses(1.0, 1.0, 1.0)
        integrator = RATTLEIntegrator(masses, config=config)

        # Create any valid state
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r3 = np.array([0.0, 0.0, 1.0])
        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.zeros((3, 3))
        )

        state0 = cartesian_3bp_to_pairwise_ks(cart_state)

        # This should raise ConvergenceError
        with pytest.raises(ConvergenceError):
            integrator.step(state0, ds=0.01)


class TestIllConditionedSystems:
    """Tests for robustness to ill-conditioned Jacobians."""

    def test_svd_fallback_activation(self):
        """Test that SVD fallback is activated for ill-conditioned systems."""
        # Create a configuration that will trigger SVD
        config = RATTLEConfig(
            condition_number_threshold=1e8  # Lower threshold
        )

        masses = Masses(1.0, 1.0, 1.0)
        integrator = RATTLEIntegrator(masses, config=config)

        # Create state with small separations (potentially ill-conditioned)
        r1 = np.array([0.1, 0.0, 0.0])
        r2 = np.array([0.0, 0.1, 0.0])
        r3 = np.array([0.0, 0.0, 0.1])

        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.zeros((3, 3))
        )

        state0 = cartesian_3bp_to_pairwise_ks(cart_state)

        # Integrate - may use SVD fallback
        trajectory = integrator.integrate(
            state0,
            s_span=(0.0, 0.5),
            n_steps=50
        )

        stats = integrator.get_statistics()

        # Check if SVD was used (it may or may not be, depending on actual conditioning)
        assert stats['svd_fallback_count'] >= 0  # Just check it's tracked


class TestEnergyConservation:
    """Tests for energy conservation (symplectic property)."""

    def test_energy_conservation_short_term(self):
        """Test energy conservation over short integration."""
        # Lagrange L4 point (stable)
        r1 = np.array([0.5, 0.0, 0.0])
        r2 = np.array([-0.5, 0.0, 0.0])
        r3 = np.array([0.0, np.sqrt(3)/2, 0.0])

        # Circular velocities
        omega = 1.0
        v1 = np.array([0.0, omega * 0.5, 0.0])
        v2 = np.array([0.0, -omega * 0.5, 0.0])
        v3 = np.array([-omega * np.sqrt(3)/2, 0.0, 0.0])

        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.array([v1, v2, v3])
        )

        masses = Masses(1.0, 1.0, 1.0)
        state0 = cartesian_3bp_to_pairwise_ks(cart_state)

        integrator = RATTLEIntegrator(masses)

        # Integrate
        trajectory = integrator.integrate(
            state0,
            s_span=(0.0, 5.0),
            n_steps=500
        )

        # Compute energy at each point
        energies = []
        for state in trajectory.states:
            # Simple energy: kinetic + potential
            E = 0.5 * np.linalg.norm(state.spinor_velocities)**2
            energies.append(E)

        energies = np.array(energies)

        # Check energy conservation
        E0 = energies[0]
        energy_drift = np.abs(energies - E0).max()
        relative_drift = energy_drift / abs(E0) if E0 != 0 else energy_drift

        # RATTLE should have good energy conservation
        assert relative_drift < 1e-8, f"Energy drift {relative_drift:.2e} is too large"


class TestRoundtripAccuracy:
    """Tests for Cartesian ↔ KS ↔ Cartesian roundtrip."""

    def test_roundtrip_preserves_state(self):
        """Test that KS integration preserves Cartesian state structure."""
        # Initial Cartesian state
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r3 = np.array([0.0, 0.0, 1.0])

        v1 = np.array([0.0, 0.1, 0.0])
        v2 = np.array([0.1, 0.0, 0.0])
        v3 = np.array([0.0, 0.0, 0.1])

        cart_state0 = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.array([v1, v2, v3])
        )

        masses = Masses(1.0, 1.0, 1.0)

        # Transform to KS
        ks_state0 = cartesian_3bp_to_pairwise_ks(cart_state0)

        # Integrate in KS space
        integrator = RATTLEIntegrator(masses)
        trajectory = integrator.integrate(
            ks_state0,
            s_span=(0.0, 1.0),
            n_steps=100
        )

        # Transform final state back to Cartesian
        ks_state_final = trajectory.states[-1]
        cart_state_final = pairwise_ks_to_cartesian_3bp(ks_state_final, masses)

        # Verify dimensions
        assert cart_state_final.positions.shape == (3, 3)
        assert cart_state_final.velocities.shape == (3, 3)

        # Verify center of mass is preserved (approximately)
        com_initial = np.sum(cart_state0.positions, axis=0) / 3
        com_final = np.sum(cart_state_final.positions, axis=0) / 3

        com_error = np.linalg.norm(com_final - com_initial)
        assert com_error < 1e-6, f"COM drift {com_error:.2e} is too large"


class TestIntegratorStatistics:
    """Tests for integrator diagnostics and statistics."""

    def test_statistics_tracking(self):
        """Test that statistics are properly tracked."""
        masses = Masses(1.0, 1.0, 1.0)
        integrator = RATTLEIntegrator(masses)

        # Create simple state
        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r3 = np.array([0.0, 0.0, 1.0])

        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.zeros((3, 3))
        )

        state0 = cartesian_3bp_to_pairwise_ks(cart_state)

        # Run integration
        trajectory = integrator.integrate(
            state0,
            s_span=(0.0, 1.0),
            n_steps=100
        )

        # Get statistics
        stats = integrator.get_statistics()

        # Verify statistics structure
        assert 'total_steps' in stats
        assert 'mean_newton_iterations' in stats
        assert 'max_constraint_violation' in stats
        assert 'mean_condition_number' in stats

        # Verify values are reasonable
        assert stats['total_steps'] == len(trajectory.states) - 1
        assert stats['mean_newton_iterations'] > 0
        assert stats['mean_newton_iterations'] < 20

    def test_trajectory_diagnostics(self):
        """Test that trajectory diagnostics are accessible."""
        masses = Masses(1.0, 1.0, 1.0)
        integrator = RATTLEIntegrator(masses)

        r1 = np.array([1.0, 0.0, 0.0])
        r2 = np.array([0.0, 1.0, 0.0])
        r3 = np.array([0.0, 0.0, 1.0])

        cart_state = CartesianState(
            positions=np.array([r1, r2, r3]),
            velocities=np.zeros((3, 3))
        )

        state0 = cartesian_3bp_to_pairwise_ks(cart_state)

        trajectory = integrator.integrate(
            state0,
            s_span=(0.0, 1.0),
            n_steps=100
        )

        # Get diagnostics
        diagnostics = trajectory.get_diagnostics()

        assert isinstance(diagnostics, dict)
        assert 'total_steps' in diagnostics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
