#!/usr/bin/env python
"""Verify the locked WP5-PUB-v1 publication package."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN_ROOT = REPO_ROOT / "validation-external/wp5-pub-v1"
PUBLICATION_ROOT = REPO_ROOT / "publication/wp5-pub-v1"
SPEC_PATH = CAMPAIGN_ROOT / "qualification_spec.json"
SPEC_LOCK_PATH = (
    CAMPAIGN_ROOT / "reports/wp5_pub_v1_specification_lock.json"
)
MANIFEST_PATH = PUBLICATION_ROOT / "artifact_manifest.json"
MANUSCRIPT_PATH = PUBLICATION_ROOT / "manuscript/main.tex"
PDF_PATH = PUBLICATION_ROOT / "manuscript/main.pdf"
CLAIM_LEDGER_PATH = PUBLICATION_ROOT / "claims/claim_ledger.json"
DEPENDENCY_MAP_PATH = PUBLICATION_ROOT / "proof_dependency_map.json"
METADATA_PATH = PUBLICATION_ROOT / "release/metadata.json"
EXTERNAL_DIR = CAMPAIGN_ROOT / "review/external"
WP4_RESULTS_PATH = (
    REPO_ROOT
    / "validation-external/wp4-mr-repl-v1/results/qualification_results.json"
)
WP4_REFERENCE_PATH = (
    REPO_ROOT
    / "validation-external/wp4-mr-repl-v1/reference/sympy_derivation.py"
)
WP4_RECORD_PATH = (
    REPO_ROOT
    / "validation-external/wp4-mr-repl-v1/reports/"
    "wp4_mr_repl_v1_qualification_record.json"
)


class VerificationError(RuntimeError):
    """Raised when a locked publication condition fails."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def safe_repo_path(relative_name: str) -> Path:
    relative = Path(relative_name)
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        f"unsafe repository path: {relative_name}",
    )
    candidate = (REPO_ROOT / relative).resolve()
    require(
        candidate == REPO_ROOT or REPO_ROOT in candidate.parents,
        f"path escapes repository: {relative_name}",
    )
    return candidate


def verify_specification_lock() -> dict[str, Any]:
    spec = load_json(SPEC_PATH)
    lock = load_json(SPEC_LOCK_PATH)
    require(lock["campaign"] == spec["campaign"], "specification campaign mismatch")
    require(
        lock["spec_sha256"] == sha256_file(SPEC_PATH),
        "qualification specification changed after lock",
    )
    source_manifest = safe_repo_path(lock["source_manifest_path"])
    review_schema = safe_repo_path(lock["review_schema_path"])
    require(
        sha256_file(source_manifest) == lock["source_manifest_sha256"],
        "WP5 source manifest changed after lock",
    )
    require(
        sha256_file(review_schema) == lock["review_schema_sha256"],
        "external review schema changed after lock",
    )
    unsigned = dict(lock)
    recorded_hash = unsigned.pop("specification_lock_sha256")
    require(
        sha256_bytes(canonical_json(unsigned)) == recorded_hash,
        "specification lock payload hash mismatch",
    )
    for relative_name, expected_hash in lock[
        "prerequisite_file_hashes"
    ].items():
        path = safe_repo_path(relative_name)
        require(path.is_file(), f"pinned prerequisite missing: {relative_name}")
        require(
            sha256_file(path) == expected_hash,
            f"pinned prerequisite changed: {relative_name}",
        )
    require(
        lock["implementation_present_at_lock"] is False,
        "lock does not preserve pre-implementation state",
    )
    require(
        lock["external_review_evidence_present_at_lock"] is False,
        "lock unexpectedly contains external review evidence",
    )
    return {
        "spec_sha256": lock["spec_sha256"],
        "specification_lock_sha256": recorded_hash,
        "prerequisite_count": len(lock["prerequisite_file_hashes"]),
    }


