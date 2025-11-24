#!/bin/bash
# Test Script for Phase 3: Validation Automation
# This script validates that all Phase 3 components are working correctly

echo "=========================================="
echo "Phase 3 Validation Automation - Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

# Test function
run_test() {
    local test_name=$1
    local command=$2

    echo -n "Testing: $test_name ... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((passed++))
    else
        echo -e "${RED}FAIL${NC}"
        ((failed++))
    fi
}

# Phase 3 Component Tests
echo "=== Component Installation Tests ==="
echo ""

run_test "mermaid-cli (mmdc) installed" "which mmdc"
run_test "validate_diagram.py exists" "test -f scripts/validate_diagram.py"
run_test "validate_diagram.py executable" "test -x scripts/validate_diagram.py"
run_test "compare_diagrams.py exists" "test -f scripts/compare_diagrams.py"
run_test "compare_diagrams.py executable" "test -x scripts/compare_diagrams.py"

echo ""
echo "=== Golden Master Tests ==="
echo ""

run_test "Golden master directory exists" "test -d diagrams/golden"
run_test "Golden C4 context exists" "test -f diagrams/golden/context/threebody_system_context.mmd"
run_test "Golden sequence exists" "test -f diagrams/golden/sequence/validation_gauntlet.mmd"
run_test "Golden ERD exists" "test -f diagrams/golden/erd/trajectory_validation_model.mmd"
run_test "Golden state machine exists" "test -f diagrams/golden/state/candidate_lifecycle.mmd"

echo ""
echo "=== Diagram Validation Tests ==="
echo ""

run_test "Validate C4 Context diagram" "python scripts/validate_diagram.py diagrams/context/threebody_system_context.mmd"
run_test "Validate Sequence diagram" "python scripts/validate_diagram.py diagrams/sequence/validation_gauntlet.mmd"
run_test "Validate ERD diagram" "python scripts/validate_diagram.py diagrams/erd/trajectory_validation_model.mmd"
run_test "Validate State Machine diagram" "python scripts/validate_diagram.py diagrams/state/candidate_lifecycle.mmd"

echo ""
echo "=== Drift Detection Tests ==="
echo ""

run_test "Drift detection on all diagrams" "python scripts/compare_diagrams.py --all"
run_test "Drift detection on specific diagram" "python scripts/compare_diagrams.py --diagram diagrams/context/threebody_system_context.mmd"

echo ""
echo "=== Configuration Tests ==="
echo ""

run_test "Settings.json exists" "test -f .claude/settings.json"
run_test "Validation hook configured" "grep -q 'validate_diagram.py' .claude/settings.json"

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 3 validation automation is fully operational!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review and fix.${NC}"
    exit 1
fi
