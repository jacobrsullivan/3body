#!/usr/bin/env python
"""Execute the locked WP6-DZ-FEAS-v3 dual-exact campaign."""

from __future__ import annotations

import importlib.util
import json
import platform
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any

import sympy as sp


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for search_path in (REPO_ROOT, VALIDATION_ROOT):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    utc_now,
)
from src.python.wp6_dz_feas_v2.model import (  # noqa: E402
    MASS_ORDER_CASES,
    build_rectilinear_model,
)
from src.python.wp6_dz_feas_v3.search import (  # noqa: E402
    EXPECTED_SYSTEM_COUNT,
    decide_system,
    enumerate_systems,
    localize_equations,
)


CAMPAIGN = "WP6-DZ-FEAS-v3"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp6-dz-feas-v3"
SPEC = CAMPAIGN_ROOT / "qualification_spec.json"
PROTOCOL = CAMPAIGN_ROOT / "constructive_protocol.json"
SEEDS = CAMPAIGN_ROOT / "sources/seed_manifest.json"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp6_dz_feas_v3_specification_lock.json"
)
OUTPUT = CAMPAIGN_ROOT / "search/search_ledger.json"
V2_CANDIDATES = (
    VALIDATION_ROOT / "wp6-dz-feas-v2/candidates/candidate_ledger.json"
)
V2_REFERENCE = (
    VALIDATION_ROOT
    / "wp6-dz-feas-v2/reference/barycentric_reference.py"
)


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=REPO_ROOT, text=True
    ).strip()


def _valid_signature(
    payload: dict[str, Any],
    signature_field: str,
) -> bool:
    unsigned = dict(payload)
    signature = unsigned.pop(signature_field, None)
    return signature == sha256_bytes(canonical_json(unsigned))


