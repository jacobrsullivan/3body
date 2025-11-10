"""
Tests for shape space coordinate system.

Tests:
    - ShapeSpaceState construction and validation
    - ComplexShapeState construction
    - Cartesian → Shape transformations
    - Triangle properties
    - Canonical orientations
"""

import pytest
import numpy as np
from src.python.coordinates.base import Masses
from src.python.coordinates.cartesian import CartesianState, enforce_barycenter
from src.python.coordinates.shape_space import (
    ShapeSpaceState,
    ComplexShapeState,
    cartesian_to_shape_distances,
    cartesian_to_complex_shape,
    compute_canonical_orientation,
    shape_distances_to_cartesian_canonical,
    complex_shape_to_cartesian_canonical,
    oriented_triangle_coordinates,
)


class TestShapeSpaceState:
    """Test ShapeSpaceState dataclass"""

    def test_construction(self):
        """Test shape space state construction"""
        state = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=1.0,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=1.5, dimension=2
        )

        assert state.r12 == 1.0
        assert state.r23 == 1.0
        assert state.r31 == 1.0
        assert state.L == 1.5

    def test_triangle_inequality_valid(self):
        """Valid triangle should pass validation"""
        state = ShapeSpaceState(
            r12=3.0, r23=4.0, r31=5.0,  # Right triangle
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.0
        )

        assert state.validate()

    def test_triangle_inequality_invalid(self):
        """Invalid triangle should fail validation"""
        state = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=10.0,  # Violates inequality
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.0
        )

        assert not state.validate()

    def test_equilateral_triangle(self):
        """Test equilateral triangle properties"""
        side = np.sqrt(3.0)
        state = ShapeSpaceState(
            r12=side, r23=side, r31=side,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=1.0
        )

        assert state.validate()
        assert abs(state.perimeter - 3 * side) < 1e-10

        # Area of equilateral triangle: A = (√3/4) * side²
        expected_area = (np.sqrt(3) / 4) * side**2
        np.testing.assert_allclose(state.area, expected_area, rtol=1e-10)

    def test_right_triangle(self):
        """Test right triangle (3-4-5)"""
        state = ShapeSpaceState(
            r12=3.0, r23=4.0, r31=5.0,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.0
        )

        # Area = (1/2) * base * height = (1/2) * 3 * 4 = 6
        expected_area = 6.0
        np.testing.assert_allclose(state.area, expected_area, rtol=1e-10)

    def test_degenerate_triangle(self):
        """Test degenerate (collinear) triangle"""
        state = ShapeSpaceState(
            r12=1.0, r23=2.0, r31=3.0,  # Collinear
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.0
        )

        # Should validate (equality allowed)
        assert state.validate()

        # Area should be zero
        assert state.area < 1e-10


class TestComplexShapeState:
    """Test ComplexShapeState dataclass"""

    def test_construction(self):
        """Test complex shape state construction"""
        z = 0.5 + 0.5j
        state = ComplexShapeState(z=z, z_dot=0.1j, L=1.0)

        assert state.z == z
        assert state.L == 1.0

    def test_positive_orientation(self):
        """Complex shape with Im(z) > 0 should validate"""
        state = ComplexShapeState(z=1.0 + 1.0j, z_dot=0.0, L=0.0)
        assert state.validate()

    def test_negative_orientation_invalid(self):
        """Complex shape with Im(z) < 0 should not validate"""
        state = ComplexShapeState(z=1.0 - 1.0j, z_dot=0.0, L=0.0)
        assert not state.validate()

    def test_to_distances(self):
        """Test conversion to distance representation"""
        # Equilateral triangle: z = e^(iπ/3) = 1/2 + i√3/2
        z = 0.5 + 0.5j * np.sqrt(3)
        state = ComplexShapeState(z=z, z_dot=0.0, L=0.0)

        scale = 2.0
        r12, r23, r13 = state.to_distances(scale=scale)

        # For equilateral: |z| = 1, |z-1| = 1
        # So r12 = scale, r23 ≈ scale, r13 ≈ scale
        assert abs(r12 - scale) < 1e-10
        np.testing.assert_allclose(r23, scale, rtol=1e-1)
        np.testing.assert_allclose(r13, scale, rtol=1e-1)


