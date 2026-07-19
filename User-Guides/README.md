# User Guides: Three-Body Problem Integrability Research

**Welcome to the User Guides for the 3-body project!**

This folder contains comprehensive, user-friendly guides for each Work Package (WP) in the project. Each guide explains what the WP does, how it fits into the overall project, what code is available, and how to use it.

> **Current status (2026-07-19)**: WP1 qualification `WP1Q-v1-937694ba58a8` passes all locked development, calibration, and holdout gates against a pinned multi-system NASA/JPL corpus. The acceptance gate, bounded Tier 1/Tier 2 qualified artifacts, and Linux/amd64 parity also pass. This qualifies the declared numerical-method scope, not native production-scale periodic-orbit catalogue generation. See `../README.md`, `../notes/wp1-qualification-plan.md`, and the formal qualification report for the evidence boundary.

---

## Quick Navigation

### For New Users: Start Here
1. Read [Project Overview](#project-overview) below
2. Start with [User-Guide-WP1.md](User-Guide-WP1.md) - Foundation infrastructure
3. Follow the guides sequentially (WP1 → WP2 → WP3 → WP4 → WP5)

### For Developers: Jump to Relevant WP
- **Infrastructure & Validation**: [WP1](#wp1-high-precision-infrastructure)
- **Geometry & Lifts**: [WP2](#wp2-geometric-foundations)
- **Discovery & ML**: [WP3](#wp3-invariant-discovery)
- **Validation & Rigor**: [WP4](#wp4-rigorous-validation)
- **Publication**: [WP5](#wp5-consolidation--publication)

### For Researchers: Key Questions
- *How do I integrate a three-body trajectory?* → [WP1](User-Guide-WP1.md#quick-start-guide)
- *How do I compute the mechanical connection?* → [WP2](User-Guide-WP2.md#task-212-connection--curvature)
- *How do I search for new conserved quantities?* → [WP3](User-Guide-WP3.md#multi-stage-pipeline)
- *How do I validate a candidate integral?* → [WP4](User-Guide-WP4.md#the-validation-gauntlet)
- *How do I prepare results for publication?* → [WP5](User-Guide-WP5.md#publication-tracks)

---

## Project Overview

This project investigates **hidden integrability** in the Newtonian three-body problem through higher-dimensional symplectic embedding. While the three-body problem is proven non-integrable in standard coordinates (Bruns, Poincaré), the **lift-integrability hypothesis** proposes that new conserved quantities may exist in appropriately constructed "upstairs" spaces.

### The Central Question

**Can the three-body problem become integrable when lifted to a higher-dimensional space that respects its geometric structure?**

### Project Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    PROJECT FLOW CHART                            │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ WP1: High-Precision Infrastructure                               │
│ • Symplectic integrators (IAS15, Yoshida8, Adaptive)            │
│ • Chaos detection (MEGNO, FLI)                                   │
│ • Validation (shadow Hamiltonian, time reversibility)            │
│ • Production pipeline (10⁵+ orbit catalogue)                     │
│                                                                   │
│ Status: Scoped external qualification PASS                     │
│ Guide: User-Guide-WP1.md                                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Provides: High-fidelity trajectories
                     ↓
┌──────────────────────────────────────────────────────────────────┐
│ WP2: Geometric Foundations                                       │
│ • Coordinate systems (Cartesian, Jacobi, Shape Space)           │
│ • Symplectic reduction (Translation, Rotation)                   │
│ • Mechanical connection A & curvature F                          │
│ • Jacobi-Maupertuis metric (chaos-curvature correlation)        │
│ • S¹ bundle lift (untwisting connection)                         │
│ • KS-Spinor lift (collision regularization)                      │
│                                                                   │
│ Status: ✅ Core Complete (Coordinates, Geometry, Lifts ✅)       │
│ Guide: User-Guide-WP2.md                                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Provides: Lifted phase spaces
                     ↓
┌──────────────────────────────────────────────────────────────────┐
│ WP3: Invariant Discovery                                         │
│ • Spinor basis (~80 functions) + specialized search             │
│ • Elliptic function basis (sn, cn, dn) + quasi-periodic search │
│ • Theta function basis (θ₁₋₄) for complete integrability        │
│ • Multi-stage pipeline (coordinate all methods)                  │
│ • Hamiltonian Neural Networks (HNN)                              │
│ • Symbolic regression (PySR, SINDy)                              │
│                                                                   │
│ Status: ✅ 100% Complete (All phases 1-4)                       │
│ Guide: User-Guide-WP3.md                                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Provides: Candidate integrals
                     ↓
┌──────────────────────────────────────────────────────────────────┐
│ WP4: Rigorous Validation ("The Gauntlet")                       │
│ • WP 4.1: Analytical Vetting                                     │
│   - Poisson brackets {I, H} = 0                                  │
│   - Involution {I, E} = 0, {I, L} = 0                           │
│   - Functional independence (Jacobian rank)                      │
│ • WP 4.2: Morales-Ramis Test                                     │
│   - Phase I: Downstairs (non-abelian → classical obstruction)   │
│   - Phase II: Upstairs (abelian → validates lift-integrability) │
│ • WP 4.3: Numerical Robustness                                   │
│   - Monte Carlo (10⁵ samples)                                    │
│   - Stress testing (collisions, chaos, escape)                   │
│   - Long-time validation (10⁴-10⁶ periods)                      │
│                                                                   │
│ Status: ✅ 100% Complete (All infrastructure ready)             │
│ Guide: User-Guide-WP4.md                                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Provides: Validated results
                     ↓
┌──────────────────────────────────────────────────────────────────┐
│ WP5: Consolidation & Publication                                 │
│ • WP 5.1: Formal proof construction                              │
│ • WP 5.2: Reproducibility package (GitHub, Zenodo, Docker)      │
│ • WP 5.3: Manuscript preparation                                 │
│   - Target: PRL, CMDA, PNAS, or Nature/Science                  │
│   - Positive, partial, or negative results all publishable      │
│                                                                   │
│ Status: 📋 Design Complete (Pending WP4 results)                │
│ Guide: User-Guide-WP5.md                                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## Work Package Summaries

### WP1: High-Precision Infrastructure

**Purpose**: Establish computational foundation for three-body problem integration

**Status**: **Scoped external qualification PASS; native production catalogue unqualified**

**Key Components**:
- **Integrators**: IAS15 (adaptive Radau), Yoshida8 (symplectic), AdaptiveSymplectic (float64 prototype with guard), HeyokaTaylor (bounded Tier 2 smoke)
- **Chaos Detection**: MEGNO, FLI indicators
- **Validation**: Shadow Hamiltonian analysis, time reversibility tests
- **Production Pipeline**: Snakemake workflow for 10⁵+ orbit catalogue
- **External-seeded Catalogue**: 284 accepted JPL seeds under closure `<= 1e-8` and absolute Jacobi drift `<= 1e-12`
- **Formal Qualification**: 39/39 gates pass on development, calibration, and locked holdout across four systems, two families, and four stability regimes

**Quick Start**:
```python
from src.python.integrators.ias15 import IAS15Integrator

integrator = IAS15Integrator(mu=0.012150585609624)
times, states = integrator.integrate(state0, t_span=(0, 100), dt=0.1)
```

**Read more**: [User-Guide-WP1.md](User-Guide-WP1.md)

---

### WP2: Geometric Foundations

**Purpose**: Create geometric "playground" for searching hidden integrals in lifted spaces

**Status**: 🔨 **Partially Complete** (Coordinates, Reduction, Connection ✅; Lifts ⚠️ Partial)

**Key Components**:
- **Task 2.1.1**: Coordinate systems (Cartesian, Jacobi, Shape Space)
- **Task 2.1.2**: Mechanical connection A and curvature F (proves non-integrability "downstairs")
- **Task 2.1.3**: Jacobi-Maupertuis metric (chaos-curvature correlation)
- **WP 2.2**: S¹ bundle lift (4D total space, fiber momentum p_θ)
- **WP 2.3**: KS-Spinor lift (12D → 9D constrained, collision regularization)

**Quick Start**:
```python
from src.python.reduction.connection import MechanicalConnection

conn = MechanicalConnection(masses=masses)
A_value = conn.evaluate(shape_point, shape_velocity)
curvature = conn.compute_curvature(shape_point)
```

**Read more**: [User-Guide-WP2.md](User-Guide-WP2.md)

---

### WP3: Invariant Discovery

**Purpose**: Use ML + symbolic regression to discover candidate conserved quantities

**Status**: ✅ **100% Complete** (All phases 1-4 implemented)

**Key Components**:
- **Phase 1**: Spinor basis (~80 functions) + enhanced validation + interpretability
- **Phase 2**: Elliptic function basis (sn, cn, dn) + quasi-periodic search
- **Phase 3**: Spinor search (regularization-aware)
- **Phase 4**: Theta function basis (θ₁₋₄) for completely integrable systems
- **Integration**: Multi-stage pipeline coordinating all methods

**Quick Start**:
```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

search = MultiStageInvariantSearch(stages=['spinor', 'elliptic', 'theta', 'polynomial'])
results = search.run(times, states, mu=mu)
```

**Read more**: [User-Guide-WP3.md](User-Guide-WP3.md)

---

### WP4: Rigorous Validation

**Purpose**: Subject candidates to analytical and numerical "gauntlet" of tests

**Status**: ✅ **100% Complete** (All validation infrastructure operational)

**Key Components**:
- **WP 4.1**: Analytical vetting (Poisson brackets, involution, independence)
- **WP 4.2 Phase I**: Downstairs Morales-Ramis (prove non-abelian)
- **WP 4.2 Phase II**: Upstairs Morales-Ramis (prove abelian) **← CRITICAL**
- **WP 4.3**: Monte Carlo (10⁵ samples), stress tests, long-time validation

**Quick Start**:
```python
from src.python.validation.analytical_vetting import PoissonBracketValidator

pb_val = PoissonBracketValidator(mu=mu)
result = pb_val.test_conservation(candidate_integral, num_samples=1000)
```

**Read more**: [User-Guide-WP4.md](User-Guide-WP4.md)

---

### WP5: Consolidation & Publication

**Purpose**: Transform validated results into publication-ready scientific contribution

**Status**: 📋 **Design Complete** (Implementation pending WP4 results)

**Key Components**:
- **WP 5.1**: Formal proof construction (analytical + numerical evidence)
- **WP 5.2**: Reproducibility package (GitHub, Zenodo, Docker)
- **WP 5.3**: Manuscript preparation (LaTeX, figures, arXiv preprint)

**Publication Philosophy**: **Rigorous work is publishable regardless of outcome** (positive, partial, or negative results)

**Quick Start**:
```python
from src.python.publication.result_consolidator import ResultConsolidator

consolidator = ResultConsolidator.from_directory('results/wp4/')
report = consolidator.generate_report()
consolidator.export_latex_tables(output_dir='manuscript/tables/')
```

**Read more**: [User-Guide-WP5.md](User-Guide-WP5.md)

---

## How to Use These Guides

### For Complete Beginners

1. **Start with WP1**: Learn how to integrate three-body trajectories
2. **Try the Quick Start examples**: Run code snippets to get hands-on experience
3. **Read the "How it fits" sections**: Understand how each WP connects to the overall project
4. **Check Available Tests**: Run tests to verify your understanding

### For Developers

1. **Identify your task**: Find the relevant WP
2. **Read Core Components**: Understand the architecture
3. **Study Examples and Workflows**: See real-world usage patterns
4. **Consult References**: Dive deeper into mathematical foundations

### For Researchers

1. **Skim all guides**: Get the big picture
2. **Focus on Methods sections**: Understand the scientific approach
3. **Study Mathematical Frameworks**: Connect to literature
4. **Review Test Coverage**: Assess rigor and reproducibility

---

## Common Workflows

### Workflow 1: Generate and Analyze a Trajectory

```python
# WP1: Integrate trajectory
from src.python.integrators.ias15 import IAS15Integrator

mu = 0.012150585609624
integrator = IAS15Integrator(mu=mu)
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])
times, states = integrator.integrate(state0, (0, 100), dt=0.1)

# WP1: Check chaos
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

analyzer = create_cr3bp_chaos_analyzer(mu=mu)
result = analyzer.analyze(state0, t_max=100, dt=0.1)
print(f"MEGNO: {result['megno']:.3f}, Classification: {result['classification']}")

# WP2: Compute connection
from src.python.reduction.connection import MechanicalConnection

conn = MechanicalConnection(masses=masses)
# ... transform to shape space coordinates first
shape_trajectory = [...]
for s_point, s_vel in shape_trajectory:
    A_val = conn.evaluate(s_point, s_vel)
    F_val = conn.compute_curvature(s_point)
```

### Workflow 2: Search for New Integrals

```python
# WP3: Multi-stage search
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

search = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=5,
    enable_ranking=True
)

results = search.run(times, states, mu=mu)

# WP4: Validate top candidate
from src.python.validation.analytical_vetting import (
    PoissonBracketValidator,
    InvolutionTester,
    IndependenceTester
)

top_candidate = results.top_candidates[0]

pb_val = PoissonBracketValidator(mu=mu)
pb_result = pb_val.test_conservation(top_candidate.function, num_samples=1000)

inv_val = InvolutionTester(mu=mu)
inv_result = inv_val.test_involution(top_candidate.function, ['energy', 'angular_momentum'])

ind_val = IndependenceTester(mu=mu)
ind_result = ind_val.test_independence(top_candidate.function, ['energy', 'angular_momentum', 'jacobi_constant'], num_samples=10000)

if pb_result.passed and inv_result.passed and ind_result.passed:
    print("✓ Candidate passed analytical vetting!")
    print("→ Proceed to Morales-Ramis test (WP 4.2)")
```

### Workflow 3: Complete Validation Pipeline

```python
# Full validation pipeline for a candidate integral

from src.python.validation.morales_ramis_validator import MoralesRamisValidator
from src.python.validation.monte_carlo_validator import MonteCarloValidator
from src.python.validation.periodic_orbits import get_lagrange_l4_orbit

# WP 4.1: Analytical vetting (done above)

# WP 4.2: Morales-Ramis test
orbit = get_lagrange_l4_orbit(mu=mu)
mr_val = MoralesRamisValidator(mu=mu)

downstairs = mr_val.test_downstairs(orbit)
upstairs = mr_val.test_upstairs(orbit, lift_type='s1_bundle')

print(f"Downstairs: {'abelian' if downstairs.is_abelian else 'non-abelian'}")
print(f"Upstairs: {'abelian' if upstairs.is_abelian else 'non-abelian'}")

if not downstairs.is_abelian and upstairs.is_abelian:
    print("✓ Morales-Ramis compatible!")

# WP 4.3: Numerical robustness
mc_val = MonteCarloValidator(candidate_integral, mu=mu, num_samples=100000)
mc_result = mc_val.validate(
    param_ranges={'x': (0.5, 1.5), 'y': (-0.5, 0.5), 'vx': (-0.5, 0.5), 'vy': (0.0, 1.0)},
    integration_time=100.0
)

if mc_result.pass_rate > 0.95:
    print("✓ Monte Carlo validation passed!")
    print("→ Proceed to WP5 (Publication)")
```

---

## File Organization

```
User-Guides/
├── README.md                      # This file
├── User-Guide-WP1.md              # High-Precision Infrastructure
├── User-Guide-WP2.md              # Geometric Foundations
├── User-Guide-WP3.md              # Invariant Discovery
├── User-Guide-WP4.md              # Rigorous Validation
└── User-Guide-WP5.md              # Consolidation & Publication
```

---

## Additional Resources

### Within This Repository

- **Project-Design-Docs/**: Detailed design documents for each WP
- **Science-Research-Docs/**: Mathematical foundations and theoretical papers
- **TechnicalReadme.md**: Technical architecture and infrastructure details
- **README.md**: Project overview and quick start
- **examples/**: Jupyter notebooks and example scripts

### External Resources

**Three-Body Problem**:
- Barrow-Green (1997), *Poincaré and the Three Body Problem*
- Szebehely (1967), *Theory of Orbits*

**Symplectic Geometry**:
- Marsden & Ratiu (1999), *Introduction to Mechanics and Symmetry*
- Abraham & Marsden (1978), *Foundations of Mechanics*

**Differential Galois Theory**:
- Morales-Ruiz & Ramis (2001), "Galoisian obstructions to integrability"
- Kovacic (1986), "An algorithm for solving second order linear ODEs"

**Machine Learning for Dynamical Systems**:
- Brunton et al. (2016), "Discovering governing equations from data" (SINDy)
- Cranmer et al. (2020), "Discovering symbolic models from deep learning"

---

## Getting Help

### Documentation Issues
- If a guide is unclear or has errors, please open an issue on GitHub
- For questions about usage, consult the relevant guide's "Examples and Workflows" section

### Code Issues
- Check the `tests/` directory for working examples
- Run `pytest tests/` to verify your environment
- Consult `TechnicalReadme.md` for infrastructure details

### Scientific Questions
- Consult the `Science-Research-Docs/` for mathematical foundations
- Check references in each user guide
- Refer to `Project-Design-Docs/` for design rationale

---

## Contributing

If you'd like to contribute to these user guides:

1. **Clarifications**: Submit pull requests with improvements
2. **Examples**: Add new examples to "Examples and Workflows" sections
3. **Tests**: Contribute new test cases demonstrating usage
4. **Figures**: Create diagrams or visualizations to enhance understanding

All contributions should maintain the guides' focus on:
- **Clarity**: Easy to understand for new users
- **Accuracy**: Reflects actual code implementation
- **Completeness**: Covers all major use cases
- **References**: Links to deeper documentation

---

## Project Status Summary

| Work Package | Status | Completion | User Guide |
|--------------|--------|------------|------------|
| **WP1** | Qualified (scoped) | External method claim passes; native production catalogue remains open | [User-Guide-WP1.md](User-Guide-WP1.md) |
| **WP2** | 🔨 Partial | ~70% | [User-Guide-WP2.md](User-Guide-WP2.md) |
| **WP3** | ✅ Complete | 100% | [User-Guide-WP3.md](User-Guide-WP3.md) |
| **WP4** | ✅ Complete | 100% | [User-Guide-WP4.md](User-Guide-WP4.md) |
| **WP5** | 📋 Designed | 0% | [User-Guide-WP5.md](User-Guide-WP5.md) |

**Overall Project**: Active research prototype. Infrastructure is usable, but publication claims are pending validated WP1 evidence and downstream validation.

---

## Citation

If you use this codebase or methodology in your research, please cite:

```bibtex
@software{3body_integrability_2025,
  author = {Sullivan, Jacob},
  title = {Three-Body Problem Integrability Research: A Systematic Search via Higher-Dimensional Symplectic Embedding},
  year = {2025},
  url = {https://github.com/jacobrsullivan/3body},
  note = {Work Packages 1-4 complete, WP5 pending validation results}
}
```

(Update with actual publication when available from WP5)

---

**Last Updated**: November 23, 2025

**Questions?** Start with the relevant user guide, check the examples, and consult the references. Happy exploring!