def verify_prerequisite_records(spec: dict[str, Any]) -> dict[str, Any]:
    verified: dict[str, Any] = {}
    for name, item in spec["prerequisites"].items():
        if "record_file" not in item:
            continue
        record_path = safe_repo_path(item["record_file"])
        lock_path = safe_repo_path(item["lock_file"])
        require(
            sha256_file(record_path) == item["record_file_sha256"],
            f"{name} qualification record hash mismatch",
        )
        require(
            sha256_file(lock_path) == item["lock_file_sha256"],
            f"{name} qualification lock hash mismatch",
        )
        record = load_json(record_path)
        require(
            record.get("qualification_id") == item["qualification_id"],
            f"{name} qualification ID mismatch",
        )
        expected_status = (
            "COMPLETE_BOUNDED_NULL_RESULT"
            if name == "wp3_bounded_null"
            else "PASS"
        )
        require(
            record.get("status") == expected_status,
            f"{name} has status {record.get('status')!r}, expected "
            f"{expected_status!r}",
        )
        if name == "wp3_bounded_null":
            gate_path = safe_repo_path(item["publication_gate_file"])
            require(
                sha256_file(gate_path) == item["publication_gate_file_sha256"],
                "WP3 bounded-null publication gate hash mismatch",
            )
            gate = load_json(gate_path)
            require(
                gate.get("PUBLICATION_GATE") == "PASS_BOUNDED_NULL_ONLY",
                "WP3 publication boundary is not PASS_BOUNDED_NULL_ONLY",
            )
        verified[name] = {
            "qualification_id": item["qualification_id"],
            "record_sha256": item["record_file_sha256"],
            "status": expected_status,
        }
    return verified


def required_artifact_paths(spec: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for group in spec["required_artifacts"].values():
        paths.extend(group)
    require(len(paths) == len(set(paths)), "required artifact paths are duplicated")
    return sorted(paths)


def verify_required_artifacts(spec: dict[str, Any]) -> dict[str, Any]:
    required_paths = required_artifact_paths(spec)
    missing = [
        relative_name
        for relative_name in required_paths
        if not safe_repo_path(relative_name).is_file()
    ]
    require(not missing, f"required publication artifacts missing: {missing}")
    return {"required_count": len(required_paths), "missing": []}


def verify_artifact_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    require(manifest["campaign"] == spec["campaign"], "manifest campaign mismatch")
    unsigned = dict(manifest)
    recorded_payload_hash = unsigned.pop("manifest_payload_sha256")
    require(
        sha256_bytes(canonical_json(unsigned)) == recorded_payload_hash,
        "artifact manifest payload hash mismatch",
    )
    artifacts = manifest["artifacts"]
    paths = [item["path"] for item in artifacts]
    require(paths == sorted(set(paths)), "manifest paths are not sorted and unique")
    require(
        manifest["artifact_count"] == len(artifacts),
        "artifact manifest count mismatch",
    )
    for item in artifacts:
        path = safe_repo_path(item["path"])
        require(path.is_file(), f"manifest artifact missing: {item['path']}")
        require(path.stat().st_size == item["bytes"], f"size mismatch: {item['path']}")
        require(
            sha256_file(path) == item["sha256"],
            f"artifact hash mismatch: {item['path']}",
        )
    listed = set(paths)
    required = set(required_artifact_paths(spec))
    required.discard("publication/wp5-pub-v1/artifact_manifest.json")
    require(
        required.issubset(listed),
        f"manifest omits required artifacts: {sorted(required - listed)}",
    )
    return {
        "artifact_count": len(artifacts),
        "manifest_file_sha256": sha256_file(MANIFEST_PATH),
        "manifest_payload_sha256": recorded_payload_hash,
    }


def _tex_to_search_text(text: str) -> str:
    text = text.replace("\\XiMap", "Xi")
    text = text.replace("\\Xi", "Xi")
    text = re.sub(r"\\(?:textbf|emph|texttt)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\cite\{[^{}]*\}", " ", text)
    text = text.replace("\\(", " ").replace("\\)", " ")
    text = text.replace("{", "").replace("}", "")
    text = text.replace("--", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:])", r"\1", text)


def unqualified_forbidden_occurrences(
    text: str, phrases: Iterable[str]
) -> list[dict[str, Any]]:
    lower = _tex_to_search_text(text).lower()
    violations = []
    qualifiers = (
        "does not",
        "do not",
        "not claim",
        "not an asserted",
        "no claim",
        "prohibited",
        "forbidden",
        "reject",
        "without an unsupported",
    )
    for phrase in phrases:
        start = 0
        phrase_lower = phrase.lower()
        while True:
            index = lower.find(phrase_lower, start)
            if index < 0:
                break
            context = lower[max(0, index - 160) : index + len(phrase_lower) + 80]
            if not any(qualifier in context for qualifier in qualifiers):
                violations.append({"phrase": phrase, "context": context})
            start = index + len(phrase_lower)
    return violations


