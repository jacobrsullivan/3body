#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <qd/dd_real.h>
#include <sstream>
#include <stdexcept>

namespace py = pybind11;

// Helper function for safe division with error checking
dd_real safe_divide(const dd_real& a, const dd_real& b) {
    if (b.is_zero()) {
        throw std::domain_error("Division by zero");
    }
    return a / b;
}

// Helper function for safe logarithm
dd_real safe_log(const dd_real& x) {
    if (x <= dd_real("0.0")) {
        throw std::domain_error("Logarithm of non-positive number");
    }
    return log(x);
}

// Helper function for safe square root
dd_real safe_sqrt(const dd_real& x) {
    if (x < dd_real("0.0")) {
        throw std::domain_error("Square root of negative number");
    }
    return sqrt(x);
}

// Helper function for safe arcsin/arccos
dd_real safe_asin(const dd_real& x) {
    if (abs(x) > dd_real("1.0")) {
        throw std::domain_error("arcsin domain error: |x| > 1");
    }
    return asin(x);
}

dd_real safe_acos(const dd_real& x) {
    if (abs(x) > dd_real("1.0")) {
        throw std::domain_error("arccos domain error: |x| > 1");
    }
    return acos(x);
}

// Custom string representation with configurable precision
std::string dd_real_repr(const dd_real& x, int precision = 31) {
    std::ostringstream oss;
    oss << "dd_real('" << x.to_string(precision) << "')";
    return oss.str();
}

std::string dd_real_str(const dd_real& x, int precision = 15) {
    return x.to_string(precision);
}

