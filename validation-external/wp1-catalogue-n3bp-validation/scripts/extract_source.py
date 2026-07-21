#!/usr/bin/env python
"""Extract the locked 13 by 13 mass patch from the pinned SJTU payload."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
for path in (ROOT, VALIDATION, Path(__file__).resolve().parent):
    sys.path.insert(0, str(path))

from campaign_common import (  # noqa: E402
    locked_mass_grid,
    validate_source_manifest_metadata,
    verify_specification_lock,
)
from qualification_tools import load_json, sha256_bytes, sha256_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    verify_specification_lock(args.spec)
    spec = load_json(args.spec)
    manifest, selected_path = validate_source_manifest_metadata(
        spec, args.source_manifest
    )
    snapshot = manifest["external_snapshot"]
    upstream = Path(args.upstream).resolve()
    if sha256_file(upstream) != snapshot["upstream_sha256"]:
        raise RuntimeError("SJTU upstream payload hash mismatch")
    output = Path(args.output).resolve()
    if output != selected_path:
        raise RuntimeError("selected source output differs from the manifest path")
    if output.exists():
        raise RuntimeError("refusing to overwrite an existing selected source snapshot")

    selected: list[str] = []
    grid = locked_mass_grid(spec)
    allowed = {round(value, 12) for value in grid}
    upstream_row_count = 0
    with upstream.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            columns = line.split()
            if len(columns) != 8:
                continue
            try:
                m1, m2, m3 = (float(value) for value in columns[:3])
            except ValueError:
                continue
            upstream_row_count += 1
            if (
                round(m1, 12) in allowed
                and round(m2, 12) in allowed
                and m3 == 1.0
            ):
                try:
                    numeric = tuple(float(value) for value in columns[:7])
                except ValueError as error:
                    raise RuntimeError(f"malformed selected source row {line_number}") from error
                if (
                    not all(math.isfinite(value) for value in numeric)
                    or columns[7] not in {"S", "U"}
                    or numeric[6] <= 0.0
                ):
                    raise RuntimeError(f"invalid selected source row {line_number}")
                if (
                    min(abs(m1 - value) for value in grid) > 1.0e-12
                    or min(abs(m2 - value) for value in grid) > 1.0e-12
                ):
                    continue
                selected.append(f"{line_number} {' '.join(columns)}")
    if upstream_row_count != snapshot["upstream_row_count"]:
        raise RuntimeError(
            f"upstream row count is {upstream_row_count}, "
            f"expected {snapshot['upstream_row_count']}"
        )
    expected_count = int(spec["execution"]["expected_candidate_count"])
    if len(selected) != expected_count:
        raise RuntimeError(
            f"expected {expected_count} exact-grid rows, found {len(selected)}"
        )
    selected_keys = {
        (round(float(line.split()[1]), 12), round(float(line.split()[2]), 12))
        for line in selected
    }
    expected_keys = {
        (round(m1, 12), round(m2, 12)) for m1 in grid for m2 in grid
    }
    if selected_keys != expected_keys or len(selected_keys) != len(selected):
        raise RuntimeError("selected source rows are not a unique exact locked grid")

    header = [
        "# Source: non-hierarchical-3b-supplementary_data.txt",
        "# Repository: " + snapshot["repository"],
        "# Commit: " + snapshot["commit"],
        "# Upstream SHA-256: " + snapshot["upstream_sha256"],
        "# Columns: source_line m1 m2 m3 x1 v1 v2 period stability",
    ]
    payload = ("\n".join(header + selected) + "\n").encode("utf-8")
    if sha256_bytes(payload) != snapshot["selected_rows_sha256"]:
        raise RuntimeError("re-extracted selected source hash differs from manifest")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(f"wrote {len(selected)} rows to {output}")
    print(f"selected SHA-256: {sha256_file(output)}")


if __name__ == "__main__":
    main()
