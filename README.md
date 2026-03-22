# 🛰 PRAJNA — Spacecraft Health Intelligence Platform

**Predictive Reasoning Architecture for Joint Network-wide Anomalics**

> Full-lifecycle spacecraft health monitoring with 10 novel algorithms for anomaly detection, failure prediction, root-cause analysis, and reusable launch vehicle requalification.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

PRAJNA is a spacecraft health intelligence platform implementing 10 novel algorithms organized across three mission phases:

| Phase | Algorithms | Purpose |
|-------|-----------|---------|
| **In-Flight** | SDWAP, TGN, AEGIS, SHAKTI, KAVACH | Real-time anomaly detection & failure prediction |
| **Bridge** | CLPX | Cross-lifecycle pattern exchange |
| **Post-Flight** | THERMAL-DIFF-GNN, RLV-RUL | Reusable vehicle requalification |
| **Support** | PhyRAG, NLG | Explainability & operator guidance |

### Key Algorithms

- **SDWAP** — Subsystem Dependency-Weighted Anomaly Propagation: Graph-based anomaly score propagation using physics-informed spacecraft dependencies
- **TGN** — Temporal Graph Network: GAT + GRU memory for temporal encoding of subsystem states
- **AEGIS** — Adversarial Environment Guard for Input Sanitization: 3-layer (spectral + autoencoder + temporal) data quality guard
- **SHAKTI** — Statistical Hardening with Adaptive Konformal Thresholding for Inference: Conformal prediction with online α-adaptation
- **KAVACH** — Formal safety verification with 5 runtime properties
- **CLPX** — Cross-Lifecycle Pattern Exchange: Forward/backward knowledge transfer between flight phases
- **THERMAL-DIFF-GNN** — Physics-informed graph diffusion for thermal damage assessment
- **RLV-RUL** — Triple-mode (thermal/radiation/vibration) remaining useful life estimation
- **PhyRAG** — Physics-constrained Retrieval-Augmented Generation for explanations
- **NLG** — Natural language alert generation with operator contingency actions

## Architecture

```
┌─────────────────────────────────────────────────┐
│               Telemetry Input                    │
│  (13 subsystems × 8 features per timestep)      │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────▼───────┐
       │  LocalDetector │  Z-score + IsolationForest
       └───────┬───────┘
               │
       ┌───────▼───────┐
       │     SDWAP      │  Graph-based score propagation
       └───────┬───────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼──┐  ┌───▼──┐  ┌───▼───┐
│ TGN  │  │AEGIS │  │SHAKTI │
└───┬──┘  └───┬──┘  └───┬───┘
    │         │          │
    └─────────┼──────────┘
              │
       ┌──────▼──────┐
       │   KAVACH     │  Safety verification
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │  NLG/PhyRAG │  Alert generation
       └─────────────┘
```

## Quick Start

### Installation

```bash
# Clone
git clone <repo-url> prajna
cd prajna

# Install (editable mode)
pip install -e .
```

### Generate Synthetic Data

```bash
prajna synthetic --timesteps 5000 --anomaly-ratio 0.05
```

### Run Demo

```bash
prajna demo
```

This injects an anomaly into the EPS subsystem and shows:
1. Local detection scores per subsystem
2. SDWAP propagation with contribution tracing
3. KAVACH safety verification
4. NLG-generated alerts with contingency actions

### Train Models

```bash
# Using synthetic data
prajna synthetic --timesteps 10000
prajna train --config config/default.yaml

# Using real NASA data
prajna download
prajna preprocess
prajna train
```

### Evaluate

```bash
prajna evaluate --data-dir data/processed
```

### Launch Dashboard

```bash
prajna dashboard --port 5000
```
Open http://127.0.0.1:5000 for real-time spacecraft health visualization.

## CLI Reference

| Command | Description |
|---------|-------------|
| `prajna demo` | Run live inference demo with synthetic anomaly injection |
| `prajna synthetic` | Generate synthetic spacecraft telemetry data |
| `prajna download` | Download real NASA/ESA datasets via Kaggle |
| `prajna preprocess` | Preprocess raw data into unified format |
| `prajna train` | Train all PRAJNA models |
| `prajna evaluate` | Run evaluation metrics (ROC-AUC, F1, Lead Time, etc.) |
| `prajna dashboard` | Launch Flask web dashboard |

## Project Structure

