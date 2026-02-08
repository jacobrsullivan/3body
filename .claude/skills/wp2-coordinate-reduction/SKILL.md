---
name: wp2-coordinate-reduction
description: >
  Coordinate transformations and symplectic reduction for the three-body problem. 
  Use when: (1) transforming between Cartesian, Jacobi, and Shape Space coordinates, 
  (2) performing translation reduction (removing COM), (3) performing rotation reduction 
  (SO(3) quotient), (4) computing angular momentum, (5) validating triangle inequality 
  constraints, (6) reconstructing full state from reduced state, (7) understanding 
  dimension counting (18D → 15D → 12D), (8) implementing Marsden-Weinstein reduction, 
  (9) computing conserved quantities during reduction, or (10) preparing reduced states 
  for WP2 lift constructions. Triggers on requests involving coordinate systems, Cartesian, 
  Jacobi, shape space, symplectic reduction, center-of-mass removal, rotation reduction, 
  SO(3) quotient, angular momentum, momentum map, phase space dimension, or conservation laws.
---

# WP2 Coordinate Reduction

Coordinate transformations and Marsden-Weinstein symplectic reduction for the three-body problem.

## Overview

Symplectic reduction exploits symmetries to reduce phase space dimension while preserving Hamiltonian structure. For the three-body problem:

```
┌────────────────────────────────────────────────────────────────┐
│ FULL CARTESIAN PHASE SPACE (18D)                               │
│ State: (r₁, r₂, r₃, p₁, p₂, p₃)                               │
│ Symmetries: Translation (ℝ³), Rotation (SO(3))                 │
│ Conserved: Total momentum P, Angular momentum L                 │
└──────────────────────────┬─────────────────────────────────────┘
                           │ Translation Reduction
                           │ Fix P = 0 (COM at origin)
                           │ Quotient by ℝ³
                           ↓
┌────────────────────────────────────────────────────────────────┐
│ JACOBI/BARYCENTRIC COORDINATES (15D)                           │
│ State: Relative positions, relative momenta                     │
│ Constraint: Σmᵢrᵢ = 0                                          │
│ Remaining symmetry: SO(3) rotation                              │
└──────────────────────────┬─────────────────────────────────────┘
                           │ Rotation Reduction  
                           │ Fix L (angular momentum)
                           │ Quotient by SO(3)/SO(2)
                           ↓
┌────────────────────────────────────────────────────────────────┐
│ SHAPE SPACE (12D planar / 7D with fixed L)                     │
│ State: Pairwise distances (r₁₂, r₂₃, r₃₁) + conjugate momenta  │
│ Rotation eliminated → dynamics on shape space                   │
│ Magnetic term appears from connection curvature                 │
└────────────────────────────────────────────────────────────────┘
```

## Quick Start

```python
from src.python.coordinates import (
    CartesianCoordinates, 
    JacobiCoordinates, 
    ShapeSpaceCoordinates
)
from src.python.reduction import TranslationReduction, RotationReduction
import numpy as np

# Three-body configuration
masses = np.array([1.0, 0.3, 0.1])
positions = np.array([
    [0.0, 0.0, 0.0],    # r₁
    [1.0, 0.0, 0.0],    # r₂
    [0.5, 0.8, 0.0]     # r₃ (planar)
])
velocities = np.array([
    [0.0, -0.1, 0.0],
    [0.0, 0.5, 0.0],
    [0.0, 0.6, 0.0]
])

# 1. Create Cartesian state (18D)
cart = CartesianCoordinates(masses=masses)
state_18d = cart.create_state(positions, velocities)
print(f"Cartesian: {len(state_18d)}D")

# 2. Translation reduction (18D → 15D)
trans = TranslationReduction(masses=masses)
state_15d = trans.reduce(state_18d)
print(f"After translation: {len(state_15d)}D")

# 3. Rotation reduction (15D → 12D for planar)
rot = RotationReduction(masses=masses, planar=True)
state_12d = rot.reduce(state_15d)
print(f"After rotation: {len(state_12d)}D")

# 4. Extract shape coordinates
shape_coords = rot.to_shape_space(state_12d)
print(f"Shape space: (r₁₂, r₂₃, r₃₁) = {shape_coords[:3]}")
```

## Coordinate Systems

### Cartesian Coordinates (18D)

**Location**: `src/python/coordinates/cartesian.py`

Standard inertial frame with absolute positions and velocities.

