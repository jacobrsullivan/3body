from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = VALIDATION / "wp1-residual-map-v1"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402

from src.python.wp1_residual_map_v1 import build_residual_map  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def test_specification_lock_is_valid_and_preimplementation() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = json.loads(
        (
            CAMPAIGN / "reports/wp1_residual_map_v1_specification_lock.json"
        ).read_text()
    )
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["implementation_present_at_lock"] is False
    assert lock["qualification_outputs_present_at_lock"] is False


def test_source_disjoint_reference_agrees_on_locked_catalogue() -> None:
    catalogue = json.loads(
        (
            VALIDATION
            / "wp1-catalogue-n3bp-validation/data/native_catalogue.json"
        ).read_text()
    )
    reference_path = CAMPAIGN / "reference/sympy_reference.py"
    assert "src.python.wp1_residual_map_v1" not in reference_path.read_text()
    reference = campaign_module(
        reference_path, "_wp1_residual_map_v1_reference_test"
    )
    assert build_residual_map(catalogue) == reference.build_map(catalogue)


def test_boundary_prohibits_invariant_interpretation() -> None:
    text = (
        ROOT / "src/python/wp1_residual_map_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text()
    assert "does not discover or interpret an invariant" in text
    assert "new locked and\nsealed qualification" in text
