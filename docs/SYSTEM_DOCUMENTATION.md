# SCALE — Formal System Documentation

**Document Title:** System Analysis and Architecture Documentation  
**System Name:** SCALE (Secure Coding Learning Environment)  
**Version:** 1.0  
**Style:** Formal academic documentation; all content derived from project source code.

---

## 1. SYSTEM OVERVIEW

### 1.1 What the System Does

SCALE is a web-based **secure coding learning environment** that teaches application security through hands-on challenges. The system allows:

- **Students (users)** to simulate attacks on deliberately vulnerable endpoints, study tutorials, and submit code fixes that are run in an isolated sandbox and verified by automated tests.
- **Instructors** to manage quiz questions, create quiz assignments for students, and view instructor dashboards.
- **Admins** to manage users (approve instructors, create admins, ban users, update roles), view statistics dashboards, and oversee the platform.

The application exposes **five implemented security challenges** (SQL Injection, XSS, CSRF, Command Injection, Unvalidated Redirect), each with an **Attack** (simulate exploit), **Fix** (submit patched code), and **Tutorial** (learning) flow. Progress is stored per user. A **quiz** subsystem supports practice and assigned quizzes, with scores and completion time recorded. The backend runs vulnerable endpoints and fix verification; the frontend provides the UI and calls the APIs.

### 1.2 Main Actors

| Actor | Description |
|-------|-------------|
| **Student (User)** | Logged-in user with role `user`. Can access home dashboard, challenges list, attack/fix/tutorial pages, quiz (practice and assignments), and view own progress and quiz attempts. |
| **Instructor** | Logged-in user with role `instructor`. Can access instructor dashboard, create/manage quiz questions and assignments, view instructor statistics. New instructors require admin approval (`is_approved`). |
| **Admin** | Logged-in user with role `admin`. Can access admin stats dashboard, admin dashboard (user management), approve pending instructors, create other admins, delete (ban) users, update user roles. |
| **External Systems** | **AI Service** (optional): backend calls `http://ai_service:8001/generate` for quiz AI preview. **Docker daemon**: backend uses Docker to run sandbox containers for fix verification. **MySQL databases**: main app DB (`main_db`), SQL injection challenge DB (`challenge_db_sqli`), CSRF challenge DB (`challenge_db_csrf`). |

### 1.3 Main Subsystems / Modules

| Subsystem | Location | Purpose |
|-----------|----------|---------|
| **Authentication & Authorization** | `backend/app/api/auth.py`, `backend/app/crud.py`, `frontend` login/register, `ProtectedRoute` | Registration, login (JWT), role-based access, instructor approval, admin user management. |
| **Challenges API** | `backend/app/api/challenges.py` | Vulnerable endpoints (SQLi login, CSRF transfer, ping, redirect), XSS/fix sandbox submission, progress, mark-attack-complete. |
| **Sandbox Runner** | `backend/app/sandbox_runner.py` | Copies challenge folder, overwrites `app.py` with student code, builds and runs Docker image, runs tests; returns success/failure and logs. |
| **Challenge Sandboxes** | `challenge-sql-injection/`, `challenge-xss/`, `challenge-csrf/`, `challenge-redirect/`, `challenge-command-injection/` | Each contains `app.py` (vulnerable template), `test_app.py`, `run_tests.sh`, `requirements.txt`; used for fix verification. |
| **Quizzes API** | `backend/app/api/quizzes.py` | Questions CRUD, topics, practice/assignment take, submit-answer, submit-attempt, attempts list; calls AI service for preview. |
| **Statistics API** | `backend/app/api/stats.py` | Admin dashboard stats (user counts, challenge counts, fixed vulns, charts data); instructor dashboard stats. |
| **Frontend — Student** | `frontend/src/pages/`: DashboardHomePage, ChallengesListPage, *AttackPage, *FixPage, *TutorialPage, AttackSuccessPage, StudentQuizPage | Dashboard, challenges list with per-user progress, attack/fix/tutorial flows, quiz with timer and attempt submission. |
| **Frontend — Instructor** | InstructorDashboardPage, InstructorQuizPage | Dashboard and quiz/assignment management. |
| **Frontend — Admin** | AdminStatsPage, AdminDashboardPage | Stats visualization and user management. |
| **Database & Models** | `backend/app/models.py`, `backend/app/db/database.py` | Users, UserProgress, XSSComment, Challenge, Question, QuestionOption, UserAnswer, QuizAssignment, QuizAttempt; main DB and challenge DBs. |

### 1.4 Overall Workflow (Simple Language)

