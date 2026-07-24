#!/usr/bin/env python
"""Execute the frozen WP4-LIFT-NI-v3 successor qualification."""

from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.metadata
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-lift-ni-v3"
V2_ROOT = VALIDATION_ROOT / "wp4-lift-ni-v2"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from validation_external_import import campaign_module  # noqa: E402
from src.python.wp4_lift_ni_v3 import (  # noqa: E402
    TRANSFER_IMPLEMENTATION,
    all_production_certificates,
)


OBLIGATION_GATE_NAMES = {
    "T1": "all_T1_exact_identities_pass",
    "T2": "all_T2_dimension_and_rank_checks_pass",
    "T3": "all_T3_chart_contract_checks_pass",
    "T4": "all_T4_sundman_identities_pass",
    "T5": "all_T5_involution_checks_pass",
    "T6": "all_T6_shell_rank_checks_pass",
    "T7": "all_T7_domain_checks_pass",
    "T8": "all_T8_spatial_subquotient_checks_pass",
    "T9": "all_T9_galois_logic_checks_pass",
    "T10": "all_T10_global_logic_checks_pass",
}
FIXED_GATE_NAMES = {
    "specification_lock_verified",
    "all_prerequisite_locks_and_records_verified",
    "inherited_source_manifest_verified",
    "all_source_download_hashes_verified",
    "source_text_contracts_verified",
    "v2_transfer_implementation_identity_verified",
    "mr_reproduced_premise_verified",
    "production_reference_exact_agreement",
    "all_negative_controls_rejected",
    "proof_document_covers_every_obligation",
    "claim_boundary_present",
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--proof-addendum", required=True)
    parser.add_argument("--marsden-weinstein-pdf", required=True)
    parser.add_argument("--tsygvintsev-pdf", required=True)
    parser.add_argument("--boucher-weil-pdf", required=True)
    parser.add_argument("--dullin-montgomery-pdf", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _source_records(
    manifest: dict[str, Any], paths: dict[str, Path]
) -> list[dict[str, Any]]:
    records = []
    for source in manifest["sources"]:
        observed = sha256_file(paths[source["source_id"]])
        expected = source["download_sha256"]
        records.append(
            {
                "source_id": source["source_id"],
                "expected_sha256": expected,
                "observed_sha256": observed,
                "verified": observed == expected,
            }
        )
    return records


def _addendum_coverage(text: str) -> dict[str, bool]:
    return {
        **{f"T{index}": f"## T{index} " in text for index in range(1, 11)},
        "evidence_identity": "## Evidence Identity" in text,
        "reproduced_generic_nve": "constructs the planar 6-dimensional" in text,
        "empty_exceptional_set": "exceptional set is empty" in text,
        "nonabelian_identity_component": "non-Abelian for every finite" in text,
        "authorized_conclusion": "## Authorized Conclusion" in text,
        "nonclaims": "## Nonclaims" in text,
    }


def _mr_synthetic_control(common: Any) -> bool:
    return not common.mr_reproduced_premise(
        {
            "status": "PASS",
            "qualification_id": "synthetic",
            "authorized_claim": "non-Abelian for every finite positive mass triple",
        }
    )


def main() -> None:
    args = _args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite one-shot v3 result")
    common = campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp4_lift_ni_v3_common_run",
    )
    v2_run = campaign_module(
        V2_ROOT / "scripts/run_qualification.py",
        "_wp4_lift_ni_v2_run_helpers_for_v3",
    )
    reference = campaign_module(
        V2_ROOT / "reference/sympy_reference.py",
        "_wp4_lift_ni_v2_reference_for_v3",
    )
    spec = load_json(args.spec)
    manifest = load_json(args.source_manifest)
    specification_lock = common.verify_specification_lock(args.spec)
    prerequisites = common.verify_prerequisites(spec)
    implementation_identity = common.verify_implementation_identity(spec)
    mr_record = prerequisites["wp4_mr_repl"]["record"]
    mr_premise = common.mr_reproduced_premise(mr_record)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("source_manifest_sha256") != sha256_file(args.source_manifest)
        or lock.get("proof_addendum_sha256") != sha256_file(args.proof_addendum)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("v3 qualification lock does not bind frozen inputs")

    inherited_manifest = spec["prerequisites"]["inherited_source_manifest"]
    source_manifest_verified = (
        sha256_file(args.source_manifest) == inherited_manifest["sha256"]
        and Path(args.source_manifest).resolve()
        == (REPO_ROOT / inherited_manifest["path"]).resolve()
    )
    source_paths = {
        "marsden-weinstein-1974": Path(args.marsden_weinstein_pdf),
        "tsygvintsev-2007-exceptional-cases": Path(args.tsygvintsev_pdf),
        "boucher-weil-morales-ramis-threebody": Path(args.boucher_weil_pdf),
        "dullin-montgomery-2025": Path(args.dullin_montgomery_pdf),
    }
    source_records = _source_records(manifest, source_paths)
    source_text = {
        source_id: v2_run._pdf_text(path)
        for source_id, path in source_paths.items()
        if source_id != "marsden-weinstein-1974"
    }
    source_text_checks = v2_run._source_text_checks(source_text)

    production = all_production_certificates()
    independent = reference.all_reference_certificates()
    wrapper_source = (
        REPO_ROOT / "src/python/wp4_lift_ni_v3/__init__.py"
    ).read_text(encoding="utf-8")
    reference_path = V2_ROOT / "reference/sympy_reference.py"
    reference_text = reference_path.read_text(encoding="utf-8")
    implementation_identity["wrapper_delegates_to_v2"] = (
        "from src.python.wp4_lift_ni_v2 import" in wrapper_source
        and TRANSFER_IMPLEMENTATION == "WP4-LIFT-NI-v2"
    )
    implementation_identity["reference_source_disjoint"] = (
        "src.python.wp4_lift_ni_v2" not in reference_text
        and "src.python.wp4_lift_ni_v3" not in reference_text
        and "all_production_certificates" not in reference_text
    )
    identity_verified = all(
        (
            implementation_identity["all_match"],
            implementation_identity["wrapper_delegates_to_v2"],
            implementation_identity["reference_source_disjoint"],
        )
    )
    exact_agreement = production == independent and identity_verified

    v2_proof_path = REPO_ROOT / spec["prerequisites"]["wp4_lift_v2"]["proof_file"]
    v2_proof = v2_proof_path.read_text(encoding="utf-8")
    addendum = Path(args.proof_addendum).read_text(encoding="utf-8")
    v2_proof_checks = v2_run._proof_coverage(v2_proof)
    addendum_checks = _addendum_coverage(addendum)
    wp2_contract = v2_run._wp2_chart_contract(prerequisites["wp2_multi"])
    synthetic_mr = (
        {
            "status": "PASS",
            "all_project_cases_universally_obstructed": True,
        }
        if mr_premise
        else {}
    )
    obligations = v2_run._obligation_results(
        production,
        wp2_contract,
        v2_proof_checks,
        synthetic_mr,
    )
    obligations["T9"] = bool(obligations["T9"] and mr_premise)

    transfer_controls = {
        "wrong_ks_momentum_factor": production["wrong_momentum_factor_control"][
            "rejected"
        ],
        "nonzero_xi": production["nonzero_xi_control"]["rejected"],
        "clock_dependent": production["transfer"][
            "clock_dependent_control_rejected"
        ],
        "gauge_variant": production["transfer"][
            "gauge_variant_control_rejected"
        ],
        "off_shell_only_rank": production["transfer"][
            "off_shell_only_control_rejected"
        ],
        "rank_loss": production["transfer"]["rank_loss_control_rejected"],
    }
    altered_spec = deepcopy(spec)
    altered_spec["prerequisites"]["wp4_lift_v2"][
        "production_file_sha256"
    ] = "0" * 64
    controls = {
        **transfer_controls,
        "status_only_mr_record_rejected": _mr_synthetic_control(common),
        "changed_v2_identity_rejected": not common.verify_implementation_identity(
            altered_spec
        )["all_match"],
    }
    boundary = spec["evidence_boundary"]
    boundary_present = all(
        phrase in boundary
        for phrase in (
            "replaces the unreplicated planar premise",
            "ambient-only rank",
            "gauge-dependent",
            "clock-dependent",
            "non-meromorphic",
            "zero angular momentum",
            "triple-collision",
            "absence of individual additional integrals",
        )
    )

    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate(
            "all_prerequisite_locks_and_records_verified",
            len(prerequisites),
            "==",
            3,
        ),
        make_gate(
            "inherited_source_manifest_verified",
            int(source_manifest_verified),
            "==",
            1,
        ),
        make_gate(
            "all_source_download_hashes_verified",
            sum(record["verified"] for record in source_records),
            "==",
            len(source_records),
        ),
        make_gate(
            "source_text_contracts_verified",
            sum(source_text_checks.values()),
            "==",
            len(source_text_checks),
        ),
        make_gate(
            "v2_transfer_implementation_identity_verified",
            int(identity_verified),
            "==",
            1,
        ),
        make_gate(
            "mr_reproduced_premise_verified",
            int(mr_premise),
            "==",
            1,
        ),
        *[
            make_gate(OBLIGATION_GATE_NAMES[name], int(passed), "==", 1)
            for name, passed in obligations.items()
        ],
        make_gate(
            "production_reference_exact_agreement",
            int(exact_agreement),
            "==",
            1,
        ),
        make_gate(
            "all_negative_controls_rejected",
            sum(controls.values()),
            "==",
            len(controls),
        ),
        make_gate(
            "proof_document_covers_every_obligation",
            int(all(v2_proof_checks.values()) and all(addendum_checks.values())),
            "==",
            1,
        ),
        make_gate("claim_boundary_present", int(boundary_present), "==", 1),
    ]
    expected_gate_names = FIXED_GATE_NAMES | set(OBLIGATION_GATE_NAMES.values())
    if (
        {gate["name"] for gate in gates} != expected_gate_names
        or expected_gate_names != set(spec["gates"])
    ):
        raise RuntimeError(
            "runtime gate set does not exactly match the locked specification"
        )
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    runtime = runtime_fingerprint()
    runtime["packages"]["sympy"] = importlib.metadata.version("sympy")
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": status,
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "proof_addendum_sha256": sha256_file(args.proof_addendum),
        "inherited_v2_proof_sha256": sha256_file(v2_proof_path),
        "runtime": runtime,
        "source_records": source_records,
        "source_text_checks": source_text_checks,
        "prerequisites": {
            name: {
                "qualification_id": value["record"]["qualification_id"],
                "status": value["record"]["status"],
                "lock_sha256": value["lock"]["lock_sha256"],
            }
            for name, value in prerequisites.items()
        },
        "mr_reproduced_premise_verified": mr_premise,
        "mr_reproduction_summary": {
            "generic_derivation": mr_record["generic_derivation"],
            "complete_integrability_exceptional_set": mr_record[
                "complete_integrability_exceptional_set"
            ],
            "implementation_independence": mr_record[
                "implementation_independence"
            ],
            "authorized_claim": mr_record["authorized_claim"],
        },
        "wp2_chart_contract_verified": wp2_contract,
        "implementation_identity": implementation_identity,
        "production_certificates": production,
        "independent_reference": {
            "path": reference_path.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_file(reference_path),
            "source_disjoint": implementation_identity[
                "reference_source_disjoint"
            ],
            "certificates": independent,
        },
        "production_reference_exact_agreement": exact_agreement,
        "v2_proof_coverage": v2_proof_checks,
        "v3_addendum_coverage": addendum_checks,
        "theorem_obligations": obligations,
        "negative_controls": controls,
        "gates": gates,
        "authorized_claim": (
            spec["decision_policy"]["AUTHORIZED_CLAIM"]
            if status == "PASS"
            else "NOT_AUTHORIZED"
        ),
        "claim_boundary": boundary,
        "prohibited_short_claim": spec["decision_policy"][
            "PROHIBITED_SHORT_CLAIM"
        ],
        "prohibited_raw_upstairs_claim": spec["decision_policy"][
            "PROHIBITED_RAW_UPSTAIRS_CLAIM"
        ],
        "prohibited_global_claim": spec["decision_policy"][
            "PROHIBITED_GLOBAL_CLAIM"
        ],
    }
    atomic_write_json(destination, payload)
    print(
        f"{spec['campaign']}: {status}; obligations="
        f"{sum(obligations.values())}/{len(obligations)}; "
        f"controls={sum(controls.values())}/{len(controls)}"
    )
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
