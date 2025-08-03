# Technical Environment Documentation

## System Architecture Overview

This project uses a **dual-layer dependency management system** designed for reproducible scientific computing:

1. **System Layer (Conda/Mamba)**: Manages compilers, system libraries, and build tools
2. **Application Layer (Poetry)**: Manages Python packages with exact version locking

This architecture ensures perfect reproducibility across different operating systems and hardware configurations.

## Prerequisites

### Required Software
- **Git**: Version control (verify with `git --version`)
- **Mamba/Conda**: Environment management
  - Recommended: [Mambaforge](https://github.com/conda-forge/miniforge) (faster than conda)
  - Alternative: Miniconda or Anaconda

### Supported Platforms
- **macOS**: ARM64 (Apple Silicon) and x86_64 (Intel)
- **Linux**: x86_64, ARM64
- **Windows**: x86_64 (via WSL2 recommended)

## Installation Guide

### Step 1: Environment Creation

```bash
# Clone the repository
git clone git@github.com:jacobrsullivan/3body.git
cd 3body

# Create the conda environment from specification
mamba env create -f environment.yml

# Activate the environment
mamba activate wp1_env
```

### Step 2: Python Dependencies

```bash
# Install Python packages from lock file
poetry install --no-root

# Alternative: Install with the project package
poetry install
```

### Step 3: Development Tools Setup

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Verify installation
python verify_setup.py
```

## Environment Specification

### System Dependencies (`environment.yml`)

```yaml
name: wp1_env
channels:
  - conda-forge
dependencies:
  - python=3.11         # Latest stable Python
  - poetry             # Python dependency management
  - compilers          # C/C++/Fortran compilers (crucial!)
  - cmake              # Build system generator
  - make               # Build automation
  - pybind11           # Python-C++ binding
  - git                # Version control
  - curl               # HTTP client
  - wget               # File downloader
```

**Critical Note**: The `compilers` package ensures we use **conda-provided compilers** rather than system compilers, guaranteeing:
- Binary compatibility across environments
- Reproducible builds
- Consistent toolchain versions

### Python Dependencies (`pyproject.toml`)

#### Core Scientific Stack
```toml
numpy = ">=1.24,<2.3"    # Numerical arrays (constrained for numba)
scipy = "^1.16.1"        # Scientific computing
matplotlib = "^3.10.5"   # Plotting and visualization
numba = ">=0.59"         # JIT compilation for performance
h5py = "^3.14.0"         # HDF5 file format (large datasets)
pyarrow = "^21.0.0"      # Parquet files (tabular data)
rebound = "^4.4.10"      # N-body simulation baseline
```

#### Development Tools
```toml
pytest = "^8.4.1"        # Testing framework
jupyterlab = "^4.4.5"    # Interactive notebooks

[tool.poetry.group.dev.dependencies]
black = "^25.1.0"        # Code formatting
flake8 = "^7.3.0"        # Linting and style checking
pre-commit = "^4.2.0"    # Git hooks automation
mypy = "^1.17.1"         # Static type checking
```

## Compiler Configuration

### macOS (Clang-based)
```bash
# Verify conda compilers are active
which clang++   # Should show: /path/to/miniconda3/envs/wp1_env/bin/clang++
which clang     # Should show: /path/to/miniconda3/envs/wp1_env/bin/clang

# Available compilers
clang --version     # C compiler
clang++ --version   # C++ compiler
gfortran --version  # Fortran compiler
```

### Linux (GCC-based)
```bash
# Verify conda compilers are active
which g++      # Should show: /path/to/miniconda3/envs/wp1_env/bin/g++
which gcc      # Should show: /path/to/miniconda3/envs/wp1_env/bin/gcc

# Available compilers
gcc --version      # C compiler
g++ --version      # C++ compiler
gfortran --version # Fortran compiler
```

## Package Version Resolution

### NumPy-Numba Compatibility Issue

**Problem**: Initial Poetry resolution failed due to version conflicts:
- `numpy ^2.3.2` (≥2.3.2, <3.0.0)
- `numba 0.61.2` requires `numpy >=1.24,<2.3`

**Solution**: Constrained numpy to compatible range:
```toml
numpy = ">=1.24,<2.3"  # Compatible with numba
numba = ">=0.59"       # Flexible numba version
```

**Result**:
- numpy 2.2.6 (recent, stable, compatible)
- numba 0.61.2 (JIT compilation enabled)
- llvmlite 0.44.0 (numba's compiler backend)

## Development Workflow

### Code Quality Pipeline

1. **Pre-commit Hooks** (automatic on `git commit`):
   ```bash
   - trailing-whitespace    # Remove trailing spaces
   - end-of-file-fixer     # Ensure files end with newline
   - check-yaml            # Validate YAML syntax
   - check-added-large-files # Prevent large file commits
   - black                 # Code formatting
   - flake8               # Style and error checking
   ```

2. **Manual Quality Checks**:
   ```bash
   # Run all pre-commit hooks manually
   poetry run pre-commit run --all-files

   # Type checking
   poetry run mypy src/

   # Testing
   poetry run pytest tests/
   ```

### Environment Management Commands

```bash
# List all conda environments
mamba env list

# Update environment from file
mamba env update -f environment.yml

# Export current environment
mamba env export > environment-exact.yml

# Remove environment
mamba env remove -n wp1_env

# Poetry commands
poetry show                    # List installed packages
poetry add <package>          # Add new dependency
poetry remove <package>       # Remove dependency
poetry update                 # Update all packages
poetry lock                   # Regenerate lock file
```

## File System Structure

```
3body/
├── environment.yml           # Conda environment specification
├── pyproject.toml           # Poetry configuration & dependencies
├── poetry.lock              # Exact dependency versions (auto-generated)
├── .pre-commit-config.yaml  # Code quality automation
├── .gitignore              # Git exclusion rules
├── README.md               # User-facing documentation
├── TechnicalReadme.md      # This file
├── verify_setup.py         # Environment verification script
├── src/
│   ├── cpp/                # High-precision C++ implementations
│   └── python/             # Python interface and analysis
├── tests/                  # Automated test suite
├── notebooks/              # Jupyter analysis notebooks
└── docs/                   # Additional documentation
```

## Verification and Troubleshooting

### Environment Verification

Run the comprehensive verification script:
```bash
python verify_setup.py
```

**Expected Output**:
```
Day 1 Setup Verification
==============================
Python version: 3.11.13
✓ Python version OK
✓ numpy 2.2.6 imported successfully
✓ scipy 1.16.1 imported successfully
✓ matplotlib 3.10.5 imported successfully
✓ rebound 4.4.10 imported successfully
✓ pytest 8.4.1 imported successfully
✓ numba 0.61.2 imported successfully
✓ h5py 3.14.0 imported successfully
✓ pyarrow 21.0.0 imported successfully
clang++ location: /Users/jacobsullivan/miniconda3/envs/wp1_env/bin/clang++
✓ Conda compilers active
✓ pyproject.toml found
✓ poetry.lock found (dependencies locked)
✓ Git repository initialized
✓ .gitignore file exists

🎉 All checks passed! Day 1 setup complete.
```

### Common Issues and Solutions

#### 1. "Mamba command not found"
```bash
# Solution 1: Restart terminal after mamba installation
source ~/.bashrc  # Linux
source ~/.zshrc   # macOS with zsh

# Solution 2: Use conda instead
conda env create -f environment.yml
```

#### 2. "Wrong compiler paths"
```bash
# Check if compilers package is installed
mamba list compilers

# Reinstall if necessary
mamba install compilers -c conda-forge --force-reinstall

# Deactivate and reactivate environment
mamba deactivate
mamba activate wp1_env
```

#### 3. "Poetry not found"
```bash
# Ensure environment is active
mamba activate wp1_env

# Verify poetry is installed in environment
mamba list poetry
```

#### 4. "Permission denied (publickey)" - Git SSH
```bash
# Test SSH connection
ssh -T git@github.com

# If fails, check SSH key
ssh-add -l

# Or use HTTPS instead
git remote set-url origin https://github.com/jacobrsullivan/3body.git
```

#### 5. "Pre-commit hooks not running"
```bash
# Reinstall hooks
poetry run pre-commit install

# Run manually to test
poetry run pre-commit run --all-files
```

## Performance Considerations

### Numba JIT Compilation
- **First run**: Compilation overhead (slow)
- **Subsequent runs**: Machine code execution (fast)
- **Caching**: Compiled functions cached between sessions

### Memory Management
- **HDF5 (h5py)**: Efficient for large numerical datasets
- **Parquet (pyarrow)**: Columnar storage for tabular data
- **NumPy**: Memory-mapped arrays for large datasets

### Build Optimization
```bash
# For production builds, set optimization flags
export CXXFLAGS="-O3 -march=native"
export CFLAGS="-O3 -march=native"
```

## Reproducibility Features

### Exact Version Locking
- **poetry.lock**: Records exact versions of ALL dependencies
- **Dependency resolution**: Consistent across machines
- **Security**: Prevents supply chain attacks

### Cross-Platform Consistency
- **Conda compilers**: Same toolchain across OS
- **Binary compatibility**: Consistent library versions
- **Environment specification**: Declarative configuration

### CI/CD Integration
Environment can be reproduced in:
- GitHub Actions
- GitLab CI
- Docker containers
- HPC clusters

## Security Considerations

### Dependency Management
- **Lock file verification**: Ensures integrity
- **Trusted channels**: conda-forge and PyPI
- **No system modifications**: Isolated environment

### Compiler Security
- **Conda toolchain**: Vetted compiler packages
- **No privileged operations**: User-space only
- **Reproducible builds**: Prevents backdoor injection

## Future Extensions

### Day 3+ Additions
- **QD Library**: High-precision arithmetic (quad-double)
- **Custom C++ modules**: pybind11 integration
- **CUDA support**: GPU acceleration (optional)
- **MPI**: Parallel computing (cluster deployment)

### Monitoring and Profiling
- **Line profiler**: Performance bottleneck identification
- **Memory profiler**: Memory usage optimization
- **Numba profiling**: JIT compilation analysis

This technical documentation ensures that any team member can reproduce the exact development environment and understand the underlying architecture decisions.
