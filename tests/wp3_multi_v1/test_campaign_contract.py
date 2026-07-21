from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from src.python.wp1_catalogue_n3bp_v1 import canonical_section_state


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = VALIDATION / "wp3-multi-candidate-v1"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402


def _module(relative: str, name: str):
    return campaign_module(CAMPAIGN / relative, name)


def test_specification_lock_and_reserve_verify() -> None:
    common = _module("scripts/campaign_common.py", "_wp3_multi_test_common")
    spec_path = CAMPAIGN / "search_spec.json"
    spec = json.loads(spec_path.read_text())
    lock = common.verify_specification_lock(spec_path)
    assert lock["campaign"] == "WP3-MULTI-CAND-v1"
    reserve = common.verify_publication_reserve(
        VALIDATION / "wp3-v2-exploration/sealed/publication_holdout_commitments.json",
        spec["prerequisites"]["sealed_publication_reserve_sha256"],
    )
    assert reserve["status"] == "SEALED_UNEXECUTED"
    assert reserve["source_rows_present"] is False


def test_frozen_corpus_has_exact_disjoint_source_counts() -> None:
    corpus = json.loads((CAMPAIGN / "data/search_corpus.json").read_text())
    cases = corpus["cases"]
    assert len(cases) == 234
    assert sum(case["split"] == "development" for case in cases) == 156
    assert sum(case["split"] == "calibration" for case in cases) == 78
    wp1 = [
        case
        for case in cases
        if case["source_kind"] == "qualified_wp1_periodic_catalogue"
    ]
    assert len(wp1) == 27
    assert len({case["candidate_id"] for case in wp1}) == 27
    assert sum(case["split"] == "development" for case in wp1) == 18
    assert sum(case["split"] == "calibration" for case in wp1) == 9
    assert corpus["sealed_publication_reserve"]["status"] == "SEALED_UNEXECUTED"


def test_corpus_builder_is_byte_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "corpus.json"
    subprocess.run(
        [
            sys.executable,
            str(CAMPAIGN / "scripts/build_corpus.py"),
            "--spec",
            str(CAMPAIGN / "search_spec.json"),
            "--source-corpus",
            str(VALIDATION / "wp3-v2-exploration/data/exploration_corpus.json"),
            "--wp1-catalogue",
            str(
                VALIDATION
                / "wp1-catalogue-n3bp-validation/data/native_catalogue.json"
            ),
            "--commitments",
            str(
                VALIDATION
                / "wp3-v2-exploration/sealed/publication_holdout_commitments.json"
            ),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert output.read_bytes() == (CAMPAIGN / "data/search_corpus.json").read_bytes()


def test_three_chart_operator_blocks_are_equally_normalized() -> None:
    runner = _module("scripts/run_search.py", "_wp3_multi_test_runner")
    state = canonical_section_state(
        1.0,
        1.0,
        -0.37200864,
        1.21800411,
        0.45310805,
        7.53971451,
    )
    corpus = {
        "charts": ["central-1", "central-2", "central-3"],
        "torus_angle_pairs": [[0.0, 0.0], [0.61, -1.17], [-1.17, 0.61]],
        "cases": [
            {
                "case_id": "tiny",
                "split": "development",
                "source_kind": "deterministic_spatial_collocation",
                "source_family": "tiny_family",
                "positions": state[:9].reshape(3, 3).tolist(),
                "velocities": state[9:].reshape(3, 3).tolist(),
                "masses": [1.0, 1.0, 1.0],
                "length_scale": 1.0,
            }
        ],
    }
    rows = runner._build_atlas_rows(
        "development",
        corpus,
        spatial_definitions={},
        spatial_results={},
        wp1_candidates={},
    )
    combined = runner._combine(rows)
    assert rows.values.shape == (9, 1520)
    assert rows.overlap_difference.shape == (6, 1520)
    assert combined.values.shape == (33, 1520)
    assert combined.constraints.shape == (33, 1520)
    for name in combined.block_scales:
        normalized = (
            combined.block_weight_totals[name] * combined.block_scales[name] ** 2
        )
        assert abs(normalized - 0.25) < 2e-15
    assert rows.chart_projection_scaled_max < 2e-14
    assert rows.minimum_pair_separation_scaled_min > 0.1


def test_publication_gate_is_fail_closed_before_candidate_interpretation() -> None:
    gate = _module(
        "scripts/evaluate_publication_gate.py", "_wp3_multi_test_publication_gate"
    )
    bounded_null = gate.decide_publication_gate(
        search_status="COMPLETE_BOUNDED_NULL_RESULT",
        candidate_count=0,
        null_certified=True,
    )
    assert bounded_null["PUBLICATION_GATE"] == "PASS_BOUNDED_NULL_ONLY"
    assert bounded_null["INTERPRETATION_AUTHORIZATION"] == "BOUNDED_NULL_ONLY"
    assert bounded_null["WP4_READY"] == "NOT_TRIGGERED_NO_CANDIDATE"

    unresolved = gate.decide_publication_gate(
        search_status="CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION",
        candidate_count=2,
        null_certified=False,
    )
    assert unresolved["PUBLICATION_GATE"] == "BLOCKED_PENDING_CANDIDATE_RESOLUTION"
    assert unresolved["INTERPRETATION_AUTHORIZATION"] == "PROHIBITED"
    assert unresolved["SEALED_QUALIFICATION"] == "BLOCKED_PENDING_RESOLUTION"

    with pytest.raises(RuntimeError):
        gate.decide_publication_gate(
            search_status="COMPLETE_BOUNDED_NULL_RESULT",
            candidate_count=1,
            null_certified=True,
        )
