#!/usr/bin/env python
"""Freeze, execute, and finalize the WP6-COMMON-v1 campaign."""

from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for search_path in (REPO_ROOT, VALIDATION_ROOT):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

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
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load reference module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
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
        if source_id in paths:
            raise ValueError(f"duplicate source id: {source_id}")
        path = Path(value)
        if not path.is_absolute():
            raise ValueError(f"source path must be absolute: {value}")
        paths[source_id] = path.resolve()
    return paths


def _source_records(
    manifest: dict[str, Any],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    expected_ids = {item["source_id"] for item in manifest["sources"]}
    if set(paths) != expected_ids:
        missing = sorted(expected_ids.difference(paths))
        extra = sorted(set(paths).difference(expected_ids))
        raise RuntimeError(f"source set mismatch: missing={missing}, extra={extra}")
    records = []
    for source in manifest["sources"]:
        source_id = source["source_id"]
        path = paths[source_id]
        if not path.is_file():
            raise RuntimeError(f"source payload missing: {path}")
        observed = sha256_file(path)
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


def _source_text_checks(paths: dict[str, Path]) -> dict[str, bool]:
    primary = _normalized_pdf_text(paths["maciejewski-przybylska-combot-2025"])
    predecessor = _normalized_pdf_text(paths["combot-2011"])
    return {
        "primary_exact_title": (
            "non integrability of the n body problem andrzej j maciejewski" in primary
        ),
        "primary_theorem_1_1_common_level": (
            "theorem 1 1 if h c 6 0 0 then the planar n body problem" in primary
            and "positive masses" in primary
            and "restricted to the level mh c is not integrable" in primary
        ),
        "primary_restricted_integrability_definition": (
            "definition 2 1 consider a hamiltonian system" in primary
            and "we say that h is integrable restricted to s" in primary
            and "rational functions" in primary
            and "poisson commute on s" in primary
        ),
        "primary_zero_momentum_branch": (
            "if c 0 and h 6 0 then we have at our disposal only homothetic solutions"
            in primary
        ),
        "primary_noncircular_branch": (
            "keplerian orbits with non zero eccentricity" in primary
            and "lemma 5 1 if e 0 and 0 then the identity component" in primary
            and "is not solvable" in primary
        ),
        "primary_circular_complex_branch": (
            "the variational equation re duces to an equation with constant coefficients"
            in primary
            and "complex part of the phase space" in primary
            and "lemma 5 3 if 0 then the identity component" in primary
        ),
        "primary_solvable_necessary_condition": (
            "necessary condition is that the identity component" in primary
            and "is solvable" in primary
        ),
        "predecessor_exact_title": (
            "non integrability of the n body problem with non zero angular momentum"
            in predecessor
        ),
        "predecessor_common_surface": (
            "surface of equation h c h0 c0" in predecessor
            and "newtonian interaction in the plane" in predecessor
        ),
        "predecessor_double_zero_limitation": (
            "remark 7 the only left case is h c 0" in predecessor
            and "one would need a new particular orbit explicit" in predecessor
            and "no such orbit is known" in predecessor
        ),
    }


def _signed_record_valid(record: dict[str, Any]) -> bool:
    unsigned = dict(record)
    signature = unsigned.pop("record_payload_sha256", None)
    return signature == sha256_bytes(canonical_json(unsigned))


def _prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name, item in spec["prerequisites"].items():
        lock_path = REPO_ROOT / item["lock_file"]
        record_path = REPO_ROOT / item["record_file"]
        lock_hash_match = sha256_file(lock_path) == item["lock_file_sha256"]
        record_hash_match = sha256_file(record_path) == item["record_file_sha256"]
        lock = verify_lock(
            lock_path,
            REPO_ROOT,
            expected_prefix=item["qualification_id"].rsplit("-", 1)[0],
        )
        record = load_json(record_path)
        record_signature_valid = _signed_record_valid(record)
        identity_match = (
            record.get("qualification_id") == item["qualification_id"]
            and record.get("status") == "PASS"
            and record.get("lock_sha256") == lock.get("lock_sha256")
        )
        records[name] = {
            "qualification_id": record.get("qualification_id"),
            "status": record.get("status"),
            "lock_file_sha256": sha256_file(lock_path),
            "record_file_sha256": sha256_file(record_path),
            "lock_hash_match": lock_hash_match,
            "record_hash_match": record_hash_match,
            "record_signature_valid": record_signature_valid,
            "identity_match": identity_match,
            "verified": bool(
                lock_hash_match
                and record_hash_match
                and record_signature_valid
                and identity_match
            ),
        }
    return records


def _proof_coverage(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    result = {f"R{index}": f"## R{index}:" in text for index in range(1, 11)}
    result.update(
        {
            "authorized_claim": "## Authorized claim" in text,
            "nonclaims": "## Nonclaims" in text,
            "model_boundary": "## Model boundary" in text,
        }
    )
    return result


def _expect_value_error(function: Any, *arguments: Any) -> bool:
    try:
        function(*arguments)
    except (TypeError, ValueError, OverflowError):
        return True
    return False


def _campaign_evidence(spec: dict[str, Any]) -> dict[str, Any]:
    from src.python.wp6_common_level_v1 import (
        CIRCULAR_RELATION_COMPLEX_WITNESS,
        NONCIRCULAR_NONZERO_MOMENTUM,
        UNQUALIFIED_DOUBLE_ZERO,
        ZERO_MOMENTUM_NONZERO_ENERGY,
        circular_discriminant_certificate,
        circular_discriminant_squared,
        classify_common_level,
        equal_mass_euler_certificate,
        generic_discriminant_certificate,
        generic_discriminant_squared,
        generic_nve_coefficients,
        kepler_relation_certificate,
        universal_common_level_certificate,
    )

    reference_path = (
        REPO_ROOT / "validation-external/wp6-common-level-v1/reference/euler_conic.py"
    )
    reference = _load_module(reference_path, "_wp6_common_level_reference_campaign")

    benchmarks: list[dict[str, Any]] = []
    level_agreement = True
    relation_agreement = True
    euler_item: dict[str, Any] | None = None
    for item in spec["exact_benchmarks"]:
        if "h" in item:
            production = classify_common_level(item["h"], item["c"], item["mu"])
            independent = reference.classify_relation(item["h"], item["c"], item["mu"])
            relation = kepler_relation_certificate(
                item["h"],
                item["c"],
                item["mu"],
                item.get("expected_e_squared"),
            )
            expected_e = item.get(
                "expected_e_squared", str(production.eccentricity_squared)
            )
            passed = bool(
                production.branch == item["expected_branch"]
                and independent["branch"] == item["expected_branch"]
                and independent["qualified"] is production.qualified
                and str(production.eccentricity_squared) == expected_e
                and independent["eccentricity_squared"] == expected_e
                and relation["relation_holds"]
            )
            level_agreement = level_agreement and passed
            relation_agreement = relation_agreement and bool(relation["relation_holds"])
            benchmarks.append(
                {
                    "case_id": item["case_id"],
                    "production": production.as_payload(),
                    "reference": independent,
                    "kepler_relation": relation,
                    "passed": passed,
                }
            )
        else:
            euler_item = item

    if euler_item is None:
        raise RuntimeError("equal-mass Euler benchmark is missing")

    production_euler = equal_mass_euler_certificate()
    reference_euler = reference.exact_equal_mass_euler_spectrum()
    generic = generic_discriminant_certificate(
        production_euler["physical_delta"], euler_item["generic_e"]
    )
    reference_generic = reference.generic_discriminant(
        production_euler["physical_delta"], euler_item["generic_e"]
    )
    circular = circular_discriminant_certificate(production_euler["physical_delta"])
    reference_circular = reference.circular_discriminant(
        production_euler["physical_delta"]
    )
    euler_passed = bool(
        production_euler["spectrum"] == euler_item["expected_C_spectrum"]
        and reference_euler["spectrum"] == euler_item["expected_C_spectrum"]
        and production_euler["physical_delta"] == euler_item["expected_delta"]
        and reference_euler["physical_delta"] == euler_item["expected_delta"]
        and production_euler["exact_spectrum_verified"]
        and generic["Delta_squared"]
        == str(Fraction(euler_item["expected_generic_Delta"]) ** 2)
        and reference_generic["Delta_squared"]
        == str(Fraction(euler_item["expected_generic_Delta"]) ** 2)
        and circular["Delta_squared"] == euler_item["expected_circular_Delta_squared"]
        and reference_circular["Delta_squared"]
        == euler_item["expected_circular_Delta_squared"]
    )
    benchmarks.append(
        {
            "case_id": euler_item["case_id"],
            "production": production_euler,
            "reference": reference_euler,
            "generic_discriminant": generic,
            "reference_generic_discriminant": reference_generic,
            "circular_discriminant": circular,
            "reference_circular_discriminant": reference_circular,
            "passed": euler_passed,
        }
    )

    derived_relation = reference.derive_kepler_relation()
    coefficient_arguments = ("7/5", "1", "1186/25", "3")
    production_coefficients = generic_nve_coefficients(*coefficient_arguments)
    reference_coefficients = reference.generic_nve_coefficients(*coefficient_arguments)
    coefficient_agreement = production_coefficients == reference_coefficients

    universal = universal_common_level_certificate()
    zero = classify_common_level("-3/2", 0)
    circular_level = classify_common_level("-1/2", 1)
    double_zero = classify_common_level(0, 0)
    boundary = (
        REPO_ROOT / "src/python/wp6_common_level_v1/QUALIFICATION_BOUNDARY.md"
    ).read_text(encoding="utf-8")
    controls = {
        "double_zero_rejected": (
            not double_zero.qualified and double_zero.branch == UNQUALIFIED_DOUBLE_ZERO
        ),
        "zero_momentum_predecessor_required": (
            zero.branch == ZERO_MOMENTUM_NONZERO_ENERGY
            and zero.requires_wp6_l0_predecessor
        ),
        "real_circular_orbit_rejected_as_witness": (
            circular_level.branch == CIRCULAR_RELATION_COMPLEX_WITNESS
            and not circular_level.real_circular_orbit_is_obstruction_witness
            and circular_level.witness == "EULER_MOULTON_COMPLEX_HOMOGRAPHIC"
        ),
        "nonpositive_generic_delta_rejected": all(
            _expect_value_error(generic_discriminant_squared, value, 1)
            for value in (0, -1)
        ),
        "nonpositive_circular_delta_rejected": all(
            _expect_value_error(circular_discriminant_squared, value)
            for value in (0, -1)
        ),
        "altered_discriminant_root_rejected": _expect_value_error(
            generic_nve_coefficients, "7/5", 1, "1187/25", 3
        ),
        "coefficient_pole_rejected": _expect_value_error(
            generic_nve_coefficients, "7/5", 1, "1186/25", 2
        ),
        "one_integral_transfer_rejected": (
            universal["one_additional_integral_excluded"] is False
            and "does not transfer" in boundary
        ),
        "spatial_transfer_rejected": (
            universal["spatial_claim"] is False
            and "spatial three-body theorem" in boundary
        ),
        "non_rational_transfer_rejected": (
            universal["non_rational_regularity_claim"] is False
            and "non-rational" in boundary
        ),
        "pointwise_domain_claim_rejected": (
            universal["pointwise_every_open_domain_claim"] is False
            and "pointwise nonintegrability" in boundary
        ),
        "regular_so3_chart_transfer_rejected": (
            universal["collinear_witness_in_regular_noncollinear_so3_chart"] is False
            and "regular noncollinear SO(3) chart" in boundary
        ),
        "reference_is_source_disjoint": (
            "src.python" not in reference_path.read_text(encoding="utf-8")
        ),
    }

    branch_set = {
        row["production"]["branch"]
        for row in benchmarks
        if "branch" in row["production"]
    }
    required_branches = {
        ZERO_MOMENTUM_NONZERO_ENERGY,
        NONCIRCULAR_NONZERO_MOMENTUM,
        CIRCULAR_RELATION_COMPLEX_WITNESS,
        UNQUALIFIED_DOUBLE_ZERO,
    }
    production_reference_agreement = bool(
        level_agreement
        and relation_agreement
        and euler_passed
        and derived_relation["relation_verified"]
        and coefficient_agreement
    )
    obligations = {
        "R1": False,
        "R2": False,
        "R3": universal["direct_common_level_theorem_not_fi1_transfer"],
        "R4": (
            branch_set == required_branches
            and universal["branch_conditions_pairwise_disjoint"]
            and universal["all_non_double_zero_levels_covered"]
        ),
        "R5": (relation_agreement and derived_relation["relation_verified"]),
        "R6": bool(production_euler["exact_spectrum_verified"] and euler_passed),
        "R7": bool(
            generic["all_terms_strictly_positive"]
            and generic["strictly_positive"]
            and reference_generic["strictly_positive"]
        ),
        "R8": bool(
            circular["strictly_positive"]
            and reference_circular["strictly_positive"]
            and controls["real_circular_orbit_rejected_as_witness"]
        ),
        "R9": coefficient_agreement,
        "R10": all(controls.values()),
    }
    return {
        "benchmarks": benchmarks,
        "universal_certificate": universal,
        "derived_kepler_relation": derived_relation,
        "generic_nve_coefficient_sample": {
            "production": production_coefficients,
            "reference": reference_coefficients,
            "exact_agreement": coefficient_agreement,
        },
        "production_reference_agreement": production_reference_agreement,
        "theorem_obligations": obligations,
        "negative_controls": controls,
    }


def _freeze(args: argparse.Namespace) -> None:
    root = Path(args.repo_root).resolve()
    if root != REPO_ROOT:
        raise RuntimeError(f"unexpected repository root: {root}")
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
        VALIDATION_ROOT / "qualification_tools.py",
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
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
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
        raise RuntimeError("refusing to overwrite immutable result")
    spec_path = Path(args.spec).resolve()
    spec = load_json(spec_path)
    if spec.get("campaign") != "WP6-COMMON-v1":
        raise RuntimeError("unexpected campaign specification")
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    specification_lock = _verify_specification_lock(
        spec_path, Path(args.spec_lock).resolve()
    )
    if (
        lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("qualification lock uses another specification lock")

    manifest = load_json(args.source_manifest)
    paths = _source_paths(args.source)
    source_records = _source_records(manifest, paths)
    source_checks = _source_text_checks(paths)
    prerequisites = _prerequisites(spec)
    evidence = _campaign_evidence(spec)
    evidence["theorem_obligations"]["R1"] = bool(
        all(row["verified"] for row in source_records) and all(source_checks.values())
    )
    evidence["theorem_obligations"]["R2"] = all(
        item["verified"] for item in prerequisites.values()
    )
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
            "passed": all(item["verified"] for item in prerequisites.values()),
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
        key: value for key, value in decision.items() if key.startswith("PROHIBITED_")
    }
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "status": status,
        "authorized_claim": decision["AUTHORIZED_CLAIM"],
        "claim_boundary": spec["evidence_boundary"],
        "prohibited_claims": prohibited,
        "spec_sha256": sha256_file(spec_path),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
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
    print(f"{spec['campaign']}: {status}")
    for gate in gates:
        print(f"  {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    if status != "PASS":
        failed_checks = [name for name, passed in source_checks.items() if not passed]
        if failed_checks:
            print("  failed source checks: " + ", ".join(failed_checks))
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
        or not all(results["negative_controls"].values())
    ):
        raise RuntimeError("results are not finalizable PASS evidence")

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
        "production_reference_agreement": results["production_reference_agreement"],
        "theorem_obligations": results["theorem_obligations"],
        "negative_controls": results["negative_controls"],
        "proof_coverage": results["proof_coverage"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)

    lines = [
        "# WP6-COMMON-v1 Qualification Report",
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
        f"- Exact deterministic benchmarks: {len(results['benchmarks'])}",
        "- Production/reference agreement: PASS",
        "- Common-level branch partition: PASS",
        "- Kepler relation and Euler-Moulton spectrum: PASS",
        "- Generic and circular discriminant audits: PASS",
        "- Representative scalar NVE coefficient agreement: PASS",
        f"- Theorem obligations: {sum(results['theorem_obligations'].values())}/10",
        (
            "- Adversarial controls rejected: "
            f"{sum(results['negative_controls'].values())}/"
            f"{len(results['negative_controls'])}"
        ),
        "- Source hashes, text contracts, and predecessors: PASS",
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
