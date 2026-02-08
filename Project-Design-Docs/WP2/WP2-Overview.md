# Work Package 2: Geometric Foundations and Lift Construction

**Mathematical Framework for Higher-Dimensional Symplectic Embedding**

**Status**: Implementation Phase
**Last Updated**: 2025-11-25
**Prerequisites**: WP1 Complete
**Next Phase**: WP3 (Invariant Discovery)

---

## Executive Summary

WP2 establishes the mathematical framework and implements two primary higher-dimensional embeddings (lifts): the **minimal cohomological fix** (S^1 untwisting) and the **maximal symmetry fix** (KS-Spinor lift). These lifts provide the "upstairs" phase spaces where hidden integrals may exist.

---

## Core Insight: Time Regularization is Fundamental

**Key Discovery**: The KS transformation is truly a **4+1 dimensional lift** (4 spatial + 1 temporal), not merely a 3->4 spatial coordinate change.

- **Before**: Time reparametrization treated as auxiliary technique
- **After**: Time regularization recognized as **geometrically fundamental** to KS lift

The Sundman transformation $dt/ds = \Omega(q)$ is essential for:
1. Collision regularization
2. Symplectic structure preservation
3. Revealing hidden temporal integrals

---

## Three Sub-Work-Packages

### WP 2.1: Geometric Reduction and Shape Space Analysis

**Objective**: Implement reduction pipeline and compute geometric structures that obstruct integrability.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 2.1.1 | Coordinate systems (Cartesian -> Jacobi -> Shape) | Transformation library |
| 2.1.2 | Mechanical connection A and curvature F = dA | Connection module |
| 2.1.3 | Jacobi-Maupertuis metric analysis | Curvature visualization |

**Key Output**: Connection 1-form A and curvature 2-form F (the geometric obstruction to integrability).

### WP 2.2: S^1 "Untwisting" Lift (Minimal)

**Objective**: Construct minimal extension to neutralize the magnetic twist.

| Feature | Description |
|---------|-------------|
| Configuration Space | Shape Space x S^1 |
| Phase Space Dimension | 8D |
| Extended Symplectic Form | omega_tilde = omega_can + d_theta wedge (p_theta - A) |
| Time Parameter | Physical time (NOT regularized) |
| Collision Handling | Not regularized |

**Key Insight**: S^1 lift does NOT regularize collisions - it's purely for geometric untwisting.

### WP 2.3: KS-Spinor "Pairwise" Lift (Maximal)

**Objective**: Implement structured lift revealing hidden symmetries analogous to Kepler's SO(4).

| Feature | Description |
|---------|-------------|
| Configuration Space | (R^4)^3 with constraints |
| Phase Space Dimension | 10D |
| Extended Symplectic Form | Canonical + constraint structure |
| Time Parameter | Fictitious time s (Sundman: dt/ds = r) |
| Collision Handling | Fully regularized |

**Extended Data Structure**:
```python
ExtendedKSState:
    u, p_u      # Spinor spatial (4D)
    s, K        # Fictitious time and regularized energy
    t, E        # Physical time and physical energy
```

**Energy Relation**: K = E * Omega(q)

---

## Comparison: S^1 vs KS Lifts

| Feature | S^1 Lift | KS Regularization |
|---------|----------|-------------------|
| **Purpose** | Geometric integrability search | Collision regularization |
| **Spatial lift** | S^1 bundle (1D fiber) | KS spinor (4D) |
| **Temporal lift** | None (physical time) | Sundman (dt/ds = r) |
| **Collision handling** | Fails | Regularized |
| **Phase space dim** | 8D (4D config) | 10D (5D config) |
| **Best for** | Non-collision systems | Collision-prone dynamics |
| **Complexity** | Lower | Higher |
| **Integrability** | May reveal spatial integrals | May reveal both spatial + temporal |

**Proposed Future Work**: Combine both (S^1 + Sundman) for maximum power.

---

## Connection and Curvature

### Mechanical Connection

The connection 1-form A arises from rotational reduction:
$$\omega_{\text{red}} = \omega_{\text{shape}} - d(L \cdot A)$$

### Curvature as Obstruction

$$F = dA \neq 0 \implies \text{non-integrable downstairs}$$

For time-regularized systems:
$$\mathcal{F}_{\text{ext}} = \mathcal{F}_{\text{spatial}} + \mathcal{F}_{\text{temporal}}$$

---

## Implementation Strategy

### Phase 1 (Months 1-2): Foundation
- Extended data structures with time tracking
- Core classes: `ExtendedKSState`, `PairwiseSpinorStateWithTime`, `SundmanTransformation`
- Test: Round-trip transformations, constraint validation

### Phase 2 (Months 3-4): Time-Regularized Integration
- RATTLE integrator with dual time tracking
- Track both s (integration variable) and t (physical observable)
- Monitor dual energy: E and K
- Test: Collision passage, energy conservation

### Phase 3 (Months 5-6): Analysis
- Identify temporal integrals
- Compare S^1 vs KS integrability
- Validate theoretical predictions

---

## Documents in This Folder

### Core Documents

| File | Description |
|------|-------------|
| `WP2-Overview.md` | This document |
| `WP2-Complete-Summary-and-Handoff.md` | WP2 completion summary |
| `README.md` | Original folder readme |
| `PLAN-WP2-Gap-Fixes.md` | Gap analysis and fixes |
| `IMPLEMENTATION_SUMMARY_RATTLE.md` | RATTLE integrator summary |

### Task 2.1: Geometric Reduction

| File | Description |
|------|-------------|
| `Task-2.1.1-Implementation-Plan.md` | Coordinate systems |
| `Task-2.1.1-Part-[A-D]-Design.md` | Detailed designs |
| `Task-2.1.2-Implementation-Plan.md` | Connection computation |
| `Task-2.1.2-Part-[A-D]-Design.md` | Detailed designs |
| `Task-2.1.3-Implementation-Plan.md` | JM metric analysis |
| `Task-2.1.3-Part-[A-D]-Design.md` | Detailed designs |

### Task 2.2: S^1 Lift

| File | Description |
|------|-------------|
| `WP2.2-S1-Lift-Implementation-Plan.md` | Original plan |
| `WP2.2-Part-[A-D]-Design.md` | Detailed designs |

### Task 2.3: KS-Spinor Lift

| File | Description |
|------|-------------|
| `WP2.3-KS-Spinor-Lift-Implementation-Plan.md` | Original plan |
| `WP2.3-Time-Regularization-Focus.md` | Time regularization aspects |
| `WP2.3-Constraint-Handling-Focus.md` | Constraint handling aspects |

---

## Dependencies

**Upstream**: WP1 (trajectory data for validation)

**Downstream**:
- WP3: Uses lifted phase spaces for invariant search
- WP4: Uses lifted Hamiltonians for Morales-Ramis test

---

## Key Equations

### Sundman Transformation
$$\frac{dt}{ds} = \Omega(q) = |u|^2 = r$$

### Extended Phase Space
Coordinates: (q, p, t, E, s, K)

Symplectic form:
$$\Omega_{\text{ext}} = dp \wedge dq + dE \wedge dt + d\mathcal{K} \wedge ds$$

### KS Bilinear Relation
$$r = |u|^2$$

### Regularized Hamiltonian (KS)
$$\mathcal{H}_{\text{reg}}(u, p_u) = \frac{1}{2|u|^2}\sum_{i=0}^3 p_{u_i}^2 - \frac{k}{|u|^2}$$

---

**Document History**:
- v2.0 (2025-11-25): Consolidated from AMENDED documents
- v1.0 (2025-11-14): Original specification
