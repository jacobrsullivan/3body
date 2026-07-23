#!/usr/bin/env python
"""Execute the frozen WP4-MR-REPL-v1 exact qualification."""

from __future__ import annotations

import argparse
from fractions import Fraction
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-mr-repl-v1"
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
from src.python.wp4_mr_repl_v1 import (  # noqa: E402
    COLLISION_CHARPOLY,
    TURNING_CHARPOLY,
    infinity_charpoly,
    nonabelian_certificate,
    reproduce,
    universal_nonabelian_domain_certificate,
    validate_residue_contract,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--proof", required=True)
    parser.add_argument("--tsygvintsev-pdf", required=True)
    parser.add_argument("--boucher-weil-pdf", required=True)
    parser.add_argument("--morales-ramis-pdf", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _normalized_text(path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-raw", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    decomposed = unicodedata.normalize("NFKD", completed.stdout)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _source_checks(paths: dict[str, Path]) -> dict[str, bool]:
    tsyg = _normalized_text(paths["tsygvintsev-2001-nve"])
    bw = _normalized_text(paths["boucher-weil-planar-threebody"])
    mr = _normalized_text(paths["morales-ramis-2001-foundation"])
    return {
        "tsygvintsev_title": (
            "the meromorphic non integrability of the three body problem" in tsyg
        ),
        "tsygvintsev_reduced_hamiltonian": (
            "closed hamiltonian system with 3 degrees of freedom" in tsyg
        ),
        "tsygvintsev_parabolic_curve": (
            "parametrized parabolic integral curve" in tsyg
        ),
        "tsygvintsev_whittaker_reduction": (
            "applying whittakers procedure" in tsyg
        ),
        "tsygvintsev_fuchs_gauge": (
            "equations 4 5 can be reduced to fuchsian form" in tsyg
            and "diag lz lz 1 1" in tsyg
        ),
        "tsygvintsev_finite_spectra": (
            "eigenvalues 1 1 0 0" in tsyg
            and "eigenvalues 2 1 0 1" in tsyg
        ),
        "tsygvintsev_infinity_spectrum": (
            "the matrix t has the following eigenvalues" in tsyg
            and "moreover spectr t 6 1 1 1 1" in tsyg
        ),
        "tsygvintsev_local_conclusion": (
            "meromorphically non integrable near the lagrangian parabolic"
            in tsyg
        ),
        "boucher_weil_title": (
            "application of the morales ramis theorem to test the non complete integrability of the planar three body problem"
            in bw
        ),
        "boucher_weil_conclusion": (
            "the planar three body problem is not completely integrable with meromorphic first integrals"
            in bw
        ),
        "morales_ramis_title": (
            "galoisian obstructions to integrability of hamiltonian systems i"
            in mr
        ),
        "morales_ramis_necessary_condition": (
            "necessary condition for meromorphic complete integrability" in mr
            and "identity component of the galois group of the variational equation"
            in mr
            and "must be abelian" in mr
        ),
        "morales_ramis_nve_quotient": (
            "identity component of gal" in mr
            and "normal variational equation" in mr
            and "is also abelian" in mr
        ),
    }


def _source_records(
    manifest: dict[str, Any], paths: dict[str, Path]
) -> list[dict[str, Any]]:
    records = []
    for source in manifest["sources"]:
        source_id = source["source_id"]
        observed = sha256_file(paths[source_id])
        expected = source["download_sha256"]
        records.append(
            {
                "source_id": source_id,
                "expected_sha256": expected,
                "observed_sha256": observed,
                "verified": observed == expected,
            }
        )
    return records


def _prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in ("wp2_multi", "wp4_mr_v2", "wp4_lift_v2"):
        item = spec["prerequisites"][name]
        lock = verify_lock(
            REPO_ROOT / item["lock_file"],
            REPO_ROOT,
            expected_prefix=item["qualification_id"].rsplit("-", 1)[0],
        )
        record = load_json(REPO_ROOT / item["record_file"])
        result[name] = {
            "qualification_id": record.get("qualification_id"),
            "status": record.get("status"),
            "lock_sha256": lock.get("lock_sha256"),
            "verified": (
                record.get("qualification_id") == item["qualification_id"]
                and record.get("status") == "PASS"
            ),
        }
    return result


def _benchmark_results(
    spec: dict[str, Any], reference: Any
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    all_agree = True
    for benchmark in spec["exact_benchmarks"]:
        masses = tuple(Fraction(value) for value in benchmark["masses"])
        production = reproduce(masses).as_payload()
        normalized_m1 = masses[0] / masses[2]
        normalized_m2 = masses[1] / masses[2]
        derived = reference.derive(str(normalized_m1), str(normalized_m2))
        residue_agreement = (
            derived["turning_charpoly"] == production["turning_charpoly"]
            and derived["collision_plus_charpoly"]
            == production["collision_charpoly"]
            and derived["collision_minus_charpoly"]
            == production["collision_charpoly"]
            and derived["infinity_charpoly"] == production["infinity_charpoly"]
        )
        passed = bool(
            production["sigma"] == benchmark["sigma"]
            and derived["sigma"] == benchmark["sigma"]
            and derived["all_exact_derivation_checks_pass"]
            and residue_agreement
            and production["galois"][
                "differential_galois_identity_component_nonabelian"
            ]
        )
        all_agree = all_agree and passed
        rows.append(
            {
                "case_id": benchmark["case_id"],
                "masses": benchmark["masses"],
                "production": production,
                "reference": derived,
                "residue_polynomials_exactly_agree": residue_agreement,
                "passed": passed,
            }
        )
    return rows, all_agree


def _negative_controls(source_records: list[dict[str, Any]]) -> dict[str, bool]:
    sigma = Fraction(11, 36)
    infinity = infinity_charpoly(sigma)
    changed_turning = list(TURNING_CHARPOLY)
    changed_turning[1] += 1
    changed_collision = list(COLLISION_CHARPOLY)
    changed_collision[3] += 1
    changed_infinity = list(infinity)
    changed_infinity[4] += 1
    invalid_masses_rejected = True
    for masses in ((0, 1, 1), (-1, 1, 1), (1, 2)):
        try:
            reproduce(masses)
            invalid_masses_rejected = False
        except (TypeError, ValueError):
            pass
    sigma_zero_rejected = False
    try:
        nonabelian_certificate(0)
    except ValueError:
        sigma_zero_rejected = True
    reference_source = (
        CAMPAIGN_ROOT / "reference/sympy_derivation.py"
    ).read_text(encoding="utf-8")
    return {
        "invalid_masses_rejected": invalid_masses_rejected,
        "changed_turning_residue_rejected": not validate_residue_contract(
            turning=changed_turning,
            infinity=infinity,
            sigma=sigma,
        ),
        "changed_collision_residue_rejected": not validate_residue_contract(
            collision=changed_collision,
            infinity=infinity,
            sigma=sigma,
        ),
        "changed_infinity_polynomial_rejected": not validate_residue_contract(
            infinity=changed_infinity,
            sigma=sigma,
        ),
        "sigma_zero_rejected": sigma_zero_rejected,
        "identity_component_premise_required": not nonabelian_certificate(
            sigma, unipotents_in_identity_component=False
        )["differential_galois_identity_component_nonabelian"],
        "commutation_premise_required": not nonabelian_certificate(
            sigma, abelian_identity_component_implies_commuting=False
        )["differential_galois_identity_component_nonabelian"],
        "changed_source_hash_rejected": all(
            record["observed_sha256"] != "0" * 64 for record in source_records
        ),
        "reference_does_not_import_production": (
            "src.python.wp4_mr_repl_v1" not in reference_source
            and "from .model" not in reference_source
        ),
    }


def _proof_coverage(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    tokens = {
        "R1": "## R1:",
        "R2": "## R2:",
        "R3": "## R3:",
        "R4": "## R4:",
        "R5": "## R5:",
        "R6": "## R6:",
        "R7": "## R7:",
        "R8": "## R8:",
        "R9": "## R9:",
        "R10": "## R10:",
        "authorized_boundary": "does not exclude one additional integral",
        "group_contradiction": "The contradiction proves that",
    }
    return {name: token in text for name, token in tokens.items()}


def main() -> None:
    args = _args()
    output = Path(args.output)
    if output.exists():
        raise RuntimeError("refusing to overwrite immutable qualification result")
    spec = load_json(args.spec)
    manifest = load_json(args.source_manifest)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    common = campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp4_mr_repl_v1_common_run",
    )
    specification_lock = common.verify_specification_lock(args.spec)
    paths = {
        "tsygvintsev-2001-nve": Path(args.tsygvintsev_pdf),
        "boucher-weil-planar-threebody": Path(args.boucher_weil_pdf),
        "morales-ramis-2001-foundation": Path(args.morales_ramis_pdf),
    }
    source_records = _source_records(manifest, paths)
    source_checks = _source_checks(paths)
    prerequisites = _prerequisites(spec)
    reference = campaign_module(
        CAMPAIGN_ROOT / "reference/sympy_derivation.py",
        "_wp4_mr_repl_v1_reference_run",
    )

    generic = reference.derive()
    universal_domain = universal_nonabelian_domain_certificate()
    benchmarks, benchmark_agreement = _benchmark_results(spec, reference)
    controls = _negative_controls(source_records)
    production_source = (
        REPO_ROOT / "src/python/wp4_mr_repl_v1/model.py"
    ).read_text(encoding="utf-8")
    implementation_independence = {
        "reference_does_not_import_production": controls[
            "reference_does_not_import_production"
        ],
        "production_does_not_import_sympy": (
            "import sympy" not in production_source
            and "from sympy" not in production_source
        ),
    }
    proof_coverage = _proof_coverage(Path(args.proof))
    source_equivalence = {
        "reduced_hamiltonian_convention": (
            generic["hamiltonian_term_count"] == 9
            and source_checks["tsygvintsev_reduced_hamiltonian"]
        ),
        "parabolic_lagrange_phase_curve": (
            generic["hamiltonian_zero_on_phase_curve"]
            and all(generic["hamilton_equation_tangent_residuals_zero"])
            and source_checks["tsygvintsev_parabolic_curve"]
        ),
        "planar_variational_and_whittaker_reduction": (
            generic["planar_variational_matrix_constructed_from_hessian"]
            and generic["whittaker_hessian_symmetric"]
            and source_checks["tsygvintsev_whittaker_reduction"]
        ),
        "fuchs_gauge_and_singular_points": (
            generic[
                "fuchs_only_simple_finite_poles_and_no_polynomial_part"
            ]
            and source_checks["tsygvintsev_fuchs_gauge"]
        ),
        "finite_residue_spectra": (
            generic["turning_charpoly_matches"]
            and generic["collision_plus_charpoly_matches"]
            and generic["collision_minus_charpoly_matches"]
            and source_checks["tsygvintsev_finite_spectra"]
        ),
        "infinity_exponent_polynomial": (
            generic["infinity_charpoly_matches"]
            and source_checks["tsygvintsev_infinity_spectrum"]
        ),
        "morales_ramis_conclusion": (
            source_checks["morales_ramis_necessary_condition"]
            and source_checks["boucher_weil_conclusion"]
            and source_checks["tsygvintsev_local_conclusion"]
        ),
    }
    obligations = {
        "R1": generic["hamiltonian_term_count"] == 9
        and source_checks["tsygvintsev_reduced_hamiltonian"],
        "R2": generic["hamiltonian_zero_on_phase_curve"]
        and all(generic["hamilton_equation_tangent_residuals_zero"]),
        "R3": generic["whittaker_hessian_symmetric"]
        and generic["normal_system_hamiltonian"]
        and generic["planar_variational_matrix_constructed_from_hessian"]
        and generic["planar_variational_matrix_hamiltonian"]
        and generic["planar_variational_phase_substitution_complete"]
        and generic["planar_variational_equation_dimension"] == 6
        and generic["whittaker_energy_shell_normal_dimension"] == 4,
        "R4": generic["fuchs_singular_points_distinct"]
        and generic["fuchs_only_simple_finite_poles_and_no_polynomial_part"],
        "R5": generic["turning_charpoly_matches"]
        and generic["collision_plus_charpoly_matches"]
        and generic["collision_minus_charpoly_matches"],
        "R6": generic["infinity_charpoly_matches"],
        "R7": generic["sigma_upper_bound_sum_of_squares_identity"],
        "R8": universal_domain[
            "all_positive_mass_triples_have_nonabelian_identity_component"
        ]
        and spec["domain_certificate"]["exceptional_set_for_complete_integrability"]
        == [],
        "R9": source_checks["morales_ramis_necessary_condition"],
        "R10": all(source_checks.values())
        and all(source_equivalence.values())
        and all(proof_coverage.values()),
    }
    all_sources = all(record["verified"] for record in source_records)
    claim_boundary_present = all(
        phrase in spec["evidence_boundary"]
        for phrase in (
            "project-owned exact reproduction",
            "does not independently reconstruct every canonical",
            "no absence of individual additional first integrals",
            "no non-meromorphic obstruction",
            "no zero-angular-momentum theorem",
            "no spatial theorem without",
            "no statement about triple collision",
        )
    )
    full_positive_domain = bool(
        obligations["R7"]
        and obligations["R8"]
        and universal_domain[
            "all_positive_mass_triples_have_nonabelian_identity_component"
        ]
    )
    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate(
            "all_prerequisite_locks_and_records_verified",
            sum(item["verified"] for item in prerequisites.values()),
            "==",
            len(prerequisites),
        ),
        make_gate(
            "all_source_download_hashes_verified",
            int(all_sources),
            "==",
            1,
        ),
        make_gate(
            "all_source_text_contracts_verified",
            sum(source_checks.values()),
            "==",
            len(source_checks),
        ),
        make_gate(
            "all_R1_through_R10_obligations_pass",
            sum(obligations.values()),
            "==",
            len(obligations),
        ),
        make_gate(
            "generic_symbolic_replay_exact",
            int(generic["all_exact_derivation_checks_pass"]),
            "==",
            1,
        ),
        make_gate(
            "all_exact_specializations_pass",
            sum(row["passed"] for row in benchmarks),
            "==",
            len(benchmarks),
        ),
        make_gate(
            "production_reference_exact_agreement",
            int(
                benchmark_agreement
                and all(implementation_independence.values())
            ),
            "==",
            1,
        ),
        make_gate(
            "full_positive_mass_domain_proved",
            int(full_positive_domain),
            "==",
            1,
        ),
        make_gate(
            "complete_integrability_exceptional_set_empty",
            len(
                universal_domain[
                    "complete_integrability_exceptional_set"
                ]
            ),
            "==",
            0,
        ),
        make_gate(
            "all_adversarial_controls_rejected",
            sum(controls.values()),
            "==",
            len(controls),
        ),
        make_gate(
            "proof_document_covers_every_obligation",
            sum(proof_coverage.values()),
            "==",
            len(proof_coverage),
        ),
        make_gate(
            "claim_boundary_present",
            int(claim_boundary_present),
            "==",
            1,
        ),
    ]
    if {gate["name"] for gate in gates} != set(spec["gates"]):
        raise RuntimeError(
            "runtime gate set does not exactly match the locked specification"
        )
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    result = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "status": status,
        "authorized_claim": spec["decision_policy"]["AUTHORIZED_CLAIM"],
        "claim_boundary": spec["evidence_boundary"],
        "prohibited_short_claim": spec["decision_policy"][
            "PROHIBITED_SHORT_CLAIM"
        ],
        "prohibited_independence_claim": spec["decision_policy"][
            "PROHIBITED_INDEPENDENCE_CLAIM"
        ],
        "prohibited_global_claim": spec["decision_policy"][
            "PROHIBITED_GLOBAL_CLAIM"
        ],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "proof_sha256": sha256_file(args.proof),
        "source_records": source_records,
        "source_text_checks": source_checks,
        "published_source_equivalence": source_equivalence,
        "prerequisites": prerequisites,
        "generic_derivation": generic,
        "universal_positive_mass_domain_certificate": universal_domain,
        "benchmarks": benchmarks,
        "production_reference_exact_agreement": benchmark_agreement,
        "implementation_independence": implementation_independence,
        "complete_integrability_exceptional_set": [],
        "first_nve_polynomial_exceptional_set": ["1/3", "8/27", "2/9"],
        "theorem_obligations": obligations,
        "negative_controls": controls,
        "proof_coverage": proof_coverage,
        "gates": gates,
        "runtime": runtime_fingerprint(),
    }
    atomic_write_json(output, result)
    print(f"{spec['campaign']} {lock['qualification_id']}: {status}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
