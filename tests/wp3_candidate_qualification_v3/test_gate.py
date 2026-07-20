from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-candidate-qualification-v3"


def _json(relative: str):
    return json.loads((CAMPAIGN / relative).read_text(encoding="utf-8"))


def test_zero_candidate_gate_keeps_reserve_sealed() -> None:
    decision = _json("results/candidate_qualification_decision.json")
    assert decision["status"] == "NOT_TRIGGERED_NO_CANDIDATE"
    assert decision["candidate_count"] == 0
    assert decision["null_result_spectral_certificate"][
        "certifies_no_training_eligible_direction"
    ]
    assert decision["candidate_specific_lock"] == "NOT_CREATED"
    assert decision["sealed_execution"] == "PROHIBITED"
    assert decision["publication_reserve_status"] == "SEALED_UNEXECUTED"
    assert decision["wp4_candidate_validation"] == "BLOCKED"


def test_protocol_binds_complete_immutable_search_chain() -> None:
    protocol = _json("qualification_protocol.json")
    prerequisite = protocol["search_prerequisite"]
    assert prerequisite["qualification_id"].startswith("WP3-UP-CAND-v3-")
    assert all(
        len(prerequisite[name]) == 64
        for name in (
            "lock_sha256",
            "lock_file_sha256",
            "record_sha256",
            "record_payload_sha256",
            "results_sha256",
            "gate_sha256",
        )
    )
    required = " ".join(protocol["required_if_triggered"]).lower()
    assert "poisson" in required
    assert "independent" in required
    assert "sealed reserve" in required
