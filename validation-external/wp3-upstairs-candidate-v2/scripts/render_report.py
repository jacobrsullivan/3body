#!/usr/bin/env python
"""Render the bounded WP3-UP search report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import load_json  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec, results, gate = load_json(args.spec), load_json(args.results), load_json(args.gate)
    search = results["search"]
    smallest = min(search["post_projection_singular_values"])
    leading = search["modes"][0]
    lines = [
        "# WP3-UP-CAND-v2 Search Report", "", "## Decision", "",
        f"- Search status: **{results['status']}**",
        f"- `SEARCH_READY`: **{gate['SEARCH_READY']}**",
        f"- `CANDIDATE_READY`: **{gate['CANDIDATE_READY']}**",
        f"- `SEALED_QUALIFICATION`: **{gate['SEALED_QUALIFICATION']}**",
        f"- `WP4_READY`: **{gate['WP4_READY']}**",
        f"- Publication reserve: **{gate['publication_reserve_status']}**", "",
        "## Frozen Scope", "", spec["evidence_boundary"], "",
        "## Evidence", "",
        f"- Qualification/search ID: `{results['qualification_id']}`",
        f"- Features: {search['feature_count']} ({spec['library']['monomial_count']} state/energy/mass polynomial monomials plus known controls)",
        f"- Training points: {results['source_summary']['training_points']}",
        f"- Calibration points: {results['source_summary']['calibration_points']}",
        f"- Gauge samples per state: {results['source_summary']['gauge_count']}",
        f"- Active value rank: {search['value_rank']}",
        f"- Removed value-identity directions: {search['value_identity_nullity']}",
        f"- Known algebra active rank: {search['known_algebra_active_rank']}",
        f"- Smallest post-projection singular value: `{smallest:.16e}`",
        f"- Leading training weighted Lie RMS: `{leading['training_lie_rms']:.16e}`",
        f"- Leading calibration weighted Lie RMS: `{leading['calibration_lie_rms']:.16e}`",
        f"- Numerical candidate count: {search['candidate_count']}", "",
        "## Claim Boundary", "",
        "A null result is a finite-library exclusion, not a proof that the upstairs system has no additional first integral and not a non-integrability theorem. A candidate result would still require a new lock, sealed holdout, independent replication, and WP4 proof-level checks.", "",
    ]
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
