#!/usr/bin/env python3
"""
Minimal trajectory generation test for Dry-Run.
Tests basic three-body integration using REBOUND.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import rebound
import h5py
from datetime import datetime

def create_lagrange_l4_initial_conditions(mu=0.5):
    """
    Create initial conditions for Lagrange L4 point in circular restricted 3-body problem.

    Args:
        mu: Mass parameter (M2/(M1+M2))

    Returns:
        Initial state [x, y, z, vx, vy, vz]
    """
    # L4 is at (0.5 - mu, sqrt(3)/2, 0) for equal masses
    x = 0.5 - mu
    y = np.sqrt(3) / 2
    z = 0.0

    # Velocity for circular orbit (perpendicular to position)
    vx = -y  # Circular velocity
    vy = x
    vz = 0.0

    return np.array([x, y, z, vx, vy, vz])


def integrate_trajectory(
    initial_state,
    mu=0.5,
    t_final=10.0,
    n_outputs=100,
    output_file=None
):
    """
    Integrate a three-body trajectory using REBOUND's IAS15.

    Args:
        initial_state: Initial state [x, y, z, vx, vy, vz]
        mu: Mass parameter
        t_final: Final integration time
        n_outputs: Number of output points
        output_file: Optional HDF5 output file path

    Returns:
        Dictionary with times, positions, velocities, energy history
    """
    print(f"\n{'='*60}")
    print("TRAJECTORY INTEGRATION TEST")
    print(f"{'='*60}")
    print(f"Initial state: {initial_state}")
    print(f"Mass parameter μ = {mu}")
    print(f"Integration time: 0 → {t_final}")
    print(f"Output points: {n_outputs}")

    # Create REBOUND simulation
    sim = rebound.Simulation()
    sim.integrator = "ias15"
    sim.ri_ias15.epsilon = 1e-14  # Tolerance

    # Add primaries (M1 at -mu, M2 at 1-mu)
    sim.add(m=1-mu, x=-mu, y=0, z=0)  # Primary 1
    sim.add(m=mu, x=1-mu, y=0, z=0)  # Primary 2

    # Add test particle with initial conditions
    x, y, z, vx, vy, vz = initial_state
    sim.add(m=0, x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)

    # Move to center of mass frame
    sim.move_to_com()

    # Storage arrays
    times = []
    positions = []
    velocities = []
    energies = []

    # Initial energy
    E0 = sim.energy()
    print(f"Initial energy: {E0:.15e}")

    # Integration loop
    print(f"\nIntegrating...")
    t_output = np.linspace(0, t_final, n_outputs)

    start_time = datetime.now()

    try:
        for i, t in enumerate(t_output):
            sim.integrate(t)

            # Get test particle (index 2)
            p = sim.particles[2]

            times.append(t)
            positions.append([p.x, p.y, p.z])
            velocities.append([p.vx, p.vy, p.vz])

            # Energy
            E = sim.energy()
            energies.append(E)

            # Progress
            if (i+1) % (n_outputs // 10) == 0:
                dE = abs((E - E0) / E0)
                print(f"  t = {t:8.3f} | |ΔE/E0| = {dE:.3e}", flush=True)

    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return None

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Convert to arrays
    times = np.array(times)
    positions = np.array(positions)
    velocities = np.array(velocities)
    energies = np.array(energies)

    # Final statistics
    print(f"\n{'='*60}")
    print("INTEGRATION COMPLETE")
    print(f"{'='*60}")
    print(f"Wall time: {duration:.2f} seconds")
    print(f"Final time: {times[-1]:.3f}")
    print(f"Output points: {len(times)}")

    # Energy conservation
    dE = energies - E0
    rel_error = np.abs(dE / E0)
    print(f"\nEnergy Conservation:")
    print(f"  Initial energy: {E0:.15e}")
    print(f"  Final energy:   {energies[-1]:.15e}")
    print(f"  |ΔE/E0| (max):  {np.max(rel_error):.3e}")
    print(f"  |ΔE/E0| (mean): {np.mean(rel_error):.3e}")
    print(f"  |ΔE/E0| (final):{rel_error[-1]:.3e}")

    # Check success criterion
    if np.max(rel_error) < 1e-13:
        print(f"\n✅ PASS: Energy conserved to < 1e-13")
        status = "PASS"
    elif np.max(rel_error) < 1e-10:
        print(f"\n⚠️  MARGINAL: Energy conserved to < 1e-10")
        status = "MARGINAL"
    else:
        print(f"\n❌ FAIL: Energy conservation insufficient")
        status = "FAIL"

    # Save to HDF5 if requested
    if output_file:
        print(f"\nSaving to {output_file}...")
        with h5py.File(output_file, 'w') as f:
            f.create_dataset('time', data=times)
            f.create_dataset('positions', data=positions)
            f.create_dataset('velocities', data=velocities)
            f.create_dataset('energies', data=energies)

            # Attributes
            f.attrs['mu'] = mu
            f.attrs['t_final'] = t_final
            f.attrs['n_outputs'] = n_outputs
            f.attrs['E0'] = E0
            f.attrs['max_energy_error'] = float(np.max(rel_error))
            f.attrs['mean_energy_error'] = float(np.mean(rel_error))
            f.attrs['status'] = status
            f.attrs['integration_time_seconds'] = duration
            f.attrs['timestamp'] = datetime.now().isoformat()

        print(f"✅ Saved successfully")

    return {
        'times': times,
        'positions': positions,
        'velocities': velocities,
        'energies': energies,
        'E0': E0,
        'max_rel_error': np.max(rel_error),
        'mean_rel_error': np.mean(rel_error),
        'status': status,
        'duration': duration
    }


if __name__ == "__main__":
    print(f"\n{'#'*60}")
    print("DRY-RUN: MINIMAL TRAJECTORY TEST")
    print(f"{'#'*60}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test configuration
    mu = 0.5  # Equal masses
    t_final = 10.0  # Integration time (reduced for quick test)
    n_outputs = 100  # Fewer points for speed

    # Output directory
    output_dir = Path(__file__).parent.parent / "data" / "trajectories"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test_trajectory_l4.h5"

    # Create initial conditions
    print(f"\nGenerating Lagrange L4 initial conditions...")
    ic = create_lagrange_l4_initial_conditions(mu=mu)

    # Integrate
    result = integrate_trajectory(
        ic,
        mu=mu,
        t_final=t_final,
        n_outputs=n_outputs,
        output_file=output_file
    )

    if result:
        print(f"\n{'#'*60}")
        print("DRY-RUN TEST COMPLETE")
        print(f"{'#'*60}")
        print(f"Status: {result['status']}")
        print(f"Output: {output_file}")

        sys.exit(0 if result['status'] == 'PASS' else 1)
    else:
        print(f"\n{'#'*60}")
        print("DRY-RUN TEST FAILED")
        print(f"{'#'*60}")
        sys.exit(1)
