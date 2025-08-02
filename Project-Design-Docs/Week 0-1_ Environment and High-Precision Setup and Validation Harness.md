### **Week 0-1: Environment, High-Precision Setup and Validation Harness**

Total Effort: 5 Days (1 FTE)  
Goal: Establish a functional, version-controlled, and reproducible software environment capable of high-precision arithmetic, validated by a standardized benchmark test.

---

#### **Day 1: Foundational Setup, Version Control, and Environment Definition**

**Objective:** Establish the project structure, initialize version control, and define the software environment.

**1.1. Version Control (Git/GitHub)**

* **Concept:** Git is the system we use to track every change in the code. This is essential for collaboration, debugging, and scientific reproducibility. GitHub/GitLab is the remote server hosting the repository.  
* **Action Items:**  
  1. Ensure Git is installed (git \--version).  
  2. Create a new repository on GitHub/GitLab (e.g., 3BP-Integrability-WP1).  
  3. Clone the repository locally: git clone \[URL\].  
  4. Navigate into the directory: cd 3BP-Integrability-WP1.

**1.2. Project Structure and .gitignore**

* **Concept:** A standardized directory structure keeps the project organized. The .gitignore file tells Git which files *not* to track (e.g., large data files, temporary build files).  
* **Action Items:**  
  1. Create the directory structure:  
     Bash  
     mkdir \-p src/cpp src/python tests notebooks docs

  2. Create a .gitignore file in the root directory. Use a standard template for Python and C++ (e.g., from gitignore.io).  
  3. Commit the initial structure: git add . ; git commit \-m "Initial project structure".

**1.3. Environment Management (Mamba/Conda)**

* **Concept:** To ensure the project runs identically on different computers, we use isolated environments. Mamba (a faster version of Conda) manages this.  
* **Action Items:**  
  1. Install Mambaforge (or Miniconda).

**1.4. Defining the Environment (environment.yml)**

* **Concept:** We define the environment in a configuration file. **Crucially**, we must ensure that Conda provides the C++ and Fortran compilers, rather than relying on the operating system's defaults. This guarantees binary compatibility and reproducibility.  
* **Action Items:**  
  1. Create environment.yml in the project root:

YAML  
name: wp1\_env  
channels:  
  \- conda-forge  
dependencies:  
  \- python=3.11  
  \- poetry  
  \# Crucial: Ensures consistent C/C++/Fortran compilers across systems  
  \- compilers  
  \# Build tools required for C++ libraries  
  \- cmake  
  \- make  
  \# Required for bridging Python and C++  
  \- pybind11  
---

#### **Day 2: Reproducible Environment Creation and Code Quality**

**Objective:** Instantiate the isolated environment, lock dependencies, and enforce code quality standards.

**2.1. Instantiating the Environment**

* **Action Items:**  
  1. Create the environment from the definition file:  
     Bash  
     mamba env create \-f environment.yml  
     mamba activate wp1\_env

  2. *Verification:* Check that the Conda compilers are active: which g++ should point to a path inside the Mamba environment.

**2.2. Deterministic Python Dependencies (Poetry)**

* **Concept:** While Mamba manages the base tools, Poetry manages the Python packages (Numpy, Scipy, etc.). Poetry creates a "lock file" (poetry.lock) recording the *exact* version of every library, guaranteeing perfect reproducibility.  
* **Action Items:**  
  1. Initialize Poetry: poetry init (follow the prompts).  
  2. Install the core scientific stack:  
     Bash  
     poetry add numpy scipy matplotlib jupyterlab pytest numba h5py pyarrow rebound

     *(Note: h5py for HDF5; pyarrow for Parquet; rebound is the baseline integrator).*  
  3. Commit pyproject.toml and poetry.lock to Git.

**2.3. Code Quality Tooling (Pre-commit)**

* **Concept:** We use tools like Black (formatter) and Flake8 (linter/error checker) to enforce consistent code style. pre-commit automatically runs these tools before any code is committed.  
* **Action Items:**  
  1. Install development dependencies: poetry add \--group dev black flake8 pre-commit.  
  2. Create a .pre-commit-config.yaml file (use standard configurations for Black and Flake8).  
  3. Install the hooks: poetry run pre-commit install.

---

#### **Day 3: High-Precision Arithmetic Setup (The QD Library)**

**Objective:** Compile and verify the library required for calculations beyond standard precision.

**3.1. Understanding Precision**

* **Concept:** Standard "double precision" (≈16 digits) is insufficient for our 10−25 error target. We use **Double-Double (DD)** arithmetic (≈31 digits), implemented via the C++ **QD Library**.

**3.2. Compiling and Installing the QD Library**

