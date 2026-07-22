#!/usr/bin/env python
"""Execute the frozen WP4-LIFT-NI-v2 theorem qualification."""

from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-lift-ni-v2"
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
from src.python.wp4_lift_ni_v2 import all_production_certificates  # noqa: E402


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
    "invalidated_v1_verified",
    "all_prerequisite_locks_and_records_verified",
    "all_source_download_hashes_verified",
    "source_text_contracts_verified",
    "production_reference_exact_agreement",
    "all_negative_controls_rejected",
    "proof_document_covers_every_obligation",
    "claim_boundary_present",
}


def runtime_gate_names() -> set[str]:
    return FIXED_GATE_NAMES | set(OBLIGATION_GATE_NAMES.values())


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--proof", required=True)
    parser.add_argument("--marsden-weinstein-pdf", required=True)
    parser.add_argument("--tsygvintsev-pdf", required=True)
    parser.add_argument("--boucher-weil-pdf", required=True)
    parser.add_argument("--dullin-montgomery-pdf", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _pdf_text(path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-raw", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _source_text_checks(source_text: dict[str, str]) -> dict[str, bool]:
    tsyg = _normalize_text(source_text["tsygvintsev-2007-exceptional-cases"])
    bw = _normalize_text(source_text["boucher-weil-morales-ramis-threebody"])
    dm = _normalize_text(source_text["dullin-montgomery-2025"])
    return {
        "tsygvintsev_planar_positive_mass_model": "newtonian planar threebody problem with positive masses"
        in tsyg,
        "tsygvintsev_parabolic_lagrange_solution": "parabolic lagrangian orbit" in tsyg,
        "tsygvintsev_fixed_nonzero_angular_momentum": "for a fixed non zero value of the angular momentum k"
        in tsyg,
        "tsygvintsev_reduced_three_degrees_of_freedom": "hamiltonian system with 3 degrees of freedom"
        in tsyg,
        "tsygvintsev_complete_meromorphic_obstruction": "not completely meromorphically integrable in the sense of liouvillearnold"
        in tsyg,
        "boucher_weil_planar_theorem": "the planar three body problem is not completely integrable with meromorphic first integrals"
        in bw,
        "boucher_weil_normal_variational_permission": "this theorem remains true if one replaces the variational system with the normal variational system"
        in bw,
        "boucher_weil_reduced_four_dimensional_nve": "after reductions the normal variational system is a 4 4 linear differential system"
        in bw,
        "dullin_montgomery_spatial_reduction": "symplectic reduction of the spatial n body problem"
        in dm,
        "dullin_montgomery_planar_frontier": "the planar stratum arises as the frontier"
        in dm,
    }


def _wp2_chart_contract(prerequisite: dict[str, Any]) -> bool:
    record = prerequisite["record"]
    required = {
        "dimension_and_constraint_count_pass_rate",
        "gauge_hamiltonian_scaled_max",
        "gauge_vector_covariance_scaled_max",
        "chart_roundtrip_scaled_max",
        "chart_hamiltonian_scaled_max",
        "chart_time_rate_scaled_max",
        "chart_cocycle_scaled_max",
    }
    if record.get("status") != "PASS":
        return False
    for split in ("development", "calibration", "holdout"):
        gates = {gate["name"]: gate for gate in record["evaluations"][split]["gates"]}
        if not required.issubset(gates) or not all(
            gates[name]["passed"] for name in required
        ):
            return False
    return True


def _proof_coverage(proof: str) -> dict[str, bool]:
    return {
        **{f"T{index}": f"## T{index} " in proof for index in range(1, 11)},
        "authorized_conclusion": "## Authorized Conclusion" in proof,
        "nonclaims": "## Nonclaims" in proof,
        "rank_argument": "Shell-relative rank nine" in proof,
        "off_shell_counterexample": "I1*p6" in proof,
        "fixed_momentum_subquotient": "fixed nonzero angular momentum" in proof,
        "galois_subquotient": "differential subquotient" in proof,
        "global_restriction": "global family would have a forbidden local" in proof,
    }


def _obligation_results(
    certificates: dict[str, Any],
    wp2_contract: bool,
    proof_checks: dict[str, bool],
    mr_record: dict[str, Any],
) -> dict[str, bool]:
    single = certificates["single_ks_zero_level"]
    product = certificates["product_reduction"]
    factor = certificates["hamiltonian_factor"]
    transfer = certificates["transfer"]
    spatial = certificates["spatial_subquotient"]
    logic = certificates["logic"]
    return {
        "T1": all(
            (
                single["radius_identity"],
                single["jacobian_metric_identity"],
                single["horizontal_projector_identity"],
                single["vertical_kernel_identity"],
                single["projection_rank"] == 6,
                single["constraint_projection_rank"] == 7,
                single["phase_gauge_kernel_identity"],
                single["gauge_tangent_to_level_identity"],
                single["canonical_on_zero_level"],
            )
        ),
        "T2": all(
            (
                product["upstairs_dimension"] == 18,
                product["regular_level_dimension"] == 16,
                product["quotient_dimension"] == 14,
                product["constraint_rank"] == 2,
                product["projection_rank"] == 14,
                product["constraint_projection_rank"] == 16,
                product["first_gauge_kernel"],
                product["second_gauge_kernel"],
                product["gauge_generators_independent"],
                factor["zero_level_factor_identity"],
                factor["nonzero_level_control_rejected"],
            )
        ),
        "T3": wp2_contract and proof_checks["T3"],
        "T4": transfer["sundman_identity_exact"] and proof_checks["T4"],
        "T5": transfer["full_family_involution"]
        and transfer["descended_family_involution"]
        and proof_checks["T5"],
        "T6": transfer["full_family_rank_on_shell"] == 9
        and transfer["descended_family_rank"] == 6
        and transfer["rank_loss_control_rejected"]
        and transfer["off_shell_only_control_rejected"]
        and proof_checks["rank_argument"],
        "T7": logic[
            "binary_collision_extension_does_not_remove_regular_open_restriction"
        ]
        and proof_checks["T7"],
        "T8": spatial["planar_vertical_cross_zero"]
        and spatial["planar_block_exact"]
        and spatial["reflection_commutes_with_variational_matrix"]
        and spatial["angular_momentum_nonzero"]
        and spatial["rotation_generator_identity"]
        and spatial["angular_momentum_conserved"]
        and spatial["flow_tangent_to_fixed_momentum_level"]
        and spatial["rotation_tangent_to_energy_level"]
        and spatial["energy_momentum_gradient_rank"] == 2
        and spatial["published_nve_chain_dimension_exact"]
        and proof_checks["fixed_momentum_subquotient"]
        and proof_checks["T8"],
        "T9": logic["abelian_group_has_only_abelian_algebraic_quotients"]
        and logic["nonabelian_quotient_obstructs_abelian_full_group"]
        and mr_record.get("status") == "PASS"
        and mr_record.get("all_project_cases_universally_obstructed") is True
        and proof_checks["galois_subquotient"],
        "T10": logic["global_family_restricts_to_every_regular_open_subset"]
        and proof_checks["global_restriction"]
        and proof_checks["T10"],
    }


def main() -> None:
    args = _args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite one-shot WP4 lift result")
    common = campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp4_lift_ni_v2_campaign_common_run",
    )
    reference = campaign_module(
        CAMPAIGN_ROOT / "reference/sympy_reference.py",
        "_wp4_lift_ni_v2_sympy_reference_run",
    )
    spec = load_json(args.spec)
    manifest = load_json(args.source_manifest)
    specification_lock = common.verify_specification_lock(args.spec)
    invalidated_predecessor = common.verify_invalidated_predecessor(spec)
    prerequisites = common.verify_prerequisites(spec)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("source_manifest_sha256") != sha256_file(args.source_manifest)
        or lock.get("proof_sha256") != sha256_file(args.proof)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("qualification lock does not bind the frozen inputs")

    source_paths = {
        "marsden-weinstein-1974": Path(args.marsden_weinstein_pdf),
        "tsygvintsev-2007-exceptional-cases": Path(args.tsygvintsev_pdf),
        "boucher-weil-morales-ramis-threebody": Path(args.boucher_weil_pdf),
        "dullin-montgomery-2025": Path(args.dullin_montgomery_pdf),
    }
    source_records = []
    source_hashes_passed = True
    for source in manifest["sources"]:
        path = source_paths[source["source_id"]]
        observed_hash = sha256_file(path)
        verified = observed_hash == source["download_sha256"]
        source_hashes_passed = source_hashes_passed and verified
        source_records.append(
            {
                "source_id": source["source_id"],
                "expected_sha256": source["download_sha256"],
                "observed_sha256": observed_hash,
                "verified": verified,
            }
        )
    if not source_hashes_passed:
        raise RuntimeError("external source PDF hash mismatch")
    source_text = {
        source_id: _pdf_text(path)
        for source_id, path in source_paths.items()
        if source_id != "marsden-weinstein-1974"
    }
    source_text_checks = _source_text_checks(source_text)

    production = all_production_certificates()
    independent = reference.all_reference_certificates()
    reference_source = CAMPAIGN_ROOT / "reference/sympy_reference.py"
    reference_text = reference_source.read_text(encoding="utf-8")
    reference_is_disjoint = (
        "src.python.wp4_lift_ni_v2" not in reference_text
        and "all_production_certificates" not in reference_text
    )
    exact_agreement = production == independent and reference_is_disjoint
    proof_text = Path(args.proof).read_text(encoding="utf-8")
    proof_checks = _proof_coverage(proof_text)
    wp2_contract = _wp2_chart_contract(prerequisites["wp2_multi"])
    obligations = _obligation_results(
        production,
        wp2_contract,
        proof_checks,
        prerequisites["wp4_mr"]["record"],
    )
    controls = {
        "wrong_ks_momentum_factor": production["wrong_momentum_factor_control"][
            "rejected"
        ],
        "nonzero_xi": production["nonzero_xi_control"]["rejected"],
        "clock_dependent": production["transfer"]["clock_dependent_control_rejected"],
        "gauge_variant": production["transfer"]["gauge_variant_control_rejected"],
        "off_shell_only_rank": production["transfer"][
            "off_shell_only_control_rejected"
        ],
        "rank_loss": production["transfer"]["rank_loss_control_rejected"],
    }
    boundary = spec["evidence_boundary"]
    boundary_present = all(
        phrase in boundary
        for phrase in (
            "conditional theorem extension",
            "ambient-only rank",
            "gauge-dependent",
            "clock-dependent",
            "non-meromorphic",
            "triple-collision",
            "does not rederive",
        )
    )
    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate(
            "invalidated_v1_verified",
            int(invalidated_predecessor["status"] == "INVALIDATED_PREFREEZE"),
            "==",
            1,
        ),
        make_gate("all_prerequisite_locks_and_records_verified", 1, "==", 1),
        make_gate(
            "all_source_download_hashes_verified",
            int(source_hashes_passed),
            "==",
            1,
        ),
        make_gate(
            "source_text_contracts_verified",
            int(all(source_text_checks.values())),
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
            int(all(controls.values())),
            "==",
            1,
        ),
        make_gate(
            "proof_document_covers_every_obligation",
            int(all(proof_checks.values())),
            "==",
            1,
        ),
        make_gate("claim_boundary_present", int(boundary_present), "==", 1),
    ]
    if runtime_gate_names() != set(spec["gates"]):
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
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "proof_sha256": sha256_file(args.proof),
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
        "invalidated_predecessor": {
            "campaign": invalidated_predecessor["campaign"],
            "status": invalidated_predecessor["status"],
            "assessment_sha256": sha256_file(common.INVALIDATED_PREDECESSOR),
            "claim_authorization": invalidated_predecessor["claim_authorization"],
        },
        "wp2_chart_contract_verified": wp2_contract,
        "production_certificates": production,
        "independent_reference": {
            "path": reference_source.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_file(reference_source),
            "production_import_absent": reference_is_disjoint,
            "certificates": independent,
        },
        "production_reference_exact_agreement": exact_agreement,
        "proof_coverage": proof_checks,
        "theorem_obligations": obligations,
        "negative_controls": controls,
        "gates": gates,
        "authorized_claim": (
            spec["decision_policy"]["AUTHORIZED_CLAIM"]
            if status == "PASS"
            else "NOT_AUTHORIZED"
        ),
        "claim_boundary": boundary,
        "prohibited_short_claim": spec["decision_policy"]["PROHIBITED_SHORT_CLAIM"],
        "prohibited_raw_upstairs_claim": spec["decision_policy"][
            "PROHIBITED_RAW_UPSTAIRS_CLAIM"
        ],
    }
    atomic_write_json(destination, payload)
    print(
        f"{spec['campaign']}: {status}; obligations="
        f"{sum(obligations.values())}/{len(obligations)}; "
        f"controls={sum(controls.values())}/{len(controls)}"
    )


if __name__ == "__main__":
    main()
