# PRAJNA -- Satellite AI System

A modular Python-based AI system designed for satellite data processing, developed as part of an ISTRAC (ISRO) research initiative. PRAJNA implements a graph-based processing pipeline with configurable training, evaluation frameworks, formal verification modules, and an interactive dashboard for monitoring and analysis.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Testing](#testing)
- [License](#license)

---

## Overview

PRAJNA provides:

- **Graph-based processing engine** for satellite data analysis
- **Configurable training pipeline** with YAML-based parameter management
- **Evaluation framework** with comprehensive metrics and benchmarks
- **Dashboard interface** for real-time monitoring
- **CLI interface** for batch processing and automation
- **Formal verification** modules for mission-critical reliability

---

## Architecture

```
+---------------------------------------+
|         CLI / Dashboard               |
|  prajna/cli.py | prajna/dashboard/    |
+---------------------------------------+
              |
              v
+---------------------------------------+
|         PRAJNA Engine                 |
|  prajna/engine/                       |
|  Core processing pipeline             |
+---------------------------------------+
    |           |           |
    v           v           v
+---------+ +-----------+ +------------+
| Graph   | | Training  | | Evaluation |
| Module  | | Pipeline  | | Framework  |
| prajna/ | | prajna/   | | prajna/    |
| graph/  | | training/ | | evaluation/|
+---------+ +-----------+ +------------+
              |
              v
+---------------------------------------+
|         Data Layer                    |
|  prajna/data/ | config/default.yaml   |
+---------------------------------------+
```

---

## Technology Stack

| Component        | Technology                    |
|------------------|-------------------------------|
| Language         | Python 3.10+                  |
| Build System     | pyproject.toml (PEP 517)      |
| Configuration    | YAML (config/default.yaml)    |
| Testing          | pytest                        |
| Package Format   | Python egg/wheel              |

---

## Project Structure

```
pranjan/
|
|-- pyproject.toml                # Package configuration
|
|-- prajna/
|   |-- __init__.py               # Package initialization
|   |-- __main__.py               # Module entry point
|   |-- config.py                 # Configuration management
|   |-- cli.py                    # Command-line interface
|   |
|   |-- engine/                   # Core processing engine
|   |-- graph/                    # Graph-based data structures
|   |-- training/                 # Model training pipeline
|   |-- evaluation/               # Evaluation and metrics
|   |-- dashboard/                # Interactive monitoring UI
|   +-- data/                     # Data loaders and processors
|
|-- config/
|   +-- default.yaml              # Default configuration
|
|-- tests/
|   +-- test_prajna.py            # Test suite
|
+-- docs/
    |-- PRAJNA_System_Architecture_ICD.md
    |-- PRAJNA_Technical_Design_Document.md
    |-- PRAJNA_Algorithm_Specification.md
    |-- PRAJNA_Research_Proposal_ISTRAC.md
    |-- PRAJNA_Evaluation_Framework.md
    +-- (8 additional documentation files)
```

---

## Modules

| Module      | Purpose                                              |
|-------------|------------------------------------------------------|
| engine      | Core satellite data processing pipeline              |
| graph       | Graph-based data structures and traversal            |
| training    | Configurable model training with YAML parameters     |
| evaluation  | Metrics computation and benchmark comparison         |
| dashboard   | Interactive Streamlit/web monitoring interface       |
| data        | Data loaders, validators, and preprocessors          |
| cli         | Command-line entry points and batch processing       |

---

## Installation

```bash
git clone https://github.com/karthik-idikuda/PRAJNA-Satellite-AI.git
cd PRAJNA-Satellite-AI

python -m venv .venv
source .venv/bin/activate

# Install as editable package
pip install -e .
```

---

## Usage

```bash
# Run via module
python -m prajna

# Run via CLI
prajna --config config/default.yaml
```

---

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- System Architecture ICD
- Technical Design Document
- Algorithm Specification
- Research Proposal (ISTRAC/ISRO)
- Evaluation Framework
- Requirements Traceability Matrix
- Quality Assurance Plan
- Advanced Capabilities Specification
- Formal Verification Report

---

## Testing

```bash
pytest
```

---

## License

This project was developed as part of an ISTRAC (ISRO) research initiative.
