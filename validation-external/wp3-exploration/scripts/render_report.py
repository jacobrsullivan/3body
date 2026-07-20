#!/usr/bin/env python
"""Render a concise, boundary-aware WP3 exploration report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import load_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--gate-result", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _scientific(value: float) -> str:
    return f"{float(value):.3e}"


def main() -> None:
    args = parse_args()
    results = load_json(args.results)
    gate = load_json(args.gate_result)
    controls = results["search"]["known_control_metrics"]
    sectors = results["search"]["sectors"]
    leaders = [
        (sector, sector["near_null_modes"][0])
        for sector in sectors
        if sector["near_null_modes"]
    ]
    blocked = [row for row in gate["gates"] if not row["passed"]]
    generalization_ratios = [
        float(mode["calibration_lie_rms"]) / float(mode["training_lie_rms"])
        for _, mode in leaders
    ]

    lines = [
        "# WP3 Exploratory Screening Report",
        "",
        f"**Campaign:** `{results['campaign']}`",
        "",
        f"**Interpretation status:** `{results['interpretation_status']}`",
        "",
        f"**Publication gate:** `{gate['status']}` "
        f"({gate['passed_gate_count']}/{gate['required_gate_count']} gates)",
        "",
        "This report ranks numerical near-null directions only. It makes no "
        "conservation, independence, involution, or integrability claim.",
        "",
        "## Data Boundary",
        "",
        f"- Training points: {results['provenance']['training']['sample_count']}",
        f"- Calibration points: {results['provenance']['calibration']['sample_count']}",
        (
            "- Qualified trajectory sources use only upstream "
            "development/calibration cases."
        ),
        (
            "- Deterministic spatial collocation probes the exact vector field "
            "but is not external trajectory evidence."
        ),
        "- Every upstream holdout case remains excluded from WP3 execution.",
        "",
        "## Known Controls",
        "",
        (
            "| Control | Train Lie RMS | Calibration Lie RMS | Train max drift "
            "| Calibration max drift |"
        ),
        "|---|---:|---:|---:|---:|",
    ]
    drift = results["known_control_trajectory_drift"]
    for name, metrics in controls.items():
        lines.append(
            f"| `{name}` | {_scientific(metrics['training_lie_rms'])} | "
            f"{_scientific(metrics['calibration_lie_rms'])} | "
            f"{_scientific(drift[name]['training_max_scaled_peak_to_peak'])} | "
            f"{_scientific(drift[name]['calibration_max_scaled_peak_to_peak'])} |"
        )

    lines.extend(
        [
            "",
            "## Screening Modes",
            "",
            results["search"]["dimensional_policy"],
            "",
            (
                "Numerical nullity after projecting known controls across "
                f"{results['search']['dimension_sector_count']} sectors: "
                f"`{results['search']['numerical_nullity_after_known_controls']}` "
                f"at relative tolerance "
                f"`{results['search']['nullity_relative_tolerance']:.1e}`."
            ),
            "",
            "The table reports only the leading direction in each dimension sector.",
            "",
            (
                "| Sector | Features | Standardized singular value | Train Lie "
                "RMS | Calibration Lie RMS | Cal/train RMS | Train max drift | "
                "Calibration max drift |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for sector, mode in leaders:
        mode_drift = mode["trajectory_drift"]
        ratio = float(mode["calibration_lie_rms"]) / float(
            mode["training_lie_rms"]
        )
        lines.append(
            f"| `{sector['sector_id']}` | {sector['feature_count']} | "
            f"{_scientific(mode['standardized_singular_value'])} | "
            f"{_scientific(mode['training_lie_rms'])} | "
            f"{_scientific(mode['calibration_lie_rms'])} | "
            f"{ratio:.1f}x | "
            f"{_scientific(mode_drift['training_max_scaled_peak_to_peak'])} | "
            f"{_scientific(mode_drift['calibration_max_scaled_peak_to_peak'])} |"
        )

    lines.extend(
        [
            "",
            (
                "For the leading sector directions, the calibration/train Lie RMS "
                f"ratio ranges from {min(generalization_ratios):.1f}x to "
                f"{max(generalization_ratios):.1f}x. No additional numerical-null "
                "direction was detected at the declared tolerance."
            ),
        ]
    )

    lines.extend(["", "## Publication Blockers", ""])
    for row in blocked:
        lines.append(
            f"- `{row['id']}`: {row.get('reason', 'required evidence is not PASS')}"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The v1 screen does not advance an additional direction to candidate "
            "qualification. Exploration may continue, but candidate interpretation is "
            "prohibited by the fail-closed gate. Any later candidate-specific campaign "
            "must freeze its model, thresholds, and a genuinely sealed holdout before "
            "evaluation.",
            "",
        ]
    )
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
