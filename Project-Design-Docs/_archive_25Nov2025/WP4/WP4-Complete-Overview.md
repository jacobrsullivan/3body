# Work Package 4: Rigorous Validation and Falsification
## Complete Overview - "The Gauntlet"

**Status**: Design Phase - Ready for Planning
**Documentation Version**: 1.0
**Last Updated**: 2025-11-16
**Prerequisites**: WP3 Complete (Candidate Integrals Discovered)
**Next Phase**: WP5 Consolidation and Publication

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Validation Philosophy](#the-validation-philosophy)
3. [WP4 Architecture](#wp4-architecture)
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

### Core Objective

**Prove or Disprove**: For each candidate integral $\widetilde{I}$ from WP3:
1. **Conservation**: Is $\{\widetilde{I}, \widetilde{H}\} = 0$ truly satisfied?
2. **Independence**: Is $\widetilde{I}$ functionally independent of known integrals (E, L, p_θ)?
3. **Involution**: Does $\widetilde{I}$ Poisson-commute with other integrals?
4. **Compatibility**: Is the discovery consistent with no-go theorems (Bruns, Poincaré)?
5. **Robustness**: Does conservation hold across parameter space and long timescales?

### The "Gauntlet" Metaphor

WP4 subjects candidates to a **multi-stage gauntlet** of increasingly stringent tests:

```
Candidate Integrals from WP3
    ↓
[Stage 1: Analytical Vetting] (WP 4.1)
    ├─→ Symbolic Poisson brackets
    ├─→ Functional independence (Jacobian)
    └─→ Involution verification
    ↓ (Survivors only)
[Stage 2: Defensive Falsification] (WP 4.2)
    ├─→ Morales-Ramis test (confirm downstairs non-integrability)
    └─→ Proof that integral lives "upstairs"
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
3. **Statistical Significance**: Require results to hold over large ensembles
4. **Reproducibility**: Provide code and data for independent verification

### Scientific Standards

**Publication Requirement**: To claim a new integral exists, we must demonstrate:
- ✅ Conservation to machine precision (< 10^{-12}) or symbolic exactness
- ✅ Functional independence (Jacobian rank test on 10^4+ states)
- ✅ Involution with known integrals (Poisson brackets < 10^{-10})
- ✅ Compatibility with Morales-Ramis test (proves "upstairs" nature)
- ✅ Long-time numerical stability (drift < integrator error over 10^4 periods)

**Negative Result Requirement**: To claim no integral exists, we must demonstrate:
- ✅ Comprehensive search (WP3 covered all approaches)
- ✅ Morales-Ramis confirms downstairs non-integrability
- ✅ Characterization of search space bounds

---

## WP4 Architecture

### Three-Stage Pipeline

```
WP4: Rigorous Validation (3 parallel tracks → synthesis)
│
├── WP 4.1: Analytical Vetting (8-10 days)
│   ├── 4.1.1: Poisson Bracket Computation (Conservation)
│   ├── 4.1.2: Involution Testing
│   └── 4.1.3: Functional Independence
│
├── WP 4.2: Defensive Falsification (5-7 days)
│   ├── 4.2.1: Variational Equations Setup
│   ├── 4.2.2: Differential Galois Group
│   └── 4.2.3: Downstairs Non-Integrability Proof
│
└── WP 4.3: Numerical Robustness (10-12 days)
    ├── 4.3.1: Monte Carlo Parameter Sweep
    ├── 4.3.2: Stress Testing (collisions, chaos)
    ├── 4.3.3: Long-Time Invariance
    └── 4.3.4: Chaos Correlation Analysis
```

**Total Duration**: 23-29 days (some parallelization possible)

---

## Component Overview

### WP 4.1: Analytical Vetting (Liouville Criteria)

**Duration**: 8-10 days

**Purpose**: Verify that candidates satisfy the **Liouville integrability criteria** through symbolic and semi-numerical tests.

**Core Tests**:

#### Test 1: Conservation ($\{\widetilde{I}, \widetilde{H}\} = 0$)

**Symbolic Approach**:
```python
# Use Computer Algebra System (SymPy or Mathematica)
pb = poisson_bracket(I_candidate, H_lifted)
pb_simplified = simplify(pb)

if pb_simplified == 0:
    status = "SYMBOLICALLY CONSERVED"
else:
    status = "NOT CONSERVED" # Reject candidate
```

**Semi-Numerical Approach** (if symbolic fails):
- Evaluate bracket on 10^4 random phase space points
- Acceptance: $\max|\{I,H\}| < 10^{-12}$

#### Test 2: Involution ($\{\widetilde{I}_i, \widetilde{I}_j\} = 0$)

For all pairs of integrals (including known E, L, p_θ):
```
{I_new, E} = 0?
{I_new, L_x} = 0?
{I_new, L_y} = 0?
{I_new, L_z} = 0?
{I_new, p_θ} = 0?  (if S¹ bundle)
```

**Acceptance**: All brackets < 10^{-10} numerically or = 0 symbolically

#### Test 3: Functional Independence

**Jacobian Rank Test**:
$$
\text{rank}\begin{pmatrix}
\nabla E \\
\nabla L_x \\
\vdots \\
\nabla \widetilde{I}
\end{pmatrix} = n + 1
$$

where $n$ = number of previously known independent integrals

**Acceptance**: Rank increases on >99% of 10^4 random samples

**Kill Switch**: If any test fails, candidate is rejected immediately.

**Deliverables**:
- Symbolic proof of conservation (if possible)
- Numerical evidence with error bounds
- Independence certification

---

### WP 4.2: Defensive Falsification (Morales-Ramis Test)

**Duration**: 5-7 days

**Purpose**: **Prove** that the system is non-integrable "downstairs" (in standard phase space), thereby validating that $\widetilde{I}$ is genuinely a feature of the lift.

**The Morales-Ramis Criterion**:

For a Hamiltonian system, if the **differential Galois group** of the Normal Variational Equations (NVE) around a periodic orbit is non-abelian, the system is **provably non-integrable**.

**Strategy**: Show that 3-body problem is non-integrable downstairs → any new integral must live upstairs.

#### Task 4.2.1: Variational Equations

1. Select test periodic orbits (e.g., Lagrange equilateral, Figure-8)
2. Compute **Normal Variational Equations** (NVE):
   - Linearize Hamiltonian flow around periodic orbit
   - Reduce to normal directions (perpendicular to orbit)

#### Task 4.2.2: Differential Galois Group

Use **Kovacic algorithm** or similar to compute Galois group:
- If identity component is non-abelian → non-integrable
- If abelian → integrable (would be surprising!)

#### Task 4.2.3: Interpretation

**Expected Result**: Galois group is non-abelian (SL(2, ℂ) or similar)
- ✅ **Confirms**: 3BP is non-integrable downstairs (consistent with Bruns/Poincaré)
- ✅ **Validates**: Any integral from WP3 is a genuine lift-integral

**Unexpected Result**: Galois group is abelian
- ⚠️ **Surprising**: Would suggest missed integrability downstairs
- 🔄 **Action**: Re-examine WP3 results, check if integral reduces to downstairs

**Deliverables**:
- Galois group computation for 3+ periodic orbits
- Proof of downstairs non-integrability
- Validation that WP3 integrals are lift-specific

---

### WP 4.3: Numerical Robustness and Generalization

**Duration**: 10-12 days

**Purpose**: Demonstrate that conservation holds **universally** across:
- All mass ratios
- All energy regimes
- Chaotic and regular regions
- Long time scales (10^4-10^6 periods)
- Near-collision scenarios

**The Statistical Validation Paradigm**:

Instead of proving conservation for all states (impossible numerically), we **probabilistically certify** conservation over a representative sample.

#### Task 4.3.1: Monte Carlo Parameter Sweep

**Sampling Strategy**:
- **Mass ratios**: 30 logarithmically spaced values in [10^{-3}, 0.5]
- **Energies**: 15 values bracketing Lagrange point energies
- **Angular momenta**: 10 values from near-zero to high rotation
- **Initial conditions**: 100-1000 per (mass, E, L) combination

**Total**: ~10^5 to 10^6 trajectories

**Per-Trajectory Test**:
1. Integrate for $t \in [0, T]$ where $T = 10^4$ to $10^6$ orbital periods
2. Monitor $\Delta I(t) = I(t) - I(0)$
3. Compute relative drift: $\epsilon_I = \sup_t |\Delta I(t)| / |I(0)|$

**Acceptance**:
- $\epsilon_I < 10^{-6}$ for >95% of trajectories
- $\epsilon_I < 10^{-8}$ for >80% of trajectories

#### Task 4.3.2: Stress Testing

**Collision Scenarios**:
- Initialize near binary collision: $r_{12} < 10^{-3}$
- Use KS regularization to integrate through collision
- Verify $I$ conserved across encounter

**Chaotic Regions**:
- Select initial conditions with positive Lyapunov exponent
- Verify conservation despite sensitive dependence

**High Eccentricity**:
- Test orbits with perihelion/aphelion ratio > 100:1

#### Task 4.3.3: Long-Time Invariance

**Shadow Hamiltonian Analysis**:
- Symplectic integrators conserve a nearby "shadow" Hamiltonian $H_{\text{shadow}}$
- Verify: $|\Delta I| \approx |I(H) - I(H_{\text{shadow}})|$
- **Acceptance**: Drift in $I$ is consistent with integrator error

**Comparison Metric**:
$$
\frac{\sup_t |\Delta I(t)|}{\sup_t |\Delta E(t)|} \approx O(1)
$$

If $I$ drifts much faster than $E$, it's not conserved!

#### Task 4.3.4: Chaos-Curvature Correlation

**Hypothesis**: True integrals are conserved in **both** regular and chaotic regions.

**Test**:
1. Compute Lyapunov exponent $\lambda_{\max}$ for each trajectory
2. Classify: Regular ($\lambda < 10^{-4}$) vs. Chaotic ($\lambda > 10^{-2}$)
3. Compare conservation error distributions

**Expected**: Conservation error independent of chaos indicator

**Deliverables**:
- Statistical validation report (10^5+ trajectories)
- Stress test results (collisions, chaos, eccentricity)
- Long-time drift analysis with error budgets
- Correlation studies (chaos, curvature, mass ratios)

---

## Mathematical Framework

### Liouville Integrability Conditions

For an $n$-DOF Hamiltonian system to be **Liouville integrable**, it must possess $n$ functionally independent integrals $I_1 = H, I_2, \ldots, I_n$ satisfying:

1. **Conservation**: $\frac{dI_k}{dt} = \{I_k, H\} = 0$ for all $k$
2. **Involution**: $\{I_j, I_k\} = 0$ for all $j, k$
3. **Functional Independence**: $\text{rank}(dI_1 \wedge \cdots \wedge dI_n) = n$ almost everywhere

**For the Lifted 3-Body Problem**:

| Coordinate System | DOF | Known Integrals | Needed | Gap |
|-------------------|-----|-----------------|--------|-----|
| Downstairs (planar) | 3 | E, L | 3 | 1 |
| S¹ Bundle | 4 | E, L, p_θ? | 4 | 0 or 1 |
| KS Spinor (constrained) | 9 | E, L, ... | 9 | many |

### Poisson Brackets

**Definition**:
$$
\{f, g\} = \sum_{i=1}^n \left( \frac{\partial f}{\partial q_i} \frac{\partial g}{\partial p_i} - \frac{\partial f}{\partial p_i} \frac{\partial g}{\partial q_i} \right)
$$

**Properties**:
- Antisymmetry: $\{f, g\} = -\{g, f\}$
- Leibniz rule: $\{fg, h\} = f\{g,h\} + g\{f,h\}$
- Jacobi identity: $\{f, \{g, h\}\} + \{g, \{h, f\}\} + \{h, \{f, g\}\} = 0$

**Conservation**: If $\{I, H\} = 0$, then $\frac{dI}{dt} = 0$ along trajectories.

### Morales-Ramis Criterion

**Theorem** (Morales-Ramis, 1999):

If a Hamiltonian system with $n$ DOF is integrable with $n$ independent meromorphic first integrals, then the identity component of the differential Galois group of the Normal Variational Equation is **abelian** for any non-equilibrium solution.

**Contrapositive** (our use):

If the Galois group is **non-abelian**, the system is **non-integrable**.

**Computational Tool**: **Kovacic Algorithm** (deterministic) for linear ODEs with rational coefficients.

---

## Decision Trees

### Decision Point 1: After WP 4.1 (Analytical Vetting)

**Question**: Do candidates pass symbolic/numerical conservation tests?

```
Candidates pass WP 4.1?
├─ YES (all tests passed)
│  └─→ Proceed to WP 4.2 & 4.3 in parallel
│       Candidates are "analytically promising"
│
├─ PARTIAL (some pass, some fail)
│  └─→ Categorize results:
│       ├─ Passed: Proceed to WP 4.2/4.3
│       └─ Failed: Document why (useful negative result)
│
└─ NO (all failed)
   └─→ NEGATIVE RESULT
        Action: Proceed to WP 4.2 to confirm downstairs non-integrability
        Document: WP3 search was comprehensive but yielded no integrals
        Still publishable: "Rigorous bounds on non-existence"
```

---

### Decision Point 2: After WP 4.2 (Morales-Ramis)

**Question**: Is the downstairs problem non-integrable?

```
Galois group non-abelian?
├─ YES (expected)
│  └─→ VALIDATION: Downstairs is provably non-integrable
│       ├─ If WP3 found integrals: They genuinely live upstairs ✓
│       └─ If WP3 found nothing: Consistent with theory ✓
│
└─ NO (Galois group abelian)
   └─→ SURPRISE: Suggests integrable structure downstairs!
        Action: Re-examine WP3 candidates
        Question: Did we miss a downstairs integral?
        Investigate: Can upstairs integral be projected down?
```

---

### Decision Point 3: After WP 4.3 (Numerical Robustness)

**Question**: Do candidates pass statistical validation?

```
>95% trajectories satisfy ε_I < 10^-6?
├─ YES
│  └─→ SUCCESS: Publication-ready integral(s) discovered!
│       Proceed to WP5:
│       ├─ Formal proof construction
│       ├─ Manuscript preparation
│       └─ Reproducibility package
│
├─ PARTIAL (70-95% success rate)
│  └─→ REGIME-SPECIFIC INTEGRAL
│       Characterize: Which parameter regions work?
│       Investigate: Approximate integral? Adiabatic invariant?
│       Still publishable: "Conditional integrability"
│
└─ NO (<70% success)
   └─→ NUMERICAL ARTIFACT
        Conclusion: WP3 candidates were spurious
        Document: Negative result (still valuable)
        Analyze: Why did WP3 methods fail?
```

---

## Quality Metrics

### Acceptance Thresholds

| Metric | Minimum | Target | Exceptional |
|--------|---------|--------|-------------|
| **Conservation** $\|\{I, H\}\|$ | < 10^{-10} | < 10^{-12} | = 0 (symbolic) |
| **Involution** $\|\{I, J\}\|$ | < 10^{-8} | < 10^{-10} | = 0 (symbolic) |
| **Independence** (Jacobian rank) | 99% samples | 99.9% | 100% |
| **Long-time drift** $\epsilon_I$ | < 10^{-5} | < 10^{-8} | < 10^{-12} |
| **Monte Carlo success** | 90% | 95% | 99% |

### Confidence Levels

**High Confidence** (publishable):
- Symbolic conservation proof OR
- Numerical conservation < 10^{-12} over 10^6 periods on 10^5 trajectories

**Medium Confidence** (conditional result):
- Numerical conservation < 10^{-8} over 10^4 periods
- Valid in specific parameter regime

**Low Confidence** (negative result):
- Conservation fails in >10% of cases
- Drift exceeds integrator error

---

## Handoff to WP5

### Outputs from WP4

**Positive Result** (integral(s) validated):
1. **Analytical Certification**:
   - Symbolic expressions for integrals
   - Poisson bracket proofs (symbolic or numerical)
   - Independence proof (Jacobian rank)

2. **Numerical Certification**:
   - Statistical validation report (10^5 trajectories)
   - Error distributions and confidence intervals
   - Stress test results

3. **Theoretical Validation**:
   - Morales-Ramis proof of downstairs non-integrability
   - Explanation of lift mechanism

**Negative Result** (no integrals found):
1. **Proof of Comprehensive Search**:
   - WP3 methodology completeness
   - Morales-Ramis confirms non-integrability
   - Bounds on search space

2. **Documentation**:
   - What was tried and why it failed
   - Limitations of current methods

### WP5 Entry Criteria

**For Positive Results**:
- [ ] At least one candidate passed all WP 4.1-4.3 tests
- [ ] Symbolic or numerical conservation to < 10^{-10}
- [ ] Statistical validation on >10^5 trajectories
- [ ] Morales-Ramis test confirms lift-integrability

**For Negative Results**:
- [ ] Morales-Ramis confirms downstairs non-integrability
- [ ] WP3 search documented as comprehensive
- [ ] Bounds on non-existence characterized

---

## Timeline and Dependencies

### Critical Path

```
WP3 Complete → Candidates Available
    ↓
Week 1-2: WP 4.1 (Analytical Vetting)
    ↓
    ├─→ Week 2-3: WP 4.2 (Morales-Ramis) [Can start after 4.1]
    └─→ Week 2-4: WP 4.3 (Numerical Robustness) [Parallel with 4.2]
    ↓
Week 4-5: Consolidation & Analysis
    ↓
WP5 (Publication)
```

**Total Duration**: 4-5 weeks (23-29 days with efficient parallelization)

### Parallelization Strategy

**Can Run in Parallel**:
- WP 4.2 and WP 4.3 (after WP 4.1 completes)
- Within WP 4.3: Different parameter sweeps (mass ratios, energies)

**Must Run Sequentially**:
- WP 4.1 first (filters candidates before expensive tests)
- WP 4.1 → WP 4.2 & 4.3
- WP 4.2 & 4.3 → WP5

---

## Risk Assessment

### Scientific Risks

**Risk 1: All Candidates Fail Validation**
- **Probability**: Medium (30%)
- **Impact**: Medium (negative result, still publishable)
- **Mitigation**:
  - Rigorous WP3 methods reduce this risk
  - Negative result proves bounds on non-integrability
  - Still advances field knowledge

**Risk 2: Morales-Ramis Test Ambiguous**
- **Probability**: Low (10%)
- **Impact**: Medium
- **Mitigation**:
  - Test multiple periodic orbits
  - Use multiple computational methods
  - Consult differential Galois theory experts

**Risk 3: Numerical Instabilities Mask Conservation**
- **Probability**: Low (15%)
- **Impact**: High (false negative)
- **Mitigation**:
  - Use high-precision arithmetic (quad precision)
  - Multiple integrators (cross-validation)
  - Shadow Hamiltonian analysis

### Implementation Risks

**Risk 4: Computational Cost Prohibitive**
- **Probability**: Medium (25%)
- **Impact**: Medium (timeline延delay)
- **Mitigation**:
  - HPC resources secured
  - Efficient sampling (stratified, importance)
  - Can reduce to 10^4 trajectories if needed

**Risk 5: Symbolic Computation Intractable**
- **Probability**: Medium (40%)
- **Impact**: Low (fall back to numerical)
- **Mitigation**:
  - Numerical Poisson brackets are acceptable
  - Semi-symbolic methods (numerical coefficients)

---

## Success Criteria

### Minimum Success
- [ ] All WP3 candidates tested against WP 4.1 criteria
- [ ] Morales-Ramis test performed on 3+ periodic orbits
- [ ] Statistical validation on >10^4 trajectories
- [ ] Results (positive or negative) documented

### Target Success
- [ ] At least one candidate passes all validation stages
- [ ] Conservation < 10^{-10} symbolically or numerically
- [ ] Statistical validation on >10^5 trajectories with 95% success
- [ ] Complete analytical and numerical certification

### Stretch Success
- [ ] Multiple independent integrals validated
- [ ] Symbolic conservation proofs
- [ ] Characterization of integrable submanifolds
- [ ] Publication in top-tier journal (Nature, Science, PRL)

---

## References

### Integrability Theory

1. **Bruns' Theorem**:
   - Bruns, H. "Über die Integrale des Vielkörper-Problems" (1887)

2. **Poincaré's Results**:
   - Poincaré, H. "Les Méthodes Nouvelles de la Mécanique Céleste" (1892-1899)

3. **Liouville-Arnold Theorem**:
   - Arnold, V. I. "Mathematical Methods of Classical Mechanics" (1989)

### Morales-Ramis Theory

4. **Original Papers**:
   - Morales-Ruiz, J. J. & Ramis, J. P. "Galoisian obstructions to integrability" (1999)
   - Morales-Ruiz, J. J. & Ramis, J. P. "A note on the non-integrability of some Hamiltonian systems" (2001)

5. **Differential Galois Theory**:
   - van der Put, M. & Singer, M. F. "Galois Theory of Linear Differential Equations" (2003)
   - Kovacic, J. "An algorithm for solving second order linear homogeneous differential equations" (1986)

6. **Applications to 3BP**:
   - Maciejewski, A. & Przybylska, M. "Non-integrability of restricted two body problems in constant curvature spaces" (2003)
   - Duarte, L. et al. "Testing the Morales-Ramis criterion" (2010)

### Numerical Validation

7. **Shadow Hamiltonians**:
   - Hairer, E. et al. "Geometric Numerical Integration" (2006)
   - McLachlan, R. & Quispel, G. "What kinds of dynamics are there?" (2014)

8. **Chaos Indicators**:
   - Cincotta, P. & Simó, C. "Simple tools to study global dynamics" (2000)
   - Maffione, N. et al. "A comparison of different indicators of chaos" (2011)

---

## Summary

Work Package 4 is the **proving ground** where candidate integrals from WP3 are subjected to the most rigorous validation possible. By combining symbolic analysis, differential Galois theory, and large-scale numerical validation, WP4 ensures that **only genuine discoveries** proceed to publication.

**Key Innovations**:
- First application of Morales-Ramis test to lift-integrability hypothesis
- Statistical validation framework for conserved quantities
- Defensive falsification to protect credibility

**Expected Outcome**: Either:
1. ✅ **Publication-ready integral(s)** with complete certification, OR
2. 📊 **Rigorous negative result** establishing bounds on integrability

Both outcomes advance the field and are publishable.

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Overview - Ready for Task Planning
**Next Documents**: Task 4.1, 4.2, 4.3 Implementation Plans
