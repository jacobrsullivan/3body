# Tier Configuration Reference

Detailed configuration for the two-tier precision strategy used in catalogue generation.

## Table of Contents

1. [Tier Overview](#tier-overview)
2. [Tier 1 Configuration](#tier-1-configuration)
3. [Tier 2 Configuration](#tier-2-configuration)
4. [Automatic Tier Selection](#automatic-tier-selection)
5. [Precision Budget](#precision-budget)
6. [Performance Characteristics](#performance-characteristics)

---

## Tier Overview

| Aspect | Tier 1 | Tier 2 |
|--------|--------|--------|
| **Target orbits** | 10⁵ | 10⁴ |
| **Precision** | IEEE double (~16 digits) | QD double-double (~31 digits) |
| **Target ΔC/C** | < 10⁻¹⁴ | < 10⁻²⁵ |
| **Integrator** | IAS15 | AdaptiveSymplectic |
| **Regularization** | Optional | Required (Sundman) |
| **Purpose** | ML training, exploration | Validation, Morales-Ramis |
| **Speed** | ~50 periods/second | ~5-10 periods/second |
| **Storage per orbit** | ~1-10 MB | ~10-100 MB |

---

## Tier 1 Configuration

### Purpose

Tier 1 provides the main exploration catalogue for:
- WP3 machine learning training data
- Parameter space mapping
- Initial candidate screening
- Chaos classification

### Integrator: IAS15

```python
tier1_config = {
    'integrator': 'ias15',
    'integrator_kwargs': {
        'epsilon': 1e-9,          # Adaptive timestep control
        'min_dt': 1e-6,           # Minimum timestep
        'max_dt': 0.1,            # Maximum timestep
    },
    'precision': 'double',
    'tol': 1e-14,
}
```

**IAS15 Characteristics:**
- 15th-order adaptive Gauss-Radau
- Non-symplectic but excellent energy conservation
- Automatic timestep adaptation
- Handles most close encounters without regularization

### Output Configuration

```python
tier1_output = {
    'dt_output': 0.1,              # Output every 0.1 time units
    'n_periods': 100,              # 100 orbital periods
    'coordinate_systems': ['rotating'],  # Single coordinate system
    'store_variational': False,    # No variational equations
    'compression': 'gzip',
    'compression_level': 4,
}
```

### Validation Thresholds

```python
tier1_validation = {
    'jacobi_drift_max': 1e-14,
    'shadow_drift_max': 1e-14,
    'reversibility_error_max': 1e-12,  # Optional
    'escape_radius': 10.0,
    'collision_radius': 1e-6,
}
```

### Sampling Parameters

```python
tier1_sampling = {
    'n_samples': 100000,
    'mu_range': (0.001, 0.5),      # Log-uniform
    'C_range': (2.8, 3.5),         # Linear
    'sobol_seed': 42,
    'scramble': True,
}
```

---

## Tier 2 Configuration

### Purpose

Tier 2 provides the validation catalogue for:
- WP4 rigorous validation
- Morales-Ramis test (variational equations)
- Publication-quality results
- Periodic orbit families

### Integrator: AdaptiveSymplectic

```python
tier2_config = {
    'integrator': 'adaptive_symplectic',
    'integrator_kwargs': {
        'order': 6,               # 6th-order composition
        'tol': 1e-20,             # Error tolerance
        'sundman_strategy': 'sum', # Time regularization
        'min_dt': 1e-10,
        'max_dt': 0.01,
    },
    'precision': 'qd',            # Double-double arithmetic
    'tol': 1e-25,
}
```

**AdaptiveSymplectic Characteristics:**
- Symplectic structure preservation
- Sundman time transformation for close encounters
- Error control via step doubling
- Requires QD library for full precision

### Sundman Strategies

| Strategy | Formula | Best For |
|----------|---------|----------|
| `'sum'` | g = 1/(r₁ + r₂) | Balanced, general use |
| `'product'` | g = 1/(r₁ · r₂) | Binary close encounters |
| `'min'` | g = 1/min(r₁, r₂) | Single primary approach |

### Output Configuration

```python
tier2_output = {
    'dt_output': 0.01,             # Finer output
    'n_periods': 1000,             # Longer integration
    'coordinate_systems': ['rotating', 'inertial', 'regularized'],
    'store_variational': True,     # For Morales-Ramis
    'store_monodromy': True,       # For periodic orbits
    'compression': 'gzip',
    'compression_level': 9,        # Maximum compression
}
```

### Validation Thresholds

```python
tier2_validation = {
    'jacobi_drift_max': 1e-25,
    'shadow_drift_max': 1e-25,
    'reversibility_error_max': 1e-20,
    'monodromy_det_error_max': 1e-20,  # |det(M) - 1|
    'escape_radius': 10.0,
    'collision_radius': 1e-8,
}
```

### QD Library Usage

```python
# Enable QD arithmetic
from src.python.qd_python import dd_real

# All state variables in double-double
state_qd = [dd_real(x) for x in state0]
mu_qd = dd_real(mu)

# Integration in extended precision
integrator = AdaptiveSymplecticIntegrator(
    mu=mu_qd,
    arithmetic='qd'
)
```

---

## Automatic Tier Selection

The pipeline can automatically select the appropriate tier:

```python
def select_tier(state0, mu, initial_result=None):
    """
    Automatically select precision tier based on orbit characteristics.

    Returns:
        'tier1' or 'tier2'
    """
    # Always use Tier 2 for:
    # - Periodic orbit families
    # - Morales-Ramis validation
    # - Close encounter orbits

    if initial_result is not None:
        # Promote if Tier 1 precision violated
        if initial_result['jacobi_drift'] > 1e-14:
            return 'tier2'

        # Promote borderline chaos
        if 2.5 <= initial_result['megno'] <= 3.0:
            return 'tier2'

    # Check for close encounters in initial conditions
    x, y, z = state0[:3]
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    r_min = min(r1, r2)

    if r_min < 0.1:  # Close to primary
        return 'tier2'

    return 'tier1'
```

### Promotion Workflow

```python
def integrate_with_promotion(state0, mu, t_max):
    """Integrate with automatic tier promotion."""

    # Try Tier 1 first
    result = integrate_tier1(state0, mu, t_max)

    # Check if promotion needed
    if not validate_tier1(result):
        print(f"Promoting orbit to Tier 2 (Jacobi drift: {result['jacobi_drift']:.2e})")
        result = integrate_tier2(state0, mu, t_max)

    return result
```

---

## Precision Budget

### Tier 1 Error Budget

| Source | Allocation | Notes |
|--------|-----------|-------|
| Floating-point roundoff | 10⁻¹⁶ | IEEE double limit |
| Integrator truncation | 10⁻¹⁵ | IAS15 15th order |
| Close encounters | 10⁻¹² | Without regularization |
| Output interpolation | 10⁻¹⁴ | Dense output |
| **Total budget** | **10⁻¹⁴** | Conservative sum |

### Tier 2 Error Budget

| Source | Allocation | Notes |
|--------|-----------|-------|
| Floating-point roundoff | 10⁻³² | QD double-double |
| Integrator truncation | 10⁻²⁶ | 6th order symplectic |
| Close encounters | 10⁻²⁵ | With Sundman regularization |
| Output interpolation | 10⁻²⁵ | Symplectic interpolation |
| **Total budget** | **10⁻²⁵** | Conservative sum |

---

## Performance Characteristics

### Computational Cost

| Operation | Tier 1 | Tier 2 | Ratio |
|-----------|--------|--------|-------|
| Integration (per period) | 20 ms | 200 ms | 10x |
| Chaos analysis | 50 ms | 500 ms | 10x |
| Validation | 10 ms | 100 ms | 10x |
| I/O (per orbit) | 5 ms | 20 ms | 4x |
| **Total per orbit** | ~100 ms | ~1 s | 10x |

### Storage Requirements

| Component | Tier 1 | Tier 2 |
|-----------|--------|--------|
| Trajectory (100 periods) | 1 MB | 10 MB |
| Variational equations | N/A | 5 MB |
| Monodromy matrix | N/A | 1 KB |
| Chaos indicators | 100 B | 100 B |
| **Per orbit total** | ~1 MB | ~15 MB |
| **Full catalogue** | ~100 GB | ~150 GB |

### Parallelization Efficiency

```
Speedup vs cores (Tier 1, 10,000 orbits):
  1 core:   100%  (baseline)
  4 cores:  380%  (95% efficiency)
  8 cores:  720%  (90% efficiency)
  16 cores: 1280% (80% efficiency)
  32 cores: 2240% (70% efficiency)

Bottlenecks:
- I/O (mitigated by local scratch)
- Memory bandwidth (mitigated by chunking)
- Load imbalance (mitigated by job grouping)
```

### Memory Usage

```
Per-job memory requirements:
  Tier 1: 2-4 GB (trajectory buffer)
  Tier 2: 4-8 GB (extended precision + variational)

Aggregation memory:
  1,000 orbits: 4 GB
  10,000 orbits: 16 GB
  100,000 orbits: 64 GB (chunked processing required)
```

---

## Configuration Templates

### Conservative (Maximum Precision)

```python
conservative_config = {
    'tier1': {
        'integrator': 'ias15',
        'tol': 1e-15,
        'n_periods': 200,
        'validate_all': True,
    },
    'tier2': {
        'integrator': 'adaptive_symplectic',
        'order': 6,
        'tol': 1e-26,
        'n_periods': 2000,
        'store_variational': True,
    }
}
```

### Balanced (Default)

```python
balanced_config = {
    'tier1': {
        'integrator': 'ias15',
        'tol': 1e-14,
        'n_periods': 100,
        'validate_jacobi': True,
    },
    'tier2': {
        'integrator': 'adaptive_symplectic',
        'order': 6,
        'tol': 1e-25,
        'n_periods': 1000,
        'store_variational': True,
    }
}
```

### Fast (Exploration)

```python
fast_config = {
    'tier1': {
        'integrator': 'ias15',
        'tol': 1e-12,
        'n_periods': 50,
        'validate_jacobi': False,  # Skip validation
    },
    # No Tier 2 for exploration
}
```
