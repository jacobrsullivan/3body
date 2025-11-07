"""
Unit tests for shape space coordinate system.
"""

import numpy as np
import pytest

from src.python.coordinates import (
    CartesianState,
    ShapeSpaceState,
    ComplexShapeState,
    Masses,
    enforce_barycenter,
    cartesian_to_shape_distances,
    cartesian_to_complex_shape,
)
from src.python.coordinates.shape_space import (
    compute_canonical_orientation,
    oriented_triangle_coordinates,
)


class TestShapeSpaceState:
    """Test ShapeSpaceState dataclass"""

    def test_construction(self):
        """Test basic construction"""
        state = ShapeSpaceState(
            r12=1.0,
            r23=1.0,
            r31=1.5,
            dr12_dt=0.0,
            dr23_dt=0.0,
            dr31_dt=0.0,
            L=1.0,
        )

        assert state.r12 == 1.0
        assert state.r23 == 1.0
        assert state.r31 == 1.5

    def test_triangle_inequality_valid(self):
        """Test valid triangle satisfies inequality"""
        state = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=1.5, dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0, L=0.0
        )

        assert state.validate()

    def test_triangle_inequality_invalid(self):
        """Test invalid triangle violates inequality"""
        # Degenerate: one side > sum of others
        state = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=3.0, dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0, L=0.0
        )

        assert not state.validate()

    def test_perimeter(self):
        """Test perimeter calculation"""
        state = ShapeSpaceState(
            r12=3.0, r23=4.0, r31=5.0, dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0, L=0.0
        )

        assert state.perimeter == 12.0

    def test_area_right_triangle(self):
        """Test area for right triangle (3-4-5)"""
        state = ShapeSpaceState(
            r12=3.0, r23=4.0, r31=5.0, dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0, L=0.0
        )

        # Area of 3-4-5 triangle = 6
        assert np.isclose(state.area, 6.0)

    def test_area_equilateral(self):
        """Test area for equilateral triangle"""
        s = 2.0  # side length
        state = ShapeSpaceState(
            r12=s, r23=s, r31=s, dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0, L=0.0
        )

        # Area = (√3/4) * s²
        expected = np.sqrt(3) / 4 * s**2
        assert np.isclose(state.area, expected)


class TestComplexShapeState:
    """Test ComplexShapeState dataclass"""

    def test_construction(self):
        """Test basic construction"""
        z = 0.5 + 0.5j
        z_dot = 0.1 + 0.1j
        state = ComplexShapeState(z, z_dot, L=1.0)

        assert state.z == z
        assert state.z_dot == z_dot
        assert state.L == 1.0

    def test_validate_positive_orientation(self):
        """Test validation requires Im(z) > 0"""
        # Valid: positive imaginary part
        state_valid = ComplexShapeState(0.5 + 0.5j, 0j, L=0.0)
        assert state_valid.validate()

        # Invalid: negative imaginary part
        state_invalid = ComplexShapeState(0.5 - 0.5j, 0j, L=0.0)
        assert not state_invalid.validate()

    def test_to_distances(self):
        """Test conversion to distances"""
        z = 1.0 + 1.0j  # Specific shape
        state = ComplexShapeState(z, 0j, L=0.0)

        r12, r23, r13 = state.to_distances(scale=2.0)

        # r12 = scale = 2.0
        assert np.isclose(r12, 2.0)

        # r13 = scale * |z| = 2 * √2
        assert np.isclose(r13, 2.0 * np.sqrt(2))

        # r23 = scale * |z - 1| = 2 * 1 = 2
        assert np.isclose(r23, 2.0)


class TestCartesianToShapeDistances:
    """Test Cartesian → Shape Space transformation"""

    def test_equilateral_triangle(self):
        """Test transformation for equilateral triangle"""
        masses = Masses.equal_masses()

        # Equilateral triangle
        R = 1.0
        angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3])
        positions = R * np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Convert to shape space
        shape = cartesian_to_shape_distances(state_cart, masses)

        # All sides should be equal
        side_length = np.sqrt(3) * R
        assert np.isclose(shape.r12, side_length, rtol=0.01)
        assert np.isclose(shape.r23, side_length, rtol=0.01)
        assert np.isclose(shape.r31, side_length, rtol=0.01)

    def test_right_triangle(self):
        """Test transformation for right triangle"""
        masses = Masses.equal_masses()

        # Right triangle: (0,0), (3,0), (0,4)
        positions = np.array([[0, 0, 0], [3, 0, 0], [0, 4, 0]], dtype=float)
        positions -= np.mean(positions, axis=0)  # Center
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)

        shape = cartesian_to_shape_distances(state_cart, masses)

        # Check distances
        distances = sorted([shape.r12, shape.r23, shape.r31])

        # Should be 3, 4, 5 (in some order)
        assert np.isclose(distances[0], 3.0, atol=0.1)
        assert np.isclose(distances[1], 4.0, atol=0.1)
        assert np.isclose(distances[2], 5.0, atol=0.1)

    def test_distance_velocities(self):
        """Test distance velocity calculations"""
        masses = Masses.equal_masses()

        # Bodies moving radially
        positions = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0]], dtype=float)
        # Body 1-2 separating along x-axis
        velocities = np.array([[0.5, 0, 0], [-0.5, 0, 0], [0, 0, 0]], dtype=float)

        state_cart = CartesianState(positions, velocities, dimension=2)

        shape = cartesian_to_shape_distances(state_cart, masses)

        # r12 should be increasing (dr12/dt > 0)
        assert shape.dr12_dt > 0


