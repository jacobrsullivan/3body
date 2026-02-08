# Work Package 3: Discovery of Candidate Invariants ($\widetilde{I}$)
## Documentation Index and Quick Start Guide

**Version**: 1.1
**Last Updated**: 2025-11-16
**Status**: Complete Design Documentation - Ready for Implementation (WP3.3 Enhanced)

---

## Overview

Work Package 3 (WP3) represents the **discovery core** of the lift-integrability research program. This work package employs three complementary methodologies to search for hidden conserved quantities in the higher-dimensional spaces constructed in WP2.

### Core Hypothesis

While the three-body problem is provably non-integrable in the standard phase space, **lift-integrability** proposes that additional conserved quantities may exist "upstairs" in appropriately constructed higher-dimensional embeddings.

**WP3 Goal**: Discover these hidden integrals using a multi-pronged approach combining deterministic geometry, machine learning, and symbolic mathematics.

---

## Documentation Structure

```
WP3/
├── README.md (this file)
├── WP3-Complete-Overview.md          # Executive summary and architecture
│
├── WP3.1-Geometric-Search-Summary.md # Deterministic PDE methods
├── WP3.1-IMPLEMENTATION-COMPLETE.md  # WP3.1 completion status
├── Task-3.1.1-Implementation-Plan.md # Lifted JM Metric (detailed)
├── Task-3.1.2-Implementation-Plan.md # Killing PDE Formulation (detailed)
├── Task-3.1.3-Implementation-Plan.md # Numerical PDE Solution (detailed)
├── Task-3.1.4-Implementation-Plan.md # Integral Conversion & Filtering (detailed)
│
├── WP3.2-ML-Discovery-Summary.md     # Machine learning approach
├── WP3.2-Implementation-Roadmap.md   # ML implementation roadmap
├── Task-3.2.1-Implementation-Plan.md # Data Generation (detailed)
├── Task-3.2.2-Implementation-Plan.md # HNN/SympNet Architecture (detailed)
├── Task-3.2.3-Implementation-Plan.md # Conservation Training (detailed)
├── Task-3.2.4-Implementation-Plan.md # Validation & Testing (detailed)
│
├── WP3.3-Symbolic-Regression-Summary.md   # Symbolic consolidation
├── Task-3.3.1-Implementation-Plan.md # Symbolic Regression Pipeline (NEW)
├── Task-3.3.2-Implementation-Plan.md # Basis Function Optimization (NEW)
└── Task-3.3.3-Implementation-Plan.md # Candidate Ranking & Consolidation (NEW)
```

---

## Quick Start Guide

### For Researchers: Understanding the Approach

**Start Here**: [`WP3-Complete-Overview.md`](WP3-Complete-Overview.md)

This document provides:
- Mathematical framework for conserved quantity discovery
- Overview of all three discovery tracks
- Integration strategy and decision trees
- Expected outcomes and risk assessment

**Key Sections**:
1. Component Overview - Summary of WP 3.1, 3.2, 3.3
2. Mathematical Framework - Killing structures, HNNs, symbolic regression
3. Timeline and Dependencies - Critical path and parallelization

---

### For Developers: Implementation Planning

**Track 1 - Geometric Search**: [`WP3.1-Geometric-Search-Summary.md`](WP3.1-Geometric-Search-Summary.md)

**What**: Solve Killing vector/tensor PDEs on lifted manifolds
**Duration**: 15-18 days
**Key Tasks**:
- 3.1.1: Implement lifted Jacobi-Maupertuis metric
- 3.1.2: Formulate Killing PDEs
- 3.1.3: Numerical PDE solution
- 3.1.4: Convert solutions to conserved quantities

**Start With**: [`Task-3.1.1-Implementation-Plan.md`](Task-3.1.1-Implementation-Plan.md) for detailed specifications.

---

**Track 2 - Machine Learning**: [`WP3.2-ML-Discovery-Summary.md`](WP3.2-ML-Discovery-Summary.md)

**What**: Train Hamiltonian Neural Networks to learn conserved quantities
**Duration**: 18-22 days
**Key Tasks**:
- 3.2.1: Generate high-precision training data
- 3.2.2: Implement HNN/SympNet architecture
- 3.2.3: Conservation-constrained training
- 3.2.4: Out-of-distribution validation

**Requirements**: GPU (NVIDIA A100/V100), JAX/PyTorch, 64-128 GB RAM

---

