# WP3 Gap Analysis and Fix Plan
## Date: November 22, 2025
## Status: Comprehensive Review

---

## Executive Summary

While the Implementation Status documents report **100% completion** for WP3, a detailed code review reveals **functional gaps** that prevent the full pipeline from running end-to-end. This document identifies these gaps and provides a prioritized fix plan.

### Key Findings

✅ **Infrastructure Complete**: All module files exist with proper structure
⚠️ **Functional Gaps**: Several `NotImplementedError` blocks prevent execution
⚠️ **Missing Features**: Some advanced features marked as TODO
✅ **Core Logic**: Main algorithms are implemented

### Gap Categories

1. **CRITICAL** (Blocks execution): 5 gaps
2. **HIGH** (Limits functionality): 3 gaps
3. **MEDIUM** (Missing optimizations): 4 gaps
4. **LOW** (Nice-to-have features): 3 gaps

---

## Detailed Gap Analysis

### CRITICAL Gaps (Must Fix)

#### Gap C1: Killing PDE Solver Not Fully Connected
**Location**: `src/python/pde/killing_equations.py:252`
```python
raise NotImplementedError("PDE solution in Task 3.1.3")
```

**Impact**: Cannot solve Killing field equations end-to-end
**Root Cause**: The `solve()` method in `KillingVectorPDE` is a stub
**Status**: The actual solver exists in `killing_solver.py` but the class method doesn't call it

**Fix Required**:
```python
def solve(self, mesh, method='svd'):
    from .killing_solver import solve_killing_fields
    # Delegate to the main solver pipeline
    return solve_killing_fields(...)
```

**Estimated Effort**: 2 hours
**Priority**: P0 - Critical

---

#### Gap C2: Coefficient Extraction for Symbolic PDEs
**Location**: `src/python/pde/killing_equations.py:191`
```python
raise NotImplementedError("Coefficient extraction to be implemented")
```

**Impact**: Cannot extract PDE coefficients for symbolic analysis
**Root Cause**: Symbolic PDE analysis not completed
**Status**: Numerical methods work, but symbolic coefficient extraction missing

**Fix Required**:
- Implement coefficient extraction from SymPy expressions
- Parse PDE terms into coefficient matrices
- Return in sparse format for analysis

**Estimated Effort**: 4 hours
**Priority**: P1 - High (only needed for symbolic analysis, not numerical solving)

---

#### Gap C3: Killing Tensor System Assembly Incomplete
**Location**: `src/python/pde/system_assembly.py:312`
```python
# TODO: Implement full assembly (similar structure to vector case)
```

**Impact**: Cannot search for rank-2 Killing tensors (quadratic integrals)
**Root Cause**: Vector field assembly complete, tensor assembly stub
**Status**: The structure is there but implementation incomplete

**Fix Required**:
- Extend vector assembly logic to tensors
- Handle symmetric tensor constraints
- Assemble ~n(n+1)(n+2)/6 equations per point

**Estimated Effort**: 8 hours
**Priority**: P1 - High (needed for quadratic integral discovery)

---

#### Gap C4: Mesh Adaptive Refinement
**Location**: `src/python/pde/mesh_generation.py:489-495`
```python
# TODO: Implement adaptive refinement
raise NotImplementedError("Mesh refinement not yet implemented")
```

**Impact**: Cannot refine mesh near interesting regions
**Root Cause**: Initial mesh generation works, but adaptive refinement not implemented
**Status**: Coarse and fine meshes can be generated, but no adaptive strategy

**Fix Required**:
- Implement error estimator (residual-based or gradient-based)
- Mark cells for refinement
- Regenerate mesh with higher density in marked regions
- Iterate until convergence

**Estimated Effort**: 12 hours
**Priority**: P2 - Medium (uniform meshes work, this is optimization)

---

#### Gap C5: Helmholtz Decomposition for Vector Fields
**Location**: `src/python/pde/regularization.py:443-445`
```python
# TODO: Implement Helmholtz decomposition
raise NotImplementedError("Helmholtz decomposition not yet implemented")
```

