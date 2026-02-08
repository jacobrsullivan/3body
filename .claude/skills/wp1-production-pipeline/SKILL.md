---
name: wp1-production-pipeline
description: >
  Production pipeline for large-scale CR3BP trajectory catalogue generation using 
  Snakemake orchestration. Use when: (1) generating trajectory catalogues at scale, 
  (2) running production integrations on HPC/SLURM clusters, (3) configuring Sobol 
  parameter sampling, (4) exporting to HDF5/Parquet formats, (5) managing parallel 
  batch jobs with checkpointing, (6) setting up multi-coordinate output (rotating, 
  inertial, regularized), (7) configuring Dask distributed computing, or (8) preparing 
  data for WP2/WP3/WP4 consumption. Triggers on requests involving catalogue generation, 
  production runs, Snakemake workflows, batch processing, HPC job submission, SLURM 
  configuration, data export, checkpointing, restart/recovery, or pipeline orchestration.
---

# WP1 Production Pipeline

Large-scale trajectory catalogue generation with Snakemake orchestration for HPC environments.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Parameter Generation (Sobol sampling)                            │
│    Input:  config (μ range, C range, n_samples)                     │
│    Output: params/tier{1,2}/samples.parquet                         │
├─────────────────────────────────────────────────────────────────────┤
│ 2. Parallel Integration (per-orbit, auto-integrator selection)      │
│    Input:  Initial conditions + integrator config                   │
│    Output: trajectories/tier{1,2}/orbit_*.h5                        │
├─────────────────────────────────────────────────────────────────────┤
│ 3. Chaos Analysis (MEGNO & FLI per orbit)                          │
│    Input:  Trajectory data                                          │
│    Output: chaos/tier{1,2}/chaos_*.parquet                          │
├─────────────────────────────────────────────────────────────────────┤
│ 4. Validation (Jacobi drift, shadow Hamiltonian)                   │
│    Input:  Trajectory + chaos data                                  │
│    Output: validation/tier{1,2}/metrics_*.parquet                   │
├─────────────────────────────────────────────────────────────────────┤
│ 5. Aggregation (HDF5 hierarchical + Parquet flat)                  │
│    Input:  All per-orbit files                                      │
│    Output: data/tier{1,2}/catalogue.{h5,parquet}                    │
├─────────────────────────────────────────────────────────────────────┤
│ 6. Quality Report (statistics, histograms, failures)               │
│    Input:  Aggregated catalogue                                     │
│    Output: reports/validation_report.html                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Activate environment
mamba activate wp1_env

# Dry run (show execution plan)
snakemake -n

# Run Tier 1 catalogue (10⁵ orbits) with 8 local cores
snakemake tier1_complete --cores 8

# Run on SLURM cluster
snakemake tier1_complete --profile slurm

# Resume interrupted run (checkpointing built-in)
snakemake tier1_complete --cores 8 --rerun-incomplete
```

## Precision Tiers

| Tier | Orbits | Precision | Integrator | Target ΔC | Use Case |
|------|--------|-----------|------------|-----------|----------|
| **Tier 1** | 10⁵ | Double | IAS15 | < 10⁻¹⁴ | Exploration, WP3 ML training |
| **Tier 2** | 10⁴ | Double-Double | AdaptiveSymplectic + QD | < 10⁻²⁵ | WP4 validation, Morales-Ramis |

See `references/tier-configuration.md` for detailed precision analysis.

## Snakemake Commands

**Location**: `Snakefile`

### Basic Commands

```bash
# List all available targets
snakemake --list

# Dry run (preview without execution)
snakemake -n

# Run with N local cores
snakemake --cores N

# Run specific target
snakemake <target> --cores N

# Force re-run of all rules
snakemake <target> --cores N --forceall

# Force re-run of specific rule
snakemake --forcerun <rule_name> --cores N

# Generate DAG visualization
snakemake --dag | dot -Tpng > dag.png

