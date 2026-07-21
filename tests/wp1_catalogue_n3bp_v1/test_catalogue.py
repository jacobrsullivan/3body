from __future__ import annotations

import inspect

from src.python.wp1_catalogue_n3bp_v1 import (
    CorrectionResult,
    OrbitParameters,
    canonical_section_state,
    candidate_sha256,
    catalogue_sha256,
    generate_catalogue,
)


def _mock_corrector(seed, _settings) -> CorrectionResult:
    parameters = OrbitParameters(
        seed.m1,
        seed.m2,
        -0.37200864 + 0.08 * (seed.m1 - 1.0) - 0.03 * (seed.m2 - 1.0),
        1.21800411 - 0.12 * (seed.m1 - 1.0) + 0.04 * (seed.m2 - 1.0),
        0.45310805 + 0.02 * (seed.m1 - 1.0) + 0.09 * (seed.m2 - 1.0),
        7.53971451 + 0.5 * (seed.m1 - 1.0) + 0.2 * (seed.m2 - 1.0),
    )
    state = canonical_section_state(
        parameters.m1,
        parameters.m2,
        parameters.x1,
        parameters.v1,
        parameters.v2,
        parameters.period,
    )
    return CorrectionResult(
        parameters=parameters,
        state=tuple(state),
        residual=(0.0,) * 12,
        residual_linf=0.0,
        position_closure_linf=0.0,
        velocity_closure_linf=0.0,
        nfev=1,
        success=True,
        message="mock correction",
    )


def test_short_grid_has_complete_cartesian_product_and_lineage() -> None:
    grid = (0.995, 1.0, 1.005)
    run = generate_catalogue(
        grid,
        include_stability=False,
        corrector=_mock_corrector,
    )
    masses = {
        (candidate.correction.parameters.m1, candidate.correction.parameters.m2)
        for candidate in run.candidates
    }

    assert len(run.candidates) == 9
    assert masses == {(m1, m2) for m1 in grid for m2 in grid}
    assert len({candidate.candidate_id for candidate in run.candidates}) == 9
    assert sum(candidate.parent_id is None for candidate in run.candidates) == 1
    assert {candidate.continuation_axis for candidate in run.candidates} == {
        "root",
        "m1",
        "m2",
    }


def test_default_mocked_grid_has_locked_13_by_13_structure() -> None:
    run = generate_catalogue(include_stability=False, corrector=_mock_corrector)
    ordered_masses = [
        (candidate.correction.parameters.m1, candidate.correction.parameters.m2)
        for candidate in run.candidates
    ]

    assert len(run.provenance.mass_grid) == 13
    assert len(run.candidates) == 169
    assert len(set(ordered_masses)) == 169
    assert ordered_masses == sorted(ordered_masses)


def test_row_parallelism_preserves_canonical_payload() -> None:
    grid = (0.995, 1.0, 1.005)
    serial = generate_catalogue(
        grid, include_stability=False, corrector=_mock_corrector, workers=1
    )
    parallel = generate_catalogue(
        grid, include_stability=False, corrector=_mock_corrector, workers=2
    )

    assert catalogue_sha256(serial.candidates) == catalogue_sha256(
        parallel.candidates
    )


def test_generator_signature_and_provenance_prohibit_external_rows() -> None:
    parameter_names = set(inspect.signature(generate_catalogue).parameters)
    prohibited_fragments = {"external", "corpus", "row", "source", "seed", "file"}
    assert not any(
        fragment in name.lower()
        for name in parameter_names
        for fragment in prohibited_fragments
    )

    run = generate_catalogue(
        (1.0,), include_stability=False, corrector=_mock_corrector
    )
    assert run.provenance.disclosed_rounded_root_count == 1
    assert run.provenance.external_seed_count == 1
    assert run.provenance.external_catalogue_rows_used == 0
    assert run.provenance.evaluation_rows_used_as_seeds == 0
    assert run.candidates[0].correction.parameters == OrbitParameters(
        1.0,
        1.0,
        -0.37200864,
        1.21800411,
        0.45310805,
        7.53971451,
    )


def test_candidate_and_catalogue_hashes_are_canonical() -> None:
    run = generate_catalogue(
        (0.995, 1.0), include_stability=False, corrector=_mock_corrector
    )
    candidate = run.candidates[0]

    assert candidate_sha256(candidate) == candidate_sha256(candidate)
    assert len(candidate_sha256(candidate)) == 64
    assert catalogue_sha256(run.candidates) == catalogue_sha256(
        tuple(reversed(run.candidates))
    )
    assert all(character in "0123456789abcdef" for character in candidate_sha256(candidate))
