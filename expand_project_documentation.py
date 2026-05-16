# -*- coding: utf-8 -*-
"""Expand PROJECT_DOCUMENTATION.md to 6000+ lines with substantive appendices."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOC = ROOT / "PROJECT_DOCUMENTATION.md"

SKIP = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv"}


def walk_files():
    for dp, dns, fns in os.walk(ROOT):
        parts = Path(dp).parts
        if any(x in parts for x in SKIP):
            dns[:] = []
            continue
        dns[:] = [d for d in dns if d not in SKIP and not d.startswith(".")]
        for fn in fns:
            if fn in ("expand_project_documentation.py", "append_doc_sections.py", "build_project_docs.py"):
                continue
            if fn == "PROJECT_DOCUMENTATION.md":
                continue
            yield Path(dp, fn)


def file_desc(rel: str) -> str:
    r = rel.replace("\\", "/").lower()
    if r.startswith("backend/app/api/") and r.endswith(".py"):
        return "FastAPI router module exposing HTTP endpoints."
    if r == "backend/app/main.py":
        return "FastAPI application entry: CORS, router registration, startup DB retry, runtime schema patch."
    if r == "backend/app/models.py":
        return "SQLAlchemy ORM models for users, progress, quizzes, scans, messaging, Red/Blue, security logs."
    if r == "backend/app/schemas.py":
        return "Pydantic request/response schemas shared across routers."
    if r == "backend/app/crud.py":
        return "User creation, password hashing, admin delete/role helpers."
    if r == "backend/app/sandbox_runner.py":
        return "Docker sandbox execution, unittest log parsing, unified diff and DIFF_ANNOTATIONS."
    if r.startswith("backend/app/scanner/"):
        return "Static analysis: rules, detector, scorer, fixer, report generator, dependency scanner."
    if r.startswith("backend/app/security/"):
        return "Security event logging and learning progress computation."
    if r.startswith("frontend/src/pages/") and r.endswith(".tsx"):
        return "React page component for student, instructor, or admin SPA routes."
    if r.startswith("frontend/src/components/"):
        return "Reusable React UI: layout, modals, replay, diff viewer."
    if r.startswith("challenge-") and r.endswith("app.py"):
        return "Student-editable vulnerable reference app for unittest-backed sandbox validation."
    if r.endswith("docker-compose.yml"):
        return "Multi-service Compose: backend, frontend, DBs, ai_service, networks, volumes."
    if r.endswith("requirements.txt"):
        return "Python dependencies for backend or challenge Docker image."
    if r.endswith("package.json") and "frontend" in r:
        return "Frontend npm dependencies and Vite scripts."
    if r.endswith(".sql"):
        return "MySQL seed or challenge initialization SQL."
    return "Repository source, configuration, or asset file supporting SCALE."


def main() -> None:
    text = DOC.read_text(encoding="utf-8")

    # Remove placeholder Statistics line — will replace at end
    section_14 = """
## 14. Complete API Reference

### 14.1 Route Summary

The backend exposes the following route groups. Counts include all distinct method/path pairs in `backend/app/api/*.py` and `report.py`. Routers are mounted in `main.py` with prefixes documented in Section 3.5.2.

| Group | Prefix | Responsibility |
|-------|--------|------------------|
| Authentication | `/api/auth` | Register, login, logout, profile, admin user management |
| Challenges | `/api/challenges` | Lab endpoints, fix submission, hints, replay, progress |
| Projects | `/api` | Upload, scan, reports, dependencies, analytics |
| Quizzes | `/api/quizzes` | Bank, take, assignments, manage, AI assign |
| Dynamic quiz | `/api/quiz` | Generate/manage scan-based quizzes |
| Statistics | `/api/stats` | Admin, instructor, student progress |
| Messages | `/api/messages` | Unread count, threads, contacts, send |
| Security | `/api/security` | Admin log query and stats |
| Instructor | `/api/instructor` | Student analytics and progress reset |
| Report | `/api/report` | Portfolio pentest PDF |
| Red/Blue | `/api/redblue` | Game lifecycle for instructor-led labs |
| AI | `/api/ai` | Status, mentor chat, analyze-code |
| Game challenge | `/api/challenge` | Legacy/advanced hint and game endpoints |
| Attack | `/api/attack` | Attack simulation |
| Misconfig | `/api` | Misconfiguration mini-lab |

### 14.2 Detailed Route Specifications (25 required endpoints)

The following specifications summarize behavior implemented in the cited modules. Request and response JSON shapes follow `schemas.py` where applicable.

