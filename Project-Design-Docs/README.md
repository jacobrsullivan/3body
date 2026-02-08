# Project Design Documentation

**Three-Body Problem Lift-Integrability Investigation**

This folder contains all design documents for the 3-body project, organized by work package.

---

## Quick Navigation

| Work Package | Status | Description |
|--------------|--------|-------------|
| [OVERVIEW](./OVERVIEW/) | Active | Project overview and theoretical framework |
| [WP1](./WP1/) | Complete | High-precision trajectory generation |
| [WP2](./WP2/) | Implementation | Geometric foundations and lift construction |
| [WP3](./WP3/) | Design | Invariant discovery methods |
| [WP4](./WP4/) | Design | Rigorous validation ("The Gauntlet") |
| [WP5](./WP5/) | Planning | Publication and reproducibility |
| [Implementation-Status](./Implementation-Status/) | Active | Progress tracking |

---

## Project Summary

**Hypothesis**: The chaotic dynamics of the three-body problem are an artifact of dimensional reduction. Hidden conserved quantities may exist in appropriately constructed higher-dimensional "upstairs" spaces.

**Objective**: Find the sixth independent integral $\widetilde{I}$ that would render the system Liouville integrable in the lifted space.

**Two Lift Approaches**:
1. **S^1 Minimal Lift** (WP 2.2): Geometric untwisting via cohomological fix
2. **KS-Spinor Lift** (WP 2.3): Maximal symmetry via Kustaanheimo-Stiefel regularization

---

## Folder Structure

### `/OVERVIEW/` - Project Overview

High-level overview documents and theoretical framework.

| Document | Description |
|----------|-------------|
| [Project-Overview.md](./OVERVIEW/Project-Overview.md) | **START HERE** - Consolidated project overview |
| [KS-Conjectural-Statement.md](./OVERVIEW/KS-Conjectural-Statement.md) | Theoretical framework for KS symplectic reduction |
| [Compute-Requirements-Analysis.md](./OVERVIEW/Compute-Requirements-Analysis.md) | Computational resource requirements |

### `/WP1/` - High-Precision Trajectory Generation

**Status**: Complete | **Duration**: Weeks 0-14

Generate validated CR3BP trajectory catalogue with unprecedented precision.

| Document | Description |
|----------|-------------|
| [WP1-Overview.md](./WP1/WP1-Overview.md) | Work package overview |
| [WP1-High-Fidelity-CR3BP-Trajectory-Catalogue.md](./WP1/WP1-High-Fidelity-CR3BP-Trajectory-Catalogue.md) | Detailed specification |
| [WP1-Implementation-Complete-22ndNov2025.md](./WP1/WP1-Implementation-Complete-22ndNov2025.md) | Completion report |
| [WP1-Gap-Fixing-Plan-22ndNov2025.md](./WP1/WP1-Gap-Fixing-Plan-22ndNov2025.md) | Gap analysis |
| `WP1-Phase-1/` | Phase 1 plans (environment setup) |
| `WP1-Phase-2/` | Phase 2 plans (integrator selection) |

### `/WP2/` - Geometric Foundations and Lift Construction

**Status**: Implementation | **Prerequisites**: WP1

Establish mathematical framework and implement two lift constructions.

| Document | Description |
|----------|-------------|
| [WP2-Overview.md](./WP2/WP2-Overview.md) | Work package overview |
| [WP2-Complete-Summary-and-Handoff.md](./WP2/WP2-Complete-Summary-and-Handoff.md) | Summary and handoff |
| Task-2.1.x files | Geometric reduction (coordinates, connection, metric) |
| WP2.2-* files | S^1 lift implementation |
| WP2.3-* files | KS-Spinor lift implementation |
| [PLAN-WP2-Gap-Fixes.md](./WP2/PLAN-WP2-Gap-Fixes.md) | Gap analysis |
| [IMPLEMENTATION_SUMMARY_RATTLE.md](./WP2/IMPLEMENTATION_SUMMARY_RATTLE.md) | RATTLE integrator summary |

### `/WP3/` - Discovery of Candidate Invariants

**Status**: Design | **Prerequisites**: WP2

Three-track search for hidden integrals.

| Document | Description |
|----------|-------------|
| [WP3-Overview.md](./WP3/WP3-Overview.md) | Work package overview |
| [WP3-Complete-Overview.md](./WP3/WP3-Complete-Overview.md) | Detailed overview |
| WP3.1-* files | Geometric search (Killing fields/tensors) |
| WP3.2-* files | ML discovery (HNN/SympNet) |
| WP3.3-* files | Symbolic regression |
| Task-3.x.x files | Individual task plans |
| [WP3-GAP-ANALYSIS-AND-FIX-PLAN.md](./WP3/WP3-GAP-ANALYSIS-AND-FIX-PLAN.md) | Gap analysis |

