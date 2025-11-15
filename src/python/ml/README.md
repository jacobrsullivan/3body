# Machine Learning Module (WP 3.2)

**Status**: Task 3.2.1 Complete, Tasks 3.2.2-3.2.4 Pending

This module implements structure-preserving machine learning methods for discovering conserved quantities in the 3-body problem using Hamiltonian Neural Networks (HNNs).

## Overview

WP 3.2 uses physics-informed neural networks that respect the symplectic geometry of Hamiltonian systems to learn conserved quantities from trajectory data.

**Key Innovation**: Training a dual-head neural network with conservation constraint {I_φ, H_θ} = 0 (Poisson bracket) to discover novel integrals.

## Implemented: Task 3.2.1 - Data Generation

### Quick Start

```python
from src.python.ml import (
    ParameterRanges, generate_lhs_samples,
    integrate_batch, IntegrationConfig,
    build_dataset, validate_dataset
)

# 1. Generate parameter samples
param_ranges = ParameterRanges(
    mass_ratio=(0.1, 0.5),
    energy=(-2.0, -0.5),
    angular_momentum=(0.5, 3.0)
)

ics = generate_lhs_samples(param_ranges, num_samples=100)

# 2. Integrate trajectories
config = IntegrationConfig(rtol=1e-12, atol=1e-13)
trajectories = integrate_batch(ics, t_span=100.0, config=config)

# 3. Build HDF5 dataset
dataset = build_dataset(
    output_path='data/training_data.h5',
    num_trajectories=1000,
    t_span=100.0,
    use_augmentation=True,
    num_workers=8  # Parallel integration
)

# 4. Validate dataset quality
report = validate_dataset('data/training_data.h5')
```

### Modules

#### `parameter_sampling.py` (~300 lines)
Latin Hypercube Sampling for parameter space exploration.

**Classes**:
- `ParameterRanges`: Parameter space bounds
- `InitialCondition`: 3-body initial state

**Functions**:
- `generate_lhs_samples()`: Generate diverse initial conditions
- `compute_energy()`, `compute_angular_momentum_magnitude()`: Physics utilities

#### `trajectory_integration.py` (~400 lines)
High-precision trajectory integration on lifted manifolds.

**Classes**:
- `Trajectory`: Integrated trajectory with quality metrics
- `IntegrationConfig`: Integration parameters

**Functions**:
- `integrate_s1_bundle_trajectory()`: Integrate on S¹ bundle
- `integrate_batch()`: Batch integration (serial)
- `integrate_batch_parallel()`: Parallel integration (multiprocessing)

**Quality Control**:
- Energy drift < 10⁻¹⁰ required
- Symplectic structure monitoring
- Automatic rejection of poor-quality trajectories

#### `data_augmentation.py` (~250 lines)
Symmetry-based data augmentation.

**Augmentations**:
1. **Permutation** (equal masses): 6× increase
2. **Time reversal**: 2× increase
3. **Virial scaling** (optional): Variable increase

**Function**:
- `augment_trajectory()`: Apply all augmentations

#### `dataset_builder.py` (~350 lines)
HDF5 dataset assembly and storage.

**Class**: `TrajectoryDataset`
- Context manager for HDF5 access
- Chunked storage (1 chunk = 1 trajectory)
- gzip compression (level 4)

**Structure**:
```
dataset.h5
├── metadata/
│   └── [param_ranges, integration_config, ...]
├── train/
│   ├── states (N, T, dim)           # Phase space states
│   ├── derivatives (N, T, dim)       # Time derivatives
│   ├── times (N, T)                  # Time points
│   ├── energies (N,)                 # Initial energies
│   ├── masses (N, 3)                 # Body masses
│   ├── trajectory_ids (N,)           # IDs
│   ├── energy_drifts (N,)            # Quality metrics
│   └── symplectic_errors (N,)
├── validation/  [same structure]
└── test/        [same structure]
```

**Functions**:
- `build_dataset()`: Complete pipeline (sample → integrate → augment → store)
- `quick_dataset()`: Fast test dataset generation

#### `dataset_validation.py` (~200 lines)
Dataset quality control and validation.

