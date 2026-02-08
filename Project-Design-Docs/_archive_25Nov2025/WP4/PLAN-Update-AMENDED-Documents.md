# Plan to Update AMENDED Documents
## Based on Implementation Assessment 2025-11-20

**Date**: 2025-11-20
**Purpose**: Update AMENDED documents to reflect actual implementation status and provide roadmap
**Related**: WP4-Implementation-Assessment-2025-11-20.md

---

## Overview

The implementation assessment revealed that WP4 is **~15% implemented**, with **WP 4.2 (Complete Morales-Ramis Test) entirely absent**. The AMENDED documents currently describe the **ideal state** (what SHOULD be implemented) but don't reflect:

1. **Current status** (what IS implemented)
2. **Implementation roadmap** (how to get from current → ideal)
3. **Blocking dependencies** (what prevents implementation)
4. **Phased approach** (realistic timeline)

This plan outlines specific updates to make the AMENDED documents **actionable**.

---

## Documents to Update

### 1. AMENDED_WP4.2-Morales-Ramis-Implementation-Plan.md

**Current State**: Describes ideal implementation (3,000 lines, 6 tasks, 10-14 days)

**Issue**: Gives impression implementation exists or is straightforward

**Required Updates**:

#### Section to Add: **Implementation Status** (After Table of Contents)

```markdown
## Implementation Status

**As of 2025-11-20**: **0% IMPLEMENTED**

**Current State**:
- ❌ `/src/python/validation/` directory does not exist
- ❌ No variational equation computation (downstairs or upstairs)
- ❌ No Kovacic algorithm
- ❌ No Galois group computation
- ❌ Phase I (downstairs) not started
- ❌ Phase II (upstairs) not started

**This document describes the TARGET implementation.**

**Estimated Effort to Reach Target**: 4-6 weeks (see roadmap below)

**Critical Dependency**: WP2 lifts must be available symbolically (currently numerical only)
```

#### Section to Add: **Phased Implementation Roadmap** (Before Tasks)

```markdown
## Phased Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal**: Set up infrastructure and dependencies

- [ ] Create `/src/python/validation/` module structure
- [ ] Gather periodic orbit initial conditions (Lagrange L4, Figure-8, Euler)
- [ ] Implement periodic orbit library (`periodic_orbits.py`)
- [ ] Test orbit integration for stability
- [ ] **Deliverable**: Catalog of ≥3 periodic solutions

**Effort**: 3-5 days
**Blocking**: None

### Phase 2: Downstairs VE (Week 2)
**Goal**: Implement Task 4.2.1-4.2.3 (Phase I)

- [ ] Implement `VariationalEquationComputer` class
- [ ] Compute downstairs NVE for test orbits
- [ ] Reduce to normal directions (symplectic projection)
- [ ] **Deliverable**: Downstairs VE ready for Kovacic

**Effort**: 5-7 days
**Blocking**: Phase 1

### Phase 3: Kovacic Algorithm (Week 3)
**Goal**: Differential Galois group computation

- [ ] Implement Kovacic solver (or SymPy integration)
- [ ] Test on known integrable systems (Kepler → abelian)
- [ ] Test on known non-integrable (3BP → non-abelian)
- [ ] Apply to downstairs NVEs from Phase 2
- [ ] **Deliverable**: Downstairs Galois groups computed

**Effort**: 5-7 days
**Blocking**: Phase 2

### Phase 4: Symbolic Lifts (Week 4) ⭐ PARALLEL with Phases 2-3
**Goal**: Resolve blocking dependency for Phase II

- [ ] Create `symbolic_lifts.py` module
- [ ] Derive S¹ extended Hamiltonian symbolically (SymPy)
- [ ] Derive KS-Spinor Hamiltonian symbolically
- [ ] Compute symbolic Hessians ∇²H̃
- [ ] Validate against numerical implementations
- [ ] **Deliverable**: Symbolic lift Hamiltonians

**Effort**: 5-7 days
**Blocking**: None (can run parallel)
**Critical**: Required for Phase 5

### Phase 5: Upstairs VE (Week 5)
**Goal**: Implement Task 4.2.4-4.2.5 (Phase II upstairs)

- [ ] Implement orbit lifting to extended space
- [ ] Compute upstairs NVE (S¹ bundle)
- [ ] Compute upstairs NVE (KS-Spinor)
- [ ] Apply Kovacic to upstairs NVEs
- [ ] **Deliverable**: Upstairs Galois groups computed

**Effort**: 5-7 days
**Blocking**: Phase 3 + Phase 4

### Phase 6: Compatibility Test (Week 6)
**Goal**: Implement Task 4.2.6 (Validation)

- [ ] Implement `CompatibilityTestValidator` class
- [ ] Two-phase test orchestration
- [ ] WP3 integral validation logic
- [ ] Verdict generation and reporting
- [ ] **Deliverable**: Complete Morales-Ramis compatibility test

**Effort**: 3-4 days
**Blocking**: Phase 5

### Timeline Summary
- **Total Duration**: 6 weeks (with parallel execution of Phase 4)
- **Critical Path**: Phase 1 → 2 → 3 → 5 → 6 (5 weeks)
- **Parallel Track**: Phase 4 (symbolic lifts) during weeks 2-4
```