1. **Visitor** lands on the app, can register or log in. Registration can be as student or instructor; instructors start as pending until an admin approves.
2. **After login**, the user is sent to a role-specific entry (e.g. home for students, instructor dashboard for instructors, admin stats for admins). The frontend stores token and role in session storage; protected routes check token and allowed roles.
3. **Student workflow:** From the home dashboard they see progress and quiz summary. They open the challenges list, choose a challenge (e.g. SQL Injection), then either **Simulate** (attack page calls vulnerable API; success can be marked via mark-attack-complete), **Fix** (edit code in browser, submit to backend; sandbox runs tests and progress is updated if tests pass), or **Tutorial** (read-only learning).
4. **Quiz workflow:** Student picks practice (topic/count) or an assignment. Questions are fetched; they answer one by one (each answer submitted to submit-answer). A timer runs in the frontend. On quiz end, frontend sends score and time to submit-attempt; attempts are stored and shown on dashboard.
5. **Instructor workflow:** Manages questions and assignments, views instructor dashboard stats.
6. **Admin workflow:** Approves instructors, creates admins, deletes/updates users, views admin stats.

---

## 2. FUNCTIONAL REQUIREMENTS (FR)

*(All requirements below are extracted from the project; no features are invented.)*

---

**FR-1: User registration**  
**Description:** Allow a new user to register with email, password, and role (user or instructor). Admin role cannot be self-registered.  
**Input:** Email, password, role (optional, default `user`).  
**Process:** Validate email not already in DB; hash password (bcrypt); create User. If role is instructor, set `is_approved=False`; otherwise `is_approved=True`.  
**Output:** Created User (id, email, role, is_approved).  
**Actor:** Anonymous (then becomes User/Instructor).

---

**FR-2: User login**  
**Description:** Authenticate user by email (username) and password; return JWT and user info.  
**Input:** username (email), password.  
**Process:** Look up user by email; verify password with bcrypt; if instructor and not approved, return 403; else create JWT (sub=email, role, exp), return token and user_id, role, email.  
**Output:** access_token, token_type, user_id, role, email.  
**Actor:** Any registered user.

---

**FR-3: Role-based route protection**  
**Description:** Restrict UI routes by role using token and stored role.  
**Input:** Session storage (token, role); route allowedRoles.  
**Process:** If no token, redirect to login. If role not in allowedRoles, redirect to role default (admin→admin/stats, instructor→instructor/dashboard, else→home).  
**Output:** Render child route or redirect.  
**Actor:** All logged-in users (enforced by frontend ProtectedRoute).

---

**FR-4: Admin — list pending instructors**  
**Description:** Return list of instructors who are not yet approved.  
**Input:** None (auth: admin).  
**Process:** Query User where role=instructor and is_approved=False.  
**Output:** List of users (id, email, role, is_approved).  
**Actor:** Admin.

---

**FR-5: Admin — approve instructor**  
**Description:** Set an instructor’s is_approved to True.  
**Input:** user_id (path).  
**Process:** Find user by id, set is_approved=True, commit.  
**Output:** Updated user.  
**Actor:** Admin.

---

**FR-6: Admin — create admin**  
**Description:** Create a new user with role admin (email + password only).  
**Input:** email, password (UserCreateAdmin).  
**Process:** If email exists return 400; create user with role=admin, is_approved=True.  
**Output:** Created User.  
**Actor:** Admin.

---

**FR-7: Admin — delete user (ban)**  
**Description:** Permanently delete a user by id. Admin cannot delete self.  
**Input:** user_id (path).  
**Process:** If user_id == current_user.id return 400; else delete user and commit.  
**Output:** Success message.  
**Actor:** Admin.

---

**FR-8: Admin — update user role**  
**Description:** Change a user’s role.  
**Input:** user_id (path), role (body).  
**Process:** Find user, set role, commit.  
**Output:** Updated user.  
**Actor:** Admin.

---

**FR-9: Execute vulnerable SQLi login**  
**Description:** Intentionally vulnerable login using string-concatenated SQL for challenge simulation.  
**Input:** username, password (JSON).  
**Process:** Build SQL string, execute against challenge_db_sqli; return success or 401/400.  
**Output:** message, user (if success); else HTTP error.  
**Actor:** Student (attack simulation).

---

**FR-10: Reset CSRF challenge accounts**  
**Description:** Reset Alice balance to 1000 and Bob to 0 in CSRF DB.  
**Input:** None.  
**Process:** UPDATE accounts in challenge_db_csrf; commit.  
**Output:** Message with balances.  
**Actor:** Student (via CSRF attack page).

---

**FR-11: Get CSRF accounts**  
**Description:** Return username and balance for all accounts in CSRF DB.  
**Input:** None.  
**Process:** SELECT from accounts in challenge_db_csrf.  
**Output:** List of {username, balance}.  
**Actor:** Student (CSRF attack page).

---

**FR-12: Execute vulnerable CSRF transfer**  
**Description:** Vulnerable transfer endpoint (no CSRF token) for challenge.  
**Input:** to_user, amount (form).  
**Process:** Check Alice balance, recipient exists; UPDATE both accounts in challenge_db_csrf; commit.  
**Output:** Success message or HTTP error.  
**Actor:** Student (attack simulation).

