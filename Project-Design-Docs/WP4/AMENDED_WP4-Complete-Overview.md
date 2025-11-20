# AMENDED Work Package 4: Rigorous Validation and Falsification
## Complete Overview - "The Gauntlet" (Updated for Upstairs Analysis)

**AMENDMENT DATE**: 2025-11-20
**AMENDMENT REASON**: Critical addition of upstairs Morales-Ramis analysis per theoretical framework

**Status**: Design Phase - Ready for Planning (AMENDED)
**Documentation Version**: 2.0 (AMENDED)
**Last Updated**: 2025-11-20
**Prerequisites**: WP3 Complete (Candidate Integrals Discovered)
**Next Phase**: WP5 Consolidation and Publication

---

## Amendment Summary

### Critical Gap Identified

The original WP4 plan was **incomplete** regarding the Morales-Ramis test:

**Original WP 4.2** (Defensive Falsification):
- ✅ Compute NVE downstairs
- ✅ Verify Galois group is non-abelian
- ✅ Confirm: 3BP is non-integrable downstairs

**Missing from Original Plan**:
- ❌ Compute NVE **upstairs** (in lifted space)
- ❌ Verify Galois group is **abelian** upstairs
- ❌ Validate: Lift-integrability is compatible with Morales-Ramis

### Theoretical Basis for Amendment

From "Abelianizing Variational Equations in the Three-Body Problem: Constraints and Transformations":

> "The aim is to find a transformation such that the NVE upstairs has an abelian Galois group, even though downstairs it was non-abelian. [...] If the extended system becomes integrable (in a broad sense), then along the lifted orbit the NVE's Galois group will have an abelian identity component by design."

**Morales-Ramis Criterion**:
- **Forward**: Integrable → Abelian Galois group
- **Contrapositive**: Non-abelian → Not integrable

**For Lift-Integrability**:
1. **Downstairs**: Must be non-abelian (confirms classical obstruction)
2. **Upstairs**: Must be abelian (validates lift-integrability)

