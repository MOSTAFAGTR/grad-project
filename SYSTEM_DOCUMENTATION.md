# SCALE System Documentation

## 1. Project Overview

### System Name
**SCALE** (Secure Coding and Attack Learning Environment)

### Purpose of the System
SCALE is a full-stack cybersecurity education platform that combines vulnerable labs, static security analysis, AI-guided explanation, and attack simulation into a single learning workflow. The platform is implemented with:
- Backend: FastAPI (`backend/app/*`)
- Frontend: React + TypeScript (`frontend/src/*`)
- Supporting services: relational persistence via SQLAlchemy-backed DB models and optional OpenAI integration for mentoring and project summarization.

### Problem It Solves
Traditional secure-coding training is often fragmented:
- vulnerable labs are disconnected from code scanning,
- scanners provide findings but weak educational context,
- students can execute steps without understanding exploit mechanics.

SCALE addresses this by linking:
1. project upload and scanning,
2. structured vulnerability findings,
3. AI mentor explanations,
4. deterministic attack simulation for exploit understanding.

### Target Users
- **Students (`user`)**: run labs, take quizzes, use scanner and mentor feedback.
- **Instructors (`instructor`)**: manage quizzes, monitor students, use scanner and messaging.
- **Admins (`admin`)**: user/role governance, approvals, global statistics, system oversight.

### Importance in Cybersecurity Education
SCALE is educationally significant because it unifies:
- **detection** (scanner),
- **understanding** (AI mentor),
- **attacker perspective** (AttackLab),
- **defensive correction** (fix submissions and recommendations),
within an authenticated, role-aware environment.

---

## 2. System Objectives

### Learning Objectives
- Teach how insecure patterns appear in real source code.
- Help learners map findings to concrete exploit chains.
- Build secure refactoring habits via fix recommendations and challenge validations.

### Security Training Goals
- Cover common vulnerability classes: SQL Injection, XSS, CSRF, Command Injection, hardcoded secrets, misconfiguration.
- Reinforce both attack and defense perspectives.
- Provide role-based progression from practice to administration.

### Practical Attack Understanding
- Move beyond static alerts by showing request-payload-execution-impact flow.
- Explain attacker gain (data exposure, privilege abuse, unauthorized state change).

### AI-Assisted Learning Goals
- Provide contextual explanation tied to exact file/line/snippet.
- Offer remediation rationale, not only payload examples.
- Maintain service continuity via deterministic fallback responses when AI is unavailable.

---

## 3. Feasibility Study

### Technical Feasibility

#### Technology Stack
- **Backend API**: FastAPI router architecture (`backend/app/main.py`, `backend/app/api/*.py`).
- **Static scanner**: regex rules + heuristic pass (`backend/app/scanner/rules.py`, `backend/app/scanner/detector.py`).
- **Fix enrichment**: template recommendations (`backend/app/scanner/fixer.py`).
- **Risk scoring/reporting**: lightweight score + PDF export (`backend/app/scanner/scorer.py`, `backend/app/scanner/report_generator.py`).
- **Attack simulation**: deterministic templates (`backend/app/attacks/templates.py`, `backend/app/api/attack_simulator.py`).
- **AI mentor**: structured endpoint with JSON contract and fallback (`backend/app/api/ai_mentor.py`).
- **Project analyzer**: structure/language/framework/risk heuristics (`backend/app/api/project_analyzer.py`).
- **Frontend**: React Router + role-protected routes + context persistence (`frontend/src/App.tsx`, `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/context/ScanContext.tsx`).

#### Scalability Considerations
- Modular APIs allow horizontal growth by domain (auth, projects, scanner, attack simulator, quizzes, messaging).
- Static scan complexity scales with number/size of extracted files (line-by-line regex).
- AI usage is naturally bounded in some paths (e.g., `/api/project/scan/ai` limits enrichment to first 5 findings).
- Polling-based unread checks are limited to visibility-aware 30s intervals (`frontend/src/components/Sidebar.tsx`).

#### Limitations Affecting Technical Feasibility
- Regex scanning does not model data flow/taint propagation.
- Some language support is extension-level with shallow semantic coverage.
- Project analysis uses heuristics rather than full parser/AST pipelines.
- Upload handling reads zip into memory before write (capped to 50 MB).

