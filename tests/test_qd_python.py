#!/usr/bin/env python3
"""
Comprehensive test suite for QD Python bindings.
Tests high-precision arithmetic operations and mathematical functions.
"""

import pytest
import sys
import os

# Add the project root to the path to import qd_python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qd_python as qd  # noqa: E402


class TestDDRealBasics:
    """Test basic dd_real operations and properties."""

    def test_construction(self):
        """Test various dd_real construction methods."""
        # Default constructor
        zero = qd.dd_real()
        assert zero.is_zero()

        # From double
        x = qd.dd_real(3.14159)
        assert abs(float(x) - 3.14159) < 1e-10

        # From int
        five = qd.dd_real(5)
        assert five == qd.dd_real(5.0)
        assert int(five) == 5

        # From string (high precision)
        pi_str = "3.1415926535897932384626433832795028841971693993751"
        pi_hp = qd.dd_real(pi_str)
        pi_repr = pi_hp.to_string(50)
        assert pi_repr.startswith("3.14159265358979323846264338327950")

    def test_string_conversion(self):
        """Test string conversion and precision."""
        x = qd.dd_real("1.23456789012345678901234567890123456789")

        # Test different precision levels
        s10 = x.to_string(10)
        s20 = x.to_string(20)
        s31 = x.to_string(31)

        assert (
            len(s10.replace(".", "").replace("e", "").replace("+", "").replace("-", ""))
            >= 10
        )
        assert (
            len(s20.replace(".", "").replace("e", "").replace("+", "").replace("-", ""))
            >= 15
        )
        assert (
            len(s31.replace(".", "").replace("e", "").replace("+", "").replace("-", ""))
            >= 25
        )

        # Test repr
        repr_str = repr(x)
        assert repr_str.startswith("dd_real(")
        assert repr_str.endswith(")")

    def test_boolean_conversion(self):
        """Test boolean conversion."""
        zero = qd.dd_real(0)
        nonzero = qd.dd_real(1.5)

        assert not bool(zero)
        assert bool(nonzero)

        # Test is_zero, is_one methods
        assert zero.is_zero()
        assert not nonzero.is_zero()

        one = qd.dd_real(1)
        assert one.is_one()
        assert not zero.is_one()


class TestArithmetic:
    """Test arithmetic operations."""

    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        a = qd.dd_real("1.5")
        b = qd.dd_real("2.5")

        # Addition
        result = a + b
        expected = qd.dd_real("4.0")
        assert abs(result - expected) < qd.dd_real("1e-30")

        # Subtraction
        result = b - a
        expected = qd.dd_real("1.0")
        assert abs(result - expected) < qd.dd_real("1e-30")

        # Multiplication
        result = a * b
        expected = qd.dd_real("3.75")
        assert abs(result - expected) < qd.dd_real("1e-30")

        # Division
        result = b / a
        expected = qd.dd_real("1.6666666666666666666666666666666667")
        assert abs(result - expected) < qd.dd_real("1e-28")

    def test_mixed_type_arithmetic(self):
        """Test arithmetic with Python built-in types."""
        x = qd.dd_real("2.5")

        # With integers
        assert x + 2 == qd.dd_real("4.5")
        assert 2 + x == qd.dd_real("4.5")
        assert x * 3 == qd.dd_real("7.5")
        assert 3 * x == qd.dd_real("7.5")

        # With floats
        assert x + 1.5 == qd.dd_real("4.0")
        assert 1.5 + x == qd.dd_real("4.0")
        assert x / 2.0 == qd.dd_real("1.25")

    def test_in_place_operations(self):
        """Test in-place arithmetic operations."""
        x = qd.dd_real("5.0")

        x += qd.dd_real("3.0")
        assert x == qd.dd_real("8.0")

        x -= qd.dd_real("2.0")
        assert x == qd.dd_real("6.0")

        x *= qd.dd_real("2.0")
        assert x == qd.dd_real("12.0")

        x /= qd.dd_real("3.0")
        assert x == qd.dd_real("4.0")

    def test_unary_operations(self):
        """Test unary operations."""
        x = qd.dd_real("3.5")

        # Negation
        neg_x = -x
        assert neg_x == qd.dd_real("-3.5")

        # Positive (identity)
        pos_x = +x
        assert pos_x == x

        # Absolute value
        neg_val = qd.dd_real("-2.5")
        assert abs(neg_val) == qd.dd_real("2.5")
        assert qd.abs(neg_val) == qd.dd_real("2.5")

    def test_power_operations(self):
        """Test power operations."""
        base = qd.dd_real("2.0")

        # Integer powers
        assert base**3 == qd.dd_real("8.0")
        assert base**0 == qd.dd_real("1.0")

        # Floating point powers
        assert abs(base**0.5 - qd.sqrt(base)) < qd.dd_real("1e-30")

        # qd.pow function
        result = qd.pow(base, qd.dd_real("3.0"))
        assert result == qd.dd_real("8.0")


