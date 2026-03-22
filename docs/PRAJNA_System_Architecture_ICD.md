
# PRAJNA — System Architecture & Interface Control Document

## Detailed Component Interfaces, Data Formats, and Integration Contracts

---

**Document Number:** PRAJNA/ARCH/2026/001  
**Version:** 1.0  
**Date of Issue:** 06 March 2026  
**Classification:** UNRESTRICTED — FOR REVIEW  
**Prepared for:** Indian Space Research Organisation (ISRO)

---

## TABLE OF CONTENTS

1. [Architecture Principles](#1-architecture-principles)
2. [Module Decomposition](#2-module-decomposition)
3. [Interface Control Specifications](#3-interface-control-specifications)
4. [Data Schema Definitions](#4-data-schema-definitions)
5. [Configuration Management](#5-configuration-management)
6. [File System Layout](#6-file-system-layout)
7. [Execution Modes](#7-execution-modes)
8. [Error Handling Strategy](#8-error-handling-strategy)
9. [Security Architecture](#9-security-architecture)

---

## 1. ARCHITECTURE PRINCIPLES

### 1.1 Design Decisions

| Principle | Rationale |
|-----------|-----------|
| **Modular pipeline** | Each algorithm is an independent module with defined input/output interfaces. Allows isolated testing and incremental development. |
| **Graph-first data model** | All inter-subsystem reasoning flows through the dependency graph. No ad-hoc subsystem pair logic. |
| **Physics-ML hybrid** | Where physics models exist (thermal fatigue, radiation, vibration), use them as priors. ML learns the residual. |
| **Offline-only** | No network calls in inference. LLM, embeddings, and vector DB all run locally. |
| **Configuration as code** | All hyperparameters, graph structure, and system settings in version-controlled YAML files. |
| **Deterministic training** | Fixed seeds, deterministic operations where possible. Results are reproducible. |

### 1.2 Technology Constraints

| Constraint | Source | Implementation |
|------------|--------|---------------|
| Air-gapped operation | ISRO security policy | Ollama local LLM, ChromaDB local vector store, no HTTP calls |
| Consumer hardware | Internship resource limitation | PyTorch CPU inference, models < 2GB RAM total |
| Python ecosystem | ISRO academic compatibility | Python 3.11+, pip-installable dependencies only |

---

## 2. MODULE DECOMPOSITION

### 2.1 Module Map

```
prajna/
├── data/
│   ├── data_adapter.py                — Multi-format adapter for NASA SMAP/MSL, ESA-AD, C-MAPSS, OPS-SAT, MOSDAC
│   ├── preprocessor.py             — Normalization, imputation, windowing, FFT features
│   └── dataloader.py               — PyTorch DataLoader for training and inference
│
├── graph/
│   ├── schema.py                   — Node/edge definitions, W_base matrix
│   ├── dynamic_builder.py          — Time-varying graph construction with learned Δw
│   └── dependency_estimator.py     — MLP that adjusts edge weights from telemetry
│
├── engine/
│   ├── local_detector.py           — Z-score and Isolation Forest anomaly detectors
│   ├── sdwap.py                    — SDWAP propagation algorithm
│   ├── tgn.py                      — Temporal Graph Neural Network core
│   └── pipeline.py                 — Orchestrates inference: preprocess → detect → propagate → predict
│
├── models/
│   ├── predictor.py                — Dual classifier-hazard failure predictor
│   ├── calibrator.py               — Platt scaling calibration module
│   ├── thermal_diff_gnn.py         — THERMAL-DIFF-GNN post-flight module
│   └── rlv_rul.py                  — Triple-mode RUL estimator
│
├── evaluation/
│   ├── metrics.py                  — ROC-AUC, PR-AUC, F1, Brier, lead time, FAR
│   ├── ablation.py                 — Ablation study runner
│   └── reporter.py                 — Generate evaluation reports (JSON + HTML)
│
├── training/
│   ├── trainer.py                  — Training loop (AdamW, focal loss, early stopping)
│   ├── losses.py                   — Focal loss, SDWAP consistency loss, reconstruction loss
│   └── scheduler.py               — Cosine annealing LR schedule
│
├── utils/
│   ├── config.py                   — YAML configuration loader and validator
│   ├── logging.py                  — Structured logging with rotation
│   ├── math_utils.py              — Shared math operations (sigmoid, layer norm, etc.)
│   └── io_utils.py                — HDF5/CSV/JSON read-write utilities
│
├── rag/
│   ├── knowledge_base.py          — ChromaDB construction and management
│   ├── retriever.py               — Query embedding and top-k retrieval
│   ├── generator.py               — Ollama/Mistral-7B prompt management
│   └── physics_checker.py         — Physics constraint validation layer
│
├── nlg/
│   ├── decision_engine.py         — Action bucket scoring for contingency selection
│   ├── template_renderer.py       — Structured alert text generation
│   └── explainability.py          — SDWAP trace, attribution, counterfactual
│
├── clpx/
│   ├── bridge.py                  — Cross-lifecycle pattern exchange core
│   ├── projections.py             — Forward/backward projection networks
│   └── adaptation.py              — Trust balance α adaptation
│
└── __init__.py                    — Package entry point

config/
├── default.yaml                   — All default hyperparameters
├── graph_schema.yaml              — W_base, node definitions, edge list
├── physics_params.yaml            — Coffin-Manson, radiation, vibration parameters
└── dashboard.yaml                 — Flask config, port, refresh rate

scripts/
├── download_data.py               — CLI: download real datasets (NASA, ESA, MOSDAC)
├── train.py                       — CLI: train all models
├── evaluate.py                    — CLI: run evaluation + ablation
├── run_inference.py               — CLI: real-time inference demo
├── run_postflight.py              — CLI: post-flight assessment demo
└── run_dashboard.py               — CLI: launch web dashboard

tests/
├── test_sdwap.py                  — SDWAP convergence and correctness
├── test_tgn.py                    — TGN forward pass shape validation
├── test_thermal_diff_gnn.py       — Physics-ML hybrid output ranges
├── test_rlv_rul.py                — RUL calculation against known values
├── test_phyrag.py                 — Physics checker constraint enforcement
├── test_clpx.py                   — Cross-lifecycle embedding consistency
├── test_pipeline.py               — End-to-end integration test
└── test_data_adapter.py           — Data ingestion and format adapter tests
```

### 2.2 Module Dependency Graph

```
                    config/
                      │
                      ▼
                 utils/config.py
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     data/         graph/      utils/
          │           │
          ▼           ▼
       engine/local_detector ──► engine/sdwap
                                     │
          ┌──────────────────────────┤
          ▼                          ▼
     engine/tgn                engine/pipeline
          │                          │
          ▼                          ▼
    models/predictor           nlg/decision_engine
    models/calibrator          nlg/template_renderer
                               nlg/explainability
          │
          ▼
    models/thermal_diff_gnn ──► rag/
    models/rlv_rul                │
          │                       ▼
          ▼                  rag/physics_checker
     clpx/bridge
```

**Dependency rule:** No circular imports. Dependencies flow downward/rightward. Each module imports only from modules above it in the dependency graph.

---

## 3. INTERFACE CONTROL SPECIFICATIONS

### 3.1 ICD-01: Data Adapter → Preprocessor

```
Output of data_adapter.ingest():
Unified format from NASA SMAP/MSL, ESA-AD, C-MAPSS, OPS-SAT:

{
    "telemetry": np.ndarray,          # shape: (T, n, max_d) — padded feature tensor
    "feature_dims": List[int],         # [6, 5, 7, 6, 6, 5, 5, 4, 5, 5, 4, 5, 6] per node
    "timestamps": np.ndarray,          # shape: (T,) — Unix timestamps, 1 Hz
    "fault_labels": List[Dict],        # per-fault annotations
    "mission_phase": np.ndarray,       # shape: (T,) — phase ID per timestep
    "metadata": Dict                   # generation parameters for reproducibility
}
```

### 3.2 ICD-02: Preprocessor → Graph Builder + Local Detector

```
Output of preprocessor.process():

{
    "features_norm": np.ndarray,       # shape: (T, n, max_d) — z-score normalized
    "features_windowed": np.ndarray,   # shape: (T, n, max_d * 5) — mean/std/min/max/slope
    "masks": np.ndarray,               # shape: (T, n, max_d) — 1=real, 0=imputed
    "confidence": np.ndarray,          # shape: (T, n) — per-node confidence scores
    "timestamps": np.ndarray           # shape: (T,) — aligned timestamps
}
```

### 3.3 ICD-03: Local Detector → SDWAP

```
Output of local_detector.detect():

{
    "anomaly_scores": np.ndarray,      # shape: (T, n) — s_i(t) ∈ [0, 1]
    "detector_type": np.ndarray,       # shape: (T, n) — "zscore" or "iforest" (which fired)
    "raw_zscores": np.ndarray          # shape: (T, n) — for explainability
}
```

### 3.4 ICD-04: Graph Builder → TGN + SDWAP

```
Output of dynamic_builder.build():

{
    "adjacency": torch.Tensor,         # shape: (T, n, n) — W_t at each timestep
    "edge_index": torch.LongTensor,    # shape: (2, |E|) — PyG format edge index
    "edge_weight": torch.FloatTensor,  # shape: (|E|,) — edge weights
    "node_features": torch.FloatTensor # shape: (n, d) — current node features
}
```

### 3.5 ICD-05: TGN → Predictor + SDWAP + CLPX

```
Output of tgn.forward():

{
    "embeddings": torch.FloatTensor,   # shape: (n, 256) — z_i(t) per node
    "hidden_states": torch.FloatTensor,# shape: (n, 256) — h_i(t) per node
    "memory_states": torch.FloatTensor,# shape: (n, 256) — mem_i(t) per node
    "attention_weights": torch.FloatTensor # shape: (H, |E|) — for explainability
}
```

### 3.6 ICD-06: SDWAP → Predictor + NLG

```
Output of sdwap.propagate():

{
    "refined_scores": np.ndarray,      # shape: (n,) — A_i(t) per node
    "propagation_trace": List[Dict],   # per-iteration state for visualization
    "top_influences": Dict[int, List[Tuple[int, float]]]  # per node: top-3 influencers
}
```

### 3.7 ICD-07: Predictor → NLG + Dashboard

```
Output of predictor.predict():

{
    "failure_probs": np.ndarray,       # shape: (n,) — P_i^30(t) calibrated
    "hazard_bins": np.ndarray,         # shape: (n, 6) — 5-min bin probabilities
    "severity_level": List[str],       # per node: "nominal", "watch", "warning", "critical"
    "threshold_exceeded": List[bool]   # per node: True if P > θ_alert
}
```

### 3.8 ICD-08: THERMAL-DIFF-GNN → PhyRAG + RLV-RUL + CLPX

```
Output of thermal_diff_gnn.assess():

{
    "degradation_scores": np.ndarray,  # shape: (n_post,) — D_i per component
    "physics_component": np.ndarray,   # shape: (n_post,) — Φ_i per component
    "learned_component": np.ndarray,   # shape: (n_post,) — f_i per component
    "lambda_current": float,           # current physics-ML trust parameter
    "stress_graph": Dict               # G_post adjacency and features
}
```

### 3.9 ICD-09: PhyRAG → Requalification Report

```
Output of phyrag.explain():

{
    "explanation_text": str,           # generated diagnostic text
    "source_citations": List[Dict],    # {doc_name, section, similarity_score}
    "blocked_statements": List[str],   # statements that failed physics check
    "physics_scores": Dict[str, float],# per-statement physics constraint scores
    "confidence": float                # overall explanation confidence
}
```

### 3.10 ICD-10: CLPX → TGN (forward) + THERMAL-DIFF-GNN (backward)

```
Output of clpx.exchange():

{
    "shared_embedding": np.ndarray,    # shape: (128,) — E_shared
    "tgn_init_memory": np.ndarray,     # shape: (n, 256) — for next flight TGN init
    "postflight_mask": np.ndarray,     # shape: (n_post,) — attention mask for T-DIFF-GNN
    "alpha_current": float             # current flight/post trust balance
}
```

---

## 4. DATA SCHEMA DEFINITIONS

### 4.1 Telemetry HDF5 Schema

```
/telemetry.h5
├── /raw
│   ├── solar_array          (T × 6) float32
│   ├── power_bus             (T × 5) float32
│   ├── battery_pack          (T × 7) float32
│   ├── thermal_control       (T × 6) float32
│   ├── propulsion_main       (T × 6) float32
│   ├── eclss_air_handler     (T × 5) float32
│   ├── thermal_loop_1        (T × 5) float32
│   ├── radiator              (T × 4) float32
│   ├── propellant_tank       (T × 5) float32
│   ├── thruster_valve        (T × 5) float32
│   ├── co2_scrubber          (T × 4) float32
│   ├── attitude_control      (T × 5) float32
│   └── reaction_wheels       (T × 6) float32
├── /timestamps               (T,) float64 — Unix epoch seconds
├── /mission_phase             (T,) int8    — Phase ID [0-6]
└── /metadata
    ├── sampling_rate_hz       scalar int
    ├── generation_seed        scalar int
    └── duration_seconds       scalar int
```

### 4.2 Fault Labels JSON Schema

```json
{
    "faults": [
        {
            "fault_id": "F001",
            "fault_type": "cascade_failure",
            "onset_time": 12345.0,
            "failure_time": 14100.0,
            "root_cause_node": 2,
            "affected_nodes": [2, 1, 3],
            "severity": 0.7,
            "propagation_delays": {
                "2_to_1": 600.0,
                "1_to_3": 900.0
            },
            "parameters": {
                "drift_rate": null,
                "amplitude": null,
                "degradation_rate": 0.005
            }
        }
    ],
    "binary_labels": {
        "description": "Per-node, per-timestep binary failure labels (1 = failure within 30 min)",
        "shape": [86400, 13],
        "file": "binary_labels.npy"
    }
}
```

### 4.3 Configuration YAML Schema

```yaml
# config/default.yaml

system:
  name: "PRAJNA"
  version: "1.0"
  random_seed: 42

data:
  sampling_rate_hz: 1
  duration_hours: 24
  num_subsystems: 13
  feature_window_seconds: 60
  normalization: "zscore"
  imputation: "forward_fill"

graph:
  num_nodes: 13
  baseline_matrix: "config/graph_schema.yaml"
  dynamic_update: true
  ema_alpha: 0.1

sdwap:
  injection_rate: 0.3        # η
  damping_factor: 0.7        # γ
  temporal_decay: 0.1        # β
  iterations: 5              # K
  alert_threshold: 0.6       # θ

tgn:
  embedding_dim: 256
  attention_heads: 4
  time_encoding_dim: 64
  message_dim: 128
  dependency_coupling: 1.0   # λ
  dropout: 0.1
  gru_hidden_dim: 256

predictor:
  classifier_hidden: [128, 64]
  hazard_bins: 6
  hazard_bin_minutes: 5
  ensemble_method: "average"
  calibration: "platt"
  alert_thresholds:
    watch: 0.4
    warning: 0.6
    critical: 0.8

training:
  optimizer: "adamw"
  learning_rate: 0.0001
  weight_decay: 0.00001
  batch_size: 64
  max_epochs: 100
  early_stopping_patience: 10
  gradient_clip_norm: 1.0
  focal_loss_gamma: 2.0
  sdwap_loss_weight: 0.3
  recon_loss_weight: 0.1
  cosine_annealing: true

postflight:
  lambda_initial: 0.8
  lambda_adaptation_rate: 0.02
  lambda_min: 0.2
  lambda_max: 0.95
  gcn_layers: 2
  gcn_hidden_dim: 64

rlv_rul:
  safety_margin: 0.2         # Replace at D=0.8 instead of D=1.0

phyrag:
  embedding_model: "all-MiniLM-L6-v2"
  llm_model: "mistral"
  llm_temperature: 0.1
  top_k_docs: 5
  chunk_size: 512
  chunk_overlap: 128
  physics_threshold: 0.5

clpx:
  shared_dim: 128
  alpha_initial: 0.5
  alpha_adaptation_rate: 0.01
  alpha_min: 0.2
  alpha_max: 0.8

dashboard:
  host: "0.0.0.0"
  port: 5000
  refresh_interval_ms: 1000
  graph_layout: "force"

evaluation:
  metrics:
    - "roc_auc"
    - "pr_auc"
    - "f1"
    - "brier_score"
    - "median_lead_time"
    - "false_alarm_rate"
    - "rca_accuracy"
    - "requalification_accuracy"
    - "rul_mape"
```

---

## 5. CONFIGURATION MANAGEMENT

### 5.1 Configuration Hierarchy

```
Priority (highest to lowest):
  1. Command-line arguments (--sdwap.iterations=10)
  2. Environment variables (PRAJNA_SDWAP_ITERATIONS=10)
  3. config/default.yaml
  4. Built-in code defaults
```

### 5.2 Configuration Validation

All configuration values are validated at startup:

```
Validation rules:
  - All floats in [0, 1] where specified (rates, thresholds, damping)
  - Integer counts >= 1 (iterations, heads, layers)
  - Dimensions are powers of 2 or common values (64, 128, 256, 512)
  - File paths exist and are readable
  - YAML syntax is valid
  - No unknown keys (strict mode)
```

---

## 6. FILE SYSTEM LAYOUT

### 6.1 Runtime Directory Structure

```
prajna_workspace/
├── config/                     — Configuration files (version-controlled)
├── data/
│   ├── raw/                    — Downloaded real datasets (NASA, ESA, MOSDAC)
│   ├── processed/              — Preprocessed features (HDF5)
│   ├── labels/                 — Fault labels and binary targets (JSON, NPY)
│   └── knowledge_base/         — PhyRAG source documents (PDF, TXT, CSV)
├── models/
│   ├── checkpoints/            — Training checkpoints (PT files)
│   ├── best/                   — Best model weights selected by validation AUC
│   └── calibrator/             — Platt scaling parameters (JSON)
├── results/
│   ├── evaluation/             — Metric reports (JSON, HTML)
│   ├── ablation/               — Ablation study results (JSON, plots)
│   └── demo/                   — Demo run outputs (JSON, screenshots)
├── logs/                       — Structured log files (rotated daily)
├── vectordb/                   — ChromaDB persistent storage
└── docs/                       — This documentation
```

---

## 7. EXECUTION MODES

### 7.1 Training Mode

```
python scripts/train.py --config config/default.yaml

Pipeline:
  1. Download real data via data_adapter (NASA SMAP/MSL, ESA-AD, C-MAPSS)
  2. Preprocess → data/processed/
  3. Build graph (static W_base + learned Δw)
  4. Train TGN + SDWAP + Predictor jointly
  5. Save best checkpoint to models/best/
  6. Calibrate on validation set → models/calibrator/
  7. Log training metrics to logs/

Duration: ~30-60 minutes on Apple M2
```

### 7.2 Inference Mode (In-Flight)

```
python scripts/run_inference.py --config config/default.yaml --data data/raw/test.h5

Pipeline (per timestep):
  1. Read telemetry frame → preprocess
  2. Local anomaly detection
  3. Dynamic graph update
  4. TGN forward pass → embeddings
  5. SDWAP propagation → refined scores
  6. Failure prediction → calibrated probabilities
  7. If alert: NLG → contingency text
  8. Write output to JSON / push to dashboard

Latency: < 35 ms per timestep
```

### 7.3 Post-Flight Mode

```
python scripts/run_postflight.py --config config/default.yaml --flight_data data/raw/flight_007.h5

Pipeline:
  1. Load flight recorder data
  2. Build avionics stress graph
  3. THERMAL-DIFF-GNN → degradation scores
  4. RLV-RUL → remaining life estimates
  5. PhyRAG → explainable diagnostics
  6. CLPX → update shared embeddings
  7. Generate requalification report (JSON + HTML)
```

### 7.4 Dashboard Mode

```
python scripts/run_dashboard.py --config config/default.yaml

Launches Flask server at http://localhost:5000
Serves:
  - Real-time graph visualization (D3.js)
  - Telemetry time-series plots (Chart.js)
  - 30-minute prediction gauges
  - Alert panel with NLG output
  - SDWAP cascade trace visualization
  - Post-flight requalification view (mode switch)
```

---

## 8. ERROR HANDLING STRATEGY

### 8.1 Error Categories

| Category | Example | Response |
|----------|---------|----------|
| Data error | Missing sensor channel, corrupt HDF5 | Log warning, impute with last-known value, set confidence = 0.1 |
| Model error | NaN in gradients, exploding loss | Roll back to previous checkpoint, reduce learning rate by 0.5× |
| Inference error | SDWAP non-convergence | Fall back to local anomaly scores only, log alert |
| RAG error | Ollama not running, ChromaDB empty | Return "diagnostic unavailable" with raw scores only |
| Config error | Invalid parameter value | Fail fast at startup with descriptive error message |

### 8.2 Graceful Degradation

PRAJNA is designed to degrade gracefully when components fail:

```
Full system → SDWAP + TGN + Predictor + NLG + RAG      (normal operation)
Without RAG → SDWAP + TGN + Predictor + NLG            (no explanations, scores still valid)
Without NLG → SDWAP + TGN + Predictor                  (raw numbers on dashboard)
Without TGN → SDWAP with local scores only              (reduced accuracy, still functional)
Without SDWAP → Local anomaly scores per-node           (baseline mode, no cascade detection)
```

---

## 9. SECURITY ARCHITECTURE

### 9.1 Air-Gap Compliance

| Component | Network Requirement | Air-Gap Status |
|-----------|-------------------|----------------|
| PyTorch inference | None | COMPLIANT |
| Ollama + Mistral-7B | None (pre-downloaded model) | COMPLIANT |
| ChromaDB | None (local persistency) | COMPLIANT |
| LlamaIndex | None (local embeddings) | COMPLIANT |
| Flask dashboard | Localhost only (127.0.0.1 or 0.0.0.0) | COMPLIANT |
| pip dependencies | Required during initial setup only | Install before air-gap |

### 9.2 Data Classification

| Data Type | Classification | Handling |
|-----------|---------------|----------|
| Real mission telemetry | UNRESTRICTED | Publicly available NASA/ESA datasets (no ISRO classified data) |
| Configuration | UNRESTRICTED | Hyperparameters only |
| Model weights | UNRESTRICTED | Trained on public NASA/ESA data only |
| Knowledge base docs | UNRESTRICTED | Public datasheets and standards only |
| Dashboard output | UNRESTRICTED | Derived from publicly available data |

**Note:** If PRAJNA is ever connected to real ISRO telemetry, all data and model weights trained on real data would inherit the classification level of the source telemetry.

### 9.3 Input Validation

All external inputs (configuration files, telemetry data files) are validated:

- YAML parsing with strict mode (no arbitrary code execution)
- HDF5 dataset shape validation against expected schema
- Numeric range checking on all telemetry values
- Path traversal prevention on file operations
- **AEGIS 3-layer adversarial guard** (spectral + autoencoder + temporal consistency)

---

## 10. ADVANCED MODULES (INTERFACE SPECIFICATIONS)

### ICD-11: Telemetry → AEGIS Guard

```
Interface: ICD-11
Producer: Data Pipeline (preprocessor)
Consumer: AEGIS Guard (aegis/ensemble_decision.py)
Data: Preprocessed telemetry tensor {x_i(t)} ∈ R^{N×d}
Protocol: In-process function call
AEGIS Output: Integrity-scored tensor {x'_i(t), integrity_score_i(t), decision_i}
  where decision ∈ {PASS, FLAG, BLOCK}
  FLAG: confidence_i *= (1 - AEGIS_score)
  BLOCK: x_i replaced with last_known_good, confidence_i = 0.1
```

### ICD-12: Predictor → SHAKTI Conformal Wrapper

```
Interface: ICD-12
Producer: Failure Predictor / THERMAL-DIFF-GNN
Consumer: SHAKTI (shakti/conformal_wrapper.py)
Data: Point prediction P_i(t) or D_i(flight)
Protocol: In-process function call
SHAKTI Output: ConformalPrediction {
  point: float,
  lower_bound: float,  # at 99% coverage
  upper_bound: float,
  coverage_level: float,
  calibration_size: int
}
```

### ICD-13: Decisions → KAVACH Verifier

```
Interface: ICD-13
Producer: Decision Engine (post-flight or in-flight)
Consumer: KAVACH (kavach/runtime_verifier.py)
Data: List[ComponentDecision] with D_i, RUL_i, Decision_i
Protocol: In-process function call
KAVACH Output: VerifiedDecisions {
  decisions: List[ComponentDecision],  # potentially overridden
  violations: List[Violation],
  overrides: List[Override],
  safety_case: GSN  # machine-readable safety argumentation
}
```

### ICD-14: VAYUH Federation Protocol

```
Interface: ICD-14
Producer: Local PRAJNA instance (any satellite)
Consumer: VAYUH Aggregation Server (vayuh/fed_server.py)
Data: Gradient deltas Δθ_k (clipped, DP-noised)
Protocol: File-based exchange (air-gap compliant)
Schedule: After each local training epoch
VAYUH Output: Updated global model weights θ_global
```

### ICD-15: PRAJNA → NETRA Sync

```
Interface: ICD-15
Producer: Ground PRAJNA (full model)
Consumer: NETRA (onboard edge model)
Data (uplink): Model weight delta (≤50KB compressed)
Data (downlink): Anomaly summary (≤1KB per orbit)
Protocol: File-based exchange via ground station pass
Sync Criteria: |NETRA_score - PRAJNA_score| > δ_sync (0.15)
```

### 10.1 Extended File System Layout

```
prajna/
├── data/            — (unchanged from core)
├── graph/           — (unchanged)
├── engine/          — (unchanged)
├── models/          — (unchanged)
├── evaluation/      — (unchanged)
├── training/        — (unchanged)
├── utils/           — (unchanged)
├── rag/             — (unchanged)
├── nlg/             — (unchanged)
├── clpx/            — (unchanged)
│
├── aegis/           — NEW: Adversarial Guard
│   ├── spectral_detector.py
│   ├── autoencoder_guard.py
│   ├── temporal_checker.py
│   └── ensemble_decision.py
│
├── shakti/          — NEW: Conformal Prediction
│   ├── conformal_wrapper.py
│   ├── adaptive_ci.py
│   ├── calibration_store.py
│   └── coverage_monitor.py
│
├── vayuh/           — NEW: Federated Learning
│   ├── fed_server.py
│   ├── fed_client.py
│   ├── privacy.py
│   ├── schema_harmonizer.py
│   └── communication.py
│
├── kavach/          — NEW: Formal Verification
│   ├── safety_properties.py
│   ├── runtime_verifier.py
│   ├── interval_propagation.py
│   ├── safety_case_gen.py
│   └── override_engine.py
│
└── netra/           — NEW: Edge Deployment
    ├── micro_tgn.py
    ├── fast_sdap.py
    ├── distillation.py
    ├── quantizer.py
    └── sync_protocol.py
```

---

**END OF DOCUMENT**

**Document Number:** PRAJNA/ARCH/2026/001  
**Version:** 1.1  
**Classification:** UNRESTRICTED — FOR REVIEW

---
