# Three-Body Problem Integrability Research

**Work Package 1: High-Fidelity CR3BP Trajectory Catalogue**

A systematic search for hidden integrability in the Newtonian three-body problem via higher-dimensional symplectic embedding.

## Project Structure

- `src/cpp/` - High-precision C++ implementations
- `src/python/` - Python interface and analysis tools
- `tests/` - Automated test suite
- `notebooks/` - Jupyter analysis notebooks
- `docs/` - Documentation

## Environment Setup

This project uses conda/mamba for system-level dependencies and Poetry for Python package management.

### Quick Start

1. Create the conda environment:
   ```bash
   mamba env create -f environment.yml
   mamba activate wp1_env
   ```

2. Install Python dependencies:
   ```bash
   poetry install
   ```

3. Verify setup:
   ```bash
   python verify_setup.py
   ```

## Quick Start

1. Activate the conda environment:
   ```bash
   mamba activate wp1_env
   ```

2. Verify setup (Days 1-3):
   ```bash
   python verify_setup.py
   ```

3. Build C++ components:
   ```bash
   ./scripts/build_cpp.sh
   ```

4. Run tests:
   ```bash
   ./scripts/run_tests.sh
   ```

## Verification

### Environment Verification
Run the setup verification script to ensure all components are working correctly:

```bash
python verify_setup.py
```

This checks:
- Python version and packages
- Conda compilers
- QD library installation
- QD high-precision arithmetic

### Comprehensive Testing
Run the full test suite (C++ and Python):

```bash
./scripts/run_tests.sh
```

Or run specific tests:
```bash
# Python environment tests
pytest tests/python/ -v

# QD comprehensive tests
./build/qd_comprehensive_test

# QD performance benchmarks
./build/qd_benchmark
```

## Development

This project uses:
- **CMake** for C++ build automation
- **pytest** for Python testing
- **Black** for code formatting
- **Flake8** for linting
- **Pre-commit hooks** for quality control

All code quality checks run automatically before commits.

### Build System

The project includes automated build scripts in `scripts/`:
- `build_cpp.sh` - Build all C++ components
- `run_tests.sh` - Run all tests (Python + C++)

See `scripts/README.md` for detailed usage.
