"""One-off: list all FastAPI routes from backend/app/api/*.py"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "backend" / "app" / "api"
prefixes = {
    "auth": "/api/auth",
    "quizzes": "/api/quizzes",
    "challenges": "/api/challenges",
    "stats": "/api/stats",
    "messages": "/api/messages",
    "projects": "/api",
    "game_challenge": "/api/challenge",
    "misconfig": "/api",
    "ai_mentor": "/api/ai",
    "attack_simulator": "/api/attack",
    "project_analyzer": "/api",
    "security_logs": "/api/security",
    "quiz_dynamic": "/api/quiz",
    "instructor": "/api/instructor",
    "report": "/api/report",
    "red_blue": "/api/redblue",
}
pat = re.compile(r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']')
routes = []
for f in sorted(root.glob("*.py")):
    mod = f.stem
    pfx = prefixes.get(mod, "?")
    text = f.read_text(encoding="utf-8")
    for m in pat.finditer(text):
        method, path = m.group(1).upper(), m.group(2)
        if path.startswith("/"):
            full = pfx.rstrip("/") + path
        else:
            full = pfx.rstrip("/") + "/" + path
        routes.append((full, method, mod))
seen = set()
out = []
for full, method, mod in sorted(routes, key=lambda x: (x[0].lower(), x[1])):
    k = (full, method)
    if k in seen:
        continue
    seen.add(k)
    out.append((full, method, mod))
print(len(out))
for full, method, mod in out:
    print(f"{method}\t{full}\t{mod}")
