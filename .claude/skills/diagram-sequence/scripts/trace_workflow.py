#!/usr/bin/env python3
"""
Extract workflow sequences from Python code for Sequence diagram generation.

This script analyzes:
1. Test files to identify canonical workflow patterns
2. Function call chains to map component interactions
3. Try/except blocks to identify error paths

Usage:
    python trace_workflow.py [test_file_or_directory] [--workflow WorkflowName]

Output:
    JSON representation of sequence diagram participants, messages, and flows
"""

import ast
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict


class WorkflowTracer(ast.NodeVisitor):
    """Extract workflow patterns from test files and implementation code."""

    def __init__(self, module_mappings: Dict[str, str] = None):
        self.participants = set()
        self.messages = []
        self.current_function = None
        self.current_participant = "TestRunner"
        self.message_sequence = []

        # Map module/class names to participant names
        self.module_mappings = module_mappings or DEFAULT_MODULE_MAPPINGS

    def visit_FunctionDef(self, node):
        """Track test functions and workflow methods."""
        old_function = self.current_function
        self.current_function = node.name

        # If this is a test function, it's our entry point
        if node.name.startswith('test_'):
            self.current_participant = "TestRunner"
            self.participants.add("TestRunner")

        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node):
        """Extract function calls as messages between participants."""
        # Determine the target participant and method
        target_info = self._extract_call_info(node)

        if target_info:
            participant = target_info['participant']
            method = target_info['method']
            is_return = target_info.get('is_return', False)

            # Add participants
            self.participants.add(participant)

            # Record message
            message = {
                'from': self.current_participant,
                'to': participant,
                'method': method,
                'lineno': node.lineno,
                'args': self._extract_args(node),
                'is_return': is_return
            }

            self.messages.append(message)

            # If this is an assignment, the next calls might be from the result
            # For now, keep current participant context

        self.generic_visit(node)

    def visit_Try(self, node):
        """Extract error handling paths (alt/else blocks for sequence diagrams)."""
        # Process try block (happy path)
        for stmt in node.body:
            self.visit(stmt)

        # Process except blocks (unhappy paths)
        for handler in node.handlers:
            # Mark this as error path
            error_type = self._get_exception_type(handler.type)

            # Visit handler body
            for stmt in handler.body:
                self.visit(stmt)

        # Process else and finally
        for stmt in node.orelse:
            self.visit(stmt)

        for stmt in node.finalbody:
            self.visit(stmt)

    def _extract_call_info(self, node: ast.Call) -> Dict[str, Any]:
        """Extract participant and method from a function call."""
        if isinstance(node.func, ast.Attribute):
            # Method call: obj.method()
            obj = self._extract_object_name(node.func.value)
            method = node.func.attr

            # Map object to participant
            participant = self._map_to_participant(obj, method)

            return {
                'participant': participant,
                'method': method,
                'object': obj
            }

        elif isinstance(node.func, ast.Name):
            # Function call: function()
            func_name = node.func.id

            # Map function to participant (assume it's a module function)
            participant = self._map_function_to_participant(func_name)

            return {
                'participant': participant,
                'method': func_name
            }

        return None

    def _extract_object_name(self, node):
        """Extract object name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._extract_object_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            # Result of a call
            info = self._extract_call_info(node)
            if info:
                return info['method']
        return "object"

    def _map_to_participant(self, obj_name: str, method_name: str) -> str:
        """Map object name to participant (component) name."""
        # Check if object name matches a known participant mapping
        for pattern, participant in self.module_mappings.items():
            if pattern.lower() in obj_name.lower() or pattern.lower() in method_name.lower():
                return participant

        # Default: use object name as participant
        return obj_name.title().replace('_', '')

    def _map_function_to_participant(self, func_name: str) -> str:
        """Map function name to participant."""
        # Check mappings
        for pattern, participant in self.module_mappings.items():
            if pattern.lower() in func_name.lower():
                return participant

        # Default
        return "Utility"

    def _extract_args(self, node: ast.Call) -> List[str]:
        """Extract argument names/values from call."""
        args = []

        for arg in node.args:
            if isinstance(arg, ast.Name):
                args.append(arg.id)
            elif isinstance(arg, ast.Constant):
                args.append(str(arg.value))
            else:
                args.append("arg")

        return args

    def _get_exception_type(self, node):
        """Get exception type name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        else:
            return "Exception"


# Default mapping of code patterns to participant names
DEFAULT_MODULE_MAPPINGS = {
    # Storage
    'h5py': 'DataStore',
    'load_trajectory': 'DataStore',
    'load_': 'DataStore',
    'store': 'DataStore',
    'hdf5': 'DataStore',

    # Integration
    'integrat': 'IntegrationEngine',
    'rebound': 'IntegrationEngine',
    'ias15': 'IntegrationEngine',

    # Validation
    'analytical_vetting': 'AnalyticalVetting',
    'validate': 'ValidationGauntlet',
    'vetting': 'AnalyticalVetting',
    'morales_ramis': 'MoralesRamisValidator',
    'kovacic': 'MoralesRamisValidator',
    'monte_carlo': 'MonteCarloValidator',

    # Discovery
    'symbolic': 'SymbolicRegressor',
    'pysr': 'SymbolicRegressor',
    'discover': 'DiscoverySystem',

    # Geometry
    'transform': 'GeometricTools',
    'coordinate': 'GeometricTools',
    'lift': 'GeometricTools',
}


