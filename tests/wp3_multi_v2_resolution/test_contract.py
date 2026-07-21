from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from src.python.n3bp_qualification import (
    InertialState,
    SystemParameters,
    newtonian_rhs,
    total_energy,
)
from src.python.wp3_multi_v2 import evaluate_multi_features


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = VALIDATION / "wp3-multi-candidate-v2-resolution"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402


def _module(relative: str, name: str):
    return campaign_module(CAMPAIGN / relative, name)


def test_specification_lock_candidate_metadata_and_reserve_are_intact() -> None:
    common = _module("scripts/campaign_common.py", "_resolution_test_common")
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = common.verify_specification_lock(CAMPAIGN / "qualification_spec.json")
    assert lock["candidate_expression_accessed_before_lock"] is False
    metadata = common.verify_candidate_metadata(spec)
    assert metadata["candidate_subspace_count"] == 1
    assert metadata["candidate_dimension"] == 1
    assert metadata["mode_rank"] == 1
    reserve = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    assert reserve["status"] == "SEALED_UNEXECUTED"
    assert reserve["source_rows_present"] is False


def test_challenge_corpus_is_byte_deterministic_and_unsealed(tmp_path: Path) -> None:
    output = tmp_path / "challenge.json"
    subprocess.run(
        [
            sys.executable,
            str(CAMPAIGN / "scripts/build_challenge_corpus.py"),
            "--spec",
            str(CAMPAIGN / "qualification_spec.json"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    expected = CAMPAIGN / "data/challenge_corpus.json"
    assert output.read_bytes() == expected.read_bytes()
    corpus = json.loads(expected.read_text())
    assert len(corpus["cases"]) == 192
    assert corpus["development_challenge_count"] == 128
    assert corpus["calibration_challenge_count"] == 64
    assert corpus["spatial_case_count"] == 96
    assert corpus["planar_case_count"] == 96
    assert corpus["publication_reserve_used"] is False


def test_mpmath_reference_matches_production_on_challenge_case() -> None:
    reference = _module(
        "reference/mpmath_features.py", "_resolution_test_mpmath_reference"
    )
    source = (CAMPAIGN / "reference/mpmath_features.py").read_text()
    assert "src.python.wp3_multi_v2" not in source
    case = json.loads((CAMPAIGN / "data/challenge_corpus.json").read_text())["cases"][0]
    positions = np.asarray(
        [[float(Fraction(value)) for value in row] for row in case["positions"]]
    )
    velocities = np.asarray(
        [[float(Fraction(value)) for value in row] for row in case["velocities"]]
    )
    parameters = SystemParameters([float(Fraction(value)) for value in case["masses"]])
    state = InertialState.from_components(positions, velocities)
    clock = np.prod(
        [
            np.linalg.norm(positions[first] - positions[second])
            for first, second in ((0, 1), (1, 2), (2, 0))
        ]
    )
    tangent = clock * newtonian_rhs(0.0, state, parameters)
    production = evaluate_multi_features(
        state,
        tangent,
        parameters,
        fixed_energy=total_energy(state, parameters),
    )
    values, derivatives = reference.evaluate(case, dps=80)
    reference_values = np.asarray([float(value) for value in values])
    reference_derivatives = np.asarray([float(value) for value in derivatives])
    assert (
        np.max(
            np.abs(production.values - reference_values)
            / np.maximum(1.0, np.abs(reference_values))
        )
        < 2e-14
    )
    assert (
        np.max(
            np.abs(production.derivatives - reference_derivatives)
            / np.maximum(1.0, np.abs(reference_derivatives))
        )
        < 2e-13
    )


def test_resolution_decision_is_fail_closed() -> None:
    resolver = _module("scripts/run_resolution.py", "_resolution_test_runner")
    assert (
        resolver.decide_resolution(
            numeric_gates_pass=False,
            known_direction=False,
            formula_resolved=False,
        )
        == "REJECTED_NUMERICAL_OR_GENERALIZATION_ARTIFACT"
    )
    assert (
        resolver.decide_resolution(
            numeric_gates_pass=True,
            known_direction=True,
            formula_resolved=True,
        )
        == "EXACT_KNOWN_DIRECTION"
    )
    assert (
        resolver.decide_resolution(
            numeric_gates_pass=True,
            known_direction=False,
            formula_resolved=True,
        )
        == "SURVIVES_RESOLUTION"
    )


def test_generalized_backend_reconstruction_finds_synthetic_null_direction() -> None:
    resolver = _module("scripts/run_resolution.py", "_resolution_test_backend")
    rng = np.random.default_rng(20260721)
    values = rng.normal(size=(80, 6))
    derivatives = rng.normal(size=(80, 6))
    derivatives[:, 1] = 0.0
    known = np.zeros(6)
    known[0] = 1.0
    groups = tuple(f"group-{index // 10}" for index in range(80))
    families = tuple(f"family-{(index // 10) % 2}" for index in range(80))
    for driver in ("numpy", "gesdd", "gesvd"):
        result = resolver.generalized_direction(
            values,
            derivatives,
            groups,
            families,
            known,
            driver=driver,
            value_rank_relative_tolerance=1e-11,
        )
        direction = result["raw_coefficients"]
        expected = np.zeros(6)
        expected[1] = 1.0
        projection = abs(float(direction @ expected)) / np.linalg.norm(direction)
        assert projection > 0.999999
        assert result["generalized_singular_value"] < 1e-12