### `/WP4/` - Rigorous Validation

**Status**: Design | **Prerequisites**: WP3

Three-stage validation pipeline ("The Gauntlet").

| Document | Description |
|----------|-------------|
| [WP4-Overview.md](./WP4/WP4-Overview.md) | Work package overview |
| [WP4-Complete-Overview.md](./WP4/WP4-Complete-Overview.md) | Detailed overview |
| [WP4.1-Analytical-Vetting-Implementation-Plan.md](./WP4/WP4.1-Analytical-Vetting-Implementation-Plan.md) | Poisson brackets, independence |
| [WP4.2-Morales-Ramis-Implementation-Plan.md](./WP4/WP4.2-Morales-Ramis-Implementation-Plan.md) | Complete Morales-Ramis (downstairs + upstairs) |
| [WP4.3-Numerical-Robustness-Implementation-Plan.md](./WP4/WP4.3-Numerical-Robustness-Implementation-Plan.md) | Monte Carlo, stress testing |
| [WP4-GAP-FIX-PLAN.md](./WP4/WP4-GAP-FIX-PLAN.md) | Gap analysis |

### `/WP5/` - Consolidation and Publication

**Status**: Planning | **Prerequisites**: WP4

Final consolidation and publication preparation.

| Document | Description |
|----------|-------------|
| [WP5-Overview.md](./WP5/WP5-Overview.md) | Work package overview |
| [WP5-Complete-Overview.md](./WP5/WP5-Complete-Overview.md) | Detailed overview |
| [WP5.1-Formal-Proof-Construction-Implementation-Plan.md](./WP5/WP5.1-Formal-Proof-Construction-Implementation-Plan.md) | Proof construction |
| [WP5.2-Reproducibility-Package-Implementation-Plan.md](./WP5/WP5.2-Reproducibility-Package-Implementation-Plan.md) | Reproducibility |
| [WP5.3-Publication-Preparation-Implementation-Plan.md](./WP5/WP5.3-Publication-Preparation-Implementation-Plan.md) | Manuscript preparation |
| [WP5-GAPS-FIX-PLAN.md](./WP5/WP5-GAPS-FIX-PLAN.md) | Gap analysis |

### `/Implementation-Status/` - Progress Tracking

Current implementation status and tracking documents.

| Document | Description |
|----------|-------------|
| Implementation-WP1-22ndNov2025.md | WP1 status |
| Implementation-WP2-22ndNov2025.md | WP2 status |
| Implementation-WP3-22ndNov2025.md | WP3 status |
| Implementation-WP4-22ndNov2025.md | WP4 status |
| Implementation-WP5-22ndNov2025.md | WP5 status |
| `archive/` | Historical status documents |

### `/_archive_25Nov2025/` - Archive

Previous version of all documents before 25 Nov 2025 reorganization. Preserved for reference.

---

## Document Naming Conventions

| Pattern | Meaning |
|---------|---------|
| `WPX-Overview.md` | Work package X consolidated overview |
| `WPX.Y-*.md` | Sub-work-package documents |
| `Task-X.Y.Z-*.md` | Specific task implementation plans |
| `*-Gap-*.md` | Gap analysis and fix plans |
| `*-Implementation-*.md` | Implementation status/reports |

**Note**: Previous `AMENDED_` prefixed files have been consolidated into their base documents. Original versions are preserved in the archive.

---

## Reading Guide

### For Project Overview
1. Start with [OVERVIEW/Project-Overview.md](./OVERVIEW/Project-Overview.md)
2. Review theoretical framework in [KS-Conjectural-Statement.md](./OVERVIEW/KS-Conjectural-Statement.md)

### For Implementation Details
1. Read the `WPX-Overview.md` for the relevant work package
2. Dive into specific task plans as needed

### For Current Status
1. Check `Implementation-Status/` for latest progress
2. Review gap analysis documents in each WP folder

---

## Dependencies Between Work Packages

```
WP1 (Trajectories) --> WP2 (Geometry) --> WP3 (Discovery) --> WP4 (Validation) --> WP5 (Publication)
                   \                   \                   /
                    \                   +---- WP3 uses ---+
                     +-------- WP4 uses Tier 2 data ------+
```

---

## Key Theoretical Concepts

| Concept | Location | Description |
|---------|----------|-------------|
| Lift-Integrability | OVERVIEW | Central hypothesis |
| S^1 Untwisting | WP2.2 | Minimal cohomological lift |
| KS-Spinor Lift | WP2.3 | Maximal symmetry lift |
| Time Regularization | WP2.3 | Sundman transformation |
| Morales-Ramis Test | WP4.2 | Differential Galois obstruction |
| Validation Gauntlet | WP4 | Three-stage validation pipeline |

---

**Last Updated**: 2025-11-25
**Maintained By**: Project Team