**Functions**:
- `validate_dataset()`: Comprehensive validation report
- `check_quality_thresholds()`: Pass/fail quality check
- `print_validation_summary()`: Human-readable report
- `generate_validation_plots()`: Diagnostic plots

**Validation Checks**:
1. Energy conservation statistics
2. Symplectic error distribution
3. Parameter space coverage
4. Data quality (no NaN/Inf)
5. Trajectory diversity

## Usage Examples

### Generate Small Test Dataset

```python
from src.python.ml import quick_dataset

# Generate 10 trajectories, 10 time units each
dataset = quick_dataset(
    output_path='data/test.h5',
    num_trajectories=10,
    t_span=10.0
)
```

### Generate Production Dataset

```python
from src.python.ml import build_dataset, ParameterRanges, IntegrationConfig

# High-quality dataset
param_ranges = ParameterRanges(
    mass_ratio=(0.01, 0.5),
    energy=(-2.0, -0.1),
    angular_momentum=(0.5, 3.0)
)

config = IntegrationConfig(
    rtol=1e-13,
    atol=1e-14,
    t_eval_dt=0.01
)

dataset = build_dataset(
    output_path='data/s1_bundle_train.h5',
    num_trajectories=10000,
    param_ranges=param_ranges,
    integration_config=config,
    t_span=100.0,
    use_augmentation=True,
    num_workers=16  # Use 16 CPU cores
)
```

### Validate Dataset

```python
from src.python.ml import validate_dataset, print_validation_summary

# Validate
report = validate_dataset('data/s1_bundle_train.h5')

# Print summary
print_validation_summary(report)

# Generate plots (requires matplotlib)
from src.python.ml import generate_validation_plots
generate_validation_plots(
    'data/s1_bundle_train.h5',
    output_dir='data/validation_plots'
)
```

### Load Dataset for Training (Task 3.2.2+)

```python
from src.python.ml import TrajectoryDataset

with TrajectoryDataset('data/s1_bundle_train.h5', mode='r') as dataset:
    # Get dataset sizes
    n_train = dataset.get_size('train')
    n_val = dataset.get_size('validation')

    # Load trajectory
    traj_data = dataset.get_trajectory('train', idx=0)
    states = traj_data['states']          # (T, dim)
    derivatives = traj_data['derivatives']  # (T, dim)
    times = traj_data['times']            # (T,)

    # Direct HDF5 access for batching
    train_states = dataset.file['train']['states'][:]  # (N, T, dim)
```

## Pending: Tasks 3.2.2-3.2.4

### Task 3.2.2: HNN Architecture (~1,700 lines)
**Status**: Not implemented
**Dependencies**: JAX, Flax, Optax

Modules to implement:
- `jax_utils.py`: Symplectic operations, Poisson brackets
- `hnn_architecture.py`: Hamiltonian Neural Network models
- `hnn_training.py`: Training loop, optimization
- `model_utils.py`: Checkpointing, integration with learned dynamics

### Task 3.2.3: Conservation Training (~1,750 lines)
**Status**: Not implemented

Modules to implement:
- `conservation_hnn.py`: Dual-head architecture (H_θ and I_φ)
- `conservation_loss.py`: Physics-informed loss L = L_traj + λ₁·L_cons + λ₂·L_Noether
- `symmetry_transforms.py`: Noether regularization
- `conservation_training.py`: Two-stage training pipeline

### Task 3.2.4: Validation (~1,900 lines)
**Status**: Not implemented

Modules to implement:
- `validation.py`: Conservation verification on trajectories
- `ood_tests.py`: Out-of-distribution generalization testing
- `independence_test.py`: Functional independence analysis
- `wp31_comparison.py`: Comparison with WP 3.1 geometric results

## Dependencies

### Current (Task 3.2.1)
- NumPy ≥ 1.24
- SciPy ≥ 1.10
- h5py ≥ 3.10
- tqdm (optional, for progress bars)
- matplotlib (optional, for plots)

### Future (Tasks 3.2.2-3.2.4)
- JAX ≥ 0.4.20 (GPU support recommended)
- Flax ≥ 0.7.5
- Optax ≥ 0.1.7

