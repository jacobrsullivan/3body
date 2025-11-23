---
name: wp1-precision-integration
description: Use when setting up or running high-precision trajectory integrations. Provides workflow for integrator selection, precision arithmetic, and production pipelines.
---

# WP1 Precision Integration Workflow

## Source of Truth
- **Code**: `src/python/integrators/`
- **User Guide**: `User-Guides/User-Guide-WP1.md`
- **Tests**: `tests/python/`, `tests/regularization/`

## Workflow

### 1. Integrator Selection
**Available**: IAS15, Adaptive Symplectic, Yoshida8

**Read** these files to understand implementations:
- `src/python/integrators/ias15.py` - Standard precision, adaptive
- `src/python/integrators/adaptive_symplectic.py` - Double-double, symplectic
- `src/python/integrators/yoshida8.py` - Fixed step, benchmarking

**Decision Matrix**: See `User-Guides/User-Guide-WP1.md` Section 2.1

### 2. Precision Configuration
**Double-Double Arithmetic**: Uses QD library (31 decimal digits)

**Check installation**:
```bash
./build/qd_comprehensive_test
```

**Python binding**: `src/python/integrators/qd_wrapper.py` (if exists, otherwise mpmath)

### 3. Production Run
**Tool**: Snakemake pipeline

**Entry point**: `Snakefile` (root directory)

**Usage**: See `User-Guides/User-Guide-WP1.md` Section 3

### 4. Validation
**Criteria**:
- |ΔC/C| < 10^-14 (Tier 1) or 10^-25 (Tier 2)
- MEGNO convergence (regular: Y→2, chaotic: Y→∞)

**Tool**: `src/python/validation/conservation_validator.py`

## Testing
**Before production runs**:
```bash
pytest tests/python/ -v
pytest tests/regularization/ -v
```