### Operational Feasibility
- Supports three operational roles with clear access boundaries.
- Requires standard web deployment:
  - backend reachable on API base URL,
  - frontend build served to browser,
  - DB availability at app startup.
- User journey is practical for classrooms/labs:
  - login -> challenge/scan -> mentor/simulation -> message/quiz/report.

### Economic Feasibility
- Core scanner/simulation/reporting are deterministic and run locally in backend process.
- AI cost is variable and controllable:
  - optional via `OPENAI_API_KEY`,
  - model configurable via env in `ai_mentor.py` and `project_analyzer.py`.
- Educational value-to-cost ratio is high because non-AI fallback preserves functionality.

### Legal and Security Feasibility
- Attack simulation endpoint is text-template based and does not execute real commands/queries.
- Scanner performs static reading only (no execution).
- Authenticated endpoints guard sensitive features using JWT and role checks.
- Challenge endpoints intentionally include vulnerable behavior for training; scope control and deployment policy must isolate training environments from production systems.

---

## 4. Functional Requirements

Each requirement below is represented in current implementation.

### 4.1 User Authentication and Authorization
- **Input**: email/password and optional registration role.
- **Process**:
  - user registration/login in `backend/app/api/auth.py`,
  - JWT generation/validation,
  - reusable role dependency `require_role(...)`,
  - client-side verification via `/api/auth/me` in `frontend/src/components/ProtectedRoute.tsx`.
- **Output**:
  - authenticated session token,
  - role-aware route access,
  - gated API behavior by role.

### 4.2 Project Upload
- **Input**: `.zip` file from Scanner page (`frontend/src/pages/Scanner.tsx`).
- **Process**:
  - `POST /api/project/upload` (`backend/app/api/projects.py`),
  - extension and size validation,
  - disk persistence under uploads directory.
- **Output**:
  - `project_id`,
  - extracted project folder path metadata.

### 4.3 ZIP Extraction and Validation
- **Input**: uploaded zip artifact.
- **Process** (`extract_zip` in `backend/app/api/projects.py`):
  - whitelist extension filtering,
  - traversal protection (`resolve` path guard),
  - skip unwanted trees (e.g., `node_modules`),
  - debug logging and extracted-file count checks.
- **Output**:
  - safe extracted files,
  - explicit failure if zero files extracted.

### 4.4 Project Root Normalization
- **Input**: extraction root path.
- **Process** (`normalize_project_root`):
  - descend through single-child directory wrappers.
- **Output**:
  - practical scan root for nested archive layouts.

### 4.5 File Traversal and Language Mapping
- **Input**: normalized project root.
- **Process** (`scan_project_files` in `projects.py`):
  - recursive walk with skip directories,
  - extension -> language mapping (including `.dart`),
  - per-file scan debug output.
- **Output**:
  - file inventory list for scanner.

### 4.6 Vulnerability Scanning
- **Input**: discovered files and scanner rules.
- **Process**:
  - regex line matching by rule (`backend/app/scanner/rules.py`),
  - detailed scan with aliases and CSRF heuristic (`backend/app/scanner/detector.py`),
  - fix attachment (`backend/app/scanner/fixer.py`),
  - risk score (`backend/app/scanner/scorer.py`).
- **Output**:
  - findings array with type/severity/file/line/code/fix,
  - summary counts, risk object, debug telemetry.

### 4.7 Project Structure Analysis
- **Input**: `project_id`.
- **Process** (`POST /api/project/analyze-structure` in `backend/app/api/project_analyzer.py`):
  - language/framework detection heuristics,
  - entry-point detection,
  - risk-indicator extraction,
  - optional AI summary generation.
- **Output**:
  - `{languages, frameworks, entry_points, files_summary, risk_indicators, ai_summary}`.

### 4.8 AI Mentor Analysis
- **Input**: finding context `{code, language, vulnerability_type, severity, file, line}`.
- **Process** (`POST /api/ai/analyze-code` in `backend/app/api/ai_mentor.py`):
  - bounded snippet length,
  - strict output schema expectation,
  - JSON extraction/normalization,
  - fallback on key absence or exceptions.
