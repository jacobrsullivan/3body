#!/usr/bin/env python3
"""
Extract state machines and transitions from Python code using AST analysis.

This script searches for:
1. Enum definitions representing states
2. Conditional logic showing state transitions
3. State assignment patterns

Usage:
    python extract_state_transitions.py [file_or_directory] [--entity EntityName]

Output:
    JSON representation of state machines with states and transitions
"""

import ast
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict


class StateEnumExtractor(ast.NodeVisitor):
    """Extract Enum definitions that represent states."""

    def __init__(self):
        self.enums = {}
        self.current_class = None

    def visit_ClassDef(self, node):
        """Visit class definitions to find Enums."""
        # Check if this class inherits from Enum
        is_enum = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Enum':
                is_enum = True
            elif isinstance(base, ast.Attribute) and base.attr == 'Enum':
                is_enum = True

        if is_enum:
            # Extract enum members
            enum_name = node.name
            members = []

            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            # Get the string value if possible
                            value = self._extract_value(item.value)
                            members.append({
                                'name': target.id,
                                'value': value,
                                'lineno': item.lineno
                            })

            self.enums[enum_name] = {
                'name': enum_name,
                'members': members,
                'lineno': node.lineno
            }

        self.generic_visit(node)

    def _extract_value(self, node):
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.Name):
            return node.id
        else:
            return None


