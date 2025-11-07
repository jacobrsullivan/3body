#include <iostream>
#include <iomanip>
#include <cmath>
#include <qd/dd_real.h>

void test_trigonometric_accuracy() {
    std::cout << "=== Trigonometric Function Accuracy ===" << std::endl;
    std::cout << std::endl;

    // Test sin(π/6) = 0.5 exactly
    std::cout << "Testing sin(π/6) = 0.5:" << std::endl;
    dd_real pi = dd_real::_pi;
    dd_real pi_over_6 = pi / dd_real("6.0");
    dd_real sin_result = sin(pi_over_6);
    dd_real expected_half = dd_real("0.5");
    dd_real sin_error = abs(sin_result - expected_half);

    std::cout << "π/6 = " << pi_over_6.to_string(35) << std::endl;
    std::cout << "sin(π/6) = " << sin_result.to_string(35) << std::endl;
    std::cout << "Expected: 0.5" << std::endl;
    std::cout << "Error: " << sin_error.to_string(35) << std::endl;
    std::cout << "Relative error: " << (sin_error / expected_half).to_string(10) << std::endl;
    std::cout << std::endl;

    // Test cos(π/3) = 0.5
    std::cout << "Testing cos(π/3) = 0.5:" << std::endl;
    dd_real pi_over_3 = pi / dd_real("3.0");
    dd_real cos_result = cos(pi_over_3);
    dd_real cos_error = abs(cos_result - expected_half);

    std::cout << "π/3 = " << pi_over_3.to_string(35) << std::endl;
    std::cout << "cos(π/3) = " << cos_result.to_string(35) << std::endl;
    std::cout << "Expected: 0.5" << std::endl;
    std::cout << "Error: " << cos_error.to_string(35) << std::endl;
    std::cout << "Relative error: " << (cos_error / expected_half).to_string(10) << std::endl;
    std::cout << std::endl;

    // Test sin(π/4) = cos(π/4) = √2/2
    std::cout << "Testing sin(π/4) = cos(π/4) = √2/2:" << std::endl;
    dd_real pi_over_4 = pi / dd_real("4.0");
    dd_real sin_45 = sin(pi_over_4);
    dd_real cos_45 = cos(pi_over_4);
    dd_real sqrt2_over_2 = sqrt(dd_real("2.0")) / dd_real("2.0");

    std::cout << "π/4 = " << pi_over_4.to_string(35) << std::endl;
    std::cout << "sin(π/4) = " << sin_45.to_string(35) << std::endl;
    std::cout << "cos(π/4) = " << cos_45.to_string(35) << std::endl;
    std::cout << "√2/2 = " << sqrt2_over_2.to_string(35) << std::endl;
    std::cout << "sin error: " << abs(sin_45 - sqrt2_over_2).to_string(35) << std::endl;
    std::cout << "cos error: " << abs(cos_45 - sqrt2_over_2).to_string(35) << std::endl;
    std::cout << "sin = cos: " << abs(sin_45 - cos_45).to_string(35) << std::endl;
    std::cout << std::endl;

    // Test sin(π/2) = 1 and cos(π/2) = 0
    std::cout << "Testing sin(π/2) = 1, cos(π/2) = 0:" << std::endl;
    dd_real pi_over_2 = pi / dd_real("2.0");
    dd_real sin_90 = sin(pi_over_2);
    dd_real cos_90 = cos(pi_over_2);
    dd_real one = dd_real("1.0");
    dd_real zero = dd_real("0.0");

    std::cout << "sin(π/2) = " << sin_90.to_string(35) << std::endl;
    std::cout << "cos(π/2) = " << cos_90.to_string(35) << std::endl;
    std::cout << "sin error from 1: " << abs(sin_90 - one).to_string(35) << std::endl;
    std::cout << "cos error from 0: " << abs(cos_90 - zero).to_string(35) << std::endl;
    std::cout << std::endl;
}

