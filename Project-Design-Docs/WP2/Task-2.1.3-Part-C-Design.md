# Task 2.1.3 Part C: Visualization & Exploration - Detailed Design

**Task**: WP 2.1.3 - Jacobi-Maupertuis Metric Analysis
**Part**: C - Visualization & Exploration
**Status**: Design Phase
**Estimated Duration**: 1-2 days
**Dependencies**: Task 2.1.3 Parts A & B Complete

---

## Overview

Part C provides visualization and interactive exploration tools for the JM metric and its curvature. These tools enable:
1. **Scientific Understanding** - Visualize abstract geometric concepts
2. **Interactive Exploration** - Real-time parameter variation
3. **Publication Figures** - High-quality graphics for papers
4. **Hypothesis Testing** - Visual validation of chaos-curvature link

### Deliverables

- Metric ellipsoid visualizations
- Curvature landscape 3D plots
- Interactive Jupyter widgets
- Chaos-curvature scatter plots
- Publication-quality figure templates

---

## C1: Metric Ellipsoid Visualization

The metric tensor $g_{ij}$ defines an ellipsoid at each point showing "distances" in different directions.

```python
# File: src/python/visualization/metric_ellipsoid.py

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Ellipse

def plot_metric_field_2d(
    masses: Masses,
    energy: float,
    r12_range: tuple,
    r23_range: tuple,
    r31_fixed: float,
    L_magnitude: float = 1.0,
    grid_resolution: int = 10
):
    """
    Plot metric tensor as ellipses on 2D slice.

    Shows how "distance" varies across shape space.
    """
    fig, ax = plt.subplots(figsize=(12, 10))

    r12_vals = np.linspace(*r12_range, grid_resolution)
    r23_vals = np.linspace(*r23_range, grid_resolution)

    for r12 in r12_vals:
        for r23 in r23_vals:
            state = ShapeSpaceState(r12, r23, r31_fixed, L_magnitude)

            try:
                metric = compute_jm_metric(state, masses, energy, L_magnitude)

                # Extract 2D submatrix (r12, r23 directions)
                g_2d = metric.components[:2, :2]

                # Eigendecomposition
                eigenvals, eigenvecs = np.linalg.eigh(g_2d)

                # Draw ellipse
                angle = np.degrees(np.arctan2(eigenvecs[1,0], eigenvecs[0,0]))
                width = 2 * np.sqrt(eigenvals[0]) * 0.05  # Scale for visibility
                height = 2 * np.sqrt(eigenvals[1]) * 0.05

                ellipse = Ellipse(
                    (r12, r23),
                    width, height,
                    angle=angle,
                    facecolor='blue',
                    edgecolor='black',
                    alpha=0.5
                )
                ax.add_patch(ellipse)
            except:
                continue

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_title('JM Metric Tensor Field')
    ax.set_aspect('equal')
    plt.show()
```

---

## C2: Curvature Landscape

Visualize scalar curvature as 3D surface or heatmap.

