from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.python.wp4_upstairs_v2.cli import LOCK_PATH, RECORD_PATH, RESULTS_PATH, ROOT, verify
from src.python.wp4_upstairs_v2.harness import (
    POSITIVE_CONTROLS,
    deterministic_cases,
    evaluate_readiness,
)
from src.python.wp4_upstairs_v2.integrity import load_json, verify_signed_lock
from src.python.upstairs_ks import regularized_hamiltonian


SPEC = ROOT / "validation-external/wp4-upstairs-readiness-v2/qualification_spec.json"


def test_deterministic_states_are_on_the_declared_shell() -> None:
    cases = deterministic_cases()
    assert len(cases) == 6
    assert {tuple(case.parameters.masses) for case in cases} == {
        (1.0, 1.0, 1.0),
        (4.0, 2.0, 1.0),
        (2.0, 3.0, 5.0),
    }
    for case in cases:
        assert abs(case.state.xi) < 5e-13
        assert abs(regularized_hamiltonian(case.state, case.parameters, case.energy)) < 5e-13


def test_raw_gauntlet_discriminates_controls() -> None:
    raw = evaluate_readiness(load_json(SPEC))
    metrics = raw["metrics"]
    assert tuple(raw["controls"]["positive"]) == POSITIVE_CONTROLS
    assert all(
        value["decision"] == "ACCEPT_KNOWN_CONTROL"
        for value in raw["controls"]["positive"].values()
    )
    assert metrics["positive_control_lie_scaled_max"] < 2e-9
    assert metrics["negative_coordinate_lie_scaled_min"] > 1e-4
    assert metrics["known_functional_rank_min"] == 5
    assert metrics["dependent_rank_increment_max"] == 0
    assert metrics["nonconserved_rank_increment_min"] == 1
    assert metrics["positive_controls_accepted"] == 5
    assert metrics["negative_controls_rejected"] == 2
    assert raw["controls"]["negative"]["dependent_2K_minus_3Xi"]["conservation_precheck_passed"]
    assert metrics["publication_reserve_open_attempts"] == 0


def test_frozen_record_separates_readiness_from_candidate_work() -> None:
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


def test_artifacts_contain_no_candidate_expression_or_reserve_payload() -> None:
    record_text = RECORD_PATH.read_text(encoding="utf-8")
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert "candidate_expression" not in record_text
    assert "reserve_rows" not in record_text
    assert results["metrics"]["candidate_validation_triggered"] == 0
    assert results["metrics"]["morales_ramis_triggered"] == 0
    assert results["metrics"]["publication_reserve_open_attempts"] == 0


def test_all_written_paths_stay_in_the_disjoint_scope() -> None:
    allowed = (
        "src/python/wp4_upstairs_v2/",
        "tests/wp4_upstairs_v2/",
        "validation-external/wp4-upstairs-readiness-v2/",
        "notes/wp4-upstairs-v2-readiness-",
    )
    status = __import__("subprocess").check_output(
        ["git", "status", "--short"], cwd=ROOT, text=True
    )
    wp4_lines = [line for line in status.splitlines() if "wp4" in line.lower()]
    for line in wp4_lines:
        path = line[3:]
        assert path.startswith(allowed), line
