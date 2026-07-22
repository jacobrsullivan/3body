#!/usr/bin/env python3
"""
Setup script for QD Library Python bindings.
Builds the qd_python extension module using pybind11.
"""

import os
import sys
from pathlib import Path

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

QD_PYTHON_VERSION = "1.0.0"
QD_LIBRARY_VERSION = "2.3.22"


def find_qd_prefix() -> Path:
    """Find one prefix containing both QD headers and a linkable library."""
    candidates = [
        os.environ.get("QD_ROOT"),
        os.environ.get("CONDA_PREFIX"),
        sys.prefix,
        "/opt/homebrew",
        "/usr/local",
        "/usr",
    ]
    searched = []
    for value in candidates:
        if not value:
            continue
        prefix = Path(value).resolve()
        if prefix in searched:
            continue
        searched.append(prefix)
        header = prefix / "include" / "qd" / "dd_real.h"
        libraries = tuple((prefix / "lib").glob("libqd.*"))
        if header.is_file() and libraries:
            return prefix

    locations = "\n  - ".join(str(path) for path in searched)
    raise RuntimeError(
        "QD headers and library were not found under any candidate prefix:\n"
        f"  - {locations}"
    )


qd_prefix = find_qd_prefix()
qd_include_dir = str(qd_prefix / "include")
qd_lib_dir = str(qd_prefix / "lib")

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
        define_macros=[
            ("QD_PYTHON_VERSION", f'"{QD_PYTHON_VERSION}"'),
            ("QD_LIBRARY_VERSION", f'"{QD_LIBRARY_VERSION}"'),
        ],
        language="c++",
        cxx_std=11,
    ),
]

setup(
    name="qd_python",
    version=QD_PYTHON_VERSION,
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
