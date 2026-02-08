# Data Schema Reference

Complete schema documentation for HDF5 and Parquet output formats used in the trajectory catalogue.

## Table of Contents

1. [HDF5 Schema](#hdf5-schema)
2. [Parquet Schema](#parquet-schema)
3. [Coordinate Systems](#coordinate-systems)
4. [Validation Metrics](#validation-metrics)
5. [Reading Examples](#reading-examples)

---

## HDF5 Schema

### File Naming Convention

```
data/tier{1,2}/hdf5/orbit_mu{mu}_C{C}_{orbit_id:05d}.h5

Examples:
  orbit_mu0.0121_C3.00_00001.h5
  orbit_mu0.5000_C2.80_12345.h5
```

### Complete Schema

```
/
├── metadata/
│   ├── orbit_id: int64                 # Unique identifier
│   ├── mu: float64                     # Mass ratio
│   ├── C: float64                      # Jacobi constant (initial)
│   ├── energy: float64                 # Total energy
│   ├── angular_momentum: float64       # z-component of L
│   ├── integrator: string              # 'ias15', 'adaptive_symplectic', etc.
│   ├── precision_tier: int             # 1 or 2
│   ├── n_periods: int                  # Integration duration (periods)
│   ├── dt_output: float64              # Output timestep
│   ├── creation_time: string           # ISO 8601 timestamp
│   ├── sobol_seed: int                 # Sampling seed
│   └── sobol_index: int                # Index in Sobol sequence
│
├── initial_conditions/
│   ├── x0: float64                     # Initial x (rotating)
│   ├── y0: float64                     # Initial y (rotating)
│   ├── z0: float64                     # Initial z (rotating)
│   ├── vx0: float64                    # Initial vx (rotating)
│   ├── vy0: float64                    # Initial vy (rotating)
│   └── vz0: float64                    # Initial vz (rotating)
│
├── trajectory/
│   ├── time: (N,) float64              # Time array [0, T_final]
│   │
│   ├── rotating/                       # Synodic (co-rotating) frame
│   │   ├── positions: (N, 3) float64   # [x, y, z]
│   │   └── velocities: (N, 3) float64  # [vx, vy, vz]
│   │
│   ├── inertial/                       # Barycentric inertial frame
│   │   ├── positions: (N, 3) float64   # [X, Y, Z]
│   │   └── velocities: (N, 3) float64  # [VX, VY, VZ]
│   │
│   └── regularized/                    # KS coordinates (if applicable)
│       ├── u: (N, 4) float64           # KS position spinor
│       ├── p_u: (N, 4) float64         # KS momentum spinor
│       └── fictitious_time: (N,) float64  # Sundman time s
│
├── chaos/
│   ├── megno: float64                  # MEGNO indicator (final value)
│   ├── fli: float64                    # FLI indicator (final value)
│   ├── megno_history: (M,) float64     # MEGNO time series (optional)
│   ├── fli_history: (M,) float64       # FLI time series (optional)
│   ├── classification: string          # 'regular', 'chaotic', 'borderline'
│   └── lyapunov_estimate: float64      # Estimated max Lyapunov exponent
│
├── validation/
│   ├── jacobi_constant/
│   │   ├── initial: float64            # C at t=0
│   │   ├── final: float64              # C at t=T
│   │   ├── min: float64                # min(C) over trajectory
│   │   ├── max: float64                # max(C) over trajectory
│   │   ├── drift_absolute: float64     # max - min
│   │   └── drift_relative: float64     # (max - min) / |mean|
│   │
│   ├── shadow_hamiltonian/
│   │   ├── drift_rate: float64         # Per-period drift
│   │   ├── H2_coefficient: float64     # Leading correction term
│   │   └── effective_order: int        # Observed convergence order
│   │
│   └── reversibility/                  # (Tier 2 only)
│       ├── position_error: float64     # RMS position error
│       └── velocity_error: float64     # RMS velocity error
│
├── variational/                        # (Tier 2 only)
│   ├── fundamental_matrix: (N, 6, 6) float64  # Φ(t)
│   ├── monodromy_matrix: (6, 6) float64       # Φ(T) for periodic
│   ├── floquet_multipliers: (6,) complex128  # Eigenvalues of M
│   ├── lyapunov_exponents: (6,) float64      # From Floquet
│   └── is_periodic: bool                      # Orbit closure check
│
└── poincare/                           # (optional, Poincaré mode)
    ├── section_type: string            # 'y_zero', 'x_L1', etc.
    ├── crossing_times: (K,) float64    # Times of crossings
    ├── crossing_states: (K, 6) float64 # States at crossings
    └── crossing_directions: (K,) int   # +1 or -1
```

### Compression Settings

```python
# Default compression for HDF5
hdf5_config = {
    'compression': 'gzip',
    'compression_opts': 4,      # Level 1-9 (4 = balanced)
    'shuffle': True,            # Improves compression
    'fletcher32': True,         # Checksum for integrity
}

# For Tier 2 (maximum compression)
tier2_hdf5_config = {
    'compression': 'gzip',
    'compression_opts': 9,
    'shuffle': True,
    'fletcher32': True,
}
```

---

## Parquet Schema

### Catalogue File

```
data/tier{1,2}/parquet/catalogue.parquet
```

### Column Schema

| Column | Type | Description |
|--------|------|-------------|
| `orbit_id` | int64 | Unique identifier |
| `mu` | float64 | Mass ratio |
| `C` | float64 | Jacobi constant |
| `x0` | float64 | Initial x position |
| `y0` | float64 | Initial y position |
| `z0` | float64 | Initial z position |
| `vx0` | float64 | Initial x velocity |
| `vy0` | float64 | Initial y velocity |
| `vz0` | float64 | Initial z velocity |
| `energy` | float64 | Total energy |
| `angular_momentum` | float64 | Angular momentum (z) |
| `period_estimate` | float64 | Estimated orbital period |
| `megno` | float64 | MEGNO indicator |
| `fli` | float64 | FLI indicator |
| `classification` | string | 'regular'/'chaotic'/'borderline' |
| `jacobi_drift` | float64 | Relative Jacobi drift |
| `shadow_drift` | float64 | Shadow Hamiltonian drift |
| `precision_tier` | int32 | 1 or 2 |
| `integrator` | string | Integrator used |
| `n_timesteps` | int32 | Number of output points |
| `integration_time` | float64 | Total time integrated |
| `is_periodic` | bool | Whether orbit closes |
| `close_encounter` | bool | Had close encounter |
| `validation_passed` | bool | All checks passed |
| `hdf5_path` | string | Path to HDF5 file |

### Parquet Settings

```python
parquet_config = {
    'compression': 'snappy',    # Fast compression
    'row_group_size': 10000,    # Rows per group
    'use_dictionary': True,     # For string columns
    'write_statistics': True,   # Enable predicate pushdown
}
```

---

## Coordinate Systems

### Rotating (Synodic) Frame

Standard CR3BP coordinates with origin at barycenter, x-axis toward smaller primary:

```
x: Along line connecting primaries (toward m2)
y: In orbital plane, perpendicular to x
z: Normal to orbital plane (right-hand rule)

Equations of motion:
  ẍ - 2ẏ = ∂Ω/∂x
  ÿ + 2ẋ = ∂Ω/∂y
  z̈      = ∂Ω/∂z
```

### Inertial Frame

Barycentric J2000-like frame (non-rotating):

```
X: Fixed direction (e.g., vernal equinox)
Y: In reference plane, perpendicular to X
Z: Normal to reference plane

Transformation from rotating:
  X = x·cos(t) - y·sin(t)
  Y = x·sin(t) + y·cos(t)
  Z = z

  VX = (vx - y)·cos(t) - (vy + x)·sin(t)
  VY = (vx - y)·sin(t) + (vy + x)·cos(t)
  VZ = vz
```

### Regularized (KS) Coordinates

Kustaanheimo-Stiefel transformation for collision regularization:

```
Spinor u = (u0, u1, u2, u3) ∈ R⁴

Position mapping:
  x = u0² - u1² - u2² + u3²
  y = 2(u0·u1 - u2·u3)
  z = 2(u0·u2 + u1·u3)
  
Radial distance:
  r = |u|² = u0² + u1² + u2² + u3²

Fictitious time s (Sundman):
  dt/ds = r
```

---

## Validation Metrics

### Jacobi Constant Conservation

```python
def jacobi_constant(state, mu):
    """Compute Jacobi constant."""
    x, y, z, vx, vy, vz = state
    
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    
    Omega = 0.5 * (x**2 + y**2) + (1 - mu)/r1 + mu/r2 + 0.5*mu*(1-mu)
    v_squared = vx**2 + vy**2 + vz**2
    
    return 2*Omega - v_squared

# Drift calculation
C_values = [jacobi_constant(s, mu) for s in states]
drift_absolute = max(C_values) - min(C_values)
drift_relative = drift_absolute / abs(np.mean(C_values))
```

### Thresholds

| Metric | Tier 1 Pass | Tier 2 Pass | Fail |
|--------|-------------|-------------|------|
| `jacobi_drift_relative` | < 10⁻¹⁴ | < 10⁻²⁵ | > 10⁻¹⁰ |
| `shadow_drift` | < 10⁻¹⁴ | < 10⁻²⁵ | > 10⁻¹⁰ |
| `reversibility_error` | < 10⁻¹² | < 10⁻²⁰ | > 10⁻⁸ |
| `monodromy_det_error` | N/A | < 10⁻²⁰ | > 10⁻¹⁰ |

---

## Reading Examples

### HDF5 Reading

```python
import h5py
import numpy as np

def load_orbit(filepath):
    """Load complete orbit data from HDF5."""
    data = {}
    
    with h5py.File(filepath, 'r') as f:
        # Metadata
        data['mu'] = f['metadata']['mu'][()]
        data['C'] = f['metadata']['C'][()]
        data['orbit_id'] = f['metadata']['orbit_id'][()]
        
        # Trajectory (rotating frame)
        data['time'] = f['trajectory']['time'][:]
        data['positions'] = f['trajectory']['rotating']['positions'][:]
        data['velocities'] = f['trajectory']['rotating']['velocities'][:]
        
        # Combine into states
        data['states'] = np.hstack([data['positions'], data['velocities']])
        
        # Chaos indicators
        data['megno'] = f['chaos']['megno'][()]
        data['fli'] = f['chaos']['fli'][()]
        data['classification'] = f['chaos']['classification'][()].decode()
        
        # Validation
        data['jacobi_drift'] = f['validation']['jacobi_constant']['drift_relative'][()]
        
        # Variational (Tier 2 only)
        if 'variational' in f:
            data['monodromy'] = f['variational']['monodromy_matrix'][:]
            data['floquet'] = f['variational']['floquet_multipliers'][:]
    
    return data
```

### Parquet Reading

```python
import pandas as pd
import pyarrow.parquet as pq

# Load full catalogue
df = pd.read_parquet('data/tier1/parquet/catalogue.parquet')

# Filtered loading (efficient)
df_regular = pd.read_parquet(
    'data/tier1/parquet/catalogue.parquet',
    filters=[('classification', '==', 'regular')]
)

# Column subset (memory efficient)
df_summary = pd.read_parquet(
    'data/tier1/parquet/catalogue.parquet',
    columns=['orbit_id', 'mu', 'C', 'megno', 'classification']
)

# Lazy loading with PyArrow
table = pq.read_table(
    'data/tier1/parquet/catalogue.parquet',
    columns=['orbit_id', 'mu', 'C'],
    filters=[('jacobi_drift', '<', 1e-14)]
)
df = table.to_pandas()
```

### Batch Processing

```python
from pathlib import Path

def process_catalogue(catalogue_dir, func, **kwargs):
    """Apply function to all orbits in catalogue."""
    results = []
    
    for hdf5_file in Path(catalogue_dir).glob('*.h5'):
        orbit = load_orbit(hdf5_file)
        result = func(orbit, **kwargs)
        results.append(result)
    
    return results

# Example: compute mean MEGNO
def get_megno(orbit):
    return orbit['megno']

megno_values = process_catalogue('data/tier1/hdf5/', get_megno)
print(f"Mean MEGNO: {np.mean(megno_values):.3f}")
```
