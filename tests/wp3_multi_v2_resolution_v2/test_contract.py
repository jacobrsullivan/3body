from __future__ import annotations

from pathlib import Path

import mpmath
import numpy as np

from validation_external_import import campaign_module


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-multi-candidate-v2-resolution-v2"
RUNNER = campaign_module(
    CAMPAIGN / "scripts/run_resolution.py",
    "_test_wp3_multi_v2_resolution_v2_runner",
)
COMMON = campaign_module(
    CAMPAIGN / "scripts/campaign_common.py",
    "_test_wp3_multi_v2_resolution_v2_common",
)
REFERENCE = campaign_module(
    CAMPAIGN / "reference/physical_l2.py",
    "_test_wp3_multi_v2_resolution_v2_reference",
)


def test_corrected_specification_lock_verifies() -> None:
    lock = COMMON.verify_specification_lock(CAMPAIGN / "qualification_spec.json")
    assert lock["campaign"] == "WP3-MULTI-CAND-v2-RES-v2"


def test_response_equivalence_ignores_coefficient_representative() -> None:
    values = np.asarray([[1.0, 1.0], [2.0, 2.0], [4.0, 4.0]])
    weights = np.asarray([0.2, 0.3, 0.5])
    first = values @ np.asarray([1.0, 0.0])
    second = values @ np.asarray([0.0, -3.0])
    assert np.isclose(
        RUNNER.centered_response_projection(first, second, weights), 1.0
    )
    assert np.dot(np.asarray([1.0, 0.0]), np.asarray([0.0, -3.0])) == 0.0


def test_zero_intercept_scale_and_residual() -> None:
    known = np.asarray([1.0, 2.0, 5.0])
    candidate = -7.5 * known
    weights = np.full(3, 1.0 / 3.0)
    scale = RUNNER.fit_zero_intercept_scale(candidate, known, weights)
    assert np.isclose(scale, -7.5)
    assert (
        RUNNER.relative_weighted_rms(
            candidate - scale * known, candidate, weights
        )
        < 1e-14
    )


def test_source_disjoint_physical_l2() -> None:
    case = {
        "masses": ["1", "2", "3"],
        "positions": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "velocities": [["0", "1", "0"], ["0", "0", "1"], ["1", "0", "0"]],
    }
    with mpmath.workdps(80):
        assert REFERENCE.evaluate(case, dps=80) == mpmath.mpf("14")


def test_superseded_v1_is_pinned_without_claim_authority() -> None:
    prerequisites = COMMON.verify_prerequisites(
        __import__("json").loads((CAMPAIGN / "qualification_spec.json").read_text())
    )
    assert prerequisites["superseded_qualification_id"].startswith(
        "WP3-MULTI-CAND-v2-RES-v1-"
    )
