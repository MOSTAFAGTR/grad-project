"""
Serper.dev — Google Search API (https://serper.dev).
Used when OPENAI_API_KEY is not set: web search backs quiz hints, mentor text, and scan enrichment.
"""

from __future__ import annotations

import os
import random
from typing import Any

import requests

SERPER_SEARCH_URL = "https://google.serper.dev/search"


def _serper_key() -> str:
    """Read at call time so load_dotenv() / Docker env_file apply before first use."""
    return (os.getenv("SERPER_API_KEY", "") or "").strip()


def serper_configured() -> bool:
    return bool(_serper_key())


def serper_organic(query: str, num: int = 10) -> list[dict[str, Any]]:
    key = _serper_key()
    if not key:
        return []
    try:
        r = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": min(10, max(1, num))},
            timeout=30,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return list(data.get("organic") or [])
    except Exception as e:
        print(f"Serper search failed: {e}")
        return []


def build_quiz_questions_from_serper(topic: str, difficulty: str, num_questions: int) -> list[dict]:
    """Build MCQ dicts from real web snippets (training-style questions)."""
    organic = serper_organic(
        f"{topic} cybersecurity secure coding OWASP quiz {difficulty}",
        num=max(10, num_questions + 2),
    )
    if not organic:
        organic = serper_organic(f"{topic} vulnerability prevention best practices", num=10)
    if not organic:
        return []

    wrong_pool = [
        "Rely only on client-side validation for security",
        "Use Base64 encoding as a substitute for sanitization",
        "Disable security logging to reduce noise",
        "Trust data from the browser for authorization decisions",
    ]
    out: list[dict] = []
    topic_l = (topic or "").lower()
    for i in range(num_questions):
        o = organic[i % len(organic)]
        snippet = (o.get("snippet") or "Review secure practices for this topic.")[:450]
        title = (o.get("title") or topic)[:200]
        if "sql" in topic_l or "injection" in topic_l:
            correct = "Use parameterized queries (prepared statements) and avoid concatenating user input into SQL."
        elif "xss" in topic_l:
            correct = "Apply context-aware output encoding and a strict Content Security Policy (CSP)."
        elif "csrf" in topic_l:
            correct = "Use anti-CSRF tokens and SameSite cookies for state-changing requests."
        elif "command" in topic_l:
            correct = "Avoid shell invocation; use APIs that do not invoke a shell and validate/allowlist input."
        else:
            correct = "Apply defense-in-depth: validate input, enforce least privilege, and use secure defaults."

        wrongs = random.sample(wrong_pool, 3)
        opts = [correct] + wrongs
        random.shuffle(opts)
        ci = opts.index(correct)
        out.append(
            {
                "question": (
                    f"[From web search] {snippet}\n\nWhich option best reflects secure practice for “{topic}” "
                    f"({difficulty})?"
                ),
                "options": opts,
                "correct_index": ci,
                "explanation": f"Context summarized from public web results (source title: {title}).",
            }
        )
    return out


def _lab_pedagogy_hint(challenge_id: str, question: str) -> str | None:
    """
    Short, challenge-aware explanation for common student questions (no off-lab exploit recipes).
    """
    cid = (challenge_id or "").lower()
    q = (question or "").strip().lower()

    def asks_why() -> bool:
        return ("why" in q or "how" in q) and any(
            w in q for w in ("work", "attack", "inject", "bypass", "this", "explain")
        )

    sql_lab = "sql" in cid or "sqli" in cid
    if sql_lab and asks_why():
        return (
            "**For this lab (SQL injection login):**\n\n"
            "Many training login forms build a query by concatenating your username and password into a string "
            "like `WHERE username='...' AND password='...'`. If you enter a username that contains a single quote "
            "(`'`), you can break out of the string the SQL parser expected. Adding `OR 1=1` makes the condition "
            "always true for a matching row, and `--` (or `#` in MySQL) comments out the rest of the query—often "
            "the password check—so the row is treated as a valid login. "
            "The vulnerable pattern is **string-building SQL from user input**; the fix is **parameterized queries** "
            "(prepared statements), not more clever string filtering alone."
        )

    if sql_lab and ("payload" in q or "quote" in q or "comment" in q or "or 1" in q):
        return (
            "**Concept (this lab):** Quotes and operators change how the database parses the query. "
            "Prepared statements bind values as data, so the database never concatenates user input into SQL text."
        )

    if ("xss" in cid or "cross-site" in cid) and asks_why():
        return (
            "**For this XSS lab:** Untrusted input is rendered in HTML context without proper encoding. "
            "When you inject markup or script, the browser parses it as part of the page. "
            "Defense is context-aware encoding, CSP, and avoiding unsafe sinks like `innerHTML` with raw input."
        )

    if ("csrf" in cid) and asks_why():
        return (
            "**For this CSRF lab:** The browser sends cookies automatically; if the server only checks cookies "
            "for state-changing requests, a forged request from another site can act as your user. "
            "Anti-CSRF tokens and SameSite cookies break that."
        )

    return None