---

**FR-13: Execute vulnerable ping (command injection)**  
**Description:** Run ping with user-supplied host via shell for challenge.  
**Input:** host (JSON).  
**Process:** subprocess.run("ping -c 1 {host}", shell=True); return stdout+stderr and whether COMMAND_INJECTION_SUCCESS is in output.  
**Output:** output, success (boolean).  
**Actor:** Student (attack simulation).

---

**FR-14: Vulnerable redirect**  
**Description:** Redirect to any URL supplied in query for open-redirect challenge.  
**Input:** url (query).  
**Process:** Return 302 RedirectResponse(url).  
**Output:** HTTP 302 to given URL.  
**Actor:** Student (attack simulation).

---

**FR-15: Submit fix (SQL Injection)**  
**Description:** Run student’s code in sandbox for challenge-sql-injection; record progress if tests pass.  
**Input:** code (JSON), auth token.  
**Process:** sandbox_runner.run_in_sandbox(code, "challenge-sql-injection"); if success, mark_challenge_complete(user, "sql-injection"); return success and logs.  
**Output:** success (boolean), logs (string).  
**Actor:** Student (authenticated).

---

**FR-16: Submit fix (XSS)**  
**Description:** Same as FR-15 for challenge-xss and challenge_id "xss".  
**Input:** code, auth token.  
**Process:** Sandbox run; on success mark "xss".  
**Output:** success, logs.  
**Actor:** Student.

---

**FR-17: Submit fix (CSRF)**  
**Description:** Same for challenge-csrf and "csrf".  
**Input:** code, auth token.  
**Process:** Sandbox run; on success mark "csrf".  
**Output:** success, logs.  
**Actor:** Student.

---

**FR-18: Submit fix (Command Injection)**  
**Description:** Same for challenge-command-injection and "command-injection".  
**Input:** code, auth token.  
**Process:** Sandbox run; on success mark "command-injection".  
**Output:** success, logs.  
**Actor:** Student.

---

**FR-19: Submit fix (Redirect)**  
**Description:** Same for challenge-redirect and "redirect".  
**Input:** code, auth token.  
**Process:** Sandbox run; on success mark "redirect".  
**Output:** success, logs.  
**Actor:** Student.

---

**FR-20: Get my progress**  
**Description:** Return list of completed challenges for the current user.  
**Input:** Auth token.  
**Process:** Query UserProgress for current_user.id; order by completed_at.  
**Output:** List of {challenge_id, completed_at}.  
**Actor:** Student (and dashboard).

---

**FR-21: Mark attack complete**  
**Description:** Record that the current user completed an attack simulation for a given challenge type.  
**Input:** challenge_type (query: sql-injection|xss|csrf|command-injection|redirect), auth token.  
**Process:** If challenge_type allowed, mark_challenge_complete(current_user, challenge_type).  
**Output:** {ok: true}.  
**Actor:** Student (frontend after successful attack).

---

**FR-22: Get quiz topics**  
**Description:** Return distinct question topics from DB.  
**Input:** None.  
**Process:** Query Question.topic.distinct().  
**Output:** List of topic strings.  
**Actor:** Instructor/frontend.

---

**FR-23: Create question**  
**Description:** Add a new question with options to the bank.  
**Input:** text, type, topic, difficulty, skill_focus, explanation, options[{text, is_correct}].  
**Process:** Insert Question; insert QuestionOption for each option; commit.  
**Output:** QuestionResponse (full question with options).  
**Actor:** Instructor (auth required in practice; endpoint itself has no Depends(get_current_user) in provided code but is under /api/quizzes).

---

**FR-24: Get questions**  
**Description:** List questions optionally filtered by topic and difficulty.  
**Input:** topic (query optional), difficulty (query optional).  
**Process:** Query Question with filters; return all matching.  
**Output:** List of QuestionResponse.  
**Actor:** Instructor/student (quiz flows).

---

**FR-25: Update question**  
**Description:** Update text, topic, difficulty, explanation of a question.  
**Input:** q_id (path), body (QuestionUpdate).  
**Process:** Find question; update fields; commit.  
**Output:** {message: "Updated"}.  
**Actor:** Instructor.

---

**FR-26: Delete question**  
**Description:** Delete a question by id (and cascade options/answers as per model).  
**Input:** q_id (path).  
**Process:** Delete UserAnswer for question; delete Question; commit.  
**Output:** {message: "Deleted"}.  
**Actor:** Instructor.

---

**FR-27: Delete all questions**  
**Description:** Remove all user answers, question options, and questions.  
**Input:** None.  
**Process:** Delete in order UserAnswer, QuestionOption, Question; commit.  
**Output:** {message: "All questions deleted"}.  
**Actor:** Instructor.

---