#### Section to Update: **Critical Dependencies** (Add before Tasks)

```markdown
## Critical Dependencies

### Dependency 1: Symbolic WP2 Lifts ⭐ BLOCKING

**Issue**: Current WP2 implementations are numerical (NumPy), not symbolic (SymPy)

**Files Affected**:
- `src/python/lifts/s1_bundle.py` - Numerical BundleState
- `src/python/lifts/lifted_hamiltonian.py` - Numerical evaluation
- `src/python/geometry/connection_form.py` - Numerical connection

**Impact**:
- Cannot derive symbolic upstairs NVE
- Cannot apply Kovacic algorithm to upstairs (requires rational functions)
- **BLOCKS Phase II** (Tasks 4.2.4-4.2.6)

**Resolution** (see Phase 4 roadmap):
- Option C (Hybrid): Keep numerical WP2, create separate symbolic derivations
- Implement `symbolic_lifts.py` module
- Derive H̃ and ∇²H̃ using SymPy
- **Effort**: 5-7 days
- **Can run in parallel with Phases 2-3**

### Dependency 2: Periodic Orbit Library

**Issue**: No catalog of periodic solutions with initial conditions

**Required Orbits**:
1. Lagrange L4/L5 equilateral (literature available)
2. Euler collinear (literature available)
3. Figure-8 choreography (Moore 1993, Chenciner-Montgomery 2000)
4. (Optional) Additional choreographies

**Resolution**:
- Literature review for initial conditions
- Implement `periodic_orbits.py` module
- **Effort**: 1-2 days
- **Priority**: Phase 1

### Dependency 3: Kovacic Algorithm

**Issue**: No implementation of Kovacic algorithm for Galois group computation

**Options**:
1. Use SymPy's `dsolve` with Kovacic hints (easiest, may be incomplete)
2. Implement Kovacic from scratch (rigorous, ~600 lines)
3. Interface with Maple's Kovacic (pragmatic)

**Resolution**:
- Start with SymPy (Phase 3)
- Fall back to manual implementation if needed
- Test on known cases (Kepler, Pendulum)
- **Effort**: 5-7 days
- **Priority**: Phase 3
```

---

### 2. AMENDED_WP4-Complete-Overview.md

**Current State**: Describes complete WP4 architecture

**Issue**: No indication of what's implemented vs. planned

**Required Updates**:

#### Section to Add: **Implementation Status Dashboard** (After Executive Summary)

