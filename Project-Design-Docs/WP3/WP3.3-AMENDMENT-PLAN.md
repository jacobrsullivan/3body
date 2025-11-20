# WP3.3 Implementation Assessment and Amendment Plan
## Comprehensive Analysis and Roadmap for Complex Integral Search

**Assessment Date**: 2025-11-20
**Status**: AMENDMENT PLAN
**Purpose**: Document current implementation state, identify gaps, and plan amendments for discovering complex integrals

---

## Executive Summary

This document assesses the current WP3.3 (Symbolic Regression and Consolidation) implementation status and provides a comprehensive amendment plan to enable discovery of potentially complex conserved quantities in the three-body problem.

**Key Findings**:
- ✅ **Core infrastructure** (SINDy, PySR, basic basis functions) is **IMPLEMENTED**
- ⚠️ **Advanced basis functions** (spinor, elliptic, theta) are **NOT IMPLEMENTED**
- ⚠️ **Multi-scale validation** for complex integrals is **NOT IMPLEMENTED**
- ✅ **Integration framework** (WP3.1 → WP3.3, WP3.2 → WP3.3) is **COMPLETE**

**Recommendation**: Proceed with phased implementation of AMENDED features, prioritizing spinor basis (KS-motivated) and elliptic function search.

---

## Part 1: Current Implementation Status

### 1.1 Implemented Components (✅ COMPLETE)

#### Module: `src/python/symbolic/basis_functions.py` (549 lines)

**Status**: ✅ **FUNCTIONAL**

**Implemented Features**:
- `BasisFunction` dataclass for individual basis functions
- `BasisLibrary` class for managing collections
- `construct_polynomial_basis()` - polynomials up to degree 3
- `construct_transcendental_basis()` - sin, cos, exp, log, sqrt, tanh
- `construct_conservation_basis()` - Energy (E), angular momentum (L), powers
- `construct_hierarchical_basis()` - main API with adaptive refinement
- `get_pysr_operators()` - operator configuration for PySR

**Coordinate Systems Supported**:
- Cartesian
- S¹ bundle
- KS spinor (structure defined, but spinor basis functions NOT implemented)
- Shape space

**Basis Function Categories**:
| Category | Count | Degree | Status |
|----------|-------|--------|--------|
| Constant | 1 | 0 | ✅ |
| Linear | ~10 | 1 | ✅ |
| Quadratic | ~50 | 2 | ✅ |
| Cubic | ~100 | 3 | ✅ |
| Transcendental | ~30 | 0 | ✅ |
| Conservation | ~5 | 2-4 | ✅ |
| **Total (Standard)** | **~200** | - | **✅** |

---

#### Module: `src/python/symbolic/regression_pipeline.py` (520 lines)

**Status**: ✅ **FUNCTIONAL**

**Implemented Methods**:
1. **`sindy_regression()`**:
   - Sparse Identification of Nonlinear Dynamics
   - Uses STLSQ (Sequential Thresholded Least Squares)
   - Enforces sparsity (few terms)
   - Fast (seconds to minutes)
   - ✅ **COMPLETE**

2. **`pysr_regression()`**:
   - Python Symbolic Regression via genetic programming
   - Evolutionary search over expression trees
   - Pareto optimization (accuracy vs. complexity)
   - Slow (minutes to hours)
   - ✅ **COMPLETE**

3. **`hierarchical_regression()`**:
   - Adaptive complexity increase (degree 1 → 2 → 3 → transcendental)
   - Stops when good fit found
   - ✅ **COMPLETE**

4. **`compare_methods()`**:
   - Benchmarks SINDy vs. PySR
   - ✅ **COMPLETE**

**Dependencies**:
- `pysindy` - ✅ Optional (graceful degradation if missing)
- `pysr` - ✅ Optional (graceful degradation if missing)
- `sympy` - ✅ Required

---

#### Module: `src/python/symbolic/geometric_invariants.py` (447 lines)

**Status**: ✅ **FUNCTIONAL**