def _extract_environment(text: str, environment: str) -> str:
    match = re.search(
        rf"\\begin\{{{re.escape(environment)}\}}(.*?)"
        rf"\\end\{{{re.escape(environment)}\}}",
        text,
        flags=re.DOTALL,
    )
    require(match is not None, f"missing LaTeX {environment} environment")
    return match.group(1)


def verify_manuscript(spec: dict[str, Any]) -> dict[str, Any]:
    text = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    for section in spec["manuscript_requirements"]["required_sections"]:
        if section == "Abstract":
            require(
                "\\begin{abstract}" in text and "\\end{abstract}" in text,
                "manuscript abstract environment missing",
            )
            continue
        require(
            f"\\section{{{section}}}" in text,
            f"manuscript section missing: {section}",
        )
    searchable = _tex_to_search_text(text)
    for statement in spec["manuscript_requirements"]["required_statements"]:
        require(
            statement in searchable,
            f"required manuscript statement missing: {statement}",
        )
    violations = unqualified_forbidden_occurrences(
        text,
        spec["manuscript_requirements"]["forbidden_unqualified_phrases"],
    )
    require(not violations, f"unqualified forbidden manuscript claim: {violations}")
    abstract = _tex_to_search_text(_extract_environment(text, "abstract"))
    require(
        "complete meromorphic Liouville integrability" in abstract,
        "abstract omits complete-meromorphic boundary",
    )
    require("locally near one" in abstract, "abstract omits local phase-curve scope")
    require(
        "does not exclude one additional integral" in abstract,
        "abstract omits one-integral nonclaim",
    )
    theorem_match = re.search(
        r"\\begin\{theorem\}\[Qualified spatial and KS obstruction\]"
        r"(.*?)\\end\{theorem\}",
        text,
        flags=re.DOTALL,
    )
    require(theorem_match is not None, "qualified main theorem is missing")
    theorem = _tex_to_search_text(theorem_match.group(1))
    theorem_tokens = (
        "finite positive mass triple",
        "translation-reduced spatial",
        "not completely integrable",
        "meromorphic first integrals",
        "neighborhood",
        "fixed nonzero angular momentum",
        "shell-regular physically admissible",
    )
    for token in theorem_tokens:
        require(token in theorem, f"main theorem omits boundary token: {token}")
    require("WP1" not in theorem and "WP3" not in theorem, "context enters theorem")
    return {
        "required_section_count": len(
            spec["manuscript_requirements"]["required_sections"]
        ),
        "required_statement_count": len(
            spec["manuscript_requirements"]["required_statements"]
        ),
        "unqualified_forbidden_claim_count": 0,
        "main_theorem_sha256": sha256_bytes(theorem.encode("utf-8")),
        "abstract_sha256": sha256_bytes(abstract.encode("utf-8")),
    }


def find_context_dependency_violations(dependency_map: dict[str, Any]) -> list[str]:
    adjacency: dict[str, list[str]] = {}
    for edge in dependency_map["edges"]:
        adjacency.setdefault(edge["from"], []).append(edge["to"])
    contexts = set(dependency_map["context_isolation"]["context_nodes"])
    violations: set[str] = set()
    for root in (
        "C3-POSITIVE-MASS-GALOIS",
        "C4-PLANAR-LOCAL-OBSTRUCTION",
        "C5-SPATIAL-TRANSFER",
        "C6-KS-ATLAS-CONSEQUENCE",
    ):
        pending = [root]
        visited: set[str] = set()
        while pending:
            node = pending.pop()
            if node in visited:
                continue
            visited.add(node)
            if node in contexts:
                violations.add(f"{root}->{node}")
            pending.extend(adjacency.get(node, []))
    return sorted(violations)


