# WP2 User Guide: Geometric Reduction and Shape Space Analysis

**Version**: 1.0
**Status**: Complete (100%)
**Last Updated**: November 22, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Coordinate Systems](#coordinate-systems)
4. [Geometric Objects](#geometric-objects)
5. [Lift Constructions](#lift-constructions)
6. [Visualization](#visualization)
7. [Common Workflows](#common-workflows)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## Overview

Work Package 2 (WP2) provides the geometric foundations for investigating lift-integrability in the three-body problem. This guide explains how to use the WP2 implementation for:

- Coordinate transformations (Cartesian, Jacobi, Shape)
- Geometric analysis (connection, curvature, metrics)
- Lift constructions (S¹ bundle, KS spinor)
- Visualization and analysis

### Key Modules

```
src/python/
├── coordinates/        # Coordinate systems and transformations
├── geometry/          # Connection, curvature, JM metric
├── lifts/             # S¹ bundle and extended symplectic forms
├── regularization/    # KS-Spinor transformation and time regularization
├── symbolic_lifts/    # Symbolic implementations for Morales-Ramis
└── visualization/     # Publication-quality plotting tools
```

---

## Quick Start

### Basic Example: Coordinate Transformation

```python
import numpy as np
from src.python.coordinates.cartesian import CartesianState
from src.python.coordinates.shape_space import cartesian_to_shape_distances

# Define a Cartesian state
masses = np.array([1.0, 1.0, 1.0])
positions = np.array([
    [1.0, 0.0, 0.0],   # Body 1
    [-0.5, 0.866, 0.0], # Body 2
    [-0.5, -0.866, 0.0] # Body 3
])
velocities = np.zeros_like(positions)

state = CartesianState(
    positions=positions,
    velocities=velocities,
    masses=masses
)

# Transform to shape space
shape_state = cartesian_to_shape_distances(state)
print(f"Distances: r₁₂={shape_state.r12:.3f}, r₂₃={shape_state.r23:.3f}, r₃₁={shape_state.r31:.3f}")
```

### Symbolic KS Hamiltonian

```python
from src.python.symbolic_lifts import create_ks_pairwise_3bp
import sympy as sp

# Create pairwise KS Hamiltonian for 3BP
ks_ham = create_ks_pairwise_3bp()

# Get symbolic system
system = ks_ham.get_symbolic_system()

print(f"Hamiltonian: {system.H}")
print(f"Constraints: {len(system.constraints)} equations")

# Compute Hessian for Morales-Ramis analysis
hess = ks_ham.compute_hessian()
print(f"Hessian shape: {hess.shape}")  # (24, 24)
```

### Visualization Example

```python
from src.python.visualization import plot_connection_field

def my_connection(r12, r23, r31):
    """Example connection evaluator."""
    L = r12**2 + r23**2 + r31**2  # Total angular momentum proxy
    I = r12**2 * r23**2 * r31**2  # Moment of inertia proxy
    A = L / (I + 1.0)
    return (A * r12, A * r23, 0.0)

fig = plot_connection_field(my_connection, grid_resolution=30)
# fig.savefig('connection_field.png')
```

---

## Coordinate Systems

### 1. Cartesian Coordinates

**Module**: `coordinates.cartesian`

Standard inertial coordinates for three bodies.

**State**: `CartesianState`
- `positions`: (3, 3) array - [x, y, z] for each body
- `velocities`: (3, 3) array
- `masses`: (3,) array

**Operations**:
- `compute_energy()`: Total energy E
- `compute_angular_momentum()`: Angular momentum L
- `enforce_barycenter()`: Project to center-of-mass frame

### 2. Jacobi Coordinates

**Module**: `coordinates.jacobi`

Decouples center-of-mass motion from internal dynamics.

**Transformation**:
```python
from src.python.coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian

jacobi_state = cartesian_to_jacobi(cartesian_state)
# Round-trip
cartesian_back = jacobi_to_cartesian(jacobi_state)
```

### 3. Shape Space Coordinates

**Module**: `coordinates.shape_space`

Represents configuration by mutual distances: (r₁₂, r₂₃, r₃₁).

**Key Functions**:
- `cartesian_to_shape_distances()`: Extract distances
- `shape_distances_to_cartesian_canonical()`: Reconstruct (with orientation fixing)

**Constraints**: Triangle inequality must be satisfied.

---

## Geometric Objects

### Connection One-Form A

**Module**: `geometry.connection_form`

The mechanical connection A encodes rotational coupling.

**Computation**:
```python
from src.python.geometry.connection_form import compute_connection_coefficients
from src.python.coordinates.shape_space import ShapeSpaceState

shape_state = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0)
masses = np.array([1.0, 1.0, 1.0])

conn_form = compute_connection_coefficients(shape_state, masses)
magnitude = conn_form.magnitude()
```

**Scientific Significance**: A ≠ 0 indicates rotational coupling (magnetic connection).

### Curvature Two-Form F

**Module**: `geometry.curvature_form`

F = dA is the exterior derivative of the connection.

**Computation**:
```python
from src.python.geometry.curvature_form import compute_curvature

curvature_form = compute_curvature(shape_state, masses)
is_flat = curvature_form.is_flat(tolerance=1e-10)
```

**Scientific Significance**: F ≠ 0 proves non-integrability "downstairs" (obstruction to integrability).

### Jacobi-Maupertuis Metric

**Module**: `geometry.jm_metric`

The JM metric makes trajectories geodesics.

**Computation**:
```python
from src.python.geometry.jm_metric import RiemannianMetric

energy = -1.0  # Example energy
metric = RiemannianMetric.compute(shape_state, energy, masses)

# Scalar curvature
R = metric.scalar_curvature()
```

**Scientific Significance**: R < 0 correlates with chaos.

---

## Lift Constructions

### S¹ Bundle Lift

**Module**: `lifts.s1_bundle`

Minimal spatial lift adding fiber coordinate θ ∈ S¹.

**Phase Space**: 8D (3 shape + 1 fiber) × 2

**Key Property**: Fiber momentum p_θ is conserved (potential third integral).

**Usage**:
```python
from src.python.lifts.s1_bundle import BundleState, S1Bundle

bundle = S1Bundle()
bundle_state = BundleState(
    shape_coords=np.array([1.0, 1.0]),
    theta=0.0,
    shape_momenta=np.array([0.1, 0.1]),
    p_theta=0.5
)

# Check conservation
# Integrate dynamics and verify p_θ is conserved
```

### KS-Spinor Lift

**Module**: `regularization.ks_transform`

Higher-dimensional lift using spinor coordinates.

**Phase Space**: 24D (12 spinor + 12 momenta), constrained to 18D

**Key Properties**:
- Regularizes collisions (r → 0 smooth in u-space)
- Time regularization: dt/ds = r
- SU(2) structure

**Usage**:
```python
from src.python.regularization.ks_transform import cartesian_to_ks, ks_to_cartesian

# For a single pair
r_vec = np.array([1.0, 0.0, 0.0])
v_vec = np.array([0.0, 0.5, 0.0])

u, u_prime = cartesian_to_ks(r_vec, v_vec)
r_back, v_back = ks_to_cartesian(u, u_prime)

# Verify bilinear relation
assert np.isclose(np.linalg.norm(r_vec)**2, np.linalg.norm(u)**4)
```

---

## Visualization

### Connection Visualization

```python
from src.python.visualization import plot_connection_field, plot_connection_magnitude_heatmap

# Vector field
fig1 = plot_connection_field(
    connection_evaluator=my_conn_func,
    grid_resolution=30,
    arrow_scale=0.5
)

# Heatmap
fig2 = plot_connection_magnitude_heatmap(
    connection_evaluator=my_conn_func,
    grid_resolution=100,
    log_scale=True
)
```

### Curvature Visualization

```python
from src.python.visualization import plot_curvature_heatmap, plot_curvature_vs_chaos

# Curvature landscape
fig = plot_curvature_heatmap(
    curvature_evaluator=my_curv_func,
    grid_resolution=80
)

# Curvature-chaos correlation
curvatures = np.random.randn(1000)  # From simulation
lyapunovs = np.random.randn(1000)
fig = plot_curvature_vs_chaos(curvatures, lyapunovs)
```

### Trajectory Visualization

```python
from src.python.visualization import plot_shape_trajectory, plot_lift_comparison

# Single trajectory
trajectory = np.random.rand(100, 2) * 2 + 0.5  # Example
fig = plot_shape_trajectory(trajectory, color_by='time')

# Lift comparison
traj_reduced = trajectory
traj_s1 = np.column_stack([trajectory, np.linspace(0, 2*np.pi, 100)])  # Add θ
fig = plot_lift_comparison(traj_reduced, traj_s1=traj_s1)
```

---

## Common Workflows

### Workflow 1: Geometric Analysis Pipeline

```python
# 1. Define initial state
from src.python.coordinates.cartesian import CartesianState
state = CartesianState(positions, velocities, masses)

# 2. Transform to shape space
from src.python.coordinates.shape_space import cartesian_to_shape_distances
shape_state = cartesian_to_shape_distances(state)

# 3. Compute connection
from src.python.geometry.connection_form import compute_connection_coefficients
connection = compute_connection_coefficients(shape_state, masses)

# 4. Compute curvature
from src.python.geometry.curvature_form import compute_curvature
curvature = compute_curvature(shape_state, masses)

# 5. Visualize
from src.python.visualization import plot_connection_field
fig = plot_connection_field(lambda r12, r23, r31: connection.evaluate(...))
```

### Workflow 2: Symbolic Morales-Ramis Analysis

```python
# 1. Create symbolic KS system
from src.python.symbolic_lifts import create_ks_pairwise_3bp, prepare_ks_for_upstairs_mr_test

masses_numeric = (1.0, 1.0, 1.0)
data = prepare_ks_for_upstairs_mr_test(masses_numeric, orbit_name='figure8')

# 2. Extract components
H_upstairs = data['hamiltonian']
hess_upstairs = data['hessian']
constraints = data['constraints']

# 3. Compute variational equations (for Morales-Ramis)
# Use Hessian to form upstairs NVEs
# Apply Kovacic algorithm (WP4.2)
```

### Workflow 3: Lift Comparison

```python
# Compare S¹ vs KS for integrability

# S¹ Lift
from src.python.lifts.s1_bundle import S1Bundle, integrate_bundle_dynamics
bundle = S1Bundle()
traj_s1, conserved = integrate_bundle_dynamics(initial_state, t_span)

# KS Lift
from src.python.regularization.threebody_time_regularized import integrate_ks_regularized
traj_ks, info = integrate_ks_regularized(initial_state_ks, s_span)

# Visualize comparison
from src.python.visualization import plot_lift_comparison
fig = plot_lift_comparison(traj_reduced, traj_s1, traj_ks)
```

---

## Troubleshooting

### Common Issues

#### 1. Triangle Inequality Violated

**Error**: "Invalid triangle: distances do not satisfy inequality"

**Cause**: Shape space coordinates (r₁₂, r₂₃, r₃₁) must form a valid triangle.

**Solution**:
```python
from src.python.coordinates.shape_space import is_valid_triangle

if not is_valid_triangle(r12, r23, r31):
    # Adjust distances or use different configuration
    pass
```

#### 2. KS Transform Singularity

**Error**: Division by zero in KS transformation

**Cause**: Binary collision (r → 0) in non-regularized coordinates.

**Solution**: Use time-regularized integration in fictitious time s:
```python
from src.python.regularization.time_regularized_dynamics import TimeRegularizedDynamics

dynamics = TimeRegularizedDynamics()
# Integrate in s instead of t
```

#### 3. Constraint Drift in RATTLE

**Error**: "Constraint violation exceeds tolerance"

**Cause**: Accumulated numerical error in constrained integration.

**Solution**: Reduce time step or increase projection frequency:
```python
from src.python.regularization.rattle_integrator import RATTLEConfig

config = RATTLEConfig(dt=0.001, max_iter=50, tolerance=1e-12)
```

#### 4. Hessian Computation Too Slow

**Issue**: Symbolic Hessian computation takes too long.

**Solution**:
1. Simplify symbolic expressions first
2. Use numerical differentiation for large systems
3. Parallelize computation (for grid evaluations)

---

## API Reference

### Coordinates Package

**`coordinates.cartesian`**
- `CartesianState`: Dataclass for Cartesian coordinates
- `compute_energy(state)`: Total energy
- `enforce_barycenter(state)`: Project to COM frame

**`coordinates.jacobi`**
- `JacobiState`: Dataclass for Jacobi coordinates
- `cartesian_to_jacobi(cartesian_state)`: Transform
- `jacobi_to_cartesian(jacobi_state)`: Inverse transform

**`coordinates.shape_space`**
- `ShapeSpaceState`: Dataclass for shape coordinates
- `cartesian_to_shape_distances(state)`: Extract distances
- `is_valid_triangle(r12, r23, r31)`: Check validity

### Geometry Package

**`geometry.connection_form`**
- `ConnectionForm`: Connection one-form class
- `compute_connection_coefficients(shape_state, masses)`: Compute A

**`geometry.curvature_form`**
- `CurvatureForm`: Curvature two-form class
- `compute_curvature(shape_state, masses)`: Compute F = dA

**`geometry.jm_metric`**
- `RiemannianMetric`: JM metric class
- `compute(shape_state, energy, masses)`: Compute metric tensor

### Symbolic Lifts Package

**`symbolic_lifts.ks_symbolic`**
- `KSSpinorHamiltonian`: Single-pair KS Hamiltonian
- `KSPairwiseHamiltonian`: Three-body pairwise KS
- `create_ks_pairwise_3bp(masses)`: Factory function
- `prepare_ks_for_upstairs_mr_test(masses)`: MR preparation

**`symbolic_lifts.s1_symbolic`**
- `S1BundleHamiltonian`: S¹ lift Hamiltonian
- `create_s1_hamiltonian_cr3bp(mu)`: CR3BP version

### Visualization Package

**`visualization.connection_plots`**
- `plot_connection_field(evaluator, **kwargs)`: Vector field
- `plot_connection_magnitude_heatmap(evaluator, **kwargs)`: Heatmap

**`visualization.curvature_plots`**
- `plot_curvature_heatmap(evaluator, **kwargs)`: Curvature map
- `plot_curvature_vs_chaos(R, λ, **kwargs)`: Correlation plot

**`visualization.trajectory_plots`**
- `plot_shape_trajectory(traj, **kwargs)`: Single trajectory
- `plot_lift_comparison(traj_reduced, traj_s1, traj_ks)`: Multi-lift

---

## Best Practices

### 1. Coordinate Choice

- **Cartesian**: Initial conditions, debugging
- **Jacobi**: Hamiltonian decoupling, CR3BP
- **Shape**: Geometric analysis, connection/curvature
- **S¹**: Testing integrability (p_θ conservation)
- **KS**: Near-collision regions, regularization

### 2. Numerical Precision

- Use `float64` (double precision) as default
- For high-precision near collisions: `float128` or sympy
- Validate conservation laws (E, L) at every step

### 3. Visualization

- Start with low resolution (grid_resolution=30) for quick preview
- Use high resolution (≥100) for publication figures
- Save figures as PNG (raster) for quick view, PDF (vector) for publication

---

## Further Reading

- Design Documents: `/Project-Design-Docs/WP2/`
- Implementation Status: `/Project-Design-Docs/Implementation-Status/Implementation-WP2-22ndNov2025.md`
- Examples: `/examples/wp2/`
- Tutorials: `/notebooks/tutorials/`

---

**Document Version**: 1.0
**Status**: Complete
**Last Updated**: November 22, 2025
