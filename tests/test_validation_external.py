"""
Tests for the validation-external/wp1-validation pipeline.

Covers:
- Lyapunov and Halo generate_family()
- Halo orbit 3D properties
- normalize_jpl_orbits helpers (_load_table, _find_key)
- generate_report.py path handling (no hardcoded paths)
- compare_to_jpl.py helpers (match_candidate, stratified_sample)
- create_earth_moon_library()
- Parquet export (export_tier1_to_parquet)
"""

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Ensure repo root is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.python.orbits.periodic_families import (
    HaloOrbitGenerator,
    LyapunovOrbitGenerator,
    PeriodicOrbitLibrary,
    create_earth_moon_library,
)

# Import helpers from validation scripts
SCRIPTS_DIR = REPO_ROOT / "validation-external" / "wp1-validation" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Lyapunov generate_family
# ---------------------------------------------------------------------------
class TestLyapunovGenerateFamily:
    def setup_method(self):
        self.mu = 0.01215
        self.gen = LyapunovOrbitGenerator(self.mu, "L1")

    def test_count(self):
        family = self.gen.generate_family(n_orbits=7)
        assert len(family) == 7

    def test_fields(self):
        family = self.gen.generate_family(n_orbits=3)
        for orb in family:
            assert orb.family == "lyapunov"
            assert orb.L_point == "L1"
            assert orb.mu == self.mu
            assert orb.initial_state.shape == (6,)
            assert orb.period > 0
            assert np.isfinite(orb.jacobi_constant)

    def test_amplitude_range(self):
        family = self.gen.generate_family(n_orbits=5, amplitude_range=(0.02, 0.1))
        amps = [orb.amplitude for orb in family]
        assert pytest.approx(amps[0], abs=1e-10) == 0.02
        assert pytest.approx(amps[-1], abs=1e-10) == 0.1


# ---------------------------------------------------------------------------
# Halo generate_family (new method)
# ---------------------------------------------------------------------------
class TestHaloGenerateFamily:
    def setup_method(self):
        self.mu = 0.01215
        self.gen = HaloOrbitGenerator(self.mu, "L1")

    def test_count(self):
        family = self.gen.generate_family(n_orbits=8)
        assert len(family) == 8

    def test_family_field(self):
        family = self.gen.generate_family(n_orbits=3)
        for orb in family:
            assert orb.family == "halo"

    def test_amplitude_range(self):
        family = self.gen.generate_family(n_orbits=5, amplitude_range=(0.05, 0.25))
        amps = [orb.amplitude for orb in family]
        assert pytest.approx(amps[0], abs=1e-10) == 0.05
        assert pytest.approx(amps[-1], abs=1e-10) == 0.25

    def test_jacobi_consistency(self):
        """Each orbit's Jacobi constant should match recalculation."""
        from src.python.utils.dynamics import calculate_jacobi_constant

        family = self.gen.generate_family(n_orbits=4)
        for orb in family:
            C_recomputed = calculate_jacobi_constant(orb.initial_state, self.mu)
            assert pytest.approx(orb.jacobi_constant, rel=1e-12) == C_recomputed

    def test_default_params(self):
        """Default call should produce 10 orbits."""
        family = self.gen.generate_family()
        assert len(family) == 10


# ---------------------------------------------------------------------------
# Halo 3D orbit properties
# ---------------------------------------------------------------------------
class TestHaloOrbitSpec:
    def setup_method(self):
        self.mu = 0.01215
        self.gen = HaloOrbitGenerator(self.mu, "L1")

    def test_nonzero_vz(self):
        """Halo orbits should have nonzero vz."""
        orbit = self.gen.generate_richardson_halo(0.1, branch="northern")
        assert orbit.initial_state[5] != 0.0  # vz

    def test_northern_southern_differ(self):
        """Northern and southern branches should differ."""
        north = self.gen.generate_richardson_halo(0.1, branch="northern")
        south = self.gen.generate_richardson_halo(0.1, branch="southern")
        assert not np.allclose(north.initial_state, south.initial_state)
        # vz should have opposite signs
        assert north.initial_state[5] * south.initial_state[5] < 0