class TestComparisons:
    """Test comparison operations."""

    def test_equality(self):
        """Test equality comparisons."""
        a = qd.dd_real("3.14159")
        b = qd.dd_real("3.14159")
        c = qd.dd_real("2.71828")

        assert a == b
        assert not (a == c)
        assert a != c
        assert not (a != b)

    def test_ordering(self):
        """Test ordering comparisons."""
        small = qd.dd_real("1.0")
        large = qd.dd_real("2.0")

        assert small < large
        assert small <= large
        assert small <= small
        assert large > small
        assert large >= small
        assert large >= large

        # Mixed type comparisons
        assert small < 1.5
        assert small <= 1.0
        assert large > 1.5
        assert large >= 2.0


class TestMathematicalFunctions:
    """Test mathematical functions."""

    def test_trigonometric_functions(self):
        """Test trigonometric functions."""
        # Test sin(π/6) = 0.5
        pi_over_6 = qd.pi / qd.dd_real("6.0")
        sin_result = qd.sin(pi_over_6)
        expected = qd.dd_real("0.5")
        assert abs(sin_result - expected) < qd.dd_real("1e-30")

        # Test cos(π/3) = 0.5
        pi_over_3 = qd.pi / qd.dd_real("3.0")
        cos_result = qd.cos(pi_over_3)
        assert abs(cos_result - expected) < qd.dd_real("1e-30")

        # Test sin²(x) + cos²(x) = 1
        x = qd.dd_real("0.7")
        sin_x = qd.sin(x)
        cos_x = qd.cos(x)
        identity = sin_x * sin_x + cos_x * cos_x
        assert abs(identity - qd.dd_real("1.0")) < qd.dd_real("1e-30")

        # Test tan function
        tan_result = qd.tan(qd.pi / qd.dd_real("4.0"))
        assert abs(tan_result - qd.dd_real("1.0")) < qd.dd_real("1e-30")

    def test_inverse_trigonometric_functions(self):
        """Test inverse trigonometric functions."""
        # Test arcsin(0.5) = π/6
        arcsin_half = qd.asin(qd.dd_real("0.5"))
        pi_over_6 = qd.pi / qd.dd_real("6.0")
        assert abs(arcsin_half - pi_over_6) < qd.dd_real("1e-30")

        # Test arccos(0.5) = π/3
        arccos_half = qd.acos(qd.dd_real("0.5"))
        pi_over_3 = qd.pi / qd.dd_real("3.0")
        assert abs(arccos_half - pi_over_3) < qd.dd_real("1e-30")

        # Test arctan(1) = π/4
        arctan_one = qd.atan(qd.dd_real("1.0"))
        pi_over_4 = qd.pi / qd.dd_real("4.0")
        assert abs(arctan_one - pi_over_4) < qd.dd_real("1e-30")

        # Test inverse relationships
        x = qd.dd_real("0.7")
        assert abs(qd.sin(qd.asin(x)) - x) < qd.dd_real("1e-30")
        assert abs(qd.cos(qd.acos(x)) - x) < qd.dd_real("1e-30")
        assert abs(qd.tan(qd.atan(x)) - x) < qd.dd_real("1e-30")

    def test_exponential_logarithmic_functions(self):
        """Test exponential and logarithmic functions."""
        # Test exp(1) = e
        exp_one = qd.exp(qd.dd_real("1.0"))
        assert abs(exp_one - qd.e) < qd.dd_real("1e-30")

        # Test log(e) = 1
        log_e = qd.log(qd.e)
        assert abs(log_e - qd.dd_real("1.0")) < qd.dd_real("1e-30")

        # Test exp(log(x)) = x
        x = qd.dd_real("2.5")
        identity_result = qd.exp(qd.log(x))
        assert abs(identity_result - x) < qd.dd_real("1e-28")

        # Test log10 and log2
        ten = qd.dd_real("10.0")
        two = qd.dd_real("2.0")

        assert abs(qd.log10(ten) - qd.dd_real("1.0")) < qd.dd_real("1e-30")
        assert abs(qd.log2(two) - qd.dd_real("1.0")) < qd.dd_real("1e-30")

    def test_hyperbolic_functions(self):
        """Test hyperbolic functions."""
        x = qd.dd_real("0.5")

        # Test cosh²(x) - sinh²(x) = 1
        sinh_x = qd.sinh(x)
        cosh_x = qd.cosh(x)
        identity = cosh_x * cosh_x - sinh_x * sinh_x
        assert abs(identity - qd.dd_real("1.0")) < qd.dd_real("1e-30")

        # Test tanh(x) = sinh(x)/cosh(x)
        tanh_x = qd.tanh(x)
        tanh_calc = sinh_x / cosh_x
        assert abs(tanh_x - tanh_calc) < qd.dd_real("1e-30")

    def test_power_and_root_functions(self):
        """Test power and root functions."""
        # Test sqrt(4) = 2
        sqrt_four = qd.sqrt(qd.dd_real("4.0"))
        assert abs(sqrt_four - qd.dd_real("2.0")) < qd.dd_real("1e-30")

        # Test sqrt(2) * sqrt(2) = 2
        sqrt_two = qd.sqrt(qd.dd_real("2.0"))
        product = sqrt_two * sqrt_two
        assert abs(product - qd.dd_real("2.0")) < qd.dd_real("1e-30")

        # Test power function
        base = qd.dd_real("3.0")
        exp = qd.dd_real("4.0")
        result = qd.pow(base, exp)
        expected = qd.dd_real("81.0")
        assert abs(result - expected) < qd.dd_real("1e-28")

    def test_rounding_functions(self):
        """Test rounding functions."""
        x = qd.dd_real("3.7")
        y = qd.dd_real("-2.3")

        # Floor function
        assert qd.floor(x) == qd.dd_real("3.0")
        assert qd.floor(y) == qd.dd_real("-3.0")

        # Ceiling function
        assert qd.ceil(x) == qd.dd_real("4.0")
        assert qd.ceil(y) == qd.dd_real("-2.0")

        # Round function
        assert qd.round(x) == qd.dd_real("4.0")
        assert qd.round(y) == qd.dd_real("-2.0")


