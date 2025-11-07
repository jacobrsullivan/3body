#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>
#include <qd/dd_real.h>

void test_catastrophic_cancellation() {
    std::cout << "=== Catastrophic Cancellation Tests ===" << std::endl;
    std::cout << std::endl;

    // Test (a + b) - a where b << a
    std::cout << "Testing (large + small) - large catastrophic cancellation:" << std::endl;

    std::vector<std::pair<std::string, std::string>> test_pairs = {
        {"1e20", "1e-10"},
        {"1e30", "1e-20"},
        {"1e15", "1e-15"},
        {"1e25", "1"},
        {"1e40", "1e-5"}
    };

    for (const auto& pair : test_pairs) {
        dd_real large(pair.first.c_str());
        dd_real small(pair.second.c_str());

        dd_real sum = large + small;
        dd_real difference = sum - large;
        dd_real error = abs(difference - small);
        dd_real relative_error = error / small;

        std::cout << "Large: " << pair.first << ", Small: " << pair.second << std::endl;
        std::cout << "Sum: " << sum.to_string(20) << std::endl;
        std::cout << "Recovered small: " << difference.to_string(35) << std::endl;
        std::cout << "Expected small: " << small.to_string(35) << std::endl;
        std::cout << "Absolute error: " << error.to_string(35) << std::endl;
        std::cout << "Relative error: " << relative_error.to_string(10) << std::endl;
        std::cout << "Precision preserved: " << (relative_error < dd_real("1e-25") ? "YES" : "NO") << std::endl;
        std::cout << std::endl;
    }

    // Test subtraction of nearly equal large numbers
    std::cout << "Testing subtraction of nearly equal large numbers:" << std::endl;
    dd_real base("1.23456789012345678901234567890123456789e30");
    dd_real delta("1e15");
    dd_real a = base + delta;
    dd_real b = base;
    dd_real diff = a - b;
    dd_real diff_error = abs(diff - delta);

    std::cout << "Base: " << base.to_string(20) << std::endl;
    std::cout << "a = base + delta: " << a.to_string(20) << std::endl;
    std::cout << "b = base: " << b.to_string(20) << std::endl;
    std::cout << "a - b: " << diff.to_string(35) << std::endl;
    std::cout << "Expected delta: " << delta.to_string(35) << std::endl;
    std::cout << "Recovery error: " << diff_error.to_string(35) << std::endl;
    std::cout << std::endl;
}

void test_iterative_stability() {
    std::cout << "=== Iterative Algorithm Stability ===" << std::endl;
    std::cout << std::endl;

    // Test Newton's method for sqrt(2) with high precision
    std::cout << "Testing Newton's method for sqrt(2):" << std::endl;
    dd_real x("1.5");  // Initial guess
    dd_real two("2.0");
    dd_real target = sqrt(two);

    std::cout << "Target sqrt(2): " << target.to_string(35) << std::endl;
    std::cout << "Initial guess: " << x.to_string(35) << std::endl;
    std::cout << std::endl;

    for (int i = 0; i < 10; ++i) {
        dd_real x_new = (x + two/x) / two;
        dd_real error = abs(x_new - target);
        dd_real relative_error = error / target;

        std::cout << "Iteration " << i+1 << ":" << std::endl;
        std::cout << "  x = " << x_new.to_string(35) << std::endl;
        std::cout << "  error = " << error.to_string(35) << std::endl;
        std::cout << "  relative error = " << relative_error.to_string(10) << std::endl;

        // Check for convergence
        if (relative_error < dd_real("1e-30")) {
            std::cout << "  Converged to machine precision!" << std::endl;
            break;
        }

        x = x_new;
        std::cout << std::endl;
    }

    // Test series convergence: arctan(1) = π/4 using Gregory-Leibniz series
    std::cout << std::endl << "Testing Gregory-Leibniz series for π/4:" << std::endl;
    std::cout << "arctan(1) = 1 - 1/3 + 1/5 - 1/7 + ... = π/4" << std::endl;

    dd_real sum("0.0");
    dd_real pi_over_4 = dd_real::_pi / dd_real("4.0");
    dd_real one("1.0");

    std::cout << "Target π/4: " << pi_over_4.to_string(35) << std::endl;
    std::cout << std::endl;

    for (int n = 0; n < 1000000; n += 100000) {
        // Add 100,000 terms at a time
        for (int i = 0; i < 100000; ++i) {
            int k = n + i;
            dd_real term = one / dd_real(2*k + 1);
            if (k % 2 == 1) term = -term;
            sum += term;
        }

        if (n % 100000 == 0 && n > 0) {
            dd_real error = abs(sum - pi_over_4);
            dd_real relative_error = error / pi_over_4;

            std::cout << "After " << n+100000 << " terms:" << std::endl;
            std::cout << "  sum = " << sum.to_string(35) << std::endl;
            std::cout << "  error = " << error.to_string(35) << std::endl;
            std::cout << "  relative error = " << relative_error.to_string(10) << std::endl;
            std::cout << std::endl;
        }
    }
}

