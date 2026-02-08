# Task 2.1.1: Coordinate Systems and Reduction Implementation
## WP 2.1 - Geometric Reduction and Shape Space Analysis

**Status**: Planning
**Priority**: Critical Path
**Estimated Duration**: 10-12 days
**Dependencies**: WP1 Complete (High-Precision Integration Suite)

---

## Overview

This task implements the foundational coordinate transformations and symplectic reduction machinery needed for the entire WP2-5 pipeline. We transition from the Circular Restricted 3-Body Problem (CR3BP) to the **general Newtonian 3-Body Problem (3BP)**, establishing the geometric framework for discovering hidden integrability.

### Objectives

1. Implement robust, high-precision transformations between coordinate systems:
   - Cartesian coordinates (barycentric inertial frame)
   - Jacobi coordinates (hierarchical mass-weighted)
   - Shape Space coordinates (quotient by translations & rotations)

2. Implement Marsden-Weinstein symplectic reduction:
   - Quotient by translations (remove center-of-mass motion)
   - Quotient by rotations SO(3) (reduce to shape dynamics)
   - Preserve symplectic structure throughout

### Mathematical Background

#### The General 3-Body Problem

Unlike CR3BP (where one body has zero mass), we now consider three bodies with arbitrary masses $m_1, m_2, m_3$.

**Configuration Space**: $\mathbb{R}^9$ (3 bodies × 3D positions)
**Phase Space**: $T^*\mathbb{R}^9 \cong \mathbb{R}^{18}$ (positions + momenta)

**Hamiltonian** (Newtonian gravity):
$$
H = \frac{1}{2}\sum_{i=1}^3 \frac{|\mathbf{p}_i|^2}{m_i} - \sum_{1 \le i < j \le 3} \frac{G m_i m_j}{|\mathbf{r}_i - \mathbf{r}_j|}
$$

**Symmetries**:
- Translations: $\mathbb{R}^3$ (center-of-mass conservation)
- Rotations: $SO(3)$ (angular momentum conservation)
- Time translation: Energy conservation

**Goal of Reduction**: Remove the 6 trivial symmetries (3 translation + 3 rotation) to obtain a **3-dimensional shape space** (for planar motion).

---

## Part A: Coordinate System Implementations

### A1. Cartesian (Barycentric Inertial) Coordinates

**What**: Standard Cartesian positions and velocities in an inertial frame centered at the barycenter.

**State Vector**:
$$
\mathbf{z}_{\text{cart}} = (\mathbf{r}_1, \mathbf{r}_2, \mathbf{r}_3, \mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3) \in \mathbb{R}^{18}
$$

**Barycenter Constraint**:
$$
\sum_{i=1}^3 m_i \mathbf{r}_i = \mathbf{0}, \quad \sum_{i=1}^3 m_i \mathbf{v}_i = \mathbf{0}
$$

#### Implementation Tasks

**A1.1**: Create module `src/python/coordinates/cartesian.py`
- Define `CartesianState` dataclass with validation
- Implement barycenter enforcement functions
- Implement conserved quantities (energy, angular momentum, linear momentum)
- Handle both planar (2D) and spatial (3D) cases

**A1.2**: Implement high-precision Cartesian dynamics
- Newtonian gravitational force calculation
- Equations of motion: $\dot{\mathbf{r}}_i = \mathbf{v}_i$, $\dot{\mathbf{v}}_i = \mathbf{a}_i$
- Acceleration with collision regularization handling
- Use QD library for critical calculations (distances, potentials)

**A1.3**: Validation harness
- Verify conservation laws (energy, linear momentum, angular momentum)
- Test against known solutions (Lagrange equilibria, Figure-8 orbit)
- Benchmark precision vs. double-precision arithmetic

**Deliverable A1**:
- `cartesian.py` module with complete documentation
- Unit tests achieving >95% coverage
- Validation report confirming conservation to $\Delta E/E < 10^{-12}$

---

### A2. Jacobi Coordinates

**What**: Hierarchical mass-weighted relative coordinates that decouple center-of-mass motion.

**Definition** (3-body case):
$$
\begin{aligned}
\mathbf{r}_{J,1} &= \mathbf{r}_1 - \mathbf{r}_2 \quad &\text{(relative position of bodies 1-2)} \\
\mathbf{r}_{J,2} &= \mathbf{r}_3 - \mathbf{r}_{\text{cm},12} \quad &\text{(body 3 relative to cm of 1-2)} \\
\mathbf{r}_{J,3} &= \mathbf{r}_{\text{cm}} \quad &\text{(barycenter, decoupled)}
\end{aligned}
$$

