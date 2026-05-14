from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _cell_paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    """Plain text in a table cell, wrapped; safe for XML/Paragraph."""
    raw = "" if text is None else str(text)
    return Paragraph(escape(raw).replace("\n", "<br/>"), style)


def _priority_rank(priority: str) -> int:
    p = (priority or "").strip().lower()
    if p == "fix now":
        return 0
    if p == "fix soon":
        return 1
    return 2


def _build_prioritized_actions(findings: List[Dict[str, Any]]) -> List[str]:
    actions = []
    seen = set()
    sorted_findings = sorted(
        findings,
        key=lambda f: (
            _priority_rank(str(f.get("remediation_priority", "Hardening"))),
            str(f.get("severity", "")),
        ),
    )
    for finding in sorted_findings:
        vtype = finding.get("vulnerability_type", "Security issue")
        rec = (finding.get("fix") or {}).get("recommendation") or "Apply secure coding controls for this pattern."
        priority = finding.get("remediation_priority", "Hardening")
        msg = f"[{priority}] {vtype}: {rec}"
        if msg in seen:
            continue
        seen.add(msg)
        actions.append(msg)
        if len(actions) >= 10:
            break
    return actions


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
        "prioritized_actions": _build_prioritized_actions(findings),
        "testing_checklist": [
            "Validate all user-controlled input boundaries and allowed formats.",
            "Run negative tests for SQLi/XSS/command-injection payloads.",
            "Verify authN/authZ checks for privileged and sensitive routes.",
            "Scan dependencies and update vulnerable packages with known fixes.",
            "Re-test high-priority issues after remediation before release.",
        ],
    }

    return report


def generate_pdf_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """
    Render a simple, professional-looking PDF report from structured data.

    This layer focuses purely on presentation; detection, scoring, and fixes
    are handled elsewhere.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Landscape + slightly tighter margins so wide findings tables fit without clipping.
    page = landscape(A4)
    side_margin = 36
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=page,
        leftMargin=side_margin,
        rightMargin=side_margin,
        topMargin=42,
        bottomMargin=42,
    )
    usable_w = page[0] - 2 * side_margin

    styles = getSampleStyleSheet()
    hdr_style = ParagraphStyle(
        "FindingsHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.whitesmoke,
    )
    cell_style = ParagraphStyle(
        "FindingsCell",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
    )

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

    # Detailed findings: landscape + fixed column widths + wrapped cells (no clipping).
    elements.append(Paragraph("<b>Detailed Findings</b>", styles["Heading2"]))
    findings = report_data.get("detailed_findings", [])
    if findings:
        header_row = [
            Paragraph("<b>File</b>", hdr_style),
            Paragraph("<b>Line</b>", hdr_style),
            Paragraph("<b>Type</b>", hdr_style),
            Paragraph("<b>Severity</b>", hdr_style),
            Paragraph("<b>CWE</b>", hdr_style),
            Paragraph("<b>Priority</b>", hdr_style),
            Paragraph("<b>Business Impact</b>", hdr_style),
        ]
        data = [header_row]
        for f in findings:
            data.append(
                [
                    _cell_paragraph(f.get("file", ""), cell_style),
                    _cell_paragraph(f.get("line", ""), cell_style),
                    _cell_paragraph(f.get("vulnerability_type", ""), cell_style),
                    _cell_paragraph(f.get("severity", ""), cell_style),
                    _cell_paragraph(f.get("cwe") or "", cell_style),
                    _cell_paragraph(f.get("remediation_priority") or "Hardening", cell_style),
                    _cell_paragraph(f.get("business_impact", ""), cell_style),
                ]
            )
        # Widths sum to usable_w so the table fits the body frame.
        col_w = [
            usable_w * 0.24,
            usable_w * 0.045,
            usable_w * 0.11,
            usable_w * 0.08,
            usable_w * 0.065,
            usable_w * 0.09,
            usable_w * 0.37,
        ]
        table = Table(data, colWidths=col_w, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("LEADING", (0, 1), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 12))

    actions = report_data.get("prioritized_actions", [])
    if actions:
        elements.append(Paragraph("<b>Prioritized Remediation Plan</b>", styles["Heading2"]))
        for idx, action in enumerate(actions, start=1):
            elements.append(Paragraph(f"{idx}. {action}", styles["Normal"]))
        elements.append(Spacer(1, 8))

    doc.build(elements)

