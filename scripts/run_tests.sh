#!/bin/bash
# Run all tests (C++ and Python)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Running All Tests"
echo "=========================================="

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
if pytest tests/python/test_environment.py -v; then
    echo -e "${GREEN}✓ Python environment tests passed${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Python environment tests failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Run C++ tests if built
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
