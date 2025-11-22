# AMENDED Updated Plan: A Systematic Search for Hidden Integrability in the Newtonian Three-Body Problem via Higher-Dimensional Symplectic Embedding

**AMENDMENT DATE**: 2025-11-20
**AMENDMENT SCOPE**: Work Package 4.2 - Complete Morales-Ramis Test
**AMENDMENT REASON**: Critical discrepancy identified between theoretical framework and implementation plan

---

## Amendment Summary

### Critical Update to WP 4.2

**Original WP 4.2** (Defensive Falsification):
- Only tested variational equations **downstairs**
- Only confirmed non-integrability in original coordinates
- **Missing**: Analysis of variational equations **upstairs** in lifted space

**Amended WP 4.2** (Complete Morales-Ramis Test):
- **PHASE I**: Test variational equations downstairs (non-abelian → non-integrable)
- **PHASE II**: Test variational equations upstairs (abelian → compatible with integrability) **← NEW**
- Provides complete compatibility test for lift-integrability hypothesis

### Theoretical Justification

From "Abelianizing Variational Equations in the Three-Body Problem":

> "The aim is to find a transformation such that the NVE upstairs has an abelian Galois group, even though downstairs it was non-abelian."

The **complete** Morales-Ramis test for lift-integrability requires **both**:
1. Downstairs non-abelian (proves classical obstruction)
2. **Upstairs abelian (validates lift-integrability)** ← **This was missing**

---

This document outlines the revised working plan for the project: "A Systematic Search for Hidden Integrability in the Newtonian Three-Body Problem via Higher-Dimensional Symplectic Embedding."

This plan integrates critical expert feedback, pivoting the core strategy towards **lift-integrability**. The goal is to find a new conserved quantity ($\\widetilde{I}$) in a minimal higher-dimensional symplectic extension ("upstairs"), whose projection reproduces the standard three-body dynamics ("downstairs"). This approach circumvents classical obstructions (e.g., Bruns, Poincaré).

Work Package 1 (WP1: High-Precision Symplectic Integration Suite and R3BP Data Generation) is complete. The following plan details the subsequent phases, designed for developers to create detailed weekly implementation plans.

---

### **WP 2: Geometric Foundations and Lift Construction**

*[Content unchanged from original plan - see original document lines 9-56]*

---

### **WP 3: Discovery of Candidate Invariants ($\\widetilde{I}$)**

*[Content unchanged from original plan - see original document lines 57-111]*

---

### **WP 4: Rigorous Validation and Falsification (The "Gauntlet")**

This critical phase subjects the candidate integrals $\\widetilde{I}$ to stringent analytical and numerical tests designed to meet the criteria of Liouville integrability and compatibility with known obstructions.

#### **WP 4.1: Analytical Vetting (The Liouville Criteria)**

**Objective:** Symbolically verify the core requirements of integrability: Conservation, Independence, and Involution.

* **Task 4.1.1: Poisson Bracket Computation (Conservation):**
  * Utilize Computer Algebra Systems (CAS, e.g., SymPy, Mathematica) to compute $\\{\\widetilde{I},\\widetilde{H}\\}\_{\\widetilde{\\omega}}$.
  * **Acceptance Threshold:** Must be symbolically zero, or the normalized residual must be $\<10^{-12}$ (quad precision) on random test points if full symbolic proof is intractable.
* **Task 4.1.2: Poisson Bracket Computation (Involution \- Crucial):**
  * Verify that $\\widetilde{I}$ commutes with all classical integrals (E, L). If multiple new integrals are found, verify they commute with each other.
* **Task 4.1.3: Functional Independence (Jacobian Rank Test):**
  * Calculate the rank of the Jacobian matrix of the gradients of all integrals.
  * **Validation:** Verify that $\\widetilde{I}$ is independent of known invariants AND the fiber momentum ($p\_\\theta$). Empirical Jacobian rank must increase by 1 on \>99% of randomly sampled states.
* **Kill Switch A:** If $\\widetilde{I}$ fails the Poisson bracket tests, or if it is functionally dependent on known quantities or the trivial fiber momentum, discard the candidate.
* **Deliverable 4.1:** Symbolic proof (or refutation) of Liouville criteria for each candidate.

#### **WP 4.2: Complete Morales-Ramis Test (AMENDED)**

**Objective:** Validate lift-integrability hypothesis by proving **BOTH**:
1. The system is non-integrable downstairs (defensive falsification)
2. The lifted system has abelian Galois structure upstairs (compatibility test) **← AMENDED**

This two-phase test ensures discovered integrals are genuine features of the lift and compatible with Morales-Ramis theory.

**PHASE I: Downstairs Non-Integrability (Defensive Falsification)**

