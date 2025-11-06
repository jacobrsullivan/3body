#!/bin/bash
# Build script for C++ components using CMake

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Building C++ Components"
echo "=========================================="

# Check for conda environment
if [ -z "$CONDA_PREFIX" ]; then
    echo -e "${YELLOW}Warning: CONDA_PREFIX not set. Are you in the conda environment?${NC}"
    echo "Run: mamba activate wp1_env"
    exit 1
fi

echo -e "${GREEN}Using Conda environment: $CONDA_PREFIX${NC}"

# Create build directory
BUILD_DIR="build"
if [ ! -d "$BUILD_DIR" ]; then
    echo "Creating build directory..."
    mkdir -p "$BUILD_DIR"
fi

cd "$BUILD_DIR"

# Configure with CMake
echo ""
echo "Configuring with CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
echo ""
echo "Building..."
cmake --build . --config Release

# Run tests
echo ""
echo "=========================================="
echo "Running Tests"
echo "=========================================="
ctest --output-on-failure

echo ""
echo -e "${GREEN}=========================================="
echo "Build Complete!"
echo "==========================================${NC}"
echo ""
echo "Executables built:"
echo "  - build/verify_qd"
echo "  - build/qd_comprehensive_test"
echo "  - build/qd_benchmark"
echo ""
echo "To run tests:"
echo "  ./build/qd_comprehensive_test"
echo ""
echo "To run benchmarks:"
echo "  ./build/qd_benchmark"

cd ..
