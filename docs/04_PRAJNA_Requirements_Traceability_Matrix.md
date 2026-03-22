# PRAJNA — Requirements Traceability Matrix

## Mapping System Capabilities to ISRO Requirements

---

**Document Number:** PRAJNA/RTM/2026/001  
**Version:** 1.0  
**Date of Issue:** 06 March 2026  
**Classification:** UNRESTRICTED — FOR REVIEW  
**Prepared for:** Indian Space Research Organisation (ISRO)  
**Prepared by:** Karthik  

---

## TABLE OF CONTENTS

1. [Purpose](#1-purpose)
2. [Requirements Sources](#2-requirements-sources)
3. [Forward Traceability — ISRO Requirements to PRAJNA](#3-forward-traceability--isro-requirements-to-prajna)
4. [Backward Traceability — PRAJNA Features to Requirements](#4-backward-traceability--prajna-features-to-requirements)
5. [Functional Requirements Traceability](#5-functional-requirements-traceability)
6. [Non-Functional Requirements Traceability](#6-non-functional-requirements-traceability)
7. [Coverage Summary](#7-coverage-summary)

---

## 1. PURPOSE

This Requirements Traceability Matrix (RTM) provides bidirectional mapping between ISRO's documented requirements (from RESPOND Basket calls, VSSC priorities, and ISTRAC initiatives) and PRAJNA's system capabilities. It ensures every ISRO requirement is addressed and every PRAJNA feature traces to a motivated need.

---

## 2. REQUIREMENTS SOURCES

| Source ID | Source Name | Authority | Year |
|-----------|-----------|-----------|------|
| SRC-01 | RESPOND Basket 2023-2024 | ISRO HQ, Bengaluru | 2023-2024 |
| SRC-02 | RESPOND Basket 2025 | ISRO/VSSC, Thiruvananthapuram | 2025 |
| SRC-03 | VSSC AI Framework Priority | VSSC, Thiruvananthapuram | 2024 |
| SRC-04 | ISTRAC MuST Initiative | ISTRAC, Bengaluru | 2024 |
| SRC-05 | RLV-TD Programme Requirements | VSSC/ISRO | 2023-2026 |
| SRC-06 | ISRO Security Policy (inferred) | ISRO HQ | Standing |
| SRC-07 | ISRO Academic Compatibility | ISRO HQ | Standing |

---

## 3. FORWARD TRACEABILITY — ISRO REQUIREMENTS TO PRAJNA

### 3.1 RESPOND Basket 2023-2024 (SRC-01)

| Req ID | ISRO Requirement Text | PRAJNA Module | Algorithm | TDD Section | Verification |
|--------|----------------------|---------------|-----------|-------------|--------------|
| R-01-01 | ML-based spacecraft telemetry anomaly detection | In-flight module | SDWAP + TGN | §8.1, §8.2 | ROC-AUC > 0.92, PR-AUC > 0.75 |
| R-01-02 | Detection of previously unseen anomaly patterns | Evaluation framework | TGN generalization | §11, §3.2 (Eval) | 5 unseen fault combos in test set |
| R-01-03 | Multi-variate telemetry analysis | Graph layer | Dynamic graph builder | §6.1, §7.1 | 13 subsystems, 69 features |
| R-01-04 | Reduce false alarm rate vs current systems | SDWAP + Predictor | Confidence weighting + calibration | §8.1.3, §10 | FAR < 3/day |

### 3.2 RESPOND Basket 2025 (SRC-02)

| Req ID | ISRO Requirement Text | PRAJNA Module | Algorithm | TDD Section | Verification |
|--------|----------------------|---------------|-----------|-------------|--------------|
| R-02-01 | AI-powered post-flight avionics requalification | Post-flight module | THERMAL-DIFF-GNN | §8.3 | Requalification accuracy > 85% |
| R-02-02 | Component-level health assessment after RLV landing | Requalification engine | RLV-RUL + PhyRAG | §8.5, §8.4 | Per-component GO/AMBER/REJECT |
| R-02-03 | Remaining useful life estimation for reusable components | RLV-RUL module | Triple-mode RUL | §8.5 | MAPE < 15% |
| R-02-04 | Explainable AI outputs for engineering review | PhyRAG + NLG | Physics-constraint RAG | §8.4 | Source-cited, physics-validated |

### 3.3 VSSC AI Framework Priority (SRC-03)

| Req ID | ISRO Requirement Text | PRAJNA Module | Algorithm | TDD Section | Verification |
|--------|----------------------|---------------|-----------|-------------|--------------|
| R-03-01 | Offline, hallucination-free AI decision support | PhyRAG engine | Physics constraint checker | §8.4.5 | All statements physics-validated |
| R-03-02 | Grounded in engineering documentation | Knowledge base | ChromaDB + LlamaIndex | §8.4.4 (TDD) | Each claim cites source document |
| R-03-03 | Deterministic, reproducible results | Training framework | Fixed seeds, deterministic ops | §10 (TDD) | Reproduces ±0.01 across runs |

### 3.4 ISTRAC MuST Initiative (SRC-04)

| Req ID | ISRO Requirement Text | PRAJNA Module | Algorithm | TDD Section | Verification |
|--------|----------------------|---------------|-----------|-------------|--------------|
| R-04-01 | Multi-satellite telemetry analysis capability | Graph architecture | Scalable graph builder | §6.3, §NFR-05 | Supports 13-50 nodes |
| R-04-02 | Integrated monitoring across subsystems | Graph + SDWAP | Dependency propagation | §8.1, §7 | Cross-subsystem cascade detection |

### 3.5 RLV-TD Programme (SRC-05)

| Req ID | ISRO Requirement Text | PRAJNA Module | Algorithm | TDD Section | Verification |
|--------|----------------------|---------------|-----------|-------------|--------------|
| R-05-01 | Reusable vehicle turnaround optimization | Post-flight module | Full pipeline | §6.2 | Maintenance priority queue |
| R-05-02 | Cross-flight learning and improvement | CLPX bridge | Pattern exchange | §8.6 | Accuracy improves flight 3+ |
| R-05-03 | Physics-based component assessment | THERMAL-DIFF-GNN | Coffin-Manson + GNN | §8.3 | Adaptive λ (physics-dominant initially) |

### 3.6 ISRO Security Policy (SRC-06)

| Req ID | ISRO Requirement Text | PRAJNA Module | Approach | TDD Section | Verification |
|--------|----------------------|---------------|----------|-------------|--------------|
| R-06-01 | Air-gapped operation (no internet) | All modules | Ollama local LLM, ChromaDB local, no HTTP | §13, ICD §9 | Zero network calls in inference |
| R-06-02 | Data classification compliance | Data handling | Public NASA/ESA data (UNRESTRICTED) | ICD §9.2 | All data is publicly available datasets |
| R-06-03 | Input validation against injection | Config/data loaders | YAML strict mode, schema validation | ICD §9.3 | Path traversal prevention, range checks |

### 3.7 Academic Compatibility (SRC-07)

| Req ID | ISRO Requirement Text | PRAJNA Module | Approach | TDD Section | Verification |
|--------|----------------------|---------------|----------|-------------|--------------|
| R-07-01 | Python ecosystem | All code | Python 3.11+ | §13.2 | pip-installable |
| R-07-02 | Consumer hardware deployment | All modules | CPU inference, <2 GB RAM | §13.1, §NFR-02 | Tested on MacBook Air M2 |
| R-07-03 | Open-source, zero cost | Dependencies | BSD/MIT/Apache 2.0 only | §13.2 | ₹0 total |

---

## 4. BACKWARD TRACEABILITY — PRAJNA FEATURES TO REQUIREMENTS

This section verifies that every major PRAJNA feature traces to at least one ISRO requirement.

| PRAJNA Feature | PRAJNA Module | Traced To |
|---------------|---------------|-----------|
| Dynamic dependency graph (13 nodes) | graph/ | R-01-03, R-04-02 |
| SDWAP anomaly propagation | engine/sdwap | R-01-01, R-01-04, R-04-02 |
| Temporal GNN node embeddings | engine/tgn | R-01-01, R-01-02 |
| Local anomaly detection (z-score + iForest) | engine/local_detector | R-01-01 |
| 30-minute failure prediction | models/predictor | R-01-01, R-01-04 |
| Calibrated probability output | models/calibrator | R-01-04, R-03-03 |
| Contingency NLG | nlg/ | R-02-04, R-03-01 |
| SDWAP propagation trace | nlg/explainability | R-02-04, R-03-01 |
| THERMAL-DIFF-GNN degradation scoring | models/thermal_diff_gnn | R-02-01, R-05-03 |
| PhyRAG explanations | rag/ | R-02-04, R-03-01, R-03-02 |
| RLV-RUL triple-mode estimation | models/rlv_rul | R-02-03 |
| GO/AMBER/REJECT decisions | Requalification engine | R-02-01, R-02-02, R-05-01 |
| CLPX cross-lifecycle transfer | clpx/ | R-05-02 |
| Maintenance priority queue | Post-flight output | R-05-01 |
| Operator dashboard (D3.js + Chart.js) | Dashboard | R-02-04, R-04-01 |
| Real data ingestion pipeline | data/data_adapter | R-01-02 (enables training + testing) |
| Offline operation | All modules | R-06-01 |
| Evaluation + ablation framework | evaluation/ | R-01-01 (validation) |

**Coverage check:** Every PRAJNA feature traces to at least one ISRO requirement. No orphaned features.

---

## 5. FUNCTIONAL REQUIREMENTS TRACEABILITY

| FR ID | Functional Requirement | Source Req | Implementing Module | Test Method |
|-------|----------------------|-----------|-------------------|-------------|
| FR-01 | Ingest 13-subsystem telemetry at 1-100 Hz | R-01-03 | data/preprocessor | Unit test: verify data shapes |
| FR-02 | Construct dynamic dependency graph G_t | R-04-02 | graph/dynamic_builder | Unit test: verify edge weights evolve |
| FR-03 | Compute local anomaly scores per subsystem | R-01-01 | engine/local_detector | Unit test: known anomaly → score > 0.5 |
| FR-04 | Propagate scores via SDWAP (K=5, configurable) | R-01-01 | engine/sdwap | Unit test: convergence < 0.01 residual |
| FR-05 | Produce TGN node embeddings z_i(t) ∈ R^256 | R-01-01 | engine/tgn | Unit test: output shape (13, 256) |
| FR-06 | Predict 30-min failure probability per node | R-01-01 | models/predictor | Integration test: known fault → P > 0.6 |
| FR-07 | Generate template-based contingency text | R-02-04 | nlg/template_renderer | Unit test: output contains action + root cause |
| FR-08 | Provide explainability: top-3 nodes, SDWAP trace | R-03-01 | nlg/explainability | Unit test: trace length > 0 for alert |
| FR-09 | Accept post-flight telemetry dumps | R-02-01 | Post-flight ingestion | Unit test: parse HDF5 flight data |
| FR-10 | Estimate degradation via THERMAL-DIFF-GNN | R-02-01 | models/thermal_diff_gnn | Unit test: D_i ∈ [0, 1] |
| FR-11 | GO/NO-GO decisions with PhyRAG explanations | R-02-02 | Requalification engine + RAG | Integration test: damaged component → REJECT |
| FR-12 | Triple-mode RUL per component | R-02-03 | models/rlv_rul | Unit test: known params → expected RUL |
| FR-13 | CLPX cross-lifecycle transfer | R-05-02 | clpx/bridge | Integration test: accuracy improves by flight 5 |
| FR-14 | Web dashboard with graph, telemetry, alerts | R-04-01 | Dashboard (Flask) | Manual validation: visual inspection |
| FR-15 | Fully offline operation | R-06-01 | All modules | Integration test: no network calls |

---

## 6. NON-FUNCTIONAL REQUIREMENTS TRACEABILITY

| NFR ID | Requirement | Specification | Source Req | Verification Method |
|--------|------------|---------------|-----------|-------------------|
| NFR-01 | Inference latency | ≤ 2 seconds end-to-end | R-01-01 | Profiling: measure per-timestep |
| NFR-02 | Memory footprint | < 2 GB RAM total | R-07-02 | Monitor RSS during inference |
| NFR-03 | Platform support | Python 3.11+, macOS/Linux | R-07-01 | CI on both platforms |
| NFR-04 | Offline operation | Zero network dependencies | R-06-01 | Network monitor during full pipeline |
| NFR-05 | Scalability | 13-50 nodes without architecture change | R-04-01 | Test with multi-mission ESA-AD graph |
| NFR-06 | Data formats | CSV, HDF5, JSON input; JSON + HTML output | R-07-01 | Format validation tests |
| NFR-07 | Reproducibility | Fixed seeds, deterministic training | R-03-03 | Run 2× with same seed, diff < 0.01 |
| NFR-08 | Test coverage | >80% code coverage | R-07-01 | pytest --cov report |

---

## 7. COVERAGE SUMMARY

### 7.1 Requirements Coverage

```
Total ISRO requirement items identified:  26
Requirements addressed by PRAJNA:         26  (100%)
Requirements partially addressed:          0  (0%)
Requirements not addressed:                0  (0%)
```

### 7.2 Feature Coverage

```
Total PRAJNA features:                    25
Features with requirement traceability:   25  (100%)
Orphaned features (no requirement):        0  (0%)
```

### 7.3 Traceability Summary Table

```
┌─────────────────────────────────────────────────────────────────┐
│                  REQUIREMENTS COVERAGE MATRIX                    │
│                                                                 │
│  ISRO Source          │ Requirements │ Addressed │ Coverage     │
│  ─────────────────────┼──────────────┼───────────┼──────────── │
│  RESPOND 2023-24      │      4       │     4     │   100%      │
│  RESPOND 2025         │      4       │     4     │   100%      │
│  VSSC AI Priority     │      3       │     3     │   100%      │
│  ISTRAC MuST          │      3       │     3     │   100%      │
│  RLV-TD Programme     │      3       │     3     │   100%      │
│  Security Policy      │      4       │     4     │   100%      │
│  Academic Compat.     │      3       │     3     │   100%      │
│  Gaganyaan Programme  │      2       │     2     │   100%      │
│  ─────────────────────┼──────────────┼───────────┼──────────── │
│  TOTAL                │     26       │    26     │   100%      │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 New Requirements Addressed by Advanced Capabilities

| Req ID | Source | Requirement | PRAJNA Feature |
|--------|--------|-------------|----------------|
| R-04-03 | ISTRAC MuST | Fleet-wide multi-satellite telemetry learning | VAYUH federated learning with DP |
| R-06-04 | Security Policy | Protection against adversarial telemetry manipulation | AEGIS 3-layer ensemble guard |
| R-08-01 | Gaganyaan | Onboard real-time autonomous health monitoring | NETRA edge-deployed model (45KB) |
| R-08-02 | Gaganyaan | Safety-certified AI decision support | KAVACH formal verification + SHAKTI conformal guarantees |

### 7.4 Novel Contributions Beyond Requirements

PRAJNA also provides capabilities not explicitly requested but valuable:

| Extra Capability | Description | Potential ISRO Value |
|-----------------|-------------|---------------------|
| CLPX cross-lifecycle learning | Automatic improvement across flights | Reduces time-to-accuracy for new vehicle programs |
| SHAKTI conformal predictions | 99% coverage-guaranteed prediction intervals | Mathematically proven safety for operator decisions |
| KAVACH safety case generation | Automated GSN safety argumentation | Potentially audit-ready safety evidence |
| VAYUH privacy-preserving FL | DP-protected federated model updates | Constellation-wide AI without compromising data classification |
| NETRA edge deployment | 45KB onboard model with knowledge distillation | Future-proofs for deep-space / Gaganyaan autonomous ops |
| 10 ablation studies | Rigorous scientific validation of each component | Publishable research results for ISRO |
| 7 stress test protocols | Extended robustness validation | Builds confidence for operational consideration |
| Graceful degradation | System continues operating with component failures | Operational resilience |
| FMEA safety analysis | Failure Mode and Effects Analysis for all 10 modules | Safety assurance evidence |

---

**END OF DOCUMENT**

**Document Number:** PRAJNA/RTM/2026/001  
**Version:** 1.1  
**Classification:** UNRESTRICTED — FOR REVIEW  

---
