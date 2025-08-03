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

## Verification

Run the setup verification script to ensure all components are working correctly:

```bash
python verify_setup.py
```

## Development

This project uses:
- **Black** for code formatting
- **Flake8** for linting
- **Pre-commit hooks** for quality control
- **pytest** for testing

All code quality checks run automatically before commits.
