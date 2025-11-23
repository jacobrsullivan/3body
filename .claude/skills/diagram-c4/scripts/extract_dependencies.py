#!/usr/bin/env python3
"""
Extract external dependencies from pyproject.toml and environment.yml for C4 Context diagrams.

This script parses dependency manifests and classifies libraries into external systems
with appropriate metadata for C4 Context diagram generation.

Usage:
    python extract_dependencies.py [--pyproject path/to/pyproject.toml] [--env path/to/environment.yml]

Output:
    JSON mapping library names to external system classifications
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Python 3.11+ has tomllib built-in
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: tomllib/tomli not available. Please install tomli: pip install tomli", file=sys.stderr)
        sys.exit(1)

# Dependency classification mapping
# Maps library names to external system information
DEPENDENCY_CLASSIFICATIONS = {
    # Data Storage
    "h5py": {
        "system_name": "HDF5 Data Store",
        "description": "Persistent trajectory and validation result storage",
        "type": "datastore",
        "boundary": "external"
    },
    "pyarrow": {
        "system_name": "Apache Arrow Storage",
        "description": "Columnar data format for ML pipelines",
        "type": "datastore",
        "boundary": "external"
    },

    # Numerical Computing
    "numpy": {
        "system_name": "NumPy",
        "description": "Array computations and linear algebra",
        "type": "library",
        "boundary": "external"
    },
    "scipy": {
        "system_name": "SciPy",
        "description": "Scientific computing algorithms",
        "type": "library",
        "boundary": "external"
    },

    # Integration Libraries
    "rebound": {
        "system_name": "REBOUND Integrator Library",
        "description": "Adaptive IAS15 N-body integrator",
        "type": "library",
        "boundary": "external"
    },

    # ML and Optimization
    "torch": {
        "system_name": "PyTorch Framework",
        "description": "Neural network training for HNN discovery",
        "type": "library",
        "boundary": "external"
    },
    "pysr": {
        "system_name": "PySR (Julia)",
        "description": "Symbolic regression engine",
        "type": "external_process",
        "boundary": "external"
    },

    # JIT Compilation
    "numba": {
        "system_name": "Numba JIT Compiler",
        "description": "High-performance numerical computation",
        "type": "library",
        "boundary": "external"
    },

    # Visualization
    "matplotlib": {
        "system_name": "Matplotlib",
        "description": "Scientific plotting and visualization",
        "type": "library",
        "boundary": "external"
    },

    # Development/Interactive
    "jupyterlab": {
        "system_name": "JupyterLab",
        "description": "Interactive development environment",
        "type": "tool",
        "boundary": "external",
        "exclude_from_production": True
    },
    "pytest": {
        "system_name": "PyTest Framework",
        "description": "Unit and integration testing",
        "type": "tool",
        "boundary": "external",
        "exclude_from_production": True
    },

    # Language Bindings
    "pybind11": {
        "system_name": "PyBind11 Bridge",
        "description": "Python-C++ interoperability for QD library",
        "type": "library",
        "boundary": "external"
    },

    # Symbolic Math
    "sympy": {
        "system_name": "SymPy",
        "description": "Symbolic mathematics and computer algebra",
        "type": "library",
        "boundary": "external"
    },

    # System Dependencies (from environment.yml)
    "cmake": {
        "system_name": "CMake Build System",
        "description": "C++ build tool for QD library",
        "type": "build_tool",
        "boundary": "external",
        "exclude_from_production": True
    },
    "qd": {
        "system_name": "QD Library",
        "description": "Double-double precision arithmetic (31 digits)",
        "type": "library",
        "boundary": "external"
    }
}


def parse_pyproject_toml(filepath: Path) -> Dict[str, Any]:
    """Parse pyproject.toml and extract dependencies."""
    if not filepath.exists():
        return {}

    with open(filepath, 'rb') as f:
        data = tomllib.load(f)

    dependencies = {}

    # Extract main dependencies from poetry section
    if 'tool' in data and 'poetry' in data['tool']:
        poetry = data['tool']['poetry']

        # Main dependencies
        if 'dependencies' in poetry:
            for dep_name in poetry['dependencies']:
                # Skip Python version specifier
                if dep_name.lower() == 'python':
                    continue

                # Normalize name (lowercase)
                dep_normalized = dep_name.lower()

                # Check if we have classification
                if dep_normalized in DEPENDENCY_CLASSIFICATIONS:
                    dependencies[dep_name] = DEPENDENCY_CLASSIFICATIONS[dep_normalized]
                else:
                    # Unknown dependency - provide generic classification
                    dependencies[dep_name] = {
                        "system_name": dep_name,
                        "description": "External library",
                        "type": "library",
                        "boundary": "external",
                        "unknown": True
                    }

    return dependencies


def parse_environment_yml(filepath: Path) -> Dict[str, Any]:
    """Parse environment.yml and extract conda dependencies."""
    if not filepath.exists():
        return {}

    try:
        import yaml
    except ImportError:
        # If PyYAML not available, return empty
        return {}

    dependencies = {}

    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    if 'dependencies' in data:
        for dep in data['dependencies']:
            if isinstance(dep, str):
                # Parse dep string (e.g., "python=3.11" or "cmake")
                dep_name = dep.split('=')[0].split('>')[0].split('<')[0].strip()

                # Skip python
                if dep_name.lower() == 'python':
                    continue

                dep_normalized = dep_name.lower()

                if dep_normalized in DEPENDENCY_CLASSIFICATIONS:
                    dependencies[dep_name] = DEPENDENCY_CLASSIFICATIONS[dep_normalized]
                else:
                    dependencies[dep_name] = {
                        "system_name": dep_name,
                        "description": "System dependency",
                        "type": "tool",
                        "boundary": "external",
                        "unknown": True
                    }

    return dependencies


def merge_dependencies(pyproject_deps: Dict, env_deps: Dict) -> Dict[str, Any]:
    """Merge dependencies from multiple sources."""
    merged = {}

    # Add pyproject.toml dependencies
    merged.update(pyproject_deps)

    # Add environment.yml dependencies (avoid duplicates)
    for dep_name, dep_info in env_deps.items():
        if dep_name not in merged:
            merged[dep_name] = dep_info

    return merged


def filter_for_c4(dependencies: Dict[str, Any]) -> Dict[str, Any]:
    """Filter dependencies appropriate for C4 Context diagrams.

    Removes development tools and focuses on runtime external systems.
    """
    filtered = {}

    for dep_name, dep_info in dependencies.items():
        # Exclude development/build tools from production C4 diagrams
        if dep_info.get('exclude_from_production', False):
            continue

        # Include all runtime dependencies
        if dep_info.get('type') in ['datastore', 'library', 'external_process']:
            filtered[dep_name] = dep_info

    return filtered


def generate_c4_metadata(dependencies: Dict[str, Any]) -> Dict[str, Any]:
    """Generate additional metadata for C4 Context diagram generation."""

    # Group by type
    grouped = {
        'datastores': [],
        'libraries': [],
        'external_processes': [],
        'unknown': []
    }

    for dep_name, dep_info in dependencies.items():
        dep_type = dep_info.get('type', 'unknown')

        entry = {
            'name': dep_name,
            'system_name': dep_info.get('system_name', dep_name),
            'description': dep_info.get('description', ''),
            'mermaid_type': 'System_Ext'
        }

        if dep_type == 'datastore':
            grouped['datastores'].append(entry)
        elif dep_type == 'library':
            grouped['libraries'].append(entry)
        elif dep_type == 'external_process':
            grouped['external_processes'].append(entry)
        else:
            grouped['unknown'].append(entry)

    return {
        'dependencies': dependencies,
        'grouped': grouped,
        'total_count': len(dependencies)
    }


def main():
    parser = argparse.ArgumentParser(
        description='Extract dependencies for C4 Context diagram generation'
    )
    parser.add_argument(
        '--pyproject',
        type=Path,
        default=Path('pyproject.toml'),
        help='Path to pyproject.toml (default: pyproject.toml)'
    )
    parser.add_argument(
        '--env',
        type=Path,
        default=Path('environment.yml'),
        help='Path to environment.yml (default: environment.yml)'
    )
    parser.add_argument(
        '--filter',
        action='store_true',
        help='Filter for C4 diagram (exclude dev dependencies)'
    )
    parser.add_argument(
        '--metadata',
        action='store_true',
        help='Include C4 metadata (groupings, counts)'
    )

    args = parser.parse_args()

    # Parse both files
    pyproject_deps = parse_pyproject_toml(args.pyproject)
    env_deps = parse_environment_yml(args.env)

    # Merge dependencies
    all_deps = merge_dependencies(pyproject_deps, env_deps)

    # Filter if requested
    if args.filter:
        all_deps = filter_for_c4(all_deps)

    # Generate metadata if requested
    if args.metadata:
        output = generate_c4_metadata(all_deps)
    else:
        output = all_deps

    # Output JSON
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
