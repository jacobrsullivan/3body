cmake_minimum_required(VERSION 3.18)
project(ThreeBodyQD VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Use conda environment if available
if(DEFINED ENV{CONDA_PREFIX})
    message(STATUS "Using Conda environment: $ENV{CONDA_PREFIX}")
    set(CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}" ${CMAKE_PREFIX_PATH})
    include_directories("$ENV{CONDA_PREFIX}/include")
    link_directories("$ENV{CONDA_PREFIX}/lib")
endif()

# Find QD library
find_library(QD_LIBRARY
    NAMES qd libqd
    HINTS $ENV{CONDA_PREFIX}/lib
    REQUIRED
)

find_path(QD_INCLUDE_DIR
    NAMES qd/dd_real.h
    HINTS $ENV{CONDA_PREFIX}/include
    REQUIRED
)

if(QD_LIBRARY AND QD_INCLUDE_DIR)
    message(STATUS "Found QD library: ${QD_LIBRARY}")
    message(STATUS "Found QD headers: ${QD_INCLUDE_DIR}")
else()
    message(FATAL_ERROR "QD library not found. Please install QD library.")
endif()

# Include directories
include_directories(${QD_INCLUDE_DIR})

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native")

# Default to Release build if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# Executables
add_executable(verify_qd src/cpp/verify_qd.cpp)
target_link_libraries(verify_qd ${QD_LIBRARY})

add_executable(qd_comprehensive_test src/cpp/qd_comprehensive_test.cpp)
target_link_libraries(qd_comprehensive_test ${QD_LIBRARY})

add_executable(qd_benchmark src/cpp/qd_benchmark.cpp)
target_link_libraries(qd_benchmark ${QD_LIBRARY})

# Install targets
install(TARGETS verify_qd qd_comprehensive_test qd_benchmark
    RUNTIME DESTINATION bin
)

# Testing support
enable_testing()
add_test(NAME QDComprehensiveTest COMMAND qd_comprehensive_test)
add_test(NAME QDVerification COMMAND verify_qd)

# Print summary
message(STATUS "")
message(STATUS "Configuration Summary:")
message(STATUS "  Project:      ${PROJECT_NAME}")
message(STATUS "  Version:      ${PROJECT_VERSION}")
message(STATUS "  Build type:   ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  QD library:   ${QD_LIBRARY}")
message(STATUS "  QD headers:   ${QD_INCLUDE_DIR}")
message(STATUS "")