# ---------------------------------------------------------------------------
# Normalization helpers (_load_table, _find_key)
# ---------------------------------------------------------------------------
class TestNormalizationHelpers:
    def test_load_table_fields_data_format(self):
        from normalize_jpl_orbits import _load_table

        data = {
            "fields": ["x", "y", "vx", "vy"],
            "data": [
                [1.0, 2.0, 0.1, 0.2],
                [3.0, 4.0, 0.3, 0.4],
            ],
        }
        table = _load_table(data)
        assert len(table) == 2
        assert table[0]["x"] == 1.0
        assert table[1]["vy"] == 0.4

    def test_load_table_orbits_format(self):
        from normalize_jpl_orbits import _load_table

        data = {
            "orbits": [
                {"x": 1.0, "y": 2.0},
                {"x": 3.0, "y": 4.0},
            ]
        }
        table = _load_table(data)
        assert len(table) == 2

    def test_load_table_unknown_raises(self):
        from normalize_jpl_orbits import _load_table

        with pytest.raises(ValueError):
            _load_table({"foo": "bar"})

    def test_find_key_case_insensitive(self):
        from normalize_jpl_orbits import _find_key

        keys = ["X", "Y", "VX", "VY"]
        assert _find_key(keys, ["x"]) == "X"
        assert _find_key(keys, ["vx"]) == "VX"

    def test_find_key_returns_none(self):
        from normalize_jpl_orbits import _find_key

        assert _find_key(["a", "b"], ["z"]) is None


# ---------------------------------------------------------------------------
# Report path handling regression
# ---------------------------------------------------------------------------
class TestReportPathHandling:
    def test_no_hardcoded_user_path(self):
        """generate_report.py should not contain hardcoded /Users/ paths."""
        report_src = (
            REPO_ROOT
            / "validation-external"
            / "wp1-validation"
            / "scripts"
            / "generate_report.py"
        )
        content = report_src.read_text()
        assert (
            "/Users/" not in content
        ), "Hardcoded /Users/ path found in generate_report.py"

    def test_read_text_missing(self):
        """read_text should return '(missing)' for nonexistent files."""
        from generate_report import read_text

        result = read_text("/nonexistent/file.txt")
        assert result == "(missing)"


# ---------------------------------------------------------------------------
# JPL comparison helpers
# ---------------------------------------------------------------------------
class TestJPLComparisonHelpers:
    def test_match_candidate_by_jacobi(self):
        from compare_to_jpl import match_candidate

        candidates = [
            {"family": "lyapunov", "lpoint": "L1", "jacobi": 3.0},
            {"family": "lyapunov", "lpoint": "L1", "jacobi": 3.2},
            {"family": "halo", "lpoint": "L2", "jacobi": 2.8},
        ]
        jpl_row = {"family": "lyapunov", "lpoint": "L1", "jacobi": 3.15}
        match = match_candidate(jpl_row, candidates)
        # Should pick the one closest in Jacobi (3.2)
        assert match["jacobi"] == 3.2

    def test_match_candidate_family_filter(self):
        from compare_to_jpl import match_candidate

        candidates = [
            {"family": "lyapunov", "lpoint": "L1", "jacobi": 3.0},
            {"family": "halo", "lpoint": "L1", "jacobi": 3.0},
        ]
        jpl_row = {"family": "halo", "lpoint": "L1", "jacobi": 3.0}
        match = match_candidate(jpl_row, candidates)
        assert match["family"] == "halo"

    def test_match_candidate_empty(self):
        from compare_to_jpl import match_candidate

        assert match_candidate({"jacobi": 3.0}, []) is None


# ---------------------------------------------------------------------------
# Earth-Moon library
# ---------------------------------------------------------------------------
class TestEarthMoonLibrary:
    def test_orbit_count(self):
        lib = create_earth_moon_library()
        assert len(lib.orbits) == 16  # 5 L1 lyap + 5 L2 lyap + 3*2 halo

    def test_both_families_present(self):
        lib = create_earth_moon_library()
        families = {orb.family for orb in lib.orbits}
        assert "lyapunov" in families
        assert "halo" in families

    def test_library_type(self):
        lib = create_earth_moon_library()
        assert isinstance(lib, PeriodicOrbitLibrary)


