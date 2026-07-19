#!/usr/bin/env python
"""
Generate a checksum/provenance manifest for WP1 validation artifacts.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

WORKSPACE_PATTERNS = [
    "config.yaml",
    "data/jpl/manifest.json",
    "data/jpl/raw_latest.json",
    "data/jpl/normalized.parquet",
    "results/*.csv",
    "results/*.json",
    "results/*.parquet",
    "reports/*.md",
]

REPO_PATTERNS = [
    "environment.yml",
    "poetry.lock",
    "pyproject.toml",
    "data/tier1/analysis/validation_report.txt",
    "data/tier1/parquet/*.parquet",
    "data/tier2/analysis/validation_report.txt",
    "data/tier2/parquet/*.parquet",
]

PACKAGE_NAMES = [
    "numpy",
    "scipy",
    "rebound",
    "heyoka",
    "h5py",
    "pyarrow",
    "pytest",
    "snakemake",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate WP1 artifact manifest")
    parser.add_argument(
        "--workspace",
        default=str(Path(__file__).resolve().parents[1]),
        help="External validation workspace root",
    )
    parser.add_argument("--output", required=True, help="Output manifest JSON")
    parser.add_argument(
        "--command",
        default="",
        help="Command used to generate the current validation artifacts",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def _package_versions() -> dict[str, str]:
    versions = {}
    for name in PACKAGE_NAMES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def _artifact_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256_file(path),
    }


def _collect_paths(workspace: Path, output: Path) -> list[Path]:
    paths: set[Path] = set()

    for pattern in WORKSPACE_PATTERNS:
        paths.update(Path(p).resolve() for p in glob.glob(str(workspace / pattern)))

    for pattern in REPO_PATTERNS:
        paths.update(Path(p).resolve() for p in glob.glob(str(REPO_ROOT / pattern)))

    output = output.resolve()
    return sorted(p for p in paths if p.is_file() and p.resolve() != output)


def build_manifest(workspace: Path, output: Path, command: str) -> dict[str, Any]:
    status = _run_git(["status", "--short"])
    artifacts = [_artifact_record(path) for path in _collect_paths(workspace, output)]

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "WP1 bobs-mini validation artifacts",
        "repo": {
            "root": str(REPO_ROOT),
            "commit": _run_git(["rev-parse", "HEAD"]),
            "branch": _run_git(["branch", "--show-current"]),
            "dirty": bool(status),
            "status_short": status.splitlines(),
        },
        "environment": {
            "python": sys.version.replace("\n", " "),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "packages": _package_versions(),
        },
        "command": command,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def main() -> None:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    output = Path(args.output).resolve()

    manifest = build_manifest(workspace, output, args.command)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"Wrote artifact manifest: {output}")


if __name__ == "__main__":
    main()
