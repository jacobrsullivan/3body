"""WP3-UP-CAND-v1 campaign contract tests."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-upstairs-candidate"
RESERVE = ROOT / "validation-external/wp3-v2-exploration/sealed/publication_holdout_commitments.json"


def _json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def test_spec_freezes_degree_three_scope_and_candidate_gate() -> None:
    spec = _json(CAMPAIGN / "search_spec.json")
    assert spec["library"]["polynomial_total_degree_max"] == 3
    assert spec["library"]["monomial_count"] == 679
    assert spec["library"]["total_feature_count"] == 685
    assert spec["staged_policy"]["WP4_READY"].startswith("Can be triggered only")


def test_corpus_exposes_no_holdout_or_reserve_rows() -> None:
    corpus = _json(CAMPAIGN / "data/search_corpus.json")
    assert {case["split"] for case in corpus["cases"]} == {"development", "calibration"}
    reserve = _json(RESERVE)
    forbidden = {
        "source_case_id", "source_index", "initial_positions_decimal",
        "initial_velocities_decimal", "brutus_final_positions_decimal",
        "brutus_final_velocities_decimal",
    }
    assert reserve["status"] == "SEALED_UNEXECUTED"
    assert all(not (forbidden & set(item)) for item in reserve["commitments"])


def test_search_execution_requires_presearch_lock() -> None:
    shell = (CAMPAIGN / "run_search.sh").read_text(encoding="utf-8")
    runner = (CAMPAIGN / "scripts/run_search.py").read_text(encoding="utf-8")
    assert "verify_qualification.py" in shell
    assert 'parser.add_argument("--lock", required=True)' in runner
    assert "SEALED_QUALIFICATION" in runner
