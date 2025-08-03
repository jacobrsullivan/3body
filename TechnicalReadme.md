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
├── verify_qd               # QD library verification executable
├── src/
│   ├── cpp/                # High-precision C++ implementations
│   │   └── verify_qd.cpp   # QD library verification program
│   └── python/             # Python interface and analysis
├── tests/                  # Automated test suite
├── notebooks/              # Jupyter analysis notebooks
├── docs/                   # Additional documentation
│   └── Explanation_DoubleDoubleArithmetic.md  # DD arithmetic explanation
└── build_external/         # External library compilation
    ├── v2.3.24.tar.gz      # QD library source archive
    └── QD-2.3.24/          # QD library source code
        ├── src/            # Compiled QD library source
        ├── include/        # QD header files
        └── configure       # Generated build configuration
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

#### 6. "autoreconf: command not found" - QD Library Build
```bash
# Install autotools in conda environment
mamba install -n wp1_env autoconf automake libtool -c conda-forge -y

# Verify installation
mamba run -n wp1_env which autoreconf
```

#### 7. "qd/dd_real.h: No such file or directory"
```bash
# Verify QD headers are installed
mamba run -n wp1_env ls $CONDA_PREFIX/include/qd/

# Compile with proper include path
mamba run -n wp1_env clang++ -I$CONDA_PREFIX/include -L$CONDA_PREFIX/lib -o verify_qd src/cpp/verify_qd.cpp -lqd
```

#### 8. "Library not loaded" - QD Runtime Linking (macOS)
```bash
# Set library path for runtime linking
mamba run -n wp1_env bash -c 'DYLD_LIBRARY_PATH=$CONDA_PREFIX/lib:$DYLD_LIBRARY_PATH ./verify_qd'

# For Linux, use LD_LIBRARY_PATH instead
mamba run -n wp1_env bash -c 'LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH ./verify_qd'
```

#### 9. "make: *** [docs/qd.pdf] Error 2" - Documentation Build
```bash
# Skip documentation build and compile only library
mamba run -n wp1_env make -C src  # Compile library only
mamba run -n wp1_env make install -C src  # Install library only

# Documentation requires LaTeX which is not needed for library functionality
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

## High-Precision Arithmetic (Day 3 Implementation)

### QD Library Installation and Configuration

The QD (Quad-Double) Library provides double-double (~31 digits) and quad-double (~62 digits) precision arithmetic, essential for high-fidelity orbital simulations in the three-body problem.

#### Installation Process

```bash
# Step 1: Install autotools dependencies
mamba install -n wp1_env autoconf automake libtool -c conda-forge -y

# Step 2: Download and extract QD Library
cd build_external
curl -L -O https://github.com/BL-highprecision/QD/archive/refs/tags/v2.3.24.tar.gz
tar -xzf v2.3.24.tar.gz
cd QD-2.3.24

# Step 3: Generate configure script and build
mamba run -n wp1_env autoreconf -fi
mamba run -n wp1_env bash -c '
export CXX=$(which clang++)
export CC=$(which clang)
./configure --prefix=$CONDA_PREFIX CXXFLAGS="-O3 -march=native"
'

# Step 4: Compile and install
mamba run -n wp1_env make -C src
mamba run -n wp1_env make install -C src
mamba run -n wp1_env make install -C include
```

#### Verification

A C++ verification program confirms the library installation:

```cpp
#include <iostream>
#include <iomanip>
#include <qd/dd_real.h>

int main() {
    dd_real pi = "3.1415926535897932384626433832795028841971693993751";
    std::cout << std::fixed << std::setprecision(35);
    std::cout << "QD Pi: " << pi << std::endl;
    return 0;
}
```

**Compilation and execution:**
```bash
mamba run -n wp1_env bash -c '
clang++ -I$CONDA_PREFIX/include -L$CONDA_PREFIX/lib -o verify_qd src/cpp/verify_qd.cpp -lqd
DYLD_LIBRARY_PATH=$CONDA_PREFIX/lib:$DYLD_LIBRARY_PATH ./verify_qd
'
```

**Expected output:** Pi displayed to 37 digits precision
```
QD Pi: 3.14159265358979323846264338327950588
```

#### Implementation Details

**Library Components:**
- **libqd.dylib/libqd.a**: Shared/static libraries installed in `$CONDA_PREFIX/lib`
- **Headers**: Installed in `$CONDA_PREFIX/include/qd/`
- **Core types**: `dd_real` (double-double), `qd_real` (quad-double)

**Compiler Configuration:**
```bash
# Conda compilers used (ensures reproducibility)
CC=/path/to/conda/envs/wp1_env/bin/clang
CXX=/path/to/conda/envs/wp1_env/bin/clang++

# Optimization flags applied
CXXFLAGS="-O3 -march=native -DHAVE_CONFIG_H"

# Installation prefix
--prefix=$CONDA_PREFIX  # Isolated to conda environment
```

**Platform-Specific Notes:**
- **macOS**: Uses clang/clang++ compilers, requires `DYLD_LIBRARY_PATH` for runtime linking
- **Linux**: Uses gcc/g++ compilers, requires `LD_LIBRARY_PATH` for runtime linking

#### Precision Capabilities

| Type | Mantissa Bits | Decimal Digits | Use Case |
|------|---------------|----------------|----------|
| `double` | 53 | ~16 | Standard precision (insufficient for WP1) |
| `dd_real` | 106 | ~31 | Double-double (primary for WP1) |
| `qd_real` | 212 | ~62 | Quad-double (research/validation) |

#### Integration with Python (Future)

The QD library will be exposed to Python via pybind11:
```cpp
#include <pybind11/pybind11.h>
#include <qd/dd_real.h>

PYBIND11_MODULE(qd_python, m) {
    pybind11::class_<dd_real>(m, "dd_real")
        .def(pybind11::init<double>())
        .def("__str__", [](const dd_real &a) {
            return a.to_string(31);
        });
}
```

## Future Extensions

### Upcoming Implementations
- **pybind11 QD Bindings**: Python interface for high-precision arithmetic
- **High-precision integrators**: Custom CR3BP solvers using dd_real
- **CUDA support**: GPU acceleration for parallel simulations (optional)
- **MPI**: Distributed computing for large parameter studies

### Monitoring and Profiling
- **Line profiler**: Performance bottleneck identification
- **Memory profiler**: Memory usage optimization
- **Numba profiling**: JIT compilation analysis
- **QD performance analysis**: Double-double vs quad-double benchmarks

This technical documentation ensures that any team member can reproduce the exact development environment and understand the underlying architecture decisions.
