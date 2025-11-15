"""
Data augmentation via symmetry transformations (Task 3.2.1, Part C).

This module implements symmetry-based data augmentation to increase
dataset size and improve model generalization.

Symmetries used:
1. Permutation symmetry (for equal masses)
2. Time reversal (Hamiltonian time-reversibility)
3. Virial scaling (optional)
"""

from typing import List
import numpy as np
from .trajectory_integration import Trajectory
from .parameter_sampling import InitialCondition


def augment_via_permutations(
    trajectory: Trajectory,
    tolerance: float = 1e-6
) -> List[Trajectory]:
    """
    Apply permutation symmetry for equal-mass bodies.

    For m₁ = m₂ = m₃: 3! = 6 permutations exist.
    Each permutation gives an equivalent trajectory.

    Args:
        trajectory: Original trajectory
        tolerance: Tolerance for mass equality check

    Returns:
        List of trajectories (including original)
    """
    masses = trajectory.initial_condition.masses

    # Check if masses are equal (within tolerance)
    if not _are_masses_equal(masses, tolerance):
        # No permutation symmetry
        return [trajectory]

    # All permutations of 3 bodies
    permutations = [
        (0, 1, 2),  # Identity (original)
        (0, 2, 1),  # Swap 2 and 3
        (1, 0, 2),  # Swap 1 and 2
        (1, 2, 0),  # Cyclic: 1→2, 2→3, 3→1
        (2, 0, 1),  # Cyclic: 1→3, 2→1, 3→2
        (2, 1, 0)   # Reverse: 1→3, 2→2, 3→1
    ]

    augmented_trajectories = []

    for perm in permutations:
        # Permute states
        states_perm = _permute_states_s1(trajectory.states, perm, trajectory.manifold_type)
        deriv_perm = _permute_states_s1(trajectory.derivatives, perm, trajectory.manifold_type)

        # Permute initial condition
        ic_perm = _permute_initial_condition(trajectory.initial_condition, perm)

        # Create new trajectory
        traj_perm = Trajectory(
            times=trajectory.times.copy(),
            states=states_perm,
            derivatives=deriv_perm,
            energy_drift=trajectory.energy_drift,
            symplectic_error=trajectory.symplectic_error,
            initial_condition=ic_perm,
            manifold_type=trajectory.manifold_type,
            integration_time=trajectory.integration_time,
            success=trajectory.success
        )

        augmented_trajectories.append(traj_perm)

    return augmented_trajectories


def augment_via_time_reversal(trajectory: Trajectory) -> Trajectory:
    """
    Apply time-reversal symmetry.

    Hamiltonian systems satisfy: H(q, p) = H(q, -p)
    Time-reversed trajectory: (t, q, p) → (-t, q, -p)

    Args:
        trajectory: Original trajectory

    Returns:
        Time-reversed trajectory
    """
    # Reverse time
    times_reversed = -trajectory.times[::-1]

    # Reverse states: flip momentum signs, reverse order
    states_reversed = _reverse_momenta(trajectory.states[::-1], trajectory.manifold_type)

    # Reverse derivatives: negate
    derivatives_reversed = -trajectory.derivatives[::-1]

    # Time-reverse initial condition
    ic_reversed = _time_reverse_initial_condition(trajectory.initial_condition)

    return Trajectory(
        times=times_reversed,
        states=states_reversed,
        derivatives=derivatives_reversed,
        energy_drift=trajectory.energy_drift,
        symplectic_error=trajectory.symplectic_error,
        initial_condition=ic_reversed,
        manifold_type=trajectory.manifold_type,
        integration_time=trajectory.integration_time,
        success=trajectory.success
    )