class StateTransitionExtractor(ast.NodeVisitor):
    """Extract state transition patterns from code."""

    def __init__(self, state_enum_members: Set[str]):
        self.state_members = state_enum_members
        self.transitions = []
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Track current function context."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Assign(self, node):
        """Find state assignments (state = NewState)."""
        # Look for assignments to variables named 'state', 'status', 'stage', etc.
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ['state', 'status', 'stage', 'verdict']:
                # Check if value is a state enum member
                new_state = self._extract_state_reference(node.value)
                if new_state:
                    self.transitions.append({
                        'to_state': new_state,
                        'context': self.current_function,
                        'lineno': node.lineno,
                        'type': 'assignment'
                    })

        self.generic_visit(node)

    def visit_If(self, node):
        """Find conditional transitions (if condition: state = X else: state = Y)."""
        # Extract condition description
        condition = self._extract_condition_desc(node.test)

        # Find state transitions in if branch
        if_states = self._find_states_in_block(node.body)

        # Find state transitions in else branch
        else_states = self._find_states_in_block(node.orelse)

        # Record conditional transitions
        for state in if_states:
            self.transitions.append({
                'to_state': state,
                'condition': condition,
                'context': self.current_function,
                'lineno': node.lineno,
                'type': 'conditional_if'
            })

        for state in else_states:
            self.transitions.append({
                'to_state': state,
                'condition': f"NOT ({condition})",
                'context': self.current_function,
                'lineno': node.lineno,
                'type': 'conditional_else'
            })

        self.generic_visit(node)

    def _extract_state_reference(self, node):
        """Extract state enum member reference."""
        if isinstance(node, ast.Attribute):
            # e.g., ValidationStage.DISCOVERED
            if isinstance(node.value, ast.Name):
                return node.attr
        elif isinstance(node, ast.Name):
            # Direct reference
            if node.id in self.state_members:
                return node.id
        return None

    def _find_states_in_block(self, block: List[ast.stmt]) -> List[str]:
        """Find state assignments in a code block."""
        states = []
        for stmt in block:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id in ['state', 'status', 'stage', 'verdict']:
                        state = self._extract_state_reference(stmt.value)
                        if state:
                            states.append(state)
        return states

    def _extract_condition_desc(self, node):
        """Extract a human-readable description of a condition."""
        if isinstance(node, ast.Compare):
            left = self._node_to_string(node.left)
            ops = [self._op_to_string(op) for op in node.ops]
            comparators = [self._node_to_string(comp) for comp in node.comparators]
            return f"{left} {' '.join(ops)} {' '.join(comparators)}"
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            operand = self._extract_condition_desc(node.operand)
            return f"NOT {operand}"
        elif isinstance(node, ast.Attribute):
            return f"{self._node_to_string(node.value)}.{node.attr}"
        else:
            return "condition"

    def _node_to_string(self, node):
        """Convert AST node to string representation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._node_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return "expr"

    def _op_to_string(self, op):
        """Convert comparison operator to string."""
        op_map = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        return op_map.get(type(op), "?")


def analyze_file(filepath: Path) -> Dict[str, Any]:
    """Analyze a Python file for state machines."""
    try:
        with open(filepath, 'r') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))

        # First pass: Extract enums
        enum_extractor = StateEnumExtractor()
        enum_extractor.visit(tree)

        # Second pass: Extract transitions for each enum
        results = {
            'file': str(filepath),
            'state_machines': []
        }

        for enum_name, enum_info in enum_extractor.enums.items():
            # Get enum member names
            member_names = {m['name'] for m in enum_info['members']}

            # Extract transitions
            transition_extractor = StateTransitionExtractor(member_names)
            transition_extractor.visit(tree)

            # Build state machine
            state_machine = {
                'entity': enum_name,
                'states': enum_info['members'],
                'transitions': transition_extractor.transitions,
                'file': str(filepath),
                'lineno': enum_info['lineno']
            }

            results['state_machines'].append(state_machine)

        return results

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        return None


def analyze_directory(dirpath: Path, pattern: str = "*.py") -> List[Dict[str, Any]]:
    """Analyze all Python files in a directory."""
    all_results = []

    for filepath in dirpath.rglob(pattern):
        if filepath.is_file():
            result = analyze_file(filepath)
            if result and result.get('state_machines'):
                all_results.append(result)

    return all_results


def generate_mermaid_state_diagram(state_machine: Dict[str, Any], entity_name: str = None) -> str:
    """Generate Mermaid state diagram from extracted state machine."""
    lines = ["stateDiagram-v2"]

    entity = entity_name or state_machine.get('entity', 'StateMachine')

    # Get all states
    states = {s['name'] for s in state_machine.get('states', [])}

    # Track which states we've seen in transitions
    seen_in_transitions = set()

    # Add initial transition (assume first state is initial)
    if states:
        first_state = list(states)[0]
        lines.append(f"    [*] --> {first_state}")
        seen_in_transitions.add(first_state)

    # Group transitions by (from_state, to_state)
    transition_map = defaultdict(list)

    transitions = state_machine.get('transitions', [])

    # Build transition graph
    # We need to infer from_state by tracking the flow
    current_state = list(states)[0] if states else None

    for trans in transitions:
        to_state = trans['to_state']
        condition = trans.get('condition', '')

        if current_state and to_state != current_state:
            transition_map[(current_state, to_state)].append(condition)
            seen_in_transitions.add(to_state)
            current_state = to_state

    # Add transitions
    for (from_state, to_state), conditions in transition_map.items():
        if conditions and conditions[0]:
            label = conditions[0][:50]  # Truncate long conditions
            lines.append(f"    {from_state} --> {to_state} : {label}")
        else:
            lines.append(f"    {from_state} --> {to_state}")

    # Add terminal states
    terminal_states = states - seen_in_transitions
    for state in terminal_states:
        if state != list(states)[0]:  # Don't add [*] for initial state
            lines.append(f"    {state} --> [*]")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Extract state machines from Python code using AST analysis'
    )
    parser.add_argument(
        'path',
        nargs='?',
        type=Path,
        default=Path('src/python/validation'),
        help='Path to Python file or directory to analyze'
    )
    parser.add_argument(
        '--entity',
        type=str,
        help='Filter for specific entity/enum name'
    )
    parser.add_argument(
        '--mermaid',
        action='store_true',
        help='Output Mermaid state diagram syntax'
    )

    args = parser.parse_args()

    # Analyze path
    if args.path.is_file():
        result = analyze_file(args.path)
        results = [result] if result else []
    elif args.path.is_dir():
        results = analyze_directory(args.path)
    else:
        print(f"Error: Path {args.path} not found", file=sys.stderr)
        sys.exit(1)

    # Filter by entity if specified
    if args.entity:
        filtered_results = []
        for result in results:
            filtered_machines = [
                sm for sm in result.get('state_machines', [])
                if sm['entity'] == args.entity
            ]
            if filtered_machines:
                filtered_results.append({
                    'file': result['file'],
                    'state_machines': filtered_machines
                })
        results = filtered_results

    # Output
    if args.mermaid:
        # Output Mermaid diagram for first state machine found
        for result in results:
            for sm in result.get('state_machines', []):
                print(generate_mermaid_state_diagram(sm))
                break  # Only first one
            break
    else:
        # Output JSON
        output = {
            'analyzed_files': len(results),
            'state_machines_found': sum(len(r.get('state_machines', [])) for r in results),
            'results': results
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