**Both are necessary.**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Validation Philosophy](#the-validation-philosophy)
3. [WP4 Architecture (AMENDED)](#wp4-architecture-amended)
4. [Component Overview](#component-overview)
5. [Mathematical Framework](#mathematical-framework)
6. [Decision Trees](#decision-trees)
7. [Quality Metrics](#quality-metrics)
8. [Handoff to WP5](#handoff-to-wp5)
9. [Timeline and Dependencies](#timeline-and-dependencies)
10. [References](#references)

---

## Executive Summary

Work Package 4 is the **critical validation phase** where candidate conserved quantities from WP3 face rigorous analytical and numerical scrutiny. This phase distinguishes genuine scientific discovery from numerical artifacts and ensures results meet publication standards.

### Core Objective (AMENDED)

**Prove or Disprove**: For each candidate integral $\widetilde{I}$ from WP3:
1. **Conservation**: Is $\{\widetilde{I}, \widetilde{H}\} = 0$ truly satisfied?
2. **Independence**: Is $\widetilde{I}$ functionally independent of known integrals (E, L, p_θ)?
3. **Involution**: Does $\widetilde{I}$ Poisson-commute with other integrals?
4. **Compatibility (AMENDED)**:
   - ✅ **Downstairs**: Non-abelian Galois group (confirms classical obstruction)
   - ✅ **Upstairs**: Abelian Galois group (validates lift-integrability) **← NEW**
5. **Robustness**: Does conservation hold across parameter space and long timescales?

### The "Gauntlet" Metaphor (AMENDED)

WP4 subjects candidates to a **multi-stage gauntlet** of increasingly stringent tests:

```
Candidate Integrals from WP3
    ↓
[Stage 1: Analytical Vetting] (WP 4.1)
    ├─→ Symbolic Poisson brackets
    ├─→ Functional independence (Jacobian)
    └─→ Involution verification
    ↓ (Survivors only)
[Stage 2: Compatibility Test] (WP 4.2 - AMENDED)
    ├─→ PHASE I: Downstairs Morales-Ramis
    │    ├─→ Compute NVE downstairs
    │    ├─→ Verify: Galois group NON-ABELIAN
    │    └─→ Confirm: 3BP non-integrable (Bruns/Poincaré)
    │
    ├─→ PHASE II: Upstairs Morales-Ramis ⭐ NEW
    │    ├─→ Compute NVE upstairs (S¹ lift, KS-Spinor lift)
    │    ├─→ Verify: Galois group ABELIAN
    │    └─→ Validate: Lift-integrability compatible with MR
    │
    └─→ Compatibility Verdict:
         • If upstairs abelian + WP3 found integrals → SUCCESS
         • If upstairs non-abelian → WP3 integrals SPURIOUS
    ↓ (Validated candidates)
[Stage 3: Numerical Robustness] (WP 4.3)
    ├─→ Monte Carlo across parameter space
    ├─→ Long-time integration (10^4-10^6 periods)
    ├─→ Stress testing (near-collisions, chaos)
    └─→ Statistical validation
    ↓
Publication-Ready Results → WP5
```

**Acceptance Threshold**: Only candidates passing ALL stages proceed to WP5.

---

## The Validation Philosophy

### Why Such Rigor?

The three-body problem has a history of false claims of integrability. To avoid adding to this list, WP4 implements **defensive validation**:

1. **Symbolic Certainty**: Where possible, prove results symbolically (not just numerically)
2. **Negative Results**: Explicitly test compatibility with known obstructions
3. **Positive Validation (AMENDED)**: **Explicitly test compatibility with Morales-Ramis upstairs**
4. **Statistical Significance**: Require results to hold over large ensembles
5. **Reproducibility**: Provide code and data for independent verification

### Scientific Standards (AMENDED)

**Publication Requirement**: To claim a new integral exists, we must demonstrate:
- ✅ Conservation to machine precision (< 10^{-12}) or symbolic exactness
- ✅ Functional independence (Jacobian rank test on 10^4+ states)
- ✅ Involution with known integrals (Poisson brackets < 10^{-10})
- ✅ **Downstairs non-abelian** (proves "upstairs" nature) - WP 4.2 Phase I
- ✅ **Upstairs abelian** (validates lift-integrability) - WP 4.2 Phase II **← NEW**
- ✅ Long-time numerical stability (drift < integrator error over 10^4 periods)

**Negative Result Requirement**: To claim no integral exists, we must demonstrate:
- ✅ Comprehensive search (WP3 covered all approaches)
- ✅ Morales-Ramis confirms downstairs non-integrability
- ✅ **Morales-Ramis confirms upstairs also non-integrable (for current lifts)** **← NEW**
- ✅ Characterization of search space bounds

---

## WP4 Architecture (AMENDED)

### Three-Stage Pipeline

```
WP4: Rigorous Validation (3 parallel tracks → synthesis)
│
├── WP 4.1: Analytical Vetting (8-10 days)
│   ├── 4.1.1: Poisson Bracket Computation (Conservation)
│   ├── 4.1.2: Involution Testing
│   └── 4.1.3: Functional Independence
│
├── WP 4.2: Complete Morales-Ramis Test (10-14 days) ⭐ AMENDED
│   │
│   ├── PHASE I: Downstairs (Defensive Falsification)
│   │   ├── 4.2.1: Downstairs Variational Equations Setup
│   │   ├── 4.2.2: Downstairs Differential Galois Group
│   │   └── 4.2.3: Confirmation of Downstairs Non-Integrability
│   │
│   └── PHASE II: Upstairs (Compatibility Test) ⭐ NEW
│       ├── 4.2.4: Upstairs Variational Equations Setup
│       ├── 4.2.5: Upstairs Differential Galois Group
│       └── 4.2.6: Compatibility Test Validation
│
└── WP 4.3: Numerical Robustness (10-12 days)
    ├── 4.3.1: Monte Carlo Parameter Sweep
    ├── 4.3.2: Stress Testing (collisions, chaos)
    ├── 4.3.3: Long-Time Invariance
    └── 4.3.4: Chaos Correlation Analysis
```

**Total Duration**: 28-36 days (increased from 23-29 days)
**Reason for Increase**: Addition of upstairs Morales-Ramis analysis (Phase II)

---

## Component Overview

### WP 4.1: Analytical Vetting (Liouville Criteria)

**Duration**: 8-10 days

*[Content unchanged from original plan - omitted for brevity]*

---

### WP 4.2: Complete Morales-Ramis Test (AMENDED)

**Duration**: 10-14 days (increased from 5-7 days)

**Purpose**: **Prove BOTH** that:
1. The system is non-integrable "downstairs" (defensive falsification)
2. The system exhibits abelian Galois structure "upstairs" (compatibility test)

This validates that $\widetilde{I}$ is genuinely a feature of the lift and consistent with Morales-Ramis theory.

#### PHASE I: Downstairs Analysis (Original Plan)

**The Morales-Ramis Criterion (Contrapositive)**:

For a Hamiltonian system, if the **differential Galois group** of the Normal Variational Equations (NVE) around a periodic orbit is non-abelian, the system is **provably non-integrable**.

**Strategy**: Show that 3-body problem is non-integrable downstairs → any new integral must live upstairs.

**Tasks**:

##### Task 4.2.1: Downstairs Variational Equations

1. Select test periodic orbits (e.g., Lagrange equilateral, Figure-8, Euler collinear)
2. Compute **Normal Variational Equations** (NVE) **downstairs**:
   - Linearize Hamiltonian flow around periodic orbit
   - Reduce to normal directions (perpendicular to orbit)

##### Task 4.2.2: Downstairs Differential Galois Group

Use **Kovacic algorithm** or similar to compute Galois group **downstairs**:
- If identity component is non-abelian → non-integrable downstairs ✓
- If abelian → integrable downstairs (would contradict Bruns/Poincaré!)

##### Task 4.2.3: Downstairs Interpretation

**Expected Result**: Galois group is non-abelian (SL(2, ℂ) or similar)
- ✅ **Confirms**: 3BP is non-integrable downstairs (consistent with Bruns/Poincaré)
- ✅ **Validates**: Any integral from WP3 must be a lift-integral

**Deliverables (Phase I)**:
- Downstairs Galois group computation for 3+ periodic orbits
- Proof of downstairs non-integrability

---

#### PHASE II: Upstairs Analysis (NEW)

**The Morales-Ramis Criterion (Forward Direction)**:

If a Hamiltonian system is integrable, then the **differential Galois group** of the NVE must have an **abelian identity component**.

**Strategy**: Show that the lifted system has abelian Galois group upstairs → validates lift-integrability hypothesis.

**Tasks**:

##### Task 4.2.4: Upstairs Variational Equations ⭐ NEW

1. Select same periodic orbits as Phase I
2. **Lift orbits** to extended phase space:
   - **S¹ bundle**: Add (θ, p_θ) fiber coordinates
   - **KS-Spinor**: Transform to constrained spinor coordinates
3. Compute **Normal Variational Equations UPSTAIRS**:
   - Linearize **extended** Hamiltonian $\widetilde{H}$ along lifted orbit
   - Use **extended** symplectic form $\widetilde{\omega}$
   - Reduce to normal directions in lifted space

**Key Difference from Downstairs**:
- Downstairs NVE: $\frac{d}{dt}\delta y = J \nabla^2 H \delta y$
- **Upstairs NVE**: $\frac{d}{dt}\delta \widetilde{y} = \widetilde{J} \nabla^2 \widetilde{H} \delta \widetilde{y}$

**Requirements**:
- Requires WP2 lifts to be implemented (preferably symbolically)
- Requires extended Hamiltonians and symplectic forms
- Requires connection $A$ (for S¹ bundle) from WP 2.1.2

##### Task 4.2.5: Upstairs Differential Galois Group ⭐ NEW

Use **Kovacic algorithm** to compute Galois group **upstairs**:

**If identity component is ABELIAN**:
- ✅ Consistent with Morales-Ramis integrability criterion
- ✅ Validates that upstairs system CAN be integrable
- ✅ Supports WP3 integral discoveries

**If identity component is NON-ABELIAN**:
- ✗ Inconsistent with Morales-Ramis
- ✗ Implies WP3 integrals are spurious or not true integrals
- ✗ Suggests lift construction is inadequate

**Implementation Challenge**:
- Upstairs NVE may need to be derived symbolically (from WP2)
- Numerical → symbolic conversion is difficult
- **Recommendation**: Implement WP2 lifts using SymPy

##### Task 4.2.6: Compatibility Test Validation ⭐ NEW

Interpret upstairs Galois group results and validate against WP3 discoveries.

**Compatibility Matrix**:

| Upstairs Galois | WP3 Found Integrals | Verdict |
|-----------------|---------------------|---------|
| **Abelian** | ✅ Yes | ✓✓✓ **LIFT-INTEGRABILITY CONFIRMED** |
| Abelian | ✗ No | ⚠ Integrals exist but WP3 missed them |
| **Non-abelian** | ✅ Yes | ✗✗✗ **WP3 INTEGRALS SPURIOUS** |
| Non-abelian | ✗ No | ○ Negative result confirmed |

**Deliverables (Phase II)**:
- Upstairs Galois group computation for 3+ periodic orbits
- Upstairs NVE analysis for both S¹ and KS-Spinor lifts
- **Compatibility test report**: Are WP3 integrals consistent with upstairs Galois structure?
- **Validation**: If abelian, confirm that this validates lift-integrability hypothesis

**Combined Deliverables (Phase I + II)**:
- Complete two-phase Morales-Ramis analysis
- Proof that integrals live upstairs (downstairs non-abelian) AND are compatible with Morales-Ramis (upstairs abelian)
- **This is the COMPATIBILITY TEST mentioned in the theoretical paper**

---

### WP 4.3: Numerical Robustness and Generalization

**Duration**: 10-12 days

*[Content unchanged from original plan - omitted for brevity]*

---

## Mathematical Framework

### Liouville Integrability Conditions

*[Content unchanged from original plan - omitted for brevity]*

### Poisson Brackets

*[Content unchanged from original plan - omitted for brevity]*

### Morales-Ramis Criterion (COMPLETE FORMULATION - AMENDED)

**Theorem** (Morales-Ramis, 1999):

If a Hamiltonian system with $n$ DOF is integrable with $n$ independent meromorphic first integrals, then the identity component of the differential Galois group of the Normal Variational Equation is **abelian** for any non-equilibrium solution.

**Contrapositive** (Downstairs Test):
$$
G^0_{\text{downstairs}} \text{ non-abelian} \Rightarrow H_{\text{downstairs}} \text{ non-integrable}
$$

**Forward Direction** (Upstairs Test) **← NEW**:
$$
\widetilde{H}_{\text{upstairs}} \text{ integrable} \Rightarrow G^0_{\text{upstairs}} \text{ abelian}
$$

**Contrapositive of Forward** (Compatibility Test) **← NEW**:
$$
G^0_{\text{upstairs}} \text{ non-abelian} \Rightarrow \widetilde{H}_{\text{upstairs}} \text{ NOT integrable}
$$

**Application to Lift-Integrability**:

1. **Test 1** (Downstairs): Compute $G^0_{\text{downstairs}}$ for 3BP
   - **Expected**: Non-abelian (SL(2,ℂ))
   - **Conclusion**: 3BP non-integrable downstairs
   - **Validates**: Bruns/Poincaré theorems

2. **Test 2** (Upstairs) **← NEW**: Compute $G^0_{\text{upstairs}}$ for lifted system
   - **If abelian**: Lift-integrability is POSSIBLE and COMPATIBLE with MR
   - **If non-abelian**: Lift-integrability is IMPOSSIBLE (current lift inadequate)
   - **Validates/Refutes**: WP3 integral discoveries

**Computational Tool**: **Kovacic Algorithm** (deterministic) for linear ODEs with rational coefficients.

**Both tests are necessary for complete validation.**

---

## Decision Trees

### Decision Point 1: After WP 4.1 (Analytical Vetting)

*[Content unchanged from original plan - omitted for brevity]*

---

### Decision Point 2: After WP 4.2 Phase I (Downstairs Morales-Ramis)

**Question**: Is the downstairs problem non-integrable?

```
Downstairs Galois group non-abelian?
├─ YES (expected)
│  └─→ PASS PHASE I: Downstairs is provably non-integrable
│       Proceed to PHASE II (Upstairs Test)
│
└─ NO (Galois group abelian)
   └─→ SURPRISE: Suggests integrable structure downstairs!
        Action: Re-examine computation
        Question: Did we miss a downstairs integral?
        STOP: Cannot proceed to Phase II if Phase I failed
```

---

### Decision Point 2b: After WP 4.2 Phase II (Upstairs Morales-Ramis) ⭐ NEW

**Question**: Does the upstairs system have abelian Galois structure?

```
Upstairs Galois group abelian?
├─ YES (hoped for)
│  ├─ WP3 found integrals?
│  │  ├─ YES → ✓✓✓ LIFT-INTEGRABILITY CONFIRMED
│  │  │         Proceed to WP 4.3 and WP5
│  │  │         Publication: Major discovery
│  │  │
│  │  └─ NO  → ⚠ Integrals exist but WP3 missed them
│  │           Action: Re-run WP3 with expanded search
│  │           OR: Characterize partial integrability
│  │
│  └─ Conclusion: Upstairs structure is compatible with integrability
│
└─ NO (non-abelian upstairs)
   ├─ WP3 found integrals?
   │  ├─ YES → ✗✗✗ WP3 INTEGRALS ARE SPURIOUS
   │  │         Action: Re-examine WP3 conservation tests
   │  │         Likely: Numerical artifacts or approximate invariants
   │  │         Do NOT proceed to publication with these integrals
   │  │
   │  └─ NO  → ○ NEGATIVE RESULT CONFIRMED
   │            Conclusion: Current lifts do not resolve integrability
   │            Action: Try alternative lift constructions
   │            OR: Document rigorous negative result
   │
   └─ Conclusion: Upstairs structure is still non-integrable
```

---

### Decision Point 3: After WP 4.3 (Numerical Robustness)

*[Content unchanged from original plan - omitted for brevity]*

---

## Quality Metrics

### Acceptance Thresholds (AMENDED)

| Metric | Minimum | Target | Exceptional |
|--------|---------|--------|-------------|
| **Conservation** $\|\{I, H\}\|$ | < 10^{-10} | < 10^{-12} | = 0 (symbolic) |
| **Involution** $\|\{I, J\}\|$ | < 10^{-8} | < 10^{-10} | = 0 (symbolic) |
| **Independence** (Jacobian rank) | 99% samples | 99.9% | 100% |
| **Downstairs Galois** | Non-abelian | Non-abelian (SL(2,ℂ)) | Proven non-abelian |
| **Upstairs Galois** ⭐ **NEW** | **Abelian (80%+ orbits)** | **Abelian (all orbits)** | **Proven abelian** |
| **Long-time drift** $\epsilon_I$ | < 10^{-5} | < 10^{-8} | < 10^{-12} |
| **Monte Carlo success** | 90% | 95% | 99% |

### Confidence Levels (AMENDED)

**High Confidence** (publishable):
- Symbolic conservation proof OR
- Numerical conservation < 10^{-12} over 10^6 periods on 10^5 trajectories AND
- **Downstairs Galois group non-abelian** AND
- **Upstairs Galois group abelian** ⭐ **NEW**

**Medium Confidence** (conditional result):
- Numerical conservation < 10^{-8} over 10^4 periods
- Valid in specific parameter regime
- Upstairs Galois group abelian for some (not all) orbits

**Low Confidence** (negative result):
- Conservation fails in >10% of cases
- Drift exceeds integrator error
- **Upstairs Galois group non-abelian** (contradicts WP3 integrals)

---

## Handoff to WP5

### Outputs from WP4 (AMENDED)

**Positive Result** (integral(s) validated):
1. **Analytical Certification**:
   - Symbolic expressions for integrals
   - Poisson bracket proofs (symbolic or numerical)
   - Independence proof (Jacobian rank)

2. **Numerical Certification**:
   - Statistical validation report (10^5 trajectories)
   - Error distributions and confidence intervals
   - Stress test results

3. **Theoretical Validation** (AMENDED):
   - **Downstairs Morales-Ramis**: Proof of non-integrability (confirms classical obstruction)
   - **Upstairs Morales-Ramis**: Proof of abelian Galois structure (validates lift-integrability) ⭐ **NEW**
   - **Compatibility Test Report**: WP3 integrals are consistent with MR theory
   - Explanation of lift mechanism

**Negative Result** (no integrals found):
1. **Proof of Comprehensive Search**:
   - WP3 methodology completeness
   - **Downstairs Morales-Ramis** confirms non-integrability
   - **Upstairs Morales-Ramis** shows current lifts inadequate ⭐ **NEW**
   - Bounds on search space

2. **Documentation**:
   - What was tried and why it failed
   - Limitations of current methods
   - Suggested alternative approaches

### WP5 Entry Criteria (AMENDED)

**For Positive Results**:
- [ ] At least one candidate passed all WP 4.1-4.3 tests
- [ ] Symbolic or numerical conservation to < 10^{-10}
- [ ] Statistical validation on >10^5 trajectories
- [ ] **Downstairs Morales-Ramis** confirms non-integrability (Phase I)
- [ ] **Upstairs Morales-Ramis** confirms abelian structure (Phase II) ⭐ **NEW**
- [ ] **Compatibility test** validates WP3 integrals ⭐ **NEW**

**For Negative Results**:
- [ ] **Downstairs Morales-Ramis** confirms non-integrability
- [ ] **Upstairs Morales-Ramis** confirms current lifts inadequate ⭐ **NEW**
- [ ] WP3 search documented as comprehensive
- [ ] Bounds on non-existence characterized

---

## Timeline and Dependencies (AMENDED)

### Critical Path

```
WP3 Complete → Candidates Available
    ↓
Week 1-2: WP 4.1 (Analytical Vetting)
    ↓
    ├─→ Week 2-4: WP 4.2 Phase I (Downstairs Morales-Ramis)
    │       ↓
    │   Week 4-5: WP 4.2 Phase II (Upstairs Morales-Ramis) ⭐ NEW
    │
    └─→ Week 2-5: WP 4.3 (Numerical Robustness) [Parallel with 4.2]
    ↓
Week 5-6: Consolidation & Analysis
    ↓
WP5 (Publication)
```

**Total Duration**: 5-6 weeks (28-36 days, increased from 4-5 weeks / 23-29 days)

**Reason for Increase**: Addition of Phase II (Upstairs Morales-Ramis) in WP 4.2

### Parallelization Strategy (AMENDED)

**Can Run in Parallel**:
- WP 4.2 Phase I and WP 4.3 (after WP 4.1 completes)
- Within WP 4.3: Different parameter sweeps (mass ratios, energies)

**Must Run Sequentially**:
- WP 4.1 first (filters candidates before expensive tests)
- WP 4.1 → WP 4.2 Phase I (Downstairs)
- **WP 4.2 Phase I → WP 4.2 Phase II** (Upstairs) ⭐ **NEW**
- WP 4.2 Phase II & WP 4.3 → WP5

**Note**: Phase II can overlap with WP 4.3 if Phase I passes quickly.

---

## Risk Assessment

### Scientific Risks (AMENDED)

**Risk 1: All Candidates Fail Validation**
- **Probability**: Medium (30%)
- **Impact**: Medium (negative result, still publishable)
- **Mitigation**:
  - Rigorous WP3 methods reduce this risk
  - Negative result proves bounds on non-integrability
  - Still advances field knowledge

**Risk 2a: Downstairs Morales-Ramis Test Ambiguous**
- **Probability**: Low (10%)
- **Impact**: Medium
- **Mitigation**:
  - Test multiple periodic orbits
  - Use multiple computational methods
  - Consult differential Galois theory experts

**Risk 2b: Upstairs Galois Group is Non-Abelian** ⭐ **NEW**
- **Probability**: Medium-High (40% if lifts are inadequate)
- **Impact**: High (invalidates WP3 integrals if found)
- **Mitigation**:
  - Test multiple lift types (S¹ bundle AND KS-Spinor)
  - Consider alternative lift constructions
  - Document as negative result if confirmed
- **Interpretation**:
  - If upstairs is non-abelian, current lifts do NOT resolve integrability
  - This is valuable information (eliminates certain approaches)
  - Suggests need for more sophisticated lift constructions

**Risk 3: Numerical Instabilities Mask Conservation**
- **Probability**: Low (15%)
- **Impact**: High (false negative)
- **Mitigation**:
  - Use high-precision arithmetic (quad precision)
  - Multiple integrators (cross-validation)
  - Shadow Hamiltonian analysis

**Risk 4: Symbolic Computation for Upstairs NVE Intractable** ⭐ **NEW**
- **Probability**: Medium-High (50%)
- **Impact**: Medium (delays Phase II)
- **Mitigation**:
  - Implement WP2 lifts symbolically from the start (using SymPy)
  - Alternatively, use numerical→symbolic fitting (PySR)
  - Consult with differential Galois theory experts
  - May need to restrict to specific orbits where symbolic form is known

### Implementation Risks (AMENDED)

**Risk 5: Computational Cost Prohibitive**
- **Probability**: Medium (25%)
- **Impact**: Medium (timeline delay)
- **Mitigation**:
  - HPC resources secured
  - Efficient sampling (stratified, importance)
  - Can reduce to 10^4 trajectories if needed

**Risk 6: WP2 Lifts Not Available in Symbolic Form** ⭐ **NEW**
- **Probability**: Medium (40% if WP2 implemented numerically only)
- **Impact**: High (blocks Phase II)
- **Mitigation**:
  - **Critical dependency**: WP2 must deliver symbolic Hamiltonians
  - Coordinate with WP2 implementation to ensure SymPy compatibility
  - Allocate extra time for symbolic→numerical conversion if needed

---

## Success Criteria (AMENDED)

### Minimum Success
- [ ] All WP3 candidates tested against WP 4.1 criteria
- [ ] Morales-Ramis Phase I (downstairs) performed on 3+ periodic orbits
- [ ] **Morales-Ramis Phase II (upstairs) attempted for at least one lift** ⭐ **NEW**
- [ ] Statistical validation on >10^4 trajectories
- [ ] Results (positive or negative) documented

### Target Success
- [ ] At least one candidate passes all validation stages
- [ ] Conservation < 10^{-10} symbolically or numerically
- [ ] Downstairs Galois groups non-abelian (all orbits)
- [ ] **Upstairs Galois groups abelian (≥80% of orbits)** ⭐ **NEW**
- [ ] **Compatibility test confirms WP3 integrals are genuine** ⭐ **NEW**
- [ ] Statistical validation on >10^5 trajectories with 95% success

### Stretch Success
- [ ] Multiple independent integrals validated
- [ ] Symbolic conservation proofs
- [ ] **Symbolic proof of abelian Galois structure upstairs** ⭐ **NEW**
- [ ] **Both S¹ and KS-Spinor lifts show abelian structure** ⭐ **NEW**
- [ ] Characterization of integrable submanifolds
- [ ] Publication in top-tier journal (Nature, Science, PRL, Inventiones)

---

## References

*[Original references retained, plus:]*

### Additional References for Upstairs Analysis ⭐ NEW

9. **Abelianizing Variational Equations**:
   - Project document: "Abelianizing Variational Equations in the Three-Body Problem: Constraints and Transformations"
   - Theoretical framework for upstairs Morales-Ramis test

10. **Inverse Differential Galois Theory**:
   - Compoint & Singer, "Inverse differential Galois problem" (1999)
   - Provides framework for forcing abelian Galois groups

11. **Symplectic Lifts and Extensions**:
   - Eisenhart lift, KS regularization as examples of phase space extensions
   - Theoretical basis for "upstairs" integrability

---

## Summary

Work Package 4 is the **proving ground** where candidate integrals from WP3 are subjected to the most rigorous validation possible. **This amended plan completes the Morales-Ramis test by adding the critical upstairs analysis.**

**Key Innovations**:
- First application of **two-phase** Morales-Ramis test to lift-integrability hypothesis
- **Downstairs test** (Phase I): Confirms non-integrability (defensive)
- **Upstairs test** (Phase II): Validates lift-integrability (constructive) ⭐ **NEW**
- Statistical validation framework for conserved quantities
- Complete compatibility test for WP3 discoveries

**Expected Outcome**: Either:
1. ✅ **Publication-ready integral(s)** with complete certification:
   - Downstairs non-abelian (Bruns/Poincaré confirmed)
   - **Upstairs abelian (lift-integrability validated)** ⭐ **NEW**
   - Numerical conservation verified
   - **MAJOR DISCOVERY: Hidden integrability via lifts**

2. 📊 **Rigorous negative result** establishing bounds on integrability:
   - Downstairs non-abelian (confirmed)
   - **Upstairs also non-abelian (current lifts inadequate)** ⭐ **NEW**
   - Characterizes what lifts DON'T work
   - **Still publishable and valuable**

**Both outcomes advance the field.**

---

**Document Version**: 2.0 (AMENDED)
**Original Version**: 1.0 (2025-11-16)
**Amendment Date**: 2025-11-20
**Amendment Reason**: Critical addition of upstairs Morales-Ramis analysis per theoretical framework
**Status**: Complete Overview - Ready for Task Planning (AMENDED)
**Next Documents**: AMENDED WP 4.2 Implementation Plan (complete), WP 4.1 and 4.3 plans (unchanged)
