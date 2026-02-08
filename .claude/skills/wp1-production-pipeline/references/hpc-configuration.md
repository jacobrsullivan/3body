# HPC Configuration Reference

Detailed configuration for running the production pipeline on HPC clusters with SLURM, PBS, or other job schedulers.

## Table of Contents

1. [Cluster Profile Setup](#cluster-profile-setup)
2. [SLURM Configuration](#slurm-configuration)
3. [PBS Configuration](#pbs-configuration)
4. [Resource Management](#resource-management)
5. [Job Grouping](#job-grouping)
6. [Monitoring and Debugging](#monitoring-and-debugging)

---

## Cluster Profile Setup

Snakemake uses profiles to configure cluster submission. Create a profile directory:

```bash
mkdir -p ~/.config/snakemake/slurm
mkdir -p ~/.config/snakemake/pbs
```

---

## SLURM Configuration

### Basic Profile

Create `~/.config/snakemake/slurm/config.yaml`:

```yaml
# Cluster submission command
cluster:
  mkdir -p logs/{rule} &&
  sbatch
    --partition={resources.partition}
    --cpus-per-task={threads}
    --mem={resources.mem_mb}M
    --time={resources.runtime}
    --job-name=smk-{rule}-{wildcards}
    --output=logs/{rule}/{rule}-{wildcards}-%j.out
    --error=logs/{rule}/{rule}-{wildcards}-%j.err
    --parsable

# Status check command
cluster-status: status-sacct.sh

# Cancel command
cluster-cancel: scancel

# Default resources (applied to all rules)
default-resources:
  - partition=normal
  - mem_mb=4000
  - runtime=60

# Rule-specific resources
set-resources:
  # Integration is memory-intensive
  - integrate_orbit:mem_mb=8000
  - integrate_orbit:runtime=120
  - integrate_orbit:partition=normal
  
  # Tier 2 needs more time
  - integrate_orbit_tier2:mem_mb=16000
  - integrate_orbit_tier2:runtime=480
  - integrate_orbit_tier2:partition=long
  
  # Chaos analysis
  - chaos_analysis:mem_mb=4000
  - chaos_analysis:runtime=60
  
  # Aggregation needs lots of memory
  - aggregate_catalogue:mem_mb=64000
  - aggregate_catalogue:runtime=120
  - aggregate_catalogue:partition=himem

# Thread settings
set-threads:
  - integrate_orbit:1
  - chaos_analysis:1
  - aggregate_catalogue:4

# Maximum concurrent jobs
jobs: 100

# Latency wait (seconds between status checks)
latency-wait: 60

# Restart failed jobs
restart-times: 2

# Local rules (don't submit to cluster)
local-cores: 4
localrules: clean, all
```

### Job Status Script

Create `~/.config/snakemake/slurm/status-sacct.sh`:

```bash
#!/bin/bash
# Check SLURM job status for Snakemake

jobid="$1"

if [[ -z "$jobid" ]]; then
    echo "Usage: $0 <jobid>"
    exit 1
fi

# Query sacct for job state
state=$(sacct -j "$jobid" --format=State --noheader | head -1 | awk '{print $1}')

if [[ -z "$state" ]]; then
    # Job not found in sacct, check squeue
    state=$(squeue -j "$jobid" -h -o "%T" 2>/dev/null)
fi

case "$state" in
    COMPLETED)
        echo "success"
        ;;
    RUNNING|PENDING|CONFIGURING|COMPLETING|RESIZING|SUSPENDED)
        echo "running"
        ;;
    FAILED|TIMEOUT|CANCELLED|NODE_FAIL|PREEMPTED|OUT_OF_MEMORY)
        echo "failed"
        ;;
    *)
        echo "running"  # Default to running for unknown states
        ;;
esac
```

Make it executable:
```bash
chmod +x ~/.config/snakemake/slurm/status-sacct.sh
```

### Advanced SLURM Options

```yaml
# For GPU-enabled nodes (if using CUDA)
set-resources:
  - ml_training:gres=gpu:1
  - ml_training:partition=gpu

# For high-memory nodes
set-resources:
  - aggregate_catalogue:partition=himem
  - aggregate_catalogue:mem_mb=128000

# For long-running jobs
set-resources:
  - tier2_complete:runtime=2880  # 48 hours
  - tier2_complete:partition=long

# Array jobs for large batches
cluster:
  sbatch
    --array=1-{params.batch_size}%50  # 50 concurrent
    ...
```

---

## PBS Configuration

### Basic Profile

Create `~/.config/snakemake/pbs/config.yaml`:

```yaml
cluster:
  mkdir -p logs/{rule} &&
  qsub
    -q {resources.queue}
    -l nodes=1:ppn={threads}
    -l mem={resources.mem_mb}mb
    -l walltime={resources.walltime}
    -N smk-{rule}
    -o logs/{rule}/{rule}-{wildcards}.out
    -e logs/{rule}/{rule}-{wildcards}.err

cluster-status: status-qstat.sh

default-resources:
  - queue=batch
  - mem_mb=4000
  - walltime=01:00:00

set-resources:
  - integrate_orbit:mem_mb=8000
  - integrate_orbit:walltime=02:00:00
  - aggregate_catalogue:mem_mb=64000
  - aggregate_catalogue:queue=himem

jobs: 100
latency-wait: 60
```

### PBS Status Script

Create `~/.config/snakemake/pbs/status-qstat.sh`:

```bash
#!/bin/bash
jobid="$1"
state=$(qstat -f "$jobid" 2>/dev/null | grep "job_state" | awk '{print $3}')

case "$state" in
    C)  echo "success" ;;
    R|Q|H|W|S)  echo "running" ;;
    *)  echo "failed" ;;
esac
```

---

## Resource Management

### Memory Estimation

```python
# Rule of thumb for memory requirements
def estimate_memory(n_periods, precision='double'):
    """Estimate memory in MB for orbit integration."""
    # Base: 8 bytes per double, 6 state variables
    bytes_per_step = 8 * 6
    
    # Timesteps: ~100 per period
    n_steps = n_periods * 100
    
    # Buffer factor
    buffer = 3.0
    
    # QD needs 2x memory
    if precision == 'qd':
        buffer *= 2
    
    memory_mb = (bytes_per_step * n_steps * buffer) / (1024 * 1024)
    
    # Minimum 2GB, add overhead
    return max(2000, int(memory_mb) + 1000)

# Examples:
# 100 periods, double: ~2000 MB
# 100 periods, QD: ~4000 MB
# 1000 periods, QD: ~8000 MB
```

### Runtime Estimation

```python
def estimate_runtime(n_periods, tier='tier1'):
    """Estimate runtime in minutes."""
    # Base rates (periods per minute)
    rates = {
        'tier1': 3000,  # ~50 periods/second
        'tier2': 300,   # ~5 periods/second
    }
    
    minutes = n_periods / rates[tier]
    
    # Add overhead and safety factor
    return int(minutes * 2) + 5
```

### Dynamic Resource Allocation

In Snakefile:

```python
def get_mem_mb(wildcards, attempt):
    """Increase memory on retry."""
    base = 4000
    return base * (2 ** (attempt - 1))

def get_runtime(wildcards, attempt):
    """Increase runtime on retry."""
    base = 60
    return base * (2 ** (attempt - 1))

rule integrate_orbit:
    resources:
        mem_mb=get_mem_mb,
        runtime=get_runtime,
        attempt=lambda wildcards, attempt: attempt
    retries: 3
```

---

## Job Grouping

For large catalogues, reduce scheduler overhead by grouping jobs:

### Group by Parameter

```bash
# Group 10 integrations per job submission
snakemake tier1_complete --profile slurm \
  --group-components integrate_orbit=10

# Group chaos analysis (fast jobs)
snakemake tier1_complete --profile slurm \
  --group-components chaos_analysis=50
```

### Batch Processing Rule

```python
# Snakefile: Process orbits in batches
rule integrate_batch:
    input:
        params=expand("params/tier1/batch_{batch}.parquet",
                     batch=range(N_BATCHES))
    output:
        trajectories=expand("trajectories/tier1/batch_{batch}.h5",
                           batch=range(N_BATCHES))
    params:
        orbits_per_batch=1000
    resources:
        mem_mb=16000,
        runtime=240
    script:
        "scripts/integrate_batch.py"
```

---

## Monitoring and Debugging

### SLURM Monitoring Commands

```bash
# Check queue status
squeue -u $USER

# Detailed job info
scontrol show job <jobid>

# Job accounting
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,MaxRSS,ExitCode

# Node status
sinfo -N -l

# Cancel all pipeline jobs
scancel -u $USER -n "smk-*"

# Cancel specific rule jobs
scancel -u $USER -n "smk-integrate*"
```

### Real-time Monitoring

```bash
# Watch job queue
watch -n 30 'squeue -u $USER | head -50'

# Monitor node usage
watch -n 60 'sinfo -N -l | grep -v idle'

# Tail latest Snakemake log
tail -f .snakemake/log/*.snakemake.log
```

### Debugging Failed Jobs

```bash
# List failed jobs
sacct -u $USER --state=FAILED --starttime=today

# Check error output
cat logs/integrate_orbit/integrate_orbit-mu0.01_C3.0_00042-12345.err

# Check memory usage (did it OOM?)
sacct -j <jobid> --format=JobID,MaxRSS,MaxVMSize,State

# Check time limit (did it timeout?)
sacct -j <jobid> --format=JobID,Elapsed,Timelimit,State
```

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Jobs pending indefinitely | Resource request too high | Reduce mem/time |
| Jobs fail immediately | Module not loaded | Add to cluster command |
| Out of memory | Underestimated memory | Increase `mem_mb` |
| Timeout | Long orbit integration | Increase `runtime` or tier |
| Node failure | Hardware issue | Enable `--rerun-incomplete` |

### Cluster Environment Setup

Add to cluster submission command:

```yaml
cluster:
  sbatch
    ...
    --export=ALL  # Export environment
```

Or use a wrapper script:

```bash
#!/bin/bash
# cluster_submit.sh

# Load required modules
module load python/3.11
module load hdf5
module load gcc

# Activate conda
source ~/miniconda3/etc/profile.d/conda.sh
conda activate wp1_env

# Submit job
sbatch "$@"
```

---

## Performance Tuning

### I/O Optimization

```bash
# Use local scratch for intermediate files
export SNAKEMAKE_OUTPUT_CACHE=/scratch/$USER/snakemake_cache

# In Snakefile:
config['tmp_dir'] = os.environ.get('TMPDIR', '/tmp')
```

### Network Filesystem Issues

```yaml
# Increase latency wait for slow NFS
latency-wait: 120

# Use shadow directory for local work
shadow: "shallow"  # or "full" for complete isolation
```

### Optimal Job Sizes

```
Cluster size recommendations:

Small cluster (< 100 cores):
  - jobs: 20
  - group_components: 5
  - Focus on Tier 1

Medium cluster (100-500 cores):
  - jobs: 100
  - group_components: 10
  - Both tiers feasible

Large cluster (> 500 cores):
  - jobs: 500
  - group_components: 20
  - Full catalogue in < 1 day
```
