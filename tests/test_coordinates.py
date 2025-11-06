"""
Tests for coordinate transformation utilities.
"""

import numpy as np
import pytest
from src.python.utils import coordinates


class TestRotationMatrix:
    """Test rotation matrix properties."""

    def test_rotation_matrix_orthogonal(self):
        """Rotation matrices should be orthogonal (R^T R = I)."""
        for t in [0.0, np.pi/4, np.pi/2, np.pi, 2*np.pi]:
            R = coordinates.rotation_matrix(t)
            # Check orthogonality
            identity = R.T @ R
            assert np.allclose(identity, np.eye(3), atol=1e-14)

    def test_rotation_matrix_det_one(self):
        """Rotation matrices should have determinant = 1."""
        for t in [0.0, 1.0, 2.0, np.pi]:
            R = coordinates.rotation_matrix(t)
            det = np.linalg.det(R)
            assert np.isclose(det, 1.0, atol=1e-14)

    def test_rotation_matrix_periodic(self):
        """Rotation matrix should be periodic with period 2π."""
        t = 1.5
        R1 = coordinates.rotation_matrix(t)
        R2 = coordinates.rotation_matrix(t + 2*np.pi)
        assert np.allclose(R1, R2, atol=1e-14)

    def test_rotation_matrix_identity_at_zero(self):
        """At t=0, rotation matrix should be identity."""
        R = coordinates.rotation_matrix(0.0)
        assert np.allclose(R, np.eye(3), atol=1e-14)


class TestRoundTripTransformation:
    """Test round-trip coordinate transformations."""

    def test_roundtrip_origin(self):
        """Round-trip transformation at origin."""
        state_rot = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        t = 1.0
        assert coordinates.verify_transformation_roundtrip(state_rot, t)

    def test_roundtrip_general_state(self):
        """Round-trip transformation for general state."""
        state_rot = np.array([1.2, 0.5, 0.1, -0.3, 0.8, 0.05])
        for t in [0.0, 1.0, np.pi, 5.0]:
            assert coordinates.verify_transformation_roundtrip(state_rot, t)

    def test_roundtrip_various_times(self):
        """Round-trip at various times."""
        state_rot = np.array([1.0, 0.5, 0.0, 0.2, 0.4, 0.0])
        times = np.linspace(0, 2*np.pi, 20)
        for t in times:
            assert coordinates.verify_transformation_roundtrip(state_rot, t)


class TestCoordinateTransformation:
    """Test individual transformation functions."""

    def test_position_transformation_at_t_zero(self):
        """At t=0, position should be unchanged."""
        state_rot = np.array([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])
        state_inertial = coordinates.corotating_to_inertial(state_rot, 0.0)

        # Position should be same at t=0
        assert np.allclose(state_inertial[:3], state_rot[:3], atol=1e-14)

    def test_velocity_includes_rotation_effect(self):
        """Velocity transformation should include frame rotation."""
        # At t=0, for a point at (r, 0, 0) with v_rot = 0
        # v_inertial should have y-component from rotation
        r = 1.5
        state_rot = np.array([r, 0.0, 0.0, 0.0, 0.0, 0.0])
        state_inertial = coordinates.corotating_to_inertial(state_rot, 0.0)

        # At t=0: dR/dt @ r = [0, r, 0]
        # So v_inertial should be [0, r, 0] for stationary point in rotating frame
        assert np.isclose(state_inertial[3], 0.0, atol=1e-14)
        assert np.isclose(state_inertial[4], r, atol=1e-14)
        assert np.isclose(state_inertial[5], 0.0, atol=1e-14)

    def test_transformation_preserves_z_axis(self):
        """Z-axis is rotation axis, should be preserved."""
        state_rot = np.array([1.0, 2.0, 3.5, 0.1, 0.2, 0.7])
        t = 2.3
        state_inertial = coordinates.corotating_to_inertial(state_rot, t)

        # Z position and velocity should be unchanged
        assert np.isclose(state_inertial[2], state_rot[2], atol=1e-14)
        assert np.isclose(state_inertial[5], state_rot[5], atol=1e-14)