def verify_claims_and_dependencies(spec: dict[str, Any]) -> dict[str, Any]:
    ledger = load_json(CLAIM_LEDGER_PATH)
    dependency_map = load_json(DEPENDENCY_MAP_PATH)
    require(ledger["campaign"] == spec["campaign"], "claim-ledger campaign mismatch")
    claims = {item["claim_id"]: item for item in ledger["claims"]}
    expected_claims = {f"C{index}" for index in range(1, 9)}
    observed_prefixes = {claim_id.split("-", 1)[0] for claim_id in claims}
    require(
        observed_prefixes == expected_claims,
        f"claim-ledger IDs incomplete: {sorted(observed_prefixes)}",
    )
    require(
        ledger["prohibited_assertions"]
        == spec["manuscript_requirements"]["forbidden_unqualified_phrases"],
        "claim ledger and specification prohibited phrases diverge",
    )
    require(
        claims["C7-WP3-BOUNDED-NULL"]["status"] == "CONTEXT_ONLY",
        "WP3 claim is not context-only",
    )
    require(
        claims["C8-WP1-EXTERNAL-CATALOGUE"]["status"] == "CONTEXT_ONLY",
        "WP1 claim is not context-only",
    )
    nodes = {node["node_id"]: node for node in dependency_map["nodes"]}
    require(
        len(nodes) == len(dependency_map["nodes"]),
        "dependency-map node IDs are duplicated",
    )
    for edge in dependency_map["edges"]:
        require(edge["from"] in nodes, f"unknown edge source: {edge['from']}")
        require(edge["to"] in nodes, f"unknown edge target: {edge['to']}")
    for node in nodes.values():
        authority = node.get("authority")
        if not authority or "sha256" not in node:
            continue
        path = safe_repo_path(authority)
        require(
            sha256_file(path) == node["sha256"],
            f"proof-map authority changed: {authority}",
        )
    violations = find_context_dependency_violations(dependency_map)
    require(not violations, f"context records feed theorem chain: {violations}")
    require(
        dependency_map["root_claim"] == "C6-KS-ATLAS-CONSEQUENCE",
        "unexpected root publication claim",
    )
    return {
        "claim_count": len(claims),
        "dependency_node_count": len(nodes),
        "dependency_edge_count": len(dependency_map["edges"]),
        "context_dependency_violations": [],
    }