where $\mathbf{r}_{\text{cm},12} = \frac{m_1 \mathbf{r}_1 + m_2 \mathbf{r}_2}{m_1 + m_2}$.

**Conjugate Momenta**:
$$
\begin{aligned}
\mathbf{p}_{J,1} &= \mu_{12} \dot{\mathbf{r}}_{J,1}, \quad \mu_{12} = \frac{m_1 m_2}{m_1 + m_2} \\
\mathbf{p}_{J,2} &= \mu_3 \dot{\mathbf{r}}_{J,2}, \quad \mu_3 = \frac{(m_1+m_2) m_3}{m_1+m_2+m_3} \\
\mathbf{p}_{J,3} &= M \dot{\mathbf{r}}_{J,3}, \quad M = m_1 + m_2 + m_3
\end{aligned}
$$

**Key Property**: Hamiltonian decouples into internal + center-of-mass motion:
$$
H = H_{\text{internal}}(\mathbf{r}_{J,1}, \mathbf{r}_{J,2}, \mathbf{p}_{J,1}, \mathbf{p}_{J,2}) + \frac{|\mathbf{p}_{J,3}|^2}{2M}
$$

#### Implementation Tasks

**A2.1**: Create module `src/python/coordinates/jacobi.py`
- Implement transformation: Cartesian → Jacobi
- Implement inverse transformation: Jacobi → Cartesian
- Define reduced masses $\mu_{12}, \mu_3$
- Validate symplectic property: $\omega_{\text{Jacobi}} = \omega_{\text{Cartesian}}$

**A2.2**: Jacobi Hamiltonian
- Implement internal Hamiltonian $H_{\text{internal}}$
- Verify decoupling: $\{H_{\text{internal}}, \mathbf{r}_{J,3}\} = 0$
- Implement equations of motion in Jacobi coordinates
- Numerical validation: run integrator in both coordinate systems, compare

**A2.3**: High-precision utilities
- Distance calculations in Jacobi form
- Conversion to/from mass-weighted coordinates
- Handle singular mass ratios (e.g., $m_1 \gg m_2 \approx m_3$)

**A2.4**: Extension to arbitrary hierarchies
- Allow user-specified hierarchical structure (which pair to group first)
- Default: group the two closest/most massive bodies
- Validation for different mass hierarchies (hierarchical, democratic, extreme)

**Deliverable A2**:
- `jacobi.py` module with bidirectional transformations
- Test suite with round-trip error $< 10^{-14}$ (double precision)
- Verification that Hamiltonian decouples correctly
- Documentation of mass parameter conventions

---

### A3. Shape Space Coordinates

**What**: Coordinates on the quotient space obtained by removing translations and rotations.

**Shape Space Dimension** (planar 3BP):
- Original: 12 DOF (3 bodies × 2D × 2 (pos+vel))
- Subtract 3 DOF: center-of-mass translation + velocity
- Subtract 2 DOF: rotation + angular velocity (planar SO(2))
- **Result**: 7 DOF → Reduced phase space is 7-dimensional

**Common Coordinate Choices**:

1. **Relative Distances** (Gauge-invariant):
   $$
   (r_{12}, r_{23}, r_{31}) = (|\mathbf{r}_1 - \mathbf{r}_2|, |\mathbf{r}_2 - \mathbf{r}_3|, |\mathbf{r}_3 - \mathbf{r}_1|)
   $$
   - **Triangle constraint**: $r_{12} + r_{23} \ge r_{31}$ (and cyclic)
   - Shape space is a 3D cone (with apex at collision)

2. **Normalized Relative Coordinates**:
   $$
   \mathbf{s}_1 = \frac{\mathbf{r}_1 - \mathbf{r}_2}{r_{12}}, \quad \mathbf{s}_2 = \frac{\mathbf{r}_3 - \mathbf{r}_{\text{cm},12}}{r_{3,12}}
   $$
   - Angles parameterize the shape, distances give scale

3. **Complex Shape Variables** (planar):
   $$
   z = \frac{r_3 - r_1}{r_2 - r_1} \in \mathbb{C}
   $$
   - Convenient for analytical work (Möbius symmetry)

#### Implementation Tasks

