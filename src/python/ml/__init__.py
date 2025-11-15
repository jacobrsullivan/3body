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

Task 3.2.2: HNN Architecture (To be implemented)
    - jax_utils: JAX utility functions
    - hnn_architecture: Hamiltonian Neural Network models
    - hnn_training: Training loops and optimization
    - model_utils: Model utilities

Task 3.2.3: Conservation Training (To be implemented)
    - conservation_hnn: Dual-head HNN with invariant prediction
    - conservation_loss: Physics-informed loss functions
    - conservation_training: Two-stage training pipeline

Task 3.2.4: Validation (To be implemented)
    - validation: Conservation verification
    - ood_tests: Out-of-distribution testing
    - independence_test: Functional independence analysis
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
]

__version__ = '0.1.0'
__author__ = 'WP 3.2 Implementation'
