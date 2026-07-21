#!/usr/bin/env python
"""Build the frozen WP3 multi-chart development/calibration corpus."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
)
from validation_external_import import campaign_module  # type: ignore[import-not-found]  # noqa: E402


def _load_common():
    return campaign_module(
        REPO_ROOT
        / "validation-external/wp3-multi-candidate-v1/scripts/campaign_common.py",
        "_wp3_multi_campaign_common_build",
    )


def _selection_key(salt: str, candidate_id: str) -> str:
    return hashlib.sha256(f"{salt}|{candidate_id}".encode("ascii")).hexdigest()


def _select_wp1_cases(spec: dict[str, Any], catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = catalogue.get("candidates", [])
    if catalogue.get("campaign") != "WP1-CAT-N3BP-v1" or len(candidates) != 169:
        raise RuntimeError("unexpected WP1 native catalogue")
    salt = spec["data"]["wp1_selection_salt"]
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for label in ("S", "U"):
        ordered = sorted(
            (
                candidate
                for candidate in candidates
                if candidate.get("stability", {}).get("label") == label
            ),
            key=lambda candidate: _selection_key(salt, candidate["candidate_id"]),
        )
        offset = 0
        for split in spec["data"]["executable_splits"]:
            count = int(spec["data"]["wp1_selection"][split][label])
            chunk = ordered[offset : offset + count]
            if len(chunk) != count:
                raise RuntimeError(f"insufficient WP1 {label} candidates")
            offset += count
            for candidate in chunk:
                candidate_id = candidate["candidate_id"]
                if candidate_id in used:
                    raise RuntimeError("WP1 selection is not disjoint")
                used.add(candidate_id)
                selected.append(
                    {
                        "case_id": f"wp1-cat:{candidate_id}",
                        "split": split,
                        "source_kind": "qualified_wp1_periodic_catalogue",
                        "source_family": f"wp1_bABabaBAba_{label}",
                        "candidate_id": candidate_id,
                        "stability_label": label,
                        "checkpoint_fractions": spec["data"][
                            "wp1_checkpoint_fractions"
                        ],
                        "length_scale": 1.0,
                    }
                )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-corpus", required=True)
    parser.add_argument("--wp1-catalogue", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    common = _load_common()
    spec = load_json(args.spec)
    specification_lock = common.verify_specification_lock(args.spec)
    source = load_json(args.source_corpus)
    catalogue = load_json(args.wp1_catalogue)
    if sha256_file(args.source_corpus) != spec["prerequisites"][
        "source_exploration_corpus_sha256"
    ]:
        raise RuntimeError("source exploration corpus hash mismatch")
    if sha256_file(args.wp1_catalogue) != spec["prerequisites"]["wp1_catalogue"][
        "native_catalogue_sha256"
    ]:
        raise RuntimeError("WP1 catalogue hash mismatch")
    reserve = common.verify_publication_reserve(
        args.commitments,
        spec["prerequisites"]["sealed_publication_reserve_sha256"],
    )
    if len(source.get("cases", [])) != int(spec["data"]["source_case_count"]):
        raise RuntimeError("source exploration case count changed")

    allowed = set(spec["data"]["executable_splits"])
    cases: list[dict[str, Any]] = []
    for source_case in source["cases"]:
        if source_case["split"] not in allowed:
            continue
        copied = dict(source_case)
        if copied["source_kind"] == "qualified_external_trajectory":
            copied["checkpoint_indices"] = spec["data"][
                "external_checkpoint_indices"
            ]
        cases.append(copied)
    wp1_cases = _select_wp1_cases(spec, catalogue)
    cases.extend(wp1_cases)
    counts = {
        split: sum(case["split"] == split for case in cases) for split in allowed
    }
    if counts != {
        key: int(value) for key, value in spec["data"]["expected_group_counts"].items()
    }:
        raise RuntimeError(f"unexpected corpus group counts: {counts}")
    selected_ids = sorted(case["candidate_id"] for case in wp1_cases)
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "corpus_id": "wp3-multi-v1-shared-chart-degree3-corpus",
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "source_corpus_sha256": sha256_file(args.source_corpus),
        "wp1_catalogue_sha256": sha256_file(args.wp1_catalogue),
        "selected_wp1_candidate_ids_sha256": sha256_bytes(
            canonical_json(selected_ids)
        ),
        "sealed_publication_reserve": reserve,
        "charts": spec["library"]["charts"],
        "torus_angle_pairs": spec["library"]["torus_angle_pairs"],
        "cases": cases,
    }
    atomic_write_json(args.output, payload)
    print(
        f"built {len(cases)} groups: splits={counts}; "
        f"WP1 periodic={len(wp1_cases)}; reserve=SEALED_UNEXECUTED"
    )


if __name__ == "__main__":
    main()
