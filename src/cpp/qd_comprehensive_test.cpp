/**
 * Comprehensive QD Library Test Suite
 * Tests precision, accuracy, and stability of double-double arithmetic
 */

#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <cmath>
#include <qd/dd_real.h>

class QDTestSuite {
private:
    int passed_tests;
    int total_tests;

    void report_test(const std::string& name, bool passed, const std::string& details = "") {
        total_tests++;
        if (passed) {
            passed_tests++;
            std::cout << "✓ " << name << std::endl;
        } else {
            std::cout << "✗ " << name << " - FAILED" << std::endl;
            if (!details.empty()) {
                std::cout << "  Details: " << details << std::endl;
            }
        }
    }

public:
    QDTestSuite() : passed_tests(0), total_tests(0) {}

    // Test 1: Basic Arithmetic Precision
    void test_basic_arithmetic() {
        std::cout << "\n=== Testing Basic Arithmetic ===" << std::endl;

        // Test addition
        dd_real a("1.5");
        dd_real b("2.5");
        dd_real sum = a + b;
        dd_real expected("4.0");
        bool add_ok = abs(sum - expected) < dd_real("1e-30");
        report_test("Addition (1.5 + 2.5 = 4.0)", add_ok);

        // Test subtraction
        dd_real diff = b - a;
        expected = dd_real("1.0");
        bool sub_ok = abs(diff - expected) < dd_real("1e-30");
        report_test("Subtraction (2.5 - 1.5 = 1.0)", sub_ok);

        // Test multiplication
        dd_real product = a * b;
        expected = dd_real("3.75");
        bool mul_ok = abs(product - expected) < dd_real("1e-30");
        report_test("Multiplication (1.5 * 2.5 = 3.75)", mul_ok);

        // Test division
        dd_real quotient = b / a;
        expected = dd_real("1.666666666666666666666666666666667");
        dd_real error = abs(quotient - expected);
        bool div_ok = error < dd_real("1e-30");
        report_test("Division (2.5 / 1.5)", div_ok);
    }

    // Test 2: Precision Limits
    void test_precision_limits() {
        std::cout << "\n=== Testing Precision Limits ===" << std::endl;

        dd_real one("1.0");

        // Test that we can represent 1 + 1e-31
        dd_real tiny("1e-31");
        dd_real result = one + tiny;
        bool precision_31 = result > one;
        report_test("Precision at 1e-31 (1 + 1e-31 > 1)", precision_31);

        // Test that we lose precision at 1e-35
        dd_real very_tiny("1e-35");
        dd_real result2 = one + very_tiny;
        bool precision_35 = (result2 - one).is_zero();
        report_test("Precision limit at 1e-35 (precision lost)", precision_35);

        // Test mantissa bits (~106 bits)
        dd_real epsilon = dd_real("1e-31");
        dd_real sum = one;
        for (int i = 0; i < 10; ++i) {
            sum = sum + epsilon;
        }
        dd_real expected = one + dd_real("1e-30");
        bool accumulation = abs(sum - expected) < dd_real("1e-32");
        report_test("Precision accumulation (10 * 1e-31)", accumulation);
    }

    // Test 3: Mathematical Constants
    void test_mathematical_constants() {
        std::cout << "\n=== Testing Mathematical Constants ===" << std::endl;

        // Test Pi
        dd_real pi = dd_real::_pi;
        std::string pi_str = pi.to_string(35);
        bool pi_ok = pi_str.substr(0, 10) == "3.14159265";
        report_test("Pi constant (first 10 digits)", pi_ok);

        // Test e
        dd_real e = dd_real::_e;
        std::string e_str = e.to_string(35);
        bool e_ok = e_str.substr(0, 10) == "2.71828182";
        report_test("e constant (first 10 digits)", e_ok);

        // Test log2
        dd_real log2 = dd_real::_log2;
        dd_real expected_log2("0.69314718055994530941723212145817657");
        bool log2_ok = abs(log2 - expected_log2) < dd_real("1e-30");
        report_test("log2 constant", log2_ok);
    }

    // Test 4: Trigonometric Functions
    void test_trigonometric_functions() {
        std::cout << "\n=== Testing Trigonometric Functions ===" << std::endl;

        // Test sin(π/6) = 0.5
        dd_real pi = dd_real::_pi;
        dd_real pi_over_6 = pi / dd_real("6.0");
        dd_real sin_result = sin(pi_over_6);
        dd_real expected("0.5");
        dd_real error = abs(sin_result - expected);
        bool sin_ok = error < dd_real("1e-30");
        report_test("sin(π/6) = 0.5", sin_ok,
                   "Error: " + error.to_string(10));

        // Test cos(π/3) = 0.5
        dd_real pi_over_3 = pi / dd_real("3.0");
        dd_real cos_result = cos(pi_over_3);
        error = abs(cos_result - expected);
        bool cos_ok = error < dd_real("1e-30");
        report_test("cos(π/3) = 0.5", cos_ok,
                   "Error: " + error.to_string(10));

        // Test sin²(x) + cos²(x) = 1
        dd_real x("0.7853981633974483096156608458198757"); // π/4
        dd_real sin_x = sin(x);
        dd_real cos_x = cos(x);
        dd_real sum = sin_x * sin_x + cos_x * cos_x;
        error = abs(sum - dd_real("1.0"));
        bool identity_ok = error < dd_real("1e-30");
        report_test("Pythagorean identity: sin²(x) + cos²(x) = 1", identity_ok,
                   "Error: " + error.to_string(10));
    }

