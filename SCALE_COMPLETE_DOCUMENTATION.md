# SCALE — Security Challenge and Learning Environment
## Complete System Documentation
### Version: Final Release | Graduation Project Submission
### Date: May 2026

---

## Abstract

The Security Challenge and Learning Environment (SCALE) is a web-based educational platform that integrates guided vulnerability laboratories, dual-engine static analysis (Semgrep SAST merged with legacy regex rules), dependency analysis of uploaded projects, competitive Red versus Blue exercises, instructor-assigned timed lab tasks, formal quiz assignments with due dates and time limits, adaptive "common mistakes" quizzes derived from prior wrong answers, and a **leaderboard system** surfacing ranked challenge completion and Red versus Blue game scores. The student dashboard provides gamified feedback including a three-tier Defense Level (Beginner / Intermediate / Advanced) derived from backend learning analytics, a client-side XP-style score combining lab completions and quiz averages, per-lab Challenge Mastery bars, and narrative "XP gained" values on attack-success screens. The platform distinguishes persisted metrics (MySQL via `user_learning_progress`, `UserProgress`, `QuizAttempt`) from display-only figures that are not stored as currency.

SCALE addresses the gap between passive lecture delivery and unstructured capture-the-flag platforms by providing instructor dashboards, role-based access control, repeatable sandbox validation of remediated code, and portfolio-grade reporting. The architecture centers on a FastAPI backend exposing REST endpoints under `/api`, a React 18 single-page application built with Vite 5 and TypeScript, three MySQL 8.0 instances for the primary application database, the SQL injection challenge database, and the CSRF challenge database, and an optional `ai_service` container on port 8001. Docker Compose supplies a shared bridge network `scale_net`, mounts the Docker socket into the backend for per-submission container builds, serves voiced tutorial MP4s from `Web-Videos/` via a Vite dev middleware, and persists main database state in the named volume `scale_db_data`.

Students progress through scanning uploaded ZIP archives or Git repositories, reviewing findings and dependency advisories from OSV.dev, completing ten interactive labs spanning injection, cross-site, session, misconfiguration, storage, traversal, XML, and redirect flaws, validating fixes inside disposable Python 3.9 slim images, and consolidating evidence into a multi-section ReportLab PDF. Supplementary features include animated attack replays, unified code diffs with security annotations, AI mentor chat and scan enrichment when `OPENAI_API_KEY` or `SERPER_API_KEY` is present, dual quiz pipelines, instructor AI-assisted assignment creation, administrative security log review, peer messaging, and a challenge leaderboard at `GET /api/challenge/leaderboard`. Three roles — student (`user`), instructor, and administrator — govern registration approval, dashboard routing, and privileged operations.

---

## Table of Contents

