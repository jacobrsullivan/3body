from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from src.python.wp2_multi_v1 import DEFAULT_COLLISION_FLOOR


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp2-multi-validation"
sys.path.insert(0, str(ROOT / "validation-external"))


def test_locked_specification_is_bounded_and_fail_closed() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    boundary = spec["evidence_boundary"].lower()
    assert spec["specification_status"] == "LOCKED_BY_SEPARATE_RECORD"
    assert "triple collision" in boundary
    assert "integrability" in boundary
    assert spec["model"]["time_law"] == "dt/ds=g=R1*R2*R3 in every chart."
    assert spec["model"]["gauge_group"].startswith("T2=S1xS1")
    assert spec["gates"]["structural_triple_collision_qualified"] == 0
    assert DEFAULT_COLLISION_FLOOR == spec["corpus"]["triple_collision_floor"]


def test_corpus_allocation_matches_the_locked_claim() -> None:
    path = CAMPAIGN / "data/qualification_corpus.json"
    if not path.exists():
        return
    corpus = json.loads(path.read_text())
    assert corpus["category_counts"] == {
        "exact_passage": 9,
        "generic": 18,
        "near_binary": 18,
    }
    assert corpus["split_counts"] == {
        "calibration": 12,
        "development": 21,
        "holdout": 12,
    }
    assert len({case["case_id"] for case in corpus["cases"]}) == 45
    assert corpus["exact_passage_channel_counts"] == {
        "12": 3,
        "23": 3,
        "31": 3,
    }
    for case in corpus["cases"]:
        assert case["physical_channel"] in {"12", "23", "31"}
    for split in ("development", "calibration", "holdout"):
        assert {
            case["physical_channel"]
            for case in corpus["cases"]
            if case["split"] == split
        } == {"12", "23", "31"}


def test_evaluator_rejects_missing_category_evidence() -> None:
    path = CAMPAIGN / "scripts/evaluate_qualification.py"
    definition = importlib.util.spec_from_file_location("wp2_multi_evaluator", path)
    assert definition is not None and definition.loader is not None
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)

    with pytest.raises(RuntimeError, match="no cases"):
        module._maximum([], "trajectory_scaled")
    with pytest.raises(RuntimeError, match="missing"):
        module._maximum([{"case_id": "missing", "metrics": {}}], "trajectory_scaled")


def test_prequalification_executes_structural_and_switch_contracts() -> None:
    result_path = CAMPAIGN / "results/development.json"
    if not result_path.exists():
        return
    result = json.loads(result_path.read_text())
    assert result["structural"]["case_count"] == 64
    assert result["structural"]["dimension_and_constraint_count_pass_rate"] == 1.0
    noncollision = [
        case for case in result["cases"] if case["category"] != "exact_passage"
    ]
    assert noncollision
    assert all(case["metrics"]["switch_policy_pass"] == 1.0 for case in noncollision)
    exact = [case for case in result["cases"] if case["category"] == "exact_passage"]
    assert exact
    assert all(case["metrics"]["collision_probe_convergence"] == 1.0 for case in exact)
    assert all(case["metrics"]["collision_spinor_crossing"] == 1.0 for case in exact)


def test_committed_evidence_finalizer_recomputes_gate_decisions(
    tmp_path: Path,
) -> None:
    path = ROOT / "validation-external/finalize_committed_qualification.py"
    definition = importlib.util.spec_from_file_location("committed_finalizer", path)
    assert definition is not None and definition.loader is not None
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    evaluation = tmp_path / "evaluation.json"
    payload = {
        "status": "PASS",
        "gates": [
            {
                "name": "bounded",
                "observed": 1.0,
                "comparator": "<=",
                "threshold": 2.0,
                "passed": True,
            }
        ],
    }
    evaluation.write_text(json.dumps(payload), encoding="utf-8")
    module._verify_evaluation(evaluation)

    payload["gates"][0]["passed"] = False
    evaluation.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="inconsistent gate"):
        module._verify_evaluation(evaluation)