**FR-28: Generate AI preview**  
**Description:** Call external AI service to generate quiz preview.  
**Input:** topic, count, difficulty, skill_focus (optional).  
**Process:** POST to ai_service:8001/generate; return response.  
**Output:** AI service response (e.g. generated questions preview).  
**Actor:** Instructor (authenticated).

---

**FR-29: Create assignment**  
**Description:** Create a quiz assignment with title, question_ids, and assigned_student_ids.  
**Input:** title, student_ids[], question_ids[]; auth.  
**Process:** Create QuizAssignment (instructor_id=current user, store ids as comma-separated); commit.  
**Output:** AssignmentResponse (id, title, instructor_id, created_at).  
**Actor:** Instructor.

---

**FR-30: Get instructor assignments**  
**Description:** List assignments created by the current instructor.  
**Input:** Auth token.  
**Process:** Query QuizAssignment where instructor_id=current_user.id.  
**Output:** List of AssignmentResponse.  
**Actor:** Instructor.

---

**FR-31: Delete assignment**  
**Description:** Delete an assignment by id.  
**Input:** id (path).  
**Process:** Delete QuizAssignment; commit.  
**Output:** {message: "Deleted"}.  
**Actor:** Instructor.

---

**FR-32: Get student assignments**  
**Description:** List assignments where current user’s id is in assigned_student_ids.  
**Input:** Auth token.  
**Process:** Query all assignments; filter where str(user.id) in assigned_student_ids.split(',').  
**Output:** List of AssignmentResponse.  
**Actor:** Student.

---

**FR-33: Take assignment quiz**  
**Description:** Return questions for an assignment by id.  
**Input:** id (path).  
**Process:** Load assignment; parse question_ids; return Question list.  
**Output:** List of QuestionResponse.  
**Actor:** Student.

---

**FR-34: Take practice quiz**  
**Description:** Return random questions by topics and optional difficulty.  
**Input:** topics[], count, difficulty (optional), mode.  
**Process:** Query Question by topic (and difficulty); limit 100; random.sample(count).  
**Output:** List of QuestionResponse.  
**Actor:** Student.

---

**FR-35: Submit answer**  
**Description:** Record one quiz answer and return correctness and explanation.  
**Input:** question_id, selected_option_id; auth.  
**Process:** Find option; check is_correct; insert UserAnswer; return correct and question explanation.  
**Output:** correct (boolean), explanation (string).  
**Actor:** Student.

---

**FR-36: Submit quiz attempt**  
**Description:** Store a completed quiz attempt (score, total, time_seconds, title, optional assignment_id).  
**Input:** assignment_id (optional), title, score, total, time_seconds; auth.  
**Process:** Insert QuizAttempt for current user; commit.  
**Output:** QuizAttemptResponse (id, title, score, total, time_seconds, completed_at).  
**Actor:** Student (frontend on quiz end).

---

**FR-37: Get my quiz attempts**  
**Description:** List current user’s quiz attempts, newest first.  
**Input:** Auth token.  
**Process:** Query QuizAttempt for user_id; order by completed_at desc.  
**Output:** List of QuizAttemptResponse.  
**Actor:** Student (dashboard).

---

**FR-38: Admin dashboard stats**  
**Description:** Aggregate counts and chart data for admin dashboard.  
**Input:** None.  
**Process:** Count users by role, Challenge count, UserProgress count; build user_distribution and challenge_usage (from progress by challenge_id); system_status.  
**Output:** total_users, active_exploits, fixed_vulns, user_distribution, challenge_usage, system_status.  
**Actor:** Admin.

---

**FR-39: Instructor dashboard stats**  
**Description:** Aggregate stats for instructor view.  
**Input:** None.  
**Process:** Count students, questions, assignments, UserProgress; compute avg_completion; class_performance placeholders.  
**Output:** total_students, quizzes_created, questions_in_bank, class_performance, avg_completion_rate.  
**Actor:** Instructor.

---

**FR-40: Search/list users**  
**Description:** List users with optional email search (auth not enforced on endpoint in provided code; may be used by admin/instructor UIs).  
**Input:** query (optional).  
**Process:** If query, filter by email contains, limit 20; else limit 50.  
**Output:** List of UserSearchResponse.  
**Actor:** Admin/Instructor.

---

**FR-41: Sandbox fix verification**  
**Description:** Run student code in isolated Docker container and determine pass/fail from test output.  
**Input:** student_code (string), challenge_dir (e.g. challenge-sql-injection).  
**Process:** Copy challenge folder to temp dir; overwrite app.py with student code; write Dockerfile; build image; run container on scale_net; capture logs; success if no "FAILED"/"Error"/"Traceback"; remove image.  
**Output:** (success: bool, logs: string).  
**Actor:** System (backend, triggered by submit-fix-*).

---

