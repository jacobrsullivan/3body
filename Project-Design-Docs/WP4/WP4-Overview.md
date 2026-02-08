# Work Package 4: Rigorous Validation ("The Gauntlet")

**Three-Stage Validation Pipeline for Candidate Integrals**

**Status**: Design Phase
**Last Updated**: 2025-11-25
**Prerequisites**: WP3 Complete (candidate integrals)
**Next Phase**: WP5 (Publication)

---

## Executive Summary

WP4 subjects candidate integrals $\widetilde{I}$ from WP3 to stringent analytical and numerical tests designed to meet Liouville integrability criteria and compatibility with known obstructions. This is the "validation gauntlet" - only candidates passing all stages are considered genuine.

---

## Three-Stage Validation Pipeline

```
WP4: Validation Gauntlet (28-36 days total)
|
+-- WP 4.1: Analytical Vetting (8-10 days)
|   └── Poisson brackets, independence, involution
|
+-- WP 4.2: Complete Morales-Ramis Test (10-14 days)
|   ├── Phase I: Downstairs non-abelian (defensive)
|   └── Phase II: Upstairs abelian (validation) <- CRITICAL
|
+-- WP 4.3: Numerical Robustness (10-12 days)
    └── Monte Carlo, stress testing, chaos correlation
```

---

## WP 4.1: Analytical Vetting (The Liouville Criteria)

**Duration**: 8-10 days | **Approach**: Symbolic verification

### Objective

Symbolically verify core requirements of integrability: Conservation, Independence, and Involution.

### Tasks

| Task | Test | Acceptance Threshold |
|------|------|---------------------|
| 4.1.1 | Conservation: {I_tilde, H_tilde}_omega = 0 | Symbolically zero OR residual < 10^-12 |
| 4.1.2 | Involution: {I_tilde, L_i} = 0 | Must commute with all classical integrals |
| 4.1.3 | Independence: Jacobian rank test | Rank increases on >99% of sampled states |

### Kill Switch A

If $\widetilde{I}$ fails Poisson bracket tests OR is functionally dependent on known quantities OR trivial fiber momentum -> **DISCARD CANDIDATE**

### Deliverable

Symbolic proof (or refutation) of Liouville criteria for each candidate.

---

## WP 4.2: Complete Morales-Ramis Test (CRITICAL)

**Duration**: 10-14 days | **Approach**: Differential Galois theory

### Objective

Validate lift-integrability hypothesis by proving BOTH:
1. System is non-integrable downstairs (defensive falsification)
2. Lifted system has abelian Galois structure upstairs (compatibility test)

### Phase I: Downstairs Non-Integrability

| Task | Description |
|------|-------------|
| 4.2.1 | Setup Normal Variational Equations (NVE) along periodic solutions (Lagrange, Collinear) in original coordinates |
| 4.2.2 | Apply Kovacic algorithm to downstairs NVE |
| 4.2.3 | Verify identity component is **non-abelian** |

**Validation**: Confirms non-integrability downstairs, proves consistency with Bruns/Poincare.

### Phase II: Upstairs Compatibility Test (CRITICAL AMENDMENT)

| Task | Description |
|------|-------------|
| 4.2.4 | Lift periodic solutions to extended phase space (S^1 or KS) |
| 4.2.5 | Apply Kovacic algorithm to **upstairs** NVE |
| 4.2.6 | Determine if identity component is **abelian** upstairs |

### Compatibility Test Matrix

| Upstairs Galois | WP3 Found Integrals | Interpretation |
|-----------------|---------------------|----------------|
| Abelian | Yes | **LIFT-INTEGRABILITY CONFIRMED** |
| Non-abelian | Yes | WP3 integrals spurious |
| Abelian | No | Integrals exist but missed |
| Non-abelian | No | Negative result confirmed |

### Why Phase II is Critical

**Without Phase II** (original plan):
- Confirms 3BP non-integrable downstairs
- Does NOT validate upstairs integrals are genuine
- Cannot distinguish lift-integrals from numerical artifacts