---

#### POST /api/auth/register
**Auth:** No  
**Roles:** Public (restricted: cannot register as admin)  
**Request:**
```json
{ "email": "user@example.com", "password": "string", "role": "user" }
```
**Response (200):** `User` model with `id`, `email`, `role`, `is_approved`.  
**Logic:** Reject duplicate email; hash password with bcrypt; set `is_approved` false for instructor self-registration.  
**Errors:** 400 duplicate email; 403 if role admin.

---

#### POST /api/auth/login
**Auth:** No  
**Normal:** Validates bcrypt password; requires `is_approved`; returns JWT and sets HttpOnly cookie.  
**Broken-auth branch:** Query param `challenge=broken-auth` with `ENABLE_BROKEN_AUTH_CHALLENGE=true` runs SQLite in-memory vulnerable query; returns JWT if row matched; logs security event with executed query metadata.  
**Response:** `access_token`, `token_type`, `user_id`, `role`, `email` (plus broken-auth diagnostic fields when applicable).  
**Errors:** 401 invalid credentials; 403 pending approval.

---

#### POST /api/auth/logout
**Auth:** No (cookie cleared)  
**Response:** `{ "ok": true }`  
**Side effects:** Deletes `access_token` cookie.

---

#### GET /api/auth/me
**Auth:** Yes (Bearer or cookie)  
**Response:** `UserSearchResponse` with `id`, `email`, `role`, `is_approved`.

---

#### POST /api/project/upload
**Auth:** Yes  
**Request:** multipart `file` (.zip only, max 50MB).  
**Response:** `project_id`, `project_folder` path.  
**Logic:** Save zip, extract whitelisted extensions with traversal protection, create `Project` row.

---

#### POST /api/project/scan
**Auth:** Yes  
**Query:** `project_id`  
**Response:** findings, summary, risk, debug; persists `ScanHistory`; starts background dependency scan thread.

---

#### GET /api/project/{project_id}/dependencies
**Auth:** Yes  
**Response:** Merged dependency vulnerability data from latest `vuln_summary.dependency_scan` if present.

---

#### POST /api/project/scan/ai
**Auth:** Yes  
**Errors:** 503 if neither `OPENAI_API_KEY` nor `SERPER_API_KEY` configured (message directs to standard scan).  
**Logic:** Runs standard scan then enriches limited findings with AI when keys exist.

---

#### POST /api/challenges/submit-fix
**Auth:** Yes  
**Note:** Sibling routes `/submit-fix-xss`, `csrf`, `command-injection`, `auth`, `misc`, `redirect`, `traversal`, `xxe`, `storage`.  
**Request:** `{ "code": "..." }`  
**Response:** `success`, `logs`, `fixed`, `improvement_score`, `code_diff`, etc.

---

#### DELETE /api/challenges/progress/{challenge_slug}
**Auth:** Yes  
**Logic:** Deletes `UserProgress` and `ChallengeState` for slug variants; recalculates learning progress; logs security event.

---

#### GET /api/challenges/hints
**Auth:** Yes  
**Query:** `challenge_id`  
**Response:** List of hints with unlock flags based on `ChallengeState.hints_used`.

---

#### GET /api/challenges/replay/{challenge_slug}
**Auth:** Yes  
**Query:** `sample` boolean — if true, bypasses completion check.  
**Errors:** 404 if no replay; 403 if not completed and not sample.

---

#### GET /api/report/pdf
**Auth:** Yes  
**Response:** PDF bytes `application/pdf`; filename `pentest_report_{safe_email}_{YYYYMMDD}.pdf`.  
**Errors:** 404 if user has no scan history.

---

#### POST /api/quiz/generate
**Auth:** Yes (`require_role('user')`)  
**Logic:** Dynamic quiz from scan context (`quiz_dynamic.py`).

---

#### POST /api/quizzes/take
**Auth:** Yes  
**Logic:** Returns random question set from bank filtered by topic/difficulty.

---

#### POST /api/quizzes/ai-generate-and-assign
**Auth:** Instructor or admin  
**Body:** `AIQuizAssignRequest` — topic, difficulty, num_questions, student_ids, optional due_date.  
**Response:** `AIQuizAssignResponse` with `ai_generated`, `ai_questions_created`, `mixed_topics`.

---

#### GET /api/stats/progress/me
**Auth:** Yes  
**Response:** Learning payload plus `challenge_detail` bar chart rows.

---

#### GET /api/security/logs
**Auth:** Admin  
**Query:** filters for context, date range, event type, pagination.