# Generate detailed rulegraph
snakemake --rulegraph | dot -Tpng > rulegraph.png
```

### Key Targets

| Target | Description | Typical Runtime |
|--------|-------------|-----------------|
| `tier1_complete` | Full Tier 1 catalogue (10⁵ orbits) | 4-8 hours (8 cores) |
| `tier2_complete` | Full Tier 2 catalogue (10⁴ orbits) | 8-16 hours (8 cores) |
| `tier1_integration` | Integration only (no chaos analysis) | 2-4 hours |
| `tier1_chaos` | Chaos analysis only | 1-2 hours |
| `validation_report` | Generate quality report | 10-30 min |
| `parquet_export` | Export to ML-ready format | 10-30 min |
| `clean` | Remove all outputs | immediate |

### Checkpointing and Recovery

```bash
# Resume interrupted run (automatic checkpoint detection)
snakemake tier1_complete --cores 8 --rerun-incomplete

# Show incomplete jobs
snakemake --list-incomplete

# Unlock directory after crash
snakemake --unlock

# Show reason for re-running jobs
snakemake -n --reason
```

## Configuration

Edit the `config` section in `Snakefile`:

```python
config = {
    # === Sampling Parameters ===
    'n_samples_tier1': 100000,      # Number of Tier 1 orbits
    'n_samples_tier2': 10000,       # Number of Tier 2 orbits
    'sobol_seed': 42,               # Reproducible sampling

    # === Mass Ratio Range ===
    'mu_min': 0.001,                # Minimum mass ratio (log-uniform)
    'mu_max': 0.5,                  # Maximum mass ratio
    'mu_samples': 30,               # Number of μ values

    # === Jacobi Constant Range ===
    'C_min': 2.8,                   # Minimum Jacobi constant
    'C_max': 3.5,                   # Maximum Jacobi constant
    'C_samples': 15,                # Number of C values

    # === Integration Parameters ===
    'n_periods': 100,               # Orbital periods per orbit
    'dt_output': 0.1,               # Output timestep (normalized)
    'max_steps': 10000000,          # Maximum integration steps

    # === Precision ===
    'tier1_tol': 1e-14,             # Tier 1 tolerance
    'tier2_tol': 1e-25,             # Tier 2 tolerance (requires QD)

    # === Output ===
    'output_dir': 'data',
    'tier1_subdir': 'tier1',
    'tier2_subdir': 'tier2',
    'coordinate_systems': ['rotating', 'inertial'],  # Multi-coord output

    # === Parallelization ===
    'cores': 8,                     # Default local cores
    'mem_per_job': '4G',            # Memory per job
    'time_per_job': '01:00:00',     # Time limit per job

    # === Validation ===
    'validate_jacobi': True,
    'validate_shadow': True,
    'validate_reversibility': False,  # Slow, enable for Tier 2
}
```

See `references/configuration-guide.md` for all parameters.

## HPC/SLURM Integration

### Cluster Profile Setup

Create `~/.config/snakemake/slurm/config.yaml`:

```yaml
cluster:
  mkdir -p logs/{rule} &&
  sbatch
    --partition={resources.partition}
    --cpus-per-task={threads}
    --mem={resources.mem_mb}
    --time={resources.runtime}
    --job-name=smk-{rule}-{wildcards}
    --output=logs/{rule}/{wildcards}.out
    --error=logs/{rule}/{wildcards}.err

default-resources:
  - partition=normal
  - mem_mb=4000
  - runtime=60

set-threads: 1
set-resources:
  - integrate_orbit:mem_mb=8000
  - integrate_orbit:runtime=120
  - chaos_analysis:mem_mb=4000
  - aggregate_catalogue:mem_mb=32000

jobs: 100  # Max concurrent jobs
```

### Running on SLURM

```bash
# Submit to cluster
snakemake tier1_complete --profile slurm

# With job grouping (fewer submissions)
snakemake tier1_complete --profile slurm --group-components integrate=10

# Monitor jobs
squeue -u $USER | grep smk

# Cancel all pipeline jobs
scancel -u $USER -n "smk-*"
```

See `references/hpc-configuration.md` for detailed HPC setup.

## Sobol Sampling

**Location**: `src/python/ml/sobol_sampling.py`

Deterministic quasi-random sampling for reproducibility:

```python
from src.python.ml.sobol_sampling import SobolSampler
import numpy as np

# Create sampler
sampler = SobolSampler(dim=6, seed=42)

# Generate N samples in [0,1]^6
samples = sampler.generate(n=100000)

