#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <functional>
#include <chrono>
#include <qd/dd_real.h>

class QDTestSuite {
private:
    struct TestCase {
        std::string name;
        std::function<bool()> test_function;
        std::string category;
        bool passed;
        std::string error_message;
        double execution_time_ms;
    };

    std::vector<TestCase> test_cases;
    int tests_passed = 0;
    int tests_failed = 0;

public:
    void add_test(const std::string& name, const std::string& category, std::function<bool()> test_func) {
        test_cases.push_back({name, test_func, category, false, "", 0.0});
    }

    void run_all_tests() {
        std::cout << "QD Library Comprehensive Test Suite" << std::endl;
        std::cout << "====================================" << std::endl;
        std::cout << "Total tests: " << test_cases.size() << std::endl;
        std::cout << std::endl;

        std::string current_category = "";

        for (auto& test : test_cases) {
            if (test.category != current_category) {
                current_category = test.category;
                std::cout << std::endl << "=== " << current_category << " ===" << std::endl;
            }

            auto start = std::chrono::high_resolution_clock::now();

            try {
                test.passed = test.test_function();
                if (test.passed) {
                    tests_passed++;
                    std::cout << "✓ " << test.name;
                } else {
                    tests_failed++;
                    std::cout << "✗ " << test.name << " - FAILED";
                }
            } catch (const std::exception& e) {
                test.passed = false;
                test.error_message = e.what();
                tests_failed++;
                std::cout << "✗ " << test.name << " - ERROR: " << e.what();
            }

            auto end = std::chrono::high_resolution_clock::now();
            test.execution_time_ms = std::chrono::duration<double, std::milli>(end - start).count();

            std::cout << " (" << std::fixed << std::setprecision(2) << test.execution_time_ms << " ms)" << std::endl;
        }

        print_summary();
    }

private:
    void print_summary() {
        std::cout << std::endl << "=== Test Summary ===" << std::endl;
        std::cout << "Tests passed: " << tests_passed << std::endl;
        std::cout << "Tests failed: " << tests_failed << std::endl;
        std::cout << "Success rate: " << std::fixed << std::setprecision(1)
                  << (100.0 * tests_passed / (tests_passed + tests_failed)) << "%" << std::endl;

        double total_time = 0.0;
        for (const auto& test : test_cases) {
            total_time += test.execution_time_ms;
        }
        std::cout << "Total execution time: " << std::fixed << std::setprecision(2) << total_time << " ms" << std::endl;

        if (tests_failed > 0) {
            std::cout << std::endl << "Failed tests:" << std::endl;
            for (const auto& test : test_cases) {
                if (!test.passed) {
                    std::cout << "  " << test.name;
                    if (!test.error_message.empty()) {
                        std::cout << " (" << test.error_message << ")";
                    }
                    std::cout << std::endl;
                }
            }
        }

        if (tests_passed == tests_passed + tests_failed) {
            std::cout << std::endl << "🎉 All tests passed!" << std::endl;
        }
    }
};

// Test implementations
bool test_basic_arithmetic() {
    dd_real a("1.5");
    dd_real b("2.5");
    dd_real sum = a + b;
    dd_real expected("4.0");
    return abs(sum - expected) < dd_real("1e-30");
}

bool test_precision_limits() {
    dd_real one("1.0");
    dd_real small("1e-31");
    dd_real result = one + small;
    return result > one;  // Should be able to represent this difference
}

bool test_mathematical_constants() {
    // Test that π² ≈ 9.869604401...
    dd_real pi_squared = dd_real::_pi * dd_real::_pi;
    dd_real expected("9.8696044010893586188344909998761511353136994072408");
    dd_real error = abs(pi_squared - expected);
    return error < dd_real("1e-30");
}

bool test_trigonometric_identity() {
    // Test sin²(x) + cos²(x) = 1
    dd_real x("0.5");
    dd_real sin_x = sin(x);
    dd_real cos_x = cos(x);
    dd_real identity = sin_x * sin_x + cos_x * cos_x;
    dd_real one("1.0");
    return abs(identity - one) < dd_real("1e-30");
}

bool test_exponential_identity() {
    // Test e^(ln(x)) = x
    dd_real x("2.5");
    dd_real ln_x = log(x);
    dd_real exp_ln_x = exp(ln_x);
    return abs(exp_ln_x - x) < dd_real("1e-28");
}

bool test_catastrophic_cancellation() {
    // Test (1e15 + 1e-15) - 1e15 = 1e-15
    dd_real large("1e15");
    dd_real small("1e-15");
    dd_real sum = large + small;
    dd_real diff = sum - large;
    dd_real error = abs(diff - small);
    return error / small < dd_real("1e-15");  // Relative error should be small
}

bool test_iterative_convergence() {
    // Test Newton's method for sqrt(2) convergence
    dd_real x("1.5");
    dd_real two("2.0");
    dd_real target = sqrt(two);

    // One iteration should significantly improve accuracy
    dd_real x_new = (x + two/x) / two;
    dd_real error_before = abs(x - target);
    dd_real error_after = abs(x_new - target);

    return error_after < error_before * dd_real("0.1");  // Should improve by factor of 10
}

