from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-fi1-v1"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def test_specification_lock_is_valid_and_preimplementation() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = json.loads(
        (CAMPAIGN / "reports/wp6_fi1_v1_specification_lock.json").read_text()
    )
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["implementation_present_at_lock"] is False
    assert lock["qualification_outputs_present_at_lock"] is False


def test_proof_reference_and_boundary_cover_the_locked_scope() -> None:
    proof = (CAMPAIGN / "proof/WP6-FI1-v1-proof.md").read_text()
    reference = (CAMPAIGN / "reference/sympy_hessian.py").read_text()
    boundary = (
        ROOT / "src/python/wp6_fi1_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text()
    for index in range(1, 11):
        assert f"## R{index}:" in proof
    assert "src.python" not in reference
    assert "fixed-energy" in boundary
    assert "non-meromorphic" in boundary
    assert "not exceptions" in boundary