```python
# File: src/python/visualization/curvature_landscape.py

def plot_curvature_surface_3d(
    masses: Masses,
    energy: float,
    shape_region: tuple,
    L_magnitude: float = 1.0,
    resolution: int = 50
):
    """
    Plot scalar curvature R as 3D surface.

    Negative regions (red) indicate chaos.
    """
    r12_range, r23_range = shape_region
    r12_grid = np.linspace(*r12_range, resolution)
    r23_grid = np.linspace(*r23_range, resolution)

    R_grid = np.zeros((resolution, resolution))

    for i, r12 in enumerate(r12_grid):
        for j, r23 in enumerate(r23_grid):
            r31 = (r12 + r23) / 2.0  # Valid triangle
            state = ShapeSpaceState(r12, r23, r31, L_magnitude)

            try:
                curv = compute_curvature_tensors_complete(
                    state, masses, energy, L_magnitude
                )
                R_grid[i, j] = curv.scalar
            except:
                R_grid[i, j] = np.nan

    # 3D surface plot
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    X, Y = np.meshgrid(r12_grid, r23_grid)

    # Color: red for negative, blue for positive
    surf = ax.plot_surface(
        X, Y, R_grid.T,
        cmap='RdBu_r',
        vmin=-np.nanmax(np.abs(R_grid)),
        vmax=np.nanmax(np.abs(R_grid)),
        alpha=0.9
    )

    # Add zero plane
    ax.plot_surface(
        X, Y, np.zeros_like(R_grid.T),
        color='gray',
        alpha=0.2
    )

    fig.colorbar(surf, label='Scalar Curvature $R$')
    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_zlabel('$R$')
    ax.set_title('Curvature Landscape (Red = Chaotic)')
    plt.show()


def plot_curvature_heatmap(
    masses: Masses,
    energy: float,
    shape_region: tuple,
    L_magnitude: float = 1.0
):
    """
    2D heatmap of curvature magnitude.
    """
    # Similar to above, but imshow instead of surface
    pass
```

---

## C3: Interactive Explorer

Jupyter widget for real-time parameter exploration.

```python
# File: src/python/visualization/interactive_jm.py

import ipywidgets as widgets
from IPython.display import display

def create_curvature_explorer():
    """
    Interactive widget to explore how curvature changes with parameters.
    """
    @widgets.interact(
        m1=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0, description='m₁'),
        m2=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0, description='m₂'),
        m3=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0, description='m₃'),
        energy=widgets.FloatSlider(min=-2.0, max=-0.1, step=0.1, value=-1.0, description='E'),
        L=widgets.FloatSlider(min=0.0, max=3.0, step=0.1, value=1.0, description='L'),
        r12=widgets.FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0, description='r₁₂'),
        r23=widgets.FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0, description='r₂₃'),
        r31=widgets.FloatSlider(min=0.5, max=2.0, step=0.1, value=1.0, description='r₃₁')
    )
    def explore(m1, m2, m3, energy, L, r12, r23, r31):
        masses = Masses(m1, m2, m3)
        state = ShapeSpaceState(r12, r23, r31, L)

        try:
            # Compute curvature
            curv = compute_curvature_tensors_complete(
                state, masses, energy, L
            )

            # Display results
            print(f"\nScalar Curvature: R = {curv.scalar:.6f}")

            if curv.is_negative:
                print("→ NEGATIVE curvature → Expect CHAOS")
            elif curv.is_positive:
                print("→ POSITIVE curvature → Expect regular motion")
            else:
                print("→ FLAT space → Possibly integrable")

            # Plot metric eigenvalues
            metric = compute_jm_metric(state, masses, energy, L)
            eigenvals = metric.eigenvalues()

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Metric eigenvalues
            ax1.bar(['λ₁', 'λ₂', 'λ₃'], eigenvals, color='steelblue')
            ax1.set_ylabel('Eigenvalue')
            ax1.set_title('JM Metric Eigenvalues')
            ax1.grid(True, alpha=0.3)

            # Ricci eigenvalues
            ricci_eigenvals = curv.ricci.eigenvalues()
            colors = ['red' if ev < 0 else 'green' for ev in ricci_eigenvals]
            ax2.bar(['R₁', 'R₂', 'R₃'], ricci_eigenvals, color=colors)
            ax2.axhline(0, color='black', linestyle='--', alpha=0.5)
            ax2.set_ylabel('Eigenvalue')
            ax2.set_title('Ricci Tensor Eigenvalues')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        except ValueError as e:
            print(f"Error: {e}")
```

---

## C4: Chaos-Curvature Scatter Plot

Visualize correlation between R and λ_max.

