"""
Machine Learning module for WP 3.2: Structure-Preserving ML Discovery.

This module implements Hamiltonian Neural Networks (HNNs) for discovering
conserved quantities in the 3-body problem.

Submodules:
-----------
Task 3.2.1: Data Generation
    - parameter_sampling: Parameter space sampling via LHS
    - trajectory_integration: High-precision trajectory integration
    - data_augmentation: Symmetry-based data augmentation
    - dataset_builder: HDF5 dataset assembly
    - dataset_validation: Dataset quality control

Task 3.2.2: HNN Architecture (Available)
    - jax_utils: JAX utility functions
    - hnn_architecture: Hamiltonian Neural Network models
    - hnn_training: Training loops and optimization
    - model_utils: Model utilities

Task 3.2.3: Conservation Training (Available)
    - conservation_hnn: Dual-head HNN with invariant prediction
    - conservation_loss: Physics-informed loss functions
    - symmetry_transforms: Noether regularization via symmetries
    - conservation_training: Two-stage training pipeline

Task 3.2.4: Validation (Available)
    - validation: Conservation verification on trajectories
    - ood_tests: Out-of-distribution generalization testing
    - independence_test: Functional independence analysis
    - wp31_comparison: Comparison with WP 3.1 geometric methods
    - validation_report: Automated comprehensive reporting
"""

# Task 3.2.1: Data Generation (Available)
from .parameter_sampling import (
    ParameterRanges,
    InitialCondition,
    generate_lhs_samples,
    generate_test_samples,
    compute_energy,
    compute_angular_momentum_magnitude
)

from .trajectory_integration import (
    Trajectory,
    IntegrationConfig,
    integrate_s1_bundle_trajectory,
    integrate_batch,
    integrate_batch_parallel
)

from .data_augmentation import (
    augment_via_permutations,
    augment_via_time_reversal,
    augment_via_virial_scaling,
    augment_trajectory
)

from .dataset_builder import (
    TrajectoryDataset,
    build_dataset,
    quick_dataset
)

from .dataset_validation import (
    validate_dataset,
    check_quality_thresholds,
    print_validation_summary,
    generate_validation_plots
)

# Task 3.2.2: HNN Architecture (Available)
from .jax_utils import (
    symplectic_matrix,
    split_state,
    join_state,
    hamiltonian_vector_field,
    poisson_bracket,
    batch_hamiltonian_dynamics,
    batch_poisson_bracket,
    check_symplectic_form
)

from .hnn_architecture import (
    HamiltonianNN,
    SeparableHNN,
    ConstrainedHNN,
    create_hnn_model,
    count_parameters as count_hnn_parameters
)

from .hnn_training import (
    TrainState,
    create_train_state,
    trajectory_loss_fn,
    train_step,
    train_epoch,
    evaluate,
    train_hnn
)

from .model_utils import (
    count_parameters,
    save_checkpoint,
    load_checkpoint,
    integrate_trajectory_learned,
    verify_energy_conservation,
    compare_dynamics,
    benchmark_model,
    visualize_phase_portrait
)

# Task 3.2.3: Conservation Training (Available)
from .conservation_hnn import (
    ConservationHNN,
    MultiInvariantHNN,
    create_conservation_hnn
)

from .conservation_loss import (
    trajectory_loss as conservation_trajectory_loss,
    conservation_loss,
    noether_regularizer,
    involution_loss,
    regularization_loss,
    combined_loss,
    compute_conservation_violation
)

from .symmetry_transforms import (
    time_reversal_transform,
    permutation_transform_s1,
    rotation_transform,
    virial_scaling_transform,
    compose_transforms,
    get_symmetry_transforms_3body,
    test_symmetry_preservation
)

from .conservation_training import (
    ConservationTrainState,
    create_conservation_train_state,
    train_step_stage1,
    train_step_stage2,
    evaluate_conservation,
    train_epoch as conservation_train_epoch,
    two_stage_training
)

# Task 3.2.4: Validation (Available)
from .validation import (
    TrajectoryValidation,
    verify_conservation_single_trajectory,
    verify_conservation_batch,
    compare_with_known_invariant,
    long_term_conservation_test,
    energy_surface_validation,
    phase_space_coverage_validation
)

from .ood_tests import (
    OODTestResult,
    test_parameter_extrapolation,
    test_temporal_extrapolation,
    test_extreme_mass_ratios,
    test_high_eccentricity,
    test_near_collisions,
    compute_ood_degradation,
    ood_test_suite
)

