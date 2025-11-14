"""
Kustaanheimo-Stiefel (KS) Regularization for the Three-Body Problem.

This module implements the KS spinor transformation, which:
1. Embeds 3D space into 4D spinor space
2. Regularizes collisions (singularities become regular)
3. Reveals hidden symmetries through spinor algebra

Mathematical Framework:
    3D position r ∈ ℝ³ → 4D spinor u ∈ ℝ⁴
    Bilinear relation: r = L(u)·u where L is the Levi-Civita matrix
    Key property: |r|² = |u|⁴, so r = |u|²

For three-body problem:
    Apply pairwise to all three relative vectors (r12, r23, r31)
    Result: 12D spinor space, constrained to effective 9D

Task: WP 2.3 - KS Spinor "Pairwise" Lift
"""

from .levi_civita import (
    levi_civita_matrix,
    levi_civita_map,
    inverse_levi_civita_map,
    validate_bilinear_relation,
)
from .spinor_vector import (
    SpinorVector,
    create_spinor,
    spinor_norm_squared,
)
from .ks_transform import (
    KSState,
    cartesian_to_ks,
    ks_to_cartesian,
    compute_ks_energy,
    validate_ks_roundtrip,
)
from .ks_pairwise import (
    PairwiseSpinorState,
    cartesian_3bp_to_pairwise_ks,
    pairwise_ks_to_cartesian_3bp,
    validate_pairwise_roundtrip,
    compute_constraint_manifold_dimension,
)
from .constrained_dynamics import (
    ConstrainedHamiltonian,
    KSTrajectory,
    integrate_constrained_ks,
    project_onto_constraints,
    verify_collision_regularization,
    compare_with_s1_lift,
)

__all__ = [
    # Levi-Civita operations
    "levi_civita_matrix",
    "levi_civita_map",
    "inverse_levi_civita_map",
    "validate_bilinear_relation",
    # Spinor vectors
    "SpinorVector",
    "create_spinor",
    "spinor_norm_squared",
    # KS transformation
    "KSState",
    "cartesian_to_ks",
    "ks_to_cartesian",
    "compute_ks_energy",
    "validate_ks_roundtrip",
    # Pairwise extension
    "PairwiseSpinorState",
    "cartesian_3bp_to_pairwise_ks",
    "pairwise_ks_to_cartesian_3bp",
    "validate_pairwise_roundtrip",
    "compute_constraint_manifold_dimension",
    # Constrained dynamics
    "ConstrainedHamiltonian",
    "KSTrajectory",
    "integrate_constrained_ks",
    "project_onto_constraints",
    "verify_collision_regularization",
    "compare_with_s1_lift",
]
