from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_security_report(
    project_id: str,
    findings: List[Dict[str, Any]],
    risk_data: Dict[str, Any],
    files: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Build a structured, professional-style security report object.

    Structured reporting is critical in enterprise security because:
    - it lets teams track risk over time,
    - supports audits and compliance,
    - and separates raw detection from how results are communicated.
    """
    total_files_scanned = len(files or [])
    total_vulns = len(findings)

    # Vulnerability distribution by type
    vuln_dist: Dict[str, int] = {}
    # Severity distribution
    sev_dist: Dict[str, int] = {"High": 0, "Medium": 0, "Low": 0}

    for f in findings:
        vtype = f.get("vulnerability_type", "Unknown")
        vuln_dist[vtype] = vuln_dist.get(vtype, 0) + 1

        sev = f.get("severity", "Medium")
        if sev in sev_dist:
            sev_dist[sev] += 1
        else:
            sev_dist[sev] = sev_dist.get(sev, 0) + 1

    risk_score = risk_data.get("total_score", 0)
    risk_level = risk_data.get("risk_level", "Low")

    # Simple executive summary text based on risk level.
    if risk_level == "High":
        executive_summary = (
            "The project contains multiple high-risk vulnerabilities, including issues such as "
            "SQL Injection, XSS, or Command Injection. Immediate remediation is strongly recommended."
        )
    elif risk_level == "Medium":
        executive_summary = (
            "The project shows a moderate security risk with several vulnerabilities present. "
            "Prioritize fixing higher-severity findings to reduce exposure."
        )
    else:
        executive_summary = (
            "The project currently appears to have a relatively low security risk. "
            "Continue to follow secure coding practices and monitor for new issues."
        )

    report = {
        "project_id": project_id,
        "executive_summary": executive_summary,
        "scan_summary": {
            "total_files_scanned": total_files_scanned,
            "total_vulnerabilities": total_vulns,
            "risk_score": risk_score,
            "risk_level": risk_level,
        },
        "vulnerability_distribution": vuln_dist,
        "severity_distribution": sev_dist,
        "detailed_findings": findings,
    }

    return report


def generate_pdf_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """
    Render a simple, professional-looking PDF report from structured data.

    This layer focuses purely on presentation; detection, scoring, and fixes
    are handled elsewhere.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("Security Scan Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Project + risk
    proj_info = Paragraph(
        f"<b>Project ID:</b> {report_data.get('project_id')}<br/>"
        f"<b>Risk Level:</b> {report_data.get('scan_summary', {}).get('risk_level', 'N/A')}<br/>"
        f"<b>Risk Score:</b> {report_data.get('scan_summary', {}).get('risk_score', 0)}",
        styles["Normal"],
    )
    elements.append(proj_info)
    elements.append(Spacer(1, 12))

    # Executive summary
    elements.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    elements.append(
        Paragraph(report_data.get("executive_summary", "No summary available."), styles["Normal"])
    )
    elements.append(Spacer(1, 12))

    # Vulnerability distribution
    elements.append(Paragraph("<b>Vulnerability Distribution</b>", styles["Heading3"]))
    vuln_dist = report_data.get("vulnerability_distribution", {})
    if vuln_dist:
        data = [["Type", "Count"]] + [[k, str(v)] for k, v in vuln_dist.items()]
        table = Table(data, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ]
            )
        )
        elements.append(table)
    elements.append(Spacer(1, 12))

    # Severity distribution
    elements.append(Paragraph("<b>Severity Distribution</b>", styles["Heading3"]))
    sev_dist = report_data.get("severity_distribution", {})
    if sev_dist:
        data = [["Severity", "Count"]] + [[k, str(v)] for k, v in sev_dist.items()]
        table = Table(data, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ]
            )
        )
        elements.append(table)
    elements.append(Spacer(1, 18))

    # Detailed findings table (limited columns for readability)
    elements.append(Paragraph("<b>Detailed Findings</b>", styles["Heading2"]))
    findings = report_data.get("detailed_findings", [])
    if findings:
        data = [["File", "Line", "Type", "Severity"]]
        for f in findings:
            data.append(
                [
                    f.get("file", ""),
                    str(f.get("line", "")),
                    f.get("vulnerability_type", ""),
                    f.get("severity", ""),
                ]
            )
        table = Table(data, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ]
            )
        )
        elements.append(table)

    doc.build(elements)

