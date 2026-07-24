"""Integrity helpers for WP4-LIFT-NI-v3."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-lift-ni-v3"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp4_lift_ni_v3_specification_lock.json"
)
MR_SOURCE_EQUIVALENCE_KEYS = {
    "finite_residue_spectra",
    "fuchs_gauge_and_singular_points",
    "infinity_exponent_polynomial",
    "morales_ramis_conclusion",
    "parabolic_lagrange_phase_curve",
    "planar_variational_and_whittaker_reduction",
    "reduced_hamiltonian_convention",
}
MR_THEOREM_OBLIGATION_KEYS = {f"R{index}" for index in range(1, 11)}

for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    verify_lock,
)


def verify_specification_lock(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    lock = load_json(SPECIFICATION_LOCK)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("WP4 lift v3 specification lock payload is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "successor_claim_specification"
        or lock.get("v3_implementation_present_at_lock") is not False
        or lock.get("v3_qualification_outputs_present_at_lock") is not False
        or lock.get("inherited_v2_implementation_present_at_lock") is not True
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("WP4 lift v3 specification lock mismatch")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    return lock


def verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name in ("wp2_multi", "wp4_mr_repl", "wp4_lift_v2"):
        contract = spec["prerequisites"][name]
        lock_path = REPO_ROOT / contract["lock_file"]
        record_path = REPO_ROOT / contract["record_file"]
        if sha256_file(lock_path) != contract["lock_file_sha256"]:
            raise RuntimeError(f"{name} prerequisite lock hash changed")
        if sha256_file(record_path) != contract["record_file_sha256"]:
            raise RuntimeError(f"{name} prerequisite record hash changed")
        lock = verify_lock(
            lock_path,
            REPO_ROOT,
            expected_prefix=contract["qualification_id"].rsplit("-", 1)[0],
        )
        record = load_json(record_path)
        if (
            record.get("status") != "PASS"
            or record.get("qualification_id") != contract["qualification_id"]
            or record.get("lock_sha256") != lock["lock_sha256"]
        ):
            raise RuntimeError(f"{name} prerequisite is not a matching PASS")
        records[name] = {"lock": lock, "record": record}
    return records


def mr_reproduced_premise(record: dict[str, Any]) -> bool:
    equivalence = record.get("published_source_equivalence", {})
    obligations = record.get("theorem_obligations", {})
    return bool(
        record.get("status") == "PASS"
        and record.get("generic_derivation", {}).get(
            "all_exact_derivation_checks_pass"
        )
        is True
        and record.get("complete_integrability_exceptional_set") == []
        and record.get("implementation_independence", {}).get(
            "production_does_not_import_sympy"
        )
        is True
        and record.get("implementation_independence", {}).get(
            "reference_does_not_import_production"
        )
        is True
        and set(equivalence) == MR_SOURCE_EQUIVALENCE_KEYS
        and all(value is True for value in equivalence.values())
        and set(obligations) == MR_THEOREM_OBLIGATION_KEYS
        and all(value is True for value in obligations.values())
        and "non-Abelian for every finite positive mass triple"
        in str(record.get("authorized_claim", ""))
    )


def verify_implementation_identity(spec: dict[str, Any]) -> dict[str, Any]:
    contract = spec["prerequisites"]["wp4_lift_v2"]
    paths = {
        "production": contract["production_file"],
        "reference": contract["reference_file"],
        "proof": contract["proof_file"],
    }
    expected = {
        "production": contract["production_file_sha256"],
        "reference": contract["reference_file_sha256"],
        "proof": contract["proof_file_sha256"],
    }
    observed = {name: sha256_file(REPO_ROOT / path) for name, path in paths.items()}
    return {
        "paths": paths,
        "expected_sha256": expected,
        "observed_sha256": observed,
        "all_match": observed == expected,
    }