```markdown
## Implementation Status Dashboard

**Assessment Date**: 2025-11-20

| Component | Status | % Complete | Priority | Blocking Issues |
|-----------|--------|------------|----------|-----------------|
| **WP 4.1** Analytical Vetting | 🟡 Partial | 30% | P2 | Needs symbolic CAS |
| **WP 4.2 Phase I** Downstairs MR | 🔴 Not Started | 0% | P0 | None - can start |
| **WP 4.2 Phase II** Upstairs MR | 🔴 Not Started | 0% | P0 | Symbolic lifts |
| **WP 4.3** Numerical Robustness | 🟡 Partial | 15% | P1 | WP3 candidates |
| **Overall WP4** | 🔴 Critical Gaps | **~15%** | - | See assessment |

### What Exists

**WP 4.1 Components** (30% implemented):
- ✅ Functional independence test (`analysis/independence_test.py`)
- ✅ Involution testing (Poisson brackets)
- ✅ Conservation verification (`analysis/conservation_verification.py`)
- ❌ Symbolic CAS-based verification (missing)

**WP 4.3 Components** (15% implemented):
- ✅ Single trajectory conservation verification
- ❌ Monte Carlo framework (missing)
- ❌ Stress testing (missing)
- ❌ Long-time analysis (missing)

**WP 4.2 Components** (0% implemented):
- ❌ **ENTIRE WP 4.2 ABSENT**
- ❌ No variational equations
- ❌ No Kovacic algorithm
- ❌ No Galois group computation
- ❌ No compatibility test

### Critical Path to Completion

**Immediate** (Weeks 1-3): Implement WP 4.2 Phase I
- Variational equations downstairs
- Kovacic algorithm
- Downstairs Galois groups

**Next** (Weeks 4-6): Implement WP 4.2 Phase II ⭐
- Symbolic lifts (parallel track)
- Upstairs variational equations
- Upstairs Galois groups
- **Compatibility test**

**Then** (Weeks 7-8): Complete WP 4.3
- Monte Carlo sweep
- Statistical validation

**Timeline to WP5**: 8-10 weeks from current state
```

#### Section to Update: **WP4 Architecture** (Add status indicators)

```markdown
## WP4 Architecture (AMENDED)

### Three-Stage Pipeline with Implementation Status

```
WP4: Rigorous Validation (3 parallel tracks → synthesis)
│
├── WP 4.1: Analytical Vetting (8-10 days) 🟡 30% IMPLEMENTED
│   ├── 4.1.1: Poisson Bracket Computation ✅ PARTIAL (numerical only)
│   ├── 4.1.2: Involution Testing ✅ IMPLEMENTED
│   └── 4.1.3: Functional Independence ✅ IMPLEMENTED
│
├── WP 4.2: Complete Morales-Ramis Test (10-14 days) 🔴 0% IMPLEMENTED
│   │
│   ├── PHASE I: Downstairs (Defensive Falsification) ❌ NOT STARTED
│   │   ├── 4.2.1: Downstairs Variational Equations Setup
│   │   ├── 4.2.2: Downstairs Differential Galois Group
│   │   └── 4.2.3: Confirmation of Downstairs Non-Integrability
│   │
│   └── PHASE II: Upstairs (Compatibility Test) ❌ NOT STARTED ⭐ CRITICAL
│       ├── 4.2.4: Upstairs Variational Equations Setup
│       ├── 4.2.5: Upstairs Differential Galois Group
│       └── 4.2.6: Compatibility Test Validation
│
└── WP 4.3: Numerical Robustness (10-12 days) 🟡 15% IMPLEMENTED
    ├── 4.3.1: Monte Carlo Parameter Sweep ❌ NOT STARTED
    ├── 4.3.2: Stress Testing ❌ NOT STARTED
    ├── 4.3.3: Long-Time Invariance ✅ BASIC VERSION
    └── 4.3.4: Chaos Correlation Analysis ❌ NOT STARTED