**Impact**: Cannot decompose vector fields into curl-free + divergence-free parts
**Root Cause**: Advanced regularization not implemented
**Status**: Basic regularization works, this is an advanced feature

**Fix Required**:
- Solve for scalar potential φ: K_cf = ∇φ
- Solve for vector potential A: K_df = ∇×A
- Decompose: K = K_cf + K_df

**Estimated Effort**: 10 hours
**Priority**: P2 - Medium (optional advanced feature)

---

### HIGH Priority Gaps

#### Gap H1: Permutation Symmetry Projection
**Location**: `src/python/pde/regularization.py:275`
```python
# TODO: Implement permutation symmetry projection
```

**Impact**: Cannot enforce permutation symmetry for identical particles
**Root Cause**: Symmetry handling incomplete
**Status**: The framework is there but projection not implemented

**Fix Required**:
- Build permutation group representation
- Project Killing fields onto symmetric subspace
- Ensure fields respect particle exchange symmetry

**Estimated Effort**: 6 hours
**Priority**: P1 - High (important for equal-mass systems)

---

#### Gap H2: Geometric Invariant Coordinate Transforms
**Location**: `src/python/symbolic/geometric_invariants.py:98, 105`
```python
# TODO: Implement Jacobi → Cartesian transformation
# TODO: Implement proper reconstruction
```

**Impact**: Cannot convert geometric invariants between coordinate systems
**Root Cause**: Coordinate transformation logic incomplete
**Status**: Basic invariants computed, but coordinate conversions missing

**Fix Required**:
- Implement Jacobi to Cartesian position reconstruction
- Add Cartesian to Jacobi inverse transformation
- Validate on test cases

**Estimated Effort**: 5 hours
**Priority**: P1 - High (needed for multi-coordinate analysis)

---

#### Gap H3: Numerical Equivalence Verification in Simplification
**Location**: `src/python/symbolic/simplification.py:185`
```python
numerical_equivalence=True  # TODO: Verify numerically
```

**Impact**: Simplification might not preserve numerical accuracy
**Root Cause**: Equivalence check not implemented
**Status**: Symbolic simplification works, but numerical verification missing

**Fix Required**:
- Generate random test points
- Evaluate original and simplified expressions
- Check relative error < tolerance
- Return verification result

**Estimated Effort**: 3 hours
**Priority**: P1 - High (important for validation)

---

### MEDIUM Priority Gaps

#### Gap M1: LaTeX Formatting for Candidates
**Location**: `src/python/symbolic/candidate_ranking.py:466`
```python
# TODO: Implement LaTeX formatting
```

**Impact**: Cannot generate publication-ready mathematical expressions
**Root Cause**: Export formatting incomplete
**Status**: Plain text works, LaTeX formatting missing

**Fix Required**:
- Use SymPy's latex() function
- Format candidate expressions in LaTeX
- Add display settings (inline, equation, aligned)

**Estimated Effort**: 2 hours
**Priority**: P2 - Medium (nice for documentation)

---

#### Gap M2: Energy Function in Basis Functions
**Location**: `src/python/symbolic/basis_functions.py:388`
```python
return 1.0  # TODO: Implement
```

**Impact**: Energy-based basis functions return placeholder
**Root Cause**: Function stub not completed
**Status**: Other basis functions work, this one is incomplete

**Fix Required**:
- Compute total energy E = T + V
- Return as basis function value
- Add to basis function library

**Estimated Effort**: 1 hour
**Priority**: P2 - Medium (one of many basis functions)

---

#### Gap M3: ML Trajectory Integration Helpers
**Location**: `src/python/ml/trajectory_integration.py` (multiple TODOs)

**Impact**: Some helper functions incomplete
**Root Cause**: Non-critical utilities not fully implemented
**Status**: Main integration pipeline works

**Fix Required**:
- Complete helper functions as needed
- Add convenience wrappers
- Improve error handling

**Estimated Effort**: 4 hours
**Priority**: P2 - Medium

---

#### Gap M4: Data Augmentation Extensions
**Location**: `src/python/ml/data_augmentation.py` (TODOs)

