#include <iostream>
#include <qd/dd_real.h>

int main() {
    dd_real pi = dd_real::_pi;
    dd_real result = sin(pi / dd_real("2.0"));
    std::cout << "sin(π/2) = " << result.to_string(10) << std::endl;
    return 0;
}