PYBIND11_MODULE(qd_python, m) {
    m.doc() = "QD Library Python bindings for high-precision arithmetic";

    // dd_real class bindings
    py::class_<dd_real>(m, "dd_real", "Double-double precision floating point number (~31 decimal digits)")
        // Constructors
        .def(py::init<>(), "Default constructor (zero)")
        .def(py::init<double>(), "Constructor from double", py::arg("value"))
        .def(py::init<int>(), "Constructor from int", py::arg("value"))
        .def(py::init<const char*>(), "Constructor from string", py::arg("value"))
        .def(py::init<double, double>(), "Constructor from high and low double",
             py::arg("hi"), py::arg("lo"))

        // String representation
        .def("__str__", [](const dd_real& x) { return dd_real_str(x); })
        .def("__repr__", [](const dd_real& x) { return dd_real_repr(x); })
        .def("to_string", [](const dd_real& x, int precision) {
            return x.to_string(precision);
        }, "Convert to string with specified precision", py::arg("precision") = 31)

        // Arithmetic operators
        .def(py::self + py::self)
        .def(py::self + double())
        .def(double() + py::self)
        .def(py::self + int())
        .def(int() + py::self)

        .def(py::self - py::self)
        .def(py::self - double())
        .def(double() - py::self)
        .def(py::self - int())
        .def(int() - py::self)

        .def(py::self * py::self)
        .def(py::self * double())
        .def(double() * py::self)
        .def(py::self * int())
        .def(int() * py::self)

        .def("__truediv__", [](const dd_real& a, const dd_real& b) { return safe_divide(a, b); })
        .def("__truediv__", [](const dd_real& a, double b) { return safe_divide(a, dd_real(b)); })
        .def("__rtruediv__", [](const dd_real& a, double b) { return safe_divide(dd_real(b), a); })
        .def("__truediv__", [](const dd_real& a, int b) { return safe_divide(a, dd_real(b)); })
        .def("__rtruediv__", [](const dd_real& a, int b) { return safe_divide(dd_real(b), a); })

        .def(py::self += py::self)
        .def(py::self -= py::self)
        .def(py::self *= py::self)
        .def("__itruediv__", [](dd_real& a, const dd_real& b) { a = safe_divide(a, b); return a; })

        // Unary operators
        .def("__neg__", [](const dd_real& x) { return -x; })
        .def("__pos__", [](const dd_real& x) { return x; })

        // Comparison operators
        .def(py::self == py::self)
        .def(py::self != py::self)
        .def(py::self < py::self)
        .def(py::self <= py::self)
        .def(py::self > py::self)
        .def(py::self >= py::self)

        .def(py::self == double())
        .def(py::self != double())
        .def(py::self < double())
        .def(py::self <= double())
        .def(py::self > double())
        .def(py::self >= double())

        // Power function
        .def("__pow__", [](const dd_real& base, const dd_real& exp) { return pow(base, exp); })
        .def("__pow__", [](const dd_real& base, double exp) { return pow(base, dd_real(exp)); })
        .def("__pow__", [](const dd_real& base, int exp) { return pow(base, dd_real(exp)); })

        // Absolute value
        .def("__abs__", [](const dd_real& x) { return abs(x); })

        // Conversion to Python types
        .def("__float__", [](const dd_real& x) { return x.x[0]; }, "Convert to Python float (loses precision)")
        .def("__int__", [](const dd_real& x) { return static_cast<int>(x.x[0]); }, "Convert to Python int")
        .def("__bool__", [](const dd_real& x) { return !x.is_zero(); }, "Boolean conversion")

        // Utility methods
        .def("is_zero", &dd_real::is_zero, "Check if value is zero")
        .def("is_one", &dd_real::is_one, "Check if value is one")
        .def("is_positive", &dd_real::is_positive, "Check if value is positive")
        .def("is_negative", &dd_real::is_negative, "Check if value is negative")

        // Hash support for use in sets/dicts
        .def("__hash__", [](const dd_real& x) {
            return std::hash<std::string>{}(x.to_string(31));
        });

    // Mathematical functions
    m.def("abs", [](const dd_real& x) { return abs(x); }, "Absolute value");
    m.def("fabs", [](const dd_real& x) { return abs(x); }, "Absolute value (alias)");

    // Trigonometric functions
    m.def("sin", [](const dd_real& x) { return sin(x); }, "Sine function");
    m.def("cos", [](const dd_real& x) { return cos(x); }, "Cosine function");
    m.def("tan", [](const dd_real& x) { return tan(x); }, "Tangent function");

    m.def("asin", safe_asin, "Arcsine function");
    m.def("acos", safe_acos, "Arccosine function");
    m.def("atan", [](const dd_real& x) { return atan(x); }, "Arctangent function");
    m.def("atan2", [](const dd_real& y, const dd_real& x) { return atan2(y, x); }, "Two-argument arctangent");

    // Hyperbolic functions
    m.def("sinh", [](const dd_real& x) { return sinh(x); }, "Hyperbolic sine");
    m.def("cosh", [](const dd_real& x) { return cosh(x); }, "Hyperbolic cosine");
    m.def("tanh", [](const dd_real& x) { return tanh(x); }, "Hyperbolic tangent");

    // Exponential and logarithmic functions
    m.def("exp", [](const dd_real& x) { return exp(x); }, "Exponential function");
    m.def("log", safe_log, "Natural logarithm");
    m.def("log10", [](const dd_real& x) { return log10(x); }, "Base-10 logarithm");
    m.def("log2", [](const dd_real& x) { return safe_log(x) / log(dd_real("2.0")); }, "Base-2 logarithm");

    // Power and root functions
    m.def("pow", [](const dd_real& base, const dd_real& exp) { return pow(base, exp); }, "Power function");
    m.def("sqrt", safe_sqrt, "Square root");

    // Rounding functions
    m.def("floor", [](const dd_real& x) { return floor(x); }, "Floor function");
    m.def("ceil", [](const dd_real& x) { return ceil(x); }, "Ceiling function");
    m.def("round", [](const dd_real& x) { return nint(x); }, "Round to nearest integer");

    // Mathematical constants
    m.attr("pi") = dd_real::_pi;
    m.attr("e") = dd_real::_e;

    // Additional constants
    m.attr("nan") = dd_real::_nan;
    m.attr("inf") = dd_real::_inf;

    // Utility functions for precision and performance info
    m.def("precision_digits", []() { return 31; }, "Get approximate decimal digits of precision");
    m.def("machine_epsilon", []() { return dd_real::_eps; }, "Get machine epsilon");

    // Version information
    m.attr("__version__") = "1.0.0";
    m.attr("__qd_version__") = "2.3.24";
}
