import os
import json
from typing import Dict, Any

from dotenv import load_dotenv
import openai

from .serper_helpers import scan_feedback_from_serper, serper_configured


# env_bootstrap runs first; override=True so empty Docker-injected keys are replaced from .env
load_dotenv(override=True)


def generate_ai_security_feedback(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the OpenAI API to provide deep, contextual security mentoring for a finding.

    This AI layer is deliberately separate from the rule engine so that:
    - detection remains deterministic and auditable,
    - AI is an optional enhancement that enriches explanations and examples.
    """
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    openai.api_key = key or None
    if not openai.api_key and serper_configured():
        return scan_feedback_from_serper(finding)

    if not openai.api_key:
        # If API key is not configured, gracefully skip AI enrichment.
        return {}

    vtype = finding.get("vulnerability_type", "Unknown")
    severity = finding.get("severity", "Unknown")
    file_path = finding.get("file", "unknown")
    code = finding.get("code_snippet", "")

    system_prompt = (
        "You are a senior application security engineer and educator. "
        "You provide concise, technically accurate explanations and secure coding guidance."
    )

    user_prompt = f"""
Analyze this vulnerability in the context of secure coding training.

Type: {vtype}
Severity: {severity}
File: {file_path}
Code:
{code}

Explain in detail:
1. Why this pattern is dangerous.
2. How an attacker could realistically exploit it.
3. Show a secure refactored code example (keep it short and focused).
4. List 3-5 concrete best practices relevant to this issue.

Respond ONLY as a JSON object with the following shape:
{{
  "deep_explanation": "...",
  "how_attack_works": "...",
  "secure_refactoring": "...",
  "best_practices": ["...", "..."]
}}
"""

    try:
        # Use a small timeout so scans don't hang indefinitely.
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            timeout=20,
        )

        content = response.choices[0].message["content"]
        # Try to parse the response as JSON as requested.
        data = json.loads(content)

        return {
            "deep_explanation": data.get("deep_explanation"),
            "how_attack_works": data.get("how_attack_works"),
            "secure_refactoring": data.get("secure_refactoring"),
            "best_practices": data.get("best_practices"),
        }
    except Exception:
        if serper_configured():
            fb = scan_feedback_from_serper(finding)
            if fb:
                return fb
        # On any error (timeout, parsing, API failure), return empty analysis
        # so the platform still works with rule-based results only.
        return {}

