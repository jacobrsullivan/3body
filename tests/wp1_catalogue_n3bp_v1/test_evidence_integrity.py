from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp1-catalogue-n3bp-validation"
SCRIPTS = CAMPAIGN / "scripts"
VALIDATION = ROOT / "validation-external"
for path in (SCRIPTS, VALIDATION):
    sys.path.insert(0, str(path))

from campaign_common import (  # noqa: E402
    locked_mass_grid,
    require_full_lock_runtime,
    require_source_free_generation_event,
    validate_source_manifest_metadata,
)
from evaluate_qualification import (  # noqa: E402
    CASE_METRICS,
    CATALOGUE_METRICS,
    REBOUND_METRICS,
    STRUCTURAL_METRICS,
    TRAJECTORY_METRICS,
    require_new_holdout_evaluation,
    validate_evidence_contract,
)
from qualification_tools import (  # noqa: E402
    canonical_json,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
)
from run_focused_tests import (  # noqa: E402
    NORMALIZED_COMMAND,
    focused_test_input_hashes,
    verify_receipt,
)


def _spec() -> dict:
    return {
        "campaign": "WP1-CAT-N3BP-v1",
        "generation": {
            "output_grid": {"m1_min": 0.99, "m1_max": 1.0, "step": 0.01}
        },
        "execution": {
            "expected_candidate_count": 4,
            "expected_external_case_count": 3,
            "rebound_cases_per_split": 1,
        },
        "external_source": {
            "repository": "https://example.invalid/repository",
            "commit": "abc123",
            "path": "source.txt",
            "sha256": "a" * 64,
        },
    }


def _valid_evidence() -> tuple[dict, dict, dict]:
    spec = _spec()
    corpus_cases = [
        {
            "case_id": f"case-{split}",
            "split": split,
            "rebound_selected": True,
        }
        for split in ("development", "calibration", "holdout")
    ]
    corpus = {"campaign": spec["campaign"], "cases": corpus_cases}
    case_metrics = {name: 0.0 for name in CASE_METRICS | REBOUND_METRICS}
    results = {
        "campaign": spec["campaign"],
        "split": "development",
        "cases": [
            {
                "case_id": "case-development",
                "rebound_selected": True,
                "success": True,
                "metrics": case_metrics,
            }
        ],
        "catalogue_metrics": {name: 0.0 for name in CATALOGUE_METRICS},
        "structural": {name: 0.0 for name in STRUCTURAL_METRICS},
        "root_native_metrics": {name: 0.0 for name in TRAJECTORY_METRICS},
    }
    return spec, corpus, results


def test_source_free_boundary_allows_manifest_but_blocks_every_numeric_stage(
    tmp_path: Path,
) -> None:
    campaign = tmp_path / "campaign"
    sources = campaign / "sources"
    sources.mkdir(parents=True)
    (sources / "manifest.json").write_text(
        json.dumps({"external_snapshot": {"selected_rows_path": "patch.txt"}}),
        encoding="utf-8",
    )
    require_source_free_generation_event(campaign)

    forbidden = [
        sources / "patch.txt",
        campaign / "sources/sjtu_mass_patch.txt",
        campaign / "data/qualification_corpus.json",
        campaign / "results/development.json",
        campaign / "results/calibration_evaluation.json",
        campaign / "results/holdout.json",
        campaign / "results/holdout_evaluation.json",
    ]
    for artifact in forbidden:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("numerical evidence", encoding="utf-8")
        with pytest.raises(RuntimeError, match="source-free repository event"):
            require_source_free_generation_event(campaign)
        artifact.unlink()


