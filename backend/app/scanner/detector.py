from pathlib import Path
from typing import List, Dict
import re

from .rules import RULES


def _scan_file(file_path: Path) -> Dict:
    findings: List[Dict] = []
    try:
        with open(file_path, "r", errors="ignore") as f:
            lines = f.readlines()
            file_text = "".join(lines)
            for line_no, line in enumerate(lines, start=1):
                for rule in RULES:
                    for pattern in rule["patterns"]:
                        if re.search(pattern, line):
                            code_snippet = line.strip()[:500]
                            findings.append(
                                {
                                    "line": line_no,
                                    "vulnerability_type": rule["type"],
                                    "type": rule["type"],  # alias for frontend/API consumers
                                    "severity": rule["severity"],
                                    # Trim snippet to keep responses compact
                                    "code_snippet": code_snippet,
                                    "code": code_snippet,  # alias for frontend/API consumers
                                }
                            )
                            # Avoid duplicating the same rule for the same line;
                            # but allow other rule types to also match.
                            break

            # File-level CSRF heuristic:
            # if POST handlers/forms exist but no obvious csrf token check, flag it.
            has_post_handler = bool(
                re.search(r"methods\s*=\s*\[[^]]*['\"]POST['\"]", file_text, re.IGNORECASE)
                or re.search(r"<form[^>]*method=['\"]post['\"]", file_text, re.IGNORECASE)
            )
            has_csrf_protection = bool(
                re.search(r"csrf_token|X-CSRF-Token|XSRF|wtforms|FlaskForm|csrf_protect|validate_csrf", file_text, re.IGNORECASE)
            )
            if has_post_handler and not has_csrf_protection:
                # Find a representative line to point at.
                csrf_line = 1
                for idx, line in enumerate(lines, start=1):
                    if re.search(r"POST|method=['\"]post['\"]", line, re.IGNORECASE):
                        csrf_line = idx
                        break
                snippet = lines[csrf_line - 1].strip()[:500] if lines else "POST handler/form without CSRF token validation"
                findings.append(
                    {
                        "line": csrf_line,
                        "vulnerability_type": "CSRF",
                        "type": "CSRF",
                        "severity": "Medium",
                        "code_snippet": snippet,
                        "code": snippet,
                    }
                )
        return {"findings": findings, "lines_scanned": len(lines), "error": None}
    except (OSError, UnicodeError):
        # Preserve error details for scanner diagnostics.
        return {"findings": [], "lines_scanned": 0, "error": "file_read_error"}


def scan_file_for_vulnerabilities_detailed(file_path: Path) -> Dict:
    """
    Detailed scanner result with findings + diagnostics.
    """
    return _scan_file(file_path)


def scan_file_for_vulnerabilities(file_path: Path) -> List[Dict]:
    """
    Backward-compatible scanner API returning only findings.
    """
    return _scan_file(file_path)["findings"]

