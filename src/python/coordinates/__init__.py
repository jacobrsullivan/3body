"""
Coordinate systems for the general three-body problem.

This package implements multiple coordinate representations and transformations
for the Newtonian three-body problem, supporting the geometric reduction and
shape space analysis in WP2.

Available coordinate systems:
    - Cartesian: Standard inertial frame (barycentric)
    - Jacobi: Hierarchical mass-weighted coordinates
    - ShapeSpace: Quotient coordinates (gauge-invariant)

Key classes:
    - CoordinateSystem: Abstract base class
    - CartesianState: Cartesian representation
    - JacobiState: Jacobi representation
    - ShapeSpaceState: Shape space representation
    - Masses: Mass parameter container
"""

from .base import CoordinateSystem, Masses, Precision
from .cartesian import CartesianState, enforce_barycenter, ConservationMonitor
from .jacobi import JacobiState, cartesian_to_jacobi, jacobi_to_cartesian
from .shape_space import (
    ShapeSpaceState,
    ComplexShapeState,
    cartesian_to_shape_distances,
    cartesian_to_complex_shape,
)
from .transforms import CoordinateTransform

__all__ = [
    # Base classes
    "CoordinateSystem",
    "Masses",
    "Precision",
    # Cartesian
    "CartesianState",
    "enforce_barycenter",
    "ConservationMonitor",
    # Jacobi
    "JacobiState",
    "cartesian_to_jacobi",
    "jacobi_to_cartesian",
    # Shape Space
    "ShapeSpaceState",
    "ComplexShapeState",
    "cartesian_to_shape_distances",
    "cartesian_to_complex_shape",
    # Transforms
    "CoordinateTransform",
]

__version__ = "1.0.0"
