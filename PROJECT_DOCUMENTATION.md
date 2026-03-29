# SCALE Platform — Full System Technical Documentation

**Generated from codebase analysis (FastAPI backend, React/Vite frontend, Docker Compose).**  
This document describes **observed behavior in code**, not marketing intent. Known defects and “fake” training logic are called out explicitly.

---

## 1. Project Overview

### 1.1 Purpose

The platform (**SCALE API** root message in `backend/app/main.py`) is a **security learning and lab environment** that combines:

- **Static project scanning** (regex/rule-based) on uploaded ZIP archives  
- **Interactive vulnerability challenges** (attack → optional fix via sandboxed tests)  
- **Quizzes** (database-backed bank + scan-driven synthetic questions)  
- **Dashboards** for students, instructors, and admins  
- **Centralized security event logging** with admin-facing filters and stats  

### 1.2 Architecture Style

- **Backend:** Single **FastAPI monolith** (`backend/app/main.py`) with modular routers under `backend/app/api/`.  
- **Frontend:** Single **React SPA** (Vite) with React Router; layout via `MainLayout`, auth gating via `ProtectedRoute`.  
- **Data:** **MySQL** (SQLAlchemy) for application state; **additional MySQL instances** for SQLi and CSRF challenge data.  
- **Sandbox:** **Docker-in-Docker** (host socket mounted) builds per-submission images and runs `run_tests.sh` (see §5).  
- **AI:** Optional **separate `ai_service`** container for quiz preview generation; project scan AI hooks exist in `projects.py`.

### 1.3 Core Subsystems

| Subsystem | Role |
|-----------|------|
| `api/auth` | JWT login/register, RBAC, broken-auth challenge mode |
| `api/challenges` | Challenge APIs: vulnerable endpoints, fix submission, progress, hints, state |
| `api/projects` | ZIP upload, extract, scan, reports, analytics |
| `api/quizzes` + `api/quiz` (`quiz_dynamic`) | Two parallel quiz systems (see §8) |
| `api/stats` + `security/learning_tracker` | Learning progress payload for dashboards |
| `api/security` (`security_logs`) | Admin log listing + aggregate stats |
| `scanner/*` | Rule-based detector, scorer, fix text attachment |
| `sandbox_runner` | Isolated fix validation for challenge `app.py` |
| `security/security_logger` | DB-backed event stream + context normalization |

### 1.4 Learning Flow (As Implemented)

**Scan → Attack → Fix → Quiz → Progress → Logs** is the **intended** didactic order. In code:

1. **Scan:** `POST /api/project/upload` → `POST /api/project/scan` (optional `POST /api/project/scan/ai`).  
2. **Attack:** Per-challenge pages call vulnerable routes under `/api/challenges/...` or `/api/auth/login?challenge=...` or `/api/...` (misconfig). Success often triggers `POST /api/challenges/mark-attack-complete` and navigation to `/challenges/attack-success`.  
3. **Fix:** `POST /api/challenges/submit-fix-*` → `_verify_fix_improvement` → `sandbox_runner.run_in_sandbox_detailed` → on success, `UserProgress` + `recalculate_learning_progress`.  
4. **Quiz:** Student `/quiz` uses bank (`/api/quizzes/take`) and/or **`/api/quiz/generate`** with `ScanContext` findings.  
5. **Progress:** `GET /api/stats/progress/me` aggregates `UserProgress`, `UserAnswer`, `QuizAttempt` in `learning_tracker.py`.  
6. **Logs:** `GET /api/security/logs` (admin), `GET /api/security/logs/stats` — challenge vs real split by `context_type`.

**Gaps:** XSS attack flow is **broken** without backend comment routes (§4, §12). Progress can be marked without completing a realistic attack where the frontend uses **string heuristics** (XSS) or **iframe** checks (CSRF/redirect).

---

## 2. System Architecture

### 2.1 Backend Architecture

**Framework:** FastAPI + Uvicorn (`docker-compose` runs `uvicorn app.main:app` after `seed_db.py`).

**Folder structure (high level):**

| Path | Purpose |
|------|---------|
| `backend/app/main.py` | App factory, CORS, router registration, DB startup + runtime schema patches |
| `backend/app/api/*.py` | HTTP routers (one file per domain) |
| `backend/app/models.py` | SQLAlchemy ORM models |
| `backend/app/schemas.py` | Pydantic request/response models |
| `backend/app/db/database.py` | Engine + `SessionLocal` + `get_db` |
| `backend/app/scanner/` | Detection rules, scoring, report generation |
| `backend/app/security/` | `security_logger`, `learning_tracker` |
| `backend/app/sandbox_runner.py` | Docker-based challenge validation |
| `backend/app/attacks/` | Attack lab simulation templates |