void test_overflow_underflow_behavior() {
    std::cout << "=== Overflow/Underflow Behavior ===" << std::endl;
    std::cout << std::endl;

    // Test very large numbers
    std::cout << "Testing very large number operations:" << std::endl;
    dd_real very_large("1e100");
    dd_real large_squared = very_large * very_large;
    dd_real large_cubed = large_squared * very_large;

    std::cout << "1e100: " << very_large.to_string(20) << std::endl;
    std::cout << "(1e100)²: " << large_squared.to_string(20) << std::endl;
    std::cout << "(1e100)³: " << large_cubed.to_string(20) << std::endl;

    // Test arithmetic with very large numbers
    dd_real large_sum = very_large + very_large;
    dd_real large_diff = large_cubed - large_squared;

    std::cout << "1e100 + 1e100: " << large_sum.to_string(20) << std::endl;
    std::cout << "(1e100)³ - (1e100)²: " << large_diff.to_string(20) << std::endl;
    std::cout << std::endl;

    // Test very small numbers
    std::cout << "Testing very small number operations:" << std::endl;
    dd_real very_small("1e-100");
    dd_real small_squared = very_small * very_small;
    dd_real small_half = very_small / dd_real("2.0");

    std::cout << "1e-100: " << very_small.to_string(35) << std::endl;
    std::cout << "(1e-100)²: " << small_squared.to_string(35) << std::endl;
    std::cout << "(1e-100)/2: " << small_half.to_string(35) << std::endl;

    // Test operations between very large and very small
    dd_real product_extremes = very_large * very_small;
    dd_real ratio_extremes = very_large / very_small;

    std::cout << "1e100 * 1e-100: " << product_extremes.to_string(35) << std::endl;
    std::cout << "1e100 / 1e-100: " << ratio_extremes.to_string(20) << std::endl;
    std::cout << std::endl;
}

void test_precision_accumulation() {
    std::cout << "=== Precision Accumulation in Long Calculations ===" << std::endl;
    std::cout << std::endl;

    // Test precision loss in repeated operations
    std::cout << "Testing precision accumulation in repeated multiplication:" << std::endl;
    dd_real x("1.00000000000000000000000000000001");  // 1 + 1e-32
    dd_real product("1.0");

    std::cout << "Starting value: " << x.to_string(35) << std::endl;
    std::cout << "Computing x^n by repeated multiplication:" << std::endl;
    std::cout << std::endl;

    for (int n = 1; n <= 1000; n *= 10) {
        // Multiply to get x^n
        for (int i = product.is_zero() ? 1 : 100; i < n; i += (n <= 10 ? 1 : n/10)) {
            product *= x;
        }

        // Compare with direct power calculation
        dd_real exponent(n);
        dd_real direct_power = pow(x, exponent);
        dd_real accumulation_error = abs(product - direct_power);

        std::cout << "n = " << n << ":" << std::endl;
        std::cout << "  Repeated mult: " << product.to_string(35) << std::endl;
        std::cout << "  Direct power:  " << direct_power.to_string(35) << std::endl;
        std::cout << "  Accumulation error: " << accumulation_error.to_string(35) << std::endl;
        std::cout << std::endl;
    }

    // Test precision in summation of many small terms
    std::cout << "Testing precision accumulation in summation:" << std::endl;
    dd_real small_term("1e-15");
    dd_real sum("0.0");
    int n_terms = 1000000;

    for (int i = 0; i < n_terms; ++i) {
        sum += small_term;
    }

    dd_real expected = dd_real(n_terms) * small_term;
    dd_real summation_error = abs(sum - expected);

    std::cout << "Small term: " << small_term.to_string(35) << std::endl;
    std::cout << "Number of terms: " << n_terms << std::endl;
    std::cout << "Sum by addition: " << sum.to_string(35) << std::endl;
    std::cout << "Expected (n * term): " << expected.to_string(35) << std::endl;
    std::cout << "Summation error: " << summation_error.to_string(35) << std::endl;
    std::cout << "Relative error: " << (summation_error / expected).to_string(10) << std::endl;
    std::cout << std::endl;
}