**FR-42: Database startup and table creation**  
**Description:** On backend startup, wait for DB and create tables if not present.  
**Input:** None (startup).  
**Process:** Retry connection up to 10 times; models.Base.metadata.create_all(bind=engine).  
**Output:** Tables created; app ready or raise.  
**Actor:** System.

---

**FR-43: Seed initial data**  
**Description:** Create default admin and instructor users and seed questions/challenges if configured (seed_db.py run at container start).  
**Input:** None (script).  
**Process:** wait_for_db; seed_users (admin, instructor); seed questions and challenges as per script.  
**Output:** DB populated.  
**Actor:** System (deployment).

---

## 3. NON-FUNCTIONAL REQUIREMENTS (NFR)

**NFR-1: Performance — API response time**  
**Requirement:** Authenticated API endpoints shall respond within a reasonable time (e.g. under 5 seconds for non-sandbox operations) under normal load.  
**Justification:** Users interact via browser; slow responses degrade usability. Sandbox operations may take longer (build + run).

---

**NFR-2: Performance — Sandbox execution**  
**Requirement:** Fix verification (sandbox build and test run) may take 30–120 seconds; the UI shall provide loading feedback.  
**Justification:** Docker build and test execution are inherently slower; user must be informed.

---

**NFR-3: Security — Authentication**  
**Requirement:** All protected operations shall require a valid JWT (Bearer token).  
**Justification:** Prevents unauthorized access to progress, fix submission, quiz attempts, and admin/instructor actions.

---

**NFR-4: Security — Password storage**  
**Requirement:** Passwords shall be stored only in hashed form (bcrypt).  
**Justification:** Reduces impact of DB compromise.

---

**NFR-5: Security — CORS**  
**Requirement:** API shall allow requests only from configured origins (e.g. localhost:5173, localhost:3000).  
**Justification:** Limits browser-based cross-origin abuse.

---

**NFR-6: Security — Role-based access**  
**Requirement:** Admin-only and instructor-only operations shall be restricted by role on the backend where applicable.  
**Justification:** Prevents privilege escalation via direct API calls.

---

**NFR-7: Usability — Responsive layout**  
**Requirement:** Frontend shall be usable on desktop and typical tablet viewports (layout and navigation).  
**Justification:** Students and instructors may use different devices; Tailwind and layout components support this.

---

**NFR-8: Usability — Clear feedback**  
**Requirement:** Fix submission and quiz submission shall show clear success/failure and logs or messages.  
**Justification:** Learning effectiveness depends on understanding outcomes (e.g. test logs, quiz score).

---

**NFR-9: Scalability — Stateless API**  
**Requirement:** API shall not rely on in-memory session state; JWT and DB hold authority.  
**Justification:** Allows horizontal scaling of backend instances.

---

**NFR-10: Scalability — Sandbox isolation**  
**Requirement:** Each fix verification run shall use an ephemeral container; no shared mutable state between runs.  
**Justification:** Prevents cross-user interference and allows concurrent submissions.

---

**NFR-11: Availability — Database retry**  
**Requirement:** Backend shall retry DB connection on startup (configurable retries with delay).  
**Justification:** DB may start after backend in Docker; retry improves startup reliability.

---

**NFR-12: Maintainability — Modular structure**  
**Requirement:** Backend shall be organized into routers (auth, challenges, quizzes, stats), shared DB and models, and a single sandbox runner.  
**Justification:** Eases maintenance and addition of new challenges or quiz features.

---

**NFR-13: Maintainability — Pydantic schemas**  
**Requirement:** Request and response shapes shall be defined with Pydantic models.  
**Justification:** Validation and documentation; fewer contract mismatches.

---

**NFR-14: Portability — Containerized deployment**  
**Requirement:** System shall run via Docker Compose (backend, frontend, main_db, challenge DBs, sandbox base, AI service).  
**Justification:** Consistent environment across development and deployment; backend needs Docker socket for sandbox.

---

**NFR-15: Reliability — Idempotent progress marking**  
**Requirement:** mark_challenge_complete shall not duplicate progress records (check exists before insert).  
**Justification:** Same challenge can be completed once per user; avoids duplicate rows.

---

**NFR-16: Compatibility — Browser support**  
**Requirement:** Frontend shall run on modern browsers supporting ES2020 and the used React/React Router features.  
**Justification:** Target environment is educational/lab; modern browsers are assumed.

---

**NFR-17: Compatibility — API contract**  
**Requirement:** Frontend and backend shall agree on API base URL (e.g. VITE_API_URL), auth header (Bearer token), and JSON request/response formats.  
**Justification:** Ensures frontend and backend can be developed or replaced consistently.

---

## 4. FEASIBILITY STUDY REPORT

### A) Technical Feasibility