from .independence_test import (
    IndependenceTestResult,
    gradient_rank_test,
    correlation_test,
    involution_test,
    jacobian_determinant_test,
    mutual_information_test,
    test_functional_independence,
    test_liouville_integrability
)

from .wp31_comparison import (
    ComparisonResult,
    compare_invariants,
    detect_functional_relationship,
    compare_with_energy,
    compare_with_angular_momentum,
    cross_method_validation,
    method_comparison_summary
)

from .validation_report import (
    ValidationReport,
    generate_validation_report,
    print_report,
    save_report
)

__all__ = [
    # Parameter sampling
    'ParameterRanges',
    'InitialCondition',
    'generate_lhs_samples',
    'generate_test_samples',
    'compute_energy',
    'compute_angular_momentum_magnitude',

    # Trajectory integration
    'Trajectory',
    'IntegrationConfig',
    'integrate_s1_bundle_trajectory',
    'integrate_batch',
    'integrate_batch_parallel',

    # Data augmentation
    'augment_via_permutations',
    'augment_via_time_reversal',
    'augment_via_virial_scaling',
    'augment_trajectory',

    # Dataset building
    'TrajectoryDataset',
    'build_dataset',
    'quick_dataset',

    # Dataset validation
    'validate_dataset',
    'check_quality_thresholds',
    'print_validation_summary',
    'generate_validation_plots',

    # JAX utils
    'symplectic_matrix',
    'split_state',
    'join_state',
    'hamiltonian_vector_field',
    'poisson_bracket',
    'batch_hamiltonian_dynamics',
    'batch_poisson_bracket',
    'check_symplectic_form',

    # HNN architecture
    'HamiltonianNN',
    'SeparableHNN',
    'ConstrainedHNN',
    'create_hnn_model',
    'count_hnn_parameters',

    # HNN training
    'TrainState',
    'create_train_state',
    'trajectory_loss_fn',
    'train_step',
    'train_epoch',
    'evaluate',
    'train_hnn',

    # Model utilities
    'count_parameters',
    'save_checkpoint',
    'load_checkpoint',
    'integrate_trajectory_learned',
    'verify_energy_conservation',
    'compare_dynamics',
    'benchmark_model',
    'visualize_phase_portrait',

    # Conservation HNN
    'ConservationHNN',
    'MultiInvariantHNN',
    'create_conservation_hnn',

    # Conservation losses
    'conservation_trajectory_loss',
    'conservation_loss',
    'noether_regularizer',
    'involution_loss',
    'regularization_loss',
    'combined_loss',
    'compute_conservation_violation',

    # Symmetry transforms
    'time_reversal_transform',
    'permutation_transform_s1',
    'rotation_transform',
    'virial_scaling_transform',
    'compose_transforms',
    'get_symmetry_transforms_3body',
    'test_symmetry_preservation',

    # Conservation training
    'ConservationTrainState',
    'create_conservation_train_state',
    'train_step_stage1',
    'train_step_stage2',
    'evaluate_conservation',
    'conservation_train_epoch',
    'two_stage_training',

    # Validation
    'TrajectoryValidation',
    'verify_conservation_single_trajectory',
    'verify_conservation_batch',
    'compare_with_known_invariant',
    'long_term_conservation_test',
    'energy_surface_validation',
    'phase_space_coverage_validation',

    # OOD tests
    'OODTestResult',
    'test_parameter_extrapolation',
    'test_temporal_extrapolation',
    'test_extreme_mass_ratios',
    'test_high_eccentricity',
    'test_near_collisions',
    'compute_ood_degradation',
    'ood_test_suite',

    # Independence tests
    'IndependenceTestResult',
    'gradient_rank_test',
    'correlation_test',
    'involution_test',
    'jacobian_determinant_test',
    'mutual_information_test',
    'test_functional_independence',
    'test_liouville_integrability',

    # WP31 comparison
    'ComparisonResult',
    'compare_invariants',
    'detect_functional_relationship',
    'compare_with_energy',
    'compare_with_angular_momentum',
    'cross_method_validation',
    'method_comparison_summary',

    # Validation reporting
    'ValidationReport',
    'generate_validation_report',
    'print_report',
    'save_report',
]

__version__ = '1.0.0'  # Updated for Task 3.2.4 (complete WP 3.2)
__author__ = 'WP 3.2 Implementation'
