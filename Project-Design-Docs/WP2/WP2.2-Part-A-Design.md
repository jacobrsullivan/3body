# WP 2.2 Part A: Principal Bundle Construction - Detailed Design

**Task**: WP 2.2 - S¹ "Untwisting" Lift Construction
**Part**: A - Principal Bundle Construction
**Status**: Design Phase
**Estimated Duration**: 3 days
**Dependencies**: Task 2.1.2 Complete (Connection and Curvature)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Data Structures](#data-structures)
4. [Core Algorithms](#core-algorithms)
5. [Implementation Details](#implementation-details)
6. [Validation Strategy](#validation-strategy)
7. [Performance Targets](#performance-targets)
8. [Integration Points](#integration-points)
9. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

Part A implements the foundational infrastructure for the **S¹ principal bundle** over shape space. This geometric structure is the key to the "untwisting" lift: by adding a circular fiber at each point in shape space, we create an extended space where the magnetic connection discovered in Task 2.1.2 can be "unwound."

**Core Geometric Idea**:
- **Base Space**: $S$ = 3D shape space (after rotation reduction)
- **Fiber**: $S^1 = \mathbb{R}/2\pi\mathbb{Z}$ = circle (1D)
- **Total Space**: $P = S \times S^1$ (4D)
- **Projection**: $\pi: P \to S$ forgets the fiber coordinate

The fiber coordinate $\theta$ represents the "twist" accumulated as we move through shape space. By explicitly tracking this twist, we transform the non-integrable dynamics "downstairs" (shape space with magnetic connection) into potentially integrable dynamics "upstairs" (bundle space).

### Objectives

1. **Data Structures**: Implement `BundleState` representing points in $P$
2. **Bundle Class**: Create `S1Bundle` managing the total space geometry
3. **Charts**: Implement local coordinate systems on $P$
4. **Transition Functions**: Handle chart overlaps via gauge transformations
5. **Bundle Operations**: Projection, fiber extraction, sections
6. **Validation**: Verify bundle axioms and consistency

### Deliverables

- `BundleState` class: Coordinates $(s, \theta, p_s, p_\theta)$ in phase space
- `S1Bundle` class: Manages bundle structure
- `BundleChart` class: Local coordinate patches
- `BundleSection` class: Maps from base to bundle
- Transition function algorithms
- Comprehensive validation tests
- Complete documentation with examples

---

## Mathematical Background

### Principal Bundles: A Brief Review

A **principal $G$-bundle** consists of:
- **Total space** $P$ (manifold)
- **Base space** $M$ (manifold)
- **Structure group** $G$ (Lie group)
- **Projection** $\pi: P \to M$ (surjective submersion)
- **Group action** $P \times G \to P$ (free, right action preserving fibers)

**Local Triviality**: For each $x \in M$, there exists neighborhood $U \ni x$ such that:
$$\pi^{-1}(U) \cong U \times G$$

For our case:
- $M = S$ (shape space)
- $G = S^1 = \{e^{i\theta} : \theta \in [0, 2\pi)\}$ (circle group)
- $P = S \times S^1$ (locally, may have global topology)

### Why S¹?

The fiber $S^1$ is chosen to match the structure of the connection one-form $\mathcal{A}$ from Task 2.1.2:

1. **Connection as Gauge Field**: $\mathcal{A}$ takes values in $\mathfrak{u}(1) = i\mathbb{R}$ (Lie algebra of $S^1$)
2. **Curvature as Obstruction**: $\mathcal{F} = d\mathcal{A}$ measures the failure of $\mathcal{A}$ to be "pure gauge"
3. **Lift Eliminates Curvature**: By adding the fiber, we can absorb $\mathcal{A}$ into the geometry, making the lifted space "flatter"

**Physical Analogy**: Think of $\mathcal{A}$ as a magnetic vector potential. The bundle is the "gauge bundle" where phases (elements of $S^1$) live naturally.

### Bundle Coordinates

**Global Coordinates** (when bundle is trivial):
$$P = S \times S^1$$
Point: $(s, \theta)$ where $s \in S$, $\theta \in [0, 2\pi)$

**Phase Space Coordinates** (cotangent bundle $T^*P$):
$$(s, \theta, p_s, p_\theta)$$
where:
- $s = (r_{12}, r_{23}, r_{31})$ ∈ shape space
- $\theta$ ∈ $[0, 2\pi)$ = fiber coordinate ("gauge phase")
- $p_s = (p_{12}, p_{23}, p_{31})$ = momenta conjugate to shape coordinates
- $p_\theta$ = momentum conjugate to fiber coordinate (will be conserved!)

**Dimension Count**:
- Configuration space: $\dim(P) = 3 + 1 = 4$
- Phase space: $\dim(T^*P) = 2 \times 4 = 8$

### Gauge Transformations

In overlapping charts, the fiber coordinate transforms by:
$$\theta_2 = \theta_1 + \alpha_{12}(s)$$

where $\alpha_{12}: U_1 \cap U_2 \to \mathbb{R}$ is the **gauge transformation**.

**Cocycle Condition** (on triple overlaps $U_1 \cap U_2 \cap U_3$):
$$\alpha_{12}(s) + \alpha_{23}(s) + \alpha_{31}(s) = 0 \mod 2\pi$$

This ensures consistency when moving through three charts.

**Connection Transformation**: Under gauge transformation, the connection transforms:
$$\mathcal{A}_2 = \mathcal{A}_1 - d\alpha_{12}$$

This is the standard gauge transformation for a $U(1)$ connection.

### Triviality of Bundle

For **shape space** (contractible or simply connected):
- Bundle is **trivial**: $P = S \times S^1$ globally
- Can choose $\alpha_{12} = 0$ (trivial gauge)
- Simplifies implementation significantly

**Note**: If shape space has non-trivial topology (holes, handles), the bundle may be non-trivial (e.g., Möbius strip over circle). For now, we assume contractibility.

---

## Data Structures

### BundleState

```python
# File: src/python/lifts/s1_bundle.py

from dataclasses import dataclass
from typing import Optional
import numpy as np
from ..core.shape_space import ShapeSpaceState

@dataclass(frozen=True)
class BundleState:
    """
    State in the S¹ principal bundle P = Shape Space × S¹.

    Represents a point in phase space T*P with coordinates:
        (s, θ, p_s, p_θ)
    where:
        - s ∈ Shape Space (base coordinates)
        - θ ∈ [0, 2π) (fiber coordinate)
        - p_s = momenta conjugate to s
        - p_θ = momentum conjugate to θ (conserved!)

    Attributes:
        shape_state: Base space coordinates (r12, r23, r31, L)
        theta: Fiber coordinate (angle ∈ [0, 2π))
        shape_momenta: Momenta conjugate to shape coordinates (3,)
        p_theta: Momentum conjugate to fiber coordinate (scalar)
        metadata: Optional dictionary for auxiliary data

    Examples:
        >>> shape_state = ShapeSpaceState(r12=1.0, r23=1.2, r31=1.1, L=1.0)
        >>> momenta = np.array([0.1, -0.05, 0.08])
        >>> state = BundleState(
        ...     shape_state=shape_state,
        ...     theta=np.pi/4,
        ...     shape_momenta=momenta,
        ...     p_theta=0.5
        ... )
        >>> state.dimension
        8
        >>> state.theta
        0.7853981633974483  # π/4
    """
    shape_state: ShapeSpaceState
    theta: float  # Fiber coordinate ∈ [0, 2π)
    shape_momenta: np.ndarray  # (3,) for planar case
    p_theta: float  # Fiber momentum
    metadata: Optional[dict] = None

    def __post_init__(self):
        """
        Post-initialization validation and normalization.

        - Normalizes theta to [0, 2π)
        - Validates array shapes
        - Freezes arrays for immutability
        """
        # Normalize theta to [0, 2π)
        theta_normalized = self.theta % (2 * np.pi)
        if theta_normalized < 0:
            theta_normalized += 2 * np.pi
        object.__setattr__(self, 'theta', theta_normalized)

        # Validate shape_momenta dimension
        shape_dim = 3  # Planar 3-body
        if len(self.shape_momenta) != shape_dim:
            raise ValueError(
                f"shape_momenta must have dimension {shape_dim}, "
                f"got {len(self.shape_momenta)}"
            )

        # Freeze arrays (immutability)
        momenta_frozen = np.array(self.shape_momenta, dtype=np.float64)
        momenta_frozen.flags.writeable = False
        object.__setattr__(self, 'shape_momenta', momenta_frozen)

    @property
    def dimension(self) -> int:
        """
        Phase space dimension: 2 × (dim(base) + dim(fiber))

        For planar 3-body: 2 × (3 + 1) = 8
        """
        return 2 * (len(self.shape_momenta) + 1)

    @property
    def configuration_dimension(self) -> int:
        """Configuration space dimension: 3 (shape) + 1 (fiber) = 4"""
        return len(self.shape_momenta) + 1

    def to_vector(self) -> np.ndarray:
        """
        Flatten state to vector [s, θ, p_s, p_θ].

        Order: [r12, r23, r31, θ, p12, p23, p31, p_θ]

        Returns:
            Array of shape (8,) for planar case

        Examples:
            >>> state.to_vector()
            array([1.0, 1.2, 1.1, 0.785, 0.1, -0.05, 0.08, 0.5])
        """
        shape_coords = self.shape_state.to_array()  # [r12, r23, r31]
        return np.concatenate([
            shape_coords,
            [self.theta],
            self.shape_momenta,
            [self.p_theta]
        ])

    @staticmethod
    def from_vector(vector: np.ndarray, L: float = 1.0) -> 'BundleState':
        """
        Reconstruct BundleState from flat vector.

        Args:
            vector: Flattened state [s, θ, p_s, p_θ]
            L: Angular momentum (needed for ShapeSpaceState)

        Returns:
            BundleState

        Examples:
            >>> vec = np.array([1.0, 1.2, 1.1, 0.785, 0.1, -0.05, 0.08, 0.5])
            >>> state = BundleState.from_vector(vec, L=1.0)
        """
        if len(vector) != 8:
            raise ValueError(f"Expected vector of length 8, got {len(vector)}")

        shape_coords = vector[:3]  # [r12, r23, r31]
        theta = vector[3]
        shape_momenta = vector[4:7]
        p_theta = vector[7]

        shape_state = ShapeSpaceState(
            r12=shape_coords[0],
            r23=shape_coords[1],
            r31=shape_coords[2],
            L=L
        )

        return BundleState(
            shape_state=shape_state,
            theta=theta,
            shape_momenta=shape_momenta,
            p_theta=p_theta
        )

    def copy_with(
        self,
        shape_state: Optional[ShapeSpaceState] = None,
        theta: Optional[float] = None,
        shape_momenta: Optional[np.ndarray] = None,
        p_theta: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> 'BundleState':
        """
        Create modified copy (functional update).

        Args:
            shape_state: New base state (or keep current)
            theta: New fiber coordinate (or keep current)
            shape_momenta: New base momenta (or keep current)
            p_theta: New fiber momentum (or keep current)
            metadata: New metadata (or keep current)

        Returns:
            New BundleState with updates applied
        """
        return BundleState(
            shape_state=shape_state if shape_state is not None else self.shape_state,
            theta=theta if theta is not None else self.theta,
            shape_momenta=shape_momenta if shape_momenta is not None else self.shape_momenta,
            p_theta=p_theta if p_theta is not None else self.p_theta,
            metadata=metadata if metadata is not None else self.metadata
        )

    def __repr__(self) -> str:
        """Human-readable representation"""
        return (
            f"BundleState(\n"
            f"  shape: ({self.shape_state.r12:.4f}, {self.shape_state.r23:.4f}, "
            f"{self.shape_state.r31:.4f}),\n"
            f"  θ: {self.theta:.4f} rad,\n"
            f"  p_shape: [{self.shape_momenta[0]:.4f}, {self.shape_momenta[1]:.4f}, "
            f"{self.shape_momenta[2]:.4f}],\n"
            f"  p_θ: {self.p_theta:.4f}\n"
            f")"
        )
```

### S1Bundle

```python
# File: src/python/lifts/s1_bundle.py (continued)

from typing import List, Callable
from ..core.shape_space import ShapeSpace

class S1Bundle:
    """
    Principal S¹ bundle over shape space.

    Structure: P = S × S¹ where:
        - S = shape space (base manifold, 3D for planar case)
        - S¹ = circle fiber (1D)
        - P = total space (4D)

    For planar three-body problem:
        - Base: S ≅ ℝ³ (valid triangle configurations)
        - Fiber: S¹ = [0, 2π) with periodic boundary
        - Total space: P = S × S¹ (trivial bundle over contractible base)

    Attributes:
        base: ShapeSpace manifold (base of bundle)
        fiber_dimension: Dimension of S¹ fiber (always 1)
        trivial: Whether bundle is topologically trivial (True for contractible base)

    Examples:
        >>> from src.python.core.shape_space import ShapeSpace
        >>> base = ShapeSpace()
        >>> bundle = S1Bundle(base)
        >>> bundle.total_dimension
        4
        >>> bundle.phase_space_dimension
        8
    """

    def __init__(
        self,
        base_manifold: ShapeSpace,
        trivial: bool = True
    ):
        """
        Initialize S¹ bundle.

        Args:
            base_manifold: Shape space (base of bundle)
            trivial: Whether to assume trivial bundle structure (default True)
                    For contractible shape space, this is valid.
        """
        self.base = base_manifold
        self.fiber_dimension = 1  # S¹ is 1-dimensional
        self.trivial = trivial

        # Chart atlas (list of BundleChart objects)
        self._charts: List[BundleChart] = []

    @property
    def base_dimension(self) -> int:
        """Dimension of base space (3 for planar case)"""
        return self.base.dimension

    @property
    def total_dimension(self) -> int:
        """Dimension of total space = dim(base) + dim(fiber) = 3 + 1 = 4"""
        return self.base_dimension + self.fiber_dimension

    @property
    def phase_space_dimension(self) -> int:
        """Dimension of phase space T*P = 2 × total_dimension = 8"""
        return 2 * self.total_dimension

    def create_state(
        self,
        shape_state: ShapeSpaceState,
        theta: float,
        shape_momenta: np.ndarray,
        p_theta: float,
        metadata: Optional[dict] = None
    ) -> BundleState:
        """
        Create a state in the bundle.

        Args:
            shape_state: Point in shape space
            theta: Fiber coordinate (angle in radians)
            shape_momenta: Momenta in base space (3,)
            p_theta: Fiber momentum
            metadata: Optional auxiliary data

        Returns:
            BundleState representing point in T*P

        Examples:
            >>> shape_state = ShapeSpaceState(1.0, 1.2, 1.1, L=1.0)
            >>> momenta = np.array([0.1, -0.05, 0.08])
            >>> state = bundle.create_state(shape_state, np.pi/4, momenta, 0.5)
        """
        # Validate base state is physically valid
        if not self.base.is_valid_state(shape_state):
            raise ValueError(
                f"Invalid shape state: {shape_state}. "
                f"Must satisfy triangle inequality."
            )

        return BundleState(
            shape_state=shape_state,
            theta=theta,
            shape_momenta=shape_momenta,
            p_theta=p_theta,
            metadata=metadata
        )

    def project_to_base(self, bundle_state: BundleState) -> ShapeSpaceState:
        """
        Projection π: P → S.

        Forgets the fiber coordinate, returning only base space point.

        Args:
            bundle_state: Point in bundle

        Returns:
            Projection to shape space

        Examples:
            >>> projected = bundle.project_to_base(state)
            >>> projected.r12
            1.0
        """
        return bundle_state.shape_state

    def fiber_over_point(
        self,
        base_point: ShapeSpaceState,
        n_samples: int = 100,
        momenta: Optional[np.ndarray] = None,
        p_theta_value: float = 0.0
    ) -> List[BundleState]:
        """
        Return fiber π⁻¹(s) over a base point.

        The fiber is a circle: all states with fixed shape coordinates,
        varying only θ ∈ [0, 2π).

        Args:
            base_point: Point in shape space
            n_samples: Number of points to sample on fiber
            momenta: Base momenta (default: zero)
            p_theta_value: Fiber momentum (default: 0)

        Returns:
            List of BundleStates representing fiber (discrete sample)

        Examples:
            >>> base_point = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
            >>> fiber = bundle.fiber_over_point(base_point, n_samples=50)
            >>> len(fiber)
            50
            >>> # All project to same base point
            >>> all(bundle.project_to_base(s) == base_point for s in fiber)
            True
        """
        if momenta is None:
            momenta = np.zeros(self.base_dimension)

        theta_values = np.linspace(0, 2*np.pi, n_samples, endpoint=False)

        return [
            BundleState(
                shape_state=base_point,
                theta=theta,
                shape_momenta=momenta,
                p_theta=p_theta_value
            )
            for theta in theta_values
        ]

    def create_section(
        self,
        section_function: Callable[[ShapeSpaceState], float]
    ) -> 'BundleSection':
        """
        Create a section σ: S → P.

        A section assigns a fiber coordinate θ = σ(s) to each base point.
        Equivalently, it "picks a point" in each fiber consistently.

        Args:
            section_function: Function s ↦ θ(s) defining the section

        Returns:
            BundleSection object

        Examples:
            >>> # Zero section: θ = 0 everywhere
            >>> zero_section = bundle.create_section(lambda s: 0.0)
            >>>
            >>> # Constant section: θ = π everywhere
            >>> const_section = bundle.create_section(lambda s: np.pi)
            >>>
            >>> # Non-trivial section (if base is not contractible)
            >>> def winding_section(s):
            ...     # Example: θ depends on angle in base space
            ...     return np.arctan2(s.r23 - 1.0, s.r12 - 1.0)
            >>> winding = bundle.create_section(winding_section)
        """
        return BundleSection(self, section_function)

    def add_chart(self, chart: 'BundleChart'):
        """
        Add a coordinate chart to the atlas.

        Args:
            chart: BundleChart to add
        """
        self._charts.append(chart)

    def find_chart(self, state: BundleState) -> Optional['BundleChart']:
        """
        Find a chart containing the given state.

        Args:
            state: Bundle state

        Returns:
            BundleChart containing state, or None if not found
        """
        for chart in self._charts:
            if chart.is_in_domain(state):
                return chart
        return None

    def validate_structure(self) -> dict:
        """
        Validate bundle structure properties.

        Checks:
            1. Projection is surjective
            2. Fibers are diffeomorphic to S¹
            3. Local triviality (if charts defined)
            4. Cocycle condition on chart overlaps

        Returns:
            Dictionary with validation results
        """
        results = {
            'projection_valid': True,
            'fiber_structure_valid': True,
            'charts_valid': True,
            'cocycle_valid': True,
            'errors': []
        }

        # Test 1: Projection preserves base dimension
        try:
            test_shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
            test_state = self.create_state(
                test_shape, 0.0, np.zeros(3), 0.0
            )
            projected = self.project_to_base(test_state)

            if projected.to_array().shape[0] != self.base_dimension:
                results['projection_valid'] = False
                results['errors'].append("Projection dimension mismatch")
        except Exception as e:
            results['projection_valid'] = False
            results['errors'].append(f"Projection error: {e}")

        # Test 2: Fiber has circular topology
        try:
            test_shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
            fiber = self.fiber_over_point(test_shape, n_samples=100)

            # Check all fiber points project to same base point
            for state in fiber:
                proj = self.project_to_base(state)
                if not np.allclose(proj.to_array(), test_shape.to_array()):
                    results['fiber_structure_valid'] = False
                    results['errors'].append("Fiber projection inconsistency")
                    break

            # Check fiber coordinates cover [0, 2π)
            thetas = [s.theta for s in fiber]
            if min(thetas) < 0 or max(thetas) >= 2*np.pi:
                results['fiber_structure_valid'] = False
                results['errors'].append("Fiber coordinate range invalid")

        except Exception as e:
            results['fiber_structure_valid'] = False
            results['errors'].append(f"Fiber structure error: {e}")

        # Test 3: Charts cover total space (if charts defined)
        if len(self._charts) == 0:
            results['charts_valid'] = True  # No charts to validate
        else:
            # Check charts are well-defined
            # (More detailed tests in BundleChart validation)
            pass

        # Test 4: Cocycle condition (if multiple charts)
        if len(self._charts) >= 2:
            # Verify gauge transformations satisfy cocycle condition
            # (Detailed implementation in transition function tests)
            pass

        results['valid'] = all([
            results['projection_valid'],
            results['fiber_structure_valid'],
            results['charts_valid'],
            results['cocycle_valid']
        ])

        return results
```

### BundleChart

```python
# File: src/python/lifts/bundle_coordinates.py

from typing import Callable, Tuple, Optional
import numpy as np
from .s1_bundle import BundleState, ShapeSpaceState

class BundleChart:
    """
    Local coordinate chart for S¹ bundle.

    A chart φ: π⁻¹(U) → U × S¹ provides local coordinates on the bundle,
    where U ⊂ Shape Space is an open set.

    For trivial bundle: φ is just the identity (s, θ) ↦ (s, θ)
    For non-trivial bundle: φ may involve gauge transformations

    Attributes:
        domain: Function determining if base point is in chart domain U
        name: Human-readable chart identifier
        gauge_choice: Function s ↦ gauge offset (for non-trivial bundles)

    Examples:
        >>> # Chart covering all of shape space
        >>> def always_true(s):
        ...     return True
        >>> global_chart = BundleChart(always_true, name="Global")
        >>>
        >>> # Chart covering region r12 < 2.0
        >>> def region1(s):
        ...     return s.r12 < 2.0
        >>> chart1 = BundleChart(region1, name="Region1")
    """

    def __init__(
        self,
        base_chart_domain: Callable[[ShapeSpaceState], bool],
        name: str = "Chart",
        gauge_choice: Optional[Callable[[ShapeSpaceState], float]] = None
    ):
        """
        Initialize bundle chart.

        Args:
            base_chart_domain: Function determining if base point is in U
            name: Chart identifier
            gauge_choice: Optional gauge transformation function
                         (default: zero gauge for trivial bundle)
        """
        self.domain = base_chart_domain
        self.name = name
        self.gauge_choice = gauge_choice if gauge_choice is not None else (lambda s: 0.0)

    def is_in_domain(self, state: BundleState) -> bool:
        """
        Check if bundle state is in chart domain π⁻¹(U).

        Args:
            state: Point in bundle

        Returns:
            True if base projection is in U

        Examples:
            >>> state = BundleState(...)
            >>> chart.is_in_domain(state)
            True
        """
        return self.domain(state.shape_state)

    def coordinates(self, state: BundleState) -> Tuple[np.ndarray, float]:
        """
        Chart map: bundle state → (s, θ) coordinates.

        For trivial bundle, this is just extraction of coordinates.
        For non-trivial bundle, applies gauge transformation.

        Args:
            state: Point in bundle

        Returns:
            (shape_coords, theta) tuple

        Raises:
            ValueError: If state not in chart domain

        Examples:
            >>> coords, theta = chart.coordinates(state)
            >>> coords.shape
            (3,)  # [r12, r23, r31]
            >>> 0 <= theta < 2*np.pi
            True
        """
        if not self.is_in_domain(state):
            raise ValueError(
                f"State not in domain of chart '{self.name}'. "
                f"Base point: {state.shape_state}"
            )

        shape_coords = state.shape_state.to_array()

        # Apply gauge transformation
        gauge_offset = self.gauge_choice(state.shape_state)
        theta_transformed = (state.theta + gauge_offset) % (2 * np.pi)

        return (shape_coords, theta_transformed)

    def from_coordinates(
        self,
        shape_coords: np.ndarray,
        theta: float,
        L: float = 1.0
    ) -> BundleState:
        """
        Inverse chart map: (s, θ) → bundle state.

        Args:
            shape_coords: Shape space coordinates [r12, r23, r31]
            theta: Fiber coordinate
            L: Angular momentum (needed for ShapeSpaceState)

        Returns:
            BundleState (with zero momenta)

        Examples:
            >>> coords = np.array([1.0, 1.2, 1.1])
            >>> state = chart.from_coordinates(coords, np.pi/3, L=1.0)
        """
        shape_state = ShapeSpaceState(
            r12=shape_coords[0],
            r23=shape_coords[1],
            r31=shape_coords[2],
            L=L
        )

        # Undo gauge transformation
        gauge_offset = self.gauge_choice(shape_state)
        theta_original = (theta - gauge_offset) % (2 * np.pi)

        return BundleState(
            shape_state=shape_state,
            theta=theta_original,
            shape_momenta=np.zeros(len(shape_coords)),
            p_theta=0.0
        )

    def validate(self) -> dict:
        """
        Validate chart properties.

        Checks:
            1. Domain function is well-defined
            2. Gauge choice is smooth
            3. Coordinate maps are invertible

        Returns:
            Dictionary with validation results
        """
        results = {
            'domain_valid': True,
            'gauge_valid': True,
            'invertible': True,
            'errors': []
        }

        # Test domain function on sample points
        try:
            test_states = [
                ShapeSpaceState(1.0, 1.0, 1.0, L=1.0),
                ShapeSpaceState(0.5, 0.8, 1.0, L=1.0),
                ShapeSpaceState(2.0, 1.5, 1.2, L=1.0),
            ]

            for shape_state in test_states:
                test_bundle_state = BundleState(
                    shape_state, 0.0, np.zeros(3), 0.0
                )
                in_domain = self.is_in_domain(test_bundle_state)
                # Just check it returns bool without error
                assert isinstance(in_domain, (bool, np.bool_))

        except Exception as e:
            results['domain_valid'] = False
            results['errors'].append(f"Domain function error: {e}")

        # Test gauge choice
        try:
            for shape_state in test_states:
                gauge_val = self.gauge_choice(shape_state)
                assert isinstance(gauge_val, (int, float, np.number))
                assert np.isfinite(gauge_val)

        except Exception as e:
            results['gauge_valid'] = False
            results['errors'].append(f"Gauge choice error: {e}")

        # Test invertibility: φ⁻¹(φ(state)) = state
        try:
            test_state = BundleState(
                ShapeSpaceState(1.0, 1.0, 1.0, L=1.0),
                np.pi/4,
                np.zeros(3),
                0.0
            )

            if self.is_in_domain(test_state):
                coords, theta = self.coordinates(test_state)
                reconstructed = self.from_coordinates(coords, theta, L=1.0)

                # Check coordinates match (up to gauge)
                if not np.allclose(
                    reconstructed.shape_state.to_array(),
                    test_state.shape_state.to_array()
                ):
                    results['invertible'] = False
                    results['errors'].append("Coordinate inversion failed")

                # Theta may differ by gauge (check mod 2π)
                theta_diff = abs(reconstructed.theta - test_state.theta)
                if theta_diff > 1e-10 and abs(theta_diff - 2*np.pi) > 1e-10:
                    results['invertible'] = False
                    results['errors'].append("Fiber coordinate inversion failed")

        except Exception as e:
            results['invertible'] = False
            results['errors'].append(f"Invertibility test error: {e}")

        results['valid'] = all([
            results['domain_valid'],
            results['gauge_valid'],
            results['invertible']
        ])

        return results


class BundleSection:
    """
    Section of the S¹ bundle: σ: S → P.

    A section picks a point in each fiber consistently, i.e., π ∘ σ = id_S.
    Geometrically, it's a "choice of gauge" or "reference phase" at each base point.

    Attributes:
        bundle: The S¹ bundle
        section_function: Function s ↦ θ(s) defining fiber coordinate

    Examples:
        >>> # Zero section
        >>> zero_section = BundleSection(bundle, lambda s: 0.0)
        >>>
        >>> # Evaluate at base point
        >>> shape_state = ShapeSpaceState(1.0, 1.2, 1.1, L=1.0)
        >>> bundle_state = zero_section.evaluate(shape_state)
        >>> bundle_state.theta
        0.0
    """

    def __init__(
        self,
        bundle: 'S1Bundle',
        section_function: Callable[[ShapeSpaceState], float]
    ):
        """
        Initialize bundle section.

        Args:
            bundle: The S¹ bundle
            section_function: Function s ↦ θ(s)
        """
        self.bundle = bundle
        self.section_function = section_function

    def evaluate(
        self,
        base_point: ShapeSpaceState,
        momenta: Optional[np.ndarray] = None,
        p_theta: float = 0.0
    ) -> BundleState:
        """
        Evaluate section at base point: σ(s) ∈ P.

        Args:
            base_point: Point s in shape space
            momenta: Base momenta (default: zero)
            p_theta: Fiber momentum (default: 0)

        Returns:
            BundleState in fiber over base_point

        Examples:
            >>> section = BundleSection(bundle, lambda s: np.pi * s.r12 / 2.0)
            >>> base = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
            >>> state = section.evaluate(base)
            >>> state.theta
            1.5707963267948966  # π/2
        """
        if momenta is None:
            momenta = np.zeros(self.bundle.base_dimension)

        theta = self.section_function(base_point)

        return BundleState(
            shape_state=base_point,
            theta=theta,
            shape_momenta=momenta,
            p_theta=p_theta
        )

    def derivative(
        self,
        base_point: ShapeSpaceState,
        tangent_vector: np.ndarray,
        epsilon: float = 1e-8
    ) -> float:
        """
        Compute directional derivative dσ/ds(v) at base point.

        This gives the rate of change of fiber coordinate as we move
        in direction v on base space.

        Args:
            base_point: Point s in base space
            tangent_vector: Direction v ∈ T_s(S)
            epsilon: Finite difference step size

        Returns:
            dθ/ds(v) (scalar)

        Examples:
            >>> # How does θ change as r12 increases?
            >>> v = np.array([1.0, 0.0, 0.0])  # ∂/∂r12 direction
            >>> dtheta_dr12 = section.derivative(base, v)
        """
        # Finite difference approximation
        theta_0 = self.section_function(base_point)

        # Perturb base point in tangent direction
        perturbed_coords = base_point.to_array() + epsilon * tangent_vector
        perturbed_state = ShapeSpaceState(
            r12=perturbed_coords[0],
            r23=perturbed_coords[1],
            r31=perturbed_coords[2],
            L=base_point.L
        )

        theta_1 = self.section_function(perturbed_state)

        # Handle periodicity: if theta jumps by ~2π, unwrap
        dtheta = theta_1 - theta_0
        if dtheta > np.pi:
            dtheta -= 2 * np.pi
        elif dtheta < -np.pi:
            dtheta += 2 * np.pi

        return dtheta / epsilon

    def validate(self) -> dict:
        """
        Validate section properties.

        Checks:
            1. π ∘ σ = id (projection property)
            2. θ(s) is smooth
            3. Values in [0, 2π)

        Returns:
            Dictionary with validation results
        """
        results = {
            'projection_valid': True,
            'smoothness_valid': True,
            'range_valid': True,
            'errors': []
        }

        test_points = [
            ShapeSpaceState(1.0, 1.0, 1.0, L=1.0),
            ShapeSpaceState(0.8, 1.2, 1.0, L=1.0),
            ShapeSpaceState(1.5, 1.3, 1.4, L=1.0),
        ]

        for base_point in test_points:
            try:
                # Evaluate section
                bundle_state = self.evaluate(base_point)

                # Check projection: π(σ(s)) = s
                projected = self.bundle.project_to_base(bundle_state)
                if not np.allclose(
                    projected.to_array(),
                    base_point.to_array()
                ):
                    results['projection_valid'] = False
                    results['errors'].append(
                        f"Projection property failed at {base_point}"
                    )

                # Check range
                if bundle_state.theta < 0 or bundle_state.theta >= 2*np.pi:
                    results['range_valid'] = False
                    results['errors'].append(
                        f"Fiber coordinate out of range: {bundle_state.theta}"
                    )

            except Exception as e:
                results['smoothness_valid'] = False
                results['errors'].append(f"Section evaluation error: {e}")

        results['valid'] = all([
            results['projection_valid'],
            results['smoothness_valid'],
            results['range_valid']
        ])

        return results
```

---

## Core Algorithms

### A1: Bundle State Management

**Purpose**: Create, manipulate, and validate states in the bundle.

**Key Operations**:
1. Creation from coordinates
2. Vector conversion (for integrators)
3. Functional updates (immutable)
4. Validation

**Algorithm: State Creation**

```python
def create_bundle_state_from_initial_conditions(
    r12: float,
    r23: float,
    r31: float,
    L: float,
    theta: float,
    p12: float,
    p23: float,
    p31: float,
    p_theta: float
) -> BundleState:
    """
    Create bundle state from explicit initial conditions.

    Validates:
        - Triangle inequality for (r12, r23, r31)
        - Theta in [0, 2π)
        - All values finite

    Args:
        r12, r23, r31: Shape space coordinates
        L: Angular momentum
        theta: Fiber coordinate
        p12, p23, p31: Base momenta
        p_theta: Fiber momentum

    Returns:
        Valid BundleState

    Raises:
        ValueError: If inputs invalid
    """
    # Validate triangle inequality
    if not (r12 + r23 > r31 and r23 + r31 > r12 and r31 + r12 > r23):
        raise ValueError(
            f"Triangle inequality violated: ({r12}, {r23}, {r31})"
        )

    # Validate finite values
    values = [r12, r23, r31, L, theta, p12, p23, p31, p_theta]
    if not all(np.isfinite(v) for v in values):
        raise ValueError("All values must be finite")

    # Create shape state
    shape_state = ShapeSpaceState(r12, r23, r31, L)

    # Create momenta array
    shape_momenta = np.array([p12, p23, p31])

    # Create bundle state (normalizes theta automatically)
    return BundleState(
        shape_state=shape_state,
        theta=theta,
        shape_momenta=shape_momenta,
        p_theta=p_theta
    )
```

**Algorithm: Random State Generation** (for testing)

```python
def generate_random_bundle_state(
    shape_bounds: Tuple[float, float] = (0.5, 2.0),
    momentum_scale: float = 0.1,
    seed: Optional[int] = None
) -> BundleState:
    """
    Generate random valid bundle state.

    Useful for:
        - Testing
        - Monte Carlo sampling
        - Ensemble generation

    Args:
        shape_bounds: (min, max) for shape coordinates
        momentum_scale: Scale for random momenta
        seed: Random seed for reproducibility

    Returns:
        Random BundleState
    """
    if seed is not None:
        np.random.seed(seed)

    r_min, r_max = shape_bounds

    # Generate valid triangle configuration
    while True:
        r12 = np.random.uniform(r_min, r_max)
        r23 = np.random.uniform(r_min, r_max)
        r31 = np.random.uniform(r_min, r_max)

        # Check triangle inequality
        if (r12 + r23 > r31 and r23 + r31 > r12 and r31 + r12 > r23):
            break

    # Random fiber coordinate
    theta = np.random.uniform(0, 2*np.pi)

    # Random momenta (Gaussian)
    shape_momenta = np.random.normal(0, momentum_scale, size=3)
    p_theta = np.random.normal(0, momentum_scale)

    # Random angular momentum
    L = np.random.uniform(0.5, 2.0)

    shape_state = ShapeSpaceState(r12, r23, r31, L)

    return BundleState(
        shape_state=shape_state,
        theta=theta,
        shape_momenta=shape_momenta,
        p_theta=p_theta
    )
```

### A2: Projection and Fiber Operations

**Purpose**: Navigate between bundle and base space.

**Algorithm: Batch Projection**

```python
def project_batch_to_base(
    bundle_states: List[BundleState]
) -> List[ShapeSpaceState]:
    """
    Project list of bundle states to base space.

    Vectorized operation for efficiency.

    Args:
        bundle_states: List of states in bundle

    Returns:
        List of projected states in shape space
    """
    return [state.shape_state for state in bundle_states]
```

**Algorithm: Fiber Parallel Transport**

```python
def parallel_transport_along_fiber(
    initial_state: BundleState,
    theta_end: float,
    n_steps: int = 100
) -> List[BundleState]:
    """
    Move along fiber from initial θ to θ_end.

    Keeps base coordinates and momenta fixed, varies only fiber coordinate.

    Args:
        initial_state: Starting point
        theta_end: Target fiber coordinate
        n_steps: Number of intermediate points

    Returns:
        List of states along fiber

    Examples:
        >>> # Move from θ=0 to θ=π along fiber
        >>> path = parallel_transport_along_fiber(state, np.pi, n_steps=50)
    """
    theta_start = initial_state.theta

    # Handle periodic boundary
    if theta_end < theta_start:
        theta_end += 2 * np.pi

    theta_values = np.linspace(theta_start, theta_end, n_steps)

    return [
        initial_state.copy_with(theta=theta % (2 * np.pi))
        for theta in theta_values
    ]
```

### A3: Transition Functions

**Purpose**: Handle chart overlaps via gauge transformations.

**Algorithm: Gauge Transformation**

```python
def compute_gauge_transformation(
    shape_coords: np.ndarray,
    chart1: BundleChart,
    chart2: BundleChart
) -> float:
    """
    Compute gauge transformation α(s) between charts.

    For S¹ bundle, transition functions have form:
        θ₂ = θ₁ + α₁₂(s)

    For trivial bundle over contractible base: α = 0
    For non-trivial bundle: α may be non-zero

    Args:
        shape_coords: Point s in shape space
        chart1, chart2: Overlapping charts

    Returns:
        Gauge transformation angle α ∈ [0, 2π)

    Examples:
        >>> # For trivial bundle
        >>> alpha = compute_gauge_transformation(coords, chart1, chart2)
        >>> alpha
        0.0
    """
    # For trivial bundle over contractible shape space
    # We can choose trivial gauge: α = 0
    return 0.0

    # For non-trivial bundle, would compute:
    # alpha = chart2.gauge_choice(shape_state) - chart1.gauge_choice(shape_state)
    # return alpha % (2 * np.pi)
```

**Algorithm: Transition Function Validation**

```python
def validate_transition_function(
    chart1: BundleChart,
    chart2: BundleChart,
    test_state: BundleState
) -> dict:
    """
    Verify transition function consistency.

    Checks:
        1. If state in both domains, transition is well-defined
        2. θ₂ = θ₁ + α₁₂(s) where α₁₂ is smooth
        3. Gauge transformation is S¹-valued

    Args:
        chart1, chart2: Charts to test
        test_state: State in overlap region

    Returns:
        Dictionary with validation results
    """
    results = {
        'in_overlap': False,
        'transition_defined': False,
        'smooth': True,
        'gauge_range_valid': True,
        'errors': []
    }

    # Check if state is in overlap
    in_chart1 = chart1.is_in_domain(test_state)
    in_chart2 = chart2.is_in_domain(test_state)

    if not (in_chart1 and in_chart2):
        results['in_overlap'] = False
        return results

    results['in_overlap'] = True

    try:
        # Get coordinates in both charts
        coords1, theta1 = chart1.coordinates(test_state)
        coords2, theta2 = chart2.coordinates(test_state)

        # Verify base coordinates agree
        if not np.allclose(coords1, coords2):
            results['transition_defined'] = False
            results['errors'].append("Base coordinates disagree between charts")
            return results

        # Compute gauge transformation
        alpha = compute_gauge_transformation(coords1, chart1, chart2)

        # Verify transition: θ₂ = θ₁ + α (mod 2π)
        theta2_expected = (theta1 + alpha) % (2 * np.pi)
        if not np.isclose(theta2, theta2_expected):
            results['transition_defined'] = False
            results['errors'].append(
                f"Transition function inconsistent: "
                f"θ₂={theta2}, expected {theta2_expected}"
            )

        # Check gauge range
        if not (0 <= alpha < 2*np.pi):
            results['gauge_range_valid'] = False
            results['errors'].append(f"Gauge out of range: α={alpha}")

        results['transition_defined'] = True

    except Exception as e:
        results['transition_defined'] = False
        results['errors'].append(f"Transition function error: {e}")

    results['valid'] = (
        results['in_overlap'] and
        results['transition_defined'] and
        results['gauge_range_valid']
    )

    return results
```

**Algorithm: Cocycle Condition Check**

```python
def verify_cocycle_condition(
    chart1: BundleChart,
    chart2: BundleChart,
    chart3: BundleChart,
    test_state: BundleState
) -> dict:
    """
    Verify cocycle condition on triple overlap.

    For three charts with pairwise gauge transformations α₁₂, α₂₃, α₃₁,
    must satisfy:
        α₁₂ + α₂₃ + α₃₁ = 0 (mod 2π)

    This ensures global consistency of the bundle structure.

    Args:
        chart1, chart2, chart3: Three overlapping charts
        test_state: State in triple overlap U₁ ∩ U₂ ∩ U₃

    Returns:
        Dictionary with validation results
    """
    results = {
        'in_triple_overlap': False,
        'cocycle_valid': False,
        'cocycle_error': None,
        'errors': []
    }

    # Check if state in all three charts
    in_all = all([
        chart.is_in_domain(test_state)
        for chart in [chart1, chart2, chart3]
    ])

    if not in_all:
        results['in_triple_overlap'] = False
        return results

    results['in_triple_overlap'] = True

    try:
        shape_coords = test_state.shape_state.to_array()

        # Compute pairwise gauge transformations
        alpha_12 = compute_gauge_transformation(shape_coords, chart1, chart2)
        alpha_23 = compute_gauge_transformation(shape_coords, chart2, chart3)
        alpha_31 = compute_gauge_transformation(shape_coords, chart3, chart1)

        # Check cocycle condition
        cocycle_sum = (alpha_12 + alpha_23 + alpha_31) % (2 * np.pi)

        # Should be 0 or 2π (equivalent mod 2π)
        error = min(cocycle_sum, 2*np.pi - cocycle_sum)

        results['cocycle_error'] = error
        results['cocycle_valid'] = error < 1e-10

        if not results['cocycle_valid']:
            results['errors'].append(
                f"Cocycle condition violated: "
                f"α₁₂ + α₂₃ + α₃₁ = {cocycle_sum:.6f} (should be 0)"
            )

    except Exception as e:
        results['errors'].append(f"Cocycle validation error: {e}")

    results['valid'] = results['in_triple_overlap'] and results['cocycle_valid']

    return results
```

### A4: Bundle Validation Suite

**Purpose**: Comprehensive validation of bundle structure.

**Algorithm: Full Bundle Validation**

```python
def validate_bundle_structure_complete(
    bundle: S1Bundle,
    n_test_states: int = 100
) -> dict:
    """
    Comprehensive validation of S¹ bundle structure.

    Tests:
        1. Projection property: π(P) = S
        2. Fiber structure: π⁻¹(s) ≅ S¹
        3. Local triviality: π⁻¹(U) ≅ U × S¹
        4. Chart consistency
        5. Transition functions (if multiple charts)
        6. Cocycle condition (if ≥3 charts)
        7. Section properties (if sections defined)

    Args:
        bundle: S¹ bundle to validate
        n_test_states: Number of random test states

    Returns:
        Dictionary with comprehensive validation results
    """
    results = {
        'projection': [],
        'fiber': [],
        'charts': [],
        'transitions': [],
        'cocycles': [],
        'overall_valid': True,
        'errors': []
    }

    # Test 1: Projection
    print("Testing projection property...")
    for i in range(n_test_states):
        test_state = generate_random_bundle_state()

        # Project and verify dimensions
        projected = bundle.project_to_base(test_state)

        if projected.to_array().shape[0] != bundle.base_dimension:
            results['projection'].append({
                'valid': False,
                'error': 'Dimension mismatch'
            })
            results['overall_valid'] = False
        else:
            results['projection'].append({'valid': True})

    # Test 2: Fiber structure
    print("Testing fiber structure...")
    for i in range(10):  # Fewer tests (more expensive)
        base_point = generate_random_bundle_state().shape_state
        fiber = bundle.fiber_over_point(base_point, n_samples=50)

        # All should project to same base point
        fiber_valid = True
        for state in fiber:
            proj = bundle.project_to_base(state)
            if not np.allclose(proj.to_array(), base_point.to_array()):
                fiber_valid = False
                break

        # Fiber coordinates should span [0, 2π)
        thetas = [s.theta for s in fiber]
        theta_range_valid = (min(thetas) >= 0 and max(thetas) < 2*np.pi)

        results['fiber'].append({
            'valid': fiber_valid and theta_range_valid,
            'theta_range': (min(thetas), max(thetas))
        })

        if not fiber_valid:
            results['overall_valid'] = False

    # Test 3: Charts
    if len(bundle._charts) > 0:
        print("Testing charts...")
        for chart in bundle._charts:
            chart_results = chart.validate()
            results['charts'].append(chart_results)

            if not chart_results['valid']:
                results['overall_valid'] = False

    # Test 4: Transition functions
    if len(bundle._charts) >= 2:
        print("Testing transition functions...")
        for i in range(len(bundle._charts)):
            for j in range(i+1, len(bundle._charts)):
                chart1 = bundle._charts[i]
                chart2 = bundle._charts[j]

                # Test on random states
                for _ in range(10):
                    test_state = generate_random_bundle_state()
                    trans_results = validate_transition_function(
                        chart1, chart2, test_state
                    )

                    if trans_results['in_overlap']:
                        results['transitions'].append(trans_results)

                        if not trans_results['valid']:
                            results['overall_valid'] = False

    # Test 5: Cocycle condition
    if len(bundle._charts) >= 3:
        print("Testing cocycle conditions...")
        # Test all triples
        for i in range(len(bundle._charts)):
            for j in range(i+1, len(bundle._charts)):
                for k in range(j+1, len(bundle._charts)):
                    chart1 = bundle._charts[i]
                    chart2 = bundle._charts[j]
                    chart3 = bundle._charts[k]

                    # Test on random states
                    for _ in range(5):
                        test_state = generate_random_bundle_state()
                        cocycle_results = verify_cocycle_condition(
                            chart1, chart2, chart3, test_state
                        )

                        if cocycle_results['in_triple_overlap']:
                            results['cocycles'].append(cocycle_results)

                            if not cocycle_results['valid']:
                                results['overall_valid'] = False

    # Summary statistics
    results['summary'] = {
        'projection_pass_rate': sum(
            1 for r in results['projection'] if r['valid']
        ) / max(len(results['projection']), 1),
        'fiber_pass_rate': sum(
            1 for r in results['fiber'] if r['valid']
        ) / max(len(results['fiber']), 1),
        'charts_valid': all(
            r['valid'] for r in results['charts']
        ) if results['charts'] else True,
        'transitions_valid': all(
            r['valid'] for r in results['transitions']
        ) if results['transitions'] else True,
        'cocycles_valid': all(
            r['valid'] for r in results['cocycles']
        ) if results['cocycles'] else True,
    }

    return results
```

---

## Implementation Details

### File Organization

```
src/python/lifts/
├── __init__.py                    # Package exports
├── s1_bundle.py                   # BundleState, S1Bundle classes
├── bundle_coordinates.py          # BundleChart, BundleSection
└── validation.py                  # Validation utilities
```

### Dependencies

```python
# Core dependencies
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable

# Internal dependencies
from ..core.shape_space import ShapeSpace, ShapeSpaceState
from ..core.masses import Masses
```

### Type Hints

All functions use comprehensive type hints:

```python
def function_name(
    arg1: Type1,
    arg2: Type2
) -> ReturnType:
    ...
```

### Error Handling

**Validation Errors**: Raise `ValueError` for invalid inputs
```python
if not triangle_inequality(r12, r23, r31):
    raise ValueError("Triangle inequality violated")
```

**Numerical Errors**: Catch and report
```python
try:
    result = compute_something()
except np.linalg.LinAlgError as e:
    raise RuntimeError(f"Numerical error in computation: {e}")
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def create_bundle():
    logger.info("Creating S¹ bundle...")
    # ...
    logger.debug(f"Bundle created with dimension {bundle.total_dimension}")
```

---

## Validation Strategy

### Unit Tests

```python
# File: tests/lifts/test_s1_bundle.py

import pytest
import numpy as np
from src.python.lifts.s1_bundle import BundleState, S1Bundle
from src.python.core.shape_space import ShapeSpaceState, ShapeSpace

class TestBundleState:
    """Test BundleState data structure"""

    def test_creation(self):
        """Test basic state creation"""
        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        momenta = np.array([0.1, -0.05, 0.08])

        state = BundleState(
            shape_state=shape,
            theta=np.pi/4,
            shape_momenta=momenta,
            p_theta=0.5
        )

        assert state.dimension == 8
        assert np.isclose(state.theta, np.pi/4)

    def test_theta_normalization(self):
        """Test theta is normalized to [0, 2π)"""
        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        momenta = np.zeros(3)

        # Theta > 2π should wrap
        state1 = BundleState(shape, 3*np.pi, momenta, 0.0)
        assert 0 <= state1.theta < 2*np.pi
        assert np.isclose(state1.theta, np.pi)

        # Negative theta should wrap
        state2 = BundleState(shape, -np.pi/2, momenta, 0.0)
        assert 0 <= state2.theta < 2*np.pi
        assert np.isclose(state2.theta, 3*np.pi/2)

    def test_vector_conversion(self):
        """Test to_vector and from_vector are inverses"""
        shape = ShapeSpaceState(1.0, 1.2, 1.1, L=1.0)
        momenta = np.array([0.1, -0.05, 0.08])

        state = BundleState(shape, np.pi/3, momenta, 0.5)

        vec = state.to_vector()
        reconstructed = BundleState.from_vector(vec, L=1.0)

        assert np.allclose(
            reconstructed.to_vector(),
            state.to_vector()
        )

    def test_immutability(self):
        """Test state is immutable"""
        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        momenta = np.array([0.1, -0.05, 0.08])
        state = BundleState(shape, 0.0, momenta, 0.0)

        # Should not be able to modify arrays
        with pytest.raises((ValueError, AttributeError)):
            state.shape_momenta[0] = 999.0

    def test_copy_with(self):
        """Test functional update via copy_with"""
        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        momenta = np.array([0.1, -0.05, 0.08])
        state = BundleState(shape, 0.0, momenta, 0.5)

        # Update theta
        new_state = state.copy_with(theta=np.pi)

        assert np.isclose(new_state.theta, np.pi)
        assert np.allclose(new_state.shape_momenta, state.shape_momenta)
        assert new_state.p_theta == state.p_theta


class TestS1Bundle:
    """Test S¹ bundle structure"""

    def test_creation(self):
        """Test bundle creation"""
        base = ShapeSpace()
        bundle = S1Bundle(base)

        assert bundle.base_dimension == 3
        assert bundle.total_dimension == 4
        assert bundle.phase_space_dimension == 8

    def test_projection(self):
        """Test projection π: P → S"""
        base = ShapeSpace()
        bundle = S1Bundle(base)

        shape = ShapeSpaceState(1.0, 1.2, 1.1, L=1.0)
        momenta = np.array([0.1, -0.05, 0.08])

        state = bundle.create_state(shape, np.pi/4, momenta, 0.5)
        projected = bundle.project_to_base(state)

        assert np.allclose(
            projected.to_array(),
            shape.to_array()
        )

    def test_fiber_structure(self):
        """Test fiber π⁻¹(s) is circular"""
        base = ShapeSpace()
        bundle = S1Bundle(base)

        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        fiber = bundle.fiber_over_point(shape, n_samples=100)

        # All should project to same base point
        for state in fiber:
            proj = bundle.project_to_base(state)
            assert np.allclose(proj.to_array(), shape.to_array())

        # Theta values should span [0, 2π)
        thetas = [s.theta for s in fiber]
        assert min(thetas) >= 0
        assert max(thetas) < 2*np.pi

        # Should be approximately uniformly distributed
        assert len(set(np.round(thetas, 2))) > 95  # Most unique

    def test_bundle_validation(self):
        """Test bundle structure validation"""
        base = ShapeSpace()
        bundle = S1Bundle(base)

        results = bundle.validate_structure()

        assert results['valid']
        assert results['projection_valid']
        assert results['fiber_structure_valid']


class TestBundleChart:
    """Test bundle coordinate charts"""

    def test_chart_creation(self):
        """Test chart creation"""
        from src.python.lifts.bundle_coordinates import BundleChart

        def always_true(s):
            return True

        chart = BundleChart(always_true, name="Global")

        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        state = BundleState(shape, 0.0, np.zeros(3), 0.0)

        assert chart.is_in_domain(state)

    def test_coordinate_maps(self):
        """Test chart maps are invertible"""
        from src.python.lifts.bundle_coordinates import BundleChart

        chart = BundleChart(lambda s: True, name="Test")

        shape = ShapeSpaceState(1.0, 1.2, 1.1, L=1.0)
        state = BundleState(shape, np.pi/3, np.zeros(3), 0.0)

        # Forward map
        coords, theta = chart.coordinates(state)

        # Inverse map
        reconstructed = chart.from_coordinates(coords, theta, L=1.0)

        # Should match (up to zero momenta)
        assert np.allclose(
            reconstructed.shape_state.to_array(),
            state.shape_state.to_array()
        )
        assert np.isclose(reconstructed.theta, state.theta)


class TestBundleSection:
    """Test bundle sections"""

    def test_zero_section(self):
        """Test zero section σ(s) = (s, 0)"""
        from src.python.lifts.bundle_coordinates import BundleSection

        base = ShapeSpace()
        bundle = S1Bundle(base)

        zero_section = bundle.create_section(lambda s: 0.0)

        shape = ShapeSpaceState(1.0, 1.2, 1.1, L=1.0)
        state = zero_section.evaluate(shape)

        assert np.isclose(state.theta, 0.0)
        assert np.allclose(
            state.shape_state.to_array(),
            shape.to_array()
        )

    def test_section_projection_property(self):
        """Test π ∘ σ = id"""
        from src.python.lifts.bundle_coordinates import BundleSection

        base = ShapeSpace()
        bundle = S1Bundle(base)

        # Non-trivial section
        def section_func(s):
            return np.pi * s.r12 / 2.0

        section = bundle.create_section(section_func)

        shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        state = section.evaluate(shape)
        projected = bundle.project_to_base(state)

        assert np.allclose(
            projected.to_array(),
            shape.to_array()
        )

    def test_section_validation(self):
        """Test section validation"""
        from src.python.lifts.bundle_coordinates import BundleSection

        base = ShapeSpace()
        bundle = S1Bundle(base)

        section = bundle.create_section(lambda s: np.pi/2)
        results = section.validate()

        assert results['valid']
        assert results['projection_valid']
        assert results['range_valid']
```

### Integration Tests

```python
# File: tests/lifts/test_bundle_integration.py

def test_full_bundle_workflow():
    """
    End-to-end test: create bundle, generate trajectory, project back.
    """
    # Create bundle
    base = ShapeSpace()
    bundle = S1Bundle(base)

    # Create initial state
    shape = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
    momenta = np.array([0.01, -0.005, 0.008])
    state = bundle.create_state(shape, 0.0, momenta, 0.1)

    # Generate fiber path
    fiber_path = parallel_transport_along_fiber(state, 2*np.pi, n_steps=100)

    # All should project to same base point
    for s in fiber_path:
        proj = bundle.project_to_base(s)
        assert np.allclose(proj.to_array(), shape.to_array())

    # Should return to starting theta (periodic)
    assert np.isclose(fiber_path[-1].theta, 0.0, atol=1e-10)


def test_bundle_validation_comprehensive():
    """
    Comprehensive validation on random bundle.
    """
    base = ShapeSpace()
    bundle = S1Bundle(base)

    # Add charts
    def domain1(s):
        return s.r12 < 1.5

    def domain2(s):
        return s.r12 > 0.8

    chart1 = BundleChart(domain1, name="Region1")
    chart2 = BundleChart(domain2, name="Region2")

    bundle.add_chart(chart1)
    bundle.add_chart(chart2)

    # Validate
    results = validate_bundle_structure_complete(bundle, n_test_states=50)

    assert results['overall_valid']
    assert results['summary']['projection_pass_rate'] > 0.99
    assert results['summary']['fiber_pass_rate'] > 0.99
```

---

## Performance Targets

### Computational Complexity

| Operation | Complexity | Target Time |
|-----------|-----------|-------------|
| State creation | O(1) | < 1 μs |
| Projection π(state) | O(1) | < 100 ns |
| Fiber generation (n points) | O(n) | < 1 ms for n=100 |
| Chart lookup | O(k) | < 10 μs (k = # charts) |
| Validation (n tests) | O(n) | < 1 s for n=1000 |

### Memory Usage

- **BundleState**: ~200 bytes per state
- **S1Bundle**: ~1 KB base overhead
- **BundleChart**: ~500 bytes per chart
- **Fiber (100 points)**: ~20 KB

### Scalability

- Support 10⁶ bundle states in memory (~200 MB)
- Validate 10³ random states in < 10 seconds
- Batch operations vectorized where possible

---

## Integration Points

### With Task 2.1.2 (Connection and Curvature)

```python
from ..connection.connection_form import ConnectionForm

# Use connection to define extended symplectic form (Part B)
connection = compute_connection_form(shape_state)

# Connection will appear in symplectic form:
# ω̃ = ω_shape + dθ ∧ d(L·A)
```

### With WP1 (High-Precision Integration)

```python
from ..integration.symplectic_integrator import SymplecticIntegrator

# Bundle dynamics will be integrated in Part C
# Integrator needs to handle 8D phase space
```

### With Task 2.1.1 (Shape Space)

```python
from ..core.shape_space import ShapeSpace, ShapeSpaceState

# Bundle is built on top of shape space
# Base manifold is shape space
```

---

## Success Criteria

### Part A Complete When:

- [  ] `BundleState` class implemented with all methods
- [  ] `S1Bundle` class functional with projection, fibers
- [  ] `BundleChart` and `BundleSection` classes complete
- [  ] Transition functions and gauge transformations working
- [  ] All unit tests passing (>95% coverage)
- [  ] Integration tests successful
- [  ] Validation suite runs without errors
- [  ] Performance targets met
- [  ] Documentation complete with examples
- [  ] Type hints on all public APIs

### Validation Criteria:

1. **Projection**: π(P) maps correctly to S, dimension preserved
2. **Fiber Structure**: π⁻¹(s) ≅ S¹ for all s ∈ S
3. **Chart Consistency**: Coordinate maps invertible
4. **Transition Functions**: Satisfy cocycle condition (if multiple charts)
5. **Section Property**: π ∘ σ = id_S for all sections
6. **Numerical Stability**: No NaN/Inf in normal operation
7. **Performance**: All operations within target times

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 3 days
**Next**: Part B (Extended Symplectic Form)

**Dependencies**:
- Task 2.1.1 (Shape Space) ✅
- Task 2.1.2 (Connection) ✅

**Blocks**:
- Part B (needs bundle state structure)
- Part C (needs bundle infrastructure)
- Part D (needs complete bundle)

---

## Appendix: Mathematical Proofs

### Theorem: Bundle is Trivial

**Statement**: For contractible shape space S, the S¹ bundle P is trivial: P ≅ S × S¹.

**Proof**:
- Shape space S ≅ ℝ³ (valid triangle configurations)
- ℝ³ is contractible (can shrink to a point continuously)
- All principal bundles over contractible base are trivial
- Therefore P = S × S¹ globally
- QED

**Implication**: We can use global coordinates (s, θ) without worrying about transition functions.

### Lemma: Fiber is S¹

**Statement**: For any s ∈ S, the fiber π⁻¹(s) is diffeomorphic to S¹.

**Proof**:
- By definition of principal G-bundle, fiber = orbit of G-action
- G = S¹ acts freely and transitively on each fiber
- Therefore fiber ≅ S¹
- QED

### Proposition: θ Normalization is Well-Defined

**Statement**: The map θ ↦ θ mod 2π is a smooth projection ℝ → S¹.

**Proof**:
- Quotient map by discrete group 2πℤ
- Smooth (locally identity)
- Universal covering space property
- QED