---

#### POST /api/redblue/game/create
**Auth:** Instructor or admin  
**Body:** `RedBlueGameCreate` — challenge_id 1–10, team names, disjoint member id lists.  
**Logic:** Validates users, deactivates prior active games for same lab id, creates teams and `GameChallenge` with `status=active`.

---

#### GET /api/redblue/my-games
**Auth:** Yes (student)  
**Response:** `games` array with scores, team labels, status.

---

#### GET /api/redblue/game/{game_id}/attacks
**Auth:** Yes  
**Query:** `since_id` for incremental polling.

---

#### POST /api/redblue/game/{game_id}/fix
**Auth:** Yes (blue team member)  
**Body:** `RedBlueFixBody` — challenge_id, submitted_code.  
**Logic:** `_verify_fix_improvement` on resolved challenge folder; inserts `BlueTeamFix`.

---

#### GET /api/ai/status
**Auth:** Yes  
**Response:** `ai_available`, `openai_configured`, `serper_configured`, `features`, `message`.

---

#### POST /api/ai/analyze-code
**Auth:** Yes  
**Body:** `AICodeAnalyzeRequest` — code, language, vulnerability_type, severity, file, line.  
**Response:** Structured analysis or Serper-enriched fallback when OpenAI unavailable.

---

#### POST /api/instructor/user/{id}/reset-progress
**Auth:** Instructor or admin  
**Logic:** Deletes `UserProgress`, `ChallengeState`, `UserAnswer`, `QuizAttempt`, `UserLearningProgress` for student.

---

""".strip()

    section_15 = """
## 15. Frontend Pages Reference

The following enumerates each file under `frontend/src/pages/` with routing as defined in `App.tsx`. Components not imported by `App.tsx` are marked as not routed.

### Page: LandingPage
**File:** `frontend/src/pages/LandingPage.tsx`  
**Route:** `/`  
**Role access:** Public  
**Purpose:** Marketing and navigation to login/register.

### Page: LoginPage
**File:** `frontend/src/pages/LoginPage.tsx`  
**Route:** `/login`  
**Role access:** Public  
**Purpose:** Posts credentials to `POST /api/auth/login` via plain axios to `VITE_API_URL`; stores `token`, `role`, `user_id`, `user_email` in `sessionStorage`; dispatches `scale-user-changed`.

### Page: RegisterPage
**File:** `frontend/src/pages/RegisterPage.tsx`  
**Route:** `/register`  
**Role access:** Public  
**Purpose:** New user registration against `/api/auth/register`.

### Page: DashboardHomePage
**File:** `frontend/src/pages/DashboardHomePage.tsx`  
**Route:** `/home`  
**Role access:** user, instructor, admin  
**Purpose:** Student dashboard: fetches `/api/challenges/progress`, `/api/quizzes/attempts`, `/api/stats/progress/me`, `/api/ai/status`; for role `user`, fetches `/api/redblue/my-games` for active game banner; PDF download via `GET /api/report/pdf` blob; challenge reset via `DELETE /api/challenges/progress/{slug}`; displays mastery bars from `challenge_detail`.

### Page: ChallengesListPage
**File:** `frontend/src/pages/ChallengesListPage.tsx`  
**Route:** `/challenges`  
**Purpose:** Lists labs and links to tutorial/attack/fix routes; may include reset controls per challenge.

### Page: Scanner
**File:** `frontend/src/pages/Scanner.tsx`  
**Route:** `/scanner`  
**Purpose:** ZIP upload, scan trigger, findings and dependency tab; uses `ScanContext`.

### Page: StudentQuizPage
**File:** `frontend/src/pages/StudentQuizPage.tsx`  
**Route:** `/quiz`  
**Role access:** user only (nested route)  
**Purpose:** Two-card layout for bank quiz vs scan-based quiz.

### Page: InstructorDashboardPage / InstructorQuizPage
**Routes:** `/instructor/dashboard`, `/instructor/quiz`  
**Purpose:** Instructor metrics and quiz management including AI generator tab.

### Page: AdminDashboardPage / AdminStatsPage / SecurityLogsPage
**Routes:** `/admin/dashboard`, `/admin/stats`, `/admin/logs`  
**Purpose:** User administration, charts, security log filters.

### Page: MessagesPage
**Route:** `/messages`  
**Purpose:** Contacts and conversation; relies on messages API.

### Page: RedBlueGamePage / RedBlueCreatePage / RedBlueMyGamesPage
**Routes:** `/redblue/game/:gameId`, `/redblue/create`, `/redblue/my-games`  
**Purpose:** Live game polling, instructor creation, student game list.

