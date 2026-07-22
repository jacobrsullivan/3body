"""
Test suite for environment verification and basic functionality.
"""

import pytest
import sys
import os
import subprocess


class TestEnvironment:
    """Test environment setup and configuration."""

    def test_python_version(self):
        """Verify Python version is 3.11 or higher."""
        assert sys.version_info >= (3, 11), "Python 3.11+ required"

    def test_numpy_import(self):
        """Test that NumPy can be imported."""
        import numpy as np

        assert hasattr(np, "__version__")
        # Verify numpy version is compatible with numba
        major, minor, _ = map(int, np.__version__.split(".")[:3])
        assert (major, minor) < (2, 3), "NumPy version should be < 2.3 for numba"

    def test_scipy_import(self):
        """Test that SciPy can be imported."""
        import scipy

        assert hasattr(scipy, "__version__")

    def test_matplotlib_import(self):
        """Test that Matplotlib can be imported."""
        import matplotlib

        assert hasattr(matplotlib, "__version__")

    def test_numba_import(self):
        """Test that Numba can be imported."""
        import numba

        assert hasattr(numba, "__version__")

    def test_h5py_import(self):
        """Test that h5py can be imported."""
        import h5py

        assert hasattr(h5py, "__version__")

    def test_pyarrow_import(self):
        """Test that PyArrow can be imported."""
        import pyarrow

        assert hasattr(pyarrow, "__version__")

    def test_rebound_import(self):
        """Test that REBOUND can be imported."""
        import rebound

        assert hasattr(rebound, "__version__")


class TestCompilers:
    """Test compiler availability and configuration."""

    def test_cpp_compiler_available(self):
        """Verify C++ compiler is available."""
        # Try to find clang++ or g++
        result_clang = subprocess.run(
            ["which", "clang++"], capture_output=True, text=True
        )
        result_gcc = subprocess.run(["which", "g++"], capture_output=True, text=True)

        assert (
            result_clang.returncode == 0 or result_gcc.returncode == 0
        ), "C++ compiler not found"

    def test_cmake_available(self):
        """Verify CMake is available."""
        result = subprocess.run(["which", "cmake"], capture_output=True, text=True)
        assert result.returncode == 0, "CMake not found"

    def test_conda_environment(self):
        """Verify conda environment is active."""
        conda_prefix = os.environ.get("CONDA_PREFIX")
        assert conda_prefix is not None, "CONDA_PREFIX not set"
        assert os.path.realpath(conda_prefix) == os.path.realpath(sys.prefix), (
            "CONDA_PREFIX does not match the running Python environment"
        )


class TestQDLibrary:
    """Test QD library installation and basic functionality."""

    VERIFY_QD = os.path.join("build", "verify_qd")

    def test_qd_executable_exists(self):
        """Verify QD verification executable exists."""
        assert os.path.exists(self.VERIFY_QD), "build/verify_qd executable not found"

    def test_qd_executable_runs(self):
        """Test that QD verification executable runs successfully."""
        if not os.path.exists(self.VERIFY_QD):
            pytest.skip("build/verify_qd executable not found")

        result = subprocess.run(
            [self.VERIFY_QD], capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0, "verify_qd execution failed"
        assert "3.14159" in result.stdout, "QD verification output incorrect"

    def test_qd_library_files(self):
        """Verify QD library files are installed."""
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if not conda_prefix:
            pytest.skip("CONDA_PREFIX not set")

        # Check for library files (dylib for macOS, so for Linux)
        lib_paths = [
            os.path.join(conda_prefix, "lib", "libqd.dylib"),
            os.path.join(conda_prefix, "lib", "libqd.so"),
            os.path.join(conda_prefix, "lib", "libqd.a"),
        ]

        assert any(os.path.exists(p) for p in lib_paths), "QD library not found"

    def test_qd_headers(self):
        """Verify QD header files are installed."""
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if not conda_prefix:
            pytest.skip("CONDA_PREFIX not set")

        header_path = os.path.join(conda_prefix, "include", "qd", "dd_real.h")
        assert os.path.exists(header_path), "QD headers not found"


class TestProjectStructure:
    """Test project directory structure."""

    def test_directories_exist(self):
        """Verify expected project directories exist."""
        required_dirs = [
            "src",
            "src/cpp",
            "tests",
            "tests/python",
            "tests/cpp",
            "examples",
            "scripts",
            "Project-Design-Docs",
            "Science-Research-Docs",
            "User-Guides",
            "External-Validation-Planning-Docs",
            "validation-external",
        ]

        for directory in required_dirs:
            assert os.path.exists(directory), f"Directory {directory} not found"

    def test_configuration_files_exist(self):
        """Verify configuration files exist."""
        required_files = [
            "pyproject.toml",
            "poetry.lock",
            "environment.yml",
            ".gitignore",
            ".pre-commit-config.yaml",
            "CMakeLists.txt",
        ]

        for file in required_files:
            assert os.path.exists(file), f"Configuration file {file} not found"

    def test_documentation_exists(self):
        """Verify documentation files exist."""
        doc_files = ["README.md", "CLAUDE.md"]

        for file in doc_files:
            assert os.path.exists(file), f"Documentation file {file} not found"


class TestCMakeBuild:
    """Test CMake build system."""

    def test_cmake_lists_valid(self):
        """Test that CMakeLists.txt is valid."""
        assert os.path.exists("CMakeLists.txt"), "CMakeLists.txt not found"

        # Try to configure (dry run)
        build_dir = "build_test"
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        result = subprocess.run(
            ["cmake", "..", "-DCMAKE_BUILD_TYPE=Debug"],
            cwd=build_dir,
            capture_output=True,
            text=True,
        )

        # Clean up
        if os.path.exists(build_dir):
            import shutil

            shutil.rmtree(build_dir)

        assert result.returncode == 0, f"CMake configuration failed: {result.stderr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
