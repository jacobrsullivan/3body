/**
 * QD Library Performance Benchmark Suite
 * Measures performance overhead and scalability of double-double arithmetic
 */

#include <iostream>
#include <iomanip>
#include <chrono>
#include <vector>
#include <cmath>
#include <qd/dd_real.h>

class Timer {
private:
    std::chrono::high_resolution_clock::time_point start_time;

public:
    void start() {
        start_time = std::chrono::high_resolution_clock::now();
    }

    double elapsed_ms() {
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
        return duration.count() / 1000.0; // Convert to milliseconds
    }
};

class QDBenchmark {
private:
    static const int SMALL_OPS = 100000;
    static const int MEDIUM_OPS = 1000000;
    static const int LARGE_OPS = 10000000;

    void print_header(const std::string& title) {
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << title << std::endl;
        std::cout << std::string(70, '=') << std::endl;
    }

    void print_result(const std::string& operation, double dd_time, double double_time, int ops) {
        double overhead = dd_time / double_time;
        double dd_ops_per_sec = ops / (dd_time / 1000.0);
        double double_ops_per_sec = ops / (double_time / 1000.0);

        std::cout << std::fixed << std::setprecision(2);
        std::cout << operation << ":" << std::endl;
        std::cout << "  DD time:     " << std::setw(10) << dd_time << " ms  ("
                  << std::scientific << std::setprecision(2) << dd_ops_per_sec << " ops/s)" << std::endl;
        std::cout << "  Double time: " << std::fixed << std::setw(10) << double_time << " ms  ("
                  << std::scientific << std::setprecision(2) << double_ops_per_sec << " ops/s)" << std::endl;
        std::cout << "  Overhead:    " << std::fixed << std::setw(10) << overhead << "x" << std::endl;
    }

public:
    void benchmark_addition() {
        print_header("Addition Benchmark");

        Timer timer;
        const int N = LARGE_OPS;

        // DD addition
        std::vector<dd_real> dd_data(100);
        for (int i = 0; i < 100; ++i) {
            dd_data[i] = dd_real(1.1 + i * 0.001);
        }

        timer.start();
        dd_real dd_sum = dd_real("0.0");
        for (int i = 0; i < N; ++i) {
            dd_sum += dd_data[i % 100];
        }
        double dd_time = timer.elapsed_ms();

        // Double addition
        std::vector<double> double_data(100);
        for (int i = 0; i < 100; ++i) {
            double_data[i] = 1.1 + i * 0.001;
        }

        timer.start();
        double double_sum = 0.0;
        for (int i = 0; i < N; ++i) {
            double_sum += double_data[i % 100];
        }
        double double_time = timer.elapsed_ms();

        print_result("Addition (" + std::to_string(N) + " operations)", dd_time, double_time, N);
    }

    void benchmark_multiplication() {
        print_header("Multiplication Benchmark");

        Timer timer;
        const int N = MEDIUM_OPS;

        // DD multiplication
        dd_real dd_a("1.000000001");
        dd_real dd_b("1.000000002");

        timer.start();
        dd_real dd_product = dd_real("1.0");
        for (int i = 0; i < N; ++i) {
            dd_product = dd_product * dd_a;
            if ((i % 1000) == 0) {
                dd_product = dd_real("1.0"); // Reset to avoid overflow
            }
        }
        double dd_time = timer.elapsed_ms();

        // Double multiplication
        double double_a = 1.000000001;
        double double_b = 1.000000002;

        timer.start();
        double double_product = 1.0;
        for (int i = 0; i < N; ++i) {
            double_product = double_product * double_a;
            if ((i % 1000) == 0) {
                double_product = 1.0; // Reset to avoid overflow
            }
        }
        double double_time = timer.elapsed_ms();

        print_result("Multiplication (" + std::to_string(N) + " operations)", dd_time, double_time, N);
    }

    void benchmark_division() {
        print_header("Division Benchmark");

        Timer timer;
        const int N = MEDIUM_OPS;

        // DD division
        dd_real dd_numerator("1234567.89");
        dd_real dd_denominator("1.234");

        timer.start();
        dd_real dd_quotient;
        for (int i = 0; i < N; ++i) {
            dd_quotient = dd_numerator / (dd_denominator + dd_real(i % 100));
        }
        double dd_time = timer.elapsed_ms();

        // Double division
        double double_numerator = 1234567.89;
        double double_denominator = 1.234;

        timer.start();
        double double_quotient;
        for (int i = 0; i < N; ++i) {
            double_quotient = double_numerator / (double_denominator + (i % 100));
        }
        double double_time = timer.elapsed_ms();

        print_result("Division (" + std::to_string(N) + " operations)", dd_time, double_time, N);
    }

