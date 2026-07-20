from __future__ import annotations

import json
from pathlib import Path

from src.python.wp4_upstairs_v3.cli import (
    LOCK_PATH,
    RECORD_PATH,
    RESULTS_PATH,
    ROOT,
    _spec,
    verify,
)
from src.python.wp4_upstairs_v3 import (
    POSITIVE_CONTROLS,
    deterministic_cases,
    evaluate_readiness,
)
from src.python.wp4_upstairs_v3.integrity import load_json, verify_signed_lock
from src.python.upstairs_ks import regularized_hamiltonian


SPEC = ROOT / "validation-external/wp4-upstairs-readiness-v3/qualification_spec.json"


def test_v3_spec_binds_authoritative_wp3_null() -> None:
    spec = load_json(SPEC)
    wp3 = spec["prerequisites"]["wp3_upstairs_search"]
    assert spec["campaign"] == "WP4-UP-READY-v3"
    assert wp3["qualification_id"].startswith("WP3-UP-CAND-v3-")
    assert wp3["search_record_sha256"]
    assert wp3["candidate_decision_sha256"]
    assert "bounded-null" in spec["claim"]


def test_deterministic_states_are_on_declared_shell() -> None:
    cases = deterministic_cases()
    assert len(cases) == 6
    for case in cases:
        assert abs(case.state.xi) < 5e-13
        assert abs(regularized_hamiltonian(case.state, case.parameters, case.energy)) < 5e-13


def test_raw_gauntlet_discriminates_controls() -> None:
    raw = evaluate_readiness(_spec())
    metrics = raw["metrics"]
    assert tuple(raw["controls"]["positive"]) == POSITIVE_CONTROLS
    assert metrics["positive_controls_accepted"] == 5
    assert metrics["negative_controls_rejected"] == 2
    assert metrics["known_functional_rank_min"] == 5
    assert metrics["dependent_rank_increment_max"] == 0
    assert metrics["publication_reserve_open_attempts"] == 0


def test_frozen_v3_record_separates_readiness_from_candidate_work() -> None:
    lock = verify_signed_lock(LOCK_PATH, ROOT)
    record = verify()
    assert record["qualification_id"] == lock["qualification_id"]
    assert record["harness_status"] == "HARNESS_READY"
    assert record["candidate_validation_status"] == "CANDIDATE_NOT_TRIGGERED"
    assert record["sealed_qualification_status"] == "NOT_TRIGGERED"
    assert record["morales_ramis_status"] == "NOT_TRIGGERED"
    assert record["publication_reserve_status"] == "SEALED_UNEXECUTED"
    assert record["candidate_count"] == 0
    assert all(gate["passed"] for gate in record["gates"])
    assert RESULTS_PATH.is_file() and RECORD_PATH.is_file()


def test_v3_artifacts_contain_no_candidate_or_reserve_payload() -> None:
    record_text = RECORD_PATH.read_text(encoding="utf-8")
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert "candidate_expression" not in record_text
    assert "reserve_rows" not in record_text
    assert results["metrics"]["candidate_validation_triggered"] == 0
    assert results["metrics"]["morales_ramis_triggered"] == 0
    assert results["metrics"]["publication_reserve_open_attempts"] == 0
