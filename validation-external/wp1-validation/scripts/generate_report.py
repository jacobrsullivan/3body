#!/usr/bin/env python
"""
Generate a public-facing WP1 external validation report.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate WP1 external validation report"
    )
    parser.add_argument("--output", required=True, help="Output Markdown file")
    parser.add_argument(
        "--workspace",
        default=os.path.dirname(os.path.dirname(__file__)),
        help="Validation workspace root",
    )
    return parser.parse_args()


def read_text(path: str) -> str:
    if not os.path.exists(path):
        return "(missing)"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _fmt_stat_table(section: dict, metrics: list[tuple[str, str]]) -> list[str]:
    """Format a section of the summary JSON into a Markdown table."""
    lines = []
    lines.append("| Metric | Count | Median | P95 | Max |")
    lines.append("|--------|------:|-------:|----:|----:|")
    for key, label in metrics:
        s = section.get(key, {})
        if s.get("count", 0) == 0:
            lines.append(f"| {label} | 0 | — | — | — |")
        else:
            lines.append(
                f"| {label} | {s['count']} "
                f"| {s['median']:.2e} "
                f"| {s['p95']:.2e} "
                f"| {s['max']:.2e} |"
            )
    return lines


def main() -> None:
    args = parse_args()
    ws = args.workspace

    tier1_report = os.path.join(
        str(REPO_ROOT), "data", "tier1", "analysis", "validation_report.txt"
    )
    tier2_report = os.path.join(
        str(REPO_ROOT), "data", "tier2", "analysis", "validation_report.txt"
    )

    jpl_summary = os.path.join(ws, "results", "jpl_comparison_summary.json")
    ext_precision = os.path.join(ws, "results", "extended_precision_summary.csv")

    megno_img = os.path.join(ws, "results", "chaos_map_megno.png")
    fli_img = os.path.join(ws, "results", "chaos_map_fli.png")
    overlay_img = os.path.join(ws, "results", "chaos_map_megno_overlay.png")

    report_lines = []
    report_lines.append("# WP1 External Validation Report")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    report_lines.append("")

    report_lines.append("## Tier 1 Validation")
    report_lines.append("```")
    report_lines.append(read_text(tier1_report))
    report_lines.append("```")
    report_lines.append("")

    report_lines.append("## Tier 2 Validation")
    report_lines.append("```")
    report_lines.append(read_text(tier2_report))
    report_lines.append("```")
    report_lines.append("")

    # --- JPL Cross-Check with structured output ---
    report_lines.append("## JPL Cross-Check Summary")
    if os.path.exists(jpl_summary):
        with open(jpl_summary, "r", encoding="utf-8") as f:
            summary = json.load(f)

        meta = summary.get("meta", {})
        report_lines.append(
            f"*{meta.get('n_sampled', '?')} orbits sampled from "
            f"{meta.get('n_jpl_total', '?')} total JPL orbits "
            f"(max_jpl={meta.get('max_jpl', '?')}), "
            f"matched against {meta.get('n_wp1_candidates', '?')} WP1 candidates.*"
        )
        report_lines.append("")

        # Integrator Accuracy
        report_lines.append("### Integrator Accuracy")
        report_lines.append("")
        report_lines.append(
            "Measures IAS15 performance on **JPL initial conditions** "
            "(converged periodic orbits). Isolates integrator quality."
        )
        report_lines.append("")
        int_section = summary.get("integrator_accuracy", {})
        report_lines.extend(
            _fmt_stat_table(
                int_section,
                [
                    ("closure_error", "Closure error (||x(T) - x(0)||)"),
                    ("jacobi_drift", "Jacobi drift (|C(T) - C(0)|)"),
                ],
            )
        )
        report_lines.append("")

        # Richardson Approximation Quality
        report_lines.append("### Richardson Approximation Quality")
        report_lines.append("")
        report_lines.append(
            "Measures geometric distance between WP1 Richardson 3rd-order ICs "
            "and JPL converged ICs. No integration — purely geometric comparison."
        )
        report_lines.append("")
        rich_section = summary.get("richardson_quality", {})
        report_lines.extend(
            _fmt_stat_table(
                rich_section,
                [
                    ("state_distance", "State distance (||x_WP1 - x_JPL||)"),
                    ("delta_C", "Jacobi constant delta (|C_WP1 - C_JPL|)"),
                    ("period_error", "Period error (|T_WP1 - T_JPL| / T_JPL)"),
                ],
            )
        )
    else:
        report_lines.append("(missing)")
    report_lines.append("")

    report_lines.append("## Extended Precision Summary")
    if os.path.exists(ext_precision):
        ext_rel = os.path.relpath(ext_precision, os.path.dirname(args.output))
        report_lines.append(f"See `{ext_rel}` for full details.")
    else:
        report_lines.append("(missing)")
    report_lines.append("")

    # --- Reversibility Test ---
    reversibility_summary = os.path.join(ws, "results", "reversibility_summary.json")
    report_lines.append("## Reversibility Test")
    report_lines.append("")
    report_lines.append(
        "Forward-backward integration should recover the initial state. "
        "This tests that the integrator preserves Hamiltonian time-reversal symmetry "
        "(Hairer, Lubich & Wanner 2006). Error is expected to grow with forward time."
    )
    report_lines.append("")
    if os.path.exists(reversibility_summary):
        with open(reversibility_summary, "r", encoding="utf-8") as f:
            rev_data = json.load(f)
        report_lines.append(
            "| Fwd Time | N | Med Pos RMS | P95 Pos RMS" " | Max Pos RMS | Tier1 Pass |"
        )
        report_lines.append(
            "|----------|--:|------------:|------------:" "|------------:|-----------:|"
        )
        for key in sorted(rev_data.keys()):
            s = rev_data[key]
            report_lines.append(
                f"| {key} | {s['n']} "
                f"| {s['median_pos_rms']:.2e} "
                f"| {s['p95_pos_rms']:.2e} "
                f"| {s['max_pos_rms']:.2e} "
                f"| {s['tier1_pass_rate']:.0%} |"
            )
    else:
        report_lines.append("(missing)")
    report_lines.append("")

    # --- Convergence Order Test ---
    convergence_summary = os.path.join(ws, "results", "convergence_summary.json")
    report_lines.append("## Convergence Order Test")
    report_lines.append("")
    report_lines.append(
        "Sweeps integrator tolerance from 1e-8 to 1e-14 and measures how error scales. "
        "For a well-behaved integrator, error should scale roughly as O(tol) "
        "(slope ~1 in log-log space)."
    )
    report_lines.append("")
    if os.path.exists(convergence_summary):
        with open(convergence_summary, "r", encoding="utf-8") as f:
            conv_data = json.load(f)
        report_lines.append(
            "| Tolerance | N | Med Closure | P95 Closure" " | Med Jacobi | P95 Jacobi |"
        )
        report_lines.append(
            "|-----------|--:|------------:|------------:" "|-----------:|-----------:|"
        )
        for key in sorted(k for k in conv_data if k.startswith("tol_")):
            s = conv_data[key]
            report_lines.append(
                f"| {key} | {s['n']} "
                f"| {s['median_closure']:.2e} "
                f"| {s['p95_closure']:.2e} "
                f"| {s['median_jacobi']:.2e} "
                f"| {s['p95_jacobi']:.2e} |"
            )
        order = conv_data.get("convergence_order")
        report_lines.append("")
        if order is not None:
            report_lines.append(f"**Estimated convergence order (slope):** {order:.2f}")
        else:
            report_lines.append("**Estimated convergence order:** not computed")
    else:
        report_lines.append("(missing)")
    report_lines.append("")

    report_lines.append("## Chaos Maps")
    output_dir = os.path.dirname(args.output)
    if os.path.exists(megno_img):
        report_lines.append(f"![MEGNO Map]({os.path.relpath(megno_img, output_dir)})")
    if os.path.exists(fli_img):
        report_lines.append(f"![FLI Map]({os.path.relpath(fli_img, output_dir)})")
    if os.path.exists(overlay_img):
        report_lines.append(
            f"![MEGNO Overlay]({os.path.relpath(overlay_img, output_dir)})"
        )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Wrote report: {args.output}")


if __name__ == "__main__":
    main()