* **Task 4.2.1: Downstairs Variational Equations Setup:**
  * Set up the Normal Variational Equations (NVE) along specific known periodic solutions (e.g., Lagrange equilateral, Collinear configurations) in the *original* (downstairs) coordinates.

* **Task 4.2.2: Downstairs Differential Galois Group Computation:**
  * Apply the Morales-Ramis (MR) criteria (e.g., using the Kovacic algorithm) to the downstairs NVE.

* **Task 4.2.3: Confirmation of Downstairs Non-Integrability:**
  * Verify that the identity component of the differential Galois group is **non-abelian**.
  * **Validation:** This confirms non-integrability downstairs, proving that any new integral must live upstairs and validating consistency with Bruns/Poincaré.

**PHASE II: Upstairs Compatibility Test (NEW - CRITICAL AMENDMENT)**

* **Task 4.2.4: Upstairs Variational Equations Setup:**
  * Lift the same periodic solutions to the **extended phase space** (S¹ bundle or KS-Spinor lift).
  * Set up the Normal Variational Equations in the **lifted coordinates**, using:
    - Extended Hamiltonian $\\widetilde{H}$ (from WP 2.2 or 2.3)
    - Extended symplectic form $\\widetilde{\\omega}$
    - Connection one-form $A$ (for S¹ bundle, from WP 2.1.2)

* **Task 4.2.5: Upstairs Differential Galois Group Computation:**
  * Apply the Kovacic algorithm to the **upstairs** NVE.
  * Determine whether the identity component of the Galois group is **abelian** upstairs.
  * **Critical Test:** This is the core of the Compatibility Test.

* **Task 4.2.6: Compatibility Test Validation:**
  * Interpret results in context of WP3 discoveries:
    - **If upstairs abelian + WP3 found integrals** → ✓ **LIFT-INTEGRABILITY CONFIRMED**
    - **If upstairs non-abelian + WP3 found integrals** → ✗ **WP3 INTEGRALS SPURIOUS**
    - **If upstairs abelian + WP3 found nothing** → ⚠ Integrals exist but were missed
    - **If upstairs non-abelian + WP3 found nothing** → ○ Negative result confirmed
  * **Validation:** Confirm that the upstairs abelian structure is consistent with the lift-integrability hypothesis and validates (or refutes) WP3 integral discoveries.

**Deliverable 4.2:**
* **Phase I**: Formal proof of downstairs non-integrability via Morales-Ramis
* **Phase II** (NEW): Formal analysis of upstairs Galois structure
* **Complete Compatibility Test Report**: Validation or refutation of lift-integrability hypothesis

**Duration**: 10-14 days (increased from 5-7 days due to Phase II addition)

**Critical Dependencies**:
- Requires WP2 lifts to be implemented (preferably symbolically using SymPy)
- Requires extended Hamiltonians $\\widetilde{H}$ from WP 2.2 and 2.3
- Requires connection one-form $A$ from WP 2.1.2

#### **WP 4.3: Numerical Robustness and Generalization**

**Objective:** Validate the universality and stability of $\\widetilde{I}$ across the entire parameter space of the general three-body problem.

* **Task 4.3.1: Generalization and Monte Carlo Suite:**
  * Generalize the analytical expression of $\\widetilde{I}$ to the full 3BP (arbitrary masses, 3D orbits).
  * Execute a large-scale simulation ($\\geq 10^5$ initial conditions) covering the full parameter space.
* **Task 4.3.2: Stress Testing and Regularization:**
  * Test $\\widetilde{I}$ in extreme scenarios: near-triple collisions, high eccentricity orbits.
  * Ensure the integrator employs robust regularization (KS, chain regularization, Sundman time scaling) during close encounters.
* **Task 4.3.3: Long-Time Invariance Analysis:**
  * Analyze the drift of $\\widetilde{I}$ relative to the energy error (shadow Hamiltonian accuracy).
  * **Acceptance Threshold:** Require $\\sup\_{t\\le T}\\frac{|\\Delta \\widetilde{I}(t)|}{\\max(1,|\\widetilde{I}(0)|)} \\le C\\cdot \\epsilon\_H(T)$ with $C\\approx 10$. Drift in $\\widetilde{I}$ must not exceed the integrator error.
* **Task 4.3.4: Chaos Correlation Analysis:**
  * Measure Lyapunov exponents downstairs and verify that $\\widetilde{I}$ remains conserved upstairs even in strongly chaotic regions.
* **Deliverable 4.3:** Comprehensive statistical validation report confirming the universality and robustness of $\\widetilde{I}$.

---

### **WP 5: Consolidation and Publication**

