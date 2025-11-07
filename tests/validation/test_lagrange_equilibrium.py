"""
Validation test for Lagrange equilateral equilibrium configuration.

The Lagrange equilateral configuration is an exact solution where three
equal masses sit at the vertices of an equilateral triangle and rotate
rigidly with a specific angular velocity.
"""

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from src.python.coordinates import (
    CartesianState,
    Masses,
    enforce_barycenter,
    ConservationMonitor,
    cartesian_to_jacobi,
    cartesian_to_shape_distances,
)
from src.python.coordinates.cartesian import cartesian_rhs, compute_angular_momentum
from src.python.coordinates.validation import verify_conservation_laws


class TestLagrangeEquilateralConfiguration:
    """Test Lagrange equilateral equilibrium"""

    @staticmethod
    def create_lagrange_state(R: float = 1.0, masses: Masses = None) -> CartesianState:
        """
        Create Lagrange equilateral configuration.

        For equal masses, the angular velocity is ω = √(3GM/R³)
        In units where G=1 and M=3 (total mass), ω = √(3/R³)

        Args:
            R: Radius of circle on which bodies sit
            masses: Mass parameters (default: equal masses)

        Returns:
            CartesianState for rotating equilateral configuration
        """
        if masses is None:
            masses = Masses.equal_masses(1.0)

        # Angles for equilateral triangle
        angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3])

        # Positions on circle of radius R
        positions = R * np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])

        # Angular velocity (for equal masses and G=1)
        M_total = masses.total
        omega = np.sqrt(M_total / R**3)

        # Circular velocities: v = ω × r
        velocities = R * omega * np.column_stack(
            [-np.sin(angles), np.cos(angles), np.zeros(3)]
        )

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        return state

    def test_lagrange_state_creation(self):
        """Test that Lagrange state is created correctly"""
        masses = Masses.equal_masses()
        state = self.create_lagrange_state(R=1.0, masses=masses)

        # Check barycentric
        from src.python.coordinates.validation import verify_barycentric_frame

        assert verify_barycentric_frame(state, masses)

        # Check distances (equilateral)
        r = state.positions
        r12 = np.linalg.norm(r[0] - r[1])
        r23 = np.linalg.norm(r[1] - r[2])
        r31 = np.linalg.norm(r[2] - r[0])

        # All distances should be equal
        assert np.isclose(r12, r23, rtol=1e-10)
        assert np.isclose(r23, r31, rtol=1e-10)

    def test_energy_conservation_short_integration(self):
        """Test energy conservation over one period"""
        masses = Masses.equal_masses(1.0)
        R = 1.0
        state0 = self.create_lagrange_state(R, masses)

        # Period: T = 2π/ω
        omega = np.sqrt(masses.total / R**3)
        T = 2 * np.pi / omega

        # Set up conservation monitor
        monitor = ConservationMonitor(state0, masses)

        # Integrate for one period
        z0 = state0.to_flat()
        t_span = (0, T)
        t_eval = np.linspace(0, T, 100)

        sol = solve_ivp(
            lambda t, z: cartesian_rhs(t, z, masses, dimension=2),
            t_span,
            z0,
            t_eval=t_eval,
            method="DOP853",
            rtol=1e-12,
            atol=1e-12,
        )

        # Record conservation
        for i, t in enumerate(sol.t):
            state_i = CartesianState.from_flat(sol.y[:, i], dimension=2)
            monitor.record(t, state_i, masses)

        # Check conservation
        summary = monitor.get_summary()

        # Energy should be conserved to high precision
        assert summary["energy"]["max_rel_error"] < 1e-10

        # Angular momentum should be conserved
        assert summary["angular_momentum"]["max_error"] < 1e-10

        # Linear momentum should remain zero
        assert summary["linear_momentum"]["max_error"] < 1e-11

    def test_periodic_return(self):
        """Test that configuration returns to initial state after one period"""
        masses = Masses.equal_masses(1.0)
        R = 1.0
        state0 = self.create_lagrange_state(R, masses)

        omega = np.sqrt(masses.total / R**3)
        T = 2 * np.pi / omega

        z0 = state0.to_flat()
        t_span = (0, T)

        sol = solve_ivp(
            lambda t, z: cartesian_rhs(t, z, masses, dimension=2),
            t_span,
            z0,
            method="DOP853",
            rtol=1e-12,
            atol=1e-12,
        )

        z_final = sol.y[:, -1]

        # Should return to initial state (positions rotated, but configuration same)
        # Check distances are preserved
        state_final = CartesianState.from_flat(z_final, dimension=2)

        r0 = state0.positions
        rf = state_final.positions

        d0 = [
            np.linalg.norm(r0[0] - r0[1]),
            np.linalg.norm(r0[1] - r0[2]),
            np.linalg.norm(r0[2] - r0[0]),
        ]
        df = [
            np.linalg.norm(rf[0] - rf[1]),
            np.linalg.norm(rf[1] - rf[2]),
            np.linalg.norm(rf[2] - rf[0]),
        ]

        for i in range(3):
            assert np.isclose(d0[i], df[i], rtol=1e-9)

    def test_shape_space_constant(self):
        """Test that shape space coordinates remain constant (rigid rotation)"""
        masses = Masses.equal_masses(1.0)
        R = 1.0
        state0 = self.create_lagrange_state(R, masses)

        shape0 = cartesian_to_shape_distances(state0, masses)

        omega = np.sqrt(masses.total / R**3)
        T = 2 * np.pi / omega

        z0 = state0.to_flat()
        t_span = (0, T / 4)  # Quarter period
        t_eval = np.linspace(0, T / 4, 20)

        sol = solve_ivp(
            lambda t, z: cartesian_rhs(t, z, masses, dimension=2),
            t_span,
            z0,
            t_eval=t_eval,
            method="DOP853",
            rtol=1e-12,
            atol=1e-12,
        )

        # Check that distances remain constant
        for i in range(len(sol.t)):
            state_i = CartesianState.from_flat(sol.y[:, i], dimension=2)
            shape_i = cartesian_to_shape_distances(state_i, masses)

            # Distances should be constant (rigid rotation)
            assert np.isclose(shape_i.r12, shape0.r12, rtol=1e-8)
            assert np.isclose(shape_i.r23, shape0.r23, rtol=1e-8)
            assert np.isclose(shape_i.r31, shape0.r31, rtol=1e-8)

    def test_angular_momentum_constant(self):
        """Test that angular momentum is constant"""
        masses = Masses.equal_masses(1.0)
        R = 1.0
        state0 = self.create_lagrange_state(R, masses)

        L0 = compute_angular_momentum(state0, masses)

        omega = np.sqrt(masses.total / R**3)
        T = 2 * np.pi / omega

        z0 = state0.to_flat()
        t_span = (0, T)
        t_eval = np.linspace(0, T, 50)

        sol = solve_ivp(
            lambda t, z: cartesian_rhs(t, z, masses, dimension=2),
            t_span,
            z0,
            t_eval=t_eval,
            method="DOP853",
            rtol=1e-12,
            atol=1e-12,
        )

        # Check angular momentum at all times
        for i in range(len(sol.t)):
            state_i = CartesianState.from_flat(sol.y[:, i], dimension=2)
            L_i = compute_angular_momentum(state_i, masses)

            np.testing.assert_allclose(L_i, L0, atol=1e-11)

    def test_jacobi_coordinates_rigid_rotation(self):
        """Test that internal Jacobi coordinates remain constant"""
        masses = Masses.equal_masses(1.0)
        R = 1.0
        state0 = self.create_lagrange_state(R, masses)

        jacobi0 = cartesian_to_jacobi(state0, masses)

        omega = np.sqrt(masses.total / R**3)
        T = 2 * np.pi / omega

        z0 = state0.to_flat()
        t_span = (0, T / 4)
        t_eval = np.linspace(0, T / 4, 20)

        sol = solve_ivp(
            lambda t, z: cartesian_rhs(t, z, masses, dimension=2),
            t_span,
            z0,
            t_eval=t_eval,
            method="DOP853",
            rtol=1e-12,
            atol=1e-12,
        )

        # Check Jacobi internal coordinates
        for i in range(len(sol.t)):
            state_i = CartesianState.from_flat(sol.y[:, i], dimension=2)
            jacobi_i = cartesian_to_jacobi(state_i, masses)

            # Magnitudes of internal coordinates should be constant
            assert np.isclose(
                np.linalg.norm(jacobi_i.r1), np.linalg.norm(jacobi0.r1), rtol=1e-8
            )
            assert np.isclose(
                np.linalg.norm(jacobi_i.r2), np.linalg.norm(jacobi0.r2), rtol=1e-8
            )

    def test_different_radii(self):
        """Test Lagrange configuration for different radii"""
        masses = Masses.equal_masses(1.0)

        for R in [0.5, 1.0, 2.0, 5.0]:
            state = self.create_lagrange_state(R, masses)

            # Verify barycentric
            from src.python.coordinates.validation import verify_barycentric_frame

            assert verify_barycentric_frame(state, masses)

            # Verify distances scale with R
            shape = cartesian_to_shape_distances(state, masses)
            expected_side = np.sqrt(3) * R

            assert np.isclose(shape.r12, expected_side, rtol=0.01)

    def test_unequal_masses_not_equilibrium(self):
        """Test that unequal masses don't give equilibrium with this configuration"""
        # This is a sanity check - equal-mass solution doesn't work for unequal masses
        masses = Masses(1.0, 2.0, 1.0)  # Unequal!
        R = 1.0

        # Use equal-mass formula (will NOT be equilibrium)
        angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3])
        positions = R * np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])

        # Use equal-mass omega (WRONG for unequal masses)
        omega = np.sqrt(3.0 / R**3)  # Assumes total mass = 3
        velocities = R * omega * np.column_stack(
            [-np.sin(angles), np.cos(angles), np.zeros(3)]
        )

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        # Integrate briefly
        z0 = state.to_flat()
        t_span = (0, 1.0)

        sol = solve_ivp(
            lambda t, z: cartesian_rhs(t, z, masses, dimension=2),
            t_span,
            z0,
            method="RK45",
            rtol=1e-9,
            atol=1e-9,
        )

        state_final = CartesianState.from_flat(sol.y[:, -1], dimension=2)

        # Shape should have changed (not rigid rotation)
        shape0 = cartesian_to_shape_distances(state, masses)
        shape_final = cartesian_to_shape_distances(state_final, masses)

        # At least one distance should have changed significantly
        distance_changes = [
            abs(shape_final.r12 - shape0.r12),
            abs(shape_final.r23 - shape0.r23),
            abs(shape_final.r31 - shape0.r31),
        ]

        assert max(distance_changes) > 0.01  # Significant change