**Technologies used:**  
- Backend: Python 3.9+, FastAPI, SQLAlchemy, PyMySQL, JWT (python-jose), bcrypt (passlib), Docker SDK, Pydantic.  
- Frontend: React 18, TypeScript, Vite, React Router, Axios, Monaco Editor, Tailwind CSS, Recharts.  
- Databases: MySQL 8.0 (main_db, challenge_db_sqli, challenge_db_csrf).  
- Infrastructure: Docker and Docker Compose; backend uses host Docker socket for sandbox.  
- Optional: Separate AI service (e.g. uvicorn on 8001) for quiz generation preview.

**Required skills:**  
- Backend: Python, FastAPI, SQL, JWT, Docker API, basic security (hashing, CORS).  
- Frontend: React, TypeScript, REST consumption, role-based routing.  
- DevOps: Docker Compose, MySQL, network configuration (scale_net).

**System limitations:**  
- Sandbox requires Docker; cannot run in environments where Docker is unavailable or restricted.  
- Challenge DBs (SQLi, CSRF) are separate MySQL instances; schema and connectivity must be maintained.  
- AI service is optional; quiz generation preview fails if service is down.  
- XSS challenge: frontend calls `/api/challenges/xss/comments`; if backend does not implement these endpoints, XSS attack page may fail or rely on client-side simulation only.

**Risks:**  
- Docker-in-Docker or socket mounting may be restricted in some hosting environments.  
- Resource usage: each fix submission builds and runs a container; high concurrency may stress CPU/memory.  
- Secret key and DB credentials in configuration; must be externalized and secured in production.

---

### B) Economic Feasibility

**Development cost:**  
- One-time: analysis, design, backend (auth, challenges, sandbox, quizzes, stats), frontend (all pages and flows), challenge content (five challenges with tests), seed data, Docker setup.  
- Proportional to team size and duration (e.g. 2–4 developers for several months for a full implementation as in the codebase).

**Infrastructure cost:**  
- Local: developer machines and Docker; minimal direct cost.  
- Deployed: hosting for backend, frontend, MySQL (x3), and optional AI service; Docker-capable host with sufficient RAM/CPU for sandbox builds.

**Maintenance cost:**  
- Updates to dependencies (Python, Node, React, FastAPI, MySQL).  
- Security patches; monitoring of JWT expiry and DB connectivity.  
- Adding new challenges or quiz topics (new challenge folders, tests, and UI).

**Cost vs benefit:**  
- Benefit: reusable secure-coding lab for students; reduced need for physical lab setup; progress and analytics in one place.  
- Cost is justified in educational settings where many students use the platform and instructors save time on manual grading of fixes and quizzes.

---

### C) Operational Feasibility

**User readiness:**  
- Students need a browser and basic understanding of “login, challenges, quiz.”  
- Instructors need to understand assignments and question bank.  
- Admins need to understand approval and user management.

**Organizational impact:**  
- Integrates into existing curricula as a lab component; may replace or supplement other security exercises.  
- Requires someone to run and maintain the deployment (and optionally the AI service).

**Training needs:**  
- Students: short guide or in-class walkthrough of challenges and quiz.  
- Instructors: how to create questions and assignments, interpret dashboard.  
- Admins: user lifecycle, approval, and stats.

---

### D) Schedule Feasibility

**Estimated timeline (indicative):**

- **Analysis:** 2–4 weeks — requirements, actors, challenge set, quiz and progress model, API and UI wireframes.  
- **Design:** 2–3 weeks — DB schema, API contracts, sandbox design, role and route matrix.  
- **Development:** 10–16 weeks — backend (auth, challenges, sandbox, quizzes, stats), frontend (all roles and pages), five challenges (app.py, test_app.py per challenge), seed data and Docker Compose.  
- **Testing:** 3–4 weeks — unit tests for sandbox and critical APIs, integration tests for login/progress/quiz, manual UI and challenge flows.  
- **Deployment:** 1–2 weeks — production Docker/Compose or equivalent, env configuration, DB backups, initial rollout.

*(Total rough order: 18–29 weeks for a small team; actuals depend on team size and scope changes.)*

---

## 5. CONTEXT DIAGRAM (DFD LEVEL 0) — TEXT DESCRIPTION

**External Entities:**

- **E1: Student** — A user with role “user” who logs in, views dashboard and challenges list, performs attack simulations, submits fixes, takes quizzes, and views own progress and quiz attempts.  
- **E2: Instructor** — A user with role “instructor” who logs in, manages questions and assignments, and views instructor dashboard.  
- **E3: Admin** — A user with role “admin” who logs in, manages users (approve, create admin, delete, update role) and views admin stats.  
- **E4: AI Service** — External HTTP service that generates quiz content (e.g. preview); called by the backend.  
- **E5: Docker (runtime)** — External runtime used by the backend to build and run sandbox containers for fix verification.

**Main System:**

- **SCALE (Secure Coding Learning Environment)** — The single system in the center. It includes the web application (frontend + backend API), main database, challenge databases, and the logic that coordinates authentication, challenges, quizzes, progress, and sandbox execution.

**Data Flows:**