**Track 3 - Symbolic Regression**: [`WP3.3-Symbolic-Regression-Summary.md`](WP3.3-Symbolic-Regression-Summary.md)

**What**: Convert numerical candidates to analytical expressions
**Duration**: 10-12 days
**Key Tasks**:
- 3.3.1: Implement SINDy and PySR pipelines ([Task-3.3.1-Implementation-Plan.md](Task-3.3.1-Implementation-Plan.md))
- 3.3.2: Optimize physics-informed basis functions ([Task-3.3.2-Implementation-Plan.md](Task-3.3.2-Implementation-Plan.md))
- 3.3.3: Consolidate and rank all candidates ([Task-3.3.3-Implementation-Plan.md](Task-3.3.3-Implementation-Plan.md))

**Dependencies**: Requires outputs from WP 3.1 and/or 3.2

**Start With**: [`Task-3.3.1-Implementation-Plan.md`](Task-3.3.1-Implementation-Plan.md) for symbolic regression pipeline.

---

## Three-Track Methodology

### Why Three Approaches?

**Complementary Strengths**:

| Approach | Best For | Limitations |
|----------|----------|-------------|
| **WP 3.1: Geometric** | Simple polynomial integrals, low degree | Computationally expensive, high-dimensional PDEs |
| **WP 3.2: ML** | Complex non-polynomial forms, pattern discovery | Requires large datasets, risk of overfitting |
| **WP 3.3: Symbolic** | Converting numerical → analytical | Requires input from 3.1 or 3.2 |

**Synergies**:
- WP 3.1 results inform WP 3.2 architecture (use Killing fields as priors)
- WP 3.2 discoveries guide WP 3.3 basis function selection
- WP 3.3 validates both WP 3.1 and 3.2 results

---

## Execution Strategy

### Phase 1: Parallel Launch (Weeks 1-2)

**Simultaneously**:
- WP 3.1.1: Implement lifted metrics
- WP 3.2.1: Generate training datasets
- WP 3.3.1: Set up symbolic regression infrastructure

**Why Parallel**: Each track has independent initialization phases.

---

### Phase 2: Core Discovery (Weeks 3-5)

**WP 3.1**: Solve Killing PDEs (Tasks 3.1.2-3.1.3)
**WP 3.2**: Train HNNs (Tasks 3.2.2-3.2.3)
**WP 3.3**: Begin processing early WP 3.1 results

**Checkpoints**:
- Week 3: WP 3.1 first results available → feed into WP 3.3
- Week 4: WP 3.2 training converged → extract numerical integrals
- Week 5: Both tracks producing candidates

---

### Phase 3: Consolidation (Week 6)

**WP 3.3 Dominates**: Consolidate all candidates
- Symbolic regression on all numerical results
- Rank by conservation accuracy + simplicity
- Filter duplicates and trivial combinations
- Produce final ranked list of top 10 candidates

**Output**: Handoff to WP4 for rigorous validation

---

## Expected Outcomes

### Scenario 1: Non-Trivial Integrals Discovered (Target Case)

**Indicators**:
- Conservation error $< 10^{-6}$ on test trajectories
- Functionally independent of $E, L, p_\theta$
- Generalizes across parameter space

**Action**:
- Extract symbolic expressions (WP 3.3)
- Proceed to WP4 for Poisson bracket validation
- Prepare for publication

---

### Scenario 2: Partial or Regime-Specific Integrals

**Indicators**:
- Conservation holds only in certain regimes (e.g., low energy)
- Or: approximate integral with small drift ($10^{-4}$ to $10^{-6}$)

**Action**:
- Characterize boundary of validity
- Document as "near-integrability" or adiabatic invariant
- Still scientifically valuable

---

### Scenario 3: No Non-Trivial Integrals Found (Negative Result)

**Indicators**:
- WP 3.1 finds no Killing fields (up to degree N)
- WP 3.2 fails to learn conserved quantities
- All candidates are trivial or dependent

**Action**:
- Document rigorous negative result
- Establish bounds: "No polynomial integrals up to degree 4"
- Proceed to WP4 for Morales-Ramis confirmation
- Still publishable (negative results are valuable!)

---

## Decision Tree

### After WP 3.1 (Geometric Search)

```
Killing fields found?
├─ YES → Priority: Validate in WP 3.3, use as ML priors
├─ PARTIAL → Continue ML, document geometric bounds
└─ NO → Rely on WP 3.2, increase ML search scope
```

### After WP 3.2 (Machine Learning)

