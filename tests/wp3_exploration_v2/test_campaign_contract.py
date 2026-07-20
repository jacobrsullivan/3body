"""Evidence and fail-closed gate checks for WP3-EXP-v2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-v2-exploration"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_search_inputs_pin_qualified_prerequisites_and_sealed_reserve() -> None:
    specification = _json(CAMPAIGN / "exploration_spec.json")
    definitions = (
        (
            "wp1_spatial_n3bp",
            ROOT
            / "validation-external/wp3-spatial-validation-v2/reports/wp3_spatial_v2_qualification_record.json",
        ),
        (
            "wp2_threebody_flow",
            ROOT
            / "validation-external/wp2-threebody-flow-validation/reports/wp2_threebody_flow_qualification_record.json",
        ),
    )
    for name, path in definitions:
        record = _json(path)
        expected = specification["prerequisites"][name]
        assert record["status"] == "PASS"
        assert record["qualification_id"] == expected["qualification_id"]
        assert record["lock_sha256"] == expected["lock_sha256"]
        assert _sha(path) == expected["record_sha256"]
    commitments = CAMPAIGN / "sealed/publication_holdout_commitments.json"
    assert _sha(commitments) == specification["prerequisites"][
        "sealed_publication_reserve_sha256"
    ]


def test_exploration_corpus_contains_no_qualification_or_publication_holdout() -> None:
    corpus = _json(CAMPAIGN / "data/exploration_corpus.json")
    assert len(corpus["cases"]) == 207
    assert {case["split"] for case in corpus["cases"]} == {
        "development",
        "calibration",
    }
    assert all(case["split"] != "holdout" for case in corpus["cases"])
    assert sum(
        case["source_kind"] == "qualified_external_trajectory"
        for case in corpus["cases"]
    ) == 72
    assert sum(
        case["source_kind"] == "deterministic_spatial_collocation"
        for case in corpus["cases"]
    ) == 135


def test_bounded_null_result_passes_search_gate_without_interpretation() -> None:
    result_path = CAMPAIGN / "results/exploration_results.json"
    result = _json(result_path)
    gate = _json(CAMPAIGN / "results/staged_gate.json")
    assert result["status"] == "COMPLETE_BOUNDED_NULL_RESULT"
    assert result["interpretation_status"] == "PROHIBITED"
    assert result["search"]["candidate_count"] == 0
    assert result["search"]["numerical_nullity_at_candidate_threshold"] == 0
    assert min(result["search"]["post_projection_singular_values"]) > 1e-10
    assert result["sealed_publication_reserve"]["status"] == "SEALED_UNEXECUTED"
    assert gate["result_sha256"] == _sha(result_path)
    assert gate["SEARCH_READY"]["status"] == "PASS"
    assert gate["CANDIDATE_READY"]["status"] == "NOT_TRIGGERED"
    assert gate["PUBLICATION_READY"]["status"] == "BLOCKED"
    assert gate["PUBLICATION_READY"]["interpretation_authorized"] is False


def test_implementation_snapshot_recomputes() -> None:
    result = _json(CAMPAIGN / "results/exploration_results.json")
    for relative_name, expected_hash in result["implementation_snapshot"][
        "file_hashes"
    ].items():
        assert _sha(ROOT / relative_name) == expected_hash


def test_bobs_mini_cross_runtime_parity_passes() -> None:
    parity = _json(CAMPAIGN / "reports/wp3_v2_bobs_mini_parity.json")
    assert parity["status"] == "PASS"
    assert parity["comparison"]["runtime"]["python"] == "3.11.15"
    assert parity["reference"]["runtime"]["python"] == "3.13.2"
    assert len(parity["checks"]) == 12
    assert all(check["passed"] for check in parity["checks"])