**Request lifecycle (typical):**

1. CORS middleware (`localhost:5173`, `3000` variants).  
2. Route handler — many routes use `Depends(get_db)` and `Depends(get_current_user)` / `require_role(...)`.  
3. **No global HTTP middleware** for request logging in `main.py`; security events are **explicit** `log_security_event(...)` calls.

**Auth dependency:** `OAuth2PasswordBearer(tokenUrl="/api/auth/login")` — tokens are **JWT** (`jose.jwt`) with `sub` = email.

### 2.2 Frontend Architecture

**Stack:** React 18 + TypeScript + Vite (`frontend/vite.config.ts`). Dev server exposed on **5173** (`docker-compose`).

**Routing:** `BrowserRouter` in `frontend/src/App.tsx`:

- Public: `/`, `/login`, `/register`  
- Student + instructor + admin: `/home`, `/challenges`, `/scanner`, `/attack-lab`, challenge routes `/challenges/{id}/...`  
- Student-only: `/quiz`  
- Instructor: `/instructor/dashboard`, `/instructor/quiz`  
- Admin: `/admin/stats`, `/admin/dashboard`, `/admin/logs`  
- Unknown paths → `Navigate to="/"` (catch-all)

**State management:**

- **Session:** `sessionStorage` for `token`, `role`, `user_id`, `user_email` (see `LoginPage`, `ProtectedRoute`).  
- **Scan pipeline:** `ScanContext` (`frontend/src/context/ScanContext.tsx`) persists **`localStorage` key `scale.scanData`** — project id, scan results, overview from structure analyzer.

**API base:** `VITE_API_URL` (default `http://localhost:8000`); `frontend/src/lib/api.ts` axios instance adds `Authorization` header.

### 2.3 Database Design

Tables are created via **`models.Base.metadata.create_all`** on startup (`main.py`). `db_init/init.sql` only seeds an extra **`challenge_users`** table in `scale_db` (legacy/demo); **ORM tables** are still created by SQLAlchemy.

#### All ORM tables (from `backend/app/models.py`)

| Table | Purpose |
|-------|---------|
| `users` | Accounts: email, hashed password, role, `is_approved` |
| `user_progress` | One row per user per completed `challenge_id` (string slug) |
| `xss_comments` | **Model exists** for XSS; **no API routes** were found that use it in `challenges.py` (§12) |
| `challenges` | Metadata rows (title/description); used in **admin stats count** |
| `questions` | Quiz bank |
| `question_options` | MCQ options |
| `user_answers` | Per-question answers + `is_correct` |
| `quiz_assignments` | Instructor assignments (`question_ids`, `assigned_student_ids` as comma-separated **Text**) |
| `quiz_attempts` | Completed attempts: score, total, `time_seconds` |
| `csrf_accounts` | **Legacy/unused in hot path** — live CSRF lab uses **external DB** `accounts` table via raw SQL in `challenges.py` |
| `messages` | User-to-user messaging |
| `projects` | Uploaded project metadata (`id` = string UUID-like folder name) |
| `scan_history` | Per-scan aggregates + `vuln_summary` JSON text |
| `teams`, `team_members`, `game_challenges`, `challenge_vulnerabilities`, `red_team_actions`, `blue_team_fixes` | Red/blue game (separate from training labs) |
| `challenge_state` | Per-user hint usage, stage, attempts, time for “game layer” |
| `security_logs` | Security events with `context_type`, `metadata` JSON column (`meta_data` in Python) |
| `user_learning_progress` | **One row per user**: aggregated metrics for dashboard |

#### Table details (columns & relationships)

**`users`**

- `id` PK, `email` unique, `hashed_password`, `role` (`user` / `instructor` / `admin`), `is_approved` (default `True`; instructors can be pending — see `auth.py`).  
- Relationships: `answers`, `progress`, `quiz_attempts`.

**`user_progress`**

- `user_id` → `users.id`, `challenge_id` **string** (e.g. `sql-injection`, `xss`, or legacy `"1"`/`"2"` normalized in `learning_tracker`).  
- `completed_at` — used for **streak** approximation in `recalculate_learning_progress`.

**`security_logs`**

- `event_type`, `severity`, `payload` (stringified), `endpoint`, IP, `geo_bucket`, `user_agent`, `session_id`, `correlation_id`, **`context_type`** (`real` / `challenge` after normalization), **`metadata`** (JSON).  
- Runtime migration in `main.py` may add columns if missing (`geo_bucket`, `session_id`, `correlation_id`, `context_type` default).

