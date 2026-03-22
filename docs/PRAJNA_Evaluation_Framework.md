
# PRAJNA — Evaluation & Validation Framework

## Metrics, Ablation Studies, Test Protocol, and Acceptance Criteria

---

**Document Number:** PRAJNA/EVAL/2026/001  
**Version:** 1.0  
**Date of Issue:** 06 March 2026  
**Classification:** UNRESTRICTED — FOR REVIEW  
**Prepared for:** Indian Space Research Organisation (ISRO)

---

## TABLE OF CONTENTS

1. [Evaluation Philosophy](#1-evaluation-philosophy)
2. [Metric Definitions](#2-metric-definitions)
3. [Test Data Specification](#3-test-data-specification)
4. [Ablation Study Protocol](#4-ablation-study-protocol)
5. [Stress Testing Protocol](#5-stress-testing-protocol)
6. [Operational Validation Scenarios](#6-operational-validation-scenarios)
7. [Acceptance Criteria Matrix](#7-acceptance-criteria-matrix)
8. [Reporting Format](#8-reporting-format)

---

## 1. EVALUATION PHILOSOPHY

### 1.1 Principles

1. **Operationally meaningful metrics first.** ROC-AUC alone is insufficient for spacecraft monitoring. We prioritize metrics that map to operator experience: false alarm rate (trust), lead time (actionability), and root cause accuracy (diagnosability).

2. **Ablation proves contribution.** Each novel algorithm must demonstrate measurable improvement over the system without it. Ablations use controlled experiments with identical data splits.

3. **Class-imbalance-aware evaluation.** With >99% nominal data, accuracy is meaningless. We use PR-AUC, F1 at operational threshold, and false alarm rate instead.

4. **Statistical rigor.** All comparisons report standard deviations across 5 random seeds. Significance is tested via paired t-tests with α = 0.05.

5. **Stress testing validates robustness.** The system must degrade gracefully under adversarial conditions: missing sensors, simultaneous faults, out-of-distribution phases.

---

## 2. METRIC DEFINITIONS

### 2.1 In-Flight Detection Metrics

**M-01: ROC-AUC (Area Under Receiver Operating Characteristic)**

```
Definition: Probability that a randomly chosen anomalous sample receives a higher 
anomaly score than a randomly chosen nominal sample.

Computation: 
  For each threshold θ ∈ [0, 1]:
    TPR(θ) = TP(θ) / (TP(θ) + FN(θ))
    FPR(θ) = FP(θ) / (FP(θ) + TN(θ))
  ROC-AUC = ∫ TPR(FPR) dFPR

Evaluated per-node and macro-averaged across all 13 subsystems.
Target: > 0.92
```

**M-02: PR-AUC (Area Under Precision-Recall Curve)**

```
Definition: Summarizes the precision-recall trade-off across all thresholds.
More informative than ROC-AUC under extreme class imbalance.

Computation:
  For each threshold θ:
    Precision(θ) = TP(θ) / (TP(θ) + FP(θ))
    Recall(θ) = TP(θ) / (TP(θ) + FN(θ))
  PR-AUC = ∫ Precision(Recall) dRecall

Target: > 0.75
```

**M-03: F1 Score at Operational Threshold**

```
Definition: Harmonic mean of precision and recall at the deployment threshold θ_alert.

F1 = 2 · (Precision · Recall) / (Precision + Recall)

Evaluated at θ_alert = 0.6 (default operational threshold).
Target: > 0.80
```

**M-04: Median Lead Time**

```
Definition: For true positive detections, the time gap between first alert and 
ground-truth failure onset.

Lead_time_i = t_failure_i - t_first_alert_i  (for each correctly detected fault)
Median_lead_time = median(Lead_time_i for all i where detection is correct)

Only computed for fault scenarios that include a defined failure time.
Target: > 20 minutes
```

**M-05: False Alarm Rate (FAR)**

```
Definition: Number of false positive alerts per 24-hour operational period.

FAR = (Number of alerts where no real fault exists within 30 min) / 
      (Total monitoring hours / 24)

An alert is a "false alarm" if P_i^30(t) > θ_alert AND no ground-truth fault 
occurs for subsystem i within [t, t + 30 min].
Target: < 3 per day
```

**M-06: Root Cause Accuracy (RCA)**

```
Definition: Percentage of correctly detected faults where the top-1 
identified root cause matches the ground-truth root cause node.

RCA = (Number of TPs with correct top-1 root cause) / (Total TPs)

Ground truth root cause is defined in the fault injection labels.
Target: > 70%
```

### 2.2 Calibration Metric

**M-07: Brier Score**

```
Definition: Mean squared error between predicted probabilities and binary outcomes.

Brier = (1/N) · Σ_{i=1}^{N} (p_i - y_i)²

Where p_i is the calibrated probability and y_i ∈ {0, 1} is the true outcome.
Lower is better. Perfect calibration = 0.
Target: < 0.15
```

### 2.3 Post-Flight Metrics

**M-08: Requalification Accuracy**

```
Definition: Percentage of correct GO/AMBER/REJECT decisions across all components.

Accuracy = (Correct decisions) / (Total component decisions)

Decision categories:
  GO (D_i < 0.3):     Component is flight-worthy
  AMBER (0.3 ≤ D_i < 0.7): Component needs inspection
  REJECT (D_i ≥ 0.7): Component must be replaced

Evaluated against real C-MAPSS degradation profiles and published material fatigue data.
Target: > 85%
```

**M-09: RUL MAPE**

```
Definition: Mean Absolute Percentage Error of remaining useful life predictions.

MAPE = (1/n) · Σ_{i=1}^{n} |RUL_predicted_i - RUL_actual_i| / RUL_actual_i × 100%

Only for components where RUL_actual > 0 (not already failed).
Target: < 15%
```

### 2.4 Propagation Quality Metric

**M-10: SDWAP Propagation Fidelity**

```
Definition: How well SDWAP-computed propagation scores match ground-truth 
cascade propagation patterns from labeled data.

Fidelity = 1 - MSE(A_predicted, A_groundtruth) / Var(A_groundtruth)

Where A_groundtruth is derived from fault injection propagation delay labels:
  A_groundtruth_j(t) = severity × exp(-β × delay_j)  for affected nodes
  A_groundtruth_j(t) = 0 for unaffected nodes

Target: Report (no fixed threshold; used for algorithm tuning)
```

---

## 3. TEST DATA SPECIFICATION

### 3.1 Data Split Protocol

```
Total dataset: 24 hours × 1 Hz × 13 subsystems = 86,400 × 13 timesteps

Split strategy: TIME-BASED (no random shuffling — prevents temporal leakage)

  Training:   Hours 0-16.8   (70% = 60,480 timesteps)
  Validation: Hours 16.8-20.4 (15% = 12,960 timesteps)
  Test:       Hours 20.4-24.0 (15% = 12,960 timesteps)

Each split contains proportionally distributed fault scenarios.
```

### 3.2 Fault Distribution in Test Set

| Fault Type | Count in Test | Description |
|------------|------|-------------|
| Sensor Drift | 8 | Gradual offset accumulation |
| Cascade Failure | 8 | Multi-node propagating fault |
| Abrupt Spike | 8 | Sudden transient event |
| Gradual Degradation | 8 | Slow performance decay |
| Intermittent Glitch | 8 | Random sporadic disturbances |
| **Unseen combination** | **5** | **Multi-fault and novel combos not in training** |

The 5 "unseen combination" scenarios test generalization to fault patterns not present in training data.

### 3.3 Cross-Validation Strategy

```
5-fold time-based cross-validation:

Fold 1: Train [00-19h], Val [19-21.5h], Test [21.5-24h]
Fold 2: Train [00-16.8h] + [21.5-24h], Val [16.8-19h], Test [19-21.5h]
Fold 3: Train [00-14.4h] + [19-24h], Val [14.4-16.8h], Test [16.8-19h]
Fold 4: Train [02.4-24h], Val [00-02.4h], Test [02.4-04.8h] (wrap-around*)
Fold 5: Train [04.8-24h], Val [02.4-04.8h], Test [00-02.4h] (wrap-around*)

*Wrap-around folds test early-mission phase detection quality.

Each fold trains independently. Final metrics are mean ± std across 5 folds.
```

---

## 4. ABLATION STUDY PROTOCOL

### 4.1 Experiment Design

Each ablation removes or replaces exactly ONE component while keeping everything else identical: same data splits, same random seeds, same training hyperparameters.

### 4.2 Ablation A1: SDWAP Contribution

```
Configuration A (Full):   PRAJNA with SDWAP as specified
Configuration B (Ablated): Replace SDWAP with plain anomaly scores (A_i = s_i, no propagation)

Hypothesis: SDWAP improves cascade detection, root cause accuracy, and lead time.

Metrics to compare:
  - ROC-AUC (expected: A > B by 0.03-0.08)
  - RCA Accuracy (expected: A > B by 15-25%)
  - Median Lead Time (expected: A > B by 5-15 minutes)
  - FAR (expected: A ≤ B — SDWAP should not increase false alarms)
```

### 4.3 Ablation A2: Dynamic vs. Static Graph

```
Configuration A (Full):   Time-varying W_t with learned Δw adjustments
Configuration B (Ablated): Fixed W_base throughout (no dynamic adjustment)

Hypothesis: Dynamic graph improves detection during mission phase transitions.

Metrics to compare:
  - PR-AUC (expected: A > B by 0.02-0.05)
  - Lead Time during phase transitions (expected: A > B significantly)
  - Per-phase ROC-AUC breakdown
```

### 4.4 Ablation A3: TGN Architecture

```
Configuration A (Full):   Temporal Graph Neural Network as specified
Configuration B1:          LSTM per-node (no graph structure, just temporal)
Configuration B2:          Vanilla RNN per-node
Configuration B3:          Static MLP (no temporal, no graph)

Hypothesis: Graph + temporal modeling (TGN) outperforms temporal-only and static models.

Metrics to compare:
  - ROC-AUC (expected: A > B1 > B2 > B3)
  - F1 (expected: same ordering)
  - Cascade detection rate (expected: A >> B1 for multi-node faults)
```

### 4.5 Ablation A4: Dual Predictor vs. Single

```
Configuration A (Full):   Classifier + Hazard Model ensemble
Configuration B (Ablated): Classifier only (no hazard model)
Configuration C (Ablated): Hazard model only (no classifier)

Hypothesis: Ensemble provides better calibration and more informative uncertainty.

Metrics to compare:
  - Brier Score (expected: A < B, A < C)
  - F1 (expected: A ≈ B, A > C)
  - Hazard bin accuracy (only A and C; expected: A ≈ C)
```

### 4.6 Ablation A5: CLPX Cross-Lifecycle Feedback

```
Configuration A (Full):   With CLPX exchanging embeddings between flights
Configuration B (Ablated): Independent modules (no cross-lifecycle communication)

Hypothesis: CLPX improves requalification accuracy from flight 3+ onward.

Evaluation:
  Simulate 10 sequential flights.
  Plot requalification accuracy vs. flight number for A and B.
  
Expected: A converges to higher accuracy faster than B.
Difference should emerge starting at flight 3-5.
```

### 4.7 Ablation A6: Confidence Weighting in SDWAP

```
Configuration A (Full):   SDWAP with sensor confidence weighting (c_i injection + C_ij)
Configuration B (Ablated): SDWAP with uniform confidence (all c_i = 1.0)

Hypothesis: Confidence weighting reduces false alarms from unreliable sensors.

Metrics to compare:
  - FAR (expected: A < B — fewer false alarms with confidence weighting)
  - ROC-AUC at 30% sensor dropout (expected: A >> B)
```

### 4.8 Ablation A7: Physics Trust λ Adaptation

```
Configuration A (Full):   Adaptive λ starting at 0.8
Configuration B (Ablated): Fixed λ = 0.5 throughout

Hypothesis: Adaptive λ performs better when few flights are available (early flights) 
AND when many flights are available (late flights).

Evaluation:
  Plot RUL MAPE vs. flight number (1-10) for both A and B.

Expected: 
  Early flights (1-3): A better because λ→0.8 trusts physics when data is scarce
  Late flights (8-10): A ≈ B or A slightly better because λ adapted optimally
```

### 4.9 Results Reporting Template

| Ablation | Config | ROC-AUC | PR-AUC | F1 | Brier | Lead Time | FAR | RCA |
|----------|--------|---------|--------|-----|-------|-----------|-----|-----|
| A1-Full | PRAJNA + SDWAP | — | — | — | — | — | — | — |
| A1-Ablated | No SDWAP | — | — | — | — | — | — | — |
| A1-Δ | Difference | — | — | — | — | — | — | — |
| A1-p | p-value | — | — | — | — | — | — | — |

All values reported as mean ± std over 5 seeds. p-values from paired t-test.

---

## 5. STRESS TESTING PROTOCOL

### 5.1 ST-01: Sensor Dropout

```
Test: Randomly zero out 10%, 30%, and 50% of sensor channels.
      Set corresponding confidence c_i to match dropout level.

Evaluate: 
  - ROC-AUC degradation curve vs. dropout percentage
  - FAR vs. dropout percentage
  - Whether graceful degradation is achieved (no crashes, 
    scores still meaningful at 30%)

Pass criteria:
  - At 10% dropout: ROC-AUC > 0.88 (< 0.04 degradation)
  - At 30% dropout: ROC-AUC > 0.80
  - At 50% dropout: System still runs, ROC-AUC > 0.70
```

### 5.2 ST-02: Simultaneous Multi-Fault

```
Test: Inject 2 or 3 independent faults simultaneously in different subsystems.

Evaluate:
  - Can the system detect all faults? (multi-label detection)
  - Does SDWAP correctly identify multiple root causes?
  - Does the predictor produce distinct alerts for each fault?

Pass criteria:
  - Detect ≥ 80% of simultaneously active faults
  - Root cause accuracy ≥ 50% for simultaneous faults (harder than single-fault)
```

### 5.3 ST-03: Out-of-Distribution Mission Phase

```
Test: Present telemetry from a mission phase not seen in training 
      (e.g., train on phases 0-4, test on phase 6 = re-entry/landing).

Evaluate:
  - Does the model produce reasonable scores (not all 0 or all 1)?
  - Does the system raise an "out-of-distribution" warning?

Pass criteria:
  - System does not crash
  - Anomaly scores are still correlated with injected faults (ROC-AUC > 0.70)
```

### 5.4 ST-04: Adversarial Sensor Spoofing

```
Test: Inject nominal-looking values into a genuinely failing subsystem 
      (mask the anomaly at the sensor level).

Evaluate:
  - Can SDWAP still detect the anomaly through propagation from affected 
    neighbors? (e.g., battery is spoofed to look normal, but power bus 
    and thermal show cascade effects)

Pass criteria:
  - Detection via propagation within 10 minutes of neighbor effects appearing
```

### 5.5 ST-05: Latency Under Load

```
Test: Run inference continuously for 1 hour of simulated real-time data.
      Measure per-timestep latency distribution.

Pass criteria:
  - Mean latency < 100 ms
  - 99th percentile latency < 500 ms
  - No memory leaks (RSS remains stable ± 10%)
```

---

## 6. OPERATIONAL VALIDATION SCENARIOS

### 6.1 Scenario OV-01: Single Subsystem Slow Degradation

```
Setup: Battery pack gradually degrades over 4 hours (sensor drift fault).
       No immediate failure, but 30-min prediction should eventually trigger.

Expected behavior:
  t=0h:     All scores nominal
  t=1h:     Battery A_score begins rising (0.1 → 0.25)
  t=2h:     SDWAP elevates power bus score (0.05 → 0.15)
  t=3h:     30-min predictor triggers WARNING for thermal control
  t=3.5h:   CRITICAL alert with root cause = battery_pack
  t=4h:     Ground truth failure occurs
  
Validation: Lead time should be ~30-60 minutes.
```

### 6.2 Scenario OV-02: Rapid Cascade Failure

```
Setup: Propulsion thruster valve jams open → propellant tank pressure drops → 
       emergency propulsion shutdown → attitude control degradation (5-minute cascade).

Expected behavior:
  t=0:      Thruster valve score spikes (0.0 → 0.9)
  t+30s:    SDWAP propagates to propellant tank (0.1 → 0.5)
  t+60s:    SDWAP propagates to propulsion main (0.1 → 0.6)
  t+90s:    SDWAP propagates to attitude control (0.1 → 0.4)
  t+2min:   CRITICAL alert for propulsion, root cause = thruster_valve
  t+3min:   WARNING for attitude control

Validation: Full cascade detected within 3 minutes, root cause correct.
```

### 6.3 Scenario OV-03: Eclipse Transition

```
Setup: Spacecraft enters eclipse. Solar power drops to zero. Battery takes over.
       This is NOMINAL behavior, not a fault.

Expected behavior:
  - Battery discharge increases → scores may briefly elevate
  - SDWAP should NOT trigger cascade alarm (this is expected behavior)
  - Mission phase encoding should suppress false positives

Validation: FAR = 0 during eclipse transition (no false alarms).
```

### 6.4 Scenario OV-04: Post-Flight Routine Assessment

```
Setup: Normal landing of RLV-TD. All components within design limits.
       No damage beyond normal wear.

Expected behavior:
  - All components receive GO (green) status
  - RUL estimates are all > 5 flights
  - PhyRAG provides nominal summary citing component specs
  - No maintenance queue items except routine inspection

Validation: All 8 components correctly classified as GO.
```

### 6.5 Scenario OV-05: Post-Flight with Damage

```
Setup: Hard landing with 1.5× nominal shock load. Pyro circuits and 
       one actuator bank show elevated stress.

Expected behavior:
  - Pyro circuits: RED (D > 0.7), RUL = 0-1 flights
  - Actuator bank: AMBER (D = 0.4-0.6), RUL = 2-4 flights
  - Other components: GREEN
  - PhyRAG explains damage mechanism citing MIL-STD specs
  - Maintenance queue prioritizes pyro replacement

Validation: Correct damage classification, physically plausible explanation.
```

---

## 7. ACCEPTANCE CRITERIA MATRIX

### 7.1 Minimum Viable Performance

| Metric | Target | Minimum Acceptable | Fail |
|--------|--------|-------------------|------|
| ROC-AUC | > 0.92 | > 0.88 | ≤ 0.88 |
| PR-AUC | > 0.75 | > 0.65 | ≤ 0.65 |
| F1 (θ=0.6) | > 0.80 | > 0.72 | ≤ 0.72 |
| Median Lead Time | > 20 min | > 12 min | ≤ 12 min |
| FAR (/day) | < 3 | < 5 | ≥ 5 |
| RCA Accuracy | > 70% | > 55% | ≤ 55% |
| Brier Score | < 0.15 | < 0.22 | ≥ 0.22 |
| Requalification Accuracy | > 85% | > 75% | ≤ 75% |
| RUL MAPE | < 15% | < 25% | ≥ 25% |
| Inference Latency | < 35 ms | < 200 ms | ≥ 2000 ms |

### 7.2 Ablation Requirements

Each ablation must demonstrate:

```
For ablation Ak (comparing Full vs. Ablated):
  - At least ONE primary metric shows statistically significant improvement (p < 0.05)
  - No primary metric shows statistically significant degradation
  - Report all metrics regardless of significance
```

### 7.3 Stress Test Requirements

```
ST-01 (Sensor Dropout): Pass at 30% dropout level
ST-02 (Multi-fault): Detect ≥ 80% of active faults
ST-03 (OOD Phase): No crash, ROC-AUC > 0.70
ST-04 (Spoofing): Detection via propagation within 10 min
ST-05 (Latency): 99th percentile < 500 ms
```

---

## 8. REPORTING FORMAT

### 8.1 Evaluation Report Structure

```
evaluation_report.json:
{
    "system_version": "1.0",
    "evaluation_date": "2026-03-10",
    "data_split": "time-based 70/15/15",
    "random_seeds": [42, 123, 456, 789, 1024],
    
    "primary_metrics": {
        "roc_auc": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "pr_auc": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "f1_at_0.6": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "brier_score": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "median_lead_time_min": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "false_alarm_rate_per_day": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "rca_accuracy": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "requalification_accuracy": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]},
        "rul_mape": {"mean": 0.XX, "std": 0.XX, "per_seed": [...]}
    },
    
    "per_node_metrics": {
        "solar_array": {"roc_auc": 0.XX, "f1": 0.XX, ...},
        "power_bus": {"roc_auc": 0.XX, "f1": 0.XX, ...},
        ...
    },
    
    "ablation_results": {
        "A1_sdwap": {
            "full": {"roc_auc": 0.XX, ...},
            "ablated": {"roc_auc": 0.XX, ...},
            "delta": {"roc_auc": 0.XX, ...},
            "p_values": {"roc_auc": 0.XX, ...}
        },
        ...
    },
    
    "stress_tests": {
        "ST01_sensor_dropout": {"10pct": {...}, "30pct": {...}, "50pct": {...}},
        "ST02_multi_fault": {...},
        "ST03_ood_phase": {...},
        "ST04_spoofing": {...},
        "ST05_latency": {"mean_ms": X, "p99_ms": X, "max_ms": X}
    },
    
    "operational_scenarios": {
        "OV01_slow_degradation": {"lead_time": X, "correct_root_cause": true/false},
        "OV02_rapid_cascade": {"detection_time": X, "correct_root_cause": true/false},
        "OV03_eclipse_transition": {"false_alarms": 0},
        "OV04_routine_postflight": {"all_go": true/false},
        "OV05_damage_postflight": {"correct_classifications": X, "total": Y}
    }
}
```

### 8.2 Visual Report

An HTML report is generated alongside the JSON, containing:

- ROC and PR curves (per-node and aggregate)
- Confusion matrix heatmap
- Lead time histogram
- Ablation comparison bar charts
- Stress test degradation curves
- SDWAP propagation trace visualization for key scenarios
- Training loss curves
- Conformal prediction interval width distribution
- AEGIS detection rate curves
- KAVACH property satisfaction heatmap

---

## 9. ADVANCED CAPABILITY METRICS (AEGIS, SHAKTI, VAYUH, KAVACH, NETRA)

### 9.1 Additional Metrics

| ID | Metric | Formula / Method | Target | Minimum |
|----|--------|-----------------|--------|--------|
| M-11 | AEGIS Detection Rate | TP_adv / (TP_adv + FN_adv) on adversarial test set | >95% | >85% |
| M-12 | AEGIS False Block Rate | FP_block / total_nominal_inputs | <1% | <3% |
| M-13 | SHAKTI Empirical Coverage | count(y ∈ C(x)) / N over rolling 1000 predictions | ≥99% | ≥97% |
| M-14 | SHAKTI Interval Width | mean(upper - lower) across all predictions | <0.20 | <0.35 |
| M-15 | KAVACH Override Rate | safety_overrides / total_decisions | <5% | <10% |
| M-16 | KAVACH Property Satisfaction | satisfied_checks / total_checks | 100% | 98% |
| M-17 | NETRA Fidelity | 1 - |PRAJNA_score - NETRA_score| / PRAJNA_score | >95% | >90% |
| M-18 | NETRA Edge Latency | P99 inference time on ARM Cortex-A53 | <5ms | <10ms |
| M-19 | VAYUH Fed Improvement | (AUC_federated - AUC_local) / AUC_local | >3% | >1% |

### 9.2 Additional Ablation Studies

| ID | Ablation | Condition | Expected Impact |
|----|----------|-----------|----------------|
| A8 | Without AEGIS | Remove adversarial guard entirely | Vulnerability to adversarial inputs; no impact on clean data |
| A9 | Without SHAKTI | Remove conformal wrapper | No coverage guarantee; point predictions only |
| A10 | Without KAVACH | Remove formal verification layer | Potential safety property violations on edge cases |

### 9.3 Additional Stress Tests

| ID | Test | Protocol | Pass Criteria |
|----|------|----------|---------------|
| ST-06 | AEGIS Adversarial Barrage | 100 adversarial samples (replay, spoof, noise) injected per subsystem | Detection rate >90%, false alarm <3% |
| ST-07 | SHAKTI Coverage Stress | 5% distribution shift applied across 10,000 timesteps | Empirical coverage remains ≥97% with ACI adaptation |

### 9.4 NETRA Distillation Validation Protocol

```
Phase 1: Train teacher (full PRAJNA) to convergence
Phase 2: Distill to NETRA student with α_KD=0.7, T=4.0
Phase 3: Quantize to INT8
Phase 4: Evaluate on same test set:
  - Compare ROC-AUC, F1, lead time vs teacher
  - Fidelity metric M-17 must be >90%
  - Latency on target hardware must be <10ms
```

---

**END OF DOCUMENT**

**Document Number:** PRAJNA/EVAL/2026/001  
**Version:** 1.1  
**Classification:** UNRESTRICTED — FOR REVIEW

---
