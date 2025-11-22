"""
Poincaré Section Utilities for CR3BP (WP1 Phase 5).

Implements standard Poincaré sections for the Circular Restricted Three-Body Problem.
Used for:
- Phase space visualization
- Periodic orbit detection
- Comparison with literature results

Mathematical Background:
========================

Poincaré Section:
-----------------
A (2n-1)-dimensional hypersurface Σ in 2n-dimensional phase space,
intersected transversally by trajectories.

Standard CR3BP Sections:
------------------------
1. **y = 0, vy > 0**: x-vx section (most common)
2. **x = x₀**: Perpendicular to x-axis
3. **z = 0, vz > 0**: Equatorial section (for 3D orbits)

Return Map:
-----------
P: Σ → Σ maps one crossing to the next.
Fixed points of P correspond to periodic orbits.

References:
-----------
- Koon, Lo, Marsden, Ross (2000): "Dynamical Systems, the Three-Body Problem
  and Space Mission Design"
- Contopoulos (2002): "Order and Chaos in Dynamical Astronomy"
- WP1 Specification, Section 2.5 (Poincaré Section Utilities)
"""

from dataclasses import dataclass
from typing import List, Callable, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class PoincareCrossing:
    """
    Single Poincaré section crossing.

    Attributes:
        time: Time of crossing
        state: Full state at crossing (6D)
        section_coords: Coordinates on section (4D for CR3BP)
        crossing_number: Sequential crossing number
    """
    time: float
    state: np.ndarray  # (6,)
    section_coords: np.ndarray  # (4,)
    crossing_number: int