**`user_learning_progress`**

- `user_id` **unique**, `vulnerabilities_solved`, `failed_attempts`, `accuracy`, `avg_time`, `strongest_category`, `weakest_category`, `level`, `streak_days`, `learning_speed`, `retention_score`, `updated_at`.  
- `vulnerabilities_solved` is **capped** at `TOTAL_CHALLENGES` (10) in code.

**`challenges` (ORM)**

- Distinct from **string-based** lab ids in `user_progress`. Admin dashboard counts **rows in `challenges`** as `active_exploits`.

**`quiz_assignments`**

- `assigned_student_ids` and `question_ids` stored as **comma-separated strings** — fragile if empty or malformed.

---

## 3. Authentication System

### 3.1 Login Flow (Normal)

1. `POST /api/auth/login` with body `LoginAttempt`: `username` (email), `password`.  
2. Server loads user by email; verifies **bcrypt** hash (`passlib`).  
3. On failure: `log_security_event(..., LOGIN_FAILED or CHALLENGE_AUTH, context_type real vs challenge)` — see §6.  
4. On success: JWT with `sub` = email, `role` = DB role; `LOGIN_SUCCESS` or `CHALLENGE_AUTH` logged.  
5. Pending instructors: `403` if `is_approved` is false.

**Token storage (frontend):** `sessionStorage` — not `httpOnly` cookies; **XSS on any origin** could steal tokens (mitigation is not part of this codebase).

### 3.2 Registration

- `POST /api/auth/register` — **cannot** self-register as `admin`.  
- `POST /api/auth/admin/create-admin` — admin-only.

### 3.3 Challenge Mode: `?challenge=broken-auth`

- When `challenge=broken-auth` and `ENABLE_BROKEN_AUTH_CHALLENGE` is true (default): **no MySQL auth**.  
- Code uses **in-memory SQLite** with a deliberately unsafe string-built query (`auth.py`).  
- Returns JWT possibly tied to **platform user** if email exists (`crud.get_user_by_email`), else token `sub` may be synthetic (`admin@scale.edu`).  
- Logs `CHALLENGE_SQLI` with metadata describing `bypass_success`, `is_injected`, etc.  
- **Intentional weakness:** SQL injection simulation.  
- **Real weakness:** Default `SECRET_KEY` in env example; JWT is symmetric HS256.

### 3.4 RBAC

- `require_role(...)` normalizes `"student"` → `"user"` (`auth.py`).  
- Endpoints mix `get_current_user`, `get_current_admin`, and `require_role("admin", "instructor")` etc.

---

## 4. Challenge System (All 10 Labs)

Global backend prefix: **`/api/challenges`** (router in `main.py`).

Fix verification for all sandbox-backed labs uses **`_verify_fix_improvement`** (`challenges.py`):

- Runs **vulnerable reference `app.py`** from `/app/challenges/<challenge_dir>/app.py` through the sandbox.  
- Runs **student code** through the same.  
- Compares **unittest summary** (`failures` + `errors` from log parsing — not “vulnerability counts” from a static scanner).  
- `before_vulnerabilities` / `after_vulnerabilities` variable names are **misleading** — they store **test failure/error counts**, not CVE-style counts.

---

### Challenge 1 — SQL Injection

| Aspect | Detail |
|--------|--------|
| **Type** | SQLi (authentication bypass) |
| **Backend** | `POST /api/challenges/vulnerable-login` — builds raw SQL against `SQLI_DATABASE_URL` (MySQL `challenge_db_sqli`). |
| **Frontend** | `/challenges/1/attack`, `/challenges/1/fix`, `/challenges/1/tutorial` |
| **Attack phase** | **Real** DB query execution; success when a row is returned (`200`). Frontend treats any `200` as success and calls `mark-attack-complete` + redirect to attack-success. |
| **Fix phase** | `POST /api/challenges/submit-fix` → `challenge-sql-injection`. |
| **Sandbox tests** | `challenge-sql-injection/test_app.py` uses **gunicorn** on port 5000; `run_tests.sh` also starts `python app.py &` first → **port/process conflict risk** (§12). Student Flask app expects MySQL host `db` by default but sandbox container uses **`network=scale_net`** — DB service naming must match `requirements`/env inside the challenge image (often fails unless challenge image configures DB host — **environment coupling**). |

**Current problems**