# Scale to physical ranges
mu_samples = 10**(samples[:, 0] * (np.log10(mu_max) - np.log10(mu_min)) + np.log10(mu_min))
C_samples = samples[:, 1] * (C_max - C_min) + C_min
x0_samples = samples[:, 2] * (x_max - x_min) + x_min
# ... etc for other dimensions
```

**Why Sobol?**
- **Low discrepancy** → better coverage than random with fewer samples
- **Deterministic** → reproducible catalogues (same seed = same samples)
- **Efficient** → ~4x better coverage than pseudo-random for same sample size

### Adaptive Refinement

**Location**: `src/python/pipeline/adaptive_sampling.py`

Refine sampling in high-gradient regions (chaos boundaries):

```python
from src.python.pipeline.adaptive_sampling import AdaptiveSampler

# Initial coarse grid
initial_samples = sobol_sampler.generate(n=1000)
metrics = [compute_chaos_metric(s) for s in initial_samples]

# Adaptively refine where MEGNO gradient is high
sampler = AdaptiveSampler(
    refinement_factor=4,
    gradient_threshold=0.5
)
refined = sampler.refine(
    samples=initial_samples,
    metrics=metrics,
    num_refinements=3
)

print(f"Initial: {len(initial_samples)}")
print(f"Refined: {len(refined)}")  # More samples near chaos boundaries
```

## Data Output Formats

### HDF5 (Hierarchical - Archival)

**Location**: `data/tier{1,2}/hdf5/`

```
data/tier1/hdf5/
├── orbit_mu0.01_C3.0_00001.h5
├── orbit_mu0.01_C3.0_00002.h5
└── ...

# Schema per file:
/metadata
  ├── mu: float64           # Mass ratio
  ├── C: float64            # Jacobi constant
  ├── orbit_id: int64       # Unique identifier
  └── integrator: string    # 'ias15' or 'adaptive_symplectic'

/trajectory
  ├── time: (N,) float64          # Time array
  ├── rotating/
  │   ├── positions: (N, 3) float64   # [x, y, z] in rotating frame
  │   └── velocities: (N, 3) float64  # [vx, vy, vz] in rotating frame
  ├── inertial/
  │   ├── positions: (N, 3) float64   # [X, Y, Z] in inertial frame
  │   └── velocities: (N, 3) float64  # [VX, VY, VZ] in inertial frame
  └── regularized/  (if close encounters)
      ├── u: (N, 4) float64           # KS coordinates
      └── p_u: (N, 4) float64         # KS momenta

/chaos
  ├── megno: float64
  ├── fli: float64
  └── classification: string   # 'regular', 'chaotic', 'borderline'

/validation
  ├── jacobi_drift: float64    # max(C) - min(C)
  ├── shadow_drift: float64    # Shadow Hamiltonian drift rate
  └── precision_tier: int      # 1 or 2
```

**Reading HDF5:**
```python
import h5py

with h5py.File('data/tier1/hdf5/orbit_mu0.01_C3.0_00042.h5', 'r') as f:
    # Metadata
    mu = f['metadata']['mu'][()]
    C = f['metadata']['C'][()]

    # Trajectory in rotating frame
    t = f['trajectory']['time'][:]
    q_rot = f['trajectory']['rotating']['positions'][:]
    p_rot = f['trajectory']['rotating']['velocities'][:]

    # Chaos indicators
    megno = f['chaos']['megno'][()]
    classification = f['chaos']['classification'][()].decode()

    # Validation metrics
    jacobi_drift = f['validation']['jacobi_drift'][()]
```

### Parquet (Flat - ML-Ready)

**Location**: `data/tier{1,2}/parquet/`

Flattened table format optimized for ML pipelines:

```
catalogue.parquet columns:
─────────────────────────────────
orbit_id          int64       Unique identifier
mu                float64     Mass ratio
C                 float64     Jacobi constant
x0, y0, z0        float64     Initial position (rotating)
vx0, vy0, vz0     float64     Initial velocity (rotating)
period            float64     Estimated orbital period
megno             float64     MEGNO indicator
fli               float64     FLI indicator
classification    string      'regular'/'chaotic'/'borderline'
jacobi_drift      float64     Conservation quality
shadow_drift      float64     Backward error
precision_tier    int         1 or 2
integrator        string      Integrator used
n_timesteps       int         Number of output points
integration_time  float64     Total integration time
```

**Reading Parquet:**
```python
import pandas as pd
import pyarrow.parquet as pq