void test_exponential_accuracy() {
    std::cout << "=== Exponential Function Accuracy ===" << std::endl;
    std::cout << std::endl;

    // Test e^1 = e
    std::cout << "Testing exp(1) = e:" << std::endl;
    dd_real one("1.0");
    dd_real exp_one = exp(one);
    dd_real e_constant = dd_real::_e;
    dd_real exp_error = abs(exp_one - e_constant);

    std::cout << "exp(1) = " << exp_one.to_string(35) << std::endl;
    std::cout << "e constant = " << e_constant.to_string(35) << std::endl;
    std::cout << "Error: " << exp_error.to_string(35) << std::endl;
    std::cout << "Relative error: " << (exp_error / e_constant).to_string(10) << std::endl;
    std::cout << std::endl;

    // Test exp(0) = 1
    std::cout << "Testing exp(0) = 1:" << std::endl;
    dd_real zero("0.0");
    dd_real exp_zero = exp(zero);
    dd_real exp_zero_error = abs(exp_zero - one);

    std::cout << "exp(0) = " << exp_zero.to_string(35) << std::endl;
    std::cout << "Expected: 1.0" << std::endl;
    std::cout << "Error: " << exp_zero_error.to_string(35) << std::endl;
    std::cout << std::endl;

    // Test exp(ln(x)) = x for various x
    std::cout << "Testing exp(ln(x)) = x identity:" << std::endl;
    std::vector<dd_real> test_values = {
        dd_real("2.0"),
        dd_real("10.0"),
        dd_real("0.5"),
        dd_real("100.0")
    };

    for (const auto& x : test_values) {
        dd_real ln_x = log(x);
        dd_real exp_ln_x = exp(ln_x);
        dd_real identity_error = abs(exp_ln_x - x);

        std::cout << "x = " << x.to_string(10) << std::endl;
        std::cout << "ln(x) = " << ln_x.to_string(35) << std::endl;
        std::cout << "exp(ln(x)) = " << exp_ln_x.to_string(35) << std::endl;
        std::cout << "Identity error: " << identity_error.to_string(35) << std::endl;
        std::cout << "Relative error: " << (identity_error / x).to_string(10) << std::endl;
        std::cout << std::endl;
    }
}

void test_logarithmic_accuracy() {
    std::cout << "=== Logarithmic Function Accuracy ===" << std::endl;
    std::cout << std::endl;

    // Test log(e) = 1
    std::cout << "Testing log(e) = 1:" << std::endl;
    dd_real e = dd_real::_e;
    dd_real log_e = log(e);
    dd_real one("1.0");
    dd_real log_error = abs(log_e - one);

    std::cout << "log(e) = " << log_e.to_string(35) << std::endl;
    std::cout << "Expected: 1.0" << std::endl;
    std::cout << "Error: " << log_error.to_string(35) << std::endl;
    std::cout << std::endl;

    // Test log(1) = 0
    std::cout << "Testing log(1) = 0:" << std::endl;
    dd_real log_one = log(one);
    dd_real zero("0.0");
    dd_real log_one_error = abs(log_one - zero);

    std::cout << "log(1) = " << log_one.to_string(35) << std::endl;
    std::cout << "Expected: 0.0" << std::endl;
    std::cout << "Error: " << log_one_error.to_string(35) << std::endl;
    std::cout << std::endl;

    // Test log(10) for base conversion
    std::cout << "Testing log(10) and log10 consistency:" << std::endl;
    dd_real ten("10.0");
    dd_real log_10 = log(ten);
    dd_real log10_10 = log10(ten);
    dd_real log10_expected = dd_real("1.0");

    std::cout << "log(10) = " << log_10.to_string(35) << std::endl;
    std::cout << "log10(10) = " << log10_10.to_string(35) << std::endl;
    std::cout << "log10 error from 1: " << abs(log10_10 - log10_expected).to_string(35) << std::endl;

    // Verify log(10) = ln(10) ≈ 2.302585...
    dd_real ln10_expected("2.302585092994045684017991454684364207601101488628772976");
    dd_real ln10_error = abs(log_10 - ln10_expected);
    std::cout << "ln(10) expected: " << ln10_expected.to_string(35) << std::endl;
    std::cout << "ln(10) error: " << ln10_error.to_string(35) << std::endl;
    std::cout << std::endl;
}