- Local `run_tests.sh` + `test_app.py` **duplicate server startup** (Flask background + gunicorn in tests).  
- Admin dashboard `stats.py` only attributes **SQLi/XSS** “fixes” in a narrow legacy map — **does not list all 10 challenge types**.

---

### Challenge 2 — XSS

| Aspect | Detail |
|--------|--------|
| **Type** | Stored XSS (conceptually) |
| **Backend** | **No** `/api/challenges/xss/comments` routes in `challenges.py` (confirmed by router list). `XSSComment` model and `CommentCreate` schema exist but are **unused** by registered routes. |
| **Frontend** | `XssAttackPage.tsx`: GET/POST/DELETE `/api/challenges/xss/comments`; **then** client-side “XSS detection” via substring patterns (`<script>`, `onerror=`, etc.). |
| **Attack success** | **Hardcoded / client-only:** Patterns in frontend; **not** server-rendered execution. Posting requires **successful POST** to missing API → **flow broken** (§12). |
| **Fix** | `POST /api/challenges/submit-fix-xss` |

**Current problems**

- **Critical:** Comment API **missing** → typical user cannot post comments successfully; success path never reached in order implemented (POST before pattern check).  
- Success is **not** tied to real DOM execution — pattern matching only.

---

### Challenge 3 — CSRF

| Aspect | Detail |
|--------|--------|
| **Type** | CSRF on bank transfer |
| **Backend** | `POST /api/challenges/csrf/transfer` (form), `GET /api/challenges/csrf/accounts`, `POST /api/challenges/csrf/reset`; recipient lookup uses **string-interpolated SQL** (second-order injection surface). |
| **Frontend** | Writes attacker HTML into hidden iframe; polls Alice balance; success if balance **decreases**. |
| **Attack success** | **Real** state change on CSRF DB if the forged request executes. |

**Problems**

- Timing **1500ms** `setTimeout` — flaky under load.  
- CSRF **logging** uses `context_type="challenge_simulation"` in code; normalized to **`challenge`** in logger.

---

### Challenge 4 — Command Injection

| Aspect | Detail |
|--------|--------|
| **Backend** | `POST /api/challenges/ping` — `subprocess.run(..., shell=True)`; success boolean = output contains `COMMAND_INJECTION_SUCCESS`. |
| **Frontend** | Checks same marker in response output. |
| **Attack** | **Real** command execution on API server (container). Input length capped; newlines rejected. |

**Fix:** `submit-fix-command-injection` — sandbox Dockerfile adds `iputils-ping` for this challenge only.

---

### Challenge 5 — Broken Authentication

| Aspect | Detail |
|--------|--------|
| **Backend** | `POST /api/auth/login?challenge=broken-auth` — SQLite simulation (`auth.py`). |
| **Frontend** | On `bypass_success`, **overwrites** `sessionStorage` token/role with **admin** JWT from response → **session confusion** if user navigates away without understanding. |
| **Attack success** | **Real** relative to the challenge contract (`bypass_success` true). |

**Fix:** `submit-fix-auth` → `challenge-broken-auth`.

---

### Challenge 6 — Security Misconfiguration

| Aspect | Detail |
|--------|--------|
| **Backend** | `POST /api/calc/interest` (`misconfig.py`); `GET /api/admin/config` exposes config — **any authenticated user**. Also mutates challenge state via `challenges_api.update_challenge_state` inline. |
| **Frontend** | `SecurityMiscAttackPage` probes paths; success when `GET` hits `/api/admin/config`. |
| **Attack success** | **Real** HTTP success to exposed endpoint. |

---

### Challenge 7 — Insecure Storage

| Aspect | Detail |
|--------|--------|
| **Backend** | **In-memory** dict `INSECURE_USERS` in `challenges.py` — **not durable across workers/restarts**; **not shared across multiple backend instances**. |
| **Frontend** | Dump with `secure: false`; success if any user has plaintext `password` string. |
| **Attack** | **Real** relative to in-memory store for that process lifetime. |

**Fix:** `submit-fix-storage`.

---

### Challenge 8 — Directory Traversal

| Aspect | Detail |
|--------|--------|
| **Backend** | `GET /api/challenges/traversal/read?file=&secure=` — reads under `/app/uploads` (created if missing). |
| **Frontend** | Success if response `content` looks like passwd file (`root:`, `/bin/bash`, etc.) — **heuristic**, not server-side flag. |

---

### Challenge 9 — XXE

| Aspect | Detail |
|--------|--------|
| **Backend** | `POST /api/challenges/xxe/parse` — **custom** entity extraction via regex + `Path.read_text` (not a full XML external resolver); “secure” mode blocks when entities present. |
| **Frontend** | Success if combined output fields contain passwd-like strings. |

