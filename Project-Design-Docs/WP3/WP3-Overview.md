# Work Package 3: Discovery of Candidate Invariants

**Multi-Track Search for Hidden Integrals in Lifted Phase Spaces**

**Status**: Design Phase - Ready for Planning
**Last Updated**: 2025-11-25
**Prerequisites**: WP2 Complete
**Next Phase**: WP4 (Rigorous Validation)

---

## Executive Summary

WP3 represents the **critical discovery phase** of the lift-integrability hypothesis. Using the geometric foundations and higher-dimensional embeddings from WP2, WP3 employs a multi-pronged strategy to search for new conserved quantities ($\widetilde{I}$) that exist "upstairs" in the lifted spaces but are invisible "downstairs."

### Core Objective

**Search for Hidden Integrals**: Discover conserved quantities in lifted phase spaces (S^1 bundle or KS-Spinor coordinates) that:
1. Are non-trivial (functionally independent of E, L, and fiber coordinates)
2. Satisfy Liouville integrability criteria (conservation, independence, involution)
3. Provide insight into three-body dynamics geometric structure

---

## Three-Track Approach

```
WP3: Invariant Discovery (3 parallel tracks, ~35-45 days total)
|
+-- WP 3.1: Deterministic Geometric Search (15-18 days)
|   └── Killing Fields/Tensors via PDE solvers
|
+-- WP 3.2: Structure-Preserving ML Discovery (18-22 days)
|   └── Hamiltonian Neural Networks + Conservation constraints
|
+-- WP 3.3: Symbolic Regression & Consolidation (10-12 days)
    └── Convert numerical candidates -> analytical expressions
```

**Philosophy**: Cast a wide net using complementary methodologies, then consolidate and validate the most promising candidates.

---

## WP 3.1: Deterministic Geometric Search

**Duration**: 15-18 days | **Approach**: Direct PDE solution

### Core Idea

If a conserved quantity $\widetilde{I}$ exists, it must correspond to a symmetry of the lifted geometry. For the Jacobi-Maupertuis metric, symmetries are characterized by:
- **Killing vector fields** (linear integrals): nabla_(i) K_j) = 0
- **Killing tensors** (quadratic integrals): nabla_(k) K_ij) = 0

### Tasks

| Task | Description | Output |
|------|-------------|--------|
| 3.1.1 | Lifted JM metric on S^1 bundle and KS spaces | Metric implementation |
| 3.1.2 | Killing PDE formulation (vector and tensor) | PDE system |
| 3.1.3 | Numerical PDE solution (mesh + least-squares) | Numerical solutions |
| 3.1.4 | Convert fields -> integrals + triviality filter | Candidate library |

### Key Innovation

First systematic geometric search for hidden symmetries in higher-dimensional three-body embeddings.

---

## WP 3.2: Structure-Preserving ML Discovery

**Duration**: 18-22 days | **Approach**: Geometric deep learning

### Core Idea

Train neural networks that respect symplectic structure to implicitly learn conserved quantities from trajectory data.

### Architecture

**Hamiltonian Neural Networks (HNNs)** or **Symplectic Neural Networks (SympNets)**:
- Network learns lifted Hamiltonian H_tilde
- Auxiliary head predicts candidate integral I_tilde
- Loss function enforces {I, H}_omega = 0 (conservation)

### Tasks

| Task | Description | Output |
|------|-------------|--------|
| 3.2.1 | Generate training datasets on lifted spaces | Trajectory data |
| 3.2.2 | Implement HNN/SympNet architecture (JAX/PyTorch) | Network code |
| 3.2.3 | Conservation-constrained training with Noether regularizers | Training pipeline |
| 3.2.4 | Out-of-distribution validation | Generalization metrics |

### Key Innovation

First application of structure-preserving ML to hidden integral discovery in celestial mechanics.

---

## WP 3.3: Symbolic Regression & Consolidation

**Duration**: 10-12 days | **Approach**: Analytical expression discovery

### Core Idea

Convert numerically discovered candidates into concise analytical expressions.

### Pipeline

1. **Symbolic Regression Tools**: SINDy, PySR, AI-Feynman
2. **Basis Function Optimization**: Restrict to physically meaningful functions
3. **Candidate Ranking**: Filter by complexity and initial conservation tests

### Tasks

