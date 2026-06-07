#!/usr/bin/env python
"""
Normalize JPL periodic orbit data into WP1 CR3BP units.

Expected inputs:
- JSON with either {"fields": [...], "data": [...]} or {"orbits": [ {...} ]}

Normalization:
- Positions: x_norm = x / LU
- Velocities: v_norm = v * TU / LU
- Period: T_norm = T / TU
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize JPL periodic orbits")
    parser.add_argument("--input", required=True, help="Path to raw JPL JSON")
    parser.add_argument("--output", required=True, help="Output Parquet path")
    parser.add_argument(
        "--lu", type=float, default=None, help="Length unit (LU) in input units"
    )
    parser.add_argument(
        "--tu", type=float, default=None, help="Time unit (TU) in input units"
    )
    return parser.parse_args()


def _load_table(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "fields" in data and "data" in data:
        fields = data["fields"]
        rows = data["data"]
        table = []
        for row in rows:
            record = {fields[i]: row[i] for i in range(len(fields))}
            table.append(record)
        return table
    if "orbits" in data and isinstance(data["orbits"], list):
        return data["orbits"]
    raise ValueError(
        "Unrecognized JPL JSON structure: expected fields/data or orbits list"
    )


def _find_key(record_keys: List[str], candidates: List[str]) -> str | None:
    keys_lower = {k.lower(): k for k in record_keys}
    for c in candidates:
        if c.lower() in keys_lower:
            return keys_lower[c.lower()]
    return None


def main() -> None:
    args = parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    lu = args.lu
    tu = args.tu

    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    lu = lu if lu is not None else meta.get("lu")
    tu = tu if tu is not None else meta.get("tu")

    if lu is None or tu is None:
        raise ValueError("LU/TU not found in input or args; provide --lu and --tu")

    table = _load_table(data)

    # Detect canonical fields
    keys = list(table[0].keys()) if table else []
    kx = _find_key(keys, ["x", "x0", "x_0"])
    ky = _find_key(keys, ["y", "y0", "y_0"])
    kz = _find_key(keys, ["z", "z0", "z_0"])
    kvx = _find_key(keys, ["vx", "vx0", "vx_0"])
    kvy = _find_key(keys, ["vy", "vy0", "vy_0"])
    kvz = _find_key(keys, ["vz", "vz0", "vz_0"])
    kT = _find_key(keys, ["period", "T", "t", "orbital_period"])
    kC = _find_key(keys, ["C", "jacobi", "jacobi_constant", "cj"])
    kfamily = _find_key(keys, ["family", "type"])
    klpoint = _find_key(keys, ["lpoint", "L", "lagrange", "lagrange_point"])
    kbranch = _find_key(keys, ["branch", "orbit_branch"])
    kstability = _find_key(keys, ["stability", "stable", "stability_index"])

    if not all([kx, ky, kvx, kvy]):
        raise ValueError(f"Missing required state fields in JPL data. Keys: {keys}")

    records = []
    for row in table:
        x = float(row.get(kx))
        y = float(row.get(ky))
        z = float(row.get(kz, 0.0)) if kz else 0.0
        vx = float(row.get(kvx))
        vy = float(row.get(kvy))
        vz = float(row.get(kvz, 0.0)) if kvz else 0.0

        x_n = x / lu
        y_n = y / lu
        z_n = z / lu
        vx_n = vx * tu / lu
        vy_n = vy * tu / lu
        vz_n = vz * tu / lu

        period = float(row.get(kT)) if kT and row.get(kT) is not None else np.nan
        period_n = period / tu if np.isfinite(period) else np.nan

        C = float(row.get(kC)) if kC and row.get(kC) is not None else np.nan

        records.append(
            {
                "x": x_n,
                "y": y_n,
                "z": z_n,
                "vx": vx_n,
                "vy": vy_n,
                "vz": vz_n,
                "period": period_n,
                "jacobi": C,
                "family": row.get(kfamily, ""),
                "lpoint": row.get(klpoint, ""),
                "branch": row.get(kbranch, "") if kbranch else "",
                "stability": row.get(kstability, "") if kstability else "",
            }
        )

    table_out = pa.Table.from_pylist(records)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    pq.write_table(table_out, args.output)

    print(f"Wrote normalized data: {args.output}")


if __name__ == "__main__":
    main()
