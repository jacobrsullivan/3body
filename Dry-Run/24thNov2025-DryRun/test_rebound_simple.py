#!/usr/bin/env python3
"""
Simple REBOUND test - verify basic integration works
"""
import rebound
import numpy as np

print("Testing basic REBOUND integration...")

# Create simulation
sim = rebound.Simulation()
sim.integrator = "ias15"

# Add Sun, Earth, Jupiter (simple example)
sim.add(m=1.0)  # Sun
sim.add(m=3e-6, a=1.0, e=0.0167)  # Earth-like
sim.add(m=1e-3, a=5.2, e=0.048)  # Jupiter-like

# Move to center of mass
sim.move_to_com()

print(f"Initial energy: {sim.energy():.6e}")
print(f"Number of particles: {sim.N}")

# Integrate for 10 time units with 10 outputs
times = np.linspace(0, 10, 11)
print("\nIntegrating...")

for i, t in enumerate(times):
    sim.integrate(t)
    E = sim.energy()
    print(f"t={t:5.1f}, E={E:.6e}, particles={sim.N}")

print("\n✓ Integration completed successfully!")
