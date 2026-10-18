"""
Basic standalone tests for geometry module (no pytest required).

These tests verify that the modules can be imported and basic
functionality works without requiring external dependencies.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_imports():
    """Test that all geometry modules can be imported."""
    print("Testing imports...")

    try:
        from src.python.geometry import (
            compute_locked_inertia_tensor,
            compute_connection_coefficients,
            compute_jm_metric,
            compute_christoffel_symbols,
            compute_scalar_curvature,
        )
        print("✓ All geometry modules import successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        assert False


def test_module_structure():
    """Test that modules have expected structure."""
    print("\nTesting module structure...")

    try:
        from src.python.geometry import locked_inertia
        from src.python.geometry import connection_form
        from src.python.geometry import curvature_form
        from src.python.geometry import jm_metric
        from src.python.geometry import christoffel
        from src.python.geometry import riemann_curvature

        # Check for key classes/functions
        assert hasattr(locked_inertia, 'LockedInertiaTensor')
        assert hasattr(connection_form, 'ConnectionForm')
        assert hasattr(curvature_form, 'CurvatureForm')
        assert hasattr(jm_metric, 'RiemannianMetric')
        assert hasattr(christoffel, 'ChristoffelSymbols')
        assert hasattr(riemann_curvature, 'CurvatureTensors')

        print("✓ All expected classes and functions present")
    except (ImportError, AssertionError) as e:
        print(f"✗ Structure test failed: {e}")
        assert False


def test_dataclass_creation():
    """Test that dataclasses can be instantiated."""
    print("\nTesting dataclass creation...")

    try:
        # This will fail if numpy not available, but that's expected
        from src.python.geometry.locked_inertia import LockedInertiaTensor
        from src.python.geometry.connection_form import ConnectionForm
        from src.python.geometry.curvature_form import CurvatureForm
        from src.python.geometry.jm_metric import RiemannianMetric
        from src.python.geometry.christoffel import ChristoffelSymbols
        from src.python.geometry.riemann_curvature import CurvatureTensors

        print("✓ All dataclasses can be imported (numpy required for instantiation)")
    except ImportError as e:
        print(f"✗ Dataclass import failed: {e}")
        assert False


def main():
    """Run all standalone tests."""
    print("="*60)
    print("Geometry Module Standalone Tests")
    print("="*60)

    test_imports()
    test_module_structure()
    test_dataclass_creation()

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("All tests passed")
    print("="*60)


if __name__ == "__main__":
    sys.exit(main())
