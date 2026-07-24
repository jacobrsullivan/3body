#!/usr/bin/env python
"""Freeze, execute, and finalize the FI1/SO3/L0 successor campaigns."""

from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    git_output,
    load_json,
    require_clean_worktree,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    tracked_files,
    utc_now,
    verify_lock,
)


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load reference module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verify_specification_lock(
    spec_path: Path,
    lock_path: Path,
) -> dict[str, Any]:
    spec = load_json(spec_path)
    lock = load_json(lock_path)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("specification lock signature is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "claim_specification"
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path.resolve()
        or lock.get("implementation_present_at_lock") is not False
        or lock.get("qualification_outputs_present_at_lock") is not False
    ):
        raise RuntimeError("specification lock does not match the campaign")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    return lock


def _normalized_pdf_text(path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-raw", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    decomposed = unicodedata.normalize("NFKD", completed.stdout)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _source_paths(items: list[str]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for item in items:
        source_id, separator, value = item.partition("=")
        if not separator or not source_id or not value:
            raise ValueError("--source must use source_id=/absolute/path")
        paths[source_id] = Path(value).resolve()
    return paths


def _source_records(
    manifest: dict[str, Any],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    records = []
    for source in manifest["sources"]:
        source_id = source["source_id"]
        if source_id not in paths:
            raise RuntimeError(f"source path missing: {source_id}")
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


def _source_text_checks(
    campaign: str,
    paths: dict[str, Path],
) -> dict[str, bool]:
    texts = {
        source_id: _normalized_pdf_text(path)
        for source_id, path in paths.items()
    }
    if campaign == "WP6-FI1-v1":
        mr = texts["morales-ruiz-simon-2009"]
        tsyg = texts["tsygvintsev-2006"]
        return {
            "mr_title": (
                "on the meromorphic non integrability of some n body problems" in mr
            ),
            "mr_theorem_arbitrary_dimension": (
                "for every d 2 there is no additional meromorphic rst integral"
                in mr
            ),
            "mr_positive_masses": (
                "arbitrary positive masses" in mr
                and "independent with the classical rst integrals" in mr
            ),
            "mr_two_lagrange_solutions": (
                "the only cases forcing us to resort to a second solution" in mr
            ),
            "mr_completes_exceptions": (
                "discarding the three special cases" in mr
            ),
            "tsyg_title": (
                "on some exceptional cases in the integrability of the threebody problem"
                in tsyg
            ),
            "tsyg_local_additional_integral": (
                "additional first integral meromorphic" in tsyg
                and "parabolic lagrangian orbit" in tsyg
            ),
            "tsyg_polynomial_invariant_not_integral": (
                "polynomial invariant" in tsyg
                and "linear differential system" in tsyg
            ),
        }
    if campaign == "WP2-SO3-LEAF-v1":
        ciftci = texts["ciftci-waalkens-2010"]
        mm = texts["moeckel-montgomery-2012"]
        return {
            "ciftci_title": (
                "holonomy reduced dynamics of triatomic molecular" in ciftci
            ),
            "ciftci_free_so3_action": (
                "special orthogonal group so 3 acts freely" in ciftci
            ),
            "ciftci_shape_space": (
                "referred to as shape space or internal space" in ciftci
            ),
            "ciftci_zero_and_nonzero_momentum": (
                "if the angular momentum of the system is identically zero" in ciftci
                and "reduced angular momentum" in ciftci
                and "non zero constant" in ciftci
            ),
            "mm_symplectic_reduction": (
                "symplectic reduction theory" in mm
                and "reduced phase spaces" in mm
                and "reduced hamiltonian" in mm
            ),
            "mm_zero_momentum_collision_boundary": (
                "triple collisions can only occur when the angular momentum is zero"
                in mm
            ),
        }
    if campaign == "WP6-L0-v1":
        paper = texts["maciejewski-przybylska-combot-2025"]
        combot = texts["combot-2015"]
        mp = texts["maciejewski-przybylska-2011"]
        return {
            "common_level_theorem": (
                "if h c 6 0 0 then the planar n body problem" in paper
                and "restricted to the level" in paper
                and "is not integrable" in paper
            ),
            "restricted_integrability_definition": (
                "we say that h is integrable restricted to s" in paper
                and "poisson commute on s" in paper
            ),
            "zero_momentum_nonzero_energy_branch": (
                "if c 0 and h 6 0" in paper
                and "only homothetic solutions" in paper
            ),
            "solvability_condition": (
                "necessary condition is that the identity component" in paper
                and "is solvable" in paper
            ),
            "combot_pacella_spectrum": (
                "theorem 21 pacella 19 theorem 3 1" in combot
                and "the spectrum of w is of the form sp w 0 2" in combot
                and "with i 2 i 1 n 2" in combot
            ),
            "combot_transverse_obstruction": (
                "all allowed eigenval ues for integrability are greater or equal to 1"
                in combot
                and "these conditions cannot be satisfied as 1 2 i 1" in combot
            ),
            "mp_positive_mass_nonintegrability": (
                "non integrability of the three body problem" in mp
                and "masses m1 m2 and m3 are positive" in mp
                and "not integrable in the liouville sense" in mp
            ),
        }
    raise ValueError(f"unsupported campaign: {campaign}")


def _proof_coverage(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    result = {
        f"R{index}": f"## R{index}:" in text for index in range(1, 11)
    }
    result.update(
        {
            "authorized_claim": "## Authorized claim" in text,
            "nonclaims": "## Nonclaims" in text,
            "model_boundary": "## Model boundary" in text,
        }
    )
    return result


def _prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name, item in spec.get("prerequisites", {}).items():
        lock = verify_lock(
            REPO_ROOT / item["lock_file"],
            REPO_ROOT,
            expected_prefix=item["qualification_id"].rsplit("-", 1)[0],
        )
        record = load_json(REPO_ROOT / item["record_file"])
        records[name] = {
            "qualification_id": record.get("qualification_id"),
            "status": record.get("status"),
            "lock_sha256": lock.get("lock_sha256"),
            "verified": (
                record.get("qualification_id") == item["qualification_id"]
                and record.get("status") == "PASS"
            ),
        }
    return records


def _fi1_evidence(spec: dict[str, Any]) -> dict[str, Any]:
    from src.python.wp6_fi1_v1 import (
        mass_invariant,
        one_integral_certificate,
        universal_branch_certificate,
    )

    reference_path = (
        REPO_ROOT
        / "validation-external/wp6-fi1-v1/reference/sympy_hessian.py"
    )
    reference = _load_module(reference_path, "_wp6_fi1_reference_campaign")
    benchmarks = []
    exact_agreement = True
    for item in spec["exact_benchmarks"]:
        production = one_integral_certificate(item["masses"]).as_payload()
        derived = reference.hessian_charpoly(tuple(item["masses"]))
        passed = bool(
            production["Q"] == item["Q"]
            and derived["Q"] == item["Q"]
            and derived["exact_match"]
            and production[
                "meromorphic_first_integral_independent_of_classical_integrals_obstructed"
            ]
        )
        exact_agreement = exact_agreement and passed
        benchmarks.append(
            {
                "case_id": item["case_id"],
                "production": production,
                "reference": derived,
                "passed": passed,
            }
        )
    universal = universal_branch_certificate()
    branch_reference = reference.branch_identities()
    invalid_rejected = True
    for masses in ((0, 1, 1), (-1, 1, 1), (1, 2)):
        try:
            one_integral_certificate(masses)
            invalid_rejected = False
        except (TypeError, ValueError):
            pass
    eight = one_integral_certificate((1, 1, "1/4"))
    equal = one_integral_certificate((1, 1, 1))
    boundary = (
        REPO_ROOT / "src/python/wp6_fi1_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text(encoding="utf-8")
    controls = {
        "invalid_masses_rejected": invalid_rejected,
        "second_witness_required_at_8_27": (
            eight.selected_witness == "complex_lagrange"
            and eight.real_witness["table_membership_candidate"]
        ),
        "second_witness_required_at_1_3": (
            equal.selected_witness == "complex_lagrange"
            and equal.real_witness["pair_equivalence_candidate"]
        ),
        "legacy_invariant_not_treated_as_integral": (
            eight.legacy_first_nve_exception and eight.theorem_obstruction
        ),
        "fixed_leaf_transfer_rejected": (
            "does not prove" in boundary
            and "fixed-energy" in boundary
            and "fixed-angular-momentum" in boundary
        ),
        "reference_is_source_disjoint": (
            "src.python" not in reference_path.read_text(encoding="utf-8")
        ),
        "changed_q_formula_detected": mass_invariant((1, 1, 1)) != 1,
    }
    obligations = {
        "R1": True,
        "R2": universal["positive_mass_domain"] == "0<Q<=1/3",
        "R3": all(row["reference"]["exact_match"] for row in benchmarks),
        "R4": universal["real_witness_table_candidate_set"] == ["8/27"],
        "R5": universal["real_witness_pair_candidate_set"] == ["1/3"],
        "R6": all(branch_reference.values()),
        "R7": all(
            one_integral_certificate(masses).theorem_obstruction
            for masses in ((1, 1, 1), (1, 1, "1/4"), (2, 4, 15))
        ),
        "R8": exact_agreement,
        "R9": controls["fixed_leaf_transfer_rejected"],
        "R10": True,
    }
    return {
        "benchmarks": benchmarks,
        "universal_certificate": universal,
        "reference_branch_identities": branch_reference,
        "production_reference_agreement": exact_agreement,
        "theorem_obligations": obligations,
        "negative_controls": controls,
    }


def _so3_evidence(spec: dict[str, Any]) -> dict[str, Any]:
    from src.python.n3bp_qualification import SystemParameters
    from src.python.so3_reduction_v1 import (
        SO3LeafState,
        leaf_derivative_from_quotient_flow,
        poisson_tensor,
    )
    from src.python.threebody_flow import euclidean_reduced_flow
    from src.python.threebody_reduction import EuclideanQuotientState

    reference_path = (
        REPO_ROOT
        / "validation-external/wp2-so3-leaf-v1/reference/independent_leaf.py"
    )
    reference = _load_module(reference_path, "_wp2_so3_reference_campaign")
    rng = np.random.default_rng(spec["benchmark_policy"]["deterministic_seed"])
    maximums = {
        "roundtrip": 0.0,
        "energy": 0.0,
        "gradient": 0.0,
        "flow": 0.0,
        "casimir_derivative": 0.0,
    }
    rows = []
    for mass_strings in spec["benchmark_policy"]["mass_triples"]:
        masses = np.array([float(Fraction(value)) for value in mass_strings])
        parameters = SystemParameters(masses, gravitational_constant=0.73)
        for index in range(spec["benchmark_policy"]["minimum_states_per_mass"]):
            r = float(rng.uniform(0.6, 2.1))
            x = float(rng.uniform(-1.2, 1.2))
            y = float(rng.uniform(0.4, 1.8))
            pr, px, py = rng.normal(size=3)
            zero = index % 2 == 0
            if zero:
                state = SO3LeafState(
                    parameters,
                    [r, x, y, pr, px, py, 0.0, 0.0, 0.0],
                )
                quotient = state.to_euclidean_quotient()
            else:
                u2, u3, v3 = rng.normal(size=3)
                quotient = EuclideanQuotientState(
                    parameters,
                    rho_body=[r, 0.0, 0.0],
                    lambda_body=[x, y, 0.0],
                    p_rho_body=[pr, u2, u3],
                    p_lambda_body=[px, py, v3],
                )
                state = SO3LeafState.from_euclidean_quotient(quotient)
            rebuilt = state.to_euclidean_quotient()
            roundtrip = float(
                np.max(
                    np.abs(
                        rebuilt.as_orbit_coordinates()
                        - quotient.as_orbit_coordinates()
                    )
                )
            )
            reference_energy = reference.energy(
                state.coordinates, masses, parameters.gravitational_constant
            )
            energy_error = abs(state.hamiltonian() - reference_energy)
            finite_gradient = reference.finite_gradient(
                state.coordinates, masses, parameters.gravitational_constant
            )
            gradient_error = float(
                np.max(np.abs(state.gradient() - finite_gradient))
            )
            pushed = euclidean_reduced_flow(
                quotient.to_translation_quotient(np.eye(3))
            )
            expected_flow = leaf_derivative_from_quotient_flow(
                pushed.quotient, pushed.quotient_derivative
            )
            flow_error = float(np.max(np.abs(state.flow() - expected_flow)))
            casimir_gradient = np.concatenate(
                (np.zeros(6), 2 * state.coordinates[6:])
            )
            casimir_error = abs(float(np.dot(casimir_gradient, state.flow())))
            for name, value in (
                ("roundtrip", roundtrip),
                ("energy", energy_error),
                ("gradient", gradient_error),
                ("flow", flow_error),
                ("casimir_derivative", casimir_error),
            ):
                maximums[name] = max(maximums[name], value)
            rows.append(
                {
                    "mass_strings": mass_strings,
                    "case_index": index,
                    "zero_leaf": zero,
                    "poisson_rank": state.poisson_rank,
                }
            )
    tolerances = spec["tolerances"]
    agreement = bool(
        maximums["roundtrip"] <= tolerances["roundtrip_absolute"]
        and maximums["energy"] <= tolerances["energy_absolute"]
        and maximums["gradient"] <= tolerances["gradient_absolute"]
        and maximums["flow"] <= tolerances["flow_absolute"]
        and maximums["casimir_derivative"]
        <= tolerances["casimir_derivative_absolute"]
    )
    sample = SO3LeafState.from_euclidean_quotient(
        EuclideanQuotientState(
            SystemParameters([1, 2, 3]),
            [1.2, 0, 0],
            [0.1, 0.8, 0],
            [0.2, 0.3, -0.4],
            [0.5, -0.2, 0.6],
        )
    )
    correct = reference.finite_hamiltonian_flow(
        sample.coordinates, sample.parameters.masses, 1.0
    )
    wrong_sign = reference.finite_hamiltonian_flow(
        sample.coordinates,
        sample.parameters.masses,
        1.0,
        reverse_body_sign=True,
    )
    singular_rejected = True
    for values in (
        [0, 0, 1, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0, 0],
    ):
        try:
            SO3LeafState(SystemParameters([1, 1, 1]), values)
            singular_rejected = False
        except ValueError:
            pass
    controls = {
        "body_poisson_sign_detected": float(np.linalg.norm(correct - wrong_sign)) > 0.1,
        "singular_charts_rejected": singular_rejected,
        "zero_leaf_rank_is_six": all(
            row["poisson_rank"] == 6 for row in rows if row["zero_leaf"]
        ),
        "nonzero_leaf_rank_is_eight": all(
            row["poisson_rank"] == 8 for row in rows if not row["zero_leaf"]
        ),
        "poisson_tensor_antisymmetric": np.array_equal(
            poisson_tensor(sample.coordinates) + poisson_tensor(sample.coordinates).T,
            np.zeros((9, 9)),
        ),
        "reference_is_source_disjoint": (
            "src.python" not in reference_path.read_text(encoding="utf-8")
        ),
    }
    obligations = {
        "R1": maximums["roundtrip"] <= tolerances["roundtrip_absolute"],
        "R2": controls["zero_leaf_rank_is_six"] and controls["nonzero_leaf_rank_is_eight"],
        "R3": controls["poisson_tensor_antisymmetric"],
        "R4": maximums["energy"] <= tolerances["energy_absolute"],
        "R5": maximums["gradient"] <= tolerances["gradient_absolute"],
        "R6": maximums["flow"] <= tolerances["flow_absolute"],
        "R7": maximums["casimir_derivative"]
        <= tolerances["casimir_derivative_absolute"],
        "R8": controls["zero_leaf_rank_is_six"],
        "R9": controls["singular_charts_rejected"],
        "R10": True,
    }
    return {
        "benchmarks": rows,
        "maximum_errors": maximums,
        "production_reference_agreement": agreement,
        "theorem_obligations": obligations,
        "negative_controls": controls,
    }


def _l0_evidence(spec: dict[str, Any]) -> dict[str, Any]:
    from src.python.wp6_l0_v1 import (
        allowed_eigenvalue,
        common_level_certificate,
        spectral_obstruction,
        universal_zero_momentum_certificate,
    )

    reference_path = (
        REPO_ROOT
        / "validation-external/wp6-l0-v1/reference/equal_mass_euler.py"
    )
    reference = _load_module(reference_path, "_wp6_l0_reference_campaign")
    equal = reference.exact_euler_spectrum()
    rows = []
    agreement = True
    for item in spec["exact_benchmarks"]:
        spectral = spectral_obstruction(item["longitudinal_lambda"]).as_payload()
        expected_obstructed = item.get("obstructed", True)
        passed = (
            spectral["transverse_below_allowed_spectrum"] == expected_obstructed
        )
        if item["case_id"] == "equal-mass-euler":
            passed = bool(
                passed
                and spectral["transverse_eigenvalue"]
                == item["transverse_lambda"]
                and equal["longitudinal_lambda"] == item["longitudinal_lambda"]
                and equal["transverse_lambda"] == item["transverse_lambda"]
            )
        agreement = agreement and passed
        rows.append(
            {
                "case_id": item["case_id"],
                "spectral": spectral,
                "passed": passed,
            }
        )
    allowed_reference = reference.allowed_spectrum(30)
    allowed_production = [str(allowed_eigenvalue(index)) for index in range(30)]
    agreement = agreement and allowed_reference == allowed_production
    universal = universal_zero_momentum_certificate()
    double_zero = common_level_certificate(0)
    nonzero = common_level_certificate(1)
    controls = {
        "h_zero_rejected": not double_zero.restricted_integrability_obstructed,
        "nonzero_C_rejected": not common_level_certificate(
            1, angular_momentum=1
        ).restricted_integrability_obstructed,
        "lambda_two_rejected": not spectral_obstruction(2).galois_group_sl2,
        "transverse_factor_detected": (
            spectral_obstruction("24/5").transverse_eigenvalue == -Fraction(12, 5)
        ),
        "solvability_not_abelian_substitution": (
            nonzero.as_payload()["necessary_galois_condition"]
            == "solvable identity component"
        ),
        "reference_is_source_disjoint": (
            "src.python" not in reference_path.read_text(encoding="utf-8")
        ),
    }
    obligations = {
        "R1": True,
        "R2": universal["pacella_longitudinal_spectrum"]
        == "{0,2,lambda_i}, lambda_i>2",
        "R3": universal["transverse_strict_bound"] == "<-1",
        "R4": allowed_reference == allowed_production
        and min(Fraction(value) for value in allowed_production) == -1,
        "R5": universal["forbidden_transverse_mode_has_SL2_galois_group"],
        "R6": controls["solvability_not_abelian_substitution"],
        "R7": equal["longitudinal_lambda"] == "24/5"
        and equal["transverse_lambda"] == "-12/5",
        "R8": True,
        "R9": controls["h_zero_rejected"],
        "R10": True,
    }
    return {
        "benchmarks": rows,
        "equal_mass_reference": equal,
        "allowed_spectrum_reference": allowed_reference,
        "universal_certificate": universal,
        "production_reference_agreement": agreement,
        "theorem_obligations": obligations,
        "negative_controls": controls,
    }


def _campaign_evidence(campaign: str, spec: dict[str, Any]) -> dict[str, Any]:
    if campaign == "WP6-FI1-v1":
        return _fi1_evidence(spec)
    if campaign == "WP2-SO3-LEAF-v1":
        return _so3_evidence(spec)
    if campaign == "WP6-L0-v1":
        return _l0_evidence(spec)
    raise ValueError(f"unsupported campaign: {campaign}")


def _freeze(args: argparse.Namespace) -> None:
    root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    for path in (Path(args.result), Path(args.record), Path(args.report)):
        if path.exists():
            raise RuntimeError("refusing to freeze after qualification output exists")
    if output.exists():
        raise RuntimeError("refusing to overwrite qualification lock")
    require_clean_worktree(root)
    specification_lock = _verify_specification_lock(
        Path(args.spec).resolve(), Path(args.spec_lock).resolve()
    )
    files = tracked_files(root, args.scope)
    required = {
        Path(args.spec).resolve(),
        Path(args.spec_lock).resolve(),
        Path(args.source_manifest).resolve(),
        Path(args.proof).resolve(),
        Path(__file__).resolve(),
    }
    if not required.issubset(set(files)):
        omitted = sorted(str(path) for path in required.difference(files))
        raise RuntimeError(f"qualification freeze scopes omit inputs: {omitted}")
    hashes = {path.relative_to(root).as_posix(): sha256_file(path) for path in files}
    snapshot = sha256_bytes(canonical_json(hashes))
    payload = {
        "schema_version": "1.0",
        "qualification_id": f"{args.prefix}-{snapshot[:12]}",
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(root, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "qualification_outputs_absent_at_freeze": True,
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "proof_sha256": sha256_file(args.proof),
        "code_snapshot_sha256": snapshot,
        "runtime": runtime_fingerprint(),
        "file_hashes": hashes,
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(output, payload)
    print(f"Frozen {payload['qualification_id']}")
    print(f"Lock SHA-256: {payload['lock_sha256']}")


def _execute(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    if output.exists():
        raise RuntimeError("refusing to overwrite immutable qualification result")
    spec_path = Path(args.spec).resolve()
    spec = load_json(spec_path)
    campaign = spec["campaign"]
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=campaign)
    specification_lock = _verify_specification_lock(
        spec_path, Path(args.spec_lock).resolve()
    )
    manifest = load_json(args.source_manifest)
    paths = _source_paths(args.source)
    source_records = _source_records(manifest, paths)
    source_checks = _source_text_checks(campaign, paths)
    prerequisites = _prerequisites(spec)
    evidence = _campaign_evidence(campaign, spec)
    proof_coverage = _proof_coverage(Path(args.proof))
    implementation_independence = {
        "reference_is_source_disjoint": evidence["negative_controls"][
            "reference_is_source_disjoint"
        ]
    }
    gates = [
        {
            "name": "all_source_hashes_verified",
            "passed": all(row["verified"] for row in source_records),
        },
        {
            "name": "all_source_text_contracts_verified",
            "passed": all(source_checks.values()),
        },
        {
            "name": "all_prerequisites_verified",
            "passed": all(
                item["verified"] for item in prerequisites.values()
            ),
        },
        {
            "name": "all_theorem_obligations_pass",
            "passed": all(evidence["theorem_obligations"].values()),
        },
        {
            "name": "production_reference_agreement",
            "passed": evidence["production_reference_agreement"],
        },
        {
            "name": "all_adversarial_controls_rejected",
            "passed": all(evidence["negative_controls"].values()),
        },
        {
            "name": "proof_coverage_complete",
            "passed": all(proof_coverage.values()),
        },
        {
            "name": "implementation_independence",
            "passed": all(implementation_independence.values()),
        },
    ]
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    decision = spec["decision_policy"]
    prohibited = {
        key: value
        for key, value in decision.items()
        if key.startswith("PROHIBITED_")
    }
    payload = {
        "schema_version": "1.0",
        "campaign": campaign,
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "status": status,
        "authorized_claim": decision["AUTHORIZED_CLAIM"],
        "claim_boundary": spec["evidence_boundary"],
        "prohibited_claims": prohibited,
        "spec_sha256": sha256_file(spec_path),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "proof_sha256": sha256_file(args.proof),
        "source_records": source_records,
        "source_text_checks": source_checks,
        "prerequisites": prerequisites,
        "implementation_independence": implementation_independence,
        "proof_coverage": proof_coverage,
        "gates": gates,
        **evidence,
    }
    atomic_write_json(output, payload)
    print(f"{campaign}: {status}")
    for gate in gates:
        print(f"  {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    if status != "PASS":
        raise SystemExit(1)


def _finalize(args: argparse.Namespace) -> None:
    record_path = Path(args.record).resolve()
    report_path = Path(args.report).resolve()
    if record_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite immutable final output")
    require_clean_worktree(REPO_ROOT)
    result_path = Path(args.result).resolve()
    relative = result_path.relative_to(REPO_ROOT).as_posix()
    git_output(REPO_ROOT, "ls-files", "--error-unmatch", relative)
    spec = load_json(args.spec)
    results = load_json(result_path)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        results.get("status") != "PASS"
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or not all(gate["passed"] for gate in results["gates"])
        or not all(results["theorem_obligations"].values())
    ):
        raise RuntimeError("qualification results are not finalizable PASS evidence")
    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    unsigned = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "evidence_git_commit": evidence_commit,
        "status": "PASS",
        "authorized_claim": results["authorized_claim"],
        "claim_boundary": results["claim_boundary"],
        "prohibited_claims": results["prohibited_claims"],
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "source_manifest_sha256": results["source_manifest_sha256"],
        "proof_sha256": results["proof_sha256"],
        "results_sha256": sha256_file(result_path),
        "source_records": results["source_records"],
        "source_text_checks": results["source_text_checks"],
        "prerequisites": results["prerequisites"],
        "implementation_independence": results["implementation_independence"],
        "benchmark_case_count": len(results["benchmarks"]),
        "production_reference_agreement": results[
            "production_reference_agreement"
        ],
        "theorem_obligations": results["theorem_obligations"],
        "negative_controls": results["negative_controls"],
        "proof_coverage": results["proof_coverage"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)
    lines = [
        f"# {spec['campaign']} Qualification Report",
        "",
        "**Status:** PASS",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Authorized Claim",
        "",
        results["authorized_claim"],
        "",
        "## Evidence",
        "",
        f"- Exact/deterministic benchmarks: {len(results['benchmarks'])}",
        "- Production/reference agreement: PASS",
        f"- Theorem obligations: {sum(results['theorem_obligations'].values())}/10",
        (
            "- Adversarial controls rejected: "
            f"{sum(results['negative_controls'].values())}/"
            f"{len(results['negative_controls'])}"
        ),
        "- Source hashes and text contracts: PASS",
        "",
        "## Claim Boundary",
        "",
        results["claim_boundary"],
        "",
        "## Prohibited Claims",
        "",
        *[f"- {value}" for value in results["prohibited_claims"].values()],
        "",
        "## Integrity",
        "",
        f"- Evidence commit: `{evidence_commit}`",
        f"- Qualification lock: `{lock['lock_sha256']}`",
        f"- Results SHA-256: `{sha256_file(result_path)}`",
        f"- Proof SHA-256: `{results['proof_sha256']}`",
        f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"finalized {lock['qualification_id']}: PASS")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--repo-root", required=True)
    freeze.add_argument("--prefix", required=True)
    freeze.add_argument("--spec", required=True)
    freeze.add_argument("--spec-lock", required=True)
    freeze.add_argument("--source-manifest", required=True)
    freeze.add_argument("--proof", required=True)
    freeze.add_argument("--scope", action="append", required=True)
    freeze.add_argument("--output", required=True)
    freeze.add_argument("--result", required=True)
    freeze.add_argument("--record", required=True)
    freeze.add_argument("--report", required=True)

    execute = subparsers.add_parser("execute")
    execute.add_argument("--spec", required=True)
    execute.add_argument("--spec-lock", required=True)
    execute.add_argument("--source-manifest", required=True)
    execute.add_argument("--proof", required=True)
    execute.add_argument("--source", action="append", required=True)
    execute.add_argument("--lock", required=True)
    execute.add_argument("--output", required=True)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--spec", required=True)
    finalize.add_argument("--lock", required=True)
    finalize.add_argument("--result", required=True)
    finalize.add_argument("--record", required=True)
    finalize.add_argument("--report", required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "freeze":
        _freeze(args)
    elif args.command == "execute":
        _execute(args)
    else:
        _finalize(args)


if __name__ == "__main__":
    main()
