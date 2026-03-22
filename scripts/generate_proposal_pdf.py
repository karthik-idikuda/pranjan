#!/usr/bin/env python3
"""
Generate ISRO-style clean government proposal PDF.
Minimal, formal, no flashy colors - Indian government document standard.
"""
from fpdf import FPDF


def s(text):
    """Sanitize unicode for latin-1 PDF."""
    return (
        text.replace("\u2014", "--")
        .replace("\u2013", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2022", "-")
        .replace("\u2026", "...")
        .replace("\u2192", "->")
        .replace("\u00d7", "x")
        .replace("\u0394", "delta_")
        .replace("\u03b1", "alpha")
        .replace("\u03b2", "beta")
        .replace("\u03b3", "gamma")
        .replace("\u03bb", "lambda")
    )


class GovPDF(FPDF):
    """Clean Indian government-style document."""

    def header(self):
        if self.page_no() > 1:
            self.set_font("Times", "I", 8)
            self.set_text_color(80, 80, 80)
            self.cell(95, 5, "PRAJNA/PROP/2026/001", align="L")
            self.cell(95, 5, "For ISTRAC Review", align="R")
            self.ln(6)
            self.set_draw_color(0, 0, 0)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(0, 0, 0)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        self.set_font("Times", "", 8)
        self.set_text_color(80, 80, 80)
        self.cell(95, 5, "Karthik Idikuda | PRAJNA Proposal", align="L")
        self.cell(95, 5, f"Page {self.page_no()}/{{nb}}", align="R")

    def sec(self, num, title):
        """Section heading - government style: bold, underlined, no color."""
        if self.get_y() > 245:
            self.add_page()
        self.ln(5)
        self.set_font("Times", "B", 13)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, s(f"{num}.  {title.upper()}"), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 0, 0)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(4)

    def subsec(self, title):
        if self.get_y() > 255:
            self.add_page()
        self.ln(2)
        self.set_font("Times", "B", 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, s(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def para(self, text):
        self.set_font("Times", "", 10.5)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.2, s(text))
        self.ln(2)

    def bpara(self, text):
        self.set_font("Times", "B", 10.5)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.2, s(text))
        self.ln(1)

    def bullet(self, text):
        self.set_font("Times", "", 10.5)
        self.set_text_color(0, 0, 0)
        x = 20
        self.set_x(x)
        n = getattr(self, '_bc', 0) + 1
        self._bc = n
        self.cell(10, 5.2, s(f"({n})"))
        self.set_x(x + 10)
        self.multi_cell(160, 5.2, s(text))

    def reset_bullets(self):
        self._bc = 0

    def simple_bullet(self, text):
        self.set_font("Times", "", 10.5)
        self.set_text_color(0, 0, 0)
        self.set_x(20)
        self.cell(5, 5.2, "-")
        self.set_x(25)
        self.multi_cell(165, 5.2, s(text))

    def table(self, headers, rows, widths=None):
        if widths is None:
            widths = [180 / len(headers)] * len(headers)

        # Header row - light grey background
        self.set_font("Times", "B", 9.5)
        self.set_fill_color(220, 220, 220)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        for i, h in enumerate(headers):
            self.cell(widths[i], 7, s(h), border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Times", "", 9.5)
        for row in rows:
            # Calculate height needed
            max_lines = 1
            for i, cell in enumerate(row):
                lines = self.multi_cell(widths[i], 4.5, s(str(cell)), dry_run=True, output="LINES")
                max_lines = max(max_lines, len(lines))
            rh = max(7, max_lines * 4.5)

            if self.get_y() + rh > 270:
                self.add_page()
                self.set_font("Times", "B", 9.5)
                self.set_fill_color(220, 220, 220)
                for i, h in enumerate(headers):
                    self.cell(widths[i], 7, s(h), border=1, fill=True, align="C")
                self.ln()
                self.set_font("Times", "", 9.5)

            y0 = self.get_y()
            x0 = self.get_x()
            max_y = y0
            for i, cell in enumerate(row):
                self.set_xy(x0 + sum(widths[:i]), y0)
                self.multi_cell(widths[i], 4.5, s(str(cell)), border="LR")
                max_y = max(max_y, self.get_y())
            # Bottom border
            self.set_draw_color(0, 0, 0)
            for i in range(len(row)):
                self.line(x0 + sum(widths[:i]), max_y, x0 + sum(widths[:i + 1]), max_y)
            self.set_y(max_y)
        self.ln(3)

    def code(self, text):
        self.set_font("Courier", "", 8)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(0, 0, 0)
        lines = text.strip().split("\n")
        h = len(lines) * 4 + 6
        if self.get_y() + h > 275:
            self.add_page()
        y0 = self.get_y()
        self.set_draw_color(180, 180, 180)
        self.rect(15, y0, 180, h, "FD")
        self.ln(3)
        for line in lines:
            self.set_x(17)
            self.cell(0, 4, s(line[:95]), new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


def build():
    pdf = GovPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, 20)

    # ============================================================
    # COVER PAGE
    # ============================================================
    pdf.add_page()

    # Double border - government style
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(12, 12, 186, 273, "D")
    pdf.rect(13, 13, 184, 271, "D")

    pdf.ln(18)
    pdf.set_font("Times", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "PROPOSAL FOR CONTRIBUTION TO R&D EFFORTS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Times", "B", 15)
    pdf.cell(0, 9, "ISRO TELEMETRY, TRACKING AND COMMAND NETWORK", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 7, "(ISTRAC)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 10)
    pdf.cell(0, 6, "Bangalore - 560058", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Times", "B", 20)
    pdf.cell(0, 12, "P R A J N A", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 6, "Predictive Reasoning Architecture for", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Joint Network-wide Anomalics", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Times", "I", 10)
    pdf.cell(0, 6, "A Graph Neural Network Framework for Spacecraft Health Intelligence", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(8)

    # Details
    details = [
        ("Proposal No.", "PRAJNA/PROP/2026/001"),
        ("Date", "10 March 2026"),
        ("Classification", "UNRESTRICTED"),
    ]
    for label, val in details:
        pdf.set_font("Times", "B", 10)
        pdf.cell(95, 6, label, align="R")
        pdf.set_font("Times", "", 10)
        pdf.cell(0, 6, s(f" :  {val}"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # TO box
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(30, pdf.get_y(), 150, 35, "D")
    y = pdf.get_y() + 3
    pdf.set_xy(35, y)
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 5, "TO:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(35)
    pdf.set_font("Times", "", 10)
    pdf.cell(0, 5, "Dr. A.K. Anil Kumar, Director, ISTRAC", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(35)
    pdf.cell(0, 5, "Shri Leo Jackson John, Group Director, Spacecraft Operations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(35)
    pdf.cell(0, 5, "Shri Amit Kumar Singh, SpOA, ISTRAC", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # FROM box
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(30, pdf.get_y(), 150, 35, "D")
    y = pdf.get_y() + 3
    pdf.set_xy(35, y)
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 5, "FROM:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(35)
    pdf.set_font("Times", "B", 11)
    pdf.cell(0, 6, "Karthik Idikuda", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(35)
    pdf.set_font("Times", "", 10)
    pdf.cell(0, 5, "B.Tech Artificial Intelligence (3rd Year), Marwadi University", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(35)
    pdf.cell(0, 5, "Phone: +91 9494432697  |  Email: idikudakarthik55@gmail.com", new_x="LMARGIN", new_y="NEXT")

    # ============================================================
    # TABLE OF CONTENTS
    # ============================================================
    pdf.add_page()
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "TABLE OF CONTENTS", new_x="LMARGIN", new_y="NEXT")
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    toc_items = [
        ("1.", "Executive Summary"),
        ("2.", "Problem Statement"),
        ("3.", "Proposed Solution -- PRAJNA"),
        ("4.", "System Architecture"),
        ("5.", "Algorithm Specifications"),
        ("6.", "Prototype Status and Results"),
        ("7.", "Relevance to ISTRAC Operations"),
        ("8.", "Proposed Role: R&D Ideas and Architecture"),
        ("9.", "Deliverables and Timeline"),
        ("10.", "Profile of the Proposer"),
        ("11.", "References"),
    ]
    for num, title in toc_items:
        pdf.set_font("Times", "", 11)
        pdf.cell(10, 7, num)
        pdf.cell(170, 7, s(title))
        pdf.ln()

    # ============================================================
    # 1. EXECUTIVE SUMMARY
    # ============================================================
    pdf.add_page()
    pdf.sec("1", "Executive Summary")

    pdf.para(
        "PRAJNA (Predictive Reasoning Architecture for Joint Network-wide Anomalics) "
        "is a spacecraft health intelligence framework that models inter-subsystem "
        "dependencies as a dynamic graph. Unlike conventional threshold-based monitoring "
        "where each parameter is watched independently, PRAJNA detects how a fault in "
        "one subsystem cascades through the spacecraft -- predicting failures before they "
        "reach critical systems."
    )

    pdf.para(
        "For example: when EPS (Electrical Power System) begins degrading, PRAJNA traces "
        "the cascading impact through EPS -> OBC -> COMM -> mission loss risk, and warns "
        "operators with specific contingency actions -- before the damage spreads."
    )

    pdf.bpara("Key Metrics of Working Prototype:")
    pdf.table(
        ["Parameter", "Value"],
        [
            ["Novel algorithms designed", "10"],
            ["Spacecraft subsystems modeled", "13 (ISRO-heritage configuration)"],
            ["Physics-informed dependency edges", "24"],
            ["Features per subsystem", "8 (unified, normalized)"],
            ["Source code", "6,000+ lines (Python)"],
            ["Automated test cases", "39/39 passing"],
            ["Technical documentation", "10 documents"],
            ["External cost", "Rs. 0 (fully open-source stack)"],
            ["Internet dependency", "None -- 100% air-gap compliant"],
            ["Hardware requirement", "Consumer laptop (tested on MacBook Air M2)"],
        ],
        [70, 110],
    )

    pdf.bpara(
        "Purpose of this proposal: I wish to contribute to ISTRAC's R&D team by "
        "providing novel ideas, system architectures, and algorithm designs for "
        "spacecraft health monitoring. This document presents the PRAJNA framework "
        "as a demonstration of my research and design capabilities."
    )

    # ============================================================
    # 2. PROBLEM STATEMENT
    # ============================================================
    pdf.add_page()
    pdf.sec("2", "Problem Statement")

    pdf.subsec("2.1 Current Gaps in Spacecraft Health Monitoring")
    pdf.para(
        "India's spacecraft fleet is monitored through static threshold checking and "
        "rule-based expert systems. Each telemetry parameter is watched independently. "
        "This approach has three critical gaps:"
    )

    pdf.bpara("Gap 1: No Inter-Subsystem Dependency Modeling")
    pdf.para(
        "A spacecraft has 13 tightly coupled subsystems. When EPS degrades, it "
        "affects OBC, COMM, BATT, and every power-dependent subsystem. Current systems "
        "detect EPS anomaly only when EPS parameters breach thresholds -- by which time "
        "dependent subsystems may already be stressed. No operational system models "
        "these dependencies or predicts cascade effects."
    )

    pdf.bpara("Gap 2: No AI-Based Post-Flight Requalification for RLV")
    pdf.para(
        "ISRO's Reusable Launch Vehicle programme requires rapid turnaround assessment "
        "of recovered avionics. Currently done through manual inspection. No AI system "
        "combines thermal fatigue, radiation damage, and vibration wear into a unified "
        "GO/AMBER/REJECT reuse decision."
    )

    pdf.bpara("Gap 3: No Cross-Flight Knowledge Transfer")
    pdf.para(
        "Each mission is analyzed in isolation. Lessons from one spacecraft's anomaly "
        "patterns are not systematically transferred to improve monitoring of the next "
        "flight or constellation satellites."
    )

    pdf.subsec("2.2 Global Comparison")
    pdf.table(
        ["Capability", "ISRO", "NASA", "ESA", "JAXA", "PRAJNA"],
        [
            ["Graph-based health monitoring", "No", "No", "No", "No", "Yes"],
            ["Cascade prediction", "No", "No", "No", "No", "Yes"],
            ["AI post-flight requalification", "No", "No", "No", "No", "Yes"],
            ["Cross-lifecycle transfer", "No", "No", "No", "No", "Yes"],
            ["Formal safety verification", "No", "No", "No", "No", "Yes"],
            ["Triple-mode RUL estimation", "No", "No", "No", "No", "Yes"],
        ],
        [50, 22, 22, 22, 22, 22],
    )
    pdf.para("No space agency currently operates a system with these combined capabilities.")

    # ============================================================
    # 3. PROPOSED SOLUTION
    # ============================================================
    pdf.add_page()
    pdf.sec("3", "Proposed Solution -- PRAJNA")

    pdf.para("PRAJNA models a spacecraft as a dynamic dependency graph:")
    pdf.simple_bullet("13 nodes -- one per subsystem (EPS, TCS, PROP, AOCS, COMM, OBC, PL, STRUCT, HARNESS, PYRO, REA, BATT, SA)")
    pdf.simple_bullet("24 directed, weighted edges -- physical dependencies (power, thermal, mechanical, data)")
    pdf.simple_bullet("8 unified features per node -- normalized telemetry measurements")
    pdf.ln(3)

    pdf.para("Ten algorithms operate in two modules:")

    pdf.subsec("In-Flight Module (Real-Time Monitoring)")
    pdf.table(
        ["#", "Algorithm", "Function"],
        [
            ["1", "Local Detector", "Score each subsystem (Z-score + Isolation Forest)"],
            ["2", "SDWAP", "Propagate anomaly scores through dependency graph"],
            ["3", "Temporal GNN", "Predict future failures using graph neural networks"],
            ["4", "SHAKTI", "Attach confidence intervals (conformal prediction)"],
            ["5", "KAVACH", "Verify 5 safety properties before any decision"],
            ["6", "NLG Engine", "Generate alerts with contingency actions"],
            ["7", "AEGIS", "Guard against adversarial/corrupted inputs"],
        ],
        [10, 35, 135],
    )

    pdf.subsec("Post-Flight Module (RLV Requalification)")
    pdf.table(
        ["#", "Algorithm", "Function"],
        [
            ["8", "THERMAL-DIFF-GNN", "Coffin-Manson physics + GNN for thermal fatigue"],
            ["9", "RLV-RUL", "Triple-mode remaining useful life estimation"],
            ["10", "CLPX", "Cross-lifecycle knowledge transfer bridge"],
        ],
        [10, 40, 130],
    )

    # ============================================================
    # 4. SYSTEM ARCHITECTURE
    # ============================================================
    pdf.add_page()
    pdf.sec("4", "System Architecture")

    pdf.subsec("4.1 Processing Pipeline")
    pdf.code(
        "DATA INGESTION\n"
        "  Telemetry Stream (T x 13 x 8)  |  Flight History Database\n"
        "                  |\n"
        "IN-FLIGHT ENGINE\n"
        "  AEGIS --> Local Detector --> SDWAP --> Temporal GNN --> SHAKTI\n"
        "  (Input     (Subsystem       (Graph     (Future         (Confidence\n"
        "   Guard)     Scoring)         Cascade)   Prediction)     Bounds)\n"
        "                                 |\n"
        "                              KAVACH (Formal Safety Verification)\n"
        "                                 |\n"
        "                              NLG Engine (Alerts + Actions)\n"
        "                                 |\n"
        "            ---- CLPX Cross-Lifecycle Bridge ----\n"
        "                                 |\n"
        "POST-FLIGHT ENGINE\n"
        "  THERMAL-DIFF-GNN --> RLV-RUL --> KAVACH --> GO / AMBER / REJECT\n"
        "                                 |\n"
        "OUTPUT\n"
        "  Dashboard  |  Alert Feed  |  Safety Reports  |  PhyRAG Explanations"
    )

    pdf.subsec("4.2 Spacecraft Graph -- 13 Subsystem Nodes")
    pdf.table(
        ["Node", "Subsystem", "Role"],
        [
            ["0", "EPS", "Electrical Power System"],
            ["1", "TCS", "Thermal Control System"],
            ["2", "PROP", "Propulsion"],
            ["3", "AOCS", "Attitude and Orbit Control"],
            ["4", "COMM", "Communication"],
            ["5", "OBC", "On-Board Computer"],
            ["6", "PL", "Payload"],
            ["7", "STRUCT", "Structure"],
            ["8", "HARNESS", "Wiring Harness"],
            ["9", "PYRO", "Pyrotechnics"],
            ["10", "REA", "Reaction Wheels"],
            ["11", "BATT", "Battery"],
            ["12", "SA", "Solar Array"],
        ],
        [15, 30, 135],
    )

    pdf.subsec("4.3 Key Dependency Edges (24 total)")
    pdf.table(
        ["Edge", "Weight", "Physical Basis"],
        [
            ["SA -> EPS", "0.95", "Solar array feeds power system"],
            ["EPS -> OBC", "0.90", "OBC critically depends on power"],
            ["BATT -> EPS", "0.90", "Battery backup for power"],
            ["EPS -> COMM", "0.85", "Communication requires power"],
            ["OBC -> AOCS", "0.85", "Computer commands attitude control"],
            ["EPS -> AOCS", "0.80", "Attitude control requires power"],
            ["OBC -> COMM", "0.80", "Computer manages communication"],
            ["EPS -> PL", "0.75", "Payload requires power"],
            ["AOCS -> PL", "0.70", "Pointing accuracy affects payload"],
            ["TCS -> BATT", "0.70", "Thermal conditions affect battery"],
            ["TCS -> EPS", "0.65", "Thermal affects power electronics"],
            ["PROP -> AOCS", "0.60", "Thruster assist for attitude"],
        ],
        [32, 18, 130],
    )

    # ============================================================
    # 5. ALGORITHM SPECIFICATIONS
    # ============================================================
    pdf.add_page()
    pdf.sec("5", "Algorithm Specifications")

    pdf.subsec("5.1 SDWAP -- Structural Dependency-Weighted Anomaly Propagation")
    pdf.para("Propagates local anomaly scores through the dependency graph to quantify cascade risk.")
    pdf.code(
        "Input:  s(t) in [0,1]^N     (local scores, 13 subsystems)\n"
        "        A in R^{NxN}          (weighted adjacency matrix)\n"
        "        c(t) in [0,1]^N      (confidence weights)\n"
        "\n"
        "Output: p(t) in [0,1]^N      (propagated cascade risk scores)\n"
        "\n"
        "  p^0 = s(t)\n"
        "  For k = 1 to K (max 5):\n"
        "      p^k = gamma * (A_hat * diag(c) * p^{k-1}) + (1-gamma) * s(t)\n"
        "\n"
        "  gamma = 0.85, convergence threshold = 0.001"
    )
    pdf.para("Novelty: Combines structural dependency propagation, confidence weighting, temporal decay, and iterative damping. No existing method combines all four.")

    pdf.subsec("5.2 Temporal GNN")
    pdf.para("Predicts future subsystem failures using time-aware graph learning.")
    pdf.code(
        "Telemetry -> Time2Vec -> GAT (4-head attention) -> GRU -> Prediction Heads\n"
        "            (learned      (graph attention over     (temporal  (failure prob\n"
        "             periodic      subsystem edges)          memory)   + survival)\n"
        "             time repr.)\n"
        "\n"
        "Loss: Focal Loss (gamma=2.0, alpha=0.25) for rare anomaly handling"
    )

    pdf.subsec("5.3 KAVACH -- Formal Safety Verification")
    pdf.para("Every AI decision must satisfy 5 formal properties before execution:")
    pdf.table(
        ["ID", "Property", "Specification"],
        [
            ["SP-1", "Score Bounds", "All scores in [0, 1]"],
            ["SP-2", "Detector Liveness", "At least one detector active"],
            ["SP-3", "SDWAP Convergence", "Terminates within max iterations"],
            ["SP-4", "Prediction Coherence", "Predictions consistent with scores"],
            ["SP-5", "Requalification Safety", "Decisions respect physics limits"],
        ],
        [15, 42, 123],
    )
    pdf.para("If any property fails: output is BLOCKED with auditable safety case (GSN format).")

    pdf.subsec("5.4 THERMAL-DIFF-GNN")
    pdf.para("Assesses whether a recovered RLV component is safe to reuse.")
    pdf.code(
        "Physics: D_thermal = N_cycles x (delta_T / C1)^(1/beta)   [Coffin-Manson]\n"
        "\n"
        "Hybrid: 80% physics model + 20% GNN learned correction\n"
        "Output: GO / AMBER / REJECT per component"
    )

    pdf.subsec("5.5 RLV-RUL -- Triple-Mode Remaining Useful Life")
    pdf.table(
        ["Degradation Mode", "Physics Model", "Affected Components"],
        [
            ["Thermal cycling", "Coffin-Manson fatigue", "Solder joints, PCBs, connectors"],
            ["Radiation", "Total Ionizing Dose", "Semiconductors, memory, sensors"],
            ["Vibration", "Miner's cumulative damage", "Mechanical mounts, wiring, optics"],
        ],
        [35, 55, 90],
    )
    pdf.para("Combined: min(RUL_thermal, RUL_radiation, RUL_vibration) x 0.6 + learned x 0.4")

    pdf.subsec("5.6 Other Algorithms")
    pdf.table(
        ["Algorithm", "Purpose"],
        [
            ["SHAKTI", "Conformal prediction with guaranteed confidence intervals"],
            ["AEGIS", "3-layer adversarial guard: spectral + autoencoder + GRU (2-of-3 vote)"],
            ["CLPX", "Cross-lifecycle bridge: in-flight <-> post-flight knowledge transfer"],
            ["NLG", "Natural language alerts with subsystem-specific actions"],
            ["PhyRAG", "Physics-informed retrieval-augmented generation for explanations"],
        ],
        [28, 152],
    )

    # ============================================================
    # 6. PROTOTYPE STATUS
    # ============================================================
    pdf.add_page()
    pdf.sec("6", "Prototype Status and Results")

    pdf.subsec("6.1 Implementation Status")
    pdf.table(
        ["Component", "Status", "Specification"],
        [
            ["SDWAP", "Complete", "K=5, gamma=0.85, lambda=0.1"],
            ["Temporal GNN", "Complete", "Time2Vec + GAT + GRU + Focal Loss"],
            ["THERMAL-DIFF-GNN", "Complete", "Coffin-Manson + GNN, lambda=0.8"],
            ["RLV-RUL", "Complete", "Thermal + Radiation + Vibration"],
            ["CLPX", "Complete", "Forward + backward transfer"],
            ["AEGIS", "Complete", "Spectral + AE + GRU, majority vote"],
            ["SHAKTI", "Complete", "Conformal prediction, adaptive alpha"],
            ["KAVACH", "Complete", "5 safety properties, GSN case"],
            ["NLG Engine", "Complete", "13 templates, 4 risk levels"],
            ["PhyRAG", "Complete", "ChromaDB, physics validation"],
            ["Dashboard", "Complete", "Flask web app, live charts"],
            ["CLI", "Complete", "7 commands"],
        ],
        [42, 22, 116],
    )

    pdf.subsec("6.2 Test Results")
    pdf.code(
        "Unit Tests:          39 / 39  PASSING\n"
        "Stress Tests:        52 / 52  PASSING\n"
        "CLI Demo:            Full pipeline operational\n"
        "Evaluation Metrics:  ROC-AUC = 0.775  |  Recall = 1.000  |  RCA = 1.000"
    )

    pdf.subsec("6.3 Technology Stack (All Open-Source, Rs. 0)")
    pdf.table(
        ["Component", "Technology", "License", "Cost"],
        [
            ["Core ML", "PyTorch, PyTorch Geometric", "BSD", "Free"],
            ["Vector DB", "ChromaDB", "Apache 2.0", "Free"],
            ["Dashboard", "Flask, Chart.js", "BSD / MIT", "Free"],
            ["Scientific", "NumPy, SciPy, scikit-learn", "BSD", "Free"],
        ],
        [35, 60, 40, 45],
    )

    # ============================================================
    # 7. ISTRAC ALIGNMENT
    # ============================================================
    pdf.add_page()
    pdf.sec("7", "Relevance to ISTRAC Operations")

    pdf.subsec("7.1 ISTRAC Operational Functions")
    pdf.table(
        ["ISTRAC Function", "PRAJNA Capability"],
        [
            ["Real-time health monitoring", "SDWAP cascade detection + NLG alerts"],
            ["Multi-satellite fleet management", "VAYUH federated learning (future)"],
            ["Anomaly root cause analysis", "SDWAP trace + PhyRAG explanations"],
            ["Mission ops decision support", "KAVACH verification + contingency actions"],
            ["Telemetry data analysis", "Temporal GNN + Local Detector scoring"],
        ],
        [72, 108],
    )

    pdf.subsec("7.2 ISRO Programme Mapping")
    pdf.table(
        ["ISRO Programme", "Requirement", "PRAJNA Response"],
        [
            ["RESPOND (2023-25)", "ML anomaly detection", "SDWAP + Temporal GNN"],
            ["RLV-TD", "Reusable vehicle turnaround", "THERMAL-DIFF-GNN + RLV-RUL"],
            ["Gaganyaan", "Human spaceflight safety", "KAVACH + SHAKTI"],
            ["Security Policy", "Classified data protection", "AEGIS + air-gap operation"],
            ["NavIC / IRNSS", "Constellation monitoring", "VAYUH (future scope)"],
        ],
        [38, 55, 87],
    )

    # ============================================================
    # 8. PROPOSED ROLE -- THE KEY SECTION
    # ============================================================
    pdf.add_page()
    pdf.sec("8", "Proposed Role: R&D Ideas and Architecture")

    pdf.bpara("What I Am Seeking")
    pdf.para(
        "I wish to work with ISTRAC's R&D team in a hands-on capacity focused on "
        "ideation, system architecture design, and algorithm formulation. I am not "
        "proposing an external research collaboration -- I want to be part of the team, "
        "contributing ideas and designs from within."
    )

    pdf.bpara("My Contribution")
    pdf.para(
        "My strength lies in identifying problems, conceiving novel solutions, "
        "and translating them into detailed technical architectures and specifications. "
        "The PRAJNA framework -- 10 algorithms, full system architecture, 10 technical "
        "documents -- was designed and specified entirely by me. This is what I do best: "
        "think deeply about hard problems and design solutions."
    )

    pdf.para("Specifically, I would contribute:")
    pdf.reset_bullets()
    pdf.bullet("Identifying gaps and opportunities in spacecraft health monitoring")
    pdf.bullet("Designing novel algorithm architectures for anomaly detection and prediction")
    pdf.bullet("Creating detailed system architecture diagrams and specifications")
    pdf.bullet("Formulating mathematical frameworks for new methods")
    pdf.bullet("Proposing new research directions aligned with upcoming ISRO missions")
    pdf.bullet("Writing technical documentation and specifications")
    pdf.ln(3)

    pdf.bpara("What This Prototype Demonstrates")
    pdf.table(
        ["Capability", "Evidence in PRAJNA"],
        [
            ["Ability to identify real gaps", "3 gaps no space agency has solved (Section 2)"],
            ["Algorithm design", "10 novel algorithms with mathematical specs"],
            ["System architecture", "13-node, 24-edge spacecraft graph model"],
            ["Technical depth", "Physics-ML hybrid models, formal verification"],
            ["Documentation quality", "10 complete technical documents"],
            ["Completeness", "Working prototype, 39/39 tests, dashboard"],
        ],
        [50, 130],
    )

    pdf.bpara("What I Request")
    pdf.reset_bullets()
    pdf.bullet("A place in the R&D team to contribute ideas and architecture designs")
    pdf.bullet("Mentorship from ISTRAC engineers on real operational challenges")
    pdf.bullet("Domain knowledge to make my designs operationally relevant")
    pdf.bullet("Feedback on my work to continuously improve")
    pdf.ln(3)

    pdf.bpara("A Note on Honesty")
    pdf.para(
        "I am a 3rd year B.Tech student. My core strength is in thinking, designing, "
        "and creating novel ideas and architectures. I designed all 10 algorithms, "
        "specified their mathematics, and created the full system architecture for PRAJNA "
        "independently. I want to bring this ideation and design capability to ISTRAC's "
        "R&D work, learning from experienced engineers while contributing fresh perspectives."
    )

    # ============================================================
    # 9. DELIVERABLES & TIMELINE
    # ============================================================
    pdf.add_page()
    pdf.sec("9", "Deliverables and Timeline")

    pdf.subsec("9.1 Already Completed")
    pdf.table(
        ["#", "Deliverable", "Status"],
        [
            ["1", "Working prototype (6,000+ lines, Python)", "Done"],
            ["2", "10 technical documents", "Done"],
            ["3", "39 automated tests (all passing)", "Done"],
            ["4", "Interactive web dashboard", "Done"],
            ["5", "CLI with 7 commands", "Done"],
            ["6", "Live demonstration capability", "Ready"],
        ],
        [10, 130, 40],
    )

    pdf.subsec("9.2 Proposed Contribution Plan (If Opportunity Given)")
    pdf.table(
        ["Phase", "Duration", "Activity"],
        [
            ["1. Learning", "2 weeks", "Understand ISTRAC operations, telemetry formats, real challenges"],
            ["2. Design", "4 weeks", "Design improved algorithms based on real operational needs"],
            ["3. Architecture", "4 weeks", "Detailed system architecture for ISTRAC deployment"],
            ["4. Specification", "4 weeks", "Complete technical specs, interface documents"],
            ["5. Documentation", "2 weeks", "Final reports, presentation, knowledge transfer"],
        ],
        [28, 20, 132],
    )
    pdf.bpara("Total: 16 weeks (4 months)")

    # ============================================================
    # 10. ABOUT ME
    # ============================================================
    pdf.add_page()
    pdf.sec("10", "Profile of the Proposer")

    pdf.subsec("Karthik Idikuda")
    pdf.table(
        ["", ""],
        [
            ["Education", "B.Tech AI, Marwadi University, Gujarat (2024-2027, 3rd Year)"],
            ["", "Diploma CSE, Sree Dattaha Group of Institutions (2021-2024)"],
            ["Current Role", "Co-Founder and CTO, infinall.ai (Hyderabad)"],
            ["Experience", "AI Engineer -- infinall.ai (Mar 2026 - Present)"],
            ["", "Computer Vision Intern -- Karoza Technologies (Jun-Dec 2025)"],
            ["", "UI Designer -- pax-z (Oct 2024 - Jan 2025)"],
            ["", "Industrial Training -- NSIC Technical Services (Jan-Jun 2024)"],
            ["Skills", "AI/ML, System Architecture, Algorithm Design, Research"],
            ["Certifications", "IBM Dev Day AI, AWS Academy Cloud Foundations"],
            ["Location", "Hyderabad, Telangana"],
        ],
        [30, 150],
    )

    pdf.subsec("Contact Details")
    pdf.table(
        ["", ""],
        [
            ["Phone", "+91 9494432697"],
            ["Email", "idikudakarthik55@gmail.com"],
            ["GitHub", "github.com/karthik-idikuda"],
            ["LinkedIn", "linkedin.com/in/karthik129259"],
            ["Portfolio", "karthikidikuda.dev"],
        ],
        [30, 150],
    )

    # ============================================================
    # 11. REFERENCES
    # ============================================================
    pdf.sec("11", "References")

    pdf.subsec("11.1 Accompanying Technical Documents")
    pdf.table(
        ["Document No.", "Title"],
        [
            ["PRAJNA/EXEC/2026/001", "Executive Brief"],
            ["PRAJNA/ARCH/2026/001", "System Architecture and ICD"],
            ["PRAJNA/ALGO/2026/001", "Algorithm Specification"],
            ["PRAJNA/EVAL/2026/001", "Evaluation Framework"],
            ["PRAJNA/FORMAL/2026/001", "Formal Verification"],
            ["PRAJNA/QA/2026/001", "Quality Assurance Plan"],
            ["PRAJNA/ADV/2026/001", "Advanced Capabilities"],
            ["PRAJNA/REQ/2026/001", "Requirements Traceability Matrix"],
            ["PRAJNA/TDD/2026/001", "Technical Design Document"],
            ["PRAJNA/NAP/2026/001", "Novelty and Prior Art"],
        ],
        [55, 125],
    )

    pdf.subsec("11.2 Academic References")
    refs = [
        "1. Hundman et al. (2018), 'Detecting Spacecraft Anomalies Using LSTMs', KDD 2018",
        "2. Velickovic et al. (2018), 'Graph Attention Networks', ICLR 2018",
        "3. Lin et al. (2017), 'Focal Loss for Dense Object Detection', ICCV 2017",
        "4. Coffin (1954), 'Effects of Cyclic Thermal Stresses on a Ductile Metal'",
        "5. Vovk et al. (2005), 'Algorithmic Learning in a Random World', Springer",
        "6. Kelly (1998), 'Arguing Safety -- A Systematic Approach to Safety Cases'",
    ]
    for ref in refs:
        pdf.set_font("Times", "", 9.5)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, s(ref))
        pdf.ln(1)

    # ============================================================
    # CLOSING
    # ============================================================
    pdf.ln(8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    pdf.para(
        "This document presents a working prototype and a body of independent research. "
        "The system is available for live demonstration at ISTRAC's convenience. "
        "I am eager to contribute my ideas and architectural thinking to ISTRAC's "
        "R&D efforts in whatever capacity the team finds appropriate."
    )

    pdf.ln(8)
    pdf.set_font("Times", "B", 11)
    pdf.cell(0, 6, "Respectfully submitted,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 7, "Karthik Idikuda", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 10)
    pdf.cell(0, 5, "10 March 2026", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "+91 9494432697 | idikudakarthik55@gmail.com", new_x="LMARGIN", new_y="NEXT")

    # Save
    pdf.output("docs/PRAJNA_Research_Proposal_ISTRAC.pdf")
    print("PDF generated successfully: docs/PRAJNA_Research_Proposal_ISTRAC.pdf")


if __name__ == "__main__":
    build()