**Impact**: Some augmentation strategies not implemented
**Root Cause**: Advanced augmentation features deferred
**Status**: Basic augmentation (permutation, time reversal) works

**Fix Required**:
- Add energy scaling augmentation
- Add phase space rotation
- Add noise injection (if needed)

**Estimated Effort**: 3 hours
**Priority**: P2 - Medium

---

### LOW Priority Gaps (Optional)

#### Gap L1-L3: Various Minor TODOs

**Locations**: Various files (connection_form.py, lifted_jm_metric.py, etc.)

**Impact**: Minor missing features, edge case handling
**Root Cause**: Non-critical features deferred
**Status**: Core functionality complete

**Fix Required**: Address as needed during testing

**Estimated Effort**: 1-2 hours each
**Priority**: P3 - Low

---

## Prioritized Fix Plan

### Phase 1: Critical Path Fixes (P0-P1) - **1-2 days**

**Goal**: Make the full WP3 pipeline executable end-to-end

1. **Fix C1**: Connect Killing PDE solver (2 hours)
   - Link `killing_equations.py` to `killing_solver.py`
   - Test on simple case (sphere)

2. **Fix C3**: Complete Killing tensor assembly (8 hours)
   - Implement tensor system assembly
   - Test on harmonic oscillator (expect quadratic integrals)

3. **Fix H1**: Permutation symmetry projection (6 hours)
   - Implement symmetry group projection
   - Test on equal-mass three-body

4. **Fix H2**: Geometric invariant transforms (5 hours)
   - Implement coordinate conversions
   - Validate on Kepler problem

5. **Fix H3**: Numerical equivalence verification (3 hours)
   - Implement verification in simplification
   - Test on known integrals

**Total Phase 1**: ~24 hours (3 days with testing)

---

### Phase 2: High-Value Features (P1-P2) - **1-2 days**

**Goal**: Add important features for robustness and usability

1. **Fix C2**: Coefficient extraction (4 hours)
   - Implement symbolic coefficient extraction
   - Test on known PDEs

2. **Fix M2**: Energy basis function (1 hour)
   - Complete energy function
   - Add to regression tests

3. **Fix M1**: LaTeX formatting (2 hours)
   - Add LaTeX export
   - Generate example outputs

4. **Fix M3**: ML helpers (4 hours)
   - Complete trajectory integration helpers
   - Improve error handling

**Total Phase 2**: ~11 hours (1-2 days)

---

### Phase 3: Optimizations and Polish (P2-P3) - **2-3 days**

**Goal**: Add advanced features and optimizations

1. **Fix C4**: Adaptive mesh refinement (12 hours)
   - Implement error estimator
   - Add refinement loop
   - Test convergence

2. **Fix C5**: Helmholtz decomposition (10 hours)
   - Implement decomposition
   - Test on vector fields

3. **Fix M4**: Data augmentation (3 hours)
   - Add advanced augmentation
   - Benchmark improvements

4. **Fix L1-L3**: Minor TODOs (3-5 hours)
   - Clean up remaining TODOs
   - Address edge cases

**Total Phase 3**: ~28-30 hours (3-4 days)

---

## Testing Strategy

### Unit Tests

**For each fix**:
- Write test case first (TDD)
- Implement fix
- Verify test passes
- Add edge case tests

### Integration Tests

**End-to-end validation**:
1. **Kepler Problem**:
   - Expect: E, L (3 components), Runge-Lenz (3 components)
   - Test both vector and tensor searches

2. **Harmonic Oscillator**:
   - Expect: n independent integrals
   - Validate conservation to machine precision

3. **Restricted Three-Body**:
   - Expect: Jacobi integral only
   - Negative result validation

4. **Equal-Mass Planar Three-Body**:
   - Use permutation symmetry
   - Search for hidden integrals

### Regression Tests

**After each phase**:
- Run full test suite
- Check no existing tests break
- Verify performance doesn't degrade

---

## Success Criteria

### Phase 1 Success
- [ ] Full WP3.1 pipeline runs without NotImplementedError
- [ ] Can discover Killing vectors on S¹ bundle
- [ ] Can discover Killing tensors (quadratic integrals)
- [ ] Symmetry projection works for equal masses
- [ ] Coordinate transforms validated

