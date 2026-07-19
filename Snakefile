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

from src.python.validation.qualification import qualification_metadata

# Configuration
TIER = int(config.get("tier", 1))

# mu configuration: allow explicit list, fixed value, or logspace range
MU_VALUES = config.get("mu_values")
if MU_VALUES is None:
    mu_single = config.get("mu")
    if mu_single is not None:
        MU_VALUES = np.array([float(mu_single)])
    else:
        n_mu = int(config.get("n_mu", 30))
        mu_min = float(config.get("mu_min", 1e-3))
        mu_max = float(config.get("mu_max", 0.5))
        MU_VALUES = np.logspace(np.log10(mu_min), np.log10(mu_max), n_mu)
else:
    MU_VALUES = np.array(MU_VALUES, dtype=float)

# C configuration: allow explicit list or linear range
C_VALUES = config.get("C_values")
if C_VALUES is None:
    n_C = int(config.get("n_C", 15))
    C_min = float(config.get("C_min", 2.5))
    C_max = float(config.get("C_max", 3.5))
    C_VALUES = np.linspace(C_min, C_max, n_C)
else:
    C_VALUES = np.array(C_VALUES, dtype=float)

# Per-tier configuration
if TIER == 1:
    N_ORBITS_PER_MU_C = int(config.get("n_orbits_per_mu_c", 200))
    INTEGRATOR = "IAS15"
    PRECISION = "double"
    TARGET_ACCURACY = float(config.get("target_accuracy", 1e-14))
else:  # TIER == 2
    N_ORBITS_PER_MU_C = int(config.get("n_orbits_per_mu_c", 30))
    INTEGRATOR = "HeyokaTaylor"
    PRECISION = "heyoka-real"
    TARGET_ACCURACY = float(config.get("target_accuracy", 1e-25))
    PRECISION_BITS = int(config.get("precision_bits", 160))

