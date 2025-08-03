#include <iostream>
#include <iomanip>
#include <qd/dd_real.h>

int main() {
    // Define Pi to high precision using dd_real constructor
    dd_real pi = "3.1415926535897932384626433832795028841971693993751";

    // Set output format to fixed decimal notation with high precision
    std::cout << std::fixed << std::setprecision(35);
    std::cout << "QD Pi: " << pi << std::endl;

    // Show the precision we achieved
    std::cout << "\nVerification:" << std::endl;
    std::cout << "Expected: 3.14159265358979323846264338327950288..." << std::endl;
    std::cout << "QD shows: " << pi << std::endl;

    // Count significant digits shown
    std::string pi_str = pi.to_string(35);
    std::cout << "String representation: " << pi_str << std::endl;
    std::cout << "Length: " << pi_str.length() << " characters" << std::endl;

    return 0;
}
