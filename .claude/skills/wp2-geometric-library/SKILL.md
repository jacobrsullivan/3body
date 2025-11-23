---
name: wp2-geometric-library
description: Use when working with coordinate transformations, bundles, lifts, or geometric objects (connection, curvature). Points to WP2 geometric foundations.
---

# WP2 Geometric Library

## Source of Truth
- **Code**: `src/python/coordinates/`, `src/python/geometry/`, `src/python/lifts/`
- **User Guide**: `User-Guides/User-Guide-WP2.md`
- **Tests**: `tests/symbolic_lifts/`

## Modules

### Coordinate Systems
**Location**: `src/python/coordinates/`

**Read** these for transformation logic:
- `cartesian.py` - Standard 18D phase space
- `jacobi.py` - Relative coordinates (15D after COM reduction)
- `shape_space.py` - Distance coordinates (12D planar)
- `transforms.py` - Conversion functions

**Usage Rule**: ALWAYS import, NEVER re-implement inline

### Geometric Objects
**Location**: `src/python/geometry/`

**Key files**:
- `connection_form.py` - Mechanical connection (1-form)
- `curvature_form.py` - Curvature (2-form, exterior derivative)
- `metric.py` - Riemannian metric on shape space

**Workflow**: See `User-Guides/User-Guide-WP2.md` Section 2

### Lift Constructions
**Location**: `src/python/lifts/`

**Implementations**:
- `s1_lift.py` - S¹ principal bundle (Montgomery-Marsden)
- `ks_regularization.py` - KS spinor coordinates (collision regularization)

**Symbolic versions**: `src/python/symbolic_lifts/ks_symbolic.py` (SymPy Hamiltonians)

## Validation
**Symplectic structure preservation**:
```python
from src.python.validation.conservation_validator import check_symplectic_form
```

**Known solutions** (for testing): `src/python/validation/periodic_orbits.py`