**Note:** Vulnerable path is **simplified** vs real XXE parsers.

---

### Challenge 10 — Unvalidated Redirect

| Aspect | Detail |
|--------|--------|
| **Backend** | `GET /api/challenges/redirect?url=` → `RedirectResponse` **302**. |
| **Frontend** | Iframe navigates to crafted URL; success if final `href` includes `attack-success` + `type=redirect` **or** “external” redirect. |

**Attack success** | Mixed: **open redirect is real**; some success branches **do not require** hitting the educational success page.

---

## 5. Sandbox System (`backend/app/sandbox_runner.py`)

### 5.1 Purpose

Validate student-submitted **`app.py`** for a known challenge directory by building a **fresh Docker image** and running **`run_tests.sh`**.

### 5.2 Allowed Directories

`ALLOWED_CHALLENGE_DIRS` lists exactly **10** folder names (sql-injection, xss, csrf, …).

### 5.3 Execution Flow

1. Validate `challenge_dir` and payload size (`SANDBOX_MAX_CODE_CHARS`, default 200000).  
2. Resolve **`/app/challenges/<challenge_dir>`** — if missing → error string `Configuration Error: Challenge directory not found at ...`.  
3. Copy tree to temp dir; **overwrite `app.py`** with student code.  
4. Write inline **Dockerfile** (Python 3.9-slim, bash, `pip install -r requirements.txt`, `sed` fix for Windows CRLF on `run_tests.sh`, **CMD `bash run_tests.sh`**).  
5. **`network="scale_net"`** — must match compose network name.  
6. Resource limits: `mem_limit=256m`, `cpu_quota=50000`, `pids_limit=128`.  
7. Wait up to **`SANDBOX_RUN_TIMEOUT`** (default 25s); on timeout, kill container.  
8. Parse logs with **`_parse_test_summary`** — expects **unittest-style** `Ran N tests` and `FAILED (failures=X, errors=Y)`.  
9. **Success** iff exit code **0** and `failures==0` and `errors==0`.  
10. Remove container and image.

### 5.4 `run_tests.sh` (typical)

Challenges use shell script to start **`python app.py &`**, sleep, then **`python test_app.py`**. Many `test_app.py` files **also start gunicorn** on port 5000 → **duplicate listeners / races** (§12).

### 5.5 Issues: `_verify_fix_improvement`

- **“before_vulnerabilities”** uses failure/error counts from sandbox logs — **not** static analysis counts.  
- If **reference** `app.py` already passes tests, `before_count` can be **0**, producing **`improvement_score` 100** when both pass — may not reflect “security improvement” in human terms.  
- **Directory not found** inside API container if volumes not mounted (Compose mounts each `./challenge-*` to `/app/challenges/...` — **matches** `sandbox_runner` when using provided `docker-compose.yml`).

---

## 6. Security Logging System

### 6.1 Architecture

- **`log_security_event`** (`security_logger.py`) writes **`SecurityLog`** rows.  
- **Context normalization:** aliases `real_user_action` → `real`, `challenge_simulation` → **`challenge`**.  
- **Challenge detection:** `_is_challenge_request` forces `context_type` to **`challenge`** for paths under `/api/challenges/`, `/api/attack/`, or `/api/auth/login` **with** `challenge` query param (or payload/metadata challenge key).

### 6.2 Event Types (excerpt)

Class `SecurityEventType` includes: `LOGIN_*`, `CHALLENGE_SQLI`, `CHALLENGE_CSRF`, `CHALLENGE_AUTH`, `FIX_SUBMISSION`, `SANDBOX_EXECUTION`, `PROJECT_SCAN`, etc.

### 6.3 Challenge Event Remapping

When `context_type` resolves to **`challenge`**, `event_type` may be rewritten via `_challenge_event_for` — e.g. mapping **login-related** events to **`CHALLENGE_*`** based on endpoint and metadata, reducing misclassification of challenge traffic as pure `LOGIN_FAILED`.

### 6.4 Why CSRF / Challenge Logins Were “LOGIN_FAILED” Before

Historically, failed **real** logins always logged `LOGIN_FAILED`. **Current code** (`auth.py`):

- Uses `is_challenge_login` from `challenge` query param.  
- Failed login in challenge context logs **`CHALLENGE_AUTH`** with `context_type="challenge"` (not `real`).  
- **`is_repeated_failed_login`** only considers **`LOGIN_FAILED`** with **`context_type=="real"`** — challenge failures **do not** trigger “repeated” escalation.

### 6.5 Admin API

