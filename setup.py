#!/usr/bin/env python3
"""
Setup script for QD Library Python bindings.
Builds the qd_python extension module using pybind11.
"""

import os
import sys

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

# Try to find QD library paths
# First check conda environment, then fall back to system paths
conda_prefix = os.environ.get("CONDA_PREFIX", "")

if conda_prefix:
    # Using conda environment
    qd_include_dir = os.path.join(conda_prefix, "include")
    qd_lib_dir = os.path.join(conda_prefix, "lib")
else:
    # Try system-wide installation
    qd_include_dir = "/usr/include"
    qd_lib_dir = "/usr/lib/x86_64-linux-gnu"

    # Also try /usr/local for manual installations
    if not os.path.exists(os.path.join(qd_include_dir, "qd", "dd_real.h")):
        qd_include_dir = "/usr/local/include"
        qd_lib_dir = "/usr/local/lib"

# Verify QD library is available
qd_header = os.path.join(qd_include_dir, "qd", "dd_real.h")
if not os.path.exists(qd_header):
    print(f"ERROR: QD library header not found at {qd_header}", file=sys.stderr)
    print("Searched paths:", file=sys.stderr)
    print("  - /usr/include/qd/dd_real.h", file=sys.stderr)
    print("  - /usr/local/include/qd/dd_real.h", file=sys.stderr)
    if conda_prefix:
        print(f"  - {conda_prefix}/include/qd/dd_real.h", file=sys.stderr)
    raise RuntimeError(f"QD library header not found at {qd_header}")

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "qd_python",
        sources=["src/cpp/qd_python_bindings.cpp"],
        include_dirs=[
            qd_include_dir,
        ],
        libraries=["qd"],
        library_dirs=[qd_lib_dir],
        language="c++",
        cxx_std=11,
    ),
]

setup(
    name="qd_python",
    version="1.0.0",
    author="Three-Body Problem Research Team",
    author_email="research@example.com",
    description="Python bindings for QD Library high-precision arithmetic",
    long_description="High-precision double-double arithmetic operations "
    "for scientific computing",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
)
