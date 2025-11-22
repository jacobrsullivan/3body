"""
Symbolic KS Hamiltonian example for WP2.

Demonstrates:
- Creating symbolic KS Hamiltonian
- Computing Hessian for Morales-Ramis analysis
- Verification of bilinear relation
- Constraint equations
"""

import sympy as sp
from src.python.symbolic_lifts import (
    create_ks_hamiltonian_kepler,
    create_ks_pairwise_3bp,
    verify_bilinear_relation_symbolic,
    prepare_ks_for_upstairs_mr_test
)


def example_ks_single_pair():
    """Symbolic KS for single two-body pair (Kepler problem)."""
    print("\n1. Symbolic KS for Kepler Problem")
    print("-" * 50)

    # Create KS Hamiltonian
    mu = sp.Symbol('mu', positive=True, real=True)
    ks_ham = create_ks_hamiltonian_kepler(mass_product=mu)

    # Get symbolic system
    system = ks_ham.get_symbolic_system()

    print(f"   Phase space dimension: {len(system.coordinates)}")
    print(f"   Configuration space dimension: {system.dimension}")

    # Display Hamiltonian (simplified)
    H = sp.simplify(system.H)
    print(f"\n   Regularized Hamiltonian K:")
    sp.pprint(H)

    # Compute gradient
    print(f"\n   Computing gradient...")
    grad = system.gradient()
    print(f"   Gradient shape: {grad.shape}")

    # Compute Hessian (for Morales-Ramis)
    print(f"\n   Computing Hessian (for Morales-Ramis analysis)...")
    hess = ks_ham.compute_hessian_ks()
    print(f"   Hessian shape: {hess.shape}")

    # Bilinear constraint
    constraint = ks_ham.bilinear_constraints()
    print(f"\n   Bilinear constraint: {constraint}")


def example_ks_pairwise_3bp():
    """Symbolic pairwise KS for three-body problem."""
    print("\n2. Pairwise KS for Three-Body Problem")
    print("-" * 50)

    # Create pairwise KS Hamiltonian
    m1, m2, m3 = sp.symbols('m_1 m_2 m_3', positive=True, real=True)
    ks_3bp = create_ks_pairwise_3bp(masses=(m1, m2, m3))

    # Get system
    system = ks_3bp.get_symbolic_system()

    print(f"   Phase space dimension: {len(system.coordinates)}")
    print(f"   Number of constraints: {len(system.constraints)}")

    # Display constraints
    print(f"\n   Constraints:")
    for i, c in enumerate(system.constraints[:3]):  # Show first 3
        print(f"   c{i+1}: {c}")

    # Compute Hessian
    print(f"\n   Computing 24×24 Hessian...")
    hess = ks_3bp.compute_hessian()
    print(f"   Hessian computed: {hess.shape}")

    # Constraint Jacobian
    jac = ks_3bp.constraint_jacobian()
    print(f"   Constraint Jacobian shape: {jac.shape}")


def example_verify_bilinear_relation():
    """Verify fundamental KS identity symbolically."""
    print("\n3. Verify Bilinear Relation |r|² = |u|⁴")
    print("-" * 50)

    result = verify_bilinear_relation_symbolic()

    if result:
        print("   ✓ Bilinear relation verified symbolically")
        print("   The fundamental KS identity holds exactly")
    else:
        print("   ✗ Verification failed")


def example_mr_preparation():
    """Prepare KS system for upstairs Morales-Ramis test."""
    print("\n4. Prepare for Upstairs Morales-Ramis Test")
    print("-" * 50)

    # Numerical masses for Figure-8 orbit
    masses = (1.0, 1.0, 1.0)

    print(f"   Masses: {masses}")
    print(f"   Orbit: Figure-8")

    # Prepare system
    data = prepare_ks_for_upstairs_mr_test(masses, orbit_name='figure8')

    print(f"\n   Hamiltonian (with numerical masses): ready")
    print(f"   Hessian shape: {data['hessian'].shape}")
    print(f"   Number of constraints: {len(data['constraints'])}")
    print(f"   Constraint Jacobian shape: {data['constraint_jacobian'].shape}")

    print(f"\n   → Ready for upstairs NVE computation (WP4.2)")


def main():
    """Run all symbolic KS examples."""
    print("="*60)
    print("Symbolic KS-Spinor Hamiltonian Examples")
    print("="*60)

    try:
        example_ks_single_pair()
        example_ks_pairwise_3bp()
        example_verify_bilinear_relation()
        example_mr_preparation()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