bool test_power_function() {
    // Test x^2 = x * x
    dd_real x("3.14159");
    dd_real power_result = pow(x, dd_real("2.0"));
    dd_real mult_result = x * x;
    return abs(power_result - mult_result) < dd_real("1e-28");
}

bool test_inverse_functions() {
    // Test sin(arcsin(x)) = x
    dd_real x("0.7");
    dd_real arcsin_x = asin(x);
    dd_real sin_arcsin_x = sin(arcsin_x);
    return abs(sin_arcsin_x - x) < dd_real("1e-30");
}

bool test_large_number_arithmetic() {
    // Test arithmetic with very large numbers
    dd_real large("1e50");
    dd_real result = large * large;
    dd_real expected("1e100");
    dd_real relative_error = abs((result - expected) / expected);
    return relative_error < dd_real("1e-25");
}

bool test_small_number_arithmetic() {
    // Test arithmetic with very small numbers
    dd_real small("1e-50");
    dd_real result = small * small;
    dd_real expected("1e-100");
    dd_real relative_error = abs((result - expected) / expected);
    return relative_error < dd_real("1e-25");
}

bool test_string_conversion() {
    // Test round-trip string conversion
    std::string original = "3.1415926535897932384626433832795";
    dd_real value(original.c_str());
    std::string converted = value.to_string(31);

    // Check that first 30 characters match (accounting for formatting)
    int matching = 0;
    size_t min_len = std::min(original.length(), converted.length());
    for (size_t i = 0; i < min_len && matching < 30; ++i) {
        if (original[i] == converted[i]) matching++;
        else break;
    }

    return matching >= 25;  // Should match at least 25 digits
}

bool test_division_by_zero_handling() {
    // Test that division by zero is handled appropriately
    try {
        dd_real a("1.0");
        dd_real zero("0.0");
        dd_real result = a / zero;

        // Check if result is infinite or very large
        std::string result_str = result.to_string(10);
        return result_str.find("inf") != std::string::npos ||
               result_str.find("nan") != std::string::npos ||
               abs(result) > dd_real("1e100");
    } catch (...) {
        return true;  // Exception handling is also acceptable
    }
}

bool test_machin_pi_formula() {
    // Test Machin's formula for π
    dd_real coeff1("16.0");
    dd_real coeff2("4.0");
    dd_real arg1 = dd_real("1.0") / dd_real("5.0");
    dd_real arg2 = dd_real("1.0") / dd_real("239.0");

    dd_real pi_machin = coeff1 * atan(arg1) - coeff2 * atan(arg2);
    dd_real error = abs(pi_machin - dd_real::_pi);

    return error < dd_real("1e-30");
}

bool test_memory_consistency() {
    // Test that dd_real objects maintain consistency across operations
    std::vector<dd_real> values;
    for (int i = 0; i < 100; ++i) {
        values.push_back(dd_real(i * 0.1));
    }

    // Verify all values are still correct
    for (int i = 0; i < 100; ++i) {
        dd_real expected(i * 0.1);
        if (abs(values[i] - expected) > dd_real("1e-30")) {
            return false;
        }
    }
    return true;
}

bool test_performance_regression() {
    // Simple performance regression test
    auto start = std::chrono::high_resolution_clock::now();

    dd_real sum("0.0");
    for (int i = 0; i < 10000; ++i) {
        dd_real x(i * 0.001);
        sum += sin(x) + cos(x);
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // Should complete in reasonable time (less than 5 seconds)
    return duration.count() < 5000;
}

int main() {
    QDTestSuite suite;

    // Basic arithmetic tests
    suite.add_test("Basic Addition", "Basic Arithmetic", test_basic_arithmetic);
    suite.add_test("Precision Limits", "Basic Arithmetic", test_precision_limits);
    suite.add_test("Power Function", "Basic Arithmetic", test_power_function);
    suite.add_test("Large Number Arithmetic", "Basic Arithmetic", test_large_number_arithmetic);
    suite.add_test("Small Number Arithmetic", "Basic Arithmetic", test_small_number_arithmetic);

    // Mathematical function tests
    suite.add_test("Mathematical Constants", "Mathematical Functions", test_mathematical_constants);
    suite.add_test("Trigonometric Identity", "Mathematical Functions", test_trigonometric_identity);
    suite.add_test("Exponential Identity", "Mathematical Functions", test_exponential_identity);
    suite.add_test("Inverse Functions", "Mathematical Functions", test_inverse_functions);
    suite.add_test("Machin π Formula", "Mathematical Functions", test_machin_pi_formula);

    // Numerical stability tests
    suite.add_test("Catastrophic Cancellation", "Numerical Stability", test_catastrophic_cancellation);
    suite.add_test("Iterative Convergence", "Numerical Stability", test_iterative_convergence);

    // System and integration tests
    suite.add_test("String Conversion", "System Integration", test_string_conversion);
    suite.add_test("Division by Zero", "System Integration", test_division_by_zero_handling);
    suite.add_test("Memory Consistency", "System Integration", test_memory_consistency);
    suite.add_test("Performance Regression", "System Integration", test_performance_regression);

    suite.run_all_tests();

    return 0;
}
