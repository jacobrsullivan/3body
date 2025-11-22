"""
Kustaanheimo-Stiefel (KS) Regularization for the Three-Body Problem.

This module implements the KS spinor transformation with time regularization:
1. Spatial Lift: Embeds 3D space into 4D spinor space
2. Temporal Lift: Sundman time transformation (dt/ds = r)
3. Combined: (4+1)-dimensional regularization eliminating singularities

Mathematical Framework:
    Spatial: 3D position r ∈ ℝ³ → 4D spinor u ∈ ℝ⁴
    Bilinear relation: r = L(u)·u where L is the Levi-Civita matrix
    Key property: |r|² = |u|⁴, so r = |u|²

    Temporal: dt/ds = Ω(u) = |u|² (time reparametrization)
    Extended phase space: (u, p_u, s, K, t, E) ∈ R^10

For three-body problem:
    Apply pairwise to all three relative vectors (r12, r23, r31)
    Result: 12D spatial + 2D temporal = 14D extended space

Task: WP 2.3 - KS Spinor "Pairwise" Lift with Time Regularization
References: AMENDED_WP2.3-KS-Spinor-Lift-Implementation-Plan.md
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
# Time regularization (NEW - AMENDED documents)
from .extended_phase_space import (
    ExtendedKSState,
    create_extended_ks_state,
    compute_time_dilation_history,
    compute_energy_drift,
    validate_extended_trajectory,
)
from .sundman import (
    TimeTransformationStrategy,
    TimeDilationResult,
    SundmanTransformation,
    compute_time_dilation_single,
    compute_time_dilation_threebody,
    compute_time_dilation_from_spinors,
    integrate_physical_time,
    compute_effective_timestep,
)
from .time_synchronizer import (
    DualTimeTrajectory,
    TimeSynchronizer,
    validate_time_consistency,
    resample_to_physical_time,
    compute_time_dilation_profile,
)
from .time_regularized_dynamics import (
    TimeRegularizedHamiltonian,
    TimeRegularizedTrajectory,
    integrate_time_regularized_ks,
    validate_kepler_orbit,
    create_kepler_initial_state,
)
from .threebody_time_regularized import (
    PairwiseSpinorStateWithTime,
    ThreeBodyTimeRegularizedHamiltonian,
    ThreeBodyTrajectory,
    integrate_threebody_time_regularized,
)
from .integrability_analysis import (
    ConservationAnalysis,
    analyze_energy_conservation,
    analyze_temporal_structure,
    verify_symplectic_structure,
    comprehensive_integrability_analysis,
    generate_integrability_report,
)
from .validation_studies import (
    ValidationResult,
    validate_collision_passage,
    validate_energy_conservation_long_term,
    validate_time_transformation_accuracy,
    validate_k_e_omega_relation,
    run_comprehensive_validation_suite,
    generate_validation_report,
)
from .comparative_analysis import (
    PerformanceBenchmark,
    benchmark_time_regularized_integration,
    compare_regularization_approaches,
    analyze_accuracy_vs_efficiency,
    run_comprehensive_benchmarks,
    generate_comparative_report,
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
    # Extended phase space with time (NEW)
    "ExtendedKSState",
    "create_extended_ks_state",
    "compute_time_dilation_history",
    "compute_energy_drift",
    "validate_extended_trajectory",
    # Sundman time transformations (NEW)
    "TimeTransformationStrategy",
    "TimeDilationResult",
    "SundmanTransformation",
    "compute_time_dilation_single",
    "compute_time_dilation_threebody",
    "compute_time_dilation_from_spinors",
    "integrate_physical_time",
    "compute_effective_timestep",
    # Time synchronization (NEW)
    "DualTimeTrajectory",
    "TimeSynchronizer",
    "validate_time_consistency",
    "resample_to_physical_time",
    "compute_time_dilation_profile",
    # Time-regularized dynamics (NEW - Phase 2)
    "TimeRegularizedHamiltonian",
    "TimeRegularizedTrajectory",
    "integrate_time_regularized_ks",
    "validate_kepler_orbit",
    "create_kepler_initial_state",
    # Three-body time-regularized dynamics (NEW - Phase 3)
    "PairwiseSpinorStateWithTime",
    "ThreeBodyTimeRegularizedHamiltonian",
    "ThreeBodyTrajectory",
    "integrate_threebody_time_regularized",
    # Integrability analysis (NEW - Phase 4)
    "ConservationAnalysis",
    "analyze_energy_conservation",
    "analyze_temporal_structure",
    "verify_symplectic_structure",
    "comprehensive_integrability_analysis",
    "generate_integrability_report",
    # Validation studies (NEW - Phase 5)
    "ValidationResult",
    "validate_collision_passage",
    "validate_energy_conservation_long_term",
    "validate_time_transformation_accuracy",
    "validate_k_e_omega_relation",
    "run_comprehensive_validation_suite",
    "generate_validation_report",
    # Comparative analysis (NEW - Phase 6)
    "PerformanceBenchmark",
    "benchmark_time_regularized_integration",
    "compare_regularization_approaches",
    "analyze_accuracy_vs_efficiency",
    "run_comprehensive_benchmarks",
    "generate_comparative_report",
]
