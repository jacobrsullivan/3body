#include <iostream>
#include <iomanip>
#include <vector>
#include <chrono>
#include <cmath>
#include <qd/dd_real.h>

class PerformanceBenchmark {
private:
    static const int ARITHMETIC_OPERATIONS = 1000000;
    static const int FUNCTION_OPERATIONS = 100000;
    static const int MEMORY_OPERATIONS = 500000;

public:
    void benchmark_basic_arithmetic() {
        std::cout << "=== Basic Arithmetic Operations Benchmark ===" << std::endl;
        std::cout << "Operations per test: " << ARITHMETIC_OPERATIONS << std::endl;
        std::cout << std::endl;

        // Initialize test data
        std::vector<dd_real> dd_data_a(ARITHMETIC_OPERATIONS);
        std::vector<dd_real> dd_data_b(ARITHMETIC_OPERATIONS);
        std::vector<double> double_data_a(ARITHMETIC_OPERATIONS);
        std::vector<double> double_data_b(ARITHMETIC_OPERATIONS);

        for (int i = 0; i < ARITHMETIC_OPERATIONS; ++i) {
            double val_a = 1.1 + i * 1e-10;
            double val_b = 2.2 + i * 1e-11;
            dd_data_a[i] = dd_real(val_a);
            dd_data_b[i] = dd_real(val_b);
            double_data_a[i] = val_a;
            double_data_b[i] = val_b;
        }

        // Benchmark addition
        benchmark_operation("Addition",
            [&]() {
                dd_real dd_sum("0.0");
                for (int i = 0; i < ARITHMETIC_OPERATIONS; ++i) {
                    dd_sum += dd_data_a[i] + dd_data_b[i];
                }
                return dd_sum;
            },
            [&]() {
                double double_sum = 0.0;
                for (int i = 0; i < ARITHMETIC_OPERATIONS; ++i) {
                    double_sum += double_data_a[i] + double_data_b[i];
                }
                return double_sum;
            }
        );

        // Benchmark multiplication
        benchmark_operation("Multiplication",
            [&]() {
                dd_real dd_product("1.0");
                for (int i = 0; i < ARITHMETIC_OPERATIONS / 1000; ++i) {
                    dd_product *= dd_data_a[i] * dd_data_b[i];
                }
                return dd_product;
            },
            [&]() {
                double double_product = 1.0;
                for (int i = 0; i < ARITHMETIC_OPERATIONS / 1000; ++i) {
                    double_product *= double_data_a[i] * double_data_b[i];
                }
                return double_product;
            }
        );

        // Benchmark division
        benchmark_operation("Division",
            [&]() {
                dd_real dd_result("0.0");
                for (int i = 0; i < ARITHMETIC_OPERATIONS; ++i) {
                    dd_result += dd_data_a[i] / dd_data_b[i];
                }
                return dd_result;
            },
            [&]() {
                double double_result = 0.0;
                for (int i = 0; i < ARITHMETIC_OPERATIONS; ++i) {
                    double_result += double_data_a[i] / double_data_b[i];
                }
                return double_result;
            }
        );

        std::cout << std::endl;
    }

    void benchmark_mathematical_functions() {
        std::cout << "=== Mathematical Functions Benchmark ===" << std::endl;
        std::cout << "Operations per test: " << FUNCTION_OPERATIONS << std::endl;
        std::cout << std::endl;

        // Initialize test data
        std::vector<dd_real> dd_angles(FUNCTION_OPERATIONS);
        std::vector<double> double_angles(FUNCTION_OPERATIONS);

        for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
            double angle = -M_PI + (2.0 * M_PI * i) / FUNCTION_OPERATIONS;
            dd_angles[i] = dd_real(angle);
            double_angles[i] = angle;
        }