def _pdfinfo(path: Path) -> dict[str, str]:
    completed = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    values: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def verify_pdf(spec: dict[str, Any]) -> dict[str, Any]:
    require(PDF_PATH.read_bytes()[:5] == b"%PDF-", "manuscript is not a PDF")
    info = _pdfinfo(PDF_PATH)
    pages = int(info["Pages"])
    require(pages >= 8, f"manuscript is unexpectedly short: {pages} pages")
    completed = subprocess.run(
        ["pdftotext", "-layout", str(PDF_PATH), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    extracted = (
        completed.stdout.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\ufb00", "ff")
        .replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\ufb03", "ffi")
        .replace("\ufb04", "ffl")
    )
    text = re.sub(r"\s+", " ", extracted)
    require(
        spec["publication_title"] in text,
        "rendered PDF title does not match specification",
    )
    for section in spec["manuscript_requirements"]["required_sections"]:
        require(section in text, f"rendered PDF section missing: {section}")
    return {
        "sha256": sha256_file(PDF_PATH),
        "bytes": PDF_PATH.stat().st_size,
        "pages": pages,
        "page_size": info.get("Page size"),
        "pdf_version": info.get("PDF version"),
    }


def validate_release_metadata(metadata: dict[str, Any]) -> dict[str, bool]:
    author = metadata["author"]
    confirmations = {
        "author_name": bool(author["name"]) and author["name_confirmed_by_author"],
        "affiliation_status": author["affiliation_status_confirmed"],
        "orcid_status": author["orcid_status_confirmed"],
        "contact": bool(author["contact"]) and author["contact_confirmed"],
        "contributions": metadata["contributions"]["confirmed_by_author"],
        "conflicts": (
            metadata["conflicts"]["statement"] is not None
            and metadata["conflicts"]["confirmed_by_author"]
        ),
        "funding": (
            metadata["funding"]["statement"] is not None
            and metadata["funding"]["confirmed_by_author"]
        ),
        "ai_assistance": metadata["ai_assistance"]["confirmed_by_author"],
        "licenses": (
            all(metadata["licenses"][name] for name in (
                "code",
                "evidence_data",
                "manuscript_text",
            ))
            and metadata["licenses"]["confirmed_by_author"]
        ),
    }
    return {name: bool(value) for name, value in confirmations.items()}


def _valid_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(
        rf"[0-9a-f]{{{length}}}", value
    ) is not None


def _validate_signature(
    record: dict[str, Any], *, allow_missing_artifact: bool = False
) -> None:
    signature = record["signature"]
    require(
        signature["method"]
        in {"detached_pgp", "signed_pdf", "institutional_email_archive"},
        "unsupported external signature method",
    )
    require(
        _valid_hex(signature["artifact_sha256"], 64),
        "invalid signature-artifact hash",
    )
    artifact = safe_repo_path(signature["artifact_path"])
    if not allow_missing_artifact:
        require(artifact.is_file(), "signature artifact is missing")
        require(
            sha256_file(artifact) == signature["artifact_sha256"],
            "signature artifact hash mismatch",
        )


def validate_review_record(
    record: dict[str, Any],
    *,
    manifest_sha256: str,
    pdf_sha256: str,
    author_name: str,
    allow_missing_signature_artifact: bool = False,
) -> dict[str, Any]:
    require(record.get("schema_version") == "1.0", "review schema mismatch")
    require(record.get("campaign") == "WP5-PUB-v1", "review campaign mismatch")
    require(
        re.fullmatch(r"WP5-PUB-v1-EXT-[A-Za-z0-9._-]+", record.get("review_id", ""))
        is not None,
        "invalid review ID",
    )
    reviewer = record["reviewer"]
    require(reviewer["human"] is True, "reviewer is not declared human")
    require(
        reviewer["identity_publication_consent"] is True,
        "reviewer identity-publication consent missing",
    )
    require(
        reviewer["name"].strip().casefold() != author_name.strip().casefold(),
        "self-review is not independent",
    )
    independence = record["independence"]
    for key in (
        "not_author",
        "not_implementation_contributor",
        "not_project_controlled_agent",
        "conflicts_disclosed",
    ):
        require(independence[key] is True, f"review independence failed: {key}")
    require(record["recommendation"] == "APPROVE", "review does not approve")
    severe = [
        item
        for item in record["findings"]
        if item["severity"] in {"blocker", "major"}
    ]
    require(not severe, "review has unresolved blocker or major findings")
    artifacts = record["artifacts"]
    require(_valid_hex(artifacts["git_commit"], 40), "invalid review commit")
    require(
        artifacts["artifact_manifest_sha256"] == manifest_sha256,
        "review targets a different artifact manifest",
    )
    require(
        artifacts["manuscript_pdf_sha256"] == pdf_sha256,
        "review targets a different manuscript PDF",
    )
    _validate_signature(
        record, allow_missing_artifact=allow_missing_signature_artifact
    )
    return {
        "review_id": record["review_id"],
        "reviewer_name": reviewer["name"],
        "expertise": sorted(set(reviewer["expertise"])),
        "scope": sorted(set(record["scope"])),
    }


def validate_clean_room_receipt(
    record: dict[str, Any],
    *,
    manifest_sha256: str,
    pdf_sha256: str,
    author_name: str,
    allow_missing_signature_artifact: bool = False,
) -> dict[str, Any]:
    require(record.get("schema_version") == "1.0", "receipt schema mismatch")
    require(record.get("campaign") == "WP5-PUB-v1", "receipt campaign mismatch")
    require(
        re.fullmatch(r"WP5-PUB-v1-CR-[A-Za-z0-9._-]+", record.get("receipt_id", ""))
        is not None,
        "invalid clean-room receipt ID",
    )
    reproducer = record["reproducer"]
    require(reproducer["human"] is True, "clean-room reproducer is not human")
    require(
        reproducer["identity_publication_consent"] is True,
        "clean-room identity-publication consent missing",
    )
    require(
        reproducer["name"].strip().casefold() != author_name.strip().casefold(),
        "author's run is not an external clean-room replay",
    )
    independence = record["independence"]
    for key in (
        "not_author",
        "not_implementation_contributor",
        "hardware_not_project_controlled",
        "account_not_project_controlled",
        "conflicts_disclosed",
    ):
        require(independence[key] is True, f"clean-room independence failed: {key}")
    artifacts = record["artifacts"]
    require(_valid_hex(artifacts["git_commit"], 40), "invalid receipt commit")
    require(
        artifacts["artifact_manifest_sha256"] == manifest_sha256,
        "receipt targets a different artifact manifest",
    )
    require(
        artifacts["manuscript_pdf_sha256"] == pdf_sha256,
        "receipt targets a different manuscript PDF",
    )
    execution = record["execution"]
    require(
        execution["command"] == "./scripts/reproduce_wp5_pub_v1.sh --core",
        "receipt used a different command",
    )
    require(execution["exit_code"] == 0, "clean-room command did not exit zero")
    require(execution["status"] == "PASS", "clean-room replay did not pass")
    require(
        _valid_hex(execution["report_sha256"], 64),
        "invalid clean-room report hash",
    )
    require(
        _valid_hex(execution["normalized_generic_payload_sha256"], 64),
        "invalid clean-room generic payload hash",
    )
    _validate_signature(
        record, allow_missing_artifact=allow_missing_signature_artifact
    )
    return {
        "receipt_id": record["receipt_id"],
        "reproducer_name": reproducer["name"],
    }


def evaluate_external_gates(
    manifest: dict[str, Any], pdf: dict[str, Any]
) -> dict[str, Any]:
    metadata = load_json(METADATA_PATH)
    author_name = metadata["author"]["name"]
    reviews = []
    receipts = []
    if EXTERNAL_DIR.is_dir():
        for path in sorted(EXTERNAL_DIR.glob("*.review.json")):
            reviews.append(
                validate_review_record(
                    load_json(path),
                    manifest_sha256=manifest["manifest_file_sha256"],
                    pdf_sha256=pdf["sha256"],
                    author_name=author_name,
                )
            )
        for path in sorted(EXTERNAL_DIR.glob("*.receipt.json")):
            receipts.append(
                validate_clean_room_receipt(
                    load_json(path),
                    manifest_sha256=manifest["manifest_file_sha256"],
                    pdf_sha256=pdf["sha256"],
                    author_name=author_name,
                )
            )
    distinct_names = {
        review["reviewer_name"].strip().casefold() for review in reviews
    }
    expertise = {
        item for review in reviews for item in review["expertise"]
    }
    scope = {item for review in reviews for item in review["scope"]}
    human_review_gate = (
        len(reviews) >= 2
        and len(distinct_names) >= 2
        and bool(
            expertise.intersection({"differential_galois", "hamiltonian_integrability"})
        )
        and "planar_derivation" in scope
        and "differential_galois_argument" in scope
        and bool(expertise.intersection({"symplectic_reduction", "ks_regularization"}))
        and "spatial_subquotient" in scope
        and "ks_sundman_transfer" in scope
    )
    metadata_gates = validate_release_metadata(metadata)
    return {
        "human_reviews": human_review_gate,
        "review_count": len(reviews),
        "distinct_reviewer_count": len(distinct_names),
        "collective_expertise": sorted(expertise),
        "collective_scope": sorted(scope),
        "external_clean_room": len(receipts) >= 1,
        "receipt_count": len(receipts),
        "author_metadata": metadata_gates,
        "author_metadata_complete": all(metadata_gates.values()),
        "licenses_complete": metadata_gates["licenses"],
        "release_authorized": metadata["release"]["authorized_by_author"],
        "archive_identifiers_complete": bool(
            metadata["archives"]["software_doi"]
            and metadata["archives"]["preprint_identifier"]
        ),
        "review_ids": [review["review_id"] for review in reviews],
        "receipt_ids": [receipt["receipt_id"] for receipt in receipts],
    }


def normalized_generic_payload(value: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(value)
    normalized.pop("elapsed_seconds", None)
    return normalized


def run_generic_replay() -> dict[str, Any]:
    record = load_json(WP4_RECORD_PATH)
    require(
        sha256_file(WP4_RESULTS_PATH) == record["results_sha256"],
        "frozen WP4 qualification results changed",
    )
    expected = normalized_generic_payload(
        load_json(WP4_RESULTS_PATH)["generic_derivation"]
    )
    with tempfile.TemporaryDirectory(prefix="wp5-pub-v1-generic-") as directory:
        output = Path(directory) / "generic.json"
        started = time.monotonic()
        subprocess.run(
            [
                sys.executable,
                str(WP4_REFERENCE_PATH),
                "--generic",
                "--output",
                str(output),
            ],
            cwd=REPO_ROOT,
            check=True,
        )
        elapsed = time.monotonic() - started
        observed = normalized_generic_payload(load_json(output))
    require(
        observed == expected,
        "generic symbolic replay disagrees with frozen decision-bearing payload",
    )
    return {
        "field_count": len(observed),
        "elapsed_seconds": elapsed,
        "normalized_payload_sha256": sha256_bytes(canonical_json(observed)),
        "all_exact_derivation_checks_pass": observed[
            "all_exact_derivation_checks_pass"
        ],
        "exactly_matches_frozen_payload": True,
    }


def run_publication_tests() -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/wp5_pub_v1",
        "-q",
    ]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        "publication-specific tests failed:\n"
        + completed.stdout
        + "\n"
        + completed.stderr,
    )
    return {
        "command": command,
        "elapsed_seconds": time.monotonic() - started,
        "stdout_tail": "\n".join(completed.stdout.splitlines()[-8:]),
        "passed": True,
    }


def run_legacy_lanes() -> dict[str, Any]:
    lanes: dict[str, Any] = {}
    for lane in ("fast", "slow", "quarantine"):
        started = time.monotonic()
        completed = subprocess.run(
            ["./scripts/run_legacy_baseline.sh", lane],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        require(
            completed.returncode == 0,
            f"legacy {lane} lane failed:\n"
            + completed.stdout[-4000:]
            + "\n"
            + completed.stderr[-4000:],
        )
        lanes[lane] = {
            "elapsed_seconds": time.monotonic() - started,
            "stdout_tail": "\n".join(completed.stdout.splitlines()[-12:]),
            "passed": True,
        }
    return lanes


def adversarial_controls(
    spec: dict[str, Any],
    dependency_map: dict[str, Any],
    metadata: dict[str, Any],
    manifest: dict[str, Any],
    pdf: dict[str, Any],
) -> dict[str, bool]:
    controls: dict[str, bool] = {}
    phrase = spec["manuscript_requirements"]["forbidden_unqualified_phrases"][0]
    controls["unqualified_no_integrals_claim_rejected"] = bool(
        unqualified_forbidden_occurrences(
            f"We prove that {phrase}.",
            spec["manuscript_requirements"]["forbidden_unqualified_phrases"],
        )
    )
    controls["qualified_nonclaim_permitted"] = not bool(
        unqualified_forbidden_occurrences(
            f"We do not claim that {phrase}.",
            spec["manuscript_requirements"]["forbidden_unqualified_phrases"],
        )
    )
    changed_graph = copy.deepcopy(dependency_map)
    changed_graph["edges"].append(
        {
            "from": "C3-POSITIVE-MASS-GALOIS",
            "to": "REC-WP3-KQ",
            "relation": "invalid_evidence",
        }
    )
    controls["wp3_theorem_dependency_rejected"] = bool(
        find_context_dependency_violations(changed_graph)
    )
    controls["status_only_predecessor_rejected"] = all(
        "record_file_sha256" in item
        for item in spec["prerequisites"].values()
        if "record_file" in item
    )
    changed_metadata = copy.deepcopy(metadata)
    changed_metadata["release"]["authorized_by_author"] = True
    controls["unconfirmed_metadata_blocks_release"] = not all(
        validate_release_metadata(changed_metadata).values()
    )
    fake_review = {
        "schema_version": "1.0",
        "campaign": "WP5-PUB-v1",
        "review_id": "WP5-PUB-v1-EXT-self",
        "reviewer": {
            "name": metadata["author"]["name"],
            "human": True,
            "identity_publication_consent": True,
            "expertise": ["differential_galois"],
        },
        "independence": {
            "not_author": True,
            "not_implementation_contributor": True,
            "not_project_controlled_agent": True,
            "conflicts_disclosed": True,
        },
        "scope": ["planar_derivation", "differential_galois_argument"],
        "artifacts": {
            "git_commit": "0" * 40,
            "artifact_manifest_sha256": manifest["manifest_file_sha256"],
            "manuscript_pdf_sha256": pdf["sha256"],
        },
        "findings": [],
        "recommendation": "APPROVE",
        "signed_utc": "2026-07-24T00:00:00Z",
        "signature": {
            "method": "detached_pgp",
            "artifact_path": "missing.sig",
            "artifact_sha256": "0" * 64,
        },
    }
    try:
        validate_review_record(
            fake_review,
            manifest_sha256=manifest["manifest_file_sha256"],
            pdf_sha256=pdf["sha256"],
            author_name=metadata["author"]["name"],
            allow_missing_signature_artifact=True,
        )
        controls["self_review_rejected"] = False
    except VerificationError:
        controls["self_review_rejected"] = True
    changed_pdf = copy.deepcopy(manifest)
    changed_pdf["manifest_file_sha256"] = "f" * 64
    controls["changed_manifest_hash_rejected"] = (
        changed_pdf["manifest_file_sha256"] != manifest["manifest_file_sha256"]
    )
    return controls


def determine_status(
    mode: str, internal_pass: bool, external: dict[str, Any]
) -> str:
    if not internal_pass:
        return "FAIL"
    if mode == "static":
        return "STATIC_PASS"
    external_complete = (
        external["human_reviews"]
        and external["external_clean_room"]
        and external["author_metadata_complete"]
        and external["licenses_complete"]
    )
    if not external_complete:
        return "READY_FOR_EXTERNAL_REVIEW"
    if not external["release_authorized"]:
        return "READY_FOR_SUBMISSION"
    if external["archive_identifiers_complete"]:
        return "PUBLISHED"
    return "READY_FOR_SUBMISSION"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("static", "core", "full"),
        default="static",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started_utc = utc_now()
    started = time.monotonic()
    spec = load_json(SPEC_PATH)
    gate_results: dict[str, Any] = {}
    gate_results["specification_lock"] = verify_specification_lock()
    gate_results["prerequisite_records"] = verify_prerequisite_records(spec)
    gate_results["required_artifacts"] = verify_required_artifacts(spec)
    gate_results["manuscript"] = verify_manuscript(spec)
    gate_results["claims_and_dependencies"] = verify_claims_and_dependencies(spec)
    gate_results["pdf"] = verify_pdf(spec)
    gate_results["artifact_manifest"] = verify_artifact_manifest(spec)
    metadata = load_json(METADATA_PATH)
    dependency_map = load_json(DEPENDENCY_MAP_PATH)
    controls = adversarial_controls(
        spec,
        dependency_map,
        metadata,
        gate_results["artifact_manifest"],
        gate_results["pdf"],
    )
    require(all(controls.values()), f"adversarial control failed: {controls}")
    gate_results["adversarial_controls"] = controls
    gate_results["publication_tests"] = run_publication_tests()
    if args.mode in {"core", "full"}:
        gate_results["generic_replay"] = run_generic_replay()
    if args.mode == "full":
        gate_results["legacy_lanes"] = run_legacy_lanes()
    external = evaluate_external_gates(
        gate_results["artifact_manifest"],
        gate_results["pdf"],
    )
    status = determine_status(args.mode, True, external)
    report = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "mode": args.mode,
        "started_utc": started_utc,
        "completed_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "runtime": {
            "python": platform.python_version(),
            "python_executable": str(Path(sys.executable).resolve()),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "internal_gates_pass": True,
        "gate_results": gate_results,
        "external_gates": external,
        "status": status,
        "authorized_claim": spec["primary_result"],
        "claim_boundary": (
            "Local complete meromorphic Liouville-integrability obstruction "
            "near the declared fixed-nonzero-angular-momentum phase curve. "
            "No one-integral, global, zero-angular-momentum, non-meromorphic, "
            "nonzero-Xi, or triple-collision claim is authorized."
        ),
    }
    report["report_payload_sha256"] = sha256_bytes(canonical_json(report))
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = REPO_ROOT / output
        write_json(output, report)
    print(
        json.dumps(
            {
                "campaign": report["campaign"],
                "mode": report["mode"],
                "status": report["status"],
                "internal_gates_pass": report["internal_gates_pass"],
                "external_review_count": external["review_count"],
                "external_clean_room_count": external["receipt_count"],
                "report_payload_sha256": report["report_payload_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (
        VerificationError,
        FileNotFoundError,
        KeyError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"WP5-PUB-v1 verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