def test_source_free_boundary_rejects_escaping_manifest_path(tmp_path: Path) -> None:
    sources = tmp_path / "campaign/sources"
    sources.mkdir(parents=True)
    (sources / "manifest.json").write_text(
        json.dumps({"external_snapshot": {"selected_rows_path": "../patch.txt"}}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="unsafe selected source path"):
        require_source_free_generation_event(tmp_path / "campaign")


def test_full_lock_runtime_requires_complete_dictionary_equality() -> None:
    runtime = runtime_fingerprint()
    assert require_full_lock_runtime({"runtime": runtime}, runtime) == runtime

    changed = deepcopy(runtime)
    changed["packages"]["numpy"] = "different"
    with pytest.raises(RuntimeError, match="runtime fingerprint differs"):
        require_full_lock_runtime({"runtime": runtime}, changed)


def test_evaluator_requires_exact_campaign_case_ids_and_complete_metrics() -> None:
    spec, corpus, results = _valid_evidence()
    assert validate_evidence_contract(spec, corpus, results) == results["cases"]

    missing_case = deepcopy(results)
    missing_case["cases"] = []
    with pytest.raises(RuntimeError, match="case-ID set/count"):
        validate_evidence_contract(spec, corpus, missing_case)

    wrong_campaign = deepcopy(results)
    wrong_campaign["campaign"] = "another-campaign"
    with pytest.raises(RuntimeError, match="campaigns must match"):
        validate_evidence_contract(spec, corpus, wrong_campaign)

    missing_metric = deepcopy(results)
    del missing_metric["cases"][0]["metrics"]["external_parameter_error"]
    with pytest.raises(RuntimeError, match="missing required values"):
        validate_evidence_contract(spec, corpus, missing_metric)


def test_evaluator_refuses_existing_holdout_evaluation(tmp_path: Path) -> None:
    output = tmp_path / "holdout_evaluation.json"
    require_new_holdout_evaluation("holdout", output)
    output.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="existing holdout evaluation"):
        require_new_holdout_evaluation("holdout", output)
    require_new_holdout_evaluation("development", output)


def test_grid_and_manifest_are_derived_from_locked_metadata(tmp_path: Path) -> None:
    spec = _spec()
    assert locked_mass_grid(spec) == (0.99, 1.0)
    manifest = {
        "campaign": spec["campaign"],
        "external_snapshot": {
            "repository": spec["external_source"]["repository"],
            "commit": spec["external_source"]["commit"],
            "path": spec["external_source"]["path"],
            "upstream_sha256": spec["external_source"]["sha256"],
            "upstream_row_count": 10,
            "selected_rows_path": "patch.txt",
            "selected_rows_sha256": "b" * 64,
            "selected_row_count": 4,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    loaded, selected = validate_source_manifest_metadata(spec, manifest_path)
    assert loaded == manifest
    assert selected == tmp_path / "patch.txt"

    invalid = deepcopy(spec)
    invalid["generation"]["output_grid"]["m1_max"] = 1.005
    with pytest.raises(RuntimeError, match="not divisible"):
        locked_mass_grid(invalid)


def test_focused_test_receipt_is_self_verifying(tmp_path: Path) -> None:
    spec_path = CAMPAIGN / "qualification_spec.json"
    stdout = "focused tests passed\n"
    stderr = ""
    receipt = {
        "schema_version": "1.0",
        "campaign": "WP1-CAT-N3BP-v1",
        "generated_utc": "2026-07-21T00:00:00+00:00",
        "status": "PASS",
        "spec_sha256": sha256_file(spec_path),
        "command": list(NORMALIZED_COMMAND),
        "test_scope": "tests/wp1_catalogue_n3bp_v1",
        "test_input_hashes": focused_test_input_hashes(),
        "runtime": runtime_fingerprint(),
        "exit_code": 0,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json(receipt))
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert verify_receipt(receipt_path, spec_path) == receipt

    receipt["stdout"] = "tampered"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="receipt integrity failure"):
        verify_receipt(receipt_path, spec_path)


def test_integrity_helpers_are_wired_into_campaign_entry_points() -> None:
    generate = (SCRIPTS / "generate_candidate.py").read_text(encoding="utf-8")
    freeze = (SCRIPTS / "freeze_candidate.py").read_text(encoding="utf-8")
    runner = (SCRIPTS / "run_qualification.py").read_text(encoding="utf-8")
    evaluator = (SCRIPTS / "evaluate_qualification.py").read_text(encoding="utf-8")
    shell = (CAMPAIGN / "run_qualification.sh").read_text(encoding="utf-8")

    assert "require_source_free_generation_event()" in generate
    assert "require_source_free_generation_event()" in freeze
    assert "require_full_lock_runtime(full_lock, execution_runtime)" in runner
    assert "validate_evidence_contract(spec, corpus, results)" in evaluator
    assert "require_new_holdout_evaluation" in evaluator
    assert "run_focused_tests.py\" run" in shell
    assert "run_focused_tests.py\" verify" in shell
    assert "reports/wp1_cat_n3bp_v1_focused_tests.json" in shell