| Task | Description | Output |
|------|-------------|--------|
| 3.3.1 | Symbolic regression pipeline | Expression discovery |
| 3.3.2 | Basis function optimization | Constrained search |
| 3.3.3 | Candidate ranking and consolidation | Ranked candidate list |

### Specialized Function Bases

| Basis | Purpose | Functions |
|-------|---------|-----------|
| Spinor | KS-lifted polynomial integrals | ~80 spinor functions |
| Elliptic | Quasi-periodic integrals | Jacobi sn, cn, dn |
| Theta | Complete integrability | Theta functions theta_1-4 |

---

## Candidate Flow

```
WP 3.1 Geometric ----+
                     |
WP 3.2 ML ---------->+---> Consolidation ---> Initial Filter ---> WP4 Validation
                     |
WP 3.3 Symbolic ----+
```

### Triviality Checks

Before passing to WP4, verify candidates are NOT:
- Energy E
- Angular momentum L
- Fiber momentum p_theta
- Known classical integrals
- Linear combinations of above

---

## Documents in This Folder

### Core Documents

| File | Description |
|------|-------------|
| `WP3-Overview.md` | This document |
| `WP3-Complete-Overview.md` | Original detailed overview |
| `README.md` | Original folder readme |
| `WP3-GAP-ANALYSIS-AND-FIX-PLAN.md` | Gap analysis |
| `WP3-PHASE1-COMPLETION-REPORT.md` | Phase 1 report |
| `WP3-PHASE1-IMPLEMENTATION-ROADMAP.md` | Phase 1 roadmap |

### WP 3.1: Geometric Search

| File | Description |
|------|-------------|
| `WP3.1-Geometric-Search-Summary.md` | Summary |
| `WP3.1-IMPLEMENTATION-COMPLETE.md` | Completion status |
| `Task-3.1.1-Implementation-Plan.md` | Lifted JM metric |
| `Task-3.1.1-STATUS.md` | Status tracking |
| `Task-3.1.2-Implementation-Plan.md` | Killing PDEs |
| `Task-3.1.3-Implementation-Plan.md` | PDE solver |
| `Task-3.1.4-Implementation-Plan.md` | Integral conversion |

### WP 3.2: ML Discovery

| File | Description |
|------|-------------|
| `WP3.2-ML-Discovery-Summary.md` | Summary |
| `WP3.2-Implementation-Roadmap.md` | Roadmap |
| `Task-3.2.1-Implementation-Plan.md` | Data generation |
| `Task-3.2.2-Implementation-Plan.md` | HNN/SympNet |
| `Task-3.2.3-Implementation-Plan.md` | Constrained training |
| `Task-3.2.4-Implementation-Plan.md` | Validation |

### WP 3.3: Symbolic Regression

| File | Description |
|------|-------------|
| `WP3.3-Symbolic-Regression-Summary.md` | Summary (consolidated) |
| `WP3.3-AMENDMENT-PLAN.md` | Amendment details |
| `WP3.3-COMPLETE-IMPLEMENTATION-SUMMARY.md` | Implementation summary |
| `Task-3.3.1-Implementation-Plan.md` | Symbolic regression (consolidated) |
| `Task-3.3.2-Implementation-Plan.md` | Basis optimization (consolidated) |
| `Task-3.3.3-Implementation-Plan.md` | Consolidation (consolidated) |

---

## Dependencies

**Upstream**:
- WP1: High-precision trajectory data
- WP2: Lifted phase spaces, Hamiltonians, symplectic forms

**Downstream**:
- WP4: Receives candidate integrals for validation

---

## Success Metrics

| Metric | Requirement |
|--------|-------------|
| Candidate Quality | >1 non-trivial candidate passing initial filter |
| Coverage | All three tracks produce results |
| Conservation Error | |d I_tilde/dt| < 10^-10 numerically |
| Complexity | Analytical expressions with <20 terms |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| No non-trivial candidates | Project negative result | Characterize bounds on non-existence |
| ML overfitting | False positives | Hold-out mass ratio regimes |
| PDE solver instability | No geometric results | Multiple discretization schemes |
| Symbolic regression complexity | Uninterpretable results | Restrict basis functions |

---

**Document History**:
- v2.0 (2025-11-25): Consolidated from AMENDED documents
- v1.0 (2025-11-14): Original specification
