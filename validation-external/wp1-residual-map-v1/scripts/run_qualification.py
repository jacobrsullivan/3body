#!/usr/bin/env python
"""Execute the frozen WP1-RESIDUAL-MAP-v1 qualification."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp1-residual-map-v1"
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
from src.python.wp1_residual_map_v1 import (  # noqa: E402
    HIGHER_VARIATIONAL_EXCEPTION,
    PUBLICATION_GATE,
    build_residual_map,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--map-output", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _map_contract(payload: dict[str, Any]) -> bool:
    rows = payload.get("candidates", [])
    return bool(
        payload.get("no_invariant_interpretation") is True
        and payload.get("publication_gate") == PUBLICATION_GATE
        and all(
            row.get("publication_gate") == PUBLICATION_GATE
            and str(row.get("prohibited_interpretation", "")).startswith(
                "This row does not discover"
            )
            and "qualification" in str(row.get("authorized_next_test", ""))
            for row in rows
        )
    )


def _input_hash(payload: dict[str, Any]) -> str:
    import hashlib

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _negative_controls(
    catalogue: dict[str, Any],
    expected_catalogue_hash: str,
    production: dict[str, Any],
) -> dict[str, bool]:
    missing = deepcopy(catalogue)
    missing["candidates"].pop()
    missing_detected = (
        _input_hash(missing) != expected_catalogue_hash
        and build_residual_map(missing)["candidate_count"] != 169
    )

    duplicate = deepcopy(catalogue)
    duplicate["candidates"].append(deepcopy(duplicate["candidates"][0]))
    duplicate_rejected = False
    try:
        build_residual_map(duplicate)
    except ValueError:
        duplicate_rejected = True

    changed_mass = deepcopy(catalogue)
    changed_mass["candidates"][0]["parameters"]["m1"] = "1"
    changed_mass_detected = _input_hash(changed_mass) != expected_catalogue_hash

    changed_label = deepcopy(catalogue)
    first_label = changed_label["candidates"][0]["stability"]["label"]
    changed_label["candidates"][0]["stability"]["label"] = (
        "U" if first_label == "S" else "S"
    )
    changed_label_detected = _input_hash(changed_label) != expected_catalogue_hash

    unknown = deepcopy(catalogue)
    unknown["candidates"][0]["stability"]["label"] = "?"
    unknown_rejected = False
    try:
        build_residual_map(unknown)
    except ValueError:
        unknown_rejected = True

    near_exception = deepcopy(catalogue)
    equal_index = next(
        index
        for index, candidate in enumerate(near_exception["candidates"])
        if candidate["parameters"]["m1"] == "0x1.0000000000000p+0"
        and candidate["parameters"]["m2"] == "0x1.0000000000000p+0"
    )
    near_exception["candidates"][equal_index]["parameters"][
        "m1"
    ] = "0x1.0000000000001p+0"
    near_map = build_residual_map(near_exception)
    near_row = next(
        row
        for row in near_map["candidates"]
        if row["candidate_id"]
        == near_exception["candidates"][equal_index]["candidate_id"]
    )
    exact_membership_enforced = HIGHER_VARIATIONAL_EXCEPTION not in near_row[
        "overlays"
    ]

    overinterpreted = deepcopy(production)
    overinterpreted["candidates"][0][
        "prohibited_interpretation"
    ] = "This row establishes a new invariant."
    overinterpretation_rejected = not _map_contract(overinterpreted)

    missing_gate = deepcopy(production)
    missing_gate["candidates"][0]["publication_gate"] = ""
    missing_gate_rejected = not _map_contract(missing_gate)

    shuffled = deepcopy(catalogue)
    random.Random(20260723).shuffle(shuffled["candidates"])
    permutation_invariant = build_residual_map(shuffled) == production
    return {
        "missing_candidate_detected": missing_detected,
        "duplicate_candidate_rejected": duplicate_rejected,
        "changed_mass_detected_by_frozen_input": changed_mass_detected,
        "changed_label_detected_by_frozen_input": changed_label_detected,
        "unknown_label_rejected": unknown_rejected,
        "exact_exception_membership_enforced": exact_membership_enforced,
        "overinterpretation_rejected": overinterpretation_rejected,
        "missing_publication_gate_rejected": missing_gate_rejected,
        "input_row_permutation_invariant": permutation_invariant,
    }


def _prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    wp1 = spec["prerequisites"]["wp1_catalogue"]
    wp1_lock = verify_lock(
        REPO_ROOT / wp1["lock_file"],
        REPO_ROOT,
        expected_prefix="WP1-CAT-N3BP-v1",
    )
    wp1_record = load_json(REPO_ROOT / wp1["record_file"])
    mr = spec["prerequisites"]["wp4_mr_v2_boundary"]
    mr_record = load_json(REPO_ROOT / mr["record_file"])
    return {
        "wp1_catalogue": {
            "qualification_id": wp1_record.get("qualification_id"),
            "status": wp1_record.get("status"),
            "lock_sha256": wp1_lock.get("lock_sha256"),
            "verified": (
                wp1_record.get("qualification_id") == wp1["qualification_id"]
                and wp1_record.get("status") == "PASS"
            ),
        },
        "wp4_mr_v2_boundary": {
            "qualification_id": mr_record.get("qualification_id"),
            "status": mr_record.get("status"),
            "verified": (
                mr_record.get("qualification_id") == mr["qualification_id"]
                and mr_record.get("status") == "PASS"
            ),
        },
    }


def main() -> None:
    args = _args()
    output = Path(args.output)
    map_output = Path(args.map_output)
    if output.exists() or map_output.exists():
        raise RuntimeError("refusing to overwrite immutable campaign output")
    spec = load_json(args.spec)
    catalogue = load_json(args.catalogue)
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    common = campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp1_residual_map_v1_common_run",
    )
    specification_lock = common.verify_specification_lock(args.spec)
    prerequisites = _prerequisites(spec)
    reference = campaign_module(
        CAMPAIGN_ROOT / "reference/sympy_reference.py",
        "_wp1_residual_map_v1_reference_run",
    )
    production = build_residual_map(catalogue)
    independent = reference.build_map(catalogue)
    reference_agreement = production == independent
    expected_hash = spec["prerequisites"]["wp1_catalogue"][
        "catalogue_file_sha256"
    ]
    input_hash_verified = sha256_file(args.catalogue) == expected_hash
    controls = _negative_controls(
        catalogue, _input_hash(catalogue), production
    )
    expected_counts = {
        "candidate_count": spec["expected_counts"]["candidate_count"],
        "local_stable_normal_form": spec["expected_counts"]["stable_track_count"],
        "asymptotic_manifold": spec["expected_counts"]["unstable_track_count"],
        "higher_variational_exception_overlay": spec["expected_counts"][
            "first_nve_exception_overlay_count"
        ],
    }
    counts_pass = (
        production["candidate_count"] == expected_counts["candidate_count"]
        and production["counts"]["local_stable_normal_form"]
        == expected_counts["local_stable_normal_form"]
        and production["counts"]["asymptotic_manifold"]
        == expected_counts["asymptotic_manifold"]
        and production["counts"]["higher_variational_exception_overlay"]
        == expected_counts["higher_variational_exception_overlay"]
    )
    one_to_one = len(
        {row["candidate_id"] for row in production["candidates"]}
    ) == len(production["candidates"]) == 169
    map_contract = _map_contract(production)
    publication_gates_present = all(
        row["publication_gate"] == PUBLICATION_GATE
        for row in production["candidates"]
    )
    no_interpretation_present = bool(
        production["no_invariant_interpretation"]
        and all(
            str(row["prohibited_interpretation"]).startswith(
                "This row does not discover"
            )
            for row in production["candidates"]
        )
    )
    claim_boundary_present = all(
        phrase in spec["evidence_boundary"]
        for phrase in (
            "deterministic evidence-quality ordering",
            "explicit publication gates",
            "does not discover an invariant",
            "qualify spatial stability",
            "widen the WP1 catalogue claim",
        )
    )
    reference_source = (
        CAMPAIGN_ROOT / "reference/sympy_reference.py"
    ).read_text(encoding="utf-8")
    source_disjoint = "src.python.wp1_residual_map_v1" not in reference_source
    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate(
            "all_prerequisite_hashes_verified",
            int(
                input_hash_verified
                and all(item["verified"] for item in prerequisites.values())
            ),
            "==",
            1,
        ),
        make_gate("all_169_candidates_mapped_once", int(one_to_one), "==", 1),
        make_gate(
            "expected_track_counts_exact", int(counts_pass), "==", 1
        ),
        make_gate(
            "exact_exception_overlay_count",
            production["counts"]["higher_variational_exception_overlay"],
            "==",
            spec["expected_counts"]["first_nve_exception_overlay_count"],
        ),
        make_gate(
            "deterministic_ordering_verified",
            int(controls["input_row_permutation_invariant"]),
            "==",
            1,
        ),
        make_gate(
            "production_reference_exact_agreement",
            int(reference_agreement and source_disjoint),
            "==",
            1,
        ),
        make_gate(
            "all_adversarial_controls_rejected",
            sum(controls.values()),
            "==",
            len(controls),
        ),
        make_gate(
            "publication_gate_present_on_every_row",
            int(publication_gates_present and map_contract),
            "==",
            1,
        ),
        make_gate(
            "no_invariant_interpretation_present",
            int(no_interpretation_present),
            "==",
            1,
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
    map_payload = dict(production)
    map_payload["qualification_id"] = lock["qualification_id"]
    map_payload["qualification_lock_sha256"] = lock["lock_sha256"]
    map_payload["catalogue_sha256"] = sha256_file(args.catalogue)
    map_payload["spec_sha256"] = sha256_file(args.spec)
    atomic_write_json(map_output, map_payload)
    result = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "generated_utc": utc_now(),
        "status": status,
        "authorized_claim": spec["decision_policy"]["AUTHORIZED_CLAIM"],
        "claim_boundary": spec["evidence_boundary"],
        "prohibited_claim": spec["decision_policy"]["PROHIBITED_CLAIM"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "catalogue_sha256": sha256_file(args.catalogue),
        "prerequisites": prerequisites,
        "map_path": map_output.relative_to(REPO_ROOT).as_posix(),
        "map_sha256": sha256_file(map_output),
        "counts": production["counts"],
        "candidate_count": production["candidate_count"],
        "production_reference_exact_agreement": reference_agreement,
        "reference_source_disjoint": source_disjoint,
        "publication_contract_complete": map_contract,
        "negative_controls": controls,
        "gates": gates,
        "runtime": runtime_fingerprint(),
    }
    atomic_write_json(output, result)
    print(f"{spec['campaign']} {lock['qualification_id']}: {status}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