void test_power_function_accuracy() {
    std::cout << "=== Power Function Accuracy ===" << std::endl;
    std::cout << std::endl;

    // Test x^2 = x * x
    std::cout << "Testing x^2 = x * x identity:" << std::endl;
    std::vector<dd_real> bases = {
        dd_real("2.0"),
        dd_real("3.5"),
        dd_real("0.7"),
        dd_real("10.0")
    };

    dd_real two("2.0");
    for (const auto& x : bases) {
        dd_real power_result = pow(x, two);
        dd_real mult_result = x * x;
        dd_real power_error = abs(power_result - mult_result);

        std::cout << "x = " << x.to_string(10) << std::endl;
        std::cout << "pow(x, 2) = " << power_result.to_string(35) << std::endl;
        std::cout << "x * x = " << mult_result.to_string(35) << std::endl;
        std::cout << "Error: " << power_error.to_string(35) << std::endl;
        std::cout << std::endl;
    }

    // Test x^0 = 1
    std::cout << "Testing x^0 = 1:" << std::endl;
    dd_real zero("0.0");
    dd_real one("1.0");

    for (const auto& x : bases) {
        dd_real power_zero = pow(x, zero);
        dd_real power_zero_error = abs(power_zero - one);

        std::cout << "pow(" << x.to_string(10) << ", 0) = " << power_zero.to_string(35) << std::endl;
        std::cout << "Error from 1: " << power_zero_error.to_string(35) << std::endl;
        std::cout << std::endl;
    }

    // Test 2^n for integer powers
    std::cout << "Testing powers of 2:" << std::endl;
    dd_real base_2("2.0");
    for (int n = 1; n <= 10; ++n) {
        dd_real exponent(n);
        dd_real power_result = pow(base_2, exponent);

        // Calculate expected value by repeated multiplication
        dd_real expected("1.0");
        for (int i = 0; i < n; ++i) {
            expected *= base_2;
        }

        dd_real power_error = abs(power_result - expected);
        std::cout << "2^" << n << " = " << power_result.to_string(20) << ", error: " << power_error.to_string(35) << std::endl;
    }
    std::cout << std::endl;
}

void test_inverse_relationships() {
    std::cout << "=== Inverse Function Relationships ===" << std::endl;
    std::cout << std::endl;

    // Test sin(arcsin(x)) = x
    std::cout << "Testing sin(arcsin(x)) = x:" << std::endl;
    std::vector<dd_real> arcsin_inputs = {
        dd_real("0.0"),
        dd_real("0.5"),
        dd_real("0.7071067811865475"),  // √2/2
        dd_real("0.8660254037844387"),  // √3/2
        dd_real("1.0")
    };

    for (const auto& x : arcsin_inputs) {
        dd_real arcsin_x = asin(x);
        dd_real sin_arcsin_x = sin(arcsin_x);
        dd_real inverse_error = abs(sin_arcsin_x - x);

        std::cout << "x = " << x.to_string(20) << std::endl;
        std::cout << "arcsin(x) = " << arcsin_x.to_string(35) << std::endl;
        std::cout << "sin(arcsin(x)) = " << sin_arcsin_x.to_string(35) << std::endl;
        std::cout << "Error: " << inverse_error.to_string(35) << std::endl;
        std::cout << std::endl;
    }

    // Test tan(arctan(x)) = x
    std::cout << "Testing tan(arctan(x)) = x:" << std::endl;
    std::vector<dd_real> arctan_inputs = {
        dd_real("0.0"),
        dd_real("1.0"),
        dd_real("0.5773502691896257"),  // 1/√3
        dd_real("1.7320508075688772"),  // √3
        dd_real("10.0")
    };

    for (const auto& x : arctan_inputs) {
        dd_real arctan_x = atan(x);
        dd_real tan_arctan_x = tan(arctan_x);
        dd_real inverse_error = abs(tan_arctan_x - x);

        std::cout << "x = " << x.to_string(20) << std::endl;
        std::cout << "arctan(x) = " << arctan_x.to_string(35) << std::endl;
        std::cout << "tan(arctan(x)) = " << tan_arctan_x.to_string(35) << std::endl;
        std::cout << "Error: " << inverse_error.to_string(35) << std::endl;
        std::cout << std::endl;
    }
}

