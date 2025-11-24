#!/usr/bin/env python3
"""
Diagram Drift Detection Script for 4 Abstractions System

This script compares current diagrams against golden master baselines to detect
architectural drift (changes in system structure, relationships, participants, etc.)

Usage:
    python scripts/compare_diagrams.py --baseline golden
    python scripts/compare_diagrams.py --diagram diagrams/context/example.mmd

Returns:
    0 - No significant drift detected
    1 - Significant drift detected (flagged for review)
    2 - Minor cosmetic changes only
"""

import sys
import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from difflib import unified_diff

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header(text: str, color: str = Colors.BLUE):
    """Print formatted header"""
    print(f"\n{color}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{text:^70}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")

def extract_c4_elements(content: str) -> Dict[str, Set[str]]:
    """Extract C4 diagram elements (people, systems, relationships)"""
    elements = {
        'people': set(),
        'systems': set(),
        'external_systems': set(),
        'relationships': set(),
    }

    # Extract Person
    people = re.findall(r'Person\((\w+),', content)
    elements['people'].update(people)

    # Extract System
    systems = re.findall(r'System\((\w+),', content)
    elements['systems'].update(systems)

    # Extract System_Ext
    ext_systems = re.findall(r'System_Ext\((\w+),', content)
    elements['external_systems'].update(ext_systems)

    # Extract Rel
    relationships = re.findall(r'Rel\((\w+),\s*(\w+),', content)
    elements['relationships'].update([f"{src}->{dst}" for src, dst in relationships])

    return elements

def extract_sequence_elements(content: str) -> Dict[str, Set[str]]:
    """Extract sequence diagram elements (participants, messages)"""
    elements = {
        'participants': set(),
        'messages': set(),
        'alt_blocks': set(),
    }

    # Extract participants
    participants = re.findall(r'participant\s+(\w+)', content)
    elements['participants'].update(participants)

    # Extract messages (->>, -->, ->>)
    messages = re.findall(r'(\w+)\s*-[->]+\s*(\w+)\s*:', content)
    elements['messages'].update([f"{src}->{dst}" for src, dst in messages])

    # Extract alt/else blocks
    alt_blocks = re.findall(r'alt\s+(.+?)(?=\n)', content)
    elements['alt_blocks'].update(alt_blocks)

    return elements

def extract_erd_elements(content: str) -> Dict[str, Set[str]]:
    """Extract ERD elements (entities, relationships)"""
    elements = {
        'entities': set(),
        'relationships': set(),
        'attributes': {},
    }

    # Extract entities (entity name followed by {)
    entities = re.findall(r'(\w+)\s*\{', content)
    elements['entities'].update(entities)

    # Extract relationships
    relationships = re.findall(r'(\w+)\s+[|{}o]+--[|{}o]+\s+(\w+)\s*:\s*"([^"]+)"', content)
    elements['relationships'].update([f"{e1}-{e2}:{rel}" for e1, e2, rel in relationships])

    # Extract attributes for each entity
    for entity in elements['entities']:
        pattern = rf'{entity}\s*\{{([^}}]+)\}}'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            attrs = re.findall(r'\s+(\w+)\s+(\w+)', match.group(1))
            elements['attributes'][entity] = set([f"{typ} {name}" for typ, name in attrs])

    return elements

def extract_state_elements(content: str) -> Dict[str, Set[str]]:
    """Extract state machine elements (states, transitions)"""
    elements = {
        'states': set(),
        'transitions': set(),
        'initial_state': None,
        'terminal_states': set(),
    }

    # Extract states
    states = re.findall(r'(\w+)\s+-->', content)
    states.extend(re.findall(r'-->\s+(\w+)', content))
    elements['states'].update([s for s in states if s != '[*]'])

    # Extract transitions
    transitions = re.findall(r'(\w+)\s+-->\s+(\w+)\s*:', content)
    elements['transitions'].update([f"{s1}->{s2}" for s1, s2 in transitions])

    # Extract initial state
    initial = re.search(r'\[\*\]\s+-->\s+(\w+)', content)
    if initial:
        elements['initial_state'] = initial.group(1)

    # Extract terminal states
    terminals = re.findall(r'(\w+)\s+-->\s+\[\*\]', content)
    elements['terminal_states'].update(terminals)

    return elements

