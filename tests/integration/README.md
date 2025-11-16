# WP3 Integration Tests

This directory contains integration tests for Work Package 3 (Discovery of Candidate Invariants).

## Test Structure

### Quick Validation (Start Here)

**File**: `test_wp3_quick_validation.py`

A fast validation suite that tests basic functionality without requiring extensive computation or external dependencies.

```bash
# Run quick validation
python tests/integration/test_wp3_quick_validation.py
```

**Tests Included**:
- Test 0: Module imports
- Test 1: Basis function construction
- Test 2: Symbolic regression (if PySINDy available)
- Test 3: Expression simplification
- Test 4: Conservation validation
- Test 5: Candidate ranking

**Expected runtime**: < 1 minute

---

### Comprehensive Tests (Full Validation)

**File**: `WP3_INTEGRATION_TESTS.md`

Detailed specification for comprehensive integration tests that validate the complete WP3 pipeline with real data from WP3.1 (geometric search) and WP3.2 (ML discovery).

**Test Suites**:

#### Suite 1: WP3.1 → WP3.3 (Geometric to Symbolic)
- Test 1.1: Trivial case - Angular momentum
- Test 1.2: Complex case - Quadratic integral

#### Suite 2: WP3.2 → WP3.3 (ML to Symbolic)
- Test 2.1: HNN prediction to symbolic
- Test 2.2: Method comparison (SINDy vs PySR)

#### Suite 3: Full Pipeline
- Test 3.1: Complete workflow (discovery → consolidation → ranking → report)

**Implementation**: See `WP3_INTEGRATION_TESTS.md` for detailed test code and specifications.

---

## Running Tests

### Prerequisites

**Required**:
```bash
pip install numpy scipy sympy
```

**Optional** (for full symbolic regression):
```bash
pip install pysindy  # For SINDy regression
pip install pysr     # For PySR (requires Julia)
```

### Quick Start

```bash
# From project root
cd /home/user/3body

# Run quick validation
python tests/integration/test_wp3_quick_validation.py

# Expected output:
# ================================================================================
# WP3 INTEGRATION - QUICK VALIDATION TESTS
# ================================================================================
#
# TEST 0: Module Import Validation
# ✓ WP3.1 modules imported
# ✓ WP3.2 modules imported
# ✓ WP3.3 modules imported
# ✓ TEST 0 PASSED
# ...
# Total: 6/6 tests passed (100.0%)
```

### Full Integration Tests

Once the comprehensive tests are implemented:

```bash
# Run all suites
python tests/integration/test_wp3_integration.py

# Run specific suite
python tests/integration/test_wp3_integration.py --suite 1
python tests/integration/test_wp3_integration.py --suite 2
python tests/integration/test_wp3_integration.py --suite 3
```

---

## Test Files

```
tests/integration/
├── README.md                          # This file
├── WP3_INTEGRATION_TESTS.md          # Comprehensive test specifications
├── test_wp3_quick_validation.py      # Quick validation suite
├── test_wp3_integration.py           # Master test runner (TODO)
├── test_wp31_to_wp33.py              # Suite 1 tests (TODO)
├── test_wp32_to_wp33.py              # Suite 2 tests (TODO)
├── test_full_pipeline.py             # Suite 3 tests (TODO)
└── fixtures/                          # Test data (TODO)
    ├── sample_killing_fields.pkl
    ├── sample_hnn_predictions.pkl
    └── test_trajectories.npy
```

---

## Success Criteria

### Quick Validation
- ✓ All modules import successfully
- ✓ Basis construction works
- ✓ Symbolic regression finds accurate fits (if PySINDy available)
- ✓ Expression simplification reduces complexity
- ✓ Validation detects agreement/disagreement correctly
- ✓ Ranking produces sensible ordering

### Comprehensive Tests

**Test Suite 1 (WP3.1 → WP3.3)**:
- ✓ Killing fields discovered from geometric search
- ✓ Integrals extracted and converted to symbolic form
- ✓ Symbolic-numerical residual < 1e-10
- ✓ Conservation error < 1e-5 on test trajectories