- **Output**:
  - structured mentor response:
    `explanation`, `attack_scenario`, `payload_example`, `technical_breakdown`, `fix_recommendation`, `secure_code_example`, `critique`, `confidence`.

### 4.9 Attack Simulation Lab
- **Input**: vulnerability type + code + payload.
- **Process**:
  - `POST /api/attack/simulate` in `backend/app/api/attack_simulator.py`,
  - normalized type dispatch to `backend/app/attacks/templates.py`,
  - deterministic timeline/result generation.
- **Output**:
  - educational simulation response with state transition and impact narrative.

### 4.10 Frontend Scanner UX
- **Input**: scan response and project overview response.
- **Process** (`frontend/src/pages/Scanner.tsx`):
  - card rendering of findings,
  - severity badges,
  - selected-finding details,
  - mentor drawer launch,
  - simulation navigation.
- **Output**:
  - readable, non-horizontal-overflow security results experience.

### 4.11 AttackLab UX
- **Input**: scanner navigation state.
- **Process** (`frontend/src/pages/AttackLab.tsx`):
  - locked vulnerability type (guided),
  - auto/default payload initialization,
  - API call + replay timeline.
- **Output**:
  - interactive exploit walkthrough.

### 4.12 Messaging and Unread Indicators
- **Input**: contacts/messages endpoints.
- **Process**:
  - global unread polling in sidebar (`frontend/src/components/Sidebar.tsx`),
  - per-contact unread counts in `frontend/src/pages/MessagesPage.tsx`,
  - read-state update when conversation loaded (`backend/app/api/messages.py`).
- **Output**:
  - global dot indicator and per-conversation unread metadata.

### 4.13 Dashboards, Quizzes, and Progress
- **Input**: stats/quizzes/challenge-progress API calls.
- **Process**:
  - role-based dashboard aggregation,
  - quiz assignment/attempt flows,
  - challenge completion and hint usage tracking.
- **Output**:
  - operational visibility for students/instructors/admins.

---

## 5. Non-Functional Requirements

### Performance
- Upload constrained to 50 MB in backend upload endpoint.
- Scanner processes text files with line-level regex; complexity proportional to file size and rule count.
- Sidebar unread polling is reduced to 30s and visibility-aware.

### Scalability
- Domain-separated routers allow service growth.
- Context-based frontend state avoids repeated rescan on route change.
- Analyzer and scan endpoints can be independently optimized/cached.

### Security
- JWT authentication with role checks on sensitive endpoints.
- Zip traversal protection and extension whitelisting.
- Attack simulation is deterministic and non-executing.
- AI prompt includes untrusted-code instruction boundary.

### Usability
- Guided scanner -> mentor -> simulation flow.
- AttackLab includes fallback message when state is missing.
- Severity and risk visualization is immediate in scanner.

### Reliability
- AI fallback ensures degraded-but-functional behavior.
- Detailed debug payload supports root-cause diagnostics.
- Build-time frontend type checks and backend schema typing improve runtime consistency.

### Maintainability
- Modular backend packages by concern.
- Shared frontend API base config (`frontend/src/lib/api.ts`).
- Shared default payload utilities (`frontend/src/utils/payloads.ts`).
- Persistent scan context (`frontend/src/context/ScanContext.tsx`).

---

## 6. System Architecture

### High-Level Architecture
1. **Presentation Layer (Frontend)**:
   - React pages, role-protected routing, contextual state.
2. **Application/API Layer (Backend)**:
   - FastAPI routers by bounded context (`auth`, `projects`, `scanner`, `ai`, `attack`, `messages`, `quizzes`, `stats`, `challenges`).
3. **Analysis Layer**:
   - static scanner + risk + fix engine,
   - project analyzer heuristics,
   - optional AI assist.
4. **Persistence Layer**:
   - SQLAlchemy models and scan history.

### API Communication Flow
- Browser sends bearer-authenticated requests to FastAPI JSON endpoints.
- Backend emits structured contracts consumed directly by React state renderers.
- AI endpoints call OpenAI only if configured; fallback otherwise.