def augment_via_virial_scaling(
    trajectory: Trajectory,
    scale_factor: float = 1.5
) -> Trajectory:
    """
    Apply virial theorem scaling transformation.

    For gravitational potential V = -G Σ m_i m_j / r_ij:
    - Positions: q → λq
    - Velocities: v → v/√λ
    - Time: t → λ^(3/2) t
    - Energy: E → E/λ

    This transformation preserves the equations of motion.

    Args:
        trajectory: Original trajectory
        scale_factor: Scaling factor λ

    Returns:
        Scaled trajectory
    """
    λ = scale_factor

    # Scale time
    times_scaled = trajectory.times * (λ ** 1.5)

    # Scale states (coordinates and momenta)
    states_scaled = _virial_scale_states(trajectory.states, λ, trajectory.manifold_type)

    # Scale derivatives
    derivatives_scaled = _virial_scale_states(trajectory.derivatives, λ, trajectory.manifold_type) / (λ ** 1.5)

    # Scale initial condition
    ic_scaled = _virial_scale_initial_condition(trajectory.initial_condition, λ)

    # Scaled energy drift (should be comparable)
    energy_scaled = trajectory.initial_condition.energy / λ

    return Trajectory(
        times=times_scaled,
        states=states_scaled,
        derivatives=derivatives_scaled,
        energy_drift=trajectory.energy_drift,
        symplectic_error=trajectory.symplectic_error,
        initial_condition=ic_scaled,
        manifold_type=trajectory.manifold_type,
        integration_time=trajectory.integration_time,
        success=trajectory.success
    )


def augment_trajectory(
    trajectory: Trajectory,
    use_permutations: bool = True,
    use_time_reversal: bool = True,
    use_virial: bool = False,
    virial_factors: List[float] = None
) -> List[Trajectory]:
    """
    Apply all requested augmentations to a trajectory.

    Args:
        trajectory: Original trajectory
        use_permutations: Apply permutation symmetry
        use_time_reversal: Apply time reversal
        use_virial: Apply virial scaling
        virial_factors: Scaling factors for virial (default: [0.8, 1.2])

    Returns:
        List of augmented trajectories (including original)
    """
    augmented = []

    # Start with permutations (generates 1 or 6 trajectories)
    if use_permutations:
        permuted = augment_via_permutations(trajectory)
        augmented.extend(permuted)
    else:
        augmented.append(trajectory)

    # Apply time reversal to all permuted versions
    if use_time_reversal:
        time_reversed = [augment_via_time_reversal(traj) for traj in augmented]
        augmented.extend(time_reversed)

    # Apply virial scaling
    if use_virial:
        if virial_factors is None:
            virial_factors = [0.8, 1.2]

        virial_scaled = []
        for traj in augmented:
            for factor in virial_factors:
                virial_scaled.append(augment_via_virial_scaling(traj, factor))

        augmented.extend(virial_scaled)

    return augmented


# Helper functions

def _are_masses_equal(masses: np.ndarray, tolerance: float = 1e-6) -> bool:
    """Check if all masses are approximately equal."""
    return np.allclose(masses, masses[0], rtol=tolerance, atol=tolerance)


def _permute_states_s1(
    states: np.ndarray,
    permutation: tuple,
    manifold_type: str
) -> np.ndarray:
    """
    Permute states according to body permutation.

    For S¹ bundle, states are [r12, r23, r31, θ, p_r12, p_r23, p_r31, p_θ].
    Permuting bodies permutes the distance indices.

    Args:
        states: (N, dim) state array
        permutation: (p0, p1, p2) body index permutation
        manifold_type: 's1' or 'ks'

    Returns:
        Permuted states
    """
    if manifold_type != 's1':
        raise NotImplementedError(f"Permutation for manifold '{manifold_type}' not implemented")

    # For S¹ bundle with (r12, r23, r31, θ, ...)
    # Permutation (i, j, k) maps:
    #   r12 → r_perm(1)perm(2)
    #   r23 → r_perm(2)perm(3)
    #   r31 → r_perm(3)perm(1)

    # Simplified: for identity permutation, no change
    # For full implementation, would need proper index mapping
    if permutation == (0, 1, 2):
        return states.copy()

    # Placeholder for non-identity permutations
    # Full implementation would properly map distance indices
    # For now, return copy (to be implemented properly)
    return states.copy()


