"""Integrity helpers shared by the WP1-CAT-N3BP-v1 campaign scripts."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = Path(__file__).resolve().parents[1]
SPECIFICATION_LOCK = (
    CAMPAIGN / "reports/wp1_cat_n3bp_v1_specification_lock.json"
)
PREREQUISITE_LOCK = (
    VALIDATION / "wp1-n3bp-validation/reports/wp1_n3bp_qualification_lock.json"
)
PREREQUISITE_RECORD = (
    VALIDATION / "wp1-n3bp-validation/reports/wp1_n3bp_qualification_record.json"
)
SPLITS = ("development", "calibration", "holdout")


def _safe_child(base: Path, relative_name: str, label: str) -> Path:
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"unsafe {label} path: {relative_name}")
    candidate = (base / relative).resolve()
    resolved_base = base.resolve()
    if candidate != resolved_base and resolved_base not in candidate.parents:
        raise RuntimeError(f"unsafe {label} path: {relative_name}")
    return candidate


def require_source_free_generation_event(campaign: Path = CAMPAIGN) -> None:
    """Require all numerical external evidence to be absent before generation."""

    from qualification_tools import load_json

    campaign = campaign.resolve()
    manifest_path = campaign / "sources/manifest.json"
    selected_source = campaign / "sources/sjtu_mass_patch.txt"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        try:
            selected_name = manifest["external_snapshot"]["selected_rows_path"]
        except (KeyError, TypeError) as error:
            raise RuntimeError("source manifest lacks selected_rows_path") from error
        selected_source = _safe_child(
            manifest_path.parent, str(selected_name), "selected source"
        )

    forbidden = {
        selected_source,
        campaign / "sources/sjtu_mass_patch.txt",
        campaign / "data/qualification_corpus.json",
    }
    forbidden.update((campaign / "data").glob("*corpus*.json"))
    forbidden.update((campaign / "results").glob("*.json"))
    for split in SPLITS:
        forbidden.add(campaign / f"results/{split}.json")
        forbidden.add(campaign / f"results/{split}_evaluation.json")
    existing = sorted(str(path) for path in forbidden if path.exists())
    if existing:
        raise RuntimeError(
            "native generation/freeze requires a source-free repository event; "
            "remove numerical SJTU, corpus, and split outputs first: "
            + ", ".join(existing)
        )


def locked_mass_grid(spec: dict[str, Any]) -> tuple[float, ...]:
    """Derive the exact one-dimensional mass grid from locked decimal values."""

    output_grid = spec["generation"]["output_grid"]
    start = Decimal(str(output_grid["m1_min"]))
    stop = Decimal(str(output_grid["m1_max"]))
    step = Decimal(str(output_grid["step"]))
    if step <= 0 or stop < start:
        raise RuntimeError("locked mass-grid bounds or step are invalid")
    intervals = (stop - start) / step
    if intervals != intervals.to_integral_value():
        raise RuntimeError("locked mass-grid endpoints are not divisible by the step")
    count = int(intervals) + 1
    expected_candidates = int(spec["execution"]["expected_candidate_count"])
    if count * count != expected_candidates:
        raise RuntimeError(
            "locked mass grid does not produce the expected candidate count"
        )
    return tuple(float(start + step * index) for index in range(count))


def validate_source_manifest_metadata(
    spec: dict[str, Any], manifest_path: str | Path
) -> tuple[dict[str, Any], Path]:
    from qualification_tools import load_json

    path = Path(manifest_path).resolve()
    manifest = load_json(path)
    if manifest.get("campaign") != spec["campaign"]:
        raise RuntimeError("source manifest campaign mismatch")
    snapshot = manifest.get("external_snapshot")
    if not isinstance(snapshot, dict):
        raise RuntimeError("source manifest lacks external_snapshot metadata")
    for manifest_key, spec_key in (
        ("repository", "repository"),
        ("commit", "commit"),
        ("path", "path"),
        ("upstream_sha256", "sha256"),
    ):
        if snapshot.get(manifest_key) != spec["external_source"][spec_key]:
            raise RuntimeError(
                f"source manifest {manifest_key} differs from the locked specification"
            )
    expected_count = int(spec["execution"]["expected_candidate_count"])
    if snapshot.get("selected_row_count") != expected_count:
        raise RuntimeError("source manifest selected-row count mismatch")
    if not isinstance(snapshot.get("upstream_row_count"), int) or snapshot[
        "upstream_row_count"
    ] < expected_count:
        raise RuntimeError("source manifest upstream-row count is invalid")
    for key in ("upstream_sha256", "selected_rows_sha256"):
        digest = snapshot.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise RuntimeError(f"source manifest {key} is not a SHA-256 digest")
    selected_name = snapshot.get("selected_rows_path")
    if not isinstance(selected_name, str) or not selected_name:
        raise RuntimeError("source manifest selected_rows_path is invalid")
    selected_path = _safe_child(path.parent, selected_name, "selected source")
    return manifest, selected_path


def verify_source_snapshot(
    spec: dict[str, Any], manifest_path: str | Path
) -> tuple[dict[str, Any], Path]:
    from qualification_tools import sha256_file

    manifest, selected_path = validate_source_manifest_metadata(spec, manifest_path)
    if not selected_path.is_file():
        raise RuntimeError(f"selected SJTU source snapshot is missing: {selected_path}")
    expected = manifest["external_snapshot"]["selected_rows_sha256"]
    if sha256_file(selected_path) != expected:
        raise RuntimeError("selected SJTU source snapshot hash mismatch")
    return manifest, selected_path


def require_full_lock_runtime(
    full_lock: dict[str, Any], actual: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Require exact equality across every runtime-fingerprint field."""

    from qualification_tools import runtime_fingerprint

    expected = full_lock.get("runtime")
    if not isinstance(expected, dict):
        raise RuntimeError("full qualification lock lacks a runtime fingerprint")
    observed = runtime_fingerprint() if actual is None else actual
    if observed != expected:
        raise RuntimeError(
            f"runtime fingerprint differs from full lock: expected {expected!r}, "
            f"observed {observed!r}"
        )
    return observed


