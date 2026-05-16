"""
Rebuild PROJECT_DOCUMENTATION.md: Section 15, Appendix A/B, remove E-G filler.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "PROJECT_DOCUMENTATION.md"
PAGES = ROOT / "frontend" / "src" / "pages"

# Routes from App.tsx (manual authoritative map: component -> routes)
APP_ROUTES: list[tuple[str, str, str]] = [
    ("LandingPage", "LandingPage.tsx", "/", "Public"),
    ("LoginPage", "LoginPage.tsx", "/login", "Public"),
    ("RegisterPage", "RegisterPage.tsx", "/register", "Public"),
    ("DashboardHomePage", "DashboardHomePage.tsx", "/home", "user, instructor, admin"),
    ("ChallengesListPage", "ChallengesListPage.tsx", "/challenges", "user, instructor, admin"),
    ("MessagesPage", "MessagesPage.tsx", "/messages", "user, instructor, admin"),
    ("Scanner", "Scanner.tsx", "/scanner", "user, instructor, admin"),
    ("AttackLab", "AttackLab.tsx", "/attack-lab", "user, instructor, admin"),
    ("SqlInjectionTutorialPage", "SqlInjectionTutorialPage.tsx", "/challenges/1/tutorial", "user, instructor, admin"),
    ("SqlInjectionAttackPage", "SqlInjectionAttackPage.tsx", "/challenges/1/attack", "user, instructor, admin"),
    ("SqlInjectionFixPage", "SqlInjectionFixPage.tsx", "/challenges/1/fix", "user, instructor, admin"),
    ("XssTutorialPage", "XssTutorialPage.tsx", "/challenges/2/tutorial", "user, instructor, admin"),
    ("XssAttackPage", "XssAttackPage.tsx", "/challenges/2/attack", "user, instructor, admin"),
    ("XssFixPage", "XssFixPage.tsx", "/challenges/2/fix", "user, instructor, admin"),
    ("CsrfAttackPage", "CsrfAttackPage.tsx", "/challenges/3/attack", "user, instructor, admin"),
    ("CsrfFixPage", "CsrfFixPage.tsx", "/challenges/3/fix", "user, instructor, admin"),
    ("CsrfTutorialPage", "CsrfTutorialPage.tsx", "/challenges/3/tutorial", "user, instructor, admin"),
    ("CommandChallengePage", "CommandChallengePage.tsx", "/challenges/4/:tab", "user, instructor, admin"),
    ("BrokenAuthAttackPage", "BrokenAuthAttackPage.tsx", "/challenges/5/attack", "user, instructor, admin"),
    ("BrokenAuthFixPage", "BrokenAuthFixPage.tsx", "/challenges/5/fix", "user, instructor, admin"),
    ("BrokenAuthTutorialPage", "BrokenAuthTutorialPage.tsx", "/challenges/5/tutorial", "user, instructor, admin"),
    ("SecurityMiscAttackPage", "SecurityMiscAttackPage.tsx", "/challenges/6/attack", "user, instructor, admin"),
    ("SecurityMiscFixPage", "SecurityMiscFixPage.tsx", "/challenges/6/fix", "user, instructor, admin"),
    ("SecurityMiscTutorialPage", "SecurityMiscTutorialPage.tsx", "/challenges/6/tutorial", "user, instructor, admin"),
    ("InsecureStorageChallengePage", "InsecureStorageChallengePage.tsx", "/challenges/7/:tab", "user, instructor, admin"),
    ("DirectoryTraversalChallengePage", "DirectoryTraversalChallengePage.tsx", "/challenges/8/:tab", "user, instructor, admin"),
    ("XxeChallengePage", "XxeChallengePage.tsx", "/challenges/9/:tab", "user, instructor, admin"),
    ("RedirectChallengePage", "RedirectChallengePage.tsx", "/challenges/10/:tab", "user, instructor, admin"),
    ("AttackSuccessPage", "AttackSuccessPage.tsx", "/challenges/attack-success", "user, instructor, admin"),
    ("RedBlueGamePage", "RedBlueGamePage.tsx", "/redblue/game/:gameId", "user, instructor, admin"),
    ("StudentQuizPage", "StudentQuizPage.tsx", "/quiz", "user only"),
    ("RedBlueMyGamesPage", "RedBlueMyGamesPage.tsx", "/redblue/my-games", "user only"),
    ("UnderConstructionPage", "UnderConstructionPage.tsx", "/under-construction", "user, instructor, admin"),
    ("InstructorDashboardPage", "InstructorDashboardPage.tsx", "/instructor/dashboard", "instructor, admin"),
    ("InstructorQuizPage", "InstructorQuizPage.tsx", "/instructor/quiz", "instructor, admin"),
    ("RedBlueCreatePage", "RedBlueCreatePage.tsx", "/redblue/create", "instructor, admin"),
    ("AdminStatsPage", "AdminStatsPage.tsx", "/admin/stats", "admin"),
    ("AdminDashboardPage", "AdminDashboardPage.tsx", "/admin/dashboard", "admin"),
    ("SecurityLogsPage", "SecurityLogsPage.tsx", "/admin/logs", "admin"),
    ("HomePage", "HomePage.tsx", "(not in App.tsx)", "unreachable"),
    ("ScenarioPage", "ScenarioPage.tsx", "(not in App.tsx)", "unreachable"),
]

API_PATTERNS = [
    re.compile(r"api\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"axios\.(get|post|put|delete|patch)\(\s*[`'\"]([^`'\"]+)[`'\"]", re.I),
    re.compile(r"\$\{API_URL\}(/api/[^`'\")\s]+)", re.I),
]


def extract_apis(text: str) -> list[str]:
    found: list[str] = []
    for idx, pat in enumerate(API_PATTERNS):
        for m in pat.finditer(text):
            if idx == 2:
                method = "GET"
                full = m.group(1).split("?")[0].rstrip("`")
            else:
                method = m.group(1).upper()
                path = m.group(2)
                if path.startswith("http"):
                    continue
                full = path if path.startswith("/api") else ""
            if full.startswith("/api"):
                found.append(f"{method} {full}")
    # dedupe preserve order
    seen = set()
    out = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def extract_state(text: str) -> list[str]:
    """useState lines - first 12 hooks"""
    lines = []
    for m in re.finditer(r"useState\s*<[^>]+>\s*\([^)]*\)|useState\s*\([^)]*\)", text):
        snippet = text[max(0, m.start() - 40) : m.end() + 80]
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        lines.append(snippet.replace("\n", " "))
    return lines[:14]


def build_page_doc(name: str, fname: str, route: str, roles: str) -> str:
    path = PAGES / fname
    if not path.exists():
        return f"### Page: {name}\n**File:** `frontend/src/pages/{fname}`\n**Route:** `{route}`\n**Role access:** {roles}\n**Purpose:** File not found on disk.\n\n"
    text = path.read_text(encoding="utf-8", errors="replace")
    # purpose: first line of component comment or first export const line
    purpose = "Student or staff UI for the SCALE web application."
    if 'Purpose:' in text[:500]:
        pass
    m = re.search(r"^\s*(?:/\*\*?\s*(.*?)\*/|//\s*(.+))", text[:800], re.S | re.M)
    if m:
        purpose = (m.group(1) or m.group(2) or "").strip().split("\n")[0][:200]
    apis = extract_apis(text)
    api_table = "| Endpoint (method + path) | Notes |\n|----------|------|\n"
    if apis:
        for a in apis[:25]:
            api_table += f"| {a} | From `useEffect` or handler |\n"
    else:
        api_table += "| — | No `/api` calls detected in file (static or child-only) |\n"
    states = extract_state(text)
    st_table = "| Hook / state (excerpt) |\n|---|\n"
    for s in states[:12]:
        st_table += f"| `{s[:180]}` |\n"
    if not states:
        st_table += "| *(see file for local state)* |\n"

    child = []
    for im in re.finditer(r"^import\s+(\w+)\s+from\s+['\"]\.\/", text, re.M):
        child.append(im.group(1))
    child_str = ", ".join(sorted(set(child))[:15]) or "—"

    return f"""### Page: {name}

