#!/usr/bin/env python3
"""
Diagram Validation Script for 4 Abstractions System

This script validates Mermaid diagrams against:
1. Syntax correctness (basic structure)
2. Abstraction-specific rules (C4, Sequence, ERD, State Machine)

Usage:
    python scripts/validate_diagram.py diagrams/context/example.mmd

Returns:
    0 - Validation passed
    1 - Validation failed with errors
    2 - Warnings (passes but with recommendations)
"""

import sys
import re
import os
from pathlib import Path
from typing import Tuple, List, Dict

# ANSI color codes for terminal output
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

def print_result(passed: bool, message: str):
    """Print validation result"""
    symbol = "✓" if passed else "✗"
    color = Colors.GREEN if passed else Colors.RED
    print(f"{color}{symbol} {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def validate_syntax(content: str, diagram_type: str) -> Tuple[bool, List[str]]:
    """Validate basic Mermaid syntax structure"""
    errors = []

    # Check for diagram type declaration
    type_patterns = {
        'c4': r'C4Context',
        'sequence': r'sequenceDiagram',
        'erd': r'erDiagram',
        'state': r'stateDiagram-v2'
    }

    if diagram_type in type_patterns:
        if not re.search(type_patterns[diagram_type], content):
            errors.append(f"Missing {type_patterns[diagram_type]} declaration")

    # Check for unclosed quotes
    single_quotes = content.count("'")
    double_quotes = content.count('"')

    if single_quotes % 2 != 0:
        errors.append("Unclosed single quotes detected")
    if double_quotes % 2 != 0:
        errors.append("Unclosed double quotes detected")

    # Check for basic structure
    lines = content.split('\n')
    non_comment_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('%%')]

    if len(non_comment_lines) < 3:
        errors.append("Diagram appears to be empty or too minimal")

    return len(errors) == 0, errors