- **E1 (Student) → SCALE:** Registration (email, password, role); Login (username, password); Challenge fix code (code); Quiz answers (question_id, selected_option_id); Quiz attempt (title, score, total, time_seconds); Attack simulation inputs (e.g. login credentials, host, redirect URL, comment content); Requests for progress, assignments, attempts, dashboard data.  
- **SCALE → E1 (Student):** Token and user info; Challenge list and progress; Fix submission result (success, logs); Quiz questions and feedback; Dashboard stats and recent quiz attempts; Attack success/failure and redirects.  
- **E2 (Instructor) → SCALE:** Login; Question CRUD (create/update/delete); Assignment create/delete; Requests for topics, questions, assignments, instructor stats; AI preview request.  
- **SCALE → E2 (Instructor):** Token and user info; Questions and assignments list; Instructor dashboard stats; AI preview response.  
- **E3 (Admin) → SCALE:** Login; Approve instructor (user_id); Create admin (email, password); Delete user (user_id); Update role (user_id, role); Request user list and pending list; Request admin dashboard stats.  
- **SCALE → E3 (Admin):** Token and user info; Pending users list; Admin dashboard stats; User list; Success/error responses.  
- **SCALE → E4 (AI Service):** HTTP POST with topic, count, difficulty, skill_focus.  
- **E4 (AI Service) → SCALE:** Generated content (e.g. questions preview).  
- **SCALE → E5 (Docker):** Build image (Dockerfile, context); Run container (image, network).  
- **E5 (Docker) → SCALE:** Build logs; Container stdout/stderr (test results).

---

## 6. DATA FLOW DIAGRAM — LEVEL 1 (STRUCTURED TEXT)

**Processes:**

- **P1: Authenticate & Authorize** — Validates credentials, issues JWT; checks token and role for protected endpoints; handles registration and instructor approval.  
- **P2: Manage Users (Admin)** — List users and pending instructors; approve instructor; create admin; delete user; update user role.  
- **P3: Run Challenge Attacks** — Executes vulnerable SQLi login, CSRF reset/accounts/transfer, ping (command injection), redirect; returns results to frontend.  
- **P4: Verify Fixes (Sandbox)** — Receives code and challenge name; runs sandbox (copy, overwrite app.py, build, run, parse logs); updates UserProgress on success; returns success and logs.  
- **P5: Manage Progress & Attacks** — Returns current user’s progress list; marks attack complete for a challenge type (writes to UserProgress).  
- **P6: Manage Questions & Assignments** — CRUD questions; list topics; create/list/delete assignments; return questions for assignment or practice.  
- **P7: Run Quiz & Record Attempts** — Submit single answer (store UserAnswer, return correct/explanation); submit quiz attempt (store QuizAttempt); return user’s attempts list.  
- **P8: Aggregate Statistics** — Compute admin dashboard (user counts, progress counts, chart data); compute instructor dashboard (students, questions, assignments, completion).  
- **P9: Call AI Service** — Send request to AI service; return response (or error).

**Data Stores:**

- **D1: users** — User accounts (id, email, hashed_password, role, is_approved).  
- **D2: user_progress** — Completed challenges per user (user_id, challenge_id, completed_at).  
- **D3: questions** — Quiz questions (id, text, type, topic, difficulty, skill_focus, explanation).  
- **D4: question_options** — Options per question (id, question_id, text, is_correct).  
- **D5: user_answers** — Single quiz answers (user_id, question_id, selected_option_id, is_correct, timestamp).  
- **D6: quiz_assignments** — Assignments (id, title, instructor_id, question_ids, assigned_student_ids, created_at).  
- **D7: quiz_attempts** — Completed quiz attempts (user_id, assignment_id, title, score, total, time_seconds, completed_at).  
- **D8: challenges** — Challenge metadata (id, title, description) — used for stats.  
- **D9: xss_comments** — (Model exists; if used, stores XSS challenge comments.)  
- **D10: challenge_db_sqli** — External DB for SQLi challenge (e.g. users table).  
- **D11: challenge_db_csrf** — External DB for CSRF challenge (accounts table).

**External Entities (same as Level 0):**

- **E1: Student**  
- **E2: Instructor**  
- **E3: Admin**  
- **E4: AI Service**  
- **E5: Docker**

**Data Flows (Level 1):**

