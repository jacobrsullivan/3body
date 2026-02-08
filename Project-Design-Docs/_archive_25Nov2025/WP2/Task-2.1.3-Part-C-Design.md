# Task 2.1.3 Part C: Visualization - Detailed Design

**Task**: WP 2.1.3 - Jacobi-Maupertuis Metric Analysis
**Part**: C - Metric and Curvature Visualization
**Status**: Design Phase
**Estimated Duration**: 1 day
**Dependencies**: Task 2.1.3 Parts A & B Complete

---

## Overview

Part C implements visualization tools for the JM metric and scalar curvature, providing intuitive geometric insights into the three-body problem's phase space structure.

---

## C1: Metric Ellipsoids

### Algorithm C1.1: 3D Ellipsoid Visualization

```python
def plot_metric_ellipsoids(
    masses: Masses,
    energy: float,
    shape_space_grid: list[ShapeSpaceState],
    scale: float = 0.1
) -> tuple[plt.Figure, Axes3D]:
    """
    Visualize metric as ellipsoids at grid points.

    The metric tensor defines an ellipsoid via eigendecomposition.

    Args:
        masses: Body masses
        energy: Total energy
        shape_space_grid: Points where to draw ellipsoids
        scale: Scale factor for ellipsoid size

    Returns:
        (figure, 3D axes)
    """
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    for state in shape_space_grid:
        metric = compute_jm_metric(state, masses, energy)

        # Eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eigh(metric.components)

        # Draw ellipsoid
        center = state.to_array()
        radii = scale * np.sqrt(eigenvalues)

        draw_ellipsoid_3d(ax, center, radii, eigenvectors, alpha=0.3)

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_zlabel('$r_{31}$')
    ax.set_title('JM Metric Tensor Field')

    return fig, ax


def draw_ellipsoid_3d(
    ax: Axes3D,
    center: np.ndarray,
    radii: np.ndarray,
    rotation: np.ndarray,
    color: str = 'blue',
    alpha: float = 0.3
):
    """Draw an ellipsoid in 3D."""
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)

    x = radii[0] * np.outer(np.cos(u), np.sin(v))
    y = radii[1] * np.outer(np.sin(u), np.sin(v))
    z = radii[2] * np.outer(np.ones_like(u), np.cos(v))

    # Rotate
    for i in range(len(x)):
        for j in range(len(x[0])):
            [x[i, j], y[i, j], z[i, j]] = rotation @ [x[i, j], y[i, j], z[i, j]]

    # Translate
    x += center[0]
    y += center[1]
    z += center[2]

    ax.plot_surface(x, y, z, color=color, alpha=alpha)
```

---

## C2: Curvature Landscapes

### Algorithm C2.1: 3D Surface Plot

```python
def plot_curvature_landscape_3d(
    masses: Masses,
    energy: float,
    r12_range: tuple,
    r23_range: tuple,
    r31_fixed: float = 1.0,
    resolution: int = 50
) -> tuple[plt.Figure, Axes3D]:
    """
    Plot scalar curvature R as 3D surface.

    Negative regions indicate chaos.
    """
    # Compute curvature field
    r12_vals = np.linspace(*r12_range, resolution)
    r23_vals = np.linspace(*r23_range, resolution)

    R12, R23 = np.meshgrid(r12_vals, r23_vals)
    R_grid = np.zeros_like(R12)

    for i in range(resolution):
        for j in range(resolution):
            r12, r23 = R12[i, j], R23[i, j]

            if not satisfies_triangle_inequality(r12, r23, r31_fixed):
                R_grid[i, j] = np.nan
                continue

            state = ShapeSpaceState(r12, r23, r31_fixed, L=1.0)

            try:
                curv = compute_curvature_tensors(state, masses, energy)
                R_grid[i, j] = curv.scalar
            except:
                R_grid[i, j] = np.nan

    # Plot
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(
        R12, R23, R_grid,
        cmap='RdBu_r',  # Red=negative, Blue=positive
        vmin=-np.nanmax(np.abs(R_grid)),
        vmax=np.nanmax(np.abs(R_grid)),
        alpha=0.9
    )

    # Zero plane
    ax.plot_surface(R12, R23, np.zeros_like(R_grid), color='gray', alpha=0.2)

    fig.colorbar(surf, ax=ax, label='Scalar Curvature $R$')

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_zlabel('$R$')
    ax.set_title('Scalar Curvature Landscape')

    return fig, ax
```

