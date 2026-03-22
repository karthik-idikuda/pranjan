# PRAJNA — Submission Cover Letter

---

**Document Number:** PRAJNA/SUB/2026/001  
**Version:** 1.0  
**Date:** 06 March 2026  
**Classification:** UNRESTRICTED — FOR REVIEW  

---

**From:**  
Karthik  
Intern Applicant, ISRO RESPOND Programme  

**To:**  
The Programme Director  
Research Sponsored (RESPOND) Programme  
Indian Space Research Organisation  
ISRO Headquarters, Antariksh Bhavan  
New BEL Road, Bengaluru – 560 094  

**Subject:** Submission of Technical Proposal — PRAJNA: Predictive Reasoning Architecture for Joint Network-wide Anomalics — Full-Lifecycle Spacecraft Health Intelligence Platform  

---

Respected Sir/Madam,

I respectfully submit herewith the complete technical proposal for **PRAJNA** (Predictive Reasoning Architecture for Joint Network-wide Anomalics), a novel software system designed to address documented gaps in spacecraft health monitoring and reusable launch vehicle avionics requalification.

### Project Summary

PRAJNA is a full-lifecycle spacecraft health intelligence platform that:

1. **Detects** anomalies across 13 spacecraft subsystems using a novel graph-based propagation algorithm (SDWAP) that models inter-subsystem dependencies — a capability absent from all current ISRO, NASA, and ESA systems
2. **Predicts** subsystem failures 30 minutes in advance using Temporal Graph Neural Networks with physics-coupled attention mechanisms
3. **Explains** anomaly root causes and generates actionable contingency recommendations through a physics-grounded RAG engine (PhyRAG) that operates entirely offline
4. **Assesses** post-flight avionics health for reusable launch vehicles using a novel physics-ML hybrid diffusion network (THERMAL-DIFF-GNN)
5. **Learns** across flight cycles through a cross-lifecycle pattern exchange mechanism (CLPX), improving with every mission
6. **Guards** against adversarial telemetry manipulation through a 3-layer ensemble defence system (AEGIS) that detects spoofing, replay attacks, and noise injection
7. **Guarantees** prediction safety through conformal prediction wrappers (SHAKTI) providing mathematically proven 99% coverage bounds on every decision
8. **Federates** learning across ISRO's multi-satellite fleet without sharing raw telemetry (VAYUH), enabling constellation-wide health intelligence while respecting data classification policies
9. **Verifies** every safety-critical decision through runtime formal verification (KAVACH), producing auditable safety cases with interval arithmetic bounds on neural network outputs
10. **Deploys** to onboard spacecraft edge computers via knowledge distillation (NETRA), enabling autonomous real-time monitoring for deep-space and Gaganyaan missions

### Alignment with ISRO Requirements

This proposal directly addresses requirements documented in:

- **RESPOND Basket 2023-2024:** ML-based spacecraft telemetry anomaly detection
- **RESPOND Basket 2025:** AI-powered post-flight avionics requalification for RLV
- **VSSC Priority:** Offline, hallucination-free AI decision support systems
- **ISTRAC MuST Initiative:** Multi-satellite telemetry analysis
- **RLV-TD Programme:** Reusable vehicle turnaround optimization

### Novelty Claims

PRAJNA introduces **ten novel algorithms and modules** — SDWAP, THERMAL-DIFF-GNN, PhyRAG, RLV-RUL, CLPX, AEGIS, SHAKTI, VAYUH, KAVACH, and NETRA — none of which exist in any published research paper, patent database (ISRO IPR list, USPTO, EPO, Indian Patent Office), or deployed system as of March 2026. Detailed prior art analysis is provided in the Novelty Statement document (PRAJNA/NOV/2026/001) and Advanced Capabilities document (PRAJNA/ADV/2026/001).

### Technical Approach

The system is implemented entirely in Python using open-source frameworks (PyTorch, PyTorch Geometric, Flask, Ollama), operates fully offline in air-gapped environments, requires zero cloud infrastructure, and runs on consumer hardware (MacBook Air M2). Total infrastructure cost: **₹0**.

### Submission Package Contents

This submission comprises **eleven documents** totalling 200+ pages of original technical content:

| # | Document | Content |
|---|----------|---------|
| 01 | This Cover Letter | Submission overview |
| 02 | Executive Brief | 4-page project summary for review panel |
| 03 | Technical Design Document | Complete system specification (45+ pages) |
| 04 | Algorithm Specification | Full mathematical derivations of all 10 algorithms |
| 05 | System Architecture & ICD | Module interfaces, data schemas, security |
| 06 | Evaluation Framework | Metrics, ablation studies, stress testing protocol |
| 07 | Novelty Statement | Prior art analysis and first-of-kind claims |
| 08 | Requirements Traceability | Mapping to ISRO RESPOND requirements |
| 09 | Quality Assurance Plan | Testing, verification, and validation approach |
| 10 | Advanced Capabilities | AEGIS, SHAKTI, VAYUH, KAVACH, NETRA specifications |
| 11 | Formal Verification & Safety | Safety properties, IBP, FMEA, safety case |

### Declaration

I declare that:

1. All algorithms, architectures, and technical content in this submission are **original work** and have not been copied from any existing system, paper, or patent
2. The system is designed as a **research prototype** for demonstration purposes and does not claim operational certification
3. All software dependencies are **open-source** with permissive licenses (BSD, MIT, Apache 2.0)
4. The project can be demonstrated as a **working software system** upon request

I respectfully request the review committee to consider this proposal for the ISRO internship programme. I am available for technical presentation and demonstration at your convenience.

Respectfully submitted,

**Karthik**  
Date: 06 March 2026

---

**Enclosures:** Documents 02 through 11 as listed above  
**Total Documents:** 11  
**Total Pages:** 200+  
**Total Novel Algorithms:** 10  
**Classification:** UNRESTRICTED — FOR REVIEW  

---