**A3.1**: Create module `src/python/coordinates/shape_space.py`

**A3.2**: Relative distance coordinates
- Compute $(r_{12}, r_{23}, r_{31})$ from Cartesian or Jacobi
- Compute velocities $(\dot{r}_{12}, \dot{r}_{23}, \dot{r}_{31})$
- Validation: triangle inequality enforcement
- Singular handling: near-collision regularization

**A3.3**: Normalized shape coordinates
- Implement oriented triangle representation
- Choose canonical orientation (e.g., align body 1-2 axis with x-axis)
- Compute shape + orientation angle $\theta$ (for planar case)
- Conjugate momentum to $\theta$ (related to angular momentum $L$)

**A3.4**: Complex shape variable (planar only)
- Implement $z = (r_3 - r_1)/(r_2 - r_1)$ and conjugate momentum
- Validate against distance-based representation
- Inverse transformation: shape → Cartesian (with ambiguity in overall rotation/translation)

**A3.5**: Metric and volume forms
- Implement mass-weighted metric $g_{\text{mass}} = \sum m_i dr_i \otimes dr_i$
- Implement induced shape space metric (quotient metric)
- Numerical computation of metric tensor components
- Validate: metric is positive-definite away from collisions

**Deliverable A3**:
- `shape_space.py` module with multiple coordinate representations
- Coordinate transformation test suite (round-trip accuracy)
- Geometric structure validation (metric, symplectic form)
- Visualization tools for shape space trajectories

---

## Part B: Marsden-Weinstein Symplectic Reduction

### B1. Theoretical Foundation

**Marsden-Weinstein Reduction**: Given a Hamiltonian system $(M, \omega, H)$ with a Lie group $G$ action preserving $\omega$ and $H$, and a momentum map $\mu: M \to \mathfrak{g}^*$:

1. The level set $\mu^{-1}(c)$ is $G$-invariant
2. The quotient $M_c = \mu^{-1}(c) / G$ inherits a symplectic structure $\omega_{\text{red}}$
3. The Hamiltonian descends to $H_{\text{red}}$ on $M_c$

**For 3BP**:
- $G = \mathbb{R}^3 \times SO(3)$ (translations × rotations)
- Momentum map: $\mu = (\mathbf{P}, \mathbf{L})$ (linear + angular momentum)
- Standard reduction: $\mu^{-1}(0, \mathbf{0})$ (zero total momentum)

### B2. Reduction by Translations

**Goal**: Remove center-of-mass motion.

**Momentum Map**: $\mu_{\text{trans}}(\mathbf{z}) = \sum_{i=1}^3 \mathbf{p}_i$ (total linear momentum)

**Zero Level Set**: $\mathbf{P} = \sum m_i \mathbf{v}_i = \mathbf{0}$

**Quotient**: Work in barycentric frame ($\sum m_i \mathbf{r}_i = \mathbf{0}$)

#### Implementation Tasks

**B2.1**: Create module `src/python/reduction/translation_reduction.py`

**B2.2**: Barycenter enforcement
- Project arbitrary state onto $\sum m_i \mathbf{r}_i = 0$ constraint surface
- Validate: $\mathbf{P} = 0$ is conserved in barycentric frame
- High-precision projection (minimize drift in long integrations)

**B2.3**: Reduced Hamiltonian
- Verify that $H$ does not depend on $\mathbf{r}_{\text{cm}}$ (translational invariance)
- Implement reduced equations of motion on the quotient

**B2.4**: Validation
- Conservation of $\mathbf{P} = 0$ to machine precision
- Numerical stability tests over long integrations

**Deliverable B2**:
- `translation_reduction.py` module
- Constraint enforcement with error $< 10^{-14}$
- Test suite validating momentum conservation

---

### B3. Reduction by Rotations (SO(3))

**Goal**: Remove rotational degrees of freedom while preserving angular momentum.

**Momentum Map**: $\mu_{\text{rot}}(\mathbf{z}) = \mathbf{L} = \sum_{i=1}^3 \mathbf{r}_i \times m_i \mathbf{v}_i$ (total angular momentum)

**Zero Level Set** (planar reduction):
- For planar 3BP: $\mathbf{L} = L \hat{z}$ (out-of-plane component only)
- Quotient by SO(2) rotations about z-axis

**Non-zero Angular Momentum**:
- General case: reduce on $\mu^{-1}(\mathbf{L}_0)$ for fixed $\mathbf{L}_0 \ne 0$
- Leads to "magnetic" symplectic structure on shape space

