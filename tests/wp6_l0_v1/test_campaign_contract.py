from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-l0-v1"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def test_specification_lock_is_valid_and_preimplementation() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = json.loads(
        (CAMPAIGN / "reports/wp6_l0_v1_specification_lock.json").read_text()
    )
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["implementation_present_at_lock"] is False
    assert lock["qualification_outputs_present_at_lock"] is False


def test_proof_reference_and_boundary_preserve_double_zero_exclusion() -> None:
    proof = (CAMPAIGN / "proof/WP6-L0-v1-proof.md").read_text()
    reference = (CAMPAIGN / "reference/equal_mass_euler.py").read_text()
    boundary = (
        ROOT / "src/python/wp6_l0_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text()
    for index in range(1, 11):
        assert f"## R{index}:" in proof
    assert "src.python" not in reference
    assert "(H,C)=(0,0)" in boundary
    assert "absence of one additional integral" in boundary
    assert "spatial zero-angular-momentum" in boundary