### Module Separation
- `backend/app/api/*`: transport + orchestration
- `backend/app/scanner/*`: static analysis logic
- `backend/app/attacks/*`: simulation templates
- `frontend/src/pages/*`: user journeys
- `frontend/src/context/*`: cross-page persistence
- `frontend/src/utils/*`: shared helpers (payload defaults)

### Upload-to-Learning Pipeline (Required)
1. **UPLOAD**: `Scanner.tsx` -> `POST /api/project/upload`
2. **EXTRACTION**: `extract_zip` validates and extracts code files
3. **NORMALIZATION**: `normalize_project_root` resolves nested single-dir archives
4. **SCAN**: `POST /api/project/scan` -> rule detector + fixes + score + debug
5. **AI**: `POST /api/ai/analyze-code` for selected finding explainability
6. **SIMULATION**: `POST /api/attack/simulate` for attacker-flow representation

---

## 7. Detailed Module Explanation

### 7.1 Scanner Engine

#### `backend/app/scanner/rules.py`
- Defines vulnerability signatures with regex arrays and severities.
- Coverage: SQLi, XSS, Command Injection, Hardcoded Secret (including Dart secret pattern), CSRF.

#### `backend/app/scanner/detector.py`
- Reads file line-by-line with ignored decode errors.
- Adds frontend-friendly aliases (`type`, `code`) in addition to canonical fields.
- Includes file-level CSRF heuristic:
  - detects POST form/handler presence without CSRF evidence.
- Returns detailed diagnostics (`lines_scanned`, read error status).

#### `backend/app/scanner/fixer.py`
- Maps finding type to explanation/recommendation/example.
- Language guess from file extension selects best example variant.

#### `backend/app/scanner/scorer.py`
- Severity-weight score:
  - High=5, Medium=3, Low=1
- Risk band thresholds:
  - <=10 Low, <=20 Medium, >20 High

#### `backend/app/scanner/report_generator.py`
- Produces structured JSON report and printable PDF.
- Includes executive summary, severity/type distributions, detailed findings table.

#### Scanner Limitations
- Regex is pattern-based, not semantic.
- Can produce false positives/negatives.
- No call graph, taint path, or sanitization trace validation.

### 7.2 AI Mentor

#### Endpoint and Contract
- Route: `POST /api/ai/analyze-code` (`backend/app/api/ai_mentor.py`)
- Request/Response schema in `backend/app/schemas.py`.

#### Prompt Design
- System prompt positions model as penetration tester + secure coding instructor.
- User prompt injects file/line/type/severity/language + snippet.
- Requires strict JSON response shape.

#### Safety Handling
- Code snippet length cap (`AI_MENTOR_MAX_CODE_CHARS`).
- Explicit instruction to treat code as untrusted text.
- Robust fallback response path when API key absent or response parse fails.

### 7.3 Attack Simulator

#### Endpoint and Contract
- Route: `POST /api/attack/simulate` (`backend/app/api/attack_simulator.py`)
- Contract in `AttackSimulateRequest/Response` (`backend/app/schemas.py`)

#### Template Model
- Type dispatch into template map (`backend/app/attacks/templates.py`):
  - SQL Injection
  - XSS
  - Command Injection
  - CSRF
- Unsupported types return safe fallback.

#### Deterministic Behavior
- Simulator returns narrative state transitions and timeline.
- No shell execution, DB query execution, or side-effectful attack execution.

### 7.4 Project Analyzer

#### Endpoint
- `POST /api/project/analyze-structure` (`backend/app/api/project_analyzer.py`)

#### Detection Logic
- Language detection from extension map.
- Framework inference by content markers (React/FastAPI/Flask/Django/Express/Flutter).
- Entry-point inference by canonical file names.
- Risk indicator heuristics:
  - API route patterns,
  - DB usage markers,
  - possible command sinks,
  - secret indicators,
  - docker socket marker.

#### AI Summary
- Optional summary from OpenAI if key configured.
- Returns `ai_summary` or `null` without breaking overall response.

### 7.5 Frontend UI Modules

#### Scanner Page (`frontend/src/pages/Scanner.tsx`)
- Upload -> structure analysis -> scan orchestrator.
- Findings cards with severity badges and wrapped snippets.
- AI mentor drawer state machine with caching.
- Simulation navigation to AttackLab with prefilled data.
- Scan result persistence via `ScanContext`.

