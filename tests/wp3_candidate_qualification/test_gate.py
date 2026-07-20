from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-candidate-qualification"


def test_zero_candidate_gate_keeps_reserve_sealed() -> None:
    decision = json.loads((CAMPAIGN / "results/candidate_qualification_decision.json").read_text())
    assert decision["status"] == "NOT_TRIGGERED_NO_CANDIDATE"
    assert decision["candidate_count"] == 0
    assert decision["candidate_specific_lock"] == "NOT_CREATED"
    assert decision["sealed_execution"] == "PROHIBITED"
    assert decision["publication_reserve_status"] == "SEALED_UNEXECUTED"
    assert decision["wp4_candidate_validation"] == "BLOCKED"


def test_protocol_requires_candidate_specific_evidence() -> None:
    protocol = json.loads((CAMPAIGN / "qualification_protocol.json").read_text())
    required = " ".join(protocol["required_if_triggered"]).lower()
    assert "poisson" in required
    assert "independent" in required
    assert "sealed reserve" in required