```
Conserved quantities learned?
├─ YES (error < 10⁻⁶) → Extract numerical form, symbolic regression
├─ PARTIAL (error 10⁻⁴ to 10⁻⁶) → Check regime-specificity
└─ NO → Document negative result, proceed with WP 3.1 only
```

### After WP 3.3 (Symbolic Regression)

```
Symbolic form found?
├─ YES (residual < 10⁻¹⁰) → Ready for WP4 analytical validation
├─ APPROXIMATE → Use for numerical WP4 validation
└─ NO → Proceed to WP4 with numerical candidates
```

---

## Key Deliverables

### Scientific Outputs

1. **Candidate Conserved Quantities** (if found):
   - Analytical expressions
   - Numerical accuracy: conservation error, independence tests
   - Domain of validity (parameter space coverage)

2. **Rigorous Negative Results** (if no integrals):
   - Degree bounds (e.g., "no polynomial integrals up to degree N")
   - Search space coverage documentation
   - Ruling out specific symmetry types

3. **Methodology Contributions**:
   - First application of HNNs to celestial mechanics integral discovery
   - Physics-informed symbolic regression for geometric systems
   - Benchmark datasets and code for future research

---

### Code Deliverables

**Total**: ~25-30 new Python modules across three tracks

**WP 3.1**: ~10 modules (geometry, PDEs, solvers)
**WP 3.2**: ~10 modules (ML, data generation, training)
**WP 3.3**: ~5 modules (symbolic regression, ranking)

**Languages**: Python (primary), JAX (ML), SymPy (symbolic)
**Dependencies**: NumPy, SciPy, PyTorch/JAX, PySINDy, PySR

---

### Documentation Deliverables

**Technical Reports** (3 documents, ~50 pages total):
1. "Geometric Search for Hidden Symmetries" (WP 3.1)
2. "Machine Learning Discovery of Conserved Quantities" (WP 3.2)
3. "Symbolic Regression and Candidate Consolidation" (WP 3.3)

**Tutorial Notebooks** (3-5 notebooks):
- Killing field computation on simple manifolds
- Training HNNs for conservation laws
- Symbolic regression workflow

**API Documentation**: Sphinx-generated, all public functions documented

---

## Success Metrics

### Minimum Success Criteria (Must Achieve)

- [ ] All three tracks implemented and tested
- [ ] Search completed to specified resolution/degree
- [ ] Validation framework in place (conservation tests, independence)
- [ ] Results (positive or negative) documented
- [ ] Code passes CI/CD and review

---

### Target Success Criteria (Expected)

- [ ] At least one non-trivial candidate discovered
- [ ] Conservation verified: $|\Delta I| / |I| < 10^{-5}$
- [ ] Functional independence confirmed (Jacobian rank test)
- [ ] Symbolic expression obtained (complexity ≤ 20 operations)
- [ ] Handoff to WP4 with analytical candidates

---

### Stretch Success Criteria (Best Case)

- [ ] Multiple independent integrals found
- [ ] Simple analytical forms (polynomial, low degree)
- [ ] Clear physical interpretation (geometric symmetry)
- [ ] Universal across parameter space
- [ ] Publication-ready figures and results

---

## Timeline Summary

| Phase | Duration | Tasks | Parallelizable? |
|-------|----------|-------|-----------------|
| **Phase 1: Setup** | Week 1-2 | 3.1.1, 3.2.1, 3.3.1 | Yes (all 3 tracks) |
| **Phase 2: Discovery** | Week 3-5 | 3.1.2-3.1.4, 3.2.2-3.2.4 | Yes (WP 3.1 ∥ WP 3.2) |
| **Phase 3: Consolidation** | Week 6 | 3.3.2-3.3.3 | No (requires inputs) |

**Total Calendar Time**: 6 weeks (35-45 days with efficient parallelization)

**Critical Path**: WP 3.1 (15-18 days) ∥ WP 3.2 (18-22 days) → WP 3.3 (10-12 days)

---

## Computational Resources

### Hardware Requirements

**WP 3.1 (Geometric)**:
- CPU: 16+ cores
- RAM: 64 GB
- Storage: ~10 GB
- Runtime: 10-50 hours (PDE solvers)

**WP 3.2 (ML)**:
- GPU: NVIDIA A100 or V100 (16-40 GB VRAM)
- RAM: 128 GB
- Storage: ~100 GB (datasets + models)
- Runtime: 2-4 days (training)

**WP 3.3 (Symbolic)**:
- CPU: 16+ cores
- RAM: 32-64 GB
- Storage: ~1 GB
- Runtime: Hours to days (PySR)