class TestTrajectoryTransformation:
    """Test batch trajectory transformations."""

    def test_single_state_trajectory(self):
        """Transform single state (N=1 trajectory)."""
        state_rot = np.array([[1.0, 0.5, 0.0, 0.2, 0.3, 0.0]])
        times = np.array([1.5])

        states_inertial = coordinates.transform_trajectory_to_inertial(
            state_rot, times
        )

        assert states_inertial.shape == (1, 6)

        # Verify matches single transformation
        expected = coordinates.corotating_to_inertial(state_rot[0], times[0])
        assert np.allclose(states_inertial[0], expected, atol=1e-14)

    def test_multiple_state_trajectory(self):
        """Transform multi-point trajectory."""
        n_points = 10
        times = np.linspace(0, 2*np.pi, n_points)
        states_rot = np.random.randn(n_points, 6)

        states_inertial = coordinates.transform_trajectory_to_inertial(
            states_rot, times
        )

        assert states_inertial.shape == (n_points, 6)

        # Verify each point
        for i in range(n_points):
            expected = coordinates.corotating_to_inertial(states_rot[i], times[i])
            assert np.allclose(states_inertial[i], expected, atol=1e-14)

    def test_trajectory_roundtrip(self):
        """Round-trip trajectory transformation."""
        n_points = 20
        times = np.linspace(0, 10, n_points)
        states_rot = np.random.randn(n_points, 6)

        # Forward and back
        states_inertial = coordinates.transform_trajectory_to_inertial(
            states_rot, times
        )
        states_recovered = coordinates.transform_trajectory_to_corotating(
            states_inertial, times
        )

        assert np.allclose(states_recovered, states_rot, atol=1e-13)


class TestPrimaryPositions:
    """Test primary body position calculations."""

    def test_primaries_opposite_sides_at_t_zero(self):
        """At t=0, primaries should be on opposite sides of x-axis."""
        mu = 0.3
        r1, r2 = coordinates.primary_positions_inertial(mu, 0.0)

        # At t=0, should be along x-axis
        assert np.isclose(r1[1], 0.0, atol=1e-14)
        assert np.isclose(r2[1], 0.0, atol=1e-14)
        assert np.isclose(r1[2], 0.0, atol=1e-14)
        assert np.isclose(r2[2], 0.0, atol=1e-14)

        # Check distances from origin
        # r1 (larger mass, m=1-μ) is at distance μ from origin
        # r2 (smaller mass, m=μ) is at distance 1-μ from origin
        assert np.isclose(np.linalg.norm(r1), mu, atol=1e-14)
        assert np.isclose(np.linalg.norm(r2), 1 - mu, atol=1e-14)

    def test_primaries_barycenter_at_origin(self):
        """Barycenter should always be at origin."""
        mu = 0.15
        times = np.linspace(0, 2*np.pi, 10)

        for t in times:
            r1, r2 = coordinates.primary_positions_inertial(mu, t)
            # Barycenter: (1-μ)*r1 + μ*r2 = 0
            barycenter = (1 - mu) * r1 + mu * r2
            assert np.allclose(barycenter, 0.0, atol=1e-14)

    def test_primaries_constant_separation(self):
        """Distance between primaries should be constant."""
        mu = 0.2
        times = np.linspace(0, 2*np.pi, 20)

        separations = []
        for t in times:
            r1, r2 = coordinates.primary_positions_inertial(mu, t)
            separation = np.linalg.norm(r2 - r1)
            separations.append(separation)

        # All separations should be 1.0 (system length scale)
        assert np.allclose(separations, 1.0, atol=1e-14)

    def test_primaries_circular_motion(self):
        """Primaries should move in circles."""
        mu = 0.1
        n_points = 50
        times = np.linspace(0, 2*np.pi, n_points)

        r1_positions = np.array([
            coordinates.primary_positions_inertial(mu, t)[0] for t in times
        ])

        # Check constant radius
        # r1 (larger mass) orbits at distance μ from barycenter
        radii_1 = np.linalg.norm(r1_positions, axis=1)
        assert np.allclose(radii_1, mu, atol=1e-13)


class TestCoordinateIntegration:
    """Integration tests for coordinate transformations."""

    def test_lagrange_point_l4_stationary_in_rotating(self):
        """L4 point is stationary in rotating frame but moves in inertial."""
        mu = 0.01215  # Earth-Moon
        # L4 is at equilateral triangle with primaries
        l4_rot = np.array([0.5 - mu, np.sqrt(3)/2, 0.0, 0.0, 0.0, 0.0])

        # Transform at different times
        times = np.array([0.0, np.pi/4, np.pi/2, np.pi])
        states_inertial = coordinates.transform_trajectory_to_inertial(
            np.tile(l4_rot, (len(times), 1)), times
        )

        # In inertial frame, should be moving (different positions)
        positions = states_inertial[:, :2]  # x, y positions
        # Check that positions are different
        for i in range(1, len(times)):
            assert not np.allclose(positions[i], positions[0], atol=1e-10)

        # But round-trip should work
        states_recovered = coordinates.transform_trajectory_to_corotating(
            states_inertial, times
        )
        assert np.allclose(states_recovered, np.tile(l4_rot, (len(times), 1)), atol=1e-13)