class PoincareSection:
    """
    Poincaré section for CR3BP.

    Detects and records crossings of specified hypersurface.
    """

    def __init__(
        self,
        section_type: str = "y_zero_positive",
        section_value: float = 0.0,
        tolerance: float = 1e-10
    ):
        """
        Initialize Poincaré section.

        Args:
            section_type: Type of section
                - "y_zero_positive": y=0, vy>0 (standard)
                - "x_fixed": x=section_value
                - "z_zero_positive": z=0, vz>0
            section_value: Value for fixed coordinate (if applicable)
            tolerance: Tolerance for detecting crossings
        """
        self.section_type = section_type
        self.section_value = section_value
        self.tolerance = tolerance

        logger.info(f"Initialized Poincare section: {section_type}")

    def _check_crossing(
        self,
        state1: np.ndarray,
        state2: np.ndarray
    ) -> bool:
        """
        Check if trajectory crosses section between two states.

        Args:
            state1: State before
            state2: State after

        Returns:
            True if crossing detected
        """
        if self.section_type == "y_zero_positive":
            # Check if y crosses zero and vy > 0
            y1, y2 = state1[1], state2[1]
            vy1, vy2 = state1[4], state2[4]

            # Sign change in y and positive vy
            crosses_y = (y1 * y2 <= 0)
            positive_vy = (vy1 > 0 or vy2 > 0)  # At least one positive

            return crosses_y and positive_vy

        elif self.section_type == "x_fixed":
            # Check if x crosses x_fixed
            x1, x2 = state1[0], state2[0]
            crosses = (x1 - self.section_value) * (x2 - self.section_value) <= 0
            return crosses

        elif self.section_type == "z_zero_positive":
            # Check if z crosses zero and vz > 0
            z1, z2 = state1[2], state2[2]
            vz1, vz2 = state1[5], state2[5]

            crosses_z = (z1 * z2 <= 0)
            positive_vz = (vz1 > 0 or vz2 > 0)

            return crosses_z and positive_vz

        else:
            raise ValueError(f"Unknown section type: {self.section_type}")

    def _interpolate_crossing(
        self,
        t1: float,
        state1: np.ndarray,
        t2: float,
        state2: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        """
        Interpolate exact crossing point via linear interpolation.

        Args:
            t1: Time before crossing
            state1: State before crossing
            t2: Time after crossing
            state2: State after crossing

        Returns:
            (crossing_time, crossing_state)
        """
        if self.section_type == "y_zero_positive":
            # Interpolate to y = 0
            y1, y2 = state1[1], state2[1]

            if np.abs(y2 - y1) < 1e-15:
                # Parallel to section
                alpha = 0.5
            else:
                alpha = -y1 / (y2 - y1)

        elif self.section_type == "x_fixed":
            # Interpolate to x = section_value
            x1, x2 = state1[0], state2[0]

            if np.abs(x2 - x1) < 1e-15:
                alpha = 0.5
            else:
                alpha = (self.section_value - x1) / (x2 - x1)

        elif self.section_type == "z_zero_positive":
            # Interpolate to z = 0
            z1, z2 = state1[2], state2[2]

            if np.abs(z2 - z1) < 1e-15:
                alpha = 0.5
            else:
                alpha = -z1 / (z2 - z1)

        else:
            raise ValueError(f"Unknown section type: {self.section_type}")

        # Clamp alpha to [0, 1]
        alpha = np.clip(alpha, 0.0, 1.0)

        # Linear interpolation
        t_cross = t1 + alpha * (t2 - t1)
        state_cross = state1 + alpha * (state2 - state1)

        return t_cross, state_cross

    def _get_section_coordinates(self, state: np.ndarray) -> np.ndarray:
        """
        Extract coordinates on Poincaré section.

        For CR3BP (6D phase space), section is 4D.

        Args:
            state: Full 6D state

        Returns:
            4D section coordinates
        """
        if self.section_type == "y_zero_positive":
            # Section: (x, z, vx, vz) with y=0, vy>0
            return np.array([state[0], state[2], state[3], state[5]])

        elif self.section_type == "x_fixed":
            # Section: (y, z, vy, vz) with x=fixed
            return np.array([state[1], state[2], state[4], state[5]])

        elif self.section_type == "z_zero_positive":
            # Section: (x, y, vx, vy) with z=0, vz>0
            return np.array([state[0], state[1], state[3], state[4]])

        else:
            raise ValueError(f"Unknown section type: {self.section_type}")

    def find_crossings(
        self,
        times: np.ndarray,
        states: np.ndarray
    ) -> List[PoincareCrossing]:
        """
        Find all Poincaré section crossings in trajectory.

        Args:
            times: Time array (N,)
            states: State array (N, 6)

        Returns:
            List of PoincareCrossing objects
        """
        crossings = []
        n_points = len(times)

        logger.info(f"Searching for Poincaré crossings in {n_points} points...")

        for i in range(n_points - 1):
            if self._check_crossing(states[i], states[i+1]):
                # Interpolate exact crossing
                t_cross, state_cross = self._interpolate_crossing(
                    times[i], states[i],
                    times[i+1], states[i+1]
                )

                # Get section coordinates
                section_coords = self._get_section_coordinates(state_cross)

                # Create crossing object
                crossing = PoincareCrossing(
                    time=t_cross,
                    state=state_cross,
                    section_coords=section_coords,
                    crossing_number=len(crossings)
                )

                crossings.append(crossing)

        logger.info(f"Found {len(crossings)} crossings")
        return crossings

    def compute_return_map(
        self,
        crossings: List[PoincareCrossing]
    ) -> np.ndarray:
        """
        Compute return map: P_i → P_{i+1}.

        Args:
            crossings: List of section crossings

        Returns:
            Return map array (n_crossings-1, 8)
            Each row: [x_i, z_i, vx_i, vz_i, x_{i+1}, z_{i+1}, vx_{i+1}, vz_{i+1}]
        """
        n_crossings = len(crossings)

        if n_crossings < 2:
            logger.warning("Need at least 2 crossings for return map")
            return np.array([])

        return_map = np.zeros((n_crossings - 1, 8))

        for i in range(n_crossings - 1):
            coords_i = crossings[i].section_coords
            coords_ip1 = crossings[i+1].section_coords

            return_map[i, :4] = coords_i
            return_map[i, 4:] = coords_ip1

        return return_map


def plot_poincare_section(
    crossings: List[PoincareCrossing],
    plot_dims: Tuple[int, int] = (0, 2),
    title: str = "Poincaré Section",
    **kwargs
):
    """
    Plot 2D projection of Poincaré section.

    Args:
        crossings: List of crossings
        plot_dims: Which dimensions to plot (0=x/y, 1=z, 2=vx/vy, 3=vz)
        title: Plot title
        **kwargs: Additional matplotlib arguments
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available, cannot plot")
        return

    if not crossings:
        logger.warning("No crossings to plot")
        return

    # Extract coordinates
    coords = np.array([c.section_coords for c in crossings])

    dim_labels = ['x/y', 'z', 'vx/vy', 'vz']

    plt.figure(figsize=(8, 6))
    plt.scatter(coords[:, plot_dims[0]], coords[:, plot_dims[1]], **kwargs)
    plt.xlabel(dim_labels[plot_dims[0]])
    plt.ylabel(dim_labels[plot_dims[1]])
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    return plt.gcf()


# Standard CR3BP sections (pre-configured)


def create_standard_y_section() -> PoincareSection:
    """Create standard y=0, vy>0 section."""
    return PoincareSection(section_type="y_zero_positive")


def create_lagrange_point_section(L_point: str, mu: float) -> PoincareSection:
    """
    Create section through Lagrange point.

    Args:
        L_point: "L1", "L2", "L3", "L4", or "L5"
        mu: Mass parameter

    Returns:
        PoincareSection through specified Lagrange point
    """
    # Approximate Lagrange point positions (simplified)
    L_positions = {
        "L1": 1.0 - mu - (mu/3.0)**(1.0/3.0),
        "L2": 1.0 - mu + (mu/3.0)**(1.0/3.0),
        "L3": -1.0 - mu - (5.0*mu/12.0),
    }

    if L_point in L_positions:
        x_L = L_positions[L_point]
        return PoincareSection(section_type="x_fixed", section_value=x_L)
    else:
        raise ValueError(f"L4 and L5 sections require 2D implementation")
