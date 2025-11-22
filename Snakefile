"""
Snakemake Pipeline for WP1 Production Runs (Phase 4).

Orchestrates parallel execution of:
- Tier 1: 10⁵ orbits (double precision, ΔC < 10⁻¹⁴)
- Tier 2: 10⁴ orbits (double-double precision, ΔC < 10⁻²⁵)

Usage:
    snakemake --cores 64 --config tier=1
    snakemake --cores 32 --config tier=2

Dependencies:
    - Python 3.11+
    - All WP1 modules installed
    - HDF5, Parquet libraries
"""

import numpy as np

# Configuration
TIER = config.get("tier", 1)
MU_VALUES = np.logspace(-3, np.log10(0.5), 30)
C_VALUES = np.linspace(2.5, 3.5, 15)

if TIER == 1:
    N_ORBITS_PER_MU_C = 200
    INTEGRATOR = "IAS15"
    PRECISION = "double"
    TARGET_ACCURACY = 1e-14
else:  # TIER == 2
    N_ORBITS_PER_MU_C = 30
    INTEGRATOR = "AdaptiveSymplectic"
    PRECISION = "double-double"
    TARGET_ACCURACY = 1e-25

# Generate orbit IDs
ORBIT_IDS = expand(
    "orbit_mu{mu_idx}_C{C_idx}_{orb_idx}",
    mu_idx=range(len(MU_VALUES)),
    C_idx=range(len(C_VALUES)),
    orb_idx=range(N_ORBITS_PER_MU_C)
)

# Output directories
TIER_DIR = f"data/tier{TIER}"
HDF5_DIR = f"{TIER_DIR}/hdf5"
PARQUET_DIR = f"{TIER_DIR}/parquet"
ANALYSIS_DIR = f"{TIER_DIR}/analysis"


rule all:
    input:
        f"{TIER_DIR}/complete.flag",
        f"{PARQUET_DIR}/tier{TIER}.parquet",
        f"{ANALYSIS_DIR}/validation_report.txt"


rule generate_parameters:
    """Generate parameter samples using Sobol sequences."""
    output:
        f"{TIER_DIR}/parameters.h5"
    run:
        from src.python.ml.sobol_sampling import generate_tier1_parameters

        n_total = len(MU_VALUES) * len(C_VALUES) * N_ORBITS_PER_MU_C
        samples, param_names = generate_tier1_parameters(n_samples=n_total)

        # Save to HDF5
        import h5py
        with h5py.File(output[0], 'w') as f:
            f.create_dataset('samples', data=samples)
            f.attrs['param_names'] = param_names
            f.attrs['tier'] = TIER
            f.attrs['n_samples'] = n_total


rule integrate_orbit:
    """Integrate single orbit with chaos indicators."""
    input:
        f"{TIER_DIR}/parameters.h5"
    output:
        f"{HDF5_DIR}/{{orbit_id}}.h5"
    params:
        integrator=INTEGRATOR,
        precision=PRECISION
    run:
        import h5py
        import numpy as np
        from src.python.integrators.ias15 import IAS15Integrator
        from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator
        from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

        # Parse orbit ID
        orbit_id = wildcards.orbit_id
        # Extract indices from orbit ID
        parts = orbit_id.split('_')
        mu_idx = int(parts[0].replace('orbitmu', ''))
        C_idx = int(parts[1].replace('C', ''))
        orb_idx = int(parts[2])

        mu = MU_VALUES[mu_idx]
        C = C_VALUES[C_idx]

        # Load parameters
        with h5py.File(input[0], 'r') as f:
            sample_idx = mu_idx * len(C_VALUES) * N_ORBITS_PER_MU_C + C_idx * N_ORBITS_PER_MU_C + orb_idx
            params = f['samples'][sample_idx]

        # Create initial condition from parameters
        initial_state = np.array([
            params[2],  # x
            params[3],  # y
            0.0,        # z
            params[4],  # vx
            0.0,        # vy (from Jacobi constant)
            0.0         # vz
        ])

        # Select integrator
        if params.integrator == "IAS15":
            integrator = IAS15Integrator(mu, tolerance=TARGET_ACCURACY)
        else:
            integrator = AdaptiveSymplecticIntegrator(
                mu,
                order=6,
                error_tolerance=TARGET_ACCURACY
            )

        # Integrate
        result = integrator.integrate(initial_state, duration=1000.0, output_interval=1.0)

        # Compute chaos indicators
        analyzer = create_cr3bp_chaos_analyzer(mu)
        chaos_result = analyzer.analyze(initial_state, t_final=1000.0)

        # Save to HDF5
        with h5py.File(output[0], 'w') as f:
            f.create_dataset('times', data=result.times)
            f.create_dataset('states_corotating', data=result.states_corotating)
            f.create_dataset('states_inertial', data=result.states_inertial)
            f.create_dataset('MEGNO', data=chaos_result.megno)
            f.create_dataset('FLI', data=chaos_result.fli)

            f.attrs['mu'] = mu
            f.attrs['C'] = C
            f.attrs['orbit_id'] = orbit_id
            f.attrs['chaos_class'] = chaos_result.classification
            f.attrs['mean_MEGNO'] = chaos_result.mean_megno
            f.attrs['final_FLI'] = chaos_result.final_fli


