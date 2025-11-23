---
name: wp3-discovery-methods
description: Use when searching for conserved quantities via PDE solvers, Hamiltonian Neural Networks, or symbolic regression. Points to WP3 discovery tools.
---

# WP3 Discovery Methods

## Source of Truth
- **Code**: `src/python/symbolic/`, `src/python/ml/`
- **User Guide**: `User-Guides/User-Guide-WP3.md`
- **Tests**: `tests/wp3/`

## Method 1: Symbolic Regression
**Entry Point**: `src/python/symbolic/multi_stage_pipeline.py`

**Basis Libraries**:
- `spinor_basis.py` - ~80 KS spinor functions
- `elliptic_basis.py` - Jacobi elliptic functions (sn, cn, dn)
- `theta_basis.py` - Theta functions (complete integrability)

**Workflow**: See `User-Guides/User-Guide-WP3.md` Section 2

## Method 2: Hamiltonian Neural Networks
**Entry Point**: `src/python/ml/hnn_trainer.py`

**Architecture**: Defined in User-Guide-WP3.md Section 3.2

**Data Loader**: `src/python/ml/parquet_export.py` (HDF5 → Parquet conversion)

## Method 3: PDE Solver (Hamilton-Jacobi)
**Entry Point**: `src/python/symbolic/hj_solver.py`

**Theory**: Solve ∂S/∂t + H(q, ∂S/∂q) = 0

**Workflow**: See `User-Guides/User-Guide-WP3.md` Section 4

## Post-Processing
**Deduplication**: `src/python/symbolic/interpretability.py`

**Trivial Filter**: `src/python/symbolic/trivial_detector.py`