* **Concept:** We must compile QD using the Conda-provided compilers and install it *inside* the active Conda environment ($CONDA\_PREFIX). This keeps the environment isolated and portable.  
* **Action Items:**  
  1. Download the QD library source code (e.g., from D.H. Bailey's website).  
  2. Extract the source code (e.g., into a temporary build\_external/ directory).  
  3. Configure, compile, and install:  
     Bash  
     cd build\_external/qd-X.Y.Z  
     \# Ensure Conda compilers are used (they should be, as the env is active)  
     export CXX=$(which g++)  
     export CC=$(which gcc)  
     \# Configure: Install into the Conda environment prefix, optimize for CPU  
     ./configure \--prefix=$CONDA\_PREFIX \--enable-cxx CXXFLAGS="-O3 \-march=native"  
     make  
     make install  
     cd ../../

**3.3. Verifying the QD Library**

* **Concept:** A minimal C++ program confirms the library is correctly installed and linked.  
* **Action Items:**  
  1. Create src/cpp/verify\_qd.cpp:

  C++  
     \#**include** \<iostream\>  
     \#**include** \<qd/dd\_real.h\>

     int main() {  
         // Define Pi to high precision  
         dd\_real pi \= "3.1415926535897932384626433832795";  
         std::cout.precision(35);  
         std::cout \<\< "QD Pi: " \<\< pi \<\< std::endl;  
         return 0;  
     }

  2. Compile and run. Because we installed into $CONDA\_PREFIX, the compiler should find the headers and libraries automatically.  
     Bash  
     g++ \-o verify\_qd src/cpp/verify\_qd.cpp \-lqd  
     ./verify\_qd

  3. *Success Criterion:* The output shows Pi to \>30 digits.

---

#### **Day 4: The Validation Harness \- Tier 1 (Standard Precision)**

**Objective:** Set up the automated testing framework and implement the baseline precision benchmark.

**4.1. The Validation Harness (PyTest)**

* **Concept:** PyTest is used to automate tests. Our "harness" runs simulations and checks if they meet precision criteria.

**4.2. The Kepler Smoke Test**

* **Concept:** A "Smoke Test" checks basic functionality. We use the **Kepler Problem** (two-body orbit) because it is analytically solvable. Energy should be perfectly conserved; any drift is purely numerical error. We use the REBOUND package with the high-accuracy IAS15 integrator.  
* **Action Items:**  
  1. Create tests/test\_kepler\_dp.py.  
  2. Implement a PyTest function:  
     * Set up a REBOUND simulation (two bodies, elliptical orbit e=0.5, IAS15 integrator).  
     * Calculate the initial energy (E0​).  
     * Integrate for 104 orbital periods.  
     * Calculate the final energy (Eend​).  
     * Calculate the relative error: ∣(Eend​−E0​)/E0​∣.  
  3. Add the assertion: assert relative\_error \< 1e-14.  
  4. Run the harness: poetry run pytest tests/test\_kepler\_dp.py.

---

#### **Day 5: High-Precision Toolchain Verification and Automation (CI)**

**Objective:** Verify the high-precision C++ toolchain works with Python and automate the testing process.

**5.1. Python-C++ Bridging (pybind11)**

* **Concept:** To use the C++ QD library from Python, we need a bridge. pybind11 (installed via Conda on Day 1\) provides this interface.

**5.2. High-Precision Toolchain Verification**

* **Concept:** Implementing a full high-precision integrator is too complex for Week 1\. Instead, we verify the full toolchain (Python \-\> pybind11 \-\> C++ \-\> QD) by calculating a single physical quantity (e.g., energy) in high precision.  
* **Action Items:**  
  1. Implement a C++ function (src/cpp/hp\_toolchain.cpp) that accepts coordinates and calculates the Keplerian energy using the dd\_real type.  
  2. Use pybind11 within that file to expose the function to Python. *(Note: dd\_real must be converted to a string or Python Decimal when crossing the boundary).*  
  3. Compile the C++ code into a Python-importable module (using CMake or a simple setup.py script).  
  4. Write a Python test (tests/test\_hp\_toolchain.py) that calls this C++ function and compares the result against a known high-precision value (e.g., from WolframAlpha).  
  5. *Success Criterion:* The Python test passes, confirming the high-precision stack is operational.

**5.3. Continuous Integration (CI) (GitHub Actions)**

* **Concept:** CI automatically runs the validation harness every time code is pushed to GitHub, preventing accidental breakage of the code.  
* **Action Items:**  
  1. Create .github/workflows/ci.yml.  
  2. Configure the workflow to:  
     * Check out the code.  
     * Set up Mamba and restore the environment using environment.yml.  
     * Install Python dependencies using poetry install.  
     * Run the standard precision tests: poetry run pytest tests/test\_kepler\_dp.py.  
       (Note: Running the high-precision tests in CI is complex as it requires compiling QD on the CI server. This is deferred to Week 2).  
  3. Commit all files and push. Verify the CI pipeline passes on GitHub.