# ---------------------------------------------------------------------------
# Stratified sampling
# ---------------------------------------------------------------------------
class TestStratifiedSampling:
    def test_returns_all_when_under_limit(self):
        from compare_to_jpl import stratified_sample

        rows = [
            {"family": "lyapunov", "lpoint": "L1", "branch": "", "jacobi": i}
            for i in range(10)
        ]
        result = stratified_sample(rows, max_total=50)
        assert len(result) == 10

    def test_respects_max_total(self):
        from compare_to_jpl import stratified_sample

        rows = [
            {"family": "lyapunov", "lpoint": "L1", "branch": "", "jacobi": float(i)}
            for i in range(100)
        ]
        result = stratified_sample(rows, max_total=20)
        assert len(result) <= 20

    def test_all_groups_present(self):
        from compare_to_jpl import stratified_sample

        rows = []
        for fam in ["lyapunov", "halo"]:
            for lp in ["L1", "L2"]:
                for br in ["northern", "southern"]:
                    for i in range(50):
                        rows.append(
                            {
                                "family": fam,
                                "lpoint": lp,
                                "branch": br,
                                "jacobi": 2.5 + i * 0.02,
                            }
                        )
        # 8 groups x 50 = 400 total, sample 40
        result = stratified_sample(rows, max_total=40)

        groups_present = set()
        for r in result:
            groups_present.add(
                (r["family"].lower(), r["lpoint"].upper(), r["branch"].lower())
            )
        # All 8 groups should have at least 1 representative
        assert len(groups_present) == 8

    def test_proportional_representation(self):
        from compare_to_jpl import stratified_sample

        # One large group, one small group
        rows = []
        for i in range(900):
            rows.append(
                {"family": "lyapunov", "lpoint": "L1", "branch": "", "jacobi": float(i)}
            )
        for i in range(100):
            rows.append(
                {"family": "halo", "lpoint": "L2", "branch": "", "jacobi": float(i)}
            )

        result = stratified_sample(rows, max_total=100)
        n_lyap = sum(1 for r in result if r["family"] == "lyapunov")
        n_halo = sum(1 for r in result if r["family"] == "halo")

        # Lyapunov should get roughly 90%, halo ~10% (within tolerance)
        assert n_lyap > n_halo
        assert n_halo >= 1  # minimum 1


# ---------------------------------------------------------------------------
# Split metrics structure
# ---------------------------------------------------------------------------
class TestSplitMetrics:
    def test_integrator_accuracy_uses_jpl_ics(self):
        """Verify the comparison script integrates JPL ICs, not Richardson ICs."""
        compare_src = (
            REPO_ROOT
            / "validation-external"
            / "wp1-validation"
            / "scripts"
            / "compare_to_jpl.py"
        )
        content = compare_src.read_text()
        # Test 1 block should integrate state_jpl
        assert (
            "integrator.integrate(\n                state_jpl" in content
            or "integrator.integrate(state_jpl" in content
        )

    def test_richardson_quality_no_integration(self):
        """Richardson quality section should not call integrator.integrate."""
        compare_src = (
            REPO_ROOT
            / "validation-external"
            / "wp1-validation"
            / "scripts"
            / "compare_to_jpl.py"
        )
        content = compare_src.read_text()
        # After "Test 2: Richardson quality", there should be no integrate call
        test2_marker = "Test 2: Richardson quality"
        idx = content.find(test2_marker)
        assert idx > 0
        rest = content[idx : idx + 500]
        assert "integrator.integrate" not in rest

    def test_summary_json_structure(self):
        """Summary JSON should have integrator_accuracy, richardson_quality, meta."""
        compare_src = (
            REPO_ROOT
            / "validation-external"
            / "wp1-validation"
            / "scripts"
            / "compare_to_jpl.py"
        )
        content = compare_src.read_text()
        assert '"integrator_accuracy"' in content
        assert '"richardson_quality"' in content
        assert '"meta"' in content