# Load entire catalogue
df = pd.read_parquet('data/tier1/parquet/catalogue.parquet')

# Filter regular orbits
regular = df[df['classification'] == 'regular']

# Get high-precision orbits
precise = df[df['jacobi_drift'] < 1e-14]

# Filter by mass ratio range
earth_moon = df[(df['mu'] > 0.01) & (df['mu'] < 0.015)]

# Lazy loading for large catalogues
table = pq.read_table('data/tier1/parquet/catalogue.parquet',
                      columns=['orbit_id', 'mu', 'C', 'megno'])
```

See `references/data-schema.md` for complete schema documentation.

## Multi-Coordinate Output

The pipeline outputs trajectories in multiple coordinate systems for different analysis needs:

| Coordinate System | Best For | Equations |
|-------------------|----------|-----------|
| **Rotating** | CR3BP analysis, WP2 lifts | Standard synodic frame |
| **Inertial** | Physical interpretation | Barycentric J2000 |
| **Regularized** | Close encounters | KS coordinates |

```python
# Enable multi-coordinate output
config['coordinate_systems'] = ['rotating', 'inertial', 'regularized']

# Access different frames
with h5py.File(orbit_file, 'r') as f:
    # Rotating frame (standard for CR3BP)
    q_rot = f['trajectory']['rotating']['positions'][:]

    # Inertial frame (for visualization)
    q_inert = f['trajectory']['inertial']['positions'][:]

    # KS regularized (if close encounters detected)
    if 'regularized' in f['trajectory']:
        u_ks = f['trajectory']['regularized']['u'][:]
```

## Downstream Data Flow

### WP2: Geometric Foundations

```python
# WP2 consumes rotating frame trajectories for lift construction
from src.python.lifts.s1_bundle import S1Bundle

# Load trajectory
df = pd.read_parquet('data/tier1/parquet/catalogue.parquet')
orbit = df[df['orbit_id'] == 42].iloc[0]

# Construct S¹ lift
bundle = S1Bundle(mu=orbit['mu'])
lifted = bundle.lift(orbit['trajectory'])
```

### WP3: ML Discovery

```python
# WP3 uses Parquet format for efficient ML training
import pandas as pd

# Load regular orbits only (filter chaotic)
df = pd.read_parquet('data/tier1/parquet/catalogue.parquet')
training_data = df[df['classification'] == 'regular']

# Build ML dataset
from src.python.ml.dataset_builder import DatasetBuilder
builder = DatasetBuilder(trajectories=training_data)
X_train, y_train = builder.build(target='conservation')
```

### WP4: Validation

```python
# WP4 uses Tier 2 data for rigorous validation
tier2_orbits = pd.read_parquet('data/tier2/parquet/catalogue.parquet')

# Select periodic orbits for Morales-Ramis
periodic = tier2_orbits[tier2_orbits['is_periodic'] == True]

from src.python.validation.morales_ramis_validator import MoralesRamisValidator
validator = MoralesRamisValidator(mu=periodic.iloc[0]['mu'])
```

## Monitoring and Logging

### Real-time Monitoring

```bash
# Watch Snakemake progress
snakemake tier1_complete --cores 8 --stats stats.json

# Monitor resource usage
htop  # or nvidia-smi for GPU

