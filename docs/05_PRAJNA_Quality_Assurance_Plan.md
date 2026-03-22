# PRAJNA — Quality Assurance Plan

## Verification, Validation, and Quality Control

---

**Document Number:** PRAJNA/QAP/2026/001  
**Version:** 1.0  
**Date of Issue:** 06 March 2026  
**Classification:** UNRESTRICTED — FOR REVIEW  
**Prepared for:** Indian Space Research Organisation (ISRO)  
**Prepared by:** Karthik  
**Applicable Standards:** ECSS-Q-ST-80C (Software Product Assurance), IEEE 730-2014 (SQA Plans)  

---

## TABLE OF CONTENTS

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Applicable Documents and Standards](#2-applicable-documents-and-standards)
3. [Organisation and Responsibilities](#3-organisation-and-responsibilities)
4. [Quality Objectives](#4-quality-objectives)
5. [Software Development Lifecycle](#5-software-development-lifecycle)
6. [Configuration Management](#6-configuration-management)
7. [Verification Strategy](#7-verification-strategy)
8. [Validation Strategy](#8-validation-strategy)
9. [Testing Programme](#9-testing-programme)
10. [Code Quality Controls](#10-code-quality-controls)
11. [Review and Audit Programme](#11-review-and-audit-programme)
12. [Defect Management](#12-defect-management)
13. [Risk-Based Quality Priorities](#13-risk-based-quality-priorities)
14. [Quality Metrics and Reporting](#14-quality-metrics-and-reporting)
15. [Delivery and Acceptance](#15-delivery-and-acceptance)

---

## 1. PURPOSE AND SCOPE

### 1.1 Purpose

This Quality Assurance Plan (QAP) defines the processes, standards, and controls that ensure the PRAJNA system meets ISRO's requirements for software quality, correctness, and scientific rigour. It governs all software artefacts from design through delivery.

### 1.2 Scope

This QAP covers:

- All Python source code in the `prajna/` package
- Configuration files (`config/`)
- Test suites (`tests/`)
- Documentation (`docs/`)
- Real data ingestion adapters (`prajna/data/`)
- Build and deployment scripts (`scripts/`)

### 1.3 Out of Scope

- Hardware procurement and qualification
- ISRO classified telemetry data handling (PRAJNA uses publicly available NASA/ESA data only)
- Operational deployment to ground station environments (requires separate ISRO QA)

---

## 2. APPLICABLE DOCUMENTS AND STANDARDS

| Standard | Title | Applicability |
|----------|-------|---------------|
| ECSS-Q-ST-80C | Space Product Assurance — Software Product Assurance | Overall QA framework |
| IEEE 730-2014 | Standard for Software Quality Assurance Plans | QAP structure |
| IEEE 829-2008 | Standard for Software Test Documentation | Test reporting format |
| ECSS-E-ST-40C | Space Engineering — Software | Development lifecycle |
| PEP 8 | Style Guide for Python Code | Code formatting |
| PEP 257 | Docstring Conventions | Documentation |
| PRAJNA/TDD/2026/001 | PRAJNA Technical Design Document | Requirements source |
| PRAJNA/ALS/2026/001 | PRAJNA Algorithm Specification | Algorithm validation baseline |
| PRAJNA/EVL/2026/001 | PRAJNA Evaluation Framework | Test criteria and protocols |
| PRAJNA/RTM/2026/001 | PRAJNA Requirements Traceability Matrix | Requirements coverage |

---

## 3. ORGANISATION AND RESPONSIBILITIES

### 3.1 Roles

| Role | Responsibility | Personnel |
|------|---------------|-----------|
| Developer / Quality Owner | Code development, unit tests, code review, QA compliance | Karthik |
| Technical Advisor | Design review, algorithm correctness audit | ISRO Mentor (TBD) |
| Independent Reviewer | Final acceptance review | ISRO Evaluation Panel |

### 3.2 Quality Decision Authority

For this internship project, quality decisions follow:

```
Developer self-review → ISRO mentor review → ISRO panel acceptance
```

All quality gates are documented in Section 11 (Review and Audit Programme).

---

## 4. QUALITY OBJECTIVES

| ID | Objective | Metric | Target |
|----|-----------|--------|--------|
| QO-01 | Functional correctness | All FR-01 to FR-15 pass verification | 100% pass |
| QO-02 | Code coverage | Line coverage via pytest-cov | > 80% |
| QO-03 | Zero critical defects at delivery | Open critical/blocker defects | 0 |
| QO-04 | Algorithm accuracy | Meets all acceptance criteria (Eval Framework §6) | All metrics ≥ minimum threshold |
| QO-05 | Reproducibility | Same seed → same results | Variance < 0.01 across runs |
| QO-06 | Documentation completeness | All 9 documents delivered, internally consistent | 100% delivered |
| QO-07 | Security compliance | No known vulnerabilities, air-gap validated | Zero network calls |

---

## 5. SOFTWARE DEVELOPMENT LIFECYCLE

### 5.1 Lifecycle Model

PRAJNA follows a **modified V-model** adapted for a single-developer research project:

```
                    Requirements
                   /            \
              Design              Acceptance Test
             /      \            /
    Detailed Design   System Test
           /              /
     Implementation → Unit Test → Integration Test
```

### 5.2 Phase Gates

| Phase | Entry Criteria | Exit Criteria | Artefacts |
|-------|---------------|---------------|-----------|
| Requirements | ISRO RESPOND call received | TDD approved, RTM complete | TDD, RTM |
| Design | TDD approved | Algorithm Spec + ICD approved | ALS, ICD |
| Implementation | Design docs approved | All code written, unit tests pass | Source code, unit tests |
| Integration Testing | All modules unit-tested | All integration tests pass, >80% coverage | Test reports |
| System Validation | Integration tests pass | All acceptance criteria met (Eval Framework) | Evaluation report |
| Delivery | System validation complete | All docs + code packaged, QA checklist signed | Delivery package |

### 5.3 Implementation Order (Risk-Ordered)

1. Data pipeline and real data ingestion adapters
2. Graph construction and SDWAP
3. TGN model and training loop
4. Dual predictor and calibration
5. THERMAL-DIFF-GNN post-flight module
6. RLV-RUL estimation
7. PhyRAG pipeline (depends on Ollama setup)
8. CLPX bridge
9. NLG and explanations
10. Dashboard (Flask + Chart.js)
11. Evaluation framework and ablation studies

---

## 6. CONFIGURATION MANAGEMENT

### 6.1 Version Control

- **Tool:** Git (local repository)
- **Branching:** Single `main` branch with tagged releases
- **Tags:** Semantic versioning: `v0.1.0` (data pipeline) → `v1.0.0` (delivery)
- **Commit Messages:** Conventional format: `type(scope): description`
  - Types: `feat`, `fix`, `test`, `docs`, `refactor`, `perf`
  - Example: `feat(sdwap): implement K-step propagation with convergence check`

### 6.2 Baseline Control

| Baseline | Content | Gate |
|----------|---------|------|
| B0 — Documentation baseline | All 9 documents | Design review complete |
| B1 — Code alpha | Core engine (data + graph + SDWAP + TGN + predictor) | Unit tests pass |
| B2 — Code beta | All modules integrated | Integration tests pass, >80% coverage |
| B3 — Release candidate | Full system + evaluation results | Acceptance criteria met |
| B4 — Delivery | Final package with all artefacts | QA checklist signed |

### 6.3 Configuration Items

| CI ID | Item | Format | Location |
|-------|------|--------|----------|
| CI-01 | Source code | Python (.py) | `prajna/` |
| CI-02 | Test suites | Python (.py) | `tests/` |
| CI-03 | Configuration | YAML | `config/` |
| CI-04 | Documentation | Markdown (.md) | `docs/` |
| CI-05 | Dependencies | Text | `requirements.txt` |
| CI-06 | Scripts | Shell/Python | `scripts/` |
| CI-07 | Trained models | PyTorch (.pt) | `outputs/models/` |
| CI-08 | Evaluation results | JSON + HTML | `outputs/reports/` |

---

## 7. VERIFICATION STRATEGY

### 7.1 Verification Methods

| Method | Description | Applied To |
|--------|-------------|-----------|
| Inspection | Manual document review | All documentation |
| Static Analysis | Automated linting and type checking | All Python code |
| Unit Testing | Automated function-level tests | All modules |
| Integration Testing | Automated module-interface tests | Module boundaries |
| System Testing | End-to-end pipeline execution | Full pipeline |
| Performance Testing | Latency and memory profiling | Inference path |
| Security Testing | Air-gap validation, input fuzzing | All entry points |

### 7.2 Verification Matrix

| Requirement | Inspection | Static | Unit | Integration | System | Perf | Security |
|-------------|:---------:|:------:|:----:|:-----------:|:------:|:----:|:--------:|
| FR-01 to FR-08 (In-flight) | | ✓ | ✓ | ✓ | ✓ | ✓ | |
| FR-09 to FR-13 (Post-flight) | | ✓ | ✓ | ✓ | ✓ | | |
| FR-14 (Dashboard) | ✓ | ✓ | | ✓ | ✓ | | |
| FR-15 (Offline) | | | | | ✓ | | ✓ |
| NFR-01 (Latency) | | | | | | ✓ | |
| NFR-02 (Memory) | | | | | | ✓ | |
| NFR-04 (Offline) | | | | | ✓ | | ✓ |
| NFR-07 (Reproducibility) | | | ✓ | | ✓ | | |
| NFR-08 (Coverage) | | | ✓ | | | | |
| Docs (all 9) | ✓ | | | | | | |

---

## 8. VALIDATION STRATEGY

### 8.1 Scientific Validation

PRAJNA is a research prototype. Validation follows the Evaluation Framework (PRAJNA/EVL/2026/001):

1. **Metric validation:** 10 quantitative metrics against acceptance thresholds
2. **Ablation validation:** 7 ablation studies proving each component's contribution
3. **Stress validation:** 5 stress tests proving robustness to degraded inputs
4. **Scenario validation:** 5 operational scenarios simulating realistic conditions

### 8.2 Acceptance Criteria (Summary)

| Metric | Target | Minimum | Fail |
|--------|--------|---------|------|
| ROC-AUC | ≥ 0.95 | ≥ 0.92 | < 0.90 |
| PR-AUC | ≥ 0.80 | ≥ 0.75 | < 0.70 |
| F1 (threshold=0.5) | ≥ 0.82 | ≥ 0.78 | < 0.72 |
| Mean Lead Time | ≥ 12 min | ≥ 8 min | < 5 min |
| False Alarm Rate | ≤ 2/day | ≤ 3/day | > 5/day |
| RCA Top-3 Accuracy | ≥ 80% | ≥ 70% | < 60% |
| Brier Score | ≤ 0.08 | ≤ 0.12 | > 0.15 |
| Requalification Accuracy | ≥ 90% | ≥ 85% | < 80% |
| RUL MAPE | ≤ 12% | ≤ 15% | > 20% |
| SDWAP Fidelity | ≥ 0.90 | ≥ 0.85 | < 0.80 |

Full justification and measurement methodology in PRAJNA/EVL/2026/001.

---

## 9. TESTING PROGRAMME

### 9.1 Test Levels

#### 9.1.1 Unit Tests

- **Framework:** pytest 7.x
- **Location:** `tests/unit/`
- **Naming:** `test_<module>_<function>.py`
- **Isolation:** Mocked dependencies, no file I/O, no network calls
- **Coverage target:** > 80% line coverage

**Key unit test areas:**

| Module | Test Focus | Est. Test Count |
|--------|-----------|----------------|
| data/preprocessor | Normalisation, NaN handling, shape checks | 12 |
| data/data_adapter | Format adapter correctness, multi-dataset ingestion | 10 |
| graph/dynamic_builder | Edge weight computation, adjacency matrix properties | 8 |
| engine/sdwap | Convergence, boundary conditions, K-step correctness | 10 |
| engine/local_detector | z-score + iForest anomaly scores | 6 |
| engine/tgn | Forward pass shapes, Time2Vec output range | 8 |
| models/predictor | Output probability range [0,1], gradient flow | 6 |
| models/thermal_diff_gnn | Degradation score range [0,1], physics constraint | 8 |
| models/rlv_rul | Mode outputs, combined RUL = min logic | 6 |
| rag/physics_checker | Constraint pass/fail on known inputs | 8 |
| clpx/bridge | Embedding transfer, trust adaptation logic | 6 |
| nlg/template_renderer | Template population completeness | 5 |
| **TOTAL** | | **~93** |

#### 9.1.2 Integration Tests

- **Location:** `tests/integration/`
- **Focus:** Module interface contracts (ICD-01 through ICD-10)
- **Data:** Real test fixtures from NASA/ESA datasets (labeled anomalies and nominal segments)

**Key integration tests:**

| Test ID | Interfaces Tested | Input | Expected Output |
|---------|------------------|-------|----------------|
| IT-01 | ICD-01: Preprocessor → Graph | Raw telemetry CSV | Valid dependency graph G_t |
| IT-02 | ICD-02: Graph → SDWAP | Graph + local scores | Propagated scores S_sdwap |
| IT-03 | ICD-03: SDWAP → TGN | Scores + features | Embeddings z ∈ R^(13×256) |
| IT-04 | ICD-04: TGN → Predictor → NLG | Embeddings | Probability + explanation text |
| IT-05 | ICD-05: Telemetry → Post-flight | Post-flight HDF5 | THERMAL-DIFF-GNN scores |
| IT-06 | ICD-06: RUL → Requalification | Component observations | GO/AMBER/REJECT per component |
| IT-07 | ICD-07: CLPX transfer | In-flight history | Updated post-flight priors |
| IT-08 | ICD-08: Engine → Dashboard | Full pipeline output | Valid JSON for D3.js |

#### 9.1.3 System Tests

- **Location:** `tests/system/`
- **Focus:** End-to-end pipeline execution
- **Scenarios:** All 5 operational scenarios from Evaluation Framework

| Test ID | Scenario | Duration | Pass Criteria |
|---------|----------|----------|---------------|
| ST-01 | Slow battery degradation | 24h simulated | Alert > 10 min before failure |
| ST-02 | Rapid thermal cascade | 1h simulated | Correct cascade detection in < 5 min |
| ST-03 | Eclipse transition | 4h simulated | No false alarm during nominal eclipse |
| ST-04 | Routine post-flight | Full flight data | All components GO, RUL > 80% |
| ST-05 | Damaged post-flight | Full flight + damage | REJECT flagged, PhyRAG explains |

### 9.2 Test Data Management

- All test data uses real mission telemetry from NASA SMAP/MSL, ESA-AD, and C-MAPSS datasets via `prajna/data/data_adapter.py`
- Test fixtures include:
  - `tests/fixtures/nominal_100.csv` — 100 timesteps nominal data
  - `tests/fixtures/battery_fault.csv` — Battery degradation → failure
  - `tests/fixtures/cascade_fault.csv` — Multi-subsystem cascade
  - `tests/fixtures/postflight_nominal.hdf5` — Clean post-flight dump
  - `tests/fixtures/postflight_damaged.hdf5` — Damaged component post-flight
- No real spacecraft telemetry is used at any point

### 9.3 Test Execution

```bash
# Unit tests with coverage
pytest tests/unit/ --cov=prajna --cov-report=html -v

# Integration tests
pytest tests/integration/ -v --tb=short

# System tests (longer runtime)
pytest tests/system/ -v --timeout=300

# Full suite
pytest tests/ --cov=prajna --cov-report=html --junitxml=outputs/reports/test_results.xml
```

---

## 10. CODE QUALITY CONTROLS

### 10.1 Static Analysis Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| ruff | Linting + formatting (PEP 8) | `ruff.toml` with ISRO-appropriate rules |
| mypy | Static type checking | `mypy.ini`, strict mode on critical modules |
| bandit | Security vulnerability scanning | Default rules, scan all Python files |

### 10.2 Code Review Checklist

Every module must pass the following checklist before baseline inclusion:

- [ ] Follows PEP 8 conventions (enforced by ruff)
- [ ] All public functions have docstrings with parameter/return types
- [ ] No hardcoded magic numbers (all constants in config or module top)
- [ ] No network calls (air-gap compliance)
- [ ] No file paths constructed from user input without sanitisation
- [ ] Unit tests exist and pass for all logic branches
- [ ] Type hints present on all function signatures
- [ ] No `TODO` or `FIXME` comments in delivered code
- [ ] Error handling follows graceful degradation chain (ICD §8)
- [ ] Memory allocation is bounded (no unbounded lists/dicts)

### 10.3 Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Modules | lowercase_snake | `sdwap_propagator.py` |
| Classes | PascalCase | `TemporalGraphNetwork` |
| Functions | lowercase_snake | `compute_sdwap_scores()` |
| Constants | UPPER_SNAKE | `MAX_PROPAGATION_STEPS` |
| Config keys | lowercase_dot | `model.tgn.hidden_dim` |
| Test files | test_ prefix | `test_sdwap_convergence.py` |

---

## 11. REVIEW AND AUDIT PROGRAMME

### 11.1 Review Schedule

| Review | Timing | Scope | Participants |
|--------|--------|-------|-------------|
| R1 — Design Review | Week 1 end | All documentation, architecture | Developer + ISRO mentor |
| R2 — Code Alpha Review | Week 3 end | Core engine code + unit tests | Developer + ISRO mentor |
| R3 — Integration Review | Week 4 mid | Integration tests, coverage report | Developer + ISRO mentor |
| R4 — Final Acceptance | Week 5 end | Full system, evaluation, docs | Developer + ISRO panel |

### 11.2 Review Artefacts

Each review produces:

1. **Review Record:** Date, attendees, items reviewed, findings
2. **Action Items:** Numbered, assigned, with resolution deadline
3. **Decision:** PASS / CONDITIONAL PASS (with action items) / FAIL

### 11.3 Audit Criteria

Audit criteria correspond to ECSS-Q-ST-80C annexes:

- **Documentation audit:** All 9 documents present, internally consistent, version-controlled
- **Code audit:** Matches design, passes static analysis, coverage > 80%
- **Test audit:** All tests pass, results recorded, fixtures documented
- **Configuration audit:** All CIs identified, baselined, and version-tagged

---

## 12. DEFECT MANAGEMENT

### 12.1 Defect Classification

| Severity | Definition | Example | Resolution Deadline |
|----------|-----------|---------|-------------------|
| **Critical** | System non-functional or produces wrong results | SDWAP diverges, wrong RUL | Before next baseline |
| **Major** | Feature impaired but workaround exists | Dashboard rendering glitch | Before delivery |
| **Minor** | Cosmetic or documentation issue | Typo in log message | Best effort before delivery |

### 12.2 Defect Lifecycle

```
OPEN → ANALYSED → FIXING → FIXED → VERIFIED → CLOSED
                                  ↘ REOPEN (if verification fails)
```

### 12.3 Defect Tracking

- **Tool:** Git issues (local repository) or `DEFECTS.md` tracking file
- **Fields:** ID, date, severity, description, module, root cause, fix, verification

---

## 13. RISK-BASED QUALITY PRIORITIES

### 13.1 Quality Risk Assessment

| Risk | Impact | Likelihood | Quality Mitigation |
|------|--------|-----------|-------------------|
| Algorithm divergence (SDWAP) | Critical: wrong anomaly scores | Low (convergence proven) | Unit test with divergent inputs; convergence check in code |
| PhyRAG hallucination | Critical: misleading advice | Medium | Physics constraint checker with 4-layer validation |
| Model overfitting | Major: poor generalisation | Medium | 5-fold cross-validation, ablation studies |
| Data leakage (temporal) | Critical: inflated metrics | Low | Time-ordered split enforced in code |
| Ollama model loading failure | Major: PhyRAG unavailable | Medium | Graceful degradation: template-only NLG mode |
| Memory overflow on M2 | Major: system crash | Low | Profiling during integration, bounded data structures |
| Non-deterministic training | Major: irreproducible results | Low | Fixed seeds, deterministic mode flags |
| CLPX negative transfer | Minor: no improvement | Medium | Trust adaptation mechanism (λ_trust) limits damage |

### 13.2 Testing Priority Order

Based on risk and criticality, testing effort is allocated:

1. **Highest:** SDWAP convergence, predictor accuracy, data pipeline integrity
2. **High:** THERMAL-DIFF-GNN physics compliance, RUL accuracy, PhyRAG hallucination prevention
3. **Medium:** CLPX transfer effectiveness, dashboard correctness
4. **Lower:** Logging, error messages, edge-case formatting

---

## 14. QUALITY METRICS AND REPORTING

### 14.1 Tracked Metrics

| Metric | Target | Measurement Tool | Frequency |
|--------|--------|-----------------|-----------|
| Test pass rate | 100% | pytest | Every commit |
| Code coverage | > 80% | pytest-cov | Every commit |
| Lint violations | 0 | ruff | Every commit |
| Type errors | 0 critical | mypy | Every commit |
| Security findings | 0 high/critical | bandit | Weekly |
| Open critical defects | 0 at delivery | DEFECTS.md | Continuously |
| Documentation currency | All docs match code | Manual review | Each baseline |

### 14.2 Quality Dashboard

At delivery, the quality report includes:

```
PRAJNA Quality Report
═══════════════════════
Date:        [delivery date]
Version:     v1.0.0
Baseline:    B4

Test Summary:
  Unit tests:        XX/XX passed (100%)
  Integration tests: XX/XX passed (100%)
  System tests:      XX/XX passed (100%)
  Coverage:          XX.X% (target: >80%)

Static Analysis:
  Ruff violations:   0
  mypy errors:       0 critical
  Bandit findings:   0 high/critical

Defect Summary:
  Critical open:     0
  Major open:        0
  Minor open:        X
  Total resolved:    XX

Algorithm Validation:
  Acceptance criteria met: XX/10 (see Evaluation Report)
  Ablation studies passed: X/7

Reviewer Sign-off:
  Developer:    ____________  Date: ________
  ISRO Mentor:  ____________  Date: ________
```

---

## 15. DELIVERY AND ACCEPTANCE

### 15.1 Delivery Package Contents

| Item | Format | Filename |
|------|--------|----------|
| Source code (10 algorithm modules) | Python package | `prajna/` |
| Tests (~130 tests) | Python test files | `tests/` |
| Configuration | YAML | `config/default.yaml` |
| Documentation (11 docs) | Markdown | `docs/` |
| Requirements | Text | `requirements.txt` |
| Setup | Python | `setup.py` or `pyproject.toml` |
| README | Markdown | `README.md` |
| Quality Report | JSON + HTML | `outputs/reports/quality_report.*` |
| Evaluation Report | JSON + HTML | `outputs/reports/evaluation_report.*` |
| Trained models | PyTorch | `outputs/models/` |
| NETRA edge model (quantized) | ONNX / TFLite | `outputs/models/netra/` |
| Formal safety case | GSN + JSON | `outputs/safety/` |

### 15.2 Acceptance Checklist

The delivery is accepted when:

- [ ] All 20 functional requirements verified (FR-01 to FR-20)
- [ ] All 8 non-functional requirements verified (NFR-01 to NFR-08)
- [ ] Test coverage > 80% (~130 tests)
- [ ] Zero open critical defects
- [ ] All 19 metric thresholds met at minimum level or above
- [ ] All 11 documents delivered and internally consistent
- [ ] AEGIS adversarial detection rate > 85%
- [ ] SHAKTI conformal coverage ≥ 97%
- [ ] KAVACH property satisfaction ≥ 98%
- [ ] NETRA fidelity > 90%
- [ ] Formal safety case (GSN) generated and complete
- [ ] Quality report signed by developer
- [ ] Code runs successfully on clean MacBook Air M2 from `git clone` to `python -m prajna`

### 15.3 Handover

Upon acceptance by ISRO mentor/panel:

1. Tagged release `v1.0.0` created in Git
2. Full repository archived as `.tar.gz`
3. Delivery receipt signed by both parties
4. All documentation updated to final version numbers

---

**END OF DOCUMENT**

**Document Number:** PRAJNA/QAP/2026/001  
**Version:** 1.1  
**Classification:** UNRESTRICTED — FOR REVIEW  

---
