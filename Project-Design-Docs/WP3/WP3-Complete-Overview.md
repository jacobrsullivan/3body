# Work Package 3: Discovery of Candidate Invariants ($\widetilde{I}$)
## Complete Overview and Implementation Guide

**Status**: Design Phase - Ready for Planning
**Documentation Version**: 1.0
**Last Updated**: 2025-11-14
**Prerequisites**: WP2 Complete (Geometric Foundations and Lift Constructions)
**Next Phase**: WP4 Rigorous Validation

---

## Executive Summary

Work Package 3 represents the **critical discovery phase** of the lift-integrability hypothesis. Using the geometric foundations and higher-dimensional embeddings constructed in WP2, WP3 employs a multi-pronged strategy to search for new conserved quantities ($\widetilde{I}$) that exist "upstairs" in the lifted spaces but are invisible "downstairs" in the standard three-body problem.

### Core Objective

**Search for Hidden Integrals**: Discover conserved quantities in the lifted phase spaces (S¹ bundle or KS-Spinor coordinates) that:
1. Are non-trivial (functionally independent of E, L, and fiber coordinates)
2. Satisfy the Liouville integrability criteria (conservation, independence, involution)
3. Provide insight into the geometric structure of three-body dynamics

### WP3 Three-Track Approach

```
WP3: Invariant Discovery (3 parallel tracks, ~35-45 days total)
│
├── WP 3.1: Deterministic Geometric Search (15-18 days)
│   └── Killing Fields/Tensors via PDE solvers
│
├── WP 3.2: Structure-Preserving ML Discovery (18-22 days)
│   └── Hamiltonian Neural Networks + Conservation constraints
│
└── WP 3.3: Symbolic Regression & Consolidation (10-12 days)
    └── Convert numerical candidates → analytical expressions
```

**Philosophy**: Cast a wide net using complementary methodologies, then consolidate and validate the most promising candidates.

---

## Table of Contents

