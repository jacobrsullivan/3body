from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp2-up-validation-v2"


def _json(relative: str):
    return json.loads((CAMPAIGN / relative).read_text(encoding="utf-8"))


def test_v2_discloses_holdout_and_collision_boundaries() -> None:
    spec = _json("qualification_spec.json")
    boundary = spec["evidence_boundary"].lower()
    assert "not an unseen scientific holdout" in boundary
    assert "simultaneous regularization" in boundary
    assert spec["gates"]["structural_unseen_scientific_holdout"] == 0


def test_v2_locks_every_consumed_upstream_module_and_spatial_input() -> None:
    shell = (CAMPAIGN / "run_qualification.sh").read_text(encoding="utf-8")
    for scope in (
        "validation-external/wp3-spatial-validation-v2",
        "src/python/threebody_reduction",
        "src/python/n3bp_qualification",
    ):
        assert f"--scope {scope}" in shell


def test_v2_uses_autodiff_and_on_shell_collision_passage() -> None:
    runner = (CAMPAIGN / "scripts/run_qualification.py").read_text(encoding="utf-8")
    assert "autodiff_reference.py" in runner
    assert "corrected_squared" in runner
    assert "collision_passage_finite" in runner
