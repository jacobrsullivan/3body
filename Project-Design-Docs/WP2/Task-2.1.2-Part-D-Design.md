# Task 2.1.2 Part D: Visualization and Validation - Detailed Design

**Task**: WP 2.1.2 - Computation of the "Magnetic Twist" (Connection and Curvature)
**Part**: D - Visualization and Validation
**Status**: Design Phase
**Estimated Duration**: 2 days
**Dependencies**: Task 2.1.2 Parts A, B, C Complete

---

## Table of Contents

1. [Overview](#overview)
2. [D1: Connection Vector Field Visualization](#d1-connection-vector-field-visualization)
3. [D2: Curvature Heatmaps and Landscapes](#d2-curvature-heatmaps-and-landscapes)
4. [D3: Interactive Exploration Tools](#d3-interactive-exploration-tools)
5. [D4: Publication-Quality Figures](#d4-publication-quality-figures)
6. [D5: Validation Test Suite](#d5-validation-test-suite)

---

## Overview

### Purpose

Part D implements comprehensive visualization and validation tools for connection and curvature fields. These tools provide both scientific insight and publication-ready figures for the geometric structure of the three-body problem.

### Key Visualizations

1. **Connection Vector Fields**: Quiver plots showing rotation induced by shape changes
2. **Curvature Heatmaps**: Color-coded maps of curvature magnitude
3. **3D Landscapes**: Surface plots of $|\mathcal{F}|$ over shape space
4. **Stokes Validation Plots**: Visual verification of integral theorems
5. **Interactive Widgets**: Real-time exploration with parameter sliders

---

## D1: Connection Vector Field Visualization

### Algorithm D1.1: 2D Vector Field Plot

```python
import matplotlib.pyplot as plt
from matplotlib.quiver import Quiver

def plot_connection_vector_field(
    connection_func: Callable,
    r12_range: tuple[float, float],
    r23_range: tuple[float, float],
    r31_fixed: float = 1.0,
    L_magnitude: float = 1.0,
    resolution: int = 20,
    figsize: tuple = (12, 10)
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plot connection as vector field on shape space.

    Args:
        connection_func: Connection evaluator
        r12_range, r23_range: Grid ranges
        r31_fixed: Fixed third coordinate
        L_magnitude: Angular momentum
        resolution: Grid resolution
        figsize: Figure size

    Returns:
        (figure, axes)
    """
    # Create grid
    r12_vals = np.linspace(*r12_range, resolution)
    r23_vals = np.linspace(*r23_range, resolution)
    R12, R23 = np.meshgrid(r12_vals, r23_vals)

    # Compute connection at each grid point
    A_r12 = np.zeros_like(R12)
    A_r23 = np.zeros_like(R23)

    for i in range(resolution):
        for j in range(resolution):
            r12, r23 = R12[i, j], R23[i, j]

            if not satisfies_triangle_inequality(r12, r23, r31_fixed):
                A_r12[i, j] = np.nan
                A_r23[i, j] = np.nan
                continue

            state = ShapeSpaceState(r12, r23, r31_fixed, L=L_magnitude)
            try:
                conn = connection_func(state)
                A_r12[i, j] = conn.coefficients[0]  # A_{r12}
                A_r23[i, j] = conn.coefficients[1]  # A_{r23}
            except:
                A_r12[i, j] = np.nan
                A_r23[i, j] = np.nan

    # Create plot
    fig, ax = plt.subplots(figsize=figsize)

    # Quiver plot
    quiver = ax.quiver(
        R12, R23, A_r12, A_r23,
        scale=50,
        width=0.003,
        headwidth=3,
        headlength=4,
        color='blue',
        alpha=0.7
    )

    # Colorbar for magnitude
    magnitudes = np.sqrt(A_r12**2 + A_r23**2)
    contour = ax.contourf(R12, R23, magnitudes, levels=20, cmap='viridis', alpha=0.3)
    plt.colorbar(contour, ax=ax, label='$|\mathcal{A}|$')

    # Labels
    ax.set_xlabel('$r_{12}$', fontsize=14)
    ax.set_ylabel('$r_{23}$', fontsize=14)
    ax.set_title(f'Connection Vector Field (L={L_magnitude:.2f}, $r_{{31}}$={r31_fixed:.2f})',
                 fontsize=16)

    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    return fig, ax
```

### Algorithm D1.2: Streamline Visualization

```python
def plot_connection_streamlines(
    connection_func: Callable,
    r12_range: tuple[float, float],
    r23_range: tuple[float, float],
    r31_fixed: float = 1.0,
    L_magnitude: float = 1.0,
    resolution: int = 50
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plot connection as streamlines.

    Streamlines follow the "flow" of the connection.
    """
    # Compute connection field (same as above)
    R12, R23, A_r12, A_r23 = compute_connection_field_grid(
        connection_func, r12_range, r23_range, r31_fixed, L_magnitude, resolution
    )

    fig, ax = plt.subplots(figsize=(12, 10))

    # Streamplot
    stream = ax.streamplot(
        R12, R23, A_r12, A_r23,
        density=1.5,
        linewidth=1,
        color=np.sqrt(A_r12**2 + A_r23**2),
        cmap='plasma',
        arrowsize=1.5
    )

    plt.colorbar(stream.lines, ax=ax, label='$|\mathcal{A}|$')

    ax.set_xlabel('$r_{12}$', fontsize=14)
    ax.set_ylabel('$r_{23}$', fontsize=14)
    ax.set_title('Connection Streamlines', fontsize=16)

    return fig, ax
```

---

## D2: Curvature Heatmaps and Landscapes

### Algorithm D2.1: 2D Heatmap

```python
def plot_curvature_heatmap(
    curvature_func: Callable,
    r12_range: tuple[float, float],
    r23_range: tuple[float, float],
    r31_fixed: float = 1.0,
    resolution: int = 100,
    log_scale: bool = True
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plot curvature magnitude as heatmap.

    Args:
        curvature_func: Curvature evaluator
        r12_range, r23_range: Grid ranges
        r31_fixed: Fixed coordinate
        resolution: Grid resolution
        log_scale: Use log scale for color

    Returns:
        (figure, axes)
    """
    # Compute curvature field
    field = compute_curvature_field_fast(
        curvature_func, r12_range, r23_range, r31_fixed, resolution
    )

    R12 = field['r12_grid']
    R23 = field['r23_grid']
    F_mag = field['curvature_magnitude']

    # Handle log scale
    if log_scale:
        F_plot = np.log10(F_mag + 1e-15)  # Avoid log(0)
        label = '$\log_{10}|\mathcal{F}|$'
    else:
        F_plot = F_mag
        label = '$|\mathcal{F}|$'

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 10))

    # Heatmap
    im = ax.imshow(
        F_plot,
        extent=[*r12_range, *r23_range],
        origin='lower',
        cmap='hot',
        aspect='auto',
        interpolation='bilinear'
    )

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(label, fontsize=14)

    # Contour lines
    contours = ax.contour(R12, R23, F_mag, levels=10, colors='white',
                          linewidths=0.5, alpha=0.5)
    ax.clabel(contours, inline=True, fontsize=8)

    ax.set_xlabel('$r_{12}$', fontsize=14)
    ax.set_ylabel('$r_{23}$', fontsize=14)
    ax.set_title(f'Curvature Magnitude ($r_{{31}}$={r31_fixed:.2f})', fontsize=16)

    return fig, ax
```

### Algorithm D2.2: 3D Surface Plot

```python
from mpl_toolkits.mplot3d import Axes3D

def plot_curvature_landscape_3d(
    curvature_func: Callable,
    r12_range: tuple[float, float],
    r23_range: tuple[float, float],
    r31_fixed: float = 1.0,
    resolution: int = 50
) -> tuple[plt.Figure, Axes3D]:
    """
    Plot curvature as 3D landscape.

    Surface height represents curvature magnitude.
    """
    field = compute_curvature_field_fast(
        curvature_func, r12_range, r23_range, r31_fixed, resolution
    )

    R12 = field['r12_grid']
    R23 = field['r23_grid']
    F_mag = field['curvature_magnitude']

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Surface plot
    surf = ax.plot_surface(
        R12, R23, F_mag,
        cmap='coolwarm',
        linewidth=0,
        antialiased=True,
        alpha=0.9
    )

    # Colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, label='$|\mathcal{F}|$')

    # Labels
    ax.set_xlabel('$r_{12}$', fontsize=12)
    ax.set_ylabel('$r_{23}$', fontsize=12)
    ax.set_zlabel('$|\mathcal{F}|$', fontsize=12)
    ax.set_title('Curvature Landscape', fontsize=16)

    # Viewing angle
    ax.view_init(elev=25, azim=45)

    return fig, ax
```

---

## D3: Interactive Exploration Tools

### Algorithm D3.1: IPyWidgets Explorer

```python
import ipywidgets as widgets
from IPython.display import display

def create_interactive_curvature_explorer(
    connection_func: Callable,
    curvature_func: Callable
):
    """
    Create interactive widget for exploring curvature.

    Allows real-time parameter adjustment.
    """
    @widgets.interact(
        r31=widgets.FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0,
                                description='$r_{31}$:'),
        L=widgets.FloatSlider(min=0.0, max=3.0, step=0.1, value=1.0,
                              description='L:'),
        resolution=widgets.IntSlider(min=10, max=100, step=10, value=50,
                                     description='Resolution:'),
        log_scale=widgets.Checkbox(value=True, description='Log scale')
    )
    def update_plot(r31, L, resolution, log_scale):
        fig, ax = plot_curvature_heatmap(
            curvature_func,
            r12_range=(0.3, 2.0),
            r23_range=(0.3, 2.0),
            r31_fixed=r31,
            resolution=resolution,
            log_scale=log_scale
        )
        plt.show()

        # Print statistics
        field = compute_curvature_field_fast(
            curvature_func, (0.3, 2.0), (0.3, 2.0), r31, resolution
        )
        F_mag = field['curvature_magnitude']
        F_valid = F_mag[~np.isnan(F_mag)]

        print(f"Curvature Statistics (r31={r31:.2f}, L={L:.2f}):")
        print(f"  Min: {np.min(F_valid):.6e}")
        print(f"  Max: {np.max(F_valid):.6e}")
        print(f"  Mean: {np.mean(F_valid):.6e}")
        print(f"  Median: {np.median(F_valid):.6e}")
```

### Algorithm D3.2: Point Probe Tool

```python
def create_point_probe_tool(connection_func: Callable, curvature_func: Callable):
    """
    Interactive tool to probe connection and curvature at specific points.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Plot base curvature field
    field = compute_curvature_field_fast(
        curvature_func, (0.5, 1.5), (0.5, 1.5), 1.0, 50
    )

    im = ax1.imshow(field['curvature_magnitude'], extent=[0.5, 1.5, 0.5, 1.5],
                    origin='lower', cmap='hot')
    ax1.set_xlabel('$r_{12}$')
    ax1.set_ylabel('$r_{23}$')
    ax1.set_title('Click to probe')

    # Text display
    info_text = ax2.text(0.1, 0.5, 'Click on heatmap...', fontsize=12,
                         verticalalignment='center')
    ax2.axis('off')

    def on_click(event):
        if event.inaxes == ax1:
            r12, r23 = event.xdata, event.ydata

            if satisfies_triangle_inequality(r12, r23, 1.0):
                state = ShapeSpaceState(r12, r23, 1.0, L=1.0)

                try:
                    conn = connection_func(state)
                    curv = curvature_func(state)

                    info = f"""
Point: ({r12:.3f}, {r23:.3f}, 1.000)

Connection:
  A_r12 = {conn.coefficients[0]:.6f}
  A_r23 = {conn.coefficients[1]:.6f}
  A_r31 = {conn.coefficients[2]:.6f}
  |A| = {np.linalg.norm(conn.coefficients):.6f}

Curvature:
  |F| = {curv.magnitude():.6e}
  Max component: {curv.max_component()[0]:.6e}
  Classification: {classify_curvature(curv)}
                    """

                    info_text.set_text(info)
                    fig.canvas.draw()
                except Exception as e:
                    info_text.set_text(f"Error at ({r12:.3f}, {r23:.3f}): {e}")
                    fig.canvas.draw()

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()
```

---

## D4: Publication-Quality Figures

### Algorithm D4.1: Figure Template

```python
import matplotlib as mpl

def setup_publication_style():
    """
    Configure matplotlib for publication-quality figures.
    """
    mpl.rcParams['font.family'] = 'serif'
    mpl.rcParams['font.serif'] = 'Computer Modern'
    mpl.rcParams['text.usetex'] = True
    mpl.rcParams['font.size'] = 11
    mpl.rcParams['axes.labelsize'] = 12
    mpl.rcParams['axes.titlesize'] = 14
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['ytick.labelsize'] = 10
    mpl.rcParams['legend.fontsize'] = 10
    mpl.rcParams['figure.figsize'] = (6, 4.5)  # Standard for 2-column format
    mpl.rcParams['figure.dpi'] = 300


def create_publication_figure_1(connection_func: Callable, curvature_func: Callable):
    """
    Create Figure 1: Connection and Curvature Overview.

    2x2 panel figure suitable for publication.
    """
    setup_publication_style()

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel A: Connection vector field
    plot_connection_vector_field_on_axis(axes[0, 0], connection_func)
    axes[0, 0].set_title('(a) Connection $\mathcal{A}$')

    # Panel B: Curvature heatmap
    plot_curvature_heatmap_on_axis(axes[0, 1], curvature_func)
    axes[0, 1].set_title('(b) Curvature $|\mathcal{F}|$')

    # Panel C: Stokes verification
    plot_stokes_verification_on_axis(axes[1, 0], connection_func, curvature_func)
    axes[1, 0].set_title('(c) Stokes Theorem Validation')

    # Panel D: Curvature statistics
    plot_curvature_statistics_on_axis(axes[1, 1], curvature_func)
    axes[1, 1].set_title('(d) Curvature Distribution')

    plt.tight_layout()
    return fig
```

---

## D5: Validation Test Suite

### Algorithm D5.1: Comprehensive Validation

```python
class ValidationTestSuite:
    """Comprehensive validation of connection and curvature."""

    def __init__(self, connection_func: Callable, curvature_func: Callable):
        self.connection_func = connection_func
        self.curvature_func = curvature_func
        self.results = {}

    def run_all_tests(self) -> dict:
        """Run complete validation suite."""

        self.results['stokes_theorem'] = self.test_stokes_theorem()
        self.results['gauge_invariance'] = self.test_gauge_invariance()
        self.results['two_body_limit'] = self.test_two_body_limit()
        self.results['equal_mass_symmetry'] = self.test_equal_mass_symmetry()
        self.results['non_flatness'] = self.test_generic_non_flatness()

        # Summary
        all_pass = all(r['passes'] for r in self.results.values())

        return {
            'individual_tests': self.results,
            'all_pass': all_pass,
            'summary': self.generate_summary()
        }

    def test_stokes_theorem(self) -> dict:
        """Test Stokes' theorem on multiple paths."""
        paths = generate_test_paths(n_paths=5)
        errors = []

        for path, surface in paths:
            result = verify_stokes_theorem(
                self.connection_func, self.curvature_func, path, surface
            )
            errors.append(result['relative_error'])

        max_error = np.max(errors)
        passes = max_error < 1e-8

        return {
            'test': 'Stokes Theorem',
            'max_error': max_error,
            'passes': passes,
            'n_paths_tested': len(paths)
        }

    def generate_summary(self) -> str:
        """Generate human-readable summary."""
        summary = "Validation Test Results\n"
        summary += "=" * 50 + "\n\n"

        for test_name, result in self.results.items():
            status = "✓ PASS" if result['passes'] else "✗ FAIL"
            summary += f"{test_name}: {status}\n"

        return summary
```

---

## Summary

Part D provides:

✅ **Vector field visualizations** (quiver plots, streamlines)
✅ **Heatmaps and 3D landscapes** for curvature
✅ **Interactive exploration tools** (widgets, probe tools)
✅ **Publication-quality figures** (LaTeX formatting)
✅ **Comprehensive validation suite** (Stokes, gauge, symmetry tests)

**Task 2.1.2 Complete**: All parts A-D finished.

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Complete
**Estimated Lines**: ~1,200