def detect_diagram_type(filepath: str) -> str:
    """Detect diagram type from filepath (returns directory name, not diagram type)"""
    path_str = str(filepath).lower()
    if 'context' in path_str:
        return 'context'
    elif 'sequence' in path_str:
        return 'sequence'
    elif 'erd' in path_str:
        return 'erd'
    elif 'state' in path_str:
        return 'state'
    return 'unknown'

def compare_elements(baseline: Dict, current: Dict, element_type: str) -> Dict:
    """Compare two sets of elements and return changes"""
    changes = {
        'added': {},
        'removed': {},
        'modified': {},
    }

    for key in baseline.keys():
        if isinstance(baseline[key], set):
            baseline_set = baseline[key]
            current_set = current.get(key, set())

            added = current_set - baseline_set
            removed = baseline_set - current_set

            if added:
                changes['added'][key] = added
            if removed:
                changes['removed'][key] = removed
        elif isinstance(baseline[key], dict):
            # Compare dictionaries (e.g., attributes in ERD)
            for entity, attrs in baseline[key].items():
                current_attrs = current.get(key, {}).get(entity, set())
                added = current_attrs - attrs
                removed = attrs - current_attrs

                if added:
                    if key not in changes['added']:
                        changes['added'][key] = {}
                    changes['added'][key][entity] = added
                if removed:
                    if key not in changes['removed']:
                        changes['removed'][key] = {}
                    changes['removed'][key][entity] = removed

    return changes

def is_significant_drift(changes: Dict, diagram_type: str) -> bool:
    """Determine if changes represent significant architectural drift"""

    # Significant changes that require review
    significant_keys = {
        'c4': ['systems', 'external_systems', 'people'],
        'sequence': ['participants', 'alt_blocks'],
        'erd': ['entities', 'relationships'],
        'state': ['states', 'terminal_states', 'transitions'],
    }

    sig_keys = significant_keys.get(diagram_type, [])

    for change_type in ['added', 'removed']:
        for key, values in changes.get(change_type, {}).items():
            if key in sig_keys and len(values) > 0:
                return True

    return False

def compare_diagrams(baseline_path: str, current_path: str) -> Tuple[bool, Dict]:
    """Compare baseline and current diagrams"""

    # Read files
    with open(baseline_path, 'r') as f:
        baseline_content = f.read()

    with open(current_path, 'r') as f:
        current_content = f.read()

    # Detect diagram type (directory name)
    dir_type = detect_diagram_type(baseline_path)

    # Map directory name to diagram type for extractors
    type_mapping = {
        'context': 'c4',
        'sequence': 'sequence',
        'erd': 'erd',
        'state': 'state',
    }

    diagram_type = type_mapping.get(dir_type, dir_type)

    # Extract elements based on type
    extractors = {
        'c4': extract_c4_elements,
        'sequence': extract_sequence_elements,
        'erd': extract_erd_elements,
        'state': extract_state_elements,
    }

    if diagram_type not in extractors:
        print(f"{Colors.YELLOW}⚠ Unknown diagram type, skipping drift detection{Colors.RESET}")
        return False, {}

    baseline_elements = extractors[diagram_type](baseline_content)
    current_elements = extractors[diagram_type](current_content)

    # Compare elements
    changes = compare_elements(baseline_elements, current_elements, diagram_type)

    # Determine if drift is significant
    significant = is_significant_drift(changes, diagram_type)

    return significant, changes