- [Abstract](#abstract)
- [1. Introduction](#1-introduction)
- [2. System Overview](#2-system-overview)
- [3. Architecture](#3-architecture)
- [4. Authentication and Authorization](#4-authentication-and-authorization)
- [5. Challenge System](#5-challenge-system)
- [6. Project Scanner](#6-project-scanner)
- [7. Penetration Test Report Generation](#7-penetration-test-report-generation)
- [8. Quiz System](#8-quiz-system)
- [9. Learning Progress and Analytics](#9-learning-progress-and-analytics)
- [10. Leaderboards](#10-leaderboards)
- [11. Security Event Logging](#11-security-event-logging)
- [12. Messaging System](#12-messaging-system)
- [13. AI Services](#13-ai-services)
- [14. Red vs Blue Team Mode](#14-red-vs-blue-team-mode)
- [15. Complete API Reference](#15-complete-api-reference)
- [16. Frontend Pages Reference](#16-frontend-pages-reference)
- [17. Environment and Configuration](#17-environment-and-configuration)
- [18. Setup and Deployment](#18-setup-and-deployment)
- [19. Known Limitations and Technical Debt](#19-known-limitations-and-technical-debt)
- [20. Security Analysis](#20-security-analysis)
- [21. Testing and Verification Strategy](#21-testing-and-verification-strategy)
- [22. Operational Failure Modes and Error Handling](#22-operational-failure-modes-and-error-handling)
- [Appendix A — Complete Annotated File Tree](#appendix-a--complete-annotated-file-tree)
- [Appendix B — Complete Route Map](#appendix-b--complete-route-map)
- [Appendix C — Glossary](#appendix-c--glossary)
- [Appendix D — Development Changelog](#appendix-d--development-changelog)
- [Appendix E — ORM Models](#appendix-e--orm-models-complete-column-reference)
- [Appendix F — Learning Progress Module](#appendix-f--learning-progress-module-full-source)
- [Appendix G — Hints and Replays](#appendix-g--challenge-hints-and-attack-replay-payloads)
- [Appendix H — Frontend Components](#appendix-h--frontend-components)
- [Appendix I — Challenge Directories](#appendix-i--challenge-docker-bind-mounts-and-directories)
- [Appendix J — Docker and Environment](#appendix-j--docker-compose-and-environment-expanded-reference)
- [Appendix K — Route Handlers](#appendix-k--http-route-to-python-handler-names)
- [Appendix L — Scanner Rules](#appendix-l--static-scanner-rules)
- [Appendix M — Source Listings](#appendix-m--primary-backend-and-configuration-source-listings)

---

## 1. Introduction

### 1.1 Problem Statement

Cybersecurity education requires more than conceptual coverage of OWASP vulnerability categories; learners must manipulate realistic inputs, observe server-side effects, and iterate on defensive fixes. Lecture-only delivery fails to build the muscle memory required for secure coding practices. Generic learning management systems lack sandboxed execution for fix validation and do not model adversarial team dynamics. Publicly available vulnerable applications such as DVWA provide exploitation surfaces but do not integrate with instructor grading, analytics, or structured progress across multiple courses. Capture-the-flag platforms emphasize competition over pedagogy and rarely align with syllabus milestones. SCALE bridges this gap by combining instructor oversight, measurable progress, and hands-on exploitation and remediation within a single deployable stack.

Hands-on practice is essential because vulnerabilities manifest as interactions between parsers, frameworks, and data flows that cannot be understood purely from static reading. Students must see how SQL parsers interpret delimiters, how browsers execute injected markup, and how cross-site request forgery relies on ambient authority. SCALE provides bounded, logged simulations so that experimentation produces educational telemetry without exposing unrelated production systems.

Existing tools are insufficient for structured undergraduate education with instructor oversight because they lack unified role models, do not persist per-student analytics in a relational schema suitable for grading exports, and do not combine static scanning of student projects with lab completion in one dashboard. SCALE aggregates scan history, quiz attempts, challenge completion, and remediation evidence for portfolio PDF generation.

### 1.2 Project Objectives

1. Provide a FastAPI backend with JWT authentication, role-based access control, and MySQL persistence for users, progress, quizzes, messages, scans, and security logs.
2. Deliver ten sandbox-validated OWASP-style labs with distinct attack surfaces, fix submission endpoints, and Docker-based unittest scoring.
3. Implement ZIP upload (and optional Git clone) of projects up to 50 MB with safe extraction, Semgrep + regex static scanning with severity scoring and fix recommendations.
4. Integrate OSV.dev dependency vulnerability queries with concurrency caps and background merging into scan results.
5. Offer AI-assisted mentoring, scan explanation, and quiz generation when OpenAI or Serper API keys are configured, with graceful degradation.
6. Support instructor quiz creation, assignment to students with time limits and due dates, AI-assisted bulk generation with fallback to the static bank, and adaptive common-mistakes quizzes from prior wrong answers.
7. Provide student dashboards with challenge mastery visualization, quiz history, instructor-assigned timed lab tasks, PDF export, Red versus Blue game notifications, and a **leaderboard** surfacing ranked challenge completion.
8. Implement Red versus Blue team games mapped to lab identifiers 1–10 with live attack polling and fix validation, scored per round.
9. Record security events with context classification and present an admin console for review.
10. Provide internal messaging between users with unread counts in the sidebar.

### 1.3 Scope and Boundaries

SCALE provides web application security training, static analysis, quizzes, and reporting. It does not provide network penetration testing against arbitrary hosts, malware analysis, or mobile application security. It assumes deployment via Docker Compose on a developer workstation or small server with Docker socket access for sandbox builds. It assumes trusted operators for the host because the backend mounts `/var/run/docker.sock`. SCALE does not guarantee production-grade isolation for command-injection pedagogy on the live ping endpoint; the implementation uses guarded subprocess execution.

### 1.4 Document Organization

Section 2 describes the learning model and feature inventory. Section 3 documents architecture (including data flow and trust boundaries), databases, and frontend state. Sections 4–8 cover authentication, challenges (including sandbox `improvement_score`, narrative attack XP, and timed lab assignments in §5.10), Semgrep + regex scanner (§6), reports, and quizzes (including assignments and mistakes quiz). Section 9 is the full learning analytics reference (Defense Level, skill buckets, streak, dashboard XP, instructor/admin stats). **Section 10 covers Leaderboards** (challenge leaderboard endpoint, Red vs Blue per-game scores, and ranking model). Sections 11–14 cover logging, messaging, AI, and Red vs Blue. Sections 15–16 list APIs and pages. Sections 17–18 cover configuration and deployment (§18.7 dependency pinning). Sections 19–20 state limitations and security posture. Section 21 documents testing and verification. Section 22 documents failure modes. Appendices provide file tree, route map (128 routes), glossary, source listings, and changelog.

---

## 2. System Overview

### 2.1 Platform Description

SCALE is a three-role learning platform. Students complete labs, upload projects for scanning, take quizzes, and participate in Red versus Blue games. Instructors manage quizzes, approve students, assign work, and create games. Administrators manage users, view security logs, and access aggregate statistics. Unlike a static course site, SCALE executes server-side challenge logic, persists progress, generates downloadable evidence artifacts, and surfaces leaderboard rankings for both individual challenge completion and competitive game scores.

### 2.2 Core Learning Model — Scan → Attack → Fix → Quiz → Progress

**Scan:** The student uploads a ZIP via `POST /api/project/upload` or clones a Git repo via `POST /api/project/scan-from-git`. Results are stored in `ScanContext` under `scale.scanData.{user_id}` in `localStorage`. `POST /api/project/scan` walks extracted files, runs Semgrep + regex (`semgrep_scanner.py`, `detector.py`), scores risk in `scorer.py`, attaches fix recommendations in `fixer.py`, persists `ScanHistory` rows, and starts a background thread for `scan_dependencies()`.

**Attack:** For each lab, the student opens attack routes under `/challenges/{n}/attack` or tabbed routes, invoking endpoints such as `POST /api/challenges/vulnerable-login` or `POST /api/challenges/xss/comments`. Success is detected by HTTP responses and client-side success maps.

**Fix (sandbox-validated — primary persistence path):** The student submits Python source via `POST /api/challenges/submit-fix*` routes. On `fixed == true`, the backend calls `mark_challenge_complete`, inserts `UserProgress`, and runs `recalculate_learning_progress`. This is the path used for graded remediation evidence and PDF reports.

**Attack-only completion (optional shortcut):** After a successful attack, the UI may call `POST /api/challenges/mark-attack-complete?challenge_type=<slug>`, which also inserts `UserProgress` and recalculates learning metrics without sandbox validation. Instructors should treat sandbox-passing fixes as the authoritative remediation signal; attack-only rows are a UX convenience, not proof of secure code.

**Quiz:** Students use `StudentQuizPage` to call `POST /api/quizzes/take` for bank quizzes or `POST /api/quiz/generate` for scan-driven quizzes. Attempts persist via `POST /api/quizzes/submit-attempt`.

**Progress and Leaderboard:** `GET /api/stats/progress/me` returns `build_learning_progress_payload` plus `challenge_detail` bar chart data. The backend persists Defense Level (`level`), `streak_days`, `learning_speed`, `retention_score`, `accuracy`, and `skills` buckets. `GET /api/challenge/leaderboard` returns ranked completion data for the challenge game layer (Section 10).

### 2.3 Feature Inventory

| Feature | Description | User Role | Primary Implementation |
|---------|-------------|-----------|------------------------|
| ZIP upload and static analysis | Upload ZIP or Git repo, extract whitelisted code, Semgrep + regex scan | Student | `projects.py`, `semgrep_scanner.py`, `detector.py` |
| Dependency scanning (OSV.dev) | Manifests parsed, POST to `https://api.osv.dev/v1/query` | Student | `dependency_scanner.py` |
| Ten interactive labs | Attack, fix, tutorial flows per OWASP category | Student | `challenges.py`, `frontend/src/pages/*` |
| Docker sandbox fix validation | Build image, run `run_tests.sh`, timeout 25 s | Student | `sandbox_runner.py` |
| Code diff viewer | Unified diff with security annotations | Student | `CodeDiffViewer.tsx`, `generate_code_diff` |
| Attack replay visualizer | Stepper UI over `ATTACK_REPLAYS` | Student | `AttackReplayVisualizer.tsx` |
| AI mentor | Mentor chat and `/api/ai/analyze-code` | Student | `ai_mentor.py`, `ChallengeHintPanel.tsx` |
| AI quiz generation | Instructor AI assign and dynamic quiz | Instructor, Student | `quizzes.py`, `quiz_dynamic.py` |
| Static MCQ bank | Topics, difficulty, random sampling; 200 seeded questions across 20 topics | Student | `quizzes.py`, `seed_db.py` |
| Quiz assignments | Instructor assigns bank questions with `time_limit_minutes`, `due_date`, per-student status | Instructor, Student | `quizzes.py`, `StudentQuizPage.tsx` |
| Common mistakes quiz | AI or fallback quiz from student's prior wrong answers | Student, Instructor | `quizzes.py`, `StudentQuizPage.tsx` |
| Timed lab assignments | Instructor assigns a lab fix task with countdown timer and sandbox grading | Instructor, Student | `challenge_assignments.py`, `ChallengeAssignmentPage.tsx` |
| **Leaderboard** | Challenge game leaderboard ranking participants by completion count and score | Student, Instructor | `game_challenge.py`, `/api/challenge/leaderboard` |
| Voiced tutorial videos | MP4 playback via `/challenge-videos/` dev middleware | Student | `ChallengeTutorialVideo.tsx`, `vite.config.ts`, `Web-Videos/` |
| Pentest PDF report | Five-section ReportLab PDF | Student | `report.py` |
| Challenge progress reset | `DELETE /api/challenges/progress/{slug}` | Student | `challenges.py`, `ChallengesListPage` |
| Challenge mastery chart | `challenge_detail` horizontal bars | Student | `DashboardHomePage.tsx`, `learning_tracker.py` |
| Red vs Blue mode | Teams, attacks, fixes, turn-based scoring | Instructor, Student | `red_blue.py` |
| My Games portal | Student `GET /api/redblue/my-games` | Student | `RedBlueMyGamesPage.tsx` |
| Role dashboards | Admin, instructor, student stats | All | `stats.py`, dashboard pages |
| Security logging | `security_logs` table and filters | Admin | `security_logger.py`, `security_logs.py` |
| Admin user management | Approve, role, delete | Admin | `auth.py` |
| Messaging | Unread count and threads | All | `messages.py`, `Sidebar.tsx` |
| AI status indicator | `GET /api/ai/status` | Student | `DashboardHomePage.tsx` |
| Tab-isolated auth | `sessionStorage` keys | All | `LoginPage.tsx`, `ProtectedRoute.tsx` |
| User-scoped scan storage | `scale.scanData.{user_id}` | Student | `ScanContext.tsx` |
| Gamified progress and analytics | Defense Level tiers, skill buckets, streak, retention, dashboard XP (client), mastery bars | Student | `learning_tracker.py`, `DashboardHomePage.tsx` |
| Instructor / admin analytics | Class completion, per-bucket performance, challenge usage and attempts | Instructor, Admin | `stats.py`, dashboard pages |

### 2.4 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Backend runtime | Python | 3.x (image 3.9-slim in sandbox) | Server and sandbox |
| Backend framework | FastAPI | unpinned in `requirements.txt` | REST API |
| ASGI server | Uvicorn | `[standard]` extra | ASGI |
| ORM | SQLAlchemy | unpinned | Database access |
| MySQL driver | PyMySQL | unpinned | MySQL connectivity |
| Auth hashing | passlib bcrypt, bcrypt | `bcrypt==4.0.1` | Password hashing |
| JWT | python-jose | `[cryptography]` | Tokens |
| HTTP client | requests, httpx | unpinned | OSV HTTP, async clients |
| SAST | Semgrep | unpinned in `requirements.txt` | Security rule scanning |
| PDF | ReportLab | unpinned | PDF reports |
| Docker SDK | docker | unpinned | Sandbox |
| XML | lxml | unpinned | XXE lab |
| Frontend | React | `^18.2.0` | UI |
| Frontend | Vite | `^5.2.0` | Dev server |
| Frontend | TypeScript | `^5.2.2` | Typing |
| Frontend | axios | `^1.12.2` | HTTP |
| Frontend | react-router-dom | `^6.22.3` | Routing |
| Frontend | recharts | `^3.7.0` | Charts |
| Database | MySQL | `8.0` (image) | Persistence |
| AI (optional) | OpenAI | unpinned in requirements | LLM |

> **Reproducibility note:** Python dependencies in `backend/requirements.txt` pin **only** `bcrypt==4.0.1`; FastAPI, SQLAlchemy, Uvicorn, and most other packages are unpinned. Node dependencies use semver ranges in `frontend/package.json`. Builds are therefore not bit-for-bit reproducible across time unless operators freeze versions (`pip freeze`, `npm ci` with lockfile). For examination or deployment, capture a snapshot of resolved versions alongside this document.

---

## 3. Architecture

### 3.1 Architectural Overview

The browser loads the Vite dev server on port 5173. API calls use `VITE_API_URL` defaulting to `http://localhost:8000`, targeting the FastAPI backend on port 8000. The backend connects to `main_db:3306` internally (`scale_db`), `challenge_db_sqli:3306` (`testdb`), and `challenge_db_csrf:3306` (`csrfdb`). The `ai_service` container listens on 8001. The backend mounts the Docker socket and builds per-submission images on `scale_net`; containers run with memory and CPU limits. CORS allows `http://localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, and `127.0.0.1:3000` with credentials.

```
Browser (port 5173)
    | HTTP (VITE_API_URL → port 8000)
    v
FastAPI Backend (scale_application-backend-1)
    |          |              |              |
    v          v              v              v
main_db:3306  sqli:3307  csrf:3308    ai_service:8001
    |
    Docker socket → ephemeral sandbox containers (scale_net)
```

### 3.1.1 Data Flow, Trust Boundaries, and Student Artifact Path

**Trust zones:**

| Zone | Boundary | What is trusted |
|------|----------|-----------------|
| Browser | User agent | Same-origin SPA; JWT in `sessionStorage` is readable to scripts on that origin (Section 20). |
| API process | FastAPI on `backend` container | Validates JWT, enforces roles, writes MySQL; does not trust file contents as safe code. |
| Extracted project | Host filesystem under `uploads/` | Treated as untrusted input for regex scanning; never executed as application code during static scan. |
| Sandbox container | Ephemeral Docker build on `scale_net` | Executes only the challenge template harness (`run_tests.sh` + unittest) with submitted `app.py` replacement; network and resources capped in `sandbox_runner.py`. |
| External OSV | `https://api.osv.dev` | Treated as best-effort; failures degrade to partial dependency results (Section 22). |

**Data flow — upload → scan → results:** The student selects a ZIP in the Scanner page. The browser sends it to `POST /api/project/upload`; the backend stores the archive and extracts allowed source files to a user-scoped folder, creating a `Project` row. `POST /api/project/scan` walks extracted files, applies `RULES` and heuristics, computes severity-weighted scores, persists a `ScanHistory` row with `vuln_summary` JSON, and starts a background thread that queries OSV for dependency advisories and merges results into the same summary. The HTTP response returns static/regex findings immediately; dependency rows may populate shortly after via refresh on the Dependencies tab.

**Data flow — fix → sandbox → score:** Fix submissions never reuse the uploaded project tree for execution. They replace `app.py` inside a known challenge directory (bind-mounted from `challenge-*` at `/app/challenges/...`). `_verify_fix_improvement` runs the sandbox twice (vulnerable baseline vs. student code) and derives `improvement_score` (Section 5.2.1).

### 3.2 Docker Compose Services

| Service | Image / Build | Internal Port | External Port | Volumes | Depends On | Purpose |
|---------|---------------|---------------|---------------|---------|------------|---------|
| sandbox_base | build `./backend/sandbox_base` | — | — | — | — | Base image for student sandbox containers |
| backend | build `./backend` | 8000 | 8000 | docker.sock, backend, challenge dirs | DBs, sandbox_base | FastAPI API + sandbox runner |
| frontend | build `./frontend` | 5173 | 5173 | frontend, node_modules volume | — | Vite SPA dev server |
| ai_service | build `./ai_service` | 8001 | 8001 | ai_service | — | Template AI microservice |
| main_db | mysql:8.0 | 3306 | 3306 | scale_db_data, init.sql | — | Primary application database |
| challenge_db_sqli | mysql:8.0 | 3306 | 3307 | users.sql | — | SQL injection challenge data |
| challenge_db_csrf | mysql:8.0 | 3306 | 3308 | csrf.sql | — | CSRF challenge accounts |

### 3.3 Startup Sequence

`docker compose up --build` builds images, starts `sandbox_base` to completion, starts MySQL containers with healthchecks, then starts `backend` after `depends_on` conditions succeed. The backend runs `seed_db.py` then `uvicorn ... --reload`. On startup, `startup_event` retries `create_all` up to ten times with three-second delays until MySQL accepts connections. `_ensure_runtime_schema()` patches missing columns on `security_logs`, `user_learning_progress`, `teams`, `game_challenges`, `red_team_actions`, and `blue_team_fixes`. `seed_db.py` waits for MySQL, creates tables, seeds default accounts (**development only — rotate before exposure; Section 18.2**), and inserts up to 200 quiz questions if fewer exist.

### 3.4 Network Configuration

`scale_net` is a bridge network attaching backend, frontend, databases, and ai_service so internal DNS names resolve. CORS is an explicit allowlist as listed in `main.py`. The Docker socket must be mounted so `docker.from_env()` can build and run sandbox images; this grants significant host capability and is documented as a development-oriented choice.

### 3.5 Backend Architecture

#### 3.5.1 Application Structure

- `backend/app/main.py` — FastAPI app factory, CORS, routers, startup event.
- `backend/app/models.py` — SQLAlchemy ORM models.
- `backend/app/schemas.py` — Pydantic request/response schemas.
- `backend/app/crud.py` — User CRUD helpers.
- `backend/app/db/database.py` — Engine and session factory.
- `backend/app/sandbox_runner.py` — Docker sandbox execution and diff generation.
- `backend/app/api/*.py` — Routers for each feature area.
- `backend/app/scanner/*.py` — Detection, scoring, fixes, and dependency scanning.
- `backend/app/security/*.py` — Security logging and learning analytics.
- `backend/seed_db.py` — Database seeding on first run.

#### 3.5.2 Application Factory (`main.py`)

Routers mounted in `main.py`:

| Router File | Prefix | Primary Responsibility |
|-------------|--------|------------------------|
| auth.py | /api/auth | Login, register, logout, profile, admin user management |
| challenges.py | /api/challenges | Labs, fix submission, hints, replay, progress |
| projects.py | /api | Upload, scan, reports, dependencies |
| quizzes.py | /api/quizzes | Bank, take, assignments, AI assign |
| quiz_dynamic.py | /api/quiz | Dynamic generation from scan context |
| stats.py | /api/stats | Admin, instructor, student dashboards |
| messages.py | /api/messages | Messaging threads |
| security_logs.py | /api/security | Admin log query and stats |
| instructor.py | /api/instructor | Student analytics, progress reset |
| report.py | /api/report | Portfolio pentest PDF |
| red_blue.py | /api/redblue | Red vs Blue game lifecycle |
| challenge_assignments.py | /api/challenge-assignments | Instructor timed lab assignments |
| ai_mentor.py | /api/ai | Status, mentor chat, analyze-code |
| game_challenge.py | /api/challenge | Legacy game endpoints, **leaderboard** |
| misconfig.py | /api | Security misconfiguration mini-lab |
| attack_simulator.py | /api/attack | Attack simulation |
| project_analyzer.py | /api | Project structure analysis |

Startup runs `models.Base.metadata.create_all`, then `_ensure_runtime_schema()` — a lightweight runtime migration guard that `ALTER TABLE`s missing columns when Alembic is not used. Logs AI status via `OPENAI_API_KEY` and `SERPER_API_KEY` environment variables.

#### 3.5.3 Dependency Injection

`OAuth2PasswordBearer` reads an optional bearer token. `get_current_user` decodes the JWT from the header or `access_token` cookie, loads the user by email, and returns 401 if invalid. `get_db` yields `SessionLocal`. `require_role(*roles)` maps `student` to `user` and returns 403 if the role is not allowed.

### 3.6 Frontend Architecture

#### 3.6.1 Application Structure

- `frontend/src/App.tsx` — Route table.
- `frontend/src/lib/api.ts` — Axios instance with `withCredentials`.
- `frontend/src/context/ScanContext.tsx` — User-scoped scan storage.
- `frontend/src/components/` — Layout, modals, replay visualizer, diff viewer.
- `frontend/src/pages/` — Page-level React components.

#### 3.6.2 Routing (`App.tsx`)

`/` Landing, `/login`, `/register` — public. Protected shell: `/home` Dashboard, `/challenges`, `/messages`, `/scanner`, `/attack-lab`, challenge routes `/challenges/1..10/...`, `/challenges/attack-success`, `/redblue/game/:gameId`. Student-only routes: `/quiz`, `/redblue/my-games`, `/assignment/:assignmentId`. Instructor routes: `/instructor/dashboard`, `/instructor/quiz`, `/instructor/assignment/:assignmentId/results`, `/redblue/create`. Admin routes: `/admin/stats`, `/admin/dashboard`, `/admin/logs`. Unknown paths redirect to `/`.

#### 3.6.3 Authentication State (`sessionStorage`)

Keys stored: `token`, `role`, `user_id`, `user_email`. Session storage isolates tabs so multiple roles can be tested in parallel browser windows. `ProtectedRoute` calls `GET /api/auth/me` and clears storage on failure.

#### 3.6.4 API Client (`api.ts`)

`baseURL` is `import.meta.env.VITE_API_URL || 'http://localhost:8000'`. The request interceptor sets `Authorization: Bearer` when a token is present and not `cookie-auth`. `withCredentials: true` sends cookies on every request.

#### 3.6.5 Scan Context (`ScanContext.tsx`)

Stores `scanData` with `projectId` and `results`. Storage key is `scale.scanData.{user_id}` in `localStorage`. On logout, `Sidebar` removes `scale.scanData.{user_id}`. A `scale-user-changed` browser event refreshes context when the authenticated user changes.

### 3.7 Database Architecture

#### 3.7.1 Three Database Instances

| Instance | External Port | Internal | Database | Purpose |
|----------|---------------|----------|----------|---------|
| main_db | 3306 | 3306 | scale_db | Users, progress, scans, messages, quizzes |
| challenge_db_sqli | 3307 | 3306 | testdb | SQL injection lab user data |
| challenge_db_csrf | 3308 | 3306 | csrfdb | CSRF lab bank accounts |

#### 3.7.2 ORM Models — Summary Reference

| Model | Table | Key Columns | Used By |
|-------|-------|-------------|---------|
| User | users | id, email, hashed_password, role, is_approved | Auth, dashboards, all user-scoped features |
| UserProgress | user_progress | user_id, challenge_id, completed_at | Challenges, stats, PDF |
| XSSComment | xss_comments | author, content | XSS lab |
| Challenge | challenges | id, title, description | PDF titles |
| Question / QuestionOption / UserAnswer | questions, question_options, user_answers | Quiz bank and per-answer tracking | Quiz system |
| QuizAssignment / QuizAssignmentStudent / QuizAssignmentQuestion | quiz_assignments, quiz_assignment_students, quiz_assignment_questions | Normalized quiz assignment tables with timing | Quiz assignments |
| QuizAttempt | quiz_attempts | user_id, score, total, time_seconds | Scoring, dashboard XP |
| CSRFAccount | csrf_accounts | username, balance | CSRF lab |
| Message | messages | sender_id, receiver_id, content, is_read | Messaging |
| Project / ScanHistory | projects, scan_history | owner_id, vuln_summary JSON, risk_score | Scanner, PDF |
| ChallengeAssignment / ChallengeAssignmentStudent | challenge_assignments, challenge_assignment_students | challenge_slug, time_limit_minutes, due_date, status, score | Timed assignments |
| Team / TeamMember / GameChallenge / ChallengeVulnerability / RedTeamAction / BlueTeamFix | teams, team_members, game_challenges, challenge_vulnerabilities, red_team_actions, blue_team_fixes | Red vs Blue game data; red_score, blue_score, current_phase | Red vs Blue |
| ChallengeState | challenge_state | user_id, challenge_id, attempt_count, hints_used | Analytics, hint system |
| SecurityLog | security_logs | event_type, severity, payload, context_type | Admin log console |
| UserLearningProgress | user_learning_progress | level, streak_days, accuracy, skills, retention_score | Dashboard analytics |

Full column-level source is in Appendix E.

---

## 4. Authentication and Authorization

### 4.1 Registration

`POST /api/auth/register` accepts a `UserCreate` schema with email, password, and role (defaults to `user`). Admin self-registration is forbidden — the endpoint returns 403 if the requested role is `admin`. Passwords are hashed with bcrypt via passlib. Instructors who self-register receive `is_approved=False` and must be approved by an administrator before they can log in.

### 4.2 Login

The normal login path (`POST /api/auth/login`) verifies the bcrypt hash, requires `is_approved=true`, issues a JWT with `sub=email`, `role`, and `exp`, and sets an HttpOnly `access_token` cookie. When `ENABLE_BROKEN_AUTH_CHALLENGE=true` and the query parameter `challenge=broken-auth` is present, the endpoint switches to a SQLite in-memory branch that executes `f"SELECT * FROM users WHERE email = '{user.username}' AND password = '{user.password}'"` — an intentionally injectable query used for pedagogical demonstration in Lab 5.

### 4.3 Role-Based Access Control

`require_role` normalizes the string `student` to `user`. Students register as `user` (auto-approved); instructors may be pending; administrators are created by existing admins. Dashboard routing in the frontend sends each role to its dedicated section.

| Role | Access | Notes |
|------|--------|-------|
| user (student) | Labs, quizzes, scanner, messages, assignments, Red vs Blue (participant) | Default role on registration |
| instructor | All student access + quiz management + assignment creation + game creation + student analytics | Requires admin approval |
| admin | All instructor access + user management + security logs | Created via admin endpoint |

### 4.4 Tab-Isolated Sessions

JWT data (`token`, `role`, `user_id`, `user_email`) is stored in `sessionStorage`, which is scoped to the browser tab. Multiple roles can be tested in parallel without interference.

### 4.5 Logout

`POST /api/auth/logout` deletes the `access_token` cookie server-side. The frontend clears `sessionStorage`, removes `scale.scanData.{user_id}` from `localStorage`, and dispatches a `scale-user-changed` event to refresh context across components.

### 4.6 Token Validation

`get_current_user` checks the `Authorization: Bearer` header first, then falls back to the `access_token` cookie. The token is decoded using `SECRET_KEY` and `JWT_ALGORITHM` (default HS256). A 401 is returned for expired, malformed, or missing tokens.

---

## 5. Challenge System

### 5.1 Challenge Catalog

| ID | Slug | Vulnerability | Attack Endpoint | Fix Endpoint | Sandbox Directory |
|----|------|---------------|-----------------|--------------|-------------------|
| 1 | sql-injection | SQL Injection | `POST /api/challenges/vulnerable-login` | `POST /api/challenges/submit-fix` | challenge-sql-injection |
| 2 | xss | Cross-Site Scripting | `POST /api/challenges/xss/comments` | `POST /api/challenges/submit-fix-xss` | challenge-xss |
| 3 | csrf | Cross-Site Request Forgery | `POST /api/challenges/csrf/transfer` | `POST /api/challenges/submit-fix-csrf` | challenge-csrf |
| 4 | command-injection | Command Injection | `POST /api/challenges/ping` | `POST /api/challenges/submit-fix-command-injection` | challenge-command-injection |
| 5 | broken-auth | Broken Authentication | Auth branch + labs | `POST /api/challenges/submit-fix-auth` | challenge-broken-auth |
| 6 | security-misc | Security Misconfiguration | `GET /api/admin/config` — any authenticated user (intentionally missing authorization; see §5.2.2) | `POST /api/challenges/submit-fix-misc` | challenge-security-misc |
| 7 | insecure-storage | Insecure Storage | `POST /api/challenges/storage/register` + `GET /api/challenges/storage/dump` | `POST /api/challenges/submit-fix-storage` | challenge-insecure-storage |
| 8 | directory-traversal | Directory Traversal | `GET /api/challenges/traversal/read` | `POST /api/challenges/submit-fix-traversal` | challenge-directory-traversal |
| 9 | xxe | XML External Entity | `POST /api/challenges/xxe/parse` | `POST /api/challenges/submit-fix-xxe` | challenge-xxe |
| 10 | redirect | Unvalidated Redirect | `GET /api/challenges/redirect` | `POST /api/challenges/submit-fix-redirect` | challenge-redirect |

### 5.2 Challenge Architecture Pattern

Each challenge follows the pattern: Tutorial → Attack → Fix → optional `mark-attack-complete`. Fix routes post JSON `{"code": "..."}` to their respective submit-fix endpoint. `_verify_fix_improvement` runs the sandbox twice and derives `improvement_score`. `mark_challenge_complete` is invoked on both successful sandbox fixes and on `POST /api/challenges/mark-attack-complete` (attack-only, no code validation).

### 5.2.1 Improvement Score (`improvement_score`)

`improvement_score` is returned by every fix submission path that calls `_verify_fix_improvement`. It quantifies how much the student's submission reduced unittest failure and error counts relative to the vulnerable baseline.

**Computation:**

1. `before_result` = `run_in_sandbox_detailed` with the on-disk vulnerable `app.py`.
2. `after_result` = `run_in_sandbox_detailed` with the submitted source string.
3. `before_count` = `failures + errors` from the baseline run.
4. `after_count` = `failures + errors` from the student run.
5. `fixed` is `true` only if the after-run reports `success` and `after_count == 0`.
6. `improvement_score` (integer 0–100):
   - If both `before_count == 0` and `after_count == 0`: score is **100** (already-clean baseline edge case).
   - Otherwise: `floor(min(100, max(0, (before_count - after_count) / max(before_count, 1) * 100)))`.

A high `improvement_score` with `fixed == false` means tests still fail but the student reduced failing cases. The code diff (`code_diff`) is only attached when `fixed == true` and vulnerable source existed.

### 5.2.2 Security Misconfiguration Lab — Auth Model for `GET /api/admin/config`

This endpoint is **not** unauthenticated. It uses `Depends(get_current_user)` in `misconfig.py`: the caller must present a valid JWT. There is **no** `require_role("admin")` check — any authenticated student, instructor, or admin may read the response. That missing authorization step (authentication without role enforcement) is the intentional misconfiguration taught in Lab 6; it is not an accidental auth bypass on a production admin API.

The JSON body includes a pedagogical snapshot (`debug: true`, sample `secret_key`, `database_url`, filtered `env_sample`) — not a live dump of all production secrets, but realistic enough to teach impact.

### 5.3 Sandbox Fix Validation

Docker builds from Python 3.9 slim on `scale_net`, with `mem_limit=256m`, `cpu_quota=50000`, `pids_limit=128`, and `SANDBOX_RUN_TIMEOUT` default of 25 seconds. The submission image is removed after the run. The sandbox pipeline is:

1. Backend builds a Docker image from the challenge directory with the student's code replacing `app.py`.
2. `run_tests.sh` runs `python -m unittest discover` inside the container.
3. Pass/fail counts, test output, and timing are returned to the API handler.
4. The handler calls `mark_challenge_complete` only if `fixed == true`.

### 5.4 Code Diff Viewer

`CodeDiffViewer.tsx` renders a side-by-side table with red (removed) and green (added) rows, plus annotation tooltips from `DIFF_ANNOTATIONS` in `sandbox_runner.py` (covers slugs: sql-injection, xss, command-injection, csrf, broken-auth, directory-traversal, xxe).

### 5.5 Attack Replay

`GET /api/challenges/replay/{slug}?sample=true` bypasses the completion check and returns `ATTACK_REPLAYS` — a structured list of steps with types `user_action`, `user_input`, `http_request`, `server_processing`, and `http_response`. The `AttackReplayVisualizer.tsx` component renders each step as an interactive stepper.

### 5.6 Hint System

`GET /api/challenges/hints?challenge_id=<slug>` returns `_HINTS` for slugs: `csrf`, `broken-auth`, `security-misc`, `directory-traversal`, `xxe`, `insecure-storage`. Each hint has a `level` and optional `penalty`. Advanced hints for the game layer are available via `POST /api/challenge/hint` in `game_challenge.py`.

### 5.7 Challenge Progress and Reset

`GET /api/challenges/progress` returns all `UserProgress` rows for the current user. `DELETE /api/challenges/progress/{slug}` removes `UserProgress` and `ChallengeState` variants for that slug and recalculates learning progress.

### 5.8 Attack-Success Narrative XP (Display Only)

After a successful attack, students may navigate to `/challenges/attack-success?type=<slug>`. The page reads static `typeConfig` integers that are labeled "XP gained" in the UI.

| Slug | Narrative XP Shown |
|------|--------------------|
| sql-injection | 150 |
| command-injection | 160 |
| broken-auth | 140 |
| security-misc | 140 |
| xxe | 140 |
| csrf | 130 |
| directory-traversal | 130 |
| insecure-storage | 130 |
| xss | 120 |
| redirect | 110 |

These numbers are **not** sent to the backend, **not** added to `currentXp` on the dashboard, and **not** stored in any table. They exist solely to reinforce accomplishment after completing an attack.

### 5.9 Instructor Timed Lab Assignments

Instructors create timed fix assignments via `POST /api/challenge-assignments/create`, selecting a lab slug, title, optional instructions, `time_limit_minutes` (10–240), optional `due_date`, and a list of student user IDs. This is separate from self-paced labs on `/challenges` — assignment progress is stored in `challenge_assignment_students`, not `user_progress`.

**Student workflow:**

1. The dashboard lists open assignments via `GET /api/challenge-assignments/my`.
2. Student opens `/assignment/:assignmentId` (`ChallengeAssignmentPage.tsx`).
3. `POST /api/challenge-assignments/{id}/start` begins the countdown (`status` → `in_progress`, `started_at` set).
4. Student submits fix code; `POST /api/challenge-assignments/{id}/submit-fix` runs the same `_verify_fix_improvement` sandbox as self-paced labs.
5. On timeout or past due date, status becomes `expired`; score is **100** if sandbox passes, **0** otherwise.

**Instructor workflow:** `GET /api/challenge-assignments/instructor` lists assignments with aggregate pass/fail counts. `GET /api/challenge-assignments/{id}/results` shows per-student outcomes. `DELETE /api/challenge-assignments/{id}` soft-deactivates the assignment (`is_active=false`).

---

## 6. Project Scanner

### 6.1 Dual-Engine Static Analysis (Semgrep + Regex)

`POST /api/project/scan` invokes `run_merged_scan` in `projects.py`, which:

1. Runs `run_semgrep_scan` (`scanner/semgrep_scanner.py`) with security-focused rulesets when the `semgrep` CLI is available in the backend container.
2. Runs the legacy regex detector (`detector.py` + `rules.py`) including CSRF heuristics (POST patterns without CSRF token keywords).
3. Merges findings via `_merge_findings`, deduplicating by file/line/type where possible and tagging each row with `engine: "semgrep"` or the legacy source.

If Semgrep is unavailable, the scan degrades gracefully to regex-only. The response includes `scanner_engines.semgrep: false` and optional `semgrep_errors`. The Scanner UI (`Scanner.tsx`) displays a Semgrep badge when the engine contributed findings.

### 6.2 Scoring, Fixes, and Dependencies

Severity weights: High=5, Medium=3, Low=1. Risk thresholds: score ≤ 10 → Low, ≤ 20 → Medium, else High. `fixer.py` attaches `FIX_RECOMMENDATIONS` to each finding by vulnerability type. `vuln_summary` JSON includes findings, summary counts, debug info, `semgrep_findings` count, and `dependency_scan` results (populated after the background thread).

### 6.3 Git Upload and Async Scan Status

`POST /api/project/scan-from-git` clones a repository URL into the uploads area and triggers the same merged scan pipeline. `GET /api/project/scan-status/{scan_id}` supports polling for long-running scan jobs.

### 6.4 Dependency Scanner (OSV.dev)

`dependency_scanner.py` parses manifest files (`requirements.txt`, `package.json`, `pom.xml`, etc.) from the extracted project, queries `https://api.osv.dev/v1/query` for each dependency, and merges advisory data into `vuln_summary.dependency_scan`. The scanner caps queries at `MAX_DEPS_TO_QUERY = 50` packages. OSV queries use a 4-second timeout per package; failures are silent per-package and do not fail the overall scan.

---

## 7. Penetration Test Report Generation

### 7.1 Student Portfolio PDF (`GET /api/report/pdf`)

Router: `report.py`, prefix `/api/report`. Builds a five-section ReportLab PDF:

1. Cover page with student email, date, and risk summary.
2. Executive summary with a colored vulnerability severity table.
3. Vulnerability inventory (flattened findings from latest `ScanHistory`).
4. Remediation evidence from `UserProgress` and `ChallengeState` rows.
5. Learning metrics table (Defense Level, accuracy, streak, skills).

The filename is `pentest_report_{safe_email}_{YYYYMMDD}.pdf`. Returns **404** if the user has no owned `ScanHistory`.

### 7.2 Project-Scoped Reports (`projects.py`)

`GET /api/project/report` returns JSON security analysis for the latest scan of a project. `GET /api/project/report/pdf` generates a per-upload PDF via `scanner/report_generator.py`, which is distinct from the student portfolio PDF above. Operators should not confuse the two URLs; the dashboard typically emphasizes the portfolio export.

---

## 8. Quiz System

### 8.1 Architecture Overview

SCALE provides two quiz pipelines:

- **`/api/quizzes`** — static MCQ bank, normalized assignment tables, instructor workflows, common mistakes, AI generation.
- **`/api/quiz`** — dynamic generation from scan context (`quiz_dynamic.py`).

### 8.2 Static Quiz Bank

`POST /api/quizzes/take` samples questions by topic and difficulty. `seed_db.py` seeds **200 MCQ questions** across **20 security topics** (10 questions each). Topics include all ten OWASP categories covered by SCALE labs, plus broader categories such as cryptography, network security, and secure design principles.

### 8.3 Instructor Quiz Management

`GET /api/quizzes/manage` and `POST /api/quizzes/manage` provide CRUD for the question bank. `POST /api/quizzes/assignments` creates assignments with normalized rows in `quiz_assignment_students` and `quiz_assignment_questions`. Assignments support `time_limit_minutes` and `due_date`. Legacy comma-separated `question_ids` / `assigned_student_ids` columns on `QuizAssignment` are retained for backward compatibility but new assignments use normalized tables.

### 8.4 Student Quiz Interface

`StudentQuizPage.tsx` provides four quiz modes:

| Mode | Trigger | Backend Endpoint |
|------|---------|-----------------|
| Practice quiz | Topic/difficulty bank sampling | `POST /api/quizzes/take` |
| Instructor assignment | Start from `assignments/student` list | `GET /api/quizzes/assignments/{id}/take` |
| Scan-based quiz | From scan findings | `POST /api/quiz/generate` |
| Common mistakes quiz | From prior wrong answers | `POST /api/quizzes/common-mistakes-quiz` |

### 8.5 Dynamic AI Quiz

`POST /api/quiz/generate` (`quiz_dynamic.py`) generates a quiz from scan findings context. Requires `require_role('user')`. Falls back to static bank questions when no scan context is provided.

### 8.6 Instructor AI Quiz Generator

`POST /api/quizzes/ai-generate-and-assign` accepts an `AIQuizAssignRequest` with topic, difficulty, num_questions, student_ids, and optional due_date. Returns `AIQuizAssignResponse` with `ai_generated`, `ai_questions_created`, and `mixed_topics`. A preview step is available via `POST /api/quizzes/generate-ai-preview`.

### 8.7 Instructor Mistakes Quiz Assignment

`POST /api/quizzes/assign-mistakes-quiz` (instructor/admin) accepts `student_id` and optional `num_questions`. It generates a mistakes payload for the specified student and creates a `QuizAssignment` assigned to that student. Questions generated for mistakes quizzes are tagged with `targets_mistake=true` on the `questions` table.

### 8.8 Quiz Attempts and History

`POST /api/quizzes/submit-attempt` persists a `QuizAttempt` row with `score`, `total`, `time_seconds`, and optional `assignment_id`. `GET /api/quizzes/attempts` returns the current user's full history. `GET /api/quizzes/wrong-answer-count` returns the count of incorrect `UserAnswer` rows for the mistakes quiz trigger.

---

## 9. Learning Progress and Analytics

Analytics are implemented in `backend/app/security/learning_tracker.py` and exposed primarily via `GET /api/stats/progress/me` (`stats.py`). That endpoint returns `build_learning_progress_payload` plus `challenge_detail` from `build_challenge_progress_detail`. `GET /api/instructor/user/{id}/analytics` returns the same core fields as the student payload but without `challenge_detail`.

### 9.1 Persisted Learning Profile (`user_learning_progress`)

`recalculate_learning_progress` aggregates:

- **Distinct labs solved:** count of distinct `UserProgress.challenge_id` values, capped at `TOTAL_CHALLENGES` (10).
- **Quiz accuracy:** from `UserAnswer` rows (`is_correct`).
- **Failed attempts:** total answers minus correct (quiz-focused).
- **Average quiz time:** mean of `QuizAttempt.time_seconds` for the user.
- **Strongest / weakest category:** derived from `compute_skills_scores` (see §9.2).
- **`level`:** Beginner / Intermediate / Advanced via `_determine_level` (see §9.3).
- **`streak_days`:** consecutive calendar days with at least one `UserProgress.completed_at` (see §9.4).
- **`learning_speed`:** `(solved / max(avg_time, 1)) * 100` when solved > 0, else 0.
- **`retention_score`:** blended metric capped at 100 — accuracy component (60% weight), streak component (scaled to 14 days), and a penalty for failed quiz answers.

The `recommendations` array from `get_learning_recommendations` provides personalized guidance, e.g. focus on the weakest bucket, suggest AI Mentor if accuracy < 60%, suggest hints if `failed_attempts` > 10.

### 9.2 Skill Buckets and Radar Dimensions

Six named dimensions aggregate completion of one or more challenge slugs each:

| Bucket | Contributing Slugs |
|--------|--------------------|
| SQL Injection | `sql-injection`, `broken-auth` |
| XSS | `xss` |
| CSRF | `csrf`, `redirect` |
| Traversal | `directory-traversal`, `command-injection` |
| XXE | `xxe` |
| Storage | `insecure-storage`, `security-misc` |

Per bucket, the score is `floor(100 * (slugs solved in bucket) / (number of slugs in bucket))`. The API returns `skills` (map) and `skills_radar` (array of `{subject, value}`) for radar chart rendering.

### 9.3 Defense Level (Ranking Tier) — Backend `level` Field

The dashboard "Defense Level" card displays `learning.level` from the API. It is not a numeric rank among all users. Thresholds in `_determine_level`:

| Level | Condition |
|-------|-----------|
| **Advanced** | `vulnerabilities_solved >= 9` **and** `accuracy >= 80` |
| **Intermediate** | `vulnerabilities_solved >= 4` **and** `accuracy >= 60` |
| **Beginner** | Otherwise |

`vulnerabilities_solved` is the capped distinct-completion count; `accuracy` is quiz accuracy from `UserAnswer`. The UI copy "Keep fixing to rank up" refers to moving between these three tiers.

### 9.4 Streak, Learning Speed, and Retention Score

- **Streak:** `UserProgress.completed_at` dates are sorted (most recent first). The algorithm increments the streak while dates are consecutive calendar days (same-day completions count toward the current day).
- **Learning speed:** Higher when more labs are solved relative to mean quiz duration.
- **Retention score:** Combines accuracy (60% weight), streak (scaled to 14 days), and a penalty from failed quiz answers — capped between 0 and 100.

### 9.5 Challenge Mastery Detail (`challenge_detail`)

`build_challenge_progress_detail` returns ten rows — one per lab. Each row has `slug`, `label`, `category`, `color`, `completed` (boolean from `UserProgress`), and `value` (0 or 100 for bar width). The student dashboard renders horizontal Challenge Mastery bars, category badges, per-row Reset controls, and a by-category summary grid.

### 9.6 Dashboard "Current Score" XP (`currentXp`) — Client-Side Only

`DashboardHomePage.tsx` computes:

```
currentXp = solvedLabs * 100 + (quizAttempts.length > 0 ? avgScorePercent : 0)
```

`solvedLabs` prefers `learning.vulnerabilities_solved` from the API, falling back to a distinct count from `GET /api/challenges/progress`. `avgScorePercent` is the mean percentage across all `GET /api/quizzes/attempts` rows. If there are no quiz attempts, the second term is **0**. This value is labeled "XP" in the UI but is **not** persisted in MySQL and is **not** the same as narrative attack-success XP (§5.8) or sandbox `improvement_score`. It is a single-number gamification summary for the student.

### 9.7 Other Dashboard Cards (Student)

| Card | Data source |
|------|-------------|
| Vulnerabilities | `solvedLabs / totalLabs` with link to `/challenges` |
| Quiz Results | Latest attempt percentage and rolling average / average time from `quizAttempts` |
| Overall Progress | Bar uses `progressPercent` from solved labs vs `TOTAL_CHALLENGES` |
| Red vs Blue banner | `GET /api/redblue/my-games` filtered to `status === 'active'` |
| Challenge assignments | `GET /api/challenge-assignments/my` with countdown timers |
| AI Features Active | `GET /api/ai/status` when `ai_available` is true |

### 9.8 Instructor Dashboard Metrics (`GET /api/stats/instructor/dashboard`)

Returns: `total_students`, `quizzes_created` (assignment count), `questions_in_bank`, `avg_completion_rate` (sum of per-student solved labs vs `total_students * 10`), `class_performance` (per-`SKILL_BUCKETS` average score and count of students at 100%), and `total_challenges` (=10).

### 9.9 Admin Dashboard Metrics (`GET /api/stats/admin/dashboard`)

Returns: `total_users`, role distribution, `fixed_vulns` (total row count in `user_progress`), `challenge_usage` per lab with `attempts` (sum of `ChallengeState.attempt_count`) and `successes` (distinct users with `UserProgress` for that slug), plus `system_status`.

---

## 10. Leaderboards

SCALE provides two distinct leaderboard surfaces: the **challenge game leaderboard** via the legacy `game_challenge` router, and the **Red vs Blue per-game scores** maintained in `GameChallenge` (covered in detail in Section 14.3).

### 10.1 Challenge Leaderboard (`GET /api/challenge/leaderboard`)

**Endpoint:** `GET /api/challenge/leaderboard`  
**Handler:** `challenge_leaderboard()` in `backend/app/api/game_challenge.py`  
**Auth:** Yes (JWT required)  
**Router prefix:** `/api/challenge`

This endpoint returns a ranked list of participants in the challenge game layer. Rankings are computed from challenge completion counts and cumulative scores in `ChallengeState` and `UserProgress`. The response includes each ranked user's email (or identifier), the number of challenges completed, and optionally the aggregate attempt count and hints used.

**Response shape (representative):**

```json
{
  "leaderboard": [
    { "rank": 1, "user_id": 4, "email": "student@example.com", "challenges_completed": 8, "total_score": 800 },
    { "rank": 2, "user_id": 7, "email": "alice@example.com",   "challenges_completed": 6, "total_score": 600 }
  ]
}
```

**Ranking logic:** Users are ordered by `challenges_completed` (descending), then by `total_score` (descending) as a tiebreaker. `challenges_completed` is the count of distinct slugs in `user_progress` for the user. `total_score` correlates to the sum of completed-lab XP values (100 per lab) plus quiz average. Only approved users with at least one completion event appear in the leaderboard.

### 10.2 Red vs Blue Per-Game Scores

Each `GameChallenge` row stores `red_score` and `blue_score` as integer columns. Scores are updated in the same database transaction as each blue fix submission (Section 14.3). The `GET /api/redblue/game/{game_id}` endpoint returns the computed scores alongside team rosters and recent actions. `GET /api/redblue/games` (instructor/admin) lists all games with scores for a cross-game overview.

**Score increments:**

| Event | Score change |
|-------|--------------|
| Blue fix `fixed == true` | `blue_score += 1` |
| Blue fix `fixed == false` | `red_score += 1` |
| Red attack confirmed | No score change (sets phase to `awaiting_blue`) |

### 10.3 Defense Level Tiers as a Personal Leaderboard

The three-tier **Defense Level** (Beginner / Intermediate / Advanced) on each student's profile acts as a personal progress benchmark. Instructors can view each student's Defense Level via `GET /api/instructor/user/{id}/analytics`. Administrators can see aggregate Defense Level distributions in the admin dashboard.

### 10.4 Class Leaderboard (Instructor View)

The instructor dashboard (`GET /api/stats/instructor/dashboard`) returns `class_performance`, which is the nearest analog to a class-wide leaderboard: per-skill-bucket average scores and counts of students who have achieved 100% in that bucket. This allows instructors to identify which topic areas the class excels at and which require additional focus.

---

## 11. Security Event Logging

### 11.1 Event Pipeline

`log_security_event` in `security_logger.py` writes rows to `security_logs` with fields including `event_type`, `severity`, `payload`, `endpoint`, `ip_address`, `user_agent`, and `context_type` (`real` vs `challenge`). Lab routers pass `context_type="challenge"` for Red vs Blue and challenge traffic so operators can filter pedagogical noise from genuine platform events. `GET /api/security/logs` (admin) supports pagination and filters by context, date range, event type, and severity. `GET /api/security/logs/stats` returns aggregate counts.

### 11.2 Data Retention, Privacy, and Institutional Deployment

**Retention:** The platform implements no automatic log rotation or TTL. `security_logs` rows persist until an operator deletes them or drops the database volume. Payload columns may contain student-supplied attack strings (SQL fragments, XSS snippets, file paths).

**Lab vs production traffic:** Use `context_type` and the admin log filters to separate `challenge` events (expected lab behavior) from `real` platform events (login failures, upload anomalies). This does not anonymize student identity — `user_id` is stored when available.

**Privacy / GDPR considerations for institutional deployment:**

- A lawful basis and privacy notice should state that attack payloads and IP addresses are logged.
- Consider truncating or hashing `payload` in production configurations; the reference implementation stores full text for instructor review.
- Define a maximum log age (e.g., 90 days) and a purge job — not included in the reference stack.
- Admin user deletion (`DELETE /api/auth/admin/users/{id}`) does not automatically cascade-delete `security_logs`; operators must handle erasure requests manually.
- External AI keys (OpenAI, Serper) may send code snippets outside the institution; disable AI features if data residency requires it.

---

## 12. Messaging System

`Message` rows in the `messages` table store `sender_id`, `receiver_id`, `content`, `created_at`, and `is_read`. `GET /api/messages/contacts` returns the user list for composing new messages. `GET /api/messages/with/{user_id}` fetches a conversation thread. `POST /api/messages/send` creates a new message. `GET /api/messages/unread-count` is polled every 30 seconds by `Sidebar.tsx` and is used to display the unread badge in the navigation.

---

## 13. AI Services

### 13.1 Configuration

`OPENAI_API_KEY` and `SERPER_API_KEY` are read at startup. `GET /api/ai/status` returns `ai_available`, `openai_configured`, `serper_configured`, `features`, and `message`. When neither key is configured, AI-dependent endpoints degrade gracefully:

| Endpoint | Behavior without keys |
|----------|-----------------------|
| `POST /api/project/scan/ai` | Returns 503 with a message directing to standard scan |
| `POST /api/ai/mentor-chat` | Returns structured "not configured" fallback |
| `POST /api/quizzes/ai-generate-and-assign` | Falls back to static bank questions |
| `POST /api/quizzes/common-mistakes-quiz` | Uses `_common_mistakes_fallback` from the bank |

### 13.2 AI Mentor

`POST /api/ai/mentor-chat` accepts a challenge context and student question, calls the OpenAI chat completion API, and returns a structured coaching response. When only Serper is configured, web-search results are used to construct answers. The `ChallengeHintPanel.tsx` component surfaces this as a chat UI within each challenge page.

### 13.3 Code Analysis

`POST /api/ai/analyze-code` accepts `AICodeAnalyzeRequest` (code, language, vulnerability_type, severity, file, line) and returns a structured analysis with explanation, fix suggestion, and references. Uses OpenAI when available, otherwise Serper-enriched fallback.

### 13.4 AI Scan Enrichment

`POST /api/project/scan/ai` runs the standard scan then passes a subset of findings through the AI pipeline for natural-language explanations and recommended remediation steps.

---

## 14. Red vs Blue Team Mode

Red vs Blue mode is an instructor-led competitive layer on top of the same ten SCALE labs. `LAB_CHALLENGE_SLUGS` in `red_blue.py` maps integers 1–10 to challenge slugs. It is distinct from the legacy `/api/challenge/*` game router (`game_challenge.py`) but shares the same challenge lab assets.

### 14.1 Purpose and Participants

**Red team** members log synthetic attacks (payloads and impact descriptions) into `RedTeamAction` rows. **Blue team** members submit Python code fixes against the same lab; fixes are validated with `_verify_fix_improvement` (same `improvement_score` and `fixed` semantics as Section 5.2.1). **Instructors or administrators** create games and may end them. Students see only games they belong to via `GET /api/redblue/my-games`.

### 14.2 Game Lifecycle

1. **Create:** `POST /api/redblue/game/create` (instructor/admin) validates user IDs, enforces no overlap between red and blue rosters, checks `challenge_id ∈ [1,10]`, then sets any existing active games for that lab to `inactive`, creates two `Team` rows (`type=red|blue`), `TeamMember` rows, and a `GameChallenge` with `status=active`, `lab_challenge_id` set, and `started_at` timestamp.
2. **Play:** While `status == active`, red players call `POST /api/redblue/game/{game_id}/attack`; blue players call `POST /api/redblue/game/{game_id}/fix`. Both endpoints reject participants who are not on the correct team.
3. **Observe:** `GET /api/redblue/game/{game_id}` returns teams, members, recent actions, fixes, and computed scores. `GET /api/redblue/game/{game_id}/attacks?since_id=` returns new `RedTeamAction` rows with `id > since_id` for incremental polling.
4. **End:** `POST /api/redblue/game/{game_id}/end` (instructor/admin) sets `status` to `completed`.
5. **Instructor overview:** `GET /api/redblue/games` lists all games with scores.

### 14.3 Scoring Model

Red vs Blue uses turn-based round scoring. New games set `current_phase="awaiting_red"` and initialize `red_score` and `blue_score` to 0.

| Event | Score change | Notes |
|-------|--------------|-------|
| Red attack confirmed | None | Sets `current_phase="awaiting_blue"`; logs `RedTeamAction` with `status=confirmed`. |
| Blue fix `fixed == true` | `blue_score += 1` | Sandbox unittest pass; round advances. |
| Blue fix `fixed == false` | `red_score += 1` | Fix still vulnerable; round advances. |

After each blue submission, `current_phase` returns to `awaiting_red` and `current_round` increments. Points are not weighted by severity; each round has exactly one winner (+1). A fix with `improvement_score > 0` but `fixed == false` awards the round to red.

**Authoritative read path:** `_red_score_query` and `_blue_score_query` in `red_blue.py` return stored columns when `current_phase` is set (all instructor-led games). A legacy fallback counts `RedTeamAction` / `BlueTeamFix` rows directly only when `current_phase` is null (older rows). The columns are updated in the same transaction as fix submission, so drift should not occur unless data is edited manually.

### 14.4 Timing and Real-Time Model

There is no WebSocket. The live game UI (`RedBlueGamePage.tsx`) uses polling: `GET .../attacks?since_id=<last>` every few seconds to append new attacks. Fix submission is request/response. Ordering is by `RedTeamAction.id` / database timestamps.

### 14.5 Student Portal

`GET /api/redblue/my-games` joins `TeamMember` → `GameChallenge` and returns, for each participation, game id, lab title, team side, computed scores, and status. The student dashboard shows an amber banner when any returned game has `status === 'active'`, linking to `/redblue/game/:gameId`.

### 14.6 Failure and Edge Cases

- Invalid lab id or unknown user → HTTP 400/404 at creation.
- Game not active → attack/fix return 400.
- Wrong team → 403.
- Challenge directory missing in container → fix path returns 400 (`Cannot resolve challenge directory`).
- Sandbox Docker errors propagate like standard lab fixes (Section 22).

---

## 15. Complete API Reference

### 15.1 Route Summary

| Group | Prefix | Responsibility |
|-------|--------|----------------|
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
| Challenge assignments | `/api/challenge-assignments` | Timed instructor lab fix assignments |
| AI | `/api/ai` | Status, mentor chat, analyze-code |
| Game challenge (legacy) | `/api/challenge` | Legacy game endpoints, leaderboard, advanced hints |
| Attack | `/api/attack` | Attack simulation |
| Misconfig | `/api` | Misconfiguration mini-lab |

**Total routes:** 128 (including `GET /`).

### 15.2 Key Endpoint Specifications

---

#### POST /api/auth/register
**Auth:** No | **Roles:** Public (cannot register as admin)

**Request:**
```json
{ "email": "user@example.com", "password": "string", "role": "user" }
```
**Response (200):** `User` with `id`, `email`, `role`, `is_approved`.  
**Errors:** 400 duplicate email; 403 if role is admin.

---

#### POST /api/auth/login
**Auth:** No  
**Normal:** Validates bcrypt password, requires `is_approved`, returns JWT and sets HttpOnly cookie.  
**Broken-auth branch:** Query param `challenge=broken-auth` with `ENABLE_BROKEN_AUTH_CHALLENGE=true` runs SQLite in-memory vulnerable query.  
**Response:** `access_token`, `token_type`, `user_id`, `role`, `email`.  
**Errors:** 401 invalid credentials; 403 pending approval.

---

#### POST /api/auth/logout
**Auth:** No (cookie cleared)  
**Response:** `{ "ok": true }`  
**Side effects:** Deletes `access_token` cookie.

---

#### GET /api/auth/me
**Auth:** Yes  
**Response:** `UserSearchResponse` with `id`, `email`, `role`, `is_approved`.

---

#### POST /api/project/upload
**Auth:** Yes  
**Request:** multipart `file` (.zip only, max 50 MB).  
**Response:** `project_id`, `project_folder` path.  
**Logic:** Save zip, extract whitelisted extensions with traversal protection, create `Project` row.

---

#### POST /api/project/scan
**Auth:** Yes  
**Query:** `project_id`  
**Response:** findings, summary, risk, debug info; persists `ScanHistory`; starts background dependency scan thread.

---

#### GET /api/project/{project_id}/dependencies
**Auth:** Yes  
**Response:** Merged dependency vulnerability data from latest `vuln_summary.dependency_scan`.

---

#### POST /api/project/scan/ai
**Auth:** Yes  
**Errors:** 503 if neither `OPENAI_API_KEY` nor `SERPER_API_KEY` is configured.  
**Logic:** Runs standard scan then enriches findings with AI when keys exist.

---

#### POST /api/challenges/submit-fix
**Auth:** Yes  
**Note:** Sibling routes: `/submit-fix-xss`, `/submit-fix-csrf`, `/submit-fix-command-injection`, `/submit-fix-auth`, `/submit-fix-misc`, `/submit-fix-redirect`, `/submit-fix-traversal`, `/submit-fix-xxe`, `/submit-fix-storage`.  
**Request:** `{ "code": "..." }`  
**Response:** `success`, `logs`, `fixed`, `improvement_score`, `code_diff`.

---

#### DELETE /api/challenges/progress/{challenge_slug}
**Auth:** Yes  
**Logic:** Deletes `UserProgress` and `ChallengeState` for slug variants; recalculates learning progress; logs security event.

---

#### POST /api/challenges/mark-attack-complete
**Auth:** Yes  
**Query:** `challenge_type` — slug such as `sql-injection`, `xss`, etc.  
**Logic:** Calls `mark_challenge_complete` → inserts `UserProgress` without sandbox validation; runs `recalculate_learning_progress`.

---

#### GET /api/admin/config
**Auth:** Yes — any authenticated user (JWT required); no admin role check (intentional lab 6 misconfiguration — Section 5.2.2)  
**Response:** Pedagogical config JSON with `debug`, sample secrets, and filtered env keys.

---

#### GET /api/challenges/hints
**Auth:** Yes  
**Query:** `challenge_id`  
**Response:** List of hints with unlock flags based on `ChallengeState.hints_used`.

---

#### GET /api/challenges/replay/{challenge_slug}
**Auth:** Yes  
**Query:** `sample` boolean — if true, bypasses the completion check.  
**Errors:** 404 if no replay exists; 403 if not completed and not sample.

---

#### GET /api/report/pdf
**Auth:** Yes  
**Response:** PDF bytes `application/pdf`; filename `pentest_report_{safe_email}_{YYYYMMDD}.pdf`.  
**Errors:** 404 if user has no scan history.

---

#### POST /api/quiz/generate
**Auth:** Yes (`require_role('user')`)  
**Logic:** Dynamic quiz from scan context.

---

#### POST /api/quizzes/take
**Auth:** Yes  
**Logic:** Returns random question set from bank filtered by topic/difficulty.

---

#### POST /api/quizzes/ai-generate-and-assign
**Auth:** Instructor or admin  
**Body:** `AIQuizAssignRequest` — topic, difficulty, num_questions, student_ids, optional due_date.  
**Response:** `ai_generated`, `ai_questions_created`, `mixed_topics`.

---

#### GET /api/stats/progress/me
**Auth:** Yes  
**Response:** Learning payload plus `challenge_detail` bar chart rows.

---

#### GET /api/security/logs
**Auth:** Admin  
**Query:** filters for context, date range, event type, pagination.

---

#### GET /api/challenge/leaderboard
**Auth:** Yes  
**Handler:** `challenge_leaderboard()` in `game_challenge.py`  
**Response:** Ranked list of participants ordered by challenges completed (desc), then by total score (desc). See Section 10.1 for full details.

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

---

#### POST /api/instructor/user/{id}/reset-progress
**Auth:** Instructor or admin  
**Logic:** Deletes `UserProgress`, `ChallengeState`, `UserAnswer`, `QuizAttempt`, `UserLearningProgress` for the student.

---

#### POST /api/challenge-assignments/create
**Auth:** Instructor or admin  
**Body:** `ChallengeAssignmentCreate` — `challenge_slug`, `title`, `instructions`, `time_limit_minutes` (10–240), optional `due_date`, `student_ids[]`.  
**Logic:** Validates slug against ten labs; creates `ChallengeAssignment` + `ChallengeAssignmentStudent` rows with `status=assigned`.

---

#### POST /api/challenge-assignments/{assignment_id}/start
**Auth:** Assigned student  
**Logic:** Sets `started_at`, `status=in_progress`; rejects if past due or already started.

---

#### POST /api/challenge-assignments/{assignment_id}/submit-fix
**Auth:** Assigned student (in progress)  
**Body:** `{ "submitted_code": "..." }`  
**Logic:** Sandbox via `_verify_fix_improvement`; sets `score` 100/0, `sandbox_passed`, `status=passed|failed`; expires on timeout.

---

#### POST /api/quizzes/assignments/{assignment_id}/start
**Auth:** Assigned student  
**Response:** `QuizAssignmentStartResponse` with deadline timestamp when `time_limit_minutes` is set.

---

#### POST /api/quizzes/common-mistakes-quiz
**Auth:** Authenticated student  
**Logic:** Aggregates wrong `UserAnswer` rows; OpenAI generates targeted MCQs or `_common_mistakes_fallback` from bank; may save new questions with `targets_mistake`.

---

#### POST /api/quizzes/assign-mistakes-quiz
**Auth:** Instructor or admin  
**Body:** `{ "student_id": int, "num_questions": int }`  
**Logic:** Generates mistakes payload for student and creates a `QuizAssignment` assigned to that student.

---

## 16. Frontend Pages Reference

All pages are located in `frontend/src/pages/`. Routes match `App.tsx`. The `ChallengeHintPanel` component (not a page) uses `POST /api/challenge/hint` (game_challenge router) for leveled hints and `POST /api/ai/mentor-chat` for the AI mentor; this is distinct from `GET /api/challenges/hints` and `POST /api/challenges/hints/use` on the main challenges router.

---

### LandingPage
**Route:** `/` | **Role:** Public  
**Purpose:** Entry page that checks authentication state and redirects authenticated users to their role-appropriate dashboard.  
**API calls:** None directly; relies on sessionStorage check.

---

### LoginPage
**Route:** `/login` | **Role:** Public  
**Purpose:** User authentication form with email/password inputs. Stores JWT, role, user_id, and user_email to sessionStorage on success.  
**API calls:** `POST /api/auth/login`

---

### RegisterPage
**Route:** `/register` | **Role:** Public  
**Purpose:** New user registration with email, password, confirm password, and role selection (user or instructor).  
**API calls:** `POST /api/auth/register`

---

### DashboardHomePage
**Route:** `/home` | **Role:** user, instructor, admin  
**Purpose:** Central student dashboard showing Defense Level, XP score, challenge progress, quiz results, active Red vs Blue games, and open timed assignments. Includes PDF export and AI status indicator.  
**API calls:** `GET /api/stats/progress/me`, `GET /api/challenges/progress`, `GET /api/quizzes/attempts`, `GET /api/report/pdf`, `GET /api/ai/status`, `GET /api/redblue/my-games`, `GET /api/challenge-assignments/my`

---

### ChallengesListPage
**Route:** `/challenges` | **Role:** user, instructor, admin  
**Purpose:** Grid of ten challenge cards with completion status badges, per-lab reset controls, and links to tutorial/attack/fix sub-routes.  
**API calls:** `GET /api/challenges/progress` (via child components)

---

### MessagesPage
**Route:** `/messages` | **Role:** user, instructor, admin  
**Purpose:** Peer messaging interface with contact list, conversation thread view, and message compose field.  
**API calls:** `GET /api/messages/contacts`, `GET /api/messages/with/${contact.id}`, `POST /api/messages/send`

---

### Scanner
**Route:** `/scanner` | **Role:** user, instructor, admin  
**Purpose:** Project scanner with ZIP file upload or Git URL input. Displays findings, severity chart, fix recommendations, dependency advisories, and AI code analysis panel.  
**API calls:** `POST /api/project/upload`, `POST /api/project/scan`, `POST /api/project/scan-from-git`, `POST /api/ai/analyze-code`

---

### AttackLab
**Route:** `/attack-lab` | **Role:** user, instructor, admin  
**Purpose:** General-purpose attack simulation lab using a payload input and the attack simulator endpoint. Displays a stepper timeline of the simulated attack.  
**API calls:** `POST /api/attack/simulate`

---

### SqlInjectionTutorialPage
**Route:** `/challenges/1/tutorial` | **Role:** user, instructor, admin  
**Purpose:** Video and text tutorial explaining SQL injection concepts, vulnerable query patterns, and parameterization defenses. Includes voiced MP4 tutorial playback.

---

### SqlInjectionAttackPage
**Route:** `/challenges/1/attack` | **Role:** user, instructor, admin  
**Purpose:** Interactive SQL injection attack form against the vulnerable login endpoint. Students enter injection payloads and observe the successful bypass.  
**API calls:** `POST /api/challenges/vulnerable-login`, `POST /api/challenges/mark-attack-complete`

---

### SqlInjectionFixPage
**Route:** `/challenges/1/fix` | **Role:** user, instructor, admin  
**Purpose:** Code editor pre-loaded with the vulnerable `app.py` source. Students edit the query to use parameterized statements and submit for sandbox validation.  
**API calls:** `POST /api/challenges/submit-fix`

---

### XssTutorialPage / XssAttackPage / XssFixPage
**Routes:** `/challenges/2/tutorial`, `/challenges/2/attack`, `/challenges/2/fix` | **Role:** user, instructor, admin  
**Purpose:** Three-stage XSS challenge. Tutorial explains DOM manipulation and sanitization. Attack page lets students post raw script tags into the comment section. Fix page validates HTML escaping.  
**Key API calls:** `GET /api/challenges/xss/comments`, `POST /api/challenges/xss/comments`, `POST /api/challenges/mark-attack-complete`, `POST /api/challenges/submit-fix-xss`

---

### CsrfTutorialPage / CsrfAttackPage / CsrfFixPage
**Routes:** `/challenges/3/tutorial`, `/challenges/3/attack`, `/challenges/3/fix` | **Role:** user, instructor, admin  
**Purpose:** CSRF challenge using the external CSRF database. Attack page auto-submits a hidden form to trigger unauthorized bank transfers. Fix page validates CSRF token enforcement.  
**Key API calls:** `GET /api/challenges/csrf/accounts`, `POST /api/challenges/csrf/transfer`, `POST /api/challenges/csrf/reset`, `POST /api/challenges/mark-attack-complete`, `POST /api/challenges/submit-fix-csrf`

---

### CommandChallengePage
**Route:** `/challenges/4/:tab` | **Role:** user, instructor, admin  
**Purpose:** Tab-based wrapper for the Command Injection challenge. Renders Tutorial, Attack, or Fix sub-page based on the `:tab` URL parameter.  
**Child components:** `CommandInjectionTutorialPage`, `CommandInjectionAttackPage`, `CommandInjectionFixPage`

---

### BrokenAuthTutorialPage / BrokenAuthAttackPage / BrokenAuthFixPage
**Routes:** `/challenges/5/tutorial`, `/challenges/5/attack`, `/challenges/5/fix` | **Role:** user, instructor, admin  
**Purpose:** Broken Authentication challenge. Attack page submits credentials to the in-memory SQLite broken-auth branch, exposing the executed query and result. Fix page validates bcrypt hashing.  
**Key API calls:** `POST /api/auth/login` (with `?challenge=broken-auth`), `POST /api/challenges/mark-attack-complete`, `POST /api/challenges/submit-fix-auth`

---

### SecurityMiscTutorialPage / SecurityMiscAttackPage / SecurityMiscFixPage
**Routes:** `/challenges/6/tutorial`, `/challenges/6/attack`, `/challenges/6/fix` | **Role:** user, instructor, admin  
**Purpose:** Security Misconfiguration challenge. Attack page calls `GET /api/admin/config` with a student JWT, demonstrating missing authorization on a sensitive endpoint. Fix page validates role enforcement.  
**Key API calls:** `GET /api/admin/config`, `POST /api/challenges/mark-attack-complete`, `POST /api/challenges/submit-fix-misc`

---

### InsecureStorageChallengePage
**Route:** `/challenges/7/:tab` | **Role:** user, instructor, admin  
**Purpose:** Tab-based wrapper for the Insecure Storage challenge.  
**Child components:** `InsecureStorageTutorialPage`, `InsecureStorageAttackPage`, `InsecureStorageFixPage`

---

### DirectoryTraversalChallengePage
**Route:** `/challenges/8/:tab` | **Role:** user, instructor, admin  
**Purpose:** Tab-based wrapper for the Directory Traversal challenge.  
**Child components:** `DirectoryTraversalTutorialPage`, `DirectoryTraversalAttackPage`, `DirectoryTraversalFixPage`

---

### XxeChallengePage
**Route:** `/challenges/9/:tab` | **Role:** user, instructor, admin  
**Purpose:** Tab-based wrapper for the XXE challenge.  
**Child components:** `XxeTutorialPage`, `XxeAttackPage`, `XxeFixPage`

---

### RedirectChallengePage
**Route:** `/challenges/10/:tab` | **Role:** user, instructor, admin  
**Purpose:** Tab-based wrapper for the Unvalidated Redirect challenge.  
**Child components:** `RedirectTutorialPage`, `RedirectAttackPage`, `RedirectFixPage`

---

### AttackSuccessPage
**Route:** `/challenges/attack-success` | **Role:** user, instructor, admin  
**Purpose:** Displays the attack success confirmation with narrative XP gained (display only), attack replay option, and a link to the fix phase. Reads `typeConfig` for the challenge slug passed via query parameter.  
**API calls:** `GET /api/challenges/progress`

---

### RedBlueGamePage
**Route:** `/redblue/game/:gameId` | **Role:** user, instructor, admin  
**Purpose:** Live Red vs Blue game interface. Red team players enter attack payloads; blue team players submit fix code. Polls for new attacks via `since_id`. Displays real-time round scores and team rosters.  
**API calls:** `GET /api/redblue/game/${gameId}`, `POST /api/redblue/game/${gameId}/attack`, `POST /api/redblue/game/${gameId}/fix`, `GET /api/redblue/game/${gameId}/attacks`, `POST /api/redblue/game/${gameId}/end`

---

### StudentQuizPage
**Route:** `/quiz` | **Role:** user only  
**Purpose:** Multi-mode quiz interface offering practice quizzes, instructor assignments, scan-based quizzes, and adaptive common-mistakes quizzes. Displays per-question timer for timed assignments.  
**API calls:** `POST /api/quizzes/take`, `GET /api/quizzes/assignments/student`, `GET /api/quizzes/assignments/${id}/take`, `POST /api/quizzes/assignments/${id}/start`, `POST /api/quizzes/submit-answer`, `POST /api/quizzes/submit-attempt`, `POST /api/quiz/generate`, `POST /api/quizzes/common-mistakes-quiz`, `GET /api/quizzes/wrong-answer-count`

---

### RedBlueMyGamesPage
**Route:** `/redblue/my-games` | **Role:** user only  
**Purpose:** Lists all Red vs Blue games the student participates in, showing team side, scores, lab title, and status. Links to the live game page.  
**API calls:** `GET /api/redblue/my-games`

---

### ChallengeAssignmentPage
**Route:** `/assignment/:assignmentId` | **Role:** user only  
**Purpose:** Timed lab assignment interface. Shows assignment details, countdown timer, a code editor pre-loaded from the challenge source, and submit controls. Enforces time limits and marks the assignment expired on timeout.  
**API calls:** `GET /api/challenge-assignments/${assignmentId}/status`, `POST /api/challenge-assignments/${assignmentId}/start`, `POST /api/challenge-assignments/${assignmentId}/submit-fix`

---

### InstructorDashboardPage
**Route:** `/instructor/dashboard` | **Role:** instructor, admin  
**Purpose:** Instructor control center. Shows student list, per-student analytics panel, class performance stats, Red vs Blue game management, and timed challenge assignment creation form.  
**API calls:** `GET /api/auth/users`, `GET /api/stats/instructor/dashboard`, `GET /api/instructor/user/${id}/analytics`, `POST /api/instructor/user/${id}/reset-progress`, `GET /api/redblue/games`, `DELETE /api/redblue/game/${id}`, `GET /api/challenge-assignments/instructor`, `POST /api/challenge-assignments/create`, `POST /api/quizzes/assign-mistakes-quiz`

---

### InstructorQuizPage
**Route:** `/instructor/quiz` | **Role:** instructor, admin  
**Purpose:** Quiz bank management with tabs for browsing questions, creating questions manually, AI-generating question sets, and creating/managing assignments with time limits and due dates.  
**API calls:** `GET /api/quizzes/questions`, `POST /api/quizzes/questions`, `PUT /api/quizzes/questions/${id}`, `DELETE /api/quizzes/questions/${id}`, `GET /api/quizzes/assignments/instructor`, `POST /api/quizzes/assignments`, `DELETE /api/quizzes/assignments/${id}`, `POST /api/quizzes/ai-generate-and-assign`, `POST /api/quizzes/generate-ai-preview`, `GET /api/auth/users`

---

### InstructorAssignmentResultsPage
**Route:** `/instructor/assignment/:assignmentId/results` | **Role:** instructor, admin  
**Purpose:** Per-student results view for a timed lab assignment. Shows each student's status (assigned / in_progress / passed / failed / expired), score, sandbox result, and submitted code.  
**API calls:** `GET /api/challenge-assignments/${assignmentId}/results`

---

### RedBlueCreatePage
**Route:** `/redblue/create` | **Role:** instructor, admin  
**Purpose:** Game creation form for selecting a lab challenge (1–10), naming the teams, and assigning students to red or blue rosters.  
**API calls:** `GET /api/auth/users`, `GET /api/redblue/games`, `POST /api/redblue/game/create`

---

### AdminStatsPage
**Route:** `/admin/stats` | **Role:** admin  
**Purpose:** Platform-wide statistics dashboard. Displays total users, role distribution, fixed vulnerabilities count, challenge usage per lab (attempts and successes), and system status.  
**API calls:** `GET /api/stats/admin/dashboard`

---

### AdminDashboardPage
**Route:** `/admin/dashboard` | **Role:** admin  
**Purpose:** Administrator control panel. Manages user accounts (approve, change role, delete), creates new admin accounts, and reviews pending instructor registrations.  
**API calls:** `GET /api/auth/users`, `GET /api/auth/admin/pending`, `POST /api/auth/admin/approve/${id}`, `PUT /api/auth/admin/users/${id}/role`, `DELETE /api/auth/admin/users/${id}`, `POST /api/auth/admin/create-admin`

---

### SecurityLogsPage
**Route:** `/admin/logs` | **Role:** admin  
**Purpose:** Security event log viewer with filters for severity, event type, context type (real vs challenge), and date range. Supports pagination and expandable row detail.  
**API calls:** `GET /api/security/logs`, `GET /api/security/logs/stats`

---

### UnderConstructionPage
**Route:** `/under-construction` | **Role:** user, instructor, admin  
**Purpose:** Placeholder page for features in development.

---

### Child Pages (Compose-Only — No Direct App.tsx Route)

These pages are imported and rendered by their wrapper page components:

| Page | Parent Route |
|------|-------------|
| CommandInjectionTutorialPage | `/challenges/4/:tab` |
| CommandInjectionAttackPage | `/challenges/4/:tab` |
| CommandInjectionFixPage | `/challenges/4/:tab` |
| InsecureStorageTutorialPage | `/challenges/7/:tab` |
| InsecureStorageAttackPage | `/challenges/7/:tab` |
| InsecureStorageFixPage | `/challenges/7/:tab` |
| DirectoryTraversalTutorialPage | `/challenges/8/:tab` |
| DirectoryTraversalAttackPage | `/challenges/8/:tab` |
| DirectoryTraversalFixPage | `/challenges/8/:tab` |
| XxeTutorialPage | `/challenges/9/:tab` |
| XxeAttackPage | `/challenges/9/:tab` |
| XxeFixPage | `/challenges/9/:tab` |
| RedirectTutorialPage | `/challenges/10/:tab` |
| RedirectAttackPage | `/challenges/10/:tab` |
| RedirectFixPage | `/challenges/10/:tab` |

---

## 17. Environment and Configuration

### 17.1 Environment Variables

All variables are read from `.env` (root) or `backend/.env`. Copy `.env.example` to `.env` before first run.

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | (empty) | Enables OpenAI for mentor, quiz generation, scan AI |
| `SERPER_API_KEY` | (empty) | Web-search-backed AI fallback |
| `AI_SERVICE_URL` | `http://ai_service:8001` | Internal URL for template AI microservice |
| `DATABASE_URL` | `mysql+pymysql://user:password@main_db/scale_db` | SQLAlchemy main database connection |
| `SQLI_DATABASE_URL` | `...@challenge_db_sqli/testdb` | SQL injection challenge database |
| `CSRF_DATABASE_URL` | `...@challenge_db_csrf/csrfdb` | CSRF challenge database |
| `SECRET_KEY` | `scale_graduation_project_secret_key` | JWT signing secret — **rotate before any network exposure** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `600` | JWT lifetime in minutes |
| `ENABLE_BROKEN_AUTH_CHALLENGE` | `true` | Enables SQLite in-memory vulnerable login branch |
| `SANDBOX_MAX_CODE_CHARS` | `200000` | Maximum uploaded fix source size |
| `SANDBOX_RUN_TIMEOUT` | `25` | Sandbox container timeout in seconds |
| `VITE_API_URL` | `http://localhost:8000` | Frontend Axios base URL |

### 17.2 Docker Volumes

`scale_db_data` is the named volume that persists MySQL data for `main_db`. Bind mounts mount the backend code directory and all ten challenge directories into the backend container.

### 17.3 Port Reference

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Backend API | 8000 | 8000 |
| Frontend (Vite) | 5173 | 5173 |
| AI Service | 8001 | 8001 |
| Main DB | 3306 | 3306 |
| SQL Injection DB | 3307 | 3306 |
| CSRF DB | 3308 | 3306 |

---

## 18. Setup and Deployment

### 18.1 Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin) installed and running.
- Minimum 4 GB RAM recommended for Docker-in-Docker workloads.
- Git for repository cloning.

### 18.2 First-Time Setup

```bash
git clone <repository-url>
cd grad-project
cp .env.example .env          # edit .env to set API keys and secrets
docker compose up --build
```

Open `http://localhost:5173` in a browser. Voiced lab tutorials require the `Web-Videos/` folder to exist in the project root (mounted read-only into the frontend container as `/app/web-videos`).

> **WARNING — DEFAULT CREDENTIALS (DEVELOPMENT ONLY)**
> `seed_db.py` creates `admin@scale.edu` / `AdminPass123!` and `instructor@scale.edu` / `TeachPass123!`.
> These are intentional for local demo and examination but **must be changed or disabled before any network-exposed deployment**.
> Also rotate `SECRET_KEY`, MySQL passwords in `.env`, and delete or re-seed accounts if the stack was ever reachable from the internet.

### 18.3 Enabling AI Features

Set `OPENAI_API_KEY` or `SERPER_API_KEY` in `.env` or `backend/.env`. Check availability via `GET /api/ai/status` after startup. The platform operates normally without either key — AI-dependent features degrade gracefully.

### 18.4 Development Workflow

- Backend: `--reload` flag in the startup command enables hot-reload for Python changes.
- Frontend: Vite HMR (Hot Module Replacement) is active by default.
- Logs: `docker logs scale_application-backend-1 -f`

### 18.5 Common Issues

| Issue | Resolution |
|-------|------------|
| Backend DB retry loop at startup | Wait for MySQL healthchecks; check `depends_on` in `docker-compose.yml` |
| Docker socket permission denied | Ensure `/var/run/docker.sock` is mounted; verify Docker is running |
| CORS errors in browser | Check that `VITE_API_URL` matches the backend origin in `main.py` CORS list |
| Sandbox `run_tests.sh` line ending errors | Convert challenge `run_tests.sh` files to Unix line endings (LF) |
| `PROJECT_STORAGE_ROOT` errors | Ensure the uploads directory exists and has write permissions |
| Missing tutorial videos | Place `.mp4` files in `Web-Videos/` in the project root |

### 18.6 Production Considerations

- Rotate `SECRET_KEY`, database passwords, and all default seeded credentials.
- Terminate TLS at a reverse proxy (nginx, Traefik, Cloudflare); enforce HSTS.
- Apply per-IP rate limits on `/api/auth/login` and `/api/project/scan`.
- Restrict Docker socket access; consider a dedicated builder host.
- Bind MySQL ports to the internal network only (remove host port mappings for DBs in production).
- Ship `security_logs` to a SIEM; alert on repeated 401/403 events.

### 18.7 Dependency Pinning and Reproducible Builds

> **WARNING — UNPINNED DEPENDENCIES**
> `backend/requirements.txt` pins only `bcrypt==4.0.1`; FastAPI, SQLAlchemy, Semgrep, and most other Python packages are unpinned. `frontend/package.json` uses semver ranges. Running `docker compose up --build` months later may pull newer package versions and break silently.

**Before any production or long-term demo:**

1. Capture `pip freeze > backend/requirements.lock.txt` from a known-good container.
2. Commit `frontend/package-lock.json` and use `npm ci` in the frontend Dockerfile for immutable Node installs.
3. Tag the Docker images with the lockfile snapshot date in your deployment notes.

---

## 19. Known Limitations and Technical Debt

| # | Limitation | Impact | Mitigation / Workaround | Future Direction |
|---|------------|--------|-------------------------|-----------------|
| 1 | Two parallel quiz systems (`/api/quizzes` vs `/api/quiz`) | Operators must learn two URL namespaces; duplicated concepts | Document which UI uses which; both are documented in Section 8 | Unify into one router or deprecate `/api/quiz` behind a facade |
| 2 | Legacy `quiz_assignments.question_ids` comma-separated text alongside normalized tables | Dual storage paths during migration | New assignments use `quiz_assignment_questions`; legacy column retained for compatibility | Remove legacy text columns once all readers use normalized tables |
| 3 | Dashboard "XP" / `currentXp` computed client-side | Not auditable for grading; refresh can desync | Treat as informal only; use `QuizAttempt` and `UserProgress` for official metrics | Persist aggregate XP server-side if needed |
| 4 | Defense Level label must reflect backend `level` (`user_learning_progress`) | Confusing if stale or derived twice | Trust `GET /api/stats/progress/me`; the card reads `learning.level` directly | Remove any duplicate client "level" logic if introduced |
| 5 | `MainLayout` polls `/api/messages/unread-count` on an interval; no WebSocket | Extra HTTP traffic; not real-time | Acceptable for small cohorts; increase interval if needed | WebSocket or SSE for unread counts |
| 6 | Command injection lab executes shell-related behavior on the backend host path | Pedagogical risk if misconfigured | Deploy only in isolated VMs; restrict who can reach `/api/challenges/ping` | Run ping lab in a dedicated sandbox with no host network |
| 7 | JWT stored in `sessionStorage` and mirrored in `Authorization: Bearer` | Same-origin XSS can exfiltrate the token immediately | Rely on HttpOnly cookie only; interim: strict CSP, no `dangerouslySetInnerHTML` in SCALE UI | Implement cookie-only session; remove Bearer-from-storage path |
| 8 | Uploading the SCALE repository as a ZIP scans first-party code | False positives and noise | Instruct students to upload only their own app | Add ignore patterns to scanner entrypoint |
| 9 | Dependency scanner caps at 50 packages (`MAX_DEPS_TO_QUERY`) | Large monorepos may miss advisories | Run focused scans on service subfolders | Raise cap with pagination or batch OSV |
| 10 | Red vs Blue fix resolution depends on `/app/challenges/challenge-{slug}` mounts | Wrong compose layout → 400 on fix | Verify bind mounts in `docker-compose.yml` match `challenge-*` directory names | Health-check endpoint listing resolvable challenge dirs |
| 11 | Dual APIs `/api/redblue` and `/api/challenge` | Two mental models for "game" features | Prefer documented `/api/redblue` for instructor games; use `/api/challenge` only for hint/leaderboard flows | Deprecate or merge routers |
| 12 | Tutorial videos require `Web-Videos/` mount | Missing folder → empty tutorial player | Ensure `Web-Videos/*.mp4` exist and compose mounts `./Web-Videos:/app/web-videos:ro` | CDN or static asset pipeline for production builds |
| 13 | AI features require external API keys | No AI without key | Rely on Serper-only or standard scan; `GET /api/ai/status` surfaces availability | Self-hosted models |
| 14 | Semgrep CLI optional in backend image | Scan falls back to regex-only if `semgrep` binary missing | Install via `requirements.txt`; check `scanner_engines.semgrep` in scan response | Bake Semgrep into backend Dockerfile explicitly and verify in CI |

---

## 20. Security Analysis

This section addresses both the intentionally vulnerable teaching surfaces and the security posture of the platform that hosts them. SCALE is a high-trust operator environment: the backend holds the Docker socket, database credentials, and JWT signing keys.

### 20.1 Intentional Vulnerabilities (Pedagogical)

| Component | Intended Weakness | Bounded How | Learning Objective |
|-----------|------------------|-------------|-------------------|
| `auth.py` broken-auth branch | SQLite in-memory string interpolation | `ENABLE_BROKEN_AUTH_CHALLENGE`; separate from production users | SQL injection in authentication |
| `challenge-*/app.py` | Per-lab OWASP flaws | Only mounted paths; not exposed as generic RCE on host | Category-specific exploitation |
| `misconfig.py` | Missing authorization on `/api/admin/config` | Any authenticated user (JWT required); no admin role check — see §5.2.2 | Misconfiguration discovery |
| Insecure storage lab | Plaintext in-memory dict | Process-local; resets on restart | Storage anti-patterns |
| CSRF / SQLi challenge DBs | Intentionally weak queries | Isolated MySQL instances on 3307/3308 | Database-layer effects |

### 20.2 Platform Security Posture (Controls in Place)

- **Passwords:** bcrypt via passlib; no plaintext storage for production users.
- **Authentication:** JWT (HS256) with `SECRET_KEY`; `get_current_user` validates Bearer and cookie.
- **Authorization:** `require_role` on sensitive routers; admin-only user management.
- **Transport:** Development assumes HTTPS termination in front of Compose in production.
- **CORS:** Explicit origin allowlist with credentials (Section 3.4).
- **Input validation:** Upload size, extension allowlists, path traversal checks on extraction.
- **Audit:** `security_logs` with `context_type` for lab vs real traffic.

### 20.3 Threat Model (STRIDE on Primary Surfaces)

| Attack Surface | S | T | R | I | D | E | Notes |
|----------------|---|---|---|---|---|---|-------|
| JWT in sessionStorage | ✓ | — | — | ✓ | — | — | Stolen token → session replay until expiry. HttpOnly cookie exists but SPA sends Bearer from storage — cookie-only mitigation not implemented. |
| Docker socket on backend | — | ✓ | ✓ | ✓ | ✓ | ✓ | Critical: container escape or malicious Dockerfile could affect host. |
| Sandbox escape / malicious student code | — | ✓ | ✓ | ✓ | ✓ | ✓ | Mitigated by disposable containers, `scale_net` isolation, CPU/mem/pid limits; not a full hypervisor boundary. |
| Same-origin XSS in SPA | ✓ | — | — | ✓ | — | — | If XSS existed in SCALE UI, token theft is immediate. |
| OSV.dev dependency | — | — | ✓ | — | ✓ | — | Supply-chain integrity of OSV responses; TLS transport only. |
| MySQL | — | ✓ | ✓ | ✓ | ✓ | — | Network exposure via published ports; default passwords in compose are development only. |
| Admin / instructor actions | ✓ | — | ✓ | — | — | — | Role misuse; relies on correct JWT claims. |

### 20.4 Residual Risks (Operational)

1. **Docker socket** (`/var/run/docker.sock`): grants equivalent capability to root on the host. Must not be exposed in untrusted multi-tenant production without strong isolation (separate host, rootless Docker, or remote builder API with policy).
2. **No global rate limiting** on API endpoints: brute-force login and DoS are possible. Mitigate with reverse-proxy limits.
3. **Sandbox and host shared kernel**: student code runs in containers. Mitigate with kernel updates and minimal images.
4. **Command injection lab** (`/api/challenges/ping`) runs on the backend host path. Mitigate by isolating to a dedicated worker.
5. **JWT in `sessionStorage`:** same-origin script can exfiltrate immediately. Short TTL is insufficient. Documented mitigation (HttpOnly-only, no Bearer from storage) is not implemented — treat as open finding for production.

### 20.5 Recommendations for Production Deployment

| Risk | Mitigation |
|------|------------|
| Docker socket | Dedicated builder host; no student-facing shell; audit `docker` API usage |
| JWT | Required fix: HttpOnly session cookie only; remove JWT from `sessionStorage` and stop setting `Authorization` from client storage; add CSRF on POST/PUT/DELETE. Current code does not do this. Rotate `SECRET_KEY`. |
| TLS | Terminate TLS at reverse proxy; enforce HSTS |
| Database | Non-default credentials; bind MySQL to internal network only |
| Rate limiting | Per-IP limits on `/api/auth/login` and expensive endpoints (`/api/project/scan`) |
| Observability | Ship `security_logs` to SIEM; alert on repeated 401/403 |

---

## 21. Testing and Verification Strategy

### 21.1 What Is Tested Automatically Today

**Lab correctness:** Each `challenge-*` directory includes `run_tests.sh` and Python unittest modules that the sandbox executes after every fix submission. These tests are the authoritative signal for `fixed` and for `improvement_score` (Section 5.2.1).

**Platform codebase:** The repository does not ship a dedicated pytest suite for FastAPI route handlers, React components, or end-to-end browser flows. Verification of the host application relies on documented manual exercise.

### 21.2 Manual Verification Performed (Development / Release Candidate)

The following paths were exercised manually during recent development (May 2026):

| Area | Scenario Verified | Expected Outcome |
|------|-------------------|------------------|
| Auth and RBAC | Student login; instructor pending approval; admin role change; `ProtectedRoute` 403 for wrong role | JWT issued; dashboards route by role; forbidden routes blocked |
| Scanner — happy path | Upload ZIP → `POST /api/project/scan` | Merged Semgrep + regex findings; `scanner_engines.semgrep` flag present; `ScanHistory` row written |
| Scanner — OSV degradation | Scan with OSV unreachable (simulated timeout) | Static findings still returned; dependency section partial or empty |
| Scanner — Git | `POST /api/project/scan-from-git` with public repo URL | Clone + scan completes or returns structured error for bad URL |
| Sandbox — pass | Submit corrected `app.py` for SQLi lab | `fixed: true`, `improvement_score: 100`, unittest logs show `OK` |
| Sandbox — fail | Submit still-vulnerable code | `fixed: false`, `improvement_score` between 0–99, logs show failing test names |
| Sandbox — timeout | Oversized/slow code near `SANDBOX_RUN_TIMEOUT` | HTTP 200 with `success: false` and timeout text in logs |
| Timed lab assignment — expire | Start assignment, wait past `time_limit_minutes`, submit fix | 403 "Time limit exceeded"; student row `status=expired` |
| Timed lab assignment — pass | Start → submit passing fix within window | `score: 100`, `sandbox_passed: true`, `status=passed` |
| Quiz assignment — timer | Instructor assignment with `time_limit_minutes`; student start → take → submit | Deadline enforced; attempt stored in `quiz_attempts` |
| Mistakes quiz | Student with prior wrong `UserAnswer` rows → `POST /api/quizzes/common-mistakes-quiz` | Returns targeted questions; fallback bank path when OpenAI absent |
| Leaderboard | `GET /api/challenge/leaderboard` after multiple students complete challenges | Returns ranked list ordered by challenges_completed (desc) |
| Red vs Blue | Create game → confirmed red attack → blue fix pass/fail | Phase transitions `awaiting_red` ↔ `awaiting_blue`; `blue_score` or `red_score` increments by 1 per round |
| Misconfig lab | Logged-in student calls `GET /api/admin/config` | 200 with config JSON; not callable without JWT |
| Admin config vs overview | Student gets 403 on `GET /api/admin/overview`; student gets 200 on `/api/admin/config` | Confirms auth gap is lab-specific, not a global admin bypass |

### 21.3 Example Sandbox Responses (SQL Injection Lab)

**Passing fix:**
```json
{
  "success": true,
  "fixed": true,
  "improvement_score": 100,
  "message": "All tests passed! Challenge completed.",
  "test_output": "Ran 3 tests in 0.042s\n\nOK\n"
}
```

**Failing fix (still injectable):**
```json
{
  "success": false,
  "fixed": false,
  "improvement_score": 33,
  "message": "Tests failed. Review the output and try again.",
  "test_output": "FAIL: test_login_still_vulnerable\n\nFAILED (failures=1)\n"
}
```

### 21.4 Known Untested or Lightly Tested Paths

| Path | Risk | Notes |
|------|------|-------|
| `POST /api/quizzes/ai-generate-and-assign` OpenAI failure → Serper → static bank fallback | Medium | Exercised ad hoc; no automated assertion of fallback chain |
| `POST /api/project/scan-from-git` private repos / auth | Low | Public clone only tested |
| `POST /api/quizzes/assign-mistakes-quiz` (instructor push) | Medium | Happy path manually verified once |
| Concurrent Red vs Blue games on same lab | Low | Creation deactivates prior active game; race not stress-tested |
| Full 128-route matrix | High | Checklist covers representative routes, not exhaustive combinatorics |
| Leaderboard under high concurrency | Low | Verified functional; not load-tested |

### 21.5 Recommended Manual Checklist (Minimum Before Demo)

| Area | Check |
|------|-------|
| Auth | Register student; instructor pending; admin approves; login; logout clears session; tab isolation. |
| Scanner | Upload valid ZIP; scan returns findings; Dependencies tab populates or degrades gracefully. |
| Labs | Spot-check attack + sandbox fix pass for at least two categories. |
| Quizzes | Bank quiz; instructor timed assignment; optional mistakes quiz. |
| Assignments | Instructor creates timed lab assignment; student completes or expires. |
| Leaderboard | Verify `GET /api/challenge/leaderboard` returns ranked data. |
| Red vs Blue | Create game; attack phase; fix round scoring; end game. |
| Admin | Security logs filter; user role change; `/api/admin/overview` admin-only. |
| AI (optional) | `GET /api/ai/status`; mentor fallback when keys absent. |

### 21.6 Coverage and CI (Future Work)

| Target | Suggested Approach |
|--------|-------------------|
| API | pytest + `httpx.AsyncClient` against FastAPI `TestClient`; cover auth, RBAC 403, sandbox mock, assignment expiry, leaderboard ranking |
| Frontend | Vitest + React Testing Library for `ProtectedRoute`, `ScanContext`, assignment countdown |
| E2E | Playwright for login → scan → quiz → assignment (optional) |

For a teaching deployment, no global percentage is mandated. For a maintained product, aim for ≥70% line coverage on `backend/app/api` and smoke E2E on auth and scan.

---

## 22. Operational Failure Modes and Error Handling

| Failure | Observable Behavior | User / Operator Impact | Recovery |
|---------|--------------------|-----------------------|----------|
| **MySQL not ready at backend start** | `startup_event` retries `create_all` up to ten times with 3-second delays. | API may delay listening; eventually raises if DB never appears. | Ensure `depends_on` healthchecks in Compose; check `docker logs` for `OperationalError`. |
| **Docker daemon unreachable or socket missing** | `docker.from_env()` raises `docker.errors.APIError` or `BuildError`; returned JSON includes `success: false`; **HTTP 200** with failure payload on fix routes. | Fix submission fails with diagnostic logs in UI. | Restore Docker; mount `/var/run/docker.sock`; verify `scale_net` exists. |
| **Sandbox build timeout / read timeout** | `ReadTimeout` and build errors are caught; logs returned to client. | Student sees "not fixed"; may retry. | Increase `SANDBOX_RUN_TIMEOUT`; optimize `run_tests.sh`; check host load. |
| **OSV.dev down, slow, or rate-limited** | `query_osv` uses 4s timeout; exceptions are logged; failures are silent per package; merged results may omit dependency CVEs. | Static scan still succeeds; dependency tab may show fewer or no rows. | Retry scan; self-host OSV mirror for air-gapped sites. |
| **Background dependency thread errors** | `_run_dep_scan_background` uses a separate `SessionLocal`; exceptions should not crash the main process. | Stale dependency section until next scan. | Inspect backend logs; fix DB connectivity. |
| **OPENAI / Serper keys absent** | `POST /api/project/scan/ai` returns 503; mentor endpoints return structured "not configured." | Features degrade; core scan works. | Set keys in `.env` / `backend/.env` (Section 17). |
| **Disk full on upload** | `POST /api/project/upload` may fail with 500 or OS error. | Upload rejected. | Free disk; set `PROJECT_STORAGE_ROOT` to a large volume. |
| **Leaderboard with no completions** | `GET /api/challenge/leaderboard` returns an empty list. | Empty leaderboard displayed; not an error. | Ensure at least one student has completed a challenge or marked an attack complete. |

**Instructor takeaway:** During an exam or live demo, the highest-risk failure modes are **Docker** (sandbox) and **database** connectivity. OSV is best-effort; static regex scan does not depend on OSV.

---

---

## Appendix A — Complete Annotated File Tree

Key files and their roles in SCALE. Generated artifacts (`uploads/`, `node_modules/`, `.git`) are excluded.

```
grad-project/
├── docker-compose.yml              — Compose stack definition (services, volumes, networks)
├── .env.example                    — Environment variable template; copy to .env
├── backend/
│   ├── requirements.txt            — Python dependencies (mostly unpinned; bcrypt==4.0.1 pinned)
│   ├── seed_db.py                  — Database seeding: default accounts, quiz bank (200 questions)
│   ├── sandbox_base/               — Dockerfile for the pre-built sandbox base image
│   └── app/
│       ├── main.py                 — FastAPI app factory; CORS, routers, startup event, runtime schema patch
│       ├── models.py               — SQLAlchemy ORM models (all tables)
│       ├── schemas.py              — Pydantic request/response schemas
│       ├── crud.py                 — User CRUD helpers
│       ├── sandbox_runner.py       — Docker sandbox execution, diff generation, DIFF_ANNOTATIONS
│       ├── env_bootstrap.py        — Loads .env before SQLAlchemy initialization
│       ├── db/
│       │   └── database.py         — Engine and SessionLocal factory
│       ├── api/
│       │   ├── auth.py             — Login, register, logout, profile, admin user management
│       │   ├── challenges.py       — All ten lab endpoints, fix submission, hints, replay, progress
│       │   ├── projects.py         — Upload, scan (merged), scan-from-git, scan status, reports
│       │   ├── quizzes.py          — Bank, take, assignments, mistakes quiz, AI assign
│       │   ├── quiz_dynamic.py     — Dynamic quiz generation from scan context
│       │   ├── stats.py            — Admin, instructor, student dashboard stats
│       │   ├── messages.py         — Messaging threads
│       │   ├── security_logs.py    — Admin log query and stats
│       │   ├── instructor.py       — Student analytics, progress reset
│       │   ├── report.py           — Portfolio pentest PDF
│       │   ├── red_blue.py         — Red vs Blue game lifecycle, scoring
│       │   ├── challenge_assignments.py — Instructor timed lab assignments
│       │   ├── ai_mentor.py        — AI status, mentor chat, analyze-code
│       │   ├── game_challenge.py   — Legacy game endpoints, challenge leaderboard
│       │   ├── misconfig.py        — Security misconfiguration mini-lab, interest calculator
│       │   ├── attack_simulator.py — Attack simulation endpoint
│       │   └── project_analyzer.py — Project structure analysis
│       ├── scanner/
│       │   ├── rules.py            — Regex RULES with severity levels
│       │   ├── detector.py         — File walker applying rules
│       │   ├── scorer.py           — Severity-weighted risk scoring
│       │   ├── fixer.py            — FIX_RECOMMENDATIONS per vulnerability type
│       │   ├── semgrep_scanner.py  — Semgrep CLI integration and result normalization
│       │   ├── dependency_scanner.py — OSV.dev queries for manifest dependencies
│       │   └── report_generator.py — Per-upload PDF via ReportLab
│       └── security/
│           ├── security_logger.py  — log_security_event, SecurityEventType, SecuritySeverity
│           └── learning_tracker.py — TOTAL_CHALLENGES, SKILL_BUCKETS, recalculate_learning_progress, leaderboard helpers
├── frontend/
│   ├── package.json                — Node dependencies (semver ranges)
│   ├── vite.config.ts              — Vite config with challenge tutorial video middleware
│   └── src/
│       ├── App.tsx                 — Route table
│       ├── main.tsx                — React DOM entry
│       ├── index.css               — Global styles
│       ├── lib/
│       │   ├── api.ts              — Axios instance with Bearer interceptor, withCredentials
│       │   └── challengeTutorialVideos.ts — Video asset mapping per challenge slug
│       ├── context/
│       │   └── ScanContext.tsx     — User-scoped scan localStorage context
│       ├── utils/
│       │   └── payloads.ts         — Default payload templates for attack pages
│       ├── components/
│       │   ├── AttackReplayVisualizer.tsx — Stepper UI for ATTACK_REPLAYS
│       │   ├── BuildingWallAnimation.tsx  — Animated loading component
│       │   ├── ChallengeHintPanel.tsx     — Hint UI with AI mentor chat
│       │   ├── ChallengeTutorialVideo.tsx — MP4 tutorial video player
│       │   ├── CodeDiffViewer.tsx         — Side-by-side code diff with annotations
│       │   ├── MainLayout.tsx             — App shell with navigation
│       │   ├── ProtectedRoute.tsx         — JWT validation guard
│       │   ├── ResultModal.tsx            — Fix submission result overlay
│       │   └── Sidebar.tsx                — Navigation sidebar with unread message badge
│       └── pages/
│           ├── (all pages listed in Section 16)
├── challenge-sql-injection/        — Lab 1: app.py, test_app.py, run_tests.sh, users.sql
├── challenge-xss/                  — Lab 2: app.py, test_app.py, run_tests.sh, xss.sql
├── challenge-csrf/                 — Lab 3: app.py, test_app.py, run_tests.sh, csrf.sql
├── challenge-command-injection/    — Lab 4: app.py, test_app.py, run_tests.sh
├── challenge-broken-auth/          — Lab 5: app.py, test_app.py, run_tests.sh
├── challenge-security-misc/        — Lab 6: app.py, test_app.py, run_tests.sh
├── challenge-insecure-storage/     — Lab 7: app.py, test_app.py, run_tests.sh
├── challenge-directory-traversal/  — Lab 8: app.py, test_app.py, run_tests.sh
├── challenge-xxe/                  — Lab 9: app.py, test_app.py, run_tests.sh
├── challenge-redirect/             — Lab 10: app.py, test_app.py, run_tests.sh
├── Web-Videos/                     — Voiced tutorial MP4s (mounted read-only into frontend)
└── db_init/
    └── init.sql                    — Initial SQL for main_db (challenges table, etc.)
```

---

## Appendix B — Complete Route Map (Alphabetical by Path)

| Method | Path | Router Module | Auth | Description |
|--------|------|---------------|------|-------------|
| GET | `/` | `main.py` | No | Root health check |
| GET | `/api/admin/config` | `misconfig.py` | Yes (any user — missing authz; lab 6) | Intentional misconfiguration — see §5.2.2 |
| GET | `/api/admin/overview` | `projects.py` | Yes (admin) | Admin platform overview |
| POST | `/api/ai/analyze-code` | `ai_mentor.py` | Yes (JWT) | AI code analysis |
| POST | `/api/ai/mentor-chat` | `ai_mentor.py` | Yes (JWT) | AI mentor chat |
| GET | `/api/ai/status` | `ai_mentor.py` | Yes (JWT) | AI configuration status |
| POST | `/api/attack/simulate` | `attack_simulator.py` | Yes (JWT) | Attack simulation |
| POST | `/api/auth/admin/approve/{user_id}` | `auth.py` | Yes (admin) | Approve instructor |
| POST | `/api/auth/admin/create-admin` | `auth.py` | Yes (admin) | Create admin account |
| GET | `/api/auth/admin/pending` | `auth.py` | Yes (admin) | List pending instructors |
| DELETE | `/api/auth/admin/users/{user_id}` | `auth.py` | Yes (admin) | Delete user |
| PUT | `/api/auth/admin/users/{user_id}/role` | `auth.py` | Yes (admin) | Update user role |
| POST | `/api/auth/login` | `auth.py` | No | Login |
| POST | `/api/auth/logout` | `auth.py` | Yes (JWT) | Logout |
| GET | `/api/auth/me` | `auth.py` | Yes (JWT) | Current user profile |
| POST | `/api/auth/register` | `auth.py` | No | Register |
| GET | `/api/auth/users` | `auth.py` | Yes (JWT) | Search users |
| POST | `/api/calc/interest` | `misconfig.py` | Yes (JWT) | Interest calculator (misconfig lab) |
| POST | `/api/challenge-assignments/create` | `challenge_assignments.py` | Yes (JWT) | Create timed assignment |
| GET | `/api/challenge-assignments/instructor` | `challenge_assignments.py` | Yes (JWT) | List instructor assignments |
| GET | `/api/challenge-assignments/my` | `challenge_assignments.py` | Yes (JWT) | List student assignments |
| DELETE | `/api/challenge-assignments/{assignment_id}` | `challenge_assignments.py` | Yes (JWT) | Deactivate assignment |
| GET | `/api/challenge-assignments/{assignment_id}/results` | `challenge_assignments.py` | Yes (JWT) | Per-student results |
| POST | `/api/challenge-assignments/{assignment_id}/start` | `challenge_assignments.py` | Yes (JWT) | Start assignment |
| GET | `/api/challenge-assignments/{assignment_id}/status` | `challenge_assignments.py` | Yes (JWT) | Assignment status |
| POST | `/api/challenge-assignments/{assignment_id}/submit-fix` | `challenge_assignments.py` | Yes (JWT) | Submit assignment fix |
| POST | `/api/challenge/blue/fix` | `game_challenge.py` | Yes (JWT) | Legacy blue team fix |
| POST | `/api/challenge/hint` | `game_challenge.py` | Yes (JWT) | Advanced hint |
| GET | `/api/challenge/leaderboard` | `game_challenge.py` | Yes (JWT) | **Challenge leaderboard** |
| POST | `/api/challenge/red/attack` | `game_challenge.py` | Yes (JWT) | Legacy red team attack |
| POST | `/api/challenge/start` | `game_challenge.py` | Yes (JWT) | Start legacy challenge |
| GET | `/api/challenge/status` | `game_challenge.py` | Yes (JWT) | Legacy challenge status |
| GET | `/api/challenges/csrf/accounts` | `challenges.py` | Yes (JWT) | CSRF lab accounts |
| POST | `/api/challenges/csrf/reset` | `challenges.py` | Yes (JWT) | Reset CSRF accounts |
| POST | `/api/challenges/csrf/transfer` | `challenges.py` | Yes (JWT) | Vulnerable CSRF transfer |
| GET | `/api/challenges/hints` | `challenges.py` | Yes (JWT) | Get hints |
| POST | `/api/challenges/hints/use` | `challenges.py` | Yes (JWT) | Use hint |
| POST | `/api/challenges/mark-attack-complete` | `challenges.py` | Yes (JWT) | Mark attack complete |
| POST | `/api/challenges/ping` | `challenges.py` | Yes (JWT) | Command injection ping |
| GET | `/api/challenges/progress` | `challenges.py` | Yes (JWT) | Get challenge progress |
| DELETE | `/api/challenges/progress/{challenge_slug}` | `challenges.py` | Yes (JWT) | Delete challenge progress |
| GET | `/api/challenges/redirect` | `challenges.py` | Yes (JWT) | Vulnerable redirect |
| GET | `/api/challenges/replay/{challenge_slug}` | `challenges.py` | Yes (JWT) | Attack replay |
| GET | `/api/challenges/source/{challenge_slug}` | `challenges.py` | Yes (JWT) | Challenge source |
| GET | `/api/challenges/state` | `challenges.py` | Yes (JWT) | Challenge state |
| POST | `/api/challenges/state/update` | `challenges.py` | Yes (JWT) | Update challenge state |
| GET | `/api/challenges/storage/dump` | `challenges.py` | Yes (JWT) | Insecure storage dump |
| POST | `/api/challenges/storage/register` | `challenges.py` | Yes (JWT) | Insecure storage register |
| POST | `/api/challenges/submit-fix` | `challenges.py` | Yes (JWT) | SQL injection fix |
| POST | `/api/challenges/submit-fix-auth` | `challenges.py` | Yes (JWT) | Broken auth fix |
| POST | `/api/challenges/submit-fix-command-injection` | `challenges.py` | Yes (JWT) | Command injection fix |
| POST | `/api/challenges/submit-fix-csrf` | `challenges.py` | Yes (JWT) | CSRF fix |
| POST | `/api/challenges/submit-fix-misc` | `challenges.py` | Yes (JWT) | Security misc fix |
| POST | `/api/challenges/submit-fix-redirect` | `challenges.py` | Yes (JWT) | Redirect fix |
| POST | `/api/challenges/submit-fix-storage` | `challenges.py` | Yes (JWT) | Insecure storage fix |
| POST | `/api/challenges/submit-fix-traversal` | `challenges.py` | Yes (JWT) | Directory traversal fix |
| POST | `/api/challenges/submit-fix-xss` | `challenges.py` | Yes (JWT) | XSS fix |
| POST | `/api/challenges/submit-fix-xxe` | `challenges.py` | Yes (JWT) | XXE fix |
| GET | `/api/challenges/traversal/read` | `challenges.py` | Yes (JWT) | Traversal file read |
| POST | `/api/challenges/vulnerable-login` | `challenges.py` | Yes (JWT) | SQL injection login |
| DELETE | `/api/challenges/xss/comments` | `challenges.py` | Yes (JWT) | Clear XSS comments |
| GET | `/api/challenges/xss/comments` | `challenges.py` | Yes (JWT) | Get XSS comments |
| POST | `/api/challenges/xss/comments` | `challenges.py` | Yes (JWT) | Post XSS comment |
| POST | `/api/challenges/xxe/parse` | `challenges.py` | Yes (JWT) | XXE XML parse |
| GET | `/api/instructor/user/{user_id}/analytics` | `instructor.py` | Yes (JWT) | Student analytics |
| POST | `/api/instructor/user/{user_id}/reset-progress` | `instructor.py` | Yes (JWT) | Reset student progress |
| GET | `/api/messages/contacts` | `messages.py` | Yes (JWT) | Message contacts |
| POST | `/api/messages/send` | `messages.py` | Yes (JWT) | Send message |
| GET | `/api/messages/unread-count` | `messages.py` | Yes (JWT) | Unread message count |
| GET | `/api/messages/with/{user_id}` | `messages.py` | Yes (JWT) | Get conversation |
| GET | `/api/project/analytics` | `projects.py` | Yes (JWT) | Project analytics |
| POST | `/api/project/analyze-structure` | `project_analyzer.py` | Yes (JWT) | Project structure analysis |
| GET | `/api/project/files` | `projects.py` | Yes (JWT) | List project files |
| GET | `/api/project/report` | `projects.py` | Yes (JWT) | JSON security report |
| GET | `/api/project/report/pdf` | `projects.py` | Yes (JWT) | Per-upload PDF |
| POST | `/api/project/scan` | `projects.py` | Yes (JWT) | Run merged scan |
| POST | `/api/project/scan-from-git` | `projects.py` | Yes (JWT) | Clone and scan Git repo |
| GET | `/api/project/scan-status/{scan_id}` | `projects.py` | Yes (JWT) | Async scan status |
| POST | `/api/project/scan/ai` | `projects.py` | Yes (JWT) | AI-enriched scan |
| POST | `/api/project/upload` | `projects.py` | Yes (JWT) | Upload ZIP |
| GET | `/api/project/{project_id}` | `projects.py` | Yes (JWT) | Get project |
| GET | `/api/project/{project_id}/dependencies` | `projects.py` | Yes (JWT) | Get dependencies |
| POST | `/api/quiz/generate` | `quiz_dynamic.py` | Yes (JWT) | Dynamic quiz generation |
| GET | `/api/quiz/manage` | `quiz_dynamic.py` | Yes (JWT) | List dynamic quizzes |
| POST | `/api/quiz/manage` | `quiz_dynamic.py` | Yes (JWT) | Manage dynamic quizzes |
| POST | `/api/quizzes/ai-generate-and-assign` | `quizzes.py` | Yes (JWT) | AI generate and assign |
| POST | `/api/quizzes/assign-mistakes-quiz` | `quizzes.py` | Yes (JWT) | Assign mistakes quiz |
| POST | `/api/quizzes/assignments` | `quizzes.py` | Yes (JWT) | Create assignment |
| GET | `/api/quizzes/assignments/instructor` | `quizzes.py` | Yes (JWT) | Instructor assignments |
| GET | `/api/quizzes/assignments/student` | `quizzes.py` | Yes (JWT) | Student assignments |
| POST | `/api/quizzes/assignments/{assignment_id}/start` | `quizzes.py` | Yes (JWT) | Start quiz assignment |
| GET | `/api/quizzes/assignments/{assignment_id}/status` | `quizzes.py` | Yes (JWT) | Assignment status |
| DELETE | `/api/quizzes/assignments/{id}` | `quizzes.py` | Yes (JWT) | Delete assignment |
| GET | `/api/quizzes/assignments/{id}/take` | `quizzes.py` | Yes (JWT) | Take assigned quiz |
| GET | `/api/quizzes/attempts` | `quizzes.py` | Yes (JWT) | Quiz attempt history |
| POST | `/api/quizzes/common-mistakes-quiz` | `quizzes.py` | Yes (JWT) | Common mistakes quiz |
| POST | `/api/quizzes/generate-ai-preview` | `quizzes.py` | Yes (JWT) | AI quiz preview |
| GET | `/api/quizzes/manage` | `quizzes.py` | Yes (JWT) | Manage questions |
| POST | `/api/quizzes/manage` | `quizzes.py` | Yes (JWT) | Mutate questions |
| DELETE | `/api/quizzes/questions` | `quizzes.py` | Yes (JWT) | Delete all questions |
| GET | `/api/quizzes/questions` | `quizzes.py` | Yes (JWT) | Get questions |
| POST | `/api/quizzes/questions` | `quizzes.py` | Yes (JWT) | Create question |
| DELETE | `/api/quizzes/questions/{q_id}` | `quizzes.py` | Yes (JWT) | Delete question |
| PUT | `/api/quizzes/questions/{q_id}` | `quizzes.py` | Yes (JWT) | Update question |
| POST | `/api/quizzes/submit-answer` | `quizzes.py` | Yes (JWT) | Submit answer |
| POST | `/api/quizzes/submit-attempt` | `quizzes.py` | Yes (JWT) | Submit attempt |
| POST | `/api/quizzes/take` | `quizzes.py` | Yes (JWT) | Take practice quiz |
| GET | `/api/quizzes/topics` | `quizzes.py` | Yes (JWT) | Available topics |
| GET | `/api/quizzes/wrong-answer-count` | `quizzes.py` | Yes (JWT) | Wrong answer count |
| POST | `/api/redblue/game/create` | `red_blue.py` | Yes (JWT) | Create game |
| DELETE | `/api/redblue/game/{game_id}` | `red_blue.py` | Yes (JWT) | Delete game |
| GET | `/api/redblue/game/{game_id}` | `red_blue.py` | Yes (JWT) | Get game |
| POST | `/api/redblue/game/{game_id}/attack` | `red_blue.py` | Yes (JWT) | Log red attack |
| GET | `/api/redblue/game/{game_id}/attacks` | `red_blue.py` | Yes (JWT) | Poll attacks |
| GET | `/api/redblue/game/{game_id}/challenge-code` | `red_blue.py` | Yes (JWT) | Get challenge source code |
| POST | `/api/redblue/game/{game_id}/delete` | `red_blue.py` | Yes (JWT) | Delete game (POST variant) |
| POST | `/api/redblue/game/{game_id}/end` | `red_blue.py` | Yes (JWT) | End game |
| POST | `/api/redblue/game/{game_id}/fix` | `red_blue.py` | Yes (JWT) | Submit blue fix |
| GET | `/api/redblue/games` | `red_blue.py` | Yes (JWT) | List all games |
| GET | `/api/redblue/my-games` | `red_blue.py` | Yes (JWT) | Student game list |
| GET | `/api/report/pdf` | `report.py` | Yes (JWT) | Portfolio PDF |
| GET | `/api/report/pdf/scan` | `report.py` | Yes (JWT) | Scan-specific PDF |
| GET | `/api/security/logs` | `security_logs.py` | Yes (JWT) | Security logs |
| GET | `/api/security/logs/stats` | `security_logs.py` | Yes (JWT) | Log statistics |
| GET | `/api/stats/admin/dashboard` | `stats.py` | Yes (admin) | Admin dashboard stats |
| GET | `/api/stats/instructor/dashboard` | `stats.py` | Yes (JWT) | Instructor stats |
| GET | `/api/stats/progress/me` | `stats.py` | Yes (JWT) | Student learning progress |
| GET | `/api/user/projects` | `projects.py` | Yes (JWT) | User project list |

**Total routes: 128** (including `GET /`).

---

## Appendix C — Glossary

| Term | Definition |
|------|------------|
| **Challenge slug** | Canonical string identifier for a lab, e.g. `sql-injection`, `xss`, `csrf`. |
| **Sandbox runner** | `run_in_sandbox_detailed` in `sandbox_runner.py` — builds a disposable Docker container, runs `run_tests.sh`, and returns pass/fail counts and logs. |
| **`improvement_score`** | Integer 0–100 returned by `_verify_fix_improvement`. Measures reduction in unittest failure + error counts between the vulnerable baseline and the student submission. See Section 5.2.1 for the exact formula. |
| **`fixed`** | Boolean returned alongside `improvement_score`. True only when the after-run reports `success` and `after_count == 0` (all tests pass). |
| **Defense Level** | The `level` string on `user_learning_progress` (Beginner / Intermediate / Advanced) from `_determine_level`. Not a class rank — see Section 9.3. |
| **`currentXp`** | Client-only dashboard figure: `solvedLabs * 100 + (quizAttempts.length > 0 ? avgScorePercent : 0)`. Not persisted. See Section 9.6. |
| **Narrative attack XP** | Static integers in `AttackSuccessPage` `typeConfig` labeled "XP gained". Not stored or added to `currentXp`. See Section 5.8. |
| **Retention score** | Aggregate on `user_learning_progress`; formula: `(accuracy * 0.6) + (min(streak, 14) / 14.0 * 20.0) + (100.0 - min(failed_answers * 2, 40))`, capped at 100. |
| **Learning speed** | `(solved / max(avg_time, 1)) * 100` where `avg_time` is mean quiz time in seconds. |
| **streak_days** | Consecutive calendar days with at least one `UserProgress.completed_at`. |
| **context_type** | `security_logs` discriminator: `"real"` for platform events, `"challenge"` or `"challenge_simulation"` for lab traffic. |
| **ScanContext** | React context for per-user scan JSON, keyed `scale.scanData.{user_id}` in `localStorage`. |
| **vuln_summary** | JSON text stored in `scan_history` containing all scan findings, summary counts, semgrep flag, and dependency data. |
| **SKILL_BUCKETS** | Six radar dimensions mapping skill names to challenge slug lists in `learning_tracker.py`. |
| **OSV.dev** | Open-source vulnerability database API used for dependency advisories. |
| **scale-user-changed** | Browser CustomEvent dispatched on login/logout to refresh context across components. |
| **LAB_CHALLENGE_SLUGS** | Integer 1–10 to slug mapping in `red_blue.py` for instructor-led Red vs Blue games. |
| **Semgrep engine** | Optional SAST pass in `semgrep_scanner.py`; merged with regex findings in `projects.py`. Results tagged `engine: "semgrep"`. |
| **Challenge assignment** | Instructor-created timed lab task in `challenge_assignments` / `challenge_assignment_students`. Separate from self-paced lab progress. |
| **Mistakes quiz** | Adaptive MCQ set generated from prior wrong answers via `/api/quizzes/common-mistakes-quiz`. |
| **targets_mistake** | Boolean column on `questions` linking a generated MCQ to a student's weak topic. |
| **Leaderboard** | `GET /api/challenge/leaderboard` in `game_challenge.py`; ranks participants by challenges completed. See Section 10.1. |
| **current_phase** | Column on `GameChallenge` tracking turn state: `awaiting_red` or `awaiting_blue`. |
| **current_round** | Column on `GameChallenge` incremented after each blue submission in Red vs Blue. |
| **`improvement_score` (Red vs Blue)** | Same computation as lab `improvement_score`; a fix with `improvement_score > 0` but `fixed == false` still awards the round to red. |

---

## Appendix D — Development Changelog

### Phase 1 — Core Platform
Original ten challenges, project scanner (regex only), quiz bank, auth, role dashboards, messaging.

### Phase 2 — Bug Fixes
XSS comment routes, upload path resolution, sandbox script line endings, session isolation improvements, axios multipart fix.

### Phase 3 — Feature Additions (Round 1)
Code diff viewer, portfolio PDF report, AI mentor, Red vs Blue game mode, OSV dependency scanner, attack replay visualizer.

### Phase 4 — Fixes and Polish (Round 2)
PDF flattening for ReportLab, background dependency scan threading, user-scoped scan storage keys, quiz UI cards, My Games portal, replay overlay portal.

### Phase 5 — Feature Additions (Round 3)
Tutorial pages with voiced video playback, admin real attempts display, AI environment configuration, AI status endpoint, instructor AI quiz generator, challenge progress reset, skill mastery bar chart.

### Phase 6 — Scanner, Assignments, and Analytics (May 2026)

- **Semgrep SAST** merged with legacy regex scanner (`semgrep_scanner.py`, `httpx` dependency).
- **Git repository scan** (`POST /api/project/scan-from-git`) and **async scan status** polling.
- **Normalized quiz assignment tables** (`quiz_assignment_students`, `quiz_assignment_questions`) with time limits and due dates.
- **Common mistakes quiz** — student self-service (`/api/quizzes/common-mistakes-quiz`) and instructor push (`/api/quizzes/assign-mistakes-quiz`).
- **Instructor timed lab assignments** (`/api/challenge-assignments`, `ChallengeAssignmentPage.tsx`, instructor results view).
- **Red vs Blue** turn phases (`current_phase`, `current_round`), attack polling enhancements, game delete/end routes.
- **Voiced tutorial videos** served via Vite middleware from `Web-Videos/` (Docker volume mount).
- **Runtime schema self-heal** in `main._ensure_runtime_schema()` for deployments without Alembic.
- **Quiz bank expanded** to 200 seeded questions across 20 security topics in `seed_db.py`.
- **Challenge leaderboard** (`GET /api/challenge/leaderboard`) in `game_challenge.py`.

---

## Appendix E — ORM Models (Complete Column Reference)

See `backend/app/models.py`. Key models and columns:

### User (`users`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| email | String(255) unique indexed | Login email |
| hashed_password | String(255) | bcrypt hash |
| role | String(50) default `user` | user / instructor / admin |
| is_approved | Boolean default True | False for pending instructors |

### UserProgress (`user_progress`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | Integer FK users.id | |
| challenge_id | String(50) | Slug or legacy integer id |
| completed_at | DateTime default utcnow | |

### Question (`questions`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| text | Text | MCQ stem |
| type | String(20) | Question type |
| topic | String(50) | Security category |
| difficulty | String(20) | Easy / Medium / Hard |
| skill_focus | String(50) | Targeted skill |
| explanation | Text | Answer rationale |
| targets_mistake | Boolean | True for mistakes-quiz-generated questions |

### QuizAssignment (`quiz_assignments`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| title | String(255) | |
| instructor_id | Integer FK users.id | |
| assigned_student_ids | Text | Legacy comma-separated (compat) |
| question_ids | Text | Legacy comma-separated (compat) |
| time_limit_minutes | Integer nullable | |
| due_date | DateTime nullable | |
| created_at | DateTime default utcnow | |

### QuizAttempt (`quiz_attempts`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | Integer FK users.id | |
| assignment_id | Integer FK quiz_assignments.id nullable | |
| title | String(255) | e.g. "Practice: SQL Injection" |
| score | Integer | Correct answers |
| total | Integer | Total questions |
| time_seconds | Integer | Elapsed time |
| completed_at | DateTime default utcnow | |

### ChallengeAssignment (`challenge_assignments`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| created_by | Integer FK users.id | |
| challenge_slug | String(100) | One of the ten lab slugs |
| title | String(255) | |
| instructions | Text nullable | |
| time_limit_minutes | Integer | 10–240 |
| due_date | DateTime nullable | |
| is_active | Boolean default True | Set to False on soft-delete |

### ChallengeAssignmentStudent (`challenge_assignment_students`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| assignment_id | Integer FK challenge_assignments.id | |
| student_id | Integer FK users.id | |
| started_at | DateTime nullable | |
| submitted_at | DateTime nullable | |
| time_used_seconds | Integer default 0 | |
| status | String(50) default `assigned` | assigned / in_progress / passed / failed / expired |
| score | Integer nullable | 100 if passed, 0 otherwise |
| fix_code_submitted | Text nullable | |
| sandbox_passed | Boolean nullable | |

### GameChallenge (`game_challenges`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| project_id | String(100) | `redblue-<uuid>` for instructor games |
| status | String(20) | active / inactive / completed |
| lab_challenge_id | Integer nullable | 1–10 |
| red_team_id | Integer FK teams.id | |
| blue_team_id | Integer FK teams.id | |
| red_score | Integer default 0 | Incremented when blue fix fails |
| blue_score | Integer default 0 | Incremented when blue fix passes |
| current_phase | String | awaiting_red / awaiting_blue |
| current_round | Integer | Incremented after each blue submission |
| started_at | DateTime | |

### SecurityLog (`security_logs`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | Integer FK users.id nullable | |
| event_type | String(100) | SecurityEventType |
| severity | String(20) | low / medium / high / critical |
| payload | Text nullable | Attack strings, file paths |
| endpoint | String(255) nullable | |
| ip_address | String(64) nullable | |
| user_agent | String(512) nullable | |
| context_type | String(50) default `real` | real / challenge |
| meta_data | JSON nullable | Structured metadata |
| created_at | DateTime indexed | |

### UserLearningProgress (`user_learning_progress`)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | Integer FK users.id unique | |
| vulnerabilities_solved | Integer default 0 | Capped at TOTAL_CHALLENGES (10) |
| failed_attempts | Integer default 0 | |
| accuracy | Float default 0.0 | Quiz accuracy 0–100 |
| avg_time | Float default 0.0 | Mean quiz time in seconds |
| strongest_category | String(100) | |
| weakest_category | String(100) | |
| level | String(30) | Beginner / Intermediate / Advanced |
| streak_days | Integer default 0 | |
| learning_speed | Float default 0.0 | |
| retention_score | Float default 0.0 | |
| updated_at | DateTime | |

---

## Appendix F — Learning Progress Module (Full Source)

See `backend/app/security/learning_tracker.py`. Key constants and functions:

```python
TOTAL_CHALLENGES = 10

LEGACY_CHALLENGE_IDS = {
    "1": "sql-injection", "2": "xss", "3": "csrf", "4": "command-injection",
    "5": "broken-auth", "6": "security-misc", "7": "insecure-storage",
    "8": "directory-traversal", "9": "xxe", "10": "redirect",
}

SKILL_BUCKETS = {
    "SQL Injection": ["sql-injection", "broken-auth"],
    "XSS": ["xss"],
    "CSRF": ["csrf", "redirect"],
    "Traversal": ["directory-traversal", "command-injection"],
    "XXE": ["xxe"],
    "Storage": ["insecure-storage", "security-misc"],
}
```

**`_determine_level(vulnerabilities_solved, accuracy)`**
- Advanced: solved >= 9 and accuracy >= 80
- Intermediate: solved >= 4 and accuracy >= 60
- Beginner: otherwise

**`recalculate_learning_progress(db, user_id)`**
Aggregates `UserProgress`, `UserAnswer`, `QuizAttempt` rows; computes all `UserLearningProgress` fields; commits to DB.

**`build_learning_progress_payload(db, user_id)`**
Returns the full dashboard payload dict including `skills`, `skills_radar`, and `recommendations`.

**`build_challenge_progress_detail(db, user_id)`**
Returns ten rows for the Challenge Mastery bar chart, each with `slug`, `label`, `category`, `color`, `completed`, `value`.

**`get_learning_recommendations(profile)`**
Returns a list of personalized recommendation strings based on `weakest_category`, `accuracy`, and `failed_attempts`.

**Retention score formula:**
```
retention_score = min(100, max(0,
    (accuracy * 0.6) +
    (min(streak_days, 14) / 14.0 * 20.0) +
    (100.0 - min(failed_attempts * 2, 40))
))
```

---

## Appendix G — Challenge Hints and Attack Replay Payloads

### G.1 Progressive Hints (`_HINTS`)

Available for slugs: `csrf`, `broken-auth`, `security-misc`, `directory-traversal`, `xxe`, `insecure-storage`. Each hint has a `level` (1–3) and a `penalty` value.

| Slug | Level 1 Hint | Level 2 Hint | Level 3 Hint |
|------|-------------|-------------|-------------|
| csrf | Look for an action that changes server state without validation. | Think about how a victim's browser might send a request without them clicking a bank button. | Consider abusing an auto-submitting mechanism in HTML. |
| broken-auth | Can you log in without knowing the real password? | Try manipulating the login input so that the server's check always evaluates as true. | Think about classic injection techniques against authentication queries. |
| security-misc | Real apps sometimes expose debug or admin endpoints. | Try calling endpoints that are not linked from the UI. | Hunt for a configuration or debug endpoint that should never be reachable in production. |
| directory-traversal | Try using `../` in the file name parameter. | Your goal is to escape the intended files directory. | Fix by normalizing paths and rejecting paths outside the base directory. |
| xxe | Use a DOCTYPE payload with an external entity. | Try reading `file:///etc/passwd` through an entity reference. | Fix by disabling external entities and blocking DTD processing. |
| insecure-storage | Register a user, then dump storage. | Look for plaintext passwords in the dump output. | Fix by hashing before storing credentials. |

### G.2 Attack Replays (`ATTACK_REPLAYS`)

Structured step sequences for `GET /api/challenges/replay/{slug}`. Each step has: `step`, `type` (user_action / user_input / http_request / server_processing / http_response), `title`, `description`, and `data`.

Available slugs with replay steps: `sql-injection`, `xss`, `csrf`, `command-injection`, `broken-auth`, `directory-traversal`, `xxe`, `insecure-storage`, `security-misc`, `redirect`.

---

## Appendix H — Frontend Components

Components located in `frontend/src/components/`:

| File | Role |
|------|------|
| `AttackReplayVisualizer.tsx` | Stepper UI that renders `ATTACK_REPLAYS` step-by-step with type-based icons and code blocks |
| `BuildingWallAnimation.tsx` | Animated loading/intro component for visual feedback |
| `ChallengeHintPanel.tsx` | Progressive hint display with AI mentor chat integration; uses `POST /api/challenge/hint` and `POST /api/ai/mentor-chat` |
| `ChallengeTutorialVideo.tsx` | MP4 video player for voiced lab tutorials; resolves video from `challengeTutorialVideos.ts` |
| `CodeDiffViewer.tsx` | Side-by-side unified diff table with red/green rows and annotation tooltips from `DIFF_ANNOTATIONS` |
| `MainLayout.tsx` | App shell wrapping all protected pages; contains navigation and polls unread message count every 30 s |
| `ProtectedRoute.tsx` | Route guard that calls `GET /api/auth/me` and clears sessionStorage on 401 |
| `ResultModal.tsx` | Overlay modal displaying sandbox result: success/failure, improvement score, test output, and code diff |
| `Sidebar.tsx` | Navigation sidebar with role-based links, user email display, unread message badge, and logout |

---

## Appendix I — Challenge Docker Bind Mounts and Directories

Each challenge directory contains the same four files (`app.py`, `requirements.txt`, `run_tests.sh`, `test_app.py`). Some include additional SQL initialization files.

| Directory | Extra Files | Purpose |
|-----------|-------------|---------|
| `challenge-sql-injection/` | `users.sql` | SQL injection lab; users.sql seeds testdb |
| `challenge-xss/` | `xss.sql` | XSS lab; xss.sql seeds comment table |
| `challenge-csrf/` | `csrf.sql` | CSRF lab; csrf.sql seeds csrfdb accounts |
| `challenge-command-injection/` | — | Command injection lab |
| `challenge-broken-auth/` | — | Broken authentication lab |
| `challenge-security-misc/` | — | Security misconfiguration lab |
| `challenge-insecure-storage/` | — | Insecure storage lab |
| `challenge-directory-traversal/` | — | Directory traversal lab |
| `challenge-xxe/` | — | XML external entity lab |
| `challenge-redirect/` | — | Unvalidated redirect lab |

The backend `docker-compose.yml` mounts each directory to `/app/challenges/<name>`. `_challenge_source_file` resolves to `/app/challenges/<challenge_dir>/app.py`.

---

## Appendix J — Docker Compose and Environment (Expanded Reference)

### J.1 Services

| Service | Build / Image | Host Ports | Depends On | Purpose |
|---------|---------------|------------|------------|---------|
| `sandbox_base` | `./backend/sandbox_base` → `scale-sandbox-base` | — | — | Pre-built base image for student sandbox containers |
| `backend` | `./backend` | 8000:8000 | healthy DBs, sandbox_base | FastAPI API, sandbox runner |
| `frontend` | `./frontend` | 5173:5173 | — | Vite dev server for SPA |
| `ai_service` | `./ai_service` | 8001:8001 | — | Template AI microservice for quiz preview |
| `main_db` | `mysql:8.0` | 3306:3306 | — | Primary application database |
| `challenge_db_sqli` | `mysql:8.0` | 3307:3306 | — | SQL injection lab data |
| `challenge_db_csrf` | `mysql:8.0` | 3308:3306 | — | CSRF lab accounts |

### J.2 Named Volume

| Volume | Mount Point | Persisted |
|--------|-------------|-----------|
| `scale_db_data` | `/var/lib/mysql` in `main_db` | Yes — user accounts, progress, scans, quiz attempts |

### J.3 Environment Variables (Full Reference)

| Variable | Default in Compose | Consumed By | Purpose |
|----------|--------------------|-------------|---------|
| `OPENAI_API_KEY` | empty | Backend | Enables OpenAI for mentor, quizzes, scan AI |
| `SERPER_API_KEY` | empty | Backend | Web-search-backed fallback |
| `AI_SERVICE_URL` | `http://ai_service:8001` | Backend | Template AI quiz generation |
| `DATABASE_URL` | `mysql+pymysql://user:password@main_db/scale_db` | Backend | SQLAlchemy main DB |
| `SQLI_DATABASE_URL` | `...@challenge_db_sqli/testdb` | Challenges | SQLi lab connection |
| `CSRF_DATABASE_URL` | `...@challenge_db_csrf/csrfdb` | Challenges | CSRF lab connection |
| `SECRET_KEY` | `scale_graduation_project_secret_key` | Backend | JWT signing — rotate before production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `600` | Backend | JWT lifetime |
| `ENABLE_BROKEN_AUTH_CHALLENGE` | `true` | Backend | SQLite vulnerable login branch |
| `SANDBOX_MAX_CODE_CHARS` | `200000` | Sandbox | Fix source size cap |
| `SANDBOX_RUN_TIMEOUT` | `25` | Sandbox | Container execution timeout (seconds) |
| `VITE_API_URL` | `http://localhost:8000` | Frontend | Axios base URL |

---

## Appendix K — HTTP Route to Python Handler Names

| Route | Handler Function |
|-------|-----------------|
| `GET /` | `read_root()` |
| `GET /api/admin/config` | `exposed_admin_config()` |
| `GET /api/admin/overview` | `admin_overview()` |
| `POST /api/ai/analyze-code` | `analyze_code_with_ai_mentor()` |
| `POST /api/ai/mentor-chat` | `mentor_challenge_chat()` |
| `GET /api/ai/status` | `ai_status()` |
| `POST /api/attack/simulate` | `simulate_attack()` |
| `POST /api/auth/admin/approve/{user_id}` | `approve_instructor()` |
| `POST /api/auth/admin/create-admin` | `create_admin_internal()` |
| `GET /api/auth/admin/pending` | `get_pending_instructors()` |
| `DELETE /api/auth/admin/users/{user_id}` | `delete_user_endpoint()` |
| `PUT /api/auth/admin/users/{user_id}/role` | `update_role_endpoint()` |
| `POST /api/auth/login` | `login()` |
| `POST /api/auth/logout` | `logout()` |
| `GET /api/auth/me` | `get_current_user_profile()` |
| `POST /api/auth/register` | `register()` |
| `GET /api/auth/users` | `search_users()` |
| `POST /api/calc/interest` | `calc_interest()` |
| `POST /api/challenge/blue/fix` | `blue_team_fix()` |
| `POST /api/challenge/hint` | `get_next_hint()` |
| `GET /api/challenge/leaderboard` | `challenge_leaderboard()` |
| `POST /api/challenge/red/attack` | `red_team_attack()` |
| `POST /api/challenge/start` | `start_challenge()` |
| `GET /api/challenge/status` | `challenge_status()` |
| `GET /api/challenges/csrf/accounts` | `get_csrf_accounts()` |
| `POST /api/challenges/csrf/reset` | `reset_csrf_accounts()` |
| `POST /api/challenges/csrf/transfer` | `vulnerable_transfer()` |
| `GET /api/challenges/hints` | `get_hints()` |
| `POST /api/challenges/hints/use` | `use_hint()` |
| `POST /api/challenges/mark-attack-complete` | `mark_attack_complete()` |
| `POST /api/challenges/ping` | `vulnerable_ping()` |
| `GET /api/challenges/progress` | `get_my_progress()` |
| `DELETE /api/challenges/progress/{challenge_slug}` | `delete_challenge_progress()` |
| `GET /api/challenges/redirect` | `vulnerable_redirect()` |
| `GET /api/challenges/replay/{challenge_slug}` | `get_attack_replay()` |
| `GET /api/challenges/state` | `get_challenge_state()` |
| `POST /api/challenges/state/update` | `update_challenge_state()` |
| `GET /api/challenges/storage/dump` | `insecure_storage_dump()` |
| `POST /api/challenges/storage/register` | `insecure_storage_register()` |
| `POST /api/challenges/submit-fix` | `submit_fix_sql()` |
| `POST /api/challenges/submit-fix-auth` | `submit_fix_auth()` |
| `POST /api/challenges/submit-fix-command-injection` | `submit_fix_command_injection()` |
| `POST /api/challenges/submit-fix-csrf` | `submit_fix_csrf()` |
| `POST /api/challenges/submit-fix-misc` | `submit_fix_misc()` |
| `POST /api/challenges/submit-fix-redirect` | `submit_fix_redirect()` |
| `POST /api/challenges/submit-fix-storage` | `submit_fix_storage()` |
| `POST /api/challenges/submit-fix-traversal` | `submit_fix_traversal()` |
| `POST /api/challenges/submit-fix-xss` | `submit_fix_xss()` |
| `POST /api/challenges/submit-fix-xxe` | `submit_fix_xxe()` |
| `GET /api/challenges/traversal/read` | `traversal_read_file()` |
| `POST /api/challenges/vulnerable-login` | `execute_vulnerable_login()` |
| `DELETE /api/challenges/xss/comments` | `clear_xss_comments()` |
| `GET /api/challenges/xss/comments` | `get_xss_comments()` |
| `POST /api/challenges/xss/comments` | `create_xss_comment()` |
| `POST /api/challenges/xxe/parse` | `parse_xml()` |
| `GET /api/instructor/user/{user_id}/analytics` | `get_student_analytics()` |
| `POST /api/instructor/user/{user_id}/reset-progress` | `reset_student_progress()` |
| `GET /api/messages/contacts` | `list_contacts()` |
| `POST /api/messages/send` | `send_message()` |
| `GET /api/messages/unread-count` | `get_unread_count()` |
| `GET /api/messages/with/{user_id}` | `get_conversation()` |
| `GET /api/project/analytics` | `project_analytics()` |
| `POST /api/project/analyze-structure` | `analyze_project_structure()` |
| `GET /api/project/files` | `list_project_files()` |
| `GET /api/project/report` | `get_project_report()` |
| `GET /api/project/report/pdf` | `get_project_report_pdf()` |
| `POST /api/project/scan` | `scan_project()` |
| `POST /api/project/scan-from-git` | `scan_from_git()` |
| `GET /api/project/scan-status/{scan_id}` | `get_scan_status()` |
| `POST /api/project/scan/ai` | `scan_project_with_ai()` |
| `POST /api/project/upload` | `upload_project()` |
| `GET /api/project/{project_id}` | `get_project_by_id()` |
| `GET /api/project/{project_id}/dependencies` | `get_project_dependencies()` |
| `POST /api/quiz/generate` | `generate_quiz_from_scan()` |
| `GET /api/quiz/manage` | `quiz_manage_entry()` |
| `POST /api/quiz/manage` | `quiz_manage_mutation()` |
| `POST /api/quizzes/ai-generate-and-assign` | `ai_generate_and_assign()` |
| `POST /api/quizzes/assign-mistakes-quiz` | `assign_mistakes_quiz()` |
| `POST /api/quizzes/assignments` | `create_assign()` |
| `GET /api/quizzes/assignments/instructor` | `get_instr_assigns()` |
| `GET /api/quizzes/assignments/student` | `get_student_assigns()` |
| `POST /api/quizzes/assignments/{assignment_id}/start` | `start_quiz_assignment()` |
| `GET /api/quizzes/assignments/{assignment_id}/status` | `get_assignment_status()` |
| `DELETE /api/quizzes/assignments/{id}` | `delete_assign()` |
| `GET /api/quizzes/assignments/{id}/take` | `take_assign_quiz()` |
| `GET /api/quizzes/attempts` | `get_my_quiz_attempts()` |
| `POST /api/quizzes/common-mistakes-quiz` | `common_mistakes_quiz()` |
| `POST /api/quizzes/generate-ai-preview` | `generate_ai()` |
| `GET /api/quizzes/manage` | `quiz_manage_entry()` |
| `POST /api/quizzes/manage` | `quiz_manage_mutation()` |
| `DELETE /api/quizzes/questions` | `delete_all_questions()` |
| `GET /api/quizzes/questions` | `get_questions()` |
| `POST /api/quizzes/questions` | `create_question()` |
| `DELETE /api/quizzes/questions/{q_id}` | `delete_question()` |
| `PUT /api/quizzes/questions/{q_id}` | `update_question()` |
| `POST /api/quizzes/submit-answer` | `submit_answer()` |
| `POST /api/quizzes/submit-attempt` | `submit_quiz_attempt()` |
| `POST /api/quizzes/take` | `take_quiz()` |
| `GET /api/quizzes/topics` | `get_topics()` |
| `GET /api/quizzes/wrong-answer-count` | `wrong_answer_count()` |
| `POST /api/challenge-assignments/create` | `create_challenge_assignment()` |
| `GET /api/challenge-assignments/instructor` | `instructor_list_assignments()` |
| `GET /api/challenge-assignments/my` | `my_challenge_assignments()` |
| `DELETE /api/challenge-assignments/{assignment_id}` | `deactivate_assignment()` |
| `GET /api/challenge-assignments/{assignment_id}/results` | `instructor_assignment_results()` |
| `POST /api/challenge-assignments/{assignment_id}/start` | `start_assignment()` |
| `GET /api/challenge-assignments/{assignment_id}/status` | `assignment_status()` |
| `POST /api/challenge-assignments/{assignment_id}/submit-fix` | `submit_assignment_fix()` |
| `POST /api/redblue/game/create` | `create_redblue_game()` |
| `GET /api/redblue/game/{game_id}` | `get_redblue_game()` |
| `POST /api/redblue/game/{game_id}/attack` | `log_attack()` |
| `GET /api/redblue/game/{game_id}/attacks` | `poll_attacks()` |
| `POST /api/redblue/game/{game_id}/end` | `end_game()` |
| `DELETE /api/redblue/game/{game_id}` | `delete_game()` |
| `POST /api/redblue/game/{game_id}/delete` | `delete_game_post()` |
| `POST /api/redblue/game/{game_id}/fix` | `submit_fix()` |
| `GET /api/redblue/games` | `list_games()` |
| `GET /api/redblue/my-games` | `my_redblue_games()` |
| `GET /api/report/pdf` | `generate_pentest_report_pdf()` |
| `GET /api/security/logs` | `get_security_logs()` |
| `GET /api/security/logs/stats` | `get_security_log_stats()` |
| `GET /api/stats/admin/dashboard` | `get_admin_dashboard_stats()` |
| `GET /api/stats/instructor/dashboard` | `get_instructor_stats()` |
| `GET /api/stats/progress/me` | `get_my_learning_progress()` |
| `GET /api/user/projects` | `list_user_projects()` |

---

## Appendix L — Static Scanner Rules

### L.1 Regex Rules (`backend/app/scanner/rules.py`)

Each rule contributes regex matches to `detector.py`. Severity weights feed `scorer.py` (High=5, Medium=3, Low=1). `semgrep_scanner.py` runs in parallel; when the Semgrep CLI is available, findings are normalized to the same JSON shape with `engine: "semgrep"` and merged with regex output.

```python
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
```

### L.2 Fix Recommendations (`fixer.py`)

`fixer.py` maps each detected vulnerability type to a `FIX_RECOMMENDATIONS` entry containing a title, description, and code example. Types covered: SQL Injection, XSS, Command Injection, Hardcoded Secret, CSRF, Path Traversal, Insecure Deserialization, XXE, Open Redirect, and Insecure Storage.

### L.3 Semgrep Integration (`semgrep_scanner.py`)

`run_semgrep_scan(project_path)` invokes `semgrep --config=auto --json` on the extracted project directory. The function normalizes each Semgrep finding to the same shape as regex findings:

```python
{
    "type": check_id,
    "file": relative_path,
    "line": start_line,
    "severity": mapped_severity,  # "High" / "Medium" / "Low"
    "engine": "semgrep",
    "description": message,
    "fix_suggestion": extra.message or "",
}
```

If the `semgrep` CLI is not found in `PATH`, `run_semgrep_scan` returns `{"available": false, "findings": [], "errors": ["semgrep not found"]}` and the scan degrades gracefully to regex-only.

---

## Appendix M — Primary Backend and Configuration Source Listings

This appendix reproduces key configuration files for examiner review.

### M.1 `backend/requirements.txt`

```text
fastapi
uvicorn[standard]
sqlalchemy
pymysql
passlib[bcrypt]
bcrypt==4.0.1
python-jose[cryptography]
python-multipart
requests
httpx
reportlab
docker
lxml
openai
semgrep
```

### M.2 `frontend/package.json` (Key Dependencies)

```json
{
  "dependencies": {
    "@monaco-editor/react": "^4.7.0",
    "axios": "^1.12.2",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-icons": "^5.5.0",
    "react-router-dom": "^6.22.3",
    "recharts": "^3.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}
```

### M.3 `.env.example`

```bash
# ─── AI Features ──────────────────────────────────────────
# Leave empty to disable AI features gracefully.
OPENAI_API_KEY=
SERPER_API_KEY=
AI_SERVICE_URL=http://ai_service:8001

# ─── Database ─────────────────────────────────────────────
DATABASE_URL=mysql+pymysql://user:password@main_db/scale_db
SQLI_DATABASE_URL=mysql+pymysql://user:password@challenge_db_sqli/testdb
CSRF_DATABASE_URL=mysql+pymysql://user:password@challenge_db_csrf/csrfdb

# ─── Auth ─────────────────────────────────────────────────
# WARNING: Change SECRET_KEY before any network-exposed deployment.
SECRET_KEY=scale_graduation_project_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=600
ENABLE_BROKEN_AUTH_CHALLENGE=true

# ─── Sandbox ──────────────────────────────────────────────
SANDBOX_MAX_CODE_CHARS=200000
SANDBOX_RUN_TIMEOUT=25

# ─── Frontend ─────────────────────────────────────────────
VITE_API_URL=http://localhost:8000
```

### M.4 `docker-compose.yml` (Abridged Structure)

```yaml
networks:
  scale_net:
    name: scale_net
    driver: bridge

services:
  sandbox_base:
    build: ./backend/sandbox_base
    image: scale-sandbox-base

  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./backend:/app
      - ./challenge-sql-injection:/app/challenges/challenge-sql-injection
      - ./challenge-xss:/app/challenges/challenge-xss
      - ./challenge-csrf:/app/challenges/challenge-csrf
      - ./challenge-command-injection:/app/challenges/challenge-command-injection
      - ./challenge-broken-auth:/app/challenges/challenge-broken-auth
      - ./challenge-security-misc:/app/challenges/challenge-security-misc
      - ./challenge-insecure-storage:/app/challenges/challenge-insecure-storage
      - ./challenge-directory-traversal:/app/challenges/challenge-directory-traversal
      - ./challenge-xxe:/app/challenges/challenge-xxe
      - ./challenge-redirect:/app/challenges/challenge-redirect
    depends_on:
      main_db: { condition: service_healthy }
      challenge_db_sqli: { condition: service_healthy }
      challenge_db_csrf: { condition: service_healthy }
      sandbox_base: { condition: service_completed_successfully }
    command: ["sh", "-c", "python seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - ./Web-Videos:/app/web-videos:ro
    command: npm run dev -- --host

  ai_service:
    build: ./ai_service
    ports: ["8001:8001"]

  main_db:
    image: mysql:8.0
    ports: ["3306:3306"]
    volumes:
      - scale_db_data:/var/lib/mysql
      - ./db_init/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h localhost -uuser -ppassword || exit 1"]
      interval: 5s
      retries: 20

  challenge_db_sqli:
    image: mysql:8.0
    ports: ["3307:3306"]
    volumes:
      - ./challenge-sql-injection/users.sql:/docker-entrypoint-initdb.d/init.sql

  challenge_db_csrf:
    image: mysql:8.0
    ports: ["3308:3306"]
    volumes:
      - ./challenge-csrf/csrf.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  scale_db_data:
```

### M.5 `frontend/vite.config.ts` (Key Middleware)

The `webVideosDevPlugin` registers a Vite dev middleware (`challengeVideosMiddleware`) that serves `.mp4` files from the `Web-Videos/` directory (or its Docker mount at `./web-videos`) under the `/challenge-videos/` URL path. It validates that:

- The request URL starts with `/challenge-videos/`.
- The filename decodes to a basename-only value (no path traversal).
- The file ends with `.mp4`.
- The file exists and is a regular file.

It supports HTTP range requests (206 Partial Content) for video seeking.

---

*End of SCALE Complete System Documentation — Version: Final Release | May 2026*