1. [Component Overview](#component-overview)
2. [Mathematical Framework](#mathematical-framework)
3. [Implementation Architecture](#implementation-architecture)
4. [Integration Strategy](#integration-strategy)
5. [Deliverables Checklist](#deliverables-checklist)
6. [Quality Metrics](#quality-metrics)
7. [Handoff to WP4](#handoff-to-wp4)
8. [Risk Assessment](#risk-assessment)
9. [Timeline and Dependencies](#timeline-and-dependencies)
10. [References and Resources](#references-and-resources)

---

## Component Overview

### WP 3.1: Deterministic Geometric Search (Killing Fields/Tensors)

**Duration**: 15-18 days | **Approach**: Direct PDE solution

**Core Idea**: If a conserved quantity $\widetilde{I}$ exists, it must correspond to a symmetry of the lifted geometry. For the Jacobi-Maupertuis metric, these symmetries are characterized by:
- **Killing vector fields** (linear integrals): $\nabla_{(i} K_{j)} = 0$
- **Killing tensors** (quadratic integrals): $\nabla_{(k} K_{ij)} = 0$

**Tasks**:
- **3.1.1**: Implement lifted JM metric on S¹ bundle and KS spaces
- **3.1.2**: Formulate Killing PDEs (both vector and tensor forms)
- **3.1.3**: Numerical PDE solution (mesh discretization + least-squares solver)
- **3.1.4**: Convert discovered fields → conserved quantities + triviality filtering

**Key Innovation**: First systematic geometric search for hidden symmetries in higher-dimensional three-body embeddings.

**Deliverable**: Library of candidate Killing fields/tensors OR rigorous bounds on non-existence.

---

### WP 3.2: Structure-Preserving Machine Learning Discovery

**Duration**: 18-22 days | **Approach**: Geometric deep learning

**Core Idea**: Train neural networks that respect the symplectic structure to implicitly learn conserved quantities from trajectory data.

**Architecture**: Hamiltonian Neural Networks (HNNs) or Symplectic Neural Networks (SympNets)
- Network learns the lifted Hamiltonian $\widetilde{H}$
- Auxiliary head predicts candidate integral $\widetilde{I}$
- Loss function enforces $\{I, \widetilde{H}\}_{\widetilde{\omega}} = 0$ (conservation)

**Tasks**:
- **3.2.1**: Generate high-precision training datasets on lifted spaces
- **3.2.2**: Implement HNN/SympNet architecture (JAX or PyTorch)
- **3.2.3**: Design conservation-constrained training with Noether regularizers
- **3.2.4**: Out-of-distribution validation and generalization testing

**Key Innovation**: First application of structure-preserving ML to hidden integral discovery in celestial mechanics.

**Deliverable**: Trained models capable of predicting conserved quantities + numerical representations of $\widetilde{I}$.

---

### WP 3.3: Symbolic Regression and Consolidation

**Duration**: 10-12 days | **Approach**: Data-driven symbolic discovery

**Core Idea**: Convert numerical candidates (from WP 3.1 and 3.2) into concise analytical expressions suitable for symbolic validation (WP4).

**Tools**: SINDy (Sparse Identification of Nonlinear Dynamics), PySR, AI-Feynman

**Tasks**:
- **3.3.1**: Build symbolic regression pipeline with physics-informed basis functions
- **3.3.2**: Optimize search space (restrict to polynomials/rationals in geometric quantities)
- **3.3.3**: Consolidate candidates from all tracks + rank by simplicity & conservation accuracy

**Key Innovation**: Bridge between numerical discovery and analytical validation.

**Deliverable**: Consolidated list of analytical candidate integrals $\widetilde{I}$ ranked by promise.

---

## Mathematical Framework

### The Integrability Landscape

**Classical Integrability (Liouville-Arnold)**:

For an $n$-DOF Hamiltonian system to be integrable, we need:
1. **n independent integrals** $I_1 = H, I_2, \ldots, I_n$
2. **In involution**: $\{I_i, I_j\}_\omega = 0$ for all $i, j$
3. **Functional independence**: $\text{rank}(dI_1 \wedge \cdots \wedge dI_n) = n$

**For the 3-Body Problem**:

| Coordinate System | DOF | Known Integrals | Needed for Integrability | Gap |
|-------------------|-----|-----------------|-------------------------|-----|
| **Downstairs** (reduced) | 3 (planar) | 2 (E, L) | 3 | **1 missing** |
| **S¹ Lift** | 4 | 3 (E, L, $p_\theta$)? | 4 | **0 or 1** |
| **KS Spinor Lift** | 9 (constrained) | 2 (E, L) + ? | 9 | **7 missing** |

**WP3 Goal**: Find the missing integral(s)!

---

### Geometric Integrals: Killing Structures

#### Killing Vector Fields (Linear Integrals)

A vector field $K$ on the lifted configuration manifold is a **Killing vector** if it preserves the lifted JM metric:

$$
\mathcal{L}_K g_{JM} = 0 \quad \Leftrightarrow \quad \nabla_{(i} K_{j)} = 0
$$

**Associated Integral**:
$$
I_K = g_{JM}(K, \dot{q}) = K_i \dot{q}^i
$$

**Physical Interpretation**: Generators of continuous symmetries (Noether's theorem).

**Example**: In the Kepler problem, rotational symmetry → angular momentum conservation.

---

#### Killing Tensors (Quadratic Integrals)

A symmetric (0,2)-tensor field $K_{ij}$ is a **Killing tensor** if:

$$
\nabla_{(k} K_{ij)} = 0
$$

**Associated Integral**:
$$
I_{KT} = K_{ij} \dot{q}^i \dot{q}^j
$$

**Physical Interpretation**: Hidden symmetries not associated with group actions.

**Example**: Kepler problem in 4D (after KS lift) has SO(4) symmetry → Runge-Lenz vector (Killing tensor).

---

### Machine Learning Integrals: Implicit Conservation

**Hamiltonian Neural Networks (HNNs)**:

Learn the Hamiltonian structure directly:
$$
\widetilde{H}_\theta(\mathbf{q}, \mathbf{p}) \approx \widetilde{H}_{\text{true}}
$$

with dynamics:
$$
\dot{\mathbf{q}} = \frac{\partial \widetilde{H}_\theta}{\partial \mathbf{p}}, \quad \dot{\mathbf{p}} = -\frac{\partial \widetilde{H}_\theta}{\partial \mathbf{q}}
$$

**Conservation-Constrained Training**:

Add auxiliary network $I_\phi(\mathbf{q}, \mathbf{p})$ with loss:
$$
\mathcal{L} = \mathcal{L}_{\text{trajectory}} + \lambda \mathbb{E}\left[\left|\frac{dI_\phi}{dt}\right|^2\right]
$$

where $\frac{dI_\phi}{dt} = \{I_\phi, \widetilde{H}_\theta\}$.

**Key Advantage**: Can discover integrals that are complicated functions, not necessarily polynomial.

---

## Implementation Architecture

### Track 1: Killing Field Search (WP 3.1)

```
Input: Lifted JM Metric g_JM (from WP2)
  ↓
Discretize lifted configuration manifold (mesh generation)
  ↓
Formulate Killing PDE system (sparse linear constraints)
  ↓
Solve numerically (least-squares + regularization)
  ↓
Filter trivial solutions (E, L, p_θ, fiber coordinates)
  ↓
Output: Candidate Killing fields K → Integrals I_K
```

**Key Modules**:
- `src/python/geometry/lifted_jm_metric.py` - JM metric on bundles
- `src/python/pde/killing_equations.py` - PDE formulation
- `src/python/pde/mesh_discretization.py` - Finite element mesh
- `src/python/pde/killing_solver.py` - Numerical solver
- `src/python/analysis/integral_from_killing.py` - K → I conversion

---

### Track 2: ML Discovery (WP 3.2)

```
Input: High-precision trajectory data on lift
  ↓
Train HNN/SympNet (learn lifted Hamiltonian)
  ↓
Add auxiliary head (predict candidate integral I_φ)
  ↓
Constrained training: enforce dI_φ/dt = 0
  ↓
Out-of-distribution validation (new mass ratios, energies)
  ↓
Extract learned function I_φ(q, p)
  ↓
Output: Numerical representation of conserved quantity
```

**Key Modules**:
- `src/python/ml/data_generation.py` - High-precision dataset creation
- `src/python/ml/hnn_architecture.py` - HNN/SympNet models
- `src/python/ml/conservation_loss.py` - Physics-informed loss
- `src/python/ml/noether_regularizers.py` - Symmetry priors
- `src/python/ml/validation.py` - Generalization testing

---

### Track 3: Symbolic Consolidation (WP 3.3)

```
Input: Numerical candidates (from 3.1 and 3.2)
  ↓
Generate high-precision evaluation data
  ↓
Symbolic regression (SINDy/PySR)
  ↓
Restrict to physically motivated basis functions
  ↓
Simplify expressions (SymPy/Mathematica)
  ↓
Numerical validation: does symbolic form conserve?
  ↓
Output: Analytical expressions for I~ candidates
```

**Key Modules**:
- `src/python/symbolic/regression_pipeline.py` - SINDy/PySR interface
- `src/python/symbolic/basis_functions.py` - Physics-informed basis
- `src/python/symbolic/simplification.py` - Expression optimization
- `src/python/symbolic/validation.py` - Symbolic vs. numerical comparison

---

## Integration Strategy

### Parallel Execution Plan

**Weeks 1-2**: Launch all three tracks simultaneously
- WP 3.1 starts with metric implementation
- WP 3.2 starts with data generation
- WP 3.3 sets up infrastructure (waits for candidates)

**Week 3**: First checkpoint
- WP 3.1: Initial Killing field candidates available
- WP 3.2: Training data ready, model architecture implemented
- WP 3.3: Begins symbolic regression on WP 3.1 candidates

**Weeks 4-5**: Iteration and refinement
- Cross-validate candidates between tracks
- Use WP 3.1 results to inform WP 3.2 architecture
- Feed WP 3.2 outputs into WP 3.3 pipeline

**Week 6**: Consolidation
- Merge candidate lists
- Rank by conservation accuracy and simplicity
- Prepare handoff to WP4

---

### Data Flow Between Tracks

```
WP 2.2/2.3 (Lifts)
    ↓
    ├─→ WP 3.1 (Geometric)
    │   └─→ Killing fields → Integrals → WP 3.3
    │
    ├─→ WP 3.2 (ML)
    │   └─→ Trained models → Numerical I → WP 3.3
    │
    └─→ WP 3.3 (Symbolic)
        └─→ Analytical expressions → WP 4
```

**Key Insight**: Tracks are complementary, not redundant.
- WP 3.1: Best for simple, polynomial integrals
- WP 3.2: Can find complex, non-polynomial forms
- WP 3.3: Provides analytical validation-ready expressions

---

## Deliverables Checklist

### WP 3.1: Geometric Search

**Code Deliverables**:
- [ ] `src/python/geometry/lifted_jm_metric.py` - JM metric on S¹ and KS spaces
- [ ] `src/python/pde/killing_equations.py` - Killing PDE formulation
- [ ] `src/python/pde/mesh_discretization.py` - Manifold discretization
- [ ] `src/python/pde/killing_solver.py` - PDE numerical solver
- [ ] `src/python/analysis/integral_from_killing.py` - Field → integral conversion
- [ ] `src/python/analysis/triviality_filter.py` - Filter known integrals

**Validation**:
- [ ] Metric implementation verified (limiting cases: Kepler, equal mass)
- [ ] PDE solver tested on known cases (sphere: rotations are Killing fields)
- [ ] Killing fields for Kepler problem recovered (angular momentum, Runge-Lenz)
- [ ] Non-trivial candidates (if any) pass initial conservation tests

**Documentation**:
- [ ] Technical report: "Geometric Search for Hidden Symmetries"
- [ ] Visualization: Killing field streamlines on lifted manifolds
- [ ] Negative result documentation (if no non-trivial fields found)

---

### WP 3.2: ML Discovery

**Code Deliverables**:
- [ ] `src/python/ml/data_generation.py` - Lifted trajectory datasets
- [ ] `src/python/ml/hnn_architecture.py` - HNN/SympNet implementation
- [ ] `src/python/ml/conservation_loss.py` - Physics-informed loss functions
- [ ] `src/python/ml/noether_regularizers.py` - Symmetry priors
- [ ] `src/python/ml/training.py` - Training loop with conservation enforcement
- [ ] `src/python/ml/validation.py` - Out-of-distribution testing

**Validation**:
- [ ] HNN accurately reproduces lifted dynamics (trajectory prediction error < 1%)
- [ ] Predicted integral $I_\phi$ conserved: $|\Delta I_\phi| / |I_\phi| < 10^{-6}$
- [ ] Generalization: works on held-out mass ratios and energy shells
- [ ] Independence: $I_\phi$ not a function of E, L, $p_\theta$ only

**Documentation**:
- [ ] Technical report: "Machine Learning Discovery of Hidden Integrals"
- [ ] Training curves: loss vs. epochs, conservation accuracy
- [ ] Ablation studies: effect of Noether regularizers

---

### WP 3.3: Symbolic Consolidation

**Code Deliverables**:
- [ ] `src/python/symbolic/regression_pipeline.py` - SINDy/PySR integration
- [ ] `src/python/symbolic/basis_functions.py` - Geometric basis library
- [ ] `src/python/symbolic/simplification.py` - Expression optimization
- [ ] `src/python/symbolic/candidate_ranking.py` - Scoring and filtering
- [ ] `src/python/symbolic/validation.py` - Symbolic conservation verification

**Validation**:
- [ ] Symbolic expressions reproduce numerical candidates (residual < 1e-10)
- [ ] Expressions are maximally simplified (using SymPy/Mathematica)
- [ ] Ranking correlates with conservation accuracy and complexity
- [ ] Top candidates pass preliminary Poisson bracket tests

**Documentation**:
- [ ] Technical report: "Symbolic Representations of Candidate Integrals"
- [ ] Table: Top 10 candidates with expressions, complexity, conservation error
- [ ] Comparison: Symbolic vs. numerical accuracy trade-offs

---

## Quality Metrics

### Numerical Precision Targets

| Quantity | Target | Measurement |
|----------|--------|-------------|
| **Conservation Accuracy** | $\|\Delta \widetilde{I}\| / \|\widetilde{I}\| < 10^{-6}$ | Time-series of candidate integral |
| **Functional Independence** | Jacobian rank increases by 1 | Numerical rank on 10^4 random states |
| **Generalization (ML)** | <5% accuracy drop out-of-dist | Held-out test set performance |
| **Symbolic Residual** | $< 10^{-10}$ | Symbolic - numerical difference |
| **PDE Solver Convergence** | Mesh refinement → stable solution | Richardson extrapolation |

---

### Code Quality Standards

**Target Metrics**:
- Test coverage: > 90% (ML components may be lower)
- Docstring coverage: 100% (all public APIs)
- Type hints: 100%
- Lint compliance: Zero warnings

**Performance**:
- Killing PDE solve: < 10 minutes for 10^4 mesh points
- ML training: Convergence in < 1000 epochs
- Symbolic regression: < 1 hour per candidate
- Batch evaluation: > 1000 states/second

---

## Handoff to WP4

### Outputs Provided to WP4

**From WP 3.1 (Geometric)**:
- Candidate Killing fields $K$ and tensors $K_{ij}$
- Associated integrals $I_K$
- Numerical evidence of conservation
- Metadata: degree, coordinate dependencies

**From WP 3.2 (ML)**:
- Trained HNN/SympNet models
- Numerical functions $I_\phi(q, p)$
- Evaluation datasets for validation
- Generalization test results

**From WP 3.3 (Symbolic)**:
- Consolidated list of analytical expressions
- Ranked by: (1) conservation accuracy, (2) simplicity, (3) independence
- Preliminary Poisson bracket computations
- SymPy/Mathematica code for symbolic validation

---

### WP4 Entry Criteria

**Required for WP4 to Begin**:
1. At least one non-trivial candidate integral with conservation error < 10^{-6}
2. Symbolic expression available (not just numerical)
3. Preliminary functional independence verified (Jacobian rank test on sample)

**If No Candidates Found**:
- Document search space covered (degree, coordinate systems, mesh resolution)
- Provide rigorous negative results (bounds on non-existence)
- Still proceed to WP4.2 (Morales-Ramis test confirms downstairs non-integrability)

---

## Risk Assessment

### Scientific Risks

**Risk 1: No Non-Trivial Integrals Exist (Even Upstairs)**
- **Probability**: Medium (30%)
- **Impact**: High (challenges core hypothesis)
- **Mitigation**:
  - Negative result is scientifically valid and publishable
  - Establishes rigorous bounds on hidden symmetries
  - Informs future lift construction strategies

**Risk 2: Integrals Exist But Are Too Complex to Discover**
- **Probability**: Medium (25%)
- **Impact**: Medium
- **Mitigation**:
  - Use multiple discovery methods (geometric + ML + symbolic)
  - Start with low-degree search, incrementally increase complexity
  - Focus on physically motivated subspaces (e.g., planar, equal mass)

**Risk 3: Discovered Integrals Are Numerically Unstable**
- **Probability**: Low (15%)
- **Impact**: Medium
- **Mitigation**:
  - High-precision validation from the start
  - Regularization techniques for near-singular configurations
  - Multiple coordinate representations

---

### Implementation Risks

**Risk 4: PDE Solver Non-Convergence**
- **Probability**: Medium (30%)
- **Impact**: Low (can increase mesh resolution or use alternative methods)
- **Mitigation**:
  - Start with coarse mesh, refine adaptively
  - Multiple solver backends (SciPy, FEniCS, custom)
  - Fallback to lower-order approximations

**Risk 5: ML Overfitting to Spurious Patterns**
- **Probability**: Medium-High (40%)
- **Impact**: Low (detected by out-of-distribution validation)
- **Mitigation**:
  - Rigorous train/validation/test splits
  - Hold out entire parameter regimes (not just random states)
  - Physics-informed regularization (Noether priors)
  - Cross-validation with symbolic regression

**Risk 6: Symbolic Regression Doesn't Converge**
- **Probability**: Low (20%)
- **Impact**: Low (can use numerical forms in WP4)
- **Mitigation**:
  - Restrict basis function library (physical constraints)
  - Use multiple tools (SINDy, PySR, AI-Feynman)
  - Manually guided simplification if needed

---

### Computational Risks

**Risk 7: Insufficient Computational Resources**
- **Probability**: Low (10%)
- **Impact**: Medium (delays timeline)
- **Mitigation**:
  - Parallelize across mesh regions (WP 3.1)
  - Use GPU acceleration (WP 3.2)
  - Cloud compute if local resources insufficient
  - Reduce problem size (planar only, restricted mass ratios)

---

## Timeline and Dependencies

### Critical Path (Sequential Dependencies)

```
WP 2 Complete
    ↓
WP 3.1.1 (Lifted Metric) ← MUST complete before 3.1.2-3.1.4
    ↓
WP 3.1.2 (PDE Formulation) ← MUST complete before 3.1.3
    ↓
WP 3.1.3 (PDE Solution) ← Can run parallel with 3.2
    ↓
WP 3.3 (Consolidation) ← Requires outputs from 3.1 and 3.2
    ↓
WP 4 (Validation)
```

### Parallelization Opportunities

**Weeks 1-2**:
- WP 3.1.1 (Metric) + WP 3.2.1 (Data Generation) + WP 3.3.1 (Pipeline Setup)

**Weeks 2-4**:
- WP 3.1.3 (PDE Solve) ∥ WP 3.2.2-3.2.3 (ML Training)

**Weeks 4-5**:
- WP 3.1.4 (Integral Conversion) + WP 3.2.4 (Validation) → feed into 3.3

**Week 6**:
- WP 3.3.2-3.3.3 (Consolidation) - Sequential, requires inputs from both tracks

---

### Estimated Durations

| Component | Optimistic | Realistic | Pessimistic |
|-----------|------------|-----------|-------------|
| **WP 3.1** | 12 days | 15 days | 18 days |
| **WP 3.2** | 15 days | 18 days | 22 days |
| **WP 3.3** | 8 days | 10 days | 12 days |
| **Total (with parallelization)** | 25 days | 35 days | 45 days |

**Assumptions**:
- 3.1 and 3.2 run in parallel (Weeks 1-4)
- 3.3 starts in Week 3 (partial overlap)
- Buffer for iteration between tracks

---

## References and Resources

### Geometric Methods

1. **Killing Tensors and Integrability**:
   - Benenti, S. "Intrinsic characterization of the variable separation in the Hamilton-Jacobi equation" (2002)
   - Hauser & Malhiot, "Spherically symmetric static spacetimes which admit stationary Killing tensors of rank two" (1975)
   - Kalnins et al., "Tools for verifying classical and quantum superintegrability" (2010)

2. **Jacobi-Maupertuis Metric**:
   - Pettini, M. *Geometry and Topology in Hamiltonian Dynamics and Statistical Mechanics* (2007)
   - Casetti et al., "Geometric approach to Hamiltonian dynamics and statistical mechanics" (2000)

---

### Machine Learning for Physics

3. **Hamiltonian Neural Networks**:
   - Greydanus et al., "Hamiltonian Neural Networks" (2019) - Original HNN paper
   - Toth et al., "Hamiltonian Generative Networks" (2020)
   - Chen et al., "Symplectic Recurrent Neural Networks" (2020)

4. **Conservation Law Discovery**:
   - Cranmer et al., "Lagrangian Neural Networks" (2020)
   - Zhong et al., "Unsupervised Learning of Lagrangian Dynamics from Images" (2020)
   - Sanchez-Gonzalez et al., "Learning to Simulate Complex Physics with Graph Networks" (2020)

---

### Symbolic Regression

5. **SINDy Framework**:
   - Brunton et al., "Discovering governing equations from data by sparse identification of nonlinear dynamical systems" (2016)
   - Champion et al., "Data-driven discovery of coordinates and governing equations" (2019)

6. **PySR and Evolutionary Methods**:
   - Cranmer, M. "Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl" (2023)
   - Schmidt & Lipson, "Distilling free-form natural laws from experimental data" (2009)

7. **AI-Feynman**:
   - Udrescu & Tegmark, "AI Feynman: A physics-inspired method for symbolic regression" (2020)

---

### Three-Body Problem & Integrability

8. **Classical Results**:
   - Bruns, H. *Über die Integrale des Vielkörper-Problems* (1887) - Original no-go theorem
   - Poincaré, H. *Les Méthodes Nouvelles de la Mécanique Céleste* (1892-1899)
   - Siegel, C. L. "On the integrals of canonical systems" (1941)

9. **Modern Perspectives**:
   - Moeckel, R. "Lectures on Central Configurations" (2014)
   - Chenciner, A. "Three-body problem" (2012) - Scholarpedia article
   - Féjoz, J. "Quasiperiodic motions in the planar three-body problem" (2004)

---

## Summary Statistics

### Documentation Structure

**Main Documents**:
- WP3 Complete Overview: This document
- WP 3.1 Implementation Plan: Killing Fields (separate document)
- WP 3.2 Implementation Plan: ML Discovery (separate document)
- WP 3.3 Implementation Plan: Symbolic Regression (separate document)
- Individual Task Plans: 3.1.1 through 3.3.3 (10 detailed documents)

**Total Estimated Documentation**: ~15,000 lines across all WP3 documents

---

### Key Deliverables Summary

**Scientific Outputs**:
- Candidate conserved quantities (geometric + ML + symbolic)
- Rigorous bounds on hidden symmetries (if negative result)
- Methodology for integral discovery in lifted spaces

**Code Outputs**:
- ~25 new Python modules
- ~40 validation tests
- ~15 visualization and analysis tools
- Trained ML models (HNN/SympNet)

**Documentation Outputs**:
- 3 technical reports (one per WP 3.x)
- Tutorial notebooks (geometric search, ML training, symbolic regression)
- API documentation
- Negative result documentation (if applicable)

---

## Strategic Decision Points

### Decision Point 1: After WP 3.1 (Geometric Search)

**Question**: Did we find non-trivial Killing fields?

```
├─ YES: Non-trivial Killing fields found
│  └─→ HIGH PRIORITY: Validate in WP 3.3 immediately
│       Feed into ML as priors (WP 3.2)
│       Skip some ML search space
│
├─ PARTIAL: Only low-degree or trivial fields
│  └─→ Continue with ML (may find higher-degree integrals)
│       Use geometric results to inform basis functions
│
└─ NO: No non-trivial Killing fields up to degree N
   └─→ Document rigorous negative result
        Increase N (computational cost increases)
        Rely on ML to find complex forms
```

---

### Decision Point 2: After WP 3.2 (ML Training)

**Question**: Do trained networks predict conserved quantities?

```
├─ YES: Conservation error < 10^-6
│  └─→ SUCCESS: Extract numerical form
│       Proceed to symbolic regression (WP 3.3)
│       Validate out-of-distribution
│
├─ PARTIAL: Conservation error 10^-6 to 10^-3
│  └─→ Possible approximate integral
│       Check if regime-specific (e.g., low energy only)
│       May indicate near-integrability
│
└─ NO: No conserved quantities learned
   └─→ Debugging: Check training hyperparameters
        Check data quality and coverage
        Fallback: Document negative result
```

---

### Decision Point 3: After WP 3.3 (Symbolic Regression)

**Question**: Can we express candidates analytically?

```
├─ YES: Symbolic form with residual < 10^-10
│  └─→ EXCELLENT: Ready for WP4 validation
│       Analytical Poisson brackets computable
│       Publishable result
│
├─ PARTIAL: Approximate symbolic form
│  └─→ Use as starting point for manual refinement
│       Validate numerically in WP4
│       May be sufficient for partial results
│
└─ NO: No simple symbolic form
   └─→ Document complexity of discovered integrals
        Proceed to WP4 with numerical forms
        Poisson brackets computed numerically
```

---

## Conclusion

Work Package 3 represents the **discovery core** of the lift-integrability research program. By employing three complementary methodologies—deterministic geometric search, structure-preserving machine learning, and symbolic regression—WP3 maximizes the probability of finding hidden conserved quantities if they exist, while also establishing rigorous negative results if they do not.

### Success Scenarios

**Best Case**:
- Discover analytical expression for $\widetilde{I}$
- Conservation verified to $< 10^{-10}$
- Functionally independent of known integrals
- → Proceed to WP4 for rigorous validation

**Good Case**:
- Discover numerical $\widetilde{I}$ (complex, non-polynomial)
- Conservation verified to $< 10^{-6}$
- Regime-specific or approximate
- → Partial integrability, still publishable

**Acceptable Case**:
- No non-trivial integrals found
- Rigorous bounds established on non-existence
- Methodology validated on test cases
- → Negative result, informs future lift strategies

### Readiness for Implementation

✅ **Mathematical Framework**: Complete understanding of Killing structures, HNNs, symbolic regression
✅ **Algorithmic Strategy**: Clear three-track approach with consolidation phase
✅ **Validation Plan**: Multiple checkpoints and decision points
✅ **Flexible Design**: Adapts to positive, partial, or negative results
✅ **Clear Handoff to WP4**: Well-defined outputs and entry criteria

**Next Action**: Begin detailed implementation planning for WP 3.1.1 (Lifted JM Metric).

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Complete Overview - Ready for Detailed Task Planning
**Total Estimated WP3 Duration**: 35-45 days (with parallelization)
**Next Document**: Task 3.1.1 Implementation Plan