def _synthesize_from_snippets(question: str, hits: list[dict[str, Any]], max_sentences: int = 3) -> str:
    """Pull a few short sentences from the top snippets for a general question."""
    parts: list[str] = []
    for h in hits[:3]:
        s = (h.get("snippet") or "").strip()
        if not s:
            continue
        # First sentence-ish chunk
        for chunk in s.replace("…", ".").split(".")[:2]:
            c = chunk.strip()
            if len(c) > 40:
                parts.append(c + "." if not c.endswith(".") else c)
            if len(parts) >= max_sentences:
                break
        if len(parts) >= max_sentences:
            break
    return " ".join(parts).strip()


def mentor_text_from_serper(challenge_id: str, question: str) -> str:
    """
    Prefer a lab-specific answer; then add a short synthesis from search; then optional links.
    """
    q_raw = (question or "").strip()
    cid = (challenge_id or "").strip()

    direct = _lab_pedagogy_hint(cid, q_raw)
    # Tighter search for this lab + question (avoid generic "cybersecurity" only)
    sql = "sql" in cid.lower() or "sqli" in cid.lower()
    if sql:
        q_search = (
            f"{q_raw} SQL injection login authentication bypass WHERE clause prepared statement explanation "
            "educational"
        )
    else:
        q_search = f"{cid} {q_raw} cybersecurity lab educational explanation"

    hits = serper_organic(q_search, num=6)
    if not hits:
        hits = serper_organic(f"{q_raw} {cid} cybersecurity", num=6)
    if not hits:
        hits = serper_organic(q_raw or "OWASP secure coding", num=6)

    lines: list[str] = []

    if direct:
        lines.append(direct)
        lines.append("")
        lines.append("**More context (from web search — study pointers, not step-by-step exploits):**")
    else:
        syn = _synthesize_from_snippets(q_raw, hits)
        if syn:
            lines.append("**Summary:**")
            lines.append(syn)
            lines.append("")
        lines.append("**Further reading (external):**")

    for h in hits[:5]:
        t = (h.get("title") or "").strip()
        s = (h.get("snippet") or "").strip()[:320]
        link = (h.get("link") or "").strip()
        line = f"• **{t}**\n  {s}"
        if link:
            line += f"\n  {link}"
        lines.append(line)

    return "\n\n".join(lines) if lines else ""


def serper_context_block(vulnerability_type: str, file_hint: str, code_sample: str) -> str:
    q = f"{vulnerability_type} secure coding remediation CWE"
    hits = serper_organic(q, num=5)
    if not hits and code_sample:
        hits = serper_organic(f"{vulnerability_type} vulnerability example fix", num=5)
    if not hits:
        return ""
    parts = ["--- Web search context (Serper) ---"]
    for h in hits[:5]:
        parts.append(f"{h.get('title', '')}: {h.get('snippet', '')[:400]}")
    parts.append(f"(Finding file: {file_hint})")
    return "\n".join(parts)


def scan_feedback_from_serper(finding: dict[str, Any]) -> dict[str, Any]:
    """Structured enrichment for project scan (same keys as OpenAI path when possible)."""
    vtype = finding.get("vulnerability_type") or finding.get("type") or "Unknown"
    file_path = finding.get("file") or ""
    code = (finding.get("code_snippet") or "")[:200]
    hits = serper_organic(f"{vtype} secure coding fix OWASP", num=6)
    if not hits:
        return {}
    top = hits[0]
    blob = "\n\n".join(
        f"{h.get('title', '')}: {h.get('snippet', '')[:500]}" for h in hits[:4]
    )
    return {
        "deep_explanation": (
            f"Web-sourced context for {vtype} (Serper). {top.get('snippet', '')[:800]}"
        ),
        "how_attack_works": (
            f"Search-backed summary: attackers often abuse weak input handling near sensitive sinks; "
            f"see references in results for {file_path}."
        ),
        "secure_refactoring": (
            "Prefer framework-safe APIs, strict validation, and least privilege. See OWASP guides linked in search titles."
        ),
        "best_practices": [
            "Validate and encode per context (SQL/HTML/shell).",
            "Deny by default; allowlist where possible.",
            "Add tests for security regressions.",
            "Review search results for framework-specific patterns.",
        ],
        "serper_sources": blob[:4000],
    }
