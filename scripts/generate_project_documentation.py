"""
Generates PROJECT_DOCUMENTATION.md at repository root from narrative sections
plus verbatim excerpts of configuration and core modules (read from disk).
Run: python scripts/generate_project_documentation.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def _h2_spans_outside_fences(lines: list[str]) -> list[tuple[str, int, int, int]]:
    """Return (title, start_line, end_line, count) for each ## header outside ``` fences."""
    in_fence = False
    headers: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## ") and not line.startswith("###"):
            headers.append((line[3:].strip(), i + 1))
    spans: list[tuple[str, int, int, int]] = []
    for j, (name, start) in enumerate(headers):
        end = headers[j + 1][1] - 1 if j + 1 < len(headers) else len(lines)
        spans.append((name, start, end, end - start + 1))
    return spans


def lines() -> list[str]:
    out: list[str] = []

    def w(*parts: str) -> None:
        for p in parts:
            out.extend(p.splitlines() if "\n" in p else [p])

    def blank() -> None:
        out.append("")

    def fence(lang: str, body: str) -> None:
        out.append(f"```{lang}")
        out.extend(body.rstrip().splitlines())
        out.append("```")
        blank()

    w("# SCALE — Security Challenge and Learning Environment")
    w("## Complete System Documentation")
    w("### Version: Final Release | Graduation Project Submission")
    blank()
    w("---")
    blank()
    w("## Abstract")
    w(
        "SCALE (Security Challenge and Learning Environment) is a web-based platform for applied "
        "cybersecurity education built from a FastAPI backend, a React/Vite single-page application, "
        "three MySQL 8.0 instances under Docker Compose, and optional OpenAI-backed analysis. Students "
        "upload ZIP archives for regex-driven static analysis with OSV.dev dependency enrichment, "
        "complete ten interactive vulnerability laboratories with Docker-sandboxed fix validation, "
        "take static and scan-derived quizzes, and export a penetration-test-style PDF report. "
        "Instructors manage quiz banks, assignments, and Red versus Blue games mapped to lab identifiers "
        "1–10. Administrators govern accounts and audit centralized security event logs. Authentication "
        "uses JWT bearer tokens with optional HttpOnly cookies; role-based access control restricts "
        "instructor and admin surfaces. The platform intentionally exposes pedagogical vulnerabilities "
        "only on designated routes. This document describes the as-built system from source; features "
        "absent from the repository (such as dedicated CTF flag databases) are explicitly noted rather "
        "than assumed."
    )
    blank()
    w("## Table of Contents")
    w("")
    w("- [Abstract](#abstract)")
    w("- [1. Project Overview](#1-project-overview)")
    w("- [2. Architecture](#2-architecture)")
    w("- [3. Authentication and Authorization](#3-authentication-and-authorization)")
    w("- [4. Challenge System](#4-challenge-system)")
    w("- [5. Project Scanner](#5-project-scanner)")
    w("- [6. Penetration Test Report Generation (Student PDF)](#6-penetration-test-report-generation-student-pdf)")
    w("- [7. Quiz System](#7-quiz-system)")
    w("- [8. Learning Progress and Analytics](#8-learning-progress-and-analytics)")
    w("- [9. Security Event Logging](#9-security-event-logging)")
    w("- [10. Messaging System](#10-messaging-system)")
    w("- [11. AI Services](#11-ai-services)")
    w("- [11a. CTF Competitive Mode (not implemented in backend)](#11a-ctf-competitive-mode-not-implemented-in-backend)")
    w("- [11b. Red vs Blue Team Mode (instructor-led)](#11b-red-vs-blue-team-mode-instructor-led)")
    w("- [12. Complete API Reference](#12-complete-api-reference)")
    w("- [13. Data Models Reference](#13-data-models-reference)")
    w("- [14. Frontend Pages Reference](#14-frontend-pages-reference)")
    w("- [15. Environment and Configuration](#15-environment-and-configuration)")
    w("- [16. Setup and Deployment Guide](#16-setup-and-deployment-guide)")
    w("- [17. Known Limitations and Technical Debt](#17-known-limitations-and-technical-debt)")
    w("- [18. Security Considerations](#18-security-considerations)")
    w("- [Appendix A — Annotated File Tree](#appendix-a--annotated-file-tree-abbreviated)")
    w("- [Appendix B — Complete Route Map](#appendix-b--complete-route-map-alphabetical-by-path)")
    w("- [Appendix C — Glossary](#appendix-c--glossary)")
    w("- [Appendix D — Verbatim configuration and core modules](#appendix-d--verbatim-configuration-and-core-modules)")
    w("- [Documentation Statistics](#documentation-statistics)")
    w("- [Graduation outline cross-reference](#graduation-outline-cross-reference)")
    blank()
    w("## Graduation outline cross-reference")
    w(
        "The submission specification numbered sections **1–20** plus appendices A–C. This file uses a "
        "subsystem-oriented numbering that consolidates the same material: **Introduction / problem / "
        "objectives** appear under **§1 Project Overview**; **system overview, learning loop, stack** "
        "span **§1–2**; **architecture** is **§2**; **authentication** is **§3**; **challenges and sandbox** "
        "**§4**; **scanner** **§5**; **student PDF report** **§6**; **quizzes** **§7**; **learning analytics** "
        "**§8**; **security logs** **§9**; **messaging** **§10**; **AI** **§11**; **CTF absence** **§11a**; "
        "**Red vs Blue** **§11b**; **full route list** **§12** and **Appendix B**; **ORM summary** **§13**; "
        "**frontend pages** **§14**; **environment** **§15**; **setup** **§16**; **limitations** **§17**; "
        "**security analysis** **§18**. **Appendix A** lists every repository file path; **Appendix C** is the "
        "glossary; **Appendix D** embeds configuration and core modules verbatim. **Detailed route specs** appear "
        "under **§12** (selected endpoints). **Data model repetition** requested as §15 in the template is "
        "represented by **§13** here plus column detail in Appendix D models files where cited."
    )
    blank()
    w(
        "The narrative below describes the **SCALE** security learning platform as implemented in the "
        "repository at generation time. Behaviour statements are derived from reading application "
        "source files (FastAPI backend, React/Vite frontend, Docker Compose, scanners, and supporting "
        "services). Where pedagogical vulnerabilities exist by design, they are described explicitly."
    )
    blank()
    w("---")
    blank()

    # --- Section 1 ---
    w("## 1. Project Overview")
    w("### 1.1 Purpose and Scope")
    w(
        "SCALE is a web-based platform for **applied cybersecurity education**. It targets three "
        "audiences: **students** (`role=user`), who complete hands-on vulnerability labs, upload "
        "projects for static analysis, take quizzes, and track progress; **instructors**, who view "
        "class-wide analytics and manage quiz assignments; and **administrators**, who approve "
        "accounts, manage roles, and review centralized security event logs. The system name appears "
        "in the public API root handler (`GET /` returns a welcome message for the SCALE API in "
        "`backend/app/main.py`)."
    )
    w(
        "Unlike a lecture-only course, SCALE combines **rule-based project scanning** (regex patterns "
        "over uploaded ZIP archives), **interactive exploit endpoints** (intentionally vulnerable "
        "routes under `/api/challenges` and related routers), **sandboxed fix validation** (Docker "
        "builds per submission against `run_tests.sh` in each challenge folder), **two quiz subsystems** "
        "(database MCQ bank under `/api/quizzes` and synthetic questions from scan findings under "
        "`/api/quiz`), and **PDF reporting** (`GET /api/report/pdf`) summarizing scans, remediation, "
        "and quiz metrics for the authenticated student."
    )
    w(
        "The platform teaches identification and remediation of common web weaknesses aligned with "
        "the ten lab tracks: SQL injection, XSS, CSRF, command injection, broken authentication, "
        "security misconfiguration, insecure storage, directory traversal, XXE, and unvalidated "
        "redirect. Students progress through attack simulation pages, optional tutorials, fix editors "
        "that post code to the backend, and quizzes that reinforce concepts."
    )
    w(
        "SCALE differs from a generic LMS by embedding **deliberately vulnerable behaviour** in "
        "controlled API routes (for example string-built SQL in the SQLi lab, SQLite-built queries in "
        "broken-auth challenge mode, and `shell=True` subprocess usage in the command-injection lab). "
        "Those behaviours are constrained to specific endpoints and documented here so operators "
        "understand scope and residual risk (especially command execution on the API host)."
    )
    w("### 1.2 Core Learning Philosophy")
    w(
        "The implemented learning path is **Scan → Attack → Fix → Quiz → Progress**, supported by "
        "logging and dashboards. **Scan**: the student uploads a `.zip` via `POST /api/project/upload`; "
        "files are extracted under `STORAGE_ROOT/uploads/extracted_projects/<project_id>` with "
        "extension filtering and path traversal checks (`extract_zip` in `projects.py`). "
        "**Attack**: each challenge exposes HTTP endpoints that mirror vulnerable patterns; the React "
        "routes under `/challenges/<id>/...` call these APIs. Successful exploitation often triggers "
        "`POST /api/challenges/mark-attack-complete` and navigation to `/challenges/attack-success`. "
        "**Fix**: the student submits Python source for `app.py`; `_verify_fix_improvement` in "
        "`challenges.py` runs the reference vulnerable file and the submission through "
        "`sandbox_runner.run_in_sandbox_detailed`, compares unittest failure/error counts, and on "
        "success inserts `UserProgress` and calls `recalculate_learning_progress`. "
        "**Quiz**: `StudentQuizPage` uses the bank (`/api/quizzes/take`) and/or dynamic generation "
        "(`POST /api/quiz/generate`) using `ScanContext` data from `localStorage` key `scale.scanData.{user_id}` "
        "(or `scale.scanData.guest`). "
        "**Progress**: `GET /api/stats/progress/me` returns `build_learning_progress_payload` including "
        "radar dimensions from `SKILL_BUCKETS` in `learning_tracker.py`."
    )
    w(
        "Pedagogically, the ordering matters because scanning grounds abstract rules in real project "
        "artefacts; attacks build intuition; fixes are objectively graded by automated tests; quizzes "
        "consolidate vocabulary; and aggregated metrics give instructors visibility into skill gaps."
    )
    w("### 1.3 Technology Stack")
    w(
        "| Layer | Technology | Version | Purpose |\n"
        "|-------|------------|---------|---------|\n"
        "| HTTP API | FastAPI | unpinned (`requirements.txt`) | REST API and OpenAPI |\n"
        "| ASGI server | Uvicorn | unpinned (`uvicorn[standard]`) | Serves FastAPI in containers |\n"
        "| ORM | SQLAlchemy | unpinned | MySQL persistence |\n"
        "| DB driver | PyMySQL | unpinned | MySQL dialect for SQLAlchemy |\n"
        "| Auth | python-jose[cryptography], passlib[bcrypt], bcrypt==4.0.1 | bcrypt pinned | JWT and password hashing |\n"
        "| PDF | ReportLab | unpinned | Student pentest PDF and project PDF reports |\n"
        "| Sandbox | docker (PyPI) + Docker Engine socket | unpinned | Per-submission challenge images |\n"
        "| AI client | openai | unpinned | Optional AI enrichment paths |\n"
        "| Frontend runtime | React | ^18.2.0 (`package.json`) | SPA |\n"
        "| Frontend language | TypeScript | ^5.2.2 | Type-safe UI |\n"
        "| Build tool | Vite | ^5.2.0 | Dev server and bundling |\n"
        "| HTTP client | axios | ^1.12.2 | Calls backend with credentials |\n"
        "| Styling | Tailwind CSS | ^3.4.3 | Utility-first CSS |\n"
        "| Charts | recharts | ^3.7.0 | Dashboard radar and charts |\n"
        "| Database | MySQL | 8.0 (`mysql:8.0` image) | Three separate instances |\n"
        "| Orchestration | Docker Compose | project file | Services and networking |"
    )
    w("### 1.4 System Capabilities Summary")
    w(
        "- Registers and authenticates users with bcrypt-hashed passwords and JWT bearer tokens; optional "
        "HttpOnly cookie (`AUTH_COOKIE_NAME`, default `access_token`) parallel to bearer auth.\n"
        "- Exposes ten guided challenge tracks with attack routes, fix submission endpoints, optional XSS "
        "comment storage, CSRF transfer lab backed by `CSRF_DATABASE_URL`, and in-memory storage for "
        "the insecure-storage lab.\n"
        "- Validates student fixes inside disposable Docker images on network `scale_net`, parses "
        "unittest output, and returns structured improvement metrics plus optional `code_diff` lines "
        "with annotations from `DIFF_ANNOTATIONS` in `sandbox_runner.py`.\n"
        "- Performs static analysis on uploaded projects: per-line regex rules, CSRF heuristics, "
        "`attach_fixes` recommendations, risk scoring, persistence in `scan_history.vuln_summary`.\n"
        "- Offers AI-assisted scan explanation (`POST /api/project/scan/ai`) and AI mentor analysis "
        "(`POST /api/ai/analyze-code`) when configured.\n"
        "- Generates a **student** penetration-test-style PDF via `GET /api/report/pdf` from latest owned "
        "scan, `UserProgress`, `ChallengeState`, `QuizAttempt`, and security logs.\n"
        "- Generates **per-project** JSON/PDF reports via `GET /api/project/report` and "
        "`GET /api/project/report/pdf` using `scanner/report_generator.py`.\n"
        "- Provides instructor class dashboards and per-student analytics; admin dashboards and security "
        "log review; internal messaging; legacy red/blue mini-game under `/api/challenge` and instructor-led "
        "games under `/api/redblue` (see §11b)."
    )
    blank()

    # Section 2
    w("## 2. Architecture")
    w("### 2.1 High-Level Architecture")
    w(
        "The **browser** loads the React SPA from the **frontend** container on host port **5173** "
        "(Vite dev server). API calls use `VITE_API_URL` (default `http://localhost:8000`) so the browser "
        "reaches the **backend** on port **8000**. The backend connects to **main_db** (MySQL on internal "
        "3306, host-mapped 3306) via `DATABASE_URL`. Separate MySQL services **challenge_db_sqli** "
        "(host 3307) and **challenge_db_csrf** (host 3308) hold lab data for SQLi and CSRF respectively. "
        "The **ai_service** container listens on **8001** for template generation used by quiz AI preview. "
        "The backend mounts `/var/run/docker.sock` and challenge directories under `/app/challenges/*` "
        "so `sandbox_runner` can build images and join **`scale_net`**. All listed services attach to "
        "the bridge network `scale_net`."
    )
    w("### 2.2 Docker Compose Services")
    w(
        "| Service Name | Image/Build | Host Ports | Volumes | Depends On | Purpose |\n"
        "|----------------|------------|------------|---------|------------|---------|\n"
        "| sandbox_base | build `./backend/sandbox_base` → `scale-sandbox-base` | none | none | — | Pre-build base image for sandbox (exits after echo) |\n"
        "| backend | build `./backend` | 8000:8000 | docker.sock; `./backend`→`/app`; each `./challenge-*`→`/app/challenges/...` | main_db, challenge_db_sqli, challenge_db_csrf healthy; sandbox_base completed | FastAPI API, seed, Uvicorn |\n"
        "| frontend | build `./frontend` | 5173:5173 | `./frontend`→`/app`; anonymous `/app/node_modules` | — | Vite dev server |\n"
        "| ai_service | build `./ai_service` | 8001:8001 | `./ai_service`→`/app` | — | Auxiliary AI HTTP service |\n"
        "| main_db | mysql:8.0 | 3306:3306 | `scale_db_data`; `./db_init/init.sql` | — | Application database |\n"
        "| challenge_db_sqli | mysql:8.0 | 3307:3306 | `./challenge-sql-injection/users.sql` | — | SQLi lab DB |\n"
        "| challenge_db_csrf | mysql:8.0 | 3308:3306 | `./challenge-csrf/csrf.sql` | — | CSRF lab DB |\n"
        "Named volume **scale_db_data** persists main MySQL data."
    )
    w("### 2.3 Backend Architecture")
    w(
        "**Router registration** (`main.py`): `auth` → `/api/auth`; `quizzes` → `/api/quizzes`; "
        "`challenges` → `/api/challenges`; `stats` → `/api/stats`; `messages` → `/api/messages`; "
        "`projects` and `project_analyzer` → `/api` (no extra prefix); `game_challenge` → `/api/challenge`; "
        "`misconfig` → `/api`; `ai_mentor` → `/api/ai`; `attack_simulator` → `/api/attack`; "
        "`security_logs` → `/api/security`; `quiz_dynamic` → `/api/quiz`; `instructor` → `/api/instructor`; "
        "`report` includes its own prefix `/api/report`."
    )
    w(
        "**Startup**: `startup_event` retries `create_all` up to 10 times with 3s sleep on "
        "`OperationalError`, then `_ensure_runtime_schema()` issues conditional `ALTER TABLE` for "
        "`security_logs` and `user_learning_progress` when columns are missing."
    )
    w(
        "**CORS**: `CORSMiddleware` allows origins `http://localhost:5173`, `127.0.0.1:5173`, "
        "`localhost:3000`, `127.0.0.1:3000`; credentials enabled; methods and headers wildcard."
    )
    w(
        "**Dependencies**: `get_db` yields a SQLAlchemy session. `get_current_user` tries JWT from "
        "`Authorization: Bearer` via `OAuth2PasswordBearer` (`auto_error=False`), then cookie "
        "`AUTH_COOKIE_NAME`. `require_role(*roles)` maps `student` → `user` and returns 403 if role "
        "not in the allowed set."
    )
    w("### 2.4 Frontend Architecture")
    w(
        "**Routing** (`App.tsx`): Public `/`, `/login`, `/register`. Authenticated shell "
        "`ProtectedRoute` with `allowedRoles=['user','instructor','admin']` wraps `MainLayout` routes: "
        "`/home`, `/challenges`, `/messages`, `/scanner`, `/attack-lab`, all `/challenges/...` lab paths, "
        "`/under-construction`. Nested `ProtectedRoute` with `['user']` only wraps `/quiz`. "
        "Instructor routes: `/instructor/dashboard`, `/instructor/quiz`. Admin: `/admin/stats`, "
        "`/admin/dashboard`, `/admin/logs`. Unknown paths redirect to `/`."
    )
    w(
        "**Session storage** (`sessionStorage`): `token`, `role`, `user_id`, `user_email` set on login. "
        "Using **sessionStorage** (not `localStorage`) scopes tokens to the **browser tab**, so multiple "
        "tabs can hold different roles or sessions for testing."
    )
    w(
        "**Axios** (`lib/api.ts`): `baseURL` = `VITE_API_URL || http://localhost:8000`, `withCredentials` "
        "true. Request interceptor sets `Authorization: Bearer <token>` when token exists and is not "
        "`cookie-auth`."
    )
    w(
        "**ScanContext** (`context/ScanContext.tsx`): **localStorage** key `scale.scanData.{user_id}` "
        "(from `sessionStorage.user_id`, or `scale.scanData.guest`) holds last scan payload (project id, findings, "
        "summary, debug). `setScanData` normalizes `projectId`/`project_id`."
    )
    w(
        "**ProtectedRoute** (`components/ProtectedRoute.tsx`): on mount calls `GET /api/auth/me` with "
        "stored token; 401 clears session and redirects to `/login`."
    )
    w("### 2.5 Database Architecture")
    w(
        "- **main_db** (port 3306): application data — users, progress, quizzes, projects, scans, logs, "
        "game tables, learning aggregates.\n"
        "- **challenge_db_sqli** (host 3307): MySQL for `vulnerable-login` raw SQL in `SessionSQLi`.\n"
        "- **challenge_db_csrf** (host 3308): MySQL for CSRF transfer/accounts used via raw SQL in "
        "`challenges.py`.\n"
        "Isolation is **network and credential** separation: distinct containers and DSN environment "
        "variables (`SQLI_DATABASE_URL`, `CSRF_DATABASE_URL`)."
    )
    w(
        "Main ORM tables (see §13 for full column specs): `users`, `user_progress`, `xss_comments`, "
        "`challenges`, `questions`, `question_options`, `user_answers`, `quiz_assignments`, "
        "`quiz_assignment_students`, `quiz_assignment_questions`, `quiz_attempts`, `csrf_accounts`, "
        "`messages`, `projects`, `scan_history`, `teams`, `team_members`, `game_challenges`, "
        "`challenge_vulnerabilities`, `red_team_actions`, `blue_team_fixes`, `challenge_state`, "
        "`security_logs`, `user_learning_progress`."
    )
    w("### 2.6 Network and Security Configuration")
    w(
        "- **Docker network**: `scale_net` bridge driver (`docker-compose.yml`).\n"
        "- **JWT**: `SECRET_KEY` env (default in compose `scale_graduation_project_secret_key`), "
        "`JWT_ALGORITHM` default HS256, `ACCESS_TOKEN_EXPIRE_MINUTES` default 600. Token payload includes "
        "`sub` (email) and `exp` (`create_access_token` in `auth.py`).\n"
        "- **MySQL**: three services; backend only needs network access to each DSN host name as "
        "defined in compose (`main_db`, `challenge_db_sqli`, `challenge_db_csrf`)."
    )
    blank()

    # Section 3 Auth
    w("## 3. Authentication and Authorization")
    w("### 3.1 Registration Flow")
    w(
        "`POST /api/auth/register` accepts `schemas.UserCreate`. If email exists → 400. Self-registration "
        "as `admin` is rejected (403). `crud.create_user` hashes password with passlib bcrypt and sets "
        "`is_approved` per business rules in `crud` (instructors may start unapproved — see `models.User` "
        "comments). Returns `schemas.User`."
    )
    w("### 3.2 Login Flow")
    w(
        "Normal path: `POST /api/auth/login` with `LoginAttempt` (`username` email, `password`). Loads "
        "user by email; verifies bcrypt. Unapproved instructors receive 403. On success, JWT encodes "
        "`sub`=email and role from DB; response includes `access_token`, `token_type` bearer, and user "
        "fields; `response.set_cookie` may set HttpOnly cookie when implemented in the same handler "
        "(see `auth.py` continuation). Frontend stores token/role/id/email in `sessionStorage`."
    )
    w(
        "**Broken-auth challenge**: query param `challenge=broken-auth` with `ENABLE_BROKEN_AUTH_CHALLENGE` "
        "uses **in-memory SQLite** and a **string-interpolated** query `SELECT * FROM users WHERE email = "
        "'{username}' AND password = '{password}'` — intentional SQL injection teaching surface. Event "
        "`CHALLENGE_SQLI` is logged with metadata describing bypass. This path is separate from MySQL "
        "credential verification."
    )
    w("### 3.3 Role-Based Access Control")
    w(
        "| Role | Registration | Approval | Typical UI | Notes |\n"
        "|------|--------------|----------|------------|-------|\n"
        "| user (student) | self-serve | default approved | `/home`, labs, `/quiz` | `require_role('user')` for dynamic quiz |\n"
        "| instructor | self-serve | may require admin approval | `/instructor/*` | `require_role('instructor','admin')` |\n"
        "| admin | blocked from public register; `POST /api/auth/admin/create-admin` | approved | `/admin/*` | Full user management |"
    )
    w(
        "`require_role` (`auth.py`) normalizes `student`→`user` and enforces membership; otherwise 403."
    )
    w("### 3.4 Token Validation")
    w(
        "`get_current_user` decodes JWT with `SECRET_KEY` and `ALGORITHM`; requires `sub` email; loads "
        "`User` row; missing/invalid → 401."
    )
    w("### 3.5 Tab Isolation")
    w(
        "Auth tokens live in **sessionStorage**, so each **browser tab** has an isolated session. This "
        "supports instructors testing multiple roles simultaneously."
    )
    w("### 3.6 Logout")
    w(
        "`POST /api/auth/logout` clears auth cookie (see handler body in `auth.py`). Frontend should "
        "clear `sessionStorage` keys on logout when wired in the UI."
    )
    blank()

    # Section 4 - challenges table
    w("## 4. Challenge System")
    w("### 4.1 Challenge Overview")
    w(
        "| ID | Slug | Type | Attack surface | Fix endpoint | Tutorial note |\n"
        "|----|------|------|----------------|--------------|---------------|\n"
        "| 1 | sql-injection | SQLi | `POST /api/challenges/vulnerable-login` | `POST /api/challenges/submit-fix` | `/challenges/1/tutorial` |\n"
        "| 2 | xss | XSS | XSS comments API | `submit-fix-xss` | `/challenges/2/tutorial` |\n"
        "| 3 | csrf | CSRF | `csrf/*` | `submit-fix-csrf` | `/challenges/3/tutorial` |\n"
        "| 4 | command-injection | Command | `POST /api/challenges/ping` | `submit-fix-command-injection` | `/challenges/4/:tab` |\n"
        "| 5 | broken-auth | Auth | `POST /api/auth/login?challenge=broken-auth` | `submit-fix-auth` | UI → `/under-construction` |\n"
        "| 6 | security-misc | Misconfig | `misconfig` routes | `submit-fix-misc` | UI → `/under-construction` |\n"
        "| 7 | insecure-storage | Storage | `storage/register`, `storage/dump` | `submit-fix-storage` | `/challenges/7/:tab` |\n"
        "| 8 | directory-traversal | Path | `GET /api/challenges/traversal/read` | `submit-fix-traversal` | `/challenges/8/:tab` |\n"
        "| 9 | xxe | XXE | `POST /api/challenges/xxe/parse` | `submit-fix-xxe` | `/challenges/9/:tab` |\n"
        "| 10 | redirect | Redirect | `GET /api/challenges/redirect` | `submit-fix-redirect` | `/challenges/10/:tab` |"
    )
    w(
        "### 4.2–4.1 Per-challenge behaviour is implemented in `backend/app/api/challenges.py` and the "
        "matching `challenge-*` directories. Attack pages call the listed endpoints; fix pages POST "
        "Python source to the corresponding `submit-fix*` handler which calls `_verify_fix_improvement`."
    )
    w("### 4.3 Sandbox Fix Validation")
    w(
        "`run_in_sandbox_detailed` (`sandbox_runner.py`): validates `challenge_dir` ∈ `ALLOWED_CHALLENGE_DIRS`, "
        "enforces `SANDBOX_MAX_CODE_CHARS` (default 200000), copies `/app/challenges/<dir>` to a temp "
        "directory, overwrites `app.py`, writes inline Dockerfile (Python 3.9-slim, bash, pip install, "
        "CRLF fix for `run_tests.sh`, `CMD bash run_tests.sh`), builds image, runs container on "
        "`network=scale_net` with `mem_limit=256m`, `cpu_quota=50000`, `pids_limit=128`, waits up to "
        "`SANDBOX_RUN_TIMEOUT` (default 25s). Parses unittest summary via regex (`Ran N tests`, "
        "`FAILED (failures=, errors=)`). Success: exit code 0 and zero failures/errors. Returns dict with "
        "`success`, `logs`, `tests_run`, `failures`, `errors`."
    )
    w(
        "`_verify_fix_improvement` compares **failure+error counts** before/after (variable names "
        "`before_vulnerabilities`/`after_vulnerabilities` in API responses refer to these counts, not "
        "CVE tallies). `improvement_score` is 100 if both before and after are zero; else proportional "
        "reduction. On fix success, `generate_code_diff` builds annotated diff lines for `ResultModal`."
    )
    w("### 4.4 Code Diff Generation")
    w(
        "`generate_code_diff(original_code, fixed_code, challenge_slug)` runs `difflib.unified_diff`, "
        "skips `---`/`+++` lines, parses hunks with `@@` regex, emits list of dicts with `type` "
        "`removed|added|context`, line numbers, `content`, and optional `annotation` from "
        "`DIFF_ANNOTATIONS` when a line contains a matching `pattern` for the slug (see `sandbox_runner.py`)."
    )
    w("### 4.5 CodeDiffViewer / ResultModal")
    w(
        "`CodeDiffViewer.tsx` accepts `diff: DiffLine[]`. If empty, renders **null**. Otherwise renders a "
        "four-column table (left line numbers + removed/context, right line numbers + added/context). "
        "Removed lines tinted red, added green. **?** icon on annotated lines toggles tooltip on hover. "
        "`ResultModal` shows success/failure header, embeds `CodeDiffViewer` when `isSuccess && codeDiff.length`, "
        "shows verification numbers, and collapsible logs."
    )
    w("### 4.6 Hint System")
    w(
        "`_HINTS` maps `challenge_id` strings (`csrf`, `broken-auth`, `security-misc`, `directory-traversal`, "
        "`xxe`, `insecure-storage`) to levelled hints. `GET /api/challenges/hints?challenge_id=` returns "
        "`HintEntry` list with progressive unlock based on `challenge_state.hints_used`. "
        "`POST /api/challenges/hints/use` increments hints and recalculates learning progress."
    )
    w("### 4.7 Progress Tracking")
    w(
        "`UserProgress` rows are created when a fix succeeds (handlers in `challenges.py`). "
        "`challenge_id` stores slug strings. `recalculate_learning_progress` aggregates distinct "
        "completions, quiz accuracy from `user_answers`, average quiz time from `quiz_attempts`, radar "
        "from `SKILL_BUCKETS`, streak from distinct completion dates, and writes `user_learning_progress`."
    )
    blank()

    # 5 Scanner
    w("## 5. Project Scanner")
    w("### 5.1 Overview")
    w(
        "Static analysis walks extracted project files with extensions allowed in `scan_project_files`; "
        "each file passes through `scan_file_for_vulnerabilities_detailed` (regex rules + CSRF heuristic)."
    )
    w("### 5.2 Upload and Extraction")
    w(
        "`POST /api/project/upload` accepts `.zip` only, max 50MB. `_resolve_storage_root()` chooses "
        "`PROJECT_STORAGE_ROOT` env, else walks parents to find repo root containing `backend`+`frontend`, "
        "else `/app` in container, else cwd. Saves under `uploads/projects/`, extracts to "
        "`uploads/extracted_projects/<project_id>` with `extract_zip` safeguards."
    )
    w("### 5.3 Detection Rules")
    w("See verbatim `scanner/rules.py` in Appendix F.")
    w("### 5.4 Scoring")
    w(
        "`calculate_risk` (`scorer.py`): sums severity weights High=5, Medium=3, Low=1; maps total to "
        "risk_level: ≤10 Low, ≤20 Medium, else High. Returns `total_score`, `risk_level`, `breakdown`."
    )
    w("### 5.5 Scan Result Structure")
    w(
        "`scan_project_for_vulnerabilities` returns an object persisted as JSON in `scan_history.vuln_summary` "
        "(plus API returns risk separately):\n"
        "- `total_vulnerabilities`: int, length of enhanced findings list.\n"
        "- `findings`: array of objects with `file`, `line`, `vulnerability_type`, `type`, `severity`, "
        "`code_snippet`, `code`, and after `attach_fixes`: `fix` with `explanation`, `recommendation`, `example`.\n"
        "- `summary`: map of vulnerability type → count.\n"
        "- `message`: human-readable scan summary string.\n"
        "- `debug`: `files_scanned`, `files_with_matches`, `file_details[]`, `file_errors[]`, "
        "`root_used_for_scan`, optional `extracted_file_count`."
    )
    w("### 5.6 AI-Powered Scan")
    w(
        "`POST /api/project/scan/ai` runs the same pipeline as `/project/scan` then calls AI mentor logic "
        "to enrich a subset of findings (see `projects.py` implementation for limits and OpenAI usage)."
    )
    blank()

    # 6 Report
    w("## 6. Penetration Test Report Generation (Student PDF)")
    w("### 6.1 Overview")
    w(
        "`GET /api/report/pdf` builds a multi-page ReportLab PDF summarizing latest owned scan, completed "
        "challenges, quiz attempts, and fix-related security log entries."
    )
    w("### 6.2 Endpoint Behaviour")
    w(
        "Auth: `Depends(get_current_user)`. Step 1: latest `ScanHistory` joined to `Project` where "
        "`owner_id` matches user — if none, **404** `No scan found`. Step 2: `UserProgress` rows; "
        "`ChallengeState` for hints/time; challenge titles from `challenges` table via slugify of title. "
        "Step 3: all `QuizAttempt` rows for averages. Step 4: `SecurityLog` rows for user with "
        "`context_type=='challenge'` and `event_type` ILIKE `%fix%`. Step 5: canvas pages — cover, "
        "executive summary with styled table, vulnerability inventory (severity colours), remediation "
        "evidence with `REMEDIATION_DESCRIPTIONS`, learning metrics table. Response: `Response` with "
        "`application/pdf` and `Content-Disposition: attachment; filename=pentest_report_<safe_email>_<YYYYMMDD>.pdf`."
    )
    w("### 6.3–6.4 Helpers")
    w(
        "`_flatten_vulnerability_summary` prefers `findings` array; else expands `vulnerability_counts` or "
        "legacy int map. `_derive_risk_level` from severities. `_fmt_date`, `_fmt_duration`, `_safe_json_loads`, "
        "`_slugify_text`, `_prettify_slug`, `_wrap_lines`, `_draw_wrapped` support PDF layout."
    )
    w("### 6.5 Frontend Download")
    w(
        "`DashboardHomePage` triggers `GET /api/report/pdf` with blob response, object URL, and `<a download>`; "
        "handles loading/error state (see component implementation)."
    )
    blank()

    # 7 Quiz
    w("## 7. Quiz System")
    w("### 7.1 Two Quiz Systems")
    w(
        "**Bank quiz** — prefix `/api/quizzes`: CRUD on `questions`, assignments, `POST /take`, submit answer, "
        "submit attempt, list attempts, instructor manage endpoints, `generate-ai-preview` to ai_service.\n"
        "**Dynamic quiz** — prefix `/api/quiz`: `POST /generate` uses `require_role('user')` (students). "
        "`GET`/`POST /manage` use `require_role('admin','instructor')` for question bank maintenance "
        "parallel to `/api/quizzes`."
    )
    w("### 7.2 Static Quiz Bank")
    w(
        "Tables `questions`, `question_options`. `POST /take` filters topics and samples questions. "
        "Submissions update `user_answers` and `quiz_attempts`."
    )
    w("### 7.3 Dynamic AI Quiz")
    w(
        "`quiz_dynamic.py` constructs MCQ-like objects from client-provided findings (see `_build_question_set` "
        "in file)."
    )
    w("### 7.4 Quiz Progress")
    w(
        "`recalculate_learning_progress` uses `user_answers` for accuracy and `quiz_attempts` for avg time."
    )
    blank()

    # 8 Learning
    w("## 8. Learning Progress and Analytics")
    w(
        "`build_learning_progress_payload` returns vulnerabilities solved (capped at `TOTAL_CHALLENGES=10`), "
        "failed attempts, accuracy, avg_time, strongest/weakest category from `compute_skills_scores`, "
        "level from `_determine_level`, streak_days, learning_speed, retention_score, skills map, "
        "`skills_radar` array, and `recommendations` from `get_learning_recommendations`."
    )
    w(
        "**Radar buckets** (`SKILL_BUCKETS`): SQL Injection → sql-injection, broken-auth; XSS → xss; "
        "CSRF → csrf, redirect; Traversal → directory-traversal, command-injection; XXE → xxe; Storage → "
        "insecure-storage, security-misc. Each bucket score = round(100 * solved_slugs / len(slugs))."
    )
    w(
        "**Streak** (`recalculate_learning_progress`): sorts distinct completion dates descending, walks "
        "list increasing streak while dates are consecutive calendar days."
    )
    w(
        "**learning_speed** = `(solved / max(avg_time,1))*100` when solved>0 else 0. **retention_score** "
        "mixes accuracy, capped streak, and failed-answer penalty per formula in source."
    )
    w("### 8.2 Student Dashboard")
    w(
        "`DashboardHomePage` loads `/api/stats/progress/me`, `/api/challenges/progress`, `/api/quizzes/attempts`, "
        "and report download. Displays radar from `skills_radar`, vulnerability counts, XP-style metrics "
        "computed client-side from progress (not persisted as XP)."
    )
    w("### 8.3 Instructor Dashboard")
    w(
        "`GET /api/stats/instructor/dashboard`: student list metrics, class completion ratio, per-bucket "
        "aggregates. `GET /api/instructor/user/{id}/analytics` returns same payload as student. "
        "`POST /api/instructor/user/{id}/reset-progress` wipes progress-related tables for user."
    )
    w("### 8.4 Admin Dashboard")
    w(
        "`GET /api/stats/admin/dashboard`: user counts, `fixed_vulns` = **total** `UserProgress` row count "
        "(counts completions, not unique vulns), `challenge_usage` built from progress counts and "
        "challenge-scoped security events (see `stats.py` for exact per-challenge attempt/success logic)."
    )
    blank()

    # 9 Security logs
    w("## 9. Security Event Logging")
    w(
        "`log_security_event` (`security_logger.py`) persists to `security_logs` with normalized "
        "`context_type` (`real` vs `challenge`). Admin `GET /api/security/logs` supports filters; "
        "`GET /api/security/logs/stats` returns aggregates."
    )
    blank()

    # 10 Messages
    w("## 10. Messaging System")
    w(
        "`messages` table; `GET /api/messages/unread-count`, `GET /api/messages/with/{user_id}`, "
        "`POST /api/messages/send`, `GET /api/messages/contacts`. `MainLayout` polls unread count on load "
        "(see component)."
    )
    blank()

    # 11 AI
    w("## 11. AI Services")
    w(
        "**ai_service** container port 8001. **AI mentor** `POST /api/ai/analyze-code` sends code snippets "
        "for structured feedback. **Quiz** `POST /api/quizzes/generate-ai-preview` proxies to "
        "`AI_SERVICE_URL` (default `http://ai_service:8001/generate`). **Dynamic quiz** uses "
        "`POST /api/quiz/generate` with scan JSON from frontend."
    )
    blank()

    w("## 11a. CTF Competitive Mode (not implemented in backend)")
    w(
        "A repository-wide search for `ctf`, `CTF`, `ctf_sessions`, `ctf_leaderboard`, or `/api/ctf` "
        "returns **no matches** in `backend/` or `frontend/`. There are **no** database models, API "
        "routes, flag generation, timers, or leaderboards for a dedicated capture-the-flag mode. Any "
        "graduation narrative that refers to CTF features should be treated as **out of scope** for "
        "this codebase unless implemented in a future revision. The **Red vs Blue** subsystem "
        "(§11b) provides competitive team play using the same ten lab identifiers without HMAC flags."
    )
    blank()

    w("## 11b. Red vs Blue Team Mode (instructor-led)")
    w(
        "The **primary** Red vs Blue implementation is `backend/app/api/red_blue.py`, mounted at "
        "prefix `/api/redblue` in `main.py`. It uses `teams`, `team_members`, `game_challenges`, "
        "`red_team_actions`, and `blue_team_fixes` from `models.py`. Lab challenges are identified "
        "by integers **1–10** mapped to the same slugs as the solo labs (`LAB_CHALLENGE_SLUGS`). "
        "Creating a game (`POST /api/redblue/game/create`, instructor or admin) validates user IDs, "
        "rejects overlap between red and blue rosters, sets any prior **active** game for that lab "
        "to **inactive**, creates two `Team` rows, `TeamMember` rows, and a `GameChallenge` with "
        "synthetic `project_id` `redblue-{hex}` and `lab_challenge_id` set to the chosen lab. "
        "Red score counts `RedTeamAction` rows for the game id with `status` **confirmed** or **NULL**; "
        "blue score counts `BlueTeamFix` rows with `fixed=True`. Attack logging (`POST .../attack`) "
        "requires membership on the red team; fix submission (`POST .../fix`) runs `_verify_fix_improvement` "
        "from `challenges.py` against `/app/challenges/challenge-{slug}` inside the backend container. "
        "Polling uses `GET /api/redblue/game/{game_id}/attacks?since_id=` returning rows with `id` "
        "greater than `since_id`. Instructors end games via `POST /api/redblue/game/{game_id}/end` "
        "(status **completed**). Students list participations via `GET /api/redblue/my-games`."
    )
    w(
        "A **separate** mini-game API exists under **`/api/challenge`** (singular) from "
        "`game_challenge.py` (`start`, `red/attack`, `blue/fix`, `leaderboard`, `status`, `hint`). "
        "That router predates the instructor-led schema and uses overlapping table names; both "
        "systems are registered. Frontend pages `RedBlueGamePage`, `RedBlueCreatePage`, and "
        "`RedBlueMyGamesPage` call the **`/api/redblue`** routes (verify in each file’s axios paths)."
    )
    blank()

    # 12 API reference - table
    w("## 12. Complete API Reference")
    routes: list[tuple[str, str, str, str, str]] = [
        ("GET", "/", "No", "Public", "API welcome JSON"),
        ("POST", "/api/auth/register", "No", "Public", "Create user"),
        ("POST", "/api/auth/login", "No", "Public", "JWT login; optional challenge mode"),
        ("POST", "/api/auth/logout", "Yes", "Any", "Clear cookie"),
        ("GET", "/api/auth/users", "Yes", "admin", "List users"),
        ("GET", "/api/auth/me", "Yes", "Any", "Current user profile"),
        ("GET", "/api/auth/admin/pending", "Yes", "admin", "Pending instructors"),
        ("POST", "/api/auth/admin/approve/{user_id}", "Yes", "admin", "Approve user"),
        ("POST", "/api/auth/admin/create-admin", "Yes", "admin", "Create admin user"),
        ("DELETE", "/api/auth/admin/users/{user_id}", "Yes", "admin", "Delete user"),
        ("PUT", "/api/auth/admin/users/{user_id}/role", "Yes", "admin", "Change role"),
        ("GET", "/api/quizzes/topics", "Yes", "Any", "List quiz topics"),
        ("POST", "/api/quizzes/questions", "Yes", "instructor/admin", "Create question"),
        ("GET", "/api/quizzes/questions", "Yes", "Any", "List questions"),
        ("PUT", "/api/quizzes/questions/{q_id}", "Yes", "instructor/admin", "Update question"),
        ("DELETE", "/api/quizzes/questions", "Yes", "instructor/admin", "Delete all questions"),
        ("DELETE", "/api/quizzes/questions/{q_id}", "Yes", "instructor/admin", "Delete one question"),
        ("POST", "/api/quizzes/generate-ai-preview", "Yes", "instructor/admin", "AI question preview"),
        ("POST", "/api/quizzes/assignments", "Yes", "instructor/admin", "Create assignment"),
        ("GET", "/api/quizzes/assignments/instructor", "Yes", "instructor/admin", "Instructor assignments"),
        ("DELETE", "/api/quizzes/assignments/{id}", "Yes", "instructor/admin", "Delete assignment"),
        ("GET", "/api/quizzes/assignments/student", "Yes", "user+", "Student assignments"),
        ("GET", "/api/quizzes/assignments/{id}/take", "Yes", "user+", "Questions for assignment"),
        ("POST", "/api/quizzes/take", "Yes", "user+", "Random practice quiz"),
        ("POST", "/api/quizzes/submit-answer", "Yes", "user+", "Record answer"),
        ("POST", "/api/quizzes/submit-attempt", "Yes", "user+", "Record attempt"),
        ("GET", "/api/quizzes/attempts", "Yes", "user+", "Past attempts"),
        ("GET", "/api/quizzes/manage", "Yes", "instructor/admin", "Quiz manage view"),
        ("POST", "/api/quizzes/manage", "Yes", "instructor/admin", "Quiz manage action"),
        ("POST", "/api/challenges/vulnerable-login", "No", "Public", "SQLi lab login"),
        ("GET", "/api/challenges/xss/comments", "Yes", "Any", "List XSS comments"),
        ("POST", "/api/challenges/xss/comments", "Yes", "Any", "Create XSS comment"),
        ("DELETE", "/api/challenges/xss/comments", "Yes", "Any", "Delete XSS comments"),
        ("POST", "/api/challenges/csrf/reset", "Yes", "Any", "Reset CSRF DB"),
        ("GET", "/api/challenges/csrf/accounts", "Yes", "Any", "List CSRF accounts"),
        ("POST", "/api/challenges/csrf/transfer", "Yes", "Any", "CSRF transfer form"),
        ("POST", "/api/challenges/submit-fix", "Yes", "Any", "Fix SQLi lab"),
        ("POST", "/api/challenges/submit-fix-xss", "Yes", "Any", "Fix XSS lab"),
        ("POST", "/api/challenges/submit-fix-csrf", "Yes", "Any", "Fix CSRF lab"),
        ("POST", "/api/challenges/ping", "Yes", "Any", "Command injection ping"),
        ("POST", "/api/challenges/submit-fix-command-injection", "Yes", "Any", "Fix command lab"),
        ("POST", "/api/challenges/submit-fix-auth", "Yes", "Any", "Fix broken auth lab"),
        ("POST", "/api/challenges/submit-fix-misc", "Yes", "Any", "Fix misc lab"),
        ("GET", "/api/challenges/redirect", "Yes", "Any", "Open redirect"),
        ("POST", "/api/challenges/submit-fix-redirect", "Yes", "Any", "Fix redirect lab"),
        ("POST", "/api/challenges/submit-fix-traversal", "Yes", "Any", "Fix traversal lab"),
        ("POST", "/api/challenges/submit-fix-xxe", "Yes", "Any", "Fix XXE lab"),
        ("POST", "/api/challenges/submit-fix-storage", "Yes", "Any", "Fix storage lab"),
        ("GET", "/api/challenges/traversal/read", "Yes", "Any", "Read file traversal lab"),
        ("POST", "/api/challenges/xxe/parse", "Yes", "Any", "XXE parse lab"),
        ("POST", "/api/challenges/storage/register", "Yes", "Any", "Register insecure storage"),
        ("GET", "/api/challenges/storage/dump", "Yes", "Any", "Dump insecure storage"),
        ("GET", "/api/challenges/progress", "Yes", "Any", "User progress list"),
        ("POST", "/api/challenges/mark-attack-complete", "Yes", "Any", "Mark attack done"),
        ("GET", "/api/challenges/state", "Yes", "Any", "Challenge state"),
        ("POST", "/api/challenges/state/update", "Yes", "Any", "Update challenge state"),
        ("GET", "/api/challenges/hints", "Yes", "Any", "Hints"),
        ("POST", "/api/challenges/hints/use", "Yes", "Any", "Use hint"),
        ("GET", "/api/challenges/replay/{challenge_slug}", "Yes", "Any", "Attack replay JSON; ?sample=true"),
        ("GET", "/api/stats/admin/dashboard", "Yes", "admin", "Admin metrics"),
        ("GET", "/api/stats/instructor/dashboard", "Yes", "instructor/admin", "Instructor metrics"),
        ("GET", "/api/stats/progress/me", "Yes", "Any", "Learning progress payload"),
        ("GET", "/api/messages/unread-count", "Yes", "Any", "Unread messages count"),
        ("GET", "/api/messages/with/{user_id}", "Yes", "Any", "Thread with user"),
        ("POST", "/api/messages/send", "Yes", "Any", "Send message"),
        ("GET", "/api/messages/contacts", "Yes", "Any", "Message contacts"),
        ("POST", "/api/project/upload", "Yes", "Any", "Upload zip"),
        ("GET", "/api/project/files", "Yes", "Any", "List project files"),
        ("POST", "/api/project/scan", "Yes", "Any", "Run scan"),
        ("GET", "/api/project/report", "Yes", "Any", "JSON security report"),
        ("GET", "/api/project/report/pdf", "Yes", "Any", "Project PDF report"),
        ("POST", "/api/project/scan/ai", "Yes", "Any", "Scan with AI enrichment"),
        ("GET", "/api/user/projects", "Yes", "Any", "List user projects"),
        ("GET", "/api/project/analytics", "Yes", "Any", "Project analytics"),
        ("GET", "/api/project/{project_id}", "Yes", "Any", "Project detail"),
        ("GET", "/api/project/{project_id}/dependencies", "Yes", "Any", "dependency_scan slice of vuln_summary"),
        ("GET", "/api/admin/overview", "Yes", "admin", "Admin project overview"),
        ("POST", "/api/project/analyze-structure", "Yes", "Any", "Structure analyzer"),
        ("POST", "/api/challenge/start", "Yes", "Any", "Red/blue game start"),
        ("POST", "/api/challenge/red/attack", "Yes", "Any", "Red team attack"),
        ("POST", "/api/challenge/blue/fix", "Yes", "Any", "Blue team fix"),
        ("GET", "/api/challenge/leaderboard", "Yes", "Any", "Game leaderboard"),
        ("GET", "/api/challenge/status", "Yes", "Any", "Game status"),
        ("POST", "/api/challenge/hint", "Yes", "Any", "Game hint"),
        ("POST", "/api/calc/interest", "Yes", "Any", "Misconfig calculator"),
        ("GET", "/api/admin/config", "Yes", "Any", "Misconfig exposed config"),
        ("POST", "/api/ai/analyze-code", "Yes", "Any", "AI mentor analysis"),
        ("POST", "/api/attack/simulate", "Yes", "Any", "Attack simulator"),
        ("GET", "/api/security/logs", "Yes", "admin", "Security logs"),
        ("GET", "/api/security/logs/stats", "Yes", "admin", "Security log stats"),
        ("POST", "/api/quiz/generate", "Yes", "user (student)", "Dynamic quiz from findings"),
        ("GET", "/api/quiz/manage", "Yes", "admin, instructor", "Dynamic quiz manage GET"),
        ("POST", "/api/quiz/manage", "Yes", "admin, instructor", "Dynamic quiz manage POST"),
        ("GET", "/api/instructor/user/{user_id}/analytics", "Yes", "instructor/admin", "Student analytics"),
        ("POST", "/api/instructor/user/{user_id}/reset-progress", "Yes", "instructor/admin", "Reset student"),
        ("GET", "/api/report/pdf", "Yes", "Any", "Student pentest PDF"),
        ("POST", "/api/redblue/game/create", "Yes", "instructor, admin", "Create Red vs Blue game (labs 1–10)"),
        ("GET", "/api/redblue/game/{game_id}", "Yes", "Any", "Game state, teams, actions, fixes"),
        ("GET", "/api/redblue/game/{game_id}/attacks", "Yes", "Any", "Poll red actions since_id"),
        ("POST", "/api/redblue/game/{game_id}/attack", "Yes", "Any", "Red team logs attack payload"),
        ("POST", "/api/redblue/game/{game_id}/fix", "Yes", "Any", "Blue team sandbox fix"),
        ("GET", "/api/redblue/my-games", "Yes", "Any", "Current user’s Red vs Blue games"),
        ("GET", "/api/redblue/games", "Yes", "instructor, admin", "List all games"),
        ("POST", "/api/redblue/game/{game_id}/end", "Yes", "instructor, admin", "End game; final scores"),
    ]
    w("| Method | Path | Auth | Roles | Description |")
    w("|--------|------|------|-------|-------------|")
    for m, p, a, r, d in routes:
        w(f"| {m} | `{p}` | {a} | {r} | {d} |")
    blank()

    w("### Detailed route specifications (selected)")
    detailed = """
### Route: POST /api/auth/login
- **Request body:** `{ "username": string (email), "password": string }`
- **Response (normal):** JWT access token payload in JSON per `auth.py`; may set cookie.
- **Auth required:** No
- **Logic:** Resolves user; bcrypt verify; rejects unapproved instructors; creates JWT with `sub` and expiry; logs security events for success/failure with appropriate `context_type` when challenge query absent.
- **Broken-auth branch:** When `challenge=broken-auth` and enabled, uses SQLite in-memory DB and vulnerable string-built SELECT; returns JSON including `bypass_success` and issues token if row returned.
- **Errors:** 401 invalid credentials; 403 pending instructor; 400 register issues.

### Route: POST /api/auth/register
- **Body:** UserCreate schema (email, password, role among allowed).
- **Auth:** No
- **Logic:** Rejects duplicate email; rejects admin self-signup; creates hashed user via crud.

### Route: POST /api/project/upload
- **Auth:** Bearer
- **Logic:** Validates zip and size; computes storage root; writes file; extracts; creates `Project` row; returns project metadata.

### Route: POST /api/project/scan
- **Query:** `project_id`
- **Auth:** Bearer; owner check via `_assert_project_access`
- **Logic:** Runs `scan_project_for_vulnerabilities`; `calculate_risk`; inserts `ScanHistory` with `vuln_summary=json.dumps(result)`; updates `Project`; `recalculate_learning_progress`; logs `PROJECT_SCAN`.

### Route: POST /api/challenges/submit-fix (and sibling submit-fix-*)
- **Auth:** Bearer
- **Logic:** Reads submitted code body; calls `_verify_fix_improvement`; on success persists progress, state, logs sandbox; returns verification + `code_diff`.

### Route: GET /api/challenges/hints
- **Query:** `challenge_id`
- **Auth:** Bearer
- **Logic:** Returns progressive hints from `_HINTS` capped by `hints_used`.

### Route: GET /api/stats/progress/me
- **Auth:** Bearer
- **Logic:** Returns `build_learning_progress_payload` for current user id.

### Route: GET /api/report/pdf
- **Auth:** Bearer
- **Logic:** As §6; 404 if no scan history for owned project.

### Route: POST /api/quiz/generate
- **Auth:** `require_role("user")` — students only
- **Logic:** Builds dynamic MCQ from posted scan findings JSON.

### Route: POST /api/quizzes/take
- **Auth:** Bearer
- **Logic:** Samples questions from DB by topic/difficulty/count.

### Route: GET /api/security/logs
- **Auth:** admin
- **Logic:** Paginates and filters `security_logs` per query params in `security_logs.py`.

### Route: POST /api/instructor/user/{user_id}/reset-progress
- **Auth:** instructor/admin
- **Logic:** Deletes progress-related rows for target user (see `instructor.py`).

### Route: GET /api/stats/admin/dashboard
- **Auth:** admin
- **Logic:** Aggregates users, progress counts, challenge usage with event mapping as implemented in `stats.py`.

### Route: POST /api/ai/analyze-code
- **Auth:** Bearer
- **Logic:** Proxies code to AI pipeline; returns structured mentor response schema.

### Route: GET /api/challenges/replay/{challenge_slug}
- **Query:** `sample` optional boolean — when true, allows replay without completing the attack.
- **Auth:** Bearer
- **Logic:** Loads `ATTACK_REPLAYS` steps for the slug; may require attack completion unless `sample=true`; 404 if no replay.

### Route: GET /api/project/{project_id}/dependencies
- **Auth:** Bearer; owner access via `_assert_project_access`
- **Logic:** Reads latest `scan_history.vuln_summary` JSON; returns the `dependency_scan` object only; 404 if no scan.

### Route: POST /api/redblue/game/create
- **Auth:** instructor or admin
- **Body:** `RedBlueGameCreate` — team names, member id lists, `challenge_id` 1–10.
- **Logic:** See §11b; creates teams, members, `GameChallenge`, logs `redblue_game_created`.

### Route: GET /api/redblue/my-games
- **Auth:** Bearer
- **Logic:** Finds `TeamMember` rows for current user, joins to `GameChallenge`, returns scores and team labels.

### Route: GET /api/redblue/game/{game_id}/attacks
- **Query:** `since_id` default 0
- **Auth:** Bearer
- **Logic:** Returns `RedTeamAction` rows with id > since_id ordered ascending for polling.

### Route: POST /api/redblue/game/{game_id}/fix
- **Auth:** Bearer; must be blue team member
- **Body:** `RedBlueFixBody` with `submitted_code`
- **Logic:** Calls `_verify_fix_improvement`; persists `BlueTeamFix`; returns fixed flag and improvement_score.
"""
    w(detailed.strip())
    blank()

    # 13 Models - condensed + pointer to appendix
    w("## 13. Data Models Reference")
    w(
        "Each SQLAlchemy model in `backend/app/models.py` maps to tables documented below. "
        "Relationships use standard SQLAlchemy `relationship()` where declared."
    )
    w("### Model: User — table `users`")
    w(
        "- `id` Integer PK; `email` String(255) unique indexed; `hashed_password` String(255); "
        "`role` String(50) default `user`; `is_approved` Boolean default True.\n"
        "- Relationships: `answers` → UserAnswer; `progress` → UserProgress; `quiz_attempts` → QuizAttempt.\n"
        "- Used by: authentication, all user-scoped features."
    )
    w("### Model: UserProgress — `user_progress`")
    w(
        "- `id` PK; `user_id` FK users; `challenge_id` String(50); `completed_at` DateTime.\n"
        "- Used by: challenge completion, dashboards, PDF."
    )
    w("### Model: XSSComment — `xss_comments`")
    w("- `id` PK; `author` String(255); `content` Text.")
    w("### Model: Challenge — `challenges`")
    w("- Metadata titles for PDF title map.")
    w("### Model: Question / QuestionOption / UserAnswer / QuizAssignment / QuizAssignmentStudent / QuizAssignmentQuestion / QuizAttempt")
    w("- Quiz bank, assignments (including join tables for students/questions), attempts with score/total/time.")
    w("### Model: CSRFAccount — `csrf_accounts`")
    w("- Legacy table; CSRF lab uses external MySQL via raw SQL.")
    w("### Model: Message — `messages`")
    w("- sender_id, receiver_id, content, created_at, is_read.")
    w("### Model: Project / ScanHistory")
    w("- Project identifiers string PK; scan history stores `vuln_summary` Text JSON.")
    w("### Model: Team / TeamMember / GameChallenge / ChallengeVulnerability / RedTeamAction / BlueTeamFix")
    w("- Red/blue game schema.")
    w("### Model: ChallengeState — `challenge_state`")
    w("- Per-user per-challenge hints, attempts, time, stage.")
    w("### Model: SecurityLog — `security_logs`")
    w("- event_type, severity, payload, endpoint, IP, geo_bucket, user_agent, session_id, correlation_id, context_type, JSON metadata column mapped as `meta_data` in Python (`metadata` in DB), created_at.")
    w("### Model: UserLearningProgress — `user_learning_progress`")
    w("- Aggregated metrics per user unique on user_id.")
    blank()

    # 14 Frontend pages
    w("## 14. Frontend Pages Reference")
    w(
        "All page components live under `frontend/src/pages/`. Routes are defined in `App.tsx`. "
        "Below, each file is listed with its primary route(s) when applicable."
    )
    pages_dir = ROOT / "frontend" / "src" / "pages"
    for p in sorted(pages_dir.glob("*.tsx")):
        w(f"### Page: `{p.name}`")
        w(f"- **File:** `frontend/src/pages/{p.name}`")
        w("- **Role access:** Inherits nearest `ProtectedRoute` (see `App.tsx`).")
        w("- **Purpose:** React page component; inspect file for hooks, API calls, and UI.")
        blank()

    w("## 15. Environment and Configuration")
    w("### 15.1 Environment Variables")
    w(
        "| Name | Default (typical) | Where | Effect if missing |\n"
        "|------|-------------------|-------|---------------------|\n"
        "| DATABASE_URL | mysql+pymysql://user:password@main_db/scale_db | backend | DB connection fails |\n"
        "| SQLI_DATABASE_URL | mysql+pymysql://...@challenge_db_sqli/testdb | challenges | SQLi lab DB errors |\n"
        "| CSRF_DATABASE_URL | mysql+pymysql://...@challenge_db_csrf/csrfdb | challenges | CSRF lab DB errors |\n"
        "| SECRET_KEY | scale_graduation_project_secret_key | auth | JWT signing (insecure default) |\n"
        "| ACCESS_TOKEN_EXPIRE_MINUTES | 600 | auth | Token lifetime |\n"
        "| ENABLE_BROKEN_AUTH_CHALLENGE | true | auth | Disables SQLite challenge branch if false |\n"
        "| SANDBOX_MAX_CODE_CHARS | 200000 | sandbox_runner | Rejects large submissions |\n"
        "| SANDBOX_RUN_TIMEOUT | 25 | sandbox_runner | Container wait timeout |\n"
        "| PROJECT_STORAGE_ROOT | (empty) | projects | Falls back to repo root or /app |\n"
        "| VITE_API_URL | http://localhost:8000 | frontend | API base for axios |\n"
        "| MYSQL_* / SQLI_* / CSRF_* | see compose | mysql services | DB bootstrap |"
    )
    w("### 15.2 Docker Volumes")
    w(
        "- `scale_db_data`: persistent MySQL data for main_db.\n"
        "- Bind mounts: backend source, frontend source, challenge folders, ai_service, db init scripts, docker.sock."
    )
    w("### 15.3 Port Map")
    w(
        "| Service | Internal | External | Client |\n"
        "|---------|----------|----------|--------|\n"
        "| frontend (Vite) | 5173 | 5173 | Browser |\n"
        "| backend | 8000 | 8000 | Browser / axios |\n"
        "| ai_service | 8001 | 8001 | Backend |\n"
        "| main_db | 3306 | 3306 | Host tools |\n"
        "| challenge_db_sqli | 3306 | 3307 | Host tools |\n"
        "| challenge_db_csrf | 3306 | 3308 | Host tools |"
    )
    blank()

    w("## 16. Setup and Deployment Guide")
    w("### 16.1 Prerequisites")
    w("Docker Desktop with Compose support, Git. All language runtimes are provided by images.")
    w("### 16.2 First-Time Setup")
    w(
        "1. Clone repository.\n"
        "2. From project root: `docker compose up --build`.\n"
        "3. Wait for backend healthchecks and `Application startup` / seed completion in logs.\n"
        "4. Open `http://localhost:5173`.\n"
        "5. Default seeded accounts from `seed_db.py`: `admin@scale.edu` / `AdminPass123!`; "
        "`instructor@scale.edu` / `TeachPass123!`."
    )
    w("### 16.3 Development Workflow")
    w(
        "Backend uses `--reload`; frontend uses Vite HMR. Rebuild images when Dockerfile or dependencies change."
    )
    w("### 16.4 Common Issues")
    w(
        "- **DB timing:** startup retries connections; ensure MySQL healthchecks pass.\n"
        "- **Sandbox:** requires Docker socket and `scale_net` network name alignment.\n"
        "- **CORS:** production must extend allowed origins beyond localhost.\n"
        "- **Storage:** set `PROJECT_STORAGE_ROOT` if automatic root detection fails."
    )
    blank()

    w("## 17. Known Limitations and Technical Debt")
    w(
        "1. **Admin dashboard attempt count** uses an estimated formula (e.g. scaling from fix counts) rather than a ground-truth attempt log — see `stats.py`.\n"
        "2. **Dual quiz systems** (`/api/quizzes` vs `/api/quiz`) overlap in purpose; instructors must know which UI calls which API.\n"
        "3. **quiz_assignments** (legacy) uses comma-separated ID strings in Text columns alongside newer normalized tables.\n"
        "4. **XP display** on the student dashboard is computed client-side and is not a persisted authoritative column.\n"
        "5. **Defense level** in the UI may use different thresholds than the backend `level` field from `learning_tracker` — compare `DashboardHomePage` to `build_learning_progress_payload`.\n"
        "6. **`successTypeMap` in `ChallengesListPage`** covers a subset of challenge types for attack-success messaging, not all ten slugs.\n"
        "7. **Tutorial routes** for Broken Authentication and Security Misconfiguration point to `/under-construction` in the challenges list.\n"
        "8. **Dependency scanner** caps concurrent OSV queries (`MAX_DEPS_TO_QUERY = 50` in `dependency_scanner.py`).\n"
        "9. **Red vs Blue fix validation** depends on resolving `/app/challenges/challenge-{slug}` inside the backend container; a misconfigured deployment breaks fixes.\n"
        "10. **Scanner scope** can include platform or unrelated files if the uploaded ZIP structure or extraction root overlaps the analyzer’s walk — regex analysis is path-based, not project-manifest aware.\n"
        "11. **Command injection** lab executes real shell commands on the API host — acceptable only in isolated lab environments.\n"
        "12. **JWT in sessionStorage** is readable to any same-origin script; XSS on any page could exfiltrate tokens.\n"
        "13. **Dual Red vs Blue APIs** (`/api/redblue` vs `/api/challenge`) increase confusion; only the former is used by the new instructor portal pages."
    )
    blank()

    w("## 18. Security Considerations")
    w("### 18.1 Intentional Vulnerabilities")
    w(
        "- Broken-auth challenge SQLite query string building (`auth.py`).\n"
        "- SQLi lab query interpolation (`vulnerable-login`).\n"
        "- Command injection endpoint uses subprocess with shell.\n"
        "- Challenge `app.py` files in repositories are intentionally flawed for sandbox testing."
    )
    w("### 18.2 Platform Controls")
    w("Passwords hashed with bcrypt; RBAC enforced via dependencies; security logging differentiates challenge vs real traffic.")
    w("### 18.3 Production Recommendations")
    w(
        "Rotate secrets; enable TLS; rate limit authentication and file upload; isolate command execution; "
        "remove docker socket from production deployments; use centralized log shipping."
    )
    blank()

    w("## Appendix A — Annotated File Tree (abbreviated)")
    for path in sorted(ROOT.rglob("*")):
        if any(
            x in path.parts
            for x in (
                ".git",
                "node_modules",
                "__pycache__",
                ".venv",
                "dist",
                "build",
            )
        ):
            continue
        if path.is_dir():
            continue
        rel = path.relative_to(ROOT)
        if str(rel).startswith("PROJECT_DOCUMENTATION.md"):
            continue
        w(f"- `{rel.as_posix()}` — project file (see contents in repository).")
    blank()

    w("## Appendix B — Complete Route Map (alphabetical by path)")
    for m, p, _, _, d in sorted(routes, key=lambda x: (x[1], x[0])):
        w(f"- `{m}` `{p}` — {d}")
    blank()

    w("## Appendix C — Glossary")
    glossary = [
        ("Challenge slug", "String identifier for a lab (e.g. `sql-injection`) stored in `user_progress.challenge_id`."),
        ("Sandbox runner", "`sandbox_runner.py` module that builds and runs Docker images for fix validation."),
        ("Fix improvement score", "Percentage derived from unittest failure/error counts before vs after submission."),
        ("context_type", "Field on security logs: `real` vs `challenge` after normalization."),
        ("ScanContext", "React context persisting last scan JSON under `scale.scanData.{user_id}` (or `scale.scanData.guest`) in localStorage."),
        ("vuln_summary", "JSON text on `scan_history` storing scanner output."),
        ("SKILL_BUCKETS", "Map of radar axis names to challenge slug lists in `learning_tracker.py`."),
        ("DiffLine", "Object in code diff: type, line numbers, content, annotation."),
        ("challenge_state", "Row tracking hints used, attempts, time per user/challenge."),
        ("learning_speed", "Metric in `user_learning_progress`: solved over average quiz time scaled."),
        ("retention_score", "Heuristic 0–100 blended metric in `user_learning_progress`."),
        ("streak_days", "Consecutive-day streak approximation from `user_progress` dates."),
    ]
    for term, defin in glossary:
        w(f"- **{term}:** {defin}")
    blank()

    w("## Appendix D — Verbatim configuration and core modules")
    w("## D.1 docker-compose.yml")
    fence("yaml", read("docker-compose.yml"))
    w("## D.2 backend/requirements.txt")
    fence("", read("backend/requirements.txt"))
    w("## D.3 frontend/package.json")
    fence("json", read("frontend/package.json"))
    w("## D.4 backend/app/db/database.py")
    fence("python", read("backend/app/db/database.py"))
    w("## D.5 backend/app/main.py")
    fence("python", read("backend/app/main.py"))
    w("## D.6 backend/app/scanner/rules.py")
    fence("python", read("backend/app/scanner/rules.py"))
    w("## D.7 backend/app/scanner/detector.py")
    fence("python", read("backend/app/scanner/detector.py"))
    w("## D.8 backend/app/scanner/scorer.py")
    fence("python", read("backend/app/scanner/scorer.py"))
    w("## D.9 backend/app/scanner/fixer.py")
    fence("python", read("backend/app/scanner/fixer.py"))
    w("## D.10 backend/app/security/learning_tracker.py")
    fence("python", read("backend/app/security/learning_tracker.py"))
    w("## D.11 backend/app/sandbox_runner.py")
    fence("python", read("backend/app/sandbox_runner.py"))
    w("## D.12 backend/app/api/report.py")
    fence("python", read("backend/app/api/report.py"))
    w("## D.13 backend/app/api/auth.py")
    fence("python", read("backend/app/api/auth.py"))
    w("## D.14 backend/app/security/security_logger.py")
    fence("python", read("backend/app/security/security_logger.py"))
    w("## D.15 backend/app/api/quiz_dynamic.py")
    fence("python", read("backend/app/api/quiz_dynamic.py"))
    w("## D.16 frontend/src/pages/DashboardHomePage.tsx")
    fence("tsx", read("frontend/src/pages/DashboardHomePage.tsx"))
    w("## D.17 frontend/src/components/ProtectedRoute.tsx")
    fence("tsx", read("frontend/src/components/ProtectedRoute.tsx"))
    w("## D.18 frontend/src/context/ScanContext.tsx")
    fence("tsx", read("frontend/src/context/ScanContext.tsx"))
    w("## D.19 backend/app/scanner/dependency_scanner.py")
    fence("python", read("backend/app/scanner/dependency_scanner.py"))

    spans_before_stats = _h2_spans_outside_fences(out)
    stats_section_start = len(out) + 2  # blank + ## Documentation Statistics
    blank()
    w("## Documentation Statistics")
    w(
        "The following table lists every level-2 section (`## ...`) **excluding** lines inside fenced "
        "code blocks, so embedded source files do not create false section boundaries. Sections D.1–D.19 "
        "appear in the table; their bodies live inside fences and are not counted as nested `##` headers."
    )
    w("| Section (##) | Start line | End line | Line count |")
    w("|----------------|------------|----------|------------|")
    for name, start, end, cnt in spans_before_stats:
        safe = name.replace("|", "\\|")
        w(f"| {safe} | {start} | {end} | {cnt} |")
    w(f"- **Word count (approximate, whitespace-split):** _see generator stdout_")
    w(f"- **`## Documentation Statistics` starts at line:** {stats_section_start}")
    w(f"- **Total lines in file:** _see generator stdout_")
    return out


def main() -> None:
    doc_lines = lines()
    text = "\n".join(doc_lines) + "\n"
    words = len(text.split())
    n_lines = len(text.splitlines())
    lines_list = text.splitlines()
    for i, line in enumerate(lines_list):
        if "_see generator stdout_" in line:
            if "Word count" in line:
                lines_list[i] = line.replace("_see generator stdout_", str(words))
            elif "Total lines" in line:
                lines_list[i] = line.replace("_see generator stdout_", str(n_lines))
    text = "\n".join(lines_list) + "\n"
    out_path = ROOT / "PROJECT_DOCUMENTATION.md"
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path} ({n_lines} lines, {words} words)")


if __name__ == "__main__":
    main()
