# Project Overview: Lift-Integrability in the Three-Body Problem

**A Systematic Search for Hidden Integrability in the Newtonian Three-Body Problem via Higher-Dimensional Symplectic Embedding**

**Document Version**: 2.0 (Consolidated)
**Last Updated**: 2025-11-25
**Status**: Active Research Program

---

## Executive Summary

This project investigates **lift-integrability** in the Newtonian three-body problem through higher-dimensional symplectic embedding. The central hypothesis: while the three-body problem is non-integrable in standard coordinates (Bruns-Poincare theorem), new conserved quantities may exist in appropriately constructed "upstairs" spaces.

### Core Hypothesis

> We hypothesize that the chaotic dynamics of the Newtonian three-body problem are an artifact of dimensional reduction. We propose that the standard 3D formulation is a projection of an integrable Hamiltonian system evolving on a higher-dimensional, regularized symplectic manifold.

### Research Objective

Find the crucial **sixth independent integral** $\widetilde{I}$ that would render the system Liouville integrable in the lifted space, while being invisible "downstairs" in standard coordinates.

---

## Theoretical Foundation

### Classical Obstructions

A credible approach must directly confront the rigorous "no-go" theorems:

1. **Bruns' Theorem (1887)**: No integrals exist beyond the classical ten that are *algebraic* functions of standard coordinates and momenta.

2. **Poincare's Theorem (1890)**: Non-existence of additional *analytic* integrals for the generic case.

3. **Ziglin and Morales-Ramis Theories (1980s-Present)**: Differential Galois theory methods prove non-existence of *meromorphic* first integrals.

### Our Strategy: Circumventing Obstructions

1. **Expanding the Function Space**: We do not restrict the search to integrals that are algebraic, analytic, or meromorphic in the *original* coordinates.

2. **Regularization and Embedding**: We embed dynamics into a higher-dimensional, regularized phase space. The classical theorems apply to the original formulation; the lifted space may admit symmetries lost in the projection.

### Liouville Integrability Requirements

A Hamiltonian system with N degrees of freedom is Liouville integrable if it possesses N functionally independent integrals of motion in involution (pairwise Poisson brackets vanish).

**Dimensional Accounting**:
- General three-body problem: N=6 DOF (12-dimensional phase space after center-of-mass reduction)
- Classical integrals (Energy E, Linear Momentum P, Angular Momentum L): 5 independent integrals in involution
- **Objective**: Find the sixth independent integral $\widetilde{I}$ in involution with the existing five

---

## Two Lift Constructions

### 1. S^1 Minimal "Untwisting" Lift (WP 2.2)

The **minimal cohomological fix** that neutralizes the magnetic twist obstructing integrability.

| Property | Description |
|----------|-------------|
| **Configuration Space** | Shape Space x S^1 |
| **Phase Space Dimension** | 8D (4D configuration) |
| **Purpose** | Geometric integrability search |
| **Collision Handling** | Not regularized |
| **Time Parameter** | Physical time |
| **Best For** | Non-collision systems |

**Extended Symplectic Form**:
$$\widetilde{\omega} = \omega_{\text{can}} + d\theta \wedge (p_\theta - A)$$

where $A$ is the mechanical connection one-form.

### 2. KS-Spinor "Pairwise" Lift (WP 2.3)

The **maximal symmetry fix** inspired by Kustaanheimo-Stiefel transformation, revealing hidden SO(4)-like symmetries.

| Property | Description |
|----------|-------------|
| **Configuration Space** | (R^4)^3 with constraints |
| **Phase Space Dimension** | 10D (5D configuration) |
| **Purpose** | Collision regularization |
| **Collision Handling** | Fully regularized |
| **Time Parameter** | Fictitious time (Sundman) |
| **Best For** | Collision-prone dynamics |

**Key Insight**: The KS transformation is a **4+1 dimensional lift** (4 spatial + 1 temporal), not merely a 3->4 spatial coordinate change.

**Time Regularization (Sundman)**:
$$\frac{dt}{ds} = \Omega(q) = |u|^2 = r$$

**Extended Phase Space Coordinates**: $(q, p, t, E, s, \mathcal{K})$

**Energy Relation**:
$$\mathcal{K} = E \cdot \Omega(q)$$

---

## Work Package Structure

### WP1: High-Precision Trajectory Generation
**Status**: Complete

Generate and validate high-fidelity CR3BP trajectory catalogue:
- Tier 1: 10^5 orbits, double precision (|Delta C/C| < 10^-14)
- Tier 2: 10^4 orbits, double-double precision (|Delta C/C| < 10^-25)

### WP2: Geometric Foundations and Lift Construction
**Status**: Implementation Phase

