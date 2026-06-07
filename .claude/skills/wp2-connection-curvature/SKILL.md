---
name: wp2-connection-curvature
description: >
  Mechanical connection, curvature computation, and Jacobi-Maupertuis metric analysis
  for the three-body problem. Use when: (1) computing connection 1-forms on shape space,
  (2) computing curvature 2-forms F = dA, (3) evaluating locked inertia tensors,
  (4) computing Jacobi-Maupertuis metrics and geodesics, (5) computing Christoffel symbols,
  (6) analyzing scalar/Riemann curvature, (7) testing curvature-chaos correlation,
  (8) understanding geometric obstructions to integrability, (9) visualizing curvature
  landscapes, or (10) preparing geometric data for WP3/WP4. Triggers on requests involving
  mechanical connection, curvature forms, locked inertia, JM metric, Christoffel symbols,
  scalar curvature, Riemann tensor, magnetic terms, geometric phases, anholonomy,
  or curvature-chaos correlation.
---

# WP2 Connection & Curvature

Geometric analysis of the mechanical connection and Jacobi-Maupertuis metric on shape space.

## Overview

The mechanical connection and its curvature are central to understanding why the three-body problem is non-integrable in reduced coordinates—and how lifting to higher dimensions might restore integrability.

```
┌─────────────────────────────────────────────────────┐
│ Full Phase Space (18D)                               │
│ Has: Energy E, Angular Momentum L conserved          │
└──────────────────────┬──────────────────────────────┘
                       │ Symplectic Reduction (SO(3))
                       ↓
┌─────────────────────────────────────────────────────┐
│ Shape Space (12D planar)                             │
│ H_red = K(s,ṡ) + V(s) + ⟨A(s), ṡ⟩ · L              │
│                         ↑                            │
│                   "Magnetic Term"                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────┐
│ F = dA ≠ 0  →  GEOMETRIC OBSTRUCTION                │
│ This curvature prevents integrability downstairs    │
└─────────────────────────────────────────────────────┘
```

## Key Concepts

| Concept | Symbol | Physical Meaning |
|---------|--------|------------------|
| **Mechanical Connection** | A | How rotation couples to shape change |
| **Curvature** | F = dA | Geometric obstruction to integrability |
| **Locked Inertia** | I(s) | Moment of inertia frozen at shape s |
| **JM Metric** | g_JM | Riemannian metric for geodesic interpretation |
| **Scalar Curvature** | R | Single number measuring local geometry |

## Quick Start

```python
from src.python.reduction.connection import MechanicalConnection
from src.python.geometry.jm_metric import JacobiMaupertuisMetric
from src.python.geometry.locked_inertia import LockedInertiaTensor
import numpy as np

masses = np.array([1.0, 0.3, 0.1])

# Shape space point: (r12, r23, r31)
shape_point = np.array([1.0, 1.2, 0.8])
shape_velocity = np.array([0.1, -0.05, 0.02])

# 1. Locked Inertia Tensor
inertia = LockedInertiaTensor(masses=masses)
I = inertia.compute(shape_point)
print(f"Locked inertia tensor:\n{I}")

# 2. Mechanical Connection
conn = MechanicalConnection(masses=masses)
A_value = conn.evaluate(shape_point, shape_velocity)
print(f"Connection A · ṡ = {A_value:.6f}")

# 3. Curvature (the obstruction!)
F = conn.compute_curvature(shape_point)
print(f"Curvature |F| = {np.linalg.norm(F):.6f}")
if np.linalg.norm(F) > 1e-10:
    print("→ Non-zero curvature: geometric obstruction exists")

# 4. Jacobi-Maupertuis Scalar Curvature
jm = JacobiMaupertuisMetric(masses=masses, energy=0.5)
R = jm.scalar_curvature(shape_point)
print(f"Scalar curvature R = {R:.6f}")
if R < 0:
    print("→ Negative curvature: expect chaotic behavior")
```

## Mechanical Connection

### Theory

When a system with rotational symmetry is reduced, angular momentum conservation creates a coupling between shape changes and rotation. The **mechanical connection** A encodes this coupling:

```
A(s) · ṡ = ⟨I(s)⁻¹ L, ∂I(s)/∂s · ṡ⟩
```

**Physical interpretation**: When the shape changes (ṡ ≠ 0), the system must rotate to conserve angular momentum. The connection tells you the rotation rate.

**Location**: `src/python/reduction/connection.py`

### Locked Inertia Tensor

The locked inertia tensor I(s) is the moment of inertia computed as if the system were "frozen" at shape s:

```python
from src.python.geometry.locked_inertia import LockedInertiaTensor

inertia = LockedInertiaTensor(masses=masses)

# Compute at shape point
I = inertia.compute(shape_point)  # 3×3 matrix

# Inverse (needed for connection)
I_inv = inertia.compute_inverse(shape_point)

# Derivative ∂I/∂s (needed for connection formula)
dI_ds = inertia.compute_derivative(shape_point)
# Returns: (3, 3, 3) tensor, dI_ds[i,j,k] = ∂I_ij/∂s_k
```

### Connection Components

```python
from src.python.reduction.connection import MechanicalConnection

conn = MechanicalConnection(masses=masses)

# Full contraction A(s) · ṡ
A_contracted = conn.evaluate(shape_point, shape_velocity)

# Individual components [A_1, A_2, A_3]
A_components = conn.components(shape_point)

# Connection as 1-form (for differential geometry)
A_form = conn.as_one_form(shape_point)
```

### Curvature 2-Form

The curvature F = dA (exterior derivative) measures the geometric obstruction to integrability:

```python
# Compute curvature matrix F_ij = ∂A_j/∂s_i - ∂A_i/∂s_j
F = conn.compute_curvature(shape_point)
# Returns: 3×3 antisymmetric matrix

# Curvature magnitude
F_magnitude = np.linalg.norm(F)

# Physical interpretation
if F_magnitude > 1e-10:
    print("F ≠ 0: Non-integrable in reduced space")
    print("This is the geometric obstruction that lifts are designed to remove")
else:
    print("F ≈ 0: Connection is flat (no obstruction)")
```

See `references/connection-theory.md` for detailed mathematical derivations.

## Jacobi-Maupertuis Metric

### Theory

The Jacobi-Maupertuis principle reinterprets Hamiltonian dynamics as geodesic motion on a Riemannian manifold:

```
g_JM = 2(E - V_eff) g_shape
```

Trajectories with fixed energy E are geodesics of this conformally scaled metric.

**Location**: `src/python/geometry/jm_metric.py`

### Metric Tensor

```python
from src.python.geometry.jm_metric import JacobiMaupertuisMetric

jm = JacobiMaupertuisMetric(masses=masses, energy=0.5)

# Metric tensor g_JM (3×3 for planar 3BP)
g = jm.metric_tensor(shape_point)

# Inverse metric
g_inv = jm.inverse_metric(shape_point)

# Line element: ds² = g_ij dx^i dx^j
# Trajectories minimize this
```

### Christoffel Symbols

Connection coefficients for geodesic equation:

```python
# Christoffel symbols Γ^k_ij
Gamma = jm.christoffel_symbols(shape_point)
# Returns: 3×3×3 array

# Geodesic equation: ẍ^k + Γ^k_ij ẋ^i ẋ^j = 0
```

### Riemann Curvature

```python
# Full Riemann tensor R^l_ijk
R_tensor = jm.riemann_tensor(shape_point)

# Ricci tensor R_ij = R^k_ikj (contraction)
Ricci = jm.ricci_tensor(shape_point)

# Scalar curvature R = g^ij R_ij
R = jm.scalar_curvature(shape_point)
```

See `references/jm-metric-theory.md` for complete theory.

## Curvature-Chaos Correlation

### Hypothesis

**Conjecture**: Negative scalar curvature R < 0 correlates with chaotic motion (positive Lyapunov exponents).

**Physical basis**: Negative curvature implies geodesic instability (geodesics diverge exponentially), analogous to chaos.

### Testing the Correlation