- **`GET /api/security/logs`** — filters: severity, event_type, user_id, **context_type** (accepts aliases), date range, pagination.  
- **`GET /api/security/logs/stats`** — `total_attacks` counts **`real`/`real_user_action`** only; `challenge_events` counts **`challenge`/`challenge_simulation`**. **Timeline** includes **all** contexts (last 100 rows) — read code before interpreting charts.

---

## 7. Scanner System

### 7.1 Upload

- **`POST /api/project/upload`** — `.zip` only, max **50MB**.  
- **`extract_zip`** whitelists extensions; blocks path traversal; skips `node_modules`; **throws** if zero files extracted.  
- **`Project`** row: `id` = hex name without `.zip`; **`owner_id`** set.

**Path resolution bug (Docker):**  
`PROJECTS_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "projects"` (`projects.py`).  

- On a **local repo** layout `.../grad-project/backend/app/api/projects.py`, `parents[3]` is **`grad-project`** → `grad-project/uploads/projects`. **Correct.**  
- In the **backend container**, `WORKDIR /app` and package layout **`/app/app/api/projects.py`** → `parents[3]` is **`/`** (filesystem root). Upload paths become **`/uploads/projects`** — **not** under the project mount, **not** persisted by default compose volumes, and **inconsistent** with host expectations.

### 7.2 Scan

- **`POST /api/project/scan?project_id=`** — walks extracted tree under `EXTRACTED_PROJECTS_DIR`, runs **`scan_file_for_vulnerabilities_detailed`** per file (`detector.py` regex rules + CSRF heuristic).  
- **`calculate_risk`**, persist **`ScanHistory`**, update **`Project`**.

### 7.3 Retrieval — `GET /api/project/{project_id}`

Returns DB metadata + **`last_scan_summary`** from latest `ScanHistory`. **Requires:**

1. `_assert_project_access` — owner must match unless admin.  
2. **On-disk folder** `EXTRACTED_PROJECTS_DIR / project_id` **must exist** — else **`404` `Project files not found`**.

**Why “can’t fetch project” / restore fails**

- **Scanner.tsx** calls `GET /api/project/{id}` on reload to confirm context — fails when:  
  - Files were never extracted to the path the API checks (Docker path bug above).  
  - Container recreated and **`/uploads` not on a volume**.  
  - **Owner mismatch** — project row exists but `owner_id` doesn’t match (older rows with null owner may behave differently — `_assert_project_access` returns early if **no** project row).

### 7.4 Rule-Based Detector

- **Per-line regex** from `scanner/rules.py`; multiple rules can match; **no** dataflow/taint analysis.  
- **Message** when empty: `"No vulnerabilities detected OR not supported by current scanner depth"`.

---

## 8. Quiz System

### 8.1 Student Quiz (`/api/quizzes/*`)

- **Practice:** `POST /api/quizzes/take` — filters `Question.topic.in_(req.topics)`, optional difficulty, **`random.sample`** up to `count`.  
- **Submit answer:** `POST /api/quizzes/submit-answer` — records `UserAnswer`; **does not** enforce assignment scope for practice.  
- **Attempts:** `POST /api/quizzes/submit-attempt` — stores score/total/time.  
- **Assignments:** `GET /api/quizzes/assignments/student` — **parses** `assigned_student_ids.split(',')` — will **throw** if column is null/empty (`.split` on `None` not guarded in router — potential **500** if bad data).

### 8.2 Instructor / Bank CRUD

- `POST/GET/PUT/DELETE` questions; `POST` assignments; AI preview `POST /api/quizzes/generate-ai-preview` proxies to **`AI_SERVICE_URL`** (default `http://ai_service:8001/generate`).

### 8.3 Dynamic Quiz (`/api/quiz/*`, `quiz_dynamic.py`)

- **`POST /api/quiz/generate`** — **does not** read DB questions; **synthesizes** MCQ-style objects from **scan findings** using `_build_question_set`.  
- **`require_role("user")`** — **students only**; admins/instructors **cannot** call this endpoint as implemented.  
- **`GET/POST /api/quiz/manage`** — parallel “manage” API mutating **`questions`** table — overlaps with `/api/quizzes/questions` — **two CRUD surfaces**.

### 8.4 What Is Weak / Not Working Well

- **Separation:** Instructors may use `InstructorQuizPage` against one API surface while students use another — easy to confuse.  
- **`delete_all_questions`** exists — destructive.  
- **Dynamic quiz** options include **intentionally wrong** “fixes” (e.g. “Base64-encode secret”) labeled correct in **payload** questions — **pedagogically risky** if treated as ground truth.  
- **Quiz → learning `accuracy`** ties to **`UserAnswer`** only — dynamic quiz may use **temporary option ids** (`StudentQuizPage` mapping) — must match how submissions are recorded (if at all).