```

**Legend**:
- ✅ Implemented
- 🟡 Partial
- ❌ Not Started
- 🔴 Critical gap
```

---

### 3. AMENDED_Updated-Plan-WP2-5-Nov2025.md

**Current State**: Top-level project plan with corrected WP 4.2

**Issue**: Doesn't mention implementation status or WP2 symbolic requirements

**Required Updates**:

#### Section to Add: **Implementation Status Note** (After Amendment Summary)

```markdown
## Implementation Status (as of 2025-11-20)

**WP1**: ✅ COMPLETE

**WP2**: ✅ IMPLEMENTED (numerical only)
- ⚠️ **Note**: Lifts are numerical (NumPy), not symbolic (SymPy)
- ⚠️ **Impact**: Blocks WP 4.2 Phase II upstairs analysis
- 📋 **Action Required**: Add symbolic derivations (see WP2-Symbolic-Requirements)

**WP3**: 🟡 IMPLEMENTATION ONGOING
- Killing field search: Implementation in progress
- ML discovery: HNN architecture implemented
- Symbolic regression: Pipeline implemented

**WP4**: 🔴 CRITICAL GAPS (Overall: ~15% implemented)
- WP 4.1: 30% implemented (basic tools exist)
- **WP 4.2: 0% implemented** ← **CRITICAL: Completely absent**
- WP 4.3: 15% implemented (basic verification only)
- 📋 **See**: WP4-Implementation-Assessment-2025-11-20.md

**WP5**: ⏸️ BLOCKED (waiting for WP4 completion)
```

#### Section to Add: **WP2 Symbolic Requirements** (After WP 2.3)

```markdown
### **WP 2 Symbolic Requirements for WP 4.2**

**Issue Identified**: Current WP2 lift implementations are numerical only, which **blocks WP 4.2 Phase II**.

**What's Needed**:

For WP 4.2 Phase II (Upstairs Morales-Ramis Test), we require **symbolic** derivations of:

1. **S¹ Bundle Extended Hamiltonian** (WP 2.2):
   ```
   H̃(s, θ, p_s, p_θ) in SymPy
   ∇²H̃ (Hessian) in SymPy
   ```

2. **Extended Symplectic Form** (WP 2.2):
   ```
   ω̃ = ω_can + dθ ∧ (dp_θ - A)
   Symbolic representation
   ```

3. **Connection One-Form** (WP 2.1.2):
   ```
   A = A_i dq^i
   Symbolic coefficients A_i(q)
   ```

4. **KS-Spinor Hamiltonian** (WP 2.3):
   ```
   H̃_KS in SymPy (with constraints)
   ∇²H̃_KS (Hessian)
   ```

**Implementation Approach** (Recommended):

**Option C: Hybrid Numerical + Symbolic**

- ✅ Keep existing numerical WP2 for trajectory integration (WP1, WP3)
- ➕ Add parallel symbolic derivations in new module:
  - `src/python/symbolic_lifts/s1_symbolic.py`
  - `src/python/symbolic_lifts/ks_symbolic.py`
  - Use SymPy for all algebraic operations
  - Validate against numerical implementations

**Effort**: 1 week (5-7 days)

**Can Run Parallel**: Yes - while implementing WP 4.2 Phase I

**Deliverable**: Symbolic Hamiltonians ready for upstairs VE computation
```

#### Update WP 4.2 Description: Add Implementation Note

```markdown
#### **WP 4.2: Complete Morales-Ramis Test (AMENDED)**

**⚠️ IMPLEMENTATION STATUS: 0% - NOT STARTED** (as of 2025-11-20)

**Objective:** Validate lift-integrability hypothesis by proving **BOTH**:
1. The system is non-integrable downstairs (defensive falsification)
2. The lifted system has abelian Galois structure upstairs (compatibility test) **← AMENDED**

**📋 Implementation Roadmap**: See WP4.2-Implementation-Plan.md for phased approach

**⏰ Estimated Effort**: 4-6 weeks (from current state)

**🚧 Blocking Dependencies**:
- Periodic orbit library (1-2 days to resolve)
- Symbolic WP2 lifts (5-7 days to resolve, can run parallel)
- Kovacic algorithm (5-7 days to implement)
```

