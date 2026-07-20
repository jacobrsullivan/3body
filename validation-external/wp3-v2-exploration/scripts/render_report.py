#!/usr/bin/env python
"""Render the bounded WP3 v2 result and staged gate decision."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import load_json  # noqa: E402


def _atomic_write_text(path: str, value: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = load_json(args.result)
    gate = load_json(args.gate)
    search = result["search"]
    lines = [
        "# WP3 v2 Exploration Report",
        "",
        f"**Campaign:** `{result['campaign']}`",
        "",
        f"**Decision:** `{result['status']}`",
        "",
        f"**SEARCH_READY:** `{gate['SEARCH_READY']['status']}`",
        "",
        f"**CANDIDATE_READY:** `{gate['CANDIDATE_READY']['status']}`",
        "",
        f"**PUBLICATION_READY:** `{gate['PUBLICATION_READY']['status']}`",
        "",
        "No result in this report authorizes interpretation as a first integral.",
        "",
        "## Evidence Boundary",
        "",
        f"- Training points: {result['source_summary']['training_points']}",
        f"- Calibration points: {result['source_summary']['calibration_points']}",
        f"- Feature count: {search['feature_count']}",
        f"- Active value rank: {search['value_rank']}",
        f"- Removed value-identity nullity: {search['value_identity_nullity']}",
        f"- Removed known-algebra rank: {search['known_algebra_active_rank']}",
        f"- Candidate count: {search['candidate_count']}",
        f"- Publication reserve: `{result['sealed_publication_reserve']['status']}`",
        "",
        "## Leading Modes",
        "",
        "| Rank | Train Lie RMS | Calibration Lie RMS | Ratio | Fold cosine min | Calibration drift max | Candidate |",
        "|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for mode in search["modes"]:
        cosine = min(mode["family_fold_coefficient_cosines"].values(), default=0.0)
        lines.append(
            f"| {mode['rank']} | {mode['training_lie_rms']:.3e} | "
            f"{mode['calibration_lie_rms']:.3e} | "
            f"{mode['calibration_to_training_ratio']:.2f} | {cosine:.3f} | "
            f"{mode['calibration_trajectory_drift_max']:.3e} | "
            f"{'yes' if mode['candidate_ready'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "At least one numerical direction passed the search thresholds. "
                "A separate candidate-specific qualification must be specified and "
                "locked before the reserve can be opened."
                if search["candidate_count"]
                else "No additional direction passed the frozen numerical gates. "
                "This is a bounded null result for the declared feature library; "
                "the publication reserve remains sealed and no invariant is interpreted."
            ),
            "",
        ]
    )
    _atomic_write_text(args.output, "\n".join(lines))


if __name__ == "__main__":
    main()