    void benchmark_sqrt() {
        print_header("Square Root Benchmark");

        Timer timer;
        const int N = MEDIUM_OPS;

        // DD sqrt
        timer.start();
        dd_real dd_result;
        for (int i = 1; i < N; ++i) {
            dd_result = sqrt(dd_real(i));
        }
        double dd_time = timer.elapsed_ms();

        // Double sqrt
        timer.start();
        double double_result;
        for (int i = 1; i < N; ++i) {
            double_result = std::sqrt(double(i));
        }
        double double_time = timer.elapsed_ms();

        print_result("Square root (" + std::to_string(N) + " operations)", dd_time, double_time, N);
    }

    void benchmark_sin() {
        print_header("Sine Function Benchmark");

        Timer timer;
        const int N = SMALL_OPS;

        // DD sin
        timer.start();
        dd_real dd_result;
        for (int i = 0; i < N; ++i) {
            dd_real x = dd_real(i) / dd_real(N) * dd_real::_pi;
            dd_result = sin(x);
        }
        double dd_time = timer.elapsed_ms();

        // Double sin
        timer.start();
        double double_result;
        for (int i = 0; i < N; ++i) {
            double x = double(i) / N * M_PI;
            double_result = std::sin(x);
        }
        double double_time = timer.elapsed_ms();

        print_result("Sine function (" + std::to_string(N) + " operations)", dd_time, double_time, N);
    }

    void benchmark_exp() {
        print_header("Exponential Function Benchmark");

        Timer timer;
        const int N = SMALL_OPS;

        // DD exp
        timer.start();
        dd_real dd_result;
        for (int i = 0; i < N; ++i) {
            dd_real x = dd_real(i) / dd_real(N * 10); // Keep argument small
            dd_result = exp(x);
        }
        double dd_time = timer.elapsed_ms();

        // Double exp
        timer.start();
        double double_result;
        for (int i = 0; i < N; ++i) {
            double x = double(i) / (N * 10);
            double_result = std::exp(x);
        }
        double double_time = timer.elapsed_ms();

        print_result("Exponential function (" + std::to_string(N) + " operations)", dd_time, double_time, N);
    }

    void benchmark_mixed_operations() {
        print_header("Mixed Operations Benchmark (Orbital Mechanics Simulation)");

        Timer timer;
        const int N = SMALL_OPS;

        // Simulate typical orbital mechanics computation: energy = v²/2 - μ/r
        // DD version
        timer.start();
        dd_real dd_energy_sum("0.0");
        for (int i = 1; i < N; ++i) {
            dd_real r = dd_real(1.0) + dd_real(i) / dd_real(N);
            dd_real v = sqrt(dd_real("2.0") / r); // Circular velocity
            dd_real energy = v * v / dd_real("2.0") - dd_real("1.0") / r;
            dd_energy_sum += energy;
        }
        double dd_time = timer.elapsed_ms();

        // Double version
        timer.start();
        double double_energy_sum = 0.0;
        for (int i = 1; i < N; ++i) {
            double r = 1.0 + double(i) / N;
            double v = std::sqrt(2.0 / r);
            double energy = v * v / 2.0 - 1.0 / r;
            double_energy_sum += energy;
        }
        double double_time = timer.elapsed_ms();

        print_result("Mixed operations (" + std::to_string(N) + " iterations)", dd_time, double_time, N);
    }

    void benchmark_memory_usage() {
        print_header("Memory Usage Analysis");

        std::cout << "Size of types:" << std::endl;
        std::cout << "  double:   " << sizeof(double) << " bytes" << std::endl;
        std::cout << "  dd_real:  " << sizeof(dd_real) << " bytes" << std::endl;
        std::cout << "  overhead: " << sizeof(dd_real) / sizeof(double) << "x" << std::endl;

        const int ARRAY_SIZE = 1000000;
        std::cout << "\nMemory for " << ARRAY_SIZE << " elements:" << std::endl;
        std::cout << "  double:   " << (ARRAY_SIZE * sizeof(double)) / (1024.0 * 1024.0) << " MB" << std::endl;
        std::cout << "  dd_real:  " << (ARRAY_SIZE * sizeof(dd_real)) / (1024.0 * 1024.0) << " MB" << std::endl;
    }

    void run_all_benchmarks() {
        benchmark_addition();
        benchmark_multiplication();
        benchmark_division();
        benchmark_sqrt();
        benchmark_sin();
        benchmark_exp();
        benchmark_mixed_operations();
        benchmark_memory_usage();
    }
};

int main() {
    std::cout << "QD Library Performance Benchmark Suite" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "Measuring performance overhead of double-double arithmetic" << std::endl;
    std::cout << "Platform: " << sizeof(void*) * 8 << "-bit" << std::endl;

    QDBenchmark benchmark;
    benchmark.run_all_benchmarks();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "Benchmark Complete" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    return 0;
}
