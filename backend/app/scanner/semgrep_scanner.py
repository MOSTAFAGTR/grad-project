"""
Semgrep-based SAST scanner for SCALE platform.
Runs Semgrep with security-focused rulesets and normalizes
results to the same format as the legacy regex scanner.
Falls back gracefully to legacy scanner if Semgrep is
unavailable.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

# Severity mapping from Semgrep to SCALE format
SEVERITY_MAP = {
    "ERROR": "High",
    "WARNING": "Medium",
    "INFO": "Low",
    "CRITICAL": "Critical",
}

# Semgrep rule ID to SCALE vulnerability type mapping
RULE_TYPE_MAP = {
    "sql": "SQL Injection",
    "sqli": "SQL Injection",
    "injection": "SQL Injection",
    "xss": "XSS",
    "cross-site": "XSS",
    "command": "Command Injection",
    "exec": "Command Injection",
    "shell": "Command Injection",
    "csrf": "CSRF",
    "secret": "Hardcoded Secret",
    "password": "Hardcoded Secret",
    "hardcoded": "Hardcoded Secret",
    "traversal": "Directory Traversal",
    "path": "Directory Traversal",
    "xxe": "XXE",
    "redirect": "Unvalidated Redirect",
    "open-redirect": "Unvalidated Redirect",
    "storage": "Insecure Storage",
    "auth": "Broken Authentication",
    "authentication": "Broken Authentication",
}

SCANNABLE_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".php",
    ".java",
    ".rb",
    ".go",
    ".cs",
    ".cpp",
    ".c",
}


def _count_scannable_files(path: str) -> int:
    count = 0
    for root, _, files in os.walk(path):
        for f in files:
            if Path(f).suffix.lower() in SCANNABLE_EXTS:
                count += 1
    return count


def _classify_rule(rule_id: str, message: str) -> str:
    """Map a Semgrep rule ID to a SCALE vulnerability type."""
    combined = (rule_id + " " + message).lower()
    for keyword, vtype in RULE_TYPE_MAP.items():
        if keyword in combined:
            return vtype
    return "Security Issue"


def _normalize_finding(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a Semgrep finding to SCALE finding format."""
    check_id = raw.get("check_id", "")
    message = raw.get("extra", {}).get("message", "")
    severity_raw = raw.get("extra", {}).get("severity", "WARNING")
    severity = SEVERITY_MAP.get(str(severity_raw).upper(), "Medium")
    file_path = raw.get("path", "")
    start_line = raw.get("start", {}).get("line", 0)
    end_line = raw.get("end", {}).get("line", start_line)
    code_lines = raw.get("extra", {}).get("lines", "")
    metadata = raw.get("extra", {}).get("metadata", {})

    cwe = ""
    if isinstance(metadata.get("cwe"), list) and metadata["cwe"]:
        cwe = metadata["cwe"][0]
    elif isinstance(metadata.get("cwe"), str):
        cwe = metadata["cwe"]

    owasp = ""
    if isinstance(metadata.get("owasp"), list) and metadata["owasp"]:
        owasp = metadata["owasp"][0]

    vuln_type = _classify_rule(check_id, message)

    fix_rec = metadata.get("fix", "") or metadata.get("fix-regex", "")
    references = metadata.get("references", [])
    ref_str = references[0] if references else ""

    snippet = code_lines.strip()[:500] if code_lines else ""

    return {
        "file": file_path,
        "line": start_line,
        "end_line": end_line,
        "vulnerability_type": vuln_type,
        "type": vuln_type,
        "severity": severity,
        "code_snippet": snippet,
        "code": snippet,
        "rule_id": check_id,
        "cwe": cwe,
        "owasp": owasp,
        "fix": {
            "explanation": message,
            "recommendation": fix_rec or f"Review and fix the {vuln_type} vulnerability.",
            "example": ref_str,
        },
        "engine": "semgrep",
    }


def run_semgrep_scan(
    target_path: str,
    timeout_seconds: int = 45,
) -> dict[str, Any]:
    """
    Run Semgrep on the target directory using OWASP-focused rules.
    Falls back to empty findings if Semgrep is unavailable or skipped.
    """
    findings: list[dict] = []
    errors: list[str] = []
    semgrep_available = False

    try:
        check = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        semgrep_available = check.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        semgrep_available = False

    if not semgrep_available:
        return {
            "findings": [],
            "engine": "semgrep",
            "available": False,
            "error": "Semgrep not installed",
            "errors": [],
        }

    target = str(Path(target_path).resolve())

    file_count = _count_scannable_files(target)
    if file_count > 200:
        return {
            "findings": [],
            "engine": "semgrep",
            "available": True,
            "skipped": True,
            "reason": f"Project too large ({file_count} files). Using regex scanner only.",
            "errors": [],
        }

    cmd = [
        "semgrep",
        "--config",
        "p/owasp-top-ten",
        "--config",
        "p/secrets",
        "--json",
        "--no-git-ignore",
        "--timeout",
        "8",
        "--max-memory",
        "256",
        "--jobs",
        "1",
        "--metrics",
        "off",
        "--quiet",
        target,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        if result.returncode > 1:
            errors.append(
                f"Semgrep error (exit {result.returncode}): "
                f"{result.stderr[:300]}"
            )
            cmd_fallback = [
                "semgrep",
                "--config",
                "p/python",
                "--json",
                "--no-git-ignore",
                "--timeout",
                "8",
                "--max-memory",
                "256",
                "--jobs",
                "1",
                "--metrics",
                "off",
                "--quiet",
                target,
            ]
            fallback = subprocess.run(
                cmd_fallback,
                capture_output=True,
                text=True,
                timeout=min(60, timeout_seconds + 15),
            )
            if fallback.returncode <= 1 and fallback.stdout:
                result = fallback

        if result.stdout:
            data = json.loads(result.stdout)
            raw_findings = data.get("results", [])
            for raw in raw_findings:
                try:
                    if isinstance(raw.get("path"), str):
                        try:
                            raw = {**raw, "path": str(Path(raw["path"]).relative_to(target))}
                        except ValueError:
                            pass
                    findings.append(_normalize_finding(raw))
                except Exception as e:
                    errors.append(f"Parse error: {e}")

            for err in data.get("errors", []):
                errors.append(str(err.get("message", err))[:200])

    except subprocess.TimeoutExpired:
        errors.append(
            f"Semgrep timed out after {timeout_seconds}s. "
            "Results may be partial."
        )
    except json.JSONDecodeError as e:
        errors.append(f"Semgrep output parse error: {e}")
    except Exception as e:
        errors.append(f"Semgrep execution error: {e}")

    return {
        "findings": findings,
        "engine": "semgrep",
        "available": True,
        "total_findings": len(findings),
        "errors": errors,
    }
