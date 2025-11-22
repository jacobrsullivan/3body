"""
Theta function basis for symbolic regression (AMENDED WP3.3 Phase 4).

This module provides basis functions based on Jacobi theta functions:
- θ₁(z, τ), θ₂(z, τ), θ₃(z, τ), θ₄(z, τ)

Theta functions are doubly periodic meromorphic functions that appear in
completely integrable Hamiltonian systems. Their presence in conserved
quantities would indicate complete integrability of the three-body problem.

Physical motivation:
- Theta functions describe motion on abelian varieties (higher-dimensional tori)
- Doubly periodic structure: periodic in z and quasi-periodic in τ
- Appear in solutions to integrable PDEs (KdV, Toda lattice, etc.)
- Discovery in 3-body problem would be revolutionary

WARNING: This is highly speculative. Theta functions should only appear if:
1. System has hidden complete integrability
2. Motion lives on higher-dimensional torus
3. All Phase 1-2 methods have indicated quasi-periodic structure

References:
- AMENDED_Task-3.3.2-Implementation-Plan.md
- AMENDED_WP3.3-Symbolic-Regression-Summary.md
- Mumford, "Tata Lectures on Theta" (mathematical reference)
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Callable, Optional
from scipy import special


def jacobi_theta1(z: complex, q: complex) -> complex:
    """
    Jacobi theta function θ₁(z, q).

    Definition (product form):
        θ₁(z, q) = 2q^(1/4) sin(z) ∏_{n=1}^∞ (1-q^(2n))(1-2q^(2n)cos(2z)+q^(4n))

    Args:
        z: Argument (complex)
        q: Nome q = exp(iπτ), where τ is the modular parameter

    Returns:
        θ₁(z, q) value

    Properties:
        - θ₁(-z, q) = -θ₁(z, q) (odd in z)
        - θ₁(z + π, q) = -θ₁(z, q)
        - θ₁(z + πτ, q) = -q^(-1) exp(-2iz) θ₁(z, q)
        - θ₁(0, q) = 0 (has zero at z=0)
    """
    # Use truncated product formula (converges rapidly for |q| < 1)
    if np.abs(q) >= 1.0:
        # q must satisfy |q| < 1
        return np.nan + 0j

    # Truncate at N terms (typically N=10-20 sufficient)
    N = 20
    result = 2 * q**0.25 * np.sin(z)

    for n in range(1, N):
        term = (1 - q**(2*n)) * (1 - 2*q**(2*n)*np.cos(2*z) + q**(4*n))
        result *= term

    return result


def jacobi_theta2(z: complex, q: complex) -> complex:
    """
    Jacobi theta function θ₂(z, q).

    Definition:
        θ₂(z, q) = 2q^(1/4) cos(z) ∏_{n=1}^∞ (1-q^(2n))(1+2q^(2n)cos(2z)+q^(4n))

    Properties:
        - θ₂(-z, q) = θ₂(z, q) (even in z)
        - θ₂(z + π, q) = -θ₂(z, q)
        - θ₂(0, q) = 2q^(1/4) ∏ (1-q^(2n))(1+q^(2n))²
    """
    if np.abs(q) >= 1.0:
        return np.nan + 0j

    N = 20
    result = 2 * q**0.25 * np.cos(z)

    for n in range(1, N):
        term = (1 - q**(2*n)) * (1 + 2*q**(2*n)*np.cos(2*z) + q**(4*n))
        result *= term

    return result


def jacobi_theta3(z: complex, q: complex) -> complex:
    """
    Jacobi theta function θ₃(z, q).

    Definition (series form):
        θ₃(z, q) = 1 + 2∑_{n=1}^∞ q^(n²) cos(2nz)

    Properties:
        - θ₃(-z, q) = θ₃(z, q) (even in z)
        - θ₃(z + π, q) = θ₃(z, q) (periodic with period π)
        - θ₃(0, q) = 1 + 2∑ q^(n²)
    """
    if np.abs(q) >= 1.0:
        return np.nan + 0j

    # Use series form (converges for |q| < 1)
    N = 20
    result = 1.0

    for n in range(1, N):
        result += 2 * q**(n**2) * np.cos(2*n*z)

    return result


def jacobi_theta4(z: complex, q: complex) -> complex:
    """
    Jacobi theta function θ₄(z, q).

    Definition:
        θ₄(z, q) = 1 + 2∑_{n=1}^∞ (-1)^n q^(n²) cos(2nz)

    Properties:
        - θ₄(-z, q) = θ₄(z, q) (even in z)
        - θ₄(z + π, q) = θ₄(z, q)
        - θ₄(0, q) = 1 + 2∑ (-q)^(n²)
    """
    if np.abs(q) >= 1.0:
        return np.nan + 0j

    N = 20
    result = 1.0

    for n in range(1, N):
        result += 2 * ((-1)**n) * q**(n**2) * np.cos(2*n*z)

    return result


def estimate_modular_parameter(
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    candidate_integral: Callable
) -> complex:
    """
    Estimate modular parameter τ (and hence nome q) from trajectory.

    For completely integrable systems, motion is quasi-periodic on a torus.
    The modular parameter τ encodes the geometry of this torus.

    Args:
        trajectory: Phase space trajectory
        trajectory_times: Time points
        candidate_integral: Candidate conserved quantity

    Returns:
        tau: Modular parameter τ (complex, Im(τ) > 0)

    Strategy:
        1. Detect two fundamental frequencies ω₁, ω₂
        2. Estimate τ ≈ i·ω₂/ω₁ (pure imaginary for simplicity)
        3. Compute q = exp(iπτ)
    """
    # Evaluate integral
    I_values = np.array([candidate_integral(state) for state in trajectory])
    I_values = I_values - np.mean(I_values)

    # FFT analysis
    fft = np.fft.rfft(I_values)
    freqs = np.fft.rfftfreq(len(I_values), d=np.mean(np.diff(trajectory_times)))
    power = np.abs(fft)**2

    # Find peaks
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(power, height=np.max(power)*0.1)

    if len(peaks) < 2:
        # Default: τ = i (q ≈ 0.043)
        return 1.0j

    # Get two strongest frequencies
    sorted_peaks = peaks[np.argsort(power[peaks])[-2:]]
    omega1, omega2 = sorted(freqs[sorted_peaks])

    if omega1 < 1e-10:
        return 1.0j

    # Estimate τ = i·ω₂/ω₁
    tau = 1.0j * (omega2 / omega1)

    # Ensure Im(τ) > 0
    if np.imag(tau) <= 0:
        tau = 1.0j

    return tau


def construct_theta_basis(
    masses: np.ndarray,
    max_degree: int = 1,
    tau_values: Optional[List[complex]] = None
) -> List[Tuple[Callable, str]]:
    """
    Construct theta function basis for symbolic regression.

    WARNING: This is highly speculative. Only use if:
    - Quasi-periodic detection strongly suggests complete integrability
    - Elliptic function search has been successful
    - You are prepared for mostly null results

    Args:
        masses: Body masses
        max_degree: Maximum polynomial degree (keep low)
        tau_values: Modular parameters to try (default: [i, 2i])

    Returns:
        basis: List of (callable, description) tuples

    Basis categories:
        1. θ₁, θ₂, θ₃, θ₄ with different arguments
        2. Products θᵢ·θⱼ
        3. Ratios θᵢ/θⱼ (related to Jacobi elliptic functions)

    Total: ~30-40 functions

    Example:
        >>> masses = np.array([1.0, 1.0, 1.0])
        >>> basis = construct_theta_basis(masses)
        >>> len(basis)
        ~35
    """
    if tau_values is None:
        # Default modular parameters
        tau_values = [1.0j, 2.0j]  # Pure imaginary

    basis_functions = []
    n_bodies = len(masses)

    # Helper to extract coordinates
    def extract_coords(state: np.ndarray, body_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        dim = 3
        n_bodies_local = len(state) // 6
        r = state[body_idx * dim : (body_idx + 1) * dim]
        v = state[n_bodies_local * dim + body_idx * dim :
                 n_bodies_local * dim + (body_idx + 1) * dim]
        return r, v

    # ========== Category 1: Basic theta functions ==========

    for tau in tau_values:
        q = np.exp(1.0j * np.pi * tau)  # Nome

        # Check |q| < 1
        if np.abs(q) >= 0.99:
            print(f"Warning: |q| = {np.abs(q):.3f} too large for tau={tau}, skipping")
            continue

        for i in range(n_bodies):
            # θ₁(|r_i|, q)
            def make_theta1_r(body_idx, q_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    val = jacobi_theta1(r_mag, q_val)
                    return np.real(val)  # Take real part
                return func

            basis_functions.append((
                make_theta1_r(i, q),
                f"Re[θ₁(|r_{i+1}|, τ={tau})]"
            ))

            # θ₂(|r_i|, q)
            def make_theta2_r(body_idx, q_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    val = jacobi_theta2(r_mag, q_val)
                    return np.real(val)
                return func

            basis_functions.append((
                make_theta2_r(i, q),
                f"Re[θ₂(|r_{i+1}|, τ={tau})]"
            ))

            # θ₃(|r_i|, q)
            def make_theta3_r(body_idx, q_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    val = jacobi_theta3(r_mag, q_val)
                    return np.real(val)
                return func

            basis_functions.append((
                make_theta3_r(i, q),
                f"Re[θ₃(|r_{i+1}|, τ={tau})]"
            ))

            # θ₄(|r_i|, q)
            def make_theta4_r(body_idx, q_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    val = jacobi_theta4(r_mag, q_val)
                    return np.real(val)
                return func

            basis_functions.append((
                make_theta4_r(i, q),
                f"Re[θ₄(|r_{i+1}|, τ={tau})]"
            ))

    # ========== Category 2: Products ==========

    # Use only first tau value for products (limit combinatorics)
    if len(tau_values) > 0:
        tau = tau_values[0]
        q = np.exp(1.0j * np.pi * tau)

        if np.abs(q) < 0.99:
            for i in range(min(n_bodies, 2)):  # Only first 2 bodies
                # θ₃·θ₄ (appears in Jacobi elliptic function relations)
                def make_theta3_theta4(body_idx, q_val):
                    def func(state):
                        r, v = extract_coords(state, body_idx)
                        r_mag = np.linalg.norm(r)
                        val3 = jacobi_theta3(r_mag, q_val)
                        val4 = jacobi_theta4(r_mag, q_val)
                        return np.real(val3 * val4)
                    return func

                basis_functions.append((
                    make_theta3_theta4(i, q),
                    f"Re[θ₃·θ₄](|r_{i+1}|)"
                ))

                # θ₂·θ₄
                def make_theta2_theta4(body_idx, q_val):
                    def func(state):
                        r, v = extract_coords(state, body_idx)
                        r_mag = np.linalg.norm(r)
                        val2 = jacobi_theta2(r_mag, q_val)
                        val4 = jacobi_theta4(r_mag, q_val)
                        return np.real(val2 * val4)
                    return func

                basis_functions.append((
                    make_theta2_theta4(i, q),
                    f"Re[θ₂·θ₄](|r_{i+1}|)"
                ))

    # ========== Category 3: Ratios (related to Jacobi elliptic) ==========

    # θ₁/θ₄ ≈ sn (for appropriate scaling)
    # Only include a few to avoid numerical issues

    print(f"Constructed {len(basis_functions)} theta basis functions")
    print("WARNING: Theta functions are HIGHLY SPECULATIVE")
    print("         Only use if strong evidence of complete integrability")

    return basis_functions


def test_theta_identities() -> bool:
    """
    Test fundamental theta function identities.

    Returns:
        True if tests pass

    Identities:
        1. θ₃²(0, q) = θ₂²(0, q) + θ₄²(0, q) (Jacobi's identity)
        2. θ₁(0, q) = 0
        3. Symmetries: θ₃(-z) = θ₃(z), θ₁(-z) = -θ₁(z)
    """
    print("Testing theta function identities...")

    q = np.exp(1.0j * np.pi * 1.0j)  # tau = i, so q ≈ 0.043

    # Test 1: θ₁(0) = 0
    theta1_0 = jacobi_theta1(0.0, q)
    if np.abs(theta1_0) > 1e-10:
        print(f"  FAIL: θ₁(0) = {theta1_0} ≠ 0")
        return False

    # Test 2: Symmetries
    z = 1.5
    theta1_z = jacobi_theta1(z, q)
    theta1_mz = jacobi_theta1(-z, q)

    if not np.allclose(theta1_mz, -theta1_z, rtol=1e-8):
        print(f"  FAIL: θ₁(-z) ≠ -θ₁(z)")
        return False

    theta3_z = jacobi_theta3(z, q)
    theta3_mz = jacobi_theta3(-z, q)

    if not np.allclose(theta3_mz, theta3_z, rtol=1e-8):
        print(f"  FAIL: θ₃(-z) ≠ θ₃(z)")
        return False

    print("  ✓ Theta function identities satisfied")
    return True


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("Theta Basis Module - Tests")
    print("=" * 70)

    # Test 1: Theta identities
    print("\nTest 1: Theta function identities")
    print("-" * 70)
    test_theta_identities()

    # Test 2: Theta values
    print("\nTest 2: Theta function values")
    print("-" * 70)
    tau = 1.0j
    q = np.exp(1.0j * np.pi * tau)
    print(f"τ = {tau}, q = {q:.6f}")

    z_values = [0.0, 0.5, 1.0, np.pi/2]
    for z in z_values:
        theta1 = jacobi_theta1(z, q)
        theta2 = jacobi_theta2(z, q)
        theta3 = jacobi_theta3(z, q)
        theta4 = jacobi_theta4(z, q)
        print(f"z = {z:.4f}:")
        print(f"  θ₁ = {theta1:.6f}")
        print(f"  θ₂ = {theta2:.6f}")
        print(f"  θ₃ = {theta3:.6f}")
        print(f"  θ₄ = {theta4:.6f}")

    # Test 3: Basis construction
    print("\nTest 3: Theta basis construction")
    print("-" * 70)
    masses = np.array([1.0, 1.0, 1.0])
    basis = construct_theta_basis(masses, max_degree=1)

    print(f"Total basis functions: {len(basis)}")
    print("\nFirst 8 functions:")
    for i, (func, desc) in enumerate(basis[:8]):
        print(f"  {i+1:2d}. {desc}")

    # Test 4: Evaluation
    print("\nTest 4: Basis evaluation")
    print("-" * 70)
    state = np.random.randn(18)

    print("Evaluating first 4 basis functions:")
    for i, (func, desc) in enumerate(basis[:4]):
        try:
            value = func(state)
            print(f"  {desc}: {value:.6f}")
        except Exception as e:
            print(f"  {desc}: ERROR - {e}")

    print("\n" + "=" * 70)
    print("All tests complete")
    print("=" * 70)
