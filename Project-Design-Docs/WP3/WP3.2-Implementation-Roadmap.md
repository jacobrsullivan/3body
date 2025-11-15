# WP 3.2: ML Discovery - Complete Implementation Roadmap
## Master Plan for Structure-Preserving Machine Learning

**Document Type**: Implementation Roadmap
**Status**: Ready for Execution
**Estimated Duration**: 18-22 days
**Created**: 2025-11-15

---

## Executive Summary

This roadmap provides a complete implementation plan for **WP 3.2: Structure-Preserving Machine Learning Discovery**. The goal is to use Hamiltonian Neural Networks (HNNs) with conservation-constrained training to discover hidden conserved quantities in the 3-body problem.

### Quick Overview

| Aspect | Details |
|--------|---------|
| **Approach** | Hamiltonian Neural Networks with auxiliary invariant head |
| **Key Innovation** | Physics-informed loss enforcing {I, H} = 0 (Poisson bracket) |
| **Total Code** | ~7,400 lines (implementation + tests) |
| **Datasets** | 10-50 GB (10⁵-10⁶ trajectories) |
| **Hardware Required** | GPU (A100/V100), 16+ CPU cores, 64-128 GB RAM |
| **Dependencies** | JAX, Flax, Optax, h5py, WP1 integrators, WP2 lifted dynamics |

### Four Tasks Pipeline

```
Task 3.2.1: Data Generation (4-5 days, ~1,500 lines)
    ↓ High-precision trajectory datasets
Task 3.2.2: HNN Architecture (5-6 days, ~1,700 lines)
    ↓ Structure-preserving neural networks
Task 3.2.3: Conservation Training (6-7 days, ~1,750 lines)
    ↓ Learn invariants via {I, H} = 0 constraint
Task 3.2.4: Validation (3-4 days, ~1,900 lines)
    ✓ Rigorous generalization testing
```

**Expected Outcome**: Discovery of conserved quantity I(q,p) with conservation error < 10⁻⁵, functionally independent of E, L, p_θ.

---

## Table of Contents