---

## 9. Learning & Progress System

### 9.1 `user_learning_progress`

Recomputed by **`recalculate_learning_progress`**:

- **`vulnerabilities_solved`:** `COUNT(DISTINCT challenge_id)` for `user_progress` — capped at **`TOTAL_CHALLENGES` (10)**.  
- **`accuracy`:** `correct_answers / total_answers * 100` from **`user_answers`** only.  
- **`avg_time`:** average of **`quiz_attempts.time_seconds`**.  
- **`strongest_category` / `weakest_category`:** from **`compute_skills_scores`** — six **radar** buckets, each bucket covers **1–2** challenge slugs (`SKILL_BUCKETS`).  
- **`streak_days`:** derived from **distinct dates** in `user_progress.completed_at` — algorithm attempts consecutive calendar days; edge cases may not match intuitive “streak”.  
- **`learning_speed`:** `(solved / max(avg_time,1))*100` — **dimensional mix** (dimensionless hack).  
- **`retention_score`:** weighted blend of accuracy, streak cap, failed answers — **heuristic**.

### 9.2 Dashboard Logic Mismatches

- **`DashboardHomePage`:** “Defense Level” uses **`learning.level`** when loaded; fallback labels (**Novice/Apprentice/Expert/Master**) use **`progressCount`** thresholds — **not the same** algorithm as backend `level`.  
- **Progress bar:** uses **`vulnerabilities_solved`** from **`/api/stats/progress/me`** when available, else **`progressCount`** from raw **`/api/challenges/progress` row count** — if API partially fails, **numbers diverge**.  
- **XP display:** `progressCount * 100 + avg quiz %` — **arbitrary** formula, not persisted server-side.

---

## 10. Dashboard & Analytics

### 10.1 Student Dashboard (`DashboardHomePage`)

- **Welcome** uses `user_email` or **`role`** string if email missing — can look wrong.  
- **Vulnerabilities card:** `solvedLabs/totalLabs` from learning payload.  
- **Radar chart:** `skills_radar` from API — **empty array** renders empty chart if learning failed.  
- **Recent quizzes:** `/api/quizzes/attempts`.

### 10.2 Instructor (`InstructorDashboardPage` + `/api/stats/instructor/dashboard`)

- Lists students from `/api/auth/users`.  
- **Class completion:** `sum_solved / (total_students * TOTAL_CHALLENGES)` using **`UserProgress` row counts** — **not distinct** per challenge per user if data were duplicated (DB uniqueness **not** enforced in model).  
- **Per-student drill-in:** `/api/instructor/user/{id}/analytics` — same payload as student **`build_learning_progress_payload`**.  
- **Reset:** `POST /api/instructor/user/{id}/reset-progress` deletes progress, answers, attempts, learning row, challenge state.

### 10.3 Admin (`AdminDashboardPage`, `/api/stats/admin/dashboard`)

- **`fixed_vulns`:** **total count of `user_progress` rows** (not distinct vulnerabilities).  
- **`challenge_usage`:** **only** maps legacy/`sql-injection` and `xss` — **ignores other challenge types**.  
- **`attempts` estimate** is **fabricated** (`sqli_fixes * 2`) — comment in code admits estimation.

### 10.4 Data Consistency

- **Instructor vs student** analytics align **when** both call `build_learning_progress_payload` — good.  
- **Admin dashboard** metrics **do not** align with instructor/student **TOTAL_CHALLENGES** framing.

---

## 11. Frontend UI/UX Analysis

- **Challenge list** (`ChallengesListPage`): **“Success”** deep-link to `/challenges/attack-success` only for **`successTypeMap`** entries — **ids 1,2,3,4,10 only**. Challenges **5–9** get **no** Success shortcut from the grid **even if** completed.  
- **Tutorial links:** Broken Auth & Security Misc point to **`/under-construction`** — not implemented pages.  
- **ChallengeHintPanel** + **`/api/challenges/hints`** — used on some pages with **`challenge_id`** keys matching backend `_HINTS` (csrf, broken-auth, security-misc, directory-traversal, xxe, insecure-storage). **SQL/XSS/CSRF/command/redirect** may rely on different patterns — **inconsistent coverage**.  
- **Older “7” vs new “3”** framing: **10** challenges are numbered **1–10** in the UI; backend progress uses **string slugs**; `learning_tracker.LEGACY_CHALLENGE_IDS` maps numeric strings to slugs for migration.