**Implemented Features**:
- `GeometricQuantities` dataclass
- `compute_all_geometric_invariants()` - distances, velocities, angular momenta
- `compute_mutual_distances()` - r₁₂, r₂₃, r₃₁
- `compute_radial_velocities()` - ṙ₁₂, ṙ₂₃, ṙ₃₁
- `compute_angular_momentum_vectors()` - **L**₁₂, **L**₂₃, **L**₃₁, **L**_total
- `compute_moment_of_inertia()` - I = Σ m_i |**r**_i|²
- `compute_shape_coordinates()` - (s₁, s₂, s₃) shape space
- `create_geometric_basis_functions()` - factory for geometric basis

**Coverage**: ✅ All standard geometric invariants for three-body problem

---

#### Module: `src/python/symbolic/simplification.py` (487 lines)

**Status**: ✅ **FUNCTIONAL**

**Implemented Features**:
- `count_operations()` - complexity metric
- `round_coefficients()` - remove numerical noise
- `simplify_expression()` - SymPy simplification
- `extract_common_factors()` - algebraic factorization
- `substitute_conserved_quantities()` - replace E, L with symbols
- `minimize_expression_tree()` - reduce AST depth
- `format_for_publication()` - LaTeX generation
- `verify_numerical_equivalence()` - test symbolic = numerical
- `simplify_candidate_integral()` - main API

**Status**: ✅ **COMPLETE** for polynomial and rational expressions

---

#### Module: `src/python/symbolic/validation.py` (512 lines)

**Status**: ✅ **FUNCTIONAL**

**Implemented Features**:
- `lambdify_expression()` - SymPy → NumPy function
- `validate_symbolic_numerical_agreement()` - residual test
- `test_conservation_on_trajectory()` - single trajectory conservation
- `test_conservation_ensemble()` - multiple trajectories
- `compute_poisson_bracket_symbolic()` - {I, H}
- `check_functional_independence()` - Jacobian rank test
- `validate_candidate_integral()` - main validation API

**Validation Criteria**:
- Conservation error < 10⁻⁶ (default threshold)
- Poisson bracket {I, H} ≈ 0
- Functional independence via Jacobian rank

**Status**: ✅ **COMPLETE** for standard polynomial integrals

---

#### Module: `src/python/symbolic/candidate_ranking.py` (534 lines)

**Status**: ✅ **FUNCTIONAL**

**Implemented Features**:
- `CandidateIntegral` dataclass - metadata for candidates
- `CandidateSource` enum - KILLING_FIELD, ML_DISCOVERY, SYMBOLIC_REGRESSION
- `compute_candidate_score()` - multi-criteria scoring
- `detect_duplicate_candidates()` - symbolic + numerical equivalence
- `filter_trivial_candidates()` - remove known integrals
- `consolidate_and_rank()` - main consolidation API
- `create_candidate_from_wp31_killing()` - WP3.1 integration
- `create_candidate_from_wp32_ml()` - WP3.2 integration
- `generate_candidate_report()` - Markdown/LaTeX output

**Scoring Function**:
```
Score = w_cons * log10(error) + w_comp * complexity + w_indep * penalty
```

**Status**: ✅ **COMPLETE** for standard ranking

---

### 1.2 Partially Implemented / Limited Components (⚠️)

None - all implemented modules are fully functional for their intended scope.

---

### 1.3 NOT Implemented Components (❌)

The following components are **proposed in AMENDED documents but NOT YET implemented**:

#### 1.3.1 Spinor Basis Functions (❌ NOT IMPLEMENTED)

**File**: `src/python/symbolic/spinor_basis.py` (DOES NOT EXIST)

**Proposed Features** (from AMENDED_Task-3.3.2):
- `SpinorCoordinates` dataclass
- `cartesian_to_ks_spinors()` - Cartesian → KS spinor conversion
- `position_to_spinor()` - 3D position → 4D spinor (KS map)
- `velocity_to_spinor_momentum()` - velocity → spinor momentum
- `construct_spinor_basis()` - ~80 basis functions:
  - Individual components: u₁₂₀, u₁₂₁, u₁₂₂, u₁₂₃, ... (24 functions)
  - Bilinear products: ⟨u₁₂, u₂₃⟩, ... (9 functions)
  - Quaternion products: u₁₂ ⊗ u₂₃ (6 functions)
  - Norms: |u₁₂|², ... (6 functions)
  - Mixed: u₁₂ · u̇₁₂ (3 functions)
