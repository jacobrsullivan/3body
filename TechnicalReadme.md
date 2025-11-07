# Technical Readme - 3body Project

## Project Overview

This is a research codebase for studying the Circular Restricted Three-Body Problem (CR3BP) with high-precision numerical methods, focused on searching for hidden integrability via higher-dimensional symplectic embedding.

## Technical Architecture

### Core Components

#### 1. High-Precision Arithmetic (QD Library)
- **Library**: QD (Quad-Double) library v2.3.24
- **Precision**: ~31 decimal digits using double-double arithmetic
- **Language**: C++ with Python bindings via pybind11
- **Location**: `src/cpp/qd_python_bindings.cpp`
- **Binary**: `qd_python.cpython-311-darwin.so`

#### 2. Numerical Integrators
- **IAS15**: 15th-order adaptive Radau integrator (REBOUND backend)
  - Excellent energy conservation (< 1e-15 relative drift)
  - Adaptive timestep control
  - Location: `src/python/integrators/ias15.py`

- **Yoshida8**: 8th-order symplectic composition integrator
  - Fixed timestep, excellent long-term stability
  - Preserves Hamiltonian structure
  - Location: `src/python/integrators/yoshida8.py`

#### 3. CR3BP Dynamics
- **Equations of Motion**: Full CR3BP with Coriolis and centrifugal terms
- **Conservation**: Jacobi constant calculation and monitoring
- **Coordinate Systems**: Rotating and inertial frame transformations
- **Location**: `src/python/utils/dynamics.py`, `src/python/utils/coordinates.py`

### Build System

#### Python Environment
- **Manager**: Conda (miniconda3) + Poetry
- **Environment**: `wp1_env`
- **Python Version**: 3.11.x
- **Key Dependencies**:
  - numpy >= 1.24
  - scipy ^1.16
  - rebound ^4.4 (for IAS15)
  - numba >= 0.59 (JIT compilation)
  - h5py, pyarrow (data storage)

#### C++ Build
- **Build System**: CMake 3.18+
- **Compiler**: Conda-provided clang++ / gcc
- **Flags**: `-O3 -march=native` for production
- **QD Library**: Installed in `$CONDA_PREFIX/lib`

### Test Infrastructure

- **Framework**: pytest 8.4+
- **Test Count**: 121 tests
- **Coverage**: Unit tests, integration tests, benchmarks
- **Location**: `tests/` directory
- **Configuration**: `pytest.ini`, `.flake8`

### Performance Characteristics

#### IAS15 Integrator
- **Conservation**: Jacobi drift ~1e-16 (machine precision)
- **Speed**: ~50 periods/second for Earth-Moon system
- **Use Case**: High-accuracy trajectories, arbitrary duration

#### Yoshida8 Integrator
- **Conservation**: Jacobi drift ~1e-8 for moderate durations
- **Speed**: ~5x faster than IAS15 for fixed timestep
- **Use Case**: Long-term symplectic integration, periodic orbits

#### QD Library
- **Precision**: 31 decimal digits vs 15 for IEEE double
- **Overhead**: 10-50x slower than double precision
- **Use Case**: Energy/Jacobi constant verification, periodic orbit refinement

## Development Workflow

### Setup
```bash
cd /Users/jacobsullivan/Desktop/3body
mamba activate wp1_env
poetry install --no-root
```

### Testing
```bash
pytest tests/ -v                    # All tests
pytest tests/test_integrators.py   # Specific module
pytest -m "not slow"                # Skip long-running tests
```

### Benchmarking
```bash
python scripts/run_benchmark.py --backend ias15 --spec benchmarks/cr3bp_smoke.yaml
```

### Building QD Extension
```bash
python setup.py build_ext --inplace
```

## Known Issues

1. **QD Python Bindings**: Some convenience operators not fully implemented (mixed-type arithmetic, in-place operations). Workaround: use `dd_real` for all operands.

2. **Yoshida8 Extreme Cases**: Numerical overflow possible in very long integrations (>10,000 periods). Use IAS15 for ultra-long durations.

3. **RPATH Issues**: Some compiled executables have library loading issues on macOS. Use Python interfaces instead.

## Project Status

- **Phase 1 (Complete)**: High-precision infrastructure, integrators, testing
- **Phase 2 (In Progress)**: Trajectory cataloging, periodic orbit searches
- **Phase 3 (Future)**: Manifold computation, integrability analysis

## References

- QD Library: http://crd-legacy.lbl.gov/~dhbailey/mpdist/
- REBOUND: https://rebound.readthedocs.io/
- IAS15: Rein & Spiegel (2015), MNRAS 446:1424-1437
- Yoshida (1990): Construction of higher order symplectic integrators

## Contact

Project: Three-Body Problem Integrability Research - Work Package 1
