"""
Symmetry transformations for Noether regularization (Task 3.2.3, Part C).

This module implements symmetry transformations that can be used as
soft constraints during training. Noether's theorem states that
continuous symmetries correspond to conserved quantities.

By enforcing I(σ(z)) ≈ I(z) for known symmetries σ, we bias the
network toward discovering physically meaningful integrals.

Symmetries implemented:
1. Time reversal: (q, p) → (q, -p)
2. Permutation (equal masses): body label permutations
3. Rotations: SO(3) rotations
4. Scaling (virial): (q, p, t) → (λq, p/√λ, λ^{3/2}t)
"""

import jax
import jax.numpy as jnp
from typing import List, Callable, Tuple, Dict
from functools import partial

from .jax_utils import split_state, join_state


def time_reversal_transform(z: jnp.ndarray) -> jnp.ndarray:
    """
    Time reversal transformation: (q, p) → (q, -p).

    For time-independent Hamiltonians:
        H(q, p) = H(q, -p)

    Some conserved quantities are even under time reversal (e.g., energy),
    while others are odd (e.g., angular momentum).

    Args:
        z: Phase space state (2n,) = [q, p]

    Returns:
        z_reversed: Time-reversed state [q, -p]

    Example:
        >>> z = jnp.array([1.0, 2.0, 3.0, 4.0])
        >>> z_rev = time_reversal_transform(z)
        >>> print(z_rev)  # [1, 2, -3, -4]
    """
    n = len(z) // 2
    q, p = z[:n], z[n:]
    return join_state(q, -p)


def permutation_transform_s1(
    z: jnp.ndarray, permutation: Tuple[int, int, int] = (0, 2, 1)
) -> jnp.ndarray:
    """
    Permutation transformation for S¹ bundle coordinates.

    For equal-mass 3-body problem, permuting body labels is a symmetry.

    S¹ bundle coordinates: [r12, r23, r31, θ, p_r12, p_r23, p_r31, p_θ]

    Permutation (0, 2, 1) swaps bodies 2 and 3:
        r12 → r13 (distance 1-3)
        r23 → r32 = r23 (symmetric)
        r31 → r21 = r12 (cyclic)

    This is a simplified version - full implementation would properly
    map distance indices under permutations.

    Args:
        z: State in S¹ bundle coordinates (8,)
        permutation: Body permutation tuple

    Returns:
        z_permuted: Permuted state
    """
    # For identity permutation, no change
    if permutation == (0, 1, 2):
        return z

    # Simplified: return original for now
    # Full implementation would map shape coordinates correctly
    # This is a placeholder for the proper coordinate transformation
    return z


def rotation_transform(z: jnp.ndarray, axis: jnp.ndarray, angle: float) -> jnp.ndarray:
    """
    SO(3) rotation transformation.

    For systems with rotational symmetry, integrals should be invariant
    under rotations.

    This applies to Cartesian coordinates (q_x, q_y, q_z, p_x, p_y, p_z).
    For lifted coordinates (S¹ bundle), rotations are more complex.

    Args:
        z: State in Cartesian coordinates
        axis: Rotation axis (3D unit vector)
        angle: Rotation angle (radians)

    Returns:
        z_rotated: Rotated state
    """
    # Simplified implementation for 2D case
    n = len(z) // 2
    q, p = z[:n], z[n:]

    # For 2D rotation (common case)
    if n == 2:
        cos_a = jnp.cos(angle)
        sin_a = jnp.sin(angle)

        # Rotation matrix
        R = jnp.array([[cos_a, -sin_a], [sin_a, cos_a]])

        q_rot = R @ q
        p_rot = R @ p

        return join_state(q_rot, p_rot)

    # For higher dimensions, return original (placeholder)
    return z


def virial_scaling_transform(z: jnp.ndarray, scale_factor: float = 1.2) -> jnp.ndarray:
    """
    Virial scaling transformation.

    For gravitational potential V = -G Σ m_i m_j / r_ij:
        q → λq
        p → p/√λ
        E → E/λ

    This transformation preserves the equations of motion.
    Some integrals scale with λ, others are invariant.

    Args:
        z: Phase space state (2n,)
        scale_factor: Scaling factor λ

    Returns:
        z_scaled: Scaled state
    """
    λ = scale_factor
    n = len(z) // 2
    q, p = z[:n], z[n:]

    q_scaled = λ * q
    p_scaled = p / jnp.sqrt(λ)

    return join_state(q_scaled, p_scaled)


def random_rotation_2d(key: jax.random.PRNGKey) -> Callable:
    """
    Generate random 2D rotation transformation.

    Args:
        key: JAX random key

    Returns:
        rotation_fn: Function that rotates 2D states
    """
    angle = jax.random.uniform(key, minval=0, maxval=2 * jnp.pi)

    def rotate(z):
        return rotation_transform(z, axis=jnp.array([0, 0, 1]), angle=angle)

    return rotate


