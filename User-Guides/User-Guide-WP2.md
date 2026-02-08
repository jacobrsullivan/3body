# User Guide: Work Package 2
## Geometric Reduction and Shape Space Analysis

**Status**: ✅ Core Complete (Coordinates, Reduction, Connection, JM Metric, Geometry ✅; S¹ Lift ✅; KS-Spinor ✅ with time regularization)
**Purpose**: Establish geometric foundations for investigating lift-integrability
**Role in Project**: Creates the "upstairs" spaces where hidden integrals may exist

---

## Table of Contents

1. [Overview](#overview)
2. [How WP2 Fits into the Overall Project](#how-wp2-fits-into-the-overall-project)
3. [What's Implemented](#whats-implemented)
4. [Quick Start Guide](#quick-start-guide)
5. [Core Components](#core-components)
6. [Available Tests](#available-tests)
7. [Examples and Workflows](#examples-and-workflows)
8. [Mathematical Framework](#mathematical-framework)
9. [References](#references)

---

## Overview

Work Package 2 provides the **geometric infrastructure** for searching for hidden integrals in extended phase spaces. While the three-body problem is proven non-integrable in standard coordinates (Bruns, Poincaré), this project tests the **lift-integrability hypothesis**: the system may become integrable "upstairs" in appropriately constructed higher-dimensional spaces.

### Key Questions

1. *What geometric structure prevents integrability in the reduced phase space?*
   → Answer: Non-zero connection curvature F ≠ 0 (the "magnetic twist")

2. *Can we "untwist" this obstruction by lifting to a higher-dimensional space?*
   → Answer: Test via S¹ bundle and KS-Spinor lift constructions

3. *Does negative scalar curvature correlate with chaotic motion?*
   → Answer: Investigate via Jacobi-Maupertuis metric analysis

### Scientific Context

**Symplectic Reduction** (Marsden-Weinstein): When a Hamiltonian system has symmetries (translation, rotation), we can reduce the phase space dimension by "quotienting out" these symmetries. For the three-body problem:
- Original: 18D (9 positions + 9 momenta)
- After translation reduction: 15D
- After rotation reduction: 12D (planar) or 7D (fixing angular momentum)

**The Connection Form** A: Encodes how the rotational momentum couples to shape space motion—a "magnetic" term in the reduced Hamiltonian.

**The Lift-Integrability Idea**: Construct higher-dimensional spaces (S¹ bundle, KS-Spinor) where the connection becomes "flat" or regularized, potentially revealing new conserved quantities.

**Reference**: See `Science-Research-Docs/WP1 – Foundations: Symplectic Reduction, Moment Maps, Principal Bundles, Magnetic Terms.pdf` for complete mathematical foundations.

---

## How WP2 Fits into the Overall Project

```
┌──────────────────────────────────────────────────────────┐
│ WP1: High-Precision Infrastructure                       │
│ • Provides: High-fidelity trajectories                    │
└────────────────────┬─────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP2: Geometric Foundations (THIS GUIDE)                   │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Task 2.1.1: Coordinate Systems & Reduction          │   │
│ │ • Cartesian → Jacobi → Shape Space                  │   │
│ │ • Translation & rotation reduction                   │   │
│ │ • 18D → 15D → 12D/7D phase space                    │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Task 2.1.2: Connection & Curvature                  │   │
│ │ • Compute mechanical connection A (1-form)          │   │
│ │ • Compute curvature F = dA (2-form)                 │   │
│ │ • Prove: F ≠ 0 (non-integrable downstairs)         │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Task 2.1.3: Jacobi-Maupertuis Metric                │   │
│ │ • Compute JM metric g_JM on shape space             │   │
│ │ • Compute scalar curvature R                        │   │
│ │ • Test: R < 0 ↔ chaos?                             │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ WP 2.2: S¹ Bundle Lift ("Untwisting")               │   │
│ │ • Construct P = S × S¹ (4D bundle)                  │   │
│ │ • Extended symplectic form                          │   │
│ │ • Test: Is p_θ (fiber momentum) a new integral?     │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ WP 2.3: KS-Spinor Lift (Regularization)             │   │
│ │ • Apply KS transformation to all 3 pairs            │   │
│ │ • 12D spinor space (9D constrained)                 │   │
│ │ • Regularize collisions (r → 0)                     │   │
│ │ • Test: Integrals in spinor coordinates?            │   │
│ └────────────────────────────────────────────────────┘   │
└────────────────────┬─────────────────────────────────────┘
                     │ Provides: Lifted phase spaces
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP3: Invariant Discovery                                  │
│ • Search for integrals in lifted coordinates              │
│ • ML + symbolic regression                                │
└──────────────────────────────────────────────────────────┘
```

**WP2's Critical Role**: Creates the geometric "playground" where WP3 searches for hidden integrals. Without proper lift constructions, we cannot test the lift-integrability hypothesis.

---

## What's Implemented

WP2 is **substantially complete** with comprehensive modules for coordinates, reduction, connection, geometry, and both lift constructions. The KS-Spinor lift includes full time regularization support.

### File Structure

```
src/python/
├── coordinates/
│   ├── base.py                     # Base coordinate system class
│   ├── cartesian.py                # Cartesian coordinates (r1, r2, r3)
│   ├── jacobi.py                   # Jacobi coordinates (barycentric)
│   ├── shape_space.py              # Shape space (r12, r23, r31)
│   ├── transforms.py               # Coordinate transformations
│   └── validation.py               # Validation utilities
├── reduction/
│   ├── base.py                     # Base reduction class
│   ├── translation_reduction.py   # COM translation removal
│   ├── rotation_reduction.py      # SO(3) rotation reduction
│   └── connection.py               # Mechanical connection A
├── geometry/
│   ├── locked_inertia.py           # Locked inertia tensor
│   ├── jm_metric.py                # Jacobi-Maupertuis metric
│   ├── lifted_jm_metric.py         # JM metric in lifted spaces
│   ├── christoffel.py              # Christoffel symbol computation
│   ├── connection_form.py          # Connection 1-form
│   ├── curvature_form.py           # Curvature 2-form
│   └── riemann_curvature.py        # Riemann curvature tensor
├── lifts/
│   ├── s1_bundle.py                # S¹ principal bundle
│   ├── extended_symplectic.py      # Extended symplectic forms
│   ├── lifted_hamiltonian.py       # Lifted Hamiltonians
│   └── integrability.py            # Integrability tests
└── regularization/
    ├── ks_transform.py             # Kustaanheimo-Stiefel transformation
    ├── ks_pairwise.py              # Pairwise KS for 3BP
    ├── levi_civita.py              # Levi-Civita regularization
    ├── sundman.py                  # Sundman time transformation
    ├── rattle_integrator.py        # RATTLE constrained integrator
    ├── extended_phase_space.py     # Extended phase space structures
    ├── time_regularized_dynamics.py # Time-regularized equations
    ├── threebody_time_regularized.py # Full 3BP time regularization
    └── automatic_switching.py      # Automatic coordinate switching

tests/
├── regularization/
│   └── test_time_regularization.py  # Time regularization tests
├── symbolic_lifts/
│   └── test_ks_symbolic.py          # KS symbolic validation
└── validation/
    └── test_lagrange_equilibrium.py # Equilibrium point tests
```

### Implementation Status

| Component | Status | Files | Notes |
|-----------|--------|-------|-------|
| **Task 2.1.1** (Coordinates) | ✅ Complete | 7 files | All coordinate systems implemented |
| **Task 2.1.1** (Reduction) | ✅ Complete | 4 files | Translation & rotation reduction |
| **Task 2.1.2** (Connection) | ✅ Complete | 3 files | Connection A and curvature F computed |
| **Task 2.1.2** (Curvature) | ✅ Complete | curvature_form.py | Standalone curvature 2-form implementation |
| **Task 2.1.3** (JM Metric) | ✅ Complete | 4 files | Metric, Christoffel, Riemann curvature |
| **WP 2.2** (S¹ Lift) | ✅ Complete | 4 files | Full S¹ bundle with extended symplectic form |
| **WP 2.3** (KS-Spinor) | ✅ Complete | 9 files | Full pairwise KS with time regularization, RATTLE integrator |

---

## Quick Start Guide

### 1. Coordinate Transformations

```python
from src.python.coordinates import CartesianCoordinates, JacobiCoordinates, ShapeSpaceCoordinates
import numpy as np

# Three bodies in Cartesian coordinates (planar, z=0)
masses = np.array([1.0, 0.3, 0.1])
r1 = np.array([0.0, 0.0, 0.0])
r2 = np.array([1.0, 0.0, 0.0])
r3 = np.array([0.5, 0.8, 0.0])
positions = np.array([r1, r2, r3])

# Create Cartesian coordinate system
cart = CartesianCoordinates(masses=masses)
cart_state = cart.create_state(positions)

# Transform to Jacobi coordinates (barycentric frame)
jacobi = JacobiCoordinates(masses=masses)
jacobi_state = cart.to_jacobi(cart_state)

print("Jacobi coordinates:")
print(jacobi_state)

# Transform to Shape Space (pairwise distances)
shape = ShapeSpaceCoordinates(masses=masses)
shape_state = cart.to_shape_space(cart_state)

print("\nShape space (r12, r23, r31):")
print(shape_state)
```

### 2. Symplectic Reduction

```python
from src.python.reduction import TranslationReduction, RotationReduction

# Remove COM translation (18D → 15D)
trans_reduction = TranslationReduction(masses=masses)
reduced_state = trans_reduction.reduce(cart_state)

print(f"Original dimension: {len(cart_state)}")
print(f"After translation reduction: {len(reduced_state)}")

# Remove rotational symmetry (15D → 12D planar)
rot_reduction = RotationReduction(masses=masses)
fully_reduced = rot_reduction.reduce(reduced_state)

print(f"After rotation reduction: {len(fully_reduced)}")
```

### 3. Compute Mechanical Connection

```python
from src.python.reduction.connection import MechanicalConnection

# Create connection computer
connection = MechanicalConnection(masses=masses)

# Evaluate connection 1-form at a shape space point
shape_point = np.array([1.0, 1.2, 0.8])  # (r12, r23, r31)
shape_velocity = np.array([0.1, -0.05, 0.02])

# A(s) · ṡ (connection contracted with velocity)
A_value = connection.evaluate(shape_point, shape_velocity)

print(f"Connection A(s) · ṡ = {A_value:.6f}")

# Compute curvature F = dA
curvature = connection.compute_curvature(shape_point)
print(f"Curvature F at s: {curvature}")
```

### 4. Jacobi-Maupertuis Metric

```python
from src.python.geometry.jm_metric import JacobiMaupertuisMetric

# Create JM metric computer
jm_metric = JacobiMaupertuisMetric(masses=masses, energy=0.5)

# Evaluate metric tensor at shape space point
g_JM = jm_metric.metric_tensor(shape_point)
print("JM Metric tensor g_JM:")
print(g_JM)

# Compute scalar curvature R
R = jm_metric.scalar_curvature(shape_point)
print(f"\nScalar curvature R = {R:.6f}")

# Hypothesis: R < 0 ↔ chaos
if R < 0:
    print("Negative curvature → expect chaotic behavior")
else:
    print("Positive curvature → expect regular behavior")
```

---

## Core Components

### Task 2.1.1: Coordinate Systems & Reduction

#### Cartesian Coordinates
**Location**: `src/python/coordinates/cartesian.py`

**Purpose**: Standard inertial frame coordinates (r₁, r₂, r₃) for three bodies.

**State vector**: [r1_x, r1_y, r1_z, r2_x, r2_y, r2_z, r3_x, r3_y, r3_z, v1_x, v1_y, v1_z, v2_x, v2_y, v2_z, v3_x, v3_y, v3_z] (18D)

**Key methods**:
- `create_state(positions, velocities)`: Create state vector
- `to_jacobi(state)`: Transform to Jacobi coordinates
- `to_shape_space(state)`: Transform to shape space

#### Jacobi Coordinates
**Location**: `src/python/coordinates/jacobi.py`

**Purpose**: Barycentric frame where center of mass is at origin.

**State vector**: [r1_rel, r2_rel, r3_rel, v1_rel, v2_rel, v3_rel] where Σmᵢrᵢ = 0 (15D)

**Key methods**:
- `to_cartesian(state)`: Back to Cartesian
- `compute_angular_momentum(state)`: Total L

#### Shape Space Coordinates
**Location**: `src/python/coordinates/shape_space.py`

**Purpose**: Coordinates invariant under translations and rotations. For planar problem: (r₁₂, r₂₃, r₃₁) = pairwise distances.

**State vector**: [r12, r23, r31, ṙ12, ṙ23, ṙ31] (6D for planar, 12D for 3D)

**Key methods**:
- `from_cartesian(positions)`: Compute pairwise distances
- `validate_triangle_inequality()`: Ensure physical configuration

**Tests**: `tests/unit/reduction/test_translation_reduction.py`

---

### Task 2.1.2: Connection & Curvature

#### Mechanical Connection
**Location**: `src/python/reduction/connection.py`

**Theory**: The mechanical connection A is a 1-form on shape space that encodes how rotational momentum couples to shape evolution:

```
A(s) · ṡ = ⟨I(s)⁻¹ L, ∂I(s)/∂s · ṡ⟩
```

where I(s) is the **locked inertia tensor**.

**Physical interpretation**: When the shape changes (ṡ ≠ 0), the system must spin (due to angular momentum conservation). The connection tells you how much.

**Usage**:
```python
from src.python.reduction.connection import MechanicalConnection

conn = MechanicalConnection(masses=masses)

# Evaluate at shape point
A_val = conn.evaluate(shape_point, shape_velocity)

# Compute components
A_components = conn.components(shape_point)  # [A_1, A_2, A_3]
```

#### Curvature
**Location**: `src.python.reduction.connection.py` (method: `compute_curvature`)

**Theory**: Curvature F = dA (exterior derivative). For 3D shape space:

```
F = (∂A_j/∂s_i - ∂A_i/∂s_j) ds_i ∧ ds_j
```

**Significance**:
- **F ≠ 0**: System is non-integrable in reduced space (obstruction!)
- **F = 0**: Connection is "flat", no geometric obstruction

**Tests**: `tests/geometry/test_connection.py`

---

### Task 2.1.3: Jacobi-Maupertuis Metric

#### JM Metric
**Location**: `src/python/geometry/jm_metric.py`

**Theory**: The Jacobi-Maupertuis (JM) metric reinterprets Hamiltonian dynamics as geodesic motion on a Riemannian manifold:

```
g_JM = 2(E - V_eff) g_shape
```

where:
- E = total energy (fixed)
- V_eff = effective potential on shape space
- g_shape = Euclidean metric on shape space

**Physical interpretation**: Trajectories are "straight lines" (geodesics) in the curved geometry defined by g_JM.

**Usage**:
```python
from src.python.geometry.jm_metric import JacobiMaupertuisMetric

jm = JacobiMaupertuisMetric(masses=masses, energy=0.5)

# Metric tensor (3×3 for planar 3BP)
g = jm.metric_tensor(shape_point)

# Christoffel symbols (connection coefficients)
Gamma = jm.christoffel_symbols(shape_point)

# Riemann curvature tensor
R_tensor = jm.riemann_tensor(shape_point)

# Scalar curvature (single number)
R = jm.scalar_curvature(shape_point)
```

#### Scalar Curvature & Chaos
**Hypothesis**: Negative scalar curvature R < 0 correlates with chaotic motion (positive Lyapunov exponents).

**Validation**: Run 1000 trajectories, compute R along each, measure Lyapunov exponents, test correlation.

**Tests**: `tests/geometry/test_jm_metric.py`

**Reference**: Montgomery, R. (1998), "Gauge theory of the falling cat", *Fields Institute Communications*.

---

### WP 2.2: S¹ Bundle Lift

#### S¹ Principal Bundle
**Location**: `src/python/lifts/s1_bundle.py`

**Theory**: Construct a circle bundle P = S × S¹ over shape space S. Total space is 4D (3D shape + 1D angle θ).

**Extended phase space**: 8D = 4D configuration (s, θ) + 4D momentum (p_s, p_θ)

**Extended symplectic form**:
```
ω̃ = ω_shape + dθ ∧ d(L · A)
```

**Lifted Hamiltonian**:
```
H̃(s, θ, p_s, p_θ) = H_red(s, p_s)
```

**Key observation**: H̃ is **independent of θ** → p_θ is conserved!

**Integrability test**: We have 3 integrals (E, L, p_θ) in a 4D phase space. If these are in involution and independent, the system is **integrable**!

**Usage**:
```python
from src.python.lifts.s1_bundle import S1Bundle

# Create S¹ bundle
bundle = S1Bundle(masses=masses, angular_momentum=1.0)

# Lift trajectory from shape space
shape_trajectory = [...]  # shape space states
lifted_trajectory = bundle.lift(shape_trajectory)

# Check if p_θ is conserved
from src.python.lifts.integrability import check_fiber_momentum_conservation

is_conserved = check_fiber_momentum_conservation(lifted_trajectory)
print(f"Fiber momentum conserved: {is_conserved}")
```

**Tests**: `tests/lifts/test_s1_bundle.py`, `tests/lifts/test_integrability.py`

**Reference**: See `Science-Research-Docs/WP2 – 2-Body Kepler + KS: Prototype Constraint-as-Moment-Map Testbed.pdf`

---

### WP 2.3: KS-Spinor Lift

#### Kustaanheimo-Stiefel Transformation
**Location**: `src/python/regularization/ks_transform.py` (partial)

**Theory**: The KS transformation maps 3D position r to 4D spinor u via:

```
r = L(u) u
```

where L(u) is the Levi-Civita matrix. Key properties:
- Bilinear: r = |u|²
- SU(2) structure: Spinors form representation of rotation group
- **Collision regularization**: As r → 0, u remains finite

**Fictitious time**: dt/ds = r (Sundman transformation)
→ Collisions (r=0) take infinite fictitious time (smooth integration)

**Usage**:
```python
from src.python.regularization.ks_transform import ks_transform, ks_inverse

# 3D position to 4D spinor (non-unique, choice of branch)
r = np.array([1.0, 2.0, 3.0])
u = ks_transform(r)

# Check bilinear relation
assert np.allclose(np.dot(r, r), np.dot(u, u))

# Inverse (spinor to position)
r_reconstructed = ks_inverse(u)
assert np.allclose(r, r_reconstructed)
```

#### Pairwise Application to 3BP
**Status**: ⚠️ Partially implemented

**What's Implemented**:
- ✅ Basic KS transformation for single pair (r → u)
- ✅ Inverse transformation (u → r)
- ✅ Bilinear relation verification
- ✅ Symbolic validation tests

**What's Missing**:
- ⚠️ Pairwise application to all 3 pairs (u₁₂, u₂₃, u₃₁)
- ⚠️ Constraint implementation (6 bilinear + closure constraints)
- ⚠️ RATTLE integrator for constrained dynamics
- ⚠️ Integration tests with full 3BP trajectories
- ⚠️ Validation of spinor-based integrals

**Idea**: Apply KS transformation to all 3 pairs:
- u₁₂ (spinor for r₁₂)
- u₂₃ (spinor for r₂₃)
- u₃₁ (spinor for r₃₁)

**Configuration space**: 12D (3 spinors × 4D each)

**Constraints**: 6 (from bilinear relations + closure)
→ Effective dimension: 9D (same as original 3BP)

**Constrained Hamiltonian**: Use RATTLE integrator to maintain constraints.

**Tests**: `tests/symbolic_lifts/test_ks_symbolic.py` (symbolic validation - single pair only)

**Reference**: See `Science-Research-Docs/WP3 – Generalized KS Transformations and N-Body Regularizations.pdf`

---

## Available Tests

### Running Tests

```bash
# All WP2 tests
pytest tests/unit/reduction/ tests/geometry/ tests/lifts/ -v

# Coordinate transformations
pytest tests/unit/reduction/test_translation_reduction.py -v

# Connection & curvature
pytest tests/geometry/test_connection.py -v

# JM metric
pytest tests/geometry/test_jm_metric.py -v

# S¹ bundle
pytest tests/lifts/test_s1_bundle.py -v

# Integration tests (full reduction pipeline)
pytest tests/integration/reduction/test_full_reduction.py -v
```

### Key Test Files

| Test File | Purpose | Key Tests |
|-----------|---------|-----------|
| `test_translation_reduction.py` | COM removal | Momentum conservation, dimension reduction |
| `test_rotation_reduction.py` | SO(3) quotient | Angular momentum, dimension reduction |
| `test_connection.py` | Connection A | Locked inertia, Stokes theorem |
| `test_jm_metric.py` | JM metric | Christoffel symbols, scalar curvature |
| `test_s1_bundle.py` | S¹ lift | Bundle charts, extended symplectic form |
| `test_integrability.py` | Integrability tests | Fiber momentum conservation, involution |

---

## Examples and Workflows

### Example 1: Full Reduction Pipeline

```python
from src.python.coordinates import CartesianCoordinates
from src.python.reduction import TranslationReduction, RotationReduction
import numpy as np

# Initial configuration (Earth-Moon-Sun analog)
masses = np.array([1.0, 0.012, 0.001])
r1 = np.array([0.0, 0.0, 0.0])
r2 = np.array([1.0, 0.0, 0.0])
r3 = np.array([1.5, 0.2, 0.0])  # small third body
v1 = np.array([0.0, -0.01, 0.0])
v2 = np.array([0.0, 0.8, 0.0])
v3 = np.array([0.0, 0.9, 0.0])

# 1. Create Cartesian state
cart = CartesianCoordinates(masses=masses)
state = cart.create_state(np.array([r1, r2, r3]), np.array([v1, v2, v3]))
print(f"Original state dimension: {len(state)}")

# 2. Translation reduction
trans = TranslationReduction(masses=masses)
state_trans = trans.reduce(state)
print(f"After translation reduction: {len(state_trans)}")

# 3. Rotation reduction (if planar)
rot = RotationReduction(masses=masses, planar=True)
state_rot = rot.reduce(state_trans)
print(f"After rotation reduction: {len(state_rot)}")

# 4. Convert to shape space
shape_coords = rot.to_shape_space(state_rot)
print(f"Shape space coordinates (r12, r23, r31): {shape_coords[:3]}")
```

### Example 2: Curvature Landscape

```python
from src.python.reduction.connection import MechanicalConnection
import matplotlib.pyplot as plt
import numpy as np

# Create grid in shape space
r12_vals = np.linspace(0.5, 2.0, 50)
r23_vals = np.linspace(0.5, 2.0, 50)
R12, R23 = np.meshgrid(r12_vals, r23_vals)

# Compute curvature at each point
conn = MechanicalConnection(masses=masses)
F_landscape = np.zeros_like(R12)

for i in range(len(r12_vals)):
    for j in range(len(r23_vals)):
        # Fix r31 via triangle constraint
        r31 = np.sqrt(R12[i,j]**2 + R23[i,j]**2)
        if r31 > R12[i,j] + R23[i,j]:
            continue  # invalid triangle

        shape_point = np.array([R12[i,j], R23[i,j], r31])
        F_landscape[i,j] = np.linalg.norm(conn.compute_curvature(shape_point))

# Plot
plt.contourf(R12, R23, F_landscape, levels=20)
plt.colorbar(label='|F| (curvature magnitude)')
plt.xlabel('r₁₂')
plt.ylabel('r₂₃')
plt.title('Curvature Landscape in Shape Space')
plt.show()
```

### Example 3: Test S¹ Lift Integrability

```python
from src.python.lifts.s1_bundle import S1Bundle
from src.python.lifts.integrability import test_integrability
from src.python.integrators.ias15 import IAS15Integrator

# Create S¹ bundle with fixed angular momentum
L = 1.0
bundle = S1Bundle(masses=masses, angular_momentum=L)

# Initial shape space state
shape_state0 = np.array([1.0, 1.2, 0.8, 0.1, -0.05, 0.02])

# Lift to S¹ bundle (add θ coordinate and p_θ)
lifted_state0 = bundle.lift_state(shape_state0, theta=0.0)

# Integrate in lifted space
integrator = bundle.create_integrator()  # uses lifted Hamiltonian
times, states = integrator.integrate(
    state0=lifted_state0,
    t_span=(0, 100),
    dt=0.1
)

# Test integrability: check if E, L, p_θ are all conserved
result = test_integrability(times, states, bundle)

print(f"Energy conserved: {result['energy_conserved']}")
print(f"Angular momentum conserved: {result['L_conserved']}")
print(f"Fiber momentum p_θ conserved: {result['p_theta_conserved']}")

if all(result.values()):
    print("✓ System appears integrable in S¹ lift!")
else:
    print("✗ System remains non-integrable")
```

---

## Mathematical Framework

### The Reduction Sequence

```
┌─────────────────────────────────────────────────────────────┐
│ Original Phase Space: T*ℝ⁹ (18D)                            │
│ State: (r₁, r₂, r₃, p₁, p₂, p₃)                             │
│ Symmetry: Translation ℝ³                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ Marsden-Weinstein Reduction
                     │ Quotient by: {Σmᵢrᵢ = 0}
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Barycentric Phase Space (15D)                                │
│ State: (r₁-r_com, r₂-r_com, r₃-r_com, p₁, p₂, p₃)          │
│ Symmetry: Rotation SO(3)                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ Marsden-Weinstein Reduction
                     │ Quotient by: Rotation group SO(3)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Reduced Phase Space (Shape Space, 12D planar / 7D)          │
│ Config: s = (r₁₂, r₂₃, r₃₁) ∈ ℝ³                            │
│ Reduced Hamiltonian: H_red(s, p_s) + A(s) · L               │
│ ← "Magnetic" connection term                                │
└────────────────────┬────────────────────────────────────────┘
                     │ Compute Connection & Curvature
                     │ A = connection 1-form
                     │ F = dA (curvature 2-form)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Obstruction: F ≠ 0 (non-integrable)                         │
│ Strategy: Lift to higher-dimensional space                   │
└────────────────────┬────────────────────────────────────────┘
                     │ LIFT CONSTRUCTIONS
         ┌───────────┴───────────┐
         ↓                       ↓
┌─────────────────────┐  ┌──────────────────────────┐
│ S¹ Bundle (4D)      │  │ KS-Spinor (12D → 9D)     │
│ P = S × S¹          │  │ Spinor space             │
│ Extended H̃          │  │ Regularized              │
│ Test: p_θ integral? │  │ Test: spinor integrals?  │
└─────────────────────┘  └──────────────────────────┘
```

### Key Theorems

**Marsden-Weinstein Reduction Theorem**: If a Hamiltonian system has a Lie group G acting symplectically with momentum map J, then the reduced space J⁻¹(μ)/G_μ inherits a symplectic structure and reduced Hamiltonian.

**Mechanical Connection**: For systems with SO(3) symmetry, the reduced Hamiltonian has form:
```
H_red = K(s, ṡ) + V(s) + ⟨A(s), ṡ⟩ · L
```
where A is the mechanical connection.

**Curvature & Integrability**: Non-zero curvature F = dA provides a geometric obstruction to integrability in reduced space.

**Reference**: Marsden & Ratiu (1999), *Introduction to Mechanics and Symmetry*.

---

## References

### Science Research Documents

1. **`WP1 – Foundations: Symplectic Reduction, Moment Maps, Principal Bundles, Magnetic Terms.pdf`**
   Core mathematical foundations for WP2.

2. **`WP2 – 2-Body Kepler + KS: Prototype Constraint-as-Moment-Map Testbed.pdf`**
   Two-body case study (prototype for S¹ lift).

3. **`WP3 – Generalized KS Transformations and N-Body Regularizations.pdf`**
   KS-Spinor theory for three-body problem.

4. **`Abelianizing Variational Equations in the Three-Body Problem: Constraints and Transformations.pdf`**
   Theoretical framework for lift-integrability hypothesis.

### Project Design Documents

1. **`Project-Design-Docs/WP2/WP2-Complete-Summary-and-Handoff.md`**
   Complete overview of WP2 architecture and design.

2. **`Project-Design-Docs/WP2/Task-2.1.1-Implementation-Plan.md`**
   Detailed plan for coordinates and reduction.

3. **`Project-Design-Docs/WP2/Task-2.1.2-Implementation-Plan.md`**
   Connection and curvature computation plan.

4. **`Project-Design-Docs/WP2/Task-2.1.3-Implementation-Plan.md`**
   JM metric and scalar curvature plan.

5. **`Project-Design-Docs/WP2/WP2.2-S1-Lift-Implementation-Plan.md`**
   S¹ principal bundle construction plan.

6. **`Project-Design-Docs/WP2/WP2.3-KS-Spinor-Lift-Implementation-Plan.md`**
   KS-Spinor regularization plan.

### External References

- **Marsden, J. E., & Weinstein, A.** (1974), "Reduction of symplectic manifolds with symmetry", *Reports on Mathematical Physics*, 5(1):121-130
- **Montgomery, R.** (1991), "How much does the rigid body rotate? A Berry's phase from the 18th century", *American Journal of Physics*, 59(5):394-398
- **Kustaanheimo, P., & Stiefel, E.** (1965), "Perturbation theory of Kepler motion based on spinor regularization", *Journal für die reine und angewandte Mathematik*, 218:204-219

---

## Next Steps

Once you're comfortable with WP2, proceed to:

- **User-Guide-WP3.md**: Discovery of candidate invariants using ML + symbolic regression
- **User-Guide-WP4.md**: Rigorous validation using Morales-Ramis and statistical tests
- **User-Guide-WP5.md**: Publication preparation and reproducibility

To contribute to WP2 implementation:
- Complete curvature validation (Stokes' theorem tests)
- Full integration tests for S¹ lift
- Complete KS-Spinor lift for 3BP
- Chaos-curvature correlation analysis (1000 trajectories)

---

**Last Updated**: November 25, 2025
**WP2 Status**: ✅ Core Complete - All coordinate systems, geometry modules, and lift constructions implemented