---

## 12. Known Issues (Critical Inventory)

### Backend

| Issue | Root cause | Affected files |
|-------|------------|----------------|
| XSS comment API missing | Routes never registered; model unused | `challenges.py`, `XssAttackPage.tsx`, `models.py` |
| Upload path on Docker | `parents[3]` resolves to `/` inside container | `projects.py` |
| `csrf_accounts` table unused | CSRF lab uses external MySQL + raw SQL | `models.py`, `challenges.py` |
| Quiz assignment split fragile | CSV strings | `quizzes.py`, models |
| Sandbox double server | `run_tests.sh` + `test_app.py` both start servers | `challenge-*/run_tests.sh`, `challenge-*/test_app.py` |
| SQLi sandbox DB host | Challenge `app.py` defaults `host=db` | `challenge-sql-injection/app.py`, compose networking |

### Frontend

| Issue | Root cause | Affected files |
|-------|------------|----------------|
| XSS attack broken | POST to missing API before client “success” check | `XssAttackPage.tsx` |
| Success link partial | `successTypeMap` only 5 labs | `ChallengesListPage.tsx` |
| Defense level dual logic | Local heuristic vs API `level` | `DashboardHomePage.tsx` |
| Broken-auth overwrites session | Stores challenge JWT as main session | `BrokenAuthAttackPage.tsx` |

### Security / Teaching Fidelity

| Issue | Notes |
|-------|--------|
| JWT in sessionStorage | Stolen via XSS on any compromising page |
| Command injection | **Real** shell execution on backend host |
| “Vulnerability count” in fix feedback | Actually **test failure counts** |
| XXE backend | Regex-based file read — **not** identical to XML parser XXE |
| Insecure storage | **In-memory** dict — not a real DB |

### Fake / Heuristic Logic

| Area | Behavior |
|------|----------|
| XSS | Substring patterns — no DOM execution |
| Directory traversal / XXE | Passwd-like **string** checks on client |
| Admin challenge stats | Estimated “attempts”, partial challenge mapping |
| XP on dashboard | Client-side formula |

---

## 13. Recommendations (High Level)

1. **Implement `/api/challenges/xss/comments`** (GET/POST/DELETE) backed by `XSSComment` + DB, **or** remove DB model and **reorder** XSS page to evaluate success **before** POST (still weak pedagogically).  
2. **Fix upload path** for Docker: derive repo root from env **`UPLOAD_ROOT`** or use `parents[2]` with explicit layout checks; mount a **named volume** for `/uploads` or `/app/uploads`.  
3. **Sandbox:** unify **one** server start per `run_tests.sh`; align **DB** hostnames for challenge containers or use embedded sqlite for tests.  
4. **Unify quiz management** — single CRUD API; document which UI uses which.  
5. **Admin dashboard:** compute metrics from **`UserProgress.challenge_id`** with **full** slug map — remove fake attempt multipliers or label them **estimated**.  
6. **Challenges list:** extend **`successTypeMap`** to all **10** labs for parity.  
7. **Broken-auth page:** avoid overwriting real session; use **`sessionStorage` key** scoped to challenge or separate tab flow.

---

## Appendix A — Route Map (Quick Reference)

| Prefix | Module |
|--------|--------|
| `/api/auth` | `auth.py` |
| `/api/quizzes` | `quizzes.py` |
| `/api/challenges` | `challenges.py` |
| `/api/stats` | `stats.py` |
| `/api/messages` | `messages.py` |
| `/api` (projects, project, user/projects, …) | `projects.py`, `project_analyzer.py` |
| `/api/challenge` | `game_challenge.py` |
| `/api/calc`, `/api/admin/config` | `misconfig.py` |
| `/api/ai` | `ai_mentor.py` |
| `/api/attack` | `attack_simulator.py` |
| `/api/security` | `security_logs.py` |
| `/api/quiz` | `quiz_dynamic.py` |
| `/api/instructor` | `instructor.py` |

---

## Appendix B — Environment & Compose

- **`docker-compose.yml`** mounts `./backend` → `/app`, challenge folders → `/app/challenges/...`, **`/var/run/docker.sock`** for sandbox.  
- **Databases:** `main_db`, `challenge_db_sqli`, `challenge_db_csrf` — ports **3306, 3307, 3308** exposed to host.  
- **Frontend:** `VITE_API_URL` defaults to `http://localhost:8000` — browser calls host, not Docker service name.

---

*End of `PROJECT_DOCUMENTATION.md`.*
