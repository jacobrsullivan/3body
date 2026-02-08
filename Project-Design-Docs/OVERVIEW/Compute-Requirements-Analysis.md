# Compute Requirements Analysis
## Three-Body Problem Lift-Integrability Investigation (WP1-WP4)

**Document Version**: 1.0
**Date**: 2025-11-23
**Status**: Complete Analysis
**Purpose**: Comprehensive analysis of computational resources required for Work Packages 1-4

---

## Executive Summary

This document provides a detailed analysis of computational requirements for the three-body problem lift-integrability investigation across Work Packages 1-4. The project requires **significant high-performance computing resources** spanning CPU-intensive numerical integration, GPU-accelerated machine learning, and symbolic computation.

### Quick Reference: Total Compute Requirements

| Resource Type | Minimum | Target | Notes |
|---------------|---------|--------|-------|
| **CPU Cores** | 32 | 64-128 | Embarrassingly parallel trajectory generation |
| **RAM** | 64 GB | 128-256 GB | For large-scale Monte Carlo validation |
| **GPU** | Optional | 1-2 GPUs (16+ GB VRAM) | Neural network training (WP3) |
| **Storage** | 500 GB | 2-5 TB | HDF5 + Parquet trajectory data |
| **Wall Time** | 2-3 weeks | 4-6 weeks | Full pipeline execution |
| **Total Core-Hours** | ~15,000 | ~50,000 | Across all work packages |

### Computational Intensity by Work Package

```
WP1 (Trajectory Generation):     ████████████████████░░  ~70% of total compute
WP2 (Geometric Foundations):     ██░░░░░░░░░░░░░░░░░░░░  ~5% of total compute
WP3 (Invariant Discovery):       ██████░░░░░░░░░░░░░░░░  ~15% of total compute
WP4 (Validation):                ████░░░░░░░░░░░░░░░░░░  ~10% of total compute
```

**Key Insight**: WP1 (high-precision trajectory generation) dominates compute requirements, accounting for ~70% of total computational budget.

---

## Table of Contents

