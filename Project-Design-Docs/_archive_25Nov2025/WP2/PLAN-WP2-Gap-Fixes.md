# WP2 Gap Analysis and Implementation Plan
## Comprehensive Plan to Achieve 100% Completion

**Current Status**: 85% Complete
**Target Status**: 100% Complete
**Created**: November 22, 2025
**Priority**: High
**Estimated Duration**: 8-12 days

---

## Executive Summary

Based on comprehensive review of the Implementation Status document and codebase analysis, WP2 (Geometric Reduction and Shape Space Analysis) is **85% complete** with **substantial implementation progress**. The remaining 15% comprises three main areas:

1. **Symbolic KS Implementation** (Primary Gap - ~10% of total WP2)
2. **Visualization Infrastructure** (Secondary Gap - ~3% of total WP2)
3. **Documentation/Tutorials** (Minor Gap - ~2% of total WP2)

All **core mathematical and computational components are fully implemented and tested**. The gaps represent enhancement and completion items that will bring WP2 to production-ready 100% status.

---

## Table of Contents

1. [Gap Analysis](#gap-analysis)
2. [Priority Classification](#priority-classification)
3. [Implementation Plan](#implementation-plan)
4. [Detailed Task Breakdown](#detailed-task-breakdown)
5. [Success Criteria](#success-criteria)
6. [Integration and Testing](#integration-and-testing)
7. [Timeline and Milestones](#timeline-and-milestones)

---

## Gap Analysis

### Current Implementation Status by Component

| Component | Status | Files | Lines | Completion |
|-----------|--------|-------|-------|------------|
| Task 2.1.1: Coordinates | ✅ Complete | 6 | ~1,879 | 100% |
| Task 2.1.2: Connection/Curvature | ✅ Complete | 3 | ~948 | 100% |
| Task 2.1.3: JM Metric | ✅ Complete | 4 | ~1,426 | 100% |
| WP 2.2: S¹ Lift | ✅ Complete | 4 | ~1,323 | 100% |
| WP 2.3: KS-Spinor Lift | ✅ Complete | 14 | ~5,025 | 100% |
| Reduction | ✅ Complete | 4 | ~1,587 | 100% |
| **Symbolic Lifts** | 🟡 **Partial** | 2 | ~746 | **70%** |
| **Visualization** | 🔴 **Missing** | 0 | 0 | **0%** |
| **Tutorials** | 🟡 **Partial** | ? | ? | **50%** |

### Identified Gaps

#### Gap 1: Symbolic KS Implementation (PRIMARY)

**Status**: Missing
**Impact**: High for WP4.2 Morales-Ramis upstairs analysis
**Effort**: 5-7 days

**Missing Components**:
- `src/python/symbolic_lifts/ks_symbolic.py` (complete module)
  - Symbolic Levi-Civita matrix L(u)
  - Symbolic KS transformation (r ↔ u)
  - Pairwise spinor Hamiltonian
  - Constraint equations (bilinear, closure)
  - Extended phase space with fictitious time
  - Hessian computation for Morales-Ramis analysis

**Evidence**:
```python
# From symbolic_lifts/__init__.py, line 15:
- ks_symbolic: KS-Spinor extended Hamiltonian (TODO)
```

**Why This Matters**:
- WP4.2 Phase II requires symbolic Hessian of upstairs Hamiltonian
- Kovacic algorithm needs exact symbolic expressions
- Cannot proceed with upstairs Morales-Ramis test without this

#### Gap 2: Visualization Infrastructure (SECONDARY)

**Status**: Missing
**Impact**: Medium - affects presentation and analysis
**Effort**: 3-4 days

**Missing Components**:
- Connection field visualization
  - Vector field plots of A(s) on shape space
  - Streamlines showing rotational coupling
  - Magnitude heatmaps
- Curvature visualization
  - 2D heatmaps of |F(s)|
  - Contour plots showing obstruction regions
  - 3D surface plots
- JM Metric visualization
  - Metric ellipsoids at sample points
  - Scalar curvature R landscape
  - Geodesic flow visualization
- Shape space trajectory visualization
  - Trajectories in (r₁₂, r₂₃, r₃₁) space
  - Colored by energy/chaos
  - Comparison plots (S¹ vs KS coordinates)

**Evidence**:
- Design documents (Task 2.1.2, 2.1.3) specify visualization deliverables
- No visualization modules found in codebase
- Implementation status mentions "visualization components referenced but may need expansion"

**Why This Matters**:
- Essential for publication-quality figures
- Diagnostic tool for understanding geometry
- User interface for exploring results

#### Gap 3: Documentation and Tutorials (MINOR)

**Status**: Partial
**Impact**: Low - code is well-documented
**Effort**: 1-2 days

**Missing Components**:
- Tutorial notebooks
  - "Getting Started with WP2 Coordinates"
  - "Understanding the Mechanical Connection"
  - "S¹ vs KS Lift Comparison"
- Integration examples
  - End-to-end workflow examples
  - Common use cases
- User guides
  - Choosing coordinates for different scenarios
  - Troubleshooting guide

**Evidence**:
- Implementation status: "API docs complete, tutorials could be expanded"
- README files exist but narrative tutorials limited

---

## Priority Classification

### P0 (Critical - Blocks WP4)
- **Gap 1: Symbolic KS Implementation**
  - Required for WP4.2 Phase II Morales-Ramis
  - Blocks upstairs integrability analysis

### P1 (Important - Enhances Usability)
- **Gap 2: Visualization Infrastructure**
  - Needed for publication figures
  - Diagnostic and analysis tool

### P2 (Nice to Have - Improves Accessibility)
- **Gap 3: Documentation/Tutorials**
  - Improves onboarding
  - Not blocking for research

---

## Implementation Plan

### Phase 1: Symbolic KS Implementation (Days 1-7)

**Objective**: Complete `ks_symbolic.py` module to match quality of `s1_symbolic.py`

#### Step 1.1: Module Architecture Design (Day 1)
- Review `s1_symbolic.py` structure as template
- Design `KSSpinorHamiltonian` class hierarchy
- Define interfaces for constraint handling
- Plan symbolic representation of time regularization

**Deliverable**: Architecture document

#### Step 1.2: Core KS Symbolic Components (Days 2-3)
- Implement `SymbolicLeviCivitaMatrix` class
- Implement `symbolic_ks_transform()` functions
  - `symbolic_cartesian_to_ks(r_sym, v_sym)`
  - `symbolic_ks_to_cartesian(u_sym, u_prime_sym)`
- Validate bilinear relation: r = L(u)·u symbolically
- Test round-trip transformation

**Deliverable**: `ks_symbolic.py` (Part 1/3)

#### Step 1.3: Pairwise Spinor Hamiltonian (Days 4-5)
- Implement `KSPairwiseHamiltonian` class
- Three spinors: u₁₂, u₂₃, u₃₁ (12D)
- Symbolic kinetic energy in spinor coordinates
- Symbolic potential energy
- Constraint equations as symbolic expressions:
  ```python
  constraints = [
      |u_12|^2 - r_12,  # Bilinear for pair 1-2
      |u_23|^2 - r_23,  # Bilinear for pair 2-3
      |u_31|^2 - r_31,  # Bilinear for pair 3-1
      # Closure constraint (triangle closure)
  ]
  ```

**Deliverable**: `ks_symbolic.py` (Part 2/3)

#### Step 1.4: Extended Phase Space and Hessian (Days 6-7)
- Implement fictitious time s formulation
- Extended Hamiltonian: K(u, u', s)
- Compute symbolic Hessian: ∇²K
- Compute symbolic variational equations
- Helper functions for Morales-Ramis analysis

**Deliverable**: `ks_symbolic.py` (Part 3/3) - COMPLETE

#### Step 1.5: Integration and Testing (Day 7)
- Unit tests: bilinear relation, round-trip
- Symbolic verification tests
- Constraint manifold tests
- Hessian computation tests
- Update `symbolic_lifts/__init__.py`

**Deliverable**: Test suite for `ks_symbolic.py`

---

### Phase 2: Visualization Infrastructure (Days 8-11)

**Objective**: Create publication-quality visualization tools for WP2 components

#### Step 2.1: Visualization Module Structure (Day 8 morning)
- Create `src/python/visualization/` package
- Submodules:
  - `connection_plots.py`
  - `curvature_plots.py`
  - `metric_plots.py`
  - `trajectory_plots.py`
  - `common.py` (shared utilities)

**Deliverable**: Package structure

#### Step 2.2: Connection Visualization (Day 8)
- Vector field plots: `plot_connection_field()`
- Streamline plots: `plot_connection_streamlines()`
- Magnitude heatmap: `plot_connection_magnitude()`
- Holonomy visualization: `plot_holonomy_loop()`

**Deliverable**: `connection_plots.py`

#### Step 2.3: Curvature Visualization (Day 9)
- 2D heatmap: `plot_curvature_heatmap()`
- Contour plots: `plot_curvature_contours()`
- 3D surface: `plot_curvature_surface()`
- Comparison plot: `plot_curvature_vs_chaos()`

**Deliverable**: `curvature_plots.py`

#### Step 2.4: JM Metric Visualization (Day 10)
- Metric ellipsoids: `plot_metric_ellipsoids()`
- Scalar curvature landscape: `plot_scalar_curvature_landscape()`
- Geodesic flow: `plot_geodesic_flow()`
- Correlation scatter: `plot_curvature_vs_lyapunov()`

**Deliverable**: `metric_plots.py`

#### Step 2.5: Trajectory Visualization (Day 11)
- Shape space trajectory: `plot_shape_trajectory()`
- Multi-trajectory comparison: `plot_trajectory_family()`
- S¹ bundle trajectory: `plot_s1_bundle_trajectory()`
- KS spinor trajectory: `plot_ks_trajectory()`
- Lift comparison: `plot_lift_comparison()`

**Deliverable**: `trajectory_plots.py`

---

### Phase 3: Documentation and Tutorials (Day 12)

**Objective**: Create user-friendly documentation and examples

#### Step 3.1: Tutorial Notebooks (Day 12 morning)
- Create `notebooks/tutorials/` directory
- Notebooks:
  1. `01-coordinate-systems.ipynb` - Cartesian, Jacobi, Shape
  2. `02-geometric-reduction.ipynb` - Translation and rotation reduction
  3. `03-connection-and-curvature.ipynb` - Computing A and F
  4. `04-s1-lift.ipynb` - S¹ bundle construction
  5. `05-ks-lift.ipynb` - KS spinor regularization

**Deliverable**: 5 tutorial notebooks

#### Step 3.2: Integration Examples (Day 12 afternoon)
- Create `examples/wp2/` directory
- Examples:
  - `basic_coordinate_transforms.py`
  - `reduction_pipeline.py`
  - `lift_comparison.py`
  - `visualization_gallery.py`

**Deliverable**: Example scripts

#### Step 3.3: User Guide (Day 12 afternoon)
- Update main README with WP2 overview
- Create `docs/WP2-USER-GUIDE.md`
  - Choosing coordinates
  - Interpreting connection/curvature
  - When to use S¹ vs KS lift
  - Troubleshooting common issues

**Deliverable**: User documentation

---

## Detailed Task Breakdown

### Task 1: Symbolic KS Implementation

#### File: `src/python/symbolic_lifts/ks_symbolic.py`

**Structure**:
```python
"""
KS-Spinor Extended Hamiltonian (Symbolic Implementation).

Implements the Kustaanheimo-Stiefel (KS) spinor regularization
in symbolic form for Morales-Ramis integrability analysis.
"""

import sympy as sp
from sympy import Symbol, Matrix, sqrt, simplify
from typing import Tuple, Dict, List
from dataclasses import dataclass

from .common import SymbolicHamiltonianSystem, LiftedHamiltonianBase

# Core Components:

@dataclass
class KSSpinorHamiltonian(LiftedHamiltonianBase):
    """Symbolic KS-Spinor extended Hamiltonian."""

    spinor_vars: Tuple[sp.Symbol, ...]  # u₀, u₁, u₂, u₃
    spinor_momenta: Tuple[sp.Symbol, ...]  # u'₀, u'₁, u'₂, u'₃
    constraints: List[sp.Expr]  # Bilinear constraints
    fictitious_time: sp.Symbol  # s (regularized time)

    def levi_civita_matrix(self, u: Matrix) -> Matrix:
        """Compute Levi-Civita matrix L(u) symbolically."""
        # L(u) definition from WP2.3 design doc
        pass

    def bilinear_relation(self) -> sp.Expr:
        """Return bilinear constraint: |r|² = |u|⁴."""
        pass

    def regularized_hamiltonian(self) -> sp.Expr:
        """Compute K = Σ |u'|²/|u|² - V_reg."""
        pass

    def compute_hessian(self) -> Matrix:
        """Compute Hessian ∇²K for Morales-Ramis."""
        pass

@dataclass
class KSPairwiseHamiltonian:
    """Pairwise KS Hamiltonian for three-body problem."""

    u_12: Tuple[sp.Symbol, ...]  # Spinor for pair 1-2
    u_23: Tuple[sp.Symbol, ...]  # Spinor for pair 2-3
    u_31: Tuple[sp.Symbol, ...]  # Spinor for pair 3-1

    # Similar methods for three simultaneous KS transforms

# Factory functions:
def create_ks_hamiltonian_single_pair(
    m1: float, m2: float
) -> KSSpinorHamiltonian:
    """Create symbolic KS Hamiltonian for single two-body pair."""
    pass

def create_ks_hamiltonian_3bp_pairwise(
    m1: float, m2: float, m3: float
) -> KSPairwiseHamiltonian:
    """Create pairwise KS Hamiltonian for 3BP."""
    pass

# Utilities:
def symbolic_ks_transform(
    r_vec: Matrix, v_vec: Matrix
) -> Tuple[Matrix, Matrix]:
    """Symbolic KS transform: (r, v) → (u, u')."""
    pass

def symbolic_ks_inverse(
    u: Matrix, u_prime: Matrix
) -> Tuple[Matrix, Matrix]:
    """Symbolic KS inverse: (u, u') → (r, v)."""
    pass
```

**Testing** (`tests/symbolic_lifts/test_ks_symbolic.py`):
- Test bilinear relation holds symbolically
- Test Levi-Civita matrix properties
- Test round-trip transformation
- Test Hessian computation
- Test constraint Jacobian

---

### Task 2: Visualization Infrastructure

#### File: `src/python/visualization/connection_plots.py`

**Key Functions**:
```python
def plot_connection_field(
    connection_form: ConnectionForm,
    grid_resolution: int = 50,
    arrow_scale: float = 1.0,
    **kwargs
) -> Figure:
    """
    Plot connection one-form as vector field on shape space.

    Parameters:
        connection_form: Connection object from geometry module
        grid_resolution: Number of grid points per dimension
        arrow_scale: Scale factor for arrow lengths

    Returns:
        Matplotlib figure
    """
    # Create grid in (r₁₂, r₂₃) space (fixed r₃₁ via triangle ineq)
    # Evaluate A at each grid point
    # Plot as quiver (vector field)
    # Add magnitude colormap
    # Add labels, title, colorbar
    pass

def plot_connection_magnitude_heatmap(
    connection_form: ConnectionForm,
    grid_resolution: int = 100,
    **kwargs
) -> Figure:
    """2D heatmap of |A(s)|."""
    pass

def plot_holonomy_loop(
    connection_form: ConnectionForm,
    loop_path: np.ndarray,
    **kwargs
) -> Tuple[Figure, float]:
    """
    Visualize holonomy around a closed loop.

    Returns:
        Figure and computed holonomy value ∮A
    """
    pass
```

#### File: `src/python/visualization/curvature_plots.py`

**Key Functions**:
```python
def plot_curvature_heatmap(
    curvature_form: CurvatureForm,
    grid_resolution: int = 100,
    **kwargs
) -> Figure:
    """2D heatmap of |F(s)| on shape space."""
    pass

def plot_curvature_vs_chaos(
    curvature_values: np.ndarray,
    lyapunov_exponents: np.ndarray,
    **kwargs
) -> Figure:
    """
    Scatter plot: Curvature magnitude vs. max Lyapunov exponent.

    Shows correlation between geometric obstruction and chaos.
    """
    pass
```

#### File: `src/python/visualization/metric_plots.py`

**Key Functions**:
```python
def plot_jm_metric_ellipsoids(
    metric: RiemannianMetric,
    sample_points: np.ndarray,
    **kwargs
) -> Figure:
    """
    Plot JM metric as ellipsoids at sample points in shape space.

    Visualizes anisotropy and energy dependence of metric.
    """
    pass

def plot_scalar_curvature_landscape(
    metric: RiemannianMetric,
    energy: float,
    grid_resolution: int = 100,
    **kwargs
) -> Figure:
    """
    3D surface plot of scalar curvature R(s, E).

    Shows regions of negative curvature (chaos-prone).
    """
    pass
```

#### File: `src/python/visualization/trajectory_plots.py`

**Key Functions**:
```python
def plot_shape_trajectory(
    trajectory: np.ndarray,
    color_by: str = 'time',  # 'time', 'energy', 'chaos'
    **kwargs
) -> Figure:
    """Plot trajectory in shape space coordinates."""
    pass

def plot_lift_comparison(
    traj_reduced: np.ndarray,
    traj_s1: np.ndarray,
    traj_ks: np.ndarray,
    **kwargs
) -> Figure:
    """
    Compare same trajectory in three representations:
    - Reduced (shape space)
    - S¹ lifted
    - KS spinor lifted

    Multi-panel figure showing projections.
    """
    pass
```

---

### Task 3: Documentation and Tutorials

#### Notebook 1: `notebooks/tutorials/01-coordinate-systems.ipynb`

**Content**:
1. Introduction to three-body problem
2. Cartesian coordinates
   - Define state
   - Compute energy, momentum
   - Example: Lagrange L₄ point
3. Jacobi coordinates
   - Definition and physical meaning
   - Transformation
   - Hamiltonian decoupling demonstration
4. Shape space coordinates
   - Distance representation (r₁₂, r₂₃, r₃₁)
   - Triangle constraints
   - Example: Figure-8 orbit in shape space
5. Round-trip validation
   - Transform chain: Cartesian → Jacobi → Shape → Cartesian
   - Error analysis

#### Notebook 2: `notebooks/tutorials/02-geometric-reduction.ipynb`

**Content**:
1. Symmetries and reduction
2. Translation reduction
   - Barycenter constraint
   - Dimension reduction: 18D → 15D
3. Rotation reduction
   - Angular momentum conservation
   - Orientation fixing conventions
   - Dimension reduction: 15D → 12D (planar: 7D)
4. Full reduction pipeline
   - End-to-end example
5. Validation
   - Conservation laws

#### Notebook 3: `notebooks/tutorials/03-connection-and-curvature.ipynb`

**Content**:
1. Geometric mechanics background
2. Locked inertia tensor
   - Definition and computation
   - Physical interpretation
3. Mechanical connection A
   - Computation
   - Visualization
4. Curvature F = dA
   - Numerical computation via finite differences
   - Stokes' theorem validation
5. Scientific significance
   - F ≠ 0 ⟹ non-integrability

#### Notebook 4: `notebooks/tutorials/04-s1-lift.ipynb`

**Content**:
1. Principal bundles (gentle introduction)
2. S¹ bundle construction
   - Bundle coordinates (s, θ)
   - Extended symplectic form
3. Lifted Hamiltonian
   - θ-independence
   - Conserved fiber momentum p_θ
4. Integration example
   - Lifted dynamics
   - Conservation validation
5. Integrability test
   - Three integrals: E, L, p_θ
   - Involution verification

#### Notebook 5: `notebooks/tutorials/05-ks-lift.ipynb`

**Content**:
1. Regularization motivation
   - Collision singularities
2. KS transformation (single pair)
   - Levi-Civita matrix
   - Bilinear relation
3. Pairwise extension (3BP)
   - Three spinors
   - Constraints
4. Time regularization
   - Fictitious time s
   - Sundman transformation
5. Collision simulation
   - Integrate through r → 0
   - Compare with non-regularized
6. Comparison: S¹ vs KS
   - When to use which

---

## Success Criteria

### Phase 1: Symbolic KS (MUST HAVE)
- [ ] `ks_symbolic.py` module complete (~400-500 lines)
- [ ] All symbolic KS classes implemented
- [ ] Symbolic Hessian computation working
- [ ] Test suite passing (>95% coverage)
- [ ] Integration with existing symbolic_lifts package
- [ ] Documentation complete (docstrings, type hints)

### Phase 2: Visualization (SHOULD HAVE)
- [ ] 4 visualization modules created
- [ ] At least 12 visualization functions implemented
- [ ] Publication-quality plot defaults
- [ ] Example gallery created
- [ ] Integration with existing geometry/lifts modules
- [ ] Test plots generated for validation

### Phase 3: Documentation (NICE TO HAVE)
- [ ] 5 tutorial notebooks complete
- [ ] 4+ example scripts
- [ ] User guide written
- [ ] All notebooks executable without errors
- [ ] Clear pedagogical progression

---

## Integration and Testing

### Integration Points

1. **Symbolic KS ↔ Numerical KS**
   - Cross-validation: symbolic expressions vs. numerical implementations
   - Test: symbolic.subs() values match numerical functions

2. **Symbolic KS → WP4.2**
   - Hessian export for Morales-Ramis analysis
   - Variational equation generation
   - Interface with Kovacic algorithm

3. **Visualization ↔ All WP2 Components**
   - Connection module → connection_plots
   - Curvature module → curvature_plots
   - Metric module → metric_plots
   - Trajectory data → trajectory_plots

### Testing Strategy

**Unit Tests**:
- Each symbolic function tested independently
- Each visualization function tested (output is Figure object)
- Notebooks tested for execution

**Integration Tests**:
- Full pipeline: Generate data → Visualize → Validate
- Symbolic ↔ Numerical agreement
- End-to-end workflows

**Validation Tests**:
- Symbolic identities (bilinear relation, etc.)
- Visual regression tests (plot outputs)
- Notebook execution tests (nbval)

---

## Timeline and Milestones

### Week 1 (Days 1-5): Symbolic KS Implementation
**Days 1-2**: Architecture + Core KS
**Days 3-4**: Pairwise Hamiltonian
**Day 5**: Extended phase space + Hessian

**Milestone 1**: Symbolic KS module complete and tested

### Week 2 (Days 6-10): Visualization + Documentation
**Days 6-7**: Visualization modules (connection, curvature)
**Days 8-9**: Visualization modules (metric, trajectory)
**Day 10**: Tutorials and documentation

**Milestone 2**: Visualization infrastructure complete

### Week 2+ (Days 11-12): Polish and Integration
**Day 11**: Integration testing
**Day 12**: Documentation finalization, example gallery

**Milestone 3**: WP2 at 100% completion

---

## Risk Assessment

### Technical Risks

**Risk 1: Symbolic Complexity**
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - Start with simplified cases (planar, equal mass)
  - Use SymPy simplification aggressively
  - Can fall back to numerical Hessian if symbolic too complex

**Risk 2: Visualization Performance**
- **Probability**: Low
- **Impact**: Low
- **Mitigation**:
  - Use efficient matplotlib backends
  - Cache grid evaluations
  - Provide low-resolution defaults

**Risk 3: Time Estimation**
- **Probability**: Medium
- **Impact**: Low
- **Mitigation**:
  - Prioritization: P0 (symbolic) → P1 (viz) → P2 (docs)
  - Can defer P2 if time constrained
  - Visualization can be incremental

---

## Dependencies

### External Dependencies
- sympy >= 1.12 (symbolic computation)
- matplotlib >= 3.8 (visualization)
- jupyter >= 1.0 (notebooks)
- nbval (notebook testing)

### Internal Dependencies
- All existing WP2 modules (coordinates, geometry, lifts, regularization)
- WP1 integrators (for trajectory generation)

---

## Deliverables Summary

### Code Deliverables
1. `src/python/symbolic_lifts/ks_symbolic.py` (~400-500 lines)
2. `src/python/visualization/` package (~800-1000 lines)
   - `connection_plots.py`
   - `curvature_plots.py`
   - `metric_plots.py`
   - `trajectory_plots.py`
   - `common.py`
3. Test suites (~300-400 lines)

### Documentation Deliverables
1. 5 tutorial notebooks (~500-1000 lines total)
2. 4+ example scripts (~200-300 lines)
3. User guide document
4. Updated README

### Total New Code
- Implementation: ~1,500-2,000 lines
- Tests: ~400-500 lines
- Documentation/Examples: ~1,000-1,500 lines
- **Grand Total**: ~3,000-4,000 lines

---

## Conclusion

This plan provides a **comprehensive roadmap** to bring WP2 from 85% to 100% completion. The gaps are well-understood and addressable with focused effort:

1. **Symbolic KS** (P0): Critical for WP4.2, well-scoped, 5-7 days
2. **Visualization** (P1): Enhances usability, modular, 3-4 days
3. **Documentation** (P2): Improves accessibility, incremental, 1-2 days

**Total Estimated Duration**: 8-12 days
**Recommended Approach**: Implement in priority order (P0 → P1 → P2)

Upon completion, WP2 will provide a **complete, production-ready foundation** for:
- WP3: Killing tensor search
- WP4: Morales-Ramis integrability analysis
- WP5: Machine learning integration

---

**Plan Status**: Ready for Implementation
**Next Action**: Begin Phase 1, Task 1.1 (Symbolic KS Architecture Design)
**Owner**: TBD
**Review Date**: After Milestone 1 completion
