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
    packages = ["numpy", "scipy", "matplotlib", "rebound", "pytest"]
    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} imported successfully")
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


def main():
    """Run all verification checks."""
    print("Day 1 Setup Verification")
    print("=" * 30)

    try:
        check_python_version()
        check_packages()
        check_compilers()
        check_poetry()
        check_git_repo()

        print("\n🎉 All checks passed! Day 1 setup complete.")

    except Exception as e:
        print(f"\n❌ Setup verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