**With Phase II** (amended plan):
- Tests whether upstairs Galois group is abelian
- Validates or refutes WP3 discoveries
- Provides complete compatibility test
- Meets publication standards

### Deliverables

- **Phase I**: Formal proof of downstairs non-integrability
- **Phase II**: Formal analysis of upstairs Galois structure
- **Complete Report**: Validation or refutation of lift-integrability

---

## WP 4.3: Numerical Robustness and Generalization

**Duration**: 10-12 days | **Approach**: Statistical validation

### Objective

Validate universality and stability of $\widetilde{I}$ across entire parameter space.

### Tasks

| Task | Description | Requirement |
|------|-------------|-------------|
| 4.3.1 | Monte Carlo suite (>= 10^5 ICs) | Full parameter space coverage |
| 4.3.2 | Stress testing (collisions, high-e, chaos) | Robust regularization |
| 4.3.3 | Long-time invariance analysis | Drift <= C * epsilon_H(T), C ~ 10 |
| 4.3.4 | Chaos correlation | I_tilde conserved in chaotic regions |

### Acceptance Threshold

$$\sup_{t \le T} \frac{|\Delta \widetilde{I}(t)|}{\max(1, |\widetilde{I}(0)|)} \le C \cdot \epsilon_H(T)$$

Drift in $\widetilde{I}$ must not exceed integrator error.

### Deliverable

Comprehensive statistical validation report confirming universality and robustness.

---

## Documents in This Folder

### Core Documents

| File | Description |
|------|-------------|
| `WP4-Overview.md` | This document |
| `WP4-Complete-Overview.md` | Detailed overview (consolidated) |
| `README.md` | Original folder readme |
| `WP4-GAP-FIX-PLAN.md` | Gap analysis and fixes |
| `COMPLETE-IMPLEMENTATION-REPORT.md` | Implementation report |

### Implementation Plans

| File | Description |
|------|-------------|
| `WP4.1-Analytical-Vetting-Implementation-Plan.md` | Analytical vetting details |
| `WP4.2-Morales-Ramis-Implementation-Plan.md` | Morales-Ramis (consolidated) |
| `WP4.3-Numerical-Robustness-Implementation-Plan.md` | Numerical robustness details |

### Status Documents

| File | Description |
|------|-------------|
| `IMPLEMENTATION-STATUS-2025-11-20.md` | Status 20 Nov |
| `IMPLEMENTATION-STATUS-2025-11-21.md` | Status 21 Nov |
| `PHASE3-IMPLEMENTATION-REPORT.md` | Phase 3 report |
| `WP4-Implementation-Assessment-2025-11-20.md` | Assessment |

---

## Dependencies

**Upstream**:
- WP2: Lifted Hamiltonians for upstairs NVE
- WP3: Candidate integrals to validate

**Downstream**:
- WP5: Validated integrals for publication

---

## Computational Requirements

### WP 4.2 Phase II Dependencies

From WP2:
- Extended Hamiltonians H_tilde (preferably symbolic/SymPy)
- Extended symplectic forms omega_tilde
- Connection one-form A

### Computational Approaches

1. **Symbolic (preferred)**: Derive nabla^2 H_tilde symbolically -> NVE -> Kovacic
2. **Numerical->Symbolic (fallback)**: Evaluate NVE numerically, fit to rational form
3. **Hybrid**: Symbolic regression (PySR) to discover form, validate against numerical

---

## Success Criteria

| Stage | Criterion |
|-------|-----------|
| 4.1 | Poisson brackets symbolically zero |
| 4.2 Phase I | Downstairs Galois non-abelian |
| 4.2 Phase II | Upstairs Galois abelian |
| 4.3 | Statistical validation passes |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Symbolic computation intractable | No analytical proof | Numerical verification fallback |
| Upstairs NVE too complex | Phase II fails | Hybrid approach |
| Numerical artifacts | False positives | Shadow Hamiltonian analysis |
| All candidates fail | No positive result | Characterize bounds |

---

**Document History**:
- v2.0 (2025-11-25): Consolidated from AMENDED documents, includes Phase II
- v1.0 (2025-11-17): Original specification (Phase I only)
