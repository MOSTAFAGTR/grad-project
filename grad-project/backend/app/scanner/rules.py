RULES = [
    {
        "type": "SQL Injection",
        "patterns": [
            r"SELECT\s+.*(\+|format\(|f\")",
            r"INSERT\s+.*(\+|format\(|f\")",
            r"UPDATE\s+.*(\+|format\(|f\")",
            r"DELETE\s+.*(\+|format\(|f\")",
            r"execute\(\s*f?[\"'].*\{.*\}.*[\"']",
            r"cursor\.execute\(\s*query\s*\)",
            r"\$_(GET|POST).*(SELECT|INSERT|UPDATE|DELETE)",
        ],
        "severity": "High",
    },
    {
        "type": "XSS",
        "patterns": [
            r"innerHTML\s*=",
            r"dangerouslySetInnerHTML",
            r"v-html\s*=",
            r"document\.write\(",
            r"echo\s+\$_(GET|POST)",
            r"render_template_string\(",
        ],
        "severity": "High",
    },
    {
        "type": "Command Injection",
        "patterns": [
            r"os\.system\(",
            r"exec\(",
            r"shell_exec\(",
            r"subprocess\.call\(",
            r"subprocess\.run\(.*shell\s*=\s*True",
        ],
        "severity": "High",
    },
    {
        "type": "Hardcoded Secret",
        "patterns": [
            r"(password|passwd|pwd)\s*=\s*[\"'][^\"']+[\"']",
            r"(api_key|apikey)\s*=\s*[\"'][^\"']+[\"']",
            r"(secret|secret_key|jwt_secret|token)\s*=\s*[\"'][^\"']+[\"']",
            r"MYSQL_PASSWORD\s*=\s*[\"'][^\"']+[\"']",
            r"String\s+(password|apiKey|token)\s*=\s*['\"].+['\"]",
        ],
        "severity": "High",
    },
    {
        "type": "CSRF",
        "patterns": [
            r"@app\.route\([^)]*methods\s*=\s*\[[^]]*['\"]POST['\"]",
            r"<form[^>]*method=['\"]post['\"]",
            r"csrf_exempt",
        ],
        "severity": "Medium",
    },
]

