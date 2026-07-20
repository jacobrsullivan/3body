"""Integrity and smoke tests for WP1Q-N3BP-SPATIAL-v1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-spatial-validation"
CORPUS = CAMPAIGN / "data/qualification_corpus.json"
REFERENCE = CAMPAIGN / "scripts/spatial_reference.py"
COMMITMENTS = (
    ROOT
    / "validation-external/wp3-v2-exploration/sealed/publication_holdout_commitments.json"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reference_module():
    spec = importlib.util.spec_from_file_location("wp3_spatial_reference", REFERENCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_frozen_corpus_is_balanced_and_bound_to_verbatim_source_rows() -> None:
    corpus = _json(CORPUS)
    rows = {
        hashlib.sha256(line.encode("ascii")).hexdigest()
        for line in (CAMPAIGN / "sources/brutus_selected_rows.txt")
        .read_text(encoding="ascii")
        .splitlines()
        if line and not line.startswith("#")
    }
    assert len(corpus["cases"]) == 84
    expected = {
        ("development", "equal_mass_plummer"): 24,
        ("development", "mass_4_2_1_plummer"): 24,
        ("calibration", "equal_mass_plummer"): 12,
        ("calibration", "mass_4_2_1_plummer"): 12,
        ("holdout", "equal_mass_plummer"): 6,
        ("holdout", "mass_4_2_1_plummer"): 6,
    }
    observed = {
        key: sum(
            case["split"] == key[0] and case["source_family"] == key[1]
            for case in corpus["cases"]
        )
        for key in expected
    }
    assert observed == expected
    assert all(case["source_line_sha256"] in rows for case in corpus["cases"])


def test_arbitrary_precision_oracle_converges_on_short_smoke_interval() -> None:
    case = _json(CORPUS)["cases"][0]
    reference = _reference_module()
    times = np.array([0.0, 0.125, 0.25])
    low = reference.integrate_taylor(
        case, times, precision_bits=96, tolerance="1e-18"
    )
    high = reference.integrate_taylor(
        case, times, precision_bits=128, tolerance="1e-24"
    )
    np.testing.assert_allclose(
        low["states_float64"], high["states_float64"], rtol=0.0, atol=2e-14
    )
    assert float(high["relative_energy_drift_decimal"]) < 1e-20


def test_publication_reserve_contains_commitments_but_no_source_states() -> None:
    payload = _json(COMMITMENTS)
    forbidden = {
        "source_case_id",
        "source_index",
        "initial_positions_decimal",
        "initial_velocities_decimal",
        "brutus_final_positions_decimal",
        "brutus_final_velocities_decimal",
    }
    assert payload["status"] == "SEALED_UNEXECUTED"
    assert len(payload["commitments"]) == payload["case_count"] == 24
    assert all(not (set(item) & forbidden) for item in payload["commitments"])
    assert all(item["status"] == "SEALED_UNEXECUTED" for item in payload["commitments"])
