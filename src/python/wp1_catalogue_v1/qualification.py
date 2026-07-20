"""Locked corpus, gate, and record support for WP1-CAT-v1."""

from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .core import STATE_KEYS, canonical_catalogue_payload, match_external_rows


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: str | Path, value: Any, *, refuse_overwrite: bool = False) -> None:
    destination = Path(path)
    if refuse_overwrite and destination.exists():
        raise RuntimeError(f"Refusing to overwrite immutable artifact: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], *, refuse_overwrite: bool = False) -> None:
    if not rows:
        raise ValueError("Refusing to write an empty result table")
    destination = Path(path)
    if refuse_overwrite and destination.exists():
        raise RuntimeError(f"Refusing to overwrite immutable artifact: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_rank(identifier: str, salt: str) -> str:
    return sha256_bytes(f"{salt}:{identifier}".encode("utf-8"))


def _source_identifier(row: Mapping[str, Any], index: int) -> str:
    token = {
        "source_row_index": index,
        **{key: row[key] for key in (*STATE_KEYS, "period", "jacobi", "family", "lpoint", "branch", "stability")},
    }
    return f"jpl-em-lyapunov-{str(row['lpoint']).lower()}-{sha256_bytes(canonical_json(token))[:16]}"


def build_corpus(
    spec_path: str | Path,
    source_path: str | Path,
    corpus_path: str | Path,
    manifest_path: str | Path,
    holdout_ids_path: str | Path,
) -> dict[str, Any]:
    """Build balanced disjoint partitions from the pinned evaluation source."""
    spec = load_json(spec_path)
    source = Path(source_path).resolve()
    table = pq.read_table(source)
    if table.num_rows != int(spec["external_source"]["required_rows"]):
        raise RuntimeError(
            f"Pinned source has {table.num_rows} rows, expected "
            f"{spec['external_source']['required_rows']}"
        )
    rows = table.to_pylist()
    selected: list[dict[str, Any]] = []
    salt = str(spec["sampling"]["salt"])
    split_order = ("development", "calibration", "holdout")
    counts = spec["sampling"]["per_lpoint"]

    from src.python.orbits.periodic_families import collinear_lagrange_point

    mu = float(spec["model"]["mu"])
    for lpoint in ("L1", "L2"):
        branch = spec["generation"]["branches"][lpoint]
        minimum = float(branch["amplitude_min"])
        maximum = float(branch["amplitude_max"])
        x_l = collinear_lagrange_point(mu, lpoint)
        eligible: list[dict[str, Any]] = []
        for index, raw in enumerate(rows):
            if str(raw["family"]).lower() != "lyapunov" or str(raw["lpoint"]) != lpoint:
                continue
            amplitude = x_l - float(raw["x"])
            if not (minimum <= amplitude <= maximum):
                continue
            if not all(math.isfinite(float(raw[key])) for key in (*STATE_KEYS, "period", "jacobi", "stability")):
                continue
            row = {
                "catalog_id": _source_identifier(raw, index),
                "source_row_index": index,
                "source": "NASA/JPL Three-Body Periodic Orbits API",
                "system": "earth-moon",
                "family": "lyapunov",
                "lpoint": lpoint,
                "branch": str(raw.get("branch", "") or ""),
                "amplitude": float(amplitude),
                **{key: float(raw[key]) for key in STATE_KEYS},
                "period": float(raw["period"]),
                "jacobi": float(raw["jacobi"]),
                "stability": float(raw["stability"]),
            }
            eligible.append(row)
        ordered = sorted(eligible, key=lambda row: _stable_rank(row["catalog_id"], f"{salt}:{lpoint}"))
        required = sum(int(counts[split]) for split in split_order)
        if len(ordered) < required:
            raise RuntimeError(f"Only {len(ordered)} eligible {lpoint} rows; {required} required")
        cursor = 0
        for split in split_order:
            amount = int(counts[split])
            for row in ordered[cursor : cursor + amount]:
                selected.append({**row, "split": split})
            cursor += amount

    identifiers = [row["catalog_id"] for row in selected]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("Corpus selection produced duplicate identifiers")
    destination = Path(corpus_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(selected), destination, compression="zstd")
    holdout_ids = sorted(row["catalog_id"] for row in selected if row["split"] == "holdout")
    write_json(
        holdout_ids_path,
        {
            "schema_version": "1.0",
            "campaign": "WP1-CAT-v1",
            "selection_salt_sha256": sha256_bytes(salt.encode("utf-8")),
            "holdout_ids": holdout_ids,
        },
    )
    split_counts = Counter(row["split"] for row in selected)
    lpoint_counts = Counter(f"{row['split']}|{row['lpoint']}" for row in selected)
    manifest = {
        "schema_version": "1.0",
        "campaign": "WP1-CAT-v1",
        "created_utc": _utc_now(),
        "spec_sha256": sha256_file(spec_path),
        "source_path": str(source.relative_to(Path(spec_path).resolve().parents[2])),
        "source_sha256": sha256_file(source),
        "source_rows": table.num_rows,
        "corpus_path": str(destination.resolve().relative_to(Path(spec_path).resolve().parents[2])),
        "corpus_sha256": sha256_file(destination),
        "holdout_ids_path": str(Path(holdout_ids_path).resolve().relative_to(Path(spec_path).resolve().parents[2])),
        "holdout_ids_sha256": sha256_file(holdout_ids_path),
        "selected_rows": len(selected),
        "split_counts": dict(sorted(split_counts.items())),
        "split_lpoint_counts": dict(sorted(lpoint_counts.items())),
        "partition_disjoint": True,
        "generation_inputs_include_external_rows": False,
    }
    write_json(manifest_path, manifest)
    return manifest


def write_native_catalogue(
    catalogue_path: str | Path,
    provenance_path: str | Path,
    run: Any,
) -> dict[str, Any]:
    destination = Path(catalogue_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(run.rows), destination, compression="zstd")
    total_seconds = float(run.generation_seconds + run.stability_seconds)
    provenance = {
        **run.provenance,
        "created_utc": _utc_now(),
        "catalogue_path": f"{destination.parent.name}/{destination.name}",
        "catalogue_file_sha256": sha256_file(destination),
        "generation_seconds": float(run.generation_seconds),
        "stability_seconds": float(run.stability_seconds),
        "total_seconds": total_seconds,
        "corrected_orbits_per_second": len(run.rows) / total_seconds,
        "rejected_duplicates": run.rejected_duplicates,
    }
    write_json(provenance_path, provenance)
    return provenance


def freeze_qualification(
    repo_root: str | Path,
    campaign_root: str | Path,
    lock_path: str | Path,
) -> dict[str, Any]:
    """Freeze exact implementation, corpus, external source, and candidates."""
    root = Path(repo_root).resolve()
    campaign = Path(campaign_root).resolve()
    spec_path = campaign / "qualification_spec.json"
    manifest = load_json(campaign / "data/corpus_manifest.json")
    provenance = load_json(campaign / "results/native_catalogue_provenance.json")
    paths = [
        spec_path,
        campaign / "data/corpus.parquet",
        campaign / "data/corpus_manifest.json",
        campaign / "data/holdout_ids.json",
        campaign / "results/native_catalogue.parquet",
        campaign / "results/native_catalogue_provenance.json",
        campaign / "run_qualification.sh",
        campaign / "scripts/run_campaign.py",
        root / "src/python/wp1_catalogue_v1/__init__.py",
        root / "src/python/wp1_catalogue_v1/core.py",
        root / "src/python/wp1_catalogue_v1/qualification.py",
        root / "src/python/wp1_catalogue_v1/cli.py",
        root / "src/python/orbits/differential_correction.py",
        root / "src/python/orbits/periodic_families.py",
        root / "src/python/validation/cr3bp_variational.py",
        root / manifest["source_path"],
    ]
    file_hashes = {
        str(path.resolve().relative_to(root)): sha256_file(path)
        for path in paths
    }
    design_sha = sha256_bytes(canonical_json(file_hashes))
    try:
        base_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        base_commit = "unavailable"
    unsigned = {
        "schema_version": "1.0",
        "campaign": "WP1-CAT-v1",
        "qualification_id": f"WP1-CAT-v1-{design_sha[:12]}",
        "created_utc": _utc_now(),
        "base_git_commit": base_commit,
        "design_snapshot_sha256": design_sha,
        "spec_sha256": sha256_file(spec_path),
        "corpus_sha256": manifest["corpus_sha256"],
        "external_source_sha256": manifest["source_sha256"],
        "candidate_payload_sha256": provenance["catalogue_payload_sha256"],
        "candidate_file_sha256": provenance["catalogue_file_sha256"],
        "holdout_ids_sha256": manifest["holdout_ids_sha256"],
        "file_hashes": dict(sorted(file_hashes.items())),
        "policy": {
            "thresholds_frozen_before_split_evaluation": True,
            "candidate_generated_without_external_input": True,
            "holdout_requires_preholdout_pass": True,
            "final_record_immutable": True,
        },
    }
    lock = {**unsigned, "lock_sha256": sha256_bytes(canonical_json(unsigned))}
    write_json(lock_path, lock, refuse_overwrite=True)
    return lock


def verify_lock(lock_path: str | Path, repo_root: str | Path) -> dict[str, Any]:
    lock = load_json(lock_path)
    unsigned = dict(lock)
    expected = str(unsigned.pop("lock_sha256", ""))
    actual = sha256_bytes(canonical_json(unsigned))
    if not expected or actual != expected:
        raise RuntimeError(f"Qualification lock integrity failure: {actual} != {expected}")
    root = Path(repo_root).resolve()
    for relative, expected_hash in lock["file_hashes"].items():
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RuntimeError(f"Lock path escapes repository: {relative}") from exc
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Qualification lock violation: {relative} is {actual_hash}, expected {expected_hash}"
            )
    return lock


def _percentile(values: Iterable[float], quantile: float) -> float:
    array = np.asarray(list(values), dtype=float)
    return float(np.percentile(array, quantile)) if len(array) else float("nan")


def _maximum(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    return float(np.max(array)) if len(array) else float("nan")


def _rate(values: Iterable[bool]) -> float:
    array = list(values)
    return float(sum(bool(value) for value in array) / len(array)) if array else 0.0


def _add_gate(
    gates: list[dict[str, Any]], name: str, observed: float | int, comparator: str, threshold: float | int
) -> None:
    finite = math.isfinite(float(observed))
    operations = {
        ">=": observed >= threshold,
        "<=": observed <= threshold,
        "==": observed == threshold,
    }
    gates.append(
        {
            "name": name,
            "observed": observed,
            "comparator": comparator,
            "threshold": threshold,
            "passed": bool(finite and operations[comparator]),
        }
    )


def _monotone_fraction(rows: Sequence[Mapping[str, Any]], lpoint: str) -> float:
    branch = sorted(
        (row for row in rows if row["lpoint"] == lpoint),
        key=lambda row: float(row["amplitude"]),
    )
    differences = np.diff([float(row["jacobi"]) for row in branch])
    return float(np.mean(differences < 0.0)) if len(differences) else 0.0


def _load_candidates(catalogue_path: str | Path, provenance_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = pq.read_table(catalogue_path).to_pylist()
    provenance = load_json(provenance_path)
    payload_hash = sha256_bytes(canonical_catalogue_payload(rows))
    if payload_hash != provenance["catalogue_payload_sha256"]:
        raise RuntimeError("Native catalogue payload does not match provenance")
    if sha256_file(catalogue_path) != provenance["catalogue_file_sha256"]:
        raise RuntimeError("Native catalogue file does not match provenance")
    return rows, provenance


def evaluate_split(
    repo_root: str | Path,
    campaign_root: str | Path,
    split: str,
) -> dict[str, Any]:
    if split not in {"development", "calibration", "holdout"}:
        raise ValueError(f"Unsupported split: {split}")
    root = Path(repo_root).resolve()
    campaign = Path(campaign_root).resolve()
    lock = verify_lock(campaign / "reports/wp1_cat_v1_qualification_lock.json", root)
    if split == "holdout":
        for prerequisite in ("development", "calibration"):
            path = campaign / f"results/{prerequisite}_evaluation.json"
            if not path.exists() or load_json(path).get("status") != "PASS":
                raise RuntimeError(f"Holdout is sealed until {prerequisite} is PASS")
    evaluation_path = campaign / f"results/{split}_evaluation.json"
    matches_path = campaign / f"results/{split}_matches.csv"
    if evaluation_path.exists() or matches_path.exists():
        raise RuntimeError(f"Refusing to overwrite immutable {split} results")

    spec = load_json(campaign / "qualification_spec.json")
    corpus = [
        row
        for row in pq.read_table(campaign / "data/corpus.parquet").to_pylist()
        if row["split"] == split
    ]
    candidates, provenance = _load_candidates(
        campaign / "results/native_catalogue.parquet",
        campaign / "results/native_catalogue_provenance.json",
    )
    if provenance["external_data_used_by_generation"] is not False:
        raise RuntimeError("Candidate provenance does not prove external-free generation")
    matches = match_external_rows(corpus, candidates, spec)
    if {row["catalog_id"] for row in matches} != {row["catalog_id"] for row in corpus}:
        raise RuntimeError("Evaluation did not exactly cover the frozen split")

    native = spec["gates"]["native"]
    external = spec["gates"]["external"]
    gates: list[dict[str, Any]] = []
    lpoint_counts = Counter(row["lpoint"] for row in candidates)
    _add_gate(gates, "native.candidate_count", len(candidates), ">=", int(native["candidate_count_min"]))
    _add_gate(gates, "native.L1_members", lpoint_counts["L1"], ">=", int(native["L1_members_min"]))
    _add_gate(gates, "native.L2_members", lpoint_counts["L2"], ">=", int(native["L2_members_min"]))
    _add_gate(gates, "native.duplicate_count", int(provenance["duplicate_count"]), "<=", int(native["duplicate_count_max"]))
    _add_gate(gates, "native.closure_error_p95", _percentile((row["closure_error"] for row in candidates), 95), "<=", float(native["closure_error_p95_max"]))
    _add_gate(gates, "native.closure_error_max", _maximum(row["closure_error"] for row in candidates), "<=", float(native["closure_error_max"]))
    _add_gate(gates, "native.symmetry_residual_p95", _percentile((row["symmetry_residual"] for row in candidates), 95), "<=", float(native["symmetry_residual_p95_max"]))
    for lpoint in ("L1", "L2"):
        _add_gate(gates, f"native.{lpoint}_jacobi_monotone_fraction", _monotone_fraction(candidates, lpoint), ">=", float(native["jacobi_monotone_fraction_min"]))
    _add_gate(gates, "native.monodromy_determinant_error_max", _maximum(row["monodromy_determinant_error"] for row in candidates), "<=", float(native["monodromy_determinant_error_max"]))
    _add_gate(gates, "native.reciprocal_pair_error_max", _maximum(row["reciprocal_pair_error"] for row in candidates), "<=", float(native["reciprocal_pair_error_max"]))
    _add_gate(gates, "external.minimum_cases", len(matches), ">=", int(external["minimum_cases"][split]))
    _add_gate(gates, "external.recovery_rate", _rate(row["recovered"] for row in matches), ">=", float(external["recovery_rate_min"]))
    for metric in ("state_error", "period_relative_error", "jacobi_error", "stability_relative_error"):
        _add_gate(gates, f"external.{metric}_p95", _percentile((row[metric] for row in matches), 95), "<=", float(external[f"{metric}_p95_max"]))
        _add_gate(gates, f"external.{metric}_max", _maximum(row[metric] for row in matches), "<=", float(external[f"{metric}_max"]))
    _add_gate(gates, "external.stability_label_accuracy", _rate(row["stability_label_match"] for row in matches), ">=", float(external["stability_label_accuracy_min"]))
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    evaluation = {
        "schema_version": "1.0",
        "campaign": "WP1-CAT-v1",
        "qualification_id": lock["qualification_id"],
        "split": split,
        "status": status,
        "executed_utc": _utc_now(),
        "lock_sha256": lock["lock_sha256"],
        "candidate_payload_sha256": provenance["catalogue_payload_sha256"],
        "case_count": len(matches),
        "case_counts_by_lpoint": dict(sorted(Counter(row["lpoint"] for row in matches).items())),
        "native_candidate_counts": dict(sorted(lpoint_counts.items())),
        "throughput": {
            key: provenance[key]
            for key in (
                "generation_seconds",
                "stability_seconds",
                "total_seconds",
                "corrected_orbits_per_second",
            )
        },
        "gates": gates,
        "failed_gates": [gate["name"] for gate in gates if not gate["passed"]],
    }
    write_csv(matches_path, matches, refuse_overwrite=True)
    evaluation["matches_sha256"] = sha256_file(matches_path)
    write_json(evaluation_path, evaluation, refuse_overwrite=True)
    return evaluation


def finalize_record(repo_root: str | Path, campaign_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    campaign = Path(campaign_root).resolve()
    lock = verify_lock(campaign / "reports/wp1_cat_v1_qualification_lock.json", root)
    spec = load_json(campaign / "qualification_spec.json")
    evaluations = {
        split: load_json(campaign / f"results/{split}_evaluation.json")
        for split in ("development", "calibration", "holdout")
    }
    status = "PASS" if all(value["status"] == "PASS" for value in evaluations.values()) else "FAIL"
    manifest = load_json(campaign / "data/corpus_manifest.json")
    provenance = load_json(campaign / "results/native_catalogue_provenance.json")
    record: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": "WP1-CAT-v1",
        "qualification_id": lock["qualification_id"],
        "status": status,
        "claim": spec["claim"],
        "evidence_boundary": spec["evidence_boundary"],
        "created_utc": _utc_now(),
        "base_git_commit": lock["base_git_commit"],
        "lock_sha256": lock["lock_sha256"],
        "design_snapshot_sha256": lock["design_snapshot_sha256"],
        "external_source_sha256": manifest["source_sha256"],
        "corpus_sha256": manifest["corpus_sha256"],
        "corpus_counts": {
            "split": manifest["split_counts"],
            "split_lpoint": manifest["split_lpoint_counts"],
        },
        "candidate_payload_sha256": provenance["catalogue_payload_sha256"],
        "candidate_file_sha256": provenance["catalogue_file_sha256"],
        "candidate_count": provenance["candidate_count_after_deduplication"],
        "duplicate_count": provenance["duplicate_count"],
        "external_data_used_by_generation": provenance["external_data_used_by_generation"],
        "throughput": {
            key: provenance[key]
            for key in (
                "generation_seconds",
                "stability_seconds",
                "total_seconds",
                "corrected_orbits_per_second",
                "runtime",
            )
        },
        "evaluation_status": {split: value["status"] for split, value in evaluations.items()},
        "evaluation_sha256": {
            split: sha256_file(campaign / f"results/{split}_evaluation.json")
            for split in evaluations
        },
        "evaluations": evaluations,
        "downstream_policy": "Cite the qualification ID and exact evidence boundary; do not promote this bounded planar result to a complete or general three-body catalogue claim.",
    }
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    record_path = campaign / "reports/wp1_cat_v1_qualification_record.json"
    write_json(record_path, record, refuse_overwrite=True)
    generate_report(record, campaign / "reports/wp1_cat_v1_qualification_report.md")
    return record


def generate_report(record: Mapping[str, Any], output_path: str | Path) -> None:
    evaluations = record["evaluations"]
    lines = [
        "# WP1-CAT-v1 qualification report",
        "",
        f"**Qualification:** `{record['qualification_id']}`  ",
        f"**Status:** **{record['status']}**  ",
        f"**Lock:** `{record['lock_sha256']}`",
        "",
        "## Qualified claim",
        "",
        str(record["claim"]),
        "",
        "## Evidence boundary",
        "",
        str(record["evidence_boundary"]),
        "",
        "## Evidence summary",
        "",
        f"- Native candidates: {record['candidate_count']} ({record['duplicate_count']} duplicates rejected)",
        f"- External data used during native generation: {record['external_data_used_by_generation']}",
        f"- Measured end-to-end rate: {record['throughput']['corrected_orbits_per_second']:.3f} corrected/stability-labelled orbits/s",
        f"- Development: {evaluations['development']['status']} on {evaluations['development']['case_count']} JPL rows",
        f"- Calibration: {evaluations['calibration']['status']} on {evaluations['calibration']['case_count']} JPL rows",
        f"- Holdout: {evaluations['holdout']['status']} on {evaluations['holdout']['case_count']} JPL rows",
        "",
        "## Gate detail",
        "",
        "| Split | Gate | Observed | Requirement | Result |",
        "|---|---|---:|---:|---|",
    ]
    for split in ("development", "calibration", "holdout"):
        for gate in evaluations[split]["gates"]:
            lines.append(
                f"| {split} | `{gate['name']}` | {gate['observed']:.8g} | "
                f"{gate['comparator']} {gate['threshold']:.8g} | "
                f"{'PASS' if gate['passed'] else 'FAIL'} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A PASS qualifies only the two declared, connected, planar family segments and their sampled external recovery. It is evidence for a usable bounded native catalogue component, not evidence of catalogue completeness or general periodic-orbit production.",
            "",
        ]
    )
    destination = Path(output_path)
    if destination.exists():
        raise RuntimeError(f"Refusing to overwrite immutable report: {destination}")
    destination.write_text("\n".join(lines), encoding="utf-8")
