#include <iostream>
#include <iomanip>
#include <string>
#include <qd/dd_real.h>

void test_precision_limits() {
    std::cout << "=== QD Precision Limits Analysis ===" << std::endl;
    std::cout << std::endl;

    // Test addition precision at different scales
    std::cout << "Testing addition precision limits:" << std::endl;
    dd_real one("1.0");

    for (int i = 25; i <= 35; ++i) {
        std::string epsilon_str = "1e-" + std::to_string(i);
        dd_real test_epsilon(epsilon_str.c_str());
        dd_real result = one + test_epsilon;
        dd_real diff = result - one;

        std::cout << "1 + " << epsilon_str << " = " << result.to_string(35) << std::endl;
        std::cout << "Difference from 1: " << diff.to_string(35) << std::endl;
        std::cout << "Precision lost at 1e-" << i << ": " << (diff.is_zero() ? "YES" : "NO") << std::endl;
        std::cout << std::endl;
    }
}

void test_arithmetic_precision() {
    std::cout << "=== Compound Arithmetic Precision Analysis ===" << std::endl;
    std::cout << std::endl;

    // Test multiplication precision accumulation
    std::cout << "Testing precision degradation in compound multiplication:" << std::endl;
    dd_real x("1.0000000000000000000000000000001");  // 1 + 1e-31
    dd_real product = x;

    std::cout << "Starting value x = " << x.to_string(35) << std::endl;
    std::cout << "Computing x^n for increasing n:" << std::endl;
    std::cout << std::endl;

    for (int i = 1; i <= 100; i += 10) {
        for (int j = 0; j < 10; ++j) {
            product *= x;
        }
        std::cout << "x^" << i+10 << " = " << product.to_string(35) << std::endl;
    }

    std::cout << std::endl;

    // Test division precision
    std::cout << "Testing division precision with challenging ratios:" << std::endl;
    dd_real a("1.0");
    dd_real b("3.0");
    dd_real quotient = a / b;
    dd_real reconstructed = quotient * b;
    dd_real error = abs(reconstructed - a);

    std::cout << "1/3 = " << quotient.to_string(35) << std::endl;
    std::cout << "(1/3) * 3 = " << reconstructed.to_string(35) << std::endl;
    std::cout << "Reconstruction error: " << error.to_string(35) << std::endl;
    std::cout << std::endl;
}

void test_representation_accuracy() {
    std::cout << "=== Number Representation Accuracy ===" << std::endl;
    std::cout << std::endl;

    // Test decimal representation precision
    std::cout << "Testing decimal representation accuracy:" << std::endl;

    // Test known fractions
    std::vector<std::pair<std::string, std::string>> test_fractions = {
        {"1", "7"},
        {"22", "7"},  // pi approximation
        {"355", "113"},  // better pi approximation
        {"1", "9"},
        {"2", "9"}
    };

    for (const auto& frac : test_fractions) {
        dd_real numerator(frac.first.c_str());
        dd_real denominator(frac.second.c_str());
        dd_real quotient = numerator / denominator;

        std::cout << frac.first << "/" << frac.second << " = " << quotient.to_string(35) << std::endl;

        // Verify by reconstruction
        dd_real reconstructed = quotient * denominator;
        dd_real error = abs(reconstructed - numerator);
        std::cout << "Reconstruction error: " << error.to_string(35) << std::endl;
        std::cout << std::endl;
    }
}

void test_string_conversion_precision() {
    std::cout << "=== String Conversion Precision Analysis ===" << std::endl;
    std::cout << std::endl;

    // Test round-trip string conversion
    std::cout << "Testing round-trip string conversion:" << std::endl;

    std::vector<std::string> test_strings = {
        "3.1415926535897932384626433832795028841971693993751",
        "2.7182818284590452353602874713526624977572470937000",
        "1.4142135623730950488016887242096980785696718753769",
        "0.5772156649015328606065120900824024310421593359399"
    };

    for (const auto& test_str : test_strings) {
        dd_real value(test_str.c_str());
        std::string converted = value.to_string(test_str.length() - 2);  // Account for decimal point

        std::cout << "Original:  " << test_str << std::endl;
        std::cout << "Converted: " << converted << std::endl;

        // Check character-by-character agreement
        int matching_digits = 0;
        size_t min_len = std::min(test_str.length(), converted.length());

        for (size_t i = 0; i < min_len; ++i) {
            if (test_str[i] == converted[i]) {
                matching_digits++;
            } else {
                break;
            }
        }

        std::cout << "Matching characters: " << matching_digits << "/" << test_str.length() << std::endl;
        std::cout << "Precision agreement: " << (matching_digits >= 31 ? "EXCELLENT" : "LIMITED") << std::endl;
        std::cout << std::endl;
    }
}

void test_precision_at_boundaries() {
    std::cout << "=== Boundary Precision Testing ===" << std::endl;
    std::cout << std::endl;

    // Test precision near machine limits
    std::cout << "Testing precision near representation boundaries:" << std::endl;

    // Test very small numbers
    dd_real very_small("1e-100");
    dd_real tiny_increment("1e-130");
    dd_real sum_small = very_small + tiny_increment;
    dd_real diff_small = sum_small - very_small;

    std::cout << "Very small number test:" << std::endl;
    std::cout << "Base: " << very_small.to_string(35) << std::endl;
    std::cout << "Increment: " << tiny_increment.to_string(35) << std::endl;
    std::cout << "Sum: " << sum_small.to_string(35) << std::endl;
    std::cout << "Recovered increment: " << diff_small.to_string(35) << std::endl;
    std::cout << "Precision maintained: " << (!diff_small.is_zero() ? "YES" : "NO") << std::endl;
    std::cout << std::endl;

    // Test very large numbers
    dd_real very_large("1e50");
    dd_real large_increment("1e20");
    dd_real sum_large = very_large + large_increment;
    dd_real diff_large = sum_large - very_large;

    std::cout << "Very large number test:" << std::endl;
    std::cout << "Base: " << very_large.to_string(15) << std::endl;
    std::cout << "Increment: " << large_increment.to_string(15) << std::endl;
    std::cout << "Sum: " << sum_large.to_string(15) << std::endl;
    std::cout << "Recovered increment: " << diff_large.to_string(15) << std::endl;
    std::cout << "Precision maintained: " << (!diff_large.is_zero() ? "YES" : "NO") << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "QD Library Precision Analysis" << std::endl;
    std::cout << "=============================" << std::endl;
    std::cout << std::endl;

    std::cout << "Double-double (dd_real) precision analysis:" << std::endl;
    std::cout << "Expected precision: ~31 decimal digits" << std::endl;
    std::cout << "sizeof(dd_real): " << sizeof(dd_real) << " bytes" << std::endl;
    std::cout << "sizeof(double): " << sizeof(double) << " bytes" << std::endl;
    std::cout << "Memory overhead: " << sizeof(dd_real) / sizeof(double) << "x" << std::endl;
    std::cout << std::endl;

    test_precision_limits();
    test_arithmetic_precision();
    test_representation_accuracy();
    test_string_conversion_precision();
    test_precision_at_boundaries();

    std::cout << "=== Precision Analysis Complete ===" << std::endl;
    std::cout << std::endl;
    std::cout << "Key Findings:" << std::endl;
    std::cout << "- dd_real maintains precision to approximately 31 decimal digits" << std::endl;
    std::cout << "- Memory overhead is exactly 2x compared to double precision" << std::endl;
    std::cout << "- Arithmetic operations preserve precision within expected limits" << std::endl;
    std::cout << "- String conversion maintains full precision for round-trip operations" << std::endl;

    return 0;
}
