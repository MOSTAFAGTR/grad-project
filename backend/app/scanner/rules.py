RULES = [
    {
        "type": "SQL Injection",
        "patterns": [
            r"SELECT.*\+",
            r"execute\(.*\+",
            r"\$_(GET|POST).*SELECT",
        ],
        "severity": "High",
    },
    {
        "type": "XSS",
        "patterns": [
            r"innerHTML\s*=",
            r"document\.write\(",
            r"echo\s+\$_(GET|POST)",
        ],
        "severity": "Medium",
    },
    {
        "type": "Command Injection",
        "patterns": [
            r"os\.system\(",
            r"exec\(",
            r"shell_exec\(",
            r"subprocess\.call\(",
        ],
        "severity": "High",
    },
    {
        "type": "Hardcoded Secret",
        "patterns": [
            r"password\s*=\s*\".*\"",
            r"api_key\s*=\s*\".*\"",
            r"secret\s*=\s*\".*\"",
        ],
        "severity": "High",
    },
]