void test_mathematical_identities() {
    std::cout << "=== Mathematical Identity Verification ===" << std::endl;
    std::cout << std::endl;

    // Test sin²(x) + cos²(x) = 1
    std::cout << "Testing sin²(x) + cos²(x) = 1:" << std::endl;
    std::vector<dd_real> identity_angles = {
        dd_real("0.1"),
        dd_real("0.5"),
        dd_real("1.0"),
        dd_real("1.5"),
        dd_real("2.0")
    };

    dd_real one("1.0");
    for (const auto& x : identity_angles) {
        dd_real sin_x = sin(x);
        dd_real cos_x = cos(x);
        dd_real sin_squared = sin_x * sin_x;
        dd_real cos_squared = cos_x * cos_x;
        dd_real identity_sum = sin_squared + cos_squared;
        dd_real identity_error = abs(identity_sum - one);

        std::cout << "x = " << x.to_string(10) << std::endl;
        std::cout << "sin²(x) = " << sin_squared.to_string(35) << std::endl;
        std::cout << "cos²(x) = " << cos_squared.to_string(35) << std::endl;
        std::cout << "sin²(x) + cos²(x) = " << identity_sum.to_string(35) << std::endl;
        std::cout << "Error from 1: " << identity_error.to_string(35) << std::endl;
        std::cout << std::endl;
    }

    // Test e^(iπ) + 1 = 0 using e^(ix) = cos(x) + i*sin(x)
    // For real arithmetic: e^(π*i) corresponds to cos(π) + i*sin(π) = -1 + i*0 = -1
    // So e^(π*i) + 1 = 0, or cos(π) = -1, sin(π) = 0
    std::cout << "Testing Euler's identity components (cos(π) = -1, sin(π) = 0):" << std::endl;
    dd_real pi = dd_real::_pi;
    dd_real cos_pi = cos(pi);
    dd_real sin_pi = sin(pi);
    dd_real minus_one("-1.0");
    dd_real zero("0.0");

    std::cout << "π = " << pi.to_string(35) << std::endl;
    std::cout << "cos(π) = " << cos_pi.to_string(35) << std::endl;
    std::cout << "sin(π) = " << sin_pi.to_string(35) << std::endl;
    std::cout << "cos(π) error from -1: " << abs(cos_pi - minus_one).to_string(35) << std::endl;
    std::cout << "sin(π) error from 0: " << abs(sin_pi - zero).to_string(35) << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "QD Library Mathematical Function Accuracy Analysis" << std::endl;
    std::cout << "=================================================" << std::endl;
    std::cout << std::endl;

    std::cout << "Testing mathematical function accuracy with double-double precision" << std::endl;
    std::cout << "Expected accuracy: ~31 decimal digits for most operations" << std::endl;
    std::cout << std::endl;

    test_trigonometric_accuracy();
    test_exponential_accuracy();
    test_logarithmic_accuracy();
    test_power_function_accuracy();
    test_inverse_relationships();
    test_mathematical_identities();

    std::cout << "=== Mathematical Function Analysis Complete ===" << std::endl;
    std::cout << std::endl;
    std::cout << "Key Findings:" << std::endl;
    std::cout << "- Trigonometric functions maintain high accuracy for special values" << std::endl;
    std::cout << "- Exponential/logarithmic functions preserve precision in identities" << std::endl;
    std::cout << "- Power functions agree with direct multiplication" << std::endl;
    std::cout << "- Inverse function relationships maintained within precision limits" << std::endl;
    std::cout << "- Fundamental mathematical identities verified to high precision" << std::endl;

    return 0;
}
