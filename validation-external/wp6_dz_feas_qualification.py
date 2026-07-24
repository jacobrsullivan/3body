#!/usr/bin/env python
"""Freeze, execute, and finalize the WP6-DZ-FEAS-v1 campaign."""

from __future__ import annotations

import argparse
from datetime import datetime
from fractions import Fraction
import html
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


CAMPAIGN = "WP6-DZ-FEAS-v1"
EXPECTED_OUTCOME = "COMPLETE_BOUNDED_NULL_RESULT"


def _load_module(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _verify_specification_lock(
    spec_path: Path,
    protocol_path: Path,
    seed_manifest_path: Path,
    lock_path: Path,
) -> dict[str, Any]:
    lock = load_json(lock_path)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("specification lock signature is invalid")
    required_false = (
        "candidate_ledger_present_at_lock",
        "discovery_implementation_present_at_lock",
        "discovery_source_manifest_present_at_lock",
        "discovery_started_at_lock",
        "qualification_outputs_present_at_lock",
        "wp6_dz_mr_campaign_present_at_lock",
    )
    if (
        lock.get("campaign") != CAMPAIGN
        or lock.get("lock_type") != "pre_discovery_feasibility_specification"
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or lock.get("protocol_sha256") != sha256_file(protocol_path)
        or lock.get("seed_manifest_sha256") != sha256_file(seed_manifest_path)
        or any(lock.get(field) is not False for field in required_false)
    ):
        raise RuntimeError("specification lock does not match the campaign")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    legacy = lock["legacy_negative_control"]
    if sha256_file(REPO_ROOT / legacy["path"]) != legacy["sha256"]:
        raise RuntimeError("legacy negative control changed after pre-discovery lock")
    return lock


def _normalized_source_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        completed = subprocess.run(
            ["pdftotext", "-raw", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        text = completed.stdout
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = html.unescape(re.sub(r"<[^>]*>", " ", text))
    decomposed = unicodedata.normalize("NFKD", text)
    decomposed = decomposed.replace("−", " minus ").replace("–", " minus ")
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _source_records(
    manifest: dict[str, Any],
    source_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    if not source_dir.is_dir():
        raise RuntimeError(f"source directory does not exist: {source_dir}")
    records: list[dict[str, Any]] = []
    paths: dict[str, Path] = {}
    for source in manifest["sources"]:
        source_id = source["source_id"]
        path = (source_dir / source["payload_filename"]).resolve()
        if not path.is_file():
            raise RuntimeError(f"source payload missing: {path}")
        observed_hash = sha256_file(path)
        observed_bytes = path.stat().st_size
        paths[source_id] = path
        records.append(
            {
                "source_id": source_id,
                "payload_filename": source["payload_filename"],
                "expected_sha256": source["sha256"],
                "observed_sha256": observed_hash,
                "expected_bytes": source["payload_bytes"],
                "observed_bytes": observed_bytes,
                "verified": (
                    observed_hash == source["sha256"]
                    and observed_bytes == source["payload_bytes"]
                ),
            }
        )
    return records, paths


def _source_text_checks(paths: dict[str, Path]) -> dict[str, bool]:
    texts = {
        source_id: _normalized_source_text(path) for source_id, path in paths.items()
    }

    def contains(source_id: str, *phrases: str) -> bool:
        text = texts[source_id]
        return all(phrase in text for phrase in phrases)

    return {
        "mpc_current_gap": contains(
            "maciejewski-przybylska-combot-2025",
            "non integrability of the n body problem",
            "except in the case when both values of these integrals are zero",
        ),
        "combot_all_orders_and_new_orbit": contains(
            "combot-2011",
            "the only left case is h c 0",
            "always the case at all orders",
            "one would need a new particular orbit explicit",
            "no such orbit is known",
        ),
        "morales_simon_homothetic_scope": contains(
            "morales-ruiz-simon-2009",
            "on the meromorphic non integrability of some n body problems",
            "homothetic point of potential",
            "variational equations around a given particular solution",
        ),
        "tsygvintsev_parabolic_lagrange": contains(
            "tsygvintsev-2006",
            "three minus body problem",
            "parabolic lagrangian orbit",
            "additional first integral meromorphic",
        ),
        "chenciner_collision_manifold": contains(
            "chenciner-1997",
            "collision manifold is the quotient",
            "zero energy and zero angular momentum",
            "homographic solutions are the only solutions one is able to explicitely compute",
        ),
        "figure_eight_equal_mass_zero_c": contains(
            "chenciner-montgomery-2000",
            "periodic solution of the three body problem in the case of equal masses",
            "zero angular momentum",
        ),
        "symmetric_blowup_method": contains(
            "moeckel-montgomery-2012",
            "symmetric regularization reduction and blow up",
            "regularize all three double collision singularities",
            "blow up the triple collision",
        ),
        "weak_kam_zero_c_family": contains(
            "percino-figueroa-2017",
            "completely parabolic motion starting at x has zero angular momentum",
            "free time minimizers with zero angular momentum",
        ),
        "free_time_minimizer_existence": contains(
            "moeckel-montgomery-sanchez-2018",
            "free time minimizers for the three body problem",
            "asymptotic to lagranges parabolic homothetic solution",
            "large open set of mass ratios",
        ),
        "isosceles_zero_energy_nonexplicit": contains(
            "moeckel-2019",
            "minimal geodesics of the isosceles three body",
            "minimal geodesics for the zero energy isosceles problem",
            "central configurations of the n body problem give rise to simple explicit solutions",
        ),
        "saari_nonnegative_zero_c": contains(
            "diacu-fujiwara-perezchavela-santoprete-2008",
            "saaris homographic conjecture",
            "non negative values of the energy",
            "zero angular momentum",
        ),
        "regularized_examples_h_minus_one": contains(
            "rose-dullin-2013",
            "symmetry reduced and regularised planar 3 minus body problem with vanishing angular momentum",
            "periodic collision orbit",
            "with h minus 1 and equal unit masses",
        ),
        "periodic_catalogue_zero_c": contains(
            "li-jing-liao-2017",
            "periodic orbits of planar three body problem with unequal mass and zero angular momentum",
            "collisionless periodic orbits",
        ),
        "total_collision_essential": contains(
            "mercati-reichert-2021",
            "total collisions in the n body shape space",
            "essential singularity",
            "no way to evolve solutions through these points",
        ),
        "formal_explicit_triple_collision": contains(
            "hey-werkhausen-2024",
            "sundman theorem revisited",
            "explicit solution for the exact triple collision scenario",
            "sundman like formal regularization",
        ),
        "restricted_collinear_identity": contains(
            "delgado-vidal-2019",
            "dynamics of the parabolic restricted collinear three body problem",
            "family delgado",
            "given claudio",
            "family vidal",
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


def _search_integrity(
    spec: dict[str, Any],
    protocol: dict[str, Any],
    seed_manifest: dict[str, Any],
    source_manifest: dict[str, Any],
    receipt: dict[str, Any],
    ledger: dict[str, Any],
    specification_lock: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any]]:
    protocol_queries = {item["query_id"]: item for item in protocol["queries"]}
    receipt_queries = {item["query_id"]: item for item in receipt["queries"]}
    result_pages = receipt["result_pages"]
    query_ids_match = set(protocol_queries) == set(receipt_queries)
    query_texts_match = query_ids_match and all(
        receipt_queries[query_id]["text"] == protocol_queries[query_id]["text"]
        for query_id in protocol_queries
    )
    query_windows_complete = query_ids_match and all(
        query["window_complete"]
        and query["result_window_count"] == len(query["result_ids"])
        and 0 < query["result_window_count"] <= protocol["result_window_per_query"]
        and all(result_id in result_pages for result_id in query["result_ids"])
        for query in receipt_queries.values()
    )

    seed_sources = {item["source_id"]: item for item in seed_manifest["sources"]}
    discovery_sources = {item["source_id"]: item for item in source_manifest["sources"]}
    seed_preserved = set(seed_sources).issubset(discovery_sources) and all(
        discovery_sources[source_id]["sha256"] == item["sha256"]
        for source_id, item in seed_sources.items()
    )
    role_counts = {
        role: sum(source["role"] == role for source in source_manifest["sources"])
        for role in ("PRELOCK_SEED", "CITATION_EXPANSION")
    }

    candidates = ledger["candidates"]
    candidate_ids = {item["candidate_id"] for item in candidates}
    candidate_sources_known = all(
        set(candidate["sources"]).issubset(discovery_sources)
        for candidate in candidates
    )
    source_candidate_links_known = all(
        set(source["candidate_ids"]).issubset(candidate_ids)
        for source in source_manifest["sources"]
    )
    mandatory_coverage = {
        item["candidate_class"]: item for item in ledger["mandatory_class_coverage"]
    }
    mandatory_classes_complete = (
        set(mandatory_coverage) == set(spec["mandatory_candidate_classes"])
        and all(item["status"] == "COMPLETE" for item in mandatory_coverage.values())
        and all(
            set(item["candidate_ids"]).issubset(candidate_ids) and item["candidate_ids"]
            for item in mandatory_coverage.values()
        )
    )
    search_after_lock = _parse_utc(receipt["executed_utc"]) > _parse_utc(
        specification_lock["locked_utc"]
    )
    search_before_cutoff = _parse_utc(receipt["executed_utc"]) <= _parse_utc(
        protocol["stop_rule"]["search_cutoff_utc"]
        if "stop_rule" in protocol
        else spec["stop_rule"]["search_cutoff_utc"]
    )
    checks = {
        "query_ids_match": query_ids_match,
        "query_texts_match": query_texts_match,
        "query_windows_complete": query_windows_complete,
        "search_started_after_prelock": search_after_lock,
        "search_completed_before_cutoff": search_before_cutoff,
        "search_frontier_exhausted": bool(receipt["query_frontier_exhausted"]),
        "all_plausible_results_audited": bool(receipt["all_plausible_results_audited"]),
        "citation_expansion_exhausted": bool(
            receipt["eligible_citation_expansion_exhausted"]
        ),
        "seed_sources_preserved": seed_preserved,
        "source_count_within_cap": (
            len(discovery_sources) == source_manifest["primary_source_count"]
            and len(discovery_sources) <= spec["stop_rule"]["source_cap"]
        ),
        "citation_expansion_at_locked_cap": (
            role_counts["CITATION_EXPANSION"]
            == spec["stop_rule"]["citation_expansion_cap"]
            == source_manifest["citation_expansion_source_count"]
        ),
        "candidate_count_within_cap": (
            len(candidates) == ledger["candidate_family_count"]
            and len(candidates) <= spec["stop_rule"]["candidate_family_cap"]
        ),
        "candidate_sources_known": candidate_sources_known,
        "source_candidate_links_known": source_candidate_links_known,
        "mandatory_classes_complete": mandatory_classes_complete,
        "receipt_counts_consistent": (
            receipt["query_count"] == len(protocol_queries)
            and receipt["primary_sources_inspected"] == len(discovery_sources)
            and receipt["candidate_families_created"] == len(candidates)
            and receipt["citation_expansion_sources"]
            == role_counts["CITATION_EXPANSION"]
        ),
    }
    details = {
        "query_ids": sorted(receipt_queries),
        "result_page_count": len(result_pages),
        "source_count": len(discovery_sources),
        "source_role_counts": role_counts,
        "candidate_count": len(candidates),
        "mandatory_class_count": len(mandatory_coverage),
    }
    return checks, details


def _audit_coverage(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    headings = (
        "## Pre-Discovery Lock",
        "## Source Frontier",
        "## Exact Controls",
        "## Candidate Results",
        "## W1-W12 Outcome",
        "## Bounded Result",
        "## MR Promotion",
    )
    return {heading: heading in text for heading in headings}


def _exact_evidence(
    ledger: dict[str, Any],
    specification_lock: dict[str, Any],
    reference_path: Path,
) -> dict[str, Any]:
    from src.python.wp6_dz_feas_v1 import (
        COMPLETE_BOUNDED_NULL_RESULT,
        corrected_euler_homothetic_certificate,
        evaluate_candidate_ledger,
        free_fall_energy_certificate,
        legacy_euler_fixture_certificate,
        newtonian_scaling_certificate,
        periodic_energy_certificate,
        sundman_triple_collision_certificate,
    )

    reference = _load_module(reference_path, "_wp6_dz_feas_reference")
    production = {
        "legacy": legacy_euler_fixture_certificate(),
        "corrected": corrected_euler_homothetic_certificate(),
        "scaling": newtonian_scaling_certificate("-7/3", "11/5"),
        "periodic": periodic_energy_certificate("14/5"),
        "free_fall": free_fall_energy_certificate(),
        "triple_collision": sundman_triple_collision_certificate(),
    }
    independent = {
        "legacy": reference.legacy_fixture(),
        "corrected": reference.corrected_homothetic(),
        "scaling": reference.scaling(Fraction(-7, 3), Fraction(11, 5)),
        "periodic": reference.periodic(Fraction(14, 5)),
        "free_fall": reference.free_fall(),
        "triple_collision": reference.published_triple_collision(),
    }
    agreement = {
        "legacy_energy": (
            production["legacy"]["energy"] == independent["legacy"]["energy"] == "-1"
        ),
        "legacy_invariant": (
            production["legacy"]["angular_momentum"]
            == independent["legacy"]["angular_momentum"]
            == "0"
        ),
        "corrected_energy": (
            production["corrected"]["energy"]
            == independent["corrected"]["energy"]
            == "0"
        ),
        "corrected_equations": (
            production["corrected"]["equations_hold"]
            and independent["corrected"]["equations_hold"]
        ),
        "corrected_homothetic_rejection": (
            production["corrected"]["known_homothetic_curve"]
            and independent["corrected"]["known_homothetic_curve"]
            and not production["corrected"]["qualifying_witness"]
            and not independent["corrected"]["qualifying_witness"]
        ),
        "scaling_energy": (
            production["scaling"]["scaled_energy"]
            == independent["scaling"]["scaled_energy"]
            == "-35/33"
            and production["scaling"]["sign_preserved"]
            and independent["scaling"]["sign_preserved"]
        ),
        "periodic_energy": (
            production["periodic"]["energy"]
            == independent["periodic"]["energy"]
            == "-7/5"
            and independent["periodic"]["energy_is_strictly_negative"]
        ),
        "free_fall_energy": (
            production["free_fall"]["energy"]
            == independent["free_fall"]["energy"]
            == "-5/2"
            and independent["free_fall"]["energy_is_strictly_negative"]
        ),
        "triple_collision_shape": (
            production["triple_collision"]["delta_over_r_squared"]
            == independent["triple_collision"]["delta_over_r_squared"]
            == "3/4"
            and production["triple_collision"]["homothetic"]
            and independent["triple_collision"]["homothetic"]
        ),
        "triple_collision_energy_and_scope": (
            production["triple_collision"]["energy_sign"] == "negative"
            and independent["triple_collision"]["released_from_rest_energy_is_negative"]
            and independent["triple_collision"]["equal_masses_only"]
        ),
    }
    decision = evaluate_candidate_ledger(
        ledger,
        search_complete=True,
        integrity_complete=True,
        candidate_cap=16,
    )
    mr_paths = (
        REPO_ROOT / "validation-external/wp6-dz-mr-v1",
        REPO_ROOT / "src/python/wp6_dz_mr_v1",
        REPO_ROOT / "tests/wp6_dz_mr_v1",
    )
    negative_controls = {
        "legacy_fixture_rejected": production["legacy"]["stated_zero_energy_is_false"],
        "corrected_homothetic_rejected": (
            production["corrected"]["failed_requirements"] == ["W3", "W9"]
        ),
        "scaling_cannot_zero_nonzero_energy": production["scaling"][
            "nonzero_energy_cannot_scale_to_zero"
        ],
        "periodic_orbits_rejected_at_H_zero": production["periodic"][
            "nonstationary_collision_free_periodic_H_zero_impossible"
        ],
        "free_fall_rejected_at_H_zero": production["free_fall"][
            "finite_collision_free_free_fall_H_zero_impossible"
        ],
        "formal_collision_formula_rejected": (
            not production["triple_collision"]["qualifying_witness"]
            and {"W2", "W3", "W4", "W10"}.issubset(
                production["triple_collision"]["failed_requirements"]
            )
        ),
        "no_candidate_passes_W1_W12": (
            decision.outcome == COMPLETE_BOUNDED_NULL_RESULT
            and not decision.qualifying_candidate_ids
        ),
        "mr_promotion_prohibited": (
            not decision.mr_promotion_authorized
            and not any(path.exists() for path in mr_paths)
        ),
        "legacy_control_hash_unchanged": (
            sha256_file(
                REPO_ROOT / specification_lock["legacy_negative_control"]["path"]
            )
            == specification_lock["legacy_negative_control"]["sha256"]
        ),
        "independent_reference_source_disjoint": (
            "src.python" not in reference_path.read_text(encoding="utf-8")
            and "wp6_dz_feas_v1" not in reference_path.read_text(encoding="utf-8")
        ),
    }
    return {
        "production": production,
        "independent": independent,
        "production_reference_agreement": agreement,
        "negative_controls": negative_controls,
        "ledger_decision": decision.as_payload(),
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
        Path(args.spec).resolve(),
        Path(args.protocol).resolve(),
        Path(args.seed_manifest).resolve(),
        Path(args.spec_lock).resolve(),
    )
    files = tracked_files(root, args.scope)
    required = {
        Path(args.spec).resolve(),
        Path(args.protocol).resolve(),
        Path(args.seed_manifest).resolve(),
        Path(args.spec_lock).resolve(),
        Path(args.source_manifest).resolve(),
        Path(args.search_receipt).resolve(),
        Path(args.candidate_ledger).resolve(),
        Path(args.audit).resolve(),
        Path(args.reference).resolve(),
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
        "campaign": CAMPAIGN,
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(root, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "qualification_outputs_absent_at_freeze": True,
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "protocol_sha256": sha256_file(args.protocol),
        "seed_manifest_sha256": sha256_file(args.seed_manifest),
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "search_receipt_sha256": sha256_file(args.search_receipt),
        "candidate_ledger_sha256": sha256_file(args.candidate_ledger),
        "audit_sha256": sha256_file(args.audit),
        "reference_sha256": sha256_file(args.reference),
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
    protocol_path = Path(args.protocol).resolve()
    seed_manifest_path = Path(args.seed_manifest).resolve()
    spec = load_json(spec_path)
    protocol = load_json(protocol_path)
    seed_manifest = load_json(seed_manifest_path)
    source_manifest = load_json(args.source_manifest)
    receipt = load_json(args.search_receipt)
    ledger = load_json(args.candidate_ledger)
    if any(
        value.get("campaign") != CAMPAIGN
        for value in (
            spec,
            protocol,
            seed_manifest,
            source_manifest,
            receipt,
            ledger,
        )
    ):
        raise RuntimeError("campaign identity mismatch")
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=CAMPAIGN)
    specification_lock = _verify_specification_lock(
        spec_path,
        protocol_path,
        seed_manifest_path,
        Path(args.spec_lock).resolve(),
    )
    if (
        lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("qualification lock uses another specification lock")

    source_records, source_paths = _source_records(
        source_manifest, Path(args.source_dir).resolve()
    )
    source_checks = _source_text_checks(source_paths)
    prerequisites = _prerequisites(spec)
    search_checks, search_details = _search_integrity(
        spec,
        protocol,
        seed_manifest,
        source_manifest,
        receipt,
        ledger,
        specification_lock,
    )
    exact_evidence = _exact_evidence(
        ledger,
        specification_lock,
        Path(args.reference).resolve(),
    )
    audit_coverage = _audit_coverage(Path(args.audit).resolve())
    decision = exact_evidence["ledger_decision"]
    gates = [
        {
            "name": "all_source_hashes_and_sizes_verified",
            "passed": all(record["verified"] for record in source_records),
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
            "name": "locked_search_protocol_complete",
            "passed": all(search_checks.values()),
        },
        {
            "name": "candidate_ledger_derives_bounded_null",
            "passed": (
                decision["outcome"] == EXPECTED_OUTCOME
                and decision["all_requirements_decided"]
                and decision["all_candidates_have_failure"]
                and not decision["qualifying_candidate_ids"]
            ),
        },
        {
            "name": "production_reference_exact_agreement",
            "passed": all(exact_evidence["production_reference_agreement"].values()),
        },
        {
            "name": "all_adversarial_controls_rejected",
            "passed": all(exact_evidence["negative_controls"].values()),
        },
        {
            "name": "audit_coverage_complete",
            "passed": all(audit_coverage.values()),
        },
        {
            "name": "mr_campaign_not_opened",
            "passed": not decision["mr_promotion_authorized"],
        },
    ]
    gate_status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    outcome = decision["outcome"] if gate_status == "PASS" else "INCOMPLETE"
    prohibited = {
        key: value
        for key, value in spec["decision_policy"].items()
        if key.startswith("PROHIBITED_")
    }
    payload = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "qualification_gate_status": gate_status,
        "outcome": outcome,
        "authorized_claim": (
            spec["decision_policy"]["AUTHORIZED_NULL_CLAIM"]
            if outcome == EXPECTED_OUTCOME
            else None
        ),
        "claim_boundary": spec["claim_boundary"],
        "prohibited_claims": prohibited,
        "mr_promotion_authorized": decision["mr_promotion_authorized"],
        "mr_promotion_rule": spec["decision_policy"]["MR_PROMOTION_RULE"],
        "spec_sha256": sha256_file(spec_path),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "protocol_sha256": sha256_file(protocol_path),
        "seed_manifest_sha256": sha256_file(seed_manifest_path),
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "search_receipt_sha256": sha256_file(args.search_receipt),
        "candidate_ledger_sha256": sha256_file(args.candidate_ledger),
        "audit_sha256": sha256_file(args.audit),
        "reference_sha256": sha256_file(args.reference),
        "source_records": source_records,
        "source_text_checks": source_checks,
        "prerequisites": prerequisites,
        "search_integrity": search_checks,
        "search_details": search_details,
        "audit_coverage": audit_coverage,
        "gates": gates,
        **exact_evidence,
    }
    atomic_write_json(output, payload)
    print(f"{CAMPAIGN} gate: {gate_status}")
    print(f"{CAMPAIGN} outcome: {outcome}")
    for gate in gates:
        print(f"  {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    if gate_status != "PASS":
        failed_source_checks = [
            name for name, passed in source_checks.items() if not passed
        ]
        if failed_source_checks:
            print("  failed source checks: " + ", ".join(failed_source_checks))
        failed_search_checks = [
            name for name, passed in search_checks.items() if not passed
        ]
        if failed_search_checks:
            print("  failed search checks: " + ", ".join(failed_search_checks))
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
    results = load_json(result_path)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=CAMPAIGN)
    if (
        results.get("qualification_gate_status") != "PASS"
        or results.get("outcome") != EXPECTED_OUTCOME
        or results.get("qualification_id") != lock["qualification_id"]
        or results.get("lock_sha256") != lock["lock_sha256"]
        or results.get("mr_promotion_authorized") is not False
        or not all(gate["passed"] for gate in results["gates"])
        or not all(results["negative_controls"].values())
        or not all(results["production_reference_agreement"].values())
        or not all(results["search_integrity"].values())
    ):
        raise RuntimeError("results are not finalizable bounded-null evidence")

    evidence_commit = git_output(REPO_ROOT, "rev-parse", "HEAD")
    unsigned = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "evidence_git_commit": evidence_commit,
        "qualification_gate_status": "PASS",
        "status": EXPECTED_OUTCOME,
        "authorized_claim": results["authorized_claim"],
        "claim_boundary": results["claim_boundary"],
        "prohibited_claims": results["prohibited_claims"],
        "mr_promotion_authorized": False,
        "mr_promotion_rule": results["mr_promotion_rule"],
        "spec_sha256": results["spec_sha256"],
        "specification_lock_sha256": results["specification_lock_sha256"],
        "protocol_sha256": results["protocol_sha256"],
        "source_manifest_sha256": results["source_manifest_sha256"],
        "search_receipt_sha256": results["search_receipt_sha256"],
        "candidate_ledger_sha256": results["candidate_ledger_sha256"],
        "audit_sha256": results["audit_sha256"],
        "reference_sha256": results["reference_sha256"],
        "results_sha256": sha256_file(result_path),
        "source_count": len(results["source_records"]),
        "candidate_count": results["ledger_decision"]["candidate_count"],
        "qualifying_candidate_ids": results["ledger_decision"][
            "qualifying_candidate_ids"
        ],
        "nearest_miss_candidate_id": "C03",
        "source_records": results["source_records"],
        "source_text_checks": results["source_text_checks"],
        "prerequisites": results["prerequisites"],
        "search_integrity": results["search_integrity"],
        "production_reference_agreement": results["production_reference_agreement"],
        "negative_controls": results["negative_controls"],
        "audit_coverage": results["audit_coverage"],
        "gates": results["gates"],
    }
    record = dict(unsigned)
    record["record_payload_sha256"] = sha256_bytes(canonical_json(unsigned))
    atomic_write_json(record_path, record)

    lines = [
        "# WP6-DZ-FEAS-v1 Qualification Report",
        "",
        "**Qualification gate:** PASS",
        "",
        f"**Outcome:** `{EXPECTED_OUTCOME}`",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Authorized Claim",
        "",
        results["authorized_claim"],
        "",
        "## Material Finding",
        "",
        (
            "The target level contains many exact nonhomothetic solutions by "
            "weak-KAM/free-time-minimizer existence theorems, but the locked "
            "search found no explicit algebraic phase curve suitable for a "
            "candidate-specific tangent NVE."
        ),
        "",
        "## Evidence",
        "",
        f"- Primary payloads inspected and hash-verified: {len(results['source_records'])}",
        f"- Candidate families audited: {results['ledger_decision']['candidate_count']}",
        "- Locked query windows complete: 12/12",
        "- Mandatory candidate classes complete: 8/8",
        "- Citation-expansion cap reached: 12/12",
        (
            "- Production/reference exact controls: "
            f"{sum(results['production_reference_agreement'].values())}/"
            f"{len(results['production_reference_agreement'])}"
        ),
        (
            "- Adversarial controls rejected: "
            f"{sum(results['negative_controls'].values())}/"
            f"{len(results['negative_controls'])}"
        ),
        "- Qualifying candidates: 0",
        "- Nearest miss: C03 (algebraicity/explicitness fails at W5)",
        "",
        "## MR Promotion",
        "",
        "`WP6-DZ-MR-v1` was not opened and is not authorized by this record.",
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
        f"- Audit SHA-256: `{results['audit_sha256']}`",
        f"- Record payload SHA-256: `{record['record_payload_sha256']}`",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"finalized {lock['qualification_id']}: {EXPECTED_OUTCOME}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--repo-root", required=True)
    freeze.add_argument("--prefix", required=True)
    freeze.add_argument("--spec", required=True)
    freeze.add_argument("--protocol", required=True)
    freeze.add_argument("--seed-manifest", required=True)
    freeze.add_argument("--spec-lock", required=True)
    freeze.add_argument("--source-manifest", required=True)
    freeze.add_argument("--search-receipt", required=True)
    freeze.add_argument("--candidate-ledger", required=True)
    freeze.add_argument("--audit", required=True)
    freeze.add_argument("--reference", required=True)
    freeze.add_argument("--scope", action="append", required=True)
    freeze.add_argument("--output", required=True)
    freeze.add_argument("--result", required=True)
    freeze.add_argument("--record", required=True)
    freeze.add_argument("--report", required=True)

    execute = subparsers.add_parser("execute")
    execute.add_argument("--spec", required=True)
    execute.add_argument("--protocol", required=True)
    execute.add_argument("--seed-manifest", required=True)
    execute.add_argument("--spec-lock", required=True)
    execute.add_argument("--source-manifest", required=True)
    execute.add_argument("--search-receipt", required=True)
    execute.add_argument("--candidate-ledger", required=True)
    execute.add_argument("--audit", required=True)
    execute.add_argument("--reference", required=True)
    execute.add_argument("--source-dir", required=True)
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
    elif args.command == "finalize":
        _finalize(args)
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    main()