#### AttackLab Page (`frontend/src/pages/AttackLab.tsx`)
- Guided mode with locked vulnerability type.
- Payload auto-init from navigation or defaults.
- Simulation call rendering: execution flow, timeline, result impact.
- Replay step animation.

#### AI Mentor Panel (inside Scanner page)
- On-demand analysis per finding.
- Editable code snippet for iterative re-analysis.
- Structured educational sections with confidence label.

---

## 8. Data Flow Diagram (Textual)

1. **User authenticates** -> token stored in session storage.
2. **User uploads zip** from Scanner page.
3. **Backend upload endpoint** validates extension and size, saves archive.
4. **Extraction module** extracts whitelisted files with traversal safeguards.
5. **Root normalization** resolves nested top-level wrapper directories.
6. **Project analyzer endpoint** (optional immediate call from frontend) extracts project metadata.
7. **Scan endpoint** enumerates files, runs rule detector, attaches fixes, computes risk.
8. **Backend returns findings + summary + debug telemetry**.
9. **Frontend renders findings cards** and selected snippet.
10. **User opens AI mentor** -> finding context sent to `/api/ai/analyze-code`.
11. **Mentor response displayed** as explanation/attack/fix/critique.
12. **User clicks Simulate Attack** -> route transition to `/attack-lab` with state.
13. **AttackLab calls simulator API** and displays timeline + impact narrative.

---

## 9. Project Management Plan (PMP)

### Development Phases

#### Phase 1: Scanner Foundation
- Upload endpoint, extraction, traversal, rule engine, risk scoring.
- Deliverable: functional static scanner with debug metadata.

#### Phase 2: AI Mentor Integration
- Structured mentor endpoint and UI panel.
- Deliverable: finding-level contextual explanation with fallback resilience.

#### Phase 3: Attack Simulation Lab
- Template-driven `/api/attack/simulate` + AttackLab UI.
- Deliverable: safe exploit walkthrough and replayable timeline.

#### Phase 4: UX and Product Hardening
- Scanner card UX, payload centralization, state persistence, messaging unread refinement, project overview analyzer.
- Deliverable: production-oriented user flow and continuity.

### Risk Management
- **False positives/negatives**: mitigate by documenting scanner depth and expanding rules incrementally.
- **Unsupported languages**: mitigate via extension support roadmap and honest no-detection messaging.
- **AI failures/timeouts**: mitigate via deterministic fallback contracts.
- **Access-control drift**: mitigate through strict route-role mapping and `/api/auth/me` verification.
- **Operational noise**: extraction debug logging should be managed per environment.

### Timeline Estimation (Indicative)
- Phase 1: 3-5 weeks
- Phase 2: 2-3 weeks
- Phase 3: 2-4 weeks
- Phase 4: 2-3 weeks
- Total: ~9-15 weeks depending on team size/testing depth.

---

## 10. Security Considerations

### Why Simulation Is Safe
- Attack simulation templates are static string transformations.
- No real command execution or database mutation from simulator endpoint.

### No Real Attack Execution in Scanner/Analyzer
- Scanner and analyzer read text files only.
- No dynamic execution of uploaded source.

### Input Safety
- Upload endpoint validates type and size.
- Zip extraction blocks path traversal.
- Auth-required endpoints enforce bearer token dependencies.

### Auth and RBAC Controls
- Backend uses role checks for sensitive management endpoints.
- Frontend route protection validates token and role server-side (`/api/auth/me`).

### Challenge Surface Isolation Note
- Certain vulnerable challenge endpoints are intentionally unsafe by design for training.
- Deployment policy must isolate training system from production business assets.

---

## 11. Limitations

1. **Regex-based detection depth**:
   - no AST-level data flow,
   - no inter-file taint correlation.
2. **CSRF heuristic simplicity**:
   - may over/under-report depending on framework idioms.
3. **Partial language semantics**:
   - extension recognized does not imply deep parser support.
4. **AI variability**:
   - quality depends on model behavior and prompt adherence.
5. **State handoff dependency**:
   - direct navigation to AttackLab without scanner state yields limited context.
