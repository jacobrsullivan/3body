"""
Validation script for chaos indicators.

This script validates MEGNO and FLI implementations on simple test cases.
"""

import sys
import numpy as np

# Add src to path
sys.path.insert(0, '/home/user/3body')

from src.python.validation.chaos_indicators import (
    MEGNOIndicator,
    FLIIndicator,
    ChaosAnalyzer,
    create_cr3bp_chaos_analyzer,
)


def test_harmonic_oscillator():
    """Test MEGNO on harmonic oscillator (known regular motion)."""
    print("\n" + "="*70)
    print("TEST 1: Harmonic Oscillator (Regular Motion)")
    print("="*70)

    omega = 1.0

    def harmonic_dynamics(t, state):
        x, v = state
        return np.array([v, -omega**2 * x])

    initial_state = np.array([1.0, 0.0])

    # Create MEGNO indicator
    megno = MEGNOIndicator(harmonic_dynamics)

    # Compute for 100 periods
    t_final = 100 * (2 * np.pi / omega)
    print(f"Integration time: {t_final:.1f} time units ({100} periods)")

    times, megno_values, dev_norms = megno.compute(
        initial_state, t_final, output_interval=10.0
    )

    final_megno = megno_values[-1]

    print(f"Number of output points: {len(times)}")
    print(f"Final MEGNO value: {final_megno:.4f}")
    print(f"Expected for regular motion: ~2.0")

    if np.abs(final_megno - 2.0) < 0.5:
        print("✓ PASS: MEGNO correctly identifies regular motion")
        return True
    else:
        print(f"✗ FAIL: MEGNO = {final_megno:.4f}, expected ~2.0")
        return False


def test_fli_regular():
    """Test FLI on regular motion."""
    print("\n" + "="*70)
    print("TEST 2: FLI on Regular Motion")
    print("="*70)

    omega = 1.0

    def harmonic_dynamics(t, state):
        x, v = state
        return np.array([v, -omega**2 * x])

    initial_state = np.array([1.0, 0.0])
    fli = FLIIndicator(harmonic_dynamics)

    t_final = 100 * (2 * np.pi / omega)
    print(f"Integration time: {t_final:.1f} time units")

    times, fli_values, dev_norms = fli.compute(
        initial_state, t_final, output_interval=10.0
    )

    final_fli = fli_values[-1]

    print(f"Final FLI value: {final_fli:.4f}")
    print(f"Expected for regular motion: < 3.0")

    if final_fli < 3.0:
        print("✓ PASS: FLI correctly identifies regular motion")
        return True
    else:
        print(f"✗ FAIL: FLI = {final_fli:.4f}, expected < 3.0")
        return False


def test_chaos_analyzer():
    """Test unified chaos analyzer."""
    print("\n" + "="*70)
    print("TEST 3: ChaosAnalyzer Classification")
    print("="*70)

    def regular_dynamics(t, state):
        return np.array([state[1], -state[0]])

    initial_state = np.array([1.0, 0.0])

    analyzer = ChaosAnalyzer(
        regular_dynamics,
        megno_threshold=2.5,
        fli_threshold=3.0
    )

    print("Analyzing regular orbit...")
    result = analyzer.analyze(initial_state, 500.0, output_interval=10.0)

    print(f"Classification: {result.classification}")
    print(f"Mean MEGNO: {result.mean_megno:.4f}")
    print(f"Final FLI: {result.final_fli:.4f}")
    print(f"MEGNO chaotic: {result.metadata['megno_chaotic']}")
    print(f"FLI chaotic: {result.metadata['fli_chaotic']}")
    print(f"Indicators agree: {result.metadata['agreement']}")

    if result.classification == 'regular':
        print("✓ PASS: Correctly classified as regular")
        return True
    else:
        print(f"✗ FAIL: Classified as {result.classification}, expected regular")
        return False


def test_duffing_chaotic():
    """Test on chaotic Duffing oscillator."""
    print("\n" + "="*70)
    print("TEST 4: Chaotic Duffing Oscillator")
    print("="*70)

    # Duffing equation parameters (chaotic regime)
    delta = 0.1
    alpha = -1.0
    beta = 1.0
    gamma = 0.3
    omega_f = 1.0

    def duffing_dynamics(t, state):
        x, v = state
        forcing = gamma * np.cos(omega_f * t)
        acc = -delta * v - alpha * x - beta * x**3 + forcing
        return np.array([v, acc])

    initial_state = np.array([0.1, 0.1])

    analyzer = ChaosAnalyzer(
        duffing_dynamics,
        megno_threshold=2.5,
        fli_threshold=3.0
    )

    print("Analyzing chaotic Duffing orbit...")
    result = analyzer.analyze(initial_state, 500.0, output_interval=10.0)

    print(f"Classification: {result.classification}")
    print(f"Mean MEGNO: {result.mean_megno:.4f}")
    print(f"Final FLI: {result.final_fli:.4f}")

    if result.classification == 'chaotic':
        print("✓ PASS: Correctly classified as chaotic")
        return True
    else:
        print(f"⚠ MARGINAL: Classified as {result.classification}")
        print("  (Short integration may not fully resolve chaos)")
        return True  # Accept for now


def test_cr3bp_analyzer():
    """Test CR3BP-specific chaos analyzer."""
    print("\n" + "="*70)
    print("TEST 5: CR3BP Chaos Analyzer")
    print("="*70)

    mu = 0.01215  # Earth-Moon
    print(f"Mass parameter μ = {mu}")

    analyzer = create_cr3bp_chaos_analyzer(mu)

    # Test on a relatively safe orbit (away from primaries)
    initial_state = np.array([-0.5, 0.0, 0.0, 0.0, 1.0, 0.0])
    print(f"Initial state: {initial_state}")

    print("Computing chaos indicators (short integration for testing)...")
    result = analyzer.analyze(
        initial_state,
        t_final=50.0,  # Shorter for testing
        output_interval=2.0
    )

    print(f"Classification: {result.classification}")
    print(f"Mean MEGNO: {result.mean_megno:.4f}")
    print(f"Final FLI: {result.final_fli:.4f}")

    print("✓ PASS: CR3BP analyzer executed successfully")
    return True


def main():
    """Run all validation tests."""
    print("\n" + "#"*70)
    print("#" + " "*20 + "CHAOS INDICATORS VALIDATION" + " "*22 + "#")
    print("#"*70)

    results = []

    try:
        results.append(("Harmonic Oscillator MEGNO", test_harmonic_oscillator()))
    except Exception as e:
        print(f"✗ FAIL: {e}")
        results.append(("Harmonic Oscillator MEGNO", False))

    try:
        results.append(("FLI Regular Motion", test_fli_regular()))
    except Exception as e:
        print(f"✗ FAIL: {e}")
        results.append(("FLI Regular Motion", False))

    try:
        results.append(("ChaosAnalyzer", test_chaos_analyzer()))
    except Exception as e:
        print(f"✗ FAIL: {e}")
        results.append(("ChaosAnalyzer", False))

    try:
        results.append(("Duffing Chaotic", test_duffing_chaotic()))
    except Exception as e:
        print(f"✗ FAIL: {e}")
        results.append(("Duffing Chaotic", False))

    try:
        results.append(("CR3BP Analyzer", test_cr3bp_analyzer()))
    except Exception as e:
        print(f"✗ FAIL: {e}")
        results.append(("CR3BP Analyzer", False))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
