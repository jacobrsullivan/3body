"""A bounded, canonical KS lift of the three N3BP pair states.

For the oriented cycle

``x12=r2-r1, x23=r3-r2, x31=r1-r3``, each pair uses canonical relative
momentum ``pij=muij*(vj-vi)`` and the qualified zero-level KS cotangent lift.
The three position and velocity closure equations recover the 12-dimensional
translation-reduced N3BP phase space after the three Xi restrictions and
three S1 quotients.

This is a kinematic constrained lift.  In a genuine three-body field each
pair is perturbed by the remaining body, the three pair Hamiltonians are not
independent Kepler Hamiltonians, and one physical time cannot obey three
different Sundman rules ``dt/ds=rij``.  No simultaneous oscillator or global
three-body regularization claim is made here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.ks import (
    KSPhaseState,
    KeplerPhaseState,
    lift_cotangent,
    project_cotangent,
    s1_action,
)
from src.python.n3bp_qualification import InertialState, SystemParameters
from src.python.threebody_reduction import TranslationReconstruction


FloatArray: TypeAlias = NDArray[np.float64]
PAIR_NAMES = ("12", "23", "31")


def _vector(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result


def _reduced_masses(parameters: SystemParameters) -> tuple[float, float, float]:
    m1, m2, m3 = (float(value) for value in parameters.masses)
    return (
        m1 * m2 / (m1 + m2),
        m2 * m3 / (m2 + m3),
        m3 * m1 / (m3 + m1),
    )


@dataclass(frozen=True)
class PairKeplerParameters:
    """Instantaneous isolated-pair parameters used by each KS cotangent map."""

    pair: str
    reduced_mass: float
    kappa: float


@dataclass(frozen=True)
class PairConstraintResiduals:
    """Residuals defining the constrained three-pair physical image."""

    momentum_maps: ArrayLike
    position_closure: ArrayLike
    velocity_closure: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "momentum_maps",
            _vector(self.momentum_maps, "momentum_maps"),
        )
        object.__setattr__(
            self,
            "position_closure",
            _vector(self.position_closure, "position_closure"),
        )
        object.__setattr__(
            self,
            "velocity_closure",
            _vector(self.velocity_closure, "velocity_closure"),
        )

    @property
    def momentum_map_max(self) -> float:
        return float(np.max(np.abs(self.momentum_maps)))

    @property
    def position_closure_norm(self) -> float:
        return float(np.linalg.norm(self.position_closure))

    @property
    def velocity_closure_norm(self) -> float:
        return float(np.linalg.norm(self.velocity_closure))

    def satisfied(
        self,
        *,
        momentum_tolerance: float = 1e-11,
        position_tolerance: float = 1e-11,
        velocity_tolerance: float = 1e-11,
    ) -> bool:
        return bool(
            self.momentum_map_max <= momentum_tolerance
            and self.position_closure_norm <= position_tolerance
            and self.velocity_closure_norm <= velocity_tolerance
        )


@dataclass(frozen=True)
class CanonicalPairwiseKSLift:
    """Three canonical KS pair states before the S1 cubed quotient."""

    parameters: SystemParameters
    ks12: KSPhaseState
    ks23: KSPhaseState
    ks31: KSPhaseState

    def __post_init__(self) -> None:
        for name in ("ks12", "ks23", "ks31"):
            if not isinstance(getattr(self, name), KSPhaseState):
                raise TypeError(f"{name} must be a KSPhaseState")

    @property
    def pair_states(self) -> tuple[KSPhaseState, KSPhaseState, KSPhaseState]:
        return self.ks12, self.ks23, self.ks31

    @property
    def kepler_parameters(
        self,
    ) -> tuple[PairKeplerParameters, PairKeplerParameters, PairKeplerParameters]:
        masses = tuple(float(value) for value in self.parameters.masses)
        reduced = _reduced_masses(self.parameters)
        gravitational_constant = self.parameters.gravitational_constant
        products = (masses[0] * masses[1], masses[1] * masses[2], masses[2] * masses[0])
        return tuple(
            PairKeplerParameters(
                pair=name,
                reduced_mass=mu,
                kappa=gravitational_constant * product,
            )
            for name, mu, product in zip(PAIR_NAMES, reduced, products, strict=True)
        )

    def project_pairs(
        self,
    ) -> tuple[KeplerPhaseState, KeplerPhaseState, KeplerPhaseState]:
        return tuple(project_cotangent(state) for state in self.pair_states)

    def relative_velocities(self) -> tuple[FloatArray, FloatArray, FloatArray]:
        projected = self.project_pairs()
        reduced = _reduced_masses(self.parameters)
        return tuple(
            state.p / mass for state, mass in zip(projected, reduced, strict=True)
        )

    def constraint_residuals(self) -> PairConstraintResiduals:
        projected = self.project_pairs()
        velocities = self.relative_velocities()
        return PairConstraintResiduals(
            momentum_maps=np.array([state.xi for state in self.pair_states]),
            position_closure=sum((state.x for state in projected), np.zeros(3)),
            velocity_closure=sum(velocities, np.zeros(3)),
        )

    def act_s1_cubed(self, angles: Sequence[float]) -> "CanonicalPairwiseKSLift":
        angle_array = np.asarray(angles, dtype=np.float64)
        if angle_array.shape != (3,) or not np.all(np.isfinite(angle_array)):
            raise ValueError("angles must contain three finite values")
        transformed = tuple(
            s1_action(state, float(angle))
            for state, angle in zip(self.pair_states, angle_array, strict=True)
        )
        return CanonicalPairwiseKSLift(self.parameters, *transformed)

    def to_inertial(
        self,
        reconstruction: TranslationReconstruction | None = None,
        *,
        closure_tolerance: float = 1e-10,
    ) -> InertialState:
        if not np.isfinite(closure_tolerance) or closure_tolerance < 0.0:
            raise ValueError("closure_tolerance must be finite and non-negative")
        if reconstruction is None:
            reconstruction = TranslationReconstruction(np.zeros(3), np.zeros(3))
        projected = self.project_pairs()
        velocities = self.relative_velocities()
        position_scale = max(1.0, *(state.radius for state in projected))
        velocity_scale = max(
            1.0, *(float(np.linalg.norm(value)) for value in velocities)
        )
        residuals = self.constraint_residuals()
        if residuals.position_closure_norm > closure_tolerance * position_scale:
            raise ValueError("pair positions do not satisfy triangle closure")
        if residuals.velocity_closure_norm > closure_tolerance * velocity_scale:
            raise ValueError("pair velocities do not satisfy triangle closure")

        x12, x23, _ = (state.x for state in projected)
        v12, v23, _ = velocities
        positions = np.stack((np.zeros(3), x12, x12 + x23))
        body_velocities = np.stack((np.zeros(3), v12, v12 + v23))
        masses = self.parameters.masses
        total_mass = self.parameters.total_mass
        temporary_center = np.sum(masses[:, None] * positions, axis=0) / total_mass
        temporary_velocity = (
            np.sum(masses[:, None] * body_velocities, axis=0) / total_mass
        )
        positions = positions - temporary_center + reconstruction.center_of_mass
        center_velocity = reconstruction.total_momentum / total_mass
        body_velocities = body_velocities - temporary_velocity + center_velocity
        return InertialState.from_components(positions, body_velocities)


@dataclass(frozen=True)
class PairwiseKSResult:
    """Constrained pairwise lift plus the removed translational data."""

    lift: CanonicalPairwiseKSLift
    reconstruction: TranslationReconstruction

    def reconstruct(self, *, closure_tolerance: float = 1e-10) -> InertialState:
        return self.lift.to_inertial(
            self.reconstruction,
            closure_tolerance=closure_tolerance,
        )


def lift_pairwise_ks(
    state: InertialState,
    parameters: SystemParameters,
    *,
    angles: Sequence[float] = (0.0, 0.0, 0.0),
) -> PairwiseKSResult:
    """Lift all three oriented relative states with the qualified KS section."""

    angle_array = np.asarray(angles, dtype=np.float64)
    if angle_array.shape != (3,) or not np.all(np.isfinite(angle_array)):
        raise ValueError("angles must contain three finite values")
    positions = state.positions
    velocities = state.velocities
    pair_indices = ((0, 1), (1, 2), (2, 0))
    reduced_masses = _reduced_masses(parameters)
    lifted: list[KSPhaseState] = []
    for (first, second), reduced_mass, angle in zip(
        pair_indices, reduced_masses, angle_array, strict=True
    ):
        physical = KeplerPhaseState(
            x=positions[second] - positions[first],
            p=reduced_mass * (velocities[second] - velocities[first]),
        )
        lifted.append(lift_cotangent(physical, angle=float(angle)))
    center_of_mass = (
        np.sum(parameters.masses[:, None] * positions, axis=0) / parameters.total_mass
    )
    total_momentum = np.sum(parameters.masses[:, None] * velocities, axis=0)
    lift = CanonicalPairwiseKSLift(parameters, *lifted)
    residuals = lift.constraint_residuals()
    scales = max(
        1.0,
        *(item.radius for item in lift.project_pairs()),
        *(float(np.linalg.norm(value)) for value in lift.relative_velocities()),
    )
    if not residuals.satisfied(
        momentum_tolerance=5e-12 * scales,
        position_tolerance=5e-12 * scales,
        velocity_tolerance=5e-12 * scales,
    ):
        raise ArithmeticError("canonical pairwise lift failed its defining constraints")
    return PairwiseKSResult(
        lift=lift,
        reconstruction=TranslationReconstruction(center_of_mass, total_momentum),
    )


def pairwise_dimension_accounting() -> dict[str, int | bool | str]:
    """Return the constraint and quotient dimensions of the pairwise lift."""

    return {
        "three_ks_phase_spaces": 24,
        "xi_zero_constraints": 3,
        "s1_gauge_dimensions": 3,
        "three_physical_pair_phase_spaces": 18,
        "position_closure_constraints": 3,
        "velocity_closure_constraints": 3,
        "translation_reduced_n3bp_phase_space": 12,
        "global_sundman_time_qualified": False,
        "interpretation": "kinematic constrained lift, not three independent Kepler systems",
    }