def _verify_specification_lock() -> dict[str, Any]:
    lock = load_json(SPECIFICATION_LOCK)
    required_false = (
        "implementation_present_at_lock",
        "implementation_tests_present_at_lock",
        "constructive_search_started_at_lock",
        "search_ledger_present_at_lock",
        "candidate_ledger_present_at_lock",
        "qualification_outputs_present_at_lock",
        "wp6_dz_mr_campaign_present_at_lock",
    )
    if (
        not _valid_signature(lock, "specification_lock_sha256")
        or lock.get("campaign") != CAMPAIGN
        or lock.get("lock_type")
        != "pre_implementation_constructive_search_specification"
        or lock.get("spec_sha256") != sha256_file(SPEC)
        or lock.get("protocol_sha256") != sha256_file(PROTOCOL)
        or lock.get("seed_manifest_sha256") != sha256_file(SEEDS)
        or any(lock.get(field) is not False for field in required_false)
    ):
        raise RuntimeError("v3 specification lock is invalid")
    for relative, expected in lock["predecessor_artifact_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"frozen predecessor changed: {relative}")
    return lock


def _load_reference() -> Any:
    specification = importlib.util.spec_from_file_location(
        "_wp6_v3_barycentric_reference",
        V2_REFERENCE,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load source-disjoint reference")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _reference_checks() -> dict[str, bool]:
    protocol = load_json(PROTOCOL)
    inherited = protocol["scope_inheritance"]
    model_source = REPO_ROOT / inherited["model_source"]
    reference_source = REPO_ROOT / inherited["reference_source"]
    source_hashes = (
        sha256_file(model_source) == inherited["model_source_sha256"]
        and sha256_file(reference_source)
        == inherited["reference_source_sha256"]
    )

    masses = sp.symbols("m1 m2 m3", positive=True)
    production = build_rectilinear_model(masses)
    independent = _load_reference().derive(masses)
    substitution = {
        independent["x"]: production.x,
        independent["v"]: production.v,
        independent["u"]: production.u,
        independent["r"]: production.r,
    }
    independent_agreement = (
        sp.cancel(production.A - independent["A"].subs(substitution)) == 0
        and sp.cancel(production.B - independent["B"].subs(substitution)) == 0
        and sp.cancel(
            production.normalized_energy
            - independent["normalized_energy"].subs(substitution)
        )
        == 0
        and sp.simplify(
            production.mass_metric - independent["mass_metric"]
        )
        == sp.zeros(2)
        and independent["center_of_mass"] == 0
        and independent["linear_momentum"] == 0
    )
    energy_polynomial_identity = (
        sp.cancel(
            production.energy_numerator
            - 2
            * production.x
            * (1 - production.x)
            * production.normalized_energy
        )
        == 0
    )

    alpha, beta = sp.symbols("alpha beta")
    localized, exponents = localize_equations(
        (6 * alpha**3 * beta**2 * (alpha + 2 * beta),),
        (alpha, beta),
    )
    localization_identity = (
        localized == (alpha + 2 * beta,)
        and exponents == ((3, 2),)
    )

    systems = list(enumerate_systems())
    enumeration_identity = (
        len(systems) == EXPECTED_SYSTEM_COUNT == 11700
        and systems[0].system_id == "S00001"
        and systems[-1].system_id == "S11700"
        and tuple(
            (item["case_id"], tuple(item["masses"]))
            for item in protocol["enumeration"]["mass_order_cases"]
        )
        == MASS_ORDER_CASES
    )
    return {
        "frozen_source_hashes_match": source_hashes,
        "source_disjoint_barycentric_derivation_matches": (
            independent_agreement
        ),
        "polynomial_energy_numerator_identity": (
            energy_polynomial_identity
        ),
        "support_localization_identity": localization_identity,
        "v2_enumeration_identity": enumeration_identity,
    }


def _v2_unresolved_ids() -> set[str]:
    ledger = load_json(V2_CANDIDATES)
    if (
        not _valid_signature(ledger, "candidate_payload_sha256")
        or ledger.get("status") != "SEARCH_INCOMPLETE"
        or ledger.get("unresolved_system_count") != 151
    ):
        raise RuntimeError("v2 unresolved ledger is invalid")
    return set(ledger["timeout_system_ids"]) | set(
        ledger["unexecuted_system_ids"]
    )


def _peak_memory_megabytes() -> float:
    observed = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return observed / (1024 * 1024)
    return observed / 1024


def _runtime_checks(protocol: dict[str, Any]) -> dict[str, bool]:
    return {
        "python_3_11": platform.python_version().startswith("3.11."),
        "sympy_1_14_0": sp.__version__ == protocol["compute_policy"]["sympy"],
        "single_process": protocol["compute_policy"]["execution"]
        == "single process",
    }


def main() -> None:
    if OUTPUT.exists():
        raise RuntimeError("refusing to overwrite immutable v3 search ledger")
    if _git("status", "--short"):
        raise RuntimeError("constructive search requires a clean worktree")

    lock = _verify_specification_lock()
    protocol = load_json(PROTOCOL)
    spec = load_json(SPEC)
    runtime_checks = _runtime_checks(protocol)
    if not all(runtime_checks.values()):
        raise RuntimeError(f"runtime does not match lock: {runtime_checks}")
    reference_checks = _reference_checks()
    if not all(reference_checks.values()):
        raise RuntimeError(f"reference checks failed: {reference_checks}")
    v2_unresolved_ids = _v2_unresolved_ids()

    per_system_cap = spec["stop_rule"]["per_system_timeout_seconds"]
    aggregate_cap = spec["stop_rule"]["aggregate_compute_cap_seconds"]
    memory_cap = spec["stop_rule"]["memory_cap_megabytes"]
    candidate_cap = spec["stop_rule"]["candidate_family_cap"]
    models = {
        case_id: build_rectilinear_model(masses)
        for case_id, masses in MASS_ORDER_CASES
    }

    started_utc = utc_now()
    started = time.monotonic()
    records: list[dict[str, object]] = []
    abort_reason: str | None = None
    for system in enumerate_systems():
        elapsed = time.monotonic() - started
        if elapsed >= aggregate_cap:
            abort_reason = "aggregate_compute_cap_exceeded"
            break
        if _peak_memory_megabytes() >= memory_cap:
            abort_reason = "memory_cap_exceeded"
            break
        decision = decide_system(
            models[system.mass_case_id],
            system,
            timeout_seconds=min(per_system_cap, aggregate_cap - elapsed),
        )
        records.append(decision.as_payload())
        non_unit_count = sum(
            record["status"] == "NON_UNIT_IDEAL" for record in records
        )
        if non_unit_count > candidate_cap:
            abort_reason = "candidate_family_cap_exceeded"
            break
        if system.index % 900 == 0:
            unresolved_count = sum(
                record["status"]
                in {"TIMEOUT", "ERROR", "DISAGREEMENT"}
                for record in records
            )
            print(
                f"{system.index}/{EXPECTED_SYSTEM_COUNT}: "
                f"non-unit={non_unit_count}, "
                f"unresolved={unresolved_count}, "
                f"elapsed={time.monotonic() - started:.2f}s",
                flush=True,
            )

    elapsed = time.monotonic() - started
    statuses = (
        "UNIT_IDEAL",
        "NON_UNIT_IDEAL",
        "TIMEOUT",
        "ERROR",
        "DISAGREEMENT",
    )
    status_counts = {
        status: sum(record["status"] == status for record in records)
        for status in statuses
    }
    records_by_id = {
        str(record["system_id"]): record for record in records
    }
    unresolved_predecessor_records = {
        system_id: records_by_id[system_id]["status"]
        for system_id in sorted(v2_unresolved_ids)
        if system_id in records_by_id
    }
    complete = (
        len(records) == EXPECTED_SYSTEM_COUNT
        and abort_reason is None
        and status_counts["TIMEOUT"] == 0
        and status_counts["ERROR"] == 0
        and status_counts["DISAGREEMENT"] == 0
        and len(unresolved_predecessor_records) == len(v2_unresolved_ids)
    )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "search_status": "COMPLETE" if complete else "INCOMPLETE",
        "started_utc": started_utc,
        "completed_utc": utc_now(),
        "base_git_commit": _git("rev-parse", "HEAD"),
        "host": platform.node(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "sympy_version": sp.__version__,
        "specification_lock_sha256": lock[
            "specification_lock_sha256"
        ],
        "spec_sha256": sha256_file(SPEC),
        "protocol_sha256": sha256_file(PROTOCOL),
        "seed_manifest_sha256": sha256_file(SEEDS),
        "enumeration_order": protocol["enumeration"]["ordering"],
        "algorithms": spec["stop_rule"]["required_algorithms"],
        "expected_system_count": EXPECTED_SYSTEM_COUNT,
        "executed_system_count": len(records),
        "status_counts": status_counts,
        "non_unit_system_ids": [
            record["system_id"]
            for record in records
            if record["status"] == "NON_UNIT_IDEAL"
        ],
        "v2_unresolved_expected_count": len(v2_unresolved_ids),
        "v2_unresolved_decisions": unresolved_predecessor_records,
        "abort_reason": abort_reason,
        "elapsed_seconds": elapsed,
        "peak_memory_megabytes": _peak_memory_megabytes(),
        "resource_caps": {
            "per_system_timeout_seconds": per_system_cap,
            "aggregate_compute_cap_seconds": aggregate_cap,
            "memory_cap_megabytes": memory_cap,
            "candidate_family_cap": candidate_cap,
        },
        "runtime_checks": runtime_checks,
        "reference_checks": reference_checks,
        "records": records,
    }
    unsigned = dict(payload)
    payload["search_payload_sha256"] = sha256_bytes(
        canonical_json(unsigned)
    )
    atomic_write_json(OUTPUT, payload)
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "search_status",
                    "executed_system_count",
                    "status_counts",
                    "abort_reason",
                    "elapsed_seconds",
                    "peak_memory_megabytes",
                    "search_payload_sha256",
                )
            },
            indent=2,
        )
    )
    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
