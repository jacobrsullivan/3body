# Day 1 Implementation Plan: Foundational Setup Guide

**Target Audience:** Novice Engineers
**Estimated Time:** 6-8 hours
**Prerequisites:** Basic command line familiarity

## Overview

This guide will walk you through setting up the foundational infrastructure for the Three-Body Problem Integrability project. By the end of Day 1, you'll have a complete, version-controlled development environment ready for high-precision scientific computing.

## Learning Objectives

By completing this plan, you will understand:
- How to set up professional version control workflows
- Why environment isolation is critical for reproducible science
- How to structure a scientific computing project
- Basic Git operations and best practices

---

## Section 1: Version Control Setup (60 minutes)

### 1.1 Understanding Git and Version Control

**What is Git?**
Git is a distributed version control system that tracks every change in your code. Think of it as a time machine for your project - you can see what changed, when it changed, and who changed it. This is essential for:
- **Collaboration:** Multiple people can work on the same code safely
- **Debugging:** You can identify when and where bugs were introduced
- **Scientific Reproducibility:** You can recreate exact conditions from any point in time

**What is GitHub?**
GitHub is a cloud service that hosts Git repositories, making them accessible from anywhere and enabling collaboration.

### 1.2 Prerequisites Check

Before starting, verify Git is installed:

```bash
git --version
```

**Expected Output:** Something like `git version 2.x.x`

