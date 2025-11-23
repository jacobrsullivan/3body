#!/bin/bash
# Run all tests (C++ and Python)
#
# Usage:
#   ./scripts/run_tests.sh          # Run full test suite (~30 min)
#   ./scripts/run_tests.sh --fast   # Run fast test suite (<5 min, for pre-commit)

set -e  # Exit on error

# Parse arguments
FAST_MODE=false
if [ "$1" == "--fast" ]; then
    FAST_MODE=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ "$FAST_MODE" == true ]; then
    echo "=========================================="
    echo "Running Fast Test Suite (Pre-Commit)"
    echo "=========================================="
else
    echo "=========================================="
    echo "Running Full Test Suite"
    echo "=========================================="
fi

# Check for conda environment
if [ -z "$CONDA_PREFIX" ]; then
    echo -e "${YELLOW}Warning: CONDA_PREFIX not set. Are you in the conda environment?${NC}"
    echo "Run: mamba activate wp1_env"
    exit 1
fi

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Run Python environment tests
echo ""
echo -e "${BLUE}=========================================="
echo "Running Python Environment Tests"
echo "==========================================${NC}"
if [ "$FAST_MODE" == true ]; then
    # Fast mode: Only run critical tests, stop on first 5 failures
    if pytest tests/python/test_environment.py -v --maxfail=5 -x; then
        echo -e "${GREEN}✓ Python environment tests passed${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ Python environment tests failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    # Full mode: Run all tests
    if pytest tests/python/test_environment.py -v; then
        echo -e "${GREEN}✓ Python environment tests passed${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ Python environment tests failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

# Run C++ tests if built (skip in fast mode)
if [ "$FAST_MODE" != true ]; then
    if [ -f "build/qd_comprehensive_test" ]; then
        echo ""
        echo -e "${BLUE}=========================================="
        echo "Running QD Comprehensive Tests"
        echo "==========================================${NC}"
        if ./build/qd_comprehensive_test; then
            echo -e "${GREEN}✓ QD comprehensive tests passed${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ QD comprehensive tests failed${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${YELLOW}⚠ QD comprehensive tests not built (run scripts/build_cpp.sh first)${NC}"
    fi

    # Run verification test
    if [ -f "verify_qd" ]; then
        echo ""
        echo -e "${BLUE}=========================================="
        echo "Running QD Verification"
        echo "==========================================${NC}"
        if ./verify_qd; then
            echo -e "${GREEN}✓ QD verification passed${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ QD verification failed${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${YELLOW}⚠ QD verification executable not found${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}Fast mode: Skipping C++ tests (use full mode for complete coverage)${NC}"
fi

# In fast mode, also run coordinate transform tests (critical for WP2)
if [ "$FAST_MODE" == true ]; then
    if [ -f "tests/symbolic_lifts/test_coordinate_transforms.py" ]; then
        echo ""
        echo -e "${BLUE}=========================================="
        echo "Running Critical Coordinate Transform Tests"
        echo "==========================================${NC}"
        if pytest tests/symbolic_lifts/test_coordinate_transforms.py -v --maxfail=5; then
            echo -e "${GREEN}✓ Coordinate transform tests passed${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ Coordinate transform tests failed${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "=========================================="

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
