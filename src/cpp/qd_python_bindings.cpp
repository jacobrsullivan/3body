/**
 * QD Library Python Bindings
 *
 * High-precision arithmetic Python interface using pybind11.
 * Provides Python access to double-double (dd_real) precision arithmetic.
 */

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <qd/dd_real.h>
#include <sstream>
#include <iomanip>

namespace py = pybind11;

PYBIND11_MODULE(qd_python, m) {
    m.doc() = "QD Library Python bindings for high-precision arithmetic (~31 decimal digits)";

    // dd_real class binding
    py::class_<dd_real>(m, "dd_real", "Double-double precision floating point number (~31 decimal digits)")
        // Constructors
        .def(py::init<>(), "Default constructor (zero)")
        .def(py::init<double>(), py::arg("value"), "Construct from Python float")
        .def(py::init<int>(), py::arg("value"), "Construct from Python int")
        .def(py::init<const char*>(), py::arg("value"), "Construct from string")
        .def(py::init([](const std::string& s) { return dd_real(s.c_str()); }),
             py::arg("value"), "Construct from string")

        // String representation
        .def("__str__", [](const dd_real &a) {
            return a.to_string(31);
        }, "String representation with 31 digits")
        .def("__repr__", [](const dd_real &a) {
            return "dd_real('" + a.to_string(31) + "')";
        }, "Python repr() representation")
        .def("to_string", [](const dd_real &a, int precision) {
            return a.to_string(precision);
        }, py::arg("precision") = 31, "Convert to string with specified precision")

        // Arithmetic operators
        .def(py::self + py::self, "Addition")
        .def(py::self + double(), "Addition with float")
        .def(double() + py::self, "Addition with float (reversed)")
        .def(py::self - py::self, "Subtraction")
        .def(py::self - double(), "Subtraction with float")
        .def(double() - py::self, "Subtraction with float (reversed)")
        .def(py::self * py::self, "Multiplication")
        .def(py::self * double(), "Multiplication with float")
        .def(double() * py::self, "Multiplication with float (reversed)")
        .def(py::self / py::self, "Division")
        .def(py::self / double(), "Division with float")
        .def(double() / py::self, "Division with float (reversed)")

        // Unary operators
        .def(-py::self, "Unary negation")
        .def(+py::self, "Unary plus")

        // In-place operators
        .def(py::self += py::self, "In-place addition")
        .def(py::self += double(), "In-place addition with float")
        .def(py::self -= py::self, "In-place subtraction")
        .def(py::self -= double(), "In-place subtraction with float")
        .def(py::self *= py::self, "In-place multiplication")
        .def(py::self *= double(), "In-place multiplication with float")
        .def(py::self /= py::self, "In-place division")
        .def(py::self /= double(), "In-place division with float")

        // Comparison operators
        .def(py::self == py::self, "Equality comparison")
        .def(py::self == double(), "Equality comparison with float")
        .def(py::self != py::self, "Inequality comparison")
        .def(py::self != double(), "Inequality comparison with float")
        .def(py::self < py::self, "Less than comparison")
        .def(py::self < double(), "Less than comparison with float")
        .def(py::self <= py::self, "Less than or equal comparison")
        .def(py::self <= double(), "Less than or equal comparison with float")
        .def(py::self > py::self, "Greater than comparison")
        .def(py::self > double(), "Greater than comparison with float")
        .def(py::self >= py::self, "Greater than or equal comparison")
        .def(py::self >= double(), "Greater than or equal comparison with float")

        // Power operator
        .def("__pow__", [](const dd_real &a, const dd_real &b) {
            return pow(a, b);
        }, py::arg("exponent"), "Power operator")
        .def("__pow__", [](const dd_real &a, double b) {
            return pow(a, dd_real(b));
        }, py::arg("exponent"), "Power operator with float exponent")
        .def("__pow__", [](const dd_real &a, int b) {
            return pow(a, dd_real(b));
        }, py::arg("exponent"), "Power operator with int exponent")

        // Conversion methods
        .def("__float__", [](const dd_real &a) {
            return to_double(a);
        }, "Convert to Python float")
        .def("__int__", [](const dd_real &a) {
            return static_cast<int>(to_double(a));
        }, "Convert to Python int")
        .def("__bool__", [](const dd_real &a) {
            return !a.is_zero();
        }, "Boolean conversion (True if non-zero)")

        // Special methods
        .def("is_zero", &dd_real::is_zero, "Check if value is zero")
        .def("is_positive", &dd_real::is_positive, "Check if value is positive")
        .def("is_negative", &dd_real::is_negative, "Check if value is negative")

        // Hashing support (for use in sets and dicts)
        .def("__hash__", [](const dd_real &a) {
            return std::hash<double>{}(to_double(a));
        }, "Hash function for dd_real");

    // Mathematical functions
    m.def("abs", [](const dd_real &x) { return abs(x); }, py::arg("x"),
          "Absolute value");
    m.def("sqrt", [](const dd_real &x) { return sqrt(x); }, py::arg("x"),
          "Square root");
    m.def("pow", [](const dd_real &x, const dd_real &y) { return pow(x, y); },
          py::arg("x"), py::arg("y"), "Power function");
    m.def("pow", [](const dd_real &x, double y) { return pow(x, dd_real(y)); },
          py::arg("x"), py::arg("y"), "Power function with float exponent");

    // Trigonometric functions
    m.def("sin", [](const dd_real &x) { return sin(x); }, py::arg("x"),
          "Sine function");
    m.def("cos", [](const dd_real &x) { return cos(x); }, py::arg("x"),
          "Cosine function");
    m.def("tan", [](const dd_real &x) { return tan(x); }, py::arg("x"),
          "Tangent function");
    m.def("asin", [](const dd_real &x) { return asin(x); }, py::arg("x"),
          "Arcsine function");
    m.def("acos", [](const dd_real &x) { return acos(x); }, py::arg("x"),
          "Arccosine function");
    m.def("atan", [](const dd_real &x) { return atan(x); }, py::arg("x"),
          "Arctangent function");
    m.def("atan2", [](const dd_real &y, const dd_real &x) { return atan2(y, x); },
          py::arg("y"), py::arg("x"), "Two-argument arctangent function");

    // Hyperbolic functions
    m.def("sinh", [](const dd_real &x) { return sinh(x); }, py::arg("x"),
          "Hyperbolic sine function");
    m.def("cosh", [](const dd_real &x) { return cosh(x); }, py::arg("x"),
          "Hyperbolic cosine function");
    m.def("tanh", [](const dd_real &x) { return tanh(x); }, py::arg("x"),
          "Hyperbolic tangent function");
    m.def("asinh", [](const dd_real &x) { return asinh(x); }, py::arg("x"),
          "Inverse hyperbolic sine function");
    m.def("acosh", [](const dd_real &x) { return acosh(x); }, py::arg("x"),
          "Inverse hyperbolic cosine function");
    m.def("atanh", [](const dd_real &x) { return atanh(x); }, py::arg("x"),
          "Inverse hyperbolic tangent function");

    // Exponential and logarithmic functions
    m.def("exp", [](const dd_real &x) { return exp(x); }, py::arg("x"),
          "Exponential function (e^x)");
    m.def("log", [](const dd_real &x) { return log(x); }, py::arg("x"),
          "Natural logarithm");
    m.def("log10", [](const dd_real &x) { return log10(x); }, py::arg("x"),
          "Base-10 logarithm");

    // Rounding and remainder functions
    m.def("floor", [](const dd_real &x) { return floor(x); }, py::arg("x"),
          "Floor function (largest integer <= x)");
    m.def("ceil", [](const dd_real &x) { return ceil(x); }, py::arg("x"),
          "Ceiling function (smallest integer >= x)");
    m.def("fmod", [](const dd_real &x, const dd_real &y) { return fmod(x, y); },
          py::arg("x"), py::arg("y"), "Floating-point remainder");

    // Special values and constants
    m.attr("pi") = dd_real::_pi;
    m.attr("e") = dd_real::_e;
    m.attr("log2") = dd_real::_log2;
    m.attr("log10") = dd_real::_log10;

    // Utility functions
    m.def("max", [](const dd_real &x, const dd_real &y) { return max(x, y); },
          py::arg("x"), py::arg("y"), "Maximum of two values");
    m.def("min", [](const dd_real &x, const dd_real &y) { return min(x, y); },
          py::arg("x"), py::arg("y"), "Minimum of two values");

    // Version information
    m.attr("__version__") = "1.0.0";
    m.def("precision_digits", []() { return 31; },
          "Return the approximate number of decimal digits of precision");
}