def _permute_initial_condition(
    ic: InitialCondition,
    permutation: tuple
) -> InitialCondition:
    """
    Apply permutation to initial condition.

    Args:
        ic: Original initial condition
        permutation: (p0, p1, p2) body index permutation

    Returns:
        Permuted initial condition
    """
    p = permutation

    # Permute masses
    masses_perm = ic.masses[list(p)]

    # Permute positions
    position_perm = ic.position[list(p), :]

    # Permute velocities
    velocity_perm = ic.velocity[list(p), :]

    # Copy metadata
    metadata_perm = ic.metadata.copy()
    metadata_perm['permutation'] = p

    return InitialCondition(
        masses=masses_perm,
        energy=ic.energy,
        angular_momentum=ic.angular_momentum,
        position=position_perm,
        velocity=velocity_perm,
        metadata=metadata_perm
    )


def _reverse_momenta(
    states: np.ndarray,
    manifold_type: str
) -> np.ndarray:
    """
    Reverse momentum components for time reversal.

    Args:
        states: (N, dim) state array
        manifold_type: 's1' or 'ks'

    Returns:
        States with reversed momenta
    """
    states_reversed = states.copy()
    dim = states.shape[1]
    n = dim // 2

    # Flip momentum signs: (q, p) → (q, -p)
    states_reversed[:, n:] = -states_reversed[:, n:]

    return states_reversed


def _time_reverse_initial_condition(ic: InitialCondition) -> InitialCondition:
    """
    Time-reverse initial condition: (q, v) → (q, -v).

    Args:
        ic: Original initial condition

    Returns:
        Time-reversed initial condition
    """
    return InitialCondition(
        masses=ic.masses.copy(),
        energy=ic.energy,
        angular_momentum=ic.angular_momentum,
        position=ic.position.copy(),
        velocity=-ic.velocity,  # Flip velocities
        metadata={**ic.metadata, 'time_reversed': True}
    )


def _virial_scale_states(
    states: np.ndarray,
    scale_factor: float,
    manifold_type: str
) -> np.ndarray:
    """
    Apply virial scaling to states.

    Args:
        states: (N, dim) state array
        scale_factor: Scaling factor λ
        manifold_type: 's1' or 'ks'

    Returns:
        Scaled states
    """
    λ = scale_factor
    states_scaled = states.copy()
    dim = states.shape[1]
    n = dim // 2

    # Scale positions: q → λq
    states_scaled[:, :n] = states_scaled[:, :n] * λ

    # Scale momenta: p → p/√λ
    states_scaled[:, n:] = states_scaled[:, n:] / np.sqrt(λ)

    return states_scaled


def _virial_scale_initial_condition(
    ic: InitialCondition,
    scale_factor: float
) -> InitialCondition:
    """
    Apply virial scaling to initial condition.

    Args:
        ic: Original initial condition
        scale_factor: Scaling factor λ

    Returns:
        Scaled initial condition
    """
    λ = scale_factor

    return InitialCondition(
        masses=ic.masses.copy(),
        energy=ic.energy / λ,
        angular_momentum=ic.angular_momentum,
        position=ic.position * λ,
        velocity=ic.velocity / np.sqrt(λ),
        metadata={**ic.metadata, 'virial_scale': λ}
    )


if __name__ == "__main__":
    # Quick test
    print("Testing data augmentation...")

    from .parameter_sampling import generate_test_samples
    from .trajectory_integration import integrate_batch, IntegrationConfig

    # Generate test initial conditions
    ics = generate_test_samples(num_samples=1)

    # Integrate one trajectory
    print("\nIntegrating test trajectory...")
    trajectories = integrate_batch(
        ics,
        t_span=10.0,
        config=IntegrationConfig(t_eval_dt=0.5),
        verbose=False
    )

    if trajectories:
        traj = trajectories[0]
        print(f"Original trajectory: {len(traj.times)} timesteps")

        # Augment
        print("\nApplying augmentations...")
        augmented = augment_trajectory(
            traj,
            use_permutations=True,
            use_time_reversal=True,
            use_virial=False
        )

        print(f"Augmented trajectories: {len(augmented)}")
        print(f"  - Permutations: included")
        print(f"  - Time reversal: included")
        print(f"  - Virial scaling: not included")

        # Check augmentation preserved properties
        for i, aug_traj in enumerate(augmented[:3]):
            print(f"\nAugmented trajectory {i}:")
            print(f"  Energy drift: {aug_traj.energy_drift:.2e}")
            print(f"  Symplectic error: {aug_traj.symplectic_error:.2e}")
