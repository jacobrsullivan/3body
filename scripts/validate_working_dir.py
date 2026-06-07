#!/usr/bin/env python3
"""
Validate Working Directory - 3Body Project

Ensures the current working directory is the project root before executing
any scripts or dry-run operations.

Usage:
    python scripts/validate_working_dir.py

Exit codes:
    0 - Validation passed (correct directory)
    1 - Validation failed (wrong directory)

Created: 2025-11-24
Purpose: Prevent path confusion issues in dry-runs and script execution
"""

import sys
from pathlib import Path


def validate_working_directory(verbose=True):
    """
    Ensure we're in the project root directory.

    Args:
        verbose: If True, print detailed output

    Returns:
        bool: True if in correct directory, False otherwise
    """
    cwd = Path.cwd()

    # Define key project markers that should exist at root
    critical_markers = {
        "CLAUDE.md": "Project instructions file",
        "pyproject.toml": "Poetry configuration",
        "src/python": "Python source code directory",
        "tests": "Test suite directory",
        "Dry-Run": "Dry-run infrastructure directory",
        "User-Guides": "Documentation directory",
    }

    optional_markers = {
        ".git": "Git repository",
        "environment.yml": "Conda environment file",
        "poetry.lock": "Poetry lock file",
    }

    # Check critical markers
    missing_critical = {}
    for marker, description in critical_markers.items():
        marker_path = cwd / marker
        if not marker_path.exists():
            missing_critical[marker] = description

    # Check optional markers (for additional context)
    missing_optional = {}
    for marker, description in optional_markers.items():
        marker_path = cwd / marker
        if not marker_path.exists():
            missing_optional[marker] = description

    # Validation result
    is_valid = len(missing_critical) == 0

    if verbose:
        print("=" * 70)
        print("Working Directory Validation")
        print("=" * 70)
        print(f"Current directory: {cwd}")
        print(f"Directory name: {cwd.name}")
        print()

        if is_valid:
            print("✅ VALIDATION PASSED")
            print()
            print("All critical project markers found:")
            for marker, description in critical_markers.items():
                print(f"  ✓ {marker:<25} {description}")

            # Show optional markers
            if missing_optional:
                print()
                print("Optional markers (informational):")
                for marker in optional_markers:
                    if (cwd / marker).exists():
                        print(f"  ✓ {marker}")
                    else:
                        print(f"  ✗ {marker} (not critical)")

            print()
            print("✅ You are in the correct directory: project root")
            print("=" * 70)
        else:
            print("❌ VALIDATION FAILED")
            print()
            print("Missing critical project markers:")
            for marker, description in missing_critical.items():
                print(f"  ✗ {marker:<25} {description}")

            print()
            print("Expected directory structure:")
            print("  /path/to/3body/")
            print("  ├── CLAUDE.md")
            print("  ├── pyproject.toml")
            print("  ├── src/")
            print("  │   └── python/")
            print("  ├── tests/")
            print("  ├── Dry-Run/")
            print("  └── User-Guides/")

            print()
            print("🔧 How to fix:")
            print()
            print("1. Navigate to project root:")
            print(f"   cd /path/to/3body")
            print()
            print("2. Or from any subdirectory:")
            print("   cd $(git rev-parse --show-toplevel)")
            print()
            print("3. Then re-run this validation:")
            print("   python scripts/validate_working_dir.py")

            print()
            print("=" * 70)

    return is_valid


def get_project_root():
    """
    Attempt to find the project root from current location.

    Returns:
        Path or None: Project root path if found, None otherwise
    """
    current = Path.cwd()

    # Try going up directories looking for markers
    for parent in [current] + list(current.parents):
        if (parent / "CLAUDE.md").exists() and (parent / "src" / "python").exists():
            return parent

    return None


def main():
    """Main validation routine."""
    is_valid = validate_working_directory(verbose=True)

    if not is_valid:
        print()

        # Try to find project root
        project_root = get_project_root()
        if project_root:
            print(f"💡 Hint: Project root appears to be: {project_root}")
            print(f"         Run: cd {project_root}")
        else:
            print("⚠️  Could not automatically locate project root.")
            print("    Please navigate to the 3body directory manually.")

        print()
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