- `quaternion_product_norm()` - non-commutative product

**Estimated Code**: ~600 lines

**Priority**: 🔴 **HIGH** (KS regularization is central to three-body theory)

---

#### 1.3.2 Elliptic Function Basis (❌ NOT IMPLEMENTED)

**File**: `src/python/symbolic/elliptic_basis.py` (DOES NOT EXIST)

**Proposed Features** (from AMENDED_Task-3.3.2):
- `construct_jacobi_elliptic_basis()` - Jacobi sn, cn, dn functions
  - Moduli: k = 0.5, 0.7, 0.9, ...
  - Arguments: √E, E·θ, L/√E, r₁₂·√E, ...
  - ~60 templates
- `construct_weierstrass_elliptic_basis()` - Weierstrass ℘ function
  - Lattice parameters: ω₁, ω₂ (to be fitted)
  - ~30 templates
- `make_elliptic_function()` - factory for elliptic basis elements
- `make_weierstrass_function()` - factory for Weierstrass elements
- `get_argument_functions()` - physically motivated arguments

**Dependencies**: `mpmath` or `scipy.special` (not currently in requirements)

**Estimated Code**: ~700 lines

**Priority**: 🟡 **MEDIUM** (theoretically motivated but computationally expensive)

---

#### 1.3.3 Theta Function Basis (❌ NOT IMPLEMENTED)

**File**: `src/python/symbolic/theta_basis.py` (DOES NOT EXIST)

**Proposed Features** (from AMENDED_Task-3.3.2):
- `construct_theta_basis()` - Jacobi θ₁, θ₂, θ₃, θ₄
  - Nome parameter: q = exp(iπτ)
  - ~16 templates (4 theta functions × 4 argument types)
- `make_theta_function()` - factory

**Dependencies**: `mpmath.jtheta`

**Estimated Code**: ~300 lines

**Priority**: 🟢 **LOW** (advanced, only if elliptic functions fail)

---

#### 1.3.4 Multi-Scale Conservation Testing (❌ NOT IMPLEMENTED)

**Location**: Should extend `src/python/symbolic/validation.py`

**Proposed Features** (from AMENDED_WP3.3):
- `multi_scale_conservation_test()` - test at dt = 0.01, 0.1, 1.0, 10.0
- `identify_function_type()` - classify as polynomial, rational, elliptic, etc.
- Enhanced `validate_candidate_integral()` with multi-scale tests

**Estimated Code**: ~200 lines (additions to validation.py)

**Priority**: 🟡 **MEDIUM** (useful for complex integrals)

---

#### 1.3.5 Enhanced Candidate Scoring (❌ NOT IMPLEMENTED)

**Location**: Should extend `src/python/symbolic/candidate_ranking.py`

**Proposed Features** (from AMENDED_WP3.3):
- Function-type bonuses: spinor_bilinear (-30), elliptic (+50), theta (+100)
- Interpretability bonus: -50 if physical interpretation clear
- Enhanced `compute_enhanced_score()` function

**Estimated Code**: ~100 lines (modifications to candidate_ranking.py)

**Priority**: 🟢 **LOW** (nice-to-have for ranking complex expressions)

---

## Part 2: Gap Analysis

### 2.1 Implementation vs. Original Task Documents

| Task Document | Original Promise | Current Implementation | Gap |
|---------------|------------------|----------------------|-----|
| Task 3.3.1 | SINDy, PySR regression | ✅ COMPLETE | None |
| Task 3.3.1 | Hierarchical search | ✅ COMPLETE | None |
| Task 3.3.2 | Polynomial basis | ✅ COMPLETE | None |
| Task 3.3.2 | Geometric invariants | ✅ COMPLETE | None |
| Task 3.3.2 | Transcendental functions | ✅ COMPLETE | None |
| Task 3.3.3 | Candidate consolidation | ✅ COMPLETE | None |
| Task 3.3.3 | Duplicate detection | ✅ COMPLETE | None |
| Task 3.3.3 | Ranking and scoring | ✅ COMPLETE | None |

