#!/usr/bin/env python
"""Execute the locked 11,700-system WP6-DZ-FEAS-v2 search."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any


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
from src.python.wp6_dz_feas_v2 import (  # noqa: E402
    MASS_ORDER_CASES,
    build_rectilinear_model,
)
from src.python.wp6_dz_feas_v2.search import (  # noqa: E402
    EXPECTED_SYSTEM_COUNT,
    decide_system,
    enumerate_systems,
)


CAMPAIGN = "WP6-DZ-FEAS-v2"
ROOT = VALIDATION_ROOT / "wp6-dz-feas-v2"
SPEC = ROOT / "qualification_spec.json"
PROTOCOL = ROOT / "constructive_protocol.json"
SEEDS = ROOT / "sources/seed_manifest.json"
SPEC_LOCK = ROOT / "reports/wp6_dz_feas_v2_specification_lock.json"
REFERENCE = ROOT / "reference/barycentric_reference.py"
OUTPUT = ROOT / "search/search_ledger.json"


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=REPO_ROOT, text=True
    ).strip()


def _load_module(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _verify_specification_lock() -> dict[str, Any]:
    lock = load_json(SPEC_LOCK)
    unsigned = dict(lock)
    signature = unsigned.pop("specification_lock_sha256", None)
    if signature != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("specification-lock signature is invalid")
    if (
        lock.get("campaign") != CAMPAIGN
        or lock.get("lock_type") != "pre_constructive_search_specification"
        or lock.get("spec_sha256") != sha256_file(SPEC)
        or lock.get("protocol_sha256") != sha256_file(PROTOCOL)
        or lock.get("seed_manifest_sha256") != sha256_file(SEEDS)
        or lock["locked_counts"]["coefficient_ideals"] != EXPECTED_SYSTEM_COUNT
        or lock.get("constructive_search_started_at_lock") is not False
        or lock.get("search_implementation_present_at_lock") is not False
        or lock.get("search_ledger_present_at_lock") is not False
        or lock.get("candidate_ledger_present_at_lock") is not False
        or lock.get("qualification_outputs_present_at_lock") is not False
        or lock.get("wp6_dz_mr_campaign_present_at_lock") is not False
    ):
        raise RuntimeError("specification lock does not match the campaign")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"prerequisite changed: {relative}")
    for relative, expected in lock["seed_artifact_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"seed artifact changed: {relative}")
    return lock


def _reference_checks() -> dict[str, bool]:
    import sympy as sp

    reference = _load_module(REFERENCE, "_wp6_dz_feas_v2_reference")
    checks: dict[str, bool] = {}
    symbolic_masses = sp.symbols("m1 m2 m3", positive=True)
    symbolic_production = build_rectilinear_model(symbolic_masses)
    symbolic_independent = reference.derive(symbolic_masses)
    symbolic_substitution = {
        symbolic_independent["x"]: symbolic_production.x,
        symbolic_independent["v"]: symbolic_production.v,
        symbolic_independent["u"]: symbolic_production.u,
        symbolic_independent["r"]: symbolic_production.r,
    }
    checks["symbolic_A"] = (
        sp.cancel(
            symbolic_production.A
            - symbolic_independent["A"].subs(symbolic_substitution)
        )
        == 0
    )
    checks["symbolic_B"] = (
        sp.cancel(
            symbolic_production.B
            - symbolic_independent["B"].subs(symbolic_substitution)
        )
        == 0
    )
    checks["symbolic_energy"] = (
        sp.cancel(
            symbolic_production.normalized_energy
            - symbolic_independent["normalized_energy"].subs(symbolic_substitution)
        )
        == 0
    )
    checks["symbolic_metric"] = sp.simplify(
        symbolic_production.mass_metric - symbolic_independent["mass_metric"]
    ) == sp.zeros(2)
    for case_id, masses in MASS_ORDER_CASES:
        production = build_rectilinear_model(masses)
        independent = reference.derive(masses)
        substitution = {
            independent["x"]: production.x,
            independent["v"]: production.v,
            independent["u"]: production.u,
            independent["r"]: production.r,
        }
        checks[f"{case_id}_A"] = (
            sp.cancel(production.A - independent["A"].subs(substitution)) == 0
        )
        checks[f"{case_id}_B"] = (
            sp.cancel(production.B - independent["B"].subs(substitution)) == 0
        )
        checks[f"{case_id}_energy"] = (
            sp.cancel(
                production.normalized_energy
                - independent["normalized_energy"].subs(substitution)
            )
            == 0
        )
        checks[f"{case_id}_metric"] = sp.simplify(
            production.mass_metric - independent["mass_metric"]
        ) == sp.zeros(2)
        checks[f"{case_id}_barycentric"] = (
            independent["center_of_mass"] == 0 and independent["linear_momentum"] == 0
        )
        derivative = (
            sp.diff(production.normalized_energy, production.x)
            * production.vector_field[1]
            + sp.diff(production.normalized_energy, production.v)
            * production.vector_field[2]
            + sp.diff(production.normalized_energy, production.u)
            * production.vector_field[3]
        )
        checks[f"{case_id}_energy_invariance"] = (
            sp.cancel(derivative - production.v * production.normalized_energy) == 0
        )
    checks["reference_source_disjoint"] = "src.python" not in REFERENCE.read_text(
        encoding="utf-8"
    ) and "wp6_dz_feas_v2" not in REFERENCE.read_text(encoding="utf-8")
    return checks


def _peak_memory_megabytes() -> float:
    observed = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return observed / (1024 * 1024)
    return observed / 1024


def main() -> None:
    if OUTPUT.exists():
        raise RuntimeError("refusing to overwrite immutable search ledger")
    if _git("status", "--short"):
        raise RuntimeError("constructive search requires a clean worktree")
    lock = _verify_specification_lock()
    protocol = load_json(PROTOCOL)
    spec = load_json(SPEC)
    reference_checks = _reference_checks()
    if not all(reference_checks.values()):
        failed = [name for name, passed in reference_checks.items() if not passed]
        raise RuntimeError(f"reference derivation failed: {failed}")

    timeout_seconds = spec["stop_rule"]["per_ideal_timeout_seconds"]
    aggregate_cap = spec["stop_rule"]["aggregate_compute_cap_seconds"]
    memory_cap = spec["stop_rule"]["memory_cap_megabytes"]
    started_utc = utc_now()
    started = time.monotonic()
    models = {
        case_id: build_rectilinear_model(masses) for case_id, masses in MASS_ORDER_CASES
    }
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
            timeout_seconds=min(timeout_seconds, aggregate_cap - elapsed),
        )
        records.append(decision.as_payload())
        if system.index % 900 == 0:
            non_unit = sum(record["status"] == "NON_UNIT_IDEAL" for record in records)
            undecided = sum(
                record["status"] in {"TIMEOUT", "ERROR"} for record in records
            )
            print(
                f"{system.index}/{EXPECTED_SYSTEM_COUNT}: "
                f"non-unit={non_unit}, undecided={undecided}, "
                f"elapsed={time.monotonic() - started:.2f}s",
                flush=True,
            )

    elapsed = time.monotonic() - started
    status_counts = {
        status: sum(record["status"] == status for record in records)
        for status in ("UNIT_IDEAL", "NON_UNIT_IDEAL", "TIMEOUT", "ERROR")
    }
    complete = (
        len(records) == EXPECTED_SYSTEM_COUNT
        and abort_reason is None
        and status_counts["TIMEOUT"] == 0
        and status_counts["ERROR"] == 0
    )
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "search_status": "COMPLETE" if complete else "INCOMPLETE",
        "started_utc": started_utc,
        "completed_utc": utc_now(),
        "base_git_commit": _git("rev-parse", "HEAD"),
        "specification_lock_sha256": lock["specification_lock_sha256"],
        "spec_sha256": sha256_file(SPEC),
        "protocol_sha256": sha256_file(PROTOCOL),
        "reference_sha256": sha256_file(REFERENCE),
        "sympy_version": __import__("sympy").__version__,
        "enumeration_order": protocol["enumeration"]["ordering"],
        "expected_system_count": EXPECTED_SYSTEM_COUNT,
        "executed_system_count": len(records),
        "status_counts": status_counts,
        "non_unit_system_ids": [
            record["system_id"]
            for record in records
            if record["status"] == "NON_UNIT_IDEAL"
        ],
        "abort_reason": abort_reason,
        "elapsed_seconds": elapsed,
        "peak_memory_megabytes": _peak_memory_megabytes(),
        "resource_caps": {
            "per_ideal_timeout_seconds": timeout_seconds,
            "aggregate_compute_cap_seconds": aggregate_cap,
            "memory_cap_megabytes": memory_cap,
        },
        "reference_checks": reference_checks,
        "records": records,
    }
    unsigned = dict(payload)
    payload["search_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
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
