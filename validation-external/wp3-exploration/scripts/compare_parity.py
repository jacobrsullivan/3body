#!/usr/bin/env python
"""Compare two WP3 exploration records under the frozen parity policy."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    sha256_file,
    utc_now,
)


MODE_METRICS = (
    "standardized_singular_value",
    "training_lie_rms",
    "training_lie_max_abs",
    "calibration_lie_rms",
    "calibration_lie_max_abs",
    "training_value_std",
    "calibration_value_std",
    "known_control_overlap_max",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--reference-label", required=True)
    parser.add_argument("--comparison-label", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _check(name: str, passed: bool, **details: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), **details}


def _sector_layout(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "sector_id": sector["sector_id"],
            "dimension_signature": sector["dimension_signature"],
            "global_feature_indices": sector["global_feature_indices"],
            "feature_names": sector["feature_names"],
        }
        for sector in payload["search"]["sectors"]
    ]


def _max_search_deltas(
    reference: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, float]:
    singular_delta = 0.0
    coefficient_delta = 0.0
    metric_delta = 0.0
    for reference_sector, comparison_sector in zip(
        reference["search"]["sectors"],
        comparison["search"]["sectors"],
        strict=True,
    ):
        singular_delta = max(
            singular_delta,
            float(
                np.max(
                    np.abs(
                        np.asarray(
                            reference_sector["standardized_singular_values"]
                        )
                        - np.asarray(
                            comparison_sector["standardized_singular_values"]
                        )
                    )
                )
            ),
        )
        for reference_mode, comparison_mode in zip(
            reference_sector["near_null_modes"],
            comparison_sector["near_null_modes"],
            strict=True,
        ):
            coefficient_delta = max(
                coefficient_delta,
                float(
                    np.max(
                        np.abs(
                            np.asarray(reference_mode["coefficients"])
                            - np.asarray(comparison_mode["coefficients"])
                        )
                    )
                ),
            )
            metric_delta = max(
                metric_delta,
                *(
                    abs(
                        float(reference_mode[name])
                        - float(comparison_mode[name])
                    )
                    for name in MODE_METRICS
                ),
            )
    return {
        "standardized_singular_value_max_abs_delta": singular_delta,
        "mode_coefficient_max_abs_delta": coefficient_delta,
        "mode_metric_max_abs_delta": metric_delta,
    }


def main() -> None:
    args = parse_args()
    spec = load_json(args.spec)
    reference = load_json(args.reference)
    comparison = load_json(args.comparison)
    thresholds = spec["thresholds"]
    deltas = _max_search_deltas(reference, comparison)
    gate_fields = ("campaign", "status", "interpretation_authorized")
    checks = [
        _check(
            "input_hashes",
            reference["input_hashes"] == comparison["input_hashes"],
        ),
        _check(
            "implementation_snapshot",
            reference["implementation_snapshot"]
            == comparison["implementation_snapshot"],
        ),
        _check(
            "provenance",
            reference["provenance"] == comparison["provenance"],
        ),
        _check(
            "matrix_hashes",
            reference["matrix_hashes"] == comparison["matrix_hashes"],
        ),
        _check(
            "publication_gate_boundary",
            all(
                reference["publication_gate"][field]
                == comparison["publication_gate"][field]
                for field in gate_fields
            ),
        ),
        _check(
            "dimension_sector_layout",
            _sector_layout(reference) == _sector_layout(comparison),
        ),
        _check(
            "numerical_nullity",
            reference["search"]["numerical_nullity_after_known_controls"]
            == comparison["search"]["numerical_nullity_after_known_controls"],
        ),
    ]
    exact_check_names = {check["name"] for check in checks}
    if exact_check_names != set(spec["required_exact_matches"]):
        raise RuntimeError(
            "parity implementation and specification exact checks differ"
        )
    for name, observed in deltas.items():
        threshold = float(thresholds[name])
        checks.append(
            _check(
                name,
                observed <= threshold,
                observed=observed,
                comparator="<=",
                threshold=threshold,
            )
        )

    status = "PASS" if all(check["passed"] for check in checks) else "FAIL"
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "status": status,
        "spec_sha256": sha256_file(args.spec),
        "implementation_sha256": sha256_file(Path(__file__)),
        "reference": {
            "label": args.reference_label,
            "path": str(args.reference),
            "sha256": sha256_file(args.reference),
            "runtime": reference["runtime"],
        },
        "comparison": {
            "label": args.comparison_label,
            "path": str(args.comparison),
            "sha256": sha256_file(args.comparison),
            "runtime": comparison["runtime"],
        },
        "checks": checks,
    }
    atomic_write_json(args.output, payload)
    passed_count = sum(check["passed"] for check in checks)
    print(
        f"{spec['campaign']}: {status} "
        f"({passed_count}/{len(checks)} checks)"
    )


if __name__ == "__main__":
    main()
