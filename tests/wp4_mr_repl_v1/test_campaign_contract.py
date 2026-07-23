from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp4-mr-repl-v1"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def test_specification_lock_is_valid_and_preimplementation() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    path = CAMPAIGN / "reports/wp4_mr_repl_v1_specification_lock.json"
    lock = json.loads(path.read_text())
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["implementation_present_at_lock"] is False
    assert lock["qualification_outputs_present_at_lock"] is False


def test_reference_is_source_disjoint_and_differentiates_hamiltonian() -> None:
    text = (CAMPAIGN / "reference/sympy_derivation.py").read_text()
    production = (
        ROOT / "src/python/wp4_mr_repl_v1/model.py"
    ).read_text()
    assert "src.python.wp4_mr_repl_v1" not in text
    assert "import sympy" not in production
    assert "from sympy" not in production
    assert "sp.diff(hamiltonian" in text
    assert "sp.hessian(" in text
    assert "planar_variational" in text
    assert "whittaker_hessian" in text
    assert "_residue(fuchs" in text


def test_proof_and_boundary_cover_locked_nonclaims() -> None:
    proof = (CAMPAIGN / "proof/WP4-MR-REPL-v1-proof.md").read_text()
    boundary = (
        ROOT / "src/python/wp4_mr_repl_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text()
    for token in (
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6",
        "R7",
        "R8",
        "R9",
        "R10",
    ):
        assert token in proof
    assert "does not exclude one additional integral" in proof
    assert "does not say that the three-body problem has no additional integrals" in boundary
