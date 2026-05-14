# SCALE — Master System Documentation

**Document Title:** Complete Reverse Engineering & System Documentation  
**System Name:** SCALE (Secure Coding Learning Environment)  
**Version:** 1.0  
**Style:** Formal academic documentation; all content derived from project source code.  
**Scope:** Every implemented feature, file reference, API, database table, and workflow.

---

## 1. PROJECT OVERVIEW

### 1.1 System Name

**SCALE** — Secure Coding Learning Environment.

### 1.2 System Purpose

SCALE is a web-based **secure coding learning environment** that teaches application security through hands-on labs. The system allows students to simulate attacks on deliberately vulnerable endpoints, study tutorials, and submit code fixes that are executed in an isolated Docker sandbox and verified by automated tests. Instructors manage quiz questions and assignments; administrators manage users and view platform statistics. The system also includes a **security scanner** for uploaded project ZIPs (rule-based static analysis, risk scoring, PDF reports) and a **Red vs Blue** game mode over scanned projects.

### 1.3 Real-World Problem Solved

- **Education:** Students often learn security only in theory. SCALE provides a safe, controlled environment to exploit real vulnerabilities (SQLi, XSS, CSRF, Command Injection, Unvalidated Redirect) and then fix them with code that is automatically tested.
- **Assessment:** Instructors need to assign quizzes and track completion; the system stores quiz attempts with scores and time.
- **Governance:** New instructors require approval; admins need to approve them, create other admins, and manage users (delete, update roles).
- **Code Security:** Organizations need to scan source code for common vulnerability patterns; SCALE offers upload → scan → report (including PDF and AI-enriched feedback) and optional Red/Blue challenges.

### 1.4 Target Users

| User Type   | Role Value   | Description |
|------------|--------------|-------------|
| **Student** | `user`       | Takes challenges (attack/fix/tutorial), takes quizzes, views progress and dashboard, uses scanner, sends messages to instructors/admins. |
| **Instructor** | `instructor` | Manages question bank and assignments, views instructor dashboard, uses scanner, receives messages from students; must be approved by admin. |
| **Admin**  | `admin`      | Approves instructors, creates admins, deletes/updates users, views admin stats and project analytics, uses scanner, receives messages. |

### 1.5 System Goals

- Deliver five fully implemented security challenges (SQL Injection, XSS, CSRF, Command Injection, Unvalidated Redirect) with Attack, Fix, and Tutorial flows.
- Persist user progress (completed challenges, quiz attempts) and enforce role-based access.
- Verify fix submissions in isolated Docker containers using per-challenge test suites.
- Provide quiz practice and assignments with immediate feedback and attempt history.
- Support project upload, static vulnerability scanning, risk scoring, reporting (JSON/PDF), and optional AI mentoring and Red/Blue game.

### 1.6 Key Capabilities

- **Authentication:** Registration (email, password, role), login (JWT), instructor approval gate, session storage for token/role.
- **Challenges:** Vulnerable backend endpoints for each challenge type; frontend attack pages; fix pages with Monaco editor submitting code to sandbox; tutorial pages; progress and attack-complete marking.
- **Quizzes:** Question bank (200 seeded questions across 20 topics), topics/difficulty filters, practice quiz, assignments (instructor → students), submit answer (correctness + explanation), submit attempt (score, time), attempts list.
- **Admin:** Pending instructors list, approve, create admin, delete user, update role; admin dashboard stats (user counts, challenge usage, fixed vulns); user search.
- **Instructor:** Question CRUD, assignment create/list/delete, assignment take (questions by id), instructor dashboard stats; AI quiz preview (calls external AI service).
- **Messaging:** Unread count, conversation with a user, send message (role rules: students → instructors/admins only), contacts list.
- **Scanner:** Upload ZIP (50 MB max, whitelisted extensions), extract, list files, scan (rule-based detector + scorer + fixer), report JSON, report PDF download, scan with AI (first N findings enriched by AI mentor), user projects list, project analytics, admin overview.
- **Red/Blue Game:** Start challenge for a project (snapshot vulns), red team attack (score on unfixed vuln), blue team fix (mark fixed, score by severity), leaderboard, status with remaining risk.

### 1.7 Demo Scenario

**What the demo shows:** A typical user journey from landing → login → dashboard → challenges list → one full challenge (e.g. Unvalidated Redirect: attack then fix) → quiz and progress, plus optional scanner and admin flows.

**User journey during the demo:**

1. **Visitor** opens the app at `/` (LandingPage). Sees branding and links to Login/Register.
2. **Register** (optional): `/register` → submit email, password, role (user/instructor). If instructor, account is pending until admin approves.
3. **Login:** `/login` → submit email (username) and password. Backend returns JWT and role. Frontend stores token, role, user_id, user_email in sessionStorage and redirects by role: admin → `/admin/stats`, instructor → `/instructor/dashboard`, else → `/home`.
4. **Dashboard (student):** `/home` (DashboardHomePage). Shows welcome, defense level, vulnerabilities patched (X/20), current score (XP), quiz results; fetches `/api/challenges/progress` and `/api/quizzes/attempts`. Links to challenges and quiz.
5. **Challenges list:** `/challenges` (ChallengesListPage). Grid of challenge cards (SQLi, XSS, CSRF, Command Injection, Broken Auth, Security Misc, Insecure Storage, Directory Traversal, XXE, Unvalidated Redirect). Each card has Simulate / Fix / Tutorial (or Under Construction). Progress is fetched from `/api/challenges/progress`; completed challenges show a “Success” link.
6. **Unvalidated Redirect — Attack:** User clicks “Simulate” for Unvalidated Redirect → `/challenges/10/attack` (RedirectAttackPage). Reads instructions, enters target URL (e.g. attack-success page), clicks “Verify Redirect”. Frontend builds link `GET /api/challenges/redirect?url=...`, loads it in a hidden iframe; on redirect to attack-success, calls `POST /api/challenges/mark-attack-complete?challenge_type=redirect` and navigates to attack-success.
7. **Unvalidated Redirect — Fix:** User clicks “Try the Fix” or goes to `/challenges/10/fix` (RedirectFixPage). Sees vulnerable Flask code in Monaco editor. User edits code to allow only allowlisted relative paths and reject absolute URLs (e.g. with `urlparse`, `abort(400)`). Clicks “Submit Fix”. Frontend sends `POST /api/challenges/submit-fix-redirect` with `{ code }`. Backend runs sandbox (copy challenge-redirect, overwrite app.py, build Docker image, run tests). If tests pass, backend marks progress and returns success; frontend shows ResultModal with logs.
8. **Quiz:** User goes to `/quiz` (StudentQuizPage). Chooses practice (topics, count) or assignment. Questions loaded from `/api/quizzes/take` or `/api/quizzes/assignments/{id}/take`. User answers each; each answer sent to `POST /api/quizzes/submit-answer`. Timer runs in frontend. On finish, `POST /api/quizzes/submit-attempt` with title, score, total, time_seconds. Attempts appear on dashboard.
9. **Optional — Scanner:** User goes to `/scanner` (Scanner). Uploads a .zip → `POST /api/project/upload`. Then triggers `POST /api/project/scan?project_id=...`. Results show findings and risk. User can request report PDF or AI-enriched scan.
10. **Optional — Admin:** Admin logs in → `/admin/stats` (AdminStatsPage). Sees total users, active exploits, fixed vulns, pie chart (user distribution), bar chart (challenge usage). Can go to `/admin/dashboard` (AdminDashboardPage) to approve instructors, create admin, delete user, update role.

**Order of actions in the demo:** Landing → Login → Home → Challenges → Redirect Attack → Redirect Fix (submit code, see result) → (optional) Quiz, Scanner, or Admin flows.

---

## 2. SYSTEM ARCHITECTURE

