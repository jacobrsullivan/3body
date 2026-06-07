#!/usr/bin/env python3
"""
Minimal Dry-Run Test Script
Date: 2025-11-24
Purpose: Execute minimal dry-run test for environment validation

This script:
1. Generates 10 test trajectories at Lagrange L4
2. Checks energy conservation
3. Validates basic integration functionality
4. Logs results to dry-run logs

Usage:
    python run_minimal_test.py
"""

import sys
import os
import time
import numpy as np
import h5py
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "python"))

# Import configuration
from configs.minimal_test_config import CONFIG, get_l4_initial_state

# Setup logging
import logging

log_file = Path(CONFIG["output"]["log_dir"]) / "minimal_test_execution.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def test_rebound_integration():
    """
    Test basic REBOUND integration with Lagrange L4 initial conditions.
    """
    try:
        import rebound

        logger.info("Testing REBOUND integration...")

        # Create REBOUND simulation
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.dt = 0.01  # Initial timestep guess

        # Set up circular restricted three-body problem
        # Primary mass at origin
        sim.add(m=1.0 - CONFIG["mass_ratio"], x=-CONFIG["mass_ratio"], y=0, z=0)

        # Secondary mass
        sim.add(m=CONFIG["mass_ratio"], x=1.0 - CONFIG["mass_ratio"], y=0, z=0)

        # Third body at L4
        state = get_l4_initial_state(
            mu=CONFIG["mass_ratio"],
            perturbation=CONFIG["initial_conditions"]["perturbation"],
        )

        # Add third body (massless test particle)
        sim.add(
            m=0.0,  # Massless
            x=state[0],
            y=state[1],
            z=state[2],
            vx=state[3],
            vy=state[4],
            vz=state[5],
        )

        # Move to center of mass frame
        sim.move_to_com()

        # Store initial energy
        E_initial = sim.energy()
        logger.info(f"Initial energy: {E_initial:.15e}")

        # Integration
        n_outputs = int(CONFIG["integration_time"] / CONFIG["output_interval"])
        times = np.linspace(0, CONFIG["integration_time"], n_outputs)

        positions = np.zeros((n_outputs, 3, 3))  # (time, particle, xyz)
        velocities = np.zeros((n_outputs, 3, 3))
        energies = np.zeros(n_outputs)

        logger.info(f"Integrating for {CONFIG['integration_time']} time units...")
        start_time = time.time()

        for i, t in enumerate(times):
            sim.integrate(t)

            # Store particle states
            for j in range(3):
                p = sim.particles[j]
                positions[i, j] = [p.x, p.y, p.z]
                velocities[i, j] = [p.vx, p.vy, p.vz]

            energies[i] = sim.energy()

            if i % 100 == 0:
                dE = abs((energies[i] - E_initial) / E_initial)
                logger.info(f"t={t:.2f}, |ΔE/E|={dE:.3e}")

        elapsed = time.time() - start_time
        logger.info(f"Integration completed in {elapsed:.2f} seconds")

        # Check energy conservation
        E_final = energies[-1]
        dE_relative = abs((E_final - E_initial) / E_initial)

        logger.info(f"Final energy: {E_final:.15e}")
        logger.info(f"Relative energy error: {dE_relative:.3e}")

        # Validate
        tolerance = CONFIG["validation"]["energy_tolerance"]
        if dE_relative < tolerance:
            logger.info(f"✓ Energy conservation PASSED (|ΔE/E| < {tolerance:.0e})")
            status = "PASS"
        else:
            logger.warning(
                f"✗ Energy conservation FAILED (|ΔE/E| = {dE_relative:.3e} > {tolerance:.0e})"
            )
            status = "FAIL"

        # Save trajectory to HDF5
        output_dir = Path(CONFIG["output"]["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "test_trajectory_001.h5"
        with h5py.File(output_file, "w") as f:
            f.create_dataset("time", data=times)
            f.create_dataset("positions", data=positions)
            f.create_dataset("velocities", data=velocities)
            f.create_dataset("energies", data=energies)

            # Metadata
            f.attrs["status"] = status
            f.attrs["E_initial"] = E_initial
            f.attrs["E_final"] = E_final
            f.attrs["dE_relative"] = dE_relative
            f.attrs["integration_time"] = CONFIG["integration_time"]
            f.attrs["n_outputs"] = n_outputs
            f.attrs["mass_ratio"] = CONFIG["mass_ratio"]

        logger.info(f"Trajectory saved to {output_file}")

        return {
            "status": status,
            "energy_error": dE_relative,
            "integration_time": elapsed,
            "output_file": str(output_file),
        }

    except Exception as e:
        logger.error(f"Integration failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return {"status": "ERROR", "error": str(e)}


def main():
    """Run minimal dry-run test."""
    logger.info("=" * 60)
    logger.info("24thNov2025 Minimal Dry-Run Test")
    logger.info("=" * 60)

    # Test 1: Single trajectory with REBOUND
    logger.info("\nTest 1: REBOUND Integration at L4")
    logger.info("-" * 60)

    result = test_rebound_integration()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DRY-RUN TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Status: {result['status']}")

    if result["status"] == "PASS":
        logger.info(f"Energy conservation: {result['energy_error']:.3e}")
        logger.info(f"Integration time: {result['integration_time']:.2f} seconds")
        logger.info(f"Output file: {result['output_file']}")
        logger.info("\n✓ Minimal dry-run test PASSED")
        return 0
    else:
        logger.error("\n✗ Minimal dry-run test FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