```python
# File: src/python/visualization/chaos_curvature_plot.py

def plot_chaos_curvature_correlation(
    correlation_results: CorrelationResults,
    save_path: Optional[str] = None
):
    """
    Scatter plot of R vs λ_max with regression line.
    """
    R = correlation_results.curvatures
    lambda_max = correlation_results.lyapunov_exponents

    fig, ax = plt.subplots(figsize=(10, 8))

    # Color by classification (chaotic vs regular)
    chaotic = lambda_max > 0.01

    scatter = ax.scatter(
        R, lambda_max,
        c=chaotic,
        cmap='RdYlGn_r',
        alpha=0.6,
        s=50,
        edgecolors='black',
        linewidths=0.5
    )

    # Decision boundaries
    ax.axvline(0, color='blue', linestyle='--', alpha=0.5, label='R = 0')
    ax.axhline(0, color='red', linestyle='--', alpha=0.5, label='λ = 0')

    # Regression line
    from scipy.stats import linregress
    slope, intercept, r_value, p_value, std_err = linregress(R, lambda_max)
    x_line = np.linspace(R.min(), R.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'k-', linewidth=2, alpha=0.7,
            label=f'Linear fit (r={correlation_results.pearson_r:.3f})')

    ax.set_xlabel('Scalar Curvature $R$', fontsize=14)
    ax.set_ylabel('Maximal Lyapunov Exponent $\\lambda_{\\mathrm{max}}$', fontsize=14)
    ax.set_title('Chaos-Curvature Correlation', fontsize=16)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # Add text box with statistics
    textstr = f'Pearson r: {correlation_results.pearson_r:.4f}\n'
    textstr += f'p-value: {correlation_results.pearson_p:.3e}\n'
    textstr += f'Accuracy: {correlation_results.classification_accuracy*100:.1f}%'

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)

    plt.colorbar(scatter, label='Chaotic (True/False)')

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()
```

---

## C5: Publication-Quality Figure Templates

```python
# File: src/python/visualization/publication_jm.py

import matplotlib as mpl

# Publication settings
PUBLICATION_CONFIG = {
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'figure.figsize': (8, 6),
    'figure.dpi': 300,
    'font.family': 'serif',
    'text.usetex': True,
}

def configure_for_publication():
    """Apply publication settings."""
    mpl.rcParams.update(PUBLICATION_CONFIG)


def create_figure_1_curvature_landscape():
    """
    Figure 1: Curvature landscape for equal-mass planar 3BP.

    Publication-ready figure showing negative curvature regions.
    """
    configure_for_publication()

    masses = Masses(1.0, 1.0, 1.0)
    energy = -1.0
    L = 1.0

    # High-resolution grid for smooth surface
    fig = plot_curvature_surface_3d(
        masses, energy,
        shape_region=((0.8, 1.2), (0.8, 1.2)),
        L_magnitude=L,
        resolution=100
    )

    # Save in multiple formats
    fig.savefig('Fig1_curvature_landscape.pdf', dpi=300, bbox_inches='tight')
    fig.savefig('Fig1_curvature_landscape.png', dpi=300, bbox_inches='tight')

    return fig


def create_figure_2_chaos_correlation():
    """
    Figure 2: Chaos-curvature correlation scatter plot.

    Main scientific result showing R < 0 ⟺ chaos.
    """
    configure_for_publication()

    # Compute correlation (1000 random initial conditions)
    # ...

    fig = plot_chaos_curvature_correlation(results)

    fig.savefig('Fig2_chaos_curvature.pdf', dpi=300, bbox_inches='tight')
    fig.savefig('Fig2_chaos_curvature.png', dpi=300, bbox_inches='tight')

    return fig
```

---

## Success Criteria

### Part C Complete When:

- [ ] Metric ellipsoid plots working
- [ ] Curvature landscape 3D visualization functional
- [ ] Interactive Jupyter widget responsive
- [ ] Chaos-curvature scatter plots generated
- [ ] Publication-quality templates created
- [ ] All visualizations render correctly
- [ ] Interactive tools work in notebooks
- [ ] Documentation complete with examples

**Ready to proceed to Part D** when all boxes checked.

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 1-2 days
**Next**: Part D (Scientific Validation)
