#!/usr/bin/env python3
"""
Simple Trajectory Test - v2
Minimal test with short integration time and few output points
"""
import sys
from pathlib import Path

# Validate working directory
PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "CLAUDE.md").exists():
    print(f"ERROR: Must run from project root")
    print(f"Current: {PROJECT_ROOT}")
    sys.exit(1)

print(f"✓ Working directory: {PROJECT_ROOT}")

import rebound
import numpy as np
import h5py
import time

print("\n" + "=" * 70)
print("Simple Trajectory Test - 24thNov2025-DryRun-v2")
print("=" * 70)

# Configuration
CONFIG = {
    "integration_time": 10.0,  # Short: just 10 time units
    "n_outputs": 50,  # Only 50 output points
    "output_dir": PROJECT_ROOT
    / "Dry-Run"
    / "24thNov2025-DryRun-v2"
    / "data"
    / "trajectories",
}

print(f"\nConfiguration:")
print(f"  Integration time: {CONFIG['integration_time']} time units")
print(f"  Output points: {CONFIG['n_outputs']}")
print(f"  Output directory: {CONFIG['output_dir']}")

# Create simulation - simple circular restricted 3-body
print("\nCreating REBOUND simulation...")
sim = rebound.Simulation()
sim.integrator = "ias15"

# Add 3 bodies - simplified equal mass case
# Primary at origin
sim.add(m=0.5, x=-0.5, y=0, vx=0, vy=-0.5)

# Secondary
sim.add(m=0.5, x=0.5, y=0, vx=0, vy=0.5)

# Third body (test particle) at L4-ish location
sim.add(m=1e-6, x=0, y=0.866, vx=-0.5, vy=0)

sim.move_to_com()

E_initial = sim.energy()
print(f"Initial energy: {E_initial:.6e}")
print(f"Number of particles: {sim.N}")

# Integration
times = np.linspace(0, CONFIG["integration_time"], CONFIG["n_outputs"])
positions = np.zeros((CONFIG["n_outputs"], 3, 3))
velocities = np.zeros((CONFIG["n_outputs"], 3, 3))
energies = np.zeros(CONFIG["n_outputs"])

print(f"\nIntegrating for {CONFIG['integration_time']} time units...")
start_time = time.time()

for i, t in enumerate(times):
    sim.integrate(t)

    for j in range(3):
        p = sim.particles[j]
        positions[i, j] = [p.x, p.y, p.z]
        velocities[i, j] = [p.vx, p.vy, p.vz]

    energies[i] = sim.energy()

    if i % 10 == 0 or i == len(times) - 1:
        dE = abs((energies[i] - E_initial) / E_initial)
        print(f"  t={t:5.2f}, E={energies[i]:.6e}, |ΔE/E|={dE:.3e}")

elapsed = time.time() - start_time

print(f"\n✓ Integration completed in {elapsed:.2f} seconds")

# Check energy conservation
E_final = energies[-1]
dE_relative = abs((E_final - E_initial) / E_initial)

print(f"\nEnergy Conservation:")
print(f"  Initial: {E_initial:.10e}")
print(f"  Final:   {E_final:.10e}")
print(f"  |ΔE/E|:  {dE_relative:.3e}")

tolerance = 1e-13
if dE_relative < tolerance:
    print(f"  ✓ PASS (|ΔE/E| < {tolerance:.0e})")
    status = "PASS"
else:
    print(f"  ✗ FAIL (|ΔE/E| > {tolerance:.0e})")
    status = "FAIL"

# Save to HDF5
CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)
output_file = CONFIG["output_dir"] / "simple_trajectory_v2.h5"

print(f"\nSaving trajectory to: {output_file}")
with h5py.File(output_file, "w") as f:
    f.create_dataset("time", data=times)
    f.create_dataset("positions", data=positions)
    f.create_dataset("velocities", data=velocities)
    f.create_dataset("energies", data=energies)

    f.attrs["status"] = status
    f.attrs["E_initial"] = E_initial
    f.attrs["E_final"] = E_final
    f.attrs["dE_relative"] = dE_relative
    f.attrs["integration_time"] = CONFIG["integration_time"]
    f.attrs["n_outputs"] = CONFIG["n_outputs"]
    f.attrs["elapsed_time"] = elapsed

print(f"✓ Trajectory saved")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Status: {status}")
print(f"Energy conservation: {dE_relative:.3e}")
print(f"Integration time: {elapsed:.2f} seconds")
print(f"Output file: {output_file}")
print("=" * 70)

sys.exit(0 if status == "PASS" else 1)