---

### 4. NEW Document: WP2-Symbolic-Requirements.md

**Purpose**: Detailed specification for symbolic lift implementations

**Location**: `Project-Design-Docs/WP2/WP2-Symbolic-Requirements.md`

**Content Outline**:

```markdown
# WP2 Symbolic Requirements for WP4.2 Compatibility

## Purpose

WP 4.2 Phase II requires symbolic computation of upstairs variational equations.
This document specifies the symbolic WP2 deliverables needed.

## Background

Current WP2 implementations use NumPy (numerical). For Galois group computation
via Kovacic algorithm, we need SymPy (symbolic) representations.

## Requirements

### R1: Symbolic S¹ Extended Hamiltonian

**Module**: `src/python/symbolic_lifts/s1_symbolic.py`

**Deliverable**:
```python
import sympy as sp

def derive_s1_hamiltonian_symbolic(
    masses: tuple,  # (m1, m2, m3)
    use_shape_coords: bool = True
) -> sp.Expr:
    """
    Derive H̃(s, θ, p_s, p_θ) symbolically.

    Returns:
        SymPy expression for extended Hamiltonian
    """
    pass

def compute_s1_hessian_symbolic(
    H_tilde: sp.Expr,
    coords: List[sp.Symbol],
    momenta: List[sp.Symbol]
) -> sp.Matrix:
    """
    Compute ∇²H̃ (Hessian matrix).

    Returns:
        8×8 SymPy matrix (for planar 3BP in bundle)
    """
    pass
```

### R2: Symbolic Connection Form

[... etc ...]

## Testing

Each symbolic derivation must be validated against numerical implementation:

```python
def test_symbolic_vs_numerical_hamiltonian():
    """Verify symbolic matches numerical at random points."""
    pass
```

## Timeline

**Phase 1** (2-3 days): S¹ symbolic derivation
**Phase 2** (2-3 days): KS symbolic derivation
**Phase 3** (1-2 days): Validation and testing

**Total**: 5-7 days
```

---

### 5. NEW Document: WP4-Implementation-Roadmap.md

**Purpose**: High-level roadmap from current state → complete WP4

**Location**: `Project-Design-Docs/WP4/WP4-Implementation-Roadmap.md`

**Content Outline**:

```markdown
# WP4 Implementation Roadmap
## From Current State (15%) to Complete (100%)

**Current Status**: 2025-11-20
**Target Completion**: 8-10 weeks from now

## Roadmap Overview

```
Timeline (Weeks)
│
Week 1 │ ████████ Phase 1: Foundation (WP 4.2 infra + periodic orbits)
       │
Week 2 │ ████████ Phase 2: Downstairs VE (Task 4.2.1)
       │ ░░░░░░░░ Phase 4: Symbolic Lifts (PARALLEL) ⭐
       │
Week 3 │ ████████ Phase 3: Kovacic Algorithm (Task 4.2.2-4.2.3)
       │ ░░░░░░░░ Phase 4: Symbolic Lifts (continued)
       │
Week 4 │ ████████ Phase 4: Symbolic Lifts (completion)
       │ ░░░░░░░░ Phase 5: Upstairs VE (start)
       │
Week 5 │ ████████ Phase 5: Upstairs VE + Galois (Task 4.2.4-4.2.5)
       │
Week 6 │ ████████ Phase 6: Compatibility Test (Task 4.2.6) ⭐ CRITICAL
       │
Week 7 │ ████████ WP 4.3: Monte Carlo + Stress Testing
       │
Week 8 │ ████████ WP 4.3: Analysis + WP 4.1 Symbolic Integration
       │
