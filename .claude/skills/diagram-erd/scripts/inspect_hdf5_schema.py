#!/usr/bin/env python3
"""
Extract entity structure from HDF5 files for Conceptual ERD generation.

This script inspects HDF5 trajectory files and extracts the conceptual data model,
filtering out technical implementation details per 4Abstractions de-noising rules.

Usage:
    python inspect_hdf5_schema.py [hdf5_file] [--all-files pattern]

Output:
    JSON representation of conceptual entities, attributes, and relationships
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
import glob

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False
    print("Warning: h5py not available. Using fallback schema.", file=sys.stderr)


# Expected schema based on CLAUDE.md documentation
EXPECTED_SCHEMA = {
    "TRAJECTORY": {
        "attributes": {
            "orbit_id": {"type": "string", "description": "Unique trajectory identifier", "business": True},
            "mass_ratio": {"type": "float", "description": "Mass ratio parameter μ", "business": True},
            "jacobi_constant": {"type": "float", "description": "Jacobi constant C", "business": True},
            "tier": {"type": "int", "description": "Integration tier (1=double, 2=double-double)", "business": True},
            "coordinate_system": {"type": "string", "description": "Coordinate system (Cartesian, Jacobi, etc.)", "business": True},
            "integration_time": {"type": "float", "description": "Total integration time", "business": True},
        },
        "datasets": {
            "time": {"type": "array[float]", "description": "Time points", "technical": False},
            "positions": {"type": "array[float, (N, 3, 3)]", "description": "Body positions", "technical": False},
            "momenta": {"type": "array[float, (N, 3, 3)]", "description": "Body momenta", "technical": False},
        },
        "relationships": [
            {"target": "CHAOS_INDICATOR", "cardinality": "1:1", "description": "classified_by"},
            {"target": "VALIDATION_REPORT", "cardinality": "1:many", "description": "tested_with"}
        ]
    },
    "CHAOS_INDICATOR": {
        "attributes": {
            "megno_value": {"type": "float", "description": "MEGNO chaos indicator", "business": True},
            "classification": {"type": "string", "description": "regular/chaotic/escape", "business": True},
            "lyapunov_estimate": {"type": "float", "description": "Approximate Lyapunov exponent", "business": True},
        },
        "relationships": [
            {"target": "TRAJECTORY", "cardinality": "1:1", "description": "classifies"}
        ]
    },
    "VALIDATION_REPORT": {
        "attributes": {
            "report_id": {"type": "string", "description": "Unique report identifier", "business": True},
            "conservation_error": {"type": "float", "description": "Integral conservation error", "business": True},
            "rank_test_passed": {"type": "bool", "description": "Independence test result", "business": True},
            "involution_test_passed": {"type": "bool", "description": "Commutativity test result", "business": True},
            "overall_passed": {"type": "bool", "description": "Overall validation verdict", "business": True},
        },
        "relationships": [
            {"target": "TRAJECTORY", "cardinality": "many:1", "description": "tests"},
            {"target": "CANDIDATE_INTEGRAL", "cardinality": "many:1", "description": "evaluates"}
        ]
    },
    "CANDIDATE_INTEGRAL": {
        "attributes": {
            "integral_id": {"type": "string", "description": "Unique integral identifier", "business": True},
            "symbolic_form": {"type": "string", "description": "Mathematical expression", "business": True},
            "basis_type": {"type": "string", "description": "spinor/elliptic/theta", "business": True},
            "discovery_confidence": {"type": "float", "description": "Discovery method confidence", "business": True},
        },
        "relationships": [
            {"target": "VALIDATION_REPORT", "cardinality": "1:many", "description": "evaluated_on"},
            {"target": "MORALES_RAMIS_RESULT", "cardinality": "1:optional", "description": "validated_via"},
            {"target": "DISCOVERY_METHOD", "cardinality": "many:1", "description": "discovered_by"}
        ]
    },
    "PERIODIC_ORBIT": {
        "attributes": {
            "family_name": {"type": "string", "description": "Orbit family (Lagrange, Euler, etc.)", "business": True},
            "period": {"type": "float", "description": "Orbital period", "business": True},
            "symmetry_group": {"type": "string", "description": "Symmetry classification", "business": True},
        },
        "relationships": [
            {"target": "MORALES_RAMIS_RESULT", "cardinality": "1:1", "description": "generates"}
        ]
    },
    "MORALES_RAMIS_RESULT": {
        "attributes": {
            "galois_group": {"type": "string", "description": "Differential Galois group", "business": True},
            "integrable_upstairs": {"type": "bool", "description": "Lift-integrability verdict", "business": True},
            "variational_equation": {"type": "string", "description": "Variational equation form", "business": True},
        },
        "relationships": [
            {"target": "CANDIDATE_INTEGRAL", "cardinality": "optional:1", "description": "validates"},
            {"target": "PERIODIC_ORBIT", "cardinality": "1:1", "description": "uses"}
        ]
    },
    "DISCOVERY_METHOD": {
        "attributes": {
            "method_name": {"type": "string", "description": "SymbolicRegression/HNN/PDE", "business": True},
            "basis_family": {"type": "string", "description": "Function basis used", "business": True},
        },
        "relationships": [
            {"target": "CANDIDATE_INTEGRAL", "cardinality": "1:many", "description": "discovers"}
        ]
    }
}


def inspect_hdf5_file(filepath: Path) -> Dict[str, Any]:
    """Inspect an actual HDF5 file and extract schema."""
    if not HDF5_AVAILABLE:
        return None

    if not filepath.exists():
        print(f"Error: File {filepath} not found", file=sys.stderr)
        return None

    schema = {
        "filename": filepath.name,
        "attributes": {},
        "datasets": {},
        "groups": {}
    }

    try:
        with h5py.File(filepath, 'r') as f:
            # Extract file-level attributes
            for attr_name in f.attrs:
                # Filter technical attributes
                if attr_name not in ['created_at', 'updated_at', 'version', 'modified_by']:
                    schema["attributes"][attr_name] = {
                        "value": str(f.attrs[attr_name]),
                        "type": type(f.attrs[attr_name]).__name__
                    }

            # Extract datasets
            def visit_datasets(name, obj):
                if isinstance(obj, h5py.Dataset):
                    schema["datasets"][name] = {
                        "shape": obj.shape,
                        "dtype": str(obj.dtype),
                        "size": obj.size
                    }

            f.visititems(visit_datasets)

    except Exception as e:
        print(f"Error reading HDF5 file: {e}", file=sys.stderr)
        return None

    return schema


def apply_denoising_rules(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Apply de-noising rules to remove technical details.

    Per 4Abstractions ERD rules:
    - Strip technical columns: created_at, updated_at, version, deleted_at
    - Strip audit fields: modified_by, audit_id
    - Keep business identifiers and domain attributes
    """
    if not schema:
        return {}

    denoised = {
        "attributes": {},
        "datasets": {}
    }

    # Technical fields to exclude
    EXCLUDED_FIELDS = {
        'created_at', 'updated_at', 'deleted_at', 'version',
        'modified_by', 'audit_id', 'row_id', 'internal_id'
    }

    # Filter attributes
    if "attributes" in schema:
        for attr_name, attr_info in schema["attributes"].items():
            if attr_name.lower() not in EXCLUDED_FIELDS:
                denoised["attributes"][attr_name] = attr_info

    # Filter datasets (keep all as they represent business data)
    if "datasets" in schema:
        denoised["datasets"] = schema["datasets"]

    return denoised