class TestCartesianToComplexShape:
    """Test Cartesian → Complex shape transformation"""

    def test_transformation_planar_only(self):
        """Test that complex shape requires planar motion"""
        masses = Masses.equal_masses()

        # 3D state should raise error
        state_3d = CartesianState(np.random.randn(3, 3), np.random.randn(3, 3), dimension=3)

        with pytest.raises(ValueError, match="planar"):
            cartesian_to_complex_shape(state_3d, masses)

    def test_equilateral_triangle_complex(self):
        """Test complex shape for equilateral triangle"""
        masses = Masses.equal_masses()

        # Equilateral with body 1 at origin, body 2 on x-axis
        positions = np.array([[0, 0, 0], [1, 0, 0], [0.5, np.sqrt(3) / 2, 0]], dtype=float)
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)

        shape = cartesian_to_complex_shape(state_cart, masses)

        # For equilateral: z = (r3-r1)/(r2-r1) should have specific form
        # z = (0.5 + i√3/2) / 1 = 0.5 + i√3/2
        expected_z = 0.5 + 1j * np.sqrt(3) / 2

        assert np.isclose(shape.z, expected_z, atol=0.01)

    def test_orientation_independence(self):
        """Test that complex shape is rotationally covariant"""
        masses = Masses.equal_masses()

        # Random planar state
        positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
        velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        z1 = cartesian_to_complex_shape(state, masses).z

        # Rotate by angle theta
        theta = np.pi / 4
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        state_rot = CartesianState(state.positions @ R.T, state.velocities @ R.T, dimension=2)

        z2 = cartesian_to_complex_shape(state_rot, masses).z

        # Shape magnitude should be preserved under rotation
        # (angle changes by e^{iθ})
        assert np.isclose(abs(z1), abs(z2), rtol=0.01)


class TestCanonicalOrientation:
    """Test canonical orientation computation"""

    def test_align_axis(self):
        """Test aligning 1-2 axis with x-axis"""
        # Random orientation
        positions = np.array([[1, 1, 0], [-1, 0.5, 0], [0, -1, 0]], dtype=float)
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)

        state_canonical, theta = compute_canonical_orientation(state, method="align_axis")

        # After rotation, r1-r2 should be along x-axis
        r12_vec = state_canonical.positions[0] - state_canonical.positions[1]

        # y-component should be ~0
        assert abs(r12_vec[1]) < 1e-10

        # x-component should be positive (by convention)
        # (or we could have negative, depending on choice)

    def test_roundtrip_orientation(self):
        """Test that rotating back recovers original (up to barycenter)"""
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0  # Planar
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, Masses.equal_masses())

        state_canonical, theta = compute_canonical_orientation(state)

        # Rotate back
        c, s = np.cos(theta), np.sin(theta)
        R_back = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        state_back = CartesianState(
            state_canonical.positions @ R_back.T,
            state_canonical.velocities @ R_back.T,
            dimension=2,
        )

        # Should recover original (up to numerical error)
        np.testing.assert_allclose(state.positions, state_back.positions, atol=1e-10)


class TestOrientedTriangleCoordinates:
    """Test oriented triangle representation"""

    def test_equilateral_angles(self):
        """Test that equilateral triangle has 60° angles"""
        masses = Masses.equal_masses()

        # Equilateral triangle
        R = 1.0
        angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3])
        positions = R * np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        coords = oriented_triangle_coordinates(state, masses)

        alpha, beta, gamma = coords["angles"]

        # All angles should be π/3 = 60°
        expected = np.pi / 3
        assert np.isclose(alpha, expected, atol=0.01)
        assert np.isclose(beta, expected, atol=0.01)
        assert np.isclose(gamma, expected, atol=0.01)

    def test_right_triangle_angles(self):
        """Test right triangle has 90° angle"""
        masses = Masses.equal_masses()

        # Right triangle at origin
        positions = np.array([[1, 0, 0], [0, 0, 0], [0, 1, 0]], dtype=float)
        positions -= np.mean(positions, axis=0)
        velocities = np.zeros((3, 3))

        state = CartesianState(positions, velocities, dimension=2)

        coords = oriented_triangle_coordinates(state, masses)

        angles = sorted(coords["angles"])

        # Should have one 90° angle (π/2)
        assert any(np.isclose(a, np.pi / 2, atol=0.01) for a in angles)

        # Sum should be π
        assert np.isclose(sum(angles), np.pi, atol=0.01)


class TestShapeSpaceReconstruction:
    """Test reconstruction of Cartesian from shape space"""

    def test_distances_to_cartesian_canonical(self):
        """Test reconstruction from distances"""
        masses = Masses.equal_masses()

        # Create shape state
        shape = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=1.0, dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0, L=0.0
        )

        # Reconstruct
        state_cart = shape.to_cartesian(masses)

        # Check that distances match
        r = state_cart.positions
        r12_check = np.linalg.norm(r[0] - r[1])
        r23_check = np.linalg.norm(r[1] - r[2])
        r31_check = np.linalg.norm(r[2] - r[0])

        assert np.isclose(r12_check, shape.r12, atol=0.01)
        assert np.isclose(r23_check, shape.r23, atol=0.01)
        assert np.isclose(r31_check, shape.r31, atol=0.01)

    def test_complex_to_cartesian_canonical(self):
        """Test reconstruction from complex shape"""
        masses = Masses.equal_masses()

        # Equilateral triangle shape
        z = 0.5 + 1j * np.sqrt(3) / 2
        shape = ComplexShapeState(z, 0j, L=0.0)

        # Reconstruct
        state_cart = shape.to_cartesian(masses)

        # Should be approximately equilateral
        r = state_cart.positions
        r12 = np.linalg.norm(r[0] - r[1])
        r23 = np.linalg.norm(r[1] - r[2])
        r31 = np.linalg.norm(r[2] - r[0])

        # All sides should be approximately equal
        assert np.isclose(r12, r23, rtol=0.1)
        assert np.isclose(r23, r31, rtol=0.1)