- **E1 → P1:** Login (username, password); Register (email, password, role).  
- **P1 → D1:** Read user by email; Create user (register); Update is_approved (approve).  
- **P1 → E1:** JWT, user_id, role, email.  
- **E3 → P2:** Approve (user_id); Create admin (email, password); Delete user (user_id); Update role (user_id, role); List/pending requests.  
- **P2 → D1:** Read users, pending; Update is_approved, role; Delete user; Insert user (create admin).  
- **P2 → E3:** User list; Pending list; Success/error.  
- **E1 → P3:** Vulnerable login (username, password); CSRF reset; CSRF accounts request; CSRF transfer (to_user, amount); Ping (host); Redirect (url).  
- **P3 → D10:** SQL query (vulnerable login); P3 → D11: Reset/select/update accounts; CSRF transfer.  
- **P3 → E1:** Login result; Account list; Transfer result; Ping output/success; Redirect (302).  
- **E1 → P4:** Code submission (code, challenge identifier via endpoint).  
- **P4 → E5:** Build and run container (context, Dockerfile).  
- **E5 → P4:** Build logs; Container output (test results).  
- **P4 → D2:** Insert UserProgress on success.  
- **P4 → E1:** success, logs.  
- **E1 → P5:** Get progress; Mark attack complete (challenge_type).  
- **P5 → D2:** Read by user_id; Insert (mark complete).  
- **P5 → E1:** Progress list; {ok: true}.  
- **E2 → P6:** Create/update/delete question; Create/delete assignment; Get topics, questions, assignments; Get assignment questions.  
- **E1 → P6:** Get assignments (student); Take assignment (id); Take practice (topics, count).  
- **P6 → D3, D4:** Question and options CRUD.  
- **P6 → D6:** Assignment CRUD; Read for instructor and student.  
- **P6 → E2, E1:** Questions, topics, assignments, assignment questions.  
- **E1 → P7:** Submit answer (question_id, selected_option_id); Submit attempt (title, score, total, time_seconds, assignment_id); Get attempts.  
- **P7 → D5:** Insert UserAnswer.  
- **P7 → D7:** Insert QuizAttempt; Read by user_id.  
- **P7 → D3, D4:** Read question/options for correctness and explanation.  
- **P7 → E1:** correct, explanation; Attempt record; Attempts list.  
- **E3 → P8:** Request admin dashboard.  
- **E2 → P8:** Request instructor dashboard.  
- **P8 → D1, D2, D3, D6, D8:** Counts and aggregates.  
- **P8 → E3, E2:** Dashboard JSON (stats, charts).  
- **E2 → P9:** AI preview request (topic, count, difficulty, skill_focus).  
- **P9 → E4:** HTTP POST (body).  
- **E4 → P9:** HTTP response (generated content).  
- **P9 → E2:** Response or error.

---

## 7. ASSUMPTIONS & LIMITATIONS

### System Assumptions

- Users have a modern browser with JavaScript enabled and support for session storage.  
- The backend has access to the Docker socket (or equivalent) to create and run sandbox containers.  
- MySQL instances (main_db, challenge_db_sqli, challenge_db_csrf) are reachable from the backend on the Docker network and are initialized with the expected schemas and seed data where applicable.  
- JWT secret and database credentials are provided via configuration or environment; they are not assumed to be default or empty in production.  
- Email is used as the unique user identifier (username) for login.  
- Instructors registering through the app start with `is_approved=False` until an admin approves.  
- One attempt per user per challenge type is sufficient for progress (no versioning of multiple completions).  
- Quiz timer is maintained in the frontend only; the backend trusts the submitted time_seconds for quiz attempts.  
- The frontend and backend are deployed so that the frontend can reach the backend at the configured API URL (e.g. same host or CORS-allowed origin).  
- The AI service, if used, is deployed and reachable at the configured URL; its absence or failure only affects the AI preview feature.

### System Limitations

- Fix verification depends on Docker; environments without Docker (or with restricted Docker) cannot run sandbox verification.  
- Sandbox runs are sequential per request; high concurrency may cause queuing or resource contention.  
- Challenge databases (SQLi, CSRF) use separate MySQL instances; backup and recovery must include these.  
- XSS challenge: the frontend references `/api/challenges/xss/comments` for GET/POST/DELETE; if these routes are not implemented in the backend, the XSS attack page may not persist or load comments from the main app DB.  
- Admin and instructor stats use challenge_id and progress aggregates; mapping to challenge names (e.g. SQLi, XSS) is partly hardcoded in stats (e.g. pid '1', '2').  
- No password reset or email verification flow is implemented.  
- Session storage is used for token; logout is effectively “clear session” (e.g. closing the tab or explicit clear).  
- Recharts and dashboard charts depend on the shape of data returned by the stats API; changes to API require frontend updates.

### Known Risks

- **Security:** Default or weak JWT secret or DB credentials in code or config could lead to compromise.  
- **Availability:** If MySQL or Docker is down, core features (login, progress, fix verification) are affected.  
- **Resource:** Many simultaneous sandbox runs can exhaust CPU/memory on the host.  
- **Integrity:** Student-submitted code is executed in containers; sandbox isolation limits but does not eliminate risk (e.g. malicious code in app.py).  
- **Compatibility:** Future Docker or MySQL version changes may require adjustments to the sandbox or connection strings.

---

*End of System Documentation. All sections are derived from the project source code and configuration as analyzed.*
