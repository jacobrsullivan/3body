"""Native two-mass continuation campaign for WP1-CAT-N3BP-v1."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, replace
import platform
import time

import numpy as np
import scipy

from .correction import correct_orbit
from .model import (
    CatalogueCandidate,
    CorrectionResult,
    CorrectionSettings,
    MASS_GRID,
    OrbitParameters,
)
from .variational import StabilitySettings, classify_orbit_stability


Corrector = Callable[[OrbitParameters, CorrectionSettings], CorrectionResult]


@dataclass(frozen=True, slots=True)
class CatalogueProvenance:
    campaign: str
    native_seed_mechanism: str
    disclosed_rounded_root_count: int
    external_seed_count: int
    external_catalogue_rows_used: int
    evaluation_rows_used_as_seeds: int
    mass_grid: tuple[float, ...]
    corrector: str
    integrator: str
    python_version: str
    numpy_version: str
    scipy_version: str


@dataclass(frozen=True, slots=True)
class CatalogueRun:
    candidates: tuple[CatalogueCandidate, ...]
    provenance: CatalogueProvenance
    elapsed_seconds: float


def candidate_id(m1: float, m2: float) -> str:
    return f"n3bp-m1-{m1:.3f}-m2-{m2:.3f}"


def _seed_from_vector(
    m1: float, m2: float, vector: np.ndarray
) -> OrbitParameters:
    return OrbitParameters(m1, m2, *(float(value) for value in vector))


def _checked_correction(
    seed: OrbitParameters,
    settings: CorrectionSettings,
    corrector: Corrector,
) -> CorrectionResult:
    result = corrector(seed, settings)
    if (result.parameters.m1, result.parameters.m2) != (seed.m1, seed.m2):
        raise RuntimeError("corrector changed fixed continuation masses")
    if not result.success:
        raise RuntimeError(
            f"correction failed at m1={seed.m1:.6f}, m2={seed.m2:.6f}: "
            f"{result.message} (closure={result.residual_linf:.3e})"
        )
    return result


def _continue_mass_line(
    center: CorrectionResult,
    axis: str,
    targets: Sequence[float],
    settings: CorrectionSettings,
    corrector: Corrector,
    internal_initial_step: float,
) -> dict[float, tuple[CorrectionResult, float]]:
    if axis not in {"m1", "m2"}:
        raise ValueError("continuation axis must be m1 or m2")
    center_mass = center.parameters.m1 if axis == "m1" else center.parameters.m2
    output: dict[float, tuple[CorrectionResult, float]] = {}

    for direction in (-1.0, 1.0):
        side = sorted(
            (float(value) for value in targets if direction * (value - center_mass) > 0.0),
            key=lambda value: abs(value - center_mass),
        )
        if not side:
            continue
        first_distance = abs(side[0] - center_mass)
        bootstrap_mass = center_mass + direction * min(
            internal_initial_step, first_distance
        )
        bootstrap_seed = center.parameters.with_masses(
            bootstrap_mass if axis == "m1" else center.parameters.m1,
            bootstrap_mass if axis == "m2" else center.parameters.m2,
        )
        previous_result = center
        current_result = _checked_correction(bootstrap_seed, settings, corrector)
        previous_mass = center_mass
        current_mass = bootstrap_mass
        prior_output_mass = center_mass

        if np.isclose(current_mass, side[0], rtol=0.0, atol=1.0e-14):
            output[side[0]] = (current_result, prior_output_mass)
            prior_output_mass = side[0]
            side = side[1:]

        for target_mass in side:
            fraction = (target_mass - current_mass) / (current_mass - previous_mass)
            predicted_vector = current_result.parameters.correction_vector() + fraction * (
                current_result.parameters.correction_vector()
                - previous_result.parameters.correction_vector()
            )
            seed = _seed_from_vector(
                target_mass if axis == "m1" else center.parameters.m1,
                target_mass if axis == "m2" else center.parameters.m2,
                predicted_vector,
            )
            corrected = _checked_correction(seed, settings, corrector)
            output[target_mass] = (corrected, prior_output_mass)
            prior_output_mass = target_mass
            previous_mass, previous_result = current_mass, current_result
            current_mass, current_result = target_mass, corrected
    return output


def _candidate(
    correction: CorrectionResult,
    parent_id: str | None,
    axis: str,
    include_stability: bool,
    stability_settings: StabilitySettings,
) -> CatalogueCandidate:
    candidate = CatalogueCandidate(
        candidate_id=candidate_id(
            correction.parameters.m1, correction.parameters.m2
        ),
        correction=correction,
        parent_id=parent_id,
        continuation_axis=axis,  # type: ignore[arg-type]
    )
    if include_stability:
        candidate = replace(
            candidate,
            stability=classify_orbit_stability(candidate, stability_settings),
        )
    return candidate


def _generate_row(
    work: tuple[
        float,
        CorrectionResult,
        float | None,
        tuple[float, ...],
        CorrectionSettings,
        StabilitySettings,
        bool,
        float,
        Corrector,
    ],
) -> tuple[CatalogueCandidate, ...]:
    (
        m1,
        center_result,
        center_parent_mass,
        grid,
        correction_settings,
        stability_settings,
        include_stability,
        internal_initial_step,
        corrector,
    ) = work
    center_parent_id = (
        None
        if center_parent_mass is None
        else candidate_id(center_parent_mass, 1.0)
    )
    row = [
        _candidate(
            center_result,
            center_parent_id,
            "root" if np.isclose(m1, 1.0) else "m1",
            include_stability,
            stability_settings,
        )
    ]
    m2_line = _continue_mass_line(
        center_result,
        "m2",
        grid,
        correction_settings,
        corrector,
        internal_initial_step,
    )
    for m2 in grid:
        if np.isclose(m2, 1.0):
            continue
        result, parent_mass = m2_line[m2]
        row.append(
            _candidate(
                result,
                candidate_id(m1, parent_mass),
                "m2",
                include_stability,
                stability_settings,
            )
        )
    return tuple(row)


def generate_catalogue(
    mass_grid: Sequence[float] = MASS_GRID,
    *,
    correction_settings: CorrectionSettings = CorrectionSettings(),
    stability_settings: StabilitySettings = StabilitySettings(),
    include_stability: bool = True,
    internal_initial_step: float = 1.0e-3,
    corrector: Corrector = correct_orbit,
    workers: int = 1,
) -> CatalogueRun:
    """Generate the native grid from the sole disclosed rounded root.

    The API deliberately has no external-row, source-corpus, seed-file, or
    evaluation-catalogue argument. ``mass_grid`` and ``corrector`` support
    bounded campaigns and focused tests without introducing data provenance.
    """

    started = time.perf_counter()
    grid = tuple(sorted({float(value) for value in mass_grid}))
    if not grid or not any(np.isclose(value, 1.0, atol=1.0e-14) for value in grid):
        raise ValueError("mass grid must contain the disclosed-root mass 1.0")
    if min(grid) <= 0.0 or internal_initial_step <= 0.0 or workers <= 0:
        raise ValueError(
            "mass values, the internal initial step, and workers must be positive"
        )

    root_result = _checked_correction(
        OrbitParameters.disclosed_root(), correction_settings, corrector
    )
    m1_line = _continue_mass_line(
        root_result,
        "m1",
        grid,
        correction_settings,
        corrector,
        internal_initial_step,
    )
    row_centers: dict[float, tuple[CorrectionResult, float | None]] = {
        1.0: (root_result, None)
    }
    row_centers.update(m1_line)

    row_work = [
        (
            m1,
            *row_centers[m1],
            grid,
            correction_settings,
            stability_settings,
            include_stability,
            internal_initial_step,
            corrector,
        )
        for m1 in grid
    ]
    if workers == 1:
        rows = map(_generate_row, row_work)
        candidates = [candidate for row in rows for candidate in row]
    else:
        try:
            executor = ProcessPoolExecutor(max_workers=workers)
        except PermissionError:
            executor = ThreadPoolExecutor(max_workers=workers)
        with executor:
            rows = executor.map(_generate_row, row_work)
            candidates = [candidate for row in rows for candidate in row]

    candidates.sort(
        key=lambda item: (
            item.correction.parameters.m1,
            item.correction.parameters.m2,
        )
    )
    provenance = CatalogueProvenance(
        campaign="WP1-CAT-N3BP-v1",
        native_seed_mechanism="disclosed-rounded-root-plus-two-mass-secant-continuation",
        disclosed_rounded_root_count=1,
        external_seed_count=1,
        external_catalogue_rows_used=0,
        evaluation_rows_used_as_seeds=0,
        mass_grid=grid,
        corrector="damped-scipy-least_squares-trf",
        integrator="scipy-DOP853",
        python_version=platform.python_version(),
        numpy_version=np.__version__,
        scipy_version=scipy.__version__,
    )
    return CatalogueRun(
        candidates=tuple(candidates),
        provenance=provenance,
        elapsed_seconds=time.perf_counter() - started,
    )
