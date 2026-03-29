from typing import Dict, Callable


def _extract_representative_query(code: str) -> str:
    for line in (code or "").splitlines():
        l = line.strip()
        if "SELECT" in l.upper() and ("FROM" in l.upper() or "WHERE" in l.upper()):
            return l
    return "SELECT * FROM users WHERE id = '1'"


def simulate_sql_injection(code: str, payload: str) -> Dict:
    original_query = _extract_representative_query(code)
    injected_query = (
        "SELECT * FROM users WHERE id = '' OR 1=1 --"
        if not payload
        else f"SELECT * FROM users WHERE id = '{payload}'"
    )
    return {
        "original_state": original_query,
        "payload": payload or "' OR 1=1 --",
        "injected_state": injected_query,
        "execution_flow": (
            "Application concatenates user input into SQL. Payload modifies predicate logic, "
            "turning a scoped lookup into a broad data-return query."
        ),
        "result": "Database returns records beyond intended scope (often all rows).",
        "data_exposed": "Usernames, emails, password hashes, profile/financial data depending on table access.",
        "impact": "Authentication bypass and bulk data exfiltration; potential privilege escalation.",
        "timeline": [
            "User input received by vulnerable SQL builder",
            "Payload injected into dynamic query string",
            "Query structure modified by attacker-controlled tokens",
            "Database executes altered query logic",
            "Sensitive records returned to attacker",
        ],
    }


def simulate_xss(code: str, payload: str) -> Dict:
    unsafe_sink = "dangerouslySetInnerHTML / innerHTML sink receives untrusted input"
    return {
        "original_state": unsafe_sink,
        "payload": payload or "<script>alert('Hacked')</script>",
        "injected_state": "Browser interprets payload as executable script inside trusted origin.",
        "execution_flow": (
            "Untrusted input is written into an HTML-executing sink. Browser parses payload as code "
            "and executes in victim session context."
        ),
        "result": "Injected JavaScript runs with user privileges in the application origin.",
        "data_exposed": "Session tokens, CSRF tokens, DOM secrets, sensitive user interactions.",
        "impact": "Account takeover, phishing overlays, lateral actions through authenticated session.",
        "timeline": [
            "Attacker submits crafted HTML/JS payload",
            "Application stores/renders payload without encoding",
            "Victim loads vulnerable page",
            "Browser executes injected script",
            "Attacker exfiltrates secrets or performs unauthorized actions",
        ],
    }


def simulate_command_injection(code: str, payload: str) -> Dict:
    original = "ping -c 1 <user_input>"
    injected = f"ping -c 1 {payload or '8.8.8.8; cat /etc/passwd'}"
    return {
        "original_state": original,
        "payload": payload or "8.8.8.8; cat /etc/passwd",
        "injected_state": injected,
        "execution_flow": (
            "Input is passed to shell-enabled command execution. Shell metacharacters split/append commands, "
            "allowing arbitrary system instruction execution."
        ),
        "result": "OS executes attacker-supplied command chain beyond intended operation.",
        "data_exposed": "System files, environment secrets, service credentials, host metadata.",
        "impact": "Remote code execution and full host compromise depending on service permissions.",
        "timeline": [
            "Application receives host parameter",
            "Input embedded in shell command string",
            "Shell parses command separators/metacharacters",
            "Injected command executes on server",
            "Command output returned or persisted for attacker retrieval",
        ],
    }


def simulate_csrf(code: str, payload: str) -> Dict:
    forged = payload or "POST /transfer amount=1000&to_user=attacker (auto-submitted form)"
    return {
        "original_state": "State-changing endpoint accepts authenticated browser request without CSRF validation.",
        "payload": forged,
        "injected_state": "Victim browser sends attacker-forged request with valid session cookies.",
        "execution_flow": (
            "Attacker lures authenticated victim to malicious page. Browser auto-submits forged request "
            "to trusted origin; server cannot distinguish intent without CSRF token checks."
        ),
        "result": "Unauthorized state change occurs as victim (e.g., transfer, profile/email/password update).",
        "data_exposed": "Action outcomes and potentially account state if response is observable.",
        "impact": "Unauthorized transactions or configuration changes without victim consent.",
        "timeline": [
            "Victim authenticated in target application",
            "Attacker hosts page with forged state-changing request",
            "Victim visits attacker-controlled page",
            "Browser automatically submits request with victim cookies",
            "Server processes action as legitimate user operation",
        ],
    }


def simulate_unsupported(vulnerability_type: str, code: str, payload: str) -> Dict:
    return {
        "original_state": "Template not available for this vulnerability type.",
        "payload": payload,
        "injected_state": "No simulation template matched.",
        "execution_flow": "Fallback simulation response returned safely.",
        "result": "Unsupported vulnerability type for attack lab simulation.",
        "data_exposed": "Unknown",
        "impact": "Educational simulation unavailable for this type.",
        "timeline": [
            "Request received by simulator",
            f"Type '{vulnerability_type}' not mapped to attack template",
            "Safe fallback response generated",
        ],
    }


ATTACK_TEMPLATES: Dict[str, Callable[[str, str], Dict]] = {
    "sql injection": simulate_sql_injection,
    "xss": simulate_xss,
    "command injection": simulate_command_injection,
    "csrf": simulate_csrf,
}