```python
from src.python.coordinates import CartesianCoordinates

cart = CartesianCoordinates(masses=masses)

# Create state vector (18D)
state = cart.create_state(positions, velocities)
# Layout: [r1_x, r1_y, r1_z, r2_x, r2_y, r2_z, r3_x, r3_y, r3_z,
#          v1_x, v1_y, v1_z, v2_x, v2_y, v2_z, v3_x, v3_y, v3_z]

# Extract components
r1, r2, r3 = cart.get_positions(state)  # Each (3,)
v1, v2, v3 = cart.get_velocities(state)

# Compute conserved quantities
P_total = cart.total_momentum(state)      # Total linear momentum
L_total = cart.angular_momentum(state)     # Total angular momentum
E = cart.total_energy(state)               # Total energy
```

### Jacobi Coordinates (15D)

**Location**: `src/python/coordinates/jacobi.py`

Barycentric frame where center of mass is at origin. Uses relative (Jacobi) vectors.

```python
from src.python.coordinates import JacobiCoordinates

jacobi = JacobiCoordinates(masses=masses)

# Transform from Cartesian
jacobi_state = jacobi.from_cartesian(cart_state)
# Layout: 15D (COM constrained to origin)

# Jacobi vectors
# ρ₁ = r₂ - r₁ (relative position, body 2 wrt body 1)
# ρ₂ = r₃ - (m₁r₁ + m₂r₂)/(m₁+m₂) (body 3 wrt COM of 1,2)
rho1, rho2, prho1, prho2 = jacobi.get_jacobi_vectors(jacobi_state)

# Reduced masses
mu1 = masses[0] * masses[1] / (masses[0] + masses[1])
mu2 = masses[2] * (masses[0] + masses[1]) / sum(masses)

# Angular momentum (conserved)
L = jacobi.compute_angular_momentum(jacobi_state)

# Back to Cartesian
cart_state_back = jacobi.to_cartesian(jacobi_state)
```

### Shape Space Coordinates (6D-12D)

**Location**: `src/python/coordinates/shape_space.py`

Coordinates invariant under translations and rotations—pure "shape" information.

```python
from src.python.coordinates import ShapeSpaceCoordinates

shape = ShapeSpaceCoordinates(masses=masses)

# Pairwise distances
distances = shape.from_positions(positions)
r12, r23, r31 = distances
# r12 = |r₂ - r₁|, r23 = |r₃ - r₂|, r31 = |r₁ - r₃|

# Full shape space state (6D for configuration, 12D for phase space)
shape_state = shape.from_cartesian(cart_state)

# Validate triangle inequality
is_valid = shape.validate_triangle_inequality(distances)
# Must satisfy: |rij - rjk| < rki < rij + rjk for all permutations

# Shape space metric
g_shape = shape.metric_tensor(distances)
```

See `references/coordinate-systems.md` for complete theory.

## Symplectic Reduction

### Marsden-Weinstein Theorem

**Theorem**: If G acts on (M, ω) with equivariant momentum map J: M → g*, then the reduced space J⁻¹(μ)/G_μ inherits a symplectic structure.

For the three-body problem:
- **G = SE(3)** (translations + rotations)
- **Momentum map**: J = (P, L) (linear + angular momentum)
- **Reduction at μ**: Fix P = 0, fix or quotient by L

### Translation Reduction (18D → 15D)

**Location**: `src/python/reduction/translation_reduction.py`

Removes center-of-mass motion using momentum map J_trans = P (total momentum).

```python
from src.python.reduction import TranslationReduction

trans = TranslationReduction(masses=masses)

# Reduce: fix P = 0, place COM at origin
reduced_state = trans.reduce(full_state)

# The reduced state lives in the constrained subspace
# where Σmᵢrᵢ = 0 and Σpᵢ = 0

# Verify constraint satisfaction
P_total = trans.total_momentum(reduced_state)
assert np.allclose(P_total, 0), "Momentum constraint violated"

COM = trans.center_of_mass(reduced_state)
assert np.allclose(COM, 0), "COM constraint violated"
```

**Dimension counting**:
- Original: 18D (9 positions + 9 momenta)
- Constraints: 3 (P = 0) + 3 (COM = 0) = 6
- Reduced: 18 - 6 + 3 (gauge freedom) = 15D

### Rotation Reduction (15D → 12D/7D)

**Location**: `src/python/reduction/rotation_reduction.py`

Quotients out SO(3) rotation symmetry using momentum map J_rot = L (angular momentum).

