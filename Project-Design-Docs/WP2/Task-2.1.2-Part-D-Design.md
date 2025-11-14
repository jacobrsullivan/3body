# Task 2.1.2 Part D: Visualization and Validation - Detailed Design

**Task**: WP 2.1.2 - Computation of the "Magnetic Twist" (Connection and Curvature)
**Part**: D - Visualization & Validation
**Status**: Design Phase
**Estimated Duration**: 2-3 days
**Dependencies**: Task 2.1.2 Parts A, B, C Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Visualization Requirements](#visualization-requirements)
3. [D1: Connection Vector Field Plots](#d1-connection-vector-field-plots)
4. [D2: Curvature Heatmaps](#d2-curvature-heatmaps)
5. [D3: Interactive Exploration Tools](#d3-interactive-exploration-tools)
6. [D4: Validation: Stokes' Theorem](#d4-validation-stokes-theorem)
7. [D5: Additional Validation Tests](#d5-additional-validation-tests)
8. [Implementation Details](#implementation-details)
9. [Publication Quality Figures](#publication-quality-figures)
10. [Integration Guide](#integration-guide)

---

## Overview

### Purpose

Part D provides visualization and validation infrastructure for the connection and curvature computations. This includes:

1. **Scientific Visualizations** - Understanding geometric structure
2. **Interactive Tools** - Exploring shape space dynamics
3. **Rigorous Validation** - Verifying theoretical properties
4. **Publication Figures** - High-quality graphics for papers

### Key Goals

- **Visual Clarity**: Make abstract geometry intuitive
- **Mathematical Rigor**: Validate all theoretical properties
- **Interactive Exploration**: Enable rapid hypothesis testing
- **Publication Quality**: Camera-ready figures for papers

### Deliverables

- `src/python/visualization/connection_field.py` - Vector field plots
- `src/python/visualization/curvature_heatmap.py` - Curvature magnitude maps
- `src/python/visualization/interactive.py` - Interactive exploration
- `src/python/validation/stokes_theorem.py` - Stokes' theorem validator
- `tests/validation/test_theoretical_properties.py` - Comprehensive validation
- Gallery of publication-quality figures

---

## Visualization Requirements

### Scientific Requirements

1. **Accuracy**: Visualizations must faithfully represent mathematical objects
2. **Clarity**: Complex geometry presented intuitively
3. **Completeness**: All relevant aspects shown (magnitude, direction, singularities)
4. **Validation**: Visual checks of theoretical properties

### Technical Requirements

1. **Performance**: Real-time interaction for exploration
2. **Resolution**: High-resolution grids for publication figures
3. **Color Maps**: Perceptually uniform, colorblind-friendly
4. **Annotations**: Clear labels, scales, and legends

### Output Formats

- **Interactive**: Jupyter notebooks with widgets
- **Static**: PDF/PNG for papers (300 DPI minimum)
- **Animated**: MP4/GIF for presentations
- **3D**: Interactive 3D plots for spatial understanding

---

## D1: Connection Vector Field Plots

### Overview

Visualize the connection one-form $\mathcal{A}$ as a vector field on shape space.

**Physical Interpretation**: Arrows show the "automatic rotation" induced by shape changes.

### Implementation

```python
# File: src/python/visualization/connection_field.py

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.quiver import Quiver
from matplotlib.patches import Polygon
from typing import Optional, Tuple, Callable

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from ..geometry.connection import compute_connection_form
from ..geometry.batch_ops import compute_connection_grid


class ConnectionFieldPlotter:
    """
    Plotter for connection vector fields on shape space.

    Supports 2D slices of 3D shape space (fixing one coordinate).
    """

    def __init__(
        self,
        masses: Masses,
        figsize: Tuple[float, float] = (10, 8),
        dpi: int = 100
    ):
        self.masses = masses
        self.figsize = figsize
        self.dpi = dpi

    def plot_2d_slice(
        self,
        r12_range: Tuple[float, float],
        r23_range: Tuple[float, float],
        r31_fixed: float,
        L: float,
        resolution: int = 20,
        normalize_arrows: bool = True,
        show_magnitude: bool = True,
        colormap: str = 'viridis',
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot connection field on 2D slice of shape space.

        Args:
            r12_range: (min, max) for r12 axis
            r23_range: (min, max) for r23 axis
            r31_fixed: Fixed value for r31
            L: Angular momentum
            resolution: Grid resolution (N×N)
            normalize_arrows: Normalize arrow lengths for visibility
            show_magnitude: Show magnitude as background color
            colormap: Matplotlib colormap name
            save_path: If provided, save figure to this path

        Returns:
            Matplotlib figure object
        """
        # Compute connection field on grid
        r12_grid, r23_grid, conn_field = compute_connection_grid(
            r12_range, r23_range, r31_fixed, L, self.masses, resolution
        )

        # Extract components (using first two: A_r12, A_r23)
        U = conn_field[:, :, 0]  # A_r12 component
        V = conn_field[:, :, 1]  # A_r23 component

        # Compute magnitude
        magnitude = np.sqrt(U**2 + V**2)

        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Background: magnitude heatmap
        if show_magnitude:
            im = ax.imshow(
                magnitude,
                extent=[*r12_range, *r23_range],
                origin='lower',
                cmap=colormap,
                alpha=0.6,
                interpolation='bilinear'
            )
            cbar = plt.colorbar(im, ax=ax, label='$|\\mathcal{A}|$')

        # Quiver plot: vector field
        if normalize_arrows:
            # Normalize for visibility
            norm = np.sqrt(U**2 + V**2)
            norm = np.where(norm > 0, norm, 1.0)  # Avoid division by zero
            U_norm = U / norm
            V_norm = V / norm
        else:
            U_norm = U
            V_norm = V

        # Mask invalid regions (outside triangle inequality)
        mask = np.isnan(U)
        U_norm = np.ma.array(U_norm, mask=mask)
        V_norm = np.ma.array(V_norm, mask=mask)

        # Plot arrows
        quiver = ax.quiver(
            r12_grid, r23_grid,
            U_norm, V_norm,
            magnitude,
            cmap=colormap,
            scale=20,
            scale_units='xy',
            width=0.003,
            headwidth=3,
            headlength=4,
            alpha=0.8
        )

        # Mark valid triangle region boundary
        self._plot_triangle_inequality_boundary(ax, r12_range, r23_range, r31_fixed)

        # Labels and title
        ax.set_xlabel('$r_{12}$', fontsize=14)
        ax.set_ylabel('$r_{23}$', fontsize=14)
        ax.set_title(
            f'Connection One-Form $\\mathcal{{A}}$ (L={L:.2f}, $r_{{31}}$={r31_fixed:.2f})',
            fontsize=16
        )

        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def _plot_triangle_inequality_boundary(
        self,
        ax: plt.Axes,
        r12_range: Tuple[float, float],
        r23_range: Tuple[float, float],
        r31: float
    ):
        """
        Draw boundary of valid triangle region.

        Triangle inequality: r12 + r23 > r31, etc.
        """
        # Sample boundary
        r12_vals = np.linspace(*r12_range, 200)
        r23_vals = np.linspace(*r23_range, 200)

        # Find boundary points
        boundary_points = []

        for r12 in r12_vals:
            # r23 such that r12 + r23 = r31 (critical line)
            r23 = r31 - r12
            if r23_range[0] <= r23 <= r23_range[1]:
                boundary_points.append((r12, r23))

        for r23 in r23_vals:
            # r12 such that r12 + r23 = r31
            r12 = r31 - r23
            if r12_range[0] <= r12 <= r12_range[1]:
                boundary_points.append((r12, r23))

        if boundary_points:
            boundary = np.array(boundary_points)
            ax.plot(
                boundary[:, 0], boundary[:, 1],
                'r--', linewidth=2, label='Triangle inequality boundary'
            )
            ax.legend(loc='best')

    def plot_streamlines(
        self,
        r12_range: Tuple[float, float],
        r23_range: Tuple[float, float],
        r31_fixed: float,
        L: float,
        resolution: int = 50,
        density: float = 1.5,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot streamlines of connection field.

        Streamlines show "flow" induced by connection.
        """
        # Compute field
        r12_grid, r23_grid, conn_field = compute_connection_grid(
            r12_range, r23_range, r31_fixed, L, self.masses, resolution
        )

        U = conn_field[:, :, 0]
        V = conn_field[:, :, 1]

        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Streamlines
        magnitude = np.sqrt(U**2 + V**2)

        stream = ax.streamplot(
            r12_grid[0, :], r23_grid[:, 0],
            U.T, V.T,
            color=magnitude.T,
            cmap='plasma',
            density=density,
            linewidth=1.5,
            arrowsize=1.5
        )

        plt.colorbar(stream.lines, ax=ax, label='$|\\mathcal{A}|$')

        ax.set_xlabel('$r_{12}$', fontsize=14)
        ax.set_ylabel('$r_{23}$', fontsize=14)
        ax.set_title(
            f'Connection Streamlines (L={L:.2f}, $r_{{31}}$={r31_fixed:.2f})',
            fontsize=16
        )

        ax.set_aspect('equal')
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig
```

### Example Usage

```python
# Create plotter
masses = Masses(1.0, 1.0, 1.0)
plotter = ConnectionFieldPlotter(masses)

# Generate plot
fig = plotter.plot_2d_slice(
    r12_range=(0.8, 1.2),
    r23_range=(0.8, 1.2),
    r31_fixed=1.0,
    L=1.0,
    resolution=30,
    save_path='connection_field.pdf'
)

plt.show()
```

---

## D2: Curvature Heatmaps

### Overview

Visualize curvature magnitude $|\mathcal{F}|$ as a heatmap on shape space.

**Physical Interpretation**: Bright regions indicate strong obstruction to integrability.

### Implementation

```python
# File: src/python/visualization/curvature_heatmap.py

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, PowerNorm
from typing import Optional, Tuple, Callable

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from ..geometry.connection import compute_connection_form
from ..geometry.curvature import compute_curvature_form
from ..geometry.batch_ops import BatchShapeSpace


class CurvatureHeatmapPlotter:
    """
    Plotter for curvature magnitude heatmaps.
    """

    def __init__(
        self,
        masses: Masses,
        figsize: Tuple[float, float] = (10, 8),
        dpi: int = 100
    ):
        self.masses = masses
        self.figsize = figsize
        self.dpi = dpi

    def plot_magnitude_heatmap(
        self,
        r12_range: Tuple[float, float],
        r23_range: Tuple[float, float],
        r31_fixed: float,
        L: float,
        resolution: int = 50,
        colormap: str = 'hot',
        log_scale: bool = False,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot curvature magnitude as heatmap.

        Args:
            r12_range, r23_range: Coordinate ranges
            r31_fixed: Fixed coordinate
            L: Angular momentum
            resolution: Grid resolution
            colormap: Matplotlib colormap
            log_scale: Use logarithmic color scale
            vmin, vmax: Color scale limits
            save_path: Save path

        Returns:
            Figure object
        """
        # Compute curvature magnitude on grid
        r12_vals = np.linspace(*r12_range, resolution)
        r23_vals = np.linspace(*r23_range, resolution)
        r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

        curvature_magnitude = np.zeros((resolution, resolution))

        connection_evaluator = lambda s: compute_connection_form(s, self.masses)

        for i in range(resolution):
            for j in range(resolution):
                r12 = r12_grid[i, j]
                r23 = r23_grid[i, j]

                # Check triangle inequality
                if not self._is_valid_triangle(r12, r23, r31_fixed):
                    curvature_magnitude[i, j] = np.nan
                    continue

                try:
                    state = ShapeSpaceState(
                        r12=r12, r23=r23, r31=r31_fixed, L=L
                    )

                    curv = compute_curvature_form(connection_evaluator, state)
                    curvature_magnitude[i, j] = curv.magnitude()

                except Exception:
                    curvature_magnitude[i, j] = np.nan

        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Choose normalization
        if log_scale:
            norm = LogNorm(vmin=vmin, vmax=vmax)
        else:
            norm = None

        # Heatmap
        im = ax.imshow(
            curvature_magnitude,
            extent=[*r12_range, *r23_range],
            origin='lower',
            cmap=colormap,
            norm=norm,
            vmin=vmin,
            vmax=vmax,
            interpolation='bilinear',
            aspect='auto'
        )

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('$|\\mathcal{F}|$ (Curvature Magnitude)', fontsize=12)

        # Contour lines
        if not log_scale:
            levels = np.linspace(
                np.nanmin(curvature_magnitude),
                np.nanmax(curvature_magnitude),
                10
            )
            contours = ax.contour(
                r12_grid, r23_grid,
                curvature_magnitude,
                levels=levels,
                colors='white',
                alpha=0.4,
                linewidths=0.5
            )

        # Labels
        ax.set_xlabel('$r_{12}$', fontsize=14)
        ax.set_ylabel('$r_{23}$', fontsize=14)
        ax.set_title(
            f'Curvature Magnitude (L={L:.2f}, $r_{{31}}$={r31_fixed:.2f})',
            fontsize=16
        )

        ax.grid(True, alpha=0.3, color='white')

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_component_comparison(
        self,
        r12_range: Tuple[float, float],
        r23_range: Tuple[float, float],
        r31_fixed: float,
        L: float,
        resolution: int = 40,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot individual curvature components side-by-side.

        Shows F_12_23, F_23_31, F_31_12 separately.
        """
        # Compute curvature components
        r12_vals = np.linspace(*r12_range, resolution)
        r23_vals = np.linspace(*r23_range, resolution)
        r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

        F_components = np.zeros((resolution, resolution, 3))

        connection_evaluator = lambda s: compute_connection_form(s, self.masses)

        for i in range(resolution):
            for j in range(resolution):
                r12 = r12_grid[i, j]
                r23 = r23_grid[i, j]

                if not self._is_valid_triangle(r12, r23, r31_fixed):
                    F_components[i, j, :] = np.nan
                    continue

                try:
                    state = ShapeSpaceState(r12=r12, r23=r23, r31=r31_fixed, L=L)
                    curv = compute_curvature_form(connection_evaluator, state)

                    # Extract components
                    F_components[i, j, 0] = curv.matrix[0, 1]  # F_{r12,r23}
                    F_components[i, j, 1] = curv.matrix[1, 2]  # F_{r23,r31}
                    F_components[i, j, 2] = curv.matrix[2, 0]  # F_{r31,r12}

                except Exception:
                    F_components[i, j, :] = np.nan

        # Create figure with subplots
        fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=self.dpi)

        component_names = [
            '$F_{r_{12},r_{23}}$',
            '$F_{r_{23},r_{31}}$',
            '$F_{r_{31},r_{12}}$'
        ]

        for idx, (ax, name) in enumerate(zip(axes, component_names)):
            im = ax.imshow(
                F_components[:, :, idx],
                extent=[*r12_range, *r23_range],
                origin='lower',
                cmap='RdBu_r',
                interpolation='bilinear'
            )

            plt.colorbar(im, ax=ax)
            ax.set_xlabel('$r_{12}$')
            ax.set_ylabel('$r_{23}$')
            ax.set_title(name)
            ax.grid(True, alpha=0.3)

        fig.suptitle(f'Curvature Components (L={L:.2f}, $r_{{31}}$={r31_fixed:.2f})', fontsize=16)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def _is_valid_triangle(self, r12: float, r23: float, r31: float) -> bool:
        """Check triangle inequality."""
        return (
            r12 + r23 > r31 and
            r23 + r31 > r12 and
            r31 + r12 > r23 and
            r12 > 0 and r23 > 0 and r31 > 0
        )
```

---

## D3: Interactive Exploration Tools

### Jupyter Widget Interface

```python
# File: src/python/visualization/interactive.py

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, FloatSlider, IntSlider, Dropdown, Checkbox
from IPython.display import display

from ..coordinates.base import Masses
from .connection_field import ConnectionFieldPlotter
from .curvature_heatmap import CurvatureHeatmapPlotter


class InteractiveShapeSpaceExplorer:
    """
    Interactive explorer for connection and curvature fields.

    For use in Jupyter notebooks with ipywidgets.
    """

    def __init__(self, masses: Masses):
        self.masses = masses
        self.connection_plotter = ConnectionFieldPlotter(masses)
        self.curvature_plotter = CurvatureHeatmapPlotter(masses)

    def launch_connection_explorer(self):
        """
        Launch interactive connection field explorer.
        """
        @interact(
            r31_fixed=FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0,
                                  description='r₃₁ (fixed)'),
            L=FloatSlider(min=0.1, max=3.0, step=0.1, value=1.0,
                         description='L (ang. mom.)'),
            resolution=IntSlider(min=10, max=50, step=5, value=20,
                                description='Grid resolution'),
            show_magnitude=Checkbox(value=True, description='Show magnitude'),
            normalize_arrows=Checkbox(value=True, description='Normalize arrows')
        )
        def plot(r31_fixed, L, resolution, show_magnitude, normalize_arrows):
            # Fixed ranges
            r12_range = (0.5, 1.5)
            r23_range = (0.5, 1.5)

            fig = self.connection_plotter.plot_2d_slice(
                r12_range, r23_range, r31_fixed, L,
                resolution=resolution,
                show_magnitude=show_magnitude,
                normalize_arrows=normalize_arrows
            )
            plt.show()

    def launch_curvature_explorer(self):
        """
        Launch interactive curvature heatmap explorer.
        """
        @interact(
            r31_fixed=FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0,
                                  description='r₃₁ (fixed)'),
            L=FloatSlider(min=0.1, max=3.0, step=0.1, value=1.0,
                         description='L (ang. mom.)'),
            resolution=IntSlider(min=20, max=100, step=10, value=50,
                                description='Grid resolution'),
            log_scale=Checkbox(value=False, description='Log scale'),
            colormap=Dropdown(options=['hot', 'viridis', 'plasma', 'inferno'],
                            value='hot', description='Colormap')
        )
        def plot(r31_fixed, L, resolution, log_scale, colormap):
            r12_range = (0.5, 1.5)
            r23_range = (0.5, 1.5)

            fig = self.curvature_plotter.plot_magnitude_heatmap(
                r12_range, r23_range, r31_fixed, L,
                resolution=resolution,
                log_scale=log_scale,
                colormap=colormap
            )
            plt.show()

    def launch_combined_explorer(self):
        """
        Combined view: connection + curvature side-by-side.
        """
        @interact(
            r31_fixed=FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0),
            L=FloatSlider(min=0.1, max=3.0, step=0.1, value=1.0),
            resolution=IntSlider(min=15, max=40, step=5, value=20)
        )
        def plot(r31_fixed, L, resolution):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            # Connection field (simplified for side-by-side)
            from ..geometry.batch_ops import compute_connection_grid

            r12_range = (0.5, 1.5)
            r23_range = (0.5, 1.5)

            # ... (plotting code)

            plt.tight_layout()
            plt.show()
```

### Example Notebook Usage

````python
# In Jupyter notebook:

from coordinates.base import Masses
from visualization.interactive import InteractiveShapeSpaceExplorer

# Create explorer
masses = Masses(1.0, 1.0, 1.0)
explorer = InteractiveShapeSpaceExplorer(masses)

# Launch interactive widget
explorer.launch_curvature_explorer()
````

---

## D4: Validation: Stokes' Theorem

### Theoretical Foundation

**Stokes' Theorem** for differential forms:

$$
\int_{\partial S} \mathcal{A} = \int_S d\mathcal{A} = \int_S \mathcal{F}
$$

For a closed curve $\gamma = \partial S$ in shape space:
- **LHS**: Line integral of connection around $\gamma$
- **RHS**: Surface integral of curvature over surface $S$ bounded by $\gamma$

This provides a fundamental consistency check.

### Implementation

```python
# File: src/python/validation/stokes_theorem.py

import numpy as np
from typing import List, Callable, Tuple
from dataclasses import dataclass

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from ..geometry.connection import ConnectionForm, compute_connection_form
from ..geometry.curvature import CurvatureForm, compute_curvature_form


@dataclass
class StokesValidationResult:
    """
    Result of Stokes' theorem validation.

    Attributes:
        line_integral: ∮ A around boundary
        surface_integral: ∫∫ F over surface
        absolute_error: |line - surface|
        relative_error: error / max(|line|, |surface|)
        passes: True if error below threshold
    """
    line_integral: float
    surface_integral: float
    absolute_error: float
    relative_error: float
    passes: bool


class StokesTheoremValidator:
    """
    Validator for Stokes' theorem on shape space.

    Tests: ∮_∂S A = ∫_S F
    """

    def __init__(self, masses: Masses, tolerance: float = 1e-6):
        self.masses = masses
        self.tolerance = tolerance

    def validate_rectangular_path(
        self,
        r12_min: float,
        r12_max: float,
        r23_min: float,
        r23_max: float,
        r31_fixed: float,
        L: float,
        n_path_points: int = 50,
        n_surface_grid: int = 20
    ) -> StokesValidationResult:
        """
        Validate Stokes' theorem on rectangular path.

        Args:
            r12_min, r12_max: Rectangle bounds in r12
            r23_min, r23_max: Rectangle bounds in r23
            r31_fixed: Fixed r31 value
            L: Angular momentum
            n_path_points: Number of points along boundary
            n_surface_grid: Grid resolution for surface integral

        Returns:
            Validation result
        """
        # Define rectangular path
        path = self._create_rectangular_path(
            r12_min, r12_max,
            r23_min, r23_max,
            r31_fixed, L,
            n_path_points
        )

        # Compute line integral ∮ A
        line_integral = self._compute_line_integral(path)

        # Compute surface integral ∫∫ F
        surface_integral = self._compute_surface_integral(
            r12_min, r12_max,
            r23_min, r23_max,
            r31_fixed, L,
            n_surface_grid
        )

        # Compare
        abs_error = abs(line_integral - surface_integral)
        denom = max(abs(line_integral), abs(surface_integral), 1e-10)
        rel_error = abs_error / denom

        passes = rel_error < self.tolerance

        return StokesValidationResult(
            line_integral=line_integral,
            surface_integral=surface_integral,
            absolute_error=abs_error,
            relative_error=rel_error,
            passes=passes
        )

    def _create_rectangular_path(
        self,
        r12_min: float, r12_max: float,
        r23_min: float, r23_max: float,
        r31: float, L: float,
        n_points: int
    ) -> List[ShapeSpaceState]:
        """
        Create closed rectangular path in shape space.

        Path goes counterclockwise around rectangle.
        """
        path = []

        # Number of points per side
        n_per_side = n_points // 4

        # Side 1: r12_min to r12_max (r23 = r23_min)
        for r12 in np.linspace(r12_min, r12_max, n_per_side, endpoint=False):
            path.append(ShapeSpaceState(r12, r23_min, r31, L))

        # Side 2: r23_min to r23_max (r12 = r12_max)
        for r23 in np.linspace(r23_min, r23_max, n_per_side, endpoint=False):
            path.append(ShapeSpaceState(r12_max, r23, r31, L))

        # Side 3: r12_max to r12_min (r23 = r23_max)
        for r12 in np.linspace(r12_max, r12_min, n_per_side, endpoint=False):
            path.append(ShapeSpaceState(r12, r23_max, r31, L))

        # Side 4: r23_max to r23_min (r12 = r12_min)
        for r23 in np.linspace(r23_max, r23_min, n_per_side, endpoint=True):
            path.append(ShapeSpaceState(r12_min, r23, r31, L))

        return path

    def _compute_line_integral(
        self,
        path: List[ShapeSpaceState]
    ) -> float:
        """
        Compute ∮ A · ds along path.

        Uses trapezoidal rule.
        """
        integral = 0.0

        for i in range(len(path) - 1):
            state1 = path[i]
            state2 = path[i + 1]

            # Midpoint for connection evaluation
            state_mid = ShapeSpaceState(
                r12=(state1.r12 + state2.r12) / 2,
                r23=(state1.r23 + state2.r23) / 2,
                r31=(state1.r31 + state2.r31) / 2,
                L=(state1.L + state2.L) / 2
            )

            # Connection at midpoint
            conn = compute_connection_form(state_mid, self.masses)

            # Path displacement
            ds = np.array([
                state2.r12 - state1.r12,
                state2.r23 - state1.r23,
                state2.r31 - state1.r31
            ])

            # A · ds
            contribution = conn.evaluate(ds)
            integral += contribution

        return integral

    def _compute_surface_integral(
        self,
        r12_min: float, r12_max: float,
        r23_min: float, r23_max: float,
        r31: float, L: float,
        n_grid: int
    ) -> float:
        """
        Compute ∫∫ F over rectangular surface.

        Uses midpoint rule on grid.
        """
        dr12 = (r12_max - r12_min) / n_grid
        dr23 = (r23_max - r23_min) / n_grid

        integral = 0.0

        connection_evaluator = lambda s: compute_connection_form(s, self.masses)

        for i in range(n_grid):
            for j in range(n_grid):
                # Grid cell center
                r12 = r12_min + (i + 0.5) * dr12
                r23 = r23_min + (j + 0.5) * dr23

                state = ShapeSpaceState(r12, r23, r31, L)

                # Curvature at this point
                curv = compute_curvature_form(connection_evaluator, state)

                # F_{12,23} component (for r12-r23 plane)
                F_component = curv.matrix[0, 1]

                # Area element: dr12 ∧ dr23
                integral += F_component * dr12 * dr23

        return integral

    def validate_multiple_paths(
        self,
        n_tests: int = 10
    ) -> List[StokesValidationResult]:
        """
        Validate on multiple random rectangular paths.

        Returns:
            List of validation results
        """
        results = []

        for _ in range(n_tests):
            # Random rectangle
            r12_center = np.random.uniform(0.8, 1.2)
            r23_center = np.random.uniform(0.8, 1.2)

            size = np.random.uniform(0.1, 0.3)

            r12_min = r12_center - size / 2
            r12_max = r12_center + size / 2
            r23_min = r23_center - size / 2
            r23_max = r23_center + size / 2

            r31_fixed = np.random.uniform(0.8, 1.2)
            L = np.random.uniform(0.5, 1.5)

            result = self.validate_rectangular_path(
                r12_min, r12_max,
                r23_min, r23_max,
                r31_fixed, L
            )

            results.append(result)

        return results


def print_stokes_validation_summary(results: List[StokesValidationResult]):
    """
    Print summary of Stokes' theorem validation results.
    """
    print("\n" + "="*70)
    print("Stokes' Theorem Validation Summary")
    print("="*70)

    n_total = len(results)
    n_passed = sum(1 for r in results if r.passes)

    print(f"Total tests: {n_total}")
    print(f"Passed:      {n_passed} ({100*n_passed/n_total:.1f}%)")
    print(f"Failed:      {n_total - n_passed}")
    print()

    # Statistics
    rel_errors = [r.relative_error for r in results]

    print(f"Relative Error Statistics:")
    print(f"  Mean:   {np.mean(rel_errors):.3e}")
    print(f"  Median: {np.median(rel_errors):.3e}")
    print(f"  Max:    {np.max(rel_errors):.3e}")
    print(f"  Min:    {np.min(rel_errors):.3e}")
    print("="*70)
```

### Example Usage

```python
# Run Stokes' theorem validation
from coordinates.base import Masses
from validation.stokes_theorem import StokesTheoremValidator, print_stokes_validation_summary

masses = Masses(1.0, 1.0, 1.0)
validator = StokesTheoremValidator(masses, tolerance=1e-6)

# Single test
result = validator.validate_rectangular_path(
    r12_min=0.9, r12_max=1.1,
    r23_min=0.9, r23_max=1.1,
    r31_fixed=1.0,
    L=1.0
)

print(f"Line integral:    {result.line_integral:.6e}")
print(f"Surface integral: {result.surface_integral:.6e}")
print(f"Relative error:   {result.relative_error:.6e}")
print(f"Passes: {result.passes}")

# Multiple tests
results = validator.validate_multiple_paths(n_tests=20)
print_stokes_validation_summary(results)
```

---

## D5: Additional Validation Tests

### Gauge Invariance Test

```python
def test_curvature_gauge_invariance():
    """
    Test that curvature is gauge-invariant.

    Under gauge transformation A → A + dα, curvature is unchanged.
    """
    from ..geometry.connection import compute_connection_form_with_gauge
    from ..geometry.curvature import compute_curvature_form

    state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)
    masses = Masses(1.0, 1.0, 1.0)

    # Gauge 1: align r12 with x-axis
    conn_eval_1 = lambda s: compute_connection_form_with_gauge(
        s, masses, gauge='align_12_x'
    )
    curv_1 = compute_curvature_form(conn_eval_1, state)

    # Gauge 2: align r23 with x-axis
    conn_eval_2 = lambda s: compute_connection_form_with_gauge(
        s, masses, gauge='align_23_x'
    )
    curv_2 = compute_curvature_form(conn_eval_2, state)

    # Curvatures should be identical
    error = np.linalg.norm(curv_1.matrix - curv_2.matrix)

    assert error < 1e-10, f"Curvature not gauge-invariant (error={error})"
    print(f"✓ Gauge invariance test passed (error={error:.3e})")
```

### Symmetry Tests

```python
def test_equilateral_triangle_symmetry():
    """
    For equilateral triangle with equal masses, curvature should be zero.

    This is due to maximal symmetry.
    """
    side = 1.0
    state = ShapeSpaceState(r12=side, r23=side, r31=side, L=1.0)
    masses = Masses(1.0, 1.0, 1.0)

    conn_eval = lambda s: compute_connection_form(s, masses)
    curv = compute_curvature_form(conn_eval, state)

    magnitude = curv.magnitude()

    assert magnitude < 1e-10, f"Equilateral should have zero curvature (got {magnitude})"
    print(f"✓ Equilateral symmetry test passed (|F|={magnitude:.3e})")


def test_permutation_symmetry():
    """
    For equal masses, curvature should respect body permutation symmetry.
    """
    masses = Masses(1.0, 1.0, 1.0)

    # State and its permutation
    state1 = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.2, L=1.0)
    state2 = ShapeSpaceState(r12=1.1, r23=1.2, r31=1.0, L=1.0)  # Cyclic permutation

    conn_eval = lambda s: compute_connection_form(s, masses)

    curv1 = compute_curvature_form(conn_eval, state1)
    curv2 = compute_curvature_form(conn_eval, state2)

    # Magnitudes should be equal
    assert abs(curv1.magnitude() - curv2.magnitude()) < 1e-10

    print("✓ Permutation symmetry test passed")
```

---

## Implementation Details

### Directory Structure

```
src/python/visualization/
├── __init__.py
├── connection_field.py      # D1: Connection plots
├── curvature_heatmap.py     # D2: Curvature heatmaps
├── interactive.py           # D3: Interactive tools
└── publication.py           # Publication-quality figure generation

src/python/validation/
├── __init__.py
├── stokes_theorem.py        # D4: Stokes' theorem validation
└── theoretical_properties.py # D5: Additional validation tests

tests/validation/
├── test_stokes_theorem.py
├── test_gauge_invariance.py
└── test_symmetries.py
```

---

## Publication Quality Figures

### Configuration for Publications

```python
# File: src/python/visualization/publication.py

import matplotlib.pyplot as plt
import matplotlib as mpl

# Publication settings
PUBLICATION_CONFIG = {
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 11,
    'figure.figsize': (6, 4),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman'],
    'text.usetex': True,  # Use LaTeX for text
    'axes.grid': True,
    'grid.alpha': 0.3
}


def configure_for_publication():
    """Apply publication-quality settings."""
    mpl.rcParams.update(PUBLICATION_CONFIG)


def save_publication_figure(
    fig: plt.Figure,
    filename: str,
    formats: List[str] = ['pdf', 'png']
):
    """
    Save figure in multiple formats for publication.

    Args:
        fig: Matplotlib figure
        filename: Base filename (without extension)
        formats: List of formats to save
    """
    for fmt in formats:
        output_path = f"{filename}.{fmt}"
        fig.savefig(
            output_path,
            format=fmt,
            dpi=300,
            bbox_inches='tight'
        )
        print(f"Saved: {output_path}")
```

---

## Integration Guide

### Complete Validation Workflow

```python
# Complete validation and visualization workflow

from coordinates.base import Masses
from visualization.connection_field import ConnectionFieldPlotter
from visualization.curvature_heatmap import CurvatureHeatmapPlotter
from visualization.publication import configure_for_publication
from validation.stokes_theorem import StokesTheoremValidator

# Setup
configure_for_publication()
masses = Masses(1.0, 1.0, 1.0)

# 1. Generate connection field plot
conn_plotter = ConnectionFieldPlotter(masses)
fig_conn = conn_plotter.plot_2d_slice(
    r12_range=(0.8, 1.2),
    r23_range=(0.8, 1.2),
    r31_fixed=1.0,
    L=1.0,
    resolution=30,
    save_path='figures/connection_field.pdf'
)

# 2. Generate curvature heatmap
curv_plotter = CurvatureHeatmapPlotter(masses)
fig_curv = curv_plotter.plot_magnitude_heatmap(
    r12_range=(0.8, 1.2),
    r23_range=(0.8, 1.2),
    r31_fixed=1.0,
    L=1.0,
    resolution=50,
    save_path='figures/curvature_heatmap.pdf'
)

# 3. Validate Stokes' theorem
validator = StokesTheoremValidator(masses, tolerance=1e-6)
results = validator.validate_multiple_paths(n_tests=20)
print_stokes_validation_summary(results)

# 4. Run additional validation tests
test_curvature_gauge_invariance()
test_equilateral_triangle_symmetry()
test_permutation_symmetry()

print("\n✓ All validation and visualization complete!")
```

---

## Success Criteria

### Part D Complete When:

- [ ] Connection vector field plots implemented
- [ ] Curvature heatmaps implemented with multiple color schemes
- [ ] Interactive exploration tools functional in Jupyter
- [ ] Stokes' theorem validation implemented and passing
- [ ] Additional validation tests pass:
  - [ ] Gauge invariance
  - [ ] Equilateral symmetry
  - [ ] Permutation symmetry
  - [ ] Two-body limit
- [ ] Publication-quality figure generation working
- [ ] All visualizations rendering correctly
- [ ] Interactive widgets responsive and intuitive
- [ ] Documentation complete with examples

**Task 2.1.2 Complete** when all Parts A, B, C, D boxes checked.

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 2-3 days
**Completes**: Task 2.1.2 (Connection and Curvature)