**Summary**: ✅ **All original Task promises are FULFILLED**

---

### 2.2 Implementation vs. AMENDED Proposals

| AMENDED Feature | Proposed Location | Current Status | Gap |
|----------------|-------------------|----------------|-----|
| Spinor basis | `spinor_basis.py` | ❌ NOT EXISTS | ~600 lines |
| Elliptic functions | `elliptic_basis.py` | ❌ NOT EXISTS | ~700 lines |
| Theta functions | `theta_basis.py` | ❌ NOT EXISTS | ~300 lines |
| Multi-scale validation | `validation.py` (extend) | ❌ NOT IMPLEMENTED | ~200 lines |
| Enhanced scoring | `candidate_ranking.py` (extend) | ❌ NOT IMPLEMENTED | ~100 lines |
| **TOTAL GAP** | - | - | **~1,900 lines** |

**Summary**: ⚠️ **AMENDED features are NOT YET implemented** (as expected, they are proposals)

---

## Part 3: Prioritized Amendment Plan

### 3.1 Phase 1: High Priority (Weeks 1-2)

**Goal**: Implement KS spinor basis (most physically motivated)

#### Task 3.3.1 Amendment: Spinor Regression Support

**Documents to Create**:
- ✅ AMENDED_Task-3.3.1-Implementation-Plan.md (TO BE CREATED)

**Implementation**:
1. Create `src/python/symbolic/spinor_basis.py`:
   - KS transformation functions
   - Spinor basis construction (~80 functions)
   - Quaternion algebra utilities

2. Extend `src/python/symbolic/basis_functions.py`:
   - Add `add_spinor_basis()` method to `BasisLibrary`
   - Integrate with `construct_hierarchical_basis()`

3. Testing:
   - Unit tests: Verify |u|² = r (KS norm condition)
   - Integration test: Recover Kepler integrals in spinor form

**Deliverables**:
- [ ] `spinor_basis.py` (~600 lines)
- [ ] Tests in `tests/wp3/test_spinor_basis.py` (~200 lines)
- [ ] Documentation: "KS Spinor Geometry Tutorial"

**Effort**: 5-7 days

**Risk**: 🟡 MEDIUM - KS transformation is well-defined but momentum map is subtle

---

### 3.2 Phase 2: Medium Priority (Weeks 3-4)

**Goal**: Add elliptic function search capability

#### Task 3.3.2 Complete Amendment

**Documents to Create**:
- ✅ AMENDED_Task-3.3.2-Implementation-Plan.md (ALREADY CREATED)

**Implementation**:
1. Create `src/python/symbolic/elliptic_basis.py`:
   - Jacobi elliptic functions (sn, cn, dn)
   - Weierstrass ℘ function
   - Argument templates

2. Add dependencies:
   - `mpmath` for arbitrary precision elliptic functions
   - Update `requirements.txt`

3. Extend `regression_pipeline.py`:
   - Add `elliptic_regression()` method
   - Parameter fitting (modulus k, lattice ω)

4. Testing:
   - Validate on simple pendulum (known elliptic solution)
   - Test on Kowalevskaya top integral

**Deliverables**:
- [ ] `elliptic_basis.py` (~700 lines)
- [ ] Modified `regression_pipeline.py` (+200 lines)
- [ ] Tests in `tests/wp3/test_elliptic_basis.py` (~300 lines)
- [ ] Tutorial: "Elliptic Functions in Mechanics"

**Effort**: 6-8 days

**Risk**: 🔴 HIGH - Numerical stability of elliptic functions, parameter fitting complexity

---

### 3.3 Phase 3: Medium Priority (Week 5)

**Goal**: Enhanced validation for complex integrals

#### Task 3.3.3 Amendment: Multi-Scale Testing

**Documents to Create**:
- ✅ AMENDED_Task-3.3.3-Implementation-Plan.md (TO BE CREATED)

**Implementation**:
1. Extend `src/python/symbolic/validation.py`:
   - `multi_scale_conservation_test()` - test at multiple time scales
   - `identify_function_type()` - classify expression type
   - Enhanced conservation error metrics

