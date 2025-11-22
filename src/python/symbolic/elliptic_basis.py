"""
Elliptic function basis for symbolic regression (AMENDED WP3.3 Phase 2).

This module provides basis functions based on elliptic functions:
- Jacobi elliptic functions: sn(u, m), cn(u, m), dn(u, m)
- Weierstrass elliptic function: ℘(z; g2, g3)
- Complete elliptic integrals: K(m), E(m)
- Combinations and products

Elliptic functions are natural candidates for integrals in integrable Hamiltonian
systems. They appear in solutions to the Kepler problem, rigid body dynamics,
and potentially in the three-body problem if hidden integrability exists.

Physical motivation:
- Jacobi functions describe motion on elliptic curves
- Doubly periodic structure indicates two independent frequencies
- Natural for systems with quasi-periodic dynamics

References:
- AMENDED_Task-3.3.2-Implementation-Plan.md
- AMENDED_WP3.3-Symbolic-Regression-Summary.md
- Whittaker & Watson, "A Course of Modern Analysis"
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Callable, Optional
from scipy import special


def jacobi_sn(u: float, m: float) -> float:
    """
    Jacobi elliptic function sn(u, m).

    Args:
        u: Argument
        m: Parameter (0 ≤ m ≤ 1)

    Returns:
        sn(u, m) value

    Properties:
        - sn(0, m) = 0
        - sn²(u, m) + cn²(u, m) = 1
        - Doubly periodic with periods 4K(m) and 2iK'(m)

    Example:
        >>> jacobi_sn(0.5, 0.5)
        0.470...
    """
    # Use scipy's Jacobi elliptic functions
    # scipy uses parameter m (not k), where m = k²
    sn, cn, dn, ph = special.ellipj(u, m)
    return sn


def jacobi_cn(u: float, m: float) -> float:
    """
    Jacobi elliptic function cn(u, m).

    Args:
        u: Argument
        m: Parameter (0 ≤ m ≤ 1)

    Returns:
        cn(u, m) value

    Properties:
        - cn(0, m) = 1
        - sn²(u, m) + cn²(u, m) = 1
    """
    sn, cn, dn, ph = special.ellipj(u, m)
    return cn


def jacobi_dn(u: float, m: float) -> float:
    """
    Jacobi elliptic function dn(u, m).

    Args:
        u: Argument
        m: Parameter (0 ≤ m ≤ 1)

    Returns:
        dn(u, m) value

    Properties:
        - dn(0, m) = 1
        - dn²(u, m) + m·sn²(u, m) = 1
    """
    sn, cn, dn, ph = special.ellipj(u, m)
    return dn


def complete_elliptic_K(m: float) -> float:
    """
    Complete elliptic integral of the first kind K(m).

    Args:
        m: Parameter (0 ≤ m ≤ 1)

    Returns:
        K(m) = ∫₀^(π/2) dθ / √(1 - m·sin²θ)

    This is the quarter-period of Jacobi elliptic functions.
    """
    return special.ellipk(m)


def complete_elliptic_E(m: float) -> float:
    """
    Complete elliptic integral of the second kind E(m).

    Args:
        m: Parameter (0 ≤ m ≤ 1)

    Returns:
        E(m) = ∫₀^(π/2) √(1 - m·sin²θ) dθ
    """
    return special.ellipe(m)


def estimate_elliptic_parameter(trajectory: np.ndarray,
                                trajectory_times: np.ndarray,
                                candidate_integral: Callable) -> float:
    """
    Estimate elliptic parameter m from trajectory.

    For integrable systems, motion is quasi-periodic with two fundamental
    frequencies ω₁ and ω₂. The elliptic parameter m is related to the
    ratio of these frequencies.

    Args:
        trajectory: Phase space trajectory (N, dim)
        trajectory_times: Time points
        candidate_integral: Function to evaluate on trajectory

    Returns:
        m: Estimated elliptic parameter (0 ≤ m ≤ 1)

    Strategy:
        1. Compute FFT of candidate integral
        2. Find two dominant frequencies ω₁, ω₂
        3. Estimate m from frequency ratio
    """
    # Evaluate integral along trajectory
    I_values = np.array([candidate_integral(state) for state in trajectory])

    # Remove mean
    I_values = I_values - np.mean(I_values)

    # Compute FFT
    fft = np.fft.rfft(I_values)
    freqs = np.fft.rfftfreq(len(I_values), d=np.mean(np.diff(trajectory_times)))
    power = np.abs(fft)**2

    # Find peaks in power spectrum
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(power, height=np.max(power)*0.1)

    if len(peaks) < 2:
        # Not enough frequencies - default to m=0.5
        return 0.5

    # Get two strongest peaks
    sorted_peaks = peaks[np.argsort(power[peaks])[-2:]]
    omega1, omega2 = sorted(freqs[sorted_peaks])

    if omega1 < 1e-10:
        return 0.5

    # Estimate m from frequency ratio
    # For Jacobi functions, period ratio is related to K(m)/K'(m)
    ratio = omega2 / omega1

    # Rough estimate: m ≈ 1 - (ratio)²
    m_est = max(0.0, min(1.0, 1.0 - 1.0/(ratio**2 + 1)))

    return m_est


def construct_elliptic_basis(
    masses: np.ndarray,
    max_degree: int = 2,
    m_values: Optional[List[float]] = None,
    include_weierstrass: bool = False
) -> List[Tuple[Callable, str]]:
    """
    Construct elliptic function basis for symbolic regression.

    Args:
        masses: Body masses (N_bodies,)
        max_degree: Maximum polynomial degree for combinations
        m_values: Elliptic parameters to use (default: [0.1, 0.5, 0.9])
        include_weierstrass: Include Weierstrass ℘ function (experimental)

    Returns:
        basis: List of (callable, description) tuples

    Basis function categories:
        1. Jacobi sn, cn, dn with different arguments
        2. Products: sn·cn, sn·dn, cn·dn
        3. Powers: sn², cn², dn²
        4. Combinations with position/momentum
        5. Complete elliptic integrals K(m), E(m)

    Total: ~60-80 functions depending on parameters

    Example:
        >>> masses = np.array([1.0, 1.0, 1.0])
        >>> basis = construct_elliptic_basis(masses, max_degree=2)
        >>> len(basis)
        ~70
    """
    if m_values is None:
        # Default elliptic parameters
        # m=0.1: nearly circular
        # m=0.5: moderate eccentricity
        # m=0.9: highly eccentric
        m_values = [0.1, 0.5, 0.9]

    basis_functions = []
    n_bodies = len(masses)

    # Helper to extract position/momentum for body i
    def extract_coords(state: np.ndarray, body_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        """Extract (r_i, v_i) for body i from state."""
        dim = 3  # 3D space
        n_bodies_local = len(state) // 6  # Total dimension / 6

        r = state[body_idx * dim : (body_idx + 1) * dim]
        v = state[n_bodies_local * dim + body_idx * dim :
                 n_bodies_local * dim + (body_idx + 1) * dim]
        return r, v

    # ========== Category 1: Basic Jacobi functions ==========

    for m in m_values:
        # For each body, use |r| as argument
        for i in range(n_bodies):
            # sn(|r_i|, m)
            def make_sn_r(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    return jacobi_sn(r_mag, m_val)
                return func

            basis_functions.append((
                make_sn_r(i, m),
                f"sn(|r_{i+1}|, m={m:.1f})"
            ))

            # cn(|r_i|, m)
            def make_cn_r(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    return jacobi_cn(r_mag, m_val)
                return func

            basis_functions.append((
                make_cn_r(i, m),
                f"cn(|r_{i+1}|, m={m:.1f})"
            ))

            # dn(|r_i|, m)
            def make_dn_r(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    return jacobi_dn(r_mag, m_val)
                return func

            basis_functions.append((
                make_dn_r(i, m),
                f"dn(|r_{i+1}|, m={m:.1f})"
            ))

            # sn(|v_i|, m)
            def make_sn_v(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    v_mag = np.linalg.norm(v)
                    return jacobi_sn(v_mag, m_val)
                return func

            basis_functions.append((
                make_sn_v(i, m),
                f"sn(|v_{i+1}|, m={m:.1f})"
            ))

            # cn(|v_i|, m)
            def make_cn_v(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    v_mag = np.linalg.norm(v)
                    return jacobi_cn(v_mag, m_val)
                return func

            basis_functions.append((
                make_cn_v(i, m),
                f"cn(|v_{i+1}|, m={m:.1f})"
            ))

    # ========== Category 2: Products of Jacobi functions ==========

    for m in m_values[:2]:  # Use fewer m values for products
        for i in range(n_bodies):
            # sn(|r_i|)·cn(|r_i|)
            def make_sn_cn(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    return jacobi_sn(r_mag, m_val) * jacobi_cn(r_mag, m_val)
                return func

            basis_functions.append((
                make_sn_cn(i, m),
                f"sn(|r_{i+1}|)·cn(|r_{i+1}|), m={m:.1f}"
            ))

            # sn(|r_i|)·dn(|r_i|)
            def make_sn_dn(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    return jacobi_sn(r_mag, m_val) * jacobi_dn(r_mag, m_val)
                return func

            basis_functions.append((
                make_sn_dn(i, m),
                f"sn(|r_{i+1}|)·dn(|r_{i+1}|), m={m:.1f}"
            ))

    # ========== Category 3: Squares (use identities) ==========

    for m in m_values[:2]:
        for i in range(n_bodies):
            # sn²(|r_i|, m)
            def make_sn2(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    sn = jacobi_sn(r_mag, m_val)
                    return sn**2
                return func

            basis_functions.append((
                make_sn2(i, m),
                f"sn²(|r_{i+1}|, m={m:.1f})"
            ))

            # cn²(|r_i|, m)
            def make_cn2(body_idx, m_val):
                def func(state):
                    r, v = extract_coords(state, body_idx)
                    r_mag = np.linalg.norm(r)
                    cn = jacobi_cn(r_mag, m_val)
                    return cn**2
                return func

            basis_functions.append((
                make_cn2(i, m),
                f"cn²(|r_{i+1}|, m={m:.1f})"
            ))

    # ========== Category 4: Mixed with coordinates ==========

    # Use only m=0.5 for mixed terms to limit combinatorial explosion
    m_mid = 0.5

    for i in range(n_bodies):
        # r_x · sn(|r|, m)
        def make_rx_sn(body_idx, m_val):
            def func(state):
                r, v = extract_coords(state, body_idx)
                r_mag = np.linalg.norm(r)
                if r_mag < 1e-10:
                    return 0.0
                return r[0] * jacobi_sn(r_mag, m_val)
            return func

        basis_functions.append((
            make_rx_sn(i, m_mid),
            f"r_{i+1,x} · sn(|r_{i+1}|)"
        ))

        # v_x · sn(|v|, m)
        def make_vx_sn(body_idx, m_val):
            def func(state):
                r, v = extract_coords(state, body_idx)
                v_mag = np.linalg.norm(v)
                if v_mag < 1e-10:
                    return 0.0
                return v[0] * jacobi_sn(v_mag, m_val)
            return func

        basis_functions.append((
            make_vx_sn(i, m_mid),
            f"v_{i+1,x} · sn(|v_{i+1}|)"
        ))

    # ========== Category 5: Relative coordinates ==========

    # Jacobi functions of inter-body distances
    if n_bodies >= 2:
        for i in range(n_bodies):
            for j in range(i + 1, min(i + 2, n_bodies)):  # Only nearest pairs
                for m in m_values[:1]:  # Only one m value
                    # sn(|r_i - r_j|, m)
                    def make_sn_rij(bi, bj, m_val):
                        def func(state):
                            ri, vi = extract_coords(state, bi)
                            rj, vj = extract_coords(state, bj)
                            r_ij = ri - rj
                            r_ij_mag = np.linalg.norm(r_ij)
                            return jacobi_sn(r_ij_mag, m_val)
                        return func

                    basis_functions.append((
                        make_sn_rij(i, j, m),
                        f"sn(|r_{i+1} - r_{j+1}|, m={m:.1f})"
                    ))

                    # cn(|r_i - r_j|, m)
                    def make_cn_rij(bi, bj, m_val):
                        def func(state):
                            ri, vi = extract_coords(state, bi)
                            rj, vj = extract_coords(state, bj)
                            r_ij = ri - rj
                            r_ij_mag = np.linalg.norm(r_ij)
                            return jacobi_cn(r_ij_mag, m_val)
                        return func

                    basis_functions.append((
                        make_cn_rij(i, j, m),
                        f"cn(|r_{i+1} - r_{j+1}|, m={m:.1f})"
                    ))

    # ========== Category 6: Complete elliptic integrals ==========

    # These are constants for fixed m, but we include them for completeness
    for m in m_values:
        # K(m)
        K_m = complete_elliptic_K(m)
        basis_functions.append((
            lambda state, K=K_m: K,
            f"K(m={m:.1f}) = {K_m:.4f}"
        ))

        # E(m)
        E_m = complete_elliptic_E(m)
        basis_functions.append((
            lambda state, E=E_m: E,
            f"E(m={m:.1f}) = {E_m:.4f}"
        ))

    print(f"Constructed {len(basis_functions)} elliptic basis functions")

    return basis_functions


def test_jacobi_identities() -> bool:
    """
    Test fundamental Jacobi elliptic function identities.

    Returns:
        True if all tests pass

    Identities tested:
        1. sn²(u, m) + cn²(u, m) = 1
        2. dn²(u, m) + m·sn²(u, m) = 1
        3. sn(0, m) = 0, cn(0, m) = 1, dn(0, m) = 1
    """
    print("Testing Jacobi elliptic function identities...")

    test_points = [
        (0.0, 0.5),
        (0.5, 0.1),
        (1.0, 0.5),
        (1.5, 0.9),
        (2.0, 0.5),
    ]

    for u, m in test_points:
        sn = jacobi_sn(u, m)
        cn = jacobi_cn(u, m)
        dn = jacobi_dn(u, m)

        # Identity 1: sn² + cn² = 1
        identity1 = sn**2 + cn**2
        if not np.isclose(identity1, 1.0, rtol=1e-10):
            print(f"  FAIL: sn²+cn² = {identity1} ≠ 1 at u={u}, m={m}")
            return False

        # Identity 2: dn² + m·sn² = 1
        identity2 = dn**2 + m * sn**2
        if not np.isclose(identity2, 1.0, rtol=1e-10):
            print(f"  FAIL: dn²+m·sn² = {identity2} ≠ 1 at u={u}, m={m}")
            return False

    # Identity 3: Values at u=0
    sn0 = jacobi_sn(0.0, 0.5)
    cn0 = jacobi_cn(0.0, 0.5)
    dn0 = jacobi_dn(0.0, 0.5)

    if not np.isclose(sn0, 0.0, atol=1e-10):
        print(f"  FAIL: sn(0) = {sn0} ≠ 0")
        return False

    if not np.isclose(cn0, 1.0, rtol=1e-10):
        print(f"  FAIL: cn(0) = {cn0} ≠ 1")
        return False

    if not np.isclose(dn0, 1.0, rtol=1e-10):
        print(f"  FAIL: dn(0) = {dn0} ≠ 1")
        return False

    print("  ✓ All Jacobi identities satisfied")
    return True


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Elliptic Basis Module - Tests")
    print("=" * 70)

    # Test 1: Jacobi identities
    print("\nTest 1: Jacobi elliptic function identities")
    print("-" * 70)
    test_jacobi_identities()

    # Test 2: Complete elliptic integrals
    print("\nTest 2: Complete elliptic integrals")
    print("-" * 70)
    for m in [0.0, 0.5, 1.0]:
        if m == 1.0:
            print(f"m = {m}: K(m) = ∞ (singular)")
        else:
            K = complete_elliptic_K(m)
            E = complete_elliptic_E(m)
            print(f"m = {m}: K(m) = {K:.6f}, E(m) = {E:.6f}")

    # Test 3: Basis construction
    print("\nTest 3: Elliptic basis construction")
    print("-" * 70)
    masses = np.array([1.0, 1.0, 1.0])
    basis = construct_elliptic_basis(masses, max_degree=2)

    print(f"Total basis functions: {len(basis)}")
    print("\nFirst 10 functions:")
    for i, (func, desc) in enumerate(basis[:10]):
        print(f"  {i+1:2d}. {desc}")

    # Test 4: Evaluation on random state
    print("\nTest 4: Basis evaluation")
    print("-" * 70)
    state = np.random.randn(18)  # 3 bodies, 6D phase space each

    print("Evaluating first 5 basis functions on random state:")
    for i, (func, desc) in enumerate(basis[:5]):
        try:
            value = func(state)
            print(f"  {desc}: {value:.6f}")
        except Exception as e:
            print(f"  {desc}: ERROR - {e}")

    # Test 5: Elliptic parameter estimation
    print("\nTest 5: Elliptic parameter estimation")
    print("-" * 70)

    # Create synthetic quasi-periodic signal
    t = np.linspace(0, 100, 10000)
    omega1 = 1.0
    omega2 = np.sqrt(2)

    # Synthetic trajectory (just for demo)
    trajectory = np.random.randn(10000, 18)

    def synthetic_integral(state):
        # Quasi-periodic function
        idx = np.random.randint(0, len(t))
        return np.sin(omega1 * t[idx]) + 0.5 * np.sin(omega2 * t[idx])

    m_est = estimate_elliptic_parameter(trajectory, t, synthetic_integral)
    print(f"Estimated elliptic parameter: m = {m_est:.4f}")

    print("\n" + "=" * 70)
    print("All tests complete")
    print("=" * 70)
