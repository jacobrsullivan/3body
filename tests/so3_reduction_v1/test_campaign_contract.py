from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp2-so3-leaf-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def test_specification_lock_and_prerequisites_are_valid() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = json.loads(
        (CAMPAIGN / "reports/wp2_so3_leaf_v1_specification_lock.json").read_text()
    )
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["implementation_present_at_lock"] is False
    for relative, expected in lock["prerequisite_file_hashes"].items():
        assert _sha256(ROOT / relative) == expected


def test_proof_reference_and_boundary_cover_the_locked_scope() -> None:
    proof = (CAMPAIGN / "proof/WP2-SO3-LEAF-v1-proof.md").read_text()
    reference = (CAMPAIGN / "reference/independent_leaf.py").read_text()
    boundary = (
        ROOT / "src/python/so3_reduction_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text()
    for index in range(1, 11):
        assert f"## R{index}:" in proof
    assert "src.python" not in reference
    assert "not:" in boundary
    assert "collinearity" in boundary
    assert "global quotient atlas" in boundary
