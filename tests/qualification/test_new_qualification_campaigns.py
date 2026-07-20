"""Integrity checks for the bounded WP2KSQ and WP1Q-N3BP campaigns."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WP2_ROOT = REPO_ROOT / "validation-external" / "wp2-ks-validation"
N3BP_ROOT = REPO_ROOT / "validation-external" / "wp1-n3bp-validation"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_campaign_corpora_have_unique_nonempty_splits():
    for root in (WP2_ROOT, N3BP_ROOT):
        corpus = load_json(root / "data" / "qualification_corpus.json")
        case_ids = [case["case_id"] for case in corpus["cases"]]
        assert len(case_ids) == len(set(case_ids))
        assert {case["split"] for case in corpus["cases"]} == {
            "development",
            "calibration",
            "holdout",
        }
        assert all(case["split"] != "holdout" for case in corpus["cases"][:2])


def test_wp2_collision_free_conics_obey_frozen_bounds():
    spec = load_json(WP2_ROOT / "qualification_spec.json")
    corpus = load_json(WP2_ROOT / "data" / "qualification_corpus.json")
    minimum = spec["corpus"]["collision_free_bounds"]["periapsis_min"]
    maximum_eccentricity = spec["corpus"]["collision_free_bounds"][
        "eccentricity_max"
    ]
    for case in corpus["cases"]:
        if case["case_type"] != "elliptic":
            continue
        elements = case["elements"]
        assert elements["eccentricity"] <= maximum_eccentricity
        assert (
            elements["semi_major_axis"] * (1.0 - elements["eccentricity"])
            >= minimum
        )


def test_n3bp_selected_source_rows_match_corpus_decimals():
    corpus = load_json(N3BP_ROOT / "data" / "qualification_corpus.json")
    source_cases = {
        case["source_line"]: case
        for case in corpus["cases"]
        if case["case_type"] == "sjtu_periodic"
    }
    rows = {}
    source_path = N3BP_ROOT / "sources" / "sjtu_selected_rows.txt"
    for line in source_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        rows[int(fields[0])] = fields[1:]
    assert rows.keys() == source_cases.keys()
    for line_number, fields in rows.items():
        case = source_cases[line_number]
        assert fields == [
            *case["masses"],
            case["x1"],
            case["v1"],
            case["v2"],
            case["period"],
            case["source_stability_label"],
        ]


def test_n3bp_manifest_pins_the_observed_upstream_digest():
    manifest = load_json(N3BP_ROOT / "sources" / "manifest.json")
    snapshot = manifest["external_snapshot"]
    assert snapshot["commit"] == "b96b0193579a9952299d710ed616f529bb7cf898"
    assert snapshot["upstream_sha256"] == (
        "9c06eedc41b537b2ed926217cdf149d9f"
        "808a21866148ea3d89b9eb3c6069fd4"
    )
    selected = (N3BP_ROOT / "sources" / snapshot["selected_rows_path"]).read_bytes()
    assert hashlib.sha256(selected).hexdigest() == snapshot["selected_rows_sha256"]
