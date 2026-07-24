from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = VALIDATION / "wp4-lift-ni-v3"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402

from src.python.wp4_lift_ni_v2 import (  # noqa: E402
    all_production_certificates as v2_certificates,
)
from src.python.wp4_lift_ni_v3 import (  # noqa: E402
    TRANSFER_IMPLEMENTATION,
    all_production_certificates as v3_certificates,
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _common():
    return campaign_module(
        CAMPAIGN / "scripts/campaign_common.py",
        "_wp4_lift_ni_v3_common_test",
    )


def test_specification_lock_is_valid_and_preimplementation() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = json.loads(
        (
            CAMPAIGN / "reports/wp4_lift_ni_v3_specification_lock.json"
        ).read_text()
    )
    signature = lock.pop("specification_lock_sha256")
    assert hashlib.sha256(_canonical(lock)).hexdigest() == signature
    assert lock["campaign"] == spec["campaign"]
    assert lock["v3_implementation_present_at_lock"] is False
    assert lock["v3_qualification_outputs_present_at_lock"] is False
    assert lock["inherited_v2_implementation_present_at_lock"] is True


def test_v3_delegates_to_unchanged_v2_certificates() -> None:
    assert TRANSFER_IMPLEMENTATION == "WP4-LIFT-NI-v2"
    assert v3_certificates() == v2_certificates()


def test_prerequisites_identity_and_full_mr_record_verify() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    common = _common()
    prerequisites = common.verify_prerequisites(spec)
    assert set(prerequisites) == {"wp2_multi", "wp4_mr_repl", "wp4_lift_v2"}
    assert common.verify_implementation_identity(spec)["all_match"] is True
    assert common.mr_reproduced_premise(
        prerequisites["wp4_mr_repl"]["record"]
    ) is True


def test_status_only_mr_record_and_changed_identity_are_rejected() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    common = _common()
    assert common.mr_reproduced_premise({"status": "PASS"}) is False
    valid_record = common.verify_prerequisites(spec)["wp4_mr_repl"]["record"]
    for field in ("published_source_equivalence", "theorem_obligations"):
        incomplete = deepcopy(valid_record)
        incomplete[field].pop(next(iter(incomplete[field])))
        assert common.mr_reproduced_premise(incomplete) is False
    changed = deepcopy(spec)
    changed["prerequisites"]["wp4_lift_v2"][
        "reference_file_sha256"
    ] = "0" * 64
    assert common.verify_implementation_identity(changed)["all_match"] is False


def test_reference_remains_source_disjoint() -> None:
    text = (
        VALIDATION / "wp4-lift-ni-v2/reference/sympy_reference.py"
    ).read_text()
    assert "src.python.wp4_lift_ni_v2" not in text
    assert "src.python.wp4_lift_ni_v3" not in text
    assert "all_production_certificates" not in text


def test_addendum_covers_all_obligations_and_nonclaims() -> None:
    text = (
        CAMPAIGN / "proof/WP4-LIFT-NI-v3-addendum.md"
    ).read_text()
    for index in range(1, 11):
        assert f"## T{index} " in text
    assert "## Authorized Conclusion" in text
    assert "## Nonclaims" in text
    assert "exceptional set is empty" in text


def test_runtime_gate_set_exactly_matches_locked_specification() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    runner = campaign_module(
        CAMPAIGN / "scripts/run_qualification.py",
        "_wp4_lift_ni_v3_runner_test",
    )
    expected = runner.FIXED_GATE_NAMES | set(
        runner.OBLIGATION_GATE_NAMES.values()
    )
    assert set(spec["gates"]) == expected
    assert len(expected) == 21