6. **Project analyzer heuristics**:
   - framework/risk detection is indicator-based, not formal static analysis.

---

## 12. Future Improvements

1. **AST and parser-based scanning**
   - language-specific parsers for lower false positives.
2. **Taint analysis**
   - source-to-sink path reasoning with sanitization tracking.
3. **Semantic framework plugins**
   - framework-aware rules (Django, Spring, Flutter, etc.).
4. **Advanced AI personalization**
   - learner-level adaptation, remediation progression tracking.
5. **More robust project modeling**
   - dependency graph extraction and architecture visualization.
6. **Security policy hardening**
   - stricter defaults for secrets and challenge-route gating by environment.
7. **Observability**
   - structured logs, trace IDs, and monitoring dashboards.

---

## 13. Conclusion

SCALE is a comprehensive secure-coding learning platform that exceeds a typical student project by integrating:
- role-aware full-stack architecture,
- practical vulnerability labs,
- upload-based static analysis,
- AI-assisted mentoring,
- deterministic attack simulation,
- project-structure intelligence,
- and operational UX features such as persistent scan context and messaging signals.

Its strongest contribution is not any single module, but the **end-to-end educational loop**:
**detect -> explain -> simulate -> fix -> track**.
This architecture enables learners to move from passive vulnerability awareness to active adversarial and defensive reasoning, which is the core objective of advanced cybersecurity education.

---

## Appendix A: Module Coverage Matrix (Analyzed Scope)

### Backend API (`backend/app/api/*`)
- `auth.py`
- `quizzes.py`
- `challenges.py`
- `stats.py`
- `messages.py`
- `projects.py`
- `game_challenge.py`
- `misconfig.py`
- `ai_mentor.py`
- `attack_simulator.py`
- `project_analyzer.py`

### Backend Scanner (`backend/app/scanner/*`)
- `rules.py`
- `detector.py`
- `fixer.py`
- `scorer.py`
- `report_generator.py`

### Backend Attacks (`backend/app/attacks/*`)
- `templates.py`

### Core Backend Wiring
- `backend/app/schemas.py`
- `backend/app/main.py`

### Frontend Pages (`frontend/src/pages/*`)
- `AdminDashboardPage.tsx`
- `AdminStatsPage.tsx`
- `AttackLab.tsx`
- `AttackSuccessPage.tsx`
- `BrokenAuthAttackPage.tsx`
- `BrokenAuthFixPage.tsx`
- `ChallengesListPage.tsx`
- `CommandChallengePage.tsx`
- `CommandInjectionAttackPage.tsx`
- `CommandInjectionFixPage.tsx`
- `CommandInjectionTutorialPage.tsx`
- `CsrfAttackPage.tsx`
- `CsrfFixPage.tsx`
- `CsrfTutorialPage.tsx`
- `DashboardHomePage.tsx`
- `HomePage.tsx`
- `InstructorDashboardPage.tsx`
- `InstructorQuizPage.tsx`
- `LandingPage.tsx`
- `LoginPage.tsx`
- `MessagesPage.tsx`
- `RedirectAttackPage.tsx`
- `RedirectChallengePage.tsx`
- `RedirectFixPage.tsx`
- `RedirectTutorialPage.tsx`
- `RegisterPage.tsx`
- `Scanner.tsx`
- `ScenarioPage.tsx`
- `SecurityMiscAttackPage.tsx`
- `SecurityMiscFixPage.tsx`
- `SqlInjectionAttackPage.tsx`
- `SqlInjectionFixPage.tsx`
- `SqlInjectionTutorialPage.tsx`
- `StudentQuizPage.tsx`
- `UnderConstructionPage.tsx`
- `XssAttackPage.tsx`
- `XssFixPage.tsx`
- `XssTutorialPage.tsx`

### Frontend Context/Utils
- `frontend/src/context/ScanContext.tsx`
- `frontend/src/utils/payloads.ts`

### Frontend Routing/State Infrastructure
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/components/ProtectedRoute.tsx`
- `frontend/src/components/MainLayout.tsx`
- `frontend/src/components/Sidebar.tsx`
- `frontend/src/lib/api.ts`