Establish mathematical framework and implement both lift constructions:
- WP 2.1: Geometric reduction, connection, curvature computation
- WP 2.2: S^1 bundle lift implementation
- WP 2.3: KS-Spinor lift with time regularization

### WP3: Discovery of Candidate Invariants
**Status**: Design Phase

Three-track approach to invariant discovery:
- WP 3.1: Deterministic geometric search (Killing fields/tensors)
- WP 3.2: Structure-preserving ML (Hamiltonian Neural Networks)
- WP 3.3: Symbolic regression consolidation

### WP4: Rigorous Validation ("The Gauntlet")
**Status**: Design Phase

Three-stage validation pipeline:
- WP 4.1: Analytical vetting (Poisson brackets, independence, involution)
- WP 4.2: Complete Morales-Ramis test (downstairs non-abelian + upstairs abelian)
- WP 4.3: Numerical robustness (Monte Carlo, stress testing)

### WP5: Consolidation and Publication
**Status**: Planning Phase

Final consolidation:
- WP 5.1: Formal proof construction
- WP 5.2: Reproducibility package
- WP 5.3: Publication preparation

---

## Validation Criteria

### A. Hamiltonian Consistency
- Extended Hamiltonian $\widetilde{H}$ must exactly reduce to standard $H$ under projection
- Symplectic structure must remain exact and non-degenerate

### B. Analytical Verification
- **Conservation**: $\{\widetilde{I}, \widetilde{H}\}_{\widetilde{\omega}} \equiv 0$
- **Involution**: $\{\widetilde{I}, L_i\} = 0$ for all classical integrals
- **Independence**: Jacobian rank must increase by 1 on >99% of sampled states

### C. Numerical Validation
- High-order symplectic integration in quadruple precision
- Error monitoring near machine precision (<10^-20)
- Shadow Hamiltonian analysis
- Monte Carlo suite: >= 10^5 initial conditions

### D. Morales-Ramis Test (Complete)
- **Phase I (Downstairs)**: Verify non-abelian Galois group (proves classical non-integrability)
- **Phase II (Upstairs)**: Verify abelian Galois group (validates lift-integrability)

---

## Key Theoretical Results

### Mechanical Connection and Curvature

The **mechanical connection** $A$ describes how rotations couple to translations:
$$\omega_{\text{red}} = \omega_{\text{shape}} - d(L \cdot A)$$

The **curvature** $F = dA \neq 0$ is the geometric obstruction to integrability downstairs.

### Connection-Curvature Decomposition

For time-regularized systems:
$$\mathcal{F}_{\text{ext}} = \mathcal{F}_{\text{spatial}} + \mathcal{F}_{\text{temporal}}$$

### Compatibility Test Matrix

| Upstairs Galois | WP3 Found Integrals | Interpretation |
|-----------------|---------------------|----------------|
| Abelian | Yes | **LIFT-INTEGRABILITY CONFIRMED** |
| Non-abelian | Yes | WP3 integrals spurious |
| Abelian | No | Integrals exist but missed |
| Non-abelian | No | Negative result confirmed |

---

## References

### Core Mathematical Framework
1. Marsden & Weinstein (1974): "Reduction of symplectic manifolds with symmetry"
2. Montgomery (1988): "The connection whose holonomy is the classical adiabatic angles"
3. Littlejohn & Reinsch (1997): "Gauge fields in the separation of rotations and internal motions"
4. Cushman & Bates (1997): *Global Aspects of Classical Integrable Systems*

### KS Regularization
5. Stiefel & Scheifele (1971): *Linear and Regular Celestial Mechanics*
6. Moser (1970): "Regularization of Kepler's problem and the averaging method"

### Differential Galois Theory
7. Morales-Ruiz (1999): *Differential Galois Theory and Non-Integrability*
8. Ziglin (1983): "Branching of solutions and non-existence of first integrals"

---

## Document Index

### In This Folder (OVERVIEW/)

| Document | Description |
|----------|-------------|
| `Project-Overview.md` | This document - consolidated project overview |
| `Compute-Requirements-Analysis.md` | Computational resource requirements for WP1-4 |
| `KS-Conjectural-Statement.md` | Theoretical framework for KS symplectic reduction |

### Related Documents

| Location | Document | Description |
|----------|----------|-------------|
| `WP1/` | `WP1-Overview.md` | High-precision trajectory generation |
| `WP2/` | `WP2-Overview.md` | Geometric foundations and lifts |
| `WP3/` | `WP3-Overview.md` | Invariant discovery methods |
| `WP4/` | `WP4-Overview.md` | Validation gauntlet |
| `WP5/` | `WP5-Overview.md` | Publication preparation |

---

**Document History**:
- v2.0 (2025-11-25): Consolidated from multiple overview documents
- v1.0 (2025-11-16): Original project plan
