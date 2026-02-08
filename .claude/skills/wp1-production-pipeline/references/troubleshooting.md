# Troubleshooting Guide

Solutions for common issues encountered when running the production pipeline.

## Table of Contents

1. [Snakemake Issues](#snakemake-issues)
2. [Integration Failures](#integration-failures)
3. [Precision Problems](#precision-problems)
4. [I/O and Storage Issues](#io-and-storage-issues)
5. [HPC/Cluster Issues](#hpccluster-issues)
6. [Memory Issues](#memory-issues)
7. [Performance Issues](#performance-issues)

---

## Snakemake Issues

### Directory Locked

**Symptom:**
```
Error: Directory cannot be locked. Please make sure that no other
Snakemake process is using this directory.
```

**Solution:**
```bash
# Unlock the directory
snakemake --unlock

# If that fails, manually remove lock
rm -rf .snakemake/locks/
```

### Incomplete Files Blocking Re-run

**Symptom:**
```
Error: Output file exists but is incomplete
```

**Solution:**
```bash
# List incomplete files
snakemake --list-incomplete

# Re-run with incomplete flag
snakemake tier1_complete --cores 8 --rerun-incomplete

# Or force re-run of specific rule
snakemake --forcerun integrate_orbit --cores 8
```

### DAG Too Large

**Symptom:**
```
Error: Too many jobs in DAG (> 100000)
```

**Solution:**
```bash
# Use batch mode to reduce DAG size
snakemake tier1_complete --cores 8 --batch integrate_orbit=1/100

# Or use job grouping
snakemake tier1_complete --cores 8 --group-components integrate_orbit=100
```

### Rule Not Found

**Symptom:**
```
WorkflowError: Target rules are ambiguous
```

**Solution:**
```bash
# List available rules
snakemake --list

# Check Snakefile syntax
snakemake --lint

# Specify exact target
snakemake data/tier1/hdf5/orbit_mu0.01_C3.0_00001.h5 --cores 1
```

---

## Integration Failures

### NaN in Trajectory

**Symptom:**
```
Warning: NaN detected in trajectory at t=XX.XX
```

**Causes:**
- Close encounter/collision
- Escape to infinity
- Numerical overflow

**Solutions:**
```python
# 1. Enable automatic regularization switching
config['enable_regularization'] = True
config['regularization_threshold'] = 0.01  # Switch when r < 0.01

# 2. Filter extreme initial conditions
def filter_safe_ics(samples, mu):
    safe = []
    for s in samples:
        x, y, z = s[:3]
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        if r1 > 0.05 and r2 > 0.05:  # Not too close
            safe.append(s)
    return safe

# 3. Use escape detection
config['escape_radius'] = 10.0
config['terminate_on_escape'] = True
```

### Integration Timeout

**Symptom:**
```
Error: Integration exceeded maximum steps (10000000)
```

**Causes:**
- Very chaotic orbit requiring tiny timesteps
- Close encounter without regularization
- Stuck in numerical loop

**Solutions:**
```python
# 1. Increase max steps
config['max_steps'] = 50000000

# 2. Promote to Tier 2 (with regularization)
def should_promote(initial_result):
    if initial_result.get('timeout', False):
        return True
    return False

# 3. Skip problematic orbits
config['skip_on_timeout'] = True
config['max_retries'] = 3
```

### Integrator Convergence Failure

**Symptom:**
```
Error: Integrator failed to converge at t=XX.XX
```

**Solutions:**
```python
# 1. Use more robust integrator
config['integrator'] = 'adaptive_symplectic'
config['integrator_kwargs']['fallback'] = 'ias15'

# 2. Reduce tolerance (more steps)
config['tier1_tol'] = 1e-15  # Stricter than default

# 3. Enable step doubling
config['integrator_kwargs']['step_control'] = 'doubling'
```

---

## Precision Problems

### Jacobi Drift Too Large

**Symptom:**
```
Warning: Jacobi drift 1.23e-12 exceeds threshold 1e-14
```

**Solutions:**
```python
# 1. Reduce timestep
config['dt_output'] = 0.01  # Instead of 0.1

# 2. Promote to Tier 2
orbit['precision_tier'] = 2

# 3. Use symplectic integrator
config['integrator'] = 'yoshida8'

# 4. Check for close encounters
if orbit['min_distance'] < 0.1:
    config['enable_regularization'] = True
```

### Shadow Hamiltonian Drift

**Symptom:**
```
Warning: Shadow Hamiltonian drift rate 5.67e-13 too large
```

**Solutions:**
```python
# 1. Use higher-order integrator
config['integrator_kwargs']['order'] = 8  # Instead of 6

# 2. Reduce timestep
config['integrator_kwargs']['max_dt'] = 0.001

# 3. For chaotic orbits, drift is expected
if orbit['classification'] == 'chaotic':
    # Accept larger drift for chaotic orbits
    threshold = 1e-10
```

### QD Library Precision Not Achieved

**Symptom:**
```
Error: QD arithmetic not achieving expected precision
```

**Solutions:**
```bash
# 1. Verify QD installation
python -c "from src.python.qd_python import dd_real; print(dd_real(1.0)/dd_real(3.0))"

# 2. Check library linking
ldd $(python -c "import src.python.qd_python; print(src.python.qd_python.__file__)")

# 3. Rebuild with correct flags
cd src/cpp && make clean && make PRECISION=qd
```

---

## I/O and Storage Issues

### Disk Full

**Symptom:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**
```bash
# 1. Check disk usage
df -h

# 2. Clean incomplete files
snakemake --delete-incomplete-output

# 3. Use compression
config['hdf5_compression'] = 'gzip'
config['hdf5_compression_opts'] = 9

# 4. Use Poincaré mode (100x smaller)
config['output_mode'] = 'poincare'

# 5. Move to larger filesystem
config['output_dir'] = '/scratch/user/3body/data'
```

### HDF5 Corruption

**Symptom:**
```
OSError: Unable to open file (file signature not found)
```

**Solutions:**
```bash
# 1. Check file integrity
h5dump -H corrupt_file.h5

# 2. Use h5repack to recover
h5repack -f GZIP=4 corrupt_file.h5 recovered_file.h5

# 3. Enable checksums
config['hdf5_fletcher32'] = True

# 4. Re-run affected jobs
snakemake --forcerun integrate_orbit --cores 8
```

### Parquet Write Failure

**Symptom:**
```
pyarrow.lib.ArrowIOError: Failed to write Parquet file
```

**Solutions:**
```python
# 1. Reduce row group size
config['parquet_row_group_size'] = 5000

# 2. Use smaller batches
def write_catalogue_chunked(orbits, output_path, chunk_size=10000):
    for i in range(0, len(orbits), chunk_size):
        chunk = orbits[i:i+chunk_size]
        chunk_path = output_path.replace('.parquet', f'_part{i//chunk_size}.parquet')
        write_parquet(chunk, chunk_path)

# 3. Disable statistics (faster)
config['parquet_write_statistics'] = False
```

---

## HPC/Cluster Issues

### Jobs Pending Forever

**Symptom:**
```
squeue shows jobs in PD (pending) state indefinitely
```

**Solutions:**
```bash
# 1. Check resource requests
squeue -u $USER -o "%.10i %.20j %.8T %.10M %.6D %R"

# 2. Reduce resource requests
# In profile config.yaml:
# default-resources:
#   - mem_mb=2000  # Reduce from 4000

# 3. Use different partition
# In profile config.yaml:
# default-resources:
#   - partition=shared  # Instead of normal

# 4. Check cluster load
sinfo -s
```

### Job Failing Immediately

**Symptom:**
```
Job exits with status 1 immediately after starting
```

**Solutions:**
```bash
# 1. Check error log
cat logs/integrate_orbit/integrate_orbit-*.err

# 2. Verify environment setup
# Add to cluster command:
#   source ~/.bashrc && conda activate wp1_env

# 3. Check module loading
module list

# 4. Test interactively
srun --pty bash
conda activate wp1_env
python -c "from src.python.integrators.ias15 import IAS15Integrator"
```

### Out of Memory on Cluster

**Symptom:**
```
slurmstepd: error: Detected 1 oom-kill events
```

**Solutions:**
```yaml
# 1. Increase memory allocation
set-resources:
  - integrate_orbit:mem_mb=16000

# 2. Use high-memory partition
set-resources:
  - aggregate_catalogue:partition=himem
  - aggregate_catalogue:mem_mb=128000

# 3. Process in smaller batches
# In Snakefile:
params:
    batch_size=100  # Instead of 1000
```

---

## Memory Issues

### Python Out of Memory

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
```python
# 1. Process orbits in chunks
def process_large_catalogue(catalogue_dir, chunk_size=100):
    orbit_files = list(Path(catalogue_dir).glob('*.h5'))
    
    for i in range(0, len(orbit_files), chunk_size):
        chunk = orbit_files[i:i+chunk_size]
        data = [load_orbit(f) for f in chunk]
        process_chunk(data)
        del data  # Explicit cleanup
        gc.collect()

# 2. Use memory-mapped arrays
import numpy as np
mmap_array = np.memmap('large_array.dat', dtype='float64', mode='r', shape=(N, 6))

# 3. Stream processing (don't load full trajectory)
def stream_validate(orbit_file):
    with h5py.File(orbit_file, 'r') as f:
        # Process in chunks
        for i in range(0, len(f['trajectory']['time']), 10000):
            chunk = f['trajectory']['rotating']['positions'][i:i+10000]
            validate_chunk(chunk)
```

### Memory Leak

**Symptom:**
```
Memory usage grows continuously over pipeline run
```

**Solutions:**
```python
# 1. Use subprocess isolation
from multiprocessing import Pool

def process_orbit(args):
    orbit_file, config = args
    # Process in subprocess (memory freed on exit)
    return integrate_orbit(orbit_file, config)

with Pool(8) as pool:
    results = pool.map(process_orbit, orbit_args)

# 2. Force garbage collection
import gc

for i, orbit in enumerate(orbits):
    result = process(orbit)
    if i % 100 == 0:
        gc.collect()

# 3. Check for circular references
import objgraph
objgraph.show_most_common_types(limit=20)
```

---

## Performance Issues

### Slow Integration

**Symptom:**
```
Integration taking >10x expected time
```

**Solutions:**
```python
# 1. Profile the code
import cProfile
cProfile.run('integrate(state0, t_span)', 'profile.stats')

# 2. Check for repeated allocations
# Bad:
for i in range(N):
    result = np.zeros(6)  # Allocates every iteration
    
# Good:
result = np.zeros(6)
for i in range(N):
    result[:] = 0  # Reuse allocation

# 3. Enable Numba JIT
from numba import jit

@jit(nopython=True)
def cr3bp_dynamics(t, state, mu):
    ...

# 4. Use vectorized operations
# Bad:
for i in range(N):
    r = np.sqrt(x[i]**2 + y[i]**2)
    
# Good:
r = np.sqrt(x**2 + y**2)  # Vectorized
```

### Slow I/O

**Symptom:**
```
Most time spent in file read/write
```

**Solutions:**
```bash
# 1. Use local scratch (not network filesystem)
export TMPDIR=/local/scratch/$USER
config['tmp_dir'] = os.environ['TMPDIR']

# 2. Use SSD if available
config['output_dir'] = '/ssd/user/3body/data'

# 3. Batch writes
# Instead of writing each orbit immediately,
# accumulate and write in batches

# 4. Use parallel I/O
config['hdf5_driver'] = 'mpio'  # MPI-IO for parallel HDF5
```

### Poor Parallel Scaling

**Symptom:**
```
Speedup plateaus despite adding more cores
```

**Solutions:**
```bash
# 1. Check for I/O bottleneck
iostat -x 1  # Monitor disk I/O

# 2. Use job grouping (reduce scheduler overhead)
snakemake tier1_complete --cores 64 --group-components integrate_orbit=10

# 3. Check load balance
# Some orbits take much longer - use dynamic scheduling

# 4. Reduce inter-process communication
# Use file-based communication instead of shared memory for large data
```

---

## Quick Reference

### Common Commands

```bash
# Unlock directory
snakemake --unlock

# Resume interrupted run
snakemake tier1_complete --cores 8 --rerun-incomplete

# Force re-run
snakemake tier1_complete --cores 8 --forceall

# Check why rules will run
snakemake -n --reason

# Debug DAG
snakemake --debug-dag

# List incomplete outputs
snakemake --list-incomplete

# Delete all outputs
snakemake --delete-all-output
```

### Diagnostic Commands

```bash
# Check Snakemake logs
tail -f .snakemake/log/*.snakemake.log

# Check job logs (SLURM)
cat logs/integrate_orbit/*.err

# Check resource usage
sacct -j JOBID --format=JobID,MaxRSS,MaxVMSize,Elapsed

# Check disk usage
du -sh data/tier1/

# Count completed orbits
ls data/tier1/hdf5/*.h5 | wc -l
```
