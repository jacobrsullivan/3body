#!/bin/bash
# WP1 acceptance and test-gate runner.
#
# Usage:
#   ./scripts/run_tests.sh          # WP1 acceptance gate
#   ./scripts/run_tests.sh --fast   # Skip full collection; run fast WP1 checks
#
# This is intentionally not a claim that every research test in the repo passes.
# The complete pytest tree includes later-work-package tests with optional stacks.

set -e

FAST_MODE=false
if [ "${1:-}" = "--fast" ]; then
    FAST_MODE=true
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ -z "$CONDA_PREFIX" ]; then
    echo -e "${RED}CONDA_PREFIX not set.${NC}"
    echo "Activate the WP1 environment first, e.g.: micromamba activate wp1_env"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

run_step() {
    local name="$1"
    shift

    echo ""
    echo -e "${BLUE}=========================================="
    echo "$name"
    echo -e "==========================================${NC}"

    "$@"
}

echo "=========================================="
echo "WP1 Acceptance Gate"
echo "=========================================="
echo "Project: $PROJECT_ROOT"
echo "Conda:   $CONDA_PREFIX"

run_step "Setup Verification" python verify_setup.py

if [ "$FAST_MODE" != true ]; then
    run_step "Pytest Collection" python -m pytest --collect-only -q -p no:cacheprovider
else
    echo ""
    echo -e "${YELLOW}Fast mode: skipping full pytest collection.${NC}"
fi

run_step "WP1 Focused Pytest Suite" \
    python -m pytest \
        tests/python/test_environment.py \
        tests/test_dynamics.py \
        tests/test_integrators.py::TestAdaptiveSymplecticIntegrator \
        tests/test_integrators.py::TestHeyokaTaylorIntegrator \
        tests/test_sampling.py \
        tests/test_validation_external.py \
        tests/test_wp1_qualification.py \
        -q -p no:cacheprovider

if [ -d build ] && [ -x build/verify_qd ]; then
    run_step "QD CTest Suite" ctest --test-dir build --output-on-failure
else
    echo ""
    echo -e "${YELLOW}QD CTest skipped: build/verify_qd not found.${NC}"
    echo "Run ./scripts/build_cpp.sh before publication acceptance."
fi

echo ""
echo -e "${GREEN}WP1 acceptance gate passed.${NC}"