```python
from src.python.geometry.jm_metric import JacobiMaupertuisMetric
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer
import numpy as np

def test_curvature_chaos_correlation(trajectories, masses, energy):
    """
    Test if R < 0 correlates with chaotic motion.

    Args:
        trajectories: List of trajectory dicts with 'shape_states' and 'state0'
        masses: Mass array
        energy: Fixed energy for JM metric

    Returns:
        Correlation coefficient and analysis results
    """
    jm = JacobiMaupertuisMetric(masses=masses, energy=energy)
    analyzer = create_cr3bp_chaos_analyzer(mu=masses[1]/sum(masses))

    results = []
    for traj in trajectories:
        # Average scalar curvature along trajectory
        R_values = [jm.scalar_curvature(s) for s in traj['shape_states']]
        R_avg = np.mean(R_values)
        R_min = np.min(R_values)

        # Chaos indicator (MEGNO)
        chaos_result = analyzer.analyze(traj['state0'], t_max=100)

        results.append({
            'R_avg': R_avg,
            'R_min': R_min,
            'megno': chaos_result['megno'],
            'is_chaotic': chaos_result['classification'] == 'chaotic'
        })

    # Compute correlation
    R_values = [r['R_avg'] for r in results]
    megno_values = [r['megno'] for r in results]
    correlation = np.corrcoef(R_values, megno_values)[0, 1]

    # Count agreement
    n_agree = sum(1 for r in results
                  if (r['R_avg'] < 0) == r['is_chaotic'])
    agreement_rate = n_agree / len(results)

    return {
        'correlation': correlation,
        'agreement_rate': agreement_rate,
        'results': results
    }
```

### Curvature Landscape Visualization

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_curvature_landscape(masses, energy, n_points=50):
    """Visualize scalar curvature across shape space."""
    jm = JacobiMaupertuisMetric(masses=masses, energy=energy)

    r12_vals = np.linspace(0.5, 2.0, n_points)
    r23_vals = np.linspace(0.5, 2.0, n_points)
    R12, R23 = np.meshgrid(r12_vals, r23_vals)

    R_landscape = np.zeros_like(R12)

    for i in range(n_points):
        for j in range(n_points):
            # Compute r31 from triangle constraint
            r31 = compute_r31(R12[i,j], R23[i,j])
            if not valid_triangle(R12[i,j], R23[i,j], r31):
                R_landscape[i,j] = np.nan
                continue

            shape = np.array([R12[i,j], R23[i,j], r31])

            # Check if in allowed region (E > V)
            V_eff = compute_potential(shape, masses)
            if energy <= V_eff:
                R_landscape[i,j] = np.nan
                continue

            R_landscape[i,j] = jm.scalar_curvature(shape)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Color map: blue = negative (chaos), red = positive (regular)
    im = ax.contourf(R12, R23, R_landscape, levels=20, cmap='RdBu_r')
    plt.colorbar(im, label='Scalar Curvature R')

    # Mark R = 0 contour
    ax.contour(R12, R23, R_landscape, levels=[0], colors='black',
               linewidths=2, linestyles='--')

    ax.set_xlabel('r₁₂')
    ax.set_ylabel('r₂₃')
    ax.set_title('Scalar Curvature Landscape\n(R < 0 → chaos expected)')

    return fig
