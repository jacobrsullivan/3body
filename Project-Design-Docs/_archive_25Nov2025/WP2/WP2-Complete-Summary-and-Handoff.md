# Work Package 2: Geometric Reduction and Shape Space Analysis
## Complete Summary and Handoff to WP3

**Status**: Design Complete - Ready for Implementation
**Documentation Version**: 1.0
**Last Updated**: 2025-11-13
**Next Phase**: Implementation → WP3 Invariant Discovery

---

## Executive Summary

Work Package 2 establishes the **geometric foundations** for investigating lift-integrability in the three-body problem. Through a systematic progression from coordinate systems to symplectic reduction to lift constructions, WP2 creates the infrastructure necessary to search for hidden integrals of motion in extended phase spaces.

### Core Hypothesis

**Lift-Integrability Hypothesis**: While the three-body problem is non-integrable in the standard (reduced) phase space, it may become integrable "upstairs" in appropriately constructed higher-dimensional spaces that respect the system's geometric structure.

### WP2 Architecture

```
WP2: Geometric Foundations (5 components, ~48-57 days total)
│
├── Task 2.1: Reduced Space Geometry (26-28 days)
│   ├── 2.1.1: Coordinates & Reduction (12 days) ✅ DOCUMENTED
│   ├── 2.1.2: Connection & Curvature (10 days) ✅ DOCUMENTED
│   └── 2.1.3: JM Metric & Chaos (8 days) ✅ DOCUMENTED
│
├── WP 2.2: S¹ Untwisting Lift (12 days) ✅ DOCUMENTED
│   └── Minimal dimensional increase (4D bundle)
│
└── WP 2.3: KS-Spinor Lift (15 days) ✅ DOCUMENTED
    └── Regularizing lift with collision handling (12D spinor space)
```

---

## Table of Contents