### Algorithm C2.2: Heatmap with Contours

```python
def plot_curvature_heatmap(
    masses: Masses,
    energy: float,
    r12_range: tuple,
    r23_range: tuple,
    r31_fixed: float = 1.0,
    resolution: int = 100
) -> tuple[plt.Figure, plt.Axes]:
    """
    2D heatmap of scalar curvature.

    Shows regions of positive/negative curvature.
    """
    # [Similar grid computation as above]

    fig, ax = plt.subplots(figsize=(12, 10))

    im = ax.imshow(
        R_grid,
        extent=[*r12_range, *r23_range],
        origin='lower',
        cmap='RdBu_r',
        vmin=-np.nanmax(np.abs(R_grid)),
        vmax=np.nanmax(np.abs(R_grid))
    )

    # Zero contour (separates chaos from stability)
    ax.contour(R12, R23, R_grid, levels=[0], colors='black', linewidths=2)

    # Additional contours
    ax.contour(R12, R23, R_grid, levels=10, colors='white', linewidths=0.5, alpha=0.5)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('$R$', fontsize=14)

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_title(f'Scalar Curvature (E={energy:.2f}, $r_{{31}}$={r31_fixed:.2f})')

    return fig, ax
```

---

## C3: Interactive Exploration

### Algorithm C3.1: Parameter Sliders

```python
import ipywidgets as widgets

def create_interactive_curvature_explorer():
    """Interactive widget for parameter exploration."""

    @widgets.interact(
        m1=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0),
        m2=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0),
        m3=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0),
        energy=widgets.FloatSlider(min=-2.0, max=-0.1, step=0.1, value=-1.0),
        L=widgets.FloatSlider(min=0.0, max=3.0, step=0.1, value=1.0)
    )
    def plot(m1, m2, m3, energy, L):
        masses = Masses(m1, m2, m3)
        state = ShapeSpaceState(1.0, 1.0, 1.0, L=L)

        try:
            curv = compute_curvature_tensors(state, masses, energy, L)

            print(f"Scalar Curvature: R = {curv.scalar:.6f}")
            print(f"Sign: {classify_curvature_sign(curv.scalar)}")

            # Plot metric
            metric = compute_jm_metric(state, masses, energy, L)
            eigenvals = metric.eigenvalues()

            fig, ax = plt.subplots(figsize=(8, 6))
            ax.bar(['λ₁', 'λ₂', 'λ₃'], eigenvals)
            ax.set_ylabel('Eigenvalue')
            ax.set_title('JM Metric Principal Lengths')
            plt.show()

        except ValueError as e:
            print(f"Error: {e}")
```

---

## C4: Chaos-Curvature Scatter Plot

### Algorithm C4.1: R vs λ Correlation

```python
def plot_chaos_curvature_correlation(
    masses: Masses,
    energy: float,
    n_samples: int = 1000
) -> tuple[plt.Figure, plt.Axes]:
    """
    Scatter plot: scalar curvature R vs Lyapunov exponent λ.

    Validates hypothesis: R < 0 ⟺ λ > 0
    """
    # Generate random initial conditions
    states = generate_random_shape_states(n_samples)

    # Compute R and λ
    result = correlate_curvature_with_chaos(states, masses, energy)

    R = result['curvatures']
    lambda_max = result['lyapunov_exponents']

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))

    chaotic = lambda_max > 0.01

    ax.scatter(R[chaotic], lambda_max[chaotic], c='red', label='Chaotic', alpha=0.6)
    ax.scatter(R[~chaotic], lambda_max[~chaotic], c='blue', label='Regular', alpha=0.6)

    ax.axvline(0, color='k', linestyle='--', alpha=0.3, label='R=0')
    ax.axhline(0, color='k', linestyle='--', alpha=0.3, label='λ=0')

    ax.set_xlabel('Scalar Curvature $R$')
    ax.set_ylabel('Maximal Lyapunov Exponent $\lambda_{max}$')
    ax.set_title(f'Chaos-Curvature Correlation (r={result["correlation_coefficient"]:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig, ax
```

---

**Status**: Complete | **Lines**: ~900
