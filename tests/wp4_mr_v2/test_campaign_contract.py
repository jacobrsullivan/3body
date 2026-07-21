from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
import sys

from src.python.wp4_mr_v2 import classify_masses


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = VALIDATION / "wp4-mr-ni-v2"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402


def _module(relative: str, name: str):
    return campaign_module(CAMPAIGN / relative, name)


def test_corrected_specification_lock_and_invalidated_v1_are_intact() -> None:
    common = _module("scripts/campaign_common.py", "_wp4_mr_v2_test_common")
    lock = common.verify_specification_lock(CAMPAIGN / "qualification_spec.json")
    assert lock["campaign"] == "WP4-MR-NI-v2"
    assert (
        lock["specification_lock_sha256"]
        == "75a2fdb11354baa903bb1861d6fb7a9967f42b5428cdb877820a042a09ec8cd4"
    )
    predecessor = common.verify_invalidated_v1()
    assert predecessor["status"] == "INVALIDATED_PREIMPLEMENTATION"
    assert predecessor["implementation_started"] is False
    assert predecessor["scientific_outputs_produced"] is False


def test_source_manifest_pins_two_primary_pdf_hashes_without_redistribution() -> None:
    manifest = json.loads((CAMPAIGN / "sources/manifest.json").read_text())
    assert len(manifest["sources"]) == 2
    assert {source["download_sha256"] for source in manifest["sources"]} == {
        "cb17b74716e1a6ad91805285477e80667fc9fd4d6afc2ed967b60f944c572f0d",
        "cf2e115a03b5ad7a77c95f50cde1e5384daa6cfd299eefb2b0ad8ff2c1f5b236",
    }
    assert not list(CAMPAIGN.rglob("*.pdf"))


def test_all_locked_benchmarks_match_production_and_disjoint_reference() -> None:
    runner = _module("scripts/run_qualification.py", "_wp4_mr_v2_test_runner")
    reference = _module(
        "reference/sympy_reference.py", "_wp4_mr_v2_test_reference_contract"
    )
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    results, exact, symmetries = runner._benchmark_results(spec, reference)
    assert len(results) == 6
    assert exact is True
    assert symmetries is True
    assert classify_masses(("1", "1", "2500001/1000000")).sigma != Fraction(8, 27)


def test_reference_and_campaign_do_not_import_legacy_kovacic_placeholder() -> None:
    paths = (
        ROOT / "src/python/wp4_mr_v2/model.py",
        CAMPAIGN / "reference/sympy_reference.py",
        CAMPAIGN / "scripts/run_qualification.py",
    )
    for path in paths:
        source = path.read_text()
        assert "from src.python.validation.kovacic" not in source
        assert "import src.python.validation.kovacic" not in source