```
prajna/
├── __init__.py              # Package init, version 1.1.0
├── __main__.py              # Entry point
├── cli.py                   # CLI with 7 commands
├── config.py                # YAML config loader
├── data/
│   ├── __init__.py          # DataDownloader + DataAdapter
│   ├── preprocessor.py      # Z-score, FFT, rolling window features
│   └── synthetic_generator.py  # Synthetic telemetry generator
├── engine/
│   ├── __init__.py          # Module exports
│   ├── local_detector.py    # Z-score + IsolationForest ensemble
│   ├── sdwap.py             # Novel: graph anomaly propagation
│   ├── tgn.py               # Novel: temporal graph network
│   ├── aegis.py             # Novel: adversarial data guard
│   ├── shakti.py            # Novel: conformal prediction
│   ├── kavach.py            # Novel: formal safety verification
│   ├── clpx.py              # Novel: cross-lifecycle transfer
│   ├── phyrag.py            # Novel: physics-constrained RAG
│   ├── postflight.py        # Novel: THERMAL-DIFF-GNN + RLV-RUL
│   └── nlg.py               # Alert generation engine
├── evaluation/
│   └── __init__.py          # 10+ metrics + ablation runner
├── training/
│   └── __init__.py          # TGN + AEGIS + LocalDetector training
├── dashboard/
│   └── __init__.py          # Flask web dashboard
├── graph/
│   └── __init__.py          # 13-node spacecraft dependency graph
config/
│   └── default.yaml         # Full project configuration
tests/
│   └── test_prajna.py       # 40+ unit/integration/system tests
```

## Spacecraft Subsystem Graph

13 subsystems with 24 physics-informed dependency edges:

```
EPS ──→ TCS, COMM, OBC, BATT, SA
TCS ──→ EPS, OBC, BATT
PROP ──→ AOCS, STRUCT
AOCS ──→ PROP, COMM, PL
COMM ──→ OBC
OBC ──→ EPS, AOCS, COMM, PYRO
STRUCT ──→ HARNESS
HARNESS ──→ EPS, COMM
BATT ──→ EPS
SA ──→ EPS, TCS
```

## Evaluation Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| ROC-AUC | ≥ 0.92 | Detection discrimination |
| PR-AUC | ≥ 0.85 | Precision-recall balance |
| F1 Score | ≥ 0.88 | Harmonic mean P/R |
| Lead Time | ≥ 30 min | Early warning capability |
| False Alarm Rate | ≤ 2% | Operator trust |
| RCA Accuracy | ≥ 90% | Root cause identification |
| Brier Score | ≤ 0.08 | Calibration quality |
| RUL MAPE | ≤ 15% | Life prediction accuracy |
| SDWAP Fidelity | ≥ 0.85 | Propagation correctness |
| Coverage Gap | ≤ 1% | SHAKTI calibration |

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Configuration

Edit `config/default.yaml` to customize:
- Graph structure (nodes, edges, weights)
- SDWAP parameters (iterations, damping, decay)
- TGN architecture (hidden dim, heads, layers)
- Training parameters (epochs, batch size, LR)
- AEGIS thresholds
- SHAKTI coverage level
- KAVACH safety properties

## Hardware Requirements

- **Minimum**: MacBook Air M2, 8GB RAM
- **Recommended**: Any machine with Python 3.11+
- **GPU**: Optional (MPS/CUDA accelerated if available)
- **Cost**: $0 — fully offline operation
- **Internet**: Only needed for initial dataset download

## License

MIT License

## Author

Karthik — ISRO RESPOND Programme Submission

---

*PRAJNA: Where ancient wisdom meets modern spacecraft intelligence.*


## Architecture Overview

### Project Type
- **Primary stack:** Python package/project
- **Primary language:** Python
- **Primary entrypoint/build root:** Python package entry points

### High-Level Architecture
- This repository is organized in modular directories grouped by concern (application code, configuration, scripts, documentation, and assets).
- Runtime/build artifacts such as virtual environments, node modules, and compiled outputs are intentionally excluded from architecture mapping.
- The project follows a layered flow: entry point -> domain/application modules -> integrations/data/config.

### Component Breakdown
- **Application layer:** Core executables, services, UI, or command handlers.
- **Domain/business layer:** Feature logic and processing modules.
- **Integration layer:** External APIs, databases, files, or platform-specific connectors.
- **Support layer:** Config, scripts, docs, tests, and static assets.

### Data/Execution Flow
1. Start from the configured entrypoint or package scripts.
2. Route execution into feature-specific modules.
3. Process domain logic and interact with integrations/storage.
4. Return results to UI/API/CLI outputs.

### Directory Map (Top-Level + Key Subfolders)
```
prajna.egg-info
prajna.egg-info/PKG-INFO
prajna.egg-info/SOURCES.txt
prajna.egg-info/entry_points.txt
prajna.egg-info/requires.txt
prajna.egg-info/top_level.txt
prajna.egg-info/dependency_links.txt
.DS_Store
prajna
prajna/.DS_Store
prajna/config.py
prajna/training
prajna/graph
prajna/__init__.py
prajna/__pycache__
prajna/dashboard
prajna/cli.py
prajna/evaluation
prajna/data
prajna/engine
prajna/__main__.py
.pytest_cache
.pytest_cache/CACHEDIR.TAG
.pytest_cache/README.md
.pytest_cache/.gitignore
.pytest_cache/v
config
config/default.yaml
pyproject.toml
tests
tests/__pycache__
tests/test_prajna.py
docs
docs/00_PRAJNA_Document_Register.md
docs/PRAJNA_Technical_Design_Document.md
```

### Notes
- Architecture section auto-generated on 2026-03-22 and can be refined further with exact runtime/deployment details.