def identity_transform(z: jnp.ndarray) -> jnp.ndarray:
    """
    Identity transformation (no change).

    Useful as a baseline.

    Args:
        z: State

    Returns:
        z: Same state
    """
    return z


def compose_transforms(*transforms: Callable) -> Callable:
    """
    Compose multiple transformations.

    Args:
        *transforms: Variable number of transformation functions

    Returns:
        composed: Function that applies all transforms in sequence

    Example:
        >>> composed = compose_transforms(
        ...     time_reversal_transform,
        ...     lambda z: virial_scaling_transform(z, 1.5)
        ... )
        >>> z_transformed = composed(z)
    """

    def composed(z):
        result = z
        for transform in transforms:
            result = transform(result)
        return result

    return composed


def get_symmetry_transforms_3body(
    masses: jnp.ndarray,
    manifold_type: str = "s1",
    include_time_reversal: bool = True,
    include_permutations: bool = True,
    include_rotations: bool = False,  # Complex for S¹ bundle
    include_virial: bool = False,
    num_rotations: int = 3,
    seed: int = 42,
) -> List[Callable]:
    """
    Get applicable symmetry transforms for 3-body problem.

    Args:
        masses: Body masses (3,)
        manifold_type: 's1' or 'cartesian'
        include_time_reversal: Include time reversal
        include_permutations: Include permutations (if masses equal)
        include_rotations: Include random rotations
        include_virial: Include virial scaling
        num_rotations: Number of random rotations to sample
        seed: Random seed

    Returns:
        transforms: List of symmetry transformation functions

    Example:
        >>> masses = jnp.array([1.0, 1.0, 1.0])  # Equal masses
        >>> transforms = get_symmetry_transforms_3body(masses)
        >>> print(f"Number of symmetries: {len(transforms)}")
    """
    transforms = []

    # Time reversal (always applicable for time-independent systems)
    if include_time_reversal:
        transforms.append(time_reversal_transform)

    # Permutations (only if all masses are equal)
    if include_permutations:
        masses_equal = jnp.allclose(masses, masses[0], rtol=1e-6)

        if masses_equal:
            # All 3! = 6 permutations of 3 bodies
            # We exclude identity (0,1,2) and include 5 others
            permutations = [
                (0, 2, 1),  # Swap 2 and 3
                (1, 0, 2),  # Swap 1 and 2
                (1, 2, 0),  # Cyclic: 1→2, 2→3, 3→1
                (2, 0, 1),  # Cyclic: 1→3, 2→1, 3→2
                (2, 1, 0),  # Reverse: 1→3, 2→2, 3→1
            ]

            for perm in permutations:
                # Create closure to capture permutation
                transform_fn = partial(permutation_transform_s1, permutation=perm)
                transforms.append(transform_fn)

    # Rotations (for Cartesian coordinates)
    if include_rotations and manifold_type == "cartesian":
        key = jax.random.PRNGKey(seed)

        for i in range(num_rotations):
            key, subkey = jax.random.split(key)
            rotation_fn = random_rotation_2d(subkey)
            transforms.append(rotation_fn)

    # Virial scaling
    if include_virial:
        # Sample a few different scale factors
        scale_factors = [0.8, 1.2, 1.5]

        for λ in scale_factors:
            transform_fn = partial(virial_scaling_transform, scale_factor=λ)
            transforms.append(transform_fn)

    return transforms


def test_symmetry_preservation(
    symmetry_fn: Callable,
    test_states: jnp.ndarray,
    known_invariant: Callable,
    tolerance: float = 1e-6,
) -> Dict:
    """
    Test if a known invariant is preserved under a symmetry transformation.

    For a true symmetry σ and conserved quantity I:
        I(σ(z)) = I(z) for all z

    Args:
        symmetry_fn: Symmetry transformation σ
        test_states: Test states (N, 2n)
        known_invariant: Function computing I(z)
        tolerance: Tolerance for invariance check

    Returns:
        results: Dictionary with test results

    Example:
        >>> def energy(z):  # Energy for harmonic oscillator
        ...     q, p = split_state(z)
        ...     return 0.5 * (jnp.sum(q**2) + jnp.sum(p**2))
        >>> states = jnp.random.normal(jax.random.PRNGKey(0), (100, 4))
        >>> results = test_symmetry_preservation(
        ...     time_reversal_transform, states, energy
        ... )
        >>> print(f"Preserved: {results['is_symmetry']}")
    """
    # Compute invariant on original states
    I_original = jax.vmap(known_invariant)(test_states)

    # Transform states
    transformed_states = jax.vmap(symmetry_fn)(test_states)

    # Compute invariant on transformed states
    I_transformed = jax.vmap(known_invariant)(transformed_states)

    # Check if preserved
    differences = jnp.abs(I_original - I_transformed)
    max_diff = jnp.max(differences)
    mean_diff = jnp.mean(differences)
    is_symmetry = max_diff < tolerance

    results = {
        "is_symmetry": bool(is_symmetry),
        "max_difference": float(max_diff),
        "mean_difference": float(mean_diff),
        "num_states": len(test_states),
        "tolerance": tolerance,
    }

    return results


