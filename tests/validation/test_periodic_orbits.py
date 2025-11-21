"""
Tests for periodic orbit library (WP 4.2, Phase 1).
"""

import pytest
import numpy as np
from src.python.validation.periodic_orbits import (
    PeriodicOrbit,
    lagrange_l4_circular_restricted_3bp,
    lagrange_l4_equal_masses,
    euler_collinear_equal_masses,
    figure_8_choreography_approximate,
    get_orbit_catalog,
    list_available_orbits,
    integrate_orbit,
    validate_periodicity,
)


class TestPeriodicOrbitDataclass:
    """Test PeriodicOrbit dataclass."""

    def test_creation(self):
        """Test basic orbit creation."""
        orbit = PeriodicOrbit(
            name="test",
            initial_condition=np.array([1.0, 0.0, 0.0, 1.0]),
            period=2*np.pi,
            mass_ratios=(0.5, 0.5)
        )
        assert orbit.name == "test"
        assert orbit.period == 2*np.pi
        assert len(orbit.initial_condition) == 4

    def test_invalid_period(self):
        """Test that negative period raises error."""
        with pytest.raises(ValueError, match="Period must be positive"):
            PeriodicOrbit(
                name="bad",
                initial_condition=np.array([1, 0, 0, 1]),
                period=-1.0,
                mass_ratios=(0.5, 0.5)
            )

    def test_odd_dimension(self):
        """Test that odd-dimensional state raises error."""
        with pytest.raises(ValueError, match="even dimension"):
            PeriodicOrbit(
                name="bad",
                initial_condition=np.array([1, 0, 0]),  # 3D, odd
                period=1.0,
                mass_ratios=(0.5, 0.5)
            )


class TestLagrangeOrbits:
    """Test Lagrange equilibrium configurations."""

    def test_l4_cr3bp_earthmoon(self):
        """Test L4 point for Earth-Moon system."""
        orbit = lagrange_l4_circular_restricted_3bp(mu=0.012)

        assert orbit.name == "Lagrange_L4"
        assert orbit.period == pytest.approx(2*np.pi)
        assert orbit.stability_type == "stable"  # μ < 0.0385
        assert len(orbit.initial_condition) == 4

        # Check position is at equilateral point
        x, y, vx, vy = orbit.initial_condition
        assert x == pytest.approx(0.5 - 0.012)
        assert y == pytest.approx(np.sqrt(3)/2)
        assert vx == 0.0  # Equilibrium
        assert vy == 0.0

    def test_l4_unstable_regime(self):
        """Test L4 is unstable for large mass ratio."""
        orbit = lagrange_l4_circular_restricted_3bp(mu=0.1)
        assert orbit.stability_type == "unstable"  # μ > 0.0385

    def test_l4_equal_masses(self):
        """Test equilateral configuration for equal masses."""
        orbit = lagrange_l4_equal_masses()

        assert orbit.name == "Lagrange_Equilateral_EqualMass"
        assert orbit.mass_ratios == (1.0, 1.0, 1.0)
        assert len(orbit.initial_condition) == 12  # 3 bodies, planar: 6q + 6p

        # Check that initial configuration forms equilateral triangle
        q = orbit.initial_condition[:6]
        x1, y1, x2, y2, x3, y3 = q

        # Compute pairwise distances
        r12 = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        r23 = np.sqrt((x3 - x2)**2 + (y3 - y2)**2)
        r31 = np.sqrt((x1 - x3)**2 + (y1 - y3)**2)

        # All distances should be equal (equilateral)
        assert r12 == pytest.approx(r23, rel=1e-6)
        assert r23 == pytest.approx(r31, rel=1e-6)

        # Check center of mass at origin
        com_x = (x1 + x2 + x3) / 3
        com_y = (y1 + y2 + y3) / 3
        assert com_x == pytest.approx(0.0, abs=1e-10)
        assert com_y == pytest.approx(0.0, abs=1e-10)


