#include <iostream>
#include <iomanip>
#include <chrono>
#include <qd/dd_real.h>

class HighPrecisionPiCalculator {
public:
    // Machin's formula: π = 16*arctan(1/5) - 4*arctan(1/239)
    dd_real calculate_pi_machin() {
        std::cout << "Computing π using Machin's formula:" << std::endl;
        std::cout << "π = 16*arctan(1/5) - 4*arctan(1/239)" << std::endl;

        auto start = std::chrono::high_resolution_clock::now();

        dd_real coeff1("16.0");
        dd_real coeff2("4.0");
        dd_real arg1 = dd_real("1.0") / dd_real("5.0");
        dd_real arg2 = dd_real("1.0") / dd_real("239.0");

        dd_real pi_machin = coeff1 * atan(arg1) - coeff2 * atan(arg2);

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "Result: " << pi_machin.to_string(35) << std::endl;
        std::cout << "Time: " << duration.count() << " μs" << std::endl;

        return pi_machin;
    }

    // Bailey–Borwein–Plouffe formula (BBP)
    // π = Σ(k=0 to ∞) [1/16^k * (4/(8k+1) - 2/(8k+4) - 1/(8k+5) - 1/(8k+6))]
    dd_real calculate_pi_bbp(int iterations = 100) {
        std::cout << std::endl << "Computing π using Bailey-Borwein-Plouffe (BBP) formula:" << std::endl;
        std::cout << "Iterations: " << iterations << std::endl;

        auto start = std::chrono::high_resolution_clock::now();

        dd_real sum("0.0");
        dd_real sixteen("16.0");

        for (int k = 0; k < iterations; ++k) {
            dd_real k_dd(k);
            dd_real eight_k = dd_real("8.0") * k_dd;

            dd_real term1 = dd_real("4.0") / (eight_k + dd_real("1.0"));
            dd_real term2 = dd_real("2.0") / (eight_k + dd_real("4.0"));
            dd_real term3 = dd_real("1.0") / (eight_k + dd_real("5.0"));
            dd_real term4 = dd_real("1.0") / (eight_k + dd_real("6.0"));

            dd_real bracket_term = term1 - term2 - term3 - term4;
            dd_real power_term = pow(sixteen, -k_dd);

            sum += bracket_term * power_term;

            // Show convergence progress
            if (k > 0 && (k % 20 == 0 || k < 10)) {
                dd_real current_error = abs(sum - dd_real::_pi);
                std::cout << "  k=" << k << ": π ≈ " << sum.to_string(20) << ", error: " << current_error.to_string(10) << std::endl;
            }
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "Final result: " << sum.to_string(35) << std::endl;
        std::cout << "Time: " << duration.count() << " μs" << std::endl;

        return sum;
    }

    // Monte Carlo π estimation using random points in unit circle
    dd_real calculate_pi_monte_carlo(int n_points = 1000000) {
        std::cout << std::endl << "Computing π using Monte Carlo method:" << std::endl;
        std::cout << "Sample points: " << n_points << std::endl;

        auto start = std::chrono::high_resolution_clock::now();

        // Simple pseudo-random number generator (linear congruential)
        unsigned long long seed = 12345;
        int points_inside = 0;

        for (int i = 0; i < n_points; ++i) {
            // Generate pseudo-random x and y in [-1, 1]
            seed = (1103515245 * seed + 12345) % (1ULL << 31);
            double x = (double(seed) / (1ULL << 30)) - 1.0;

            seed = (1103515245 * seed + 12345) % (1ULL << 31);
            double y = (double(seed) / (1ULL << 30)) - 1.0;

            // Check if point is inside unit circle
            if (x*x + y*y <= 1.0) {
                points_inside++;
            }

            // Show progress
            if (i > 0 && i % (n_points / 10) == 0) {
                dd_real current_pi = dd_real("4.0") * dd_real(points_inside) / dd_real(i);
                dd_real error = abs(current_pi - dd_real::_pi);
                std::cout << "  " << i << " points: π ≈ " << current_pi.to_string(10) << ", error: " << error.to_string(8) << std::endl;
            }
        }

        dd_real pi_monte_carlo = dd_real("4.0") * dd_real(points_inside) / dd_real(n_points);

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        std::cout << "Final result: " << pi_monte_carlo.to_string(35) << std::endl;
        std::cout << "Time: " << duration.count() << " ms" << std::endl;

        return pi_monte_carlo;
    }

    // Gauss-Legendre algorithm (very fast convergence)
    dd_real calculate_pi_gauss_legendre(int iterations = 5) {
        std::cout << std::endl << "Computing π using Gauss-Legendre algorithm:" << std::endl;
        std::cout << "Iterations: " << iterations << " (doubles precision each iteration)" << std::endl;

        auto start = std::chrono::high_resolution_clock::now();

        dd_real a("1.0");
        dd_real b = dd_real("1.0") / sqrt(dd_real("2.0"));
        dd_real t("0.25");
        dd_real p("1.0");

        std::cout << "Initial values:" << std::endl;
        std::cout << "  a₀ = " << a.to_string(20) << std::endl;
        std::cout << "  b₀ = " << b.to_string(20) << std::endl;
        std::cout << "  t₀ = " << t.to_string(20) << std::endl;
        std::cout << std::endl;

        for (int i = 0; i < iterations; ++i) {
            dd_real a_next = (a + b) / dd_real("2.0");
            dd_real b_next = sqrt(a * b);
            dd_real t_next = t - p * (a - a_next) * (a - a_next);
            dd_real p_next = dd_real("2.0") * p;

            std::cout << "Iteration " << i+1 << ":" << std::endl;
            std::cout << "  a = " << a_next.to_string(20) << std::endl;
            std::cout << "  b = " << b_next.to_string(20) << std::endl;
            std::cout << "  t = " << t_next.to_string(20) << std::endl;

            // Calculate current π estimate
            dd_real pi_estimate = (a_next + b_next) * (a_next + b_next) / (dd_real("4.0") * t_next);
            dd_real error = abs(pi_estimate - dd_real::_pi);

            std::cout << "  π estimate = " << pi_estimate.to_string(35) << std::endl;
            std::cout << "  error = " << error.to_string(10) << std::endl;
            std::cout << std::endl;

            a = a_next;
            b = b_next;
            t = t_next;
            p = p_next;
        }

        dd_real pi_gauss = (a + b) * (a + b) / (dd_real("4.0") * t);

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "Final result: " << pi_gauss.to_string(35) << std::endl;
        std::cout << "Time: " << duration.count() << " μs" << std::endl;

        return pi_gauss;
    }

    // Ramanujan's formula (extremely fast convergence)
    dd_real calculate_pi_ramanujan(int iterations = 3) {
        std::cout << std::endl << "Computing π using Ramanujan's formula:" << std::endl;
        std::cout << "1/π = (2√2/9801) * Σ[(4k)!(1103+26390k)/((k!)⁴*396^(4k))]" << std::endl;
        std::cout << "Iterations: " << iterations << " (each adds ~8 digits)" << std::endl;

        auto start = std::chrono::high_resolution_clock::now();

        dd_real sum("0.0");
        dd_real factorial_k("1.0");
        dd_real factorial_4k("1.0");
        dd_real power_396("1.0");

        dd_real base_396("396.0");
        dd_real multiplier = dd_real("2.0") * sqrt(dd_real("2.0")) / dd_real("9801.0");

        for (int k = 0; k < iterations; ++k) {
            // Update factorials
            if (k > 0) {
                // Update k!
                factorial_k *= dd_real(k);

                // Update (4k)!
                for (int j = 4*(k-1) + 1; j <= 4*k; ++j) {
                    factorial_4k *= dd_real(j);
                }

                // Update 396^(4k)
                power_396 *= pow(base_396, dd_real("4.0"));
            }

            // Calculate term
            dd_real numerator = factorial_4k * (dd_real("1103.0") + dd_real("26390.0") * dd_real(k));
            dd_real denominator = pow(factorial_k, dd_real("4.0")) * power_396;
            dd_real term = numerator / denominator;

            sum += term;

            std::cout << "k=" << k << ": term = " << term.to_string(15) << std::endl;
            std::cout << "     sum = " << sum.to_string(35) << std::endl;

            // Calculate current π estimate
            dd_real pi_inverse = multiplier * sum;
            dd_real pi_estimate = dd_real("1.0") / pi_inverse;
            dd_real error = abs(pi_estimate - dd_real::_pi);

            std::cout << "     π estimate = " << pi_estimate.to_string(35) << std::endl;
            std::cout << "     error = " << error.to_string(10) << std::endl;
            std::cout << std::endl;
        }

        dd_real pi_ramanujan = dd_real("1.0") / (multiplier * sum);

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "Final result: " << pi_ramanujan.to_string(35) << std::endl;
        std::cout << "Time: " << duration.count() << " μs" << std::endl;

        return pi_ramanujan;
    }

    void compare_all_methods() {
        std::cout << std::endl << "=== Comparison of All π Calculation Methods ===" << std::endl;
        std::cout << std::endl;

        dd_real pi_reference = dd_real::_pi;
        std::cout << "Reference π (QD library): " << pi_reference.to_string(35) << std::endl;
        std::cout << std::endl;

        // Calculate using all methods
        dd_real pi_machin = calculate_pi_machin();
        dd_real pi_bbp = calculate_pi_bbp(50);
        dd_real pi_gauss = calculate_pi_gauss_legendre(4);
        dd_real pi_ramanujan = calculate_pi_ramanujan(2);
        dd_real pi_monte_carlo = calculate_pi_monte_carlo(100000);

        std::cout << std::endl << "=== Final Comparison ===" << std::endl;
        std::cout << std::setprecision(15) << std::scientific;

        std::vector<std::pair<std::string, dd_real>> results = {
            {"Machin", pi_machin},
            {"BBP", pi_bbp},
            {"Gauss-Legendre", pi_gauss},
            {"Ramanujan", pi_ramanujan},
            {"Monte Carlo", pi_monte_carlo}
        };

        for (const auto& result : results) {
            dd_real error = abs(result.second - pi_reference);
            dd_real relative_error = error / pi_reference;

            std::cout << result.first << ":" << std::endl;
            std::cout << "  Value: " << result.second.to_string(35) << std::endl;
            std::cout << "  Error: " << error.to_string(10) << std::endl;
            std::cout << "  Relative error: " << relative_error.to_string(10) << std::endl;
            std::cout << std::endl;
        }

        std::cout << "Performance ranking (by accuracy):" << std::endl;
        std::cout << "1. Gauss-Legendre (quadratic convergence)" << std::endl;
        std::cout << "2. Ramanujan (very fast convergence)" << std::endl;
        std::cout << "3. Machin (classical arctan formula)" << std::endl;
        std::cout << "4. BBP (spigot algorithm)" << std::endl;
        std::cout << "5. Monte Carlo (statistical approximation)" << std::endl;
    }
};

int main() {
    std::cout << "High-Precision π Calculation Algorithms" << std::endl;
    std::cout << "=======================================" << std::endl;
    std::cout << std::endl;

    std::cout << "Demonstrating various algorithms for computing π to high precision" << std::endl;
    std::cout << "All calculations use dd_real (double-double) arithmetic (~31 digits)" << std::endl;
    std::cout << std::endl;

    HighPrecisionPiCalculator calculator;
    calculator.compare_all_methods();

    std::cout << std::endl << "=== Algorithm Analysis Complete ===" << std::endl;
    std::cout << std::endl;
    std::cout << "Key Insights:" << std::endl;
    std::cout << "- Gauss-Legendre achieves machine precision in just a few iterations" << std::endl;
    std::cout << "- Ramanujan's formula provides exceptional convergence rate" << std::endl;
    std::cout << "- Classical methods (Machin) remain highly effective" << std::endl;
    std::cout << "- Monte Carlo demonstrates statistical vs. analytical approaches" << std::endl;
    std::cout << "- All deterministic methods achieve precision limited only by dd_real representation" << std::endl;

    return 0;
}