class TestConstants:
    """Test mathematical constants."""

    def test_pi_precision(self):
        """Test π constant precision."""
        pi_str = qd.pi.to_string(35)
        expected_start = "3.14159265358979323846264338327950"
        assert pi_str.startswith(expected_start)

    def test_e_precision(self):
        """Test e constant precision."""
        e_str = qd.e.to_string(35)
        expected_start = "2.71828182845904523536028747135266"
        assert e_str.startswith(expected_start)

    def test_constants_relationships(self):
        """Test relationships between constants."""
        # Test e^(iπ) + 1 = 0 components: cos(π) = -1, sin(π) = 0
        cos_pi = qd.cos(qd.pi)
        sin_pi = qd.sin(qd.pi)

        assert abs(cos_pi - qd.dd_real("-1.0")) < qd.dd_real("1e-30")
        assert abs(sin_pi) < qd.dd_real("1e-30")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_division_by_zero(self):
        """Test division by zero handling."""
        a = qd.dd_real("1.0")
        zero = qd.dd_real("0.0")

        with pytest.raises(Exception):  # Should raise domain_error
            _ = a / zero

    def test_invalid_domain_operations(self):
        """Test operations with invalid domains."""
        # Square root of negative number
        with pytest.raises(Exception):
            qd.sqrt(qd.dd_real("-1.0"))

        # Logarithm of non-positive number
        with pytest.raises(Exception):
            qd.log(qd.dd_real("0.0"))

        with pytest.raises(Exception):
            qd.log(qd.dd_real("-1.0"))

        # Arcsin/arccos of value outside [-1, 1]
        with pytest.raises(Exception):
            qd.asin(qd.dd_real("1.5"))

        with pytest.raises(Exception):
            qd.acos(qd.dd_real("-1.5"))


class TestPrecision:
    """Test high-precision capabilities."""

    def test_precision_advantage(self):
        """Test precision advantage over standard float."""
        # Test calculation that loses precision in double arithmetic
        # 1 + 1e-16 should be exactly representable in dd_real but not in double

        one = qd.dd_real("1.0")
        small = qd.dd_real("1e-20")  # Much smaller than double precision

        result = one + small
        difference = result - one

        # Should be able to recover the small number exactly
        error = abs(difference - small)
        relative_error = error / small

        # This should be much better than what's possible with double precision
        # dd_real provides ~31 digits, so relative error should be < 1e-15
        assert relative_error < qd.dd_real("1e-15")

    def test_iterative_precision(self):
        """Test precision in iterative calculations."""
        # Newton's method for sqrt(2)
        x = qd.dd_real("1.5")  # Initial guess
        two = qd.dd_real("2.0")
        target = qd.sqrt(two)

        # One iteration: x_new = (x + 2/x) / 2
        x_new = (x + two / x) / two
        error = abs(x_new - target)

        # Should be reasonable after one iteration (Newton convergence is quadratic)
        assert error < qd.dd_real("1e-2")

        # Another iteration should be much more accurate (quadratic convergence)
        x_newer = (x_new + two / x_new) / two
        error_new = abs(x_newer - target)
        assert error_new < qd.dd_real("1e-5")

        # Third iteration should reach excellent precision
        x_final = (x_newer + two / x_newer) / two
        error_final = abs(x_final - target)
        assert error_final < qd.dd_real("1e-10")


class TestUtilityFunctions:
    """Test utility and informational functions."""

    def test_precision_info(self):
        """Test precision information functions."""
        # Test precision_digits function
        digits = qd.precision_digits()
        assert digits == 31

        # Test machine_epsilon
        eps = qd.machine_epsilon()
        assert eps > qd.dd_real("0.0")
        assert eps < qd.dd_real("1e-30")

    def test_version_info(self):
        """Test version information."""
        # These should be accessible without errors
        version = qd.__version__
        qd_version = qd.__qd_version__

        assert isinstance(version, str)
        assert isinstance(qd_version, str)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