2. Extend `src/python/symbolic/candidate_ranking.py`:
   - Function-type aware scoring
   - Interpretability bonus
   - Physical interpretation heuristics

**Deliverables**:
- [ ] Extended `validation.py` (+200 lines)
- [ ] Extended `candidate_ranking.py` (+100 lines)
- [ ] Tests in `tests/wp3/test_enhanced_validation.py` (~150 lines)

**Effort**: 3-4 days

**Risk**: 🟢 LOW - Extends existing functionality

---

### 3.4 Phase 4: Low Priority (Week 6, if needed)

**Goal**: Theta functions for doubly-periodic motion

#### Optional: Theta Function Basis

**Implementation**:
1. Create `src/python/symbolic/theta_basis.py`:
   - Jacobi theta functions θ₁, θ₂, θ₃, θ₄
   - Nome parameter fitting

2. Integration with regression pipeline

**Deliverables**:
- [ ] `theta_basis.py` (~300 lines)
- [ ] Tests (~100 lines)

**Effort**: 2-3 days

**Risk**: 🟢 LOW - Only proceed if elliptic functions show promise

---

## Part 4: Required AMENDED Documents

### 4.1 Documents Already Created ✅

1. ✅ **AMENDED_WP3.3-Symbolic-Regression-Summary.md**
   - Status: COMPLETE
   - Commit: 1021362
   - Content: Extended overview with elliptic/theta functions, multi-scale testing

2. ✅ **AMENDED_Task-3.3.2-Implementation-Plan.md**
   - Status: COMPLETE
   - Commit: 1021362
   - Content: Spinor, elliptic, theta basis implementation details

---

### 4.2 Documents to Create ❌

1. ❌ **AMENDED_Task-3.3.1-Implementation-Plan.md**
   - **Purpose**: Extend regression pipeline for elliptic function search
   - **Key Sections**:
     - Elliptic function regression strategy
     - Parameter fitting (modulus k, lattice ω)
     - Integration with existing SINDy/PySR pipeline
     - Performance benchmarks
   - **Priority**: 🔴 HIGH
   - **Effort**: 2 hours

2. ❌ **AMENDED_Task-3.3.3-Implementation-Plan.md**
   - **Purpose**: Enhanced candidate ranking for complex integrals
   - **Key Sections**:
     - Multi-scale conservation testing
     - Function-type classification and scoring
     - Physical interpretability heuristics
     - Enhanced consolidation workflow
   - **Priority**: 🟡 MEDIUM
   - **Effort**: 1.5 hours

---

## Part 5: Testing and Validation Strategy

### 5.1 Unit Tests (Per Module)

| Module | Test File | Status | Priority |
|--------|-----------|--------|----------|
| `spinor_basis.py` | `test_spinor_basis.py` | ❌ NOT EXISTS | 🔴 HIGH |
| `elliptic_basis.py` | `test_elliptic_basis.py` | ❌ NOT EXISTS | 🟡 MEDIUM |
| `theta_basis.py` | `test_theta_basis.py` | ❌ NOT EXISTS | 🟢 LOW |

**Test Coverage Goals**:
- Unit tests: >90%
- Integration tests: >80%

---

### 5.2 Benchmark Cases

**Test Integrals** (known answers for validation):

1. **Kepler Problem** (2-body):
   - Energy: E = p²/2 - 1/r
   - Angular momentum: L = r × p
   - Runge-Lenz vector: **A** = **p** × **L** - **r**/r
   - **Test**: Can spinor basis recover these?

2. **Simple Pendulum**:
   - Exact solution: θ(t) = 2 arcsin(k sn(ωt, k))
   - **Test**: Can elliptic regression find this?

3. **Kowalevskaya Top**:
   - Integral involves elliptic function
   - **Test**: Validate elliptic function search

---

### 5.3 Integration Tests

**End-to-End Workflow Tests**:

1. WP3.1 → WP3.3 (Spinor):
   - Killing field → numerical integral → spinor regression → validation

2. WP3.2 → WP3.3 (Elliptic):
   - ML prediction → elliptic regression → multi-scale validation