Install:
```bash
pip install numpy scipy h5py tqdm matplotlib
# For Tasks 3.2.2+:
pip install jax[cuda] flax optax  # With GPU support
```

## Performance

### Data Generation (Task 3.2.1)

**Small dataset** (100 trajectories):
- CPU: 8 cores, RAM: 16 GB
- Time: ~5-10 minutes
- Storage: ~50 MB

**Medium dataset** (10K trajectories):
- CPU: 16 cores, RAM: 32 GB
- Time: ~2-4 hours
- Storage: ~5 GB

**Large dataset** (100K trajectories):
- CPU: 32 cores, RAM: 64 GB
- Time: ~1-2 days
- Storage: ~50 GB

**Recommendations**:
- Use `num_workers=N` for parallel integration (N = number of CPU cores)
- Set `use_augmentation=True` for 10-20× data increase
- Monitor disk space (datasets can be large)

## Testing

Run tests for Task 3.2.1:

```bash
# Test parameter sampling
python src/python/ml/parameter_sampling.py

# Test trajectory integration
python src/python/ml/trajectory_integration.py

# Test data augmentation
python src/python/ml/data_augmentation.py

# Build test dataset
python src/python/ml/dataset_builder.py

# Validate dataset
python src/python/ml/dataset_validation.py data/test_dataset.h5
```

## File Manifest

```
src/python/ml/
├── __init__.py                    (~80 lines)  ✅ Complete
├── README.md                      (this file)   ✅ Complete
├── parameter_sampling.py          (~300 lines)  ✅ Complete
├── trajectory_integration.py      (~400 lines)  ✅ Complete
├── data_augmentation.py           (~250 lines)  ✅ Complete
├── dataset_builder.py             (~350 lines)  ✅ Complete
├── dataset_validation.py          (~200 lines)  ✅ Complete
├── jax_utils.py                   (~150 lines)  ❌ Pending
├── hnn_architecture.py            (~400 lines)  ❌ Pending
├── hnn_training.py                (~350 lines)  ❌ Pending
├── model_utils.py                 (~200 lines)  ❌ Pending
├── conservation_hnn.py            (~400 lines)  ❌ Pending
├── conservation_loss.py           (~450 lines)  ❌ Pending
├── symmetry_transforms.py         (~200 lines)  ❌ Pending
├── conservation_training.py       (~500 lines)  ❌ Pending
├── hyperparameter_tuning.py       (~200 lines)  ❌ Pending
├── validation.py                  (~400 lines)  ❌ Pending
├── ood_tests.py                   (~350 lines)  ❌ Pending
├── independence_test.py           (~400 lines)  ❌ Pending
├── wp31_comparison.py             (~200 lines)  ❌ Pending
└── validation_report.py           (~300 lines)  ❌ Pending

Total: 1,580/7,700 lines implemented (20.5%)
```

## Next Steps

1. **Immediate**: Verify Task 3.2.1 implementation
   - Generate small test dataset
   - Validate quality metrics
   - Test on different parameter ranges

2. **Next**: Implement Task 3.2.2 (HNN Architecture)
   - Install JAX/Flax
   - Implement base HNN
   - Train on toy systems (harmonic oscillator)
   - Train on S¹ bundle data

3. **Then**: Implement Task 3.2.3 (Conservation Training)
   - Extend HNN with invariant head
   - Implement conservation loss
   - Two-stage training

4. **Finally**: Implement Task 3.2.4 (Validation)
   - Conservation verification
   - OOD testing
   - Compare with WP 3.1

**Estimated timeline**: 18-22 days total (4-5 days per task)

## References

See detailed implementation plans in `Project-Design-Docs/WP3/`:
- `Task-3.2.1-Implementation-Plan.md` ✅
- `Task-3.2.2-Implementation-Plan.md` ✅
- `Task-3.2.3-Implementation-Plan.md` ✅
- `Task-3.2.4-Implementation-Plan.md` ✅
- `WP3.2-Implementation-Roadmap.md` ✅

---

**Document Version**: 1.0
**Status**: Task 3.2.1 Complete
**Last Updated**: 2025-11-15