---

## Prerequisites

### From WP2 (Required Inputs)

- [ ] S¹ bundle construction (WP 2.2)
- [ ] KS-Spinor lift (WP 2.3)
- [ ] High-precision integrators (WP 1)
- [ ] Connection form $A(s)$ (WP 2.1.2)
- [ ] Shape space JM metric (WP 2.1.3)

### Software Dependencies

**Python Packages**:
- Core: NumPy, SciPy, SymPy
- ML: JAX/Flax or PyTorch
- Symbolic: PySINDy, PySR
- Utilities: h5py, matplotlib, pandas

**Installation**:
```bash
conda activate wp1_env
pip install jax jaxlib flax pysindy pysr
```

---

## Risk Assessment

### Scientific Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No integrals exist (even upstairs) | Medium (30%) | High | Document negative result |
| Integrals too complex to discover | Medium (25%) | Medium | Multi-method approach |
| Numerical instabilities | Low (15%) | Medium | High-precision arithmetic |

### Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PDE solver non-convergence | Medium (30%) | Low | Mesh refinement, regularization |
| ML overfitting | Medium-High (40%) | Low | OOD validation, physics constraints |
| Symbolic regression timeout | Low (20%) | Low | Hierarchical basis, SINDy fallback |

---

## Integration with Other Work Packages

### Inputs from Earlier Phases

- **WP1**: High-precision integrators, validation harness
- **WP2.1**: Shape space coordinates, JM metric, connection
- **WP2.2**: S¹ bundle dynamics
- **WP2.3**: KS-Spinor coordinates

### Outputs to Later Phases

- **WP4.1**: Symbolic expressions for Poisson bracket tests
- **WP4.2**: Confirmation of downstairs non-integrability (if no integrals found)
- **WP4.3**: Candidate integrals for Monte Carlo validation
- **WP5**: Final results (positive or negative) for publication

---

## References

### Comprehensive Bibliography

See individual summary documents for detailed references:
- [`WP3.1-Geometric-Search-Summary.md`](WP3.1-Geometric-Search-Summary.md#references): Killing tensors, geometric methods
- [`WP3.2-ML-Discovery-Summary.md`](WP3.2-ML-Discovery-Summary.md#references): HNNs, physics-informed ML
- [`WP3.3-Symbolic-Regression-Summary.md`](WP3.3-Symbolic-Regression-Summary.md#references): SINDy, PySR, AI-Feynman

**Key Foundational Papers**:
1. Greydanus et al., "Hamiltonian Neural Networks" (2019)
2. Brunton et al., "Discovering governing equations from data by sparse identification" (2016)
3. Benenti, "Intrinsic characterization of variable separation in Hamilton-Jacobi equation" (2002)

---

## Getting Help

### Documentation Questions

- **Architecture and Strategy**: See [`WP3-Complete-Overview.md`](WP3-Complete-Overview.md)
- **Task-Specific Details**: See individual implementation plans
- **Mathematical Background**: See technical reports (to be generated)

### Implementation Support

- **Code Examples**: Check `notebooks/` directory (tutorials)
- **API Reference**: Build with `make docs` (Sphinx)
- **Testing**: Run `pytest tests/wp3/` for validation

---

## Version History

- **v1.1** (2025-11-16): WP3.3 Complete Documentation
  - Added Task-3.3.1-Implementation-Plan.md (Symbolic Regression Pipeline)
  - Added Task-3.3.2-Implementation-Plan.md (Basis Function Optimization)
  - Added Task-3.3.3-Implementation-Plan.md (Candidate Ranking & Consolidation)
  - WP3.3 now has complete task-level documentation matching WP3.1/3.2
  - Total: 3 new detailed implementation plans (~5,600 lines)

- **v1.0** (2025-11-14): Initial complete documentation release
  - All three track summaries complete
  - Detailed implementation plans for critical path tasks
  - Integration strategy and decision trees finalized

---

## Contact and Contributions

**Status**: This documentation is complete and ready for implementation.

**Next Steps**:
1. Review all documents for technical accuracy
2. Begin implementation starting with WP 3.1.1 or 3.2.1 (parallel tracks)
3. Use decision trees to adapt strategy based on early results

---

**Document Status**: ✅ Complete Design Documentation
**Implementation Status**: ⏳ Ready to Begin
**Total Documentation**: ~15,000 lines across 7+ comprehensive documents
**Last Updated**: 2025-11-14