1. [WP1: High-Precision Trajectory Generation](#wp1-high-precision-trajectory-generation)
2. [WP2: Geometric Foundations](#wp2-geometric-foundations)
3. [WP3: Invariant Discovery](#wp3-invariant-discovery)
4. [WP4: Rigorous Validation](#wp4-rigorous-validation)
5. [Aggregate Resource Planning](#aggregate-resource-planning)
6. [Hardware Recommendations](#hardware-recommendations)
7. [Cost Analysis](#cost-analysis)
8. [Optimization Strategies](#optimization-strategies)
9. [Risk Assessment](#risk-assessment)

---

## WP1: High-Precision Trajectory Generation

### Overview

WP1 provides the computational foundation by generating large-scale catalogues of high-fidelity three-body trajectories. This is the **most computationally intensive** work package, requiring sustained HPC resources for parallel integration.

### Computational Tasks

#### Task 1.1: Tier 1 Trajectory Catalogue (Standard Precision)

**Objective**: Generate 100,000 trajectories with energy conservation ΔC/C < 10⁻¹⁴

**Parameters**:
- **Number of trajectories**: N = 100,000
- **Parameter space sampling**:
  - Mass ratios (μ): 30 values in [10⁻³, 0.5] (logarithmic spacing)
  - Jacobi constants (C): 15 values in [2.5, 3.5] (linear spacing)
  - Initial conditions per (μ, C) cell: 200-250 orbits
  - Sampling method: Sobol sequences (deterministic quasi-random)
- **Integration duration**: 1,000-10,000 orbital periods per trajectory
- **Integrator**: IAS15 (adaptive 15th-order Radau)
- **Precision**: IEEE 754 double precision (15-17 decimal digits)
- **Output cadence**: Every 1.0 time units (adaptive dense output)

**Computational Requirements**:

```
Single Trajectory Performance:
- Time per orbit: ~0.02 seconds (50 orbits/second on modern CPU core)
- Average integration: 1,000 periods × 0.02 sec = 20 seconds/trajectory
- With chaos indicators (MEGNO/FLI): +30% overhead → 26 seconds/trajectory

Total Tier 1 Compute:
- Sequential time: 100,000 trajectories × 26 sec = 2.6 × 10⁶ seconds
                                                  = ~722 CPU-hours
                                                  = ~30 CPU-days

Parallel execution (64 cores):
- Wall time: 722 hours / 64 cores = 11.3 hours ≈ 0.5 days

Storage per trajectory:
- States: 1,000 timesteps × 6 DOF × 8 bytes = 48 KB
- Dense output metadata: +50% → 72 KB
- Chaos indicators (MEGNO, FLI): +10 KB → 82 KB/trajectory
- HDF5 compression (gzip level 6): 50% reduction → 41 KB/trajectory

Total Tier 1 Storage:
- Raw HDF5: 100,000 × 41 KB = 4.1 GB
- Parquet export (for ML): +2 GB = 6.1 GB total
```

**Bottlenecks**:
- I/O for HDF5 writes (mitigate with buffering, parallel HDF5)
- Memory for chaos indicators (requires storing trajectory + variational equations)

**Parallelization**:
- **Embarrassingly parallel**: Each trajectory is independent
- **Scalability**: Near-linear scaling up to ~128 cores (limited by I/O contention)
- **Snakemake orchestration**: `snakemake --cores 64 --config tier=1`

---

#### Task 1.2: Tier 2 Trajectory Catalogue (Ultra-High Precision)

**Objective**: Generate 10,000 trajectories with energy conservation ΔC/C < 10⁻²⁵ using double-double arithmetic

**Parameters**:
- **Number of trajectories**: N = 10,000 (refined subset from Tier 1)
- **Parameter space**: Same (μ, C) grid, but 30 orbits per cell instead of 200
- **Integration duration**: 10,000-100,000 periods (longer for stability analysis)
- **Integrator**: Adaptive Symplectic (6th-8th order with Richardson extrapolation)
- **Precision**: QD library double-double (31 decimal digits)
- **Output cadence**: Every 10.0 time units (reduce I/O overhead)

**Computational Requirements**:

```
Single Trajectory Performance:
- Time per orbit: ~0.08 seconds (3-4× slower than double precision)
- Average integration: 10,000 periods × 0.08 sec = 800 seconds/trajectory
- With double-double overhead: +20% → 960 seconds ≈ 16 minutes/trajectory

Total Tier 2 Compute:
- Sequential time: 10,000 trajectories × 960 sec = 9.6 × 10⁶ seconds
                                                  = ~2,667 CPU-hours
                                                  = ~111 CPU-days

Parallel execution (32 cores):
- Wall time: 2,667 hours / 32 cores = 83.3 hours ≈ 3.5 days

Storage per trajectory:
- States: 1,000 timesteps × 6 DOF × 16 bytes (dd_real) = 96 KB
- Dense output: +50% → 144 KB
- Chaos indicators: +20 KB → 164 KB/trajectory
- HDF5 compression: 60% reduction → 66 KB/trajectory

Total Tier 2 Storage:
- Raw HDF5: 10,000 × 66 KB = 660 MB
- Parquet export: +300 MB = 960 MB ≈ 1 GB total
```

**Bottlenecks**:
- **QD library overhead**: Double-double arithmetic is 3-4× slower
- **Memory**: Double-double requires 2× storage per float
- **Cache efficiency**: Larger data structures reduce cache hit rate

**Critical Dependencies**:
- QD library (C++ with Python bindings via Cython/pybind11)
- CMake build system for QD wrappers
- Properly tuned BLAS/LAPACK for matrix operations

---

#### Task 1.3: Chaos Indicators (MEGNO & FLI)

**Objective**: Classify each trajectory as regular or chaotic

**Method**:
- **MEGNO (Mean Exponential Growth of Nearby Orbits)**: Monitor variational equations
- **FLI (Fast Lyapunov Indicator)**: Track tangent vector divergence

**Computational Cost**:
- **Overhead**: +30% integration time (solve 6 additional variational equations)
- **Memory**: +50% (store deviation vectors)
- **Already included in Task 1.1/1.2 estimates above**

**Interpretation**:
- MEGNO → 2 (asymptotically): Regular orbit
- MEGNO → ∞: Chaotic orbit
- FLI threshold: ~10³ (regular) vs. >10⁶ (chaotic) after 10⁴ periods

---

### WP1 Aggregate Requirements

| Metric | Tier 1 | Tier 2 | **Total** |
|--------|--------|--------|-----------|
| **Trajectories** | 100,000 | 10,000 | **110,000** |
| **CPU-Hours** | 722 | 2,667 | **3,389** |
| **Wall Time (64/32 cores)** | 11.3 hours | 83.3 hours | **~4 days** |
| **Storage (HDF5 + Parquet)** | 6.1 GB | 1.0 GB | **~7 GB** |
| **Peak RAM** | 32 GB | 64 GB | **64 GB** |

**Note**: Wall time assumes sequential execution (Tier 1 → Tier 2). If run in parallel on separate clusters, wall time ≈ 3.5 days.

---

## WP2: Geometric Foundations

### Overview

WP2 is **primarily analytical and symbolic**, with moderate numerical compute for evaluating geometric objects (connection, curvature, metric) on trajectory data.

### Computational Tasks

#### Task 2.1: Symbolic Hamiltonian Derivations

**Objective**: Derive lifted Hamiltonians (S¹, KS-Spinor) symbolically using SymPy

**Computational Requirements**:
- **Type**: Single-threaded symbolic computation
- **Duration**: Minutes to hours (one-time setup)
- **Resources**: 1 CPU core, 4 GB RAM
- **Tools**: SymPy, SageMath (optional for Galois group computations)

**Bottlenecks**:
- Symbolic simplification of high-degree polynomials (O(n⁴) complexity)
- **Not a runtime bottleneck** (results cached)

---

#### Task 2.2: Geometric Object Evaluation

**Objective**: Compute connection A, curvature F, JM metric g on Tier 1 trajectories

**Parameters**:
- **Number of evaluations**: 100,000 trajectories × 1,000 timesteps = 10⁸ evaluations
- **Per-evaluation cost**:
  - Locked inertia tensor I(q): 6 eigenvalue decompositions → ~1 ms
  - Connection 1-form A: ∇I · v → ~0.5 ms
  - Curvature 2-form F: dA + A∧A → ~1 ms
  - JM metric g: Inverse of locked tensor → ~0.5 ms
  - **Total**: ~3 ms/evaluation

**Computational Requirements**:

```
Total Compute:
- Sequential: 10⁸ evaluations × 3 ms = 3 × 10⁵ seconds
                                      = 83 CPU-hours
                                      = 3.5 CPU-days

Parallel execution (64 cores):
- Wall time: 83 hours / 64 = 1.3 hours

Storage:
- Per trajectory: 1,000 timesteps × (3×3 tensor + 3-vector) × 8 bytes
                = 1,000 × 72 bytes = 72 KB
- Total: 100,000 × 72 KB = 7.2 GB
```

**Optimization**:
- **Vectorization**: NumPy/JAX for batch evaluation
- **JIT compilation**: JAX transforms for 10-100× speedup
- **GPU acceleration**: Optional (JAX on CUDA) → 100× speedup for large batches

---

#### Task 2.3: Coordinate Transformations

**Objective**: Transform trajectories between coordinate systems

**Transformations**:
1. Cartesian (18D) → Jacobi (15D): Remove center-of-mass
2. Jacobi → Shape Space (12D): Quotient by SO(3) rotations
3. Shape Space → S¹ Lift (13D): Add fiber coordinate θ
4. Cartesian → KS-Spinor (22D): Add 4 spinor DOF

**Cost per transformation**: ~0.1-1.0 ms (matrix multiplications, quaternion operations)

**Total Compute**: ~10 CPU-hours (negligible, done during Tier 1 generation)

---

### WP2 Aggregate Requirements

| Metric | Value |
|--------|-------|
| **CPU-Hours** | ~100 (mostly geometric evaluations) |
| **Wall Time (64 cores)** | ~2 hours |
| **Storage** | ~10 GB (geometric object fields) |
| **Peak RAM** | 16 GB |

**Characterization**: WP2 is **lightweight** compared to WP1. Main cost is developer time for symbolic derivations, not compute time.

---

## WP3: Invariant Discovery

### Overview

WP3 uses **machine learning and symbolic regression** to discover candidate conserved quantities. This is **GPU-intensive** for neural network training and **CPU-intensive** for symbolic regression.

### Computational Tasks

#### Task 3.1: Hamiltonian Neural Network (HNN) Training

**Objective**: Train neural networks to learn conserved quantities from trajectory data

**Architecture**:
- **Model**: Hamiltonian Neural Network (HNN)
  - Input: Phase space coordinates (q, p) ∈ ℝ¹²
  - Output: Predicted Hamiltonian H̃(q, p)
  - Layers: 6-8 hidden layers, 128-256 neurons/layer
  - Parameters: ~500,000-1,000,000 weights
- **Loss function**: Conservation loss + symplectic structure preservation
- **Training data**: 100,000 trajectories × 1,000 timesteps = 10⁸ samples

**Computational Requirements**:

```
Single HNN Training Run:
- Batch size: 256 samples
- Iterations: 10⁸ samples / 256 = ~400,000 batches
- Epochs: 100 (with early stopping)
- Time per batch (GPU): ~50 ms
- Total training time: 400,000 batches × 50 ms × 100 epochs / 10 (early stop)
                     = 2 × 10⁸ ms = 55 GPU-hours

Multiple Architectures (Hyperparameter Search):
- Grid search: 5 learning rates × 3 architectures × 2 regularization
              = 30 training runs
- Total GPU time: 30 × 55 hours = 1,650 GPU-hours

With modern GPU (NVIDIA A100):
- Wall time: 1,650 hours / 1 GPU = ~69 days (sequential)
- With 4 GPUs: 1,650 / 4 = ~17 days
- With early stopping + smart search: ~5-7 days on 4 GPUs
```

**Storage**:
- Model checkpoints: 30 models × 500 MB = 15 GB
- Training logs (TensorBoard): 5 GB
- **Total**: 20 GB

**Hardware**:
- **GPU**: 1-4 GPUs with 16+ GB VRAM (NVIDIA V100, A100, RTX 4090)
- **CPU**: 16 cores (data loading, preprocessing)
- **RAM**: 64 GB (hold training batches in memory)

---

#### Task 3.2: Symbolic Regression (PySR)

**Objective**: Convert learned HNN functions to symbolic expressions

**Method**: PySR (Python Symbolic Regression) with Julia backend

**Parameters**:
- **Search space**:
  - Operators: +, -, ×, /, sin, cos, exp, log, powers
  - Complexity: Expressions up to 50 nodes
  - Population size: 500-1,000 candidate expressions
- **Evolution**:
  - Generations: 1,000-10,000
  - Mutations per generation: 5,000
  - Selection: Pareto frontier (accuracy vs. complexity)

**Computational Requirements**:

```
Single Symbolic Regression Run:
- Evaluation time per candidate: ~10 ms (NumPy vectorization)
- Candidates per generation: 1,000
- Generations: 5,000
- Time per generation: 1,000 × 10 ms = 10 seconds
- Total time: 5,000 generations × 10 sec = 50,000 sec ≈ 14 CPU-hours

Three Search Stages (Spinor, Elliptic, Theta Bases):
- Stage 1 (Spinor): 80 basis functions → 20 CPU-hours
- Stage 2 (Elliptic): 50 basis functions → 15 CPU-hours
- Stage 3 (Theta): 30 basis functions → 10 CPU-hours
- **Total**: 45 CPU-hours per search iteration

Multiple Iterations (Refine Search):
- Iterations: 10 (progressive refinement)
- Total: 10 × 45 = 450 CPU-hours

Parallel execution (PySR multi-core):
- Cores: 32 (PySR spawns parallel workers)
- Wall time: 450 hours / 32 = 14 hours ≈ 0.6 days
```

**Storage**:
- Pareto frontiers (all candidates): 5 GB
- Best expressions (symbolic): 100 MB

---

#### Task 3.3: PDE Solvers (Hamilton-Jacobi Equations)

**Objective**: Solve Hamilton-Jacobi PDE to find generating functions

**Method**: Finite difference or spectral methods on (q, p) grid

**Computational Requirements**:

```
Grid-Based PDE Solver:
- Grid size: 128³ = 2 million points (3D configuration space)
- Time steps: 10,000 (implicit Euler)
- Cost per timestep: Sparse linear solve → ~2 seconds
- Total: 10,000 × 2 sec = 20,000 sec ≈ 5.5 CPU-hours

Multiple Initial Conditions:
- Number of PDEs: 50 (sweep over initial guesses)
- Total: 50 × 5.5 hours = 275 CPU-hours

Parallel execution (OpenMP):
- Cores: 16 (sparse solver threads)
- Wall time: 275 hours / 16 = 17 hours ≈ 0.7 days
```

**Note**: PDE solvers are **optional** (not critical path). Can skip if HNN + PySR succeed.

---

### WP3 Aggregate Requirements

| Metric | Value |
|--------|-------|
| **GPU-Hours** | 1,650 (HNN training) |
| **CPU-Hours** | 725 (PySR 450 + PDE 275) |
| **Wall Time (4 GPUs + 32 CPUs)** | ~7-10 days |
| **Storage** | ~40 GB (models + Pareto frontiers) |
| **Peak RAM** | 64 GB |
| **GPU VRAM** | 16 GB per GPU |

**Critical Hardware**:
- **4× NVIDIA A100 (40 GB)** or **4× RTX 4090 (24 GB)** for HNN training
- **32-64 CPU cores** for PySR (embarrassingly parallel)
- **Fast SSD** (1 TB NVMe) for training data I/O

---

## WP4: Rigorous Validation

### Overview

WP4 subjects candidate integrals to rigorous tests. Dominated by **Monte Carlo validation** (10⁵-10⁶ trajectories) and **Morales-Ramis test** (symbolic Galois group computations).

### Computational Tasks

#### Task 4.1: Analytical Vetting (Poisson Brackets)

**Objective**: Verify {Ĩ, H} = 0 symbolically and numerically

**Methods**:
1. **Symbolic differentiation** (SymPy): Compute ∂Ĩ/∂q, ∂Ĩ/∂p symbolically
2. **Numerical evaluation**: Evaluate Poisson bracket on 10⁴ sample states

**Computational Requirements**:

```
Symbolic Computation (Per Candidate):
- Derivative computation: ~10 seconds (one-time)
- Simplification: ~60 seconds (depends on complexity)
- Total per candidate: ~70 seconds

Numerical Verification:
- Sample points: 10,000
- Evaluation time: 10,000 × 1 ms = 10 seconds
- **Total per candidate**: ~80 seconds ≈ 1.3 CPU-minutes

For 100 Candidates:
- Total: 100 × 80 sec = 8,000 sec ≈ 2.2 CPU-hours
```

**Negligible** compared to other WP4 tasks.

---

#### Task 4.2: Morales-Ramis Test (Differential Galois Theory)

**Objective**: Compute Galois groups of Normal Variational Equations (NVE)

**Method**: Kovacic algorithm for 2nd-order linear ODEs

**Phases**:
1. **Phase I (Downstairs)**: Compute NVE in reduced space, verify non-abelian Galois group
2. **Phase II (Upstairs)**: Compute NVE in lifted space, check for abelian Galois group

**Computational Requirements**:

```
Single Periodic Orbit Analysis:

Phase I (Downstairs):
1. Find periodic orbit: Newton-Raphson → 50-200 iterations × 10 ms = 2 seconds
2. Integrate variational equations: 1 period × 10× integration cost = 20 seconds
3. Compute monodromy matrix: Eigenvalue decomposition → 1 ms
4. Formulate NVE symbolically: 30 seconds (SymPy)
5. Apply Kovacic algorithm: 60-600 seconds (depends on singularity structure)
   - Singularity analysis: 10 seconds
   - Case 1 trial: 20 seconds
   - Case 2 trial: 30 seconds
   - Case 3 trial: 40 seconds
   - Galois group classification: 5 seconds
- **Downstairs total**: ~120 seconds (best case) to 10 minutes (worst case)

Phase II (Upstairs):
1. Lift orbit to S¹/KS space: Coordinate transform → 1 second
2. Integrate upstairs variational equations: 1 period × 15× cost = 30 seconds
3. Formulate upstairs NVE: 60 seconds
4. Apply Kovacic algorithm upstairs: 120-900 seconds
- **Upstairs total**: ~200 seconds to 15 minutes

Total per orbit: 5-25 minutes (average: 10 minutes)

Multiple Periodic Orbits:
- Number of orbits: 20 (Lagrange L4/L5, Euler, Figure-8, Broucke families)
- Total: 20 × 10 minutes = 200 minutes ≈ 3.3 CPU-hours

Multiple Candidates (if WP3 discovers many):
- Candidates: 10
- Total: 10 × 3.3 hours = 33 CPU-hours
```

**Bottlenecks**:
- **Symbolic computation** (SymPy): Expression swell in Kovacic algorithm
- **Numerical-symbolic interface**: Converting numerical NVE to symbolic form
- **Memory**: Large symbolic expressions (10-100 MB per Galois group computation)

**Optimization**:
- Use SageMath for Galois computations (more efficient than pure SymPy)
- Cache intermediate results (monodromy matrices, NVE coefficients)
- Parallelize over multiple periodic orbits (embarrassingly parallel)

---

#### Task 4.3: Monte Carlo Validation

**Objective**: Validate conservation of candidate integrals across parameter space

**Parameters**:
- **Number of trajectories**: 100,000 - 1,000,000
- **Integration duration**: 1,000-10,000 periods per trajectory
- **Precision**: Standard double (reuse Tier 1 data where possible)

**Computational Requirements**:

```
Scenario 1: Reuse Tier 1 Data (100,000 trajectories)
- Trajectories: Already computed in WP1
- Additional cost: Evaluate candidate integral Ĩ(q,p) on stored states
- Evaluation time: 100,000 trajectories × 1,000 timesteps × 0.1 ms
                 = 10⁷ evaluations × 0.1 ms = 1,000 seconds ≈ 0.3 CPU-hours
- **Negligible** (I/O-bound, ~1 hour wall time to load HDF5 files)

Scenario 2: New Trajectories for Stress Testing (1,000,000 trajectories)
- Near-collision scenarios: 100,000 trajectories
- Chaotic regions: 500,000 trajectories
- High-eccentricity: 200,000 trajectories
- Escape orbits: 200,000 trajectories

Per-category compute (using WP1 estimates):
- Near-collision: 100,000 × 26 sec = 2,600,000 sec = 722 CPU-hours
- Chaotic: 500,000 × 26 sec = 13,000,000 sec = 3,611 CPU-hours
- High-ecc: 200,000 × 26 sec = 5,200,000 sec = 1,444 CPU-hours
- Escape: 200,000 × 26 sec = 5,200,000 sec = 1,444 CPU-hours
- **Total**: 7,221 CPU-hours ≈ 301 CPU-days

Parallel execution (128 cores):
- Wall time: 7,221 hours / 128 = 56 hours ≈ 2.3 days
```

**Storage** (if generating new trajectories):
- 1,000,000 trajectories × 41 KB = 41 GB

**Note**: This is the **single most expensive task in WP4**. Can be reduced by:
1. Reusing Tier 1 data where possible
2. Adaptive sampling (focus on regions where candidates nearly fail)
3. Lower integration duration (1,000 periods instead of 10,000)

---

#### Task 4.4: Long-Time Validation

**Objective**: Track conservation over 10⁴-10⁶ orbital periods

**Parameters**:
- **Number of trajectories**: 100 (selected representatives)
- **Integration duration**: 100,000 periods (extreme long-time test)
- **Precision**: Tier 2 (double-double) to isolate numerical error

**Computational Requirements**:

```
Single Long Trajectory:
- Duration: 100,000 periods × 0.08 sec/period = 8,000 sec ≈ 2.2 hours
- With chaos indicators: +30% → 2.9 hours

Total Compute:
- Sequential: 100 trajectories × 2.9 hours = 290 CPU-hours
- Parallel (32 cores): 290 / 32 = 9 hours wall time
```

**Critical Role**: Distinguishes between:
- **True conserved quantity**: ΔĨ/Ĩ ~ 10⁻²⁵ (constant, limited by double-double precision)
- **Adiabatic invariant**: ΔĨ/Ĩ ~ 10⁻⁸ t (slow linear drift)
- **Numerical artifact**: ΔĨ/Ĩ ~ 10⁻⁵ t (fast drift)

---

### WP4 Aggregate Requirements

| Task | CPU-Hours | Wall Time (64/128 cores) | Storage |
|------|-----------|--------------------------|---------|
| **4.1 Analytical Vetting** | 2 | <1 hour | Negligible |
| **4.2 Morales-Ramis** | 33 | ~1 hour | 1 GB |
| **4.3 Monte Carlo (Tier 1 reuse)** | 0.3 | ~1 hour (I/O) | 0 (reuse) |
| **4.3 Monte Carlo (new trajectories)** | 7,221 | ~56 hours | 41 GB |
| **4.4 Long-Time Validation** | 290 | ~9 hours | 3 GB |
| **Total (reuse Tier 1)** | **325** | **~10 hours** | **4 GB** |
| **Total (new trajectories)** | **7,546** | **~65 hours** | **45 GB** |

**Key Decision**: Reusing Tier 1 data reduces WP4 compute by **95%** (7,546 → 325 CPU-hours).

**Recommendation**: Prioritize Tier 1 data completeness in WP1 to minimize WP4 recomputation.

---

## Aggregate Resource Planning

### Total Computational Budget (Across WP1-WP4)

#### Scenario A: Optimal (Reuse WP1 Data in WP4)

| Work Package | CPU-Hours | GPU-Hours | Wall Time | Storage |
|--------------|-----------|-----------|-----------|---------|
| **WP1 (Tier 1 + Tier 2)** | 3,389 | 0 | 4 days | 7 GB |
| **WP2 (Geometric)** | 100 | 0 | 2 hours | 10 GB |
| **WP3 (Discovery)** | 725 | 1,650 | 7-10 days | 40 GB |
| **WP4 (Validation - reuse)** | 325 | 0 | 10 hours | 4 GB |
| **TOTAL** | **4,539** | **1,650** | **~14 days** | **61 GB** |

**Total Core-Hours**: 4,539 CPU + 1,650 GPU ≈ **6,200 equivalent CPU-hours** (assuming 1 GPU-hour ≈ 1 CPU-hour for cost parity)

---

#### Scenario B: Conservative (WP4 Generates New Trajectories)

| Work Package | CPU-Hours | GPU-Hours | Wall Time | Storage |
|--------------|-----------|-----------|-----------|---------|
| **WP1** | 3,389 | 0 | 4 days | 7 GB |
| **WP2** | 100 | 0 | 2 hours | 10 GB |
| **WP3** | 725 | 1,650 | 7-10 days | 40 GB |
| **WP4 (new trajectories)** | 7,546 | 0 | 2.3 days | 45 GB |
| **TOTAL** | **11,760** | **1,650** | **~17 days** | **102 GB** |

**Total Core-Hours**: 11,760 CPU + 1,650 GPU ≈ **13,400 equivalent CPU-hours**

---

### Resource Timeline (Scenario A)

```
Week 1-2: WP1 Tier 1 (100,000 trajectories)
├─ Days 1-2: Parameter generation, test runs
├─ Day 3: Full Tier 1 run (11 hours on 64 cores)
└─ Days 4-14: Tier 2 run (83 hours on 32 cores, background)

Week 2: WP2 Geometric Evaluations (concurrent with Tier 2)
├─ 2 hours on 64 cores (geometric object computation)
└─ Symbolic work (human time, not compute time)

Week 3-4: WP3 Invariant Discovery
├─ Days 1-7: HNN training (1,650 GPU-hours on 4 GPUs → 7 days)
├─ Days 8-9: PySR symbolic regression (14 hours on 32 cores)
└─ Days 9-14: Analysis, candidate ranking (human time)

Week 4-5: WP4 Validation
├─ Day 1: Analytical vetting (1 hour)
├─ Days 2-3: Morales-Ramis test (1 hour compute + human interpretation)
├─ Days 4-5: Monte Carlo validation (1 hour I/O + analysis)
└─ Days 6-7: Long-time validation (9 hours on 32 cores)

Total Calendar Time: ~5 weeks (accounting for human analysis time)
Total Active Compute Time: ~14 days wall time
```

---

## Hardware Recommendations

### Minimum Viable Configuration

**For Academic/Small Lab**:

```
Compute Server:
- CPU: 2× AMD EPYC 7543 (32 cores each) = 64 cores total
- RAM: 128 GB DDR4 ECC
- GPU: 2× NVIDIA RTX 4090 (24 GB VRAM each)
- Storage: 2 TB NVMe SSD (RAID 1 for HDF5 data)
- Network: 10 GbE for cluster file system access

Estimated Cost: ~$25,000 USD
```

**Limitations**:
- WP3 HNN training takes 2× longer (7 → 14 days) with 2 GPUs instead of 4
- No redundancy (single point of failure)

---

### Target Configuration

**For Medium Lab/Research Group**:

```
Cluster Configuration:
- Compute Nodes: 4× nodes, each with:
  - CPU: 2× AMD EPYC 7543 (64 cores/node, 256 cores total)
  - RAM: 256 GB DDR4 ECC
  - GPU: 2× NVIDIA A100 40GB (8 GPUs total)
  - Storage: 4 TB NVMe SSD (local scratch)

- Head Node: 1× node with:
  - CPU: 2× Intel Xeon (32 cores)
  - RAM: 128 GB
  - Storage: 10 TB HDD RAID 6 (shared file system)

- Network: 100 GbE InfiniBand fabric

Estimated Cost: ~$150,000 USD (including networking)
```

**Advantages**:
- WP1 completes in <1 day (256 cores → 3 hours wall time)
- WP3 completes in 3-4 days (8 GPUs with hyperparameter parallelization)
- Fault tolerance (redundant nodes)

---

### Cloud Computing Alternative

**AWS EC2 Configuration**:

```
WP1 + WP4 (CPU-intensive):
- Instance: c6i.32xlarge (128 vCPUs, 256 GB RAM)
- Spot pricing: ~$2.50/hour
- Duration: 100 hours (WP1 + WP4 sequential)
- Cost: 100 × $2.50 = $250

WP3 (GPU-intensive):
- Instance: p4d.24xlarge (8× A100 40GB, 96 vCPUs, 1.1 TB RAM)
- Spot pricing: ~$10/hour (vs. $32.77 on-demand)
- Duration: 80 hours (HNN + PySR)
- Cost: 80 × $10 = $800

Total Cloud Cost: ~$1,050 USD (one-time full pipeline run)
```

**Considerations**:
- **Pros**: No upfront hardware cost, elastic scaling, pay-as-you-go
- **Cons**: Data egress fees (~$0.09/GB), spot instance interruptions, ongoing costs for multiple runs
- **Break-even**: ~15-20 full pipeline runs before owned hardware becomes cheaper

---

## Cost Analysis

### Total Cost of Ownership (3-Year Horizon)

#### Option 1: Owned Hardware (Target Configuration)

```
Capital Expenditure:
- Hardware: $150,000
- Installation/setup: $10,000
- Software licenses (commercial tools): $5,000/year × 3 = $15,000
- Total CAPEX: $175,000

Operating Expenditure (per year):
- Electricity: 256 cores × 200W + 8 GPUs × 400W = ~80 kW
  - Usage: 8 hours/day × 365 days = 2,920 hours/year
  - Cost: 2,920 hours × 80 kW × $0.10/kWh = $23,360/year
- Cooling: +50% of electricity = $11,680/year
- Maintenance: $5,000/year
- Total OPEX: $40,040/year × 3 years = $120,120

Total 3-Year Cost: $175,000 + $120,120 = $295,120
Cost per pipeline run: $295,120 / 50 runs = $5,902/run
```

#### Option 2: Cloud (AWS)

```
Per Pipeline Run: $1,050 (from above)
Total for 50 runs over 3 years: 50 × $1,050 = $52,500

Additional Costs:
- Data storage (S3): 200 GB × $0.023/GB/month × 36 months = $165
- Data egress: 200 GB/run × 50 runs × $0.09/GB = $900
- Total: $52,500 + $165 + $900 = $53,565
```

**Verdict**: Cloud is **5× cheaper** if you run ≤50 full pipelines over 3 years.

**Owned hardware makes sense if**:
- You run >100 pipelines (extensions, parameter sweeps, follow-up projects)
- You have other compute needs (not just this project)
- You value data sovereignty (no cloud egress)

---

## Optimization Strategies

### 1. Data Reuse (Highest Impact)

**Strategy**: Maximize reuse of WP1 Tier 1 data in WP4 validation

**Impact**:
- Reduces WP4 compute from 7,546 → 325 CPU-hours (23× reduction)
- Saves ~$700 in cloud costs (or 7 days of cluster time)

**Implementation**:
- Design WP1 parameter space to cover WP4 stress test regions
- Use stratified sampling (Sobol sequences) for uniform coverage
- Store full trajectories (not just Poincaré sections) to enable post-hoc analysis

---

### 2. Adaptive Sampling in WP4

**Strategy**: Focus Monte Carlo validation on regions where candidates nearly fail

**Method**:
1. Run coarse sweep (10,000 trajectories) on WP1 data
2. Identify parameter regions where |{Ĩ, H}| ~ threshold
3. Generate new trajectories only in those regions (adaptive refinement)

**Impact**:
- Reduces new trajectories from 1,000,000 → 100,000 (10× reduction)
- Cuts WP4 compute from 7,221 → 722 CPU-hours

---

### 3. Early Stopping in WP3

**Strategy**: Use Bayesian optimization for HNN hyperparameter search instead of grid search

**Method**:
- Use Optuna or Weights & Biases for automated hyperparameter tuning
- Stop training when validation loss plateaus (early stopping)

**Impact**:
- Reduces HNN training from 1,650 → 500 GPU-hours (3× reduction)
- Cuts WP3 wall time from 10 → 4 days

---

### 4. Symbolic Caching in WP4.2

**Strategy**: Cache intermediate symbolic computations (monodromy matrices, NVE coefficients)

**Impact**:
- Morales-Ramis test becomes ~2× faster on repeated runs
- Critical for iterative debugging/refinement

**Implementation**: Use `functools.lru_cache` or custom disk-based cache (SymPy pickles)

---

### 5. GPU Acceleration for Geometric Evaluations (WP2)

**Strategy**: Use JAX on CUDA for batch geometric object evaluation

**Impact**:
- WP2 compute drops from 100 → 1 CPU-hour (100× speedup)
- Negligible wall time (minutes instead of hours)

**Trade-off**: Requires JAX/CUDA setup, but ROI is high if evaluating >10⁷ points

---

## Risk Assessment

### Computational Risks

#### Risk 1: Tier 2 Integration Failures (High Impact, Medium Probability)

**Scenario**: Double-double integrator fails to converge for chaotic orbits

**Mitigation**:
- Implement adaptive error control (Richardson extrapolation)
- Fall back to quad precision (128-bit) if double-double insufficient
- Use regularization (KS transform) preemptively for near-collision orbits

**Contingency**: Budget +50% time for Tier 2 (3.5 → 5 days wall time)

---

#### Risk 2: HNN Training Divergence (Medium Impact, Medium Probability)

**Scenario**: HNN fails to learn conserved quantities (common in chaotic systems)

**Mitigation**:
- Use physics-informed loss (penalize non-conservation explicitly)
- Pre-train on known conserved quantities (E, L, C) before searching for new ones
- Try alternative architectures (Graph Neural Networks for better generalization)

**Contingency**: Rely more heavily on PySR (symbolic regression) instead of HNNs

---

#### Risk 3: Monte Carlo Validation Explosion (Low Impact, High Probability)

**Scenario**: WP4 reveals candidates fail in unexpected regions → need 10× more trajectories

**Mitigation**:
- Use adaptive sampling (focus on failure regions)
- Implement "kill switch" logic (stop validation if failure rate >10%)
- Accept negative results early (don't chase false positives)

**Contingency**: Budget +100% compute for WP4 if pursuing marginal candidates

---

#### Risk 4: I/O Bottlenecks (Low Impact, High Probability)

**Scenario**: HDF5 writes saturate disk bandwidth, slowing WP1 integration

**Mitigation**:
- Use parallel HDF5 (MPI-IO) for concurrent writes
- Buffer outputs in RAM, batch writes every 100 trajectories
- Use NVMe SSDs (5 GB/s bandwidth) instead of HDDs (200 MB/s)

**Contingency**: Increase WP1 wall time by 20-30% (4 → 5 days)

---

### Timeline Risks

#### Risk 5: WP3 Discovery Failure (Critical Impact, Low-Medium Probability)

**Scenario**: No candidate integrals discovered (negative result)

**Impact on Compute**:
- WP4 validation unnecessary → Save ~7,000 CPU-hours
- But may need WP3 re-runs with different methods → +500 GPU-hours

**Scientific Impact**: Negative results are still publishable (computational bounds on integrability)

**Mitigation**: Plan manuscript structure for both positive and negative outcomes

---

## Summary and Recommendations

### Key Takeaways

1. **WP1 dominates compute** (~70% of total): Invest in parallelization and I/O optimization
2. **WP3 is GPU-bound**: Access to 4-8 modern GPUs (A100 or RTX 4090) is critical
3. **WP4 benefits massively from WP1 data reuse**: Plan parameter space carefully in WP1
4. **Total budget**: 4,500-12,000 CPU-hours + 1,650 GPU-hours depending on WP4 strategy

### Resource Allocation Priority

```
Priority 1: Secure GPU access (WP3 is on critical path)
├─ Option A: 4× NVIDIA A100 40GB (cloud or owned)
└─ Option B: 8× RTX 4090 (better $/TFLOP for FP32, sufficient for HNNs)

Priority 2: CPU cluster for WP1 (embarrassingly parallel)
├─ Minimum: 64 cores (wall time: 1 week)
└─ Target: 128-256 cores (wall time: 2-3 days)

Priority 3: Fast storage for HDF5 I/O
├─ Minimum: 1 TB NVMe SSD (local)
└─ Target: 10 TB RAID (shared file system with parallel HDF5)

Priority 4: RAM for WP3/WP4
├─ Minimum: 64 GB (tight but workable)
└─ Target: 128-256 GB (comfortable for large batches)
```

### Cost-Effective Execution Plan

**For Academic Budget (~$50,000 total)**:

1. **Hybrid approach**:
   - WP1 + WP4: Use university HPC cluster (often free/subsidized)
   - WP3: Rent AWS p4d instances for 1 week (~$1,000)

2. **Stagger execution**:
   - Run WP1 Tier 1 on cluster (queue for 3-5 days)
   - Run WP2 on local workstation (negligible compute)
   - Run WP3 on cloud burst (tight 1-week sprint)
   - Run WP4 on cluster (reuse WP1 data)

3. **Total cost**:
   - Cloud (WP3 only): ~$1,000
   - Cluster fees (if any): ~$500
   - **Total**: <$2,000

**For Industry/Well-Funded Lab (~$150,000 total)**:

1. **Buy dedicated hardware** (target configuration above)
2. Run all WP1-4 on owned cluster
3. Amortize cost over multiple projects (3-5 years)
4. **Cost per project**: ~$30,000-50,000 (including OPEX)

---

**Document Status**: Complete
**Last Updated**: 2025-11-23
**Next Review**: After WP1 Tier 1 completion (update actual vs. estimated performance)