**If Git is not installed:**
- **macOS:** Install via Homebrew: `brew install git` or download from [git-scm.com](https://git-scm.com)
- **Linux:** `sudo apt install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RHEL)
- **Windows:** Download from [git-scm.com](https://git-scm.com)

### 1.3 GitHub Repository Creation

1. **Go to GitHub.com** and sign in (create account if needed)
2. **Click "New Repository"** (green button or "+" icon)
3. **Configure the repository:**
   - Repository name: `3BP-Integrability-WP1`
   - Description: "Three-Body Problem Integrability Research - Work Package 1"
   - Set to **Public** (for scientific transparency)
   - **Do NOT** initialize with README, .gitignore, or license (we'll create these)
4. **Click "Create repository"**

### 1.4 SSH Key Setup and Authentication

**Why SSH Keys?** SSH keys provide secure, password-free authentication with GitHub. This is more secure than HTTPS and more convenient for frequent pushes.

#### 1.4.1 Check for Existing SSH Keys

```bash
ls -la ~/.ssh/
```

**Look for files like:** `id_rsa`, `id_ed25519`, `id_jacob`, etc. If you see these, you likely have SSH keys already.

#### 1.4.2 Set Up SSH Key (if needed)

**If you have an existing key** (like `id_jacob`):
```bash
# Add your existing key to SSH agent
ssh-add ~/.ssh/id_jacob
```

**If you need to create a new key:**
```bash
# Generate new SSH key (replace email with yours)
ssh-keygen -t ed25519 -C "your.email@example.com"
# Press Enter to accept default location
# Enter a passphrase (optional but recommended)

# Add to SSH agent
ssh-add ~/.ssh/id_ed25519
```

#### 1.4.3 Add SSH Key to GitHub

1. **Copy your public key:**
   ```bash
   cat ~/.ssh/id_jacob.pub  # Or ~/.ssh/id_ed25519.pub
   ```
2. **Go to GitHub.com** → Settings → SSH and GPG keys
3. **Click "New SSH key"**
4. **Paste the key content** and give it a descriptive title
5. **Click "Add SSH key"**

#### 1.4.4 Test SSH Connection

```bash
ssh -T git@github.com
```

**Expected output:** `Hi [username]! You've successfully authenticated...`

### 1.5 Git User Configuration

Configure Git with your identity (this appears in commit history):

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Example:**
```bash
git config --global user.name "Jacob Sullivan"
git config --global user.email "jacobrsullivan@gmail.com"
```

### 1.6 Local Repository Setup

1. **Copy the SSH URL** from GitHub (starts with `git@github.com:`)
2. **Open your terminal** and navigate to where you want the project:
   ```bash
   cd ~/Desktop  # Or wherever you prefer
   ```
3. **Clone the repository:**
   ```bash
   git clone git@github.com:yourusername/3BP-Integrability-WP1.git
   cd 3BP-Integrability-WP1
   ```

**Example with real repository:**
```bash
git clone git@github.com:jacobrsullivan/3body.git
cd 3body
```

**Verification:** You should now be in your project directory. Running `ls -la` should show a `.git` folder.

---

## Section 2: Project Structure and Git Configuration (30 minutes)

### 2.1 Understanding Project Organization

A well-organized project structure is like a well-organized laboratory - everything has its place:

- `src/`: Source code (the actual programs we write)
- `tests/`: Automated tests to verify our code works
- `notebooks/`: Jupyter notebooks for analysis and visualization
- `docs/`: Documentation and guides
- `data/`: (Created later) Store simulation results and datasets

### 2.2 Creating the Directory Structure

```bash
mkdir -p src/cpp src/python tests notebooks docs
```

**What this does:** The `-p` flag creates parent directories as needed. This single command creates the entire folder structure.

### 2.3 Understanding .gitignore

The `.gitignore` file tells Git which files to **never** track. This is crucial because:
- **Large files** (simulation data) would make the repository huge
- **Temporary files** (like `.pyc` files) are automatically generated
- **System files** (like `.DS_Store` on macOS) are not relevant to other users

### 2.4 Creating .gitignore

1. **Visit gitignore.io** (or copy the content below)
2. **Create the file:**
   ```bash
   touch .gitignore
   ```
3. **Open in your text editor** and paste this content:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
*.egg-info/
dist/
build/

# C++
*.o
*.a
*.so
*.exe
*.dll
*.dylib
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
Makefile

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
data/
results/
*.h5
*.hdf5
*.parquet
build_external/
```

### 2.5 First Commit and Remote Setup

If you created an empty repository (as recommended), you'll need to set up the remote and push:

```bash
git add .
git commit -m "Initial project structure with comprehensive .gitignore"
git remote add origin git@github.com:yourusername/3BP-Integrability-WP1.git
git push -u origin main
```

**Example with real repository:**
```bash
git add .
git commit -m "Initial project structure with comprehensive .gitignore"
git remote add origin git@github.com:jacobrsullivan/3body.git
git push -u origin main
```

**What this does:**
- `git add .`: Stage all files for commit
- `git commit -m "..."`: Create a commit with a descriptive message
- `git remote add origin [URL]`: Connect local repo to GitHub repository
- `git push -u origin main`: Upload the commit to GitHub and set upstream tracking

**Verification:** Check GitHub - you should see your folders and .gitignore file.

---

## Section 3: Environment Management Setup (45 minutes)

### 3.1 Why Environment Isolation Matters

**The Problem:** Different projects need different versions of software. Python 3.8 vs 3.11, NumPy 1.20 vs 1.24, etc. Installing everything globally leads to conflicts.

**The Solution:** Create isolated environments for each project. Think of it as a separate "laboratory" for each experiment.

### 3.2 Installing Mambaforge

**Why Mamba over Conda?** Mamba is a drop-in replacement for Conda that's significantly faster and more reliable at resolving dependencies.

1. **Download Mambaforge:**
   - Go to [github.com/conda-forge/miniforge](https://github.com/conda-forge/miniforge)
   - Download the appropriate installer for your system

2. **Install (example for macOS/Linux):**
   ```bash
   bash Mambaforge-*.sh
   ```
   - Accept the license
   - Accept the default location (or choose another)
   - **Important:** Say "yes" to initializing conda

3. **Restart your terminal** or run:
   ```bash
   source ~/.bashrc  # Linux
   source ~/.zshrc   # macOS with zsh
   ```

**Verification:** Running `mamba --version` should show version information.

### 3.3 Understanding environment.yml

This file defines our project's environment in a reproducible way. **Crucially**, we use Conda-provided compilers rather than system ones for consistency.

### 3.4 Creating environment.yml

Create `environment.yml` in your project root:

```yaml
name: wp1_env
channels:
  - conda-forge
dependencies:
  - python=3.11
  - poetry
  # Crucial: Ensures consistent C/C++/Fortran compilers across systems
  - compilers
  # Build tools required for C++ libraries
  - cmake
  - make
  # Required for bridging Python and C++
  - pybind11
  # Additional useful tools
  - git
  - curl
  - wget
```

**Why these specific packages?**
- `python=3.11`: Latest stable Python version
- `poetry`: Modern Python dependency management
- `compilers`: Provides gcc, g++, gfortran via Conda
- `cmake`: Build system for C++ projects
- `pybind11`: Connects Python and C++ code

---

## Section 4: Environment Creation and Verification (30 minutes)

### 4.1 Creating the Environment

```bash
mamba env create -f environment.yml
```

**What happens:** Mamba downloads and installs all specified packages into an isolated environment.

**Expected time:** 2-5 minutes depending on internet speed.

### 4.2 Activating the Environment

```bash
mamba activate wp1_env
```

**Visual cue:** Your command prompt should now show `(wp1_env)` at the beginning.

### 4.3 Critical Verification: Compiler Location

This step ensures we're using Conda compilers, not system ones:

```bash
which g++
which gcc
which python
```

**Expected output:** All paths should contain your Conda environment path, something like:
```
/home/user/mambaforge/envs/wp1_env/bin/g++
/home/user/mambaforge/envs/wp1_env/bin/gcc
/home/user/mambaforge/envs/wp1_env/bin/python
```

**If paths show `/usr/bin/...`:** The system compilers are active instead. Try:
1. Deactivate and reactivate: `mamba deactivate`, then `mamba activate wp1_env`
2. Check that `compilers` package was installed: `mamba list compilers`

### 4.4 Committing the Environment Definition

```bash
git add environment.yml
git commit -m "Add reproducible environment definition with Conda compilers"
git push origin main
```

---

## Section 5: Python Dependency Management (30 minutes)

### 5.1 Understanding Poetry

Poetry solves a critical problem in Python dependency management:
- **Pip** tracks what you install, but not exact versions of sub-dependencies
- **Poetry** creates a lock file with exact versions of every package
- This guarantees that `pip install` will produce identical environments

### 5.2 Initializing Poetry

```bash
poetry init
```

**Follow the prompts:**
- Package name: `three-body-integrability-wp1`
- Version: `0.1.0`
- Description: `High-precision three-body problem integrability research`
- Author: `Your Name <your.email@example.com>`
- License: `MIT` (or your preference)
- Compatible Python versions: `^3.11`
- Define dependencies interactively: `no` (we'll add them next)

### 5.3 Adding Core Scientific Dependencies

```bash
poetry add numpy scipy matplotlib jupyterlab pytest numba h5py pyarrow rebound
```

**What each package does:**
- `numpy`: Fundamental array operations
- `scipy`: Advanced scientific computing
- `matplotlib`: Plotting and visualization
- `jupyterlab`: Interactive notebooks
- `pytest`: Testing framework
- `numba`: Just-in-time compilation for speed
- `h5py`: HDF5 file format (efficient for large datasets)
- `pyarrow`: Parquet file format (efficient for tabular data)
- `rebound`: N-body simulation package

**Expected time:** 2-3 minutes to resolve and install dependencies.

### 5.4 Adding Development Dependencies

```bash
poetry add --group dev black flake8 pre-commit mypy
```

**What these do:**
- `black`: Automatic code formatting
- `flake8`: Code style checking and error detection
- `pre-commit`: Runs checks before each commit
- `mypy`: Type checking for Python

### 5.5 Verification

```bash
poetry show
```

This should list all installed packages with their exact versions.

---

## Section 6: Code Quality Automation (30 minutes)

### 6.1 Understanding Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each Git commit. This prevents "bad" code from entering the repository.

### 6.2 Creating .pre-commit-config.yaml

Create this file in your project root:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
```

### 6.3 Installing Pre-commit Hooks

```bash
poetry run pre-commit install
```

### 6.4 Testing the Setup

Create a test Python file to verify everything works:

```bash
echo 'print("Hello,     World!")   ' > test_style.py
git add test_style.py
git commit -m "Test pre-commit hooks"
```

**Expected behavior:** Pre-commit should automatically fix the formatting and the commit should succeed.

---

## Section 7: Final Verification and Documentation (20 minutes)

### 7.1 Creating a Quick Verification Script

Create `verify_setup.py`:

```python
"""
Day 1 Setup Verification Script
Confirms all components are working correctly.
"""

import sys
import subprocess
import importlib

def check_python_version():
    """Verify Python version is 3.11."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    assert version >= (3, 11), "Python 3.11+ required"
    print("✓ Python version OK")

def check_packages():
    """Verify core packages can be imported."""
    packages = ['numpy', 'scipy', 'matplotlib', 'rebound', 'pytest']
    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} imported successfully")
        except ImportError:
            print(f"✗ Failed to import {package}")
            raise

def check_compilers():
    """Verify Conda compilers are active."""
    try:
        result = subprocess.run(['which', 'g++'], capture_output=True, text=True)
        gcc_path = result.stdout.strip()
        print(f"g++ location: {gcc_path}")

        # Should contain conda/mamba environment path
        if 'conda' in gcc_path or 'mamba' in gcc_path:
            print("✓ Conda compilers active")
        else:
            print("⚠ Warning: System compilers may be active")

    except Exception as e:
        print(f"✗ Compiler check failed: {e}")

def main():
    """Run all verification checks."""
    print("Day 1 Setup Verification")
    print("=" * 30)

    try:
        check_python_version()
        check_packages()
        check_compilers()

        print("\n🎉 All checks passed! Day 1 setup complete.")

    except Exception as e:
        print(f"\n❌ Setup verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 7.2 Running Verification

```bash
python verify_setup.py
```

**Expected output:** All checks should pass with ✓ marks.

### 7.3 Final Commit

```bash
git add .
git commit -m "Complete Day 1 setup: environment, dependencies, and verification"
git push origin main
```

---

## Troubleshooting Common Issues

### Issue: "Git not found"
**Solution:** Install Git following Section 1.2 instructions.

### Issue: "Mamba command not found"
**Solution:**
1. Restart terminal after installation
2. Check if conda is available: `conda --version`
3. If conda works, install mamba: `conda install mamba -c conda-forge`

### Issue: "Pre-commit hooks not running"
**Solution:**
1. Ensure poetry environment is active: `poetry shell`
2. Reinstall hooks: `poetry run pre-commit install`

### Issue: "Poetry not found"
**Solution:**
1. Activate conda environment: `mamba activate wp1_env`
2. Verify Poetry is installed: `mamba list poetry`

### Issue: "Wrong compiler paths"
**Solution:**
1. Deactivate and reactivate environment
2. Check `mamba list compilers` shows installed
3. Try `mamba install compilers -c conda-forge --force-reinstall`

### Issue: "Permission denied (publickey)" when pushing to GitHub
**Solution:**
1. Check SSH key is added to agent: `ssh-add -l`
2. Test GitHub connection: `ssh -T git@github.com`
3. Verify SSH key is added to GitHub account
4. If using HTTPS URL, switch to SSH: `git remote set-url origin git@github.com:username/repo.git`

### Issue: "Could not read from remote repository"
**Solution:**
1. Verify the repository URL is correct: `git remote -v`
2. Check you have access to the repository on GitHub
3. Try cloning with HTTPS if SSH fails: `git clone https://github.com/username/repo.git`

---

## Success Criteria for Day 1

You have successfully completed Day 1 setup if:

- [ ] Git repository is created and pushed to GitHub
- [ ] Project directory structure is organized
- [ ] Conda environment is created with proper compilers
- [ ] Poetry is managing Python dependencies with lock file
- [ ] Pre-commit hooks are installed and working
- [ ] Verification script passes all checks
- [ ] All changes are committed and pushed to GitHub

## Next Steps

Day 2 will focus on:
- Instantiating the complete environment from scratch (testing reproducibility)
- Setting up comprehensive code quality tooling
- Creating the first automated tests

---

## Quick Reference Commands

```bash
# Environment management
mamba activate wp1_env
mamba deactivate

# Poetry operations
poetry add <package>                 # Add new dependency
poetry install                       # Install from pyproject.toml
poetry shell                        # Enter poetry environment
poetry run <command>                # Run command in poetry environment

# Git operations
git status                          # Check current status
git add <file>                      # Stage files for commit
git commit -m "message"             # Create commit
git push origin main                # Push to GitHub
git pull origin main                # Pull from GitHub

# Verification
python verify_setup.py              # Run setup verification
poetry run pytest                   # Run tests
poetry run pre-commit run --all-files  # Run all pre-commit checks
```

---

**Estimated Total Time:** 5-7 hours for novice engineers
**Files Created:** 7 files (environment.yml, pyproject.toml, poetry.lock, .gitignore, .pre-commit-config.yaml, verify_setup.py, plus this guide)
**Repository State:** Fully reproducible development environment ready for scientific computing
