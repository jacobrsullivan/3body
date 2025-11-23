#!/usr/bin/env python3
"""
Extract external dependencies from pyproject.toml for C4 Context diagrams.

Usage:
    python extract_dependencies.py [path/to/pyproject.toml]

Output:
    JSON mapping library names to external system classifications
"""

import json
import sys
from pathlib import Path

def parse_pyproject(filepath):
    """Parse pyproject.toml and extract dependencies."""
    # TODO (Phase 2): Implement TOML parsing
    # For now, return stub data

    dependencies = {
        "h5py": {
            "system_name": "HDF5 Storage",
            "description": "Trajectory data persistence",
            "type": "datastore"
        },
        "rebound": {
            "system_name": "REBOUND Library",
            "description": "Adaptive integration algorithms",
            "type": "library"
        },
        "PySR": {
            "system_name": "PySR Engine",
            "description": "Symbolic regression via Julia",
            "type": "external_process"
        },
        "torch": {
            "system_name": "ML Framework",
            "description": "Neural network training",
            "type": "library"
        }
    }

    return dependencies

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "pyproject.toml"

    if not Path(filepath).exists():
        print(f"Error: {filepath} not found", file=sys.stderr)
        sys.exit(1)

    dependencies = parse_pyproject(filepath)

    # Output JSON
    print(json.dumps(dependencies, indent=2))

if __name__ == "__main__":
    main()