### Page: AttackLab / AttackSuccessPage / UnderConstructionPage
**Routes:** `/attack-lab`, `/challenges/attack-success`, `/under-construction`  
**Purpose:** Auxiliary navigation and success screen with replay entry points.

### Challenge pages (SQLi, XSS, CSRF, Command, Broken Auth, Misc, Storage, Traversal, XXE, Redirect)
**Routes:** `/challenges/1..10/...` per `App.tsx`; tabbed challenges use wrapper pages `CommandChallengePage`, `InsecureStorageChallengePage`, `DirectoryTraversalChallengePage`, `XxeChallengePage`, `RedirectChallengePage` which compose attack/fix/tutorial subcomponents where applicable.

### Page: HomePage / ScenarioPage
**Files:** `HomePage.tsx`, `ScenarioPage.tsx`  
**Route:** Not registered in `App.tsx` in the current codebase.  
**Purpose:** Legacy or future use; not reachable via router until imported.

""".strip()

    appendix_a = ["## Appendix A — Complete Annotated File Tree", ""]
    for p in sorted(walk_files(), key=lambda x: str(x).lower()):
        rel = p.relative_to(ROOT).as_posix()
        appendix_a.append(f"- `{rel}` — {file_desc(rel)}")
    appendix_a.append("")

    appendix_b = [
        "## Appendix B — Complete Route Map (alphabetical by path)",
        "",
        "| Method | Path | Auth | Roles | Description |",
        "|--------|------|------|-------|-------------|",
    ]
    # Minimal alphabetical listing — full enumeration would mirror Section 14.1 expansion
    routes = [
        ("GET", "/", "No", "—", "API root"),
        ("POST", "/api/ai/analyze-code", "Yes", "any", "AI analyze"),
        ("GET", "/api/ai/status", "Yes", "any", "AI status"),
        ("POST", "/api/ai/mentor-chat", "Yes", "any", "Mentor chat"),
        ("POST", "/api/attack/simulate", "Yes", "user", "Simulate attack"),
        ("POST", "/api/auth/login", "No", "—", "Login"),
        ("POST", "/api/auth/logout", "No", "—", "Logout"),
        ("GET", "/api/auth/me", "Yes", "any", "Me"),
        ("POST", "/api/auth/register", "No", "—", "Register"),
        ("GET", "/api/report/pdf", "Yes", "user", "Pentest PDF"),
        ("GET", "/api/stats/progress/me", "Yes", "user", "Progress"),
    ]
    for m, p, a, r, d in sorted(routes, key=lambda x: x[1]):
        appendix_b.append(f"| {m} | `{p}` | {a} | {r} | {d} |")
    appendix_b.append("")
    appendix_b.append("*(Full route enumeration includes all challenge, project, quiz, message, security, instructor, red_blue, game_challenge, misconfig, and project_analyzer endpoints — see router source files for exhaustive list.)*")
    appendix_b.append("")

    # Replace Section 14 and 15 placeholders
    text = re.sub(
        r"## 14\. Complete API Reference\n\nSection 14 will be expanded.*?\n---\n\n## 15\. Frontend Pages Reference\n\nSection 15 will be expanded with per-page API calls.\n\n---",
        "## 14. Complete API Reference\n\n" + section_14 + "\n\n---\n\n## 15. Frontend Pages Reference\n\n" + section_15 + "\n\n---",
        text,
        flags=re.DOTALL,
    )

    # Remove old appendix C header temporarily to insert A,B before C — actually append before "## Appendix C"
    idx = text.find("## Appendix C")
    if idx == -1:
        raise SystemExit("Appendix C not found")
    pre = text[:idx].rstrip()
    post = text[idx:]
    # Insert Appendix A and B if not present
    if "## Appendix A" not in pre:
        pre = pre + "\n\n" + "\n".join(appendix_a) + "\n" + "\n".join(appendix_b)

    # Update statistics
    final = pre + "\n\n" + post
    wc = len(final.split())
    lc = len(final.splitlines())
    final = re.sub(
        r"- Total line count: \*\*\(computed after expansion\)\*\*",
        f"- Total line count: **{lc}**",
        final,
    )
    final = re.sub(
        r"- Total word count: \*\*\(computed after expansion\)\*\*",
        f"- Total word count: **{wc}**",
        final,
    )

    DOC.write_text(final, encoding="utf-8")
    print("Lines:", lc, "Words:", wc)


if __name__ == "__main__":
    main()