def verify_specification_lock(spec_path: str | Path) -> dict[str, Any]:
    from qualification_tools import canonical_json, load_json, sha256_bytes, sha256_file

    lock = load_json(SPECIFICATION_LOCK)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256")
    if sha256_bytes(canonical_json(unsigned)) != recorded:
        raise RuntimeError("WP1-CAT-N3BP specification lock integrity failure")
    if lock["spec_sha256"] != sha256_file(spec_path):
        raise RuntimeError("WP1-CAT-N3BP specification changed after claim lock")
    for relative, expected in lock["prerequisite_file_hashes"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"WP1-CAT-N3BP prerequisite changed: {relative}")
    return lock


def verify_prerequisite(spec: dict[str, Any]) -> dict[str, str]:
    from qualification_tools import load_json, sha256_file, verify_lock

    expected = spec["prerequisites"]["wp1_n3bp"]
    lock = verify_lock(PREREQUISITE_LOCK, ROOT, expected_prefix="WP1Q-N3BP-v1")
    record = load_json(PREREQUISITE_RECORD)
    if not (
        record.get("status") == "PASS"
        and record.get("qualification_id")
        == expected["qualification_id"]
        == lock["qualification_id"]
        and lock["lock_sha256"] == expected["lock_sha256"]
        and sha256_file(PREREQUISITE_RECORD) == expected["record_file_sha256"]
    ):
        raise RuntimeError("WP1-CAT-N3BP prerequisite qualification is invalid")
    return {"status": "PASS", "qualification_id": lock["qualification_id"]}


def verify_candidate_lock(
    lock_path: str | Path, catalogue_path: str | Path, spec_path: str | Path
) -> dict[str, Any]:
    from qualification_tools import canonical_json, load_json, sha256_bytes, sha256_file

    lock = load_json(lock_path)
    unsigned = dict(lock)
    recorded = unsigned.pop("candidate_lock_sha256", "")
    actual = sha256_bytes(canonical_json(unsigned))
    if not recorded or actual != recorded:
        raise RuntimeError("native candidate lock integrity failure")
    if lock.get("spec_sha256") != sha256_file(spec_path):
        raise RuntimeError("native candidate lock uses a different specification")
    if lock.get("catalogue_file_sha256") != sha256_file(catalogue_path):
        raise RuntimeError("native catalogue changed after candidate freeze")
    for relative, expected in lock.get("file_hashes", {}).items():
        candidate = (ROOT / relative).resolve()
        if ROOT not in candidate.parents and candidate != ROOT:
            raise RuntimeError(f"unsafe candidate-lock path: {relative}")
        if sha256_file(candidate) != expected:
            raise RuntimeError(f"candidate-generation input changed: {relative}")
    return lock


def from_hex(value: str) -> float:
    return float.fromhex(str(value))
