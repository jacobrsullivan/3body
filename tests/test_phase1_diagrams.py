"""
Test Suite for Phase 1: 4 Abstraction Agent Implementation

This test suite validates that Phase 1 deliverables are complete:
1. All 4 diagram types generated (C4, Sequence, ERD, State)
2. All diagrams have valid Mermaid syntax structure
3. All diagrams follow abstraction-specific rules
4. Flight Recorder documentation is complete
"""

import os
import pytest
from pathlib import Path


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DIAGRAMS_DIR = PROJECT_ROOT / "diagrams"


class TestPhase1Infrastructure:
    """Test that Phase 1 infrastructure is in place."""

    def test_diagrams_directory_exists(self):
        """Verify diagrams directory exists."""
        assert DIAGRAMS_DIR.exists(), "diagrams/ directory should exist"

    def test_subdirectories_exist(self):
        """Verify all diagram type subdirectories exist."""
        subdirs = ["context", "sequence", "erd", "state"]
        for subdir in subdirs:
            path = DIAGRAMS_DIR / subdir
            assert path.exists(), f"diagrams/{subdir}/ should exist"

    def test_flight_recorder_exists(self):
        """Verify Flight Recorder log exists."""
        log_path = DIAGRAMS_DIR / "session_log.md"
        assert log_path.exists(), "diagrams/session_log.md should exist"


class TestPhase1Diagrams:
    """Test that all 4 diagrams are generated."""

    def test_c4_context_diagram_exists(self):
        """Verify C4 Context diagram exists."""
        diagram_path = DIAGRAMS_DIR / "context" / "threebody_system_context.mmd"
        assert diagram_path.exists(), "C4 Context diagram should exist"
        assert diagram_path.stat().st_size > 0, "C4 Context diagram should not be empty"

    def test_sequence_diagram_exists(self):
        """Verify Sequence diagram exists."""
        diagram_path = DIAGRAMS_DIR / "sequence" / "validation_gauntlet.mmd"
        assert diagram_path.exists(), "Sequence diagram should exist"
        assert diagram_path.stat().st_size > 0, "Sequence diagram should not be empty"

    def test_erd_diagram_exists(self):
        """Verify ERD diagram exists."""
        diagram_path = DIAGRAMS_DIR / "erd" / "trajectory_validation_model.mmd"
        assert diagram_path.exists(), "ERD diagram should exist"
        assert diagram_path.stat().st_size > 0, "ERD diagram should not be empty"

    def test_state_diagram_exists(self):
        """Verify State Machine diagram exists."""
        diagram_path = DIAGRAMS_DIR / "state" / "candidate_lifecycle.mmd"
        assert diagram_path.exists(), "State Machine diagram should exist"
        assert diagram_path.stat().st_size > 0, "State Machine diagram should not be empty"


class TestMermaidSyntax:
    """Test that diagrams have valid Mermaid syntax structure."""

    def test_c4_context_syntax(self):
        """Verify C4 Context diagram has correct syntax."""
        diagram_path = DIAGRAMS_DIR / "context" / "threebody_system_context.mmd"
        content = diagram_path.read_text()

        # Check for required C4 elements
        assert "C4Context" in content, "Should have C4Context declaration"
        assert "title" in content, "Should have title"
        assert "Person(" in content, "Should have Person actors"
        assert "System(" in content, "Should have System components"
        assert "System_Ext(" in content, "Should have External Systems"
        assert "Rel(" in content, "Should have Relationships"

    def test_sequence_diagram_syntax(self):
        """Verify Sequence diagram has correct syntax."""
        diagram_path = DIAGRAMS_DIR / "sequence" / "validation_gauntlet.mmd"
        content = diagram_path.read_text()

        # Check for required sequence elements
        assert "sequenceDiagram" in content, "Should have sequenceDiagram declaration"
        assert "participant" in content, "Should have participant declarations"
        assert "->>" in content or "-->" in content, "Should have message arrows"
        assert "alt" in content, "Should have alt blocks for branching"
        assert "end" in content, "Should have end statements"

    def test_erd_syntax(self):
        """Verify ERD has correct syntax."""
        diagram_path = DIAGRAMS_DIR / "erd" / "trajectory_validation_model.mmd"
        content = diagram_path.read_text()

        # Check for required ERD elements
        assert "erDiagram" in content, "Should have erDiagram declaration"
        assert "||--" in content or "}o--" in content, "Should have relationships with cardinality"
        assert "{" in content and "}" in content, "Should have entity attribute blocks"

    def test_state_diagram_syntax(self):
        """Verify State Machine diagram has correct syntax."""
        diagram_path = DIAGRAMS_DIR / "state" / "candidate_lifecycle.mmd"
        content = diagram_path.read_text()

        # Check for required state machine elements
        assert "stateDiagram-v2" in content, "Should have stateDiagram-v2 declaration"
        assert "[*]" in content, "Should have initial/terminal state markers"
        assert "-->" in content, "Should have state transitions"