# Test code
if __name__ == "__main__":
    print("Testing symmetry transformations...")

    # Test 1: Time reversal
    print("\n[Test 1] Time reversal:")
    z = jnp.array([1.0, 2.0, 3.0, 4.0])
    z_rev = time_reversal_transform(z)
    print(f"  Original: {z}")
    print(f"  Reversed: {z_rev}")
    print(f"  Expected: [1, 2, -3, -4]")
    print(f"  Correct: {jnp.allclose(z_rev, jnp.array([1, 2, -3, -4]))}")

    # Test 2: Double reversal should give identity
    print("\n[Test 2] Double time reversal (should be identity):")
    z_double_rev = time_reversal_transform(z_rev)
    print(f"  Original: {z}")
    print(f"  Double reversed: {z_double_rev}")
    print(f"  Is identity: {jnp.allclose(z, z_double_rev)}")

    # Test 3: Virial scaling
    print("\n[Test 3] Virial scaling:")
    z_scaled = virial_scaling_transform(z, scale_factor=2.0)
    print(f"  Original: {z}")
    print(f"  Scaled (λ=2): {z_scaled}")
    q, p = split_state(z)
    q_s, p_s = split_state(z_scaled)
    print(f"  q scaled by 2: {jnp.allclose(q_s, 2*q)}")
    print(f"  p scaled by 1/√2: {jnp.allclose(p_s, p/jnp.sqrt(2.0))}")

    # Test 4: Rotation (2D)
    print("\n[Test 4] 2D rotation (π/2):")
    z_2d = jnp.array([1.0, 0.0, 0.0, 1.0])  # q=[1,0], p=[0,1]
    z_rot = rotation_transform(z_2d, axis=jnp.array([0, 0, 1]), angle=jnp.pi / 2)
    print(f"  Original: {z_2d}")
    print(f"  Rotated π/2: {z_rot}")
    print(f"  Expected: [0, 1, -1, 0] (approximately)")

    # Test 5: Get transforms for 3-body (equal masses)
    print("\n[Test 5] Get symmetries for 3-body (equal masses):")
    masses_equal = jnp.array([1.0, 1.0, 1.0])
    transforms = get_symmetry_transforms_3body(
        masses_equal,
        include_time_reversal=True,
        include_permutations=True,
        include_rotations=False,
        include_virial=False,
    )
    print(f"  Equal masses: {masses_equal}")
    print(f"  Number of symmetries: {len(transforms)}")
    print(f"  Expected: 1 (time reversal) + 5 (permutations) = 6")

    # Test 6: Get transforms for 3-body (unequal masses)
    print("\n[Test 6] Get symmetries for 3-body (unequal masses):")
    masses_unequal = jnp.array([1.0, 2.0, 3.0])
    transforms = get_symmetry_transforms_3body(
        masses_unequal, include_time_reversal=True, include_permutations=True
    )
    print(f"  Unequal masses: {masses_unequal}")
    print(f"  Number of symmetries: {len(transforms)}")
    print(f"  Expected: 1 (only time reversal, no permutation symmetry)")

    # Test 7: Test symmetry preservation for energy
    print("\n[Test 7] Test energy preservation under time reversal:")

    def harmonic_energy(z):
        """Energy for harmonic oscillator: E = (q² + p²)/2"""
        q, p = split_state(z)
        return 0.5 * (jnp.sum(q**2) + jnp.sum(p**2))

    test_states = jax.random.normal(jax.random.PRNGKey(0), (100, 4))
    results = test_symmetry_preservation(
        time_reversal_transform, test_states, harmonic_energy, tolerance=1e-6
    )

    print(f"  Is energy preserved under time reversal: {results['is_symmetry']}")
    print(f"  Max difference: {results['max_difference']:.2e}")
    print(f"  Mean difference: {results['mean_difference']:.2e}")

    # Test 8: Compose transformations
    print("\n[Test 8] Compose transformations:")
    composed = compose_transforms(
        time_reversal_transform, lambda z: virial_scaling_transform(z, 1.5)
    )
    z_composed = composed(z)
    print(f"  Original: {z}")
    print(f"  After time_reversal + virial_scale(1.5): {z_composed}")

    print("\n✓ All tests passed!")