**Test Suite 2 (WP3.2 → WP3.3)**:
- ✓ HNN predictions can be symbolically regressed
- ✓ Regression residual < 1e-4
- ✓ Multiple methods (SINDy/PySR) work
- ✓ Symbolic expressions validated

**Test Suite 3 (Full Pipeline)**:
- ✓ Candidates from all sources consolidated
- ✓ Duplicates removed
- ✓ Ranking reflects quality (conservation + independence + complexity)
- ✓ Report generation successful
- ✓ Top candidates are physically meaningful

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError` for WP3 modules
```python
ModuleNotFoundError: No module named 'src'
```

**Solution**: Run from project root or add to Python path:
```bash
cd /home/user/3body
python tests/integration/test_wp3_quick_validation.py
```

### Missing Optional Dependencies

**Problem**: PySINDy or PySR not installed

**Solution**: Tests will skip gracefully. To install:
```bash
pip install pysindy  # Lightweight, recommended
pip install pysr     # Heavy (requires Julia), optional
```

### Numerical Issues

**Problem**: Tests fail with numerical instabilities

**Solution**: Check that:
- NumPy and SciPy are up to date
- Random seed is set for reproducibility
- Sample sizes are sufficient (500+ for regression)

---

## Development Guide

### Adding New Tests

1. **For quick validation**: Add to `test_wp3_quick_validation.py`
   - Keep runtime < 10 seconds per test
   - Use mock data or simple cases
   - Test API contracts, not full functionality

2. **For comprehensive tests**: Follow specs in `WP3_INTEGRATION_TESTS.md`
   - Use real data from WP3.1/WP3.2
   - Test complete workflows
   - Validate numerical accuracy rigorously

### Test Design Principles

- **Isolation**: Each test should be independent
- **Reproducibility**: Use fixed random seeds
- **Fast feedback**: Quick tests fail fast
- **Clear assertions**: One concept per test
- **Good error messages**: Explain what failed and why

### Example Test Pattern

```python
def test_my_feature():
    """Test description: what this validates."""
    print("="*80)
    print("TEST X: Feature Name")
    print("="*80)

    try:
        # Setup
        # ... create test data

        # Execute
        # ... call function under test

        # Verify
        success = (assertion1 and assertion2)

        # Report
        if success:
            print("✓ TEST X PASSED")
        else:
            print("✗ TEST X FAILED - reason")

        return success

    except Exception as e:
        print(f"✗ TEST X FAILED - Error: {e}")
        return False
```

---

## Continuous Integration

Tests are designed to run in CI/CD:

```yaml
# .github/workflows/wp3-tests.yml
name: WP3 Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install numpy scipy sympy pysindy
      - run: python tests/integration/test_wp3_quick_validation.py
```

---

## Test Data

### Fixtures

Pre-computed test data for expensive operations:

- **`sample_killing_fields.pkl`**: Pre-computed Killing fields (from WP3.1)
- **`sample_hnn_predictions.pkl`**: Pre-trained HNN predictions (from WP3.2)
- **`test_trajectories.npy`**: High-precision trajectories for validation

### Generating Fixtures

```python
# Generate test fixtures
python tests/integration/generate_fixtures.py

# Fixtures saved to tests/integration/fixtures/
```

---

## Related Documentation

- **WP3 Overview**: `Project-Design-Docs/WP3/WP3-Complete-Overview.md`
- **WP3.1 Implementation**: `Project-Design-Docs/WP3/WP3.1-IMPLEMENTATION-COMPLETE.md`
- **WP3.2 Roadmap**: `Project-Design-Docs/WP3/WP3.2-Implementation-Roadmap.md`
- **WP3.3 Summary**: `Project-Design-Docs/WP3/WP3.3-Symbolic-Regression-Summary.md`
- **Symbolic Module**: `src/python/symbolic/README.md`

---

## Contact

For questions about integration tests:
- See main project documentation
- Check test specifications in `WP3_INTEGRATION_TESTS.md`
- Review module documentation in `src/python/symbolic/`

---

**Last Updated**: 2025-11-15
**Status**: Quick validation implemented, comprehensive tests specified
**Next**: Implement comprehensive test suites 1-3
