"""
Minimal Dry-Run Test Configuration
Created: 2025-11-24
Purpose: Quick smoke test (~10 minutes) for 24thNov2025-DryRun

Test Parameters:
- 10 test trajectories
- Lagrange L4 point (equilateral triangle configuration)
- Integration time: 100 time units
- Standard double precision (Tier 1)
- REBOUND IAS15 integrator
"""

import numpy as np

# Test Configuration
CONFIG = {
    "run_name": "24thNov2025-minimal",
    "test_scope": "minimal",

    # Trajectory Parameters
    "n_trajectories": 10,
    "integration_time": 100.0,  # Time units
    "output_interval": 0.1,     # Save every 0.1 time units
    "precision": "double",       # Standard double precision
    "integrator": "ias15",       # REBOUND IAS15 (15th-order adaptive)

    # Three-body parameters
    "mass_ratio": 0.5,  # μ = 0.5 (equal mass case)

    # Initial conditions: Lagrange L4 (equilateral triangle)
    "initial_conditions": {
        "type": "lagrange_l4",
        "config": "equilateral",
        "perturbation": 1e-6,  # Small perturbation to test stability
    },

    # Integration settings
    "tolerance": 1e-14,  # IAS15 tolerance
    "min_dt": 1e-10,     # Minimum timestep
    "max_dt": 0.1,       # Maximum timestep

    # Validation settings
    "validation": {
        "conservation_check": True,
        "energy_tolerance": 1e-13,  # |ΔE/E| should be < 10⁻¹³
        "angular_momentum_check": True,
        "chaos_indicators": False,  # Skip for minimal run
        "analytical_vetting": False,  # Skip for minimal run
    },

    # Output settings
    "output": {
        "save_hdf5": True,
        "save_parquet": False,  # Skip for minimal run
        "generate_plots": True,
        "log_level": "INFO",
        "output_dir": "Dry-Run/24thNov2025-DryRun/data/trajectories",
        "log_dir": "Dry-Run/24thNov2025-DryRun/logs",
        "plot_dir": "Dry-Run/24thNov2025-DryRun/plots",
    },
}

# Lagrange L4 initial conditions (Circular Restricted Three-Body Problem)
# For μ = 0.5, the equilibrium points form an equilateral triangle
# Position: (x, y) = (-0.5 + μ, ±√3/2)
# Velocity: circular orbit velocity

def get_l4_initial_state(mu=0.5, perturbation=1e-6):
    """
    Generate initial conditions for Lagrange L4 point.

    Args:
        mu: Mass parameter (0 < μ < 1)
        perturbation: Small displacement from equilibrium (for stability test)

    Returns:
        state: [x, y, z, vx, vy, vz] in rotating frame
    """
    # L4 position in rotating frame
    x = 0.5 - mu
    y = np.sqrt(3) / 2
    z = 0.0

    # Circular velocity in rotating frame
    vx = -y  # Rotating frame velocity
    vy = x
    vz = 0.0

    # Add small perturbation
    x += perturbation * np.random.randn()
    y += perturbation * np.random.randn()

    return np.array([x, y, z, vx, vy, vz])


# Expected outcomes for L4 test:
# - All 10 trajectories should complete without errors
# - Energy conservation: |ΔC/C| < 10⁻¹⁴ (Jacobi constant)
# - L4 position should remain stable (< 10⁻³ drift over 100 time units)
# - Integration time: ~5-10 minutes for 10 orbits

EXPECTED_RESULTS = {
    "success_rate": 1.0,  # 100% completion expected
    "energy_conservation": 1e-14,
    "max_position_drift": 1e-3,
    "expected_duration_minutes": 10,
}