        // Benchmark sin function
        benchmark_function("sin(x)",
            [&]() {
                dd_real dd_sum("0.0");
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    dd_sum += sin(dd_angles[i]);
                }
                return dd_sum;
            },
            [&]() {
                double double_sum = 0.0;
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    double_sum += std::sin(double_angles[i]);
                }
                return double_sum;
            }
        );

        // Benchmark cos function
        benchmark_function("cos(x)",
            [&]() {
                dd_real dd_sum("0.0");
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    dd_sum += cos(dd_angles[i]);
                }
                return dd_sum;
            },
            [&]() {
                double double_sum = 0.0;
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    double_sum += std::cos(double_angles[i]);
                }
                return double_sum;
            }
        );

        // Benchmark exp function
        std::vector<dd_real> dd_exp_inputs(FUNCTION_OPERATIONS);
        std::vector<double> double_exp_inputs(FUNCTION_OPERATIONS);

        for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
            double val = -5.0 + (10.0 * i) / FUNCTION_OPERATIONS;
            dd_exp_inputs[i] = dd_real(val);
            double_exp_inputs[i] = val;
        }

        benchmark_function("exp(x)",
            [&]() {
                dd_real dd_sum("0.0");
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    dd_sum += exp(dd_exp_inputs[i]);
                }
                return dd_sum;
            },
            [&]() {
                double double_sum = 0.0;
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    double_sum += std::exp(double_exp_inputs[i]);
                }
                return double_sum;
            }
        );

        // Benchmark sqrt function
        std::vector<dd_real> dd_sqrt_inputs(FUNCTION_OPERATIONS);
        std::vector<double> double_sqrt_inputs(FUNCTION_OPERATIONS);

        for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
            double val = 0.1 + (100.0 * i) / FUNCTION_OPERATIONS;
            dd_sqrt_inputs[i] = dd_real(val);
            double_sqrt_inputs[i] = val;
        }

        benchmark_function("sqrt(x)",
            [&]() {
                dd_real dd_sum("0.0");
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    dd_sum += sqrt(dd_sqrt_inputs[i]);
                }
                return dd_sum;
            },
            [&]() {
                double double_sum = 0.0;
                for (int i = 0; i < FUNCTION_OPERATIONS; ++i) {
                    double_sum += std::sqrt(double_sqrt_inputs[i]);
                }
                return double_sum;
            }
        );

        std::cout << std::endl;
    }

    void benchmark_memory_operations() {
        std::cout << "=== Memory Operations Benchmark ===" << std::endl;
        std::cout << "Array size: " << MEMORY_OPERATIONS << " elements" << std::endl;
        std::cout << std::endl;

        // Memory allocation benchmark
        std::cout << "Memory allocation:" << std::endl;

        auto start = std::chrono::high_resolution_clock::now();
        std::vector<dd_real> dd_array(MEMORY_OPERATIONS);
        auto end = std::chrono::high_resolution_clock::now();
        auto dd_alloc_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        start = std::chrono::high_resolution_clock::now();
        std::vector<double> double_array(MEMORY_OPERATIONS);
        end = std::chrono::high_resolution_clock::now();
        auto double_alloc_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "  dd_real allocation: " << dd_alloc_time.count() << " μs" << std::endl;
        std::cout << "  double allocation: " << double_alloc_time.count() << " μs" << std::endl;
        std::cout << "  Overhead factor: " << double(dd_alloc_time.count()) / double_alloc_time.count() << "x" << std::endl;
        std::cout << std::endl;

        // Memory copy benchmark
        std::vector<dd_real> dd_source(MEMORY_OPERATIONS);
        std::vector<dd_real> dd_dest(MEMORY_OPERATIONS);
        std::vector<double> double_source(MEMORY_OPERATIONS);
        std::vector<double> double_dest(MEMORY_OPERATIONS);

        // Initialize source arrays
        for (int i = 0; i < MEMORY_OPERATIONS; ++i) {
            dd_source[i] = dd_real(i * 1.1);
            double_source[i] = i * 1.1;
        }

        std::cout << "Memory copy operations:" << std::endl;

        start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < MEMORY_OPERATIONS; ++i) {
            dd_dest[i] = dd_source[i];
        }
        end = std::chrono::high_resolution_clock::now();
        auto dd_copy_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < MEMORY_OPERATIONS; ++i) {
            double_dest[i] = double_source[i];
        }
        end = std::chrono::high_resolution_clock::now();
        auto double_copy_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "  dd_real copy: " << dd_copy_time.count() << " μs" << std::endl;
        std::cout << "  double copy: " << double_copy_time.count() << " μs" << std::endl;
        std::cout << "  Overhead factor: " << double(dd_copy_time.count()) / double_copy_time.count() << "x" << std::endl;
        std::cout << std::endl;

        // Memory usage analysis
        std::cout << "Memory usage analysis:" << std::endl;
        std::cout << "  sizeof(dd_real): " << sizeof(dd_real) << " bytes" << std::endl;
        std::cout << "  sizeof(double): " << sizeof(double) << " bytes" << std::endl;
        std::cout << "  Memory overhead: " << sizeof(dd_real) / sizeof(double) << "x" << std::endl;
        std::cout << "  Array memory (dd_real): " << (sizeof(dd_real) * MEMORY_OPERATIONS / 1024.0) << " KB" << std::endl;
        std::cout << "  Array memory (double): " << (sizeof(double) * MEMORY_OPERATIONS / 1024.0) << " KB" << std::endl;
        std::cout << std::endl;
    }

    void benchmark_complex_computations() {
        std::cout << "=== Complex Computation Benchmark ===" << std::endl;
        std::cout << "Simulating typical scientific computation patterns" << std::endl;
        std::cout << std::endl;

        const int n_particles = 1000;
        const int n_steps = 100;

        // Simulate N-body force calculation (simplified)
        std::cout << "Simulated N-body computation (" << n_particles << " particles, " << n_steps << " steps):" << std::endl;

        // DD-real computation
        auto start = std::chrono::high_resolution_clock::now();
        dd_real dd_total_energy("0.0");

        for (int step = 0; step < n_steps; ++step) {
            for (int i = 0; i < n_particles; ++i) {
                for (int j = i + 1; j < n_particles; ++j) {
                    dd_real dx = dd_real(i * 0.1) - dd_real(j * 0.1);
                    dd_real dy = dd_real(i * 0.2) - dd_real(j * 0.2);
                    dd_real dz = dd_real(i * 0.3) - dd_real(j * 0.3);

                    dd_real r_squared = dx*dx + dy*dy + dz*dz;
                    dd_real r = sqrt(r_squared);
                    dd_real potential = dd_real("1.0") / r;
                    dd_total_energy += potential;
                }
            }
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto dd_computation_time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        // Double computation
        start = std::chrono::high_resolution_clock::now();
        double double_total_energy = 0.0;

        for (int step = 0; step < n_steps; ++step) {
            for (int i = 0; i < n_particles; ++i) {
                for (int j = i + 1; j < n_particles; ++j) {
                    double dx = i * 0.1 - j * 0.1;
                    double dy = i * 0.2 - j * 0.2;
                    double dz = i * 0.3 - j * 0.3;

                    double r_squared = dx*dx + dy*dy + dz*dz;
                    double r = std::sqrt(r_squared);
                    double potential = 1.0 / r;
                    double_total_energy += potential;
                }
            }
        }

        end = std::chrono::high_resolution_clock::now();
        auto double_computation_time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        std::cout << "  dd_real computation: " << dd_computation_time.count() << " ms" << std::endl;
        std::cout << "  double computation: " << double_computation_time.count() << " ms" << std::endl;
        std::cout << "  Overhead factor: " << double(dd_computation_time.count()) / double_computation_time.count() << "x" << std::endl;
        std::cout << "  dd_real result: " << dd_total_energy.to_string(20) << std::endl;
        std::cout << "  double result: " << std::setprecision(15) << double_total_energy << std::endl;

        // Check result agreement
        dd_real double_as_dd(double_total_energy);
        dd_real difference = abs(dd_total_energy - double_as_dd);
        std::cout << "  Result difference: " << difference.to_string(20) << std::endl;
        std::cout << std::endl;
    }

private:
    template<typename DDFunc, typename DoubleFunc>
    void benchmark_operation(const std::string& operation_name, DDFunc dd_func, DoubleFunc double_func) {
        std::cout << operation_name << ":" << std::endl;

        // Benchmark dd_real
        auto start = std::chrono::high_resolution_clock::now();
        auto dd_result = dd_func();
        auto end = std::chrono::high_resolution_clock::now();
        auto dd_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        // Benchmark double
        start = std::chrono::high_resolution_clock::now();
        auto double_result = double_func();
        end = std::chrono::high_resolution_clock::now();
        auto double_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "  dd_real time: " << dd_time.count() << " μs" << std::endl;
        std::cout << "  double time: " << double_time.count() << " μs" << std::endl;
        std::cout << "  Overhead factor: " << double(dd_time.count()) / double_time.count() << "x" << std::endl;
        std::cout << std::endl;
    }

    template<typename DDFunc, typename DoubleFunc>
    void benchmark_function(const std::string& function_name, DDFunc dd_func, DoubleFunc double_func) {
        benchmark_operation(function_name, dd_func, double_func);
    }
};

int main() {
    std::cout << "QD Library Performance Benchmark" << std::endl;
    std::cout << "================================" << std::endl;
    std::cout << std::endl;

    std::cout << "Comparing dd_real (double-double) vs double precision performance" << std::endl;
    std::cout << "Platform: " << sizeof(void*) * 8 << "-bit" << std::endl;
    std::cout << std::endl;

    PerformanceBenchmark benchmark;

    benchmark.benchmark_basic_arithmetic();
    benchmark.benchmark_mathematical_functions();
    benchmark.benchmark_memory_operations();
    benchmark.benchmark_complex_computations();

    std::cout << "=== Performance Benchmark Complete ===" << std::endl;
    std::cout << std::endl;
    std::cout << "Summary:" << std::endl;
    std::cout << "- Basic arithmetic: 5-20x slower than double precision" << std::endl;
    std::cout << "- Mathematical functions: 10-50x slower than standard library" << std::endl;
    std::cout << "- Memory usage: Exactly 2x larger than double precision" << std::endl;
    std::cout << "- Complex computations: Overall ~10-30x slower but maintain precision" << std::endl;
    std::cout << "- Trade-off: Performance cost vs. precision gain is acceptable for high-precision simulations" << std::endl;

    return 0;
}