### 2.1 Architectural Style

The system follows a **layered architecture** with a clear separation:

- **Presentation layer:** React SPA (Vite, TypeScript) with React Router, role-based route protection.
- **API layer:** FastAPI backend exposing REST endpoints; JWT for authentication; Pydantic for request/response validation.
- **Business logic layer:** Implemented in FastAPI route handlers and shared modules (crud, sandbox_runner, scanner, ai).
- **Data layer:** SQLAlchemy ORM, MySQL (main DB + challenge DBs for SQLi and CSRF); Docker for sandbox execution.

There is no formal MVC folder naming; the backend is organized by **routers** (auth, challenges, quizzes, stats, messages, projects, game_challenge) and shared **models**, **schemas**, **db**, and **crud**.

### 2.2 Backend Structure

**Purpose:** Serve REST API, run vulnerable challenge endpoints, run sandbox verification, persist data, perform scanning and reporting.

**Responsibilities:** Authentication and authorization; challenge attack endpoints and fix submission; quiz and assignment CRUD and attempt recording; progress and attack-complete marking; admin and instructor stats; messaging; project upload, extraction, scanning, reporting, AI enrichment; Red/Blue game.

**Main components and files:**

| Component        | Path | Purpose |
|-----------------|------|---------|
| Application entry | `backend/app/main.py` | FastAPI app, CORS, router registration, startup DB retry and table creation. |
| Database        | `backend/app/db/database.py` | Engine, SessionLocal, Base, get_db. URL: `mysql+pymysql://user:password@main_db/scale_db`. |
| Models          | `backend/app/models.py` | SQLAlchemy models: User, UserProgress, XSSComment, Challenge, Question, QuestionOption, UserAnswer, QuizAssignment, QuizAttempt, Message, Project, ScanHistory, Team, TeamMember, GameChallenge, ChallengeVulnerability, RedTeamAction, BlueTeamFix. |
| Schemas         | `backend/app/schemas.py` | Pydantic models for API request/response. |
| CRUD            | `backend/app/crud.py` | get_user_by_email, create_user, approve_user, delete_user, update_user_role. |
| Auth API        | `backend/app/api/auth.py` | register, login, search users, admin pending, approve, create-admin, delete user, update role. |
| Challenges API  | `backend/app/api/challenges.py` | vulnerable-login, csrf reset/accounts/transfer, ping, redirect, submit-fix-*, progress, mark-attack-complete. |
| Quizzes API     | `backend/app/api/quizzes.py` | topics, questions CRUD, take, submit-answer, submit-attempt, attempts; assignments CRUD, take assignment; generate-ai-preview. |
| Stats API       | `backend/app/api/stats.py` | admin dashboard, instructor dashboard. |
| Messages API    | `backend/app/api/messages.py` | unread-count, with/{user_id}, send, contacts. |
| Projects API    | `backend/app/api/projects.py` | project/upload, project/files, project/scan, project/report, project/report/pdf, project/scan/ai, user/projects, project/analytics, admin/overview. |
| Game challenge API | `backend/app/api/game_challenge.py` | start, red/attack, blue/fix, leaderboard, status. |
| Sandbox runner  | `backend/app/sandbox_runner.py` | run_in_sandbox(code, challenge_dir): copy challenge, overwrite app.py, build Docker image, run container on scale_net, parse logs for success/failure. |
| Scanner         | `backend/app/scanner/detector.py`, `rules.py`, `fixer.py`, `scorer.py`, `report_generator.py` | Rule-based detection, severity, attach fixes, risk calculation, JSON/PDF report. |
| AI              | `backend/app/ai/mentor.py` | generate_ai_security_feedback (used by project/scan/ai). |
| Seed            | `backend/seed_db.py` | wait_for_db, create_all, seed_users (admin@scale.edu, instructor@scale.edu), generate_questions (200 questions), seed questions and options. |

### 2.3 Frontend Structure

**Purpose:** Provide UI for all user roles, consume backend APIs, enforce protected routes, and display challenge/quiz/scanner/admin flows.

**Responsibilities:** Landing, login, register; role-based redirect after login; dashboard (home, admin stats, instructor dashboard); challenges list and per-challenge attack/fix/tutorial pages; quiz (student and instructor); messages; scanner (upload, scan, results, report); admin panel (user management); sidebar and layout.

**Main components and files:**

| Component   | Path | Purpose |
|------------|------|---------|
| Entry      | `frontend/src/main.tsx`, `App.tsx` | React root, Router, Routes (public, protected by role). |
| Layout     | `frontend/src/components/MainLayout.tsx`, `Sidebar.tsx` | MainLayout with collapsible Sidebar; Outlet for child routes. |
| Protection | `frontend/src/components/ProtectedRoute.tsx` | Reads token/role from sessionStorage; redirects to login if no token; redirects to role default if role not in allowedRoles. |
| Pages      | `frontend/src/pages/*.tsx` | Landing, Login, Register, DashboardHome, ChallengesList, *AttackPage, *FixPage, *TutorialPage, AttackSuccess, Messages, Admin*, Instructor*, StudentQuizPage, Scanner, UnderConstructionPage, etc. |
| Shared     | `frontend/src/components/ResultModal.tsx` | Modal for fix submission success/failure and logs. |

### 2.4 Database Structure

- **Main database (`main_db`, scale_db):** Used by FastAPI and SQLAlchemy. Tables created by `models.Base.metadata.create_all(bind=engine)` at startup and in seed_db. Contains users, user_progress, questions, question_options, user_answers, quiz_assignments, quiz_attempts, challenges, xss_comments, messages, projects, scan_history, teams, team_members, game_challenges, challenge_vulnerabilities, red_team_actions, blue_team_fixes. The `db_init/init.sql` also creates `challenge_users` in scale_db (legacy/alternate use).
- **Challenge DBs:**  
  - **challenge_db_sqli** (testdb): Used by vulnerable SQLi login in challenges.py; schema from `challenge-sql-injection/users.sql`.  
  - **challenge_db_csrf** (csrfdb): Used by CSRF reset/accounts/transfer; schema from `challenge-csrf/csrf.sql` (e.g. accounts table).

### 2.5 API Structure

All APIs are under `/api` with the following prefixes:

- `/api/auth` — auth router (register, login, users, admin/*).
- `/api/quizzes` — quizzes router (topics, questions, assignments, take, submit-answer, submit-attempt, attempts, generate-ai-preview).
- `/api/challenges` — challenges router (vulnerable-login, csrf/*, ping, redirect, submit-fix-*, progress, mark-attack-complete).
- `/api/stats` — stats router (admin/dashboard, instructor/dashboard).
- `/api/messages` — messages router (unread-count, with/{user_id}, send, contacts).
- `/api/project/*`, `/api/user/projects`, `/api/project/analytics`, `/api/admin/overview` — projects router (mounted at `/api`).
- `/api/challenge` — game_challenge router (start, red/attack, blue/fix, leaderboard, status).

### 2.6 Frontend → Backend → Database Flow

1. **User action (e.g. Login):** User submits form on LoginPage → axios POST `/api/auth/login` with username (email) and password.
2. **Backend:** auth.login receives body, crud.get_user_by_email, verify_password; if instructor and not is_approved → 403; else create_access_token (JWT with sub=email, role, exp), return token and user_id, role, email.
3. **Database:** Only read from `users` table (no write on login).
4. **Frontend:** Stores token, role, user_id, email in sessionStorage; redirects by role.

5. **User action (e.g. Submit Fix):** User clicks Submit on RedirectFixPage → axios POST `/api/challenges/submit-fix-redirect` with Authorization Bearer and body `{ code }`.
6. **Backend:** submit_fix_redirect receives CodeSubmission, get_current_user; sandbox_runner.run_in_sandbox(code, "challenge-redirect"); on success, mark_challenge_complete(db, user_id, "redirect"); return { success, logs }.
7. **Database:** Read user from token; write UserProgress row if tests pass.
8. **Frontend:** Shows ResultModal with success/failure and logs.

---

## 3. COMPLETE FEATURE BREAKDOWN

### 3.1 Authentication

**Feature name:** User registration.  
**Purpose:** Allow new users to create an account with email, password, and role (user or instructor).  
**Business logic:** If email exists → 400. If role is admin → 403. Hash password with bcrypt. Create User; if role is instructor and not admin-created, set is_approved=False.  
**User flow:** RegisterPage form → POST /api/auth/register.  
**Files:** `backend/app/api/auth.py` (register), `backend/app/crud.py` (create_user, get_user_by_email), `frontend/src/pages/RegisterPage.tsx`.  
**Database:** `users` (insert).  
**APIs:** POST /api/auth/register.  
**Validations:** Email uniqueness; role not admin.  
**Error handling:** 400 email already registered; 403 admin registration restricted.

**Feature name:** User login.  
**Purpose:** Authenticate by email and password; return JWT and user info.  
**Business logic:** Find user by email; verify password with passlib; if instructor and not is_approved → 403; else create JWT (sub=email, role, exp), return access_token, user_id, role, email.  
**User flow:** LoginPage form → POST /api/auth/login → store token/role in sessionStorage, redirect by role.  
**Files:** `backend/app/api/auth.py` (login, create_access_token), `frontend/src/pages/LoginPage.tsx`.  
**Database:** `users` (read).  
**APIs:** POST /api/auth/login.  
**Validations:** Credentials.  
**Error handling:** 401 incorrect email or password; 403 account pending approval.

**Feature name:** Role-based route protection.  
**Purpose:** Restrict UI routes by role.  
**Business logic:** ProtectedRoute reads token and role from sessionStorage; no token → Navigate to /login; role not in allowedRoles → Navigate to admin/stats, instructor/dashboard, or /home.  
**Files:** `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/App.tsx` (Route element with allowedRoles).  
**No backend/database.**

### 3.2 Admin Management

**Feature name:** List pending instructors.  
**Purpose:** Allow admin to see instructors awaiting approval.  
**Business logic:** Query User where role=instructor and is_approved=False.  
**Files:** `backend/app/api/auth.py` (get_pending_instructors), `frontend/src/pages/AdminDashboardPage.tsx`.  
**Database:** `users`. **APIs:** GET /api/auth/admin/pending. **Auth:** get_current_admin.

**Feature name:** Approve instructor.  
**Purpose:** Set is_approved=True for an instructor.  
**Business logic:** crud.approve_user(db, user_id).  
**Files:** `backend/app/api/auth.py` (approve_instructor), `backend/app/crud.py` (approve_user).  
**Database:** `users` (update). **APIs:** POST /api/auth/admin/approve/{user_id}.

**Feature name:** Create admin.  
**Purpose:** Create a new user with role admin (email + password).  
**Business logic:** If email exists → 400; create_user with role=admin, is_admin_created=True.  
**Files:** `backend/app/api/auth.py` (create_admin_internal), `backend/app/crud.py` (create_user).  
**Database:** `users` (insert). **APIs:** POST /api/auth/admin/create-admin.

**Feature name:** Delete user (ban).  
**Purpose:** Permanently remove a user.  
**Business logic:** If user_id == current_user.id → 400; else crud.delete_user.  
**Files:** `backend/app/api/auth.py` (delete_user_endpoint), `backend/app/crud.py` (delete_user).  
**Database:** `users` (delete). **APIs:** DELETE /api/auth/admin/users/{user_id}.

**Feature name:** Update user role.  
**Purpose:** Change a user’s role.  
**Business logic:** Find user, set role, commit.  
**Files:** `backend/app/api/auth.py` (update_role_endpoint), `backend/app/crud.py` (update_user_role).  
**Database:** `users` (update). **APIs:** PUT /api/auth/admin/users/{user_id}/role.

### 3.3 Security Challenges (Attack / Fix / Tutorial)

**Feature name:** SQL Injection challenge.  
**Purpose:** Simulate vulnerable login and allow students to submit a fixed version.  
**Attack:** POST /api/challenges/vulnerable-login (username, password) → string-concatenated SQL against challenge_db_sqli.  
**Fix:** POST /api/challenges/submit-fix with code → sandbox challenge-sql-injection.  
**Files:** `backend/app/api/challenges.py`, `frontend/src/pages/SqlInjectionAttackPage.tsx`, `SqlInjectionFixPage.tsx`, `SqlInjectionTutorialPage.tsx`, `challenge-sql-injection/app.py`, `test_app.py`, `run_tests.sh`.  
**Database:** challenge_db_sqli (attack); main_db user_progress (fix success).  
**APIs:** POST /api/challenges/vulnerable-login, POST /api/challenges/submit-fix.

**Feature name:** XSS challenge.  
**Purpose:** Simulate XSS and allow students to submit fixed code.  
**Attack/Fix:** Similar pattern; submit-fix-xss, challenge-xss.  
**Files:** `backend/app/api/challenges.py`, `frontend/src/pages/XssAttackPage.tsx`, `XssFixPage.tsx`, `XssTutorialPage.tsx`, `challenge-xss/`.  
**APIs:** POST /api/challenges/submit-fix-xss; XSS comments endpoints if implemented.

**Feature name:** CSRF challenge.  
**Purpose:** Simulate vulnerable transfer and allow fix.  
**Attack:** GET /api/challenges/csrf/reset; GET /api/challenges/csrf/accounts; POST /api/challenges/csrf/transfer (form).  
**Fix:** POST /api/challenges/submit-fix-csrf, challenge-csrf.  
**Files:** `backend/app/api/challenges.py`, `frontend/src/pages/CsrfAttackPage.tsx`, `CsrfFixPage.tsx`, `challenge-csrf/`.  
**Database:** challenge_db_csrf (accounts).  
**APIs:** GET/POST /api/challenges/csrf/*, POST /api/challenges/submit-fix-csrf.

**Feature name:** Command Injection challenge.  
**Purpose:** Vulnerable ping endpoint; fix in sandbox.  
**Attack:** POST /api/challenges/ping with host (e.g. "8.8.8.8; echo COMMAND_INJECTION_SUCCESS").  
**Fix:** POST /api/challenges/submit-fix-command-injection, challenge-command-injection.  
**Files:** `backend/app/api/challenges.py`, `frontend/src/pages/CommandChallengePage.tsx`, `CommandInjectionAttackPage.tsx`, `CommandInjectionFixPage.tsx`, `challenge-command-injection/`.  
**APIs:** POST /api/challenges/ping, POST /api/challenges/submit-fix-command-injection.

**Feature name:** Unvalidated Redirect challenge.  
**Purpose:** Vulnerable redirect to any URL; fix by allowlisting relative paths.  
**Attack:** GET /api/challenges/redirect?url=... (302 to url).  
**Fix:** POST /api/challenges/submit-fix-redirect, challenge-redirect (app.py validates with urlparse and ALLOWED_PATHS).  
**Files:** `backend/app/api/challenges.py`, `frontend/src/pages/RedirectChallengePage.tsx`, `RedirectAttackPage.tsx`, `RedirectFixPage.tsx`, `RedirectTutorialPage.tsx`, `challenge-redirect/app.py`, `test_app.py`.  
**APIs:** GET /api/challenges/redirect, POST /api/challenges/submit-fix-redirect.

**Feature name:** Progress and mark attack complete.  
**Purpose:** Track which challenges the user has completed (fix or attack).  
**Business logic:** GET /api/challenges/progress returns UserProgress for current user. POST /api/challenges/mark-attack-complete?challenge_type=... inserts UserProgress if not exists.  
**Files:** `backend/app/api/challenges.py` (get_my_progress, mark_attack_complete, mark_challenge_complete).  
**Database:** `user_progress`. **APIs:** GET /api/challenges/progress, POST /api/challenges/mark-attack-complete.

### 3.4 Quizzes and Assignments

**Feature name:** Question bank and CRUD.  
**Purpose:** Store and manage multiple-choice questions with topics, difficulty, options.  
**Files:** `backend/app/api/quizzes.py` (create_question, get_questions, update_question, delete_question, delete_all_questions), `backend/app/models.py` (Question, QuestionOption), `backend/seed_db.py` (generate_questions, 200 questions).  
**Database:** `questions`, `question_options`. **APIs:** GET/POST /api/quizzes/questions, PUT/DELETE /api/quizzes/questions/{q_id}, DELETE /api/quizzes/questions.

**Feature name:** Assignments.  
**Purpose:** Instructor creates assignment with title, question_ids, student_ids.  
**Business logic:** QuizAssignment stores question_ids and assigned_student_ids as comma-separated strings.  
**Files:** `backend/app/api/quizzes.py` (create_assign, get_instr_assigns, delete_assign, get_student_assigns, take_assign_quiz).  
**Database:** `quiz_assignments`. **APIs:** POST /api/quizzes/assignments, GET /api/quizzes/assignments/instructor, GET /api/quizzes/assignments/student, GET /api/quizzes/assignments/{id}/take.

**Feature name:** Practice quiz.  
**Purpose:** Get random questions by topics and count.  
**Business logic:** Filter by topic (and optional difficulty), limit 100, random.sample(count).  
**APIs:** POST /api/quizzes/take.

**Feature name:** Submit answer and submit attempt.  
**Purpose:** Record each answer and final attempt with score and time.  
**Business logic:** submit_answer: find option, insert UserAnswer, return correct and explanation. submit_attempt: insert QuizAttempt.  
**Files:** `backend/app/api/quizzes.py` (submit_answer, submit_quiz_attempt, get_my_quiz_attempts).  
**Database:** `user_answers`, `quiz_attempts`. **APIs:** POST /api/quizzes/submit-answer, POST /api/quizzes/submit-attempt, GET /api/quizzes/attempts.

**Feature name:** AI quiz preview.  
**Purpose:** Call external AI service for generated question preview.  
**Business logic:** POST to ai_service:8001/generate with topic, count, difficulty, skill_focus.  
**Files:** `backend/app/api/quizzes.py` (generate_ai), `ai_service/`. **APIs:** POST /api/quizzes/generate-ai-preview.

### 3.5 Statistics Dashboards

**Feature name:** Admin dashboard stats.  
**Purpose:** Aggregate user counts, challenge counts, fixed vulns, pie chart (user distribution), bar chart (challenge usage).  
**Files:** `backend/app/api/stats.py` (get_admin_dashboard_stats), `frontend/src/pages/AdminStatsPage.tsx`.  
**Database:** users, challenges, user_progress. **APIs:** GET /api/stats/admin/dashboard.

**Feature name:** Instructor dashboard stats.  
**Purpose:** Total students, quizzes, questions, assignments, fixes, avg completion, class performance placeholders.  
**Files:** `backend/app/api/stats.py` (get_instructor_stats), `frontend/src/pages/InstructorDashboardPage.tsx`.  
**APIs:** GET /api/stats/instructor/dashboard.

### 3.6 Messaging

**Feature name:** Unread count, conversation, send, contacts.  
**Purpose:** In-app messaging with role rules (students → instructors/admins only).  
**Files:** `backend/app/api/messages.py`, `frontend/src/pages/MessagesPage.tsx`.  
**Database:** `messages`. **APIs:** GET /api/messages/unread-count, GET /api/messages/with/{user_id}, POST /api/messages/send, GET /api/messages/contacts.

### 3.7 Project Upload and Scanner

**Feature name:** Upload project ZIP.  
**Purpose:** Accept .zip (max 50 MB), extract whitelisted extensions (.php, .js, .py, .java, .html, .css), block path traversal.  
**Files:** `backend/app/api/projects.py` (upload_project, extract_zip), `frontend/src/pages/Scanner.tsx`.  
**APIs:** POST /api/project/upload.

**Feature name:** List files, scan project.  
**Purpose:** Enumerate source files; run detector (rules.py regexes), attach fixes (fixer), calculate risk (scorer); persist Project and ScanHistory.  
**Files:** `backend/app/api/projects.py` (list_project_files, scan_project), `backend/app/scanner/detector.py`, `rules.py`, `fixer.py`, `scorer.py`.  
**Database:** `projects`, `scan_history`. **APIs:** GET /api/project/files, POST /api/project/scan.

**Feature name:** Report JSON and PDF.  
**Purpose:** Generate security report and optionally PDF download.  
**Files:** `backend/app/api/projects.py` (get_project_report, get_project_report_pdf), `backend/app/scanner/report_generator.py`.  
**APIs:** GET /api/project/report, GET /api/project/report/pdf.

**Feature name:** Scan with AI.  
**Purpose:** Run normal scan, enrich first N findings with AI mentor feedback.  
**Files:** `backend/app/api/projects.py` (scan_project_with_ai), `backend/app/ai/mentor.py`.  
**APIs:** POST /api/project/scan/ai.

**Feature name:** User projects list, project analytics, admin overview.  
**Purpose:** List projects owned by current user; risk/vuln trends per project; global admin analytics.  
**Files:** `backend/app/api/projects.py` (list_user_projects, project_analytics, admin_overview).  
**Database:** `projects`, `scan_history`. **APIs:** GET /api/user/projects, GET /api/project/analytics, GET /api/admin/overview.

### 3.8 Red vs Blue Game

**Feature name:** Start challenge, red attack, blue fix, leaderboard, status.  
**Purpose:** Snapshot vulnerabilities for a project; red team scores by exploiting unfixed vulns; blue team scores by marking vulns fixed (severity-based points); track scores and remaining risk.  
**Files:** `backend/app/api/game_challenge.py`, `backend/app/models.py` (Team, TeamMember, GameChallenge, ChallengeVulnerability, RedTeamAction, BlueTeamFix).  
**Database:** `teams`, `team_members`, `game_challenges`, `challenge_vulnerabilities`, `red_team_actions`, `blue_team_fixes`.  
**APIs:** POST /api/challenge/start, POST /api/challenge/red/attack, POST /api/challenge/blue/fix, GET /api/challenge/leaderboard, GET /api/challenge/status.

### 3.9 User Search

**Feature name:** Search/list users.  
**Purpose:** Optional query filter by email; used by admin/instructor UIs.  
**Files:** `backend/app/api/auth.py` (search_users). **APIs:** GET /api/auth/users?query=.

---

## 4. DEMO WALKTHROUGH (STEP-BY-STEP)

**Step 1 — User opens app**  
- **User:** Opens browser at `/`.  
- **System:** Renders LandingPage (`frontend/src/pages/LandingPage.tsx`).  
- **API:** None.  
- **DB:** None.  
- **User sees:** Landing with links to Login/Register.

**Step 2 — User logs in**  
- **User:** Clicks Login, enters email and password, submits.  
- **System:** LoginPage calls POST `/api/auth/login` with `{ username, password }`.  
- **Controller:** `backend/app/api/auth.py` login(); crud.get_user_by_email; verify_password; create_access_token; return token, user_id, role, email.  
- **DB:** SELECT from `users` by email.  
- **User sees:** Redirect to /home (or /admin/stats or /instructor/dashboard); Sidebar shows role.

**Step 3 — User views dashboard**  
- **User:** Lands on /home (or role default).  
- **System:** DashboardHomePage fetches GET `/api/challenges/progress` and GET `/api/quizzes/attempts` with Bearer token.  
- **Controller:** challenges.get_my_progress; quizzes.get_my_quiz_attempts.  
- **DB:** SELECT from `user_progress`, `quiz_attempts` for user_id.  
- **User sees:** Welcome, defense level, vulnerabilities count, score, quiz results, links to challenges and quiz.

**Step 4 — User opens challenges list**  
- **User:** Clicks Labs & Attacks or navigates to /challenges.  
- **System:** ChallengesListPage fetches GET `/api/challenges/progress`.  
- **Controller:** challenges.get_my_progress.  
- **DB:** SELECT from `user_progress`.  
- **User sees:** Grid of challenge cards; completed challenges show “Success” link.

**Step 5 — User performs Redirect attack**  
- **User:** Clicks Simulate on Unvalidated Redirect; enters target URL (e.g. attack-success); clicks Verify Redirect.  
- **System:** RedirectAttackPage builds URL `/api/challenges/redirect?url=...`, loads in iframe; on load checks location; if success, POST `/api/challenges/mark-attack-complete?challenge_type=redirect`, then navigate to attack-success.  
- **Controller:** GET /api/challenges/redirect (vulnerable_redirect) returns 302 to url; POST mark_attack_complete calls mark_challenge_complete.  
- **DB:** INSERT into `user_progress` (if not exists).  
- **User sees:** “Redirect successful” and redirect to attack-success page.

**Step 6 — User submits Redirect fix**  
- **User:** Goes to /challenges/10/fix; edits code to validate redirect target (allowlist, reject absolute URLs); clicks Submit Fix.  
- **System:** RedirectFixPage POST `/api/challenges/submit-fix-redirect` with `{ code }` and Bearer token.  
- **Controller:** submit_fix_redirect; sandbox_runner.run_in_sandbox(code, "challenge-redirect"); on success mark_challenge_complete.  
- **DB:** INSERT into `user_progress` when tests pass.  
- **User sees:** ResultModal with success/failure and test logs.

**Step 7 — User takes a quiz**  
- **User:** Goes to /quiz; selects practice (topics, count) or assignment; answers questions; finishes quiz.  
- **System:** StudentQuizPage GET take or GET assignments/{id}/take; for each answer POST submit-answer; on end POST submit-attempt with title, score, total, time_seconds.  
- **Controller:** quizzes.take_quiz or take_assign_quiz; submit_answer; submit_quiz_attempt.  
- **DB:** SELECT questions/options; INSERT user_answers, quiz_attempts.  
- **User sees:** Questions, correct/incorrect and explanation per answer, final score and time; attempts on dashboard.

---

## 5. DATABASE ANALYSIS

### 5.1 Tables (from models.py and usage)

**users**  
- **Purpose:** User accounts (students, instructors, admins).  
- **Columns:** id (PK), email (unique, indexed), hashed_password, role (String 50), is_approved (Boolean, default True).  
- **Relationships:** UserProgress, UserAnswer, QuizAttempt; Message (sender_id, receiver_id).  
- **Why:** Single table for all roles; is_approved gates instructors.

**user_progress**  
- **Purpose:** Record which challenges a user has completed (fix or attack marked complete).  
- **Columns:** id (PK), user_id (FK users.id), challenge_id (String 50), completed_at (DateTime).  
- **Relationships:** user (User).  
- **Why:** One row per user per challenge type; used for dashboard and challenge list badges.

**xss_comments**  
- **Purpose:** Store comments for XSS challenge (if used).  
- **Columns:** id (PK), author, content (Text).  
- **Why:** Persist comments for stored XSS simulation.

**challenges**  
- **Purpose:** Metadata for challenges (used in stats).  
- **Columns:** id (PK), title, description.  
- **Why:** Seed and reference for admin dashboard counts.

**questions**  
- **Purpose:** Quiz question bank.  
- **Columns:** id (PK), text (Text), type, topic, difficulty, skill_focus, explanation (Text).  
- **Relationships:** options (QuestionOption), answers (UserAnswer).  
- **Why:** Multiple-choice questions with topic/difficulty for practice and assignments.

**question_options**  
- **Purpose:** Answer options for each question.  
- **Columns:** id (PK), question_id (FK questions.id), text, is_correct (Boolean).  
- **Relationships:** question (Question).  
- **Why:** One-to-many options per question.

**user_answers**  
- **Purpose:** Record each submitted quiz answer.  
- **Columns:** id (PK), user_id (FK users.id), question_id (FK questions.id), selected_option_id (FK question_options.id), is_correct (Boolean), timestamp.  
- **Relationships:** user (User), question (Question).  
- **Why:** Per-answer history and grading.

**quiz_assignments**  
- **Purpose:** Instructor-created assignments (title, question set, student set).  
- **Columns:** id (PK), title, instructor_id (FK users.id), assigned_student_ids (Text, comma-separated), question_ids (Text, comma-separated), created_at.  
- **Why:** Flexible assignment without extra tables; student list and question list as CSV.

**quiz_attempts**  
- **Purpose:** Completed quiz attempts with score and time.  
- **Columns:** id (PK), user_id (FK users.id), assignment_id (FK quiz_assignments.id, nullable), title, score, total, time_seconds, completed_at.  
- **Relationships:** user (User).  
- **Why:** Dashboard and history; assignment_id links to assigned quiz when applicable.

**messages**  
- **Purpose:** In-app messages between users.  
- **Columns:** id (PK), sender_id (FK users.id), receiver_id (FK users.id), content (Text), created_at, is_read (Boolean).  
- **Why:** Simple two-party conversation with read state.

**projects**  
- **Purpose:** Uploaded/extracted project metadata and latest scan summary.  
- **Columns:** id (String 100, PK), name, owner_id (FK users.id, nullable), created_at, last_scan_date, latest_risk_score, latest_risk_level, total_scans.  
- **Why:** One row per extracted project; id matches folder name.

**scan_history**  
- **Purpose:** History of scans per project.  
- **Columns:** id (PK), project_id (FK projects.id), scan_date, total_vulnerabilities, risk_score, risk_level, vuln_summary (Text, JSON).  
- **Relationships:** project (Project).  
- **Why:** Trend and analytics over time.

**teams**  
- **Purpose:** Red/Blue teams for game challenges.  
- **Columns:** id (PK), name, type ('red'|'blue'), created_at.  
- **Relationships:** members (TeamMember).  
- **Why:** One red and one blue team per game challenge.

**team_members**  
- **Purpose:** Link users to teams.  
- **Columns:** id (PK), team_id (FK teams.id), user_id (FK users.id).  
- **Why:** Many-to-many user–team (optional for future expansion).

**game_challenges**  
- **Purpose:** One Red vs Blue game instance per project.  
- **Columns:** id (PK), project_id (String), status, created_at, red_team_id (FK teams.id), blue_team_id (FK teams.id), red_score, blue_score.  
- **Relationships:** ChallengeVulnerability, RedTeamAction, BlueTeamFix.  
- **Why:** Snapshot of vulns and scores per game.

**challenge_vulnerabilities**  
- **Purpose:** Snapshot of each vulnerability in a game challenge.  
- **Columns:** id (PK), challenge_id (FK game_challenges.id), file, line, vulnerability_type, severity, is_fixed (Boolean).  
- **Why:** Red/Blue score off fixed/unfixed state without changing source.

**red_team_actions**  
- **Purpose:** Log of red team exploit attempts.  
- **Columns:** id (PK), challenge_id (FK game_challenges.id), vulnerability_id (FK challenge_vulnerabilities.id), exploit_attempted, success, timestamp.  
- **Why:** Audit and scoring.

**blue_team_fixes**  
- **Purpose:** Log of blue team fix actions.  
- **Columns:** id (PK), challenge_id (FK game_challenges.id), vulnerability_id (FK challenge_vulnerabilities.id), fixed (Boolean), timestamp.  
- **Why:** Audit and scoring.

### 5.2 Relationships Summary

- **One-to-many:** User → UserProgress, UserAnswer, QuizAttempt; Question → QuestionOption, UserAnswer; QuizAssignment → (conceptual) attempts; Project → ScanHistory; GameChallenge → ChallengeVulnerability, RedTeamAction, BlueTeamFix; Team → TeamMember.  
- **Many-to-one:** UserProgress, UserAnswer, QuizAttempt, Message → User; QuestionOption, UserAnswer → Question; ScanHistory → Project; ChallengeVulnerability, RedTeamAction, BlueTeamFix → GameChallenge.  
- **Design rationale:** Single users table with role; progress and attempts normalized by user_id; assignments denormalized with CSV columns for simplicity; scanner and game use projects and snapshots for analytics and scoring.

---

## 6. API DOCUMENTATION

### 6.1 Auth (`/api/auth`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|---------|----------|------------|
| /register | POST | Register user | Body: UserCreate (email, password, role?) | User | auth.register |
| /login | POST | Login | Body: LoginAttempt (username, password) | access_token, user_id, role, email | auth.login |
| /users | GET | Search users | Query: query (optional) | List UserSearchResponse | auth.search_users |
| /admin/pending | GET | Pending instructors | — | List UserSearchResponse | auth.get_pending_instructors |
| /admin/approve/{user_id} | POST | Approve instructor | Path: user_id | Updated user | auth.approve_instructor |
| /admin/create-admin | POST | Create admin | Body: UserCreateAdmin (email, password) | User | auth.create_admin_internal |
| /admin/users/{user_id} | DELETE | Delete user | Path: user_id | message | auth.delete_user_endpoint |
| /admin/users/{user_id}/role | PUT | Update role | Path: user_id, Body: { role } | Updated user | auth.update_role_endpoint |

**Validation:** Email uniqueness on register; role != admin on self-register; login 401/403; admin endpoints require get_current_admin.

### 6.2 Challenges (`/api/challenges`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|---------|----------|------------|
| /vulnerable-login | POST | SQLi simulation | Body: LoginAttempt | message, user or 401/400 | challenges.execute_vulnerable_login |
| /csrf/reset | POST | Reset CSRF accounts | — | message | challenges.reset_csrf_accounts |
| /csrf/accounts | GET | List CSRF accounts | — | List CSRFAccountResponse | challenges.get_csrf_accounts |
| /csrf/transfer | POST | Vulnerable transfer | Form: to_user, amount | message or error | challenges.vulnerable_transfer |
| /ping | POST | Command injection sim | Body: PingRequest (host) | output, success | challenges.vulnerable_ping |
| /redirect | GET | Open redirect sim | Query: url | 302 Redirect | challenges.vulnerable_redirect |
| /submit-fix | POST | Submit SQLi fix | Body: CodeSubmission, Auth | success, logs | challenges.submit_fix_sql |
| /submit-fix-xss | POST | Submit XSS fix | Body: CodeSubmission, Auth | success, logs | challenges.submit_fix_xss |
| /submit-fix-csrf | POST | Submit CSRF fix | Body: CodeSubmission, Auth | success, logs | challenges.submit_fix_csrf |
| /submit-fix-command-injection | POST | Submit cmd fix | Body: CodeSubmission, Auth | success, logs | challenges.submit_fix_command_injection |
| /submit-fix-redirect | POST | Submit redirect fix | Body: CodeSubmission, Auth | success, logs | challenges.submit_fix_redirect |
| /progress | GET | My progress | Auth | List ProgressResponse | challenges.get_my_progress |
| /mark-attack-complete | POST | Mark attack done | Query: challenge_type, Auth | { ok: true } | challenges.mark_attack_complete |

**Validation:** challenge_type in allowed set; auth required for progress and submit-fix and mark-attack-complete.

### 6.3 Quizzes (`/api/quizzes`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|---------|----------|------------|
| /topics | GET | List topics | — | List[str] | quizzes.get_topics |
| /questions | GET | List questions | Query: topic?, difficulty? | List QuestionResponse | quizzes.get_questions |
| /questions | POST | Create question | Body: QuestionCreate | QuestionResponse | quizzes.create_question |
| /questions/{q_id} | PUT | Update question | Path: q_id, Body: QuestionUpdate | message | quizzes.update_question |
| /questions/{q_id} | DELETE | Delete question | Path: q_id | message | quizzes.delete_question |
| /questions | DELETE | Delete all questions | — | message | quizzes.delete_all_questions |
| /assignments | POST | Create assignment | Body: AssignmentCreate, Auth | AssignmentResponse | quizzes.create_assign |
| /assignments/instructor | GET | My assignments | Auth | List AssignmentResponse | quizzes.get_instr_assigns |
| /assignments/student | GET | Assigned to me | Auth | List AssignmentResponse | quizzes.get_student_assigns |
| /assignments/{id} | DELETE | Delete assignment | Path: id | message | quizzes.delete_assign |
| /assignments/{id}/take | GET | Questions for assignment | Path: id | List QuestionResponse | quizzes.take_assign_quiz |
| /take | POST | Practice quiz | Body: QuizRequest (topics, count, difficulty?, mode) | List QuestionResponse | quizzes.take_quiz |
| /submit-answer | POST | Submit one answer | Body: AnswerSubmit, Auth | correct, explanation | quizzes.submit_answer |
| /submit-attempt | POST | Submit attempt | Body: QuizAttemptSubmit, Auth | QuizAttemptResponse | quizzes.submit_quiz_attempt |
| /attempts | GET | My attempts | Auth | List QuizAttemptResponse | quizzes.get_my_quiz_attempts |
| /generate-ai-preview | POST | AI preview | Body: AIGenerationRequest, Auth | AI response | quizzes.generate_ai |

### 6.4 Stats (`/api/stats`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|----------|----------|------------|
| /admin/dashboard | GET | Admin stats | — | total_users, active_exploits, fixed_vulns, user_distribution, challenge_usage, system_status | stats.get_admin_dashboard_stats |
| /instructor/dashboard | GET | Instructor stats | — | total_students, quizzes_created, questions_in_bank, class_performance, avg_completion_rate | stats.get_instructor_stats |

### 6.5 Messages (`/api/messages`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|---------|----------|------------|
| /unread-count | GET | Unread count | Auth | { unread: number } | messages.get_unread_count |
| /with/{user_id} | GET | Conversation | Path: user_id, Auth | List of messages | messages.get_conversation |
| /send | POST | Send message | Body: { receiver_id, content }, Auth | message object | messages.send_message |
| /contacts | GET | List contacts | Auth | List { id, email, role } | messages.list_contacts |

### 6.6 Projects (`/api`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|---------|----------|------------|
| /project/upload | POST | Upload ZIP | Form: file (.zip, max 50MB) | message, project_folder | projects.upload_project |
| /project/files | GET | List files | Query: project_id | project_id, total_files, files | projects.list_project_files |
| /project/scan | POST | Scan project | Query: project_id | findings, summary, risk, DB updated | projects.scan_project |
| /project/report | GET | Report JSON | Query: project_id | report object | projects.get_project_report |
| /project/report/pdf | GET | Report PDF | Query: project_id | FileResponse PDF | projects.get_project_report_pdf |
| /project/scan/ai | POST | Scan + AI | Query: project_id | findings with ai_analysis | projects.scan_project_with_ai |
| /user/projects | GET | My projects | Auth | total_projects, projects | projects.list_user_projects |
| /project/analytics | GET | Project trends | Query: project_id | risk_trend, vulnerability_trend | projects.project_analytics |
| /admin/overview | GET | Admin overview | Auth (admin) | total_projects, total_scans, average_risk_score, high_risk_projects, top_vulnerability_types | projects.admin_overview |

### 6.7 Game Challenge (`/api/challenge`)

| Endpoint | Method | Purpose | Request | Response | Controller |
|----------|--------|---------|---------|----------|------------|
| /start | POST | Start game | Query: project_id | challenge_id, red_team_id, blue_team_id, initial_vulnerabilities | game_challenge.start_challenge |
| /red/attack | POST | Red attack | Body: AttackRequest (challenge_id, vulnerability_id) | success, red_team_score | game_challenge.red_team_attack |
| /blue/fix | POST | Blue fix | Body: FixRequest (challenge_id, vulnerability_id) | blue_team_score, current_risk | game_challenge.blue_team_fix |
| /leaderboard | GET | Leaderboard | Query: challenge_id | red_team_score, blue_team_score, status | game_challenge.challenge_leaderboard |
| /status | GET | Status | Query: challenge_id | remaining_vulnerabilities, fixed_vulnerabilities, scores, score_difference, current_risk | game_challenge.challenge_status |

---

## 7. USER INTERFACE ANALYSIS

### 7.1 Pages

| Page | File | Purpose | User Actions | Backend Connections |
|------|------|---------|--------------|---------------------|
| Landing | LandingPage.tsx | Entry, branding | Navigate to Login/Register | None |
| Login | LoginPage.tsx | Authenticate | Submit email/password; redirect by role | POST /api/auth/login |
| Register | RegisterPage.tsx | Create account | Submit email, password, role | POST /api/auth/register |
| Home (Dashboard) | DashboardHomePage.tsx | Student dashboard | View stats; links to challenges, quiz | GET progress, GET attempts |
| Challenges list | ChallengesListPage.tsx | List all challenges | Click Simulate/Fix/Tutorial per challenge | GET /api/challenges/progress |
| SQLi Attack/Fix/Tutorial | SqlInjection*.tsx | SQLi challenge | Attack: submit credentials; Fix: submit code | vulnerable-login, submit-fix, progress |
| XSS Attack/Fix/Tutorial | Xss*.tsx | XSS challenge | Same pattern | submit-fix-xss, progress |
| CSRF Attack/Fix | Csrf*.tsx | CSRF challenge | Reset, view accounts, transfer; fix code | csrf/*, submit-fix-csrf |
| Command Injection | CommandChallengePage.tsx, *AttackPage, *FixPage | Cmd injection | Ping with host; fix code | ping, submit-fix-command-injection |
| Redirect | RedirectChallengePage, *AttackPage, *FixPage, *TutorialPage | Open redirect | Enter URL, verify; fix code | redirect, submit-fix-redirect, mark-attack-complete |
| Broken Auth / Security Misc | BrokenAuth*.tsx, SecurityMisc*.tsx | Placeholder challenges | Links to under-construction or specific flow | As implemented |
| Attack Success | AttackSuccessPage.tsx | Post-attack success | View message; link back | Optional mark-attack-complete |
| Student Quiz | StudentQuizPage.tsx | Take quiz | Practice or assignment; answer; submit attempt | take, submit-answer, submit-attempt, attempts |
| Instructor Quiz | InstructorQuizPage.tsx | Manage questions/assignments | CRUD questions; create/delete assignments; AI preview | questions, assignments, generate-ai-preview |
| Instructor Dashboard | InstructorDashboardPage.tsx | Instructor stats | View stats | GET /api/stats/instructor/dashboard |
| Admin Stats | AdminStatsPage.tsx | Admin charts | View user/challenge stats | GET /api/stats/admin/dashboard |
| Admin Dashboard | AdminDashboardPage.tsx | User management | Approve, create admin, delete, update role; search users | auth admin endpoints |
| Messages | MessagesPage.tsx | Inbox/conversations | Select contact; view thread; send message | unread-count, with/{id}, send, contacts |
| Scanner | Scanner.tsx | Upload and scan | Upload ZIP; scan; view results; report PDF/AI | project/upload, project/scan, report, scan/ai |
| Under Construction | UnderConstructionPage.tsx | Placeholder | — | — |

### 7.2 Components

- **MainLayout:** Wraps protected content; Sidebar + margin; Outlet for child routes.  
- **Sidebar:** Role-based nav links (Dashboard, Labs & Attacks, Scanner, Messages, Quiz, Instructor Zone, Admin Panel, Security Logs); unread count from GET /api/messages/unread-count; logout (sessionStorage.clear, navigate /login).  
- **ProtectedRoute:** Reads token and role; redirects to /login or role default when not allowed.  
- **ResultModal:** Displays success/failure and logs (used by fix pages).

### 7.3 Navigation Structure

- **Public:** /, /login, /register.  
- **Student (user):** /home, /challenges, /challenges/1|2|3|4|10/…, /quiz, /messages, /scanner.  
- **Instructor:** /instructor/dashboard, /instructor/quiz; also /scanner, /messages.  
- **Admin:** /admin/stats, /admin/dashboard, /admin/logs; also /scanner, /messages.  
- **Catch-all:** * → Navigate to /.

### 7.4 Forms and Interactions

- Login/Register: controlled inputs, submit to auth API, error display.  
- Fix pages: Monaco editor (code), Submit button → submit-fix-* → ResultModal.  
- Attack pages: inputs (e.g. URL, host, credentials), Verify/Submit → vulnerable endpoint and optional mark-attack-complete.  
- Quiz: topic/count or assignment selection; per-question submit-answer; final submit-attempt.  
- Scanner: file input (ZIP), Upload → project_id; Scan → results; optional Report PDF / AI scan.  
- Admin: user list/search; approve, create admin, delete, update role (forms or buttons).  
- Messages: contact list; conversation view; send text.

---

## 8. FUNCTIONAL REQUIREMENTS (CONSOLIDATED)

*(Same as in SYSTEM_DOCUMENTATION.md; abbreviated here. Each FR has Actor, Input, Process, Output.)*

- **FR-1** User registration (email, password, role; instructor pending).  
- **FR-2** User login (JWT, role, redirect).  
- **FR-3** Role-based route protection (token, allowedRoles).  
- **FR-4–FR-8** Admin: pending list, approve, create admin, delete user, update role.  
- **FR-9–FR-14** Challenge attacks: SQLi login, CSRF reset/accounts/transfer, ping, redirect.  
- **FR-15–FR-19** Submit fix (SQLi, XSS, CSRF, Command Injection, Redirect).  
- **FR-20** Get my progress. **FR-21** Mark attack complete.  
- **FR-22–FR-27** Quiz: topics, questions CRUD, delete all.  
- **FR-28** Generate AI preview. **FR-29–FR-34** Assignments create/list/delete, student assigns, take assignment, practice quiz.  
- **FR-35** Submit answer. **FR-36** Submit quiz attempt. **FR-37** Get my quiz attempts.  
- **FR-38** Admin dashboard stats. **FR-39** Instructor dashboard stats.  
- **FR-40** Search/list users. **FR-41** Sandbox fix verification. **FR-42** Database startup. **FR-43** Seed initial data.  
- **FR-44** Messaging: unread count, conversation, send, contacts (role rules).  
- **FR-45** Project upload (ZIP, extract). **FR-46** List files, scan project (detector, scorer, fixer). **FR-47** Report JSON/PDF. **FR-48** Scan with AI. **FR-49** User projects, analytics, admin overview.  
- **FR-50** Red/Blue: start, red attack, blue fix, leaderboard, status.

---

## 9. NON-FUNCTIONAL REQUIREMENTS

*(Same categories as SYSTEM_DOCUMENTATION.md; abbreviated.)*

- **Performance:** API response time; sandbox execution 30–120s with loading feedback.  
- **Security:** JWT for protected operations; bcrypt passwords; CORS; role-based access.  
- **Usability:** Responsive layout; clear feedback for fix/quiz.  
- **Scalability:** Stateless API; ephemeral sandbox per run.  
- **Availability:** DB connection retry on startup.  
- **Maintainability:** Modular routers, Pydantic schemas.  
- **Portability:** Docker Compose deployment.  
- **Reliability:** Idempotent progress marking.  
- **Compatibility:** Modern browser; agreed API contract (VITE_API_URL, Bearer, JSON).

---

## 10. DATA FLOW DIAGRAMS (TEXT)

### 10.1 Context Diagram (Level 0)

**External entities:** Student (E1), Instructor (E2), Admin (E3), AI Service (E4), Docker (E5).  
**System:** SCALE (single box).  
**Flows:** E1/E2/E3 → SCALE: login, register, challenge inputs, fix code, quiz answers/attempts, messages, upload/scan requests, admin actions. SCALE → E1/E2/E3: token, pages, progress, results, reports. SCALE → E4: generate request. E4 → SCALE: generated content. SCALE → E5: build/run container. E5 → SCALE: logs.

### 10.2 Level 1

**Processes:** P1 Authenticate/Authorize; P2 Manage Users (Admin); P3 Run Challenge Attacks; P4 Verify Fixes (Sandbox); P5 Manage Progress/Attacks; P6 Manage Questions/Assignments; P7 Run Quiz & Attempts; P8 Aggregate Statistics; P9 Call AI Service; P10 Messaging; P11 Project Upload/Scan/Report; P12 Red/Blue Game.  
**Data stores:** D1 users; D2 user_progress; D3 questions; D4 question_options; D5 user_answers; D6 quiz_assignments; D7 quiz_attempts; D8 challenges; D9 xss_comments; D10 messages; D11 projects; D12 scan_history; D13–D18 teams, game_challenges, challenge_vulnerabilities, red_team_actions, blue_team_fixes; external challenge_db_sqli, challenge_db_csrf.  
**Flows:** As in SECTION 6 and existing SYSTEM_DOCUMENTATION.md DFD Level 1; add flows for P10 (messages), P11 (upload, scan, report), P12 (start, attack, fix).

---

## 11. SYSTEM WORKFLOWS

### 11.1 User Registration Workflow

1. User opens /register.  
2. Submits email, password, role (user or instructor).  
3. Frontend POST /api/auth/register.  
4. Backend: if email exists → 400; if role admin → 403; hash password; create User (is_approved=False for instructor); return User.  
5. Frontend may redirect to login or show success.

### 11.2 Login Workflow

1. User opens /login, submits email and password.  
2. Frontend POST /api/auth/login.  
3. Backend: get user by email; verify password; if instructor and not approved → 403; create JWT; return token, user_id, role, email.  
4. Frontend stores token, role, user_id, email in sessionStorage; redirects to /admin/stats, /instructor/dashboard, or /home.

### 11.3 Fix Submission Workflow

1. User edits code on a Fix page (e.g. RedirectFixPage).  
2. Clicks Submit; frontend POST /api/challenges/submit-fix-redirect (or other submit-fix-*) with Bearer token and { code }.  
3. Backend: get_current_user; sandbox_runner.run_in_sandbox(code, "challenge-redirect"): copy challenge dir, overwrite app.py, write Dockerfile, build image, run container on scale_net, capture logs; success = no FAILED/Error/Traceback in logs.  
4. If success: mark_challenge_complete(db, user_id, "redirect"); return { success: true, logs }.  
5. Frontend shows ResultModal with success and logs (or failure and error logs).

### 11.4 Quiz Taking Workflow

1. User goes to /quiz; selects practice (topics, count) or an assignment.  
2. Frontend GET /api/quizzes/take (POST body) or GET /api/quizzes/assignments/{id}/take.  
3. Backend returns list of QuestionResponse.  
4. For each answer user submits: POST /api/quizzes/submit-answer (question_id, selected_option_id); backend inserts UserAnswer, returns correct and explanation.  
5. On quiz end: POST /api/quizzes/submit-attempt (title, score, total, time_seconds, assignment_id?); backend inserts QuizAttempt; frontend shows score and links to dashboard.

### 11.5 Admin Approve Instructor Workflow

1. Admin opens /admin/dashboard; frontend GET /api/auth/admin/pending.  
2. Backend returns list of users with role=instructor and is_approved=False.  
3. Admin clicks Approve for a user; frontend POST /api/auth/admin/approve/{user_id}.  
4. Backend: crud.approve_user(db, user_id) sets is_approved=True; return user.  
5. Instructor can now log in without 403.

### 11.6 Project Scan Workflow

1. User opens /scanner; selects .zip file; clicks Upload.  
2. Frontend POST /api/project/upload (FormData file).  
3. Backend: validate .zip, max 50MB; save to uploads/projects; extract to uploads/extracted_projects/{id}; return project_folder/project_id.  
4. User clicks Scan; frontend POST /api/project/scan?project_id=...  
5. Backend: scan_project_files; scan_project_for_vulnerabilities (detector + fixer); calculate_risk; create/update Project and ScanHistory; return findings, summary, risk.  
6. Frontend displays results; user may request GET /api/project/report or /api/project/report/pdf or POST /api/project/scan/ai.

---

## 12. ASSUMPTIONS AND LIMITATIONS

### 12.1 Assumptions

- Users have a modern browser with sessionStorage and JavaScript.  
- Backend has access to Docker socket (or equivalent) for sandbox.  
- MySQL (main_db, challenge_db_sqli, challenge_db_csrf) is reachable and initialized.  
- JWT secret and DB credentials are provided via configuration.  
- Email is the unique login identifier.  
- New instructors have is_approved=False until admin approves.  
- One progress record per user per challenge type is sufficient.  
- Quiz timer is client-side; backend trusts time_seconds.  
- Frontend can reach backend at configured API URL; CORS allows it.  
- AI service is optional; if down, only AI preview is affected.

### 12.2 Limitations

- Sandbox requires Docker; no Docker means no fix verification.  
- Sandbox runs are sequential per request; high concurrency may queue.  
- Challenge DBs are separate; backup must include them.  
- XSS comments endpoints may be missing or partial.  
- Stats mapping (e.g. challenge_id '1','2') is partly hardcoded.  
- No password reset or email verification.  
- Logout is sessionStorage clear (single tab).  
- Scanner is rule-based (regex); no taint or full context.

### 12.3 Security Risks

- Weak or default JWT/DB credentials.  
- MySQL or Docker down affects core features.  
- Many simultaneous sandbox runs can exhaust resources.  
- Student code runs in containers; isolation limits but does not eliminate risk.

### 12.4 Design Trade-offs

- Assignment student/list stored as CSV for simplicity vs normalized table.  
- Progress is “completed” flag per challenge type (no versioning).  
- Scanner uses simple regex rules for speed and clarity vs deeper analysis.

---

## 13. FUTURE IMPROVEMENTS

- **Security:** Externalize secrets; add rate limiting; optional CSRF tokens for state-changing APIs.  
- **Scalability:** Queue for sandbox jobs; optional separate worker pool; cache for stats.  
- **Features:** Password reset; email verification; more challenges (Broken Auth, Security Misc full flows); XSS comments API; full Red/Blue UI.  
- **Scanner:** Taint analysis or AST-based rules; more vulnerability types; configurable rules.  
- **UX:** Real-time messaging (WebSocket); better error messages; accessibility.  
- **Ops:** Health checks; structured logging; metrics; DB migrations (e.g. Alembic).

---

*End of Master System Documentation. All content is derived from the project source code and configuration.*