3. Full Consolidation:
   - Multiple candidates (polynomial, spinor, elliptic) → ranking → report

**Test File**: `tests/integration/test_wp3_amended_pipeline.py` (TO BE CREATED)

---

## Part 6: Dependency Management

### 6.1 Current Dependencies

**Required** (already in `requirements.txt`):
- `numpy`
- `scipy`
- `sympy`

**Optional** (graceful degradation):
- `pysindy`
- `pysr` (requires Julia)

**Status**: ✅ Well-managed with try/except imports

---

### 6.2 New Dependencies Needed

**For Spinor Basis**:
- `quaternion` (optional) - for quaternion algebra
  - Alternative: Implement manually (preferred for minimal dependencies)

**For Elliptic Functions**:
- `mpmath` - arbitrary precision elliptic functions
  - **Priority**: 🔴 HIGH
  - **Action**: Add to `requirements.txt`

**For Theta Functions**:
- `mpmath` - Jacobi theta functions (same as above)

**Recommendation**: Add `mpmath` as optional dependency with graceful degradation.

---

## Part 7: Timeline and Milestones

### 7.1 Phased Rollout

| Phase | Duration | Deliverables | Milestone |
|-------|----------|--------------|-----------|
| **Phase 0** | Week 0 | Amendment plan, AMENDED docs | Planning complete |
| **Phase 1** | Weeks 1-2 | Spinor basis implementation | KS basis functional |
| **Phase 2** | Weeks 3-4 | Elliptic function basis | Elliptic search operational |
| **Phase 3** | Week 5 | Enhanced validation & ranking | Multi-scale testing |
| **Phase 4** | Week 6 | Theta functions (optional) | Full AMENDED pipeline |
| **Total** | **5-6 weeks** | - | **AMENDED WP3.3 Complete** |

---

### 7.2 Success Criteria

**Minimum Success** (Phase 1):
- [ ] Spinor basis implemented and tested
- [ ] Can construct ~80 spinor-based basis functions
- [ ] Regression recovers Kepler integrals in spinor form

**Target Success** (Phases 1-3):
- [ ] Spinor + elliptic basis functional
- [ ] Multi-scale validation operational
- [ ] Can test complex integrals from WP3.1/WP3.2

**Stretch Success** (Phases 1-4):
- [ ] Theta functions implemented
- [ ] Complete AMENDED pipeline tested on three-body problem
- [ ] Discover non-polynomial integral (if exists)

---

## Part 8: Risk Assessment

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Spinor momentum map complexity** | MEDIUM | HIGH | Use simplified formulation; validate on Kepler |
| **Elliptic function numerical stability** | HIGH | MEDIUM | Use `mpmath` arbitrary precision; clipping |
| **Parameter fitting convergence** | HIGH | MEDIUM | Multi-start optimization; coarse grid search |
| **No complex integrals exist** | LOW-MEDIUM | HIGH | Document exhaustive search; negative results valuable |

---

### 8.2 Resource Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Computational cost (PySR + elliptic)** | HIGH | MEDIUM | Hierarchical search; early stopping |
| **Development time underestimated** | MEDIUM | MEDIUM | Phased rollout; prioritize Phase 1 |
| **Library dependency issues** | LOW | LOW | Optional dependencies; graceful degradation |

---

## Part 9: Recommendations

### 9.1 Immediate Actions (This Week)

1. ✅ **Create remaining AMENDED documents**:
   - AMENDED_Task-3.3.1-Implementation-Plan.md
   - AMENDED_Task-3.3.3-Implementation-Plan.md

2. ✅ **Finalize amendment plan** (this document)

3. **Update project roadmap**:
   - Add AMENDED WP3.3 to milestones
   - Communicate timeline to stakeholders

---

### 9.2 Medium-Term Actions (Weeks 1-2)

1. **Begin Phase 1 implementation**:
   - Create `spinor_basis.py`
   - Write unit tests
   - Validate on Kepler problem

2. **Dependency management**:
   - Add `mpmath` to `requirements.txt` (optional)
   - Test installation on clean environment

---

### 9.3 Long-Term Strategy

