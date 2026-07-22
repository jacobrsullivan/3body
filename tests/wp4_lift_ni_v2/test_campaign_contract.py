from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp4-lift-ni-v2"
sys.path.insert(0, str(ROOT / "validation-external"))

from validation_external_import import campaign_module  # noqa: E402


def test_specification_lock_and_prerequisites_verify() -> None:
    common = campaign_module(
        CAMPAIGN / "scripts/campaign_common.py",
        "_wp4_lift_test_campaign_common",
    )
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    lock = common.verify_specification_lock(CAMPAIGN / "qualification_spec.json")
    prerequisites = common.verify_prerequisites(spec)
    assert lock["implementation_existed_before_lock"] is False
    assert lock["qualification_outputs_existed_before_lock"] is False
    assert lock["predecessor_invalidated_before_lock"] is True
    predecessor = common.verify_invalidated_predecessor(spec)
    assert predecessor["status"] == "INVALIDATED_PREFREEZE"
    assert predecessor["claim_authorization"] == "NONE"
    assert prerequisites["wp2_multi"]["record"]["status"] == "PASS"
    assert prerequisites["wp4_mr"]["record"]["status"] == "PASS"


def test_production_and_source_disjoint_reference_agree_exactly() -> None:
    from src.python.wp4_lift_ni_v2 import all_production_certificates

    reference_path = CAMPAIGN / "reference/sympy_reference.py"
    reference_text = reference_path.read_text()
    assert "src.python.wp4_lift_ni_v2" not in reference_text
    assert "all_production_certificates" not in reference_text
    reference = campaign_module(reference_path, "_wp4_lift_test_reference")
    assert all_production_certificates() == reference.all_reference_certificates()


def test_locked_proof_and_claim_boundaries_are_complete() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    proof = (CAMPAIGN / "proof/WP4-LIFT-NI-v2-proof.md").read_text()
    assert all(f"## T{index} " in proof for index in range(1, 11))
    assert "## Authorized Conclusion" in proof
    assert "## Nonclaims" in proof
    assert "differential subquotient" in proof
    assert "Shell-relative rank nine" in proof
    assert "I1*p6" in proof
    assert "fixed nonzero angular momentum" in proof
    boundary = spec["evidence_boundary"]
    for phrase in (
        "gauge-dependent",
        "ambient-only rank",
        "clock-dependent",
        "non-meromorphic",
        "triple-collision",
        "does not rederive",
    ):
        assert phrase in boundary


def test_qualification_runtime_is_exactly_pinned() -> None:
    requirements = (CAMPAIGN / "runtime_requirements.txt").read_text().splitlines()
    assert requirements == ["sympy==1.14.0", "pytest==8.4.1"]


def test_runtime_gate_set_exactly_matches_locked_specification() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    runner = campaign_module(
        CAMPAIGN / "scripts/run_qualification.py",
        "_wp4_lift_test_runner_contract",
    )
    assert runner.runtime_gate_names() == set(spec["gates"])


def test_runtime_obligation_mapping_accepts_all_frozen_inputs() -> None:
    from src.python.wp4_lift_ni_v2 import all_production_certificates

    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    common = campaign_module(
        CAMPAIGN / "scripts/campaign_common.py",
        "_wp4_lift_test_common_obligations",
    )
    runner = campaign_module(
        CAMPAIGN / "scripts/run_qualification.py",
        "_wp4_lift_test_runner_obligations",
    )
    prerequisites = common.verify_prerequisites(spec)
    proof = (CAMPAIGN / "proof/WP4-LIFT-NI-v2-proof.md").read_text()
    proof_checks = runner._proof_coverage(proof)
    obligations = runner._obligation_results(
        all_production_certificates(),
        runner._wp2_chart_contract(prerequisites["wp2_multi"]),
        proof_checks,
        prerequisites["wp4_mr"]["record"],
    )
    assert all(proof_checks.values())
    assert obligations == {f"T{index}": True for index in range(1, 11)}
