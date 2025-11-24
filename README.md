# Three-Body Problem Integrability Research

**Work Package 1: High-Fidelity CR3BP Trajectory Catalogue**

A systematic search for hidden integrability in the Newtonian three-body problem via higher-dimensional symplectic embedding.

## Project Structure

- `src/cpp/` - High-precision C++ implementations
- `src/python/` - Python interface and analysis tools
- `tests/` - Automated test suite
- `notebooks/` - Jupyter analysis notebooks
- `docs/` - Documentation

## Environment Setup

This project uses conda/mamba for system-level dependencies and Poetry for Python package management.

### Quick Start

1. Create the conda environment:
   ```bash
   mamba env create -f environment.yml
   mamba activate wp1_env
   ```

2. Install Python dependencies:
   ```bash
   poetry install
   ```

3. Verify setup:
   ```bash
   python verify_setup.py
   ```

## Quick Start

1. Activate the conda environment:
   ```bash
   mamba activate wp1_env
   ```

2. Verify setup (Days 1-3):
   ```bash
   python verify_setup.py
   ```

3. Build C++ components:
   ```bash
   ./scripts/build_cpp.sh
   ```

4. Run tests:
   ```bash
   ./scripts/run_tests.sh
   ```

## Verification

### Environment Verification
Run the setup verification script to ensure all components are working correctly:

```bash
python verify_setup.py
```

This checks:
- Python version and packages
- Conda compilers
- QD library installation
- QD high-precision arithmetic

### Comprehensive Testing
Run the full test suite (C++ and Python):

```bash
./scripts/run_tests.sh
```

Or run specific tests:
```bash
# Python environment tests
pytest tests/python/ -v

# QD comprehensive tests
./build/qd_comprehensive_test

# QD performance benchmarks
./build/qd_benchmark
```

## Development

This project uses:
- **CMake** for C++ build automation
- **pytest** for Python testing
- **Black** for code formatting
- **Flake8** for linting
- **Pre-commit hooks** for quality control

All code quality checks run automatically before commits.

### Build System

The project includes automated build scripts in `scripts/`:
- `build_cpp.sh` - Build all C++ components
- `run_tests.sh` - Run all tests (Python + C++)

See `scripts/README.md` for detailed usage.

## Using Claude Code Agents

This project includes an **agentic architecture** with 12 specialized agents and 11 skills to help with complex scientific computing tasks. The agents handle everything from trajectory generation to manuscript writing.

### Quick Start with Agents

When using Claude Code with this project, you can simply describe what you want to do in natural language:

**Examples**:
```
"Generate 1000 high-precision trajectories"
→ Automatically routes to wp1-lab-director agent

"Build the KS spinor lift construction"
→ Routes to wp2-architect agent

"Search for conserved quantities"
→ Routes to wp3-investigator agent

"Validate this candidate integral: u1**2 + u2**2"
→ Routes to wp4-mathematician agent

"Show me the system architecture"
→ Routes to diagram generation agents
```

### Agent System Overview

The project includes:

**Work Package (WP) Agents (10)**:
- `wp1-lab-director` - Trajectory generation and validation
- `wp2-architect` - Geometric construction (lifts, bundles)
- `wp2-analyst` - Geometric verification (curvature, integrability)
- `wp3-investigator` - Integral discovery (PDE, ML, symbolic)
- `wp3-consolidator` - Result filtering and ranking
- `wp4-mathematician` - Analytical validation (Morales-Ramis)
- `wp4-stress-tester` - Numerical robustness testing
- `wp5-author` - Manuscript writing
- `wp5-librarian` - Code release and archival
- `research-orchestrator` - Multi-WP planning

**Diagram Agents (2)**:
- `abstraction-architect` - Generate architectural diagrams
- `abstraction-analyst` - Validate diagrams

**Navigation Skills (2)**:
- `wp-navigator` - Routes work package tasks
- `project-navigator` - Routes architectural questions

### Documentation

For detailed information on using and modifying the agents:

- **Agent User Guide**: `Claude-Agent-Docs/WPSkillsDocs/README.md`
  - Complete guide to using agents
  - How to modify agents
  - Troubleshooting common issues

- **Agent Implementation Plan**: `Claude-Agent-Docs/WPSkillsDocs/Implementation-Plan-Agents-for-3Body.MD`
  - Architecture overview
  - Agent consolidation strategy
  - Flight Recorder logs

- **WP-Specific Agent Docs**: `Claude-Agent-Docs/WPSkillsDocs/WP[1-5]_Skills_Agents_List.MD`
  - Detailed agent capabilities for each work package

### Example Workflows

**Generate and validate trajectories**:
```
"Use wp1-lab-director to generate 100 trajectories with double-double precision,
then validate precision and create a summary report"
```

**Complete validation pipeline**:
```
"I found a candidate integral: u1**2 + u2**2.
Run the full validation pipeline through all WP4 stages"
```

**Multi-WP research question**:
```
"What's the best strategy to search for integrals in KS spinor space?"
→ Routes to research-orchestrator for strategic planning
```

### Key Features

- **Automatic Routing**: Describe tasks in natural language, agents route automatically
- **Flight Recorder Logs**: All research tasks maintain audit trails for reproducibility
- **Quality Gates**: Automated hooks enforce testing and formatting standards
- **Builder-Critic Pairs**: Separate agents for construction (creative) and validation (critical)

### For Developers

**Modifying agents**:
1. Edit agent files in `.claude/agents/<agent-name>.md`
2. Update skills in `.claude/skills/<skill-name>/SKILL.md`
3. Follow the **Read-First Principle**: Agents reference code, never duplicate it

**Creating new agents**:
See `Claude-Agent-Docs/WPSkillsDocs/README.md` section on "Creating New Agents"

**Agent locations**:
- Agents: `.claude/agents/`
- Skills: `.claude/skills/`
- Settings/Hooks: `.claude/settings.json`