Week 9 │ ████████ Integration Testing + Documentation
       │
Week 10│ Ready for WP5 (Publication Preparation)
```

## Critical Milestones

**M1** (End Week 1): Periodic orbit library + infrastructure
**M2** (End Week 3): Downstairs Galois groups computed ✓
**M3** (End Week 4): Symbolic lifts validated
**M4** (End Week 6): **UPSTAIRS GALOIS GROUPS COMPUTED** ⭐ KEY MILESTONE
**M5** (End Week 6): **COMPATIBILITY TEST OPERATIONAL** ⭐⭐ CRITICAL
**M6** (End Week 8): Statistical validation complete
**M7** (End Week 9): WP4 integration tests pass

## Dependencies

[... dependency graph ...]

## Resource Allocation

**Developer Focus**:
- Weeks 1-3: WP 4.2 Phase I (critical path)
- Weeks 2-4: Symbolic lifts (parallel track, can be different developer)
- Weeks 4-6: WP 4.2 Phase II (critical path)
- Weeks 7-8: WP 4.3 (can partially overlap with Phase II testing)

**Estimated FTE**: 1.0 FTE for critical path, 0.5 FTE for parallel track
```

---

## Summary of Updates

### Documents to Update

| Document | Updates Required | Effort | Priority |
|----------|------------------|--------|----------|
| AMENDED_WP4.2-Morales-Ramis-Implementation-Plan.md | Add status, roadmap, dependencies | 2-3 hours | P0 |
| AMENDED_WP4-Complete-Overview.md | Add status dashboard, update architecture | 1-2 hours | P0 |
| AMENDED_Updated-Plan-WP2-5-Nov2025.md | Add status note, symbolic requirements | 1-2 hours | P1 |

### New Documents to Create

| Document | Purpose | Effort | Priority |
|----------|---------|--------|----------|
| WP2-Symbolic-Requirements.md | Spec for symbolic lifts | 2-3 hours | P0 |
| WP4-Implementation-Roadmap.md | High-level schedule | 1-2 hours | P1 |
| WP4-Implementation-Assessment-2025-11-20.md | ✅ DONE | - | - |

**Total Effort**: 8-12 hours of documentation work

---

## Implementation Sequence

### Phase 1: Update Existing AMENDED Documents (2-3 hours)

1. Update AMENDED_WP4.2-Morales-Ramis-Implementation-Plan.md
   - Add "Implementation Status" section
   - Add "Phased Implementation Roadmap"
   - Add "Critical Dependencies"

2. Update AMENDED_WP4-Complete-Overview.md
   - Add "Implementation Status Dashboard"
   - Update architecture diagram with status

3. Update AMENDED_Updated-Plan-WP2-5-Nov2025.md
   - Add "Implementation Status Note"
   - Add "WP2 Symbolic Requirements" section
   - Update WP 4.2 description with status

### Phase 2: Create New Supporting Documents (2-3 hours)

4. Create WP2-Symbolic-Requirements.md
   - Detailed specifications
   - API design
   - Testing requirements

5. Create WP4-Implementation-Roadmap.md
   - Week-by-week schedule
   - Milestone definitions
   - Resource allocation

---

## Expected Outcomes

After these updates, the AMENDED documents will:

1. **Reflect Reality**: Clearly show what's implemented vs. planned
2. **Provide Roadmap**: Week-by-week path from current → complete
3. **Identify Blockers**: Explicit dependencies and resolution plans
4. **Enable Action**: Developers can immediately begin Phase 1
5. **Set Expectations**: Realistic timeline to WP5 (8-10 weeks)

**Key Message**: AMENDED documents remain **aspirational** (describe target state) but now also include **practical** roadmap to achieve that state.

---

**Document Version**: 1.0
**Created**: 2025-11-20
**Purpose**: Guide updates to AMENDED documents based on implementation assessment
**Next Action**: Begin Phase 1 updates to AMENDED_WP4.2 document