#### **WP 5.1: Results Consolidation and Dissemination**

* **Task 5.1.1: Formal Proof Construction:** Consolidate the analytical proofs (WP 4.1, 4.2) and numerical evidence (WP 4.3) into a formal mathematical argument for Lift-Integrability.
* **Task 5.1.2: Analysis of Negative or Partial Results:** If a universal $\\widetilde{I}$ is not found, rigorously characterize the boundaries established (from WP 3.1) or characterize any discovered approximate/regime-specific invariants.
* **Task 5.1.3: Reproducibility Package:** Publish the code, data artifacts (e.g., curvature fields, connection 1-forms), and the learned $\\widetilde{I}$ (if found) as executable artifacts with unit tests.
* **Task 5.1.4: Publication:** Prepare manuscripts for major journals in Physics, Mathematics, and Computational Science.

---

## Key Changes Summary

### Original vs. Amended WP 4.2

| Aspect | Original | Amended |
|--------|----------|---------|
| **Phases** | 1 (Downstairs only) | 2 (Downstairs + Upstairs) |
| **Tasks** | 3 tasks | 6 tasks |
| **Duration** | 5-7 days | 10-14 days |
| **Scope** | Defensive (prove non-integrability downstairs) | **Complete** (prove non-integrable downstairs + abelian upstairs) |
| **Validates** | Classical obstructions | **Lift-integrability hypothesis** |
| **Critical Addition** | — | **Upstairs Galois group analysis (Tasks 4.2.4-4.2.6)** |

### Why This Amendment is Critical

**Without Phase II** (original plan):
- ✅ Confirms 3BP is non-integrable downstairs
- ✅ Consistent with Bruns/Poincaré
- ❌ **Does NOT validate that upstairs integrals are genuine**
- ❌ **Does NOT test compatibility with Morales-Ramis forward direction**
- ❌ **Cannot distinguish genuine lift-integrals from spurious numerical artifacts**

**With Phase II** (amended plan):
- ✅ Confirms 3BP is non-integrable downstairs
- ✅ Consistent with Bruns/Poincaré
- ✅ **Tests whether upstairs Galois group is abelian**
- ✅ **Validates or refutes WP3 integral discoveries**
- ✅ **Provides complete compatibility test for lift-integrability**
- ✅ **Meets publication standards for major journals**

### Theoretical Foundation

**Morales-Ramis Theorem**:
- **Forward**: Integrable → Abelian Galois group
- **Contrapositive**: Non-abelian → Not integrable

**For Lift-Integrability**:
1. Downstairs must be non-abelian (Phase I) ✓
2. **Upstairs must be abelian (Phase II)** ← **This was missing**

**Both conditions are necessary for rigorous validation.**

---

## Implementation Notes

### Dependencies for Phase II

**From WP2**:
- [ ] Extended Hamiltonians $\\widetilde{H}$ (S¹ bundle, KS-Spinor) - preferably symbolic (SymPy)
- [ ] Extended symplectic forms $\\widetilde{\\omega}$
- [ ] Connection one-form $A$ (from Task 2.1.2)
- [ ] Constraint Hamiltonians (for KS-Spinor, from Task 2.3.3)

**Recommendation**: Implement WP2 lifts using SymPy to enable symbolic computation of upstairs variational equations.

### Computational Challenges

**Upstairs NVE Computation**:
1. **Symbolic approach** (preferred):
   - Derive $\\nabla^2 \\widetilde{H}$ symbolically
   - Construct NVE symbolically
   - Apply Kovacic algorithm symbolically

2. **Numerical→Symbolic** (fallback):
   - Evaluate NVE numerically at many points
   - Fit to rational function form
   - Apply Kovacic to fitted form
   - **Risk**: Fitting errors may obscure true Galois group

3. **Hybrid approach**:
   - Use symbolic regression (PySR) to discover form
   - Validate against numerical NVE
   - Apply Kovacic to discovered form

---

## Timeline Impact

**Original WP4 Duration**: 23-29 days
**Amended WP4 Duration**: 28-36 days (+5-7 days for Phase II)

**Total Project Impact**: Approximately 1 additional week for complete Morales-Ramis test.

**Justification**: The additional time is essential for rigorous validation of lift-integrability and is necessary for publication in top-tier journals.

---

**Document Version**: 2.0 (AMENDED)
**Original Version**: 1.0 (2025-11-16)
**Amendment Date**: 2025-11-20
**Amendment Scope**: WP 4.2 only (WP 1-3, 4.1, 4.3, 5 unchanged)
**Status**: Amended Implementation Plan
**Critical Change**: Addition of Phase II (Upstairs Morales-Ramis Analysis) to WP 4.2
