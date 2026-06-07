# Configuration Guide

Complete reference for all Snakefile configuration parameters.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Sampling Parameters](#sampling-parameters)
3. [Integration Parameters](#integration-parameters)
4. [Output Parameters](#output-parameters)
5. [Validation Parameters](#validation-parameters)
6. [Parallelization Parameters](#parallelization-parameters)
7. [Configuration Templates](#configuration-templates)

---

## Configuration Overview

All configuration is specified in the `config` dictionary in `Snakefile`:

```python
config = {
    # Sampling
    ...
    # Integration
    ...
    # Output
    ...
    # Validation
    ...
    # Parallelization
    ...
}
```

Parameters can be overridden from command line:

```bash
snakemake tier1_complete --config n_samples_tier1=1000 cores=4
```

---

## Sampling Parameters

### Basic Sampling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_samples_tier1` | int | 100000 | Number of Tier 1 orbits |
| `n_samples_tier2` | int | 10000 | Number of Tier 2 orbits |
| `sobol_seed` | int | 42 | Seed for Sobol sequence (reproducibility) |
| `sobol_scramble` | bool | True | Enable Owen scrambling |

### Mass Ratio Range

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mu_min` | float | 0.001 | Minimum mass ratio |
| `mu_max` | float | 0.5 | Maximum mass ratio |
| `mu_samples` | int | 30 | Number of μ values (log-uniform) |
| `mu_scale` | str | 'log' | 'log' or 'linear' sampling |

### Jacobi Constant Range

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `C_min` | float | 2.8 | Minimum Jacobi constant |
| `C_max` | float | 3.5 | Maximum Jacobi constant |
| `C_samples` | int | 15 | Number of C values |
| `C_scale` | str | 'linear' | 'log' or 'linear' sampling |

### Initial Conditions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x_range` | tuple | (0.5, 1.5) | x position range |
| `y_range` | tuple | (-0.5, 0.5) | y position range |
| `z_range` | tuple | (-0.1, 0.1) | z position range |
| `v_max` | float | 1.0 | Maximum velocity magnitude |
| `planar_only` | bool | False | Restrict to z=0 plane |

### Adaptive Sampling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `adaptive_refinement` | bool | False | Enable adaptive refinement |
| `refinement_factor` | int | 4 | Refinement multiplier |
| `refinement_iterations` | int | 3 | Number of refinement passes |
| `gradient_threshold` | float | 0.5 | MEGNO gradient threshold for refinement |

---

## Integration Parameters

### General

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_periods` | int | 100 | Orbital periods to integrate |
| `dt_output` | float | 0.1 | Output timestep (normalized units) |
| `max_steps` | int | 10000000 | Maximum integration steps |
| `timeout` | float | 3600 | Timeout per orbit (seconds) |

### Tier 1 Integrator

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tier1_integrator` | str | 'ias15' | Integrator name |
| `tier1_tol` | float | 1e-14 | Error tolerance |
| `tier1_epsilon` | float | 1e-9 | IAS15 convergence parameter |
| `tier1_min_dt` | float | 1e-6 | Minimum timestep |
| `tier1_max_dt` | float | 0.1 | Maximum timestep |

### Tier 2 Integrator

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tier2_integrator` | str | 'adaptive_symplectic' | Integrator name |
| `tier2_order` | int | 6 | Symplectic composition order |
| `tier2_tol` | float | 1e-25 | Error tolerance |
| `tier2_precision` | str | 'qd' | Arithmetic precision |
| `tier2_sundman` | str | 'sum' | Sundman strategy |

### Regularization

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_regularization` | bool | True | Enable KS regularization |
| `regularization_threshold` | float | 0.01 | Distance threshold for switching |
| `regularization_type` | str | 'ks' | 'ks' or 'levi_civita' |
| `smooth_switching` | bool | True | Use smooth transition |

### Termination

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `escape_radius` | float | 10.0 | Distance for escape detection |
| `collision_radius` | float | 1e-6 | Distance for collision detection |
| `terminate_on_escape` | bool | True | Stop on escape |
| `terminate_on_collision` | bool | True | Stop on collision |

---

## Output Parameters

### Directory Structure

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | str | 'data' | Base output directory |
| `tier1_subdir` | str | 'tier1' | Tier 1 subdirectory |
| `tier2_subdir` | str | 'tier2' | Tier 2 subdirectory |
| `logs_dir` | str | 'logs' | Log file directory |
| `reports_dir` | str | 'reports' | Report output directory |

### Coordinate Systems

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `coordinate_systems` | list | ['rotating'] | Output frames |
| `include_inertial` | bool | False | Include inertial frame |
| `include_regularized` | bool | False | Include KS coordinates |

Options for `coordinate_systems`:
- `'rotating'`: Standard CR3BP synodic frame
- `'inertial'`: Barycentric inertial frame
- `'regularized'`: KS spinor coordinates

### HDF5 Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hdf5_compression` | str | 'gzip' | Compression algorithm |
| `hdf5_compression_opts` | int | 4 | Compression level (1-9) |
| `hdf5_shuffle` | bool | True | Enable shuffle filter |
| `hdf5_fletcher32` | bool | True | Enable checksums |
| `hdf5_chunks` | bool | True | Enable chunking |

### Parquet Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parquet_compression` | str | 'snappy' | Compression codec |
| `parquet_row_group_size` | int | 10000 | Rows per group |
| `parquet_use_dictionary` | bool | True | Dictionary encoding |
| `parquet_write_statistics` | bool | True | Column statistics |

### Output Mode

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_mode` | str | 'full' | 'full' or 'poincare' |
| `poincare_section` | str | 'y_zero' | Section type for Poincaré mode |
| `poincare_direction` | str | 'positive' | Crossing direction filter |

### Variational Equations

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `store_variational` | bool | False | Store variational equations |
| `store_monodromy` | bool | False | Store monodromy matrix |
| `store_floquet` | bool | False | Store Floquet multipliers |

---

## Validation Parameters

### Jacobi Conservation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validate_jacobi` | bool | True | Enable Jacobi validation |
| `jacobi_threshold_tier1` | float | 1e-14 | Tier 1 threshold |
| `jacobi_threshold_tier2` | float | 1e-25 | Tier 2 threshold |

### Shadow Hamiltonian

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validate_shadow` | bool | True | Enable shadow analysis |
| `shadow_threshold_tier1` | float | 1e-14 | Tier 1 drift threshold |
| `shadow_threshold_tier2` | float | 1e-25 | Tier 2 drift threshold |

### Time Reversibility

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validate_reversibility` | bool | False | Enable reversibility test |
| `reversibility_threshold_tier1` | float | 1e-12 | Tier 1 threshold |
| `reversibility_threshold_tier2` | float | 1e-20 | Tier 2 threshold |

### Chaos Analysis

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `compute_megno` | bool | True | Compute MEGNO indicator |
| `compute_fli` | bool | True | Compute FLI indicator |
| `chaos_integration_periods` | int | 100 | Periods for chaos analysis |
| `megno_threshold_regular` | float | 2.5 | MEGNO regular threshold |
| `megno_threshold_chaotic` | float | 3.0 | MEGNO chaotic threshold |

---

## Parallelization Parameters

### Local Execution

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cores` | int | 8 | Default local cores |
| `local_cores` | int | 4 | Cores for local rules |

### Resource Defaults

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mem_per_job` | str | '4G' | Memory per job |
| `time_per_job` | str | '01:00:00' | Time limit per job |
| `partition` | str | 'normal' | Default partition |

### Job Control

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_jobs` | int | 100 | Maximum concurrent jobs |
| `latency_wait` | int | 60 | Seconds between status checks |
| `restart_times` | int | 2 | Retry failed jobs |
| `keep_going` | bool | True | Continue on job failure |

---

## Configuration Templates

### Development (Fast, Low Quality)

```python
dev_config = {
    # Small sample
    'n_samples_tier1': 100,
    'n_samples_tier2': 10,

    # Short integration
    'n_periods': 10,
    'dt_output': 1.0,

    # Skip validation
    'validate_jacobi': False,
    'validate_shadow': False,
    'compute_megno': False,

    # Local only
    'cores': 4,
}
```

### Testing (Medium Quality)

```python
test_config = {
    # Moderate sample
    'n_samples_tier1': 1000,
    'n_samples_tier2': 100,

    # Standard integration
    'n_periods': 50,
    'dt_output': 0.1,

    # Basic validation
    'validate_jacobi': True,
    'validate_shadow': False,
    'compute_megno': True,

    # Local execution
    'cores': 8,
}
```

### Production (High Quality)

```python
production_config = {
    # Full sample
    'n_samples_tier1': 100000,
    'n_samples_tier2': 10000,

    # Full integration
    'n_periods': 100,
    'dt_output': 0.1,

    # Full validation
    'validate_jacobi': True,
    'validate_shadow': True,
    'validate_reversibility': True,
    'compute_megno': True,
    'compute_fli': True,

    # Cluster execution
    'max_jobs': 100,
    'partition': 'normal',
}
```

### Publication (Maximum Quality)

```python
publication_config = {
    # Extended sample
    'n_samples_tier1': 100000,
    'n_samples_tier2': 20000,

    # Extended integration
    'n_periods': 1000,
    'dt_output': 0.01,

    # All validation
    'validate_jacobi': True,
    'validate_shadow': True,
    'validate_reversibility': True,
    'compute_megno': True,
    'compute_fli': True,

    # Store variational
    'store_variational': True,
    'store_monodromy': True,

    # Multi-coordinate
    'coordinate_systems': ['rotating', 'inertial', 'regularized'],

    # Maximum compression
    'hdf5_compression_opts': 9,

    # Cluster with high resources
    'max_jobs': 500,
    'tier2_time_per_job': '08:00:00',
}
```

---

## Environment Variables

The pipeline respects these environment variables:

| Variable | Description |
|----------|-------------|
| `SNAKEMAKE_OUTPUT_CACHE` | Cache directory for outputs |
| `TMPDIR` | Temporary file directory |
| `OMP_NUM_THREADS` | OpenMP threads (set to 1 for pure Python) |
| `NUMBA_NUM_THREADS` | Numba threads |
| `HDF5_USE_FILE_LOCKING` | HDF5 file locking (set to 'FALSE' for NFS) |