    // Test 5: Exponential and Logarithmic Functions
    void test_exponential_functions() {
        std::cout << "\n=== Testing Exponential Functions ===" << std::endl;

        // Test exp(1) = e
        dd_real one("1.0");
        dd_real exp_one = exp(one);
        dd_real e_constant = dd_real::_e;
        dd_real error = abs(exp_one - e_constant);
        bool exp_ok = error < dd_real("1e-30");
        report_test("exp(1) = e", exp_ok,
                   "Error: " + error.to_string(10));

        // Test log(e) = 1
        dd_real log_e = log(e_constant);
        error = abs(log_e - one);
        bool log_ok = error < dd_real("1e-30");
        report_test("log(e) = 1", log_ok,
                   "Error: " + error.to_string(10));

        // Test exp(log(x)) = x
        dd_real x("2.718281828");
        dd_real result = exp(log(x));
        error = abs(result - x);
        bool roundtrip_ok = error < dd_real("1e-28");
        report_test("exp(log(x)) = x", roundtrip_ok,
                   "Error: " + error.to_string(10));
    }

    // Test 6: Numerical Stability
    void test_numerical_stability() {
        std::cout << "\n=== Testing Numerical Stability ===" << std::endl;

        // Test catastrophic cancellation: (a + b) - a where b << a
        dd_real large("1e20");
        dd_real small("1e-10");
        dd_real sum = large + small;
        dd_real difference = sum - large;
        dd_real error = abs(difference - small);
        bool cancellation_ok = error < dd_real("1e-25");
        report_test("Catastrophic cancellation handling", cancellation_ok,
                   "Error: " + error.to_string(10));

        // Test iterative stability: Newton's method for sqrt(2)
        dd_real x("1.5");
        dd_real two("2.0");
        dd_real target = sqrt(two);

        // 10 iterations should converge
        for (int i = 0; i < 10; ++i) {
            x = (x + two/x) / two;
        }

        error = abs(x - target);
        bool newton_ok = error < dd_real("1e-30");
        report_test("Newton's method convergence (sqrt(2))", newton_ok,
                   "Error: " + error.to_string(10));
    }

    // Test 7: High-Precision Pi Calculation
    void test_machin_pi() {
        std::cout << "\n=== Testing Machin's Formula for Pi ===" << std::endl;

        // Machin's formula: π = 16*arctan(1/5) - 4*arctan(1/239)
        dd_real coeff1("16.0");
        dd_real coeff2("4.0");
        dd_real arg1 = dd_real("1.0") / dd_real("5.0");
        dd_real arg2 = dd_real("1.0") / dd_real("239.0");

        dd_real pi_calculated = coeff1 * atan(arg1) - coeff2 * atan(arg2);
        dd_real pi_qd = dd_real::_pi;
        dd_real error = abs(pi_calculated - pi_qd);

        bool machin_ok = error < dd_real("1e-30");
        report_test("Machin's formula for π", machin_ok,
                   "Error: " + error.to_string(10));
    }

    // Test 8: String Conversion and Parsing
    void test_string_operations() {
        std::cout << "\n=== Testing String Operations ===" << std::endl;

        // Test string construction
        dd_real from_string("3.14159265358979323846264338327950288");
        std::string back_to_string = from_string.to_string(35);
        bool string_ok = back_to_string.substr(0, 20) == "3.1415926535897932384";
        report_test("String construction and conversion", string_ok);

        // Test precision control
        dd_real pi = dd_real::_pi;
        std::string pi_10 = pi.to_string(10);
        std::string pi_30 = pi.to_string(30);
        bool precision_ok = pi_30.length() > pi_10.length();
        report_test("Precision control in string conversion", precision_ok);
    }

    void print_summary() {
        std::cout << "\n" << std::string(50, '=') << std::endl;
        std::cout << "Test Summary" << std::endl;
        std::cout << std::string(50, '=') << std::endl;
        std::cout << "Passed: " << passed_tests << "/" << total_tests << std::endl;

        if (passed_tests == total_tests) {
            std::cout << "🎉 All tests passed!" << std::endl;
        } else {
            std::cout << "❌ " << (total_tests - passed_tests) << " tests failed" << std::endl;
        }
        std::cout << std::string(50, '=') << std::endl;
    }

    int get_failed_count() {
        return total_tests - passed_tests;
    }
};

int main() {
    std::cout << "QD Library Comprehensive Test Suite" << std::endl;
    std::cout << std::string(50, '=') << std::endl;

    // Display QD library information
    std::cout << "QD Library Configuration:" << std::endl;
    std::cout << "  sizeof(dd_real): " << sizeof(dd_real) << " bytes" << std::endl;
    std::cout << "  sizeof(double): " << sizeof(double) << " bytes" << std::endl;
    std::cout << "  Memory overhead: " << sizeof(dd_real) / sizeof(double) << "x" << std::endl;

    QDTestSuite suite;

    // Run all tests
    suite.test_basic_arithmetic();
    suite.test_precision_limits();
    suite.test_mathematical_constants();
    suite.test_trigonometric_functions();
    suite.test_exponential_functions();
    suite.test_numerical_stability();
    suite.test_machin_pi();
    suite.test_string_operations();

    // Print summary
    suite.print_summary();

    // Return non-zero if any tests failed
    return suite.get_failed_count();
}
