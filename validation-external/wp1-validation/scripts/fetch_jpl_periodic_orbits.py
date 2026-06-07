#!/usr/bin/env python
"""
Fetch JPL periodic orbit catalog data and cache locally.

The JPL SSD Three-Body Periodic Orbits API requires separate queries per
(sys, family, libr, branch) combination.  This script fetches the families
relevant to WP1 validation (lyapunov + halo at L1/L2), merges the results
into a single JSON file, and writes a manifest.

API docs: https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from typing import List, Dict, Any


# Each tuple is (family, libr, branch-or-None).
# branch is required for halo (N/S), not needed for lyapunov.
DEFAULT_QUERIES: List[Dict[str, Any]] = [
    {"family": "lyapunov", "libr": 1},
    {"family": "lyapunov", "libr": 2},
    {"family": "halo", "libr": 1, "branch": "N"},
    {"family": "halo", "libr": 1, "branch": "S"},
    {"family": "halo", "libr": 2, "branch": "N"},
    {"family": "halo", "libr": 2, "branch": "S"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch JPL periodic orbits catalog")
    parser.add_argument(
        "--base-url",
        default="https://ssd-api.jpl.nasa.gov/periodic_orbits.api",
        help="JPL SSD periodic orbits API endpoint",
    )
    parser.add_argument(
        "--sys",
        default="earth-moon",
        help="Three-body system (e.g., earth-moon, sun-earth)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (defaults to validation workspace)",
    )
    return parser.parse_args()


def fetch_one(base_url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch a single (family, libr, branch) combination."""
    query = urlencode(params)
    url = f"{base_url}?{query}"
    request = Request(url, headers={"User-Agent": "wp1-validation/1.0"})
    with urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    if "fields" not in data or "data" not in data:
        raise RuntimeError(f"Unexpected response from {url}: {list(data.keys())}")
    return data


def main() -> None:
    args = parse_args()

    output_dir = args.output_dir or os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "jpl"
    )
    os.makedirs(output_dir, exist_ok=True)

    # We will merge all rows into a unified fields/data structure.
    # Every query returns the same 9 fields; we add family/lpoint/branch columns.
    merged_fields = [
        "family",
        "lpoint",
        "branch",
        "x",
        "y",
        "z",
        "vx",
        "vy",
        "vz",
        "jacobi",
        "period",
        "stability",
    ]
    merged_data: List[list] = []
    system_meta: Dict[str, Any] = {}
    total_fetched = 0

    for q in DEFAULT_QUERIES:
        params: Dict[str, Any] = {
            "sys": args.sys,
            "family": q["family"],
            "libr": q["libr"],
        }
        if "branch" in q:
            params["branch"] = q["branch"]

        label = f'{q["family"]} L{q["libr"]}'
        if "branch" in q:
            label += f' {q["branch"]}'

        print(f"  Fetching {label}...", end="", flush=True)
        data = fetch_one(args.base_url, params)
        count = int(data.get("count", len(data["data"])))
        print(f" {count} orbits", flush=True)

        if not system_meta:
            system_meta = data.get("system", {})

        branch_val = q.get("branch", "")
        lpoint = f'L{q["libr"]}'
        for row in data["data"]:
            merged_data.append([q["family"], lpoint, branch_val] + row)

        total_fetched += count

    print(f"  Total: {total_fetched} orbits", flush=True)

    merged = {
        "fields": merged_fields,
        "data": merged_data,
        "system": system_meta,
        "meta": {
            "lu": 1.0,  # data already in normalized units
            "tu": 1.0,
        },
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = os.path.join(output_dir, f"raw_{timestamp}.json")
    latest_path = os.path.join(output_dir, "raw_latest.json")
    manifest_path = os.path.join(output_dir, "manifest.json")

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(merged, f)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(merged, f)

    manifest = {
        "timestamp": timestamp,
        "sys": args.sys,
        "queries": DEFAULT_QUERIES,
        "total_orbits": total_fetched,
        "output_file": raw_path,
        "latest_file": latest_path,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Saved: {raw_path}")
    print(f"Saved: {latest_path}")
    print(f"Saved: {manifest_path}")


if __name__ == "__main__":
    main()
