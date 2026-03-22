# PRAJNA — Formal Verification & Safety Assurance Document

## Mathematical Safety Guarantees for Mission-Critical AI Decisions

---

**Document Number:** PRAJNA/FV/2026/001  
**Version:** 1.0  
**Date of Issue:** 06 March 2026  
**Classification:** UNRESTRICTED — FOR REVIEW  
**Prepared for:** Indian Space Research Organisation (ISRO)  
**Prepared by:** Karthik  
**Applicable Standards:** DO-178C (reference), ECSS-Q-ST-80C, ARP 4754A (reference)  

---

## TABLE OF CONTENTS

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Safety Assurance Philosophy](#2-safety-assurance-philosophy)
3. [Formal Safety Properties](#3-formal-safety-properties)
4. [KAVACH Verification Engine](#4-kavach-verification-engine)
5. [SHAKTI Coverage Guarantees](#5-shakti-coverage-guarantees)
6. [Interval Bound Propagation for GNNs](#6-interval-bound-propagation-for-gnns)
7. [Safety Case Structure (GSN)](#7-safety-case-structure-gsn)
8. [Failure Mode and Effects Analysis](#8-failure-mode-and-effects-analysis)
9. [Compliance Notes](#9-compliance-notes)

---

## 1. PURPOSE AND SCOPE

### 1.1 Purpose

This document establishes the formal safety assurance framework for PRAJNA's AI-driven decisions. It defines the mathematical guarantees provided by KAVACH (runtime verification) and SHAKTI (conformal coverage) and shows how these combine to create a verifiable safety case for spacecraft requalification and health monitoring decisions.

### 1.2 Scope

The formal verification framework covers:

- **In-flight decisions:** Anomaly alerts, failure predictions, severity classifications
- **Post-flight decisions:** GO/AMBER/REJECT requalification assessments
- **RUL estimates:** Remaining useful life predictions with guaranteed bounds
- **AEGIS decisions:** Input acceptance/rejection with verifiable criteria

### 1.3 Relationship to Other Documents

This document bridges:
- KAVACH specification (PRAJNA/ADV/2026/001 §5) — formal verification algorithms
- SHAKTI specification (PRAJNA/ADV/2026/001 §3) — conformal prediction theory
- Evaluation Framework (PRAJNA/EVL/2026/001) — acceptance criteria
- Quality Assurance Plan (PRAJNA/QAP/2026/001) — verification strategy

---

## 2. SAFETY ASSURANCE PHILOSOPHY

### 2.1 Levels of Assurance

PRAJNA provides three levels of assurance, each building on the previous:

```
Level 1: STATISTICAL ASSURANCE (standard ML)
  └── ROC-AUC, PR-AUC, F1 metrics on test set
  └── Limitation: No individual prediction guarantee

Level 2: CONFORMAL ASSURANCE (SHAKTI)
  └── Coverage guarantee: P(y ∈ C(x)) ≥ 1 - ε
  └── Holds for ANY model, ANY distribution (only needs exchangeability)
  └── Provides: prediction intervals, conservative decision making

Level 3: FORMAL ASSURANCE (KAVACH)
  └── Formally specified safety properties checked at runtime
  └── Interval bound propagation on neural network outputs
  └── Safety case argumentation with traceable evidence
  └── Provides: verifiable safety claims, auditable decision trail
```

### 2.2 Defense-in-Depth

```
┌──────────────────────────────────────────────────────┐
│                 DEFENSE IN DEPTH                      │
│                                                       │
│  Layer 1: AEGIS        — Block adversarial inputs     │
│  Layer 2: SDWAP + TGN  — Detect anomalies accurately │
│  Layer 3: SHAKTI       — Bound prediction uncertainty │
│  Layer 4: KAVACH       — Verify decision safety       │
│  Layer 5: PhyRAG       — Ground in physics knowledge  │
│                                                       │
│  Every decision passes through ALL five layers.       │
│  No single layer failure compromises safety.          │
└──────────────────────────────────────────────────────┘
```

---

## 3. FORMAL SAFETY PROPERTIES

### 3.1 Property Specification Language

Safety properties are specified using a restricted first-order logic:

```
Property := ∀ Variable_list : Precondition → Postcondition
Precondition := Atomic_predicate | Precondition ∧ Precondition
Postcondition := Atomic_predicate | ¬ Atomic_predicate | Postcondition ∧ Postcondition
Atomic_predicate := Variable op Constant | Variable op Variable | Function(Variable)
op := < | ≤ | = | ≥ | > | ∈ | ∉
```

### 3.2 In-Flight Safety Properties

```
Property IF-S1: Alert Completeness
  ∀ subsystem s, ∀ time t:
    (ground_truth_failure(s, t, t+30min) = TRUE) →
    (P_alert(s, t) > θ_warning OR SDWAP_score(s, t) > θ_warning)
  
  Interpretation: Every true failure must trigger at least a warning-level alert
  within the prediction window. Verified by: ROC-AUC > 0.88 (minimum threshold).

Property IF-S2: False Alarm Boundedness
  ∀ 24-hour period [t, t+24h]:
    count({s,τ : P_alert(s,τ) > θ_warning ∧ ¬ground_truth_failure(s,τ,τ+30min)}) ≤ FAR_max
  
  Where FAR_max = 5 (absolute maximum), target = 3
  Interpretation: System must not overwhelm operators with false alerts.

Property IF-S3: Temporal Consistency
  ∀ subsystem s, ∀ time t:
    (P_alert(s, t) > θ_critical) →
    (P_alert(s, t-60s) > θ_watch)
  
  Interpretation: A critical alert must be preceded by at least a watch-level 
  indication within the last minute. Prevents sudden jumps to critical.
```

### 3.3 Post-Flight Safety Properties

```
Property PF-S1: Conservative Safety
  ∀ component c:
    (SHAKTI_upper(D_c) ≥ θ_reject) → (Decision(c) ∈ {AMBER, REJECT})
  
  Interpretation: If the upper bound of degradation (at 99% coverage) exceeds 
  the REJECT threshold, the component cannot receive GO status.

Property PF-S2: Cascade Awareness
  ∀ pairs (c1, c2) with dependency w_{c1,c2} > 0.5:
    (Decision(c1) = REJECT) → (Decision(c2) ≠ GO)
  
  Interpretation: If a component is rejected, all strongly dependent components 
  must be flagged for inspection (AMBER or REJECT).

Property PF-S3: Physics Monotonicity
  ∀ component c, ∀ flights f1 < f2:
    (D_physics_c(f2) ≥ D_physics_c(f1))
  
  Interpretation: Physics-based degradation (Coffin-Manson, TID, Miner) is 
  monotonically non-decreasing. The learned component may fluctuate, but 
  the physics prior must be monotonic.

Property PF-S4: RUL Consistency
  ∀ component c:
    (RUL_c = 0) → (Decision(c) = REJECT)
    (RUL_c ≤ 1 ∧ D_c ≥ 0.5) → (Decision(c) ∈ {AMBER, REJECT})
  
  Interpretation: Zero remaining life mandates REJECT. One flight remaining 
  with moderate damage mandates at minimum AMBER.

Property PF-S5: Explanation Accountability  
  ∀ component c where Decision(c) ≠ GO:
    ∃ explanation E_c from PhyRAG:
      (E_c cites at least 1 source document) ∧
      (E_c passes physics constraint checker with score > θ_physics)
  
  Interpretation: Every non-GO decision must have a physics-grounded, 
  source-cited explanation. Unexplainable rejections are not permitted.
```

### 3.4 Cross-Module Safety Properties

```
Property XM-S1: AEGIS-SDWAP Consistency
  ∀ subsystem s, ∀ time t:
    (AEGIS_decision(s, t) = BLOCK) →
    (SDWAP uses last_known_good(s) with confidence_i = 0.1)
  
  Interpretation: Blocked inputs must not silently disappear from the pipeline.

Property XM-S2: SHAKTI-KAVACH Agreement
  ∀ decision d:
    (KAVACH_verified(d) = TRUE) → 
    (SHAKTI_coverage(d) ≥ 0.99 ∨ decision_is_conservative(d))
  
  Interpretation: A KAVACH-verified decision either has 99% conformal coverage 
  or errs on the side of safety.

Property XM-S3: NETRA-PRAJNA Consistency
  ∀ subsystem s, ∀ time t where ground_contact = TRUE:
    |NETRA_score(s, t) - PRAJNA_score(s, t)| < δ_sync
    ∨ trigger_model_sync(NETRA)
  
  Where δ_sync = 0.15. If onboard and ground models diverge beyond this 
  threshold, a model synchronization is triggered.
```

---

## 4. KAVACH VERIFICATION ENGINE

### 4.1 Runtime Verification Algorithm

```
function KAVACH_verify(decisions: List[ComponentDecision]) → VerifiedDecisions:
    
    violations = []
    overrides = []
    
    # Phase 1: Individual property checking
    for each decision d_i in decisions:
        for each property P in SAFETY_PROPERTIES:
            if d_i is in scope of P:
                if not satisfies(d_i, P):
                    violations.append((d_i, P, compute_violation_evidence(d_i, P)))
                    override = compute_conservative_override(d_i, P)
                    overrides.append((d_i, override))
    
    # Phase 2: Cross-decision consistency
    for each pair (d_i, d_j) with dependency w_{ij} > 0.5:
        if is_inconsistent(d_i, d_j):  # e.g., d_i=REJECT, d_j=GO
            overrides.append((d_j, make_conservative(d_j)))
    
    # Phase 3: Apply overrides (most conservative wins)
    verified_decisions = apply_overrides(decisions, overrides)
    
    # Phase 4: Generate safety case
    safety_case = generate_gsn(verified_decisions, violations, overrides)
    
    return VerifiedDecisions(
        decisions = verified_decisions,
        violations = violations,
        overrides = overrides,
        safety_case = safety_case
    )
```

### 4.2 Override Policy

```
When a property violation is detected:

Priority 1: Safety-critical properties (PF-S1, PF-S2, PF-S4)
  → Immediate override to conservative decision
  → Log CRITICAL violation
  → Require human acknowledgment before GO

Priority 2: Consistency properties (IF-S3, PF-S3, XM-S1)
  → Flag for review
  → Log WARNING violation
  → Decision proceeds but marked as QUALIFIED

Priority 3: Quality properties (PF-S5, XM-S3)
  → Log INFO note
  → Decision proceeds with annotation
```

---

## 5. SHAKTI COVERAGE GUARANTEES

### 5.1 Theoretical Foundation

**Theorem (Vovk, 2005):** For exchangeable data (X_1, Y_1), ..., (X_m, Y_m), (X_{m+1}, Y_{m+1}), and nonconformity function A, the prediction set:

```
C_ε(X_{m+1}) = {y : A(X_{m+1}, y) ≤ Q_{1-ε}(A_1, ..., A_m)}
```

satisfies:

```
P(Y_{m+1} ∈ C_ε(X_{m+1})) ≥ 1 - ε
```

This holds regardless of the underlying distribution or model quality.

### 5.2 Practical Coverage Tracking

```
SHAKTI maintains a running coverage monitor:

coverage_window = 1000  (rolling window of recent predictions)
observed_coverage = count(y_t ∈ C(x_t)) / coverage_window

Alert conditions:
  observed_coverage < (1-ε) - 0.02  →  WARNING: possible distribution shift
  observed_coverage < (1-ε) - 0.05  →  CRITICAL: recalibrate immediately

Adaptive response:
  ε_runtime = ε_runtime - η_aci × (observed_coverage - (1-ε_target))
  Recalculate q̂ with adjusted ε_runtime
```

---

## 6. INTERVAL BOUND PROPAGATION FOR GNNS

### 6.1 IBP Through Graph Convolution

```
For a GCN layer: H^{(l+1)} = ReLU(D̃^{-1/2} · Ã · D̃^{-1/2} · H^{(l)} · W^{(l)} + b^{(l)})

Given input interval [H_lower^{(l)}, H_upper^{(l)}]:

Step 1: Aggregation (linear, preserves interval structure)
  Ã_norm = D̃^{-1/2} · Ã · D̃^{-1/2}
  
  Since Ã_norm has non-negative entries (adjacency + self-loops):
    Agg_lower = Ã_norm · H_lower^{(l)}
    Agg_upper = Ã_norm · H_upper^{(l)}

Step 2: Linear transform W^{(l)}
  W_pos = max(W^{(l)}, 0)
  W_neg = min(W^{(l)}, 0)
  
  Pre_lower = W_pos · Agg_lower + W_neg · Agg_upper + b^{(l)}
  Pre_upper = W_pos · Agg_upper + W_neg · Agg_lower + b^{(l)}

Step 3: ReLU
  H_lower^{(l+1)} = max(0, Pre_lower)
  H_upper^{(l+1)} = max(0, Pre_upper)
```

### 6.2 Application to THERMAL-DIFF-GNN

```
Input perturbation model:
  Post-flight telemetry has measurement uncertainty ±δ_sensor per feature

Input intervals:
  F_post_lower = F_post - δ_sensor
  F_post_upper = F_post + δ_sensor

IBP propagation through 2-layer GCN:
  [f_lower, f_upper] = IBP_GCN(F_post_lower, F_post_upper, W^{(1)}, W^{(2)})

Combined with physics term:
  D_lower = λ · Φ + (1-λ) · f_lower
  D_upper = λ · Φ + (1-λ) · f_upper

Decision verification:
  If D_upper < 0.3:  GO is formally safe (even worst case is below threshold)
  If D_lower > 0.7:  REJECT is formally justified (even best case exceeds threshold)
  Otherwise:         AMBER is the safe default
```

---

## 7. SAFETY CASE STRUCTURE (GSN)

### 7.1 Top-Level Safety Argument

```
[G0] PRAJNA system makes safe spacecraft health decisions
├── [S1] Strategy: Argued over system lifecycle phases
│   ├── [G1] In-flight anomaly alerts are reliable
│   │   ├── [G1.1] Detection accuracy exceeds minimum thresholds
│   │   │   └── [E1.1] Evaluation report: ROC-AUC > 0.88  ← Eval Framework
│   │   ├── [G1.2] False alarm rate is bounded
│   │   │   └── [E1.2] IF-S2 verified: FAR < 5/day  ← KAVACH
│   │   ├── [G1.3] Temporal consistency is maintained
│   │   │   └── [E1.3] IF-S3 verified  ← KAVACH
│   │   └── [G1.4] Predictions have coverage guarantees
│   │       └── [E1.4] SHAKTI coverage ≥ 99%  ← SHAKTI
│   │
│   ├── [G2] Post-flight requalification decisions are conservative
│   │   ├── [G2.1] Conservative safety property holds
│   │   │   └── [E2.1] PF-S1 verified with SHAKTI bounds  ← KAVACH + SHAKTI
│   │   ├── [G2.2] Cascade effects are considered
│   │   │   └── [E2.2] PF-S2 verified  ← KAVACH
│   │   ├── [G2.3] Physics laws are respected
│   │   │   └── [E2.3] PF-S3 verified + PhyRAG checked  ← KAVACH + PhyRAG
│   │   ├── [G2.4] Every non-GO has explanation
│   │   │   └── [E2.4] PF-S5 verified  ← KAVACH + PhyRAG
│   │   └── [G2.5] Neural network bounds are verified
│   │       └── [E2.5] IBP on THERMAL-DIFF-GNN  ← KAVACH IBP
│   │
│   └── [G3] System is resilient to adversarial inputs
│       ├── [G3.1] Adversarial inputs are detected and filtered
│       │   └── [E3.1] AEGIS guard active  ← AEGIS
│       ├── [G3.2] Blocked inputs are handled safely
│       │   └── [E3.2] XM-S1 verified  ← KAVACH
│       └── [G3.3] Onboard-ground consistency maintained
│           └── [E3.3] XM-S3 verified  ← KAVACH
│
├── [S2] Strategy: Argued over independence of assurance layers
│   ├── [G4] AEGIS, SHAKTI, KAVACH are independent
│   │   └── [E4] Architecture diagram: separate modules, no shared state  ← ICD
│   └── [G5] No single layer failure compromises safety
│       └── [E5] Graceful degradation chain verified  ← QA Plan
│
└── [A1] Assumption: Real mission telemetry (NASA/ESA) is representative of ISRO telemetry patterns
    └── [J1] Justified by: physics-based generator modeling real sensor behavior
```

---

## 8. FAILURE MODE AND EFFECTS ANALYSIS

### 8.1 FMEA for PRAJNA AI Components

| ID | Failure Mode | Cause | Effect | Severity | PRAJNA Mitigation | Residual Risk |
|----|-------------|-------|--------|----------|-------------------|---------------|
| FM-01 | False negative (missed fault) | Model undertrained, novel fault type | Missed anomaly, potential mission impact | CRITICAL | SHAKTI shows wide uncertainty band → flag for human review | LOW |
| FM-02 | False positive (false alarm) | Noisy sensor, distribution shift | Operator fatigue, loss of trust | MAJOR | FAR bound (IF-S2), AEGIS filters noise, KAVACH consistency check | LOW |
| FM-03 | Adversarial input accepted | Sensor spoofing, replay attack | Wrong anomaly scores | CRITICAL | AEGIS 3-layer guard, KAVACH XM-S1 consistency | LOW |
| FM-04 | Wrong GO decision | Model error, insufficient data | Unsafe component flies | CRITICAL | PF-S1 (SHAKTI conservative bound), KAVACH override | VERY LOW |
| FM-05 | SHAKTI coverage failure | Distribution shift, non-exchangeable data | Prediction intervals too narrow | MAJOR | ACI adaptive coverage, runtime coverage monitor | LOW |
| FM-06 | KAVACH property violation | Edge case not covered by properties | Decision violates safety intent | MAJOR | GSN audit trail, human override layer | LOW |
| FM-07 | NETRA-PRAJNA divergence | Model drift, telemetry delay | Inconsistent onboard/ground decisions | MAJOR | XM-S3 sync trigger, ground PRAJNA as authority | LOW |
| FM-08 | VAYUH negative transfer | Heterogeneous satellite fleet, bad gradients | Degraded model accuracy | MINOR | Anomaly-weighted FedAvg, DP noise limits damage | LOW |
| FM-09 | PhyRAG hallucination passes checker | Novel physics not in knowledge base | Misleading explanation for operator | MAJOR | 4-layer physics checker, source citation requirement | LOW |
| FM-10 | Complete system failure | Power loss, software crash | No health monitoring | CRITICAL | Graceful degradation to threshold-only mode | LOW |

---

## 9. COMPLIANCE NOTES

### 9.1 Relationship to Aerospace Standards

| Standard | Applicability to PRAJNA | Notes |
|----------|------------------------|-------|
| **DO-178C** | Reference only — not certification target | PRAJNA is a research prototype. Full DO-178C certification would require additional activities (MC/DC coverage, traceability to object code, tool qualification). KAVACH and SHAKTI provide foundations for future certification. |
| **ARP 4754A** | Safety assessment methodology reference | FMEA and safety case structure follow ARP 4754A principles. |
| **ECSS-Q-ST-80C** | Quality assurance framework | QA Plan (PRAJNA/QAP/2026/001) follows ECSS-Q-ST-80C. |
| **ECSS-E-ST-40C** | Software engineering lifecycle | Modified V-model lifecycle follows ECSS-E-ST-40C. |

### 9.2 Path to Operational Certification

```
Current state:  Research prototype with formal assurance foundations
                (KAVACH + SHAKTI + GSN safety case)

Future path to DO-178C DAL-C (if pursued):
  1. MC/DC structural coverage analysis  (requires tool qualification)
  2. Requirements-based testing at object code level
  3. Tool qualification for PyTorch, Ollama, ChromaDB
  4. Independent verification by DER/DAR
  5. Formal configuration management (beyond Git)
  
Estimated additional effort: 12-18 months with dedicated V&V team
```

---

**END OF DOCUMENT**

**Document Number:** PRAJNA/FV/2026/001  
**Version:** 1.0  
**Classification:** UNRESTRICTED — FOR REVIEW  

---
