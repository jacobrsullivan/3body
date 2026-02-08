# Work Package 1: High-Precision Trajectory Generation

**High-Fidelity CR3BP Trajectory Catalogue**

**Status**: Complete
**Last Updated**: 2025-11-25
**Duration**: Weeks 0-14

---

## Executive Summary

WP1 generates and validates a high-precision trajectory catalogue for the Circular Restricted Three-Body Problem (CR3BP), designed to enable Machine Learning and symbolic regression searches for hidden integrals of motion. This dataset meets unprecedented precision standards to distinguish novel invariants from numerical artifacts.

---

## Objectives

1. **Parameter Space Coverage**: Span mass ratios 10^-3 <= mu <= 0.5 and comprehensive Jacobi constants
2. **Stratified Precision**: Dual-tier strategy with "gold standard" subset (|Delta C/C| < 10^-25)
3. **Rich Data Format**: Full phase-space vectors in multiple coordinate systems with chaos indicators
4. **ML Readiness**: High-throughput formats (Parquet) with fully reproducible codebase

---

## Two-Tier Precision Strategy

| Tier | Orbits | Precision | Target Error | Purpose |
|------|--------|-----------|--------------|---------|
| **Tier 1** | 10^5 | Double | |Delta C/C| < 10^-14 | Exploration, initial ML training |
| **Tier 2** | 10^4 | Double-Double | |Delta C/C| < 10^-25 | Rigorous validation of candidates |

---

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **High Precision** | QD Library (Double-Double, ~31 digits) | Achieve 10^-25 error target |
| **Symplectic Integration** | Adaptive Symplectic + IAS15 baseline | Long-term stability |
| **Regularization** | Levi-Civita / Sundman | Handle close encounters |
| **Chaos Indicators** | MEGNO + FLI | Classify regular vs. chaotic motion |
| **Data Format** | HDF5 (archival) + Parquet (ML-ready) | High-throughput I/O |

---

## Implementation Phases

### Phase 1: Environment Setup (Weeks 0-1)
- Python 3.11+ orchestration, C++/Fortran kernels
- Double-Double arithmetic via QD library
- Smoke tests: Kepler ellipse, |Delta E/E| < 10^-28

### Phase 2: Integrator Selection (Weeks 2-4)
- Evaluate adaptive symplectic, IAS15, high-order composition
- Establish precision budget and regularization strategy

### Phase 3: Parameter Space Design (Weeks 5-6)
- 30 mass ratio samples (log-uniform)
- 15 Jacobi constant values
- Sobol sequence sampling with dynamically informed refinement

### Phase 4: Production Integration (Weeks 7-10)
- Snakemake/Dask orchestration on HPC
- Simultaneous integration of state + variational equations
- Multi-coordinate output (co-rotating, inertial, regularized)

### Phase 5: Quality Assurance (Weeks 11-12)
- Precision histogram verification
- Shadow Hamiltonian analysis
- Time reversibility tests (RMS error < 10^-20)

### Phase 6: Release (Weeks 13-14)
- Post-process to Parquet format
- DOI via Zenodo
- Documentation and data descriptor

---

## Deliverables

1. **Trajectory Catalogue**: HDF5 + Parquet files with full phase-space data
2. **Integration Suite**: Validated symplectic integrators with QD support
3. **Chaos Maps**: MEGNO/FLI indicators for all orbits
4. **Reproducibility Package**: Complete codebase with environment locks

---

## Success Criteria

| Criterion | Requirement |
|-----------|-------------|
| Precision (Tier 1) | Median |Delta C/C| < 10^-14 |
| Precision (Tier 2) | 95th percentile < 10^-25 |
| Shadow Hamiltonian | Bounded error for chaotic orbits |
| Reproducibility | Bit-for-bit regeneration of 1% subset |

---

## Documents in This Folder

### Core Documents

| File | Description |
|------|-------------|
| `WP1-Overview.md` | This document |
| `WP1-High-Fidelity-CR3BP-Trajectory-Catalogue.md` | Detailed specification |
| `WP1-Implementation-Complete-22ndNov2025.md` | Completion report |
| `WP1-Gap-Fixing-Plan-22ndNov2025.md` | Gap analysis and fixes |

### Phase-Specific Plans

#### Phase 1 (`WP1-Phase-1/`)

| File | Description |
|------|-------------|
| `Week-0-1-Environment-Setup.md` | Environment and precision setup |
| `Day-1-Implementation-Plan.md` | Day 1 detailed plan |
| `Day-4-Implementation-Plan.md` | Day 4 detailed plan |
| `Day-5-Implementation-Plan.md` | Day 5 detailed plan |
| `WP1-Phase-1-TechnicalReadme.md` | Technical documentation |

#### Phase 2 (`WP1-Phase-2/`)

| File | Description |
|------|-------------|
| `Week-2-4-Integrator-Shootout.md` | Integrator selection plan |
| `WK2-DeepDive.md` | Week 2 details |
| `WK3-DeepDive.md` | Week 3 details |
| `WK4-DeepDive.md` | Week 4 details |
| `WP1-Phase2-Day6.md` | Day 6 plan |
| `WP1-Phase2-Day7.md` | Day 7 plan |
| `WP1-Phase2-Day7-Plan.md` | Day 7 detailed plan |

---

## Dependencies

**Upstream**: None (WP1 is the foundation)

**Downstream**:
- WP2: Uses trajectory data for geometric analysis
- WP3: Uses trajectory data for ML training and symbolic regression
- WP4: Uses Tier 2 data for validation

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| High-precision overhead | Runtime blowup | Stratified approach guarantees Tier 1 |
| Adaptive symplectic complexity | Delay | Fallback to IAS15 |
| Regularization switching errors | Precision loss | Smooth switching + rigorous QA |
| I/O bottlenecks | Slow ML training | Parquet format delivery |

---

**Document History**:
- v2.0 (2025-11-25): Consolidated overview
- v1.0 (2025-11-06): Original specification
