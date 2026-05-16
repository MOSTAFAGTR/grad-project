"""Insert appendices E–L before Documentation Statistics; fix duplicate heading."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "PROJECT_DOCUMENTATION.md"


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def appendix_models() -> str:
    lines = [
        "## Appendix E — ORM Models (Complete Column Reference)",
        "",
        "The following tables are transcribed from `backend/app/models.py` as of the documentation revision date.",
        "",
    ]
    src = read_text(ROOT / "backend" / "app" / "models.py")
    lines.append("```python")
    lines.extend(src.splitlines())
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def appendix_learning_tracker() -> str:
    lines = [
        "## Appendix F — Learning Progress Module (Full Source)",
        "",
        "Complete `backend/app/security/learning_tracker.py` for examiner reference.",
        "",
    ]
    src = read_text(ROOT / "backend" / "app" / "security" / "learning_tracker.py")
    lines.append("```python")
    lines.extend(src.splitlines())
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def appendix_hints_replays() -> str:
    ch = read_text(ROOT / "backend" / "app" / "api" / "challenges.py")
    m = re.search(r"(_HINTS: dict.*?\n\})", ch, re.S)
    m2 = re.search(r"(ATTACK_REPLAYS: dict.*?\n\})", ch, re.S)
    lines = [
        "## Appendix G — Challenge Hints and Attack Replay Payloads (Source Extracts)",
        "",
        "### G.1 `_HINTS`",
        "",
        "Progressive hints returned by `GET /api/challenges/hints` for selected slugs (`csrf`, `broken-auth`, `security-misc`, `directory-traversal`, `xxe`, `insecure-storage`).",
        "",
    ]
    if m:
        lines.append("```python")
        lines.extend(m.group(1).splitlines())
        lines.append("```")
    lines.append("")
    lines.append("### G.2 `ATTACK_REPLAYS`")
    lines.append("")
    lines.append(
        "Structured steps for `GET /api/challenges/replay/{challenge_slug}`. Step types include "
        "`user_action`, `user_input`, `http_request`, `server_processing`, `http_response`."
    )
    lines.append("")
    if m2:
        lines.append("```python")
        lines.extend(m2.group(1).splitlines())
        lines.append("```")
    lines.append("")
    return "\n".join(lines)


def appendix_components() -> str:
    lines = [
        "## Appendix H — Frontend Components (`frontend/src/components/`)",
        "",
        "| File | Role |",
        "|------|------|",
    ]
    comp = ROOT / "frontend" / "src" / "components"
    for p in sorted(comp.glob("*.tsx")):
        lines.append(f"| `{p.name}` | React UI component |")
    lines.append("")
    return "\n".join(lines)


def appendix_challenge_dirs() -> str:
    lines = [
        "## Appendix I — Challenge Docker Bind Mounts and Directories",
        "",
        "The backend `docker-compose.yml` mounts each `challenge-*` directory at `/app/challenges/<name>`. "
        "Sandbox validation resolves these paths when running `run_tests.sh`.",
        "",
    ]
    for name in sorted(
        d.name
        for d in ROOT.iterdir()
        if d.is_dir() and d.name.startswith("challenge-") and not d.name.startswith(".")
    ):
        lines.append(f"### `{name}/`")
        d = ROOT / name
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if f.is_file() and "venv" not in f.parts and "__pycache__" not in f.parts:
                rel = f.relative_to(d)
                lines.append(f"- `{rel}` — challenge lab asset")
        lines.append("")
    return "\n".join(lines)


def appendix_env_docker() -> str:
    return "\n".join(
        [
            "## Appendix J — Docker Compose and Environment (Expanded Reference)",
            "",
            "### J.1 Services (from `docker-compose.yml`)",
            "",
            "| Service | Build / image | Host ports | Depends on | Purpose |",
            "|---------|---------------|------------|------------|---------|",
            "| `sandbox_base` | `./backend/sandbox_base` → `scale-sandbox-base` | — | — | Pre-build base for student sandbox images |",
            "| `backend` | `./backend` | 8000:8000 | healthy DBs, sandbox_base | FastAPI API, sandbox runner |",
            "| `frontend` | `./frontend` | 5173:5173 | — | Vite dev server for SPA |",
            "| `ai_service` | `./ai_service` | 8001:8001 | — | Template AI microservice for instructor quiz preview |",
            "| `main_db` | `mysql:8.0` | 3306:3306 | — | Primary application database |",
            "| `challenge_db_sqli` | `mysql:8.0` | 3307:3306 | — | SQL injection lab data |",
            "| `challenge_db_csrf` | `mysql:8.0` | 3308:3306 | — | CSRF lab accounts |",
            "",
            "### J.2 Named volume",
            "",
            "| Volume | Mount point | Persisted |",
            "|--------|-------------|-----------|",
            "| `scale_db_data` | `/var/lib/mysql` in `main_db` | Yes — user accounts, progress, scans |",
            "",
            "### J.3 Environment variables (from `.env.example` and compose interpolation)",
            "",
            "| Variable | Default in compose | Consumed by | Purpose |",
            "|----------|-------------------|-------------|---------|",
            "| `OPENAI_API_KEY` | empty in `.env.example` | Backend, AI paths | Enables OpenAI for mentor, quizzes, scan AI |",
            "| `SERPER_API_KEY` | empty | Backend | Web-search-backed fallbacks when OpenAI absent |",
            "| `AI_SERVICE_URL` | `http://ai_service:8001` | Backend | httpx target for template AI quiz generation |",
            "| `DATABASE_URL` | `mysql+pymysql://user:password@main_db/scale_db` | Backend | SQLAlchemy main DB |",
            "| `SQLI_DATABASE_URL` | `...@challenge_db_sqli/testdb` | Challenges | SQLi lab connection |",
            "| `CSRF_DATABASE_URL` | `...@challenge_db_csrf/csrfdb` | Challenges | CSRF lab connection |",
            "| `SECRET_KEY` | `scale_graduation_project_secret_key` | Backend | JWT signing |",
            "| `ACCESS_TOKEN_EXPIRE_MINUTES` | `600` | Backend | JWT lifetime |",
            "| `ENABLE_BROKEN_AUTH_CHALLENGE` | `true` | Backend | SQLite vulnerable login branch |",
            "| `SANDBOX_MAX_CODE_CHARS` | `200000` | Sandbox | Uploaded fix size cap |",
            "| `SANDBOX_RUN_TIMEOUT` | `25` | Sandbox | Seconds for unittest run |",
            "| `VITE_API_URL` | `http://localhost:8000` | Frontend | Axios base URL |",
            "",
            "",
        ]
    )


def appendix_route_handlers() -> str:
    """One line per route: METHOD path -> function name from api/*.py"""
    lines = [
        "## Appendix K — HTTP Route to Python Handler Names",
        "",
        "Each line maps a registered path (after router prefix) to the implementing function in `backend/app/api/`.",
        "",
    ]
    api = ROOT / "backend" / "app" / "api"
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
    route_re = re.compile(
        r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\'][^\n]*\n(?:async\s+)?def\s+(\w+)\s*\(',
        re.I | re.M,
    )
    entries: list[tuple[str, str, str]] = []
    for f in sorted(api.glob("*.py")):
        text = read_text(f)
        mod = f.stem
        pfx = prefixes.get(mod, "")
        for m in route_re.finditer(text):
            method, path, fn = m.group(1).upper(), m.group(2), m.group(3)
            if path.startswith("/"):
                full = pfx.rstrip("/") + path
            else:
                full = pfx.rstrip("/") + "/" + path
            entries.append((full, method, fn))
    entries.append(("/", "GET", "read_root"))
    for full, method, fn in sorted(entries, key=lambda x: (x[0].lower(), x[1])):
        lines.append(f"- `{method} {full}` → `{fn}()`")
    lines.append("")
    return "\n".join(lines)


def appendix_static_rules() -> str:
    lines = [
        "## Appendix L — Static Scanner `RULES` (`backend/app/scanner/rules.py`)",
        "",
        "Each rule contributes regex matches to `detector.py`. Severity weights feed `scorer.py` (High=5, Medium=3, Low=1).",
        "",
    ]
    rules_src = read_text(ROOT / "backend" / "app" / "scanner" / "rules.py")
    lines.append("```python")
    lines.extend(rules_src.splitlines())
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    text = read_text(DOC)
    text = re.sub(
        r"^## 14\. Complete API Reference\n\n## 14\. Complete API Reference\n",
        "## 14. Complete API Reference\n",
        text,
        flags=re.M,
    )
    insert = "\n".join(
        [
            appendix_models(),
            appendix_learning_tracker(),
            appendix_hints_replays(),
            appendix_components(),
            appendix_challenge_dirs(),
            appendix_env_docker(),
            appendix_route_handlers(),
            appendix_static_rules(),
        ]
    )
    marker = "## Documentation Statistics (Final)"
    if marker not in text:
        raise SystemExit("marker not found")
    text = text.replace(f"\n{marker}", "\n" + insert + "\n---\n\n" + marker, 1)
    # Update TOC - add appendix E-L links after Appendix D
    toc_add = (
        "- [Appendix E — ORM Models](#appendix-e--orm-models-complete-column-reference)\n"
        "- [Appendix F — Learning Progress Module](#appendix-f--learning-progress-module-full-source)\n"
        "- [Appendix G — Hints and Replays](#appendix-g--challenge-hints-and-attack-replay-payloads-source-extracts)\n"
        "- [Appendix H — Frontend Components](#appendix-h--frontend-components-frontendsrccomponents)\n"
        "- [Appendix I — Challenge Directories](#appendix-i--challenge-docker-bind-mounts-and-directories)\n"
        "- [Appendix J — Docker and Environment](#appendix-j--docker-compose-and-environment-expanded-reference)\n"
        "- [Appendix K — Route Handlers](#appendix-k--http-route-to-python-handler-names)\n"
        "- [Appendix L — Scanner Rules](#appendix-l--static-scanner-rules-backendappscannerrulespy)\n"
    )
    text = text.replace("- [Appendix D — Development Changelog](#appendix-d--development-changelog)\n", "- [Appendix D — Development Changelog](#appendix-d--development-changelog)\n" + toc_add, 1)
    DOC.write_text(text, encoding="utf-8")
    print("lines", len(text.splitlines()))


if __name__ == "__main__":
    main()
