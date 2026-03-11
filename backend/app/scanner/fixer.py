from typing import List, Dict, Any, Optional
from pathlib import Path

from .rules import RULES  # not strictly needed, but keeps mapping types consistent


FIX_RECOMMENDATIONS = {
    "SQL Injection": {
        "explanation": "User input is directly concatenated into SQL query which allows attackers to inject malicious SQL.",
        "recommendation": "Use parameterized queries or prepared statements.",
        "example": {
            "php": "$stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');\n$stmt->execute([$id]);",
            "python": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
        },
    },
    "XSS": {
        "explanation": "User input is inserted into HTML without escaping which may execute malicious scripts.",
        "recommendation": "Escape output or use safe DOM methods.",
        "example": {
            "javascript": "element.textContent = userInput;",
            "php": "echo htmlspecialchars($userInput, ENT_QUOTES, 'UTF-8');",
        },
    },
    "Command Injection": {
        "explanation": "User input is passed to system commands allowing arbitrary command execution.",
        "recommendation": "Avoid passing raw user input to system calls.",
        "example": {
            "python": "subprocess.run(['ls', user_input])",
        },
    },
    "Hardcoded Secret": {
        "explanation": "Sensitive credentials are hardcoded in source code.",
        "recommendation": "Move secrets to environment variables.",
        "example": {
            "python": "password = os.getenv('DB_PASSWORD')",
        },
    },
}


def _guess_language_from_path(rel_path: str) -> Optional[str]:
    """
    Infer a simple language label from the file extension so we can pick
    the most relevant example snippet.
    """
    ext = Path(rel_path).suffix.lower()
    return {
        ".php": "php",
        ".js": "javascript",
        ".py": "python",
        ".java": "java",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
    }.get(ext)


def attach_fixes(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Attach template-based secure coding advice to each finding.

    Automated fix suggestions are helpful for learning because they show:
    - *why* the pattern is dangerous,
    - and *how* to rewrite it using safer APIs.

    This is intentionally template-driven (no AI) so students can see
    concrete, opinionated examples of better code.
    """
    enhanced: List[Dict[str, Any]] = []

    for f in findings:
        vtype = f.get("vulnerability_type")
        rec = FIX_RECOMMENDATIONS.get(vtype)
        fix_block: Dict[str, Any] = {}

        if rec:
            lang = _guess_language_from_path(f.get("file", ""))
            examples = rec.get("example") or {}

            # Choose best example for the detected language, fall back to any example.
            example_snippet = None
            if lang and lang in examples:
                example_snippet = examples[lang]
            elif examples:
                # Take the first example if language-specific one is not available.
                example_snippet = next(iter(examples.values()))

            fix_block = {
                "explanation": rec.get("explanation"),
                "recommendation": rec.get("recommendation"),
                "example": example_snippet,
            }

        f_with_fix = {
            **f,
            "fix": fix_block or None,
        }
        enhanced.append(f_with_fix)

    return enhanced