#### Implementation Tasks

**B3.1**: Create module `src/python/reduction/rotation_reduction.py`

**B3.2**: Angular momentum calculations
- Implement $\mathbf{L} = \sum \mathbf{r}_i \times \mathbf{p}_i$ with high precision
- Separate components: $L_x, L_y, L_z$ (or magnitude + direction)
- Monitor conservation: $|\Delta \mathbf{L}|/|\mathbf{L}_0| < 10^{-12}$

**B3.3**: Canonical orientation choice
- For planar case: rotate so that, e.g., body 1-2 axis aligns with x-axis
- For spatial case: align angular momentum with z-axis, then fix remaining SO(2)
- Implement rotation matrices (with QD precision for critical calculations)
- Inverse map: shape + orientation → Cartesian

**B3.4**: Reduced symplectic form (the "connection")
- Implement the mechanical connection one-form $A$ (this is **Task 2.1.2***, but we set up the infrastructure here)
- The reduced symplectic form is:
  $$
  \omega_{\text{red}} = \omega_{\text{shape}} - d(\mathbf{L} \cdot d\theta)
  $$
  where $\theta$ is the SO(3) orientation angle
- This "magnetic twist" is the key obstruction to integrability downstairs

**B3.5**: Validation: Symplectic property
- Verify that $\omega_{\text{red}}$ is closed: $d\omega_{\text{red}} = 0$
- Verify non-degeneracy
- Test on simple examples (e.g., planar equal-mass collinear orbit)

**Deliverable B3**:
- `rotation_reduction.py` module
- Angular momentum conservation validation
- Infrastructure for connection form $A$ (completed in Task 2.1.2)
- Test suite for reduced dynamics

---

## Part C: Integration with Existing WP1 Infrastructure

### C1. Adapt Integrators for General 3BP

**Current State**: WP1 integrators (IAS15, Yoshida8) are built for CR3BP.

**Required Changes**:
- Generalize to arbitrary masses $(m_1, m_2, m_3)$
- Implement 3BP Hamiltonian and equations of motion
- Maintain high-precision arithmetic (QD library) for energy/momentum monitoring

#### Implementation Tasks

**C1.1**: Create `src/python/integrators/threebody.py`
- Base class for 3BP integrators (inheriting from WP1 base)
- Interface: `integrate(state_cart, masses, t_span, **options)`
- Support for both Cartesian and Jacobi coordinate integration

**C1.2**: Adapt IAS15 for 3BP
- REBOUND backend can handle n-body systems naturally
- Wrapper to translate between our state representation and REBOUND's
- Validation against WP1 test cases (should recover CR3BP as special case)

**C1.3**: Adapt Yoshida8 for 3BP
- Implement symplectic splitting for 3BP Hamiltonian
- Ensure time-reversibility is maintained
- Benchmark against IAS15 for accuracy and speed

**C1.4**: High-precision monitoring
- Energy conservation tracking
- Linear momentum conservation (should be exactly zero in barycentric frame)
- Angular momentum conservation
- Validation harness similar to WP1 Day 4 tests

**Deliverable C1**:
- `threebody.py` module with adapted integrators
- Test suite demonstrating conservation properties
- Benchmark report comparing 3BP vs CR3BP performance

---

### C2. Test Cases and Validation Datasets

**Goal**: Validate coordinate transformations and reduction using known exact/high-quality solutions.

#### Known Solutions for Testing

1. **Lagrange Equilateral Configuration**:
   - Three equal masses at vertices of equilateral triangle
   - Rotates rigidly (constant shape)
   - Analytic solution in any coordinate system

2. **Euler Collinear Periodic Orbits**:
   - Three masses on a line, periodic motion
   - Known family of solutions

3. **Figure-8 Orbit** (Chenciner-Montgomery):
   - Equal masses, planar, periodic
   - High-precision initial conditions available in literature
   - Excellent test of numerical stability

4. **Restricted 3BP as Limit**:
   - Set $m_3 \to 0$ and recover CR3BP from WP1
   - Validate backward compatibility

#### Implementation Tasks

**C2.1**: Create `tests/test_coordinate_transforms.py`
- Round-trip tests: Cartesian → Jacobi → Cartesian
- Round-trip tests: Cartesian → Shape → Cartesian (with fixed orientation)
- Precision validation: max error $< 10^{-13}$ in double, $< 10^{-28}$ in QD