# ---------------------------------------------------------------------------
# Parquet export
# ---------------------------------------------------------------------------
class TestParquetExport:
    def test_export_tier1_produces_valid_parquet(self, tmp_path):
        """export_tier1_to_parquet should produce valid Parquet from HDF5."""
        import h5py
        import pyarrow.parquet as pq

        # Create sample HDF5 files
        hdf5_dir = tmp_path / "hdf5"
        hdf5_dir.mkdir()

        n_points = 10
        for i in range(3):
            fp = hdf5_dir / f"orbit_{i}.h5"
            with h5py.File(str(fp), "w") as f:
                f.attrs["mu"] = 0.012
                f.attrs["C"] = 3.0 + i * 0.1
                f.attrs["orbit_id"] = f"orbit_{i}"
                f.attrs["chaos_class"] = "regular" if i % 2 == 0 else "chaotic"
                f.create_dataset("times", data=np.linspace(0, 10, n_points))
                f.create_dataset("states_corotating", data=np.random.randn(n_points, 6))
                f.create_dataset("states_inertial", data=np.random.randn(n_points, 6))
                f.create_dataset("MEGNO", data=np.random.rand(n_points))
                f.create_dataset("FLI", data=np.random.rand(n_points))

        output_path = str(tmp_path / "output.parquet")

        from src.python.ml.parquet_export import export_tier1_to_parquet

        export_tier1_to_parquet(str(hdf5_dir), output_path)

        # Verify output
        assert os.path.exists(output_path)
        table = pq.read_table(output_path)
        assert table.num_rows == 3 * n_points
        expected_cols = {
            "orbit_id",
            "mu",
            "C",
            "t",
            "x",
            "y",
            "z",
            "vx",
            "vy",
            "vz",
            "x_inertial",
            "y_inertial",
            "z_inertial",
            "vx_inertial",
            "vy_inertial",
            "vz_inertial",
            "MEGNO",
            "FLI",
            "chaos_class",
        }
        assert expected_cols == set(table.column_names)

    def test_export_empty_dir(self, tmp_path):
        """export_tier1_to_parquet should handle empty directories gracefully."""
        hdf5_dir = tmp_path / "empty"
        hdf5_dir.mkdir()
        output_path = str(tmp_path / "output.parquet")

        from src.python.ml.parquet_export import export_tier1_to_parquet

        export_tier1_to_parquet(str(hdf5_dir), output_path)

        # No output file should be created
        assert not os.path.exists(output_path)


# ---------------------------------------------------------------------------
# Reversibility check script inspection
# ---------------------------------------------------------------------------
class TestReversibilityCheck:
    """Source-level tests for run_reversibility_check.py."""

    def setup_method(self):
        self.script = (
            REPO_ROOT
            / "validation-external"
            / "wp1-validation"
            / "scripts"
            / "run_reversibility_check.py"
        )
        self.content = self.script.read_text()

    def test_script_uses_existing_tester(self):
        """Script should import from src.python.validation.time_reversibility."""
        assert "from src.python.validation.time_reversibility" in self.content

    def test_output_csv_columns(self):
        """CSV fieldnames should match expected schema."""
        for col in [
            "orbit_idx",
            "family",
            "lpoint",
            "forward_time",
            "position_rms_error",
            "velocity_rms_error",
            "max_position_error",
            "energy_error",
            "passes_tier1",
        ]:
            assert col in self.content, f"Missing CSV column: {col}"

    def test_multiple_forward_times(self):
        """Script should test at multiple forward times (not just one)."""
        # The script defines FORWARD_TIMES with at least 3 entries
        assert "FORWARD_TIMES" in self.content
        # Check for at least two distinct T values
        for t in ["1.0", "10.0", "50.0"]:
            assert t in self.content, f"Missing forward time T={t}"


# ---------------------------------------------------------------------------
# Convergence check script inspection
# ---------------------------------------------------------------------------
class TestConvergenceCheck:
    """Source-level tests for run_convergence_check.py."""

    def setup_method(self):
        self.script = (
            REPO_ROOT
            / "validation-external"
            / "wp1-validation"
            / "scripts"
            / "run_convergence_check.py"
        )
        self.content = self.script.read_text()

    def test_tolerance_sweep_range(self):
        """Tolerances should span from ~1e-8 to ~1e-14."""
        assert "1e-8" in self.content
        assert "1e-14" in self.content

    def test_convergence_order_computed(self):
        """Summary should include a convergence order calculation."""
        assert "convergence_order" in self.content

    def test_output_csv_columns(self):
        """CSV fieldnames should match expected schema."""
        for col in [
            "orbit_idx",
            "family",
            "lpoint",
            "tolerance",
            "closure_error",
            "jacobi_drift",
        ]:
            assert col in self.content, f"Missing CSV column: {col}"
