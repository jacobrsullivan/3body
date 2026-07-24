from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-common-level-v1"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_specification_lock_is_valid_and_preimplementation() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = json.loads(
        (CAMPAIGN / "reports/wp6_common_level_v1_specification_lock.json").read_text()
    )
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["spec_sha256"] == _sha256(CAMPAIGN / "qualification_spec.json")
    assert lock["implementation_present_at_lock"] is False
    assert lock["qualification_outputs_present_at_lock"] is False
    for relative, expected in lock["prerequisite_file_hashes"].items():
        assert _sha256(ROOT / relative) == expected


def test_locked_claim_requires_direct_common_level_theorem() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    claim = spec["decision_policy"]["AUTHORIZED_CLAIM"]
    assert "every finite real common level" in claim
    assert "(h,c)!=(0,0)" in claim
    assert "direct on each common level" in claim
    assert "rather than transferred from WP6-FI1-v1" in claim


def test_proof_reference_and_boundary_preserve_nonclaims() -> None:
    proof = (CAMPAIGN / "proof/WP6-COMMON-v1-proof.md").read_text()
    reference = (CAMPAIGN / "reference/euler_conic.py").read_text()
    boundary = (
        ROOT / "src/python/wp6_common_level_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text()
    for index in range(1, 11):
        assert f"## R{index}:" in proof
    assert "src.python" not in reference
    for required in (
        "(H,C)=(0,0)",
        "one additional integral",
        "spatial",
        "non-rational",
        "regular SO(3)",
    ):
        assert required in boundary


def test_manifest_pins_primary_and_predecessor_sources() -> None:
    manifest = json.loads((CAMPAIGN / "sources/manifest.json").read_text())
    records = {item["source_id"]: item for item in manifest["sources"]}
    assert records["maciejewski-przybylska-combot-2025"]["arxiv"] == ("2502.01426")
    assert records["combot-2011"]["arxiv"] == "1112.1889"
    assert all(len(item["download_sha256"]) == 64 for item in records.values())
