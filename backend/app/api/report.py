from __future__ import annotations

import io
import json
import re
from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from .. import models
from ..db.database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/report", tags=["report"])

REMEDIATION_DESCRIPTIONS: dict[str, str] = {
    "sql-injection": (
        "The student identified and eliminated string interpolation in SQL queries, replacing them "
        "with parameterized queries that prevent user input from being interpreted as SQL syntax."
    ),
    "xss": (
        "The student replaced innerHTML usage with textContent and implemented input escaping, "
        "preventing attacker-controlled scripts from executing in victim browsers."
    ),
    "command-injection": (
        "The student replaced shell=True subprocess calls with argument list invocations, "
        "eliminating the shell interpreter that allowed command chaining."
    ),
    "csrf": (
        "The student implemented CSRF token validation on state-changing endpoints, ensuring cross-origin "
        "requests cannot silently act on behalf of authenticated users."
    ),
    "broken-auth": (
        "The student replaced plaintext password storage and comparison with bcrypt hashing, ensuring "
        "credential breaches do not expose recoverable passwords."
    ),
    "directory-traversal": (
        "The student added path canonicalization and base-directory validation, preventing file path "
        "traversal outside the intended directory."
    ),
    "xxe": (
        "The student disabled XML external entity resolution in the parser configuration, eliminating the "
        "attack surface for XXE-based file disclosure."
    ),
    "insecure-storage": (
        "The student replaced in-memory storage with a persistent database-backed store, eliminating data "
        "loss and unauthorized access risks."
    ),
    "security-misc": (
        "The student corrected the server misconfiguration that exposed sensitive endpoints and debug "
        "information to unauthenticated users."
    ),
    "broken-access-control": (
        "The student implemented proper role-based access checks on all sensitive routes, preventing "
        "privilege escalation attacks."
    ),
}


def _fmt_date(dt: datetime | None) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%d %B %Y")


def _fmt_duration(total_seconds: int | None) -> str:
    secs = int(total_seconds or 0)
    return f"{secs // 60}m {secs % 60}s"


def _safe_json_loads(raw: str | None):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _slugify_text(value: str) -> str:
    lowered = (value or "").strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-")


def _prettify_slug(slug: str) -> str:
    return (slug or "").replace("-", " ").title()


def _wrap_lines(text: str, max_chars: int) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_wrapped(c, text: str, x: float, y: float, max_chars: int = 100, leading: float = 14.0):
    for line in _wrap_lines(text, max_chars):
        c.drawString(x, y, line)
        y -= leading
    return y


def _flatten_vulnerability_summary(vuln_summary: dict) -> list[dict]:
    if not isinstance(vuln_summary, dict):
        return []

    # Primary path: full scan result with findings array
    if isinstance(vuln_summary.get("findings"), list):
        results = []
        for item in vuln_summary["findings"]:
            if not isinstance(item, dict):
                continue
            results.append({
                "vulnerability_type": (
                    item.get("vulnerability_type")
                    or item.get("type")
                    or "Unknown"
                ),
                "severity": item.get("severity", "Medium"),
                "file": item.get("file"),
                "line": item.get("line"),
                "description": (
                    item.get("fix", {}).get("explanation")
                    or item.get("code_snippet", "")[:120]
                    or "No description available."
                ),
                "recommendation": (
                    item.get("fix", {}).get("recommendation", "")
                ),
                "cwe": item.get("cwe"),
            })
        return results

    # Secondary path: summary sub-object with count map
    # e.g. {"vulnerability_counts": {"SQL Injection": 2}}
    counts = vuln_summary.get("vulnerability_counts", {})
    if not isinstance(counts, dict):
        counts = {}

    # Legacy fallback: flat count map {"SQL Injection": 2}
    if not counts:
        for key, value in vuln_summary.items():
            if isinstance(value, int):
                counts[key] = value

    findings = []
    for key, value in counts.items():
        if isinstance(value, int):
            for _ in range(max(0, value)):
                findings.append({
                    "vulnerability_type": str(key),
                    "severity": "Medium",
                    "file": None,
                    "line": None,
                    "description": f"Detected {key} issue.",
                    "recommendation": "",
                    "cwe": None,
                })
    return findings


