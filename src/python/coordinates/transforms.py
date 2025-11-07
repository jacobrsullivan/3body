"""
Coordinate transformation registry and utilities.

Provides a unified interface for transforming between different
coordinate systems.
"""

from typing import Callable, Dict, Tuple, Type
from .base import CoordinateSystem, Masses
from .cartesian import CartesianState
from .jacobi import JacobiState, cartesian_to_jacobi, jacobi_to_cartesian
from .shape_space import (
    ShapeSpaceState,
    ComplexShapeState,
    cartesian_to_shape_distances,
    cartesian_to_complex_shape,
)


class CoordinateTransform:
    """
    Registry for coordinate transformations.

    Manages transformations between different coordinate systems
    using a registry pattern.
    """

    # Registry: (from_type, to_type) -> transform_function
    _transforms: Dict[
        Tuple[Type[CoordinateSystem], Type[CoordinateSystem]],
        Callable[[CoordinateSystem, Masses], CoordinateSystem],
    ] = {}

    @classmethod
    def register(
        cls,
        from_type: Type[CoordinateSystem],
        to_type: Type[CoordinateSystem],
        transform_func: Callable[[CoordinateSystem, Masses], CoordinateSystem],
    ):
        """
        Register a transformation function.

        Args:
            from_type: Source coordinate system type
            to_type: Target coordinate system type
            transform_func: Transformation function
        """
        cls._transforms[(from_type, to_type)] = transform_func

    @classmethod
    def transform(
        cls,
        state: CoordinateSystem,
        to_type: Type[CoordinateSystem],
        masses: Masses,
    ) -> CoordinateSystem:
        """
        Transform state to target coordinate system.

        Args:
            state: Input state
            to_type: Target coordinate system type
            masses: Mass parameters

        Returns:
            Transformed state

        Raises:
            ValueError: If transformation not registered
        """
        from_type = type(state)

        # Direct transformation
        if (from_type, to_type) in cls._transforms:
            return cls._transforms[(from_type, to_type)](state, masses)

        # Identity
        if from_type == to_type:
            return state

        # Try via Cartesian (two-step transformation)
        if from_type != CartesianState and to_type != CartesianState:
            # Convert to Cartesian first
            cart_state = cls.transform(state, CartesianState, masses)
            # Then to target
            return cls.transform(cart_state, to_type, masses)

        raise ValueError(
            f"No transformation registered from {from_type.__name__} to {to_type.__name__}"
        )

    @classmethod
    def roundtrip_error(
        cls,
        state: CoordinateSystem,
        via_type: Type[CoordinateSystem],
        masses: Masses,
    ) -> float:
        """
        Compute round-trip transformation error.

        Transforms: state -> via_type -> original_type

        Args:
            state: Input state
            via_type: Intermediate coordinate system
            masses: Mass parameters

        Returns:
            Maximum error in state components
        """
        from_type = type(state)

        # Transform to intermediate
        state_via = cls.transform(state, via_type, masses)

        # Transform back
        state_back = cls.transform(state_via, from_type, masses)

        # Compute error (state-specific)
        if isinstance(state, CartesianState):
            pos_error = np.max(np.abs(state.positions - state_back.positions))
            vel_error = np.max(np.abs(state.velocities - state_back.velocities))
            return max(pos_error, vel_error)
        elif isinstance(state, JacobiState):
            errors = [
                np.max(np.abs(getattr(state, attr) - getattr(state_back, attr)))
                for attr in ["r1", "r2", "r_cm", "p1", "p2", "p_cm"]
            ]
            return max(errors)
        elif isinstance(state, ShapeSpaceState):
            errors = [
                abs(getattr(state, attr) - getattr(state_back, attr))
                for attr in ["r12", "r23", "r31", "dr12_dt", "dr23_dt", "dr31_dt", "L"]
            ]
            return max(errors)
        else:
            raise NotImplementedError(f"Round-trip error for {type(state)} not implemented")


# Register built-in transformations

# Cartesian <-> Jacobi
CoordinateTransform.register(CartesianState, JacobiState, cartesian_to_jacobi)
CoordinateTransform.register(JacobiState, CartesianState, jacobi_to_cartesian)

# Cartesian -> Shape Space
CoordinateTransform.register(CartesianState, ShapeSpaceState, cartesian_to_shape_distances)
CoordinateTransform.register(CartesianState, ComplexShapeState, cartesian_to_complex_shape)

# Shape Space -> Cartesian (via to_cartesian method)
CoordinateTransform.register(
    ShapeSpaceState,
    CartesianState,
    lambda state, masses: state.to_cartesian(masses),
)
CoordinateTransform.register(
    ComplexShapeState,
    CartesianState,
    lambda state, masses: state.to_cartesian(masses),
)


# Need to import numpy for error computation
import numpy as np