**Iterative Refinement**:
- Implement spinor basis first (highest priority, KS-motivated)
- Evaluate results before proceeding to elliptic functions
- Only implement theta functions if needed

**Documentation First**:
- Complete all AMENDED documents before implementation
- Ensure design is sound before coding
- Use documents as implementation guide

**Test-Driven Development**:
- Write tests before implementation
- Validate on known cases (Kepler, pendulum, Kowalevskaya)
- Benchmark performance at each phase

---

## Part 10: Conclusion

### 10.1 Summary

**Current State**:
- ✅ Core WP3.3 infrastructure is **COMPLETE and FUNCTIONAL**
- ✅ All original Task promises are **FULFILLED**
- ⚠️ AMENDED features (spinor, elliptic, theta) are **PROPOSALS**, not yet implemented

**Path Forward**:
- 🔴 **HIGH PRIORITY**: Implement spinor basis (Phase 1, Weeks 1-2)
- 🟡 **MEDIUM PRIORITY**: Add elliptic functions (Phase 2, Weeks 3-4)
- 🟡 **MEDIUM PRIORITY**: Enhanced validation (Phase 3, Week 5)
- 🟢 **LOW PRIORITY**: Theta functions (Phase 4, Week 6, optional)

**Estimated Total Effort**: 5-6 weeks for full AMENDED implementation

---

### 10.2 Final Recommendations

1. **Approve AMENDED documents** and amendment plan
2. **Prioritize spinor basis** as most physically motivated
3. **Implement in phases** with validation at each step
4. **Document negative results** if complex integrals not found (still valuable science)

**Sign-off**:
- Technical Lead: _________________ Date: _________
- Project Manager: _________________ Date: _________

---

**Document Version**: 1.0
**Status**: AMENDMENT PLAN
**Next Review**: After Phase 1 completion (Week 2)
**Maintainer**: WP3 Implementation Team

---

## Appendix A: File Structure Comparison

### Current Structure
```
src/python/symbolic/
├── __init__.py                   (220 lines) ✅
├── basis_functions.py            (549 lines) ✅
├── geometric_invariants.py       (447 lines) ✅
├── regression_pipeline.py        (520 lines) ✅
├── simplification.py             (487 lines) ✅
├── validation.py                 (512 lines) ✅
└── candidate_ranking.py          (534 lines) ✅

TOTAL: 3,269 lines ✅ COMPLETE
```

### AMENDED Structure (Proposed)
```
src/python/symbolic/
├── __init__.py                   (220 lines) ✅
├── basis_functions.py            (549 → 650 lines) [+100 for integration]
├── geometric_invariants.py       (447 lines) ✅
├── regression_pipeline.py        (520 → 720 lines) [+200 for elliptic]
├── simplification.py             (487 lines) ✅
├── validation.py                 (512 → 712 lines) [+200 for multi-scale]
├── candidate_ranking.py          (534 → 634 lines) [+100 for enhanced scoring]
│
├── spinor_basis.py               (600 lines) ❌ NEW
├── elliptic_basis.py             (700 lines) ❌ NEW
├── theta_basis.py                (300 lines) ❌ NEW (optional)
└── special_functions_utils.py    (200 lines) ❌ NEW

CURRENT: 3,269 lines
AMENDED: 5,765 lines (+2,496 lines, +76%)
```

---

## Appendix B: Document Checklist

### Documentation Status

- ✅ **AMENDED_WP3.3-Symbolic-Regression-Summary.md** - COMPLETE
- ✅ **AMENDED_Task-3.3.2-Implementation-Plan.md** - COMPLETE
- ❌ **AMENDED_Task-3.3.1-Implementation-Plan.md** - TO BE CREATED
- ❌ **AMENDED_Task-3.3.3-Implementation-Plan.md** - TO BE CREATED
- ✅ **WP3.3-AMENDMENT-PLAN.md** (this document) - COMPLETE

### Next Steps

1. Create remaining AMENDED Task documents
2. Review and approve all AMENDED documentation
3. Begin Phase 1 implementation (spinor basis)
4. Update project tracking with new milestones

---

**END OF AMENDMENT PLAN**