def _derive_risk_level(findings: list[dict]) -> str:
    severities = {
        str(f.get("severity", "")).strip().lower()
        for f in findings
    }
    if "critical" in severities:
        return "CRITICAL"
    if "high" in severities:
        return "HIGH"
    if "medium" in severities:
        return "MEDIUM"
    return "LOW"


def _severity_sort_key(severity: str | None) -> int:
    s = str(severity or "").strip().lower()
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(s, 4)


def _line_sort_key(line: object) -> int:
    try:
        return int(line)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _priority_label(severity: str | None) -> str:
    s = str(severity or "").strip().lower()
    if s == "critical":
        return "P1 — Critical"
    if s == "high":
        return "P2 — High"
    if s == "medium":
        return "P3 — Medium"
    if s == "low":
        return "P4 — Low"
    return "P5 — Unknown"


def _technical_findings_from_summary(vuln_summary: dict) -> list[dict]:
    """
    Findings for a technical pentest-style report: includes code context and fix guidance.
    """
    if not isinstance(vuln_summary, dict):
        return []
    items = vuln_summary.get("findings")
    if not isinstance(items, list) or not items:
        return list(_flatten_vulnerability_summary(vuln_summary))
    results: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        fix = item.get("fix") if isinstance(item.get("fix"), dict) else {}
        snippet = item.get("code_snippet") or item.get("code") or ""
        results.append(
            {
                "vulnerability_type": (
                    item.get("vulnerability_type") or item.get("type") or "Unknown"
                ),
                "severity": item.get("severity", "Medium"),
                "file": item.get("file"),
                "line": item.get("line"),
                "description": (
                    (fix.get("explanation") if isinstance(fix, dict) else None)
                    or (str(snippet)[:500] if snippet else "")
                    or "No description available."
                ),
                "recommendation": (fix.get("recommendation", "") if isinstance(fix, dict) else "") or "",
                "cwe": item.get("cwe"),
                "code_snippet": str(snippet)[:1200] if snippet else "",
                "engine": item.get("engine"),
                "rule_id": item.get("rule_id"),
            }
        )
    return results


def _resolve_owned_scan(
    db: Session,
    current_user: models.User,
    project_id: Optional[str],
) -> tuple[models.ScanHistory, models.Project]:
    if project_id:
        row = (
            db.query(models.ScanHistory, models.Project)
            .join(models.Project, models.Project.id == models.ScanHistory.project_id)
            .filter(models.ScanHistory.project_id == project_id)
            .filter(models.Project.owner_id == current_user.id)
            .order_by(models.ScanHistory.scan_date.desc())
            .first()
        )
        if not row:
            raise HTTPException(
                status_code=404,
                detail="No scan found for this project or you do not own this project.",
            )
        return row
    latest_scan = (
        db.query(models.ScanHistory, models.Project)
        .join(models.Project, models.Project.id == models.ScanHistory.project_id)
        .filter(models.Project.owner_id == current_user.id)
        .order_by(models.ScanHistory.scan_date.desc())
        .first()
    )
    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scan found. Please scan a project first.")
    return latest_scan