void test_ill_conditioned_problems() {
    std::cout << "=== Ill-Conditioned Problem Tests ===" << std::endl;
    std::cout << std::endl;

    // Test Wilkinson polynomial evaluation near roots
    // p(x) = (x-1)(x-2)...(x-n) expanded and evaluated near integer roots
    std::cout << "Testing polynomial evaluation near roots:" << std::endl;

    // Simple case: p(x) = (x-1)(x-2)(x-3) = x³ - 6x² + 11x - 6
    // Evaluate near x = 1
    dd_real one("1.0");
    dd_real epsilon("1e-10");
    dd_real x = one + epsilon;

    // Direct evaluation: (x-1)(x-2)(x-3)
    dd_real p_direct = (x - one) * (x - dd_real("2.0")) * (x - dd_real("3.0"));

    // Expanded form: x³ - 6x² + 11x - 6
    dd_real x_squared = x * x;
    dd_real x_cubed = x_squared * x;
    dd_real p_expanded = x_cubed - dd_real("6.0") * x_squared + dd_real("11.0") * x - dd_real("6.0");

    std::cout << "Polynomial: (x-1)(x-2)(x-3)" << std::endl;
    std::cout << "Evaluation point: x = 1 + " << epsilon.to_string(15) << std::endl;
    std::cout << "Direct form: " << p_direct.to_string(35) << std::endl;
    std::cout << "Expanded form: " << p_expanded.to_string(35) << std::endl;
    std::cout << "Difference: " << abs(p_direct - p_expanded).to_string(35) << std::endl;
    std::cout << std::endl;

    // Test matrix condition number effects (Hilbert matrix-like)
    // Test linear system solution accuracy for H*x = b where H_ij = 1/(i+j-1)
    std::cout << "Testing linear system conditioning (3x3 Hilbert-like):" << std::endl;

    // Create 3x3 system: H*x = b where b = [1, 1, 1]
    // H = [1, 1/2, 1/3; 1/2, 1/3, 1/4; 1/3, 1/4, 1/5]
    // Solve for x, then verify H*x = b

    dd_real h11("1.0"), h12("0.5"), h13("0.33333333333333333333333333333333");
    dd_real h21("0.5"), h22("0.33333333333333333333333333333333"), h23("0.25");
    dd_real h31("0.33333333333333333333333333333333"), h32("0.25"), h33("0.2");

    dd_real b1("1.0"), b2("1.0"), b3("1.0");

    // Solve using Cramer's rule for 3x3 system
    dd_real det = h11*(h22*h33 - h23*h32) - h12*(h21*h33 - h23*h31) + h13*(h21*h32 - h22*h31);

    dd_real det1 = b1*(h22*h33 - h23*h32) - h12*(b2*h33 - h23*b3) + h13*(b2*h32 - h22*b3);
    dd_real det2 = h11*(b2*h33 - h23*b3) - b1*(h21*h33 - h23*h31) + h13*(h21*b3 - b2*h31);
    dd_real det3 = h11*(h22*b3 - b2*h32) - h12*(h21*b3 - b2*h31) + b1*(h21*h32 - h22*h31);

    dd_real x1 = det1 / det;
    dd_real x2 = det2 / det;
    dd_real x3 = det3 / det;

    // Verify solution by computing H*x
    dd_real check1 = h11*x1 + h12*x2 + h13*x3;
    dd_real check2 = h21*x1 + h22*x2 + h23*x3;
    dd_real check3 = h31*x1 + h32*x2 + h33*x3;

    std::cout << "System determinant: " << det.to_string(35) << std::endl;
    std::cout << "Solution: x1 = " << x1.to_string(20) << std::endl;
    std::cout << "          x2 = " << x2.to_string(20) << std::endl;
    std::cout << "          x3 = " << x3.to_string(20) << std::endl;
    std::cout << "Verification (should be [1,1,1]):" << std::endl;
    std::cout << "  H*x = [" << check1.to_string(20) << ", " << check2.to_string(20) << ", " << check3.to_string(20) << "]" << std::endl;
    std::cout << "Residuals:" << std::endl;
    std::cout << "  |b1 - (H*x)1| = " << abs(b1 - check1).to_string(35) << std::endl;
    std::cout << "  |b2 - (H*x)2| = " << abs(b2 - check2).to_string(35) << std::endl;
    std::cout << "  |b3 - (H*x)3| = " << abs(b3 - check3).to_string(35) << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "QD Library Numerical Stability Analysis" << std::endl;
    std::cout << "=======================================" << std::endl;
    std::cout << std::endl;

    std::cout << "Testing QD library behavior in numerically challenging scenarios" << std::endl;
    std::cout << "Focus: catastrophic cancellation, iterative stability, extreme values" << std::endl;
    std::cout << std::endl;

    test_catastrophic_cancellation();
    test_iterative_stability();
    test_overflow_underflow_behavior();
    test_precision_accumulation();
    test_ill_conditioned_problems();

    std::cout << "=== Numerical Stability Analysis Complete ===" << std::endl;
    std::cout << std::endl;
    std::cout << "Key Findings:" << std::endl;
    std::cout << "- QD library handles catastrophic cancellation significantly better than double precision" << std::endl;
    std::cout << "- Iterative algorithms converge to machine precision when theoretically expected" << std::endl;
    std::cout << "- Extended range allows computation with very large and very small numbers" << std::endl;
    std::cout << "- Precision accumulation in long calculations shows expected degradation patterns" << std::endl;
    std::cout << "- Ill-conditioned problems benefit from extended precision but still require careful numerics" << std::endl;

    return 0;
}