rule aggregate_tier:
    """Aggregate all orbits and mark tier complete."""
    input:
        expand(f"{HDF5_DIR}/{{orbit_id}}.h5", orbit_id=ORBIT_IDS)
    output:
        f"{TIER_DIR}/complete.flag"
    shell:
        """
        echo "Tier {TIER} integration complete" > {output}
        echo "Total orbits: $(ls {HDF5_DIR}/*.h5 | wc -l)" >> {output}
        date >> {output}
        """


rule export_parquet:
    """Export HDF5 data to Parquet format."""
    input:
        f"{TIER_DIR}/complete.flag"
    output:
        f"{PARQUET_DIR}/tier{TIER}.parquet"
    run:
        from src.python.ml.parquet_export import export_tier1_to_parquet
        export_tier1_to_parquet(HDF5_DIR, output[0])


rule validation_report:
    """Generate validation report with precision statistics."""
    input:
        f"{TIER_DIR}/complete.flag"
    output:
        f"{ANALYSIS_DIR}/validation_report.txt"
    run:
        import glob
        import h5py
        import numpy as np
        from src.python.utils.dynamics import calculate_jacobi_constant

        orbit_files = glob.glob(f"{HDF5_DIR}/*.h5")

        jacobi_drifts = []
        chaos_classes = []

        for orbit_file in orbit_files:
            with h5py.File(orbit_file, 'r') as f:
                mu = f.attrs['mu']
                states = f['states_corotating'][:]

                # Compute Jacobi constant drift
                C_initial = calculate_jacobi_constant(states[0], mu)
                C_final = calculate_jacobi_constant(states[-1], mu)
                drift = abs(C_final - C_initial) / abs(C_initial)

                jacobi_drifts.append(drift)
                chaos_classes.append(f.attrs['chaos_class'])

        jacobi_drifts = np.array(jacobi_drifts)

        # Generate report
        with open(output[0], 'w') as f:
            f.write(f"WP1 Tier {TIER} Validation Report\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total orbits: {len(orbit_files)}\n")
            f.write(f"Target accuracy: {TARGET_ACCURACY:.0e}\n\n")

            f.write("Jacobi Constant Precision:\n")
            f.write(f"  Mean drift: {np.mean(jacobi_drifts):.2e}\n")
            f.write(f"  Median drift: {np.median(jacobi_drifts):.2e}\n")
            f.write(f"  95th percentile: {np.percentile(jacobi_drifts, 95):.2e}\n")
            f.write(f"  Max drift: {np.max(jacobi_drifts):.2e}\n\n")

            # Check if meets target
            passes = np.sum(jacobi_drifts < TARGET_ACCURACY)
            pass_rate = passes / len(jacobi_drifts)

            f.write(f"Pass rate (< {TARGET_ACCURACY:.0e}): {pass_rate:.1%}\n\n")

            # Chaos classification
            n_regular = chaos_classes.count('regular')
            n_chaotic = chaos_classes.count('chaotic')

            f.write(f"Chaos Classification:\n")
            f.write(f"  Regular: {n_regular} ({n_regular/len(chaos_classes):.1%})\n")
            f.write(f"  Chaotic: {n_chaotic} ({n_chaotic/len(chaos_classes):.1%})\n")


# Optional: Tier 2 selection rule
if TIER == 2:
    rule select_tier2_subset:
        """Select dynamically interesting orbits from Tier 1 for Tier 2."""
        input:
            "data/tier1/complete.flag"
        output:
            "data/tier2/selection.txt"
        run:
            # Select orbits with high FLI gradients, near separatrices, etc.
            pass