```python
from src.python.reduction import RotationReduction

# Planar case (z = 0): 15D → 12D
rot = RotationReduction(masses=masses, planar=True)
reduced_planar = rot.reduce(jacobi_state)

# 3D case with fixed |L|: 15D → 7D
rot_3d = RotationReduction(masses=masses, planar=False, fix_L_magnitude=True)
reduced_3d = rot_3d.reduce(jacobi_state, L_magnitude=1.0)

# Quotient by SO(3)/SO(2) (rotations about L axis remain)
# For L ≠ 0, stabilizer is SO(2), so we quotient by SO(3)/SO(2) ≅ S²
```

**Dimension counting (3D, fixed |L|)**:
- Jacobi: 15D
- Fix |L| = const: -1D
- Quotient SO(3): -3D + 1D (SO(2) stabilizer) = -2D
- Result: 15 - 1 - 2 = 12D (not 7D—need to also fix L direction for 7D)

See `references/reduction-theory.md` for complete theory.

## Full Reduction Pipeline

```python
def full_reduction_pipeline(positions, velocities, masses, planar=True):
    """
    Complete reduction from Cartesian to shape space.
    
    Returns dict with all intermediate states and computed quantities.
    """
    from src.python.coordinates import CartesianCoordinates
    from src.python.reduction import TranslationReduction, RotationReduction
    
    # 1. Create Cartesian state
    cart = CartesianCoordinates(masses=masses)
    state_cart = cart.create_state(positions, velocities)
    
    # 2. Compute conserved quantities
    P_total = cart.total_momentum(state_cart)
    L_total = cart.angular_momentum(state_cart)
    E_total = cart.total_energy(state_cart)
    
    # 3. Translation reduction
    trans = TranslationReduction(masses=masses)
    state_jacobi = trans.reduce(state_cart)
    
    # 4. Rotation reduction
    rot = RotationReduction(masses=masses, planar=planar)
    state_reduced = rot.reduce(state_jacobi)
    
    # 5. Extract shape coordinates
    shape_coords = rot.to_shape_space(state_reduced)
    
    return {
        # States at each level
        'cartesian': state_cart,
        'jacobi': state_jacobi,
        'reduced': state_reduced,
        'shape': shape_coords,
        
        # Dimensions
        'dim_cartesian': len(state_cart),
        'dim_jacobi': len(state_jacobi),
        'dim_reduced': len(state_reduced),
        
        # Conserved quantities
        'P_total': P_total,
        'L_total': L_total,
        'E_total': E_total,
        
        # Reduction info
        'planar': planar,
        'masses': masses,
    }
```

## Reconstruction

### From Reduced to Full State

```python
def reconstruct_full_state(reduced_state, masses, COM, orientation, planar=True):
    """
    Reconstruct full Cartesian state from reduced state.
    
    Args:
        reduced_state: State in reduced coordinates
        masses: Mass array
        COM: Center of mass position (3,) and velocity (3,)
        orientation: Rotation matrix R (3×3) or angle θ for planar
        planar: Whether system is planar
        
    Returns:
        Full 18D Cartesian state
    """
    # 1. Lift from shape to Jacobi (add rotation)
    rot = RotationReduction(masses=masses, planar=planar)
    jacobi_state = rot.reconstruct(reduced_state, orientation)
    
    # 2. Lift from Jacobi to Cartesian (add COM)
    trans = TranslationReduction(masses=masses)
    cart_state = trans.reconstruct(jacobi_state, COM)
    
    return cart_state
```

### Gauge Freedom

Reduction introduces gauge freedom—different full states map to same reduced state:

```python
def gauge_orbit(reduced_state, masses, n_samples=10):
    """
    Sample the gauge orbit of a reduced state.
    
    All states in the orbit reduce to the same reduced_state.
    """
    orbits = []
    
    for _ in range(n_samples):
        # Random COM position and velocity
        COM_pos = np.random.randn(3)
        COM_vel = np.random.randn(3)
        
        # Random orientation
        theta = np.random.uniform(0, 2*np.pi)
        R = rotation_matrix_z(theta)
        
        # Reconstruct
        full_state = reconstruct_full_state(
            reduced_state, masses, 
            (COM_pos, COM_vel), R
        )
        orbits.append(full_state)
    
    return orbits
```

## Validation

### Symplectic Structure Preservation