class TestEulerOrbits:
    """Test Euler collinear configurations."""

    def test_collinear_equal_masses(self):
        """Test collinear configuration."""
        orbit = euler_collinear_equal_masses()

        assert orbit.name == "Euler_Collinear_EqualMass"
        assert orbit.angular_momentum == 0.0  # Zero L for collinear
        assert len(orbit.initial_condition) == 12

        # Check bodies are on x-axis (y=0)
        q = orbit.initial_condition[:6]
        x1, y1, x2, y2, x3, y3 = q
        assert y1 == pytest.approx(0.0)
        assert y2 == pytest.approx(0.0)
        assert y3 == pytest.approx(0.0)

        # Check symmetry (x1 = -x3 for equal masses)
        assert x1 == pytest.approx(-x3)
        assert x2 == pytest.approx(0.0)  # Central body at origin


class TestFigure8:
    """Test Figure-8 choreography."""

    def test_figure8_approximate(self):
        """Test approximate Figure-8 initial condition."""
        orbit = figure_8_choreography_approximate()

        assert orbit.name == "Figure8_Choreography"
        assert orbit.mass_ratios == (1.0, 1.0, 1.0)
        assert orbit.period == pytest.approx(6.32591398, rel=1e-6)
        assert len(orbit.initial_condition) == 12

        # Angular momentum should be approximately zero
        assert orbit.angular_momentum == pytest.approx(0.0, abs=1e-6)


class TestOrbitCatalog:
    """Test orbit catalog functions."""

    def test_list_available_orbits(self):
        """Test listing orbit names."""
        names = list_available_orbits()
        assert isinstance(names, list)
        assert len(names) > 0
        assert 'figure8' in names
        assert 'lagrange_equilateral_equal' in names

    def test_get_orbit_catalog(self):
        """Test getting full catalog."""
        catalog = get_orbit_catalog()
        assert isinstance(catalog, dict)
        assert len(catalog) > 0

        # Check all values are PeriodicOrbit
        for orbit in catalog.values():
            assert isinstance(orbit, PeriodicOrbit)

    def test_get_orbit_by_name(self):
        """Test retrieving orbit by name."""
        from src.python.validation.periodic_orbits import get_orbit_by_name

        orbit = get_orbit_by_name('figure8')
        assert orbit is not None
        assert orbit.name == "Figure8_Choreography"

        # Non-existent orbit should return None
        orbit = get_orbit_by_name('nonexistent')
        assert orbit is None


class TestOrbitIntegration:
    """Test orbit integration utilities."""

    def test_integrate_orbit_simple(self):
        """Test integration of simple circular orbit (2-body)."""
        # Simple 2-body Kepler orbit (circular)
        # Use reduced coordinates: one body, central force

        # Circular orbit: r=1, v=1 (for μ=1)
        ic = np.array([1.0, 0.0, 0.0, 1.0])  # x, y, vx, vy
        period = 2*np.pi

        orbit = PeriodicOrbit(
            name="test_circular",
            initial_condition=ic,
            period=period,
            mass_ratios=(1.0,)
        )

        # Simple Hamiltonian for circular orbit: H = v²/2 - 1/r
        def hamiltonian(y):
            x, y_coord = y[0], y[1]
            vx, vy = y[2], y[3]
            r = np.sqrt(x**2 + y_coord**2)
            T = 0.5 * (vx**2 + vy**2)
            V = -1.0 / r
            return T + V

        # Integrate for one period
        times, states = integrate_orbit(orbit, hamiltonian, n_periods=1.0, n_points=100)

        assert len(times) == 100
        assert states.shape == (100, 4)

        # Check closure (should return close to initial state)
        closure_error = np.linalg.norm(states[-1] - states[0])
        assert closure_error < 0.1  # Loose tolerance for approximate integration


@pytest.mark.slow
class TestOrbitValidation:
    """Test orbit validation utilities (slow tests)."""

    def test_validate_periodicity_circular(self):
        """Test periodicity validation for circular 2-body orbit."""
        # Simple circular orbit
        ic = np.array([1.0, 0.0, 0.0, 1.0])
        period = 2*np.pi

        orbit = PeriodicOrbit(
            name="test_circular",
            initial_condition=ic,
            period=period,
            mass_ratios=(1.0,)
        )

        def hamiltonian(y):
            x, y_coord, vx, vy = y
            r = np.sqrt(x**2 + y_coord**2)
            return 0.5 * (vx**2 + vy**2) - 1.0 / r

        # Validate
        result = validate_periodicity(orbit, hamiltonian, tolerance=0.1)

        assert 'is_periodic' in result
        assert 'energy_conserved' in result
        assert result['energy_conserved']  # Energy should be well conserved


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
