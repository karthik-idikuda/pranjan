#!/usr/bin/env python3
"""
Generate formal internship application letter for ISTRAC HRD.
Clean, government-style, single-page formal letter.
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
    )


class LetterPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Times", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, "Karthik Idikuda | Internship Application | ISTRAC", align="C")


def build():
    pdf = LetterPDF()
    pdf.set_margins(25, 20, 25)
    pdf.set_auto_page_break(True, 20)
    pdf.add_page()

    # --- FROM address (top right) ---
    pdf.set_font("Times", "", 11)
    pdf.set_text_color(0, 0, 0)

    pdf.cell(0, 5.5, s("Karthik Idikuda"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("B.Tech Artificial Intelligence (3rd Year)"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("Marwadi University, Rajkot, Gujarat"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("Phone: +91 9494432697"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("Email: idikudakarthik55@gmail.com"), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 5.5, s("Date: 12 March 2026"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # --- TO address ---
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 5.5, s("To,"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("The Head, Human Resource Development"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("ISRO Telemetry, Tracking and Command Network (ISTRAC)"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, s("Bangalore - 560058"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # --- Subject ---
    pdf.set_font("Times", "B", 11)
    pdf.cell(0, 6, s("Subject: Application for R&D Internship at ISTRAC"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # --- Reference ---
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 5.5, s("Reference: Communication with Shri Amit Kumar Singh, SpOA, ISTRAC"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # --- Body ---
    pdf.set_font("Times", "", 11)

    pdf.cell(0, 5.5, s("Respected Sir/Madam,"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    body_paras = [
        (
            "I am Karthik Idikuda, a 3rd year B.Tech Artificial Intelligence student at "
            "Marwadi University, Gujarat. I respectfully submit this application for an "
            "R&D internship at ISTRAC, Bangalore. I have been in communication with "
            "Shri Amit Kumar Singh (SpOA, ISTRAC) regarding my research work, and on his "
            "guidance, I am submitting this formal application to the HRD department."
        ),
        (
            "I have independently designed a spacecraft health intelligence framework "
            "called PRAJNA (Predictive Reasoning Architecture for Joint Network-wide "
            "Anomalics). The framework models inter-subsystem dependencies in spacecraft "
            "using graph neural networks and includes 10 novel algorithms, complete system "
            "architecture, and a working prototype with 39 out of 39 automated tests passing. "
            "The detailed technical proposal is attached for your review."
        ),
        (
            "My core strength lies in research thinking, problem identification, and "
            "designing novel system architectures and algorithms. I wish to contribute "
            "to ISTRAC's R&D efforts by providing fresh ideas, identifying gaps in "
            "existing systems, and designing solutions -- while learning from ISTRAC's "
            "experienced engineers and gaining exposure to real operational challenges."
        ),
    ]

    for para in body_paras:
        pdf.multi_cell(0, 5.5, s(para))
        pdf.ln(3)

    # --- Details section ---
    pdf.set_font("Times", "B", 11)
    pdf.cell(0, 6, s("Internship Details:"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Times", "", 11)

    details = [
        ("Preferred Duration", "1 May 2026 to 31 August 2026 (4 months)"),
        ("Area of Interest", "Research & Development"),
        ("Focus Areas", "Algorithm design, system architecture, problem-solving"),
        ("Current CGPA", "Available on request"),
    ]
    for label, val in details:
        pdf.set_x(30)
        pdf.set_font("Times", "B", 11)
        pdf.cell(52, 5.5, s(f"{label}:"))
        pdf.set_font("Times", "", 11)
        pdf.cell(0, 5.5, s(val), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    pdf.set_font("Times", "", 11)
    pdf.multi_cell(0, 5.5, s(
        "I am also the Co-Founder and CTO of infinall.ai, a Hyderabad-based startup, "
        "which reflects my initiative and commitment to technology innovation."
    ))
    pdf.ln(3)

    pdf.multi_cell(0, 5.5, s(
        "I am willing to complete any formalities, provide additional documents, or "
        "appear for an interview as required. I would be grateful for the opportunity "
        "to contribute to ISTRAC's R&D work."
    ))
    pdf.ln(3)

    pdf.cell(0, 5.5, s("Thank you for your time and kind consideration."), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # --- Signature ---
    pdf.cell(0, 5.5, s("Yours sincerely,"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 6, s("Karthik Idikuda"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 10)
    pdf.cell(0, 5, s("B.Tech AI (3rd Year), Marwadi University"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, s("+91 9494432697 | idikudakarthik55@gmail.com"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # --- Enclosures ---
    pdf.set_draw_color(0, 0, 0)
    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 5, s("Enclosures:"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 10)
    pdf.cell(0, 5, s("1. PRAJNA Technical Proposal (PRAJNA/PROP/2026/001)"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, s("2. Resume / CV"), new_x="LMARGIN", new_y="NEXT")

    # Save
    out = "docs/ISTRAC_Internship_Application_Karthik_Idikuda.pdf"
    pdf.output(out)
    print(f"Application letter generated: {out}")


if __name__ == "__main__":
    build()