**C2.2**: Create `tests/test_reduction.py`
- Verify momentum conservation after translation reduction
- Verify angular momentum conservation after rotation reduction
- Verify reduced dynamics match full dynamics on quotient

**C2.3**: Create `validation/lagrange_equilibrium.py`
- Implement exact solution for equilateral configuration
- Integrate using all coordinate systems (Cartesian, Jacobi, Shape)
- Validate: trajectories agree to integrator tolerance

**C2.4**: Create `validation/figure8_orbit.py`
- Load high-precision Figure-8 initial conditions
- Integrate for 10+ periods
- Validate: energy drift $< 10^{-12}$, returns to initial state

**C2.5**: Create `validation/cr3bp_limit.py`
- Set up CR3BP as $m_3 \to 0$ limit of 3BP
- Compare against WP1 CR3BP integrators
- Validate: solutions converge as $m_3 \to 0$

**Deliverable C2**:
- Comprehensive test suite (>95% coverage of new code)
- Validation report with numerical convergence data
- High-precision reference datasets for future use

---

## Part D: Documentation and Deliverables

### D1. API Documentation

- Docstrings for all public functions (NumPy style)
- Mathematical background for each coordinate system
- Transformation diagrams (Cartesian ↔ Jacobi ↔ Shape)
- Usage examples with minimal working code snippets

### D2. Technical Report: "Coordinate Systems and Reduction for the 3BP"

**Sections**:
1. **Introduction**: Geometric reduction in Hamiltonian mechanics
2. **Coordinate Systems**: Definitions, transformations, advantages
3. **Marsden-Weinstein Reduction**: Theory and implementation
4. **Validation**: Test cases and numerical results
5. **Numerical Stability**: High-precision arithmetic, error analysis
6. **Appendix**: Derivations, symplectic form calculations

**Target**: 15-20 pages, publication-ready LaTeX

### D3. Tutorial Jupyter Notebook

- Step-by-step walkthrough of coordinate transformations
- Visualization of trajectories in different coordinates
- Interactive widgets for exploring mass parameters
- Comparison of shape space vs. Cartesian phase portraits

**Deliverable D**:
- `docs/Task_2.1.1_Technical_Report.pdf`
- `notebooks/Tutorial_Coordinate_Systems.ipynb`
- Complete API documentation in code

---

## Implementation Schedule

### Phase 1: Core Coordinate Systems (4 days)
- **Day 1**: Cartesian coordinates and 3BP dynamics (A1)
- **Day 2**: Jacobi coordinates and transformations (A2)
- **Day 3-4**: Shape space coordinates (A3)

### Phase 2: Symplectic Reduction (3 days)
- **Day 5**: Translation reduction (B2)
- **Day 6**: Rotation reduction (B3.1-B3.3)
- **Day 7**: Reduced symplectic structure (B3.4-B3.5)

### Phase 3: Integration and Validation (3 days)
- **Day 8**: Adapt integrators (C1)
- **Day 9**: Implement test cases (C2.1-C2.3)
- **Day 10**: Validation datasets (C2.4-C2.5)

### Phase 4: Documentation and Review (2 days)
- **Day 11**: API docs, technical report draft (D1, D2)
- **Day 12**: Tutorial notebook, final review (D3)

**Total**: 12 days (can be compressed to 10 with parallel work on docs)

---

## Success Criteria

### Functional Requirements
- [ ] Bidirectional transformations implemented for all coordinate pairs
- [ ] Round-trip error < 1e-13 (double precision) or 1e-28 (quad-double)
- [ ] Marsden-Weinstein reduction enforces constraints to machine precision
- [ ] Integrators adapted to general 3BP with conservation validation

### Performance Requirements
- [ ] Coordinate transformations complete in < 1 ms for single state
- [ ] Batch transformations vectorized (process 1000 states in < 10 ms)
- [ ] No performance regression vs. WP1 for CR3BP limit

### Quality Requirements
- [ ] Test coverage > 95% for new modules
- [ ] All tests pass in CI/CD pipeline
- [ ] Documentation complete (API + technical report)
- [ ] Code review approved by 2+ reviewers

### Scientific Validation
- [ ] Conservation laws verified: $|\Delta E| / E < 10^{-12}$
- [ ] Angular momentum drift: $|\Delta \mathbf{L}| < 10^{-14}$ (absolute)
- [ ] Figure-8 orbit integrates stably for 100+ periods
- [ ] Symplectic structure preserved: $\omega_{\text{red}}$ is closed and non-degenerate