def analyze_workflow_file(filepath: Path, module_mappings: Dict[str, str] = None) -> Dict[str, Any]:
    """Analyze a Python file for workflow patterns."""
    try:
        with open(filepath, 'r') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))

        # Extract workflow
        tracer = WorkflowTracer(module_mappings)
        tracer.visit(tree)

        # Build result
        result = {
            'file': str(filepath),
            'participants': sorted(list(tracer.participants)),
            'messages': tracer.messages,
            'message_count': len(tracer.messages)
        }

        return result

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        return None


def analyze_workflow_directory(dirpath: Path, pattern: str = "test_*.py") -> List[Dict[str, Any]]:
    """Analyze test files in a directory."""
    all_results = []

    for filepath in dirpath.rglob(pattern):
        if filepath.is_file():
            result = analyze_workflow_file(filepath)
            if result and result.get('messages'):
                all_results.append(result)

    return all_results


def generate_mermaid_sequence(workflow: Dict[str, Any], title: str = None) -> str:
    """Generate Mermaid sequence diagram from workflow trace."""
    lines = ["sequenceDiagram"]

    if title:
        lines.append(f"    title {title}")

    # Add participants
    participants = workflow.get('participants', [])
    for participant in participants:
        # Use aliases for long names
        alias = participant[:20]
        lines.append(f"    participant {alias}")

    lines.append("")

    # Add messages
    messages = workflow.get('messages', [])

    for msg in messages:
        from_p = msg['from'][:20]
        to_p = msg['to'][:20]
        method = msg['method']
        args = msg.get('args', [])

        # Build message label
        if args:
            arg_str = ', '.join(args[:2])  # Limit to first 2 args
            label = f"{method}({arg_str})"
        else:
            label = method

        # Determine arrow type
        if msg.get('is_return', False):
            arrow = "-->"
        else:
            arrow = "->>"

        lines.append(f"    {from_p}{arrow}{to_p}: {label}")

    return "\n".join(lines)


def create_validation_gauntlet_workflow() -> Dict[str, Any]:
    """Create the canonical validation gauntlet workflow from documentation."""
    return {
        'workflow_name': 'Validation Gauntlet',
        'participants': [
            'User',
            'ValidationGauntlet',
            'DataStore',
            'AnalyticalVetting',
            'MoralesRamisValidator',
            'MonteCarloValidator'
        ],
        'messages': [
            {'from': 'User', 'to': 'ValidationGauntlet', 'method': 'validate_candidate', 'args': ['integral', 'tier=2']},
            {'from': 'ValidationGauntlet', 'to': 'DataStore', 'method': 'load_trajectories', 'args': ['tier=2']},
            {'from': 'DataStore', 'to': 'ValidationGauntlet', 'method': 'return', 'args': ['trajectories'], 'is_return': True},
            {'from': 'ValidationGauntlet', 'to': 'AnalyticalVetting', 'method': 'validate', 'args': ['integral', 'trajectories']},
            {'from': 'AnalyticalVetting', 'to': 'ValidationGauntlet', 'method': 'return', 'args': ['result'], 'is_return': True},
            # Conditional: if passed
            {'from': 'ValidationGauntlet', 'to': 'MoralesRamisValidator', 'method': 'test_integrability', 'args': ['integral']},
            {'from': 'MoralesRamisValidator', 'to': 'ValidationGauntlet', 'method': 'return', 'args': ['result'], 'is_return': True},
            # Conditional: if passed
            {'from': 'ValidationGauntlet', 'to': 'MonteCarloValidator', 'method': 'statistical_validation', 'args': ['integral']},
            {'from': 'MonteCarloValidator', 'to': 'ValidationGauntlet', 'method': 'return', 'args': ['result'], 'is_return': True},
            {'from': 'ValidationGauntlet', 'to': 'User', 'method': 'return', 'args': ['VALIDATED'], 'is_return': True},
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description='Extract workflow sequences from Python code for sequence diagrams'
    )
    parser.add_argument(
        'path',
        nargs='?',
        type=Path,
        help='Path to test file or directory to analyze'
    )
    parser.add_argument(
        '--workflow',
        type=str,
        help='Use predefined workflow (e.g., "validation_gauntlet")'
    )
    parser.add_argument(
        '--mermaid',
        action='store_true',
        help='Output Mermaid sequence diagram syntax'
    )
    parser.add_argument(
        '--title',
        type=str,
        help='Diagram title'
    )

    args = parser.parse_args()

    # Check for predefined workflows
    if args.workflow:
        if args.workflow.lower() == 'validation_gauntlet':
            workflow = create_validation_gauntlet_workflow()

            if args.mermaid:
                title = args.title or workflow.get('workflow_name', 'Workflow')
                print(generate_mermaid_sequence(workflow, title))
            else:
                print(json.dumps(workflow, indent=2))
            return
        else:
            print(f"Unknown workflow: {args.workflow}", file=sys.stderr)
            print("Available workflows: validation_gauntlet", file=sys.stderr)
            sys.exit(1)

    # Analyze path if provided
    if args.path:
        if args.path.is_file():
            result = analyze_workflow_file(args.path)
            results = [result] if result else []
        elif args.path.is_dir():
            results = analyze_workflow_directory(args.path)
        else:
            print(f"Error: Path {args.path} not found", file=sys.stderr)
            sys.exit(1)

        # Output
        if args.mermaid and results:
            # Generate diagram for first workflow
            workflow = results[0]
            title = args.title or f"Workflow from {workflow['file']}"
            print(generate_mermaid_sequence(workflow, title))
        else:
            # Output JSON
            output = {
                'analyzed_files': len(results),
                'total_messages': sum(r.get('message_count', 0) for r in results),
                'workflows': results
            }
            print(json.dumps(output, indent=2))
    else:
        print("Error: Must specify either --workflow or path to analyze", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
