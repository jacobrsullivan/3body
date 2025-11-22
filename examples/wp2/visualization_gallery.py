"""
Visualization gallery for WP2.

Demonstrates all major visualization functions with example data.
"""

import numpy as np
import matplotlib.pyplot as plt

from src.python.visualization import (
    plot_connection_field,
    plot_connection_magnitude_heatmap,
    plot_curvature_heatmap,
    plot_shape_trajectory,
    plot_lift_comparison
)


def example_connection_evaluator(r12, r23, r31):
    """Example connection evaluator function."""
    # Simple model: connection proportional to angular momentum / moment of inertia
    L = r12 * r23 * r31  # Proxy for angular momentum
    I = r12**2 + r23**2 + r31**2  # Proxy for moment of inertia

    A = L / (I + 0.1)  # Add small constant to avoid division by zero

    return (A * 0.1, A * 0.1, 0.0)


def example_curvature_evaluator(r12, r23, r31):
    """Example curvature evaluator function."""
    # Curvature as obstruction to integrability
    # Higher when bodies are close

    F = 1.0 / (r12 * r23 * r31 + 0.1)

    return F


def demo_connection_plots():
    """Demonstrate connection visualization."""
    print("\n1. Connection Visualization")
    print("-" * 50)

    # Vector field
    print("   Creating connection vector field...")
    fig1 = plot_connection_field(
        example_connection_evaluator,
        grid_resolution=20,
        arrow_scale=10.0,
        title="Connection Vector Field (Example)"
    )
    plt.savefig('connection_field.png', dpi=150)
    print("   → Saved: connection_field.png")
    plt.close(fig1)

    # Magnitude heatmap
    print("   Creating connection magnitude heatmap...")
    fig2 = plot_connection_magnitude_heatmap(
        example_connection_evaluator,
        grid_resolution=80,
        log_scale=False,
        title="Connection Magnitude (Example)"
    )
    plt.savefig('connection_heatmap.png', dpi=150)
    print("   → Saved: connection_heatmap.png")
    plt.close(fig2)


def demo_curvature_plots():
    """Demonstrate curvature visualization."""
    print("\n2. Curvature Visualization")
    print("-" * 50)

    print("   Creating curvature heatmap...")
    fig = plot_curvature_heatmap(
        example_curvature_evaluator,
        grid_resolution=80,
        log_scale=True,
        title="Curvature Magnitude (Example, Log Scale)"
    )
    plt.savefig('curvature_heatmap.png', dpi=150)
    print("   → Saved: curvature_heatmap.png")
    plt.close(fig)


def demo_trajectory_plots():
    """Demonstrate trajectory visualization."""
    print("\n3. Trajectory Visualization")
    print("-" * 50)

    # Generate example trajectory (spiral in shape space)
    t = np.linspace(0, 10, 200)
    r_center = 1.5
    r_amplitude = 0.5

    trajectory = np.column_stack([
        r_center + r_amplitude * np.cos(t) * np.exp(-t/20),
        r_center + r_amplitude * np.sin(t) * np.exp(-t/20)
    ])

    print("   Creating shape space trajectory plot...")
    fig = plot_shape_trajectory(
        trajectory,
        color_by='time',
        title="Example Trajectory in Shape Space"
    )
    plt.savefig('shape_trajectory.png', dpi=150)
    print("   → Saved: shape_trajectory.png")
    plt.close(fig)


def demo_lift_comparison():
    """Demonstrate lift comparison visualization."""
    print("\n4. Lift Comparison")
    print("-" * 50)

    # Generate example data
    t = np.linspace(0, 8, 150)
    r_center = 1.5
    r_amp = 0.4

    # Reduced (shape space)
    traj_reduced = np.column_stack([
        r_center + r_amp * np.cos(t),
        r_center + r_amp * np.sin(t)
    ])

    # S¹ lift (add fiber coordinate θ)
    theta = np.mod(3*t, 2*np.pi)
    traj_s1 = np.column_stack([
        traj_reduced[:, 0],
        traj_reduced[:, 1],
        theta
    ])

    print("   Creating lift comparison plot...")
    fig = plot_lift_comparison(
        traj_reduced,
        traj_s1=traj_s1,
        title="S¹ Lift vs. Reduced Space (Example)"
    )
    plt.savefig('lift_comparison.png', dpi=150)
    print("   → Saved: lift_comparison.png")
    plt.close(fig)


def main():
    """Run all visualization examples."""
    print("="*60)
    print("WP2 Visualization Gallery")
    print("="*60)

    try:
        demo_connection_plots()
        demo_curvature_plots()
        demo_trajectory_plots()
        demo_lift_comparison()

        print("\n" + "="*60)
        print("Visualization gallery complete!")
        print("All plots saved to current directory.")
        print("="*60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