**File:** `frontend/src/pages/{fname}`  
**Route:** `{route}`  
**Role access:** {roles}  

**Purpose:** {purpose}

**API calls (extracted):**

{api_table}

**State hooks (sample):**

{st_table}

**Child / local imports:** {child_str}

**Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

---

"""


def build_appendix_a() -> str:
    lines = ["## Appendix A — Complete Annotated File Tree", ""]
    lines.append(
        "The following tree lists repository files **excluding** `backend/uploads/`, `node_modules/`, `.git`, "
        "and other generated artifacts. Each file has a one-line purpose derived from its role in SCALE.\n"
    )
    skip_parts = ("node_modules", ".git", "uploads", "__pycache__", ".venv", "dist", "build")

    def walk(base: Path, prefix: str = ""):
        if not base.exists():
            return
        subs = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        for p in subs:
            rel = p.relative_to(ROOT)
            if any(part in skip_parts for part in rel.parts):
                continue
            if p.is_dir():
                lines.append(f"{prefix}{p.name}/")
                walk(p, prefix + "    ")
            else:
                # one-line description heuristic
                name = p.name
                low = name.lower()
                if low.endswith(".py"):
                    desc = "Python module."
                    if "api" in str(rel):
                        desc = "FastAPI router or API helper."
                    elif "scanner" in str(rel):
                        desc = "Static analysis or dependency scanning logic."
                    elif "sandbox" in str(rel):
                        desc = "Docker sandbox execution or test harness."
                elif low.endswith(".tsx"):
                    desc = "React TypeScript component or page."
                elif low == "docker-compose.yml":
                    desc = "Multi-service orchestration for SCALE stack."
                elif low == "requirements.txt":
                    desc = "Python dependencies for backend or service image."
                elif low.endswith(".md"):
                    desc = "Project documentation."
                else:
                    desc = "Source or configuration asset."
                lines.append(f"{prefix}{name} — {desc}")

    lines.append("```text")
    lines.append("grad-project/")
    walk(ROOT / "backend" / "app", "    ")
    walk(ROOT / "frontend" / "src", "    ")
    for extra in ("docker-compose.yml", "backend/requirements.txt", "frontend/package.json", ".env.example"):
        ep = ROOT / extra
        if ep.exists():
            lines.append(f"│   ├── {extra} — configuration or manifest")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def build_appendix_b() -> str:
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
    api_root = ROOT / "backend" / "app" / "api"
    routes: list[tuple[str, str, str]] = []
    for f in sorted(api_root.glob("*.py")):
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
    rows = []
    for full, method, mod in sorted(routes, key=lambda x: (x[0].lower(), x[1])):
        k = (full, method)
        if k in seen:
            continue
        seen.add(k)
        rows.append((method, full, mod))
    rows.append(("GET", "/", "main"))
    rows.sort(key=lambda x: (x[1].lower(), x[0]))

    out = [
        "## Appendix B — Complete Route Map (alphabetical by path)",
        "",
        "| Method | Path | Router module | Auth (typical) | Description |",
        "|--------|------|---------------|----------------|-------------|",
    ]
    for method, path, mod in rows:
        auth = "Yes (JWT)"
        if path in ("/api/auth/register", "/api/auth/login"):
            auth = "No"
        elif path == "/":
            auth = "No"
        if "/admin/" in path or path.endswith("/admin/overview"):
            auth = "Yes (admin)"
        out.append(f"| {method} | `{path}` | `{mod}.py` | {auth} | See Section 14 |")
    out.append("")
    out.append(f"**Total routes:** {len(rows)} (including `GET /`).")
    out.append("")
    return "\n".join(out)


def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    # Section 15
    sec15 = ["## 15. Frontend Pages Reference", ""]
    sec15.append(
        "This section documents each `frontend/src/pages/*.tsx` file. Routes match `App.tsx` unless noted. "
        "The **ChallengeHintPanel** component (not a page) uses `POST /api/challenge/hint` (game_challenge router) "
        "for leveled hints and `POST /api/ai/mentor-chat` for the mentor; this is distinct from "
        "`GET /api/challenges/hints` and `POST /api/challenges/hints/use` on the main challenges router.\n"
    )
    for comp, fname, route, roles in APP_ROUTES:
        sec15.append(build_page_doc(comp, fname, route, roles))
    # Unrouted page files still on disk
    routed_files = {x[1] for x in APP_ROUTES}
    for p in sorted(PAGES.glob("*.tsx")):
        if p.name not in routed_files and p.name not in ("HomePage.tsx", "ScenarioPage.tsx"):
            sec15.append(
                build_page_doc(p.stem, p.name, "(compose-only: imported by wrapper, not App.tsx)", "see parent route")
            )

    new_sec15 = "\n".join(sec15)

    # Replace between ## 15 and ## 16
    m15 = re.search(
        r"(## 15\. Frontend Pages Reference\n)(.*?)(\n## 16\. Environment and Configuration)",
        text,
        re.S,
    )
    if not m15:
        raise SystemExit("Could not find Section 15 boundaries")
    text = text[: m15.start()] + new_sec15 + m15.group(3) + text[m15.end() :]

    # Replace Appendix A through end of Appendix B (before Appendix C)
    mab = re.search(
        r"(## Appendix A — Complete Annotated File Tree\n)(.*?)(\n## Appendix C — Glossary)",
        text,
        re.S,
    )
    if not mab:
        raise SystemExit("Could not find Appendix A–B block")
    new_a = build_appendix_a()
    new_b = build_appendix_b()
    text = text[: mab.start()] + new_a + "\n\n" + new_b + mab.group(3) + text[mab.end() :]

    # Remove Appendix E–G filler and duplicate Documentation Statistics before final block
    mg = re.search(
        r"\n## Appendix E — Per-Endpoint Operational Reference[\s\S]*?(?=\n---\n\n## Documentation Statistics \(Final\))",
        text,
    )
    if mg:
        text = text[: mg.start()] + "\n" + text[mg.end() :]
    # Remove orphan first "## Documentation Statistics" block (before Appendix E was removed)
    text = re.sub(
        r"\n## Documentation Statistics\n\n- Total line count:.*?(?=\n## Appendix [A-D]|\n---\n\n## Documentation Statistics \(Final\))",
        "\n",
        text,
        count=1,
        flags=re.S,
    )

    # Fix duplicate ## 15 heading if any
    text = re.sub(r"## 15\. Frontend Pages Reference\n\n## 15\. Frontend Pages Reference\n", "## 15. Frontend Pages Reference\n", text)

    DOC.write_text(text, encoding="utf-8")
    nlines = len(text.splitlines())
    nwords = len(text.split())
    print("Wrote", DOC, "lines", nlines, "words", nwords)


if __name__ == "__main__":
    main()