def validate_c4_rules(content: str) -> Tuple[bool, List[str], List[str]]:
    """Validate C4 Context diagram rules"""
    errors = []
    warnings = []

    # MUST NOT contain technical details
    technical_terms = [
        (r'\b(HTTP|REST|gRPC|SOAP|WebSocket)\b', "protocol names"),
        (r'\b(AWS|GCP|Azure|Docker|Kubernetes)\b', "vendor names"),
        (r'\b(:\d{1,5})\b', "port numbers"),
        (r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', "IP addresses"),
        (r'\b(VARCHAR|INT|FLOAT|PRIMARY KEY|FOREIGN KEY)\b', "database schema details"),
    ]

    for pattern, term_type in technical_terms:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Contains {term_type} (violates C4 abstraction level)")

    # MUST have System_Boundary
    if 'System_Boundary' not in content and 'Enterprise_Boundary' not in content:
        warnings.append("No System_Boundary defined - consider adding to show internal vs external")

    # Check for plain English descriptions
    if re.search(r'class\s+\w+|def\s+\w+|function\s+\w+', content):
        errors.append("Contains code-level details (use plain English descriptions)")

    return len(errors) == 0, errors, warnings

def validate_sequence_rules(content: str) -> Tuple[bool, List[str], List[str]]:
    """Validate Sequence diagram rules"""
    errors = []
    warnings = []

    # MUST have participants
    if not re.search(r'participant\s+\w+', content):
        errors.append("No participants defined")

    # MUST have error handling (alt/else or opt)
    if not re.search(r'\b(alt|else|opt)\b', content):
        warnings.append("No error handling paths (alt/else) - consider adding unhappy paths")

    # Check for return arrows (-->)
    forward_arrows = len(re.findall(r'->>', content))
    return_arrows = len(re.findall(r'-->', content))

    if forward_arrows > 0 and return_arrows == 0:
        warnings.append("No return arrows (-->) found - consider showing responses")

    # MUST NOT show internal method calls (warning only)
    if re.search(r'self\.|this\.', content):
        warnings.append("Contains internal method references - focus on cross-boundary messages")

    return len(errors) == 0, errors, warnings

def validate_erd_rules(content: str) -> Tuple[bool, List[str], List[str]]:
    """Validate Conceptual ERD rules"""
    errors = []
    warnings = []

    # Remove comments before validation to avoid false positives
    content_no_comments = re.sub(r'%%.*', '', content)

    # MUST NOT contain physical schema details (but allow conceptual types: string, int, float, bool)
    physical_terms = [
        (r'\b(VARCHAR|CHAR\(\d+\)|BIGINT|DECIMAL\(\d+,\d+\)|TIMESTAMP|TEXT|BLOB)\b', "physical data types with sizes"),
        (r'\b(PRIMARY KEY|FOREIGN KEY|INDEX|CONSTRAINT|AUTO_INCREMENT|NOT NULL)\b', "physical constraints"),
        (r'\bcreated_at\b|\bupdated_at\b|\bdeleted_at\b|\bversion\b', "audit columns"),
    ]

    for pattern, term_type in physical_terms:
        if re.search(pattern, content_no_comments, re.IGNORECASE):
            errors.append(f"Contains {term_type} (must be conceptual, not physical)")

    # MUST have cardinality on relationships
    if re.search(r'erDiagram', content):
        # Check for relationship lines with cardinality (||, }o, o{, etc.)
        relationships = re.findall(r'\w+\s+[|{}o]+--[|{}o]+\s+\w+', content)
        if len(relationships) == 0:
            warnings.append("No relationships with cardinality found - use ||, }o, o{, etc.")

    # Check for business naming
    if re.search(r'\b[a-z]+_[a-z]+_tbl\b', content):
        warnings.append("Table naming pattern detected - use business entity names")

    return len(errors) == 0, errors, warnings

def validate_state_rules(content: str) -> Tuple[bool, List[str], List[str]]:
    """Validate State Machine rules"""
    errors = []
    warnings = []

    # MUST have initial state ([*])
    if not re.search(r'\[\*\]\s*-->', content):
        errors.append("Missing initial state transition ([*] -->)")

    # MUST have terminal state(s) (--> [*])
    if not re.search(r'-->\s*\[\*\]', content):
        warnings.append("No terminal states found (--> [*])")

    # Check for meaningful event names (not function names)
    if re.search(r'-->\s*\w+\s*:\s*(def|function|call|execute)\s+\w+', content):
        errors.append("Transition labels use function names - use business event descriptions")

    # Detect potential dead states (state with no outgoing transitions except terminals)
    # This is a simplified check - full analysis would need graph traversal
    states = set(re.findall(r'(\w+)\s+-->', content))
    if len(states) == 0:
        warnings.append("Cannot detect state transitions - verify state machine structure")

    return len(errors) == 0, errors, warnings

def get_diagram_type(filepath: str, content: str) -> str:
    """Determine diagram type from filepath or content"""
    path = Path(filepath)

    # Try to determine from directory
    if 'context' in str(path):
        return 'c4'
    elif 'sequence' in str(path):
        return 'sequence'
    elif 'erd' in str(path):
        return 'erd'
    elif 'state' in str(path):
        return 'state'

    # Fall back to content detection
    if 'C4Context' in content:
        return 'c4'
    elif 'sequenceDiagram' in content:
        return 'sequence'
    elif 'erDiagram' in content:
        return 'erd'
    elif 'stateDiagram' in content:
        return 'state'

    return 'unknown'

def validate_diagram(filepath: str) -> int:
    """Main validation function"""

    # Check file exists
    if not os.path.exists(filepath):
        print_result(False, f"File not found: {filepath}")
        return 1

    # Read content
    with open(filepath, 'r') as f:
        content = f.read()

    # Determine diagram type
    diagram_type = get_diagram_type(filepath, content)

    print_header(f"Diagram Validation: {Path(filepath).name}")
    print(f"Type: {diagram_type.upper()}")
    print(f"File: {filepath}\n")

    # Track overall status
    has_errors = False
    has_warnings = False

    # Step 1: Syntax validation
    print(f"{Colors.BOLD}1. Syntax Validation{Colors.RESET}")
    syntax_passed, syntax_errors = validate_syntax(content, diagram_type)

    if syntax_passed:
        print_result(True, "Mermaid syntax structure valid")
    else:
        print_result(False, "Syntax validation failed")
        for error in syntax_errors:
            print(f"  - {error}")
        has_errors = True

    # Step 2: Rule validation (based on diagram type)
    print(f"\n{Colors.BOLD}2. Abstraction Rule Validation{Colors.RESET}")

    rule_validators = {
        'c4': validate_c4_rules,
        'sequence': validate_sequence_rules,
        'erd': validate_erd_rules,
        'state': validate_state_rules,
    }

    if diagram_type in rule_validators:
        rules_passed, rule_errors, rule_warnings = rule_validators[diagram_type](content)

        if rules_passed and len(rule_warnings) == 0:
            print_result(True, f"{diagram_type.upper()} rules compliant")
        elif rules_passed:
            print_result(True, f"{diagram_type.upper()} rules compliant (with warnings)")
            for warning in rule_warnings:
                print_warning(warning)
            has_warnings = True
        else:
            print_result(False, f"{diagram_type.upper()} rule violations detected")
            for error in rule_errors:
                print(f"  {Colors.RED}✗{Colors.RESET} {error}")
            if rule_warnings:
                print(f"\n  {Colors.BOLD}Additional warnings:{Colors.RESET}")
                for warning in rule_warnings:
                    print_warning(f"  {warning}")
            has_errors = True
            has_warnings = has_warnings or len(rule_warnings) > 0
    else:
        print_warning(f"Unknown diagram type '{diagram_type}' - skipping rule validation")
        has_warnings = True

    # Step 3: Header metadata check
    print(f"\n{Colors.BOLD}3. Metadata Validation{Colors.RESET}")

    has_header_comment = re.search(r'%%\s*(Extracted|Generated|Created)', content)
    has_sources = re.search(r'%%\s*Sources?:', content, re.IGNORECASE)

    if has_header_comment:
        print_result(True, "Header comment with extraction metadata found")
    else:
        print_warning("No header comment documenting extraction date/sources")
        has_warnings = True

    # Final summary
    print_header("Validation Summary")

    if has_errors:
        print_result(False, "VALIDATION FAILED - Diagram has errors")
        return 1
    elif has_warnings:
        print_result(True, "VALIDATION PASSED WITH WARNINGS")
        print(f"{Colors.YELLOW}Review warnings and consider improvements{Colors.RESET}")
        return 2
    else:
        print_result(True, "VALIDATION PASSED - Diagram meets all criteria")
        return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_diagram.py <diagram.mmd>")
        sys.exit(1)

    filepath = sys.argv[1]
    exit_code = validate_diagram(filepath)
    sys.exit(exit_code)