```

See `references/curvature-chaos.md` for analysis methodology.

## Complete Geometric Analysis Workflow

```python
def full_geometric_analysis(shape_point, masses, energy, angular_momentum):
    """
    Complete geometric analysis at a shape space point.

    Returns dict with all geometric quantities needed for WP3/WP4.
    """
    from src.python.geometry.locked_inertia import LockedInertiaTensor
    from src.python.reduction.connection import MechanicalConnection
    from src.python.geometry.jm_metric import JacobiMaupertuisMetric

    # 1. Locked inertia
    inertia = LockedInertiaTensor(masses=masses)
    I = inertia.compute(shape_point)
    I_inv = inertia.compute_inverse(shape_point)

    # 2. Mechanical connection
    conn = MechanicalConnection(masses=masses)
    A = conn.components(shape_point)
    F = conn.compute_curvature(shape_point)

    # 3. JM metric and curvature
    jm = JacobiMaupertuisMetric(masses=masses, energy=energy)
    g = jm.metric_tensor(shape_point)
    Gamma = jm.christoffel_symbols(shape_point)
    R_tensor = jm.riemann_tensor(shape_point)
    R_scalar = jm.scalar_curvature(shape_point)

    # 4. Magnetic term contribution
    # In reduced Hamiltonian: H_red = K + V + A·ṡ·L
    magnetic_term_coeff = np.dot(A, angular_momentum)

    # 5. Obstruction analysis
    F_magnitude = np.linalg.norm(F)
    has_obstruction = F_magnitude > 1e-10

    return {
        # Inertia
        'locked_inertia': I,
        'locked_inertia_inverse': I_inv,

        # Connection
        'connection_components': A,
        'curvature_matrix': F,
        'curvature_magnitude': F_magnitude,
        'has_geometric_obstruction': has_obstruction,

        # JM geometry
        'jm_metric': g,
        'christoffel_symbols': Gamma,
        'riemann_tensor': R_tensor,
        'scalar_curvature': R_scalar,

        # Physical
        'magnetic_term_coefficient': magnetic_term_coeff,
        'expects_chaos': R_scalar < 0,
    }
```

## Downstream Usage

### For WP3 (Invariant Discovery)

```python
# Provide geometric context for symbolic regression
geometric_data = full_geometric_analysis(shape_point, masses, E, L)

# Key quantities for WP3:
# - Connection components A: may appear in conserved quantities
# - Curvature F: determines structure of lifted integrals
# - Scalar curvature R: helps classify regular vs chaotic regions
```

### For WP4 (Validation)

```python
# Curvature provides validation targets
# If F ≠ 0 downstairs but F̃ = 0 upstairs → lift successful

# Verify curvature obstruction
assert geometric_data['has_geometric_obstruction'], "Expected non-zero curvature"

# Compare with lifted space curvature (from WP2 lift constructions)
from src.python.lifts.s1_bundle import S1Bundle
bundle = S1Bundle(masses=masses, angular_momentum=L)
F_upstairs = bundle.compute_curvature(lifted_point)
# Should be zero or reduced compared to F downstairs
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Curvature numerically zero | Invalid shape point | Check triangle inequality |
| Scalar curvature NaN | E ≤ V_eff (forbidden region) | Increase energy or check point |
| Connection blows up | Near collision (r → 0) | Use regularized coordinates |
| Negative determinant | Invalid metric | Check E > V_eff everywhere |

### Diagnostic Function

```python
def diagnose_geometry(shape_point, masses, energy):
    """Diagnose common issues with geometric computations."""
    r12, r23, r31 = shape_point

    diagnostics = {}

    # Check triangle inequality
    diagnostics['valid_triangle'] = (
        abs(r12 - r23) < r31 < r12 + r23 and
        abs(r23 - r31) < r12 < r23 + r31 and
        abs(r31 - r12) < r23 < r31 + r12
    )

    # Check for near-collision
    diagnostics['min_distance'] = min(r12, r23, r31)
    diagnostics['near_collision'] = diagnostics['min_distance'] < 0.01

    # Check energy condition
    V_eff = compute_effective_potential(shape_point, masses)
    diagnostics['E_minus_V'] = energy - V_eff
    diagnostics['allowed_region'] = diagnostics['E_minus_V'] > 0

    return diagnostics
```

## Tests

```bash
# Connection tests
pytest tests/geometry/test_connection.py -v

# Locked inertia tests
pytest tests/geometry/test_locked_inertia.py -v

# JM metric tests
pytest tests/geometry/test_jm_metric.py -v

# Curvature tests
pytest tests/geometry/test_curvature.py -v
```

## References

- `references/connection-theory.md` - Mathematical derivation of connection
- `references/jm-metric-theory.md` - Jacobi-Maupertuis theory
- `references/curvature-chaos.md` - Curvature-chaos correlation analysis
- `src/python/reduction/connection.py` - Connection implementation
- `src/python/geometry/` - All geometry modules
- `Science-Research-Docs/WP1 – Foundations.pdf` - Mathematical theory
- Montgomery (1998) - "Gauge theory of the falling cat"
- Marsden & Ratiu (1999) - *Introduction to Mechanics and Symmetry*