DURATION = float(config.get("duration", 1000.0))
OUTPUT_INTERVAL = float(config.get("output_interval", 1.0))
SEED = int(config.get("seed", 42))
REQUIRE_QUALIFICATION = bool(config.get("require_qualification", True))
QUALIFICATION_METADATA = (
    qualification_metadata(require_pass=True) if REQUIRE_QUALIFICATION else {}
)

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
        from src.python.ml.sobol_sampling import generate_initial_states_for_mu_c

        n_total = len(MU_VALUES) * len(C_VALUES) * N_ORBITS_PER_MU_C
        states = np.zeros((n_total, 6))

        idx = 0
        for mu_idx, mu in enumerate(MU_VALUES):
            for C_idx, C in enumerate(C_VALUES):
                block_seed = SEED + mu_idx * 1000 + C_idx
                block = generate_initial_states_for_mu_c(
                    mu=mu,
                    C=C,
                    n_samples=N_ORBITS_PER_MU_C,
                    seed=block_seed,
                )
                states[idx:idx + N_ORBITS_PER_MU_C] = block
                idx += N_ORBITS_PER_MU_C

        # Save to HDF5
        import h5py
        with h5py.File(output[0], 'w') as f:
            f.create_dataset('states', data=states)
            f.attrs['mu_values'] = MU_VALUES
            f.attrs['C_values'] = C_VALUES
            f.attrs['n_orbits_per_mu_c'] = N_ORBITS_PER_MU_C
            f.attrs['seed'] = SEED
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
        from src.python.integrators.heyoka_taylor import HeyokaTaylorIntegrator
        from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

        # Parse orbit ID
        orbit_id = wildcards.orbit_id
        # Extract indices from orbit ID
        parts = orbit_id.split('_')
        mu_idx = int(parts[1].replace('mu', ''))
        C_idx = int(parts[2].replace('C', ''))
        orb_idx = int(parts[3])

        mu = MU_VALUES[mu_idx]
        C = C_VALUES[C_idx]

        # Load parameters
        with h5py.File(input[0], 'r') as f:
            sample_idx = mu_idx * len(C_VALUES) * N_ORBITS_PER_MU_C + C_idx * N_ORBITS_PER_MU_C + orb_idx
            initial_state = f['states'][sample_idx]

        # Select integrator
        if INTEGRATOR == "IAS15":
            integrator = IAS15Integrator(mu, tolerance=TARGET_ACCURACY)
        elif INTEGRATOR == "AdaptiveSymplectic":
            integrator = AdaptiveSymplecticIntegrator(
                mu,
                order=6,
                error_tolerance=TARGET_ACCURACY
            )
        elif INTEGRATOR == "HeyokaTaylor":
            integrator = HeyokaTaylorIntegrator(
                mu,
                tolerance=TARGET_ACCURACY,
                precision_bits=PRECISION_BITS,
                preserve_high_precision_states=True,
            )
        else:
            raise ValueError(f"Unknown integrator: {INTEGRATOR}")

        # Integrate
        result = integrator.integrate(
            initial_state, duration=DURATION, output_interval=OUTPUT_INTERVAL
        )
        if not result.success:
            raise RuntimeError(f"Integration failed for {orbit_id}: {result.message}")

        # Compute chaos indicators (may fail on close-encounter orbits)
        n_times = len(result.times)
        try:
            analyzer = create_cr3bp_chaos_analyzer(mu)
            chaos_result = analyzer.analyze(
                initial_state, t_final=DURATION, output_interval=OUTPUT_INTERVAL
            )
            megno_data = chaos_result.megno
            fli_data = chaos_result.fli
            chaos_class = chaos_result.classification
            mean_megno = chaos_result.mean_megno
            final_fli = chaos_result.final_fli
        except Exception as e:
            print(f"  Chaos analysis failed for {orbit_id}: {e}", flush=True)
            megno_data = np.full(n_times, np.nan)
            fli_data = np.full(n_times, np.nan)
            chaos_class = "failed"
            mean_megno = np.nan
            final_fli = np.nan

        # Save to HDF5
        with h5py.File(output[0], 'w') as f:
            f.create_dataset('times', data=result.times)
            f.create_dataset('states_corotating', data=result.states_corotating)
            f.create_dataset('states_inertial', data=result.states_inertial)
            f.create_dataset('MEGNO', data=megno_data)
            f.create_dataset('FLI', data=fli_data)

            f.attrs['mu'] = mu
            f.attrs['C'] = C
            f.attrs['orbit_id'] = orbit_id
            f.attrs['chaos_class'] = chaos_class
            f.attrs['mean_MEGNO'] = mean_megno
            f.attrs['final_FLI'] = final_fli
            f.attrs['integrator'] = INTEGRATOR
            f.attrs['precision'] = PRECISION
            for key, value in QUALIFICATION_METADATA.items():
                f.attrs[key] = value
            if 'jacobi_relative_drift' in result.stats:
                f.attrs['jacobi_relative_drift'] = result.stats[
                    'jacobi_relative_drift'
                ]
                f.attrs['jacobi_relative_drift_float'] = result.stats[
                    'jacobi_relative_drift_float'
                ]
                f.attrs['jacobi_initial_hp'] = result.stats['jacobi_initial']
                f.attrs['jacobi_final_hp'] = result.stats['jacobi_final']
                f.attrs['precision_backend'] = result.stats['precision_backend']
                f.attrs['precision_bits'] = result.stats['precision_bits']
            if 'states_corotating_high_precision' in result.stats:
                string_dtype = h5py.string_dtype(encoding='utf-8')
                f.create_dataset(
                    'states_corotating_high_precision',
                    data=np.asarray(
                        result.stats['states_corotating_high_precision'], dtype=object
                    ),
                    dtype=string_dtype,
                )
                f.create_dataset(
                    'times_high_precision',
                    data=np.asarray(result.stats['times_high_precision'], dtype=object),
                    dtype=string_dtype,
                )


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
        integrators = set()
        precisions = set()
        precision_backends = set()
        precision_bits = set()

        for orbit_file in orbit_files:
            with h5py.File(orbit_file, 'r') as f:
                mu = f.attrs['mu']
                states = f['states_corotating'][:]
                integrators.add(str(f.attrs.get('integrator', INTEGRATOR)))
                precisions.add(str(f.attrs.get('precision', PRECISION)))
                if 'precision_backend' in f.attrs:
                    precision_backends.add(str(f.attrs['precision_backend']))
                if 'precision_bits' in f.attrs:
                    precision_bits.add(str(f.attrs['precision_bits']))

                # Compute Jacobi constant drift
                if TIER == 2 and 'jacobi_relative_drift' in f.attrs:
                    drift = float(f.attrs['jacobi_relative_drift'])
                else:
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
            f.write(f"Target accuracy: {TARGET_ACCURACY:.0e}\n")
            f.write(f"Integrator(s): {', '.join(sorted(integrators))}\n")
            f.write(f"Precision: {', '.join(sorted(precisions))}\n")
            if precision_backends:
                f.write(
                    f"Precision backend(s): {', '.join(sorted(precision_backends))}\n"
                )
            if precision_bits:
                f.write(f"Precision bits: {', '.join(sorted(precision_bits))}\n")
            f.write("\n")

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