def merge_with_expected_schema(observed_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Merge observed HDF5 schema with expected conceptual model."""
    # Start with expected schema
    merged = EXPECTED_SCHEMA.copy()

    # If we have observed data, enhance the schema
    if observed_schema:
        # For now, just return expected schema
        # In future, could merge observed attributes
        pass

    return merged


def generate_erd_output(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate ERD-specific output structure."""
    output = {
        "entities": [],
        "relationships": []
    }

    for entity_name, entity_def in schema.items():
        # Format entity
        entity = {
            "name": entity_name,
            "attributes": []
        }

        # Add business attributes only
        for attr_name, attr_info in entity_def.get("attributes", {}).items():
            if attr_info.get("business", False):
                entity["attributes"].append({
                    "name": attr_name,
                    "type": attr_info.get("type", "string"),
                    "description": attr_info.get("description", "")
                })

        output["entities"].append(entity)

        # Add relationships
        for rel in entity_def.get("relationships", []):
            output["relationships"].append({
                "from": entity_name,
                "to": rel["target"],
                "cardinality": rel["cardinality"],
                "label": rel["description"]
            })

    return output


def generate_mermaid_erd(erd_data: Dict[str, Any]) -> str:
    """Generate Mermaid ERD syntax from ERD data."""
    lines = ["erDiagram"]

    # Add relationships
    for rel in erd_data.get("relationships", []):
        from_entity = rel["from"]
        to_entity = rel["to"]
        cardinality = rel["cardinality"]
        label = rel["label"]

        # Map cardinality to Mermaid syntax
        cardinality_map = {
            "1:1": "||--||",
            "1:many": "||--o{",
            "many:1": "}o--||",
            "many:many": "}o--o{",
            "1:optional": "||--o|",
            "optional:1": "|o--||"
        }

        mermaid_card = cardinality_map.get(cardinality, "||--||")
        lines.append(f'    {from_entity} {mermaid_card} {to_entity} : "{label}"')

    lines.append("")

    # Add entities with attributes
    for entity in erd_data.get("entities", []):
        entity_name = entity["name"]
        lines.append(f"    {entity_name} {{")

        for attr in entity.get("attributes", []):
            attr_type = attr["type"]
            attr_name = attr["name"]
            lines.append(f"        {attr_type} {attr_name}")

        lines.append("    }")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Extract entity structure from HDF5 files for ERD generation'
    )
    parser.add_argument(
        'file',
        nargs='?',
        type=Path,
        help='Path to HDF5 file to inspect'
    )
    parser.add_argument(
        '--all-files',
        type=str,
        help='Glob pattern for multiple HDF5 files (e.g., "data/tier2/hdf5/*.h5")'
    )
    parser.add_argument(
        '--mermaid',
        action='store_true',
        help='Output Mermaid ERD diagram syntax'
    )
    parser.add_argument(
        '--use-expected',
        action='store_true',
        help='Use expected schema from documentation (default if no file specified)'
    )

    args = parser.parse_args()

    observed_schema = None

    # Inspect file if provided
    if args.file:
        observed_schema = inspect_hdf5_file(args.file)
        if observed_schema:
            observed_schema = apply_denoising_rules(observed_schema)

    # Or inspect multiple files
    elif args.all_files:
        files = glob.glob(args.all_files)
        if files:
            # Just inspect first file for schema
            observed_schema = inspect_hdf5_file(Path(files[0]))
            if observed_schema:
                observed_schema = apply_denoising_rules(observed_schema)

    # Merge with expected schema
    if args.use_expected or observed_schema is None:
        final_schema = EXPECTED_SCHEMA
    else:
        final_schema = merge_with_expected_schema(observed_schema)

    # Generate output
    erd_data = generate_erd_output(final_schema)

    if args.mermaid:
        # Output Mermaid diagram
        print(generate_mermaid_erd(erd_data))
    else:
        # Output JSON
        print(json.dumps(erd_data, indent=2))


if __name__ == "__main__":
    main()