def print_drift_report(diagram_name: str, significant: bool, changes: Dict):
    """Print formatted drift detection report"""

    print_header(f"Drift Detection: {diagram_name}")

    has_changes = any(len(v) > 0 for v in changes.get('added', {}).values()) or \
                  any(len(v) > 0 for v in changes.get('removed', {}).values())

    if not has_changes:
        print(f"{Colors.GREEN}✓ No drift detected - diagram matches golden master{Colors.RESET}")
        return 0

    print(f"{Colors.BOLD}Changes Detected:{Colors.RESET}\n")

    # Print added elements
    if changes.get('added'):
        print(f"{Colors.YELLOW}Added Elements:{Colors.RESET}")
        for element_type, values in changes['added'].items():
            if isinstance(values, dict):
                for entity, attrs in values.items():
                    for attr in attrs:
                        print(f"  + {element_type}::{entity}::{attr}")
            else:
                for value in values:
                    print(f"  + {element_type}: {value}")

    # Print removed elements
    if changes.get('removed'):
        print(f"\n{Colors.RED}Removed Elements:{Colors.RESET}")
        for element_type, values in changes['removed'].items():
            if isinstance(values, dict):
                for entity, attrs in values.items():
                    for attr in attrs:
                        print(f"  - {element_type}::{entity}::{attr}")
            else:
                for value in values:
                    print(f"  - {element_type}: {value}")

    # Print verdict
    print(f"\n{Colors.BOLD}Drift Assessment:{Colors.RESET}")
    if significant:
        print(f"{Colors.RED}✗ SIGNIFICANT DRIFT DETECTED - Requires review{Colors.RESET}")
        return 1
    else:
        print(f"{Colors.YELLOW}⚠ Minor cosmetic changes only{Colors.RESET}")
        return 2

def main():
    parser = argparse.ArgumentParser(description='Detect architectural drift in Mermaid diagrams')
    parser.add_argument('--baseline', default='golden', help='Baseline directory (default: golden)')
    parser.add_argument('--diagram', help='Specific diagram to check (optional)')
    parser.add_argument('--all', action='store_true', help='Check all diagrams')

    args = parser.parse_args()

    base_dir = Path('/home/user/3body/diagrams')
    golden_dir = base_dir / args.baseline

    if not golden_dir.exists():
        print(f"{Colors.RED}✗ Baseline directory not found: {golden_dir}{Colors.RESET}")
        return 1

    exit_code = 0

    if args.diagram:
        # Check specific diagram
        diagram_path = Path(args.diagram)
        diagram_type = detect_diagram_type(diagram_path)
        golden_path = golden_dir / diagram_type / diagram_path.name

        if not golden_path.exists():
            print(f"{Colors.YELLOW}⚠ No golden master found for {diagram_path.name}{Colors.RESET}")
            return 2

        significant, changes = compare_diagrams(str(golden_path), str(diagram_path))
        result = print_drift_report(diagram_path.name, significant, changes)
        exit_code = max(exit_code, result)

    elif args.all:
        # Check all diagrams
        diagram_types = ['context', 'sequence', 'erd', 'state']

        for dtype in diagram_types:
            current_dir = base_dir / dtype
            golden_subdir = golden_dir / dtype

            if not current_dir.exists() or not golden_subdir.exists():
                continue

            for current_file in current_dir.glob('*.mmd'):
                golden_file = golden_subdir / current_file.name

                if not golden_file.exists():
                    print(f"{Colors.YELLOW}⚠ No golden master for {current_file.name}{Colors.RESET}")
                    continue

                significant, changes = compare_diagrams(str(golden_file), str(current_file))
                result = print_drift_report(current_file.name, significant, changes)
                exit_code = max(exit_code, result)
                print()  # Blank line between diagrams

    else:
        print("Usage: python scripts/compare_diagrams.py --all  OR  --diagram <path>")
        return 1

    return exit_code

if __name__ == '__main__':
    sys.exit(main())