1. [Component Overview](#component-overview)
2. [Mathematical Framework](#mathematical-framework)
3. [Implementation Summary](#implementation-summary)
4. [Decision Tree and Outcomes](#decision-tree-and-outcomes)
5. [Deliverables Checklist](#deliverables-checklist)
6. [Quality Metrics](#quality-metrics)
7. [Handoff to WP3](#handoff-to-wp3)
8. [Risk Assessment](#risk-assessment)
9. [Scientific Validation Plan](#scientific-validation-plan)
10. [References and Resources](#references-and-resources)

---

## Component Overview

### Task 2.1.1: Coordinate Systems and Reduction

**Duration**: 12 days | **Documentation**: 6,379 lines (5 files)

**Purpose**: Establish coordinate transformation infrastructure and implement Marsden-Weinstein symplectic reduction.

**Components**:
- **Part A**: Three coordinate systems (Cartesian, Jacobi, Shape Space)
- **Part B**: Translation and rotation reduction
- **Part C**: Integration with WP1 infrastructure
- **Part D**: Documentation and tutorials

**Key Outputs**:
- Shape space coordinates $(r_{12}, r_{23}, r_{31})$ with validated transformations
- Reduced phase space (18D → 12D planar, 7D after reduction)
- Connection to WP1 integrators

**Status**: Complete design, ready for implementation

---

### Task 2.1.2: Connection and Curvature

**Duration**: 10 days | **Documentation**: 950 lines

**Purpose**: Compute the mechanical connection one-form $\mathcal{A}$ and curvature $\mathcal{F} = d\mathcal{A}$ that encode geometric obstruction to integrability.

**Components**:
- **Part A**: Connection form computation via locked inertia tensor
- **Part B**: Curvature via exterior derivative
- **Part C**: Numerical implementation with optimization
- **Part D**: Stokes' theorem validation

**Key Outputs**:
- Connection evaluator: <100 μs per point
- Curvature evaluator: <1 ms per point
- Validated via $\oint \mathcal{A} = \int \mathcal{F}$ (Stokes)

**Scientific Significance**:
- $\mathcal{F} \neq 0$ proves non-integrability "downstairs"
- Motivates "upstairs" lift constructions

**Status**: Complete design, ready for implementation

---

### Task 2.1.3: Jacobi-Maupertuis Metric Analysis

**Duration**: 8 days | **Documentation**: 945 lines

**Purpose**: Compute JM metric on shape space and analyze scalar curvature as a chaos diagnostic.

**Components**:
- **Part A**: JM metric $g_{JM} = 2(E - V_{eff}) g_{shape}$ and Christoffel symbols
- **Part B**: Ricci and scalar curvature computation
- **Part C**: Visualization (ellipsoids, landscapes)
- **Part D**: Chaos-curvature correlation: $R < 0 \Leftrightarrow \lambda_{max} > 0$

**Key Outputs**:
- Metric tensor evaluator
- Scalar curvature $R$ field
- Correlation analysis with 1000 sample trajectories

**Scientific Significance**:
- Negative curvature provides **geometric explanation for chaos**
- Coordinate-invariant chaos diagnostic

**Status**: Complete design, ready for implementation

---

### WP 2.2: S¹ Untwisting Lift

**Duration**: 12 days | **Documentation**: 1,095 lines

**Purpose**: Construct minimal S¹ principal bundle over shape space to "untwist" the magnetic connection.

**Mathematical Structure**:
- Bundle: $P = S \times S^1$ (4D total space over 3D shape space)
- Extended symplectic form: $\widetilde{\omega} = \omega_{shape} + d\theta \wedge d(L \cdot \mathcal{A})$
- Lifted Hamiltonian: $\widetilde{H}(s, \theta) = H_{red}(s)$ (independent of $\theta$!)

**Key Innovation**: Fiber momentum $p_\theta$ is conserved—**potential third integral**

**Components**:
- **Part A**: Principal bundle construction (charts, transitions)
- **Part B**: Extended symplectic form (verify $d\widetilde{\omega} = 0$)
- **Part C**: Lifted dynamics integration
- **Part D**: Integrability test (3 integrals: $E$, $L$, $p_\theta$)

**Decision Point**:
- **If integrable**: Construct action-angle coordinates → WP3
- **If non-integrable**: Document obstruction → WP2.3 (KS lift)

**Status**: Complete design, ready for implementation

---

### WP 2.3: KS-Spinor Lift

**Duration**: 15 days | **Documentation**: 1,248 lines

**Purpose**: Apply Kustaanheimo-Stiefel spinor regularization pairwise to all three body pairs, creating a 12D → 9D constrained system.

**Mathematical Structure**:
- Spinor embedding: $\mathbf{r}_{ij} = L(\mathbf{u}_{ij}) \mathbf{u}_{ij}$ where $\mathbf{u}_{ij} \in \mathbb{R}^4$
- Bilinear relation: $r_{ij} = |\mathbf{u}_{ij}|^2$
- Fictitious time: $dt/ds = r$ (regularizes collisions)

**Key Innovation**:
- **Collision regularization**: Integrate smoothly through $r_{ij} \to 0$
- **SU(2) structure**: Spinors form representation of SU(2) (may reveal symmetries)
- **Higher dimensionality**: 12D config space (vs. 4D in S¹ lift) - more room for integrals

**Components**:
- **Part A**: KS transformation for single pair (Levi-Civita matrix)
- **Part B**: Pairwise application to 3BP (3 spinors, 6 constraints)
- **Part C**: Constrained Hamiltonian dynamics (RATTLE integrator)
- **Part D**: Integrability analysis + comparison with S¹ lift

**Decision Point**:
- **If integrable**: Proceed to WP3 with KS coordinates
- **If non-integrable but regularizes**: Use for WP3 near-collision regions
- **If no advantage**: Document limits of lift-integrability approach

**Status**: Complete design, ready for implementation

---

## Mathematical Framework

### The Reduction Pipeline

```
Original Phase Space (18D)
    ↓ [Translation Reduction]
Barycentric Phase Space (15D)
    ↓ [Rotation Reduction]
Reduced Phase Space (Shape Space, 12D planar / 7D after fixing L)
    ↓ [Compute Connection A & Curvature F]
Obstruction: F ≠ 0 (non-integrable)
    ↓ [Lift Construction]
    ├─→ S¹ Bundle (4D base + 1D fiber = 5D × 2 = 10D phase space)
    └─→ KS Spinor (9D base [constrained from 12D] × 2 = 18D phase space)
        ↓
    Search for integrals "upstairs"
```

### Key Geometric Objects

| Object | Symbol | Dimension | Significance |
|--------|--------|-----------|--------------|
| **Configuration Space** | $\mathbb{R}^9$ | 9 | Three bodies in 3D |
| **Phase Space** | $T^*\mathbb{R}^9$ | 18 | Positions + momenta |
| **Barycentric Frame** | $\{\sum m_i r_i = 0\}$ | 15 | Remove COM translation |
| **Shape Space** | $S$ | 3 (planar) | After rotation reduction |
| **Connection** | $\mathcal{A}$ | 1-form | "Magnetic twist" |
| **Curvature** | $\mathcal{F} = d\mathcal{A}$ | 2-form | Obstruction ($\neq 0$) |
| **JM Metric** | $g_{JM}$ | Riemannian | Geodesics = trajectories |
| **Scalar Curvature** | $R$ | Scalar | $R < 0 \Leftrightarrow$ chaos |
| **S¹ Bundle** | $P = S \times S^1$ | 4 | Untwist connection |
| **KS Spinor Space** | $\mathbb{R}^{12}$ (constrained) | 9 | Regularize collisions |

---

## Implementation Summary

### Development Sequence

```
Week 1-2: Task 2.1.1 (Coordinates & Reduction)
    → Establish coordinate transformation library
    → Implement Marsden-Weinstein reduction
    → Validate against known solutions (Lagrange, Figure-8)

Week 3: Task 2.1.2 (Connection & Curvature)
    → Compute mechanical connection A
    → Compute curvature F via exterior derivative
    → Verify Stokes' theorem numerically

Week 4: Task 2.1.3 (JM Metric)
    → Implement Jacobi-Maupertuis metric
    → Compute scalar curvature R
    → Validate chaos-curvature correlation

Week 5-6: WP 2.2 (S¹ Lift)
    → Construct principal S¹ bundle
    → Implement lifted dynamics
    → Test for integrability (3 integrals?)

Week 7-8: WP 2.3 (KS Lift) [If needed]
    → Implement KS transformation
    → Pairwise spinor coordinates
    → Constrained integration (RATTLE)
    → Compare with S¹ lift results
```

### Critical Path

**Must Complete Sequentially**:
1. Task 2.1.1 → All others depend on coordinate systems
2. Task 2.1.2 → Required input for S¹ lift (connection $\mathcal{A}$)
3. Task 2.1.3 → Can run in parallel with 2.1.2
4. WP 2.2 → Must complete before deciding on WP 2.3

**Can Parallelize**:
- Task 2.1.2 and 2.1.3 (after 2.1.1)
- Parts A/B/C within each task (after architecture design)

---

## Decision Tree and Outcomes

### Decision Point 1: Connection Curvature (After Task 2.1.2)

**Question**: What is $|\mathcal{F}|$ in typical three-body configurations?

**Possible Outcomes**:

```
├─ F ≈ 0 (flat connection)
│  └─→ SURPRISE: Integrable "downstairs"!
│       Action: Construct action-angle coordinates directly
│       Skip lifts, proceed to WP3
│
└─ F ≠ 0 (non-flat)
   └─→ EXPECTED: Non-integrable as predicted
        Action: Proceed with lift constructions
        Continue to WP 2.2
```

**Expected**: $\mathcal{F} \neq 0$ (confirming non-integrability)

---

### Decision Point 2: JM Scalar Curvature (After Task 2.1.3)

**Question**: Does $R < 0$ correlate with chaos ($\lambda_{max} > 0$)?

**Possible Outcomes**:

```
├─ Strong correlation (r > 0.7)
│  └─→ SUCCESS: Geometric chaos diagnostic validated
│       Implication: Curvature is fundamental to 3BP dynamics
│       Use R field to guide symmetry search in WP3
│
├─ Weak correlation (0.3 < r < 0.7)
│  └─→ PARTIAL: Some geometric influence on chaos
│       Investigate: Direction-dependent (sectional) curvature
│
└─ No correlation (r < 0.3)
   └─→ UNEXPECTED: Curvature not main chaos driver
        Investigate: Other geometric quantities (connection, torsion)
```

**Expected**: Strong correlation (validates geometric approach)

---

### Decision Point 3: S¹ Lift Integrability (After WP 2.2)

**Question**: Are $(E, L, p_\theta)$ three independent integrals in involution?

**Possible Outcomes**:

```
├─ YES: Integrable on S¹ bundle
│  └─→ HYPOTHESIS CONFIRMED!
│       ├─ Construct action-angle coordinates
│       ├─ Characterize solution structure (tori foliation)
│       ├─ Skip WP 2.3 (not needed)
│       └─ Proceed to WP3: Use S¹ coordinates for invariant discovery
│
├─ PARTIAL: p_θ conserved but system still chaotic
│  └─→ Interesting: One new integral, but not enough
│       ├─ Document partial integrability
│       ├─ Proceed to WP 2.3 (try higher-dimensional lift)
│       └─ May be super-integrable in subregions
│
└─ NO: Non-integrable even on bundle
   └─→ S¹ lift insufficient
        ├─ Analyze: Why did fiber momentum fail to help?
        ├─ Compute residual obstruction
        └─ Proceed to WP 2.3 (KS lift—last resort)
```

**Expected**: Either full or partial integrability (hypothesis: YES or PARTIAL)

---

### Decision Point 4: KS Lift Analysis (After WP 2.3)

**Question**: Does spinor representation reveal additional integrals?

**Possible Outcomes**:

```
├─ YES: More integrals in KS coordinates
│  └─→ VALIDATION: Higher dimension helps!
│       ├─ Characterize spinor integrals
│       ├─ Check: SU(2) representation theory connection
│       └─ Proceed to WP3 with KS coordinates
│
├─ COLLISION REGULARIZATION ONLY
│  └─→ USEFUL: No new integrals, but smooth near collisions
│       ├─ Use KS for near-collision trajectories in WP3
│       ├─ Switch coordinates: S¹ (generic) ↔ KS (near-collision)
│       └─ Proceed to WP3 with hybrid approach
│
└─ NO ADVANTAGE
   └─→ LIMIT REACHED: Even KS doesn't help integrability
        ├─ Document: 3BP is "truly" non-integrable (no lift works)
        ├─ Implication: Hidden symmetries (if any) are very subtle
        └─ Proceed to WP3 with best available coordinates
           (probably S¹ if p_θ is conserved)
```

**Expected**: At minimum, collision regularization benefit

---

## Deliverables Checklist

### Task 2.1.1: Coordinate Systems and Reduction

**Code Deliverables**:
- [ ] `src/python/coordinates/cartesian.py` - Cartesian state, energy, momentum
- [ ] `src/python/coordinates/jacobi.py` - Jacobi coordinates, transformations
- [ ] `src/python/coordinates/shape_space.py` - Distance coordinates
- [ ] `src/python/reduction/translation_reduction.py` - Barycentric projection
- [ ] `src/python/reduction/rotation_reduction.py` - Orientation fixing
- [ ] `src/python/integrators/threebody.py` - 3BP integrator framework

**Validation**:
- [ ] Round-trip transform tests (error < 1e-13)
- [ ] Lagrange equilibrium preservation (100+ periods)
- [ ] Figure-8 periodicity (error < 1e-6 after one period)
- [ ] Conservation laws (E, P, L drift < 1e-12)

**Documentation**:
- [ ] API reference (Sphinx-generated)
- [ ] Tutorial notebook: "Coordinate Systems for 3BP"
- [ ] Technical report section (LaTeX)

---

### Task 2.1.2: Connection and Curvature

**Code Deliverables**:
- [ ] `src/python/geometry/connection.py` - Connection one-form evaluator
- [ ] `src/python/geometry/curvature.py` - Curvature two-form computation
- [ ] `src/python/geometry/locked_inertia.py` - Locked inertia tensor
- [ ] `src/python/visualization/connection_field.py` - Vector field plots
- [ ] `src/python/visualization/curvature_heatmap.py` - Curvature magnitude

**Validation**:
- [ ] Stokes' theorem: $\oint \mathcal{A} = \int \mathcal{F}$ (error < 1e-10)
- [ ] Gauge invariance under orientation changes
- [ ] Two-body limit: connection → known formula
- [ ] Equal mass symmetry

**Documentation**:
- [ ] Technical report section: "Geometric Obstruction"
- [ ] Visualization gallery (publication figures)

---

### Task 2.1.3: JM Metric Analysis

**Code Deliverables**:
- [ ] `src/python/geometry/jm_metric.py` - JM metric tensor
- [ ] `src/python/geometry/christoffel.py` - Christoffel symbols
- [ ] `src/python/geometry/riemann_curvature.py` - Scalar curvature
- [ ] `src/python/analysis/chaos_indicators.py` - Lyapunov exponents
- [ ] `src/python/visualization/curvature_landscape.py` - 3D curvature plots

**Validation**:
- [ ] Kepler limit: $R \to 0$ as $m_3 \to 0$
- [ ] Equal mass symmetry validation
- [ ] Chaos-curvature correlation: Pearson $r > 0.7$
- [ ] Classification accuracy > 80% ($R$ sign predicts chaos)

**Documentation**:
- [ ] Technical report section: "Geometric Origin of Chaos"
- [ ] Scatter plots: $R$ vs. $\lambda_{max}$

---

### WP 2.2: S¹ Lift

**Code Deliverables**:
- [ ] `src/python/lifts/s1_bundle.py` - Principal S¹ bundle
- [ ] `src/python/lifts/extended_symplectic.py` - Extended form $\widetilde{\omega}$
- [ ] `src/python/lifts/lifted_hamiltonian.py` - Bundle Hamiltonian
- [ ] `src/python/integration/bundle_integrator.py` - Integration on bundle
- [ ] `src/python/analysis/integral_search.py` - Search for integrals

**Validation**:
- [ ] $d\widetilde{\omega} = 0$ (closedness)
- [ ] $p_\theta$ conserved (drift < 1e-12)
- [ ] Projection: $\pi(\text{lifted}) = \text{reduced}$ (error < 1e-10)
- [ ] Involution test: $\{E, L\}$, $\{E, p_\theta\}$, $\{L, p_\theta\} = 0$

**Documentation**:
- [ ] Technical report section: "S¹ Lift Construction"
- [ ] Decision: Integrable? Partial? Non-integrable?

---

### WP 2.3: KS-Spinor Lift

**Code Deliverables**:
- [ ] `src/python/regularization/ks_transform.py` - KS transformation
- [ ] `src/python/regularization/levi_civita.py` - Levi-Civita matrix
- [ ] `src/python/lifts/ks_pairwise.py` - Pairwise spinor system
- [ ] `src/python/integration/constrained_integrator.py` - RATTLE integrator
- [ ] `src/python/analysis/comparison_s1_vs_ks.py` - Lift comparison

**Validation**:
- [ ] Bilinear relation: $r = |\mathbf{u}|^2$ (error < 1e-12)
- [ ] Round-trip: Cartesian → KS → Cartesian (error < 1e-12)
- [ ] Constraint satisfaction during integration (drift < 1e-10)
- [ ] Collision passage: integrate through $r_{ij} < 10^{-5}$

**Documentation**:
- [ ] Technical report section: "KS Spinor Regularization"
- [ ] Comparison report: S¹ vs. KS (which is better? when?)

---

## Quality Metrics

### Code Quality

**Target Metrics**:
- Test coverage: > 95%
- Docstring coverage: 100% (all public APIs)
- Type hints: 100% (Python 3.10+)
- Lint compliance: Zero warnings (pylint, mypy)

**Performance**:
- Coordinate transforms: < 10 μs per operation
- Connection evaluation: < 100 μs per point
- Curvature evaluation: < 1 ms per point
- Metric evaluation: < 10 μs per point
- Integration: > 1000 steps/second

**Numerical Precision**:
- Round-trip transform errors: < 1e-13
- Conservation law drift: < 1e-12
- Constraint satisfaction: < 1e-10
- Stokes' theorem error: < 1e-10

---

### Scientific Validation

**Theoretical Properties**:
- [ ] Symplectic structure preserved (all transformations)
- [ ] Gauge invariance (connection under orientation changes)
- [ ] Stokes' theorem (connection and curvature)
- [ ] Bianchi identity ($d\mathcal{F} = 0$)
- [ ] Closedness of extended form ($d\widetilde{\omega} = 0$)

**Numerical Validation**:
- [ ] Known solutions reproduced (Lagrange, Figure-8)
- [ ] Limiting cases correct (Kepler, two-body)
- [ ] Symmetries respected (equal masses, permutations)
- [ ] Collision handling (KS regularization)

**Cross-Validation**:
- [ ] Multiple coordinate systems agree (Cartesian ↔ Jacobi ↔ Shape)
- [ ] Independent curvature computations match (numerical ↔ symbolic)
- [ ] Chaos indicators consistent ($R$, $\mathcal{F}$, $\lambda_{max}$)

---

## Handoff to WP3

### Context for WP3: Invariant Discovery

WP3 will search for **additional integrals of motion** using the infrastructure built in WP2.

**Key Questions for WP3**:
1. **Which coordinate system to use?**
   - Answer depends on WP2 outcomes (S¹ if integrable, KS if regularization needed)
2. **What symmetries to exploit?**
   - Use curvature field $\mathcal{F}$ to guide search (look where $|\mathcal{F}|$ is small)
3. **What chaos threshold?**
   - Use JM scalar curvature $R$ to classify regions (avoid $R \ll 0$)

### Deliverables to WP3

**From Task 2.1.1**:
- Coordinate transformation library (all systems)
- Reduced phase space representation
- High-precision integrators

**From Task 2.1.2**:
- Connection field $\mathcal{A}(s)$ (identifies "magnetic" regions)
- Curvature field $\mathcal{F}(s)$ (obstruction map)

**From Task 2.1.3**:
- JM metric $g_{JM}(s, E)$ (geodesic structure)
- Scalar curvature $R(s, E)$ (chaos map)
- Chaos classification (regular vs. chaotic regions)

**From WP 2.2**:
- S¹ bundle coordinates (if useful)
- Fiber momentum $p_\theta$ (if conserved)
- Integrability classification

**From WP 2.3**:
- KS spinor coordinates (for near-collisions)
- Collision-regularized trajectories
- SU(2) symmetry analysis

### WP3 Strategy Decision Matrix

| WP2 Outcome | WP3 Strategy |
|-------------|--------------|
| **S¹ integrable** | Use action-angle coordinates; search for perturbative integrals |
| **S¹ partial** | Focus on integrable submanifold; characterize boundary |
| **KS reveals integrals** | Use spinor symmetries; investigate SU(2) structure |
| **Neither integrable** | Hybrid: S¹ (generic) + KS (collisions); focus on approximate integrals |
| **F ≈ 0 in regions** | Target low-curvature regions for integral search |
| **R < 0 everywhere** | Focus on short-term integrals; study chaotic sea structure |

---

## Risk Assessment

### Scientific Risks

**Risk 1: No Lift Provides Integrability**
- **Probability**: Medium (30-40%)
- **Impact**: High (challenges hypothesis)
- **Mitigation**:
  - Negative result is scientifically valid
  - Document what was tried and why it failed
  - Provides bounds on where integrability can exist

**Risk 2: Computational Cost Prohibitive**
- **Probability**: Low (< 20%)
- **Impact**: Medium
- **Mitigation**:
  - Performance targets built into design
  - Can reduce precision if needed (double → float)
  - Parallelize over grid points

**Risk 3: Numerical Instabilities**
- **Probability**: Medium (30%)
- **Impact**: Medium
- **Mitigation**:
  - Adaptive precision (double → quad)
  - Robust algorithms (RATTLE for constraints)
  - Fallback: symbolic computation (SymPy)

### Implementation Risks

**Risk 4: Integration Takes Longer Than Planned**
- **Probability**: High (60%)
- **Impact**: Low (schedule buffer exists)
- **Mitigation**:
  - Detailed task breakdowns with time estimates
  - Can parallelize parts within tasks
  - Some components optional (WP 2.3 if WP 2.2 succeeds)

**Risk 5: Dependencies on External Libraries**
- **Probability**: Low (< 10%)
- **Impact**: Medium
- **Mitigation**:
  - Primary dependencies stable (NumPy, SciPy)
  - REBOUND has fallback to SciPy
  - All algorithms implementable from scratch if needed

---

## Scientific Validation Plan

### Phase 1: Unit Testing (During Implementation)

**For Each Component**:
1. Theoretical property verification
   - Symplectic structure, gauge invariance, etc.
2. Numerical accuracy tests
   - Round-trip errors, conservation laws
3. Limiting case validation
   - Kepler, two-body, equal masses

**Pass Criteria**: All tests pass with target tolerances

---

### Phase 2: Integration Testing (After Implementation)

**System-Level Tests**:
1. **Pipeline Test**: Cartesian → Jacobi → Shape → S¹/KS → back to Cartesian
   - Error < 1e-10 for complete round-trip
2. **Long Integration**: 100-period Lagrange equilibrium
   - Energy drift < 1e-12
   - Shape preservation < 1e-12
3. **Collision Test**: Binary collision trajectory (KS)
   - Integrate through $r < 10^{-5}$ smoothly
4. **Chaos Test**: 1000 random initial conditions
   - Correlation $R$ vs. $\lambda > 0.7$

**Pass Criteria**: All integration tests successful

---

### Phase 3: Scientific Validation (Final)

**Hypothesis Tests**:

1. **Connection Curvature**:
   - $\mathcal{F} \neq 0$ in generic configurations
   - $|\mathcal{F}|$ correlates with non-integrability
   - Stokes' theorem validated to 1e-10

2. **JM Scalar Curvature**:
   - $R < 0$ correlates with $\lambda_{max} > 0$ (r > 0.7)
   - Classification accuracy > 80%
   - Statistical significance: p < 0.01

3. **S¹ Lift Integrability**:
   - $p_\theta$ conserved (drift < 1e-12)
   - If integrable: action-angle coordinates constructed
   - If not: obstruction characterized

4. **KS Regularization**:
   - Collisions regularized (test with $r_{min} < 10^{-5}$)
   - Spinor integrals (if any) identified
   - Comparison with S¹: advantages documented

**Pass Criteria**: Hypotheses supported by data (within expected outcomes)

---

## References and Resources

### Geometric Mechanics
1. Abraham & Marsden, *Foundations of Mechanics* (1978)
2. Marsden & Ratiu, *Introduction to Mechanics and Symmetry* (1999)
3. Guillemin & Sternberg, *Symplectic Techniques in Physics* (1984)
4. Cushman & Bates, *Global Aspects of Classical Integrable Systems* (1997)

### Three-Body Problem
5. Meyer & Hall, *Introduction to Hamiltonian Dynamical Systems* (2008)
6. Valtonen & Karttunen, *The Three-Body Problem* (2006)
7. Chenciner & Montgomery, "A remarkable periodic solution" (2000) - Figure-8
8. Saari, *Collisions, Rings, and Other Newtonian N-Body Problems* (2005)

### Symplectic Reduction
9. Marsden & Weinstein, "Reduction of symplectic manifolds with symmetry" (1974)
10. Littlejohn & Reinsch, "Gauge fields in the separation of rotations" (1997)
11. Montgomery, "The connection whose holonomy is the classical adiabatic angles" (1988)

### Regularization
12. Kustaanheimo & Stiefel, "Perturbation theory based on spinor regularization" (1965)
13. Stiefel & Scheifele, *Linear and Regular Celestial Mechanics* (1971)
14. Waldvogel, "Quaternions and the perturbed Kepler problem" (2006)
15. Aarseth, *Gravitational N-Body Simulations* (2003)

### Chaos and Geometry
16. Gutzwiller, *Chaos in Classical and Quantum Mechanics* (1990)
17. Pettini, *Geometry and Topology in Hamiltonian Dynamics* (2007)
18. Casetti et al., "Geometric approach to Hamiltonian dynamics" (2000)

---

## Summary Statistics

### Documentation Created

**Files**: 9 comprehensive design documents
**Total Lines**: ~11,617 lines of detailed specifications

| Document | Lines | Status |
|----------|-------|--------|
| Task 2.1.1 Implementation Plan | 602 | ✅ Complete |
| Task 2.1.1 Part A | 1,460 | ✅ Complete |
| Task 2.1.1 Part B | 1,084 | ✅ Complete |
| Task 2.1.1 Part C | 1,836 | ✅ Complete |
| Task 2.1.1 Part D | 1,397 | ✅ Complete |
| Task 2.1.2 Implementation Plan | 950 | ✅ NEW |
| Task 2.1.3 Implementation Plan | 945 | ✅ NEW |
| WP 2.2 Implementation Plan | 1,095 | ✅ NEW |
| WP 2.3 Implementation Plan | 1,248 | ✅ NEW |

### Implementation Estimates

**Total Estimated Duration**: 48-57 days
- Task 2.1.1: 12 days
- Task 2.1.2: 10 days
- Task 2.1.3: 8 days
- WP 2.2: 12 days
- WP 2.3: 15 days (conditional on WP 2.2 results)

**Critical Path**: ~38-40 days (if WP 2.2 succeeds and WP 2.3 can be skipped)

### Key Deliverables

- **9 implementation plans** (complete algorithmic specifications)
- **~30 Python modules** (coordinates, reduction, geometry, lifts, integration)
- **~50 validation tests** (unit, integration, scientific)
- **~20 visualization tools** (connection fields, curvature landscapes, etc.)
- **Technical report sections** (publication-ready LaTeX)
- **Tutorial notebooks** (educational material)

---

## Conclusion

Work Package 2 provides a **complete geometric foundation** for investigating the lift-integrability hypothesis in the three-body problem. The documentation is implementation-ready, with:

✅ **Mathematical Rigor**: All transformations and computations precisely specified
✅ **Algorithmic Detail**: Complete code templates and pseudocode
✅ **Validation Strategy**: Comprehensive testing at unit, integration, and scientific levels
✅ **Flexible Design**: Adapts to different outcomes (integrable, partial, non-integrable)
✅ **Clear Handoff**: Provides WP3 with everything needed for invariant discovery

**Next Action**: Begin implementation starting with Task 2.1.1, following the critical path outlined above.

---

**Document Version**: 1.0
**Created**: 2025-11-13
**Status**: Complete - Ready for Implementation
**Total WP2 Documentation**: 9 files, ~11,617 lines
**Next Phase**: Implementation → Validation → Handoff to WP3