# Tail latest log
tail -f .snakemake/log/*.snakemake.log

# Check job status (SLURM)
squeue -u $USER | grep smk
sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS
```

### Progress Dashboard

```python
# scripts/monitor_progress.py
import json
from pathlib import Path

def check_progress(tier='tier1'):
    """Check catalogue generation progress."""
    config = load_config()
    expected = config[f'n_samples_{tier}']

    completed = len(list(Path(f'data/{tier}/hdf5').glob('*.h5')))
    failed = len(list(Path(f'logs/integrate').glob('*.err')))

    print(f"Progress: {completed}/{expected} ({100*completed/expected:.1f}%)")
    print(f"Failed: {failed}")

    return completed, expected, failed
```

## Error Handling and Recovery

### Common Failures

| Error | Cause | Solution |
|-------|-------|----------|
| `Integration timeout` | Close encounter | Enable automatic KS switching |
| `NaN in trajectory` | Escape/collision | Filter extreme parameters |
| `Memory error` | Large trajectory | Reduce `n_periods` or chunk output |
| `Jacobi drift > threshold` | Precision loss | Promote to Tier 2 |

### Recovery Workflow

```bash
# 1. Identify failed jobs
snakemake --list-incomplete

# 2. Check failure logs
cat logs/integrate_orbit/orbit_*_failed.err

# 3. Re-run with adjusted parameters
snakemake tier1_complete --cores 8 \
  --rerun-incomplete \
  --config max_steps=20000000  # More steps for hard orbits

# 4. Quarantine persistent failures
python scripts/quarantine_failures.py --tier tier1
```

### Automatic Retry

```python
# In Snakefile
rule integrate_orbit:
    retries: 3
    resources:
        attempt=lambda wildcards, attempt: attempt
    params:
        tol=lambda wildcards, attempt: 1e-14 / (10 ** attempt)  # Tighter on retry
```

## Performance Optimization

### Memory Management

```python
# For large catalogues, use chunked processing
import h5py

def aggregate_chunked(orbit_files, output_file, chunk_size=1000):
    """Aggregate orbits in chunks to limit memory."""
    with h5py.File(output_file, 'w') as out:
        for i in range(0, len(orbit_files), chunk_size):
            chunk = orbit_files[i:i+chunk_size]
            data = [load_orbit(f) for f in chunk]
            write_chunk(out, data, offset=i)
            del data  # Free memory
```

### I/O Optimization

```bash
# Use local scratch for intermediate files (HPC)
export TMPDIR=/scratch/$USER/snakemake_tmp

# Enable compression for HDF5
config['hdf5_compression'] = 'gzip'
config['hdf5_compression_opts'] = 4

# Use Parquet row groups for parallel reads
config['parquet_row_group_size'] = 10000
```

### Parallel Tuning

```yaml
# Optimal settings for different cluster sizes
# Small (8-16 cores): jobs=8, group_components=1
# Medium (64 cores): jobs=32, group_components=4
# Large (256+ cores): jobs=100, group_components=10

snakemake tier1_complete --profile slurm \
  --jobs 100 \
  --group-components integrate=10
```

## Poincaré Section Mode

Store only Poincaré crossings (not full trajectory) for ~100x smaller files:

```python
from src.python.utils.poincare import PoincareSection

# Define y=0, vy>0 section
section = PoincareSection.create_standard_section('y_zero', mu=mu)

# Configure pipeline for Poincaré mode
config['output_mode'] = 'poincare'
config['poincare_section'] = 'y_zero'

# Output schema (much smaller)
# /crossings
#   ├── times: (M,) float64
#   ├── states: (M, 6) float64
#   └── crossing_indices: (M,) int64
```

## Tests

```bash
# Pipeline component tests
pytest tests/test_pipeline.py -v

# Sobol sampling tests
pytest tests/ml/test_sobol_sampling.py -v

# Data export tests
pytest tests/ml/test_parquet_export.py -v

# Integration tests (slow)
pytest tests/integration/test_full_pipeline.py -v -m "not slow"
```

## Troubleshooting

See `references/troubleshooting.md` for detailed solutions.

**Quick fixes:**

```bash
# Unlock after crash
snakemake --unlock

# Clear incomplete outputs
snakemake --delete-all-output

# Check why rule will run
snakemake -n --reason <target>

# Dry run with debug output
snakemake -n --debug-dag
```

## References

- `references/tier-configuration.md` - Precision tier details
- `references/configuration-guide.md` - All Snakefile parameters
- `references/hpc-configuration.md` - SLURM/PBS setup
- `references/data-schema.md` - Complete HDF5/Parquet schemas
- `references/troubleshooting.md` - Error solutions
- `Snakefile` - Pipeline definition
- `src/python/ml/sobol_sampling.py` - Sampling implementation
- `src/python/ml/parquet_export.py` - Export utilities
- `benchmarks/cr3bp_smoke.yaml` - Performance benchmarks
