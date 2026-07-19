#!/usr/bin/env python
"""Fetch and pin the multi-system JPL qualification source corpus."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from qualification_common import (
    atomic_write_json,
    canonical_json,
    load_spec,
    sha256_bytes,
    sha256_file,
)


REQUIRED_FIELDS = {"x", "y", "z", "vx", "vy", "vz", "jacobi", "period", "stability"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def fetch_json(url: str, attempts: int = 3) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "wp1-qualification/1.0"})
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network retry path.
            error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"JPL request failed after {attempts} attempts: {url}: {error}")


def validate_response(
    response: dict[str, Any],
    required_version: str,
    url: str,
    expected_query: dict[str, Any] | None = None,
) -> None:
    signature = response.get("signature") or {}
    if str(signature.get("version")) != required_version:
        raise RuntimeError(
            f"JPL API signature mismatch for {url}: {signature!r}; "
            f"required version {required_version}"
        )
    fields = response.get("fields")
    rows = response.get("data")
    if not isinstance(fields, list) or not isinstance(rows, list):
        raise RuntimeError(f"JPL response has no fields/data table: {url}")
    missing = REQUIRED_FIELDS.difference(fields)
    if missing:
        raise RuntimeError(f"JPL response missing fields {sorted(missing)}: {url}")
    if any(len(row) != len(fields) for row in rows):
        raise RuntimeError(f"JPL response row width does not match fields: {url}")
    if int(response.get("count", len(rows))) != len(rows):
        raise RuntimeError(f"JPL response count does not match data length: {url}")
    if expected_query is not None:
        actual_family = str(response.get("family", "")).lower()
        actual_libration = int(response.get("libration_point", -1))
        actual_branch = str(response.get("branch") or "").upper()
        expected_family = str(expected_query["family"]).lower()
        expected_libration = int(expected_query["libr"])
        expected_branch = str(expected_query.get("branch") or "").upper()
        if (
            actual_family != expected_family
            or actual_libration != expected_libration
            or actual_branch != expected_branch
        ):
            raise RuntimeError(
                f"JPL response metadata does not match request for {url}: "
                f"family={actual_family!r}, libr={actual_libration}, "
                f"branch={actual_branch!r}"
            )


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    spec = load_spec(spec_path)
    source = spec["external_source"]
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()

    files = []
    for system in source["systems"]:
        print(f"Fetching JPL qualification source for {system}", flush=True)
        queries = []
        system_metadata: dict[str, Any] | None = None
        signatures = []
        for query_spec in source["queries"]:
            params = {"sys": system, **query_spec}
            url = f"{source['url']}?{urlencode(params)}"
            response = fetch_json(url)
            validate_response(response, source["required_api_version"], url, query_spec)
            if system_metadata is None:
                system_metadata = response["system"]
            elif response["system"] != system_metadata:
                raise RuntimeError(f"JPL system metadata changed within {system}")
            signatures.append(response["signature"])
            queries.append(
                {
                    "request": params,
                    "url": url,
                    "signature": response["signature"],
                    "family": response.get("family", query_spec["family"]),
                    "libration_point": response.get(
                        "libration_point", query_spec.get("libr")
                    ),
                    "branch": response.get("branch", query_spec.get("branch", "")),
                    "filter": response.get("filter", {}),
                    "limits": response.get("limits", {}),
                    "count": int(response.get("count", len(response["data"]))),
                    "fields": response["fields"],
                    "data": response["data"],
                }
            )
            print(
                f"  {query_spec['family']} L{query_spec['libr']} "
                f"{query_spec.get('branch', '')}: {len(response['data'])}",
                flush=True,
            )

        payload = {
            "schema_version": "1.0",
            "retrieved_utc": retrieved,
            "source": source["name"],
            "documentation": source["documentation"],
            "system_key": system,
            "system": system_metadata,
            "signatures": signatures,
            "queries": queries,
        }
        destination = output_dir / f"{system}.json"
        atomic_write_json(destination, payload)
        files.append(
            {
                "system": system,
                "path": destination.name,
                "sha256": sha256_file(destination),
                "records": sum(query["count"] for query in queries),
                "mass_ratio": float(system_metadata["mass_ratio"]),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "retrieved_utc": retrieved,
        "spec_path": str(spec_path),
        "spec_sha256_at_fetch": sha256_file(spec_path),
        "source_config_sha256": sha256_bytes(canonical_json(source)),
        "required_api_version": source["required_api_version"],
        "files": files,
        "total_records": sum(item["records"] for item in files),
    }
    atomic_write_json(output_dir / "manifest.json", manifest)
    print(f"Pinned {manifest['total_records']} JPL records in {output_dir}")


if __name__ == "__main__":
    main()