class TestAbstractionRules:
    """Test that diagrams follow abstraction-specific rules."""

    def test_c4_no_technical_details(self):
        """Verify C4 Context has no technical details (protocols, ports, vendors)."""
        diagram_path = DIAGRAMS_DIR / "context" / "threebody_system_context.mmd"
        content = diagram_path.read_text().lower()

        # Check for violations
        violations = []
        if "http" in content or "rest" in content or "grpc" in content:
            violations.append("Contains protocol names (HTTP, REST, gRPC)")
        if ":808" in content or ":500" in content or ":300" in content:
            violations.append("Contains port numbers")
        if "aws" in content or "docker" in content or "kubernetes" in content:
            violations.append("Contains vendor names")

        assert len(violations) == 0, f"C4 rule violations: {violations}"

    def test_sequence_has_error_paths(self):
        """Verify Sequence diagram includes error handling."""
        diagram_path = DIAGRAMS_DIR / "sequence" / "validation_gauntlet.mmd"
        content = diagram_path.read_text()

        # Check for error scenarios
        assert "alt" in content, "Should have alt blocks for branching"
        assert "REJECTED" in content or "fail" in content.lower(), "Should show failure scenarios"

    def test_erd_no_physical_schema(self):
        """Verify ERD has no physical schema details."""
        diagram_path = DIAGRAMS_DIR / "erd" / "trajectory_validation_model.mmd"
        content = diagram_path.read_text()

        # Check for violations (case-insensitive)
        violations = []
        if "VARCHAR" in content or "PRIMARY KEY" in content or "FOREIGN KEY" in content:
            violations.append("Contains physical schema details (VARCHAR, PRIMARY KEY, etc.)")
        if "created_at" in content or "updated_at" in content:
            violations.append("Contains audit columns (created_at, updated_at)")

        assert len(violations) == 0, f"ERD rule violations: {violations}"

    def test_state_has_terminal_states(self):
        """Verify State Machine has terminal states."""
        diagram_path = DIAGRAMS_DIR / "state" / "candidate_lifecycle.mmd"
        content = diagram_path.read_text()

        # Check for terminal states
        assert "--> [*]" in content, "Should have transitions to terminal state [*]"


class TestFlightRecorder:
    """Test Flight Recorder documentation completeness."""

    def test_flight_recorder_has_phase1_entry(self):
        """Verify Flight Recorder has Phase 1 extraction logs."""
        log_path = DIAGRAMS_DIR / "session_log.md"
        content = log_path.read_text()

        assert "Phase 1" in content, "Should document Phase 1 extractions"

    def test_flight_recorder_has_all_diagram_entries(self):
        """Verify Flight Recorder documents all 4 diagram extractions."""
        log_path = DIAGRAMS_DIR / "session_log.md"
        content = log_path.read_text()

        # Check for all diagram type entries
        assert "C4 Context Extraction" in content, "Should document C4 extraction"
        assert "Sequence Diagram Extraction" in content, "Should document Sequence extraction"
        assert "Conceptual ERD Extraction" in content, "Should document ERD extraction"
        assert "State Machine Extraction" in content, "Should document State extraction"

    def test_flight_recorder_has_metadata(self):
        """Verify Flight Recorder includes extraction metadata."""
        log_path = DIAGRAMS_DIR / "session_log.md"
        content = log_path.read_text()

        # Check for required metadata sections
        assert "Sources Examined" in content, "Should document sources examined"
        assert "Extraction Method" in content, "Should document extraction method"
        assert "Assumptions Made" in content or "Assumptions:" in content, "Should document assumptions"


class TestPhase1SuccessCriteria:
    """Test Phase 1 success criteria from implementation plan."""

    def test_all_4_diagrams_generated(self):
        """Verify all 4 diagram types generated (1 per abstraction)."""
        diagrams = [
            DIAGRAMS_DIR / "context" / "threebody_system_context.mmd",
            DIAGRAMS_DIR / "sequence" / "validation_gauntlet.mmd",
            DIAGRAMS_DIR / "erd" / "trajectory_validation_model.mmd",
            DIAGRAMS_DIR / "state" / "candidate_lifecycle.mmd",
        ]

        for diagram in diagrams:
            assert diagram.exists(), f"{diagram.name} should exist"
            assert diagram.stat().st_size > 500, f"{diagram.name} should have substantial content"

    def test_diagrams_have_metadata_headers(self):
        """Verify all diagrams include metadata headers."""
        diagrams = [
            DIAGRAMS_DIR / "context" / "threebody_system_context.mmd",
            DIAGRAMS_DIR / "sequence" / "validation_gauntlet.mmd",
            DIAGRAMS_DIR / "erd" / "trajectory_validation_model.mmd",
            DIAGRAMS_DIR / "state" / "candidate_lifecycle.mmd",
        ]

        for diagram in diagrams:
            content = diagram.read_text()
            assert "%% Generated:" in content, f"{diagram.name} should have generation date"
            assert "%% Sources:" in content, f"{diagram.name} should document sources"
            assert "%% Architect:" in content, f"{diagram.name} should identify architect"

    def test_flight_recorder_complete(self):
        """Verify Flight Recorder has complete documentation."""
        log_path = DIAGRAMS_DIR / "session_log.md"
        assert log_path.exists(), "Flight Recorder should exist"

        content = log_path.read_text()
        assert len(content) > 5000, "Flight Recorder should have substantial documentation"
        assert "Phase 1 Summary" in content, "Should have Phase 1 summary"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
