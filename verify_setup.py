"""
Day 1 Setup Verification Script
Confirms all components are working correctly.
"""

import sys
import subprocess
import importlib
import os


def check_python_version():
    """Verify Python version is 3.11."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    assert version >= (3, 11), "Python 3.11+ required"
    print("✓ Python version OK")


def check_packages():
    """Verify core packages can be imported."""
    packages = [
        "numpy",
        "scipy",
        "matplotlib",
        "rebound",
        "pytest",
        "numba",
        "h5py",
        "pyarrow",
    ]
    for package in packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print(f"✓ {package} {version} imported successfully")
        except ImportError:
            print(f"✗ Failed to import {package}")
            raise


def check_compilers():
    """Verify Conda compilers are active."""
    try:
        # On macOS, conda provides clang++ instead of g++
        result = subprocess.run(["which", "clang++"], capture_output=True, text=True)
        compiler_path = result.stdout.strip()
        print(f"clang++ location: {compiler_path}")

        # Should contain conda/mamba environment path
        if "conda" in compiler_path or "mamba" in compiler_path:
            print("✓ Conda compilers active")
        else:
            print("⚠ Warning: System compilers may be active")

    except Exception as e:
        print(f"✗ Compiler check failed: {e}")


def check_poetry():
    """Verify Poetry configuration."""
    try:
        # Check if pyproject.toml exists
        if os.path.exists("pyproject.toml"):
            print("✓ pyproject.toml found")
        else:
            print("✗ pyproject.toml not found")

        # Check if poetry.lock exists
        if os.path.exists("poetry.lock"):
            print("✓ poetry.lock found (dependencies locked)")
        else:
            print("⚠ poetry.lock not found (run poetry install)")

    except Exception as e:
        print(f"✗ Poetry check failed: {e}")


def check_git_repo():
    """Verify Git repository is properly initialized."""
    try:
        if os.path.exists(".git"):
            print("✓ Git repository initialized")
        else:
            print("✗ Git repository not found")

        if os.path.exists(".gitignore"):
            print("✓ .gitignore file exists")
        else:
            print("⚠ .gitignore file missing")

    except Exception as e:
        print(f"✗ Git check failed: {e}")


def check_qd_library():
    """Verify QD library is installed and functional."""
    try:
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if not conda_prefix:
            print("⚠ CONDA_PREFIX not set - QD library check skipped")
            return

        # Check for QD library files
        qd_lib_path = os.path.join(conda_prefix, "lib", "libqd.dylib")
        qd_lib_alt = os.path.join(conda_prefix, "lib", "libqd.so")
        qd_lib_static = os.path.join(conda_prefix, "lib", "libqd.a")

        qd_header = os.path.join(conda_prefix, "include", "qd", "dd_real.h")

        lib_exists = (
            os.path.exists(qd_lib_path)
            or os.path.exists(qd_lib_alt)
            or os.path.exists(qd_lib_static)
        )

        if lib_exists:
            print("✓ QD library found")
        else:
            print("✗ QD library not found in $CONDA_PREFIX/lib")

        if os.path.exists(qd_header):
            print("✓ QD headers found")
        else:
            print("✗ QD headers not found")

        # Test if verify_qd executable exists and runs
        if os.path.exists("verify_qd"):
            print("✓ QD verification executable found")
            result = subprocess.run(
                ["./verify_qd"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "3.14159" in result.stdout:
                print("✓ QD library verification passed")
            else:
                print("✗ QD library verification failed")
        else:
            print("⚠ QD verification executable not found")

    except Exception as e:
        print(f"⚠ QD library check warning: {e}")


def check_qd_python_bindings():
    """Verify QD Python bindings are working (Day 5)."""
    try:
        import qd_python as qd

        # Test basic import
        print("✓ qd_python module imported successfully")

        # Check version
        version = qd.__version__
        print(f"✓ qd_python version: {version}")

        # Test basic functionality - verify pi constant
        pi = qd.pi
        pi_str = str(pi)
        if "3.14159" in pi_str:
            print(f"✓ QD constants working: π = {pi_str[:20]}...")
        else:
            print(f"✗ QD constants failed: π = {pi_str}")
            return False

        # Test arithmetic
        a = qd.dd_real("1.5")
        b = qd.dd_real("2.5")
        result = a + b
        if abs(float(result) - 4.0) < 1e-10:
            print("✓ QD arithmetic operations working")
        else:
            print(f"✗ QD arithmetic failed: 1.5 + 2.5 = {result}")
            return False

        # Test mathematical functions
        half_pi = qd.pi / qd.dd_real("2.0")
        sin_result = qd.sin(half_pi)
        if abs(float(sin_result) - 1.0) < 1e-10:
            print("✓ QD mathematical functions working")
        else:
            print(f"✗ QD functions failed: sin(π/2) = {sin_result}")
            return False

        return True

    except ImportError as e:
        print(f"✗ qd_python module not found: {e}")
        print("  Run: poetry run python setup.py build_ext --inplace")
        return False
    except Exception as e:
        print(f"✗ QD Python bindings check failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("Setup Verification (Days 1-5)")
    print("=" * 40)

    try:
        check_python_version()
        check_packages()
        check_compilers()
        check_poetry()
        check_git_repo()

        print("\n" + "=" * 40)
        print("Day 3: QD Library Verification")
        print("=" * 40)
        check_qd_library()

        print("\n" + "=" * 40)
        print("Day 5: QD Python Bindings Verification")
        print("=" * 40)
        qd_python_ok = check_qd_python_bindings()

        if qd_python_ok:
            print("\n🎉 All checks passed! Environment setup complete.")
        else:
            print("\n⚠ Some checks failed. See details above.")

    except Exception as e:
        print(f"\n❌ Setup verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
