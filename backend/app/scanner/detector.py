from pathlib import Path
from typing import List, Dict
import re

from .rules import RULES


def scan_file_for_vulnerabilities(file_path: Path) -> List[Dict]:
    """
    Scan a single file line-by-line using simple regex rules.

    This is deliberately a Phase 1, rule-based static analysis:
    - It is fast and easy to understand.
    - It will miss many real vulnerabilities and may report false positives,
      because regexes cannot fully understand context, data flow, or sanitization.
    """
    findings: List[Dict] = []

    try:
        with open(file_path, "r", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                for rule in RULES:
                    for pattern in rule["patterns"]:
                        if re.search(pattern, line):
                            findings.append(
                                {
                                    "line": line_no,
                                    "vulnerability_type": rule["type"],
                                    "severity": rule["severity"],
                                    # Trim snippet to keep responses compact
                                    "code_snippet": line.strip()[:500],
                                }
                            )
                            # Avoid duplicating the same rule for the same line;
                            # but allow other rule types to also match.
                            break
    except (OSError, UnicodeError):
        # If the file cannot be read for any reason, we silently skip it.
        # In a later phase, these errors could be logged for debugging.
        return []

    return findings

