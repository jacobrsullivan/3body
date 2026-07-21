#!/usr/bin/env python
"""Execute the frozen exact Morales-Ramis theorem-application qualification."""

from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import permutations
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-mr-ni-v2"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from validation_external_import import campaign_module  # noqa: E402
from src.python.wp4_mr_v2 import (  # noqa: E402
    EXCEPTIONAL_SIGMA,
    LINEAR_NVE_EXCEPTION,
    classify_masses,
    exact_fraction,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--tsygvintsev-pdf", required=True)
    parser.add_argument("--boucher-weil-pdf", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _load_common():
    return campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp4_mr_v2_campaign_common_run",
    )


def _load_reference():
    return campaign_module(
        CAMPAIGN_ROOT / "reference/sympy_reference.py",
        "_wp4_mr_v2_sympy_reference_run",
    )


def _tool_version(command: str) -> str:
    completed = subprocess.run(
        [command, "-v"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = (completed.stdout + completed.stderr).strip()
    return text.splitlines()[0]


def _pdf_text(path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-raw", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _source_text_checks(tsygvintsev: str, boucher_weil: str) -> dict[str, bool]:
    tsyg = _normalize_text(tsygvintsev)
    bw = _normalize_text(boucher_weil)
    return {
        "tsygvintsev_title": "on some exceptional cases in the integrability of the threebody problem"
        in tsyg,
        "tsygvintsev_positive_mass_model": "newtonian planar threebody problem with positive masses"
        in tsyg,
        "tsygvintsev_parabolic_lagrange_solution": "parabolic lagrangian orbit" in tsyg,
        "tsygvintsev_universal_two_integral_obstruction": "never has two additional independent first integrals meromorphic"
        in tsyg,
        "tsygvintsev_liouville_corollary": "not completely meromorphically integrable in the sense of liouvillearnold"
        in tsyg,
        "boucher_weil_title": "application of the morales ramis theorem to test the non complete integrability of the planar three body problem"
        in bw,
        "boucher_weil_positive_mass_hypothesis": "both the parameters m1 and m2 are positive real"
        in bw,
        "boucher_weil_nonzero_angular_momentum": "constant of the cinetic moment is non zero"
        in bw,
        "boucher_weil_theorem": "the planar three body problem is not completely integrable with meromorphic first integrals"
        in bw,
    }


def _pdf_xml(path: Path) -> ET.Element:
    with tempfile.TemporaryDirectory(prefix="wp4-mr-source-") as directory:
        prefix = Path(directory) / "source"
        subprocess.run(
            [
                "pdftohtml",
                "-xml",
                "-hidden",
                "-i",
                "-f",
                "1",
                "-l",
                "5",
                str(path),
                str(prefix),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return ET.fromstring(prefix.with_suffix(".xml").read_bytes())


def _glyphs(root: ET.Element, page_number: int) -> list[dict[str, int | str]]:
    page = next(
        item
        for item in root.findall("page")
        if int(item.attrib["number"]) == page_number
    )
    return [
        {
            "text": "".join(item.itertext()),
            "top": int(item.attrib["top"]),
            "left": int(item.attrib["left"]),
            "height": int(item.attrib["height"]),
        }
        for item in page.findall("text")
    ]


def _require_glyph(
    glyphs: list[dict[str, int | str]],
    *,
    text: str,
    top: int,
    left: int,
    height: int,
) -> dict[str, int | str]:
    matches = [
        glyph
        for glyph in glyphs
        if glyph == {"text": text, "top": top, "left": left, "height": height}
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"pinned source glyph not found exactly: {text!r}@({left},{top},{height})"
        )
    return matches[0]


def _source_power_notation(root: ET.Element) -> dict[str, Any]:
    page_one = _glyphs(root, 1)
    page_four = _glyphs(root, 4)
    evidence = {
        "2^3/3^3": [
            _require_glyph(page_four, text="2", top=460, left=375, height=9),
            _require_glyph(page_four, text="3", top=458, left=381, height=6),
            _require_glyph(page_four, text="3", top=473, left=375, height=9),
            _require_glyph(page_four, text="3", top=472, left=381, height=6),
        ],
        "2/3^2": [
            _require_glyph(page_one, text="/", top=678, left=440, height=16),
            _require_glyph(page_one, text="3", top=678, left=448, height=16),
            _require_glyph(page_one, text="2", top=676, left=456, height=9),
        ],
        "5/2^4": [
            _require_glyph(page_four, text="5", top=460, left=444, height=9),
            _require_glyph(page_four, text="2", top=473, left=440, height=9),
            _require_glyph(page_four, text="4", top=472, left=447, height=6),
        ],
    }
    return evidence


def _classification_payload(masses: list[str]) -> dict[str, object]:
    return classify_masses(masses).as_payload()


def _benchmark_results(
    spec: dict[str, Any], reference: Any
) -> tuple[list[dict[str, Any]], bool, bool]:
    results: list[dict[str, Any]] = []
    all_exact = True
    all_symmetries = True
    scales = (Fraction(1, 7), Fraction(2), Fraction(17, 3))
    for benchmark in spec["exact_benchmarks"]:
        masses = benchmark["masses"]
        production = _classification_payload(masses)
        independent = reference.classify_masses(masses)
        sigma_expected = benchmark["sigma"]
        sigma_passed = (
            production["sigma"] not in {str(value) for value in EXCEPTIONAL_SIGMA}
            if sigma_expected == "NOT_EXCEPTIONAL"
            else production["sigma"] == str(Fraction(sigma_expected))
        )
        passed = bool(
            production == independent
            and sigma_passed
            and production["single_additional_status"] == benchmark["single_additional"]
        )
        symmetry_passed = True
        parsed = tuple(exact_fraction(value) for value in masses)
        for permutation in permutations(parsed):
            for scale in scales:
                transformed = [str(scale * value) for value in permutation]
                transformed_production = _classification_payload(transformed)
                transformed_reference = reference.classify_masses(transformed)
                if (
                    transformed_production != transformed_reference
                    or transformed_production["sigma"] != production["sigma"]
                    or transformed_production["single_additional_status"]
                    != production["single_additional_status"]
                ):
                    symmetry_passed = False
        all_exact = all_exact and passed
        all_symmetries = all_symmetries and symmetry_passed
        results.append(
            {
                "case_id": benchmark["case_id"],
                "production": production,
                "reference": independent,
                "exact_expected_result": passed,
                "all_permutations_and_scales_exact": symmetry_passed,
            }
        )
    return results, all_exact, all_symmetries


def _catalogue_results(
    catalogue: dict[str, Any], reference: Any
) -> tuple[list[dict[str, Any]], dict[str, int | bool]]:
    rows: list[dict[str, Any]] = []
    triples: set[tuple[str, str, str]] = set()
    reference_agreement = True
    all_positive = True
    all_universally_obstructed = True
    exceptional_count = 0
    for candidate in catalogue["candidates"]:
        parameters = candidate["parameters"]
        original = [parameters[name] for name in ("m1", "m2", "m3")]
        production = _classification_payload(original)
        independent = reference.classify_masses(original)
        reference_agreement = reference_agreement and production == independent
        parsed = tuple(str(exact_fraction(value)) for value in original)
        triples.add(parsed)
        all_positive = all_positive and all(
            exact_fraction(value) > 0 for value in original
        )
        all_universally_obstructed = all_universally_obstructed and bool(
            production["universal_complete_meromorphic_integrability_obstructed"]
        )
        exceptional = production["single_additional_status"] == LINEAR_NVE_EXCEPTION
        exceptional_count += int(exceptional)
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "masses_exact": list(parsed),
                "sigma": production["sigma"],
                "universal_complete_meromorphic_integrability_obstructed": production[
                    "universal_complete_meromorphic_integrability_obstructed"
                ],
                "single_additional_status": production["single_additional_status"],
            }
        )
    summary: dict[str, int | bool] = {
        "candidate_count": len(rows),
        "distinct_mass_triple_count": len(triples),
        "exceptional_mass_triple_count": len(
            {
                tuple(row["masses_exact"])
                for row in rows
                if row["single_additional_status"] == LINEAR_NVE_EXCEPTION
            }
        ),
        "nonexceptional_mass_triple_count": len(
            {
                tuple(row["masses_exact"])
                for row in rows
                if row["single_additional_status"] != LINEAR_NVE_EXCEPTION
            }
        ),
        "exceptional_catalogue_case_count": exceptional_count,
        "production_reference_exact_agreement": reference_agreement,
        "all_project_masses_positive": all_positive,
        "all_cases_universally_obstructed": all_universally_obstructed,
    }
    return rows, summary


def main() -> None:
    args = _args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite one-shot WP4 MR result")
    common = _load_common()
    reference = _load_reference()
    spec = load_json(args.spec)
    manifest = load_json(args.source_manifest)
    catalogue = load_json(args.catalogue)
    specification_lock = common.verify_specification_lock(args.spec)
    invalidated_v1 = common.verify_invalidated_v1()
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("source_manifest_sha256") != sha256_file(args.source_manifest)
        or lock.get("catalogue_sha256") != sha256_file(args.catalogue)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
    ):
        raise RuntimeError("qualification lock does not bind the frozen inputs")
    source_paths = {
        "tsygvintsev-2007-exceptional-cases": Path(args.tsygvintsev_pdf),
        "boucher-weil-morales-ramis-threebody": Path(args.boucher_weil_pdf),
    }
    source_records = []
    source_hashes_passed = True
    for source in manifest["sources"]:
        path = source_paths[source["source_id"]]
        observed_hash = sha256_file(path)
        passed = observed_hash == source["download_sha256"]
        source_hashes_passed = source_hashes_passed and passed
        source_records.append(
            {
                "source_id": source["source_id"],
                "expected_sha256": source["download_sha256"],
                "observed_sha256": observed_hash,
                "verified": passed,
            }
        )
    if not source_hashes_passed:
        raise RuntimeError("external source PDF hash mismatch")
    tsyg_text = _pdf_text(source_paths["tsygvintsev-2007-exceptional-cases"])
    bw_text = _pdf_text(source_paths["boucher-weil-morales-ramis-threebody"])
    text_checks = _source_text_checks(tsyg_text, bw_text)
    glyph_evidence = _source_power_notation(
        _pdf_xml(source_paths["tsygvintsev-2007-exceptional-cases"])
    )
    arithmetic_checks = {
        "2^3/3^3": str(Fraction(2**3, 3**3)),
        "2/3^2": str(Fraction(2, 3**2)),
        "5/2^4": str(Fraction(5, 2**4)),
    }
    source_notation_passed = (
        arithmetic_checks == spec["published_contract"]["source_notation_checks"]
    )
    benchmarks, benchmarks_passed, symmetries_passed = _benchmark_results(
        spec, reference
    )
    catalogue_rows, catalogue_summary = _catalogue_results(catalogue, reference)
    reference_source = CAMPAIGN_ROOT / "reference/sympy_reference.py"
    reference_is_disjoint = "src.python.wp4_mr_v2" not in reference_source.read_text()
    legacy_loaded = any(name.endswith("validation.kovacic") for name in sys.modules)
    qualified_sources = (
        REPO_ROOT / "src/python/wp4_mr_v2/model.py",
        reference_source,
    )
    legacy_excluded = not legacy_loaded and all(
        "src.python.validation.kovacic" not in path.read_text()
        for path in qualified_sources
    )
    expected_count = int(spec["project_application"]["expected_candidate_count"])
    boundary_present = all(
        phrase in spec["evidence_boundary"]
        for phrase in (
            "not a new derivation",
            "spatial system",
            "non-meromorphic",
            "WP3 candidate",
            "not nonlinear first integrals",
        )
    )
    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate(
            "invalidated_v1_is_not_executable",
            int(invalidated_v1["status"] == "INVALIDATED_PREIMPLEMENTATION"),
            "==",
            1,
        ),
        make_gate(
            "source_manifest_verified",
            int(
                sha256_file(args.source_manifest)
                == spec["prerequisites"]["source_manifest_sha256"]
            ),
            "==",
            1,
        ),
        make_gate(
            "source_download_hashes_reverified", int(source_hashes_passed), "==", 1
        ),
        make_gate(
            "source_text_contracts_verified", int(all(text_checks.values())), "==", 1
        ),
        make_gate(
            "source_power_notation_transcribed_exactly",
            int(source_notation_passed and len(glyph_evidence) == 3),
            "==",
            1,
        ),
        make_gate("all_benchmarks_exact", int(benchmarks_passed), "==", 1),
        make_gate(
            "all_permutations_and_common_scales_exact", int(symmetries_passed), "==", 1
        ),
        make_gate(
            "project_candidate_count",
            int(catalogue_summary["candidate_count"]),
            "==",
            expected_count,
        ),
        make_gate(
            "production_reference_exact_agreement",
            int(
                bool(catalogue_summary["production_reference_exact_agreement"])
                and reference_is_disjoint
            ),
            "==",
            1,
        ),
        make_gate(
            "all_project_masses_positive",
            int(bool(catalogue_summary["all_project_masses_positive"])),
            "==",
            1,
        ),
        make_gate(
            "all_project_cases_universally_obstructed",
            int(bool(catalogue_summary["all_cases_universally_obstructed"])),
            "==",
            1,
        ),
        make_gate(
            "exceptional_cases_not_overinterpreted",
            int(
                all(
                    row["single_additional_status"]
                    in {LINEAR_NVE_EXCEPTION, "OBSTRUCTED"}
                    for row in catalogue_rows
                )
            ),
            "==",
            1,
        ),
        make_gate("legacy_placeholder_solver_excluded", int(legacy_excluded), "==", 1),
        make_gate("claim_boundary_present", int(boundary_present), "==", 1),
    ]
    status = "PASS" if all(gate["passed"] for gate in gates) else "FAIL"
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": status,
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "catalogue_sha256": sha256_file(args.catalogue),
        "runtime": runtime_fingerprint(),
        "external_tools": {
            "pdftotext": _tool_version("pdftotext"),
            "pdftohtml": _tool_version("pdftohtml"),
        },
        "invalidated_predecessor": {
            "status": invalidated_v1["status"],
            "assessment_sha256": sha256_file(common.INVALIDATED_V1_ASSESSMENT),
            "implementation_started": invalidated_v1["implementation_started"],
            "scientific_outputs_produced": invalidated_v1[
                "scientific_outputs_produced"
            ],
        },
        "source_records": source_records,
        "source_text_checks": text_checks,
        "source_power_notation": {
            "glyph_evidence": glyph_evidence,
            "arithmetic": arithmetic_checks,
            "passed": source_notation_passed,
        },
        "benchmark_results": benchmarks,
        "project_application": {
            **catalogue_summary,
            "case_classifications": catalogue_rows,
        },
        "independent_reference": {
            "path": reference_source.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_file(reference_source),
            "production_import_absent": reference_is_disjoint,
            "arithmetic": "SymPy Rational",
        },
        "legacy_placeholder": {
            "path": "src/python/validation/kovacic.py",
            "loaded": legacy_loaded,
            "included_in_qualification": False,
        },
        "gates": gates,
        "authorized_claim": (
            spec["decision_policy"]["AUTHORIZED_CLAIM"]
            if status == "PASS"
            else "NOT_AUTHORIZED"
        ),
        "claim_boundary": spec["evidence_boundary"],
    }
    atomic_write_json(destination, payload)
    print(
        f"{spec['campaign']}: {status}; catalogue={catalogue_summary['candidate_count']}; "
        f"distinct_masses={catalogue_summary['distinct_mass_triple_count']}; "
        f"linear_NVE_exceptions={catalogue_summary['exceptional_mass_triple_count']}"
    )


if __name__ == "__main__":
    main()
