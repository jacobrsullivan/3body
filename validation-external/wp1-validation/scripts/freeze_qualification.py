#!/usr/bin/env python
"""Freeze code, corpus, thresholds, and holdout IDs before holdout execution."""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from qualification_common import (
    atomic_write_json,
    canonical_json,
    load_json,
    resolve_manifest_path,
    sha256_bytes,
    sha256_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus-manifest", required=True)
    parser.add_argument("--holdout-ids", required=True)
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def tracked_inputs(
    repo_root: Path,
    spec: Path,
    corpus_manifest: Path,
    holdout: Path,
    results_dir: Path,
) -> list[Path]:
    workspace = repo_root / "validation-external" / "wp1-validation"
    scripts = sorted((workspace / "scripts").glob("*.py"))
    source = sorted((repo_root / "src" / "python").rglob("*.py"))
    tests = [
        repo_root / "tests/test_wp1_qualification.py",
        repo_root / "tests/test_validation_external.py",
    ]
    corpus_payload = load_json(corpus_manifest)
    corpus = resolve_manifest_path(corpus_manifest, corpus_payload["corpus_path"])
    source_manifest = resolve_manifest_path(
        corpus_manifest, corpus_payload["source_manifest"]
    )
    raw_payload = load_json(source_manifest)
    raw_files = [source_manifest.parent / item["path"] for item in raw_payload["files"]]
    result_files = []
    for split in ("development", "calibration"):
        result_files.extend(
            results_dir / f"{split}_{name}.csv"
            for name in ("float64", "oracle", "stability", "reconstruction")
        )
        result_files.append(results_dir / f"{split}_evaluation.json")
    fixed = [
        spec,
        corpus_manifest,
        corpus,
        holdout,
        source_manifest,
        repo_root / "environment.yml",
        repo_root / "pyproject.toml",
        repo_root / "poetry.lock",
        repo_root / "Snakefile",
        workspace / "run_qualification.sh",
        workspace / "reports/wp1_linux_parity.json",
    ]
    unique = {
        path.resolve()
        for path in scripts + source + tests + raw_files + result_files + fixed
    }
    missing = sorted(str(path) for path in unique if not path.is_file())
    if missing:
        raise RuntimeError(f"Cannot freeze missing qualification inputs: {missing}")
    outside = []
    for path in unique:
        try:
            path.relative_to(repo_root)
        except ValueError:
            outside.append(str(path))
    if outside:
        raise RuntimeError(f"Qualification inputs escape the repository: {outside}")
    return sorted(unique)


def runtime_fingerprint() -> dict[str, object]:
    package_names = (
        "numpy",
        "scipy",
        "heyoka",
        "pyarrow",
        "h5py",
        "snakemake",
        "pytest",
    )
    packages = {}
    for name in package_names:
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            if name == "heyoka":
                module = importlib.import_module("heyoka")
                packages[name] = str(module.__version__)
            else:
                packages[name] = "not-installed"
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable_name": Path(sys.executable).name,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": packages,
    }


def verify_pre_holdout_evidence(
    spec: Path, corpus_manifest: Path, results_dir: Path
) -> None:
    spec_hash = sha256_file(spec)
    manifest_hash = sha256_file(corpus_manifest)
    for split in ("development", "calibration"):
        evaluation_path = results_dir / f"{split}_evaluation.json"
        evaluation = load_json(evaluation_path)
        if evaluation.get("status") != "PASS" or evaluation.get("split") != split:
            raise RuntimeError(f"Cannot freeze non-passing {split} evidence")
        if evaluation.get("spec_sha256") != spec_hash:
            raise RuntimeError(f"{split} evaluation uses a different specification")
        if evaluation.get("corpus_manifest_sha256") != manifest_hash:
            raise RuntimeError(f"{split} evaluation uses a different corpus manifest")
        for name, expected in evaluation.get("input_hashes", {}).items():
            result_path = results_dir / f"{split}_{name}.csv"
            if sha256_file(result_path) != expected:
                raise RuntimeError(f"{split} {name} results changed after evaluation")


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    spec = Path(args.spec).resolve()
    corpus_manifest = Path(args.corpus_manifest).resolve()
    holdout = Path(args.holdout_ids).resolve()
    results_dir = Path(args.results_dir).resolve()
    existing_holdout = sorted(results_dir.glob("holdout_*.csv"))
    existing_holdout.extend(results_dir.glob("holdout_evaluation.json"))
    if existing_holdout:
        raise RuntimeError(
            "Refusing to freeze after holdout outputs exist: "
            + ", ".join(str(path) for path in existing_holdout)
        )

    corpus = load_json(corpus_manifest)
    holdout_payload = load_json(holdout)
    if corpus["holdout_ids_sha256"] != holdout_payload["ids_sha256"]:
        raise RuntimeError("Corpus manifest and holdout ID lock disagree")
    corpus_path = resolve_manifest_path(corpus_manifest, corpus["corpus_path"])
    if sha256_file(corpus_path) != corpus["corpus_sha256"]:
        raise RuntimeError("Corpus file and corpus manifest hashes disagree")
    source_manifest = resolve_manifest_path(corpus_manifest, corpus["source_manifest"])
    if sha256_file(source_manifest) != corpus["source_manifest_sha256"]:
        raise RuntimeError("Source manifest changed after corpus construction")
    source_payload = load_json(source_manifest)
    for item in source_payload["files"]:
        source_path = source_manifest.parent / item["path"]
        if sha256_file(source_path) != item["sha256"]:
            raise RuntimeError(f"Pinned source file changed: {source_path}")
    verify_pre_holdout_evidence(spec, corpus_manifest, results_dir)

    files = tracked_inputs(repo_root, spec, corpus_manifest, holdout, results_dir)
    hashes = {
        path.relative_to(repo_root).as_posix(): sha256_file(path) for path in files
    }
    snapshot_hash = sha256_bytes(canonical_json(hashes))
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()
    dirty_paths = subprocess.check_output(
        ["git", "status", "--short"], cwd=repo_root, text=True
    ).splitlines()
    output_relative = Path(args.output).resolve().relative_to(repo_root).as_posix()
    dirty_paths = [
        entry for entry in dirty_paths if entry[3:].strip() != output_relative
    ]
    payload = {
        "schema_version": "1.0",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "qualification_id": f"WP1Q-v1-{snapshot_hash[:12]}",
        "base_git_commit": head,
        "worktree_dirty_at_freeze": bool(dirty_paths),
        "dirty_paths_at_freeze": dirty_paths,
        "spec_sha256": sha256_file(spec),
        "corpus_manifest_sha256": sha256_file(corpus_manifest),
        "corpus_sha256": corpus["corpus_sha256"],
        "holdout_ids_sha256": holdout_payload["ids_sha256"],
        "holdout_case_count": len(holdout_payload["ids"]),
        "holdout_outputs_absent_at_freeze": True,
        "code_snapshot_sha256": snapshot_hash,
        "runtime": runtime_fingerprint(),
        "file_hashes": hashes,
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(args.output, payload)
    print(f"Frozen qualification {payload['qualification_id']}")
    print(f"Lock SHA-256: {payload['lock_sha256']}")


if __name__ == "__main__":
    main()