1. [Prerequisites and Dependencies](#prerequisites)
2. [Task-by-Task Breakdown](#task-breakdown)
3. [Implementation Schedule](#schedule)
4. [Resource Requirements](#resources)
5. [Integration Points](#integration)
6. [Risk Assessment](#risks)
7. [Success Metrics](#success)
8. [Deliverables Checklist](#deliverables)
9. [Getting Started Guide](#getting-started)

---

## 1. Prerequisites and Dependencies {#prerequisites}

### 1.1 Software Dependencies

#### Python Packages (New)
```bash
# Core ML framework
pip install jax==0.4.20 jaxlib==0.4.20
pip install flax==0.7.5
pip install optax==0.1.7

# Data handling
pip install h5py==3.10.0

# Visualization (optional but recommended)
pip install matplotlib seaborn
pip install tensorboard  # For training monitoring
```

#### Python Packages (Existing - Should Already Be Installed)
- NumPy ≥ 1.24
- SciPy ≥ 1.10
- tqdm (progress bars)

### 1.2 Hardware Requirements

| Component | Minimum | Recommended | Ideal |
|-----------|---------|-------------|-------|
| **GPU** | GTX 1080 Ti (11GB) | RTX 3090 (24GB) | A100 (40GB) |
| **CPU** | 8 cores | 16 cores | 32 cores |
| **RAM** | 32 GB | 64 GB | 128 GB |
| **Storage** | 50 GB | 100 GB | 200 GB (SSD) |

**Note**: Without GPU, training will be ~10-50× slower. CPU-only implementation is possible but not recommended.

### 1.3 Code Dependencies from Other Work Packages

#### From WP1 (High-Precision Integration)
- **Required**: `IAS15` or `DOP853` integrator
- **Location**: Check `src/python/integrators/` (verify existence)
- **Alternative**: Use `scipy.integrate.solve_ivp` with `DOP853` method
- **Status**: ❓ To be verified

#### From WP2 (Lifted Dynamics)
- **Required**:
  - S¹ bundle coordinate transformations: `lift_to_s1_bundle()`
  - S¹ Hamiltonian dynamics: `s1_hamiltonian.dynamics()`
  - KS-Spinor transformations (optional)
- **Location**: `src/python/lifts/`
- **Files**:
  - `s1_bundle.py`
  - `ks_regularization.py`
  - `extended_symplectic.py` (exists, content TBD)
- **Status**: ❓ To be verified

#### From WP 3.1 (Geometric Search)
- **Optional**: Comparison with Killing field integrals
- **Location**: `src/python/analysis/`
- **Status**: ✅ Complete

### 1.4 Pre-Implementation Checklist

Before starting WP 3.2, verify:

- [ ] JAX installation successful: `python -c "import jax; print(jax.devices())"`
- [ ] GPU detected (if available): Should show `gpu:0` in above command
- [ ] WP1 integrators accessible
- [ ] WP2 lifted dynamics available
- [ ] 100+ GB free disk space for datasets
- [ ] Access to compute cluster (if using HPC)

---

## 2. Task-by-Task Breakdown {#task-breakdown}

### Task 3.2.1: High-Precision Data Generation

**Duration**: 4-5 days
**Complexity**: Medium
**Blocking**: Yes (all other tasks depend on this)

#### Detailed Implementation Plan
See: [`Task-3.2.1-Implementation-Plan.md`](./Task-3.2.1-Implementation-Plan.md)

#### Key Milestones
- [ ] **Day 1**: Parameter sampling (LHS)
- [ ] **Day 2-3**: Trajectory integration
- [ ] **Day 4**: Data augmentation & HDF5 assembly
- [ ] **Day 5**: Full dataset generation & validation

#### Code Modules (5 files, ~1,500 lines)
```
src/python/ml/
├── parameter_sampling.py      (~300 lines)
├── trajectory_integration.py  (~400 lines)
├── data_augmentation.py       (~250 lines)
├── dataset_builder.py         (~350 lines)
└── dataset_validation.py      (~200 lines)
```

#### Outputs
- `data/s1_bundle_train.h5` (~20-30 GB)
- `data/ks_spinor_train.h5` (~30-40 GB, optional)
- Validation report with quality metrics

#### Integration Dependencies
- **Requires**: WP1 (integrators), WP2 (lifted dynamics)
- **Provides to**: Task 3.2.2 (training data)

---

### Task 3.2.2: HNN/SympNet Architecture

**Duration**: 5-6 days
**Complexity**: High (requires JAX expertise)
**Blocking**: Partial (Task 3.2.3 depends on this)

#### Detailed Implementation Plan
See: [`Task-3.2.2-Implementation-Plan.md`](./Task-3.2.2-Implementation-Plan.md)

#### Key Milestones
- [ ] **Day 1**: JAX utilities and setup
- [ ] **Day 2-3**: HNN architecture implementation
- [ ] **Day 4**: Training loop and optimization
- [ ] **Day 5**: Full training on S¹ bundle data
- [ ] **Day 6**: Validation and testing

#### Code Modules (5 files, ~1,700 lines)
```
src/python/ml/
├── jax_utils.py              (~150 lines)
├── hnn_architecture.py       (~400 lines)
├── hnn_training.py           (~350 lines)
├── sympnet_architecture.py   (~300 lines, optional)
└── model_utils.py            (~200 lines)

tests/wp3/
└── test_hnn_architecture.py  (~300 lines)
```

#### Outputs
- Trained HNN checkpoint (base model, no invariant head yet)
- Hyperparameters file
- Training curves and validation metrics

#### Integration Dependencies
- **Requires**: Task 3.2.1 (datasets)
- **Provides to**: Task 3.2.3 (base architecture to extend)

---

### Task 3.2.3: Conservation-Constrained Training

**Duration**: 6-7 days
**Complexity**: Very High (core research contribution)
**Blocking**: Partial (Task 3.2.4 depends on this)

#### Detailed Implementation Plan
See: [`Task-3.2.3-Implementation-Plan.md`](./Task-3.2.3-Implementation-Plan.md)

#### Key Milestones
- [ ] **Day 1-2**: Dual-head architecture (H and I heads)
- [ ] **Day 3-4**: Physics-informed loss functions
- [ ] **Day 5-6**: Two-stage training pipeline
- [ ] **Day 7**: Hyperparameter tuning

#### Code Modules (5 files, ~1,750 lines)
```
src/python/ml/
├── conservation_hnn.py         (~400 lines)
├── conservation_loss.py        (~450 lines)
├── symmetry_transforms.py      (~200 lines)
├── conservation_training.py    (~500 lines)
└── hyperparameter_tuning.py    (~200 lines)
```

#### Outputs
- Trained ConservationHNN with learned invariant I_φ
- Training history: L_trajectory, L_conservation, L_Noether
- Best hyperparameters (λ₁, λ₂, λ₃)

#### Integration Dependencies
- **Requires**: Task 3.2.2 (HNN architecture)
- **Provides to**: Task 3.2.4 (trained model for validation)

---

### Task 3.2.4: Validation and Generalization

**Duration**: 3-4 days
**Complexity**: Medium
**Blocking**: No (final task)

#### Detailed Implementation Plan
See: [`Task-3.2.4-Implementation-Plan.md`](./Task-3.2.4-Implementation-Plan.md)

#### Key Milestones
- [ ] **Day 1**: Conservation verification on trajectories
- [ ] **Day 2**: Out-of-distribution testing
- [ ] **Day 3**: Functional independence testing
- [ ] **Day 4**: Report generation and acceptance tests

#### Code Modules (5 files + tests, ~1,900 lines)
```
src/python/ml/
├── validation.py               (~400 lines)
├── ood_tests.py                (~350 lines)
├── independence_test.py        (~400 lines)
├── wp31_comparison.py          (~200 lines)
└── validation_report.py        (~300 lines)

tests/wp3/
└── test_ml_validation.py       (~250 lines)
```

#### Outputs
- Validation report (PDF, 20-30 pages)
- Conservation plots, OOD performance figures
- Acceptance test results: PASS/FAIL
- Comparison with WP 3.1 geometric results

#### Integration Dependencies
- **Requires**: Task 3.2.3 (trained model)
- **Requires**: WP 3.1 (geometric integrals for comparison)
- **Provides to**: WP 3.3 (validated numerical function for symbolic regression)

---

## 3. Implementation Schedule {#schedule}

### 3.1 Gantt Chart

```
Week 1          Week 2          Week 3          Week 4
│───────────────│───────────────│───────────────│───────
│ T3.2.1        │               │               │
│ Data Gen      │               │               │
│───────┐       │               │               │
        │       │               │               │
        └───────│ T3.2.2        │               │
                │ HNN Arch      │               │
                │───────┐       │               │
                        │       │               │
                        └───────│ T3.2.3        │
                                │ Conservation  │
                                │───────┐       │
                                        │       │
                                        └───────│ T3.2.4
                                                │ Validation
                                                │───────┐
```

### 3.2 Critical Path

The critical path (longest dependent chain) is:
```
T3.2.1 (5 days) → T3.2.2 (6 days) → T3.2.3 (7 days) → T3.2.4 (4 days)
= 22 days total
```

### 3.3 Parallel Opportunities

Some tasks can be partially parallelized:
- **T3.2.1 + T3.2.2 setup**: While data is generating (Day 4-5 of T3.2.1), begin JAX setup and toy model testing for T3.2.2
- **Documentation**: Write documentation concurrently with implementation
- **Testing**: Write unit tests while implementing each module

With parallelization: **18-20 days realistic timeline**

### 3.4 Day-by-Day Schedule (Optimized)

| Day | Primary Task | Secondary Tasks |
|-----|--------------|-----------------|
| 1 | T3.2.1: Parameter sampling | Setup JAX environment |
| 2 | T3.2.1: Trajectory integration Part I | - |
| 3 | T3.2.1: Trajectory integration Part II | Start T3.2.2: JAX utils |
| 4 | T3.2.1: Data augmentation | T3.2.2: HNN architecture sketch |
| 5 | T3.2.1: Dataset assembly (automated) | T3.2.2: HNN architecture |
| 6 | T3.2.2: HNN architecture | T3.2.1: Dataset validation |
| 7 | T3.2.2: Training loop | - |
| 8 | T3.2.2: Full HNN training | - |
| 9 | T3.2.2: Validation & testing | Start T3.2.3: Dual-head design |
| 10 | T3.2.3: ConservationHNN arch | - |
| 11 | T3.2.3: Loss functions | - |
| 12 | T3.2.3: Loss functions | - |
| 13 | T3.2.3: Training pipeline | - |
| 14 | T3.2.3: Two-stage training | - |
| 15 | T3.2.3: Hyperparameter tuning | - |
| 16 | T3.2.3: Full training run | Start T3.2.4: Validation setup |
| 17 | T3.2.4: Conservation verification | - |
| 18 | T3.2.4: OOD testing | - |
| 19 | T3.2.4: Independence testing | - |
| 20 | T3.2.4: Report generation | - |

**Total: 20 days** (with efficient parallelization)

---

## 4. Resource Requirements {#resources}

### 4.1 Computational Resources

#### Data Generation (Task 3.2.1)
- **Time**: 5-10 hours (100K trajectories on 16 cores)
- **Storage**: 30-50 GB
- **Memory**: 32 GB RAM
- **GPU**: Not required

#### HNN Training (Task 3.2.2)
- **Time**: 2-4 days continuous GPU training
- **GPU Memory**: 16-24 GB VRAM
- **Checkpointing**: Every 10 epochs (~1 GB per checkpoint)
- **Total storage**: 20 GB (checkpoints + logs)

#### Conservation Training (Task 3.2.3)
- **Time**: 3-5 days continuous GPU training
- **GPU Memory**: 24-32 GB VRAM (dual-head model)
- **Hyperparameter search**: 5-10× training time (if grid search)
- **Storage**: 30 GB

#### Validation (Task 3.2.4)
- **Time**: 1 day (trajectory integration for validation)
- **GPU**: Optional (faster inference)
- **Storage**: 10 GB (validation plots, reports)

#### Total Resources
- **Compute time**: ~10 GPU-days
- **Storage**: ~100 GB
- **Cost estimate** (cloud):
  - AWS p3.2xlarge (V100): ~$3/hr × 240 hrs = **~$720**
  - GCP a2-highgpu-1g (A100): ~$4/hr × 240 hrs = **~$960**

### 4.2 Personnel Requirements

**Recommended team composition**:
- 1 ML Engineer (JAX/Flax expertise) - 80% time, 20 days
- 1 Physicist (celestial mechanics) - 20% time, consultation
- 1 Research Engineer (data pipelines) - 40% time, 10 days

**Solo implementation**: Feasible but challenging. Expect 25-30 days.

### 4.3 External Dependencies

| Dependency | Source | Status | Contingency |
|------------|--------|--------|-------------|
| JAX/Flax | Google | ✅ Stable | PyTorch alternative exists |
| WP1 Integrators | Internal | ❓ TBD | Use scipy.integrate |
| WP2 Lifted Dynamics | Internal | ❓ TBD | Implement minimal version |
| GPU Access | Local/Cloud | ❓ TBD | CPU fallback (slow) |

---

## 5. Integration Points {#integration}

### 5.1 With Other Work Packages

#### WP1: High-Precision Integration
- **From WP1**: IAS15 integrator or equivalent
- **Interface**: `solve_ivp` compatible function
- **Fallback**: Use `scipy.integrate.solve_ivp(..., method='DOP853')`

#### WP2: Lifted Dynamics
- **From WP2**:
  - `lift_to_s1_bundle(q, v, masses) -> z_s1`
  - `s1_hamiltonian.dynamics(z, masses, E) -> dz/dt`
  - `ks_regularization.lift_to_ks(q, v, masses) -> z_ks` (optional)
- **Interface**: Callable functions returning NumPy/JAX arrays
- **Fallback**: Implement minimal S¹ bundle lift (1-2 days work)

#### WP 3.1: Geometric Search
- **From WP 3.1**: List of `ConservedIntegral` objects discovered via Killing PDEs
- **Interface**: `ConservedIntegral.expression(state) -> float`
- **Use**: Comparison and cross-validation (Task 3.2.4)
- **Status**: ✅ Available

#### WP 3.3: Symbolic Regression (Future)
- **To WP 3.3**: Validated numerical function I_φ(q,p)
- **Format**: Evaluation grid + metadata
- **Use**: Fit symbolic expression to numerical invariant

### 5.2 Data Flow Diagram

```
WP1: Integrators ──┐
                   ├──> T3.2.1: Data Gen ──> HDF5 Datasets
WP2: Lifts ────────┘                              │
                                                  ↓
                                        T3.2.2: HNN Training
                                                  │
                                                  ↓
                                        T3.2.3: Conservation
                                                  │
                       WP3.1: Geometric ──┐       ↓
                                          ├──> T3.2.4: Validation
                       Known Integrals ───┘       │
                                                  ↓
                                            Validated I_φ
                                                  │
                                                  ↓
                                        WP3.3: Symbolic Regression
```

---

## 6. Risk Assessment {#risks}

### 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **WP2 dependencies missing** | Medium | High | Implement minimal S¹ bundle lift (~2 days) |
| **GPU unavailable** | Low | High | Use cloud GPU (AWS/GCP) or CPU fallback |
| **No novel integral exists** | Medium | Medium | Document negative result (still valuable) |
| **Training doesn't converge** | Low | High | Extensive hyperparameter tuning, curriculum learning |
| **Overfitting/spurious results** | Medium | High | Rigorous validation (Task 3.2.4), OOD testing |
| **Data generation too slow** | Low | Medium | Use more CPU cores, optimize integration |
| **Memory issues (large datasets)** | Low | Medium | Use chunked HDF5 reading, reduce batch size |

### 6.2 Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Underestimated complexity** | +5-10 days | Build in 20% time buffer |
| **Debugging JAX/GPU issues** | +2-5 days | Start with simple test cases, verify JAX install early |
| **Hyperparameter search takes longer** | +3-7 days | Use Bayesian optimization instead of grid search |
| **Validation reveals issues** | +5 days | Iterate on training, may need to retrain |

### 6.3 Contingency Plans

**If GPU unavailable**:
- Reduce dataset size: 10K trajectories instead of 100K
- Simplify architecture: Smaller hidden layers
- Use CPU with reduced batch size (expect 10× slower training)

**If WP2 dependencies missing**:
- Implement minimal S¹ bundle lift from first principles (~2 days)
- Focus on S¹ bundle only (skip KS-Spinor)
- Use energy-surface coordinates as alternative

**If no novel integral discovered**:
- Verify known integrals are learned (validates method)
- Try different parameter regimes
- Document negative result for publication
- Focus on WP 3.1 geometric results instead

---

## 7. Success Metrics {#success}

### 7.1 Quantitative Metrics

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| **Conservation Rate (Validation)** | 70% | 90% | 95% |
| **Conservation Drift** | < 10⁻⁴ | < 10⁻⁵ | < 10⁻⁶ |
| **OOD Conservation Rate** | 50% | 80% | 90% |
| **Functional Independence** | - | Yes | Yes + Involution |
| **Training Time** | < 7 days | < 5 days | < 3 days |
| **Dataset Size** | 10K traj | 100K traj | 1M traj |

### 7.2 Qualitative Metrics

**Minimum Success** (Publishable Negative Result):
- [ ] HNN learns lifted Hamiltonian accurately (trajectory error < 5%)
- [ ] Training pipeline functional and documented
- [ ] Validation framework in place
- [ ] Comparison with WP 3.1 completed

**Target Success** (Strong Positive Result):
- [ ] Novel conserved quantity discovered
- [ ] Conservation verified: drift < 10⁻⁵
- [ ] Functionally independent of E, L, p_θ
- [ ] Generalizes to OOD regimes (80%+ conservation)
- [ ] Matches or extends WP 3.1 geometric results

**Stretch Success** (Exceptional Result):
- [ ] Multiple independent integrals discovered
- [ ] Perfect conservation: drift < 10⁻⁶
- [ ] Universal across all parameter space
- [ ] Symbolic form extractable (feeds into WP 3.3)
- [ ] Novel integral not accessible via WP 3.1 geometric methods

---

## 8. Deliverables Checklist {#deliverables}

### 8.1 Code Deliverables

#### Core Implementation (~6,850 lines)
- [ ] `src/python/ml/parameter_sampling.py` (300)
- [ ] `src/python/ml/trajectory_integration.py` (400)
- [ ] `src/python/ml/data_augmentation.py` (250)
- [ ] `src/python/ml/dataset_builder.py` (350)
- [ ] `src/python/ml/dataset_validation.py` (200)
- [ ] `src/python/ml/jax_utils.py` (150)
- [ ] `src/python/ml/hnn_architecture.py` (400)
- [ ] `src/python/ml/hnn_training.py` (350)
- [ ] `src/python/ml/sympnet_architecture.py` (300, optional)
- [ ] `src/python/ml/model_utils.py` (200)
- [ ] `src/python/ml/conservation_hnn.py` (400)
- [ ] `src/python/ml/conservation_loss.py` (450)
- [ ] `src/python/ml/symmetry_transforms.py` (200)
- [ ] `src/python/ml/conservation_training.py` (500)
- [ ] `src/python/ml/hyperparameter_tuning.py` (200)
- [ ] `src/python/ml/validation.py` (400)
- [ ] `src/python/ml/ood_tests.py` (350)
- [ ] `src/python/ml/independence_test.py` (400)
- [ ] `src/python/ml/wp31_comparison.py` (200)
- [ ] `src/python/ml/validation_report.py` (300)

#### Tests (~850 lines)
- [ ] `tests/wp3/test_data_generation.py` (300)
- [ ] `tests/wp3/test_hnn_architecture.py` (300)
- [ ] `tests/wp3/test_ml_validation.py` (250)

#### Module Exports
- [ ] `src/python/ml/__init__.py` (comprehensive exports)

**Total Code**: ~7,700 lines

### 8.2 Data Deliverables

- [ ] `data/s1_bundle_train.h5` (20-30 GB)
- [ ] `data/s1_bundle_val.h5` (3-5 GB)
- [ ] `data/s1_bundle_test.h5` (3-5 GB)
- [ ] `data/ks_spinor_train.h5` (30-40 GB, optional)
- [ ] Dataset validation report (plots, statistics)

### 8.3 Model Deliverables

- [ ] Trained HNN checkpoint (base model)
- [ ] Trained ConservationHNN checkpoint (with invariant head)
- [ ] Hyperparameters JSON files
- [ ] Training history logs (TensorBoard)

### 8.4 Documentation Deliverables

- [ ] `Task-3.2.1-Implementation-Plan.md` ✅
- [ ] `Task-3.2.2-Implementation-Plan.md` ✅
- [ ] `Task-3.2.3-Implementation-Plan.md` ✅
- [ ] `Task-3.2.4-Implementation-Plan.md` ✅
- [ ] `WP3.2-Implementation-Roadmap.md` ✅ (this document)
- [ ] Validation report (PDF, 20-30 pages)
- [ ] API documentation (docstrings + Sphinx/MkDocs)
- [ ] User guide: "How to train HNN on 3-body data"

### 8.5 Results Deliverables

- [ ] Learned invariant I_φ (numerical function + metadata)
- [ ] Conservation plots: I(t) vs t
- [ ] OOD generalization analysis
- [ ] Comparison with WP 3.1 geometric results
- [ ] Acceptance test results: PASS/FAIL

---

## 9. Getting Started Guide {#getting-started}

### 9.1 Environment Setup (Day 0)

```bash
# 1. Create virtual environment
conda create -n wp32 python=3.10
conda activate wp32

# 2. Install JAX (CPU-only for testing)
pip install jax[cpu]==0.4.20

# 3. Install JAX with GPU support (if available)
# CUDA 11:
pip install jax[cuda11_pip]==0.4.20 -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
# CUDA 12:
pip install jax[cuda12_pip]==0.4.20 -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html

# 4. Install other dependencies
pip install flax==0.7.5 optax==0.1.7
pip install h5py matplotlib tqdm
pip install numpy scipy

# 5. Verify JAX installation
python -c "import jax; print(jax.devices())"
# Should show [cuda(id=0)] if GPU available

# 6. Verify project structure
cd /home/user/3body
ls src/python/ml  # Should see (will be empty initially)
```

### 9.2 First Steps (Day 1)

**Before implementing, verify dependencies**:

```bash
# Check if WP1 integrators exist
python -c "from src.python.integrators import ias15" || echo "WP1 NOT AVAILABLE"

# Check if WP2 lifts exist
python -c "from src.python.lifts.s1_bundle import lift_to_s1_bundle" || echo "WP2 NOT AVAILABLE"

# Check if WP3.1 results exist
python -c "from src.python.analysis.integral_from_killing import ConservedIntegral" && echo "WP3.1 AVAILABLE"
```

**If dependencies missing**, see contingency plans in [Section 6.3](#risks).

### 9.3 Recommended Implementation Order

**Week 1**: Foundation
1. Start with Task 3.2.1, Part A (parameter sampling)
2. Verify WP2 integration (lift to S¹ bundle)
3. Implement trajectory integration (small test: 100 trajectories)
4. Generate validation dataset (1,000 trajectories)

**Week 2**: Neural Architecture
1. Implement JAX utilities (symplectic matrix, Poisson bracket)
2. Build base HNN on toy system (harmonic oscillator)
3. Train HNN on small 3-body dataset
4. Verify energy conservation with learned Hamiltonian

**Week 3**: Conservation Learning
1. Extend HNN with invariant head
2. Implement conservation loss
3. Two-stage training on full dataset
4. Monitor {I, H} Poisson bracket during training

**Week 4**: Validation
1. Verify conservation on validation trajectories
2. OOD testing
3. Compare with WP 3.1 results
4. Generate final report

### 9.4 Quick Start: Minimal Working Example

Before full implementation, validate the approach with a minimal example:

```python
# minimal_hnn_test.py - Day 1 sanity check

import jax
import jax.numpy as jnp
from flax import linen as nn

# Simplest HNN: 1D harmonic oscillator
class SimpleHNN(nn.Module):
    @nn.compact
    def __call__(self, z):
        # z = [q, p]
        x = nn.Dense(32)(z)
        x = nn.tanh(x)
        x = nn.Dense(32)(x)
        x = nn.tanh(x)
        H = nn.Dense(1)(x)
        return jnp.squeeze(H)

# Test forward pass
model = SimpleHNN()
params = model.init(jax.random.PRNGKey(0), jnp.ones(2))
z_test = jnp.array([1.0, 0.0])
H_value = model.apply(params, z_test)
print(f"Hamiltonian value: {H_value}")

# Test gradient (for dynamics)
grad_H = jax.grad(lambda z: model.apply(params, z))(z_test)
print(f"Gradient: {grad_H}")

print("✅ JAX/Flax working correctly!")
```

Run this test on Day 1 to ensure environment is set up correctly.

---

## 10. Summary and Next Actions

### 10.1 Critical Path to Success

1. ✅ **Detailed implementation plans created** (Tasks 3.2.1-3.2.4)
2. **Verify dependencies** (WP1, WP2) - DO THIS FIRST
3. **Set up environment** (JAX, GPU, disk space)
4. **Start with Task 3.2.1** (data generation)
5. **Iterate rapidly** on small datasets before scaling up
6. **Validate continuously** (don't wait until Task 3.2.4)

### 10.2 Key Success Factors

- **Start simple**: Toy systems first, then 3-body
- **Test frequently**: Unit tests for every module
- **Visualize everything**: Plots are debugging tools
- **Monitor training**: TensorBoard, conservation metrics
- **Expect iteration**: First training run likely won't work perfectly

### 10.3 Decision Points

**After Task 3.2.1** (Day 5):
- ✅ If dataset quality good: proceed to T3.2.2
- ❌ If energy drift > 10⁻⁸: improve integrator tolerances

**After Task 3.2.2** (Day 11):
- ✅ If HNN learns dynamics (< 1% error): proceed to T3.2.3
- ❌ If poor performance: debug architecture, increase training time

**After Task 3.2.3** (Day 18):
- ✅ If {I, H} < 10⁻⁴: proceed to T3.2.4
- ⚠️ If {I, H} > 10⁻³: tune hyperparameters, may need re-training

**After Task 3.2.4** (Day 22):
- ✅ **If validation PASS**: Celebrate! Write paper.
- ⚠️ **If validation PARTIAL**: Document findings, iterate if time permits
- ❌ **If validation FAIL**: Document negative result (still valuable)

### 10.4 Immediate Next Steps

**Right now**:
1. Review this roadmap with team
2. Verify hardware/software prerequisites
3. Check WP1/WP2 dependency status
4. Allocate resources (compute, personnel)

**Day 1**:
1. Set up environment (JAX, Flax, GPU)
2. Run minimal working example
3. Begin Task 3.2.1: Parameter sampling

**First week goal**:
- Complete Task 3.2.1 (data generation)
- Have 1,000-10,000 validated trajectories
- Begin Task 3.2.2 (HNN architecture)

---

## Document Control

**Version**: 1.0
**Created**: 2025-11-15
**Author**: WP 3.2 Implementation Planning
**Status**: ✅ Ready for Execution

**Change Log**:
- 2025-11-15: Initial roadmap created

**Related Documents**:
- `WP3.2-ML-Discovery-Summary.md` - High-level overview
- `Task-3.2.1-Implementation-Plan.md` - Data generation details
- `Task-3.2.2-Implementation-Plan.md` - HNN architecture details
- `Task-3.2.3-Implementation-Plan.md` - Conservation training details
- `Task-3.2.4-Implementation-Plan.md` - Validation details

**Questions or Issues**: Review task-specific implementation plans or consult with research team.

---

**End of Roadmap**

Ready to proceed with implementation. Good luck! 🚀
