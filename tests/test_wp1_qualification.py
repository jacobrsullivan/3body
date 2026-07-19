"""Focused tests for the evidence-bearing WP1 qualification components."""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

from src.python.orbits.differential_correction import (
    correct_halo,
    correct_planar_lyapunov,
)
from src.python.validation.cr3bp_variational import (
    cr3bp_jacobian,
    cr3bp_rhs,
    integrate_state_and_stm,
    reciprocal_pair_error,
    stability_index_from_eigenvalues,
)
from src.python.validation.qualification import (
    QualificationError,
    assert_metadata_matches,
    load_qualification_record,
    qualification_metadata,
)

QUALIFICATION_SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / "validation-external"
    / "wp1-validation"
    / "scripts"
)
sys.path.insert(0, str(QUALIFICATION_SCRIPTS))

from fetch_qualification_corpus import validate_response  # noqa: E402
from qualification_common import (  # noqa: E402
    canonical_json,
    deterministic_subset,
    sha256_bytes,
    sha256_file,
    verify_qualification_lock,
)


MU_EARTH_MOON = 0.012150585609624
LYAPUNOV_STATE = np.array(
    [
        0.6472382133654959,
        -5.156313909003344e-23,
        1.0974258145824058e-25,
        3.315735119008756e-13,
        0.7586104412243188,
        -1.050275389789411e-24,
    ]
)
LYAPUNOV_PERIOD = 6.527413524718724
HALO_STATE = np.array(
    [
        0.8760656451170601,
        1.0491502986863478e-26,
        0.191813535688546,
        -3.928226786817226e-14,
        0.2305575388925067,
        1.0601974505638561e-13,
    ]
)
HALO_PERIOD = 2.1764730139006754


def write_qualification_record(path: Path, status: str) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": "1.0",
        "qualification_id": "WP1Q-test",
        "status": status,
        "claim": "test claim",
        "lock_sha256": "abc",
    }
    record["record_payload_sha256"] = hashlib.sha256(
        json.dumps(
            record, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    ).hexdigest()
    path.write_text(json.dumps(record), encoding="utf-8")
    return record


def test_analytic_cr3bp_jacobian_matches_central_difference():
    state = np.array([0.84, 0.07, -0.03, 0.02, 0.19, -0.04])
    analytic = cr3bp_jacobian(state, MU_EARTH_MOON)
    numeric = np.empty((6, 6))
    for column in range(6):
        step = 2e-7 * max(1.0, abs(state[column]))
        plus = state.copy()
        minus = state.copy()
        plus[column] += step
        minus[column] -= step
        numeric[:, column] = (
            cr3bp_rhs(0.0, plus, MU_EARTH_MOON) - cr3bp_rhs(0.0, minus, MU_EARTH_MOON)
        ) / (2.0 * step)
    assert np.max(np.abs(analytic - numeric)) < 2e-7


def test_stability_index_uses_largest_reciprocal_multiplier():
    values = np.array([1.0, 1.0, 20.0, 0.05, np.exp(0.3j), np.exp(-0.3j)])
    assert stability_index_from_eigenvalues(values) == pytest.approx(10.025)
    assert reciprocal_pair_error(values) < 1e-14


def test_monodromy_reproduces_jpl_halo_stability():
    result = integrate_state_and_stm(
        HALO_STATE,
        HALO_PERIOD,
        MU_EARTH_MOON,
        rtol=3e-12,
        atol=3e-14,
    )
    assert result.closure_error < 1e-10
    assert result.stability_index == pytest.approx(1.0, abs=1e-7)
    assert result.determinant_error < 1e-8
    assert result.reciprocal_pair_error < 1e-7


def test_lyapunov_correction_recovers_periodic_neighbor():
    projected = np.array([LYAPUNOV_STATE[0], 0.0, 0.0, 0.0, LYAPUNOV_STATE[4], 0.0])
    result = correct_planar_lyapunov(
        projected,
        LYAPUNOV_PERIOD,
        MU_EARTH_MOON,
        fixed_x=projected[0] + 1e-5,
    )
    assert result.success, result.message
    assert result.closure_error < 1e-9
    assert result.symmetry_residual < 1e-10
    assert result.fixed_value == pytest.approx(projected[0] + 1e-5)


def test_halo_correction_recovers_periodic_neighbor():
    projected = np.array([HALO_STATE[0], 0.0, HALO_STATE[2], 0.0, HALO_STATE[4], 0.0])
    result = correct_halo(
        projected,
        HALO_PERIOD,
        MU_EARTH_MOON,
        fixed_z=projected[2] * 1.0001,
    )
    assert result.success, result.message
    assert result.closure_error < 1e-9
    assert result.symmetry_residual < 1e-10


def test_qualification_record_requires_pass(tmp_path):
    path = tmp_path / "record.json"
    write_qualification_record(path, "FAIL")
    with pytest.raises(QualificationError, match="is FAIL"):
        load_qualification_record(path)


def test_qualification_metadata_is_enforced(tmp_path):
    path = tmp_path / "record.json"
    write_qualification_record(path, "PASS")
    metadata = qualification_metadata(path)
    assert metadata["wp1_qualification_id"] == "WP1Q-test"
    assert_metadata_matches(metadata, metadata)
    with pytest.raises(QualificationError, match="metadata mismatch"):
        assert_metadata_matches({}, metadata)


def test_qualification_record_integrity_is_enforced(tmp_path):
    path = tmp_path / "record.json"
    record = write_qualification_record(path, "PASS")
    record["claim"] = "tampered claim"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(QualificationError, match="integrity failure"):
        load_qualification_record(path)


def test_lock_uses_portable_paths_and_detects_tampering(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    frozen = repo / "input.txt"
    frozen.write_text("frozen", encoding="utf-8")
    lock = {
        "schema_version": "1.0",
        "qualification_id": "WP1Q-test",
        "file_hashes": {"input.txt": sha256_file(frozen)},
    }
    lock["lock_sha256"] = sha256_bytes(canonical_json(lock))
    lock_path = repo / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    assert verify_qualification_lock(lock_path, repo)["qualification_id"] == "WP1Q-test"
    frozen.write_text("changed", encoding="utf-8")
    with pytest.raises(RuntimeError, match="lock violation"):
        verify_qualification_lock(lock_path, repo)


def test_jpl_response_metadata_must_match_requested_query():
    response = {
        "signature": {"version": "1.0"},
        "fields": ["x", "y", "z", "vx", "vy", "vz", "jacobi", "period", "stability"],
        "data": [["1", "0", "0", "0", "1", "0", "3", "6", "2"]],
        "count": 1,
        "family": "halo",
        "libration_point": 1,
        "branch": "N",
    }
    validate_response(
        response,
        "1.0",
        "https://example.invalid",
        {"family": "halo", "libr": 1, "branch": "N"},
    )
    with pytest.raises(RuntimeError, match="does not match request"):
        validate_response(
            response,
            "1.0",
            "https://example.invalid",
            {"family": "halo", "libr": 2, "branch": "N"},
        )


def test_capped_subset_remains_balanced_across_systems():
    rows = []
    for system in ["a", "b", "c", "d"]:
        for group in range(20):
            rows.append(
                {
                    "catalog_id": f"{system}-{group}",
                    "system": system,
                    "family": f"family-{group}",
                    "stability_regime": "test",
                }
            )
    selected = deterministic_subset(
        rows,
        24,
        salt="balance-test",
        group_keys=("system", "family", "stability_regime"),
    )
    counts = {
        system: sum(row["system"] == system for row in selected) for system in "abcd"
    }
    assert counts == {"a": 6, "b": 6, "c": 6, "d": 6}