@router.get("/pdf/scan")
def generate_technical_scan_pentest_pdf(
    project_id: Optional[str] = Query(
        None,
        description="Project id for the scan export (latest completed scan for that project)",
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Technical penetration-test style PDF: prioritized findings from static analysis only,
    with severity, affected location, evidence, and remediation — distinct from the
    platform learning/certificate report at GET /api/report/pdf.
    """
    scan_row, project_row = _resolve_owned_scan(db, current_user, project_id)
    vuln_summary = _safe_json_loads(scan_row.vuln_summary)
    findings = _technical_findings_from_summary(vuln_summary)
    findings.sort(
        key=lambda f: (
            _severity_sort_key(str(f.get("severity"))),
            str(f.get("file") or ""),
            _line_sort_key(f.get("line")),
        )
    )
    overall_risk = _derive_risk_level(findings)
    total = len(findings)

    sev_counts: dict[str, int] = {}
    for f in findings:
        sk = str(f.get("severity") or "Unknown").strip() or "Unknown"
        sev_counts[sk] = sev_counts.get(sk, 0) + 1

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setTitle("Technical Penetration Test Report — SAST")
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 100, "Technical Penetration Test Report")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 130, "Static Application Security Testing (SAST) — Findings & Remediation")
    c.setFont("Helvetica", 11)
    y = height - 180
    c.drawString(72, y, f"Engagement target: {project_row.name}")
    y -= 18
    c.drawString(72, y, f"Project / artifact ID: {project_row.id}")
    y -= 18
    c.drawString(72, y, f"Scan completed: {_fmt_date(scan_row.scan_date)}")
    y -= 18
    c.drawString(72, y, f"Report generated: {_fmt_date(datetime.utcnow())}")
    y -= 18
    c.drawString(72, y, f"Analyst / owner: {current_user.email}")
    y -= 18
    c.drawString(72, y, f"Total findings: {total}  |  Inferred risk posture: {overall_risk}")
    y -= 18
    c.drawString(
        72,
        y,
        f"SCAN risk score: {scan_row.risk_score} ({scan_row.risk_level})",
    )
    y -= 24
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#374151"))
    scope = (
        "This document summarises automated static analysis results (e.g. Semgrep and SCALE rules) "
        "for the assessed codebase. It is scoped to the latest stored scan for this project and does "
        "not include separate challenge completion or quiz history (see the dashboard learning report for that)."
    )
    y = _draw_wrapped(c, scope, 72, y, max_chars=95, leading=12)
    c.setFillColor(colors.black)
    y -= 16
    c.line(72, y, width - 72, y)
    c.showPage()

    # Executive summary + severity distribution
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, height - 60, "1. Executive summary")
    c.setFont("Helvetica", 10)
    y = height - 92
    intro = (
        f"The assessment identified {total} distinct finding(s) across the scanned source tree. "
        f"Findings are prioritised below by severity (Critical through Low). "
        "Each item includes remediation guidance suitable for developers."
    )
    y = _draw_wrapped(c, intro, 60, y, max_chars=100, leading=14)
    y -= 12
    if sev_counts:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y, "Findings by severity")
        y -= 16
        c.setFont("Helvetica", 10)
        for sev in sorted(sev_counts.keys(), key=lambda s: _severity_sort_key(s)):
            c.drawString(72, y, f"• {sev}: {sev_counts[sev]}")
            y -= 14
    y -= 24
    c.showPage()

    # Section 2 — priority index on its own page(s); wraps text; splits if tall.
    idx_margin_x = 52
    idx_table_w = width - 2 * idx_margin_x
    idx_page_top = height - 80
    idx_page_bottom = 52
    idx_usable_h = idx_page_top - idx_page_bottom
    _cw0, _cw1, _cw2, _cw3 = 22, 77, 94, 230
    col_widths = [_cw0, _cw1, _cw2, _cw3, idx_table_w - (_cw0 + _cw1 + _cw2 + _cw3)]

    hdr_par_style = ParagraphStyle(
        name="idx_hdr",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    cell_par_style = ParagraphStyle(
        name="idx_cell",
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
    )

    def _idx_cell(text: object, *, header: bool = False) -> Paragraph:
        st = hdr_par_style if header else cell_par_style
        return Paragraph(escape(str(text) if text is not None else "—"), st)

    idx_rows: list[list[Paragraph]] = [
        [
            _idx_cell("#", header=True),
            _idx_cell("Priority", header=True),
            _idx_cell("Vulnerability", header=True),
            _idx_cell("Location", header=True),
            _idx_cell("Severity", header=True),
        ]
    ]
    for i, f in enumerate(findings[:80], start=1):
        loc = f.get("file") or "—"
        ln = f.get("line")
        if ln is not None and str(ln).strip() != "":
            loc = f"{loc}:{ln}"
        idx_rows.append(
            [
                _idx_cell(str(i)),
                _idx_cell(_priority_label(f.get("severity"))),
                _idx_cell(f.get("vulnerability_type") or "Unknown"),
                _idx_cell(loc),
                _idx_cell(f.get("severity") or "—"),
            ]
        )
    if len(idx_rows) == 1:
        idx_rows.append(
            [
                _idx_cell("—"),
                _idx_cell("—"),
                _idx_cell("No findings in scan"),
                _idx_cell("—"),
                _idx_cell("—"),
            ]
        )

    idx_tbl = Table(idx_rows, colWidths=col_widths, repeatRows=1)
    idx_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#94a3b8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    c.setFont("Helvetica-Bold", 16)
    c.drawString(idx_margin_x, height - 52, "2. Finding priority index")

    parts = idx_tbl.split(idx_table_w, idx_usable_h)
    if not parts:
        parts = [idx_tbl]

    for pi, part in enumerate(parts):
        if pi > 0:
            c.showPage()
            c.setFont("Helvetica-Bold", 14)
            c.drawString(idx_margin_x, height - 52, "2. Finding priority index (continued)")
            idx_page_top = height - 80
            idx_usable_h = idx_page_top - idx_page_bottom

        _, part_h = part.wrapOn(c, idx_table_w, idx_usable_h)
        y_table_bottom = idx_page_top - part_h
        if y_table_bottom < idx_page_bottom:
            c.showPage()
            c.setFont("Helvetica-Bold", 14)
            c.drawString(idx_margin_x, height - 52, "2. Finding priority index (continued)")
            idx_page_top = height - 80
            idx_usable_h = idx_page_top - idx_page_bottom
            _, part_h = part.wrapOn(c, idx_table_w, idx_usable_h)
            y_table_bottom = idx_page_top - part_h
        part.drawOn(c, idx_margin_x, y_table_bottom)

    c.showPage()

    # Detailed findings
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, height - 55, "3. Detailed findings & remediation")
    y = height - 82

    for i, f in enumerate(findings, start=1):
        if y < 140:
            c.showPage()
            y = height - 55
        vuln_type = str(f.get("vulnerability_type") or "Unknown")
        sev = str(f.get("severity") or "Unknown")
        pr = _priority_label(sev)
        file_path = str(f.get("file")) if f.get("file") else "N/A"
        line_num = str(f.get("line")) if f.get("line") not in (None, "") else "—"
        cwe = str(f.get("cwe")) if f.get("cwe") else "Not mapped"
        desc = str(f.get("description") or "—")
        rem = str(f.get("recommendation") or "").strip()
        snippet = str(f.get("code_snippet") or "").strip()
        eng = str(f.get("engine") or "").strip()
        rule_id = str(f.get("rule_id") or "").strip()

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#0f172a"))
        c.drawString(60, y, f"Finding {i} — {vuln_type}")
        y -= 16
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#b91c1c") if sev.lower() in ("critical", "high") else colors.HexColor("#c2410c"))
        c.drawString(60, y, f"Priority: {pr}  |  Severity: {sev.upper()}")
        c.setFillColor(colors.black)
        y -= 14
        c.drawString(60, y, f"Location: {file_path}  |  Line: {line_num}  |  CWE: {cwe}")
        y -= 14
        if rule_id:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(60, y, f"Scanner rule: {rule_id}")
            c.setFont("Helvetica", 10)
            y -= 11
        if eng:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(60, y, f"Detection engine: {eng}")
            c.setFont("Helvetica", 10)
            y -= 12
        c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y, "Observation")
        y -= 12
        c.setFont("Helvetica", 9)
        y = _draw_wrapped(c, desc, 60, y, max_chars=100, leading=11)
        y -= 8
        if snippet:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(60, y, "Evidence (code excerpt)")
            y -= 12
            c.setFont("Courier", 8)
            y = _draw_wrapped(c, snippet.replace("\r", ""), 60, y, max_chars=95, leading=10)
            c.setFont("Helvetica", 10)
            y -= 6
            c.setFont("Helvetica-Oblique", 7.5)
            c.setFillColor(colors.HexColor("#64748b"))
            y = _draw_wrapped(
                c,
                "Note: Excerpt is the scanner-matched source range; if it diverges from the title, rely on rule id and path above.",
                60,
                y,
                max_chars=100,
                leading=10,
            )
            c.setFillColor(colors.black)
            y -= 6
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#15803d"))
        c.drawString(60, y, "Remediation (how to fix)")
        c.setFillColor(colors.black)
        y -= 12
        c.setFont("Helvetica", 9)
        fix_text = rem if rem else (
            "Apply secure coding patterns for this vulnerability class: validate and encode untrusted input, "
            "use safe APIs (parameterised queries, safe HTML serialisation, etc.), and retest with the scanner."
        )
        y = _draw_wrapped(c, fix_text, 60, y, max_chars=100, leading=11)
        y -= 10
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.line(60, y, width - 60, y)
        y -= 18

    if total == 0:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(60, y, "No vulnerabilities were reported for this scan.")

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    foot = (
        "Confidential — technical SAST output. Educational use on SCALE. "
        "Verify fixes in your environment before production release."
    )
    _draw_wrapped(c, foot, 60, 72, max_chars=105, leading=10)

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    pid_frag = re.sub(r"[^a-zA-Z0-9._-]+", "_", project_row.id or "project")
    date_fragment = datetime.utcnow().strftime("%Y%m%d")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=technical_pentest_{pid_frag}_{date_fragment}.pdf",
        },
    )


@router.get("/pdf")
def generate_pentest_report_pdf(
    project_id: Optional[str] = Query(None, description="Optional project id for a specific scan (latest for that project)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    scan_row, project_row = _resolve_owned_scan(db, current_user, project_id)
    vuln_summary = _safe_json_loads(scan_row.vuln_summary)
    findings = _flatten_vulnerability_summary(vuln_summary)
    overall_risk_level = _derive_risk_level(findings)

    # STEP 2: Collect completed challenges + state.
    completed_progress = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == current_user.id)
        .order_by(models.UserProgress.completed_at.asc())
        .all()
    )
    state_rows = (
        db.query(models.ChallengeState)
        .filter(models.ChallengeState.user_id == current_user.id)
        .all()
    )
    state_map = {row.challenge_id: row for row in state_rows}

    title_rows = db.query(models.Challenge).all()
    title_map = {_slugify_text(row.title): row.title for row in title_rows if row.title}

    completed_challenges: list[dict] = []
    for row in completed_progress:
        slug = row.challenge_id
        state = state_map.get(slug)
        mapped_title = title_map.get(_slugify_text(slug))
        completed_challenges.append(
            {
                "slug": slug,
                "title": mapped_title or _prettify_slug(slug),
                "hints_used": int(getattr(state, "hints_used", 0) or 0),
                "time_seconds": int(getattr(state, "time_spent_seconds", 0) or 0),
            }
        )

    # STEP 3: Collect quiz performance.
    attempts = (
        db.query(models.QuizAttempt)
        .filter(models.QuizAttempt.user_id == current_user.id)
        .order_by(models.QuizAttempt.completed_at.desc())
        .all()
    )
    total_attempts = len(attempts)
    percentages = [
        ((a.score / a.total) * 100.0) for a in attempts if (a.total or 0) > 0
    ]
    avg_score = round(sum(percentages) / len(percentages), 2) if percentages else 0.0
    best_score = round(max(percentages), 2) if percentages else 0.0

    # STEP 4: Collect fix evidence from logs.
    evidence_logs = (
        db.query(models.SecurityLog)
        .filter(models.SecurityLog.user_id == current_user.id)
        .filter(models.SecurityLog.context_type == "challenge")
        .filter(models.SecurityLog.event_type.ilike("%fix%"))
        .order_by(models.SecurityLog.created_at.desc())
        .all()
    )

    # Derived metrics for report text/table.
    total_vuln_count = len(findings) if findings else int(scan_row.total_vulnerabilities or 0)
    vuln_categories = len(set(
        f["vulnerability_type"] for f in findings
        if f.get("vulnerability_type")
    ))
    total_hints = sum(item["hints_used"] for item in completed_challenges)
    remediated_count = len(completed_challenges)
    attempted_challenges = len(state_rows)
    total_challenge_time = sum(int(getattr(row, "time_spent_seconds", 0) or 0) for row in state_rows)

    # STEP 5: Build PDF with required sections.
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # PAGE 1 - COVER PAGE.
    c.setTitle("Penetration Test Report")
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - 120, "Penetration Test Report")
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 160, "SCALE Security Learning Platform")

    y = height - 220
    c.setFont("Helvetica", 12)
    c.drawString(80, y, f"Prepared by: {current_user.email}")
    y -= 24
    c.drawString(80, y, f"Project assessed: {project_row.name}")
    y -= 24
    c.drawString(80, y, f"Scan date: {_fmt_date(scan_row.scan_date)}")
    y -= 24
    c.drawString(80, y, f"Report generated: {_fmt_date(datetime.utcnow())}")
    y -= 24
    c.drawString(80, y, f"Overall risk level: {overall_risk_level}")
    y -= 26
    c.line(80, y, width - 80, y)
    c.showPage()

    # PAGE 2 - EXECUTIVE SUMMARY.
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 70, "1. Executive Summary")
    c.setFont("Helvetica", 11)
    exec_summary = (
        f"This report documents the security assessment conducted on {project_row.name} using the "
        f"SCALE platform. The assessment identified {total_vuln_count} vulnerabilities across "
        f"{vuln_categories} categories. The student successfully remediated {remediated_count} "
        f"vulnerabilities through guided fix exercises."
    )
    y = _draw_wrapped(c, exec_summary, 60, height - 105, max_chars=105, leading=16)

    status_vuln = colors.HexColor("#ef4444") if total_vuln_count > 5 else (colors.HexColor("#f59e0b") if total_vuln_count > 2 else colors.HexColor("#22c55e"))
    status_challenges = colors.HexColor("#22c55e")
    status_quiz = (
        colors.HexColor("#22c55e")
        if avg_score >= 70
        else (colors.HexColor("#f59e0b") if avg_score >= 50 else colors.HexColor("#ef4444"))
    )
    summary_rows = [
        ["Metric", "Value", "Status"],
        ["Vulnerabilities found", str(total_vuln_count), ""],
        ["Challenges completed", str(remediated_count), ""],
        ["Quiz average score", f"{avg_score:.2f}%", ""],
        ["Hints used (total)", str(total_hints), ""],
    ]
    table = Table(summary_rows, colWidths=[220, 140, 120])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("BACKGROUND", (2, 1), (2, 1), status_vuln),
                ("BACKGROUND", (2, 2), (2, 2), status_challenges),
                ("BACKGROUND", (2, 3), (2, 3), status_quiz),
                ("BACKGROUND", (2, 4), (2, 4), colors.HexColor("#f3f4f6")),
            ]
        )
    )
    table.wrapOn(c, width, height)
    table.drawOn(c, 60, y - 170)
    c.showPage()

    # PAGE 3 - VULNERABILITY INVENTORY.
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 70, "2. Vulnerability Inventory")
    y = height - 105
    shown = 0
    for finding in findings:
        if y < 120:
            break
        vuln_type = str(finding.get("vulnerability_type") or "Unknown")
        severity = str(finding.get("severity") or "Medium")
        file_path = str(finding.get("file")) if finding.get("file") else "N/A"
        line_num = str(finding.get("line")) if finding.get("line") else "N/A"
        description = str(finding.get("description") or "No description available.")
        recommendation = str(finding.get("recommendation", "") or "")
        cwe = str(finding.get("cwe")) if finding.get("cwe") else "Not mapped"

        if severity.lower() in ("critical", "high"):
            sev_color = colors.HexColor("#dc2626")
        elif severity.lower() == "medium":
            sev_color = colors.HexColor("#f97316")
        else:
            sev_color = colors.grey

        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(60, y, vuln_type)
        y -= 16
        c.setFont("Helvetica", 10)
        c.setFillColor(sev_color)
        c.drawString(60, y, f"Severity: {severity}")
        c.setFillColor(colors.black)
        y -= 14
        c.drawString(60, y, f"File: {file_path}")
        y -= 14
        c.drawString(60, y, f"Line: {line_num}   CWE: {cwe}")
        y -= 14
        y = _draw_wrapped(c, f"Description: {description}", 60, y, max_chars=100, leading=13.0)
        if recommendation:
            y = _draw_wrapped(c, f"Recommendation: {recommendation}", 60, y, max_chars=100, leading=13.0)
        y -= 4
        c.setStrokeColor(colors.HexColor("#d1d5db"))
        c.line(60, y, width - 60, y)
        y -= 16
        shown += 1
    if shown < len(findings):
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(60, 90, f"Additional vulnerabilities omitted for space: {len(findings) - shown}")
    c.showPage()

    # PAGE 4 - REMEDIATION EVIDENCE.
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 70, "3. Remediation Evidence")
    y = height - 105
    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"Fix evidence log entries: {len(evidence_logs)}")
    y -= 20
    for item in completed_challenges:
        if y < 120:
            break
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(60, y, item["title"])
        y -= 16
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#16a34a"))
        c.drawString(60, y, "Status: REMEDIATED")
        c.setFillColor(colors.black)
        y -= 14
        c.drawString(60, y, f"Time to fix: {_fmt_duration(item['time_seconds'])}")
        y -= 14
        c.drawString(60, y, f"Hints used: {item['hints_used']}")
        y -= 14
        description = REMEDIATION_DESCRIPTIONS.get(item["slug"], "The student implemented secure coding improvements for this challenge.")
        y = _draw_wrapped(c, description, 60, y, max_chars=100, leading=13)
        y -= 6
        c.setStrokeColor(colors.HexColor("#d1d5db"))
        c.line(60, y, width - 60, y)
        y -= 16
    c.showPage()

    # PAGE 5 - LEARNING METRICS.
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 70, "4. Learning Metrics")
    metrics_rows = [
        ["Metric", "Value"],
        ["Total challenges attempted", str(attempted_challenges)],
        ["Challenges fully remediated", str(remediated_count)],
        ["Quiz sessions completed", str(total_attempts)],
        ["Quiz average score", f"{avg_score:.2f}%"],
        ["Quiz best score", f"{best_score:.2f}%"],
        ["Total time on challenges", _fmt_duration(total_challenge_time)],
    ]
    metrics_table = Table(metrics_rows, colWidths=[280, 200])
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ]
        )
    )
    metrics_table.wrapOn(c, width, height)
    metrics_table.drawOn(c, 60, height - 290)
    c.setFont("Helvetica", 10)
    closing = (
        "This report was generated automatically by the SCALE Security Learning Platform. "
        "All findings reflect analysis performed during the learning session and are intended "
        "for educational purposes."
    )
    _draw_wrapped(c, closing, 60, height - 320, max_chars=100, leading=14)

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # STEP 6: Return raw PDF bytes.
    date_fragment = datetime.utcnow().strftime("%Y%m%d")
    safe_email = re.sub(r"[^a-zA-Z0-9._-]+", "_", current_user.email or "user")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=pentest_report_{safe_email}_{date_fragment}.pdf"
        },
    )
