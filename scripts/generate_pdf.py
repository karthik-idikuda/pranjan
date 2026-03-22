#!/usr/bin/env python3
"""Generate PDF from PRAJNA Research Proposal markdown."""
import markdown
import weasyprint

# Read the markdown file
with open("docs/PRAJNA_Research_Proposal_ISTRAC.md", "r") as f:
    md_content = f.read()

# Convert markdown to HTML
html_body = markdown.markdown(
    md_content,
    extensions=["tables", "fenced_code", "codehilite", "toc"],
)

CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {
        content: "PRAJNA Research Proposal";
        font-size: 8pt;
        color: #666;
    }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #666;
    }
}
body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
}
h1 {
    font-size: 22pt;
    color: #0d3b66;
    border-bottom: 3px solid #0d3b66;
    padding-bottom: 8px;
    margin-top: 30px;
}
h2 {
    font-size: 16pt;
    color: #14619b;
    border-bottom: 1.5px solid #14619b;
    padding-bottom: 5px;
    margin-top: 25px;
    page-break-after: avoid;
}
h3 {
    font-size: 13pt;
    color: #1a7bc0;
    margin-top: 18px;
    page-break-after: avoid;
}
h4 { font-size: 11pt; color: #333; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 10pt;
    page-break-inside: avoid;
}
th {
    background-color: #0d3b66;
    color: white;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
}
td {
    padding: 6px 10px;
    border-bottom: 1px solid #ddd;
}
tr:nth-child(even) { background-color: #f8f9fa; }
code {
    background-color: #f4f4f4;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 9.5pt;
    font-family: 'Courier New', monospace;
}
pre {
    background-color: #1e1e2e;
    color: #a9b1d6;
    padding: 15px;
    border-radius: 6px;
    font-size: 9pt;
    line-height: 1.4;
    overflow-x: auto;
    page-break-inside: avoid;
}
pre code {
    background: none;
    color: inherit;
    padding: 0;
}
hr {
    border: none;
    border-top: 2px solid #0d3b66;
    margin: 25px 0;
}
strong { color: #0d3b66; }
blockquote {
    border-left: 4px solid #14619b;
    margin: 10px 0;
    padding: 8px 15px;
    background: #f0f5fa;
}
a { color: #14619b; }
"""

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

# Write HTML for reference
with open("docs/PRAJNA_Research_Proposal_ISTRAC.html", "w") as f:
    f.write(html)

# Convert to PDF
weasyprint.HTML(string=html).write_pdf("docs/PRAJNA_Research_Proposal_ISTRAC.pdf")
print("PDF generated: docs/PRAJNA_Research_Proposal_ISTRAC.pdf")
