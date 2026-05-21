    # SCALE — Security Challenge and Learning Environment
    ## Complete System Documentation
    ### Version: Final Release | Graduation Project Submission
    ### Date: May 2026

    ---

    ## Abstract

    The Security Challenge and Learning Environment (SCALE) is a web-based educational platform that integrates guided vulnerability laboratories, **dual-engine static analysis** (Semgrep SAST merged with legacy regex rules) and dependency analysis of uploaded projects, competitive Red versus Blue exercises, **instructor timed lab assignments**, **formal quiz assignments with due dates and time limits**, and **adaptive “common mistakes” quizzes** derived from prior wrong answers for structured cybersecurity instruction. The student dashboard surfaces **gamified feedback**—a three-tier **Defense Level** (Beginner / Intermediate / Advanced) derived from backend learning analytics, a **client-side XP-style score** combining lab completions and quiz averages, per-lab **Challenge Mastery** bars, and optional **narrative “XP gained”** values on attack-success screens—while distinguishing **persisted** metrics (MySQL via `user_learning_progress`, `UserProgress`, `QuizAttempt`) from **display-only** figures that are not stored as currency. The system addresses the gap between passive lecture delivery and unstructured capture-the-flag platforms by providing instructor dashboards, role-based access control, repeatable sandbox validation of remediated code, and portfolio-grade reporting. The architecture centers on a FastAPI backend exposing REST endpoints under `/api`, a React 18 single-page application built with Vite 5 and TypeScript, three MySQL 8.0 instances for the primary application database, the SQL injection challenge database, and the CSRF challenge database, and an optional `ai_service` container on port 8001. Docker Compose supplies a shared bridge network `scale_net`, mounts the Docker socket into the backend for per-submission container builds, serves voiced tutorial MP4s from `Web-Videos/` via a Vite dev middleware, and persists main database state in the named volume `scale_db_data`. Students progress through scanning uploaded ZIP archives or Git repositories, reviewing findings and dependency advisories from OSV.dev, completing ten interactive labs spanning injection, cross-site, session, misconfiguration, storage, traversal, XML, and redirect flaws, validating fixes inside disposable Python 3.9 slim images, and consolidating evidence into a multi-section ReportLab PDF. Supplementary features include animated attack replays, unified code diffs with security annotations, AI mentor chat and scan enrichment when `OPENAI_API_KEY` or `SERPER_API_KEY` is present, dual quiz pipelines (`/api/quizzes` static bank with normalized assignment tables and `/api/quiz` dynamic), instructor AI-assisted assignment creation, administrative security log review, peer messaging, and a public **promotional trailer** at `/trailer` (GSAP + Three.js cinematic demo with MIU branding). Three roles—student (`user`), instructor, and administrator—govern registration approval, dashboard routing, and privileged operations. The platform is designed so that assessors may understand design intent, data flows, and residual risk without inspecting source code directly.

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
    - [10. Security Event Logging](#10-security-event-logging)
    - [11. Messaging System](#11-messaging-system)
    - [12. AI Services](#12-ai-services)
    - [13. Red vs Blue Team Mode](#13-red-vs-blue-team-mode)
    - [14. Complete API Reference](#14-complete-api-reference)
    - [15. Frontend Pages Reference](#15-frontend-pages-reference)
    - [16. Environment and Configuration](#16-environment-and-configuration)
    - [17. Setup and Deployment](#17-setup-and-deployment)
    - [18. Known Limitations and Technical Debt](#18-known-limitations-and-technical-debt)
    - [19. Security Analysis](#19-security-analysis)
    - [20. Testing and Verification Strategy](#20-testing-and-verification-strategy)
    - [21. Operational Failure Modes and Error Handling](#21-operational-failure-modes-and-error-handling)
    - [Appendix A — Complete Annotated File Tree](#appendix-a--complete-annotated-file-tree)
    - [Appendix B — Complete Route Map](#appendix-b--complete-route-map)
    - [Appendix C — Glossary](#appendix-c--glossary)
    - [Appendix D — Development Changelog](#appendix-d--development-changelog)
    - [Appendix E — ORM Models](#appendix-e--orm-models-complete-column-reference)
    - [Appendix F — Learning Progress Module](#appendix-f--learning-progress-module-full-source)
    - [Appendix G — Hints and Replays](#appendix-g--challenge-hints-and-attack-replay-payloads-source-extracts)
    - [Appendix H — Frontend Components](#appendix-h--frontend-components-frontendsrccomponents)
    - [Appendix I — Challenge Directories](#appendix-i--challenge-docker-bind-mounts-and-directories)
    - [Appendix J — Docker and Environment](#appendix-j--docker-compose-and-environment-expanded-reference)
    - [Appendix K — Route Handlers](#appendix-k--http-route-to-python-handler-names)
    - [Appendix L — Scanner Rules](#appendix-l--static-scanner-rules-backendappscannerrulespy)
    - [Appendix M — Source Listings](#appendix-m--primary-backend-and-configuration-source-listings)

    ---

    ## 1. Introduction

    ### 1.1 Problem Statement

    Cybersecurity education requires more than conceptual coverage of OWASP categories; learners must manipulate realistic inputs, observe server-side effects, and iterate on defenses. Lecture-only delivery fails to build muscle memory for secure coding practices. Generic learning management systems lack sandboxed execution for fix validation and do not model adversarial team dynamics. Publicly available vulnerable applications such as DVWA provide exploitation surfaces but do not integrate with instructor grading, analytics, or structured progress across multiple courses. Capture-the-flag platforms emphasize competition over pedagogy and rarely align with syllabus milestones. SCALE exists to bridge this gap by combining instructor oversight, measurable progress, and hands-on exploitation and remediation within a single deployable stack.

    Hands-on practice is essential because vulnerabilities manifest as interactions between parsers, frameworks, and data flows that cannot be understood purely from static reading. Students must see how SQL parsers interpret delimiters, how browsers execute injected markup, and how cross-site request forgery relies on ambient authority. SCALE provides bounded, logged simulations so that experimentation produces educational telemetry without exposing unrelated production systems.

    Existing tools are insufficient for structured undergraduate education with instructor oversight because they lack unified role models, do not persist per-student analytics in a relational schema suitable for grading exports, and do not combine static scanning of student projects with lab completion in one dashboard. SCALE aggregates scan history, quiz attempts, challenge completion, and remediation evidence for portfolio PDF generation.

    ### 1.2 Project Objectives

    1. Provide a FastAPI backend with JWT authentication, role-based access control, and MySQL persistence for users, progress, quizzes, messages, scans, and security logs.
    2. Deliver ten sandbox-validated OWASP-style labs with distinct attack surfaces, fix submission endpoints, and Docker-based unittest scoring.
    3. Implement ZIP upload (and optional Git clone) of projects up to 50 MB with safe extraction, **Semgrep + regex** static scanning with severity scoring and fix recommendations.
    4. Integrate OSV.dev dependency vulnerability queries with concurrency caps and background merging into scan results.
    5. Offer AI-assisted mentoring, scan explanation, and quiz generation when OpenAI or Serper API keys are configured, with graceful degradation.
    6. Support instructor quiz creation, assignment to students with **time limits and due dates**, AI-assisted bulk generation with fallback to the static bank, and **adaptive common-mistakes quizzes** from prior wrong answers.
    7. Provide student dashboards with challenge mastery visualization, quiz history, **instructor-assigned timed lab tasks**, PDF export, and Red versus Blue game notifications.
    8. Implement Red versus Blue team games mapped to lab identifiers 1–10 with live attack polling and fix validation.
    9. Record security events with context classification and present an admin console for review.
    10. Provide internal messaging between users with unread counts in the sidebar.

    ### 1.3 Scope and Boundaries

    SCALE provides web application security training, static analysis, quizzes, and reporting. It does not provide network penetration testing against arbitrary hosts, malware analysis, or mobile application security. It assumes deployment via Docker Compose on a developer workstation or small server with Docker socket access for sandbox builds. It assumes trusted operators for the host because the backend mounts `/var/run/docker.sock`. SCALE does not guarantee production-grade isolation for command-injection pedagogy on the live ping endpoint; the implementation uses guarded subprocess execution.

    ### 1.4 Document Organization

    Section 2 describes the learning model and feature inventory. Section 3 documents architecture (including data flow and trust boundaries), databases, and frontend state. Sections 4–8 cover authentication, challenges (including sandbox **`improvement_score`**, narrative attack XP, and **§5.10 timed lab assignments**), **Semgrep + regex scanner (§6)**, reports, and quizzes (including **assignments, mistakes quiz**). **Section 9** is the **full learning analytics reference** (Defense Level, skill buckets, streak, dashboard XP, instructor/admin stats). Sections 10–13 cover logging, messaging, AI, and Red vs Blue. Sections 14–15 list APIs and pages (including **`/trailer`** and assignment routes). Sections 16–17 cover configuration and deployment (**§17.7 dependency pinning**). Sections 18–19 state limitations and security posture (**documented vs implemented JWT gap**). **Section 20** documents **testing and verification** (manual matrix, sandbox examples, untested paths). **Section 21** documents **failure modes**. **Section 10.2** covers **log retention and privacy**. Appendices provide file tree, route map (**128 routes**), glossary, source listings, and changelog (**Phase 6 — May 2026**).

    ---

    ## 2. System Overview

    ### 2.1 Platform Description

    SCALE is a three-role learning platform. Students complete labs, upload projects for scanning, take quizzes, and participate in Red versus Blue games. Instructors manage quizzes, approve students, assign work, and create games. Administrators manage users, view security logs, and access aggregate statistics. Unlike a static course site, SCALE executes server-side challenge logic, persists progress, and generates downloadable evidence artifacts.

    ### 2.2 Core Learning Model — Scan → Attack → Fix → Quiz → Progress

    **Scan:** The student uploads a ZIP via `POST /api/project/upload` (`projects.py`) or clones a Git repo via `POST /api/project/scan-from-git`. The frontend stores results in `ScanContext` under `scale.scanData.{user_id}` in `localStorage`. The student runs `POST /api/project/scan`, which walks extracted files, runs **Semgrep + regex** (`semgrep_scanner.py`, `detector.py`), scores risk in `scorer.py`, attaches fixes in `fixer.py`, persists `ScanHistory` rows, and starts a background thread for `scan_dependencies()` in `dependency_scanner.py`.

    **Attack:** For each lab, the student opens attack routes under `/challenges/{n}/attack` or tabbed routes, invoking endpoints such as `POST /api/challenges/vulnerable-login` or `POST /api/challenges/xss/comments` (`challenges.py`). Success is detected by HTTP responses and client-side success maps.

    **Fix (sandbox-validated — primary persistence path):** The student submits Python source via `POST /api/challenges/submit-fix*` routes. On **`fixed == true`**, the backend calls `mark_challenge_complete`, inserts **`UserProgress`**, and runs `recalculate_learning_progress`. This is the path used for **graded remediation evidence** and PDF reports.

    **Attack-only completion (optional shortcut):** After a successful attack, the UI may call **`POST /api/challenges/mark-attack-complete?challenge_type=<slug>`**, which also inserts **`UserProgress`** and recalculates learning metrics **without sandbox validation**. Mastery bars and `vulnerabilities_solved` therefore reflect attack completion even when no fix was submitted. Instructors should treat **sandbox-passing fixes** as the authoritative remediation signal; attack-only rows are a UX convenience, not proof of secure code.

    **Quiz:** Students use `StudentQuizPage` to call `POST /api/quizzes/take` for bank quizzes or `POST /api/quiz/generate` for scan-driven quizzes (`quiz_dynamic.py`). Attempts persist via `POST /api/quizzes/submit-attempt`.

    **Progress:** `GET /api/stats/progress/me` returns `build_learning_progress_payload` plus `challenge_detail` bar chart data. The backend persists **Defense Level** (`level`), **streak_days**, **learning_speed**, **retention_score**, **accuracy**, and **skills** buckets; the dashboard also shows a **non-persisted XP-style `currentXp`** derived in the browser (Section 9.6). Attack-success pages show **narrative XP** numbers that are display-only (Section 5.9).

    ### 2.3 Feature Inventory

    | Feature | Description | User Role | Primary Implementation |
    |--------|-------------|-----------|-------------------------|
    | ZIP upload and static analysis | Upload ZIP or Git repo, extract whitelisted code, **Semgrep + regex** scan | Student | `projects.py`, `semgrep_scanner.py`, `detector.py` |
    | Dependency scanning (OSV.dev) | Manifests parsed, POST to `https://api.osv.dev/v1/query` | Student | `dependency_scanner.py` |
    | Ten interactive labs | Attack, fix, tutorial flows per OWASP category | Student | `challenges.py`, `frontend/src/pages/*` |
    | Docker sandbox fix validation | Build image, run `run_tests.sh`, timeout 25s | Student | `sandbox_runner.py` |
    | Code diff viewer | Unified diff with annotations | Student | `CodeDiffViewer.tsx`, `generate_code_diff` |
    | Attack replay visualizer | Stepper UI over `ATTACK_REPLAYS` | Student | `AttackReplayVisualizer.tsx` |
    | AI mentor | Mentor chat and `/api/ai/analyze-code` | Student | `ai_mentor.py`, `ChallengeHintPanel.tsx` |
    | AI quiz generation | Instructor AI assign and dynamic quiz | Instructor, Student | `quizzes.py`, `quiz_dynamic.py` |
    | Static MCQ bank | Topics, difficulty, random sampling; **200 seeded questions** across 20 topics | Student | `quizzes.py`, `seed_db.py` |
    | Quiz assignments | Instructor assigns bank questions with **time_limit_minutes**, **due_date**, per-student status | Instructor, Student | `quizzes.py`, `StudentQuizPage.tsx` |
    | Common mistakes quiz | AI or fallback quiz from student's prior wrong answers | Student, Instructor | `quizzes.py`, `StudentQuizPage.tsx`, `InstructorDashboardPage.tsx` |
    | Timed lab assignments | Instructor assigns a lab fix task with countdown timer and sandbox grading | Instructor, Student | `challenge_assignments.py`, `ChallengeAssignmentPage.tsx` |
    | Promotional trailer | Public cinematic demo at `/trailer` (GSAP + Three.js, MIU logos) | Public | `TrailerPage.tsx` |
    | Voiced tutorial videos | MP4 playback via `/challenge-videos/` dev middleware | Student | `ChallengeTutorialVideo.tsx`, `vite.config.ts`, `Web-Videos/` |
    | Pentest PDF report | Five-section ReportLab PDF | Student | `report.py` |
    | Challenge progress reset | `DELETE /api/challenges/progress/{slug}` | Student | `challenges.py`, `ChallengesListPage` |
    | Challenge mastery chart | `challenge_detail` horizontal bars | Student | `DashboardHomePage.tsx`, `learning_tracker.py` |
    | Red vs Blue mode | Teams, attacks, fixes | Instructor, Student | `red_blue.py` |
    | My Games portal | Student `GET /api/redblue/my-games` | Student | `RedBlueMyGamesPage.tsx` |
    | Role dashboards | Admin, instructor, student stats | All | `stats.py`, dashboard pages |
    | Security logging | `security_logs` table and filters | Admin | `security_logger.py`, `security_logs.py` |
    | Admin user management | Approve, role, delete | Admin | `auth.py` |
    | Messaging | Unread count and threads | All | `messages.py`, `Sidebar.tsx` |
    | AI status indicator | `GET /api/ai/status` | Student | `DashboardHomePage.tsx` |
    | Tab-isolated auth | `sessionStorage` keys | All | `LoginPage.tsx`, `ProtectedRoute.tsx` |
    | User-scoped scan storage | `scale.scanData.{user_id}` | Student | `ScanContext.tsx` |
    | Gamified progress & analytics | Defense Level tiers, skill buckets, streak, retention, dashboard XP (client), mastery bars | Student | `learning_tracker.py`, `DashboardHomePage.tsx` |
    | Instructor / admin analytics | Class completion, per-bucket performance, challenge usage & attempts | Instructor, Admin | `stats.py`, dashboard pages |

    ### 2.4 Technology Stack

    | Layer | Technology | Version | Purpose |
    |-------|------------|---------|---------|
    | Backend runtime | Python | 3.x (image 3.9-slim in sandbox) | Server and sandbox |
    | Backend framework | FastAPI | unpinned in `requirements.txt` | REST API |
    | ASGI server | Uvicorn | `[standard]` extra | ASGI |
    | ORM | SQLAlchemy | unpinned | Database access |
    | MySQL driver | PyMySQL | unpinned | MySQL connectivity |
    | Auth hashing | passlib bcrypt, bcrypt | `bcrypt==4.0.1` | Password hashing |
    | JWT | python-jose | `[cryptryptography]` | Tokens |
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

    **Reproducibility note:** Python dependencies in `backend/requirements.txt` pin **only** `bcrypt==4.0.1`; FastAPI, SQLAlchemy, Uvicorn, and most other packages are **unpinned**. Node dependencies use **semver ranges** in `frontend/package.json` (e.g. `^18.2.0`). Builds are therefore **not bit-for-bit reproducible** across time unless operators **freeze** versions (`pip freeze`, `npm ci` with lockfile). For examination or deployment, capture a **snapshot** of resolved versions alongside this document.

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

    ### 3.1.1 Data flow, trust boundaries, and student artifact path

    The diagram below complements the deployment view in Section 3.1. It shows how **student-owned project code** (ZIP upload) and **remediation code** (fix submissions) cross **trust boundaries** before affecting persisted results or scores.

    **Trust zones (summary):**

    | Zone | Boundary | What is trusted |
    |------|----------|-----------------|
    | Browser | User agent | Same-origin SPA; JWT in `sessionStorage` is readable to scripts on that origin (Section 19). |
    | API process | FastAPI on `backend` container | Validates JWT, enforces roles, writes MySQL; does not trust file contents as safe code. |
    | Extracted project | Host filesystem under `uploads/` | Treated as **untrusted** input for regex scanning; never executed as application code during static scan. |
    | Sandbox container | Ephemeral Docker build on `scale_net` | Executes **only** the challenge template harness (`run_tests.sh` + unittest) with submitted `app.py` replacement; network and resources capped in `sandbox_runner.py`. |
    | External OSV | `https://api.osv.dev` | Treated as **best-effort**; failures degrade to partial dependency results (Section 21). |

    ```mermaid
    flowchart LR
    subgraph browser [Browser — untrusted user input]
        U[Student]
        ZIP[ZIP file]
        FIX[Fix source code textarea]
    end

    subgraph api [FastAPI — authenticated API]
        UP[POST /api/project/upload]
        EX[Extract + whitelist extensions]
        SC[POST /api/project/scan]
        RG[rules.py + detector + scorer]
        DEP[Background: dependency_scanner → OSV]
        SF[POST /api/challenges/submit-fix*]
    end

    subgraph data [Persistence — trusted store]
        DB[(MySQL scale_db)]
        SH[scan_history.vuln_summary JSON]
    end

    subgraph sb [Sandbox — isolated execution]
        IMG[Docker build per submission]
        TST[run_tests.sh + unittest]
    end

    U --> ZIP --> UP --> EX --> SC
    SC --> RG --> DB
    SC --> SH
    SC -.-> DEP
    FIX --> SF --> IMG --> TST
    TST -.->|pass/fail counts, logs| SF
    SF --> DB
    ```

    **Narrative path (upload → scan → results):** The student selects a ZIP in the Scanner page. The browser sends it to `POST /api/project/upload`; the backend stores the archive and extracts allowed source files to a user-scoped folder, creating a `Project` row. `POST /api/project/scan` walks extracted files, applies `RULES` and heuristics, computes severity-weighted scores, persists a `ScanHistory` row with `vuln_summary` JSON, and starts a **background thread** that queries OSV for dependency advisories and merges results into the same summary. The HTTP response returns static/regex findings immediately; dependency rows may populate shortly after via refresh on the Dependencies tab.

    **Narrative path (fix → sandbox → score):** Fix submissions never reuse the uploaded project tree for execution. They replace `app.py` inside a **known challenge directory** (bind-mounted from `challenge-*` at `/app/challenges/...`). `_verify_fix_improvement` runs the sandbox twice (vulnerable baseline vs. student code) and derives `improvement_score` (Section 5.2.1).

    ### 3.2 Docker Compose Services

    | Service | Image/Build | Internal Port | External Port | Volumes | Depends On | Purpose |
    |---------|-------------|-----------------|---------------|---------|------------|---------|
    | sandbox_base | build `./backend/sandbox_base` | — | — | — | — | Base image build |
    | backend | build `./backend` | 8000 | 8000 | docker.sock, backend, challenge dirs | DBs, sandbox_base | API + sandbox |
    | frontend | build `./frontend` | 5173 | 5173 | frontend, node_modules volume | — | SPA dev |
    | ai_service | build `./ai_service` | 8001 | 8001 | ai_service | — | Template AI |
    | main_db | mysql:8.0 | 3306 | 3306 | scale_db_data, init.sql | — | App data |
    | challenge_db_sqli | mysql:8.0 | 3306 | 3307 | users.sql | — | SQLi challenge |
    | challenge_db_csrf | mysql:8.0 | 3306 | 3308 | csrf.sql | — | CSRF challenge |

    ### 3.3 Startup Sequence

    `docker compose up --build` builds images, starts `sandbox_base` to completion, starts MySQL containers with healthchecks, then starts `backend` after `depends_on` conditions succeed. The backend runs `seed_db.py` then `uvicorn ... --reload`. On startup, `startup_event` retries `create_all` up to ten times with three-second delays until MySQL accepts connections. `_ensure_runtime_schema()` patches missing columns on `security_logs`, `user_learning_progress`, `teams`, `game_challenges`, `red_team_actions`, and `blue_team_fixes`. `seed_db.py` waits for MySQL, creates tables, seeds default accounts (**development only — rotate before exposure; Section 17.2**), and inserts up to 200 quiz questions if fewer exist.

    ### 3.4 Network Configuration

    `scale_net` is a bridge network attaching backend, frontend, databases, and ai_service so internal DNS names resolve. CORS is explicit as listed in `main.py`. The Docker socket must be mounted so `docker.from_env()` can build and run sandbox images; this grants significant host capability and is documented as a development-oriented choice.

    ### 3.5 Backend Architecture

    #### 3.5.1 Application Structure
    - `backend/app/main.py` — FastAPI app factory, CORS, routers, startup.
    - `backend/app/models.py` — SQLAlchemy models.
    - `backend/app/schemas.py` — Pydantic schemas.
    - `backend/app/crud.py` — User CRUD helpers.
    - `backend/app/db/database.py` — Engine and session.
    - `backend/app/sandbox_runner.py` — Docker sandbox, diff generation.
    - `backend/app/api/*.py` — Routers.
    - `backend/app/scanner/*.py` — Detection, scoring, fixes, dependency scan.
    - `backend/app/security/*.py` — Logging and learning analytics.
    - `backend/seed_db.py` — Seeding.

    #### 3.5.2 Application Factory (`main.py`)

    Routers: `auth` `/api/auth`, `quizzes` `/api/quizzes`, `challenges` `/api/challenges`, `stats` `/api/stats`, `messages` `/api/messages`, `projects` `/api` (no extra prefix), `game_challenge` `/api/challenge`, `misconfig` `/api`, `ai_mentor` `/api/ai`, `attack_simulator` `/api/attack`, `project_analyzer` `/api`, `security_logs` `/api/security`, `quiz_dynamic` `/api/quiz`, `instructor` `/api/instructor`, `report` prefix `/api/report`, `red_blue` `/api/redblue`, **`challenge_assignments` `/api/challenge-assignments`**.

    Startup runs `models.Base.metadata.create_all`, then **`_ensure_runtime_schema()`** — a lightweight runtime migration guard that `ALTER TABLE`s missing columns (quiz assignment timing fields, red/blue phase columns, `questions.targets_mistake`, etc.) when Alembic is not used. Logs AI status via `OPENAI_API_KEY` and `SERPER_API_KEY` environment variables.

    #### 3.5.3 Dependency Injection

    `OAuth2PasswordBearer` reads optional bearer token. `get_current_user` decodes JWT from header or `access_token` cookie, loads user by email, returns 401 if invalid. `get_db` yields `SessionLocal`. `require_role(*roles)` maps `student` to `user` and returns 403 if role not allowed.

    #### 3.5.4 Router Organization

    | Router File | Prefix | Tags | Primary Responsibility |
    |-------------|--------|------|------------------------|
    | auth.py | /api/auth | auth | Login, register, admin |
    | challenges.py | /api/challenges | challenges | Labs, fixes, hints, replay |
    | projects.py | /api | projects | Upload, scan, reports |
    | quizzes.py | /api/quizzes | quizzes | Bank, assignments, take |
    | quiz_dynamic.py | /api/quiz | quiz_dynamic | Dynamic generation |
    | stats.py | /api/stats | statistics | Dashboards |
    | messages.py | /api/messages | messages | Messaging |
    | security_logs.py | /api/security | security_logs | Admin logs |
    | instructor.py | /api/instructor | instructor | Analytics, reset |
    | report.py | /api/report | report | PDF |
    | red_blue.py | /api/redblue | redblue | Red/Blue games |
    | challenge_assignments.py | /api/challenge-assignments | challenge_assignments | Timed instructor lab assignments |
    | ai_mentor.py | /api/ai | ai_mentor | AI endpoints |
    | game_challenge.py | /api/challenge | game_challenge | Legacy game API |
    | misconfig.py | /api | misconfig | Misconfig lab |
    | attack_simulator.py | /api/attack | attack_simulator | Simulation |
    | project_analyzer.py | /api | project_analyzer | Structure |

    ### 3.6 Frontend Architecture

    #### 3.6.1 Application Structure

    - `frontend/src/App.tsx` — Route table.
    - `frontend/src/lib/api.ts` — Axios instance with `withCredentials`.
    - `frontend/src/context/ScanContext.tsx` — User-scoped scan storage.
    - `frontend/src/components/` — Layout, modals, replay, diff.
    - `frontend/src/pages/` — Page components.

    #### 3.6.2 Routing (`App.tsx`)

    `/` Landing, `/login`, `/register`, **`/trailer`** public. Protected shell: `/home` Dashboard, `/challenges`, `/messages`, `/scanner`, `/attack-lab`, challenge routes `/challenges/1..10/...`, `/challenges/attack-success`, `/redblue/game/:gameId`. Nested `user` only: `/quiz`, `/redblue/my-games`, **`/assignment/:assignmentId`**. Instructor: `/instructor/dashboard`, `/instructor/quiz`, **`/instructor/assignment/:assignmentId/results`**, `/redblue/create`. Admin: `/admin/stats`, `/admin/dashboard`, `/admin/logs`. Unknown paths redirect to `/`.

    #### 3.6.3 Authentication State (`sessionStorage`)

    Keys: `token`, `role`, `user_id`, `user_email`. Session storage isolates tabs. `ProtectedRoute` calls `GET /api/auth/me` and clears storage on failure.

    #### 3.6.4 API Client (`api.ts`)

    `baseURL` is `import.meta.env.VITE_API_URL || 'http://localhost:8000'`. Interceptor sets `Authorization: Bearer` when token is present and not `cookie-auth`. `withCredentials: true` sends cookies. Direct `fetch` would omit interceptor behavior.

    #### 3.6.5 Scan Context (`ScanContext.tsx`)

    Stores `scanData` with `projectId` and `results`. Key is `scale.scanData.{user_id}` in `localStorage`. On logout, `Sidebar` removes `scale.scanData.{user_id}`. `scale-user-changed` event refreshes context when user changes.

    ### 3.7 Database Architecture

    #### 3.7.1 Three Database Instances

    | Instance | External Port | Internal | Database | Purpose |
    |----------|---------------|----------|----------|---------|
    | main_db | 3306 | 3306 | scale_db | Users, progress, scans, messages |
    | challenge_db_sqli | 3307 | 3306 | testdb | SQLi login data |
    | challenge_db_csrf | 3308 | 3306 | csrfdb | CSRF bank accounts |

    #### 3.7.2 ORM Models — Complete Reference

    ##### Model: User
    **Table:** `users`

    | Column | Type | Constraints | Description |
    |--------|------|-------------|-------------|
    | id | Integer | PK | User id |
    | email | String(255) | unique, indexed | Login email |
    | hashed_password | String(255) | | bcrypt hash |
    | role | String(50) | default `user` | user | instructor | admin |
    | is_approved | Boolean | default True | False for pending instructors |

    **Relationships:** `UserAnswer`, `UserProgress`, `QuizAttempt`  
    **Used by:** Auth, dashboards, all user-scoped features

    ##### Model: UserProgress
    **Table:** `user_progress`

    | Column | Type | Constraints | Description |
    |--------|------|-------------|-------------|
    | id | Integer | PK | |
    | user_id | Integer | FK users.id | Owner |
    | challenge_id | String(50) | | Slug or legacy id |
    | completed_at | DateTime | default utcnow | Completion time |

    **Relationships:** `user`  
    **Used by:** `challenges.py`, stats, PDF

    ##### Model: XSSComment
    **Table:** `xss_comments` — id, author, content — XSS lab storage.

    ##### Model: Challenge
    **Table:** `challenges` — id, title, description — metadata for titles in PDF.

    ##### Model: Question / QuestionOption / UserAnswer / QuizAssignment / QuizAssignmentStudent / QuizAssignmentQuestion / QuizAttempt
    Quiz bank, assignments, attempts — see `models.py` for full column types.

    ##### Model: CSRFAccount
    **Table:** `csrf_accounts` — mirrors ORM for CSRF challenge balances.

    ##### Model: Message
    **Table:** `messages` — sender_id, receiver_id, content, created_at, is_read.

    ##### Model: Project / ScanHistory
    Projects and scan history JSON in `vuln_summary`. Scan payloads include **`scanner_engines.semgrep`** availability and merged finding counts.

    ##### Model: ChallengeAssignment / ChallengeAssignmentStudent
    **Tables:** `challenge_assignments`, `challenge_assignment_students` — instructor-created timed lab tasks: `challenge_slug`, `time_limit_minutes`, `due_date`, per-student `status` (`assigned` → `in_progress` → `passed`/`failed`/`expired`), `sandbox_passed`, `score`, `fix_code_submitted`. Used by `challenge_assignments.py` and `ChallengeAssignmentPage.tsx`.

    ##### Model: Team / TeamMember / GameChallenge / ChallengeVulnerability / RedTeamAction / BlueTeamFix
    Red versus Blue tables; `GameChallenge.lab_challenge_id` maps to labs 1–10.

    ##### Model: ChallengeState
    **Table:** `challenge_state` — per-user per-challenge attempts, hints, time.

    ##### Model: SecurityLog
    **Table:** `security_logs` — event_type, severity, payload, endpoint, metadata JSON, context_type.

    ##### Model: UserLearningProgress
    **Table:** `user_learning_progress` — aggregates including streak_days, learning_speed, retention_score.

    ---

    ## 4. Authentication and Authorization

    ### 4.1 Registration
    `POST /api/auth/register` accepts `UserCreate` with email, password, role default `user`. Admin self-registration is forbidden. Password hashed with bcrypt via passlib. Instructors self-registering receive `is_approved=False` until admin approval.

    ### 4.2 Login
    Normal path verifies bcrypt hash, requires `is_approved`, issues JWT with `sub=email`, `role`, `exp`, sets HttpOnly cookie `access_token` (name configurable). `ENABLE_BROKEN_AUTH_CHALLENGE` enables SQLite in-memory branch for `challenge=broken-auth` with `f"SELECT * FROM users WHERE email = '{user.username}' AND password = '{user.password}'"` for pedagogy.

    ### 4.3 Role-Based Access Control
    `require_role` normalizes `student`→`user`. Table: students register as `user` (approved); instructors may be pending; admin created by admin; dashboards route per role.

    ### 4.4 Tab-Isolated Sessions
    `sessionStorage` is tab-scoped so multiple roles can be tested in parallel sessions.

    ### 4.5 Logout
    `POST /api/auth/logout` deletes cookie. Frontend clears sessionStorage and scan key and dispatches `scale-user-changed`.

    ### 4.6 Token Validation
    Bearer first, then cookie; decode with `SECRET_KEY` and `JWT_ALGORITHM` default HS256.

    ---

    ## 5. Challenge System

    ### 5.1 Challenge Catalog

    | ID | Slug | Vulnerability | Attack | Fix | Sandbox |
    |----|------|---------------|--------|-----|---------|
    | 1 | sql-injection | SQL Injection | `/api/challenges/vulnerable-login` | `/api/challenges/submit-fix` | challenge-sql-injection |
    | 2 | xss | XSS | `/api/challenges/xss/comments` | `/api/challenges/submit-fix-xss` | challenge-xss |
    | 3 | csrf | CSRF | `/api/challenges/csrf/transfer` | `/api/challenges/submit-fix-csrf` | challenge-csrf |
    | 4 | command-injection | Command Injection | `/api/challenges/ping` | `/api/challenges/submit-fix-command-injection` | challenge-command-injection |
    | 5 | broken-auth | Broken Authentication | Auth branch + labs | `/api/challenges/submit-fix-auth` | challenge-broken-auth |
    | 6 | security-misc | Security Misconfiguration | `GET /api/admin/config` — **any logged-in user** (missing **authorization**; see §5.2.2) | `/api/challenges/submit-fix-misc` | challenge-security-misc |
    | 7 | insecure-storage | Insecure Storage | `/api/challenges/storage/*` | `/api/challenges/submit-fix-storage` | challenge-insecure-storage |
    | 8 | directory-traversal | Directory Traversal | `/api/challenges/traversal/read` | `/api/challenges/submit-fix-traversal` | challenge-directory-traversal |
    | 9 | xxe | XXE | `/api/challenges/xxe/parse` | `/api/challenges/submit-fix-xxe` | challenge-xxe |
    | 10 | redirect | Unvalidated Redirect | `/api/challenges/redirect` | `/api/challenges/submit-fix-redirect` | challenge-redirect |

    ### 5.2 Challenge Architecture Pattern
    Tutorial → attack → fix → optional `mark-attack-complete`. Fix posts JSON `{"code": "..."}` to submit-fix routes. `_verify_fix_improvement` runs sandbox twice; success requires `after_result.success` and zero failures/errors. **`mark_challenge_complete`** is invoked on **both** successful sandbox fixes and on **`POST /api/challenges/mark-attack-complete`** (attack-only, no code validation).

    ### 5.2.2 Security Misconfiguration lab — `GET /api/admin/config` auth model

    This endpoint is **not** unauthenticated. It uses `Depends(get_current_user)` in `misconfig.py`: the caller must present a **valid JWT** (Bearer header or `access_token` cookie). There is **no `require_role("admin")` check** — any authenticated student, instructor, or admin may read the response. That missing **authorization** step (authentication without role enforcement) is the **intentional misconfiguration** taught in lab 6; it is **not** an accidental auth bypass on a production admin API.

    The JSON body includes a **pedagogical snapshot** (`debug: true`, sample `secret_key`, `database_url`, filtered `env_sample`) — not a live dump of all production secrets, but realistic enough to teach impact. Students reach it **while logged in** with their normal session token after completing the attack flow in `SecurityMiscAttackPage.tsx`.

    ### 5.2.1 Improvement score (`improvement_score`)

    The field **`improvement_score`** is returned on every fix submission path that calls `_verify_fix_improvement` in `challenges.py` (and the same structure is reused for Red vs Blue fixes in `red_blue.py`). It quantifies how much the student’s submission **reduced unittest failure and error counts** relative to the vulnerable baseline, independent of whether the lab is considered fully “fixed.”

    **Computation (from `_verify_fix_improvement`):**

    1. `before_result` = `run_in_sandbox_detailed` with the **on-disk vulnerable** `app.py` from the challenge directory.
    2. `after_result` = `run_in_sandbox_detailed` with the **submitted** source string.
    3. `before_count` = `failures + errors` from the baseline run (unittest aggregate).
    4. `after_count` = `failures + errors` from the student run.
    5. **`fixed`** is true only if the after-run reports `success` **and** `after_count == 0` (all tests green).
    6. **`improvement_score`** (integer 0–100):
    - If `before_count == 0` and `after_count == 0`, the score is **100** (edge case: already clean baseline).
    - Otherwise: \(\lfloor \min(100, \max(0, \frac{\text{before\_count} - \text{after\_count}}{\max(\text{before\_count}, 1)} \times 100)) \rfloor\).

    **Interpretation for UX:** A high `improvement_score` with `fixed == false` means tests still fail but the student moved the needle; a low score with `fixed == true` should not occur if the success predicate is consistent. The **code diff** (`code_diff`) is only attached when `fixed` is true and vulnerable source existed, for display in `ResultModal` / `CodeDiffViewer`.

    **Glossary cross-reference:** See Appendix C under **`improvement_score`**.

    ### 5.3 Individual Challenge Documentation
    Each challenge includes a `challenge-*` directory with `app.py`, `requirements.txt`, `run_tests.sh`, and unittest tests. `DIFF_ANNOTATIONS` in `sandbox_runner.py` covers slugs: sql-injection, xss, command-injection, csrf, broken-auth, directory-traversal, xxe (not all ten slugs have annotations).

    ### 5.4 Sandbox Fix Validation
    Docker builds from Python 3.9 slim, network `scale_net`, `mem_limit=256m`, `cpu_quota=50000`, `pids_limit=128`, `SANDBOX_RUN_TIMEOUT` default 25s. Image removed after run.

    ### 5.5 Code Diff Viewer
    `CodeDiffViewer` renders side-by-side table with red/green rows, annotation tooltips.

    ### 5.6 Attack Replay
    `GET /api/challenges/replay/{slug}?sample=true` bypasses completion check. Steps stored in `ATTACK_REPLAYS`.

    ### 5.7 Hint System
    `GET /api/challenges/hints` for csrf, broken-auth, security-misc, directory-traversal, xxe, insecure-storage. Separate advanced hints via `POST /api/challenge/hint` in `game_challenge.py`.

    ### 5.8 Challenge Progress and Reset
    `DELETE /api/challenges/progress/{slug}` removes `UserProgress` and `ChallengeState` variants and recalculates learning progress.

    ### 5.9 Attack-success narrative XP (display only)

    After a successful attack, students may navigate to `/challenges/attack-success?type=<slug>` (`AttackSuccessPage.tsx`). The page reads **`typeConfig`** in that component: for each challenge slug it defines a **title**, **subtitle**, **explanation**, and a static integer **`xp`** (110–160) labeled “XP gained” in the UI.

    | Slug | Narrative XP shown | Notes |
    |------|-------------------|--------|
    | `sql-injection` | 150 | Highest narrative XP in the table |
    | `command-injection` | 160 | Highest value in `typeConfig` |
    | `csrf` | 130 | |
    | `xss` | 120 | Default fallback if slug missing |
    | `redirect` | 110 | Lowest in table |
    | `broken-auth` | 140 | |
    | `security-misc` | 140 | |
    | `directory-traversal` | 130 | |
    | `xxe` | 140 | |
    | `insecure-storage` | 130 | |

    These numbers are **not** sent to the backend, **not** added to `currentXp` on the dashboard, and **not** stored in any table. They exist solely to reinforce accomplishment after viewing an attack replay. The **authoritative remediation** signal is a **sandbox-passing fix** (`fixed == true` on submit-fix routes). **`UserProgress`** may also be written by **`mark-attack-complete`** without a fix (Section 2.2); that path updates mastery UI but does not prove secure code.

    ### 5.10 Instructor timed lab assignments

    Instructors create **timed fix assignments** via `POST /api/challenge-assignments/create` (`challenge_assignments.py`), selecting one of the ten lab slugs, a title, optional instructions, **`time_limit_minutes`** (10–240), optional **`due_date`**, and a list of student user IDs. This is **separate from self-paced labs** on `/challenges` — assignment progress is stored in `challenge_assignment_students`, not `user_progress`.

    **Student workflow:**

    1. Dashboard (`DashboardHomePage`) and `/home` list open assignments via `GET /api/challenge-assignments/my`.
    2. Student opens `/assignment/:assignmentId` (`ChallengeAssignmentPage.tsx`).
    3. `POST /api/challenge-assignments/{id}/start` begins the countdown (`status` → `in_progress`, `started_at` set).
    4. Student submits fix code; `POST /api/challenge-assignments/{id}/submit-fix` runs the same `_verify_fix_improvement` sandbox as self-paced labs.
    5. On timeout or past due date, status becomes **`expired`**; score is **100** if sandbox passes, **0** otherwise.

    **Instructor workflow:** `GET /api/challenge-assignments/instructor` lists assignments with aggregate pass/fail counts; `GET /api/challenge-assignments/{id}/results` (`InstructorAssignmentResultsPage`) shows per-student outcomes; `DELETE /api/challenge-assignments/{id}` soft-deactivates (`is_active=false`).

    ---

    ## 6. Project Scanner

    ### 6.1 Dual-engine static analysis (Semgrep + regex)

    `POST /api/project/scan` invokes **`run_merged_scan`** in `projects.py`, which:

    1. Runs **`run_semgrep_scan`** (`scanner/semgrep_scanner.py`) with security-focused rulesets when the `semgrep` CLI is available in the backend container.
    2. Runs the legacy **regex detector** (`detector.py` + `rules.py`) including CSRF heuristics (POST patterns without CSRF token keywords).
    3. **Merges** findings via `_merge_findings`, deduplicating by file/line/type where possible and tagging each row with `engine: "semgrep"` or legacy source.

    If Semgrep is unavailable, the scan **degrades gracefully** to regex-only; the response includes `scanner_engines.semgrep: false` and optional `semgrep_errors`. The Scanner UI (`Scanner.tsx`) displays a Semgrep badge when the engine contributed findings.

    ### 6.2 Scoring, fixes, and dependencies

    Scoring: High=5, Medium=3, Low=1; thresholds ≤10 Low, ≤20 Medium, else High. `fixer.py` attaches `FIX_RECOMMENDATIONS`. `vuln_summary` JSON includes findings, summary counts, debug, **`semgrep_findings`** count, and `dependency_scan` after a background thread.

    ### 6.3 Git upload and async scan status

    **`POST /api/project/scan-from-git`** clones a repository URL into the uploads area and triggers the same merged scan pipeline. **`GET /api/project/scan-status/{scan_id}`** supports polling for long-running scan jobs.

    ---

    ## 7. Penetration Test Report Generation

    ### 7.1 Student portfolio PDF (`GET /api/report/pdf`)

    Router: `report.py`, prefix `/api/report`. **`GET /api/report/pdf`** builds five sections: cover, executive summary with colored table, vulnerability inventory (flattened findings), remediation evidence from `UserProgress` and `ChallengeState`, learning metrics table. Filename `pentest_report_{safe_email}_{YYYYMMDD}.pdf`. Requires at least one **owned** scan (`ScanHistory` for a `Project` owned by the user) or returns **404**.

    ### 7.2 Project-scoped reports (`projects.py`)

    **`GET /api/project/report`** returns JSON security analysis for a project. **`GET /api/project/report/pdf`** generates a **per-upload** PDF via `scanner/report_generator.py` (distinct from the student portfolio PDF in §7.1). The Scanner UI and dashboards typically emphasize the student pentest export; operators should not confuse the two URLs.

    ---

    ## 8. Quiz System

    ### 8.1 Architecture Overview
    Two systems: `/api/quizzes` bank, **normalized assignment tables**, and instructor workflows; `/api/quiz` dynamic generation from scan context.

    ### 8.2 Static Quiz Bank
    `POST /api/quizzes/take` samples questions by topic/difficulty. `seed_db.py` seeds **200 MCQ questions** across **20 security topics** (10 questions each) plus default admin and instructor accounts.

    ### 8.3 Instructor Management
    `POST /api/quizzes/manage` CRUD; **`POST /api/quizzes/assignments`** creates assignments with normalized rows in `quiz_assignment_students` and `quiz_assignment_questions` (legacy comma-separated `question_ids` / `assigned_student_ids` columns remain on `QuizAssignment` for compatibility). Assignments support **`time_limit_minutes`** and **`due_date`**.

    ### 8.4 Student Quiz Interface
    `StudentQuizPage.tsx` provides:

    - **Practice quiz** — topic/difficulty bank sampling via `POST /api/quizzes/take`.
    - **Instructor assignments** — `GET /api/quizzes/assignments/student`, start via `POST /api/quizzes/assignments/{id}/start`, take via `GET /api/quizzes/assignments/{id}/take`, submit answers/attempt with timer enforcement.
    - **Scan-based quiz** — `POST /api/quiz/generate` from scan findings.
    - **Common mistakes quiz** — `POST /api/quizzes/common-mistakes-quiz` analyzes prior `UserAnswer` wrong rows and generates targeted questions (OpenAI when configured, rule-based fallback otherwise).

    ### 8.5 Dynamic AI Quiz
    `POST /api/quiz/generate` for scan-driven quizzes.

    ### 8.6 Instructor AI Quiz Generator
    `POST /api/quizzes/ai-generate-and-assign` with `AIQuizAssignRequest` fields; preview via `POST /api/quizzes/generate-ai-preview`.

    ### 8.7 Instructor “mistakes quiz” assignment
    Instructors can push a personalized mistakes quiz to a student from the instructor dashboard: **`POST /api/quizzes/assign-mistakes-quiz`** with `student_id` and optional `num_questions`. Creates a `QuizAssignment` linked to AI- or fallback-generated questions tagged with `targets_mistake` on the `questions` table.

    ### 8.8 Capture-the-flag (CTF) competitive mode

    A repository-wide search for dedicated CTF session tables, flag HMAC storage, or `/api/ctf` routes shows **no** such backend implementation. **CTF-style progression** in SCALE is approximated by **lab completion**, **quiz scores**, and **Red vs Blue** (Section 13), not by a separate flag-submission engine. Any external syllabus that refers to “CTF mode” should be mapped to those features unless a future revision adds explicit CTF APIs.

    ---

    ## 9. Learning Progress and Analytics

    Analytics are implemented in `backend/app/security/learning_tracker.py` and exposed primarily via **`GET /api/stats/progress/me`** (`stats.py`). That endpoint returns `build_learning_progress_payload` **plus** `challenge_detail` from `build_challenge_progress_detail`. **`GET /api/instructor/user/{id}/analytics`** returns **only** `build_learning_progress_payload` (same core fields as the student payload, but **without** `challenge_detail` unless the client calls another endpoint).

    ### 9.1 Persisted learning profile (`user_learning_progress`)

    `recalculate_learning_progress` aggregates:

    - **Distinct labs solved:** count of distinct `UserProgress.challenge_id` values, capped at `TOTAL_CHALLENGES` (10).
    - **Quiz accuracy:** from `UserAnswer` rows (`is_correct`).
    - **Failed attempts:** total answers minus correct (quiz-focused).
    - **Average quiz time:** mean of `QuizAttempt.time_seconds` for the user.
    - **Strongest / weakest category:** derived from `compute_skills_scores` (see §9.2).
    - **`level`:** Beginner / Intermediate / Advanced via `_determine_level` (see §9.3).
    - **`streak_days`:** consecutive calendar days with at least one `UserProgress.completed_at` (see §9.4).
    - **`learning_speed`:** \((\text{solved} / \max(\text{avg\_time}, 1)) \times 100\) when solved > 0, else 0.
    - **`retention_score`:** blended metric capped at 100 (accuracy component, streak component capped at 14 days, penalty for failed answers)—see source for exact weights.

    The **`recommendations`** array is produced by `get_learning_recommendations`: e.g. focus on weakest bucket, suggest AI mentor if accuracy < 60%, suggest hints if `failed_attempts` > 10, else a generic “maintain momentum” string.

    ### 9.2 Skill buckets and radar dimensions (`SKILL_BUCKETS`)

    Six named dimensions aggregate **completion of one or more challenge slugs** each:

    | Bucket name | Slugs contributing (all must be considered for 100% in that bucket) |
    |-------------|----------------------------------------------------------------------|
    | SQL Injection | `sql-injection`, `broken-auth` |
    | XSS | `xss` |
    | CSRF | `csrf`, `redirect` |
    | Traversal | `directory-traversal`, `command-injection` |
    | XXE | `xxe` |
    | Storage | `insecure-storage`, `security-misc` |

    Per bucket, the score is \(\lfloor 100 \times (\text{slugs solved in bucket}) / (\text{number of slugs in bucket}) \rfloor\). The API returns **`skills`** (map) and **`skills_radar`** (array of `{subject, value}`) for charting.

    ### 9.3 Defense Level (ranking tier) — backend `level` field

    The dashboard **“Defense Level”** card displays `learning.level` from the API. It is **not** a numeric rank among all users (there is **no** global solo leaderboard). Thresholds in `_determine_level`:

    | Level | Condition |
    |-------|-----------|
    | **Advanced** | `vulnerabilities_solved >= 9` **and** `accuracy >= 80` |
    | **Intermediate** | `vulnerabilities_solved >= 4` **and** `accuracy >= 60` |
    | **Beginner** | Otherwise |

    Here **`vulnerabilities_solved`** is the capped distinct-completion count; **`accuracy`** is quiz accuracy from `UserAnswer`. The UI copy “Keep fixing to rank up” refers to moving between these **three tiers**, not to a class rank.

    ### 9.4 Streak, learning speed, and retention score

    - **Streak:** `UserProgress.completed_at` dates are sorted (most recent first). The algorithm walks the list and increments the streak while dates are **consecutive calendar days** (same-day completions count toward the current day).
    - **Learning speed:** See formula in §9.1; higher when more labs are solved relative to mean quiz duration.
    - **Retention score:** Combines accuracy (60% weight in the blend), streak (scaled to 14 days), and a penalty from failed quiz answers—capped between 0 and 100. Displayed on the dashboard as “Retention score”.

    ### 9.5 Challenge mastery detail (`challenge_detail`)

    `build_challenge_progress_detail` returns **ten rows** (`CHALLENGE_DISPLAY`): each has `slug`, `label`, `category`, `color`, **`completed`** (boolean from `UserProgress`), and **`value`** 0 or 100 for bar width. The student dashboard renders horizontal **Challenge Mastery** bars, category badges, per-row **Reset** (calls `DELETE /api/challenges/progress/{slug}`), and a **by category** summary grid.

    ### 9.6 Dashboard “Current Score” XP (`currentXp`) — client-side only

    `DashboardHomePage.tsx` computes:

    ```text
    currentXp = solvedLabs * 100 + (quizAttempts.length ? avgScorePercent : 0)
    ```

    where **`solvedLabs`** prefers `learning.vulnerabilities_solved` from the API else falls back to a distinct count from `GET /api/challenges/progress`, **`avgScorePercent`** is the mean percentage across all `GET /api/quizzes/attempts` rows, and if there are **no** quiz attempts the second term is **0** (not the average alone). This value is labeled **“XP”** in the UI but is **not persisted** in MySQL and **not** the same as narrative attack-success XP (§5.9) or sandbox `improvement_score`. It is a **single-number gamification summary** for the student.

    ### 9.7 Other dashboard cards (student)

    - **Vulnerabilities:** `solvedLabs / totalLabs` with link to `/challenges`.
    - **Quiz Results:** latest attempt percentage and rolling average / average time from `quizAttempts`.
    - **Overall Progress:** bar uses `progressPercent` from solved labs vs `TOTAL_CHALLENGES`.
    - **Red vs Blue banner:** `GET /api/redblue/my-games` filtered to `status === 'active'` (Section 13).
    - **Challenge assignments:** `GET /api/challenge-assignments/my` lists open timed lab tasks with countdown (Section 5.10).
    - **AI Features Active:** `GET /api/ai/status` when `ai_available` is true.

    ### 9.8 Instructor dashboard metrics (`GET /api/stats/instructor/dashboard`)

    Returns: **`total_students`**, **`quizzes_created`** (assignment count), **`questions_in_bank`**, **`avg_completion_rate`** (sum of per-student solved labs vs `total_students * 10`), **`class_performance`** (per-`SKILL_BUCKETS` average score and count of students at 100% in that bucket), **`total_challenges`** (=10). Used by `InstructorDashboardPage.tsx` for class overview charts.

    ### 9.9 Admin dashboard metrics (`GET /api/stats/admin/dashboard`)

    Returns: **`total_users`**, role distribution, **`fixed_vulns`** = **total row count** in `user_progress` (counts completion events, not unique users), **`challenge_usage`** per lab with **`attempts`** = sum of `ChallengeState.attempt_count` for that slug and **`successes`** = distinct users with `UserProgress` for that slug, plus **`system_status`**. Used by `AdminStatsPage` / `AdminDashboardPage` for aggregate visuals.

    ---

    ## 10. Security Event Logging

    ### 10.1 Event pipeline

    `log_security_event` in `security_logger.py` writes rows to **`security_logs`** with fields including `event_type`, `severity`, `payload`, `endpoint`, `ip_address`, `user_agent`, and **`context_type`** (`real` vs `challenge`). Lab routers pass `context_type="challenge"` for Red vs Blue and challenge traffic so operators can filter pedagogical noise. **`GET /api/security/logs`** (admin) supports pagination and filters; **`GET /api/security/logs/stats`** aggregates counts.

    ### 10.2 Data retention, privacy, and institutional deployment

    **Retention:** The platform implements **no automatic log rotation or TTL**. `security_logs` rows persist until an operator deletes them or drops the database volume. Payload columns may contain **student-supplied attack strings** (SQL fragments, XSS snippets, file paths from scans). Plan storage capacity accordingly.

    **Lab vs production traffic:** Use **`context_type`** and the admin log filters to separate **`challenge`** events (expected lab behavior) from **`real`** platform events (login failures, upload anomalies). This does **not** anonymize student identity — `user_id` is stored when available.

    **Privacy / GDPR (institutional deployment):** If SCALE were used with real students outside a closed lab:

    - **Lawful basis** and **privacy notice** should state that attack payloads and IP addresses are logged for security monitoring.
    - **Data minimization:** Consider truncating or hashing `payload` in production configs; the reference implementation stores full text for instructor review.
    - **Retention policy:** Define a maximum age (e.g. 90 days) and a purge job — **not included** in the reference stack.
    - **Right to erasure:** Admin user deletion (`DELETE /api/auth/admin/users/{id}`) does not automatically cascade-delete `security_logs`; operators must handle erasure requests manually.
    - **Cross-border transfer:** External AI keys (OpenAI, Serper) may send code snippets or queries outside the institution; disable AI features if data residency requires it (Section 16).

    For **graduation / demo** deployments on localhost, these concerns are documented for completeness; a single-course VM with synthetic accounts is typically sufficient.

    ---

    ## 11. Messaging System

    `messages` table; `GET /api/messages/unread-count` polled every 30s when visible in `Sidebar.tsx`.

    ---

    ## 12. AI Services

    `OPENAI_API_KEY` and `SERPER_API_KEY` read in startup and ai modules. `GET /api/ai/status` returns availability. Mentor chat `POST /api/ai/mentor-chat`; scan AI `POST /api/project/scan/ai` returns 503 if neither key configured.

    ---

    ## 13. Red vs Blue Team Mode

    Red vs Blue mode is an **instructor-led competitive layer** on top of the same ten SCALE labs (`LAB_CHALLENGE_SLUGS` in `red_blue.py` maps integers 1–10 to challenge slugs such as `sql-injection`, `xss`, …, `redirect`). It is distinct from the legacy `/api/challenge/*` game router (`game_challenge.py`) but shares the same pedagogical lab assets under `/app/challenges/challenge-{slug}`.

    ### 13.1 Purpose and participants

    **Red team** members log synthetic attacks (payloads and impact text) into `RedTeamAction` rows. **Blue team** members submit Python code fixes against the same lab; fixes are validated with **`_verify_fix_improvement`** (same `improvement_score` and `fixed` semantics as Section 5.2.1). **Instructors or administrators** create games and may end them; **students** (`user`) see only games they belong to via `GET /api/redblue/my-games`.

    ### 13.2 Game lifecycle

    1. **Create:** `POST /api/redblue/game/create` (instructor/admin) validates user IDs, enforces **no overlap** between red and blue rosters, checks `challenge_id ∈ [1,10]`, then **sets any existing active games for that lab to `inactive`**, creates two `Team` rows (`type`=`red`|`blue`), `TeamMember` rows, and a `GameChallenge` with `status=active`, `lab_challenge_id` set, and `started_at` timestamp. A synthetic `project_id` (`redblue-<uuid>`) is stored for correlation with the generic Red/Blue schema (not an uploaded ZIP).
    2. **Play:** While `status == active`, red players call `POST /api/redblue/game/{game_id}/attack`; blue players call `POST /api/redblue/game/{game_id}/fix`. Both endpoints reject participants who are not on the correct team.
    3. **Observe:** `GET /api/redblue/game/{game_id}` returns teams, members, recent actions, fixes, and **computed scores** (see §13.3). `GET /api/redblue/game/{game_id}/attacks?since_id=` returns **new** `RedTeamAction` rows with `id > since_id` in ascending order for **incremental polling**.
    4. **End:** `POST /api/redblue/game/{game_id}/end` (instructor/admin) sets `status` to `completed`. Inactive games are retained for history.
    5. **Instructor overview:** `GET /api/redblue/games` lists all games with scores (instructor/admin).

    ### 13.3 Scoring model

    Red vs Blue uses **turn-based round scoring** for games created via `POST /api/redblue/game/create`. New games set **`current_phase="awaiting_red"`** and initialize **`GameChallenge.red_score`** and **`GameChallenge.blue_score`** to **0**.

    **How points are awarded (current implementation):**

    | Event | Score change | Notes |
    |-------|--------------|-------|
    | Red attack **confirmed** | *(none)* | Sets `current_phase="awaiting_blue"`; logs `RedTeamAction` with `status=confirmed`. |
    | Blue fix **`fixed == true`** | **`blue_score += 1`** | Sandbox unittest pass; round advances. |
    | Blue fix **`fixed == false`** | **`red_score += 1`** | Fix still vulnerable; round advances. |

    After each blue submission, `current_phase` returns to **`awaiting_red`** and **`current_round`** increments. Points are **not** weighted by severity; each round has exactly one winner (+1).

    **Authoritative read path:** `_red_score_query` and `_blue_score_query` in `red_blue.py` return the **stored columns** when `current_phase` is set (all instructor-led games). A **legacy fallback** counts `RedTeamAction` / `BlueTeamFix` rows directly only when `current_phase` is **null** (older rows). There is **no separate reconciliation job** — the columns are updated in the same transaction as fix submission (`db.commit()` after increment), so drift should not occur unless data is edited manually in MySQL.

    **Partial improvement:** A fix with `improvement_score > 0` but `fixed == false` awards the round to **red** (+1 red), not blue.

    ### 13.4 Timing and real-time model

    There is **no WebSocket**. The live game UI (`RedBlueGamePage.tsx`) uses **polling**: `GET .../attacks?since_id=<last>` every few seconds to append new attacks. Fix submission is **request/response**. Clock skew is irrelevant; ordering is by `RedTeamAction.id` / database timestamps. If polling stops (e.g. game ended), the UI should cease requests and show final scores.

    ### 13.5 Student portal

    `GET /api/redblue/my-games` joins `TeamMember` → `GameChallenge` and returns, for each participation, game id, lab title, team side, **computed** red/blue scores, and status. The student dashboard (`DashboardHomePage`) shows an **amber banner** when any returned game has `status === 'active'`, linking to `/redblue/game/:gameId`.

    ### 13.6 Failure and edge cases

    - **Invalid lab id** or unknown user → HTTP 400/404 at creation.
    - **Game not active** → attack/fix return 400.
    - **Wrong team** → 403.
    - **Challenge directory missing** in container → fix path returns 400 (`Cannot resolve challenge directory`).
    - Sandbox **Docker errors** propagate like standard lab fixes (see Section 21).

    ---

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
    | Challenge assignments | `/api/challenge-assignments` | Timed instructor lab fix assignments |
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

    #### POST /api/challenges/mark-attack-complete
    **Auth:** Yes  
    **Query:** `challenge_type` — slug such as `sql-injection`, `xss`, …  
    **Logic:** Calls `mark_challenge_complete` → inserts **`UserProgress`** without sandbox validation; runs `recalculate_learning_progress`. **Does not** prove a secure fix. Used by attack-success UI flows (Section 2.2).

    ---

    #### GET /api/admin/config
    **Auth:** Yes — **any authenticated user** (JWT required); **no admin role check** (intentional lab 6 misconfiguration — Section 5.2.2)  
    **Response:** Pedagogical config JSON (`debug`, sample secrets, filtered env keys). **Not** the same as admin-only `GET /api/admin/overview`.

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
    **Response:** `QuizAssignmentStartResponse` with deadline timestamp when `time_limit_minutes` set.

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

    ## 15. Frontend Pages Reference

    This section documents each `frontend/src/pages/*.tsx` file. Routes match `App.tsx` unless noted. The **ChallengeHintPanel** component (not a page) uses `POST /api/challenge/hint` (game_challenge router) for leveled hints and `POST /api/ai/mentor-chat` for the mentor; this is distinct from `GET /api/challenges/hints` and `POST /api/challenges/hints/use` on the main challenges router.

    ### Page: LandingPage

    **File:** `frontend/src/pages/LandingPage.tsx`  
    **Route:** `/`  
    **Role access:** Public  

    **Purpose:** Check if user is logged in

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: TrailerPage

    **File:** `frontend/src/pages/TrailerPage.tsx`  
    **Route:** `/trailer`  
    **Role access:** Public  

    **Purpose:** Public cinematic promotional trailer for SCALE — GSAP timeline animation, Three.js particle background, MIU and faculty logos (`/trailer-logos/`), feature showcase scenes (scanner, labs, Red vs Blue, mistakes quiz). No backend API calls.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: LoginPage

    **File:** `frontend/src/pages/LoginPage.tsx`  
    **Route:** `/login`  
    **Role access:** Public  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/auth/login | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `C = () => {   const [email, setEmail] = useState('');   const [password, setPassword] = useState('');   const [error,...` |
    | `('');   const [password, setPassword] = useState('');   const [error, setError] = useState('');   const [isPasswordVi...` |
    | `eState('');   const [error, setError] = useState('');   const [isPasswordVisible, setIsPasswordVisible] = useState(fa...` |
    | `asswordVisible, setIsPasswordVisible] = useState(false);   const navigate = useNavigate();    const handleLogin = asy...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RegisterPage

    **File:** `frontend/src/pages/RegisterPage.tsx`  
    **Route:** `/register`  
    **Role access:** Public  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/auth/register | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `C = () => {   const [email, setEmail] = useState('');   const [password, setPassword] = useState('');   const [confir...` |
    | `('');   const [password, setPassword] = useState('');   const [confirmPassword, setConfirmPassword] = useState('');  ...` |
    | `[confirmPassword, setConfirmPassword] = useState('');   const [role, setRole] = useState('user');   const [error, set...` |
    | `useState('');   const [role, setRole] = useState('user');   const [error, setError] = useState('');   const navigate ...` |
    | `te('user');   const [error, setError] = useState('');   const navigate = useNavigate();    const handleSubmit = async...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: DashboardHomePage

    **File:** `frontend/src/pages/DashboardHomePage.tsx`  
    **Route:** `/home`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/report/pdf | From `useEffect` or handler |
    | GET /api/challenges/progress | From `useEffect` or handler |
    | GET /api/quizzes/attempts | From `useEffect` or handler |
    | GET /api/stats/progress/me | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `();   const [userEmail, setUserEmail] = useState('');   const [progressCount, setProgressCount] = useState(0);   cons...` |
    | `nst [progressCount, setProgressCount] = useState(0);   const [quizAttempts, setQuizAttempts] = useState<QuizAttempt[]...` |
    | `const [quizAttempts, setQuizAttempts] = useState<QuizAttempt[]>([]);   const [learning, setLearning] = useState<Learn...` |
    | `([]);   const [learning, setLearning] = useState<LearningProgress | null>(null);   const [challengeDetail, setChallen...` |
    | `[challengeDetail, setChallengeDetail] = useState<ChallengeDetailRow[]>([]);   const [isGeneratingReport, setIsGenerat...` |
    | `eratingReport, setIsGeneratingReport] = useState(false);   const [reportError, setReportError] = useState('');   cons...` |
    | `  const [reportError, setReportError] = useState('');   const [aiFeaturesActive, setAiFeaturesActive] = useState(fals...` |
    | `iFeaturesActive, setAiFeaturesActive] = useState(false);   const [deletingSlug, setDeletingSlug] = useState<string | ...` |
    | `const [deletingSlug, setDeletingSlug] = useState<string | null>(null);   const [deleteFlash, setDeleteFlash] = useSta...` |
    | `  const [deleteFlash, setDeleteFlash] = useState<string | null>(null);   const [activeRbGames, setActiveRbGames] = us...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: ChallengesListPage

    **File:** `frontend/src/pages/ChallengesListPage.tsx`  
    **Route:** `/challenges`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `etingChallenge, setDeletingChallenge] = useState<string | null>(null);   const [deleteSuccess, setDeleteSuccess] = us...` |
    | `nst [deleteSuccess, setDeleteSuccess] = useState<string | null>(null);    useEffect(() => {     const token = session...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: MessagesPage

    **File:** `frontend/src/pages/MessagesPage.tsx`  
    **Route:** `/messages`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/messages/contacts | From `useEffect` or handler |
    | GET /api/messages/with/${contact.id} | From `useEffect` or handler |
    | GET /api/messages/send | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` => {   const [contacts, setContacts] = useState<Contact[]>([]);   const [selectedContact, setSelectedContact] = useS...` |
    | `[selectedContact, setSelectedContact] = useState<Contact | null>(null);   const [messages, setMessages] = useState<Me...` |
    | `ull);   const [messages, setMessages] = useState<Message[]>([]);   const [newMessage, setNewMessage] = useState(''); ...` |
    | `;   const [newMessage, setNewMessage] = useState('');   const [loadingMessages, setLoadingMessages] = useState(false)...` |
    | `[loadingMessages, setLoadingMessages] = useState(false);    const token = sessionStorage.getItem('token');   const cu...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: Scanner

    **File:** `frontend/src/pages/Scanner.tsx`  
    **Route:** `/scanner`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | POST /api/project/upload | From `useEffect` or handler |
    | POST /api/project/scan-from-git | From `useEffect` or handler |
    | POST /api/ai/analyze-code | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `const [selectedFile, setSelectedFile] = useState<File | null>(null);   const [message, setMessage] = useState<string>...` |
    | `(null);   const [message, setMessage] = useState<string>('');   const [projectId, setProjectId] = useState<string>(sc...` |
    | `');   const [projectId, setProjectId] = useState<string>(scanData?.projectId || '');   const [uploading, setUploading...` |
    | `');   const [uploading, setUploading] = useState(false);   const [scanning, setScanning] = useState(false);   const [...` |
    | `lse);   const [scanning, setScanning] = useState(false);   const [scanResults, setScanResults] = useState<any>(scanDa...` |
    | `  const [scanResults, setScanResults] = useState<any>(scanData?.results || null);   const [projectOverview, setProjec...` |
    | `[projectOverview, setProjectOverview] = useState<ProjectOverview | null>(scanData?.overview || null);   const [select...` |
    | `[selectedFinding, setSelectedFinding] = useState<Finding | null>(null);   const [mentorOpen, setMentorOpen] = useStat...` |
    | `;   const [mentorOpen, setMentorOpen] = useState(false);   const [mentorLoading, setMentorLoading] = useState(false);...` |
    | `nst [mentorLoading, setMentorLoading] = useState(false);   const [mentorError, setMentorError] = useState('');   cons...` |
    | `  const [mentorError, setMentorError] = useState('');   const [mentorData, setMentorData] = useState<MentorResponse |...` |
    | `;   const [mentorData, setMentorData] = useState<MentorResponse | null>(null);   const [mentorEditedCode, setMentorEd...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: AttackLab

    **File:** `frontend/src/pages/AttackLab.tsx`  
    **Route:** `/attack-lab`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `| 'Unknown';    const [code, setCode] = useState<string>(state.code || '');   const [payload, setPayload] = useState<...` |
    | `|| '');   const [payload, setPayload] = useState<string>(     state.payload || getDefaultPayload(vulnerabilityType) |...` |
    | `',   );   const [loading, setLoading] = useState(false);   const [error, setError] = useState('');   const [result, s...` |
    | `ate(false);   const [error, setError] = useState('');   const [result, setResult] = useState<AttackSimResponse | null...` |
    | `tate('');   const [result, setResult] = useState<AttackSimResponse | null>(null);   const [visibleStep, setVisibleSte...` |
    | `  const [visibleStep, setVisibleStep] = useState(0);   const [isReplaying, setIsReplaying] = useState(false);    cons...` |
    | `  const [isReplaying, setIsReplaying] = useState(false);    const timelineToShow = useMemo(() => {     if (!result?.t...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SqlInjectionTutorialPage

    **File:** `frontend/src/pages/SqlInjectionTutorialPage.tsx`  
    **Route:** `/challenges/1/tutorial`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SqlInjectionAttackPage

    **File:** `frontend/src/pages/SqlInjectionAttackPage.tsx`  
    **Route:** `/challenges/1/attack`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/vulnerable-login | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` => {   const [username, setUsername] = useState('');   const [password, setPassword] = useState('');   const [error,...` |
    | `('');   const [password, setPassword] = useState('');   const [error, setError] = useState('');   const [isPasswordVi...` |
    | `eState('');   const [error, setError] = useState('');   const [isPasswordVisible, setIsPasswordVisible] = useState(tr...` |
    | `asswordVisible, setIsPasswordVisible] = useState(true);   const navigate = useNavigate();    const handleLogin = asyn...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SqlInjectionFixPage

    **File:** `frontend/src/pages/SqlInjectionFixPage.tsx`  
    **Route:** `/challenges/1/fix`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({     isOpen:...` |
    | `;   const [modalState, setModalState] = useState({     isOpen: false,     isSuccess: false,     logs: '',     verific...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XssTutorialPage

    **File:** `frontend/src/pages/XssTutorialPage.tsx`  
    **Route:** `/challenges/2/tutorial`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XssAttackPage

    **File:** `frontend/src/pages/XssAttackPage.tsx`  
    **Route:** `/challenges/2/attack`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |
    | GET /api/challenges/xss/comments | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` => {   const [comments, setComments] = useState<Comment[]>([]);   const [newComment, setNewComment] = useState(''); ...` |
    | `;   const [newComment, setNewComment] = useState('');   const [author, setAuthor] = useState('Guest');   const [messa...` |
    | `tate('');   const [author, setAuthor] = useState('Guest');   const [message, setMessage] = useState('');   const [isN...` |
    | `uest');   const [message, setMessage] = useState('');   const [isNavigating, setIsNavigating] = useState(false);   co...` |
    | `const [isNavigating, setIsNavigating] = useState(false);   const [attackArmed, setAttackArmed] = useState(false);   /...` |
    | `  const [attackArmed, setAttackArmed] = useState(false);   // Ref keeps the armed flag readable inside the stale useE...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XssFixPage

    **File:** `frontend/src/pages/XssFixPage.tsx`  
    **Route:** `/challenges/2/fix`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({ isOpen: fal...` |
    | `;   const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });    const handleSubmi...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CsrfAttackPage

    **File:** `frontend/src/pages/CsrfAttackPage.tsx`  
    **Route:** `/challenges/3/attack`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/csrf/accounts | From `useEffect` or handler |
    | GET /api/challenges/csrf/reset | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |
    | GET /api/challenges/state/update | From `useEffect` or handler |
    | GET /api/challenges/csrf/transfer | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` => {   const [accounts, setAccounts] = useState<Account[]>([]);   const [payload, setPayload] = useState('');   cons...` |
    | `]>([]);   const [payload, setPayload] = useState('');   const [logs, setLogs] = useState<string[]>([]);   const [mess...` |
    | `useState('');   const [logs, setLogs] = useState<string[]>([]);   const [message, setMessage] = useState('');   const...` |
    | `]>([]);   const [message, setMessage] = useState('');   const [isExecuting, setIsExecuting] = useState(false);   cons...` |
    | `  const [isExecuting, setIsExecuting] = useState(false);   const navigate = useNavigate();    const fetchAccounts = a...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CsrfFixPage

    **File:** `frontend/src/pages/CsrfFixPage.tsx`  
    **Route:** `/challenges/3/fix`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({ isOpen: fal...` |
    | `;   const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });    const handleSubmi...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CsrfTutorialPage

    **File:** `frontend/src/pages/CsrfTutorialPage.tsx`  
    **Route:** `/challenges/3/tutorial`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CommandChallengePage

    **File:** `frontend/src/pages/CommandChallengePage.tsx`  
    **Route:** `/challenges/4/:tab`  
    **Role access:** user, instructor, admin  

    **Purpose:** Single entry for Command Injection challenge (id 4).

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** CommandInjectionAttackPage, CommandInjectionFixPage, CommandInjectionTutorialPage

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: BrokenAuthAttackPage

    **File:** `frontend/src/pages/BrokenAuthAttackPage.tsx`  
    **Route:** `/challenges/5/attack`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/auth/login | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |
    | GET /api/challenges/state/update | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` => {   const [username, setUsername] = useState('admin@scale.edu');   const [password, setPassword] = useState(''); ...` |
    | `du');   const [password, setPassword] = useState('');   const [isSubmitting, setIsSubmitting] = useState(false);   co...` |
    | `const [isSubmitting, setIsSubmitting] = useState(false);   const [showAdmin, setShowAdmin] = useState(false);   const...` |
    | `e);   const [showAdmin, setShowAdmin] = useState(false);   const [lastRequest, setLastRequest] = useState('');   cons...` |
    | `  const [lastRequest, setLastRequest] = useState('');   const [lastExecutedQuery, setLastExecutedQuery] = useState(''...` |
    | `tExecutedQuery, setLastExecutedQuery] = useState('');   const [lastDbResult, setLastDbResult] = useState('');   const...` |
    | `const [lastDbResult, setLastDbResult] = useState('');   const [lastExplanation, setLastExplanation] = useState('');  ...` |
    | `[lastExplanation, setLastExplanation] = useState('');   const [attackStatus, setAttackStatus] = useState<'success' | ...` |
    | `const [attackStatus, setAttackStatus] = useState<'success' | 'failed' | 'idle'>('idle');   const navigate = useNaviga...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: BrokenAuthFixPage

    **File:** `frontend/src/pages/BrokenAuthFixPage.tsx`  
    **Route:** `/challenges/5/fix`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({ isOpen: fal...` |
    | `;   const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });    const handleSubmi...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: BrokenAuthTutorialPage

    **File:** `frontend/src/pages/BrokenAuthTutorialPage.tsx`  
    **Route:** `/challenges/5/tutorial`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SecurityMiscAttackPage

    **File:** `frontend/src/pages/SecurityMiscAttackPage.tsx`  
    **Route:** `/challenges/6/attack`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/calc/interest | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |
    | GET /api/challenges/state/update | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `> {   const [principal, setPrincipal] = useState('5000');   const [rate, setRate] = useState('5');   const [years, se...` |
    | `tate('5000');   const [rate, setRate] = useState('5');   const [years, setYears] = useState('2');   const [calculated...` |
    | `State('5');   const [years, setYears] = useState('2');   const [calculated, setCalculated] = useState<number | null>(...` |
    | `;   const [calculated, setCalculated] = useState<number | null>(null);    const [path, setPath] = useState('/admin/co...` |
    | `null>(null);    const [path, setPath] = useState('/admin/config');   const [responseBody, setResponseBody] = useState...` |
    | `const [responseBody, setResponseBody] = useState<any>(null);   const [responseStatus, setResponseStatus] = useState<n...` |
    | `t [responseStatus, setResponseStatus] = useState<number | null>(null);   const [logs, setLogs] = useState<string[]>([...` |
    | ` null>(null);   const [logs, setLogs] = useState<string[]>([]);   const [isSending, setIsSending] = useState(false); ...` |
    | `]);   const [isSending, setIsSending] = useState(false);    const navigate = useNavigate();    const appendLog = (lin...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SecurityMiscFixPage

    **File:** `frontend/src/pages/SecurityMiscFixPage.tsx`  
    **Route:** `/challenges/6/fix`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({ isOpen: fal...` |
    | `;   const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });    const handleSubmi...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SecurityMiscTutorialPage

    **File:** `frontend/src/pages/SecurityMiscTutorialPage.tsx`  
    **Route:** `/challenges/6/tutorial`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InsecureStorageChallengePage

    **File:** `frontend/src/pages/InsecureStorageChallengePage.tsx`  
    **Route:** `/challenges/7/:tab`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** InsecureStorageAttackPage, InsecureStorageFixPage, InsecureStorageTutorialPage

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: DirectoryTraversalChallengePage

    **File:** `frontend/src/pages/DirectoryTraversalChallengePage.tsx`  
    **Route:** `/challenges/8/:tab`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** DirectoryTraversalAttackPage, DirectoryTraversalFixPage, DirectoryTraversalTutorialPage

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XxeChallengePage

    **File:** `frontend/src/pages/XxeChallengePage.tsx`  
    **Route:** `/challenges/9/:tab`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** XxeAttackPage, XxeFixPage, XxeTutorialPage

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedirectChallengePage

    **File:** `frontend/src/pages/RedirectChallengePage.tsx`  
    **Route:** `/challenges/10/:tab`  
    **Role access:** user, instructor, admin  

    **Purpose:** * Single entry for Unvalidated Redirect challenge (id 10).

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** RedirectAttackPage, RedirectFixPage, RedirectTutorialPage

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: AttackSuccessPage

    **File:** `frontend/src/pages/AttackSuccessPage.tsx`  
    **Route:** `/challenges/attack-success`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/progress | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `    const [showReplay, setShowReplay] = useState(false);   const [replaySample, setReplaySample] = useState(false);  ...` |
    | `const [replaySample, setReplaySample] = useState(false);   const [hasProgress, setHasProgress] = useState(false);   c...` |
    | `  const [hasProgress, setHasProgress] = useState(false);   const [progressLoaded, setProgressLoaded] = useState(false...` |
    | `t [progressLoaded, setProgressLoaded] = useState(false);    useEffect(() => {     let cancelled = false;     const lo...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedBlueGamePage

    **File:** `frontend/src/pages/RedBlueGamePage.tsx`  
    **Route:** `/redblue/game/:gameId`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `Id);    const [gameData, setGameData] = useState<any>(null);   const [attacks, setAttacks] = useState<AttackRow[]>([]...` |
    | `(null);   const [attacks, setAttacks] = useState<AttackRow[]>([]);   const lastSeenRef = useRef(0);   const [pollingA...` |
    | `nst [pollingActive, setPollingActive] = useState(true);   const [fixCode, setFixCode] = useState('');   const [fixSub...` |
    | `(true);   const [fixCode, setFixCode] = useState('');   const [fixSubmitting, setFixSubmitting] = useState(false);   ...` |
    | `nst [fixSubmitting, setFixSubmitting] = useState(false);   const [fixResult, setFixResult] = useState<{ fixed: boolea...` |
    | `e);   const [fixResult, setFixResult] = useState<{ fixed: boolean; message: string } | null>(null);   const [gameLoad...` |
    | `  const [gameLoading, setGameLoading] = useState(true);   const [loadError, setLoadError] = useState<string | null>(n...` |
    | `e);   const [loadError, setLoadError] = useState<string | null>(null);   const [endLoading, setEndLoading] = useState...` |
    | `;   const [endLoading, setEndLoading] = useState(false);   const [deleteLoading, setDeleteLoading] = useState(false);...` |
    | `nst [deleteLoading, setDeleteLoading] = useState(false);   const [endResult, setEndResult] = useState<{ red: number; ...` |
    | `e);   const [endResult, setEndResult] = useState<{ red: number; blue: number } | null>(null);   const [attackPayload,...` |
    | `nst [attackPayload, setAttackPayload] = useState('');   const [attackImpact, setAttackImpact] = useState('');   const...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: StudentQuizPage

    **File:** `frontend/src/pages/StudentQuizPage.tsx`  
    **Route:** `/quiz`  
    **Role access:** user only  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/quizzes/wrong-answer-count | From `useEffect` or handler |
    | GET /api/quizzes/assignments/student | From `useEffect` or handler |
    | GET /api/quizzes/submit-attempt | From `useEffect` or handler |
    | GET /api/quizzes/take | From `useEffect` or handler |
    | GET /api/quiz/generate | From `useEffect` or handler |
    | GET /api/quizzes/common-mistakes-quiz | From `useEffect` or handler |
    | GET /api/quizzes/assignments/${id}/start | From `useEffect` or handler |
    | GET /api/quizzes/assignments/${id}/take | From `useEffect` or handler |
    | GET /api/quizzes/submit-answer | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `canContext();   const [step, setStep] = useState<'setup' | 'quiz' | 'result'>('setup');   const [loading, setLoading]...` |
    | `etup');   const [loading, setLoading] = useState(false);    const [topicFilter, setTopicFilter] = useState('All topic...` |
    | `  const [topicFilter, setTopicFilter] = useState('All topics');   const [standardCount, setStandardCount] = useState(...` |
    | `nst [standardCount, setStandardCount] = useState(10);   const [standardDifficulty, setStandardDifficulty] = useState<...` |
    | `ardDifficulty, setStandardDifficulty] = useState<'Any' | 'Easy' | 'Medium' | 'Hard'>('Any');    const [scanQuizCount,...` |
    | `nst [scanQuizCount, setScanQuizCount] = useState(8);   const [scanFocus, setScanFocus] = useState<'all' | 'highest'>(...` |
    | `8);   const [scanFocus, setScanFocus] = useState<'all' | 'highest'>('all');   const [assignments, setAssignments] = u...` |
    | `  const [assignments, setAssignments] = useState<any[]>([]);   const [quizTitle, setQuizTitle] = useState('');   cons...` |
    | `]);   const [quizTitle, setQuizTitle] = useState('');   const [assignmentId, setAssignmentId] = useState<number | nul...` |
    | `const [assignmentId, setAssignmentId] = useState<number | null>(null);   const [generatedFromScan, setGeneratedFromSc...` |
    | `eratedFromScan, setGeneratedFromScan] = useState(false);    const [questions, setQuestions] = useState<any[]>([]);   ...` |
    | `);    const [questions, setQuestions] = useState<any[]>([]);   const [currentIndex, setCurrentIndex] = useState(0);  ...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedBlueMyGamesPage

    **File:** `frontend/src/pages/RedBlueMyGamesPage.tsx`  
    **Route:** `/redblue/my-games`  
    **Role access:** user only  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `gate();   const [loading, setLoading] = useState(true);   const [error, setError] = useState(false);   const [games, ...` |
    | `tate(true);   const [error, setError] = useState(false);   const [games, setGames] = useState<GameRow[]>([]);    useE...` |
    | `ate(false);   const [games, setGames] = useState<GameRow[]>([]);    useEffect(() => {     let cancelled = false;     ...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: ChallengeAssignmentPage

    **File:** `frontend/src/pages/ChallengeAssignmentPage.tsx`  
    **Route:** `/assignment/:assignmentId`  
    **Role access:** user only  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `igate();    const [status, setStatus] = useState<StatusPayload | null>(null);   const [loadError, setLoadError] = use...` |
    | `l);   const [loadError, setLoadError] = useState<string | null>(null);   const [code, setCode] = useState('');   cons...` |
    | ` null>(null);   const [code, setCode] = useState('');   const [lineCount, setLineCount] = useState(0);   const [submi...` |
    | `');   const [lineCount, setLineCount] = useState(0);   const [submitting, setSubmitting] = useState(false);   const [...` |
    | `;   const [submitting, setSubmitting] = useState(false);   const [submitBanner, setSubmitBanner] = useState<{ ok: boo...` |
    | `const [submitBanner, setSubmitBanner] = useState<{ ok: boolean; msg: string } | null>(null);   const [timesUp, setTim...` |
    | `(null);   const [timesUp, setTimesUp] = useState(false);   const [starting, setStarting] = useState(false);   const [...` |
    | `lse);   const [starting, setStarting] = useState(false);   const [remainingSec, setRemainingSec] = useState<number | ...` |
    | `const [remainingSec, setRemainingSec] = useState<number | null>(null);    const codeRef = useRef(code);   const autoS...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: UnderConstructionPage

    **File:** `frontend/src/pages/UnderConstructionPage.tsx`  
    **Route:** `/under-construction`  
    **Role access:** user, instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InstructorDashboardPage

    **File:** `frontend/src/pages/InstructorDashboardPage.tsx`  
    **Route:** `/instructor/dashboard`  
    **Role access:** instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/redblue/games | From `useEffect` or handler |
    | GET /api/challenge-assignments/instructor | From `useEffect` or handler |
    | POST /api/quizzes/assign-mistakes-quiz | From `useEffect` or handler |
    | POST /api/challenge-assignments/create | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `Navigate();   const [users, setUsers] = useState<any[]>([]);   const [searchTerm, setSearchTerm] = useState('');   co...` |
    | `;   const [searchTerm, setSearchTerm] = useState('');   const [stats, setStats] = useState<any>(null); // State for R...` |
    | `eState('');   const [stats, setStats] = useState<any>(null); // State for Real Stats    const [selectedStudent, setSe...` |
    | `[selectedStudent, setSelectedStudent] = useState<any | null>(null);   const [studentAnalytics, setStudentAnalytics] =...` |
    | `tudentAnalytics, setStudentAnalytics] = useState<any | null>(null);   const [analyticsLoading, setAnalyticsLoading] =...` |
    | `nalyticsLoading, setAnalyticsLoading] = useState(false);   const [resetting, setResetting] = useState(false);   const...` |
    | `e);   const [resetting, setResetting] = useState(false);   const [showResetConfirm, setShowResetConfirm] = useState(f...` |
    | `howResetConfirm, setShowResetConfirm] = useState(false);   const [redBlueGames, setRedBlueGames] = useState<any[]>([]...` |
    | `const [redBlueGames, setRedBlueGames] = useState<any[]>([]);   const [rbLoading, setRbLoading] = useState(true);   co...` |
    | `]);   const [rbLoading, setRbLoading] = useState(true);   const [rbError, setRbError] = useState<string | null>(null)...` |
    | `(true);   const [rbError, setRbError] = useState<string | null>(null);   const [rbDeletingId, setRbDeletingId] = useS...` |
    | `const [rbDeletingId, setRbDeletingId] = useState<number | null>(null);    const [chAssignments, setChAssignments] = u...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InstructorQuizPage

    **File:** `frontend/src/pages/InstructorQuizPage.tsx`  
    **Route:** `/instructor/quiz`  
    **Role access:** instructor, admin  

    **Purpose:** Selection State for Assign

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `ct.FC = () => {   const [tab, setTab] = useState('bank'); // bank, create, ai, assign, assign_list   const [questions...` |
    | `ist   const [questions, setQuestions] = useState<any[]>([]);   const [users, setUsers] = useState<any[]>([]);   const...` |
    | `any[]>([]);   const [users, setUsers] = useState<any[]>([]);   const [assignments, setAssignments] = useState<any[]>(...` |
    | `  const [assignments, setAssignments] = useState<any[]>([]);   const [editingId, setEditingId] = useState<number | nu...` |
    | `]);   const [editingId, setEditingId] = useState<number | null>(null);   const [editDraft, setEditDraft] = useState({...` |
    | `l);   const [editDraft, setEditDraft] = useState({     question: '',     category: 'SQL Injection',     difficulty: '...` |
    | `ent   const [selectedQ, setSelectedQ] = useState<number[]>([]);   const [selectedUsers, setSelectedUsers] = useState<...` |
    | `nst [selectedUsers, setSelectedUsers] = useState<number[]>([]);   const [assignTitle, setAssignTitle] = useState('');...` |
    | `  const [assignTitle, setAssignTitle] = useState('');    // AI State   const [aiParams, setAiParams] = useState({ top...` |
    | `State   const [aiParams, setAiParams] = useState({ topic: 'SQL Injection', count: 3, difficulty: 'Medium', skill_focu...` |
    | `});   const [aiPreview, setAiPreview] = useState<any[]>([]);   const [loadingAI, setLoadingAI] = useState(false);    ...` |
    | `]);   const [loadingAI, setLoadingAI] = useState(false);    // Manual Question State   const [newQ, setNewQ] = useSta...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InstructorAssignmentResultsPage

    **File:** `frontend/src/pages/InstructorAssignmentResultsPage.tsx`  
    **Route:** `/instructor/assignment/:assignmentId/results`  
    **Role access:** instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `seNavigate();   const [data, setData] = useState<ResultsResponse | null>(null);   const [error, setError] = useState<...` |
    | `ull>(null);   const [error, setError] = useState<string | null>(null);    useEffect(() => {     if (!assignmentId || ...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedBlueCreatePage

    **File:** `frontend/src/pages/RedBlueCreatePage.tsx`  
    **Route:** `/redblue/create`  
    **Role access:** instructor, admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/redblue/games | From `useEffect` or handler |
    | GET /api/auth/users | From `useEffect` or handler |
    | POST /api/redblue/game/create | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `  const [challengeId, setChallengeId] = useState(1);   const [redName, setRedName] = useState('');   const [blueName,...` |
    | `ate(1);   const [redName, setRedName] = useState('');   const [blueName, setBlueName] = useState('');   const [users,...` |
    | `('');   const [blueName, setBlueName] = useState('');   const [users, setUsers] = useState<{ id: number; email: strin...` |
    | `eState('');   const [users, setUsers] = useState<{ id: number; email: string }[]>([]);   const [redIds, setRedIds] = ...` |
    | `new Set());   const [error, setError] = useState<string | null>(null);   const [submitting, setSubmitting] = useState...` |
    | `;   const [submitting, setSubmitting] = useState(false);    useEffect(() => {     const load = async () => {       tr...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: AdminStatsPage

    **File:** `frontend/src/pages/AdminStatsPage.tsx`  
    **Route:** `/admin/stats`  
    **Role access:** admin  

    **Purpose:** --- FIX: USE SESSION STORAGE ---

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `C = () => {   const [stats, setStats] = useState<any>(null);   const [loading, setLoading] = useState(true);    const...` |
    | `(null);   const [loading, setLoading] = useState(true);    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: AdminDashboardPage

    **File:** `frontend/src/pages/AdminDashboardPage.tsx`  
    **Route:** `/admin/dashboard`  
    **Role access:** admin  

    **Purpose:** Data State

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` Data State   const [users, setUsers] = useState<any[]>([]);   const [pendingUsers, setPendingUsers] = useState<any[]...` |
    | `const [pendingUsers, setPendingUsers] = useState<any[]>([]);   const [platformStats, setPlatformStats] = useState<{ a...` |
    | `nst [platformStats, setPlatformStats] = useState<{ active_exploits: number; fixed_vulns: number; system_status: strin...` |
    | `const [showRequests, setShowRequests] = useState(false);   const [showAddAdmin, setShowAddAdmin] = useState(false);  ...` |
    | `const [showAddAdmin, setShowAddAdmin] = useState(false);   const [editingUser, setEditingUser] = useState<any | null>...` |
    | `  const [editingUser, setEditingUser] = useState<any | null>(null);    // Form State   const [newAdminEmail, setNewAd...` |
    | `nst [newAdminEmail, setNewAdminEmail] = useState('');   const [newAdminPass, setNewAdminPass] = useState('');   const...` |
    | `const [newAdminPass, setNewAdminPass] = useState('');   const [editRole, setEditRole] = useState('user');    const to...` |
    | `('');   const [editRole, setEditRole] = useState('user');    const token = sessionStorage.getItem('token');   const h...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: SecurityLogsPage

    **File:** `frontend/src/pages/SecurityLogsPage.tsx`  
    **Route:** `/admin/logs`  
    **Role access:** admin  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `en');   const [severity, setSeverity] = useState('');   const [eventType, setEventType] = useState('');   const [cont...` |
    | `');   const [eventType, setEventType] = useState('');   const [contextType, setContextType] = useState('');   const [...` |
    | `  const [contextType, setContextType] = useState('');   const [page, setPage] = useState(1);   const [rows, setRows] ...` |
    | `useState('');   const [page, setPage] = useState(1);   const [rows, setRows] = useState<SecurityLog[]>([]);   const [...` |
    | ` useState(1);   const [rows, setRows] = useState<SecurityLog[]>([]);   const [total, setTotal] = useState(0);   const...` |
    | `Log[]>([]);   const [total, setTotal] = useState(0);   const [expanded, setExpanded] = useState<number | null>(null);...` |
    | `e(0);   const [expanded, setExpanded] = useState<number | null>(null);   const [stats, setStats] = useState<any>(null...` |
    | `ull>(null);   const [stats, setStats] = useState<any>(null);    const pageSize = 20;   const totalPages = useMemo(() ...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: HomePage

    **File:** `frontend/src/pages/HomePage.tsx`  
    **Route:** `(not in App.tsx)`  
    **Role access:** unreachable  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: ScenarioPage

    **File:** `frontend/src/pages/ScenarioPage.tsx`  
    **Route:** `(not in App.tsx)`  
    **Role access:** unreachable  

    **Purpose:** This hook gets the 'id' from the URL (e.g., /challenges/5)

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CommandInjectionAttackPage

    **File:** `frontend/src/pages/CommandInjectionAttackPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [host, setHost] = useState('');   const [output, setOutput] = useState('');   const [error, set...` |
    | `tate('');   const [output, setOutput] = useState('');   const [error, setError] = useState('');   const [verified, se...` |
    | `eState('');   const [error, setError] = useState('');   const [verified, setVerified] = useState<'pending' | 'success...` |
    | `('');   const [verified, setVerified] = useState<'pending' | 'success' | 'failed'>('pending');   const navigate = use...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CommandInjectionFixPage

    **File:** `frontend/src/pages/CommandInjectionFixPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({ isOpen: fal...` |
    | `;   const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });    const handleSubmi...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: CommandInjectionTutorialPage

    **File:** `frontend/src/pages/CommandInjectionTutorialPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: DirectoryTraversalAttackPage

    **File:** `frontend/src/pages/DirectoryTraversalAttackPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** If user pasted full request line: GET /...?... HTTP/1.1

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/traversal/read | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `() => {   const [payload, setPayload] = useState('');   const [result, setResult] = useState<any>(null);   const [err...` |
    | `tate('');   const [result, setResult] = useState<any>(null);   const [error, setError] = useState('');   const naviga...` |
    | `any>(null);   const [error, setError] = useState('');   const navigate = useNavigate();    const runAttack = async ()...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: DirectoryTraversalFixPage

    **File:** `frontend/src/pages/DirectoryTraversalFixPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({     isOpen:...` |
    | `;   const [modalState, setModalState] = useState({     isOpen: false,     isSuccess: false,     logs: '',     verific...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: DirectoryTraversalTutorialPage

    **File:** `frontend/src/pages/DirectoryTraversalTutorialPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InsecureStorageAttackPage

    **File:** `frontend/src/pages/InsecureStorageAttackPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Track that the learner has registered at least one account this session.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/storage/register | From `useEffect` or handler |
    | GET /api/challenges/storage/dump | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | ` => {   const [username, setUsername] = useState('');   const [password, setPassword] = useState('');   const [regist...` |
    | `('');   const [password, setPassword] = useState('');   const [registerResult, setRegisterResult] = useState<any>(nul...` |
    | `t [registerResult, setRegisterResult] = useState<any>(null);   const [dumpResult, setDumpResult] = useState<any>(null...` |
    | `;   const [dumpResult, setDumpResult] = useState<any>(null);   const [error, setError] = useState('');   // Track tha...` |
    | `any>(null);   const [error, setError] = useState('');   // Track that the learner has registered at least one account...` |
    | `nst [hasRegistered, setHasRegistered] = useState(false);   const navigate = useNavigate();    const register = async ...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InsecureStorageFixPage

    **File:** `frontend/src/pages/InsecureStorageFixPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({     isOpen:...` |
    | `;   const [modalState, setModalState] = useState({     isOpen: false,     isSuccess: false,     logs: '',     verific...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: InsecureStorageTutorialPage

    **File:** `frontend/src/pages/InsecureStorageTutorialPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedirectAttackPage

    **File:** `frontend/src/pages/RedirectAttackPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** These start empty so the lab does not reveal a ready-made payload.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `const [targetDomain, setTargetDomain] = useState('');   const [targetPath, setTargetPath] = useState('');   const [qu...` |
    | `;   const [targetPath, setTargetPath] = useState('');   const [queryString, setQueryString] = useState('');   const [...` |
    | `  const [queryString, setQueryString] = useState('');   const [logs, setLogs] = useState<string[]>([]);   const [veri...` |
    | `useState('');   const [logs, setLogs] = useState<string[]>([]);   const [verified, setVerified] = useState<'pending' ...` |
    | `([]);   const [verified, setVerified] = useState<'pending' | 'success' | 'failed'>('pending');   const [error, setErr...` |
    | `'pending');   const [error, setError] = useState('');   const iframeRef = useRef<HTMLIFrameElement | null>(null);   c...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedirectFixPage

    **File:** `frontend/src/pages/RedirectFixPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({ isOpen: fal...` |
    | `;   const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });    const handleSubmi...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: RedirectTutorialPage

    **File:** `frontend/src/pages/RedirectTutorialPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XxeAttackPage

    **File:** `frontend/src/pages/XxeAttackPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | GET /api/challenges/xxe/parse | From `useEffect` or handler |
    | GET /api/challenges/mark-attack-complete | From `useEffect` or handler |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `ct.FC = () => {   const [xml, setXml] = useState('<root></root>');   const [result, setResult] = useState<any>(null);...` |
    | `/root>');   const [result, setResult] = useState<any>(null);   const [error, setError] = useState('');   const naviga...` |
    | `any>(null);   const [error, setError] = useState('');   const navigate = useNavigate();    const execute = async () =...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XxeFixPage

    **File:** `frontend/src/pages/XxeFixPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | `.FC = () => {   const [code, setCode] = useState(VULNERABLE_CODE);   const [isLoading, setIsLoading] = useState(false...` |
    | `E);   const [isLoading, setIsLoading] = useState(false);   const [modalState, setModalState] = useState({     isOpen:...` |
    | `;   const [modalState, setModalState] = useState({     isOpen: false,     isSuccess: false,     logs: '',     verific...` |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ### Page: XxeTutorialPage

    **File:** `frontend/src/pages/XxeTutorialPage.tsx`  
    **Route:** `(compose-only: imported by wrapper, not App.tsx)`  
    **Role access:** see parent route  

    **Purpose:** Student or staff UI for the SCALE web application.

    **API calls (extracted):**

    | Endpoint (method + path) | Notes |
    |----------|------|
    | — | No `/api` calls detected in file (static or child-only) |


    **State hooks (sample):**

    | Hook / state (excerpt) |
    |---|
    | *(see file for local state)* |


    **Child / local imports:** —

    **Navigation:** Uses `react-router-dom` `Link` / `useNavigate` where present; see file for targets.

    ---


    ## 16. Environment and Configuration

    ### 16.1 Environment Variables
    See `.env.example` in repository root for `OPENAI_API_KEY`, `SERPER_API_KEY`, `DATABASE_URL`, `SQLI_DATABASE_URL`, `CSRF_DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ENABLE_BROKEN_AUTH_CHALLENGE`, `SANDBOX_MAX_CODE_CHARS`, `SANDBOX_RUN_TIMEOUT`, `VITE_API_URL`, `AI_SERVICE_URL`.

    ### 16.2 Docker Volumes
    `scale_db_data` persists MySQL data for `main_db`. Bind mounts mount backend code and challenge directories.

    ### 16.3 Port Reference
    See Section 3.2.

    ### 16.4 `.env.example`
    Reproduced in repository; copy to `.env` beside `docker-compose.yml`.

    ---

    ## 17. Setup and Deployment

    ### 17.1 Prerequisites
    Docker Desktop, 4 GB RAM recommended for Docker-in-Docker workloads.

    ### 17.2 First-Time Setup

    Clone repository, copy `.env.example` to `.env`, run `docker compose up --build`, open `http://localhost:5173`. Optional public demo: **`http://localhost:5173/trailer`**. Voiced lab tutorials require the `Web-Videos/` folder (mounted read-only into the frontend container as `/app/web-videos`).

    > **⚠ DEFAULT CREDENTIALS — DEVELOPMENT ONLY**  
    > `seed_db.py` creates **`admin@scale.edu` / `AdminPass123!`** and **`instructor@scale.edu` / `TeachPass123!`**. These are **intentional for local demo and examination** but **must be changed or disabled before any network-exposed deployment**. Also rotate **`SECRET_KEY`**, MySQL passwords in `.env`, and delete or re-seed accounts if the stack was ever reachable from the internet.

    ### 17.3 Enabling AI Features
    Set `OPENAI_API_KEY` or `SERPER_API_KEY` in `.env` or `backend/.env`.

    ### 17.4 Development Workflow
    Backend `--reload`, Vite HMR. Logs via `docker logs scale_application-backend-1`.

    ### 17.5 Common Issues
    DB retry loop, Docker socket alignment, CORS origin list, `PROJECT_STORAGE_ROOT`, sandbox `run_tests.sh` line endings.

    ### 17.6 Production Considerations
    Rotate secrets, HTTPS, rate limits, restrict Docker socket, harden DB credentials. **Never** deploy with default seeded passwords (Section 17.2).

    ### 17.7 Dependency pinning and reproducible builds

    > **⚠ UNPINNED DEPENDENCIES**  
    > `backend/requirements.txt` pins only **`bcrypt==4.0.1`**; FastAPI, SQLAlchemy, Semgrep, and most other Python packages are **unpinned**. `frontend/package.json` uses semver ranges. Running `docker compose up --build` **six months later** may pull newer package versions and **break silently** (API deprecations, Semgrep CLI changes, React type errors).

    **Before any production or long-term demo:**

    1. Capture **`pip freeze > backend/requirements.lock.txt`** from a known-good container.
    2. Commit **`frontend/package-lock.json`** and use **`npm ci`** in the frontend Dockerfile for immutable Node installs.
    3. Tag the Docker images with the lockfile snapshot date in your deployment notes.

    See also Section 2.4 (tech stack reproducibility note).

    ---

    ## 18. Known Limitations and Technical Debt

    Each item states **impact**, **mitigation or workaround**, and where applicable **future engineering direction**.

    | # | Limitation | Impact | Mitigation / workaround | Future fix |
    |---|------------|--------|-------------------------|------------|
    | 1 | Two parallel quiz systems (`/api/quizzes` vs `/api/quiz`) | Operators must learn two URL namespaces; duplicated concepts (take vs generate). | Document which UI uses which (Student quiz: both cards; instructor: bank + AI assign). | **Unify** into one router with `/quizzes` resource model or deprecate `/api/quiz` behind a facade. |
    | 2 | Legacy `quiz_assignments.question_ids` comma-separated text alongside normalized tables | Dual storage paths during migration. | New assignments use `quiz_assignment_questions`; legacy column retained for compatibility. | Remove legacy text columns once all readers use normalized tables. |
    | 3 | Dashboard “XP” / `currentXp` computed client-side (`DashboardHomePage.tsx`; Section 9.6) | Not auditable for grading; refresh can desync. | Treat as **informal** only; use `QuizAttempt` and `UserProgress` for official metrics. | Persist aggregate XP server-side if needed. |
    | 4 | Defense Level label must reflect backend `level` (`user_learning_progress`) | Confusing if stale or derived twice. | **Trust** `GET /api/stats/progress/me`; the card reads `learning.level` directly. | Remove duplicate client “level” logic if introduced later; thresholds are fixed in Section 9.3. |
    | 5 | `MainLayout` polls `/api/messages/unread-count` on an interval; no WebSocket | Extra HTTP traffic; not real-time. | Acceptable for small cohorts; increase interval if needed. | **WebSocket** or SSE for unread counts. |
    | 6 | Command injection lab executes shell-related behavior on backend host path | **Pedagogical risk**: real command execution on host if misconfigured. | Deploy only in isolated VMs; restrict who can reach `/api/challenges/ping`. | Run ping lab in **dedicated** sandbox with no host network; or pure simulation. |
    | 7 | JWT stored in **`sessionStorage`** and mirrored in **`Authorization: Bearer`** (`LoginPage.tsx`, `api.ts` interceptor) | **Same-origin XSS** in the SPA exfiltrates the token **immediately** on execution. Short TTL (`ACCESS_TOKEN_EXPIRE_MINUTES`) only limits **replay window**, not theft. Login also sets an **HttpOnly** `access_token` cookie, but the SPA **still prefers Bearer from storage**, so cookie-only auth is **not** in effect. | **Not implemented in code:** stop writing JWT to `sessionStorage`; rely on HttpOnly cookie + CSRF on mutating routes (Section 19.5). Interim: strict CSP, no `dangerouslySetInnerHTML` in SCALE UI, treat any SPA XSS as full account compromise. | Implement cookie-only session; remove Bearer-from-storage path. |
    | 8 | Uploading the SCALE repository as a ZIP scans **first-party** code | False positives and noise. | **Exclude** `uploads/` or use `.scaleignore` (future); instruct students to upload only their app. | Add ignore patterns to scanner entrypoint. |
    | 9 | Dependency scanner caps at **50** packages (`MAX_DEPS_TO_QUERY`) | Large monorepos may miss advisories beyond the cap. | Run focused scans on service subfolders; split uploads. | Raise cap with pagination or batch OSV. |
    | 10 | Red vs Blue fix resolution depends on **`/app/challenges/challenge-{slug}`** mounts | Wrong compose layout → 400 on fix. | Verify bind mounts in `docker-compose.yml` match `challenge-*` directory names. | Health-check endpoint that lists resolvable challenge dirs. |
    | 11 | Dual APIs `/api/redblue` and `/api/challenge` | Two mental models for “game” features. | Prefer **documented** `/api/redblue` for instructor games; use `/api/challenge` only for hint/legacy flows. | Deprecate or merge routers. |
    | 12 | Tutorial videos require `Web-Videos/` mount in dev Docker | Missing folder → empty tutorial player. | Ensure `Web-Videos/*.mp4` exist and compose mounts `./Web-Videos:/app/web-videos:ro`. | CDN or static asset pipeline for production builds. |
    | 13 | AI features require **external** API keys | No AI without key. | Rely on Serper-only or standard scan; `GET /api/ai/status` surfaces availability. | Self-hosted models. |
    | 14 | Semgrep CLI optional in backend image | Scan falls back to regex-only if `semgrep` binary missing. | Install via `requirements.txt`; check `scanner_engines.semgrep` in scan response. | Bake Semgrep into backend Dockerfile explicitly and verify in CI. |

    ---

    ## 19. Security Analysis

    This section addresses **both** the intentionally vulnerable teaching surfaces and the **security posture of the platform** that hosts them. SCALE is a **high-trust** operator environment: the backend holds the Docker socket, database credentials, and JWT signing keys.

    ### 19.1 Intentional vulnerabilities (pedagogical)

    | Component | Intended weakness | Bounded how | Learning objective |
    |-----------|-------------------|-------------|-------------------|
    | `auth.py` broken-auth branch | SQLite in-memory string interpolation | `ENABLE_BROKEN_AUTH_CHALLENGE`; separate from production users | SQL injection in authentication |
    | Challenge `challenge-*/app.py` | Per-lab OWASP flaws | **Only** mounted paths; not exposed as generic RCE on host | Category-specific exploitation |
    | `misconfig.py` | Missing **authorization** on `/api/admin/config` | Any **authenticated** user (JWT required); no admin role check — see §5.2.2 | Misconfiguration discovery |
    | Insecure storage lab | Plaintext in-memory dict | Process-local; resets on restart | Storage anti-patterns |
    | CSRF / SQLi challenge DBs | Intentionally weak queries | Isolated MySQL instances on 3307/3308 | DB-layer effects |

    ### 19.2 Platform security posture (controls in place)

    - **Passwords:** bcrypt via passlib; no plaintext storage for production users.
    - **Authentication:** JWT (HS256) with `SECRET_KEY`; `get_current_user` validates Bearer and cookie.
    - **Authorization:** `require_role` on sensitive routers; admin-only user management.
    - **Transport:** Development assumes HTTPS termination in front of Compose in production (not enforced by Compose itself).
    - **CORS:** Explicit origin allowlist with credentials (Section 3.4).
    - **Input validation:** Upload size, extension allowlists, path traversal checks on extraction (`projects.py`).
    - **Audit:** `security_logs` with `context_type` for lab vs real traffic.

    ### 19.3 Threat model (STRIDE on primary surfaces)

    STRIDE is applied to **the platform**, not to the fake bank apps inside labs.

    | Attack surface | S | T | R | I | D | E | Notes |
    |----------------|---|---|---|---|---|---|-------|
    | **JWT in sessionStorage** | ✓ | — | — | ✓ | — | — | Stolen token → session replay until expiry. **Gap:** HttpOnly cookie exists but SPA sends Bearer from `sessionStorage` — cookie-only mitigation **not implemented** (§18 item 7). |
    | **Docker socket on backend** | — | ✓ | ✓ | ✓ | ✓ | ✓ | **Critical**: container escape or malicious Dockerfile could affect host; mount is required for sandbox builds. |
    | **Sandbox escape / malicious student code** | — | ✓ | ✓ | ✓ | ✓ | ✓ | Mitigated by **disposable** containers, `scale_net` isolation, CPU/mem/pid limits; **not** a full hypervisor boundary. |
    | **Same-origin XSS in SPA** | ✓ | — | — | ✓ | — | — | If XSS existed in SCALE UI, token theft (item 7). |
    | **OSV.dev / dependency** | — | — | ✓ | — | ✓ | — | Supply-chain integrity of OSV responses; TLS + optional signature verification not implemented. |
    | **MySQL** | — | ✓ | ✓ | ✓ | ✓ | — | Network exposure via published ports; default passwords in compose are **development only**. |
    | **Admin / instructor actions** | ✓ | — | ✓ | — | — | — | Role misuse; relies on correct JWT claims. |

    ### 19.4 Residual risks (operational)

    1. **Docker socket** (`/var/run/docker.sock`): grants equivalent capability to root on the host; **must not** be exposed in untrusted multi-tenant production without strong isolation (e.g. separate host, rootless Docker, or remote builder API with policy).
    2. **No global rate limiting** on API endpoints: brute-force login and DoS are possible; **mitigate** with reverse-proxy limits (nginx, Traefik, Cloudflare).
    3. **Sandbox and host shared kernel**: student code runs in containers; **escape** vulnerabilities in runc/kernel would affect the host—**mitigate** with kernel updates and minimal images.
    4. **Command injection lab** (`/api/challenges/ping`) runs on the **backend host** path in the reference implementation; **mitigate** by isolating that route to a dedicated worker (Section 18).
    5. **JWT in `sessionStorage`:** same-origin script can exfiltrate **immediately**; short TTL is insufficient. **Documented mitigation (HttpOnly-only, no Bearer from storage) is not implemented** — see §18 item 7 and §19.5. Interim: CSP and XSS hardening only.

    ### 19.5 Recommendations for production deployment

    | Risk | Mitigation |
    |------|------------|
    | Docker socket | Dedicated builder host; no student-facing shell; audit `docker` API usage. |
    | JWT | **Required fix:** HttpOnly session cookie only; **remove** JWT from `sessionStorage` and stop setting `Authorization` from client storage; add CSRF on POST/PUT/DELETE. **Current code does not do this** — treat as open finding for production. Rotate `SECRET_KEY`. |
    | TLS | Terminate TLS at reverse proxy; HSTS. |
    | Database | Non-default credentials; bind MySQL to internal network only. |
    | Rate limiting | Per-IP limits on `/api/auth/login` and expensive endpoints (`/api/project/scan`). |
    | Observability | Ship `security_logs` to SIEM; alert on repeated 401/403. |

    ---

    ## 20. Testing and Verification Strategy

    ### 20.1 What is tested automatically today

    **Lab (challenge) correctness:** Each `challenge-*` directory includes **`run_tests.sh`** and Python **unittest** modules that the sandbox executes after every fix submission. These tests are the **authoritative** signal for `fixed` and for `improvement_score` (Section 5.2.1). They are **not** the same as platform integration tests.

    **Platform codebase:** The repository does **not** ship a dedicated **pytest** suite for FastAPI route handlers, React components, or end-to-end browser flows. Verification of the **host application** relies on **documented manual exercise** below plus developer smoke tests during feature work.

    ### 20.2 Manual verification performed (development / release candidate)

    The following paths were exercised manually during recent development (May 2026). They are **not** automated regression tests but answer “how do we know it works?” for examination:

    | Area | Scenario verified | Expected outcome |
    |------|-------------------|------------------|
    | **Auth & RBAC** | Student login; instructor pending approval; admin role change; `ProtectedRoute` 403 for wrong role | JWT issued; dashboards route by role; forbidden routes blocked |
    | **Scanner — happy path** | Upload ZIP → `POST /api/project/scan` | Merged Semgrep + regex findings; `scanner_engines.semgrep` flag present; `ScanHistory` row written |
    | **Scanner — OSV degradation** | Scan with OSV unreachable or slow (simulated timeout) | Static findings still returned; dependency section partial or empty (Section 21) |
    | **Scanner — Git** | `POST /api/project/scan-from-git` with public repo URL | Clone + scan completes or returns structured error for bad URL |
    | **Sandbox — pass** | Submit corrected `app.py` for SQLi lab | `fixed: true`, `improvement_score: 100`, unittest logs show `OK` |
    | **Sandbox — fail** | Submit still-vulnerable code | `fixed: false`, `improvement_score` between 0–99, logs show failing test names |
    | **Sandbox — timeout** | Oversized/slow code near `SANDBOX_RUN_TIMEOUT` | HTTP 200 with `success: false` and timeout text in logs (Section 21) |
    | **Timed lab assignment — expire** | Start assignment, wait past `time_limit_minutes`, submit fix | `403` “Time limit exceeded”; student row `status=expired` |
    | **Timed lab assignment — pass** | Start → submit passing fix within window | `score: 100`, `sandbox_passed: true`, `status=passed` |
    | **Quiz assignment — timer** | Instructor assignment with `time_limit_minutes`; student start → take → submit | Deadline enforced on start response; attempt stored in `quiz_attempts` |
    | **Mistakes quiz** | Student with prior wrong `UserAnswer` rows → `POST /api/quizzes/common-mistakes-quiz` | Returns targeted questions; fallback bank path when OpenAI absent |
    | **Red vs Blue** | Create game → confirmed red attack → blue fix pass/fail | Phase transitions `awaiting_red` ↔ `awaiting_blue`; `blue_score` or `red_score` increments by 1 per round (Section 13.3) |
    | **Misconfig lab** | Logged-in **student** calls `GET /api/admin/config` | 200 with config JSON; **not** callable without JWT |
    | **Admin config vs overview** | Student gets 403 on `GET /api/admin/overview`; student gets 200 on `/api/admin/config` | Confirms authz gap is lab-specific, not global admin bypass |

    ### 20.3 Example sandbox responses (SQL injection lab)

    **Passing fix (excerpt):**
    ```json
    {
    "success": true,
    "fixed": true,
    "improvement_score": 100,
    "message": "All tests passed! Challenge completed.",
    "test_output": "... ----------------------------------------------------------------------\nRan 3 tests in 0.042s\n\nOK\n"
    }
    ```

    **Failing fix (still injectable — excerpt):**
    ```json
    {
    "success": false,
    "fixed": false,
    "improvement_score": 33,
    "message": "Tests failed. Review the output and try again.",
    "test_output": "... FAIL: test_login_still_vulnerable ...\n----------------------------------------------------------------------\nRan 3 tests in 0.038s\n\nFAILED (failures=1)\n"
    }
    ```

    Operators can reproduce by submitting fix code on `/challenges/1/fix` and inspecting the `ResultModal` / network response.

    ### 20.4 Known untested or lightly tested paths

    | Path | Risk | Notes |
    |------|------|-------|
    | `POST /api/quizzes/ai-generate-and-assign` OpenAI failure → Serper → static bank fallback | Medium | Exercised ad hoc; no automated assertion of fallback chain |
    | `POST /api/project/scan-from-git` private repos / auth | Low | Public clone only tested |
    | `POST /api/quizzes/assign-mistakes-quiz` (instructor push) | Medium | Happy path manually verified once |
    | Concurrent Red vs Blue games on same lab | Low | Creation deactivates prior active game; race not stress-tested |
    | Full 128-route matrix | High | Checklist covers representative routes, not exhaustive combinatorics |

    ### 20.5 Recommended manual checklist (minimum before demo)

    | Area | Check |
    |------|--------|
    | Auth | Register student; instructor pending; admin approves; login; logout clears session; tab isolation (`sessionStorage`). |
    | Scanner | Upload valid ZIP; scan returns findings; Dependencies tab populates or degrades gracefully. |
    | Labs | Spot-check attack + **sandbox fix pass** for at least two categories. |
    | Quizzes | Bank quiz; instructor timed assignment; optional mistakes quiz. |
    | Assignments | Instructor creates timed lab assignment; student completes or expires. |
    | Red vs Blue | Create game; attack phase; fix round scoring; end game. |
    | Admin | Security logs filter; user role change; **`/api/admin/overview` admin-only**. |
    | AI (optional) | `GET /api/ai/status`; mentor fallback when keys absent. |

    ### 20.6 Coverage and CI (future work)

    | Target | Suggested approach |
    |--------|-------------------|
    | API | **pytest** + `httpx.AsyncClient` against FastAPI `TestClient`; cover auth, RBAC 403, sandbox mock, assignment expiry. |
    | Frontend | **Vitest** + React Testing Library for `ProtectedRoute`, `ScanContext`, assignment countdown. |
    | E2E | **Playwright** for login → scan → quiz → assignment (optional). |

    **Coverage target (guidance):** For a teaching deployment, **no** global percentage is mandated; for a maintained product, aim for **≥70%** line coverage on `backend/app/api` and **smoke** E2E on auth and scan.

    ---

    ## 21. Operational Failure Modes and Error Handling

    | Failure | Observable behavior | User / operator impact | Recovery |
    |---------|----------------------|---------------------------|----------|
    | **MySQL not ready at backend start** | `startup_event` retries `create_all` up to ten times with three-second delays (`main.py`). | API may delay listening; eventually raises if DB never appears. | Ensure `depends_on` healthchecks in Compose; check `docker logs` for `OperationalError`. |
    | **Docker daemon unreachable or socket missing** | `docker.from_env()` in `sandbox_runner` raises `docker.errors.APIError` or `BuildError`; returned JSON includes `success: false` and log strings; **HTTP 200** with failure payload on fix routes (not always 503). | Fix submission **fails** with diagnostic logs in UI. | Restore Docker; mount `/var/run/docker.sock`; verify `scale_net` exists. |
    | **Sandbox build timeout / read timeout** | `ReadTimeout` and build errors are caught; logs returned to client. | Student sees “not fixed”; may retry. | Increase `SANDBOX_RUN_TIMEOUT`; optimize `run_tests.sh`; check host load. |
    | **OSV.dev down, slow, or rate-limited** | `query_osv` uses **4s timeout**; exceptions are logged (`print`); failures are **silent per package**; merged results may omit some dependency CVEs. | **Static scan still succeeds**; dependency tab may show fewer or no rows. | Retry scan; **self-host** OSV mirror for air-gapped sites. |
    | **Background dependency thread errors** | `_run_dep_scan_background` uses a separate `SessionLocal`; exceptions should not crash main process; partial merge. | **Stale** dependency section until next scan. | Inspect backend logs; fix DB connectivity. |
    | **OPENAI / Serper keys absent** | `POST /api/project/scan/ai` returns **503** with message; mentor endpoints return **fallback** or structured “not configured.” | Features degrade; core scan works. | Set keys in `.env` / `backend/.env` (Section 16). |
    | **Disk full on upload** | `POST /api/project/upload` may fail with 500 or OS error depending on environment. | Upload rejected. | Free disk; set `PROJECT_STORAGE_ROOT` to large volume. |

    **Instructor takeaway:** During an exam, the highest-risk failure modes are **Docker** (sandbox) and **database** connectivity. **OSV** is best-effort; **static regex** scan does not depend on OSV.

    ---

    ## Appendix A — Complete Annotated File Tree

    The following tree lists repository files **excluding** `backend/uploads/`, `node_modules/`, `.git`, and other generated artifacts. Each file has a one-line purpose derived from its role in SCALE.

    ```text
    grad-project/
        ai/
            __init__.py — Python module.
            mentor.py — Python module.
            serper_helpers.py — Python module.
        api/
            ai_mentor.py — FastAPI router or API helper.
            attack_simulator.py — FastAPI router or API helper.
            auth.py — FastAPI router or API helper.
            challenge_assignments.py — FastAPI router or API helper.
            challenges.py — FastAPI router or API helper.
            game_challenge.py — FastAPI router or API helper.
            instructor.py — FastAPI router or API helper.
            messages.py — FastAPI router or API helper.
            misconfig.py — FastAPI router or API helper.
            project_analyzer.py — FastAPI router or API helper.
            projects.py — FastAPI router or API helper.
            quiz_dynamic.py — FastAPI router or API helper.
            quizzes.py — FastAPI router or API helper.
            red_blue.py — FastAPI router or API helper.
            report.py — FastAPI router or API helper.
            security_logs.py — FastAPI router or API helper.
            stats.py — FastAPI router or API helper.
        attacks/
            templates.py — Python module.
        db/
            database.py — Python module.
        scanner/
            dependency_scanner.py — Static analysis or dependency scanning logic.
            detector.py — Static analysis or dependency scanning logic.
            fixer.py — Static analysis or dependency scanning logic.
            report_generator.py — Static analysis or dependency scanning logic.
            rules.py — Static analysis or dependency scanning logic.
            scorer.py — Static analysis or dependency scanning logic.
            semgrep_scanner.py — Static analysis or dependency scanning logic.
        security/
            learning_tracker.py — Python module.
            security_logger.py — Python module.
        crud.py — Python module.
        env_bootstrap.py — Python module.
        main.py — Python module.
        models.py — Python module.
        sandbox_runner.py — Docker sandbox execution or test harness.
        schemas.py — Python module.
        components/
            AttackReplayVisualizer.tsx — React TypeScript component or page.
            BuildingWallAnimation.tsx — React TypeScript component or page.
            ChallengeHintPanel.tsx — React TypeScript component or page.
            ChallengeTutorialVideo.tsx — React TypeScript component or page.
            CodeDiffViewer.tsx — React TypeScript component or page.
            MainLayout.tsx — React TypeScript component or page.
            ProtectedRoute.tsx — React TypeScript component or page.
            ResultModal.tsx — React TypeScript component or page.
            Sidebar.tsx — React TypeScript component or page.
        context/
            ScanContext.tsx — React TypeScript component or page.
        lib/
            api.ts — Source or configuration asset.
            challengeTutorialVideos.ts — Source or configuration asset.
        pages/
            AdminDashboardPage.tsx — React TypeScript component or page.
            AdminStatsPage.tsx — React TypeScript component or page.
            AttackLab.tsx — React TypeScript component or page.
            AttackSuccessPage.tsx — React TypeScript component or page.
            BrokenAuthAttackPage.tsx — React TypeScript component or page.
            BrokenAuthFixPage.tsx — React TypeScript component or page.
            BrokenAuthTutorialPage.tsx — React TypeScript component or page.
            ChallengeAssignmentPage.tsx — React TypeScript component or page.
            ChallengesListPage.tsx — React TypeScript component or page.
            CommandChallengePage.tsx — React TypeScript component or page.
            CommandInjectionAttackPage.tsx — React TypeScript component or page.
            CommandInjectionFixPage.tsx — React TypeScript component or page.
            CommandInjectionTutorialPage.tsx — React TypeScript component or page.
            CsrfAttackPage.tsx — React TypeScript component or page.
            CsrfFixPage.tsx — React TypeScript component or page.
            CsrfTutorialPage.tsx — React TypeScript component or page.
            DashboardHomePage.tsx — React TypeScript component or page.
            DirectoryTraversalAttackPage.tsx — React TypeScript component or page.
            DirectoryTraversalChallengePage.tsx — React TypeScript component or page.
            DirectoryTraversalFixPage.tsx — React TypeScript component or page.
            DirectoryTraversalTutorialPage.tsx — React TypeScript component or page.
            HomePage.tsx — React TypeScript component or page.
            InsecureStorageAttackPage.tsx — React TypeScript component or page.
            InsecureStorageChallengePage.tsx — React TypeScript component or page.
            InsecureStorageFixPage.tsx — React TypeScript component or page.
            InsecureStorageTutorialPage.tsx — React TypeScript component or page.
            InstructorAssignmentResultsPage.tsx — React TypeScript component or page.
            InstructorDashboardPage.tsx — React TypeScript component or page.
            InstructorQuizPage.tsx — React TypeScript component or page.
            LandingPage.tsx — React TypeScript component or page.
            LoginPage.tsx — React TypeScript component or page.
            MessagesPage.tsx — React TypeScript component or page.
            RedBlueCreatePage.tsx — React TypeScript component or page.
            RedBlueGamePage.tsx — React TypeScript component or page.
            RedBlueMyGamesPage.tsx — React TypeScript component or page.
            RedirectAttackPage.tsx — React TypeScript component or page.
            RedirectChallengePage.tsx — React TypeScript component or page.
            RedirectFixPage.tsx — React TypeScript component or page.
            RedirectTutorialPage.tsx — React TypeScript component or page.
            RegisterPage.tsx — React TypeScript component or page.
            Scanner.tsx — React TypeScript component or page.
            ScenarioPage.tsx — React TypeScript component or page.
            SecurityLogsPage.tsx — React TypeScript component or page.
            SecurityMiscAttackPage.tsx — React TypeScript component or page.
            SecurityMiscFixPage.tsx — React TypeScript component or page.
            SecurityMiscTutorialPage.tsx — React TypeScript component or page.
            SqlInjectionAttackPage.tsx — React TypeScript component or page.
            SqlInjectionFixPage.tsx — React TypeScript component or page.
            SqlInjectionTutorialPage.tsx — React TypeScript component or page.
            StudentQuizPage.tsx — React TypeScript component or page.
            TrailerPage.tsx — React TypeScript component or page.
            UnderConstructionPage.tsx — React TypeScript component or page.
            XssAttackPage.tsx — React TypeScript component or page.
            XssFixPage.tsx — React TypeScript component or page.
            XssTutorialPage.tsx — React TypeScript component or page.
            XxeAttackPage.tsx — React TypeScript component or page.
            XxeChallengePage.tsx — React TypeScript component or page.
            XxeFixPage.tsx — React TypeScript component or page.
            XxeTutorialPage.tsx — React TypeScript component or page.
        utils/
            payloads.ts — Source or configuration asset.
        App.tsx — React TypeScript component or page.
        index.css — Source or configuration asset.
        main.tsx — React TypeScript component or page.
    │   ├── docker-compose.yml — configuration or manifest
    │   ├── backend/requirements.txt — configuration or manifest
    │   ├── frontend/package.json — configuration or manifest
    │   ├── .env.example — configuration or manifest
    ```


    ## Appendix B — Complete Route Map (alphabetical by path)

    | Method | Path | Router module | Auth (typical) | Description |
    |--------|------|---------------|----------------|-------------|
    | GET | `/` | `main.py` | No | See Section 14 |
    | GET | `/api/admin/config` | `misconfig.py` | Yes (any user — **missing authz**; lab 6) | Intentional misconfiguration; see §5.2.2 |
    | GET | `/api/admin/overview` | `projects.py` | Yes (admin) | See Section 14 |
    | POST | `/api/ai/analyze-code` | `ai_mentor.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/ai/mentor-chat` | `ai_mentor.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/ai/status` | `ai_mentor.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/attack/simulate` | `attack_simulator.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/auth/admin/approve/{user_id}` | `auth.py` | Yes (admin) | See Section 14 |
    | POST | `/api/auth/admin/create-admin` | `auth.py` | Yes (admin) | See Section 14 |
    | GET | `/api/auth/admin/pending` | `auth.py` | Yes (admin) | See Section 14 |
    | DELETE | `/api/auth/admin/users/{user_id}` | `auth.py` | Yes (admin) | See Section 14 |
    | PUT | `/api/auth/admin/users/{user_id}/role` | `auth.py` | Yes (admin) | See Section 14 |
    | POST | `/api/auth/login` | `auth.py` | No | See Section 14 |
    | POST | `/api/auth/logout` | `auth.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/auth/me` | `auth.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/auth/register` | `auth.py` | No | See Section 14 |
    | GET | `/api/auth/users` | `auth.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/calc/interest` | `misconfig.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge-assignments/create` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenge-assignments/instructor` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenge-assignments/my` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/challenge-assignments/{assignment_id}` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenge-assignments/{assignment_id}/results` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge-assignments/{assignment_id}/start` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenge-assignments/{assignment_id}/status` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge-assignments/{assignment_id}/submit-fix` | `challenge_assignments.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge/blue/fix` | `game_challenge.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge/hint` | `game_challenge.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenge/leaderboard` | `game_challenge.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge/red/attack` | `game_challenge.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenge/start` | `game_challenge.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenge/status` | `game_challenge.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/csrf/accounts` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/csrf/reset` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/csrf/transfer` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/hints` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/hints/use` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/mark-attack-complete` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/ping` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/progress` | `challenges.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/challenges/progress/{challenge_slug}` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/redirect` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/replay/{challenge_slug}` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/source/{challenge_slug}` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/state` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/state/update` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/storage/dump` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/storage/register` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-auth` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-command-injection` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-csrf` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-misc` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-redirect` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-storage` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-traversal` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-xss` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/submit-fix-xxe` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/traversal/read` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/vulnerable-login` | `challenges.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/challenges/xss/comments` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/challenges/xss/comments` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/xss/comments` | `challenges.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/challenges/xxe/parse` | `challenges.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/instructor/user/{user_id}/analytics` | `instructor.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/instructor/user/{user_id}/reset-progress` | `instructor.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/messages/contacts` | `messages.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/messages/send` | `messages.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/messages/unread-count` | `messages.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/messages/with/{user_id}` | `messages.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/analytics` | `projects.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/project/analyze-structure` | `project_analyzer.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/files` | `projects.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/report` | `projects.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/report/pdf` | `projects.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/project/scan` | `projects.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/project/scan-from-git` | `projects.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/scan-status/{scan_id}` | `projects.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/project/scan/ai` | `projects.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/project/upload` | `projects.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/{project_id}` | `projects.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/project/{project_id}/dependencies` | `projects.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quiz/generate` | `quiz_dynamic.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quiz/manage` | `quiz_dynamic.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quiz/manage` | `quiz_dynamic.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/ai-generate-and-assign` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/assign-mistakes-quiz` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/assignments` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/assignments/instructor` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/assignments/student` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/assignments/{assignment_id}/start` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/assignments/{assignment_id}/status` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/quizzes/assignments/{id}` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/assignments/{id}/take` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/attempts` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/common-mistakes-quiz` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/generate-ai-preview` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/manage` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/manage` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/quizzes/questions` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/questions` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/questions` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/quizzes/questions/{q_id}` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | PUT | `/api/quizzes/questions/{q_id}` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/submit-answer` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/submit-attempt` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/quizzes/take` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/topics` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/quizzes/wrong-answer-count` | `quizzes.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/redblue/game/create` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | DELETE | `/api/redblue/game/{game_id}` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/redblue/game/{game_id}` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/redblue/game/{game_id}/attack` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/redblue/game/{game_id}/attacks` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/redblue/game/{game_id}/challenge-code` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/redblue/game/{game_id}/delete` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/redblue/game/{game_id}/end` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | POST | `/api/redblue/game/{game_id}/fix` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/redblue/games` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/redblue/my-games` | `red_blue.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/report/pdf` | `report.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/report/pdf/scan` | `report.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/security/logs` | `security_logs.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/security/logs/stats` | `security_logs.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/stats/admin/dashboard` | `stats.py` | Yes (admin) | See Section 14 |
    | GET | `/api/stats/instructor/dashboard` | `stats.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/stats/progress/me` | `stats.py` | Yes (JWT) | See Section 14 |
    | GET | `/api/user/projects` | `projects.py` | Yes (JWT) | See Section 14 |

    **Total routes:** 128 (including `GET /`).

    ## Appendix C — Glossary

    - **Challenge slug:** Canonical string identifier (e.g. `sql-injection`).
    - **Sandbox runner:** `run_in_sandbox_detailed` Docker build and test execution.
    - **`improvement_score`:** Integer **0–100** returned by `_verify_fix_improvement` in `challenges.py`. It measures **reduction in unittest failure+error counts** between the vulnerable baseline run and the student submission: if `before_count` and `after_count` are those aggregates, then (unless both baseline and after are zero) the score is \(\lfloor \min(100, \max(0, \frac{\text{before}-\text{after}}{\max(\text{before},1)}\times 100)) \rfloor\). **`fixed`** is a separate boolean requiring after-run success and `after_count == 0`. See Section 5.2.1.
    - **Fix improvement score:** Synonym in prose for **`improvement_score`**; do not confuse with quiz score.
    - **Defense Level:** The **`level`** string on `user_learning_progress` (**Beginner** / **Intermediate** / **Advanced**) from `_determine_level`; displayed on the student dashboard. Not a class rank—see Section 9.3.
    - **`currentXp`:** Client-only dashboard figure from `DashboardHomePage.tsx`. **Canonical formula:** `currentXp = solvedLabs * 100 + (quizAttempts.length > 0 ? avgScorePercent : 0)` where `solvedLabs` prefers `learning.vulnerabilities_solved` from `GET /api/stats/progress/me` else distinct slugs from `GET /api/challenges/progress`, and `avgScorePercent` is the mean of `(score/total)*100` over all `GET /api/quizzes/attempts` rows. **If there are zero quiz attempts, the second term is 0** (not NaN and not omitted). Not persisted. See Section 9.6.
    - **Narrative attack XP:** Static integers in `AttackSuccessPage` `typeConfig` (“XP gained”); not stored or added to `currentXp`. See Section 5.9.
    - **Retention score / learning speed / streak_days:** Aggregates on `user_learning_progress`; formulas in `recalculate_learning_progress`. See Section 9.1 and 9.4.
    - **context_type:** `security_logs` discriminator for real vs challenge events.
    - **ScanContext:** React context for scan JSON keyed per user.
    - **vuln_summary:** JSON text in `scan_history` storing scan output.
    - **SKILL_BUCKETS:** Mapping of skill names to challenge slug lists.
    - **OSV.dev:** External vulnerability database API.
    - **scale-user-changed:** Browser event for cross-component auth/scan refresh.
    - **LAB_CHALLENGE_SLUGS:** Integer 1–10 to slug map in `red_blue.py`.
    - **Semgrep engine:** Optional SAST pass in `semgrep_scanner.py`; merged with regex findings in `projects.py`.
    - **Challenge assignment:** Instructor timed lab task stored in `challenge_assignments` / `challenge_assignment_students`.
    - **Mistakes quiz:** Adaptive MCQ set from prior wrong answers via `/api/quizzes/common-mistakes-quiz`.
    - **targets_mistake:** Optional column on `questions` linking a generated MCQ to a student's weak topic.

    ---

    ## Appendix D — Development Changelog

    ### Phase 1 — Core Platform
    Original challenges, scanner, quizzes, auth, dashboards.

    ### Phase 2 — Bug Fixes
    XSS routes, upload paths, sandbox scripts, session isolation, axios multipart.

    ### Phase 3 — Feature Additions (Round 1)
    Code diff viewer, PDF report, AI mentor, Red vs Blue, dependency scanner, attack replay.

    ### Phase 4 — Fixes and Polish (Round 2)
    PDF flattening, background scan threading, user-scoped scan keys, quiz UI cards, My Games portal, replay overlay portal.

    ### Phase 5 — Feature Additions (Round 3)
    Tutorial pages, admin real attempts, AI env configuration, AI status, instructor AI quiz, progress reset, mastery bar chart.

    ### Phase 6 — Scanner, Assignments, and Promotional UX (May 2026)
    - **Semgrep SAST** merged with legacy regex scanner (`semgrep_scanner.py`, `httpx` dependency).
    - **Git repository scan** (`POST /api/project/scan-from-git`) and **async scan status** polling.
    - **Normalized quiz assignment tables** (`quiz_assignment_students`, `quiz_assignment_questions`) with time limits and due dates.
    - **Common mistakes quiz** — student self-service and instructor push (`assign-mistakes-quiz`).
    - **Instructor timed lab assignments** (`/api/challenge-assignments`, `ChallengeAssignmentPage`, instructor results view).
    - **Red vs Blue** turn phases, attack polling enhancements, game delete/end routes.
    - **Promotional trailer** at `/trailer` (GSAP + Three.js, MIU branding assets).
    - **Voiced tutorial videos** served via Vite middleware from `Web-Videos/` (Docker volume mount).
    - **Runtime schema self-heal** in `main._ensure_runtime_schema()` for deployments without Alembic.
    - **Quiz bank expanded** to 200 seeded questions across 20 security topics in `seed_db.py`.

    ---


    ---

    ## Appendix E — ORM Models (Complete Column Reference)

    The following tables are transcribed from `backend/app/models.py` as of the documentation revision date.

    ```python
    from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Float, JSON, Index
    from sqlalchemy.orm import relationship
    from datetime import datetime
    from .db.database import Base

    # --- USER MODEL ---
    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True, index=True)
        email = Column(String(255), unique=True, index=True)
        hashed_password = Column(String(255))
        role = Column(String(50), default='user')
        
        # Gatekeeping field:
        # Students/Admins = True
        # New Instructors = False (Pending)
        is_approved = Column(Boolean, default=True) 

        answers = relationship("UserAnswer", back_populates="user")
        progress = relationship("UserProgress", back_populates="user")
        quiz_attempts = relationship("QuizAttempt", back_populates="user")

    # --- PROGRESS MODEL ---
    class UserProgress(Base):  # <--- FIXED: Inherits from Base now
        __tablename__ = "user_progress"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"))
        challenge_id = Column(String(50))
        completed_at = Column(DateTime, default=datetime.utcnow)
        user = relationship("User", back_populates="progress")

    # --- CHALLENGE MODELS ---
    class XSSComment(Base):
        __tablename__ = "xss_comments"
        id = Column(Integer, primary_key=True, index=True)
        author = Column(String(255))
        content = Column(Text)

    class Challenge(Base):
        __tablename__ = "challenges"
        id = Column(Integer, primary_key=True, index=True)
        title = Column(String(255))
        description = Column(String(255))
        

    # --- QUIZ BANK MODELS ---
    class Question(Base):
        __tablename__ = "questions"
        id = Column(Integer, primary_key=True, index=True)
        text = Column(Text, nullable=False)
        type = Column(String(20)) 
        topic = Column(String(50))
        difficulty = Column(String(20))
        skill_focus = Column(String(50))
        explanation = Column(Text)
        
        options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
        answers = relationship("UserAnswer", back_populates="question")

    class QuestionOption(Base):
        __tablename__ = "question_options"
        id = Column(Integer, primary_key=True, index=True)
        question_id = Column(Integer, ForeignKey("questions.id"))
        text = Column(String(255), nullable=False)
        is_correct = Column(Boolean, default=False)
        
        question = relationship("Question", back_populates="options")

    class UserAnswer(Base):
        __tablename__ = "user_answers"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"))
        question_id = Column(Integer, ForeignKey("questions.id"))
        selected_option_id = Column(Integer, ForeignKey("question_options.id")) 
        is_correct = Column(Boolean)
        timestamp = Column(DateTime, default=datetime.utcnow)
        
        user = relationship("User", back_populates="answers")
        question = relationship("Question", back_populates="answers")

    class QuizAssignment(Base):
        __tablename__ = "quiz_assignments"
        id = Column(Integer, primary_key=True, index=True)
        title = Column(String(255))
        instructor_id = Column(Integer, ForeignKey("users.id"))
        
        assigned_student_ids = Column(Text) 
        question_ids = Column(Text)
        
        time_limit_minutes = Column(Integer, nullable=True)
        due_date = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)


    class QuizAssignmentStudent(Base):
        __tablename__ = "quiz_assignment_students"
        id = Column(Integer, primary_key=True, index=True)
        assignment_id = Column(Integer, ForeignKey("quiz_assignments.id"), nullable=False, index=True)
        student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        started_at = Column(DateTime, nullable=True)
        submitted_at = Column(DateTime, nullable=True)
        status = Column(String(50), default="assigned")


    class QuizAssignmentQuestion(Base):
        __tablename__ = "quiz_assignment_questions"
        id = Column(Integer, primary_key=True, index=True)
        assignment_id = Column(Integer, ForeignKey("quiz_assignments.id"), nullable=False, index=True)
        question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)


    class QuizAttempt(Base):
        """Stores completed quiz attempts with score and time taken."""
        __tablename__ = "quiz_attempts"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        assignment_id = Column(Integer, ForeignKey("quiz_assignments.id"), nullable=True)
        title = Column(String(255))  # e.g. "Practice: SQL Injection" or assignment title
        score = Column(Integer)  # number correct
        total = Column(Integer)
        time_seconds = Column(Integer)  # elapsed time in seconds
        completed_at = Column(DateTime, default=datetime.utcnow)
        user = relationship("User", back_populates="quiz_attempts")


    # --- CSRF CHALLENGE MODEL (NEW) ---
    class CSRFAccount(Base):
        __tablename__ = "csrf_accounts"
        
        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(100), unique=True, index=True)
        balance = Column(Integer, default=100)


    # --- MESSAGING MODEL ---
    class Message(Base):
        __tablename__ = "messages"

        id = Column(Integer, primary_key=True, index=True)
        sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        content = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        is_read = Column(Boolean, default=False)


    # --- PROJECT & SCAN HISTORY MODELS ---
    class Project(Base):
        __tablename__ = "projects"

        # We re-use the existing project identifier (e.g. upload/extracted folder name)
        # so it is easy to correlate filesystem artifacts and DB entries.
        id = Column(String(100), primary_key=True, index=True)
        name = Column(String(255), nullable=False)
        owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        last_scan_date = Column(DateTime, nullable=True)
        latest_risk_score = Column(Integer, nullable=True)
        latest_risk_level = Column(String(20), nullable=True)
        total_scans = Column(Integer, default=0)


    class ScanHistory(Base):
        __tablename__ = "scan_history"

        id = Column(Integer, primary_key=True, index=True)
        project_id = Column(String(100), ForeignKey("projects.id"), nullable=False)
        scan_date = Column(DateTime, default=datetime.utcnow)
        total_vulnerabilities = Column(Integer, nullable=False)
        risk_score = Column(Integer, nullable=False)
        risk_level = Column(String(20), nullable=False)
        # Store vulnerability type distribution as JSON-encoded text so we can
        # aggregate top vulnerability types for admin analytics.
        vuln_summary = Column(Text, nullable=True)


    class ChallengeAssignment(Base):
        __tablename__ = "challenge_assignments"
        id = Column(Integer, primary_key=True, index=True)
        created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
        challenge_slug = Column(String(100), nullable=False)
        title = Column(String(255), nullable=False)
        instructions = Column(Text, nullable=True)
        time_limit_minutes = Column(Integer, nullable=False)
        due_date = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)


    class ChallengeAssignmentStudent(Base):
        __tablename__ = "challenge_assignment_students"
        id = Column(Integer, primary_key=True, index=True)
        assignment_id = Column(Integer, ForeignKey("challenge_assignments.id"), nullable=False)
        student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        started_at = Column(DateTime, nullable=True)
        submitted_at = Column(DateTime, nullable=True)
        time_used_seconds = Column(Integer, default=0)
        status = Column(String(50), default="assigned")
        score = Column(Integer, nullable=True)
        fix_code_submitted = Column(Text, nullable=True)
        sandbox_passed = Column(Boolean, nullable=True)


    # --- RED/BLUE TEAM GAME MODELS ---
    class Team(Base):
        __tablename__ = "teams"

        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(255), nullable=False)
        type = Column(String(10), nullable=False)  # 'red' or 'blue'
        created_at = Column(DateTime, default=datetime.utcnow)
        created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

        members = relationship("TeamMember", back_populates="team")


    class TeamMember(Base):
        __tablename__ = "team_members"

        id = Column(Integer, primary_key=True, index=True)
        team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

        team = relationship("Team", back_populates="members")
        user = relationship("User")


    class GameChallenge(Base):
        """
        Represents a red vs blue challenge for a given uploaded project.
        This is separate from the training 'challenges' table used by labs.
        """
        __tablename__ = "game_challenges"

        id = Column(Integer, primary_key=True, index=True)
        project_id = Column(String(100), nullable=False)
        status = Column(String(20), default="active")  # active / inactive / completed
        created_at = Column(DateTime, default=datetime.utcnow)
        # SCALE lab challenge number (1–10) for instructor-led red vs blue sessions.
        lab_challenge_id = Column(Integer, nullable=True)
        started_at = Column(DateTime, nullable=True)

        red_team_id = Column(Integer, ForeignKey("teams.id"))
        blue_team_id = Column(Integer, ForeignKey("teams.id"))

        red_score = Column(Integer, default=0)
        blue_score = Column(Integer, default=0)


    class ChallengeVulnerability(Base):
        """
        Snapshot of a vulnerability for a specific challenge.
        We keep vulnerabilities even after they are 'fixed' by using is_fixed
        instead of deleting rows, so history and scoring remain intact.
        """
        __tablename__ = "challenge_vulnerabilities"

        id = Column(Integer, primary_key=True, index=True)
        challenge_id = Column(Integer, ForeignKey("game_challenges.id"), nullable=False)
        file = Column(String(500), nullable=False)
        line = Column(Integer)
        vulnerability_type = Column(String(100), nullable=False)
        severity = Column(String(20), nullable=False)
        is_fixed = Column(Boolean, default=False)


    class RedTeamAction(Base):
        __tablename__ = "red_team_actions"

        id = Column(Integer, primary_key=True, index=True)
        challenge_id = Column(Integer, ForeignKey("game_challenges.id"), nullable=False)
        vulnerability_id = Column(Integer, ForeignKey("challenge_vulnerabilities.id"), nullable=True)
        exploit_attempted = Column(Boolean, default=True)
        success = Column(Boolean, default=False)
        timestamp = Column(DateTime, default=datetime.utcnow)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
        payload_used = Column(Text, nullable=True)
        impact_description = Column(Text, nullable=True)
        status = Column(String(20), nullable=True, default="confirmed")


    class BlueTeamFix(Base):
        __tablename__ = "blue_team_fixes"

        id = Column(Integer, primary_key=True, index=True)
        challenge_id = Column(Integer, ForeignKey("game_challenges.id"), nullable=False)
        vulnerability_id = Column(Integer, ForeignKey("challenge_vulnerabilities.id"), nullable=True)
        fixed = Column(Boolean, default=False)
        timestamp = Column(DateTime, default=datetime.utcnow)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
        submitted_code = Column(Text, nullable=True)


    # --- PER-CHALLENGE STATE TRACKING ---
    class ChallengeState(Base):
        """
        Tracks per-user state for each interactive challenge mini-game.
        Used for analytics, hint usage, and game-like progress.
        """
        __tablename__ = "challenge_state"

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        # e.g. 'csrf', 'broken-auth', 'security-misc', 'redirect', etc.
        challenge_id = Column(String(50), nullable=False)

        # Optional high-level stage label controlled by the challenge UIs
        current_stage = Column(String(100), default="started")
        attempt_count = Column(Integer, default=0)
        time_spent_seconds = Column(Integer, default=0)
        hints_used = Column(Integer, default=0)

        created_at = Column(DateTime, default=datetime.utcnow)
        last_updated = Column(DateTime, default=datetime.utcnow)


    class SecurityLog(Base):
        __tablename__ = "security_logs"

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
        event_type = Column(String(100), nullable=False)
        severity = Column(String(20), nullable=False)
        payload = Column(Text, nullable=True)
        endpoint = Column(String(255), nullable=True)
        ip_address = Column(String(64), nullable=True)
        geo_bucket = Column(String(64), nullable=True)
        user_agent = Column(String(512), nullable=True)
        session_id = Column(String(128), nullable=True)
        correlation_id = Column(String(128), nullable=True)
        context_type = Column(String(50), default="real")
        meta_data = Column("metadata", JSON, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

        user = relationship("User")

        __table_args__ = (
            Index("ix_security_logs_user_id", "user_id"),
            Index("ix_security_logs_event_type", "event_type"),
            Index("ix_security_logs_created_at", "created_at"),
        )


    class UserLearningProgress(Base):
        __tablename__ = "user_learning_progress"

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
        vulnerabilities_solved = Column(Integer, default=0)
        failed_attempts = Column(Integer, default=0)
        accuracy = Column(Float, default=0.0)
        avg_time = Column(Float, default=0.0)
        strongest_category = Column(String(100), default="N/A")
        weakest_category = Column(String(100), default="N/A")
        level = Column(String(30), default="Beginner")
        streak_days = Column(Integer, default=0)
        learning_speed = Column(Float, default=0.0)
        retention_score = Column(Float, default=0.0)
        updated_at = Column(DateTime, default=datetime.utcnow)

        user = relationship("User")
    ```

    ## Appendix F — Learning Progress Module (Full Source)

    Complete `backend/app/security/learning_tracker.py` for examiner reference.

    ```python
    from datetime import datetime
    from typing import Optional

    from sqlalchemy import func
    from sqlalchemy.orm import Session

    from .. import models

    # Canonical lab count (7 original + 3 new); not derived from DB rows to avoid doubled totals.
    TOTAL_CHALLENGES = 10

    LEGACY_CHALLENGE_IDS: dict[str, str] = {
        "1": "sql-injection",
        "2": "xss",
        "3": "csrf",
        "4": "command-injection",
        "5": "broken-auth",
        "6": "security-misc",
        "7": "insecure-storage",
        "8": "directory-traversal",
        "9": "xxe",
        "10": "redirect",
    }

    # Six radar dimensions; each maps to one or more progress slugs (10 labs total).
    SKILL_BUCKETS: dict[str, list[str]] = {
        "SQL Injection": ["sql-injection", "broken-auth"],
        "XSS": ["xss"],
        "CSRF": ["csrf", "redirect"],
        "Traversal": ["directory-traversal", "command-injection"],
        "XXE": ["xxe"],
        "Storage": ["insecure-storage", "security-misc"],
    }


    def normalize_progress_challenge_id(raw: str) -> str:
        r = (raw or "").strip().lower()
        return LEGACY_CHALLENGE_IDS.get(r, r)


    def compute_skills_scores(db: Session, user_id: int) -> dict[str, int]:
        rows = (
            db.query(models.UserProgress.challenge_id)
            .filter(models.UserProgress.user_id == user_id)
            .all()
        )
        solved = {normalize_progress_challenge_id(p[0]) for p in rows}
        out: dict[str, int] = {}
        for skill, slugs in SKILL_BUCKETS.items():
            done = sum(1 for s in slugs if s in solved)
            out[skill] = int(round(100 * done / len(slugs)))
        return out


    def _determine_level(vulnerabilities_solved: int, accuracy: float) -> str:
        if vulnerabilities_solved >= 9 and accuracy >= 80:
            return "Advanced"
        if vulnerabilities_solved >= 4 and accuracy >= 60:
            return "Intermediate"
        return "Beginner"


    def ensure_learning_progress(db: Session, user_id: int) -> models.UserLearningProgress:
        row = db.query(models.UserLearningProgress).filter(models.UserLearningProgress.user_id == user_id).first()
        if row:
            return row
        row = models.UserLearningProgress(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


    def recalculate_learning_progress(db: Session, user_id: int) -> models.UserLearningProgress:
        row = ensure_learning_progress(db, user_id)

        solved = (
            db.query(func.count(func.distinct(models.UserProgress.challenge_id)))
            .filter(models.UserProgress.user_id == user_id)
            .scalar()
            or 0
        )
        total_answers = db.query(models.UserAnswer).filter(models.UserAnswer.user_id == user_id).count()
        correct_answers = (
            db.query(models.UserAnswer)
            .filter(models.UserAnswer.user_id == user_id, models.UserAnswer.is_correct == True)  # noqa: E712
            .count()
        )
        failed_answers = max(total_answers - correct_answers, 0)
        avg_time_value = (
            db.query(func.avg(models.QuizAttempt.time_seconds))
            .filter(models.QuizAttempt.user_id == user_id)
            .scalar()
        )
        avg_time = float(avg_time_value or 0.0)
        accuracy = (correct_answers / total_answers * 100.0) if total_answers > 0 else 0.0

        challenge_rows = db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).all()
        skills = compute_skills_scores(db, user_id)
        if skills:
            strongest = max(skills, key=skills.get)
            weakest = min(skills, key=skills.get)
        else:
            strongest = "N/A"
            weakest = "N/A"
        # Streak approximation from consecutive challenge completion days.
        progress_dates = sorted(
            {p.completed_at.date() for p in challenge_rows if p.completed_at is not None},
            reverse=True,
        )
        streak = 0
        if progress_dates:
            current = progress_dates[0]
            for d in progress_dates:
                if (current - d).days == 0:
                    streak += 1
                    current = d
                elif (current - d).days == 1:
                    streak += 1
                    current = d
                else:
                    break

        learning_speed = (solved / max(avg_time, 1.0)) * 100.0 if solved > 0 else 0.0
        retention_score = min(
            100.0,
            max(
                0.0,
                (accuracy * 0.6) + (min(streak, 14) / 14.0 * 20.0) + (100.0 - min(failed_answers * 2, 40)),
            ),
        )

        row.vulnerabilities_solved = min(solved, TOTAL_CHALLENGES)
        row.failed_attempts = failed_answers
        row.accuracy = round(accuracy, 2)
        row.avg_time = round(avg_time, 2)
        row.strongest_category = strongest
        row.weakest_category = weakest
        row.level = _determine_level(solved, accuracy)
        row.streak_days = streak
        row.learning_speed = round(learning_speed, 2)
        row.retention_score = round(retention_score, 2)
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return row


    def build_learning_progress_payload(db: Session, user_id: int) -> dict:
        """
        Single source of truth for student dashboard and instructor analytics.
        """
        profile = recalculate_learning_progress(db, user_id)
        skills = compute_skills_scores(db, user_id)
        skills_radar = [{"subject": name, "value": val} for name, val in skills.items()]
        solved = min(profile.vulnerabilities_solved, TOTAL_CHALLENGES)
        return {
            "vulnerabilities_solved": solved,
            "total_challenges": TOTAL_CHALLENGES,
            "failed_attempts": profile.failed_attempts,
            "accuracy": profile.accuracy,
            "avg_time": profile.avg_time,
            "strongest_category": profile.strongest_category,
            "weakest_category": profile.weakest_category,
            "level": profile.level,
            "streak_days": profile.streak_days,
            "learning_speed": profile.learning_speed,
            "retention_score": profile.retention_score,
            "skills": skills,
            "skills_radar": skills_radar,
            "recommendations": get_learning_recommendations(profile),
        }


    def build_challenge_progress_detail(db: Session, user_id: int) -> list[dict]:
        """
        Returns per-challenge completion status for the
        enhanced skill chart showing all 10 individual labs.
        """
        CHALLENGE_DISPLAY = [
            {"slug": "sql-injection", "label": "SQL Injection", "category": "Injection", "color": "#ef4444"},
            {"slug": "xss", "label": "XSS", "category": "Client-Side", "color": "#f97316"},
            {"slug": "csrf", "label": "CSRF", "category": "Client-Side", "color": "#f59e0b"},
            {"slug": "command-injection", "label": "Command Injection", "category": "Injection", "color": "#dc2626"},
            {"slug": "broken-auth", "label": "Broken Auth", "category": "Auth", "color": "#8b5cf6"},
            {"slug": "security-misc", "label": "Security Misc", "category": "Config", "color": "#06b6d4"},
            {"slug": "insecure-storage", "label": "Insecure Storage", "category": "Storage", "color": "#10b981"},
            {"slug": "directory-traversal", "label": "Dir Traversal", "category": "Path", "color": "#3b82f6"},
            {"slug": "xxe", "label": "XXE", "category": "Injection", "color": "#ec4899"},
            {"slug": "redirect", "label": "Open Redirect", "category": "Validation", "color": "#84cc16"},
        ]
        rows = (
            db.query(models.UserProgress.challenge_id)
            .filter(models.UserProgress.user_id == user_id)
            .all()
        )
        solved = {normalize_progress_challenge_id(r[0]) for r in rows}
        result = []
        for ch in CHALLENGE_DISPLAY:
            slug = ch["slug"]
            result.append(
                {
                    "slug": slug,
                    "label": ch["label"],
                    "category": ch["category"],
                    "color": ch["color"],
                    "completed": slug in solved,
                    "value": 100 if slug in solved else 0,
                }
            )
        return result


    def get_learning_recommendations(profile: Optional[models.UserLearningProgress]) -> list[str]:
        if not profile:
            return ["Start with SQL Injection and XSS beginner labs."]
        recs: list[str] = []
        if profile.weakest_category and profile.weakest_category != "N/A":
            recs.append(f"Focus next on {profile.weakest_category} scenarios.")
        if profile.accuracy < 60:
            recs.append("Review AI Mentor explanations before retrying quizzes.")
        if profile.failed_attempts > 10:
            recs.append("Use progressive hints strategically to reduce repeated failures.")
        if not recs:
            recs.append("Maintain momentum by attempting advanced mixed-vulnerability projects.")
        return recs

    ```

    ## Appendix G — Challenge Hints and Attack Replay Payloads (Source Extracts)

    ### G.1 `_HINTS`

    Progressive hints returned by `GET /api/challenges/hints` for selected slugs (`csrf`, `broken-auth`, `security-misc`, `directory-traversal`, `xxe`, `insecure-storage`).

    ```python
    _HINTS: dict[str, list[dict[str, object]]] = {
        "csrf": [
            {"level": 1, "text": "Look for an action that changes server state without validation.", "penalty": 0},
            {"level": 2, "text": "Think about how a victim's browser might send a request without them clicking a bank button.", "penalty": 5},
            {"level": 3, "text": "Consider abusing an auto-submitting mechanism in HTML that can talk to the vulnerable transfer endpoint.", "penalty": 10},
        ],
        "broken-auth": [
            {"level": 1, "text": "Can you log in without knowing the real password?", "penalty": 0},
            {"level": 2, "text": "Try manipulating the login input so that the server's check always evaluates as true.", "penalty": 5},
            {"level": 3, "text": "Think about classic injection techniques against authentication queries, but work the exact payload out yourself.", "penalty": 10},
        ],
        "security-misc": [
            {"level": 1, "text": "Real apps sometimes expose debug or admin endpoints.", "penalty": 0},
            {"level": 2, "text": "Try calling endpoints that are not linked from the UI or that sound internal/administrative.", "penalty": 5},
            {"level": 3, "text": "Hunt for a configuration or debug endpoint that should never be reachable in production.", "penalty": 10},
        ],
        "directory-traversal": [
            {"level": 1, "text": "Try using ../ in the file name parameter.", "penalty": 0},
            {"level": 2, "text": "Your goal is to escape the intended files directory.", "penalty": 5},
            {"level": 3, "text": "Fix by normalizing paths and rejecting paths outside the base directory.", "penalty": 10},
        ],
        "xxe": [
            {"level": 1, "text": "Use a DOCTYPE payload with an external entity.", "penalty": 0},
            {"level": 2, "text": "Try reading file:///etc/passwd through an entity reference.", "penalty": 5},
            {"level": 3, "text": "Fix by disabling external entities and blocking DTD processing.", "penalty": 10},
        ],
        "insecure-storage": [
            {"level": 1, "text": "Register a user, then dump storage.", "penalty": 0},
            {"level": 2, "text": "Look for plaintext passwords in the dump output.", "penalty": 5},
            {"level": 3, "text": "Fix by hashing before storing credentials.", "penalty": 10},
        ],
    }
    ```

    ### G.2 `ATTACK_REPLAYS`

    Structured steps for `GET /api/challenges/replay/{challenge_slug}`. Step types include `user_action`, `user_input`, `http_request`, `server_processing`, `http_response`.

    ```python
    ATTACK_REPLAYS: dict[str, list[dict[str, object]]] = {
        "sql-injection": [
            {"step": 1, "type": "user_action", "title": "Open login page", "description": "Student navigates to the SQL Injection challenge login form.", "data": None},
            {"step": 2, "type": "user_input", "title": "Enter malicious payload", "description": "Student types a SQL injection payload into the username field.", "data": "' OR 1=1 --"},
            {"step": 3, "type": "http_request", "title": "Request sent to server", "description": "Browser sends a POST request to the vulnerable login endpoint.", "data": 'POST /api/challenges/sqli/login\nContent-Type: application/json\n\n{"username": "\' OR 1=1 --", "password": "anything"}'},
            {"step": 4, "type": "server_processing", "title": "Vulnerable query assembled", "description": "The server builds a SQL query using string interpolation, injecting the payload directly.", "data": "SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = 'anything'"},
            {"step": 5, "type": "server_processing", "title": "Database returns all rows", "description": "The OR 1=1 condition is always true. The -- comments out the password check. All user rows are returned.", "data": "Result: 5 rows returned\n[{id:1, username:'admin', role:'admin'}, ...]"},
            {"step": 6, "type": "http_response", "title": "Server grants admin access", "description": "The server returns the first row's session token, granting admin access without a valid password.", "data": '{"success": true, "message": "Logged in as admin", "token": "eyJ..."}'},
        ],
        "xss": [
            {"step": 1, "type": "user_action", "title": "Open comment section", "description": "Student navigates to the XSS challenge page with a comment input field.", "data": None},
            {"step": 2, "type": "user_input", "title": "Submit script payload", "description": "Student types a script tag as a comment.", "data": "<script>alert(document.cookie)</script>"},
            {"step": 3, "type": "http_request", "title": "Comment stored in database", "description": "The comment is saved without sanitization.", "data": 'POST /api/challenges/xss/comments\n\n{"content": "<script>alert(document.cookie)</script>"}'},
            {"step": 4, "type": "server_processing", "title": "Page renders unsanitized comment", "description": "The server returns the raw comment HTML. The browser parses it as a script tag.", "data": 'innerHTML = "<script>alert(document.cookie)</script>"'},
            {"step": 5, "type": "http_response", "title": "Script executes in victim browser", "description": "The injected script runs with the victim's session context and can steal cookies.", "data": "alert() fires → cookie value: session_id=abc123xyz"},
        ],
        "csrf": [
            {"step": 1, "type": "user_action", "title": "Victim visits malicious page", "description": "A logged-in user visits an attacker-controlled page while their session is active.", "data": None},
            {"step": 2, "type": "server_processing", "title": "Hidden form auto-submits", "description": "The malicious page contains a hidden form that auto-submits on load.", "data": "<form action='http://bank/transfer' method='POST'>\n  <input name='amount' value='9999'>\n  <input name='to' value='attacker'>\n</form>\n<script>document.forms[0].submit()</script>"},
            {"step": 3, "type": "http_request", "title": "Browser sends request with victim cookies", "description": "The browser automatically attaches the victim's session cookie to the cross-origin request.", "data": 'POST /api/challenges/csrf/transfer\nCookie: session=victim_token\n\n{"amount": 9999, "to_user": "attacker"}'},
            {"step": 4, "type": "server_processing", "title": "Server accepts request — no token check", "description": "The server sees a valid session cookie and processes the transfer without verifying origin.", "data": "UPDATE accounts SET balance = balance - 9999 WHERE user = 'victim'"},
            {"step": 5, "type": "http_response", "title": "Transfer completes silently", "description": "Funds transferred. Victim never clicked anything on the real site.", "data": '{"success": true, "transferred": 9999}'},
        ],
        "command-injection": [
            {"step": 1, "type": "user_action", "title": "Open ping tool", "description": "Student opens the command injection challenge which has a ping input field.", "data": None},
            {"step": 2, "type": "user_input", "title": "Inject shell command", "description": "Student appends a shell command after a semicolon in the host field.", "data": "127.0.0.1; cat /etc/passwd"},
            {"step": 3, "type": "http_request", "title": "Request sent to backend", "description": "The input is sent directly to the backend without sanitization.", "data": 'POST /api/calc\n\n{"host": "127.0.0.1; cat /etc/passwd"}'},
            {"step": 4, "type": "server_processing", "title": "Shell interprets injected command", "description": "subprocess.run with shell=True passes the full string to /bin/sh. The semicolon starts a new command.", "data": 'sh -c "ping -c 1 127.0.0.1; cat /etc/passwd"'},
            {"step": 5, "type": "http_response", "title": "Server returns /etc/passwd contents", "description": "The injected command output is returned alongside the ping result.", "data": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:..."},
        ],
        "broken-auth": [
            {"step": 1, "type": "user_action", "title": "Open login page", "description": "Student opens the broken authentication challenge login.", "data": None},
            {"step": 2, "type": "user_input", "title": "Enter admin credentials", "description": "Student enters known or guessed admin credentials.", "data": "username: admin\npassword: admin123"},
            {"step": 3, "type": "http_request", "title": "Login request sent", "description": "Credentials sent to the broken-auth endpoint.", "data": 'POST /api/auth/login?challenge=broken_auth\n\n{"username": "admin", "password": "admin123"}'},
            {"step": 4, "type": "server_processing", "title": "Plaintext password compared", "description": "The server compares passwords in plaintext — no hashing. Credential dump from DB reveals all passwords.", "data": "SELECT password FROM users WHERE username='admin'\nResult: 'admin123' (plaintext match)"},
            {"step": 5, "type": "http_response", "title": "Admin session granted", "description": "Login succeeds. JWT token issued with admin role.", "data": '{"access_token": "eyJ...", "role": "admin"}'},
        ],
        "directory-traversal": [
            {"step": 1, "type": "user_action", "title": "Open file viewer", "description": "Student opens the directory traversal challenge file viewer.", "data": None},
            {"step": 2, "type": "user_input", "title": "Enter traversal payload", "description": "Student uses ../ sequences to escape the intended directory.", "data": "../../../../etc/passwd"},
            {"step": 3, "type": "http_request", "title": "Request sent with traversal path", "description": "The path is sent unvalidated to the file read endpoint.", "data": "GET /api/challenges/directory-traversal/file?path=../../../../etc/passwd"},
            {"step": 4, "type": "server_processing", "title": "Server resolves path outside root", "description": "open() follows the ../ sequences and resolves to /etc/passwd.", "data": "resolved path: /etc/passwd\nopen('/etc/passwd', 'r')"},
            {"step": 5, "type": "http_response", "title": "Sensitive file returned", "description": "The server returns the contents of /etc/passwd to the student.", "data": "root:x:0:0:root:/root:/bin/bash\n..."},
        ],
        "xxe": [
            {"step": 1, "type": "user_action", "title": "Open XML upload form", "description": "Student opens the XXE challenge XML processor.", "data": None},
            {"step": 2, "type": "user_input", "title": "Craft malicious XML", "description": "Student creates XML with an external entity pointing to a sensitive file.", "data": "<?xml version='1.0'?>\n<!DOCTYPE foo [\n  <!ENTITY xxe SYSTEM 'file:///etc/passwd'>\n]>\n<user><name>&xxe;</name></user>"},
            {"step": 3, "type": "http_request", "title": "XML submitted to parser", "description": "The malicious XML is sent to the backend XML parsing endpoint.", "data": "POST /api/challenges/xxe/parse\nContent-Type: application/xml"},
            {"step": 4, "type": "server_processing", "title": "Parser resolves external entity", "description": "The XML parser with resolve_entities=True reads the file referenced in the DOCTYPE.", "data": "&xxe; → reads /etc/passwd → inlines content into XML tree"},
            {"step": 5, "type": "http_response", "title": "File contents in response", "description": "The parsed XML response contains the file contents where &xxe; was referenced.", "data": "<user><name>root:x:0:0:root:/root:/bin/bash\n...</name></user>"},
        ],
        "insecure-storage": [
            {"step": 1, "type": "user_action", "title": "Register and store data", "description": "Student registers an account in the insecure storage challenge.", "data": None},
            {"step": 2, "type": "server_processing", "title": "Data stored in memory only", "description": "The challenge app stores user data in a Python dict, not a database.", "data": "users_store = {}\nusers_store['victim'] = {'password': 'secret123'}"},
            {"step": 3, "type": "user_action", "title": "Exploit: direct memory access", "description": "Because storage is in-memory, any server restart wipes all data. An attacker can also enumerate keys.", "data": "GET /api/challenges/insecure-storage/users"},
            {"step": 4, "type": "http_response", "title": "All user data exposed", "description": "The endpoint returns all keys in the in-memory store without auth.", "data": '{"users": {"victim": {"password": "secret123"}}}'},
        ],
        "security-misc": [
            {"step": 1, "type": "user_action", "title": "Probe debug endpoint", "description": "Student discovers a misconfigured admin endpoint exposed without authentication.", "data": None},
            {"step": 2, "type": "http_request", "title": "Access admin config endpoint", "description": "Student sends a request to the misconfigured endpoint.", "data": "GET /api/admin/config"},
            {"step": 3, "type": "server_processing", "title": "No auth check performed", "description": "The endpoint skips authentication and returns sensitive server configuration.", "data": 'return {"db_url": DB_URL, "secret_key": SECRET_KEY, "debug": True}'},
            {"step": 4, "type": "http_response", "title": "Sensitive config exposed", "description": "Secret keys and database URLs returned to unauthenticated attacker.", "data": '{"db_url": "mysql://root:pass@db/main", "secret_key": "hardcoded_secret"}'},
        ],
        "redirect": [
            {"step": 1, "type": "user_action", "title": "Craft malicious redirect URL", "description": "Student crafts a URL using the application's redirect parameter pointing to an external site.", "data": None},
            {"step": 2, "type": "http_request", "title": "Send redirect request", "description": "The crafted URL is sent to the redirect endpoint.", "data": "GET /api/challenges/redirect?url=https://evil.com"},
            {"step": 3, "type": "server_processing", "title": "No URL validation performed", "description": "The server takes the url parameter and redirects without checking if it is an allowed domain.", "data": "return RedirectResponse(url=request.query_params['url'])"},
            {"step": 4, "type": "http_response", "title": "Victim redirected to attacker site", "description": "User is sent to the external attacker-controlled URL, enabling phishing.", "data": "HTTP 302 Location: https://evil.com"},
        ],
    }
    ```

    ## Appendix H — Frontend Components (`frontend/src/components/`)

    | File | Role |
    |------|------|
    | `AttackReplayVisualizer.tsx` | React UI component |
    | `BuildingWallAnimation.tsx` | React UI component |
    | `ChallengeHintPanel.tsx` | React UI component |
    | `CodeDiffViewer.tsx` | React UI component |
    | `MainLayout.tsx` | React UI component |
    | `ProtectedRoute.tsx` | React UI component |
    | `ResultModal.tsx` | React UI component |
    | `Sidebar.tsx` | React UI component |

    ## Appendix I — Challenge Docker Bind Mounts and Directories

    The backend `docker-compose.yml` mounts each `challenge-*` directory at `/app/challenges/<name>`. Sandbox validation resolves these paths when running `run_tests.sh`.

    ### `challenge-broken-auth/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-command-injection/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-csrf/`
    - `app.py` — challenge lab asset
    - `csrf.sql` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-directory-traversal/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-insecure-storage/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-redirect/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-security-misc/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ### `challenge-sql-injection/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset
    - `users.sql` — challenge lab asset

    ### `challenge-xss/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset
    - `xss.sql` — challenge lab asset

    ### `challenge-xxe/`
    - `app.py` — challenge lab asset
    - `requirements.txt` — challenge lab asset
    - `run_tests.sh` — challenge lab asset
    - `test_app.py` — challenge lab asset

    ## Appendix J — Docker Compose and Environment (Expanded Reference)

    ### J.1 Services (from `docker-compose.yml`)

    | Service | Build / image | Host ports | Depends on | Purpose |
    |---------|---------------|------------|------------|---------|
    | `sandbox_base` | `./backend/sandbox_base` → `scale-sandbox-base` | — | — | Pre-build base for student sandbox images |
    | `backend` | `./backend` | 8000:8000 | healthy DBs, sandbox_base | FastAPI API, sandbox runner |
    | `frontend` | `./frontend` | 5173:5173 | — | Vite dev server for SPA |
    | `ai_service` | `./ai_service` | 8001:8001 | — | Template AI microservice for instructor quiz preview |
    | `main_db` | `mysql:8.0` | 3306:3306 | — | Primary application database |
    | `challenge_db_sqli` | `mysql:8.0` | 3307:3306 | — | SQL injection lab data |
    | `challenge_db_csrf` | `mysql:8.0` | 3308:3306 | — | CSRF lab accounts |

    ### J.2 Named volume

    | Volume | Mount point | Persisted |
    |--------|-------------|-----------|
    | `scale_db_data` | `/var/lib/mysql` in `main_db` | Yes — user accounts, progress, scans |

    ### J.3 Environment variables (from `.env.example` and compose interpolation)

    | Variable | Default in compose | Consumed by | Purpose |
    |----------|-------------------|-------------|---------|
    | `OPENAI_API_KEY` | empty in `.env.example` | Backend, AI paths | Enables OpenAI for mentor, quizzes, scan AI |
    | `SERPER_API_KEY` | empty | Backend | Web-search-backed fallbacks when OpenAI absent |
    | `AI_SERVICE_URL` | `http://ai_service:8001` | Backend | httpx target for template AI quiz generation |
    | `DATABASE_URL` | `mysql+pymysql://user:password@main_db/scale_db` | Backend | SQLAlchemy main DB |
    | `SQLI_DATABASE_URL` | `...@challenge_db_sqli/testdb` | Challenges | SQLi lab connection |
    | `CSRF_DATABASE_URL` | `...@challenge_db_csrf/csrfdb` | Challenges | CSRF lab connection |
    | `SECRET_KEY` | `scale_graduation_project_secret_key` | Backend | JWT signing |
    | `ACCESS_TOKEN_EXPIRE_MINUTES` | `600` | Backend | JWT lifetime |
    | `ENABLE_BROKEN_AUTH_CHALLENGE` | `true` | Backend | SQLite vulnerable login branch |
    | `SANDBOX_MAX_CODE_CHARS` | `200000` | Sandbox | Uploaded fix size cap |
    | `SANDBOX_RUN_TIMEOUT` | `25` | Sandbox | Seconds for unittest run |
    | `VITE_API_URL` | `http://localhost:8000` | Frontend | Axios base URL |


    ## Appendix K — HTTP Route to Python Handler Names

    Each line maps a registered path (after router prefix) to the implementing function in `backend/app/api/`.

    - `GET /` → `read_root()`
    - `GET /api/admin/config` → `exposed_admin_config()`
    - `GET /api/admin/overview` → `admin_overview()`
    - `POST /api/ai/analyze-code` → `analyze_code_with_ai_mentor()`
    - `POST /api/ai/mentor-chat` → `mentor_challenge_chat()`
    - `GET /api/ai/status` → `ai_status()`
    - `POST /api/attack/simulate` → `simulate_attack()`
    - `POST /api/auth/admin/approve/{user_id}` → `approve_instructor()`
    - `POST /api/auth/admin/create-admin` → `create_admin_internal()`
    - `GET /api/auth/admin/pending` → `get_pending_instructors()`
    - `DELETE /api/auth/admin/users/{user_id}` → `delete_user_endpoint()`
    - `PUT /api/auth/admin/users/{user_id}/role` → `update_role_endpoint()`
    - `POST /api/auth/login` → `login()`
    - `POST /api/auth/logout` → `logout()`
    - `GET /api/auth/me` → `get_current_user_profile()`
    - `POST /api/auth/register` → `register()`
    - `GET /api/auth/users` → `search_users()`
    - `POST /api/calc/interest` → `calc_interest()`
    - `POST /api/challenge/blue/fix` → `blue_team_fix()`
    - `POST /api/challenge/hint` → `get_next_hint()`
    - `GET /api/challenge/leaderboard` → `challenge_leaderboard()`
    - `POST /api/challenge/red/attack` → `red_team_attack()`
    - `POST /api/challenge/start` → `start_challenge()`
    - `GET /api/challenge/status` → `challenge_status()`
    - `GET /api/challenges/csrf/accounts` → `get_csrf_accounts()`
    - `POST /api/challenges/csrf/reset` → `reset_csrf_accounts()`
    - `POST /api/challenges/csrf/transfer` → `vulnerable_transfer()`
    - `GET /api/challenges/hints` → `get_hints()`
    - `POST /api/challenges/hints/use` → `use_hint()`
    - `POST /api/challenges/mark-attack-complete` → `mark_attack_complete()`
    - `POST /api/challenges/ping` → `vulnerable_ping()`
    - `GET /api/challenges/progress` → `get_my_progress()`
    - `DELETE /api/challenges/progress/{challenge_slug}` → `delete_challenge_progress()`
    - `GET /api/challenges/redirect` → `vulnerable_redirect()`
    - `GET /api/challenges/replay/{challenge_slug}` → `get_attack_replay()`
    - `GET /api/challenges/state` → `get_challenge_state()`
    - `POST /api/challenges/state/update` → `update_challenge_state()`
    - `GET /api/challenges/storage/dump` → `insecure_storage_dump()`
    - `POST /api/challenges/storage/register` → `insecure_storage_register()`
    - `POST /api/challenges/submit-fix` → `submit_fix_sql()`
    - `POST /api/challenges/submit-fix-auth` → `submit_fix_auth()`
    - `POST /api/challenges/submit-fix-command-injection` → `submit_fix_command_injection()`
    - `POST /api/challenges/submit-fix-csrf` → `submit_fix_csrf()`
    - `POST /api/challenges/submit-fix-misc` → `submit_fix_misc()`
    - `POST /api/challenges/submit-fix-redirect` → `submit_fix_redirect()`
    - `POST /api/challenges/submit-fix-storage` → `submit_fix_storage()`
    - `POST /api/challenges/submit-fix-traversal` → `submit_fix_traversal()`
    - `POST /api/challenges/submit-fix-xss` → `submit_fix_xss()`
    - `POST /api/challenges/submit-fix-xxe` → `submit_fix_xxe()`
    - `GET /api/challenges/traversal/read` → `traversal_read_file()`
    - `POST /api/challenges/vulnerable-login` → `execute_vulnerable_login()`
    - `DELETE /api/challenges/xss/comments` → `clear_xss_comments()`
    - `GET /api/challenges/xss/comments` → `get_xss_comments()`
    - `POST /api/challenges/xss/comments` → `create_xss_comment()`
    - `POST /api/challenges/xxe/parse` → `parse_xml()`
    - `GET /api/instructor/user/{user_id}/analytics` → `get_student_analytics()`
    - `POST /api/instructor/user/{user_id}/reset-progress` → `reset_student_progress()`
    - `GET /api/messages/contacts` → `list_contacts()`
    - `POST /api/messages/send` → `send_message()`
    - `GET /api/messages/unread-count` → `get_unread_count()`
    - `GET /api/messages/with/{user_id}` → `get_conversation()`
    - `GET /api/project/analytics` → `project_analytics()`
    - `POST /api/project/analyze-structure` → `analyze_project_structure()`
    - `GET /api/project/files` → `list_project_files()`
    - `GET /api/project/report` → `get_project_report()`
    - `GET /api/project/report/pdf` → `get_project_report_pdf()`
    - `POST /api/project/scan` → `scan_project()`
    - `POST /api/project/scan/ai` → `scan_project_with_ai()`
    - `POST /api/project/upload` → `upload_project()`
    - `GET /api/project/{project_id}` → `get_project_by_id()`
    - `GET /api/project/{project_id}/dependencies` → `get_project_dependencies()`
    - `POST /api/quiz/generate` → `generate_quiz_from_scan()`
    - `GET /api/quiz/manage` → `quiz_manage_entry()`
    - `POST /api/quiz/manage` → `quiz_manage_mutation()`
    - `POST /api/quizzes/ai-generate-and-assign` → `ai_generate_and_assign()`
    - `POST /api/quizzes/assignments` → `create_assign()`
    - `GET /api/quizzes/assignments/instructor` → `get_instr_assigns()`
    - `GET /api/quizzes/assignments/student` → `get_student_assigns()`
    - `DELETE /api/quizzes/assignments/{id}` → `delete_assign()`
    - `GET /api/quizzes/assignments/{id}/take` → `take_assign_quiz()`
    - `GET /api/quizzes/attempts` → `get_my_quiz_attempts()`
    - `POST /api/quizzes/generate-ai-preview` → `generate_ai()`
    - `GET /api/quizzes/manage` → `quiz_manage_entry()`
    - `POST /api/quizzes/manage` → `quiz_manage_mutation()`
    - `DELETE /api/quizzes/questions` → `delete_all_questions()`
    - `GET /api/quizzes/questions` → `get_questions()`
    - `POST /api/quizzes/questions` → `create_question()`
    - `DELETE /api/quizzes/questions/{q_id}` → `delete_question()`
    - `PUT /api/quizzes/questions/{q_id}` → `update_question()`
    - `POST /api/quizzes/submit-answer` → `submit_answer()`
    - `POST /api/quizzes/submit-attempt` → `submit_quiz_attempt()`
    - `POST /api/quizzes/take` → `take_quiz()`
    - `GET /api/quizzes/topics` → `get_topics()`
    - `POST /api/quizzes/assignments/{assignment_id}/start` → `start_quiz_assignment()`
    - `GET /api/quizzes/assignments/{assignment_id}/status` → `get_assignment_status()`
    - `GET /api/quizzes/wrong-answer-count` → `wrong_answer_count()`
    - `POST /api/quizzes/common-mistakes-quiz` → `common_mistakes_quiz()`
    - `POST /api/quizzes/assign-mistakes-quiz` → `assign_mistakes_quiz()`
    - `POST /api/challenge-assignments/create` → `create_challenge_assignment()`
    - `GET /api/challenge-assignments/instructor` → `instructor_list_assignments()`
    - `GET /api/challenge-assignments/my` → `my_challenge_assignments()`
    - `DELETE /api/challenge-assignments/{assignment_id}` → `deactivate_assignment()`
    - `GET /api/challenge-assignments/{assignment_id}/results` → `instructor_assignment_results()`
    - `POST /api/challenge-assignments/{assignment_id}/start` → `start_assignment()`
    - `GET /api/challenge-assignments/{assignment_id}/status` → `assignment_status()`
    - `POST /api/challenge-assignments/{assignment_id}/submit-fix` → `submit_assignment_fix()`
    - `POST /api/project/scan-from-git` → `scan_from_git()`
    - `GET /api/project/scan-status/{scan_id}` → `get_scan_status()`
    - `POST /api/redblue/game/create` → `create_redblue_game()`
    - `GET /api/redblue/game/{game_id}` → `get_redblue_game()`
    - `POST /api/redblue/game/{game_id}/attack` → `log_attack()`
    - `GET /api/redblue/game/{game_id}/attacks` → `poll_attacks()`
    - `POST /api/redblue/game/{game_id}/end` → `end_game()`
    - `DELETE /api/redblue/game/{game_id}` → `delete_game()`
    - `POST /api/redblue/game/{game_id}/delete` → `delete_game_post()`
    - `POST /api/redblue/game/{game_id}/fix` → `submit_fix()`
    - `GET /api/redblue/games` → `list_games()`
    - `GET /api/redblue/my-games` → `my_redblue_games()`
    - `GET /api/report/pdf` → `generate_pentest_report_pdf()`
    - `GET /api/security/logs` → `get_security_logs()`
    - `GET /api/security/logs/stats` → `get_security_log_stats()`
    - `GET /api/stats/admin/dashboard` → `get_admin_dashboard_stats()`
    - `GET /api/stats/instructor/dashboard` → `get_instructor_stats()`
    - `GET /api/stats/progress/me` → `get_my_learning_progress()`
    - `GET /api/user/projects` → `list_user_projects()`

    ## Appendix L — Static Scanner Rules and Semgrep SAST

    ### L.1 Regex rules (`backend/app/scanner/rules.py`)

    Each rule contributes regex matches to `detector.py`. Severity weights feed `scorer.py` (High=5, Medium=3, Low=1). **`semgrep_scanner.py`** runs in parallel via `projects.run_merged_scan()`; when the Semgrep CLI is available, findings are normalized to the same JSON shape with `engine: "semgrep"` and merged with regex output (Section 6.1).

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

    ---

    ## Appendix M — Primary Backend and Configuration Source Listings

    The following subsections reproduce key files verbatim for examiner review without opening the repository.

    ## M.1 Challenge router (`backend/app/api/challenges.py`)

    ### `backend/app/api/challenges.py`

    ```python
    from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request
    from fastapi.responses import RedirectResponse
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from typing import List
    from pathlib import Path
    import os
    import hashlib
    import xml.etree.ElementTree as ET
    import re
    import shlex

    from ..db.database import get_db
    from .. import sandbox_runner 
    from ..models import XSSComment, UserProgress, User, ChallengeState, CSRFAccount
    from .auth import get_current_user
    from ..security.security_logger import (
        SecurityEventType,
        SecuritySeverity,
        detect_attack_severity,
        log_security_event,
    )
    from ..security.learning_tracker import LEGACY_CHALLENGE_IDS, recalculate_learning_progress
    from ..schemas import (
        LoginAttempt, CodeSubmission, CommentCreate,
        CommentResponse, ProgressResponse, CSRFAccountResponse,
        PingRequest,
        ChallengeStateResponse, ChallengeStateUpdate, HintEntry, HintUseRequest,
    )

    router = APIRouter()
    UPLOADS_ROOT = Path("/app/uploads").resolve()
    INSECURE_USERS: dict[str, str] = {"alice": "password123", "bob": "qwerty", "admin": "admin123"}

    # ---------------------------------------------------------
    # CONNECTION: SQL INJECTION DATABASE (challenge_db_sqli)
    # ---------------------------------------------------------
    SQLI_DB_URL = os.getenv("SQLI_DATABASE_URL", "mysql+pymysql://user:password@challenge_db_sqli/testdb")
    sqli_engine = create_engine(SQLI_DB_URL, pool_pre_ping=True)
    SessionSQLi = sessionmaker(autocommit=False, autoflush=False, bind=sqli_engine)

    # ---------------------------------------------------------
    # CONNECTION: CSRF DATABASE (challenge_db_csrf)
    # ---------------------------------------------------------
    CSRF_DB_URL = os.getenv("CSRF_DATABASE_URL", "mysql+pymysql://user:password@challenge_db_csrf/csrfdb")
    csrf_engine = create_engine(CSRF_DB_URL, pool_pre_ping=True)
    SessionCSRF = sessionmaker(autocommit=False, autoflush=False, bind=csrf_engine)

    try:
        from lxml import etree as LET  # type: ignore
    except Exception:
        LET = None

    def _challenge_source_file(challenge_dir: str) -> Path:
        return (Path("/app/challenges").resolve() / challenge_dir / "app.py").resolve()


    def _challenge_slug_from_dir(challenge_dir: str) -> str:
        return challenge_dir.replace("challenge-", "", 1)


    def _verify_fix_improvement(challenge_dir: str, submitted_code: str):
        source_file = _challenge_source_file(challenge_dir)
        if source_file.exists():
            with open(source_file, "r", encoding="utf-8", errors="ignore") as source_fp:
                vulnerable_source = source_fp.read()
        else:
            vulnerable_source = ""

        before_result = sandbox_runner.run_in_sandbox_detailed(vulnerable_source, challenge_dir)
        after_result = sandbox_runner.run_in_sandbox_detailed(submitted_code or "", challenge_dir)

        before_count = int(before_result.get("failures", 0)) + int(before_result.get("errors", 0))
        after_count = int(after_result.get("failures", 0)) + int(after_result.get("errors", 0))
        fixed = bool(after_result.get("success")) and after_count == 0
        improvement_score = (
            100
            if before_count == 0 and after_count == 0
            else max(0, min(100, int(((before_count - after_count) / max(before_count, 1)) * 100)))
        )
        challenge_slug = _challenge_slug_from_dir(challenge_dir)
        code_diff = (
            sandbox_runner.generate_code_diff(vulnerable_source, submitted_code or "", challenge_slug)
            if fixed and vulnerable_source
            else []
        )
        return {
            "fixed": fixed,
            "improvement_score": improvement_score,
            "before_vulnerabilities": before_count,
            "after_vulnerabilities": after_count,
            "test_output": str(after_result.get("logs") or ""),
            "code_diff": code_diff,
        }


    def _extract_external_entities(xml_data: str) -> dict[str, str]:
        entities: dict[str, str] = {}
        pattern = r"<!ENTITY\s+([A-Za-z0-9_:-]+)\s+SYSTEM\s+['\"]file://([^'\"]+)['\"]>"
        for name, path in re.findall(pattern, xml_data, flags=re.IGNORECASE):
            try:
                entities[name] = Path(path).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                entities[name] = ""
        return entities


    class _XXEFileResolver(LET.Resolver if LET is not None else object):
        """
        Restrict XXE file entity resolution to controlled lab targets.
        """

        def resolve(self, system_url, public_id, context):  # type: ignore[override]
            if LET is None:
                return None

            if not isinstance(system_url, str) or not system_url.startswith("file://"):
                return self.resolve_string("", context)

            raw_path = system_url[len("file://") :]
            target = Path(raw_path).resolve()
            allowed = target == Path("/etc/passwd").resolve()
            if not allowed:
                uploads_real = UPLOADS_ROOT.resolve()
                target_real = target.resolve()
                allowed = target_real == uploads_real or str(target_real).startswith(str(uploads_real) + os.sep)
            if not allowed or not target.exists() or target.is_dir():
                return self.resolve_string("", context)

            try:
                data = target.read_text(encoding="utf-8", errors="ignore")[:5000]
            except Exception:
                data = ""
            return self.resolve_string(data, context)


    # ==========================================
    # SQL INJECTION CHALLENGE
    # ==========================================
    @router.post("/vulnerable-login")
    def execute_vulnerable_login(attempt: LoginAttempt, db_main: Session = Depends(get_db)):
        db = SessionSQLi()
        query_str = f"SELECT * FROM users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
        sev = detect_attack_severity(f"{attempt.username} {attempt.password}", default=SecuritySeverity.MEDIUM)
        try:
            result = db.execute(text(query_str)).mappings().first()
            if result:
                log_security_event(
                    db=db_main,
                    event_type=SecurityEventType.CHALLENGE_SQLI,
                    severity=sev,
                    payload={"username": attempt.username, "password": attempt.password},
                    metadata={"result": "success", "challenge": "sqli-login"},
                    context_type="challenge_simulation",
                )
                return {"message": "Login successful!", "user": result['username']}
            else: raise HTTPException(401, "Invalid credentials")
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(400, "Database Error (SQL Syntax)")
        finally:
            db.close()


    # ==========================================
    # XSS CHALLENGE
    # ==========================================
    @router.get("/xss/comments", response_model=List[CommentResponse])
    def get_xss_comments(db: Session = Depends(get_db)):
        return db.query(XSSComment).order_by(XSSComment.id.asc()).all()


    @router.post("/xss/comments", response_model=CommentResponse)
    def create_xss_comment(
        comment: CommentCreate,
        db: Session = Depends(get_db),
        request: Request = None,
    ):
        row = XSSComment(author=(comment.author or "Guest")[:255], content=comment.content or "")
        db.add(row)
        db.commit()
        db.refresh(row)
        log_security_event(
            db=db,
            event_type=SecurityEventType.CHALLENGE_XSS,
            severity=detect_attack_severity(comment.content, default=SecuritySeverity.MEDIUM),
            payload={"author": row.author, "content_preview": (row.content or "")[:200]},
            request=request,
            metadata={"challenge": "xss", "action": "comment_post"},
            context_type="challenge_simulation",
        )
        return row


    @router.delete("/xss/comments")
    def clear_xss_comments(db: Session = Depends(get_db)):
        db.query(XSSComment).delete()
        db.commit()
        return {"ok": True}

    # ==========================================
    # CSRF CHALLENGE (Uses External DB)
    # ==========================================

    @router.post("/csrf/reset")
    def reset_csrf_accounts(db_main: Session = Depends(get_db)):
        """Resets the balances in the external CSRF database."""
        db = SessionCSRF()
        try:
            db.execute(text("UPDATE accounts SET balance=1000 WHERE username='Alice'"))
            db.execute(text("UPDATE accounts SET balance=0 WHERE username='Bob'"))
            db.commit()
            for username, balance in [("Alice", 1000), ("Bob", 0)]:
                row = db_main.query(CSRFAccount).filter(CSRFAccount.username == username).first()
                if not row:
                    row = CSRFAccount(username=username, balance=balance)
                    db_main.add(row)
                else:
                    row.balance = balance
            db_main.commit()
            return {"message": "Accounts reset. Alice: $1000, Bob: $0"}
        except Exception as e:
            db.rollback()
            db_main.rollback()
            raise HTTPException(500, f"DB Error: {str(e)}")
        finally:
            db.close()

    @router.get("/csrf/accounts", response_model=List[CSRFAccountResponse])
    def get_csrf_accounts(db_main: Session = Depends(get_db)):
        """Fetches accounts from the external CSRF database."""
        db = SessionCSRF()
        try:
            results = db.execute(text("SELECT username, balance FROM accounts")).mappings().all()
            for item in results:
                row = db_main.query(CSRFAccount).filter(CSRFAccount.username == item["username"]).first()
                if not row:
                    db_main.add(CSRFAccount(username=item["username"], balance=item["balance"]))
                else:
                    row.balance = item["balance"]
            db_main.commit()
            return results
        except Exception:
            db_main.rollback()
            # Fallback to ORM mirror when external challenge DB is unavailable.
            return db_main.query(CSRFAccount).order_by(CSRFAccount.username.asc()).all()
        finally:
            db.close()

    @router.post("/csrf/transfer")
    def vulnerable_transfer(to_user: str = Form(...), amount: int = Form(...), db_main: Session = Depends(get_db)):
        """
        Vulnerable Transfer Endpoint (External DB).
        Accepts HTML Form Data (application/x-www-form-urlencoded).
        """
        db = SessionCSRF()
        try:
            # Check Sender (Alice)
            alice = db.execute(text("SELECT balance FROM accounts WHERE username='Alice'")).mappings().first()
            
            if not alice: raise HTTPException(404, "Sender Alice not found")
            if alice['balance'] < amount: raise HTTPException(400, "Insufficient funds")

            # Check Recipient
            recipient = db.execute(text(f"SELECT * FROM accounts WHERE username='{to_user}'")).mappings().first()
            if not recipient: raise HTTPException(404, "Recipient not found")

            # Perform Transfer
            db.execute(text(f"UPDATE accounts SET balance = balance - {amount} WHERE username='Alice'"))
            db.execute(text(f"UPDATE accounts SET balance = balance + {amount} WHERE username='{to_user}'"))
            db.commit()
            for username, delta in [("Alice", -amount), (to_user, amount)]:
                row = db_main.query(CSRFAccount).filter(CSRFAccount.username == username).first()
                if not row:
                    row = CSRFAccount(username=username, balance=max(delta, 0))
                    db_main.add(row)
                else:
                    row.balance = (row.balance or 0) + delta
            db_main.commit()
            log_security_event(
                db=db_main,
                event_type=SecurityEventType.CHALLENGE_CSRF,
                severity=SecuritySeverity.HIGH,
                payload={"to_user": to_user, "amount": amount},
                metadata={"result": "transfer_executed", "challenge": "csrf"},
                context_type="challenge_simulation",
            )

            return {"message": f"Transferred ${amount} to {to_user}"}
        except Exception as e:
            db.rollback()
            db_main.rollback()
            if isinstance(e, HTTPException): raise e
            raise HTTPException(500, f"Transfer Failed: {str(e)}")
        finally:
            db.close()

    # ==========================================
    # SANDBOX SUBMISSION
    # ==========================================
    @router.post("/submit-fix")
    def submit_fix_sql(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-sql-injection", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "sql-injection")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "sql-injection"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        log_security_event(
            db=db,
            event_type=SecurityEventType.SANDBOX_EXECUTION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.HIGH,
            payload={"challenge": "sql-injection"},
            user_id=current_user.id,
            metadata={"success": success, "logs_preview": (logs or "")[:500]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}

    @router.post("/submit-fix-xss")
    def submit_fix_xss(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-xss", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "xss")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "xss"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}

    @router.post("/submit-fix-csrf")
    def submit_fix_csrf(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-csrf", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "csrf")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "csrf"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}

    # ==========================================
    # COMMAND INJECTION CHALLENGE
    # ==========================================
    import subprocess

    # Success marker: if this appears in command output, frontend treats as attack success
    COMMAND_INJECTION_MARKER = "COMMAND_INJECTION_SUCCESS"


    def _safe_ping_with_simulated_injection(host_input: str) -> tuple[str, bool]:
        """
        Execute only the primary ping target without shell expansion.
        If an injected segment is present, simulate command-injection success
        when the payload tries to echo the marker string.
        """
        raw = (host_input or "").strip()
        for sep in ("&&", "||", ";", "|"):
            if sep in raw:
                host_target, injected = raw.split(sep, 1)
                host_target = host_target.strip()
                injected = injected.strip()
                break
        else:
            host_target = raw
            injected = ""

        if not host_target:
            raise HTTPException(status_code=400, detail="Host is required")

        result = subprocess.run(
            ["ping", "-c", "1", host_target],
            shell=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = (result.stdout or "") + (result.stderr or "")

        simulated_success = False
        if injected:
            try:
                tokens = shlex.split(injected)
            except ValueError:
                tokens = [injected]

            if COMMAND_INJECTION_MARKER in injected:
                simulated_success = True

            simulated_line = (
                f"\n[simulated] injected segment detected: {injected[:200]}\n"
                f"[simulated] shell execution blocked for safety.\n"
            )
            if tokens and tokens[0] == "echo" and len(tokens) > 1:
                simulated_line += " ".join(tokens[1:]) + "\n"
            if simulated_success and COMMAND_INJECTION_MARKER not in simulated_line:
                simulated_line += f"{COMMAND_INJECTION_MARKER}\n"
            output += simulated_line

        return output, simulated_success

    @router.post("/ping")
    def vulnerable_ping(req: PingRequest, db_main: Session = Depends(get_db)):
        """
        Training endpoint for command-injection payloads.
        Real shell execution of injected segments is blocked for platform safety.
        """
        try:
            # Safety guardrail: keep payload size bounded and reject multiline input.
            # This preserves challenge behavior while reducing abuse potential.
            if len(req.host or "") > 200 or "\n" in req.host or "\r" in req.host:
                raise HTTPException(status_code=400, detail="Invalid host payload")
        
            output, simulated_success = _safe_ping_with_simulated_injection(req.host)
            log_security_event(
                db=db_main,
                event_type=SecurityEventType.CHALLENGE_COMMAND,
                severity=detect_attack_severity(req.host, default=SecuritySeverity.MEDIUM),
                payload={"host": req.host},
                metadata={"success_marker": simulated_success, "challenge": "command-injection"},
                context_type="challenge_simulation",
            )
            return {"output": output, "success": simulated_success}
        except subprocess.TimeoutExpired:
            return {"output": "Command timed out.", "success": False}
        except Exception as e:
            return {"output": str(e), "success": False}

    @router.post("/submit-fix-command-injection")
    def submit_fix_command_injection(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-command-injection", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "command-injection")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "command-injection"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}


    @router.post("/submit-fix-auth")
    def submit_fix_auth(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-broken-auth", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "broken-auth")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "broken-auth"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}


    @router.post("/submit-fix-misc")
    def submit_fix_misc(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-security-misc", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "security-misc")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "security-misc"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}

    # ==========================================
    # UNVALIDATED REDIRECT CHALLENGE
    # ==========================================
    # Vulnerable: redirects to any URL from query param (open redirect).
    # Attack goal: craft a link that sends the victim to a malicious/success page.
    @router.get("/redirect")
    def vulnerable_redirect(
        url: str = Query(..., description="Redirect target"),
        db_main: Session = Depends(get_db),
        request: Request = None,
    ):
        """Vulnerable endpoint: redirects to the given URL without validation (open redirect)."""
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_REDIRECT,
            severity=SecuritySeverity.MEDIUM,
            payload={"url": url},
            request=request,
            metadata={"challenge": "redirect"},
            context_type="challenge_simulation",
        )
        return RedirectResponse(url=url, status_code=302)

    @router.post("/submit-fix-redirect")
    def submit_fix_redirect(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-redirect", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "redirect")
            recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type=SecurityEventType.FIX_SUBMISSION,
            severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
            payload={"challenge": "redirect"},
            user_id=current_user.id,
            metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
            context_type="challenge_simulation",
        )
        return {"success": success, "logs": logs, **verification}


    # ==========================================
    # NEW CHALLENGE FIX SUBMISSIONS
    # ==========================================
    @router.post("/submit-fix-traversal")
    def submit_fix_traversal(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-directory-traversal", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "directory-traversal")
            recalculate_learning_progress(db, current_user.id)
        return {"success": success, "logs": logs, **verification}


    @router.post("/submit-fix-xxe")
    def submit_fix_xxe(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-xxe", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "xxe")
            recalculate_learning_progress(db, current_user.id)
        return {"success": success, "logs": logs, **verification}


    @router.post("/submit-fix-storage")
    def submit_fix_storage(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        verification = _verify_fix_improvement("challenge-insecure-storage", submission.code)
        success = bool(verification.get("fixed"))
        logs = str(verification.get("test_output") or "")
        if success:
            mark_challenge_complete(db, current_user.id, "insecure-storage")
            recalculate_learning_progress(db, current_user.id)
        return {"success": success, "logs": logs, **verification}


    # ==========================================
    # DIRECTORY TRAVERSAL CHALLENGE
    # ==========================================
    @router.get("/traversal/read")
    def traversal_read_file(
        file: str = Query(..., description="File name/path"),
        secure: bool = Query(False),
        db_main: Session = Depends(get_db),
        request: Request = None,
    ):
        """Vulnerable path joins user input to base dir and reads the file — no payload classification."""
        base = str(UPLOADS_ROOT.resolve())
        os.makedirs(base, exist_ok=True)
        full_path = os.path.join(base, file)
        requested_path = file
        if secure:
            base_real = os.path.realpath(base)
            target_real = os.path.realpath(full_path)
            if target_real != base_real and not target_real.startswith(base_real + os.sep):
                raise HTTPException(status_code=403, detail="Blocked by secure path normalization")
        try:
            if not os.path.isfile(full_path):
                raise HTTPException(status_code=404, detail="File not found")
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()[:5000]
            resolved_path = os.path.realpath(full_path)
            response = {
                "secure_mode": secure,
                "request_path": requested_path,
                "accessed_path": resolved_path,
                "resolved_path": resolved_path,
                "content": content,
            }
            log_security_event(
                db=db_main,
                event_type=SecurityEventType.CHALLENGE_TRAVERSAL,
                severity=SecuritySeverity.MEDIUM,
                payload={"file": file, "secure": secure},
                request=request,
                metadata={"challenge": "traversal"},
                context_type="challenge",
            )
            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    # ==========================================
    # XXE CHALLENGE
    # ==========================================
    @router.post("/xxe/parse")
    def parse_xml(payload: dict, db_main: Session = Depends(get_db), request: Request = None):
        xml_data = payload.get("xml") or ""
        secure = bool(payload.get("secure", False))
        if secure:
            # Secure mode: block DTD and external entities entirely.
            if "<!DOCTYPE" in xml_data.upper() or "<!ENTITY" in xml_data.upper():
                return {
                    "secure_mode": True,
                    "xml_input": xml_data,
                    "parsed_result": "External entities are blocked by secure parser policy.",
                    "extracted_sensitive_data": None,
                }
            try:
                root = ET.fromstring(xml_data)
                return {
                    "secure_mode": True,
                    "xml_input": xml_data,
                    "parsed_result": ET.tostring(root, encoding="unicode"),
                    "extracted_sensitive_data": None,
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Secure parse error: {e}")

        # Vulnerable mode: use a real XML parser that resolves entities.
        if LET is None:
            raise HTTPException(status_code=500, detail="XXE parser unavailable: lxml is not installed")

        try:
            parser = LET.XMLParser(resolve_entities=True, load_dtd=True, no_network=True, recover=True)
            parser.resolvers.add(_XXEFileResolver())
            root = LET.fromstring(xml_data.encode("utf-8"), parser=parser)
            parsed_output = LET.tostring(root, encoding="unicode")[:5000]
            extracted = parsed_output if any(marker in parsed_output for marker in ["root:x:", "daemon:x:", "/bin/", "nobody:"]) else None

            response = {
                "secure_mode": False,
                "xml_input": xml_data,
                "parsed_result": parsed_output,
                "parsed_output": parsed_output,
                "extracted_sensitive_data": extracted,
                "sensitive_data": extracted,
            }
            log_security_event(
                db=db_main,
                event_type=SecurityEventType.CHALLENGE_XXE,
                severity=SecuritySeverity.MEDIUM if extracted else SecuritySeverity.LOW,
                payload={"xml_preview": xml_data[:300], "secure": secure},
                request=request,
                metadata={"challenge": "xxe", "real_parser": "lxml"},
                context_type="challenge",
            )
            return response
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Parse error: {e}")


    # ==========================================
    # INSECURE STORAGE CHALLENGE
    # ==========================================
    @router.post("/storage/register")
    def insecure_storage_register(payload: dict, db_main: Session = Depends(get_db), request: Request = None):
        username = (payload.get("username") or "").strip()
        password = (payload.get("password") or "").strip()
        secure = bool(payload.get("secure", False))
        if not username or not password:
            raise HTTPException(status_code=400, detail="username/password required")
        stored_value = hashlib.sha256(password.encode()).hexdigest() if secure else password
        INSECURE_USERS[username] = stored_value
        response = {
            "ok": True,
            "username": username,
            "secure_mode": secure,
            "stored_value_preview": f"{stored_value[:24]}..." if secure else stored_value,
            "risk": "Low (hashed password)" if secure else "High (plaintext password)",
        }
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_STORAGE,
            severity=SecuritySeverity.HIGH if not secure else SecuritySeverity.LOW,
            payload={"username": username, "secure": secure},
            request=request,
            metadata={"challenge": "storage", "action": "register"},
            context_type="challenge",
        )
        return response


    @router.get("/storage/dump")
    def insecure_storage_dump(
        secure: bool = Query(False),
        db_main: Session = Depends(get_db),
        request: Request = None,
    ):
        if secure:
            users = [
                {"username": u, "password_hash": hashlib.sha256(p.encode()).hexdigest() if len(p) < 64 else p}
                for u, p in INSECURE_USERS.items()
            ]
            response = {
                "secure_mode": True,
                "users": users,
                "exposure_risk": "Passwords are hashed; direct credential disclosure is reduced.",
            }
            log_security_event(
                db=db_main,
                event_type=SecurityEventType.CHALLENGE_STORAGE,
                severity=SecuritySeverity.LOW,
                payload={"secure": True},
                request=request,
                metadata={"challenge": "storage", "action": "dump"},
                context_type="challenge",
            )
            return response
        users = [{"username": u, "password": p} for u, p in INSECURE_USERS.items()]
        response = {
            "secure_mode": False,
            "users": users,
            "exposure_risk": "Dump returns stored credential material as persisted.",
        }
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_STORAGE,
            severity=SecuritySeverity.MEDIUM,
            payload={"secure": False},
            request=request,
            metadata={"challenge": "storage", "action": "dump"},
            context_type="challenge",
        )
        return response

    # ==========================================
    # HELPERS
    # ==========================================
    def mark_challenge_complete(db: Session, user_id: int, challenge_name: str):
        if not db.query(UserProgress).filter(UserProgress.user_id==user_id, UserProgress.challenge_id==challenge_name).first():
            db.add(UserProgress(user_id=user_id, challenge_id=challenge_name)); db.commit()

    @router.get("/progress", response_model=List[ProgressResponse])
    def get_my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        return db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()


    def _progress_challenge_variants(slug: str) -> set[str]:
        s = (slug or "").strip().lower()
        variants = {s}
        for legacy_num, canon in LEGACY_CHALLENGE_IDS.items():
            if canon == s:
                variants.add(legacy_num)
        return variants


    @router.delete("/progress/{challenge_slug}")
    def delete_challenge_progress(
        challenge_slug: str,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        variants = _progress_challenge_variants(challenge_slug)
        found = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == current_user.id, UserProgress.challenge_id.in_(variants))
            .first()
        )
        if not found:
            raise HTTPException(status_code=404, detail="No progress record found for this challenge.")
        db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.challenge_id.in_(variants),
        ).delete(synchronize_session=False)
        db.query(ChallengeState).filter(
            ChallengeState.user_id == current_user.id,
            ChallengeState.challenge_id.in_(variants),
        ).delete(synchronize_session=False)
        db.commit()
        recalculate_learning_progress(db, current_user.id)
        log_security_event(
            db=db,
            event_type="CHALLENGE_PROGRESS_DELETED",
            severity=SecuritySeverity.LOW,
            payload={"challenge_slug": challenge_slug},
            request=request,
            user_id=current_user.id,
            metadata={"challenge_slug": challenge_slug},
            context_type="challenge",
        )
        return {"message": "Challenge progress deleted.", "challenge_id": challenge_slug}


    @router.post("/mark-attack-complete")
    def mark_attack_complete(
        challenge_type: str = Query(..., description="Challenge type: sql-injection, xss, csrf, command-injection, redirect"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        """Mark that the current user successfully completed an attack simulation."""
        allowed = {
            "sql-injection",
            "xss",
            "csrf",
            "command-injection",
            "redirect",
            "broken-auth",
            "security-misc",
            "directory-traversal",
            "xxe",
            "insecure-storage",
        }
        if challenge_type not in allowed:
            raise HTTPException(400, f"Invalid challenge type. Must be one of: {allowed}")
        mark_challenge_complete(db, current_user.id, challenge_type)
        recalculate_learning_progress(db, current_user.id)
        return {"ok": True}


    # ==========================================
    # CHALLENGE STATE & HINTS (GAME LAYER)
    # ==========================================

    def _get_or_create_state(db: Session, user_id: int, challenge_id: str) -> ChallengeState:
        state = (
            db.query(ChallengeState)
            .filter(ChallengeState.user_id == user_id, ChallengeState.challenge_id == challenge_id)
            .first()
        )
        if not state:
            state = ChallengeState(user_id=user_id, challenge_id=challenge_id)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state


    @router.get("/state", response_model=ChallengeStateResponse)
    def get_challenge_state(
        challenge_id: str = Query(..., description="Challenge id, e.g. csrf, broken-auth, redirect"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        state = _get_or_create_state(db, current_user.id, challenge_id)
        return state


    @router.post("/state/update", response_model=ChallengeStateResponse)
    def update_challenge_state(
        update: ChallengeStateUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        state = _get_or_create_state(db, current_user.id, update.challenge_id)
        if update.current_stage:
            state.current_stage = update.current_stage
        if update.attempt_delta:
            state.attempt_count = (state.attempt_count or 0) + update.attempt_delta
        if update.time_spent_delta:
            state.time_spent_seconds = (state.time_spent_seconds or 0) + update.time_spent_delta
        from datetime import datetime as _dt
        state.last_updated = _dt.utcnow()
        db.commit()
        db.refresh(state)
        return state


    _HINTS: dict[str, list[dict[str, object]]] = {
        "csrf": [
            {"level": 1, "text": "Look for an action that changes server state without validation.", "penalty": 0},
            {"level": 2, "text": "Think about how a victim's browser might send a request without them clicking a bank button.", "penalty": 5},
            {"level": 3, "text": "Consider abusing an auto-submitting mechanism in HTML that can talk to the vulnerable transfer endpoint.", "penalty": 10},
        ],
        "broken-auth": [
            {"level": 1, "text": "Can you log in without knowing the real password?", "penalty": 0},
            {"level": 2, "text": "Try manipulating the login input so that the server's check always evaluates as true.", "penalty": 5},
            {"level": 3, "text": "Think about classic injection techniques against authentication queries, but work the exact payload out yourself.", "penalty": 10},
        ],
        "security-misc": [
            {"level": 1, "text": "Real apps sometimes expose debug or admin endpoints.", "penalty": 0},
            {"level": 2, "text": "Try calling endpoints that are not linked from the UI or that sound internal/administrative.", "penalty": 5},
            {"level": 3, "text": "Hunt for a configuration or debug endpoint that should never be reachable in production.", "penalty": 10},
        ],
        "directory-traversal": [
            {"level": 1, "text": "Try using ../ in the file name parameter.", "penalty": 0},
            {"level": 2, "text": "Your goal is to escape the intended files directory.", "penalty": 5},
            {"level": 3, "text": "Fix by normalizing paths and rejecting paths outside the base directory.", "penalty": 10},
        ],
        "xxe": [
            {"level": 1, "text": "Use a DOCTYPE payload with an external entity.", "penalty": 0},
            {"level": 2, "text": "Try reading file:///etc/passwd through an entity reference.", "penalty": 5},
            {"level": 3, "text": "Fix by disabling external entities and blocking DTD processing.", "penalty": 10},
        ],
        "insecure-storage": [
            {"level": 1, "text": "Register a user, then dump storage.", "penalty": 0},
            {"level": 2, "text": "Look for plaintext passwords in the dump output.", "penalty": 5},
            {"level": 3, "text": "Fix by hashing before storing credentials.", "penalty": 10},
        ],
    }


    ATTACK_REPLAYS: dict[str, list[dict[str, object]]] = {
        "sql-injection": [
            {"step": 1, "type": "user_action", "title": "Open login page", "description": "Student navigates to the SQL Injection challenge login form.", "data": None},
            {"step": 2, "type": "user_input", "title": "Enter malicious payload", "description": "Student types a SQL injection payload into the username field.", "data": "' OR 1=1 --"},
            {"step": 3, "type": "http_request", "title": "Request sent to server", "description": "Browser sends a POST request to the vulnerable login endpoint.", "data": 'POST /api/challenges/sqli/login\nContent-Type: application/json\n\n{"username": "\' OR 1=1 --", "password": "anything"}'},
            {"step": 4, "type": "server_processing", "title": "Vulnerable query assembled", "description": "The server builds a SQL query using string interpolation, injecting the payload directly.", "data": "SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = 'anything'"},
            {"step": 5, "type": "server_processing", "title": "Database returns all rows", "description": "The OR 1=1 condition is always true. The -- comments out the password check. All user rows are returned.", "data": "Result: 5 rows returned\n[{id:1, username:'admin', role:'admin'}, ...]"},
            {"step": 6, "type": "http_response", "title": "Server grants admin access", "description": "The server returns the first row's session token, granting admin access without a valid password.", "data": '{"success": true, "message": "Logged in as admin", "token": "eyJ..."}'},
        ],
        "xss": [
            {"step": 1, "type": "user_action", "title": "Open comment section", "description": "Student navigates to the XSS challenge page with a comment input field.", "data": None},
            {"step": 2, "type": "user_input", "title": "Submit script payload", "description": "Student types a script tag as a comment.", "data": "<script>alert(document.cookie)</script>"},
            {"step": 3, "type": "http_request", "title": "Comment stored in database", "description": "The comment is saved without sanitization.", "data": 'POST /api/challenges/xss/comments\n\n{"content": "<script>alert(document.cookie)</script>"}'},
            {"step": 4, "type": "server_processing", "title": "Page renders unsanitized comment", "description": "The server returns the raw comment HTML. The browser parses it as a script tag.", "data": 'innerHTML = "<script>alert(document.cookie)</script>"'},
            {"step": 5, "type": "http_response", "title": "Script executes in victim browser", "description": "The injected script runs with the victim's session context and can steal cookies.", "data": "alert() fires → cookie value: session_id=abc123xyz"},
        ],
        "csrf": [
            {"step": 1, "type": "user_action", "title": "Victim visits malicious page", "description": "A logged-in user visits an attacker-controlled page while their session is active.", "data": None},
            {"step": 2, "type": "server_processing", "title": "Hidden form auto-submits", "description": "The malicious page contains a hidden form that auto-submits on load.", "data": "<form action='http://bank/transfer' method='POST'>\n  <input name='amount' value='9999'>\n  <input name='to' value='attacker'>\n</form>\n<script>document.forms[0].submit()</script>"},
            {"step": 3, "type": "http_request", "title": "Browser sends request with victim cookies", "description": "The browser automatically attaches the victim's session cookie to the cross-origin request.", "data": 'POST /api/challenges/csrf/transfer\nCookie: session=victim_token\n\n{"amount": 9999, "to_user": "attacker"}'},
            {"step": 4, "type": "server_processing", "title": "Server accepts request — no token check", "description": "The server sees a valid session cookie and processes the transfer without verifying origin.", "data": "UPDATE accounts SET balance = balance - 9999 WHERE user = 'victim'"},
            {"step": 5, "type": "http_response", "title": "Transfer completes silently", "description": "Funds transferred. Victim never clicked anything on the real site.", "data": '{"success": true, "transferred": 9999}'},
        ],
        "command-injection": [
            {"step": 1, "type": "user_action", "title": "Open ping tool", "description": "Student opens the command injection challenge which has a ping input field.", "data": None},
            {"step": 2, "type": "user_input", "title": "Inject shell command", "description": "Student appends a shell command after a semicolon in the host field.", "data": "127.0.0.1; cat /etc/passwd"},
            {"step": 3, "type": "http_request", "title": "Request sent to backend", "description": "The input is sent directly to the backend without sanitization.", "data": 'POST /api/calc\n\n{"host": "127.0.0.1; cat /etc/passwd"}'},
            {"step": 4, "type": "server_processing", "title": "Shell interprets injected command", "description": "subprocess.run with shell=True passes the full string to /bin/sh. The semicolon starts a new command.", "data": 'sh -c "ping -c 1 127.0.0.1; cat /etc/passwd"'},
            {"step": 5, "type": "http_response", "title": "Server returns /etc/passwd contents", "description": "The injected command output is returned alongside the ping result.", "data": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:..."},
        ],
        "broken-auth": [
            {"step": 1, "type": "user_action", "title": "Open login page", "description": "Student opens the broken authentication challenge login.", "data": None},
            {"step": 2, "type": "user_input", "title": "Enter admin credentials", "description": "Student enters known or guessed admin credentials.", "data": "username: admin\npassword: admin123"},
            {"step": 3, "type": "http_request", "title": "Login request sent", "description": "Credentials sent to the broken-auth endpoint.", "data": 'POST /api/auth/login?challenge=broken_auth\n\n{"username": "admin", "password": "admin123"}'},
            {"step": 4, "type": "server_processing", "title": "Plaintext password compared", "description": "The server compares passwords in plaintext — no hashing. Credential dump from DB reveals all passwords.", "data": "SELECT password FROM users WHERE username='admin'\nResult: 'admin123' (plaintext match)"},
            {"step": 5, "type": "http_response", "title": "Admin session granted", "description": "Login succeeds. JWT token issued with admin role.", "data": '{"access_token": "eyJ...", "role": "admin"}'},
        ],
        "directory-traversal": [
            {"step": 1, "type": "user_action", "title": "Open file viewer", "description": "Student opens the directory traversal challenge file viewer.", "data": None},
            {"step": 2, "type": "user_input", "title": "Enter traversal payload", "description": "Student uses ../ sequences to escape the intended directory.", "data": "../../../../etc/passwd"},
            {"step": 3, "type": "http_request", "title": "Request sent with traversal path", "description": "The path is sent unvalidated to the file read endpoint.", "data": "GET /api/challenges/directory-traversal/file?path=../../../../etc/passwd"},
            {"step": 4, "type": "server_processing", "title": "Server resolves path outside root", "description": "open() follows the ../ sequences and resolves to /etc/passwd.", "data": "resolved path: /etc/passwd\nopen('/etc/passwd', 'r')"},
            {"step": 5, "type": "http_response", "title": "Sensitive file returned", "description": "The server returns the contents of /etc/passwd to the student.", "data": "root:x:0:0:root:/root:/bin/bash\n..."},
        ],
        "xxe": [
            {"step": 1, "type": "user_action", "title": "Open XML upload form", "description": "Student opens the XXE challenge XML processor.", "data": None},
            {"step": 2, "type": "user_input", "title": "Craft malicious XML", "description": "Student creates XML with an external entity pointing to a sensitive file.", "data": "<?xml version='1.0'?>\n<!DOCTYPE foo [\n  <!ENTITY xxe SYSTEM 'file:///etc/passwd'>\n]>\n<user><name>&xxe;</name></user>"},
            {"step": 3, "type": "http_request", "title": "XML submitted to parser", "description": "The malicious XML is sent to the backend XML parsing endpoint.", "data": "POST /api/challenges/xxe/parse\nContent-Type: application/xml"},
            {"step": 4, "type": "server_processing", "title": "Parser resolves external entity", "description": "The XML parser with resolve_entities=True reads the file referenced in the DOCTYPE.", "data": "&xxe; → reads /etc/passwd → inlines content into XML tree"},
            {"step": 5, "type": "http_response", "title": "File contents in response", "description": "The parsed XML response contains the file contents where &xxe; was referenced.", "data": "<user><name>root:x:0:0:root:/root:/bin/bash\n...</name></user>"},
        ],
        "insecure-storage": [
            {"step": 1, "type": "user_action", "title": "Register and store data", "description": "Student registers an account in the insecure storage challenge.", "data": None},
            {"step": 2, "type": "server_processing", "title": "Data stored in memory only", "description": "The challenge app stores user data in a Python dict, not a database.", "data": "users_store = {}\nusers_store['victim'] = {'password': 'secret123'}"},
            {"step": 3, "type": "user_action", "title": "Exploit: direct memory access", "description": "Because storage is in-memory, any server restart wipes all data. An attacker can also enumerate keys.", "data": "GET /api/challenges/insecure-storage/users"},
            {"step": 4, "type": "http_response", "title": "All user data exposed", "description": "The endpoint returns all keys in the in-memory store without auth.", "data": '{"users": {"victim": {"password": "secret123"}}}'},
        ],
        "security-misc": [
            {"step": 1, "type": "user_action", "title": "Probe debug endpoint", "description": "Student discovers a misconfigured admin endpoint exposed without authentication.", "data": None},
            {"step": 2, "type": "http_request", "title": "Access admin config endpoint", "description": "Student sends a request to the misconfigured endpoint.", "data": "GET /api/admin/config"},
            {"step": 3, "type": "server_processing", "title": "No auth check performed", "description": "The endpoint skips authentication and returns sensitive server configuration.", "data": 'return {"db_url": DB_URL, "secret_key": SECRET_KEY, "debug": True}'},
            {"step": 4, "type": "http_response", "title": "Sensitive config exposed", "description": "Secret keys and database URLs returned to unauthenticated attacker.", "data": '{"db_url": "mysql://root:pass@db/main", "secret_key": "hardcoded_secret"}'},
        ],
        "redirect": [
            {"step": 1, "type": "user_action", "title": "Craft malicious redirect URL", "description": "Student crafts a URL using the application's redirect parameter pointing to an external site.", "data": None},
            {"step": 2, "type": "http_request", "title": "Send redirect request", "description": "The crafted URL is sent to the redirect endpoint.", "data": "GET /api/challenges/redirect?url=https://evil.com"},
            {"step": 3, "type": "server_processing", "title": "No URL validation performed", "description": "The server takes the url parameter and redirects without checking if it is an allowed domain.", "data": "return RedirectResponse(url=request.query_params['url'])"},
            {"step": 4, "type": "http_response", "title": "Victim redirected to attacker site", "description": "User is sent to the external attacker-controlled URL, enabling phishing.", "data": "HTTP 302 Location: https://evil.com"},
        ],
    }


    @router.get("/replay/{challenge_slug}")
    def get_attack_replay(
        challenge_slug: str,
        sample: bool = Query(False),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        steps = ATTACK_REPLAYS.get(challenge_slug)
        if not steps:
            raise HTTPException(status_code=404, detail="No replay available for this challenge.")
        if not sample:
            done = (
                db.query(UserProgress)
                .filter(UserProgress.user_id == current_user.id, UserProgress.challenge_id == challenge_slug)
                .first()
            )
            if not done:
                raise HTTPException(
                    status_code=403,
                    detail="Complete the attack first to unlock the replay. Pass ?sample=true for a hint replay.",
                )
        return {"challenge_slug": challenge_slug, "steps": steps, "total_steps": len(steps)}


    @router.get("/hints", response_model=list[HintEntry])
    def get_hints(
        challenge_id: str = Query(..., description="Challenge id, e.g. csrf, broken-auth, security-misc"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        hints = _HINTS.get(challenge_id, [])
        state = _get_or_create_state(db, current_user.id, challenge_id)
        # Unlock up to hints_used + 1 (progressive reveal)
        unlock_count = min(len(hints), (state.hints_used or 0) + 1)
        return [
            HintEntry(id=i, text=h["text"] if i < unlock_count else "Locked hint", unlocked=i < unlock_count)
            for i, h in enumerate(hints, start=1)
        ]


    @router.post("/hints/use", response_model=ChallengeStateResponse)
    def use_hint(
        req: HintUseRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        hints = _HINTS.get(req.challenge_id, [])
        if req.hint_id < 1 or req.hint_id > len(hints):
            raise HTTPException(400, "Invalid hint id for this challenge")
        state = _get_or_create_state(db, current_user.id, req.challenge_id)
        state.hints_used = (state.hints_used or 0) + 1
        from datetime import datetime as _dt
        state.last_updated = _dt.utcnow()
        db.commit()
        db.refresh(state)
        recalculate_learning_progress(db, current_user.id)
        return state
    ```


    ## M.2 Sandbox runner (`backend/app/sandbox_runner.py`)

    ### `backend/app/sandbox_runner.py`

    ```python
    import docker
    import tempfile
    import pathlib
    import shutil
    import uuid
    import os
    import traceback
    import re
    import difflib
    from requests.exceptions import ReadTimeout

    ALLOWED_CHALLENGE_DIRS = {
        "challenge-sql-injection",
        "challenge-xss",
        "challenge-csrf",
        "challenge-command-injection",
        "challenge-redirect",
        "challenge-broken-auth",
        "challenge-security-misc",
        "challenge-directory-traversal",
        "challenge-xxe",
        "challenge-insecure-storage",
    }
    MAX_SUBMITTED_CODE_CHARS = int(os.getenv("SANDBOX_MAX_CODE_CHARS", "200000"))
    SANDBOX_RUN_TIMEOUT = int(os.getenv("SANDBOX_RUN_TIMEOUT", "25"))

    DIFF_ANNOTATIONS: dict[str, list[dict[str, str]]] = {
        "sql-injection": [
            {
                "pattern": 'f"',
                "removed_annotation": (
                    "F-string interpolation inserts user input directly into the SQL query. "
                    "An attacker controls this string and can inject any SQL they want."
                ),
                "added_annotation": (
                    "Parameterized query - the DB driver sends the value separately from the SQL structure. "
                    "The database never interprets user input as SQL syntax."
                ),
            },
            {
                "pattern": "f'",
                "removed_annotation": (
                    "F-string interpolation inserts user input directly into the SQL query. "
                    "An attacker controls this string and can inject any SQL they want."
                ),
                "added_annotation": (
                    "Parameterized query - the DB driver sends the value separately from the SQL structure. "
                    "The database never interprets user input as SQL syntax."
                ),
            },
            {
                "pattern": "execute(",
                "removed_annotation": (
                    "Executing a query built from raw string concatenation. "
                    "The database cannot distinguish between your SQL and the attacker's injected SQL."
                ),
                "added_annotation": (
                    "Passing parameters as a tuple forces the DB driver to escape and quote all values automatically."
                ),
            },
        ],
        "xss": [
            {
                "pattern": "innerHTML",
                "removed_annotation": (
                    "Setting innerHTML with unsanitized user input allows any HTML or script tag the user submits "
                    "to execute in the victim's browser."
                ),
                "added_annotation": (
                    "textContent sets the value as plain text. "
                    "The browser never parses it as HTML so scripts cannot run."
                ),
            },
            {
                "pattern": "render_template_string",
                "removed_annotation": (
                    "render_template_string with user-controlled input enables Server-Side Template Injection. "
                    "Attackers can execute arbitrary Python."
                ),
                "added_annotation": (
                    "Escaping input before rendering ensures any HTML special characters are neutralized "
                    "before the browser sees them."
                ),
            },
        ],
        "command-injection": [
            {
                "pattern": "shell=True",
                "removed_annotation": (
                    "shell=True passes the full command string to /bin/sh. "
                    "If user input is in the string, the attacker can append their own shell commands using ; or &&."
                ),
                "added_annotation": (
                    "shell=False with a list of arguments prevents the shell from ever parsing the input. "
                    "Each argument is passed directly to the process."
                ),
            },
            {
                "pattern": "os.system",
                "removed_annotation": (
                    "os.system passes the string to the shell interpreter directly. "
                    "User input in this string is a direct command injection vulnerability."
                ),
                "added_annotation": (
                    "subprocess.run with a list and shell=False never invokes a shell - user input cannot "
                    "be interpreted as a command."
                ),
            },
        ],
        "csrf": [
            {
                "pattern": "csrf_token",
                "removed_annotation": (
                    "No CSRF token means any website can silently trigger this action on behalf of a "
                    "logged-in user by submitting a hidden form."
                ),
                "added_annotation": (
                    "Validating a per-session CSRF token ensures only requests originating from your own "
                    "page are accepted."
                ),
            }
        ],
        "broken-auth": [
            {
                "pattern": "password",
                "removed_annotation": (
                    "Comparing or storing plaintext passwords means a DB breach exposes every user's real "
                    "password immediately."
                ),
                "added_annotation": (
                    "Hashing with bcrypt stores an irreversible digest. "
                    "Even with DB access, attackers cannot recover the original password."
                ),
            }
        ],
        "directory-traversal": [
            {
                "pattern": "../",
                "removed_annotation": (
                    "Allowing ../ in file paths lets attackers walk up the directory tree and read any file "
                    "the server process has permission to access."
                ),
                "added_annotation": (
                    "Resolving to an absolute path and checking it starts with the allowed base directory "
                    "prevents any escape from the intended folder."
                ),
            }
        ],
        "xxe": [
            {
                "pattern": "resolve_entities",
                "removed_annotation": (
                    "resolve_entities=True allows the XML parser to fetch external resources defined in the "
                    "DOCTYPE, enabling file disclosure and SSRF."
                ),
                "added_annotation": (
                    "Disabling entity resolution makes the parser ignore DOCTYPE declarations entirely - "
                    "external entities are never fetched."
                ),
            }
        ],
    }


    def _is_security_relevant_line(content: str) -> bool:
        stripped = (content or "").strip()
        if not stripped:
            return False
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            return False
        if stripped.startswith("import ") or stripped.startswith("from "):
            return False
        return True


    def _annotation_for_line(challenge_slug: str, line_type: str, content: str):
        if line_type not in {"added", "removed"} or not _is_security_relevant_line(content):
            return None
        rules = DIFF_ANNOTATIONS.get(challenge_slug, [])
        for rule in rules:
            if rule.get("pattern", "") in content:
                if line_type == "removed":
                    return rule.get("removed_annotation")
                return rule.get("added_annotation")
        return None


    def generate_code_diff(original_code: str, fixed_code: str, challenge_slug: str) -> list[dict]:
        diff_output = difflib.unified_diff(
            (original_code or "").splitlines(),
            (fixed_code or "").splitlines(),
            fromfile="original",
            tofile="fixed",
            lineterm="",
        )
        lines: list[dict] = []
        original_line = 0
        fixed_line = 0
        hunk_re = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        for raw in diff_output:
            if raw.startswith("---") or raw.startswith("+++"):
                continue
            if raw.startswith("@@"):
                match = hunk_re.match(raw)
                if match:
                    original_line = int(match.group(1))
                    fixed_line = int(match.group(2))
                continue
            if raw.startswith("-"):
                content = raw[1:]
                lines.append(
                    {
                        "type": "removed",
                        "line_number_original": original_line,
                        "line_number_fixed": None,
                        "content": content,
                        "annotation": _annotation_for_line(challenge_slug, "removed", content),
                    }
                )
                original_line += 1
                continue
            if raw.startswith("+"):
                content = raw[1:]
                lines.append(
                    {
                        "type": "added",
                        "line_number_original": None,
                        "line_number_fixed": fixed_line,
                        "content": content,
                        "annotation": _annotation_for_line(challenge_slug, "added", content),
                    }
                )
                fixed_line += 1
                continue
            if raw.startswith(" "):
                content = raw[1:]
                lines.append(
                    {
                        "type": "context",
                        "line_number_original": original_line,
                        "line_number_fixed": fixed_line,
                        "content": content,
                        "annotation": None,
                    }
                )
                original_line += 1
                fixed_line += 1
        return lines


    def run_in_sandbox(student_code: str, challenge_dir: str, event_logger=None):
        result = run_in_sandbox_detailed(student_code, challenge_dir, event_logger=event_logger)
        return bool(result.get("success")), str(result.get("logs") or "")


    def _parse_test_summary(logs: str) -> dict:
        text = logs or ""
        failures = 0
        errors = 0
        tests_run = 0
        match_run = re.search(r"Ran\s+(\d+)\s+tests?", text)
        if match_run:
            tests_run = int(match_run.group(1))
        match_failed = re.search(r"FAILED\s+\(([^)]*)\)", text)
        if match_failed:
            details = match_failed.group(1)
            m_fail = re.search(r"failures=(\d+)", details)
            m_err = re.search(r"errors=(\d+)", details)
            failures = int(m_fail.group(1)) if m_fail else 0
            errors = int(m_err.group(1)) if m_err else 0
        return {
            "tests_run": tests_run,
            "failures": failures,
            "errors": errors,
        }


    def run_in_sandbox_detailed(student_code: str, challenge_dir: str, event_logger=None):
        """
        Args:
            student_code (str): The code submitted by the student.
            challenge_dir (str): The folder name (e.g., 'challenge-sql-injection').
        """
        run_id = str(uuid.uuid4())
        image_tag = f"scale-challenge-run-{run_id}"

        if challenge_dir not in ALLOWED_CHALLENGE_DIRS:
            if event_logger:
                event_logger({"status": "invalid_challenge_dir", "challenge_dir": challenge_dir})
            return {"success": False, "logs": "Invalid challenge directory", "tests_run": 0, "failures": 0, "errors": 1}
        if not isinstance(student_code, str) or len(student_code) > MAX_SUBMITTED_CODE_CHARS:
            if event_logger:
                event_logger({"status": "submission_too_large", "challenge_dir": challenge_dir})
            return {"success": False, "logs": "Submission is too large", "tests_run": 0, "failures": 0, "errors": 1}
        
        base_path = pathlib.Path("/app/challenges").resolve()
        source_path = (base_path / challenge_dir).resolve()
        print(f"[{run_id}] Running sandbox at: {source_path}")

        if not source_path.exists():
            return {"success": False, "logs": f"Configuration Error: Challenge directory not found at {source_path}", "tests_run": 0, "failures": 0, "errors": 1}

        # Use a temporary directory that gets cleaned up automatically
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = pathlib.Path(temp_dir_str)
            print(f"[{run_id}] Created temporary directory: {temp_dir}")

            client = None
            container = None
            try:
                # 1. Copy the challenge files to the temp dir
                shutil.copytree(source_path, temp_dir, dirs_exist_ok=True)

                # 2. Overwrite app.py with the student's submitted code
                student_code_path = temp_dir / "app.py"
                student_code_path.write_text(student_code)
                
                # 3. Define the Dockerfile with WINDOWS FIX
                # Command-injection challenge needs 'ping' (not in python:3.9-slim)
                ping_install = ""
                if challenge_dir == "challenge-command-injection":
                    ping_install = "RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && rm -rf /var/lib/apt/lists/*\n            "

                dockerfile_content = f"""
                FROM python:3.9-slim
                WORKDIR /app
                RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

                {ping_install}
                # Install dependencies
                COPY requirements.txt .
                RUN pip install --no-cache-dir -r requirements.txt

                # Copy challenge files
                COPY . .

                # --- CRITICAL FIX FOR WINDOWS USERS ---
                RUN sed -i 's/\\r$//' run_tests.sh

                # Run the tests
                CMD ["bash", "run_tests.sh"]
                """
                
                dockerfile_path = temp_dir / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)

                client = docker.from_env()
                print(f"[{run_id}] Building Docker image: {image_tag}...")
                
                # 4. Build the sandbox image
                client.images.build(path=str(temp_dir), tag=image_tag, rm=True)
                print(f"[{run_id}] Build complete.")

                print(f"[{run_id}] Running container...")

                # 5. Create and run the container, then wait with timeout.
                # NOTE: docker.sock access is powerful. Keep this sandbox constrained.
                container = client.containers.run(
                    image_tag,
                    detach=True,
                    remove=False,
                    network="scale_net",
                    mem_limit="256m",
                    cpu_quota=50000,  # ~0.5 CPU
                    pids_limit=128,
                    environment={"PYTHONDONTWRITEBYTECODE": "1"},
                )

                timed_out = False
                exit_code = 1
                try:
                    wait_result = container.wait(timeout=SANDBOX_RUN_TIMEOUT)
                    exit_code = int(wait_result.get("StatusCode", 1))
                except ReadTimeout:
                    timed_out = True
                    try:
                        container.kill()
                    except Exception:
                        pass

                decoded_logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="ignore")
                if timed_out:
                    decoded_logs = (
                        f"Execution timed out after {SANDBOX_RUN_TIMEOUT}s.\n"
                        + decoded_logs
                    )
                    summary = _parse_test_summary(decoded_logs)
                    result = {"success": False, "logs": decoded_logs, **summary}
                else:
                    summary = _parse_test_summary(decoded_logs)
                    success = exit_code == 0 and summary["failures"] == 0 and summary["errors"] == 0
                    result = {"success": success, "logs": decoded_logs, **summary}

            except docker.errors.BuildError as e:
                # Capture build errors (like pip install failing)
                build_logs = "\n".join([line.get('stream', '').strip() for line in e.build_log])
                result = {"success": False, "logs": f"Build Error:\n{build_logs}", "tests_run": 0, "failures": 0, "errors": 1}
            except docker.errors.ContainerError as e:
                # Capture runtime errors
                stderr = (e.stderr or b"").decode("utf-8", errors="ignore")
                stdout = (e.stdout or b"").decode("utf-8", errors="ignore")
                result = {"success": False, "logs": f"Container Error:\n{stdout}\n{stderr}".strip(), "tests_run": 0, "failures": 0, "errors": 1}
            except docker.errors.APIError as e:
                result = {"success": False, "logs": f"Docker API Error: {e.explanation or str(e)}", "tests_run": 0, "failures": 0, "errors": 1}
            except Exception as e:
                result = {
                    "success": False,
                    "logs": f"Sandbox Unexpected Error: {str(e)}\n{traceback.format_exc()}",
                    "tests_run": 0,
                    "failures": 0,
                    "errors": 1,
                }
            finally:
                if container is not None:
                    try:
                        container.remove(force=True)
                    except Exception:
                        pass
                # Cleanup: Remove the image to save space
                if client:
                    try:
                        client.images.remove(image_tag, force=True)
                    except Exception:
                        pass

            if event_logger:
                event_logger(
                    {
                        "status": "completed",
                        "challenge_dir": challenge_dir,
                        "success": bool(result.get("success")),
                        "logs_preview": (result.get("logs") or "")[:500],
                    }
                )
            return result
    ```


    ## M.3 Database seed (`backend/seed_db.py`)

    > **⚠ Default passwords** in this file (`AdminPass123!`, `TeachPass123!`) are for **local development only**. See Section **17.2** before any shared or internet-facing deployment.

    ### `backend/seed_db.py`

    ```python
    from app.env_bootstrap import load_env

    load_env()

    from app.db.database import SessionLocal, engine
    from app import models
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import text
    from passlib.context import CryptContext
    import logging
    import time

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def wait_for_db(max_retries=30, delay=2):
        logger.info("Waiting for database connection...")
        for i in range(max_retries):
            try:
                # Try to create a session and run a simple query
                db = SessionLocal()
                db.execute(text("SELECT 1"))
                db.close()
                logger.info("Database is ready!")
                return
            except OperationalError:
                logger.warning(f"Database not ready yet. Retrying in {delay} seconds... ({i+1}/{max_retries})")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error while waiting for DB: {e}")
                time.sleep(delay)
        
        raise Exception("Could not connect to the database after multiple retries.")

    def seed_users(db: Session):
        """ Creates default Super Admin and Instructor users if they don't exist """
        
        # 1. Create Admin
        admin_email = "admin@scale.edu"
        if not db.query(models.User).filter(models.User.email == admin_email).first():
            admin_user = models.User(
                email=admin_email,
                hashed_password=pwd_context.hash("AdminPass123!"),
                role="admin",
                is_approved=True 
            )
            db.add(admin_user)
            logger.info(f"Created Super Admin: {admin_email}")

        # 2. Create Instructor
        inst_email = "instructor@scale.edu"
        if not db.query(models.User).filter(models.User.email == inst_email).first():
            inst_user = models.User(
                email=inst_email,
                hashed_password=pwd_context.hash("TeachPass123!"),
                role="instructor",
                is_approved=True
            )
            db.add(inst_user)
            logger.info(f"Created Default Instructor: {inst_email}")
        
        db.commit()

    def generate_questions():
        """ Generates 200 questions across top 20 hack methods """
        
        # Categories: 
        # 1. SQLi, 2. XSS, 3. Phishing, 4. MitM, 5. DoS/DDoS, 
        # 6. Credential Stuffing, 7. CSRF, 8. SSRF, 9. Ransomware, 10. Buffer Overflow, 
        # 11. XXE, 12. Directory Traversal, 13. Insecure Deserialization, 14. Session Hijacking, 
        # 15. Command Injection, 16. Zero-Day, 17. DNS Spoofing, 18. Trojans, 19. Keylogging, 20. Priv Escalation
        
        questions = []

        # --- 1. SQL Injection (SQLi) ---
        questions.extend([
            {"text": "What does SQL stand for?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Structured Query Language.", "options": [{"text": "Structured Query Language", "is_correct": True}, {"text": "Simple Query Logic", "is_correct": False}, {"text": "Standard Query Loop", "is_correct": False}, {"text": "System Question Language", "is_correct": False}]},
            {"text": "Which character is typically used to break an SQL query string?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "The single quote is often used to delimit strings in SQL.", "options": [{"text": "' (Single Quote)", "is_correct": True}, {"text": "@ (At symbol)", "is_correct": False}, {"text": "^ (Caret)", "is_correct": False}, {"text": "~ (Tilde)", "is_correct": False}]},
            {"text": "What is the primary defense against SQL Injection?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Prepared statements separate code from data.", "options": [{"text": "Prepared Statements / Parameterized Queries", "is_correct": True}, {"text": "Input Hashing", "is_correct": False}, {"text": "Firewalls", "is_correct": False}, {"text": "HTTPS", "is_correct": False}]},
            {"text": "Which condition is commonly used in SQLi to dump data (e.g., OR 1=...)?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "1=1 is a tautology (always true).", "options": [{"text": "1=1", "is_correct": True}, {"text": "1=0", "is_correct": False}, {"text": "0=1", "is_correct": False}, {"text": "Null=Null", "is_correct": False}]},
            {"text": "What type of SQLi relies on true/false server responses rather than returning data directly?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Hard", "skill_focus": "Knowledge", "explanation": "Blind SQLi infers data based on application behavior.", "options": [{"text": "Blind SQL Injection", "is_correct": True}, {"text": "Union-Based SQLi", "is_correct": False}, {"text": "Error-Based SQLi", "is_correct": False}, {"text": "Direct SQLi", "is_correct": False}]},
            {"text": "Which SQL statement is used to combine results from two queries, often used in attacks?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "UNION allows an attacker to append results to the original query.", "options": [{"text": "UNION", "is_correct": True}, {"text": "JOIN", "is_correct": False}, {"text": "MERGE", "is_correct": False}, {"text": "LINK", "is_correct": False}]},
            {"text": "If an attack successfully drops a table, what principle was violated?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "The database user had excessive privileges (Principle of Least Privilege).", "options": [{"text": "Least Privilege", "is_correct": True}, {"text": "Defense in Depth", "is_correct": False}, {"text": "Security by Obscurity", "is_correct": False}, {"text": "Open Design", "is_correct": False}]},
            {"text": "What tool is commonly used to automate SQL Injection detection?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Medium", "skill_focus": "Tools", "explanation": "SQLMap is the standard open-source tool for this.", "options": [{"text": "SQLMap", "is_correct": True}, {"text": "Nmap", "is_correct": False}, {"text": "Wireshark", "is_correct": False}, {"text": "John the Ripper", "is_correct": False}]},
            {"text": "Which database is associated with the 'information_schema' table?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Hard", "skill_focus": "Knowledge", "explanation": "MySQL, PostgreSQL, and SQL Server use information_schema to store metadata.", "options": [{"text": "MySQL", "is_correct": True}, {"text": "MongoDB", "is_correct": False}, {"text": "Redis", "is_correct": False}, {"text": "Cassandra", "is_correct": False}]},
            {"text": "Does using a stored procedure guarantee safety from SQLi?", "type": "multiple_choice", "topic": "SQL Injection", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Not if the stored procedure itself constructs dynamic SQL via string concatenation.", "options": [{"text": "No, if dynamic SQL is used inside it", "is_correct": True}, {"text": "Yes, always", "is_correct": False}, {"text": "Only in Oracle", "is_correct": False}, {"text": "Only in SQL Server", "is_correct": False}]},
        ])

        # --- 2. Cross-Site Scripting (XSS) ---
        questions.extend([
            {"text": "What does XSS stand for?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Cross-Site Scripting.", "options": [{"text": "Cross-Site Scripting", "is_correct": True}, {"text": "Extra Secure Socket", "is_correct": False}, {"text": "Extreme Server Script", "is_correct": False}, {"text": "XML Site Sheet", "is_correct": False}]},
            {"text": "Which XSS type involves the malicious script being saved on the server's database?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Stored (Persistent) XSS saves the payload to the database.", "options": [{"text": "Stored XSS", "is_correct": True}, {"text": "Reflected XSS", "is_correct": False}, {"text": "DOM XSS", "is_correct": False}, {"text": "Server XSS", "is_correct": False}]},
            {"text": "What is the primary scripting language used in XSS attacks?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "JavaScript is the language of the web browser.", "options": [{"text": "JavaScript", "is_correct": True}, {"text": "Python", "is_correct": False}, {"text": "C++", "is_correct": False}, {"text": "Java", "is_correct": False}]},
            {"text": "What HTML tag is most commonly used to inject XSS?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "The script tag is the standard way to execute JS.", "options": [{"text": "<script>", "is_correct": True}, {"text": "<body>", "is_correct": False}, {"text": "<head>", "is_correct": False}, {"text": "<table>", "is_correct": False}]},
            {"text": "What is the best defense against XSS when rendering user input?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Context-aware output encoding prevents the browser from interpreting data as code.", "options": [{"text": "Output Encoding/Escaping", "is_correct": True}, {"text": "Input Validation only", "is_correct": False}, {"text": "Using HTTP only", "is_correct": False}, {"text": "Disabling Cookies", "is_correct": False}]},
            {"text": "What HTTP header helps mitigate XSS risks?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Content Security Policy (CSP) restricts sources of executable scripts.", "options": [{"text": "Content-Security-Policy (CSP)", "is_correct": True}, {"text": "X-Frame-Options", "is_correct": False}, {"text": "Strict-Transport-Security", "is_correct": False}, {"text": "Access-Control-Allow-Origin", "is_correct": False}]},
            {"text": "Which flag prevents JavaScript from accessing a cookie?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "HttpOnly cookies cannot be read by `document.cookie`.", "options": [{"text": "HttpOnly", "is_correct": True}, {"text": "Secure", "is_correct": False}, {"text": "SameSite", "is_correct": False}, {"text": "Domain", "is_correct": False}]},
            {"text": "What is DOM-based XSS?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Hard", "skill_focus": "Knowledge", "explanation": "The vulnerability exists in client-side code rather than server-side code.", "options": [{"text": "Attack executed entirely in the browser DOM", "is_correct": True}, {"text": "Attack on the Database Object Model", "is_correct": False}, {"text": "Attack via Email", "is_correct": False}, {"text": "Attack on server logs", "is_correct": False}]},
            {"text": "Which function in JavaScript is dangerous and often leads to XSS/Code Injection?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "eval() executes a string as code.", "options": [{"text": "eval()", "is_correct": True}, {"text": "alert()", "is_correct": False}, {"text": "console.log()", "is_correct": False}, {"text": "parseInt()", "is_correct": False}]},
            {"text": "If a user clicks a link in an email and is exploited via XSS, what type is it likely?", "type": "multiple_choice", "topic": "XSS", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Reflected XSS bounces the payload off the server immediately via the URL.", "options": [{"text": "Reflected XSS", "is_correct": True}, {"text": "Stored XSS", "is_correct": False}, {"text": "Local XSS", "is_correct": False}, {"text": "Passive XSS", "is_correct": False}]},
        ])

        # --- 3. Phishing ---
        questions.extend([
            {"text": "What is Phishing?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Social engineering using fraudulent messages.", "options": [{"text": "Deceptive emails to steal data", "is_correct": True}, {"text": "Catching fish", "is_correct": False}, {"text": "Scanning ports", "is_correct": False}, {"text": "Decrypting passwords", "is_correct": False}]},
            {"text": "What is 'Spear Phishing'?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Spear phishing targets specific individuals or organizations.", "options": [{"text": "Targeted attack on a specific person", "is_correct": True}, {"text": "Random spam emails", "is_correct": False}, {"text": "Voice phishing", "is_correct": False}, {"text": "SMS phishing", "is_correct": False}]},
            {"text": "What is 'Whaling' in the context of phishing?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Whaling targets high-profile executives (CEOs, CFOs).", "options": [{"text": "Targeting high-level executives", "is_correct": True}, {"text": "Targeting large databases", "is_correct": False}, {"text": "Targeting system admins only", "is_correct": False}, {"text": "Phishing via underwater cables", "is_correct": False}]},
            {"text": "What is 'Smishing'?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Phishing via SMS text messages.", "options": [{"text": "Phishing via SMS/Text", "is_correct": True}, {"text": "Small Phishing", "is_correct": False}, {"text": "Smart Phishing", "is_correct": False}, {"text": "Social Media Phishing", "is_correct": False}]},
            {"text": "What is a Homograph attack in phishing?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "Using look-alike characters (e.g., Cyrillic 'a' vs Latin 'a') to spoof URLs.", "options": [{"text": "Using look-alike characters in URLs", "is_correct": True}, {"text": "Sending home graphics", "is_correct": False}, {"text": "Attacking home routers", "is_correct": False}, {"text": "Using same-colored fonts", "is_correct": False}]},
            {"text": "What common psychological trigger does phishing rely on?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Easy", "skill_focus": "Psychology", "explanation": "Urgency (e.g., 'Account locked!') forces quick, unthinking errors.", "options": [{"text": "Urgency/Fear", "is_correct": True}, {"text": "Logic", "is_correct": False}, {"text": "Patience", "is_correct": False}, {"text": "Generosity", "is_correct": False}]},
            {"text": "What does 'Vishing' stand for?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Voice Phishing (phone calls).", "options": [{"text": "Voice Phishing", "is_correct": True}, {"text": "Video Phishing", "is_correct": False}, {"text": "Virtual Phishing", "is_correct": False}, {"text": "Visual Phishing", "is_correct": False}]},
            {"text": "How can you verify a link destination before clicking?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "Hovering over the link shows the actual URL.", "options": [{"text": "Hover over the link", "is_correct": True}, {"text": "Click it quickly", "is_correct": False}, {"text": "Reply to the email", "is_correct": False}, {"text": "Copy paste into Notepad", "is_correct": False}]},
            {"text": "What mechanism authenticates email senders to prevent spoofing?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "SPF, DKIM, and DMARC are email auth protocols.", "options": [{"text": "SPF/DKIM/DMARC", "is_correct": True}, {"text": "SSL/TLS", "is_correct": False}, {"text": "SSH", "is_correct": False}, {"text": "HTTP", "is_correct": False}]},
            {"text": "A phishing email asking you to check an invoice usually contains what?", "type": "multiple_choice", "topic": "Phishing", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Malicious attachments (PDF/Office docs with macros) are common.", "options": [{"text": "Malicious Attachment", "is_correct": True}, {"text": "A secure token", "is_correct": False}, {"text": "A valid receipt", "is_correct": False}, {"text": "Encrypted text", "is_correct": False}]},
        ])

        # --- 4. Man-in-the-Middle (MitM) ---
        questions.extend([
            {"text": "What is a Man-in-the-Middle attack?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Attacker intercepts communication between two parties.", "options": [{"text": "Intercepting data between two parties", "is_correct": True}, {"text": "Attacking the middle server", "is_correct": False}, {"text": "Sitting in the middle of a room", "is_correct": False}, {"text": "Stopping data flow", "is_correct": False}]},
            {"text": "What protocol effectively prevents MitM by encrypting traffic?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "HTTPS (via TLS/SSL) encrypts the channel.", "options": [{"text": "HTTPS (TLS/SSL)", "is_correct": True}, {"text": "HTTP", "is_correct": False}, {"text": "FTP", "is_correct": False}, {"text": "Telnet", "is_correct": False}]},
            {"text": "What is ARP Spoofing?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Linking the attacker's MAC address to a legitimate IP on a LAN.", "options": [{"text": "Faking MAC addresses on a LAN", "is_correct": True}, {"text": "Spoofing DNS records", "is_correct": False}, {"text": "Faking IP addresses on WAN", "is_correct": False}, {"text": "Spoofing email headers", "is_correct": False}]},
            {"text": "What is 'SSL Stripping'?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "Downgrading a connection from HTTPS to HTTP.", "options": [{"text": "Downgrading HTTPS to HTTP", "is_correct": True}, {"text": "Removing SSL certificates", "is_correct": False}, {"text": "Stealing SSL keys physically", "is_correct": False}, {"text": "Breaking SSL encryption math", "is_correct": False}]},
            {"text": "What tool is famous for Wi-Fi MitM attacks (Pineapple)?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Medium", "skill_focus": "Tools", "explanation": "The WiFi Pineapple is a hardware tool for rogue APs.", "options": [{"text": "WiFi Pineapple", "is_correct": True}, {"text": "WiFi Banana", "is_correct": False}, {"text": "WiFi Apple", "is_correct": False}, {"text": "WiFi Orange", "is_correct": False}]},
            {"text": "What is a Rogue Access Point?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "An unauthorized Wi-Fi point set up to intercept traffic.", "options": [{"text": "Unauthorized Wi-Fi access point", "is_correct": True}, {"text": "A broken router", "is_correct": False}, {"text": "A hidden server", "is_correct": False}, {"text": "A restricted website", "is_correct": False}]},
            {"text": "What is Session Hijacking often a result of?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "If a session cookie is sent over unencrypted HTTP, MitM can steal it.", "options": [{"text": "Unencrypted Session Cookies", "is_correct": True}, {"text": "Strong passwords", "is_correct": False}, {"text": "Two-factor authentication", "is_correct": False}, {"text": "Encrypted hard drives", "is_correct": False}]},
            {"text": "What is DNS Spoofing?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Redirecting a domain name to a malicious IP address.", "options": [{"text": "Redirecting domain names to wrong IPs", "is_correct": True}, {"text": "Deleting domain names", "is_correct": False}, {"text": "Buying domain names", "is_correct": False}, {"text": "Encrypting DNS queries", "is_correct": False}]},
            {"text": "Which network layer does ARP Spoofing operate on?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Hard", "skill_focus": "Knowledge", "explanation": "Layer 2 (Data Link Layer) uses MAC addresses.", "options": [{"text": "Layer 2 (Data Link)", "is_correct": True}, {"text": "Layer 3 (Network)", "is_correct": False}, {"text": "Layer 7 (Application)", "is_correct": False}, {"text": "Layer 1 (Physical)", "is_correct": False}]},
            {"text": "What prevents ARP Spoofing on enterprise switches?", "type": "multiple_choice", "topic": "MitM", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Dynamic ARP Inspection (DAI) validates ARP packets.", "options": [{"text": "Dynamic ARP Inspection", "is_correct": True}, {"text": "Port Security", "is_correct": False}, {"text": "Firewall", "is_correct": False}, {"text": "VLANs", "is_correct": False}]},
        ])

        # --- 5. DoS / DDoS ---
        questions.extend([
            {"text": "What is the difference between DoS and DDoS?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "DDoS uses multiple distributed sources (botnet).", "options": [{"text": "DDoS uses multiple attack sources", "is_correct": True}, {"text": "DoS is faster", "is_correct": False}, {"text": "DDoS is only for banks", "is_correct": False}, {"text": "They are the same", "is_correct": False}]},
            {"text": "What does a SYN Flood attack exploit?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "It exploits the TCP 3-way handshake by leaving connections half-open.", "options": [{"text": "TCP 3-way Handshake", "is_correct": True}, {"text": "UDP protocols", "is_correct": False}, {"text": "HTTP headers", "is_correct": False}, {"text": "DNS queries", "is_correct": False}]},
            {"text": "What is a Botnet?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "A network of compromised computers controlled by an attacker.", "options": [{"text": "Network of compromised computers", "is_correct": True}, {"text": "A robot network for cleaning", "is_correct": False}, {"text": "A fast internet connection", "is_correct": False}, {"text": "A firewall software", "is_correct": False}]},
            {"text": "What is a 'Slowloris' attack?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "It keeps many connections open by sending HTTP headers very slowly.", "options": [{"text": "Low-bandwidth attack keeping connections open", "is_correct": True}, {"text": "High-bandwidth volume attack", "is_correct": False}, {"text": "Malware attack", "is_correct": False}, {"text": "Phishing attack", "is_correct": False}]},
            {"text": "What is an Amplification Attack?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Sending a small request that generates a large response (e.g., NTP/DNS).", "options": [{"text": "Small request causes large response", "is_correct": True}, {"text": "Making the virus louder", "is_correct": False}, {"text": "Increasing wifi signal", "is_correct": False}, {"text": "Stealing more data", "is_correct": False}]},
            {"text": "What is the 'Ping of Death'?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Medium", "skill_focus": "History", "explanation": "Sending malformed or oversized ping packets to crash a system.", "options": [{"text": "Malformed/Oversized ICMP packet", "is_correct": True}, {"text": "Too many pings", "is_correct": False}, {"text": "Pinging a dead server", "is_correct": False}, {"text": "A sound effect", "is_correct": False}]},
            {"text": "What service helps mitigate DDoS attacks?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Cloudflare (and similar CDNs) absorb traffic.", "options": [{"text": "CDN / Traffic Scrubbing (e.g., Cloudflare)", "is_correct": True}, {"text": "Antivirus", "is_correct": False}, {"text": "Password Manager", "is_correct": False}, {"text": "Disk Encryption", "is_correct": False}]},
            {"text": "What is a LOIC (Low Orbit Ion Cannon)?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Medium", "skill_focus": "Tools", "explanation": "A popular open-source network stress testing / DDoS tool.", "options": [{"text": "DDoS Tool", "is_correct": True}, {"text": "Space weapon", "is_correct": False}, {"text": "Satellite internet", "is_correct": False}, {"text": "Firewall brand", "is_correct": False}]},
            {"text": "What is the goal of a Ransom DDoS (RDoS)?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Easy", "skill_focus": "Motivation", "explanation": "Extortion: threatening DDoS unless money is paid.", "options": [{"text": "Extortion / Money", "is_correct": True}, {"text": "Stealing passwords", "is_correct": False}, {"text": "Spying", "is_correct": False}, {"text": "Testing speed", "is_correct": False}]},
            {"text": "Does a DDoS attack usually involve stealing data?", "type": "multiple_choice", "topic": "DoS/DDoS", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "No, it targets Availability, not Confidentiality.", "options": [{"text": "No, it targets Availability", "is_correct": True}, {"text": "Yes, always", "is_correct": False}, {"text": "Yes, primarily", "is_correct": False}, {"text": "It depends on the weather", "is_correct": False}]},
        ])

        # --- 6. Brute Force / Credential Stuffing ---
        questions.extend([
            {"text": "What is Credential Stuffing?", "type": "multiple_choice", "topic": "Credential Stuffing", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Using leaked username/password pairs on other sites.", "options": [{"text": "Using leaked credentials on other sites", "is_correct": True}, {"text": "Guessing random passwords", "is_correct": False}, {"text": "Stealing cookies", "is_correct": False}, {"text": "Creating fake accounts", "is_correct": False}]},
            {"text": "What is a Dictionary Attack?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "Using a list of common words/passwords.", "options": [{"text": "Using a wordlist of common passwords", "is_correct": True}, {"text": "Trying every combination (A-Z, 0-9)", "is_correct": False}, {"text": "Looking up words in a book", "is_correct": False}, {"text": "Attacking the dictionary file", "is_correct": False}]},
            {"text": "What is a Hybrid Attack?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Combining dictionary words with number/symbol variations.", "options": [{"text": "Dictionary words + variations", "is_correct": True}, {"text": "Physical and Digital attack", "is_correct": False}, {"text": "Windows and Linux attack", "is_correct": False}, {"text": "Fast and Slow attack", "is_correct": False}]},
            {"text": "What effectively stops simple Brute Force attacks?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "Account lockout after N failed attempts.", "options": [{"text": "Account Lockout Policies", "is_correct": True}, {"text": "Shorter passwords", "is_correct": False}, {"text": "Changing usernames", "is_correct": False}, {"text": "Hiding the login page", "is_correct": False}]},
            {"text": "What is the most effective defense against Credential Stuffing?", "type": "multiple_choice", "topic": "Credential Stuffing", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "MFA prevents login even if the password is known.", "options": [{"text": "Multi-Factor Authentication (MFA)", "is_correct": True}, {"text": "Complex passwords", "is_correct": False}, {"text": "Antivirus", "is_correct": False}, {"text": "Firewall", "is_correct": False}]},
            {"text": "What file is commonly used as a wordlist (rockyou)?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Medium", "skill_focus": "Tools", "explanation": "rockyou.txt is a famous leaked password list.", "options": [{"text": "rockyou.txt", "is_correct": True}, {"text": "passwords.doc", "is_correct": False}, {"text": "hack.exe", "is_correct": False}, {"text": "list.pdf", "is_correct": False}]},
            {"text": "What is 'Password Spraying'?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Trying one common password against MANY accounts to avoid lockout.", "options": [{"text": "One password against many accounts", "is_correct": True}, {"text": "Many passwords against one account", "is_correct": False}, {"text": "Emailing passwords", "is_correct": False}, {"text": "Resetting passwords", "is_correct": False}]},
            {"text": "What makes a Rainbow Table attack faster than Brute Force?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Hard", "skill_focus": "Theory", "explanation": "It uses precomputed hash chains to reverse hashes.", "options": [{"text": "Precomputed hash chains", "is_correct": True}, {"text": "Better GPU", "is_correct": False}, {"text": "Faster internet", "is_correct": False}, {"text": "More computers", "is_correct": False}]},
            {"text": "What mitigates Rainbow Table attacks?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Salting adds random data to the hash, invalidating precomputed tables.", "options": [{"text": "Salting passwords", "is_correct": True}, {"text": "Hashing twice", "is_correct": False}, {"text": "Using MD5", "is_correct": False}, {"text": "Keeping database offline", "is_correct": False}]},
            {"text": "Why is 'admin' / 'admin' a bad credential pair?", "type": "multiple_choice", "topic": "Brute Force", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "It is the default for many devices and the first thing guessed.", "options": [{"text": "Default / Easily guessed", "is_correct": True}, {"text": "Hard to remember", "is_correct": False}, {"text": "Too long", "is_correct": False}, {"text": "Cannot be typed", "is_correct": False}]},
        ])

        # --- 7. CSRF ---
        questions.extend([
            {"text": "What does CSRF stand for?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Cross-Site Request Forgery.", "options": [{"text": "Cross-Site Request Forgery", "is_correct": True}, {"text": "Common Server Request Fail", "is_correct": False}, {"text": "Client Side Router Fix", "is_correct": False}, {"text": "Cross System Root File", "is_correct": False}]},
            {"text": "What does a CSRF attack achieve?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Forces an authenticated user to perform an unwanted action.", "options": [{"text": "Forces user to perform unwanted action", "is_correct": True}, {"text": "Steals user password", "is_correct": False}, {"text": "Crashes the server", "is_correct": False}, {"text": "Intercepts Wi-Fi", "is_correct": False}]},
            {"text": "What is the standard defense against CSRF?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Anti-CSRF Tokens (Synchronizer Token Pattern).", "options": [{"text": "Anti-CSRF Tokens", "is_correct": True}, {"text": "Encryption", "is_correct": False}, {"text": "Complex Passwords", "is_correct": False}, {"text": "Hiding URLs", "is_correct": False}]},
            {"text": "Which cookie attribute helps prevent CSRF?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "SameSite=Strict/Lax prevents sending cookies on cross-site requests.", "options": [{"text": "SameSite", "is_correct": True}, {"text": "HttpOnly", "is_correct": False}, {"text": "Secure", "is_correct": False}, {"text": "Expires", "is_correct": False}]},
            {"text": "Does CSRF work if the user is NOT logged in?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "No, it relies on the user's active session.", "options": [{"text": "No", "is_correct": True}, {"text": "Yes", "is_correct": False}, {"text": "Only on mobile", "is_correct": False}, {"text": "Only on Wi-Fi", "is_correct": False}]},
            {"text": "Is reading data usually possible with standard CSRF?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Hard", "skill_focus": "Theory", "explanation": "No, CSRF is 'blind'. It sends state-changing requests but attacker can't see response (usually).", "options": [{"text": "No, it's a state-changing attack", "is_correct": True}, {"text": "Yes, always", "is_correct": False}, {"text": "Only JSON data", "is_correct": False}, {"text": "Only Images", "is_correct": False}]},
            {"text": "Which HTTP method is most dangerous for CSRF if misconfigured?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "GET requests should not change state; if they do, CSRF is trivial (via image tags).", "options": [{"text": "GET (if used for state changes)", "is_correct": True}, {"text": "OPTIONS", "is_correct": False}, {"text": "HEAD", "is_correct": False}, {"text": "TRACE", "is_correct": False}]},
            {"text": "What is 'Login CSRF'?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "Logging a victim into the attacker's account to track their activity.", "options": [{"text": "Logging victim into attacker's account", "is_correct": True}, {"text": "Stealing login credentials", "is_correct": False}, {"text": "Deleting login page", "is_correct": False}, {"text": "Brute forcing login", "is_correct": False}]},
            {"text": "Why doesn't the Same Origin Policy (SOP) stop CSRF?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Hard", "skill_focus": "Theory", "explanation": "SOP prevents reading responses, not sending requests.", "options": [{"text": "SOP prevents reading, not sending", "is_correct": True}, {"text": "SOP is deprecated", "is_correct": False}, {"text": "CSRF bypasses SOP automatically", "is_correct": False}, {"text": "SOP only works for images", "is_correct": False}]},
            {"text": "Can CAPTCHA prevent CSRF?", "type": "multiple_choice", "topic": "CSRF", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Yes, because the attacker cannot solve the CAPTCHA programmatically.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only google captcha", "is_correct": False}, {"text": "Only on Tuesdays", "is_correct": False}]},
        ])

        # --- 8. SSRF ---
        questions.extend([
            {"text": "What does SSRF stand for?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Server-Side Request Forgery.", "options": [{"text": "Server-Side Request Forgery", "is_correct": True}, {"text": "Secure Socket Remote File", "is_correct": False}, {"text": "System Side Root Fix", "is_correct": False}, {"text": "Site Security Request Form", "is_correct": False}]},
            {"text": "Who performs the request in an SSRF attack?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "The vulnerable server makes the request.", "options": [{"text": "The Web Server", "is_correct": True}, {"text": "The User's Browser", "is_correct": False}, {"text": "The Hacker's Laptop directly", "is_correct": False}, {"text": "The ISP", "is_correct": False}]},
            {"text": "What is a common target for SSRF in cloud environments?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Instance Metadata Services (e.g., 169.254.169.254) contain keys.", "options": [{"text": "Metadata Services (169.254.169.254)", "is_correct": True}, {"text": "YouTube", "is_correct": False}, {"text": "Facebook", "is_correct": False}, {"text": "Public DNS", "is_correct": False}]},
            {"text": "Can SSRF be used to scan internal networks?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Yes, the server can reach internal IPs that the outsider cannot.", "options": [{"text": "Yes, port scanning internal IPs", "is_correct": True}, {"text": "No, firewalls stop it", "is_correct": False}, {"text": "Only external IPs", "is_correct": False}, {"text": "Only if using FTP", "is_correct": False}]},
            {"text": "What URL scheme is often used in SSRF to read local files?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "file:///etc/passwd", "options": [{"text": "file://", "is_correct": True}, {"text": "http://", "is_correct": False}, {"text": "mailto:", "is_correct": False}, {"text": "tel:", "is_correct": False}]},
            {"text": "What is Blind SSRF?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Hard", "skill_focus": "Theory", "explanation": "The attacker doesn't see the response, but can observe timing or side effects.", "options": [{"text": "No response returned to attacker", "is_correct": True}, {"text": "Attacker is blindfolded", "is_correct": False}, {"text": "Server is offline", "is_correct": False}, {"text": "Full data is returned", "is_correct": False}]},
            {"text": "How do you mitigate SSRF?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Allowlisting domains and validating user input.", "options": [{"text": "Input Validation & Allowlisting", "is_correct": True}, {"text": "Disabling JS", "is_correct": False}, {"text": "Using HTTPS", "is_correct": False}, {"text": "Using Cookies", "is_correct": False}]},
            {"text": "Which vulnerability allows an attacker to make the server attack other servers?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "SSRF makes the server a proxy for attacks.", "options": [{"text": "SSRF", "is_correct": True}, {"text": "XSS", "is_correct": False}, {"text": "CSRF", "is_correct": False}, {"text": "SQLi", "is_correct": False}]},
            {"text": "Can SSRF bypass local firewalls?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Yes, because the request originates from the trusted server inside the firewall.", "options": [{"text": "Yes, request is from trusted internal source", "is_correct": True}, {"text": "No, firewalls block everything", "is_correct": False}, {"text": "Only on Windows", "is_correct": False}, {"text": "Only on Linux", "is_correct": False}]},
            {"text": "What is 'DNS Rebinding' in the context of SSRF?", "type": "multiple_choice", "topic": "SSRF", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "Changing DNS resolution from a safe IP to a malicious/internal IP during the check-time/use-time gap.", "options": [{"text": "Bypassing IP checks via DNS changes", "is_correct": True}, {"text": "Rebooting DNS server", "is_correct": False}, {"text": "Binding two DNS servers", "is_correct": False}, {"text": "Encrypting DNS", "is_correct": False}]},
        ])

        # --- 9. Ransomware ---
        questions.extend([
            {"text": "What does Ransomware do?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Encrypts files and demands payment.", "options": [{"text": "Encrypts files and demands payment", "is_correct": True}, {"text": "Deletes files silently", "is_correct": False}, {"text": "Steals internet bandwidth", "is_correct": False}, {"text": "Mines bitcoin only", "is_correct": False}]},
            {"text": "What is the best recovery method for Ransomware?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "Offline backups allow restoration without paying.", "options": [{"text": "Offline/Offline Backups", "is_correct": True}, {"text": "Paying the ransom", "is_correct": False}, {"text": "Restarting the PC", "is_correct": False}, {"text": "Calling the police", "is_correct": False}]},
            {"text": "What is 'Double Extortion' ransomware?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Encrypting files AND threatening to leak stolen data.", "options": [{"text": "Encryption + Data Leak Threat", "is_correct": True}, {"text": "Asking for double money", "is_correct": False}, {"text": "Infecting two computers", "is_correct": False}, {"text": "Encrypting twice", "is_correct": False}]},
            {"text": "What cryptocurrency is most commonly requested in ransomware?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Bitcoin (or Monero) for anonymity.", "options": [{"text": "Bitcoin/Monero", "is_correct": True}, {"text": "Credit Card", "is_correct": False}, {"text": "Paypal", "is_correct": False}, {"text": "Bank Transfer", "is_correct": False}]},
            {"text": "WannaCry ransomware exploited which protocol?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Medium", "skill_focus": "History", "explanation": "SMB (Server Message Block) via EternalBlue exploit.", "options": [{"text": "SMB (Server Message Block)", "is_correct": True}, {"text": "HTTP", "is_correct": False}, {"text": "FTP", "is_correct": False}, {"text": "SSH", "is_correct": False}]},
            {"text": "How is ransomware often delivered?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "Phishing emails are the top vector.", "options": [{"text": "Phishing Emails", "is_correct": True}, {"text": "Magic", "is_correct": False}, {"text": "Hardware failure", "is_correct": False}, {"text": "Power surge", "is_correct": False}]},
            {"text": "What is RaaS?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Ransomware as a Service (affiliate model).", "options": [{"text": "Ransomware as a Service", "is_correct": True}, {"text": "Real and active Security", "is_correct": False}, {"text": "Root as a Service", "is_correct": False}, {"text": "Recovery as a Service", "is_correct": False}]},
            {"text": "Should you pay the ransom?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Easy", "skill_focus": "Ethics/Policy", "explanation": "FBI advises no; it encourages attacks and doesn't guarantee data return.", "options": [{"text": "Generally No (No guarantee)", "is_correct": True}, {"text": "Yes, always", "is_correct": False}, {"text": "Only if it's cheap", "is_correct": False}, {"text": "Only on weekends", "is_correct": False}]},
            {"text": "What type of encryption does ransomware usually use?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Hard", "skill_focus": "Crypto", "explanation": "Asymmetric (Public/Private key) so the victim can't decrypt without the private key held by attacker.", "options": [{"text": "Asymmetric (Public/Private Key)", "is_correct": True}, {"text": "ROT13", "is_correct": False}, {"text": "Base64", "is_correct": False}, {"text": "XOR", "is_correct": False}]},
            {"text": "What is a 'Kill Switch' in ransomware context?", "type": "multiple_choice", "topic": "Ransomware", "difficulty": "Medium", "skill_focus": "History", "explanation": "A mechanism (like a domain check) that stops the malware spreading (famous in WannaCry).", "options": [{"text": "Mechanism to stop execution", "is_correct": True}, {"text": "Button to delete PC", "is_correct": False}, {"text": "Deleting the virus", "is_correct": False}, {"text": "Turning off power", "is_correct": False}]},
        ])

        # --- 10. Buffer Overflow ---
        questions.extend([
            {"text": "What causes a Buffer Overflow?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "Writing more data to a buffer than it can hold.", "options": [{"text": "Writing past memory boundaries", "is_correct": True}, {"text": "Hard drive full", "is_correct": False}, {"text": "Too many files", "is_correct": False}, {"text": "Slow CPU", "is_correct": False}]},
            {"text": "Which languages are most susceptible to Buffer Overflows?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "C and C++ do not have built-in memory safety.", "options": [{"text": "C / C++", "is_correct": True}, {"text": "Python", "is_correct": False}, {"text": "Java", "is_correct": False}, {"text": "JavaScript", "is_correct": False}]},
            {"text": "What is the 'Stack' in memory?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Memory region for local variables and function control flow.", "options": [{"text": "Region for local variables/control flow", "is_correct": True}, {"text": "Long term storage", "is_correct": False}, {"text": "Hard drive space", "is_correct": False}, {"text": "Graphics memory", "is_correct": False}]},
            {"text": "What is the 'Heap'?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Dynamic memory allocation.", "options": [{"text": "Dynamic memory area", "is_correct": True}, {"text": "Static memory area", "is_correct": False}, {"text": "Code area", "is_correct": False}, {"text": "Kernel area", "is_correct": False}]},
            {"text": "What does a Buffer Overflow often allow an attacker to overwrite?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "The Return Address (EIP/RIP) controls what code executes next.", "options": [{"text": "Return Address (EIP/RIP)", "is_correct": True}, {"text": "Screen resolution", "is_correct": False}, {"text": "Keyboard layout", "is_correct": False}, {"text": "Mouse speed", "is_correct": False}]},
            {"text": "What is 'Shellcode'?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Small piece of code used as the payload (usually spawns a shell).", "options": [{"text": "Payload code to spawn a shell", "is_correct": True}, {"text": "Code to format drive", "is_correct": False}, {"text": "Code to change colors", "is_correct": False}, {"text": "Code to zip files", "is_correct": False}]},
            {"text": "What is ASLR?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Address Space Layout Randomization moves memory locations around.", "options": [{"text": "Address Space Layout Randomization", "is_correct": True}, {"text": "Anti-Shell Logic Rule", "is_correct": False}, {"text": "Advanced Security Level Rating", "is_correct": False}, {"text": "Auto System Lock Routine", "is_correct": False}]},
            {"text": "What is a Canary (Stack Cookie)?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "A value placed on the stack to detect overflows before the return address is reached.", "options": [{"text": "Value to detect stack corruption", "is_correct": True}, {"text": "A bird", "is_correct": False}, {"text": "A password", "is_correct": False}, {"text": "A firewall rule", "is_correct": False}]},
            {"text": "What is a NOP Sled?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Sequence of No-Operation instructions to slide execution into shellcode.", "options": [{"text": "Sequence of No-Operation instructions", "is_correct": True}, {"text": "A hacking tool", "is_correct": False}, {"text": "A password cracker", "is_correct": False}, {"text": "A network scanner", "is_correct": False}]},
            {"text": "What is DEP / NX?", "type": "multiple_choice", "topic": "Buffer Overflow", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Data Execution Prevention / No-Execute makes the stack non-executable.", "options": [{"text": "Prevents code execution in data segments", "is_correct": True}, {"text": "Prevents data deletion", "is_correct": False}, {"text": "Prevents encryption", "is_correct": False}, {"text": "Prevents networking", "is_correct": False}]},
        ])

        # --- 11. XXE (XML External Entity) ---
        questions.extend([
            {"text": "What does XXE stand for?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "XML External Entity.", "options": [{"text": "XML External Entity", "is_correct": True}, {"text": "X-Ray External Entry", "is_correct": False}, {"text": "XML Extra Encryption", "is_correct": False}, {"text": "Xenon Extra Entry", "is_correct": False}]},
            {"text": "XXE attacks target applications that parse what format?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "XML.", "options": [{"text": "XML", "is_correct": True}, {"text": "JSON", "is_correct": False}, {"text": "YAML", "is_correct": False}, {"text": "CSV", "is_correct": False}]},
            {"text": "What is a common impact of XXE?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Local File Disclosure (reading /etc/passwd).", "options": [{"text": "Reading local files", "is_correct": True}, {"text": "Formatting C drive", "is_correct": False}, {"text": "Changing CSS", "is_correct": False}, {"text": "Playing audio", "is_correct": False}]},
            {"text": "What entity definition is usually used in XXE?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "<!DOCTYPE foo [ <!ENTITY xxe SYSTEM 'file:///etc/passwd'> ]>", "options": [{"text": "SYSTEM entity", "is_correct": True}, {"text": "LOCAL entity", "is_correct": False}, {"text": "GLOBAL entity", "is_correct": False}, {"text": "PRIVATE entity", "is_correct": False}]},
            {"text": "How do you prevent XXE?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Disable DTDs (Document Type Definitions) and external entities.", "options": [{"text": "Disable DTDs / External Entities", "is_correct": True}, {"text": "Use Firewall", "is_correct": False}, {"text": "Use HTTPS", "is_correct": False}, {"text": "Reboot Server", "is_correct": False}]},
            {"text": "Can XXE lead to SSRF?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Yes, by making the XML parser fetch a URL.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only via Bluetooth", "is_correct": False}, {"text": "Only on Mac", "is_correct": False}]},
            {"text": "What is a 'Billion Laughs' attack?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "XML Bomb (DoS) using recursive entity expansion.", "options": [{"text": "XML Bomb / DoS", "is_correct": True}, {"text": "Funny Virus", "is_correct": False}, {"text": "Audio attack", "is_correct": False}, {"text": "Video attack", "is_correct": False}]},
            {"text": "Is JSON vulnerable to XXE?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "No, JSON does not have entities like XML.", "options": [{"text": "No", "is_correct": True}, {"text": "Yes", "is_correct": False}, {"text": "Sometimes", "is_correct": False}, {"text": "If converted to XML", "is_correct": False}]},
            {"text": "What does DTD stand for?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Document Type Definition.", "options": [{"text": "Document Type Definition", "is_correct": True}, {"text": "Data Type Definition", "is_correct": False}, {"text": "Domain Transfer Data", "is_correct": False}, {"text": "Direct Text Data", "is_correct": False}]},
            {"text": "Which XML feature is the root cause of XXE?", "type": "multiple_choice", "topic": "XXE", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "External entities.", "options": [{"text": "External Entities", "is_correct": True}, {"text": "Tags", "is_correct": False}, {"text": "Attributes", "is_correct": False}, {"text": "Comments", "is_correct": False}]},
        ])

        # --- 12. Directory / Path Traversal ---
        questions.extend([
            {"text": "What character sequence is used for Directory Traversal?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "../ moves up a directory.", "options": [{"text": "../ (Dot Dot Slash)", "is_correct": True}, {"text": "||", "is_correct": False}, {"text": "&&", "is_correct": False}, {"text": "##", "is_correct": False}]},
            {"text": "What is the goal of Path Traversal?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "Access files outside the web root.", "options": [{"text": "Access files outside web root", "is_correct": True}, {"text": "Delete files", "is_correct": False}, {"text": "Upload files", "is_correct": False}, {"text": "Execute files", "is_correct": False}]},
            {"text": "If you see 'image=../../etc/passwd', what attack is this?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Easy", "skill_focus": "Recognition", "explanation": "Path Traversal.", "options": [{"text": "Path Traversal", "is_correct": True}, {"text": "SQL Injection", "is_correct": False}, {"text": "XSS", "is_correct": False}, {"text": "CSRF", "is_correct": False}]},
            {"text": "How do you prevent Path Traversal?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Validate input against a whitelist of filenames and avoid direct file API access.", "options": [{"text": "Input validation and canonicalization", "is_correct": True}, {"text": "Disable images", "is_correct": False}, {"text": "Use CSS", "is_correct": False}, {"text": "Shorten URLs", "is_correct": False}]},
            {"text": "What is 'Canonicalization'?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Converting data to its simplest, standard form (resolving ../).", "options": [{"text": "Resolving paths to standard form", "is_correct": True}, {"text": "Zipping files", "is_correct": False}, {"text": "Encrypting files", "is_correct": False}, {"text": "Deleting logs", "is_correct": False}]},
            {"text": "What is the null byte (%00) trick used for?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "In older systems (C-based), it terminates the string, bypassing extension checks (.php%00.jpg).", "options": [{"text": "Terminating strings early", "is_correct": True}, {"text": "Making files empty", "is_correct": False}, {"text": "Adding zero value", "is_correct": False}, {"text": "Nothing", "is_correct": False}]},
            {"text": "Can Path Traversal lead to Remote Code Execution?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Yes, if you can upload a file and then traverse to execute it, or read config files with passwords.", "options": [{"text": "Yes, in some scenarios", "is_correct": True}, {"text": "No, never", "is_correct": False}, {"text": "Only on Tuesdays", "is_correct": False}, {"text": "Only via Email", "is_correct": False}]},
            {"text": "What OS uses backslashes '\\' often causing traversal confusion?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Windows.", "options": [{"text": "Windows", "is_correct": True}, {"text": "Linux", "is_correct": False}, {"text": "Mac", "is_correct": False}, {"text": "Android", "is_correct": False}]},
            {"text": "What is 'Dot Dot Pwn'?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Medium", "skill_focus": "Tools", "explanation": "A fuzzer for directory traversal.", "options": [{"text": "Traversal Fuzzer Tool", "is_correct": True}, {"text": "A game", "is_correct": False}, {"text": "A virus", "is_correct": False}, {"text": "A firewall", "is_correct": False}]},
            {"text": "Is chroot() a defense against traversal?", "type": "multiple_choice", "topic": "Path Traversal", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Yes, it jails the process to a specific directory.", "options": [{"text": "Yes, it jails the process", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "It makes it worse", "is_correct": False}, {"text": "Only for root users", "is_correct": False}]},
        ])

        # --- 13. Insecure Deserialization ---
        questions.extend([
            {"text": "What is Serialization?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "Converting an object into a data stream (e.g., JSON, XML, Binary).", "options": [{"text": "Converting object to data stream", "is_correct": True}, {"text": "Encrypting data", "is_correct": False}, {"text": "Deleting data", "is_correct": False}, {"text": "Sorting data", "is_correct": False}]},
            {"text": "What is Deserialization?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "Converting data stream back to an object.", "options": [{"text": "Converting stream back to object", "is_correct": True}, {"text": "Decrypting data", "is_correct": False}, {"text": "Creating data", "is_correct": False}, {"text": "Hiding data", "is_correct": False}]},
            {"text": "What is the danger of Insecure Deserialization?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Remote Code Execution (RCE) via object injection.", "options": [{"text": "Remote Code Execution (RCE)", "is_correct": True}, {"text": "CSS injection", "is_correct": False}, {"text": "Slow internet", "is_correct": False}, {"text": "Spam emails", "is_correct": False}]},
            {"text": "Which Java tool is famous for generating deserialization payloads?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Hard", "skill_focus": "Tools", "explanation": "ysoserial.", "options": [{"text": "ysoserial", "is_correct": True}, {"text": "javahack", "is_correct": False}, {"text": "serialkiller", "is_correct": False}, {"text": "objectmapper", "is_correct": False}]},
            {"text": "In Python, which library is known for deserialization vulnerabilities?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Pickle.", "options": [{"text": "Pickle", "is_correct": True}, {"text": "Pandas", "is_correct": False}, {"text": "NumPy", "is_correct": False}, {"text": "Requests", "is_correct": False}]},
            {"text": "What is a 'Gadget Chain'?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Hard", "skill_focus": "Theory", "explanation": "A sequence of existing code snippets executed during deserialization to achieve RCE.", "options": [{"text": "Sequence of code chunks for RCE", "is_correct": True}, {"text": "A physical tool", "is_correct": False}, {"text": "A blockchain", "is_correct": False}, {"text": "A password list", "is_correct": False}]},
            {"text": "How do you prevent Deserialization attacks?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Don't deserialize untrusted data; use simple formats like JSON without logic.", "options": [{"text": "Avoid deserializing untrusted data", "is_correct": True}, {"text": "Use shorter variables", "is_correct": False}, {"text": "Use more memory", "is_correct": False}, {"text": "Restart often", "is_correct": False}]},
            {"text": "Is PHP `unserialize()` vulnerable?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Yes, if input is user-controlled.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only in PHP 4", "is_correct": False}, {"text": "Only on Linux", "is_correct": False}]},
            {"text": "What magic method in PHP is often a target?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Hard", "skill_focus": "Knowledge", "explanation": "__destruct() or __wakeup().", "options": [{"text": "__destruct()", "is_correct": True}, {"text": "__init()", "is_correct": False}, {"text": "__main()", "is_correct": False}, {"text": "__print()", "is_correct": False}]},
            {"text": "Are cookies a vector for deserialization attacks?", "type": "multiple_choice", "topic": "Deserialization", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Yes, if the cookie contains a serialized object.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only session IDs", "is_correct": False}, {"text": "Cookies are text only", "is_correct": False}]},
        ])

        # --- 14. Session Hijacking ---
        questions.extend([
            {"text": "What is Session Hijacking?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Taking over a user's active session.", "options": [{"text": "Taking over active session", "is_correct": True}, {"text": "Stealing a laptop", "is_correct": False}, {"text": "Crashing the server", "is_correct": False}, {"text": "Phishing password", "is_correct": False}]},
            {"text": "What is the most common token used to track sessions?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Session ID (Cookie).", "options": [{"text": "Session ID Cookie", "is_correct": True}, {"text": "IP Address", "is_correct": False}, {"text": "MAC Address", "is_correct": False}, {"text": "Username", "is_correct": False}]},
            {"text": "What is 'Session Fixation'?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Attacker sets the user's session ID before they log in.", "options": [{"text": "Attacker sets Session ID beforehand", "is_correct": True}, {"text": "Fixing broken sessions", "is_correct": False}, {"text": "Deleting sessions", "is_correct": False}, {"text": "Locking sessions", "is_correct": False}]},
            {"text": "What defense prevents Session Hijacking via XSS?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "HttpOnly flag prevents JS reading cookies.", "options": [{"text": "HttpOnly flag", "is_correct": True}, {"text": "CSS", "is_correct": False}, {"text": "HTML5", "is_correct": False}, {"text": "Flash", "is_correct": False}]},
            {"text": "What should happen to the Session ID after login?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "It should be regenerated to prevent Fixation.", "options": [{"text": "Regenerated", "is_correct": True}, {"text": "Kept same", "is_correct": False}, {"text": "Deleted", "is_correct": False}, {"text": "Printed", "is_correct": False}]},
            {"text": "Predictable Session IDs allow what?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "Guessing valid sessions of other users.", "options": [{"text": "Guessing other users' sessions", "is_correct": True}, {"text": "Faster login", "is_correct": False}, {"text": "Better UI", "is_correct": False}, {"text": "Less bandwidth", "is_correct": False}]},
            {"text": "What protocol protects Session IDs in transit?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "TLS (HTTPS).", "options": [{"text": "TLS/HTTPS", "is_correct": True}, {"text": "HTTP", "is_correct": False}, {"text": "FTP", "is_correct": False}, {"text": "Telnet", "is_correct": False}]},
            {"text": "What is 'Session Side-Jacking'?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Sniffing unencrypted cookies on Wi-Fi.", "options": [{"text": "Sniffing cookies on Wi-Fi", "is_correct": True}, {"text": "Stealing laptops", "is_correct": False}, {"text": "Breaking into servers", "is_correct": False}, {"text": "Phishing", "is_correct": False}]},
            {"text": "How long should a session timeout be?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "Short enough to minimize risk, long enough for usability.", "options": [{"text": "Short (e.g., 15-30 mins inactivity)", "is_correct": True}, {"text": "Infinite", "is_correct": False}, {"text": "1 year", "is_correct": False}, {"text": "1 second", "is_correct": False}]},
            {"text": "Can JWTs (JSON Web Tokens) be hijacked?", "type": "multiple_choice", "topic": "Session Hijacking", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Yes, if the token is stolen, it can be used until expiry.", "options": [{"text": "Yes, they are bearer tokens", "is_correct": True}, {"text": "No, they are secure", "is_correct": False}, {"text": "Only if signed", "is_correct": False}, {"text": "Only if encrypted", "is_correct": False}]},
        ])

        # --- 15. Command Injection ---
        questions.extend([
            {"text": "What is OS Command Injection?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "Executing system commands on the server via input.", "options": [{"text": "Executing system commands via input", "is_correct": True}, {"text": "Injecting SQL", "is_correct": False}, {"text": "Injecting CSS", "is_correct": False}, {"text": "Opening a command prompt on client", "is_correct": False}]},
            {"text": "Which character separates commands in Linux (e.g., cat file; ls)?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "; (Semicolon) allows chaining commands.", "options": [{"text": "; (Semicolon)", "is_correct": True}, {"text": ": (Colon)", "is_correct": False}, {"text": ". (Dot)", "is_correct": False}, {"text": "_ (Underscore)", "is_correct": False}]},
            {"text": "What does the pipe operator '|' do?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Passes output of one command to another.", "options": [{"text": "Pipes output to next command", "is_correct": True}, {"text": "Stops command", "is_correct": False}, {"text": "Deletes command", "is_correct": False}, {"text": "Nothing", "is_correct": False}]},
            {"text": "In Python, which function is dangerous if inputs aren't sanitized?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "os.system() or subprocess.call(shell=True).", "options": [{"text": "os.system()", "is_correct": True}, {"text": "print()", "is_correct": False}, {"text": "len()", "is_correct": False}, {"text": "math.sqrt()", "is_correct": False}]},
            {"text": "What is the best defense against Command Injection?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Avoid calling system commands; use language APIs.", "options": [{"text": "Use API libraries instead of shell commands", "is_correct": True}, {"text": "Use Firewalls", "is_correct": False}, {"text": "Use Antivirus", "is_correct": False}, {"text": "Hide the code", "is_correct": False}]},
            {"text": "What command helps check current user identity?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "whoami", "options": [{"text": "whoami", "is_correct": True}, {"text": "whereami", "is_correct": False}, {"text": "whatisthis", "is_correct": False}, {"text": "hello", "is_correct": False}]},
            {"text": "What is 'Blind' Command Injection?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Hard", "skill_focus": "Theory", "explanation": "No output is returned; attacker uses time delays (ping/sleep).", "options": [{"text": "No output returned, uses time delays", "is_correct": True}, {"text": "Output is encrypted", "is_correct": False}, {"text": "Screen turns black", "is_correct": False}, {"text": "Keyboard stops working", "is_correct": False}]},
            {"text": "Which character represents a variable in bash?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "$", "options": [{"text": "$", "is_correct": True}, {"text": "#", "is_correct": False}, {"text": "%", "is_correct": False}, {"text": "&", "is_correct": False}]},
            {"text": "Why is '&&' dangerous in inputs?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "It executes the second command if the first succeeds.", "options": [{"text": "Executes next command if previous succeeds", "is_correct": True}, {"text": "It means AND logic", "is_correct": False}, {"text": "It comments out code", "is_correct": False}, {"text": "It escapes characters", "is_correct": False}]},
            {"text": "Does 'escapeshellarg()' in PHP make it safe?", "type": "multiple_choice", "topic": "Command Injection", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "It helps by adding quotes, but avoiding shell execution is better.", "options": [{"text": "It adds quotes to make it safer", "is_correct": True}, {"text": "It executes the command", "is_correct": False}, {"text": "It deletes the command", "is_correct": False}, {"text": "It does nothing", "is_correct": False}]},
        ])

        # --- 16. Zero-Day Exploits ---
        questions.extend([
            {"text": "What is a Zero-Day vulnerability?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "A vulnerability known to attackers but not the vendor (0 days to patch).", "options": [{"text": "Unknown to vendor, no patch exists", "is_correct": True}, {"text": "A virus that lasts 0 days", "is_correct": False}, {"text": "Old vulnerability", "is_correct": False}, {"text": "Fake vulnerability", "is_correct": False}]},
            {"text": "What is a Zero-Day Exploit?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Code that takes advantage of a Zero-Day vulnerability.", "options": [{"text": "Code attacking a Zero-Day", "is_correct": True}, {"text": "A patch", "is_correct": False}, {"text": "A scanner", "is_correct": False}, {"text": "A firewall", "is_correct": False}]},
            {"text": "Who typically buys Zero-Days?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Medium", "skill_focus": "Context", "explanation": "Governments, criminals, and security brokers (like Zerodium).", "options": [{"text": "Governments / Criminals / Brokers", "is_correct": True}, {"text": "Regular users", "is_correct": False}, {"text": "Students", "is_correct": False}, {"text": "Libraries", "is_correct": False}]},
            {"text": "What is 'Responsible Disclosure'?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Medium", "skill_focus": "Ethics", "explanation": "Telling the vendor privately so they can patch it before public release.", "options": [{"text": "Reporting to vendor privately first", "is_correct": True}, {"text": "Posting on Twitter immediately", "is_correct": False}, {"text": "Selling it on Dark Web", "is_correct": False}, {"text": "Keeping it secret forever", "is_correct": False}]},
            {"text": "What is a Bug Bounty Program?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Easy", "skill_focus": "Context", "explanation": "Companies paying hackers for reporting bugs.", "options": [{"text": "Paying for reported bugs", "is_correct": True}, {"text": "Hunting insects", "is_correct": False}, {"text": "Buying software", "is_correct": False}, {"text": "Hiring support", "is_correct": False}]},
            {"text": "Stuxnet used how many Zero-Days?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Hard", "skill_focus": "History", "explanation": "Stuxnet famously used 4 Zero-Days.", "options": [{"text": "4", "is_correct": True}, {"text": "1", "is_correct": False}, {"text": "0", "is_correct": False}, {"text": "100", "is_correct": False}]},
            {"text": "How do you defend against Zero-Days?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Defense in Depth (layering security) since you can't patch what you don't know.", "options": [{"text": "Defense in Depth / Behavioral Analysis", "is_correct": True}, {"text": "Update windows", "is_correct": False}, {"text": "Use weak passwords", "is_correct": False}, {"text": "Turn off internet", "is_correct": False}]},
            {"text": "What is 'Heuristic Analysis'?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Hard", "skill_focus": "Defense", "explanation": "Detecting malware by behavior/patterns rather than signatures.", "options": [{"text": "Detecting by behavior/patterns", "is_correct": True}, {"text": "Detecting by exact match", "is_correct": False}, {"text": "Manual reading", "is_correct": False}, {"text": "Guessing", "is_correct": False}]},
            {"text": "What does CVE stand for?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Common Vulnerabilities and Exposures.", "options": [{"text": "Common Vulnerabilities and Exposures", "is_correct": True}, {"text": "Computer Virus Entry", "is_correct": False}, {"text": "Critical Value Error", "is_correct": False}, {"text": "Central Virus Engine", "is_correct": False}]},
            {"text": "Once a patch is released, is it still a Zero-Day?", "type": "multiple_choice", "topic": "Zero-Day", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "No, it becomes a known vulnerability (N-Day).", "options": [{"text": "No", "is_correct": True}, {"text": "Yes", "is_correct": False}, {"text": "Forever", "is_correct": False}, {"text": "Maybe", "is_correct": False}]},
        ])

        # --- 17. DNS Spoofing / Poisoning ---
        questions.extend([
            {"text": "What is DNS Cache Poisoning?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Injecting fake records into a DNS resolver's cache.", "options": [{"text": "Injecting fake records into cache", "is_correct": True}, {"text": "Deleting DNS server", "is_correct": False}, {"text": "Stealing DNS server", "is_correct": False}, {"text": "Encrypting DNS", "is_correct": False}]},
            {"text": "What is the result of DNS Spoofing?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "Users typing 'google.com' go to a malicious site.", "options": [{"text": "Redirecting users to wrong sites", "is_correct": True}, {"text": "Faster internet", "is_correct": False}, {"text": "Free internet", "is_correct": False}, {"text": "Blue screen", "is_correct": False}]},
            {"text": "What security extension prevents DNS Spoofing?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "DNSSEC signs records cryptographically.", "options": [{"text": "DNSSEC", "is_correct": True}, {"text": "HTTPS", "is_correct": False}, {"text": "SSL", "is_correct": False}, {"text": "WEP", "is_correct": False}]},
            {"text": "What file on a local computer overrides DNS?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "The 'hosts' file.", "options": [{"text": "hosts file", "is_correct": True}, {"text": "config.sys", "is_correct": False}, {"text": "registry", "is_correct": False}, {"text": "autoexec.bat", "is_correct": False}]},
            {"text": "What is 'Pharming'?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "Redirecting traffic to a fake site via DNS poisoning (without user clicking links).", "options": [{"text": "Redirecting traffic via DNS manipulation", "is_correct": True}, {"text": "Farming gold", "is_correct": False}, {"text": "Planting viruses", "is_correct": False}, {"text": "Harvesting emails", "is_correct": False}]},
            {"text": "What UDP port does DNS use?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "53.", "options": [{"text": "53", "is_correct": True}, {"text": "80", "is_correct": False}, {"text": "443", "is_correct": False}, {"text": "21", "is_correct": False}]},
            {"text": "Why is UDP used for DNS (making it easier to spoof)?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "UDP is connectionless and faster, but easier to forge packets.", "options": [{"text": "Connectionless / Faster", "is_correct": True}, {"text": "More secure", "is_correct": False}, {"text": "Encrypted", "is_correct": False}, {"text": "Newer", "is_correct": False}]},
            {"text": "What is the Kaminsky Vulnerability?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Hard", "skill_focus": "History", "explanation": "A famous flaw allowing reliable DNS cache poisoning via transaction ID guessing.", "options": [{"text": "Flaw allowing reliable cache poisoning", "is_correct": True}, {"text": "A virus", "is_correct": False}, {"text": "A firewall hole", "is_correct": False}, {"text": "A browser bug", "is_correct": False}]},
            {"text": "DoVPNs help against local DNS Spoofing?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Yes, they encrypt traffic to a trusted DNS server, bypassing local spoofing.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Makes it worse", "is_correct": False}, {"text": "Only in China", "is_correct": False}]},
            {"text": "What is DNS over HTTPS (DoH)?", "type": "multiple_choice", "topic": "DNS Spoofing", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Encrypting DNS queries inside HTTPS traffic.", "options": [{"text": "Encrypted DNS via HTTPS", "is_correct": True}, {"text": "Websites over DNS", "is_correct": False}, {"text": "Fast DNS", "is_correct": False}, {"text": "Illegal DNS", "is_correct": False}]},
        ])

        # --- 18. Trojan Horses ---
        questions.extend([
            {"text": "What is a Trojan Horse?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Malware disguised as legitimate software.", "options": [{"text": "Malware disguised as legitimate software", "is_correct": True}, {"text": "Self-replicating worm", "is_correct": False}, {"text": "A wooden horse", "is_correct": False}, {"text": "A hardware bug", "is_correct": False}]},
            {"text": "Do Trojans self-replicate like worms?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "No, they require user interaction (execution) to spread.", "options": [{"text": "No", "is_correct": True}, {"text": "Yes", "is_correct": False}, {"text": "Sometimes", "is_correct": False}, {"text": "Only on Sundays", "is_correct": False}]},
            {"text": "What is a Remote Access Trojan (RAT)?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Gives attacker full remote control of the victim PC.", "options": [{"text": "Gives attacker remote control", "is_correct": True}, {"text": "A mouse virus", "is_correct": False}, {"text": "A screen recorder", "is_correct": False}, {"text": "A fast trojan", "is_correct": False}]},
            {"text": "How are Trojans usually delivered?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Easy", "skill_focus": "Exploitation", "explanation": "Via downloaded games, cracks, or email attachments.", "options": [{"text": "Downloads / Email Attachments", "is_correct": True}, {"text": "Magic", "is_correct": False}, {"text": "Power cables", "is_correct": False}, {"text": "Monitor screen", "is_correct": False}]},
            {"text": "What is a 'Backdoor'?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Easy", "skill_focus": "Theory", "explanation": "A hidden method for bypassing authentication to access a system.", "options": [{"text": "Hidden entry point", "is_correct": True}, {"text": "Rear door of a building", "is_correct": False}, {"text": "A firewall", "is_correct": False}, {"text": "A password", "is_correct": False}]},
            {"text": "What is a 'Logic Bomb'?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "Malicious code that executes only when specific conditions are met (time, date).", "options": [{"text": "Executes under specific conditions", "is_correct": True}, {"text": "An explosive", "is_correct": False}, {"text": "A math problem", "is_correct": False}, {"text": "A logical error", "is_correct": False}]},
            {"text": "What is Emotet?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Medium", "skill_focus": "History", "explanation": "A famous banking Trojan that evolved into a malware distributor.", "options": [{"text": "Famous Banking Trojan / Loader", "is_correct": True}, {"text": "An emotion", "is_correct": False}, {"text": "A game", "is_correct": False}, {"text": "An antivirus", "is_correct": False}]},
            {"text": "Can a Trojan be inside a PDF?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Yes, exploits in the PDF reader can drop malware.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only TXT files", "is_correct": False}, {"text": "Only MP3s", "is_correct": False}]},
            {"text": "What is 'Binding' in the context of Trojans?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Merging a malicious file with a legitimate one (e.g., calc.exe + trojan).", "options": [{"text": "Merging malicious file with legitimate one", "is_correct": True}, {"text": "Tying knots", "is_correct": False}, {"text": "Compiling code", "is_correct": False}, {"text": "Zipping files", "is_correct": False}]},
            {"text": "What tool detects Trojans?", "type": "multiple_choice", "topic": "Trojan Horse", "difficulty": "Easy", "skill_focus": "Defense", "explanation": "Antivirus / Antimalware.", "options": [{"text": "Antivirus", "is_correct": True}, {"text": "Calculator", "is_correct": False}, {"text": "Paint", "is_correct": False}, {"text": "Notepad", "is_correct": False}]},
        ])

        # --- 19. Keylogging ---
        questions.extend([
            {"text": "What does a Keylogger do?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Records every keystroke made by the user.", "options": [{"text": "Records keystrokes", "is_correct": True}, {"text": "Locks keys", "is_correct": False}, {"text": "Makes keys louder", "is_correct": False}, {"text": "Types for you", "is_correct": False}]},
            {"text": "Can Keyloggers be Hardware-based?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Yes, physical devices plugged between keyboard and PC.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only on Mac", "is_correct": False}, {"text": "Only on Linux", "is_correct": False}]},
            {"text": "What is a 'Virtual Keyboard' used for?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Clicking letters on screen bypasses hardware keyloggers (and some software ones).", "options": [{"text": "Bypassing keyloggers", "is_correct": True}, {"text": "Typing faster", "is_correct": False}, {"text": "Looking cool", "is_correct": False}, {"text": "Saving power", "is_correct": False}]},
            {"text": "What is 'Spyware'?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Software that secretly gathers information about a person.", "options": [{"text": "Software gathering info secretly", "is_correct": True}, {"text": "James Bond movie", "is_correct": False}, {"text": "Antivirus", "is_correct": False}, {"text": "A game", "is_correct": False}]},
            {"text": "Can a keylogger steal copied text (Clipboard)?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Yes, advanced loggers monitor clipboard data too.", "options": [{"text": "Yes", "is_correct": True}, {"text": "No", "is_correct": False}, {"text": "Only if you paste twice", "is_correct": False}, {"text": "Only images", "is_correct": False}]},
            {"text": "How do you detect a Hardware Keylogger?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Medium", "skill_focus": "Defense", "explanation": "Physical inspection of the computer ports.", "options": [{"text": "Physical inspection", "is_correct": True}, {"text": "Antivirus software", "is_correct": False}, {"text": "Firewall", "is_correct": False}, {"text": "Restarting PC", "is_correct": False}]},
            {"text": "What is 'Stalkerware'?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Medium", "skill_focus": "Context", "explanation": "Spyware used in domestic abuse scenarios to track partners.", "options": [{"text": "Spyware used to track partners/spouses", "is_correct": True}, {"text": "Tracking animals", "is_correct": False}, {"text": "Tracking satellites", "is_correct": False}, {"text": "Tracking packages", "is_correct": False}]},
            {"text": "Does encryption help against Keyloggers?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "No, because the keylogger captures the input *before* it is encrypted.", "options": [{"text": "No, input is captured before encryption", "is_correct": True}, {"text": "Yes, always", "is_correct": False}, {"text": "Only AES", "is_correct": False}, {"text": "Only RSA", "is_correct": False}]},
            {"text": "What is 'Form Grabbing'?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "Stealing data from web forms upon submission (often used by banking trojans).", "options": [{"text": "Stealing web form data", "is_correct": True}, {"text": "Grabbing a window", "is_correct": False}, {"text": "Moving forms", "is_correct": False}, {"text": "Creating forms", "is_correct": False}]},
            {"text": "Is a keylogger always malware?", "type": "multiple_choice", "topic": "Keylogging", "difficulty": "Easy", "skill_focus": "Context", "explanation": "No, they can be used for parental control or employee monitoring (legally grey/dependent on consent).", "options": [{"text": "No, used for monitoring too", "is_correct": True}, {"text": "Yes, always illegal", "is_correct": False}, {"text": "Only in Russia", "is_correct": False}, {"text": "Only in USA", "is_correct": False}]},
        ])

        # --- 20. Privilege Escalation ---
        questions.extend([
            {"text": "What is Privilege Escalation?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "Gaining higher permissions than initially granted.", "options": [{"text": "Gaining higher permissions", "is_correct": True}, {"text": "Going up an elevator", "is_correct": False}, {"text": "Downloading files", "is_correct": False}, {"text": "Installing software", "is_correct": False}]},
            {"text": "What is Vertical Privilege Escalation?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "User -> Admin (Moving up).", "options": [{"text": "User to Admin", "is_correct": True}, {"text": "User to User", "is_correct": False}, {"text": "Admin to User", "is_correct": False}, {"text": "Admin to Root", "is_correct": False}]},
            {"text": "What is Horizontal Privilege Escalation?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Medium", "skill_focus": "Theory", "explanation": "User A -> User B (Same level, different account).", "options": [{"text": "User A to User B", "is_correct": True}, {"text": "User to Admin", "is_correct": False}, {"text": "Admin to Root", "is_correct": False}, {"text": "Guest to User", "is_correct": False}]},
            {"text": "What Linux command is often targeted for escalation (SUID)?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Commands with SUID bit run as owner (root).", "options": [{"text": "SUID binaries", "is_correct": True}, {"text": "ls", "is_correct": False}, {"text": "cd", "is_correct": False}, {"text": "echo", "is_correct": False}]},
            {"text": "What is 'Dirty COW'?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Hard", "skill_focus": "History", "explanation": "A famous Linux kernel vulnerability (Copy-On-Write) for root escalation.", "options": [{"text": "Linux Kernel Exploit", "is_correct": True}, {"text": "A farm game", "is_correct": False}, {"text": "Windows Virus", "is_correct": False}, {"text": "Mac App", "is_correct": False}]},
            {"text": "What Windows file contains password hashes (SAM)?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Medium", "skill_focus": "Knowledge", "explanation": "SAM (Security Account Manager).", "options": [{"text": "SAM", "is_correct": True}, {"text": "PASS.TXT", "is_correct": False}, {"text": "WIN.INI", "is_correct": False}, {"text": "BOOT.INI", "is_correct": False}]},
            {"text": "What is 'UAC Bypass'?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "Bypassing Windows User Account Control prompts.", "options": [{"text": "Bypassing Windows UAC", "is_correct": True}, {"text": "Unlocking A Car", "is_correct": False}, {"text": "Using A Computer", "is_correct": False}, {"text": "Under A Cloud", "is_correct": False}]},
            {"text": "What is a 'Kernel Exploit' usually used for?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Hard", "skill_focus": "Exploitation", "explanation": "Gaining Root/System privileges.", "options": [{"text": "Gaining Root/System privileges", "is_correct": True}, {"text": "Crashing the browser", "is_correct": False}, {"text": "Playing music", "is_correct": False}, {"text": "Sending email", "is_correct": False}]},
            {"text": "Why are misconfigured Cron jobs (Linux) dangerous?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Medium", "skill_focus": "Exploitation", "explanation": "If a writable script runs as root, a user can modify it to become root.", "options": [{"text": "User can modify root scripts", "is_correct": True}, {"text": "They slow down PC", "is_correct": False}, {"text": "They consume disk space", "is_correct": False}, {"text": "They send spam", "is_correct": False}]},
            {"text": "What does 'sudo' stand for?", "type": "multiple_choice", "topic": "Privilege Escalation", "difficulty": "Easy", "skill_focus": "Knowledge", "explanation": "SuperUser DO.", "options": [{"text": "SuperUser DO", "is_correct": True}, {"text": "Super User Don't", "is_correct": False}, {"text": "System Undo Do", "is_correct": False}, {"text": "Simple User Do", "is_correct": False}]},
        ])

        return questions

    def seed_data():
        wait_for_db()
        
        # --- CRITICAL FIX: CREATE TABLES BEFORE SEEDING ---
        logger.info("Ensuring database tables exist...")
        models.Base.metadata.create_all(bind=engine)
        # --------------------------------------------------

        db: Session = SessionLocal()
        try:
            # 1. Seed Users (Admin/Instructor)
            seed_users(db)

            # 2. Seed Questions
            existing_count = db.query(models.Question).count()
            if existing_count >= 200:
                logger.info(f"Database already has {existing_count} questions. Skipping seeding.")
                return

            logger.info(f"Database has {existing_count} questions. Seeding to reach 200...")

            # Get the massive list of 200 questions
            questions_data = generate_questions()

            count_added = 0
            for q_data in questions_data:
                # Check for duplicates to avoid constraint errors
                exists = db.query(models.Question).filter(models.Question.text == q_data["text"]).first()
                if exists:
                    continue
                    
                options_data = q_data.pop("options")
                question = models.Question(**q_data)
                db.add(question)
                db.commit()
                db.refresh(question)
                
                for opt_data in options_data:
                    option = models.QuestionOption(**opt_data, question_id=question.id)
                    db.add(option)
                db.commit()
                count_added += 1
                
            logger.info(f"Successfully seeded {count_added} new questions.")
            
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            db.rollback()
        finally:
            db.close()

    if __name__ == "__main__":
        seed_data()
    ```


    ## M.4 Application entry (`backend/app/main.py`)

    ### `backend/app/main.py`

    ```python
    from .env_bootstrap import load_env

    load_env()

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import inspect, text
    import time
    import logging
    import os

    # --- IMPORT ROUTERS ---
    # We added 'stats', 'projects', 'game_challenge', and 'misconfig' to this import list
    from .api import auth, quizzes, challenges, stats, messages, projects, game_challenge, misconfig, ai_mentor, attack_simulator, project_analyzer, security_logs, quiz_dynamic, instructor, report, red_blue, challenge_assignments
    from .db import database
    from . import models 

    # Setup Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app = FastAPI()

    # --- CORS SETUP ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- REGISTER ROUTES ---
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
    app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])
    # NEW: Register the stats router so the Dashboards work
    app.include_router(stats.router, prefix="/api/stats", tags=["statistics"])
    # NEW: Messaging routes
    app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
    # NEW: Project upload routes
    app.include_router(projects.router, prefix="/api", tags=["projects"])
    # NEW: Red vs Blue challenge routes (singular /challenge prefix)
    app.include_router(game_challenge.router, prefix="/api/challenge", tags=["game_challenge"])
    # NEW: Security misconfiguration mini-app routes
    app.include_router(misconfig.router, prefix="/api", tags=["misconfig"])
    # NEW: AI mentor analysis routes
    app.include_router(ai_mentor.router, prefix="/api/ai", tags=["ai_mentor"])
    # NEW: attack simulation lab routes
    app.include_router(attack_simulator.router, prefix="/api/attack", tags=["attack_simulator"])
    # NEW: project structure analyzer routes
    app.include_router(project_analyzer.router, prefix="/api", tags=["project_analyzer"])
    # NEW: centralized security logs routes
    app.include_router(security_logs.router, prefix="/api/security", tags=["security_logs"])
    # NEW: dynamic quiz generation from scan findings
    app.include_router(quiz_dynamic.router, prefix="/api/quiz", tags=["quiz_dynamic"])
    app.include_router(instructor.router, prefix="/api/instructor", tags=["instructor"])
    app.include_router(report.router)
    app.include_router(red_blue.router, prefix="/api/redblue", tags=["redblue"])
    app.include_router(challenge_assignments.router, prefix="/api/challenge-assignments", tags=["challenge_assignments"])


    def _ensure_runtime_schema():
        """
        Lightweight runtime migration guard for environments without Alembic.
        Ensures newly introduced columns exist before write paths use them.
        """
        try:
            inspector = inspect(database.engine)
            with database.engine.begin() as conn:
                if "security_logs" in inspector.get_table_names():
                    security_existing = {col["name"] for col in inspector.get_columns("security_logs")}
                    security_required = {
                        "geo_bucket": "VARCHAR(50) NULL",
                        "session_id": "VARCHAR(100) NULL",
                        "correlation_id": "VARCHAR(100) NULL",
                        "context_type": "VARCHAR(50) NULL DEFAULT 'real'",
                    }
                    for column_name, ddl in security_required.items():
                        if column_name in security_existing:
                            continue
                        conn.execute(text(f"ALTER TABLE security_logs ADD COLUMN {column_name} {ddl}"))
                        logger.warning("Applied runtime schema patch: security_logs.%s", column_name)

                if "user_learning_progress" in inspector.get_table_names():
                    learning_existing = {col["name"] for col in inspector.get_columns("user_learning_progress")}
                    learning_required = {
                        "streak_days": "INT NULL DEFAULT 0",
                        "learning_speed": "FLOAT NULL DEFAULT 0",
                        "retention_score": "FLOAT NULL DEFAULT 0",
                    }
                    for column_name, ddl in learning_required.items():
                        if column_name in learning_existing:
                            continue
                        conn.execute(text(f"ALTER TABLE user_learning_progress ADD COLUMN {column_name} {ddl}"))
                        logger.warning("Applied runtime schema patch: user_learning_progress.%s", column_name)

                tables = set(inspector.get_table_names())
                if "teams" in tables:
                    tcols = {c["name"] for c in inspector.get_columns("teams")}
                    if "created_by" not in tcols:
                        conn.execute(text("ALTER TABLE teams ADD COLUMN created_by INT NULL"))
                        logger.warning("Applied runtime schema patch: teams.created_by")
                if "game_challenges" in tables:
                    gc_cols = {c["name"] for c in inspector.get_columns("game_challenges")}
                    if "lab_challenge_id" not in gc_cols:
                        conn.execute(text("ALTER TABLE game_challenges ADD COLUMN lab_challenge_id INT NULL"))
                        logger.warning("Applied runtime schema patch: game_challenges.lab_challenge_id")
                    if "started_at" not in gc_cols:
                        conn.execute(text("ALTER TABLE game_challenges ADD COLUMN started_at DATETIME NULL"))
                        logger.warning("Applied runtime schema patch: game_challenges.started_at")
                if "red_team_actions" in tables:
                    rcols = {c["name"] for c in inspector.get_columns("red_team_actions")}
                    for col, ddl in (
                        ("user_id", "INT NULL"),
                        ("payload_used", "TEXT NULL"),
                        ("impact_description", "TEXT NULL"),
                        ("status", "VARCHAR(20) NULL DEFAULT 'confirmed'"),
                    ):
                        if col not in rcols:
                            conn.execute(text(f"ALTER TABLE red_team_actions ADD COLUMN {col} {ddl}"))
                            logger.warning("Applied runtime schema patch: red_team_actions.%s", col)
                    try:
                        conn.execute(text("ALTER TABLE red_team_actions MODIFY COLUMN vulnerability_id INT NULL"))
                    except Exception:
                        pass
                if "blue_team_fixes" in tables:
                    bcols = {c["name"] for c in inspector.get_columns("blue_team_fixes")}
                    for col, ddl in (("user_id", "INT NULL"), ("submitted_code", "TEXT NULL")):
                        if col not in bcols:
                            conn.execute(text(f"ALTER TABLE blue_team_fixes ADD COLUMN {col} {ddl}"))
                            logger.warning("Applied runtime schema patch: blue_team_fixes.%s", col)
                    try:
                        conn.execute(text("ALTER TABLE blue_team_fixes MODIFY COLUMN vulnerability_id INT NULL"))
                    except Exception:
                        pass
        except Exception as exc:
            # Logging subsystem must not block API startup if migration is partially unsupported.
            logger.warning("Runtime schema self-heal skipped: %s", exc)

    # --- DATABASE CONNECTION RETRY ---
    @app.on_event("startup")
    async def log_ai_status():
        oa = (os.getenv("OPENAI_API_KEY", "") or "").strip()
        sp = (os.getenv("SERPER_API_KEY", "") or "").strip()
        if oa:
            logger.info("AI features: OpenAI ENABLED (OPENAI_API_KEY set)")
        if sp:
            logger.info("AI features: Serper web search ENABLED (SERPER_API_KEY set)")
        if not oa and not sp:
            logger.warning(
                "AI features: DISABLED (set OPENAI_API_KEY and/or SERPER_API_KEY in .env). "
                "Serper.dev provides Google search-backed hints without an LLM."
            )


    @app.on_event("startup")
    def startup_event():
        logger.info("Waiting for Database...")
        retries = 10
        while retries > 0:
            try:
                # Create tables if they don't exist
                models.Base.metadata.create_all(bind=database.engine)
                _ensure_runtime_schema()
                logger.info("Database connected and tables created!")
                break
            except OperationalError as e:
                retries -= 1
                logger.warning(f"DB not ready. Retrying... ({retries} left)")
                time.sleep(3)
                if retries == 0:
                    logger.error("Could not connect to database.")
                    raise e

    @app.get("/")
    def read_root():
        return {"message": "Welcome to the SCALE API"}
    ```


    ## M.5 Docker Compose (`docker-compose.yml`)

    ### `docker-compose.yml`

    ```yaml
    networks:
    scale_net:
        name: scale_net
        driver: bridge

    services:
    # 1. SANDBOX BUILDER
    sandbox_base:
        build: 
        context: ./backend/sandbox_base
        image: scale-sandbox-base
        container_name: scale_sandbox_builder
        command: ["echo", "Sandbox Base Image Built Successfully"]
        networks:
        - scale_net

    # 2. MAIN BACKEND API
    backend:
        build: ./backend
        container_name: scale_application-backend-1
        restart: on-failure
        ports:
        - "8000:8000"
        volumes:
        # Required by sandbox runner to build/run challenge containers.
        # Keep this for lab mode; avoid in production unless strongly isolated.
        - /var/run/docker.sock:/var/run/docker.sock
        - ./backend:/app
        # --- MOUNT CHALLENGE FOLDERS ---
        - ./challenge-sql-injection:/app/challenges/challenge-sql-injection
        - ./challenge-xss:/app/challenges/challenge-xss
        - ./challenge-csrf:/app/challenges/challenge-csrf
        - ./challenge-redirect:/app/challenges/challenge-redirect
        - ./challenge-command-injection:/app/challenges/challenge-command-injection
        - ./challenge-broken-auth:/app/challenges/challenge-broken-auth
        - ./challenge-security-misc:/app/challenges/challenge-security-misc
        - ./challenge-directory-traversal:/app/challenges/challenge-directory-traversal
        - ./challenge-xxe:/app/challenges/challenge-xxe
        - ./challenge-insecure-storage:/app/challenges/challenge-insecure-storage
        networks:
        - scale_net
        depends_on:
        main_db:
            condition: service_healthy
        challenge_db_sqli:
            condition: service_healthy
        challenge_db_csrf:
            condition: service_healthy
        sandbox_base:
            condition: service_completed_successfully
        # Injects OPENAI_API_KEY, SERPER_API_KEY, etc. from the same folder as docker-compose.yml
        # (copy .env.example to .env). Optional so compose still runs if you only use backend/.env.
        env_file:
        - path: .env
            required: false
        environment:
        - DATABASE_URL=${DATABASE_URL:-mysql+pymysql://user:password@main_db/scale_db}
        - SQLI_DATABASE_URL=${SQLI_DATABASE_URL:-mysql+pymysql://user:password@challenge_db_sqli/testdb}
        - CSRF_DATABASE_URL=${CSRF_DATABASE_URL:-mysql+pymysql://user:password@challenge_db_csrf/csrfdb}
        - SECRET_KEY=${SECRET_KEY:-scale_graduation_project_secret_key}
        - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-600}
        - ENABLE_BROKEN_AUTH_CHALLENGE=${ENABLE_BROKEN_AUTH_CHALLENGE:-true}
        - SANDBOX_MAX_CODE_CHARS=${SANDBOX_MAX_CODE_CHARS:-200000}
        - AI_SERVICE_URL=${AI_SERVICE_URL:-http://ai_service:8001}
        command: ["sh", "-c", "python seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

    # 3. FRONTEND
    frontend:
        build: ./frontend
        container_name: scale_application-frontend-1
        ports:
        - "5173:5173"
        volumes:
        - ./frontend:/app
        - /app/node_modules
        # Voiced tutorials playback in /challenges/*/tutorial (see frontend/vite.config.ts)
        - ./Web-Videos:/app/web-videos:ro
        networks:
        - scale_net
        command: npm run dev -- --host
        environment:
        - VITE_API_URL=${VITE_API_URL:-http://localhost:8000}

    # 4. AI SERVICE
    ai_service:
        build: ./ai_service
        container_name: scale_application-ai_service-1
        ports:
        - "8001:8001"
        volumes:
        - ./ai_service:/app
        networks:
        - scale_net
        command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

    # 5. MAIN DATABASE (App Data)
    main_db:
        image: mysql:8.0
        container_name: main_db
        environment:
        - MYSQL_DATABASE=${MYSQL_DATABASE:-scale_db}
        - MYSQL_USER=${MYSQL_USER:-user}
        - MYSQL_PASSWORD=${MYSQL_PASSWORD:-password}
        - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-rootpassword}
        volumes:
        - scale_db_data:/var/lib/mysql
        - ./db_init/init.sql:/docker-entrypoint-initdb.d/init.sql
        networks:
        - scale_net
        ports:
        - "3306:3306"
        healthcheck:
        test: ["CMD-SHELL", "mysqladmin ping -h localhost -u${MYSQL_USER:-user} -p${MYSQL_PASSWORD:-password} || exit 1"]
        interval: 5s
        timeout: 5s
        retries: 20
        start_period: 20s

    # 6. SQL INJECTION DATABASE
    challenge_db_sqli:
        image: mysql:8.0
        container_name: challenge_db_sqli
        environment:
        - MYSQL_DATABASE=${SQLI_MYSQL_DATABASE:-testdb}
        - MYSQL_USER=${SQLI_MYSQL_USER:-user}
        - MYSQL_PASSWORD=${SQLI_MYSQL_PASSWORD:-password}
        - MYSQL_ROOT_PASSWORD=${SQLI_MYSQL_ROOT_PASSWORD:-rootpassword}
        volumes:
        - ./challenge-sql-injection/users.sql:/docker-entrypoint-initdb.d/init.sql
        ports:
        - "3307:3306"
        networks:
        - scale_net
        healthcheck:
        test: ["CMD-SHELL", "mysqladmin ping -h localhost -u${SQLI_MYSQL_USER:-user} -p${SQLI_MYSQL_PASSWORD:-password} || exit 1"]
        interval: 5s
        timeout: 5s
        retries: 20
        start_period: 20s

    # 7. CSRF CHALLENGE DATABASE (NEW EXTERNAL DB)
    challenge_db_csrf:
        image: mysql:8.0
        container_name: challenge_db_csrf
        environment:
        - MYSQL_DATABASE=${CSRF_MYSQL_DATABASE:-csrfdb}
        - MYSQL_USER=${CSRF_MYSQL_USER:-user}
        - MYSQL_PASSWORD=${CSRF_MYSQL_PASSWORD:-password}
        - MYSQL_ROOT_PASSWORD=${CSRF_MYSQL_ROOT_PASSWORD:-rootpassword}
        volumes:
        # Mount the new SQL file here
        - ./challenge-csrf/csrf.sql:/docker-entrypoint-initdb.d/init.sql
        ports:
        - "3308:3306"
        networks:
        - scale_net
        healthcheck:
        test: ["CMD-SHELL", "mysqladmin ping -h localhost -u${CSRF_MYSQL_USER:-user} -p${CSRF_MYSQL_PASSWORD:-password} || exit 1"]
        interval: 5s
        timeout: 5s
        retries: 20
        start_period: 20s

    volumes:
    scale_db_data:
    ```


    ## M.6 Environment template (`.env.example`)

    ### `.env.example`

    ```bash
    # SCALE Platform — Environment Variables
    #
    # IMPORTANT: Copy this file to ".env" in the SAME folder as docker-compose.yml
    #   (e.g. copy .env.example .env) and put your secrets there.
    # Docker Compose only auto-loads ".env" — editing ".env.example" alone does nothing.
    #
    # If keys still do not reach the backend container, add the same variables to
    # backend/.env (next to backend/Dockerfile). That file is mounted as /app/.env
    # and is loaded at startup with override so Serper/OpenAI keys apply reliably.
    #

    # ─── AI Features ──────────────────────────────────────────
    # Add your OpenAI API key to enable:
    #   - AI Attack Mentor (context-aware coaching)
    #   - AI Quiz Generation (topic-specific question creation)
    #   - AI Scan Explanation (vulnerability analysis narration)
    # Leave empty to disable AI features gracefully.
    # Must be a real OpenAI secret key from https://platform.openai.com/api-keys
    # (starts with sk- or sk-proj-). Leave empty if you only use Serper below.
    OPENAI_API_KEY=

    # Serper.dev — Google Search API (https://serper.dev). Used when OpenAI is not set:
    # quiz generation from web snippets, mentor answers from search results, scan enrichment.
    # This is NOT an OpenAI key; get it from your Serper dashboard.
    SERPER_API_KEY=

    # AI service internal URL (template-based quiz preview; optional)
    AI_SERVICE_URL=http://ai_service:8001

    # ─── Database ─────────────────────────────────────────────
    DATABASE_URL=mysql+pymysql://user:password@main_db/scale_db
    SQLI_DATABASE_URL=mysql+pymysql://user:password@challenge_db_sqli/testdb
    CSRF_DATABASE_URL=mysql+pymysql://user:password@challenge_db_csrf/csrfdb

    # ─── Auth ─────────────────────────────────────────────────
    SECRET_KEY=scale_graduation_project_secret_key
    ACCESS_TOKEN_EXPIRE_MINUTES=600
    ENABLE_BROKEN_AUTH_CHALLENGE=true

    # ─── Sandbox ──────────────────────────────────────────────
    SANDBOX_MAX_CODE_CHARS=200000
    SANDBOX_RUN_TIMEOUT=25

    # ─── Frontend ─────────────────────────────────────────────
    VITE_API_URL=http://localhost:8000

    ```


    ## M.7 Frontend manifests

    ### `frontend/package.json`

    ```json
    {
    "name": "frontend",
    "private": true,
    "version": "0.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "tsc && vite build",
        "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
        "preview": "vite preview"
    },
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
        "@types/prop-types": "^15.7.15",
        "@types/react": "^18.2.66",
        "@types/react-dom": "^18.2.22",
        "@typescript-eslint/eslint-plugin": "^7.2.0",
        "@typescript-eslint/parser": "^7.2.0",
        "@vitejs/plugin-react": "^4.2.1",
        "autoprefixer": "^10.4.19",
        "eslint": "^8.57.0",
        "eslint-plugin-react-hooks": "^4.6.0",
        "eslint-plugin-react-refresh": "^0.4.6",
        "postcss": "^8.4.38",
        "tailwindcss": "^3.4.3",
        "typescript": "^5.2.2",
        "vite": "^5.2.0"
    }
    }

    ```


    ### `frontend/vite.config.ts`

    ```typescript
    import fs from 'node:fs'
    import path from 'node:path'
    import { fileURLToPath } from 'node:url'

    import type { Connect } from 'vite'
    import { defineConfig } from 'vite'
    import react from '@vitejs/plugin-react'

    const __dirname = path.dirname(fileURLToPath(import.meta.url))

    /** Serve tutorial MP4s from repo `Web-Videos` in dev (Docker: mount to `./web-videos`). */
    function resolveWebVideosRoot(): string | null {
    const candidates = [
        path.join(__dirname, 'web-videos'),
        path.resolve(__dirname, '..', 'Web-Videos'),
    ]
    for (const dir of candidates) {
        try {
        if (fs.existsSync(dir) && fs.statSync(dir).isDirectory()) {
            return dir
        }
        } catch {
        /* ignore */
        }
    }
    return null
    }

    function challengeVideosMiddleware(): Connect.NextHandleFunction {
    return (req, res, next) => {
        if (!req.url?.startsWith('/challenge-videos/')) {
        next()
        return
        }
        const root = resolveWebVideosRoot()
        if (!root) {
        next()
        return
        }
        const raw = req.url.replace(/^\/challenge-videos\//, '').split('?')[0] || ''
        let name: string
        try {
        name = decodeURIComponent(raw)
        } catch {
        next()
        return
        }
        const safe = path.basename(name)
        if (safe !== name || !safe.toLowerCase().endsWith('.mp4')) {
        next()
        return
        }
        const file = path.join(root, safe)
        if (!file.startsWith(root)) {
        next()
        return
        }
        fs.stat(file, (err, st) => {
        if (err || !st.isFile()) {
            next()
            return
        }
        const size = st.size
        const range = typeof req.headers.range === 'string' ? req.headers.range : undefined
        if (range) {
            const m = /^bytes=(\d*)-(\d*)$/.exec(range)
            if (!m) {
            next()
            return
            }
            let start = m[1] ? parseInt(m[1], 10) : 0
            let end = m[2] ? parseInt(m[2], 10) : size - 1
            if (Number.isNaN(start) || Number.isNaN(end) || start >= size || end >= size || start > end) {
            res.statusCode = 416
            res.setHeader('Content-Range', `bytes */${size}`)
            res.end()
            return
            }
            res.statusCode = 206
            res.setHeader('Content-Type', 'video/mp4')
            res.setHeader('Accept-Ranges', 'bytes')
            res.setHeader('Content-Range', `bytes ${start}-${end}/${size}`)
            res.setHeader('Content-Length', String(end - start + 1))
            fs.createReadStream(file, { start, end }).pipe(res)
            return
        }
        res.setHeader('Content-Type', 'video/mp4')
        res.setHeader('Accept-Ranges', 'bytes')
        res.setHeader('Content-Length', String(size))
        fs.createReadStream(file).pipe(res)
        })
    }
    }

    function webVideosDevPlugin() {
    return {
        name: 'serve-challenge-tutorial-videos',
        configureServer(server: { middlewares: Connect.Server }) {
        server.middlewares.use(challengeVideosMiddleware())
        },
    }
    }

    // https://vitejs.dev/config/
    export default defineConfig({
    plugins: [react(), webVideosDevPlugin()],
    })
    ```


    ### `backend/requirements.txt`

    ```text
    fastapi
    uvicorn[standard]
    SQLAlchemy
    PyMySQL
    requests
    httpx
    pydantic
    python-dotenv
    docker
    # --- Auth Dependencies (CRITICAL) ---
    python-jose[cryptography]
    passlib[bcrypt]
    python-multipart
    bcrypt==4.0.1
    reportlab
    openai
    lxml
    semgrep
    ```


    ---

    *End of document. Primary artifact: `PROJECT_DOCUMENTATION.md` (repository root). Revision: May 2026. Route inventory: Appendix B (**128 routes**); full backend listings: Appendix M.*