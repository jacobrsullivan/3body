# Build and Test Scripts

This directory contains automation scripts for building and testing the project.

## Available Scripts

### `build_cpp.sh`
Builds all C++ components using CMake.

**Usage:**
```bash
./scripts/build_cpp.sh
```

**What it does:**
- Configures CMake build system
- Builds all C++ executables (verify_qd, qd_comprehensive_test, qd_benchmark)
- Runs CMake-based tests
- Creates executables in `build/` directory

**Requirements:**
- Conda environment must be active (`mamba activate wp1_env`)
- QD library must be installed

### `run_tests.sh`
Runs all tests (Python and C++).

**Usage:**
```bash
./scripts/run_tests.sh
```

**What it does:**
- Runs Python environment tests with pytest
- Runs QD comprehensive tests (if built)
- Runs QD verification executable
- Provides summary of test results

**Requirements:**
- Conda environment must be active
- C++ components should be built first (using `build_cpp.sh`)

## Typical Workflow

1. Activate conda environment:
   ```bash
   mamba activate wp1_env
   ```

2. Build C++ components:
   ```bash
   ./scripts/build_cpp.sh
   ```

3. Run all tests:
   ```bash
   ./scripts/run_tests.sh
   ```

4. Run benchmarks (optional):
   ```bash
   ./build/qd_benchmark
   ```

## Troubleshooting

- **"CONDA_PREFIX not set"**: Make sure you've activated the conda environment
- **"CMake configuration failed"**: Check that QD library is installed in the conda environment
- **"Tests not built"**: Run `build_cpp.sh` first before running tests
