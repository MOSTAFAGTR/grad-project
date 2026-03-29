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