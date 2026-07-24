"""Adversarial and structural tests for WP5-PUB-v1."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "validation-external/wp5-pub-v1/scripts/verify_package.py"
)
SPEC = importlib.util.spec_from_file_location("wp5_pub_v1_verify", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


def load(relative_name: str):
    with (REPO_ROOT / relative_name).open(encoding="utf-8") as stream:
        return json.load(stream)


def test_specification_lock_and_prerequisites_verify() -> None:
    result = verify.verify_specification_lock()
    assert result["prerequisite_count"] >= 18


def test_claim_graph_keeps_context_out_of_theorem_chain() -> None:
    dependency_map = load(
        "publication/wp5-pub-v1/proof_dependency_map.json"
    )
    assert verify.find_context_dependency_violations(dependency_map) == []


def test_wp3_dependency_mutation_is_rejected() -> None:
    dependency_map = load(
        "publication/wp5-pub-v1/proof_dependency_map.json"
    )
    dependency_map["edges"].append(
        {
            "from": "C4-PLANAR-LOCAL-OBSTRUCTION",
            "to": "REC-WP3-KQ",
            "relation": "invalid_evidence",
        }
    )
    assert verify.find_context_dependency_violations(dependency_map)


@pytest.mark.parametrize(
    "phrase",
    [
        "the three-body problem has no integrals",
        "no additional integral exists",
        "global nonintegrability of the three-body problem",
        "complete search of all possible integrals",
        "first proof",
        "novel proof",
        "solves the three-body problem",
    ],
)
def test_unqualified_overclaims_are_rejected(phrase: str) -> None:
    assert verify.unqualified_forbidden_occurrences(
        f"Our theorem establishes {phrase}.", [phrase]
    )


def test_explicit_nonclaim_is_not_an_overclaim() -> None:
    phrase = "the three-body problem has no integrals"
    assert not verify.unqualified_forbidden_occurrences(
        f"We do not claim that {phrase}.", [phrase]
    )


def test_unconfirmed_author_metadata_fails_closed() -> None:
    metadata = load("publication/wp5-pub-v1/release/metadata.json")
    gates = verify.validate_release_metadata(metadata)
    assert not all(gates.values())
    assert not gates["licenses"]
    assert not gates["ai_assistance"]


def _fake_review(
    *,
    reviewer_name: str,
    author_name: str,
    manifest_sha256: str,
    pdf_sha256: str,
) -> dict:
    return {
        "schema_version": "1.0",
        "campaign": "WP5-PUB-v1",
        "review_id": "WP5-PUB-v1-EXT-test",
        "reviewer": {
            "name": reviewer_name,
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
            "git_commit": "1" * 40,
            "artifact_manifest_sha256": manifest_sha256,
            "manuscript_pdf_sha256": pdf_sha256,
        },
        "findings": [],
        "recommendation": "APPROVE",
        "signed_utc": "2026-07-24T00:00:00Z",
        "signature": {
            "method": "detached_pgp",
            "artifact_path": "external-review-test.sig",
            "artifact_sha256": "2" * 64,
        },
        "_author_name_for_test": author_name,
    }


def test_self_review_is_rejected() -> None:
    review = _fake_review(
        reviewer_name="Jacob Sullivan",
        author_name="Jacob Sullivan",
        manifest_sha256="3" * 64,
        pdf_sha256="4" * 64,
    )
    review.pop("_author_name_for_test")
    with pytest.raises(verify.VerificationError, match="self-review"):
        verify.validate_review_record(
            review,
            manifest_sha256="3" * 64,
            pdf_sha256="4" * 64,
            author_name="Jacob Sullivan",
            allow_missing_signature_artifact=True,
        )


def test_major_finding_prevents_approval() -> None:
    review = _fake_review(
        reviewer_name="Independent Reviewer",
        author_name="Jacob Sullivan",
        manifest_sha256="3" * 64,
        pdf_sha256="4" * 64,
    )
    review.pop("_author_name_for_test")
    review["findings"].append(
        {
            "finding_id": "M1",
            "severity": "major",
            "location": "Theorem 4",
            "description": "The transfer premise is incomplete.",
        }
    )
    with pytest.raises(verify.VerificationError, match="major"):
        verify.validate_review_record(
            review,
            manifest_sha256="3" * 64,
            pdf_sha256="4" * 64,
            author_name="Jacob Sullivan",
            allow_missing_signature_artifact=True,
        )


def test_changed_review_target_is_rejected() -> None:
    review = _fake_review(
        reviewer_name="Independent Reviewer",
        author_name="Jacob Sullivan",
        manifest_sha256="3" * 64,
        pdf_sha256="4" * 64,
    )
    review.pop("_author_name_for_test")
    changed = copy.deepcopy(review)
    changed["artifacts"]["artifact_manifest_sha256"] = "5" * 64
    with pytest.raises(verify.VerificationError, match="different artifact"):
        verify.validate_review_record(
            changed,
            manifest_sha256="3" * 64,
            pdf_sha256="4" * 64,
            author_name="Jacob Sullivan",
            allow_missing_signature_artifact=True,
        )