### Phase 2 Success
- [ ] Symbolic PDE analysis functional
- [ ] LaTeX export works
- [ ] All basis functions complete
- [ ] ML pipeline robust and tested

### Phase 3 Success
- [ ] Adaptive refinement improves accuracy
- [ ] Helmholtz decomposition available
- [ ] All augmentation strategies work
- [ ] Zero TODO/NotImplementedError in WP3 core

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tensor assembly complex | Medium | High | Start with small test cases, validate math |
| Adaptive refinement bugs | Medium | Medium | Extensive testing on known cases |
| Performance regression | Low | Medium | Benchmark before/after each phase |
| Integration breaks | Low | High | Comprehensive regression testing |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Phase 1 longer than expected | Medium | High | Focus on P0 items only, defer others |
| Testing takes longer | High | Medium | Parallelize where possible |
| Edge cases found | High | Low | Address in Phase 3 or defer |

---

## Resource Requirements

### Computational
- Standard development machine (16 GB RAM, 8 cores)
- No GPU required for this phase
- ~10 GB disk space for test data

### Software Dependencies
- Python 3.10+
- NumPy, SciPy (already installed)
- SymPy (already installed)
- pytest for testing

### Human Resources
- 1 developer
- Estimated: 6-9 days total
  - Phase 1: 3 days
  - Phase 2: 1-2 days
  - Phase 3: 3-4 days (optional)

---

## Implementation Timeline

### Week 1: Critical Path (Phase 1)
**Mon-Wed**: Gaps C1, C3, H1
**Thu-Fri**: Gaps H2, H3, testing

### Week 2: Features and Optimization (Phases 2-3)
**Mon-Tue**: Gaps C2, M1, M2, M3
**Wed-Fri**: Gaps C4, C5, M4, final testing

---

## Validation Plan

### Known Cases Validation

1. **Flat Space (ℝⁿ)**:
   - Expected: n(n+1)/2 Killing vectors
   - Validates: Christoffel = 0, null space dimension

2. **Sphere (S²)**:
   - Expected: 3 rotations (SO(3))
   - Validates: Curved space computation

3. **Harmonic Oscillator**:
   - Expected: n independent integrals
   - Validates: Conservation to machine precision

4. **Kepler Problem**:
   - Expected: 7 integrals (6 independent)
   - Validates: Full pipeline including tensors

### Three-Body Problem Tests

1. **Equal Mass Planar**:
   - Test permutation symmetry
   - Search for hidden integrals
   - Expected: Negative or partial result

2. **Restricted Three-Body**:
   - Expected: Jacobi integral only
   - Validates: Negative result handling

---

## Deliverables

### Code
- [ ] All CRITICAL gaps fixed (C1-C5)
- [ ] All HIGH gaps fixed (H1-H3)
- [ ] Test suite with >90% coverage
- [ ] Integration tests passing

### Documentation
- [ ] Updated implementation status
- [ ] Gap fix summary
- [ ] Test results report
- [ ] Performance benchmarks

### Validation
- [ ] Known cases validated
- [ ] Three-body test results
- [ ] Comparison with design specs

---

## Conclusion

The WP3 implementation is **structurally complete** but has **functional gaps** that prevent full execution. The gaps are well-understood and fixable:

- **Critical Path** (Phase 1): ~3 days to achieve full pipeline execution
- **Full Feature Set** (Phases 1-2): ~4-5 days for production-ready code
- **Optimized Version** (All Phases): ~6-9 days for fully polished implementation

**Recommended Action**: Execute **Phase 1** immediately to achieve end-to-end functionality, then proceed with Phase 2 based on testing results.

**Next Steps**:
1. Review and approve this plan
2. Begin Phase 1 implementation
3. Track progress with daily updates
4. Iterate based on testing feedback

---

**Document Version**: 1.0
**Created**: November 22, 2025
**Status**: Ready for Review and Implementation
**Estimated Total Effort**: 60-75 hours (6-9 days)
**Critical Path**: Phase 1 (24 hours, 3 days)