---

## Risk Mitigation

### Risk 1: Numerical Instability Near Collisions
**Mitigation**:
- Implement regularization early (KS transform in Task 2.3)
- Softened potentials for initial testing
- Collision detection and adaptive refinement

### Risk 2: Coordinate Singularities
**Mitigation**:
- Multiple coordinate representations (switch when one becomes singular)
- Explicit handling of degenerate triangles (collinear configurations)
- Validation tests specifically for edge cases

### Risk 3: Symplectic Structure Complexity
**Mitigation**:
- Start with planar (2D) case where SO(2) is simpler
- Symbolic validation using SymPy/Mathematica before numerical implementation
- Incremental testing: translation first, then rotation

### Risk 4: Integration with WP1 Infrastructure
**Mitigation**:
- Maintain backward compatibility (CR3BP should be a special case)
- Shared test suite between WP1 and WP2
- Clear interface boundaries (duck typing for coordinate systems)

---

## Dependencies and Handoffs

### Inputs (from WP1)
- High-precision integrators (IAS15, Yoshida8)
- QD library bindings
- Testing infrastructure and CI/CD pipeline
- Validation harness framework

### Outputs (to WP2 Tasks 2.1.2 and 2.1.3)
- Complete coordinate transformation library
- Reduced dynamics in shape space
- Infrastructure for connection form $A$ (used in Task 2.1.2)
- JM metric implementation (used in Task 2.1.3)

### Outputs (to WP2.2 and WP2.3)
- Shape space coordinates (base for fiber bundles)
- Symplectic reduction machinery (extended to S¹ and KS lifts)

---

## References

### Geometric Mechanics
1. Abraham & Marsden, *Foundations of Mechanics* (1978) - Marsden-Weinstein reduction
2. Cushman & Bates, *Global Aspects of Classical Integrable Systems* (1997) - Shape space
3. Meyer & Hall, *Introduction to Hamiltonian Dynamical Systems and the N-Body Problem* (2008)

### Three-Body Problem
4. Valtonen & Karttunen, *The Three-Body Problem* (2006) - Comprehensive reference
5. Chenciner & Montgomery, "A remarkable periodic solution of the three-body problem in the case of equal masses" (2000) - Figure-8 orbit
6. Wisdom & Hernandez, "Symplectic maps for the n-body problem" (1991) - Jacobi coordinates

### Numerical Methods
7. Hairer, Lubich, Wanner, *Geometric Numerical Integration* (2006) - Symplectic integrators
8. Rein & Spiegel, "IAS15: A fast, adaptive, high-order integrator" (2015)
9. Preto & Tremaine, "A class of symplectic integrators with adaptive time step for separable Hamiltonian systems" (1999)

---

## Appendix: Coordinate Transformation Summary Table

| From ↓ / To → | **Cartesian** | **Jacobi** | **Shape Space** |
|---------------|---------------|------------|-----------------|
| **Cartesian** | — | Linear (mass-weighted) | Nonlinear (quotient + gauge) |
| **Jacobi** | Linear (inverse transform) | — | Nonlinear (quotient + gauge) |
| **Shape Space** | Ambiguous (needs orientation/position) | Ambiguous (needs orientation/position) | — |

**Key Points**:
- Cartesian ↔ Jacobi: Invertible linear transformation (6×6 matrix for planar)
- Cartesian/Jacobi → Shape: Quotient map (many-to-one), removes 6 DOF
- Shape → Cartesian/Jacobi: Requires fixing gauge (overall translation/rotation)

---

## Glossary

- **Barycentric Frame**: Coordinate system with origin at center of mass
- **Jacobi Coordinates**: Hierarchical coordinates separating internal/external motion
- **Shape Space**: Quotient space $\mathbb{R}^{3N} / (\mathbb{R}^3 \times SO(3))$
- **Marsden-Weinstein Reduction**: Symplectic quotient by group action
- **Momentum Map**: Map from phase space to dual of Lie algebra: $\mu: M \to \mathfrak{g}^*$
- **Mechanical Connection**: One-form $A$ encoding the rotational coupling in reduced dynamics
- **Symplectic Form**: Closed, non-degenerate 2-form $\omega$ defining Hamiltonian structure

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**Next Review**: After completion of Phase 1 (Day 4)
