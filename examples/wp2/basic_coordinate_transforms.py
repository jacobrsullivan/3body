"""
Basic coordinate transformations for WP2.

Demonstrates:
- Cartesian state creation
- Transformation to Jacobi coordinates
- Transformation to shape space
- Round-trip validation
"""

import numpy as np
from src.python.coordinates.cartesian import CartesianState
from src.python.coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian
from src.python.coordinates.shape_space import cartesian_to_shape_distances


def example_lagrange_l4():
    """Create Lagrange L4 equilibrium configuration."""
    # Equal masses in equilateral triangle
    masses = np.array([1.0, 1.0, 1.0])

    # Equilateral triangle configuration (side length = 1.0)
    a = 1.0
    positions = np.array([
        [a/2, 0.0, 0.0],
        [-a/4, a*np.sqrt(3)/4, 0.0],
        [-a/4, -a*np.sqrt(3)/4, 0.0]
    ])

    # Circular motion velocities (for rotating frame)
    omega = 1.0
    velocities = np.array([
        [0.0, omega*a/2, 0.0],
        [-omega*a*np.sqrt(3)/4, -omega*a/4, 0.0],
        [omega*a*np.sqrt(3)/4, -omega*a/4, 0.0]
    ])

    return CartesianState(positions=positions, velocities=velocities, masses=masses)


def main():
    """Run coordinate transformation examples."""
    print("="*60)
    print("WP2 Coordinate Transformation Examples")
    print("="*60)

    # Create Lagrange L4 state
    print("\n1. Creating Lagrange L4 configuration...")
    cartesian_state = example_lagrange_l4()

    print(f"   Masses: {cartesian_state.masses}")
    print(f"   Positions shape: {cartesian_state.positions.shape}")

    # Compute conserved quantities
    energy = cartesian_state.compute_energy()
    ang_mom = cartesian_state.compute_angular_momentum()

    print(f"\n   Energy: {energy:.6f}")
    print(f"   Angular momentum: {ang_mom}")

    # Transform to Jacobi coordinates
    print("\n2. Transform to Jacobi coordinates...")
    jacobi_state = cartesian_to_jacobi(cartesian_state)

    print(f"   Jacobi r1 (relative 1-2): {jacobi_state.r1}")
    print(f"   Jacobi r2 (relative 3-CM12): {jacobi_state.r2}")

    # Round-trip test
    print("\n3. Round-trip: Cartesian → Jacobi → Cartesian...")
    cartesian_back = jacobi_to_cartesian(jacobi_state)

    error_pos = np.linalg.norm(cartesian_back.positions - cartesian_state.positions)
    error_vel = np.linalg.norm(cartesian_back.velocities - cartesian_state.velocities)

    print(f"   Position error: {error_pos:.2e}")
    print(f"   Velocity error: {error_vel:.2e}")

    # Transform to shape space
    print("\n4. Transform to shape space...")
    shape_state = cartesian_to_shape_distances(cartesian_state)

    print(f"   r₁₂ = {shape_state.r12:.6f}")
    print(f"   r₂₃ = {shape_state.r23:.6f}")
    print(f"   r₃₁ = {shape_state.r31:.6f}")
    print(f"   Area (Heron): {shape_state.area:.6f}")

    # Check triangle inequality
    valid = (shape_state.r12 + shape_state.r23 > shape_state.r31 and
             shape_state.r23 + shape_state.r31 > shape_state.r12 and
             shape_state.r31 + shape_state.r12 > shape_state.r23)

    print(f"   Valid triangle: {valid}")

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)


if __name__ == '__main__':
    main()