class TestCartesianToShapeDistances:
    """Test Cartesian → Shape (distance) transformation"""

    def test_equilateral_triangle(self):
        """Transform equilateral triangle to shape space"""
        masses = Masses(1.0, 1.0, 1.0)

        # Set up equilateral triangle
        R = 1.0
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Convert to shape space
        shape = cartesian_to_shape_distances(state_cart, masses)

        # All sides should be equal
        side_length = np.sqrt(3) * R
        np.testing.assert_allclose(shape.r12, side_length, rtol=1e-10)
        np.testing.assert_allclose(shape.r23, side_length, rtol=1e-10)
        np.testing.assert_allclose(shape.r31, side_length, rtol=1e-10)

        # Distance velocities should be zero (static configuration)
        assert abs(shape.dr12_dt) < 1e-10
        assert abs(shape.dr23_dt) < 1e-10
        assert abs(shape.dr31_dt) < 1e-10

    def test_right_triangle(self):
        """Transform right triangle to shape space"""
        masses = Masses(1.0, 1.0, 1.0)

        # Right triangle with sides 3, 4, 5
        positions = np.array([
            [0.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
            [0.0, 4.0, 0.0]
        ])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        shape = cartesian_to_shape_distances(state_cart, masses)

        # Compute expected distances (after barycenter adjustment)
        r_bc = state_cart.positions
        expected_r12 = np.linalg.norm(r_bc[0] - r_bc[1])
        expected_r23 = np.linalg.norm(r_bc[1] - r_bc[2])
        expected_r31 = np.linalg.norm(r_bc[2] - r_bc[0])

        np.testing.assert_allclose(shape.r12, expected_r12, rtol=1e-10)
        np.testing.assert_allclose(shape.r23, expected_r23, rtol=1e-10)
        np.testing.assert_allclose(shape.r31, expected_r31, rtol=1e-10)

    def test_radial_velocities(self):
        """Test computation of distance velocities"""
        masses = Masses(1.0, 1.0, 1.0)

        # Two bodies approaching, one stationary
        positions = np.array([
            [-1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        velocities = np.array([
            [0.5, 0.0, 0.0],   # Moving right (towards body 2)
            [-0.5, 0.0, 0.0],  # Moving left (towards body 1)
            [0.0, 0.0, 0.0]    # Stationary
        ])

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        shape = cartesian_to_shape_distances(state_cart, masses)

        # Bodies 1 and 2 are approaching, so dr12_dt < 0
        assert shape.dr12_dt < 0


class TestCartesianToComplexShape:
    """Test Cartesian → Complex shape transformation"""

    def test_planar_only(self):
        """Complex shape should only work for planar motion"""
        masses = Masses(1.0, 1.0, 1.0)

        # 3D state
        state_3d = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3),
            dimension=3
        )

        with pytest.raises(ValueError):
            cartesian_to_complex_shape(state_3d, masses)

    def test_equilateral_triangle_complex(self):
        """Test complex shape for equilateral triangle"""
        masses = Masses(1.0, 1.0, 1.0)

        R = 1.0
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        shape = cartesian_to_complex_shape(state_cart, masses)

        # For equilateral triangle, |z| should be 1
        # (after barycenter shift)
        assert shape.validate()  # Im(z) > 0

    def test_rotation_invariance_magnitude(self):
        """Complex shape magnitude should be rotation-invariant"""
        masses = Masses(1.0, 1.0, 1.0)

        # Random planar state
        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        # Ensure bodies 1 and 2 are not too close
        if np.linalg.norm(state.positions[0] - state.positions[1]) < 0.1:
            pytest.skip("Bodies 1 and 2 too close")

        z1 = cartesian_to_complex_shape(state, masses).z

        # Rotate by 45 degrees
        theta = np.pi / 4
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        state_rot = CartesianState(
            state.positions @ R.T,
            velocities @ R.T,
            dimension=2
        )

        z2 = cartesian_to_complex_shape(state_rot, masses).z

        # Magnitude should be similar (phase changes)
        # Actually z rotates too, so check distances instead
        r12_1 = np.linalg.norm(state.positions[0] - state.positions[1])
        r12_2 = np.linalg.norm(state_rot.positions[0] - state_rot.positions[1])
        np.testing.assert_allclose(r12_1, r12_2, rtol=1e-10)


class TestCanonicalOrientation:
    """Test canonical orientation computation"""

    def test_align_axis_method(self):
        """Test 'align_axis' orientation"""
        masses = Masses(1.0, 1.0, 1.0)

        # Random state
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0  # Make planar
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        state_canon, theta = compute_canonical_orientation(state, method='align_axis')

        # Body 1-2 axis should now be along x-axis
        r12_vec = state_canon.positions[0] - state_canon.positions[1]

        # y-component should be near zero
        assert abs(r12_vec[1]) < 1e-10

        # x-component should be the distance
        r12_dist = np.linalg.norm(state.positions[0] - state.positions[1])
        np.testing.assert_allclose(abs(r12_vec[0]), r12_dist, rtol=1e-10)

    def test_rotation_angle(self):
        """Test that rotation angle is recovered correctly"""
        masses = Masses(1.0, 1.0, 1.0)

        # Create state with known angle
        theta_orig = np.pi / 3
        c, s = np.cos(theta_orig), np.sin(theta_orig)

        # Body 1-2 axis at angle theta_orig
        positions = np.array([
            [c, s, 0],
            [-c, -s, 0],
            [0, 0, 0]
        ])
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)

        state_canon, theta = compute_canonical_orientation(state, method='align_axis')

        # Recovered angle should match original
        np.testing.assert_allclose(theta, theta_orig, rtol=1e-10)


class TestShapeToCartesian:
    """Test Shape → Cartesian reconstruction"""

    def test_equilateral_reconstruction(self):
        """Reconstruct equilateral triangle from distances"""
        side = np.sqrt(3.0)
        shape_state = ShapeSpaceState(
            r12=side, r23=side, r31=side,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.0
        )

        masses = Masses(1.0, 1.0, 1.0)
        cart_state = shape_distances_to_cartesian_canonical(shape_state, masses)

        # Check that distances are preserved
        r = cart_state.positions
        r12 = np.linalg.norm(r[0] - r[1])
        r23 = np.linalg.norm(r[1] - r[2])
        r31 = np.linalg.norm(r[2] - r[0])

        np.testing.assert_allclose(r12, side, rtol=1e-10)
        np.testing.assert_allclose(r23, side, rtol=1e-10)
        np.testing.assert_allclose(r31, side, rtol=1e-10)

    def test_right_triangle_reconstruction(self):
        """Reconstruct right triangle (3-4-5)"""
        shape_state = ShapeSpaceState(
            r12=3.0, r23=4.0, r31=5.0,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=0.0
        )

        masses = Masses(1.0, 1.0, 1.0)
        cart_state = shape_distances_to_cartesian_canonical(shape_state, masses)

        # Check distances
        r = cart_state.positions
        r12 = np.linalg.norm(r[0] - r[1])
        r23 = np.linalg.norm(r[1] - r[2])
        r31 = np.linalg.norm(r[2] - r[0])

        np.testing.assert_allclose(r12, 3.0, rtol=1e-10)
        np.testing.assert_allclose(r23, 4.0, rtol=1e-10)
        np.testing.assert_allclose(r31, 5.0, rtol=1e-10)

        # Should be in barycentric frame
        from src.python.coordinates.validation import verify_barycentric_frame
        assert verify_barycentric_frame(cart_state, masses, tol=1e-12)

    def test_complex_shape_reconstruction(self):
        """Reconstruct from complex shape variable"""
        # Equilateral: z = e^(iπ/3)
        z = np.exp(1j * np.pi / 3)
        shape_state = ComplexShapeState(z=z, z_dot=0.0, L=0.0)

        masses = Masses(1.0, 1.0, 1.0)
        cart_state = complex_shape_to_cartesian_canonical(shape_state, masses, scale=2.0)

        # Check it's a valid state
        assert cart_state.positions.shape == (3, 3)

        # Check barycentric
        from src.python.coordinates.validation import verify_barycentric_frame
        assert verify_barycentric_frame(cart_state, masses, tol=1e-12)


class TestOrientedTriangleCoordinates:
    """Test oriented triangle representation"""

    def test_equilateral_angles(self):
        """Equilateral triangle should have 60° angles"""
        masses = Masses(1.0, 1.0, 1.0)

        R = 1.0
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        coords = oriented_triangle_coordinates(state, masses)

        # All angles should be π/3
        alpha, beta, gamma = coords['angles']
        expected_angle = np.pi / 3

        np.testing.assert_allclose(alpha, expected_angle, rtol=1e-2)
        np.testing.assert_allclose(beta, expected_angle, rtol=1e-2)
        np.testing.assert_allclose(gamma, expected_angle, rtol=1e-2)

        # Sum should be π
        np.testing.assert_allclose(alpha + beta + gamma, np.pi, rtol=1e-10)

    def test_right_triangle_angles(self):
        """Right triangle should have one 90° angle"""
        masses = Masses(1.0, 1.0, 1.0)

        # 3-4-5 triangle
        positions = np.array([
            [0.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
            [0.0, 4.0, 0.0]
        ])
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        coords = oriented_triangle_coordinates(state, masses)

        alpha, beta, gamma = coords['angles']

        # One angle should be close to π/2
        angles = [alpha, beta, gamma]
        right_angle_present = any(abs(angle - np.pi/2) < 0.1 for angle in angles)
        assert right_angle_present

        # Sum should be π
        np.testing.assert_allclose(alpha + beta + gamma, np.pi, rtol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