```python
from src.python.coordinates.validation import validate_reduction

def validate_symplectic_reduction(original_state, reduced_state, masses):
    """
    Verify reduction preserves symplectic structure.
    """
    result = validate_reduction(
        original_state=original_state,
        reduced_state=reduced_state,
        masses=masses
    )
    
    print(f"Symplectic form preserved: {result['symplectic_preserved']}")
    print(f"Momentum conserved: {result['momentum_conserved']}")
    print(f"Energy conserved: {result['energy_conserved']}")
    print(f"Dimension reduction correct: {result['dimension_correct']}")
    
    return result
```

### Constraint Verification

```python
def verify_constraints(state, masses, level='jacobi'):
    """
    Verify that constraints are satisfied at given level.
    """
    if level == 'jacobi':
        # COM at origin
        cart = CartesianCoordinates(masses=masses)
        positions = cart.get_positions(state)
        com = sum(m * r for m, r in zip(masses, positions)) / sum(masses)
        
        # Total momentum zero
        momenta = cart.get_momenta(state)
        P_total = sum(momenta)
        
        return {
            'COM_at_origin': np.allclose(com, 0),
            'COM_error': np.linalg.norm(com),
            'momentum_zero': np.allclose(P_total, 0),
            'momentum_error': np.linalg.norm(P_total)
        }
        
    elif level == 'shape':
        # Triangle inequality
        r12, r23, r31 = state[:3]
        
        valid = (
            abs(r12 - r23) < r31 < r12 + r23 and
            abs(r23 - r31) < r12 < r23 + r31 and
            abs(r31 - r12) < r23 < r31 + r12
        )
        
        return {'triangle_inequality': valid}
```

## Downstream Usage

### For WP2 Lift Constructions

```python
# Shape space state is input for S¹ bundle lift
from src.python.lifts.s1_bundle import S1Bundle

# Get reduced state
result = full_reduction_pipeline(positions, velocities, masses)
shape_state = result['shape']
L = result['L_total']

# Construct S¹ bundle
bundle = S1Bundle(masses=masses, angular_momentum=np.linalg.norm(L))

# Lift to bundle (adds θ coordinate)
lifted_state = bundle.lift_state(shape_state, theta=0.0)
```

### For WP2 Connection/Curvature

```python
# Shape coordinates are input for connection computation
from src.python.reduction.connection import MechanicalConnection

shape_point = result['shape'][:3]  # (r12, r23, r31)
shape_velocity = result['shape'][3:6]

conn = MechanicalConnection(masses=masses)
A = conn.evaluate(shape_point, shape_velocity)
F = conn.compute_curvature(shape_point)
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Triangle inequality violated | Invalid shape configuration | Filter initial conditions |
| Dimension mismatch | Wrong planar/3D setting | Check `planar=True/False` |
| Reconstruction fails | Missing gauge info | Store COM and orientation |
| Symplectic error | Numerical precision | Use higher precision |

### Diagnostic

```python
def diagnose_reduction(state, masses, expected_dim):
    """Diagnose reduction issues."""
    actual_dim = len(state)
    
    diagnostics = {
        'dimension_correct': actual_dim == expected_dim,
        'actual_dim': actual_dim,
        'expected_dim': expected_dim,
    }
    
    # Check for NaN
    diagnostics['has_nan'] = np.any(np.isnan(state))
    
    # Check for infinity
    diagnostics['has_inf'] = np.any(np.isinf(state))
    
    # Check shape constraint (if applicable)
    if expected_dim <= 12:
        r12, r23, r31 = state[:3]
        diagnostics['valid_triangle'] = validate_triangle(r12, r23, r31)
    
    return diagnostics
```

## Tests

```bash
# Translation reduction
pytest tests/unit/reduction/test_translation_reduction.py -v

# Rotation reduction
pytest tests/unit/reduction/test_rotation_reduction.py -v

# Full pipeline
pytest tests/integration/reduction/test_full_reduction.py -v

# Coordinate transformations
pytest tests/unit/coordinates/ -v
```

## References

- `references/coordinate-systems.md` - Coordinate system details
- `references/reduction-theory.md` - Marsden-Weinstein theory
- `references/dimension-counting.md` - Dimension analysis
- `src/python/coordinates/` - All coordinate implementations
- `src/python/reduction/` - Reduction implementations
- `Science-Research-Docs/WP1 – Foundations.pdf` - Mathematical theory
- Marsden & Ratiu (1999) - *Introduction to Mechanics and Symmetry*
